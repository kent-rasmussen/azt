# A-Z+T test suite

First automated tests for the desktop app (started 2026-06-06). The goal is to
**catch regressions before users do** — especially the kind this codebase is
prone to: import-time breakage from edits, and UI lifecycle bugs (the stuck
progress dialog that motivated this).

## Running

```bash
cd azt
source env/bin/activate
pip install -r requirements-dev.txt   # one-time: installs pytest
pytest                                 # run everything
pytest tests/test_waiting_contract.py  # one file
pytest -m "not integration"            # skip stubs that need fixtures/app
```

No display is required — tests import modules and exercise pure logic; none
create a Tk root. (Tests that would need a live display should be marked
`@pytest.mark.needs_display`.)

## What's here

| File | Layer | What it guards |
|---|---|---|
| `test_import_smoke.py` | guardrail | Every app module imports cleanly. Missing *optional* deps (pyaudio, torch, …) → **skip**; syntax/Name/real import errors → **fail**. Catches the "did my edit break import?" case. A handful of orphan/standalone modules that aren't part of the app's import graph are listed in `EXPECTED_NOT_IMPORTABLE` (skipped with reason) — see AUDIT_FINDINGS.md; remove from that list if you fix/wire one. |
| `test_waiting_contract.py` | guardrail | The `waiting()` context manager (v1.2.0) calls `waitdone()` on normal exit, on exception, and on early return — on each backend. Guards the stuck-dialog fix. |
| `test_settings_manager.py` | unit | `ConfigManager` JSON save/load round-trip; `CustomEncoder`/object-hook for `set`/`Path`; per-host filename scheme; setattr-persists behavior. |
| `test_utilities.py` | unit | Pure helpers (`ofromstr`, `grouptype`, `ifone`). |
| `test_backend_logic.py` | unit + TODO | Public-class API guards for `backend/core`; **skipped stubs** mapping the behavioral tests still to write (LIFT parse, profile analysis). |
| `test_status_dict.py` | unit | `StatusDict` (the sort/verify status model that sort & macrosort read/write): node creation, group list get/set + rename, verified(`done`) read/write incl. `update()`, per-check flags (`tosort`/`presorted`/`tojoin`), distinguish pairing, sense to-sort/sorted bookkeeping, `cull`/`clear_all_groups`. Uses a tiny fake `program`. |
| `test_categories_groups.py` | unit | `Categories.add_int_group` — next-numbered-group creation for regular sort (persists via `status`) and macrosort (appends to `alphabet.glyphs()`, no persist). |

## How to expand

- **Behavioral backend tests** are the biggest gap. Start with a tiny LIFT XML
  fixture in `tests/fixtures/` and assert `io_put.lift` parses it. Confirm the
  loader API in source first (don't assume) — see the `@pytest.mark.integration`
  stubs in `test_backend_logic.py`.
- **Sort / macrosort engine** (`sorting_engine.Sort.sort/verify/join`) is thin
  orchestration over `StatusDict` (now covered by `test_status_dict.py`) plus Tk
  UI — the *data* logic it drives is tested; the UI flow needs a constructed
  `program` + window harness to test end-to-end. `marksorted`/`to_distinguish`
  are mostly delegation/set-arithmetic and could be interaction-tested with a
  fake `status` if desired.
- **Keep backend tests frontend-free.** `backend/core/*` has zero frontend
  imports by design (see CLAUDE.md); tests for it shouldn't need tkinter.
- **For UI logic**, prefer testing the real method with a fake `self` (as
  `test_waiting_contract.py` does) over standing up a Tk root.

## Conventions

- `conftest.py` puts `azt/` on `sys.path` so `import backend…` works from anywhere.
- Mark anything needing data files or constructed app objects `@pytest.mark.integration`;
  mark anything needing a live display `@pytest.mark.needs_display`.
