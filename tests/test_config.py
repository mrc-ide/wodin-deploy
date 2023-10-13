from wodin_deploy.config import WodinConfig


def test_config_basic():
    cfg = WodinConfig("config/test")
    assert cfg.network == "test-network"
    assert cfg.repo == "test-repo"
    assert cfg.container_prefix == "test-prefix"
    assert cfg.sites == {
        "demo": {
            "url": "https://github.com/mrc-ide/wodin-demo-config",
            "ref": "main",
            "urlPath": "demo",
            "description": "test desc for demo",
        },
        "shortcourse": {
            "url": "https://github.com/mrc-ide/wodin-shortcourse-2023",
            "ref": "main",
            "urlPath": "shortcourse",
            "description": "test desc for shortcourse",
        },
    }
    assert cfg.redis["name"] == "redis"
    assert str(cfg.redis["ref"]) == "library/redis:6"
    assert cfg.odin_api["name"] == "odin.api"
    assert str(cfg.odin_api["ref"]) == "test-repo/odin.api:main"
    assert cfg.wodin["name"] == "wodin"
    assert str(cfg.wodin["ref"]) == "test-repo/wodin:main"
    assert cfg.wodin_proxy["name"] == "wodin-proxy"
    assert str(cfg.wodin_proxy["ref"]) == "test-repo/wodin-proxy:latest"
    assert cfg.wodin_proxy["port_http"] == 80
    assert cfg.wodin_proxy["port_https"] == 443
