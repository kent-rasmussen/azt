#!/usr/bin/env python3
# coding=UTF-8
"""file is imported lazily inside functions to avoid circular import."""
"""
from utilities import logsetup
log=logsetup.getlog(__name__)
logsetup.setlevel('INFO',log) #for this file
"""
import logging
import logging.handlers
import tarfile
import datetime
import lzma
import re
import pathlib
import os
import sys
loglevel_default='INFO'
"""
DEBUG (10):    Detailed information, typically of interest only when
                diagnosing problems.
INFO (20):     Confirmation that things are working as expected.
WARNING (30):  An indication that something unexpected happened,
                or indicative of some problem in the near future (e.g.
                'disk space low'). The software is still working as expected.
ERROR (40):    Due to a more serious problem, the software has not been
                  able to perform some function.
CRITICAL (50): A serious error, indicating that the program itself
                  may be unable to continue running.
"""
def shutdown():
    log.info("shutting down logging")
    logging.shutdown()
def getlog(name,loglevel=loglevel_default):
    thislog=logging.getLogger(name)
    setlevel(loglevel,thislog)
    log.debug(f"Logging {loglevel} for {name}")
    return thislog
def setlevel(loglevel=loglevel_default,thislog=None):
    if not thislog:
        thislog=logging.root
    thislog.setLevel(loglevel)
    # log.info("Current {} logger level: {}".format(thislog,thislog.level))
def getlogfilename():
    """The part being written RIGHT NOW. Callers that want the whole run's log
    (writelzma, the log-to-server bundle) should use runfiles() instead — one
    run is now several files, and the interesting one is usually _001."""
    for h in [i for i in logging.root.handlers if isinstance(i,logging.FileHandler)]:
        return h.baseFilename
def runfiles(runid=None):
    """Every part of one run, in order — _001 first, so the version banner is
    the first thing a reader (or a bug report) sees."""
    try:
        from utilities import file as _file
        logdir=_file.getlogdir()
        if runid is None:
            runid=os.environ.get(RUN_ENV,'')
        if not runid:
            f=getlogfilename()
            return [pathlib.Path(f)] if f else []
        return _parts(logdir,runid)
    except Exception as e:
        log.info("could not list this run's log parts: {}".format(e))
        return []
def logformat(x):
    formats={'simpleformat':logging.Formatter('%(message)s'),
                'fullformat':logging.Formatter('%(asctime)s: %(name)s: '
                                    '%(levelname)s - %(message)s'),
                'timelessformat':logging.Formatter('%(name)s: %(levelname)s: '
                                    '%(message)s'),
                'rootformat':logging.Formatter('%(asctime)s: '
                                    # '- %(name)s '
                                    '%(levelname)s: '
                                    '%(message)s')
            }
    return formats[x]
_real_stderr = sys.__stderr__
def dorootloghandlers(self):
    if getattr(self, '_azt_handlers_installed', False):
        return
    self._azt_handlers_installed = True
    console = logging.StreamHandler(_real_stderr)
    console.setLevel(0) #Let the loglevel determine what to show
    console.setFormatter(logformat('simpleformat'))
    self.addHandler(console)
    tryfilehandler(self)
RUN_ENV='AZT_LOG_RUN'      #run id, inherited by restarts
RUNS_KEPT=5                #whole runs retained, newest first
PART_BYTES=10*1024*1024    #size cap per part
TOTAL_BYTES=200*1024*1024  #drop whole runs, oldest first, above this


def _runid():
    """The id shared by every process of ONE RUN.

    A run is a USER-INITIATED launch (Kent 2026-09-02: "one log per run, not
    counting restarts for updates or venv"). A restart is a continuation, so it
    inherits the id through the environment; a hand launch mints a new one. The
    discriminator is restartmark.launched_by_restart() — `--restart` in argv or
    AZT_VENV_RELAUNCHED — the same signal the restart marker uses, so "is this a
    new run?" has exactly one definition in the app.

    No colons: illegal in Windows filenames, and the old name's ISO slicing
    existed only to strip them."""
    inherited=os.environ.get(RUN_ENV,'')
    if inherited:
        try:
            from utilities import restartmark
            if restartmark.launched_by_restart():
                return inherited
        except Exception:
            pass #can't tell → treat as a fresh run; a spare log beats a lost one
    new=datetime.datetime.now(datetime.timezone.utc).replace(
                tzinfo=None).strftime('%Y-%m-%dT%H%M%S')
    os.environ[RUN_ENV]=new #inherited by anything we spawn
    return new


def _parts(logdir,runid):
    return sorted(logdir.glob('log_{}_*.txt'.format(runid)))


