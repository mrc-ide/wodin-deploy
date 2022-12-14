import constellation
import constellation.config as config

def wodin_config(path, config_name=None, options=None):
    dat = config.read_yaml("{}/wodin.yml".format(path))
    dat_full = config.config_build(path, dat, config_name, options=options)
    return WodinConfig(dat_full);


def clean_name(name):
    if name == "/":
        return "root"
    else:
        if name[0] == "/":
            name = name[1:]
        return name.replace("/", "-")


def validate_sites(sites):
    if "/" in sites.keys() and len(sites) > 1:
        raise Exception("If '/' is a site, there can be only one site")
    sites = sites.copy()
    for k, v in sites.items():
        if "github" not in v:
            raise Exception(f"Expected key 'github' for sites/{k}")
        if type(v["github"]) is not str:
            raise Exception(f"Expected string for sites/{k}/github")
        # Check for only [[:alnum:]/-] in path?
        v["name"] = clean_name(k)
        v["path"] = k
        v["container"] = f"wodin-{v['name']}"
    # later we'll add more keys, and we should test for unknown ones
    # here to avoid typo-related dismay.
    #
    # deploy_key: use a deploy key for a private repo?
    # path: use a local path?
    # odin_api_version: require a specific version of odin api
    # wodin_version: require a specific version of wodin
    # index: indicate if they should be in the main index or not
    return sites


class WodinConfig:
    def __init__(self, data):
        self.data = data
        ## We can make this stuff configurable, but it not a big deal
        ## if it's fixed really.
        self.network = "wodin-network"
        self.volumes = {
            "redis": "redis-data",
            "wodin": "wodin-data",
            "proxy": "proxy-data",
        }
        self.container_prefix = "wodin"
        self.redis_ref = constellation.ImageReference("library", "redis", "5.0")
        self.odin_api_ref = constellation.ImageReference("mrcide", "odin.api",
                                                         "latest")
        self.wodin_ref = constellation.ImageReference("mrcide", "wodin",
                                                      "latest")
        self.sites = validate_sites(config.config_dict(self.data, ["sites"]))

        containers = ["redis", "odin.api"] + \
            [v["container"] for v in self.sites.values()]
        self.containers = { k: k for k in containers }
