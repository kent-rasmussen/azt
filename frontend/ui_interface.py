# coding=UTF-8
"""Abstract interface for the UI backend.

This module defines the contract that both ui_tkinter and ui_webview must
fulfill. Consumer code (ui_shell, sort_buttons, tasks, etc.) depends only
on the names and signatures declared here.

Not enforced at runtime — serves as documentation and a reference for
implementors.  Import this to type-check or duck-type verify a backend.
"""
from abc import ABC, abstractmethod

# ── Constants ────────────────────────────────────────────────────────────
# Both backends must export these at module level.
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

# ── Variables ────────────────────────────────────────────────────────────
# Both backends must export Variable, StringVar, IntVar, BooleanVar
# with at minimum: get(), set(), trace_add(mode, callback),
#                  trace_remove(mode, cbname)

class VariableInterface(ABC):
    @abstractmethod
    def get(self): ...
    @abstractmethod
    def set(self, value): ...
    @abstractmethod
    def trace_add(self, mode, callback):
        """Register a callback for variable changes. Returns a trace id."""
        ...
    @abstractmethod
    def trace_remove(self, mode, cbname):
        """Remove a previously registered trace."""
        ...

# ── Widget Base ──────────────────────────────────────────────────────────
class WidgetInterface(ABC):
    """Methods every widget must support."""
    # Layout
    @abstractmethod
    def grid(self, **kwargs): ...
    @abstractmethod
    def grid_remove(self): ...
    @abstractmethod
    def grid_info(self): ...
    # Configuration
    @abstractmethod
    def configure(self, **kwargs): ...
    def config(self, **kwargs):
        return self.configure(**kwargs)
    @abstractmethod
    def __setitem__(self, key, value): ...
    @abstractmethod
    def __getitem__(self, key): ...
    @abstractmethod
    def keys(self): ...
    # Lifecycle
    @abstractmethod
    def destroy(self): ...
    @abstractmethod
    def winfo_exists(self): ...
    @abstractmethod
    def winfo_children(self): ...
    # Geometry queries
    @abstractmethod
    def winfo_screenwidth(self): ...
    @abstractmethod
    def winfo_screenheight(self): ...
    @abstractmethod
    def winfo_reqwidth(self): ...
    @abstractmethod
    def winfo_reqheight(self): ...
    @abstractmethod
    def winfo_width(self): ...
    @abstractmethod
    def winfo_height(self): ...
    @abstractmethod
    def winfo_x(self): ...
    @abstractmethod
    def winfo_y(self): ...
    @abstractmethod
    def winfo_rootx(self): ...
    @abstractmethod
    def winfo_rooty(self): ...
    @abstractmethod
    def winfo_viewable(self): ...
    @abstractmethod
    def winfo_toplevel(self): ...
    # Events
    @abstractmethod
    def bind(self, event, handler, add=None): ...
    @abstractmethod
    def unbind(self, event, funcid=None): ...
    @abstractmethod
    def update_idletasks(self): ...
    @abstractmethod
    def update(self): ...
    @abstractmethod
    def after(self, ms, func=None): ...
    @abstractmethod
    def after_cancel(self, id): ...
    # Focus
    @abstractmethod
    def focus_set(self): ...
    @abstractmethod
    def focus_get(self): ...

# ── ExitFlag ─────────────────────────────────────────────────────────────
class ExitFlagInterface(ABC):
    @abstractmethod
    def istrue(self): ...
    @abstractmethod
    def true(self): ...
    @abstractmethod
    def false(self): ...

# ── Theme ────────────────────────────────────────────────────────────────
class ThemeInterface(ABC):
    """Backends must provide a Theme with at least these attributes:
    - name: str
    - background, activebackground, menubackground: str (hex color)
    - white, offwhite, highlight: str
    - fonts: dict[str, font-object]  (keys: title, big, normal, read,
        readbig, small, tiny, default, italic, fixed)
    - photo: dict[str, image-object]  (icon name -> displayable image)
    - padx, pady, ipadx, ipady: int
    - scale: float (DPI scaling factor)
    """
    pass

