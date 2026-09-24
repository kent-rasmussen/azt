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

# (what the user asked for, why it could not be honoured) — main.py's
# warn_backend_problems() shows these once the UI is live, the same way
# py_modules.BOOTSTRAP_PROBLEMS and sound.SOUND_PROBLEMS are shown.
#
# WHY A LIST RATHER THAN A RETURN VALUE: the refusal is decided during
# `import main`, long before there is a window to put it in, and the only
# record used to be a log line. A switch the user typed was declined and the
# evidence scrolled past among a hundred other lines, so a whole session could
# be spent believing the webview backend was under test while looking at
# tkinter (Kent, 2026-09-11). Recording it here lets the decision stay in one
# place and still be announced where it will be seen.
BACKEND_PROBLEMS = []


def _importable(name):
    """Is *name* a REAL, importable package? find_spec keeps this cheap —
    `gi` in particular drags in a lot.

    A NAMESPACE PACKAGE DOES NOT COUNT, and that is not pedantry: `pip
    uninstall PyQt6` leaves an empty `PyQt6/` directory behind, which
    `find_spec` happily reports as a namespace package with no origin. A
    leftover directory would then read as "a Qt binding is installed" and the
    backend would commit to an engine that cannot load (seen on Kent's venv
    2026-09-23, right after uninstalling the Qt stack). Requiring an origin
    distinguishes a package from the hole where one used to be."""
    try:
        spec = importlib.util.find_spec(name)
    except (ImportError, ValueError):
        return False
    return spec is not None and spec.origin not in (None, 'namespace')


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
    return _engine_request()[0]


def _engine_request():
    """`(engine, how it was asked for)`, or `(None, None)`. One scan, for the
    same reason as `_request()`."""
    for arg in sys.argv:
        if arg.startswith('--engine='):
            return arg.split('=', 1)[1].strip().lower() or None, arg
    engine = (os.environ.get('PYWEBVIEW_GUI') or '').strip().lower()
    if engine:
        return engine, 'PYWEBVIEW_GUI={}'.format(engine)
    return None, None


def engine_request_source():
    """How the ENGINE was asked for, in the user's own terms — `--engine=qt`
    or `PYWEBVIEW_GUI=qt`. Same rule as `request_source()`: never name a
    switch the user did not type. PYWEBVIEW_GUI is pywebview's own variable,
    honoured deliberately, so it is a real way in and must be reportable."""
    return _engine_request()[1]


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
    # ASK THE SAME QUESTION THE BACKEND CHECK ASKS. This used to test only
    # `_importable(host)` — so `--engine=gtk` passed on a machine with
    # PyGObject but no WebKit2 typelib, and `--engine=qt` passed on one with
    # `qtpy` and no binding behind it. Both are the false positives
    # `gtk_host_problem`/`qt_host_problem` exist to remove, and an engine
    # check that disagrees with the backend check is two answers to one
    # question, which is the fault this module was written to prevent.
    if platform.system() == 'Linux':
        problem = {'gtk': gtk_host_problem,
                   'qt': qt_host_problem}.get(engine, lambda: None)()
        if problem:
            return ("webview engine {!r} was requested but cannot run here: "
                    "{}".format(engine, problem))
    return None


def _base_python():
    """The interpreter this venv was built FROM, or None if not in a venv."""
    if sys.prefix == sys.base_prefix:
        return None
    for sub in ('bin', 'Scripts', ''):
        for name in ('python3', 'python', 'python.exe', 'python3.exe'):
            path = os.path.join(sys.base_prefix, sub, name)
            if os.path.isfile(path) and os.access(path, os.X_OK):
                return path
    return None


def importable_in_base(module):
    """Is `module` importable by the BASE interpreter? True / False / None.

    SEEING AROUND `include-system-site-packages` (Kent, 2026-09-23: "Can we
    not see around that setting? Is there no way to know if ONLY that setting
    is the problem?"). We can, and hedging was the tool declining work it is
    able to do. Whether apt installed `gi`, and whether THIS interpreter is
    permitted to look at it, are separate facts — and the second hides the
    first. So ask the interpreter that is allowed to see it.

    THE BASE PYTHON, not `/usr/bin/python3`: `sys.base_prefix` names the
    installation this venv was made from, which is exactly the one whose
    site-packages the flag exposes. A guessed path would be wrong on pyenv or
    a custom build, and Debian's `dist-packages` is not reachable by path
    arithmetic anyway.

    None means the question could not be asked, which stays distinct from a
    confident No."""
    py = _base_python()
    if not py:
        return None
    import subprocess
    code = ('import importlib.util as u, sys;'
            's = u.find_spec({!r});'
            'sys.exit(0 if s and s.origin else 1)'.format(module))
    try:
        done = subprocess.run([py, '-c', code], capture_output=True,
                              timeout=30)
    except Exception as e:
        log.info("could not ask %s about %s: %s", py, module, e)
        return None
    return done.returncode == 0


