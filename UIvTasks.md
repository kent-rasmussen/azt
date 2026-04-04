# Decoupling Tasks from UI — Implementation Plan

v1.6 — 2026-04-04

## Problem Statement

Every task in A-Z+T **is** a tkinter window. The inheritance chain is:

```
tkinter.Toplevel
  → ui.Window
    → TaskDressing (menus, status frame, dialogs)
      → Task (base class)
        → [backend mixins: Sort, Tone, Segments, WordCollection, Parse]
          → [concrete task: SortT, TranscribeV, RecordCitation, ...]
```

This means:
- Backend logic classes (`Sort`, `Tone`, `Segments`) call `self.withdraw()`, `self.deiconify()`, `self.wait_window()` — tkinter methods inherited from the task's Window base.
- Backend `Sort` directly creates `SortButtonFrame` and `SortGroupButtonFrame` widgets.
- Every task instance creates a tkinter `Toplevel` at construction time.
- Task logic cannot run without a running tkinter event loop.
- The codebase cannot be tested headlessly or ported to another UI framework.

## Current Architecture

### What TaskDressing provides (frontend/ui_shell.py)

**Window lifecycle:** `getrunwindow()`, `clear_runwindow()`, `isrunwindow()`, `on_quit()`, `setmainwindow()`, `i_am_the_task()`

**Status/context UI:** `makestatusframe()`, `setcontext()`, `correlatemenus()`, `_setmenus()`, `_removemenus()`, `makeeverythingok()`

**Parameter dialogs:** `getcheck()`, `getgroup()`, `_getgroup()`, `getglyph()`, `_getglyph()`, `getsensetodo()`, `getsensetodobyletter()`, `getparserlevels()`

**Display:** `maketitle()`, `fullscreen()`, `quarterscreen()`, `setfontsdefault()`, `setfontssmaller()`, `_showdetails()`, `_hidedetails()`

**Inherited from ui.Window:** `self.frame`, `self.exitFlag`, `title()`, `withdraw()`, `deiconify()`, `destroy()`, `wait_window()`, `progress()`, `resetframe()`

### What Task base adds (tasks/base.py)

Mostly class-level flags (`ischooser`, `isreport`, `uses_second_forms`, `cvt_sensitive`, etc.) plus `makecvtok()` and `makeeverythingok()`. The `__init__` stores `self.program`, sets the parent window, and calls `TaskDressing.__init__`.

### How backend mixins use UI

| Mixin | UI methods called on `self` | UI widgets created |
|-------|----------------------------|-------------------|
| `Sort` (sorting_engine) | `getrunwindow()`, `withdraw()`, `runwindow.title()`, `runwindow.waitdone()`, `runwindow.wait_window()` | `SortButtonFrame(...)`, `SortGroupButtonFrame(...)`, `ui.Label(...)`, `ui.Frame(...)` |
| `Tone` (lexicon) | `withdraw()`, `wait_window()` | `ToneFrameDrafter(self)` (via `addframe()`) |
| `Segments` (lexicon) | `getrunwindow()` (via `presortgroups()`) | None directly |
| `WordCollection` (lexicon) | Uses `self.frame` | `ui.Frame()`, `ui.Label()` (in `getwords()`) |
| `Parse` (lexicon) | Inherited from Segments | None directly |
| `Sound` (tasks/sound.py) | `withdraw()`, `deiconify()`, `wait_window()` | `SoundSettingsWindow(self)` |
| `Record` (tasks/sound.py) | Uses `self.runwindow.frame` | `ui.Label()`, `RecordButtonFrame()`, `ui.ScrollingFrame()` |

### How tasks are instantiated

```python
# tasks/chooser.py, line 195
taskclass(program=self.program)

# tasks/base.py, Task.__init__
self.program = program
parent = program.taskchooser  # or program.tk_root
TaskDressing.__init__(self, parent)  # creates Toplevel window
```

---

## Design Goals

1. **Backend mixins must not import or call tkinter.** `Sort`, `Tone`, `Segments`, `WordCollection`, `Parse` should be pure logic that returns data or calls callbacks — never creates widgets.
2. **Task logic should be separable from window lifecycle.** A task's "what to do" should be expressible without "how to show it".
3. **Preserve the existing multiple-inheritance MRO.** The mixin composition pattern (e.g., `class SortT(Sort, Tone, Task)`) is structurally sound — the problem is that `Sort` and `Tone` assume they're mixed into a `Window`, not that the composition itself is wrong.
4. **Incremental migration.** Each phase should leave the app fully functional.

