#!/usr/bin/env python3
# coding=UTF-8
"""Can the webview backend actually run here, and if not, exactly what is missing?

    python tests/manual/webview_host/check_hosts.py

READ-ONLY. It never installs anything and never calls `ui_backend.chosen()`,
which would (see `chosen`'s auto-install). It reports what that function WOULD
decide, and what it would install first.

WHY THIS EXISTS AS A SCRIPT. The question "is pywebview installed?" has at
least five answers that look alike from a distance, and telling them apart by
hand took most of a day (2026-09-22/23):

  1. The python package is absent from this interpreter.
  2. It is present, but from the SYSTEM rather than the venv — a different
     version than the project pins, silently substituted.
  3. `gi` imports, so a host looks present, but the GObject TYPELIBS are not
     installed and nothing can render. Separate apt packages.
  4. `gi` does not import, but it IS installed — the venv was built without
     `--system-site-packages`, so apt's copy is invisible to it. "Not
     importable here" is not "not installed", and confusing the two is what
     sent typelibs into a venv that could never read them (2026-09-04).
  5. `qtpy` is importable, but it is only a SHIM over PyQt/PySide, and
     pywebview's qt platform additionally needs QtWebEngine.

So this asks both interpreters, separates installed-here from installed-at-all,
and uses the app's own host checks rather than a second opinion that could
drift from them.
"""
import argparse
import importlib.util
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# Everything that decides whether a webview can be drawn.
#
# `cairo` IS A GUESS, SO IT IS LABELLED AS ONE (Kent, 2026-09-23: "are we
# using cairo?"). Nothing in A-Z+T imports it and it is in no requirements
# file — it appears in this repo only here. It is listed because
# `python3-gi-cairo` is in the documented apt set for GTK (CLAUDE.md,
# requirements-webview.txt) and PyGObject's Gtk overrides are believed to use
# pycairo, so its absence would surface as a confusing `gi` error rather than
# a cairo one. UNVERIFIED: nobody has tested whether pywebview's GTK path
# actually needs it. It costs one line of output; drop it from this tuple if
# a GTK webview is ever seen working without it.
MODULES = ('webview', 'gi', 'cairo', 'qtpy',
           'PyQt6', 'PyQt5', 'PySide6', 'PySide2')

PROBE = ('import importlib.util as u;'
         '[print("%s\\t%s" % (m, (lambda s: (s.origin or "namespace pkg")'
         ' if s else "-")(u.find_spec(m)))) for m in ({!r})]')


