from argparse import ArgumentParser, Namespace
from logging import DEBUG, INFO, WARNING, Logger, basicConfig, getLogger
from os import getcwd
from pathlib import Path
from subprocess import PIPE, Popen
from typing import Iterable, List, Optional, TypedDict, Union
from typing_extensions import Unpack
from zipfile import ZIP_DEFLATED, ZipFile

from gitzip.version import get_version
from gitzip.static import NAME, SLUG


DEFAULT_LOG_LEVEL = WARNING

EXIT_CODE_NOT_ENOUGH_ARGUMENTS = 2
EXIT_CODE_FILE_EXISTS = 4


logger = getLogger(SLUG)


class ParserArgs(TypedDict, total=False):
    zip_path: Path
    from_commit: str
    to_commit: str
    text_file: Path
    force: bool


class MissingToCommitException(Exception):
    pass


def get_files_from_git(from_commit: Optional[str], to_commit: str) -> Iterable[str]:
    cmd: List[str] = ["git", "diff"]

    if from_commit:
        cmd.append(from_commit)

    cmd += [to_commit, "--name-only"]

    logger.info(f"Executing '{' '.join(cmd)}'")
    process = Popen(cmd, stdout=PIPE)

    if process.stdout is None:
        raise Exception(
            "Could not grab output of git command. This cannot be fixed without "
            "touching the code"
        )

    out = process.stdout.read().decode("utf-8")
    logger.info(f"Command showed:\n$ {' '.join(cmd)}\n{out}")

    # remove empty inputs, split the output
    return filter(lambda x: x != "", out.split("\n"))


def expand_path(path: str) -> Path:
    return Path(path).expanduser().resolve()


def create_zip_file(
    files: Iterable[str], zip_path: Path, zip_comment: str, overwrite: bool
) -> None:
    if not overwrite and zip_path.exists():
        raise FileExistsError(f"The file {zip_path} exists already.")

    logger.info(f"Creating zip file {zip_path}")
    zip_file = ZipFile(zip_path, "w", compression=ZIP_DEFLATED)
    zip_file.comment = bytes(zip_comment, "utf-8")

    print("Creating zip file...")

    rel_path = Path(getcwd()).resolve()
    logger.debug(f"Copying file structure relative to parent {rel_path}")
    for source_path in files:
        absolute_source_path = expand_path(source_path)

        is_relative: bool
        target_path: Union[str, Path]
        if rel_path in absolute_source_path.parents:
            is_relative = True
            target_path = absolute_source_path.relative_to(rel_path)
            logger.debug(f"File {source_path} is child of parent {rel_path}")
        else:
            is_relative = False
            target_path = absolute_source_path.name
            logger.debug(f"File {source_path} is NOT a child of parent {rel_path}")

        if absolute_source_path.is_file():
            if not is_relative:
                print(
                    f"  M '{absolute_source_path}' - File is absolute, copying to zip "
                    "root"
                )
            zip_file.write(absolute_source_path, target_path)
            print(f"  S '{absolute_source_path}' - Successfully added.")
        else:
            print(
                f"  F '{absolute_source_path}' - File does not exist (eventually a "
                "commit deleted it?) or is a directory."
            )

    zip_file.close()


def run(args: Namespace) -> None:
    files: Iterable[str] = []
    zip_comment: str
    if args.text_file:
        logger.info(f"Loading text file {args.text_file}")
        zip_comment = f"Files from {args.text_file}"

        files = open(args.text_file, "r", encoding="utf-8")
    else:
        logger.info("Taking files from git diff")
        if not args.to_commit:
            raise MissingToCommitException(
                "No to_commit is given and no text file is specified."
            )

        if args.from_commit:
            zip_comment = f"Files from git diff {args.from_commit}..{args.to_commit}"
        else:
            zip_comment = f"Files from git diff HEAD..{args.to_commit}"

        files = get_files_from_git(args.from_commit, args.to_commit)

    if Logger.root.level <= INFO:
        files = tuple(files)
        logger.info(f"Found {len(files)} files")

    create_zip_file(files, args.zip_path, zip_comment, args.force)


def get_arg_parser() -> ArgumentParser:
    parser = ArgumentParser(prog=SLUG, description=NAME)

    parser.add_argument(
        "--version", "-V", action="version", version=f"{SLUG}, version {get_version()}"
    )
    parser.add_argument(
        "-v",
        "--verbose",
        dest="log_level",
        help="Set the loglevel to INFO",
        action="store_const",
        const=INFO,
        default=DEFAULT_LOG_LEVEL,
    )
    parser.add_argument(
        "-vv",
        "--very-verbose",
        dest="log_level",
        help="Set the loglevel to DEBUG",
        action="store_const",
        const=DEBUG,
    )
    parser.add_argument(
        "zip_path",
        help=(
            "The path to the zip file to create (with extension), can be relative to "
            "the current working directory."
        ),
        type=Path,
    )
    parser.add_argument(
        "to_commit",
        help=("The end commit or branch to compare against, ignore in text mode (-t)."),
        type=str,
        nargs="?",
    )
    parser.add_argument(
        "from_commit",
        help=(
            "The starting commit or branch to compare against, ignore in text mode "
            "(-t)."
        ),
        type=str,
        nargs="?",
    )
    parser.add_argument(
        "-t",
        "--text-mode",
        "--txt",
        "--text-file",
        dest="text_file",
        help=(
            "Switch to the txt file mode (second usage). This is the path to a text "
            "file containing paths defining the files to add to the zip file. All paths"
            " must be relative to the current working directory, ignored if -t is off."
        ),
        type=Path,
    )
    parser.add_argument(
        "-f",
        "--force",
        help="Overwrite the zip file if it exists already",
        default=False,
        action="store_true",
    )

    return parser


def init_logging(args: Namespace) -> None:
    if args.log_level < INFO:
        log_format = "[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
    else:
        log_format = "%(levelname)s: %(message)s"

    basicConfig(level=args.log_level, format=log_format, datefmt="%Y-%m-%d %H:%M:%S")


def main(**kwargs: Unpack[ParserArgs]) -> None:
    parser = get_arg_parser()
    if len(kwargs) > 0:
        args = Namespace(**kwargs)
    else:
        args = parser.parse_args()

    init_logging(args)

    try:
        run(args)
    except MissingToCommitException as e:
        parser.print_usage()
        print(f"gitzip: error: {e} Either specify -t or to_commit.")
        exit(EXIT_CODE_NOT_ENOUGH_ARGUMENTS)
    except FileExistsError as e:
        print(f"gitzip: error: {str(e)} Use -f to overwrite existing files.")
        exit(EXIT_CODE_FILE_EXISTS)


if __name__ == "__main__":
    main()
