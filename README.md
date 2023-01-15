# gitzip

Export all the changed files between two git commits or branches to a zip file including
the directory structure.

## gitzip usage

Navigate into your repositorys base directory. Then execute the following command.

```
python -m gitzip export.zip 0c321f2 master
```

This will create a `export.zip` file containing all files that changed between commit
`0c321f2` and the current `master` branch. The files will have the contents of the
current branch/commit that is checked out in your current repository. If the changed
files are in a subdirectory, this subdirectory is created in the zip file.

## Installation

### Via `pip`

```bash
pip install gitzip
```

### From source
To run this program from the code directly, [`python`](https://www.python.org/) and
[`poetry`](https://python-poetry.org/) (`pip install poetry`) are required. Clone or
download the repository.

To install all the dependencies, use your command line and navigate to the directory
where this `README` file is located in. Then run

```bash
poetry install
```

### For development

For development installation perform the [From source](#from-source) installation.

For installing new packages, always run
```
poetry add <pip-package-name>
```
instead of `pip install <pip-package-name>`.

Launch the program either check out the [Execution](#execution) section or use the
*Run and Debug*-side panel of VSCode.

If the interpreter of the virtual environment does not show up in VSCode, add it manually. The virtual environments are located in `{cache-dir}/virtualenvs/<venv-name>/Scripts/python.exe` where the [`{cache-dir}`](https://python-poetry.org/docs/configuration/#cache-dir) depends on the operating system (`~/.cache/pypoetry`, `~/Library/Caches/pypoetry` or `C.\Users\%USERNAME%\AppData\Local\pypoetry\Cache`).

## Execution

To execute the program use
```bash
poetry run python -m gitzip
```