def resolve_with(python, modules):
    """`{module: path or '-'}` as seen by `python`, or None if it won't run."""
    code = PROBE.format(tuple(modules))
    try:
        done = subprocess.run([python, '-c', code], capture_output=True,
                              text=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return None
    if done.returncode != 0:
        return None
    out = {}
    for line in done.stdout.splitlines():
        if '\t' in line:
            name, path = line.split('\t', 1)
            out[name] = path
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(
        description='Report what the webview backend can and cannot use '
                    'here. Changes nothing.')
    ap.add_argument('--system-python', default=None, metavar='PATH',
                    help='the interpreter to compare against, so '
                         '"installed but invisible here" is distinguishable '
                         'from "not installed". Defaults to the BASE python '
                         'this venv was built from — which is the one '
                         'include-system-site-packages would expose, and '
                         'therefore the one whose answer decides whether '
                         'flipping that flag would help')
    ap.add_argument('--as', dest='simulate', metavar='"SWITCHES"',
                    help='predict for ANOTHER command line rather than this '
                         'one, e.g. --as "--webview --engine=qt". Without it '
                         'the prediction describes the switches you typed '
                         'here, which are never the ones you want to know '
                         'about')
    ap.add_argument('--pip-list', action='store_true',
                    help='also list what pip put in THIS venv (--local, so '
                         'system packages are excluded)')
    args = ap.parse_args(argv)

    from utilities import ui_backend as b

    print('INTERPRETER')
    print('   running:   {}'.format(sys.executable))
    print('   in a venv: {}'.format(sys.prefix != sys.base_prefix))
    sees = b._venv_sees_system_site()
    print('   venv sees system site-packages: {}'.format(
        'not in a venv' if sees is None else sees))
    if sees is False:
        print('      ^ so anything apt installed is INVISIBLE here, however '
              'much of it is present.')

    # COMPARE AGAINST THE SAME INTERPRETER THE VERDICT IS ABOUT. Defaulting
    # this to /usr/bin/python3 let the table and the GTK verdict disagree:
    # the table would show `gi` present while the verdict spoke about the
    # BASE python, which on a custom-built or pyenv python is a different
    # installation with different site-packages. Kent spotted the result —
    # a table answering the question that the advice below it told him to go
    # and answer (2026-09-23).
    other = args.system_python or b._base_python() or '/usr/bin/python3'
    here = {m: (lambda s: (s.origin or 'namespace pkg') if s else '-')(
        importlib.util.find_spec(m) if _safe(m) else None) for m in MODULES}
    there = resolve_with(other, MODULES)

    print('\nWHERE EACH PACKAGE RESOLVES')
    print('   compared against: {}'.format(other))
    print('   {:<10}{:<44}{}'.format('module', 'this interpreter',
                                     'base/system python'))
    print('   ' + '-' * 74)
    for name in MODULES:
        mine = here.get(name, '-')
        theirs = '(that interpreter did not run)' if there is None \
            else there.get(name, '-')
        mine = _short(mine)
        print('   {:<10}{:<44}{}'.format(name, mine, _short(theirs)))
    print('\n   "-" means NOT IMPORTABLE by that interpreter. A dash on the '
          'left with a\n   path on the right means installed, but not '
          'reachable from here.')

    print('\nCAN IT RENDER?  (the app\'s own checks, not a second opinion)')
    gtk = b.gtk_host_problem()
    print('   GTK: {}'.format(gtk or 'OK — bindings and typelibs both present'))
    qt = b.qt_host_problem()
    print('   Qt:  {}'.format(qt or 'OK — a binding and QtWebEngine present'))

    print('\nIF YOU ASK FOR IT, WHAT HAPPENS  (nothing below is done)')
    requests = ([args.simulate] if args.simulate else
                ['--webview', '--webview --engine=gtk',
                 '--webview --engine=qt'])
    fmt = '   {:<26}{:<18}{}'
    print(fmt.format('you ask for', 'it installs', 'and you get'))
    print('   ' + '-' * 72)
    for switches in requests:
        install, outcome = predict(b, switches)
        print(fmt.format(switches, install or '—', outcome))
    print('\n   Installing is suppressed by --no-install, and never happens '
          'under pytest.')

    if args.pip_list:
        print('\nIN THIS VENV, per pip (--local excludes system packages)')
        try:
            done = subprocess.run(
                [sys.executable, '-m', 'pip', 'list', '--local'],
                capture_output=True, text=True, timeout=120)
            for line in done.stdout.splitlines():
                if any(k in line.lower() for k in
                       ('qt', 'pyside', 'shiboken', 'webview', 'gobject',
                        'cairo')):
                    print('   ' + line)
        except (OSError, subprocess.SubprocessError) as e:
            print('   could not run pip: {}'.format(e))
    return 0


def predict(b, switches):
    """`(what pip would install, what you would end up looking at)`.

    MIRRORS `ui_backend.chosen()` AND `ui_webview._engine()`, and has to be
    kept in step with them. It cannot call them: `chosen()` would install,
    and `_engine()` lives in the frontend package, importing which imports a
    backend. So this reproduces the shape — try to get what was asked for,
    then fall back in order — which is small enough to mirror honestly and
    is the thing worth showing.

    The install is SIMULATED, not done: after a successful `pywebview[qt]`
    the Qt host is present by definition, and after `pywebview` the package
    is. That is why the outcome column can differ from the state above it."""
    saved = sys.argv
    import shlex
    sys.argv = ['main.py'] + shlex.split(switches)
    try:
        engine = b.requested_engine()
        gtk_ok = b.gtk_host_problem() is None
        qt_ok = b.qt_host_problem() is None
        have_pkg = b._importable('webview')

        # STEP 1: THE VENV REPAIR, which is not an install and happens first.
        # Missing it made this table say "tkinter — no host at all" for a
        # machine that would in fact fix itself and come up on GTK (Kent,
        # 2026-09-24: "So this is stale?"). It fires only when no host is
        # usable here, the venv excludes system packages, and the base python
        # demonstrably has `gi`.
        native = b.native_toolkit()
        wants_gtk = (engine == 'gtk'
                     or (not engine
                         and (native == 'gtk'
                              or (native is None and not qt_ok))))
        repaired = (wants_gtk and not gtk_ok
                    and b._venv_sees_system_site() is False
                    and b.importable_in_base('gi') is True)
        if repaired:
            gtk_ok = True

        # STEP 2: what pip would then be asked for. Mirrors `pip_fix_for`
        # against the post-repair state rather than calling it, since it
        # reads the real one.
        if engine == 'qt' and not qt_ok:
            need = 'pywebview[qt]'
        elif engine == 'gtk' and not gtk_ok:
            need = None                     # apt's to fix, never pip's
        elif not have_pkg and (gtk_ok or qt_ok or not _is_linux()):
            need = 'pywebview'
        else:
            need = None

        # STEP 3: what the install changes, and nothing more.
        if need == 'pywebview[qt]':
            qt_ok, have_pkg = True, True
        elif need == 'pywebview':
            have_pkg = True

        after = ' (after fixing the venv and restarting)' if repaired else ''
        if not gtk_ok and not qt_ok:
            # SAY WHICH IT IS. "pip cannot fix it" was wrong here and read as
            # a contradiction of the auto-install that had just been seen
            # working (Kent, 2026-09-23: "huh? we just talked about that").
            # Pip CAN fix this, by installing Qt — the code declines to,
            # because pulling ~100 MB and substituting an engine nobody asked
            # for is not "doing as asked". That is a policy, not a
            # limitation, and the two must not read alike.
            return need, ('tkinter — no host at all; ask --engine=qt and pip '
                          'will supply one')
        if not have_pkg:
            return need, 'tkinter — pywebview absent'
        # Engine: what was asked, else the default order (gtk, then qt).
        if engine == 'gtk' and not gtk_ok:
            got = 'qt' if qt_ok else None
        elif engine == 'qt' and not qt_ok:
            got = 'gtk' if gtk_ok else None
        elif engine in ('gtk', 'qt'):
            got = engine
        else:
            got = 'gtk' if gtk_ok else 'qt'
        if got is None:
            return need, 'tkinter — no engine available'
        if engine and got != engine:
            return need, 'webview on {}, NOT the {} you asked for{}'.format(
                got, engine, after)
        return need, 'webview on {}{}'.format(got, after)
    finally:
        sys.argv = saved


def _is_linux():
    import platform
    return platform.system() == 'Linux'


def _safe(name):
    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, ValueError):
        return False


def _short(path, width=42):
    """Keep the meaningful end of a long path."""
    home = os.path.expanduser('~')
    if path.startswith(home):
        path = '~' + path[len(home):]
    return path if len(path) <= width else '…' + path[-(width - 1):]


if __name__ == '__main__':
    sys.exit(main())
