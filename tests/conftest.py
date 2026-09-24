"""Shared pytest configuration for the A-Z+T test suite.

Puts the project root (azt/) on sys.path so tests can import the app's
top-level packages (`backend`, `frontend`, `tasks`, `utilities`, `io_put`,
`settings`) the same way the app does, regardless of where pytest is invoked.
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent  # azt/
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# ── UTF-8 for source reads, everywhere ─────────────────────────────────────
# THE SUITE DOES NOT RUN ON WINDOWS WITHOUT THIS. Around thirty tests read the
# app's own source with `Path.read_text()` to make source-level assertions.
# `read_text()` with no encoding uses the locale's, which on Windows is
# cp1252, and this repo's files are UTF-8 and full of the characters that
# makes it choke on — the em-dashes and curly quotes in every comment. Four
# test modules failed to COLLECT at all on Kim's machine, 2026-09-24:
#
#   UnicodeDecodeError: 'charmap' codec can't decode byte 0x81 in position
#   176310: character maps to <undefined>
#
# Fixed here rather than at thirty call sites, because the next test to read a
# file would reintroduce it — and did, three times today, in tests written the
# same afternoon. The patch is confined to the test run and to a DEFAULT: a
# test that passes an explicit encoding still gets the one it asked for, so
# nothing that deliberately checks encoding behaviour is affected.
_read_text = pathlib.Path.read_text


def _read_text_utf8(self, encoding=None, errors=None, newline=None):
    if encoding is None:
        encoding = 'utf-8'
    try:
        return _read_text(self, encoding=encoding, errors=errors,
                          newline=newline)
    except TypeError:       # `newline` arrived in 3.13; older signature
        return _read_text(self, encoding=encoding, errors=errors)


pathlib.Path.read_text = _read_text_utf8