_gtk_checked = None


def gtk_host_problem():
    """Why GTK cannot render here, or None. Cached; Linux only.

    `gi` IMPORTING IS NOT ENOUGH, and this is the gap between what we could
    already see and what actually breaks (Kent, 2026-09-23: "We can already
    tell if any of the system packages are missing, right?"). Two of the
    three things were already answerable — `_importable('gi')` says whether
    the bindings are reachable, and `_venv_sees_system_site()` reads
    `pyvenv.cfg` for whether this venv may see them at all. The third was
    not: the bindings and the TYPELIBS are separate apt packages.

    So `python3-gi` alone gives an importable `gi` and no way to render a web
    page, because `gir1.2-webkit2-4.1` is a different package — and
    `azt/CLAUDE.md` already says it is the one usually missing, "since GTK
    alone renders no web content". Until now `webview_problem()` accepted an
    importable `gi` as proof of a host, so that machine passed the backend
    check and failed later, inside `webview.start()`, which is the exact
    shape of fault this whole item exists to remove.

    `gi.require_version` is the test because it is the call pywebview itself
    makes: it consults the typelib repository and raises without loading the
    library. Both WebKit2 spellings are tried, matching
    `webview/platforms/gtk.py`."""
    global _gtk_checked
    if _gtk_checked is not None:
        return _gtk_checked
    if platform.system() != 'Linux':
        # NOT A FAULT ANYWHERE ELSE. macOS renders through Cocoa and Windows
        # through WebView2, so GTK is simply not the road there — and every
        # caller already guards on Linux. Said plainly because the manual
        # host check prints this line on every platform, and "PyGObject is
        # not importable" on a Mac reads as a problem when it is an
        # irrelevance.
        _gtk_checked = ("not applicable on {} — GTK is the Linux host; this "
                        "platform renders through its own"
                        "".format(platform.system()))
        return _gtk_checked
    if not _importable('gi'):
        # "NOT IMPORTABLE HERE", NEVER "NOT INSTALLED" (Kent, 2026-09-23,
        # reading a diagnostic that said the latter: "the second NOT INSTALLED
        # isn't true, but I see why we'd think that"). `gi` is apt's and lives
        # in the system's dist-packages; whether THIS interpreter can see it
        # is a separate fact, decided by one line of pyvenv.cfg. Conflating
        # the two is what sent him installing typelibs into a venv that could
        # never read them (2026-09-04) — so when the venv is the reason, say
        # so instead of implying the package is absent.
        if _venv_sees_system_site() is False:
            # DON'T HEDGE — ASK. The base interpreter can see what this one
            # is forbidden to, so say which of the two situations it is.
            in_base = importable_in_base('gi')
            cfg = os.path.join(sys.prefix, 'pyvenv.cfg')
            if in_base is True:
                _gtk_checked = (
                    "PyGObject (`gi`) IS installed — {} can import it — but "
                    "this venv cannot, because {} says "
                    "include-system-site-packages = false. NOTHING NEEDS "
                    "INSTALLING: set that to true, or rebuild the venv with "
                    "--system-site-packages".format(_base_python(), cfg))
            elif in_base is False:
                _gtk_checked = (
                    "PyGObject (`gi`) is installed nowhere this machine can "
                    "reach — not in the venv and not in the base python. It "
                    "needs BOTH `sudo apt install python3-gi` and "
                    "include-system-site-packages = true in {}, since apt "
                    "installs it where this venv is currently forbidden to "
                    "look".format(cfg))
            else:
                _gtk_checked = (
                    "PyGObject (`gi`) is not importable from {}, and the base "
                    "interpreter could not be asked whether it has one. This "
                    "venv excludes system packages ({}), which is the usual "
                    "reason".format(sys.executable, cfg))
        else:
            _gtk_checked = ("PyGObject (`gi`) is not importable from {} — "
                            "`sudo apt install python3-gi`"
                            "".format(sys.executable))
        return _gtk_checked
    missing = []
    try:
        import gi
        for name, versions in (('Gtk', ('3.0',)),
                               ('WebKit2', ('4.1', '4.0')),
                               ('Soup', ('3.0', '2.4'))):
            for version in versions:
                try:
                    gi.require_version(name, version)
                    break
                except (ValueError, AttributeError):
                    continue
            else:
                missing.append('{} ({})'.format(name, ' or '.join(versions)))
    except Exception as e:                      # importing gi can fail oddly
        _gtk_checked = "PyGObject (`gi`) would not load: {}".format(e)
        return _gtk_checked
    if missing:
        # RARE ON A DESKTOP, and the message should not imply otherwise.
        # Measured on Ubuntu 25.10 (2026-09-24): gir1.2-gtk-3.0,
        # gir1.2-soup-3.0 and gir1.2-webkit2-4.1 are all pulled in by
        # `ubuntu-desktop`, the last through update-manager and the release
        # upgrader. So reaching here means a minimal, server or non-Ubuntu
        # install — worth saying, because otherwise a desktop user reads an
        # apt line as something they were expected to have run.
        # NAME THE REQUIREMENT, NOT THE PACKAGE (Kent, 2026-09-24: "I'd rather
        # step away from ad hoc figuring out which specific package names are
        # required"). Package names differ per distribution and per release —
        # `gir1.2-webkit2-4.1` today, something else once the GTK4 generation
        # lands — so a name we print is a name that goes stale, and printing a
        # retired one is worse than printing none. A typelib namespace and
        # version is true everywhere and is what a package manager searches
        # on.
        #   It also matters less than it did: Qt is fetched automatically when
        # GTK cannot run, so nobody is being asked to install anything. This
        # is for the reader who WANTS GTK.
        _gtk_checked = ("`gi` works, but the GObject typelibs pywebview's GTK "
                        "backend needs are not installed here: {}. Those come "
                        "from the operating system rather than pip — your "
                        "package manager lists them as GObject introspection "
                        "data. A full desktop normally has them already"
                        "".format(', '.join(missing)))
    else:
        _gtk_checked = None
    return _gtk_checked


