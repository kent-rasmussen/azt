# coding=UTF-8
"""The webview ContextMenu actually makes a menu.

WHY. It was a four-method stub whose methods all returned None, so nothing
raised and every `setcontext()` in the app ran to completion against a menu
that did not exist. The cost was a route the user could not take: Sound
Settings is reached by right-clicking a task window and has no other way in
(`tasks/sound.py:33`), which is what Kent hit on 2026-09-11 — "I'm talking
about the context menu I used to get to the sound settings".

The `Menu` class it builds on was never the problem: `add_command` and
`tk_popup` (a positioned `.wv-menu` div, dismissed on an outside click) have
worked all along. Three things were missing around it, and each is pinned
below:

  * `parent.context = self`, which both call sites depend on —
    `ui_shell.py:2979` and `:3733` construct `ui.ContextMenu(self)` and then
    everyone else reaches the object as `window.context`;
  * `menuitem`, the method every `setcontext()` calls;
  * a binding, and a `do_popup` for it to reach.

These are plain methods on a stand-in `self` — no pywebview, no display. A
stand-in parent with no `_wv_window` also makes `Menu.tk_popup` a no-op, so
the popup can be exercised without a page.
"""
import sys
import types
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

ui_webview = pytest.importorskip('frontend.ui_webview',
                                 reason='needs the webview backend importable')

ContextMenu = ui_webview.ContextMenu


class Parent:
    """A window-shaped stand-in: records binds and setcontext calls."""

    def __init__(self, setcontext=None):
        self.bound = {}
        self.setcontext_calls = 0
        self._setcontext = setcontext

    def bind(self, event, handler, add=None):
        self.bound[event] = handler

    def setcontext(self):
        self.setcontext_calls += 1
        if self._setcontext:
            self._setcontext(self)


def test_construction_publishes_itself_as_parent_context():
    """THE BUG THAT HID THE OTHERS. Both call sites construct and discard the
    return value, so an instance that does not register itself on the parent
    is unreachable — and every later `window.context.…` fails or, in a stub's
    case, silently does nothing."""
    parent = Parent()
    menu = ContextMenu(parent)
    assert parent.context is menu


def test_construction_binds_the_context_menu_event():
    """Nothing was bound, so no gesture could produce a menu."""
    parent = Parent()
    ContextMenu(parent)
    assert '<<ContextMenu>>' in parent.bound


def test_it_does_NOT_bind_while_the_page_is_still_LOADING():
    """THE QT CRASH GUARD. Binding during window construction issued one
    extra `evaluate_js` per window while its page was loading, and QtWebEngine
    6.11.2 segfaulted on every startup — three runs, three crashes. The bind
    has to wait for the page, so it is registered as a post-load hook."""
    import threading
    parent = Parent()
    parent._wv_loaded = threading.Event()        # created, not yet loaded
    cm = ContextMenu(parent)
    assert '<<ContextMenu>>' not in parent.bound, \
        "binding before the page loads is what crashed QtWebEngine"
    assert cm.updatebindings in parent.__dict__.get('_on_loaded_hooks', []), \
        "the bind must be deferred, not dropped"


def test_the_deferred_hook_really_binds_when_run():
    """Deferring must not mean losing it — the menu still has to work."""
    import threading
    parent = Parent()
    parent._wv_loaded = threading.Event()
    ContextMenu(parent)
    for hook in parent.__dict__['_on_loaded_hooks']:
        hook()
    assert '<<ContextMenu>>' in parent.bound


def test_it_binds_immediately_on_an_ALREADY_loaded_page():
    """A window whose page is up needs no deferral, and waiting for a load
    that already happened would never bind at all."""
    import threading
    parent = Parent()
    parent._wv_loaded = threading.Event()
    parent._wv_loaded.set()
    ContextMenu(parent)
    assert '<<ContextMenu>>' in parent.bound


def test_menuitem_creates_the_menu_and_keeps_the_entry():
    parent = Parent()
    cm = ContextMenu(parent)
    cm.menuitem('Sound settings', lambda: None)
    assert cm.menu is not None
    assert [label.strip() for _k, label, _c in cm.menu._items] \
            == ['Sound settings']


def test_menuitem_twice_keeps_both():
    parent = Parent()
    cm = ContextMenu(parent)
    cm.menuitem('Sound settings', lambda: None)
    cm.menuitem('Transcription settings', lambda: None)
    assert len(cm.menu._items) == 2


def test_menuinit_starts_a_FRESH_menu():
    """`ui_shell` calls `menuinit()` when the context changes; appending to the
    old menu would accumulate entries across pages."""
    parent = Parent()
    cm = ContextMenu(parent)
    cm.menuitem('Sound settings', lambda: None)
    cm.menuinit()
    assert cm.menu._items == []


