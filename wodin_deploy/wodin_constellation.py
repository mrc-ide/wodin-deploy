import time
from constellation import ConstellationMount, ConstellationContainer, Constellation, docker_util
import subprocess


class WodinConstellation:
    def __init__(self, cfg):
        self.cfg = cfg
        redis = redis_container(cfg)
        odin_api = odin_api_container(cfg)
        sites = sites_containers(cfg)
        proxy = wodin_proxy_container(cfg)

        containers = [redis, odin_api] + sites + [proxy]

        self.obj = Constellation(
            "wodin", cfg.container_prefix,
            containers, cfg.network,
            {"redis-data": "redis-data", "wodin-config": "wodin-config"},
            data=cfg
        )

    def start(self, **kwargs):
        self.obj.start(**kwargs)

    def stop(self, **kwargs):
        self.obj.stop(**kwargs)

    def status(self):
        self.obj.status()


def redis_container(cfg):
    redis = cfg.redis
    redis_mounts = [ConstellationMount("redis-data", "/data")]
    return ConstellationContainer(redis["name"], redis["ref"], mounts=redis_mounts)


def odin_api_container(cfg):
    odin_api = cfg.odin_api
    return ConstellationContainer("api", odin_api["ref"])


def get_preconfigure(site, container_name, container_prefix):
    return lambda x, data: subprocess.call([
        "docker", "cp", "./siteConfigs/" + site,
        container_prefix + "-" + container_name + ":/wodin/config/" + site
    ])


def configure_wodin(_, cfg):
    for i in range(0, 10):
        redis_log = subprocess.run([
            "docker", "logs",
            "{}-{}".format(cfg.container_prefix, cfg.redis["name"])
        ], stdout=subprocess.PIPE)
        if "Ready to accept connections" in redis_log.stdout.decode('utf-8'):
            break
        time.sleep(1)


def get_wodin_container(cfg, site, path, sites):
    wodin = cfg.wodin
    container_prefix = cfg.container_prefix
    wodin_mounts = [ConstellationMount("wodin-config", "/wodin/config")]
    container_name = wodin["name"] + "-" + site
    return ConstellationContainer(container_name, wodin["ref"], mounts=wodin_mounts,
                                  args=[
                                      "--redis-url=redis://epimodels-redis:6379",
                                      "--odin-api=http://epimodels-api:8001",
                                      "--base-url=http://localhost/" + path,
                                      "/wodin/config/" + site
                                  ],
                                  configure=configure_wodin,
                                  preconfigure=get_preconfigure(site, container_name, container_prefix))


def sites_containers(cfg):
    sites = cfg.sites
    subprocess.call(["rm", "-rf", "./siteConfigs"])
    subprocess.call(["mkdir", "./siteConfigs"])
    wodin_containers = []
    for site in sites.keys():
        subprocess.call(["mkdir", "./siteConfigs/" + site])
        site_dict = sites[site]
        subprocess.call(["git", "clone", "--branch=" + site_dict["ref"], site_dict["url"], "./siteConfigs/" + site])
        wodin_containers.append(get_wodin_container(cfg, site, site_dict["urlPath"], sites))
    return wodin_containers


def create_index_page(sites):
    html_strings = [
        "<html>\n<head>\n<title>Wodin</title>\n</head>\n<body>\n",
        "<h1>Wodin</h1>\n",
        "<p>There are {} deployed configurations:</p>\n".format(len(sites)),
        "<ul>\n"
    ]
    for site in sites.keys():
        site_obj = sites[site]
        html_strings.append("<li><a href='/{}'><code>{}</code></a>: {}</li>\n"
                            .format(site_obj["urlPath"], site, site_obj["description"]))
    html_strings.append("</ul>\n</body>\n</html>")
    return html_strings


def proxy_configure(container, cfg):
    docker_util.exec_safely(container, "mkdir /wodin/root")
    subprocess.call(["mkdir", "-p", "./proxyIndexPage"])
    sites = cfg.sites
    html_strings = create_index_page(sites)
    index_file = open("./proxyIndexPage/index.html", "w")
    index_file.writelines(html_strings)
    index_file.close()
    subprocess.call(["docker", "cp", "./proxyIndexPage/index.html", "epimodels-wodin-proxy:/wodin/root"])


def wodin_proxy_container(cfg):
    wodin_proxy = cfg.wodin_proxy
    sites = cfg.sites
    container_prefix = cfg.container_prefix
    wodin = cfg.wodin
    site_args = []
    for site in sites.keys():
        site_args.append("--site")
        url_path = sites[site]["urlPath"]
        container_name = "{}-{}-{}".format(container_prefix, wodin["name"], site)
        site_args.append("{}={}:3000".format(url_path, container_name))
    args = ["localhost"] + site_args
    ports = [wodin_proxy["port_http"], wodin_proxy["port_https"]]
    return ConstellationContainer(
        wodin_proxy["name"],
        wodin_proxy["ref"],
        ports=ports,
        args=args,
        configure=proxy_configure,
        network=cfg.network
    )
