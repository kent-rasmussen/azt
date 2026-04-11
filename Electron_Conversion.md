# Electron Frontend Alternative: Implementation Plan

## Architecture Decision: pywebview

**Recommendation: pywebview** over Eel or raw Electron+WebSocket.

**Rationale:**
- pywebview runs a native webview window from Python directly — no Node.js/npm/Electron install required
- Python stays as the single process; the webview is a child window
- Python calls JavaScript via `window.evaluate_js()`, JS calls Python via `pywebview.api` exposed functions
- Supports multiple windows natively (`webview.create_window()`)
- PIL images can be passed as base64 data URIs
- The `wait_window` blocking pattern (used ~50 times) maps to pywebview's `window.destroy()` + threading
- No IPC protocol to design — it is in-process

**Alternatives considered:**
- **Eel**: Simpler but single-window, poor multi-window support, abandoned maintenance
- **Raw Electron+WebSocket**: Maximum flexibility but requires Node.js, complex IPC, two-process management

---

## Communication Architecture

```
Python (main thread)                    Webview (browser thread)
─────────────────────                   ─────────────────────────
ui_electron.Root()                      index.html loads
  └─ webview.create_window()            
                                        
widget = Label(parent, text="hi")       JS: createWidget({id, type, parent_id, props})
  └─ window.evaluate_js(...)            
                                        
                                        User clicks button
                                        JS: pywebview.api.on_event(widget_id, event_data)
  └─ Python callback fires              
                                        
var.set("new value")                    JS: updateProp(widget_id, "text", "new value")
  └─ window.evaluate_js(...)            
```

### Widget Identity

Each Python-side widget object gets a unique `_wid` (integer counter). All JS operations reference widgets by this ID. The JS side maintains a `Map<string, HTMLElement>` registry.

### Layout Strategy

Map `Gridded` kwargs to CSS Grid:
- `row`, `column` → `grid-row`, `grid-column`  
- `rowspan`, `columnspan` → `grid-row: span N`, `grid-column: span N`
- `sticky="nsew"` → combinations of `justify-self` and `align-self` (`stretch`, `start`, `end`)
- `padx`, `pady` → CSS `padding` or `margin`

### Reactive Variables (StringVar/IntVar/BooleanVar)

Create Python-side `Variable`, `StringVar`, `IntVar`, `BooleanVar` classes that:
1. Store the value in Python
2. Maintain a list of trace callbacks (replicating `trace_add('write', cb)`)
3. On `.set()`, fire callbacks AND push the new value to JS via `evaluate_js`
4. No tkinter dependency

### Event Flow

JS event listeners call `pywebview.api.on_event(widget_id, event_type, event_data)`.
Python side maintains `_bindings: dict[str, list[callable]]` per widget.
Event types map: `<Button-1>` → `click`, `<Enter>` → `mouseenter`, `<KeyRelease>` → `keyup`, etc.

### Window Management

- `Root` → hidden pywebview window (or headless coordinator)
- `Window`/`Toplevel` → `webview.create_window()` calls, each gets own HTML document
- `wait_window(w)` → `threading.Event` that blocks until `w` is destroyed
- `withdraw()`/`deiconify()` → `window.hide()`/`window.show()`
- `mainloop()` → `webview.start()` (called once, blocks)

### Images

PIL Image → `base64.b64encode(img_to_png_bytes())` → `<img src="data:image/png;base64,...">` in JS.
The `Image` class stores both PIL data and a base64 cache string.

---

## Phase 0: Abstract Interface Definition (foundation, no UI yet)

**Goal:** Define `frontend/ui_interface.py` — a pure-Python abstract specification of every public widget class, method, and constant that consumers use.

**Files to create:**
- `frontend/ui_interface.py` — ABC/Protocol definitions for all 25+ widget classes

**What it contains:**
- Abstract base classes: `RootBase`, `WindowBase`, `FrameBase`, `LabelBase`, `ButtonBase`, etc.
- Each declares the methods/properties that consumer code actually calls (from grepping usage)
- Constants: `END`, `INSERT`, `N`, `S`, `E`, `W`, `RIGHT`, `LEFT`, `MULTIPLE`, `EXTENDED`, `SINGLE`
- Variable classes: `Variable`, `StringVar`, `IntVar`, `BooleanVar` with `get()`, `set()`, `trace_add()`
- Utility functions: `nfc()`, `nfd()`