_qt_checked = None


def qt_host_problem():
    """Why Qt cannot render here, or None. Cached.

    THE SAME FALSE POSITIVE AS `gi`, ONE LAYER OVER. `qtpy` is a SHIM: it
    picks between PyQt5, PyQt6, PySide2 and PySide6 and raises at import if
    none is installed — so `find_spec('qtpy')` can succeed on a machine with
    no Qt at all. And a binding alone is not enough either, because
    pywebview's qt platform needs QtWebEngine, which several distributions
    package separately.

    Found by a controlled test (Kent, 2026-09-23): flipping
    `include-system-site-packages` showed `qtpy` present in the venv while
    nothing had checked whether anything sat underneath it. Accepting that as
    "Qt is available" is how a machine passes the backend check and fails at
    the window, which is the fault this module exists to prevent."""
    global _qt_checked
    if _qt_checked is not None:
        return _qt_checked
    if not _importable('qtpy'):
        _qt_checked = "`qtpy` is not importable"
        return _qt_checked
    bindings = [b for b in ('PyQt6', 'PyQt5', 'PySide6', 'PySide2')
                if _importable(b)]
    if not bindings:
        _qt_checked = ("`qtpy` is installed but no Qt binding is (PyQt6, "
                       "PyQt5, PySide6 or PySide2) — qtpy is only a shim over "
                       "them. `pip install \"pywebview[qt]\"` brings one")
        return _qt_checked
    for binding in bindings:
        try:
            if _importable('{}.QtWebEngineWidgets'.format(binding)):
                _qt_checked = None
                return _qt_checked
        except Exception:
            continue
    _qt_checked = ("{} is installed but QtWebEngine is not, and pywebview's "
                   "qt platform needs it to render anything. `pip install "
                   "\"pywebview[qt]\"`".format(', '.join(bindings)))
    return _qt_checked


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
    # A HOST IS A HOST ONLY IF IT CAN ACTUALLY RENDER. `gi` importing was
    # accepted as proof until 2026-09-23; it is not, because the typelibs are
    # separate packages. See `gtk_host_problem`.
    gtk = gtk_host_problem()
    qt = qt_host_problem()
    if gtk is None or qt is None:
        return None
    if _importable('gi'):
        # The bindings are here and the typelibs are not, so neither the
        # venv-visibility message nor the generic apt recipe below fits: this
        # machine needs ONE more apt package, and `gtk` names it.
        return "{} — or `pip install \"pywebview[qt]\"` to use Qt instead " \
               "(pure pip, no apt)".format(gtk)

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


