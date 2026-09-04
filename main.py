#!/usr/bin/env python3
# coding=UTF-8
"""Consider making the above work for a venv"""
"""This file runs the actual GUI for lexical file manipulation/checking"""
# VERSION FIRST — before the duplicate gate and before py_modules. It is a bare
# string assignment with no imports behind it, so nothing is gained by defining
# it later, and something is lost: py_modules.ensure_venv() runs DURING the
# import below and writes a restart marker, which reads the version off
# __main__. Defined after that import, it was still unset, so the first-run venv
# relaunch — the one producer where a failure is hardest to diagnose — recorded
# `'version': None` (observed on a fresh clone, 2026-09-01).
__version__='1.15.16' #This is a string...
# Duplicate gate: py_modules MUTATES shared state (creates the venv,
# runs pip, clones sister repos) — a second instance must be stopped before
# racing the first (two pips in one venv can corrupt packages).
try:
    from utilities import duplicates
    if duplicates.running_file(__file__):
        exit()
except ImportError: #psutil not installed yet — only true on a machine's
    pass            #very first boot, when nothing can be racing anyway;
                    #py_modules below installs it, so every later boot gates.
import utilities.py_modules #This tries importing, and installs on failure
program={'name':'A-Z+T',
        'tkinter':True, #for some day
        'production':False, #True for making screenshots (default theme)
        'testing':False, #normal error screens and logs
        'Demo':False, #will get set otherwise later if it is
        'version':__version__, 
        'testversionname':'testing', #always have some real test branch here
        'url':'https://github.com/kent-rasmussen/azt',
        'Email':'kent_rasmussen@sil.org',
        'exceptiononload':False #for now
        }
import platform
program['hostname']=platform.uname().node
from utilities import file
"""Integers here are more fine grained than 'DEBUG'. I.e., 1-9 show you more
information than 'DEBUG' does):
1. Information I probably never want to see.
'DEBUG': Stuff that should probably not be shared with the user in the long
    term (as it is distracting, too much, or hard to make use of), but
    definitely should be put out all the time for now, in case of any errors.
'INFO': information that will never likely be in the user's way, and may be
    helpful.
Other levels:'WARNING','ERROR','CRITICAL'
"""
from utilities.utilities import *
from utilities import logsetup
log=logsetup.getlog(__name__)

"""My modules, which should log as above"""
from io_put import lift, xlp, export
from utilities import htmlfns, rx, executables
from backend import langtags,parser
from frontend import alphabet_chart
from frontend import alphabet_comparison
import settings
import migration
try:
    from io_put import sound
    from frontend import transcriber, sound_ui
    # These imports now SUCCEED without pyaudio (the sound modules guard
    # their own roots and degrade), so read the flag rather than relying
    # on an ImportError to reach us.
    program['nosound']=not sound.PYAUDIO_OK
    if program['nosound']:
        log.error("pyaudio unavailable; sound features are off "
                    "(recording/playback disabled, sorting etc. fine).")
except Exception as e:
    program['nosound']=True
    log.error("Problem importing Sound/pyaudio. Is it installed? {}"
            "".format(e))
    program['exceptiononload']=True
from utilities import times
program['start_time'] = times.now()
import threading
import multiprocessing
import psutil
import importlib.util
import collections
from random import randint
import os
import urllib.parse #mailto: on the error page must be properly encoded
# Stack dumper for diagnosing freezes: when the UI hangs, run `kill -USR1 <pid>`
# (pid logged just below) and the Python stacks of all threads are written to
# /tmp/azt_stacks.txt — works even when stuck in a C-level Tk/X call, so it
# names the exact blocked call instead of us guessing. Dumps to a FILE (not
# stderr) so it's easy to retrieve.
import faulthandler, signal as _signal
try:
    _stackfile = open('/tmp/azt_stacks.txt', 'w')
    faulthandler.register(_signal.SIGUSR1, file=_stackfile, all_threads=True)
    log.info("faulthandler armed: if it hangs, run `kill -USR1 %s` then send "
             "/tmp/azt_stacks.txt", os.getpid())
except (AttributeError, ValueError, OSError) as e:
    log.info("faulthandler not armed: %s", e)  # e.g. Windows
if os.environ.get('AZT_UI_BACKEND', '').lower() == 'webview':
    program['tkinter'] = False
if program['tkinter']:
    import tkinter #as gui
    import tkinter.font
    import tkinter.scrolledtext
    if not program['testing']:
        from frontend import tkintermod
        tkinter.CallWrapper = tkintermod.TkErrorCatcher
from frontend import ui
import time
import sys
"""for tr:"""
import locale
import gettext
from utilities.i18n import _, set_translator
import subprocess
import webbrowser

from backend.reporting.generator import Report
from backend.core.lexicon import Senses, Segments, WordCollection, Parse, Tone
from backend.core.sorting_engine import Sort
from backend.core.profiles import ProfileAnalyzer
from frontend.ui_shell import (HasMenus, Menus, StatusFrame, TaskDressing,
    LiftChooser, ImageFrame, Splash, ResultWindow, Settings as UISettings)
from utilities.error_handler import notify_error as ErrorNotice
from utilities.error_handler import notify_user as NotifyUser
from utilities.error_handler import set_error_handler, set_user_notifier
import frontend.error_notice
import frontend.status_window
set_error_handler(frontend.error_notice.ErrorNotice)
set_user_notifier(frontend.status_window.notify_user)
from frontend.sort_buttons import (SortButtonFrame, _GroupButtonFrame,
    SortGroupButtonFrame, SortGlyphGroupButtonFrame)
from tasks.base import Task
from tasks.chooser import TaskChooser
from backend.core.report_mixins import Multislice, MultisliceS, MultisliceT, Multicheck, Multicheckslice, ByUF, Background
from backend.core.vcs import Repository, Mercurial, Git, GitReadOnly
from backend.core.analysis import Analysis, SliceDict, StatusDict, ExampleDict, DictbyLang, Entry
from backend.core.analysis_inputs import ToneFrames, CheckParameters, Glosslangs
from backend.core.alphabet import Alphabet
from backend.core.file_parser import FileParser
from settings import Settings
from tasks.tasks import (ExportData, AlphabetChart, AlphabetComparisonPages,
    Sound, Record, Transcription, WordCollectionwRecordings,
    WordCollectionLexeme, WordCollectionCitation, WordCollectionCitationwRecordings,
    WordCollectionPlural, WordCollectionImperative, ParseWords, WordCollectnParse,
    WordCollectnParsewRecordings, WordsParse, ParseSlice, ParseSliceWords, Placeholder,
    ToneFrameDrafter, SortSyllables, SortCV, SortV, SortC, SortT, Transcribe,
    TranscribeS, TranscribeV, TranscribeC, TranscribeT, JoinUFgroups, RecordCitation,
    RecordCitationT, ReportCitation, ReportCitationBackground,
    ReportCitationMulticheckBackground, ReportCitationMultichecksliceBackground,
    ReportCitationByUF, ReportCitationByUFMulticheckBackground,
    ReportCitationByUFMultichecksliceBackground, ReportCitationByUFBackground,
    ReportCitationMultislice, ReportConsultantCheck, ReportCitationT,
    ReportCitationTBackground, ReportCitationTL, ReportCitationTLBackground,
    ReportCitationMultisliceT, ReportCitationMultisliceTL,
    ReportCitationMultisliceTBackground, ReportCitationMultisliceTLBackground)

