#!/usr/bin/env python3
from __future__ import annotations

import argparse
import io
import logging
import sys
from pathlib import Path
from typing import Iterable, Sequence

from compactify import logs as logger
from compactify.core import format_code, format_file


def _parse_args(args: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", help="Paths to format", type=Path, nargs="*", default=())
    parser.add_argument(
        "--from-stdin", help="Recieve input source code from stdin", action="store_true"
    )
    parser.add_argument(
        "--verbose", "-v", help="Set logging threshold to DEBUG", action="store_true"
    )
    return parser.parse_args(args)


def _iter_python_files(paths: Iterable[Path]) -> Iterable[Path]:
    for path in paths:
        path = path.resolve().absolute()
        if path.is_file():
            yield path
        elif path.is_dir():
            yield from path.rglob("*.py")
        else:
            raise FileNotFoundError(f"Not found: {path}")


def main(args: Sequence[str] | None = None) -> int:
    """Parse command-line arguments and run compactify on provided files.

    Args:
        args (Sequence[str]): sys.argv[1:]

    Returns:
        int: 0 if successful.

    """
    if args is None:
        args = sys.argv[1:]
    args = _parse_args(args)

    logger.set_level(logging.DEBUG if args.verbose else logging.INFO)

    if args.from_stdin:
        logger.set_level(100)  # Higher than critical
        source = sys.stdin.read()
        temp_stdout = io.StringIO()
        sys_stdout = sys.stdout
        try:
            sys.stdout = temp_stdout
            source = format_code(source)
        finally:
            sys.stdout = sys_stdout
        print(source)
        return 0

    file_count = 0
    for filename in _iter_python_files(args.paths):
        logger.info("Formatting {filename}...", filename=filename)
        format_file(filename)
        file_count += 1

    if file_count == 0:
        logger.info("No files provided")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