_REQUEST_FLAGS = (('--webview', 'webview'), ('--tkinter', 'tkinter'))


def _request():
    """`(backend, how it was asked for)`, or `(None, None)`.

    ONE scan behind both `explicit()` and `request_source()`. Two readers of
    one question is the exact fault this module exists to prevent (see the
    module docstring), and "which backend" and "how did they say so" are the
    same question read twice."""
    for flag, name in _REQUEST_FLAGS:
        if flag in sys.argv:
            return name, flag
    name = os.environ.get('AZT_UI_BACKEND', '').lower()
    if name in ('tkinter', 'webview'):
        return name, 'AZT_UI_BACKEND={}'.format(name)
    return None, None


def request_source():
    """How the backend was asked for, in the user's own terms — the switch
    they typed or the variable they set — or None if nobody asked.

    A REFUSAL MUST NOT NAME A SWITCH THE USER DID NOT TYPE.
    `AZT_UI_BACKEND=webview` asks for the webview as plainly as `--webview`
    does, so a message hardcoding the switch sends someone hunting through a
    command line that has no such flag on it. That is the mirror image of the
    2026-09-14 fault which put `explicit()` here in the first place: a log
    line blaming a switch Kent had not typed."""
    return _request()[1]


def explicit():
    """The backend the user ACTUALLY asked for, or **None** if they did not.

    Separate from `requested()` because that one DEFAULTS to 'tkinter', so it
    cannot answer "did anyone ask?" — and that is the question mixed mode
    turns on. Mixed (a Tk host serving webview pages) is the default from
    2026-09-14; `--tkinter` and `--webview` are the pure opt-ins. Asking
    `requested()` made an empty command line look like `--tkinter` and
    refused to serve anything, with a log line blaming a switch Kent had not
    typed.

    Three ways in, most explicit first. The env var was the only one, which
    makes trying the webview awkward from a desktop launcher or an IDE run
    configuration — hence the flags. They are safe because main.py does not
    parse argv (it only logs it), so an unrecognised flag is ignored rather
    than rejected.

    `--no-install` turns off the "ask for it, get it" behaviour in `chosen()`
    for a run that must not touch the network or the venv.

    A persisted setting is the obvious fourth and is deliberately NOT here:
    this is consulted before the settings system is up, so reaching into it
    would invert that dependency. When it is wanted, the place for it is a
    startup re-check in main.py.
    """
    return _request()[0]


def requested():
    """What backend to use, defaulting to tkinter. See `explicit()` for the
    "was one asked for at all" question, which this cannot answer."""
    name = explicit()
    if name:
        return name
    raw = os.environ.get('AZT_UI_BACKEND', '').lower()
    if raw:
        log.warning("Unknown AZT_UI_BACKEND {!r}; using tkinter".format(raw))
    return 'tkinter'


_QT_DESKTOPS = ('kde', 'plasma', 'lxqt', 'razor')
_GTK_DESKTOPS = ('gnome', 'ubuntu', 'xfce', 'xubuntu', 'mate', 'cinnamon',
                 'x-cinnamon', 'budgie', 'pantheon', 'lxde', 'unity',
                 'deepin')


