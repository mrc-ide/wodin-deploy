import constellation
from constellation import config


class WodinConfig:
    def __init__(self, path, extra=None, options=None):
        dat = config.read_yaml(f"{path}.yml")
        dat = config.config_build(path, dat, extra, options)
        self.dat = dat
        self.repo = config.config_string(dat, ["repo"])
        self.path = path
        self.vault = config.config_vault(dat, ["vault"])
        self.network = config.config_string(dat, ["network"])
        self.container_prefix = config.config_string(dat, ["container_prefix"])
        self.sites = config.config_dict(dat, ["sites"])

        # redis
        self.redis = self.get_base_config("redis")

        # odin.api
        self.odin_api = self.get_base_config("odin.api")

        # wodin-proxy
        self.wodin_proxy = self.get_base_config("wodin-proxy")
        self.wodin_proxy["port_http"] = config.config_integer(dat, ["wodin-proxy", "port_http"])
        self.wodin_proxy["port_https"] = config.config_integer(dat, ["wodin-proxy", "port_https"])
        self.proxy_ssl_self_signed = "ssl" not in dat["wodin-proxy"]
        if not self.proxy_ssl_self_signed:
            self.wodin_proxy["ssl_certificate"] = config.config_string(dat, ["wodin-proxy", "ssl", "certificate"])
            self.wodin_proxy["ssl_key"] = config.config_string(dat, ["wodin-proxy", "ssl", "key"])

        # wodin
        self.wodin = self.get_base_config("wodin")

        # self.vault = config.config_vault(dat, ["vault"])

    def build_ref(self, section):
        name = self.get_name(section)
        if "repo" in self.dat[section]:
            repo = config.config_string(self.dat, [section, "repo"])
        else:
            repo = self.repo
        ref = config.config_string(self.dat, [section, "ref"])
        return constellation.ImageReference(repo, name, ref)

    def get_name(self, section):
        if "name" in self.dat[section]:
            return config.config_string(self.dat, [section, "name"])
        else:
            return section

    def get_base_config(self, section):
        return {"ref": self.build_ref(section), "name": self.get_name(section)}