**Key methods per widget class (from usage analysis):**
- All widgets: `grid()`, `grid_remove()`, `grid_info()`, `destroy()`, `bind()`, `config()`/`configure()`, `__setitem__`, `__getitem__`, `winfo_exists()`, `winfo_children()`, `winfo_screenwidth()`, `winfo_screenheight()`, `winfo_reqwidth()`, `winfo_reqheight()`
- Root: `mainloop()`, `withdraw()`, `deiconify()`, `update()`, `after()`, `after_cancel()`, `protocol()`, `title()`
- Window/Toplevel: `wait_window()`, `withdraw()`, `deiconify()`, `title()`, `attributes()`, `iconphoto()`, `on_quit()`
- Frame: `grid_size()`, `grid_rowconfigure()`, `grid_columnconfigure()`
- Button: `command` kwarg
- EntryField: `get()`, `textvariable`
- Label: `text`, `image`, `font`, `wraplength`
- ScrollingFrame: `content` attribute, `tobottom()`, `totop()`, `windowsize()`, `update()`
- ButtonFrame: `buttons` dict, `optionlist`
- ListBox: `curselection()`, `get()`, `insert()`, `delete()`
- Combobox: `get()`, `set()`, `values`
- Menu: `add_command()`, `add_cascade()`, `tk_popup()`
- CheckButton: `variable`, `indicatoron`, `selectimage`
- RadioButton: `variable`, `value`
- Progressbar: `current()`

**Testing:** Import the interface, verify `ui_tkinter` classes are compatible (duck-type check script).

---

## Phase 1: Frontend-Independent Variables and Constants

**Goal:** Extract `StringVar`, `IntVar`, `BooleanVar`, and constants out of tkinter dependency.

**Files to create:**
- `frontend/ui_variables.py` — standalone Variable classes with trace support

**Implementation:**
```python
class Variable:
    def __init__(self, value=None, name=None):
        self._value = value
        self._traces = []
    def get(self):
        return self._value
    def set(self, value):
        old = self._value
        self._value = value
        for mode, callback in self._traces:
            if 'write' in mode:
                callback(self._name, '', 'write')
    def trace_add(self, mode, callback):
        self._traces.append((mode, callback))
        return id(callback)
    def trace_remove(self, mode, cbname):
        self._traces = [(m,c) for m,c in self._traces if id(c) \!= cbname]
```

- `StringVar(Variable)` with `value=''` default
- `IntVar(Variable)` with `value=0` default  
- `BooleanVar(Variable)` with `value=False` default

