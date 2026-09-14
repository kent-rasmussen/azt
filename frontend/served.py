# coding=UTF-8
"""Serve ONE page as a webview child process, with Tk keeping the mainloop.

ADR 0004 **D7**: `webview.start()` and Tk's `mainloop()` both require the main
thread, so a mixed-backend page cannot run in-process. It runs as a child —
**view model in, result out** — and the parent keeps the mainloop, therefore
keeps `VisibilityWatchdog`/`QuitOnlyGuard`, and can time out, kill, and
re-render the page in Tk.

**THE FALLBACK IS THE POINT.** Kent, 2026-09-14: "I don't want to break large
parts of AZT until such a time we everyting is fully tested and debugged on
webview." So this module's contract is that a child which does not come up,
or dies, or wedges, costs nothing but a log line: the caller gets None and
builds its Tk page as before.

**MIXED IS THE DEFAULT; THE TWO PURE MODES ARE THE OPT-INS.** Kent,
2026-09-14: "no, this mixed mode is now default. the other two are opt in" —
and, the same day, "keep --tkinter (i.e., only) and --webview (i.e., only)
fully functional thorughout."

    python main.py              # Tk host, webview children for SERVED_PAGES
    python main.py --tkinter    # Tk only. Serves nothing.
    python main.py --webview    # webview only, in-process. Serves nothing.

So `--tkinter` now carries a second meaning — "and no children" — which is
the meaning Kent was already using it with. Neither pure mode gains a code
path from this module: `available()` answers False for both, for reasons it
logs.

`SERVED_PAGES` is the registry, and it grows one page at a time as each is
ported and verified. A page not in it renders in Tk in every mode, which is
what makes the default safe to ship before the port is finished.

## Why readiness is waited for SYNCHRONOUSLY

The obvious design is to poll for the child with `after()` and carry on. It
cannot work here, and the reason is today's other lesson: **`after()` does not
fire while the main thread is busy.** `main.py` calls `splash.draw()` and then
runs the whole of boot — FileParser, repocheck, Settings, the analyzers —
without returning to the mainloop. A deferred readiness check would therefore
resolve after the thing it was gating. Same trap as the 400 ms wait-dialog
delay, which produced a 35-second blank screen
(`agenda/wait_dialog_flicker.md`).

So `start()` blocks, ONCE, with a bounded timeout, and says how long it took.
Everything after that is fire-and-forget.
"""
import json
import subprocess
import sys
import threading
import time
from pathlib import Path

from utilities import logsetup
log = logsetup.getlog(__name__)
logsetup.setlevel('INFO', log)

#: Pages that have a verified webview child. THE ONLY GATE ON THE DEFAULT
#: MODE: a page named here is served; a page not named here renders in Tk,
#: in every mode. Add a page only once it has been seen working, so the
#: default stays shippable while the port is unfinished.
SERVED_PAGES = frozenset({'splash'})

#: How long a child gets to report itself ready before we give up on it and
#: let the caller render in Tk. Generous, because it pays a Python start plus
#: a browser engine start, and paid only once per served page.
READY_TIMEOUT_S = 6.0

#: How long a child gets to exit politely before it is killed.
CLOSE_TIMEOUT_S = 2.0

# Protocol: ONE JSON OBJECT PER LINE, in both directions.
#
# Line-delimited JSON rather than pickle (a child must never execute parent
# objects) and rather than a length-prefixed frame (unreadable in a log, and
# the volume here is a handful of messages). Parent → child carries the view
# model and its updates; child → parent carries readiness and, later, results.
MSG_VIEW = 'view'         # parent→child: the whole view model, once
MSG_UPDATE = 'update'     # parent→child: changed fields only
MSG_CLOSE = 'close'       # parent→child: shut down
MSG_READY = 'ready'       # child→parent: the page is rendered and visible
MSG_RESULT = 'result'     # child→parent: what the user did
MSG_LOG = 'log'           # child→parent: a line for the parent's log


