# gitzip

Export all the changed files between two git commits or branches to a zip file including
the directory structure.

## gitzip usage

`gitzip` allows to copy all files that changed between two commits (or branches) into a
zip file.

Expect a git repository being at commit `0c321f2`. If two new files are created, e.g.
`README.md` and `docs/screenshot.jpg`, `git status` gives:

```bash
$ git status
On branch master

Changes not staged for commit:
  (use "git add <file>..." to update what will be committed)
  (use "git restore <file>..." to discard changes in working directory)
        modified:   README.md
        new:        docs/screenshot.jpg

```

After committing those changes, the command

```
python -m gitzip export.zip 0c321f2
```

will create a `export.zip` file. This file contains all files that changed between commit
`0c321f2` and the current `master` branch. So in the given example, the zip file will
have the following structure:

```
📦export.zip
 ┣ 📂docs
 ┃ ┗ 📜screenshot.jpg
 ┗ 📜README.md
```

The files will have the contents that are currently checked out in the repository.

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
