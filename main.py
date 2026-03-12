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
        'version':'1.0.5', #This is a string...
        'testversionname':'testing', #always have some real test branch here
        'url':'https://github.com/kent-rasmussen/azt',
        'Email':'kent_rasmussen@sil.org',
        'exceptiononload':False #for now
        }
# program['testing']=True # eliminates Error screens and zipped logs, repos
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
loglevel='INFO'
from utilities.utilities import *
from utilities import logsetup
log=logsetup.getlog(__name__) #not ever a module
logsetup.setlevel(loglevel)
"""My modules, which should log as above"""
from io_put import lift, xlp, export
#import openclipart
# import profiles #confirm obsolescence and remove!
# import setdefaults
# import urls
from utilities import htmlfns, rx, executables
from backend import langtags,parser
from frontend import alphabet_chart
from frontend import alphabet_comparison
import settings
import migration
program['languages']=langtags.Languages()
try:
    from io_put import sound
    from frontend import transcriber, sound_ui
    program['nosound']=False
except Exception as e:
    program['nosound']=True
    log.error("Problem importing Sound/pyaudio. Is it installed? {}"
            "".format(e))
    program['exceptiononload']=True
"""Other people's stuff"""
# try:
    
# except Exception as e:
#     log.error("Problem importing packaging.version; installed? {}".format(e))
#     program['exceptiononload']=True
from utilities import times
program['start_time'] = times.now()
import threading
import multiprocessing
import psutil
import itertools
import importlib.util
import collections
from random import randint
if program['tkinter']:
    import tkinter #as gui
    import tkinter.font
    import tkinter.scrolledtext
    if not program['testing']:
        from frontend import tkintermod
        tkinter.CallWrapper = tkintermod.TkErrorCatcher
    from frontend import ui_tkinter as ui
"""else:
    import kivy
"""
import time
# #for some day...
# from PIL import Image #, ImageTk
#import Image #, ImageTk
# import reports
import sys
"""for tr:"""
import locale
import gettext
_ = gettext.gettext  # initial fallback; updated by interfacelang() when translation loads
import sys
import os
import pprint #for settings and status files, etc.
import subprocess
import webbrowser

from backend.reporting.generator import Report
from backend.core.lexicon import Senses, Segments, WordCollection, Parse, Tone
from backend.core.sorting_engine import Sort
from frontend.ui_shell import (HasMenus, Menus, StatusFrame, TaskDressing,
    LiftChooser, SortButtonFrame, _GroupButtonFrame, SortGroupButtonFrame,
    SortGlyphGroupButtonFrame, ImageFrame, Splash, ErrorNotice, ResultWindow)
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
        
class Options:
    def alias(self,o):
        return self.odict.get(o,o)
    def next(self,o):
        o=self.alias(o)
        setattr(self,o,getattr(self,o)+1)
    def prev(self,o):
        o=self.alias(o)
        setattr(self,o,getattr(self,o)-1)
    def get(self,o):
        o=self.alias(o)
        return getattr(self,o)
    def __init__(self,**kwargs):
        self.odict={'col':'column','c':'column',
                    'r':'row'
                    }
        for arg in kwargs:
            setattr(self,self.alias(arg),kwargs[arg])
class Object:
    def __init__(self,**kwargs):
        for k in kwargs:
            setattr(self,k,kwargs[k])