def native_toolkit():
    """'qt', 'gtk', or None — which toolkit THIS DESKTOP is built on.

    NOT WHICH ONE IS INSTALLED; which one the user's desktop already looks
    like. Kent, 2026-09-24: *"it would be nice if we could tell which toolkit
    their OS uses natively, in cases where people just put --webview, which
    may become our new default."*

    It matters in two places, and the second is the one that decides
    something. Given a free choice of engine, matching the desktop means
    native-looking decorations, file dialogs and menus — a Qt window on KDE,
    a GTK one on GNOME or XFCE. And when NEITHER host is available and no
    engine was named, this names WHICH TOOLKIT TO FIX — not whether to give up
    (Kent, 2026-09-24: "this decides which to FIX, not to give up or not").
    Fixing is the normal case, and most gaps are ours to close: pywebview
    itself is pip's, `pywebview[qt]` is pip's, and this venv's own
    `include-system-site-packages` is a file we own.

    EXACTLY ONE GAP IS NOT OURS: GTK's GObject typelibs are system packages
    and installing them needs root. That is a hard limit on this route, not a
    judgement about whether to bother — and it is the only one. When it is
    hit, the answer is still a webview: Qt is installed instead, because a
    webview is what was asked for and the engine was not named. The notice
    says the desktop's native toolkit was GTK, that its system packages were
    absent, and that Qt was fetched in its place.

    `XDG_CURRENT_DESKTOP` is a colon-separated LIST ("ubuntu:GNOME"), which is
    why this scans rather than compares. `KDE_FULL_SESSION` is checked too
    because some KDE sessions set only that."""
    if platform.system() != 'Linux':
        return None
    if os.environ.get('KDE_FULL_SESSION'):
        return 'qt'
    names = []
    for var in ('XDG_CURRENT_DESKTOP', 'XDG_SESSION_DESKTOP',
                'DESKTOP_SESSION'):
        names.extend((os.environ.get(var) or '').lower().split(':'))
    for name in names:
        name = name.strip()
        if not name:
            continue
        if any(k in name for k in _QT_DESKTOPS):
            return 'qt'
        if any(k in name for k in _GTK_DESKTOPS):
            return 'gtk'
    return None


def pip_fix_for():
    """What to `pip install` so this machine can honour what was asked — or
    None when pip is not the answer.

    THE WHOLE QUESTION FOR AUTO-INSTALL, and it is answerable (Kent,
    2026-09-23: "any reason we can't just do this for the user, then?").
    `agenda/webview_requested_but_absent.md` argued against installing
    because on Linux pywebview ALSO needs a host toolkit pip cannot supply.
    That is true only when the host is missing TOO — and we can see whether
    it is. So:

      * pywebview present            → not the problem; nothing to install.
      * not Linux                    → yes. macOS uses Cocoa and Windows uses
                                       the in-box WebView2 runtime, so there
                                       is no host for pip to be unable to
                                       supply.
      * Linux with `gi` or `qtpy`    → yes. The host is already there; the
                                       python package is the only gap.
      * Linux with neither           → NO. Installing would produce a
                                       different failure one step later,
                                       which is worse than the honest refusal
                                       — and the fix is apt, which is not
                                       ours to run (see
                                       `requirements-webview.txt`).

    AND THE ENGINE, WHICH IS A SEPARATE CASE (Kent, 2026-09-23: "similarly,
    --webview --engine=qt should call pip install pywebview[qt] if not
    there"). A missing engine host does NOT fail `chosen()` — `gi` being
    present means the backend runs, and `ui_webview._engine()` quietly
    substitutes GTK for the Qt that was asked for. So `--engine=qt` on a
    GTK-only machine reaches a working webview that is not the one under
    test. Qt is the one host pip CAN supply end to end, wheels only, no apt
    and no compiler, so an explicit `--engine=qt` earns the install.

    `--engine=gtk` never does: PyGObject is apt's, per the rule in
    `requirements-webview.txt`. And when NO engine was named and no host
    exists, this declines too — Qt is ~100 MB and substituting an engine
    nobody chose, over a field connection, is not "doing as asked". The
    refusal message already names the command for someone who wants it.
    """
    engine = requested_engine()
    linux = platform.system() == 'Linux'
    missing_pkg = not _importable('webview')
    if not linux:
        return 'pywebview' if missing_pkg else None
    if engine == 'qt' and qt_host_problem():
        return 'pywebview[qt]'      # also brings pywebview itself
    if engine == 'gtk' and gtk_host_problem():
        return None                 # apt's to fix; pip must not try
    if gtk_host_problem() is None or qt_host_problem() is None:
        return 'pywebview' if missing_pkg else None
    # NO HOST AT ALL, AND NO ENGINE NAMED — the Xubuntu/Kubuntu case.
    #
    # THE RULE IS: FIX THE DESKTOP'S OWN TOOLKIT (Kent, 2026-09-24: "on a Qt
    # machine, if there's a qt thing missing, let's fix that"). Work through
    # the native one first and only move on when its gap is one we cannot
    # close.
    #
    #   Qt desktop, Qt missing      → `pywebview[qt]`. Native AND ours: pure
    #                                 wheels, no root. Fixed.
    #   GTK desktop, venv hiding it → already repaired and restarted above,
    #                                 so we never reach here for that cause.
    #   GTK desktop, typelibs gone  → the ONLY gap that needs root. Cannot
    #                                 fix the native toolkit; Qt is still a
    #                                 webview, and a webview is what was
    #                                 asked for, so fetch that instead.
    #
    # Both surviving branches want `pywebview[qt]`, so this is one line rather
    # than a fork — but the reasoning is the fork, and it is where a
    # root-install route for the typelibs would slot in if one is ever added,
    # because that would let the GTK desktop keep GTK.
    if not engine:
        return 'pywebview[qt]'
    return None


