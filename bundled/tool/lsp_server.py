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
import sysconfig
import traceback
from typing import Any, Optional, Sequence, Tuple


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
import lsp_jsonrpc as jsonrpc
import lsp_utils as utils
import lsprotocol.types as lsp
from pygls import server, uris, workspace

WORKSPACE_SETTINGS = {}
GLOBAL_SETTINGS = {}
RUNNER = pathlib.Path(__file__).parent / "lsp_runner.py"

MAX_WORKERS = 5
LSP_SERVER = server.LanguageServer(
    name="pyrefact",
    version="2024.0.1",
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


@LSP_SERVER.feature(lsp.TEXT_DOCUMENT_FORMATTING)
def formatting(params: lsp.DocumentFormattingParams) -> list[lsp.TextEdit] | None:
    """LSP handler for textDocument/formatting request."""
    document = LSP_SERVER.workspace.get_text_document(params.text_document.uri)
    edits = _formatting_helper(document)
    if edits:
        return edits

    # NOTE: If you provide [] array, VS Code will clear the file of all contents.
    # To indicate no changes to file return None.
    return None


@LSP_SERVER.feature(lsp.TEXT_DOCUMENT_RANGE_FORMATTING)
def range_formatting(params: lsp.DocumentRangeFormattingParams) -> list[lsp.TextEdit] | None:
    """LSP handler for textDocument/rangeFormatting request."""
    document = LSP_SERVER.workspace.get_text_document(params.text_document.uri)
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

    GLOBAL_SETTINGS.update(**params.initialization_options.get("globalSettings", {}))

    settings = params.initialization_options["settings"]
    _update_workspace_settings(settings)
    log_to_output(
        f"Settings used to run Server:\r\n{json.dumps(settings, indent=4, ensure_ascii=False)}\r\n"
    )
    log_to_output(
        f"Global settings:\r\n{json.dumps(GLOBAL_SETTINGS, indent=4, ensure_ascii=False)}\r\n"
    )


@LSP_SERVER.feature(lsp.EXIT)
def on_exit(_params: Optional[Any] = None) -> None:
    """Handle clean up on exit."""
    jsonrpc.shutdown_json_rpc()


@LSP_SERVER.feature(lsp.SHUTDOWN)
def on_shutdown(_params: Optional[Any] = None) -> None:
    """Handle clean up on shutdown."""
    jsonrpc.shutdown_json_rpc()


def _get_global_defaults():
    return {
        "path": GLOBAL_SETTINGS.get("path", []),
        "interpreter": GLOBAL_SETTINGS.get("interpreter", [sys.executable]),
        "args": GLOBAL_SETTINGS.get("args", []),
        "importStrategy": GLOBAL_SETTINGS.get("importStrategy", "useBundled"),
        "showNotifications": GLOBAL_SETTINGS.get("showNotifications", "off"),
    }


def _update_workspace_settings(settings):
    if not settings:
        key = os.getcwd()
        WORKSPACE_SETTINGS[key] = {
            "cwd": key,
            "workspaceFS": key,
            "workspace": uris.from_fs_path(key),
            **_get_global_defaults(),
        }
        return

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


def _get_settings_by_path(file_path: pathlib.Path):
    workspaces = {s["workspaceFS"] for s in WORKSPACE_SETTINGS.values()}

    while file_path != file_path.parent:
        str_file_path = str(file_path)
        if str_file_path in workspaces:
            return WORKSPACE_SETTINGS[str_file_path]
        file_path = file_path.parent

    setting_values = list(WORKSPACE_SETTINGS.values())
    return setting_values[0]


def _get_document_key(document: workspace.Document):
    if WORKSPACE_SETTINGS:
        document_workspace = pathlib.Path(document.path)
        workspaces = {s["workspaceFS"] for s in WORKSPACE_SETTINGS.values()}

        # Find workspace settings for the given file.
        while document_workspace != document_workspace.parent:
            if str(document_workspace) in workspaces:
                return str(document_workspace)
            document_workspace = document_workspace.parent

    return None


def _get_settings_by_document(document: workspace.Document | None):
    if document is None or document.path is None:
        return list(WORKSPACE_SETTINGS.values())[0]

    key = _get_document_key(document)
    if key is None:
        # This is either a non-workspace file or there is no workspace.
        key = os.fspath(pathlib.Path(document.path).parent)
        return {
            "cwd": key,
            "workspaceFS": key,
            "workspace": uris.from_fs_path(key),
            **_get_global_defaults(),
        }

    return WORKSPACE_SETTINGS[str(key)]


# *****************************************************
# Internal execution APIs.
# *****************************************************
def _run_tool_on_document(
    document: workspace.Document,
    use_stdin: bool = False,
    extra_args: Sequence[str] = [],
) -> utils.RunResult | None:
    """Runs tool on the given document.

    if use_stdin is true then contents of the document is passed to the
    tool via stdin.
    """
    if str(document.uri).startswith("vscode-notebook-cell"):
        # TODO: Decide on if you want to skip notebook cells.
        # Skip notebook cells
        return None

    if utils.is_stdlib_file(document.path):
        # TODO: Decide on if you want to skip standard library files.
        # Skip standard library python files.
        return None

    # deep copy here to prevent accidentally updating global settings.
    settings = copy.deepcopy(_get_settings_by_document(document))

    code_workspace = settings["workspaceFS"]
    cwd = settings["cwd"]

    use_path = False
    use_rpc = False
    if settings["path"]:
        # 'path' setting takes priority over everything.
        use_path = True
        argv = settings["path"]
    elif settings["interpreter"] and not utils.is_current_interpreter(
        settings["interpreter"][0]
    ):
        # If there is a different interpreter set use JSON-RPC to the subprocess
        # running under that interpreter.
        argv = [TOOL_MODULE]
        use_rpc = True
    else:
        # if the interpreter is same as the interpreter running this
        # process then run as module.
        argv = [TOOL_MODULE]

    argv += TOOL_ARGS + settings["args"] + extra_args

    if use_stdin:
        # TODO: update these to pass the appropriate arguments to provide document contents
        # to tool via stdin.
        # For example, for pylint args for stdin looks like this:
        #     pylint --from-stdin <path>
        # Here `--from-stdin` path is used by pylint to make decisions on the file contents
        # that are being processed. Like, applying exclusion rules.
        # It should look like this when you pass it:
        #     argv += ["--from-stdin", document.path]
        # Read up on how your tool handles contents via stdin. If stdin is not supported use
        # set use_stdin to False, or provide path, what ever is appropriate for your tool.
        argv += []
    else:
        argv += [document.path]

    if use_path:
        # This mode is used when running executables.
        log_to_output(" ".join(argv))
        log_to_output(f"CWD Server: {cwd}")
        result = utils.run_path(
            argv=argv,
            use_stdin=use_stdin,
            cwd=cwd,
            source=document.source.replace("\r\n", "\n"),
        )
        if result.stderr:
            log_to_output(result.stderr)
    elif use_rpc:
        # This mode is used if the interpreter running this server is different from
        # the interpreter used for running this server.
        log_to_output(" ".join(settings["interpreter"] + ["-m"] + argv))
        log_to_output(f"CWD Linter: {cwd}")

        result = jsonrpc.run_over_json_rpc(
            workspace=code_workspace,
            interpreter=settings["interpreter"],
            module=TOOL_MODULE,
            argv=argv,
            use_stdin=use_stdin,
            cwd=cwd,
            source=document.source,
        )
        if result.exception:
            log_error(result.exception)
            result = utils.RunResult(result.stdout, result.stderr)
        elif result.stderr:
            log_to_output(result.stderr)
    else:
        # In this mode the tool is run as a module in the same process as the language server.
        log_to_output(" ".join([sys.executable, "-m"] + argv))
        log_to_output(f"CWD Linter: {cwd}")
        # This is needed to preserve sys.path, in cases where the tool modifies
        # sys.path and that might not work for this scenario next time around.
        with utils.substitute_attr(sys, "path", sys.path[:]):
            try:
                # TODO: `utils.run_module` is equivalent to running `python -m <pytool-module>`.
                # If your tool supports a programmatic API then replace the function below
                # with code for your tool. You can also use `utils.run_api` helper, which
                # handles changing working directories, managing io streams, etc.
                # Also update `_run_tool` function and `utils.run_module` in `lsp_runner.py`.
                result = utils.run_module(
                    module=TOOL_MODULE,
                    argv=argv,
                    use_stdin=use_stdin,
                    cwd=cwd,
                    source=document.source,
                )
            except Exception:
                log_error(traceback.format_exc(chain=True))
                raise
        if result.stderr:
            log_to_output(result.stderr)

    log_to_output(f"{document.uri} :\r\n{result.stdout}")
    return result


def _run_tool(extra_args: Sequence[str]) -> utils.RunResult:
    """Runs tool."""
    # deep copy here to prevent accidentally updating global settings.
    settings = copy.deepcopy(_get_settings_by_document(None))

    code_workspace = settings["workspaceFS"]
    cwd = settings["workspaceFS"]

    use_path = False
    use_rpc = False
    if len(settings["path"]) > 0:
        # 'path' setting takes priority over everything.
        use_path = True
        argv = settings["path"]
    elif len(settings["interpreter"]) > 0 and not utils.is_current_interpreter(
        settings["interpreter"][0]
    ):
        # If there is a different interpreter set use JSON-RPC to the subprocess
        # running under that interpreter.
        argv = [TOOL_MODULE]
        use_rpc = True
    else:
        # if the interpreter is same as the interpreter running this
        # process then run as module.
        argv = [TOOL_MODULE]

    argv += extra_args

    if use_path:
        # This mode is used when running executables.
        log_to_output(" ".join(argv))
        log_to_output(f"CWD Server: {cwd}")
        result = utils.run_path(argv=argv, use_stdin=True, cwd=cwd)
        if result.stderr:
            log_to_output(result.stderr)
    elif use_rpc:
        # This mode is used if the interpreter running this server is different from
        # the interpreter used for running this server.
        log_to_output(" ".join(settings["interpreter"] + ["-m"] + argv))
        log_to_output(f"CWD Linter: {cwd}")
        result = jsonrpc.run_over_json_rpc(
            workspace=code_workspace,
            interpreter=settings["interpreter"],
            module=TOOL_MODULE,
            argv=argv,
            use_stdin=True,
            cwd=cwd,
        )
        if result.exception:
            log_error(result.exception)
            result = utils.RunResult(result.stdout, result.stderr)
        elif result.stderr:
            log_to_output(result.stderr)
    else:
        # In this mode the tool is run as a module in the same process as the language server.
        log_to_output(" ".join([sys.executable, "-m"] + argv))
        log_to_output(f"CWD Linter: {cwd}")
        # This is needed to preserve sys.path, in cases where the tool modifies
        # sys.path and that might not work for this scenario next time around.
        with utils.substitute_attr(sys, "path", sys.path[:]):
            try:
                # TODO: `utils.run_module` is equivalent to running `python -m <pytool-module>`.
                # If your tool supports a programmatic API then replace the function below
                # with code for your tool. You can also use `utils.run_api` helper, which
                # handles changing working directories, managing io streams, etc.
                # Also update `_run_tool_on_document` function and `utils.run_module` in `lsp_runner.py`.
                result = utils.run_module(
                    module=TOOL_MODULE, argv=argv, use_stdin=True, cwd=cwd
                )
            except Exception:
                log_error(traceback.format_exc(chain=True))
                raise
        if result.stderr:
            log_to_output(result.stderr)

    log_to_output(f"\r\n{result.stdout}\r\n")
    return result


# *****************************************************
# Logging and notification.
# *****************************************************
def log_to_output(
    message: str, msg_type: lsp.MessageType = lsp.MessageType.Log
) -> None:
    LSP_SERVER.show_message_log(message, msg_type)


def log_error(message: str) -> None:
    LSP_SERVER.show_message_log(message, lsp.MessageType.Error)
    if os.getenv("LS_SHOW_NOTIFICATION", "off") in ["onError", "onWarning", "always"]:
        LSP_SERVER.show_message(message, lsp.MessageType.Error)


def log_warning(message: str) -> None:
    LSP_SERVER.show_message_log(message, lsp.MessageType.Warning)
    if os.getenv("LS_SHOW_NOTIFICATION", "off") in ["onWarning", "always"]:
        LSP_SERVER.show_message(message, lsp.MessageType.Warning)


def log_always(message: str) -> None:
    LSP_SERVER.show_message_log(message, lsp.MessageType.Info)
    if os.getenv("LS_SHOW_NOTIFICATION", "off") in ["always"]:
        LSP_SERVER.show_message(message, lsp.MessageType.Info)


# *****************************************************
# Start the server.
# *****************************************************
if __name__ == "__main__":
    LSP_SERVER.start_io()