class App:
    def __getitem__(self, key): return getattr(self, key)
    def __setitem__(self, key, val): setattr(self, key, val)
    def get(self,key,default=None): 
        raise AttributeError("Update the function that called this")
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
                .format(level=loglevel, time=times.now().isoformat()[:-7]+'Z'))
    def show_scaling_from_windows(self):
        try:
            import ctypes
            log.info("Windows scaling: {factor}".format(
                        factor=ctypes.windll.shcore.GetScaleFactorForDevice(0)))
        except:
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
            except:
                log.error("Failed to load translation for {}".format(i))
            # finally:
            #     log.info("Translation for {} loaded".format(i))
        self.interfacelangs={i for i in self.i18n}
        lang=self.interfacelang() #translation works from here
        # log.info(_("Translation is working now ({lang}).").format(lang=lang))
    def interfacelang(self,lang=None,magic=False):
        global _
        log.info("interfacelang called with lang {lang} and magic {magic}".format(lang=lang,magic=magic))
        # global i18n
        """Attention: for this to work, _ has to be defined globally (here, not in
        a class or module.) So I'm getting the language setting in the class, then
        calling the module (imported globally) from here."""
        curlang=None
        magic=False
        try:
            # log.info("interfacelang")
            if _.__module__ == 'gettext':
                log.info("Magic: {}".format(_.__module__))
                magic=True
            else:
                log.info("Magic seems to be installed, but not gettext: {module}"
                ).format(module=_.__module__)
            # log.info("_ looks defined")
            for l in self.i18n:
                if self.i18n[l] == _.__self__:
                    curlang=l
                    break #i.e., if it is already set up correctly
        except NameError:
            # log.info("_ doesn't look defined yet")
            log.info("Looks like translation magic isn't defined yet; making")
        except Exception as e:
            log.error("Failed to get translation: {}".format(e))
        """Diagnostics of questionable value, with Magic above?"""
        if lang:
            log.info("Asked to set lang {lang} with curlang {curlang}".format(lang=lang,curlang=curlang))
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
        if lang and lang != curlang and lang in self.i18n: # or not magic:
            self.i18n[lang].install()
            _ = self.i18n[lang].gettext  # keep main._ updated for LazyGlobal access
            file.uilang(lang)
            log.info(_("Set Interface language: {lang}").format(lang=lang))
            return lang
        log.info(_("Returning current Interface language: {lang}").format(lang=curlang))
        return curlang
    def getlangfromlocale(self):
    # log.debug("Looking for interface language in locale.")
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
            program.Demo=True
            file.writefilename() #clear this to select next time
    def run(self):
        # global program
        log.info("Running main function on {} ({})".format(platform.system(),
                                        platform.platform())) #Don't translate yet!
        try:
            self.tk_root = ui.Root(program=self)
        except tkinter.TclError as e:
            log.info(_("Evidently you can't make a root window? ({error})").format(error=e))
            return
        # log.info("Theme ipady: {}".format(program.theme.ipady))
        # log.info("Theme ipadx: {}".format(program.theme.ipadx))
        # log.info("Theme pady: {}".format(program.theme.pady))
        # log.info("Theme padx: {}".format(program.theme.padx))
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
            except: # Windows 8 or before
                pass
            screensize = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
            log.info(_("MS Windows screen size: {size}").format(size=screensize))
        self.get_lift_file() #self.filename, self.analang set here
        self.splash = Splash(self)
        FileParser(self) #needs self.filename, pick up self.analang from file
        self.repocheck()
        Settings(self) #needs self.filename, pick up self.analang from file
        self.settings.post_lift_init()
        CheckParameters(self) #depends on settings (nothing but self.analang?)
        ExampleDict(self) #needed for makestatus, needs params,slices,data
        Alphabet(self) #after slicedict is up; needs params
        # SliceDict(adhoc,profilesbysense,self) #needs adhoc,profilesbysense
        # StatusDict(filename,dict,self) #needs filename,dict
        t = TaskChooser(self) #TaskChooser MainApplication
        t.mainloop()
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
        except:
            try:
                self.tk_root = ui.Root(program=self)
                self.tk_root.wraplength=int(self.tk_root.winfo_screenwidth()*.7) #exit button
                newtk=True
                log.info(_("Starting with new root"))
            except tkinter.TclError as e:
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
            # log.info(_("Done making update menu"))
        errorw.wait_window(errorw)
        if newtk: #likely never work/needed?
            self.tk_root.mainloop() #This has to be the last thing
    def __init__(self,program):
        # globals()['program'] = self  # replace dict with App; LazyGlobal resolves to self
        sys.excepthook = self.handle_exception
        self.show_scaling_from_windows()
        self.file = file.getfile(__file__)
        if hasattr(sys,'_MEIPASS') and sys._MEIPASS is not None:
            self.aztdir=sys._MEIPASS #android?
        else:
            self.aztdir=self.file.parent
        # if self.hostname == 'karlap':
        for k,v in program.items():
            setattr(self,k,v)
        self.default_task='WordCollectnParse'
        if self.aztdir.parent.stem == 'raspy': 
            self.testing=True #eliminates Error screens and zipped logs and repo commits
            self.production=True #True for making screenshots (default theme)
            self.me=True
            self.loglevel='INFO'
            self.testlift='Demo_en' #portion of filename
            self.testtask='SortV' #Will convert from string to class later
            # self.default_task='WordCollectnParse'
        else:
            self.me=False
            self.production=True #True for making screenshots (default theme)
            self.testing=False #True eliminates Error screens and zipped logs
            self.loglevel='INFO'
            # self.default_task='WordCollectnParse'
        self.get_interface_languages()
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
                setattr(self,exe,file.findexecutable(exe))
                # log.info(_("Found {exe} at {path}").format(exe=exe,path=getattr(self,exe)))
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
        except:
            import traceback
            log.error("uncaught exception: %s", traceback.format_exc())
            self.maybe_run_problem()
        sys.exit()
"""These are non-method utilities I'm actually using."""
def runtime_to_now():
    #this returns a delta!
    return times.now()-program.start_time