_REPAIRED = 'AZT_VENV_VISIBILITY_REPAIRED'


def _repair_venv_visibility():
    """Set `include-system-site-packages = true` in this venv. True if written.

    ON DEMAND, NEVER AT CREATION (Kent, 2026-09-24: "setting this globally is
    not a good idea, even on linux. for someone using qt, that's also all
    risk, no reward"). Exactly so — the flag's cost is that the venv stops
    being a guarantee: a package missing from it silently resolves to the
    system's at whatever version the distro ships, which is how apt's
    pywebview 5.0.5 stood in for the pinned 6.2.1. That cost is worth paying
    ONLY by someone who is about to use GTK, and only when it is the one
    thing in their way. A Qt user on the same machine gets nothing for it.

    So this runs when all three hold: a host is unavailable here, the venv
    excludes system packages, and the BASE python demonstrably has `gi`. The
    third is what makes it a repair rather than a guess — see
    `importable_in_base`."""
    cfg = os.path.join(sys.prefix, 'pyvenv.cfg')
    try:
        with open(cfg) as fh:
            lines = fh.readlines()
    except OSError as e:
        log.info("cannot read %s (%s); leaving the venv alone", cfg, e)
        return False
    out, found = [], False
    for line in lines:
        if line.strip().lower().startswith('include-system-site-packages'):
            out.append('include-system-site-packages = true\n')
            found = True
        else:
            out.append(line)
    if not found:
        out.append('include-system-site-packages = true\n')
    try:
        with open(cfg, 'w') as fh:
            fh.writelines(out)
    except OSError as e:
        log.error("could not write %s (%s); GTK stays unavailable", cfg, e)
        BACKEND_PROBLEMS.append((cfg, "this venv hides the system's PyGObject "
                                      "and could not be corrected: {}"
                                      "".format(e)))
        return False
    log.warning("%s: include-system-site-packages = true — the system's "
                "PyGObject is now reachable. Restarting to pick it up.", cfg)
    return True


def _relaunch():
    """Replace this process with the same command line. Does not return.

    `os.execv`, NOT Popen-and-exit. The macOS venv relaunch used the latter
    and did not survive a Terminal launcher: the parent exits, the shell
    session ends under it, and the orphan is SIGHUPed before it prints
    anything (`installfiles/RunMetoInstall_Mac.command`, section 4b). execv
    replaces the image, so there is no parent to exit and no orphan.

    The guard is an environment variable rather than a switch, matching
    `py_modules.ensure_venv`'s `AZT_VENV_RELAUNCHED`: it is a one-shot
    internal marker, not a way for anyone to change behaviour, and it must
    make a second attempt impossible even if the repair silently failed."""
    os.environ[_REPAIRED] = '1'
    argv = [sys.executable] + sys.argv
    log.warning("restarting: %s", ' '.join(argv))
    try:
        os.execv(sys.executable, argv)
    except Exception as e:                  # pragma: no cover - platform
        log.error("could not restart (%s); continuing without the repair", e)
        return False


def _may_install():
    """Is installing allowed in this run at all?

    NEVER UNDER PYTEST, and that is not a nicety. `chosen()` is called by
    `tests/test_ui_backend_request.py` with argv set to `--webview`; on a
    machine where pywebview is missing and a host is present — which is the
    normal state while working on this — the suite would shell out to pip and
    mutate the developer's venv. A test that installs software is not a test.

    `--no-install` is the switch for a run that must not touch the network or
    the venv (standing rule: switches, not environment variables)."""
    if '--no-install' in sys.argv:
        return False
    try:
        if logsetup.under_pytest():
            return False
    except Exception:
        pass
    return True


