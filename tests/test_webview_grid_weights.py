# coding=UTF-8
"""tkinter row/column weights reach CSS Grid as tracks.

WHY. `grid_rowconfigure` and `grid_columnconfigure` were bare `pass` in
ui_webview, with the comment "CSS Grid handles this automatically". It does
not: `weight=1` means "this track takes the space left over", and a CSS Grid
track is CONTENT-SIZED by default. So every weight in the app was accepted
and discarded — the dropped-option class, with a comment asserting there was
nothing to drop.

WHAT IT COST. `sort_ui.py:666` weights row 1 so the word list fills the kiosk
page. Discarded, the row was content-sized, so the scroller's
`max-height: min(100%, 0.9 * screen)` had no definite height to resolve its
`100%` term against and fell back to the screen-relative backstop — 90% of
the screen, with the title and instructions stacked above it. Taller than the
window, so the page scrolled AND the list scrolled inside it: Kent's double
scroll on the sort page, 2026-09-16.

The `100%` term was written to be exactly this fix (`grid.css`: "when the row
has a definite height the scroller fills it and scrolls only past that"). It
could never bind, because nothing in the height chain was definite — which is
why the stylesheet half is pinned here too.

Real methods against a stand-in `self`, per tests/README.md.
"""
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

ui_webview = pytest.importorskip('frontend.ui_webview',
                                 reason='needs the webview backend importable')

_W = ui_webview._WebviewWidget
HTML = Path(__file__).resolve().parents[1] / 'frontend' / 'webview_html'
GRID_CSS = HTML / 'grid.css'
WIDGETS_JS = HTML / 'widgets.js'


class FakeWidget:
    """A widget-shaped stand-in that records what would be sent."""

    _TRACK_KEYS = _W._TRACK_KEYS
    grid_rowconfigure = _W.grid_rowconfigure
    grid_columnconfigure = _W.grid_columnconfigure
    rowconfigure = _W.rowconfigure
    columnconfigure = _W.columnconfigure
    _track_configure = _W._track_configure

    _wid = 3

    def __init__(self):
        self.sends = 0

    def _send_grid_tracks(self):
        self.sends += 1

    @property
    def rows(self):
        return getattr(self, '_tracks_row', {})

    @property
    def cols(self):
        return getattr(self, '_tracks_column', {})


def test_a_row_weight_is_recorded():
    w = FakeWidget()
    w.grid_rowconfigure(1, weight=1)
    assert w.rows == {1: {'weight': 1}}
    assert w.sends == 1


def test_a_column_weight_is_recorded_separately():
    w = FakeWidget()
    w.grid_rowconfigure(1, weight=1)
    w.grid_columnconfigure(1, weight=3)
    assert w.rows == {1: {'weight': 1}}
    assert w.cols == {1: {'weight': 3}}


def test_the_short_spellings_are_the_same_call():
    """tkinter accepts both, and the app uses both."""
    w = FakeWidget()
    w.rowconfigure(0, weight=2)
    w.columnconfigure(0, weight=2)
    assert w.rows == {0: {'weight': 2}}
    assert w.cols == {0: {'weight': 2}}


def test_minsize_is_kept_alongside_weight():
    w = FakeWidget()
    w.grid_rowconfigure(2, weight=1, minsize=120)
    assert w.rows == {2: {'weight': 1, 'minsize': 120}}


def test_reconfiguring_the_same_track_merges_rather_than_replaces():
    w = FakeWidget()
    w.grid_rowconfigure(1, minsize=80)
    w.grid_rowconfigure(1, weight=1)
    assert w.rows == {1: {'minsize': 80, 'weight': 1}}


def test_saying_the_same_thing_twice_sends_nothing_the_second_time():
    """The template is re-sent whole, so a no-change call is pure page
    traffic. The app re-weights on every rebuild."""
    w = FakeWidget()
    w.grid_rowconfigure(1, weight=1)
    w.grid_rowconfigure(1, weight=1)
    assert w.sends == 1


def test_weight_zero_is_a_value_and_is_kept():
    """`weight=0` is how tkinter says "and this one does NOT grow" — a
    meaningful thing to say about a track that had a weight before."""
    w = FakeWidget()
    w.grid_rowconfigure(1, weight=1)
    w.grid_rowconfigure(1, weight=0)
    assert w.rows == {1: {'weight': 0}}
    assert w.sends == 2


@pytest.mark.parametrize('index', [-1, 'nonsense', None])
def test_an_index_that_is_not_a_track_is_ignored(index):
    w = FakeWidget()
    w.grid_rowconfigure(index, weight=1)
    assert w.rows == {}
    assert w.sends == 0