def _nextpart(logdir,runid):
    """One part per PROCESS, and per size roll. Allocated forward and NEVER
    renamed — unlike RotatingFileHandler, which shifts .1→.2 so the newest is
    always the base name and the START of a run ends up wherever the shuffle
    left it. Kent needs the start: it carries the version banner, and a field
    log that has rotated its banner away cannot even be attributed to a build.

    Per process, not per run, because the predecessor and successor are briefly
    alive together during a confirmed restart — two processes appending to one
    file interleaves, and on Windows risks a lock. The boundary also marks where
    the restart happened, which is useful to read."""
    highest=0
    for p in _parts(logdir,runid):
        try:
            highest=max(highest,int(p.stem.rsplit('_',1)[1]))
        except (IndexError,ValueError):
            continue
    return highest+1


def sweep(logdir=None,runid=None):
    """Keep the newest RUNS_KEPT runs ENTIRE, then trim oldest-first by total
    size. Whole runs only: a run whose _001 has been deleted is worthless, since
    that is the part with the version and the startup state."""
    try:
        from utilities import file as _file
        logdir=logdir or _file.getlogdir()
        runs={}
        for p in logdir.glob('log_*_*.txt'):
            try:
                runs.setdefault(p.stem[len('log_'):].rsplit('_',1)[0],
                                []).append(p)
            except IndexError:
                continue
        order=sorted(runs,reverse=True) #run ids sort chronologically
        keep=order[:RUNS_KEPT]
        drop=order[RUNS_KEPT:]
        total=sum(f.stat().st_size for r in keep for f in runs[r]
                    if f.exists())
        while keep and total>TOTAL_BYTES and len(keep)>1:
            oldest=keep.pop() #never drop the current run
            if oldest==runid:
                keep.append(oldest)
                break
            drop.append(oldest)
            total-=sum(f.stat().st_size for f in runs[oldest] if f.exists())
        for r in drop:
            if r==runid:
                continue
            for f in runs[r]:
                try:
                    f.unlink()
                except OSError:
                    pass
    except Exception as e:
        log.info("log sweep skipped: {}".format(e))


def tryfilehandler(self,lessiso=None):
    """One file per part of one run; retention counted in RUNS, not rollovers.

    Replaces RotatingFileHandler(mode='w', maxBytes=500k, backupCount=5) plus an
    unconditional doRollover() at import, under which rotation was driven by
    PROCESS STARTS: six launches in a day pushed the first off the end, and a
    field log arrived from OBT's machine already cut past its version banner —
    which made the bug in it undiagnosable (2026-09-02). `lessiso` is accepted
    and ignored, for old callers."""
    from utilities import file as _file
    try:
        logdir=_file.getlogdir()
        runid=_runid()
        filename=logdir.joinpath('log_{}_{:03d}.txt'.format(
                    runid,_nextpart(logdir,runid)))
        handler=_PartRollingHandler(filename,runid,encoding='utf-8')
        handler.setLevel(0) #Let the loglevel determine what to show
        handler.setFormatter(logformat('fullformat'))
        handler.addFilter(DedupeFilter())
        self.addHandler(handler)
        sweep(logdir,runid)
    except Exception as e:
        log.info("Logfile problem ({}); console logging only.".format(e))


class _PartRollingHandler(logging.FileHandler):
    """Open the NEXT part when this one passes PART_BYTES.

    Rolls FORWARD to a new name rather than renaming anything, so every earlier
    part — above all _001, with the version banner — stays exactly where it was.
    A runaway log is bounded into parts instead of overwriting its own start."""
    def __init__(self,filename,runid,**kwargs):
        self.runid=runid
        self.logdir=pathlib.Path(filename).parent
        super().__init__(filename,mode='a',**kwargs)

    def emit(self,record):
        try:
            if self.stream is not None and self.stream.tell()>=PART_BYTES:
                self._nextfile()
        except Exception:
            pass #never lose a record over bookkeeping
        super().emit(record)

    def _nextfile(self):
        new=self.logdir.joinpath('log_{}_{:03d}.txt'.format(
                    self.runid,_nextpart(self.logdir,self.runid)))
        self.close()
        self.baseFilename=str(new)
        self.stream=self._open()


