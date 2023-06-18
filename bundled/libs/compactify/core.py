import ast
import re
from pathlib import Path
from typing import Sequence

from compactify import logs as logger


def _group_matching_lines(
    lines: Sequence[str], pattern: str, min_group_size: int = 2
) -> Sequence[Sequence[int]]:
    """
    Given a list of lines and a regex pattern, return a sorted list of groups of sorted line numbers
    where each group contains at least min_group_size consecutive lines matching the pattern.
    """
    lines = (i for i, line in enumerate(lines) if re.match(pattern, line))
    groups = [set()]
    for i in lines:
        if i - 1 in groups[-1]:
            groups[-1].add(i)
        else:
            groups.append({i})
    return [sorted(group) for group in groups if len(group) >= min_group_size]


def _merge_lines(lines: Sequence[str], group: Sequence[int]) -> None:
    """
    Merge the lines at the given indices into one line.
    """
    lines_subset = [lines[i] for i in group]
    indent = min((len(line) - len(line.lstrip()) for line in lines_subset if line.strip()), default=0)
    indent_character = lines_subset[0][0]  # Won't be whitespace if indent==0, but that's fine
    new_line = indent * indent_character + re.sub(r"\s", "", "".join(lines_subset))
    for i in sorted(group, reverse=True):
        lines.pop(i)

    lines.insert(min(group), new_line)


def collapse_rparen_lines(lines: Sequence[str]) -> None:
    """
    For all consecutive lines matching rparen_pattern, collapse them into one line,
    remove all whitespace, and indent as much as the least indented line.
    """
    rparen_only_pattern = r"[\]\)\},:]"
    rparen_or_ws_pattern = r"[\]\)\},:\s]"
    rparen_pattern = r"^\s*" + rparen_only_pattern + rparen_or_ws_pattern + r"*$"

    for group in reversed(_group_matching_lines(lines, rparen_pattern)):
        _merge_lines(lines, group)


def collapse_lparen_lines(lines: Sequence[str]) -> None:
    """
    For all consecutive lines matching lparen_pattern, collapse them into one line,
    remove all whitespace, and indent as much as the least indented line.
    """
    lparen_only_pattern = r"[\[\(\{]"
    lparen_or_ws_pattern = r"[\[\(\{\s]"
    lparen_pattern = r"^\s*" + lparen_only_pattern + lparen_or_ws_pattern + r"*$"

    for group in reversed(_group_matching_lines(lines, lparen_pattern)):
        _merge_lines(lines, group)

    for start, *_ in reversed(_group_matching_lines(lines, lparen_pattern, 1)):
        if start > 0 and re.match(
            lparen_only_pattern,
            (" " + lines[start - 1].rstrip())[-1]
        ) and re.match(
            lparen_only_pattern,
            (lines[start].lstrip() + " ")[0]
        ):
            lines[start - 1] = lines[start - 1].rstrip() + lines[start].lstrip()
            lines.pop(start)


def remove_excessive_indent(lines: Sequence[str]) -> None:
    """
    For all lines where the last non-whitespace character matches lparen_only_pattern,
    and where the line after it matches lparen_pattern, remove all whitespace from the
    second line and collapse it into the first line.
    """
    if len(lines) < 2:
        return

    indents = [
        len(line) - len(line.lstrip()) for line in lines
    ]
    best_indents = [indents[0]]
    for i, indent in enumerate(indents[1:], start=1):
        previous_indent = 0
        for j in range(i - 1, -1, -1):
            if lines[j].strip():
                previous_indent = indents[j]
                break

        best_indents.append(min(indent, previous_indent + 4))

    deindents = [0 for _ in lines]

    for i, line, indent, best_indent in zip(
        range(len(lines)),
        lines,
        indents,
        best_indents
    ):
        overindent = indent - best_indent
        if overindent > 0:
            for j in range(i, len(lines)):
                if indents[j] <= best_indent:
                    break
                deindents[j] += min(overindent, indents[j] - best_indent)

    for i, deindent in enumerate(deindents):
        lines[i] = lines[i][deindent:]


def is_valid_python(source: str) -> bool:
    try:
        ast.parse(source)
    except (SyntaxError, ValueError):
        return False

    return True


def format_code(source: str) -> str:
    """Format source code.

    Args:
        filename (Path): File to format

    Returns:
        bool: True if any changes were made
    """
    if not source.strip():
        return source

    if not is_valid_python(source):
        logger.debug("Source is not valid python.")
        return source

    lines = list(source.splitlines(keepends=False))
    line_end_character = source.splitlines(keepends=True)[0][len(lines[0]):]

    collapse_rparen_lines(lines)
    collapse_lparen_lines(lines)
    remove_excessive_indent(lines)

    if source.endswith(line_end_character):
        lines.append("")

    new_source = line_end_character.join(lines)

    if not is_valid_python(source):
        logger.debug("Result is not valid python.")
        return source

    return new_source


def format_file(filename: Path) -> None:
    """Format a file.

    Args:
        filename (Path): File to format

    """
    filename = Path(filename).resolve().absolute()
    with open(filename, "r", encoding="utf-8") as stream:
        initial_content = stream.read()

    source = format_code(initial_content)

    if source != initial_content and (
        is_valid_python(source) or not is_valid_python(initial_content)
    ):
        with open(filename, "w", encoding="utf-8") as stream:
            stream.write(source)
