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
import threading
import unicodedata
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

def _flush_js_queue():
    """Execute all queued JS commands. Called once after root webview loads."""
    with _js_queue_lock:
        queue = list(_js_queue)
        _js_queue.clear()
    for window, code in queue:
        if window and not getattr(window, '_destroyed', False):
            try:
                window.evaluate_js(code)
            except Exception as e:
                log.debug(f"Queued JS failed: {e}")

# ── Base Widget ───────────────────────────────────────────────────────
class _WebviewWidget:
    """Base for all webview widgets. Mirrors the tkinter widget API."""

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
        ('V','A alone clear6.png'), ('CV','ZA alone clear6.png'),
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

        # Fonts — same sizes as ui_tkinter, using _FontInfo instead of tkinter.font.Font
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

        # Images
        self.photo = {}
        self.image_cache = {}
        if not noimagescaling:
            self._load_images(scale)

    def _load_images(self, scale):
        from utilities import file as fileu
        for name, filename in self.imagelist:
            try:
                imgurl = fileu.pathname_from_base_dir(
                    fileu.getdiredurl('../images/', filename))
                self.photo[name] = Image(str(imgurl))
                if scale != 1 and self.photo[name].base_img:
                    self.photo[name].scale(scale, pixels=0)
            except Exception as e:
                log.debug(f"Image {name} not loaded: {e}")

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
        if 'Charis' in fname:
            files = [f'CharisSIL-{fonttypewords}.ttf', f'CharisSIL-{fonttype}.ttf']
        elif 'Andika' in fname:
            files = [f'Andika-{fonttypewords}.ttf', f'Andika-{fonttype}.ttf']
        elif 'Gentium' in fname and 'Book' in fname:
            files = [f'GentiumBookPlus-{fonttypewords}.ttf']
        elif 'Gentium' in fname:
            files = [f'GentiumPlus-{fonttypewords}.ttf']
        else:
            files = []
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


class Label(_WebviewWidget):
    def __init__(self, parent, *args, **kwargs):
        # Handle font as a key name
        font = kwargs.pop('font', 'default')
        kwargs.pop('anchor', None)
        kwargs.pop('norender', None)
        kwargs.pop('image_pixels', None)
        kwargs.pop('image_scaleto', None)
        kwargs.pop('image', None)
        kwargs.pop('compound', None)
        kwargs.pop('textvariable', None)
        kwargs.pop('wraplength', None)
        kwargs['font'] = font
        # Normalize text
        if 'text' in kwargs:
            kwargs['text'] = nfc(kwargs['text'])
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
        kwargs.pop('image', None)
        kwargs.pop('compound', None)
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
    def __init__(self, widget, text=''):
        self.widget = widget
        self.text = text


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
            )
            if self._wv_window:
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
        # Flush per-window JS queue
        for code in self._wv_js_queue:
            if self._wv_window and not getattr(self._wv_window, '_destroyed', False):
                try:
                    self._wv_window.evaluate_js(code)
                except Exception as e:
                    log.debug(f"Per-window queued JS failed: {e}")
        self._wv_js_queue.clear()
        # Flush deferred wv calls (title, hide/show, etc.)
        self._flush_wv_calls()

    def _wv_call(self, method, *args):
        """Call a method on the pywebview window, deferring if not started."""
        if not self._wv_window:
            return
        if not _started.is_set():
            # Defer — will be called from _flush_wv_calls after start
            self._wv_deferred.append((method, args))
            return
        try:
            getattr(self._wv_window, method)(*args)
        except Exception as e:
            log.debug(f"wv_call {method} failed: {e}")

    def _flush_wv_calls(self):
        """Execute deferred pywebview window calls."""
        for method, args in self._wv_deferred:
            try:
                getattr(self._wv_window, method)(*args)
            except Exception as e:
                log.debug(f"Deferred wv_call {method} failed: {e}")
        self._wv_deferred.clear()

    def withdraw(self):
        self._wv_call('hide')

    def deiconify(self):
        self._wv_call('show')

    def title(self, text=None):
        if text:
            self._title_text = text
            self._wv_call('set_title', text)

    def attributes(self, *args):
        pass

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
        if self._wv_window and _started.is_set():
            try:
                self._wv_window.destroy()
            except Exception:
                pass

    def iswaiting(self):
        return hasattr(self, 'ww') and getattr(self.ww, '_exists', False)

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
    def __init__(self, parent, msg=None, cancellable=False, *args, **kwargs):
        kwargs['exit'] = False
        super().__init__(parent, *args, **kwargs)
        self.paused = False
        self.withdraw()
        self.title(_("Please Wait!"))
        self.l = Label(self.outsideframe, text=_("Please Wait..."),
                       font='title', anchor='c', row=0, column=0, sticky='we')
        self.l1 = Label(self.outsideframe, text='',
                        font='default', anchor='c', row=1, column=0, sticky='we')
        if msg:
            self.msg(msg)
        if cancellable:
            self.make_cancellable()
        self.deiconify()

    def close(self):
        self.on_quit()

    def cancel(self):
        self.parent.waitcancel()

    def make_cancellable(self):
        self.cancelbutton = Button(self.outsideframe, text='Cancel',
                                   cmd=self.cancel, row=3, column=0, sticky='e')

    def msg(self, msg):
        log.info(f"Waiting: {msg}")
        self.l1['text'] = msg


# ── Root ──────────────────────────────────────────────────────────────

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
            )
            if self._wv_window:
                _register_window_owner(self._wv_window, self)

        if not hasattr(program, 'tk_root'):
            program.tk_root = self

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
        try:
            getattr(self._wv_window, method)(*args)
        except Exception as e:
            log.debug(f"Root wv_call {method} failed: {e}")

    def _flush_wv_calls(self):
        for method, args in self._wv_deferred:
            try:
                getattr(self._wv_window, method)(*args)
            except Exception as e:
                log.debug(f"Root deferred wv_call {method} failed: {e}")
        self._wv_deferred.clear()

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
            webview.start(debug=True)

    def withdraw(self):
        self._wv_call('hide')

    def deiconify(self):
        self._wv_call('show')

    def title(self, text=None):
        if text:
            self._title_text = text
            self._wv_call('set_title', text)

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

    def iswaiting(self):
        return hasattr(self, 'ww') and getattr(self.ww, '_exists', False)

    def wait(self, msg=None, cancellable=False, thenshow=False):
        if self.iswaiting():
            if msg:
                self.ww.msg(msg)
            return
        self.showafterwait = self.winfo_viewable() | thenshow
        if self.showafterwait:
            self.withdraw()
        self.ww = Wait(self, msg, cancellable=cancellable)

    def waitdone(self):
        try:
            self.ww.close()
        except (AttributeError, Exception):
            pass
        finally:
            if not self.exitFlag.istrue() and self.showafterwait:
                self.deiconify()

    def waitprogress(self, x):
        try:
            self.ww.progress(x, r=4)
        except Exception:
            pass

    def waitcancel(self):
        self.waitcancelled = True

    def waitpause(self):
        if self.iswaiting():
            self.ww.withdraw()

    def waitunpause(self):
        if self.iswaiting():
            self.ww.deiconify()
