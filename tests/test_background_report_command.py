"""The background-report wrapper must take NO arguments.

The webview Button passes its `choice` to any command with a free
positional slot. Background wrapped the report as `lambda fn=self.do:`,
so the button's choice string replaced the report function and the
report died with "'str' object is not callable" (Kent, 2026-10-13).
"""
import inspect
from types import SimpleNamespace

import pytest

rm = pytest.importorskip('backend.core.report_mixins')


class Base:
    def __init__(self, **kwargs):
        self.do = self.real
        self.status = SimpleNamespace(redofinalbuttons=lambda: None)

    def real(self):
        pass


class Report(rm.Background, Base):
    def background(self, fn):
        self.ran = fn


def test_the_wrapped_report_has_no_slot_for_a_button_choice():
    r = Report()
    assert not inspect.signature(r.do).parameters


def test_the_wrapped_report_runs_the_report_function():
    r = Report()
    r.do()
    assert r.ran == r.real


class Scoped(Base):
    """A scope mixin that adopts another report function via set_do, as
    MultisliceT does."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        rm.set_do(self, self.other)

    def other(self):
        pass


class BackgroundFirst(rm.Background, Scoped):
    """Background's init runs LAST here (MultisliceTBackground's order)."""
    def background(self, fn):
        self.ran = fn


def test_set_do_leaves_no_slot_for_a_button_choice():
    r = BackgroundFirst()
    assert not inspect.signature(r.do).parameters


def test_a_report_is_wrapped_for_the_background_once():
    """The child process must get the REPORT, not another wrapper."""
    r = BackgroundFirst()
    r.do()
    assert r.ran == r.other
