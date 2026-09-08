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
import io
import json
import os
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


def _engine():
    """The pywebview backend to ask for, or None to let it choose."""
    for arg in sys.argv:
        if arg.startswith('--engine='):
            return arg.split('=', 1)[1].strip().lower() or None
    name = (os.environ.get('AZT_WEBVIEW_ENGINE')
            or os.environ.get('PYWEBVIEW_GUI') or '').strip().lower()
    if not name:
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


def _badge(window, label):
    """Stamp a corner badge naming the window, so a page on screen can be
    identified.

    Every window loads the SAME base.html and, until a task builds into it,
    looks identical — an empty themed box. So "the app shows a blank green
    window" could not be told from "the app shows the WRONG blank green
    window", and it turned out to matter: the visible window was the root
    (empty by design; task widgets go into Toplevels) while the window that
    had 408 widget calls flushed into it was somewhere unseen. Debug aid, and
    it should go once windows reliably show what they contain."""
    if not window:
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

    WHY, and it took a native backtrace to see: destroying a window under the
    Qt backend segfaults. Qt tears the QMainWindow down through a posted
    deferred-delete, and on the way down QWidget::~QWidget closes the window,
    which hides its children, which fires hideEvent on the QWebEngineView,
    which touches a QWebEnginePage that is already gone:

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
        log.info("{} hidden rather than destroyed (see _close_native_window: "
                 "destroying crashes QtWebEngine)".format(label))
    except Exception as e:
        log.debug("could not hide {}: {}".format(label, e))