def _install(requirement):
    """Install `requirement` into THIS interpreter. True if webview now imports.

    NEVER `pywebview[gtk]` — see `pip_fix_for`. That extra asks pip for
    PyGObject, the one thing that must come from apt; it would either fail to
    build or shadow the system `gi` the venv is configured to see. The rule
    and its reasons are in `requirements-webview.txt`.

    NO RESTART IS NEEDED, which is what makes this worth doing at all. This
    runs from `chosen()`, which `main.py` calls at line 112 — BEFORE `from
    frontend import ui` at line 152, so nothing has imported a backend yet.
    Install, invalidate the import caches so the new package is visible, and
    the same run continues into the backend that was asked for."""
    import subprocess
    # FAIL FAST WITH NO NETWORK, BUT DON'T ABANDON A SLOW ONE. Kent's
    # condition on the whole feature, 2026-09-23: "Don't die on no internet,
    # of course." `--retries 1 --timeout 15` bounds CONNECTION attempts, so
    # an unreachable index gives up in seconds instead of grinding through
    # pip's five retries with exponential backoff. It does NOT bound a
    # download that is merely slow, which is the field case worth waiting
    # for — that is what the generous subprocess timeout is for.
    cmd = [sys.executable, '-m', 'pip', 'install',
           '--retries', '1', '--timeout', '15', requirement]
    log.warning("Installing %s, because the webview backend is in use here "
                "and pip can supply it: %s", requirement, ' '.join(cmd))
    try:
        done = subprocess.run(cmd, capture_output=True, text=True,
                              timeout=600)
    except subprocess.TimeoutExpired:
        log.error("Gave up installing %s after 10 minutes; carrying on "
                  "without it.", requirement)
        return False
    except Exception as e:
        # NEVER RAISES. This runs during `import main`, before any window
        # exists, so anything escaping here is a startup crash with no screen
        # to explain it — the same rule `ensure_venv` follows.
        log.error("Could not run pip to install %s (%s); carrying on without "
                  "it.", requirement, e)
        return False
    if done.returncode != 0:
        tail = [l for l in (done.stderr or '').splitlines() if l.strip()][-4:]
        log.error("pip could not install %s:\n%s", requirement,
                  '\n'.join(tail))
        BACKEND_PROBLEMS.append((requirement,
                                 "tried to install it and pip refused; see "
                                 "the log"))
        return False
    importlib.invalidate_caches()
    log.warning("%s installed.", requirement)
    return _importable('webview')


