# coding=UTF-8
"""`EntryField.insert(INSERT, text)` inserts at the caret, in the page.

Kent, 2026-09-22, the tone transcribe page under webview: "the buttons seem
to work correctly, but only append, not input where the cursor is." Python
cannot know the caret; the DOM can. So for INSERT the splice is done by the
page (`setRangeText` at its own selection) and the variable learns the new
value through the ordinary 'input' event — the Python side writes nothing,
because two writers would race. A field with no page yet keeps the old
append.
"""
import types
from pathlib import Path

import pytest

ui_webview = pytest.importorskip('frontend.ui_webview',
                                 reason='needs the webview backend importable')

JS = (Path(__file__).resolve().parents[1]
      / 'frontend' / 'webview_html' / 'widgets.js').read_text()


def _field(value, with_window):
    var = ui_webview.StringVar(value=value)
    ns = types.SimpleNamespace(_wid=7, textvariable=var,
                               _wv_window=object() if with_window else None)
    ns._index = lambda where, current: ui_webview.EntryField._index(ns, where, current)
    ns._put = lambda text: ui_webview.EntryField._put(ns, text)
    return ns


def test_insert_at_caret_is_delegated_to_the_page(monkeypatch):
    sent = []
    monkeypatch.setattr(ui_webview, '_js', lambda wv, code: sent.append(code))
    f = _field('abc', with_window=True)
    ui_webview.EntryField.insert(f, ui_webview.INSERT, '˥')
    assert len(sent) == 1 and 'insert_at_caret' in sent[0] and '˥' in sent[0]
    assert f.textvariable.get() == 'abc', \
        "the variable is set by the page's 'input' report, not here"


def test_insert_at_end_still_goes_through_the_variable(monkeypatch):
    sent = []
    monkeypatch.setattr(ui_webview, '_js', lambda wv, code: sent.append(code))
    f = _field('abc', with_window=True)
    ui_webview.EntryField.insert(f, ui_webview.END, 'd')
    assert f.textvariable.get() == 'abcd'
    assert not any('insert_at_caret' in c for c in sent)


def test_a_field_with_no_page_yet_appends():
    f = _field('abc', with_window=False)
    ui_webview.EntryField.insert(f, ui_webview.INSERT, 'd')
    assert f.textvariable.get() == 'abcd'


def test_the_page_splices_at_the_selection_and_reports_input():
    case = JS[JS.index("case 'insert_at_caret':"):]
    case = case[:case.index('break;')]
    assert 'setRangeText' in case
    assert "dispatchEvent(new Event('input'" in case
    assert 'wvTouched' in case, "an untouched field must append, not prepend"
