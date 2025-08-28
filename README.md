![logo](doc/_static/piezosystem_logo.svg)


# NV200 Python Lib

[![PyPI version](https://img.shields.io/pypi/v/nv200)](https://pypi.org/project/nv200/)
[![Python Version](https://img.shields.io/pypi/pyversions/nv200)](https://www.python.org/downloads/)
[![Docs](https://img.shields.io/badge/docs-online-success)](https://piezosystemjena.github.io/nv200-python-lib/)
[![Publish Documentation](https://github.com/piezosystemjena/nv200-python-lib/actions/workflows/deploy-doc.yml/badge.svg)](https://github.com/piezosystemjena/nv200-python-lib/actions/workflows/deploy-doc.yml)
[![Publish Python Package](https://github.com/piezosystemjena/nv200-python-lib/actions/workflows/publish-pypi.yml/badge.svg)](https://github.com/piezosystemjena/nv200-python-lib/actions/workflows/publish-pypi.yml)


The NV200 Python library allows you to control the [NV200/D piezo controller](https://www.piezosystem.com/product/nv-200-d-compact-amplifier/) from [piezosystem Jena](https://www.piezosystem.com) via Python.
The library supports the ethernet interface as well as the USB interface of the device.

![NV200](doc/images/nv200.jpg)

## Features

- Asynchronous communication via `aioserial` and `telnetlib3`
- Simple Pythonic interface for device control
- Query & set device position
- Supports NV200 data recorder functionality
- Easy interface for NV200 waveform generator


## For Users

### 📦 Quick Install

The NV200 library is available via [PyPI](https://pypi.org/project/nv200/) - the Python Package Index. To install the library, simply use pip:

```shell
pip install nv200
```


### 📚 Documentation 

Comprehensive documentation—including API reference, installation options, and usage examples—is available here:

[https://piezosystemjena.github.io/nv200-python-lib/](https://piezosystemjena.github.io/nv200-python-lib/)


### 🧪 Quick Example

```python
import asyncio
from nv200.nv200_device import NV200Device
from nv200.shared_types import PidLoopMode
from nv200.connection_utils import connect_to_single_device


async def main_async():
    """
    Moves the device to a specified position using closed-loop control.
    """
    dev = await connect_to_single_device(NV200Device)
    print(f"Connected to device: {dev.device_info}")

    await dev.move_to_position(20)
    await asyncio.sleep(0.2)
    print(f"Current position: {await dev.get_current_position()}")

    # instead of using move_to_position, you can also use two separate commands
    # to set the PID mode and the setpoint
    await dev.set_pid_mode(PidLoopMode.CLOSED_LOOP)
    await dev.set_setpoint(0)
    await asyncio.sleep(0.2)
    print(f"Current position: {await dev.get_current_position()}")


if __name__ == "__main__":
    asyncio.run(main_async())
```

## For Developers

This project uses [Poetry](https://python-poetry.org/) for Python dependency management, packaging, and publishing. Poetry provides a modern, streamlined alternative to `pip` and `virtualenv`, handling everything from installing dependencies to building and publishing the package.

If you're contributing to the project or running it locally for development, the steps below will help you set up your environment.

### 📥 Installing poetry

If necessary, install [poetry] according to the official [installation instructions](https://python-poetry.org/docs/#installation) 
(it's recommended to use [pipx](https://github.com/pypa/pipx) to install poetry in its own isolated environment but still have it available as a system wide command). If you already have installed and configured poetry,
you can skip this step.

```shell
pip install pipx
pipx ensurepath
```

Now reload your shell or create a new instance and execute the following steps:

```shell
pipx install poetry
poetry self add "poetry-dynamic-versioning[plugin]"
poetry config virtualenvs.in-project true
```

#### Some background information about poetry config

By default, Poetry creates virtual environments in `{cache-dir}/virtualenvs`
(Windows: `%USERPROFILE%/AppData/Local/pypoetry/Cache/virtualenvs`).

You can instead configure Poetry to create the virtual environment inside the project directory by setting:

```shell
poetry config virtualenvs.in-project true
```

This will place the virtualenv in a `.venv` folder at the project root the next time you run `poetry install`.

Now, when we run `poetry install` in a project directory, it will create and install all dependencies 
(and the project itself) into an in-project virtualenv located in `{project-root}/.venv`.

> **Note:**  
> If you already have an existing environment in the default location (i.e. out-of-project) and would like to convert to an in-project virtualenv, you have to first remove the existing virtualenv, ensure that the `virtualenvs.in-project` option is set to `true` and then create the new in-project virtualenv using `poetry install` (see [below](#installing-dependencies)) again.
> 
> To remove the existing virtualenv, first get its name and then remove it:
> 
> ```shell
> poetry env list   # note the name of the environment
> poetry env remove <name>
> ```
> 
> If you're sure you only have one environment, you can also just use `poetry env remove --all`.

### 📦 Installing dependencies

#### Required dependencies

To install all required dependencies and set up the project in editable mode use:

```shell
poetry install
```

To skip installing the project itself (i.e. install only dependencies):

```shell
poetry install --no-root
```

#### Optional dependencies

Some extra features are provided via optional dependencies.

- Install all **optional packages**:

```shell
poetry install --all-extras
```

- Install **specific extras**:

```shell
poetry install --extras "extra1 extra2"
# or
poetry install -E extra1 -E extra2
```

## Building and Publishing

### Build the Wheel

To build a distributable `.whl` package:

```shell
poetry build
```

This creates a `.whl` and `.tar.gz` file in the `dist/` directory.

### Publishing 

#### To TestPyPI

```shell
poetry build
poetry config repositories.test-pypi https://test.pypi.org/legacy/
poetry config pypi-token.test-pypi your-token-here
poetry publish -r test-pypi
```

#### To PyPI

```shell
poetry build
poetry config repositories.pypi https://upload.pypi.org/legacy/
poetry config pypi-token.pypi your-token-here
poetry publish -r test-pypi
```

## Building the documentation

Documentation is generated using [Sphinx](https://www.sphinx-doc.org/), located in the `doc/` folder.

### With Poetry

```shell
poetry run sphinx-build -b html doc/ doc/_build/
```

### With Make

```shell
cd doc
make html
```
