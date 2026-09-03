#!/usr/bin/env python3
# coding=UTF-8
"""A breadcrumb across a self-restart, so a restart that never lands says so.

AZT restarts itself — after an update, after `ensure_venv` re-execs, after a
collab reconnect — and until now a restart that did not come back produced NO
EVIDENCE AT ALL. That is the 2026-07-29 field report: the user was left with the
console, closing it lost everything, and the machine had to be restarted. Nothing
in the log named what had been attempted, because there was no process left to
write a line.

WHY A FILE AND NOT A WATCHDOG. `utilities.sysrestart` is `os.execl` on Linux —
the process image is REPLACED, so Python, Tk, the event loop and every pending
`after()` callback cease to exist inside that call — and on Windows it is
`Popen` then `sys.exit()`, where the predecessor exits as soon as the successor
is LAUNCHED without ever checking that it STARTED. So no in-process mechanism can
observe the gap; only something that outlives both processes can. A file does.

THE ONE RULE THAT MATTERS: report at startup, clear when the UI is actually up.
Clearing at startup would destroy the evidence in exactly the case we care about
— a successor that dies during its own boot — and would leave the next start with
nothing to report. So a marker survives until the app is genuinely usable, and a
successor that never gets there leaves it for the start after that.

This is level 1 of `azt/agenda/restart_recovery_handshake.md`: it makes the
failure NAMEABLE, not survivable. Level 2 (the predecessor holding a visible
"Restarting…" modal until the successor signals it is up) is what makes it
recoverable, and this marker is the obvious channel for that signal — the
successor deleting it IS "I am up".
"""
import datetime
import json
import os
import pathlib
import platform
import sys

from utilities import logsetup
log=logsetup.getlog(__name__)

MARKER='restart_in_progress.json'


def _path():
    """Marker location: the log directory. Already per-user writable, already
    where diagnostics live, and already what a diagnostics bundle would carry
    (see log_to_server_button). `file` is imported lazily, as logsetup does, to
    stay out of the circular import.

    FALLBACK, and it is the point rather than defensiveness: the venv relaunch
    (`py_modules.ensure_venv`) is a restart producer that runs at IMPORT time, in
    a process whose whole job is to get the dependencies `utilities.file` needs —
    so on a first boot that import can legitimately fail. The log directory is
    `<source root>/userlogs`, which is derivable from this file's own location
    with nothing but pathlib, so the earliest producer is not the one left
    unable to leave a breadcrumb."""
    try:
        from utilities import file as _file
        return _file.getlogdir().joinpath(MARKER)
    except Exception:
        d=pathlib.Path(__file__).resolve().parent.parent.joinpath('userlogs')
        d.mkdir(parents=True,exist_ok=True)
        return d.joinpath(MARKER)


def _version():
    """Best effort. main.py defines __version__ at module level and is
    __main__, so this avoids importing main from a utility."""
    return getattr(sys.modules.get('__main__'),'__version__',None)


def mark(reason=None):
    """Record that a restart is being attempted, RIGHT BEFORE attempting it.

    `reason` is the most valuable field: an update that fails to come back is a
    different diagnosis from a venv relaunch that does, so record which one was
    running rather than just that something was."""
    data={'pid':os.getpid(),
            'started':datetime.datetime.now(datetime.timezone.utc
                        ).replace(tzinfo=None).isoformat(),
            'reason':reason or 'unspecified',
            'version':_version(),
            'platform':platform.system(),
            'argv':list(sys.argv),
            }
    # SAY IT, don't leave it to be inferred (Kent 2026-09-03: "can we not
    # explicitly know when the restart is spawned by a test?"). The test suite
    # exercises mark/report/clear against the real marker path, so its markers
    # appear in the log alongside real ones — and if a test run is interrupted
    # before clear(), one is left behind and the next real start reports a
    # restart that never happened. That was diagnosable already (a test marker
    # has version None, since the tests don't set __version__) but only by
    # noticing an ABSENCE, which is the weakest kind of evidence.
    #   Only stamped when true, so a real marker is byte-for-byte what it was.
    if logsetup.under_pytest():
        data['test']=True
    try:
        p=_path()
        with open(p,'w',encoding='utf-8') as f:
            json.dump(data,f)
        log.info("restart marker written: %s",data)
    except Exception as e:
        # Never block a restart over a diagnostic. A missing marker costs us a
        # log line; a raise here costs the user their restart.
        log.info("could not write restart marker: %s",e)
        # None, not the data: a confirmed restart uses the marker's
        # DISAPPEARANCE as the successor's "I am up", so a caller has to be able
        # to tell that there is no marker to disappear. Reporting success here
        # would read as instant confirmation of a successor that has not started.
        return None
    return data


def pending():
    """The marker left by a predecessor, or None. Never raises: a corrupt or
    unreadable marker must not be able to stop the app from starting, which is
    the one thing this file exists to help with."""
    try:
        p=_path()
        if not p.exists():
            return None
        with open(p,'r',encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        log.info("unreadable restart marker (treating as present): %s",e)
        return {'reason':'unreadable marker','error':str(e)}


def launched_by_restart():
    """Was THIS process started by a hand-over, rather than by the user?

    Two producers, two signals, and MISSING THE SECOND WOULD CRY WOLF on every
    venv relaunch:
      - `sysrestart`/`spawn_successor` append `--restart` to the successor's
        argv, which is the signal `duplicates.running_file` already keys off.
      - `py_modules.ensure_venv` relaunches with `sys.argv` UNCHANGED — no
        `--restart` — and sets `AZT_VENV_RELAUNCHED` in the child's environment.
        So its successor would have looked hand-launched, and reported a
        perfectly good relaunch as a restart that never landed.

    `AZT_BOOTSTRAP_PARENT_PID` would be the more precise signal for the second,
    but `duplicates.running_file` POPS it at import time — long before this is
    asked — so it is gone by then. `AZT_VENV_RELAUNCHED` survives.
    """
    return ('--restart' in sys.argv
            or bool(os.environ.get('AZT_VENV_RELAUNCHED')))


def report():
    """Say, loudly, that a restart was attempted and never landed.

    THE DISCRIMINATION THAT MATTERS, and the first version got it wrong (Kent's
    log, 2026-09-01): a marker is present in the SUCCESSOR too, because the
    predecessor wrote it moments earlier and only a UI that comes up clears it.
    So a marker on its own means "a restart is in flight", not "a restart
    failed", and reporting it in the successor cried wolf on every single
    successful restart.

    The question is whether THIS process is the one that restart launched. If it
    is (`--restart`), the marker is ours and in flight — nothing to report, and
    the clear() at UI-up is what resolves it. If it is NOT, the user started
    this copy by hand while a marker was outstanding, which is exactly the field
    symptom: the restart chain died and the user had to launch it themselves.

    Deliberately does NOT clear either way. If this boot also fails, the marker
    must still be there for the next one."""
    data=pending()
    if data is None:
        return None
    if launched_by_restart():
        log.info("restart in progress; this process is its successor: %s",data)
        return None
    log.warning("RESTART DID NOT COMPLETE: a restart was attempted and never "
            "cleared its marker, and this copy was started by hand rather than "
            "by that restart — so it either failed to start or died before its "
            "UI came up. %s",data)
    return data


def clear():
    """Called when the UI is genuinely up — that, and nothing earlier, is what
    'the restart worked' means."""
    try:
        p=_path()
        if p.exists():
            p.unlink()
            log.info("restart marker cleared: UI is up")
    except Exception as e:
        log.info("could not clear restart marker: %s",e)
