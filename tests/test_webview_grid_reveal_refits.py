# coding=UTF-8
"""Showing a hidden widget asks the window to refit; re-gridding a shown one does not.

Kent, 2026-09-22, the new-language page under webview: "content is off the
page". The territory frame is built at page build, hidden with
`grid_remove()`, and shown later with `grid()`. Refits are requested when a
widget is CREATED (`_finish_creation`) and when a notebook tab changes;
`grid()` created nothing, so the window kept its pre-reveal size and the frame
sat below the bottom edge. Same class as the tab switch fixed 2026-09-16.

Stand-in widget, `_js` and `_request_refit` patched: this is about WHETHER the
request is made, not what the page does with it.
"""
import types

import pytest

ui_webview = pytest.importorskip('frontend.ui_webview',
                                 reason='needs the webview backend importable')


def _widget(visible):
    win = types.SimpleNamespace(_wid=9)
    return types.SimpleNamespace(_wid=1, _wv_window=None, _grid_opts={'row': 3},
                                 _has_grid=True, _grid_visible=visible,
                                 _root_for_binding=lambda: win), win


def _grid(monkeypatch, widget):
    asked = []
    monkeypatch.setattr(ui_webview, '_js', lambda wv, code: None)
    monkeypatch.setattr(ui_webview, '_request_refit',
                        lambda win, trigger, delay=0.4: asked.append((win, trigger)))
    ui_webview._WebviewWidget.grid(widget)
    return asked


def test_revealing_a_hidden_widget_requests_a_refit(monkeypatch):
    w, win = _widget(visible=False)
    asked = _grid(monkeypatch, w)
    assert asked == [(win, 'widget shown')]
    assert w._grid_visible is True


def test_regridding_a_shown_widget_does_not(monkeypatch):
    """A page re-grids things it never hid (e.g. `dogrid()` on a visible
    list); the window's size has not changed, so no request."""
    w, _ = _widget(visible=True)
    assert _grid(monkeypatch, w) == []


def test_the_request_is_short_fused_like_the_tab_switch(monkeypatch):
    """Nothing arrives in a burst on a reveal and the user is looking at the
    cropped page, so the delay is the notebook's 0.05, not the build's 0.4."""
    w, _ = _widget(visible=False)
    seen = {}
    monkeypatch.setattr(ui_webview, '_js', lambda wv, code: None)
    monkeypatch.setattr(ui_webview, '_request_refit',
                        lambda win, trigger, delay=0.4: seen.setdefault('delay', delay))
    ui_webview._WebviewWidget.grid(w)
    assert seen['delay'] == 0.05
