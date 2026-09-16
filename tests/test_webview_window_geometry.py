# coding=UTF-8
"""The frame/client reading behind `--log-resizes`.

WHY THIS HAS A TEST AT ALL. It is a diagnostic, and diagnostics do not
usually earn tests — except that this one exists because a previous reading
of the same fault was wrong, and wrong in a way that cost a day. The window
sizing item (`agenda/webview_window_sizing.md`) had four debounced samples
showing a constant 52x89 shortfall in the page's client area; I read that as
client-side decorations growing into a frame that stayed put, which fit
everything except what Kent could see — "I'm seeing the window frame
resize/move, not content change" (2026-09-16).

The page can only ever see `innerWidth/innerHeight`. `_geometry_of` is the
one place that reads the FRAME as well, and the gap between the two is the
number the next theory will be built on. So the arithmetic is pinned here,
along with the promise that every failure is a VALUE and not an exception: a
diagnostic that can raise inside a resize report would take the window with
it.

Plain functions, fake toolkit objects — no pywebview, no display, no GTK.
"""
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

ui_webview = pytest.importorskip('frontend.ui_webview',
                                 reason='needs the webview backend importable')

_geometry_of = ui_webview._geometry_of
_format_geometry = ui_webview._format_geometry
_inset_of = ui_webview._inset_of

WIDGETS_JS = (Path(__file__).resolve().parents[1]
              / 'frontend' / 'webview_html' / 'widgets.js')


class QtWindow:
    """A QMainWindow-shaped stand-in: geometry() and frameGeometry()."""

    def __init__(self, frame, inner):
        self._frame, self._inner = frame, inner

    def frameGeometry(self):
        return _QRect(*self._frame)

    def geometry(self):
        return _QRect(*self._inner)


class _QRect:
    """QRect-shaped: x/y/width/height are accessor METHODS. The difference
    from `Rect` is the whole reason `_geometry_of` has two branches."""

    def __init__(self, x, y, w, h):
        self._v = (x, y, w, h)

    def x(self):
        return self._v[0]

    def y(self):
        return self._v[1]

    def width(self):
        return self._v[2]

    def height(self):
        return self._v[3]


class GdkWindow:
    """A Gdk.Window-shaped stand-in.

    `get_frame_extents` is present and MUST NOT BE CALLED — it is the
    out-parameter API that corrupted the process (see
    `test_frame_extents_is_never_called`), so the fake fails loudly if
    anything reaches for it again."""

    def __init__(self, size=None):
        self._size = size

    def get_frame_extents(self):
        raise AssertionError('get_frame_extents corrupts memory; see '
                             '_geometry_of')

    def get_width(self):
        return self._size[0]

    def get_height(self):
        return self._size[1]


class GtkWindow:
    """A Gtk.Window-shaped stand-in: get_size/get_position/get_window."""

    def __init__(self, size, position, gdkwin=None):
        self._size, self._position, self._gdkwin = size, position, gdkwin

    def get_size(self):
        return self._size

    def get_position(self):
        return self._position

    def get_window(self):
        return self._gdkwin


def test_nothing_reachable_says_so_rather_than_raising():
    assert _geometry_of(None) is None
    assert 'not reachable' in _format_geometry(None)


def test_qt_reports_both_boxes():
    geo = _geometry_of(QtWindow(frame=(10, 20, 1052, 859),
                                inner=(10, 89, 1000, 770)))
    assert geo['frame'] == (10, 20, 1052, 859)
    assert geo['inner'] == (10, 89, 1000, 770)


def test_gtk_reports_both_boxes():
    """`gtk_window_get_size` excludes the client-side decorations and the
    GdkWindow includes them, so the difference between the two is the
    inset — with no out-parameter anywhere."""
    win = GtkWindow(size=(1000, 770), position=(10, 89),
                    gdkwin=GdkWindow(size=(1052, 859)))
    geo = _geometry_of(win)
    assert geo['inner'] == (10, 89, 1000, 770)
    assert geo['frame'] == (10, 89, 1052, 859)
    assert 'error' not in geo


def test_frame_extents_is_never_called():
    """IT CORRUPTS THE PROCESS. `gdk_window_get_frame_extents(window,
    GdkRectangle *rect)` takes its rectangle as a CALLER-ALLOCATED
    out-parameter, and calling it through PyGObject left the process damaged:
    a later `kill -USR1` segfaulted instead of dumping — at boot, on the sort
    page, and with every thread parked. Three states with nothing in common,
    which is corruption rather than anything the app was doing. Kent,
    2026-09-16, after the switch that skips this whole function:
    "--no-frame-inset resolves this".

    The fake raises if it is called, so this test fails rather than
    segfaulting a future run."""
    win = GtkWindow(size=(1000, 770), position=(10, 89),
                    gdkwin=GdkWindow(size=(1052, 859)))
    geo = _geometry_of(win)         # would raise AssertionError if called
    assert geo['frame'][2:] == (1052, 859)
    src = (Path(__file__).resolve().parents[1]
           / 'frontend' / 'ui_webview.py').read_text(encoding='utf-8')
    body = src.split('def _geometry_of', 1)[1].split('\ndef ', 1)[0]
    calls = [line for line in body.splitlines()
             if 'get_frame_extents' in line and not line.lstrip().startswith('#')]
    assert not calls, 'get_frame_extents is back in _geometry_of: {}'.format(calls)


