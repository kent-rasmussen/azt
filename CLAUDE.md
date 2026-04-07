# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A-Z+T is a tkinter-based desktop GUI for linguistic fieldwork — sorting, transcribing, recording, and analyzing lexical data from LIFT (Lexicon Interchange FormaT) XML files. It targets SIL linguists working on minority language documentation.

## Running

```bash
# Activate the venv (Python 3.13, built from source at ~/IT/Python-3.13.7)
source env/bin/activate

# Run the app
python main.py

# Install dependencies (CPU-only torch)
pip install -r requirements.txt
```

There is no test suite. `test.py` is a scratch file, not a test runner.

## Architecture

### Task System (frontend/backend split)

Tasks are NOT windows. The class hierarchy is:

```
TaskBase          — pure logic: flags, makecvtok, makeeverythingok (tasks/base.py)
  Task            — creates a TaskWindow on init (tasks/base.py)
    ConcreteTask  — Sort, Transcribe, Report, etc. (tasks/tasks.py)

TaskWindow(TaskDressing) — tkinter window wrapper (frontend/task_window.py)
```

Bidirectional `__getattr__` links them:
- `task.ui` → TaskWindow (backend code calls `self.ui.withdraw()`, `self.ui.frame`, etc.)
- `window.task` → TaskBase (window reads task flags like `is_chooser`, `is_report`)
- `TaskBase.__getattr__` delegates unknown attrs to `self.ui`
- `TaskWindow.__getattr__` delegates unknown attrs to `self.task` (via `object.__getattribute__` to prevent recursion)

### Presenter Pattern (backend/frontend decoupling)

All backend modules have zero frontend imports. Four presenters handle UI widget creation:

- `frontend/sort_ui.py` (`SortPresenter`) — sorting_engine.py widget creation
- `frontend/lexicon_ui.py` (`LexiconPresenter`) — lexicon.py and alphabet.py widget creation
- `frontend/vcs_ui.py` (`VCSPresenter`) — vcs.py commit/wait dialogs
- `frontend/report_ui.py` (`ReportPresenter`) — generator.py result frames

Injected at startup via `program.sort_ui`, `program.lex_ui`, `program.vcs_ui`, `program.report_ui`.

### Cross-Module Import Patterns

- **Direct imports** for most cross-module references.
- **Presenter pattern** (above) for backend → frontend decoupling.
- **`self.ui.X()` indirection** for all backend UI method calls (withdraw, getrunwindow, exitFlag, runwindow, waitdone, etc.).
- **`utilities/i18n.py`** provides a swappable `_()` translation function. All modules do `from utilities.i18n import _`. The live translator is set at startup via `set_translator()`.
- **`utilities/error_handler.py`** provides `notify_error()` for backend modules to show errors without importing frontend code.
- **Flag-based dispatch** instead of `isinstance` checks for task types: `is_sound_task`, `is_record_task`, `is_sort_task`, `is_sort_tone_task` flags on task classes, checked with `getattr(task, 'is_sound_task', False)`.

### Module Layout

- **`main.py`** (~764 lines) — App class, startup, `program` dict (global config), presenter wiring, remaining orchestration functions.
- **`frontend/ui_shell.py`** (~3500 lines) — tkinter UI: menus, status frames, TaskDressing, image frames, splash, error notices, result windows, LiftChooser.
- **`frontend/task_window.py`** — `TaskWindow(TaskDressing)`: tkinter window wrapper for task logic objects.
- **`frontend/sort_buttons.py`** — Sort button frame widgets, extracted from ui_shell.
- **`frontend/sort_ui.py`**, **`lexicon_ui.py`**, **`vcs_ui.py`**, **`report_ui.py`** — Presenter classes.
- **`frontend/ui_tkinter.py`** — tkinter widget helpers and custom widgets.
- **`tasks/`** — Task system:
  - `base.py` — `TaskBase` (pure logic) and `Task(TaskBase)` (creates window).
  - `tasks.py` (~2244 lines) — All concrete task classes.
  - `chooser.py` — `TaskChooser` UI for selecting tasks.
- **`backend/core/`** — Domain logic (zero frontend imports):
  - `lexicon.py` — `Senses`, `Segments`, `WordCollection`, `Parse`, `Tone`.
  - `sorting_engine.py` — `Sort` (linguistic sorting).
  - `analysis.py` — `Analysis`, `SliceDict`, `StatusDict`, `ExampleDict`.
  - `alphabet.py` — `Alphabet`, `AlphabetChartData`, `AlphabetComparisonData`.
  - `vcs.py` — `Repository`, `Mercurial`, `Git`, `GitReadOnly`.
- **`backend/reporting/`** — `Report` and report body generation.
- **`settings/`** — Domain-split config system backed by INI files. `SettingsManager` routes get/set to the correct domain.
- **`io_put/`** — File I/O: `lift.py` (LIFT XML), `xlp.py` (XLingPaper), `export.py`, `sound.py` (audio I/O), `cawl.py`.
- **`utilities/`** — Pure utilities, logging, file ops, HTML helpers, regex, `i18n.py`, `error_handler.py`.

### Key Patterns

- **`program` dict**: Created at `main.py:9`, threaded through most classes as `self.program`. Contains runtime config, flags, and references to major objects.
- **Sound is optional**: `pyaudio`/sound imports are wrapped in try/except; `program['nosound']` gates audio features.

## Build Notes

- Python 3.13 from a custom build (`~/IT/Python-3.13.7`), used via the `env/` virtualenv.
- PyTorch is CPU-only (`torch==2.7.1+cpu` via `--extra-index-url`).
- PyAudio requires system `portaudio` headers (`sudo apt install portaudio19-dev`).