def _start_kwargs(program=None):
    """Arguments for webview.start().

    `debug=True` was unconditional, which opens the remote-debugging server
    and devtools on a FIELD machine — visible in the run log as
    "Remote debugging server started successfully". Gated on the app's own
    testing flag now."""
    kwargs = {'debug': bool(getattr(program, 'testing', False))}
    engine = _engine()
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

    def cget(self, key):
        """tkinter's option reader. Missing entirely, which is what
        "DIAG-chooser-xpad failed: 'Button' object has no attribute 'cget'"
        was — the chooser's own wrap/xpad diagnostic asking a button for its
        configured values. Reads back what was set, so a caller sees what it
        put in rather than a guess at what the browser computed."""
        if key in self._config:
            return self._config[key]
        return self._props.get(key, '')

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
    # Same imagelist as ui_tkinter.Theme — import at runtime to avoid
    # pulling in tkinter at module level.
    imagelist = [
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

    themes = {
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
            self.name = 'greygreen'
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
        kwargs.pop('wraplength', None)
        kwargs['font'] = font
        # A Variable in either slot resolves to its VALUE, not its repr.
        if 'text' in kwargs:
            kwargs['text'] = _text_of(kwargs['text'])
        elif textvariable is not None:
            kwargs['text'] = _text_of(textvariable)
        super().__init__(parent, widget_type='label', **kwargs)
        self._textvariable = None

    def wrap(self):
        pass  # Handled by CSS


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

    def _build_command(self):
        cmd = self.command
        if cmd and self.choice is not None and self.window is not None:
            self._final_cmd = lambda data, x=self.choice, w=self.window: cmd(x, window=w)
        elif cmd and self.choice is not None:
            self._final_cmd = lambda data, x=self.choice: cmd(x)
        elif cmd:
            self._final_cmd = lambda data: cmd()
        else:
            self._final_cmd = _donothing
        _api.register(self._wid, 'command', self._final_cmd)


class EntryField(_WebviewWidget):
    def __init__(self, parent, *args, **kwargs):
        kwargs.pop('render', None)
        kwargs.pop('font', None)
        self.textvariable = kwargs.pop('textvariable', StringVar())
        kwargs.pop('text', None)
        super().__init__(parent, widget_type='entry', **kwargs)
        # Sync entry → variable
        _api.register(self._wid, 'input',
                      lambda data: self.textvariable.set(data.get('value', '')))

    def get(self):
        return self.textvariable.get()


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
    def __init__(self, parent, *args, **kwargs):
        font = kwargs.pop('font', 'default')
        optionlist = kwargs.pop('optionlist', [])
        self._command = kwargs.pop('command', None)
        kwargs['height'] = kwargs.pop('height', 10)
        kwargs['width'] = kwargs.pop('width', 20)
        kwargs.pop('selectmode', None)
        kwargs['font'] = font
        super().__init__(parent, widget_type='listbox', **kwargs)
        self._items = []
        self._selection = ()
        _api.register(self._wid, 'select',
                      lambda data: self._on_select(data))
        if optionlist:
            for item in optionlist:
                self.insert(END, item)

    def _on_select(self, data):
        idx = data.get('index', 0)
        self._selection = (idx,)
        if self._command:
            self._command(None)

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
        wv = getattr(self, '_wv_window', None)
        _js(wv, f'updateProp({self._wid}, "items", {json.dumps(self._items)})')


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
    def __init__(self, parent, *args, **kwargs):
        self.parent = parent

    def menuinit(self):
        pass
    def updatebindings(self):
        pass
    def undo_popup(self, event=None):
        pass


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
        create_hidden = bool(withdrawn
                             and os.environ.get('AZT_WEBVIEW_HIDDEN'))

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
                # NEVER CREATE HIDDEN — measured 2026-09-07, and this was my
                # mistake. `hidden=True` looked like the honest equivalent of
                # Tk's withdrawn state and it removed the startup flash, but
                # tests/manual/webview_multiwindow/hide_show.py --start-hidden
                # shows a window created hidden NEVER APPEARS: show() does not
                # map it, then or later. Every task window is built withdrawn
                # (tasks/chooser.py:527), so this alone hid the entire UI.
                #
                # Opt in with AZT_WEBVIEW_HIDDEN=1 only to re-test it.
                # The flash it was meant to fix is cosmetic and comes back;
                # it needs a different answer (see the item — most likely one
                # window with page-level views instead of many OS windows).
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
        # Push theme
        if hasattr(self, 'theme') and self.theme:
            css_vars = self.theme.css_vars()
            if self._wv_window:
                try:
                    self._wv_window.evaluate_js(f'setThemeVars({json.dumps(css_vars)})')
                except Exception as e:
                    log.debug(f"Theme push failed: {e}")
        _badge(self._wv_window, 'window {}'.format(self._wid))
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
        try:
            measured = wv.evaluate_js(
                '(function(){var r=document.getElementById("root")'
                '||document.body;'
                'return [Math.ceil(r.scrollWidth),Math.ceil(r.scrollHeight),'
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
        want_w = min(max(cw + self._FIT_PAD, innerw, self._FIT_MIN[0]), availw)
        want_h = min(max(ch + self._FIT_PAD, innerh, self._FIT_MIN[1]), availh)
        if want_w <= innerw and want_h <= innerh:
            return
        try:
            wv.resize(want_w, want_h)
            log.info("window {}: fitted to content {}x{} (was {}x{}, "
                     "screen {}x{})".format(self._wid, want_w, want_h,
                                            innerw, innerh, availw, availh))
        except Exception as e:
            log.debug("window {}: resize failed: {}".format(self._wid, e))

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
        log.info("window {}: WITHDRAW (hide) requested".format(self._wid))
        self._wv_call('hide')

    def deiconify(self):
        log.info("window {}: DEICONIFY (show) requested".format(self._wid))
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

        OFF BY DEFAULT UNDER WEBVIEW, opt in with AZT_WEBVIEW_KIOSK=1.
        `TaskDressing.__init__` calls `takekioskscreen()` on EVERY task
        window, and before this method existed `attributes()` was a `pass`,
        so nothing happened. Implementing it made every task window jump to
        fullscreen and undecorated the instant it appeared — a behaviour
        change introduced while chasing a crash, and the wrong thing while
        the question is still "can we see this page at all". A fullscreen
        undecorated window showing a half-built layout is also the state
        that reads as a hung machine.

        Kiosk mode is a real feature and this is not a rejection of it; it
        needs to be turned on deliberately once pages render."""
        if bool(getattr(self, '_is_fullscreen', False)) == bool(want):
            return
        if want and not os.environ.get('AZT_WEBVIEW_KIOSK'):
            log.info("window {}: fullscreen requested, NOT applied "
                     "(set AZT_WEBVIEW_KIOSK=1 to allow it)".format(self._wid))
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
        self._set_fullscreen(False)

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

    def wait_window(self, widget=None):
        """Block until this window is destroyed. Phase 5: threading.Event."""
        self._wait_event = threading.Event()
        self._wait_event.wait()

    def iconphoto(self, default, *args):
        pass

    def on_quit(self, to_root=False, event=None):
        self.exitFlag.true()
        if to_root and self.parent:
            self.parent.on_quit(to_root=True)
        self._exists = False
        if hasattr(self, '_wait_event'):
            self._wait_event.set()
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
        if want and not os.environ.get('AZT_WEBVIEW_KIOSK'):
            log.info("root window: fullscreen requested, NOT applied "
                     "(set AZT_WEBVIEW_KIOSK=1 to allow it)")
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
        self._set_fullscreen(False)

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
            webview.start(**_start_kwargs(self.program))

    def withdraw(self):
        log.info("root window: WITHDRAW (hide) requested")
        self._wv_call('hide')

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
