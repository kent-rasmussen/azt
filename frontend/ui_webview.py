# coding=UTF-8
"""pywebview UI backend — drop-in replacement for ui_tkinter.

Usage:  from frontend import ui_webview as ui
Then:   ui.Root, ui.Window, ui.Frame, ui.Label, ui.Button, etc.

Phase 2 implements: Root, Window, Frame, Label, Button, ExitFlag,
                    Theme (stub), Image (stub), Renderer (stub),
                    Progressbar, Menu, constants, variables.
Remaining widgets are stubs that log and no-op until Phase 4.
"""
import json
import os
import threading
import unicodedata

from utilities import logsetup
from utilities.i18n import _

log = logsetup.getlog(__name__)
logsetup.setlevel('INFO', log)

try:
    import webview
except ImportError:
    webview = None
    log.error("pywebview not installed — install with: pip install pywebview")

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

# ── JS execution helper ──────────────────────────────────────────────
def _js(window, code):
    """Evaluate JS in the webview window. Thread-safe."""
    if window and not getattr(window, '_destroyed', False):
        try:
            return window.evaluate_js(code)
        except Exception as e:
            log.debug(f"JS eval failed: {e}")
    return None

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

        # Consume remaining grid-adjacent kwargs silently
        kwargs.pop('draggable', None)
        kwargs.pop('droppable', None)

        # Store remaining props
        self._props = kwargs
        self._props.setdefault('text', '')

        # Create in JS
        self._create_in_js()

        # Do initial grid (mirrors Gridded.dogrid)
        if self._has_grid:
            self._dogrid()

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

    # ── Drag and drop stubs ───────────────────────────────────────────
    def draggable_bindings(self):
        pass
    def dnd_bindings(self):
        pass

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


# ── Theme (stub — full implementation Phase 3) ───────────────────────
class Theme:
    imagelist = []  # Will be populated from ui_tkinter.Theme.imagelist

    def __init__(self, program=None, **kwargs):
        self.program = program
        self.name = 'default'
        self.background = '#d9d9d9'
        self.activebackground = '#ececec'
        self.menubackground = '#d9d9d9'
        self.white = '#ffffff'
        self.offwhite = '#f0f0f0'
        self.highlight = '#0078d7'
        self.padx = 5
        self.pady = 5
        self.ipadx = 2
        self.ipady = 2
        self.scale = 1.0
        self.fonts = {k: k for k in ('title', 'big', 'normal', 'read',
                      'readbig', 'small', 'tiny', 'default', 'italic', 'fixed')}
        self.photo = {}  # Phase 3: icon name → Image


# ── Image (stub — Phase 3) ───────────────────────────────────────────
class Image:
    def __init__(self, filename=None):
        self.filename = filename
        self.base_img = None
        self.scaled_img = None
        self.scaled = None
        if filename:
            try:
                import PIL.Image
                with PIL.Image.open(filename) as img:
                    img.load()
                    self.base_img = img.copy()
            except Exception as e:
                log.error(f"Image load failed: {e}")

    def scale(self, program_scale, pixels=None, scaleto=None):
        pass  # Phase 3

    def compile(self):
        pass  # Phase 3: convert to base64 data URI


# ── Renderer (stub — Phase 3) ────────────────────────────────────────
class Renderer:
    def __init__(self, test=False, **kwargs):
        self.isactive = False  # Phase 3
        self.renderings = {}
        self.img = None

    def render(self, **kwargs):
        pass


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
        kwargs.pop('font', None)
        kwargs.pop('variable', None)
        kwargs.pop('image', None)
        kwargs.pop('selectimage', None)
        kwargs.pop('large_images', None)
        kwargs.pop('indicatoron', None)
        kwargs.pop('command', None)
        kwargs.pop('norender', None)
        kwargs.pop('compound', None)
        super().__init__(parent, widget_type='frame', **kwargs)  # stub


class RadioButton(_WebviewWidget):
    def __init__(self, parent, *args, **kwargs):
        kwargs.pop('font', None)
        kwargs.pop('variable', None)
        kwargs.pop('value', None)
        kwargs.pop('indicatoron', None)
        kwargs.pop('command', None)
        super().__init__(parent, widget_type='frame', **kwargs)  # stub


class ListBox(_WebviewWidget):
    def __init__(self, parent, *args, **kwargs):
        kwargs.pop('font', None)
        kwargs.pop('optionlist', None)
        kwargs.pop('command', None)
        kwargs.pop('height', None)
        kwargs.pop('width', None)
        kwargs.pop('selectmode', None)
        super().__init__(parent, widget_type='frame', **kwargs)  # stub

    def curselection(self):
        return ()
    def get(self, first, last=None):
        return ''
    def insert(self, index, *elements):
        pass
    def delete(self, first, last=None):
        pass