def test_popup_asks_the_parent_for_its_entries_when_there_are_none():
    """The window's own `setcontext()` walks the task mixins and is what knows
    which entries belong on this page, so a first right-click has to run it."""
    parent = Parent(setcontext=lambda p: p.context.menuitem('Sound settings',
                                                            lambda: None))
    cm = ContextMenu(parent)
    cm.do_popup(types.SimpleNamespace(x=10, y=20))
    assert parent.setcontext_calls == 1
    assert cm.popup is True


def test_popup_uses_PAGE_coordinates():
    """`tk_popup` positions an absolutely-placed div, and the event this
    backend delivers carries clientX/clientY as `x`/`y` — there is no
    `x_root`, so reading one would have raised inside `on_event` and presented
    as a right-click that did nothing."""
    parent = Parent(setcontext=lambda p: p.context.menuitem('x', lambda: None))
    cm = ContextMenu(parent)
    seen = {}
    cm.menuinit()
    cm.menuitem('x', lambda: None)
    cm.menu.tk_popup = lambda x, y: seen.update(x=x, y=y)
    cm.do_popup(types.SimpleNamespace(x=37, y=91))
    assert seen == {'x': 37, 'y': 91}


def test_popup_with_no_entries_does_not_claim_to_have_shown_one():
    """A window whose setcontext adds nothing should not leave `popup` True —
    that would make `undo_popup` try to dismiss a menu that never appeared."""
    parent = Parent()               # setcontext adds no items
    cm = ContextMenu(parent)
    cm.do_popup(types.SimpleNamespace(x=0, y=0))
    assert cm.popup is False


def test_popup_survives_a_parent_whose_setcontext_raises():
    """A right-click must not take the window down with it."""
    def boom(p):
        raise RuntimeError('no context for you')
    parent = Parent(setcontext=boom)
    cm = ContextMenu(parent)
    cm.do_popup(types.SimpleNamespace(x=1, y=1))   # must not raise
    assert cm.popup is False


def test_undo_popup_is_quiet_when_nothing_is_shown():
    parent = Parent()
    cm = ContextMenu(parent)
    cm.undo_popup()                 # must not raise
    assert cm.popup is False


def test_a_missing_backend_member_is_named_a_PORT_GAP():
    """`on_event` swallows handler exceptions so one bad callback cannot take
    the event loop down — and that is how ten port gaps hid, each presenting
    as "nothing happened" with a traceback lost in the event noise.

    An AttributeError on one of OUR widgets means the app asked this backend
    for something tkinter provides. That is a different thing from a bug in
    the handler, and it should be impossible to miss."""
    # An APP SUBCLASS, which is what the app actually hands to handlers —
    # `SortButtonFrame(ui.ScrollingFrame)`, `Splash(ui.Window)`. Its type
    # lives in the app's module, not in ui_webview, so a check on
    # `type(obj).__module__` misses it; the MRO is what settles it. That was
    # the production bug this test found on its first run.
    class Fake(ui_webview.Label):
        def __init__(self):
            pass                    # no widget, no page, no JS

    err = None
    try:
        Fake().no_such_method()
    except AttributeError as e:
        err = e
    assert err is not None
    assert ui_webview._looks_like_port_gap(err), \
        'a missing member of a ui_webview widget subclass is a port gap'


def test_an_ordinary_AttributeError_is_NOT_called_a_port_gap():
    """The marker is worth nothing if it fires on everything. A missing
    attribute on a task, a settings object or a LIFT entry is an ordinary
    bug."""
    class NotAWidget:
        pass

    err = None
    try:
        NotAWidget().missing
    except AttributeError as e:
        err = e
    assert err is not None
    assert not ui_webview._looks_like_port_gap(err)


def test_wait_does_not_hide_the_page_it_is_waiting_on():
    """Kent, 2026-09-11: "the page opens (almost?) complete, then goes away to
    build the wait dialog, which returns almost immediately."

    Withdrawing the caller is right under tkinter — it puts a slow render
    behind "Loading…" instead of a blank screen — and wrong here, where the
    page is already rendered and hiding it removes a finished window for a
    moment. Read from source, since exercising it needs a live wait window."""
    import inspect
    src = inspect.getsource(ui_webview)
    body = src.split('def wait(self, msg=None, cancellable=False')
    # TWO copies, deliberately (Toplevel and Root mirror each other rather
    # than sharing an MRO — see the note above `_waitwindow`). The first fix
    # reached only one of them, because they had drifted to `bool(x) or
    # bool(y)` and `x | y` for the same intent and a search-and-replace
    # matched one. Assert the COUNT so a third copy, or a renamed one, fails
    # here rather than being silently unfixed.
    assert len(body) == 3, \
        'expected exactly two wait() definitions, found {}'.format(
            len(body) - 1)
    for chunk in body[1:]:
        chunk = chunk.split('def waitdone')[0]
        assert 'self.withdraw()' not in chunk, \
            'wait() must not hide the window it is waiting on'
        # AND IT MUST SHOW IMMEDIATELY. A 400ms `after()` delay was tried and
        # reverted: this app's slow work is synchronous, so the event loop
        # does not run and a scheduled dialog appears only once the work is
        # over — absent during exactly the operations it exists for (35s of
        # blank screen, Kent 2026-09-14).
        assert '_waittimer' not in chunk, \
            'wait() must not defer the dialog: a timer cannot fire during ' \
            'synchronous work'


