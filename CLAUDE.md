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

### LazyGlobal Pattern (critical to understand)

Most extracted modules use a **two-part lazy import** pattern to break circular dependencies with `main.py`:

1. A module-level `__getattr__(name)` that imports `main` on first access from outside the module.
2. A `LazyGlobal(name)` sentinel (defined in `utilities/utilities.py`) injected into `globals()` for internal name lookup.

Both parts list the same set of names. `__getattr__` handles cross-module attribute resolution; `LazyGlobal` handles within-module name resolution before class definitions run. **`LazyGlobal` cannot be used as a base class** (no `__mro_entries__`).

When moving code between modules, both tuples must be kept in sync, and any name used at class-definition time (e.g., in a base class list or decorator) must be available via a real import, not LazyGlobal.

### Module Layout

- **`main.py`** (~764 lines) — App class, startup, `program` dict (global config), remaining orchestration functions (`updateazt`, `loadCAWL`, image utils, `propagate`). The `program` dict is the central config object passed everywhere.
- **`frontend/ui_shell.py`** (~4068 lines) — All tkinter UI: menus, status frames, task UI dressing, button frames, image frames, splash, error notices, result windows, LiftChooser.
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
- **`io_put/`** — File I/O: `lift.py` (LIFT XML), `xlp.py` (XLingPaper), `export.py`, `sound.py` (audio I/O).
- **`utilities/`** — Pure utilities (`utilities.py` has moved-from-main helpers), logging setup, file ops, HTML helpers, regex, executables detection.
- **`translations/`** — gettext `.po`/`.mo` files for i18n.

### Key Patterns

- **`program` dict**: Created at `main.py:9`, threaded through most classes as `self.program`. Contains runtime config, flags (`nosound`, `testing`, `production`), and references to major objects.
- **`from utilities.utilities import *`**: main.py wildcard-imports all pure utility functions. Other modules access these via LazyGlobal or explicit import.
- **Sound is optional**: `pyaudio`/sound imports are wrapped in try/except; `program['nosound']` gates audio features.
- **i18n via gettext**: `_()` is defined globally in main.py and as a fallback in modules that may load before translation is configured.

## Active Refactoring (settings_rebuild branch)

The `settings_rebuild` branch is extracting frontend/backend separation from the original monolithic `main.py` (was ~5242 lines, now ~764). Classes are being moved to `frontend/`, `backend/`, `tasks/`, and `settings/` with LazyGlobal bridging circular dependencies. See MEMORY.md for detailed tracking of what has moved where.

## Build Notes

- Python 3.13 from a custom build (`~/IT/Python-3.13.7`), used via the `env/` virtualenv.
- PyTorch is CPU-only (`torch==2.7.1+cpu` via `--extra-index-url`).
- PyAudio requires system `portaudio` headers (`sudo apt install portaudio19-dev`).
