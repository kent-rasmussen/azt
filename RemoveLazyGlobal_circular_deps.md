# Circular Import Analysis and Recommendations

## Current State After Phases 0-5

### Files fully LazyGlobal-free (18 of 22 original)
- `backend/core/report_mixins.py`
- `backend/core/file_parser.py`
- `backend/core/alphabet.py`
- `backend/core/analysis_inputs.py`
- `backend/core/analysis.py`
- `backend/core/sorting_engine.py`
- `backend/core/vcs.py` (uses deferred `__getattr__`, no LazyGlobal class)
- `backend/reporting/generator.py`
- `backend/parser.py`
- `frontend/error_notice.py`
- `frontend/transcriber.py`
- `frontend/config/settings_ui.py`
- `tasks/base.py`
- `tasks/tasks.py`
- `tasks/chooser.py`
- `tasks/alphabet_chart.py`
- `tasks/alphabet_comparison.py`
- `io_put/xlp.py`

### Files with remaining LazyGlobal (4)
- `frontend/ui_shell.py` — 10 names
- `backend/core/lexicon.py` — 3 names
- `settings/__init__.py` — cleaned up, 0 remaining
- `utilities/utilities.py` — defines the LazyGlobal class itself

---

## Root Causes

### 1. Backend modules import frontend UI directly

Five backend modules import `frontend.ui_tkinter as ui` and/or `frontend.error_notice`:

| Backend module | Frontend imports | Why |
|---|---|---|
| `backend/core/sorting_engine.py` | `ui_tkinter`, `error_notice`, `ui_shell.SortGroupButtonFrame` | Sort class builds UI button frames |
| `backend/core/lexicon.py` | `ui_tkinter`, `error_notice` | Segments/WordCollection build regex UI, show errors |
| `backend/core/analysis.py` | `error_notice` | Shows errors |
| `backend/core/vcs.py` | `ui_tkinter`, `error_notice` | Repository shows confirmation dialogs |
| `backend/reporting/generator.py` | `ui_tkinter`, `error_notice` | Report shows progress/result windows |

This is the fundamental architectural issue. Backend should not know about UI.

### 2. `settings` inherits from `settings_ui`

`settings/__init__.py` does `from frontend.config.settings_ui import SettingsUI` and
`class Settings(SettingsUI)`. This means the settings *backend* inherits from a
*frontend* class, pulling the entire UI chain into settings import time.

### 3. `tasks/base.py` inherits from `frontend/ui_shell.TaskDressing`

`Task` (the base class for all 48 task classes) inherits from `TaskDressing`
(a UI window class). This means every task IS a window, coupling task logic to
tkinter at the class-definition level.

### 4. main.py image functions use `program` global

`scaleimageifthere`, `saveimagefile`, `scaledimage`, `getimagelocationURI` all
access the `program` global directly. They can't be moved without either passing
`program` as a parameter (changing all call sites) or injecting it at startup.

---

## Remaining Circular Dependency Chains

### Chain A: ui_shell ↔ sorting_engine
```
ui_shell.py  →(imports Sort via LazyGlobal)→  sorting_engine.py
sorting_engine.py  →(imports SortGroupButtonFrame)→  ui_shell.py
```
**Why it exists:** `Sort` (backend logic) builds UI button frames using
`SortGroupButtonFrame` (frontend widget). The Sort class mixes data processing
with UI rendering.

