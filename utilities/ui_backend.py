# coding=UTF-8
"""Which UI backend runs — decided ONCE, here.

WHY THIS IS NOT IN `frontend/`: two places need the answer, and one of them
needs it *before* `frontend` may be imported. `main.py` sets
`program['tkinter']` and installs the Tk error catcher before
`from frontend import ui`, and importing anything from the `frontend`
package runs its `__init__`, which imports a backend — so the selector
cannot live there without inverting that order.

WHY IT EXISTS AT ALL: main.py used to read AZT_UI_BACKEND itself while
`frontend/__init__` read it separately. Two readers of one variable agree
only while neither can refuse. As soon as the frontend gained a fallback —
refusing a backend that cannot open a window — they disagreed, and the app
took the webview startup path against a tkinter root:

    TypeError: Misc.mainloop() got an unexpected keyword argument
               'setup_callback'

So the rule is: ask `chosen()`, never the environment.
"""
import importlib.util
import os
import platform
import sys

from utilities import logsetup

log = logsetup.getlog(__name__)

_chosen = None
_warned = False


def _importable(name):
    """Is *name* importable, without actually importing it? find_spec keeps
    this cheap — `gi` in particular drags in a lot."""
    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, ValueError):
        return False


def _venv_sees_system_site():
    """Can this interpreter see apt-installed packages? None if not in a
    venv at all, else what pyvenv.cfg says."""
    if sys.prefix == sys.base_prefix:
        return None
    try:
        with open(os.path.join(sys.prefix, 'pyvenv.cfg')) as fh:
            for line in fh:
                if line.strip().lower().startswith(
                        'include-system-site-packages'):
                    return line.split('=', 1)[1].strip().lower() == 'true'
    except OSError:
        pass
    return False


# Which host module each engine needs, for the LINUX engines only. Duplicated
# rather than imported from frontend.ui_webview on purpose: importing anything
# from `frontend` runs its __init__, which imports a backend — the very thing
# this module exists to decide. Keep in step with ui_webview.ENGINES.
_ENGINE_HOSTS = {'gtk': 'gi', 'qt': 'qtpy'}
_KNOWN_ENGINES = ('gtk', 'qt', 'cef', 'edgechromium', 'mshtml')


def requested_engine():
    """The engine named on the command line or in PYWEBVIEW_GUI, or None.

    Mirrors frontend.ui_webview._engine's first two steps. Only the EXPLICIT
    request is of interest here — a default we pick ourselves is chosen from
    what is installed, so it cannot be missing."""
    for arg in sys.argv:
        if arg.startswith('--engine='):
            return arg.split('=', 1)[1].strip().lower() or None
    return (os.environ.get('PYWEBVIEW_GUI') or '').strip().lower() or None


def engine_problem():
    """Why the EXPLICITLY REQUESTED engine cannot run, or None.

    Two gaps this closes, both found by Kent asking whether case 1 had a
    fallback (2026-09-08). It did not:

    1. `--engine=` was passed to pywebview unvalidated, so a typo
       (`--engine=gkt`) went straight through and failed obscurely.
    2. Nothing checked that the requested engine's host was installed —
       `webview_problem()` asks only whether EITHER host is importable, so
       `--engine=qt` on a GTK-only machine passed the backend check and then
       raised inside webview.start().

    This function only NAMES the problem. What to do about it belongs to the
    caller: `frontend.ui_webview._engine()` reports it and then substitutes
    the platform default, because asking for Qt and silently getting GTK
    would make the measured engine differences impossible to reason about,
    while refusing outright would drop to tkinter over a missing engine —
    a much larger substitution than the other engine."""
    engine = requested_engine()
    if not engine:
        return None
    if engine not in _KNOWN_ENGINES:
        return ("unknown webview engine {!r} (known: {})"
                "".format(engine, ', '.join(_KNOWN_ENGINES)))
    host = _ENGINE_HOSTS.get(engine)
    if host and platform.system() == 'Linux' and not _importable(host):
        return ("webview engine {!r} was requested but its host module {!r} "
                "is not importable in {}".format(engine, host, sys.executable))
    return None


