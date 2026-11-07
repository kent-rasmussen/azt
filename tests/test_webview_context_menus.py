"""Per-widget right-click menus under webview (Kent, 2026-11-06: the play
button's praat open and the sort page's word menu showed only the page's
menu). sort_ui.attach_context_menu posts at event.x_root and asks the posted
menu winfo_exists/unpost/grab_release, as under Tk."""
import pytest


def test_events_carry_root_coordinates():
    wv = pytest.importorskip('frontend.ui_webview')
    e = wv._event_from({'x': 12, 'y': 34, 'key': None})
    assert (e.x_root, e.y_root) == (12, 34)
    assert (e.x, e.y) == (12, 34)


def test_a_menu_answers_what_a_posted_menu_is_asked():
    wv = pytest.importorskip('frontend.ui_webview')
    m = wv.Menu(object())          # no window: _js with None is a no-op
    assert m.winfo_exists()
    m.unpost()
    m.grab_release()
    m.destroy()
    assert not m.winfo_exists()