class DedupeFilter(logging.Filter):
    """Collapse a record identical to the one before it.

    THE FLOOD IS WHAT ATE THE FIELD LOG (2026-09-02): `availablexy` logs at INFO
    once per widget, dozens per page, many lines byte-identical; so do
    `update_active_cell` and the `lan_peer_sync` probe. 500 kB of log was spent
    on diagnostics nobody reads, and the banner and the actual failure rotated
    off the end.

    Chosen over demoting those call sites because it needs no judgement about
    what matters, applies to every present and future flood, and LOSES NOTHING:
    when the message finally changes, the suppressed count is emitted, so
    "this fired 87 times" is still on the record — and as a count it is easier
    to read than 87 lines. This is what syslog has done for decades.

    Deliberately compares the FORMATTED message, not the record: two calls with
    different args are different lines, which is what a reader cares about."""
    def __init__(self,name=''):
        super().__init__(name)
        self._last=None
        self._count=0

    def filter(self,record):
        try:
            msg=record.getMessage()
        except Exception:
            return True
        if msg==self._last:
            self._count+=1
            return False
        if self._count:
            #Attach the tally to the line that broke the run, so it is never
            #stranded behind a crash: a trailing summary that needs another
            #record to flush it would be lost exactly when the log matters.
            record.msg='[previous line repeated {}×] {}'.format(
                        self._count,msg)
            record.args=()
        self._last=msg
        self._count=0
        return True
def test(self):
    self.debug("Debug!")
    self.info("Info!")
    self.warning("Warning!")
    self.error("Error!")
    self.exception("Exception!") #this expects exception info
    self.critical("Critical!")
def contents(self,lastlines=0):
    with open(getlogfilename(),'r', encoding='utf-8') as d:
        return d.readlines()[-lastlines:]
def writelzma(filename=None):
    """Bundle this run's logs into ONE .tar.xz and return its path.

    It used to make TWO archives and return the wrong one (Kent 2026-09-02, who
    spotted the email naming the lesser file):
      * `log_<iso>Z.xz` — plain lzma of the CURRENT PART only, the original
        one-file assumption; and
      * `log_<iso>Z.xz.tar.xz` — the tar of every part, added later for the
        rotated `.1`-`.5` siblings, with a doubled extension because the name
        was built as `<already .xz> + '.tar.xz'`.
    The return value was never updated when the tar was added, so every caller
    — the error page's mail body, the conversion notice — named a file
    containing a fraction of the evidence. The single-file copy is a strict
    subset of the tar, so it is gone rather than fixed."""
    from utilities import file as _file
    logdir=_file.getlogdir()
    stamp=datetime.datetime.now(datetime.timezone.utc).replace(
                tzinfo=None).strftime('%Y-%m-%dT%H%M%SZ')
    compressedurl=logdir.joinpath('azt_log_{}.tar.xz'.format(stamp))
    if not filename:
        filename=getlogfilename()
    log.info("Using filename {}".format(filename))
    # EVERY PART OF THIS RUN, not a glob on the current part's name. That glob
    # worked under the old naming because rollovers were siblings of one base
    # name (log_<date>.txt, .1, .2); with per-run parts it would have matched
    # only the part being written — losing _001, which is the one carrying the
    # version banner and the startup state. Sending a bundle without it is the
    # exact failure that made a field log undiagnosable (2026-09-02).
    filenames=list(runfiles())
    if not filenames:
        filenames=list(logdir.glob(pathlib.Path(filename).name+'*'))
    # RESTART MARKERS TOO (Kent 2026-09-02). A marker still present IS the
    # evidence that a restart was attempted and never landed — it carries the
    # reason, the version, the argv and the time — and it is the only artefact
    # that says so, because the process that would have logged it is gone. It
    # lives in this same directory, so a bundle that omits it throws away the
    # one file explaining why the logs stop where they do. Whatever is there:
    # normally at most one, but a name-glob costs nothing and cannot miss a
    # variant.
    filenames+=[p for p in logdir.glob('restart_in_progress*.json')
                if p not in filenames]
    try:
        f=tarfile.open(name=str(compressedurl), mode='x:xz',
                        encoding='utf-8', preset=9)
    except Exception as e:
        log.info("could not open {}: {}".format(compressedurl,e))
        return compressedurl
    try:
        for fn in filenames:
            try:
                f.add(fn,arcname=pathlib.Path(fn).name)
            except Exception as e:
                log.info("{} not added: {}".format(fn,e))
        log.info("Compressed files: {}".format(f.getnames()))
    finally:
        f.close()
    return compressedurl
        with lzma.open(compressedurl) as ch:
            data2 = ch.read().decode("utf-8")
            ch.close()
    return compressedurl
log = logging.getLogger() #this is the root; set level with setlevel
setlevel('INFO') #If not set elsewhere
dorootloghandlers(log)
if __name__ == "__main__":
    loglevel=10
    log=getlog('root') #not ever a module
    setlevel(loglevel)
    log.info("Hey, this is something.")
    writelzma()
    shutdown()
