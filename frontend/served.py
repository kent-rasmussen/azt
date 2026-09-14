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

SERVE_SWITCH = '--serve'

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


def wanted(page):
    """Is `page` named in `--serve=`? Never raises.

    `--serve=splash` or `--serve=splash,sort`. A switch, not an environment
    variable (standing rule 2026-09-08), and comma-separated so the eventual
    per-page setting has an obvious shape to mirror.
    """
    prefix = SERVE_SWITCH + '='
    for arg in sys.argv:
        if arg.startswith(prefix):
            names = [n.strip() for n in arg[len(prefix):].split(',')]
            return page in [n for n in names if n]
    return False


def available(page, backend):
    """Should `page` be served as a child, given the active backend?

    Separate from `wanted()` so the refusals are testable without argv, and
    so each is LOGGED rather than silently dropping a switch the user passed.
    """
    if not wanted(page):
        return False
    if backend == 'webview':
        log.info("%s=%s ignored: the whole app is already webview, so there "
                 "is no Tk host to serve a page from and nothing to fall "
                 "back to", SERVE_SWITCH, page)
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
                        self.page, getattr(self.proc, 'pid', None),
                        self.proc.poll())
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
