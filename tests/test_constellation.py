import io
from contextlib import redirect_stdout

import docker
import pytest
from constellation import docker_util

from wodin_deploy.config import WodinConfig
from wodin_deploy.wodin_constellation import WodinConstellation


def get_site_container_name(site, cfg):
    return f"{cfg.wodin['full_container_name']}-{site}"


def pull_all_necessary_images(cl):
    cl.images.pull("library/redis:6.0")
    cl.images.pull("mrcide/odin.api:main")
    cl.images.pull("mrcide/wodin-proxy:main")
    cl.images.pull("mrcide/wodin:main")


@pytest.fixture
def start_constellation():
    cl = docker.client.from_env()
    pull_all_necessary_images(cl)

    cfg = WodinConfig("config/epimodels")
    obj = WodinConstellation(cfg)
    obj.start()
    yield cl, cfg, obj

    obj.stop(kill=True, remove_volumes=True)


def test_start_and_stop(start_constellation):
    cl, cfg, obj = start_constellation

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


def test_obj_status():
    cl = docker.client.from_env()
    pull_all_necessary_images(cl)

    cfg = WodinConfig("config/epimodels")
    obj = WodinConstellation(cfg)
    f = io.StringIO()
    with redirect_stdout(f):
        obj.status()

    def status_string(network_status):
        return f"""Constellation wodin
  * Network:
    - wodin-nw: {network_status}
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

    assert f.getvalue() == status_string("missing") or f.getvalue() == status_string("created")