def webview_problem():
    """Why the webview backend cannot run in THIS interpreter, or None.

    Two separate requirements, and the second is the one that bites on
    Linux: pywebview is pure Python and installs from pip, but it is only a
    WRAPPER — it still needs a native host (GTK/WebKit2 or Qt/QtWebEngine),
    and without one `webview.start()` raises WebViewException at the moment
    a window would have appeared.

    Checking here turns that into a fallback instead of a blank screen.
    Importing `frontend.ui_webview` SUCCEEDS without pywebview — it sets
    `webview = None`, logs an error and carries on — so the app used to
    start with a backend that could never open a window, and with no
    VisibilityWatchdog running to notice.

    THE MESSAGE NAMES WHAT IS ACTUALLY WRONG HERE, which the first version
    did not: it printed a generic apt+pip recipe, and Kent (2026-09-04)
    reasonably followed it — installing GTK typelibs into a venv that could
    never import `gi` no matter what apt did. A recipe that cannot work on
    the machine reading it is worse than no advice."""
    where = "this interpreter ({})".format(sys.executable)
    if not _importable('webview'):
        return "pywebview is not installed in {} — pip install pywebview" \
               "".format(where)
    # A MISSING *ENGINE* IS NOT A MISSING BACKEND. If `--engine=qt` cannot
    # run but GTK can, dropping all the way to tkinter would be a far larger
    # substitution than using the other engine — so that case is handled in
    # frontend.ui_webview._engine(), which REPORTS the problem and then
    # substitutes (Kent, 2026-09-08: "we could report then substitute").
    # Only "no host at all" blocks the backend, below.
    if platform.system() != 'Linux':
        return None
    if _importable('gi') or _importable('qtpy'):
        return None

    # Neither host is importable. Say which door is shut, not both recipes.
    sees_system = _venv_sees_system_site()
    if sees_system is False:
        return ("pywebview has no host toolkit, and {} is a venv built "
                "WITHOUT --system-site-packages, so it can never import `gi` "
                "however many apt packages are installed — GTK is not "
                "reachable from here at all. Either `pip install "
                "\"pywebview[qt]\"` into this venv (pure pip, no apt, no "
                "rebuild), or recreate the venv with --system-site-packages"
                "".format(where))
    return ("pywebview has no host toolkit for {}. Qt: `pip install "
            "\"pywebview[qt]\"` (pure pip, no apt). GTK: pywebview's gtk "
            "platform requires Gtk 3.0, WebKit2 4.1 (or 4.0) and Soup 3.0 "
            "(or 2.4) — so `sudo apt install gir1.2-gtk-3.0 "
            "gir1.2-webkit2-4.1 gir1.2-soup-3.0`. NOTE it is GTK **3**: "
            "gir1.2-gtk-4.0 does nothing for it, and the WEBKIT typelib is "
            "the one usually missing, since GTK alone renders no web content"
            "".format(where))


def requested():
    """What backend was asked for, and how.

    Three ways in, most explicit first. The env var was the only one, which
    makes trying the webview awkward from a desktop launcher or an IDE run
    configuration — hence the flags. They are safe because main.py does not
    parse argv (it only logs it), so an unrecognised flag is ignored rather
    than rejected.

    A persisted setting is the obvious fourth and is deliberately NOT here:
    this is consulted before the settings system is up, so reaching into it
    would invert that dependency. When it is wanted, the place for it is a
    startup re-check in main.py."""
    for flag, name in (('--webview', 'webview'), ('--tkinter', 'tkinter')):
        if flag in sys.argv:
            return name
    name = os.environ.get('AZT_UI_BACKEND', '').lower()
    if name in ('tkinter', 'webview'):
        return name
    if name:
        log.warning("Unknown AZT_UI_BACKEND {!r}; using tkinter".format(name))
    return 'tkinter'


def chosen():
    """The backend that will actually run: 'tkinter' or 'webview'.

    Cached, and the refusal is announced once. Every caller must use this
    rather than reading the environment, or they will disagree with it."""
    global _chosen, _warned
    if _chosen is not None:
        return _chosen
    want = requested()
    if want == 'webview':
        problem = webview_problem()
        if problem is None:
            _chosen = 'webview'
            return _chosen
        if not _warned:
            _warned = True
            # Loud on both channels: the log is what the watchdogs and bug
            # reports are read from, and stderr is what a developer who just
            # asked for the webview is looking at.
            msg = ("The webview backend was requested but cannot run: {}. "
                   "Falling back to tkinter.".format(problem))
            log.warning(msg)
            sys.stderr.write(msg + "\n")
    _chosen = 'tkinter'
    return _chosen
