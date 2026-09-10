# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A-Z+T is a desktop GUI for linguistic fieldwork — sorting, transcribing, recording, and analyzing lexical data from LIFT (Lexicon Interchange FormaT) XML files. It targets SIL linguists working on minority language documentation. The UI has a pluggable backend: tkinter (default) or pywebview, selected via the `AZT_UI_BACKEND` environment variable or configuration.

## Running

```bash
# Activate the venv (Python 3.13, built from source at ~/IT/Python-3.13.7).
# It is the SUITE venv one level up, not azt/env — there is no azt/env.
source ../env/bin/activate

# Run the app
python main.py

# Force a UI backend (default tkinter). --webview needs pywebview AND a host
# toolkit visible to this venv; it refuses and falls back with a reason if not.
python main.py --webview
python main.py --tkinter
python main.py --webview --engine=gtk    # or --engine=qt (Linux engine choice)

# Run the dev checkout AS A USER WOULD: no dev settings, so error screens and
# log zipping are on, no test lift or auto-opened task, and (under webview) no
# devtools panel and no debug window badge. Dev settings are otherwise chosen
# by the checkout's location (parent dir 'AZT'), with no other way to opt out.
python main.py --user

# Other webview switches (SWITCHES, not env vars — standing rule 2026-09-08):
python main.py --webview --no-splash        # skip the splash (it can be in the way)
python main.py --webview --no-kiosk        # DON'T make task windows fullscreen. Kiosk is
                                           # the intended default (task windows fill the
                                           # screen so users aren't distracted); this is
                                           # for debugging layout.
python main.py --webview --webview-hidden  # re-test creating windows hidden (known broken
                                           # on GTK: show() never maps them)

# Install dependencies (CPU-only torch)
pip install -r requirements.txt
```

## Testing

A pytest suite lives in `tests/` (started 2026-06-06; see `tests/README.md`).

```bash
pip install -r requirements-dev.txt   # one-time: installs pytest
pytest                                 # headless; no Tk display needed
pytest -m "not integration"            # skip stubs awaiting fixtures
```

**Use A-Z+T's own python, and install the dev requirements first.** Both are
easy to miss and fail in confusing ways: the app's packages live in its venv,
so a bare `python` reports numpy/sounddevice missing on a machine where the
app runs fine (seen on Windows and macOS, 2026-09-10), and `pytest` is in
`requirements-dev.txt` — which the app's auto-install does NOT sync, since it
reads `requirements.txt` only. So on a fresh install:

```bash
# Linux / macOS
../env/bin/python -m pip install -r requirements-dev.txt
../env/bin/python -m pytest -q

# Windows (Git Bash / MINGW64)
../env/Scripts/python.exe -m pip install -r requirements-dev.txt
../env/Scripts/python.exe -m pytest -q
```

The suite is headless by design — no display, no audio device, no files — so
it runs on any of the three platforms. Tests that need something absent skip
rather than fail.

Coverage so far is guardrails + units: an **import smoke test** (every module
must import; missing optional deps skip, real errors fail), a **`waiting()`
context-manager contract** test (guards the stuck-dialog fix), and units for
`settings.manager` and pure `utilities`. `backend/core` has API-surface guards
plus skipped behavioral stubs to grow into. Keep `backend/core` tests
frontend-free; prefer testing real methods with a fake `self` over a live Tk
root. `test.py` (at the project root) is a scratch file, **not** part of the suite.

## Architecture

### UI Backend Abstraction

Consumer code imports `from frontend import ui`, which resolves to either `ui_tkinter` or `ui_webview` based on the `AZT_UI_BACKEND` env var (see `frontend/__init__.py`). Key pieces:

- **`frontend/ui_interface.py`** — Abstract interface (ABC) defining the contract both backends must fulfill: constants (`END`, `INSERT`, `N`, `S`, etc.), Variable classes, and widget APIs.
- **`frontend/ui_tkinter.py`** — tkinter backend implementation.
- **`frontend/ui_webview.py`** — pywebview backend (Phase 2–3 complete: Root, Window, Frame, Label, Button, Theme, Image, Renderer; remaining widgets are stubs).
- **`frontend/ui_variables.py`** — Standalone `Variable`/`StringVar`/`IntVar`/`BooleanVar` classes (tkinter-free) for the webview backend.

