#!/usr/bin/env python3
# coding=UTF-8
"""What python am I, where is A-Z+T's, and what can each of them import?

RUN IT WITH ANYTHING. No packages, no virtual environment, no `-um`, no
working directory to get right — standard library only, and it never imports
anything from the app:

    python tests/manual/sound_check/where_am_i.py

WHY IT EXISTS. Every other script here needs numpy and sounddevice, which is
exactly what is missing when things will not start — so the diagnostics were
unavailable precisely when they were needed. Kent, on a Windows and a macOS
machine (2026-09-10): "I can't even get it to run." Fair: the tools assumed
the environment they were supposed to be diagnosing.

WHAT IT TELLS YOU
    which interpreter you just used, and whether it is a virtual environment;
    where A-Z+T's own interpreter is, if it can be found;
    what each of them can import of the packages the app needs;
    and the exact commands for this machine.

It does not change anything.
"""
import os
import platform
import subprocess
import sys
from pathlib import Path

NEEDED = ['numpy', 'sounddevice', 'soundfile', 'scipy', 'PIL', 'lxml',
          'psutil', 'torch', 'pytest', 'tkinter']

# Packages that are optional by design: the app runs without them and says so,
# rather than failing to start. Worth distinguishing so a missing one does not
# read as a broken install.
OPTIONAL = {'torch': 'transcription only', 'pytest': 'running the tests only'}


def app_dir():
    """The `azt` directory, from this file's location."""
    here = Path(__file__).resolve()
    return here.parents[3] if len(here.parents) > 3 else here.parent


def candidates():
    """Every place the venv interpreter might be, with whether it is there."""
    app = app_dir()
    out = []
    for base in (app.parent / 'env', app / 'env'):
        for sub, name in (('bin', 'python3'), ('bin', 'python'),
                          ('Scripts', 'python.exe'), ('Scripts', 'python')):
            path = base / sub / name
            out.append((path, path.exists()))
    return out


def imports_for(python):
    """Ask an interpreter what it can import. {name: None | 'error text'}."""
    probe = (
        'import importlib, json, sys\n'
        'names = {!r}\n'
        'out = {{}}\n'
        'for n in names:\n'
        '    try:\n'
        '        importlib.import_module(n)\n'
        '        out[n] = None\n'
        '    except Exception as e:\n'
        '        out[n] = "{{}}: {{}}".format(type(e).__name__, e)[:70]\n'
        'print(json.dumps(out))\n'
    ).format(NEEDED)
    try:
        done = subprocess.run([str(python), '-c', probe],
                              capture_output=True, text=True, timeout=120)
    except Exception as e:
        return {'(could not run it)': str(e)}
    if done.returncode != 0:
        return {'(it failed)': (done.stderr or '').strip()[:200]}
    try:
        import json
        return json.loads(done.stdout.strip().splitlines()[-1])
    except Exception as e:
        return {'(unreadable answer)': '{}: {}'.format(type(e).__name__, e)}


def show(title, results):
    print('  {}'.format(title))
    if not results:
        print('    (nothing to report)')
        return
    missing = []
    for name in sorted(results):
        why = results[name]
        if why is None:
            print('    ok      {}'.format(name))
        else:
            note = OPTIONAL.get(name)
            print('    MISSING {:<12} {}{}'.format(
                    name, why, '  [{}]'.format(note) if note else ''))
            if not note:
                missing.append(name)
    return missing


print('=' * 74)
print('Where am I? — A-Z+T audio environment check')
print('=' * 74)
print('machine: {} {} ({})'.format(platform.system(), platform.release(),
                                   platform.machine()))
print('app directory: {}'.format(app_dir()))
print()

in_venv = sys.prefix != getattr(sys, 'base_prefix', sys.prefix)
print('THE PYTHON YOU JUST USED')
print('  {}'.format(sys.executable))
print('  version {}'.format(platform.python_version()))
print('  virtual environment: {}'.format('yes' if in_venv else 'NO'))
print()
mine = imports_for(sys.executable)
missing_here = show('it can import:', mine)
print()

print("A-Z+T'S OWN PYTHON")
found = None
for path, exists in candidates():
    print('  {} {}'.format('FOUND  ' if exists else 'not here',
                            path))
    if exists and found is None:
        found = path
print()

if found is None:
    print('  No virtual environment was found in any of those places.')
    print('  That means A-Z+T has not been installed here, or it was')
    print('  installed somewhere else. Nothing below can be checked.')
    print()
    print('WHAT TO DO')
    print('  Run the installer for this platform, then try again. If A-Z+T')
    print('  DOES start on this machine, find out which python it uses and')
    print('  say where it is — the layout differs from what this looked for.')
else:
    theirs = imports_for(found)
    missing_there = show('it can import:', theirs)
    print()
    print('WHAT TO DO')
    if missing_there:
        print('  A-Z+T\'s own python is missing: {}'.format(
                ', '.join(missing_there)))
        print('  These are in requirements.txt, so the app installs them on')
        print('  first run. Either that has not happened yet or it failed.')
        print('  Start A-Z+T once and watch for a line saying')
        print('  "Requirements changed ... synchronizing python packages".')
        print('  If it is not there, or reports an error, THAT is the')
        print('  problem — not anything about the sound hardware.')
        print()
        print('  To install them by hand:')
        print('    {} -m pip install -r requirements.txt'.format(found))
    else:
        print('  A-Z+T\'s python has everything it needs.')
        if missing_here:
            print('  The python you used does NOT — so run the sound scripts')
            print('  with the app\'s one instead:')
        else:
            print('  Run the sound scripts with it:')
        print()
        print('    cd {}'.format(app_dir()))
        print('    {} -um tests.manual.sound_check.collect_audio_facts'
              .format(found))
        print('    {} -um tests.manual.sound_check.run_sound_check'
              .format(found))
        print()
        print('  And the automated tests (pytest is dev-only, so install it')
        print('  first if it is listed as missing above):')
        print('    {} -m pip install -r requirements-dev.txt'.format(found))
        print('    {} -m pytest -q'.format(found))
print('=' * 74)
