import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()
with open("VERSION", "r") as fh:
    version = fh.read()

setuptools.setup(
    name="gitzip",
    version=version,
    author="miile7",
    author_email="miile7@gmx.de",
    description=("A small python program to export files changed between " + 
                 "git commits or branches to a zip file retaining the " + 
                 "directory structure."),
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/miile7/gitzip",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)",
    ],
    python_requires='>=3.7',
)