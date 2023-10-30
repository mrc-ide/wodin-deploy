# Wodin Deploy

[![PyPI - Version](https://img.shields.io/pypi/v/wodin-deploy.svg)](https://pypi.org/project/wodin-deploy)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/wodin-deploy.svg)](https://pypi.org/project/wodin-deploy)

-----

## Installing packages
Hatch will automatically install and sync dependencies whenever you run any
```commandline
hatch run ...
```
command

## Testing
### To run all
```commandline
hatch run test
```

### To run within directory
```commandline
hatch run test ./directory/
```

### To run within file
```commandline
hatch run test ./path/to/file/test_file.py
```

### To run specific tests
```commandline
hatch run tests ./test_file_1.py::test_name_1 ./test_file_2.py::test_name_2
```

-----

## Moving parts

**NOTE: this documentation describes the state that the deployment tool will reach once fully implemented, not what currently is implemented**

A wodin deployment consists of one or more sites, and a site consists of one or more apps. The deployment requires a number of components:

* A proxy, we're going to use nginx [with some utilities](https://github.com/mrc-ide/wodin-proxy) to make setup easier. This is for TLS termination, and routing between different sites
* A redis sever, used for storing persistent state. One is sufficient for a deployment of several sites
* An [`odin.api`](https://mrc-ide.github.io/odin.api) server, used to compile [`odin`](https://mrc-ide.github.io/odin) DSL code into JavaScript; one is sufficient unless we later support either load balancing or multiple versions at once
* Several copies of [wodin](https://github.com/mrc-ide/wodin) itself, each corresponding to a site and pointing at a different source repository.

There are several bits of persistent data required here:

* proxy: the [proxy image](https://github.com/mrc-ide/wodin-proxy) that we use will serve an index page mounted into the proxy container. Practically we're only interested in an index page here and the deploy tool might create that itself, in which case it does not need to persist.
* redis: this requires a volume that will persist between deployments as this holds information about restorable sessions. This is just a case of creating a volume and mounting this into the redis container.
* odin.api: does not need any persistent state
* wodin: the most complex persistent data is each of the site configurations, which are themselves a git repository, see below for details.

For wodin's state, we need copies of each site's configuration. Each site lives in its own git repository, with `wodin.config.json`, `index.html` and `apps/` at its root. For an example see [`mrc-ide/wodin-demo-config`](https://github.com/mrc-ide/wodin-demo-config). For a multi-site deployment, the wodin volume will look like:

```
site-1/
  .git/
  apps/
  wodin.config.json
site-2/
  .git/
  apps/
  wodin.config.json
```

The deploy tool will be responsible for updating the content of these site directories. Similar to submodules, they will be checked out in headless mode so that they can be easily pointed to any remote branch or reference (they don't really exist on the host filesystem so we do not imagine that any direct editing will take place). The wodin image has an `update-sites` script that will be used to set this directory up, and the deploy tool will simply call it with the upstream repository url, path within the configuration volume, and desired git reference.

## Configuration

An example configuration might look like

```
wodin:
  msc-idm-2022:
    github: mrc-ide/wodin-msc-idm-2022
    ref: main
    description: >-
      The 2022 MSc course
  malawi-idm-2022:
    github: mrc-ide/wodin-malawi-idm-2022
    ref: main
    description: >-
      Infectious Disease Modelling with a focus on Malaria, run in Malawi
  demo:
    github: mrc-ide/wodin-demo
    ref: main
    description: >-
      A demo of core app types and configuration

proxy:
  hostname: epimodels.dide.ic.ac.uk
  ssl:
    certificate: VAULT:secret/wodin/ssl/epimodels:cert
    key: VAULT:secret/wodin/ssl/epimodels:key

vault:
  addr: https://vault.dide.ic.ac.uk:8200
  auth:
    method: github
```

Here, the `vault` section is constellation's usual vault access configuration, and the proxy section is fairly self explanatory (we might also support bringing the proxy up without ssl for testing - this is supported in the image and could be enabled by setting `ssl: ~` or `ssl: false`). For the main `wodin` block, each site is listed as a top-level key corresponding to the path (so `https://epimodels.dide.ic.ac.uk/msc-idm-2022` is the site corresponding to the first object in this section). For each site we need to know where the repository is found on github, the reference to use (defaulting to `main`) and perhaps a description (which we could use to build an index page automatically for the proxy).

## Installation

```console
pip install wodin-deploy
```

## License

`wodin-deploy` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
