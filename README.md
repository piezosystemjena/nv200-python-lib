![logo](doc/_static/piezosystem_logo.svg)

# NV200 Python Lib

The NV200 Python library allow you to control the NV200 device from piezosystem Jena
via Python. The library supports the ethernet interface as well as the
USB interface of the device.

## Getting Started

### Installing poetry

If necessary, install [poetry] according to the official [installation instructions](https://python-poetry.org/docs/#installation) 
(it's recommended to use [pipx](https://github.com/pypa/pipx) to install poetry in its own isolated environment but still have
it available as a system wide command).

```shell
pip install pipx
pipx ensurepath
# reload your shell or start a new instance
pipx install poetry
```

### Setting up poetry to install dependencies in an in-project virtualenv (optional)

By default, poetry will create virtualenv in the `{cache-dir}/virtualenvs` directory 
(which for Windows is located in `%USERPROFILE%/AppData/Local/poetry/Cache`).
But it might be nicer to have the virtualenv close to the project source code in a 
`.venv` folder in the project root directory.

This can be achieved by setting the `virtualenvs.in-project` config option of poetry to `true`:

```shell
poetry config virtualenvs.in-project true
```

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

### Installing dependencies

#### Required dependencies

Run `poetry install` in this directory to install all dependencies necessary for running the 
examples:

```shell
poetry install
```

This will also install an editable version of the `nv200` library. If you don't want this, you can add the `--no-root` flag, which will then only install the dependencies, but not the `nv200` package itself:

```shell
poetry install --no-root
```


#### Optional dependencies

There are a couple of dependencies which are not strictly necessary to run the servers but may be nice to have.

You can install them all by running `poetry install` with the `--all-extras` flag or you can choose which extras to install by only specifying them using the `-E`/`--extras` flag

```shell
# installs all optional packages
poetry install --all-extras

# installs only selected optional packages
poetry install --extras "optional-pkg-1 optional-pkg-2"
poetry install -E optional-pkg-1 -E optional-pkg-2
```

## Building the wheel

To create an `pip` installable wheel for the `nv200` package simply run:

```shell
poetry build
```

This will create a wheel file in the `dist` folder than you can distribute for installation.

## Building the documentation

The `nv200` package uses the Sphinx documentation tool for building its [HTML documentation](doc/_build/html/index.html). To build the documentation in the `doc` folder there are two ways:

### Use poetry

You can build the documentation with poetry using the following command:

```shell
poetry run sphinx-build -b html doc/ doc/_build/
```

### Use Sphinx make

CD into the `doc` folder and execute `make html`.

```shell
cd doc
make html
```

[poetry]: https://python-poetry.org/


## Publishing to TestPypI

```shell
poetry build
poetry config repositories.test-pypi https://test.pypi.org/legacy/
poetry config pypi-token.test-pypi your-token-here
poetry publish -r test-pypi
```