# Plan: Remove LazyGlobal

Version 0.1.0

## Problem

LazyGlobal and the companion `__getattr__` pattern exist solely to break circular
dependencies where extracted modules need names that live in `main.py`. Removing
them requires giving every consumed name a non-circular import path. There are
22 files using this pattern, referencing ~60 unique names.

## Inventory of names consumed via LazyGlobal

Every name below is resolved at runtime to an attribute of `main.py`. To remove
LazyGlobal, each name needs a new canonical home that can be imported directly.

### Category A — `_` (gettext translation function)
**Used in:** every file (22 of 22)

`_` is set as a module-level global in `main.py` (line 95) and later replaced
by `App.interfacelang()`. Every extracted module grabs it via LazyGlobal so it
picks up the live, swappable reference.

### Category B — Utility functions already in `utilities/utilities.py`
Names: `nn`, `t`, `flatten`, `dictofchilddicts`, `dictscompare`, `exampletype`,
`grouptype`, `firstoflist`, `nonspace`, `donothing`, `name`,
`internetconnectionproblemin`, `isinterneturl`, `updated`, `uptodate`,
`pathseparate`, `findpath`, `sysexecutableversion`, `openweburl`,
`sysshutdown`, `sysrestart`, `findexecutable`, `callerfn`

These are defined in `utilities/utilities.py` and wildcard-imported into
`main.py`. Modules pull them from main via LazyGlobal instead of importing
directly from utilities.

### Category C — Functions defined only in `main.py`
Names: `unlist`, `loadCAWL`, `saveimagefile`, `scaleimageifthere`,
`scaledimage`, `getimagelocationURI`, `compilesenseimage`, `scale_image`,
`propagate`, `updateazt`, `runtime_to_now`

These are module-level functions in `main.py` (lines 600-732) that reference
`program`, `lift`, `ui`, `file`, or other main-level state.

### Category D — `main` (the module itself) and `program` (the config dict)
Names: `main`, `interfacelang`

Some modules grab `main` itself to access `program` or call `interfacelang()`.

### Category E — Classes imported into `main.py` from elsewhere
Names: `Sort`, `Tone`, `Segments`, `WordCollection`, `Parse`, `Analysis`,
`StatusDict`, `SliceDict`, `Multislice`, `Multicheck`, `Multicheckslice`,
`MultisliceS`, `MultisliceT`, `ByUF`, `Background`, `Mercurial`, `Git`,
`Alphabet`, `FileParser`, `Settings`, `Glosslangs`, `ToneFrames`,
`TaskChooser`, `LiftChooser`, `ImageFrame`, `ResultWindow`, `ErrorNotice`,
`SortGroupButtonFrame`, `SortGlyphGroupButtonFrame`, `StatusFrame`,
`Sound`, `SortT`, `SortV`, `SortC`, `JoinUFgroups`, `TranscribeS`,
`TranscribeV`, `TranscribeC`, `TranscribeT`, `RecordCitation`, `RecordCitationT`,
`ReportCitationT`, `ReportConsultantCheck`, `ReportCitationBackground`,
`ReportCitationMulticheckBackground`, `ReportCitationMultichecksliceBackground`,
`ReportCitationTBackground`, `ReportCitationTLBackground`,
`ReportCitationMultisliceTBackground`, `ReportCitationMultisliceTLBackground`,
`ReportCitationByUFBackground`, `ReportCitationByUFMulticheckBackground`,
`ReportCitationByUFMultichecksliceBackground`, `ReportCitationMultislice`,
`WordCollectionCitation`, `WordCollectionCitationwRecordings`,
`WordCollectnParse`, `WordCollectnParsewRecordings`, `WordsParse`,
`SortSyllables`, `ExportData`, `AlphabetChart`, `AlphabetComparisonPages`,
`Sound`

These all have canonical homes already (in `backend/`, `frontend/`, `tasks/`).
Modules should import them directly from those homes.

### Category F — Other module-level objects
Names: `rx`, `xlp`, `sound`, `sound_ui`, `transcriber`, `nowruntime`,
`logfinished`, `testversion`, `reverttomain`

These are modules or functions imported/defined in `main.py` that other modules
grab via LazyGlobal.

---

## Strategy

### Phase 0: Create a shared `_` mechanism (prerequisite for everything else)

The `_` translation function is the single most pervasive LazyGlobal usage
(22 files). It is special because `App.interfacelang()` *rebinds* it at runtime
to switch languages, so every module must see the updated binding.

**Option A — Translation registry module** (recommended):
Create `utilities/i18n.py`:
```python
# utilities/i18n.py
import gettext

_current = gettext.gettext  # fallback

def _(msg):
    return _current(msg)

def set_translator(func):
    global _current
    _current = func
```
Every module does `from utilities.i18n import _`. `App.interfacelang()` calls
`i18n.set_translator(new_func)` instead of rebinding a global `_`.

**Option B — Module-attribute indirection:**
Keep `_` in a shared module and have consumers access it as `i18n._(msg)`.
Slightly more explicit but requires changing every `_("...")` call site to
`i18n._("...")`. Not recommended due to churn.

### Phase 1: Replace Category B — direct imports from utilities

These are the easiest wins. For each file, replace the LazyGlobal entry with a
direct import from `utilities.utilities`.

Example — `backend/core/analysis.py` currently has LazyGlobal for `flatten`,
`dictofchilddicts`, `dictscompare`, `exampletype`, `grouptype`, `unlist`:

```python
# Before (LazyGlobal)
# ... __getattr__ listing these names ...

# After (direct import — most already have `from utilities.utilities import *`)
# Just remove these names from the __getattr__ and LazyGlobal tuples.
# The wildcard import already covers them.
```

