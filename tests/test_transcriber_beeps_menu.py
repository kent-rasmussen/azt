# coding=UTF-8
"""Configuring tone beeps is a popup panel at the pointer, not a window.

Kent, 2026-09-22, on the "Configure Tone Beeps" window — six buttons in the
corner of an empty page plus Quit: "this should be a context menu. don't
kill the independent usage of this module!" Then, on six one-line menu
entries for three binary settings: "a bit weird … preferred would be
-|pitch|+ / -|L<->H|+ / -|speed|+", each click changing the setting, playing
at the new setting and leaving the user able to keep adjusting — and "I want
it to go away on a click anywhere else, like context menus".

So `ui.Popup`, on both backends, holding a 3×3 grid. The Transcriber runs
standalone (`python -m frontend.transcriber`), so the popup needs nothing
from the app. Source-level checks here, because posting one needs a display;
the two backends' Popup mechanics have their own tests below.
"""
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = (ROOT / 'frontend' / 'transcriber.py').read_text()


def _configurebeeps():
    start = SRC.index('def configurebeeps(')
    end = SRC.index('\n    def ', start + 1)
    return SRC[start:end]


def test_it_is_a_popup_at_the_pointer():
    body = _configurebeeps()
    assert 'ui.Popup(' in body
    assert 'ui.Window(' not in body
    assert 'ui.Menu(' not in body, "six entries for three binary options was the weird part"


def test_three_rows_minus_label_plus_under_a_title():
    body = _configurebeeps()
    assert '_("Tone Playback")' in body, \
        "an undecorated panel has no title bar; the title is its first row"
    for label in ('pitch', 'L↔H', 'speed'):
        assert '_("{}")'.format(label) in body, label
    assert "text='-'" in body and "text='+'" in body


def test_each_click_changes_and_plays():
    """Kent: "clicking on a setting should change the setting, play at the
    new settings, and leave the user able to continue modifying settings."
    """
    body = _configurebeeps()
    assert 'self.playbeeps(' in body
    for change in ('higher', 'lower', 'wider', 'narrower', 'longer', 'shorter'):
        assert 'self.beeps.{}'.format(change) in body, change


def test_it_reads_both_backends_coordinates():
    """tkinter gives `x_root`; the webview event gives page `x`/`y`."""
    body = _configurebeeps()
    assert "'x_root'" in body and "'x'" in body


def test_the_module_still_runs_on_its_own():
    assert 'if __name__ == "__main__":' in SRC
    assert 'ui.Root(program)' in SRC


# ── the `sticky` menu option, kept for a menu that wants it ───────────────
def test_tk_sticky_menu_reposts_after_the_command():
    """Tk unposts on invoke; sticky means post again where it was, once the
    command has run."""
    tk = pytest.importorskip('frontend.ui_tkinter',
                             reason='needs tkinter importable')
    order = []
    ns = types.SimpleNamespace(_at=(10, 20),
                               after_idle=lambda fn: (order.append('idle'), fn()),
                               post=lambda x, y: order.append(('post', x, y)))
    tk.Menu._reposting(ns, lambda: order.append('command'))()
    assert order == ['command', 'idle', ('post', 10, 20)]


def test_tk_sticky_menu_never_posted_does_not_repost():
    tk = pytest.importorskip('frontend.ui_tkinter',
                             reason='needs tkinter importable')
    order = []
    ns = types.SimpleNamespace(_at=None,
                               after_idle=lambda fn: order.append('idle'),
                               post=lambda x, y: order.append('post'))
    tk.Menu._reposting(ns, lambda: order.append('command'))()
    assert order == ['command']


def test_webview_sticky_menu_keeps_its_element_on_click():
    wv = pytest.importorskip('frontend.ui_webview',
                             reason='needs the webview backend importable')
    parent = types.SimpleNamespace(_wv_window=None)
    assert wv.Menu(parent, sticky=True)._sticky is True
    assert wv.Menu(parent)._sticky is False
    src = (ROOT / 'frontend' / 'ui_webview.py').read_text()
    click = src[src.index('def on_menuclick('):]
    click = click[:click.index('_api.unregister')]
    assert 'if not self._sticky:' in click


# ── the two Popups ─────────────────────────────────────────────────────────
def test_webview_popup_is_positioned_by_the_page_not_gridded():
    wv = pytest.importorskip('frontend.ui_webview',
                             reason='needs the webview backend importable')
    js = (ROOT / 'frontend' / 'webview_html' / 'widgets.js').read_text()
    case = js[js.index("case 'popup':"):]
    case = case[:case.index("\n        case '")]
    assert "addEventListener('mousedown', _outside" in case
    assert "e.key === 'Escape'" in case
    assert "'dismiss'" in case, "Python must be told when the page took it down"
    assert 'setTimeout' in case, \
        "listeners must attach after the opening right-click has finished dispatching"
    css = (ROOT / 'frontend' / 'webview_html' / 'grid.css').read_text()
    assert 'position: fixed' in css[css.index('.wv-popup {'):]
    assert hasattr(wv, 'Popup')


def test_webview_popup_dismissal_reports_once_and_calls_back():
    wv = pytest.importorskip('frontend.ui_webview',
                             reason='needs the webview backend importable')
    called = []
    ns = types.SimpleNamespace(_exists=True, parent=None, _wid=5,
                               _on_dismiss=lambda: called.append('gone'))
    wv.Popup._dismissed(ns)
    wv.Popup._dismissed(ns)          # a second report changes nothing
    assert called == ['gone']
    assert ns._exists is False


