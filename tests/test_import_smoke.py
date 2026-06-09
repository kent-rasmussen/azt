"""Import-smoke test: every app module must import cleanly.

This is the cheapest, highest-value regression guard. It would have caught
the kind of breakage we worried about during the v1.2.0 dialog work — a
`SyntaxError` from a bad re-indent, a `NameError` like `_tkinter`, a missing
comma that makes a line a runtime error, etc. Each module is its own
parametrized case, so a failure names the exact module.

Policy:
- A module that fails to import because an *optional/heavy* dependency isn't
  installed (pyaudio, torch, …) is SKIPPED, not failed — that's an environment
  gap, not a code regression.
- Any other import error (SyntaxError, NameError, a real ImportError of a
  first-party module, an `exit()` at import time) is a FAILURE.
"""
import importlib
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent

# Top-level package dirs to sweep.
PACKAGES = ["backend", "frontend", "tasks", "utilities", "io_put", "settings"]

# Directories never worth importing.
EXCLUDE_DIRS = {
    "env", ".git", "__pycache__", "tests", ".buildozer", "bin", "audio",
    "images_CAWL", "azt_images", "logs",
}

# Files that aren't import-safe (run/exit at import, or scratch).
EXCLUDE_FILES = {"main.py", "test.py", "conftest.py", "setup.py"}

# Orphan/standalone modules that are NOT part of the app's import graph (grep
# confirms nothing imports them) and don't import cleanly as package modules.
# Skipped-with-reason rather than failed, so the suite is green but the issue
# stays visible. If you wire one of these into the app or fix its imports,
# remove it here so a future regression fails. See AUDIT_FINDINGS.md.
EXPECTED_NOT_IMPORTABLE = {
    "harmony_sync": "WIP/orphan: imports absent module `harmony_client`; not imported by the app",
    "praatfns": "standalone script: Python-2-style bare `import logsetup` (app uses utilities.logsetup); not imported by the app",
    "setdefaults": "standalone script: bare `import logsetup`; not imported by the app",
    "utilities.openclipart": "orphan: bare `import urls` (should be utilities.urls); not imported by the app",
}

# Third-party deps that may be absent in a lean/headless test env. A failure to
# import one of these is a skip, not a regression.
OPTIONAL_DEPS = {
    "pyaudio", "torch", "transformers", "webview", "pywebview", "numpy",
    "sounddevice", "samplerate", "soundfile", "parselmouth", "praatio",
    "huggingface_hub", "safetensors", "whisper", "faster_whisper",
    "allosaurus", "tgt", "pydub", "reportlab", "lxml", "polib", "psutil",
    "langcodes", "language_data", "PIL",
}


def _discover():
    mods = set()
    for pkg in PACKAGES:
        base = ROOT / pkg
        if not base.is_dir():
            continue
        for p in base.rglob("*.py"):
            rel = p.relative_to(ROOT)
            if any(part in EXCLUDE_DIRS for part in rel.parts):
                continue
            if p.name in EXCLUDE_FILES:
                continue
            parts = list(rel.with_suffix("").parts)
            if parts[-1] == "__init__":
                parts = parts[:-1]
            if parts:
                mods.add(".".join(parts))
    # top-level single-file modules (langtags, migration, duplicates, …)
    for p in ROOT.glob("*.py"):
        if p.name not in EXCLUDE_FILES:
            mods.add(p.stem)
    return sorted(mods)


@pytest.mark.parametrize("modname", _discover())
def test_module_imports(modname):
    if modname in EXPECTED_NOT_IMPORTABLE:
        pytest.skip(EXPECTED_NOT_IMPORTABLE[modname])
    try:
        importlib.import_module(modname)
    except ImportError as e:
        top = (getattr(e, "name", "") or "").split(".")[0]
        if top in OPTIONAL_DEPS:
            pytest.skip(f"optional dependency not installed: {e.name}")
        raise
    except SystemExit as e:  # a module that exit()s at import time
        pytest.fail(f"{modname} called exit()/sys.exit() at import: {e!r}")
