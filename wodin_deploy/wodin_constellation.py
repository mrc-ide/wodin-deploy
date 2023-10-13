import subprocess
import time

import docker
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


def cmd(*args):
    subprocess.call(*args)  # noqa: S603


def redis_container(cfg):
    redis = cfg.redis
    redis_mounts = [ConstellationMount("redis-data", "/data")]
    return ConstellationContainer(redis["name"], redis["ref"], mounts=redis_mounts)


def odin_api_container(cfg):
    odin_api = cfg.odin_api
    return ConstellationContainer("api", odin_api["ref"])


def get_preconfigure(site, container_name, container_prefix):
    return lambda *_: cmd(
        ["docker", "cp", "./siteConfigs/" + site, container_prefix + "-" + container_name + ":/wodin/config/" + site]
    )


def configure_wodin(_, cfg):
    for _i in range(0, 10):
        cl = docker.client.from_env()
        redis = cl.containers.get(f"{cfg.container_prefix}-{cfg.redis['name']}")
        if "Ready to accept connections" in redis.logs().decode("utf-8"):
            break
        time.sleep(1)


def get_wodin_container(cfg, site, path):
    wodin = cfg.wodin
    container_prefix = cfg.container_prefix
    wodin_mounts = [ConstellationMount("wodin-config", "/wodin/config")]
    container_name = wodin["name"] + "-" + site
    return ConstellationContainer(
        container_name,
        wodin["ref"],
        mounts=wodin_mounts,
        args=[
            "--redis-url=redis://epimodels-redis:6379",
            "--odin-api=http://epimodels-api:8001",
            "--base-url=http://localhost/" + path,
            "/wodin/config/" + site,
        ],
        configure=configure_wodin,
        preconfigure=get_preconfigure(site, container_name, container_prefix),
    )


def sites_containers(cfg):
    sites = cfg.sites
    cmd(["rm", "-rf", "./siteConfigs"])
    cmd(["mkdir", "./siteConfigs"])
    wodin_containers = []
    for site in sites.keys():
        cmd(["mkdir", f"./siteConfigs/{site}"])
        site_dict = sites[site]
        cmd(["git", "clone", "--branch=" + site_dict["ref"], site_dict["url"], f"./siteConfigs/{site}"])
        wodin_containers.append(get_wodin_container(cfg, site, site_dict["urlPath"]))
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
    return html_strings


def proxy_configure(container, cfg):
    docker_util.exec_safely(container, "mkdir /wodin/root")
    cmd(["mkdir", "-p", "./proxyIndexPage"])
    sites = cfg.sites
    html_strings = create_index_page(sites)
    index_file = open("./proxyIndexPage/index.html", "w")
    index_file.writelines(html_strings)
    index_file.close()
    cmd(["docker", "cp", "./proxyIndexPage/index.html", "epimodels-wodin-proxy:/wodin/root"])


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