def test_the_inset_is_the_difference_between_the_two_boxes():
    """THE NUMBER THE NEXT THEORY RESTS ON. 52x89 inferred from client
    shrinkage alone produced a theory Kent's eyes contradicted; reported as
    frame-minus-client it is measured instead."""
    said = _format_geometry(_geometry_of(
                QtWindow(frame=(0, 0, 1052, 859), inner=(0, 0, 1000, 770))))
    assert 'decoration 52x89' in said
    assert 'frame 1052x859' in said
    assert 'client 1000x770' in said


def test_a_window_with_neither_toolkit_api_is_named_not_raised():
    class Odd:
        pass

    geo = _geometry_of(Odd())
    assert 'Odd' in geo['error']
    assert 'unreadable' in _format_geometry(geo)


def test_a_getter_that_raises_becomes_a_value():
    class Broken:
        def frameGeometry(self):
            raise RuntimeError('window is gone')

        def geometry(self):
            raise RuntimeError('window is gone')

    geo = _geometry_of(Broken())
    assert 'window is gone' in geo['error']
    # And still formats, because the caller is inside a resize report.
    assert _format_geometry(geo)


def test_one_box_alone_still_reports_without_an_inset():
    """Half the reading is worth logging; a made-up inset is not."""
    win = GtkWindow(size=(1000, 770), position=(10, 89), gdkwin=None)
    said = _format_geometry(_geometry_of(win))
    assert 'client 1000x770 at 10,89' in said
    assert 'decoration' not in said


def test_the_inset_is_what_gets_added_to_a_pinned_size():
    """WHY THE PINS NEED IT. `resize()` is in client units and lands; the
    window's default size and its MIN_SIZE hint are in FRAME units under
    client-side decorations, and were being given the client figure — so the
    window fell to exactly the pinned number as a frame and the page came
    out one decoration short. Measured 2026-09-16: fit asked 1331x773, frame
    went to 1331x773, client to 1279x684."""
    win = QtWindow(frame=(0, 0, 1383, 862), inner=(0, 0, 1331, 773))
    assert _inset_of(win) == (52, 89)


def test_no_inset_when_there_is_nothing_to_read():
    assert _inset_of(None) == (0, 0)
    assert _inset_of(GtkWindow(size=(800, 600), position=(0, 0),
                               gdkwin=None)) == (0, 0)


@pytest.mark.parametrize('frame, why', [
    ((0, 0, 100, 600), 'narrower than its own client area'),
    ((0, 0, 800, 6000), 'taller than any decoration'),
])
def test_a_nonsense_reading_adds_nothing(frame, why):
    """A nonsense reading must become NO adjustment, never a nonsense
    window: this number is added to every window the app fits."""
    win = QtWindow(frame=frame, inner=(0, 0, 800, 600))
    assert _inset_of(win) == (0, 0), why


def test_the_switch_pins_in_client_units_again(monkeypatch):
    win = QtWindow(frame=(0, 0, 1383, 862), inner=(0, 0, 1331, 773))
    monkeypatch.setattr(ui_webview.sys, 'argv',
                        ['main.py', '--webview', '--no-frame-inset'])
    assert _inset_of(win) == (0, 0)


def test_the_page_reporter_can_be_told_to_skip_the_debounce():
    """The switch has to reach the page, or every sample is still the
    settled one — which is the whole reason the previous evidence was thin.
    """
    js = WIDGETS_JS.read_text(encoding='utf-8')
    assert 'function installResizeReporter(wid, everySample)' in js
    body = js.split('function installResizeReporter', 1)[1].split('\n}', 1)[0]
    # The bypass must come BEFORE the timer, or the debounce still applies
    # and the switch reports exactly what it reported without it.
    bypass = re.search(r'if \(everySample\)[^\n]*\breturn\b', body)
    assert bypass, "nothing skips the debounce"
    assert bypass.start() < body.index('setTimeout(send')


def test_python_passes_the_flag_to_the_page():
    src = (Path(__file__).resolve().parents[1]
           / 'frontend' / 'ui_webview.py').read_text(encoding='utf-8')
    assert 'installResizeReporter({}, {})' in src, \
        'the reporter is installed without a second argument'
    assert "'true' if _switch('--log-resizes') else 'false'" in src, \
        'the second argument is not the --log-resizes switch'