def test_windows_are_NOT_created_hidden():
    """A window created hidden never loads its page on Qt, so its JS queue
    never flushes and it comes up BLANK — with every widget the Python side
    built sitting in a queue nobody reads. Kent's Sound Card Settings window,
    2026-09-11: three log lines (created HIDDEN / show requested / show now)
    and then nothing, where every "created visible" window in the same run
    fetched base.html, widgets.js and flushed its queue.

    The earlier probe measured whether `show()` could MAP such a window, which
    is not the capability that matters."""
    assert ui_webview._supports_created_hidden() is False, \
        "created-hidden windows do not load their page; this must stay off"


def test_press_and_release_map_to_press_and_release():
    """A press-and-hold control cannot work otherwise, and the record button
    is one: press starts, release stops (`sound_ui.py:70-71`).

    `<ButtonPress-1>` was absent from the map, so it registered a listener for
    an event nothing fires and recording never STARTED — then release raised
    on state that `start()` creates. And `<Button-1>` mapped to 'click', which
    fires AFTER mouseup, so the two synonyms ran in the wrong order relative
    to each other. In tkinter both names mean press."""
    js = (Path(__file__).resolve().parents[1]
          / 'frontend' / 'webview_html' / 'widgets.js').read_text()
    for name in ("'<Button-1>': 'mousedown'",
                 "'<ButtonPress-1>': 'mousedown'",
                 "'<ButtonRelease-1>': 'mouseup'"):
        assert name in js, "press/release mapping wrong or missing: " + name


def test_the_recorder_reports_nothing_recorded_rather_than_raising():
    """`file_write_OK` must exist before `start()` runs: the UI reads it after
    a take, and a stop-without-a-start used to raise an AttributeError that
    pointed at the recorder instead of at the dead binding upstream."""
    sound = pytest.importorskip('io_put.sound',
                                reason='needs the audio module importable')
    rec = sound.SoundFileRecorder.__new__(sound.SoundFileRecorder)
    sound.SoundFileRecorder.__init__(rec, 'x.wav', None, None)
    assert rec.file_write_OK is False


def test_wraplength_is_clamped_to_the_viewport_in_the_page_script():
    """An inline style beats the stylesheet, so setting maxWidth from
    `wraplength` silently defeated grid.css's cap — the one that stops a label
    demanding more width than the window has. The Sound Settings caveat ran
    off the right edge of its window on exactly that path (GTK, 2026-09-11).
    CSS min() keeps both constraints.

    THE SECOND TERM IS A VARIABLE NOW (2026-09-15), not `92vw` written out.
    It still RESOLVES to 92vw while the page is being read; what changed is
    that it resolves against the SCREEN for the duration of a fit, because a
    cap measured against the window made the measured content size depend on
    the window size the fit was computing — so the fit ratcheted the window
    wider on every measurement instead of converging
    (agenda/webview_window_sizing.md). So this checks the guarantee — the
    caller's number is bounded by a cap — rather than the literal that used
    to express it."""
    js = (Path(__file__).resolve().parents[1]
          / 'frontend' / 'webview_html' / 'widgets.js').read_text()
    assert "'min(' + value + 'px, var(--demandcap, 92vw))'" in js, \
        "an inline wraplength must not be allowed to exceed the display cap"


def test_the_display_caps_are_screen_relative_while_measuring():
    """The other half of the same guarantee, in the stylesheet: each cap is
    viewport-relative by default and redefined against `--screenw`/`--screenh`
    under `html.wv-measuring`. A cap that tracks the window cannot bound a
    window that is being sized to fit it."""
    css = (Path(__file__).resolve().parents[1]
           / 'frontend' / 'webview_html' / 'grid.css').read_text()
    assert 'html.wv-measuring {' in css, \
        'the measuring state must redefine the caps'
    for cap in ('--demandcap', '--imgcapw', '--imgcaph', '--scrollcap'):
        assert cap in css, '{} is not defined'.format(cap)
        assert '--screen' in css.split('html.wv-measuring {', 1)[1], \
            'the measuring caps must be relative to the screen, not the window'


def test_the_virtual_event_is_mapped_in_the_page_script():
    """`<<ContextMenu>>` is the name ui_tkinter binds, so the JS has to map it
    to a real DOM event. Unmapped names fall through to
    `addEventListener('<<ContextMenu>>')`, which nothing ever fires — the same
    silent death Button-3 had until 2026-09-09."""
    js = (Path(__file__).resolve().parents[1]
          / 'frontend' / 'webview_html' / 'widgets.js').read_text()
    assert "'<<ContextMenu>>': 'contextmenu'" in js, \
        "the virtual context-menu event must map to a DOM event"
