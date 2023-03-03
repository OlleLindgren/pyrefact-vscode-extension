# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
"""Implementation of tool support over LSP."""
from __future__ import annotations

import copy
import functools
import json
import os
import pathlib
import re
import sys
import traceback
from typing import Sequence, Tuple

import jsonrpc
import utils

# **********************************************************
# Update sys.path before importing any bundled libraries.
# **********************************************************

MAX_SEQUENTIAL_NEWLINES = 3


def update_sys_path(path_to_add: str, strategy: str) -> None:
    """Add given path to `sys.path`."""
    if path_to_add not in sys.path and os.path.isdir(path_to_add):
        if strategy == "useBundled":
            sys.path.insert(0, path_to_add)
        elif strategy == "fromEnvironment":
            sys.path.append(path_to_add)


# Ensure that we can import LSP libraries, and other bundled libraries.
update_sys_path(
    os.fspath(pathlib.Path(__file__).parent.parent / "libs"),
    os.getenv("LS_IMPORT_STRATEGY", "useBundled"),
)

# **********************************************************
# Imports needed for the language server goes below this.
# **********************************************************
# pylint: disable=wrong-import-position,import-error


import pyrefact
from pygls import lsp, protocol, server, uris, workspace

WORKSPACE_SETTINGS = {}
RUNNER = pathlib.Path(__file__).parent / "runner.py"

MAX_WORKERS = 5
LSP_SERVER = server.LanguageServer(
    name="pyrefact",
    version="2023.0.22",
    max_workers=MAX_WORKERS,
)


# **********************************************************
# Tool specific code goes below this.
# **********************************************************

# Reference:
#  LS Protocol:
#  https://microsoft.github.io/language-server-protocol/specifications/specification-3-16/
#
#  Sample implementations:
#  Pylint: https://github.com/microsoft/vscode-pylint/blob/main/bundled/tool
#  Black: https://github.com/microsoft/vscode-black-formatter/blob/main/bundled/tool
#  isort: https://github.com/microsoft/vscode-isort/blob/main/bundled/tool

TOOL_MODULE = "pyrefact"
TOOL_DISPLAY = "Pyrefact"
TOOL_ARGS = []  # default arguments always passed to your tool.


# **********************************************************
# Formatting features start here
# **********************************************************
#  Sample implementations:
#  Black: https://github.com/microsoft/vscode-black-formatter/blob/main/bundled/tool


@LSP_SERVER.feature(lsp.FORMATTING)
def formatting(params: lsp.DocumentFormattingParams) -> list[lsp.TextEdit] | None:
    """LSP handler for textDocument/formatting request."""
    document = LSP_SERVER.workspace.get_document(params.text_document.uri)
    edits = _formatting_helper(document)
    if edits:
        return edits

    # NOTE: If you provide [] array, VS Code will clear the file of all contents.
    # To indicate no changes to file return None.
    return None


@LSP_SERVER.feature(lsp.RANGE_FORMATTING)
def range_formatting(params: lsp.DocumentRangeFormattingParams) -> list[lsp.TextEdit] | None:
    """LSP handler for textDocument/formatting request."""
    document = LSP_SERVER.workspace.get_document(params.text_document.uri)
    edits = _formatting_helper(document, params.range)
    if edits:
        return edits

    # NOTE: If you provide [] array, VS Code will clear the file of all contents.
    # To indicate no changes to file return None.
    return None


def _count_newlines_at_start_end(source: str) -> Tuple[int, int]:
    split = source.splitlines(keepends=False)
    split_keepends = source.splitlines(keepends=True)
    newlines_before = newlines_after = 0
    for line in split:
        if line.strip():
            break

        newlines_before += 1

    for line in reversed(split):
        if line.strip():
            break

        newlines_after += 1

    if split_keepends[-1] != split[-1]:
        newlines_after += 1

    return newlines_before, newlines_after


def _formatting_helper(
    document: workspace.Document, selection_range: lsp.Range | None = None
) -> list[lsp.TextEdit] | None:
    if selection_range is not None:
        try:
            original_source = _get_text_subset(document.source, selection_range)
        except InvalidSelection:
            return None
    else:
        original_source = document.source

    new_source = pyrefact.format_code(original_source, safe=True)
    if not new_source:
        return None

    new_source = _match_line_endings(document, new_source)

    # Remove empty lines before and after
    new_source = re.sub(r"\A^(\s*\r?\n)+", "", new_source)
    new_source = re.sub(r"(\s*\r?\n)+$\Z", "", new_source)

    if selection_range is None:
        document_start = lsp.Position(line=0, character=0)
        document_end = lsp.Position(line=len(document.lines), character=0)
        selection_range = lsp.Range(start=document_start, end=document_end)

        return [lsp.TextEdit(range=selection_range, new_text=new_source)]

    expected_before, expected_after = _count_newlines_at_start_end(original_source)
    actual_before, actual_after = _count_newlines_at_start_end(new_source)
    expected_newline_type = _get_line_endings(document.source) or "\n"

    missing_before = min(MAX_SEQUENTIAL_NEWLINES, expected_before) - actual_before
    missing_after = min(MAX_SEQUENTIAL_NEWLINES, expected_after) - actual_after

    if missing_before > 0:
        new_source = expected_newline_type * missing_before + new_source
    if missing_after > 0:
        new_source = new_source + expected_newline_type * missing_after

    return [lsp.TextEdit(range=selection_range, new_text=new_source)]