def available(page, backend, requested=None):
    """Should `page` be served as a webview child?

    `backend` is the host's active backend (`frontend.backend`) and
    `requested` is what the user explicitly asked for
    (`utilities.ui_backend.requested()`, None when they asked for nothing).
    Both are passed in rather than read here: this is the decision the two
    pure modes turn off, so it has to be testable without argv, and each
    refusal is LOGGED rather than left to be inferred.
    """
    if page not in SERVED_PAGES:
        return False        # not ported yet; Tk renders it, quietly
    if backend == 'webview':
        log.info("not serving %s as a child: the whole app is already "
                 "webview, so there is no Tk host and nothing to fall back "
                 "to", page)
        return False
    if requested == 'tkinter':
        # "asked for" and not "--tkinter": AZT_UI_BACKEND=tkinter says the
        # same thing, and naming a switch the user may not have typed is how
        # the first version of this line misled Kent (2026-09-14).
        log.info("not serving %s as a child: tkinter only was asked for",
                 page)
        return False
    return True


class ServedPage:
    """A child process rendering one page. Never raises at the caller.

    Not a context manager: the splash outlives the function that creates it
    (it is held on `program.splash` for the whole of boot), so lifetime is
    the caller's, as it is for the Tk window this replaces.
    """

    def __init__(self, page, module, cwd=None):
        self.page = page
        self.module = module
        self.cwd = Path(cwd) if cwd else Path(__file__).resolve().parents[1]
        self.proc = None
        self._ready = threading.Event()
        self._broken = False        # say it once, not per message

    # ── lifecycle ────────────────────────────────────────────────────────

    def start(self, view, timeout=READY_TIMEOUT_S):
        """Launch the child and WAIT for it to report ready. True if it did.

        False means the caller must render in Tk — which is not an error path
        to be apologised for, it is the designed one.
        """
        argv = [sys.executable, '-m', self.module, '--webview']
        try:
            self.proc = subprocess.Popen(
                argv, cwd=str(self.cwd),
                stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True, bufsize=1)       # line buffered, both ways
        except Exception as e:
            log.warning("served %s: could not start %s (%r); rendering in "
                        "tkinter instead", self.page, self.module, e)
            return False
        threading.Thread(target=self._read_stdout, daemon=True).start()
        threading.Thread(target=self._read_stderr, daemon=True).start()
        if not self.send(MSG_VIEW, view=view):
            self.close()
            return False
        t0 = time.perf_counter()
        got = self._ready.wait(timeout)
        waited = time.perf_counter() - t0
        if not got:
            log.warning("served %s: no 'ready' in %.1fs (pid %s, exit %s); "
                        "killing it and rendering in tkinter instead",
                        self.page, timeout,
                        getattr(self.proc, 'pid', None), self.proc.poll())
            self.close()
            return False
        log.info("served %s: ready in %.1fs (pid %s)",
                 self.page, waited, self.proc.pid)
        return True

    @property
    def alive(self):
        return bool(self.proc) and self.proc.poll() is None

    def close(self):
        """Ask, then insist. Never raises."""
        if not self.proc:
            return
        self.send(MSG_CLOSE)
        try:
            self.proc.wait(CLOSE_TIMEOUT_S)
        except Exception:
            log.info("served %s: did not exit in %.0fs; killing",
                     self.page, CLOSE_TIMEOUT_S)
            for step in (self.proc.terminate, self.proc.kill):
                try:
                    step()
                    self.proc.wait(CLOSE_TIMEOUT_S)
                    break
                except Exception:
                    continue
        self.proc = None

    # ── messages ─────────────────────────────────────────────────────────

    def send(self, kind, **fields):
        """One JSON line to the child. False if the pipe is gone.

        A dead pipe is NOT propagated: by the time a page is being updated,
        the caller has already committed to it, and a splash that stops
        animating must not take the boot down with it. Said once.
        """
        if not self.proc or not self.proc.stdin:
            return False
        try:
            self.proc.stdin.write(json.dumps(dict(kind=kind, **fields)) + '\n')
            self.proc.stdin.flush()
            return True
        except Exception as e:
            if not self._broken:
                self._broken = True
                log.warning("served %s: lost the pipe to the child (%r); "
                            "further updates are dropped", self.page, e)
            return False

    def _read_stdout(self):
        """Protocol lines. THREAD: touches no Tk and no caller state beyond
        an Event and the log — everything else would be a race."""
        try:
            for line in self.proc.stdout:
                line = line.strip()
                if not line:
                    continue
                try:
                    msg = json.loads(line)
                except Exception:
                    # Not protocol — a print() or a library's chatter. Worth
                    # seeing, not worth failing over.
                    log.info("served %s says: %s", self.page, line)
                    continue
                kind = msg.get('kind')
                if kind == MSG_READY:
                    self._ready.set()
                elif kind == MSG_LOG:
                    log.info("served %s: %s", self.page, msg.get('text', ''))
                elif kind == MSG_RESULT:
                    log.info("served %s result: %s", self.page,
                             msg.get('value'))
                else:
                    log.info("served %s sent an unknown message %r",
                             self.page, kind)
        except Exception as e:
            log.log(3, "served %s: stdout reader ended (%r)", self.page, e)

    def _read_stderr(self):
        """THE CHILD'S LOG MUST REACH THE PARENT'S LOG. ADR 0004 requires it
        — the watchdogs are read from that file — and relaying stderr is why
        the child needs no shared file handle and cannot interleave writes
        with us."""
        try:
            for line in self.proc.stderr:
                line = line.rstrip()
                if line:
                    log.info("[%s child] %s", self.page, line)
        except Exception as e:
            log.log(3, "served %s: stderr reader ended (%r)", self.page, e)