# ── Image ────────────────────────────────────────────────────────────────
class ImageInterface(ABC):
    @abstractmethod
    def scale(self, program_scale, pixels=None, scaleto=None): ...
    @abstractmethod
    def compile(self): ...
    # Attributes: base_img, scaled_img, scaled (displayable form)

# ── Renderer ─────────────────────────────────────────────────────────────
class RendererInterface(ABC):
    @abstractmethod
    def render(self, text, font, wraplength=None, **kwargs): ...
    # Produces a displayable image from text (for diacritics/special chars)

# ── Root ─────────────────────────────────────────────────────────────────
class RootInterface(WidgetInterface):
    @abstractmethod
    def mainloop(self): ...
    @abstractmethod
    def withdraw(self): ...
    @abstractmethod
    def deiconify(self): ...
    @abstractmethod
    def title(self, text=None): ...
    @abstractmethod
    def protocol(self, name, func): ...
    @abstractmethod
    def iconphoto(self, default, *args): ...
    # Attributes: program, theme, renderer, exitFlag, wraplength, photo

# ── Toplevel / Window ────────────────────────────────────────────────────
class ToplevelInterface(WidgetInterface):
    @abstractmethod
    def withdraw(self): ...
    @abstractmethod
    def deiconify(self): ...
    @abstractmethod
    def title(self, text=None): ...
    @abstractmethod
    def attributes(self, *args): ...
    @abstractmethod
    def protocol(self, name, func): ...
    @abstractmethod
    def wait_window(self, widget=None): ...

class WindowInterface(ToplevelInterface):
    """Window adds: frame, outsideframe, resetable frame, progress,
    backcmd, exit handling, choice."""
    # Attributes: frame, outsideframe, exitFlag, mainwindow, choice
    @abstractmethod
    def on_quit(self, event=None): ...
    @abstractmethod
    def progress(self, **kwargs): ...

# ── Frame ────────────────────────────────────────────────────────────────
class FrameInterface(WidgetInterface):
    @abstractmethod
    def grid_size(self): ...
    @abstractmethod
    def grid_rowconfigure(self, index, **kwargs): ...
    @abstractmethod
    def grid_columnconfigure(self, index, **kwargs): ...

# ── Label ────────────────────────────────────────────────────────────────
class LabelInterface(WidgetInterface):
    """Constructor kwargs: text, textvariable, font, image, compound,
    wraplength, norender, image_pixels, image_scaleto"""
    @abstractmethod
    def wrap(self): ...

# ── Button ───────────────────────────────────────────────────────────────
class ButtonInterface(WidgetInterface):
    """Constructor kwargs: text, font, image, cmd, command, choice, window,
    relief, state, anchor, compound"""
    pass

# ── EntryField ───────────────────────────────────────────────────────────
class EntryFieldInterface(WidgetInterface):
    """Constructor kwargs: text/textvariable, font, width, render"""
    @abstractmethod
    def get(self): ...

# ── Message ──────────────────────────────────────────────────────────────
class MessageInterface(WidgetInterface):
    """Constructor kwargs: text, font, width"""
    pass

# ── CheckButton ──────────────────────────────────────────────────────────
class CheckButtonInterface(WidgetInterface):
    """Constructor kwargs: text, variable, image, selectimage, large_images,
    indicatoron, command"""
    pass

# ── RadioButton ──────────────────────────────────────────────────────────
class RadioButtonInterface(WidgetInterface):
    """Constructor kwargs: text, variable, value, indicatoron, command"""
    pass

# ── ListBox ──────────────────────────────────────────────────────────────
class ListBoxInterface(WidgetInterface):
    """Constructor kwargs: optionlist, command, height, width, font"""
    @abstractmethod
    def curselection(self): ...
    @abstractmethod
    def get(self, first, last=None): ...
    @abstractmethod
    def insert(self, index, *elements): ...
    @abstractmethod
    def delete(self, first, last=None): ...

