# coding=UTF-8
"""The two ListBoxes agree with Tk about `get` and keep values in step with rows.

Kent, 2026-09-22, the new-language page. Under webview the lists stayed one
row tall after the page-side height handler was added ("not fixed"): the line
before the resize asks the list for `get(0, 'end')`, and the webview `get`
computed `'end' + 1`. Under tkinter, selecting a language did nothing: rows
arrive by `insert()`, `choices` was filled only from the constructor's
`optionlist`, and `_on_select` indexed an empty list inside Tk's callback.

Stand-ins, not widgets: the methods are called unbound on a namespace that
has exactly what they touch (the suite's idiom, see test_sound_ui_handlers).
"""
import types

import pytest


# ── webview: get() ────────────────────────────────────────────────────────
def _wv_list(items):
    from frontend import ui_webview
    ns = types.SimpleNamespace(_items=list(items))
    return ui_webview.ListBox, ns


def test_webview_get_end_returns_every_row():
    LB, lb = _wv_list(['a', 'b', 'c'])
    assert LB.get(lb, 0, 'end') == ('a', 'b', 'c')


def test_webview_get_is_a_tuple_like_tk_for_ranges():
    LB, lb = _wv_list(['a', 'b', 'c'])
    assert LB.get(lb, 1, 2) == ('b', 'c')
    assert LB.get(lb, 1) == 'b'


def test_webview_get_end_as_first_is_the_last_row():
    LB, lb = _wv_list(['a', 'b', 'c'])
    assert LB.get(lb, 'end') == 'c'


def test_webview_get_on_an_empty_list_is_empty_not_an_error():
    LB, lb = _wv_list([])
    assert LB.get(lb, 0, 'end') == ()
    assert LB.get(lb, 0) == ''


# ── tkinter: values in step with rows ─────────────────────────────────────
ui_tkinter = pytest.importorskip('frontend.ui_tkinter',
                                 reason='needs tkinter importable (no display)')


def _tk_split(*elements, raw=False):
    ns = types.SimpleNamespace(_raw_command=raw)
    return ui_tkinter.ListBox._split_choices(ns, elements)


def test_tk_insert_normalises_like_the_constructor():
    codes, texts = _tk_split('plain', ('c', 'Name'), ('d', 'Other', 'desc'),
                             {'code': 'e', 'name': 'Dict'})
    assert codes == ['plain', 'c', 'd', 'e']
    assert texts == ['plain', 'Name', 'Other (desc)', 'Dict']


def test_tk_raw_mode_passes_rows_through():
    codes, texts = _tk_split('x', 'y', raw=True)
    assert codes == ['x', 'y'] and texts == ['x', 'y']


def test_tk_on_select_reads_the_row_when_values_are_short():
    """The guard for anything still bypassing insert/delete."""
    got = []
    ns = types.SimpleNamespace(curselection=lambda: (2,),
                               command=got.append,
                               choices=['only-one'],
                               _window=None,
                               get=lambda i: 'row-{}'.format(i))
    ui_tkinter.ListBox._on_select(ns)
    assert got == ['row-2']


def test_tk_on_select_uses_the_value_when_it_has_one():
    got = []
    ns = types.SimpleNamespace(curselection=lambda: (1,),
                               command=got.append,
                               choices=['a', 'b'],
                               _window=None,
                               get=lambda i: 'row-{}'.format(i))
    ui_tkinter.ListBox._on_select(ns)
    assert got == ['b']