---

## Architecture Target

```
                    ┌──────────────┐
                    │  TaskWindow  │  (tkinter.Toplevel, menus, status, dialogs)
                    │  [frontend]  │
                    └──────┬───────┘
                           │ has-a
                    ┌──────┴───────┐
                    │   TaskBase   │  (flags, program ref, makeeverythingok)
                    │   [tasks]    │
                    └──────┬───────┘
                           │ inherits
              ┌────────────┼─────────────┐
              │            │             │
        ┌─────┴─────┐ ┌───┴────┐  ┌─────┴─────┐
        │ SortLogic │ │  Tone  │  │ Segments  │   (pure logic, no UI)
        │ [backend] │ │[backend│  │ [backend] │
        └───────────┘ └────────┘  └───────────┘
```

**Key change:** TaskBase *has-a* TaskWindow instead of *is-a* Window. Backend mixins interact with UI through a protocol (abstract interface) that TaskWindow implements but TaskBase only references through `self.ui`.

---

## Phases

### Phase 0: Define the UI protocol (LOW RISK)

Create an abstract interface that captures what backend mixins need from the window:

```python
# tasks/ui_protocol.py

class TaskUI:
    """Protocol that backend mixins use for UI operations.
    Implemented by TaskWindow (tkinter) or a test stub."""

    def show_run_window(self, msg=None, title=None):
        """Create and show a secondary work window. Returns a RunWindow handle."""
        raise NotImplementedError

    def hide(self):
        """Hide the task window."""
        raise NotImplementedError

    def show(self):
        """Show the task window."""
        raise NotImplementedError

    def wait_for_window(self, window):
        """Block until window is destroyed."""
        raise NotImplementedError

    def show_progress(self, value, msg=None):
        """Update progress indicator."""
        raise NotImplementedError

    def create_label(self, parent, **kwargs):
        """Create a text label widget."""
        raise NotImplementedError

    def create_frame(self, parent, **kwargs):
        """Create a container frame widget."""
        raise NotImplementedError

    def create_button(self, parent, **kwargs):
        """Create a button widget."""
        raise NotImplementedError

    @property
    def exit_requested(self):
        """Whether the user has requested exit."""
        raise NotImplementedError
```

**Files:** Create `tasks/ui_protocol.py`.
**Risk:** Zero — no existing code changes.

### Phase 1: Introduce `self.ui` on Task (LOW RISK)

Add a `self.ui` attribute to `Task.__init__` that initially points to `self` (since Task IS the window). All existing code continues to work — nothing reads `self.ui` yet.

```python
# tasks/base.py, Task.__init__
class Task(TaskDressing):
    def __init__(self, program, **kwargs):
        self.program = program
        parent = ...
        TaskDressing.__init__(self, parent)
        self.ui = self  # Phase 1: ui IS the window; Phase N: separate object
```

**Files:** `tasks/base.py`
**Risk:** Trivial — adding one attribute.

### Phase 2: Wrap Sort's UI operations (MEDIUM RISK)

This is the highest-value target. `backend/core/sorting_engine.py` has ~46 `ui.` references and directly creates `SortButtonFrame` widgets.

**Step 2a:** Extract Sort's UI widget creation into a new class `frontend/sort_ui.py`:

```python
# frontend/sort_ui.py
from frontend.sort_buttons import SortButtonFrame, SortGroupButtonFrame
from frontend import ui_tkinter as ui

class SortPresenter:
    """Handles all UI rendering for the Sort workflow."""

    def __init__(self, task):
        self.task = task
        self.program = task.program

    def create_button_frame(self, parent, groups, **kwargs):
        return SortButtonFrame(parent, self.task, groups, **kwargs)

    def create_sort_item(self, parent, **kwargs):
        return SortGroupButtonFrame(parent, self.task, **kwargs)

    def create_run_window(self, parent, title):
        return ui.Window(parent, title=title)

    def show_sort_result(self, parent, text, image=None):
        ui.Label(parent, text=text, image=image, ...)

    # ... etc for each UI operation Sort performs
```

**Step 2b:** In `sorting_engine.Sort`, replace direct UI calls with delegation:

```python
# Before (sorting_engine.py):
self.buttonframe = SortButtonFrame(self.groupsFrame, self, groups, ...)
ui.Label(self.runwindow.frame, image=..., ...)

# After:
self.buttonframe = self.sort_presenter.create_button_frame(
    self.groupsFrame, groups, ...)
self.sort_presenter.show_sort_result(self.runwindow.frame, ...)
```

**Step 2c:** Wire it up — `tasks/tasks.py` Sort class creates the presenter:

```python
class Sort(backend.core.sorting_engine.Sort):
    is_sort_task = True
    def __init__(self, **kwargs):
        from frontend.sort_ui import SortPresenter
        self.sort_presenter = SortPresenter(self)
        super().__init__(**kwargs)
```

**Step 2d:** Remove `from frontend import ui_tkinter as ui` and `from frontend.sort_buttons import ...` from `sorting_engine.py`.

**Files:** Create `frontend/sort_ui.py`, modify `backend/core/sorting_engine.py`, `tasks/tasks.py`
**Risk:** Medium — Sort workflow is complex with many UI interactions. Test thoroughly after each method migration.
**Estimated scope:** ~15 methods in Sort that create UI.

### Phase 3: Wrap Tone/Segments UI operations (DONE)

**Tone** calls `self.withdraw()`, `self.wait_window()`, and creates `ToneFrameDrafter(self)` in `addframe()`.

**Strategy:** Replace direct window calls with `self.ui.hide()` / `self.ui.wait_for_window()`:

```python
# Before (lexicon.py, Tone.addframe):
self.withdraw()
t = ToneFrameDrafter(self)
if not t.exitFlag.istrue():
    self.wait_window(t)

# After:
self.ui.hide()
t = self.ui.create_tone_frame_drafter()
if not t.exit_requested:
    self.ui.wait_for_window(t)
```

**Segments** calls `self.getrunwindow()` in `presortgroups()`. Same pattern:

```python
# Before:
self.getrunwindow(msg, title)

# After:
self.ui.show_run_window(msg, title)
```

**WordCollection** creates `ui.Frame()` and `ui.Label()` in `getwords()`. Extract to a presenter:

```python
# frontend/lexicon_ui.py
class WordCollectionPresenter:
    def show_word_entry(self, parent, sense, ...):
        ...  # the UI creation code from getwords()
```

**Files:** Modify `backend/core/lexicon.py`, create `frontend/lexicon_ui.py`
**Risk:** Medium — many call sites, but each is a straightforward delegation.

### Phase 4: Remove `ui_tkinter` from sorting_engine (LOW RISK after Phase 2)

After Phase 2, `sorting_engine.py` should have no direct `ui.` references. Remove the import:

```python
# Remove from sorting_engine.py:
from frontend import ui_tkinter as ui
```

If any remain, they're calls that Phase 2 missed — move them to the presenter.

**Files:** `backend/core/sorting_engine.py`
**Risk:** Low — just verifying Phase 2 is complete.

### Phase 5: Remove `ui_tkinter` from lexicon.py (DONE)