# ── Combobox ─────────────────────────────────────────────────────────────
class ComboboxInterface(WidgetInterface):
    """Constructor kwargs: optionlist, command, font, width"""
    @abstractmethod
    def get(self): ...
    @abstractmethod
    def set(self, value): ...

# ── Progressbar ──────────────────────────────────────────────────────────
class ProgressbarInterface(WidgetInterface):
    @abstractmethod
    def current(self, value): ...

# ── Menu ─────────────────────────────────────────────────────────────────
class MenuInterface(ABC):
    @abstractmethod
    def add_command(self, label, command): ...
    @abstractmethod
    def add_cascade(self, label, menu): ...
    @abstractmethod
    def insert_cascade(self, label, menu, index): ...
    @abstractmethod
    def tk_popup(self, x, y): ...
    @abstractmethod
    def destroy(self): ...

# ── Scrollbar ────────────────────────────────────────────────────────────
class ScrollbarInterface(WidgetInterface):
    pass

# ── ScrollingFrame ───────────────────────────────────────────────────────
class ScrollingFrameInterface(FrameInterface):
    """Attributes: content (the inner frame to add children to),
    canvas"""
    @abstractmethod
    def windowsize(self, event=None): ...
    @abstractmethod
    def tobottom(self): ...
    @abstractmethod
    def totop(self): ...

# ── ButtonFrame ──────────────────────────────────────────────────────────
class ButtonFrameInterface(FrameInterface):
    """Constructor kwargs: optionlist, plus Button kwargs.
    Attributes: buttons (dict keyed by choice)"""
    pass

# ── ScrollingButtonFrame ─────────────────────────────────────────────────
class ScrollingButtonFrameInterface(ScrollingFrameInterface):
    """Attributes: bf (the ButtonFrame inside content)"""
    pass

# ── ScrollingListBox ─────────────────────────────────────────────────────
class ScrollingListBoxInterface(FrameInterface):
    """Listbox + Scrollbar wrapper. API-compatible with ScrollingButtonFrame:
    constructor kwargs are optionlist, command, window. The command callback
    fires on selection as command(choice_code, window=window).
    Attributes: listbox, scrollbar, choices (list of choice codes)."""
    pass

# ── RadioButtonFrame ─────────────────────────────────────────────────────
class RadioButtonFrameInterface(FrameInterface):
    """Constructor kwargs: optionlist, horizontal, sticky, variable"""
    pass

# ── ContextMenu ──────────────────────────────────────────────────────────
class ContextMenuInterface(ABC):
    @abstractmethod
    def menuinit(self): ...
    @abstractmethod
    def updatebindings(self): ...
    @abstractmethod
    def undo_popup(self, event=None): ...

# ── ToolTip ──────────────────────────────────────────────────────────────
class ToolTipInterface(ABC):
    """Constructor: ToolTip(widget, text)"""
    pass

# ── Wait ─────────────────────────────────────────────────────────────────
class WaitInterface(WindowInterface):
    """A modal wait/progress dialog."""
    pass

# ── Waitable mixin ──────────────────────────────────────────────────────
class WaitableInterface(ABC):
    """Mixin for windows that can show wait dialogs."""
    @abstractmethod
    def wait(self, msg=None, **kwargs): ...
    @abstractmethod
    def iswaiting(self): ...
    @abstractmethod
    def waitprogress(self, value): ...
    @abstractmethod
    def waitdone(self): ...
    @abstractmethod
    def waitcancel(self): ...
    @abstractmethod
    def waitpause(self): ...
    @abstractmethod
    def waitunpause(self): ...

# ── Module-level functions ───────────────────────────────────────────────
def nfc(x):
    """Unicode NFC normalization."""
    import unicodedata
    return unicodedata.normalize('NFC', x)

def nfd(x):
    """Unicode NFD normalization."""
    import unicodedata
    return unicodedata.normalize('NFD', x)
