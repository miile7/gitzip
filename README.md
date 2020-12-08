# gitzip

Export all the changed files between two git commits or branches to a zip file including 
the directory structure.

## Usage

Navigate into your repositorys base directory. Then exeucte the following command.

```
python -m gitzip export.zip 0c321f2 master
```

This will create a `export.zip` file containing all files that changed between commit 
`0c321f2` and the current `master` branch. The files will have the contents of the current
`master`. If the changed files are in a directory, this directory is created in the zip 
file.

## Installation

To install use pythons package index:

```
python -m pip install gitzip
```

## License

This program can be used by anyone since it is licensed under 
[Mozilla Public License Version 2.0](https://www.mozilla.org/en-US/MPL/2.0/).