### Task System (frontend/backend split)

Tasks are NOT windows. The class hierarchy is:

```
TaskBase          — pure logic: flags, makecvtok, makeeverythingok (tasks/base.py)
  Task            — creates a TaskWindow on init (tasks/base.py)
    ConcreteTask  — Sort, Transcribe, Report, etc. (tasks/tasks.py)
                  — TaskChooser (tasks/chooser.py)
                  — AlphabetChart (tasks/alphabet_chart.py)
                  — AlphabetComparisonPages (tasks/alphabet_comparison.py)

TaskWindow(TaskDressing) — tkinter window wrapper (frontend/task_window.py)
```

Backend mixins (no frontend imports):
```
Categories        — group/category management: create, rename, reassign groups
                    (backend/core/categories.py)
  Sort(Categories) — sorting presentation, verification, join logic
                    (backend/core/sorting_engine.py)

Senses            — base sense operations, verification codes (backend/core/lexicon.py)
  Segments(Senses) — segmental (C/V) annotation operations
  Tone(Senses)     — tone annotation operations
```

Concrete task inheritance:
```
SortS(Sort, Segments, Task)           — segmental sort tasks
SortT(Sort, Tone, Task)               — tone sort tasks
Transcribe(Sound, Categories, Task)   — transcription (does NOT inherit Sort)
  TranscribeS(Transcribe, Segments)   — segmental transcription
  TranscribeT(Transcribe, Tone)       — tone transcription
```

Bidirectional `__getattr__` links them:
- `task.ui` → TaskWindow (backend code calls `self.ui.withdraw()`, `self.ui.frame`, etc.)
- `window.task` → TaskBase (window reads task flags like `is_chooser`, `is_report`)
- `TaskBase.__getattr__` delegates unknown attrs to `self.ui`
- `TaskWindow.__getattr__` delegates unknown attrs to `self.task` (via `object.__getattribute__` to prevent recursion)

The `tasks/ui_protocol.py` module defines `TaskUI`, a semantic interface that backend mixins were *intended* to use for UI operations (`show_run_window`, `hide`, `show`, `wait_for_window`, etc.). **It is not adopted: nothing imports it.** Backend/tasks code instead calls the TaskWindow's Tk-shaped API through the `__getattr__` bridges above (`getrunwindow`, `withdraw`, `deiconify`, `wait_window`, `waitdone`, `runwindow.…`) — `drive_work` is the one member the two agree on. Finish-or-delete is an open decision: `agenda/ui_protocol_finish_or_kill.md`.

Sound tasks use a mixin split: `backend/core/sound.py` (headless audio logic) and `tasks/sound.py` (UI task mixin inheriting from it + `frontend/sound_ui.py`).

### Presenter Pattern (backend/frontend decoupling)

All backend modules have zero frontend imports. Presenters handle UI widget creation:

- `frontend/sort_ui.py` (`SortPresenter`) — sorting_engine.py widget creation
- `frontend/lexicon_ui.py` (`LexiconPresenter`) — lexicon.py and alphabet.py widget creation
- `frontend/vcs_ui.py` (`VCSPresenter`) — vcs.py commit/wait dialogs
- `frontend/report_ui.py` (`ReportPresenter`) — generator.py result frames
- `frontend/sound_ui.py` — Sound settings window UI

Injected at startup via `program.sort_ui`, `program.lex_ui`, `program.vcs_ui`, `program.report_ui`.

### Cross-Module Import Patterns

- **`from frontend import ui`** — the standard way to access UI widgets. Resolves to the active backend.
- **Presenter pattern** (above) for backend → frontend decoupling.
- **`self.ui.X()` indirection** for all backend UI method calls (withdraw, getrunwindow, exitFlag, runwindow, waitdone, etc.).
- **`utilities/i18n.py`** provides a swappable `_()` translation function. All modules do `from utilities.i18n import _`. The live translator is set at startup via `set_translator()`.
- **`utilities/error_handler.py`** provides `notify_error()` for backend modules to show errors without importing frontend code.
- **Flag-based dispatch** instead of `isinstance` checks for task types: `is_sound_task`, `is_record_task`, `is_sort_task`, `is_sort_tone_task` flags on task classes, checked with `getattr(task, 'is_sound_task', False)`.

