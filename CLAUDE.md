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

### Cross-Module Import Patterns

The codebase uses several patterns to manage dependencies between modules:

- **Direct imports** for most cross-module references.
- **Function-local imports** (`from main import X` inside a method body) where direct imports would create circular dependencies. Used for `ImageFrame`, `updateazt` — functions in `main.py` that depend on the `program` global.
- **Presenter pattern** for backend/frontend decoupling: `frontend/vcs_ui.py` (`VCSPresenter`) and `frontend/report_ui.py` (`ReportPresenter`) handle all UI widget creation for `vcs.py` and `generator.py` respectively. Injected via `program.vcs_ui` and `program.report_ui` at startup.
- **Static lazy-import helpers** in `sorting_engine.py`: `@staticmethod def _ui(): from frontend import ui_tkinter as ui; return ui` pattern, called locally as `ui = self._ui()`. Avoids module-level frontend imports while keeping code readable.
- **`utilities/i18n.py`** provides a swappable `_()` translation function. All modules do `from utilities.i18n import _`. The live translator is set at startup via `set_translator()`.
- **`utilities/error_handler.py`** provides `notify_error()` for backend modules to show errors without importing frontend code. The real `ErrorNotice` UI class is wired in at startup via `set_error_handler()`.
- **Flag-based dispatch** instead of `isinstance` checks for task types: `is_sound_task`, `is_record_task`, `is_sort_task`, `is_sort_tone_task` flags on task classes, checked with `getattr(task, 'is_sound_task', False)`.

### Module Layout

- **`main.py`** (~764 lines) — App class, startup, `program` dict (global config), remaining orchestration functions (`updateazt`, `loadCAWL`, image utils, `propagate`). The `program` dict is the central config object passed everywhere.
- **`frontend/ui_shell.py`** (~3500 lines) — tkinter UI: menus, status frames, task UI dressing, image frames, splash, error notices, result windows, LiftChooser.
- **`frontend/sort_buttons.py`** — Sort button frame widgets (`SortButtonFrame`, `SortGroupButtonFrame`, `SortGlyphGroupButtonFrame`), extracted from ui_shell to break circular dependencies.
- **`frontend/vcs_ui.py`** — `VCSPresenter`: commit confirmation dialogs, wait windows, exe-missing warnings. Decouples `vcs.py` from frontend.
- **`frontend/report_ui.py`** — `ReportPresenter`: results frames, scrolling frames, labels for report display. Decouples `generator.py` from frontend.
- **`frontend/ui_tkinter.py`** — tkinter widget helpers and custom widgets.
- **`tasks/`** — Task system:
  - `base.py` — `Task` base class (inherits `TaskDressing` from ui_shell).
  - `tasks.py` (~2244 lines) — All 48 concrete task classes (Sound, Record, Sort*, Report*, Transcribe*, etc.).
  - `chooser.py` — `TaskChooser` UI for selecting tasks.
- **`backend/core/`** — Domain logic:
  - `lexicon.py` — `Senses`, `Segments`, `WordCollection`, `Parse`, `Tone` (data model).
  - `sorting_engine.py` — `Sort` (linguistic sorting).
  - `analysis.py` — `Analysis`, `SliceDict`, `StatusDict`, `ExampleDict`.
  - `analysis_inputs.py` — `ToneFrames`, `CheckParameters`, `Glosslangs`.
  - `alphabet.py` — `Alphabet` class.
  - `file_parser.py` — `FileParser`.
  - `report_mixins.py` — `Multislice`, `Multicheck`, `ByUF`, `Background` mixins.
  - `vcs.py` — `Repository`, `Mercurial`, `Git`, `GitReadOnly`.
- **`backend/reporting/`** — `Report` and report body generation.
- **`settings/`** — Domain-split config system (`ProjectConfig`, `UIConfig`, `AudioConfig`, `AlphabetConfig`, etc.) backed by INI files. `SettingsManager` routes get/set to the correct domain. `AppSettingsManager` handles pre-project settings from a JSON file.
- **`io_put/`** — File I/O: `lift.py` (LIFT XML), `xlp.py` (XLingPaper), `export.py`, `sound.py` (audio I/O), `cawl.py` (SILCAWL loader).
- **`utilities/`** — Pure utilities (`utilities.py` has moved-from-main helpers), logging setup, file ops, HTML helpers, regex, executables detection, `i18n.py` (translation), `error_handler.py` (backend-safe error notification).
- **`translations/`** — gettext `.po`/`.mo` files for i18n.

### Key Patterns

- **`program` dict**: Created at `main.py:9`, threaded through most classes as `self.program`. Contains runtime config, flags (`nosound`, `testing`, `production`), and references to major objects.
- **`from utilities.utilities import *`**: main.py wildcard-imports all pure utility functions.
- **Sound is optional**: `pyaudio`/sound imports are wrapped in try/except; `program['nosound']` gates audio features.
- **i18n**: All modules use `from utilities.i18n import _`. The translator is swapped at runtime via `set_translator()` in `App.interfacelang()`.

## Active Refactoring (settings_rebuild branch)

The `settings_rebuild` branch has extracted frontend/backend separation from the original monolithic `main.py` (was ~5242 lines, now ~764). The `LazyGlobal` pattern has been fully eliminated. **All backend modules have zero frontend imports** — every `from frontend import` has been removed from `backend/`. Four presenters handle UI delegation:

- `frontend/sort_ui.py` (`SortPresenter`) — sorting_engine.py widget creation
- `frontend/lexicon_ui.py` (`LexiconPresenter`) — lexicon.py and alphabet.py widget creation
- `frontend/vcs_ui.py` (`VCSPresenter`) — vcs.py commit/wait dialogs
- `frontend/report_ui.py` (`ReportPresenter`) — generator.py result frames

All backend UI method calls (withdraw, deiconify, getrunwindow, exitFlag, wait*, etc.) route through `self.ui.X()` — currently `self.ui = self` (set in Task.__init__), preparing for a future Task/TaskWindow split. See `UIvTasks.md` for the full plan (Phase 8B pending).

## Build Notes

- Python 3.13 from a custom build (`~/IT/Python-3.13.7`), used via the `env/` virtualenv.
- PyTorch is CPU-only (`torch==2.7.1+cpu` via `--extra-index-url`).
- PyAudio requires system `portaudio` headers (`sudo apt install portaudio19-dev`).
