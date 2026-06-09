"""Unit tests for group creation in backend/core/categories.py.

`add_int_group` is the "make a new numbered group" logic used by both regular
sorting and macrosorting. It's testable in isolation with a fake `program`
(no LIFT file / UI): for regular sorting it reads/writes
`program.status.groups(...)`; for macrosort it appends to
`program.alphabet.glyphs()` and does NOT persist via status.

Class names verified against source on 2026-06-08.
"""
import pytest

pytest.importorskip("lxml")  # categories.py import chain
from backend.core.categories import Categories


class _FakeStatus:
    def __init__(self, groups):
        self._groups = list(groups)
        self.store_calls = 0

    def groups(self, g=None, wsorted=False):
        if g is not None:
            self._groups = g
        return self._groups

    def store(self):
        self.store_calls += 1


class _FakeAlphabet:
    def __init__(self, glyphs):
        self._glyphs = list(glyphs)

    def glyphs(self):
        return self._glyphs


class _FakeProgram:
    pass


def _categories(status=None, alphabet=None):
    c = Categories()  # Categories has no __init__; just needs .program
    prog = _FakeProgram()
    if status is not None:
        prog.status = status
    if alphabet is not None:
        prog.alphabet = alphabet
    c.program = prog
    return c, prog


def test_add_int_group_returns_next_integer_name():
    status = _FakeStatus(["1", "2"])
    c, prog = _categories(status=status)
    new = c.add_int_group(macrosort=False)
    assert new == "3"
    assert "3" in prog.status.groups(wsorted=True)
    assert status.store_calls == 1            # regular sort persists the new group


def test_add_int_group_ignores_non_digit_groups():
    status = _FakeStatus(["a", "b"])
    c, _ = _categories(status=status)
    assert c.add_int_group(macrosort=False) == "1"   # max of just the [0] fallback


def test_add_int_group_starts_at_one_when_empty():
    status = _FakeStatus([])
    c, _ = _categories(status=status)
    assert c.add_int_group(macrosort=False) == "1"


def test_add_int_group_macrosort_uses_glyphs_and_does_not_persist_status():
    status = _FakeStatus(["1", "2"])           # should be untouched in macrosort
    alphabet = _FakeAlphabet(["1"])
    c, _ = _categories(status=status, alphabet=alphabet)
    new = c.add_int_group(macrosort=True)
    assert new == "2"
    assert status.store_calls == 0             # macrosort doesn't store via status
