# coding=UTF-8
"""A notebook tab switch asks the window to re-fit.

WHY. Every refit in the webview backend is triggered by a widget being
CREATED — `_request_refit` from `_WebviewWidget._finish_creation`, which is
what makes "a page cannot forget to ask" true. A tab switch creates nothing.
All of the chooser's panels are built at startup and a hidden panel does not
contribute to layout, so the fit measured whichever tab happened to be
showing and never looked again: Kent's chooser on the Reports tab, 2026-09-16
— a third column and a fourth row off the right and bottom edges, with no
scrollbar and nothing reachable.

TWO PATHS, and the second is easy to miss. The page reports `tabchanged` only
for a USER click; `Notebook.select` passes `notify=false` deliberately, so a
programmatic select cannot re-enter an app handler that itself selects — and
selecting a starting tab programmatically is exactly what the chooser does.
A fix on one path only would leave the startup case cropped.

Plain methods against a stand-in `self`: no pywebview, no page, no display.
`_js(None, ...)` is a documented no-op, which is what makes that possible.
"""
import sys
import types
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

ui_webview = pytest.importorskip('frontend.ui_webview',
                                 reason='needs the webview backend importable')

Notebook = ui_webview.Notebook


class FakeNotebook:
    """Enough of a Notebook for the two methods under test."""

    _wid = 7
    _wv_window = None

    def __init__(self, tabs=()):
        self._tabs = list(tabs)
        self._selected = None
        self.asked = []
        self.window = object()

    def _refit_for_tab(self, trigger):
        self.asked.append(trigger)

    def _root_for_binding(self):
        return self.window


def tab(wid):
    return types.SimpleNamespace(_wid=wid)


def test_selecting_a_tab_by_index_asks_for_a_refit():
    nb = FakeNotebook([tab(8), tab(9)])
    assert Notebook.select(nb, 1) is nb._tabs[1]
    assert nb.asked == ['tab selected']


def test_selecting_a_tab_by_widget_asks_for_a_refit():
    nb = FakeNotebook([tab(8), tab(9)])
    Notebook.select(nb, nb._tabs[0])
    assert nb.asked == ['tab selected']


def test_reading_the_current_tab_asks_for_nothing():
    """`select()` with no argument is a GETTER, as it is in ttk. Refitting on
    a read would put a window resize behind every `notebook.select()` the app
    makes to find out where it is."""
    nb = FakeNotebook([tab(8)])
    nb._selected = nb._tabs[0]
    assert Notebook.select(nb) is nb._tabs[0]
    assert nb.asked == []


def test_an_index_that_is_not_a_tab_asks_for_nothing():
    nb = FakeNotebook([tab(8)])
    assert Notebook.select(nb, 4) is None
    assert nb.asked == []


def test_the_refit_request_reaches_the_window_and_is_prompt(monkeypatch):
    """SHORT DELAY, on purpose. The coalescing delay exists to let a burst of
    widget creations settle; nothing is arriving after a tab click, and the
    user is looking at the cropped page while it waits."""
    calls = []
    monkeypatch.setattr(ui_webview, '_request_refit',
                        lambda win, trigger, delay=0.4:
                            calls.append((win, trigger, delay)))
    nb = FakeNotebook()
    Notebook._refit_for_tab(nb, 'tab clicked')
    assert len(calls) == 1
    win, trigger, delay = calls[0]
    assert win is nb.window
    assert trigger == 'tab clicked'
    assert delay <= 0.1


def test_the_refit_request_does_not_go_to_the_notebook_itself(monkeypatch):
    """`_root_for_binding` can answer with the widget itself; asking THAT for
    a fit would call `fit_to_content` on something that has none."""
    calls = []
    monkeypatch.setattr(ui_webview, '_request_refit',
                        lambda *a, **k: calls.append(a))
    nb = FakeNotebook()
    nb.window = nb
    Notebook._refit_for_tab(nb, 'tab clicked')
    assert calls == []


def test_a_broken_window_lookup_does_not_break_the_tab_switch(monkeypatch):
    """A refit is an improvement to a page that already works. Raising here
    would make a failed optimisation into a dead tab."""
    def boom(self):
        raise RuntimeError('no root')

    nb = FakeNotebook()
    monkeypatch.setattr(FakeNotebook, '_root_for_binding', boom)
    Notebook._refit_for_tab(nb, 'tab clicked')     # must not raise


def test_the_user_click_path_is_registered_too():
    """The page reports `tabchanged` for a click, and `Notebook.__init__`
    registers for it rather than leaving it to an app binding that is
    optional. Read from the source because constructing a real widget needs
    a page."""
    src = (Path(__file__).resolve().parents[1]
           / 'frontend' / 'ui_webview.py').read_text(encoding='utf-8')
    body = src.split('class Notebook(', 1)[1].split('\nclass ', 1)[0]
    assert "_api.register(self._wid, 'tabchanged'" in body
    assert '_refit_for_tab' in body
