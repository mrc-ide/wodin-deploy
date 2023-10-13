from wodin_deploy.config import WodinConfig
from wodin_deploy.wodin_constellation import WodinConstellation
import docker
from constellation import docker_util


def get_site_container_name(site, cfg):
    return f"{cfg.container_prefix}-{cfg.wodin['name']}-{site}"


def test_start_and_stop():
    cfg = WodinConfig("config/epimodels")
    obj = WodinConstellation(cfg)
    obj.start()

    cl = docker.client.from_env()

    assert docker_util.network_exists(cfg.network)
    assert docker_util.volume_exists("redis-data")
    assert docker_util.volume_exists("wodin-config")

    assert docker_util.container_exists(f"{cfg.container_prefix}-api")
    assert docker_util.container_exists(f"{cfg.container_prefix}-redis")
    assert docker_util.container_exists(get_site_container_name("proxy", cfg))
    for site in cfg.sites.keys():
        assert docker_util.container_exists(get_site_container_name(site, cfg))

    containers = cl.containers.list()
    assert len(containers) == 3 + len(cfg.sites)

    obj.stop(kill=True, remove_volumes=True)
