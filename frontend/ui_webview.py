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
        """Called from JS when user interacts with a widget."""
        for cb in self._handlers.get(wid, {}).get(event_name, []):
            try:
                cb(event_data)
            except Exception:
                import traceback
                traceback.print_exc()

# Singleton API instance — shared across all widgets in a window
_api = _JsonApi()

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
    if platform.system() == 'Windows':
        # Named explicitly so a missing WebView2 runtime fails loudly instead
        # of silently dropping to mshtml, which has no CSS Grid.
        return 'edgechromium'
    if platform.system() != 'Linux':
        return None                     # macOS: pywebview uses Cocoa
    for module, engine in (('gi', 'gtk'), ('qtpy', 'qt')):
        try:
            if importlib.util.find_spec(module) is not None:
                log.info("no engine specified; defaulting to {} ({} is "
                         "importable)".format(engine, module))
                return engine
        except (ImportError, ValueError):
            continue
    # Neither host present. ui_backend.webview_problem() should already have
    # refused the backend before we got here; returning None lets pywebview
    # produce its own error rather than us inventing one.
    log.warning("no webview host toolkit found (neither gi nor qtpy); "
                "pywebview will fail to start")
    return None


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
    substitute = _default_engine()
    if substitute and substitute != requested:
        log.warning("{}; using {} instead".format(problem, substitute))
        return substitute
    log.warning("{}; no alternative engine is available either"
                "".format(problem))
    return None
    if name not in ENGINES:
        log.warning("Unknown webview engine {!r}; letting pywebview choose. "
                    "Known: {}".format(name, ', '.join(ENGINES)))
        return None
    return name


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
            'b.style.cssText="position:fixed;top:0;right:0;z-index:99999;'
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
        # The message used to say "destroying crashes QtWebEngine", which the
        # docstring above RETRACTED on 2026-09-08 — destroying is fine; being
        # garbage-collected at the wrong moment is what crashes. Left as it
        # was, the log went on asserting the retracted cause to every future
        # reader, in the one place a person looks first.
        log.info("{} hidden rather than destroyed: reused, not rebuilt, and "
                 "freeing a pywebview window at the wrong moment is what "
                 "crashes Qt (see _close_native_window)".format(label))
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
    """Arguments for webview.start().

    `debug=True` was unconditional, which opens the remote-debugging server
    and devtools on a FIELD machine — visible in the run log as
    "Remote debugging server started successfully". Gated on the app's own
    testing flag now.

    AND OFF ON QT ENTIRELY, because `debug=True` is what kills it. The
    faulthandler dump caught the main thread mid-slot (2026-09-11):

        Garbage-collecting
        qt.py:639 in resizeEvent
        qt.py:208 in show_inspector          <-- only reached when debug=True
        qt.py:737 in on_load_finished

    `show_inspector` opens the Web Inspector as each page finishes loading,
    its resize runs a Python GC inside a Qt `resizeEvent`, and the collection
    frees something Qt is still using. That is the SAME fault
    `_close_native_window` documents from 2026-09-07 — "a pywebview window
    wrapper being GARBAGE COLLECTED inside a loadFinished slot, which is a
    reference-keeping problem" — now located precisely: it is in the
    inspector path, so it only happens with devtools on.

    Which also explains the shape of the evidence. Qt "worked earlier the
    same day" because `--user` (no dev settings, no devtools) was in play, and
    every crash came from a dev-settings run. Kent had four `base.html` pages
    listed in the inspector: one live inspector per window, each one another
    chance to hit this on load.

    `--webview-devtools` forces them back on for re-testing, the same way
    `--webview-hidden` does for created-hidden."""
    testing = bool(getattr(program, 'testing', False))
    engine = _engine()
    debug = testing
    if debug and engine == 'qt' and not _switch('--webview-devtools'):
        debug = False
        log.info("devtools OFF for Qt: show_inspector garbage-collects inside "
                 "resizeEvent and segfaults (see _start_kwargs). Use "
                 "--webview-devtools to force them on, or --engine=gtk.")
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
    or if the specific window hasn't finished loading."""
    if not window:
        return None
    if not _started.is_set():
        with _js_queue_lock:
            _js_queue.append((window, code))
        return None
    # Check per-window loaded state
    owner = _get_window_owner(window)
    if owner and hasattr(owner, '_wv_loaded') and not owner._wv_loaded.is_set():
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
    """Execute all queued JS commands. Called once after root webview loads."""
    with _js_queue_lock:
        queue = list(_js_queue)
        _js_queue.clear()
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
            self._grid_opts['padx'] = kwargs.pop('padx', 0)
            self._grid_opts['pady'] = kwargs.pop('pady', 0)
            self._grid_opts['ipadx'] = kwargs.pop('ipadx', 0)
            self._grid_opts['ipady'] = kwargs.pop('ipady', 0)
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

        # Do initial grid (mirrors Gridded.dogrid)
        if self._has_grid:
            self._dogrid()

        # Set up DnD bindings after widget exists in JS
        if self.draggable:
            self.draggable_bindings()
        if self.draggable or self.droppable:
            self.dnd_bindings()

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
        _js(wv, f'createWidget({spec})')

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
    def grid(self, **kwargs):
        if kwargs:
            self._grid_opts.update(kwargs)
            self._has_grid = True
        wv = getattr(self, '_wv_window', None)
        opts = json.dumps(self._grid_opts)
        _js(wv, f'gridWidget({self._wid}, {opts})')
        self._grid_visible = True

    def grid_remove(self):
        wv = getattr(self, '_wv_window', None)
        _js(wv, f'gridRemove({self._wid})')
        self._grid_visible = False

    def grid_info(self):
        if self._has_grid:
            return dict(self._grid_opts)
        return {}

    def grid_size(self):
        # Return (columns, rows) based on children
        max_col = max_row = 0
        for c in self._children:
            if c._has_grid:
                max_row = max(max_row, c._grid_opts.get('row', 0) + 1)
                max_col = max(max_col, c._grid_opts.get('column', 0) + 1)
        return (max_col, max_row)

    def grid_rowconfigure(self, index, **kwargs):
        pass  # CSS Grid handles this automatically

    def grid_columnconfigure(self, index, **kwargs):
        pass

    # ── Configure ─────────────────────────────────────────────────────
    def configure(self, **kwargs):
        self._config.update(kwargs)
        wv = getattr(self, '_wv_window', None)
        for k, v in kwargs.items():
            if isinstance(v, (str, int, float, bool)):
                _js(wv, f'updateProp({self._wid}, {json.dumps(k)}, {json.dumps(v)})')

    def config(self, **kwargs):
        return self.configure(**kwargs)

    def __setitem__(self, key, value):
        self.configure(**{key: value})

    def __getitem__(self, key):
        return self._config.get(key, self._props.get(key, ''))

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

    def wait_window(self, widget=None):
        """Block until *widget* is destroyed — or self, if none is given.

        ON THE BASE CLASS because tkinter puts it on Misc, so ANY widget has
        it. It was implemented only on Toplevel, and `ui_shell.py:2485` does
        `buttonFrame1.wait_window(window)` on a ScrollingButtonFrame — one of
        the canary-idiom sites — which raised AttributeError mid-settings.

        The argument matters: ~30 sites pass a canary WIDGET rather than a
        window, because that widget's destruction is the signal. Returns at
        once if the target is already gone, which is the other half of the
        deadlock."""
        target = widget if widget is not None else self
        wid = getattr(target, '_wid', None)
        if wid is None:
            log.info("wait_window given {!r}, which has no widget id; not "
                     "waiting".format(type(target).__name__))
            return
        if not getattr(target, '_exists', True):
            return
        log.info("widget {}: waiting on widget {}".format(self._wid, wid))
        _waiter_for(wid).wait()
        log.info("widget {}: wait on widget {} released".format(self._wid, wid))

    def winfo_exists(self):
        return self._exists

    def winfo_children(self):
        return list(self._children)

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
        wv = getattr(self, '_wv_window', None)
        _js(wv, f'_widgets.get({self._wid})?.focus()')

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
        self.initial_widget = False
        self.dnd_focus_off()

    def _on_dnd_commit(self, data):
        """Called on the DROP TARGET when a draggable is dropped on it."""
        source_wid = data.get('source_wid')
        # Find the source widget by wid
        source = self._find_widget_by_wid(source_wid)
        if source:
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
        self.program.theme = self
        noimagescaling = kwargs.get('noimagescaling', False)

        # Scale — use devicePixelRatio later; for now default to 1.0
        self.scale = getattr(program, 'scale', None) or 1.0
        scale = self.scale

        # Pick theme
        if isinstance(getattr(program, 'theme_name', None), str):
            self.name = program.theme_name
        else:
            self.name = 'greygreen'
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

    def compile(self):
        """Convert current image to a base64 data URI string."""
        img = self.scaled_img if self.scaled_img else self.base_img
        if not img:
            self.scaled = None
            return
        buf = io.BytesIO()
        fmt = 'PNG'
        if self.filename and self.filename.lower().endswith('.jpg'):
            fmt = 'JPEG'
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
        kwargs.pop('border', None)
        kwargs.pop('highlightbackground', None)
        kwargs.pop('highlightthickness', None)
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