class Combobox(_WebviewWidget):
    def __init__(self, parent, *args, **kwargs):
        kwargs.pop('font', None)
        kwargs.pop('optionlist', None)
        kwargs.pop('command', None)
        kwargs.pop('width', None)
        super().__init__(parent, widget_type='frame', **kwargs)  # stub

    def get(self):
        return ''
    def set(self, value):
        pass


class SearchableComboBox(Combobox):
    pass


class Menu:
    def __init__(self, parent, **kwargs):
        self.parent = parent
        self._items = []
        self._exists = True
        kwargs.pop('tearoff', None)
        kwargs.pop('font', None)

    def add_command(self, label, command):
        self._items.append(('command', label, command))

    def add_cascade(self, label, menu):
        self._items.append(('cascade', label, menu))

    def insert_cascade(self, label, menu, index):
        self._items.insert(index, ('cascade', label, menu))

    def tk_popup(self, x, y):
        pass  # Phase 4: show as positioned div

    def destroy(self):
        self._exists = False


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
    def __init__(self, parent, *args, **kwargs):
        # Extract button-specific kwargs
        self.optionlist = kwargs.pop('optionlist', [])
        command = kwargs.pop('command', kwargs.pop('cmd', None))
        kwargs.pop('choice', None)
        kwargs.pop('window', None)
        kwargs.pop('font', None)
        kwargs.pop('text', None)
        kwargs.pop('image', None)
        kwargs.pop('compound', None)
        kwargs.pop('norender', None)
        kwargs.pop('wraplength', None)
        kwargs.pop('image_pixels', None)
        kwargs.pop('image_scaleto', None)
        kwargs.pop('anchor', None)
        kwargs.pop('relief', None)
        kwargs.pop('state', None)
        kwargs.pop('textvariable', None)
        # Remove brow/bcolumn etc
        for k in list(kwargs):
            if k.startswith('b') and k[1:] in self._gridkwargs:
                kwargs.pop(k)
        super().__init__(parent, *args, **kwargs)
        self.buttons = {}


class ScrollingButtonFrame(ScrollingFrame):
    def __init__(self, parent, *args, **kwargs):
        # Same extraction as ButtonFrame
        kwargs.pop('optionlist', None)
        kwargs.pop('command', None)
        kwargs.pop('cmd', None)
        kwargs.pop('choice', None)
        kwargs.pop('window', None)
        kwargs.pop('font', None)
        kwargs.pop('text', None)
        kwargs.pop('image', None)
        kwargs.pop('compound', None)
        kwargs.pop('norender', None)
        kwargs.pop('wraplength', None)
        kwargs.pop('image_pixels', None)
        kwargs.pop('image_scaleto', None)
        kwargs.pop('anchor', None)
        kwargs.pop('relief', None)
        kwargs.pop('state', None)
        kwargs.pop('textvariable', None)
        for k in list(kwargs):
            if k.startswith('b') and k[1:] in self._gridkwargs:
                kwargs.pop(k)
        super().__init__(parent, *args, **kwargs)
        self.bf = ButtonFrame(self.content)


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

    def withdraw(self):
        if self._wv_window:
            try:
                self._wv_window.hide()
            except Exception:
                pass

    def deiconify(self):
        if self._wv_window:
            try:
                self._wv_window.show()
            except Exception:
                pass

    def title(self, text=None):
        if text and self._wv_window:
            self._wv_window.set_title(text)

    def attributes(self, *args):
        pass  # Phase 5: fullscreen etc.

    def protocol(self, name, func):
        if name == 'WM_DELETE_WINDOW' and self._wv_window:
            # pywebview closing event
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
        if self._wv_window:
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
        self._config = {}
        self._props = {}
        self._has_grid = False
        self._grid_opts = {}
        self._gridwait = False
        self._grid_visible = True
        self.waitcancelled = False
        self.showafterwait = True

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

        if not hasattr(program, 'tk_root'):
            program.tk_root = self

    def mainloop(self):
        if webview:
            webview.start(debug=True)

    def withdraw(self):
        if self._wv_window:
            try:
                self._wv_window.hide()
            except Exception:
                pass

    def deiconify(self):
        if self._wv_window:
            try:
                self._wv_window.show()
            except Exception:
                pass

    def title(self, text=None):
        if text and self._wv_window:
            self._wv_window.set_title(text)

    def protocol(self, name, func):
        pass

    def iconphoto(self, default, *args):
        pass

    def on_quit(self, to_root=False, event=None):
        self.exitFlag.true()
        logsetup.shutdown()
        if self._wv_window:
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
