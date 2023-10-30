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
    assert cfg.redis["image_name"] == "redis"
    assert str(cfg.redis["ref"]) == "library/redis:6.0"
    assert cfg.redis["container_name"] == "redis"
    assert cfg.redis["full_container_name"] == "test-prefix-redis"

    assert cfg.odin_api["image_name"] == "odin-image"
    assert str(cfg.odin_api["ref"]) == "test-repo/odin-image:main"
    assert cfg.odin_api["container_name"] == "api"
    assert cfg.odin_api["full_container_name"] == "test-prefix-api"

    assert cfg.wodin["image_name"] == "wodin"
    assert str(cfg.wodin["ref"]) == "test-repo/wodin:main"
    assert cfg.wodin["container_name"] == "wodin"
    assert cfg.wodin["full_container_name"] == "test-prefix-wodin"

    assert cfg.wodin_proxy["image_name"] == "wodin-proxy"
    assert str(cfg.wodin_proxy["ref"]) == "test-repo/wodin-proxy:main"
    assert cfg.wodin_proxy["container_name"] == "wodin-proxy"
    assert cfg.wodin_proxy["full_container_name"] == "test-prefix-wodin-proxy"
    assert cfg.wodin_proxy["port_http"] == 80
    assert cfg.wodin_proxy["port_https"] == 443
    assert cfg.wodin_proxy["ssl_certificate"] == "test-cert"
    assert cfg.wodin_proxy["ssl_key"] == "test-key"


def test_config_basic_no_ssl():
    cfg = WodinConfig("config/testNoSSL")
    assert cfg.wodin_proxy["port_http"] == 80
    assert cfg.wodin_proxy["port_https"] == 443
    assert "ssl_certificate" not in cfg.wodin_proxy
    assert "ssl_key" not in cfg.wodin_proxy