def unlist(l,ignore=[None]):
    if l and isinstance(l[0],lift.et.Element):
         log.error(_("unlist should only be used on text (not node) lists ({list})"
                    "").format(list=l))
         log.error(_("Element[0] text: {text}").format(text=l[0].text))
         return
    return firstoflist(l,all=True,ignore=ignore)
def propagate(self,attr):
    """This function pushes an attribute value to all children with that
    attribute already set, for widgets that are already there (changing fonts)
    """
    log.info(self.winfo_children())
    for child in self.winfo_children():
        # log.info("working on {}".format(child))
        if hasattr(child,attr):
            # log.info("Found {} value for {} attr, setting {} value".format(
            #         getattr(child,attr),attr,getattr(self,attr)
            #         ))
            setattr(child,attr,getattr(self,attr))
            propagate(child,attr=attr)
def loadCAWL():
    stockCAWL=file.pathname_from_base_dir('SILCAWL/SILCAWL.lift')
    if file.exists(stockCAWL):
        log.info(_("Found stock LIFT file: {file}").format(file=stockCAWL))
    try:
        # cawldb=lift.Lift(str(stockCAWL))
        cawldb=lift.LiftXML(str(stockCAWL),tostrip=True)
        log.info(_("Parsed ET."))
        log.info(_("Got ET Root."))
    except lift.BadParseError as e:
        text=_("{file} doesn't look like a well formed lift file; please "
                "try again. ({error})").format(file=stockCAWL,error=e)
        ErrorNotice(text,wait=True)
        return
    except Exception as e:
        log.info(_("Error: {error}").format(error=e))
    log.info(_("Parsed stock LIFT file to tree/nodes."))
    return cawldb
def saveimagefile(url,filename,copyto=None):
    # log.info("Preparing to write image to new file")
    if not copyto:
        copyto=program.settings.imagesdir
    fqdn=file.getdiredurl(copyto,filename) #new url
    # log.info("Preparing to write image to {}".format(fqdn))
    with open(fqdn,'wb') as f:
        # log.info("opened new file")
        with open(url,'rb') as u:
            # log.info("opened old file")
            f.write(u.read())
def scaledimage(image,pixels=150,scaleto='height'):
    image.scale(program.scale,pixels=pixels,scaleto=scaleto)
def getimagelocationURI(sense):
    i=sense.illustrationvalue()
    for d in [program.settings.imagesdir,program.settings.directory]:
        if i and d:
            di=file.getdiredurl(d,i)
            if file.exists(di):
                return di
def compilesenseimage(sense):
    """This needs to capture ui.Image errors like this:
    except tkinter.TclError as e:
        if ('value for "-file" missing' not in e.args[0] and
                "couldn't recognize data in image file" not in e.args[0]):
            log.info(_("ui.Image error: {error}").format(error=e))
    """
    uri=sense.illustrationURI()
    if uri and file.exists(uri):
        sense.image=ui.Image(uri)
    else:
        sense.image=None
def scale_image(image,pixels=65,scaleto='height'):
    return image.scale(program.scale,pixels=pixels,scaleto=scaleto)
def scaleimageifthere(sense,pixels=65,scaleto='height'):
    if not getattr(sense,'image',False) or not isinstance(sense.image,ui.Image):
        try:
            compilesenseimage(sense)
        except tkinter.TclError as e:
            if ('value for "-file" missing' not in e.args[0] and
                    "couldn't recognize data in image file" not in e.args[0]):
                log.info(_("ui.Image error: {error}").format(error=e))
    if sense.image:
        return scale_image(sense.image,pixels=pixels,scaleto=scaleto)
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
        elif not me:
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
            except: #in case translation isn't working yet
                title="Update (Git) output"
            ErrorNotice(t,title=title,button=button,wait=True,**kwargs)
        except:
            log.info(set(kwargs.keys()))
            log.info(set(['parent']))
if __name__ == '__main__':
    """These things need to be done outside of a function, as we need global
    variables."""
    # log.info("TaskChooser MRO: {}".format(TaskChooser.mro()))
    # log.info("ui.Window MRO: {}".format(ui.Window.mro()))
    # log.info("ui.Exitable MRO: {}".format(ui.Exitable.mro()))
    """Not translating yet"""
    App(program)
    """The following are just for testing"""
    entry=Entry(db, guid='003307da-3636-40cd-aca9-6b0d798055d2')
    print(entry.lexeme)
    print(entry.citation)

    import timeit #for testing; remove in production
    def tests():
        m=ui.Toplevel()
        m.title("Program Name Here")
        ui.Label(m, text='This application checks lexical data, as part '
                        'of orthography development.').grid(column=0, row=0)
        m.mainloop()
    #tests()
    def test():
        formsbycvs(C,V,'C1','V1')
    def timetest():
                times=1000000000
                out1=timeit.timeit(test, number=times)
                print(out1)
    #timetest() #see which C variable takes more computing time