### Settings System

The settings system (`settings/`) uses domain-split config backed by JSON files. Key classes:

- **`settings/manager.py`** — `ConfigManager` base class: JSON-backed per-domain config with read/write, `CustomEncoder` for sets/Paths.
- **`settings/__init__.py`** — `AppSettingsManager` (pre-project settings: last file, UI language) and `SettingsManager` (post-project: routes get/set to domain configs). Legacy .ini/.dat files are no longer written; JSON domain files are the sole write path. Legacy read fallback is preserved for migration.
- **Domain configs**: `project.py`, `ui.py`, `audio.py`, `alphabet.py`, `contributors.py`, `data.py`, `reports.py`, `app.py` — each inherits from `ConfigManager`.

### Module Layout

- **`main.py`** (~800 lines) — App class, startup, `program` dict (global config), presenter wiring, remaining orchestration functions.
- **`frontend/`** — UI layer:
  - `__init__.py` — Backend selector (`from frontend import ui` resolves to tkinter or webview).
  - `ui_interface.py` — Abstract UI backend contract (ABC).
  - `ui_tkinter.py` — tkinter widget helpers and custom widgets.
  - `ui_webview.py` — pywebview backend (partial, in progress).
  - `ui_variables.py` — Standalone Variable classes for non-tkinter backends.
  - `ui_shell.py` (~3500 lines) — Main UI: menus, status frames, TaskDressing (includes chooser tab UI via `_build_chooser_tabs`/`_populate_chooser_tab`), image frames, splash, error notices, result windows, LiftChooser.
  - `task_window.py` — `TaskWindow(TaskDressing)`: window wrapper for task logic objects.
  - `sort_buttons.py` — Sort button frame widgets.
  - `sort_ui.py`, `lexicon_ui.py`, `vcs_ui.py`, `report_ui.py` — Presenter classes.
  - `sound_ui.py` — Sound settings and record button UI.
  - `transcriber.py` — `Transcriber` widget (text input with character palette).
  - `alphabet_chart.py` — Alphabet chart UI (draggable/droppable labels).
  - `alphabet_comparison.py` — Alphabet comparison booklet UI.
  - `error_notice.py` — `ErrorNotice` popup window.
  - `tkintermod.py` — Tkinter error catcher.
- **`tasks/`** — Task system:
  - `base.py` — `TaskBase` (pure logic) and `Task(TaskBase)` (creates window).
  - `tasks.py` (~2236 lines) — Most concrete task classes (Sort, Transcribe, Report, etc.).
  - `alphabet_chart.py` — `AlphabetChart` task.
  - `alphabet_comparison.py` — `AlphabetComparisonPages` task.
  - `sound.py` — Sound task UI mixin (bridges `backend/core/sound.py` + `frontend/sound_ui.py`).
  - `chooser.py` — `TaskChooser`: task selection logic, category lists. UI lives in TaskDressing.
  - `transcribe_glyph.py` — `GlyphTranscribeHelper`: shared glyph transcription UI for Transcribe and `name_new_glyphs`.
  - `ui_protocol.py` — `TaskUI`, a semantic task↔window interface. **Unadopted — imported by nothing**; see `agenda/ui_protocol_finish_or_kill.md`.
- **`backend/core/`** — Domain logic (zero frontend imports):
  - `lexicon.py` — `Senses`, `Segments`, `WordCollection`, `Parse`, `Tone`.
  - `categories.py` — `Categories` mixin: group creation, renaming, reassignment, verification node manipulation. Inherited by both Sort and Transcribe.
  - `sorting_engine.py` — `Sort(Categories)`: sorting presentation, verification UI, join logic. Sort-specific methods (`marksorted`, `sort`, `verify`, `join`, etc.).
  - `analysis.py` — `Analysis`, `SliceDict`, `StatusDict`, `ExampleDict`.
  - `analysis_inputs.py` — Analysis input data structures.
  - `alphabet.py` — `Alphabet`, `AlphabetChartData`, `AlphabetComparisonData`.
  - `vcs.py` — `Repository`, `Mercurial`, `Git`, `GitReadOnly`.
  - `sound.py` — `Sound` headless mixin: PyAudio streams, audio card config.
  - `profiles.py` — `ProfileAnalyzer`: syllable CV profile analysis (extracted from settings).
  - `templates.py` — `WordListTemplate`: CAWL wordlist template handling.
  - `report_mixins.py` — `Multislice` and report-related backend mixins.
  - `file_parser.py` — File parsing utilities for LIFT data.