def _get_line_endings(lines: list[str]) -> str:
    """Returns line endings used in the text."""
    try:
        if lines[0][-2:] == "\r\n":
            return "\r\n"
        return "\n"
    except Exception:  # pylint: disable=broad-except
        return None


def _match_line_endings(document: workspace.Document, text: str) -> str:
    """Ensures that the edited text line endings matches the document line endings."""
    expected = _get_line_endings(document.source.splitlines(keepends=True))
    actual = _get_line_endings(text.splitlines(keepends=True))
    if actual == expected or actual is None or expected is None:
        return text
    return text.replace(actual, expected)


# **********************************************************
# Formatting features ends here
# **********************************************************


# **********************************************************
# Required Language Server Initialization and Exit handlers.
# **********************************************************
@LSP_SERVER.feature(lsp.INITIALIZE)
def initialize(params: lsp.InitializeParams) -> None:
    """LSP handler for initialize request."""
    log_to_output(f"CWD Server: {os.getcwd()}")

    paths = "\r\n   ".join(sys.path)
    log_to_output(f"sys.path used to run Server:\r\n   {paths}")

    settings = params.initialization_options["settings"]
    _update_workspace_settings(settings)
    log_to_output(
        f"Settings used to run Server:\r\n{json.dumps(settings, indent=4, ensure_ascii=False)}\r\n"
    )

    if isinstance(LSP_SERVER.lsp, protocol.LanguageServerProtocol):
        if any(setting["logLevel"] == "debug" for setting in settings):
            LSP_SERVER.lsp.trace = lsp.Trace.Verbose
        elif any(setting["logLevel"] in {"error", "warn", "info"} for setting in settings):
            LSP_SERVER.lsp.trace = lsp.Trace.Messages
        else:
            LSP_SERVER.lsp.trace = lsp.Trace.Off


@LSP_SERVER.feature(lsp.EXIT)
def on_exit():
    """Handle clean up on exit."""
    jsonrpc.shutdown_json_rpc()


# *****************************************************
# Internal functional and settings management APIs.
# *****************************************************
def _update_workspace_settings(settings):
    for setting in settings:
        key = uris.to_fs_path(setting["workspace"])
        WORKSPACE_SETTINGS[key] = {
            **setting,
            "workspaceFS": key,
        }


@functools.lru_cache(maxsize=1)
def _get_line_start_charnos(source: str) -> Sequence[int]:
    start = 0
    charnos = []
    for line in source.splitlines(keepends=True):
        charnos.append(start)
        start += len(line)
    return charnos


class InvalidSelection(ValueError):
    """Selected source range is not valid"""


def _get_text_subset(source: str, selection_range: lsp.Range) -> str:
    line_start_charnos = _get_line_start_charnos(source)

    try:
        start_charno = line_start_charnos[selection_range.start.line] + selection_range.start.character
    except IndexError:
        raise InvalidSelection("Start lineno is larger than the length of source")
    try:
        end_charno = line_start_charnos[selection_range.end.line] + selection_range.end.character
    except IndexError:
        end_charno = len(source)

    return source[start_charno:end_charno]


# *****************************************************
# Logging and notification.
# *****************************************************
def log_to_output(message: str, msg_type: lsp.MessageType = lsp.MessageType.Log) -> None:
    LSP_SERVER.show_message_log(message, msg_type)


def log_error(message: str) -> None:
    LSP_SERVER.show_message_log(message, lsp.MessageType.Error)
    if os.getenv("LS_SHOW_NOTIFICATION", "off") in {"onError", "onWarning", "always"}:
        LSP_SERVER.show_message(message, lsp.MessageType.Error)


def log_warning(message: str) -> None:
    LSP_SERVER.show_message_log(message, lsp.MessageType.Warning)
    if os.getenv("LS_SHOW_NOTIFICATION", "off") in {"onWarning", "always"}:
        LSP_SERVER.show_message(message, lsp.MessageType.Warning)


def log_always(message: str) -> None:
    LSP_SERVER.show_message_log(message, lsp.MessageType.Info)
    if os.getenv("LS_SHOW_NOTIFICATION", "off") in {"always"}:
        LSP_SERVER.show_message(message, lsp.MessageType.Info)


# *****************************************************
# Start the server.
# *****************************************************
if __name__ == "__main__":
    LSP_SERVER.start_io()