def _image_src(value, parent=None):
    """A data: URI for whatever was passed as `image=`, or None.

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
    log.info("No data URI for image {!r} (filename={!r}) — it produced no "
             "output; see the theme-image warning at startup"
             "".format(type(value).__name__, getattr(value, 'filename', None)))
    return None


class Label(_WebviewWidget):
    def __init__(self, parent, *args, **kwargs):
        # Handle font as a key name
        font = kwargs.pop('font', 'default')
        kwargs.pop('anchor', None)
        kwargs.pop('norender', None)
        kwargs.pop('image_pixels', None)
        kwargs.pop('image_scaleto', None)
        image = _image_src(kwargs.pop('image', None), parent)
        compound = kwargs.pop('compound', None)
        if image:
            kwargs['image'] = image
            kwargs['compound'] = compound or 'top'
        textvariable = kwargs.pop('textvariable', None)
        # KEEP the caller's measured wrap width instead of discarding it.
        # `wraplength` is a PIXEL figure the caller worked out for the box
        # this label sits in, and it is already inherited down the widget
        # tree here (see `inherit`, :614) — popping it threw away the one
        # number that knows how much room there is. `wrap()` then had nothing
        # to act on, which is why it was a no-op with a comment claiming CSS
        # handled it.
        self._asked_wraplength = kwargs.pop('wraplength', None)
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
        kwargs.pop('anchor', None)
        image = _image_src(kwargs.pop('image', None), parent)
        compound = kwargs.pop('compound', None)
        if image:
            kwargs['image'] = image
            kwargs['compound'] = compound or 'top'
        kwargs.pop('relief', None)
        kwargs.pop('state', None)
        kwargs.pop('norender', None)
        kwargs.pop('textvariable', None)
        kwargs.pop('wraplength', None)
        kwargs.pop('image_pixels', None)
        kwargs.pop('image_scaleto', None)
        # Remove button-grid kwargs (brow, bcolumn, etc.)
        for k in list(kwargs):
            if k.startswith('b') and k[1:] in self._gridkwargs:
                kwargs.pop(k)
        kwargs['font'] = font
        if 'text' in kwargs:
            kwargs['text'] = nfc(kwargs['text'])
        super().__init__(parent, widget_type='button', **kwargs)

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
        _api.register(self._wid, 'command', self._final_cmd)


class EntryField(_WebviewWidget):
    def __init__(self, parent, *args, **kwargs):
        kwargs.pop('render', None)
        kwargs.pop('font', None)
        self.textvariable = kwargs.pop('textvariable', StringVar())
        kwargs.pop('text', None)
        super().__init__(parent, widget_type='entry', **kwargs)
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
        kwargs.pop('orient', None)
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
    def __init__(self, parent, *args, **kwargs):
        kwargs.pop('font', None)
        super().__init__(parent, widget_type='label', **kwargs)


class CheckButton(_WebviewWidget):
    def __init__(self, parent, *args, **kwargs):
        font = kwargs.pop('font', 'default')
        self._variable = kwargs.pop('variable', BooleanVar())
        kwargs.pop('image', None)
        kwargs.pop('selectimage', None)
        kwargs.pop('large_images', None)
        kwargs.pop('indicatoron', None)
        self._command = kwargs.pop('command', None)
        kwargs.pop('norender', None)
        kwargs.pop('compound', None)
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
        kwargs.pop('selectmode', None)
        kwargs.pop('listvariable', None)
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
        """(value, display text) for one option, or None to skip it."""
        if self._raw_command:
            # Legacy mode: plain strings, fed through untouched, and the
            # command wants the raw event rather than a choice.
            return option, _text_of(option)
        ck = ButtonFrame.regularize_choice(option)
        if not ck:
            return None
        if ck.get('image'):
            log.info("ListBox dropping image for {!r}".format(ck.get('code')))
        return ck.get('code'), _text_of(ck.get('name', ck.get('code', '')))

    def _on_select(self, data):
        idx = data.get('index', 0)
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
        if last is None:
            if 0 <= first < len(self._items):
                return self._items[first]
            return ''
        return self._items[first:last + 1]

    def insert(self, index, *elements):
        for elem in elements:
            if index == END or index == 'end':
                self._items.append(elem)
            else:
                self._items.insert(index, elem)
                index += 1
        self._push_items()

    def delete(self, first, last=None):
        if last is None:
            last = first
        if first == 0 and (last == END or last == 'end'):
            self._items.clear()
        else:
            del self._items[first:last + 1]
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
        kwargs['width'] = kwargs.pop('width', 20)
        kwargs['font'] = font
        super().__init__(parent, widget_type='combobox', **kwargs)
        self._value = ''
        self._options = list(optionlist)
        _api.register(self._wid, 'select',
                      lambda data: self._on_select(data.get('value', '')))
        if self._options:
            wv = getattr(self, '_wv_window', None)
            _js(wv, f'updateProp({self._wid}, "items", {json.dumps(self._options)})')

    def _on_select(self, value):
        self._value = value
        if self._command:
            self._command(None)

    def get(self):
        return self._value

    def set(self, value):
        self._value = value
        wv = getattr(self, '_wv_window', None)
        _js(wv, f'updateProp({self._wid}, "value", {json.dumps(value)})')


class SearchableComboBox(Combobox):
    pass


class Menu:
    def __init__(self, parent, **kwargs):
        self.parent = parent
        self._items = []
        self._exists = True
        self._wid = _next_wid()
        kwargs.pop('tearoff', None)
        kwargs.pop('font', None)
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
        self._items.insert(index, ('cascade', label, menu))

    def tk_popup(self, x, y):
        """Show the menu at position (x, y) as a positioned div."""
        wv = getattr(self, '_wv_window', None)
        if not wv:
            return
        # Build menu items as HTML
        items_html = []
        for i, (kind, label, _) in enumerate(self._items):
            if kind == 'command':
                items_html.append(
                    f'<div class="wv-menu-item" data-idx="{i}" '
                    f'onclick="pywebview.api.on_event({self._wid},\'menuclick\','
                    f'{{index:{i}}})">{label}</div>')
        html = ''.join(items_html)
        # Register handler
        def on_menuclick(data):
            idx = data.get('index', 0)
            if 0 <= idx < len(self._items):
                _, _, cmd = self._items[idx]
                if cmd:
                    cmd()
            # Remove menu after click
            _js(wv, f'destroyWidget({self._wid})')
        _api.unregister(self._wid)
        _api.register(self._wid, 'menuclick', on_menuclick)
        # Create and position via JS
        js = (f'(function(){{'
              f'let el=document.createElement("div");'
              f'el.className="wv-menu";'
              f'el.style.left="{x}px";el.style.top="{y}px";'
              f'el.dataset.wid={self._wid};'
              f'el.innerHTML={json.dumps(html)};'
              f'_widgets.set({self._wid},el);'
              f'document.body.appendChild(el);'
              f'document.addEventListener("click",function _dismiss(e){{'
              f'if(!el.contains(e.target)){{el.remove();_widgets.delete({self._wid});'
              f'document.removeEventListener("click",_dismiss);}}}}'
              f',{{capture:true,once:false}});'
              f'}})()')
        _js(wv, js)

    def destroy(self):
        self._exists = False
        wv = getattr(self, '_wv_window', None)
        _js(wv, f'destroyWidget({self._wid})')


class Scrollbar(_WebviewWidget):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, widget_type='frame', **kwargs)


class ScrollingFrame(Frame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.content = Frame(self)  # Inner frame for children

    def windowsize(self, event=None):
        pass
    def reflow(self):
        pass
    def tobottom(self):
        pass
    def totop(self):
        pass


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
        # Pop remaining button-only kwargs that shouldn't go to Frame
        for k in ('choice', 'text', 'image', 'compound', 'norender',
                  'wraplength', 'image_pixels', 'image_scaleto',
                  'anchor', 'relief', 'state', 'textvariable'):
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
        for k in ('choice', 'text', 'image', 'compound', 'norender',
                  'wraplength', 'image_pixels', 'image_scaleto',
                  'anchor', 'relief', 'state', 'textvariable'):
            kwargs.pop(k, None)
        btn_grid = {}
        for k in list(kwargs):
            if k.startswith('b') and k[1:] in self._gridkwargs:
                btn_grid[k[1:]] = kwargs.pop(k)
        super().__init__(parent, *args, **kwargs)
        bf_kw = {'optionlist': optionlist, 'command': command}
        if window is not None:
            bf_kw['window'] = window
        if font:
            bf_kw['font'] = font
        bf_kw.update({f'b{k}': v for k, v in btn_grid.items()})
        self.bf = ButtonFrame(self.content, **bf_kw)
        self.buttons = self.bf.buttons


class ScrollingListBox(ScrollingButtonFrame):
    """Stub for the webview backend. Mirrors the tkinter ScrollingListBox API
    by delegating to ScrollingButtonFrame for now."""
    pass


class RadioButtonFrame(Frame):
    def __init__(self, parent, *args, **kwargs):
        kwargs.pop('optionlist', None)
        kwargs.pop('horizontal', None)
        kwargs.pop('variable', None)
        super().__init__(parent, *args, **kwargs)


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

        # Create a new pywebview window
        if webview:
            html_path = os.path.join(_HTML_DIR, 'base.html')
            self._wv_window = webview.create_window(
                'A-Z+T',
                url=html_path if os.path.exists(html_path) else None,
                html='<div id="root"></div>' if not os.path.exists(html_path) else None,
                js_api=_api,
                width=800, height=600,
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
            )
            if self._wv_window:
                # The url is logged because a window pointed at nothing loads
                # pywebview's SERVER ROOT instead, which its own asset route
                # cannot serve: `GET / -> 500`, and the window shows nothing.
                log.info("window {}: created {}{}, url={}".format(
                    self._wid,
                    'HIDDEN' if create_hidden else 'visible',
                    ' (asked withdrawn)' if withdrawn else '',
                    html_path if os.path.exists(html_path) else '(NONE — will '
                    'load the server root and fail)'))
                _all_wv_windows.append(self._wv_window)
                _register_window_owner(self._wv_window, self)
                if _started.is_set():
                    # Window created after webview.start() — poll for readiness
                    # (events.loaded has a race condition: may fire before we attach)
                    t = threading.Thread(target=self._poll_until_loaded, daemon=True)
                    t.start()
                else:
                    # Window created before start — Root's on_loaded handles it
                    self._wv_loaded.set()

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
        self._wv_loaded.set()
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
        # Flush per-window JS queue
        _eval_batched(self._wv_window, self._wv_js_queue)
        self._wv_js_queue.clear()
        # Flush deferred wv calls (title, hide/show, etc.)
        self._flush_wv_calls()
        # Widgets are in the page now, so its content has a size — fit to it.
        self.fit_to_content()

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
            log.info("window {}: fullscreen, so not fitting to content"
                     "".format(self._wid))
            return
        try:
            # MEASURE THE CONTENT, NOT THE CONTAINER. scrollWidth/Height of a
            # box that fills the window reports the WINDOW's size, so it can
            # only ever say "grow" — which is why a window created at 800x600
            # with 490px of content kept the surplus as dead theme-coloured
            # space. The union of the children's bounding boxes is the real
            # extent, and it can be smaller than the window.
            measured = wv.evaluate_js(
                '(function(){'
                'var r=document.getElementById("root")||document.body;'
                'var kids=r.querySelectorAll("*");'
                'var base=r.getBoundingClientRect();'
                'var w=0,h=0,i,b;'
                'for(i=0;i<kids.length;i++){'
                ' if(kids[i].offsetParent===null&&kids[i].tagName!=="IMG")'
                '  continue;'
                ' b=kids[i].getBoundingClientRect();'
                ' if(!b.width&&!b.height) continue;'
                ' w=Math.max(w,b.right-base.left);'
                ' h=Math.max(h,b.bottom-base.top);}'
                'return [Math.ceil(w),Math.ceil(h),'
                'screen.availWidth,screen.availHeight,'
                'window.innerWidth,window.innerHeight];})()')
        except Exception as e:
            log.debug("window {}: could not measure content: {}"
                      "".format(self._wid, e))
            return
        try:
            cw, ch, availw, availh, innerw, innerh = [int(n) for n in measured]
        except (TypeError, ValueError):
            log.debug("window {}: content measurement unusable: {!r}"
                      "".format(self._wid, measured))
            return
        if cw <= 0 or ch <= 0:
            log.debug("window {}: no measurable content; leaving size alone"
                      "".format(self._wid))
            return
        # SHRINKS AS WELL AS GROWS, which is what tkinter does and what the
        # surplus space complaint was about. Clamped below by _FIT_MIN so a
        # sparse page cannot collapse to a sliver, and above by the display.
        want_w = min(max(cw + self._FIT_PAD, self._FIT_MIN[0]), availw)
        want_h = min(max(ch + self._FIT_PAD, self._FIT_MIN[1]), availh)
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
            self._centre_on_screen(innerw, innerh, availw, availh)
            return
        try:
            wv.resize(want_w, want_h)
            log.info("window {}: fitted to content {}x{} (was {}x{}, "
                     "screen {}x{})".format(self._wid, want_w, want_h,
                                            innerw, innerh, availw, availh))
        except Exception as e:
            log.debug("window {}: resize failed: {}".format(self._wid, e))
        self._centre_on_screen(want_w, want_h, availw, availh)

    def _centre_on_screen(self, w, h, availw, availh):
        """Put the window somewhere deliberate, not wherever the WM drops it.

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

        CENTRED, not cascaded, and centred on the SCREEN rather than on the
        parent. Two reasons: a dialog centred on a parent that is itself
        off-centre compounds the error, and `screen.avail*` is a number this
        method already has in hand, whereas the parent's position is one more
        thing to ask the WM for and get wrong. Centring also matches what the
        fit is for — a window the size of its content, where its content is.

        This does NOT fix the sizing item's real complaint (a window that
        never asks to be fitted at all); it makes the windows that DO fit land
        somewhere a person would put them. See
        agenda/webview_window_sizing.md.
        """
        wv = getattr(self, '_wv_window', None)
        if not wv:
            return
        if not hasattr(wv, 'move'):
            log.info("window {}: this pywebview has no move(); leaving "
                     "placement to the window manager".format(self._wid))
            return
        x = max(0, int((availw - w) / 2))
        y = max(0, int((availh - h) / 2))
        try:
            wv.move(x, y)
            # LOGGED AT INFO, not debug, and on SUCCESS as well as failure.
            # Kent, 2026-09-11: "they're still both uncentered" — and with
            # only a debug line on the failure path there was no way to tell
            # from a run whether the move was attempted, attempted with the
            # wrong numbers, or accepted and then undone. Three candidates
            # and the log distinguished none of them, which is the same
            # mistake as measuring a rate without recording the level.
            log.info("window {}: centred at {},{} for {}x{} on {}x{}"
                     "".format(self._wid, x, y, w, h, availw, availh))
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
        self._wv_call('hide')

    def deiconify(self):
        log.info("window {}: DEICONIFY (show) requested".format(self._wid))
        self._wv_call('show')

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
        self._wv_call('show')

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
        if bool(getattr(self, '_is_fullscreen', False)) == bool(want):
            return
        if want and _switch('--no-kiosk'):
            log.info("window {}: fullscreen requested, NOT applied "
                     "(--no-kiosk is in force)".format(self._wid))
            return
        self._is_fullscreen = bool(want)
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
        self.bind('<Double-Button-1>', self.releasefullscreen)

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
        pass

    # wait_window lives on _WebviewWidget — tkinter puts it on Misc, so every
    # widget has it, and call sites use it from both windows and frames.

    def iconphoto(self, default, *args):
        pass

    def on_quit(self, to_root=False, event=None):
        self.exitFlag.true()
        if to_root and self.parent:
            self.parent.on_quit(to_root=True)
        self._exists = False
        if hasattr(self, '_wait_event'):
            self._wait_event.set()
        # Quitting must free waiters too, or closing a window leaves whoever
        # was waiting on it blocked — the same deadlock by a different door.
        _release_waiters(self._wid, 'quit')
        _close_native_window(self, 'Toplevel {}'.format(self._wid))

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
        self.showafterwait = bool(self.winfo_viewable()) or bool(thenshow)
        if self.showafterwait:
            self.withdraw()
        ww.activate(parent=self, msg=msg, cancellable=cancellable,
                    reveal=self.showafterwait)

    def waitdone(self):
        ww = self._waitwindow(create=False)
        if ww is None or not ww.active:
            return
        parent = ww.reveal_parent
        if ww.do_reveal and parent is not None \
                and getattr(parent, '_exists', False) \
                and not parent.exitFlag.istrue():
            try:
                parent.deiconify()
            except Exception:
                pass
        ww.deactivate()

    def waitprogress(self, x):
        ww = self._waitwindow(create=False)
        if ww is None:
            return
        try:
            ww.progress(x, r=4)
        except Exception:
            pass

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
        if exit:
            self.exitButton = Button(self.outsideframe, width=10,
                                     text=_("Exit"), cmd=self.on_quit,
                                     font='small', column=2, row=2)

    def progress(self, value, parent=None, **kwargs):
        try:
            self.progressbar.grid() #re-show if a no-progress wait grid_remove()'d it
            self.progressbar.current(value)
        except AttributeError:
            if not parent:
                parent = self.outsideframe
            self.progressbar = Progressbar(parent, **kwargs)
            self.progressbar.current(value)

    def resetframe(self):
        if self.parent and self.parent.exitFlag.istrue():
            return
        if self._exists:
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
        super().__init__(parent, *args, **kwargs)
        self.active = False
        self.reveal_parent = None
        self.do_reveal = False
        self.cancelbutton = None
        self.paused = False
        self.withdraw()
        self.title(_("Please Wait!"))
        self.l = Label(self.outsideframe, text=_("Please Wait..."),
                       font='title', anchor='c', row=0, column=0, sticky='we')
        self.l1 = Label(self.outsideframe, text='',
                        font='default', anchor='c', row=1, column=0, sticky='we')

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

    def activate(self, parent, msg=None, cancellable=False, reveal=True):
        self.reveal_parent = parent
        self.do_reveal = reveal
        if msg:
            self.msg(msg)
        if getattr(self, 'progressbar', None) is not None:
            self.progressbar.grid_remove() #progress() re-grids on demand
        if cancellable:
            self.make_cancellable()
        else:
            self.hide_cancel()
        self.paused = False
        self.active = True
        self.deiconify()

    def deactivate(self):
        self.active = False
        self.reveal_parent = None
        self.do_reveal = False
        self.withdraw()


# ── Root ──────────────────────────────────────────────────────────────

def wrap_to_container(container, cols=1, reserve=0, minimum=60, maxdepth=2):
    """No-op mirror of ui_tkinter.wrap_to_container, so consumers can call
    `ui.wrap_to_container(...)` regardless of backend (the chooser and the
    verify page both do; without this they'd AttributeError here).

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

        noimagescaling = kwargs.pop('noimagescaling', False)

        # Theme
        if hasattr(program, 'theme') and isinstance(program.theme, Theme):
            self.theme = program.theme
        else:
            self.theme = Theme(program, noimagescaling=noimagescaling)

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
        self.bind('<Double-Button-1>', self.releasefullscreen)

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
                _started.set()
                self._wv_loaded.set()
                _log_engine_in_use(self._wv_window)
                self._push_theme()
                _badge(self._wv_window, 'ROOT (no task widgets live here)')
                self._flush_wv_calls()
                # Flush deferred calls on all child Toplevels
                for child in self._children:
                    if hasattr(child, '_flush_wv_calls'):
                        child._flush_wv_calls()
                _flush_js_queue()
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
            # desktop matches against azt's .desktop file for the dock icon.
            _app_identity(self.program)
            kwargs = _start_kwargs(self.program)
            icon = _icon_path(self.program)
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
        pass

    def iconphoto(self, default, *args):
        pass

    def on_quit(self, to_root=False, event=None):
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
        self.showafterwait = self.winfo_viewable() | thenshow
        if self.showafterwait:
            self.withdraw()
        ww.activate(parent=self, msg=msg, cancellable=cancellable,
                    reveal=self.showafterwait)

    def waitdone(self):
        ww = self._waitwindow(create=False)
        if ww is None or not ww.active:
            return
        parent = ww.reveal_parent
        if ww.do_reveal and parent is not None \
                and getattr(parent, '_exists', False) \
                and not parent.exitFlag.istrue():
            try:
                parent.deiconify()
            except Exception:
                pass
        ww.deactivate()

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
        for progress in generator or ():
            if self.iswaiting():
                self.waitprogress(progress)
        self.waitdone()
        if on_done:
            on_done()

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
