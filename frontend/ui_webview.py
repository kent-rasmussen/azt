# coding=UTF-8
"""pywebview UI backend — drop-in replacement for ui_tkinter.

Usage:  from frontend import ui_webview as ui
Then:   ui.Root, ui.Window, ui.Frame, ui.Label, ui.Button, etc.

Phase 2: Root, Window, Frame, Label, Button, ExitFlag, Progressbar, Menu,
         constants, variables.
Phase 3: Theme (reads same theme dicts as tkinter), Image (PIL + base64),
         Renderer (PIL text → base64).
Remaining widgets are stubs that log and no-op until Phase 4.
"""
import base64
import importlib.util
import io
import json
import os
import platform
import sys
import threading
import time
import unicodedata
from contextlib import contextmanager
from random import randint

from utilities import logsetup
from utilities.i18n import _

log = logsetup.getlog(__name__)
logsetup.setlevel('INFO', log)

try:
    import webview
except ImportError:
    webview = None
    log.error("pywebview not installed — install with: pip install pywebview")

try:
    import PIL.Image
    import PIL.ImageFont
    import PIL.ImageDraw
    pilisactive = True
except ImportError:
    pilisactive = False

# Re-export standalone variables (no tkinter dependency)
from frontend.ui_variables import Variable, StringVar, IntVar, BooleanVar
from frontend import theme_data  # themes + imagelist, shared with ui_tkinter

# ── Constants (same names as ui_tkinter) ───────────────────────────────
END = 'end'
INSERT = 'insert'
N = 'n'
S = 's'
E = 'e'
W = 'w'
RIGHT = 'right'
LEFT = 'left'
SINGLE = 'single'
EXTENDED = 'extended'
MULTIPLE = 'multiple'

# ── Helpers ────────────────────────────────────────────────────────────
_HTML_DIR = os.path.join(os.path.dirname(__file__), 'webview_html')

def nfc(x):
    return unicodedata.normalize('NFC', str(x))

def nfd(x):
    return unicodedata.normalize('NFD', str(x))

def _donothing(*a, **kw):
    pass

# ── Widget ID allocator ───────────────────────────────────────────────
_wid_lock = threading.Lock()
_wid_counter = 0

def _next_wid():
    global _wid_counter
    with _wid_lock:
        _wid_counter += 1
        return _wid_counter

# ── ExitFlag ──────────────────────────────────────────────────────────
class ExitFlag:
    def __init__(self):
        self.value = False
    def istrue(self):
        return self.value
    get = istrue
    def true(self):
        self.value = True
    def false(self):
        self.value = False

# ── pywebview API class (receives JS events) ─────────────────────────
def _looks_like_port_gap(err):
    """Is this AttributeError the app asking US for something we lack?

    `AttributeError` carries `obj` and `name` since 3.10, so this asks the
    object rather than parsing the message: if the thing that lacked the
    attribute is one of this module's widgets, the app asked the BACKEND for
    something it does not implement. A missing attribute on a task, a
    settings object or a LIFT entry is an ordinary bug and is reported as
    one.

    Falls back to the message text where the attributes are absent, and to
    "not a port gap" when it cannot tell — an over-eager PORT GAP label on
    ordinary errors would make the marker worthless, which is the one thing
    it cannot afford.
    """
    # THE WHOLE MRO, not `type(obj)`. Almost every widget the app touches is
    # an APP subclass — `SortButtonFrame(ui.ScrollingFrame)`,
    # `Splash(ui.Window)`, `SoundSettingsWindow(ui.Window)` — so its type
    # belongs to `frontend.sort_buttons` or `tasks.tasks`, not here. Asking
    # only about `type(obj)` classified nearly every real port gap as an
    # ordinary error, which is the exact opposite of this function's job.
    # Caught by its own test on the first run (2026-09-11).
    obj = getattr(err, 'obj', None)
    if obj is not None:
        return any(base.__module__ == __name__
                   for base in type(obj).__mro__)
    text = str(err)
    return ("'" in text
            and any(k in text for k in ('Window', 'Toplevel', 'Frame',
                                        'Label', 'Button', 'Entry', 'Menu',
                                        'ScrollingFrame', 'ListBox', 'Image',
                                        'Theme', 'Notebook', 'ToolTip')))


class _JsonApi:
    """Exposed to JS as window.pywebview.api."""
    def __init__(self):
        self._handlers = {}  # wid → {event_name: [callbacks]}

    def register(self, wid, event_name, callback):
        self._handlers.setdefault(wid, {}).setdefault(event_name, []).append(callback)

    def unregister(self, wid, event_name=None):
        if event_name:
            self._handlers.get(wid, {}).pop(event_name, None)
        else:
            self._handlers.pop(wid, None)

    def on_event(self, wid, event_name, event_data):
        """Called from JS when the user interacts with a widget.

        SWALLOWING IS DELIBERATE — a handler that raises must not take the
        event loop down with it — and it is also how ten port gaps hid. A
        call this backend does not answer raises AttributeError HERE, gets
        printed among the event noise, and the user sees only that nothing
        happened: no window, a dead button, a page with no picture.

        So the two are told apart. An AttributeError naming a member of one
        of OUR widgets is a PORT GAP: the app asked this backend for
        something tkinter provides, and the answer is to implement it, not to
        debug the handler. Anything else is an ordinary error inside working
        code. Logged at ERROR with a marker, because it is the one class of
        failure that should be impossible to miss in a log — and because
        every one of the ten so far was found by a user rather than by
        reading this output.
        """
        for cb in self._handlers.get(wid, {}).get(event_name, []):
            try:
                cb(event_data)
            except AttributeError as e:
                import traceback
                if _looks_like_port_gap(e):
                    log.error("PORT GAP: %s — the app called something this "
                              "backend does not implement, from a %r event on "
                              "widget %s. Implement it in ui_webview; the "
                              "handler is not at fault.", e, event_name, wid)
                else:
                    log.error("error in a %r handler on widget %s: %s",
                              event_name, wid, e)
                traceback.print_exc()
            except Exception as e:
                import traceback
                log.error("error in a %r handler on widget %s: %s",
                          event_name, wid, e)
                traceback.print_exc()

# Singleton API instance — shared across all widgets in a window
_api = _JsonApi()

def _request_refit(window, trigger, delay=0.4):
    """Ask a window to fit its content SOON, once, however often we ask.

    THE FIT WAS NEVER WRONG; IT WAS UNREACHABLE (Kent, 2026-09-11: "it's
    correct in other places… but there is no double click on an OS maximized
    screen, nor a screen that's simply too small or large for its content").
    `fit_to_content` ran at page load and on release-from-fullscreen, and
    nowhere else — so a window whose content was built AFTER the page loaded,
    which is most of them, was measured while empty and never measured again.
    That is the clipped chooser and the screen-filling USB prompt both:
    windows that never asked. See agenda/webview_window_sizing.md.

    COALESCED, because the obvious fix is worse than the bug: asking after
    every widget would resize the window a few hundred times during a build.
    Each request bumps a serial; the timer, when it fires, refits only if
    nothing arrived since it last looked, and otherwise waits another round.
    A burst of widgets therefore produces exactly one fit, shortly after the
    burst ends, and a page that keeps building keeps deferring it.

    It also guards the shrink-on-re-measure thread in that item (1028x749 →
    991x728): fewer, later fits means fewer chances to measure content that
    has already been squeezed by the previous one.
    """
    if window is None or not getattr(window, '_exists', True):
        return
    if not hasattr(window, 'fit_to_content'):
        return
    window._refit_serial = getattr(window, '_refit_serial', 0) + 1
    if getattr(window, '_refit_timer', None) is not None:
        return                      # one is already on its way
    # THE SERIAL AS IT IS NOW, so a burst that has already ENDED fits on the
    # first pass. Comparing against an unset value instead made every fit
    # re-arm once before doing anything, which cost a whole delay on every
    # window for nothing — Kent, 2026-09-15: "it gets there with tolerable
    # delay". The wait is only worth paying when content is still arriving.
    window._refit_seen = window._refit_serial

    def run(tries=0):
        window._refit_timer = None
        serial = getattr(window, '_refit_serial', 0)
        if serial != getattr(window, '_refit_seen', None) and tries < 6:
            # Something arrived while we waited; look again rather than
            # measuring a page that is still being built.
            window._refit_seen = serial
            window._refit_timer = window.after(int(delay * 1000),
                                               lambda: run(tries + 1))
            return
        log.info("window {}: fit requested by {}".format(
                    getattr(window, '_wid', 'root'), trigger))
        # BEFORE the fit, and not inside it: `fit_to_content` returns at its
        # first guard for a fullscreen window, and the page this check
        # exists for — the macrosort run window — is always fullscreen. A
        # diagnostic that cannot run where the fault happens is no
        # diagnostic (Kent, 2026-09-15: leave it in and catch it next time).
        try:
            checker = getattr(window, '_check_displaced', None)
            if checker:
                checker()
        except Exception as e:
            log.debug("displacement check skipped: {!r}".format(e))
        # SAME PLACE, SAME REASON. The double-scroll page is the macrosort
        # run window, which is fullscreen, so anything inside the fit is
        # unreachable there. See `_report_height_chain`.
        if _switch('--log-heights'):
            try:
                _js(getattr(window, '_wv_window', None),
                    'reportHeightChain({})'.format(
                        getattr(window, '_wid', 0)))
            except Exception as e:
                log.info("could not ask for the height chain ({!r})".format(e))
        try:
            window.fit_to_content()
        except Exception as e:
            log.info("window {}: refit failed ({!r})".format(
                        getattr(window, '_wid', 'root'), e))

    try:
        window._refit_timer = window.after(int(delay * 1000), run)
    except Exception as e:
        log.info("could not schedule a refit ({!r})".format(e))


# The droppable a drag most recently landed on, so the SOURCE's dnd_end can
# be told what it hit. The page's `dragend` does not carry a target, and
# `drop` fires first — see _WebviewWidget._on_dnd_end. One drag at a time.
_dnd_last_target = None

# ── Engine selection ─────────────────────────────────────────────────
# Which native host renders the page. Kent, 2026-09-04: Qt gives this machine
# engine parity with the Windows field (QtWebEngine IS Chromium), but "for
# anyone running Ubuntu (including myself) it would look oddly different than
# everything else on the desktop" — the page is our own HTML either way; what
# differs is the NATIVE CHROME (window decorations, native dialogs, menus).
#
# It matters more than cosmetics on Linux, though: the first --webview run
# segfaulted under Qt on this box while GTK was solid, so being able to say
# which engine is a diagnostic, not a preference.
#
# pywebview reads PYWEBVIEW_GUI itself and nothing here used to override it,
# so that already worked by accident. AZT_WEBVIEW_ENGINE and --engine= are
# ours, and take precedence.
ENGINES = ('gtk', 'qt', 'cef', 'edgechromium', 'mshtml')


def _switch(name):
    """Is a command-line switch present?

    SWITCHES, NOT ENVIRONMENT VARIABLES (Kent, standing rule 2026-09-08).
    Everything this module can be told to do differently is told on the
    command line: a switch is visible in the process list, appears in the
    "Called with arguments" log line at startup, can be typed into the dev
    console's switches box, and does not persist invisibly into the next run
    the way an exported variable does."""
    return name in sys.argv


def _switch_value(name):
    """The value of a `--name=value` switch, or None. Matches how
    `--engine=` is read in utilities.ui_backend.requested_engine."""
    prefix = name + '='
    for arg in sys.argv:
        if arg.startswith(prefix):
            return arg[len(prefix):].strip() or None
    return None


# Whether this display stack lets us place our own windows. None = not
# settled yet; see `_can_position`.
_positioning = None

# WHERE NON-KIOSK WINDOWS GO: one place for the whole session, not one
# computed per window. Seeded by wherever the first window lands (the window
# manager's choice) and replaced by the user's whenever they move one. See
# `_place_window` for why this replaced centring, and `_learn_origin` for
# how it is learned. None until something has been observed.
_window_origin = None


def _focus_kwarg():
    """`focus=False` for `create_window`, under `--no-window-focus`.

    AN EXPERIMENT, and worth being precise about what it can and cannot do.
    `focus` decides whether a window takes focus WHEN IT IS CREATED. It does
    not change how a window behaves on later focus changes, so it cannot fix
    the size revert (a compositor re-configures a toplevel on any state
    change and GTK answers from the created size; see `_reassert`).

    What it CAN remove is one TRIGGER. A new window stealing focus makes the
    previous one lose it — Kent's first revert landed 285ms after the wait
    dialog appeared — so a dialog that does not grab focus does not cause
    that one. Clicking on the desktop still will.

    So this is here to separate the two cases in a run, not as a fix: if the
    dialog-appearing reverts stop while the click-away reverts continue, the
    trigger is confirmed and the mechanism is untouched.

    Off by default, because a window created without focus is a window the
    user may have to click before it will take a keystroke, and this app's
    wait dialog has a Cancel button on it."""
    if not _switch('--no-window-focus'):
        return {}
    # ASK BEFORE PASSING IT. `focus` arrived in pywebview 4.x, and an
    # unrecognised kwarg is a TypeError from `create_window` — i.e. no
    # window at all, for every window, from a switch meant to test one
    # thing. A switch that can take the UI down is worse than a switch that
    # says it cannot help.
    try:
        import inspect
        if 'focus' not in inspect.signature(
                                webview.create_window).parameters:
            log.info("--no-window-focus ignored: this pywebview's "
                     "create_window has no `focus` parameter")
            return {}
    except Exception as e:
        log.info("--no-window-focus ignored: could not check whether "
                 "create_window accepts it ({!r})".format(e))
        return {}
    log.info("--no-window-focus: windows are created WITHOUT focus. This "
             "cannot stop a window losing its size on a focus change — it "
             "removes one CAUSE of focus changing, namely a new window "
             "taking it. See _focus_kwarg.")
    return {'focus': False}


def _kiosk_kwarg(kiosk):
    """`fullscreen=True` for `create_window`, when a window is born kiosk.

    WHY AT CREATION RATHER THAN AFTER. A run window was created at 800x600
    and then fullscreened by `takekioskscreen()`, so the user watched it
    become correct: Kent's 20fps filmstrip of one page load (2026-09-16)
    shows a decorated 800x600 window, four resizes, and only then the
    fullscreen page — tiles 3 to 17, about 1.4 seconds of it. A window
    created at the size it is going to be has nothing to change.

    It also removes work rather than hiding it. `fit_to_content` measures
    and returns for a fullscreen window, so a kiosk window born fullscreen
    never asks to be resized at all; and `takekioskscreen()` then finds the
    state already correct and sends no toggle.

    THIS IS NOT THE SAME AS "HIDDEN UNTIL READY", which is what Kent asked
    for repeatedly and which I answered with a flat no. The no was right
    about one mechanism — a window created hidden on WebKitGTK never maps
    when shown (`--webview-hidden`), and the off-screen-birth workaround
    cannot be undone on Wayland because a client may not move its own
    windows (`_can_position`) — and wrong as an answer to the request. This
    covers the resizing half of it; a page-level cover over the build covers
    the rest.

    Asked for rather than assumed, like `_focus_kwarg`: an unrecognised
    kwarg is a TypeError from `create_window`, i.e. no window at all.
    `--no-kiosk` is honoured here too, or the switch would stop working for
    exactly the windows it exists to debug."""
    if not kiosk:
        return {}
    if _switch('--no-kiosk'):
        _say_once("--no-kiosk: windows that would be born fullscreen are "
                  "born windowed instead")
        return {}
    try:
        import inspect
        if 'fullscreen' not in inspect.signature(
                                webview.create_window).parameters:
            _say_once("this pywebview's create_window has no `fullscreen` "
                      "parameter; kiosk windows are fullscreened after "
                      "creation instead, which the user sees happen")
            return {}
    except Exception as e:
        _say_once("could not check whether create_window accepts "
                  "`fullscreen` ({!r}); fullscreening after creation "
                  "instead".format(e))
        return {}
    return {'fullscreen': True}


def _created_size():
    """The size new task windows are created at: 800x600, or `--window-size`.

    A SWITCH BECAUSE THE TWO HYPOTHESES PREDICT THE SAME LOG. A window that
    loses its size on a focus change comes back at 800x600 — and every
    window in this app is CREATED at 800x600, so "it reverts to its created
    size" and "it is clamped to a fixed 800x600" cannot be told apart by
    that number (Kent, 2026-09-16, on a source claiming a backend clamp).
    Create them at something else for one run and they separate:

      * comes back at the NEW size  -> it reverts to what it was created at,
        and the answer is to change what the window's default size IS
        (`_pin_default_size`, which did not hold) or to refuse the shrink
        (`_pin_min_size`);
      * still comes back at 800x600 -> something below us has that number
        of its own, and none of the above can help.

    `--window-size=640x480`. Bad values are ignored with a line, because a
    diagnostic switch must not be able to produce an unusable window.

    SAID ONCE, not once per call. This is read at every window creation
    (twice: width and height) and again in every drop report, and each read
    logged — so the one run that mattered carried the same two sentences
    thirty times through the evidence it was there to produce."""
    asked = _switch_value('--window-size')
    if not asked:
        return 800, 600
    try:
        w, h = (int(n) for n in asked.lower().replace('*', 'x').split('x', 1))
        if w < 200 or h < 150:
            raise ValueError('too small to hold a window')
    except Exception as e:
        _say_once('--window-size={!r} ignored ({!r}); using 800x600'
                  ''.format(asked, e))
        return 800, 600
    _say_once("windows created at {}x{} (--window-size), not the usual "
              "800x600 — see _created_size for what this is for".format(w, h))
    return w, h


_said = set()


def _say_once(line):
    """Log `line` the first time it is asked for, and never again.

    For facts about the RUN rather than about an event: a switch's value, a
    capability that is missing. Keyed on the text, so a line whose numbers
    change still says the new numbers."""
    if line in _said:
        return
    _said.add(line)
    log.info(line)


def _native_window(wv):
    """The toolkit's own window object behind a pywebview window, or None.

    REACHING PAST THE WRAPPER, and only for something the wrapper cannot do.
    `resize()` is a ONE-SHOT request: on Wayland the compositor re-configures
    a toplevel on almost any state change — focus in, focus out, a click on
    the title bar — and the client must answer with a size. Once our resize
    has been consumed GTK answers from the window's DEFAULT size, which is
    the 800x600 `create_window` was given. So the window snapped back on
    every click, and putting the size back each time turns a crop into a
    flicker (Kent, 2026-09-15: "almost anywhere you click, 6x800 and back").
    The default size is the thing being answered with, and pywebview exposes
    no way to set it.

    Written defensively on purpose: this is pywebview's private structure and
    may move between versions. Every failure is a None and a log line, never
    an exception — the caller's fallback is the behaviour we already have.

    QT AS WELL AS GTK. This looked only in the GTK module, with a comment
    saying the other backends do not have this problem — and Kent's Qt run
    then reverted exactly the same way while both pins reported "no native
    window reachable" and did nothing (2026-09-16). The revert is the
    compositor's, so it is a WAYLAND behaviour, and both toolkits are on
    Wayland here. The method names differ, not the need; see `_pin_min_size`.
    """
    # NOT AN IMPORT OF Gtk/Gdk OR QtWidgets — see the warning in
    # utilities/display.py: a fresh unversioned import of GDK inside a
    # running Qt process took the gi type system apart. These only ask for
    # modules that are ALREADY LOADED, i.e. the toolkit actually in use.
    for name in ('webview.platforms.gtk', 'webview.platforms.qt'):
        plat = sys.modules.get(name)
        if plat is None:
            continue
        try:
            view = getattr(plat, 'BrowserView', None)
            instances = getattr(view, 'instances', None) or {}
            bv = instances.get(getattr(wv, 'uid', None))
            if bv is None:
                continue
            # GTK's BrowserView holds a Gtk.Window as `window`; Qt's
            # BrowserView IS the QMainWindow. Older layouts have used
            # `_window`. None of it is contractual.
            got = (getattr(bv, 'window', None)
                   or getattr(bv, '_window', None)
                   or bv)
            if got is not None:
                return got
        except Exception as e:
            log.debug("could not reach the native window via {} ({!r})"
                      "".format(name, e))
    return None


_said_no_marshal = False


def _run_on_gui_thread(fn):
    """Run `fn` on the toolkit's own thread, if we can tell which that is.

    GTK IS NOT THREAD-SAFE and our resizes come from a page-building worker,
    so touching a Gtk.Window directly from here is a crash waiting to
    happen. `GLib.idle_add` is the marshalling GTK itself provides. If GLib
    is not loaded we are not on GTK and there is nothing to marshal to."""
    glib = sys.modules.get('gi.repository.GLib')
    if glib is None:
        # SAY SO, ONCE. Falling through to a direct call means we are
        # touching the toolkit from whatever thread we are on — which is the
        # thing this function exists to avoid, and which this used to do
        # silently. If a window's size or minimum is not behaving, whether
        # the call was marshalled is the first thing worth knowing.
        global _said_no_marshal
        if not _said_no_marshal:
            _said_no_marshal = True
            log.info("GUI-thread marshalling unavailable (GLib not loaded); "
                     "toolkit calls run on the calling thread. On Qt that is "
                     "expected; on GTK it means gi was imported differently "
                     "than assumed and is worth knowing.")
        fn()
        return
    try:
        glib.idle_add(lambda: (fn(), False)[1])
    except Exception as e:
        log.info("could not defer to the GUI thread ({!r}); running the "
                 "toolkit call inline".format(e))
        fn()


def _geometry_of(win):
    """A native window's OUTER frame and INNER client box, or None.

    THE PAGE CANNOT SEE THE FRAME, and the frame is what Kent watches move.
    `window.innerWidth/Height` is the client area only, so every reading of
    the size loss so far has been made from half the evidence: a client box
    that shrank by 52x89 is equally consistent with "the frame stayed put and
    the decorations grew into it" and with "the whole frame shrank" — and
    those have opposite fixes. Kent, 2026-09-16, settling it by eye: "I'm
    seeing the window frame resize/move, not content change." This is how the
    log can see the same thing.

    Both numbers at one instant, from the toolkit, so their DIFFERENCE is the
    decoration inset measured rather than inferred.

    Returns a dict with any of 'frame', 'inner' (each `(x, y, w, h)`) and
    'error'. Every failure is a value, never an exception: this is a
    diagnostic and must not be able to break a resize report."""
    if win is None:
        return None
    out = {}
    try:
        if callable(getattr(win, 'frameGeometry', None)):
            # Qt: the BrowserView IS the QMainWindow. `geometry()` is the
            # client area in screen coordinates; `frameGeometry()` includes
            # the decorations.
            fg, ig = win.frameGeometry(), win.geometry()
            out['frame'] = (fg.x(), fg.y(), fg.width(), fg.height())
            out['inner'] = (ig.x(), ig.y(), ig.width(), ig.height())
        elif callable(getattr(win, 'get_size', None)):
            # GTK 3: `get_size()` is the window's own (client) size and
            # `get_position()` its origin; the GdkWindow's frame extents are
            # the whole thing including whatever the decorations occupy.
            w, h = win.get_size()
            x, y = win.get_position()
            out['inner'] = (x, y, w, h)
            gdkwin = win.get_window() if callable(
                        getattr(win, 'get_window', None)) else None
            if gdkwin is not None:
                # NOT `get_frame_extents()`, WHICH CORRUPTED MEMORY.
                # `gdk_window_get_frame_extents(window, GdkRectangle *rect)`
                # takes its rectangle as a CALLER-ALLOCATED out-parameter,
                # and calling it through PyGObject here left the process
                # damaged: a later `kill -USR1` segfaulted instead of
                # dumping, at boot and on the sort page and with every
                # thread parked — three states with nothing in common, which
                # is the signature of corruption rather than of anything the
                # app was doing. `--no-frame-inset` (which returns before
                # this function is reached) made it stop; Kent, 2026-09-16:
                # "--no-frame-inset resolves this".
                #   The GdkWindow's own width/height is the same number with
                # no out-parameter: on a CSD toplevel the GdkWindow includes
                # the decorations, while `gtk_window_get_size` above excludes
                # them, so the difference is still the inset.
                #   What is given up is the frame's ORIGIN, and it was worth
                # nothing: Wayland reports no global position, and every
                # sample in the trace read `frame … at 0,0` regardless.
                out['frame'] = (x, y, gdkwin.get_width(), gdkwin.get_height())
        else:
            out['error'] = 'native window {} has neither Qt nor GTK ' \
                           'geometry'.format(type(win).__name__)
    except Exception as e:
        out['error'] = repr(e)
    return out or None


def _format_geometry(geo):
    """`_geometry_of`'s dict as one readable clause, inset included."""
    if not geo:
        return 'native geometry not reachable'
    bits = []
    for key, name in (('frame', 'frame'), ('inner', 'client')):
        if key in geo:
            x, y, w, h = geo[key]
            bits.append('{} {}x{} at {},{}'.format(name, w, h, x, y))
    if 'frame' in geo and 'inner' in geo:
        bits.append('decoration {}x{}'.format(
                        geo['frame'][2] - geo['inner'][2],
                        geo['frame'][3] - geo['inner'][3]))
    if geo.get('error'):
        bits.append('unreadable ({})'.format(geo['error']))
    return ', '.join(bits)


def _inset_of(win):
    """How much bigger a window's FRAME is than its client area, or (0, 0).

    THE UNITS BUG THIS EXISTS FOR (measured 2026-09-16, `--log-resizes`).
    `resize()` is in CLIENT units and lands correctly. The two things that
    make a size survive a configure — the window's default size and its
    minimum via geometry hints — are in FRAME units under client-side
    decorations, and were being given the client number. So the window fell
    to exactly the size we had pinned, as a frame, and the client came out
    one decoration short:

        fit asked 1331x773 -> frame 1383x862, client 1331x773   (resize)
        after a focus change -> frame 1331x773, client 1279x684  (the pin)

    1331-1279 = 52 and 773-684 = 89, which is this stack's decoration, at
    every window and both created sizes. Nothing took the size away: the
    minimum was honoured EXACTLY, in units nobody had checked. The
    "compositor took the size" reading in the log lines and in
    agenda/webview_window_sizing.md was ours all along, and
    `_pin_min_size`'s own docstring had the arithmetic in it ("a window with
    a 998x770 minimum was configured to 946x681") without the subtraction
    being done.

    So: pin `want + inset` and the client lands on `want`.

    Read from the toolkit rather than assumed, because a decoration size is
    a theme's business and 52x89 is one stack's answer. `(0, 0)` whenever it
    cannot be read, which is the behaviour we already have.

    MUST BE CALLED ON THE GUI THREAD — its callers do it inside the lambda
    they marshal, so the read and the write happen together and the value
    cannot go stale between them.

    `--no-frame-inset` pins in client units again, for measuring against."""
    if _switch('--no-frame-inset'):
        return 0, 0
    geo = _geometry_of(win)
    if not geo or 'frame' not in geo or 'inner' not in geo:
        return 0, 0
    dw = geo['frame'][2] - geo['inner'][2]
    dh = geo['frame'][3] - geo['inner'][3]
    # A DECORATION IS TENS OF PIXELS. A window that is not mapped yet, or a
    # frame reading that means something else, must not be allowed to add
    # hundreds of pixels to every window in the app — a nonsense reading
    # becomes no adjustment, not a nonsense window.
    if not (0 <= dw <= 200 and 0 <= dh <= 200):
        _say_once("frame inset reads {}x{}, which is not a decoration size; "
                  "pinning window sizes in client units instead"
                  "".format(dw, dh))
        return 0, 0
    return dw, dh


def _can_position():
    """May we move our own windows? See utilities.display.positioning_available
    for what rides on the answer — on native Wayland a `move()` takes the
    window's size with it.

    Cached, because the stack cannot change mid-run — but NOT cached before
    a toolkit has a display, because until then the honest answer is "don't
    know" and caching that would make every later window unplaceable on a
    stack that allows it."""
    global _positioning
    if _positioning is not None:
        return _positioning
    try:
        from utilities import display
        said = display.toolkit(_engine())
        if not said:
            return True     # no toolkit display yet: answer, don't remember
        _positioning = 'NATIVE WAYLAND' not in display.verdict(said)
        log.info("window placement: {} ({})".format(
                    'available' if _positioning
                    else 'NOT available — the compositor owns it', said))
    except Exception as e:
        log.info("could not tell whether windows may be placed ({!r}); "
                 "assuming they may".format(e))
        _positioning = True
    return _positioning


# Which environment variable each toolkit reads to choose its transport, and
# what the useful values are.
#
# SWITCHES, NOT ENVIRONMENT VARIABLES — including here. I argued for an
# exception on the grounds that GDK_BACKEND is GTK's own variable rather than
# an AZT toggle; Kent, 2026-09-14: "rather than GDK_BACKEND, how about
# --gdk-backend?" The rule is about how WE are told to behave differently, and
# that is what this is, whoever consumes it downstream. The variable still has
# to be exported, because it is how GTK and Qt are told — but the user tells
# us on the command line and we do the exporting, in one place, logged.
_TRANSPORT_SWITCHES = {
    '--gdk-backend': ('GDK_BACKEND', 'gtk', ('wayland', 'x11')),
    '--qt-platform': ('QT_QPA_PLATFORM', 'qt', ('wayland', 'xcb')),
}


def _apply_dmabuf_default():
    """Turn WebKitGTK's accelerated buffer handoff OFF, unless `--dmabuf`.

    WHY OFF BY DEFAULT. Kent, 2026-09-14, on a window drawn in diagonal
    black bands with every scanline offset a little further than the last:
    "I've seen something similar multiple times. it typically resolves, just
    wondering". That shear is the signature of a STRIDE MISMATCH — the page
    renders correctly and the compositor reads the buffer with the wrong
    pitch. `agenda/webview_when_to_finish.md` Step 0 already knew the
    mitigation ("if GTK is blank retry with
    WEBKIT_DISABLE_DMABUF_RENDERER=1") and ADR 0004 D8 keeps Qt available as
    the escape hatch for the blank-window variant of the same bug.

    A SWITCH WOULD NOT HAVE HELPED, which is why this is the default and not
    an option. Kent: "it is so intermittent and infrequent, that 'restart' is
    as useful as 'restart with x parameters'. unless we find parameters that
    remove it entirely." Disabling the path removes the class rather than
    making it rarer, so it belongs where it cannot be forgotten.

    THE COST IS PER-FRAME, and nothing here draws frames continuously: the
    chooser is a grid of buttons, the splash is text and an occasional
    progress tick, the alphabet chart is a grid of images that renders in
    ~0s. The two things that WOULD feel it do not exist yet — drag with
    animation (agenda/drag_and_drop_animation.md, Step 4) and scrolling a
    long image-bearing verify list. `--dmabuf` is how those get measured
    both ways when they arrive; the note is in that item too.

    Only for WebKitGTK. Qt/QtWebEngine does not read this variable, and a
    value exported for it would be noise.
    """
    if _engine() not in (None, 'gtk'):
        return
    if _switch('--dmabuf'):
        log.info("WEBKIT_DISABLE_DMABUF_RENDERER left alone (--dmabuf): the "
                 "accelerated buffer handoff is ON, which is faster per "
                 "frame and is what produced the diagonal shearing this "
                 "flag exists to test.")
        return
    if 'WEBKIT_DISABLE_DMABUF_RENDERER' in os.environ:
        # An explicit environment setting is the user's, not ours to
        # overwrite — and saying so beats a silent disagreement with
        # whatever they set it for.
        log.info("WEBKIT_DISABLE_DMABUF_RENDERER already set to %r in the "
                 "environment; leaving it",
                 os.environ['WEBKIT_DISABLE_DMABUF_RENDERER'])
        return
    os.environ['WEBKIT_DISABLE_DMABUF_RENDERER'] = '1'
    log.info("WEBKIT_DISABLE_DMABUF_RENDERER=1 (default): WebKitGTK's "
             "accelerated buffer handoff is off, because a stride mismatch "
             "in it draws the window in diagonal bands. --dmabuf turns it "
             "back on for testing.")


def _apply_transport_switches():
    """Export the toolkit transport the user asked for. MUST run before the
    toolkit initialises, i.e. before webview.start().

    This exists for one experiment (agenda/wayland_freeze_audit.md): the
    alphabet chart takes 37-42s on tkinter and ~0s on both webview engines,
    but tkinter is the only backend on XWayland — both webview engines came
    up NATIVE WAYLAND — so toolkit and transport vary together and the
    comparison cannot say which is to blame. Forcing one engine onto X11
    changes only the transport:

        python main.py --webview --engine=gtk --gdk-backend=x11

    `utilities/display.py` reports what actually happened, so a run that
    silently ignored the switch is visible: the line must say
    `GdkX11Display` / `platformName=xcb`, not `GdkWaylandDisplay`.
    """
    for switch, (var, engine, known) in _TRANSPORT_SWITCHES.items():
        value = _switch_value(switch)
        if not value:
            continue
        if value not in known:
            log.warning("%s=%s is not one of %s; passing it to %s anyway",
                        switch, value, '/'.join(known), var)
        os.environ[var] = value
        log.info("%s=%s set from %s (affects the %s engine; see "
                 "display.py's line for what the toolkit actually did)",
                 var, value, switch, engine)
    # THE GTK THEME IS A SUSPECT IN THE RESIZE-ON-FOCUS FAULT, and this is
    # how to rule it in or out.
    #
    # Researched 2026-09-16 at Kent's request. numix-gtk-theme issue #362
    # reports EXACTLY this symptom — a window that "very quickly
    # disappears/reappears and resizes" when it loses focus, and resizes
    # back when it regains it — and the cause was the THEME: the `:backdrop`
    # rules in its `_window.scss`. A `:backdrop` state that changes a
    # window's margin, padding or shadow changes the window's geometry, so
    # GTK recalculates the size on every focus change. The reporter fixed it
    # by commenting those rules out.
    #
    # That would explain why nothing on our side helps: if the resize is
    # GTK's own style-driven recalculation, it is not the compositor
    # declining our geometry at all, and no amount of `resize()`,
    # `set_default_size` or MIN_SIZE would touch it.
    #
    # `GTK_THEME` is GTK's own variable, exported here from a switch for the
    # same reason `--gdk-backend` is (standing rule: switches, not
    # environment variables — we do the exporting, in one place, logged).
    #   `--gtk-theme=Adwaita` is the test: if the flicker stops, the
    # installed theme is the cause and this is not an AZT bug at all.
    theme = _switch_value('--gtk-theme')
    if theme:
        os.environ['GTK_THEME'] = theme
        log.info("GTK_THEME=%s set from --gtk-theme. If this stops the "
                 "resize-on-focus flicker, the cause is the installed GTK "
                 "theme's `:backdrop` rules changing window geometry (see "
                 "numix-gtk-theme issue 362), not this app.", theme)


def _supports_created_hidden():
    """Can this engine create a window hidden and later show() it?

    MEASURED on all four backends with
    tests/manual/webview_multiwindow/platform_probe.py --start-hidden:

        EdgeChromium / WebView2 (Windows 11)  yes
        WebKit (macOS)                        yes
        QtWebEngine (Linux)                   yes
        WebKitGTK (Linux)                     NO — show() never maps it

    So GTK is the exception, not the rule, and creating windows visible
    everywhere costs every other platform a startup flash for nothing. Every
    task window is built withdrawn (tasks/chooser.py), so on GTK a hidden
    window would never appear at all — which is why this is a capability
    question and not a preference.

    NOW OFF EVERYWHERE (2026-09-11), because the probe measured the wrong
    capability. It asked "can show() MAP a window created hidden" and Qt
    answered yes. The question the app needs answered is "does a window
    created hidden LOAD ITS PAGE", and on Qt it does not. Kent's Sound Card
    Settings window is the proof, and the A/B is in one log:

        window 52: created HIDDEN (asked withdrawn), url=…/base.html
        window 52: DEICONIFY (show) requested
        window 52: pywebview show() now
        …and nothing else. Ever.

    No `GET /base.html`, no `GET /widgets.js`, no
    "Toplevel 52 JS ready — flushing N queued calls". Every window in the
    same run that says "created visible" gets all three. So the page never
    loaded, `_poll_until_loaded` never succeeded, the JS queue never flushed,
    and the window came up EMPTY — while the Python side happily built
    labels, buttons and tooltips into a queue nobody would ever read.

    That is a worse failure than the GTK one it was written to avoid: a
    window that never appears is at least obviously broken, whereas this one
    appears and is blank, so it reads as a bug in whatever was supposed to be
    inside it. It cost most of an afternoon's diagnosis pointed at labels,
    variables and images that were all working.

    The cost of turning it off is the startup flash it was added to remove.
    That is a cosmetic problem, and this is not.

    `--webview-hidden` still forces it on, for re-testing — now with a
    second thing to check besides "does it appear": does it LOAD."""
    return False


_NO_DEFAULT_YET = object()      # None is a real answer (macOS), so sentinel
_default_cached = _NO_DEFAULT_YET


def _default_engine():
    """The engine to use when nobody said — CHOSEN BY US, not by pywebview.

    Kent's rule, 2026-09-08: *"gtk if --webview only, if gtk installed. else
    qt (if installed), else die."*

    WHY IT MATTERS THAT WE CHOOSE: pywebview's own preference order is an
    implementation detail of whatever is installed, so the same build and the
    same command line can run a DIFFERENT engine on a different machine — and
    the engines are not equivalent (created-hidden works on Qt and not GTK;
    the Qt backend has a garbage-collection crash GTK does not). Deciding
    here makes the common case identical everywhere and puts the decision
    somewhere a reader can find it.

    GTK first because it is the engine A-Z+T is known to work on. Qt second
    because it renders correctly but still has that crash. "Else die" is
    already handled upstream and better: `utilities.ui_backend` refuses the
    webview backend when neither host is importable, and falls back to
    tkinter with the reason on the log and on stderr — a refusal that names
    itself, rather than an exit."""
    # ANSWERED ONCE. `_engine()` is called from five places, so without this
    # the choice was re-derived — and re-LOGGED — per caller: "no engine
    # specified; using gtk" appeared twice in one boot (Kent, 2026-09-24).
    # That is the same shape as the duplicated backend refusal this module's
    # neighbour was fixed for: one decision, announced once. Safe to cache
    # because nothing it reads changes after `ui_backend.chosen()` has run,
    # and any auto-install happened there, before this module was imported.
    global _default_cached
    if _default_cached is not _NO_DEFAULT_YET:
        return _default_cached
    _default_cached = _decide_default_engine()
    return _default_cached


def _decide_default_engine():
    if platform.system() == 'Windows':
        # Named explicitly so a missing WebView2 runtime fails loudly instead
        # of silently dropping to mshtml, which has no CSS Grid.
        return 'edgechromium'
    if platform.system() != 'Linux':
        return None                     # macOS: pywebview uses Cocoa
    # MATCH THE DESKTOP FIRST, then fall back to whatever works. Kent,
    # 2026-09-24: "it would be nice if we could tell which toolkit their OS
    # uses natively, in cases where people just put --webview". On KDE or
    # LXQt a Qt window has native decorations, file dialogs and menus; on
    # GNOME or XFCE a GTK one does. Preferring GTK unconditionally, as this
    # did, made A-Z+T look like a visitor on every Qt desktop.
    #   Availability still wins: a Qt desktop with no Qt gets GTK rather than
    # nothing. The checks are the app's own host tests, not `find_spec`,
    # because an importable `gi` with no WebKit typelib renders nothing.
    from utilities import ui_backend as _sel
    order = [('gtk', _sel.gtk_host_problem), ('qt', _sel.qt_host_problem)]
    native = _sel.native_toolkit()
    if native == 'qt':
        order.reverse()
    for engine, problem in order:
        if problem() is None:
            log.info("no engine specified; using {}{}".format(
                engine, " (this desktop's native toolkit)"
                if engine == native else
                " ({} is unavailable here)".format(order[0][0])
                if engine != order[0][0] else ""))
            return engine
    # Neither host present. ui_backend.webview_problem() should already have
    # refused the backend before we got here; returning None lets pywebview
    # produce its own error rather than us inventing one.
    log.warning("no webview host toolkit found (neither gi nor qtpy); "
                "pywebview will fail to start")
    return None


# Has the engine substitution been announced yet? `_engine()` is called from
# several places and recomputes each time; the REPORT must happen once. Mirrors
# `ui_backend._warned`.
_engine_reported = False


def _engine():
    """The pywebview backend to ask for, or None to let it choose.

    ON WINDOWS WE ASK FOR edgechromium EXPLICITLY, because the fallback is
    worse than a failure: if the WebView2 runtime is missing, pywebview can
    drop to **mshtml** — the legacy Trident/IE engine, which has no CSS Grid.
    Our pages would then render as garbage rather than not rendering, and it
    would look like our bug instead of a missing runtime. Naming the engine
    makes a missing WebView2 raise at start, which the backend selector can
    report and fall back to tkinter over. WebView2 ships with Windows 11 and
    is present on most Windows 10, with a ~2MB bootstrapper otherwise, so a
    loud failure is actionable.

    An explicit --engine= or AZT_WEBVIEW_ENGINE still wins, so mshtml or cef
    remain reachable deliberately."""
    # An explicit request wins — but only if it can actually run. If it
    # cannot, REPORT AND SUBSTITUTE: say plainly what was asked for, why it
    # cannot be honoured, and what is being used instead. Neither silence
    # (which makes the engine differences we measured unreasonable about) nor
    # refusal (which would drop to tkinter over a missing *engine*, a much
    # bigger substitution than the other engine).
    #
    # PYWEBVIEW_GUI is pywebview's OWN variable, honoured so its documented
    # way of choosing an engine keeps working; we add no variable of our own
    # (see _switch).
    from utilities import ui_backend as _select
    requested = _select.requested_engine()
    if not requested:
        return _default_engine()
    problem = _select.engine_problem()
    if not problem:
        return requested
    # AN ENGINE ASKED FOR BY NAME AND NOT DELIVERED IS WORTH SEEING, exactly
    # as a backend asked for and not delivered is: the whole point of naming
    # an engine is to measure THAT engine, and a substitution nobody notices
    # makes every measurement taken afterwards unreasonable-about. Recorded
    # rather than raised here because this runs while deciding what to pass to
    # webview.start() — there is no window yet. main.py's
    # warn_backend_problems() shows it once there is.
    #
    # ANNOUNCED ONCE, LIKE ui_backend.chosen()'s refusal. This function is NOT
    # cached and is called from five places (the display-stack banner, the
    # dmabuf guard, two log lines and the dev console), so an unguarded report
    # here would say the same thing five times — which is how the backend
    # refusal's duplicate read as "something decides this twice" when nothing
    # did. The ANSWER is the same every call (argv, the environment and what
    # is importable do not change mid-run); only the announcement needs to be
    # once.
    global _engine_reported
    substitute = _default_engine()
    if substitute and substitute != requested:
        detail = "{}; using {} instead".format(problem, substitute)
    else:
        substitute = None
        detail = "{}; no alternative engine is available either".format(problem)
    if not _engine_reported:
        _engine_reported = True
        log.warning(detail)
        source = (_select.engine_request_source()
                  or '--engine={}'.format(requested))
        _select.BACKEND_PROBLEMS.append((source, detail))
    return substitute


# EVERY pywebview window we create, held strongly and forever.
#
# The Qt segfault is a GARBAGE COLLECTION, not a destroy — the native
# backtrace shows sipWrapper_dealloc -> forgetObject ->
# ~sipQMainWindow -> ~QWidget -> close -> hideChildren -> hideEvent ->
# QWebEnginePage::setVisible, running under _Py_HandlePending inside a
# loadFinished slot. Something dropped the last Python reference to the
# window and CPython collected it mid-Qt-event.
#
# This list makes that impossible from OUR side, which is worth doing on its
# own terms (a UI window should not be collectable while its page is live)
# and also splits the question: if the crash survives this, the reference
# being dropped is inside pywebview's Qt backend, not ours.
_all_wv_windows = []

# How long an operation must run before it is worth a dialog. Below this the
# work finishes and nobody sees anything; above it the dialog appears as it
# always did. Same name as ui_tkinter's so the two cannot drift unnoticed.
WAIT_DELAY_MS = 400
_WAIT_DELAY_MS = WAIT_DELAY_MS          # the name used inside wait()


def _badge(window, label, program=None):
    """Stamp a corner badge naming the window, so a page on screen can be
    identified.

    Every window loads the SAME base.html and, until a task builds into it,
    looks identical — an empty themed box. So "the app shows a blank green
    window" could not be told from "the app shows the WRONG blank green
    window", and it turned out to matter: the visible window was the root
    (empty by design; task widgets go into Toplevels) while the window that
    had 408 widget calls flushed into it was somewhere unseen. Debug aid, and
    it should go once windows reliably show what they contain."""
    # DEBUG ONLY. It was drawn unconditionally and reached a user's screen
    # (Kent, 2026-09-08, on the non-dev splash) — a black-on-green "window 2"
    # sticker over the app's own title area. Gated on the app's testing flag,
    # like webview's devtools.
    if not window:
        return
    if not getattr(program, 'testing', False):
        return
    code = ('(function(){'
            'var b=document.getElementById("wv-badge");'
            'if(!b){b=document.createElement("div");b.id="wv-badge";'
            # LOWER LEFT, not upper right. Kent, 2026-09-15: "may be handy,
            # but it's mostly annoying right now… less in the way there."
            # The top right is where this app puts things a user reaches for
            # — the Tasks button sits there on every page — and the badge
            # is `pointer-events:none`, so it does not block a click but it
            # does cover what you are trying to read. The lower left is the
            # one corner no page uses.
            'b.style.cssText="position:fixed;bottom:0;left:0;z-index:99999;'
            'background:#000;color:#0f0;font:12px monospace;padding:2px 6px;'
            'opacity:0.8;pointer-events:none";'
            'document.body.appendChild(b);}'
            'b.textContent=' + json.dumps(label) + ';'
            '})()')
    _js(window, code)


def _close_native_window(owner, label='window'):
    """Retire a pywebview window — by HIDING it, not destroying it.

    WHY: destroying a pywebview window is expensive to undo — a window costs
    a page load, four HTTP round trips and a JS bridge handshake before a
    single widget can be created — and A-Z+T reuses its windows anyway.

    CORRECTED 2026-09-08: this comment used to say plainly that destroying a
    window under Qt segfaults. It does not — the platform probe destroys a Qt
    window and survives cleanly. What the app's crash trace actually shows is
    a pywebview window wrapper being GARBAGE COLLECTED inside a loadFinished
    slot, which is a reference-keeping problem, not a consequence of calling
    destroy(). The teardown chain below is real and worth keeping as the
    mechanism, but it is what happens when the object is freed at the wrong
    MOMENT, not what happens whenever destroy() is called:

        sendPostedEvents -> sipQMainWindow::~sipQMainWindow
        -> QWidget::~QWidget -> QWindow::close -> hide_helper
        -> hideChildren -> sipQWebEngineView::hideEvent
        -> QWebEnginePage::setVisible   <-- SIGSEGV

    That is what "Release of profile requested but WebEnginePage still not
    deleted" was warning about all along. It appears in runs that do NOT
    crash, which is why it was dismissed as noise; it is a teardown-order
    signal that is necessary but not sufficient.

    HIDING SUITS A-Z+T ANYWAY. tkinter windows here are already reused
    rather than rebuilt — Wait is explicitly "built ONCE on the root and then
    withdrawn/deiconified rather than destroyed/rebuilt per wait" — and
    creating a pywebview window means a fresh page load, an HTTP round trip
    and a JS bridge handshake, so destroying one to make another is the
    expensive choice as well as the crashing one.

    KNOWN COST, stated rather than hidden: hidden windows are never freed, so
    a long session accumulates them. That is a leak, and it is preferable to
    a segfault; if it starts to matter the fix is a pool that reuses a hidden
    window for the next page, which is what the app's own idiom already
    suggests. Real teardown happens when the process exits."""
    wv = getattr(owner, '_wv_window', None)
    if not wv or not _started.is_set():
        return
    try:
        wv.hide()
        # NAME WHO ASKED, as `Toplevel.withdraw` does. Three of these lines in
        # a row and nothing after them is what "didn't return to task chooser
        # on alphabet close" looked like in the log (Kent, 2026-09-14), and
        # the message could not say which windows went or who sent them — so
        # the log recorded that three windows were hidden and left the only
        # useful question unanswered. `withdraw` learned this on 2026-09-09
        # for exactly the same reason; this path never did.
        try:
            import traceback as _tb
            frame = _tb.extract_stack(limit=3)[0]
            who = "{}:{} in {}()".format(frame.filename.rsplit('/', 1)[-1],
                                         frame.lineno, frame.name)
        except Exception:
            who = 'caller unknown'
        # The message used to say "destroying crashes QtWebEngine", which the
        # docstring above RETRACTED on 2026-09-08 — destroying is fine; being
        # garbage-collected at the wrong moment is what crashes. Left as it
        # was, the log went on asserting the retracted cause to every future
        # reader, in the one place a person looks first.
        log.info("{} hidden rather than destroyed, by {}: reused, not "
                 "rebuilt, and freeing a pywebview window at the wrong "
                 "moment is what crashes Qt (see _close_native_window)"
                 "".format(label, who))
    except Exception as e:
        log.debug("could not hide {}: {}".format(label, e))


def _log_engine_in_use(window):
    """Record which engine ACTUALLY rendered, not which one we asked for.

    Without `--engine` we ask for nothing on Linux and pywebview picks —
    GTK if its typelibs are importable, else Qt. So the same build and the
    same command line can run a different engine on a different machine
    (Kent, 2026-09-08), and the engines are NOT equivalent: created-hidden
    works on Qt and not on GTK, and the Qt backend has a garbage-collection
    crash the GTK one does not. A bug report that does not name the engine
    cannot be read.

    The userAgent is the engine's own self-report, so it cannot be wrong the
    way an inference from installed packages can."""
    ua = _js(window, 'navigator.userAgent') or ''
    low = ua.lower()
    if 'edg/' in low:
        name = 'EdgeChromium/WebView2'
    elif 'qtwebengine' in low:
        name = 'QtWebEngine'
    elif 'chrome' in low and 'version/' not in low:
        name = 'Chromium (CEF?)'
    elif 'macintosh' in low and 'applewebkit' in low:
        # macOS Cocoa/WKWebView. Its userAgent stops at "(KHTML, like Gecko)"
        # — no Version/, no Chrome/ — so both other WebKit tests miss it and
        # it reported as "unrecognised" on the first Mac run.
        name = 'WebKit (macOS WKWebView)'
    elif 'version/' in low and 'safari' in low:
        name = 'WebKitGTK'
    elif 'trident' in low or 'msie' in low:
        name = 'MSHTML/Trident — LEGACY IE, no CSS Grid; pages will be broken'
    else:
        name = 'unrecognised'
    asked = _engine() or '(not specified — pywebview chose)'
    log.info("webview engine IN USE: {} | asked for: {}".format(name, asked))
    log.info("webview userAgent: {}".format(ua))
    if 'LEGACY' in name:
        log.warning("This engine cannot render A-Z+T's pages. Install the "
                    "WebView2 runtime, or run with --tkinter.")


def _app_identity(program):
    """Tell the desktop what application this is, before the GUI starts.

    tkinter gets this for free: `Tk(className='azt')` sets WM_CLASS, the
    desktop matches it to azt's .desktop file, and the dock shows the right
    icon and name. pywebview creates its own GTK/Qt application and sets
    neither, so the dock showed "python3" with a generic icon.

    GLib's prgname is the GTK equivalent and has to be set BEFORE the
    application is created, which is why this runs on the way into
    webview.start(). Harmless where gi is absent (Qt, Windows): those
    backends take their identity elsewhere and the import simply fails."""
    name = getattr(program, 'className', None) or 'azt'
    try:
        import gi
        from gi.repository import GLib
        GLib.set_prgname(name)
        GLib.set_application_name('A-Z+T')
        log.info("desktop identity set: prgname={}".format(name))
    except Exception as e:
        log.debug("could not set desktop identity ({}): {}".format(name, e))


def _ico_for(png):
    """A `.ico` made from our PNG, cached; or None if it cannot be made.

    WINDOWS DOES NOT HAVE TO SETTLE FOR A GENERIC ICON (Kent, 2026-09-24:
    "generic icon should be resolvable, though, right?"). It is, and with a
    library already in `requirements.txt`: Pillow writes multi-size ICO, which
    is the one format `System.Drawing.Icon` accepts and the reason every
    `--webview` run died on Windows 11.

    SQUARED FIRST, by padding rather than scaling. ICO frames are square, and
    handing PIL a non-square image makes it stretch — the logo is wider than
    it is tall, so it would arrive squashed. The macOS installer pads for the
    same reason (`sips --padToHeightWidth` in RunMetoInstall_Mac.command).

    Cached in the temp directory rather than beside the source, which lives in
    the repo, and regenerated when the PNG is newer. Failure is not fatal:
    returning None just means no icon, which is what the crash was costing us
    anyway."""
    import tempfile
    out = os.path.join(tempfile.gettempdir(), 'azt-webview-icon.ico')
    try:
        if (os.path.exists(out)
                and os.path.getmtime(out) >= os.path.getmtime(png)):
            return out
        from PIL import Image
        im = Image.open(png).convert('RGBA')
        side = max(im.size)
        if im.size != (side, side):
            square = Image.new('RGBA', (side, side), (0, 0, 0, 0))
            square.paste(im, ((side - im.width) // 2,
                              (side - im.height) // 2))
            im = square
        im.save(out, format='ICO',
                sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128),
                       (256, 256)])
        log.info("made a Windows icon at %s from %s", out, png)
        return out
    except Exception as e:
        log.info("could not make a .ico from %s (%s); starting without an "
                 "icon, which is better than the crash a PNG causes here",
                 png, e)
        return None


def _icon_path(program):
    """A real file path for the window icon, or None.

    `theme.photo['icon']` is a ui_webview.Image, which keeps the source path
    it loaded from — so the icon the tkinter backend hands to iconphoto() is
    reachable here as a path, which is what pywebview wants."""
    theme = getattr(program, 'theme', None)
    photo = getattr(theme, 'photo', None)
    if not isinstance(photo, dict):
        return None
    for key in ('icon', 'icontall', 'transparent'):
        img = photo.get(key)
        path = getattr(img, 'filename', None)
        if path and os.path.exists(str(path)):
            return str(path)
    return None


def _start_kwargs(program=None):
    """Arguments for webview.start(). `program` is unused since the console
    stopped following its dev-settings flag; kept because the one caller
    passes it and the engine choice may yet want it.

    THE CONSOLE IS OFF UNLESS `--console` IS PASSED. Kent, 2026-09-14: "let's
    turn off the console by default. and rather than calling it
    --no-i-really-do-want-the-console-this-time, let's just use --console."
    One switch, asked for when wanted.

    It used to follow the app's dev-settings flag — so it was on in this
    working tree always, and `--user` was the only way off, which also drops
    the test lift, the auto-opened task, the debug badge and the dev theme.
    Before THAT it was unconditional, which opened the remote-debugging
    server on field machines ("Remote debugging server started successfully"
    in their logs).

    KNOWN TO SEGFAULT ON QT, and honoured anyway now that it must be asked
    for. The faulthandler dump caught the main thread mid-slot (2026-09-11):

        Garbage-collecting
        qt.py:639 in resizeEvent
        qt.py:208 in show_inspector          <-- only reached when debug=True
        qt.py:737 in on_load_finished

    `show_inspector` opens the Web Inspector as each page finishes loading,
    its resize runs a Python GC inside a Qt `resizeEvent`, and the collection
    frees something Qt is still using — the same fault
    `_close_native_window` documents from 2026-09-07 ("a pywebview window
    wrapper being GARBAGE COLLECTED inside a loadFinished slot"), located
    precisely: it is in the inspector path, so it only happens with the
    console on. That is also why Qt "worked earlier the same day" — `--user`
    runs had no console — and why four `base.html` pages were listed in the
    inspector: one per window, each another chance to hit it on load."""
    engine = _engine()
    debug = _switch('--console')
    if debug:
        log.info("console ON (--console): remote debugging server and "
                 "devtools.")
        if engine == 'qt':
            log.warning("console on Qt is known to segfault: show_inspector "
                        "garbage-collects inside resizeEvent (see "
                        "_start_kwargs). --engine=gtk if it crashes.")
    kwargs = {'debug': debug}
    if engine:
        kwargs['gui'] = engine
        log.info("Using webview engine {}".format(engine))
    return kwargs


# ── Startup state ────────────────────────────────────────────────────
_started = threading.Event()      # set once webview.start() has loaded
_js_queue = []                     # [(window, code), ...] queued before start
_js_queue_lock = threading.Lock()

# ── Per-window loaded tracking ───────────────────────────────────────
# Maps pywebview window objects to their owning Toplevel/Root widget,
# so _js() can check/queue per-window.
_window_owners = {}  # pywebview window → Toplevel/Root instance
_window_owners_lock = threading.Lock()

def _register_window_owner(wv_window, owner):
    with _window_owners_lock:
        _window_owners[wv_window] = owner

def _get_window_owner(wv_window):
    with _window_owners_lock:
        return _window_owners.get(wv_window)

# ── JS execution helper ──────────────────────────────────────────────
def _js(window, code):
    """Evaluate JS in the webview window. Queues if webview hasn't started yet,
    or if the specific window hasn't finished loading.

    A QUEUE THAT CAN BE OVERTAKEN IS NOT A QUEUE. Both gates below are read
    and acted on under the lock that the corresponding flush holds while it
    drains, so a call either joins the queue (and keeps its place) or is sent
    directly (and the queue is already empty). Without that, "the page is
    ready" became true the moment the flag was set — while the queue still
    held every call made before it — so a widget created in that gap was
    evaluated FIRST and its parent, still queued, arrived after: the child
    could not find it, fell back to #root, and laid itself out against the
    page. One such widget per run, wid varying, on whichever page happened to
    be building as its window finished loading (Kent, 2026-09-15: three
    rounds of "the extra sort group is there", widgets 221/222 in different
    runs). See `_flush_js_queue` and `_drain_wv_js_queue`."""
    if not window:
        return None
    if not _started.is_set():
        with _js_queue_lock:
            # RE-CHECKED INSIDE THE LOCK: the flush sets the flag holding it,
            # so this either appends before the flag flips or sees it flipped.
            if not _started.is_set():
                _js_queue.append((window, code))
                return None
    # Check per-window loaded state
    owner = _get_window_owner(window)
    if owner is not None and hasattr(owner, '_wv_loaded'):
        with getattr(owner, '_wv_queue_lock', _js_queue_lock):
            if not owner._wv_loaded.is_set():
                owner._wv_js_queue.append(code)
                return None
    if not getattr(window, '_destroyed', False):
        try:
            return window.evaluate_js(code)
        except Exception as e:
            log.debug(f"JS eval failed: {e}")
    return None

# How many queued statements to send in one evaluate_js. Each call is a
# synchronous round trip into the web engine, so a page that queues 408 of
# them (a real number, from the first sort page to render) pays 408 of those
# before it can paint. They are all fire-and-forget statements whose results
# nobody reads, so they can travel together.
_JS_BATCH = 100


def _eval_batched(window, codes):
    """Send *codes* to *window* in batches rather than one at a time.

    ONE FAILING STATEMENT MUST NOT TAKE ITS BATCH WITH IT: each statement is
    wrapped in its own try/catch in the page, so a bad call logs there and
    the rest of the batch still runs — which is what the one-at-a-time loop
    gave us for free and is worth keeping."""
    if not window or getattr(window, '_destroyed', False):
        return
    batch = []

    def send():
        if not batch:
            return
        wrapped = ''.join(
            'try{%s}catch(e){console.error("azt js:", e, %s)}\n'
            % (code, json.dumps(code[:120])) for code in batch)
        try:
            window.evaluate_js(wrapped)
        except Exception as e:
            log.debug(f"Batched JS failed ({len(batch)} statements): {e}")
        batch.clear()

    for code in codes:
        batch.append(code)
        if len(batch) >= _JS_BATCH:
            send()
    send()


def _flush_js_queue():
    """Send every pre-start JS call, THEN declare the engine started.

    Setting `_started` is what makes `_js` evaluate directly instead of
    queueing, so it must not become true until there is nothing left in the
    queue to be overtaken — see the ordering note in `_js`. Draining is a
    LOOP because a build thread goes on producing while we send: each pass
    takes what is there, sends it outside the lock (a round trip into the
    engine, not something to hold a lock across), and the flag is set only by
    a pass that finds the queue already empty."""
    passes = 0
    while True:
        with _js_queue_lock:
            if not _js_queue:
                _started.set()
                return
            queue = list(_js_queue)
            _js_queue.clear()
        passes += 1
        if passes == 20:
            # Not fatal, and not a reason to give up ordering: just worth
            # seeing, because it means widgets were still being built well
            # after the page reported itself ready.
            log.info("pre-start JS queue still refilling after 20 passes "
                     "({} in this one)".format(len(queue)))
        # Group consecutive calls by window so each window's batch travels whole.
        run, current = [], None
        for window, code in queue:
            if window is not current and run:
                _eval_batched(current, run)
                run = []
            current = window
            run.append(code)
        if run:
            _eval_batched(current, run)

# ── Waiting on a widget's destruction ─────────────────────────────────
# tkinter's wait_window(w) blocks until w is destroyed, and A-Z+T leans on it
# two ways: on a WINDOW (the LIFT chooser blocks boot until a file is picked)
# and on a CANARY WIDGET — ~30 sites do `w.wait_window(self.l)` on a Label,
# because the label outlives the page build and its destruction is the signal.
#
# The old implementation waited on an event that only on_quit() ever set, and
# ignored its argument entirely. So a window retired by destroy() rather than
# quit left the waiter blocked forever — which is exactly where boot stopped
# after choosing a LIFT file (2026-09-08): the chooser hid, was destroyed, and
# nothing continued.
#
# A registry keyed by widget id fixes both cases at once and needs no change
# at any call site, because _WebviewWidget.destroy is already recursive: a
# window's destruction releases waiters on its children too.
_waiter_lock = threading.Lock()
_waiters = {}          # wid -> [threading.Event, ...]


def _waiter_for(wid):
    ev = threading.Event()
    with _waiter_lock:
        _waiters.setdefault(wid, []).append(ev)
    return ev


def _release_waiters(wid, why=''):
    with _waiter_lock:
        events = _waiters.pop(wid, [])
    if events:
        log.info("releasing {} waiter(s) on widget {}{}".format(
            len(events), wid, ' ({})'.format(why) if why else ''))
    for ev in events:
        ev.set()


def _quit_window_over(widget):
    """The wid of the nearest ancestor window that has already quit, or None.

    "QUIT", not "gone": a quit window in this backend is HIDDEN, keeps its
    `_exists`, and can still be found by a flow that was mid-build when the
    user pressed Exit. Its `exitFlag` is the honest answer, and it is the
    one every guard in the app already reads. Walks parents rather than
    asking the root, because a task window can quit while the root is
    perfectly alive — which is the whole case this exists for.

    Never raises: it is consulted on the way INTO a wait, where an
    exception would be a new failure in place of the one being prevented."""
    try:
        seen = 0
        node = widget
        while node is not None and seen < 64:
            seen += 1
            flag = getattr(node, 'exitFlag', None)
            if (getattr(node, 'is_window', False) and flag is not None
                    and flag.istrue()):
                return getattr(node, '_wid', '?')
            node = getattr(node, 'parent', None)
    except Exception as e:
        log.debug("could not tell whether a window above {} had quit ({!r})"
                  "".format(getattr(widget, '_wid', '?'), e))
    return None


def _release_waiters_below(widget, why=''):
    """Free everything parked in `wait_window` on this widget OR ANY OF ITS
    DESCENDANTS.

    THE CANARY IDIOM IS WHY THIS HAS TO WALK. Around thirty call sites wait
    on a CANARY WIDGET inside a window rather than on the window — the
    widget's destruction is the signal that a page is finished
    (`sort_ui.py:762`, `ui_shell.py:2485`, …). `destroy()` handles that
    correctly: it recurses into `_children` and releases each. `on_quit` did
    not — it released waiters on the WINDOW'S OWN wid and hid the window,
    which is not a destruction, so every canary inside it stayed alive and
    every thread parked on one stayed parked.

    THAT IS THE HANG (Kent's faulthandler dump, 2026-09-16). Exit on the
    sort run window logged `widget 237: waiting on widget 764`, hid window
    237, released waiters on 237 — and left the sort flow blocked on 764
    forever:

        ui_webview.py:1844 in wait_window
        sorting_engine.py:1434 in presenttosort
        … sort → maybesort → after_presort → drive_work → runcheck
        ui_webview.py:3325 in <lambda>      (the button)

    With the app's task flow parked on a pywebview API thread and nothing
    left on screen, the app is indistinguishable from closed — which is
    what Kent reported ("I thnk the runwindow is closing the app on exit").
    tkinter never had this because destroying a Toplevel destroys every
    descendant, and `wait_window` returns on the target's destruction.

    NOT a `destroy()`: this backend HIDES windows rather than destroying
    them (see `_close_native_window` — freeing a pywebview window at the
    wrong moment crashes Qt), and tearing the page down here would be a
    much larger change than releasing the waits. Iterative rather than
    recursive, and `seen`-guarded, because this runs during teardown where
    a cycle in `_children` must not become a stack overflow."""
    seen = set()
    stack = [widget]
    while stack:
        current = stack.pop()
        wid = getattr(current, '_wid', None)
        if wid is None or wid in seen:
            continue
        seen.add(wid)
        _release_waiters(wid, why)
        try:
            stack.extend(list(getattr(current, '_children', None) or []))
        except Exception as e:
            log.info("could not walk the children of widget {} while "
                     "releasing waits ({!r})".format(wid, e))


# ── Base Widget ───────────────────────────────────────────────────────
class _WebviewWidget:
    """Base for all webview widgets. Mirrors the tkinter widget API."""

    # Toplevel and Root set this True. A window is NOT a DOM element, so a
    # widget parented to one has no DOM parent to find — that is the normal
    # case, not a fault, and the page must not warn about it.
    is_window = False

    # ── Sizing ────────────────────────────────────────────────────────
    # Extra room for the window's own chrome and a possible scrollbar when
    # fitting a window to its content. Small on purpose: too much and every
    # window carries dead margin.
    _FIT_PAD = 28
    _FIT_MIN = (420, 260)

    # Grid kwargs that get extracted before widget init (same as ui_tkinter.Gridded)
    _gridkwargs = {'sticky', 'row', 'rowspan', 'column', 'columnspan', 'colspan',
                   'r', 'c', 'col', 'padx', 'pady', 'ipadx', 'ipady',
                   'gridwait', 'draggable', 'droppable'}

    def __init__(self, parent=None, widget_type='frame', **kwargs):
        self._wid = _next_wid()
        self.parent = parent
        self._widget_type = widget_type
        self._children = []
        self._exists = True
        self._bindings = {}  # event_name → [callback]
        self._config = {}
        self._grid_visible = False

        # Inherit from parent
        if parent:
            for attr in ('theme', 'wraplength', 'renderer', 'exitFlag',
                         '_wv_window'):
                if hasattr(parent, attr):
                    setattr(self, attr, getattr(parent, attr))
            parent._children.append(self)

        # Extract grid kwargs
        self._has_grid = any(k in self._gridkwargs for k in kwargs)
        self._grid_opts = {}
        if self._has_grid:
            self._grid_opts['sticky'] = kwargs.pop('sticky', 'ew')
            self._grid_opts['row'] = kwargs.pop('row', kwargs.pop('r', 0))
            self._grid_opts['column'] = kwargs.pop('column',
                                        kwargs.pop('col', kwargs.pop('c', 0)))
            self._grid_opts['columnspan'] = kwargs.pop('columnspan',
                                            kwargs.pop('colspan', 1))
            self._grid_opts['rowspan'] = kwargs.pop('rowspan', 1)
            # ONLY IF ASKED. These were defaulted to 0 and always sent, which
            # made "asked for zero" and "said nothing" the same message — so
            # the page could not honour `ipadx=0` without also stripping the
            # stylesheet's padding off every gridded widget in the app. Left
            # absent, `_applyGrid` leaves the stylesheet in charge; sent as 0,
            # it means zero. (tkinter has no such ambiguity: its default IS
            # 0, and the stylesheet is what has no equivalent there.)
            for opt in ('padx', 'pady', 'ipadx', 'ipady'):
                if opt in kwargs:
                    self._grid_opts[opt] = kwargs.pop(opt)
            self._gridwait = kwargs.pop('gridwait', False)
        else:
            self._gridwait = kwargs.pop('gridwait', False)

        # DnD flags
        self.draggable = kwargs.pop('draggable', False)
        self.droppable = kwargs.pop('droppable', False)
        self.initial_widget = False

        # Store remaining props
        self._props = kwargs
        self._props.setdefault('text', '')

        # Create in JS
        self._create_in_js()

        # Do initial grid (mirrors Gridded.dogrid) — UNLESS THE CALLER SAID
        # WAIT. `gridwait=True` means "I will place this myself, later", and
        # ignoring it placed the widget immediately, against whatever the
        # page had at that moment — which for a row still being built is the
        # page itself. `sort_buttons.make_sgbf` sets it on every cycle
        # example precisely because `show_one()` decides which one is
        # placed; gridding them all on creation put the first one into the
        # layout before its row existed, which is the group button drawn
        # full-width across the top of the macrosort page with its own row
        # left empty (Kent, 2026-09-15, twice).
        #   tkinter's own comment on the kwarg says the same: it must not
        # reach child buttons "or they grid_remove themselves and never
        # restore" (sort_buttons.py:554).
        if self._has_grid and not self._gridwait:
            self._dogrid()

        # Set up DnD bindings after widget exists in JS
        if self.draggable:
            self.draggable_bindings()
        if self.draggable or self.droppable:
            self.dnd_bindings()

        # THE WINDOW NOW HOLDS MORE THAN IT DID. Every page in this app
        # builds its content after its window exists, so the load-time fit
        # measured an empty page and nothing measured it again — see
        # `_request_refit`. Asking here costs one coalesced request per
        # widget and gets every page, built or rebuilt, without a call in
        # any of them: a page cannot forget to ask.
        try:
            win = self._root_for_binding()
            if win is not None and win is not self:
                _request_refit(win, 'content built')
        except Exception as e:
            log.debug("could not ask for a refit ({!r})".format(e))

    def _create_in_js(self):
        wv = getattr(self, '_wv_window', None)
        parent_wid = self.parent._wid if self.parent else None
        spec = json.dumps({
            'wid': self._wid,
            'type': self._widget_type,
            'parent_wid': parent_wid,
            'props': {k: v for k, v in self._props.items()
                      if isinstance(v, (str, int, float, bool, type(None)))},
            'grid': self._grid_opts if self._has_grid else None,
            # Lets the page tell "parented to a window" (normal — the window
            # is the page) from "parent genuinely missing" (a real fault).
            'parent_is_window': bool(getattr(self.parent, 'is_window', False)),
        })
        # A WIDGET WHOSE PARENT WAS NOT IN THE PAGE says so in the log, not
        # only in a console nobody has open. See the `orphaned` event in
        # widgets.js: the page falls back to #root, so the widget appears in
        # the PAGE's grid rather than its frame's — full width at the top,
        # typically — and the row it belonged to is left empty.
        _api.register(self._wid, 'orphaned', self._report_orphaned)
        # WHY THE PARENT MIGHT NOT BE THERE, said at the moment of creation
        # rather than guessed at afterwards. The page can only report THAT a
        # parent was missing (see `_report_orphaned`); these two conditions
        # are visible only here, and they are the two things that can make a
        # parent unfindable in a page:
        #   * it was DESTROYED — `again()`/`refresh()` destroys a frame's
        #     children and rebuilds, so a widget created against one of them
        #     is building on something already gone;
        #   * it belongs to ANOTHER WINDOW — `_widgets` is per page while
        #     wids are global, so a parent from the previous run window
        #     cannot be found in this one. `clear_runwindow` retires a run
        #     window by HIDING it, so its widgets stay alive and referenced.
        # A THIRD CAUSE existed and neither of these could see it: the
        # parent's own `createWidget` was still sitting in a flush queue that
        # the page had already declared drained, so the parent was perfectly
        # healthy here and simply had not ARRIVED yet. That is fixed at the
        # gate (see `_js`); these two remain because they are real and are
        # invisible from the page side.
        if self.parent is not None and not getattr(self.parent, 'is_window',
                                                   False):
            if not getattr(self.parent, '_exists', True):
                log.error("widget {} ({}) is being created against parent {}, "
                          "WHICH HAS BEEN DESTROYED — it will land in the "
                          "page root. Text: {!r}".format(
                            self._wid, self._widget_type, parent_wid,
                            str(self._props.get('text', ''))[:40]))
            elif getattr(self.parent, '_wv_window', None) is not wv:
                log.error("widget {} ({}) is being created against parent {}, "
                          "WHICH BELONGS TO ANOTHER WINDOW — wids are global "
                          "but each page has its own map, so it cannot be "
                          "found here. Text: {!r}".format(
                            self._wid, self._widget_type, parent_wid,
                            str(self._props.get('text', ''))[:40]))
        _js(wv, f'createWidget({spec})')

    def _report_orphaned(self, data):
        log.error("widget {} ({}) was created with parent {} — which the page "
                  "does not have, so it was attached to #root and will lay "
                  "itself out against the PAGE instead of its frame. Text: "
                  "{!r}. This is a build-order fault. Look for a line above "
                  "naming the cause (destroyed parent, or a parent in "
                  "another window); if there is none, the parent was healthy "
                  "and had merely not been SENT yet — which the flush gates "
                  "in `_js` are supposed to make impossible."
                  "".format(self._wid, (data or {}).get('type'),
                            (data or {}).get('parent_wid'),
                            (data or {}).get('text')))

    def _drain_wv_js_queue(self):
        """Send this window's queued JS, THEN mark the window loaded.

        The per-window twin of `_flush_js_queue`, and for the same reason:
        `_wv_loaded` is the flag `_js` reads to decide "send now" versus
        "queue", so flipping it before the queue is empty lets a later call
        overtake an earlier one. Windows are where it BIT — a task builds its
        page from a worker thread while the window's `loaded` event runs on
        the UI thread, so the two genuinely interleave, and a child that
        overtakes its parent loses its parent (see `_js`).

        Only a pass that finds the queue empty sets the flag; the loop exists
        because the builder keeps adding while we send."""
        queue = getattr(self, '_wv_js_queue', None)
        if queue is None:
            return
        lock = getattr(self, '_wv_queue_lock', _js_queue_lock)
        passes = 0
        while True:
            with lock:
                if not queue:
                    self._wv_loaded.set()
                    return
                batch = list(queue)
                queue.clear()
            passes += 1
            if passes == 20:
                log.info("window {} JS queue still refilling after 20 passes "
                         "({} in this one)".format(self._wid, len(batch)))
            _eval_batched(getattr(self, '_wv_window', None), batch)

    def _dogrid(self):
        """Mirrors Gridded.dogrid: grid, grid_remove, then grid if not gridwait."""
        wv = getattr(self, '_wv_window', None)
        opts = json.dumps(self._grid_opts)
        _js(wv, f'gridWidget({self._wid}, {opts})')
        _js(wv, f'gridRemove({self._wid})')
        if self._gridwait:
            self._gridwait = False
            return
        _js(wv, f'gridWidget({self._wid}, {opts})')
        self._grid_visible = True

    def dogrid(self):
        """Public alias — matches ui_tkinter.Gridded.dogrid."""
        self.grid()

    # ── Grid methods ──────────────────────────────────────────────────
    # The app's short spellings, and what the page actually reads. The
    # CONSTRUCTOR normalises these (`colspan` → `columnspan`, `r` → `row`);
    # this method did not, so `.grid(colspan=2)` would store `colspan` and
    # `_applyGrid` — which reads `columnspan` — would silently ignore it.
    # Latent rather than live: every `.grid(...)` call site in the suite
    # passes `columnspan`. Normalised anyway, because a method that accepts
    # a kwarg and drops it is the shape this backend keeps getting wrong,
    # and tkinter's own `.grid()` would raise on `colspan` rather than
    # accept it quietly.
    _GRID_ALIASES = {'colspan': 'columnspan', 'col': 'column',
                     'c': 'column', 'r': 'row'}

    def grid(self, **kwargs):
        if kwargs:
            for alias, real in self._GRID_ALIASES.items():
                if alias in kwargs:
                    # `pop` inside the setdefault is what REMOVES the alias,
                    # so the option is translated rather than discarded and
                    # nothing is left for the page to ignore. (A second
                    # `kwargs.pop(alias, None)` stood here and was both
                    # redundant and — correctly —
                    # `test_no_unexplained_dropped_options`'s business: a pop
                    # with no reason reads as an oversight, which is the very
                    # class of bug this method was fixing.)
                    kwargs.setdefault(real, kwargs.pop(alias))
            self._grid_opts.update(kwargs)
            self._has_grid = True
        wv = getattr(self, '_wv_window', None)
        opts = json.dumps(self._grid_opts)
        _js(wv, f'gridWidget({self._wid}, {opts})')
        # `getattr`: the base sets `_grid_visible` in `__init__`, but the
        # grid-spans test drives this method on a bare stand-in, and a
        # widget that never said it was hidden is not being revealed.
        revealed = not getattr(self, '_grid_visible', True)
        self._grid_visible = True
        # SHOWING SOMETHING IS A SIZE CHANGE, like a tab switch. Refits are
        # asked for when a widget is CREATED (`_finish_creation`), and a page
        # that builds everything up front and reveals part of it later with
        # `grid()` creates nothing — so the window kept the size it had
        # before the territory frame appeared, and the frame sat below the
        # bottom edge (the new-language page, Kent, 2026-09-22: "content is
        # off the page"). Same class as the notebook's `_refit_for_tab`,
        # fixed 2026-09-16, and the same short delay: nothing is arriving in
        # a burst, and the user is looking at the cropped page now. Only on
        # a REVEAL (hidden → shown); a widget that is already showing has not
        # changed the page's size. `grid_remove` does not ask: shrinking a
        # window under the user is the flicker this item removed.
        if revealed:
            try:
                win = self._root_for_binding()
                if win is not None and win is not self:
                    _request_refit(win, 'widget shown', delay=0.05)
            except Exception as e:
                log.debug("could not ask for a refit on grid ({!r})".format(e))

    def grid_remove(self):
        wv = getattr(self, '_wv_window', None)
        _js(wv, f'gridRemove({self._wid})')
        self._grid_visible = False

    def grid_info(self):
        if self._has_grid:
            return dict(self._grid_opts)
        return {}

    def grid_size(self):
        """(columns, rows) actually occupied — SPANS INCLUDED.

        This counted `max(row) + 1` and ignored `rowspan`/`columnspan`
        entirely, so a frame holding one widget at row 0 with `rowspan=4`
        reported ONE row instead of four. tkinter's `grid_size` is Tk's own
        and includes the span extent, so the two backends disagreed about
        the shape of the same grid.

        `nrows()` is the consumer that makes this matter: it is how the app
        finds "the row after everything" — `sort_ui.py:705` grids the OK
        canary at `buttonframe.content.nrows()`, and a row number that is
        too small puts it ON TOP of existing content instead of below it.
        (Not the macrosort page's own bug: its group buttons are gridded
        without spans. Found by reading, on Kent's question about span
        handling across the backends, 2026-09-16.)"""
        max_col = max_row = 0
        for c in self._children:
            if not c._has_grid:
                continue
            opts = c._grid_opts

            def _span(key):
                try:
                    return max(1, int(opts.get(key, 1) or 1))
                except (TypeError, ValueError):
                    return 1

            max_row = max(max_row, opts.get('row', 0) + _span('rowspan'))
            max_col = max(max_col,
                          opts.get('column', 0) + _span('columnspan'))
        return (max_col, max_row)

    # Track options this backend understands; anything else is reported once.
    _TRACK_KEYS = ('weight', 'minsize')

    def grid_rowconfigure(self, index, **kwargs):
        """tkinter's row weights, as CSS Grid tracks.

        WAS A NO-OP, with the comment "CSS Grid handles this automatically".
        It does not, and the difference is the whole of tkinter's `weight`:
        CSS Grid's default track is CONTENT-SIZED, while `weight=1` means
        "this row takes the space left over". So every
        `grid_rowconfigure(..., weight=…)` in the app was accepted and
        discarded — the dropped-option class, with a comment asserting there
        was nothing to drop.

        WHAT IT COST, traced 2026-09-16 (Kent: "the double scroll sort
        page"). `sort_ui.py:666` weights row 1 so the word list fills the
        kiosk page. With that discarded the row was content-sized, so the
        scroller's `max-height: min(100%, 0.9 * screen)` could not resolve
        its `100%` term — a percentage against an indefinite height is not a
        constraint — and fell back to the screen-relative backstop. The
        scroller then took 90% of the SCREEN with the title and instructions
        stacked above it, which is taller than the window: the page scrolled
        AND the list scrolled inside it. Two scrollbars for one list.
        `grid.css` already said this was the intent — "when the row has a
        definite height the scroller fills it and scrolls only past that" —
        and the definite height was never arriving.

        `weight` becomes an `fr` track, `minsize` its floor. Rows past the
        highest one configured are left implicit, so `grid-auto-rows` still
        sizes them and configuring row 1 does not oblige us to know how many
        rows there will eventually be."""
        return self._track_configure('row', index, kwargs)

    def grid_columnconfigure(self, index, **kwargs):
        """Column weights. See `grid_rowconfigure`; same mechanism, same
        reason. Width was the less visible half — nothing here has a definite
        width problem of the scroller's kind — but the semantics are one
        thing and splitting them would be worse than either."""
        return self._track_configure('column', index, kwargs)

    def _track_configure(self, axis, index, kwargs):
        """Record one row/column configuration and re-send the template.

        RE-SENT WHOLE, not patched: `grid-template-rows` is one declaration
        listing every track up to the last, so there is nothing to patch.
        Cheap — a page configures a handful of tracks, once each.
        """
        try:
            index = int(index)
        except (TypeError, ValueError):
            return
        if index < 0:
            return
        store = '_tracks_' + axis
        tracks = getattr(self, store, None)
        if tracks is None:
            tracks = {}
            setattr(self, store, tracks)
        spec = dict(tracks.get(index) or {})
        changed = False
        for key in self._TRACK_KEYS:
            if key not in kwargs:
                continue
            try:
                value = int(kwargs[key] or 0)
            except (TypeError, ValueError):
                continue
            if spec.get(key) != value:
                spec[key] = value
                changed = True
        for key in kwargs:
            if key not in self._TRACK_KEYS:
                # SAID, not silently dropped — this method is in this state
                # because the last thing it dropped was never mentioned.
                # `pad` and `uniform` have no CSS Grid equivalent worth
                # faking; nothing in the app asks for either today.
                _say_once("grid {}configure({}) is not supported in the "
                          "webview backend and is being ignored (weight and "
                          "minsize are)".format(axis, key))
        if not changed:
            return
        tracks[index] = spec
        self._send_grid_tracks()

    def _send_grid_tracks(self):
        wv = getattr(self, '_wv_window', None)
        if wv is None:
            return
        _js(wv, 'setGridTracks({}, {}, {})'.format(
                self._wid,
                json.dumps(getattr(self, '_tracks_row', None) or {}),
                json.dumps(getattr(self, '_tracks_column', None) or {})))

    # THE SHORT SPELLINGS ARE THE SAME CALL. tkinter accepts both
    # `columnconfigure` and `grid_columnconfigure`, the app uses both, and
    # only the long ones existed here — so every call site using the short
    # form raised AttributeError, inside a callback where `on_event` logs and
    # carries on. Found by the backend-parity audit (2026-09-11) rather than
    # by a user, which is the point of the audit.
    def rowconfigure(self, index, **kwargs):
        return self.grid_rowconfigure(index, **kwargs)

    def columnconfigure(self, index, **kwargs):
        return self.grid_columnconfigure(index, **kwargs)

    def grid_forget(self):
        """Hide without destroying — tkinter's other name for grid_remove."""
        return self.grid_remove()

    def winfo_ismapped(self):
        """Is this on screen? Logged three times a run as a failure before
        this existed ("status window width probe failed"), each time making
        the caller give up on measuring a width it could have had."""
        return bool(self.winfo_viewable())

    def workarea(self):
        """The USABLE screen — (width, height).

        tkinter asks the window manager via `wm_maxsize()` because the raw
        screen includes the taskbar, and a window that overflows the bottom
        on Windows cannot be dragged back into reach. A page cannot ask the
        WM anything, but the browser already distinguishes the two:
        `screen.availWidth/availHeight` exclude system chrome, and
        `fit_to_content` has been using them all along.

        Callers treat a wrong answer as a layout mistake, not a crash, so an
        unreachable page falls back to the full screen rather than raising.
        """
        wv = getattr(self, '_wv_window', None)
        try:
            got = _js(wv, '[screen.availWidth, screen.availHeight]')
            if got and len(got) == 2 and all(int(n) > 0 for n in got):
                return (int(got[0]), int(got[1]))
        except Exception as e:
            log.debug("workarea: falling back to the full screen ({})".format(e))
        return (self.winfo_screenwidth(), self.winfo_screenheight())

    def winfo_pointerxy(self):
        """Where the pointer is. There is no way to ask a page this without
        a round trip, and every caller uses it to place something — so the
        honest answer is (0, 0) and the caller's own fallback, not a lie
        about the cursor."""
        return (0, 0)

    def grab_release(self):
        """Accepted and ignored. Tk grabs the pointer for a posted menu and
        releases it here; a browser has no grab to release, and
        `Menu.tk_popup` already dismisses on an outside click."""
        pass

    # ── Configure ─────────────────────────────────────────────────────
    def configure(self, **kwargs):
        # A CALLABLE IS NOT SERIALISABLE, so `command` fell through the loop
        # below and was silently discarded — `configure(command=…)` did
        # nothing at all. `StatusFrame.activate_cell` uses it to make the
        # current cell inert (`command=donothing`) and `deactivate_cell` to
        # give its click back, so both halves were no-ops and the current
        # cell stayed clickable. Handled before the loop, and NOT passed to
        # the page: the page knows the widget by id and calls back through
        # `_api`, so rebinding is entirely this side's business.
        if 'command' in kwargs or 'cmd' in kwargs:
            self.command = kwargs.pop('command', None) or kwargs.pop('cmd',
                                                                     None)
            rebuild = getattr(self, '_build_command', None)
            if callable(rebuild):
                try:
                    rebuild()
                except Exception as e:
                    log.info("widget {}: could not rebind its command ({!r})"
                             "".format(self._wid, e))
        # A MENU BAR IS NOT A PROPERTY. `ui_shell._setmenus` does
        # `self.config(menu=self.menubar)`, and a `Menus` object is not a
        # str/int/float/bool, so it fell past the loop below into `_config`
        # and nothing reached the page — "Show Menus" logged that it had
        # shown menus and did nothing (Kent, 2026-09-24). `menu=None` takes
        # the bar down again, which is what `_removemenus` needs.
        if 'menu' in kwargs:
            self._set_menubar(kwargs.pop('menu'))
        self._config.update(kwargs)
        wv = getattr(self, '_wv_window', None)
        for k, v in kwargs.items():
            if isinstance(v, (str, int, float, bool)):
                _js(wv, f'updateProp({self._wid}, {json.dumps(k)}, {json.dumps(v)})')

    def _set_menubar(self, menu):
        """Draw `menu` as a bar across the top of this window, or clear it.

        AN ELEMENT IN THE PAGE, not a native menu — the same decision as
        `Popup`, and for the same reasons: pywebview's own menu is set once,
        globally, at `start()`, while this app rebuilds its menus per task and
        on every `setcontext()`; and everything else in the port is HTML."""
        wv = getattr(self, '_wv_window', None)
        bar_id = getattr(self, '_menubar_wid', None)
        if bar_id is None:
            bar_id = self._menubar_wid = _next_wid()
        if menu is None or not getattr(menu, '_items', None):
            _api.unregister(bar_id)
            _js(wv, 'setMenubar({}, null)'.format(bar_id))
            self._menubar = None
            return
        self._menubar = menu

        def on_menubar(data):
            cmd = menu.command_at(data.get('path') or [])
            if callable(cmd):
                try:
                    cmd()
                except Exception:
                    import traceback
                    log.error("menu bar command failed:\n%s",
                              traceback.format_exc())
            else:
                log.info("menu bar: nothing to run at path %r",
                         data.get('path'))
        _api.unregister(bar_id)
        _api.register(bar_id, 'menubarclick', on_menubar)
        _js(wv, 'setMenubar({}, {})'.format(bar_id,
                                            json.dumps(menu.spec())))

    def config(self, **kwargs):
        return self.configure(**kwargs)

    def __setitem__(self, key, value):
        self.configure(**{key: value})

    # Options whose value Tk ALWAYS has, because they come from the widget's
    # own defaults and the theme rather than from the caller. Read back from
    # the theme when nobody set them explicitly — see `__getitem__`.
    _THEME_OPTIONS = ('background', 'bg', 'activebackground', 'foreground',
                      'fg', 'highlightbackground', 'highlightcolor',
                      'selectcolor', 'troughcolor', 'menubackground')

    def __getitem__(self, key):
        """tkinter's option read — WITH THE THEME BEHIND IT.

        Tk keeps every option for every widget, so `cell['activebackground']`
        answers with a real colour even on a widget created without one. Ours
        knew only what a caller had passed, and answered `''`. That is not a
        cosmetic difference: the app READS an option, then WRITES it back.
        `StatusFrame.activate_cell` is exactly that —

            cell.inactive_background = cell['background']
            cell.configure(background=cell['activebackground'])

        — so it read `''`, wrote `background: ''`, and the current-cell
        marker on the progress board silently did nothing. Kent, 2026-09-17,
        of the board's three markers: "this is already done, just not
        showing." It was done, and backend-neutral; the read underneath it
        was not.

        Only the options a THEME defines, and only when unset: anything else
        keeps answering `''` rather than inventing a value."""
        # `command` LIVES ON THE WIDGET, not in the props: Button pops it in
        # `__init__`. Reading it is half of a store-and-restore pair —
        # `activate_cell` keeps `cell['command']`, sets `donothing`, and
        # `deactivate_cell` puts the original back — so answering `''` here
        # does not merely fail to report: it makes the restore install
        # nothing and leaves the cell permanently inert.
        if key in ('command', 'cmd'):
            return getattr(self, 'command', '') or ''
        if key in self._config:
            return self._config[key]
        if key in self._props:
            return self._props[key]
        if key in self._THEME_OPTIONS:
            theme = getattr(self, 'theme', None)
            if theme is not None:
                name = {'bg': 'background', 'fg': 'foreground'}.get(key, key)
                value = getattr(theme, name, None)
                if value:
                    return value
        return ''

    def keys(self):
        return list(set(list(self._config.keys()) + list(self._props.keys())))

    # ── Lifecycle ─────────────────────────────────────────────────────
    def destroy(self):
        if not self._exists:
            return
        self._exists = False
        for child in list(self._children):
            child.destroy()
        if self.parent and self in self.parent._children:
            self.parent._children.remove(self)
        _api.unregister(self._wid)
        wv = getattr(self, '_wv_window', None)
        _js(wv, f'destroyWidget({self._wid})')
        # Anything blocked in wait_window() on this widget is now free. Last,
        # so a released waiter sees the widget already gone.
        _release_waiters(self._wid, 'destroyed')

    def cget(self, key):
        """tkinter's option reader. Missing entirely, which is what
        "DIAG-chooser-xpad failed: 'Button' object has no attribute 'cget'"
        was — the chooser's own wrap/xpad diagnostic asking a button for its
        configured values. Reads back what was set, so a caller sees what it
        put in rather than a guess at what the browser computed."""
        if key in self._config:
            return self._config[key]
        return self._props.get(key, '')

    def wait_window(self, widget=None, window=None):
        """Block until *widget* is destroyed — or self, if none is given.

        BOTH KEYWORD NAMES, because both are used. tkinter's is `window`
        (it is `Misc.wait_window(self, window=None)`), and this took only
        `widget` — so `presenttosort`'s `wait_window(window=self.sortitem)`
        raised TypeError, the sort loop caught it as "sort item gone",
        continued, and ran through every word without ever waiting. The page
        then sat there with no word presented and told the user they were
        not done (Kent's log, 2026-09-15) — which is what "presentation
        missing" was, for four screenshots.
          A signature that differs by a parameter NAME is the hardest kind
        of port gap to see: the call site reads correctly, the method
        exists, and the failure surfaces as a caught exception three frames
        away.

        ON THE BASE CLASS because tkinter puts it on Misc, so ANY widget has
        it. It was implemented only on Toplevel, and `ui_shell.py:2485` does
        `buttonFrame1.wait_window(window)` on a ScrollingButtonFrame — one of
        the canary-idiom sites — which raised AttributeError mid-settings.

        The argument matters: ~30 sites pass a canary WIDGET rather than a
        window, because that widget's destruction is the signal. Returns at
        once if the target is already gone, which is the other half of the
        deadlock."""
        target = widget if widget is not None else (
                    window if window is not None else self)
        wid = getattr(target, '_wid', None)
        if wid is None:
            log.info("wait_window given {!r}, which has no widget id; not "
                     "waiting".format(type(target).__name__))
            return
        if not getattr(target, '_exists', True):
            return
        # NEVER PARK IN A WINDOW THAT HAS ALREADY QUIT. `on_quit` releases
        # the waits below it, but only for waits that exist WHEN it runs —
        # a flow that reaches here afterwards would park on a fresh Event
        # that nothing will ever set, which is the same hang one turn later.
        # Cheap, and it makes the release in `on_quit` a fix rather than a
        # race. See `_release_waiters_below`.
        gone = _quit_window_over(target) or _quit_window_over(self)
        if gone is not None:
            log.info("widget {}: NOT waiting on widget {} — window {} has "
                     "already quit".format(self._wid, wid, gone))
            return
        log.info("widget {}: waiting on widget {}".format(self._wid, wid))
        _waiter_for(wid).wait()
        log.info("widget {}: wait on widget {} released".format(self._wid, wid))

    def _wait_host(self):
        """This window hosts its own wait, as far as the base knows.

        Declared here for the same reason as `_hide_page_wait` below:
        `waitdone` exists on both `Toplevel` and `Root`, and both must be
        able to ask without knowing whether hand-over applies to them.
        `Toplevel` overrides it."""
        return self

    def _hide_page_wait(self):
        """No page wait here. `Toplevel` overrides this with the real one.

        Declared on the base because `waitdone` is duplicated on both
        `Toplevel` and `Root` (this file duplicates the whole Waitable set),
        and both must be able to clear a cover without knowing whether they
        can have one. A window with no `outsideframe` — the root, a bare
        Toplevel — never shows one, so this is the honest answer rather than
        a guard at each call site."""
        return

    def winfo_exists(self):
        return self._exists

    def winfo_children(self):
        return list(self._children)

    # ── Tk names for the same two facts ───────────────────────────────
    # Every widget in tkinter has `master` (its parent) and `_root()` (the
    # interpreter's root window), and app code uses both on ordinary
    # widgets. Missing here, they surfaced as caught exceptions that read
    # like app bugs rather than port gaps (Kent's log, 2026-09-15):
    #
    #   SortButtonFrame scroll reflow re-arm failed:
    #       'Frame' object has no attribute 'master'
    #   context menu aqua bind skipped: 'Label' object has no attribute '_root'
    #
    # Both were swallowed by their callers' try/except, so the page built
    # WITHOUT its scroll re-arm and WITHOUT its right-click menu, and said
    # so in a line that named the symptom and not the cause.
    @property
    def master(self):
        return self.parent

    # ── ScrollingFrame internals, on EVERY widget ─────────────────────
    # `SortButtonFrame`'s re-arm calls `_configure_interior` on whatever it
    # is scrolling inside, and that is a plain Frame as often as a
    # ScrollingFrame — "'Frame' object has no attribute '_configure_interior'"
    # persisted after I put these on ScrollingFrame alone (Kent, 2026-09-15).
    # Nothing to do in either place: `overflow:auto` needs no scrollregion
    # recomputed. On the base class so no caller has to know which kind of
    # frame it holds.
    def _configure_interior(self, event=None):
        pass

    def _do_configure_interior(self, event=None):
        pass

    def _configure_canvas(self, event=None):
        pass

    def _root(self):
        """The window this widget belongs to (tkinter's Misc._root())."""
        return self._find_root() or self._root_for_binding() or self

    # ── `tk.call('tk','windowingsystem')` ─────────────────────────────
    # The one Tcl call app code makes directly, and it asks something this
    # backend can answer honestly: `sort_ui.py:216` needs to know whether it
    # is on macOS, because Aqua has no Button-3 and the context menu must
    # hang off Control-Button-1 instead. With no `tk` to ask, the probe
    # raised and the extra binding was skipped — "context menu aqua bind
    # skipped: 'Root' object has no attribute 'tk'" — which on a Mac means
    # no right-click menu anywhere in the app.
    #   It answers ONLY that, and raises otherwise: a shim that returned
    # None for every Tcl call would turn each future Tcl-shaped question
    # into a wrong answer instead of a visible error.
    class _TkShim:
        def call(self, *args):
            if list(args[:2]) == ['tk', 'windowingsystem']:
                return {'darwin': 'aqua', 'win32': 'win32'}.get(
                            sys.platform, 'x11')
            raise NotImplementedError(
                "this backend has no Tcl interpreter; tk.call{!r} has no "
                "webview equivalent — ask it a different way".format(args))

    @property
    def tk(self):
        return _WebviewWidget._TkShim()

    def _find_root(self):
        node = self
        seen = 0
        while node is not None and seen < 50:
            if getattr(node, 'parent', None) is None:
                return node
            node = node.parent
            seen += 1
        return None

    # ── Geometry queries (best-effort from JS) ────────────────────────
    def _get_rect(self):
        wv = getattr(self, '_wv_window', None)
        r = _js(wv, f'getWidgetRect({self._wid})')
        if isinstance(r, dict):
            return r
        return {'x': 0, 'y': 0, 'width': 0, 'height': 0}

    def winfo_screenwidth(self):
        wv = getattr(self, '_wv_window', None)
        return _js(wv, 'screen.width') or 1920

    def winfo_screenheight(self):
        wv = getattr(self, '_wv_window', None)
        return _js(wv, 'screen.height') or 1080

    def winfo_reqwidth(self):
        return self._get_rect().get('width', 0)

    def winfo_reqheight(self):
        return self._get_rect().get('height', 0)

    def winfo_width(self):
        return self._get_rect().get('width', 0)

    def winfo_height(self):
        return self._get_rect().get('height', 0)

    def winfo_x(self):
        return self._get_rect().get('x', 0)

    def winfo_y(self):
        return self._get_rect().get('y', 0)

    def winfo_rootx(self):
        return self.winfo_x()

    def winfo_rooty(self):
        return self.winfo_y()

    def winfo_viewable(self):
        return self._exists and self._grid_visible

    def winfo_toplevel(self):
        w = self
        while w.parent is not None:
            w = w.parent
        return w

    def winfo_class(self):
        return self.__class__.__name__

    # ── Events ────────────────────────────────────────────────────────
    def bind(self, event, handler, add=None):
        self._bindings.setdefault(event, [])
        if not add:
            self._bindings[event] = []
        self._bindings[event].append(handler)
        _api.register(self._wid, event, lambda data, h=handler: h(type('Event', (), data)()))
        wv = getattr(self, '_wv_window', None)
        _js(wv, f'bindEvent({self._wid}, {json.dumps(event)})')

    def unbind(self, event, funcid=None):
        self._bindings.pop(event, None)
        _api.unregister(self._wid, event)

    # ── bind_all belongs on EVERY widget, not just windows ────────────────
    # In tkinter `bind_all` is on Misc, so any widget can make an
    # APPLICATION-WIDE binding, and code does: `dowordframe` binds the
    # navigation keys off the Next button — `next.bind_all('<Up>', …)`
    # (lexicon.py:1345) — which is idiomatic and was raising
    # `'Button' object has no attribute 'bind_all'` here (Kent 2026-09-10).
    #   The cost was not a missing key binding. It raised in the MIDDLE of
    # dowordframe, after the widgets were built and before `getword`
    # populated them, so the page appeared with Back/Next and an empty field
    # and no word, glosses or picture at all — a plausible-looking page with
    # nothing on it.
    #   NINTH gap of this shape (takekioskscreen, after_idle, cget,
    # wait_window, lift, EntryField.delete/insert/focus_set, textvariable,
    # Button-3). It arrived through `on_event` again, which is why it showed
    # as a broken page rather than a crash.
    #
    # Routed to the ROOT, which is what "all" means: bindEvent falls back to
    # `document` for a window, so events from any widget reach it — matching
    # tkinter, where bind_all is answered by the application, not the widget
    # it was called on.
    def bind_all(self, event, handler, add=None):
        root = self._root_for_binding()
        if root is not None and root is not self:
            return root.bind(event, handler, add=add)
        return self.bind(event, handler, add=add)

    def unbind_all(self, event=None):
        root = self._root_for_binding()
        if root is not None and root is not self:
            return root.unbind(event)
        return self.unbind(event)

    def _root_for_binding(self):
        """The nearest enclosing window. Walks `parent` rather than using
        `default_root()`: a binding made from a widget in a task window
        belongs to THAT window's page, not to whichever root happens to be
        default."""
        node = self
        seen = 0
        while node is not None and seen < 50:   # cycle guard
            if getattr(node, 'is_window', False):
                return node
            node = getattr(node, 'parent', None)
            seen += 1
        return None

    def update_idletasks(self):
        pass  # Browser handles layout automatically

    def update(self):
        pass

    def after(self, ms, func=None):
        if func:
            t = threading.Timer(ms / 1000.0, func)
            t.daemon = True
            t.start()
            return t
        else:
            import time
            time.sleep(ms / 1000.0)

    def after_cancel(self, timer_id):
        if isinstance(timer_id, threading.Timer):
            timer_id.cancel()

    def after_idle(self, func=None, *args):
        """tkinter's "run when the event loop is next idle".

        There is no idle queue here to join from Python, and calling *func*
        inline would change ordering at every call site, so this is after(0):
        a timer that fires as soon as the interpreter reaches it. Missing
        entirely until now — `status_window` logged
        "could not schedule board reflow: 'StatusFrame' object has no
        attribute 'after_idle'" and simply skipped the reflow."""
        if func is None:
            return None
        return self.after(0, lambda: func(*args))

    def focus_set(self):
        # THROUGH focusWidget, not a bare `.focus()`. Two widgets here are
        # WRAPPERS around the thing that actually takes the keyboard — the
        # editable combobox is a <span> holding an <input> — and a span is
        # not focusable, so this silently did nothing for them. `EntryField`
        # already called focusWidget; everything else got the bare form and
        # the difference was invisible until a wrapper needed it.
        wv = getattr(self, '_wv_window', None)
        _js(wv, f'focusWidget({self._wid})')

    def focus_get(self):
        return None  # Simplified

    def bindchildren(self, bind, command):
        self.bind(bind, command)
        for child in self._children:
            try:
                child.bindchildren(bind, command)
            except Exception:
                pass

    # ── Drag and drop ─────────────────────────────────────────────────
    def draggable_bindings(self):
        wv = getattr(self, '_wv_window', None)
        _js(wv, f'makeDraggable({self._wid})')
        _api.register(self._wid, 'dnd_start', lambda d: self._on_dnd_start(d))
        _api.register(self._wid, 'dnd_end', lambda d: self._on_dnd_end(d))

    def dnd_bindings(self):
        self.initial_widget = False
        if self.droppable:
            wv = getattr(self, '_wv_window', None)
            _js(wv, f'makeDroppable({self._wid})')
            _api.register(self._wid, 'dnd_commit', lambda d: self._on_dnd_commit(d))
            _api.register(self._wid, 'dnd_enter', lambda d: self.dnd_focus_on())
            _api.register(self._wid, 'dnd_leave', lambda d: self.dnd_focus_off())

    def _on_dnd_start(self, data):
        self.initial_widget = True
        self.dnd_focus_on()

    def _on_dnd_end(self, data):
        """The SOURCE's end-of-drag call, which tkinter makes and this did not.

        `Gridded.dnd_end(target, event)` is the documented source-side hook —
        `ui_tkinter` calls it from tkinter.dnd with the target it landed on,
        and `testapp` shows a DragLabel overriding it to read the target's
        text. Here the page's `dragend` was answered by doing the cleanup
        inline, so any override was dead code: a caller could implement
        dnd_end, see it work under tkinter, and get silence under webview.

        The page cannot say what it landed on — `dragend` carries no target —
        but the `drop` event fires on the target FIRST, so the last commit is
        the answer, and it is cleared on the way out so a drag that lands on
        nothing reports None (which is what tkinter passes then too).
        """
        global _dnd_last_target
        target, _dnd_last_target = _dnd_last_target, None
        self.initial_widget = False
        self.dnd_end(target, data)

    def _on_dnd_commit(self, data):
        """Called on the DROP TARGET when a draggable is dropped on it."""
        global _dnd_last_target
        source_wid = data.get('source_wid')
        # Find the source widget by wid
        source = self._find_widget_by_wid(source_wid)
        if source:
            _dnd_last_target = self
            self.dnd_commit(source, data)

    def _find_widget_by_wid(self, wid):
        """Walk up to root, then search all descendants for matching _wid."""
        root = self
        while root.parent is not None:
            root = root.parent
        return self._search_children(root, wid)

    @staticmethod
    def _search_children(widget, wid):
        if widget._wid == wid:
            return widget
        for child in widget._children:
            found = _WebviewWidget._search_children(child, wid)
            if found:
                return found
        return None

    def dnd_commit(self, source, event):
        """Override in subclasses to handle drop. Default: putback."""
        try:
            super().dnd_commit(source, event)
        except (AttributeError, TypeError):
            pass

    def dnd_accept(self, source, event):
        if self.droppable:
            return self

    def dnd_focus_on(self, event=None):
        if hasattr(self, 'theme'):
            self.configure(background=self.theme.activebackground)

    def dnd_focus_off(self, event=None):
        if hasattr(self, 'theme'):
            self.configure(background=self.theme.background)

    def dnd_enter(self, source, event):
        self.dnd_focus_on()

    def dnd_leave(self, source, event):
        if not self.initial_widget:
            self.dnd_focus_off()

    def dnd_end(self, target, event):
        self.initial_widget = False
        if target and hasattr(target, 'dnd_focus_off'):
            target.dnd_focus_off()
        self.dnd_focus_off()

    def dnd_putback(self, target, event):
        self.grid()

    # ── Inherited attrs (mirroring Childof.inherit) ───────────────────
    def inherit(self, parent=None, attr=None):
        if not parent and hasattr(self, 'parent') and self.parent:
            parent = self.parent
        if not parent:
            return
        attrs = [attr] if attr else ['theme', 'wraplength', 'renderer', 'exitFlag']
        for a in attrs:
            if hasattr(parent, a):
                setattr(self, a, getattr(parent, a))

    def is_descendant_of(self, w):
        p = self.parent
        while p is not None:
            if p is w:
                return True
            p = p.parent
        return False

    # ── availablexy (from Gridded) ────────────────────────────────────
    def availablexy(self):
        self.maxwidth = self.winfo_screenwidth() - 100
        self.maxheight = self.winfo_screenheight() - 150


# ── Theme ─────────────────────────────────────────────────────────────
class _FontInfo:
    """Lightweight stand-in for tkinter.font.Font — stores font metadata
    so code that does font['family'], font['size'] etc. still works."""
    def __init__(self, family='Charis SIL', size=18, weight='normal',
                 slant='roman', underline=0, overstrike=0):
        self._data = {
            'family': family, 'size': size, 'weight': weight,
            'slant': slant, 'underline': underline, 'overstrike': overstrike,
        }
    def __getitem__(self, key):
        return self._data.get(key)
    def actual(self):
        return dict(self._data)
    def __str__(self):
        return str(self._data)
    def cget(self, key):
        return self._data.get(key)
    def configure(self, **kw):
        self._data.update(kw)

class Theme:
    # THE APP'S list and themes, from frontend/theme_data.py — which imports
    # nothing, so this does not drag tkinter in. The comment that used to sit
    # here said "Same imagelist as ui_tkinter.Theme"; it was not. 35 of 81
    # entries were missing, including `record` (the record button's icon),
    # every sort-board verb image and both alphabet-task icons — and a name
    # absent from the list resolves to None, which draws nothing and logs
    # nothing. `Kim`, Kent's own theme, was likewise absent from the four
    # themes copied here, and an unknown name fell back to greygreen in
    # silence. See agenda/webview_imagelist_stale_copy.md.
    imagelist = theme_data.IMAGELIST
    themes = theme_data.THEMES

    _imagelist_was_here = [
        ('transparent','AZT stacks6.png'), ('tall','AZT clear stacks tall.png'),
        ('small','AZT stacks6_sm.png'), ('icon','AZT stacks6_icon.png'),
        ('icontall','AZT clear stacks tall_icon.png'),
        ('iconT','T alone clear6_icon.png'), ('iconC','Z alone clear6_icon.png'),
        ('iconV','A alone clear6_icon.png'), ('iconCV','ZA alone clear6_icon.png'),
        ('iconWord','ZAZA clear stacks6_icon.png'),
        ('iconWordRec','ZAZA Rclear stacks6_icon.png'),
        ('iconTRec','T Rclear stacks6_icon.png'),
        ('iconReport','Report_icon.png'),
        ('iconReportLogo','Generic AZT Reports_icon.png'),
        ('iconTRep','T Report_icon.png'), ('iconCVRep','ZA Report_icon.png'),
        ('iconTranscribe','Transcribe Tone_icon.png'),
        ('iconTranscribeC','Consonant Choice_icon.png'),
        ('iconTranscribeV','Vowel Choice_icon.png'),
        ('iconJoinUF','Join Tone_icon.png'),
        ('iconTRepcomp','T Report Comprehensive_icon.png'),
        ('iconVRepcomp','A Report Comprehensive_icon.png'),
        ('iconCRepcomp','Z Report Comprehensive_icon.png'),
        ('iconCVRepcomp','ZA Report Comprehensive_icon.png'),
        ('iconVCCVRepcomp','AZZA Report Comprehensive_icon.png'),
        ('USBdrive','USB drive.png'),
        ('T','T alone clear6.png'), ('C','Z alone clear6.png'),
        ('V','A alone clear6.png'), ('S','ZA alone clear6.png'), #syllable-profile (cvt 'S'); was 'CV'
        ('Word','ZAZA clear stacks6.png'), ('WordRec','ZAZA Rclear stacks6.png'),
        ('TRec','T Rclear stacks6.png'),
        ('Report','Report.png'), ('ReportLogo','Generic AZT Reports.png'),
        ('TRep','T Report.png'), ('CVRep','ZA Report.png'),
        ('Transcribe','Transcribe Tone.png'),
        ('TranscribeC','Consonant Choice.png'),
        ('TranscribeV','Vowel Choice.png'),
        ('JoinUF','Join Tone.png'),
        ('checkedbox','checked.png'), ('uncheckedbox','unchecked.png'),
        ('checkedbox_sm','checked_sm.png'), ('uncheckedbox_sm','unchecked_sm.png'),
        ('NoImage','toselect/Image-Not-Found.png'),
    ]

    # RENAMED, not deleted, so a reviewer can see it was a four-entry subset
    # of a fifteen-entry dict. It sat AFTER the real assignment above and so
    # would have silently won. Delete after one release.
    _themes_was_here = {
        'greygreen': {
            'background': '#8cd9bf', 'activebackground': '#66ccaa',
            'offwhite': '#ecf9f4', 'highlight': 'red',
            'menubackground': 'white', 'white': 'white'},
        'highcontrast': {
            'background': 'white', 'activebackground': '#e6fff9',
            'offwhite': '#ecf9f4', 'highlight': 'red',
            'menubackground': 'white', 'white': 'white'},
        'pink': {
            'background': '#ff99cc', 'activebackground': '#ff66b3',
            'offwhite': None, 'highlight': 'red',
            'menubackground': 'white', 'white': 'white'},
        'lightgreygreen': {
            'background': '#9fdfca', 'activebackground': '#8cd9bf',
            'offwhite': '#ecf9f4', 'highlight': 'red',
            'menubackground': 'white', 'white': 'white'},
    }

    def __init__(self, program, **kwargs):
        self.program = program
        # READ THE NAME BEFORE OVERWRITING IT. `App.check_for_theme`
        # (main.py:1528) puts the chosen theme's NAME on `program.theme` as a
        # STRING, and the next line replaces that string with this object —
        # so the name has to be taken first. ui_tkinter.Theme does exactly
        # this (:689-699) and is where the contract actually lives.
        #   What was here read `program.theme_name`, an attribute NOTHING in
        # the codebase sets: it appears twice, both in this file. So the
        # webview backend never learned the user's theme and silently used
        # greygreen — and the fallback could not warn, because 'greygreen' is
        # a perfectly valid theme name.
        #   Kent, 2026-09-11, after the missing-themes fix: "still says Kim on
        # my machine without my Kim theme visible (qt and gtk)". Two faults in
        # one line, and fixing the dictionary only removed the first: the
        # theme was ALSO absent from the copy, so this would have failed even
        # with the name arriving.
        chosen = getattr(program, 'theme', None)
        if not isinstance(chosen, str):
            chosen = getattr(program, 'theme_name', None)
        self.program.theme = self
        noimagescaling = kwargs.get('noimagescaling', False)

        # Scale — use devicePixelRatio later; for now default to 1.0
        self.scale = getattr(program, 'scale', None) or 1.0
        scale = self.scale

        # Pick theme
        self.name = chosen if isinstance(chosen, str) \
                    else theme_data.DEFAULT_THEME
        if self.name not in self.themes:
            # SAY SO. This fell back in silence, so a theme the webview
            # backend did not define looked like a theme that did not work:
            # the log said "Using theme Kim" and the screen was greygreen
            # (Kent, 2026-09-11). Now that both backends read one dict this
            # should be unreachable, which is exactly why it must be loud if
            # it ever fires again.
            log.warning("theme %r is not defined (%d themes known); using %r "
                        "instead", self.name, len(self.themes),
                        theme_data.DEFAULT_THEME)
            self.name = theme_data.DEFAULT_THEME
        for k, v in self.themes[self.name].items():
            setattr(self, k, v)
        # NAMED, NOT DESCRIBED. "is it peach or green" is not a question this
        # project's user can answer — Kent is colourblind, and asking him to
        # judge a hue was a useless check to hand him (2026-09-11: "except for
        # peach, whatever you think that means"). The theme APPLIED is a fact
        # the program knows, so it says it, and mismatch with the theme CHOSEN
        # becomes readable rather than visual.
        log.info("theme in use: %r (asked for %r)", self.name, chosen)

        # Pads
        self.padx = kwargs.get('padx', 5)
        self.pady = kwargs.get('pady', 5)
        self.ipadx = kwargs.get('ipadx', 2)
        self.ipady = kwargs.get('ipady', 2)

        self._build_fonts(scale)

        # Images
        self.photo = {}
        self.image_cache = {}
        if not noimagescaling:
            self._load_images(scale)

    def setscale(self, scale=None, window=None):
        """Change the UI scale and push it to the page.

        NOT from devicePixelRatio, and that is a measured decision rather than
        an omission. `devicePixelRatio` reports DEVICE pixels per CSS pixel and
        says nothing about physical size: on the Linux dev box it reads 1.0
        while a real ruler against the page shows CSS inches running about ¾ of
        an inch (2026-09-04, tests/manual/tone_feature_check). Trusting it there
        renders everything at 75 % — the same under-scaling as
        agenda/ui_scaling_dpi_and_real_estate.md, arriving through a different
        API. On Windows it does track the OS 'Scale and layout' setting, so it
        is a reasonable input THERE and useless here.

        So the scale comes from the caller (program.scale, the same dpi/96
        model ui_tkinter.Theme.setscale was rewritten to in 1.14.2), and the
        CSS variable does the work: every font class is
        calc(<base>px * var(--scale))."""
        if scale is None:
            scale = getattr(self.program, 'scale', None) or 1.0
        self.scale = scale = float(scale)
        self._build_fonts(scale)
        if window is None:
            window = getattr(_app_root, '_wv_window', None)
        _js(window, 'document.documentElement.style.setProperty("--scale", {})'
                    ''.format(json.dumps(str(scale))))
        return scale

    def setfonts(self, fonttheme='default'):
        """Rebuild the font table. `ui_shell.py:2198,2204` call this to switch
        between the normal set and `fonttheme='smaller'`, and it did not exist
        here — so the "show more on screen" path did nothing under webview.

        The size arithmetic lives in `_build_fonts`; this is the name the app
        uses, plus the one option it passes. `smaller` is three-quarters
        throughout rather than a second hand-tuned table, so the ratios that
        `webview_html/theme.css` mirrors stay the ratios here.
        """
        scale = self.scale * (0.75 if fonttheme == 'smaller' else 1.0)
        self._build_fonts(scale)
        log.info("fonts rebuilt for %r theme at scale %.2f", fonttheme, scale)

    def _build_fonts(self, scale):
        """Font sizes, kept in ONE place because webview_html/theme.css
        mirrors this arithmetic and the two had drifted — the stylesheet said
        12/24/18/12/10/8 while this said 18/36/30/24/12/9. The CSS holds the
        UNSCALED bases and multiplies by --scale, so these two agree only if
        the ratios below are the ratios there."""
        default_size = int(18 * scale)
        title_size = int(default_size * 2)
        big_size = int(default_size * 5 / 3)
        normal_size = int(default_size * 4 / 3)
        small_size = int(default_size * 2 / 3)
        tiny_size = int(default_size / 2)
        charis = 'Charis SIL'
        self.fonts = {
            'title': _FontInfo(family=charis, size=title_size),
            'instructions': _FontInfo(family=charis, size=normal_size),
            'normal': _FontInfo(family=charis, size=normal_size),
            'report': _FontInfo(family=charis, size=small_size),
            'reportheader': _FontInfo(family=charis, size=small_size, slant='italic'),
            'read': _FontInfo(family=charis, size=big_size),
            'readbig': _FontInfo(family=charis, size=title_size, weight='bold'),
            'small': _FontInfo(family=charis, size=small_size),
            'tiny': _FontInfo(family=charis, size=tiny_size),
            'default': _FontInfo(family=charis, size=default_size),
            'italic': _FontInfo(family=charis, size=default_size, slant='italic'),
            'fixed': _FontInfo(family='monospace', size=small_size),
        }
        # Alias: 'big' → same as 'read'
        self.fonts['big'] = self.fonts['read']

    def _load_images(self, scale):
        """Load the theme's images.

        THE PATH WAS WRONG and every single image failed silently: this asked
        for `../images/`, i.e. `AZT/images/`, one level above the app. They
        live in `azt/images/`. It logged at DEBUG, so a run produced 45 lines
        of nothing visible unless you were watching at INFO — and then the
        NAMES leaked through as image sources, so the page requested
        `GET /transparent` and got a 404. Resolved the way
        ui_tkinter.Theme.mkimg does it (:183), from `program.aztdir`."""
        from utilities import file as fileu
        base = getattr(self.program, 'aztdir', None) or fileu.cwd()
        failed = []
        for name, filename in self.imagelist:
            try:
                imgurl = base / 'images' / filename
                self.photo[name] = Image(str(imgurl))
                if scale != 1 and self.photo[name].base_img:
                    self.photo[name].scale(scale, pixels=0)
            except Exception as e:
                failed.append(name)
                log.debug(f"Image {name} not loaded: {e}")
        if failed:
            # One WARNING beats 45 DEBUG lines: all-of-them failing is a
            # broken path, not 45 missing files.
            log.warning("{} of {} theme images failed to load from {} — "
                        "buttons and icons will be blank"
                        "".format(len(failed), len(self.imagelist),
                                  base / 'images'))

    def css_vars(self):
        """Return dict of CSS variable values for the current theme."""
        return {
            'background': self.background or '#d9d9d9',
            'activebackground': self.activebackground or '#ececec',
            'menubackground': self.menubackground or '#d9d9d9',
            'white': self.white or '#ffffff',
            'offwhite': self.offwhite or '#f0f0f0',
            'highlight': self.highlight or 'red',
            'padx': f'{self.padx}px',
            'pady': f'{self.pady}px',
            'ipadx': f'{self.ipadx}px',
            'ipady': f'{self.ipady}px',
            'scale': str(self.scale),
        }


# ── Style ─────────────────────────────────────────────────────────────
class Style:
    """ttk.Style's job, done in CSS.

    Missing entirely until now, and it is a HARD AttributeError at
    ui_shell.py:2006 — which is why the chooser could not render at all
    under this backend.

    The translation is closer than it looks: ttk.Style is a
    name -> options table that widgets consult, and CSS is a
    selector -> declarations table that elements consult. So a style name
    becomes a selector and the options become declarations. `map()`'s states
    become pseudo-classes and marker classes. What does NOT translate is
    ttk's element/layout machinery (`element_create`, `layout`), and nothing
    in azt uses it.
    """

    # ttk style name → CSS selector. Unknown names fall back to a data
    # attribute selector so a call is never silently dropped.
    SELECTORS = {
        'TNotebook': '.wv-notebook',
        'TNotebook.Tab': '.wv-tab',
        'TFrame': '.wv-frame',
        'TLabel': '.wv-label',
        'TButton': '.wv-button',
        'TEntry': '.wv-entry',
        'TCombobox': '.wv-combobox',
        'TCheckbutton': '.wv-checkbutton',
        'TRadiobutton': '.wv-radiobutton',
        'TProgressbar': '.wv-progressbar',
    }
    # ttk state name → how to reach it in CSS, relative to the base selector.
    STATES = {
        'active': ':hover',
        'hover': ':hover',
        'pressed': ':active',
        'focus': ':focus',
        'disabled': ':disabled',
        'selected': '.wv-tab-selected',
    }

    def __init__(self, *args, **kwargs):
        self.theme = kwargs.pop('theme', None)
        self._window = kwargs.pop('window', None)

    # ── helpers ───────────────────────────────────────────────────────
    def _selector(self, name):
        if name in self.SELECTORS:
            return self.SELECTORS[name]
        log.info("Style: no CSS selector for ttk style {!r}; using a data "
                 "attribute so the rule is at least addressable".format(name))
        return '[data-ttk-style="{}"]'.format(name)

    @staticmethod
    def _decls(options):
        """ttk options → CSS declarations. Unknown options are logged and
        skipped rather than guessed at."""
        out = {}
        for k, v in options.items():
            if v is None:
                continue
            if k in ('background', 'fieldbackground'):
                out['background'] = v
            elif k in ('foreground',):
                out['color'] = v
            elif k in ('font',):
                size = getattr(v, 'size', None)
                family = getattr(v, 'family', None)
                if size:
                    out['font-size'] = '{}px'.format(int(size))
                if family:
                    out['font-family'] = '"{}", var(--font-reading)'.format(family)
                if getattr(v, 'weight', None) == 'bold':
                    out['font-weight'] = 'bold'
                if getattr(v, 'slant', None) == 'italic':
                    out['font-style'] = 'italic'
            elif k in ('padding', 'padx', 'pady'):
                if isinstance(v, (tuple, list)):
                    out['padding'] = ' '.join('{}px'.format(int(n)) for n in v)
                else:
                    out['padding'] = '{}px'.format(int(v))
            elif k in ('borderwidth',):
                out['border-width'] = '{}px'.format(int(v))
            elif k in ('relief', 'anchor', 'sticky', 'expand', 'side'):
                pass  # ttk layout vocabulary; CSS has no counterpart here
            else:
                log.info("Style: no CSS mapping for option {!r}".format(k))
        return out

    @property
    def _target_window(self):
        """Callers construct this as `ui.Style(theme=...)` with no window —
        ttk.Style has no window argument — so fall back to the application
        root. Resolved per call, not at construction: Style can be built
        before the window exists, and _js() queues anyway."""
        if self._window is not None:
            return self._window
        return getattr(_app_root, '_wv_window', None)

    def _push(self, selector, decls):
        if not decls:
            return
        _js(self._target_window,
            'setStyleRule({}, {})'.format(json.dumps(selector),
                                          json.dumps(decls)))

    # ── ttk.Style API ─────────────────────────────────────────────────
    def configure(self, style_name, **options):
        self._push(self._selector(style_name), self._decls(options))

    def map(self, style_name, **options):
        """ttk: {option: [(state, value), ...]}. Each state becomes its own
        CSS rule on the base selector."""
        base = self._selector(style_name)
        perstate = {}
        for option, pairs in options.items():
            for pair in pairs or []:
                if not isinstance(pair, (tuple, list)) or len(pair) < 2:
                    continue
                state, value = pair[0], pair[-1]
                perstate.setdefault(state, {})[option] = value
        for state, opts in perstate.items():
            suffix = self.STATES.get(state)
            if suffix is None:
                log.info("Style.map: no CSS form for state {!r}".format(state))
                continue
            self._push(base + suffix, self._decls(opts))

    def apply_theme(self, style_name):
        """Mirrors ui_tkinter.Style.apply_theme: push the theme's colours at
        one style name. Most of what that does is already carried by the CSS
        custom properties Theme emits, so this only sets what a ttk style
        would genuinely override."""
        if self.theme is None:
            return
        decls = {}
        for attr, prop in (('background', 'background'),
                           ('foreground', 'color')):
            value = getattr(self.theme, attr, None)
            if value:
                decls[prop] = value
        self._push(self._selector(style_name), decls)

    def lookup(self, style_name, option, state=None, default=None):
        return default

    def theme_use(self, *args, **kwargs):
        pass

    def element_create(self, *args, **kwargs):
        log.info("Style.element_create is ttk-only; ignored under webview")

    def layout(self, *args, **kwargs):
        log.info("Style.layout is ttk-only; ignored under webview")


# ── Image ─────────────────────────────────────────────────────────────
class Image:
    """PIL-based image that produces base64 data URIs instead of PhotoImage."""

    def __init__(self, filename=None):
        self.filename = filename
        self.base_img = None
        self.scaled_img = None
        self.scaled = None  # base64 data URI string (display form)
        if filename and pilisactive:
            try:
                with PIL.Image.open(filename) as img:
                    img.load()
                    self.base_img = img.copy()
                self.compile()
            except Exception as e:
                log.error(f"Image load failed ({filename}): {e}")

    def maxhw(self, scaled=False):
        img = self.scaled_img if scaled else self.base_img
        if img:
            return max(img.width, img.height)
        return 0

    def scale(self, scale, pixels=100, resolution=5, scaleto='both'):
        if not self.base_img:
            return self.scaled
        if pixels:
            s = pixels * scale
            if scaleto == 'both':
                standard = self.maxhw()
            elif scaleto == 'height':
                standard = self.base_img.height
            elif scaleto == 'width':
                standard = self.base_img.width
            else:
                standard = self.maxhw()
            r = s / standard if standard else 1
        else:
            r = scale
        aspect = (max(1, int(self.base_img.width * r)),
                  max(1, int(self.base_img.height * r)))
        self.scaled_img = self.base_img.resize(aspect)
        self.compile()
        return self.scaled

    def scale_height(self, scale, pixels=100, resolution=5):
        return self.scale(scale, pixels=pixels, resolution=resolution, scaleto='height')

    def scale_width(self, scale, pixels=100, resolution=5):
        return self.scale(scale, pixels=pixels, resolution=resolution, scaleto='width')

    def prepare(self, scale, pixels=100, resolution=5, scaleto='both'):
        """The PIL half of `scale()`, with no display call — so the slow
        open/decode/resize can run OFF the main thread.

        `sort_ui.py:115` calls this on every card image, and it did not exist
        here: the call raised inside a builder, which is the shape that
        presents as a page missing its pictures rather than as an error.
        Found by the backend-parity audit (2026-09-11).

        Under tkinter the split is load-bearing — `compile()` must touch Tk
        from the main thread, `prepare()` must not — and here it is a
        convenience, since producing a data URI is thread-safe either way.
        Implemented as the same split anyway, so a caller can rely on one
        contract: after `prepare`, `scaled_img` is ready and `compile` is
        cheap.
        """
        if not self.base_img:
            return
        self.scale(scale, pixels=pixels, resolution=resolution,
                   scaleto=scaleto)

    def compile(self):
        """Convert current image to a base64 data URI string."""
        img = self.scaled_img if self.scaled_img else self.base_img
        if not img:
            self.scaled = None
            return
        buf = io.BytesIO()
        fmt = 'PNG'
        # str() FIRST: `filename` is a Path as often as a string — the CAWL
        # image set arrives as `PosixPath`s — and `Path.lower` does not
        # exist, so choosing the format crashed the whole picture-picking
        # page: "'PosixPath' object has no attribute 'lower'", reached from
        # `alphabet_chart.py:602` through `Image.scale` (Kent, webview,
        # 2026-09-14). `.jpeg` counts too; only `.jpg` was tested.
        name = str(self.filename).lower() if self.filename else ''
        if name.endswith('.jpg') or name.endswith('.jpeg'):
            fmt = 'JPEG'
        # A JPEG cannot hold transparency, and PIL raises rather than
        # flatten. Anything with an alpha channel goes out as PNG.
        if fmt == 'JPEG' and img.mode in ('RGBA', 'LA', 'P'):
            fmt = 'PNG'
        img.save(buf, format=fmt)
        b64 = base64.b64encode(buf.getvalue()).decode('ascii')
        mime = 'image/png' if fmt == 'PNG' else 'image/jpeg'
        self.scaled = f'data:{mime};base64,{b64}'


# ── Renderer ──────────────────────────────────────────────────────────
class Renderer:
    """PIL text rendering → base64 data URI (same logic as ui_tkinter.Renderer
    but outputs base64 strings instead of PhotoImage objects)."""

    def __init__(self, test=False, **kwargs):
        self.isactive = pilisactive
        self.renderings = {}
        self.imagefonts = {}
        self.img = None  # base64 data URI of last render

    def _get_font(self, font_info):
        """Resolve a _FontInfo to a PIL.ImageFont.truetype."""
        key = str(font_info)
        if key in self.imagefonts:
            return self.imagefonts[key]
        if not pilisactive:
            return None
        if isinstance(font_info, _FontInfo):
            fname = font_info['family']
            fsize = int(abs(font_info['size']) * 1.33)
            weight = font_info['weight']
            slant = font_info['slant']
        elif isinstance(font_info, dict):
            fname = font_info.get('family', 'Charis SIL')
            fsize = int(abs(font_info.get('size', 18)) * 1.33)
            weight = font_info.get('weight', 'normal')
            slant = font_info.get('slant', 'roman')
        else:
            return None
        fonttype = ''
        if weight == 'bold':
            fonttype += 'B'
        if slant == 'italic':
            fonttype += 'I'
        if not fonttype:
            fonttype = 'R'
        fonttypewords = fonttype.replace('B', 'Bold').replace('I', 'Italic').replace('R', 'Regular')
        # Same table as Tk and ReportLab (utilities.fonts): this branch
        # knew only the v6 'CharisSIL-*' file names, so a Charis-7 machine
        # found nothing here.
        from utilities import fonts as fontlib
        key = fontlib.key_for_family(fname)
        if key is None and 'Charis' in str(fname):
            key = 'charis'   # tolerate a family string we don't list
        files = fontlib.face_files(key, fonttypewords) if key else []
        for f in files:
            try:
                pil_font = PIL.ImageFont.truetype(font=f, size=fsize)
                self.imagefonts[key] = pil_font
                return pil_font
            except OSError:
                continue
        return None

    def render(self, **kwargs):
        if not self.isactive:
            return
        self.img = None
        font_info = kwargs.get('font')
        text = kwargs.get('text', '')
        wraplength = kwargs.get('wraplength', 0)
        if not text:
            return
        pil_font = self._get_font(font_info)
        if not pil_font:
            return
        fspacing = 10
        # Word-wrap
        img_tmp = PIL.Image.new("1", (10, 10), 255)
        draw_tmp = PIL.ImageDraw.Draw(img_tmp)
        text = text.replace('\t', '    ')
        lines = text.split('\n')
        for n, line in enumerate(lines):
            words = line.split(' ')
            nl = x = y = 0
            while y < len(words):
                y += 1
                l = ' '.join(words[x + nl:y + nl])
                bbox = draw_tmp.multiline_textbbox((0, 0), l, font=pil_font, spacing=fspacing)
                w = bbox[2] - bbox[0]
                if wraplength and w > wraplength:
                    words.insert(y + nl - 1, '\n')
                    x = y - 1
                    nl += 1
            lines[n] = ' '.join(words)
        text = '\n'.join(lines)
        # Measure final size
        bbox = draw_tmp.multiline_textbbox((0, 0), text, font=pil_font, spacing=fspacing)
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        xpad = ypad = abs(pil_font.size) if hasattr(pil_font, 'size') else 18
        align = 'center'
        if kwargs.get('justify') in ['left', 'LEFT'] or kwargs.get('anchor') in ['e', 'E']:
            align = 'left'
        # Draw
        img = PIL.Image.new("RGBA", (w + xpad, h + ypad), (255, 255, 255, 0))
        draw = PIL.ImageDraw.Draw(img)
        draw.multiline_text((xpad // 2, ypad // 4), text, font=pil_font,
                            fill='rgb(0, 0, 0)', align=align, spacing=fspacing)
        # Convert to base64
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        b64 = base64.b64encode(buf.getvalue()).decode('ascii')
        self.img = f'data:image/png;base64,{b64}'


# ── Concrete Widgets ─────────────────────────────────────────────────

class Frame(_WebviewWidget):
    def __init__(self, parent, *args, **kwargs):
        # BORDERS ARE KEPT NOW. They were dropped as cosmetic, and they are
        # not: borders are how several pages separate one region from
        # another, and with none of them drawn a webview page reads as one
        # undivided sheet. It also made `frontend/gallery.py` unable to show
        # a cell's extent, so the anchor row had to imply its boxes with
        # ruler CHARACTERS — Kent, 2026-09-14: "can we not make actual cells
        # with borders, so the 'ruler's have real values and effects?"
        #
        # `relief` maps ONE-TO-ONE onto CSS border styles, which is unusual
        # among these options: raised/sunken/groove/ridge are all real CSS
        # values, so this is a translation rather than an approximation.
        # `border` is tkinter's alias for `borderwidth`.
        border = kwargs.pop('borderwidth', kwargs.pop('border', None))
        relief = kwargs.pop('relief', None)
        if border is not None:
            kwargs['borderwidth'] = border
        if relief:
            kwargs['relief'] = relief
        # THE HIGHLIGHT RING IS USED HERE, and this dropped it with a comment
        # saying nothing styles it. Two pages style it, and not for focus:
        # `tasks.py:2064` and `transcribe_glyph.py:422` each ask for
        # `highlightthickness=10` in the theme's white to set the comparison
        # frame apart, and `sort_ui.py:1193` turns one off on purpose. Kent,
        # 2026-09-14: "we do actually use those". See `_setHighlight` in
        # widgets.js for what it draws and how it differs from Tk's.
        #   Kept as props rather than popped; only an explicit None is
        # dropped, since that means "not asked for".
        for k in ('highlightthickness', 'highlightbackground',
                  'highlightcolor'):
            if k in kwargs and kwargs[k] is None:
                kwargs.pop(k)
        super().__init__(parent, widget_type='frame', **kwargs)

    def iswaiting(self):
        if self.parent:
            return self.parent.iswaiting()
        return False

    def deiconify(self):
        if self.parent:
            return self.parent.deiconify()

    def ncolumns(self):
        return self.grid_size()[0]

    def nrows(self):
        return self.grid_size()[1]

    def windowsize(self):
        self.availablexy()


def _text_of(value):
    """The display string for a `text=`/`textvariable=` value.

    A Variable passed as text used to reach the page as its REPR — visible
    on the rendered chooser as
    "<frontend.ui_variables.StringVar object at 0x70fd9ca76270>". Two ways in:
    call sites that pass a StringVar as `text` (tkinter tolerates it because
    it stringifies through Tcl), and `textvariable`, which Label/Button were
    popping and discarding.

    This reads the CURRENT value. It does not subscribe to changes — a
    textvariable that updates later will not update the page yet, which is a
    real gap and a smaller one than printing an object address to the user.
    """
    if value is None:
        return ''
    getter = getattr(value, 'get', None)
    if callable(getter) and isinstance(value, (Variable, StringVar,
                                               IntVar, BooleanVar)):
        try:
            return nfc(str(getter()))
        except Exception:
            return ''
    return nfc(str(value))


def _image_src(value, parent=None, where=''):
    """A data: URI for whatever was passed as `image=`, or None.

    `where` names the caller for the log. A widget asked for an image that
    resolves to nothing draws an empty box, and until 2026-09-15 the one
    case that produced NO log line was the most likely one: a theme lookup
    that returned None (a name absent from this backend's imagelist —
    agenda/webview_imagelist_stale_copy.md) arrives here as None and
    returns on the first line. So "the button is empty" and "no image was
    asked for" were indistinguishable in a log, which is how the sort
    page's cycle control stayed a mystery through three rounds.

    Callers pass a ui.Image (usually straight out of theme.photo), and Image
    already keeps its base64 data URI in `.img` — so the icons were reachable
    all along; Label and Button simply threw the kwarg away.

    A BARE NAME IS NOT A SOURCE. Some call sites pass the theme key
    ('transparent', 'iconReport') rather than the Image, and returning that
    unchanged put it straight into an <img src>, which the page dutifully
    fetched: `GET /transparent HTTP/1.1" 404`. So a string is only used as-is
    when it actually looks like a URI; otherwise it is looked up in the
    theme, and failing that dropped with a log line."""
    if value is None:
        return None
    if isinstance(value, str):
        if value.startswith(('data:', 'http:', 'https:', 'file:', '/')):
            return value
        photo = getattr(getattr(parent, 'theme', None), 'photo', None)
        found = photo.get(value) if isinstance(photo, dict) else None
        if found is None:
            log.info("image={!r} is neither a URI nor a theme image name; "
                     "no image will be shown".format(value))
            return None
        return _image_src(found, parent)
    # TWO CLASSES, TWO ATTRIBUTE NAMES, and they are not interchangeable:
    # Image keeps its data URI in `.scaled` (set by Image.compile), while
    # `.img` is Renderer's (set by Renderer.render). Call sites pass either —
    # a theme icon or a rendered line of text — so both are accepted. Looking
    # only at `.img` meant every genuine ui.Image was reported as failed to
    # load, which is what "No data URI available for image
    # <class 'frontend.ui_webview.Image'>" was: my bug, not a missing file.
    for attr in ('scaled', 'img'):
        src = getattr(value, attr, None)
        if isinstance(src, str) and src:
            return src
    log.info("No data URI for image {!r} (filename={!r}) on {} — it produced "
             "no output; see the theme-image warning at startup"
             "".format(type(value).__name__, getattr(value, 'filename', None),
                       where or 'a widget'))
    return None


def _image_asked(raw, resolved, where):
    """Say so when an image was ASKED FOR and came to nothing.

    The silent case, and the likeliest one: `theme.photo['name']` for a name
    this backend's imagelist lacks hands back None, which `_image_src`
    returns unchanged without a word. The widget then draws as an empty box
    — for a bordered button, two thin lines with nothing between them, which
    is exactly what the sort page's cycle control looked like for three
    rounds (Kent, 2026-09-15: "right refresh is still missing image").
    """
    if raw is not None and not resolved:
        log.info("{}: image={!r} was asked for and resolved to nothing; the "
                 "widget will be empty".format(where, raw))
    return resolved


class Label(_WebviewWidget):
    def __init__(self, parent, *args, **kwargs):
        # Handle font as a key name
        font = kwargs.pop('font', 'default')
        # KEPT. 91 sites pass `anchor=` and every one of them was dropped
        # here, so no label or button honoured the alignment it asked for.
        # Only forwarded when actually given: `.wv-label` already defaults to
        # vertically centred and horizontally flush-left, which is tkinter's
        # own default ("w", ui_tkinter.py:2942), so an unspecified label must
        # keep looking exactly as it does now.
        anchor = kwargs.pop('anchor', None)
        if anchor:
            kwargs['anchor'] = anchor
        kwargs.pop('norender', None)
        # HONOURED, NOT DISCARDED. These were popped and dropped, so the
        # caller's pixel budget went nowhere: the alphabet chart rendered
        # every illustration at full resolution and burst its grid (Kent,
        # 2026-09-14), and `sort_ui.py:455,1238-1255` has been passing
        # image_pixels for the sort page's icons and join images all along
        # with no effect. A silently-dropped kwarg with no error is the
        # exact class agenda/webview_when_to_finish.md Step 6 is about.
        image_px = kwargs.pop('image_pixels', None)
        image_scaleto = kwargs.pop('image_scaleto', None)
        _raw_image = kwargs.pop('image', None)
        _where = '{} {!r}'.format(type(self).__name__,
                                  str(kwargs.get('text', ''))[:24])
        image = _image_asked(_raw_image,
                             _image_src(_raw_image, parent, _where), _where)
        compound = kwargs.pop('compound', None)
        if image:
            kwargs['image'] = image
            kwargs['compound'] = compound or 'top'
            if image_px:
                kwargs['image_pixels'] = image_px
            if image_scaleto:
                kwargs['image_scaleto'] = image_scaleto
        textvariable = kwargs.pop('textvariable', None)
        # KEEP the caller's measured wrap width instead of discarding it.
        # `wraplength` is a PIXEL figure the caller worked out for the box
        # this label sits in, and it is already inherited down the widget
        # tree here (see `inherit`, :614) — popping it threw away the one
        # number that knows how much room there is. `wrap()` then had nothing
        # to act on, which is why it was a no-op with a comment claiming CSS
        # handled it.
        self._asked_wraplength = kwargs.pop('wraplength', None)
        # AND APPLY IT NOW, not only when someone calls `wrap()`. Stored and
        # waited for, it made the CONSTRUCTOR KWARG INERT: tkinter applies
        # `wraplength` as a widget option the moment it is given, so
        # `Label(..., wraplength=200)` wraps there and did nothing here. In
        # `frontend/gallery.py` the specimen asking for 200 ran to ~850px,
        # which blew its grid column wide enough to push the next column off
        # the window (Kent, 2026-09-14: "column problem?").
        #   `wrap()` is still the right call for a caller that wants the
        # measured fallback; this is for a caller that already knows the
        # number.
        if self._asked_wraplength:
            kwargs['wraplength'] = self._asked_wraplength
        # BORDERS, as on Frame. Passed to labels all over the app
        # (`ui_tkinter.testapp` borders every Message/Label specimen) and
        # dropped here, so a bordered label had no border and nothing said
        # so. `relief` maps 1:1 onto CSS border styles — see _setBorder.
        border = kwargs.pop('borderwidth', kwargs.pop('border', None))
        relief = kwargs.pop('relief', None)
        if border is not None:
            kwargs['borderwidth'] = border
        if relief:
            kwargs['relief'] = relief
        kwargs['font'] = font
        # A Variable in either slot resolves to its VALUE, not its repr.
        # KEEP the Variable itself too: it has to be subscribed to below, and
        # `text=<a StringVar>` is how this app's live labels are built.
        self._passed_text_var = None
        if 'text' in kwargs:
            if isinstance(kwargs['text'], Variable):
                self._passed_text_var = kwargs['text']
            kwargs['text'] = _text_of(kwargs['text'])
        elif textvariable is not None:
            kwargs['text'] = _text_of(textvariable)
        super().__init__(parent, widget_type='label', **kwargs)
        # TRACK THE VARIABLE, don't just read it once. `_text_of` resolves a
        # Variable to its value at BUILD time and says so in its docstring
        # ("It does not subscribe to changes … which is a real gap"). The
        # Sound Card Settings window is that gap in its purest form: its four
        # rows are Labels built with `text=StringVar()` — EMPTY at creation —
        # and filled afterwards by updatesoundcard/Hz/format/cardout. So the
        # window came up with the microphone, rate, format and speaker rows
        # simply ABSENT (Kent, GTK webview, 2026-09-11), which reads as a
        # broken settings screen rather than a missing update.
        #   Same shape as the EntryField fix of 2026-09-09, and the same
        # mechanism: trace the variable and push the new value to the DOM.
        # `text=` carrying a Variable is the common case in this app; a real
        # `textvariable=` is the tkinter-idiomatic one. Either is tracked.
        tracked = textvariable if textvariable is not None \
                  else self._passed_text_var
        self._textvariable = tracked
        if tracked is not None:

            def _to_dom(*_args, _var=tracked):
                try:
                    self.configure(text=_text_of(_var))
                except Exception as e:
                    log.info("couldn't update label {} from its variable ({})"
                             "".format(getattr(self, '_wid', '?'), e))
            try:
                tracked.trace_add('write', _to_dom)
            except Exception as e:
                log.info("couldn't trace a label's textvariable ({})".format(e))

    def wrap(self):
        """Constrain this label's width so its text wraps — SAME CONTRACT as
        ui_tkinter.Label.wrap(): an explicit `wraplength` wins, `availablexy`
        is the fallback for callers with no better number. Pixels, like every
        other layout figure in this app.

        WAS `pass`, with "Handled by CSS" — and the CSS rule that would have
        handled it (`#root > .wv-label`, `#root > .wv-frame > .wv-label`) is
        scoped one or two levels deep on purpose, so a label nested deeper got
        no constraint. `ErrorNotice` is exactly such a label
        (error_notice.py:54 calls this), and its text rendered as ONE UNBROKEN
        LINE: the window fitted itself to the content and came out 1680px
        wide, a single line across the top and the rest empty (macOS, webview,
        2026-09-11).

        MY FIRST FIX HARDCODED 46em (~70-80 characters) and Kent named the
        problem: "wrapping at 70-80 chars seems like exactly the thing we were
        NOT doing. we wrap in places with much less space; this is why we have
        used availablexy... I assume this hardcoded number will bite us sooner
        or later." Correct on both counts — a fixed character count is wrong
        wherever the box is narrower than that, which is most places, and it
        reinvents (badly) a measurement the app already makes. The value was
        being THROWN AWAY one method up: `__init__` popped `wraplength` and
        dropped it.

        DIVISION OF LABOUR with the CSS, settled 2026-09-11: `.wv-label` now
        carries `max-width: 92vw`, so NOTHING can demand more width than the
        window has and the window can no longer size itself to an unwrapped
        paragraph. That is a layout invariant and belongs in the stylesheet.
        What this method does is the other half — the caller's own
        measurement of the BOX this label sits in, which is narrower than the
        screen and which only the caller (or `availablexy`) knows. The two are
        not alternatives: without the CSS a notice could still be screen-wide,
        and without this a label in a narrow cell would wrap only at 92vw.
        """
        asked = getattr(self, '_asked_wraplength', None) \
                or getattr(self, 'wraplength', None)
        if not asked:
            try:
                self.availablexy()
                asked = getattr(self, 'maxwidth', None)
            except Exception as e:
                log.info("couldn't measure available width for {} ({})"
                         "".format(getattr(self, '_wid', '?'), e))
        if not asked:
            return      # nothing measured: leave it to the CSS, as before
        try:
            self.configure(wraplength=int(asked))
        except Exception as e:
            log.info("couldn't set a wrap width on {} ({})".format(
                        getattr(self, '_wid', '?'), e))


class Button(_WebviewWidget):
    def __init__(self, parent, **kwargs):
        font = kwargs.pop('font', 'default')
        command = kwargs.pop('command', kwargs.pop('cmd', None))
        choice = kwargs.pop('choice', None)
        window = kwargs.pop('window', None)
        anchor = kwargs.pop('anchor', None)     # kept; see Label
        if anchor:
            kwargs['anchor'] = anchor
        # Captured BEFORE the image block, and kept — see Label for why
        # dropping these was a real gap rather than tidiness.
        image_px = kwargs.pop('image_pixels', None)
        image_scaleto = kwargs.pop('image_scaleto', None)
        _raw_image = kwargs.pop('image', None)
        _where = '{} {!r}'.format(type(self).__name__,
                                  str(kwargs.get('text', ''))[:24])
        image = _image_asked(_raw_image,
                             _image_src(_raw_image, parent, _where), _where)
        compound = kwargs.pop('compound', None)
        if image:
            kwargs['image'] = image
            kwargs['compound'] = compound or 'top'
            if image_px:
                kwargs['image_pixels'] = image_px
            if image_scaleto:
                kwargs['image_scaleto'] = image_scaleto
        # DROPPED ON PURPOSE, the last row of
        # agenda/webview_discards_widget_options.md to be settled (Kent,
        # 2026-09-14). A button already looks like a button here: the engine
        # draws its own raised/pressed states and hover, where Tk draws
        # nothing unless told. Reproducing tkinter's relief on top of that
        # would make webview buttons look LESS like the platform's, and the
        # item's own test is whether the PAGE is wrong, not whether the
        # option is unimplemented. (Frame and Label are the opposite case —
        # they have no default look, so relief is honoured there.)
        kwargs.pop('relief', None)
        # KEPT, not dropped. `updateProp` has handled 'state' for buttons all
        # along (widgets.js), so `button['state']='disabled'` and
        # `.config(state=…)` already worked — but a button asked for disabled
        # AT CONSTRUCTION started enabled, because this popped it here.
        # `ui_shell.py:3227` does exactly that. Passed through as a prop (not
        # translated to `disabled`) so `cget('state')` reads back what the
        # caller set, as it does under tkinter.
        state = kwargs.pop('state', None)
        if state:
            kwargs['state'] = state
        kwargs.pop('norender', None)
        # A BUTTON'S LABEL CAN COME FROM A VARIABLE, and dropping it left the
        # button BLANK. `tasks/transcribe_glyph.py:395` builds its OK button
        # with `textvariable=self.oktext` and an empty StringVar, then sets
        # the variable as the page changes — so under webview that button had
        # no text at all, ever, and no later `set()` could give it any.
        # Same treatment as Label (:2233): resolve it now AND trace it.
        textvariable = kwargs.pop('textvariable', None)
        if textvariable is not None and not kwargs.get('text'):
            kwargs['text'] = _text_of(textvariable)
        kwargs.pop('wraplength', None)
        # Remove button-grid kwargs (brow, bcolumn, etc.)
        for k in list(kwargs):
            if k.startswith('b') and k[1:] in self._gridkwargs:
                kwargs.pop(k)
        kwargs['font'] = font
        # A VARIABLE PASSED AS `text=` IS STILL A VARIABLE, and Button kept
        # only the value. Label captures it (`_passed_text_var`, :2603) and
        # traces it; Button resolved it once and forgot it, so the sort
        # page's member count was whatever it happened to be at build time —
        # which for a group button being built is 0 or blank, and never
        # changed again (Kent, 2026-09-15: "n variable not showing, on either
        # end"). The app writes `text=self._n` rather than `textvariable=`
        # because tkinter accepts it, so this is the common case here, not
        # the exotic one.
        _passed_text_var = None
        if 'text' in kwargs:
            if isinstance(kwargs['text'], (Variable, StringVar, IntVar,
                                           BooleanVar)):
                _passed_text_var = kwargs['text']
            # `_text_of` FIRST, or a Variable passed as `text=` reaches the
            # page as its REPR. Label has done this for a while; Button
            # never did, and `nfc()` on a non-string stringifies it — so the
            # sort page's group buttons each read
            # "<frontend.ui_variables.IntVar object at 0x784f4859b610>"
            # where the member count belongs (Kent, 2026-09-15). The app
            # passes a Variable as `text` in plenty of places because
            # tkinter tolerates it (it stringifies through Tcl), which is
            # why this is the second time the same repr has been on screen.
            kwargs['text'] = nfc(_text_of(kwargs['text']))
        super().__init__(parent, widget_type='button', **kwargs)
        tracked = textvariable if textvariable is not None \
                  else _passed_text_var
        self._textvariable = tracked
        if tracked is not None:

            def _to_dom(*_args, _var=tracked):
                try:
                    self.configure(text=_text_of(_var))
                except Exception as e:
                    log.info("couldn't update button {} from its variable "
                             "({})".format(getattr(self, '_wid', '?'), e))
            try:
                tracked.trace_add('write', _to_dom)
            except Exception as e:
                log.info("couldn't trace a button's textvariable ({})"
                         "".format(e))

        # Build command (same logic as ui_tkinter.Button.build_command)
        self.command = command
        self.choice = choice
        self.window = window
        self._build_command()

    def _takes(self, cmd, positional=0, keyword=None):
        """Can `cmd` be called with this many extra positional args / this kw?

        ASK THE CALLABLE instead of assuming from what the CALLER passed.
        The previous version mirrored ui_tkinter's rule — "a choice was given,
        so pass it" — and a caller that supplies a `choice` alongside a
        command taking no arguments then produced, on every click:

            TypeError: Sort.runcheck() takes 1 positional argument
                       but 2 were given

        (Kent's Mac, webview backend, 2026-09-11; it fired three times, once
        per click, and the button silently did nothing because `on_event`
        logs and carries on.) The presence of a `choice` kwarg says what the
        BUTTON knows, not what the command wants; only the command's
        signature says the latter.

        Unknown signatures (C functions, some callables) return True: this is
        a compatibility shim, so where it cannot tell it should behave as it
        did before rather than silently drop an argument.
        """
        try:
            import inspect
            sig = inspect.signature(cmd)
        except (TypeError, ValueError):
            return True
        params = list(sig.parameters.values())
        if keyword is not None:
            if any(p.name == keyword for p in params):
                return True
            return any(p.kind is p.VAR_KEYWORD for p in params)
        slots = [p for p in params
                 if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)]
        if any(p.kind is p.VAR_POSITIONAL for p in params):
            return True
        return len(slots) >= positional

    def _build_command(self):
        cmd = self.command
        if not cmd:
            self._final_cmd = _donothing
        elif (self.choice is not None and self.window is not None
                and self._takes(cmd, 1) and self._takes(cmd, keyword='window')):
            self._final_cmd = lambda data, x=self.choice, w=self.window: cmd(x, window=w)
        elif self.choice is not None and self._takes(cmd, 1):
            self._final_cmd = lambda data, x=self.choice: cmd(x)
        else:
            # Either no choice to pass, or a command that will not accept one.
            self._final_cmd = lambda data: cmd()
        # REPLACE, DON'T STACK. `_api.register` APPENDS, so rebinding a
        # command — which `configure(command=…)` now does, for
        # `activate_cell`/`deactivate_cell` — would leave the previous
        # handler live and fire both. Harmless at construction (there is
        # nothing to clear) and load-bearing on every later call.
        _api.unregister(self._wid, 'command')
        _api.register(self._wid, 'command', self._final_cmd)


class EntryField(_WebviewWidget):
    def __init__(self, parent, *args, **kwargs):
        # `render` asks tkinter to draw the text as a BITMAP, which is how
        # that backend shows glyphs its widget fonts cannot (`Renderer`). A
        # browser has no such problem and no such path, so the MECHANISM is
        # dropped — but the SHAPE is not: tkinter's field grows a `rendered`
        # Label when `render=True` (ui_tkinter.EntryField.post_tk_init), and
        # the app grids it itself (`lexicon.py:970`,
        # `formfield.rendered.grid(row=2, …)`), so dropping the attribute made
        # Add-a-Word die on its first prompt under webview: "PORT GAP:
        # 'EntryField' object has no attribute 'rendered'" (Kent, 2026-09-22).
        # See below, after the widget exists.
        render = kwargs.pop('render', False)
        # KEPT. An entry field asked for `font='readbig'` and got the browser
        # default, which matters more here than on a label: these are the
        # fields people type IPA and tone into, and the reading font is how
        # the text is legible at all. Visible side by side in
        # `frontend/gallery.py` — tkinter large, webview small (2026-09-14).
        kwargs['font'] = kwargs.pop('font', 'default')
        # `text=` IS THE APP'S SPELLING for the variable. `lexicon.py:944`
        # passes a string_var as `text=`, and tkinter's EntryField accepts it
        # (TextBase.reserve_kwargs pulls it aside); only `textvariable=` was
        # honoured here, so a caller using the app's own convention got a
        # field bound to a throwaway variable.
        var = kwargs.pop('textvariable', None) or kwargs.pop('text', None)
        if isinstance(var, str):
            # A plain string is an initial VALUE, not a variable.
            initial, var = var, None
        else:
            initial = None
        kwargs.pop('text', None)
        self.textvariable = var if var is not None else StringVar()
        if initial:
            self.textvariable.set(initial)
        super().__init__(parent, widget_type='entry', **kwargs)
        if render is True:
            # PARITY OF SHAPE, NOT OF MECHANISM. An empty label the app may
            # grid and remove exactly as it does tkinter's; it never gets
            # text, because the entry itself already renders tone letters
            # correctly here (theme.css asks the font for the feature). Placed
            # nowhere until the app places it, so an unused one costs no cell.
            self.rendered = Label(parent, text='', gridwait=True)
        # ── BOTH DIRECTIONS, which is new (2026-09-09) ────────────────────
        # Only entry → variable was wired, so a field built with a
        # `textvariable` that already had a value came up EMPTY, and any later
        # `var.set(...)` never reached the screen. The Transcriber's field is
        # created with `initval='˥˥ ˩˩ ˧˧'` and showed nothing (Kent, on both
        # engines). That is the general "textvariable doesn't track changes"
        # gap in this backend, closed here for entries.
        #   `_pushed` breaks the loop: the DOM tells us a value, we store it
        # as already-pushed, then the variable's trace sees no difference and
        # does not write it back. Writing it back would be harmless in
        # principle and awful in practice — assigning `el.value` while
        # someone is typing can move the caret to the end.
        self._pushed = self.textvariable.get() or ''

        def _from_dom(data):
            self._pushed = data.get('value', '')
            self.textvariable.set(self._pushed)
        _api.register(self._wid, 'input', _from_dom)

        def _to_dom(*_args):
            text = self.textvariable.get() or ''
            if text == self._pushed:
                return
            self._pushed = text
            wv = getattr(self, '_wv_window', None)
            if wv is not None:
                _js(wv, f'updateProp({self._wid}, "value", {json.dumps(text)})')
        self.textvariable.trace_add('write', _to_dom)

        # And show what it already holds. `_js` queues per window, so this is
        # safe before the page has loaded.
        if self._pushed:
            wv = getattr(self, '_wv_window', None)
            if wv is not None:
                _js(wv, 'updateProp({}, "value", {})'.format(
                        self._wid, json.dumps(self._pushed)))

    def get(self):
        return self.textvariable.get()

    # ── The tkinter Entry API this backend was missing ────────────────────
    # `delete` and `insert` are how text gets into an entry from CODE rather
    # than from typing, and neither existed: `Transcriber.addchar` does
    # `self.formfield.delete(0, ui.END)` then `insert(ui.INSERT, x)`, so
    # clicking a tone letter raised `'EntryField' object has no attribute
    # 'delete'` — inside a pywebview event callback, where `on_event` logs the
    # traceback and carries on, so it presented as a button that did nothing
    # (Kent, 2026-09-09, --engine=qt).
    #   That is the SIXTH tkinter call this backend didn't answer (after
    # takekioskscreen, after_idle, cget, wait_window, lift) and the second to
    # arrive silently through a callback. The conformance check against
    # ui_interface.py — noted in agenda/webview_when_to_finish.md — is what
    # stops the seventh being found this way.
    #
    # Both keep the variable and the DOM in step, in that order: the variable
    # is what `get()` reads, and `updateProp(…,'value',…)` is what the page
    # shows (widgets.js:438-440). Writing only the variable would look right
    # to the program and stay stale on screen.
    def _put(self, text):
        """Set the text. Goes through the variable, whose trace pushes it to
        the page — so there is one path to the DOM, not two that can disagree.
        """
        self.textvariable.set(text)

    def _index(self, where, current):
        """tkinter accepts 0, 'end'/END, 'insert'/INSERT and integers. There
        is no separate cursor here, so INSERT means the end — which is what
        the one caller wants (append the character just clicked)."""
        if where in (END, 'end', INSERT, 'insert'):
            return len(current)
        try:
            return max(0, min(int(where), len(current)))
        except (TypeError, ValueError):
            return len(current)

    def delete(self, first, last=None):
        """Remove text. `delete(0, END)` — the common case — clears it."""
        current = self.textvariable.get() or ''
        start = self._index(first, current)
        stop = len(current) if last is None else self._index(last, current)
        if stop < start:
            start, stop = stop, start
        self._put(current[:start] + current[stop:])

    def insert(self, index, text):
        # AT THE CARET, IN THE PAGE. Python does not know where the caret is —
        # the DOM does — so `_index` had mapped INSERT to the end, and the
        # Transcriber's character buttons appended wherever the user had
        # clicked (Kent, 2026-09-22, the tone page: "only append, not input
        # where the cursor is"). tkinter's INSERT is the caret, so the page
        # does the splice with `setRangeText` at its own selection and
        # reports the new value through the ordinary 'input' event, which
        # is what sets the variable (`_from_dom`). Nothing is written to the
        # variable here for that case: two writers would race, and the DOM
        # is the one that knows. A field with no page yet keeps the old
        # append, since there is no caret to speak of.
        wv = getattr(self, '_wv_window', None)
        if index in (INSERT, 'insert') and wv is not None:
            _js(wv, f'updateProp({self._wid}, "insert_at_caret", '
                    f'{json.dumps(str(text))})')
            return
        current = self.textvariable.get() or ''
        at = self._index(index, current)
        self._put(current[:at] + str(text) + current[at:])

    def focus_set(self):
        """Put the keyboard in this field. tkinter's widgets all answer it,
        and `addchar` calls it after clearing so the user can type on."""
        wv = getattr(self, '_wv_window', None)
        if wv is not None:
            _js(wv, f'focusWidget({self._wid})')

    def icursor(self, index):
        """Accepted and ignored: there is no separate insertion cursor to
        move, and callers use it to park the caret after inserting — which is
        already where it is."""
        pass


class Progressbar(_WebviewWidget):
    def __init__(self, parent, *args, **kwargs):
        # ORIENT IS KEPT. It was dropped, so a bar asked for vertically was
        # drawn horizontally — `ui_tkinter.testapp` builds both orientations
        # and `frontend/gallery.py` shows them side by side, which is how
        # this surfaced (Kent, 2026-09-14: "a vertical bar drawn
        # horizontally means 'orient' is being dropped" — it was).
        orient = kwargs.pop('orient', None)
        if orient:
            kwargs['orient'] = orient
        # `mode` STAYS DROPPED, and deliberately: 'indeterminate' needs an
        # animation this backend does not have, and silently drawing a
        # determinate bar at whatever value it happens to hold would be worse
        # than the honest omission. Nothing in the app asks for it yet — when
        # something does, it needs a CSS animation, not a prop.
        kwargs.pop('mode', None)
        super().__init__(parent, widget_type='progressbar', **kwargs)

    def current(self, value):
        if isinstance(value, float) and 0 <= value <= 1:
            value = int(value * 100)
        wv = getattr(self, '_wv_window', None)
        _js(wv, f'updateProp({self._wid}, "progress", {value})')


class Notebook(_WebviewWidget):
    """Tabs. `add`/`select` were bare `pass` stubs, so the chooser's three tab
    frames were created, never attached and never shown."""

    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, widget_type='notebook', **kwargs)
        self._tabs = []          # child widgets, in tab order
        self._selected = None
        # A TAB SWITCH CHANGES WHAT THE WINDOW HAS TO HOLD, and nothing was
        # telling the window so. Every refit in this backend is triggered by
        # a widget being CREATED (`_request_refit`, called from
        # `_finish_creation`), and a tab switch creates nothing: all the
        # panels were built at startup, the fit measured the one that was
        # visible, and selecting a bigger tab left its content cropped with
        # no scrollbar and no way to reach it (Kent, 2026-09-16, the
        # chooser's Reports tab: a third column and a fourth row off-page).
        #   Registered here rather than left to the app, because the app
        # binding `<<NotebookTabChanged>>` is optional and this is not: a
        # page cannot forget to ask, same principle as the creation hook.
        # `_api.register` APPENDS, so an app binding added later runs
        # alongside this and neither displaces the other.
        try:
            _api.register(self._wid, 'tabchanged',
                          lambda data: self._refit_for_tab('tab clicked'))
        except Exception as e:
            log.debug("notebook {}: could not ask for a refit on tab "
                      "change ({!r})".format(self._wid, e))

    def _refit_for_tab(self, trigger):
        """Ask the window to re-fit after the visible panel changes.

        Short delay: nothing else is arriving, so there is no burst to
        coalesce and the user is looking at the cropped page right now."""
        try:
            win = self._root_for_binding()
            if win is not None and win is not self:
                _request_refit(win, trigger, delay=0.05)
        except Exception as e:
            log.debug("notebook {}: refit request failed ({!r})"
                      "".format(self._wid, e))

    def add(self, child, **kwargs):
        text = kwargs.pop('text', '')
        self._tabs.append(child)
        wv = getattr(self, '_wv_window', None)
        _js(wv, 'notebookAdd({}, {}, {})'.format(
            self._wid, child._wid, json.dumps(nfc(text))))
        if self._selected is None:
            self._selected = child

    def select(self, tab_id=None):
        """No argument: return the current tab, as ttk does. With one: select
        it. Accepts a child widget or an index."""
        if tab_id is None:
            return self._selected
        child = tab_id
        if isinstance(tab_id, int):
            if not 0 <= tab_id < len(self._tabs):
                return None
            child = self._tabs[tab_id]
        self._selected = child
        wv = getattr(self, '_wv_window', None)
        _js(wv, 'notebookSelect({}, {}, false)'.format(self._wid, child._wid))
        # AND HERE TOO, because this path does not come back. `notify=false`
        # means the page does not send `tabchanged` — deliberately, so a
        # programmatic select cannot re-enter an app handler that selects —
        # so the registration in `__init__` never fires for it, and the
        # chooser selects its starting tab exactly this way.
        self._refit_for_tab('tab selected')
        return child

    def index(self, child=None):
        target = self._selected if child is None else child
        try:
            return self._tabs.index(target)
        except ValueError:
            return -1

    def tabs(self):
        return list(self._tabs)

    def bind(self, sequence, func, add=None):
        """Only ONE thing needs translating — the virtual event ttk emits on a
        tab change. Everything else goes to the base binding.

        The old override swallowed EVERY binding on a notebook, which is a
        different bug wearing the same clothes: a widget that silently accepts
        a callback and never calls it."""
        if sequence == '<<NotebookTabChanged>>':
            def _onchange(event, _f=func):
                idx = getattr(event, 'index', None)
                if isinstance(idx, int) and 0 <= idx < len(self._tabs):
                    self._selected = self._tabs[idx]
                return _f(event)
            return super().bind('tabchanged', _onchange, add=add)
        return super().bind(sequence, func, add=add)

class Message(_WebviewWidget):
    """tkinter's Message: a label that wraps itself.

    TWO TK QUIRKS, reproduced rather than tidied away, because a harness that
    disagrees with tkinter about the API teaches the wrong thing:

      * **`width` is in PIXELS here**, not characters — tkinter.Message
        measures its line length in screen units, unlike Entry and Label.
      * **There is no `wraplength`.** tkinter.Message simply refuses it:
        "gallery Message #3 failed: TclError('unknown option -wraplength')"
        (Kent, tkinter, 2026-09-14). It is accepted here as a synonym for
        `width` so a caller who reaches for the Label spelling gets what
        they meant, but the gallery uses `width` because that is what works
        on both.

    `font` was also being dropped — it is a plain label underneath and the
    font class works on it, so there was no reason.
    """

    def __init__(self, parent, *args, **kwargs):
        kwargs['font'] = kwargs.pop('font', 'default')
        wrap = kwargs.pop('wraplength', None) or kwargs.pop('width', None)
        if wrap:
            kwargs['wraplength'] = wrap
        super().__init__(parent, widget_type='label', **kwargs)


class CheckButton(_WebviewWidget):
    def __init__(self, parent, *args, **kwargs):
        font = kwargs.pop('font', 'default')
        self._variable = kwargs.pop('variable', BooleanVar())
        # `image` AND `selectimage` ARE CORRECTLY DROPPED, and this is the
        # one place on the discarded-options list where that is true.
        # `ui_tkinter.CheckButton` supplies them ITSELF from the theme
        # ('uncheckedbox'/'checkedbox', `_sm` unless large_images) because Tk
        # with indicatoron=False has no checkbox of its own to draw — so the
        # image pair IS the control there. A browser's <input type=checkbox>
        # draws it natively, so reproducing a themed image pair would be
        # emulating what the engine already does. No caller passes them.
        kwargs.pop('image', None)
        kwargs.pop('selectimage', None)
        kwargs.pop('indicatoron', None)     # Tk-only: no indicator to hide
        kwargs.pop('norender', None)
        kwargs.pop('compound', None)
        # THE SIZE IS NOT DROPPED, though, and it was. Callers do not pass
        # images; they pass the SIZE of them — `tasks.py:1171-1175` asks for
        # a 12px-high word-break box ("image_pixels sizes both states now, so
        # this is the actual knob"), and `large_images` is how a page asks
        # for a bigger control, which matters on a field touch screen. Both
        # went nowhere, so every webview checkbox came out at the browser
        # default.
        large = kwargs.pop('large_images', False)
        px = kwargs.pop('image_pixels', None)
        scaleto = kwargs.pop('image_scaleto', None)
        if px:
            kwargs['box_pixels'] = px
            if scaleto:
                kwargs['box_scaleto'] = scaleto
        elif large:
            kwargs['box_large'] = True
        self._command = kwargs.pop('command', None)
        kwargs['font'] = font
        super().__init__(parent, widget_type='checkbutton', **kwargs)
        _api.register(self._wid, 'toggle',
                      lambda data: self._on_toggle(data.get('checked', False)))

    def _on_toggle(self, checked):
        self._variable.set(checked)
        if self._command:
            self._command()


class RadioButton(_WebviewWidget):
    _group_counter = 0

    def __init__(self, parent, *args, **kwargs):
        font = kwargs.pop('font', 'default')
        self._variable = kwargs.pop('variable', StringVar())
        self._value = kwargs.pop('value', '')
        # DROPPED ON PURPOSE, and the effect is visible: tkinter's
        # indicatoron=0 hides the dot and draws the whole control as a button
        # that stays pressed in when chosen, so `indicatoron=0` and the
        # default look different there and identical here. Nothing in the app
        # asks for it — only `ui_tkinter.testapp` and the gallery, which says
        # so beside the specimens. If a page ever wants it, the shape is a
        # hidden <input> with the <label> styled as a button, not a prop.
        kwargs.pop('indicatoron', None)
        self._command = kwargs.pop('command', None)
        kwargs['font'] = font
        # Group radio buttons by their variable (same variable = same group)
        kwargs['group'] = str(id(self._variable))
        kwargs['value'] = str(self._value)
        super().__init__(parent, widget_type='radiobutton', **kwargs)
        _api.register(self._wid, 'select',
                      lambda data: self._on_select(data.get('value', '')))

    def _on_select(self, value):
        self._variable.set(value)
        if self._command:
            self._command()


class ListBox(_WebviewWidget):
    """Options list, with the VALUE and the DISPLAY TEXT kept apart.

    That separation is the whole point, and its absence was a visible bug:
    options arrive as strings, ints, dicts with 'code'/'name', or 2/3/4-tuples,
    and this class was storing them raw and shipping them to the page — so the
    interface-language list read `{'code': 'es', 'name': 'Spanish'}` instead of
    `Spanish`. tkinter's ListBox (ui_tkinter.py:3312) normalises every option
    through `ButtonFrame.regularize_choice` into a `choice` and a `text`, keeps
    two parallel lists, and fires `command(choice, window=window)`. This now
    does the same, so the same option list renders the same on both backends
    and the callback receives a code rather than a label.
    """

    def __init__(self, parent, *args, **kwargs):
        font = kwargs.pop('font', 'default')
        optionlist = kwargs.pop('optionlist', []) or []
        self._command = kwargs.pop('command', None)
        self._window = kwargs.pop('window', None)
        self._raw_command = kwargs.pop('raw_command', False)
        kwargs['height'] = kwargs.pop('height', 10)
        kwargs['width'] = kwargs.pop('width', 40)
        # SELECTMODE IS A CONTRACT, not decoration: dropping it made every
        # list single-select, so a caller that offered several picks could
        # only ever receive one and had no way to know. `testapp` builds a
        # MULTIPLE list and reads `curselection()` expecting several indices.
        # tkinter's values are 'single'/'browse'/'multiple'/'extended'; the
        # last two both mean more than one may be chosen.
        mode = str(kwargs.pop('selectmode', 'browse') or 'browse').lower()
        self._multiple = mode in ('multiple', 'extended')
        kwargs['multiple'] = self._multiple
        # THE MODE, not only the boolean: MULTIPLE toggles on a plain click
        # and EXTENDED replaces (shift for a run, ctrl for one row), so the
        # page needs to know which of the four it is. tkinter's constants are
        # 'single'/'browse'/'multiple'/'extended'.
        kwargs['selectmode'] = mode
        # `listvariable` holds the CONTENTS in tkinter, not the selection —
        # worth saying because the name reads like the other thing. Kept so
        # a caller's list can be read from it when no optionlist was given,
        # which is how tkinter behaves; it is NOT written back, because
        # nothing in this app reads it back and a two-way binding on a list
        # is a different feature.
        self._listvariable = kwargs.pop('listvariable', None)
        if not optionlist and self._listvariable is not None:
            try:
                held = self._listvariable.get()
            except Exception:
                held = None
            if held:
                optionlist = list(held) if not isinstance(held, str) else [held]
        kwargs['font'] = font
        super().__init__(parent, widget_type='listbox', **kwargs)
        self.choices = []        # the values, in display order
        self._items = []         # what the user reads, same order
        self._selection = ()
        _api.register(self._wid, 'select',
                      lambda data: self._on_select(data))
        for item in optionlist:
            self.insert(END, item)

    def _normalize(self, option):
        """(value, display text) for one option, or None to skip it.

        THE DESCRIPTION BELONGS IN THE TEXT. tkinter's ListBox normalises
        through `ButtonFrame.regularize_choice`, which returns button kwargs
        with the description already folded in — `text += f" ({description})"`
        (ui_tkinter.py:3852) — and this backend's copy of that function stops
        one step earlier, at the `{'code','name','description'}` dict. So a
        3- or 4-tuple option rendered here without its description, and the
        description is usually the ITEM COUNT the chooser lists show. The
        webview ButtonFrame folds it in at its own call site (:3124); this
        did not, so the same option list read differently in a list than in
        a button frame of the same page.
        """
        if self._raw_command:
            # Legacy mode: plain strings, fed through untouched, and the
            # command wants the raw event rather than a choice.
            return option, _text_of(option)
        ck = ButtonFrame.regularize_choice(option)
        if not ck:
            return None
        if ck.get('image'):
            log.info("ListBox dropping image for {!r}".format(ck.get('code')))
        text = _text_of(ck.get('name', ck.get('code', '')))
        if ck.get('description') not in (None, ''):
            text += " ({})".format(ck['description'])
        return ck.get('code'), text

    def _on_select(self, data):
        # SEVERAL INDICES WHERE THE PAGE SENDS THEM. This stored `(idx,)`
        # unconditionally, so `curselection()` could never report more than
        # one row however the list was configured — which is the other half
        # of dropping `selectmode`. `indices` is what a multiple list sends;
        # `index` is the single-selection message, kept so nothing older
        # breaks.
        idx = data.get('index', 0)
        if 'indices' in data:
            # ASCENDING, and the callback gets the FIRST — `curselection()`
            # in Tk answers in row order, and ui_tkinter.ListBox._on_select
            # passes `self.choices[sel[0]]` (:3417). This passed the
            # last-clicked row instead, so the same two picks produced
            # different codes on the two backends.
            got = tuple(sorted(int(i) for i in (data.get('indices') or [])))
            self._selection = got
            idx = got[0] if got else idx
        else:
            self._selection = (idx,)
        if not self._command:
            return
        if self._raw_command:
            self._command(type('Event', (), dict(data))())
            return
        if not 0 <= idx < len(self.choices):
            return
        code = self.choices[idx]
        # EXACTLY ui_tkinter.ListBox._on_select's contract (:3264): the
        # callback gets the CHOICE, and `window=` is passed ONLY when a window
        # was given. That conditional is load-bearing — `ui_shell.py:3892`'s
        # `on_select(event=None)` takes one positional and no window, and
        # reads curselection() itself, so passing window= unconditionally
        # (as this did for about ten minutes) raises TypeError there.
        # `self._selection` is set above, before the callback, because that
        # call site depends on curselection() already being current.
        if self._window is not None:
            self._command(code, window=self._window)
        else:
            log.info("ListBox {}: running command with code={!r}"
                     "".format(self._wid, code))
            self._command(code)

    def choice(self, index):
        """The value behind a row, as opposed to get()'s display text."""
        if 0 <= index < len(self.choices):
            return self.choices[index]
        return None

    def curselection(self):
        return self._selection

    def get(self, first, last=None):
        """Tk's `Listbox.get`: one row's text, or a TUPLE of rows.

        `'end'` IS AN INDEX. `get(0, 'end')` is how a caller reads the whole
        list — the new-language page does it to size the list to its longest
        entry (ui_shell.py:4145) — and this computed `last + 1` on the
        string, raising TypeError. `show_possibles` caught it and logged it,
        so the items appeared and the `configure(width=…, height=…)` on the
        next line never ran: both lists stayed 10 characters wide and one
        row tall (Kent, 2026-09-22, "not fixed", after the page-side height
        handler had been added). Tk also accepts `'end'` as `first`."""
        n = len(self._items)
        first = n - 1 if first in (END, 'end') else int(first)
        if last is None:
            if 0 <= first < n:
                return self._items[first]
            return ''
        last = n - 1 if last in (END, 'end') else int(last)
        return tuple(self._items[max(first, 0):last + 1])

    def insert(self, index, *elements):
        """Add rows, keeping VALUES and DISPLAY TEXT in step.

        THE COMMAND COULD NEVER FIRE until this normalised. `_normalize`
        existed, the class docstring described the two parallel lists, and
        `_on_select` guards on `0 <= idx < len(self.choices)` — but insert
        appended to `self._items` only, so `self.choices` stayed empty for
        the life of every list and that guard rejected every selection. The
        page showed the picks (the rows highlight in JS, locally) while
        Python heard nothing at all: Kent's gallery, 2026-09-14, two rows
        ticked beside "list selection: (none)".
        """
        for elem in elements:
            norm = self._normalize(elem)
            if norm is None:
                continue
            code, text = norm
            if index == END or index == 'end':
                self.choices.append(code)
                self._items.append(text)
            else:
                self.choices.insert(index, code)
                self._items.insert(index, text)
                index += 1
        self._push_items()

    def delete(self, first, last=None):
        if last is None:
            last = first
        if first == 0 and (last == END or last == 'end'):
            self._items.clear()
            self.choices.clear()
        else:
            del self._items[first:last + 1]
            del self.choices[first:last + 1]
        # A stale selection would index rows that are gone.
        self._selection = ()
        self._push_items()

    def _push_items(self):
        """Send the items as DISPLAY TEXT.

        `json.dumps(self._items)` sent the raw objects, which either raises
        (not JSON-serialisable) or ships whatever the caller happened to have
        stringified — and language options were reaching the page as object
        reprs rather than names. tkinter renders these correctly (confirmed
        2026-09-08), so this is a webview-side defect.

        `_text_of` resolves Variables and falls back to str(), so a class with
        a sensible __str__ displays properly and one without shows something
        obviously wrong rather than crashing the list. The real fix for the
        latter is at the CALL SITE — an option list should carry display
        names — see agenda/language_options_show_objects.md."""
        wv = getattr(self, '_wv_window', None)
        texts = [_text_of(item) for item in self._items]
        _js(wv, f'updateProp({self._wid}, "items", {json.dumps(texts)})')


class Combobox(_WebviewWidget):
    def __init__(self, parent, *args, **kwargs):
        font = kwargs.pop('font', 'default')
        optionlist = kwargs.pop('optionlist', [])
        self._command = kwargs.pop('command', None)
        # THE VARIABLE WAS NEVER TAKEN OUT OF kwargs AT ALL — so it went
        # through as an unknown prop, and `_on_select` set only the private
        # `_value`. The box displayed the user's pick while the variable it
        # was built with stayed empty, which is worse than not working:
        # `frontend/gallery.py` showed "choice 3" in the control and
        # `combo: ''` beside it (Kent, 2026-09-14). Every caller that reads
        # the variable rather than calling `get()` saw nothing — and that is
        # how `testapp` uses it, and `ui_shell.py:3347`'s language picker.
        self._variable = kwargs.pop('textvariable', None)
        kwargs['width'] = kwargs.pop('width', 20)
        kwargs['font'] = font
        super().__init__(parent, widget_type='combobox', **kwargs)
        self._value = ''
        self._options = list(optionlist)
        _api.register(self._wid, 'select',
                      lambda data: self._on_select(data.get('value', '')))
        # TYPING, WHICH IS NOT CHOOSING. The page reports keystrokes
        # separately from picks (widgets.js) so that a caller whose `command`
        # means "this is the answer" is not called on every character — an
        # editable field that commits on selection closed after ONE keystroke
        # otherwise, so a second character could not be typed (Kent,
        # 2026-09-16). The variable still tracks the text, which is what a
        # textvariable is for; only `select` runs the command.
        _api.register(self._wid, 'typed',
                      lambda data: self._on_typed(data.get('value', '')))
        if self._options:
            wv = getattr(self, '_wv_window', None)
            _js(wv, f'updateProp({self._wid}, "items", {json.dumps(self._options)})')
        # A variable that already holds one of the options selects it, as
        # tkinter's does — otherwise the control and the variable disagree
        # from the first paint.
        if self._variable is not None:
            try:
                held = self._variable.get()
            except Exception:
                held = None
            if held:
                self.set(held)
            # AND TRACK IT AFTERWARDS. ttk's Combobox follows its
            # textvariable for the life of the widget; this read it once at
            # construction, so a caller that set the variable later —
            # restoring a saved pick, or clearing the field — changed
            # nothing on screen. Same fix Label and EntryField already have.
            #   The guard is what stops the loop: `set()` writes the
            # variable back, and without the comparison that write would
            # re-enter here.
            def _to_dom(*_args):
                try:
                    now = self._variable.get() or ''
                except Exception:
                    return
                if now != self._value:
                    self.set(now)
            try:
                self._variable.trace_add('write', _to_dom)
            except Exception as e:
                log.info("Combobox {}: could not trace its variable ({!r})"
                         "".format(self._wid, e))

    def _on_select(self, value):
        self._value = value
        if self._variable is not None:
            try:
                self._variable.set(value)
            except Exception as e:
                log.info("Combobox {}: could not set its variable ({!r})"
                         "".format(self._wid, e))
        if self._command:
            self._command(None)

    def _on_typed(self, value):
        """Keystrokes: track the text, DO NOT run the command.

        A `textvariable` follows what is in the field, so this has to reach
        the variable — but the command means "this is the answer", and
        running it per character closed an editable field on the first
        keystroke (Kent, 2026-09-16). See the `typed` event in widgets.js."""
        self._value = value
        if self._variable is not None:
            try:
                self._variable.set(value)
            except Exception as e:
                log.info("Combobox {}: could not set its variable ({!r})"
                         "".format(self._wid, e))

    def get(self):
        return self._value

    def set(self, value):
        self._value = value
        if self._variable is not None:
            try:
                self._variable.set(value)
            except Exception as e:
                log.info("Combobox {}: could not set its variable ({!r})"
                         "".format(self._wid, e))
        wv = getattr(self, '_wv_window', None)
        _js(wv, f'updateProp({self._wid}, "value", {json.dumps(value)})')


class SearchableComboBox(Combobox):
    """NOT IMPLEMENTED, and it now says so — as tkinter's does.

    `ui_tkinter.SearchableComboBox` raises NotImplementedError from its
    __init__ ("pasted from coderslegacy.com, never adapted"). This was
    `pass`, i.e. a plain Combobox with no search box and no filtering: a
    caller would get a control that looked like the thing it asked for and
    silently was not. A stub that renders something plausible is worse than
    one that raises, because the failure moves from the call site to the
    user's hands.

    The filter-as-you-type behaviour it is meant to have does exist in the
    browser: an <input> with a <datalist> narrows its dropdown as you type,
    which is what `Combobox(state='normal')` builds here. Whoever adapts
    this class should start there rather than from the tkinter paste.
    """

    def __init__(self, parent, *args, **kwargs):
        raise NotImplementedError(
            "SearchableComboBox is not yet adapted for this project. "
            "Use Combobox instead (state='normal' is editable here).")


class Menu:
    def __init__(self, parent, **kwargs):
        self.parent = parent
        self._items = []
        self._exists = True
        self._wid = _next_wid()
        # BOTH DROPPED ON PURPOSE. `tearoff` is Tk's detachable-menu handle,
        # which has no browser equivalent and which this app always sets to
        # 0 anyway. `font` on a MENU is the one place a font is not the
        # caller's business here: `.wv-menu` is styled by the stylesheet
        # alongside the rest of the chrome, so honouring a per-menu font
        # would make one menu differ from the others for no reason a user
        # asked for. (An option dropped with no comment is indistinguishable
        # from an oversight — tests/manual/dropped_options_sweep.py.)
        kwargs.pop('tearoff', None)
        kwargs.pop('font', None)
        # `sticky=True`: the posted element is NOT removed when an item is
        # clicked, so the user can click several in a row; a mousedown
        # outside it still dismisses it. The transcriber's tone-beep
        # settings want this (Kent, 2026-09-22: change, play, keep
        # adjusting). ui_tkinter.Menu gives the same behaviour by
        # re-posting after each command.
        self._sticky = kwargs.pop('sticky', False)
        # Inherit wv_window
        if hasattr(parent, '_wv_window'):
            self._wv_window = parent._wv_window
        elif hasattr(parent, 'parent') and hasattr(parent.parent, '_wv_window'):
            self._wv_window = parent.parent._wv_window

    def pad(self, label):
        w = 5
        if len(label) < w:
            spaces = " " * (w - len(label))
            label = spaces + label + spaces
        return label

    def add_command(self, label, command):
        label = self.pad(label)
        self._items.append(('command', label, command))

    def add_cascade(self, label, menu):
        label = self.pad(label)
        self._items.append(('cascade', label, menu))

    def insert_cascade(self, label, menu, index):
        label = self.pad(label)
        # A LABEL THAT IS NOT THERE GIVES NO INDEX. `redoadvanced` does
        # `i = self.index(title)` and passes it straight back here, so a menu
        # rebuilt before that entry exists would hand us None and
        # `list.insert(None, …)` raises. Append instead: the ordering is a
        # preference, the crash is not.
        if not isinstance(index, int):
            self._items.append(('cascade', label, menu))
        else:
            self._items.insert(index, ('cascade', label, menu))

    def add_separator(self):
        """A rule between groups of entries.

        MISSING UNTIL 2026-09-24, and it stopped the menu bar dead: building
        the tree calls this seven times, so `Menus(self)` raised
        AttributeError before any of it could be drawn. Tk has it, the app
        uses it, and the webview `Menu` simply never had one."""
        self._items.append(('separator', '', None))

    def index(self, label):
        """Position of the entry with this LABEL, or None.

        Labels are padded by `pad()` on the way in, so the comparison strips —
        callers pass the text they wrote, not the text we stored."""
        want = str(label).strip()
        for i, (_kind, text, _target) in enumerate(self._items):
            if str(text).strip() == want:
                return i
        return None

    def delete(self, first, last=None):
        """Remove entries, addressed by label or by index, as Tk's does.

        `redoadvanced` deletes the Advanced cascade by label and rebuilds it
        at the index it had, which is the whole reason `index` and this exist
        as a pair."""
        start = self.index(first) if isinstance(first, str) else first
        if not isinstance(start, int):
            return
        if last is None:
            end = start
        else:
            end = self.index(last) if isinstance(last, str) else last
        if not isinstance(end, int):
            end = start
        del self._items[start:end + 1]

    def spec(self, path=()):
        """This menu as a JSON-safe nested tree, commands addressed by PATH.

        ONE SERIALISATION FOR THE POPUP AND THE BAR, so they cannot drift
        apart — which is exactly how the cascade bug arrived. `add_cascade`
        stored items happily while `tk_popup` rendered only `kind ==
        'command'`, so every submenu in the app was accepted and silently not
        drawn (found 2026-09-24, `agenda/webview_menubar_and_cascades.md`).
        Two renderers, one of which knew about half the item kinds.

        A command's address is its path from the root — `[0, 2]` is the third
        item of the first submenu — because an index alone cannot name
        anything below the top level."""
        out = []
        for i, (kind, label, target) in enumerate(self._items):
            here = list(path) + [i]
            if kind == 'separator':
                out.append({'kind': 'separator', 'label': '', 'path': here})
            elif kind == 'cascade' and hasattr(target, 'spec'):
                out.append({'kind': 'cascade', 'label': label,
                            'path': here, 'items': target.spec(here)})
            elif kind == 'cascade':
                # A cascade whose menu is not one of ours: show the label
                # disabled rather than dropping it, so it is visibly wrong
                # instead of invisibly absent.
                out.append({'kind': 'disabled', 'label': label, 'path': here})
            elif target is None:
                # A LABEL, NOT AN ACTION. `Menus.__init__` adds the open
                # filename as a top-level entry with `cmd=None`, so clicking
                # it logged "nothing to run at path [2]" as though something
                # had gone wrong (Kent, 2026-09-24). It renders inert instead,
                # and sends nothing.
                out.append({'kind': 'disabled', 'label': label, 'path': here})
            else:
                out.append({'kind': 'command', 'label': label, 'path': here})
        return out

    def command_at(self, path):
        """The callable a `spec()` path names, or None."""
        menu, cmd = self, None
        for step in path or []:
            items = getattr(menu, '_items', None)
            if not items or not (0 <= step < len(items)):
                return None
            kind, _label, target = items[step]
            if kind == 'cascade':
                menu, cmd = target, None
            else:
                cmd = target
        return cmd

    def tk_popup(self, x, y):
        """Show the menu at (x, y) as a positioned div.

        FROM `spec()`, LIKE THE BAR. This used to build its own rows with an
        f-string and an `if kind == 'command'`, so every cascade was stored
        and never drawn — submenus were missing from every context menu in the
        app, silently (2026-09-24). Rendering is now `postMenu` in widgets.js,
        shared with the menu bar, and a click comes back as a PATH rather than
        an index because an index cannot name anything below the top level.

        It also means labels are no longer interpolated into markup: they come
        from translations and lexical data, and `postMenu` sets them with
        `textContent`."""
        wv = getattr(self, '_wv_window', None)
        if not wv:
            return

        def on_menuclick(data):
            cmd = self.command_at(data.get('path') or [])
            if callable(cmd):
                try:
                    cmd()
                except Exception:
                    import traceback
                    log.error("menu command failed:\n%s",
                              traceback.format_exc())
            else:
                log.info("menu: nothing to run at path %r", data.get('path'))
        _api.unregister(self._wid)
        _api.register(self._wid, 'menuclick', on_menuclick)
        _js(wv, 'postMenu({}, {}, {}, {}, {})'.format(
            self._wid, json.dumps(self.spec()), int(x), int(y),
            'true' if self._sticky else 'false'))

    def destroy(self):
        self._exists = False
        wv = getattr(self, '_wv_window', None)
        _js(wv, f'destroyWidget({self._wid})')


class Scrollbar(_WebviewWidget):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, widget_type='frame', **kwargs)


class Popup(_WebviewWidget):
    """A panel at the pointer for a handful of controls that belong to one
    gesture; grid `ui.Button`/`ui.Label` into it as into a frame. Stays
    through clicks on its own controls, goes away on a click anywhere else
    (like a context menu) or on Escape — Kent, 2026-09-22, on the tone-beep
    settings: `-|pitch|+` on three rows, "go away on a click anywhere else".

    AN ELEMENT IN THE PAGE, NOT A WINDOW. A Wayland client may not place a
    window, and this must appear at the pointer, so it is a fixed-position
    element inside the window that holds it — the same shape as `Menu`'s
    posted list, which is why the dismissal is the same. `x`/`y` are page
    coordinates, which is what the events this backend delivers carry as
    `x`/`y`. Never gridded into its parent (`gridwait`): the page positions
    it. The tkinter `Popup` is an undecorated toplevel under a local grab,
    for the same reason the other way round.

    The page tells Python when it dismissed the element ('dismiss'), so a
    caller's `on_dismiss` runs and this object stops claiming to exist."""

    def __init__(self, parent, x, y, on_dismiss=None, **kwargs):
        kwargs['gridwait'] = True
        kwargs['popup_x'] = int(x)
        kwargs['popup_y'] = int(y)
        self._on_dismiss = on_dismiss
        super().__init__(parent, widget_type='popup', **kwargs)
        _api.register(self._wid, 'dismiss', lambda data: self._dismissed())

    def _dismissed(self):
        if not self._exists:
            return
        self._exists = False
        try:
            if self.parent and self in self.parent._children:
                self.parent._children.remove(self)
        except Exception:
            pass
        _api.unregister(self._wid)
        if callable(self._on_dismiss):
            try:
                self._on_dismiss()
            except Exception as e:
                log.info("popup {}: on_dismiss failed ({!r})".format(self._wid, e))

    def dismiss(self):
        """Take it down from Python; the page's listeners fall away with it."""
        self.destroy()


class ScrollingFrame(Frame):
    def __init__(self, parent, *args, **kwargs):
        # A CALLER'S OWN HEIGHT WINS over the stylesheet's cap. In tkinter
        # this is rows of text; here it becomes a max-height in `em`, so a
        # caller asking for 4 rows gets roughly four rows rather than the
        # generic 60vh.
        height = kwargs.pop('height', None)
        # THE CLASS THE STYLESHEET IS WRITTEN FOR. Every Frame subclass is
        # created with widget_type='frame', so this arrived as a plain
        # `wv-frame` and `.wv-scrolling-frame` matched nothing — the rule had
        # been dead since it was written. Without it the box has no height
        # cap, so `overflow:auto` never engages and twenty rows render as
        # twenty rows.
        kwargs['cssclass'] = ' '.join(
            filter(None, [kwargs.pop('cssclass', ''), 'wv-scrolling-frame']))
        super().__init__(parent, *args, **kwargs)
        if height:
            try:
                self.configure(max_height_em=float(height) * 1.6)
            except Exception as e:
                log.info("ScrollingFrame {}: could not use height={!r} ({!r})"
                         "".format(self._wid, height, e))
        self.content = Frame(self)  # Inner frame for children

    def windowsize(self, event=None):
        # STILL A NO-OP, but not for the reason first given. The comment here
        # said "the browser sizes its own box", and for WIDTH that is true.
        # For HEIGHT it is not: `overflow:auto` with no cap never scrolls,
        # because the box grows to fit and so never overflows — twenty rows
        # rendered as twenty rows and the window scrolled instead (Kent,
        # 2026-09-14). The cap is now a stylesheet rule (`.wv-scrolling-frame`
        # max-height) plus the `height=` above, which is the right place for
        # a layout invariant — but it is a cap that had to be SET, not one
        # the browser supplied.
        pass
    def reflow(self):
        pass                # the browser lays the box out

    # TK'S INTERNALS ARE PART OF THE SURFACE, because callers reach for
    # them: `SortButtonFrame.reflow` calls `_do_configure_interior` on its
    # scroller, and its absence surfaced as "SortButtonFrame.reflow failed:
    # 'SortButtonFrame' object has no attribute '_do_configure_interior'"
    # (Kent's log, 2026-09-15) — caught by the caller, so the page built
    # without its reflow and said nothing a reader could act on. Nothing to
    # do here for the same reason `reflow` does nothing: the browser lays
    # the box out and `overflow:auto` needs no scrollregion recomputed.
    def _do_configure_interior(self, event=None):
        pass

    def _configure_interior(self, event=None):
        pass

    def _configure_canvas(self, event=None):
        pass

    # SCROLLING IS REAL WORK, not a no-op. `main.py:1083` and
    # `tasks/tasks.py:914` scroll to the bottom so the newest line is the one
    # you see — a message window that does not is a message window showing
    # old news — and `alphabet_comparison.py:392-393` resets to the top.
    # These were `pass`, so none of it happened.
    def tobottom(self):
        wv = getattr(self, '_wv_window', None)
        _js(wv, 'var e=_widgets.get({}); if(e) e.scrollTop=e.scrollHeight;'
                ''.format(self._wid))

    def totop(self):
        wv = getattr(self, '_wv_window', None)
        _js(wv, 'var e=_widgets.get({}); if(e) e.scrollTop=0;'
                ''.format(self._wid))

    # ACCEPTED AND IGNORED, deliberately — not "not written yet".
    # tkinter suspends its <Configure> handler around a bulk update because
    # each reflow costs a synchronous X round trip (see the scrollframe work
    # in agenda/scrollframe_sizes_from_layout.md). A browser reflows its own
    # layout and there is nothing here to suspend, so these are no-ops with a
    # reason rather than gaps. The app calls both, and before this the calls
    # raised inside callbacks that swallow it.
    def suspend_configure(self):
        pass
    def resume_configure(self, reflow=True):
        pass
    def hwinfo(self):
        """tkinter reports the scroller's own measurements here; nothing in
        this backend measures them, and no caller uses the result for more
        than logging."""
        return {}


class ButtonFrame(Frame):
    _button_kwargs = {'command', 'cmd', 'choice', 'window', 'font', 'text',
                      'image', 'compound', 'norender', 'wraplength',
                      'image_pixels', 'image_scaleto', 'anchor', 'relief',
                      'state', 'textvariable'}

    @staticmethod
    def regularize_choice(choice):
        """Normalize an option into {'code': ..., 'name': ...} dict."""
        if isinstance(choice, (str, int)):
            return {'code': choice, 'name': str(choice)}
        if isinstance(choice, dict):
            c = dict(choice)
            if c.get('code') in (None, 'Null', 'None'):
                c['name'] = c.get('name', 'None of These')
            else:
                c['name'] = c.get('name', str(c['code']))
            return c
        if isinstance(choice, tuple):
            if len(choice) == 4:
                return {'code': choice[0], 'name': choice[1],
                        'description': choice[2], 'image': choice[3]}
            elif len(choice) == 3:
                return {'code': choice[0], 'name': choice[1],
                        'description': choice[2]}
            elif len(choice) == 2:
                return {'code': choice[0], 'name': choice[1]}
        log.info(f"Problem setting up {choice=} ({type(choice)=})")
        return None

    def __init__(self, parent, *args, **kwargs):
        self.optionlist = kwargs.pop('optionlist', [])
        btn_command = kwargs.pop('command', kwargs.pop('cmd', None))
        btn_window = kwargs.pop('window', None)
        btn_font = kwargs.pop('font', None)
        # BUTTON KWARGS ARE HELD FOR THE BUTTONS, not thrown away. They were
        # popped here so they would not reach Frame — correct — and then
        # dropped, which is not: tkinter's ButtonFrame reserves exactly these
        # onto itself and hands them back to every Button it builds
        # (`Button.restore_kwargs`, :3885). So a frame built with
        # `compound='left'` or `image_pixels=24` produced plain text buttons
        # under webview. `alphabet_chart.py:706` is such a call.
        btn_shared = {}
        for k in ('image', 'compound', 'norender', 'wraplength',
                  'image_pixels', 'image_scaleto', 'anchor', 'relief',
                  'state', 'textvariable'):
            if k in kwargs:
                btn_shared[k] = kwargs.pop(k)
        # 'choice' and 'text' are per-option and come from the option itself;
        # a frame-level one would name every button the same.
        for k in ('choice', 'text'):
            kwargs.pop(k, None)
        # Extract brow/bcolumn → row/column for buttons
        btn_grid = {}
        for k in list(kwargs):
            if k.startswith('b') and k[1:] in self._gridkwargs:
                btn_grid[k[1:]] = kwargs.pop(k)
        super().__init__(parent, *args, **kwargs)
        self.buttons = {}
        if not self.optionlist:
            return
        for i, choice in enumerate(self.optionlist):
            if not choice:
                continue
            ck = self.regularize_choice(choice)
            if not ck:
                continue
            btn_text = ck['name']
            if 'description' in ck:
                btn_text += f' ({ck["description"]})'
            btn_kw = {'text': btn_text, 'choice': ck['code'],
                      'command': btn_command, 'row': i, 'column': 0}
            btn_kw.update(btn_shared)
            # THE OPTION'S OWN PICTURE, which tkinter passes straight through
            # (`**choice_kwargs` at :3893) and this dropped: a 4-tuple option
            # carries an image, and the alphabet chart's glyph list is built
            # that way. A per-option image beats a frame-level one.
            if ck.get('image'):
                btn_kw['image'] = ck['image']
            if btn_window is not None:
                btn_kw['window'] = btn_window
            if btn_font:
                btn_kw['font'] = btn_font
            btn_kw.update(btn_grid)
            if 'row' not in btn_grid:
                btn_kw['row'] = i
            self.buttons[ck['code']] = Button(self, **btn_kw)


class ScrollingButtonFrame(ScrollingFrame):
    def __init__(self, parent, *args, **kwargs):
        optionlist = kwargs.pop('optionlist', [])
        command = kwargs.pop('command', kwargs.pop('cmd', None))
        window = kwargs.pop('window', None)
        font = kwargs.pop('font', None)
        # HELD FOR THE BUTTONS, not discarded — the same fault this class's
        # own ButtonFrame had, still live here after that one was fixed, and
        # found by tests/manual/dropped_options_sweep.py within minutes of
        # writing it (2026-09-14). These are button options, so they must not
        # reach the Frame; they were popped for that reason and then thrown
        # away, so `ScrollingButtonFrame(image='icon', compound='right',
        # image_pixels=24)` built twenty buttons with no picture on any of
        # them. `frontend/gallery.py`'s Scrolling tab asks for exactly that.
        btn_shared = {}
        for k in ('image', 'compound', 'norender', 'wraplength',
                  'image_pixels', 'image_scaleto', 'anchor', 'relief',
                  'state', 'textvariable'):
            if k in kwargs:
                btn_shared[k] = kwargs.pop(k)
        # Per-option, and a frame-level one would name every button alike.
        for k in ('choice', 'text'):
            kwargs.pop(k, None)
        btn_grid = {}
        for k in list(kwargs):
            if k.startswith('b') and k[1:] in self._gridkwargs:
                btn_grid[k[1:]] = kwargs.pop(k)
        super().__init__(parent, *args, **kwargs)
        bf_kw = {'optionlist': optionlist, 'command': command}
        bf_kw.update(btn_shared)
        if window is not None:
            bf_kw['window'] = window
        if font:
            bf_kw['font'] = font
        bf_kw.update({f'b{k}': v for k, v in btn_grid.items()})
        self.bf = ButtonFrame(self.content, **bf_kw)
        self.buttons = self.bf.buttons


class ScrollingListBox(Frame):
    """A ListBox that scrolls — `ui_tkinter.ScrollingListBox` is "Frame
    containing a ListBox + vertical Scrollbar", and this is the same shape.

    WAS A STUB SUBCLASSING ScrollingButtonFrame, which is not a smaller
    version of this widget but a different one: it rendered a column of
    BUTTONS where the caller asked for a list, so selection, multi-select and
    `curselection()` were all absent and what appeared instead looked
    deliberate (Kent's gallery, 2026-09-14 — twenty items as twenty buttons).
    A stub that renders something plausible is worse than one that raises.

    No separate scrollbar widget: `.wv-listbox` already has `overflow-y:auto`
    and takes its height from `height`, so the browser draws the scrollbar.
    That is the one place in this class where "the engine does it" is true.
    """

    def __init__(self, parent, *args, **kwargs):
        # Grid kwargs place THIS frame; everything else belongs to the list —
        # the same split ui_tkinter.ScrollingListBox makes, and for the same
        # reason: forwarding row/column to both made every call with a
        # row/column a TypeError.
        lb_kw = {k: kwargs.pop(k) for k in list(kwargs)
                 if k not in self._gridkwargs}
        super().__init__(parent, *args, **kwargs)
        self.listbox = ListBox(self, row=0, column=0, sticky='nsew', **lb_kw)
        # The tkinter one is used interchangeably with its ListBox by
        # callers, so the list's own surface has to be reachable here.
        for name in ('choices', 'curselection', 'get', 'insert', 'delete',
                     'choice', 'selection_set', 'select_clear', 'size',
                     'see', 'index'):
            attr = getattr(self.listbox, name, None)
            if attr is not None:
                setattr(self, name, attr)


class RadioButtonFrame(Frame):
    """A frame of radio buttons, one per option.

    IT BUILT NOTHING. `optionlist`, `variable` and `horizontal` were popped
    and thrown away and the result was an empty Frame — so a page asking for
    a set of radio buttons got a blank space, with no error anywhere: the
    eleventh instance of a stub that renders something plausible instead of
    raising. `ui_shell.py:4252` builds one.

    Parity with ui_tkinter.RadioButtonFrame (:4606), including its one
    surprise: `sticky` belongs to the BUTTONS, not to the frame — it is
    popped before the frame is gridded and handed to each child.
    """

    def __init__(self, parent, *args, **kwargs):
        optionlist = kwargs.pop('optionlist', []) or []
        horizontal = kwargs.pop('horizontal', False)
        variable = kwargs.pop('variable', None)
        # Reserved for the buttons, as tkinter's reserve/restore pair does.
        btn_kw = {}
        for k in ('indicatoron', 'command', 'font'):
            if k in kwargs:
                btn_kw[k] = kwargs.pop(k)
        sticky = kwargs.pop('sticky', 'w')
        super().__init__(parent, *args, **kwargs)
        self.optionlist = optionlist
        self.buttons = []
        row = column = 0
        for opt in optionlist:
            if isinstance(opt, tuple) and len(opt) == 2:
                value, name = opt
            else:
                name = value = opt
            kw = dict(btn_kw)
            # Only if there IS one: RadioButton.__init__ pops with a default,
            # and an explicit None replaces that default with None rather
            # than falling back to it — so the button would keep a variable
            # of None and raise on the first click.
            if variable is not None:
                kw['variable'] = variable
            self.buttons.append(RadioButton(
                self, value=value, text=nfc(_text_of(name)),
                row=row, column=column, sticky=sticky, **kw))
            if horizontal:
                column += 1
            else:
                row += 1


class ContextMenu:
    """Right-click menu on a window. WAS A FOUR-METHOD STUB, and the stub is
    how you lost the route to Sound Settings under webview (Kent, 2026-09-11:
    "I'm talking about the context menu I used to get to the sound settings").

    `Menu` below has worked all along — `add_command`, `tk_popup` positioning a
    `.wv-menu` div, dismiss-on-outside-click, and the CSS for it. Nothing was
    missing from the MENU. What was missing was every part of making one
    appear:

    1. **`parent.context = self` was never set.** `ui_tkinter.ContextMenu`
       does it (:3714) and both call sites rely on it: `ui_shell.py:2979` and
       `:3733` just construct `ui.ContextMenu(self)` and then everything else
       reaches the object through `window.context`. So `self.context.menuinit()`
       (`ui_shell.py:189`, `:2221`) and `self.context.menuitem(...)`
       (`tasks/sound.py:33`) had nothing to find.
    2. **No `menuitem`.** The method every `setcontext()` in the app calls to
       add its entries.
    3. **No `do_popup`, and nothing bound to right-click.** So no gesture could
       have produced a menu even if one had been built.

    TENTH gap of the shape recorded at `bind_all` above, and the worst of them
    for reachability: a stub whose methods all return None cannot raise, so
    every `setcontext()` in the app ran to completion and the menu silently did
    not exist. Sound Settings has no other route from a task window.

    `<<ContextMenu>>` is the tkinter virtual event the Tk version binds, now
    mapped in widgets.js — so app code that binds that name works here too,
    instead of registering a DOM listener for an event called
    "<<ContextMenu>>" that nothing fires.
    """

    def __init__(self, parent, *args, **kwargs):
        self.parent = parent
        self.parent.context = self
        self.popup = False
        # NOT BOUND DURING WINDOW CONSTRUCTION. Binding here issued one extra
        # `evaluate_js` per window while its page was still loading, and
        # QtWebEngine 6.11.2 segfaulted on every startup as a result — three
        # runs, three crashes, all in pywebview's own `generate_js_object`
        # injection. Commenting out this one line let Qt through, which is
        # what identified it (Kent, 2026-09-11: "But this was working just
        # fine until this last hour. you sure this is not on our end?" — it
        # was on our end). Full analysis: agenda/webview_when_to_finish.md,
        # CORRECTION (6).
        #   So wait for the page. `_on_loaded` runs these hooks alongside the
        # theme and page-name pushes, which is where per-window JS belongs.
        loaded = getattr(parent, '_wv_loaded', None)
        if loaded is not None and not loaded.is_set():
            # __dict__ directly: the task/window bridge's __getattr__ would
            # chase a missing attribute across to the task and back.
            parent.__dict__.setdefault('_on_loaded_hooks',
                                       []).append(self.updatebindings)
        else:
            self.updatebindings()

    def menuinit(self):
        """Fresh menu, so a context change does not append to the old one."""
        try:
            old = getattr(self, 'menu', None)
            if old is not None:
                old.destroy()
        except Exception as e:
            log.info("couldn't destroy the previous context menu ({})".format(e))
        self.menu = Menu(self.parent)

    def menuitem(self, msg, cmd):
        """Add an entry, creating the menu if this is the first one — the same
        contract as the tkinter version, which recovers from a destroyed menu
        the same way."""
        if getattr(self, 'menu', None) is None:
            self.menuinit()
        try:
            self.menu.add_command(label=msg, command=cmd)
        except AttributeError:
            self.menuinit()
            self.menu.add_command(label=msg, command=cmd)

    def updatebindings(self):
        # On a window, bindEvent falls back to `document`, so this catches a
        # right-click anywhere in the page — which is what the Tk version gets
        # from binding the virtual event on the window.
        try:
            self.parent.bind('<<ContextMenu>>', self.do_popup)
        except Exception as e:
            log.info("couldn't bind the context menu ({})".format(e))

    def do_popup(self, event=None):
        if getattr(self, 'menu', None) is None:
            # No setcontext() has run yet, or it ran before this menu existed.
            # Same recovery as tkinter's, and the reason it is here: the
            # window's own setcontext walks the task mixins and is what knows
            # which entries belong on this page.
            try:
                self.parent.setcontext()
            except Exception as e:
                log.info("setcontext failed for the context menu ({})"
                        .format(e))
        if getattr(self, 'menu', None) is None or not self.menu._items:
            log.info("right-click with no context-menu entries on %s",
                    type(self.parent).__name__)
            return
        # PAGE coordinates, not `x_root`. The event this backend delivers
        # carries clientX/clientY as `x`/`y` (see _WebviewWidget.bind), and
        # `tk_popup` positions an absolutely-placed div, so page coordinates
        # are what it wants. `x_root` is accepted first for the tkinter
        # callers that pass a synthetic event.
        x = getattr(event, 'x_root', None) or getattr(event, 'x', 0) or 0
        y = getattr(event, 'y_root', None) or getattr(event, 'y', 0) or 0
        # NEVER TWO POSTED AT ONCE — the same rule `sort_ui.popup` states for
        # the other context menu (:169). `tk_popup` now clears the previous
        # element itself, so this is the belt to that braces; both are cheap
        # and the failure they prevent is two menus on screen at once.
        self.undo_popup()
        self.menu.tk_popup(x, y)
        self.popup = True

    def undo_popup(self, event=None):
        if not self.popup:
            return
        try:
            if getattr(self, 'menu', None) is not None:
                self.menu.destroy()
        except Exception as e:
            log.info("couldn't dismiss the context menu ({})".format(e))
        self.popup = False


class ToolTip:
    """Hover text. The CSS class (.wv-tooltip) has existed all along and
    nothing ever created one, so ~38 call sites produced nothing."""

    def __init__(self, widget, text=''):
        self.widget = widget
        self.text = text
        self._apply()

    def _apply(self):
        wid = getattr(self.widget, '_wid', None)
        if wid is None:
            return
        wv = getattr(self.widget, '_wv_window', None)
        _js(wv, 'setTooltip({}, {})'.format(wid, json.dumps(nfc(self.text or ''))))

    def settext(self, text):
        self.text = text
        self._apply()

    # Some call sites build the tooltip then update it; others expect the
    # tkinter helper's show/hide entry points. Hovering is the browser's job,
    # so these exist to keep those call sites working, not to do anything.
    def showtip(self, event=None):
        pass

    def hidetip(self, event=None):
        pass


# ── Toplevel / Window ─────────────────────────────────────────────────

class Toplevel(_WebviewWidget):
    """A secondary window — creates a new pywebview window."""

    # A window is not a DOM element, so a widget parented to one has no DOM
    # parent to find — normal, and the page must not warn about it. This was
    # declared False on the base with a comment saying Toplevel and Root set
    # it True, and then never set: the third gate this session that always
    # answered no. The symptom was the console warning firing for every
    # window-parented widget, i.e. for the expected case.
    is_window = True

    def __init__(self, parent, *args, **kwargs):
        self._wv_window = None  # Will be set after webview.create_window
        self.parent = parent
        self._wid = _next_wid()
        self._children = []
        self._exists = True
        self._bindings = {}
        self._config = {}
        self._props = {}
        self._has_grid = False
        self._grid_opts = {}
        self._gridwait = False
        self._grid_visible = True
        self.mainwindow = False
        self.waitcancelled = False
        self._wv_deferred = []
        self._wv_loaded = threading.Event()
        self._wv_js_queue = []  # per-window JS queue
        # Guards the queue AND the flag together — the pair is what has to be
        # consistent, or a call can be queued into a queue nobody will drain
        # again. See `_js` and `_drain_wv_js_queue`.
        self._wv_queue_lock = threading.RLock()

        # WHY THIS IS NOT JUST A LATER hide(): `withdrawn` was ignored
        # entirely, so a window asked for hidden was created VISIBLE and only
        # hidden once its page had loaded — which is seconds later, because
        # _wv_call defers until _on_loaded. Kent, 2026-09-05: "I saw flashes
        # that looked like windows building, but none stuck around long
        # enough to see clearly." Every task window is built withdrawn
        # (tasks/chooser.py:527 passes withdrawn=True with the comment
        # "don't show first on boot"), so the whole startup flashed.
        # pywebview can create a window hidden, which is the honest
        # equivalent of Tk's withdrawn state at creation.
        withdrawn = bool(kwargs.pop('withdrawn', False))
        self._withdrawn = withdrawn
        # BORN FULLSCREEN, where the caller knows it is a kiosk page. See
        # `_kiosk_kwarg` for why this beats fullscreening afterwards. The
        # flag is set to match, so `takekioskscreen()` — which every such
        # window still calls, and which is the fallback when the engine
        # cannot do this — finds the state already correct and sends no
        # toggle.
        kiosk = bool(kwargs.pop('kiosk', False))
        self._born_kiosk = bool(_kiosk_kwarg(kiosk))
        self._is_fullscreen = self._born_kiosk
        # WHETHER ANYONE CAN SEE IT, tracked because a fit measured while
        # hidden is a fit measured against nothing (see fit_to_content). A
        # window asked for withdrawn starts invisible whether or not the
        # engine could honour `hidden=` at creation: the app hides it as soon
        # as the page loads either way, so "withdrawn" is the intent, and
        # intent is what the fit should wait for.
        self._wv_visible = not withdrawn
        self._refit_wanted = False
        # Kept separate from `withdrawn` ON PURPOSE: the log used to report
        # "created HIDDEN" whenever `withdrawn` was true, which stayed true
        # after hidden= was reverted — so the message claimed a state the
        # window was not in, and hid the fact that the revert had landed.
        create_hidden = bool(withdrawn and (_supports_created_hidden()
                                            or _switch('--webview-hidden')))

        # Inherit from parent
        if parent:
            for attr in ('theme', 'wraplength', 'renderer', 'exitFlag'):
                if hasattr(parent, attr):
                    setattr(self, attr, getattr(parent, attr))
            parent._children.append(self)

        self.exitFlag = ExitFlag()

        # BORN OFF-SCREEN WHEN IT IS MEANT TO BE HIDDEN, and born in the
        # THEME'S COLOUR either way. Two halves of one complaint (Kent,
        # 2026-09-15: "The first two windows show a ?grey window first on
        # top, that is then colored… would it be possible to wait to show
        # windows until they are ready? also… the second window is covering
        # the splash… We should just see the splash until the next window is
        # ready"):
        #
        #   * THE GREY is the engine's own empty page, shown for the
        #     fraction of a second before base.html and the theme arrive.
        #     pywebview can be told what colour an empty window is, and the
        #     theme knows the answer, so there is no reason for it to be grey.
        #   * THE COVERING is `hidden=` being unusable on WebKitGTK — a
        #     window created hidden there never maps at all, so every task
        #     window is created VISIBLE and hidden once its page loads. That
        #     is seconds of a blank window sitting over the splash.
        #     Creating it at a coordinate nobody can see achieves what
        #     `hidden=` would, without asking the engine to do the thing it
        #     cannot: the window IS mapped, so `show()` works later.
        #
        # Best-effort on both: a compositor that refuses client positioning
        # (native Wayland) will ignore the coordinates, and the fallback is
        # exactly today's behaviour. `_place_onscreen` puts it back.
        bg = None
        try:
            bg = self.theme.css_vars().get('background')
        except Exception:
            bg = None
        offscreen = bool(withdrawn and not create_hidden)
        self._offscreen = offscreen
        place = {}
        if offscreen:
            place = {'x': -32000, 'y': -32000}
        if bg:
            place['background_color'] = bg
        # SAID ONCE, because it halves the grey-flash question. Every new
        # window paints WHITE for a moment before its document exists
        # (Kent's recordings, one flash per window), and the document cannot
        # be the cause: `base.html` sets `background: transparent` inline,
        # ahead of both stylesheets, so what shows through is whatever is
        # BEHIND it. Either this colour never gets set, or pywebview applies
        # it to the GtkWindow and the WebView paints its own white on top.
        # This line settles the first of those.
        _say_once("windows are created with background_color={!r} (from the "
                  "theme), and the page is told the same colour in the URL "
                  "fragment — see the inline script in base.html for why "
                  "both are needed".format(bg))
        # Create a new pywebview window
        if webview:
            html_path = os.path.join(_HTML_DIR, 'base.html')
            # THE COLOUR GOES TO THE PAGE AS WELL AS TO THE WINDOW. Both are
            # needed and they cover different moments: `background_color`
            # paints the window before the web view has anything (which
            # works — Kent's log: `background_color='#ffbb99'`), and this
            # paints the DOCUMENT before either stylesheet is fetched.
            # Without it every window went theme-grey-theme, because a
            # transparent document composites onto the web view's own opaque
            # white rather than onto the window. See the inline script in
            # base.html.
            #   A FRAGMENT, so it is never sent to pywebview's http server
            # and survives a plain file path; if it is ever dropped the page
            # still loads and we are back to the flash, never to a broken
            # page.
            page_url = html_path if os.path.exists(html_path) else None
            if page_url and bg:
                try:
                    from urllib.parse import quote
                    page_url = '{}#bg={}'.format(page_url,
                                                 quote(str(bg), safe=''))
                except Exception as e:
                    log.info("could not tell the page its background colour "
                             "({!r}); it will flash white before the "
                             "stylesheet arrives".format(e))
            self._wv_window = webview.create_window(
                'A-Z+T',
                url=page_url,
                html='<div id="root"></div>' if not os.path.exists(html_path) else None,
                js_api=_api,
                width=_created_size()[0], height=_created_size()[1],
                **_kiosk_kwarg(kiosk),
                **place,
                # CREATED HIDDEN WHERE THE ENGINE SUPPORTS IT — which is
                # everywhere except WebKitGTK (see
                # _supports_created_hidden). On GTK a window created hidden
                # never appears at all, and every task window is built
                # withdrawn, so getting this wrong hides the entire UI; on
                # Windows, macOS and Qt it removes the startup flash of a
                # window appearing only to vanish.
                #
                # --webview-hidden forces it on anyway, for re-testing GTK.
                hidden=create_hidden,
                **_focus_kwarg(),
            )
            if self._wv_window:
                # The url is logged because a window pointed at nothing loads
                # pywebview's SERVER ROOT instead, which its own asset route
                # cannot serve: `GET / -> 500`, and the window shows nothing.
                # AND WHO ASKED FOR IT. Nothing named the caller, so "is
                # this window being built twice?" could not be answered from
                # a log at all — and it is the right question to ask: the
                # run window WAS being built twice until today, and Kent,
                # reading a 40fps sheet, asked the same of two more: "I
                # actually wonder if sh1.26 and sh2.15 aren't the same
                # window being built twice, like with the runwindow issue we
                # fixed earlier today" (2026-09-16).
                #   Two frames up, as in `getrunwindow`: one names the
                # constructor's caller, the one above it says which flow it
                # belongs to — which is what distinguishes two steps of one
                # page load from the same step running twice.
                try:
                    import traceback as _tb
                    frames = _tb.extract_stack()[:-1][-3:-1]
                    who = ' <- '.join('{}:{} in {}()'.format(
                                        f.filename.rsplit('/', 1)[-1],
                                        f.lineno, f.name)
                                      for f in reversed(frames))
                except Exception:
                    who = 'caller unknown'
                log.info("window {}: created {}{} as {}, asked by {}, url={}"
                         "".format(
                    self._wid,
                    'HIDDEN' if create_hidden else 'visible',
                    ' (asked withdrawn)' if withdrawn else '',
                    type(self).__name__, who,
                    html_path if os.path.exists(html_path) else '(NONE — will '
                    'load the server root and fail)'))
                _all_wv_windows.append(self._wv_window)
                _register_window_owner(self._wv_window, self)
                # POLL EITHER WAY. The else-branch used to just set
                # `_wv_loaded` with the comment "Root's on_loaded handles
                # it" — and Root's on_loaded does NOT: it pushes the theme
                # to its OWN window and flushes children's deferred calls,
                # but never runs a child's `_on_loaded`. So every Toplevel
                # created before `webview.start()` silently skipped the
                # three things that live there — the theme push, the
                # page-name push, and `_on_loaded_hooks` (where the context
                # menu's bindings are deferred to).
                #
                # Visible as: the splash showing its icon and default
                # palette but never the user's theme (Kent, 2026-09-14:
                # "icon but no theme color (either) on Splash"), which is
                # also the likeliest half of
                # agenda/webview_splash_missing_parts.md. Each pywebview
                # window is a separate document, so theme variables set on
                # one page cannot reach another.
                #
                # Polling rather than `events.loaded` for the reason the
                # other branch already gives: the event can fire before we
                # attach. It tolerates a not-yet-started webview, because
                # `evaluate_js` simply raises until then and the loop
                # retries.
                t = threading.Thread(target=self._poll_until_loaded,
                                     daemon=True)
                t.start()

    def _poll_until_loaded(self):
        """Poll the window until widgets.js is loaded, then flush JS queue."""
        import time
        for _ in range(200):  # up to 20 seconds
            time.sleep(0.1)
            try:
                r = self._wv_window.evaluate_js('typeof createWidget')
                if r == 'function':
                    self._on_loaded()
                    return
            except Exception:
                pass
        log.error(f"Toplevel window {self._wid} timed out waiting for JS load")

    def _on_loaded(self):
        """Called when this window's HTML/JS is ready."""
        log.info(f"Toplevel {self._wid} JS ready — flushing {len(self._wv_js_queue)} queued calls")
        # SEND THE BACKLOG BEFORE ANNOUNCING READINESS. This used to set the
        # flag here and flush thirty lines further down, past several
        # synchronous round trips into the engine (hooks, theme, badge) —
        # and the page build runs on another thread, so any widget created
        # across that span was sent immediately and arrived AHEAD of the
        # queued calls, its parent among them. That is the orphaned sort
        # group: a child with nothing to attach to falls back to #root and
        # lays itself out against the page. `_drain_wv_js_queue` sets the
        # flag itself, once there is nothing left to jump.
        self._drain_wv_js_queue()
        # DEFERRED WIRING — things that must wait for a live page.
        # Added 2026-09-11 because binding the context menu from
        # `TaskDressing.__init__` (i.e. during window construction) made
        # QtWebEngine segfault on every startup; see
        # agenda/webview_when_to_finish.md, CORRECTION (6). Anything that
        # needs the page to exist belongs here, with the theme and page-name
        # pushes below, rather than racing the engine's own page setup.
        for hook in list(getattr(self, '_on_loaded_hooks', ())):
            try:
                hook()
            except Exception as e:
                log.info("deferred post-load hook failed ({})".format(e))
        # Push theme
        if hasattr(self, 'theme') and self.theme:
            css_vars = self.theme.css_vars()
            if self._wv_window:
                try:
                    self._wv_window.evaluate_js(f'setThemeVars({json.dumps(css_vars)})')
                except Exception as e:
                    log.debug(f"Theme push failed: {e}")
        # Let CSS know WHICH page this is. Every window loads the same
        # base.html, so without this a stylesheet cannot tell the splash from
        # a sort board — and they want opposite treatment (one centred, one a
        # dense aligned grid). `Splash(ui.Window)` reports "splash", a task
        # window reports its own class, so this is the styling hook the port
        # needs generally rather than a one-off for the splash.
        _js(self._wv_window,
            'document.body.dataset.page={}'.format(
                json.dumps(type(self).__name__.lower())))
        # The program comes from the ROOT: `program` is not among the
        # attributes a widget inherits from its parent, so reading it off
        # `self` gave None and silently suppressed the badge even in dev —
        # a gate that always says no is not a gate.
        _badge(self._wv_window, 'window {}'.format(self._wid),
               getattr(self._find_root() or default_root(), 'program', None))
        # WATCH THE CLIENT AREA. See `installResizeReporter` in widgets.js:
        # a window that is resized and then quietly reverted logs exactly the
        # same lines as one that keeps the size, so the difference has only
        # ever been visible on screen.
        try:
            _api.register(self._wid, 'clientresize', self._report_client_resize)
            _js(self._wv_window, 'installResizeReporter({}, {})'.format(
                    self._wid,
                    'true' if _switch('--log-resizes') else 'false'))
            # WHERE A DEFINITE HEIGHT STOPS — see `_report_height_chain`.
            # Registered always, fired only under `--log-heights`.
            _api.register(self._wid, 'heightchain', self._report_height_chain)
        except Exception as e:
            log.info("window {}: could not watch the client area ({!r})"
                     "".format(self._wid, e))
        # Anything the lines above queued (they run with the page live, so
        # most went straight out) plus anything the builder added while they
        # ran. Drained, not merely sent: same reason as at the top.
        self._drain_wv_js_queue()
        # Flush deferred wv calls (title, hide/show, etc.)
        self._flush_wv_calls()
        # Widgets are in the page now, so its content has a size — fit to it.
        self.fit_to_content()
        # AND MAKE THE FIT REACHABLE BY HAND, from any window state. The
        # double-click was bound only by `takekioskscreen`, so it existed
        # exactly where the fit was least needed (a fullscreen window is
        # already the size it wants) and was missing everywhere it was:
        # an OS-maximized window has nothing to release, and a merely
        # mis-sized one has no gesture at all (agenda/webview_window_sizing.md).
        #   Same gesture, one dispatcher: release fullscreen if we are in it,
        # otherwise fit. A user who has learned "double-click fixes the
        # window" is then right in both cases.
        try:
            self.bind('<Double-Button-1>', self._dblclick_fit)
        except Exception as e:
            log.info("window {}: could not bind the fit gesture ({!r})"
                     "".format(self._wid, e))
        self._wire_default_close()

    def _wire_default_close(self):
        """Every window's close box must reach `on_quit`, as under tkinter.

        `ui_tkinter.Toplevel.post_tk_init` does exactly this in one line
        (:1395) — `self.protocol("WM_DELETE_WINDOW", self.on_quit)` — and
        this backend registered a handler only at the three call sites that
        asked for one. So most windows' close boxes went to pywebview's own
        close, which DESTROYS the window: and destroying a pywebview window
        mid-teardown is the documented SIGSEGV in `_close_native_window`.
        Kent, 2026-09-15, after clicking X on the main window: no UI, and
        `apport -p84585 -s11` — signal 11, not a clean exit.

        It had been mostly unreachable, which is why it survived: task
        windows were undecorated kiosk pages with no close box at all until
        kiosk was narrowed to run windows earlier today. Giving those windows
        their dressing back gave the user a button that crashed the app.

        A page that wants its own behaviour still calls `protocol()` and
        replaces this — `alphabet_chart.py:59` hands the close to
        `taskchooser.gettask` — which now swaps the handler rather than
        adding a second one.
        """
        if getattr(self, '_delete_handler', None) is not None:
            return          # a page got there first; leave its choice alone
        try:
            self.protocol('WM_DELETE_WINDOW', self.on_quit)
        except Exception as e:
            log.info("window {}: could not wire the default close ({!r})"
                     "".format(self._wid, e))

    def _dblclick_fit(self, event=None):
        """Double-click: leave fullscreen, or fit the window to its content."""
        if getattr(self, '_is_fullscreen', False):
            return self.releasefullscreen(event)
        _request_refit(self, 'double-click', delay=0.05)

    def fit_to_content(self):
        """Grow the window until its content fits, capped to the screen.

        WHY THIS IS NEEDED: pywebview windows are created at a fixed
        800x600 (1024x768 for the root) and nothing since has related that to
        what is in them, so the chooser opened too small and had to be
        resized by hand before its task buttons could be seen — Kent,
        2026-09-08: "will users have to ... manually move the window size and
        shape to see all the contents (as now)?" No. Under tkinter a window
        sizes to its content; this is the equivalent.

        It only ever GROWS, and only when the content actually overflows:
        `scrollWidth` of a box that fits equals its client width, so a page
        with room to spare reports no change and is left alone. Capped to
        `screen.avail*` so a long page cannot produce a window larger than
        the display — the failure mode `availablexy` used to have in reverse.
        """
        wv = getattr(self, '_wv_window', None)
        if not wv or not _started.is_set():
            return
        # A FULLSCREEN WINDOW IS ALREADY THE SIZE IT WANTS TO BE. Resizing one
        # produces the worst of both: undecorated (because fullscreen) yet not
        # filling the screen and not resizable — Kent, 2026-09-08: "my task
        # window has no decoration, and I can't change it's size", with the
        # log showing toggle_fullscreen replayed and then a resize to 918x745.
        # Kiosk mode is the deliberate default for task windows, so it wins.
        if getattr(self, '_is_fullscreen', False):
            # NOT FITTING IS NOT THE SAME AS NOT MEASURING, and conflating
            # them left the app blind on exactly its hardest pages. Kiosk is
            # the default for RUN windows, so the sort board, the macrosort
            # board and every verify list are fullscreen — and this returned
            # before the probe, so those pages produced no geometry at all.
            # Kent, 2026-09-16, on a macrosort page with two scrollbars and
            # a screen of empty space: "I can't tell if this is a recent
            # problem or not", and neither could I, because there was
            # nothing to read.
            #   So: measure and report, then stop. The resize is what must
            # not happen here (a resized fullscreen window is undecorated
            # AND not filling the screen AND not resizable — Kent,
            # 2026-09-08: "my task window has no decoration, and I can't
            # change it's size"); the measurement costs one round trip and
            # is the only diagnostic these pages have.
            log.info("window {}: fullscreen — measuring for the log, not "
                     "resizing".format(self._wid))
            self._measure_only = True
        else:
            self._measure_only = False
        # A HIDDEN WINDOW CANNOT BE MEASURED. Its page is still there, but
        # its viewport is not the size it will be when shown, and nothing
        # about a resize applied to an unmapped window survives the mapping
        # in a predictable way — so the fit was producing a size from
        # numbers that meant nothing, then the reveal showed the result.
        #   The chooser is the worst case and the one that surfaced it:
        # `gettask` withdraws it, rebuilds every tab (each new widget asking
        # for a refit), and only then reveals it — so the fit ran mid-rebuild
        # on a window nobody could see, grew it, and the user met the result
        # cropped. Deferred to `deiconify`, which is the first moment the
        # measurement means anything.
        if not getattr(self, '_wv_visible', True):
            self._refit_wanted = True
            log.info("window {}: hidden, so deferring the fit until it is "
                     "shown".format(self._wid))
            return
        try:
            # MEASURE THE CONTENT, NOT THE CONTAINER. scrollWidth/Height of a
            # box that fills the window reports the WINDOW's size, so it can
            # only ever say "grow" — which is why a window created at 800x600
            # with 490px of content kept the surplus as dead theme-coloured
            # space. The union of the children's bounding boxes is the real
            # extent, and it can be smaller than the window.
            # AND MEASURE IT UNCONSTRAINED. The union of the children is the
            # right shape of question but it is asked of a layout THIS
            # METHOD has already squeezed: a child clipped by its container
            # reports the container's edge, so a second fit measures the
            # first fit's result and agrees with it. That is the
            # 1028x749 -> 991x728 pair in the item, and it is what Kent saw
            # on 2026-09-15 — "seems fine, then maybe again after words are
            # loaded… here, the second time, it is cropped."
            #   So the root is put to `max-content` for the duration of one
            # measurement and then restored. That answers "how big would
            # this like to be", which is the question, and it is the same
            # answer however many times it is asked — so repeated fits are
            # idempotent instead of ratcheting downwards.
            measured = wv.evaluate_js(
                # ITS OWN try/catch, because a JS exception here does not
                # raise in Python — it leaves `evaluate_js` waiting for a
                # result that never comes, and the fit's timer thread parks
                # forever. Kent's 2026-09-15 log is what that looks like:
                # "fit requested by content built" for four windows, and
                # then nothing, ever, with every Python-side failure path
                # already logging at INFO. A probe that can hang is worse
                # than one that can be wrong.
                '(function(){try{'
                'var r=document.getElementById("root")||document.body;'
                # ONE CLASS ON <html>, not inline styles on one element. The
                # inline version could only release #root, and its child
                # `.wv-window` is width/height 100% OF #root — circular, so
                # the child reported the size it already had and the probe
                # measured nothing new. `.wv-measuring` in grid.css releases
                # the whole chain (and the prose cap, which is expressed in
                # vw and so is meaningless mid-measurement).
                'document.documentElement.classList.add("wv-measuring");'
                'var nw=r.scrollWidth,nh=r.scrollHeight;'
                'var nb=r.getBoundingClientRect();'
                'nw=Math.max(nw,Math.ceil(nb.width));'
                'nh=Math.max(nh,Math.ceil(nb.height));'
                'document.documentElement.classList.remove("wv-measuring");'
                # The children's union as a floor, for a page whose root
                # does not shrink-wrap (an absolutely positioned child, a
                # stray 100% width) and would otherwise measure as nothing.
                'var kids=r.querySelectorAll("*");'
                'var base=r.getBoundingClientRect();'
                'var w=0,h=0,i,b;'
                # WHAT A SCROLLER HIDES IS NOT WHAT THE PAGE NEEDS. A
                # descendant of a box with `overflow:auto` is clipped by it
                # BY DESIGN — that is what a ScrollingFrame is for — so its
                # extent must not count toward the size the page requires,
                # and its position must not count as being drawn outside
                # anything.
                #   Both were counted. On the macrosort page the sort list's
                # content frame is 762x2196 inside a 1080-tall scroller,
                # scrolled to -521: the union read the page as 2378 tall
                # (so any non-fullscreen page with a scroller was measured
                # as needing its whole list on screen), and the displacement
                # check reported the scrolled frame as "DRAWN OUTSIDE ITS
                # PARENT" — which is simply what scrolling looks like
                # (Kent's log, 2026-09-16).
                'function clipped(el){'
                ' for(var p=el.parentElement;p&&p!==r;p=p.parentElement){'
                '  var o=getComputedStyle(p);'
                '  if(o.overflow!=="visible"||o.overflowY!=="visible"'
                '     ||o.overflowX!=="visible") return true;}'
                ' return false;}'
                'var widest=null,tallest=null,wleaf=null,wl=0;'
                # '>=', NOT '>'. A parent and the child pushing it out have
                # the SAME right edge, and document order puts the parent
                # first — so with '>' the report always named the outermost
                # frame, which is 1181 wide BECAUSE something inside it is.
                # Four rounds of "widest DIV.wv-widget wv-frame[1181x628 at
                # 0,0]" said nothing that distinguished one cause from
                # another. '>=' keeps the LAST element at the maximum, which
                # is the deepest one on that edge.
                #   `wleaf` is the same edge attributed to an element with no
                # element children — the actual text, image or control — so
                # the log names the widget and not its box.
                'for(i=0;i<kids.length;i++){'
                ' if(kids[i].offsetParent===null&&kids[i].tagName!=="IMG")'
                '  continue;'
                ' if(clipped(kids[i])) continue;'
                ' b=kids[i].getBoundingClientRect();'
                ' if(!b.width&&!b.height) continue;'
                ' if(b.right-base.left>=w){w=b.right-base.left;'
                '  widest=kids[i];}'
                ' if(b.bottom-base.top>=h){h=b.bottom-base.top;'
                '  tallest=kids[i];}'
                ' if(!kids[i].children.length&&b.right-base.left>=wl){'
                '  wl=b.right-base.left;wleaf=kids[i];}}'
                # WHO STICKS OUT, by name. Four rounds of this item have
                # inferred the culprit from a screenshot; one string in the
                # log ends that. `describe` is tag + classes + a little text,
                # which is enough to find the widget in the page and the call
                # site in the app.
                'function describe(el){if(!el)return "-";'
                ' var b=el.getBoundingClientRect();'
                ' return el.tagName+"."+(el.className||"")+"["+'
                '  Math.round(b.width)+"x"+Math.round(b.height)+" at "+'
                '  Math.round(b.left-base.left)+","+'
                '  Math.round(b.top-base.top)+"] "+'
                '  (el.textContent||"").trim().slice(0,28);}'
                # HOW MANY PICTURES ARE STILL COMING. An <img> that has not
                # decoded contributes NO height, so a page measured while
                # its images load measures as if they were not there — and
                # then grows when they arrive, past the window that was
                # fitted without them. That is the last cropped page: the
                # card image counted as nothing, the frame measured 564 tall
                # (log, 2026-09-15), and the picture appeared afterwards.
                'var pending=0,imgs=document.images;'
                'for(i=0;i<imgs.length;i++)'
                ' if(!imgs[i].complete) pending++;'
                # ANY WIDGET DRAWN OUTSIDE ITS OWN PARENT. Not the same as
                # overflowing one — a scroller's rows legitimately exceed
                # it downwards — so this looks only for a child whose TOP
                # or LEFT is above/left of its parent's, which no normal
                # layout produces. It is the shape of the macrosort page's
                # displaced group button: a row's select button drawn
                # full-width at the top of the page while the row it
                # belongs to sits empty in the list (Kent, 2026-09-15). The
                # DOM parent is right, so the question is which box it is
                # being laid out against, and that needs measuring rather
                # than reading.
                'var displaced="-";'
                'for(i=0;i<kids.length;i++){'
                ' var k=kids[i],p=k.parentElement;'
                ' if(!p||p===r||p===document.body) continue;'
                ' if(clipped(k)) continue;'   # scrolled, not displaced
                ' var kb=k.getBoundingClientRect(),pb=p.getBoundingClientRect();'
                ' if(!kb.width&&!kb.height) continue;'
                ' if(!pb.width&&!pb.height) continue;'
                ' if(kb.top<pb.top-8||kb.left<pb.left-8){'
                '  displaced=describe(k)+" drawn outside "+describe(p);'
                '  break;}}'
                'return [Math.ceil(Math.max(w,nw)),Math.ceil(Math.max(h,nh)),'
                'screen.availWidth,screen.availHeight,'
                'window.innerWidth,window.innerHeight,'
                'Math.ceil(nw),Math.ceil(nh),'
                'describe(widest),describe(tallest),pending,displaced,'
                'describe(wleaf)];'
                # The catch for the try above. Returning a SHORT list makes
                # Python's unpack fail, which is already logged — so a JS
                # fault becomes a log line instead of a parked thread. It
                # also removes the measuring class, which would otherwise
                # stay on <html> and leave the page laid out for
                # measurement rather than for reading.
                '}catch(e){'
                'document.documentElement.classList.remove("wv-measuring");'
                'return ["JS ERROR",String(e)];}})()')
        except Exception as e:
            # INFO, NOT DEBUG. A fit that cannot measure does nothing and
            # said nothing: Kent's 2026-09-15 log showed "fit requested by
            # content built" with no result and no reason, three windows
            # running, because every failure path here was invisible at the
            # app's log level. A silent no-op is the bug class this whole
            # port keeps rediscovering.
            log.info("window {}: could not measure content ({!r}); leaving "
                     "the size alone".format(self._wid, e))
            return
        try:
            (cw, ch, availw, availh, innerw, innerh,
             probew, probeh, widest, tallest, pending, displaced,
             wleaf) = measured
            (cw, ch, availw, availh, innerw, innerh, probew, probeh,
             pending) = [int(n) for n in (cw, ch, availw, availh, innerw,
                                          innerh, probew, probeh, pending)]
        except (TypeError, ValueError) as e:
            log.info("window {}: content measurement unusable ({!r}): {!r}"
                     "".format(self._wid, e, measured))
            return
        # THE TWO NUMBERS AND WHO OWNS THEM. `probe` is the unconstrained
        # max-content answer, `cw/ch` the larger of that and the children's
        # union — when they disagree, the union won, which means something is
        # sticking out of a layout that claims to be smaller. Naming the
        # element is what turns "still cropped" into a place to look.
        # `inner` IS THE CLIENT AREA, and it is the only honest number here.
        # The window's own reported size does not change when we resize it
        # (every line of Kent's 2026-09-15 log says "was 800x600", including
        # the ones logged after "settled at ... sized 1310x735"), so the
        # difference between what we asked for and what the page actually
        # got is invisible — and that difference IS the chrome, which
        # `_FIT_PAD` otherwise guesses at 28 for titlebar, borders and a
        # possible scrollbar. A GTK titlebar alone is about that. Logged so
        # the allowance can be measured instead of assumed.
        log.info("window {}: fit measured {}x{} (probe {}x{}, client {}x{}, "
                 "{} image(s) still loading); widest {} | widest leaf {} | "
                 "tallest {}".format(self._wid, cw, ch, probew, probeh,
                                     innerw, innerh, pending,
                                     widest, wleaf, tallest))
        if displaced and displaced != '-':
            log.error("window {}: fit found a widget DRAWN OUTSIDE ITS "
                      "PARENT — {}. Its DOM parent is right, so it is being "
                      "laid out against a different box: a `display` that "
                      "does not establish one, or a grid placement the "
                      "parent has no track for.".format(self._wid, displaced))
        # WAIT FOR THE PICTURES. Measuring now and resizing to the result
        # produces a window fitted to a page that is about to get bigger,
        # which is a crop the moment the image appears — and the app puts a
        # card image on most task pages. Bounded by the same retry count as
        # an empty read, so a picture that never loads costs a few half
        # seconds and not a loop.
        if pending > 0:
            tries = getattr(self, '_image_waits', 0) + 1
            self._image_waits = tries
            if tries < 6:
                log.info("window {}: {} image(s) not decoded yet; measuring "
                         "again ({} of 6)".format(self._wid, pending, tries))
                _request_refit(self, 'images still loading', delay=0.4)
                return
            log.info("window {}: {} image(s) never finished loading; fitting "
                     "to what is here".format(self._wid, pending))
        else:
            self._image_waits = 0
        if cw <= 0 or ch <= 0:
            log.info("window {}: no measurable content; leaving size alone"
                     "".format(self._wid))
            return
        # MEASURED, AND THAT IS ALL. A fullscreen window is already the size
        # it wants; everything above this point is diagnosis and belongs to
        # kiosk pages as much as to any other (see the fullscreen note at
        # the top). Everything below is the resize, which must not happen
        # here. `_check_displaced` and the overflow check have run by now,
        # so a kiosk page's geometry is in the log without its size being
        # touched.
        if getattr(self, '_measure_only', False):
            log.info("window {}: measured {}x{} in a {}x{} fullscreen "
                     "window — content {} the screen"
                     "".format(self._wid, cw, ch, innerw, innerh,
                               'exceeds' if (cw > innerw or ch > innerh)
                               else 'fits'))
            return
        # A MEASUREMENT AT THE FLOOR IS NOT A MEASUREMENT. `_FIT_MIN` exists
        # so a sparse page cannot collapse to a sliver — but clamping UP to
        # it turns "I could not measure this page" into "shrink it to the
        # minimum", and that is a crop rather than a fit. Kent's log,
        # 2026-09-15:
        #
        #     window 2:  fitted to content 420x260   <- page barely built
        #     window 2:  fitted to content 810x672   <- got a second chance
        #     window 12: fitted to content 420x260   <- and never did
        #
        # 420x260 is `_FIT_MIN` exactly, on both. The chooser was left at
        # the floor holding a notebook of task buttons.
        #   So a page that measures below the floor is not resized at all:
        # it keeps whatever size it has and the fit is asked for again. If
        # the page really is that small, nothing changes on the next pass
        # either and the window keeps its created size — too big for its
        # content, which is the milder half of this item and a separate
        # decision (kiosk/sparse pages, plan step 4).
        if cw + self._FIT_PAD < self._FIT_MIN[0] \
                or ch + self._FIT_PAD < self._FIT_MIN[1]:
            # BOUNDED, or a page whose content really is smaller than the
            # floor re-measures every half second for the life of the
            # session. Five is enough for a page that is still building and
            # few enough to be free for one that is not.
            tries = getattr(self, '_floor_reads', 0) + 1
            self._floor_reads = tries
            log.info("window {}: fit measured {}x{}, under the {}x{} floor — "
                     "not resizing ({} of 5)".format(
                        self._wid, cw, ch, self._FIT_MIN[0],
                        self._FIT_MIN[1], tries))
            if tries < 5:
                _request_refit(self, 're-measure after an empty read',
                               delay=0.5)
            return
        self._floor_reads = 0
        # THE CHROME, MEASURED. `resize()` sizes the WHOLE WINDOW — on GTK the
        # titlebar is inside it — so a window sized to `content + 28` hands
        # the page `content + 28 - titlebar - borders`, and a GTK titlebar is
        # about 37 on its own. The page is then short of room by the
        # difference and clips at the bottom, which is small enough to read
        # as "still cropped" rather than as an obvious miss (Kent,
        # 2026-09-15, on a page measuring 707 in a 735 window).
        #   `_FIT_PAD` cannot be tuned into correctness: it is one constant
        # for three backends and every window decoration a user might run.
        # What IS knowable is the gap between the size we asked for last time
        # and the client area the page actually got — that difference is the
        # chrome, measured on this machine, for this window. It is available
        # only after one resize, so the constant stays as the first guess and
        # the real number takes over from the second fit on.
        pad_w = pad_h = self._FIT_PAD
        asked = getattr(self, '_fit_asked', None)
        if asked and innerw > 0 and innerh > 0:
            # Only believe it if the window still IS the size we asked for;
            # a user-dragged window makes the difference meaningless.
            chrome_w, chrome_h = asked[0] - innerw, asked[1] - innerh
            if 0 <= chrome_w < 200 and 0 <= chrome_h < 200:
                pad_w = max(pad_w, chrome_w)
                pad_h = max(pad_h, chrome_h)
                if (chrome_w, chrome_h) != getattr(self, '_chrome_said', None):
                    self._chrome_said = (chrome_w, chrome_h)
                    log.info("window {}: window chrome measures {}x{} (asked "
                             "{}x{}, page got {}x{}); using it instead of the "
                             "{}px guess".format(self._wid, chrome_w, chrome_h,
                                                 asked[0], asked[1], innerw,
                                                 innerh, self._FIT_PAD))
        # SHRINKS AS WELL AS GROWS, which is what tkinter does and what the
        # surplus space complaint was about. Capped above by the display.
        want_w = min(cw + pad_w, availw)
        want_h = min(ch + pad_h, availh)
        # Ignore differences too small to be worth a resize flicker — but
        # STILL PLACE THE WINDOW. Centring used to sit after this guard, so a
        # window that was already the right size was never positioned: in
        # Kent's run only the status window (764x260, resized from 800x600)
        # got a `centred at …` line, and every window that happened to fit
        # already stayed wherever the WM had dropped it.
        #   Placement and sizing are separate questions and this method was
        # answering only one of them. A window that needs no resize still
        # needs to be somewhere.
        if abs(want_w - innerw) < 8 and abs(want_h - innerh) < 8:
            self._place_window(innerw, innerh, availw, availh)
            return
        try:
            wv.resize(want_w, want_h)
            # WHAT WE ASKED FOR, so the next fit can tell chrome from a
            # window that did not keep the size — see the chrome block above.
            self._fit_asked = (want_w, want_h)
            self._fit_asked_at = time.monotonic()
            # AND MAKE IT STICK. `resize()` alone is consumed once; the
            # window's DEFAULT size is what answers every later configure,
            # and on Wayland those arrive on almost any click. See
            # `_pin_default_size`.
            self._pin_default_size(want_w, want_h)
            # A MINIMUM the compositor cannot go below — the only one of
            # these that REFUSES the revert rather than correcting it after
            # the fact. See `_pin_min_size` for what it costs.
            self._pin_min_size(want_w, want_h, availw, availh)
            log.info("window {}: fitted to content {}x{} (client was {}x{}, "
                     "screen {}x{})".format(self._wid, want_w, want_h,
                                            innerw, innerh, availw, availh))
            # THE BASELINE the drop is measured against. Without a reading
            # taken while the window is the size we asked for, every later
            # frame/client pair has nothing to be compared to — and whether
            # the frame moved is exactly the open question. See
            # `_trace_resize`.
            self._trace_geometry("right after resize({}x{})".format(want_w,
                                                                    want_h))
        except Exception as e:
            log.debug("window {}: resize failed: {}".format(self._wid, e))
        self._place_window(want_w, want_h, availw, availh)
        # AND AGAIN, ONCE THE RESIZE HAS LANDED. A resize anchors the window
        # at its TOP-LEFT, so a window centred at one size and then grown
        # spills down and to the right — Kent, 2026-09-15: "this window seems
        # to have been placed centered, but then expanded into the lower
        # right corner." The centring above already uses the size we asked
        # for, so the numbers are right; what is not guaranteed is the ORDER
        # the window manager applies two requests issued in the same breath,
        # and a second fit (this item's 1028x749 -> 991x728 thread) can grow
        # a window with no move behind it at all.
        #   Re-centring is cheap, idempotent and needs no assumption about
        # which of those happened. The deferred call also reports the
        # window's ACTUAL geometry, so the next run says where it ended up
        # rather than where we asked it to go.
        try:
            self.after(250, lambda: self._settle_placement(availw, availh))
        except Exception as e:
            log.debug("window {}: could not schedule a re-centre: {}"
                      "".format(self._wid, e))

    def declare_dialog_of(self, parent=None):
        """Tell the window system this window BELONGS TO another one.

        THE SAME CONTRACT AS ui_tkinter.Toplevel.declare_dialog_of, and the
        same reason: `wm_transient` appeared nowhere in this codebase before
        2026-09-15, in either backend, so no window manager had ever been
        told that any of these windows were related. Under tkinter the WM was
        left to guess ("the windows are a bit of a hot mess", Kent
        2026-09-11); here I spent an afternoon trying to fake the same thing
        with coordinates, which Wayland forbids on principle.

        It is the ONE placement thing a Wayland client may say, and saying it
        gets from the compositor everything the coordinates were for: the
        child placed on its parent, stacked above it, raised and minimised
        with it, grouped with it in the window switcher.

        pywebview exposes no parent/transient option, so this goes through
        the native window — the same route `_pin_default_size` uses, which is
        known to reach a real Gtk.Window. Best-effort: a stack where it
        cannot be reached is exactly as it was before.

        NOT FOR A WINDOW WHOSE PARENT GETS WITHDRAWN. Many WMs hide a
        transient child along with its parent, and this app's Wait dialog,
        status window and ErrorNotice all withdraw theirs — so declaring
        transience there would hide the dialog. Callers pick; there is
        deliberately no automatic version of this."""
        target = parent if parent is not None else getattr(self, 'parent', None)
        # RECORDED, NOT ONLY DECLARED. Modal-on is a different relationship
        # from ownership — a window is OWNED by whoever supplies its theme
        # and root, and MODAL ON whatever it covers — and the app has been
        # reading one off the other. Keeping it here means "what do I return
        # to when I close?" has an answer that does not depend on the
        # ownership tree having the same shape, which is what lets a task be
        # owned by the root and still return to the chooser. See
        # `_reveal_parent_on_quit` and agenda/modal_window_stack.md.
        if target is not None:
            self._modal_on = target
        wv = getattr(self, '_wv_window', None)
        pwv = getattr(target, '_wv_window', None)
        if not wv or pwv is None:
            return False
        win = _native_window(wv)
        pwin = _native_window(pwv)
        if win is None or pwin is None or not hasattr(win, 'set_transient_for'):
            # Once per window, not per dialog: on a backend where the native
            # window is not reachable (anything but GTK today) this would
            # otherwise be a line for every dialog the app ever opens.
            if not getattr(self, '_said_no_transient', False):
                self._said_no_transient = True
                log.info("window {}: could not declare it a dialog of window "
                         "{} (no native window reachable); the window manager "
                         "will place it as an unrelated window"
                         "".format(self._wid, getattr(target, '_wid', '?')))
            return False
        _run_on_gui_thread(lambda: win.set_transient_for(pwin))
        log.info("window {}: declared a dialog of window {} — the window "
                 "manager places it on its parent and keeps it there"
                 "".format(self._wid, getattr(target, '_wid', '?')))
        return True

    def _pin_min_size(self, w, h, availw=None, availh=None):
        """Forbid the window being made smaller than its content.

        A COMPOSITOR CANNOT CONFIGURE A WINDOW BELOW ITS MINIMUM, which is
        why this is the one mechanism that stops the revert at source rather
        than correcting it afterwards. `move()` cannot work on Wayland at
        all; `set_default_size` was tried and does not hold; re-asserting
        the size works but flickers on every click.

        `webview.create_window` has a `min_size`, which is the supported way
        to say this — and it is fixed for the window's life, set before the
        page exists, so it cannot be the content size (Kent asked,
        2026-09-16). This is the same request made per fit, on the toolkit's
        own window.

        THE COST, and it is real: the window cannot then be dragged smaller
        than its content. Under the app's own layout schema that forfeits
        only step 3 — scrolling — as something the user can reach by
        shrinking a window; growing and wrapping are untouched, and the page
        still scrolls whenever the content genuinely exceeds the screen.
        """
        wv = getattr(self, '_wv_window', None)
        if not wv:
            return False
        win = _native_window(wv)
        # ONE IDEA, TWO SPELLINGS. GTK says `set_size_request(w, h)`; Qt says
        # `setMinimumSize(w, h)`. Asking only for the GTK one meant this did
        # nothing at all on Qt while reporting that it could not reach a
        # window (Kent, 2026-09-16).
        # GEOMETRY HINTS FIRST, on GTK. `set_size_request` is a WIDGET
        # minimum — advisory for a toplevel — and the run proved it: a window
        # with a 998x770 request was configured to 946x681 (Kent,
        # 2026-09-16), with the call confirmed made, on the GUI thread, via
        # that setter. What reaches `xdg_toplevel.set_min_size`, which is
        # the thing a Wayland compositor is obliged to respect, is the
        # window's geometry hints.
        #   `sys.modules` rather than an import, for the reason in
        # utilities/display.py: a fresh unversioned `Gdk` import inside a
        # running Qt process took the gi type system apart. If GTK is what
        # we are on, Gdk is already loaded.
        hinter = getattr(win, 'set_geometry_hints', None)
        gdk = sys.modules.get('gi.repository.Gdk')
        if callable(hinter) and gdk is not None:
            def _hint(w=w, h=h):
                # FRAME UNITS, not client units. The minimum was always
                # honoured; it was a decoration too small, so the window
                # fell to exactly this number as a FRAME and the page lost
                # the decoration off its client area. See `_inset_of` for
                # the measurement. Read here, inside the marshalled call,
                # so the read and the write are on the same thread and the
                # same instant.
                dw, dh = _inset_of(win)
                w, h = w + dw, h + dh
                try:
                    geom = gdk.Geometry()
                    geom.min_width, geom.min_height = w, h
                    hinter(None, geom, gdk.WindowHints.MIN_SIZE)
                except Exception as e:
                    log.info("window {}: geometry hints refused ({!r}); "
                             "falling back to a size request"
                             "".format(self._wid, e))
                    try:
                        win.set_size_request(w, h)
                    except Exception as e2:
                        log.info("window {}: and the size request failed "
                                 "too ({!r})".format(self._wid, e2))
                        return
                # SAID FROM IN HERE, because the numbers are only known in
                # here: the line used to be written before the marshalled
                # call ran, and reported the client figure as though it were
                # what had been asked for.
                if getattr(self, '_min_said', None) != (w, h):
                    self._min_said = (w, h)
                    log.info("window {}: minimum FRAME size requested: {}x{} "
                             "(via geometry hints, MIN_SIZE) — {}x{} of "
                             "content plus a {}x{} decoration, so a configure "
                             "answered with the minimum leaves the page the "
                             "size it needs".format(self._wid, w, h,
                                                    w - dw, h - dh, dw, dh))
            _run_on_gui_thread(_hint)
            return True
        setter = (getattr(win, 'set_size_request', None)
                  or getattr(win, 'setMinimumSize', None))
        if not callable(setter):
            if not getattr(self, '_said_no_min', False):
                self._said_no_min = True
                log.info("window {}: cannot set a minimum size (native "
                         "window {}), so a size taken away has to be put "
                         "back afterwards instead of refused"
                         "".format(self._wid,
                                   'not reachable' if win is None
                                   else 'has neither set_size_request nor '
                                        'setMinimumSize'))
            return False
        if availw:
            w = min(w, int(availw))
        if availh:
            h = min(h, int(availh))

        def _min(w=w, h=h):
            # FRAME UNITS here too — the same reasoning as the hint path
            # above, and the same reason: on Qt `setMinimumSize` is answered
            # for the window, decorations included, and the client area of
            # the window it produces is that much smaller.
            dw, dh = _inset_of(win)
            w, h = w + dw, h + dh
            setter(w, h)
            if getattr(self, '_min_said', None) != (w, h):
                self._min_said = (w, h)
                # "REQUESTED", not "cannot go smaller": what we asked for is
                # a fact; what the window manager will do with it is not
                # ours to state. The claim that it was NOT honoured — "a
                # window with a 998x770 minimum was configured to 946x681"
                # (Kent, 2026-09-16) — was this same units error read as
                # disobedience: 998-946 is 52 and 770-681 is 89, which is
                # the decoration exactly. It was honoured all along.
                log.info("window {}: minimum FRAME size requested: {}x{} "
                         "(via {}) — {}x{} of content plus a {}x{} "
                         "decoration".format(self._wid, w, h,
                                             getattr(setter, '__name__',
                                                     'the toolkit'),
                                             w - dw, h - dh, dw, dh))

        _run_on_gui_thread(_min)
        return True

    def _pin_default_size(self, w, h):
        """Make a fitted size survive the next configure event.

        THE SIZE WE SET AND THE SIZE THE WINDOW FALLS BACK TO ARE DIFFERENT
        NUMBERS, and only the first was ever set. `resize()` is one-shot; the
        DEFAULT size is what GTK answers a compositor configure with, and on
        Wayland a configure arrives on nearly every interaction — focus in,
        focus out, a click on the title bar. So a window fitted to 1310x735
        reverted to its created 800x600 on the next click, every click, and
        re-asserting the size afterwards only converted a crop into a
        flicker (Kent, 2026-09-15: "almost anywhere you click, 6x800 and
        back").

        Best-effort by nature: it reaches past pywebview for something
        pywebview does not expose, so it reports whether it worked and the
        re-assert in `_reassert` stays as the fallback for when it did not.
        Said once per window, not per fit."""
        wv = getattr(self, '_wv_window', None)
        if not wv:
            return False
        win = _native_window(wv)
        # GTK's name; Qt has no "default size" concept to set after the fact
        # (its equivalent is the constructor's geometry), so on Qt this
        # reports and does nothing — which is honest, and `_pin_min_size` is
        # the mechanism that applies there.
        setter = getattr(win, 'set_default_size', None)
        if not callable(setter):
            if not getattr(self, '_said_no_pinning', False):
                self._said_no_pinning = True
                log.info("window {}: cannot pin the default size (native "
                         "window {}), so a size lost to a configure event "
                         "has to be refused by a minimum instead"
                         "".format(self._wid,
                                   'not reachable' if win is None
                                   else 'has no set_default_size'))
            return False
        # CLIENT UNITS HERE, DELIBERATELY, and this is the one place the
        # units fix is NOT applied. `_inset_of` explains the bug: the
        # MIN_SIZE hint is answered in frame units, so it was pinning a
        # window one decoration too small. The measurement cannot say
        # whether `set_default_size` is the same, because both calls were
        # given the same number and either would produce the frame we saw.
        #
        # So the minimum gets the inset and this does not, because the
        # minimum is the BINDING constraint and the asymmetry only ever
        # fails safe:
        #
        #   * if this is in client units, it asks for exactly the right
        #     window and the minimum agrees;
        #   * if it is in frame units, it asks for one decoration too little
        #     and the minimum forbids that, so the client still lands on
        #     what the content needs.
        #
        # Adding the inset in both places has no such guarantee: if the two
        # calls disagree about units, the window comes out a decoration too
        # BIG. That is a mild fault rather than a crop, but it is a fault we
        # would have chosen, and one run of `--log-resizes` can separate the
        # two if it ever matters.
        _run_on_gui_thread(lambda: setter(w, h))
        if not getattr(self, '_said_pinning', False):
            self._said_pinning = True
            log.info("window {}: default size pinned to {}x{} (client units — "
                     "see _pin_default_size on why the inset goes on the "
                     "minimum and not here), so a configure event answers "
                     "with this instead of the size the window was created at"
                     "".format(self._wid, w, h))
        return True

    def _trace_resize(self, w, h):
        """One line per resize SAMPLE, under `--log-resizes`.

        WHAT THE DEBOUNCED REPORT CANNOT SHOW. `installResizeReporter` waits
        150ms for the resizes to stop before reporting one, because a drag
        fires continuously — so what reaches the log is where the window
        SETTLED, and everything on the way there is discarded. I read a
        constant 52x89 shortfall out of four settled samples and built a
        decoration-inset theory on it (2026-09-16); Kent's eyes said the
        frame itself moves, which that theory forbids. One sample per event
        cannot tell a value from the tail of a trajectory.

        So this reports EVERY sample (the JS side stops debouncing under the
        same switch) and, at each one, the native frame and client boxes and
        the gap between them — the whole trajectory of one focus change,
        rather than its endpoint.

        BEFORE THE DEDUPLICATION in `_report_client_resize`, deliberately: a
        `resize` whose client box is unchanged means the FRAME changed and
        the client did not, which is precisely the case those four samples
        could not have contained.

        Off unless asked: it is one log line per frame of a drag."""
        if not _switch('--log-resizes'):
            return
        _say_once("--log-resizes: every resize sample is reported, with no "
                  "debounce, carrying the native FRAME and CLIENT boxes and "
                  "the gap between them. See _trace_resize.")
        now = time.monotonic()
        since = now - getattr(self, '_trace_at', now)
        self._trace_at = now
        seq = getattr(self, '_trace_seq', 0) + 1
        self._trace_seq = seq
        asked = getattr(self, '_fit_asked', None)
        self._trace_geometry("#{} (+{:.3f}s) page client {}x{}, fit last "
                             "asked {}".format(
                                seq, since, w, h,
                                '{}x{}'.format(*asked) if asked else 'nothing'))

    def _report_height_chain(self, data):
        """Log the ancestor chain of every scroller on the page.

        THE DOUBLE SCROLL IS A CHAIN FAULT, and a page that shows it says
        only that the chain broke, never where. Three rules have to hold at
        once for a scroller to bound itself: the document needs a definite
        height, every grid between it and the scroller needs a track that
        takes the leftover space, and `align-content` must not have parked
        that space at the end instead. I fixed all three at once and the
        double scroll survived (Kent, 2026-09-16: "were you hoping the
        double scroll was fixed? it isn't"), which is exactly the outcome a
        three-part guess deserves.

        `styleh` is the load-bearing column: the AUTHORED height. A computed
        height is a px figure whether the property was `auto` or `100%`, so
        it cannot tell a definite height from a content-sized one — and that
        distinction is the entire question, because a percentage of `auto`
        is not a constraint and an `fr` track with no free space is just
        `auto`.

        Read the `client` column from the top down: where it stops matching
        the viewport, the height stopped propagating, and the row above that
        is the grid that needs a weight."""
        scrollers = (data or {}).get('scrollers') or []
        if not scrollers:
            log.info("window {}: height chain — no scrollers on this page"
                     "".format(self._wid))
            return
        for entry in scrollers:
            log.info("window {}: height chain for {!r} (viewport {}):"
                     "".format(self._wid, entry.get('target'),
                               entry.get('viewport')))
            # OUTERMOST FIRST, because that is the direction the height
            # travels; the page hands it over innermost-first.
            #   EVERY LINE CARRIES THE TAG. These were indented
            # continuation lines, so `grep 'height chain'` returned the
            # headers and none of the data — which is the whole report
            # (Kent's first run, 2026-09-16, came back as five header lines
            # and nothing else). A multi-line report has to be greppable by
            # the phrase a reader would grep for, on every line of it. Same
            # mistake as the drop line that reported an event without its
            # value.
            for row in reversed(entry.get('chain') or []):
                log.info("height chain:   {}{}{} client={} scroll={} "
                         "inline-height={} computed-height={} max-height={} "
                         "rows={} align-content={} overflow-y={}"
                         "".format(row.get('tag'),
                                   '#' + row['id'] if row.get('id') else '',
                                   '.' + row['cls'].replace(' ', '.')
                                        if row.get('cls') else '',
                                   row.get('client'), row.get('scroll'),
                                   row.get('styleh'), row.get('comph'),
                                   row.get('maxh'),
                                   row.get('rows'), row.get('align'),
                                   row.get('overflow')))

    def _trace_geometry(self, note):
        """Log the native frame and client boxes, tagged with `note`.

        Under `--log-resizes` only, and silent otherwise, so callers need no
        gate of their own. See `_trace_resize` for what this is for."""
        if not _switch('--log-resizes'):
            return
        wv = getattr(self, '_wv_window', None)
        wid = self._wid

        # MARSHALLED, because it touches the toolkit. Reading geometry is not
        # the write that `_run_on_gui_thread` exists for, but the rule is the
        # rule and a diagnostic is the last thing that should be the reason a
        # GTK process falls over. The cost is that the line lands on the next
        # idle rather than inline; the sequence number keeps the order
        # readable regardless.
        def _say():
            geo = _geometry_of(_native_window(wv)) if wv is not None else None
            log.info("resize trace: window {} {}; {}"
                     "".format(wid, note, _format_geometry(geo)))

        _run_on_gui_thread(_say)

    def _report_client_resize(self, data):
        """Say when the page's client area changes, and whether we asked.

        The distinction is the whole point. A fit that asks for 1310x735 and
        gets it logs the same lines as one that asks, gets it, and has the
        size taken back a moment later — Kent, 2026-09-15: "doubleclick
        enlarges the window, then focusing on another window makes it shrink
        again", and the cropped run and the good run were byte-identical in
        the log. A shrink nobody asked for is the fault, and it is reported
        as an error because a window smaller than its content is unusable,
        not merely untidy."""
        try:
            w = int((data or {}).get('w') or 0)
            h = int((data or {}).get('h') or 0)
        except (TypeError, ValueError):
            return
        if w <= 0 or h <= 0:
            return
        # FIRST, and before the deduplication below: see `_trace_resize`.
        self._trace_resize(w, h)
        was = getattr(self, '_client_seen', None)
        self._client_seen = (w, h)
        if was == (w, h):
            return
        asked = getattr(self, '_fit_asked', None)
        # Within 8px of what the fit asked for: this IS our resize arriving.
        if asked and abs(asked[0] - w) < 8 and abs(asked[1] - h) < 8:
            self._reassert_strikes = 0
            # NOT resetting the run count here. The restore SUCCEEDS every
            # time — that is the whole shape of this fault: taken away,
            # given back, taken away — so clearing the count on success
            # would mean it never reached the cap in the one pattern the cap
            # exists for. It decays on TIME instead; see `_reassert`.
            log.info("window {}: client area now {}x{} — the size the fit "
                     "asked for".format(self._wid, w, h))
            return
        # SMALLER IN EITHER AXIS IS A CROP, and it is tested FIRST. Written
        # the other way round — "larger in either axis means the user
        # dragged it" — a revert from 654x735 to 800x600 matched on WIDTH
        # (800 > 654) and was adopted as a deliberate resize, leaving 735 of
        # content in 600 of window: cropped, and now recorded as wanted
        # (Kent's log, 2026-09-15, line 217). A size that is bigger one way
        # and smaller the other is not a preference, it is the created size
        # coming back.
        if asked and (w < asked[0] - 8 or h < asked[1] - 8):
            self._reassert(w, h, asked)
            return
        # A SIZE THAT ARRIVES RIGHT AFTER OUR OWN RESIZE IS THAT RESIZE
        # LANDING, not a user's drag. The toolkit does not always give back
        # exactly what was asked: a fit that asked for 998x770 was answered
        # with 1036x770, and being "larger than asked" that was adopted as
        # the user's own preference — so a 38px settling difference silently
        # became the window's target size (Kent's log, 2026-09-16). A person
        # dragging a frame does not do it within a second of the app
        # resizing it.
        recent = (time.monotonic()
                  - getattr(self, '_fit_asked_at', 0)) < 1.5
        if asked and recent and (w > asked[0] + 8 or h > asked[1] + 8):
            log.info("window {}: client area now {}x{}, a little over the "
                     "{}x{} just asked for — the toolkit settling, not a "
                     "resize by hand; keeping the asked size as the target"
                     "".format(self._wid, w, h, asked[0], asked[1]))
            return
        if asked and (w > asked[0] + 8 or h > asked[1] + 8):
            # BIGGER IN BOTH AXES (nothing smaller, by the test above) means
            # a person dragged the frame. Adopt it rather than arguing: a
            # user's size beats a computed one, and re-asserting ours would
            # take their drag away from them.
            log.info("window {}: client area now {}x{} — larger than the "
                     "{}x{} the fit asked for, so treating it as yours and "
                     "keeping it".format(self._wid, w, h, asked[0], asked[1]))
            self._fit_asked = (w, h)
            self._reassert_strikes = 0
            return
        log.info("window {}: client area now {}x{} (fit last asked for {})"
                 "".format(self._wid, w, h, asked))

    def _reassert(self, w, h, asked):
        """Put back a size the window lost without being asked.

        WHY THIS IS NEEDED AT ALL. On Wayland the compositor sends the client
        an `xdg_toplevel.configure` whenever the toplevel's state changes —
        including activated → deactivated, i.e. on losing focus — and the
        client must answer it with a size. `resize()` is a ONE-SHOT request:
        once it has been consumed, GTK answers later configures from the
        window's DEFAULT size, which is the size the window was CREATED with.
        So every task window snapped back to 800x600 the moment anything else
        took focus — another window appearing, or a click on the desktop —
        and the page was then smaller than the content the fit had just
        measured, which is exactly a crop (Kent, 2026-09-15: "doubleclick
        enlarges the window, then focusing on another window makes it shrink
        again", and every revert in his log is to 800x600, the creation size).
        The right fix is to set the window's default size, and pywebview
        exposes no way to; re-asserting is what the public API allows.

        NOT A LOOP, three ways: our own resize arriving is recognised and
        clears the count; a size LARGER than we asked for is taken as the
        user's and adopted; and if the window refuses the size three times in
        a row we stop and say so, rather than fighting a compositor that has
        its own reasons (a tiled or constrained layout is legitimate, and an
        app that will not be tiled is worse than a small one)."""
        # OFF BY DEFAULT SINCE 2026-09-16, at Kent's decision, and the
        # reasoning is worth keeping because it is a choice and not a fix.
        #
        # Three mechanisms were tried against the revert and the compositor
        # declines all of them: `move()` (forbidden by xdg-shell, and the
        # attempt costs the size), the window's DEFAULT size
        # (`_pin_default_size` — reachable, does not hold), and a MINIMUM via
        # both `set_size_request` and geometry hints/MIN_SIZE
        # (`_pin_min_size` — narrows the fall from the created size to
        # somewhere above it, and is still overridden).
        #
        # Correcting it afterwards works, and flashes on every click. Kent,
        # weighing that against a stable smaller window: "let's do 2, then,
        # since we're looking for long-term value." A window that is the
        # wrong size shows a scrollbar and everything stays reachable, which
        # is step 3 of this app's own layout schema
        # (agenda/webview_window_sizing.md); a window that strobes is a
        # different and worse kind of broken.
        #
        # `--keep-window-size` puts the correction back, for measuring
        # against — and for stacks where it is not this expensive.
        if not _switch('--keep-window-size'):
            # THE SIZE IT DROPPED TO IS THE WHOLE POINT OF THE LINE, and
            # this said only that a drop had happened — so the one
            # experiment that distinguishes "reverts to the size it was
            # created at" from "clamps to a number of its own" could not be
            # read at all (Kent, 2026-09-16, running --window-size=640x480
            # and getting no target in the log). Reporting an event without
            # its value is the same mistake as the fit naming the outermost
            # frame.
            #   Every occurrence, not once per window: the target is the
            # measurement, and a second drop to a different size is news.
            # NOT "the compositor took the size", which is what this said
            # until the frame was measured alongside the client area. The
            # shortfall was our own pinned minimum, asked for in client
            # units and answered in frame units, and naming a culprit in a
            # log line is how that reading survived three days. See
            # `_inset_of`. A shortfall EQUAL TO THE DECORATION is that bug;
            # anything else is something new, so the numbers go in the line
            # and the diagnosis does not.
            log.info("window {}: client area short of the fit — now {}x{}, "
                     "content needs {}x{} (short by {}x{}), created at {}x{}. "
                     "NOT putting it back (--keep-window-size does, at the "
                     "cost of a flicker); the page scrolls instead. "
                     "--log-resizes shows the frame and the decoration."
                     "".format(self._wid, w, h, asked[0], asked[1],
                               asked[0] - w, asked[1] - h, *_created_size()))
            return
        strikes = getattr(self, '_reassert_strikes', 0) + 1
        self._reassert_strikes = strikes
        wv = getattr(self, '_wv_window', None)
        if strikes > 3 or not wv or getattr(self, '_is_fullscreen', False):
            if strikes == 4:
                log.error("window {}: client area keeps reverting to {}x{} "
                          "and will not hold the {}x{} its content needs. "
                          "Giving up rather than fighting the window manager "
                          "— the page will scroll instead. On Wayland this is "
                          "the compositor answering a configure with the "
                          "window's created size; --gdk-backend=x11 does not "
                          "do it.".format(self._wid, w, h, asked[0], asked[1]))
            return
        # NOT MORE THAN ONCE A SECOND. This is driven by a resize REPORT from
        # the page, and putting the size back causes another resize, which
        # reports again — so a compositor that keeps taking the size away
        # gives a tight loop of shrink/restore. Kent's log, 2026-09-15, shows
        # six cycles in a row, each logged as "attempt 1 of 3" because the
        # restore succeeded every time and reset the count. The strike count
        # cannot catch that; only the clock can.
        # FAST, BUT BOUNDED. The flash lasts exactly as long as the window
        # sits at the wrong size, so a one-second rate limit made the
        # symptom WORSE than no limit — it was there to stop a tight
        # shrink/restore loop, and the loop only happens when the restore
        # itself keeps failing. 0.2s is short enough that the correction
        # reads as a flicker rather than a resize, and the count below stops
        # a compositor that will not settle from flashing indefinitely.
        now = time.monotonic()
        if now - getattr(self, '_reassert_at', 0) < 0.2:
            return
        self._reassert_at = now
        # A RUN OF THEM MEANS IT IS NOT GOING TO WORK. Correcting the size
        # is worth a flicker; twelve corrections mean the window is being
        # taken away as fast as we give it back, and at that point a stable
        # small window with a scrollbar beats a strobing correct one.
        # A BURST, measured over time. Quiet for 20 seconds and the count
        # starts again, so someone who clicks around all afternoon never
        # exhausts it; twelve inside 20 seconds is a window that will not
        # settle.
        if now - getattr(self, '_reassert_run_from', 0) > 20:
            self._reassert_run_from = now
            self._reassert_run = 0
        run = getattr(self, '_reassert_run', 0) + 1
        self._reassert_run = run
        if run > 12:
            if run == 13:
                log.error("window {}: the size has been taken away 12 times "
                          "and put back 12 times; giving up on correcting it "
                          "— the window will stay at whatever the compositor "
                          "gives it and the page will scroll. This is the "
                          "window-sizing item, not something you did."
                          "".format(self._wid))
            return
        log.info("window {}: client area dropped to {}x{} without being "
                 "asked (content needs {}x{}); putting the size back "
                 "(attempt {} of 3). Wayland re-configures a toplevel on "
                 "focus change and GTK answers from the CREATED size, since "
                 "resize() is one-shot.".format(self._wid, w, h,
                                                asked[0], asked[1], strikes))

        # ON THE GUI THREAD. This runs on the JS bridge's callback thread —
        # the page reported its own resize — and GTK is not thread-safe, so
        # resizing a window from here is undefined behaviour. The app died
        # silently right after a burst of these (Kent, 2026-09-15), which is
        # what touching a toolkit off its own thread looks like: no
        # traceback, no signal message, nothing in the log.
        def _put_back():
            try:
                wv.resize(asked[0], asked[1])
            except Exception as e:
                log.info("window {}: could not put the size back ({!r})"
                         "".format(self._wid, e))
        _run_on_gui_thread(_put_back)

    def _check_displaced(self):
        """Report any widget drawn ABOVE or LEFT of its own parent.

        Its own probe, run on every refit request — including for a
        FULLSCREEN window, which `fit_to_content` declines to measure and
        which is precisely where the fault shows: the macrosort run window
        is kiosk, and a group's select button has twice appeared full-width
        across the top of it with the row it belongs to left empty (Kent,
        2026-09-15, intermittent).
        Only that one direction, because overflowing a parent DOWNWARD is
        normal — a scroller's rows do it by design — while nothing normal
        puts a child above its parent's top edge.
        """
        wv = getattr(self, '_wv_window', None)
        if not wv or not _started.is_set():
            return
        if not getattr(self, '_wv_visible', True):
            return
        try:
            found = wv.evaluate_js(
                '(function(){try{'
                'var r=document.getElementById("root")||document.body;'
                'var base=r.getBoundingClientRect();'
                'function d(el){var b=el.getBoundingClientRect();'
                ' return el.tagName+"."+(el.className||"")+"["+'
                '  Math.round(b.width)+"x"+Math.round(b.height)+" at "+'
                '  Math.round(b.left-base.left)+","+'
                '  Math.round(b.top-base.top)+"] "+'
                '  (el.textContent||"").trim().slice(0,32);}'
                # WHAT IS SITTING DIRECTLY IN THE PAGE. A window's content is
                # ONE element under #root (its outer frame); anything else
                # there is laying itself out against the page instead of
                # against a frame, which is how a group's select button ends
                # up full-width across the top with its own row left empty
                # (Kent, 2026-09-15, twice — "the extra sort group is
                # there").
                #   This is the check that was missing: the containment test
                # below SKIPS children of #root, so the one case that
                # matters could never be reported by it.
                # Menus and anything hidden are legitimately parked here: a
                # ContextMenu is parented to the WINDOW, so the page is the
                # only place for it to live, and it spends its life hidden.
                'var top=r.children,tl=[];'
                'for(i=0;i<top.length;i++){'
                ' var t=top[i];'
                ' if(t.classList.contains("wv-menu")) continue;'
                ' if(t.offsetParent===null) continue;'
                ' tl.push(d(t));}'
                'if(tl.length>1) return "#root HAS "+tl.length+'
                ' " VISIBLE CHILDREN (expected 1): "+tl.join(" || ");'
                'var kids=r.querySelectorAll("*"),i,k,p,kb,pb;'
                'for(i=0;i<kids.length;i++){'
                ' k=kids[i];p=k.parentElement;'
                ' if(!p||p===r||p===document.body) continue;'
                ' kb=k.getBoundingClientRect();pb=p.getBoundingClientRect();'
                ' if(!kb.width&&!kb.height) continue;'
                ' if(!pb.width&&!pb.height) continue;'
                ' if(kb.top<pb.top-8||kb.left<pb.left-8)'
                '  return d(k)+" drawn outside "+d(p);}'
                # AN IMAGE THAT ARRIVED AND DRAWS AT NOTHING. The sort
                # page's right-hand cycle control has an <img> with a real
                # data URI (nothing logs a resolution failure) and a box
                # too small to hold it — so either the element is not there
                # or it is there at zero size, and no log so far tells them
                # apart (Kent, 2026-09-15: "what are we waiting on for the
                # second cycle image?"). `naturalWidth` is what the decoded
                # picture measures; the rect is what the page gave it.
                # LAID OUT, NOT MERELY PRESENT. `offsetParent === null` means
                # the element is not being laid out at all — `display:none`,
                # which is how a hidden notebook panel and a grid_remove()d
                # row are done here. Its rect is 0x0 by definition, so the
                # first version of this check reported every image on every
                # hidden tab: "Parse Already Collected Words" is a chooser
                # button on a panel nobody is looking at, and it fired long
                # before the page under test (Kent, 2026-09-15).
                #   A collapsed image is only interesting when its box IS on
                # screen, which is why the parent's own rect must be real.
                'var im=document.images,j,b2,pp;'
                'for(j=0;j<im.length;j++){'
                ' if(im[j].offsetParent===null) continue;'
                ' pp=im[j].parentElement;'
                ' if(!pp) continue;'
                ' var pr=pp.getBoundingClientRect();'
                ' if(pr.width<2||pr.height<2) continue;'
                ' b2=im[j].getBoundingClientRect();'
                ' if(im[j].naturalWidth>0&&(b2.width<2||b2.height<2))'
                '  return "IMAGE COLLAPSED: natural "+im[j].naturalWidth+'
                '   "x"+im[j].naturalHeight+" drawn "+Math.round(b2.width)+'
                '   "x"+Math.round(b2.height)+" in "+d(im[j].parentElement);}'
                'return "";}catch(e){return "ERR "+String(e);}})()')
        except Exception as e:
            log.debug("window {}: displacement probe failed ({!r})"
                      "".format(self._wid, e))
            return
        if isinstance(found, str) and found:
            log.error("window {}: WIDGET DRAWN OUTSIDE ITS PARENT — {}. The "
                      "DOM parent is right, so it is laying out against a "
                      "different box.".format(self._wid, found))

    def _settle_placement(self, availw, availh):
        """Re-centre on the size the window ACTUALLY ended up, and say so."""
        wv = getattr(self, '_wv_window', None)
        if not wv or not getattr(self, '_exists', True):
            return
        if getattr(self, '_is_fullscreen', False):
            return
        w = getattr(wv, 'width', None)
        h = getattr(wv, 'height', None)
        x = getattr(wv, 'x', None)
        y = getattr(wv, 'y', None)
        log.info("window {}: settled at {},{} sized {}x{} on {}x{}"
                 "".format(self._wid, x, y, w, h, availw, availh))
        self._learn_origin(x, y, availw, availh)
        if isinstance(w, int) and isinstance(h, int) and w > 0 and h > 0:
            self._place_window(w, h, availw, availh)
        self._grow_if_overflowing(availw, availh)

    def _learn_origin(self, x, y, availw, availh):
        """Remember where windows are, so the next one goes there too.

        THE USER'S OWN CHOICE IS THE BEST INPUT, and this is the only place we
        can see it: there is no move event, but every fit reads the window's
        actual position afterwards, and a position we did not ask for is one
        somebody else chose — the window manager placing the first window, or
        the user dragging any of them. Either is a better answer than a
        computed one, which is why both are simply adopted (Kent, 2026-09-15:
        "if a user moves a window somewhere, that should count as a
        preference to respect").

        Fullscreen windows are skipped: their position is 0,0 by definition
        and adopting it would send every later window to the corner."""
        global _window_origin
        if getattr(self, '_is_fullscreen', False) or not _can_position():
            return
        if not (isinstance(x, int) and isinstance(y, int)):
            return
        # ON SCREEN AND NOT THE OFF-SCREEN BIRTHPLACE. Windows are born at
        # -32000 to avoid a startup flash (`_place_onscreen`), and adopting
        # that would put every window where none can be seen. The upper
        # bound catches a window dragged mostly off the far edge, which is
        # a position the user may want for THAT window but not a place to
        # put new ones.
        if not (0 <= x <= max(0, availw - 100)
                and 0 <= y <= max(0, availh - 100)):
            return
        if (x, y) == _window_origin:
            return
        # Ours, already applied — not new information.
        if (x, y) == getattr(self, '_placed_at', None):
            return
        was = _window_origin
        _window_origin = (x, y)
        log.info("window {}: windows will open at {},{} from now on ({})"
                 "".format(self._wid, x, y,
                           'moved from {},{}'.format(*was) if was
                           else "the window manager's choice for the first "
                                "window"))

    def _grow_if_overflowing(self, availw, availh):
        """Ask the DISPLAYED page whether it is being clipped, and grow.

        THE LAST WORD BELONGS TO THE STATE THE USER SEES. `fit_to_content`
        measures a page with its constraints released (`.wv-measuring`), and
        four rounds of this on the Add-and-Parse page ended with the probe
        insisting on 1022x564 while the card image and the right-hand text
        were visibly cut — the same number every time, so the measurement is
        self-consistent and simply does not predict the drawn layout.
        Rather than keep hunting for the difference, this checks the thing
        that matters: `scrollWidth > clientWidth` means content the user
        cannot see, whatever the reason.
        Bounded and additive: it asks for exactly the shortfall, at most
        three times, and stops at the screen — so a page that genuinely
        cannot fit ends up scrollable rather than growing forever.
        """
        wv = getattr(self, '_wv_window', None)
        if not wv or getattr(self, '_is_fullscreen', False):
            return
        if not getattr(self, '_wv_visible', True):
            return
        tries = getattr(self, '_grow_tries', 0)
        if tries >= 3:
            return
        try:
            over = wv.evaluate_js(
                '(function(){try{'
                'var r=document.getElementById("root")||document.body;'
                'var d=document.documentElement;'
                'var ow=Math.max(r.scrollWidth-r.clientWidth,'
                ' d.scrollWidth-d.clientWidth);'
                'var oh=Math.max(r.scrollHeight-r.clientHeight,'
                ' d.scrollHeight-d.clientHeight);'
                'return [ow,oh,window.innerWidth,window.innerHeight];'
                '}catch(e){return ["ERR",String(e)];}})()')
            ow, oh, innerw, innerh = [int(n) for n in over]
        except Exception as e:
            log.info("window {}: could not check for overflow ({!r})"
                     "".format(self._wid, e))
            return
        if ow <= 2 and oh <= 2:
            self._grow_tries = 0
            return
        want_w = min(innerw + max(ow, 0), availw)
        want_h = min(innerh + max(oh, 0), availh)
        if want_w <= innerw and want_h <= innerh:
            return          # nothing left to give; the page will scroll
        self._grow_tries = tries + 1
        log.info("window {}: content overflows by {}x{}; growing to {}x{} "
                 "({} of 3)".format(self._wid, ow, oh, want_w, want_h,
                                    self._grow_tries))
        try:
            wv.resize(want_w, want_h)
        except Exception as e:
            log.info("window {}: grow failed ({!r})".format(self._wid, e))
            return
        try:
            self.after(250, lambda: self._settle_placement(availw, availh))
        except Exception as e:
            log.debug("window {}: could not re-check overflow: {}"
                      "".format(self._wid, e))

    def _place_window(self, w=None, h=None, availw=None, availh=None):
        """Put the window where windows go, not wherever the WM drops it.

        `w`/`h`/`availw`/`availh` are UNUSED and kept only so the call sites
        did not all have to change: the position is remembered, not derived
        from the size, which is the whole point of the change below.

        Kent, 2026-09-11, on four overlapping windows — task page, Sound Card
        Settings, the rate chooser and the status window, none of them related
        to any other: "the windows are a bit of a hot mess."

        Nothing ever positioned a pywebview window. `create_window` is given
        a size and no coordinates, so placement is whatever the window manager
        chooses — which for a stack of dialogs opened in sequence is a
        cascade, or a pile, depending on the WM. Under tkinter these are
        Toplevels of one root and the WM places them as a family; here every
        one is a separate OS window with no stated relationship, so the
        family resemblance has to be supplied.

        ONE PLACE, NOT ONE PER WINDOW — and it was CENTRING until
        2026-09-15. Kent: "if a user moves a window somewhere, that should
        count as a preference to respect. So can we just keep drawing
        (non-kiosk) windows in the SAME place, rather than trying to centre
        them?"

        Centring was wrong on two counts beyond ignoring the user. It
        DERIVES the position from the size, so every refit moved the window —
        a window that grew by 40px slid 20px left, for no reason a user could
        see. And a page whose content settles over several fits therefore
        walked across the screen while it settled.

        A remembered origin fixes both: the position is a fact, not a
        computation, so a resize leaves it alone. The origin is seeded by
        wherever the FIRST window lands — the window manager's own choice,
        which is the best available guess and costs nothing to accept — and
        replaced by the user's whenever they move one (`_settle_placement`
        adopts any position we did not ask for). Windows then appear where
        the last one was, which is where the user is looking.

        Session-scoped, deliberately: a remembered origin in the settings
        file would also need a screen-geometry check on load (a window
        restored to a monitor that is no longer attached is unreachable), and
        that is a bigger decision than this. Say if it should persist.

        KIOSK WINDOWS ARE EXEMPT — they are fullscreen, so they have no
        position to have a preference about; the guard is `_is_fullscreen`
        in the callers. See agenda/webview_window_sizing.md.
        """
        wv = getattr(self, '_wv_window', None)
        if not wv:
            return
        if not hasattr(wv, 'move'):
            log.info("window {}: this pywebview has no move(); leaving "
                     "placement to the window manager".format(self._wid))
            return
        # A MOVE THAT CANNOT WORK MUST NOT BE ATTEMPTED, because it is not
        # free. On native Wayland a client cannot place its own toplevel —
        # and `move()` is not merely ignored there: it re-configures the
        # surface, which brings the window back at its DEFAULT size. So a
        # window fitted to 1310x735 and then centred reverted to the 800x600
        # it was created with, and the log showed the shrink landing
        # immediately after each `centred at` line, three cycles running
        # (Kent, 2026-09-15). The page was then smaller than the content the
        # fit had just measured — i.e. cropped — and the fit was blamed for
        # it for most of a day. `--gdk-backend=x11` cured it because there
        # the move genuinely works.
        #   So: centring is a real improvement where it is possible, and a
        # net loss where it is not. Said once per window, not per attempt.
        if not _can_position():
            if not getattr(self, '_said_no_positioning', False):
                self._said_no_positioning = True
                log.info("window {}: leaving placement to the compositor — "
                         "this display stack does not let a client place its "
                         "own windows, and the attempt is not free (it "
                         "re-configures the surface, which costs the window "
                         "the size it was just given). --gdk-backend=x11 "
                         "allows positioning.".format(self._wid))
            return
        global _window_origin
        if _window_origin is None:
            # NOTHING TO GO ON YET. Let this one land where the window
            # manager puts it and learn from that: `_settle_placement` reads
            # the position it ended up at and makes it the origin. Moving it
            # somewhere invented would be a worse guess than the WM's, and
            # would be the first thing the user has to undo.
            return
        x, y = _window_origin
        try:
            wv.move(x, y)
            # LOGGED AT INFO, not debug, and on SUCCESS as well as failure.
            # Kent, 2026-09-11: "they're still both uncentered" — and with
            # only a debug line on the failure path there was no way to tell
            # from a run whether the move was attempted, attempted with the
            # wrong numbers, or accepted and then undone. Three candidates
            # and the log distinguished none of them, which is the same
            # mistake as measuring a rate without recording the level.
            self._placed_at = (x, y)
            log.info("window {}: placed at {},{} — where windows go in this "
                     "session".format(self._wid, x, y))
        except Exception as e:
            # pywebview's move() is not on every backend/version, and a
            # window in the wrong place is not worth an exception.
            log.info("window {}: move to {},{} failed: {}"
                     "".format(self._wid, x, y, e))

    def _wv_call(self, method, *args):
        """Call a method on the pywebview window, deferring until the window
        is ready.

        TWO READINESS CONDITIONS, and only the first was checked: the global
        `_started` (webview.start has run) AND this window's own page having
        loaded. `_js()` has always had the per-window queue for exactly this
        reason; `_wv_call` did not, so calls aimed at a window that existed
        but had not loaded were issued and lost.

        That is why no task window was ever visible. The log reads:

            window 20: created HIDDEN (withdrawn=True)
            window 20: WITHDRAW -> hide()
            window 20: DEICONIFY -> show()      <- before the page exists
            window 20: DEICONIFY -> show()      <- still before
            GET /base.html                       <- page starts loading HERE
            Toplevel 20 JS ready - flushing 408 queued calls

        Both reveals landed on an unloaded window and evaporated; nothing
        asked again afterwards, so a window created hidden stayed hidden
        forever. Queuing preserves ORDER, which matters here — hide-then-show
        must replay as hide, then show."""
        if not self._wv_window:
            return
        if not _started.is_set() or not self._wv_loaded.is_set():
            # Defer — replayed by _flush_wv_calls once this window has loaded
            self._wv_deferred.append((method, args))
            if method in ('show', 'hide'):
                log.info("window {}: {}() deferred until its page loads"
                         "".format(self._wid, method))
            return
        if method in ('show', 'hide'):
            log.info("window {}: pywebview {}() now".format(
                getattr(self, '_wid', 'root'), method))
        try:
            getattr(self._wv_window, method)(*args)
        except Exception as e:
            log.debug(f"wv_call {method} failed: {e}")

    def _flush_wv_calls(self):
        """Execute deferred pywebview window calls."""
        # COALESCE VISIBILITY: only the LAST show/hide matters. These were
        # queued because the window was not ready, so replaying them
        # literally makes the window blink through states the user was never
        # meant to see — Kent, 2026-09-08, on the splash: "Are the first two
        # flashes necessary? I can't see users not being affected by that."
        # A queued hide followed by a queued show is a no-op in intent; the
        # user should see the end state, not the journey to it.
        if self._wv_deferred:
            queued = list(self._wv_deferred)
            last_vis = None
            for method, args in queued:
                if method in ('show', 'hide'):
                    last_vis = (method, args)
            kept = [(m, a) for m, a in queued if m not in ('show', 'hide')]
            if last_vis is not None:
                kept.append(last_vis)
            dropped = len(queued) - len(kept)
            self._wv_deferred = kept
            log.info("window {}: replaying deferred {}{}".format(
                getattr(self, '_wid', 'root'),
                [m for m, _a in kept],
                " (collapsed {} redundant show/hide)".format(dropped)
                if dropped else ''))
        for method, args in self._wv_deferred:
            try:
                getattr(self._wv_window, method)(*args)
            except Exception as e:
                log.debug(f"Deferred wv_call {method} failed: {e}")
        self._wv_deferred.clear()
        # AND SAY IT AGAIN A MOMENT LATER, if the intent is to be hidden.
        # These calls are replayed from inside the engine's load-finished
        # handler, and on QtWebEngine the window's own creation map wins the
        # race: the Wait window replayed `hide`, logged it, and stayed on
        # screen over everything for the rest of the session (Kent, Qt,
        # 2026-09-15 — "qt seems stuck with this window still up"). GTK
        # honours the same call, which is why this went unseen.
        #   Re-asserting is safe on every backend: hiding an already hidden
        # window is a no-op, and the intent is the thing we are sure of.
        if not getattr(self, '_wv_visible', True):
            def _reassert_hidden():
                if getattr(self, '_wv_visible', True):
                    return          # something asked for it meanwhile
                try:
                    self._wv_window.hide()
                    log.info("window {}: re-asserted hide after the deferred "
                             "replay".format(getattr(self, '_wid', 'root')))
                except Exception as e:
                    log.info("window {}: could not re-assert hide ({!r})"
                             "".format(getattr(self, '_wid', 'root'), e))
            try:
                self.after(200, _reassert_hidden)
            except Exception as e:
                log.debug("could not schedule the hide re-assert: {}"
                          "".format(e))

    # VISIBILITY IS LOGGED AT INFO, DELIBERATELY. No task window has ever been
    # seen on screen under this backend — the root shows as an empty themed
    # box, task windows flashed and vanished, and nothing appears in the
    # window list. That has two possible shapes and the log could not tell
    # them apart: either nothing ever ASKS a window to show, or the ask is
    # made and does not take. Every hide/show now says so, with the window id,
    # so one run answers it. There is a known recurring class here on the Tk
    # side too — a withdrawn run window never revealed — so "who asked for
    # show" is worth being able to read off a log permanently, not just once.
    def withdraw(self):
        """Hide — and NAME WHO ASKED, as ui_tkinter.Toplevel.withdraw does.

        This logging predates the Tk side's and inspired it (see the note
        below), but it reported only the window id. On the 2026-09-09 NWAA it
        showed two windows going away at the end with nothing to say why, and
        the answer had to come from the Tk run instead. Caller attribution
        added here 2026-09-09 so either backend can name its own producer.
        """
        try:
            import traceback as _tb
            frame = _tb.extract_stack(limit=2)[0]
            log.info("window {}: WITHDRAW (hide) requested by {}:{} in {}()"
                     "".format(self._wid, frame.filename.rsplit('/', 1)[-1],
                               frame.lineno, frame.name))
        except Exception as e:
            log.info("window {}: WITHDRAW (hide) requested, caller unknown "
                     "({})".format(self._wid, e))
        self._wv_visible = False
        self._wv_call('hide')

    def _place_onscreen(self):
        """Bring a window created OFF-SCREEN back where it can be seen.

        Unconditional and immediate, not left to the refit: the refit
        centres properly, but it can return early (no measurable content, a
        failed evaluate_js), and a window parked at -32000 that never gets
        placed is invisible — which is worse than the startup flash the
        off-screen trick exists to avoid. So this moves it somewhere visible
        first and lets the fit centre it properly afterwards.
        """
        if not getattr(self, '_offscreen', False):
            return
        self._offscreen = False
        wv = getattr(self, '_wv_window', None)
        if not wv or not hasattr(wv, 'move'):
            return
        # THE ONE MOVE THAT IS STILL WORTH TRYING where positioning is not
        # available: a window born at -32000 is invisible, which is worse
        # than a size reverting. The birth is also before any fit, so there
        # is no fitted size to lose yet. See `_place_window` for why
        # every LATER move is skipped on such a stack.
        try:
            wv.move(60, 60)
            log.info("window {}: brought on-screen from its off-screen "
                     "birthplace".format(self._wid))
        except Exception as e:
            log.info("window {}: could not place it on-screen ({!r})"
                     "".format(self._wid, e))

    def deiconify(self):
        log.info("window {}: DEICONIFY (show) requested".format(self._wid))
        was_hidden = not getattr(self, '_wv_visible', True)
        self._wv_visible = True
        self._place_onscreen()
        self._wv_call('show')
        # A FIT DEFERRED WHILE HIDDEN HAPPENS NOW. See fit_to_content: a
        # hidden window cannot be measured, and the chooser is rebuilt
        # entirely while hidden (`gettask` withdraws it, rebuilds its tabs,
        # then reveals it), so every refit its new content asked for arrived
        # at the worst possible moment. Kent, 2026-09-15: "when the
        # taskchooser comes back from being waited … it is cropped again
        # (having been expanded into the lower right in the previous ~1s)."
        if was_hidden or getattr(self, '_refit_wanted', False):
            self._refit_wanted = False
            _request_refit(self, 'window shown')

    def lift(self, aboveThis=None):
        """Bring this window to the front. MISSING UNTIL 2026-09-09, and its
        absence was a NO-WINDOW bug rather than a stacking annoyance.

        `ui_shell._option_dialog`'s two callers finish with `w.lift()`
        (`ui_shell.py:2389`, `:2425`), so under this backend picking a sense
        letter in Add and Parse Words with Audio raised
        `AttributeError: 'Window' object has no attribute 'lift'`. That fires
        inside a pywebview event callback, where `on_event` (line ~114) logs
        the traceback and CONTINUES — so nothing crashed, the caller simply
        stopped at that line, and the user got no window and no error.

        Same bug shape as the four earlier misses in this port (`takekioskscreen`,
        `after_idle`, `cget`, `wait_window`): a call that tkinter answers and
        this backend did not, swallowed by a handler that keeps going. It is
        also why implementing this is not enough on its own — see the note on
        `on_event` swallowing in agenda/webview_when_to_finish.md.

        pywebview has no stacking API, so `show()` is the honest equivalent: on
        every engine it maps AND raises, and calling it on an already-visible
        window is harmless. That also makes `lift()` do the useful thing the
        two call sites actually wanted — the dialog they had just built was
        hidden, and lift is what was meant to present it.
        """
        log.info("window {}: LIFT (show, no stacking API) requested"
                 "".format(self._wid))
        # `lift` IS a show here, so it is also the moment a deferred fit
        # becomes possible — several dialogs are built hidden and presented
        # with lift() rather than deiconify().
        was_hidden = not getattr(self, '_wv_visible', True)
        self._wv_visible = True
        self._place_onscreen()
        self._wv_call('show')
        if was_hidden or getattr(self, '_refit_wanted', False):
            self._refit_wanted = False
            _request_refit(self, 'window lifted')

    def lower(self, belowThis=None):
        """The pair of `lift`, and missing for the same reason it was.

        pywebview has no stacking API either way, so this cannot put a window
        BEHIND another — but a caller reaching for it wants this one out of
        the way, and hiding it is the closest honest thing. Logged, because
        "the window vanished" is a confusing symptom and this is one of the
        two places that can cause it.
        """
        log.info("window {}: LOWER (hide, no stacking API) requested"
                 "".format(self._wid))
        _close_native_window(self, 'window {}'.format(self._wid))

    def geometry(self, spec=None):
        """`WxH+X+Y`, as tkinter's — getter with no argument, setter with one.

        MISSING UNTIL 2026-09-11, and it failed visibly: every status-window
        open logged "status window geometry failed: 'StatusWindow' object has
        no attribute 'geometry'", so the window was never sized or placed by
        the code that meant to.
        """
        if spec is None:
            return '{}x{}+{}+{}'.format(self.winfo_width(),
                                        self.winfo_height(),
                                        self.winfo_x(), self.winfo_y())
        try:
            size, _sep, pos = str(spec).partition('+')
            if 'x' in size:
                w, _x, h = size.partition('x')
                if w and h:
                    self._wv_call('resize', int(w), int(h))
            if pos:
                x, _p, y = pos.partition('+')
                if x and y:
                    self._wv_call('move', int(x), int(y))
        except Exception as e:
            log.info("window {}: couldn't apply geometry {!r} ({})"
                     "".format(self._wid, spec, e))

    def title(self, text=None):
        """tkinter's title() is a GETTER with no argument, and the ambient
        collab status depends on that: `base = w.title().split(SEP)[0]`
        (main.py:493). Returning None made every 10-second poll log
        "collab_title_status: 'NoneType' object has no attribute 'split'"
        for every visible window — five per tick in the first sort run."""
        if text is None:
            return getattr(self, '_title_text', '')
        self._title_text = text
        self._wv_call('set_title', text)
        return text

    def attributes(self, *args):
        """tkinter's -fullscreen / -zoomed / -topmost, as far as pywebview
        can honour them. Anything else is accepted and ignored, as it was
        before — but fullscreen is NOT ignorable: TaskDressing.__init__
        calls takekioskscreen() unconditionally."""
        if len(args) >= 2 and args[0] in ('-fullscreen', '-zoomed'):
            self._set_fullscreen(bool(args[1]))
        return None

    wm_attributes = attributes

    def _set_fullscreen(self, want):
        """pywebview exposes only a TOGGLE, so track the state ourselves —
        calling toggle twice for the same intent would undo it.

        ON BY DEFAULT, as under tkinter; `--no-kiosk` disables it.

        `TaskDressing.__init__` calls `takekioskscreen()` on EVERY task
        window, and that is DELIBERATE — Kent, 2026-09-08: "I like it on most
        task windows, to avoid distractions on the computer." A task window
        filling the screen is the point: the people using these pages are
        sorting words, not managing windows.

        I briefly defaulted it OFF (2026-09-07) because implementing this
        method turned every task window fullscreen while I was still trying
        to establish whether windows appeared at all — my debugging
        convenience overriding the design. Reverted. `--no-kiosk` exists for
        exactly that debugging case, where a fullscreen undecorated window
        showing a half-built layout is hard to work with (and reads as a hung
        machine). Escape and double-click release fullscreen either way, so a
        user is never trapped."""
        # SAY IT, EVERY TIME, AND SAY WHO ASKED. This logged only the
        # --no-kiosk refusal, so applying fullscreen and declining to apply
        # it again were BOTH silent — and the question "why is kiosk taken
        # twice?" (Kent, 2026-09-16, from a 20fps filmstrip showing
        # fullscreen, then a decorated window, then fullscreen again) could
        # not be answered from the log at all. A state transition that can
        # be lost underneath us is exactly the kind that has to be
        # announced; `ui_tkinter.py:1631` already logs its kiosk withdraw
        # for the same reason.
        #   THE REPEAT IS THE INTERESTING CASE, not the change. pywebview
        # exposes a TOGGLE, so `_is_fullscreen` is our own bookkeeping, and
        # it is only as good as our knowledge of what the compositor did.
        # Hiding and re-showing a Wayland toplevel drops fullscreen; `wait()`
        # withdraws the waiting window and `waitdone()` re-shows it, and
        # `sort_ui.py:709` / `sorting_engine.py:2314` deiconify the run
        # window explicitly. If the flag says True while the window is
        # decorated, this guard is what keeps it decorated — so a "no change
        # needed" line next to a decorated window IS the diagnosis.
        try:
            import traceback as _tb
            frame = _tb.extract_stack(limit=3)[0]
            who = '{}:{} in {}()'.format(frame.filename.rsplit('/', 1)[-1],
                                         frame.lineno, frame.name)
        except Exception:
            who = 'caller unknown'
        if bool(getattr(self, '_is_fullscreen', False)) == bool(want):
            # EXPECTED for a window born kiosk: `create_window` already did
            # it, and `getrunwindow` calls `takekioskscreen()` anyway as the
            # fallback for engines that cannot. Said differently from a
            # drift, so the line does not read as an alarm in the case it is
            # now the normal one.
            if want and getattr(self, '_born_kiosk', False):
                log.info("window {}: fullscreen already set at creation — "
                         "nothing to toggle, asked by {}"
                         "".format(self._wid, who))
            else:
                log.info("window {}: fullscreen already believed {} — no "
                         "toggle sent, asked by {}. If the window is NOT in "
                         "that state, this line is the bug: the flag has "
                         "drifted from the compositor and nothing re-applies "
                         "it.".format(self._wid, bool(want), who))
            return
        if want and _switch('--no-kiosk'):
            log.info("window {}: fullscreen requested, NOT applied "
                     "(--no-kiosk is in force), asked by {}"
                     "".format(self._wid, who))
            return
        self._is_fullscreen = bool(want)
        log.info("window {}: fullscreen {} — sending toggle, asked by {}"
                 "".format(self._wid, 'ON' if want else 'OFF', who))
        self._wv_call('toggle_fullscreen')

    def takekioskscreen(self, event=None):
        """Kiosk mode: no window dressing, all the screen.

        ui_tkinter (:3536) also binds Escape and double-click to leave. Here
        the ESCAPE BINDING IS THE IMPORTANT HALF — a webview window in
        fullscreen with no decorations and no way out is a machine that looks
        hung, and this is called on EVERY task window
        (ui_shell.py:2952), so getting it wrong strands the user everywhere
        rather than on one page."""
        self._set_fullscreen(True)
        self.bind('<Escape>', self.releasefullscreen)
        # Double-click is bound once, at load, to `_dblclick_fit`, which
        # routes to release-fullscreen while we are fullscreen. Binding it
        # again here would run the handler twice per click.

    def takefullscreen(self, event=None):
        """Maximise, keeping the window dressing. pywebview has no 'maximise'
        that works across all backends, so this is kiosk mode with the same
        escapes — the tkinter version falls back to exactly that when
        '-zoomed' is unsupported (:3550)."""
        self.takekioskscreen(event)

    def releasefullscreen(self, event=None):
        """Leave fullscreen — and then fit the window to its content.

        Without the refit the window snaps back to the size it was CREATED
        at (800x600) while holding a page laid out for the whole screen, so
        it clips on the right and bottom. fit_to_content() runs once at page
        load and is skipped while fullscreen, so leaving fullscreen is the
        only other moment its answer changes.

        Deferred rather than immediate: the toggle has to reach the window
        manager before the window's own dimensions mean anything, and
        fit_to_content compares against them."""
        self._set_fullscreen(False)
        if hasattr(self, 'fit_to_content'):
            self.after(250, self.fit_to_content)

    # ── Global bindings ───────────────────────────────────────────────
    # tkinter's bind_all/unbind_all reach every widget in the interpreter;
    # in a page the equivalent target is the document. Used by
    # lexicon.py:1329-1342 for navigation keys.
    def bind_all(self, event, handler, add=None):
        return self.bind(event, handler, add=add)

    def unbind_all(self, event=None):
        return self.unbind(event)

    def _root(self):
        """tkinter's Misc._root(). sort_ui.py:172 asks for it."""
        return self._find_root() or self

    def mainloop(self, setup_callback=None):
        """Delegate to Root.mainloop() — mirrors tkinter where any widget can call mainloop."""
        root = self._find_root()
        if root:
            root.mainloop(setup_callback=setup_callback)

    def _find_root(self):
        p = self.parent
        while p:
            if isinstance(p, Root):
                return p
            p = getattr(p, 'parent', None)
        return None

    def protocol(self, name, func):
        """`WM_DELETE_WINDOW` — what to run when the user closes the window.

        WAS A NO-OP, so the close box did nothing but close. Three call sites
        depend on it and each loses something different:

          * `sound_ui.py:893` — `on_quit`, which RESTORES THE TASK WINDOW.
            Without this, closing Sound Settings with the X left the user
            with no visible window at all; the Done button worked because it
            calls `on_quit` directly. (That restore was itself added today,
            so the fix was half-dead on arrival under webview.)
          * `tasks/alphabet_chart.py:59` and
            `tasks/alphabet_comparison.py:54` — `taskchooser.gettask`, so
            closing either page returns to the chooser. Without it the page
            closes and nothing comes back.

        IT INTERCEPTS THE CLOSE. In tkinter `WM_DELETE_WINDOW` replaces the
        close: the window does NOT go away unless the handler makes it. My
        first version let pywebview close the window anyway and called the
        handler alongside, which is a different contract — and Kent spotted
        the consequence (2026-09-11): the alphabet pages hand the close to
        `taskchooser.gettask`, so if the window is closed out from under that
        call, whatever `gettask` decides to reuse or rebuild is being torn
        down behind it.

        So the `closing` handler returns False, cancelling the native close,
        and the app owns what happens next — exactly as under tkinter, where
        a handler that forgets to destroy leaves an unclosable window. All
        three call sites do dispose of the window: `on_quit` hides it,
        `gettask` finishes the task through `finish_task_ui`.
        """
        if name != 'WM_DELETE_WINDOW' or not func:
            return
        # ONE SUBSCRIBER, A SWAPPABLE HANDLER. `protocol()` gets called more
        # than once for a window now that every window is given a default
        # (see `_wire_default_close`), and `closing += …` ADDS rather than
        # replaces — so two calls would leave both handlers running, and the
        # app would return to the chooser AND quit. tkinter's `protocol`
        # replaces; this keeps one subscription and swaps what it dispatches.
        self._delete_handler = func
        if getattr(self, '_closing_wired', False):
            log.info("window {}: close box re-pointed at {}".format(
                        self._wid, getattr(func, '__name__', func)))
            return
        wv = getattr(self, '_wv_window', None)
        events = getattr(wv, 'events', None)
        closing = getattr(events, 'closing', None) if events else None
        if closing is None:
            log.info("window {}: this pywebview has no closing event; the "
                     "close box will not run {}".format(
                        self._wid, getattr(func, '__name__', func)))
            return

        def _on_closing():
            handler = getattr(self, '_delete_handler', None)
            try:
                if handler:
                    handler()
            except Exception as e:
                log.error("window %s: the close handler raised (%s)",
                          self._wid, e)
            # False CANCELS the native close — see the docstring. The handler
            # disposes of the window itself, or deliberately keeps it.
            return False
        try:
            closing += _on_closing
            self._closing_wired = True
            log.info("window {}: close box wired to {}".format(
                        self._wid, getattr(func, '__name__', func)))
        except Exception as e:
            log.info("window {}: couldn't wire the close box ({})"
                     "".format(self._wid, e))

    # wait_window lives on _WebviewWidget — tkinter puts it on Misc, so every
    # widget has it, and call sites use it from both windows and frames.

    def iconphoto(self, default, *args):
        pass

    def on_quit(self, to_root=False, event=None):
        """Close this window — and the PROGRAM if this is the main window.

        `or getattr(self,'ismainwindow',False)` is the half that was
        missing, and `ui_tkinter.py:1422` has had it all along:

            if (to_root or getattr(self,'ismainwindow',False)) and self.parent:

        Without it, quitting the main window closed one window and left the
        app running with nothing visible — every other window being hidden
        or gone. `ismainwindow` is set by `TaskDressing.i_am_mainwindow`,
        which moves the title as the user moves between the chooser and a
        task, so it is the app's own answer to "is this the last window that
        matters", and this backend never asked it.

        AND THE OTHER HALF, missing until 2026-09-16: tkinter's `else:`
        branch REVEALS THE PARENT (`ui_tkinter.py:1425-1495`). Without it,
        closing a child window hides that window and puts nothing in its
        place — so Exit on a run window left the screen empty with the app
        still running, which is indistinguishable from the app closing. Kent
        reported it as exactly that ("I thnk the runwindow is closing the app
        on exit"), and the log agreed with him about the symptom and not
        about the cause: no `PROGRAM QUIT` line anywhere, just
        `Toplevel 237 hidden rather than destroyed, by ... in <lambda>()` —
        the Exit button's own command, closing one window and revealing
        nothing. `getrunwindow` withdraws the task window before handing the
        run window over (`ui_shell.py:3159`), so the parent is always hidden
        by the time this runs.

        The three-way decision is tkinter's, predicate for predicate, using
        the SAME `visibility` helpers rather than a local re-reading of
        "does this page have anything on it" — two copies of that would
        drift, and it is the same question the watchdog and QuitOnlyGuard
        ask. A wait already covering the screen will do the revealing; an
        EMPTY parent is reported and left hidden, because Kent's rule is
        "we shouldn't be making pages visible, counting on them having
        meaning later"; anything else is revealed.
        """
        self.exitFlag.true()
        # KILL ANY IN-FLIGHT drive_work, as tkinter does (:1420) and for the
        # same reason: a long verify-list build goes on draining the event
        # loop after the user has quit, so the next dialog cannot paint or
        # take a click until it finishes.
        if hasattr(self, 'cancel_drive_work'):
            try:
                self.cancel_drive_work()
            except Exception as e:
                log.info("window {}: could not cancel drive_work on quit "
                         "({!r})".format(self._wid, e))
        # Nothing should be left reading "Please Wait…" on a window that has
        # quit. See `_hide_page_wait`.
        self._hide_page_wait()
        if (to_root or getattr(self, 'ismainwindow', False)) and self.parent:
            self.parent.on_quit(to_root=True)
        else:
            self._reveal_parent_on_quit()
        self._exists = False
        if hasattr(self, '_wait_event'):
            self._wait_event.set()
        # Quitting must free waiters too, or closing a window leaves whoever
        # was waiting on it blocked — the same deadlock by a different door.
        # AND EVERY CANARY INSIDE IT, not just the window: see
        # `_release_waiters_below` for the dump that proved this was the hang.
        _release_waiters_below(self, 'the window it is in has quit')
        _close_native_window(self, 'Toplevel {}'.format(self._wid))

    def _nothing_behind_me(self):
        """This window closed and there is nothing underneath it.

        THE CLOSE PATH OWNS WHAT COMES NEXT. Until now a task closing with
        nothing behind it simply left the screen empty, and two separate
        safety nets existed to notice afterwards — `guardvisible` at 15s and
        the visibility watchdog at 25s. Both are there because this case had
        no answer; giving it one removes the case rather than watching for
        it.

        The answer is the task list, which is what a user who has finished a
        task wants and is the one page that is always meaningful. It is also
        what makes a window-less chooser possible: the first task of a
        session is modal on nothing, so closing it is exactly when the
        chooser first needs to exist. See agenda/modal_window_stack.md.

        Never raises: this runs inside `on_quit`, where an exception would
        cost the close itself."""
        try:
            root = self._find_root() or default_root()
            chooser = getattr(getattr(root, 'program', None),
                              'taskchooser', None)
            if chooser is None or chooser is getattr(self, 'task', None):
                log.info("window {}: nothing behind it and no task chooser "
                         "to fall back to; the screen is now empty"
                         "".format(self._wid))
                return
            log.info("window {}: nothing behind it — showing the task list"
                     "".format(self._wid))
            chooser.gettask()
        except Exception as e:
            log.info("window {}: nothing behind it, and the task list could "
                     "not be shown ({!r})".format(self._wid, e))

    def _reveal_parent_on_quit(self):
        """Put the parent window back when this one closes, or say why not.

        The mirror of `ui_tkinter.Toplevel.on_quit`'s `else:` branch. See
        `on_quit` for what its absence cost. Never allowed to raise: this
        runs during teardown, and a failed reveal must not also break the
        close."""
        # WHAT THIS WINDOW COVERS, not what owns it. `_modal_on` is set by
        # `declare_dialog_of`; `parent` is the fallback and is what every
        # window used before the two were separated. A task owned by the
        # root still returns to the chooser, because the chooser is what it
        # was covering. See agenda/modal_window_stack.md.
        parent = getattr(self, '_modal_on', None) \
                 or getattr(self, 'parent', None)
        if parent is None or not getattr(parent, '_exists', False):
            self._nothing_behind_me()
            return
        if isinstance(parent, Root):
            # The root has no page of its own worth revealing, and tkinter
            # excludes it for the same reason — but something must still
            # come next, or the user is left with nothing.
            self._nothing_behind_me()
            return
        try:
            from frontend.visibility import has_content, report_empty_page
        except Exception as e:
            log.info("window {}: cannot decide whether to reveal the parent "
                     "({!r}); leaving it hidden".format(self._wid, e))
            return
        try:
            content = has_content(parent)
            waiting = parent.iswaiting()
            log.info("window {}: on_quit reveal decision for window {}: "
                     "has_content={} iswaiting={}"
                     "".format(self._wid, getattr(parent, '_wid', '?'),
                               content, waiting))
        except Exception as e:
            log.info("window {}: on_quit reveal decision couldn't be "
                     "reported ({!r})".format(self._wid, e))
            content, waiting = True, False
        try:
            if waiting:
                # A wait is already on the screen and will reveal what it
                # covers. If NO WINDOW follows this line, the wait is the
                # thing to chase, not a missing reveal.
                log.info("window {}: leaving window {} to the wait that "
                         "covers it".format(self._wid,
                                            getattr(parent, '_wid', '?')))
                return
            if not content:
                report_empty_page('on_quit', parent, 'not revealed',
                                  'closing window {}'.format(self._wid))
                return
            log.info("window {}: revealing window {}"
                     "".format(self._wid, getattr(parent, '_wid', '?')))
            parent.deiconify()
        except Exception as e:
            log.info("window {}: could not reveal the parent ({!r})"
                     "".format(self._wid, e))

    def destroy(self):
        """Destroying a Toplevel must retire its WINDOW, not just its widgets.

        `_WebviewWidget.destroy` only tells the page to remove DOM nodes,
        which for a window means emptying it and leaving it on screen. The
        splash is destroyed at `tasks/chooser.py:551`, so it sat there for the
        whole session and was still up after Quit — Kent, 2026-09-08: "on
        quit, the Splash is still up."

        Retired by hiding rather than destroying, for the reason in
        _close_native_window: destroying a pywebview window crashes
        QtWebEngine, and A-Z+T reuses windows anyway."""
        if not self._exists:
            return
        super().destroy()
        _close_native_window(self, 'Toplevel {}'.format(self._wid))

    def iswaiting(self):
        # A PAGE WAIT COUNTS. Both visibility guards treat "something is
        # waiting" as evidence that the screen is accounted for
        # (`guardvisible` declines to act, `visibility.anything_viewable`
        # accepts it), and `drive_work` reports progress only while this is
        # true. A cover this window is showing has to answer yes, or the
        # guards would read a page that says "Please Wait…" as no window at
        # all and the build would report no progress.
        holder = getattr(self, '_page_wait', None)
        if holder is not None and getattr(holder, '_exists', False):
            return True
        # AND A WAIT THIS WINDOW HANDED OVER IS STILL THIS WINDOW'S WAIT.
        # `drive_work` reports progress only while this is true, so
        # answering no here silenced the bar on the run window's cover. See
        # `_wait_host`.
        if self._wait_host() is not self:
            return True
        # The reused wait window lives on the root; bubble up to Root.iswaiting
        # (which reports whether the one wait window is currently active).
        if self.parent:
            return self.parent.iswaiting()
        return False

    # ── Waiting ───────────────────────────────────────────────────────
    # wait()/waiting()/waitdone() existed ONLY on Root, but they are called on
    # TASK windows — `tasks/chooser.py:108` does
    #   with self.ui.waiting(_("Getting your task list…"), thenshow=True):
    # which reached TaskWindow.__getattr__, fell through to the task, and
    # raised AttributeError mid-boot. That is the §7 row "wait()/waiting()/
    # waitdone only on Root", and it stopped the chooser from being built.
    #
    # The bodies mirror Root's deliberately rather than delegating: `wait()`
    # hides the window that is waiting and reveals it again in `waitdone()`,
    # so it has to run against THIS window, and Root's signature has no way
    # to say "wait on someone else". A shared mixin is the tidy-up, and is
    # not worth restructuring this file's MRO for today.
    def _waitwindow(self, create=True):
        """The one reused Wait window, owned by the app root."""
        root = self._find_root() or default_root()
        if root is None:
            return None
        return root._waitwindow(create=create)

    @contextmanager
    def waiting(self, msg=None, **kwargs):
        """Context-manager form of wait()/waitdone(): closes the wait dialog
        even if the body raises or returns early.

        The `finally` is the point — `tests/test_waiting_contract.py` exists
        to guard it, because the failure it prevents is a wait dialog left on
        screen over a window nobody can reach."""
        self.wait(msg=msg, **kwargs)
        try:
            yield self
        finally:
            self.waitdone()

    # ── The wait that lives ON the page ───────────────────────────────
    # WHY THIS EXISTS AT ALL, since the answer is "no good reason it didn't".
    # The wait has always been a separate Toplevel in both backends — that is
    # tkinter's shape, and this backend mirrored it without asking whether it
    # had to. Under tkinter there are reasons: no cheap overlay idiom, and
    # painting during a build is exactly where the XWayland deadlocks live.
    # Neither applies to a page. Kent, 2026-09-16, on being told the content
    # could simply be swapped in place: "sorry, what?!? if we can do this,
    # why have we not? that is essentially the goal here: don't show page
    # content before its ready / don't leave the user confused in the
    # interim."
    #
    # WHAT IT REPLACES. A kiosk run window is born fullscreen (see
    # `_kiosk_kwarg`) and cannot be born hidden on this stack — `hidden=`
    # never maps on WebKitGTK, and the off-screen fallback cannot work
    # because Wayland ignores client-set positions (`_can_position`). So the
    # window is briefly visible with nothing in it: a full screen of empty
    # theme, then a separate wait dialog appearing over it, then the page.
    # One surface that says "Please Wait" and then becomes the page is both
    # fewer windows and the thing the user should be looking at.
    #
    # NOT IN `frame`, DELIBERATELY. `visibility.has_content` tests
    # `w.frame.winfo_children()`, and its own warning is the rule: "NOTHING A
    # GUARD ADDS IS CONTENT" — anything put there would make an empty page
    # read as built and hand the visibility guards a false reveal target. It
    # goes in `outsideframe`, in the same cell as `frame`, so it covers the
    # content area without being part of it.
    _PAGE_WAIT_ROW = 1
    _PAGE_WAIT_COLUMN = 1
    #: Longest a cover may sit there with nobody clearing it. Generous on
    #: purpose — one sort-page build measured 21.6s — but finite, because
    #: `getrunwindow` now covers every run window and a cover nobody clears
    #: is indistinguishable from a hung app.
    _PAGE_WAIT_LIMIT_MS = 90000

    def _page_wait_expired(self, holder):
        """A cover nobody cleared. Remove it and name the situation."""
        if getattr(self, '_page_wait', None) is not holder:
            return          # already cleared, or replaced by a newer one
        log.error("window {}: a page wait has been up for {:.0f}s and "
                  "nothing cleared it — removing it, because a cover nobody "
                  "clears looks exactly like a hung app. Whoever raised this "
                  "wait never called waitdone(); see "
                  "agenda/webview_flows_run_concurrently.md"
                  "".format(self._wid, self._PAGE_WAIT_LIMIT_MS / 1000.0))
        self._hide_page_wait()

    def _page_wait_ok(self):
        """Is an in-page wait the right kind for THIS window?

        TWO CASES, and the first version had only one. "Fullscreen" alone
        meant a wait raised before a run window exists — the parser's
        "Loading Affixes", raised on the visible task window — had nothing to
        host it and fell back to the dialog. Kent's 20fps recording,
        2026-09-16, frame 24: the one small "Please Wait" window left in an
        otherwise clean sequence.

          * FULLSCREEN: this window is the page-to-be. Host the wait even if
            it is currently hidden, and reveal it — that is the run window
            case, and `wait()` does the revealing.
          * ALREADY VISIBLE: this window is what the user is looking at, so
            covering its content area is exactly what a dialog over it would
            have done, minus the window. No reveal: a hidden window is hidden
            for a reason, and showing it to display a wait could put a
            half-built page on screen.

        A window with no `outsideframe` (a bare Toplevel, the root) has
        nowhere to put one. `--no-page-wait` restores the dialog for
        comparison."""
        if _switch('--no-page-wait'):
            return False
        if getattr(self, 'outsideframe', None) is None:
            return False
        return (bool(getattr(self, '_is_fullscreen', False))
                or bool(getattr(self, '_wv_visible', False)))

    def _show_page_wait(self, msg):
        """Cover this window's content area with a wait message."""
        existing = getattr(self, '_page_wait', None)
        if existing is not None and getattr(existing, '_exists', False):
            for label in getattr(existing, '_wait_labels', []):
                try:
                    label.configure(text=str(msg or ''))
                except Exception as e:
                    log.info("window {}: page wait message not updated "
                             "({!r})".format(self._wid, e))
            return True
        try:
            # A REAL OVERLAY, not a grid cell that happens to be the same
            # one. Sharing `frame`'s cell relies on paint order and on the
            # cover being sized to the whole area, and it was neither: Kent,
            # 2026-09-16, sent a wait page with the sort board's group-count
            # labels showing straight through it (window 389 — "5 14 2 5 16
            # 2 2 2 8" down the middle of "Please Wait…"). The content
            # building behind the cover is the POINT; being able to see it is
            # the bug.
            #   `cssclass` is the existing way a widget gets a class of its
            # own — `ScrollingFrame` uses it for the same reason — and
            # `.wv-page-wait` in grid.css does the covering with
            # `position: absolute; inset: 0`, which states the intent
            # instead of inferring it from the layout.
            holder = Frame(self.outsideframe,
                           cssclass='wv-page-wait',
                           row=self._PAGE_WAIT_ROW,
                           column=self._PAGE_WAIT_COLUMN,
                           sticky='nsew')
            Label(holder, text=_("Please Wait…"), font='title',
                  row=0, column=0, sticky='ew')
            detail = Label(holder, text=str(msg or ''), font='instructions',
                           row=1, column=0, sticky='ew')
            # A THIRD LINE FOR PROGRESS, because the dialog this replaces has
            # a bar and losing it would trade one silence for another. Text
            # rather than a bar: `waitprogress` is handed a count, not a
            # fraction, so a number is the honest rendering of what we know.
            # A BAR AND NO NUMBER. The dialog this replaces has always had a
            # bar, and losing it was a regression the page wait introduced
            # (Kent: "can we give that modal a progressbar?"). A figure
            # alongside it was my addition and his answer was no — "the
            # progressbar doesn't need the number, especially as it's just a
            # calculated %" — which is right: the same quantity twice is
            # noise, and the bar reports it by LENGTH, a shape, so nothing
            # about the reading depends on colour.
            #   GRID-REMOVED UNTIL SOMETHING REPORTS. Plenty of waits never
            # call `waitprogress` at all, and a bar sitting at zero for
            # twenty seconds says "stuck" rather than "working". Same
            # treatment the wait dialog gives its own bar (`activate`
            # removes it; `progress()` re-grids on demand).
            bar = Progressbar(holder, row=2, column=0, sticky='ew')
            # AND THE CARD IMAGE, because this is now the app's general
            # "Please Wait" surface and not a one-off cover (Kent: "We're
            # building that Please wait modal thingy generally, right? if so,
            # we should have the AZT icon on it."). `image='small'` and the
            # `noimagescaling` gate are both taken from `Wait.__init__` —
            # the dialog this replaces has shown it since the window existed,
            # and a user looking at a twenty-second operation should see the
            # app's own picture rather than a bare field.
            #   BELOW the bar: the message says what is happening and the bar
            # says how far along, which is what a reader needs first; the
            # image is what makes the screen the app's rather than a browser's.
            if not getattr(getattr(self, '_find_root', lambda: None)(),
                           'noimagescaling', False):
                # `sticky=''` — CENTRED IN THE COLUMN, not stretched across
                # it. `'ew'` makes the label fill the column and then the
                # image sits wherever the label's own flex layout puts it;
                # an empty sticky is tkinter's way of saying "centre me in
                # my cell", and it is the grid that does the centring rather
                # than something inside the label.
                Label(holder, image='small', text='',
                      row=3, column=0, sticky='', pady=30)
            try:
                bar.grid_remove()
            except Exception as e:
                log.info("window {}: page wait bar could not start hidden "
                         "({!r})".format(self._wid, e))
            holder._wait_labels = [detail]
            holder._wait_bar = bar
            self._page_wait = holder
            # AND STOP THE DOCUMENT SCROLLING, or the engine paints its
            # scrollbar beside a cover that cannot reach it. See
            # `setPageWaitCover` in widgets.js.
            _js(getattr(self, '_wv_window', None), 'setPageWaitCover(true)')
            # BOUNDED, because `getrunwindow` now raises one for EVERY run
            # window and a cover nobody clears looks exactly like a hung
            # app — the `tryNAgain` hole in a new place, and worse than the
            # blank screens it replaces. `waitdone` and `resetframe` are the
            # normal exits; this is the one that fires when neither
            # happened, and it says so at ERROR because a page that took
            # this long to say nothing is a bug with a caller's name on it.
            try:
                # A CLOSURE, because this backend's `after` takes no extra
                # arguments — tkinter's does (`after(ms, func, *args)`) and
                # ui_webview's is `after(ms, func=None)`, so passing the
                # holder raised TypeError and the timeout silently did not
                # exist (Kent's log, 2026-09-16 — caught only because the
                # fallback says so out loud).
                self.after(self._PAGE_WAIT_LIMIT_MS,
                           lambda h=holder: self._page_wait_expired(h))
            except Exception as e:
                log.info("window {}: page wait has no timeout ({!r})"
                         "".format(self._wid, e))
            self._page_wait_at = time.monotonic()
            log.info("window {}: page wait shown ({!r}) — no separate wait "
                     "window for this one".format(self._wid, msg))
            return True
        except Exception as e:
            # A failed page wait must fall back to the real one, never leave
            # the user on a blank screen — that is the whole point of it.
            log.info("window {}: could not show a page wait ({!r}); using "
                     "the wait window instead".format(self._wid, e))
            self._page_wait = None
            return False

    def _wait_host(self):
        """The window that is actually showing this window's wait.

        ONE QUESTION, ASKED IN ONE PLACE. `wait()` hands a task window's
        wait to its run window — the surface the user is about to see — and
        every other wait method has to ask the same thing or it acts on the
        wrong window. It didn't: the cover sat on the run window while
        `waitprogress` reported to the task window and was dropped, and
        `iswaiting()` answered no there, so `drive_work` stopped reporting
        at all. Kent, 2026-09-16, of the bar just added: "no visible bar."

        Answers `self` when this window hosts its own wait or when nothing
        does, so callers need no special case."""
        holder = getattr(self, '_page_wait', None)
        if holder is not None and getattr(holder, '_exists', False):
            return self
        run = getattr(self, 'runwindow', None)
        if (run is not None and run is not self
                and getattr(run, '_exists', False)):
            theirs = getattr(run, '_page_wait', None)
            if theirs is not None and getattr(theirs, '_exists', False):
                return run
        return self

    def _hide_page_wait(self):
        """Remove the in-page wait, if there is one.

        A WAIT NOBODY CLOSES is this app's worst failure mode (the tryNAgain
        hole), and an in-page one is worse than a dialog because it looks
        like the page itself. So it is cleared from `waitdone`, from
        `resetframe` (a page being rebuilt has no business keeping the old
        cover) and from `on_quit`, and its lifetime is logged — a long one in
        the log is the thing to chase."""
        holder = getattr(self, '_page_wait', None)
        self._page_wait = None
        if holder is None:
            return
        # THE SCROLLING COMES BACK FIRST, and unconditionally: a page left
        # unable to scroll is worse than a visible scrollbar, and this must
        # happen even if destroying the holder below fails.
        try:
            _js(getattr(self, '_wv_window', None), 'setPageWaitCover(false)')
        except Exception as e:
            log.info("window {}: could not restore scrolling after the page "
                     "wait ({!r})".format(self._wid, e))
        held = time.monotonic() - getattr(self, '_page_wait_at', 0)
        try:
            if getattr(holder, '_exists', False):
                holder.destroy()
            log.info("window {}: page wait cleared after {:.2f}s"
                     "".format(self._wid, held))
        except Exception as e:
            log.info("window {}: could not clear the page wait ({!r})"
                     "".format(self._wid, e))

    def wait(self, msg=None, cancellable=False, thenshow=False):
        # IN THE PAGE WHERE THAT MAKES SENSE. `cancellable` is the one thing
        # a page wait does not do yet — a wait the user must be able to
        # abandon keeps the real dialog, which has the Cancel button.
        if not cancellable and self._page_wait_ok():
            if self._show_page_wait(msg):
                self.showafterwait = False
                # `_wv_visible`, NOT `winfo_viewable()`. The latter reads
                # `_grid_visible`, which for a WINDOW is set True once at
                # construction and never touched by hide/show — so a hidden
                # window reports itself viewable and this reveal never
                # happened. Kent, 2026-09-16: "Did you change the wait? I
                # don't see a difference" — the log showed `page wait shown`
                # one line after `WITHDRAW (hide) requested by
                # getrunwindow()`, i.e. a perfectly good wait screen on a
                # window nobody could see.
                #   A PAGE WAIT WITHOUT ITS WINDOW IS WORSE THAN NO WAIT: it
                # takes the place of the dialog that would have been visible.
                # So this reveal is not an optimisation, it is the feature.
                if not getattr(self, '_wv_visible', True):
                    try:
                        log.info("window {}: revealing it to show its own "
                                 "page wait".format(self._wid))
                        self.deiconify()
                    except Exception as e:
                        log.info("window {}: the page wait could not reveal "
                                 "its own window ({!r})"
                                 "".format(self._wid, e))
                return
        # A WAIT ALREADY ON SCREEN IS THE ONE TO UPDATE. This window may not
        # be the right host for a page wait — a task window is not kiosk —
        # while its own RUN window is standing there showing one. Raising the
        # dialog as well would put a second wait surface over the first, and
        # the run window is the one that will become the page.
        #   `sort_ui.py:709` already names this as the wrong target: the
        # sort-page build waits via `with task.waiting()` on the TaskWindow,
        # "so its showafterwait is False and waitdone reveals nothing". That
        # was harmless while the dialog was the only visible thing; with a
        # page wait it is a collision. Kent's log, 2026-09-16: `page wait
        # shown` on window 1347, then `DEICONIFY` on window 86 — the dialog —
        # with "Gathering groups", which is the one he could actually see.
        #   WHENEVER ONE EXISTS, not only when it already shows a wait. The
        # first version required a page wait to be up on the run window
        # already, which is false for the earliest wait of a task's setup —
        # the parser's "Loading Affixes". Kent corrected the reason I gave
        # for that (2026-09-16): "the task window was already withdrawn at
        # that point. runcheck was called, whether or not getrunwindow was,
        # but that was a close race, if not." So it is not that no surface
        # exists; it is that this window has just been withdrawn while the
        # window the user is about to see is standing right there.
        #   The race is why this is a check and not an assumption: if the run
        # window does not exist yet, the dialog is the only thing that can be
        # shown, and it is shown.
        run = getattr(self, 'runwindow', None)
        if (run is not None and run is not self
                and getattr(run, '_exists', False)):
            try:
                hostable = run._page_wait_ok()
            except Exception:
                hostable = False
            if hostable:
                log.info("window {}: wait({!r}) handed to run window {} — "
                         "the surface the user is about to see"
                         "".format(self._wid, msg, getattr(run, '_wid', '?')))
                run.wait(msg=msg, cancellable=cancellable, thenshow=thenshow)
                return
        ww = self._waitwindow()
        if ww is None:
            return
        if ww.active:
            if msg:
                ww.msg(msg)
            if cancellable:
                ww.make_cancellable()
            if thenshow:
                self.showafterwait = True
                ww.reveal_parent = self
                ww.do_reveal = True
            return
        # DO NOT HIDE THE PAGE. Kent, 2026-09-11, opening Add and Parse Words
        # with Audio: "the page opens (almost?) complete, then goes away to
        # build the wait dialog, which returns almost immediately."
        #
        # Withdrawing the caller is right under tkinter and wrong here. There
        # it exists so a slow render happens under cover of "Loading…" rather
        # than on a blank screen (the 1.3.38 XWayland finding in
        # ui_tkinter.waitdone). Under webview the page is ALREADY rendered
        # when the wait starts, so hiding it removes a finished window from
        # the screen and puts it back a moment later — the flash he saw, and
        # the opposite of what the hiding was for.
        #
        # `showafterwait` stays True so `waitdone` still reveals the window:
        # some callers reach wait() while genuinely withdrawn (a task window
        # mid-construction), and revealing one that was never hidden costs a
        # no-op show.
        self.showafterwait = bool(self.winfo_viewable()) or bool(thenshow)
        # IMMEDIATELY — the 400ms delay tried on 2026-09-11 was reverted the
        # same day. `after()` runs on the event loop and this app's slow work
        # is synchronous, so the scheduled dialog appeared only once the work
        # was done: the indicator was guaranteed absent during exactly the
        # operations it exists for (a 35s build with a blank screen). Not
        # hiding the page, above, is what actually fixed the flicker.
        ww.activate(parent=self, msg=msg, cancellable=cancellable,
                    reveal=self.showafterwait)

    def waitdone(self):
        # THE PAGE WAIT FIRST, and unconditionally: the early return below
        # means "no wait WINDOW is active", which says nothing about a cover
        # sitting on this page. Returning before clearing it would leave the
        # user reading "Please Wait…" over a finished page — a wait nobody
        # closes, which is this app's worst failure mode. No-op on windows
        # that cannot have one.
        #   AND ON THE WINDOW HOSTING OURS, for the same reason
        # `waitprogress` has to go there: a task window whose wait was handed
        # to its run window would otherwise clear nothing and leave the cover
        # up. See `_wait_host`.
        host = self._wait_host()
        if host is not self:
            host._hide_page_wait()
        self._hide_page_wait()
        ww = self._waitwindow(create=False)
        if ww is None or not ww.active:
            return
        # OUR OWN CLAIM'S REVEAL, not the current owner's. Reading
        # `ww.reveal_parent` meant that after a handover an outgoing flow's
        # `waitdone()` revealed the INCOMING flow's page — the shared-window
        # fault in its subtlest form. `release` hands back the claim it
        # dropped, so each flow reveals what it asked to reveal, and the
        # window itself stays up for whoever is still waiting underneath.
        parent, do_reveal = ww.release(by=self)
        if do_reveal and parent is not None \
                and getattr(parent, '_exists', False) \
                and not parent.exitFlag.istrue():
            try:
                parent.deiconify()
            except Exception:
                pass

    def waitprogress(self, x):
        # THE PAGE WAIT OWNS THE PROGRESS when it is the thing on screen.
        # Falling through to the wait window here would report progress into
        # a dialog nobody raised, and leave the visible cover frozen.
        # WHEREVER THE WAIT ACTUALLY IS. See `_wait_host`: a task window's
        # wait is hosted by its run window, and reporting progress to the
        # task window meant reporting it to nobody.
        host = self._wait_host()
        if host is not self:
            host.waitprogress(x)
            return
        holder = getattr(self, '_page_wait', None)
        if holder is not None and getattr(holder, '_exists', False):
            bar = getattr(holder, '_wait_bar', None)
            if bar is not None and x is not None:
                try:
                    # FIRST REPORT BRINGS IT BACK. It starts grid-removed so
                    # a wait that never reports has no bar to look stuck at.
                    if not getattr(bar, '_grid_visible', False):
                        # SAID ONCE PER BAR, because "no visible bar" has
                        # three possible causes and none of them logged
                        # anything: progress never arrives, it arrives at a
                        # window with no cover, or it arrives and the bar
                        # fails to re-grid. This line separates the third
                        # from the first two.
                        log.info("window {}: page wait bar shown (first "
                                 "progress {})".format(self._wid, x))
                        bar.grid()
                    bar.current(x)
                except Exception as e:
                    log.info("window {}: page wait bar not updated ({!r})"
                             "".format(self._wid, e))
            elif bar is None:
                log.info("window {}: page wait has no bar to update — it was "
                         "built before one existed".format(self._wid))
            return
        # PROGRESS WITH NOWHERE TO PUT IT. Not an error — the shared dialog
        # below is a legitimate destination — but it is the answer to "why
        # is there no bar", so it is said rather than left silent. Once per
        # window: this is called per iteration of a long loop.
        if not getattr(self, '_said_no_page_wait_progress', False):
            self._said_no_page_wait_progress = True
            log.info("window {}: progress {} reported with no page wait on "
                     "this window or its run window; it goes to the wait "
                     "dialog".format(self._wid, x))
        ww = self._waitwindow(create=False)
        if ww is None:
            return
        try:
            ww.progress(x, r=4)
            # AND MAKE SURE IT IS ON SCREEN. `activate` grid_removes the bar
            # so a wait that never reports has none, and `progress()` was
            # trusted to bring it back — it re-grids only in its
            # AttributeError branch, i.e. the first time the bar is built.
            # On every later activation the bar exists and stays removed, so
            # the dialog showed a message and nothing else for the whole
            # affix load (Kent's screencast, 2026-09-16, tiles 11-16).
            #   This is the same one-line omission the page wait had, in the
            # older of the two implementations.
            bar = getattr(ww, 'progressbar', None)
            if bar is not None and not getattr(bar, '_grid_visible', False):
                bar.grid()
        except Exception as e:
            log.info("window {}: wait dialog progress {} not shown ({!r})"
                     "".format(self._wid, x, e))

    # ── Driving generator work ────────────────────────────────────────
    # ON THE WINDOW AS WELL AS ON THE ROOT. These three exist on `Root`
    # further down this file and were never copied here, so every call on a
    # task window raised — `sorting_engine.py:666` does
    # `self._get_safe_window().drive_work(gen, on_done=after_presort)` and
    # got "PORT GAP: 'Window' object has no attribute 'drive_work'" the
    # moment a sort check ran (Kent, GTK, 2026-09-15). The safe window is a
    # Window, never the root, so the root's copy could never be reached from
    # there.
    #   `drive_work` is also the ONE member `tasks/ui_protocol.py` and the
    # Tk-shaped API agree on (azt/CLAUDE.md), which makes a window that
    # cannot answer it the worst possible gap in the set.
    #   Duplicated rather than shared because Root and Toplevel duplicate
    # the whole Waitable set in this file; factoring that is its own job and
    # this fault is what the duplication costs.

    def drive_work(self, generator, on_done=None):
        """Consume a work generator one yield at a time, reporting progress.

        Synchronous, unlike tkinter's `after`-chained version: there is no
        Tk event loop to hand control back to between chunks, and the page
        repaints on its own. The cancellation flag is what `cancel_drive_work`
        clears, and the loop checks it every tick so a quit part way through
        stops the work instead of draining it into a dead window.
        """
        self._driving = True
        try:
            for progress in generator or ():
                if not getattr(self, '_driving', True):
                    log.info("window {}: drive_work cancelled part way"
                             "".format(self._wid))
                    break
                if self.iswaiting():
                    self.waitprogress(progress)
        finally:
            self._driving = False
        self.waitdone()
        if on_done:
            on_done()

    def cancel_drive_work(self):
        """Stop a running drive_work. Safe when nothing is running."""
        self._driving = False

    def wait_and_drive_work(self, generator, msg=None, on_done=None,
                            **kwargs):
        """Raise the wait, drive the work, close the wait — tkinter's pairing
        of the two, and the name several call sites use."""
        self.wait(msg=msg, **kwargs)
        self.drive_work(generator, on_done=on_done)

    # The rest of the wait contract, also Root-only until now. `waitcancel`
    # is what a Cancel button sets and `vcs.py`/`lexicon.py` poll;
    # `waitpause`/`waitunpause` are how a dialog raised DURING a wait gets
    # the screen (the wait dialog would otherwise sit over the question it
    # is waiting for the answer to).
    def waitcancel(self):
        self.waitcancelled = True
        log.info("window {}: wait cancel registered".format(self._wid))

    def waitpause(self):
        ww = self._waitwindow(create=False)
        if ww is not None:
            ww.withdraw()
            ww.paused = True

    def waitunpause(self):
        ww = self._waitwindow(create=False)
        if ww is not None and ww.active:
            ww.deiconify()
            ww.paused = False

    def cleanup(self):
        pass


class Window(Toplevel):
    """Application window with outsideframe, frame, progress, exit button."""

    def __init__(self, parent, backcmd=False, exit=True, title="No Title Yet!",
                 choice=None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.title(title)
        self.outsideframe = Frame(self, row=1, column=1, sticky='nsew')
        self.frame = Frame(self.outsideframe, row=1, column=1, sticky='nsew')
        # THE TWO LINKS THAT BOUND EVERY PAGE, and both were missing.
        #
        # A page's content sits at row 1 of `outsideframe`, which sits at row
        # 1 of the window. Neither row was weighted here, so both were
        # CONTENT-SIZED — and Kent's height chain (2026-09-16) showed the
        # cost as plainly as it could: `#root` bounded at the viewport's
        # 1200px with its row at 2378px, and `outsideframe` at 2347px inside
        # it. Every page in the app therefore overflowed the window before
        # any of its own layout was consulted, so no row structure inside
        # `frame` could ever bound the scroller — which is the sort page's
        # double scroll (the page scrolls AND the word list scrolls inside
        # it), and the empty band under the list, and the Exit button 1150px
        # below the bottom of the screen.
        #
        # WHY tkinter NEEDS ONLY ONE OF THESE. It weights `outsideframe`'s
        # row 1 already (`ui_tkinter.py:3767`) and leaves the WINDOW's row 1
        # unweighted, giving rows 0 and 2 weight 3 to centre the content
        # (`Window.post_tk_init`, :3668). It gets away with that because
        # Tk's grid SHRINKS its tracks when the master is too small; CSS Grid
        # overflows instead. So the window's row has to be told here what Tk
        # infers — and that difference is worth stating once: every teardown
        # and every squeeze that tkinter gets for free has to be written out
        # in this backend.
        #
        # Weight 1 rather than 3: the number only matters against a
        # competing weight, and rows 0 and 2 here hold nothing.
        #
        for target in (self, self.outsideframe):
            target.grid_rowconfigure(1, weight=1)
        # AND THE SPACER COLUMNS, which is how tkinter centres a page.
        #
        # `Window.post_tk_init` weights rows and columns 0 and 2 — NOT 1 —
        # with the comment "This centers the r=c=1 frame"
        # (`ui_tkinter.py:3666-3670`): the empty tracks either side absorb
        # the leftover, so the content keeps its own width and ends up in
        # the middle. I skipped the column axis entirely on the grounds that
        # weighting it would stretch the content, which confused two
        # different tracks: weighting column 1 stretches, weighting 0 and 2
        # centres. So a kiosk page sat hard against the left with ~700px
        # empty to its right (Kent, 2026-09-16: "what still hasn't happened
        # is this content centering in the kiosk").
        #
        # ROWS 0 AND 2 ARE LEFT ALONE, deliberately, and this is where we
        # part from tkinter. Weighting them would centre VERTICALLY too, and
        # a kiosk page wants its list to USE the height rather than sit in a
        # band in the middle — row 1 taking the vertical leftover is what
        # lets the scroller bound itself at all (see `_inset_of`'s
        # neighbours and agenda/webview_window_sizing.md). tkinter can
        # afford to centre vertically because Tk shrinks its tracks under
        # pressure; CSS Grid overflows.
        #
        # Costs nothing on a window fitted to its content: with no leftover,
        # a spacer track resolves to zero.
        for column in (0, 2):
            self.grid_columnconfigure(column, weight=3)
        if exit:
            # `cssclass` so the stylesheet can raise it above a page wait —
            # see `.wv-exit` in grid.css. A viewport-wide wait cover would
            # otherwise take the window's only control with it, and one
            # sort-page build measured 21.6 seconds.
            self.exitButton = Button(self.outsideframe, width=10,
                                     cssclass='wv-exit',
                                     text=_("Exit"), cmd=self.on_quit,
                                     font='small', column=2, row=2)

    def progress(self, value, parent=None, **kwargs):
        try:
            self.progressbar.grid() #re-show if a no-progress wait grid_remove()'d it
            self.progressbar.current(value)
        except AttributeError:
            if not parent:
                parent = self.outsideframe
            # UNDER THE CONTENT, NOT IN THE OUTER LEFT COLUMN. `outsideframe`
            # is a three-column grid whose middle column holds `frame` — the
            # window's content — so a bar gridded with no column lands in
            # column 0, to the left of everything it is reporting on, at its
            # minimum width (Kent, 2026-09-15: "wait progress bar is in left
            # column?"). tkinter parents it to `outsideframe` too and gets
            # away with it because `Window.post_tk_init` weights the outer
            # columns, which stretches the bar across; nothing weights them
            # here.
            #   `setdefault`, so a caller that names its own cell still wins.
            kwargs.setdefault('column', 1)
            kwargs.setdefault('sticky', 'ew')
            self.progressbar = Progressbar(parent, **kwargs)
            self.progressbar.current(value)

    def resetframe(self):
        if self.parent and self.parent.exitFlag.istrue():
            return
        if self._exists:
            # A PAGE BEING REBUILT HAS NO BUSINESS KEEPING THE OLD COVER.
            # `getrunwindow` reuses a window by resetting its frame, so
            # without this a page wait raised for the previous page would sit
            # over the next one. See `_hide_page_wait`.
            self._hide_page_wait()
            if hasattr(self, 'frame') and self.frame._exists:
                self.frame.destroy()
            self.frame = Frame(self.outsideframe, row=1, column=1, sticky='nsew')


# ── Waitable mixin (for windows) ─────────────────────────────────────

class Wait(Window):
    """The single 'Please Wait' window (mirror of ui_tkinter.Wait): built ONCE on
    the root and then withdrawn/deiconified rather than destroyed/rebuilt per wait.
    Waitable owns the instance (`root.ww`); wait()/waitdone() call activate()/
    deactivate(). `active` is what iswaiting() reports."""
    def __init__(self, parent, *args, **kwargs):
        kwargs['exit'] = False
        # BORN HIDDEN, not shown and then hidden. This window is built once
        # and spends most of the session withdrawn, so it is the clearest
        # possible case for `withdrawn=True`: without it the window was
        # created VISIBLE and hidden a line later, which queues the hide
        # until the page loads — and on Qt the creation's own map beat that
        # replayed hide, leaving "Please Wait… Loading Affixes" over the
        # whole app for the rest of the session (Kent, 2026-09-15).
        kwargs.setdefault('withdrawn', True)
        super().__init__(parent, *args, **kwargs)
        self.active = False
        self.reveal_parent = None
        self.do_reveal = False
        self.cancelbutton = None
        self.paused = False
        self.withdraw()
        # THE TITLE NAMES THE APP, as tkinter's does. A window saying only
        # "Please Wait!" in the task bar, with no program name, is not
        # identifiable among a dozen others.
        try:
            appname = self._find_root().program.name
        except Exception:
            appname = 'A-Z+T'
        self.title(_("Please Wait! {azt} Dictionary and Orthography Checker "
                     "in Process").format(azt=appname))
        # `self.frame`, NOT `self.outsideframe` — the same parent tkinter
        # uses (:4818). `frame` is the window's CENTRED cell (row/column 1,
        # with 0 and 2 weighted); `outsideframe` is the outer one that holds
        # the Exit and Cancel buttons. Building the wait's own text in the
        # outer frame is why the webview wait came up flush to the top-left
        # while tkinter's sat in the middle (Kent's three-way comparison,
        # 2026-09-15).
        self.l = Label(self.frame, text=_("Please Wait..."),
                       font='title', anchor='c', row=0, column=0, sticky='we')
        self.l1 = Label(self.frame, text='',
                        font='default', anchor='c', row=1, column=0,
                        sticky='we')
        # AND THE CARD IMAGE, which was missing entirely. It is most of what
        # the wait window IS — a user looking at a long operation sees the
        # app's own picture rather than a blank field, and tkinter has shown
        # it since the window existed (:4824). Same gate: a root created
        # with noimagescaling has no scaled photos to draw.
        if not getattr(getattr(self, '_find_root', lambda: None)(),
                       'noimagescaling', False):
            self.l2 = Label(self.frame, image='small', text='',
                            row=2, column=0, sticky='we', padx=50, pady=50)

    def close(self):
        self.on_quit()

    def cancel(self):
        (self.reveal_parent or self.parent).waitcancel()

    def make_cancellable(self):
        # Idempotent (the window is reused): build once, then re-show.
        if getattr(self, 'cancelbutton', None) is None:
            self.cancelbutton = Button(self.outsideframe, text='Cancel',
                                       cmd=self.cancel, row=3, column=0, sticky='e')
        else:
            self.cancelbutton.grid()

    def hide_cancel(self):
        if getattr(self, 'cancelbutton', None) is not None:
            self.cancelbutton.grid_remove()

    def msg(self, msg):
        log.info(f"Waiting: {msg}")
        self.l1['text'] = msg

    # ── ONE WINDOW, A STACK OF CLAIMS ─────────────────────────────────
    # THE SINGLE-WINDOW SCHEMA IS DELIBERATE, so a second flow wanting the
    # wait is a HANDOVER and not a conflict. Kent, 2026-09-16: "we set up a
    # single wait window schema, at one point, so if one is going to take
    # over another in process, we'd want to transfer ownership sanely."
    #
    # WHY IT COMES UP NOW. Page events arrive on their own threads under
    # pywebview (`webview/util.py:_call`), so one task's build and another's
    # run side by side and both reach for this one window. Two things then
    # go wrong with a single `owner` field:
    #
    #   * the outgoing task's `with waiting(...)` closes its `waitdone()` in
    #     a `finally` and takes the INCOMING task's wait down with it — half
    #     of Kent's chain, "…Wait(Parser)-Wait(SortV)": not two waits so
    #     much as two flows fighting over one;
    #   * and simply DECLINING that close is not enough either, because when
    #     the taker finishes the wait would disappear while the first flow
    #     is still working.
    #
    # A stack answers both: releasing a claim that is not on top just drops
    # it, and releasing the top one falls back to whatever is still waiting
    # underneath — its message restored — or closes the window when nothing
    # is. Each claim carries its own reveal target, so a flow's page is
    # revealed by ITS release and not by someone else's.
    #   See agenda/webview_flows_run_concurrently.md.
    owner = None

    def _claim_list(self):
        claims = getattr(self, '_claims', None)
        if claims is None:
            claims = []
            self._claims = claims
        return claims

    def _apply_top_claim(self):
        """Show the window for the newest claim, or hide it if there are
        none left."""
        claims = self._claim_list()
        if not claims:
            self.active = False
            self.owner = None
            self.reveal_parent = None
            self.do_reveal = False
            self.withdraw()
            return
        top = claims[-1]
        self.owner = top['by']
        self.reveal_parent = top['by']
        self.do_reveal = top['reveal']
        if top['msg']:
            self.msg(top['msg'])
        if getattr(self, 'progressbar', None) is not None:
            self.progressbar.grid_remove()  # progress() re-grids on demand
        if top['cancellable']:
            self.make_cancellable()
        else:
            self.hide_cancel()
        self.paused = False
        self.active = True
        self.deiconify()

    def activate(self, parent, msg=None, cancellable=False, reveal=True):
        claims = self._claim_list()
        # RE-ACTIVATING IS UPDATING YOUR OWN CLAIM, not making a second one:
        # `wait()` is called repeatedly with new messages by the same flow.
        mine = [c for c in claims if c['by'] is parent]
        self._claims = [c for c in claims if c['by'] is not parent]
        if self._claims and self.active:
            # A HANDOVER IS A SYMPTOM, NOT A FEATURE. Kent, on being told
            # the stack lets the wait fall back to whoever was still
            # waiting: "hopefully we won't have THAT kind of silliness. But
            # the stack is preparedness, in case." Two flows wanting this
            # window at once means one of them should already have stopped —
            # `TaskBase._on_close`/`still_wanted` is what is supposed to
            # ensure that. So this line is logged as the thing to CHASE, and
            # a run with no such line is the actual goal; the stack only
            # keeps the symptom survivable while it is still possible.
            log.info("wait window: window {} takes it over from window {} "
                     "({} claim(s) still open underneath). TWO FLOWS WANT "
                     "THE WAIT AT ONCE — one of them should have stopped; "
                     "see agenda/webview_flows_run_concurrently.md"
                     "".format(getattr(parent, '_wid', '?'),
                               getattr(self.owner, '_wid', '?'),
                               len(self._claims)))
        elif mine:
            pass            # same flow, new message; nothing to announce
        self._claims.append({'by': parent, 'msg': msg,
                             'reveal': reveal, 'cancellable': cancellable})
        self._apply_top_claim()

    def release(self, by=None):
        """Give up `by`'s claim. Returns that claim's (parent, do_reveal).

        `by=None` drops EVERY claim and hides the window — what teardown and
        the Cancel button want, since neither is a flow handing the wait
        back to another.

        A claim that is not on top is simply removed: the flow that owns it
        has finished, the window stays up for whoever is using it now, and
        that flow's own release will close it. Releasing the top claim falls
        back to the next one and restores its message."""
        claims = self._claim_list()
        if by is None:
            self._claims = []
            self._apply_top_claim()
            return (None, False)
        mine = [c for c in claims if c['by'] is by]
        if not mine:
            # Never raised one, or it was already released. Not an error:
            # `waitdone` is called defensively all over this app.
            return (None, False)
        was_top = claims[-1]['by'] is by
        self._claims = [c for c in claims if c['by'] is not by]
        if not was_top:
            log.info("wait window: window {} released its claim, but window "
                     "{} is using the window now — leaving it up"
                     "".format(getattr(by, '_wid', '?'),
                               getattr(self.owner, '_wid', '?')))
        elif self._claims:
            log.info("wait window: window {} released it; handing back to "
                     "window {}, which is still waiting"
                     "".format(getattr(by, '_wid', '?'),
                               getattr(self._claims[-1]['by'], '_wid', '?')))
        self._apply_top_claim()
        claim = mine[-1]
        return (claim['by'], claim['reveal'])

    def deactivate(self, by=None):
        """Backwards-compatible name for `release`, kept because the cancel
        button and teardown call it. Returns True when the window ended up
        closed, which is what those callers mean by "done"."""
        self.release(by=by)
        return not self.active


# ── Root ──────────────────────────────────────────────────────────────

def wrap_to_container(container, cols=1, reserve=0, minimum=60, maxdepth=2,
                      targets_parent=None, **kwargs):
    """No-op mirror of ui_tkinter.wrap_to_container, so consumers can call
    `ui.wrap_to_container(...)` regardless of backend (the chooser and the
    verify page both do; without this they'd AttributeError here).

    THE SIGNATURE IS PART OF THE MIRROR, and this one was short by a
    parameter. `sort_ui.py:518` passes `targets_parent=buttonframe`, which
    tkinter's version takes (:2063), so the sort page raised
    `TypeError: wrap_to_container() got an unexpected keyword argument
    'targets_parent'` inside a button callback — where `on_event` logs it
    and carries on, so the page simply stopped building (Kent, 2026-09-15).
    A no-op that cannot be CALLED is not a no-op.
      `**kwargs` as well, deliberately: the point of this function is that
    the caller need not know which backend it is talking to, and a
    keyword-for-keyword copy of a signature is exactly the kind of parity
    that drifts. Anything tkinter grows later is accepted and ignored here
    rather than raising in a callback nobody sees.

    Nothing to do: the tkinter version exists because Tk needs a wraplength in
    PIXELS, computed from a width only known at <Configure> time. In a browser
    the containing box wraps text itself, which is what the tkinter helper is
    laboriously emulating. Returns a callable so a caller that re-applies after
    a build still has something to call."""
    return lambda event=None: None
_app_root = None  # the application's main themed Root (set in Root.__init__)
def default_root():
    """The app's main themed Root (with .theme/.photo), or None — mirror of
    ui_tkinter.default_root() so consumers can call ui.default_root()
    regardless of backend. Excludes dummy/contextless and fakeroot Roots."""
    if _app_root is not None and getattr(_app_root, '_exists', False):
        return _app_root
    return None
def _screen_pixels():
    """(width, height) of the primary screen, in pixels, BEFORE any page exists.

    `program.screenw`/`screenh` are set by tkinter's `Theme.setscale`
    (ui_tkinter.py:589-590) and read by two task builders that size a button
    frame against the screen (`tasks.py:1955`, `transcribe_glyph.py:342` —
    the raw layout arithmetic ADR 0004 D3 lists for cleanup). This backend
    never set them, so opening a glyph window under webview died with
    `'App' object has no attribute 'screenw'` (Kent, 2026-09-22, twice). The
    webview `setscale` is not the place: nothing calls it at boot — the only
    `.setscale()` call in the app is tkinter's own — so the root sets them
    at construction, as early as tkinter does.

    pywebview's `screens` is usable before `start()`; the JS `screen.width`
    route is not, since no page is loaded yet. A guess is logged as one."""
    try:
        if webview is not None:
            s = webview.screens[0]
            w, h = int(s.width), int(s.height)
            if w > 0 and h > 0:
                return w, h
    except Exception as e:
        log.info("could not read the screen size from pywebview (%r); "
                 "assuming 1920x1080 until a page can say", e)
    return 1920, 1080


class Root(_WebviewWidget):
    """The root window — starts the pywebview event loop."""

    is_window = True   # see Toplevel.is_window

    def __init__(self, program=None, *args, **kwargs):
        log.info(f"Root called with {program=}")
        if not program:
            from dummy import App
            program = App()

        self.program = program
        self.parent = None
        self.mainwindow = False
        self._wid = _next_wid()
        self._children = []
        self._exists = True
        self._bindings = {}
        self._wv_deferred = []
        self._config = {}
        self._props = {}
        self._has_grid = False
        self._grid_opts = {}
        self._gridwait = False
        self._grid_visible = True
        self.waitcancelled = False
        self.showafterwait = True
        self._wv_loaded = threading.Event()
        self._wv_js_queue = []
        self._wv_queue_lock = threading.RLock()   # see `_drain_wv_js_queue`

        noimagescaling = kwargs.pop('noimagescaling', False)

        # Theme
        if hasattr(program, 'theme') and isinstance(program.theme, Theme):
            self.theme = program.theme
        else:
            self.theme = Theme(program, noimagescaling=noimagescaling)

        # What tkinter's Theme.setscale publishes; see `_screen_pixels`.
        program.screenw, program.screenh = _screen_pixels()
        log.info("screen %dx%d px (program.screenw/screenh)",
                 program.screenw, program.screenh)

        self.renderer = Renderer()
        self.exitFlag = ExitFlag()
        self.wraplength = 600

        # Create the main webview window
        self._wv_window = None
        if webview:
            html_path = os.path.join(_HTML_DIR, 'base.html')
            self._wv_window = webview.create_window(
                program.name if hasattr(program, 'name') else 'A-Z+T',
                url=html_path if os.path.exists(html_path) else None,
                html='<div id="root"></div>' if not os.path.exists(html_path) else None,
                js_api=_api,
                width=1024, height=768,
                # THE ROOT IS NEVER SEEN, so create it hidden and spare the
                # user a window that appears only to vanish. Under tkinter
                # the root is withdrawn for the whole session and every
                # visible window is a Toplevel; this backend was creating it
                # visible purely because nothing passed `hidden=`, and the
                # app withdraws it a moment later — the first of the two
                # startup flashes.
                #
                # `hidden=True` is unusable for a window that must appear
                # later (measured: show() never maps it — see
                # tests/manual/webview_multiwindow/hide_show.py), and that is
                # exactly why it is safe HERE and nowhere else: nothing shows
                # the root. deiconify() logs a warning if anything tries.
                hidden=True,
            )
            self._created_hidden = True
            if self._wv_window:
                _all_wv_windows.append(self._wv_window)
                _register_window_owner(self._wv_window, self)

        if not hasattr(program, 'tk_root'):
            program.tk_root = self
        # dummy.App sets .dummy=True; exclude dummy/contextless roots and the
        # image-scaling fakeroot. What's left is the real app root.
        if not getattr(program,'dummy',False) and not noimagescaling:
            global _app_root
            _app_root = self

    def _push_theme(self):
        """Push theme CSS variables to the webview after it's loaded."""
        if self._wv_window and self.theme:
            css_vars = self.theme.css_vars()
            try:
                self._wv_window.evaluate_js(f'setThemeVars({json.dumps(css_vars)})')
            except Exception as e:
                log.debug(f"Theme push failed: {e}")

    def _wv_call(self, method, *args):
        """Call a method on the pywebview window, deferring if not started."""
        if not self._wv_window:
            return
        if not _started.is_set():
            self._wv_deferred.append((method, args))
            return
        if method in ('show', 'hide'):
            log.info("window {}: pywebview {}() now".format(
                getattr(self, '_wid', 'root'), method))
        try:
            getattr(self._wv_window, method)(*args)
        except Exception as e:
            log.debug(f"Root wv_call {method} failed: {e}")

    def _flush_wv_calls(self):
        # COALESCE VISIBILITY: only the LAST show/hide matters. These were
        # queued because the window was not ready, so replaying them
        # literally makes the window blink through states the user was never
        # meant to see — Kent, 2026-09-08, on the splash: "Are the first two
        # flashes necessary? I can't see users not being affected by that."
        # A queued hide followed by a queued show is a no-op in intent; the
        # user should see the end state, not the journey to it.
        if self._wv_deferred:
            queued = list(self._wv_deferred)
            last_vis = None
            for method, args in queued:
                if method in ('show', 'hide'):
                    last_vis = (method, args)
            kept = [(m, a) for m, a in queued if m not in ('show', 'hide')]
            if last_vis is not None:
                kept.append(last_vis)
            dropped = len(queued) - len(kept)
            self._wv_deferred = kept
            log.info("window {}: replaying deferred {}{}".format(
                getattr(self, '_wid', 'root'),
                [m for m, _a in kept],
                " (collapsed {} redundant show/hide)".format(dropped)
                if dropped else ''))
        for method, args in self._wv_deferred:
            try:
                getattr(self._wv_window, method)(*args)
            except Exception as e:
                log.debug(f"Root deferred wv_call {method} failed: {e}")
        self._wv_deferred.clear()

    # Same window verbs as Toplevel — ui_shell asks for these on the root as
    # well as on task windows (:2739 and :2952).
    def attributes(self, *args):
        if len(args) >= 2 and args[0] in ('-fullscreen', '-zoomed'):
            self._set_fullscreen(bool(args[1]))
        return None

    wm_attributes = attributes

    def _set_fullscreen(self, want):
        """Off by default; see Toplevel._set_fullscreen for why."""
        if bool(getattr(self, '_is_fullscreen', False)) == bool(want):
            return
        if want and _switch('--no-kiosk'):
            log.info("root window: fullscreen requested, NOT applied "
                     "(--no-kiosk is in force)")
            return
        self._is_fullscreen = bool(want)
        self._wv_call('toggle_fullscreen')

    def takekioskscreen(self, event=None):
        self._set_fullscreen(True)
        self.bind('<Escape>', self.releasefullscreen)
        # Double-click is bound once, at load, to `_dblclick_fit`, which
        # routes to release-fullscreen while we are fullscreen. Binding it
        # again here would run the handler twice per click.

    def takefullscreen(self, event=None):
        self.takekioskscreen(event)

    def releasefullscreen(self, event=None):
        """Leave fullscreen — and then fit the window to its content.

        Without the refit the window snaps back to the size it was CREATED
        at (800x600) while holding a page laid out for the whole screen, so
        it clips on the right and bottom. fit_to_content() runs once at page
        load and is skipped while fullscreen, so leaving fullscreen is the
        only other moment its answer changes.

        Deferred rather than immediate: the toggle has to reach the window
        manager before the window's own dimensions mean anything, and
        fit_to_content compares against them."""
        self._set_fullscreen(False)
        if hasattr(self, 'fit_to_content'):
            self.after(250, self.fit_to_content)

    def bind_all(self, event, handler, add=None):
        return self.bind(event, handler, add=add)

    def unbind_all(self, event=None):
        return self.unbind(event)

    def _root(self):
        return self

    def mainloop(self, setup_callback=None):
        """Start the pywebview event loop.

        If *setup_callback* is provided it is called in a **background thread**
        once the webview has loaded.  This lets callers run blocking startup
        code (file-chooser dialogs, splash screens, etc.) after the event loop
        is live — avoiding the deadlock that occurs when ``wait_window()`` is
        called before ``webview.start()``.
        """
        if webview:
            def on_loaded():
                # BOTH GATES OPEN ONLY ONCE THEIR QUEUES ARE EMPTY, and they
                # open FIRST, because everything below needs a live page:
                # `_log_engine_in_use` reads a value back out of `_js` (a
                # queued call returns None, so the engine would go unlogged)
                # and `_flush_wv_calls` refuses to run until `_started`.
                # Order matters between the two: a call made before the
                # engine started is in the GLOBAL queue and one made after is
                # in this window's, so the global one has to go out first or
                # the window's later calls would precede it. See `_js`.
                _flush_js_queue()          # drains, then sets `_started`
                self._drain_wv_js_queue()  # drains, then sets `_wv_loaded`
                _log_engine_in_use(self._wv_window)
                # X11 or Wayland, from the toolkit and the open socket rather
                # than from what GTK/Qt defaults are believed to be. Here
                # beside the engine line because both answer "what are we
                # actually running on"; a separate `events.loaded` handler
                # registered nearby did not report at all, and this one
                # demonstrably fires. See agenda/wayland_freeze_audit.md.
                from utilities import display
                display.report('pywebview {} running'.format(
                                                _engine() or 'default'))
                self._push_theme()
                _badge(self._wv_window, 'ROOT (no task widgets live here)')
                self._flush_wv_calls()
                # Flush deferred calls on all child Toplevels
                for child in self._children:
                    if hasattr(child, '_flush_wv_calls'):
                        child._flush_wv_calls()
                if setup_callback:
                    def _safe_setup():
                        try:
                            setup_callback()
                        except Exception:
                            import traceback
                            log.error("Setup callback failed:\n" + traceback.format_exc())
                    t = threading.Thread(target=_safe_setup, daemon=True)
                    t.start()
            if self._wv_window:
                self._wv_window.events.loaded += on_loaded
            # Before the GUI toolkit exists: prgname/WM_CLASS is what the
            # desktop matches against azt's .desktop file for the dock icon,
            # and --gdk-backend/--qt-platform must be exported before the
            # toolkit picks a transport.
            _app_identity(self.program)
            _apply_transport_switches()
            _apply_dmabuf_default()
            kwargs = _start_kwargs(self.program)
            icon = _icon_path(self.program)
            # WINDOWS TAKES ONLY A .ico, AND KILLS THE APP OVER IT. The
            # EdgeChromium backend hands this to System.Drawing.Icon through
            # pythonnet, which rejects a PNG — and not with a Python
            # exception we could catch, but as an unhandled .NET
            # ArgumentException on a background thread:
            #
            #   Unhandled Exception: System.ArgumentException: Argument
            #   'picture' must be a picture that can be used as an Icon
            #       at System.Drawing.Icon.Initialize(Int32, Int32)
            #
            # So EVERY `--webview` run died on Windows 11, right after
            # "Using webview engine edgechromium" (Kim's machine, 2026-09-24).
            # The `TypeError` guard below cannot help: that catches pywebview
            # REFUSING the argument, and here it accepted it and crashed
            # later. `theme.photo` holds PNGs, so on Windows the icon is
            # simply not passed — a generic icon is a cost worth paying for
            # an app that starts.
            if icon and platform.system() == 'Windows' \
                    and not str(icon).lower().endswith('.ico'):
                icon = _ico_for(icon)
            if icon:
                kwargs['icon'] = icon
            try:
                webview.start(**kwargs)
            except TypeError as e:
                # `icon=` is not accepted by every pywebview version or
                # backend. Losing the icon must not stop the app, so drop it
                # and say so rather than failing to start.
                if 'icon' not in str(e) or 'icon' not in kwargs:
                    raise
                log.info("pywebview rejected icon= ({}); starting without it"
                         "".format(e))
                kwargs.pop('icon', None)
                webview.start(**kwargs)

    def withdraw(self):
        """As Toplevel.withdraw: say who hid it."""
        try:
            import traceback as _tb
            frame = _tb.extract_stack(limit=2)[0]
            log.info("root window: WITHDRAW (hide) requested by {}:{} in {}()"
                     "".format(frame.filename.rsplit('/', 1)[-1],
                               frame.lineno, frame.name))
        except Exception as e:
            log.info("root window: WITHDRAW (hide) requested, caller unknown "
                     "({})".format(e))
        self._wv_call('hide')

    def lift(self, aboveThis=None):
        """As Toplevel.lift: pywebview has no stacking API, so show() is the
        honest equivalent. Here for the same reason — tkinter's root answers
        `lift()`, so anything that calls it must not hit AttributeError.

        (Placed here on the second attempt: the first landed a duplicate in
        Toplevel instead, where the later definition silently overrode the
        earlier one and made every window log itself as "root window". A
        method added twice to one class is not an error Python reports.)
        """
        log.info("root window: LIFT (show, no stacking API) requested")
        self._wv_call('show')

    def deiconify(self):
        log.info("root window: DEICONIFY (show) requested")
        if getattr(self, '_created_hidden', False):
            # Not a refusal — the call still goes through — but a window
            # created hidden does not map on show() under pywebview, so if
            # this ever fires the root genuinely needs to be visible and
            # creating it hidden was the wrong call. Say so rather than
            # leaving a silently missing window.
            log.warning("root window was created hidden, so show() will "
                        "probably not map it — if the root is meant to be "
                        "visible, stop creating it hidden")
        self._wv_call('show')

    def title(self, text=None):
        """Getter with no argument, as on Toplevel — same reason (main.py:493
        splits the result)."""
        if text is None:
            return getattr(self, '_title_text', '')
        self._title_text = text
        self._wv_call('set_title', text)
        return text

    def protocol(self, name, func):
        """`WM_DELETE_WINDOW` — what to run when the user closes the window.

        WAS A NO-OP, so the close box did nothing but close. Three call sites
        depend on it and each loses something different:

          * `sound_ui.py:893` — `on_quit`, which RESTORES THE TASK WINDOW.
            Without this, closing Sound Settings with the X left the user
            with no visible window at all; the Done button worked because it
            calls `on_quit` directly. (That restore was itself added today,
            so the fix was half-dead on arrival under webview.)
          * `tasks/alphabet_chart.py:59` and
            `tasks/alphabet_comparison.py:54` — `taskchooser.gettask`, so
            closing either page returns to the chooser. Without it the page
            closes and nothing comes back.

        IT INTERCEPTS THE CLOSE. In tkinter `WM_DELETE_WINDOW` replaces the
        close: the window does NOT go away unless the handler makes it. My
        first version let pywebview close the window anyway and called the
        handler alongside, which is a different contract — and Kent spotted
        the consequence (2026-09-11): the alphabet pages hand the close to
        `taskchooser.gettask`, so if the window is closed out from under that
        call, whatever `gettask` decides to reuse or rebuild is being torn
        down behind it.

        So the `closing` handler returns False, cancelling the native close,
        and the app owns what happens next — exactly as under tkinter, where
        a handler that forgets to destroy leaves an unclosable window. All
        three call sites do dispose of the window: `on_quit` hides it,
        `gettask` finishes the task through `finish_task_ui`.
        """
        if name != 'WM_DELETE_WINDOW' or not func:
            return
        # ONE SUBSCRIBER, A SWAPPABLE HANDLER. `protocol()` gets called more
        # than once for a window now that every window is given a default
        # (see `_wire_default_close`), and `closing += …` ADDS rather than
        # replaces — so two calls would leave both handlers running, and the
        # app would return to the chooser AND quit. tkinter's `protocol`
        # replaces; this keeps one subscription and swaps what it dispatches.
        self._delete_handler = func
        if getattr(self, '_closing_wired', False):
            log.info("window {}: close box re-pointed at {}".format(
                        self._wid, getattr(func, '__name__', func)))
            return
        wv = getattr(self, '_wv_window', None)
        events = getattr(wv, 'events', None)
        closing = getattr(events, 'closing', None) if events else None
        if closing is None:
            log.info("window {}: this pywebview has no closing event; the "
                     "close box will not run {}".format(
                        self._wid, getattr(func, '__name__', func)))
            return

        def _on_closing():
            handler = getattr(self, '_delete_handler', None)
            try:
                if handler:
                    handler()
            except Exception as e:
                log.error("window %s: the close handler raised (%s)",
                          self._wid, e)
            # False CANCELS the native close — see the docstring. The handler
            # disposes of the window itself, or deliberately keeps it.
            return False
        try:
            closing += _on_closing
            self._closing_wired = True
            log.info("window {}: close box wired to {}".format(
                        self._wid, getattr(func, '__name__', func)))
        except Exception as e:
            log.info("window {}: couldn't wire the close box ({})"
                     "".format(self._wid, e))

    def iconphoto(self, default, *args):
        pass

    def on_quit(self, to_root=False, event=None):
        # SAY SO BEFORE THE LOG IS CLOSED. This logged nothing, and the next
        # line shuts logging down — so a deliberate quit left a log that
        # simply STOPS, with no message, no traceback and no signal. That is
        # byte-for-byte what a crash looks like from outside, and it is why
        # three rounds went on trying to tell "the app died" from "the app
        # quit" (Kent, 2026-09-15/16, several silent deaths).
        #   WHO ASKED, too. The escalation path is real: a Toplevel with
        # `ismainwindow` calls `self.parent.on_quit(to_root=True)`, so any
        # window that happens to hold that flag can take the program with
        # it. If one of the silent deaths was this, the caller named here is
        # the answer.
        try:
            import traceback as _tb
            frame = _tb.extract_stack(limit=3)[0]
            who = '{}:{} in {}()'.format(frame.filename.rsplit('/', 1)[-1],
                                         frame.lineno, frame.name)
        except Exception:
            who = 'caller unknown'
        log.info("PROGRAM QUIT requested by %s (to_root=%s) — this is a "
                 "deliberate exit, not a crash; the log ends here because "
                 "logging is shut down next", who, to_root)
        self.exitFlag.true()
        logsetup.shutdown()
        if self._wv_window and _started.is_set():
            try:
                self._wv_window.destroy()
            except Exception:
                pass

    def _waitwindow(self, create=True):
        """The single reused Wait window, owned by the app root (built once, then
        withdrawn/deiconified). Mirror of ui_tkinter._waitwindow; resolves the root
        via default_root(), falling back to self when self is itself a root."""
        root = default_root()
        if root is None or not getattr(root, '_exists', False):
            root = self if getattr(self, 'parent', True) is None else None
        if root is None:
            return None
        ww = getattr(root, 'ww', None)
        if ww is None or not getattr(ww, '_exists', False):
            if not create:
                return None
            ww = Wait(root)
            root.ww = ww
        return ww

    def iswaiting(self):
        ww = self._waitwindow(create=False)
        return ww is not None and getattr(ww, 'active', False)

    @contextmanager
    def waiting(self, msg=None, **kwargs):
        """Context-manager form of wait()/waitdone(): closes the wait dialog
        even if the body raises or returns early. Mirror of ui_tkinter."""
        self.wait(msg=msg, **kwargs)
        try:
            yield self
        finally:
            self.waitdone()

    def wait(self, msg=None, cancellable=False, thenshow=False):
        ww = self._waitwindow()
        if ww is None:
            return
        if ww.active:
            if msg:
                ww.msg(msg)
            if cancellable:
                ww.make_cancellable()
            if thenshow:
                self.showafterwait = True
                ww.reveal_parent = self
                ww.do_reveal = True
            return
        # NO WITHDRAW — see the other copy of this method for why. Kept
        # CHARACTER-FOR-CHARACTER identical to it from here down: these two
        # are meant to mirror each other, and every time they have differed
        # by something meaningless — `bool(x) or bool(y)` against `x | y`,
        # then a hand-written comment against a generated one — an edit has
        # reached one and not the other. Twice in one afternoon.
        self.showafterwait = bool(self.winfo_viewable()) or bool(thenshow)
        # IMMEDIATELY — the 400ms delay tried on 2026-09-11 was reverted the
        # same day. `after()` runs on the event loop and this app's slow work
        # is synchronous, so the scheduled dialog appeared only once the work
        # was done: the indicator was guaranteed absent during exactly the
        # operations it exists for (a 35s build with a blank screen). Not
        # hiding the page, above, is what actually fixed the flicker.
        ww.activate(parent=self, msg=msg, cancellable=cancellable,
                    reveal=self.showafterwait)

    def waitdone(self):
        # THE PAGE WAIT FIRST, and unconditionally: the early return below
        # means "no wait WINDOW is active", which says nothing about a cover
        # sitting on this page. Returning before clearing it would leave the
        # user reading "Please Wait…" over a finished page — a wait nobody
        # closes, which is this app's worst failure mode. No-op on windows
        # that cannot have one.
        #   AND ON THE WINDOW HOSTING OURS, for the same reason
        # `waitprogress` has to go there: a task window whose wait was handed
        # to its run window would otherwise clear nothing and leave the cover
        # up. See `_wait_host`.
        host = self._wait_host()
        if host is not self:
            host._hide_page_wait()
        self._hide_page_wait()
        ww = self._waitwindow(create=False)
        if ww is None or not ww.active:
            return
        # OUR OWN CLAIM'S REVEAL, not the current owner's. Reading
        # `ww.reveal_parent` meant that after a handover an outgoing flow's
        # `waitdone()` revealed the INCOMING flow's page — the shared-window
        # fault in its subtlest form. `release` hands back the claim it
        # dropped, so each flow reveals what it asked to reveal, and the
        # window itself stays up for whoever is still waiting underneath.
        parent, do_reveal = ww.release(by=self)
        if do_reveal and parent is not None \
                and getattr(parent, '_exists', False) \
                and not parent.exitFlag.istrue():
            try:
                parent.deiconify()
            except Exception:
                pass

    def waitprogress(self, x):
        ww = self._waitwindow(create=False)
        if ww is None:
            return
        try:
            ww.progress(x, r=4)
        except Exception:
            pass

    def drive_work(self, generator, on_done=None):
        """Consume a work generator one yield at a time, letting the event
        loop breathe. Webview stub — runs synchronously for now."""
        self._driving = True
        try:
            for progress in generator or ():
                if not getattr(self, '_driving', True):
                    log.info("drive_work cancelled part way")
                    break
                if self.iswaiting():
                    self.waitprogress(progress)
        finally:
            self._driving = False
        self.waitdone()
        if on_done:
            on_done()

    def cancel_drive_work(self):
        """Stop a running drive_work. tkinter cancels the pending `after`
        chain; this runs synchronously, so it sets a flag the loop checks.

        The reason it exists is the same in both: a long build keeps draining
        the event loop after the user has QUIT the window, starving whatever
        modal comes next. Missing here until the backend-parity audit found
        it (2026-09-11) — and because `drive_work` is synchronous, a caller
        that cancelled got an AttributeError instead of a stop.
        """
        self._driving = False

    def wait_and_drive_work(self, generator, msg=None, on_done=None,
                            **kwargs):
        """Show the wait dialog, drive the work, close it. tkinter's pairing
        of the two, and the name several call sites use."""
        self.wait(msg=msg, **kwargs)
        self.drive_work(generator, on_done=on_done)

    def waitcancel(self):
        self.waitcancelled = True

    def waitpause(self):
        ww = self._waitwindow(create=False)
        if ww is not None:
            ww.withdraw()
            ww.paused = True

    def waitunpause(self):
        ww = self._waitwindow(create=False)
        if ww is not None and ww.active:
            ww.deiconify()
            ww.paused = False

    def lower(self, belowThis=None):
        """The pair of `lift`, on the root as well — `ui_shell` asks for
        these on the root and on task windows alike, and tkinter's root
        answers both. pywebview has no stacking API, so hiding is the closest
        honest thing; see Toplevel.lower.
        """
        log.info("root window: LOWER (hide, no stacking API) requested")
        self._wv_visible = False
        self._wv_call('hide')