class App:
    def handle_exception(self, exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt): #ignore Ctrl-C
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        log.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
    def disclosure(self):
        log.info(_("Running {azt} v{version}, updated {rel} ({date})").format(
                                    azt=self.name,
                                    version=self.version,
                                    rel=self.modified_time_relative,
                                    date=self.modified_time))
        log.info(_("Called with arguments {exe} {script} / {args}").format(exe=sys.executable,
                                                        script=sys.argv[0], args=sys.argv))
        log.info(_("Executed by {version}").format(version=sysexecutableversion()))
        text=_("Working directory is {dir} on {host}, running on {cores} cores"
                ).format(dir=self.aztdir,
                        host=self.hostname,
                        cores=multiprocessing.cpu_count())
        try:
            text+=_(", at {mhz}Mhz").format(mhz=collections.Counter(
                    [i.current for i in psutil.cpu_freq(percpu=True)]).most_common(1)[0][0])
        except ModuleNotFoundError:
            pass
        log.info(text)
        log.info(_("Computer identifies as {platform}").format(platform=platform.uname()))
        log.info(_("Loglevel is {level}; started at {time}")
                .format(level=self.loglevel, time=times.now().isoformat()[:-7]+'Z'))
    def show_scaling_from_windows(self):
        try:
            import ctypes
            log.info("Windows scaling: {factor}".format(
                        factor=ctypes.windll.shcore.GetScaleFactorForDevice(0)))
        except Exception:
            pass
    def get_interface_languages(self):
        transdir=file.gettranslationdirin(self.aztdir)
        log.info("looking for translations actually available in {transdir}".format(transdir=transdir))
        langs=[
            os.path.basename(i) for i in os.listdir(transdir)
            if os.path.isdir(os.path.join(transdir, i))
            and os.path.isdir(os.path.join(transdir, i, 'LC_MESSAGES'))
            and 'azt.mo' in os.listdir(os.path.join(transdir, i, 'LC_MESSAGES'))
            ]
        log.info("Found {langs}".format(langs=langs))
        self.i18n={'en': gettext.translation('azt', transdir, languages=['en_US'],
                                        fallback=True
                                    )}
        for i in langs:
            # log.info("Loading translation for {}".format(i))
            try:
                self.i18n[i.split('_')[0]] = gettext.translation('azt', transdir, languages=[i])
            except Exception:
                log.error("Failed to load translation for {}".format(i))
            # finally:
            #     log.info("Translation for {} loaded".format(i))
        self.interfacelangs={i for i in self.i18n}
        lang=self.interfacelang() #translation works from here
        # log.info(_("Translation is working now ({lang}).").format(lang=lang))
    def interfacelang(self,lang=None,magic=False):
        """Determine and/or set the interface language.
        Uses i18n._current to detect which translation is active."""
        from utilities import i18n
        curlang=None
        for l in self.i18n:
            if i18n._current == self.i18n[l].gettext:
                curlang=l
                break
        if not lang and not curlang: #deduce, but don't override current setting.
            # log.info("checking for a local setting")
            code=file.uilang()
            if not code:
                # log.debug("local settings don't seem to have returned any "
                #         f"results ({code})")
                code=self.getlangfromlocale()
                if not code:
                    log.info(_("locale.getlocale doesn’t seem to have "
                    "returned any results: "
                    "{locale} (OS: {os})"
                    "Using English user interface").format(locale=locale.getlocale(),
                                                            os=platform.system()))
                    log.info(_("locale.getdefaultlocale output for "
                                "comparison: {locale}").format(locale=locale.getdefaultlocale()))
                    code='en' #I think loc=None normally means English on macOS
            if code in self.i18n:
                # log.info("returning {} (of {})".format(code,list(i18n)))
                lang=code
        if lang and lang != curlang and lang in self.i18n:
            set_translator(self.i18n[lang].gettext)
            self.chain_collab_translations(lang)
            file.uilang(lang)
            return lang
        return curlang
    def chain_collab_translations(self,lang):
        """Client contract § 6. azt ships its own catalog, so the collab
        client's catalog must be chained UNDERNEATH it as a gettext
        fallback: since client 0.43.1 there is no second-chance retry, so
        a host translator that returns the msgid unchanged leaves every
        client-owned string (i.e. every sync/collab dialog) rendering as
        English — the French-app-with-English-collab-dialogs split. Also
        re-languages the client itself, and subscribes so the chain is
        rebuilt if the daemon's language toggle fires (without that hook
        azt's catalog stays frozen at the startup language while the
        client catalog re-languages under it). Never blocks startup: with
        no client importable there is simply nothing to chain."""
        try:
            import azt_collab_client
            from azt_collab_client import i18n as collab_i18n
        except Exception:
            return #legacy mode / client not importable
        try:
            t=self.i18n.get(lang)
            collab_i18n.set_language(lang)
            if t is None:
                # No azt catalog for this language (English): let the
                # client use its own catalog rather than a null host one.
                azt_collab_client.set_translator(None)
                return
            if not getattr(t,'_azt_collab_fallback',False):
                # gettext accumulates fallbacks; only add ours once per
                # translation object (they're per-language singletons).
                t.add_fallback(collab_i18n.gettext_translation())
                t._azt_collab_fallback=True
            azt_collab_client.set_translator(t.gettext)
            collab_i18n.subscribe_language_change(
                self._collab_language_changed) #idempotent per contract
        except Exception as e:
            log.info(f"collab translation chain: {e}")
    def _collab_language_changed(self,lang):
        """The client re-languaged (daemon settings toggle): rebuild the
        chain so azt follows. Terminates — interfacelang() only re-chains
        when the language actually CHANGED, and by the time this fires our
        translator is already on *lang*."""
        try:
            if lang in getattr(self,'i18n',{}):
                self.interfacelang(lang)
            else:
                self.chain_collab_translations(lang)
        except Exception as e:
            log.info(f"collab language change: {e}")
    def getlangfromlocale(self):
        loc,enc=locale.getlocale()
        log.info(f"Found locale {loc}, encoding {enc}")
        if loc:
            code=loc.split('_')[0]
            if code not in self.i18n and code in ['English','Français','French']:
                if code == 'English':
                    code='en'
                else:
                    code='fr'
            # log.info("Using code {}".format(code))
            return code
    def show_error_notice(self, text, **kwargs):
        ErrorNotice(text, program=self, **kwargs)
    def find_source_repo(self):
        # self.findexecutable('git') #done in repo init
        self.source_repo=GitReadOnly(self) #this needs root for errors
        self.modified_time=self.source_repo.lastcommitdate()
        self.modified_time_relative=self.source_repo.lastcommitdaterelative()
        try:
            branch=self.source_repo.branch
        except AttributeError:
            branch='main'
            log.info(_("Repo has no branch attribute; assuming main branch."))
        if branch != 'main':
            self.version+=f" ({branch})"
        self.docsurl=f'https://github.com/kent-rasmussen/azt/blob/{branch}/docs'
    def repocheck(self):
        log.info(_("Checking for a data repository"))
        self.data_repo=dict() #then copy to class attribute if there
        self.data_directory=file.getfilenamedir(self.filename)
        if getattr(self,'collab',None):
            # Collab mode: the daemon owns this repo (commits via the
            # submit_file seam, push/pull via its scheduler + shutdown
            # sync). Building Git/Mercurial objects here would fight it
            # (author -c injection, .gitignore rewrites, subprocess git
            # against a daemon-locked repo). data_repo stays empty, so
            # repo_commit() and the shutdown share() loop are no-ops.
            log.info(_("Collaboration active; legacy VCS disengaged "
                        "for this project."))
            return
        if not self.testing:
            repo={ #start with local variable:
                    'git': Git(self),
                    'hg': Mercurial(self),
                    }
            for r in repo:
                if (hasattr(repo[r],'files') #fails if no exe
                        and repo[r].exists()): #tests for .code dir
                    log.info(_("Found {name} Repository!"
                                ).format(name=repo[r].repotypename))
                    self.data_repo[r]=repo[r]
                elif r == 'git' and repo[r].cmd: #git executable found
                    #don't worry about hg, if not there already
                    log.info(_("No Git data repository found; creating."))
                    repo[r].init()
                    # self.filename, NOT self.liftfilename: that name belongs to
                    # SettingsManager (settings/__init__.py, set FROM
                    # program.filename) and has never existed on App — so this
                    # line raised AttributeError every time it was reached. It
                    # survived because it is reached only when there is no git
                    # data repo yet AND git is present, i.e. creating a data
                    # repo from scratch; collab projects let the daemon own the
                    # repo, so nobody hit it until a fresh legacy project
                    # (2026-09-02). Nor would self.settings work here: repocheck
                    # runs before Settings(self) exists.
                    repo[r].add(self.filename)
                    repo[r].commit()
                    self.data_repo[r]=repo[r]
    def repo_commit(self):
        for r in self.data_repo:
            self.data_repo[r].commit()
    def collab_poll(self):
        """Phase-3 background poll (10 s, tk after-loop): notice peer
        changes the daemon merged into our working tree and offer a
        reload. Detection lives in CollabSession.poll_remote_change;
        correctness never depends on this poll (saves are base-aware)
        — it only bounds how long stale peer data stays displayed.

        The daemon calls run on a WORKER thread, and only the widget-
        touching tail returns to the UI loop (_collab_poll_done). Before
        that they ran here, so a daemon that listened without answering
        froze the Tk main loop for rpc.call's 300s default — and because
        this fires inside wait_window's nested loop too, the freeze could
        land mid-sort. Nothing here is load-bearing, per the paragraph
        above, so it must never be able to block the UI."""
        if getattr(self,'_restarting',False):
            # A confirmed restart keeps this process alive while the successor
            # boots (see _confirm_restart), and the successor attaches to the
            # same project. Two clients polling and offering reloads on one
            # working tree is exactly what the handover is meant to avoid, so
            # stop polling the moment we start handing over. RESCHEDULED, not
            # abandoned: a restart can fail, and then this copy is live again
            # and should be polling — dropping the loop here would leave a
            # working app quietly not noticing peer changes for the session.
            self.tk_root.after(10000,self.collab_poll)
            return
        session=getattr(self,'collab',None)
        if not session:
            return #project disconnected mid-session; stop polling
        if getattr(self,'_collab_poll_busy',False):
            # Still waiting on the daemon. Skipping beats stacking a thread
            # per tick on a wedged daemon; log once, then stay quiet.
            if not getattr(self,'_collab_poll_skipped',False):
                self._collab_poll_skipped=True
                log.info("collab_poll: daemon slow to answer; skipping ticks")
            self.tk_root.after(10000, self.collab_poll)
            return
        def work():
            # ONE project_status per tick, shared by the change-detection
            # and the title-bar badge (client contract § 17c rule 4: never
            # fire it from several handlers for the same UI event). It also
            # means both read the SAME snapshot, instead of deciding
            # "stale" and "shared" from two different ones.
            # poll_remote_change belongs here too: it makes a SECOND call
            # (since_sha enrichment) once HEAD is known to have moved.
            st=outcome=None
            try:
                st=session.status()
                outcome=session.poll_remote_change(st=st)
            except Exception as e:
                log.info(f"collab_poll worker: {e}")
            try:
                self.tk_root.after(
                        0,lambda: self._collab_poll_done(session,st,outcome))
            except Exception:
                pass #root already gone; shutting down
        self._collab_poll_busy=True
        try:
            threading.Thread(target=work,daemon=True,
                    name='collab_poll').start()
        except Exception as e:
            # Never let a thread failure end the poll loop for the session.
            self._collab_poll_busy=False
            log.info(f"collab_poll: could not start worker: {e}")
            self.tk_root.after(10000, self.collab_poll)
    def _collab_poll_done(self,session,st,outcome):
        """UI-thread tail of collab_poll — everything here touches widgets."""
        self._collab_poll_busy=False
        self._collab_poll_skipped=False
        try:
            if getattr(self,'collab',None) is not session:
                return #disconnected (or reconnected) while we were waiting
            # Say it out loud, ONCE per outage. status() returns None on every
            # failure, so without this an unreachable daemon is now completely
            # silent — the freeze used to be the only symptom. Interim: the
            # real cause is the daemon wedging before it serves.
            if st is None and not getattr(self,'_collab_silent_since',None):
                self._collab_silent_since=time.time()
                NotifyUser(_("The collaboration server has stopped answering. "
                        "Sync status will be out of date until it responds."))
            elif st is not None and getattr(self,'_collab_silent_since',None):
                mins=(time.time()-self._collab_silent_since)/60
                self._collab_silent_since=None
                NotifyUser(_("The collaboration server is answering again "
                        "(after {mins:.0f} minutes).").format(mins=mins))
            if (outcome == 'changed'
                    and not getattr(self,'writing',False)
                    and session.reload_offer_due()):
                self.collab_offer_reload()
            self.collab_title_status(session,st=st)
        except Exception as e:
            log.info(f"collab_poll: {e}")
        finally:
            self.tk_root.after(10000, self.collab_poll)
    def collab_title_status(self,session,st=None):
        """Ambient sync status, title-bar cheap (Kent 2026-07-11): every
        poll tick, append the one-phrase collab truth to the visible
        window titles (task window + its runwindow — whichever the user
        is actually looking at). The separator marks our suffix so we
        never eat the real title; tasks that reset their own titles just
        get re-suffixed on the next tick."""
        SEP=' ⇅ '
        try:
            txt=session.ambient_status(st=st)
        except Exception:
            return
        task=getattr(self,'task',None)
        win=getattr(task,'ui',None) if task is not None \
            else getattr(getattr(self,'taskchooser',None),'ui',None)
        for w in {win, getattr(win,'runwindow',None)} - {None}:
            try:
                if not w.winfo_exists():
                    continue
                base=w.title().split(SEP)[0]
                w.title(base+SEP+txt if txt else base)
            except Exception as e:
                log.info(f"collab_title_status: {e}")
    def collab_offer_reload(self):
        # F6: one open offer at a time. Multiple polls detecting team
        # changes used to each spawn their own "Team changes available"
        # window (6+ stacked observed). If an offer is still open, don't
        # stack another — the existing one already says "reload", and
        # its restart action pulls the newest HEAD regardless of which
        # poll opened it.
        existing = getattr(self, '_collab_offer_win', None)
        try:
            if existing is not None and existing.winfo_exists():
                return
        except Exception:
            pass
        from utilities.error_handler import notify_error
        log.info(_("Offering reload for team changes"))
        # § 8b obl. 3a: say WHY. A prompt that can't name what changed is
        # indistinguishable from a spurious one, and users learn to
        # dismiss both. summary is '' when there's nothing honest to say.
        summary=''
        try:
            summary=self.collab.changes_summary()
        except Exception as e:
            log.info(f"changes_summary: {e}")
        # The paragraph below keeps its original msgid so the five
        # existing catalogs still translate it; the summary rides ABOVE it
        # as one new string rather than editing the old one (a changed
        # msgid orphans every translation of it).
        text=_("Your team made changes to this database. Press "
              "‘Load now’ to load them — or OK to keep working and "
              "load them later. Your saves are safe either way, and "
              "will be combined with your team’s.")
        if summary:
            text=_("What changed: {summary}").format(
                    summary=summary)+'\n\n'+text
        else:
            # NEVER PROMPT WITHOUT A REASON (field 2026-07-30, 1.13.0: a "Team
            # changes available" window carrying no explanation at all). The
            # comment above states obl. 3a's rule — an unexplained prompt is
            # indistinguishable from a spurious one — and then the `if` quietly
            # allowed exactly that whenever changes_summary() came back ''.
            # changes_summary returns '' in two cases: the changes_since probe
            # failed (or the daemon predates it), or the daemon reported a range it
            # could attribute nothing to. Either way, SAY so; the string is the
            # same literal changes_summary uses for an unknown base, so it shares
            # that translation.
            text=_("What changed: {summary}").format(
                    summary=_("(couldn’t tell what changed)"))+'\n\n'+text
            log.warning("Reload prompt with NO attribution: changes_since=%r "
                        "— empty means the probe failed or the daemon predates "
                        "it; known with count 0 and bot_count 0 means the daemon "
                        "attributed nothing in the range.",
                        getattr(self.collab,'changes_since',None))
        self._collab_offer_win = notify_error(
            text,
            title=_("Team changes available"),
            button=(_("Load now"),
                    lambda event=None: self.reload_database()))
    def askwhichlift(self):
        # put right click menu here
        LiftChooser(self)
        if not self.filename or isinstance(self.filename, list): 
            #If not set or still list, for any reason
            sysshutdown()
    def get_lift_file(self):
        self.filename=file.getfilename() #returns filename if there, else filenames
        log.info("getfilename returned {}".format(self.filename))
        if not self.filename:
            self.askwhichlift()
        if isinstance(self.filename, list):
            if self.testing and (tl:=getattr(self, 'testlift', None)):
                if (f:=[i for i in self.filename if tl in i]):
                    self.filename=f[0]
                    return
            self.askwhichlift()
        elif not file.exists(self.filename):
            self.askwhichlift()
        if self.filename and 'Demo' in str(self.filename):
            self.demo=True #not used?
            file.writefilename() #clear this to select next time
    def warn_sound_problems(self):
        """Booting with degraded sound is a LAST RESORT and must be noisy
        (Kent 2026-07-16): the self-heal installers get their chance every
        start; if problems remain, the user must acknowledge them before
        doing any work — a fieldworker must never record silence, or skip
        transcription, without knowing why."""
        from backend.core.sound import SOUND_PROBLEMS
        if not SOUND_PROBLEMS:
            return
        lines=[_("This computer’s sound support is BROKEN, and A-Z+T "
                 "couldn’t repair it automatically:"),'']
        lines+=[f"• {component}: {error}"
                for component,error in SOUND_PROBLEMS]
        if (platform.system() == 'Linux'
                and any(c.startswith('pyaudio') for c,e in SOUND_PROBLEMS)):
            lines+=['',_("If you have errors containing ˋportaudioˊ above, "
                     "you should install pyaudio with your package manager "
                     "(e.g. ˋsudo apt install portaudio19-devˊ, then restart "
                     "{name} so it can rebuild pyaudio).").format(
                                                            name=self.name)]
        lines+=['',_("You can sort and run reports, but recording, playback "
                 "and/or transcription will NOT work until this is fixed. "
                 "Fix the problem (see the log for details), or ask for "
                 "help, before collecting data on this machine."),'',
                _("Restarting {name} retries the automatic repair."
                  ).format(name=self.name)]
        ErrorNotice('\n'.join(lines),title=_("Sound is not working!"),
                    wait=True) #blocking: acknowledge before any work
    def warn_bootstrap_problems(self):
        """Setup failures (venv, pip) happen before any UI exists, so
        py_modules can only log them — and a machine that then starts
        and half-works looks healthy (Kent 2026-07-25: a Linux install
        failed on a missing ensurepip and "just failed and continued").
        Surface them here, blocking, like degraded sound."""
        from utilities.py_modules import BOOTSTRAP_PROBLEMS
        if not BOOTSTRAP_PROBLEMS:
            return
        lines=[_("{name} couldn’t finish setting itself up on this "
                 "computer:").format(name=self.name),'']
        lines+=[f"• {component}: {problem}"
                for component,problem in BOOTSTRAP_PROBLEMS]
        lines+=['',_("It will run with whatever modules are already "
                 "installed, so some features may fail or behave oddly, "
                 "and updates won’t reach this machine. Fix this (see the "
                 "log for details), or ask for help, before relying on "
                 "this computer for real work."),'',
                _("Restarting {name} retries the automatic setup."
                  ).format(name=self.name)]
        ErrorNotice('\n'.join(lines),title=_("Setup did not finish!"),
                    wait=True) #blocking: acknowledge before any work
    def warn_font_problems(self):
        """Charis SIL missing (Kent 2026-07-29: "this should never be; if we're
        missing charis SIL at boot, please let's put up an error notice saying
        so"). Tk substitutes a missing family SILENTLY, and the substitute's
        metrics differ — so text wraps and buttons size differently from every
        other machine, which reads as a layout bug rather than a missing font.
        Theme.setfonts records what actually resolved."""
        missing=getattr(getattr(self,'theme',None),'missing_font_families',None)
        if not missing:
            return
        lines=[_("{name} can’t find the font(s) it lays its screens out with "
                 "on this computer:").format(name=self.name),'']
        lines+=[_("• {wanted} — your computer used ‘{got}’ instead"
                  ).format(wanted=wanted,got=got) for wanted,got in missing]
        lines+=['',_("Text will be a different size here than on other "
                 "machines, so words may wrap oddly and buttons may look "
                 "wrong. Install the missing font(s) and restart {name} — "
                 "they are free from software.sil.org."
                 ).format(name=self.name)]
        ErrorNotice('\n'.join(lines),title=_("Missing font!"),wait=True)
    def _run_setup(self):
        """All setup that must happen after the UI event loop is live.

        For tkinter this runs synchronously before mainloop().
        For pywebview this runs in a background thread after webview.start()
        has loaded, so that blocking calls like wait_window() can work.
        """
        # Did the run BEFORE this one try to restart and never come back? Asked
        # first, before any of the slow work below, and deliberately without
        # clearing: if this boot also fails, the next one must still find it.
        # See utilities/restartmark.py.
        try:
            from utilities import restartmark
            restartmark.report()
        except Exception as e:
            log.info("restart marker check skipped: %s",e)
        lastcommit=self.source_repo.lastcommitdate()
        self.tk_root.wraplength=self.tk_root.winfo_screenwidth()-300 #exit button
        self.tk_root.wraplength=int(self.tk_root.winfo_screenwidth()*.7) #exit button
        self.tk_root.withdraw()
        if platform.system() == 'Windows': #this is only for MS Windows!
            import ctypes
            user32 = ctypes.windll.user32
            import ctypes
            try: # Windows 8.1 and later
                ctypes.windll.shcore.SetProcessDpiAwareness(2)
            except Exception as e:
                pass
            try: # Before Windows 8.1
                ctypes.windll.user32.SetProcessDPIAware()
            except (AttributeError, OSError): # Windows 8 or before
                pass
            screensize = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
            log.info(_("MS Windows screen size: {size}").format(size=screensize))
        self.warn_bootstrap_problems() #first: a failed venv is usually WHY
        #                               sound (or anything else) is degraded
        self.warn_sound_problems() #LOUD, blocking; degraded sound must never
        #                           be silent in a sound-centric app
        self.warn_font_problems() #a substituted font silently changes every
        #                          layout on this machine only
        self.prep_to_write()
        langtags.Languages(self)
        self.get_lift_file() #self.filename, maybe LiftChooser (NOT self.analang)
        self.splash = Splash(self)
        self.splash.draw()
        FileParser(self) #needs self.filename, pick up self.analang from settings or file
        # Collab seam: no-op unless this project opted in (per-project
        # 'collab' setting). On success sets self.collab and hooks
        # db.collab_submit; on daemon-unavailable logs + leaves
        # self.collab None so repocheck below runs the legacy path.
        from backend.core import collab
        if collab.attach(self):
            # Phase 3: the desktop has no push channel from the daemon
            # (§17b), so poll for peer changes landing under us.
            self.tk_root.after(10000, self.collab_poll)
        self.splash.progress(5)
        from frontend.vcs_ui import VCSPresenter
        from frontend.report_ui import ReportPresenter
        from frontend.sort_ui import SortPresenter
        from frontend.lexicon_ui import LexiconPresenter
        self.vcs_ui = VCSPresenter(self)
        self.report_ui = ReportPresenter()
        self.sort_ui = SortPresenter(self.theme) #only needed (so far)
        self.lex_ui = LexiconPresenter()
        self.splash.progress(25)
        self.repocheck()
        ToneFrames(self)
        self.splash.progress(35)
        Settings(self) #needs self.filename, pick up self.analang from file
        CheckParameters(self) #depends on settings (nothing but self.analang?)
        self.settings.post_lift_init()
        self.splash.progress(45)
        ProfileAnalyzer(self) #registers as self.profiles
        ExampleDict(self) #needed for makestatus, needs params,slices,data
        Alphabet(self) #after slicedict is up; needs params
        langtags.Languages(self)
        self.splash.progress(50)
        # SliceDict(adhoc,profilesbysense,self) #needs adhoc,profilesbysense
        # StatusDict(filename,dict,self) #needs filename,dict
        UISettings(self)
        TaskChooser(self) #TaskChooser MainApplication
        # GLOBAL no-window watchdog. Started here, last, because this is the
        # first moment the app is supposed to HAVE a window — everything above
        # legitimately runs with nothing but the splash on screen. It arms
        # itself on the first window it actually sees, so an unusually slow
        # boot below this line still can't produce a false alarm.
        # THE RESTART SUCCEEDED — but only a window that actually reaches the
        # SCREEN says so, which is why clearing the marker is handed to the
        # watchdog rather than done here. Two ways the obvious placement (a
        # clear at the end of this method) gets it wrong: _run_setup returns
        # BEFORE mainloop() is entered, so it would claim success while the app
        # could still wedge before ever painting; and if anything above blocks —
        # the chooser opening its own window, say — the clear is never reached
        # at all, and a restart that plainly worked keeps its marker (observed,
        # Kent 2026-09-01). The watchdog already computes "a window is
        # viewable", from the event loop, in order to arm itself.
        from frontend.visibility import VisibilityWatchdog, QuitOnlyGuard
        from utilities import restartmark
        self.visibility_watchdog=VisibilityWatchdog(self,
                                        on_first_window=restartmark.clear)
        self.visibility_watchdog.start()
        # Global guard against the nothing-but-Quit page. Same reasoning as the
        # watchdog and started in the same place: that page is bad no matter who
        # produced it, so ask about the SCREEN rather than auditing producers
        # one at a time (Kent 2026-09-01).
        self.quit_only_guard=QuitOnlyGuard(self)
        self.quit_only_guard.start()
    def run(self):
        # global program
        log.info("Running main function on {} ({})".format(platform.system(),
                                        platform.platform())) #Don't translate yet!
        try:
            self.tk_root = ui.Root(program=self)
        except Exception as e:
            log.info(_("Evidently you can’t make a root window? ({error})").format(error=e))
            return
        # Now that a root exists, error notices from worker threads can —
        # and must — be marshaled onto the main thread:
        set_error_handler(self.notify_error_threadsafe)
        set_user_notifier(self.notify_user_threadsafe)
        if self.tkinter:
            # tkinter: setup runs synchronously, then mainloop blocks
            self._run_setup()
            self.tk_root.mainloop()
        else:
            # webview: start event loop first, run setup in background thread
            # after loaded — avoids deadlock from wait_window() before start()
            self.tk_root.mainloop(setup_callback=self._run_setup)
        sysshutdown()
    def maybe_run_problem(self):
        if self.testing and self.me:
            log.info("Not starting up help line")
            # ErrorNotice(_("Not starting up help line"),program=self,wait=True)
            ErrorNotice(_("Not starting up help line"),parent=self.tk_root,wait=True)
            # ErrorNotice(_("Not starting up help line"),wait=True)
            return
            # raise
            # sys.exit()
        self.run_problem()
    def email_log(self,event=None,bundle=None,lastlines=None):
        """Compress this run's log, open a mail draft, and SHOW the user the file.

        Reachable two ways, deliberately: the Help menu (a normal page, nothing
        has gone wrong) and the error page (something has). Until now only the
        error page could package a log at all, so a machine that merely
        MISBEHAVED had no way to hand one over — which is why field diagnosis
        keeps stalling on "ask the linguist to find and send a file".

        THE MAIL DRAFT CANNOT CARRY THE LOG, and that is not a limitation of
        this code: RFC 6068 lists the headers a mailto: handler may honour and
        says attachment parameters must NOT be, since otherwise any web page
        could make a mail client exfiltrate a local file. So the best available
        is: draft addressed and described, and the folder opened with the file
        HIGHLIGHTED, so attaching is one drag with no searching. Naming a path
        in the body is not enough for a field user (Kent 2026-09-02: "I can't
        count on people finding it on their own").

        The previous URL was malformed and reportedly did nothing when clicked.
        Three faults, any one sufficient: NOTHING WAS ENCODED, while 50 raw log
        lines went into the query string — '&' ends the body parameter, '#'
        starts a fragment and drops the rest, a bare '%' is an invalid escape
        that makes handlers reject the whole URI, and spaces and newlines are
        illegal outright; it was TOO LONG, 5-10 kB against the ~2 kB that
        ShellExecute and browsers accept; and the lines were joined with
        '%0d%0a' when readlines() had already left a real newline on each.

        The log no longer travels in the URL. Kent: the 50-line excerpt "has
        been useful in the past" — so the single most identifying line goes in
        the SUBJECT, where it costs nothing and is better placed, because the
        failure is then visible in the inbox and a report can be triaged, and
        duplicates spotted, without opening anything. The error page still
        DISPLAYS all 50, and the attachment holds the whole run."""
        try:
            if bundle is None:
                bundle=str(logsetup.writelzma())
            if lastlines is None:
                try:
                    lastlines=logsetup.contents(50)
                except Exception:
                    lastlines=[]
            failure=''
            for line in reversed([l.strip() for l in lastlines if l.strip()]):
                if 'Error' in line or 'Exception' in line:
                    failure=line[-120:] #the tail: the message, not the prefix
                    break
            subject=_("Please help with {name}").format(name=self.name)
            if failure:
                subject+=': '+failure
            body='\n'.join([
                    _("Please replace this text with a description of what you "
                        "just did."),
                    '',
                    _("IMPORTANT: please attach the file named below. It is "
                        "the only thing that says what went wrong."),
                    str(bundle),
                    ])
            eurl='mailto:{addr}?subject={subject}&body={body}'.format(
                        addr=urllib.parse.quote(str(self.Email)),
                        subject=urllib.parse.quote(subject),
                        body=urllib.parse.quote(body))
            # Show the file FIRST, so it is in front of the user whether or not
            # a mail client exists — the folder is the part that always works.
            reveal_file(bundle)
            def _nomailclient():
                # THE SILENT FAILURE, now spoken (Kent 2026-09-02: "I've seen
                # that silent error before", then watched it happen: folder
                # opened, no mail client, no message). No mail client is
                # configured, so the click genuinely did nothing, which reads as
                # the app ignoring it. Say so, and give the two facts they need:
                # where the file is, and who to send it to.
                NotifyUser(text=_("This computer has no email program set up, "
                            "so {name} could not start a message for you.\n\n"
                            "Please send this file to {addr} yourself — it is "
                            "in the folder that just opened:\n\n{bundle}"
                            ).format(name=self.name,addr=self.Email,
                            bundle=bundle),
                            title=_("No email program"))
            # ASK BEFORE DISPATCHING. Cheap, synchronous, ON THIS THREAD (so the
            # notice below is built where Tk allows it), and it answers before
            # the click has had time to look ignored. mailto_configured() is
            # also the only thing that can answer on Linux at all — xdg-open
            # exits 0 with no handler.
            if mailto_configured() is False:
                _nomailclient()
                return bundle
            def _mail_result(ok):
                if ok is not False:
                    return #took it, or we cannot tell: a false alarm is worse
                # WORKER THREAD — hand the notice to the main loop rather than
                # building a window here. Tk is main-thread-only, and this is
                # exactly how the first version of this warning never appeared.
                root=ui.default_root()
                if root is None:
                    log.info("no mail client, and no root to say so on")
                    return
                root.after(0,_nomailclient)
            open_mailto(eurl,on_result=_mail_result)
            return bundle
        except Exception as e:
            log.exception("could not prepare a log to email")
            try:
                ErrorNotice(_("Could not prepare your log to send ({error}). "
                            "Your log files are in {dir}.").format(
                            error=e,dir=file.getlogdir()),
                            title=_("Couldn’t send the log"))
            except Exception:
                pass
    def run_problem(self):
        # self.restart(), NOT sysrestart(): these two switch the SOURCE BRANCH and
        # then restart, which makes them the likeliest of all the restart callers
        # to fail to come back — a bad checkout means the successor may not start
        # at all. So they get the confirmed path (a held "Restarting…" dialog, and
        # the old copy handed back with an explanation if the new one dies) rather
        # than the fire-and-forget one.
        #
        # NB self.restart() RETURNS, where sysrestart() never did: it opens the
        # wait and schedules the confirm loop. So the destroy() below now actually
        # runs — which is what it was always meant to do and never could.
        def reverttomain(event=None):
            self.source_repo.reverttomain()
            self.restart(reason='revert to main branch')
            revertb.destroy()
        def testversion(event=None):
            self.source_repo.testversion()
            self.restart(reason='switch to testing branch')
            tryb.destroy()
        # global _
        try:
            log.info(_("Starting up help line (with translation)..."))
        except Exception as e:
            log.info("Starting up help line (without translation?)... {}".format(e))
        # if self.testing and self.me:
        #     sys.exit()
        #     exit()
        file=str(logsetup.writelzma())
        try: #Make this work whether root has run/still runs or not.
            newtk=False
            assert hasattr(self,'tk_root')
            assert self.tk_root.winfo_exists()
            log.info(_("Root there!"))
            # errorroot = self.tk_root
            for w in self.tk_root.winfo_children():
                w.destroy()
        except Exception:
            try:
                self.tk_root = ui.Root(program=self)
                self.tk_root.wraplength=int(self.tk_root.winfo_screenwidth()*.7) #exit button
                newtk=True
                log.info(_("Starting with new root"))
            except Exception as e:
                log.info(_("Evidently you can’t make a root window? ({error})").format(error=e))
                log.info(_("This was your error:\n{error}").format(error=logsetup.contents(50)))
                return
        self.tk_root.withdraw()
        errorw=ui.Window(self.tk_root)
        errorw.title(_("Serious Problem!"))
        errorw.mainwindow=True
        l=ui.Label(errorw.frame,text=_("Hey! You found a problem! (details and "
                "solution below)"),justify='left',font='title',
                row=0,column=0
                )
        if False and self.exceptiononload:
            durl='{}/INSTALL.md#dependencies'.format(self.docsurl)
            m=ui.Label(errorw.frame,text=_("\nPlease see {url}").format(url=durl),
                justify='left', font='instructions',
                row=1,column=0
                )
            m.bind("<Button-1>", lambda e: openweburl(durl))
            m2=ui.Label(errorw.frame,
                text=_("I have tried to install some Python dependencies for you. "
                        "If everything but ‘patiencediff’ installed "
                        "(see log below), just close this window and {azt} "
                        "will restart. "
                        "\nIf you see connectivity errors, check your internet "
                        "connection before running {azt} again; we need to "
                        "download some stuff for this.").format(azt=self.name),
                justify='left', font='instructions',
                wraplength=errorroot.wraplength,
                row=2,column=0
                )
        lcontents=logsetup.contents(50)
        addr=self.Email
        def _email_log(event=None):
            self.email_log(bundle=file,lastlines=lcontents)
        n=ui.Label(errorw.frame,text=_("\n\nIf this information doesn’t help "
            "you fix this, click this text to Email me your log (to {addr}). "
            "Your log file will also be shown in a folder window — please "
            "attach it to the message."
            "").format(addr=addr),justify='left', font='default',
            row=5,column=0
            )
        n.bind("<Button-1>", _email_log)
        o=ui.Label(errorw.frame,text=_("The end of {log} / {file} are below:"
                                    "").format(log=logsetup.getlogfilename(),file=file),
                                    justify='left',
                                    font='report',
                                    row=3,column=0,
                                    sticky='w')
        scroll=ui.ScrollingFrame(errorw.frame,row=4,column=0)
        """Norender here keeps this from dying on complex characters in the log."""
        o=ui.Label(scroll.content,text=''.join(lcontents), norender=True,
                    justify=ui.LEFT,
                    font='report',
                    row=0,column=0)
        o.wrap()
        if not self.me:
            o.bind("<Button-1>", lambda e: openweburl(eurl))
        scroll.reflow()  # grow canvas/scrollregion to the wrapped log label
        scroll.tobottom()
        f=ui.Frame(errorw.outsideframe,row=1,column=2)
        buttonwraplength=75
        if (hasattr(self,'source_repo')
                and hasattr(self.source_repo,'files')): #repo init succeeded
            ui.Button(f,
                    text=_("Check for {azt} updates").format(azt=self.name),
                    cmd=lambda x=errorw:self.updateazt(parent=x),
                    wraplength=buttonwraplength,
                    row=0,column=0,
                    pady=20)
            if getattr(self.source_repo,'branch','main') != 'main':
                revertb=ui.Button(f,
                        text=_("Revert to main branch of {azt}").format(azt=self.name),
                        cmd=reverttomain,
                        wraplength=buttonwraplength,
                        row=1,column=0,
                        pady=20)
            else:
                tryb=ui.Button(f,
                        text=_("Try testing branch of {azt}").format(azt=self.name),
                        cmd=testversion,
                        wraplength=buttonwraplength,
                        row=1,column=0,
                        pady=20)
        ui.Button(f,text=_("Restart {azt}").format(azt=self.name),
                    cmd=sysrestart, #This should be in task/chooser
                    wraplength=buttonwraplength,
                    row=2,column=0,
                    pady=20)
        errorw.wait_window(errorw)
        if newtk: #likely never work/needed?
            self.tk_root.mainloop() #This has to be the last thing
    def task_base(self):
        if not self.task:
            return "No task"
        cvt=self.params.cvt()
        name=self.task.__class__.__name__
        # cvt is None on a fresh project before any cvt-bearing task
        # has run (the chooser doesn't seed params.cvt) — normal, not
        # an anomaly; crashed TaskChooser init via the base.py boot
        # log line (field 2026-07-17, fresh project copy).
        if cvt and cvt in name:
            return name[:-len(cvt)]
        if getattr(self.task,'cvt_sensitive',False) \
                and name.endswith(('S','T')):
            # params.cvt out of sync with a cvt-suffixed task class;
            # the class name itself carries the suffix.
            return name[:-1]
        if cvt:
            log.info(f"cvt {cvt} not in task name {name}; "
                     "not sure how to derive a base")
        return name
    def reload_database(self):
        """A5 (in-place reload): re-read the LIFT from disk and rebuild
        everything derived from it — no process restart. Used when the
        collab daemon merged team changes under us.

        DESTROY NOTHING (lesson of the first live run, 2026-07-10): the
        whole session runs NESTED inside the boot stack's wait_window
        event loops (_run_setup → TaskChooser.__init__ → maketask → …),
        and the chooser's window is effectively the application's main
        window — destroying it killed the Tk app, and the resumed outer
        frames then crashed on Tk calls a try/except here cannot catch.
        So: rebuild the BACKEND objects only (program.* swaps under the
        live UI), then swap the task view with the SAME machinery a
        user's task switch exercises daily — maketask() launches the
        new task, whose window-init retires the old task's UI
        (i_am_mainwindow → finish_task_ui), and the old frames unwind
        through their proven exit branches. The user's position
        (current check/group/slice) is durable state, so re-entering
        the same task class resumes close to where they were. Failures
        BEFORE the task swap fall back to the trusted full restart."""
        log.info("In-place reload: starting")
        w=None
        try: #cover the seconds of synchronous rebuild with a wait dialog
            w=self.taskchooser.ui
            w.wait(_("Loading your team’s changes…"))
            w.update() #paint it NOW: the rebuild blocks the event loop, so
            #           without one draining update() it stays black (2026-07-11)
        except Exception as e:
            log.info("reload: no wait dialog (%s)",e)
            w=None
        try:
            # Quiesce writes (as restart() does): the reload must read a
            # settled file, and no write thread may straddle the db swap.
            if self.towrite:
                self.maybewrite(definitely=True)
            while self.writing:
                log.info(_("Waiting to finish writing to lift"))
                time.sleep(1)
                self.check_if_write_done()
            prev_task_class=None
            task=getattr(self,'task',None)
            if task is not None and task is not getattr(self,'taskchooser',None):
                prev_task_class=type(task)
            # Rebuild: boot-parity with _run_setup's post-FileParser
            # chain (same constructors, same order; presenters/root/
            # theme/langtags/TaskChooser are process-lifetime and stay).
            FileParser(self)
            if getattr(self,'collab',None):
                self.collab.adopt_reloaded_db()
            # Make the rebuild BOOT-LIKE for the settings push (2026-07-11
            # DATA-WIPE root cause): moveattrstoobjects pushes each stored
            # value into its object ONCE per Settings instance. At boot,
            # params/slices/alphabet don't exist when Settings initializes,
            # so the push correctly waits for them. On reload the OLD objects
            # still existed → the push fired into them, consumed itself, and
            # the NEW Alphabet starved — whose init-save then wrote EMPTY
            # glyph data over alphabet.json (wiped Kent's verified letters,
            # 16:18). Deleting the stale objects first restores boot order.
            for _stale in ('alphabet','params','slices','status','examples',
                           'profiles'):
                if hasattr(self,_stale):
                    delattr(self,_stale)
            ToneFrames(self)
            Settings(self)
            CheckParameters(self)
            self.settings.post_lift_init()
            ProfileAnalyzer(self)
            ExampleDict(self)
            Alphabet(self)
            UISettings(self)
            # Boot-parity tail: at boot TaskChooser.__init__ runs these BEFORE
            # any task exists — whatsdone() (task-availability state) and
            # profiles.run() (derives profiles AND builds profiles.rxdict,
            # which Task __init__ reads). The reload keeps the chooser, so run
            # them here explicitly.
            self.taskchooser.whatsdone()
            self.profiles.run()
            self.status_dirty=True #force the first maybesort to rebuild
        except Exception as e:
            log.error("In-place reload failed before the task swap (%s); "
                      "falling back to a full restart.", e)
            self.restart()
            return
        finally:
            if w is not None:
                try:
                    w.waitdone()
                except Exception:
                    pass
        # Task swap OUTSIDE the try: from here the app must ride the
        # normal task-switch path; a restart from these depths is what
        # crashed run one.
        log.info("In-place reload: backend rebuilt; swapping task view "
                 "(%s)", prev_task_class)
        # Retire the OLD task's window BEFORE launching the new one:
        # maketask() does not return until the new task ENDS (the task's
        # life nests inside it), so nothing after it can clean up — and
        # leaving the old window alive gave two TaskWindows whose shared
        # exit closed the whole app (2026-07-11 morning). on_quit is NOT
        # the tool (it revives the chooser / quits toward root — the
        # 16:42 ghost shutdown): _dismiss_unshown is the purpose-built
        # silent board teardown for "another task is taking over".
        old=getattr(self,'task',None)
        if old is not None and old is not self.taskchooser:
            # Anchor hand-off: tasks that track a within-task position (e.g.
            # the record page loop) expose it as _record_anchor; the relaunch
            # consumes program._reload_anchor to resume there — the "user
            # barely notices the reload" bar.
            self._reload_anchor=getattr(old,'_record_anchor',None)
            try:
                old._dismiss_unshown()
            except Exception as e:
                log.info("reload: old task dismiss: %s",e)
        self.task=None
        if prev_task_class is not None:
            self.taskchooser.maketask(prev_task_class)
        else:
            self.taskchooser.gettask() #re-present the chooser
        log.info("In-place reload: done")
    def restart(self,filename=None,reason=None):
        # `reason` reaches the restart marker, and it is the field worth having:
        # an update that fails to come back is a different diagnosis from a
        # branch switch that does. Callers that don't say get 'App.restart',
        # which at least distinguishes this path from the menu buttons.
        log.info(_("Restarting from App"))
        file.writefilename(self.filename)
        for loc in [self,self.mainwindow]:
            if hasattr(loc,'warning') and loc.warning.winfo_exists():
                loc.warning.destroy()
        # log.info("towrite: {}; writing: {}".format(self.towrite,self.writing))
        if self.towrite: #Do even if not closed by user
            log.info(_("Final write to lift"))
            self.maybewrite(definitely=True)
        # NO withdraw(), and no time.sleep() loop. Both were here to stop the
        # user acting during the wait, and together they produced the failure
        # this whole item exists for: every window hidden, and a dead main loop
        # so nothing — not after(), not a repaint, not either visibility guard —
        # could run or report. A WAIT DIALOG does the same job honestly: it
        # blocks input, it says what is happening, and it is the one thing both
        # guards accept as "something is happening and the user is being told".
        self._restart_reason=reason or 'App.restart'
        self._restart_child=None
        self._restart_childgone=None
        # Set BEFORE the wait opens: from here on this process is handing over,
        # so background work that touches the project must stop (collab_poll
        # checks this). Cleared only by _restart_failed, where we genuinely are
        # the live copy again.
        self._restarting=True
        w=self._restart_holder()
        if w is not None:
            try:
                w.wait(msg=_("Restarting {name}…").format(name=self.name))
            except Exception as e:
                log.info("no restart wait dialog: %s",e)
        self._await_write_then_restart()
    def _restart_holder(self):
        """The window that holds the "Restarting…" dialog and, if the restart
        fails, is handed back to the user. The task if there is one, else the
        chooser — the same preference order the visibility watchdog uses."""
        for owner in (getattr(self,'task',None),getattr(self,'taskchooser',None)):
            if owner is None:
                continue
            win=getattr(owner,'ui',owner)
            try:
                if win.winfo_exists():
                    return win
            except Exception:
                continue
        return None
    RESTART_POLL_MS=500
    RESTART_EXIT_GRACE_S=15 #a successor may re-exec once (venv relaunch)
    RESTART_BACKSTOP_S=300
    def _await_write_then_restart(self):
        """Drive the write-wait from after(), not sleep(). Same wait, but the
        event loop stays alive — which is the prerequisite for everything below:
        a dialog that can paint, and a confirm loop that can run at all."""
        if self.writing:
            log.info(_("Waiting to finish writing to lift"))
            self.check_if_write_done()
            self.tk_root.after(1000,self._await_write_then_restart)
            return
        self._spawn_and_confirm()
    def _spawn_and_confirm(self):
        from utilities.utilities import spawn_successor
        self._restart_child=spawn_successor(reason=self._restart_reason)
        if self._restart_child is None:
            # The launch itself failed, so there is no successor to wait for and
            # we are still a working app. Say so and stay up; a silent return to
            # a half-torn-down UI is what we are trying to stop.
            self._restart_failed(_("Could not start a new copy of {name}. "
                        "Your work is saved and this window is still usable."
                        ).format(name=self.name))
            return
        from utilities import restartmark
        if restartmark.pending() is None:
            # No marker means no signal: its DISAPPEARANCE is what we wait on,
            # so an absent one would read as instant confirmation of a successor
            # that has not started. The successor is already launched and this
            # is only a diagnostic failure, so hand over the old way rather than
            # pretending to confirm.
            self._leave_to_successor("no restart marker to watch (could not be "
                    "written); handing over unconfirmed")
            return
        self._restart_started=time.monotonic()
        self._confirm_restart()
    def _confirm_restart(self):
        """Wait for the successor to say it is up, and recover if it cannot.

        THE SIGNAL IS THE MARKER: level 1 already has the successor delete it
        once a real work surface is on screen, so its disappearance is exactly
        "I am up" — no second channel, and the thing we wait for is the thing we
        actually care about (a window the user can use), not merely a process
        that exists.

        The failure we can detect precisely is the successor EXITING, which
        poll() reports at once — far better than a wall-clock timeout, which on
        a slow machine with a big lexicon would cry failure on a boot that was
        simply taking its time. But an exited child is not proof on its own: a
        successor may legitimately re-exec once (the venv relaunch Popens and
        exits), orphaning a grandchild we cannot see. So an exit only counts
        after a grace period in which the marker is still uncleared."""
        from utilities import restartmark
        try:
            if restartmark.pending() is None:
                self._leave_to_successor("successor confirmed up")
                return
            if self._restart_child.poll() is not None:
                now=time.monotonic()
                if self._restart_childgone is None:
                    self._restart_childgone=now
                    log.info("successor process exited; waiting %ss in case it "
                            "re-execed (venv relaunch) before calling it a "
                            "failure",self.RESTART_EXIT_GRACE_S)
                elif now-self._restart_childgone>self.RESTART_EXIT_GRACE_S:
                    self._restart_failed(_("{name} could not restart: the new "
                            "copy stopped before it opened. Your work is saved "
                            "and this window is still usable."
                            ).format(name=self.name))
                    return
            elif time.monotonic()-self._restart_started>self.RESTART_BACKSTOP_S:
                # Still running after a very long time. Do NOT hand the UI back:
                # two live copies on one project is worse than a long wait, and
                # the successor owns the project from here.
                self._leave_to_successor("successor still unconfirmed after "
                        "{}s but alive; leaving anyway rather than risk two "
                        "live copies".format(self.RESTART_BACKSTOP_S))
                return
        except Exception:
            log.exception("restart confirmation failed")
        self.tk_root.after(self.RESTART_POLL_MS,self._confirm_restart)
    def _leave_to_successor(self,why):
        """Hand the machine over and GO, from inside an after() callback.

        `sys.exit()` DOES NOT WORK HERE, and that is the bug this method exists
        for: tkinter catches exceptions raised in a callback (and this app adds
        its own catcher in frontend/tkintermod.py), so the SystemExit was
        swallowed and the callback simply returned. Both exit paths of
        _confirm_restart — the confirmed one and the 300s backstop — therefore
        did nothing, and the predecessor sat there indefinitely: Kent's
        duplicate-process gate found two live copies, 1934s and 1216s old, on
        one project (2026-09-01). Two live copies is the exact outcome the
        confirm loop was written to prevent, so it was worse than no handshake.

        quit() ends the main loop instead, and App.run() falls through to
        sysshutdown() at top level, where sys.exit() means something. No final
        write on the way out, deliberately: the successor owns the project now,
        and this process already wrote before it spawned."""
        log.info("%s; predecessor leaving",why)
        try:
            self.tk_root.quit()
        except Exception:
            # Nothing left to be careful with: the successor is up, this copy
            # must not linger, and os._exit skips the interpreter shutdown that
            # a wedged Tk could otherwise block.
            log.exception("could not end the main loop; forcing exit")
            os._exit(0)
    def _restart_failed(self,text):
        """Give the user their window back, and say why. This is the whole point
        of level 2: a failed restart becomes a sentence instead of a blank
        screen."""
        log.error("RESTART FAILED: %s",text)
        # We are the live copy again, so background work resumes. Do this first:
        # everything below can raise, and a stuck _restarting flag would leave a
        # working app quietly not polling.
        self._restarting=False
        w=self._restart_holder()
        if w is not None:
            try:
                w.waitdone()
                if not w.exitFlag.istrue():
                    w.deiconify()
            except Exception:
                log.exception("could not restore the UI after a failed restart")
        try:
            ErrorNotice(text,title=_("Restart failed"))
        except Exception:
            log.exception("could not report the failed restart")
    def prep_to_write(self):
        self.writeable=0 #start the count
        self.towrite=False
        self.writing=False
        self.status_dirty=True #force first status rebuild; see maybesort
    def maybewrite(self,definitely=False):
        #Any call here means a LIFT mutation just happened, so the sorting
        #status derived from LIFT is now stale. maybesort clears this after it
        #rebuilds, and skips its rebuild while it stays False.
        self.status_dirty=True
        write=self.timetowrite() #just call this once!
        #this currently defaults to write every time asked; can up writeeverynwrites when stable.
        if (write or definitely) and not self.writing:# or definitely:bad idea to overwrite write
            self._write()
        elif write:
            # log.info(_("Already writing to lift; I trust this new mod will "
            #         "get picked up later..."))
            #This tells A−Z+T that something hasn't been written yet, so it will force a write on shutdown.
            self.towrite=True
            # self.schedule_write()
    def schedule_write_check(self):
        """Schedule `check_if_write_done()` function after x seconds."""
        x=1 #delay (seconds)
        # log.info("Scheduling check after {x} seconds")
        self.tk_root.after(x*1000, self.check_if_write_done)
        # log.info("Scheduled check")
        # self.taskchooser.after(5000, self.check_if_write_done, t)
    def check_if_write_done(self):
        # If the thread has finished, allow another write.
        # log.info("Checking if writing done to lift.")
        try:
            done=not self.writethread.is_alive()
        except AttributeError:
            done=True
        except Exception as e:
            log.info(_("Exception: {error}").format(error=e))
            log.info(_("writethread: {exists}").format(exists=hasattr(self,'writethread')))
        if done:
            log.info(_("Done writing to lift ({status}).").format(status=self.db.write_OK))
            if not self.db.write_OK:
                ErrorNotice(_("Write to lift returned "
                            "‘{error}’.").format(error=self.db.write_error),wait=True)
            self.writing=False
            if self.towrite:
                log.info(_("Found previous request to write; doing again."))
                self._write()
            else:
                self.repo_commit()
        else:
            # Otherwise check again later.
            # log.info("schedule_write_check writing to lift.")
            self.schedule_write_check()
    def timetowrite(self):
        """only write to file every self.writeeverynwrites times you might.
        current default is every write possible (writeeverynwrites=1)
        change this in your project settings if your power is stable and you
        want to write less."""
        self.writeable+=1 #and tally here each time this is asked
        return not self.writeable%self.settings.writeeverynwrites
    def _write(self):
        self.towrite=False
        self.writethread = threading.Thread(target=self.db.write)
        self.writing=True
        log.info(_("Writing to lift..."))
        self.writethread.start()
        self.schedule_write_check()
    def runtime_to_now(self):
        #this returns a delta!
        return times.now()-self.start_time
    def check_for_theme(self):
        hard_themes={'CS-477':'pink',
                    'karlap':'Kim' if not self.production else None}
        #check if theme exists
        self.theme=file.uitheme()
        if not self.theme:
            self.theme=hard_themes.get(platform.uname().node,None)
        log.info(f"Using theme {self.theme}")
    def notify_error_threadsafe(self,text,**kwargs):
        """ErrorNotice builds Tk widgets, so a call from a worker thread
        (e.g. updateazt's git thread) is marshaled to the main thread via
        after(); those callers get None back instead of the window."""
        if threading.current_thread() is threading.main_thread():
            return frontend.error_notice.ErrorNotice(text,**kwargs)
        log.info(_("Marshaling error notice from thread {name}: {text}"
                    ).format(name=threading.current_thread().name,text=text))
        self.tk_root.after(0,lambda:frontend.error_notice.ErrorNotice(text,**kwargs))
    def notify_user_threadsafe(self,text,**kwargs):
        """Same marshaling as notify_error_threadsafe: the status window is Tk
        widgets, so a worker thread must not append to it directly."""
        if threading.current_thread() is threading.main_thread():
            return frontend.status_window.notify_user(text,**kwargs)
        log.info(_("Marshaling status message from thread {name}: {text}"
                    ).format(name=threading.current_thread().name,text=text))
        self.tk_root.after(0,
                lambda:frontend.status_window.notify_user(text,**kwargs))
    def updateazt(self,event=None,**kwargs): #kwargs should only be parent, for errorroot
        log.info(_("Updating {azt}").format(azt=self.name))
        if not hasattr(self.source_repo, 'files'): #set only when repo init succeeded
            log.info(_("No usable {azt} source repository; not updating."
                        ).format(azt=self.name))
            return
        parent=kwargs.get('parent')
        if not parent or not parent.winfo_exists(): #take kwarg if there
            kwargs['parent']=getattr(self, 'mainwindow', None) or self.tk_root
        log.info(_("parent title: {title}").format(title=kwargs['parent'].title()))
        # The git work is network-bound and must not starve the mainloop
        # (inert dialogs); it runs on a worker thread, while every window
        # (wait, notices, output) is made here on the main thread.
        kwargs['parent'].wait(msg=_("Updating {azt}").format(azt=self.name))
        results={}
        def work():
            from utilities import sister_repos
            try:
                results['r']=self.source_repo.share() #dict of main+testing results
                # Sister repos ride along with every azt update — a Windows
                # field machine has no other path to server/client (azt-collab)
                # updates; nobody runs git in a shell there.
                results['sisters']=sister_repos.update_all()
            except Exception as e:
                log.exception(_("Update failed: {error}").format(error=e))
                results['error']=e
        worker=threading.Thread(target=work,name='updateazt',daemon=True)
        worker.start()
        def poll():
            if worker.is_alive():
                self.tk_root.after(200,poll)
                return
            kwargs['parent'].waitdone()
            self.updateaztdone(results,**kwargs)
        self.tk_root.after(200,poll)
    def updateaztdone(self,results,**kwargs):
        """Main-thread half of updateazt: interpret the worker's results
        and show them."""
        def tryagain(event=None):
            kwargs['tryagain']=True
            self.updateazt(**kwargs)
        retrying=kwargs.get('tryagain')
        if 'error' in results:
            ErrorNotice(_("Problem updating {azt}: {error}"
                        ).format(azt=self.name,error=results['error']),
                        parent=kwargs.get('parent'))
            return
        r=results.get('r')
        sisters=results.get('sisters',{})
        from utilities import sister_repos
        if r:
            t='\n'.join([i for j in r.items() #each tuple
                        for k in j #each tuple item
                        if k #don't give empty items
                        for i in [l for l in k.split('\n')# each tuple item line
                                if 'hint: ' not in l][:10] #first 10 w/o hint
                                ])
        else:
            self.source_repo.clonetoUSB()
            # Retry once, and only if clonetoUSB actually yielded a
            # source — an exited/refused media prompt must not loop.
            if not retrying and self.source_repo.localremotes():
                tryagain()
            return
        for sname,(sok,scode,sout) in sisters.items():
            t+='\n{}: {}'.format(sname,sister_repos.describe(scode))
        if sisters.get('azt-collab',(False,'',''))[1]=='updated':
            # The daemon is detached and outlives azt restarts; new
            # server code does nothing until it is bounced.
            from backend.core import collab
            # COVER THIS. The update's wait is closed back in updateazt's poll,
            # BEFORE this method runs — so this daemon bounce, which is network
            # work and can take tens of seconds, ran with every window withdrawn
            # and nothing on screen. The global watchdog caught it on a fresh
            # clone: "found no viewable window in 5 polls (25.0s)", with the Wait
            # withdrawn too and two task windows sitting there content=True,
            # unrevealed (Kent's log, 2026-09-01). thenshow=True so waitdone also
            # puts a window back, which is the half that was missing.
            parent=kwargs.get('parent')
            try:
                if parent is not None:
                    parent.wait(msg=_("Restarting the collaboration service…"),
                                thenshow=True)
            except Exception as e:
                log.info("could not cover the daemon restart: %s",e)
            try:
                bounced=collab.restart_collab_daemon()
            finally:
                try:
                    if parent is not None:
                        parent.waitdone()
                except Exception as e:
                    log.info("could not close the daemon-restart wait: %s",e)
            if bounced:
                t+='\n'+_("(Collaboration service restarted with its "
                            "update)")
        button=False
        if internetconnectionproblemin(t):
            if retrying:
                t=t+'\n'+_("Insert USB with A−Z+T source")
                button=(_("USB inserted"),self.source_repo.clonetoUSB)
            else:
                t=t+_('\n(Check your internet connection and try again)')
                button=(_("Try Again"),tryagain)
        elif not self.me:
            if [i for i in r.values() if 'fatal: ' in i]: #any fatal problem
                t+='\n'+_("(Problem! You will likely need help with this.)")
            elif [i for i in r.values() if updated(i)]: #anything updated
                t+='\n'+_("(Restart {name} to use this update)"
                        ).format(name=self.name)
            if [i for i in r.values() if not uptodate(i)] \
                    or any(s[1]=='updated' for s in sisters.values()):
                # sister 'updated' needs a restart too: azt has the old
                # azt_collab_client already imported in-process.
                # reason=: this is the restart most worth naming in a marker —
                # a restart AFTER AN UPDATE is the one whose failure to come back
                # strands the user on a half-updated install. Without it the
                # marker said 'unspecified' (Kent's log, 2026-09-01).
                button=(_("Restart Now"),
                        lambda event=None:sysrestart(reason='after update'))
        try:
            try:
                title=_("Update (Git) output")
            except Exception: #in case translation isn't working yet
                title="Update (Git) output"
            ErrorNotice(t,title=title,button=button,wait=True,
                        parent=kwargs.get('parent'))
        except Exception:
            log.info(set(kwargs.keys()))
            log.info(set(['parent']))
    def __init__(self,program):
        sys.excepthook = self.handle_exception
        self.show_scaling_from_windows()
        self.file = file.getfile(__file__)
        if hasattr(sys,'_MEIPASS') and sys._MEIPASS is not None:
            self.aztdir=sys._MEIPASS #android?
        else:
            self.aztdir=self.file.parent
        self.className='azt'
        # if self.hostname == 'karlap':
        for k,v in program.items():
            setattr(self,k,v)
        self.default_task='WordCollectnParse'
        self.loglevel=logsetup.loglevel_default #'INFO'
        if self.aztdir.parent.stem == 'AZT': 
            self.testing=True #eliminates Error screens and zipped logs and repo commits
            # self.production=True #True for making screenshots (default theme)
            self.me=True
            self.testlift='Demo_en' #portion of filename
            # self.testtask='SortT' #Will convert from string to class later
            self.testtask='SortV' #Will convert from string to class later
            # self.testtask='SortSyllables' #Will convert from string to class later
            # self.testtask='WordCollectnParsewRecordings'
            # self.default_task='WordCollectnParse'
        else:
            self.me=False
            self.production=True #True for making screenshots (default theme)
            self.testing=False #True eliminates Error screens and zipped logs
            # self.loglevel='INFO'
            # self.default_task='WordCollectnParse'
        logsetup.setlevel(self.loglevel) #update to value just set
        self.get_interface_languages()
        self.check_for_theme()
        #This isn't helpful where things are copied to disk later:
        self.modified_time=times.modified(self.file)
        self.modified_time_relative=f'{times.now()-self.modified_time} ago'
        self.disclosure()
        self.find_source_repo()
        #'sendpraat' now in 'praat', if useful
        try:
            assert not self.exceptiononload or self.me
            #Don't worry about these if exceptiononload:
            for exe in ['praat', 'ffmpeg', 'lame']:
                result=file.findexecutable(exe)
                if isinstance(result, (str, Exception)) and not file.exists(result):
                    log.info(result)
                    result=None
                setattr(self,exe,result)
            self.python=sys.executable
            self.run()
        except SystemExit:
            log.info(_("Shutting down by user request"))
        except KeyboardInterrupt:
            log.info(_("Shutting down by keyboard interrupt"))
        except AssertionError as e:
            log.exception(_("Module loading failed! {error}").format(error=e))
            self.maybe_run_problem()
        except Exception as e:
            log.exception(_("Unexpected exception! {error}").format(error=e))
            self.maybe_run_problem()
        except BaseException:
            import traceback
            log.error("uncaught exception: %s", traceback.format_exc())
            self.maybe_run_problem()
        sys.exit()
from io_put.cawl import loadCAWL  # moved; re-exported for compatibility
if __name__ == '__main__':
    App(program)