**Files to modify:**
- `frontend/ui_tkinter.py` — change `StringVar = tkinter.StringVar` to import from `ui_variables` (or keep tkinter's for tkinter mode, with a compatibility shim)

**Testing:** Unit test that traces fire on `.set()`.

---

## Phase 2: Minimal ui_electron.py — Root, Window, Frame, Label, Button

**Goal:** Create a working `ui_electron.py` that can display a window with text and buttons.

**Files to create:**
- `frontend/ui_electron.py` — the Electron alternative module
- `frontend/electron_html/base.html` — minimal HTML template
- `frontend/electron_html/widgets.js` — JS widget creation/management
- `frontend/electron_html/grid.css` — CSS Grid layout system
- `frontend/electron_html/theme.css` — dynamic theme injection

**Core Python classes (Phase 2 subset):**

```python
# Widget ID counter
_next_id = itertools.count(1)

class ElectronWidget:
    """Base for all pywebview-backed widgets."""
    def __init__(self, parent, **kwargs):
        self._wid = next(_next_id)
        self.parent = parent
        self._window = parent._window  # the pywebview window object
        self._bindings = {}
        # Extract grid kwargs exactly like Gridded.__init__
        # Send create command to JS
        
    def _js(self, code):
        """Execute JS in this widget's webview window."""
        self._window.evaluate_js(code)
        
    def bind(self, event, handler):
        tk_to_js = {'<Button-1>': 'click', '<Button-3>': 'contextmenu',
                     '<Enter>': 'mouseenter', '<Leave>': 'mouseleave',
                     '<KeyRelease>': 'keyup', '<Double-Button-1>': 'dblclick'}
        js_event = tk_to_js.get(event, event)
        self._bindings.setdefault(event, []).append(handler)
        self._js(f"widgets.bindEvent('{self._wid}', '{js_event}')")
        
    def grid(self, **kwargs): ...
    def grid_remove(self): ...
    def destroy(self): ...
    def config(self, **kwargs): ...
    def configure(self, **kwargs): return self.config(**kwargs)
    def winfo_exists(self): ...
    def winfo_children(self): ...
```

**JS side (`widgets.js`):**
```javascript
const widgets = new Map();

function createWidget(id, type, parentId, props) {
    const el = document.createElement(typeToTag(type));
    el.id = `w-${id}`;
    el.dataset.wid = id;
    applyGridProps(el, props);
    applyStyleProps(el, props);
    const parent = parentId ? widgets.get(parentId) : document.body;
    parent.appendChild(el);
    widgets.set(id, el);
}

function bindEvent(wid, eventType) {
    widgets.get(wid).addEventListener(eventType, (e) => {
        pywebview.api.on_event(wid, eventType, {
            x: e.clientX, y: e.clientY, 
            x_root: e.screenX, y_root: e.screenY
        });
    });
}
```

**pywebview API class:**
```python
class WebviewAPI:
    def __init__(self, root):
        self._root = root
        self._widgets = {}  # wid -> ElectronWidget
    def on_event(self, wid, event_type, event_data):
        widget = self._widgets.get(str(wid))
        if widget:
            # Convert back to tkinter-style event name
            for tk_name, js_name in widget._bindings_map.items():
                if js_name == event_type:
                    for handler in widget._bindings.get(tk_name, []):
                        handler(Event(event_data))
```

**Testing:** Run `testapp4`-style test: create Root, Window, add Labels and Buttons, verify clicks work.

---

## Phase 3: Theme, Renderer, Image, ExitFlag

**Goal:** Port non-widget support classes to work without tkinter.

**Theme:**
- Fonts become CSS font-family + size declarations (no `tkinter.font.Font`)
- Colors stay as hex strings (already compatible)
- Images: load via PIL, convert to base64, inject as `<img>` or CSS `background-image`
- DPI scaling: use `window.devicePixelRatio` from JS, or pass screen dimensions

**Renderer:**
- PIL rendering of diacritics stays identical (PIL has no tkinter dependency)
- Output changes: instead of `PIL.ImageTk.PhotoImage`, produce base64 PNG string
- Cache keyed the same way (font style + wraplength + text)

**Image class:**
- Remove `PIL.ImageTk.PhotoImage` calls
- Add `to_base64()` method that returns `data:image/png;base64,...`
- `compile()` stores base64 string instead of PhotoImage
- `scaled` attribute becomes the base64 string

**ExitFlag:** Already pure Python, no changes needed.

**Testing:** Load theme, verify images display in webview, test rendered text with diacritics.

---

## Phase 4: Remaining Widgets

**Goal:** Implement all remaining widget classes.

**Priority order (by usage frequency):**

1. **ScrollingFrame** — CSS `overflow-y: auto` on a `<div>`. The `content` child is another `<div>` inside it. `tobottom()` → `el.scrollTop = el.scrollHeight`.

2. **ButtonFrame / ScrollingButtonFrame** — Frame containing dynamically created Buttons from `optionlist`. Reuse Frame + Button.

3. **EntryField** — `<input type="text">`. `textvariable` syncs via input events → Python Variable.set() → trace callbacks.

4. **CheckButton** — `<input type="checkbox">` styled with custom images. `variable` is a `BooleanVar`.

5. **RadioButton / RadioButtonFrame** — `<input type="radio">` with shared `variable` (IntVar/StringVar).

6. **ListBox** — `<select multiple>` or custom `<div>` with selectable items. `curselection()`, `insert()`, `delete()`.

7. **Combobox** — `<select>` or searchable dropdown. `<<ComboboxSelected>>` → `change` event.

8. **Menu / ContextMenu** — Custom `<div>` positioned absolute, shown on right-click. `tk_popup()` → show at coordinates.

9. **Progressbar** — `<progress>` or `<div>` with width animation. `current(value)` updates width.

10. **Scrollbar** — Not needed separately in HTML (CSS handles it), but expose the interface for compatibility.

11. **ToolTip** — CSS tooltip on hover with delay (CSS `transition-delay` or JS `setTimeout`).

12. **RadioButtonFrame** — Composition of Frame + RadioButtons.

**Testing:** Each widget gets a standalone test page. Run through `testapp2`/`testapp3`/`testapp4` equivalents.

---

## Phase 5: Blocking Patterns (wait_window, mainloop, after)

**Goal:** Handle the ~50 `wait_window` calls, `mainloop`, and `after` scheduling.

**This is the hardest phase.** The tkinter model is fundamentally synchronous — `wait_window(w)` blocks the calling thread until `w` is destroyed. pywebview runs on its own thread.

**Strategy:**

1. **`mainloop()`** → `webview.start()` called once from main thread. All Python UI logic runs in a background thread (pywebview supports this via `webview.start(func=background_entry, ...)`)

2. **`wait_window(widget)`** → `threading.Event`:
   ```python
   def wait_window(self, widget=None):
       if widget is None:
           widget = self
       evt = threading.Event()
       original_destroy = widget.destroy
       def on_destroy():
           original_destroy()
           evt.set()
       widget.destroy = on_destroy
       evt.wait()  # blocks calling thread until widget destroyed
   ```

3. **`after(ms, callback)`** → `threading.Timer(ms/1000, callback).start()`, returning the timer for `after_cancel`. Must ensure callbacks run on the correct thread (use a queue if needed).

4. **`update()` / `update_idletasks()`** → In pywebview these are mostly no-ops (the browser handles layout). For cases where Python needs to wait for layout, use `time.sleep(0.01)` or JS `requestAnimationFrame` roundtrip.

**Testing:** Test the sort workflow end-to-end (it heavily uses `wait_window` to step through items).

---

## Phase 6: Drag-and-Drop

**Goal:** Implement the `draggable=True`/`droppable=True` kwargs.

**Strategy:** Use HTML5 Drag and Drop API:
- `draggable=True` → `el.draggable = true` + `dragstart`/`dragend` listeners
- `droppable=True` → `dragenter`/`dragover`/`drop` listeners
- `dnd_commit(source, event)` → JS `drop` event calls `pywebview.api.on_dnd_commit(source_wid, target_wid)`
- Visual feedback (highlight on enter) via CSS classes

**Testing:** Run `testapp2` (drag-and-drop test) with Electron frontend.

---

## Phase 7: Leakage Remediation

**Goal:** Address the ~439 direct tkinter calls outside `ui_tkinter.py`.

**This phase does NOT change the tkinter interface** — it adds wrapper methods to `ui_interface` so that both backends support them.

**Categories of leakage and solutions:**

1. **`.grid()` / `.grid_remove()` / `.grid_info()`** (~120 calls) — Already in widget base class. No change needed.

2. **`.bind(event, handler)`** (~173 calls) — Already in widget base class. No change needed.

3. **`.configure()` / `.config()` / `widget['key']=value`** (~60 calls) — Already in widget base class via `__setitem__`.

4. **`.winfo_*()` calls** (~40 calls) — Add to base class: `winfo_exists()`, `winfo_children()`, `winfo_screenwidth()`, `winfo_screenheight()`, `winfo_reqwidth()`, `winfo_reqheight()`, `winfo_toplevel()`, `winfo_x()`, `winfo_y()`, `winfo_rootx()`, `winfo_rooty()`, `winfo_viewable()`.

5. **`.destroy()`** (~30 calls) — Already in widget base class.

6. **`.after()` / `.after_cancel()`** (~10 calls) — Add to widget base class.

7. **`StringVar` / `.trace_add()`** (~80 calls) — Handled by Phase 1 variables.

8. **Heavy files needing attention:**
   - `ui_shell.py` (87 calls): Most are `.grid()`, `.bind()`, `.configure()` which are covered. The `tkinter as tk` import on line 10 needs to become conditional.
   - `alphabet_chart.py` (21 calls): Canvas drawing for alphabet charts — may need a specialized HTML5 Canvas widget.
   - `sort_buttons.py` (15 calls): Mostly covered by base widget methods.
   - `sound_ui.py` (27 calls): Audio playback UI — covered by base widgets.

**The one hard case:** `alphabet_chart.py` uses canvas drawing. This will need either:
- An HTML5 `<canvas>` wrapper widget, or
- Convert the chart to SVG/HTML table generation

**Testing:** Run each of the 19 consumer files with both frontends (import swap test).

---

## Phase 8: main.py Integration

**Goal:** Make the frontend swap work from `main.py`.

**Changes to `main.py`:**
```python
if program['tkinter']:
    import tkinter
    import tkinter.font
    import tkinter.scrolledtext
    if not program['testing']:
        from frontend import tkintermod
        tkinter.CallWrapper = tkintermod.TkErrorCatcher
    from frontend import ui_tkinter as ui
elif program.get('electron'):
    from frontend import ui_electron as ui
```

**Consumer files** already use `from frontend import ui_tkinter as ui` — for the swap, either:
1. Use `frontend/__init__.py` to expose `ui` as an alias (configured at startup), or
2. Each file changes to `from frontend import ui` where `frontend/__init__.py` does the selection

Option 2 is cleaner long-term but requires touching all 19 files.

**Testing:** Full app launch with Electron frontend, run through task chooser → sort workflow.

---

## Dependency Summary

```
Phase 0: ui_interface.py          (no dependencies)
Phase 1: ui_variables.py          (no dependencies)
Phase 2: ui_electron.py basics    (depends on Phase 0, 1)
Phase 3: Theme/Renderer/Image     (depends on Phase 2)
Phase 4: Remaining widgets        (depends on Phase 2, 3)
Phase 5: Blocking patterns        (depends on Phase 2)
Phase 6: Drag-and-drop            (depends on Phase 4)
Phase 7: Leakage remediation      (depends on Phase 4, 5)
Phase 8: main.py integration      (depends on all above)
```

Phases 0 and 1 can be done first and tested independently.
Phases 2 and 5 should be developed together (blocking patterns are needed early).
Phases 3, 4, 6 can proceed incrementally.
Phase 7 can start as soon as Phase 4 is done.

---

## Key Risks and Mitigations

1. **`wait_window` blocking model**: The biggest risk. pywebview's threading model may cause deadlocks if callbacks try to create new windows from the blocked thread. **Mitigation:** Use a dedicated UI command queue; all JS calls go through a single thread.

2. **Performance**: Hundreds of `evaluate_js` calls for building complex UIs (sort buttons with 50+ groups). **Mitigation:** Batch widget creation — send a JSON array of widget specs in one `evaluate_js` call.

3. **Font rendering**: Charis SIL / Andika fonts with diacritics. The Renderer already produces PIL images, which transfer as base64. But in Electron, we could use CSS `@font-face` and render natively (better quality). **Mitigation:** Try CSS fonts first; fall back to PIL rendering.

4. **Canvas operations** in `alphabet_chart.py` and `ScrollingFrame` (which uses `tkinter.Canvas` internally). **Mitigation:** ScrollingFrame becomes CSS `overflow: auto` (simpler). Alphabet chart needs an HTML5 Canvas or SVG approach.

5. **pywebview limitations**: No `eval_js` return values in some backends (Windows CEF vs GTK WebKit). **Mitigation:** Use `window.evaluate_js()` which does return values in pywebview >= 4.0. Pin version.

---

## New Dependencies

- `pywebview>=5.0` (pip installable, no Node.js)
- On Linux: `python3-gi` + `gir1.2-webkit2-4.1` (system packages, usually present)
- On Windows: Uses Edge WebView2 (ships with Windows 10+)
- On macOS: Uses WKWebView (built-in)