# ── the splash, the first page served ────────────────────────────────────

def splash_view(program):
    """The splash's view model: six strings, an image name and an integer.

    Kept HERE rather than in the child so parent and child share one
    vocabulary in one file, and so it can be unit-tested against a fake
    program with no display. Every value is plain data — this page has no
    live objects to hand over, which is why it was chosen first.

    Never raises: `source_repo` reads git, and a boot must not die because a
    date could not be formatted.
    """
    from utilities.i18n import _

    def safe(fn, default=''):
        try:
            return fn()
        except Exception as e:
            log.info("splash view model: %s", e)
            return default

    name = getattr(program, 'name', 'A-Z+T')
    repo = getattr(program, 'source_repo', None)
    return {
        'title': _("{azt} Dictionary and Orthography Checker").format(azt=name),
        'version': _("Version: {version}").format(
                        version=getattr(program, 'version', '?')),
        'updated': _("updated to {date} ({date_rel})").format(
                        date=safe(lambda: repo.lastcommitdate(), '?'),
                        date_rel=safe(lambda: repo.lastcommitdaterelative(),
                                      '?')),
        'loading': _("Your dictionary database is loading..."),
        'description': _("{azt} is a computer program that accelerates "
                "community-based language development by facilitating the "
                "sorting of a beginning dictionary by vowels, consonants and "
                "tone. (more in help:about)").format(azt=name),
        'image': 'transparent',
        'progress': 0,
    }


# ── the alphabet chart, the second page ──────────────────────────────────

def _plain(value, default=None):
    """A `ui.Variable`'s value, or the value itself. Never raises.

    The chart holds several settings as `ui.Variable`s — `save_settings`
    checks `isinstance(value, ui.Variable)` for exactly this reason — and a
    Variable cannot cross a pipe.
    """
    get = getattr(value, 'get', None)
    if callable(get):
        try:
            return get()
        except Exception as e:
            log.info("chart view model: could not read a variable (%s)", e)
            return default
    return value if value is not None else default


