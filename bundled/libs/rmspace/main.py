"""Remove trailing whitespace from code and other plain-text files."""

import argparse
import mimetypes
import re
import sys
from pathlib import Path
from typing import Iterable, Sequence

# pylint: disable=unspecified-encoding


# Whitespace or tabs followed by newline or string end
_WHITESPACE_RE_PATTERN = re.compile(r"( |\t)+(?=$|\n)")


def _parse_args(args: Sequence[str]) -> argparse.Namespace:
    """Parse command-line arguments.

    Args:
        args (Sequence[str]): Command-line arguments.

    Returns:
        argparse.Namespace: Parsed arguments.

    """
    _PARSER = argparse.ArgumentParser()
    _PARSER.add_argument("paths", nargs="+", help="Paths to format", type=Path)

    _PARSER.add_argument("--check", action="store_true", help="Return 1 if any file was formatted.")

    return _PARSER.parse_args(args)


def _is_text_encoded(filename: Path) -> bool:
    """Determine if a file is encoded as plain text.

    Args:
        filename (Path): Filename to check.

    Returns:
        bool: True if the file has normal text encoding.

    """
    inferred_type = mimetypes.guess_type(filename)[0]
    return inferred_type is not None and inferred_type.startswith("text/")


def _iter_files(paths: Iterable[Path]) -> Iterable[Path]:
    """Iterate over all plain text files that can be recursively found in some paths.

    Args:
        paths (Iterable[Path]): Files or directories to search.

    Raises:
        FileNotFoundError: If a file is provided that doesn't exist.

    Yields:
        Path: A path that can be formatted.

    """
    for path in paths:
        if path.is_dir():
            yield from _iter_files(path.iterdir())
        elif path.is_file():
            if _is_text_encoded(path):
                yield path
        else:
            raise FileNotFoundError(f"Not found: {path}")


def format_str(content: str, pattern: str = _WHITESPACE_RE_PATTERN) -> str:
    if isinstance(pattern, str):
        pattern = re.compile(pattern)
    return pattern.sub("", content)


def format_file(filename: Path, *, pattern: str = _WHITESPACE_RE_PATTERN) -> bool:
    """Format a file.

    Args:
        filename (Path): File to format.
        pattern (str): Regex pattern to identify whitespace.

    Returns:
        bool: True if the file was formatted.

    """
    if isinstance(pattern, str):
        pattern = re.compile(pattern)

    with open(filename, "r") as stream:
        content = stream.read()

    if not pattern.search(content):
        return False

    formatted_content = format_str(content, pattern)
    with open(filename, "w") as stream:
        stream.write(formatted_content)

    return True


def main(args: Sequence[str]) -> int:
    """Remove whitespace from files provided as command-line arguments.

    Args:
        args (Sequence[str]): Command-line arguments.

    Returns:
        int: 1 if --check, and any file was formatted, otherwise 0.

    """
    args = [str(arg) for arg in args]  # To support calling with Path object list
    args = _parse_args(args)

    file_formatting_count = 0
    file_total_count = 0

    for filename in _iter_files(args.paths):
        file_total_count += 1
        if format_file(filename):
            print(f"Formatting {filename}")
            file_formatting_count += 1

    print(f"Found trailing whitespace in {file_formatting_count}/{file_total_count} files.")

    if args.check and file_formatting_count > 0:
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