- **`backend/reporting/`** — `Report` and report body generation (`generator.py`).
- **`settings/`** — Domain-split config system backed by JSON files. `SettingsManager` routes get/set to the correct domain. Domain configs: `project.py`, `ui.py`, `audio.py`, `alphabet.py`, `contributors.py`, `data.py`, `reports.py`, `app.py`.
- **`io_put/`** — File I/O: `lift.py` (LIFT XML), `xlp.py` (XLingPaper), `export.py`, `sound.py` (audio I/O), `cawl.py`, `alphabet_chart_pdf.py`, `alphabet_comparison_pdf.py`, `images_CAWL.py`.
- **`utilities/`** — Pure utilities: logging (`logsetup.py`), file ops (`file.py`), HTML helpers (`htmlfns.py`), regex (`rx.py`), `i18n.py`, `error_handler.py`, `encodings.py`, `executables.py`, `duplicates.py`, `times.py`, `ui_lang.py`, `urls.py`, `xmlfns.py`, `xmletfns.py`, `openclipart.py`, `py_modules.py`.

### Key Patterns

- **`program` dict**: Created at `main.py:9`, threaded through most classes as `self.program`. Contains runtime config, flags, and references to major objects.
- **Sound is optional**: `pyaudio`/sound imports are wrapped in try/except; `program['nosound']` gates audio features.

## Shallow clones: widen the refspec before checking out a branch

Clones are `--depth 1` by design (agenda/rework_install_procedure.md). That
implies `--single-branch`, so the clone's refspec covers ONLY the default
branch and `git checkout testing` fails with "did not match any file(s) known
to git" — no ref for it can ever arrive. The clone looks normal; it isn't.

Whenever you need another branch in a shallow clone:

```bash
git remote set-branches --add origin <branch>   # config edit; downloads nothing
git fetch --depth 1                             # branch TIPS only, still shallow
git checkout <branch>
```

**Name the branches; don't use `'*'`.** For an installed copy the only two a
user can reach are `main` and `program['testversionname']` (`'testing'`,
`main.py:30`) — `vcs.py:1126` toggles between exactly those and nothing else.
A `'*'` refspec would also pull every work branch on the remote, which no
install has any use for. The macOS installer sets this up at clone time and
reads the test-branch name out of `main.py` rather than hardcoding it.

**In-app branch switching is already handled** and needs none of this:
`backend/core/vcs.py::fetch_tracking_branch()` fetches
`<branch>:refs/remotes/origin/<branch>` with an explicit refspec for exactly
this reason (its docstring says so) — don't "fix" that by widening refspecs.

## Build Notes

- Python 3.13 from a custom build (`~/IT/Python-3.13.7`), used via the **suite** virtualenv
  at `AZT/env/` — shared with the rest of the suite. There is **no `azt/env/`**; this file
  said there was until 2026-09-04, which makes every `source env/bin/activate` line copied
  out of it fail.
- The venv has `include-system-site-packages = true` (set 2026-09-05 in
  `AZT/env/pyvenv.cfg`) so it can import apt-installed bindings — specifically `gi`, which
  pip cannot supply and which pywebview's GTK backend needs. Before that, `gi` was
  invisible no matter how many `gir1.2-*` packages were installed, and the webview backend
  fell back to Qt.
  - Consequence worth knowing: system site-packages are a **fallback**, not an override —
    the venv's own packages still win — but a module that is absent from the venv will now
    resolve to the system copy instead of failing. If a suite app starts importing
    something nobody pinned, this is why.
  - pywebview's GTK backend wants **Gtk 3.0** and **WebKit2 4.1** (`gi.require_version` in
    `webview/platforms/gtk.py`): `gir1.2-gtk-3.0`, `gir1.2-webkit2-4.1`, `gir1.2-soup-3.0`.
    `gir1.2-gtk-4.0` does nothing for it.
- PyTorch is CPU-only (`torch==2.7.1+cpu` via `--extra-index-url`).
- PyAudio requires system `portaudio` headers (`sudo apt install portaudio19-dev`).