After Phase 3, `lexicon.py` should have no direct `ui.` references. Remove the import. The function-local `ImageFrame` imports remain (they're already using the right pattern).

**Files:** `backend/core/lexicon.py`
**Risk:** Medium — 75 references, many in deeply nested UI code.

### Phase 6: Remove `ui_tkinter` from vcs.py (MEDIUM RISK)

`vcs.py` uses `ui.` for confirmation dialogs and wait windows (~20 refs). Extract these to a VCS UI helper:

```python
# frontend/vcs_ui.py
class VCSPresenter:
    def confirm_commit(self, text):
        """Show commit confirmation dialog. Returns bool."""
        ...

    def show_install_instructions(self, repo_type, install_page, ...):
        """Show repository install instructions window."""
        ...

    def show_wait(self, msg):
        """Show a wait/progress dialog."""
        ...
```

Wire in `vcs.py`:
```python
class Repository:
    def __init__(self, program, **kwargs):
        self.vcs_ui = program.get('vcs_ui')  # injected

    def commitconfirm(self, text):
        if self.vcs_ui:
            return self.vcs_ui.confirm_commit(text)
        return True  # headless: auto-confirm
```

**Files:** Create `frontend/vcs_ui.py`, modify `backend/core/vcs.py`
**Risk:** Medium — VCS dialogs are simpler than Sort, but there are many.

### Phase 7: Remove `ui_tkinter` from generator.py (LOW-MEDIUM RISK)

`generator.py` uses `ui.` for report result windows (~8 refs). Extract to:

```python
# frontend/report_ui.py
class ReportPresenter:
    def create_results_frame(self, parent):
        ...
    def show_result_label(self, parent, text):
        ...
```

**Files:** Create `frontend/report_ui.py`, modify `backend/reporting/generator.py`
**Risk:** Low-medium — fewest references of any backend module.

### Phase 8: Split Task from TaskWindow (HIGH RISK — only after Phases 2-7)

This is the final structural change. Once backend mixins no longer call UI methods on `self`, the inheritance can be inverted.

#### Phase 8A: self.ui indirection (DONE)

All backend UI method calls now go through `self.ui.X()`:
- `self.withdraw()` → `self.ui.withdraw()`
- `self.exitFlag.istrue()` → `self.ui.exitFlag.istrue()`
- `self.getrunwindow()` → `self.ui.getrunwindow()`
- `self.waitdone()` → `self.ui.waitdone()`
- `self.wait(...)` → `self.ui.wait(...)`
- `self.frame` → `self.ui.frame` (in lexicon.py, sorting_engine.py)
- etc.

Currently `self.ui = self` (set in Task.__init__), so this is a no-op. But it
establishes the contract: backend code accesses the window ONLY through `self.ui`.

All `self.runwindow` references (162 total across sorting_engine.py, lexicon.py,
generator.py, body.py, tasks/sound.py, tasks/tasks.py) are now `self.ui.runwindow`.

#### Phase 8B-partial: Extract TaskBase (DONE)

`TaskBase` extracted from `Task` in `tasks/base.py`. Contains all class-level
flags and pure logic methods (makecvtok, makeeverythingok). `Task` now inherits
from `TaskBase` AND `TaskDressing`:

```python
class TaskBase:           # Pure logic, no window
    ischooser = False
    isreport = False
    # ... 12 flags + makecvtok + makeeverythingok

class Task(TaskBase, TaskDressing):   # Logic + window
    def __init__(self, program): ...
```

Concrete tasks still inherit `Task` — no changes needed to 48 task classes.
`TaskBase` can be instantiated without tkinter for testing.

#### Phase 8B-full: Remove TaskDressing from MRO (PENDING — HIGH RISK)

To fully separate task logic from the window, TaskDressing must be removed
from the concrete task's MRO. This requires:

**Prerequisite audit (DONE):** TaskDressing reads these task-logic attrs on `self`:
- `self.ischooser` (2 places), `self.isreport` (1), `self.tasktitle` (3)
- `self.makeeverythingok()` (1 call)
- `isinstance(self, WordCollection)` (1 — line 1555)
- `isinstance(self.task, Multicheck)` (1 — line 1985, guarded by hasattr)
- Most flags are read via `self.program.task.<flag>` in StatusFrame, not
  via `self.<flag>` in TaskDressing — this is already split-safe.

**Remaining blockers:**
- **`super().setcontext()` chain** — overridden in tasks/sound.py and
  tasks/tasks.py, chains through MRO to TaskDressing.setcontext().
  After removing TaskDressing from MRO, the chain breaks. Fix: add
  explicit delegation in TaskBase: `def setcontext(self, ctx=None): self.ui.setcontext(ctx)`
- **TaskWindow creation** — need `TaskWindow(TaskDressing)` with `__getattr__`
  delegating to `self.task` so TaskDressing.__init__ can read task flags.
- **isinstance checks** — `isinstance(self, WordCollection)` in
  TaskDressing line 1555 would fail (self is TaskWindow, not concrete task).
  Fix: `isinstance(getattr(self, 'task', self), WordCollection)`

**Approach:** Use `__getattr__` on BOTH sides:
- TaskBase.__getattr__ → delegates to self.ui (for window methods)
- TaskWindow.__getattr__ → delegates to self.task (for task flags/methods)

**Files:** Modify `tasks/base.py`, create `frontend/task_window.py`, update
`tasks/tasks.py` (48 classes), `tasks/chooser.py`, modify `frontend/ui_shell.py`
**Risk:** HIGH — changes every task class, the instantiation flow, and TaskDressing.
Must be done atomically with thorough manual testing.

---

## Risk Mitigation

### Testing strategy

Since there's no test suite, testing is manual:

1. **After each phase:** Launch the app, open a LIFT file, and exercise the affected task type.
2. **Phase 2 (Sort):** Test all sort variants — SortCV, SortV, SortC, SortT, SortSyllables. Test macro sorting (glyph grouping). Test the verify/re-presort flows.
3. **Phase 3 (Tone/Segments):** Test SortT (tone frames), TranscribeV/TranscribeC (segments), all Transcribe variants.
4. **Phase 6 (VCS):** Test git/mercurial operations — share, clone to USB, commit confirm dialogs.
5. **Phase 7 (Reports):** Generate each report type, verify result windows appear correctly.
6. **Phase 8 (Task split):** Test every task type in the chooser.

### Rollback strategy

Each phase should be a separate commit. If a phase breaks something, `git revert` the commit.

### Migration helpers

For phases 2-3, a common pattern will emerge. Create a helper to catch missed delegations:

```python
class DeprecatedUIAccess:
    """Temporary wrapper that logs when backend code accesses UI directly."""
    def __init__(self, real_ui, module_name):
        self._real = real_ui
        self._module = module_name

    def __getattr__(self, name):
        import warnings
        warnings.warn(
            f"{self._module} accessed UI method '{name}' directly. "
            f"This should go through a presenter.",
            DeprecationWarning, stacklevel=2)
        return getattr(self._real, name)
```

---

## Priority Order

| Phase | Target | Effort | Value |
|-------|--------|--------|-------|
| 0 | Define UI protocol | Trivial | Foundation | **DONE** |
| 1 | Add `self.ui` to Task | Trivial | Foundation | **DONE** |
| 2 | Sort presenter | Medium-High | Highest — Sort is most complex | **DONE** |
| 3 | Tone/Segments/WordCollection presenters | Medium | High — enables lexicon cleanup | Pending |
| 4 | Remove module-level ui_tkinter from sorting_engine | Low | Completes Sort separation | **DONE** (function-local) |
| 5 | Remove module-level ui_tkinter from lexicon | Medium | Completes lexicon separation | **DONE** (function-local) |
| 6 | VCS presenter | Medium | Moderate — VCS is less core | **DONE** |
| 7 | Report presenter | Low-Medium | Moderate | **DONE** |
| 8 | Split Task from TaskWindow | High | Highest — but only possible after 2-7 | Pending |

**Phases 0-1** are prerequisites with zero risk. **DONE.**
**Phases 4-7** (module-level import removal): **DONE.** `vcs.py` and `generator.py` are fully decoupled via presenters (zero frontend imports). `sorting_engine.py` and `lexicon.py` use function-local imports (zero module-level frontend imports).
**Phases 2-3** deliver the most value — once Sort and Tone presenters are in place, even the function-local imports in sorting_engine.py and lexicon.py can be removed.
**Phase 8** is the capstone that makes the architecture clean, but is only safe after everything else.

---

## What This Enables

Once complete:
- **Headless testing:** Task logic can run without tkinter, enabling automated tests.
- **Alternative UIs:** The presenter pattern makes it possible to swap tkinter for another framework (Qt, web, terminal).
- **Cleaner imports:** Backend modules have zero frontend dependencies.
- **Smaller cognitive load:** Each file has a single responsibility — logic OR presentation, not both.

---

## Changelog

- v1.0 (2026-04-03): Initial plan.
- v1.1 (2026-04-03): Phases 0-1, 4-7 complete. VCS and Report presenters created. All backend modules have zero module-level frontend imports. sorting_engine.py and lexicon.py use function-local imports pending presenter extraction (Phases 2-3).
- v1.2 (2026-04-03): Phase 2 complete. SortPresenter created — sorting_engine.py now has zero frontend imports. Only lexicon.py (Phase 3) and alphabet.py remain with function-local imports.
- v1.3 (2026-04-03): Phases 3 and 5 complete. LexiconPresenter created and wired — lexicon.py now has zero frontend imports. Only alphabet.py remains with function-local imports.
- v1.4 (2026-04-04): All phases through 8A complete. All backend modules have zero frontend imports. All backend UI method calls route through self.ui indirection. alphabet.py decoupled via lex_ui. Phase 8B (actual class split) documented with blockers and approach.
- v1.5 (2026-04-04): self.runwindow indirection complete (162 refs). All non-frontend code now accesses UI exclusively through self.ui. Phase 8A fully done — no caveats remain.
- v1.6 (2026-04-04): TaskBase extracted from Task. Phase 8B-partial done. Full 8B blocker audit complete — setcontext chain, isinstance checks, TaskWindow __getattr__ documented.
