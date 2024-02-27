# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
"""
Test for linting over LSP.
"""

import sys
from pathlib import Path
from threading import Event

from .lsp_test_client import constants, defaults, session, utils
from . import testing_infra

TEST_FILE_PATH = constants.TEST_DATA / "document_formatting" / "sample.py"
TEST_FILE_URI = utils.as_uri(str(TEST_FILE_PATH))
SERVER_INFO = utils.get_server_info_defaults()
TIMEOUT = 10  # 10 seconds


# Ensure that we can import LSP libraries, and other bundled libraries.
BUNDLED_LIBS_PATH = Path(__file__).parents[3] / "bundled" / "libs"
sys.path.append(str(BUNDLED_LIBS_PATH))
import lsprotocol.types as lsp


def test_document_formatting():
    """Test formatting a python file."""
    FORMATTED_TEST_FILE_PATH = constants.TEST_DATA / "document_formatting" / "sample.py"
    UNFORMATTED_TEST_FILE_PATH = constants.TEST_DATA / "document_formatting" / "sample.unformatted"

    contents = UNFORMATTED_TEST_FILE_PATH.read_text()
    lines = contents.splitlines(keepends=False)

    actual = []
    with utils.PythonFile(contents, UNFORMATTED_TEST_FILE_PATH.parent) as pf:
        uri = utils.as_uri(str(pf.fullpath))

        with session.LspSession() as ls_session:
            ls_session.initialize()
            ls_session.notify_did_open(
                {
                    "textDocument": {
                        "uri": uri,
                        "languageId": "python",
                        "version": 1,
                        "text": contents,
                    }
                }
            )
            actual = ls_session.text_document_formatting(
                {
                    "textDocument": {"uri": uri},
                    # `options` is not used by black
                    "options": {"tabSize": 4, "insertSpaces": True},
                }
            )

    expected = [
        {
            "range": {
                "start": {"line": 0, "character": 0},
                "end": {"line": len(lines), "character": 0},
            },
            "newText": FORMATTED_TEST_FILE_PATH.read_text(),
        }
    ]

    assert testing_infra.check_fixes_equal(
        actual[0]["newText"],
        expected[0]["newText"],
        clear_whitespace=True,  # Do not assert that whitespace is correct
    )


def test_range_formatting():
    """Test formatting a python file."""
    FORMATTED_TEST_FILE_PATH = constants.TEST_DATA / "range_formatting" / "sample.py"
    UNFORMATTED_TEST_FILE_PATH = constants.TEST_DATA / "range_formatting" / "sample.unformatted"

    contents = UNFORMATTED_TEST_FILE_PATH.read_text()

    actual = []
    with utils.PythonFile(contents, UNFORMATTED_TEST_FILE_PATH.parent) as pf:
        uri = utils.as_uri(str(pf.fullpath))

        with session.LspSession() as ls_session:
            ls_session.initialize()
            ls_session.notify_did_open(
                {
                    "textDocument": {
                        "uri": uri,
                        "languageId": "python",
                        "version": 1,
                        "text": contents,
                    }
                }
            )
            actual = ls_session.text_document_range_formatting(
                {
                    "textDocument": {"uri": uri},
                    # `options` is not used by black
                    "options": {"tabSize": 4, "insertSpaces": True},
                    "range": {
                        "start": {"line": 4, "character": 0},
                        "end": {"line": 10, "character": 0}
                    },
                }
            )

    expected = [
        {
            "range": {
                "start": {"line": 4, "character": 0},
                "end": {"line": 10, "character": 0},
            },
            "newText": "".join(
                FORMATTED_TEST_FILE_PATH.read_text().splitlines(keepends=True)[3:10]
            ),
        }
    ]

    assert actual[0]["range"] == expected[0]["range"]
    assert testing_infra.check_fixes_equal(
        actual[0]["newText"],
        expected[0]["newText"],
        clear_whitespace=True,  # Do not assert that whitespace is correct
    )