def test_an_unsupported_option_does_not_pretend_to_work():
    """This method is in this state because the last thing it dropped was
    never mentioned. `pad`/`uniform` have no CSS Grid equivalent worth
    faking, so they are reported rather than silently accepted."""
    w = FakeWidget()
    w.grid_rowconfigure(1, pad=4)
    assert w.rows == {}
    said = [line for line in ui_webview._said if 'pad' in line]
    assert said, 'nothing was said about the dropped option'
    assert 'ignored' in said[0]


def test_an_unsupported_option_alongside_a_good_one_still_applies_the_good_one():
    w = FakeWidget()
    w.grid_rowconfigure(1, weight=1, uniform='a')
    assert w.rows == {1: {'weight': 1}}


def test_the_payload_names_the_widget_and_both_axes(monkeypatch):
    sent = []
    monkeypatch.setattr(ui_webview, '_js',
                        lambda wv, code: sent.append(code))

    class Real(FakeWidget):
        _send_grid_tracks = _W._send_grid_tracks
        _wv_window = object()

    w = Real()
    w.grid_rowconfigure(1, weight=1)
    assert len(sent) == 1
    assert sent[0].startswith('setGridTracks(3, ')
    # JSON object keys are strings; the page reads them back as such.
    assert '"1": {"weight": 1}' in sent[0]
    assert sent[0].rstrip().endswith('{})')      # no columns configured yet


def test_nothing_is_sent_before_there_is_a_window(monkeypatch):
    """Weights can be set while a window is still being built. `_js` queues,
    but there is nothing to queue against without a window."""
    sent = []
    monkeypatch.setattr(ui_webview, '_js', lambda wv, code: sent.append(code))

    class Real(FakeWidget):
        _send_grid_tracks = _W._send_grid_tracks

    Real().grid_rowconfigure(1, weight=1)
    assert sent == []


# ── The page side ────────────────────────────────────────────────────

def test_the_page_turns_a_weight_into_an_fr_track():
    js = WIDGETS_JS.read_text(encoding='utf-8')
    assert 'function setGridTracks(wid, rows, cols)' in js
    body = js.split('function _trackSize', 1)[1].split('\n}', 1)[0]
    assert "'fr'" in body or "+ 'fr'" in body or 'fr)' in body
    # An unweighted track stays content-sized, which is what it already was.
    assert "'auto'" in body


def test_the_page_falls_back_to_the_root_for_a_window():
    """A window is not a DOM widget, and `Window.post_tk_init` weights the
    window's own rows. In a window the window IS the page."""
    js = WIDGETS_JS.read_text(encoding='utf-8')
    body = js.split('function setGridTracks', 1)[1].split('\n}', 1)[0]
    assert "getElementById('root')" in body


# ── The stylesheet side: the height chain the fr tracks need ─────────

def _rule(css, selector):
    """The declarations of the first rule whose selector list matches."""
    match = re.search(re.escape(selector) + r'\s*\{([^}]*)\}', css)
    return match.group(1) if match else ''


def test_the_document_has_a_definite_height():
    """Without this an `fr` track has no free space to take a share of, and
    a percentage max-height is not a constraint. This is the half that made
    the other two unable to work however correctly they were written."""
    css = GRID_CSS.read_text(encoding='utf-8')
    assert 'height: 100%' in _rule(css, 'html, body')
    assert 'height: 100%' in _rule(css, '#root')


def test_measuring_releases_the_document_height():
    """A fit asks "how big would you like to be", and a page pinned to the
    window cannot answer — the same reason `#root` and `.wv-window` are
    already released. The class sits ON html, so both are named."""
    css = GRID_CSS.read_text(encoding='utf-8')
    released = _rule(css, 'html.wv-measuring,\nhtml.wv-measuring body')
    assert 'max-content' in released


def test_unweighted_rows_do_not_stretch():
    """CSS Grid's `align-content: normal` acts as `stretch`, which hands
    leftover space to AUTO tracks — so a definite-height page would inflate
    its title row. tkinter's `weight=0` does not grow, and its `grid_anchor`
    default is 'nw'."""
    css = GRID_CSS.read_text(encoding='utf-8')
    assert 'align-content: start' in _rule(css, '#root,\n.wv-frame,\n.wv-container')


def test_the_column_axis_is_left_alone():
    """Widths were already definite, so nothing about column distribution
    changes with this fix — and adding it anyway would put a second untested
    alteration inside one measurement."""
    css = GRID_CSS.read_text(encoding='utf-8')
    block = _rule(css, '#root,\n.wv-frame,\n.wv-container')
    assert 'justify-content' not in block


def test_the_splash_still_centres_itself():
    """It overrides `align-content` and must keep winning on specificity."""
    css = GRID_CSS.read_text(encoding='utf-8')
    at_splash = css.find('body[data-page="splash"] #root,')
    at_default = css.find('#root,\n.wv-frame,\n.wv-container')
    assert at_default != -1 and at_splash != -1
    assert 'align-content: center' in css[at_splash:at_splash + 400]
