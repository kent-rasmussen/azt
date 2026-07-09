#!/usr/bin/env python3
# coding=UTF-8
"""Consider making the above work for a venv"""
"""This file runs the actual GUI for lexical file manipulation/checking"""
import utilities.py_modules #This tries importing, and installs on failure
from utilities import duplicates
if duplicates.running_file(__file__):
    exit()
program={'name':'A-Z+T',
        'tkinter':True, #for some day
        'production':False, #True for making screenshots (default theme)
        'testing':False, #normal error screens and logs
        'Demo':False, #will get set otherwise later if it is
        'version':'1.8.5', #This is a string...
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
    program['nosound']=False
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
from utilities.error_handler import set_error_handler
import frontend.error_notice 
set_error_handler(frontend.error_notice.ErrorNotice)
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
                    log.info(_("locale.getlocale doesn't seem to have "
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
            file.uilang(lang)
            return lang
        return curlang
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
                elif r == 'git' and hasattr(self,'git') and self.git:
                    #don't worry about hg, if not there already
                    log.info(_("No Git data repository found; creating."))
                    repo[r].init()
                    repo[r].add(self.liftfilename)
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
        — it only bounds how long stale peer data stays displayed."""
        session=getattr(self,'collab',None)
        if not session:
            return #project disconnected mid-session; stop polling
        try:
            outcome=session.poll_remote_change()
            if (outcome == 'changed'
                    and not getattr(self,'writing',False)
                    and session.reload_offer_due()):
                self.collab_offer_reload()
        except Exception as e:
            log.info(f"collab_poll: {e}")
        self.tk_root.after(10000, self.collab_poll)
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
        self._collab_offer_win = notify_error(
            _("Your team made changes to this database. Loading them "
              "requires {name} to restart — or press OK to keep "
              "working and load them later. Your saves are safe "
              "either way, and will be combined with your team's."
              ).format(name=self.name),
            title=_("Team changes available"),
            button=(_("Load now (restart)"),
                    lambda event=None: self.restart()))
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
    def _run_setup(self):
        """All setup that must happen after the UI event loop is live.

        For tkinter this runs synchronously before mainloop().
        For pywebview this runs in a background thread after webview.start()
        has loaded, so that blocking calls like wait_window() can work.
        """
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
    def run(self):
        # global program
        log.info("Running main function on {} ({})".format(platform.system(),
                                        platform.platform())) #Don't translate yet!
        try:
            self.tk_root = ui.Root(program=self)
        except Exception as e:
            log.info(_("Evidently you can't make a root window? ({error})").format(error=e))
            return
        if program['tkinter']:
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
    def run_problem(self):
        def reverttomain(event=None):
            self.source_repo.reverttomain()
            sysrestart()
            revertb.destroy()
        def testversion(event=None):
            self.source_repo.testversion()
            sysrestart()
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
                log.info(_("Evidently you can't make a root window? ({error})").format(error=e))
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
                        "If everything but 'patiencediff' installed "
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
        eurl='mailto:{addr}?subject=Please help with {name} installation'.format(addr=addr,
                                                                    name=self.name)
        eurl+='&body='
        eurl+=_("Please replace this text with a description of what you just did.")
        eurl+='%0d%0a'
        eurl+=_("If the log below doesn't include the text '{text}', or if it happened "
                "after a longer work session, please attach "
                "your compressed log file").format(
                text='Traceback (most recent call last): ')+' ('+(file)+')'
        eurl+='%0d%0a--log info--%0d%0a{info}'.format(info='%0d%0a'.join(lcontents))
        n=ui.Label(errorw.frame,text=_("\n\nIf this information doesn't help "
            "you fix this, please click on this text to Email me your log (to {addr})"
            "").format(addr=addr),justify='left', font='default',
            row=3,column=0
            )
        n.bind("<Button-1>", lambda e: openweburl(eurl))
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
        if hasattr(self,'git') and self.git:
            ui.Button(f,
                    text=_("Check for {azt} updates").format(azt=self.name),
                    cmd=lambda x=errorw:updateazt(parent=x),
                    wraplength=buttonwraplength,
                    row=0,column=0,
                    pady=20)
            if self.repo.branch != 'main':
                revertb=ui.Button(f,
                        text=_("Revert to main branch of {azt}").format(azt=program.name),
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
        if cvt in name:
            return name[:-len(cvt)]
        else:
            log.info(f"cvt {cvt} not in task name {name}; not sure how to derive a base")
    def restart(self,filename=None):
        log.info(_("Restarting from App"))
        file.writefilename(self.filename)
        for loc in [self,self.mainwindow]:
            if hasattr(loc,'warning') and loc.warning.winfo_exists():
                loc.warning.destroy()
        # log.info("towrite: {}; writing: {}".format(self.towrite,self.writing))
        if self.towrite: #Do even if not closed by user
            log.info(_("Final write to lift"))
            self.maybewrite(definitely=True)
        try:
            self.task.withdraw() #so users don't do stuff while waiting
        except (AttributeError, Exception):
            log.info("There doesn't seem to be a task to hide; moving on.")
        try:
            self.task.runwindow.withdraw() #so users don't do stuff while waiting
        except (AttributeError, Exception):
            log.info(_("There doesn't seem to be a runwindow to hide; moving on."))
        while self.writing:
            # log.info("towrite: {}; writing: {}; taskwrite: {}".format(
            #     self.towrite,self.writing,self.taskchooser.writing))
            log.info(_("Waiting to finish writing to lift"))
            time.sleep(1)
            self.check_if_write_done() #because after() isn't working here...
        # log.info("Not writing to lift")
        sysrestart()
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
                            "'{error}'.").format(error=self.db.write_error),wait=True)
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
    def __init__(self,program):
        # globals()['program'] = self  # replace dict with App; LazyGlobal resolves to self
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
            self.testtask='SortC' #Will convert from string to class later
            # self.testtask='SortV' #Will convert from string to class later
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
def updateazt(event=None,**kwargs): #should only be parent, for errorroot
    def tryagain(event=None):
        kwargs['tryagain']=True
        updateazt(**kwargs)
    log.info(_("Updating {azt}").format(azt=program.name))
    tryagain=kwargs.get('tryagain')
    if hasattr(program, 'git'):
        parent=kwargs.get('parent')
        if not parent or not parent.winfo_exists(): #take kwarg if there
            if hasattr(program, 'taskchooser'):
                kwargs['parent']=program.taskchooser.mainwindowis
            else:
                kwargs['parent']=program.tk_root
        log.info(_("parent title: {title}").format(title=kwargs['parent'].title()))
        w=ui.Wait(msg=_("Updating {azt}").format(azt=program.name), **kwargs)
        r=program.source_repo.share() #t is a dict of main and testing results
        w.close()
        if r:
            t='\n'.join([i for j in r.items() #each tuple
                        for k in j #each tuple item
                        if k #don't give empty items
                        for i in [l for l in k.split('\n')# each tuple item line
                                if 'hint: ' not in l][:10] #first 10 w/o hint
                                ])
        else:
            program.source_repo.clonetoUSB()
            tryagain()
            return
        button=False
        if internetconnectionproblemin(t):
            if tryagain:
                t=t+'\n'+_("Insert USB with A−Z+T source")
                button=(_("USB inserted"),program.source_repo.clonetoUSB)
            else:
                t=t+_('\n(Check your internet connection and try again)')
                button=(_("Try Again"),tryagain)
        elif not program.me:
            if [i for i in r.values() if 'fatal: ' in i]: #any fatal problem
                t+='\n'+_("(Problem! You will likely need help with this.)")
            elif [i for i in r.values() if updated(i)]: #anything updated
                t+='\n'+_("(Restart {name} to use this update)"
                        ).format(name=program.name)
            if [i for i in r.values() if not uptodate(i)]:
                button=(_("Restart Now"),sysrestart)
        try:
            try:
                title=_("Update (Git) output")
            except Exception: #in case translation isn't working yet
                title="Update (Git) output"
            ErrorNotice(t,title=title,button=button,wait=True,**kwargs)
        except Exception:
            log.info(set(kwargs.keys()))
            log.info(set(['parent']))
if __name__ == '__main__':
    App(program)