**Files affected:** `backend/core/analysis.py`, `backend/core/vcs.py`,
`backend/reporting/generator.py`, `frontend/ui_shell.py`, `settings/__init__.py`,
`tasks/chooser.py`

**Work per file:** Remove names from both tuples; verify `from utilities.utilities import *`
is present (it already is in most files). For files that don't wildcard-import,
add explicit imports.

### Phase 2: Replace Category E — direct imports from canonical homes

Modules grab class names like `Sort`, `Tone`, `Analysis` from `main.py` when
those classes have clear canonical homes. Replace with direct imports.

Example — `frontend/ui_shell.py` has LazyGlobal for `Sort`, `Analysis`,
`Tone`, `Segments`, etc.:

```python
# Before
# __getattr__ returns getattr(main, 'Sort') etc.

# After
from backend.core.sorting_engine import Sort
from backend.core.lexicon import Tone, Segments, WordCollection, Parse
from backend.core.analysis import Analysis, StatusDict
```

**Circular dependency risk:** Some of these imports may create cycles. The main
risk is when module A imports from module B and B imports from A. Check each
pair:
- `ui_shell.py` → `backend/core/lexicon.py`: lexicon does NOT import ui_shell → **safe**
- `ui_shell.py` → `tasks/tasks.py`: tasks.py imports from ui_shell (TaskDressing) → **circular!**
  - Fix: task class references in ui_shell (like `Sound`, `SortT` in `makeoptions()`)
    should use late binding (import inside function body) or be passed as parameters.
- `tasks/chooser.py` → `tasks/tasks.py`: chooser imports task classes → check if tasks imports chooser → **check needed**
- `settings/__init__.py` → `backend/core/lexicon.py`: check for reverse import → **likely safe**

**Work per file:** Add direct imports, remove from LazyGlobal tuples. For
circular cases, use function-local imports.

### Phase 3: Replace Category C — relocate main.py functions

These functions must move out of `main.py` to be importable without circular
dependencies. Group by dependency:

**Group 3a — Image utilities** (depend on `program`, `file`, `ui`):
`scaledimage`, `scale_image`, `scaleimageifthere`, `getimagelocationURI`,
`compilesenseimage`, `saveimagefile`

Move to `utilities/images.py` or `frontend/images.py`. Pass `program` as a
parameter instead of using the global, or accept the specific attributes needed
(e.g., `settings.imagesdir`, `scale`).

**Group 3b — LIFT/data utilities** (depend on `lift`, `file`, `ErrorNotice`):
`loadCAWL`, `unlist`

Move to `io_put/` or `utilities/`. `unlist` just wraps `firstoflist` with a
`lift.et.Element` check — move to `utilities/utilities.py` with a local import
of `lift`. `loadCAWL` move to `io_put/lift.py` or a new `io_put/cawl.py`.

**Group 3c — UI utilities** (depend on tkinter widgets):
`propagate`

Move to `frontend/ui_tkinter.py`.

**Group 3d — App lifecycle** (depend on `program`):
`runtime_to_now`, `updateazt`

`runtime_to_now` is trivial (uses `times.now()` and `program.start_time`) —
move to `utilities/times.py`, accept start_time as parameter.
`updateazt` is complex (UI + VCS + program) — keep in `main.py` or move to
`backend/core/vcs.py` with program passed as parameter. Only 1 consumer
(ui_shell.py) so a function-local import is also viable.

### Phase 4: Replace Category D — `main` module reference and `interfacelang`

After Phase 0 (`_` handled) and Phase 3 (functions relocated):
- `interfacelang` — only called from `settings_ui.py` and `ui_shell.py`.
  After Phase 0, these modules call `i18n.set_translator()` instead.
  `App.interfacelang()` remains in `main.py` but calls `i18n.set_translator()`.
- `main` — used to access `program` or as a namespace. After other phases,
  the remaining uses should be minimal. Each can be replaced with either:
  - A direct import of the specific object needed, or
  - Passing `program` as a constructor/method parameter (already done in most classes)

### Phase 5: Replace Category F — module references

- `rx` → `from utilities import rx` (already available)
- `xlp` → `from io_put import xlp` (already available)
- `sound` → `from io_put import sound` (already conditionally imported)
- `sound_ui` → `from frontend import sound_ui`
- `transcriber` → `from frontend import transcriber`
- `nowruntime`, `logfinished` → move to `utilities/times.py` or define locally
- `testversion`, `reverttomain` → move to `backend/core/vcs.py`

### Phase 6: Delete LazyGlobal infrastructure

Once all names are resolved through direct imports:
1. Remove `LazyGlobal` class from `utilities/utilities.py`
2. Remove all `__getattr__` functions and `for name in ... LazyGlobal` loops
3. Remove `from utilities.utilities import LazyGlobal` imports
4. Grep for any remaining references

---

## Execution order and risk

| Phase | Files touched | Risk | Can be done incrementally |
|-------|--------------|------|--------------------------|
| 0     | ~22 + main.py | Medium — touches every file | Yes, but must be first |
| 1     | ~6 | Low — imports already present | Yes, per-file |
| 2     | ~10 | Medium — circular dep risk | Yes, per-file with testing |
| 3     | main.py + 4-6 new/target files | High — moving code | Yes, per-group |
| 4     | ~4 | Low after phases 0+3 | Yes |
| 5     | ~5 | Low | Yes, per-name |
| 6     | ~22 | Low — just cleanup | Only after all above |

**Recommended execution:** Phase 0 → 1 → 5 → 2 (safe pairs first) → 3a → 3b →
3c → 3d → 2 (circular pairs) → 4 → 6.

Each phase should be a separate commit. Test by running `python main.py` after
each phase — the app should start and reach the file chooser / task chooser
without import errors.

---

## Changelog

- 0.1.0 — Initial plan draft