def chosen():
    """The backend that will actually run: 'tkinter' or 'webview'.

    Cached, and the refusal is announced once. Every caller must use this
    rather than reading the environment, or they will disagree with it."""
    global _chosen, _warned
    if _chosen is not None:
        return _chosen
    want = requested()
    if want == 'webview':
        # ASKED FOR IT? THEN TRY TO GET IT, then fall back in order (Kent,
        # 2026-09-23: "if qt is requested, try to get. if we fail, *then*
        # fall back to gtk (or then) tkinter"). That chain falls out of the
        # pieces rather than being coded as a ladder:
        #   1. `pip_fix_for()` names what pip could supply — `pywebview[qt]`
        #      for an explicit --engine=qt, plain `pywebview` when only the
        #      package is missing, and NOTHING when the gap is apt's.
        #   2. `webview_problem()` then decides backend or tkinter, against
        #      whatever is true AFTER the attempt.
        #   3. `ui_webview._engine()` does the qt→gtk step, reporting the
        #      substitution rather than making it silently.
        # So a failed Qt install lands on GTK if GTK can render, and on
        # tkinter if it cannot, with each step named in the notice.
        # DELIBERATELY `requested()`, WHICH INCLUDES THE DEFAULT — do not
        # "fix" this to `explicit()`. Asked whether a future default flip
        # should carry everyone or only people who typed the switch, Kent,
        # 2026-09-23: *"that's what I want. I don't want to wait for each user
        # to ask explicitly; when we change the default, everyone should
        # change. Don't die on no internet, of course."* And on "one machine
        # at a time as they ask": *"which they WON'T, is the point."*
        #
        # THAT IS THE PRINCIPLE, not a preference about this feature: a user
        # will not opt in, so anything we want them to have has to arrive by
        # default and the software has to do the work. The same sentence
        # governs python upgrades in ADR 0005 D4 — nobody installs a new
        # interpreter voluntarily either. An opt-in is a decision not to ship
        # the thing.
        #
        # So the day webview becomes the default (ADR 0004 A4), every install
        # picks it up on its next start. The no-internet clause is the only
        # constraint, and it is why `_install` fails fast and never raises.
        # FIRST, THE ONE FIX THAT IS NOT AN INSTALL. If the only thing
        # hiding a host is this venv's own config, correct it and restart —
        # before deciding what to install, because after the flip `gi` is
        # visible and the right answer changes. Guarded so it can happen at
        # most once per launch.
        # REPAIR GTK WHENEVER GTK IS WANTED, not only when nothing else works.
        # This used to require `qt_host_problem()` too — i.e. it fired only if
        # NO host was available — so on a machine with Qt installed,
        # `--engine=gtk` quietly got Qt instead while GTK sat one line of
        # pyvenv.cfg away (Kent's run, 2026-09-24). Naming an engine is asking
        # for that engine; an installed alternative is not a reason to stop
        # trying to honour it.
        #   AND WITH NO ENGINE NAMED EITHER, when the desktop's OWN toolkit is
        # the one being hidden (Kent, same run: "but also NOT asking for an
        # engine, when your native OS toolkit is a boolean away"). A GNOME or
        # XFCE user who types only `--webview` should get GTK, not whichever
        # host happens to be installed — his run produced "webview on qt" on a
        # GNOME desktop, which is the app looking like a visitor for want of
        # one line of config.
        #
        # So "wanted" is one of three:
        #   * asked for by name;
        #   * nothing named, and this desktop is GTK-native;
        #   * nothing named, the desktop is unrecognised, and Qt cannot run
        #     either — so GTK is the only route to a webview at all.
        # An explicit --engine=qt is left alone, and so is an unrecognised
        # desktop where Qt already works: flipping the flag has a real cost
        # (the venv stops being a guarantee) and there is no reason to pay it
        # for a toolkit nobody asked for or needs.
        _native = native_toolkit()
        _wants_gtk = (requested_engine() == 'gtk'
                      or (not requested_engine()
                          and (_native == 'gtk'
                               or (_native is None and qt_host_problem()))))
        if (_may_install() and not os.environ.get(_REPAIRED)
                and _wants_gtk and gtk_host_problem()
                and _venv_sees_system_site() is False
                and importable_in_base('gi') is True):
            if _repair_venv_visibility():
                _relaunch()                 # replaces this process
        if _may_install():
            need = pip_fix_for()
            if need:
                installed = _install(need)
                # SAY SO WHEN THE DESKTOP AND THE ENGINE DISAGREE. Fetching Qt
                # onto a GTK desktop is the right call — the webview was asked
                # for and Qt is the only host pip can deliver — but it is a
                # ~100 MB download and the windows will not match the rest of
                # the desktop, so it must not happen quietly (Kent,
                # 2026-09-24: "minimally we want to complain loudly in such a
                # context. UserNotice. And probably Qt, given that webviews is
                # already turned on at that point"). Nothing recorded this
                # before, so the notice never fired for the one case that most
                # needs it.
                if (installed and need == 'pywebview[qt]'
                        and not requested_engine()
                        and native_toolkit() == 'gtk'):
                    BACKEND_PROBLEMS.append((
                        request_source() or '--webview',
                        "this is a GTK desktop, but GTK's GObject typelibs "
                        "are not installed, so Qt was downloaded and used "
                        "instead, which took a large download. NOTHING NEEDS "
                        "DOING: everything works, but the windows will look "
                        "different from the rest of your desktop. If that "
                        "matters, tell whoever supports this computer — the "
                        "log says exactly what was missing"))
        problem = webview_problem()
        if problem is None:
            _chosen = 'webview'
            return _chosen
        if not _warned:
            _warned = True
            # ONE CHANNEL, NOT TWO — and this printed the refusal TWICE until
            # 2026-09-22. The comment here used to claim the log and stderr
            # were separate audiences, but `logsetup` attaches a
            # StreamHandler(sys.__stderr__) to the ROOT logger at import, with
            # format '%(message)s' — so `log.warning(msg)` already puts this
            # exact text, bare, on the same stderr a `sys.stderr.write` would.
            # The duplicate read as "something decides this twice"; nothing
            # does — `_chosen`/`_warned` make the decision exactly once.
            log.warning("The webview backend was requested but cannot run: "
                        "%s. Falling back to tkinter.", problem)
            # Seen, not just logged: raised as a notice by main.py once a
            # window exists. See BACKEND_PROBLEMS above.
            BACKEND_PROBLEMS.append((request_source() or '--webview', problem))
    _chosen = 'tkinter'
    return _chosen
