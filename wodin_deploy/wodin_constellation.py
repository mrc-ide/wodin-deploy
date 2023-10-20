from constellation import Constellation, ConstellationContainer, ConstellationMount, docker_util


class WodinConstellation:
    def __init__(self, cfg):
        self.cfg = cfg
        redis = redis_container(cfg)
        odin_api = odin_api_container(cfg)
        sites = sites_containers(cfg)
        proxy = wodin_proxy_container(cfg)

        containers = [redis, odin_api, *sites, proxy]

        self.obj = Constellation(
            "wodin",
            cfg.container_prefix,
            containers,
            cfg.network,
            {"redis-data": "redis-data", "wodin-config": "wodin-config"},
            data=cfg,
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
    return ConstellationContainer(redis["name"], redis["ref"], mounts=redis_mounts, network=cfg.network)


def odin_api_container(cfg):
    odin_api = cfg.odin_api
    return ConstellationContainer("api", odin_api["ref"], network=cfg.network)


def get_wodin_container(cfg, site, site_dict):
    wodin = cfg.wodin
    wodin_mounts = [ConstellationMount("wodin-config", "/wodin/config")]
    container_name = f"{wodin['name']}-{site}"

    return ConstellationContainer(
        container_name,
        wodin["ref"],
        mounts=wodin_mounts,
        network=cfg.network,
        entrypoint=[
            "/wodin/docker/pull-site-and-start.sh",
            site_dict["ref"],
            site_dict["url"],
            f"/wodin/config/{site}",
            "--redis-url=redis://epimodels-redis:6379",
            "--odin-api=http://epimodels-api:8001",
            f"--base-url=http://localhost/{site_dict['urlPath']}",
            f"/wodin/config/{site}",
        ],
    )


def sites_containers(cfg):
    sites = cfg.sites
    wodin_containers = []
    for site in sites.keys():
        site_dict = sites[site]
        wodin_containers.append(get_wodin_container(cfg, site, site_dict))
    return wodin_containers


def create_index_page(sites):
    html_strings = [
        "<html>\n<head>\n<title>Wodin</title>\n</head>\n<body>\n",
        "<h1>Wodin</h1>\n",
        f"<p>There are {len(sites)} deployed configurations:</p>\n",
        "<ul>\n",
    ]
    for site in sites.keys():
        site_obj = sites[site]
        html_strings.append(
            "<li><a href='/{}'><code>{}</code></a>: {}</li>\n".format(
                site_obj["urlPath"], site, site_obj["description"]
            )
        )
    html_strings.append("</ul>\n</body>\n</html>")
    return "".join(html_strings)


def proxy_configure(container, cfg):
    docker_util.exec_safely(container, "mkdir /wodin/root")
    html_string = create_index_page(cfg.sites)
    docker_util.string_into_container(html_string, container, "/wodin/root/index.html")
    docker_util.exec_safely(container, "chmod +r /wodin/root/index.html")


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
        site_args.append(f"{url_path}={container_name}:3000")
    args = ["localhost", *site_args]
    ports = [wodin_proxy["port_http"], wodin_proxy["port_https"]]
    return ConstellationContainer(
        wodin_proxy["name"], wodin_proxy["ref"], ports=ports, args=args, configure=proxy_configure, network=cfg.network
    )
