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
