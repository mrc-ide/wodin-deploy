from wodin_deploy.config import WodinConfig

import constellation


def test_create_config():
    dat = { "sites": { "/": { "github": "mrc-ide/wodin-demo" } } }
    cfg = WodinConfig(dat)
    assert cfg.network == "wodin-network"
    assert cfg.volumes == {
        "redis": "redis-data", "wodin": "wodin-data", "proxy": "proxy-data"}
