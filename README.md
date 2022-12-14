# wodin-deploy

[![PyPI - Version](https://img.shields.io/pypi/v/wodin-deploy.svg)](https://pypi.org/project/wodin-deploy)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/wodin-deploy.svg)](https://pypi.org/project/wodin-deploy)

-----

A wodin instance requires a number of components

* A proxy, we're going to use nginx. This is for TLS termination, and routing between different apps
* A redis sever, used for storing persistant state. One is sufficient for a deployment
* An [`odin.api`](https://mrc-ide.github.io/odin.api) server, used to compile [`odin`](https://mrc-ide.github.io/odin) DSL code into JavaScript
* Several copies of wodin, each pointing at a different repo. If more than one wodin is running, each runs at some path on the server.

## Packaging and development

This is built on hatch, which is this week's python packing framework, backward compatible with some unknown fraction of the other thousand frameworks, and perhaps usable for some small amount of common tasks. We'll see!

The docs are [here](https://hatch.pypa.io/latest/build/) but don't seem to be very comprehensive or useful, so expand this doc as we work out how to do basic housekeeping chores that most sytems make obvious.

Run the tests with:

```
hatch run cov
```

Run a specific test

```
hatch run test tests/test_file.py::test_name
```

## Installation

Nominally,

```
pip install wodin-deploy
```

But practically probably

```
pip3 install --user wodin-deploy
```

possibly with `--upgrade` if you want the installation to replace an existing one rather than appearing to run but then actually doing nothing. We're not yet on pypi, so for now you'll have to install from the command line after a clone, which is an exercise left to the reader.

## License

`wodin-deploy` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