def chart_view(chart):
    """The alphabet chart as plain data: a title, a column count and cells.

    READ-ONLY, deliberately (step 3a). The real page is a CONFIGURATION page
    — draggable glyph order, per-group hide toggles, and `save_settings()`
    writing five settings back — and none of that can work until there is a
    child→parent result channel. So this proves the data shape and the
    images, which is the half that can be proved without one. The Tk page is
    untouched and `alphabet_chart` is deliberately NOT in `SERVED_PAGES`;
    serving a read-only chart would be a regression, not a port.

    WHY THIS PAGE. It is the one that takes 37-42 seconds to build under Tk
    while both webview engines draw the same content in ~0s
    (`agenda/wayland_freeze_audit.md`), so "does it appear fast" is a
    falsifiable win by eye rather than a matter of taste.

    Images cross as ABSOLUTE PATHS, not bitmaps. The Tk path attaches a
    scaled bitmap to the sense (`getimagelocationURI`, then `Image.compile`);
    a browser wants a source, and `_image_src` already accepts a string
    starting with '/' or 'file:' straight into an <img src>. So no HTTP route
    and no base64 is needed — which is the one thing Step 3 assumed would be
    necessary.

    Never raises: one unreadable sense must cost its own cell, not the page.
    """
    cells = []
    order = _plain(getattr(chart, 'order', None), []) or []
    exobjs = getattr(chart, 'exobjs', None) or {}
    for glyph in [str(g) for g in order]:
        sense = exobjs.get(glyph)
        word, image = '', None
        if sense is not None:
            try:
                word = sense.entry.lcvalue()
            except Exception as e:
                log.info("chart view model: no word for %r (%s)", glyph, e)
            try:
                image = sense.illustrationURI_or_default()
            except Exception as e:
                log.info("chart view model: no image for %r (%s)", glyph, e)
        cells.append({'glyph': glyph, 'word': word or '', 'image': image})
    return {
        'title': _plain(getattr(chart, 'chart_title', None), '') or '',
        'ncolumns': _sane_columns(_plain(getattr(chart, 'ncolumns', None), 5)),
        'copyright': _plain(getattr(chart, 'copyright', None), '') or '',
        'cells': cells,
    }


def _sane_columns(value, default=5):
    """A column count must be a positive int — the chart grids on
    `n // ncolumns`, and `AlphabetChartData._sane_columns` exists because a
    string ("using_helvetica") once got stored and killed every redraw. Same
    hazard on this side of the pipe."""
    try:
        n = int(value)
    except (TypeError, ValueError):
        return default
    return n if n > 0 else default


class ServedSplash:
    """A splash living in a child process, wearing `Splash`'s surface.

    `splash` is touched in ~15 places across `main.py`, `tasks/chooser.py`
    and `frontend/ui_shell.py` — draw, progress, withdraw, destroy,
    maketexts, exitFlag, winfo_exists. `_NoSplash` already proved a null
    object is the right seam for that; this is the same trick with a process
    behind it, so **no call site changes** and `--tkinter` keeps the code
    path it has today.

    ONE BEHAVIOUR IS LOST, and it should be recorded rather than discovered:
    `exitFlag.istrue()` is how the user cancels during boot
    (`tasks/chooser.py:493,549`). A served splash has no child→parent channel
    yet, so cancelling from it is unavailable and the flag always reads
    False — never True, because "the user asked to quit" must not be invented
    from a page that cannot ask. `_NoSplash` accepts the same loss under
    `--no-splash`.
    """

    class _Flag:
        def istrue(self):
            return False

        def true(self):
            pass

        def false(self):
            pass

    def __init__(self, page):
        self.exitFlag = self._Flag()
        self._page = page

    def draw(self):
        pass        # already visible: `ready` means the page is on screen

    def progress(self, value):
        self._page.send(MSG_UPDATE, fields={'progress': value})

    def maketexts(self):
        pass        # the texts went over in the view model

    def winfo_exists(self):
        return self._page.alive

    def withdraw(self):
        self._page.close()

    def destroy(self):
        self._page.close()

    def deiconify(self):
        pass

    def __getattr__(self, name):
        """Swallow the rest of the splash API, as `_NoSplash` does — and SAY
        SO, because a call nobody noticed is how a page silently loses a
        feature (the `ContextMenu` lesson, 2026-09-11)."""
        log.info("served splash: ignoring %s()", name)
        return lambda *a, **k: None


def splash(program, backend, requested=None):
    """A `ServedSplash`, or None if the caller should build the Tk `Splash`.

    None is the ordinary path until this is verified, and it is not an error:
    every refusal is logged by `available()` or by `start()`.
    """
    if not available('splash', backend, requested):
        return None
    page = ServedPage('splash', 'frontend.served_splash')
    if not page.start(splash_view(program)):
        return None
    return ServedSplash(page)
