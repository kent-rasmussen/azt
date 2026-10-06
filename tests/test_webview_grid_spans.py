# coding=UTF-8
"""Spans mean the same thing in both UI backends.

WHY, and it was Kent's question rather than a symptom: *"Have you looked at
span variable usage between these UI backends? this page is what it is,
layout wise, with a couple uses of rowspan."* The sort page's layout leans on
`rowspan`/`columnspan`, so a backend that reads them differently lays the page
out differently.

Three of the four places they could diverge were already fine — constructor
extraction is identical (`ui_webview.py:1499` / `ui_tkinter.py:1304`), and
`_applyGrid` emits `grid-row: N / span M`. Two were not:

  * `.grid()` as a METHOD did a raw `_grid_opts.update(kwargs)`, so
    `.grid(colspan=2)` stored `colspan` while the page reads `columnspan`.
    Latent — every call site in the suite passes `columnspan` — but it is the
    accept-and-drop shape this backend keeps getting wrong, and tkinter's own
    `.grid()` would RAISE on `colspan` rather than accept it quietly.
  * `grid_size()` counted `max(row) + 1` and ignored spans, so a frame with
    one widget at row 0 spanning 4 rows reported ONE row. tkinter's is Tk's
    own and includes the extent. `nrows()` is the consumer that matters: it is
    how the app finds "the row after everything", and `sort_ui.py:705` grids
    the OK canary at `buttonframe.content.nrows()` — too small a number puts
    it on top of existing content.

Real methods against stand-in widgets, per tests/README.md.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

ui_webview = pytest.importorskip('frontend.ui_webview',
                                 reason='needs the webview backend importable')

_W = ui_webview._WebviewWidget


class Child:
    """A gridded child: only the fields grid_size reads."""

    def __init__(self, **opts):
        self._has_grid = True
        self._grid_opts = dict(opts)


class Holder:
    """A container answering grid_size/nrows with the real methods.

    `grid_size` is on the base widget; `nrows` is on `Frame` (:3100), which
    is where the app's containers get it. Borrowing both from the base class
    was an AttributeError at COLLECTION time, which stopped the whole suite
    rather than failing one test — so the other four files added the same day
    did not run either."""

    grid_size = _W.grid_size
    nrows = ui_webview.Frame.nrows

    def __init__(self, *children):
        self._children = list(children)


class Griddable:
    """A widget answering `.grid()` with the real method, sending nothing."""

    _GRID_ALIASES = _W._GRID_ALIASES
    grid = _W.grid
    _wid = 4

    def __init__(self):
        self._grid_opts = {}
        self._has_grid = False


# ── grid_size / nrows ────────────────────────────────────────────────

def test_a_rowspan_counts_as_the_rows_it_occupies():
    """One widget at row 0 spanning 4 rows is a FOUR-row grid. This reported
    one, which is what `nrows()` then handed to the next caller."""
    assert Holder(Child(row=0, column=0, rowspan=4)).grid_size() == (1, 4)


def test_a_columnspan_counts_as_the_columns_it_occupies():
    assert Holder(Child(row=0, column=1, columnspan=2)).grid_size() == (3, 1)


def test_a_span_starting_part_way_down_extends_from_there():
    """`row=1, rowspan=2` occupies rows 1 and 2, so the grid is 3 deep —
    which is the non-macrosort verify layout (`sort_ui.py:747`)."""
    assert Holder(Child(row=1, column=0, rowspan=2)).nrows() == 3


def test_the_widest_and_deepest_children_both_count():
    holder = Holder(Child(row=0, column=0, rowspan=3),
                    Child(row=0, column=0, columnspan=5),
                    Child(row=7, column=1))
    assert holder.grid_size() == (5, 8)


def test_no_span_still_means_one_track():
    assert Holder(Child(row=2, column=3)).grid_size() == (4, 3)


def test_an_ungridded_child_occupies_nothing():
    child = Child(row=9, column=9)
    child._has_grid = False
    assert Holder(child).grid_size() == (0, 0)


def test_an_empty_container_is_zero_by_zero():
    assert Holder().grid_size() == (0, 0)
    assert Holder().nrows() == 0


@pytest.mark.parametrize('span', [0, None, '', 'two', -3])
def test_a_nonsense_span_counts_as_one(span):
    """`nrows()` positions real widgets. A bad span must not make the grid
    SHRINK — that puts the next widget on top of this one."""
    assert Holder(Child(row=2, column=0, rowspan=span)).nrows() == 3


def test_a_span_given_as_a_string_of_digits_is_honoured():
    """tkinter accepts what Tcl accepts, and the app passes computed values
    around; `'2'` is a span, not nonsense."""
    assert Holder(Child(row=0, column=0, rowspan='2')).nrows() == 2


# ── .grid() as a method ──────────────────────────────────────────────

def test_the_method_normalises_colspan():
    w = Griddable()
    w.grid(row=1, column=0, colspan=3, sticky='ew')
    assert w._grid_opts['columnspan'] == 3
    assert 'colspan' not in w._grid_opts, \
        'the page reads columnspan; colspan would be dropped'


def test_the_method_normalises_the_short_position_spellings():
    w = Griddable()
    w.grid(r=2, c=5)
    assert w._grid_opts['row'] == 2
    assert w._grid_opts['column'] == 5
    assert 'r' not in w._grid_opts and 'c' not in w._grid_opts


def test_an_explicit_long_spelling_wins_over_its_alias():
    """Both given is a caller contradicting itself; the name the page reads
    is the one to believe."""
    w = Griddable()
    w.grid(columnspan=2, colspan=9)
    assert w._grid_opts['columnspan'] == 2


def test_rowspan_needs_no_translation_and_is_kept():
    w = Griddable()
    w.grid(row=0, rowspan=4)
    assert w._grid_opts['rowspan'] == 4


def test_a_regrid_keeps_what_it_did_not_mention():
    """`.grid()` updates; it does not replace. A caller re-gridding to move a
    row must not lose its span."""
    w = Griddable()
    w.grid(row=0, column=0, columnspan=2)
    w.grid(row=5)
    assert w._grid_opts == {'row': 5, 'column': 0, 'columnspan': 2}


def test_a_bare_regrid_changes_nothing():
    w = Griddable()
    w.grid(row=3, rowspan=2)
    before = dict(w._grid_opts)
    w.grid()
    assert w._grid_opts == before