**Recommendation:** Extract `SortGroupButtonFrame` into a separate file
(`frontend/sort_buttons.py`) that neither ui_shell nor sorting_engine import
at module level. Then:
- `sorting_engine.py` does `from frontend.sort_buttons import SortGroupButtonFrame`
  (sort_buttons doesn't import sorting_engine → no cycle)
- `ui_shell.py` does `from frontend.sort_buttons import SortGroupButtonFrame`
  (already safe)
- `ui_shell.py` does `from backend.core.sorting_engine import Sort` (sort_buttons
  doesn't import ui_shell → no cycle)

**Longer term:** The real fix is that `Sort` should not build button frames.
Split `Sort` into:
- `backend/core/sorting_engine.py` — pure sorting logic (no UI imports)
- `frontend/sort_ui.py` — Sort UI (buttons, frames) that imports from both
  sorting_engine and ui_shell

### Chain B: ui_shell ↔ tasks (via Sound, SortT)
```
ui_shell.py  →(imports Sound, SortT via LazyGlobal)→  tasks/tasks.py
tasks/tasks.py  →(imports SortGroupButtonFrame, SortGlyphGroupButtonFrame)→  ui_shell.py
```
**Why it exists:** ui_shell references task class names (Sound, SortT) for
`isinstance` checks or `makeoptions()` logic. Task classes import UI widgets
from ui_shell.

**Recommendation:** The task class references in ui_shell should use string-based
dispatch or a registry pattern instead of direct class references:
```python
# Instead of: isinstance(task, Sound)
# Use:        task.__class__.__name__ == 'Sound'
# Or:         hasattr(task, 'is_sound_task')  # flag on Sound class
```
This eliminates ui_shell's need to import task classes entirely.

**Longer term:** Task classes importing `SortGroupButtonFrame` from ui_shell is
the same issue as Chain A. Resolving Chain A fixes this side too.

### Chain C: vcs ↔ settings (via Settings)
```
vcs.py  →(imports Settings via deferred __getattr__)→  settings/__init__.py
settings/__init__.py  →(imports SettingsUI)→  settings_ui.py
settings_ui.py  →(imports Sort)→  sorting_engine.py
sorting_engine.py  →(imports SortGroupButtonFrame)→  ui_shell.py
ui_shell.py  →(imports Mercurial, Git via LazyGlobal)→  vcs.py  [indirect]
```
**Why it exists:** VCS needs Settings to access repository configuration.
The chain is long because Settings inherits from SettingsUI which pulls in
the entire frontend import chain.

**Recommendation (short term):** The deferred `__getattr__` in vcs.py already
works. Keep it.

**Recommendation (long term):** Split `Settings` into backend-only config
(no UI inheritance) and a UI adapter:
- `settings/__init__.py` defines `Settings` with pure data logic
- `settings/__init__.py` does NOT import `SettingsUI`
- `frontend/config/settings_ui.py` defines `SettingsWithUI(Settings, SettingsUI)`
  or wraps Settings with a UI adapter
- main.py instantiates `SettingsWithUI` (the composed version)

This breaks the inheritance chain and lets vcs import Settings directly.

### Chain D: ui_shell ↔ vcs (via Mercurial, Git)
```
ui_shell.py  →(imports Mercurial, Git via LazyGlobal)→  vcs.py
vcs.py  →(imports Settings)→  settings  →  settings_ui  →  sorting_engine  →  ui_shell.py
```
**Why it exists:** ui_shell menus offer "switch to Mercurial/Git" options.

**Recommendation:** Use function-local imports at the 2 call sites in ui_shell
(lines 3089, 3092). These are menu callbacks, called rarely at runtime:
```python
def switch_to_git(self):
    from backend.core.vcs import Git
    ...
```
This completely eliminates the LazyGlobal need.

### Chain E: lexicon ↔ ui_shell (via ImageFrame)
```
lexicon.py  →(imports ImageFrame via LazyGlobal)→  main  →  ui_shell.ImageFrame
ui_shell.py  →(imports Report)→  generator  →(imports Tone, Segments)→  lexicon.py
```
**Why it exists:** `lexicon.py` builds image display frames directly inside
data model classes (Senses, WordCollection).

**Recommendation:** `ImageFrame` is a UI widget being used inside backend data
classes. The ~10 call sites in lexicon.py should use a callback or factory pattern:
```python
# In lexicon class __init__ or setup:
self.image_frame_factory = kwargs.get('image_frame_factory', None)

# At call site (instead of ImageFrame(parent, sense, ...)):
if self.image_frame_factory:
    self.image_frame_factory(parent, sense, ...)
```
main.py or the task initialization code passes `image_frame_factory=ImageFrame`
when constructing lexicon objects. Lexicon no longer needs to know about ImageFrame.

**Longer term:** The lexicon classes should not build UI at all. The pattern of
data-model classes containing UI rendering methods is the deepest architectural
issue. Ideally:
- `backend/core/lexicon.py` — pure data (senses, entries, forms)
- `frontend/lexicon_ui.py` — UI rendering for lexicon data

---

## Recommended Priority Order

| Priority | Action | Unblocks | Effort |
|----------|--------|----------|--------|
| 1 | Extract SortGroupButtonFrame to `frontend/sort_buttons.py` | Chains A, B, C | Low |
| 2 | Function-local imports for Mercurial/Git in ui_shell | Chain D | Trivial |
| 3 | String-based dispatch for task classes in ui_shell | Chain B | Medium |
| 4 | Split Settings inheritance (backend/frontend) | Chain C | Medium |
| 5 | Callback pattern for ImageFrame in lexicon | Chain E | Medium |
| 6 | Remove `ui_tkinter` imports from backend modules | All | High (many call sites) |
| 7 | Separate Task logic from TaskDressing window | Foundational | High |

Items 1 and 2 together would eliminate most remaining LazyGlobal usage.
Items 1-5 would make the codebase fully LazyGlobal-free.
Items 6-7 are the deeper architectural separation of frontend/backend.

---

## The `program` Global Problem

The remaining main.py functions (`scaleimageifthere`, `saveimagefile`,
`scaledimage`, `getimagelocationURI`, `updateazt`) all depend on the `program`
global. Two approaches:

**A. Inject at module init** — After `App.__init__` creates the program object,
call an init function on each module that needs it:
```python
import frontend.image_utils
frontend.image_utils.init(program)
```
The module stores `program` as a module-level variable. Functions access it
without parameters. Call sites don't change.

**B. Access via `self.program`** — Most call sites are inside methods on objects
that already have `self.program`. Refactor to pass program explicitly:
```python
scaleimageifthere(sense, self.program)
```
More explicit, but requires changing every call site.

Option A is lower-risk for the current codebase. Option B is cleaner long-term.
