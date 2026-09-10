# coding=UTF-8
"""Say which python to run these scripts with, on THIS machine.

WHY THIS EXISTS. Kent ran `python -um tests.manual.sound_check.mic_check` in
MINGW64 on a Windows box (2026-09-10) and got "needs numpy and sounddevice:
No module named 'numpy'" — twice, then started installing numpy into the
system python by hand. Nothing was wrong with the machine: A-Z+T's
dependencies live in its VENV, and the bare `python` on PATH is not it.

The old message named what was missing and not where it lives, and the one
script that did offer a path offered a POSIX one (`../env/bin/python`), which
is wrong on the platform where this is most likely to bite. These scripts are
meant to be handed to other people, so the failure has to end with a command
they can paste rather than a diagnosis they have to act on.
"""
import os
import sys
from pathlib import Path


def venv_python(start=None):
    """Path to the venv interpreter for this checkout, or None.

    Looks where the suite actually puts it: `AZT/env` beside the app
    directory (azt/CLAUDE.md is explicit that there is no `azt/env`), plus
    `azt/env` because installs on other machines have not always agreed, and
    both layouts' interpreter names.
    """
    here = Path(start or __file__).resolve()
    app = here.parents[3] if len(here.parents) > 3 else here.parent
    for base in (app.parent / 'env', app / 'env'):
        for sub, name in (('bin', 'python3'), ('bin', 'python'),
                          ('Scripts', 'python.exe'), ('Scripts', 'python')):
            candidate = base / sub / name
            if candidate.exists():
                return candidate
    return None


def in_the_venv():
    """Are we already running under a venv with the app's packages?"""
    return sys.prefix != getattr(sys, 'base_prefix', sys.prefix)


def how_to_run(module, missing=None):
    """The message to print when an import fails. Ends in a command."""
    lines = []
    if missing:
        lines.append("This needs {} and cannot run without it.".format(
                                                                    missing))
    found = venv_python()
    if found:
        # A relative path where that is short, since these are run from the
        # app directory; absolute otherwise, because a wrong relative path is
        # worse than a long correct one.
        try:
            shown = os.path.relpath(str(found))
            if shown.count('..') > 2:
                shown = str(found)
        except Exception:
            shown = str(found)
        lines.append("")
        lines.append("A-Z+T's packages live in its virtual environment, not "
                     "in the `python` on your PATH.")
        lines.append("Run it with that interpreter instead:")
        lines.append("")
        lines.append("    {} -um {}".format(shown, module))
        lines.append("")
        lines.append("(Do NOT `pip install` these into your system python: "
                     "the app will not use them there.)")
    else:
        lines.append("")
        lines.append("A-Z+T's packages live in its virtual environment, and "
                     "no environment was found next to this checkout "
                     "(looked for env/bin/python and env/Scripts/python.exe "
                     "beside and inside the app directory).")
        lines.append("Install A-Z+T first, or activate its environment, then "
                     "run:")
        lines.append("")
        lines.append("    python -um {}".format(module))
    return "\n".join(lines)
