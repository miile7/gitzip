from argparse import ArgumentParser, Namespace
from logging import DEBUG, INFO, WARNING, Logger, basicConfig, getLogger
from os import getcwd
from pathlib import Path
from re import compile
from subprocess import PIPE, Popen
from typing import Iterable, List, Optional, Tuple, TypedDict, Union
from typing_extensions import Unpack
from zipfile import ZIP_DEFLATED, ZipFile

from gitzip.version import get_version
from gitzip.static import NAME, SLUG


DEFAULT_LOG_LEVEL = WARNING

GIT_VERSION_REGEXP = compile(r"git\s*version((?:[\d]+\.){2}[\d]+)")
GIT_BRANCH_SHOW_CURRENT_MIN_VER = (2, 22)
CURRENT_HEAD_SYMBOLS = ("HEAD", )

EXIT_CODE_NOT_ENOUGH_ARGUMENTS = 2
EXIT_CODE_FILE_EXISTS = 4


logger = getLogger(SLUG)


class ParserArgs(TypedDict, total=False):
    zip_path: Path
    commit: str
    commit2: str
    text_file: Path
    force: bool


class MissingToCommitException(Exception):
    pass


class VersionNotFound(Exception):
    pass


def exec(cmd: List[str]) -> str:
    logger.info(f"Executing '{' '.join(cmd)}'")
    process = Popen(cmd, stdout=PIPE)

    if process.stdout is None:
        raise Exception(
            f"Could not grab output of command '{' '.join(cmd)}'. This cannot be fixed "
            "without touching the code."
        )

    out = process.stdout.read().decode("utf-8")
    logger.info(f"Command showed:\n$ {' '.join(cmd)}\n{out}")

    return out


def get_git_version() -> Tuple[int, ...]:
    logger.info("Retrieving git version")

    version_output = exec(["git", "--version"])

    match = GIT_VERSION_REGEXP.match(version_output)
    if match is None:
        raise VersionNotFound("Could not find git version.")

    version_str = match.group(1)
    return tuple(map(int, version_str.split(".")))


def get_current_branch() -> str:
    git_version: Tuple[int, ...]
    try:
        git_version = get_git_version()
    except (VersionNotFound, IndexError) as e:
        logger.warning(e)
        git_version = (0, 0, 0)

    cmd: List[str]
    if (
        len(git_version) >= len(GIT_BRANCH_SHOW_CURRENT_MIN_VER) and
        git_version[0] > GIT_BRANCH_SHOW_CURRENT_MIN_VER[0] and
        git_version[1] > GIT_BRANCH_SHOW_CURRENT_MIN_VER[1]
    ):
        cmd = ["git", "branch", "--show-current"]
    else:
        cmd = ["git", "rev-parse", "--abbrev-ref", "HEAD"]

    return exec(cmd).strip()


def get_current_commit() -> str:
    return exec(["git", "rev-parse", "HEAD"]).strip()


def get_files_from_git(commit: str, commit2: Optional[str]) -> Iterable[str]:
    cmd: List[str] = ["git", "diff", commit]

    if commit2:
        cmd.append(commit2)

    cmd += ["--name-only"]

    out = exec(cmd)

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
        if not args.commit:
            raise MissingToCommitException(
                "No commit is given and no text file is specified."
            )

        if args.commit:
            zip_comment = f"Files from git diff {args.commit}..{args.commit2}"
        else:
            zip_comment = f"Files from git diff HEAD..{args.commit}"

        if args.commit2:
            current_branch: str
            try:
                current_branch = get_current_branch()
            except Exception as e:
                logger.exception(e)
                current_branch = ""

            current_commit: str
            try:
                current_commit = get_current_commit()
            except Exception as e:
                logger.exception(e)
                current_commit = ""

            if (
                args.commit2 not in CURRENT_HEAD_SYMBOLS and
                args.commit2 not in current_commit and
                args.commit2 != current_branch
            ):
                logger.warn(
                    f"Note: The files are taken from the current file tree, NOT from "
                    "the git repository. If the commit2 is not the same as your "
                    "HEAD (the current files in your repository) this means, that the "
                    "diff is determined by the commit2 but the files content is still "
                    "taken from the current HEAD."
                )

        files = get_files_from_git(args.commit, args.commit2)

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
        "commit",
        help=(
            "The first reference (commit, branch, ...) to compare against, ignore this "
            "for text mode (-t)."
        ),
        type=str,
        nargs="?",
    )
    parser.add_argument(
        "commit2",
        help=(
            "The second reference (commit, branch, ...) to compare against, if not "
            "given, HEAD is used, ignore this for text mode (-t)."
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
        print(f"gitzip: error: {e} Either specify -t or commit.")
        exit(EXIT_CODE_NOT_ENOUGH_ARGUMENTS)
    except FileExistsError as e:
        print(f"gitzip: error: {str(e)} Use -f to overwrite existing files.")
        exit(EXIT_CODE_FILE_EXISTS)


if __name__ == "__main__":
    main()
