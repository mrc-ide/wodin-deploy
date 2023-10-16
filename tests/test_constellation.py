import io
from contextlib import redirect_stdout

import docker
import pytest
from constellation import docker_util

from wodin_deploy.config import WodinConfig
from wodin_deploy.wodin_constellation import WodinConstellation, configure_wodin


def get_site_container_name(site, cfg):
    return f"{cfg.container_prefix}-{cfg.wodin['name']}-{site}"


def pull_all_necessary_images(cl):
    cl.images.pull("library/redis:6.0")
    cl.images.pull("mrcide/odin.api:main")
    cl.images.pull("mrcide/wodin-proxy:latest")
    cl.images.pull("mrcide/wodin:main")


def test_start_and_stop():
    cl = docker.client.from_env()
    pull_all_necessary_images(cl)

    cfg = WodinConfig("config/epimodels")
    obj = WodinConstellation(cfg)
    obj.start()

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


def test_obj_status():
    cl = docker.client.from_env()
    pull_all_necessary_images(cl)

    cfg = WodinConfig("config/epimodels")
    obj = WodinConstellation(cfg)
    f = io.StringIO()
    with redirect_stdout(f):
        obj.status()
    assert (
        f.getvalue()
        == """Constellation wodin
  * Network:
    - wodin-nw: created
  * Volumes:
    - redis-data (redis-data): missing
    - wodin-config (wodin-config): missing
  * Containers:
    - redis (epimodels-redis): missing
    - api (epimodels-api): missing
    - wodin-demo (epimodels-wodin-demo): missing
    - wodin-msc-idm-2022 (epimodels-wodin-msc-idm-2022): missing
    - wodin-msc-idm-2023 (epimodels-wodin-msc-idm-2023): missing
    - wodin-malawi-idm-2022 (epimodels-wodin-malawi-idm-2022): missing
    - wodin-gambia-idm-2023 (epimodels-wodin-gambia-idm-2023): missing
    - wodin-acomvec-2023 (epimodels-wodin-acomvec-2023): missing
    - wodin-infectiousdiseasemodels-2023 (epimodels-wodin-infectiousdiseasemodels-2023): missing
    - wodin-proxy (epimodels-wodin-proxy): missing\n"""
    )


def test_wodin_throws_if_no_redis():
    cfg = WodinConfig("config/epimodels")
    cl = docker.client.from_env()
    x = cl.containers.run("alpine:latest", name=f"{cfg.container_prefix}-{cfg.redis['name']}", detach=True)
    with pytest.raises(Exception, match="Wodin could not connect to Redis"):
        configure_wodin(None, cfg)
    x.stop()
    x.remove()