def test_tk_popup_outside_press_dismisses_and_inside_does_not():
    tk = pytest.importorskip('frontend.ui_tkinter',
                             reason='needs tkinter importable')
    gone = []
    ns = types.SimpleNamespace(winfo_width=lambda: 100, winfo_height=lambda: 50,
                               dismiss=lambda: gone.append('dismissed'))
    # a press the grab delivered to the popup itself, outside its box
    tk.Popup._press(ns, types.SimpleNamespace(widget=ns, x=150, y=10))
    assert gone == ['dismissed']
    # a press on the popup's own background, inside
    tk.Popup._press(ns, types.SimpleNamespace(widget=ns, x=10, y=10))
    assert gone == ['dismissed']
    # a press on one of its controls: the control's own business
    tk.Popup._press(ns, types.SimpleNamespace(widget=object(), x=-5, y=-5))
    assert gone == ['dismissed']


def test_tk_popup_takes_no_grab():
    """THE REGRESSION GUARD. The panel held a local grab to make "click
    anywhere else" work, on the theory that the grab redirects outside
    presses to it the way `tk_popup` does for a menu. It does not — Kent's
    screenshot showed two panels stacked, meaning the right-click that opened
    the second (a press outside the first) did not dismiss the first. What
    unposts a Tk MENU is Tk's own menu code under that grab, which a plain
    toplevel does not inherit; the grab could then only keep the press from
    reaching anything else. Don't put it back."""
    tk = pytest.importorskip('frontend.ui_tkinter',
                             reason='needs tkinter importable')
    src = (ROOT / 'frontend' / 'ui_tkinter.py').read_text()
    start = src.index('class Popup(')
    body = src[start:src.index('\nclass ', start + 1)]
    code = '\n'.join(line for line in body.splitlines()
                     if not line.strip().startswith('#'))
    code = code[code.index('_open=[]'):]       # past the docstring, which
    #                                            discusses the grab at length
    assert 'grab_set' not in code, "the grab was the bug"
    assert 'grab_release' not in code
    assert hasattr(tk.Popup, 'dismiss_open')


def test_tk_popup_dismisses_armed_panels_only():
    """An unarmed panel is one whose opening press is still being dispatched.
    Dismissing it there would mean right-click appeared to do nothing."""
    tk = pytest.importorskip('frontend.ui_tkinter',
                             reason='needs tkinter importable')
    gone = []
    armed = types.SimpleNamespace(_armed=True,
                                  dismiss=lambda: gone.append('armed'))
    unarmed = types.SimpleNamespace(_armed=False,
                                    dismiss=lambda: gone.append('unarmed'))
    original = tk.Popup._open
    tk.Popup._open = [armed, unarmed]
    try:
        tk.Popup.dismiss_open()
    finally:
        tk.Popup._open = original
    assert gone == ['armed']


def test_tk_popup_forget_deregisters_only_its_own_destroy():
    """`<Destroy>` on a toplevel fires for every descendant too."""
    tk = pytest.importorskip('frontend.ui_tkinter',
                             reason='needs tkinter importable')
    original = tk.Popup._open
    ns = types.SimpleNamespace(_armed=True)
    tk.Popup._open = [ns]
    try:
        tk.Popup._forget(ns, types.SimpleNamespace(widget=object()))
        assert tk.Popup._open == [ns], "a child's destroy is not the panel's"
        tk.Popup._forget(ns, types.SimpleNamespace(widget=ns))
        assert tk.Popup._open == []
        assert ns._armed is False
        tk.Popup._forget(ns, types.SimpleNamespace(widget=ns))   # twice is fine
    finally:
        tk.Popup._open = original


def test_tk_popup_binds_its_owner_once_not_once_per_panel():
    """tkinter's `unbind(sequence, funcid)` clears EVERY binding for that
    sequence, so a per-panel binding could not be removed without taking out
    whatever else the window binds. One dispatcher, bound once."""
    tk = pytest.importorskip('frontend.ui_tkinter',
                             reason='needs tkinter importable')
    bound = []
    owner = types.SimpleNamespace(
        bind=lambda seq, fn, add=None: bound.append(seq))
    first = types.SimpleNamespace(_armed=False, _owner=owner,
                                  winfo_exists=lambda: True)
    tk.Popup._arm(first)
    assert first._armed is True
    assert sorted(bound) == ['<ButtonPress>', '<Escape>']
    second = types.SimpleNamespace(_armed=False, _owner=owner,
                                   winfo_exists=lambda: True)
    tk.Popup._arm(second)
    assert sorted(bound) == ['<ButtonPress>', '<Escape>'], "bound twice"


def test_tk_popup_without_an_owner_still_arms():
    """`_owner_toplevel` returns None if the parent cannot give one; Escape on
    the panel itself must still work, so arming must not raise."""
    tk = pytest.importorskip('frontend.ui_tkinter',
                             reason='needs tkinter importable')
    ns = types.SimpleNamespace(_armed=False, _owner=None,
                               winfo_exists=lambda: True)
    tk.Popup._arm(ns)
    assert ns._armed is True
