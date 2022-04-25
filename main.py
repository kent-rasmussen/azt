#!/usr/bin/env python3
# coding=UTF-8
"""This file runs the actual GUI for lexical file manipulation/checking"""
program={'name':'A→Z+T'}
program['tkinter']=True
program['production']=False #True for making screenshots (default theme)
program['testing']=True #True eliminates Error screens and zipped logs
program['demo']=True #True sets me=False, production=True, testing=False
program['version']='0.9.1' #This is a string...
program['url']='https://github.com/kent-rasmussen/azt'
program['Email']='kent_rasmussen@sil.org'
exceptiononload=False
import platform
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
if platform.uname().node == 'karlap':
    loglevel=6 #
    if program['demo']:
        me=False
        program['production']=True #True for making screenshots (default theme)
        program['testing']=False #True eliminates Error screens and zipped logs
    else:
        me=True
else:
    loglevel='DEBUG'
    me=False
import logsetup
log=logsetup.getlog('root') #not ever a module
logsetup.setlevel(loglevel)
"""My modules, which should log as above"""
import lift
import file
# import profiles
import setdefaults
import xlp
try:
    import sound
    import transcriber
except Exception as e:
    log.error("Problem importing Sound/pyaudio. Is it installed? {}".format(e))
    exceptiononload=True
"""Other people's stuff"""
import threading
import multiprocessing
import itertools
import importlib.util
import collections
from random import randint
if program['tkinter']==True:
    try:
        import tkinter #as gui
        import tkinter.font
        import tkinter.scrolledtext
        import tkintermod
        tkinter.CallWrapper = tkintermod.TkErrorCatcher
    except Exception as e:
        log.exception("Problem importing GUI/tkinter. Is it installed? %s",e)
        exceptiononload=True
    import ui_tkinter as ui
"""else:
    import kivy
"""
import ast
import time
import datetime
import wave
# #for some day...
# from PIL import Image #, ImageTk
#import Image #, ImageTk
import configparser
import rx
import inspect #this is for determining this file name and location
import reports
import sys
"""for tr:"""
import locale
import gettext
import sys
import os
import pprint #for settings and status files, etc.
import subprocess
import webbrowser
import pkg_resources

class FileChooser(object):
    """This class selects the LIFT database we'll be working with, and does
    some basic processing on it."""
    def askwhichlift(self,filenamelist):
        def setfilename(choice,window):
            if choice == 'New':
                window.withdraw()
                self.name=self.startnewfile()
                log.info("self.name: {}".format(self.name))
                window.deiconify()
                if self.name in ['New',''] or not hasattr(self,'analang'):
                    return
            elif choice == 'Other':
                self.name=file.lift()
                if not self.name:
                    return
            else:
                self.name=choice
            if self.name:
                file.writefilename(self.name)
                window.destroy()
        self.name=None # in case of exit
        window=ui.Window(program['root'],title=_("Select LIFT Database"))
        text=_('What LIFT database do you want to work on?')
        ui.Label(window.frame, text=text).grid(column=0, row=0)
        optionlist=[('New',_("Start work on a new language"))]
        if filenamelist:
            optionlist+=[(f,f) for f in filenamelist] #keep everything a tuple
        optionlist+=[('Other',_("Select another database on my computer"))]
        buttonFrame1=ui.ScrollingButtonFrame(window.frame,
                                optionlist=optionlist,
                                command=setfilename,
                                window=window,
                                column=0, row=1
                                )
        window.wait_window(window)
    def loadCAWL(self):
        stockCAWL=file.fullpathname('SILCAWL/SILCAWL.lift')
        if file.exists(stockCAWL):
            log.info("Found stock LIFT file: {}".format(stockCAWL))
        try:
            self.cawldb=lift.Lift(str(stockCAWL))
            log.info("Parsed ET.")
            log.info("Got ET Root.")
        except Exception as e:
            log.info("Error: {}".format(e))
        except lift.BadParseError:
            text=_("{} doesn't look like a well formed lift file; please "
                    "try again.").format(stockCAWL)
            ErrorNotice(text,wait=True)
            return
        log.info("Parsed stock LIFT file to tree/nodes.")
        return self.cawldb
    def copytonewfile(self,newfile):
        log.info("Beginning Copy of stock to new LIFT file.")
        self.loadCAWL()
        for n in (self.cawldb.nodes.findall('entry/lexical-unit')+
                    self.cawldb.nodes.findall('entry/citation')):
            for f in n.findall('form'):
                n.remove(f)
        log.info("Stripped stock LIFT file.")
        log.info("Trying to write empty LIFT file to {}".format(newfile))
        try:
            self.cawldb.write(str(newfile))
        except Exception as e:
            log.error("Exception: {}".format(e))
        log.info("Tried to write empty LIFT file to {}".format(newfile))
        if file.exists(newfile):
            log.info("Wrote empty LIFT file to {}".format(newfile))
    def startnewfile(self):
        def done(event=None):
            window.destroy()
        window=ui.Window(program['root'],title=_("Start New LIFT Database"))
        ethnologueurl="https://www.ethnologue.com/"
        title=_("What is the Ethnologue (ISO 639-3) code?")#" of the language you "
                # "want to study?")
        text=_("(find your language on {}; the code is at the top of "
                "the page) "
                "\nThis code will be used throughout your database, so please "
                "\ntake a moment and confirm that this is correct before "
                "continuing.".format(ethnologueurl)
                )
        t=ui.Label(window.frame, text=title, font='title', column=0, row=0)
        l=ui.Label(window.frame, text=text, column=0, row=1)
        l.bind("<Button-1>", lambda e: openweburl(ethnologueurl))
        l.wrap()
        entryframe=ui.Frame(window.frame,row=2,column=0,sticky='nsew')
        analang=ui.StringVar()
        e=ui.EntryField(entryframe, textvariable=analang, font='readbig',
                        width=5, row=0,column=0,sticky='w')
        e.bind('<Return>',done)
        e.focus_set()
        ui.Button(entryframe, text='OK', cmd=done, font='title',
                    row=0,column=1,sticky='e')
        l.wait_window(window)
        self.analang=analang.get()
        if not self.analang:
            return
        if len(self.analang) != 3:
            e=ErrorNotice("That doesn't look like an ethnologue code "
                        "(just three letters)",wait=True)
            return
        dir=file.getdirectory()
        newfile=file.getnewlifturl(dir,analang.get())
        if not newfile:
            ErrorNotice(_("Problem creating file; does the directory "
                        "already exist?"),wait=True)
            return
        if file.exists(newfile):
            ErrorNotice(_("The file {} already exists! {}").format(newfile),
                                                                wait=True)
            return
        log.info("Copying over stock to new LIFT file.")
        self.copytonewfile(newfile)
        return str(newfile)
    def getfilename(self):
        self.name=file.getfilename()
        if not self.name or type(self.name) is list:
            self.askwhichlift(self.name)
        if not self.name or not file.exists(self.name):
            log.error("Didn't select a lexical database to check; exiting.")
            exit()
    def loaddatabase(self):
        try:
            self.db=lift.Lift(self.name)
        except lift.BadParseError:
            text=_("{} doesn't look like a well formed lift file; please "
                    "try again.").format(self.name)
            log.info("'lift_url.py' removed.")
            ErrorNotice(text,title='LIFT parse error',wait=True)
            file.writefilename() #just clear the default
            raise #Then force a quit and retry
        except Exception as e:
            text=_("There seems to be a (non-XML) problem loading your "
            "database ({}); I will remove it as default so you can open "
            "another").format(self.name)
            log.error(text)
            ErrorNotice(text,title='LIFT non-parse error',wait=True)
            file.writefilename()
            raise
    def dailybackup(self):
        if not file.exists(self.db.backupfilename):
            self.db.write(self.db.backupfilename)
        else:
            print(_("Apparently we've run this before today; not backing "
            "up again."))
    def senseidtriage(self):
        # import time
        # print("Doing senseid triage... This takes awhile...")
        # start_time=time.time()
        self.senseids=self.db.senseids
        self.senseidsinvalid=[] #nothing, for now...
        # print(time.time() - start_time,"seconds.")
        print(len(self.senseidsinvalid),'senses with invalid data found.')
        self.db.senseidsinvalid=self.senseidsinvalid
        self.senseidsvalid=[]
        for senseid in self.senseids:
            if senseid not in self.senseidsinvalid:
                self.senseidsvalid+=[senseid]
        print(len(self.senseidsvalid),'senses with valid data remaining.')
        self.senseidswanyps=self.db.get('sense',path=['ps'],showurl=True).get('senseid') #any ps value works here.
        print(len(self.senseidswanyps),'senses with ps data found.')
        self.senseidsvalidwops=[]
        self.senseidsvalidwps=[]
        for senseid in self.senseidsvalid:
            if senseid in self.senseidswanyps:
                self.senseidsvalidwps+=[senseid]
            else:
                self.senseidsvalidwops+=[senseid]
        self.db.senseidsvalidwps=self.senseidsvalidwps #This is what we'll search
        print(len(self.senseidsvalidwops),'senses with valid data but no ps data.')
        print(len(self.senseidsvalidwps),'senses with valid data and ps data.')
    def getwritingsystemsinfo(self):
        """This doesn't actually do anything yet, as we can't parse ldml."""
        self.db.languagecodes=self.db.analangs+self.db.glosslangs
        self.db.languagepaths=file.getlangnamepaths(self.name,
                                                    self.db.languagecodes)
    def __init__(self):
        super(FileChooser, self).__init__()
        self.getfilename()
        self.loaddatabase()
        self.dailybackup()
        self.senseidtriage() #sets: self.senseidswanyps self.senseidswops self.senseidsinvalid self.senseidsvalid
        self.getwritingsystemsinfo()
class Menus(ui.Menu):
    """this is the overall menu set, from which each will be selected."""
    def command(self,parent,label,cmd):
        parent.add_command(label=label, command=cmd)
    def cascade(self,parent,label,newmenuname):
        setattr(self,newmenuname, ui.Menu(parent, tearoff=0))
        parent.add_cascade(label=label, menu=getattr(self,newmenuname))
    # def setmenus(self):
    #     self.menubar = ui.Menu(self)
    def change(self):
        self.cascade(self,_("Change"),'changemenu')
        # changemenu = ui.Menu(self.menubar, tearoff=0)
        # self.menubar.add_cascade(label=_("Change"), menu=changemenu)
        self.languages()
        if isinstance(self.parent,Sort):
            self.parameterslice()
    def languages(self):
        """Language stuff"""
        self.cascade(self.changemenu,_("Languages"),'languagemenu')
        for m in [("Interface/computer language", self.parent.getinterfacelang),
                    ("Analysis language",self.parent.getanalang),
                    ("Analysis language Name",self.parent.getanalangname),
                    ("Gloss language",self.parent.getglosslang),
                    ("Another gloss language",self.parent.getglosslang2)]:
            self.command(self.languagemenu,
                        label=_(m[0]),
                        cmd=m[1]
                        )
        """Word/data choice stuff"""
    def parameterslice(self):
        for m in [("Part of speech", self.parent.getps),
                    ("Consonant-Vowel-Tone", self.parent.getcvt),
                    ]:
            self.command(self.changemenu,
                        label=_(m[0]),
                        cmd=m[1]
                        )
        self.cascade(self.changemenu,_("Syllable profile"),'profilemenu')
        for m in [("Next", self.parent.status.nextprofile),
                    ("Choose", self.parent.getprofile),
                    ]:
            self.command(self.profilemenu,
                        label=_(m[0]),
                        cmd=m[1]
                        )
        """What to check stuff"""
        cvt=self.parent.params.cvt()
        ps=self.parent.slices.ps()
        profile=self.parent.slices.profile()
        if None not in [ps, profile, cvt]:
            if cvt == 'T':
                self.changemenu.add_separator()
                self.cascade(self.changemenu,_("Tone Frame"),'framemenu')
                self.checkmenus=[
                            ("Choose", self.parent.getcheck),
                            ]
                # if isinstance(parent,Check):
                #     checkmenus.append(("Next to Sort", self.parent.nextcheck,
                #                                             tosort=True))
                # elif isinstance(parent,Record):
                #     checkmenus.append(("Next to Record", self.parent.nextcheck,
                #                                             wsorted=True))
                # else:
                #     checkmenus.append(("Next to Record", self.parent.nextcheck))
                for m in self.checkmenus:
                    self.command(self.framemenu,
                                label=_(m[0]),
                                cmd=m[1]
                                )
                # framemenu = ui.Menu(changemenu, tearoff=0)
                # changemenu.add_cascade(label=_("Tone Frame"), menu=framemenu)
                # framemenu.add_command(label=_("Next"),
                #         command=lambda x=check.status:StatusDict.nextcheck(x))
                # framemenu.add_command(label=_("Next to sort"),
                #         command=lambda x=check.status:StatusDict.nextcheck(x,
                #                                                 tosort=True))
                # framemenu.add_command(label=_("Next with data already sorted"),
                #         command=lambda x=check.status:StatusDict.nextcheck(x,
                #                                                 wsorted=True))
                # framemenu.add_command(label=_("Choose"),
                #                 command=lambda x=check:Check.getcheck(x))
            else:
                self.changemenu.add_separator()
                self.changemenu.add_command(label=_("Location in word"),
                        command=lambda x=check:Check.getcheck(x))
                if check.check is not None:
                    self.changemenu.add_command(label=_("Segment(s) to check"),
                        command=lambda x=check:Check.getgroup(x,tosort=True)) #any
        """Do"""
    def do(self):
        domenu = ui.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label=_("Do"), menu=domenu)
        reportmenu = ui.Menu(self.menubar, tearoff=0)
        reportmenu.add_command(label=_("Tone by sense"),
                        command=lambda x=check:Check.tonegroupreport(x))
        reportmenu.add_command(label=_("Tone by location"
                        ),command=lambda x=check:Check.tonegroupreport(x,
                                                            bylocation=True))
        reportmenu.add_command(label=_("Tone by sense (comprehensive)"),
                command=lambda x=check:Check.tonegroupreportcomprehensive(x))
        if me:
            reportmenu.add_command(label=_("Initiate Consultant Check"),
                command=lambda x=check:Check.consultantcheck(x))
        reportmenu.add_command(label=_("Basic Vowel report (to file)"),
                        command=lambda x=check:Check.basicreport(x,cvtstodo=['V']))
        reportmenu.add_command(label=_("Basic Consonant report (to file)"),
                        command=lambda x=check:Check.basicreport(x,cvtstodo=['C']))
        reportmenu.add_command(label=_("Basic report on Consonants and Vowels "
                                                                "(to file)"),
                command=lambda x=check:Check.basicreport(x,cvtstodo=['C','V']))
        domenu.add_cascade(label=_("Reports"), menu=reportmenu)
    def record(self):
        recordmenu = ui.Menu(self.menubar, tearoff=0)
        recordmenu.add_command(label=_("Sound Card Settings"),
                        command=lambda x=check:Check.soundcheck(x))
        recordmenu.add_command(label=_("Record tone group examples"),
                        command=lambda x=check:Check.showtonegroupexs(x))
        recordmenu.add_command(label=_("Record dictionary words, largest group "
                                                                    "first"),
                        command=lambda x=check:Check.showentryformstorecord(x,
                                                                justone=False))
        recordmenu.add_command(label=_("Record examples for particular "
                                                    "entries, 1 at at time"),
                        command=lambda x=check:Check.showsenseswithexamplestorecord(x))
        domenu.add_cascade(label=_("Recording"), menu=recordmenu)
        domenu.add_command(label=_("Join Groups"),
                        command=lambda x=check:Check.join(x))
        """Advanced"""
    def advanced(self):
        self.cascade(self,_("Advanced"),'advancedmenu')
        options=[(_("Change to another Database (Restart)"),
                            self.parent.taskchooser.changedatabase),
                (_("Digraph and Trigraph settings"),
                            self.parent.settings.askaboutpolygraphs),
                (_("Segment Interpretation Settings"),
                            self.parent.setSdistinctions),
                (_("Syllable Profile Analysis (Restart)"),
                            self.parent.settings.reloadprofiledata),
                (_("Remake Status file (several minutes)"),
                            self.parent.settings.reloadstatusdata),
                ]
        for m in options:
            self.command(self.advancedmenu,
                        label=_(m[0]),
                        cmd=m[1]
                        )
        if isinstance(self.parent,Record):
            self.record()
        if isinstance(self.parent,Sort):
            self.sort()
    def record(self):
        self.advancedmenu.add_separator()
        options=[(_("Number of Examples to Record"),
                self.parent.taskchooser.getexamplespergrouptorecord),]
        for m in options:
            self.command(self.advancedmenu,
                    label=_(m[0]),
                    cmd=m[1]
                    )
    def sort(self):
        self.advancedmenu.add_separator()
        options=[(_("Add/Modify Ad Hoc Sorting Group"),
                                                self.parent.addmodadhocsort),]
        if isinstance(self.parent,SortT):
            options.extend([(_("Add Tone frame"), self.parent.addframe)])
        options.extend([(_("Resort skipped data"), self.parent.tryNAgain),
                        (_("Reverify current framed group"),
                                                        self.parent.reverify),
                        (_("Join Groups"), self.parent.join)
                        ])
        for m in options:
            self.command(self.advancedmenu,
                    label=_(m[0]),
                    cmd=m[1]
                    )
        # advancedmenu = ui.Menu(self.menubar, tearoff=0)
        # self.menubar.add_cascade(label=_("Advanced"), menu=advancedmenu)
        # filemenu = ui.Menu(self.menubar, tearoff=0)
        # filemenu.add_command(label=_("Dictionary Morpheme"),
        #                 command=lambda x=check:Check.addmorpheme(x))
        # advancedmenu.add_command(label=_("Add Tone frame"),
        #                 command=lambda x=check:Check.addframe(x))
        # advancedmenu.add_command(label=_("Transcribe/(re)name Framed Tone Group"),
        #                         command=lambda x=check:Check.renamegroup(x))
        # advtonemenu = ui.Menu(self.menubar, tearoff=0)
        # advancedmenu.add_cascade(label=_("Tone Reports"), menu=advtonemenu)
        # advtonemenu.add_command(label=_("Name/join UF Tone Groups"),
        #                 command=lambda x=check:Check.tonegroupsjoinrename(x))
        # advtonemenu.add_command(label=_("Custom groups by sense"),
        #                         command=lambda x=check:Check.tonegroupreport(x,
        #                                                         default=False))
        # advtonemenu.add_command(label=_("Custom groups by location"),
        #                         command=lambda x=check:Check.tonegroupreport(x,
        #                                         bylocation=True, default=False))
        # advtonemenu.add_command(
        #             label=_("Custom groups by sense (comprehensive)"),
        #             command=lambda x=check:Check.tonegroupreportcomprehensive(x,
        #                                                         default=False))
        # redomenu = ui.Menu(self.menubar, tearoff=0)
        # redomenu.add_command(label=_("Previously skipped data"),
        #                         command=lambda x=check:Check.tryNAgain(x))
        # advancedmenu.add_cascade(label=_("Redo"), menu=redomenu)
        # advancedmenu.add_cascade(label=_("Add other"), menu=filemenu)
        # redomenu.add_command(
        #                 label=_("Verification of current framed group"),
        #                 command=lambda x=check:Check.reverify(x))
        # redomenu.add_command(
        #                 label=_("Digraph and Trigraph settings (Restart)"),
        #                 command=lambda x=check:Check.askaboutpolygraphs(x))
        # redomenu.add_command(
        #                 label=_("Syllable Profile Analysis (Restart)"),
        #                 command=lambda x=check:Check.reloadprofiledata(x))
        # redomenu.add_command(
        #                 label=_("Change to another Database (Restart)"),
        #                 command=lambda x=check:Check.changedatabase(x))
        # redomenu.add_command(
        #                 label=_("Verification Status file (several minutes)"),
        #                 command=lambda x=check:Check.reloadstatusdata(x))
        # advancedmenu.add_command(
        #                 label=_("Segment Interpretation Settings"),
        #                 command=lambda x=check:Check.setSdistinctions(x))
        # advancedmenu.add_command(
        #                 label=_("Add/Modify Ad Hoc Sorting Group"),
        #                 command=lambda x=check:Check.addmodadhocsort(x))
        # advancedmenu.add_command(
        #         label=_("Number of Examples to Record"),
        #         command=lambda x=check:Check.getexamplespergrouptorecord(x))
        """Unused for now"""
        # settingsmenu = ui.Menu(menubar, tearoff=0)
        # changestuffmenu.add_cascade(label=_("Settings"), menu=settingsmenu)
        """help"""
    def help(self):
        self.cascade(self,_("Help"),'helpmenu')
        helpitems=[(_("About"), self.parent.helpabout)]
        if program['git']:
            helpitems+=[(_("Update A→Z+T"), self.parent.updateazt)]
        helpitems+=[("What's with the New Interface?",
                        self.parent.helpnewinterface)
                    ]
        for m in helpitems:
            self.command(self.helpmenu,
                        label=_(m[0]),
                        cmd=m[1]
                        )
    def __init__(self, parent):
        super(Menus, self).__init__(parent)
        self.advanced()
        self.help()
class StatusFrame(ui.Frame):
    """This contains all the info about what the user is currently working on,
    and buttons to change it."""
    def setopts(self):
        self.opts={
            'row':0,
            'labelcolumn':0,
            'valuecolumn':1,
            'buttoncolumn':2,
            'labelxpad':15,
            'width':None, #10
            'columnspan':3,
            'columnplus':0}
    def proselabel(self,label,parent=None,cmd=None,tt=None):
        if parent is None:
            parent=self.proseframe
            column=self.opts['labelcolumn']
            row=self.opts['row']
            columnspan=self.opts['columnspan']
            ipadx=self.opts['labelxpad']
        else:
            column=0+self.opts['columnplus']
            row=0
            columnspan=1
            ipadx=0
        if not self.mainrelief:
            l=ui.Label(parent, text=label,font='report',anchor='w')
        else:
            l=ui.Button(parent,text=label,font='report',anchor='w',
                relief=self.mainrelief)
        l.grid(column=column, row=row, columnspan=columnspan,
                ipadx=ipadx, sticky='w')
        if cmd is not None:
            l.bind('<ButtonRelease>',cmd)
        if tt is not None:
            ttl=ui.ToolTip(l,tt)
    def labels(self,parent,label,value): #not used!
        ui.Label(self, text=label,
                column=opts['labelcolumn'], row=self.opts['row'],
                ipadx=opts['labelxpad'], sticky='w'
                )
        ui.Label(self, text=value,
                column=opts['valuecolumn'], row=self.opts['row'],
                ipadx=opts['labelxpad'], sticky='w'
                )
    def button(self,text,fn,**kwargs): #=opts['labelcolumn']
        """cmd overrides the standard button command system."""
        ttt=kwargs.pop('tttext',None)
        b=ui.Button(self.proseframe, choice=text, text=text, anchor='c',
                        cmd=fn, width=self.opts['width'],
                        column=0, row=self.opts['row'],
                        columnspan=self.opts['columnspan'],
                        wraplength=int(program['root'].wraplength/4),
                        **kwargs)
        if ttt:
            tt=ui.ToolTip(b,ttt)
        return b
    """These functions point to self.taskchooser functions, betcause we don't
    know who this frame's parent is"""
    def makeproseframe(self):
        self.proseframe=ui.Frame(self,row=0,column=0)
    def interfacelangline(self):
        for l in self.taskchooser.interfacelangs:
            if l['code']==interfacelang():
                interfacelanguagename=l['name']
        t=(_("Using {}").format(interfacelanguagename))
        self.proselabel(t,cmd=self.taskchooser.getinterfacelang)
        self.opts['row']+=1
    def analangline(self):
        analang=self.settings.params.analang()
        langname=self.settings.languagenames[analang]
        t=(_("Studying {}").format(langname))
        if (langname == _("Language with code [{}]").format(analang)):
            self.proselabel(t,cmd=self.taskchooser.getanalangname,
                                            tt=_("Set analysis language Name"))
        else:
            self.proselabel(t,cmd=self.taskchooser.getanalang,
                                            tt=_("Change analysis language"))
        self.opts['row']+=1
    def glosslangline(self):
        lang1=self.settings.languagenames[self.settings.glosslangs.lang1()]
        t=(_("Meanings in {}").format(lang1))
        line=ui.Frame(self.proseframe,row=self.opts['row'],column=0,
                        columnspan=3,sticky='w') #3 cols is the width of frame
        self.opts['row']+=1
        self.proselabel(t,cmd=self.taskchooser.getglosslang,parent=line)
        self.opts['columnplus']=1
        if len(self.settings.glosslangs) >1:
            lang2=self.settings.languagenames[self.settings.glosslangs.lang2()]
            t=(_("and {}").format(lang2))
        else:
            t=_("only")
        self.proselabel(t,cmd=self.taskchooser.getglosslang2,parent=line)
        self.opts['columnplus']=0
    def fieldsline(self):
        for ps in [self.settings.nominalps, self.settings.verbalps]:
            if ps in self.settings.secondformfield:
                field=self.settings.secondformfield[ps]
            else:
                field='<unset>'
            t=(_("Using second form field ‘{}’ ({})").format(field,ps))
            line=ui.Frame(self.proseframe,row=self.opts['row'],column=0,
                            columnspan=3,sticky='w') #3 cols is the width of frame
            self.opts['row']+=1
            if ps == self.settings.nominalps:
                cmd=self.taskchooser.getsecondformfieldN
            else:
                cmd=self.taskchooser.getsecondformfieldV
            self.proselabel(t, cmd=cmd, parent=line)
    def sliceline(self):
        count=self.settings.slices.count()
        line=ui.Frame(self.proseframe,row=self.opts['row'],column=0,
                        columnspan=3,sticky='w')
        self.opts['row']+=1
        t=(_("Looking at {}").format(self.profile))
        self.proselabel(t,cmd=self.taskchooser.getprofile,parent=line)
        self.opts['columnplus']=1
        t=(_("{} words ({})").format(self.ps,count))
        self.proselabel(t,cmd=self.taskchooser.getps,parent=line)
        self.opts['columnplus']=0
    def cvtline(self):
        line=ui.Frame(self.proseframe,row=self.opts['row'],column=0,
                        columnspan=3,sticky='w')
        self.opts['row']+=1
        t=(_("Checking {},").format(
                                self.settings.params.cvtdict()[self.cvt]['pl']))
        self.proselabel(t,cmd=self.taskchooser.getcvt,parent=line)
        #this continues on the same line:
        if self.cvt == 'T':
            self.toneframe(line)
            self.tonegroup(line)
        else:
            self.cvcheck(line)
    def toneframe(self,line):
        self.opts['columnplus']=1
        if not self.checks:
            t=_("no tone frames defined.")
            # self.check=None
        elif self.check not in self.checks:
            t=_("no tone frame selected.")
            # self.check=None
        else:
            t=(_("working on ‘{}’ tone frame").format(self.check))
        self.proselabel(t,cmd=self.taskchooser.getcheck,parent=line)
    def tonegroup(self,line):
        self.opts['columnplus']=2
        check=self.settings.params.check()
        group=self.settings.status.group()
        profile=self.settings.slices.profile()
        if None in [check, group]:
            t=_("(no framed group)")
        else:
            t=(_("(framed group: ‘{}’)").format(group))
        log.info("cvt: {}; check: {}".format(self.cvt,self.check))
        """Set appropriate conditions for each of these:"""
        if (not check or (check in self.settings.status.checks(wsorted=True) and
            profile in self.settings.status.profiles(wsorted=True))):
            cmd=self.taskchooser.getgroupwsorted
        elif (not check or (check in self.settings.status.checks(tosort=True) and
            profile in self.settings.status.profiles(tosort=True))):
            cmd=self.taskchooser.getgrouptosort
        elif (check in self.settings.status.checks(toverify=True) and
            profile in self.settings.status.profiles(toverify=True)):
            cmd=self.taskchooser.getgrouptoverify
        elif (check in self.settings.status.checks(torecord=True) and
            profile in self.settings.status.profiles(torecord=True)):
            cmd=self.taskchooser.getgrouptorecord
        else:
            cmd=None
        log.info("check: {}; profile: {}; \n{}-{}; \n{}-{}; \n{}-{};"
                    "".format(check,profile,
                                self.settings.status.checks(wsorted=True),
                                self.settings.status.profiles(wsorted=True),
                                self.settings.status.checks(tosort=True),
                                self.settings.status.profiles(tosort=True),
                                self.settings.status.checks(toverify=True),
                                self.settings.status.profiles(toverify=True),
                                self.settings.status.checks(torecord=True),
                                self.settings.status.profiles(torecord=True)))
        self.proselabel(t,cmd=cmd,parent=line)
        self.opts['columnplus']=0
    def cvcheck(self,line):
        self.opts['columnplus']=1
        t=(_("working on {}".format(self.settings.params.cvcheckname())))
        self.proselabel(t,cmd=self.taskchooser.getcheck,parent=line)
        # self.opts['row']+=1
    def buttoncolumnsline(self):
        self.opts['row']+=1
        if self.settings.buttoncolumns:
            t=(_("Using {} button columns").format(self.settings.buttoncolumns))
        else:
            t=(_("Not using multiple button columns").format(self.check))
        log.info(t)
        tt=_("Click here to change the number of columns used for sort buttons")
        self.proselabel(t,cmd=self.taskchooser.getbuttoncolumns,tt=tt)
    def maxes(self):
        line=ui.Frame(self.proseframe,row=self.opts['row'],column=0,
                        columnspan=3,sticky='w')
        self.opts['row']+=1
        t=(_("Max profiles: {}; ".format(self.settings.maxprofiles)))
        self.proselabel(t,cmd=self.taskchooser.getmaxprofiles,parent=line)
        self.opts['columnplus']=1
        t=(_("Max lexical categories: {}".format(self.settings.maxpss)))
        self.proselabel(t,cmd=self.taskchooser.getmaxpss,parent=line)
    def finalbuttons(self):
        # self.opts['row']+=6
        self.opts['row']+=1
        if hasattr(self.taskchooser.mainwindowis,'dobuttonkwargs'):
            self.bigbutton=self.button(**self.task.dobuttonkwargs())
    """Right side"""
    def maybeboard(self):
        profileori=self.settings.slices.profile()
        if hasattr(self,'leaderboard') and type(self.leaderboard) is ui.Frame:
            self.leaderboard.destroy()
        self.leaderboard=ui.Frame(self,row=0,column=1,sticky="") #nesw
        #Given the line above, much of the below can go, but not all?
        self.settings.status.cull() #remove nodes with no data
        if self.cvt in self.settings.status:
            if self.ps in self.settings.status[self.cvt]: #because we cull, this == data is there.
                if (hasattr(self,'noboard') and (self.noboard is not None)):
                    self.noboard.destroy()
                if self.cvt == 'T':
                    if self.ps in self.settings.toneframes:
                        self.makeprogresstable()
                        return
                    else:
                        log.info("Ps {} not in toneframes ({})".format(self.ps,
                                self.settings.toneframes))
                else:
                    log.info("Found CV verifications")
                    self.makeprogresstable()
                    return
        else:
            log.info("cvt {} not in status {}".format(self.cvt,
                                                        self.settings.status))
        self.makenoboard()
    def boardtitle(self):
        titleframe=ui.Frame(self.leaderboard)
        titleframe.grid(row=0,column=0,sticky='n')
        cvtdict=self.settings.params.cvtdict()
        if not self.mainrelief:
            lt=ui.Label(titleframe, text=_(cvtdict[self.cvt]['sg']),
                                                    font='title')
        else:
            lt=ui.Button(titleframe, text=_(cvtdict[self.cvt]['sg']),
                                font='title',relief=self.mainrelief)
        lt.grid(row=0,column=0,sticky='nwe')
        ui.Label(titleframe, text=_('Progress for'), font='title'
            ).grid(row=0,column=1,sticky='nwe',padx=10)
        # ps=self.settings.slices.ps()
        if not self.mainrelief:
            lps=ui.Label(titleframe,text=self.ps,anchor='c',font='title')
        else:
            lps=ui.Button(titleframe,text=self.ps, anchor='c',
                            relief=self.mainrelief, font='title')
        lps.grid(row=0,column=2,ipadx=0,ipady=0)
        ttt=ui.ToolTip(lt,_("Change Check Type"))
        ttps=ui.ToolTip(lps,_("Change Part of Speech"))
        lt.bind('<ButtonRelease>',self.taskchooser.getcvt)
        lps.bind('<ButtonRelease>',self.taskchooser.getps)
    def makenoboard(self):
        log.info("No Progress board")
        self.boardtitle()
        self.noboard=ui.Label(self.leaderboard,
                            image=self.theme.photo['transparent'],
                            text='', pady=50,
                            # background=self.theme.background
                            ).grid(row=1,column=0,sticky='we')
        # self.frame.update()
    def makeCVprogresstable(self):
        self.boardtitle()
        self.leaderboardtable=ui.Frame(self.leaderboard)
        self.leaderboardtable.grid(row=1,column=0)
        notext=_("Nothing to see here...")
        ui.Label(self.leaderboardtable,text=notext).grid(row=1,column=0)
        # self.frame.update()
    def makeprogresstable(self):
        def groupfn(x):
            for i in x:
                try:
                    int(i)
                    log.log(3,"Integer {} fine".format(i))
                except:
                    log.log(3,"Problem with integer {}".format(i))
                    if not self.settings.hidegroupnames:
                        return nn(x,oneperline=True) #if any is not an integer, all.
            return len(x) #to show counts only
        def updateprofilencheck(profile,check):
            self.settings.slices.profile(profile)
            self.settings.params.check(check)
            #run this in any case, rather than running it not at all, or twice
        def refresh(event=None):
            self.settings.storesettingsfile()
            self.taskchooser.mainwindowis.tableiteration+=1
        self.boardtitle()
        # leaderheader=Frame(self.leaderboard) #someday, make this not scroll...
        # leaderheader.grid(row=1,column=0)
        leaderscroll=ui.ScrollingFrame(self.leaderboard)
        leaderscroll.grid(row=1,column=0)
        self.leaderboardtable=leaderscroll.content
        row=0
        #put in a footer for next profile/frame
        cvt=self.settings.params.cvt()
        ps=self.settings.slices.ps()
        profiles=self.settings.slices.profiles()
        curprofile=self.settings.slices.profile()
        curcheck=self.settings.params.check()
        frames=list(self.settings.toneframes[ps].keys())
        allchecks=[]
        for profile in profiles:
            if profile in self.settings.status[cvt][ps]:
                allchecks+=self.settings.status[cvt][ps][profile].keys()
        allchecks=list(dict.fromkeys(allchecks))
        profiles=['colheader']+profiles+['next']
        ungroups=0
        tv=_("verified")
        tu=_("unsorted data")
        t="+ = {} \n! = {}".format(tv,tu)
        h=ui.Label(self.leaderboardtable,text=t,font="small")
        h.grid(row=row,column=0,sticky='e')
        h.bind('<ButtonRelease>', refresh)
        htip=_("Refresh table, \nsave settings")
        th=ui.ToolTip(h,htip)
        r=list(self.settings.status[cvt][ps])
        log.debug("Table rows possible: {}".format(r))
        for profile in profiles:
            column=0
            if profile in ['colheader','next']+list(self.settings.status[cvt][
                                                            ps].keys()):
                if profile in self.settings.status[cvt][ps]:
                    if self.settings.status[cvt][ps][profile] == {}:
                        continue
                    #Make row header
                    t="{} ({})".format(profile,
                                len(self.settings.profilesbysense[ps][profile]))
                    h=ui.Label(self.leaderboardtable,text=t)
                    h.grid(row=row,column=column,sticky='e')
                    if profile == curprofile and curcheck is None:
                        h.config(background=h.theme['activebackground']) #highlight
                        tip=_("Current profile \n(no check set)")
                        ttb=ui.ToolTip(h,tip)
                elif profile == 'next': # end of row headers
                    brh=ui.Button(self.leaderboardtable,text=profile,
                            relief='flat',cmd=self.settings.status.nextprofile)
                    brh.grid(row=row,column=column,sticky='e')
                    brht=ui.ToolTip(brh,_("Go to the next syllable profile"))
                for check in allchecks+['next']:
                    column+=1
                    if profile == 'colheader':
                        if check == 'next': # end of column headers
                            bch=ui.Button(self.leaderboardtable,text=check,
                                        relief='flat',
                                        cmd=self.settings.status.nextcheck,
                                        font='reportheader',
                                        row=row,column=column,sticky='s')
                            bcht=ui.ToolTip(bch,_("Go to the next check"))
                        else:
                            ui.Label(self.leaderboardtable,
                                    text=rx.linebreakwords(check),
                                    font='reportheader',
                                    row=row,column=column,sticky='s',ipadx=5)
                    elif profile == 'next':
                        continue
                    elif check in self.settings.status[cvt][ps][profile]:
                        node=self.settings.status[cvt][ps][profile][check]
                        if len(node['done']) > len(node['groups']):
                            ungroups+=1
                        #At this point, these should be there
                        done=node['done']
                        total=node['groups']
                        tosort=node['tosort']
                        totalwverified=[]
                        for g in total:
                            if g in done:
                                g='+'+g #these should be strings
                            totalwverified+=[g]
                        donenum=groupfn(done)
                        totalnum=groupfn(total)
                        if (self.settings.hidegroupnames or
                            (type(totalnum) is int and type(donenum) is int)):
                            donenum="+{}/{}".format(donenum,totalnum)
                        else:
                            donenum=nn(totalwverified,oneperline=True)
                        # This should only be needed on a new database
                        if tosort == True and donenum != '':
                            donenum='!'+str(donenum) #mark data to sort
                        tb=ui.Button(self.leaderboardtable,
                                relief='flat',
                                bd=0, #border
                                text=donenum,
                                cmd=lambda p=profile,
                                f=check:updateprofilencheck(profile=p, check=f),
                                anchor='c',
                                padx=0,pady=0
                                )
                        if profile == curprofile and check == curcheck:
                            tb.configure(background=tb['activebackground'])
                            tb.configure(command=donothing)
                            tip=_("Current settings \nprofile: ‘{}’; \ncheck: ‘{}’"
                                "".format(profile,check))
                        else:
                            tip=_("Change to \nprofile: ‘{}’; \ncheck: ‘{}’"
                                "".format(profile,check))
                        tb.grid(row=row,column=column,ipadx=0,ipady=0,
                                                                sticky='nesw')
                        ttb=ui.ToolTip(tb,tip)
            row+=1
        if ungroups > 0:
            log.error(_("You have more groups verified than there are, in {} "
                        "cells".format(ungroups)))
        # self.frame.update()
    def __init__(self, parent, taskchooser, task, **kwargs):
        self.setopts()
        self.parent=parent
        self.settings=taskchooser.settings
        self.taskchooser=taskchooser
        self.task=task
        self.mainrelief=kwargs.pop('relief',None) #not for frame
        kwargs['padx']=25
        super(StatusFrame, self).__init__(parent, **kwargs)
        self.makeproseframe()
        self.interfacelangline()
        self.analangline()
        self.glosslangline()
        if isinstance(self.task,Segments):
            self.fieldsline()
        if hasattr(self.settings,'slices') and (isinstance(self.task,Sort) or
            (isinstance(self.task,Tone) and
                not isinstance(self.task,Report)) or
            (isinstance(self.task,Report) and
                not isinstance(self.task,Comprehensive))
            ):
            self.cvt=self.settings.params.cvt()
            self.ps=self.settings.slices.ps()
            self.profile=self.settings.slices.profile()
            self.check=self.settings.params.check()
            self.checks=self.settings.status.checks()
            self.sliceline()
            if not (isinstance(self.task,Report) or
                    isinstance(self.task,Record) or
                    isinstance(self.task,JoinUFgroups)
                    ):
                self.cvtline()
                self.buttoncolumnsline()
                self.maybeboard()
            elif isinstance(self.task,Segments):
                self.cvtline()
        if isinstance(self.task,Comprehensive):
            self.maxes()
        if not self.taskchooser.showreports:
            self.finalbuttons()
class Settings(object):
    """docstring for Settings."""
    def interfacelangwrapper(self,choice=None,window=None):
        if choice:
            interfacelang(choice) #change the UI *ONLY*; no object attributes
            file.writeinterfacelangtofile(choice) #>ui_lang.py, for startup
            self.set('interfacelang',choice,window) #set variable for the future
            self.storesettingsfile() #>xyz.CheckDefaults.py
            #because otherwise, this stays as is...
            self.taskchooser.mainwindowis.maketitle()
        else:
            return interfacelang()
    def mercurialwarning(self,filedir):
        title=_("Warning: Mercurial Repository without Executable")
        window=ui.Window(self.frame,title=title)
        hgurl="https://www.mercurial-scm.org/wiki/Download"
        hgfilename="Mercurial-6.0-x64.exe"
        hgfile=("https://www.mercurial-scm.org/release/windows/{}".format(
                                                                    hgfilename))
        text=_("You seem to be working on a repository of data ({}), "
        "\nwhich seems to be tracked by mercurial (used by Chorus "
        "and languagedepot.org), "
        "\nbut you don't seem to have the Mercurial executable installed in "
        "your computer's PATH.").format(filedir)
        clickable=_("Please see {} for installation recommendations").format(
                                                                program['url'])
        clickable1=_("(e.g., in Windows, install *this* file),").format(hgfile)
        clickable2=_("or see all your options at {}.").format(hgurl)
        l=ui.Label(window.frame, text=text)
        l.grid(column=0, row=0)
        m=ui.Label(window.frame, text=clickable)
        m.grid(column=0, row=1)
        m.bind("<Button-1>", lambda e: openweburl(program['url']))
        mtt=ui.ToolTip(m,_("Go to {}").format(program['url']))
        n=ui.Label(window.frame, text=clickable1)
        n.grid(column=0, row=2)
        n.bind("<Button-1>", lambda e: openweburl(hgfile))
        ntt=ui.ToolTip(n,_("download {}").format(hgfilename))
        o=ui.Label(window.frame, text=clickable2)
        o.grid(column=0, row=3)
        o.bind("<Button-1>", lambda e: openweburl(hgurl))
        mtt=ui.ToolTip(o,_("Go to {}").format(hgurl))
        window.lift()
    def repocheck(self):
        self.repo=None #leave this for test of both repo and exe
        if file.exists(file.getdiredurl(self.directory,'.hg')):
            log.info("Found Mercurial Repository!")
            if not program['hg']:
                log.info("But found no Mercurial executable!")
                self.mercurialwarning(self.directory)
            else:
                self.repo=Repository(self.directory)
    def settingsbyfile(self):
        #Here we set which settings are stored in which files
        self.settings={'defaults':{
                            'file':'defaultfile',
                            'attributes':['analang',
                                'glosslangs',
                                'audiolang',
                                'ps',
                                'profile',
                                'cvt',
                                'check',
                                'regexCV',
                                'additionalps',
                                'entriestoshow',
                                'additionalprofiles',
                                'interfacelang',
                                'examplespergrouptorecord',
                                'adnlangnames',
                                'maxpss',
                                'hidegroupnames',
                                'maxprofiles',
                                'menu',
                                'mainrelief',
                                'fontthemesmall',
                                'secondformfield',
                                'soundsettingsok',
                                'buttoncolumns',
                                'writeeverynwrites'
                                ]},
            'profiledata':{
                                'file':'profiledatafile',
                                'attributes':[
                                    'distinguish',
                                    'interpret',
                                    'polygraphs',
                                    # "profilecounts",
                                    "scount",
                                    "sextracted",
                                    "profilesbysense",
                                    "formstosearch"
                                    ]},
            'status':{
                                'file':'statusfile',
                                'attributes':['status']},
            'adhocgroups':{
                                'file':'adhocgroupsfile',
                                'attributes':['adhocgroups']},
            'soundsettings':{
                                'file':'soundsettingsfile',
                                'attributes':['sample_format',
                                            'fs',
                                            'audio_card_in',
                                            'audio_card_out',
                                            ]},
            'toneframes':{
                                'file':'toneframesfile',
                                'attributes':['toneframes']}
                                }
    def settingsfile(self,setting):
        fileattr=self.settings[setting]['file']
        if hasattr(self,fileattr):
            return getattr(self,fileattr)
        else:
            log.error("No file name for setting {}!".format(setting))
    def loadandconvertlegacysettingsfile(self,setting='defaults'):
        savefile=self.settingsfile(setting)
        legacy=savefile.with_suffix('.py')
        log.info("Going to make {} into {}".format(legacy,savefile))
        if setting == 'soundsettings':
            self.makesoundsettings()
            o=self.soundsettings
        else:
            o=self
        oldnames={'cvt':'type',
                    'check':'name',
                    'group':'subcheck'
                    }
        try:
            log.debug("Trying for {} settings in {}".format(setting, legacy))
            spec = importlib.util.spec_from_file_location(setting,legacy)
            module = importlib.util.module_from_spec(spec)
            sys.modules[setting] = module
            spec.loader.exec_module(module)
            for s in self.settings[setting]['attributes']:
                if s in oldnames and hasattr(module,oldnames[s]):
                    setattr(o,s,getattr(module,oldnames[s]))
                    log.info("Imported and upgraded {}/{}: {}".format(
                                                    s,oldnames[s],getattr(o,s)))
                elif hasattr(module,s):
                    setattr(o,s,getattr(module,s))
                    log.info("Imported {}: {}".format(s,getattr(o,s)))
                else:
                    log.info("Attribute {} not found".format(s))
            log.info("Importing {} settings done.".format(setting))
        except Exception as e:
            log.error("Problem importing {} ({})".format(legacy,e))
        # b/c structure changed:
        if 'glosslangs' in self.settings[setting]['attributes']:
            self.glosslangs=[]
            for lang in ['glosslang','glosslang2']:
                if hasattr(module,lang):
                    self.glosslangs.append(getattr(module,lang))
                    delattr(self,lang) #because this would be made above
        dict1=self.makesettingsdict(setting=setting)
        self.storesettingsfile(setting=setting) #do last
        self.loadsettingsfile(setting=setting) #verify write and read
        dict2=self.makesettingsdict(setting=setting)
        """Now we verify that each value read the same each time"""
        for s in dict1:
            if s in dict2 and str(dict1[s]) == str(dict2[s]):
                log.info("Attribute {} verified as {}={}".format(s,
                                            str(dict1[s]), str(dict2[s])))
            elif s in dict2:
                log.error("Problem with attribute {}; {}≠{}".format(s,
                                            str(dict1[s]), str(dict2[s])))
            else:
                log.error("Attribute {} didn't make it back".format(s))
                log.error("You should send in an error report for this.")
                exit()
        log.info("Settings file {} converted to {}, with each value verified."
                "".format(legacy,savefile))
    def settingsfilecheck(self):
        """We need the namebase variable to make filenames for files
        that will be imported as python modules. To do that, they need
        to not have periods (.) in their filenames. So we take the base
        name from the lift file, and replace periods with underscores,
        to make our modules basename."""
        self.liftnamebase=rx.pymoduleable(file.getfilenamebase(
                                                            self.liftfilename))
        # re.sub('\.','_', str(
        basename=file.getdiredurl(self.directory,self.liftnamebase)
        self.defaultfile=basename.with_suffix('.CheckDefaults.ini')
        self.toneframesfile=basename.with_suffix(".ToneFrames.dat")
        self.statusfile=basename.with_suffix(".VerificationStatus.dat")
        self.profiledatafile=basename.with_suffix(".ProfileData.dat")
        self.adhocgroupsfile=basename.with_suffix(".AdHocGroups.dat")
        self.soundsettingsfile=basename.with_suffix(".SoundSettings.ini")
        self.settingsbyfile() #This just sets self.settings
        for setting in self.settings:#[setting]
            savefile=self.settingsfile(setting)#self.settings[setting]['file']
            if not file.exists(savefile):
                log.debug("{} doesn't exist!".format(savefile))
                legacy=savefile.with_suffix('.py')
                if file.exists(legacy):
                    log.debug("But legacy file {} does; converting!".format(legacy))
                    self.loadandconvertlegacysettingsfile(setting=setting)
            if (str(savefile).endswith('.dat') and
                    file.exists(savefile) and
                    self.repo and
                    not me):
                self.repo.add(savefile)
        if self.repo:
            self.repo.commit()
    def moveattrstoobjects(self):
        # log.info("Glosslangs (in moveattrstoobjects): {}".format(self.glosslangs.langs()))
        for attr in self.fndict:
            if hasattr(self,attr):
                log.info("moving attr {} to object ({})".format(attr,getattr(self,attr)))
                self.fndict[attr](getattr(self,attr))
                # log.info("Glosslangs (in moveattrstoobjects): {}".format(self.glosslangs.langs()))
                if attr not in ['glosslangs']: #obj and attr have same name...
                    delattr(self,attr)
        # log.info("Glosslangs (in moveattrstoobjects): {}".format(self.glosslangs.langs()))
    def settingsobjects(self):
        """These should each push and pull values to/from objects"""
        self.fndict=fns={}
        try: #these objects may not exist yet
            fns['cvt']=self.params.cvt
            fns['check']=self.params.check
            fns['analang']=self.params.analang
            fns['glosslang']=self.glosslangs.lang1
            fns['glosslang2']=self.glosslangs.lang2
            fns['glosslangs']=self.glosslangs.langs
            fns['ps']=self.slices.ps
            fns['profile']=self.slices.profile
            # except this one, which pretends to set but doesn't (throws arg away)
            fns['profilecounts']=self.slices.slicepriority
        except:
            log.error("Only finished settingsobjects up to {}".format(fns))
            return []
    def makesettingsdict(self,setting='defaults'):
        """This returns a dictionary of values, keyed by a set of settings"""
        """It pulls from objects if it can, otherwise from self attributes
        (if there), for backwards compatibility, when converting from legacy
        files before the objects are created."""
        d={}
        if setting == 'soundsettings':
            o=self.soundsettings
        else:
            o=self
        for s in self.settings[setting]['attributes']:
            # log.info("Looking for {} attr".format(s))
            """This dictionary of functions isn't made until after the objects,
            at the end of settings init. So this block is not used in
            conversion, only in later saves."""
            if hasattr(self,'fndict') and s in self.fndict:
                # log.info("Trying to dict {} attr".format(s))
                try:
                    d[s]=self.fndict[s]()
                    log.info("Value {}={} found in object".format(s,d[s]))
                except:
                    log.log(4,"Value of {} not found in object".format(s))
            elif hasattr(o,s) and getattr(o,s):
                d[s]=getattr(o,s)
                # log.log(4,"Trying to dict self.{} with value {}, type {}"
                #         "".format(s,d[s],type(d[s])))
            # else:
            #     log.error("Couldn't find {} in {}".format(s,setting))
        """This is the only glosslang > glosslangs conversion"""
        if 'glosslangs' in d and d['glosslangs'] in [None,[]]:
            if 'glosslang' in d and d['glosslang'] is not None:
                d['glosslangs']=[d['glosslang']]
                del d['glosslang']
                if 'glosslang2' in d and d['glosslang2'] is not None:
                    d['glosslangs'].append(d['glosslang2'])
                    del d['glosslang2']
        return d
    def readsettingsdict(self,dict):
        """This takes a dictionary keyed by attribute names"""
        d=dict
        if 'fs' in dict:
            o=self.soundsettings
        else:
            o=self
        for s in dict:
            v=d[s]
            if hasattr(self,'fndict') and s in self.fndict:
                log.debug("Trying to read {} to object with value {} and fn "
                            "{}".format(s,v,self.fndict[s]))
                self.fndict[s](v)
            else:
                log.debug("Trying to read {} to {} with value {}, type {}"
                            "".format(s,o,v,type(v)))
                setattr(o,s,v)
        return d
    def storesettingsfile(self,setting='defaults',noobjects=False):
        filename=self.settingsfile(setting)
        config=ConfigParser()
        config['default']={}
        d=self.makesettingsdict(setting=setting)
        for s in [i for i in d if i not in [None,'None']]:
            v=d[s]
            if isinstance(v, dict):
                config[s]=v
            else:
                config['default'][s]=str(v)
        if config['default'] == {}:
            del config['default']
        header=("# This settings file was made on {} on {}".format(
                                                    now(),platform.uname().node)
                )
        with open(filename, "w", encoding='utf-8') as file:
            file.write(header+'\n\n')
            config.write(file)
    def loadsettingsfile(self,setting='defaults'):
        filename=self.settingsfile(setting)
        config=ConfigParser()
        config.read(filename,encoding='utf-8')
        if len(config.sections()) == 0:
            if setting == "adhocgroups":
                self.adhocgroups={}
            return
        log.debug("Trying for {} settings in {}".format(setting, filename))
        d={}
        for section in self.settings[setting]['attributes']:
            if section in config:
                log.debug("Trying for {} settings in {}".format(section, setting))
                if len(config[section].values())>0:
                    log.debug("Found Dictionary value for {}".format(section))
                    d[section]={}
                    for s in config[section]:
                        d[section][s]={}
                        """Make sure strings become python data"""
                        d[section][ofromstr(s)]=ofromstr(config[section][s])
                else:
                    log.debug("Found String/list/other value for {}: {}".format(
                                                    section,config[section]))
                    d[section]=ofromstr(config[section])
            elif 'default' in config and section in config['default']:
                d[section]=ofromstr(config['default'][section])
        self.readsettingsdict(d)
    def initdefaults(self):
        """Some of these defaults should be reset when setting another field.
        These are listed under that other field. If no field is specified
        (e.g., on initialization), then do all the fields with None key (other
        fields are NOT saved to file!).
        These are check related defaults; others in lift.get"""
        self.defaultstoclear={'ps':[
                            'profile' #do I want this?
                            # 'name',
                            # 'subcheck'
                            ],
                        'analang':[
                            'glosslangs',
                            'ps',
                            'profile',
                            'cvt',
                            'check',
                            'subcheck'
                            ],
                        'interfacelang':[],
                        'glosslangs':[],
                        'check':[],
                        'subcheck':[
                            'regexCV'
                            ],
                        'group_comparison':[],
                        'profile':[
                            # 'name'
                            ],
                        'cvt':[
                            'check',
                            # 'subcheck'
                            ],
                        'fs':[],
                        'sample_format':[],
                        'audio_card_index':[],
                        'audioout_card_index':[],
                        'examplespergrouptorecord':[],
                        'distinguish':[],
                        'interpret':[],
                        'adnlangnames':[],
                        'hidegroupnames':[],
                        'maxprofiles':[]
                        }
    def cleardefaults(self,field=None):
        if field==None:
            fields=self.settings['defaults']['attributes']
        else:
            fields=self.defaultstoclear[field]
        for default in fields: #self.defaultstoclear[field]:
            setattr(self, default, None)
    def settingsinit(self):
        log.info("Initializing settings.")
        # self.defaults is already there, from settingsfilecheck
        self.initdefaults() #provides self.defaultstoclear, needed?
        self.cleardefaults() #this resets all to none (to be set below)
        self.pss() #sets self.nominalps and self.verbalps
        self.fields() #sets self.pluralname and self.imperativename
    def getdirectories(self):
        self.directory=file.getfilenamedir(self.liftfilename)
        if not file.exists(self.directory):
            log.info(_("Looks like there's a problem with your directory... {}"
                    "\n{}".format(self.liftfilename,filemod)))
            exit()
        self.repocheck()
        self.settingsfilecheck()
        self.imagesdir=file.getimagesdir(self.directory)
        self.audiodir=file.getaudiodir(self.directory)
        log.info('self.audiodir: {}'.format(self.audiodir))
        self.reportsdir=file.getreportdir(self.directory)
        self.reportbasefilename=file.getdiredurl(self.reportsdir,
                                                    self.liftnamebase)
        self.reporttoaudiorelURL=file.getreldir(self.reportsdir, self.audiodir)
        log.log(2,'self.reportsdir: {}'.format(self.reportsdir))
        log.log(2,'self.reportbasefilename: {}'.format(self.reportbasefilename))
        log.log(2,'self.reporttoaudiorelURL: {}'.format(self.reporttoaudiorelURL))
        # setdefaults.langs(self.db) #This will be done again, on resets
    def pss(self):
        log.info("checking these lexical category names for plausible noun "
                "and verb names: {}".format(self.db.pss))
        for ps in self.db.pss[:2]:
            if ps in ['N','n','Noun','noun',
                    'Nom','nom',
                    'S','s','Sustantivo','sustantivo'
                    ]:
                self.nominalps=ps
            elif ps in ['V','v','Verb','verb',
                    'Verbe','verbe',
                    'Verbo','verbo'
                    ]:
                self.verbalps=ps
            else:
                log.error("Not sure what to do with top ps {}".format(ps))
        if not hasattr(self,'nominalps'):
                self.nominalps='Noun'
        if not hasattr(self,'verbalps'):
                self.verbalps='Verb'
        try:
            log.info("Using ‘{}’ for nouns, and ‘{}’ for verbs".format(self.nominalps,
                self.verbalps))
        except AttributeError:
            log.info("Problem with finding a nominal and verbal lexical "
            "category (looked in first two of [{}])".format(self.db.pss))
    def fields(self):
        """I think this is lift specific; may move it to defaults, if not."""
        fields=self.db.fields
        self.secondformfield={}
        log.info(_("Fields found in lexicon: {}".format(str(fields))))
        self.plopts=['Plural', 'plural', 'pl', 'Pluriel', 'pluriel']
        self.impopts=['Imperative', 'imperative', 'imp', 'Imp']
        for opt in self.plopts:
            if opt in fields:
                self.secondformfield[self.nominalps]=self.pluralname=opt
        try:
            log.info(_('Plural field name: {}').format(self.pluralname))
        except AttributeError:
            log.info(_('Looks like there is no Plural field in the database'))
            self.pluralname=None
        for opt in self.impopts:
            if opt in fields:
                self.secondformfield[self.verbalps]=self.imperativename=opt
        try:
            log.info(_('Imperative field name: {}'.format(self.imperativename)))
        except AttributeError:
            log.info(_('Looks like there is no Imperative field in the database'))
            self.imperativename=None
    def askaboutpolygraphs(self):
        def nochanges():
            log.info("Trying to make no changes")
            if foundchanges() and not pgw.exitFlag.istrue():
                log.info("Found changes; exiting.")
                pgw.destroy()
                self.parent.destroy()
                exit()
            elif not pgw.exitFlag.istrue():
                pgw.destroy()
        def makechanges():
            log.info("Changes called for; like it or not, redoing analysis.")
            pgw.destroy()
            if not foundchanges():
                log.info("User asked for changes to polygraph settings, but "
                        "no changes found.")
                return
            for lang in self.db.analangs:
                for pc in vars[lang]:
                    for pg in vars[lang][pc]:
                        self.polygraphs[lang][pc][pg]=vars[lang][pc][pg].get()
            # self.storesettingsfile(setting='profiledata') Done below!
            self.reloadprofiledata()
        def foundchanges():
            for lang in vars:
                if lang not in self.polygraphs:
                    return True
                for pc in vars[lang]:
                    if pc not in self.polygraphs[lang]:
                        return True
                    for pg in vars[lang][pc]:
                        if pg not in self.polygraphs[lang][pc]:
                            return True
                        v=vars[lang][pc][pg].get()
                        if self.polygraphs[lang][pc][pg]!=v:
                            return True
            log.info("No changes found to polygraph settings, continuing.")
        oktext=_("OK")
        nochangetext=_("Exit {} with no changes".format(program['name']))
        log.info("Asking about Digraphs and Trigraphs!")
        titlet=_("A→Z+T Digraphs and Trigraphs")
        pgw=ui.Window(self.taskchooser.frame,title=titlet)
        t=_("Select which of the following graph sequences found in your data "
                "refer to a single sound (digraph or trigraph) in {}".format(
            unlist([self.languagenames[y] for y in self.db.analangs])))
        row=0
        title=ui.Label(pgw.frame,text=titlet, font='title',
                        column=0, row=row
                        )
        title.wrap()
        row+=1
        b=ui.Button(pgw.frame,text=nochangetext,command=nochanges,
                    column=0, row=row, sticky='e')
        row+=1
        instr=ui.Label(pgw.frame,text=t,
                        column=0, row=row
                        )
        instr.wrap()
        t=_("If your data contains a digraph or trigraph that isn't listed "
            "here, please click here to Email me, and I can add it.")
        row+=1
        t2=ui.Label(pgw.frame,text=t,column=0, row=row)
        t2.bind("<Button-1>", lambda e: openweburl(eurl))
        t=_("Clicking ‘{}’ will restart {} and trigger another syllable "
            "profile analysis. \nIf you don't want that, click ‘{}’ ==>"
            "\nEither way, you won't get past this window until you answer "
            "This question.".format(
                                        oktext,program['name'],nochangetext))
        row+=1
        t3=ui.Label(pgw.frame,text=t,column=0, row=row)
        eurl='mailto:{}?subject=New trigraph or digraph to add (today)'.format(
                                                            program['Email'])
        if not hasattr(self,'polygraphs'):
            self.polygraphs={}
        vars={}
        row+=1
        scroll=ui.ScrollingFrame(pgw.frame, row=row, column=0)
        row=0
        ncols=4 # increase this for wider window
        for lang in self.db.analangs:
            if lang not in self.polygraphs:
                self.polygraphs[lang]={}
            row+=1
            title=ui.Label(scroll.content,text=self.languagenames[lang],
                                                        font='read')
            title.grid(column=0, row=row, columnspan=ncols)
            vars[lang]={}
            for sclass in [sc for sc in self.db.s[lang] #Vtg, Vdg, Ctg, Cdg, etc
                                    if ('dg' in sc or 'tg' in sc)]:
                pclass=sclass.replace('dg','').replace('tg','')
                if pclass not in self.polygraphs[lang]:
                    self.polygraphs[lang][pclass]={}
                if pclass not in vars[lang]:
                    vars[lang][pclass]={}
                if len(self.db.s[lang][sclass])>0:
                    row+=1
                    header=ui.Label(scroll.content,
                    text=sclass.replace('dg',' (digraph)').replace('tg',
                                                            ' (trigraph)')+': ')
                    header.grid(column=0, row=row)
                col=1
                for pg in self.db.s[lang][sclass]:
                    vars[lang][pclass][pg] = ui.BooleanVar()
                    vars[lang][pclass][pg].set(
                                    self.polygraphs[lang][pclass].get(pg,False))
                    cb=ui.CheckButton(scroll.content, text = pg, #.content
                                        variable = vars[lang][pclass][pg],
                                        onvalue = True, offvalue = False,
                                        )
                    cb.grid(column=col, row=row,sticky='nsew')
                    if col<= ncols:
                        col+=1
                    else:
                        col=1 #not header
                        row+=1
        row+=1
        b=ui.Button(pgw.frame,text=oktext,command=makechanges, width=15,
                    column=0, row=row, sticky='e',padx=15)
        pgw.wait_window(pgw)
        if not self.taskchooser.exitFlag.istrue():
            nochanges() #this is the default exit behavior
    def polygraphcheck(self):
        log.info("Checking for Digraphs and Trigraphs!")
        if not hasattr(self,'polygraphs'):
            self.polygraphs={}
        for lang in self.db.analangs:
            if lang not in self.polygraphs:
                self.polygraphs[lang]={}
            for sclass in [sc for sc in self.db.s[lang]
                                    if ('dg' in sc or 'tg' in sc)]:
                pclass=sclass.replace('dg','').replace('tg','')
                if pclass not in self.polygraphs[lang]:
                    self.polygraphs[lang][pclass]={}
                for pg in self.db.s[lang][sclass]:
                    if pg not in self.polygraphs[lang][pclass]:
                        log.info("{} ([]/{}) has no Di/Trigraph setting; "
                        "prompting user or info.".format(pg,pclass,sclass))
                        self.askaboutpolygraphs()
                        return
        log.info("Di/Trigraph settings seem complete; moving on.")
    def checkinterpretations(self):
        if (not hasattr(self,'distinguish')) or (self.distinguish is None):
            self.distinguish={}
        if (not hasattr(self,'interpret')) or (self.interpret is None):
            self.interpret={}
        for var in ['G','Gwd','N','S','Swd','D','Dwd','Nwd','ʔ','ʔwd',
                    "̀",'ː','<','=']:
            if ((var not in self.distinguish) or
                (type(self.distinguish[var]) is not bool)):
                self.distinguish[var]=False
            """These defaults are not settable, yet:"""
            if var in ["̀",'ː']: #typically word-forming
                self.distinguish[var]=False
            if var in ['<','=']: #typically not word-forming
                self.distinguish[var]=True
        for var in ['NC','CG','CS','VV','VN']:
            if ((var not in self.interpret) or
                (type(self.interpret[var]) is not str) or
                not(1 <=len(self.interpret[var])<= 2)):
                if (var == 'VV') or (var == 'VN'):
                    self.interpret[var]=var
                else:
                    self.interpret[var]='CC'
        if self.interpret['VV']=='Vː' and self.distinguish['ː']==False:
            self.interpret['VV']='VV'
        log.log(2,"self.distinguish: {}".format(self.distinguish))
    def checkforprofileanalysis(self):
        if not hasattr(self,'profilesbysense') or self.profilesbysense == {}:
            t=time.time()-self.taskchooser.start_time
            log.info("Starting profile analysis at {}".format(t))
            self.getprofiles() #creates self.profilesbysense nested dicts
            for var in ['rx','profilesbysense']:
                log.debug("{}: {}".format(var,getattr(self,var)))
            self.storesettingsfile(setting='profiledata')
            e=time.time()-self.taskchooser.start_time
            log.info("Finished profile analysis at {} ({}s)".format(e,e-t))
    def addpstoprofileswdata(self,ps=None):
        if ps is None:
            ps=self.slices.ps()
        if ps not in self.profilesbysense:
            self.profilesbysense[ps]={}
    def addprofiletoprofileswdata(self,ps=None,profile=None):
        if ps is None:
            ps=self.slices.ps()
        if profile is None:
            profile=self.slices.profile()
        if profile not in self.profilesbysense[ps]:
            self.profilesbysense[ps][profile]=[]
    def addtoprofilesbysense(self,senseid,ps=None,profile=None):
        if ps is None:
            if hasattr(self,'slices'):
                ps=self.slices.ps()
            else:
                log.error("You didn't specifiy ps, but don't have slices yet!")
                return
        self.addpstoprofileswdata(ps=ps)
        if profile is None:
            profile=self.slices.profile()
        self.addprofiletoprofileswdata(ps=ps,profile=profile)
        self.profilesbysense[ps][profile]+=[senseid]
    def getprofileofsense(self,senseid):
        #Convert to iterate over local variables
        ps=unlist(self.db.ps(senseid=senseid))
        if ps in [None,'None','']:
            return None,'NoPS'
        forms=self.db.citationorlexeme(senseid=senseid,
            analang=self.params.analang())
        if forms == []:
            profile='Invalid'
            self.addtoprofilesbysense(senseid, ps=ps, profile=profile)
            return None, profile
        if forms is None:
            return None,'Invalid'
        for form in forms:
            """This adds to self.sextracted, too"""
            profile=self.profileofform(form,ps=ps)
            if not set(self.profilelegit).issuperset(profile):
                profile='Invalid'
            self.addtoprofilesbysense(senseid, ps=ps, profile=profile)
            if ps not in self.formstosearch:
                self.formstosearch[ps]={}
            if form in self.formstosearch[ps]:
                self.formstosearch[ps][form].append(senseid)
            else:
                self.formstosearch[ps][form]=[senseid]
        return firstoflist(forms),profile
    def getprofiles(self):
        self.profileswdatabyentry={}
        self.profilesbysense={}
        self.profilesbysense['Invalid']=[]
        self.profiledguids=[]
        self.profiledsenseids=[]
        self.formstosearch={}
        self.sextracted={} #Will store matching segments here
        for ps in self.db.pss:
            self.sextracted[ps]={}
            for s in self.rx:
                self.sextracted[ps][s]={}
        todo=len(self.db.senseids)
        x=0
        for senseid in self.db.senseids:
            x+=1
            form,profile=self.getprofileofsense(senseid)
            if x % 10 == 0:
                log.debug("{}: {}; {}".format(str(x)+'/'+str(todo),form,
                                            profile))
        #Convert to iterate over local variables
        """Do I want this? better to keep the adhoc groups separate"""
        """We will *never* have slices set up by this time; read from file."""
        if hasattr(self,'adhocgroups'):
            for ps in self.adhocgroups:
                for a in self.adhocgroups[ps]:
                    log.debug("Adding {} to {} ps-profile: {}".format(a,ps,
                                                self.adhocgroups[ps][a]))
                    self.addpstoprofileswdata(ps=ps) #in case the ps isn't already there
                    #copy over stored values:
                    self.profilesbysense[ps][a]=self.adhocgroups[ps][a]
                    log.debug("resulting profilesbysense: {}".format(
                                            self.profilesbysense[ps][a]))
    def profileofformpreferred(self,form):
        """Simplify combinations where desired"""
        for c in ['N','S','G','ʔ','D']:
            if self.distinguish[c] is False:
                form=self.rx[c+'_'].sub('C',form)
            if self.distinguish[c+'wd'] is False:
                form=self.rx[c+'wd'].sub('C',form)
                # log.debug("{}wd regex result: {}".format(c,form))
        for o in ["̀",'<','=','ː']:
            if self.distinguish[o] is False and o in self.rx:
                form=self.rx[o].sub('',form)
        for cc in ['CG','CS','NC','VN','VV']:
            form=self.rx[cc].sub(self.interpret[cc],form)
        return form
    def profileofform(self,form,ps):
        if not form or not ps:
            return "Invalid"
        # log.debug("profiling {}...".format(form))
        formori=form
        """priority sort alphabets (need logic to set one or the other)"""
        """Look for any C, don't find N or G"""
        # self.profilelegit=['#','̃','C','N','G','S','V']
        """Look for word boundaries, N and G before C (though this doesn't
        work, since CG is captured by C first...)"""
        # self.profilelegit=['#','̃','N','G','S','C','Ṽ','V','d','b']
        log.log(4,"Searching {} in this order: {}".format(form,self.profilelegit
                        ))
        log.log(4,"Searching with these regexes: {}".format(self.rx))
        for s in set(self.profilelegit) & set(self.rx.keys()):
            log.log(3,'s: {}; rx: {}'.format(s, self.rx[s]))
            for i in self.rx[s].findall(form):
                if i not in self.sextracted[ps][s]:
                    self.sextracted[ps][s][i]=0
                self.sextracted[ps][s][i]+=1 #self.rx[s].subn('',form)[1] #just the count
            form=self.rx[s].sub(s,form) #replace with profile variable
        """We could consider combining NC to C (or not), and CG to C (or not)
        here, after the 'splitter' profiles are formed..."""
        # log.debug("{}: {}".format(formori,form))
        # log.info("Form before simplification:{}".format(form))
        form=self.profileofformpreferred(form)
        # log.info("Form after simplification:{}".format(form))
        return form
    def getscounts(self):
        """This depends on self.sextracted, from getprofiles, so should only
        run when that changes."""
        scount={}
        for ps in self.db.pss:
            scount[ps]={}
            for s in self.rx:
                try:
                    scount[ps][s]=sorted([(x,self.sextracted[ps][s][x])
                        for x in self.sextracted[ps][s]],key=lambda x:x[1],
                                                                reverse=True)
                except KeyError as e:
                    log.info(_("{} KeyError reading {}-{} from sextracted"
                                "").format(e,ps,s))
        self.slices.scount(scount) #send to object
    def notifyuserofextrasegments(self):
        if not hasattr(self,'analang'):
            self.analang=self.params.analang()
        if self.analang not in self.db.segmentsnotinregexes:
            return
        invalids=self.db.segmentsnotinregexes[self.analang]
        ninvalids=len(invalids)
        extras=list(dict.fromkeys(invalids).keys())
        if ninvalids >10 and self.analang != 'en':
            text=_("Your {} database has the following symbols, which are "
                "excluding {} words from being analyzed: \n{}"
                "".format(self.analang,ninvalids,extras))
            title=_("More than Ten Invalid Characters Found!")
            self.warning=ErrorNotice(text,title=title)
            # l=ui.Label(self.warning, text=t)
            # l.grid(row=0, column=0)
    def slists(self):
        """This sets up the lists of segments, by types. For the moment, it
        just pulls from the segment types in the lift database."""
        if not hasattr(self,'s'):
            self.s={}
        for lang in self.db.analangs:
            if lang not in self.s:
                self.s[lang]={}
            """These should always be there, no matter what"""
            for sclass in [x for x in self.db.s[lang]
                                        if 'dg' not in x and 'tg' not in x]: #Just populate each list now
                if sclass in self.polygraphs[lang]:
                    pgthere=[k for k,v in self.polygraphs[lang][sclass].items() if v]
                    log.debug("Polygraphs for {} in {}: {}".format(lang,sclass,
                                                                    pgthere))
                    self.s[lang][sclass]=pgthere
                else:
                    self.s[lang][sclass]=list()
                self.s[lang][sclass]+=self.db.s[lang][sclass]
                """These lines just add to a C list, for a later regex"""
            log.info("Segment lists for {} language: {}".format(lang,
                                                                self.s[lang]))
    def setinvalidcharacters(self):
        self.invalidchars=[' ','...',')','(<field type="tone"><form lang="gnd"><text>'] #multiple characters not working.
        self.invalidregex='( |\.|,|\)|\()+'
        # self.profilelegit=['#','̃','C','N','G','S','V','o'] #In 'alphabetical' order
        self.profilelegit=['#','̃','N','G','S','D','C','Ṽ','V','ʔ','ː',"̀",'=','<'] #'alphabetical' order
    def setupCVrxs(self):
        self.rx={}
        for sclass in list(self.s[self.analang])+['C']: #be sure to do C last
            if self.s[self.analang][sclass] != []: #don't make if empty
                if sclass in ['G','N','S','D'] and not self.distinguish[sclass]:
                    self.s[self.analang]['C']+=self.s[self.analang][sclass]
                    continue
                self.rx[sclass]=rx.make(rx.s(self,sclass),compile=True)
        #Compile preferred regexs here
        for cc in ['CG','CS','NC','VN','VV']:
            ccc=cc.replace('C','[CSGDʔN]{1}')
            self.rx[cc]=rx.compile(ccc)
        for c in ['N','S','G','ʔ','D']:
            if c == 'N': #i.e., before C
                self.rx[c+'_']=rx.compile(c+'(?!([CSGDʔ]|\Z))') #{1}|
            elif c in ['ʔ','D']:
                self.rx[c+'_']=rx.compile(c+'(?!\Z)')
            else:
                self.rx[c+'_']=rx.compile('(?<![CSGDNʔ])'+c)
            self.rx[c+'wd']=rx.compile(c+'(?=\Z)')
    def checkforlegacyverification(self):
        start_time=time.time()
        n=0
        for ps in self.profilesbysense:
            for profile in self.profilesbysense[ps]:
                for senseid in self.profilesbysense[ps][profile]:
                    if profile != 'Invalid':
                        node=self.db.legacyverificationconvert(senseid,vtype=profile,
                                                            lang=self.analang)
                        if node is not None:
                            n+=1
        self.db.write()
        log.info("Found {} legacy verification nodes in {} seconds".format(n,
                                                time.time()-start_time))
    def reloadprofiledata(self):
        self.storesettingsfile() # why?
        self.profilesbysense={}
        self.storesettingsfile(setting='profiledata')
        self.taskchooser.restart()
    def reloadstatusdata(self):
        # This fn is very inefficient, as it iterates over everything in
        # profilesbysense, creating status dictionaries for all of that, in
        # order to populate it if found —before removing empty entires.
        # This also has no access to verification information, which comes only
        # from verify()
        start_time=time.time()
        self.storesettingsfile()
        pss=self.slices.pss() #this depends on nothing
        cvts=[i for i in self.params.cvts() if i in self.status]
        if not cvts:
            cvts=[i for i in self.params.cvts()]
        for t in cvts: #this depends on nothing
            log.info("Working on {}".format(t))
            for ps in pss:
                log.info("Working on {}".format(ps))
                profiles=self.slices.profiles(ps=ps) #This depends on ps only
                for p in profiles:
                    log.info("Working on {}".format(p))
                    checks=self.status.checks(ps=ps,profile=p)
                    for c in checks:
                        log.info("Working on {}".format(c))
                        self.status.build(cvt=t, ps=ps, profile=p, check=c)
                        """this just populates groups and the tosort boolean."""
                        self.updatesortingstatus(cvt=t,ps=ps,profile=p,check=c,
                                                store=False) #do below
        """Now remove what didn't get data"""
        self.status.cull()
        if None in self.status: #This should never be there
            del self.status[None]
        self.storesettingsfile(setting='status')
        log.info("Status settings refreshed from LIFT in {}s".format(
                                                        time.time()-start_time))
    def guessanalang(self):
        #have this call set()?
        """if there's only one analysis language, use it."""
        nlangs=len(self.db.analangs)
        log.debug(_("Found {} analangs: {}".format(nlangs,self.db.analangs)))
        lxwdata=self.db.nentrieswlexemedata
        lcwdata=self.db.nentrieswcitationdata
        lxwdatamax=lcwdatamax=None
        for lang in [l for l in lxwdata if lxwdata[l] > 0]:
            if not lxwdatamax or lxwdata[lxwdatamax] < lxwdata[lang]:
                lxwdatamax=lang
        for lang in [l for l in lcwdata if lcwdata[l] > 0]:
            if not lcwdatamax or lcwdata[lcwdatamax] < lcwdata[lang]:
                lcwdatamax=lang
        log.info("Most citation data in [{}] ({})".format(lcwdatamax,lcwdata))
        log.info("Most lexeme data in [{}] ({})".format(lxwdatamax,lxwdata))
        if not nlangs:
            errortext=_("There don't seem to be any language forms in your "
            "database!")
            basename=file.getfilenamebase(self.liftfilename)
            parent=file.getfilenamebase(file.getfilenamedir(self.liftfilename))
            if parent == basename and len(parent) == 3: #plausible iso
                self.analang=parent
                errortext+=_("\n(guessing [{}]; if that's not correct, exit now "
                            "and fix it!)").format(self.analang)
            log.info(errortext)
            e=ErrorNotice(errortext,title=_("Error!"),wait=True)
            # return
        elif nlangs == 1:
            self.analang=self.db.analangs[0]
            log.debug(_('Only one analang in file; using it: ({})'.format(
                                                        self.db.analangs[0])))
            """If there are more than two analangs in the database, check if one
            of the first two is three letters long, and the other isn't"""
        elif nlangs == 2:
            if ((len(self.db.analangs[0]) == 3) and
                (lcwdatamax == self.db.analangs[0] or
                    lxwdatamax == self.db.analangs[0]) and
                (len(self.db.analangs[1]) != 3)):
                log.debug(_('Looks like I found an iso code with data for '
                                'analang! ({})'.format(self.db.analangs[0])))
                self.analang=self.db.analangs[0] #assume this is the iso code
                self.analangdefault=self.db.analangs[0] #In case it gets changed.
            elif ((len(self.db.analangs[1]) == 3) and
                (lcwdatamax == self.db.analangs[1] or
                    lxwdatamax == self.db.analangs[1]) and
                    (len(self.db.analangs[0]) != 3)):
                log.debug(_('Looks like I found an iso code with data for '
                                'analang! ({})'.format(self.db.analangs[1])))
                self.analang=self.db.analangs[1] #assume this is the iso code
                self.analangdefault=self.db.analangs[1] #In case it gets changed.
            elif lcwdatamax in self.db.analangs:
                self.analang=lcwdatamax
                log.debug('Neither analang looks like an iso code, taking the '
                'one with most citation data: {}'.format(self.db.analangs))
            elif lxwdatamax in self.db.analangs:
                self.analang=lxwdatamax
                log.debug('Neither analang looks like an iso code, taking the '
                'one with most lexeme data: {}'.format(self.db.analangs))
            else:
                self.analang=self.db.analangs[0]
                log.debug('Neither analang looks like an iso code, nor has much'
                'data; taking the first one: {}'.format(self.db.analangs))
        else: #for three or more analangs, take the first plausible iso code
            if lcwdatamax in self.db.analangs and len(lcwdatamax) == 3:
                self.analang=lcwdatamax
                log.debug('The language with the most citation data looks like '
                'an iso code; using: {}'.format(self.db.analangs))
            elif lcwdatamax == lxwdatamax and lxwdatamax in self.db.analangs:
                self.analang=lxwdatamax
                log.debug('The language with the most citation data is also '
                    'the language with the most lexeme data; using: {}'.format(
                                                            self.db.analangs))
            elif lxwdatamax in self.db.analangs and len(lxwdatamax) == 3:
                self.analang=lxwdatamax
                log.debug('The language with the most lexeme data looks like '
                'an iso code; using: {}'.format(self.db.analangs))
            else:
                for n in range(1,nlangs+1): # end with first
                    self.analang=self.db.analangs[-n]
                    log.debug(_('trying {}').format(self.analang))
                    if len(self.db.analangs[-n]) == 3:
                        log.debug(_('Looks like I found an iso code for '
                                'analang! ({})'.format(self.db.analangs[n-1])))
                        break #stop iterating, and keep this one.
        log.info("analang guessed: {} (If you don't like this, change it in "
                    "the menus)".format(self.analang))
    def guessaudiolang(self):
        nlangs=len(self.db.audiolangs)
        """if there's only one audio language, use it."""
        if nlangs == 0 and self.analang:
            self.audiolang=lift.Lift.makeaudiolangname(self) #self.db.audiolangs[0]
        if nlangs == 1:
            self.audiolang=self.db.audiolangs[0]
        elif nlangs == 2:
            if ((self.analang in self.db.audiolangs[0]) and
                (self.analang not in self.db.audiolangs[1])):
                self.audiolang=self.db.audiolangs[0]
                log.info("Analang in first of two audiolangs only, selecting "
                                            "{}".format(self.audiolang))
            elif ((self.analang in self.db.audiolangs[1]) and
                    (self.analang not in self.db.audiolangs[0])):
                self.audiolang=self.db.audiolangs[1]
                log.info("Analang in second of two audiolangs only, selecting "
                                            "{}".format(self.audiolang))
            elif ((self.analang in self.db.audiolangs[1]) and
                    (self.analang in self.db.audiolangs[0])):
                self.audiolang=sorted(self.db.audiolangs,key = len)[0]
                log.info("Analang in both of two audiolangs only, selecting "
                "shorter: {}".format(self.audiolang))  #assume is more basic
        else: #for three or more analangs, take the first plausible iso code
            for n in range(nlangs):
                if self.analang in self.db.analangs[n]:
                    self.audiolang=self.db.audiolangs[n]
                    return
    def makeglosslangs(self):
        if self.glosslangs:
            self.glosslangs=Glosslangs(self.glosslangs)
        else:
            self.glosslangs=Glosslangs()
    def checkglosslangs(self):
        if self.glosslangs:
            for lang in self.glosslangs:
                if lang not in self.db.glosslangs:
                    self.glosslangs.rm(lang)
        if not self.glosslangs:
            self.guessglosslangs()
    def guessglosslangs(self):
        """if there's only one gloss language, use it."""
        if len(self.db.glosslangs) == 1:
            log.info('Only one glosslang!')
            self.glosslangs.lang1(self.db.glosslangs[0])
            """if there are two or more gloss languages, just pick the first
            two, and the user can select something else later (the gloss
            languages are not for CV profile analaysis, but for info after
            checking, when this can be reset."""
        elif len(self.db.glosslangs) > 1:
            self.glosslangs.lang1(self.db.glosslangs[0])
            self.glosslangs.lang2(self.db.glosslangs[1])
        else:
            print("Can't tell how many glosslangs!",len(self.db.glosslangs))
    def guesscvt(self):
        """For now, if cvt isn't set, start with Vowels."""
        self.set('cvt','V')
    def refreshattributechanges(self):
        """I need to think through these; what things must/should change when
        one of these attributes change? Especially when we've changed a few...
        """
        if not hasattr(self,'attrschanged'):
            return
        if hasattr(self.taskchooser,'status'):
            self.taskchooser.status.build()
        t=self.taskchooser.params.cvt()
        if 'cvt' in self.attrschanged:
            self.taskchooser.status.updatechecksbycvt()
            self.taskchooser.status.makecheckok()
            self.attrschanged.remove('cvt')
        if 'ps' in self.attrschanged:
            if t == 'T':
                self.taskchooser.status.updatechecksbycvt()
            self.attrschanged.remove('ps')
        if 'profile' in self.attrschanged:
            if t != 'T':
                self.taskchooser.status.updatechecksbycvt()
            self.attrschanged.remove('profile')
        if 'check' in self.attrschanged:
            self.attrschanged.remove('check')
        if 'interfacelang' in self.attrschanged:
            self.attrschanged.remove('interfacelang')
        if 'glosslangs' in self.attrschanged:
            self.attrschanged.remove('glosslangs')
        if 'secondformfield' in self.attrschanged:
            self.attrschanged.remove('secondformfield')
        soundattrs=['fs',
                    'sample_format',
                    'audio_card_index',
                    'audioout_card_index'
                    ]
        soundattrschanged=set(soundattrs) & set(self.attrschanged)
        for a in soundattrschanged:
            self.storesettingsfile(setting='soundsettings')
            self.attrschanged.remove(a)
            break
        if self.attrschanged != []:
            log.error("Remaining changed attribute! ({})".format(
                                                        self.attrschanged))
    def makeparameters(self):
        self.params=CheckParameters(self.analang) #remove self.profilesbysense?
    def makeslicedict(self):
        if not hasattr(self,'adhocgroups'): #I.e., not loaded from file
            self.adhocgroups={}
        self.slices=SliceDict(self.params,
                                self.adhocgroups,
                                self.profilesbysense
                                ) #self.profilecounts
        if hasattr(self,'sextracted'):
            self.getscounts()
    def maketoneframes(self):
        if not hasattr(self,'toneframes'):
            self.toneframes={}
        self.toneframes=ToneFrames(self.toneframes)
    def makestatus(self):
        if not hasattr(self,'status'):
            self.status={}
        log.info("Making status object with value {}".format(self.status))
        self.status=StatusDict(self.params,
                                self.slices,
                                # self.exs,
                                self.toneframes,
                                self.settingsfile('status'),
                                self.status
                                )
        log.info("Made status object with value {}".format(self.status))
    def set(self,attribute,choice,window=None,refresh=True):
        #Normally, pass the attribute through the button frame,
        #otherwise, don't set window (which would be destroyed)
        #Set refresh=False (or anything but True) to not redo the main window
        #afterwards. Do this to save time if you are setting multiple variables.
        log.info("Setting {} variable with value: {}".format(attribute,choice))
        if window is not None:
            window.destroy()
        if not hasattr(self,attribute) or getattr(self,attribute) != choice: #only set if different
            setattr(self,attribute,choice)
            self.attrschanged.append(attribute)
            """If there's something getting reset that shouldn't be, remove it
            from self.defaultstoclear[attribute]"""
            self.cleardefaults(attribute)
            if attribute in ['analang',  #do the last two cause problems?
                                'interpret','distinguish']:
                self.reloadprofiledata()
            elif refresh == True:
                self.refreshattributechanges()
        else:
            log.debug(_('No change: {} == {}'.format(attribute,choice)))
    def setsecondformfieldN(self,choice,window=None):
        # ps=Noun# t=self.params.cvt()
        self.secondformfield[self.nominalps]=choice
        self.attrschanged.append('secondformfield')
        self.refreshattributechanges()
        window.destroy()
    def setsecondformfieldV(self,choice,window=None):
        # ps=Noun# t=self.params.cvt()
        self.secondformfield[self.verbalps]=choice
        self.attrschanged.append('secondformfield')
        self.refreshattributechanges()
        window.destroy()
    def setprofile(self,choice,window):
        self.slices.profile(choice)
        self.attrschanged.append('profile')
        self.refreshattributechanges()
        window.destroy()
    def setcvt(self,choice,window=None):
        self.params.cvt(choice)
        self.attrschanged.append('cvt')
        self.refreshattributechanges()
        if isinstance(self.taskchooser.task,Transcribe):
            text=_("You just changed what set of contrasts you're working on,"
                    "while working on transcription; I trust you know what you "
                    "are doing!")
            ErrorNotice(text)
        elif isinstance(self.taskchooser.task,Sort):
            newtaskclass=getattr(sys.modules[__name__],'Sort'+choice)
            self.status.makecheckok() #this is intentionally broad: *any* check
            self.taskchooser.maketask(newtaskclass)
        if window:
            window.destroy()
    def setanalang(self,choice,window):
        self.params.analang(choice)
        self.attrschanged.append('analang')
        self.refreshattributechanges()
        window.destroy()
        self.reloadprofiledata()
    def setgroup(self,choice,window):
        # log.debug("group: {}".format(choice))
        self.status.group(choice)
        # log.debug("group: {}".format(choice))
        window.destroy()
        # log.debug("group: {}".format(choice))
    def setgroup_comparison(self,choice,window):
        if hasattr(self,'group_comparison'):
            log.debug("group_comparison: {}".format(self.group_comparison))
        self.set('group_comparison',choice,window,refresh=False)
        log.debug("group_comparison: {}".format(self.group_comparison))
    def setcheck(self,choice,window=None):
        self.params.check(choice)
        self.attrschanged.append('check')
        self.refreshattributechanges()
        if window:
            window.destroy()
    def setbuttoncolumns(self,choice,window=None):
        self.buttoncolumns=self.taskchooser.mainwindowis.buttoncolumns=choice
        if window:
            window.destroy()
    def setmaxprofiles(self,choice,window):
        self.maxprofiles=choice
        window.destroy()
    def setmaxpss(self,choice,window):
        self.maxpss=choice
        window.destroy()
    def setglosslang(self,choice,window):
        self.glosslangs.lang1(choice)
        self.attrschanged.append('glosslangs')
        self.refreshattributechanges()
        window.destroy()
    def setglosslang2(self,choice,window):
        if choice:
            self.glosslangs.lang2(choice)
        elif len(self.glosslangs)>1:
            self.glosslangs.pop(1) #if lang2 is None
        self.attrschanged.append('glosslangs')
        self.refreshattributechanges()
        window.destroy()
    def setps(self,choice,window):
        self.slices.ps(choice)
        self.attrschanged.append('ps')
        self.refreshattributechanges()
        window.destroy()
    def setexamplespergrouptorecord(self,choice,window):
        self.set('examplespergrouptorecord',choice,window)
    def setsoundhz(self,choice,window):
        self.soundsettings.fs=choice
        window.destroy()
    def setsoundformat(self,choice,window):
        self.soundsettings.sample_format=choice
        window.destroy()
    def setsoundcardindex(self,choice,window):
        self.soundsettings.audio_card_in=choice
        window.destroy()
    def setsoundcardoutindex(self,choice,window):
        self.soundsettings.audio_card_out=choice
        window.destroy()
    def langnames(self):
        """This is for getting the prose name for a language from a code."""
        """It should ultimately use a xyz.ldml file, produced (at least)
        by WeSay, but for now is just a dict."""
        #ET.register_namespace("", 'palaso')
        ns = {'palaso': 'urn://palaso.org/ldmlExtensions/v1'}
        node=None
        self.languagenames={}
        for xyz in [self.analang]+self.db.analangs+self.db.glosslangs:
            # log.info(' '.join('Looking for language name for',xyz))
            """This provides an ldml node"""
            #log.info(' '.join(tree.nodes.find(f"special/palaso:languageName", namespaces=ns)))
            #nsurl=tree.nodes.find(f"ldml/special/@xmlns:palaso")
            """This doesn't seem to be working; I should fix it, but there
            doesn't seem to be reason to generalize it for now."""
            # tree=ET.parse(self.languagepaths[xyz])
            # tree.nodes=tree.getroot()
            # node=tree.nodes.find(f"special/palaso:languageName", namespaces=ns)
            if node is not None:
                self.languagenames[xyz]=node.get('value')
                log.info(' '.join('found',self.languagenames[xyz]))
            elif xyz == 'fr':
                self.languagenames[xyz]=_("French")
            elif xyz == 'en':
                self.languagenames[xyz]=_("English")
            elif xyz == 'es':
                self.languagenames[xyz]=_("Spanish")
            elif xyz == 'pt':
                self.languagenames[xyz]=_("Portuguese")
            elif xyz in ['id','ind']:
                self.languagenames[xyz]=_("Bahasa Indonesian")
            elif xyz in ['ha','hau']:
                self.languagenames[xyz]=_("Hausa")
            elif xyz == 'swc':
                self.languagenames[xyz]=_("Congo Swahili")
            elif xyz == 'swh':
                self.languagenames[xyz]=_("Swahili")
            elif xyz == 'gnd':
                self.languagenames[xyz]=_("Zulgo")
            elif xyz == 'fub':
                self.languagenames[xyz]=_("Fulfulde")
            elif xyz == 'bfj':
                self.languagenames[xyz]=_("Chufie’")
            else:
                self.languagenames[xyz]=_("Language with code "
                                                        "[{}]").format(xyz)
            if not hasattr(self,'adnlangnames') or self.adnlangnames is None:
                self.adnlangnames={}
            if xyz in self.adnlangnames and self.adnlangnames[xyz] is not None:
                self.languagenames[xyz]=self.adnlangnames[xyz]
    def makeeverythingok(self):
        try:
            self.status.makecvtok()
            self.slices.makepsok()
            self.slices.makeprofileok()
            self.status.makecheckok() #this is intentionally broad: *any* check
        except AttributeError as e:
            log.info(_("Maybe status/slices aren't set up yet."))
        # self.status.makegroupok(wsorted=True)
    def setrefreshdelay(self):
        """This sets the main window refresh delay, in miliseconds"""
        if (hasattr(self.taskchooser.mainwindowis,'runwindow') and
                self.taskchooser.mainwindowis.runwindow.winfo_exists()):
            self.refreshdelay=10000 #ten seconds if working in another window
        else:
            self.refreshdelay=1000 #one second if not working in another window
    def ifcollectionlc(self):
        self.notifyuserofextrasegments() #self.analang set by now
        self.polygraphcheck()
        self.checkinterpretations() #checks/sets values for self.distinguish
        self.slists() #lift>check segment dicts: s[lang][segmenttype]
        self.setupCVrxs() # self.rx (needs s)
        self.checkforprofileanalysis()
        """The line above may need to go after this block"""
        self.loadsettingsfile(setting='status')
        self.loadsettingsfile(setting='adhocgroups')
        self.loadsettingsfile(setting='toneframes')
        """Make these objects here only"""
        self.makeslicedict() #needs params
        self.maketoneframes()
        self.makestatus() #needs params, slices, data, toneframes, exs
        self.makeeverythingok()
        self.settingsobjects() #needs params, glosslangs, slices
        self.moveattrstoobjects()
    def __init__(self,taskchooser,liftfileobject):
        self.taskchooser=taskchooser
        self.liftfilename=liftfileobject.name
        self.db=liftfileobject.db
        self.getdirectories() #incl settingsfilecheck and repocheck
        self.setinvalidcharacters()
        self.settingsfilecheck()
        self.settingsinit() #init, clear, fields
        self.loadsettingsfile()
        self.loadsettingsfile(setting='profiledata')
        """I think I need this before setting up regexs"""
        if hasattr(self.taskchooser,'analang'): #i.e., new file
            self.analang=self.taskchooser.analang #I need to keep this alive until objects are done
        else:
            self.guessanalang() #needed for regexs
        if not self.analang:
            log.error("No analysis language; exiting.")
            return
        self.langnames()
        self.guessaudiolang()
        self.loadsettingsfile() # overwrites guess above, stored on runcheck
        self.makeglosslangs()
        self.checkglosslangs() #if stated aren't in db, guess
        self.makeparameters() #depends on nothing but self.analang
        if not self.buttoncolumns:
            self.setbuttoncolumns(1)
        """The following might be OK here, but need to be OK later, too."""
        # """The following should only be done after word collection"""
        # if self.taskchooser.donew['collectionlc']:
        #     self.ifcollectionlc()
        self.attrschanged=[]
class TaskDressing(object):
    """This Class covers elements that belong to (or should be available to)
    all tasks, e.g., menus and button appearance."""
    def taskicon(self):
        return program['theme'].photo['icon'] #default
    def tasktitle(self):
        return _("Unnamed {} Task ({})".format(program['name'],
                                                type(self).__name__))
    def _taskchooserbutton(self):
        if len(self.taskchooser.makeoptions())<2:
            return
        if isinstance(self,TaskChooser) and not self.showreports:
            if self.datacollection:
                text=_("Analyze")
            else:
                text=_("Collect Data")
        else:
            text=_("Tasks")
        if hasattr(self,'chooserbutton'):
            self.chooserbutton.destroy()
        self.chooserbutton=ui.Button(self.outsideframe,text=text,
                                    font='small',
                                    cmd=self.taskchooser.gettask,
                                    row=0,column=2,
                                    sticky='ne')
    def mainlabelrelief(self,relief=None,refresh=False,event=None):
        #set None to make this a label instead of button:
        log.log(3,"setting button relief to {}, with refresh={}".format(relief,
                                                                    refresh))
        self.mainrelief=relief # None "raised" "groove" "sunken" "ridge" "flat"
    def _showbuttons(self,event=None):
        self.mainlabelrelief(relief='flat',refresh=True)
        self.setcontext()
    def _hidebuttons(self,event=None):
        self.mainlabelrelief(relief=None,refresh=True)
        self.setcontext()
    def _removemenus(self,event=None):
        if hasattr(self,'menubar'):
            self.menubar.destroy()
            self.menu=False
            self.setcontext()
    def _setmenus(self,event=None):
        # check=self.check
        self.menubar=Menus(self)
        self.config(menu=self.menubar)
        self.menu=True
        self.setcontext()
        self.unbind_all('<Enter>')
    def correlatemenus(self):
        log.info("Menus: {}; {} (chooser)".format(self.menu,self.taskchooser.menu))
        if hasattr(self,'task'):
            log.info("Menus: {}; {} (task)".format(self.menu,self.task.menu))
        if self.menu != self.taskchooser.menu: #for tasks
            if self.menu:
                self._removemenus()
            else:
                self._setmenus()
        elif hasattr(self,'task') and self.menu != self.task.menu: #for chooser
            if self.menu:
                self._removemenus()
            else:
                self._setmenus()
    def setfontsdefault(self):
        self.theme.setfonts()
        self.fontthemesmall=False
        if hasattr(self,'context'): #don't do this before ContextMenu is there
            self.setcontext()
            self.tableiteration+=1
    def setfontssmaller(self):
        self.theme.setfonts(fonttheme='smaller')
        self.fontthemesmall=True
        self.setcontext()
        self.tableiteration+=1
    def hidegroupnames(self):
        self.settings.set('hidegroupnames', True, refresh=True)
        self.setcontext()
    def showgroupnames(self):
        self.settings.set('hidegroupnames', False, refresh=True)
        self.setcontext()
    def setcontext(self,context=None):
        self.context.menuinit() #This is a ContextMenu() method
        if not hasattr(self,'menu') or not self.menu:
            self.context.menuitem(_("Show Menus"),self._setmenus)
        else:
            self.context.menuitem(_("Hide Menus"),self._removemenus)
        if hasattr(self,'mainrelief') and not self.mainrelief:
            self.context.menuitem(_("Show Buttons"),self._showbuttons)
        else:
            self.context.menuitem(_("Hide Buttons"),self._hidebuttons)
        if hasattr(self,'fontthemesmall') and not self.fontthemesmall:
            self.context.menuitem(_("Smaller Fonts"),self.setfontssmaller)
        else:
            self.context.menuitem(_("Larger Fonts"),self.setfontsdefault)
        if hasattr(self,'hidegroupnames') and self.hidegroupnames:
            self.context.menuitem(_("Show group names"),self.showgroupnames)
        else:
            self.context.menuitem(_("Hide group names"),self.hidegroupnames)
    def maketitle(self):
        title=_("{} Dictionary and Orthography Checker: {}").format(
                                            program['name'],self.tasktitle())
        if program['theme'].name != 'greygreen':
            log.info("Using theme '{}'.".format(program['theme'].name))
            title+=_(' ('+program['theme'].name+')')
        self.title(title)
        t=ui.Label(self.frame, font='title',
                text=self.tasktitle(),
                row=0, column=0, columnspan=2)
        t.bind("<Button-1>",self.taskchooser.gettask)
    def fullscreen(self):
        w, h = self.parent.winfo_screenwidth(), self.parent.winfo_screenheight()
        self.parent.geometry("%dx%d+0+0" % (w, h))
    def quarterscreen(self):
        w, h = self.parent.winfo_screenwidth(), self.parent.winfo_screenheight()
        w=w/2
        h=h/2
        self.parent.geometry("%dx%d+0+0" % (w, h))
    def helpnewinterface(self):
        title=(_("{} Dictionary and Orthography Checker"
                "".format(program['name'])))
        window=ui.Window(self, title=title)
        text=_("{0} has a new interface, starting mid January 2022. You "
                "should still be able to do everything you did before, though "
                "you will probably get to each function a bit differently "
                "—hopefully more intuitively."
                "\nTasks are organized into Data Collection and Analysis, "
                "and you can switch between them with the button in the upper "
                "right of the main {0} window."
                "\nEither window allows you to run reports."
                "").format(program['name'])
        url='https://github.com/kent-rasmussen/azt/blob/main/TASKS.md'
        webtext=_("For more information on {} tasks, please check out the "
                "documentation at {} ").format(program['name'],url)
        ui.Label(window.frame, image=self.frame.theme.photo['icon'],
                text=title, font='title',compound="bottom",
                row=0,column=0,sticky='we'
                )
        l=ui.Label(window.frame, text=text, padx=50,
                wraplength=int(self.winfo_screenwidth()/2),
                row=1,column=0,pady=(50,0),sticky='we'
                )
        webl=ui.Label(window.frame, text=webtext, padx=50,
                wraplength=int(self.winfo_screenwidth()/2),
                row=2,column=0,sticky='we'
                )
        webl.bind("<Button-1>", lambda e: openweburl(url))
    def helpabout(self):
        title=(_("{name} Dictionary and Orthography Checker"
                "".format(name=program['name'])))
        window=ui.Window(self, title=title)
        ui.Label(window.frame,
                text=_("version: {}").format(program['version']),
                anchor='c',padx=50,
                row=1,column=0,sticky='we'
                        )
        text=_("{name} is a computer program that accelerates community"
                "-based language development by facilitating the sorting of a "
                "beginning dictionary by vowels, consonants and tone.\n"
                "It does this by presenting users with sets of words from a "
                "LIFT dictionary database, one part of speech and syllable "
                "profile at a time. These words are sorted into groups based "
                "on consonants, vowels, and tone. \nTone frames are "
                "customizable and stored in the database for each word, "
                "allowing for a number of approaches to collecting this data. "
                "A tone report aids the drafting of underlying categories by "
                "grouping words based on sorting across tone frames. \n{name} then "
                "allows the user to record a word in each of the frames where "
                "it has been sorted, storing the recorded audio file in a "
                "directory, with links to each file in the dictionary database."
                " Recordings can be made up to 192khz/32float, according to "
                "your recording equipment's capacity.").format(
                                                    name=program['name'])
        webtext=_("For help with this tool, please check out the documentation "
                "at {url} ").format(url=program['url'])
        mailtext=_("or write me at {}.").format(program['Email'])
        ui.Label(window.frame, text=title,
                font='title',anchor='c',padx=50,
                row=0,column=0,sticky='we')
        f=ui.ScrollingFrame(window.frame,
                            row=2,column=0,sticky='we')
        ui.Label(f.content, image=self.frame.theme.photo['small'],
                text='',
                row=0,column=0,sticky='we'
                )
        l=ui.Label(f.content, text=text, padx=50,
                wraplength=int(self.winfo_screenwidth()/2),
                row=1,column=0,pady=(50,0),sticky='we'
                )
        webl=ui.Label(f.content, text=webtext, padx=50,#pady=50,
                wraplength=int(self.winfo_screenwidth()/2),
                row=2,column=0,sticky='we'
                )
        maill=ui.Label(f.content, text=mailtext, padx=50,#pady=50,
                wraplength=int(self.winfo_screenwidth()/2),
                row=3,column=0,sticky='we'
                )
        webl.bind("<Button-1>", lambda e: openweburl(program['url']))
        murl='mailto:{}?subject= A→Z+T question'.format(program['Email'])
        maill.bind("<Button-1>", lambda e: openweburl(murl))
    def inherittaskattrs(self):
        for attr in ['file',
                    'db',
                    'datadict','exs',
                    'settings',
                    # 'menu',
                    'mainrelief','fontthemesmall',
                    'buttoncolumns',
                    'hidegroupnames'
                    # 'glosslangs',
                    # 'analang',
                    # 'audiolang',
                    # 'profilesbysense'
                    ]:
            if hasattr(self.parent,attr):
                setattr(self,attr,getattr(self.parent,attr))
        # Make these directly available:
        for attr in ['params','slices','status','toneframes','glosslangs',
                    'buttoncolumns',
                    'soundsettings'
                    ]:
            if hasattr(self.settings,attr):
                setattr(self,attr,getattr(self.settings,attr))
            else:
                log.info("Didn't find {} in {}".format(attr,self.settings))
    def makestatusframe(self,dict=None):
        if hasattr(self,'slices'):
            dictnow={
                'iflang':self.settings.interfacelangwrapper(),
                'analang':self.params.analang(),
                'glang1':self.glosslangs.lang1(),
                'glang2':self.glosslangs.lang2(),
                'cvt':self.params.cvt(),
                'check':self.params.check(),
                'ps':self.slices.ps(),
                'profile':self.slices.profile(),
                'group':self.status.group(),
                'secondformfield':str(self.settings.secondformfield),
                'tableiteration':self.tableiteration,
                'maxprofiles':self.settings.maxprofiles,
                'maxpss':self.settings.maxpss
                }
        else:
            dictnow={
                    'iflang':self.settings.interfacelangwrapper(),
                    'analang':self.params.analang(),
                    'glang1':self.glosslangs.lang1(),
                    'glang2':self.glosslangs.lang2(),
                    'secondformfield':str(self.settings.secondformfield),
                    'maxprofiles':self.settings.maxprofiles,
                    'maxpss':self.settings.maxpss
                    }
        """Call this just once. If nothing changed, wait; if changes, run,
        then run again."""
        if dict == dictnow:
            self.settings.setrefreshdelay()
            self.parent.after(self.settings.refreshdelay,
                                self.makestatusframe,
                                dictnow)
            return
        log.info("Dict changes; checking attributes and updating the UI. ({})"
                                                            "".format(dictnow))
        if self.taskchooser.donew['collectionlc']:
            self.settings.makeeverythingok()
        #This will probably need to be reworked
        if self.exitFlag.istrue():
            return
        if hasattr(self.frame,'status') and self.frame.status.winfo_exists():
            self.frame.status.destroy()
        self.frame.status=StatusFrame(self.frame, self.taskchooser, self,
                                        relief=self.mainrelief,
                                        row=1, column=0, sticky='nw')
        self.frame.update_idletasks()
        self.settings.storesettingsfile()
        self.makestatusframe(dictnow)
    def setSdistinctions(self):
        def notice(changed):
            def confirm():
                ok.value=True
                w.destroy()
            ti=_("Important Notice!")
            w=ui.Window(self.frame,title=ti)
            til=ui.Label(w.frame,text=ti,font='title')
            til.grid(row=0,column=0)
            t=_("You are changing segment interpretation "
            "settings in a way that could cause you problems: ")
            d=[x for x in changed.keys()
                                            if changed[x][1] is False]
            if len(d) >0:
                t+=_("\n=> You are no longer distinguishing {}.").format(
                                    unlist([x.replace('wd','#') for x in d]))
            i=[y for y in changed.keys() if changed[y][1] is not False]
            if len(i) >0:
                t+=_("\n=> Your interpretation of {} changed.").format(
                                                            unlist(i))
            t+=_("\nHere is the full info, in form setting: (from, to): {}."
                    "").format(changed)
            t+=_("\n\nAnywhere you have sorted a group based on your "
            "old interpretation settings, you should sort/verify "
            "that data again, as there is a possiblity that "
            "you have mixed unrelated groups.").format(changed)
            ui.Label(w.frame,text=t,wraplength=int(
                        self.frame.winfo_screenwidth()/2)).grid(row=1,column=0)
            for ps in pss:
                i=[x for x in self.profilesbysense[ps].keys()
                                    if set(d).intersection(set(x))]
                p=_("Profiles to check: {}").format(i)
                log.info(p)
                ui.Label(w.frame,text=p).grid(row=2,column=0)
            ok=Object()
            ok.value=False
            b=ui.Button(w.frame,text=_("OK, go ahead"), command=confirm)
            b.grid(row=1,column=1)
            w.wait_window(w)
            return ok.value
        def submitform():
            def undo(changed):
                for s in changed:
                    if s in self.settings.distinguish:
                        if self.settings.distinguish[s]==changed[s][1]:
                            self.settings.distinguish[s]=changed[s][0] #(oldvar,newvar):
                        else:
                            log.error("Changed to value ({}) doesn't match "
                            "current setting for ‘{}’: {}".format(changed[s][1],
                                                        s,self.distinguish[s]))
                    elif s in self.settings.interpret:
                        if self.settings.interpret[s]==changed[s][1]:
                            self.settings.interpret[s]=changed[s][0] #(oldvar,newvar):
                        else:
                            log.error("Changed to value ({}) doesn't match "
                            "current setting for ‘{}’: {}".format(changed[s][1],
                                                        s,self.interpret[s]))
            r=True #only false if changes made, and user exits notice
            changed={}
            for typ in ['distinguish', 'interpret']:
                for s in getattr(self,typ):
                    if s in options.vars and s in getattr(self,typ):
                        newvar=options.vars[s].get()
                        oldvar=getattr(self,typ)[s]
                        if oldvar != newvar:
                            if typ == 'distinguish': #i.e., boolean
                                if oldvar and not newvar: #True becomes False
                                    changed[s]=(oldvar,newvar)
                            else: #i.e., CC v CG v C, etc.
                                if (len(oldvar)>len(newvar) or # becomes shorter
                                    len(set(['V','G','N'] #one of these is there
                                    ).intersection(set(oldvar))) >0):
                                    changed[s]=(oldvar,newvar)
                            getattr(self,typ)[s]=newvar
            log.debug('self.distinguish: {}'.format(self.settings.distinguish))
            log.debug('self.interpret: {}'.format(self.settings.interpret))
            if changed:
                log.info('There was a change; we need to redo the analysis now.')
                log.info('The following changed (from,to): {}'.format(changed))
                self.storesettingsfile()
                r=notice(changed)
                if r:
                    self.runwindow.destroy()
                    self.reloadprofiledata()
                else:
                    undo(changed)
            else:
                self.runwindow.destroy()
        def buttonframeframe(self):
            s=options.s
            f=options.frames[s]=ui.Frame(self.runwindow.scroll.content)
            f.grid(row=options.get('r'),
                        column=options.get('c'),
                        sticky='ew', padx=options.padx, pady=options.pady)
            bffl=ui.Label(f,text=options.text,justify=ui.LEFT,
                                                                anchor='c')
            bffl.grid(row=1,column=options.column,
                            sticky='ew',
                            padx=options.padx,
                            pady=options.pady)
            # for opt in self.runwindow.options['opts']:
            #     bffrb=CheckButton(self.runwindow.frames[ss],var=var[ss])#, #RadioButtonFrame
            #                             # opts=self.runwindow.options['opts'])
            #     bffrb.grid(row=1,column=1)
            for opt in options.opts:
                bffrb=ui.RadioButtonFrame(f,
                                        var=options.vars[s],
                                        opts=options.opts)
                bffrb.grid(row=1,column=1)
            options.next('r') #self.runwindow.options['row']+=1
        self.getrunwindow()
        self.settings.checkinterpretations()
        analang=self.params.analang()
        options=Options(r=0,padx=50,pady=10,c=0,vars={},frames={})
        for s in self.settings.distinguish: #Should be already set.
            options.vars[s] = ui.BooleanVar()
            options.vars[s].set(self.settings.distinguish[s])
        for s in self.settings.interpret: #This should already be set, even by default
            options.vars[s] = ui.StringVar()
            options.vars[s].set(self.settings.interpret[s])
        """Page title and instructions"""
        self.runwindow.title(_("Set Parameters for Segment Interpretation"))
        mwframe=self.runwindow.frame
        title=_("Interpret {} Segments"
                ).format(self.settings.languagenames[analang])
        titl=ui.Label(mwframe,text=title,font='title',
                justify=ui.LEFT,anchor='c')
        titl.grid(row=options.get('r'), column=options.get('c'), #self.runwindow.options['column'],
                    sticky='ew', padx=options.padx, pady=10)
        options.next('r')
        text=_("Here you can view and set parameters that change how {} "
        "interprets {} segments \n(consonant and vowel glyphs/characters)"
                ).format(program['name'],self.settings.languagenames[analang])
        instr=ui.Label(mwframe,text=text,justify=ui.LEFT,anchor='c')
        instr.grid(row=options.get('r'), column=options.get('c'),
                    sticky='ew', padx=options.padx, pady=options.pady)
        """The rest of the page"""
        self.runwindow.scroll=ui.ScrollingFrame(mwframe)
        self.runwindow.scroll.grid(row=2,column=0)
        log.debug('self.distinguish: {}'.format(self.settings.distinguish))
        log.debug('self.interpret: {}'.format(self.settings.interpret))
        """I considered offering these to the user conditionally, but I don't
        see a subset of them that would only be relevant when another is
        selected. For instance, a user may NOT want to distinguish all Nasals,
        yet distinguish word final nasals. Or CG sequences, but not other G's
        --or distinguish G, but leave as CG (≠C). So I think these are all
        independent boolean selections."""
        options.s='ʔ'
        options.text=_('Do you want to distinguish '
                        'initial and medial glottal stops (ʔ) \nfrom '
                        'other (simple/single) consonants?')
        options.opts=[(True,'ʔ≠C'),(False,'ʔ=C')]
        buttonframeframe(self)
        options.s='ʔwd'
        options.text=_('Do you want to distinguish Word '
                        'Final glottal stops (ʔ#) \nfrom other '
                        'word final consonants?')
        options.opts=[(True,'ʔ#≠C#'),(False,'ʔ#=C#')]
        buttonframeframe(self)
        options.s='N'
        options.text=_('Do you want to distinguish '
                        'initial and medial Nasals (N) \nfrom '
                        'other (simple/single) consonants?')
        options.opts=[(True,'N≠C'),(False,'N=C')]
        buttonframeframe(self)
        options.s='Nwd'
        options.text=_('Do you want to distinguish Word '
                        'Final Nasals (N#) \nfrom other word '
                        'final consonants?')
        options.opts=[(True,'N#≠C#'),(False,'N#=C#')]
        buttonframeframe(self)
        options.s='D'
        if analang in self.db.s and 'D' in self.db.s[analang]:
            depressors=self.db.s[analang]['D']
        else:
            depressors=_("<none so far>")
        options.text=_('Do you want to distinguish '
                        'initial and medial likely depressor consonants (D={})'
                        '\nfrom '
                        'other (simple/single) consonants?'
                        "").format(depressors)
        options.opts=[(True,'D≠C'),(False,'D=C')]
        buttonframeframe(self)
        options.s='Dwd'
        options.text=_('Do you want to distinguish Word '
                        'Final likely depressor consonants (D={})'
                        '\nfrom '
                        'other (simple/single) consonants?'
                        "").format(depressors)
        options.opts=[(True,'D#≠C#'),(False,'D#=C#')]
        buttonframeframe(self)
        options.s='G'
        options.text=_('Do you want to distinguish '
                        'initial and medial Glides (G) \nfrom '
                        'other (simple/single) consonants?')
        options.opts=[(True,'G≠C'),(False,'G=C')]
        buttonframeframe(self)
        options.s='Gwd'
        options.text=_('Do you want to distinguish Word '
                        'Final Glides (G) \nfrom '
                        'other (simple/single) consonants?')
        options.opts=[(True,'G#≠C#'),(False,'G#=C#')]
        buttonframeframe(self)
        options.s='S'
        options.text=_('Do you want to distinguish '
                        'initial and medial Non-Nasal/Glide Sonorants (S) '
                    '\nfrom other (simple/single) consonants?')
        options.opts=[(True,'S≠C'),(False,'S=C')]
        buttonframeframe(self)
        options.s='Swd'
        options.text=_('Do you want to distinguish Word '
                        'Final Non-Nasal/Glide Sonorants (S) '
                    '\nfrom other (simple/single) consonants?')
        options.opts=[(True,'S#≠C#'),(False,'S#=C#')]
        buttonframeframe(self)
        options.s='NC'
        options.text=_('How do you want to interpret '
                                        '\nNasal-Consonant (NC) sequences?')
        options.opts=[('NC','NC=NC (≠C, ≠CC)'),
                        ('C','NC=C (≠NC, ≠CC)'),
                        ('CC','NC=CC (≠NC, ≠C)')
                        ]
        buttonframeframe(self)
        options.s='CG'
        options.text=_('How do you want to interpret '
                                        '\nConsonant-Glide (CG) sequences?')
        options.opts=[('CG','CG=CG (≠C, ≠CC)'),
                        ('C','CG=C (≠CG, ≠CC)'),
                        ('CC','CG=CC (≠CG, ≠C)')]
        buttonframeframe(self)
        options.s='VN'
        options.text=_('How do you want to interpret '
                                        '\nVowel-Nasal (VN) sequences?')
        options.opts=[('VN','VN=VN (≠Ṽ)'), ('Ṽ','VN=Ṽ (≠VN)')]
        buttonframeframe(self)
        """Submit button, etc"""
        self.runwindow.frame2d=ui.Frame(self.runwindow.scroll.content)
        self.runwindow.frame2d.grid(row=options.get('r'),
                    column=options.get('c'),
                    sticky='ew', padx=options.padx, pady=options.pady)
        sub_btn=ui.Button(self.runwindow.frame2d,text = 'Use these settings',
                  command = submitform)
        sub_btn.grid(row=0,column=1,sticky='nw',pady=options.pady)
        nbtext=_("If you make changes, this button==> \nwill "
                "restart the program to reanalyze your data, \nwhich will "
                "take some time.")
        sub_nb=ui.Label(self.runwindow.frame2d,text = nbtext, anchor='e')
        sub_nb.grid(row=0,column=0,sticky='e',
                    pady=options.pady)
        self.runwindow.waitdone()
    def getinterfacelang(self,event=None):
        log.info("Asking for interface language...")
        window=ui.Window(self.frame, title=_('Select Interface Language'))
        ui.Label(window.frame, text=_('What language do you want this program '
                                'to address you in?')
                ).grid(column=0, row=0)
        buttonFrame1=ui.ButtonFrame(window.frame,
                                optionlist=self.taskchooser.interfacelangs,
                                command=self.settings.interfacelangwrapper,
                                window=window,
                                column=0, row=1
                                )
    def getanalangname(self,event=None):
        log.info("this sets the language name")
        def submit(event=None):
            self.settings.languagenames[self.analang]=name.get()
            if (not hasattr(self.taskchooser,'adnlangnames') or
                    not self.taskchooser.adnlangnames):
                self.taskchooser.adnlangnames={}
            if "Language with code [" not in name.get():
                self.settings.adnlangnames[self.analang]=name.get()
                # if self.analang in self.adnlangnames:
            self.settings.storesettingsfile()
            window.destroy()
        window=ui.Window(self.frame,title=_('Enter Analysis Language Name'))
        curname=self.settings.languagenames[self.analang]
        defaultname=_("Language with code [{}]").format(self.analang)
        t=_("How do you want to display the name of {}").format(curname)
        if curname != defaultname:
            t+=_(", with ISO 639-3 code [{}]").format(self.analang)
        t+='?' # _("Language with code [{}]").format(xyz)
        ui.Label(window.frame,text=t,row=0,column=0,sticky='e',columnspan=2)
        name = ui.EntryField(window.frame)
        name.grid(row=1,column=0,sticky='e')
        name.focus_set()
        name.bind('<Return>',submit)
        ui.Button(window.frame,text='OK',cmd=submit,row=1,column=1,sticky='w')
    def getanalang(self,event=None):
        if len(self.db.analangs) <2: #The user probably wants to change display.
            self.getanalangname()
            return
        log.info("this sets the language")
        # fn=inspect.currentframe().f_code.co_name
        window=ui.Window(self.frame,title=_('Select Analysis Language'))
        if self.db.analangs is None :
            ui.Label(window.frame,
                          text='Error: please set Lift file first! ('
                          +str(self.db.filename)+')'
                          ).grid(column=0, row=0)
        else:
            ui.Label(window.frame,
                          text=_('What language do you want to analyze?')
                          ).grid(column=0, row=1)
            langs=list()
            for lang in self.db.analangs:
                langs.append({'code':lang,
                                'name':self.settings.languagenames[lang]})
                # print(lang, self.taskchooser.languagenames[lang])
            buttonFrame1=ui.ButtonFrame(window.frame,
                                     optionlist=langs,
                                     command=self.settings.setanalang,
                                     window=window,
                                     column=0, row=4
                                     )
    def getglosslang(self,event=None):
        window=ui.Window(self.frame,title=_('Select Gloss Language'))
        text=_('What Language do you want to use for glosses?')
        ui.Label(window.frame, text=text, column=0, row=1)
        langs=list()
        for lang in self.db.glosslangs:
            langs.append({'code':lang,
                            'name':self.settings.languagenames[lang]})
        buttonFrame1=ui.ButtonFrame(window.frame,
                                 optionlist=langs,
                                 command=self.settings.setglosslang,
                                 window=window,
                                 column=0, row=4
                                 )
    def getglosslang2(self,event=None):
        window=ui.Window(self.frame,title='Select Second Gloss Language')
        text=_('What other language do you want to use for glosses?')
        ui.Label(window.frame, text=text, column=0, row=1)
        langs=list()
        for lang in self.db.glosslangs:
            if lang == self.settings.glosslangs[0]:
                continue
            langs.append({'code':lang,
                            'name':self.settings.languagenames[lang]})
        langs.append({'code':None, 'name':'just use '
                +self.settings.languagenames[self.settings.glosslangs.lang1()]})
        buttonFrame1=ui.ButtonFrame(window.frame,
                                    optionlist=langs,
                                    command=self.settings.setglosslang2,
                                    window=window,
                                    column=0, row=4
                                    )
    def getcvt(self,event=None):
        log.debug(_("Asking for check cvt/type"))
        window=ui.Window(self.frame,title=_('Select Check Type'))
        cvts=[]
        x=0
        tdict=self.params.cvtdict()
        for cvt in tdict:
            cvts.append({})
            cvts[x]['name']=tdict[cvt]['pl']
            cvts[x]['code']=cvt
            x+=1
        ui.Label(window.frame, text=_('What part of the sound system do you '
                                    'want to work with?')
            ).grid(column=0, row=0)
        buttonFrame1=ui.ButtonFrame(window.frame,
                                    optionlist=cvts,
                                    command=self.settings.setcvt,
                                    window=window,
                                    column=0, row=1
                                    )
        return window
    def getps(self,event=None):
        log.info("Asking for ps...")
        # self.refreshattributechanges()
        window=ui.Window(self.frame, title=_('Select Grammatical Category'))
        ui.Label(window.frame, text=_('What grammatical category do you '
                                    'want to work with (Part of speech)?')
                ).grid(column=0, row=0)
        if hasattr(self,'additionalps') and self.settings.additionalps is not None:
            pss=self.db.pss+self.settings.additionalps #these should be lists
        else:
            pss=self.db.pss
        buttonFrame1=ui.ScrollingButtonFrame(window.frame,
                                            optionlist=pss,
                                            command=self.settings.setps,
                                            window=window,
                                            column=0, row=1
                                            )
    def getprofile(self,event=None,**kwargs):
        log.info("Asking for profile...")
        # self.refreshattributechanges()
        window=ui.Window(self.frame,title=_('Select Syllable Profile'))
        ps=self.slices.ps()
        if self.settings.profilesbysense[ps] is None: #likely never happen...
            ui.Label(window.frame,
            text=_('Error: please set Grammatical category with profiles '
                    'first!')+' (not '+str(ps)+')'
            ).grid(column=0, row=0)
        else:
            profilecounts=self.slices.valid()
            profilecountsAdHoc=self.slices.adhoccounts()
            profiles=self.status.profiles(**kwargs)
            if profilecountsAdHoc:
                adhocdict=self.slices.adhoc()
                profilecounts.update(profilecountsAdHoc)
                if ps in adhocdict:
                    profiles+=self.slices.adhoc()[ps].keys()
            profiles=dict.fromkeys(profiles)
            if not profiles:
                log.error("No profiles of {} type found!".format(kwargs))
            log.info("count types: {}, {}".format(type(profilecounts),
                                                    type(profilecountsAdHoc)))
            ui.Label(window.frame, text=_('What ({}) syllable profile do you '
                                    'want to work with?'.format(ps))
                                    ).grid(column=0, row=0)
            optionslist = [(x,profilecounts[(x,ps)]) for x in profiles]
            """What does this extra frame do?"""
            window.scroll=ui.Frame(window.frame)
            window.scroll.grid(column=0, row=1)
            buttonFrame1=ui.ScrollingButtonFrame(window.scroll,
                                    optionlist=optionslist,
                                    command=self.settings.setprofile,
                                    window=window,
                                    column=0, row=0
                                    )
            window.wait_window(window)
    def getsecondformfieldN(self,event=None):
        ps=self.settings.nominalps
        opts=self.settings.plopts
        othername=self.settings.imperativename
        setcmd=self.settings.setsecondformfieldN
        self.getsecondformfield(ps,opts,othername,setcmd)
    def getsecondformfieldV(self,event=None):
        ps=self.settings.verbalps
        opts=self.settings.impopts
        othername=self.settings.pluralname
        setcmd=self.settings.setsecondformfieldV
        self.getsecondformfield(ps,opts,othername,setcmd)
    def getsecondformfield(self,ps,opts,othername,setcmd,other=False):
        def getother():
            window.destroy()
            self.getsecondformfield(ps=ps,
                                    opts=opts,
                                    othername=othername,
                                    setcmd=setcmd,
                                    other=True)
        log.info("Asking for ‘{}’ second form field...".format(ps))
        optionslist = self.db.fields
        if not optionslist:
            ErrorNotice(_("I don't see any appropriate fields; I'll give you "
            "some commonly used ones to choose from."), wait=True)
            other=True
        title=_('Select Second Form Field for {}').format(ps)
        window=ui.Window(self.frame,title=title)
        if other:
            text=_("What database field name do you want to use for second "
                    "forms for {} words?".format(ps))
            optionslist=opts
        else:
            text=_("What is the database field for second forms for ‘{}’ words?"
            "".format(ps))
            try:
                optionslist.remove(othername)
            except ValueError:
                log.info("Imperative field ‘{}’ doesn't seem to be there: {}"
                        "".format(othername,optionslist))
        ui.Label(window.frame, text=text, column=0, row=0)
        """What does this extra frame do?"""
        window.scroll=ui.Frame(window.frame)
        window.scroll.grid(column=0, row=2)
        buttonFrame1=ui.ScrollingButtonFrame(window.scroll,
                optionlist=optionslist,
                command=setcmd,
                window=window,
                column=0, row=0
                )
        if not other:
            otherbutton=ui.Button(buttonFrame1.content,
                            text=_("None of these; make a new field"),
                            column=0, row=1,
                            cmd=getother
                            )
        window.wait_window(window)
    def getbuttoncolumns(self,event=None):
        log.info("Asking for number of button columns...")
        window=ui.Window(self.frame,title=_('Select Button Columns'))
        ui.Label(window.frame, text=_('How many columns do you want to use for '
                                        'the sort buttons?')
                                        ).grid(column=0, row=0)
        optionslist = list(range(1,4))
        buttonFrame1=ui.ButtonFrame(window.frame,
                                optionlist=optionslist,
                                command=self.settings.setbuttoncolumns,
                                window=window,
                                column=0, row=1
                                )
        window.wait_window(window)
    def getmaxpss(self,event=None):
        title=_('Select Maximum Number of Lexical Categories')
        window=ui.Window(self.frame, title=title)
        text=_('How many lexical categories to report (2 = Noun and Verb) ?')
        ui.Label(window.frame, text=text, column=0, row=0)
        r=[x for x in range(1,10)]
        buttonFrame1=ui.ScrollingButtonFrame(window.frame,
                                optionlist=r,
                                command=self.settings.setmaxpss,
                                window=window,
                                column=0, row=1
                                )
        buttonFrame1.wait_window(window)
    def getmaxprofiles(self,event=None):
        title=_('Select Maximum Number of Syllable Profiles')
        window=ui.Window(self.frame, title=title)
        text=_('How many syllable profiles to report?')
        ui.Label(window.frame, text=text, column=0, row=0)
        r=[x for x in range(1,10)]
        buttonFrame1=ui.ScrollingButtonFrame(window.frame,
                                optionlist=r,
                                command=self.settings.setmaxprofiles,
                                window=window,
                                column=0, row=1
                                )
        buttonFrame1.wait_window(window)
    def getcheck(self,guess=False,event=None,**kwargs):
        log.info("this sets the check")
        # fn=inspect.currentframe().f_code.co_name
        log.info("Getting the check name...")
        checks=self.status.checks(**kwargs)
        window=ui.Window(self.frame,title='Select Check')
        if not checks:
            if self.params.cvt() == 'T':
                btext=_("Define a New Tone Frame")
                text=_("You don't seem to have any tone frames set up.\n"
                "Click '{}' below to define a tone frame. \nPlease "
                "pay attention to the instructions, and if \nthere's anything "
                "you don't understand, or if you're not \nsure what a tone "
                "frame is, please ask for help. \nWhen you are done making "
                "frames, click ‘Exit’ to continue.".format(btext))
                cmd=self.addframe
            else:
                btext=_("Return to A→Z+T, to fix settings")
                text=_("I can't find any checks for type {}, ps {}, profile {}."
                        " Probably that means there is a problem with your "
                        " settings, or with your syllable profile analysis"
                        "".format(cvt,ps,profile))
                cmd=window.destroy
            ui.Label(window.frame, text=text).grid(column=0, row=0, ipady=25)
            b=ui.Button(window.frame, text=btext,
                    cmd=cmd,
                    anchor='c')
            b.grid(column=0, row=1,sticky='')
            """I need to make this quit the whole program, immediately."""
            b.wait_window(window)
        elif guess is True:
            self.status.makecheckok(tosort=tosort,wsorted=wsorted)
        else:
            log.info("Checks: {}".format(checks))
            if self.params.cvt() == 'T':
                checklist=checks
            else:
                checklist=[(c,self.params.cvcheckname(c)) for c in checks]
            text=_('What check do you want to do?')
            ui.Label(window.frame, text=text).grid(column=0, row=0)
            buttonFrame1=ui.ScrollingButtonFrame(window.frame,
                                    optionlist=checklist,
                                    command=self.settings.setcheck,
                                    window=window,
                                    column=0, row=4
                                    )
            count=len(buttonFrame1.bf.winfo_children())
            if self.taskchooser is self:
                task=self.mainwindowis
            else:
                task=self
            newb=ui.Button(buttonFrame1.bf,
                            text=_("New Frame"),
                            cmd=lambda w=window: task.addframe(window=w),
                            row=count+1)
            buttonFrame1.wait_window(window)
        """Make sure we got a value"""
        if self.params.check() not in checks:
            return 1
    def getframedtonegroup(self,window,event=None,guess=False,**kwargs):
        """Window is called in getgroup"""
        log.info("getframedtonegroup kwargs: {}".format(kwargs))
        kwargs=grouptype(**kwargs)
        cvt=kwargs.get('cvt',self.params.cvt())
        ps=kwargs.get('ps',self.slices.ps())
        profile=kwargs.get('profile',self.slices.profile())
        check=kwargs.get('check',self.params.check())
        if (None in [cvt, ps, profile, check]
                or cvt != 'T'):
            ui.Label(window.frame,
                          text=_("You need to set "
                          "\nCheck type (as Tone, currently {}) "
                          "\nGrammatical category (currently {})"
                          "\nSyllable Profile (currently {}), and "
                          "\nTone Frame (currently {})"
                          "\nBefore this function will do anything!"
                          "").format(self.params.cvtdict()[cvt]['sg'], ps,
                          profile, check)).grid(column=0, row=0)
            return 1
        else:
            g=self.status.groups(**kwargs) #wsorted=True above
            if not g:
                ui.Label(window.frame,
                          text=_("It looks like you don't have {}-{} lexemes "
                          "grouped in the ‘{}’ frame yet \n({})."
                          "").format(ps,profile,check,kwargs)
                          ).grid(column=0, row=0)
            elif guess == True or (len(g) == 1 and not kwargs['comparison']):
                self.settings.setgroup(g[0],window) #don't ask, just set
            else:
                ui.Label(window.frame,
                          text=_("What {}-{} tone group in the ‘{}’ frame do "
                          "you want to work with?").format(ps,profile,
                          check)).grid(column=0, row=0)
                window.scroll=ui.Frame(window.frame)
                window.scroll.grid(column=0, row=1)
                if kwargs['comparison']:
                    g2=g[:]
                    g2.remove(self.status.group())
                    if not g2:
                        window.destroy()
                        ErrorNotice(text=_("There don't seem to be any groups "
                                    "to compare with!"))
                        return
                    if len(g2) == 1:
                        self.settings.setgroup_comparison(g2[0],window)
                        return
                    buttonFrame1=ui.ScrollingButtonFrame(window.scroll,
                                    optionlist=g2,
                                    command=self.settings.setgroup_comparison,
                                    window=window,
                                    column=0, row=4
                                    )
                else:
                    buttonFrame1=ui.ScrollingButtonFrame(window.scroll,
                                                optionlist=g,
                                                command=self.settings.setgroup,
                                                window=window,
                                                column=0, row=4
                                                )
    def getV(self,window,event=None, **kwargs):
        # fn=inspect.currentframe().f_code.co_name
        """Window is called in getgroup"""
        ps=kwargs.get('ps',self.slices.ps())
        if ps is None:
            ui.Label(window.frame,
                          text='Error: please set Grammatical category first! ('
                          +str(ps)+')'
                          ).grid(column=0, row=0)
        else:
            g=self.status.groups(**kwargs)
            ui.Label(window.frame,
                          text='What Vowel do you want to work with?'
                          ).grid(column=0, row=0)
            window.scroll=ui.ScrollingFrame(window.frame)
            window.scroll.grid(column=0, row=1)
            buttonFrame1=ui.ScrollingButtonFrame(window.scroll,
                                     optionlist=g,
                                     command=self.setsubcheck,
                                     window=window,
                                     column=0, row=4
                                     )
    def getC(self,window,event=None, **kwargs):
        # fn=inspect.currentframe().f_code.co_name
        """Window is called in getgroup"""
        ps=kwargs.get('ps',self.slices.ps())
        if ps is None:
            text=_('Error: please set Grammatical category first! ')+'('
            +str(ps)+')'
            ui.Label(window.frame,
                          text=text
                          ).grid(column=0, row=0)
        else:
            # ui.Label(window.frame,
            #               ).grid(column=0, row=0)
            g=self.status.groups(**kwargs)
            ui.Label(window.frame,
                          text='What consonant do you want to work with?'
                          ).grid(column=0, row=0,sticky='nw')
            window.scroll=Frame(window.frame)
            window.scroll.grid(column=0, row=1)
            buttonFrame1=ui.ScrollingButtonFrame(window.scroll,
                                    optionlist=g,
                                    command=self.setsubcheck,
                                    window=window,
                                    column=0, row=0
                                    )
    def getgroup(self,guess=False,event=None,**kwargs):
        log.info("this sets the group")
        kwargs=grouptype(**kwargs) #if any should be True, set in wrappers above
        log.info("getgroup kwargs: {}".format(kwargs))
        self.settings.refreshattributechanges()
        cvt=kwargs.get('cvt',self.params.cvt())
        if cvt == "V":
            w=ui.Window(self.frame,title=_('Select Vowel'))
            self.getV(window=w,**kwargs)
            w.wait_window(window=w)
        elif cvt == "C":
            w=ui.Window(self.frame,title=_('Select Consonant'))
            self.getC(w,**kwargs)
            self.frame.wait_window(window=w)
        elif cvt == "CV":
            CV=''
            for cvt in ['C','V']:
                self.getgroup(**kwargs)
                CV+=group
            group=CV
            cvt = "CV"
        elif cvt == "T":
            w=ui.Window(self.frame,title=_('Select Framed Tone Group'))
            self.getframedtonegroup(window=w,guess=guess,**kwargs)
            # windowT.wait_window(window=windowT) #?!?
        return w #so others can wait for this
    def getgroupwsorted(self,event=None,**kwargs):
        kwargs['wsorted']=True
        kwargs=grouptype(**kwargs)
        return self.getgroup(**kwargs)
    def getgrouptosort(self,event=None,**kwargs):
        kwargs['tosort']=True
        kwargs=grouptype(**kwargs)
        return self.getgroup(**kwargs)
    def getgrouptoverify(self,event=None,**kwargs):
        kwargs['toverify']=True
        kwargs=grouptype(**kwargs)
        return self.getgroup(**kwargs)
    def getgrouptorecord(self,event=None,**kwargs):
        kwargs['torecord']=True
        kwargs=grouptype(**kwargs)
        return self.getgroup(**kwargs)
    def getexamplespergrouptorecord(self):
        log.info("this sets the number of examples per group to record")
        self.npossible=[
            {'code':1,'name':"1 - Bare minimum, just one per group"},
            {'code':5,'name':"5 - Some, but not all, of most groups"},
            {'code':100,'name':"100 - All examples in most databases"},
            {'code':1000,'name':"1000 - All examples in VERY large databases"}
                        ]
        title=_('Select Number of Examples per Group to Record')
        window=ui.Window(self.frame, title=title)
        text=_("The {0} tone report splits sorted data into "
                "draft underlying tone melody groups. "
                # ", with distinct values for each of your tone frames. This "
                # "exhaustively finds differences between groups of lexical "
                # "senses, but often "
                # "misses similarities between groups, which might be "
                # "distinguished only because a single word was skipped or sorted "
                # "incorrectly.\n\n"
                "Even before a linguist has been able to evaluate these "
                "groups, it may be helpful to record your sorted data. "
                "{0} can give you a window for each lexicon sense in a tone "
                "group, with a record button for each sorted sense-frame "
                "combination. "
                "\n\nThose "
                "windows will be presented to the user from one tone report "
                "group after "
                "another, until all groups have had one page presented. Then "
                "{0} will "
                "repeat this process, until it has done a number of "
                "rounds equal to the number selected below. "
                # "\n\nIf a "
                # "group has fewer examples than this number, that group will be "
                # "skipped once done. "
                "\nPicking a larger number could delay opening "
                "the recording window; picking a smaller number could mean "
                "data not getting recorded. "
                "Up to how many examples do you want to record for each group?"
                "".format(program['name'])
                )
        t=ui.Label(window.frame, text=title, font='title',column=0, row=0)
        l=ui.Label(window.frame, text=text, justify='left',column=0, row=1)
        t.wrap()
        l.wrap()
        buttonFrame1=ui.ButtonFrame(window.frame,
                            optionlist=self.npossible,
                            command=self.settings.setexamplespergrouptorecord,
                            window=window,
                            column=0, row=4
                                )
        buttonFrame1.wait_window(window)
    def getrunwindow(self,nowait=False,msg=None,title=None):
        """Can't test for widget/window if the attribute hasn't been assigned,"
        but the attribute is still there after window has been killed, so we
        need to test for both."""
        if title is None:
            title=(_("Run Window"))
        if self.exitFlag.istrue():
            return
        if hasattr(self,'runwindow') and self.runwindow.winfo_exists():
            log.info("Runwindow already there! Resetting frame...")
            self.runwindow.resetframe() #I think I'll always want this here...
        else:
            self.runwindow=ui.Window(self.frame,title=title)
        self.runwindow.title(title)
        self.runwindow.lift()
        if not nowait:
            self.runwindow.wait(msg=msg)
    """Functions that everyone needs"""
    def verifictioncode(self,**kwargs):
        check=kwargs.get('check',self.params.check())
        group=kwargs.get('group',self.status.group())
        log.info("about to return {}={}".format(check,group))
        return check+'='+group
    def maybewrite(self):
        def schedule_check(t):
            """Schedule `check_if_done()` function after five seconds."""
            self.after(5000, check_if_done, t)
        def check_if_done(t):
            # If the thread has finished, allow another write.
            if not t.is_alive():
                self.taskchooser.writing=False
            else:
                # Otherwise check again later.
                schedule_check(t)
        if self.timetowrite() and not self.taskchooser.writing:
            t = threading.Thread(target=self.db.write)
            self.taskchooser.writing=True
            t.start()
            schedule_check(t)
    def timetowrite(self):
        """only write to file every self.writeeverynwrites times you might."""
        self.taskchooser.writeable+=1 #and tally here each time this is asked
        return not self.taskchooser.writeable%self.settings.writeeverynwrites
    def updateazt(self):
        if 'git' in program:
            gitargs=[str(program['git']), "-C", str(program['aztdir']), "pull"]
            try:
                o=subprocess.check_output(gitargs,shell=False,
                                            stderr=subprocess.STDOUT)
                # o=e.decode(sys.stdout.encoding).strip()
                # log.info("git output: {}".format(o))
            except subprocess.CalledProcessError as e:
                o=e.output
            try:
                t=o.decode(sys.stdout.encoding).strip()
            except:
                t=o
            log.info("git output: {} ({})".format(t,type(t)))
            if (type(t) is str and
                        "Already up to date." not in t and
                        "No route to host" not in t) or (
                type(t) is not str and
                            b"Already up to date." not in t and
                            b"No route to host" not in t):
                t=str(t)+_('\n(Restart {} to use this update)').format(
                                                                program['name'])
            e=ErrorNotice(t,parent=self,title=_("Update (Git) output"))
            e.wait_window(e)
    def __init__(self,parent):
        log.info("Initializing TaskDressing")
        self.parent=parent
        self.menu=False #initialize once
        if isinstance(self,TaskChooser):
            self.taskchooser=self
        else:
            self.taskchooser=self.parent
        """Whenever this runs, it's the main window."""
        self.taskchooser.mainwindowis=self
        self.mainwindow=True
        self.withdraw() #made visible by chooser when complete
        self.maketitle()
        """At some point, I need to think through which attributes are needed,
        and if I can get them all into objects, read/writeable with files."""
        """These are raw attributes from file"""
        """these are objects made by the task chooser"""
        self.inherittaskattrs()
        self.analang=self.params.analang() # Every task gets this here
        # super(TaskDressing, self).__init__(parent)
        for k in ['settings',
                    # 'menu',
                    'mainrelief','fontthemesmall',
                    'hidegroupnames']:
            if not hasattr(self,k):
                if hasattr(parent,k):
                    setattr(self,k,getattr(parent,k))
                else:
                    setattr(self,k,False)
        ui.ContextMenu(self)
        self.tableiteration=0
        self.makestatusframe()
        self._taskchooserbutton()
        self.correlatemenus()
        # back=ui.Button(self.outsideframe,text=_("Tasks"),cmd=self.taskchooser)
        # self.setfontsdefault()
class TaskChooser(TaskDressing,ui.Window):
    """This class stores the hierarchy of tasks to do in A→Z+T, plus the
    minimum and optimum prerequisites for each. Based on these, it presents
    to the user a default (highest in hierarchy without optimum fulfilled)
    task on opening, and allows users to choose others (any with minimum
    prequisites satisfied)."""
    def tasktitle(self):
        if self.showreports:
            return _("Run Reports")
        elif self.datacollection:
            return _("Data Collection Tasks")
        else:
            return _("Analysis Tasks")
    def dobuttonkwargs(self):
        return {'text':_("Reports"),
                'fn':self.choosereports,
                'font':'title',
                'compound':'top', #image bottom, left, right, or top of text
                'image':self.taskchooser.theme.photo['iconReportLogo'],
                'sticky':'ew'
                }
    def choosereports(self):
        self.frame.status.bigbutton.destroy()
        self.showreports=True
        self.gettask()
    def getfile(self):
        # def getit(attr):
        #     if hasattr(self.file,attr):
        #         setattr(self,attr,getattr(self.file,attr))
        file=self.file=FileChooser()
        # I want to access these attributes directly
        for attr in ['s','db']:
            if hasattr(self.file,attr):
                setattr(self,attr,getattr(self.file,attr))
    def makesettings(self):
        self.settings=Settings(self,self.file) #give object, for name and db
    def makedatadict(self):
        self.datadict=FramedDataDict(self) #needs self.toneframes
    def makeexampledict(self):
        self.exs=ExampleDict(self.params,self.slices,self.db,self.datadict)
    def guidtriage(self):
        # import time
        log.info("Doing guid triage... This takes awhile...")
        start_time=time.time()
        self.guids=self.db.guids
        self.guidsinvalid=[] #nothing, for now...
        self.senseids=self.db.senseids
        self.senseidsinvalid=[] #nothing, for now...
        print(time.time() - start_time,"seconds.")
        print(len(self.guidsinvalid),'entries with invalid data found.')
        self.db.guidsinvalid=self.guidsinvalid
        self.guidsvalid=[]
        for guid in self.guids:
            if guid not in self.guidsinvalid:
                self.guidsvalid+=[guid]
        print(len(self.guidsvalid),'entries with valid data remaining.')
        self.guidswanyps=self.db.get('guidwanyps') #any ps value works here.
        print(len(self.guidswanyps),'entries with ps data found.')
        self.guidsvalidwops=[]
        self.guidsvalidwps=[]
        for guid in self.guidsvalid:
            if guid in self.guidswanyps:
                self.guidsvalidwps+=[guid]
            else:
                self.guidsvalidwops+=[guid]
        self.db.guidsvalidwps=self.guidsvalidwps #This is what we'll search
        print(len(self.guidsvalidwops),'entries with valid data but no ps data.')
        print(len(self.guidsvalidwps),'entries with valid data and ps data.')
        print(time.time() - start_time,"seconds.")
        # for var in [self.guids, self.guidswanyps, self.guidsvalidwops, self.guidsvalidwps, self.guidsinvalid, self.guidsvalid]:
        #     print(len(var),str(var))
        # for guid in self.guidswanyps:
        #     if guid not in self.formstosearch[self.analangs[0]][None]:
        #         guids+=[guid]
        # print(len(guids),guids)
        print("Set the above variables in "+str(time.time() - start_time)+" se"
                "conds.")
    def guidtriagebyps(self):
        log.info("Doing guid triage by ps... This also takes awhile?...")
        self.guidsvalidbyps={}
        for ps in self.db.pss:
            self.guidsvalidbyps[ps]=self.db.get('guidbyps',ps=ps)
    def gettask(self,event=None):
        """This function allows the user to select from any of tasks whose
        prerequisites are minimally satisfied."""
        # if self.reports:
        self.frame.status.bigbutton.destroy()
        if not self.showreports:
            self.frame.status.finalbuttons()
        if not self.mainwindow:
            self.correlatemenus() #only if moving to this window
            self.unsetmainwindow() #first, so the program stays alive
        elif not self.showingreports and not self.showreports:
            self.datacollection=not self.datacollection
        if self.showingreports:
            self.showingreports=False
        self.maketitle() #b/c this changes
        if hasattr(self,'task') and self.task.winfo_exists():
            self.task.on_quit() #destroy and set flag
        if hasattr(self,'optionsframe'):
            self.optionsframe.destroy()
        self._taskchooserbutton()
        optionlist=self.makeoptions()
        bpr=3
        # compound='left', #image bottom, left, right, or top of text
        self.optionsframe=ui.Frame(self.frame,column=1, row=1, pady=(25,0))
        optionlist_maxi=len(optionlist)-1
        if optionlist_maxi == 3:
            bpr=2
        columnspan=1
        for n,o in enumerate(optionlist):
            if n is optionlist_maxi:
                # log.info("bpr: {}, n%bpr: {}".format(bpr,n%bpr))
                columnspan=bpr-n%bpr
            b=ui.Button(self.optionsframe,
                        text=o[1],
                        command=lambda t=o[0]:self.maketask(t),
                        column=n%bpr,
                        row=int(n/bpr),
                        compound='top', #left, bottom
                        image=o[2],
                        wraplength=int(program['root'].wraplength*.6/bpr),
                        anchor='n',
                        sticky='nesw',
                        columnspan=columnspan
                        )
            try:
                ui.ToolTip(b, o[0].tooltip(None))
            except AttributeError:
                log.info("Task {} doesn't seem to have a tooltip.".format(o[0]))
        for c in range(bpr):
            self.optionsframe.grid_columnconfigure(c, weight=1, uniform='a')
        self.setmainwindow(self) #deiconify here
        if self.showreports:
            self.showreports=False #just do this once each button click
            self.showingreports=True
    def makedefaulttask(self):
        """This function makes the task after the highest optimally
        satisfied task"""
        if self.taskchooser.doneenough['collectionlc']:
            self.ifcollectionlc()
        """The above is prerequisite to the below, so it is here. It could be
        elsewhere, but that led to numerous repetitions."""
        optionlist=self.makeoptions()
        # task,title,icon
        optionlist=[i for i in optionlist if not issubclass(i[0],Sound)]
        log.info("getting default from option list {}".format(optionlist))
        if program['testing'] and hasattr(self,'testdefault'):
            self.maketask(self.testdefault)
        else:
            self.maketask(optionlist[-1][0]) #last item, the code
    def maketask(self,taskclass): #,filename=None
        self.unsetmainwindow()
        try:
            self.task.waitdone()
            self.task.on_quit() #destroy and set flag
        except AttributeError:
            log.info(_("No task, apparently; not destroying."))
        self.task=taskclass(self) #filename
        if not self.task.exitFlag.istrue():
            self.task.deiconify()
    def unsetmainwindow(self):
        """self.mainwindowis tracks who the mainwindow is for the chooser,
        x.mainwindow tracks if the object is the mainwindow, so it will
        exit the program on closure appropriately. This fn keeps them
        synchronized."""
        if hasattr(self,'mainwindowis'):
            self.mainwindowis.withdraw()
            self.mainwindowis.mainwindow=False #keep only one of these
        else:
            log.info("No mainwindowis found.")
    def setmainwindow(self,window):
        """This is really only useful for the taskChooser; others live or die"""
        self.mainwindowis=window
        self.mainwindowis.mainwindow=True #keep only one of these
        self.mainwindowis.deiconify()
    def setiflang(self):
        self.interfacelangs=file.getinterfacelangs()
        iflang=file.getinterfacelang()
        if iflang is None:
            interfacelang('fr')
        else:
            interfacelang(iflang)
    def makeoptions(self):
        """This function (and probably a few dependent functions, maybe
        another class) provides a list of functions with prerequisites
        that are minimally and/or optimally satisfied."""
        """So far that distinction isn't being made. For instance, we should
        not offer recordingT as default if all examples have sound files, yet
        a user may well want to go back and look at those recordings, and maybe
        rerecord some."""
        #if nothing to do??
        if self.showreports:
            tasks=[
                    ReportCitation,
                    ]
            if self.doneenough['collectionlc']:
                """This currently takes way too much time. Until it gets
                mutithreaded, it will not be an option"""
                tasks.append(ReportCitationBasicV)
                tasks.append(ReportCitationBasicC)
                tasks.append(ReportCitationBasicCV)
                tasks.append(ReportCitationBasic)
            if self.doneenough['sortT']:
                tasks.append(ReportCitationT)
                tasks.append(ReportCitationTlocation)
                tasks.append(ReportCitationBasicT)
        elif self.datacollection:
            tasks=[
                    WordCollectionCitation,
                    # WordCollectionLexeme
                    ]
            if self.doneenough['collectionlc']:
                tasks.append(RecordCitation)
                """Do these next"""
                # tasks.append(SortV)
                # tasks.append(SortC)
                tasks.append(SortT)
                if self.doneenough['sortT']:
                    tasks.append(RecordCitationT)
            if program['testing'] and hasattr(self,'testdefault'):
                tasks.append(self.testdefault)
            # if self.donew['parsedlx']:
            #     tasks.append(SortRoots)
        else: #i.e., analysis tasks
            tasks=[]
            if self.doneenough['sortT']:
                if self.doneenough['recordedT']:
                    tasks.append(Transcribe)
                    if self.doneenough['analysis']:
                        tasks.append(JoinUFgroups)
            if me:
                tasks.append(ReportConsultantCheck)
        # tasks.append(WordCollectionCitation),
        # tasks.append(WordCollectionPlImp),
        # tasks.append(ParseA), # input pl/imp, gives lx and ps
        # tasks.append(ParseB), # user selects pl/imp, gives ls and ps
        # tasks.append(SyllableProfileAnalysisCitation),
        # tasks.append(SortTCitation),
        # tasks.append(SyllableProfileAnalysisLexeme),
        # tasks.append(TranscribeTCitation),
        # tasks.append(RecordTCitation),
        # tasks.append(RecordPlImp),
        # tasks.append(Placeholder),
        # tasks.append(Reports),
        # tasks.append(SortV),
        # tasks.append(SortC),
        # tasks.append(SortTLexeme),
        # tasks.append(TranscribeTLexeme),
        # tasks.append(RecordTLexeme)
        # ]:
        tasktuples=[]
        for task in tasks:
            if hasattr(task,'tasktitle'):
                if hasattr(task,'taskicon'):
                    tasktuples.append((task,task.tasktitle(task),
                                            task.taskicon(task)))
                else:
                    tasktuples.append((task,task.tasktitle(task),None))
            else:
                if hasattr(task,'taskicon'):
                    tasktuples.append((task,str(task),task.taskicon(task)))
                else:
                    tasktuples.append((task,str(task),None))
        log.info("Tasks available ({}): {}".format(len(tasktuples),tasktuples))
        return tasktuples
        # [(Check,"Citation Form Sorting in Tone Frames"),
        #         (WordCollection,"Placeholder for future checks"),
        #         (Placeholder,"Placeholder for future checks")
        #         ]bum
    def convertlxtolc(self,window):
        window.destroy()
        backup=self.file.name+"_backupBeforeLx2LcConversion"
        self.db.write(backup)
        for e in self.db.nodes.findall('entry'):
            lxs=e.findall('lexical-unit')
            for lx in lxs:
                log.info("Looking at entry w/guid: {}".format(e.get("guid")))
                #,lx.find('text').get('lang')))
                # log.info("Found {}".format([i for i in lx
                # if i.findall('text')
                # and [j for j in i.findall('text') if j.text]
                # # and i.find('text').text
                #         ]))
                for lxf in [i for i in lx
                            if i.findall('text') and
                            [j for j in i.findall('text') if j.text]
                        ]: #only forms with text info
                    lxfl=lxf.get('lang')
                    lxft=lxf.find('text')
                    log.info("Moving {} from lang {}".format(lxft.text,lxfl))
                    # lc=e.findall('citation')
                    """This finds or creates, by lang:"""
                    lc=self.db.citationformnodeofentry(e,lxfl)
                    log.info("Moving to citation winfo {} from lang {}".format(lc.text,lxfl))
                    if not lc.text: #don't overwrite info
                        lc.text=lxft.text
                        lxft.text='' #clear only on move
        # self.db.write(self.file.name+str(now()))
        self.db.write()
        conversionlogfile=logsetup.writelzma() # log.filename no longer needed
        #             tmpdb.nodes.findall('entry/citation')):
        #     for f in n.findall('form'):
        #         n.remove(f)
        ErrorNotice(_("The conversion is done now, so {0} will quit. You may "
                    "want to inspect your current file ({1}) and the backup "
                    "({2}) to confirm this did what you wanted, before "
                    "opening {0} again. In case there are any issues, the "
                    "log file is also saved in {3}").format(program['name'],
                                                self.file.name,
                                                backup,
                                                conversionlogfile),
                    title=_("Conversion Done!"),
                    wait=True)
        self.restart()
    def asktoconvertlxtolc(self):
        title=_("Convert lexeme field data to citation form fields?")
        url="https://github.com/kent-rasmussen/azt/blob/main/CITATIONFORMS.md"
        w=ui.Window(self,title=title,exit=False)
        lexemesdone=list(self.db.nentrieswlexemedata.values())#[self.settings.analang]
        citationsdone=list(self.db.nentrieswcitationdata.values())#[self.settings.analang]
        nbtext1=_("You have {} entries with lexeme data, and only {} with "
                "citation data.").format(lexemesdone,citationsdone)
        instructions=_("Typically, dictionary work starts by collecting "
                        "citation forms, and later moves to analyzing those "
                        "forms into lexemes (meaningful, but not necessarily "
                        "pronounceable, word parts). Sometimes, people store "
                        "those citation forms in lexeme fields, though this "
                        "is typically in error. {} can help you analyze your "
                        "citation forms into lexeme forms, but they first need "
                        "to be moved to the correct fields in your database."
                        "".format(program['name']))
        Question=_("Do you want {} to move data from your lexeme fields to "
                    "citation fields, for each entry with no citation field "
                    "data?".format(program['name']))
        infot=_("See {} for more information.".format(url))
        oktext=_("Move lexeme field data to citation fields")
        noktext=_("No thanks; I'll manage this myself")
        nbtext=_("N.B.: This is a fairly radical change to your database, "
                "so it would be wise to back up your data.")
        noktttext=_("You will need to do this yourself, either in FLEx, or "
                    "with expert help.")
        lt=ui.Label(w.frame, text=title, font='title',
                    row=0, column=0, columnspan=2)
        nb=ui.Label(w.frame, text=nbtext1, font='default',
                    row=1, column=0, columnspan=2)
        # li=ui.Label(w.frame, text=instructions, font='instructions',
        #             row=2, column=0, columnspan=2)
        lq=ui.Label(w.frame, text=Question, font='read',
                    row=3, column=0, columnspan=2)
        bok=ui.Button(w.frame, text=oktext,
                        font='instructions',
                        cmd=lambda w=w:self.convertlxtolc(w),
                        row=4, column=0)
        bok.tt=ui.ToolTip(bok,instructions)
        bnok=ui.Button(w.frame, text=noktext,
                        font='instructions',
                        cmd=w.destroy, row=4, column=1)
        bnok.tt=ui.ToolTip(bnok, text=noktttext)
        lnb=ui.Label(w.frame, text=nbtext, row=5, column=0, columnspan=2)
        info=ui.Label(w.frame, text=infot, font='default',
                    row=7, column=0, columnspan=2)
        info.tt=ui.ToolTip(info, text=_("go to {}").format(url))
        info.bind("<Button-1>", lambda e: openweburl(url))
        for l in [lt,nb,lq,lnb]:
            l.wrap()
        return w
    def getcawlmissing(self):
        cawls=self.db.get('cawlfield/form/text').get('text')
        # log.info("CAWL ({}): {}".format(len(cawls),cawls))
        self.cawlmissing=[]
        for i in range(1700):
            if "{:04}".format(i+1) not in cawls:
                self.cawlmissing.append(i+1)
        log.info("CAWL missing ({}): {}".format(len(self.cawlmissing),
                                                    self.cawlmissing))
    def whatsdone(self):
        """I should probably have a roundtable with people to discuss these
        numbers, to see that we agree the decision points are rational."""
        self.donew={} # last is default to show user
        self.doneenough={} # which options the user *can* see
        for taskreq in ['collectionlc','parsedlx','collectionplimp',
                    'tonereport',
                    # 'torecord',
                    # 'torecordT',
                    'recorded',
                    'recordedT',
                    'sortT',
                    'sort',
                    'sortlc',
                    'torecord',
                    'torecordT',
                    'analysis'
                    ]:
            self.donew[taskreq]=False
            self.doneenough[taskreq]=False
        nentries=self.db.nguids
        lexemesdone=self.db.nentrieswlexemedata
        citationsdone=self.db.nentrieswcitationdata
        log.info("lexemesdone by lang: {}".format(lexemesdone))
        log.info("citationsdone by lang: {}".format(citationsdone))
        #There should never be more lexemes than citation forms.
        for l in lexemesdone:
            if l not in citationsdone or citationsdone[l] < lexemesdone[l]:
                w=self.asktoconvertlxtolc()
                w.wait_window(w) # wait for this answer before moving on
                break #just ask this once
        self.getcawlmissing()
        sorts=self.db.nfields
        log.info("nfields by lang: {}".format(sorts))
        sortsrecorded=self.db.nfieldswsoundfiles
        log.info("nfieldswsoundfiles by lang: {}".format(sortsrecorded))
        sortsnotrecorded={}
        enough=50
        for f in sorts:
            if f not in sortsrecorded:
                sortsrecorded[f]={}
            sortsnotrecorded[f]={}
            for l in sorts[f]:
                """I don't think I can faithfully distinguish between
                sorting on lc v other fields here, at least not yet"""
                if f == 'sense/example':
                    #sorting is never done; mark when the top slices are done?
                    if sorts[f][l] >= enough: #what is a reasonable number here?
                        self.doneenough['sortT']=True
                else:
                    if sorts[f][l] >= enough: #what is a reasonable number here?
                        self.doneenough['sort']=True
                #This is a bit of a hack, but no analang nor audiolang yet.
                maybeals=[i for i in self.db.audiolangs if l in i]
                if maybeals:
                    al=maybeals[0]
                    log.info("Using audiolang {} for analang {}".format(al,l))
                    if al not in sortsrecorded[f]:
                        sortsrecorded[f][al]=0
                    sortsnotrecorded[f][l]=sorts[f][l]-sortsrecorded[f][al]
                    if f == 'sense/example':
                        if not sortsnotrecorded[f][l]:
                            self.donew['recordedT']=True
                        if sortsrecorded[f][al] >= enough:
                            self.doneenough['recordedT']=True
                        # Needed? Any time sorting is done, show recording
                        # if not sortsrecorded[f][al]:
                        #     self.donew['torecordT']=True
                        if sortsnotrecorded[f][l] < enough:
                            self.doneenough['torecordT']=True
                    else:
                        if not sortsnotrecorded[f][l]:
                            self.donew['recorded']=True
                        if sortsrecorded[f][al] >= enough:
                            self.doneenough['recorded']=True
                        #see above
                        if sortsnotrecorded[f][l] < enough:
                            self.doneenough['torecord']=True
                else:
                    log.info("Couldn't find plausible audiolang (among {}) "
                            "for analang {}".format(self.db.audiolangs,l))
        log.info("nfieldswosoundfiles by lang: {}".format(sortsnotrecorded))
        for lang in self.file.db.nentrieswlexemedata:
            remaining=self.file.db.nentrieswcitationdata[lang
                                        ]-self.file.db.nentrieswlexemedata[lang]
            if not remaining:
                self.donew['parsedlx']=True
            if remaining < 100:
                self.doneenough['parsedlx']=True
                break
        for lang in citationsdone:
            if nentries-citationsdone[lang] < 50 and not len(self.cawlmissing):
                self.donew['collectionlc']=True
            if me or citationsdone[lang] > 200: #was 705
                self.doneenough['collectionlc']=True#I need to think through this
        for f in self.db.sensefields:
            if 'verification' in f:
                self.doneenough['analysis']=True
                break
        log.info("Analysis of what you're done with: {}".format(self.donew))
        log.info("You're done enough with: {}".format(self.doneenough))
    def restart(self,filename=None):
        if hasattr(self,'warning') and self.warning.winfo_exists():
            self.warning.destroy()
        # pyargs=[program['python'],file.getfile(__file__)]
        # subprocess.run(pyargs)
        sysrestart()
        # self.parent.makecheck(filename)
    def changedatabase(self):
        log.debug("Removing database name, so user will be asked again.")
        self.file.askwhichlift(file.getfilenames())
        # text=_("{} will now exit; restart to work with the new database."
        #         "".format(program['name']))
        # ErrorNotice(text,title=_("Change Database"),wait=True)
        # program['root'].destroy()
        # subprocess.call?
        # __name__
        # main()
        self.restart()
        # self.restart(self.filename)
    def ifcollectionlc(self):
        log.info("Considering finishing setup for post-collection projects")
        if not self.ifcollectionlcsettingsdone: #only do this once
            try:
                log.info("Finishing setup for post-collection projects")
                self.settings.ifcollectionlc()
                self.inherittaskattrs()
                self.makedatadict()
                self.makeexampledict() #needed for makestatus, needs params,slices,data
                self.maxprofiles=5 # how many profiles to check before moving on to another ps
                self.maxpss=2 #don't automatically give more than two grammatical categories
                self.ifcollectionlcsettingsdone=True
            except Exception as e:
                log.error(_("There seems to be a problem loading your "
                "database with post-word collection settings; I will remove "
                "it as default so you can open another"))
                file.writefilename()
                raise
    def __init__(self,parent):
        # self.testdefault=Parse
        self.start_time=time.time() #this enables boot time evaluation
        self.writing=False
        self.datacollection=True # everyone starts here?
        self.showreports=False
        self.showingreports=False
        self.ifcollectionlcsettingsdone=False
        self.setiflang() #before Splash
        ui.Window.__init__(self,parent)
        self.setmainwindow(self)
        splash = Splash(self)
        self.getfile()
        # self.guidtriage() #sets: self.guidswanyps self.guidswops self.guidsinvalid self.guidsvalid
        # self.guidtriagebyps() #sets self.guidsvalidbyps (dictionary keyed on ps)
        """Can whatsdone be joined with makedefaulttask? they appear together
        elsewhere."""
        self.whatsdone()
        if hasattr(self.file,'analang'): #i.e., new file
            self.analang=self.file.analang #I need to keep this alive until objects are done
        self.makesettings()
        TaskDressing.__init__(self,parent)
        if not self.settings.writeeverynwrites: #0/None are not sensible values
            self.settings.writeeverynwrites=1
            self.settings.storesettingsfile()
        self.writeable=0 #start the count
        self.makedefaulttask() #normal default
        # self.gettask() # let the user pick
        """Do I want this? Rather give errors..."""
        splash.destroy()
class Segments(object):
    """docstring for Segments."""
    def getlisttodo(self,all=False):
        """Whichever field is being asked for (textnodefn), this fn returns
        which are left to do."""
        all=self.db.get('entry',
                        showurl=True).get()
        # done=self.db.get('entry',path=['lexeme'],analang=analang,
        #                 showurl=True).get()
        # for i in all[:10]:
        #     log.info("textnodecontents: {}".format(self.textnodefn(i,analang).text))
        done=[i for i in all
                    if self.textnodefn(i,self.analang).text
                    # self.db.get('lexeme/form/text', node=i, analang=analang,
                    # showurl=True
                    #                 ).get('text') != ''
                    ]
        todo=[x for x in all if x not in done]
        log.info("To do: ({}) {}".format(len(todo),todo))
        return todo
    def getwords(self):
        self.entries=self.getlisttodo()
        self.nentries=len(self.entries)
        self.index=0
        r=self.getword()
        if r == 'noglosses':
            self.nextword()
    def buildregex(self,**kwargs):
        """include profile (of those available for ps and check),
        and subcheck (e.g., a: CaC\2)."""
        """Provides self.regexCV and self.regex"""
        cvt=kwargs.get('cvt',self.params.cvt())
        # ps=kwargs.get('ps',self.slices.ps())
        profile=kwargs.get('profile',self.slices.profile())
        check=kwargs.get('check',self.params.check())
        group=kwargs.get('group',self.status.group())
        maxcount=rx.countxiny(cvt, profile)
        # re.subn(cvt, cvt, profile)[1]
        if profile is None:
            print("It doesn't look like you've picked a syllable profile yet.")
            return
        """Don't need this; only doing count=1 at a time. Let's start with
        the easier ones, with the first occurrance changed."""
        # log.info("self.regexCV: {}".format(self.regexCV))
        self.regexCV=str(profile) #Let's set this before changing it.
        # log.info("self.regexCV: {}".format(self.regexCV))
        """One pass for all regexes, S3, then S2, then S1, as needed."""
        cvts=['V','C']
        # log.info("maxcount: {}".format(maxcount))
        # log.info("check: {}".format(check))
        # log.info("group: {}".format(group))
        # log.info("self.groupcomparison: {}".format(self.groupcomparison))
        if 'x' in check:
            if self.groupcomparison in self.status.groups(cvt='C'):
                # self.s[self.analang]['V']:
                cvts=['C','V'] #comparison needs to be done first
        compared=False #don't reset this for each cvt
        for t in cvts:
            if t not in cvt:
                continue
            S=str(t) #should this ever be cvt? Do I ever want CV1xCV2,CV1=CV2?
            regexS='[^'+S+']*'+S #This will be a problem if S=NC or CG...
            # log.info("regexS: {}".format(regexS))
            for occurrence in reversed(range(maxcount)):
                occurrence+=1
                # log.info("S+str(occurrence): {}".format(S+str(occurrence)))
                # if re.search(S+str(occurrence),check) is not None:
                if S+str(occurrence) in check:
                    """Get the (n=occurrence) S, regardless of intervening
                    non S..."""
                    # log.info("regexS: {}".format(regexS))
                    regS='^('+regexS*(occurrence-1)+'[^'+S+']*)('+S+')'
                    # log.info("regS: {}".format(regS))
                    # log.info("regexS: {}".format(regexS))
                    if 'x' in check:
                        if compared == False: #occurrence == 2:
                            replS='\\1'+self.groupcomparison
                            compared=True
                        else: #if occurrence == 1:
                            replS='\\1'+group
                    else:
                        # log.info("Not comparing: {}".format(check))
                        replS='\\1'+group
                    # log.info("regS: {}".format(regS))
                    # log.info("replS: {}".format(replS))
                    # log.info("self.regexCV: {}".format(self.regexCV))
                    self.regexCV=rx.sub(regS,replS,self.regexCV, count=1)
                    # log.info("self.regexCV: {}".format(self.regexCV))
        # log.info("self.regexCV: {}".format(self.regexCV))
        """Final step: convert the CVx code to regex, and store in self."""
        self.regex=rx.fromCV(self,lang=self.analang,
                            word=True, compile=True)
    def senseidformsbyregex(self,regex,**kwargs):
        """This function takes in a compiled regex,
        and outputs a list/dictionary of senseid/{senseid:form} form."""
        ps=kwargs.get('ps',self.slices.ps())
        output=[] #This is just a list of senseids now: (Do we need the dict?)
        for form in [i for i in self.settings.formstosearch[ps] if i]:
            log.info("Looking for form {}".format(form))
            if regex.search(form):
                output+=self.settings.formstosearch[ps][form]
        return output
    def __init__(self, parent):
        if parent.params.cvt() == 'T':
            parent.settings.setcvt('V')
class WordCollection(Segments):
    """This task collects words, from the SIL CAWL, or one by one."""
    def addmorpheme(self):
        def makewindow():
            def submitform(event=None):
                self.runwindow.form[lang]=form[lang].get()
                self.runwindow.frame2.destroy()
            def skipform(event=None):
                self.runwindow.frame2.destroy() #Just move on.
            self.runwindow.frame2=ui.Frame(self.runwindow.frame,
                                            row=1,column=0,
                                            sticky='ew',
                                            padx=25,pady=25)
            if lang == self.analang:
                text=_("What is the form of the new "
                        "morpheme in {} \n(consonants and vowels only)?".format(
                                    self.settings.languagenames[lang]))
                ok=_('Use this form')
            else:
                text=_("What does ‘{}’ mean in {}?".format(
                                            self.runwindow.form[self.analang],
                                            self.settings.languagenames[lang]))
                ok=_('Use this {} gloss for ‘{}’'.format(
                                            self.settings.languagenames[lang],
                                            self.runwindow.form[self.analang]))
                self.runwindow.glosslangs.append(lang)
            getform=ui.Label(self.runwindow.frame2,text=text,
                                                font='read')
            getform.grid(row=0,column=0,padx=padx,pady=pady)
            form[lang]=ui.StringVar()
            eff=ui.Frame(self.runwindow.frame2) #field rendering is better this way
            eff.grid(row=1,column=0)
            formfield = ui.EntryField(eff, render=True, textvariable=form[lang])
            formfield.grid(row=1,column=0)
            formfield.focus_set()
            formfield.bind('<Return>',submitform)
            formfield.rendered.grid(row=2,column=0,sticky='new')
            sub_btn=ui.Button(self.runwindow.frame2,text = ok,
                      command = submitform,anchor ='c')
            sub_btn.grid(row=2,column=0,sticky='')
            if lang != self.analang:
                sub_btnNo=ui.Button(self.runwindow.frame2,
                    text = _('Skip {} gloss').format(
                                        self.settings.languagenames[lang]),
                    command = skipform)
                sub_btnNo.grid(row=1,column=1,sticky='')
            self.runwindow.waitdone()
            sub_btn.wait_window(self.runwindow.frame2) #then move to next step
        self.getrunwindow()
        self.runwindow.form={}
        self.runwindow.glosslangs=list()
        form={}
        padx=50
        pady=10
        self.runwindow.title(_("Add Morpheme to Dictionary"))
        title=_("Add {} morpheme to the dictionary").format(
                            self.settings.languagenames[self.analang])
        ui.Label(self.runwindow.frame,text=title,font='title',
                justify=ui.LEFT,anchor='c'
                ).grid(row=0,column=0,sticky='ew',padx=padx,pady=pady)
        # Run the above script (makewindow) for each language, analang first.
        # The user has a chance to enter a gloss for any gloss language
        # already in the datbase, and to skip any as needed/desired.
        for lang in [self.analang]+self.db.glosslangs:
            if lang in self.runwindow.form:
                continue #Someday: how to do monolingual form/gloss here
            if not self.runwindow.exitFlag.istrue():
                x=makewindow()
                if x:
                    return
        """get the new senseid back from this function, which generates it"""
        if not self.runwindow.exitFlag.istrue(): #don't do this if exited
            senseid=self.db.addentry(ps='',analang=self.analang,
                            glosslangs=self.runwindow.glosslangs,
                            form=self.runwindow.form)
            # Update profile information in the running instance, and in the file.
            self.runwindow.destroy()
            """The following are useless without ps information, so they will
            have to come later."""
            # if self.taskchooser.donew['collectionlc']:
            #     self.settings.getprofileofsense(senseid)
            #     self.slices.updateslices()
            #     self.settings.getscounts()
            #     self.settings.storesettingsfile(setting='profiledata') #since we changed this.
    def addCAWLentries(self):
        text=_("Adding CAWL entries to fill out, in established database.")
        self.wait(msg=text)
        log.info(text)
        self.file.loadCAWL()
        self.cawldb=self.file.cawldb
        added=[]
        modded=[]
        for n in self.taskchooser.cawlmissing:
            log.info("Working on SILCAWL line #{:04}.".format(n))
            e=self.cawldb.get('entry', path=['cawlfield'],
                                    cawlvalue="{:04}".format(n),
                                    ).get('node')[0] #certain to be there
            try:
                eps=self.cawldb.get('sense/ps',node=e,showurl=True).get('node')[0]
                epsv=eps.get('value')
            except IndexError:
                log.info("line {} w/o lexical category; leaving.".format(n))
                eps=epsv=None
            if epsv == "Noun":
                log.info("Found a noun, using {}".format(self.settings.nominalps))
                eps.set('value',self.settings.nominalps)
            elif epsv == "Verb":
                log.info("Found a verb, using {}".format(self.settings.verbalps))
                eps.set('value',self.settings.verbalps)
            else:
                log.error("Not sure what to do with ps {} ({})".format(epsv,eps))
            entry=None #in case no selected glosslangs in CAWL
            for lang in self.glosslangs:
                g=e.findall("sense/gloss[@lang='{}']/text".format(lang))
                if not g:
                    continue #don't worry about glosslangs not in CAWL
                else:
                    g=g[0].text
                """any entry with a matching gloss"""
                entry=self.db.get('entry',gloss=g,glosslang=lang,
                                        ).get('node') #maybe []
                if entry:
                    log.info("Found gloss of SILCAWL line #{:04} ({}); "
                            "adding info to that entry.".format(n,g))
                    self.db.fillentryAwB(entry[0],e)
                    modded.append(n)
                    break
            if not entry: #i.e., no match for any self.glosslangs gloss
                tnodes=e.findall('lexical-unit/form/text')
                for tn in tnodes:
                    tn.text=''
                log.info("Gloss of SILCAWL line #{:04} ({}) not found; "
                        "copying over that entry.".format(n,g))
                self.db.nodes.append(e)
                added.append(n)
        if added or modded:
            self.db.write()
            title=_("Entries Added!")
            text=_("Added {} entries from the SILCAWL").format(len(added))
            if len(added)<100:
                text+=": ({})".format(added)
            text+=_("\nModded {} entries with new information from the "
                    "SILCAWL").format(len(modded))
            if len(modded)<100:
                text+=": ({})".format(modded)
            self.taskchooser.whatsdone()
            self.taskchooser.makedefaulttask()
        else:
            title=_("Error trying to add SILCAWL entries")
            text=_("We seem to have not added or modded any entries, which "
                    "shouldn't happen! (missing: {})"
                    "".format(self.taskchooser.cawlmissing))
        self.waitdone()
        log.info(text)
        ErrorNotice(text,title=title)
    def nextword(self,event=None):
        def cont():
            self.taskchooser.whatsdone()
            self.taskchooser.makedefaulttask()
            self.e.on_quit()
        self.storethisword()
        if self.index < len(self.entries)-1:
            self.index+=1
            r=self.getword()
            if r == 'noglosses':
                self.nextword()
        else:
            oktext=_("Continue")
            t=_("Congratulations! \nIt looks like you got to the end of what "
            "was left to collect. "
            "\nYou can navigate through the words you just collected, "
            "\nor press ‘{}’ to go on to the next task.").format(oktext)
            self.e=ErrorNotice(t,title=_("Done!"))
            b=ui.Button(self.e.frame,text=oktext, cmd=cont, row=1, column=1)
    def backword(self):
        self.storethisword()
        if self.index == 0:
            self.index=len(self.entries)-1
        else:
            self.index-=1
        r=self.getword()
        if r == 'noglosses':
            self.backword()
    def storethisword(self):
        try:
            self.lxtextnode.text=self.lxvar.get()
            self.maybewrite() #only if above is successful
        except AttributeError as e:
            log.info("Not storing word: {}".format(e))
    def getword(self):
        try:
            self.wordframe.destroy()
        except Exception as e:
            log.info("Probably nothing (wordframe not made yet): {}".format(e))
        self.wordframe=ui.Frame(self.frame,row=1,column=1,sticky='ew')
        if not self.entries:
            text=_("It looks like you're done filling out the empty "
            "entries in your database! Congratulations! You can still add words "
            "through the button on the left ({})."
            "".format(self.dobuttonkwargs()['text']))
            l=ui.Label(self.wordframe, text=text, row=0, column=0,
                        wraplength=int(program['root'].wraplength*.6))
            l.wrap()
            # nope=_("No, I haven't done the CAWL yet; "
            #         "\nplease add it to my database, "
            #         "\nso I can fill it out.")
            # b=ui.Button(self.wordframe, text=nope, cmd=self.addCAWLentries,
            #             row=1, column=0, sticky='',
            #             wraplength=int(program['root'].wraplength*.6))
            return
        text=_("Type the word in your language that goes with these meanings."
                "\nGive a single word (not a phrase) wherever possible."
                "\nJust type consonants and vowels; don't worry about tone "
                "for now.").format(self.nentries)
        ui.Label(self.wordframe, text=text, row=0, column=0)
        progress="({}/{})".format(self.index+1,self.nentries)
        ui.Label(self.wordframe, text=progress, row=1, column=3, font='small')
        entry=self.entries[self.index]
        glosses={}
        for g in self.glosslangs:
            glosses[g]=', '.join(self.db.get('gloss/text', node=entry,
                                    glosslang=g).get('text'))
        # glossframe=ui.Frame(self.wordframe, row=1, column=0)
        glossesthere=' — '.join([glosses[i] for i in glosses if i])
        if not glossesthere:
            log.info("entry {} doesn't have glosses; not showing."
                    "".format(entry.get('id')))
            return 'noglosses'
        l=ui.Label(self.wordframe, text=glossesthere, font='read',
                row=1, column=0, columnspan=3, sticky='ew')
        l.wrap()
        self.lxtextnode=self.textnodefn(entry,self.analang)
        # log.info("lxtextnode: {}".format(self.lxtextnode))
        self.lxvar=ui.StringVar(value=self.lxtextnode.text)
        # get('entry',path=['lexeme'],analang=self.analang,
        #                 showurl=True).get()
        # lxvar=ui.StringVar()
        lxenter=ui.EntryField(self.wordframe,textvariable=self.lxvar,
                                row=2,column=0,columnspan=3)
        lxenter.focus_set()
        lxenter.bind('<Return>',self.nextword)
        # self.navigationframe=ui.Frame(self.frame, row=2, column=1,
        #                                 columnspan=3, sticky='ew')
        back=ui.Button(self.wordframe,text=_("Back"),cmd=self.backword,
        row=3, column=0, sticky='w',anchor='w',
        )
        # ui.Label(self.navigationframe,text=" ",row=0, column=1, sticky='ew')
        next=ui.Button(self.wordframe,text=_("Next"),cmd=self.nextword,
        row=3, column=2, sticky='e',anchor='e',
        )
        # self.navigationframe.grid_columnconfigure(1,weight=1)
        self.frame.grid_columnconfigure(1,weight=1)
class WordCollectionLexeme(TaskDressing,ui.Window,WordCollection):
    def tasktitle(self):
        return _("Word Collection for Lexeme Forms")
    def __init__(self, parent): #frame, filename=None
        """This should never really be used, though I made it first, so I've
        left it"""
        ui.Window.__init__(self,parent)
        TaskDressing.__init__(self,parent)
        log.info("Initializing {}".format(self.tasktitle()))
        #Status frame is 0,0
        self.textnodefn=self.db.lexemeformnodeofentry
        self.getwords()
class WordCollectionCitation(TaskDressing,ui.Window,WordCollection):
    def taskicon(self):
        return program['theme'].photo['iconWord']
    def tooltip(self):
        return _("This task helps you collect words in citation form.")
    def dobuttonkwargs(self):
        if self.taskchooser.cawlmissing:
            fn=self.addCAWLentries
            text=_("Add remaining CAWL entries")
            tttext=_("This will add entries from the Comparative African "
                    "Wordlist (CAWL) which aren't already in your database "
                    "(you are missing {} CAWL tags). If the appropriate "
                    "glosses are found in your database, CAWL tags will be "
                    "merged with those entries."
                    "\nDepending on the number of entries, this may take "
                    "awhile.").format(len(self.taskchooser.cawlmissing))
        else:
            text=_("Add a Word")
            fn=self.addmorpheme
            tttext=_("This adds any word, but is best used after filling out a "
                    "wordlist, if the word you want to add isn't there "
                    "already.")
        return {'text':text,
                'fn':fn,
                # column=0,
                'font':'title',
                'compound':'bottom', #image bottom, left, right, or top of text
                'image':self.taskchooser.theme.photo['Word'],
                'sticky':'ew',
                'tttext':tttext
                }
    def tasktitle(self):
        return _("Add Words") # for Citation Forms
    def __init__(self, parent): #frame, filename=None
        ui.Window.__init__(self,parent)
        TaskDressing.__init__(self,parent)
        log.info("Initializing {}".format(self.tasktitle()))
        #Status frame is 0,0
        self.textnodefn=self.db.citationformnodeofentry
        self.getwords()
class Parse(TaskDressing,ui.Window,Segments):
    """docstring for Parse."""
    def taskicon(self):
        return program['theme'].photo['iconWord']
    def tooltip(self):
        return _("This task will help you parse your citation forms.")
    def dobuttonkwargs(self):
        fn=self.doparse
        text=_("Parse Citation Forms")
        tttext=_("For now, this just lets you copy citation form info to "
                "The lexeme field.")
        return {'text':text,
                'fn':fn,
                # column=0,
                'font':'title',
                'compound':'bottom', #image bottom, left, right, or top of text
                'image':self.taskchooser.theme.photo['Word'],
                'sticky':'ew',
                'tttext':tttext
                }
    def tasktitle(self):
        return _("Parse Citation Forms")
    def doparse(self):
        window=ui.Window(self,title=self.tasktitle())
        ui.Label(window,text=_("Parsing!"),row=0,column=0)
        todo=self.getlisttodo(all=self.dodone)
        ui.Label(window,text=todo[:50],wraplength=program['root'].wraplength, row=1,column=0)
    def __init__(self, parent): #frame, filename=None
        log.info("Initializing {}".format(self.tasktitle()))
        ui.Window.__init__(self,parent)
        TaskDressing.__init__(self,parent)
        self.textnodefn=self.db.lexemeformnodeofentry
        self.dodone=False
class Placeholder(TaskDressing,ui.Window):
    """Fake check, placeholder for now."""
    def taskicon(self):
        return program['theme'].photo['icon']
    def tooltip(self):
        return _("Tooltip here.")
    def dobuttonkwargs(self):
        fn=self.addCAWLentries
        text=_("Add remaining CAWL entries")
        tttext=_("This will add entries from the Comparative African "
                "Wordlist (CAWL) which aren't already in your database "
                "(you are missing {} CAWL tags). If the appropriate "
                "glosses are found in your database, CAWL tags will be "
                "merged with those entries."
                "\nDepending on the number of entries, this may take "
                "awhile.").format(len(self.taskchooser.cawlmissing))
        return {'text':text,
                'fn':fn,
                # column=0,
                'font':'title',
                'compound':'bottom', #image bottom, left, right, or top of text
                'image':self.taskchooser.theme.photo['icon'],
                'sticky':'ew',
                'tttext':tttext
                }
    def tasktitle(self):
        return _("Placeholder Check2")
    def __init__(self, parent): #frame, filename=None
        ui.Window.__init__(self,parent)
        TaskDressing.__init__(self,parent)
        log.info("Initializing {}".format(self.tasktitle()))
        for r in range(5):
            ui.Label(self.frame,
                    text="This is a check placeholder.",
                    row=r, column=0)
class Tone(object):
    """This keeps stuff used for Tone checks."""
    def makeanalysis(self,**kwargs):
        return Analysis(self.params,
                                self.slices,
                                self.status,
                                self.db,
                                **kwargs
                                )
        """was, now iterable, for multiple reports at a time:"""
        if not hasattr(self,'analysis'):
            self.analysis=Analysis(self.params,
                                    self.slices,
                                    self.status,
                                    self.db,
                                    **kwargs
                                    )
        else:
            self.analysis.setslice(**kwargs)
    def gimmesenseid(self,**kwargs):
        ps=kwargs.get('ps',self.slices.ps())
        idsbyps=self.slices.senseids(ps=ps)
        return idsbyps[randint(0, len(idsbyps)-1)]
    def gimmesenseidwgloss(self,**kwargs):
        tried=0
        gloss={}
        ps=kwargs.get('ps',self.slices.ps())
        for lang in self.glosslangs:
            gloss[lang]=''
        while '' in gloss.values():
            senseid=self.gimmesenseid(ps=ps)
            for lang in self.glosslangs:
                gloss[lang]=self.db.glossordefn(senseid=senseid,glosslang=lang,
                                                showurl=True)[0]
            tried+=1
            if tried> self.db.nsenseids*1.5:
                errortext=_("I've tried (randomly) {} times, and not found one "
                "of your {} senses with a gloss in each of these languages: "
                "{}. \nAre you asking for gloss "
                "languages which actually have data in your database? \nOr, are "
                "you missing gloss fields (i.e., you have only 'definition' "
                "fields)?").format(tried,self.db.nsenseids,langs)
                log.error(errortext)
                return errortext
        log.debug("Found entry {} with glosses {}".format(senseid,gloss))
        return senseid
    def checkforsenseidstosort(self,cvt=None,ps=None,profile=None,check=None):
        """This method just asks if any senseid in the given slice is unsorted.
        It stops when it finds the first one."""
        """use if sorting senseid lists aren't needed"""
        """This is redundant with updatesortingstatus()"""
        if cvt is None:
            cvt=self.slices.cvt()
        if ps is None:
            ps=self.slices.ps()
        if profile is None:
            profile=self.slices.profile()
        if check is None:
            check=self.slices.check()
        senseids=self.slices.senseids(ps=ps,profile=profile)
        vts=False
        for senseid in senseids:
            v=unlist(self.db.get("example/tonefield/form/text", senseid=senseid,
                                                    location=check).get('text'))
            if v not in ['',None]:
                vts=True
                break
        self.status.dictcheck(cvt=cvt,ps=ps,profile=profile,check=check)
        self.status.tosort(vts,cvt=cvt,ps=ps,profile=profile,check=check) #set
    def addframe(self,**kwargs):
        log.info('Tone frame to add!')
        """I should add gloss2 option here, likely just with each language.
        This is not a problem for LFIT translation fields, and it would help to
        have language specification (not gloss/gloss2), in case check languages
        change, or switch --so french is always chosen for french glosses,
        whether french is gloss or gloss2."""
        """self.toneframes should not use 'form' or 'gloss' anymore."""
        def chk():
            checktoadd=str(name.get())
            if checktoadd in ['', None]:
                text=_('Sorry, empty name! \nPlease provide at least \na frame '
                    'name, to distinguish it \nfrom other frames.')
                log.error(rx.delinebreak(text))
                if hasattr(self.addwindow,'framechk'):
                    self.addwindow.framechk.destroy()
                self.addwindow.framechk=ui.Frame(self.addwindow.scroll.content)
                self.addwindow.framechk.grid(row=1,column=0,columnspan=3,sticky='w')
                l1=ui.Label(self.addwindow.framechk,
                        text=text,
                        font='read',
                        justify=ui.LEFT,anchor='w')
                l1.grid(row=0,column=columnleft,sticky='w')
                return
            # """Define the new frame"""
            # checkdefntoadd={}
            # checkdefntoadd['field']='lc' #update this with radio!
            # for lang in langs:
            #     db['before'][lang]['text']=db['before'][lang][
            #                                                 'entryfield'].get()
            #     db['after'][lang]['text']=db['after'][lang][
            #                                                 'entryfield'].get()
            #     frame[lang]=str(
            #         db['before'][lang]['text']+'__'+db['after'][lang]['text'])
            log.info('gimmesenseid::')
            senseid=self.gimmesenseidwgloss(ps=ps) #don't give exs w/o all glosses
            log.info('gimmesenseid result: {}'.format(senseid))
            """This will need to be updated to slices!"""
            if senseid not in self.slices.senseids(ps=ps):
                log.info('bad senseid; showing error')
                self.addwindow.framechk=ui.Frame(self.addwindow.scroll.content)
                self.addwindow.framechk.grid(row=1,column=0,columnspan=3,sticky='w')
                lt=ui.Label(self.addwindow.framechk,
                        text=senseid,
                        font='read',
                        justify=ui.LEFT,anchor='w')
                lt.grid(row=0,column=0,#row=row,column=columnleft,
                        sticky='w',columnspan=2)
                return
            """Define the new frame"""
            checkdefntoadd={}
            checkdefntoadd['field']='lc' #update this with radio!
            for lang in langs:
                before=db['before'][lang]['entryfield'].get()
                after=db['after'][lang]['entryfield'].get()
                checkdefntoadd[lang]=str(
                    before+'__'+after)
            self.toneframes.addframe(ps,checktoadd,checkdefntoadd)
            # senseid=self.gimmesenseidwgloss() #don't give exs w/o all glosses
            # senseid=self.gimmesenseid()
            # This needs self.toneframes
            framed=self.taskchooser.datadict.getframeddata(senseid)
            framed.setframe(checktoadd)
            #At this point, remove this frame (in case we don't submit it)
            del self.toneframes[ps][checktoadd]
            """Display framed data"""
            if hasattr(self.addwindow,'framechk'):
                self.addwindow.framechk.destroy()
            self.addwindow.framechk=ui.Frame(self.addwindow.scroll.content)
            self.addwindow.framechk.grid(row=1,column=0,columnspan=3,sticky='w')
            tf={}
            tfd={}
            padx=50
            pady=10
            row=0
            lt=ui.Label(self.addwindow.framechk,
                    text=_("Examples for {} tone frame").format(checktoadd),
                    font='readbig',
                    justify=ui.LEFT,anchor='w')
            lt.grid(row=row,column=columnleft,sticky='w',columnspan=2,
                    padx=padx,pady=pady)
            for lang in langs:
                row+=1
                tf[lang]=('form[{}]: {}'.format(lang,checkdefntoadd[lang]))
                tfd[lang]=('(ex: '+framed.forms.framed[lang]+')')
                l1=ui.Label(self.addwindow.framechk,
                        text=tf[lang],
                        font='read',
                        justify=ui.LEFT,anchor='w')
                l1.grid(row=row,column=columnleft,sticky='w',padx=padx,
                                                                pady=pady)
                l2=ui.Label(self.addwindow.framechk,
                        text=tfd[lang],
                        font='read',
                        justify=ui.LEFT,anchor='w')
                l2.grid(row=row,column=columnleft+1,sticky='w',padx=padx,
                                                                pady=pady)
                log.info('langlabel:{}-{}'.format(tf[lang],tfd[lang]))

            """toneframes={'Nom':
                            {'name/location (e.g.,"By itself")':
                                {'analang.xyz': '__',
                                'glosslang.xyz': 'a __'},
                                'glosslang2.xyz': 'un __'},
                        }   }
            """
            row+=1
            stext=_('Use {} tone frame'.format(checktoadd))
            sub_btn=ui.Button(self.addwindow.framechk,text = stext,
                      command = lambda x=checkdefntoadd,n=checktoadd: submit(x,n))
            sub_btn.grid(row=row,column=columnleft,sticky='w')
            log.info('sub_btn:{}'.format(stext))
            self.addwindow.scroll.windowsize() #make sure scroll's big enough
            self.addwindow.scroll.totop()
            self.addwindow.scroll.tobottom()
        def unchk(event):
            #This is here to keep people from thinking they are approving what's
            #next to this button, in case any variable has been changed.
            if hasattr(self.addwindow,'framechk'):
                self.addwindow.framechk.destroy()
        def submit(checkdefntoadd,checktoadd):
            log.info("Submitting {} frame with these values: {}".format(
                                                    checktoadd,checkdefntoadd
                                                    ))
            # Having made and unset these, we now reset and write them to file.
            self.toneframes.addframe(ps,checktoadd,checkdefntoadd)
            self.status.renewchecks() #renew (not update), because of new frame
            self.settings.storesettingsfile(setting='toneframes')
            self.addwindow.destroy()
            self.settings.setcheck(checktoadd) #assume we will use this now
            if 'window' in kwargs:
                kwargs['window'].destroy()
        ps=kwargs.get('ps',self.slices.ps())
        wtitle=_("Define a New {} Tone Frame").format(ps)
        self.addwindow=ui.Window(self.frame, title=wtitle)
        self.addwindow.scroll=ui.ScrollingFrame(self.addwindow)
        self.addwindow.scroll.grid(row=0,column=0)
        self.addwindow.frame1=ui.Frame(self.addwindow.scroll.content)
        self.addwindow.frame1.grid(row=0,column=0)
        row=0
        columnleft=0
        columnword=1
        columnright=2
        namevar=ui.StringVar()
        """Text and fields, before and after, dictionaries by language"""
        db={}
        langs=[self.analang]+self.glosslangs
        for context in ['before','after']:
            db[context]={}
            for lang in langs:
                db[context][lang]={}
                db[context][lang]['text']=ui.StringVar()
        t=(_("Add {} Tone Frame").format(ps))
        ui.Label(self.addwindow.frame1,text=t+'\n',font='title'
                ).grid(row=row,column=columnleft,columnspan=3)
        row+=1
        t=_("What do you want to call the tone frame ?")
        finst=ui.Frame(self.addwindow.frame1)
        finst.grid(row=row,column=0)
        ui.Label(finst,text=t).grid(row=0,column=columnleft,sticky='e')
        name = ui.EntryField(finst)
        name.grid(row=0,column=columnright,sticky='w')
        name.bind('<Key>', unchk)
        row+=1
        row+=1
        ti={} # text instructions
        tb={} # text before
        ta={} # text after
        f={} #frames for each lang
        """Set all the label texts"""
        for lang in langs:
            if lang == self.analang:
                ti[lang]=_("Fill in the {} frame forms below.\n(include a "
                "space to separate word forms)".format(
                                        self.settings.languagenames[lang]))
                kind='form'
            else:
                ti[lang]=(_("Fill in the {} glossing "
                    "here \nas appropriate for the morphosyntactic context.\n("
                    "include a space to separate word glosses)"
                                ).format(self.settings.languagenames[lang]))
                kind='gloss'
            tb[lang]=_("What text goes *before* \n<==the {} word *{}* "
                        "\nin the frame?"
                                ).format(self.settings.languagenames[lang],kind)
            ta[lang]=_("What text goes *after* \nthe {} word *{}*==> "
                        "\nin the frame?"
                                ).format(self.settings.languagenames[lang],kind)
        """Place the labels"""
        for lang in langs:
            f[lang]=ui.Frame(self.addwindow.frame1)
            f[lang].grid(row=row,column=0)
            langrow=0
            ui.Label(f[lang],text='\n'+ti[lang]+'\n').grid(
                                                row=langrow,column=columnleft,
                                                columnspan=3)
            langrow+=1
            ui.Label(f[lang],text=tb[lang]).grid(row=langrow,
                                        column=columnright,sticky='w')
            ui.Label(f[lang],text='word',padx=0,pady=0).grid(row=langrow,
                                                        column=columnword)
            db['before'][lang]['entryfield'] = ui.EntryField(f[lang],
                                justify='right')
            db['before'][lang]['entryfield'].grid(row=langrow,
                                        column=columnleft,sticky='e')
            langrow+=1
            ui.Label(f[lang],text=ta[lang]).grid(row=langrow,
                    column=columnleft,sticky='e')
            ui.Label(f[lang],text='word',padx=0,pady=0).grid(row=langrow,
                    column=columnword)
            db['after'][lang]['entryfield'] = ui.EntryField(f[lang],
                    justify='left')
            db['after'][lang]['entryfield'].grid(row=langrow,
                    column=columnright,sticky='w')
            for w in ['before','after']:
                db[w][lang]['entryfield'].bind('<Key>', unchk)
            row+=1
        row+=1
        text=_('See the tone frame around a word from the dictionary')
        chk_btn=ui.Button(self.addwindow.frame1,text = text, command = chk)
        chk_btn.grid(row=row+1,column=columnleft,pady=100)
    def settonevariablesiterable(self,cvt='T',ps=None,profile=None,check=None):
        """This is currently called in iteration, but doesn't refresh groups,
        so it probably isn't useful anymore."""
        self.checkforsenseidstosort(cvt=cvt,ps=ps,profile=profile,check=check)
    def settonevariables(self):
        """This is currently called before sorting. This is a waste, if you're
        not going to sort afterwards –unless you need the groups."""
        self.updatesortingstatus() #this gets groups, too
    def aframe(self):
        self.runwindow.destroy()
        self.addframe()
        self.addwindow.wait_window(self.addwindow)
        self.runcheck()
    def __init__(self,parent):
        parent.params.cvt('T')
class Sort(object):
    """This class takes methods common to all sort checks, and gives sort
    checks a common identity."""
    def getsenseidsincheckgroup(self,**kwargs):
        cvt=kwargs.get('cvt',self.params.cvt())
        check=kwargs.get('check',self.params.check())
        group=kwargs.get('group',self.status.group())
        if cvt == 'T':
            senseids=self.db.get("sense", location=check, tonevalue=group,
                            path=['tonefield']).get('senseid')
        else:
            ftype=self.params.ftype()
            fkwargs={ftype+'annotationname':check,
                    ftype+'annotationvalue':group
                    }
            senseids=self.db.get("sense", **fkwargs #location=check, tonevalue=group,
                            # path=['tonefield']
                                ).get('senseid')
        return senseids
    def updatestatuslift(self,verified=False,**kwargs):
        """This should be called only by update status, when there is an actual
        change in status to write to file."""
        write=kwargs.get('write',True)
        check=kwargs.get('check',self.params.check())
        group=kwargs.get('group',self.status.group())
        #     check=self.params.check()
        profile=kwargs.get('profile',self.slices.profile())
        # profile=self.slices.profile()
        senseids=self.getsenseidsincheckgroup()
        value=self.verifictioncode(check=check,group=group)
        if verified == True:
            add=value
            rms=[]
        else:
            add=None
            rms=[value]
        """The above doesn't test for profile, so we restrict that next"""
        for senseid in self.slices.inslice(senseids): #only for this ps-profile
            rmlist=rms[:]+self.db.getverificationnodevaluebyframe(
                                        senseid,vtype=profile,
                                        analang=self.analang,
                                        frame=check)
            log.info("Removing {}".format(rmlist))
            self.db.modverificationnode(senseid,vtype=profile,
                                        analang=self.analang,
                                        add=add,rms=rmlist,
                                        write=False)
        if write == True:
            self.db.write() #for when not iterated over, or on last repeat
    def updatestatus(self,verified=False,**kwargs):
        #This function updates the status variable, not the lift file.
        group=kwargs.get('group',self.status.group())
        write=kwargs.get('write',True)
        r=self.status.update(group=group,verified=verified,write=write)
        if r: #only do this if there is a change in status
            self.updatestatuslift(group=group,verified=verified,write=write)
        return
    def addmodadhocsort(self):
        def submitform():
            if profilevar.get() == "":
                log.debug("Give a name for this adhoc sort group!")
                return
            self.runwindow.destroy()
            ids=[]
            for var in [x for x in vars if len(x.get()) >1]:
                log.log(2,"var {}: {}".format(vars.index(var),var.get()))
                ids.append(var.get())
            log.log(2,"ids: {}".format(ids))
            newprofile=profilevar.get()
            self.settings.set('profile',newprofile,refresh=False)
            #Add to dictionaries before updating them below
            log.debug("profile: {}".format(newprofile))
            """Fix this!"""
            self.slices.adhoc(ids,profile=newprofile)#[ps][profile]=ids
            self.settings.storesettingsfile(setting='adhocgroups')#since we changed this.
            """Is this OK?!?"""
            self.slices.updateslices() #This pulls from profilesbysense
            # self.makecountssorted() #we need these to show up in the counts.
            self.settings.storesettingsfile(setting='profiledata')#since we changed this.
            #so we don't have to do this again after each profile analysis
        self.getrunwindow()
        profile=self.slices.profile()
        ps=self.slices.ps()
        if profile in [x[0] for x in self.slices.profiles()]: #profilecountsValid]:
            new=True
            title=_("New Ad Hoc Sort Group for {} Group".format(ps))
        else:
            new=False
            title=_("Modify Existing Ad Hoc Sort Group for {} Group".format(ps))
        self.runwindow.title(title)
        padx=50
        pady=10
        ui.Label(self.runwindow.frame,text=title,font='title',
                ).grid(row=0,column=0,sticky='ew')
        allpssensids=self.slices.senseidsbyps(ps)
        if len(allpssensids)>70:
            self.runwindow.waitdone()
            text=_("This is a large group ({})! Are you in the right "
                    "grammatical category?".format(len(allpssensids)))
            log.error(text)
            w=ui.Label(self.runwindow.frame,text=text)
            w.grid(row=1,column=0,sticky='ew')
            b=ui.Button(self.runwindow.frame, text=_("OK"), command=w.destroy, anchor='c')
            b.grid(row=2,column=0,sticky='ew')
            self.runwindow.wait_window(w)
            w.destroy()
        if self.runwindow.exitFlag.istrue():
            return
        else:
            self.runwindow.wait()
        ui.Label(self.runwindow.frame,text=title,font='title',
                ).grid(row=0,column=0,sticky='ew')
        text=_("This page will allow you to set up your own sets of dictionary "
                "senses to sort, within the '{0}' grammatical category. \nYou "
                "should only do this if the '{0}' grammatical category is so "
                "small that sorting them by syllable profile gives you "
                "unusably small slices of your database."
                "\nIf you want to compare words that are currently in "
                "different grammatical categories, put them first into the "
                "same grammatical category in another tool (e.g., FLEx or "
                "WeSay), then put them in an Ad Hoc group here."
                # "\nIf you're looking at a group you created earlier, and "
                "\nIf you want to create a new group, exit here, select a "
                "non-Ad Hoc syllable profile, and try this window again."
                "".format(ps))
        inst=ui.Label(self.runwindow.frame,text=text,
                row=1,column=0,sticky='ew'
                )
        inst.wrap()
        qframe=ui.Frame(self.runwindow.frame)
        qframe.grid(row=2,column=0,sticky='ew')
        text=_("What do you want to call this group for sorting {} words?"
                "".format(ps))
        instq=ui.Label(qframe,text=text,
                row=0,column=0,sticky='ew',pady=20)
        if new:
            default=None
        else:
            default=profile
        profilevar=ui.StringVar(value=default)
        namefield = ui.EntryField(qframe,textvariable=profilevar)
        namefield.grid(row=0,column=1)
        text=_("Select the {} words below that you want in this group, then "
                "click ==>".format(ps))
        ui.Label(qframe,text=text).grid(row=1,column=0,sticky='ew',pady=20)
        sub_btn=ui.Button(qframe,text = _("OK"),
                  command = submitform,anchor ='c')
        sub_btn.grid(row=1,column=1,sticky='w')
        vars=list()
        row=0
        scroll=ui.ScrollingFrame(self.runwindow.frame)
        for id in allpssensids:
            log.debug("id: {}; index: {}; row: {}".format(id,
                                                    allpssensids.index(id),row))
            idn=allpssensids.index(id)
            vars.append(ui.StringVar())
            adhocslices=self.slices.adhoc()
            if (ps in adhocslices and profile in adhocslices[ps] and
                                                id in adhocslices[ps][profile]):
                vars[idn].set(id)
            else:
                vars[idn].set(0)
            framed=self.taskchooser.datadict.getframeddata(id)
            forms=framed.formatted(noframe=True)
            log.debug("forms: {}".format(forms))
            ui.CheckButton(scroll.content, text = forms,
                                variable = vars[allpssensids.index(id)],
                                onvalue = id, offvalue = 0,
                                ).grid(row=row,column=0,sticky='ew')
            row+=1
        scroll.grid(row=3,column=0,sticky='ew')
        self.runwindow.waitdone()
        self.runwindow.wait_window(scroll)
    def removesenseidfromgroup(self,senseid,**kwargs):
        """Generalize for segments?"""
        check=kwargs.get('check',self.params.check())
        group=kwargs.get('group',self.status.group())
        cvt=kwargs.get('cvt',self.params.cvt())
        write=kwargs.get('write',True)
        sorting=kwargs.get('sorting',True) #Default to verify button
        log.info(_("Removing senseid {} from subcheck {}".format(senseid,group)))
        #This should only *mod* if already there
        if cvt == 'T':
            self.db.addmodexamplefields(senseid=senseid,
                                analang=self.analang,
                                fieldtype='tone',location=check,
                                fieldvalue='',  #this value only change
                                showurl=True,
                                write=False)
            tgroups=self.db.get("example/tonefield/form/text", senseid=senseid,
                            location=check).get('text')
        else:
            tgroups=self.marksortgroup(senseid,None,group='')
        log.info("Checking that removal worked")
        if tgroups in [[],'',['']]:
            log.info("Field removal succeeded! LIFT says '{}', = []."
                                                            "".format(tgroups))
        elif len(tgroups) == 1:
            tgroup=tgroups[0]
            log.error("Field removal failed! LIFT says '{}', != []."
                                                            "".format(tgroup))
        elif len(tgroups) > 1:
            log.error("Found {} tone values: {}; Fix this!"
                                            "".format(len(tgroups),tgroups))
            return
        rm=self.verifictioncode(check=check,group=group)
        profile=kwargs.get('profile',self.slices.profile())
        self.db.modverificationnode(senseid,vtype=profile,analang=self.analang,
                                                        rms=[rm],write=False)
        self.status.last('sort',update=True)
        if write:
            self.db.write()
        if sorting:
            self.status.marksenseidtosort(senseid)
    def ncheck(self):
        r=self.status.nextcheck(tosort=True)
        if not r:
            self.status.nextcheck(toverify=True)
        self.runwindow.destroy()
        self.runcheck()
    def nprofile(self):
        r=self.status.nextprofile(tosort=True)
        if not r:
            self.status.nextprofile(toverify=True)
        self.runwindow.destroy()
        self.runcheck()
    def nps(self):
        self.slices.nextps()
        r=self.status.nextprofile(tosort=True)
        if not r:
            self.status.nextprofile(toverify=True)
        self.runwindow.destroy()
        self.runcheck()
    def runcheck(self):
        self.settings.storesettingsfile()
        # t=(_('Run Check'))
        log.info("Running check...")
        # i=0
        # ps=self.slices.ps()
        # if not ps:
        #     self.getps()
        # group=self.status.group()
        # analang=self.params.analang()
        # if None in [analang, ps, group]:
        #     log.debug(_("'Null' value (what does this mean?): {} {} {}").format(
        #                                 self.analang, ps, group))
        cvt=self.params.cvt()
        check=self.params.check()
        profile=self.slices.profile()
        if not profile:
            self.getprofile()
        """further specify check check in maybesort, where you can send the user
        on to the next setting"""
        if (check not in self.status.checks() #tosort=True
                # and check not in self.status.checks(toverify=True)
                # and check not in self.status.checks(tojoin=True)
                ):
            exit=self.getcheck()
            if exit and not self.exitFlag.istrue():
                return #if the user didn't supply a check
        self.updatesortingstatus() # Not just tone anymore
        self.maybesort()
    def presort(self,senseids,check,group):
        if self.status.presorted():
            log.info(_("Presorting for this check/slice already done! ({}; {})"
                        "").format(check,senseids[0]))
            return
        if self.cvt == 'T':
            log.error("This function isn't used for tone!")
            return
        else:
            framed=None
        for senseid in senseids:
            self.marksortgroup(senseid,framed,group,check=check,nocheck=True)
        self.updatestatus(group=group,write=True) # marks the group unverified.
    def marksortgroup(self,senseid,framed,group,**kwargs):
        # group=kwargs.get('group',self.status.group())
        write=kwargs.get('write',True)
        check=kwargs.get('check',self.params.check())
        ftype=kwargs.get('ftype',self.params.ftype())
        nocheck=kwargs.get('nocheck',False)
        guid=None
        # if group is None or group == '':
        #     log.error("groupselected: {}; this should never happen"
        #                 "".format(group))
        #     exit()
        log.debug("Adding {} value for {} check, "
                "senseid: {} guid: {} (in main_lift.py)".format(
                    group,
                    check,
                    senseid,
                    guid))
        if self.cvt == 'T':
            if not framed:
                log.error("How did we get no frame? (presort on T?)")
                return
            ftype=self.toneframes[self.ps][self.check]['field'] #this must match check!
            self.db.addmodexamplefields( #This should only mod if already there
                                    senseid=senseid,
                                    analang=self.analang,
                                    fieldtype='tone',
                                    #frames should be ftype specific
                                    location=check,
                                    ftype=ftype, #needed to get correct form
                                    framed=framed,
                                    fieldvalue=group,
                                    write=False
                                    )
            if not nocheck:
                newgroup=unlist(self.db.get("example/tonefield/form/text",
                        senseid=senseid, location=self.check).get('text'))
        else:
            self.db.annotatefield(
                                senseid=senseid,
                                analang=self.analang,
                                name=check,
                                ftype=ftype,
                                value=group,
                                write=False
                                )
            if not nocheck:
                newgroup=unlist(self.db.fieldvalue(
                                senseid=senseid,
                                analang=self.analang,
                                name=check,
                                ftype=ftype,
                                ))
        if not nocheck:
            if newgroup != group:
                log.error("Field addition failed! LIFT says {}, not {}.".format(
                                                    newgroup,group))
            else:
                log.info("Field addition succeeded! LIFT says {}, which is {}."
                                        "".format(newgroup,group))
        self.status.last('sort',update=True)
        self.status.tojoin(True) # will need to be distinguished again
        if not nocheck:
            self.updatestatus(group=group,write=write) # marks the group unverified.
        if write:
            self.db.write() #This is never iterated over; just one entry at a time.
        return newgroup
    def updatesortingstatus(self, store=True, **kwargs):
        """This reads LIFT to create lists for sorting, populating lists of
        sorted and unsorted senses, as well as sorted (but not verified) groups.
        So don't iterate over it. Instead, use checkforsenseidstosort to just
        confirm tosort status"""
        """To get this from the object, use status.tosort(), todo() or done()"""
        cvt=kwargs.get('cvt',self.params.cvt())
        ps=kwargs.get('ps',self.slices.ps())
        profile=kwargs.get('profile',self.slices.profile())
        check=kwargs.get('check',self.params.check())
        kwargs['wsorted']=True #ever not?
        if cvt == 'T':
            senseids=self.slices.senseids(ps=ps,profile=profile)
        else:
            senseids=[]
            groups=self.status.groups(wsorted=True)
            for group in self.status.groups(cvt=cvt):
                self.buildregex(cvt=cvt,profile=profile,check=check,group=group)
                # log.log(2,"self.regex: {}; self.regexCV: {}".format(self.regex,
                #                                             self.regexCV))
                s=set(self.senseidformsbyregex(self.regex,ps=ps))
                if s: #senseids just for this group
                    if group not in groups:
                        groups.append(group)
                    self.presort(list(s),check,group)
                    senseids+=list(s)
            self.status.presorted(True)
        self.status.renewsenseidstosort([],[]) #will repopulate
        groups=[]
        for senseid in senseids:
            if cvt == 'T':
                v=firstoflist(self.db.get("example/tonefield/form/text",
                                senseid=senseid,
                                location=check
                                ).get('text'),
                        othersOK=True) #Don't complain if more than one found.
            else:
                ftype=self.params.ftype()
                kwargs={ftype+'annotationname':check,
                        # ftype+'annotationvalue':group
                        }
                v=firstoflist(self.db.get("citation/form/annotation",
                                lang=self.params.analang(),
                                # annotationname=check,
                                # annotationvalue=
                                senseid=senseid,
                                # location=check
                                **kwargs
                                ).get('value'),
                        othersOK=True) #Don't complain if more than one found.
            # if v:
            #     log.debug("Found tone value (updatesortingstatus): {} ({})"
            #             "".format(v, type(v)))
            if v in ['','None',None]: #unlist() returns strings
                log.info("Marking senseid {} tosort (v: {})".format(senseid,v))
                self.status.marksenseidtosort(senseid)
            else:
                log.info("Marking senseid {} sorted (v: {})".format(senseid,v))
                self.status.marksenseidsorted(senseid)
                if v not in ['NA','ALLOK']:
                    groups.append(v)
        """update 'tosort' status"""
        if self.status.senseidstosort():
            log.info("updatesortingstatus shows senseidstosort remaining")
            vts=True
        else:
            log.info("updatesortingstatus shows no senseidstosort remaining")
            vts=False
        self.status.tosort(vts,**kwargs)
        """update status groups"""
        sorted=list(dict.fromkeys(groups))
        self.status.groups(sorted,**kwargs)
        verified=self.status.verified(**kwargs) #read
        """This should pull verification status from LIFT, someday"""
        for v in verified:
            if v not in sorted:
                log.error("Removing verified group {} not in actual groups: {}!"
                            "".format(v, sorted))
                verified.remove(v)
        self.status.verified(verified,**kwargs) #set
        log.info("updatesortingstatus results ({}): sorted: {}, verified: {}, "
                "tosort: {}".format(kwargs.values(),sorted,verified,vts))
        if store:
            self.settings.storesettingsfile(setting='status')
    def notdonewarning(self):
        self.getrunwindow(nowait=True)
        buttontxt=_("Sort!")
        text=_("Hey, you're not done with {} {} words by {}!"
                "\nCome back when you have time; restart where you left "
                "off by pressing ‘{}’".format(self.ps,self.profile,self.check,
                                                buttontxt))
        ui.Label(self.runwindow.frame, text=text).grid(row=0,column=0)
    def maybesort(self):
        """This should look for one group to verify at a time, with sorting
        in between, then join and repeat"""
        def tosortupdate():
            log.info("maybesort tosortbool:{}; tosort:{}; sorted:{}".format(
                                self.status.tosort(),
                                self.status.senseidstosort(),
                                self.status.senseidssorted()
                                ))
        cvt=self.params.cvt()
        self.check=self.params.check()
        self.ps=self.slices.ps()
        self.profile=self.slices.profile()
        log.info("cvt:{}; ps:{}; profile:{}; check:{}".format(cvt,self.ps,
                                                    self.profile,self.check))
        tosortupdate()
        log.info("Maybe Sort (from maybesort)")
        if self.status.checktosort(): # w/o parameters, tests current check
            log.info("Sort (from maybesort)")
            quit=self.sort()
            if quit == True:
                if not self.exitFlag.istrue():
                    self.notdonewarning()
                return
        tosortupdate()
        log.info("Going to verify the first of these groups now: {}".format(
                                    self.status.groups(toverify=True)))
        log.info("Maybe verify (from maybesort)")
        groupstoverify=self.status.groups(toverify=True)
        if groupstoverify:
            self.status.group(groupstoverify[0]) #just pick the first now
            log.info("verify (from maybesort)")
            exitv=self.verify()
            if exitv == True: #fix this!
                if not self.exitFlag.istrue():
                    self.notdonewarning()
                return
            self.maybesort()
            return
        # Offer to join in any case:
        if self.status.tojoin():
            log.info("join (from maybesort)")
            exit=self.join()
            log.debug("exit: {}".format(exit))
        else:
            exit=False
        if exit:
            if not self.exitFlag.istrue():
                self.notdonewarning()
            #This happens when the user exits the window
            log.debug("exiting join True")
            #Give an error window here
            return
        elif not exit:
            self.getrunwindow()
            done=_("All ‘{}’ groups in the ‘{}’ {} are verified and "
                    "distinct!".format(self.profile,self.check,
                                                self.checktypename[cvt]))
            row=0
            if self.exitFlag.istrue():
                return
            ui.Label(self.runwindow.frame, text=done,
                    row=row,column=0,columnspan=2)
            row+=1
            ui.Label(self.runwindow.frame, text='',
                        image=self.frame.theme.photo[cvt],
                        row=row,column=0,columnspan=2)
            row+=1
            ctosort=self.status.checks(tosort=True)
            ctoverify=self.status.checks(toverify=True)
            ptosort=self.status.profiles(tosort=True)
            ptoverify=self.status.profiles(toverify=True)
            ui.Label(self.runwindow.frame,text=_("Continue to sort"),
                    columnspan=2,row=row,column=0)
            row+=1
            text1=_("same words")
            text2=_("same frame")
            if ctosort or ctoverify:
                b1=ui.Button(self.runwindow.frame, anchor='c',
                    text=text1+'\n('+_("next {}").format(self.checktypename[cvt])+')',
                    command=self.ncheck)
                b1t=ui.ToolTip(b1,_("Automatically pick "
                                "the next {} to sort for the ‘{}’ profile."
                                "".format(self.profile,self.checktypename[cvt])))
            elif cvt == 'T':
                b1=ui.Button(self.runwindow.frame, anchor='c',
                    text=text1+'\n('+_("define a new frame")+')',
                    command=self.aframe)
                b1t=ui.ToolTip(b1,_("You're done with tone frames already defined "
                                "for the ‘{}’ profile. If you want to continue "
                                "with this profile, define a new frame here."
                                "".format(self.profile)))
            b1.grid(row=row,column=0,sticky='e')
            if ptosort or ptoverify:
                b2=ui.Button(self.runwindow.frame, anchor='c',
                    text=text2+'\n('+_("next syllable profile")+')',
                    command=self.nprofile)
                b2t=ui.ToolTip(b2,_("You're done with ‘{0}’ {2} "
                                "defined for the ‘{1}’ profile. Click here to "
                                "Automatically select the next syllable "
                                "profile for ‘{0}’."
                                "".format(self.ps,self.profile,
                                self.checktypename[cvt])))
            else:
                b2=ui.Button(self.runwindow.frame, anchor='c',
                    text=text2+'\n('+_("next lexical category")+')',
                    command=self.nps)
                b2t=ui.ToolTip(b2,_("You're done with {} "
                                "defined for the top ‘{}’ syllable profiles. "
                                "Click here to automatically select the next "
                                "grammatical category."
                                "".format(self.ps, self.checktypename[cvt])))
            b2.grid(row=row,column=1,sticky='w')
            if self.parent.exitFlag.istrue():
                return
            w=int(max(b1.winfo_reqwidth(),b2.winfo_reqwidth())/(
                                        self.parent.winfo_screenwidth()/150))
            log.log(2,"b1w:{}; b2w: {}; maxb1b2w: {}".format(
                                    b1.winfo_reqwidth(),b2.winfo_reqwidth(),w))
            for i in [b1,b2]:
                i.config(width=w)
            self.runwindow.waitdone()
            return
    def presenttosort(self):
        scaledpady=int(50*program['scale'])
        groupselected=None
        """these just pull the current lists from the object"""
        senseids=self.status.senseidstosort()
        sorted=self.status.senseidssorted()
        senseid=senseids[0]
        progress=(str(self.thissort.index(senseid)+1)+'/'+str(len(self.thissort)))
        framed=self.taskchooser.datadict.getframeddata(senseid)
        framed.setframe(self.check)
        """After the first entry, sort by groups."""
        log.debug('groups: {}'.format(self.status.groups(wsorted=True)))
        if self.runwindow.exitFlag.istrue():
            return 1,1
        ui.Label(self.titles, text=progress, font='report', anchor='w'
                                        ).grid(column=1, row=0, sticky="ew")
        text=framed.formatted()
        entryview=ui.Frame(self.runwindow.frame, column=1, row=1, sticky="new")
        self.sortitem=self.buttonframe.sortitem=ui.Label(entryview,
                                text=text,font='readbig',
                                column=0,row=0, sticky="w",
                                pady=scaledpady
                                )
        self.sortitem.wrap()
        self.runwindow.waitdone()
        for b in self.buttonframe.groupbuttonlist:
            b.setcanary(self.sortitem)
        self.runwindow.wait_window(window=self.sortitem)
        if self.runwindow.exitFlag.istrue():
            return 1,1
        else:
            return senseid,framed
    def sort(self):
        # This window/frame/function shows one entry at a time (with pic?)
        # for the user to select a tone group based on buttons defined below.
        # We work only with one ps and profile at a time (of course).
        # The end result is that the user is shown one word to compare against
        # a set of other words, and is asked to say which one it is like.
        # In the event that the word isn't like any of them (and on the first
        # word!), a new group is formed, and added to the list of comparatives
        # (which is autogenerated, to update whenever a group is added or
        # taken out). Whenever a group is selected, the word being iterated
        # through is marked as the same tone group, and that tone group is
        # marked as unverified (not yet implimented!).
        # Groups are initially unlabelled for content, with each group labeled
        # with an integer --we just need a unique name, in any case, and the
        # groups are by frame (surface distinctions), rather than by lexeme
        # (underlying distinctions) in any case.
        #This function should exit 1 on a window close, or finish with None
        log.info('Running sort:')
        self.getrunwindow()
        """sortingstatus() checks by ps,profile,check (frame),
        for the presence of a populated fieldtype='tone'. So any time any of
        the above is changed, this variable should be reset."""
        """Can't do this test suite unless there are unsorted entries..."""
        """things that don't change in this fn"""
        self.thissort=self.status.senseidstosort()[:] #current list
        log.info("Going to sort these senseids: {}".format(self.status.senseidstosort()))
        groups=self.status.groups(wsorted=True)
        """Children of runwindow.frame"""
        if self.exitFlag.istrue():
            return
        self.titles=ui.Frame(self.runwindow.frame, row=0, column=0,
                                                    sticky="ew", columnspan=2)
        ui.Label(self.runwindow.frame, image=self.frame.theme.photo['sort'],
                        text='',
                        ).grid(row=1,column=0,rowspan=3,sticky='nw')
        # scroll=self.runwindow.frame.scroll=ui.ScrollingFrame(self.runwindow.frame)
        # scroll.grid(row=2, column=1, sticky="new")
        self.buttonframe=SortButtonFrame(self.runwindow.frame, self, groups,
                                row=2, column=1, sticky="new")
        """Titles"""
        if self.cvt == 'T':
            context='tone melody'
            descripttext=("in ‘{}’ frame").format(self.check)
        else:
            context=self.params.cvcheckname(self.check)
            descripttext=("by {}").format(self.check)
        title=_("Sort {} Tone ({})").format(
                                        self.settings.languagenames[self.analang],
                                        descripttext)
        ui.Label(self.titles, text=title,font='title',anchor='c',
                                            column=0, row=0, sticky="ew")
        instructions=_("Select the one with the same {} as").format(context)
        ui.Label(self.titles, text=instructions, font='instructions',
                anchor='c', column=0, row=1, sticky="ew")
        """Stuff that changes by lexical entry
        The second frame, for the other two buttons, which also scroll"""
        while self.status.tosort(): # and not self.runwindow.exitFlag.istrue():
            senseid,framed=self.presenttosort()
            if senseid == 1:
                return 1
            """thread here? No, this updates the UI, as well as writing data"""
            self.buttonframe.sortselected(senseid,framed)
        if self.runwindow.exitFlag.istrue():
            return 1
        self.runwindow.resetframe()
        return
    def reverify(self):
        group=self.status.group()
        check=self.params.check()
        log.info("Reverifying a framed tone group, at user request: {}-{}"
                    "".format(check,group))
        if check not in self.status.checks(wsorted=True):
            self.getcheck() #guess=True
        done=self.status.verified()
        if group not in done:
            log.info("Group ({}) not in groups ({}); asking."
                    "".format(group,done))
            w=self.getgroup(wsorted=True)
            w.wait_window(w)
            group=self.status.group()
            if group not in done: #i.e., still
                log.info("I asked for a framed tone group, but didn't get one.")
                return
        done.remove(group)
        self.updatesortingstatus() # Not just tone anymore
        self.maybesort()
    def verify(self,menu=False):
        def updatestatus():
            log.info("Updating status with {}, {}, {}".format(check,group,verified))
            self.updatestatus(verified=verified,write=False)
            self.maybewrite()
        log.info("Running verify!")
        """Show entries each in a row, users mark those that are different, and we
        remove that group designation from the entry (so the entry will show up on
        the next sorting). After all entries have been verified as "the same",
        click a button at the bottom of the screen for "verify", or "these are
        all the same", or some such. register with addresults (or elsewhere?).
        To show this window for a given tone group, we need to look through the
        tone group for any entries that aren't marked for verified (or will we
        just mark it one place, and that we're marking faithfully?)
        If we mark toneframes[lang][ps][name][melody]=None (v 'verified'), that
        could be enough, if we're storing that info somewhere --writing xml?
        on clicking 'verify', we take the user back to sort (to resort anything
        that got pulled from the group), then on to the next largest unverified
        pile.
        """
        #This function should exit 1 on a window close, 0/None on all ok.
        check=self.params.check()
        groups=self.status.groups(toverify=True) #needed for progress
        group=self.status.group()
        # The title for this page changes by group, below.
        self.getrunwindow(msg="preparing to verify group: {}".format(group))
        oktext='These all have the same {}'.format(self.params.cvcheckname())
        instructions=_("Read down this list to verify they all have the same "
            "{}. Select any word with a different tone melody to "
            "remove it from the list.").format(self.params.cvcheckname())
        """group is set here, but probably OK"""
        self.status.build()
        last=False
        if self.runwindow.exitFlag.istrue():
            return 1
        if group in self.status.verified():
            log.info("‘{}’ already verified, continuing.".format(group))
            return
        senseids=self.exs.senseidsinslicegroup(group,check)
        if not senseids:
            groups=self.status.groups() #from which to remove, put back
            log.info("Groups: {}".format(self.status.groups(toverify=True)))
            verified=False
            log.info("Group ‘{}’ has no examples; continuing.".format(group))
            log.info("Groups: {}".format(self.status.groups(toverify=True)))
            updatestatus()
            log.info("Group-groups: {}-{}".format(group,groups))
            if groups:
                groups.remove(group)
            log.info("Group-groups: {}-{}".format(group,groups))
            self.status.groups(groups,wsorted=True)
            log.info("Groups: {}".format(self.status.groups(toverify=True)))
            return
        elif len(senseids) == 1:
            verified=True
            log.info("Group ‘{}’ only has {} example; marking verified and "
                    "continuing.".format(group,len(senseids)))
            updatestatus()
            return
        title=_("Verify {} Group ‘{}’ for ‘{}’ ({})").format(
                                    self.settings.languagenames[self.analang],
                                    group,
                                    check,
                                    self.params.cvcheckname()
                                    )
        titles=ui.Frame(self.runwindow.frame,
                        column=0, row=0, columnspan=2, sticky="w")
        ui.Label(titles, text=title, font='title', column=0, row=0, sticky="w")
        """Move this to bool vars, like for sort"""
        if hasattr(self,'groupselected'): #so it doesn't get in way later.
            delattr(self,'groupselected')
        row=0
        column=0
        if group in groups:
            progress=('('+str(groups.index(group)+1)+'/'+str(len(
                                                            groups))+')')
            ui.Label(titles,text=progress,anchor='w',row=0,column=1,sticky="ew")
        ui.Label(titles, text=instructions,
                row=1, column=0, columnspan=2, sticky="wns")
        ui.Label(self.runwindow.frame, image=self.frame.theme.photo['verify'],
                        text='', row=1,column=0,
                        # rowspan=3,
                        sticky='nws')
        """Scroll after instructions"""
        self.sframe=ui.ScrollingFrame(self.runwindow.frame,
                                    row=1,column=1,
                                    # columnspan=2,
                                    sticky='wsn')
        """put entry buttons here."""
        for senseid in senseids:
            if senseid is None: #needed?
                continue
            self.verifybutton(self.sframe.content,senseid,
                                row, column,
                                label=False)
            if not self.buttoncolumns or (self.buttoncolumns and
                                            row+1<self.buttoncolumns):
                row+=1
            else:
                column+=1
                column%=self.buttoncolumns # from 0 to cols-1
                if not column:
                    row+=1
                elif row+1 == self.buttoncolumns:
                    row=0
            # log.info("Next button at r:{}, c:{}".format(row,column))
        bf=ui.Frame(self.sframe.content)
        bf.grid(row=max(row+1,self.buttoncolumns+1), column=0, sticky="ew") #Keep on own row
        b=ui.Button(bf, text=oktext,
                        cmd=bf.destroy,
                        anchor="w",
                        font='instructions'
                        )
        b.grid(column=0, row=0, sticky="ew")
        if self.runwindow.exitFlag.istrue():
            return 1
        self.sframe.windowsize()
        self.runwindow.waitdone()
        b.wait_window(bf)
        if self.runwindow.exitFlag.istrue(): #i.e., user exited, not hit OK
            return 1
        log.debug("User selected ‘{}’, moving on.".format(oktext))
        self.status.last('verify',update=True)
        verified=True
        updatestatus()
    def verifybutton(self,parent,senseid,row,column=0,label=False,**kwargs):
        # This must run one subcheck at a time. If the subcheck changes,
        # it will fail.
        # should move to specify location and fieldvalue in button lambda
        def notok():
            self.removesenseidfromgroup(senseid,sorting=True,write=False)
            self.maybewrite()
            bf.destroy()
        if 'font' not in kwargs:
            kwargs['font']='read'
        if 'anchor' not in kwargs:
            kwargs['anchor']='w'
        #This should be pulling from the example, as it is there already
        framed=self.taskchooser.datadict.getframeddata(senseid)
        check=self.params.check()
        framed.setframe(check)
        text=framed.formatted(showtonegroup=False)
        if label==True:
            b=ui.Label(parent, text=text,
                    **kwargs
                    ).grid(column=column, row=row,
                            sticky="ew",
                            ipady=15)
        else:
            bf=ui.Frame(parent, pady='0') #This will be killed by removesenseidfromgroup
            bf.grid(column=column, row=row, sticky='ew')
            b=ui.Button(bf, text=text, pady='0',
                    cmd=notok,
                    **kwargs
                    ).grid(column=column, row=0,
                            sticky="ew",
                            ipady=15*program['scale'] #Inside the buttons...
                            )
    def join(self):
        log.info("Running join!")
        """This window shows up after sorting, or maybe after verification, to
        allow the user to join groups that look the same. I think before
        verification, as this would require the new pile to be verified again.
        also, the joining would provide for one less group to match against
        (hopefully semi automatically).
        """
        #This function should exit 1 on a window close, 0/None on all ok.
        self.getrunwindow()
        cvt=self.params.cvt()
        check=self.params.check()
        ps=self.slices.ps()
        profile=self.slices.profile()
        groups=self.status.groups(wsorted=True) #these should be verified, too.
        if len(groups) <2:
            log.debug("No tone groups to distinguish!")
            if not self.exitFlag.istrue():
                self.runwindow.waitdone()
            return 0
        title=_("Review Groups for {} Tone (in ‘{}’ frame)").format(
                                        self.settings.languagenames[self.analang],
                                        check
                                        )
        oktext=_('These are all different')
        introtext=_("Congratulations! \nAll your {} with profile ‘{}’ are "
                "sorted into the groups exemplified below (in the ‘{}’ frame). "
                "Do any of these have the same tone melody? "
                "If so, click on two groups to join. "
                "If not, just click ‘{ok}’."
                ).format(ps,profile,check,ok=oktext)
        log.debug(introtext)
        self.runwindow.resetframe()
        self.runwindow.frame.titles=ui.Frame(self.runwindow.frame,
                                            column=0, row=0,
                                            columnspan=2, sticky="ew"
                                            )
        ltitle=ui.Label(self.runwindow.frame.titles, text=title,
                font='title',
                column=0, row=0, sticky="ew",
                )
        i=ui.Label(self.runwindow.frame.titles,
                    text=introtext,
                    row=1,column=0, sticky="w",
                    )
        i.wrap()
        ui.Label(self.runwindow.frame,
                image=self.frame.theme.photo['join'],
                text='',
                row=1,column=0,rowspan=2,sticky='nw'
                )
        self.sframe=ui.ScrollingFrame(self.runwindow.frame,
                                        row=1,column=1,sticky='w')
        self.sortitem=self.sframe.content
        row=column=0
        groupvars={}
        b={}
        for group in groups:
            b[group]=ToneGroupButtonFrame(self.sortitem, self, self.exs, group,
                                    showtonegroup=True,
                                    labelizeonselect=True
                                    )
            b[group].grid(column=column, row=row, sticky='ew')
            groupvars[group]=b[group].var()
            if not self.buttoncolumns or (self.buttoncolumns and
                                            row+1<self.buttoncolumns):
                row+=1
            else:
                column+=1
                column%=self.buttoncolumns # from 0 to cols-1
                if not column:
                    row+=1
                elif row+1 == self.buttoncolumns:
                    row=0
            # log.info("Next button at r:{}, c:{}".format(row,column))
        """If all is good, destroy this frame."""
        self.runwindow.waitdone()
        ngroupstojoin=0
        while ngroupstojoin < 2:
            bok=ui.Button(self.sortitem, text=oktext,
                    cmd=self.sortitem.destroy,
                    anchor="c",
                    font='instructions',
                    column=0,
                    row=max(row+1,self.buttoncolumns+1),
                    sticky="ew")
            for group in b:
                b[group].setcanary(bok) #this must be done after bok exists
            log.info("making button!")
            self.runwindow.frame.wait_window(bok)
            groupstojoin=selected(groupvars)
            ngroupstojoin=len(groupstojoin)
            if ngroupstojoin == 2 or not self.sortitem.winfo_exists():
                break
        if self.runwindow.exitFlag.istrue():
            return 1
        if ngroupstojoin < 2:
            log.info("User selected ‘{}’ with {} groups selected, moving on."
                    "".format(oktext,ngroupstojoin))
            #this avoids asking the user about it again, until more sorting:
            self.status.tojoin(False)
            self.runwindow.destroy()
            return 0
        elif ngroupstojoin > 2:
            log.info("User selected ‘{}’ with {} groups selected, This is "
                    "probably a mistake ({} selected)."
                    "".format(oktext,ngroupstojoin,groupstojoin))
            return self.join() #try again
        else:
            log.info("User selected ‘{}’ with {} groups selected, joining "
                    "them. ({} selected)."
                    "".format(oktext,ngroupstojoin,groupstojoin))
            msg=_("Now we're going to move group ‘{0}’ into "
                "‘{1}’, marking ‘{1}’ unverified.".format(*groupstojoin))
            self.runwindow.wait(msg=msg)
            log.debug(msg)
            """All the senses we're looking at, by ps/profile"""
            self.updatebygroupsenseid(*groupstojoin)
            groups.remove(groupstojoin[0])
            write=False
            for group in groupstojoin: #not verified=True --since joined
                self.updatestatus(group=group,write=write)
                write=True #For second group
            self.maybesort() #go back to verify, etc.
        """'These are all different' doesn't need to be saved anywhere, as this
        can happen at any time. Just move on to verification, where each group's
        sameness will be verified and recorded."""
    def tryNAgain(self):
        check=self.params.check()
        if check in self.status.checks():
            senseids=self.getsenseidsincheckgroup(group='NA')
            # self.slices.senseids()
            # ftype=self.toneframes[check]['field'] #this must match check!
        else:
            #Give an error window here
            log.error("Not Trying again; set a check first!")
            self.getrunwindow(nowait=True)
            buttontxt=_("Sort!")
            text=_("Not Trying Again; set a tone frame first!")
            ui.Label(self.runwindow.frame, text=text).grid(row=0,column=0)
            return
        for senseid in senseids: #this is a ps-profile slice
            self.removesenseidfromgroup(senseid)
            # self.db.addmodexamplefields(senseid=senseid,fieldtype='tone',
            #                 location=check,#ftype=ftype,
            #                 fieldvalue='', #just clear this
            #                 oldfieldvalue='NA', showurl=True #if this
            #                 )
        self.runcheck()
    def updatebygroupsenseid(self,oldtonevalue,newtonevalue,verified=False):
        """Generalize this for segments"""
        # This function updates the field value and verification status (which
        # contains the field value) in the lift file.
        # This is all the words in the database with the given
        # location:value correspondence (any ps/profile)
        check=self.params.check()
        lst2=self.db.get('sense',location=check,tonevalue=oldtonevalue
                                                                ).get('senseid')
        # We are agnostic of verification status of any given entry, so just
        # use this to change names, not to mark verification status (do that
        # with self.updatestatuslift())
        rm=self.verifictioncode(check=check,group=oldtonevalue)
        add=self.verifictioncode(check=check,group=newtonevalue)
        """The above doesn't test for profile, so we restrict that next"""
        profile=self.slices.profile()
        senseids=self.slices.inslice(lst2)
        for senseid in senseids:
            """This updates the fieldvalue from 'fieldvalue' to
            'newfieldvalue'."""
            self.db.addmodexamplefields(senseid=senseid,fieldtype='tone',
                                location=check,#fieldvalue=oldtonevalue,
                                fieldvalue=newtonevalue,write=False)
            self.db.modverificationnode(senseid=senseid,
                            vtype=profile,
                            analang=self.analang,
                            add=add,rms=[rm],
                            addifrmd=True,write=False)
        self.db.write() #once done iterating over senseids
    def __init__(self, parent):
        parent.settings.makeeverythingok()
        """I need some way to control for ftype"""
        """I need to think through when I would work with one ftype, and not
        another, or when I would want to work with one, then modify the other
        (e.g., lx)"""
        """sorting on individual whole forms (e.g., lc, pl, imp) should happen
        in tone, but maybe not for C, V, and CV. Or is there a context where we
        would expect (or find anyway) that the analyzable (!) plural/imp form
        doesn't have the same vowels/consonants as the citation form? Maybe we should
        plan for this, and have a 'Yes, this is OK, change them both' button
        Maybe make that button a user option, so it doesn't have to be there if
        not desired."""
        self.invariablesegmentalroots=True #otherwise, ask, or else just check each
        self.params.ftype('lc') #current default
        self.cvt=self.params.cvt()
        #for testing only!!
        # if self.settings.pluralname:
        #     self.params.ftype(self.settings.pluralname)
        # if self.settings.imperativename:
        # self.params.ftype(self.imperativename)
        self.checktypename={'T':'frame',
                        'C':'check',
                        'V':'check',
                        'CV':'check',
                        }
        self.analang=self.settings.params.analang()
class Sound(object):
    """This holds all the Sound methods, mostly for playing."""
    def donewpyaudio(self):
        try:
            self.pyaudio.terminate()
        except:
            log.info("Apparently self.pyaudio doesn't exist, or isn't initialized.")
    def pyaudiocheck(self):
        try:
            self.pyaudio.pa.get_format_from_width(1) #just check if its OK
        except:
            self.pyaudio=sound.AudioInterface()
    def getsoundcardindex(self,event=None):
        log.info("Asking for input sound card...")
        window=ui.Window(self.frame, title=_('Select Input Sound Card'))
        ui.Label(window.frame, text=_('What sound card do you '
                                    'want to record sound with with?')
                ).grid(column=0, row=0)
        l=list()
        for card in self.soundsettings.cards['in']:
            name=self.soundsettings.cards['dict'][card]
            l+=[(card, name)]
        buttonFrame1=ui.ButtonFrame(window.frame,
                                    optionlist=l,
                                    command=self.settings.setsoundcardindex,
                                    window=window,
                                    column=0, row=1
                                    )
    def getsoundcardoutindex(self,event=None):
        log.info("Asking for output sound card...")
        window=ui.Window(self.frame, title=_('Select Output Sound Card'))
        ui.Label(window.frame, text=_('What sound card do you '
                                    'want to play sound with?')
                ).grid(column=0, row=0)
        l=list()
        for card in self.soundsettings.cards['out']:
            name=self.soundsettings.cards['dict'][card]
            l+=[(card, name)]
        buttonFrame1=ui.ButtonFrame(window.frame,
                                    optionlist=l,
                                    command=self.settings.setsoundcardoutindex,
                                    window=window,
                                    column=0, row=1
                                    )
    def getsoundformat(self,event=None):
        log.info("Asking for audio format...")
        window=ui.Window(self.frame, title=_('Select Audio Format'))
        ui.Label(window.frame, text=_('What audio format do you '
                                    'want to work with?')
                ).grid(column=0, row=0)
        l=list()
        ss=self.soundsettings
        for sf in ss.cards['in'][ss.audio_card_in][ss.fs]:
            name=ss.hypothetical['sample_formats'][sf]
            l+=[(sf, name)]
        buttonFrame1=ui.ButtonFrame(window.frame,
                                    optionlist=l,
                                    command=self.settings.setsoundformat,
                                    window=window,
                                    column=0, row=1
                                    )
    def getsoundhz(self,event=None):
        log.info("Asking for sampling frequency...")
        window=ui.Window(self.frame, title=_('Select Sampling Frequency'))
        ui.Label(window.frame, text=_('What sampling frequency you '
                                    'want to work with?')
                ).grid(column=0, row=0)
        l=list()
        ss=self.soundsettings
        for fs in ss.cards['in'][ss.audio_card_in]:
            name=ss.hypothetical['fss'][fs]
            l+=[(fs, name)]
        buttonFrame1=ui.ButtonFrame(window.frame,
                                    optionlist=l,
                                    command=self.settings.setsoundhz,
                                    window=window,
                                    column=0, row=1
                                    )
    def makesoundsettings(self):
        if not hasattr(self.settings,'soundsettings'):
            self.pyaudiocheck() #in case self.pyaudio isn't there yet
            self.settings.soundsettings=sound.SoundSettings(self.pyaudio)
    def loadsoundsettings(self):
        self.makesoundsettings()
        self.settings.loadsettingsfile(setting='soundsettings')
    def soundcheckrefreshdone(self):
        self.settings.storesettingsfile(setting='soundsettings')
        self.soundsettingswindow.destroy()
    def quittask(self):
        self.soundsettingswindow.destroy()
        self.taskchooser.gettask()
        self.on_quit()
    def soundcheckrefresh(self,dict=None):
        dictnow={
                'audio_card_in':self.soundsettings.audio_card_in,
                'fs':self.soundsettings.fs,
                'sample_format': self.soundsettings.sample_format,
                'audio_card_out': self.soundsettings.audio_card_out
                }
        """Call this just once. If nothing changed, wait; if changes, run,
        then run again."""
        if self.soundsettingswindow.exitFlag.istrue():
            return
        if dict == dictnow:
            self.settings.setrefreshdelay()
            self.parent.after(self.settings.refreshdelay,
                                self.soundcheckrefresh,
                                dictnow)
            return
        self.soundsettingswindow.resetframe()
        self.soundsettingswindow.scroll=ui.ScrollingFrame(
                                                self.soundsettingswindow.frame,
                                                row=0,column=0)
        self.soundsettingswindow.content=self.soundsettingswindow.scroll.content
        row=0
        ui.Label(self.soundsettingswindow.content, font='title',
                text=_("Current Sound Card Settings"),
                row=row,column=0)
        row+=1
        ui.Label(self.soundsettingswindow.content, #font='title',
                text=_("(click any to change)"),
                row=row,column=0)
        row+=1
        ss=self.soundsettings
        ss.check() #make defaults if not valid options
        for varname, dict, cmd in [
            ('audio_card_in', ss.cards['dict'], self.getsoundcardindex),
            ('fs',ss.hypothetical['fss'], self.getsoundhz),
            ('sample_format', ss.hypothetical['sample_formats'],
                                                         self.getsoundformat),
            ('audio_card_out', ss.cards['dict'], self.getsoundcardoutindex),
                                                    ]:
            text=_("Change")
            var=getattr(ss,varname)
            log.debug("{} in {}".format(var,dict))
            l=dict[var]
            if cmd == self.getsoundcardindex:
                l=_("Microphone: ‘{}’").format(l)
            if cmd == self.getsoundcardoutindex:
                l=_("Speakers: ‘{}’").format(l)
            l=ui.Label(self.soundsettingswindow.content,text=l,
                    row=row,column=0)
            l.bind('<ButtonRelease>',cmd) #getattr(self,str(cmd)))
            row+=1
        br=RecordButtonFrame(self.soundsettingswindow.content,self,test=True)
        br.grid(row=row,column=0)
        row+=1
        # l=_("You may need to change your microphone "
        #     "\nand/or speaker sound card to get the "
        #     "\nsampling and format you want.")
        # ui.Label(self.soundsettingswindow.content,
        #         text=l).grid(row=row,column=0)
        # row+=1
        l=_("Plug in your microphone, and make sure ‘record’ and ‘play’ work "
            "well here, before recording real data!")
        caveat=ui.Label(self.soundsettingswindow.content,
                text=l,font='read',
                row=row,column=0)
        caveat.wrap()
        row+=1
        # l=_("See also note in documentation about verifying these "
        #     "recordings in an external application, such as Praat.")
        # caveat2=ui.Label(self.soundsettingswindow.content,
        #         text=l,font='instructions',
        #         row=row,column=0)
        # caveat2.wrap()
        # row+=1
        play=_("Play")
        l=_("If Praat is installed in your OS path, right click on ‘{}’ above "
            "to open in Praat.".format(play))
        caveat3=ui.Label(self.soundsettingswindow.content,
                text=l,font='default',
                row=row,column=0)
        caveat3.wrap()
        row+=1
        bd=ui.Button(self.soundsettingswindow.content,
                    text=_("Done"),
                    cmd=self.soundcheckrefreshdone,
                    # anchor='c',
                    row=row,column=0,
                    sticky=''
                    )
        bd=ui.Button(self.soundsettingswindow.content,
                    text=_("Quit Task"),
                    # cmd=program['root'].on_quit,
                    cmd=self.quittask,
                    # anchor='c',
                    row=row,column=1
                    )
        self.soundcheckrefresh(dictnow)
    def soundsettingscheck(self):
        if not hasattr(self.settings,'soundsettings'):
            self.loadsoundsettings()
    def missingsoundattr(self):
        log.info(dir(self.soundsettings))
        ss=self.soundsettings
        for s in ['fs', 'sample_format',
                    'audio_card_in',
                    'audio_card_out']:
            if hasattr(self.soundsettings,s):
                if s+'s' in ss.hypothetical and (getattr(self.soundsettings,s)
                                                not in ss.hypothetical[s+'s']):
                    log.info("Sound setting {} invalid; asking again".format(s))
                    return True
                elif 'audio_card' in s and (getattr(self.soundsettings,s)
                                                    not in ss.cards['dict']):
                    log.info("Sound setting {} invalid; asking again".format(s))
                    return True
            else:
                log.info("Missing sound setting {}; asking again".format(s))
                return True
        self.settings.soundsettingsok=True
    def soundcheck(self):
        #Set the parameters of what could be
        self.pyaudiocheck()
        self.soundsettingscheck()
        self.soundsettings=self.settings.soundsettings
        self.soundsettingswindow=ui.Window(self.frame, exit=False,
                                title=_('Select Sound Card Settings'))
        self.soundsettingswindow.protocol("WM_DELETE_WINDOW", self.quittask)
        self.soundcheckrefresh()
        self.soundsettingswindow.wait_window(self.soundsettingswindow)
        if not self.exitFlag.istrue() and self.missingsoundattr():
            self.soundcheck()
            return
        self.donewpyaudio()
        if not self.exitFlag.istrue() and self.soundsettingswindow.winfo_exists():
            self.soundsettingswindow.destroy()
    def makelabelsnrecordingbuttons(self,parent,sense):
        log.info("Making buttons for {} (in {})".format(sense['nodetoshow'],sense))
        framed=self.taskchooser.datadict.getframeddata(sense['nodetoshow'])
        t=framed.formatted(noframe=True)
        for g in sense['glosses']:
            if g:
                t+='\t‘'+g
                if ('plnode' in sense and
                        sense['nodetoshow'] is sense['plnode']):
                    t+=_(" (pl)")
                if ('impnode' in sense and
                        sense['nodetoshow'] is sense['impnode']):
                    t+="!"
                t+='’'
        lxl=ui.Label(parent, text=t)
        lcb=RecordButtonFrame(parent,self,framed)
        lcb.grid(row=sense['row'],column=sense['column'],sticky='w')
        lxl.grid(row=sense['row'],column=sense['column']+1,sticky='w')
    def __init__(self):
        self.soundcheck()
class Record(Sound):
    """This holds all the Sound methods specific for Recording."""
    def showentryformstorecordpage(self):
        #The info we're going for is stored above sense, hence guid.
        if self.runwindow.exitFlag.istrue():
            log.info('no runwindow; quitting!')
            return
        if not self.runwindow.frame.winfo_exists():
            log.info('no runwindow frame; quitting!')
            return
        self.runwindow.resetframe()
        self.runwindow.wait()
        ps=self.slices.ps()
        profile=self.slices.profile()
        count=self.slices.count()
        text=_("Record {} {} Words: click ‘Record’, talk, "
                "and release ({} words)".format(profile,ps,
                                                count))
        log.info(text)
        instr=ui.Label(self.runwindow.frame, anchor='w',text=text)
        instr.grid(row=0,column=0,sticky='w')
        buttonframes=ui.ScrollingFrame(self.runwindow.frame)
        buttonframes.grid(row=1,column=0,sticky='w')
        row=0
        done=list()
        for senseid in self.slices.senseids(ps=ps,profile=profile):
            sense={}
            sense['column']=0
            sense['row']=row
            sense['senseid']=senseid
            sense['guid']=firstoflist(self.db.get('entry',
                                        senseid=senseid).get('guid'))
            if sense['guid'] in done: #only the first of multiple senses
                continue
            else:
                done.append(sense['guid'])
            """These following two have been shifted down a level, and will
            now return a list of form elements, each. Something will need to be
            adjusted here..."""
            sense['lxnode']=firstoflist(self.db.get('lexeme',
                                                guid=sense['guid'],
                                                lang=self.analang).get())
            sense['lcnode']=firstoflist(self.db.get('citation',
                                                guid=sense['guid'],
                                                lang=self.analang).get())
            sense['glosses']=[]
            for lang in self.glosslangs:
                sense['glosses'].append(firstoflist(self.db.glossordefn(
                                                guid=sense['guid'],
                                                glosslang=lang
                                                ),othersOK=True))
            if self.settings.pluralname is not None:
                sense['plnode']=firstoflist(self.db.fieldnode(
                                guid=sense['guid'],
                                lang=self.analang,
                                ftype=self.settings.pluralname)
                                            )
            if self.settings.imperativename is not None:
                sense['impnode']=firstoflist(self.db.fieldnode(
                                guid=sense['guid'],
                                lang=self.analang,
                                ftype=self.settings.imperativename)
                                            )
            if sense['lcnode'] is not None:
                sense['nodetoshow']=sense['lcnode']
            else:
                sense['nodetoshow']=sense['lxnode']
            self.makelabelsnrecordingbuttons(buttonframes.content,sense)
            for node in ['plnode','impnode']:
                if (node in sense) and (sense[node] is not None):
                    sense['column']+=2
                    sense['nodetoshow']=sense[node]
                    self.makelabelsnrecordingbuttons(buttonframes.content,
                                                    sense)
            row+=1
        self.runwindow.waitdone()
        self.runwindow.wait_window(self.runwindow.frame)
    def showentryformstorecord(self,justone=False):
        # Save these values before iterating over them
        #Convert to iterate over local variables
        self.getrunwindow()
        if justone:
            self.showentryformstorecordpage()
        else:
            #store for later
            ps=self.slices.ps()
            prifile=self.slices.profile()
            for psprofile in self.slices.valid(): #self.profilecountsValid:
                if self.runwindow.exitFlag.istrue():
                    return 1
                self.slices.ps(psprofile[1])
                self.slices.profile(psprofile[0])
                nextb=ui.Button(self.runwindow,text=_("Next Group"),
                                        cmd=self.runwindow.resetframe) # .frame.destroy
                nextb.grid(row=0,column=1,sticky='ne')
                self.showentryformstorecordpage()
            #return to initial
            self.slices.ps(ps)
            self.slices.profile(profile)
        self.donewpyaudio()
    def showsenseswithexamplestorecord(self,senses=None,progress=None,skip=False):
        def setskip(event):
            self.runwindow.frame.skip=True
            entryframe.destroy()
        self.getrunwindow()
        if self.exitFlag.istrue() or self.runwindow.exitFlag.istrue():
            return
        log.debug("Working with skip: {}".format(skip))
        if skip == 'skip':
            self.runwindow.frame.skip=True
        else:
            self.runwindow.frame.skip=skip
        text=_("Words and phrases to record: click ‘Record’, talk, and release")
        instr=ui.Label(self.runwindow.frame, anchor='w',text=text)
        instr.grid(row=0,column=0,sticky='w',columnspan=2)
        if (self.settings.entriestoshow is None) and (senses is None):
            ui.Label(self.runwindow.frame, anchor='w',
                    text=_("Sorry, there are no entries to show!")).grid(row=1,
                                    column=0,sticky='w')
            return
        if self.runwindow.frame.skip == False:
            skipf=ui.Frame(self.runwindow.frame)
            skipb=ui.Button(skipf,
                        text=rx.linebreakwords(_("Skip to next undone")),
                        cmd=skipf.destroy)
            skipf.grid(row=1,column=1,sticky='w')
            skipb.grid(row=0,column=0,sticky='w')
            skipb.bind('<ButtonRelease>', setskip)
        if senses is None:
            senses=self.settings.entriestoshow
        for senseid in senses:
            log.debug("Working on {} with skip: {}".format(senseid,
                                                    self.runwindow.frame.skip))
            examples=self.db.get('example',senseid=senseid).get()
            if examples == []:
                log.debug(_("No examples! Add some, then come back."))
                continue
            if ((self.runwindow.frame.skip == True) and
                (lift.atleastoneexamplehaslangformmissing(
                                                    examples,
                                                    self.settings.audiolang) == False)):
                continue
            row=0
            if self.runwindow.exitFlag.istrue():
                return 1
            entryframe=ui.Frame(self.runwindow.frame)
            entryframe.grid(row=1,column=0)
            if progress is not None:
                progressl=ui.Label(self.runwindow.frame, anchor='e',
                    font='small',
                    text="({} {}/{})".format(*progress)
                    )
                progressl.grid(row=0,column=2,sticky='ne')
            """This is the title for each page: isolation form and glosses."""
            titleframed=self.taskchooser.datadict.getframeddata(senseid,check=None)
            if not titleframed or titleframed.forms[self.analang] is None:
                entryframe.destroy() #is this ever needed?
                continue
            text=titleframed.formatted(noframe=True,showtonegroup=False)
            ui.Label(entryframe, anchor='w', font='read',
                    text=text).grid(row=row,
                                    column=0,sticky='w')
            """Then get each sorted example"""
            self.runwindow.frame.scroll=ui.ScrollingFrame(entryframe)
            self.runwindow.frame.scroll.grid(row=1,column=0,sticky='w')
            examplesframe=ui.Frame(self.runwindow.frame.scroll.content)
            examplesframe.grid(row=0,column=0,sticky='w')
            examples.reverse()
            for example in examples:
                if (skip == True and
                    lift.examplehaslangform(example,self.settings.audiolang) == True):
                    continue
                """These should already be framed!"""
                framed=self.taskchooser.datadict.getframeddata(example,senseid=senseid)
                if (not framed or
                        framed.framed == 'NA' or
                        not framed.forms[self.analang]):
                    #Don't show the whole dictionary of frames here:
                    log.info("Not showing example with framed {}".format(
                            {i:framed.__dict__[i] for i in framed.__dict__
                                                        if i!='parent'}))
                    continue
                row+=1
                """If I end up pulling from example nodes elsewhere, I should
                probably make this a function, like getframeddata"""
                text=framed.formatted()
                if not framed:
                    exit()
                rb=RecordButtonFrame(examplesframe,self,framed)
                rb.grid(row=row,column=0,sticky='w')
                ui.Label(examplesframe, anchor='w',text=text
                                        ).grid(row=row, column=1, sticky='w')
            row+=1
            d=ui.Button(examplesframe, text=_("Done/Next"),command=entryframe.destroy)
            d.grid(row=row,column=0)
            self.runwindow.waitdone()
            examplesframe.wait_window(entryframe)
            if self.runwindow.exitFlag.istrue():
                return 1
            if self.runwindow.frame.skip == True:
                return 'skip'
    def showtonegroupexs(self):
        def next():
            self.status.nextprofile()
            self.runwindow.destroy()
            self.showtonegroupexs()
        if (not(hasattr(self,'examplespergrouptorecord')) or
            (type(self.examplespergrouptorecord) is not int)):
            self.examplespergrouptorecord=100
            self.settings.storesettingsfile()
        analysis=self.makeanalysis()
        analysis.donoUFanalysis()
        torecord=analysis.senseidsbygroup
        ntorecord=len(torecord) #number of groups
        nexs=len([k for i in torecord for j in torecord[i] for k in j])
        nslice=self.slices.count()
        log.info("Found {} analyzed of {} examples in slice".format(nexs,nslice))
        skip=False
        if ntorecord == 0:
            log.error(_("How did we get no UR tone groups? {}-{}"
                    "\nHave you run the tone report recently?"
                    "\nDoing that for you now...").format(
                            self.slices.profile(),
                            self.slices.ps()
                                                        ))
            analysis.do()
            self.showtonegroupexs()
            return
        batch={}
        for i in range(self.examplespergrouptorecord):
            batch[i]=[]
            for ufgroup in torecord:
                print(i,len(torecord[ufgroup]),ufgroup,torecord[ufgroup])
                if len(torecord[ufgroup]) > i: #no done piles.
                    senseid=[torecord[ufgroup][i]] #list of one
                else:
                    print("Not enough examples, moving on:",i,ufgroup)
                    continue
                log.info(_('Giving user the number {} example from tone '
                        'group {}'.format(i,ufgroup)))
                exited=self.showsenseswithexamplestorecord(senseid,
                            (ufgroup, i+1, self.examplespergrouptorecord),
                            skip=skip)
                if exited == 'skip':
                    skip=True
                if exited == True:
                    return
        if not (self.runwindow.exitFlag.istrue() or self.exitFlag.istrue()):
            self.runwindow.waitdone()
            self.runwindow.resetframe()
            ui.Label(self.runwindow.frame, anchor='w',font='read',
            text=_("All done! Sort some more words, and come back.")
            ).grid(row=0,column=0,sticky='w')
            ui.Button(self.runwindow.frame,
                    text=_("Continue to next syllable profile"),
                    command=next).grid(row=1,column=0)
        self.donewpyaudio()
    def record(self):
        self.updatesortingstatus() #is this needed? This is the first fn on button click
        if self.params.cvt() == 'T':
            self.showtonegroupexs()
        else:
            self.showentryformstorecord()
    def __init__(self):
        Sound.__init__(self)
class Report(object):
    def consultantcheck(self):
        self.settings.reloadstatusdata()
        self.bylocation=False
        self.tonegroupreportcomprehensive()
        self.bylocation=True
        self.tonegroupreportcomprehensive()
    def tonegroupreportcomprehensive(self,**kwargs):
        pss=self.slices.pss()[:self.settings.maxpss]
        d={}
        for ps in pss:
            d[ps]=self.slices.profiles(ps=ps)[:self.settings.maxprofiles]
        log.info("Starting comprehensive reports for {}".format(d))
        kwargs['usegui']=False
        for ps in pss:
            for profile in d[ps]:
                kwargs={'ps': ps, 'profile': profile}
                # self.tonegroupreport(**kwargs) #ps=ps,profile=profile)
                self.tonegroupreport(**kwargs) #ps=ps,profile=profile)
            """Not working:"""
            # with multiprocessing.Pool(processes=4) as pool:
            #     pool.map(self.tonegroupreport,[
            #             {'ps':ps,'profile':p,'usegui':False} for p in d[ps]])
    def tonegroupreportmulti(self,**kwargs):
        # threading.Thread(target=self.tonegroupreport,kwargs=kwargs).start()
        kwargs['usegui']=False
        t=multiprocessing.Process(target=self.tonegroupreport,kwargs=kwargs)
        t.start()
    def tonegroupreport(self,usegui=True,**kwargs):
        """This should iterate over at least some profiles; top 2-3?
        those with 2-4 verified frames? Selectable with radio buttons?"""
        #default=True redoes the UF analysis (removing any joining/renaming)
        ftype=kwargs.get('ftype',self.params.ftype())
        def examplestoXLP(examples,parent,senseid):
            counts['senses']+=1
            for example in examples:
                framed=self.taskchooser.datadict.getframeddata(example,senseid)
                # skip empty examples:
                if not hasattr(framed,'forms') or self.analang not in framed.forms:
                    continue
                framed.gettonegroup() #wanted for id, not for display
                for lang in [self.analang]+self.glosslangs:
                    if lang in framed.forms and framed.forms[lang]: #If all None, don't.
                        counts['examples']+=1
                        if self.settings.audiolang in framed.forms:
                            counts['audio']+=1
                        self.framedtoXLP(framed,parent=parent,ftype=ftype,
                                                        listword=True,
                                                        showgroups=showgroups)
                        break #do it on first present lang, and do next ex
        a=self.status.last('analysis',**kwargs)
        s=self.status.last('sort',**kwargs)
        j=self.status.last('join',**kwargs)
        if a and s:
            analysisOK=a>s
        elif a:
            analysisOK=True # b/c analysis would be more recent than last sorting
        else:
            analysisOK=False # w/o info, trigger reanalysis
        self.datadict.refresh() #get the most recent data
        silent=kwargs.get('silent',False)
        default=kwargs.get('default',True)
        ps=kwargs.get('ps',self.slices.ps())
        profile=kwargs.get('profile',self.slices.profile())
        checks=self.status.checks(wsorted=True,**kwargs)
        if analysisOK and j and j > a:
            showgroups=True #show groups on all non-default reports
        else:
            showgroups=False #show groups on all non-default reports
        if not checks:
            if 'profile' in kwargs:
                log.error("{} {} came up with no checks.".format(ps,profile))
                return
            self.getprofile(wsorted=True)
        log.info("Starting report {} {} at {}; last sort at {} (since={})..."
                "".format(ps,profile,a,s,analysisOK))
        self.settings.storesettingsfile()
        waitmsg=_("{} {} Tone Report in Process").format(ps,profile)
        if usegui:
            resultswindow=ResultWindow(self.parent,msg=waitmsg)
        bits=[str(self.reportbasefilename),
                rx.urlok(ps),
                rx.urlok(profile),
                "ToneReport"]
        if not default:
            bits.append('mod')
        self.tonereportfile='_'.join(bits)+".txt"
        checks=self.status.checks(wsorted=True,**kwargs)
        if not checks:
            error=_("Hey, sort some morphemes in at least one frame before "
                        "trying to make a tone report!")
            log.error(error)
            if usegui:
                resultswindow.waitdone()
                resultswindow.destroy()
                ErrorNotice(error)
            return
        start_time=time.time()
        counts={'senses':0,'examples':0, 'audio':0}
        analysis=self.makeanalysis(**kwargs)
        if analysisOK:
            analysis.donoUFanalysis() #based on (sense) UF fields
        else:
            analysis.do() #full analysis from scratch, output to UF fields
        """These are from LIFT, ordered by similarity for the report."""
        if not analysis.orderedchecks or not analysis.orderedUFs:
            log.error("Problem with checks: {} (in {} {})."
                    "".format(checks,ps,profile))
            log.error("valuesbygroupcheck: {}, valuesbycheckgroup: {}"
                        "".format(analysis.valuesbygroupcheck,
                                    analysis.valuesbycheckgroup))
            log.error("Ordered checks is {}, ordered UFs: {}"
                    "".format(analysis.orderedchecks,
                            analysis.orderedUFs))
            log.error("comparisonUFs: {}, comparisonchecks: {}"
                    "".format(analysis.comparisonUFs,
                            analysis.comparisonchecks))
        grouplist=analysis.orderedUFs
        checks=analysis.orderedchecks
        r = open(self.tonereportfile, "w", encoding='utf-8')
        title=_("Tone Report")
        if usegui:
            resultswindow.scroll=ui.ScrollingFrame(resultswindow.frame)
            resultswindow.scroll.grid(row=0,column=0)
            window=resultswindow.scroll.content
            window.row=0
        else:
            window=None
        xlpr=self.xlpstart(reporttype='Tone',
                            ps=ps,
                            profile=profile,
                            # bylocation=self.bylocation,
                            default=default
                            )
        s1=xlp.Section(xlpr,title='Introduction')
        text=_("This report follows an analysis of sortings of {} morphemes "
        "(roots or affixes) across the following frames: {}. {} stores these "
        "sortings in lift examples, which are output here, with any glossing "
        "and sound file links found in each lift sense example. "
        "Each group in "
        "this report is distinct from the others, in terms of its grouping "
        "across the multiple frames used. Sound files should be available "
        "through links, if the audio directory with those files is in the same "
        "directory as this file.".format(ps,checks,program['name']))
        p1=xlp.Paragraph(s1,text=text)
        text=_("As a warning to the analyst who may not understand the "
        "implications of this *automated analysis*, you may have too few "
        "groupings here, particularly if you have sorted on fewer frames than "
        "necessary to distinguish all your underlying tone melodies. On the "
        "other hand, if your team has been overly precise, or if your database "
        "contains bad information (sorting information which is arbitrary or "
        "otherwise inappropriate for the language), then you likely have more "
        "groups here than you have underlying tone melodies. However, if you "
        "have avoided each of these two errors, this report should contain a "
        "decent draft of your underlying tone melody groups. It does not "
        "pretend to tell you what the values of those groups are, nor how "
        "those groups interact with morphology in interesting ways (hopefully "
        "you can do each of these better than a computer could).")
        p2=xlp.Paragraph(s1,text=text)
        def output(window,r,text):
            r.write(text+'\n')
            if usegui:
                ui.Label(window,text=text,
                        font=window.theme.fonts['report'],
                        row=window.row,column=0, sticky="w"
                        )
                window.row+=1
        t=_("Summary of Frames by Draft Underlying Melody")
        m=7 #only this many columns in a table
        # Don't bother with lanscape if we're splitting the table in any case.
        if m >= len(checks) > 6:
            landscape=True
        else:
            landscape=False
        s1s=xlp.Section(xlpr,t,landscape=landscape)
        caption=' '.join([ps,profile])
        ptext=_("The following table shows correspondences across sortings by "
                "tone frames, with a row for each unique pairing. ")
        if default == True:
            ptext+=_("This is a default report, where {} "
                "intentionally splits these groups, so you can see wherever "
                "differences lie, even if those differences are likely "
                "meaningless (e.g., 'NA' means the user skipped sorting those "
                "words in that frame, but this will still distinguish one "
                "group from another). To help the qualified analyst navigate "
                "such a large selection of small slices of the data, the data "
                "is sorted (both here and in the section ordering) by "
                "similarity of groups. That similarity is structured, and "
                "it is provided here, so you can see the analysis of group "
                "relationships for yourself: {}. "
                "And here are the structured similarity relationships for the "
                "Frames: {}"
                "".format(program['name'],
                        str(analysis.comparisonUFs),
                        str(analysis.comparisonchecks)))
        else:
            ptext+=_("This is a non-default report, where a user has changed "
            "the default (hyper-split) groups created by {}.".format(
                                                        program['name']))
        p0=xlp.Paragraph(s1s,text=ptext)
        analysis.orderedchecks=list(analysis.valuesbycheckgroup)
        for slice in range(int(len(analysis.orderedchecks)/m)+1):
            locslice=analysis.orderedchecks[slice*m:(slice+1)*m]
            if len(locslice) >0:
                self.buildXLPtable(s1s,caption+str(slice),
                        yterms=grouplist,
                        xterms=locslice,
                        values=lambda x,y:nn(unlist(
                analysis.valuesbygroupcheck[y][x],ignore=[None, 'NA']
                                            )),
                        ycounts=lambda x:len(analysis.senseidsbygroup[x]),
                        xcounts=lambda y:len(analysis.valuesbycheck[y]))
        #Can I break this for multithreading?
        for group in grouplist: #These already include ps-profile
            log.info("building report for {} ({}/{}, n={})".format(group,
                grouplist.index(group)+1,len(grouplist),
                len(analysis.senseidsbygroup[group])
                ))
            sectitle=_('\n{}'.format(str(group)))
            s1=xlp.Section(xlpr,title=sectitle)
            output(window,r,sectitle)
            l=list()
            for x in analysis.valuesbygroupcheck[group]:
                l.append("{}: {}".format(x,', '.join(
                    [i for i in analysis.valuesbygroupcheck[group][x]
                                                            if i is not None]
                        )))
            if not l:
                l=[_('<no frames with a sort value>')]
            text=_('Values by frame: {}'.format('\t'.join(l)))
            log.info(text)
            p1=xlp.Paragraph(s1,text)
            output(window,r,text)
            if self.bylocation:
                textout=list()
                #This is better than checks, just whats there for this group
                for check in analysis.valuesbygroupcheck[group]:
                    id=rx.id('x'+sectitle+check)
                    headtext='{}: {}'.format(check,', '.join(
                            [i for i in
                            analysis.valuesbygroupcheck[group][check]
                            if i is not None]
                                            ))
                    e1=xlp.Example(s1,id,heading=headtext)
                    for senseid in analysis.senseidsbygroup[group]:
                        #This is for window/text output only, not in XLP file
                        framed=self.taskchooser.datadict.getframeddata(senseid,check=None)
                        text=framed.formatted(noframe=True,showtonegroup=False)
                        #This is put in XLP file:
                        examples=self.db.get('example',location=check,
                                                senseid=senseid).get()
                        examplestoXLP(examples,e1,senseid)
                        if text not in textout:
                            output(window,r,text)
                            textout.append(text)
                    if not e1.node.find('listWord'):
                        s1.node.remove(e1.node) #Don't show examples w/o data
            else:
                for senseid in analysis.senseidsbygroup[group]:
                    #This is for window/text output only, not in XLP file
                    framed=self.taskchooser.datadict.getframeddata(senseid,check=None)
                    if not framed:
                        continue
                    text=framed.formatted(noframe=True, showtonegroup=False)
                    #This is put in XLP file:
                    examples=self.db.get('example',senseid=senseid).get()
                    log.log(2,"{} examples found: {}".format(len(examples),
                                                                    examples))
                    if examples != []:
                        id=self.idXLP(framed)+'_examples'
                        headtext=text.replace('\t',' ')
                        e1=xlp.Example(s1,id,heading=headtext)
                        log.info("Asking for the following {} examples from id "
                                "{}: {}".format(len(examples),senseid,examples))
                        examplestoXLP(examples,e1,senseid)
                    else:
                        self.framedtoXLP(framed,parent=s1,ftype=ftype,
                                                        showgroups=showgroups)
                    output(window,r,text)
        sectitle=_('\nData Summary')
        s2=xlp.Section(xlpr,title=sectitle)
        try:
            eps='{:.2}'.format(float(counts['examples']/counts['senses']))
        except ZeroDivisionError:
            eps="Div/0"
        try:
            audiopercent='{:.2%}'.format(float(counts['audio']/counts['examples']))
        except ZeroDivisionError:
            audiopercent="Div/0%"
        ptext=_("This report contains {} senses, {} examples, and "
                "{} sound files. That is an average of {} examples/sense, and "
                "{} of examples with sound files."
                "").format(counts['senses'],counts['examples'],counts['audio'],
                            eps,audiopercent)
        ps2=xlp.Paragraph(s2,text=ptext)
        xlpr.close(me=me)
        text=_("Finished in {} seconds.").format(str(time.time() -start_time))
        output(window,r,text)
        text=_("(Report is also available at ({})").format(self.tonereportfile)
        output(window,r,text)
        r.close()
        if usegui:
            if me:
                resultswindow.on_quit()
            else:
                resultswindow.waitdone()
        self.status.last('report',update=True)
    def makeresultsframe(self):
        if hasattr(self,'runwindow') and self.runwindow.winfo_exists:
            self.results = ui.Frame(self.runwindow.frame,width=800)
            self.results.grid(row=0, column=0)
        else:
            log.error("Tried to get a results frame without a runwindow!")
    def getresults(self,**kwargs):
        self.getrunwindow()
        self.makeresultsframe()
        cvt=kwargs.get('cvt',self.params.cvt())
        ps=kwargs.get('ps',self.slices.ps())
        profile=kwargs.get('profile',self.slices.profile())
        check=kwargs.get('check',self.params.check())
        self.adhocreportfileXLP=''.join([str(self.reportbasefilename)
                                        ,'_',str(ps)
                                        ,'-',str(profile)
                                        ,'_',str(check)
                                        ,'_ReportXLP.xml'])
        self.checkcounts={}
        xlpr=self.xlpstart()
        """"Do I need this?"""
        self.results.grid(column=0,
                        row=self.runwindow.frame.grid_info()['row']+1,
                        columnspan=5,
                        sticky=(ui.N, ui.S, ui.E, ui.W))
        print(_("Getting results of Search request"))
        c1 = "Any"
        c2 = "Any"
        self.results.row=0
        """nn() here keeps None and {} from the output, takes one string,
        list, or tuple."""
        text=(_("{} roots of form {} by {}".format(ps,profile,check)))
        ui.Label(self.results, text=text).grid(column=0, row=self.results.row)
        self.runwindow.wait()
        si=xlp.Section(xlpr,text)
        self.results.scroll=ui.ScrollingFrame(self.results)
        self.results.scroll.grid(column=0, row=1)
        if 'x' in check and cvt != 'CV': #CV has no C=V...
            self.docheckreport(si,check=rx.sub('x','=',check, count=1))
        self.docheckreport(si) #this needs parent
        if 'x' in check:
            self.coocurrencetables(xlpr)
        # These lines get all senseids, to test that we're not losing any, below
        # This is the first of three blocks to uncomment (on line, then logs)
        # self.regexCV=profile
        # self.regex=rx.fromCV(self,lang=self.analang,
        #                     word=True, compile=True)
        # rxsenseidsinslice=self.senseidformsbyregex(self.regex)
        # senseidsinslice=self.slices.senseids()
        # log.info("nrxsenseidsinslice: {}".format(len(rxsenseidsinslice)))
        # log.info("nsenseidsinslice: {}".format(len(senseidsinslice)))
        # senseidsnotsearchable=set(senseidsinslice)-set(rxsenseidsinslice)
        # log.info("senseidsnotsearchable: {}".format(len(senseidsnotsearchable)))
        # log.info("senseidsnotsearchable: {}".format(senseidsnotsearchable))
        xlpr.close(me=me)
        self.runwindow.waitdone()
        # Report on testing blocks above
        # log.info("senseids remaining (rx): ({}) {}".format(
        #                                                 len(rxsenseidsinslice),
        #                                                 rxsenseidsinslice))
        # log.info("senseids remaining: ({}) {}".format(len(senseidsinslice),
        #                                                     senseidsinslice))
        n=0
        for ps in self.checkcounts:
            for profile in self.checkcounts[ps]:
                for check in self.checkcounts[ps][profile]:
                    for group in self.checkcounts[ps][profile][check]:
                        i=self.checkcounts[ps][profile][check][group]
                        if isinstance(i,int):
                            n+=i
                        else:
                            for g2 in i:
                                i2=i[g2]
                                if isinstance(i2,int):
                                    n+=i2
                                else:
                                    log.info("Not sure what I'm dealing with! "
                                            "({})".format(i2))
        if not n: #i.e., nothing was found above
            text=_("No results for {}/{} ({})!").format(profile,check,ps)
            log.info(text)
            ui.Label(self.results, text=text, column=0, row=self.results.row+1)
            return
    def buildXLPtable(self,parent,caption,yterms,xterms,values,ycounts=None,xcounts=None):
        #values should be a (lambda?) function that depends on x and y terms
        #ycounts should be a lambda function that depends on yterms
        log.info("Making table with caption {}".format(caption))
        t=xlp.Table(parent,caption)
        rows=list(yterms)
        nrows=len(rows)
        cols=list(xterms)
        ncols=len(cols)
        if nrows == 0:
            return
        if ncols == 0:
            return
        for row in ['header']+list(range(nrows)):
            if row != 'header':
                row=rows[row]
            r=xlp.Row(t)
            for col in ['header']+list(range(ncols)):
                log.log(4,"row: {}; col: {}".format(row,col))
                if col != 'header':
                    col=cols[col]
                log.log(4,"row: {}; col: {}".format(row,col))
                if row == 'header' and col == 'header':
                    log.log(2,"header corner")
                    cell=xlp.Cell(r,content='',header=True)
                elif row == 'header':
                    log.log(2,"header row")
                    if xcounts is not None:
                        hxcontents='{} ({})'.format(col,xcounts(col))
                    else:
                        hxcontents='{}'.format(col)
                    cell=xlp.Cell(r,content=rx.linebreakwords(hxcontents),
                                header=True,
                                linebreakwords=True)
                elif col == 'header':
                    log.log(2,"header column")
                    if ycounts is not None:
                        hycontents='{} ({})'.format(row,ycounts(row))
                    else:
                        hycontents='{}'.format(row)
                    cell=xlp.Cell(r,content=hycontents,
                                header=True)
                else:
                    log.log(2,"Not a header")
                    try:
                        value=values(col,row)
                        log.log(2,"value ({},{}):{}".format(col,row,
                                                        values(col,row)))
                    except KeyError:
                        log.info("Apparently no value for col:{}, row:{}"
                                "".format(col,row))
                        value=''
                    finally: # we need each cell to be there...
                        cell=xlp.Cell(r,content=value)
    def xlpstart(self,**kwargs):
        ps=kwargs.get('ps',self.slices.ps())
        profile=kwargs.get('profile',self.slices.profile())
        reporttype=kwargs.get('reporttype','adhoc')
        default=kwargs.get('default',True)
        if reporttype == 'Tone':
            if self.bylocation:
                reporttype='Tone-bylocation'
        elif not 'Basic' in reporttype: #We don't want this in the title
            #this is only for adhoc "big button" reports.
            reporttype=str(self.params.check())
        reporttype=' '.join([ps,profile,reporttype])
        bits=[str(self.reportbasefilename),rx.id(reporttype),"ReportXLP"]
        if not default:
            bits.append('mod')
        reportfileXLP='_'.join(bits)+".xml"
        xlpreport=xlp.Report(reportfileXLP,reporttype,
                        self.settings.languagenames[self.analang])
        langsalreadythere=[]
        for lang in set([self.analang]+self.glosslangs)-set([None]):
            xlpreport.addlang({'id':lang,'name': self.settings.languagenames[lang]})
        return xlpreport
    def wordsbypsprofilechecksubcheckp(self,parent,t="NoText!",**kwargs):
        cvt=kwargs.get('cvt',self.params.cvt())
        ps=kwargs.get('ps',self.slices.ps())
        profile=kwargs.get('profile',self.slices.profile())
        check=kwargs.get('check',self.params.check())
        group=kwargs.get('group',self.status.group())
        ftype=kwargs.get('ftype',self.params.ftype())
        xlp.Paragraph(parent,t)
        print(t)
        log.debug(t)
        """possibly iterating over all these parameters, used by buildregex"""
        self.buildregex(cvt=cvt,profile=profile,check=check,group=group)
        log.log(2,"self.regex: {}; self.regexCV: {}".format(self.regex,
                                                        self.regexCV))
        matches=set(self.senseidformsbyregex(self.regex,ps=ps))
        if 'x' not in check and '=' not in check: #only pull from simple reports
            for ncvt in self.ncvts: #for basic reports
                try:    # this removes senses already reported (e.g., in V1=V2)
                    matches-=self.basicreported[ncvt]
                except AttributeError:
                    log.info("Not removing ids from basic reported because it "
                        "isn't there. Hope that's appropriate (e.g., in an "
                        "ad hoc report)")
                except KeyError:
                    log.info("Not removing ncvt {} ids from basic reported; "
                        "hope that's appropriate."
                        "".format(ncvt))
        log.log(2,"{} matches found!: {}".format(len(matches),matches))
        if 'x' not in check:
            try:
                n=self.checkcounts[ps][profile][check][group]=len(matches)
            except:
                try:
                    self.checkcounts[ps][profile][check]={}
                    n=self.checkcounts[ps][profile][check][group]=len(matches)
                except:
                    try:
                        self.checkcounts[ps][profile]={}
                        self.checkcounts[ps][profile][check]={}
                        n=self.checkcounts[ps][profile][check][
                                                            group]=len(matches)
                    except:
                        self.checkcounts[ps]={}
                        self.checkcounts[ps][profile]={}
                        self.checkcounts[ps][profile][check]={}
                        log.info("ps: {}, profile: {}, check: {}, group: {}"
                                "".format(ps,profile,check,group))
                        n=self.checkcounts[ps][profile][check][
                                                            group]=len(matches)
        if 'x' in check or len(check.split('=')) == 2:
            if 'x' in check:
                othergroup=self.groupcomparison
            else: #if len(check.split('=')) == 2:
                """put X=Y data in XxY"""
                othergroup=group
                check=rx.sub('=','x',check, count=1)
            try:
                n=self.checkcounts[ps][profile][check][
                                                group][othergroup]=len(matches)
            except KeyError:
                try:
                    self.checkcounts[ps][profile][check][group]={}
                    n=self.checkcounts[ps][profile][check][
                                                group][othergroup]=len(matches)
                except KeyError:
                    try:
                        self.checkcounts[ps][profile][check]={}
                        self.checkcounts[ps][profile][check][group]={}
                        n=self.checkcounts[ps][profile][check][
                                                group][othergroup]=len(matches)
                    except KeyError:
                        try:
                            self.checkcounts[ps][profile]={}
                            self.checkcounts[ps][profile][check]={}
                            self.checkcounts[ps][profile][check][group]={}
                            n=self.checkcounts[ps][profile][check][
                                                group][othergroup]=len(matches)
                        except KeyError:
                            try:
                                self.checkcounts[ps]={}
                                self.checkcounts[ps][profile]={}
                                self.checkcounts[ps][profile][check]={}
                                self.checkcounts[ps][profile][check][group]={}
                                n=self.checkcounts[ps][profile][check][
                                                group][othergroup]=len(matches)
                            except KeyError:
                                self.checkcounts[ps]={}
                                self.checkcounts[ps][profile]={}
                                self.checkcounts[ps][profile][check]={}
                                self.checkcounts[ps][profile][check][group]={}
                                n=self.checkcounts[ps][profile][check][
                                                group][othergroup]=len(matches)
        if n>0:
            titlebits='x'+ps+profile+check+group
            if 'x' in check:
                titlebits+='x'+othergroup
            id=rx.id(titlebits)
            ex=xlp.Example(parent,id)
            for senseid in matches:
                if 'x' not in check: #This won't add XxY data again.
                    for ncvt in self.ncvts:
                        try:
                            self.basicreported[ncvt].add(senseid)
                        except AttributeError:
                            log.info("Not adding ids to basic reported because "
                                "it isn't there.")
                        except KeyError:
                            self.basicreported[ncvt]=set([senseid])
                framed=self.taskchooser.datadict.getframeddata(senseid)
                self.framedtoXLP(framed,parent=ex,ftype=ftype,listword=True) #showgroups?
                if hasattr(self,'results'): #i.e., showing results in window
                    self.results.row+=1
                    col=0
                    for lang in [self.analang]+self.glosslangs:
                        col+=1
                        if lang in framed.forms and framed.forms[lang]:
                            if type(framed.forms[lang]) is dict:
                                t=framed.forms[lang][ftype]
                            else:
                                t=framed.forms[lang]
                            ui.Label(self.results.scroll.content,
                                    text=t, font='read',
                                    anchor='w',padx=10, row=self.results.row,
                                    column=col,
                                    sticky='w')
    def wordsbypsprofilechecksubcheck(self,parent='NoXLPparent',**kwargs):
        """This function iterates across check and group values
        appropriate for the specified self.type, profile and check
        values (ps is irrelevant here).
        Because two functions called (buildregex and getframeddata) use
        check and group to do their work, they and their
        dependents would need to be changed to fit a new paradigm, if we
        were to change the variable here. So rather, we store the current
        check and group values, then iterate across logically
        possible values (as above), then restore the value."""
        """I need to find a way to limit these tests to appropriate
        profiles..."""
        cvt=kwargs.pop('cvt',self.params.cvt()) #only send on one
        ps=kwargs.get('ps',self.slices.ps())
        profile=kwargs.get('profile',self.slices.profile())
        groups=self.status.groups(cvt=cvt)
        #CV checks depend on profile, too
        checksunordered=self.status.checks(cvt=cvt,profile=profile)
        self.checks=self.orderchecks(checksunordered)
        """check set here"""
        for check in self.checks: #self.checkcodesbyprofile:
            """multithread here"""
            self.docheckreport(parent,check=check,cvt=cvt,**kwargs)
    def orderchecks(self,checklist):
        checks=sorted([i for i in checklist if '=' in i], key=len, reverse=True)
        checks+=sorted([i for i in checklist if '=' not in i
                                                if 'x' not in i], key=len)
        checks+=sorted([i for i in checklist if 'x' in i], key=len)
        return checks
    def docheckreport(self,parent,**kwargs):
        cvt=kwargs.get('cvt',self.params.cvt())
        ps=kwargs.get('ps',self.slices.ps())
        profile=kwargs.get('profile',self.slices.profile())
        check=kwargs.pop('check',self.params.check()) #don't pass this twice!
        groups=self.status.groups(cvt=cvt)
        self.ncvts=rx.split('[=x]',check)
        if 'x' in check:
            log.debug('Hey, I cound a correspondence number!')
            if cvt in ['V','C']:
                groupcomparisons=groups
            elif cvt == 'CV':
                groups=self.status.groups(cvt='C')
                groupcomparisons=self.status.groups(cvt='V')
            else:
                log.error("Sorry, I don't know how to compare cvt: {}"
                                                    "".format(cvt))
            for group in groups:
                for self.groupcomparison in groupcomparisons:
                    if group != self.groupcomparison:
                        t=_("{} {} {}={}-{}".format(ps,profile,
                                            check,group,
                                            self.groupcomparison))
                        self.wordsbypsprofilechecksubcheckp(parent,t,
                                        check=check, group=group,**kwargs)
        elif groups:
            for group in groups:
                t=_("{} {} {}={}".format(ps,profile,check,group))
                self.wordsbypsprofilechecksubcheckp(parent,t,
                                        check=check, group=group,**kwargs)
    def idXLP(self,framed):
        id='x' #string!
        bits=[
            self.params.cvt(),
            self.slices.ps(),
            self.slices.profile(),
            ]
        if hasattr(framed,'check'):
            bits.append(framed.check)
        if hasattr(framed,'tonegroup'):
            bits.append(framed.tonegroup)
        for lang in self.glosslangs:
            if lang in framed.forms and framed.forms[lang] is not None:
                bits+=framed.forms[lang]
        for x in bits:
            if x is not None:
                id+=x
        return rx.id(id) #for either example or listword
    def framedtoXLP(self,framed,parent,ftype,listword=False,showgroups=True):
        """This will likely only work when called by
        wordsbypsprofilechecksubcheck; but is needed because it must return if
        the word is found, leaving wordsbypsprofilechecksubcheck to continue"""
        """parent is an example in the XLP report"""
        id=self.idXLP(framed)
        if listword == True:
            ex=xlp.ListWord(parent,id)
        else:
            exx=xlp.Example(parent,id) #the id goes here...
            ex=xlp.Word(exx) #This doesn't have an id
        if (self.settings.audiolang in framed.forms and
                    ftype in framed.forms[self.settings.audiolang] and
                    framed.forms[self.settings.audiolang][ftype]):
            url=file.getdiredrelURLposix(self.reporttoaudiorelURL,
                                framed.forms[self.settings.audiolang][ftype])
            el=xlp.LinkedData(ex,self.analang,framed.forms[self.analang][ftype],
                                                                    str(url))
        else:
            el=xlp.LangData(ex,self.analang,framed.forms[self.analang][ftype])
        if hasattr(framed,'tonegroup') and showgroups: #joined groups show each
            elt=xlp.LangData(ex,self.analang,framed.tonegroup)
        for lang in self.glosslangs:
            if lang in framed.forms:
                xlp.Gloss(ex,lang,framed.forms[lang])
    def printcountssorted(self):
        #This is only used in the basic report
        log.info("Ranked and numbered syllable profiles, by grammatical category:")
        nTotal=0
        nTotals={}
        for line in self.slices: #profilecounts:
            profile=line[0]
            ps=line[1]
            nTotal+=self.slices[line]
            if ps not in nTotals:
                nTotals[ps]=0
            nTotals[ps]+=self.slices[line]
        print('Profiled data:',nTotal)
        """Pull this?"""
        for ps in self.slices.pss():
            if ps == 'Invalid':
                continue
            log.debug("Part of Speech {}:".format(ps))
            for line in self.slices.valid(ps=ps):
                profile=line[0]
                ps=line[1]
                log.debug("{}: {}".format(profile,self.slices[line]))
            print(ps,"(total):",nTotals[ps])
    def printprofilesbyps(self):
        #This is only used in the basic report
        log.info("Syllable profiles actually in senses, by grammatical category:")
        for ps in self.profilesbysense:
            if ps == 'Invalid':
                continue
            print(ps, self.profilesbysense[ps])
    def basicreport(self):
        """We iterate across these values in this script, so we save current
        values here, and restore them at the end."""
        #Convert to iterate over local variables
        instr=_("The data in this report is given by most restrictive test "
                "first, followed by less restrictive tests (e.g., V1=V2 "
                "before V1 or V2). Additionally, each word only "
                "appears once per segment in a given position, so a word that "
                "occurs in a more restrictive environment will not appear in "
                "the later less restrictive environments. But where multiple "
                "examples of a segment type occur with different values, e.g., "
                "V1≠V2, those words will appear multiple times, e.g., for "
                "both V1=x and V2=y.")
        self.wait(msg=_("Running {}").format(self.tasktitle()))
        self.basicreportfile=''.join([str(self.reportbasefilename)
                                        ,'_',''.join(sorted(self.cvtstodo)[:2])
                                        ,'_BasicReport.txt'])
        xlpr=self.xlpstart(reporttype='Basic '+''.join(self.cvtstodo))
        si=xlp.Section(xlpr,"Introduction")
        p=xlp.Paragraph(si,instr)
        sys.stdout = open(self.basicreportfile, "w", encoding='utf-8')
        print(instr)
        log.info(instr)
        #There is no runwindow here...
        self.basicreported={}
        self.checkcounts={}
        self.printprofilesbyps()
        self.printcountssorted()
        t=_("This report covers the following top two Grammatical categories, "
            "with the top {} syllable profiles in each. "
            "This is of course configurable, but I assume you don't want "
            "everything.".format(self.settings.maxprofiles))
        log.info(t)
        print(t)
        p=xlp.Paragraph(si,t)
        for ps in self.slices.pss()[:2]: #just the first two (Noun and Verb)
            profiles=self.slices.profiles(ps=ps)[:self.settings.maxprofiles]
            t=_("{} data: (profiles: {})".format(ps,profiles))
            log.info(t)
            print(t)
            s1=xlp.Section(xlpr,t)
            t=_("This section covers the following top syllable profiles "
                "which are found in {}s: {}".format(ps,profiles))
            p=xlp.Paragraph(s1,t)
            log.info(t)
            print(t)
            for profile in profiles:
                t=_("{} {}s".format(profile,ps))
                s2=xlp.Section(s1,t,level=2)
                print(t)
                log.info(t)
                for cvt in self.cvtstodo:
                    t=_("{} checks".format(self.params.cvtdict()[cvt]['sg']))
                    print(t)
                    log.info(t)
                    sid=" ".join([t,"for",profile,ps+'s'])
                    s3=xlp.Section(s2,sid,level=3)
                    maxcount=rx.countxiny(cvt, profile)
                    # re.subn(cvt, cvt, profile)[1]
                    self.wordsbypsprofilechecksubcheck(s3,cvt=cvt,ps=ps,
                                                        profile=profile)
        self.coocurrencetables(xlpr)
        log.info(self.checkcounts)
        xlpr.close(me=me)
        sys.stdout.close()
        sys.stdout=sys.__stdout__ #In case we want to not crash afterwards...:-)
        self.waitdone()
    def coocurrencetables(self,xlpr):
        t=_("Summary Co-ocurrence Tables")
        s1s=xlp.Section(xlpr,t)
        for ps in self.checkcounts:
            s2s=xlp.Section(s1s,ps,level=2)
            for profile in self.checkcounts[ps]:
                s3s=xlp.Section(s2s,' '.join([ps,profile]),level=3)
                log.info("names used ({}-{}): {}".format(ps,profile,
                                self.checkcounts[ps][profile].keys()))
                checks=self.orderchecks(self.checkcounts[ps][profile].keys())
                for check in checks:
                    log.debug("Counts by ({}) check: {}".format(
                        check,self.checkcounts[ps][profile][check]))
                    rows=list(self.checkcounts[ps][profile][check])
                    if not len(rows):
                        continue
                    if 'x' in check:
                        cols=list(self.checkcounts[ps][profile][check][rows[0]])
                    else:
                        cols=[check]
                    if not len(cols):
                        continue
                    caption=' '.join([ps,profile,check])
                    t=xlp.Table(s3s,caption)
                    for x1 in ['header']+rows:
                        h=xlp.Row(t)
                        for x2 in ['header']+cols:
                            log.debug("x1: {}; x2: {}".format(x1,x2))
                            # if x1 != 'header' and x2 not in ['header','n']:
                            #     log.debug("value: {}".format(self.checkcounts[
                            #         ps][profile][name][x1][x2]))
                            if x1 == 'header' and x2 == 'header':
                                # log.debug("header corner")
                                # cell=xlp.Cell(h,content=name,header=True)
                                cell=xlp.Cell(h,content='',header=True)
                            elif x1 == 'header':
                                # log.debug("header row")
                                cell=xlp.Cell(h,content=x2,header=True)
                            elif x2 == 'header':
                                # log.debug("header column")
                                cell=xlp.Cell(h,content=x1,header=True)
                            else:
                                # log.debug("Not a header")
                                if x2 == check:
                                    value=self.checkcounts[ps][
                                                    profile][check][x1]
                                else:
                                    value=self.checkcounts[ps][
                                                    profile][check][x1][x2]
                                if not value:
                                    value=''
                                cell=xlp.Cell(h,content=value)
    def __init__(self):
        self.reportbasefilename=self.settings.reportbasefilename
        self.reporttoaudiorelURL=self.settings.reporttoaudiorelURL
        self.distinguish=self.settings.distinguish
        self.profilesbysense=self.settings.profilesbysense
        self.s=self.settings.s
class Comprehensive(object):
    pass
class SortCV(Sort,Segments,TaskDressing,ui.Window):
    """docstring for SortCV."""
    def __init__(self, parent):
        ui.Window.__init__(self,parent)
        TaskDressing.__init__(self,parent)
        Sort.__init__(self, parent)
        Segments.__init__(self,parent)
        # super(SortCV, parent).__init__()
        # Sort.__init__(self)
    def picked(self,choice,**kwargs):
        return
        entry.addresult(check, result='OK') #let's not translate this...
        debug()
        window=ui.Window(parent, title='Same! '+entry.lexeme+': '
                        +entry.guid)
        result=(entry.citation,nn(entry.plural),nn(entry.imperative),
                    nn(entry.ps),nn(entry.gloss))
        ui.Button(window.frame, width=80, text=result,
            command=window.destroy).grid(column=0, row=0)
        window.exitButton=''
    def notpicked(self,choice):
        """I should think through what I want for this button/script."""
        if entry is None:
            log.info("No entry!")
            """Probably a bad idea"""
            entry=Entry(db, parent, window, check, guid=choice)
        entry.addresult(check, result='NOTok')
        window=ui.Window(parent, title='notpicked: Different! '
                        +entry.lexeme+': '+entry.guid)
        result=entry.citation,nn(entry.plural),nn(entry.imperative),nn(entry.ps),
        nn(entry.gloss)
        ui.Label(window.frame, width=40, text=result).grid(row=0,column=0)
        q=(_("What is wrong with this word?"))
        ui.Label(window.frame, text=q).grid(column=0, row=1)
        if check.name == "V1=V2":
            bcv1nv2=(_("Two different vowels (V1≠V2)"))
            bscv1isv2nsc=(_("Vowels are the same, but the wrong vowel"))
            problemopts=[("badCheck",bcv1nv2),
                ("badSubcheck",bscv1isv2nsc+" (V1=V2≠"+check.subcheck+")")]
        else:
            log.info("Sorry, that check isn't set up yet.")
        buttonFrame1=ui.ButtonFrame(window.frame,
                                    window=window,
                                    optionlist=problemopts,
                                    command=Check.fixdiff,
                                    width="50",
                                    column=0, row=3
                                    )
        i=4 #start at this row
        print(result)
    def fixV12(parent, window, check, entry, choice):
        """This and following scripts represent a structure of the program
        which is way more complex than we want. We have to think through how
        to organize the functions and windows in such a way as the UI is
        straightforward and completely unconfusing."""
        window.title=(_("TITLE!"))
        ui.Label(window.frame, text=entry.citation+' - '+entry.gloss,
                        anchor=ui.W).grid(column=0, row=0, columnspan=2)
        q1=_("It looks like the vowels are the same, but not the correct vowel;"
            " let's fix that.")
        ui.Label(window.frame, text=q1,anchor=ui.W).grid(column=0, row=2,
                                                                columnspan=2)
        q2=_("What are the two vowels?")
        ui.Label(window.frame, text=q2,anchor=ui.W).grid(column=0, row=3,
                                                                columnspan=1)
        ButtonFrame1=ui.ButtonFrame(window.frame,
                                window=window,
                                optionlist=check.db.vowels(),
                                command=Check.fixVs,
                                column=0, row=4
                                )
    def fixV1(parent, window, check, entry, choice):
        t=(_('fixV1:Different data to be fixed! '))+entry.lexeme+': '+entry.guid
        print(t)
        check.fix='V1'
        #window.destroy()
        #window=ui.Window(self.frame,, title=t, entry=entry, backcmd=fixdiff)
        window.resetframe()
        t2=(_("It looks like the vowels aren't the same; let's fix that."))
        ui.Label(window.frame, text=t2, justify=ui.LEFT).grid(column=0,
                                                                    row=0,
                                                                columnspan=2)
        t3=(_("What is the first vowel? (C_CV)"))
        ui.Label(window.frame, text=t3, anchor=ui.W).grid(column=0,
                                                                row=1,
                                                                columnspan=1)
        ButtonFrame1=ui.ButtonFrame(window.frame,
                                window=window,
                                optionlist=check.db.vowels(),
                                command=Check.newform,
                                column=0, row=2
                                )
    def fixV2(parent, window, check, entry, choice):
        check.fix='V2'
        t=(_('fixV2:Different data to be fixed! '))+entry.lexeme+': '+entry.guid
        t=(_("What is the second vowel?"))
        ui.Label(window.frame, text=t,justify=ui.LEFT).grid(column=0, row=1, columnspan=1)
        ButtonFrame1=ui.ButtonFrame(window.frame,
                                    window=window,
                                    optionlist=check.db.vowels(),
                                    command=Check.newform,
                                    column=0, row=2
                                    )
    def fixdiff(parent, window, check, entry, choice):
        """We need to fix problems in a more intuitively obvious way"""
        entry.problem=choice
        entry.addresult(check, result=entry.problem)
        window.destroy()
        window=ui.Window(self.frame.parent, entry=entry, backcmd=notpickedback)
        ui.Label(window, text="Let's fix those problems").grid(column=0, row=0)
        if entry.problem == "badCheck": #This isn't the right check for this entry --re.search("V1≠V2",difference):
            window.destroy()
            t=(_("fixVs:Different vowels! "))+entry.lexeme+': '+entry.guid
            window=ui.Window(self.frame, title=t, entry=entry, backcmd=Check.fixdiff)
            Check.fixV1(parent, window, check, entry, choice)
            window.wait_window(window=window)
            window=ui.Window(self.frame, title=t, entry=entry, backcmd=Check.fixdiff)
            Check.fixV2(parent, window, check, entry, choice) #I should make this wait until the first one finishes..…
            window.wait_window(window=window)
            window=ui.Window(self.frame, title=t, entry=entry, backcmd=Check.fixdiff)
            Check.fixVs(parent, window, check, entry, choice)
        elif entry.problem == "badSubcheck": #This isn't the right subcheck for this entry --re.search("V1=V2≠"+Vo,difference): #
            window.destroy()
            t=(_("fixVs:Same Vowel, but wrong one! "))+entry.lexeme+': '+entry.guid
            window=ui.Window(self.frame, title=t, entry=entry, backcmd=Check.fixdiff)
            Check.fixV12(parent, window, check, entry, choice)
        else:
            log.info("Huh? I don't understand what the user wants.")
        Check.fixVs
    def fixVs(parent, window, check, entry, choice):
        #This isn't working yet.
        log.info("running fixVs!!!!???!??!?!?!?")

        #I need to rework this to work more generally..….
        ui.Label(window.frame, text="I will make the following changes:").grid(column=0, row=0)
        lexemeNew=entry.newform #newform(entry.lexeme,'v12',check.subcheck,choice)
        """citationNew = re.sub(entry.lexeme, lexemeNew, entry.citation)"""
        ui.Label(window.frame, text="citation: "+entry.citation+" → "+citationNew).grid(column=0, row=1)
        ui.Label(window.frame, text="lexeme: "+entry.lexeme+" → "+lexemeNew).grid(column=0, row=2)
        fields={}
        if entry.plural is not None:
            """pluralNew = re.sub(entry.lexeme, lexemeNew, entry.plural)"""
            ui.Label(window.frame, text="plural: "+plural+" → "+pluralNew).grid(column=0, row=3)
            fields={'Plural'}
        if entry.imperative is not None:
            """imperativeNew = re.sub(entry.lexeme, lexemeNew, entry.imperative)"""
            ui.Label(window.frame, text="imperative: "+entry.imperative+" → "+imperativeNew).grid(column=0, row=4)
        def ok():
            entry.addresult(check, result=entry.lexeme+'->'+lexemeNew+'-ok')
            entry.db.log(entry.guid+": lexeme: "+entry.lexeme+" → "+lexemeNew)
            entry.put.lexeme(entry,lexemeNew)
            entry.db.log(entry.guid+": citation: "+entry.citation+" → "+citationNew)
            entry.put.citation(entry,citationNew)
            #lift_mod.field(guid,fieldtype,newform)
            entry.db.write() #put this in lift.py
            window.destroy()
        def notok():
            entry.addresult(check, result=entry.lexeme+'->'+lexemeNew+'-NOTok')
        ui.Button(window, width=10, text="OK", command=ok).grid(row=1,column=0)
        #This is where we should call addresult, and write to file.
        ui.Button(window, width=15, text="Not OK (Go Back)", command=notok).grid(row=1,column=1)
    def newform(parent, window, check, entry, choice):
        #I need to rework this to work more generally..….
        #or even to work once. The logic is bad.
        C=check.C
        V=check.V
        xi=1
        if check.fix == "V1":
            r=str('('+V+')'+'('+C+')'+'('+V+')')
            sub=(choice+r"\2\3")
            log.info("Note: this assumes we're changing one of two vowels "
                "separated by a consonant")
            #I want to access the second group...
            #print(r)
        elif check.fix == "C1":
            r=str('(('+C+'))'+'('+V+')'+'('+C+')')
            print(r)
            log.info("Note: this assumes we're changing one of two consonants "
                "separated by a vowel")
        elif check.fix == "V2":
            r=str('('+V+')'+'('+C+')'+'('+V+')')
            sub=(r"\1\2"+choice)
            print("Note: this assumes we're changing one of two vowels "
                "separated by a consonant")
            #print(r)
        elif check.fix == "C2":
            r=str('('+C+')'+V+'('+C+')')
            print(r)
        else:
            log.info("Fix "+check.fix +" undefined.")
        def old():
            if check.fix == ("V1" or "C1"):
                ximin=1
                ximax=1
            elif check.fix == ("V2" or "C2"):
                ximin=2
                ximax=2
            elif check.fix == ("V12" or "C12"):
                ximin=1
                ximax=2
        #print(check.subcheck, value, entry.newform)
        #I need this to find the point I'm trying to change, even if it has been
        #changed before, and even if another part of the same word has already
        #been changed, e.g., another vowel in another position. So I need to use
        #the newform when present (i.e., changes have been made but not confirmed)
        #but refer to the lexeme item for reference (e.g., which subcheck I'm running.)
        try: # use a previous entry.newform, if it exists:
            baseform=entry.newform
            entry.newform=''
            log.info("Using newform")
        except:
            baseform=entry.lexeme
            log.info("Using lexeme")
            #entry.newform = re.sub(check.subcheck, choice, entry.newform, count=1)
        print('r: '+r)
        print('sub: '+sub)
        print('baseform: '+baseform)
        """entry.newform=re.sub(r, sub, baseform)"""
        print('newform: '+entry.newform)
        def old2():
            for x in baseform:
                if x == check.subcheck: # <= ximax ):
                    if ximin <= xi <= ximax:
                        try:
                            entry.newform=entry.newform+choice #+str(xi)
                        except:
                            entry.newform=choice #+str(xi)
                    else:
                        try:
                            entry.newform=entry.newform+x #+"_"
                        except:
                            entry.newform=x #+"_"
                    xi += 1
                else:
                    try:
                        entry.newform=entry.newform+x #+"_"
                    except:
                        entry.newform=x #+"_"
                #entry.newform = re.sub(check.subcheck, choice, entry.lexeme, count=1)
        print(entry.newform)
        window.destroy()
class SortV(Sort,Segments,TaskDressing,ui.Window):
    def taskicon(self):
        return program['theme'].photo['iconV']
    def tasktitle(self):
        return _("Sort Vowels") #Citation Form Sorting in Tone Frames
    def dobuttonkwargs(self):
        return {'text':_("Sort!"),
                'fn':self.runcheck,
                # column=0,
                'font':'title',
                'compound':'bottom', #image bottom, left, right, or top of text
                'image':self.taskchooser.theme.photo['V'], #self.cvt
                'sticky':'ew'
                }
    def __init__(self, parent):
        ui.Window.__init__(self,parent)
        TaskDressing.__init__(self,parent)
        self.params.cvt('V')
        Sort.__init__(self, parent)
        Segments.__init__(self,parent)
        # super(SortV, self).__init__()
        # Sort.__init__(self)
class SortC(Sort,Segments,TaskDressing,ui.Window):
    def taskicon(self):
        return program['theme'].photo['iconC']
    def tasktitle(self):
        return _("Sort Consonants") #Citation Form Sorting in Tone Frames
    def dobuttonkwargs(self):
        return {'text':_("Sort!"),
                'fn':self.runcheck,
                # column=0,
                'font':'title',
                'compound':'bottom', #image bottom, left, right, or top of text
                'image':self.taskchooser.theme.photo['C'], #self.cvt
                'sticky':'ew'
                }
    def __init__(self, parent):
        ui.Window.__init__(self,parent)
        TaskDressing.__init__(self,parent)
        self.params.cvt('C')
        Sort.__init__(self, parent)
        Segments.__init__(self,parent)
        # super(SortC, parent).__init__()
        # Sort.__init__(self)
class SortT(Sort,Tone,TaskDressing,ui.Window):
    def taskicon(self):
        return program['theme'].photo['iconT']
    def tasktitle(self):
        return _("Sort Tone") #Citation Form Sorting in Tone Frames
    def tooltip(self):
        return _("This task helps you sort words in citation form tone frames.")
    def dobuttonkwargs(self):
        return {'text':_("Sort!"),
                'fn':self.runcheck,
                # column=0,
                'font':'title',
                'compound':'bottom', #image bottom, left, right, or top of text
                'image':self.taskchooser.theme.photo['T'], #self.cvt
                'sticky':'ew'
                }
    def __init__(self, parent): #frame, filename=None
        Tone.__init__(self,parent)
        ui.Window.__init__(self,parent)
        TaskDressing.__init__(self,parent)
        self.params.cvt('T')
        Sort.__init__(self, parent)
        log.info("status: {}".format(type(self.status)))
        # Not sure what this was for (XML?):
        self.pp=pprint.PrettyPrinter()
        """Are we OK without these?"""
        log.info("Done initializing check.")
        """Testing Zone"""
    def addtonefieldpron(self,guid,framed): #unused; leads to broken lift fn
        senseid=None
        self.db.addpronunciationfields(
                                    guid,senseid,self.analang,self.glosslangs,
                                    lang='en',
                                    forms=framed,
                                    fieldtype='tone',location=check,
                                    fieldvalue=self.groupselected,
                                    ps=None
                                    )
    def marksortedguid(self,guid):
        """I think these are only valuable during a check, so we don't have to
        constantly refresh sortingstatus() from the lift file."""
        """These four functions should be generalizable"""
        self.guidssorted.append(guid)
        self.guidstosort.remove(guid)
    def marktosortguid(self,guid):
        self.guidstosort.append(guid)
        self.guidssorted.remove(guid)
    """Doing stuff"""
class Transcribe(Tone,Sound,Sort,TaskDressing,ui.Window):
    def tasktitle(self):
        return _("Transcribe Tone")
    def tooltip(self):
        return _("This task helps you transcribe your surface groups, giving "
                "them meaniningful names (e.g., [˥˥ ˨˨]) instead of numbers.")
    def dobuttonkwargs(self):
        return {'text':_("Transcribe Surface Tone Groups"),
                'fn':self.makewindow,
                'font':'title',
                'compound':'top', #image bottom, left, right, or top of text
                'image':self.taskchooser.theme.photo['Transcribe'], #self.cvt
                'sticky':'ew'
                }
    def taskicon(self):
        return program['theme'].photo['iconTranscribe']
    def __init__(self, parent): #frame, filename=None
        Tone.__init__(self, parent)
        ui.Window.__init__(self, parent)
        TaskDressing.__init__(self, parent)
        Sound.__init__(self)
    def updateerror(self,event=None):
        self.errorlabel['text'] = ''
    def updategroups(self):
        # cvt=self.params.cvt()
        # ps=self.slices.ps()
        # profile=self.slices.profile()
        # check=self.params.check()
        self.groups=self.status.groups(wsorted=True)
        # self.status[cvt][ps][profile][check]['groups']
        # self.status[cvt][ps][profile][check]['done']
        self.groupsdone=self.status.verified()
        self.group=self.status.group()
        log.info("group: {}, groups: {}".format(self.group,self.groups))
        if not self.groups:
            ErrorNotice(_("No groups in that slice; try another!"))
            return
        log.info("group: {}, groups: {}".format(self.group,self.groups))
        if not self.group or self.group not in self.groups:
            w=self.getgroup(wsorted=True, guess=True)
            if w.winfo_exists():
                w.wait_window(w)
            self.group=self.status.group()
            if not self.group:
                log.info("I asked for a framed tone group, but didn't get one.")
                return
        log.info("group: {}, groups: {}".format(self.group,self.groups))
        self.othergroups=self.groups[:]
        try:
            self.othergroups.remove(self.group)
        except ValueError:
            log.error(_("current group ({}) doesn't seem to be in list of "
                "groups: ({})\n\tThis may be because we're looking for data "
                "that isn't there, or maybe a setting is off.".format(
                                                    self.group, self.groups)))
            return
        return 1
    def submitform(self):
        newtonevalue=self.transcriber.formfield.get()
        self.updategroups()
        if newtonevalue == "":
            noname=_("Give a name for this tone melody!")
            log.debug(noname)
            self.errorlabel['text'] = noname
            return 1
        if newtonevalue != self.group: #only make changes!
            if newtonevalue in self.groups :
                deja=_("Sorry, there is already a group with "
                                "that label; If you want to join the "
                                "groups, give it a different name now, "
                                "and join it later".format(newtonevalue))
                log.debug(deja)
                self.errorlabel['text'] = deja
                return 1
            self.updatebygroupsenseid(self.group,newtonevalue)
            self.status.renamegroup(self.group,newtonevalue)
            self.settings.storesettingsfile(setting='status')
        else: #move on, but notify in logs
            log.info("User selected ‘{}’, but with no change.".format(
                                                                self.oktext))
        if hasattr(self,'group_comparison'):
            delattr(self,'group_comparison') # in either case
        self.runwindow.destroy()
        return
    def done(self):
        self.submitform()
        self.donewpyaudio()
    def next(self):
        log.debug("running next group")
        error=self.submitform()
        if not error:
            # log.debug("group: {}".format(group))
            self.status.nextgroup(wsorted=True)
            # log.debug("group: {}".format(group))
            self.makewindow()
    def nextcheck(self):
        log.debug("running next check")
        error=self.submitform()
        if not error:
            # log.debug("check: {}".format(check))
            self.status.nextcheck(wsorted=True)
            # log.debug("check: {}".format(check))
            self.makewindow()
    def nextprofile(self):
        log.debug("running next profile")
        error=self.submitform()
        if not error:
            # log.debug("profile: {}".format(profile))
            self.status.nextprofile(wsorted=True)
            # log.debug("profile: {}".format(profile))
            self.makewindow()
    def setgroup_comparison(self):
        w=self.getgroup(comparison=True,wsorted=True) #this returns its window
        if w and w.winfo_exists(): #This window may be already gone
            w.wait_window(w)
        if hasattr(self.settings,'group_comparison'):
            self.group_comparison=self.settings.group_comparison
        self.comparisonbuttons()
    def comparisonbuttons(self):
        try: #successive runs
            self.compframe.compframeb.destroy()
            log.info("Comparison frameb destroyed!")
        except: #first run
            log.info("Problem destroying comparison frame, making...")
        # self.buttonframew=int(program['screenw']/4)
        # b['wraplength']=buttonframew
        self.compframe.compframeb=ui.Frame(self.compframe)
        self.compframe.compframeb.grid(row=1,column=0)
        t=_('Compare with another group')
        if (hasattr(self, 'group_comparison')
                and self.group_comparison in self.groups and
                self.group_comparison != self.group):
            log.info("Making comparison buttons for group {} now".format(
                                                self.group_comparison))
            t=_('Compare with another group ({})').format(
                                                self.group_comparison)
            self.compframe.bf2=ToneGroupButtonFrame(self.compframe.compframeb,
                                    self, self.exs,
                                    self.group_comparison,
                                    showtonegroup=True,
                                    playable=True,
                                    unsortable=False, #no space, bad idea
                                    alwaysrefreshable=True,
                                    font='default',
                                    wraplength=self.buttonframew
                                    )
            self.compframe.bf2.grid(row=0, column=0, sticky='w')
        elif not hasattr(self, 'group_comparison'):
            log.info("No comparison found !")
        elif self.group_comparison not in self.groups:
            log.info("Comparison ({}) not in group list ({})"
                        "".format(self.group_comparison,self.groups))
        elif self.group_comparison == group:
            log.info("Comparison ({}) same as subgroup ({}); not showing."
                        "".format(self.group_comparison,self.group))
        else:
            log.info("This should never happen (renamegroup/"
                        "comparisonbuttons)")
        self.sub_c['text']=t
    def makewindow(self):
        cvt=self.params.cvt()
        ps=self.slices.ps()
        profile=self.slices.profile()
        check=self.params.check()
        self.buttonframew=int(program['screenw']/3.5)
        if check == None:
            self.getcheck(guess=True)
            if check == None:
                log.info("I asked for a check name, but didn't get one.")
                return
        if not self.status.groups(wsorted=True):
            log.error("I don't have any sorted data for check: {}, "
                        "ps-profile: {}-{},".format(check,ps,profile))
            return
        groupsok=self.updategroups()
        if not groupsok:
            log.error("Problem with log; check earlier message.")
            return
        padx=50
        pady=10
        title=_("Rename {} {} tone group ‘{}’ in ‘{}’ frame"
                        ).format(ps,profile,self.group,check)
        self.getrunwindow(title=title)
        titlel=ui.Label(self.runwindow.frame,text=title,font='title',
                        row=0,column=0,sticky='ew',padx=padx,pady=pady
                        )
        getformtext=_("What new name do you want to call this surface tone "
                        "group? A label that describes the surface tone form "
                        "in this context would be best, like ‘[˥˥˥ ˨˨˨]’")
        getform=ui.Label(self.runwindow.frame,
                        text=getformtext,
                        font='read',
                        norender=True,
                        row=1,column=0,sticky='ew',padx=padx,pady=pady
                        )
        getform.wrap()
        inputfeedbackframe=ui.Frame(self.runwindow.frame,
                            row=2,column=0,sticky=''
                            )
        """extract from here"""
        self.transcriber=transcriber.Transcriber(inputfeedbackframe,
                                initval=self.group,
                                soundsettings=self.soundsettings,
                                row=0,column=0,sticky=''
                                )
        self.transcriber.formfield.bind('<KeyRelease>', self.updateerror) #apply function after key
        """to here"""
        infoframe=ui.Frame(inputfeedbackframe,
                            row=0,column=1,sticky=''
                            )
        g=nn(self.othergroups,twoperline=True)
        log.info("There: {}, NTG: {}; g:{}".format(self.groups,
                                                    self.othergroups,g))
        groupslabel=ui.Label(infoframe,
                            text='Other Groups:\n{}'.format(g),
                            row=0,column=1,
                            sticky='new',
                            padx=padx,
                            rowspan=2
                            )
        self.errorlabel=ui.Label(infoframe,text='',
                            fg='red',
                            wraplength=int(self.frame.winfo_screenwidth()/3),
                            row=2,column=1,sticky='nsew'
                            )
        responseframe=ui.Frame(self.runwindow.frame,
                                row=3,
                                column=0,
                                sticky='',
                                padx=padx,
                                pady=pady,
                                )
        self.oktext=_('Use this name and go to:')
        column=0
        sub_lbl=ui.Label(responseframe,text = self.oktext, font='read',
                        row=0,column=column,sticky='ns'
                        )
        for button in [
                        (_('main screen'), self.done),
                        (_('next group'), self.next),
                        (_('next tone frame'), self.nextcheck),
                        (_('next syllable profile'), self.nextprofile),
                        ]:
            column+=1
            ui.Button(responseframe,text = button[0], command = button[1],
                                anchor ='c',
                                row=0,column=column,sticky='ns'
                                )
        examplesframe=ui.Frame(self.runwindow.frame,
                                row=4,column=0,sticky=''
                                )
        b=ToneGroupButtonFrame(examplesframe, self, self.exs,
                                self.group,
                                showtonegroup=True,
                                # canary=entryview,
                                playable=True,
                                unsortable=True,
                                alwaysrefreshable=True,
                                row=0, column=0, sticky='w',
                                wraplength=self.buttonframew
                                )
        self.compframe=ui.Frame(examplesframe,
                    highlightthickness=10,
                    highlightbackground=self.frame.theme.white,
                    row=0,column=1,sticky='e'
                    ) #no hlfg here
        t=_('Compare with another group')
        self.sub_c=ui.Button(self.compframe,
                        text = t,
                        command = self.setgroup_comparison,
                        row=0,column=0
                        )
        self.comparisonbuttons()
        self.runwindow.waitdone()
        self.sub_c.wait_window(self.runwindow) #then move to next step
        """Store these variables above, finish with (destroying window with
        local variables):"""
class JoinUFgroups(Tone,TaskDressing,ui.Window):
    """docstring for JoinUFgroups."""
    def tasktitle(self):
        return _("Join Underlying Form Groups")
    def tooltip(self):
        return _("This task helps you join hypersplit UF groups, as well as "
                "giving them meaniningful names (e.g., High or Low).")
    def dobuttonkwargs(self):
        return {'text':_("Join draft UF Groups"),
                'fn':self.tonegroupsjoinrename,
                'font':'title',
                'compound':'top', #image bottom, left, right, or top of text
                'image':self.taskchooser.theme.photo['JoinUF'], #self.cvt
                'sticky':'ew'
                }
    def taskicon(self):
        return program['theme'].photo['iconJoinUF']
    def tonegroupsjoinrename(self,**kwargs):
        def clearerror(event=None):
            errorlabel['text'] = ''
        def submitform():
            clearerror()
            uf=named.get()
            if uf == "":
                noname=_("Give a name for this UF tone group!")
                log.debug(noname)
                errorlabel['text'] = noname
                return
            groupsselected=[]
            for group in groupvars: #all group variables
                groupsselected+=[group.get()] #value, name if selected, 0 if not
            groupsselected=[x for x in groupsselected if x != '']
            log.info("groupsselected:{}".format(groupsselected))
            if uf in analysis.orderedUFs and uf not in groupsselected:
                deja=_("That name is already there! (did you forget to include "
                        "the ‘{}’ group?)".format(uf))
                log.debug(deja)
                errorlabel['text'] = deja
                return
            for group in groupsselected:
                if group in analysis.senseidsbygroup: #selected ones only
                    log.debug("Changing values from {} to {} for the following "
                            "senseids: {}".format(group,uf,
                                        analysis.senseidsbygroup[group]))
                    for senseid in analysis.senseidsbygroup[group]:
                        self.db.addtoneUF(senseid,uf,analang=self.analang,
                        write=False)
            self.db.write()
            self.runwindow.destroy()
            self.status.last('join',update=True)
            self.tonegroupsjoinrename() #call again, in case needed
        def redo():
            self.runwindow.wait(_("Redoing Tone Analysis"))
            analysis.do()
            # self.runwindow.waitdone()
            # self.runwindow.destroy()
            self.tonegroupsjoinrename() #call again, in case needed
        def done():
            self.runwindow.destroy()
        ps=kwargs.get('ps',self.slices.ps())
        profile=kwargs.get('profile',self.slices.profile())
        self.getrunwindow()
        title=_("Join/Rename Draft Underlying {}-{} tone groups".format(
                                                        ps,profile))
        self.runwindow.title(title)
        padx=50
        pady=10
        rwrow=gprow=qrow=0
        t=ui.Label(self.runwindow.frame,text=title,font='title')
        t.grid(row=rwrow,column=0,sticky='ew')
        redotext=_("Redo the analysis;\nstart these groups over")
        text=_("This page allows you to join the {}-{} draft underlying tone "
                "groups created for you by {}, \nwhich are almost certainly "
                "too small for you. \nLooking at a draft report, and making "
                "your own judgement about which groups belong together, select "
                "all the groups that belong together in one group, and "
                "give that new group "
                "a name. You can then repeat this for other groups "
                "that should be joined. \nIf for any reason you want to undo "
                "the groups you create here, you can start over with an new "
                "analysis by pressing the ‘{}’ button. \nOtherwise, these "
                "joined groups will be reflected in reports until you sort "
                "more data.".format(ps,profile,program['name'],
                                                redotext.replace('\n',' ')))
        rwrow+=1
        i=ui.Label(self.runwindow.frame,text=text,
                    row=rwrow,column=0,sticky='ew')
        i.wrap()
        ui.Button(self.runwindow.frame,text=redotext, cmd=redo,
                    row=rwrow,column=1,sticky='ew')
        rwrow+=1
        qframe=ui.Frame(self.runwindow.frame)
        qframe.grid(row=rwrow,column=0,sticky='ew')
        text=_("What do you want to call this UF tone group for {}-{} words?"
                "".format(ps,profile))
        qrow+=1
        q=ui.Label(qframe,text=text,
                    row=qrow,column=0,sticky='ew',pady=20
                    )
        q.wrap()
        named=ui.StringVar() #store the new name here
        namefield = ui.EntryField(qframe,textvariable=named)
        namefield.grid(row=qrow,column=1)
        namefield.bind('<Key>', clearerror)
        errorlabel=ui.Label(qframe,text='',fg='red')
        errorlabel.grid(row=qrow,column=2,sticky='ew',pady=20)
        text=_("Select the groups below that you want in this {} group, then "
                "click ==>".format(ps))
        qrow+=1
        d=ui.Label(qframe,text=text)
        d.grid(row=qrow,column=0,sticky='ew',pady=20)
        sub_btn=ui.Button(qframe,text = _("OK"), command = submitform, anchor ='c')
        sub_btn.grid(row=qrow,column=1,sticky='w')
        done_btn=ui.Button(qframe,text = _("Done —no change"), command = done,
                                                                    anchor ='c')
        done_btn.grid(row=qrow,column=2,sticky='w')
        groupvars=list()
        rwrow+=1
        scroll=ui.ScrollingFrame(self.runwindow.frame)
        scroll.grid(row=rwrow,column=0,sticky='ew')
        analysis=self.makeanalysis()
        analysis.donoUFanalysis()
        nheaders=0
        if not analysis.orderedUFs:
            self.runwindow.waitdone()
            self.runwindow.destroy()
            ErrorNotice(title=_("No draft UF groups found for {} words!"
                                "").format(ps),
                        text=_("You don't seem to have any analyzed {0} groups "
                        "to join/rename. Have you done a tone analyis for {0} "
                        "words?").format(ps)
                        )
            return
        # ufgroups= # order by structured groups? Store this somewhere?
        for group in analysis.orderedUFs: #make a variable and button to select
            idn=analysis.orderedUFs.index(group)
            if idn % 5 == 0: #every five rows
                col=1
                for check in analysis.orderedchecks:
                    col+=1
                    cbh=ui.Label(scroll.content, text=check, font='small')
                    cbh.grid(row=idn+nheaders,
                            column=col,sticky='ew')
                nheaders+=1
            groupvars.append(ui.StringVar())
            n=len(analysis.senseidsbygroup[group])
            buttontext=group+' ({})'.format(n)
            cb=ui.CheckButton(scroll.content, text = buttontext,
                                variable = groupvars[idn],
                                onvalue = group, offvalue = 0,
                                )
            cb.grid(row=idn+nheaders,column=0,sticky='ew')
            # analysis.valuesbygroupcheck[group]:
            col=1
            for check in analysis.orderedchecks:
                col+=1
                if check in analysis.valuesbygroupcheck[group]:
                    cbl=ui.Label(scroll.content,
                        text=unlist(
                                analysis.valuesbygroupcheck[group][check]
                                    )
                            )
                    cbl.grid(row=idn+nheaders,column=col,sticky='ew')
        self.runwindow.waitdone()
        self.runwindow.wait_window(scroll)
    def __init__(self, parent):
        Tone.__init__(self, parent)
        ui.Window.__init__(self, parent)
        TaskDressing.__init__(self, parent)
class RecordCitation(Record,Segments,TaskDressing,ui.Window):
    """docstring for RecordCitation."""
    def tooltip(self):
        return _("This task helps you record words in isolation forms.")
    def dobuttonkwargs(self):
        return {'text':_("Record Dictionary Words"),
                'fn':self.showentryformstorecord,
                'font':'title',
                'compound':'top', #image bottom, left, right, or top of text
                'image':self.taskchooser.theme.photo['WordRec'],
                'sticky':'ew'
                }
    def tasktitle(self):
        return _("Record Words") #Citation Forms
    def taskicon(self):
        return program['theme'].photo['iconWordRec']
    def __init__(self, parent): #frame, filename=None
        Segments.__init__(self,parent)
        ui.Window.__init__(self,parent)
        TaskDressing.__init__(self,parent)
        Record.__init__(self)
        # self.do=self.showentryformstorecord
class RecordCitationT(Record,Tone,TaskDressing,ui.Window):
    """docstring for RecordCitation."""
    def tooltip(self):
        return _("This task helps you record words in tone frames, in citation form.")
    def dobuttonkwargs(self):
        return {'text':_("Record Words in Tone Frames"),
                'fn':self.showtonegroupexs,
                'font':'title',
                'compound':'top', #image bottom, left, right, or top of text
                'image':self.taskchooser.theme.photo['TRec'],
                'sticky':'ew'
                }
    def taskicon(self):
        return program['theme'].photo['iconTRec']
    def tasktitle(self):
        return _("Record Tone") #Citation Form Sorting in Tone Frames
    def __init__(self, parent): #frame, filename=None
        Tone.__init__(self,parent)
        ui.Window.__init__(self,parent)
        TaskDressing.__init__(self,parent)
        Record.__init__(self)
        # self.do=self.showtonegroupexs
class ReportCitation(Report,Segments,TaskDressing,ui.Window):
    """docstring for ReportCitation."""
    def tasktitle(self):
        return _("Alphabet Report") # on One Data Slice
    def taskicon(self):
        return program['theme'].photo['iconReport']
    def tooltip(self):
        return _("This report gives you reports for one lexical "
                "category, in one syllable profile. \nIt does "
                "one of three sets of reports: \n- Vowel, \n- Consonant, or "
                "\n- Consonant-Vowel Correspondence")
    def dobuttonkwargs(self):
        return {'text':"Report!",
                'fn':self.runcheck,
                # column=0,
                'font':'title',
                'compound':'bottom', #image bottom, left, right, or top of text
                'image':self.taskchooser.theme.photo['Report'],
                'sticky':'ew'
                }
    def __init__(self, parent): #frame, filename=None
        Segments.__init__(self,parent)
        ui.Window.__init__(self,parent)
        TaskDressing.__init__(self,parent)
        Report.__init__(self)
    def runcheck(self):
        """This needs to get stripped down and updated for just this check"""
        self.settings.storesettingsfile()
        t=(_('Run Check'))
        log.info("Running report...")
        i=0
        cvt=self.params.cvt()
        if cvt == 'T':
            w=self.taskchooser.getcvt()
            w.wait_window(w)
            cvt=self.params.cvt()
            if cvt == 'T':
                ErrorNotice(_("Pick Consonants, Vowels, or CV for this report."))
                return
        ps=self.slices.ps()
        if not ps:
            self.getps()
        check=self.params.check()
        profile=self.slices.profile()
        if not profile:
            self.getprofile()
        if not profile or not ps:
            window=ui.Window(self.frame)
            text=_('Error: please set Ps-Profile first! ({}/{}/{})').format(
                                                     ps,check,profile)
            ui.Label(window,text=text).grid(column=0, row=i)
            i+=1
            return
        self.getresults()
class ReportCitationBasic(Report,Comprehensive,Segments,TaskDressing,ui.Window):
    """docstring for ReportCitation."""
    def tasktitle(self):
        return _("Comprehensive Alphabet Report") # on Citation Forms
    def taskicon(self):
        return program['theme'].photo['iconVCCVRepcomp']
    def tooltip(self):
        return _("This report gives you reports across multiple lexical "
                "categories, and across multiple syllable profiles. \nIt does "
                "this for three sets of reports: \n- Vowel, \n- Consonant, and "
                "\n- Consonant-Vowel Correspondence")
    def dobuttonkwargs(self):
        return {'text':"Report!",
                'fn':self.basicreport,
                # column=0,
                'font':'title',
                'compound':'bottom', #image bottom, left, right, or top of text
                'image':self.taskchooser.theme.photo['VCCVRepcomp'],
                'sticky':'ew'
                }
    def __init__(self, parent): #frame, filename=None
        Segments.__init__(self,parent)
        ui.Window.__init__(self,parent)
        TaskDressing.__init__(self,parent)
        Report.__init__(self)
        self.cvtstodo=['V','C','CV']
class ReportCitationBasicV(Report,Comprehensive,Segments,TaskDressing,ui.Window):
    """docstring for ReportCitation."""
    def tasktitle(self):
        return _("Comprehensive Vowel Report") # on Citation Forms
    def taskicon(self):
        return program['theme'].photo['iconVRepcomp']
    def tooltip(self):
        return _("This report gives you reports across multiple lexical "
                "categories, and across multiple syllable profiles. \nIt does "
                "this just for vowel checks.")
    def dobuttonkwargs(self):
        return {'text':"Report!",
                'fn':self.basicreport,
                # column=0,
                'font':'title',
                'compound':'bottom', #image bottom, left, right, or top of text
                'image':self.taskchooser.theme.photo['VRepcomp'],
                'sticky':'ew'
                }
    def __init__(self, parent): #frame, filename=None
        Segments.__init__(self,parent)
        ui.Window.__init__(self,parent)
        TaskDressing.__init__(self,parent)
        Report.__init__(self)
        self.cvtstodo=['V']
class ReportCitationBasicC(Report,Comprehensive,Segments,TaskDressing,ui.Window):
    """docstring for ReportCitation."""
    def tasktitle(self):
        return _("Comprehensive Consonant Report") # on Citation Forms
    def taskicon(self):
        return program['theme'].photo['iconCRepcomp']
    def tooltip(self):
        return _("This report gives you reports across multiple lexical "
                "categories, and across multiple syllable profiles. \nIt does "
                "this just for consonant checks.")
    def dobuttonkwargs(self):
        return {'text':"Report!",
                'fn':self.basicreport,
                # column=0,
                'font':'title',
                'compound':'bottom', #image bottom, left, right, or top of text
                'image':self.taskchooser.theme.photo['CRepcomp'],
                'sticky':'ew'
                }
    def __init__(self, parent): #frame, filename=None
        Segments.__init__(self,parent)
        ui.Window.__init__(self,parent)
        TaskDressing.__init__(self,parent)
        Report.__init__(self)
        self.cvtstodo=['C']
        # This is really hard on memory, with correspondences.
class ReportCitationBasicCV(Report,Comprehensive,Segments,TaskDressing,ui.Window):
    """docstring for ReportCitation."""
    def tasktitle(self):
        return _("Comprehensive CxV Phonotactics Report") # on Citation Forms
    def taskicon(self):
        return program['theme'].photo['iconCVRepcomp']
    def tooltip(self):
        return _("This report gives you reports across multiple lexical "
                "categories, and across multiple syllable profiles. \nIt does "
                "this just for consonant-vowel correspondence checks.")
    def dobuttonkwargs(self):
        return {'text':"Report!",
                'fn':self.basicreport,
                # column=0,
                'font':'title',
                'compound':'bottom', #image bottom, left, right, or top of text
                'image':self.taskchooser.theme.photo['CVRepcomp'],
                'sticky':'ew'
                }
    def __init__(self, parent): #frame, filename=None
        Segments.__init__(self,parent)
        ui.Window.__init__(self,parent)
        TaskDressing.__init__(self,parent)
        Report.__init__(self)
        self.cvtstodo=['CV']
class ReportConsultantCheck(Report,Tone,TaskDressing,ui.Window):
    """docstring for ReportCitationT."""
    def tasktitle(self):
        return _("Initialize Consultant Check")
    def taskicon(self):
        return program['theme'].photo['icontall']
    def tooltip(self):
        return _("This task automates work normally done before a consultant "
                "check: \n- reloads status data, and \n- runs comprehensive tone "
                "reports, \n  - by location and \n  - by lexeme sense.")
    def dobuttonkwargs(self):
        return {'text':"Start!",
                'fn':self.consultantcheck,
                # column=0,
                'font':'title',
                'compound':'bottom', #image bottom, left, right, or top of text
                'image':self.taskchooser.theme.photo['icontall'],
                'sticky':'ew'
                }
    def __init__(self, parent): #frame, filename=None
        Tone.__init__(self,parent)
        ui.Window.__init__(self,parent)
        TaskDressing.__init__(self,parent)
        Report.__init__(self)
class ReportCitationT(Report,Tone,TaskDressing,ui.Window):
    """docstring for ReportCitationT."""
    def tasktitle(self):
        return _("Tone Report")
        # "Make Reports on Citation Form Sorting in Tone Frames")
        # return _("Report on one slice of Citation Forms (in Tone Frames)")
    def taskicon(self):
        return program['theme'].photo['iconTRep']
    def tooltip(self):
        return _("This report gives you report for one lexical "
                "category, in one syllable profile. \nIt does "
                "this for all data sorted in tone frames, organized by word.")
    def dobuttonkwargs(self):
        return {'text':"Report!",
                'fn':self.do,
                # column=0,
                'font':'title',
                'compound':'bottom', #image bottom, left, right, or top of text
                'image':self.taskchooser.theme.photo['TRep'],
                'sticky':'ew'
                }
    def __init__(self, parent): #frame, filename=None
        Tone.__init__(self,parent)
        ui.Window.__init__(self,parent)
        self.do=self.tonegroupreport
        TaskDressing.__init__(self,parent)
        Report.__init__(self)
        self.bylocation=False
class ReportCitationTlocation(Report,Tone,TaskDressing,ui.Window):
    """docstring for ReportCitationT."""
    def tasktitle(self):
        return _("Tone Report (by frames)")
        # "Make Reports on Citation Form Sorting in Tone Frames")
        # return _("Report on one slice of Citation Forms (in Tone Frames)")
    def taskicon(self):
        return program['theme'].photo['iconTRep']
    def tooltip(self):
        return _("This report gives you report for one lexical "
                "category, in one syllable profile. \nIt does "
                "this for all data sorted in tone frames, organized by frame.")
    def dobuttonkwargs(self):
        return {'text':"Report!",
                'fn':self.do,
                # column=0,
                'font':'title',
                'compound':'bottom', #image bottom, left, right, or top of text
                'image':self.taskchooser.theme.photo['TRep'],
                'sticky':'ew'
                }
    def __init__(self, parent): #frame, filename=None
        Tone.__init__(self,parent)
        ui.Window.__init__(self,parent)
        self.do=self.tonegroupreport
        TaskDressing.__init__(self,parent)
        Report.__init__(self)
        self.bylocation=True
class ReportCitationBasicT(Report,Comprehensive,Tone,TaskDressing,ui.Window):
    """docstring for ReportCitationT."""
    def tasktitle(self):
        return _("Comprehensive Tone Report")
        # Report on several slices of Citation Forms (in Tone Frames)")
    def taskicon(self):
        return program['theme'].photo['iconTRepcomp']
    def tooltip(self):
        return _("This report gives you reports across multiple lexical "
                "categories, and across multiple syllable profiles. \nIt does "
                "this for all data sorted in tone frames, organized by word.")
    def dobuttonkwargs(self):
        return {'text':"Report!",
                'fn':self.do,
                # column=0,
                'font':'title',
                'compound':'bottom', #image bottom, left, right, or top of text
                'image':self.taskchooser.theme.photo['TRepcomp'],
                'sticky':'ew'
                }
    def __init__(self, parent): #frame, filename=None
        Tone.__init__(self,parent)
        ui.Window.__init__(self,parent)
        self.do=self.tonegroupreportcomprehensive
        # self.do=self.tonegroupreport
        TaskDressing.__init__(self,parent)
        Report.__init__(self)
        self.bylocation=False
"""Task definitions end here"""
class Entry(lift.Entry): #Not in use
    def __init__(self, db, guid, window=None, check=None, problem=None,
        *args, **kwargs):
        self.problem=problem #?!?
        """"This should go elsewhere, when a check is actually done."""
        self.checkresults={}
        lift.Entry.__init__(self, db, guid=guid)
    def addresult(self, check, result):
        """This could be stored under check[guid]; otherwise, how do we want
        to store and access this info?"""
        try:
            self.checkresults[check.name]
        except:
            self.checkresults[check.name]={}
        try:
            self.checkresults[check.name][check.subcheck]
        except:
            self.checkresults[check.name][check.subcheck]={}
        self.checkresults[check.name][check.subcheck]['result']=result
        log.info("Don't forget to write these changes to a file somewhere...")
class DataList(list):
    """docstring for DataList."""
    def appendformsbylang(self,forms,langs,ftype=None,quote=False):
        for l in [f for f in forms if f in langs]:
            # log.info("forms[l]: {}; formstype: {}; ftype: {}"
            #         "".format(forms[l],type(forms[l]),ftype))
            # log.info("typecheck: {}"
            #         "".format(type(forms[l]) is dict))
            # if ftype:
            #     log.info("ftypecheck: {}"
            #         "".format(ftype in forms[l]))
            if forms[l] and type(forms[l]) is not dict:
                f=forms[l]
            elif (type(forms[l]) is dict and
                    ftype and
                    ftype in forms[l] and
                    forms[l][ftype]):
                f=forms[l][ftype]
            else:
                continue
            if quote:
                self.append("‘"+f+"’")
                if ftype:
                    self.append("("+ftype+")")
            else:
                self.append(f)
    def __init__(self, *args):
        super(DataList, self).__init__()
        self.extend(args)
class Glosslangs(DataList):
    """docstring for Glosslangs."""
    def sanitycheck(self):
        """First, remove any duplicates."""
        self.langs(list(set(self)))
        if None in self.langs():
            self.rm(None)
        if len(self) > 2:
            self=self[:2]
            return
        if len(self) < 1:
            ErrorNotice(_("Hey, you have no gloss languages set!"))
    def lang1(self,lang=None):
        if self and not lang:
            return self[0]
        if self:
            self[0]=lang
        else:
            self.append(lang)
        self.sanitycheck()
    def lang2(self,lang=None):
        if len(self) >1:
            if not lang:
                return self[1]
            elif self[0] != lang:
                self[1]=lang
        elif len(self) == 1:
            self.append(lang)
        else:
            log.debug("Tried to set second glosslang, without first set.")
        self.sanitycheck()
    def langs(self,langs=None):
        if langs is None:
            return self
        else:
            n=min(len(langs),2)
            for i in [0,1]:
                if i < len(langs):
                    self[i]=langs[i]
                elif i < len(self):
                    self.pop(i)
    def rm(self,lang):
        """This could be either position, and if lang1 will promote lang2"""
        self.remove(lang)
    def __init__(self, langlist=None):
        super(Glosslangs, self).__init__()
        if langlist:
            self.extend(langlist)
class DictbyLang(dict):
    """docstring for DictbyLang."""
    def getformfromnode(self,node,truncate=False):
        #this assumes *one* value/lang, a second will overwrite.
        #this will comma separate text nodes, if there are multiple text nodes.
        if isinstance(node,lift.ET.Element):
            lang=node.get('lang')
            if truncate: #this gives up to three words, no parens
                text=unlist([rx.glossifydefn(i.text).strip('‘’')
                                                for i in node.findall('text')
                                                if i is not None
                                                if i.text is not None
                                                ])
            else:
                text=unlist([i.text.strip('‘’') for i in node.findall('text')
                                                if i is not None
                                                if i.text is not None
                                                ])
            log.log(4,"Adding {} to {} dict under {}".format(t(text),self,lang))
            self[lang]=text
        else:
            log.info("Not an element node: {} ({})".format(node,type(node)))
            log.info("node.stripped: {} ({})".format(node.strip(),len(node)))
    def frame(self,framedict,langs): #langs can/should be ordered
        """the frame only applies if there is a language value; I hope that's
        what we want..."""
        log.info("Applying frame {} in these langs: {}".format(framedict,langs))
        log.info("Using regex {}".format(rx.framerx))
        ftype=framedict['field']
        for l in [i for i in langs if i in framedict if i in self and self[i]]:
            # log.info("Using lang {}".format(l))
            if ftype in self[l]:
                # log.info("Subbing {} into {}".format(self[l][ftype],framedict[l]))
                t=self[l][ftype]
            else:
                # log.info("Subbing {} into {}".format(self[l],framedict[l]))
                t=self[l]
            if self[l]:
                self.framed[l]=rx.framerx.sub(t,framedict[l])
            else:
                self.framed[l]=None
        log.info("Applied frame: {}".format(self.framed))
    def __init__(self):
        super(DictbyLang, self).__init__()
        self.framed={}
class ExampleDict(dict):
    """This function finds examples in the lexicon for a given tone value,
    in a given tone frame (from check); thus, only sorted data."""
    def senseidsinslicegroup(self,group,check):
        #This returns all the senseids with a given tone value
        if self.params.cvt() == 'T':
            senseids=self.db.get("sense", location=check, path=['tonefield'],
                            tonevalue=group
                            ).get('senseid')
        else:
            ftype=self.params.ftype()
            kwargs={ftype+'annotationname':check,
                    ftype+'annotationvalue':group}
            senseids=self.db.get("sense",
                                    showurl=True,
                                    **kwargs
                                    ).get('senseid')
        if not senseids:
            log.error("There don't seem to be any sensids in this check tone "
                "group, so I can't get you an example. ({} {})"
                "".format(check,group))
            return
        """The above doesn't test for profile, so we restrict that next"""
        senseidsinslice=self.slices.inslice(senseids)
        if not senseidsinslice:
            log.error("There don't seem to be any sensids from that check tone "
                "group in this slice-group, so I can't get you an example. "
                "({}-{}, {} {})"
                "".format(self.slices.ps(),self.slices.profile(),check,group))
            return
        return list(senseidsinslice)
    def hasglosses(self,framed):
        log.info("hasglosses framed: {}".format(framed))
        if framed.glosses():
            self._outdict['framed']=framed
            return True
    def hassoundfile(self,framed):
        if framed.audiofileisthere():
            self._outdict['audiofileisthere']=True
            return True
        else:
            self._outdict['audiofileisthere']=False
    def exampletypeok(self,senseid,check,**kwargs):
        kwargs=exampletype(**kwargs)
        if senseid is None:
            return
        framed=self.datadict.getframeddata(senseid=senseid,check=check)
        if framed is None:
            log.info("getframeddata didn't result in a frame! ({};{})".format(
                                                                senseid,check))
            return
        # log.info("exampletypeok framed: {}".format(framed))
        if kwargs['wglosses'] and not self.hasglosses(framed):
            log.info("Gloss check failed for {}".format(senseid))
            return
        if kwargs['wsoundfile'] and not self.hassoundfile(framed):
            log.info("Audio file check failed for {}".format(senseid))
            return
        self._outdict['senseid']=senseid
        self._outdict['framed']=framed
        return True
    def getexample(self,group,**kwargs):
        check=self.params.check()
        senseids=self.senseidsinslicegroup(group,check)
        if not senseids:
            log.error("There don't seem to be any sensids in this "
                    "check-tonegroup-slice, so I can't get you an example.")
            return
        n=len(senseids)
        self._outdict={'n': n}
        tries=0
        senseid=None #do this once, anyway...
        """hasglosses sets the framed and senseid keys"""
        log.debug("ExampleDict getexample kwargs: {}".format(kwargs))
        while not self.exampletypeok(senseid,check,**kwargs) and tries<n*2:
            # (self.hasglosses(senseid) or noglossesok or tries>n*2):
            tries+=1
            # if tries == n*2: #do this just once
            #     if exampletype['wsoundfile']:
            #         exampletype['wsoundfile']=False
            #     else:
            #         break
            log.debug("ExampleDict getexample kwargs: {}; tries: {}; n: {}"
                                            "".format(kwargs,tries,n))
            if group in self: #.exs:
                if self[group] in senseids: #if stored value is in group
                    if not kwargs['renew']:
                        log.info("Using stored value for ‘{}’ group: ‘{}’"
                                "".format(group, self[group]))
                        senseid=self[group]
                        #don't do this if clause more than once
                        kwargs['renew']=True
                    else:
                        i=senseids.index(self[group])
                        if i == len(senseids)-1: #loop back on last
                            senseid=senseids[0]
                        else:
                            senseid=senseids[i+1]
                        log.info("Using next value for ‘{}’ group: ‘{}’"
                                "".format(group, self[group]))
                else:
                    senseid=senseids[0] #randint(0, len(senseids))-1]
            elif n == 1:
                senseid=senseids[0]
            else:
                log.debug("n: {}".format(n))
                senseid=senseids[randint(0, n-1)]
            self[group]=senseid #store for next iteration
        if tries == n*2: #senseid is None: #not self.hasglosses(senseid):
            log.info("Apparently I tried for a senseid {} times, and couldn't "
            "find one matching your needs ({}) glosses (out of {} possible "
            "senses). This is probably a systematic problem to fix.".format(
                                                                tries,kwargs,n))
        else:
            self[group]=senseid #save for next time
            return self._outdict
    def __init__(self,params,slices,db,datadict):
        self.params=params
        self.slices=slices
        self.db=db
        self.datadict=datadict
        super(ExampleDict, self).__init__()
class FramedDataDict(dict):
    def refresh(self):
        self.clear()
    def updatelangs(self):
        self.analang=self.taskchooser.params.analang()
        self.audiolang=self.taskchooser.settings.audiolang
        self.audiodir=self.taskchooser.settings.audiodir
        self.glosslangs=self.taskchooser.settings.glosslangs
        log.log(4,"analang: {}; glosslangs: {}".format(self.analang,self.glosslangs))
    def isthere(self,source):
        if source in self:
            self[source].updatelangs() #maybe it has been awhile...
            log.debug("source {} already there, using with forms {}"
            "".format(source,self[source].forms))
            return self[source]
    def getframeddata(self, source=None, senseid=None, check=None, **kwargs):
        """Check here is the name of the specific check being run, e.g., V1=V2,
        or the name of a tone frame. This is used in the example @location."""
        """"If this is going to feed a recording (i.e., sound file),
        including the senseid is a good idea, even if not otherwise required."""
        self.updatelangs()
        sense=element=False
        """Is source a valid senseid in the database?"""
        if source:
            if self.db.get('sense', senseid=source).get():
                # log.info("sense?: {}".format(self.db.get('sense', senseid=source).get()))
                sense=True
            if isinstance(source,lift.ET.Element):
                element=True
            # log.info("sense: {}, element: {}".format(sense,element))
        elif senseid and check and self.taskchooser.params.cvt() == 'T':
            """If neither or None is given, try to build it from kwargs"""
            """If these aren't there, these will correctly fail w/KeyError."""
            source=firstoflist(self.db.get('example',
                                            showurl=True,
                                            senseid=senseid,
                                            location=check
                                            ).get('node'))
            element=True
        elif senseid and check:
            source=senseid
            sense=True
        # log.info("sense: {}, element: {} (after build)".format(sense,element))
        d=self.isthere(source)
        if source and not d:
            """certain limited cases have sense w/o check (like page titles)
            or element without senseid (like when not recording)"""
            if sense:
                log.info("getting framed data from sense")
                d=self[source]=FramedDataSense(self,source,check,**kwargs)
            if element:
                log.info("getting framed data from element")
                d=self[source]=FramedDataElement(self,source,senseid,**kwargs)
            log.info("FramedData {} made with forms {}".format(source,d.forms))
        else:
            log.info("FramedData used from ealier ({},with forms {})".format(
                                                                source,d.forms))
        return d #self[source]
    def __init__(self, taskchooser, **kwargs):
        super(FramedDataDict, self).__init__()
        self.frames=taskchooser.settings.toneframes #[ps][name]
        self.db=taskchooser.db
        self.taskchooser=taskchooser
        self.pluralname=taskchooser.settings.pluralname
        self.imperativename=taskchooser.settings.imperativename
class FramedData(object):
    """This is a superclass to store methods, etc. common to both
    FramedDataSense and FramedDataElement, making the information gathered by
    either formatted uniformly in either case."""
    def audio(self):
        if self.audiolang in self.forms:
            self.filename=self.forms[self.audiolang][self.ftype]
            log.info("Found link to audio file {}".format(self.filename))
            return self.filename
    def audiofileisthere(self):
        """This tests the presence of the sound file, which is referred to
        in the LIFT node, assuming there is one."""
        if hasattr(self,'filename'):
            self.filenameURL=str(file.getdiredurl(self.audiodir,self.filename))
            if file.exists(self.filenameURL):
                log.info("Found linked audio file {}".format(self.filename))
                return True
            else:
                if isinstance(self,FramedDataElement):
                    n=self.node.findall(
                                "form[@lang='{lang}'][text='{fn}']"
                                "".format(lang=self.audiolang,fn=self.filename)
                                )
                else:
                    n=self.db.fieldformnode(senseid=senseid,lang=self.audiolang)
                if n:
                    self.node.remove(n[0])
    def reallangs(self):
        if None in self.forms:
            del self.forms[None]
    def updatelangs(self):
        self.analang=self.parent.analang
        self.audiolang=self.parent.audiolang
        self.audiodir=self.parent.audiodir
        self.glosslangs=self.parent.glosslangs
        log.log(4,"analang: {}; glosslangs: {}".format(self.analang,self.glosslangs))
    def gettonegroup(self):
        if hasattr(self,'tonegroups') and self.tonegroups:
            self.tonegroup=unlist(self.tonegroups)
            return True
    def formatted(self,showtonegroup=False,noframe=False):
        ftype=self.parent.taskchooser.params.ftype()
        # if ftype != 'lc': #testing
        #     log.error("ftype is {}; why would that be?".format(ftype))
        #     raise
        tg=None
        if showtonegroup and self.gettonegroup():
            try:
                int(self.tonegroup)  #only for named groups
            except ValueError:
                tg=self.tonegroup
        toformat=DataList(tg)
        if noframe:
            toformat.appendformsbylang(self.forms,self.analang,
                                            ftype=ftype, quote=False)
            toformat.appendformsbylang(self.forms,self.glosslangs,quote=True)
        else:
            """setframe is a FramedDataSense method, so should only apply there,
            but also only be needed there, as FramedDataExample has applynoframe
            in its init."""
            if not hasattr(self,'framed') and isinstance(self,FramedDataSense):
                self.setframe() #self.noframe() #Assume no frame if not explicitly applied
            toformat.appendformsbylang(self.framed,self.analang,
                                            ftype=ftype, quote=False)
            toformat.appendformsbylang(self.framed,self.glosslangs,quote=True)
        return ' '.join([x for x in toformat if x is not None]) #put it all together
    def glosses(self):
        g=DictbyLang()
        l=0
        log.log(4,"self.glosslangs: {}; self.forms: {}".format(self.glosslangs,
                    self.forms))
        for lang in self.glosslangs:
            if lang in self.forms:
                g[lang]=self.forms[lang]
                if g[lang] is not None:
                    l+=len(g[lang])
        if l:
            return g
    def applynoframe(self):
        self.framed=self.forms
    def __init__(self, parent,  **kwargs): #source,
        """Evaluate what is actually needed"""
        super(FramedData, self).__init__()
        self.parent=parent
        self.frames=parent.frames #needed for setframe, parseelement
        self.ps=self.parent.taskchooser.slices.ps()
        # self.cvt=self.parent.taskchooser.params.cvt()
        self.updatelangs()
        self.forms=DictbyLang()
class FramedDataSense(FramedData):
    """This populates an object with attributes to format data for display,
    by senseid. It is called to make the example fields, and pulls form/gloss/etc
    information from the entry, but cannot be used for recording (which
    requires) an example or other node be specified, not a whole sense."""
    def setframe(self,frame=None):
        """This should never be done on an example, which should
        already be framed. Also, self.ps won't be defined, so you'll get
        a key error."""
        if frame is not None and (self.ps in self.frames and
                                    frame in self.frames[self.ps]):
            self.frame=self.frames[self.ps][frame]
            self.forms.frame(self.frame,[self.analang]+self.glosslangs)
            self.framed=self.forms.framed
            self.check=frame
            # log.info("setframe framed: {}".format(self.forms.framed))
        else:
            # log.info("setframe setting no frame")
            self.applynoframe() #enforce the docstring above
        self.tonegroups=self.db.get('example/tonefield/form/text',
                    senseid=self.senseid, location=frame).get('text')
    def parsesense(self,db,senseid,check,ftype):
        self.senseid=senseid #store for later
        # self.ps=unlist(db.ps(senseid=senseid)) #there should be just one
        # log.info("check: {}".format(check))
        # log.info("field: {}; ftype: {}".format(check['field'],ftype))
        if check and 'field' in check and check['field'] != ftype:
            log.error("Check ‘{}’ is for field ‘{}’, but you are looking for "
                        "field ‘{}’".format(check,check['field'],ftype))
        # log.info("self.forms: {}".format(self.forms))
        dictlangs=[self.analang, self.audiolang]
        for lang in dictlangs:
            self.forms[lang]={}
            for ft in ['lx','lc',self.parent.pluralname,
                                    self.parent.imperativename]:
                self.forms[lang][ft]=unlist(db.fieldtext(senseid=senseid,
                                                        ftype=ft,
                                                        analang=lang
                                                            ))
                # log.info("forms: {}".format(self.forms))
            # log.info("forms: {}".format(self.forms))
        glosses=db.glossesordefns(senseid=senseid)
        self.forms.update({k:glosses[k] for k in glosses if k != self.analang})
        #Concatenate lists, not dicts
        for f in [i for i in self.forms if i not in dictlangs]:
            self.forms[f]=unlist(self.forms[f])
        # log.info("forms: {}".format(self.forms))
        #This should maybe be a dict of values? Will need to support that on read
        #For now, this should use the parameter as given, not as iterated
        log.info("parsesense ftype: {}".format(ftype))
        self.group=self.db.fieldvalue(senseid=senseid, name=check, ftype=ftype,
                                        lang=self.analang,
                                        showurl=True
                                        )
        log.info("self.group of parsesense: {}".format(self.group))
    def __init__(self, parent, senseid, check, **kwargs):
        """Evaluate what is actually needed"""
        super(FramedDataSense, self).__init__(parent)
        self.db=parent.db #kwargs.pop('db',None) #not needed for examples
        ftype=kwargs.get('ftype',self.parent.taskchooser.params.ftype())
        if not ftype:
            log.error("ftype: {}!".format(ftype))
            return
        else:
            log.info("ftype: {}".format(ftype))
        if not self.db.get('sense', senseid=senseid).get():
            log.error("You should pass a senseid from your database {} "
                        "({}) to FramedDataSense!".format(source,type(source)))
            return
        self.parsesense(self.db,senseid,check,ftype)
        self.reallangs()
        self.setframe(check)
        # log.info("FramedDataSense initalization done, with forms {}"
        #             "".format(self.forms))
class FramedDataElement(FramedData):
    """This class formats for display a node with form/text elements
    (e.g., examples), without access to senseid or entry guids (parent nodes).
    Example nodes will have forms and glosses, but lc, lx, pl, and imp
    will only have form info. The rest should be added elsewhere
    (e.g., at the top of page/line). This is the class that allows for
    recording into the form[@audiolang] node of that node."""
    def makeaudiofilename(self):
        self.audio()
        if self.audiofileisthere():
            return
        """First check if *any* glosslang has data"""
        self.gloss=None
        for lang in self.glosslangs:
            if lang in self.forms:
                self.gloss=self.forms[lang]
                break #glosslangs are prioritized; take the first one you find.
        """This is for nodes that don't include glosses (lc/lx/pl/imp fields)"""
        if not self.gloss and self.senseid:
            for lang in self.glosslangs:
                self.gloss=t(self.parent.db.get('gloss',
                                            senseid=self.senseid,
                                            glosslang=lang
                                            ).get('text')
                        )
                if self.gloss:
                    self.gloss+='_'+self.node.tag() #since not gloss of the form
                    break
        filenames=self.filenameoptions()
        """if any of the generated filenames are there, stop at the first one"""
        for self.filename in filenames:
            if self.audiofileisthere():
                break
            # self.filenameURL=str(file.getdiredurl(self.audiodir,self.filename))
            # log.debug("Looking for Audio file: {}; filename possibilities: {}; "
            #     "url:{}".format(self.filename, filenames, self.filenameURL))
            # if file.exists(self.filenameURL):
            #     log.debug("Audiofile found! using name: {}; possibilities: {}; "
            #         "url:{}".format(self.filename, filenames, self.filenameURL))
            #     break
        #if you don't find any files, the *last* values are used below
        if not self.audiofileisthere(): #file.exists(self.filenameURL):
            log.debug("No audio file found, but ready to record using name: "
                        "{}; url:{}".format(self.filename, self.filenameURL))
        return self.filename, self.filenameURL
    def filenameoptions(self):
        """This should generate possible filenames, with preferred (current
        schema) last, as that will be used if none are found."""
        ps=self.parent.taskchooser.slices.ps()
        pslocopts=[ps]
        # Except for data generated early in 2021, profile should not be there,
        # because it can change with analysis. But we include here to pick up
        # old files, in case they are there but not linked.
        # First option (legacy):
        pslocopts.insert(0,ps+'_'+self.parent.taskchooser.slices.profile())
        fieldlocopts=[None]
        if (self.node.tag == 'example'):
            l=self.node.find("field[@type='location']//text")
            if hasattr(l,'text') and l.text is not None:
                #the last option is taken, if none are found
                pslocopts.insert(0,ps+'-'+l.text) #the first option.
                fieldlocopts.append(l.text) #make this the last option.
                # Yes, these allow for location to be present twice, but
                # that should never be found, nor offered
        filenames=[]
        """We iterate over lots of filename schemas, to preserve legacy data.
        This is only really needed (and so could be removed at some point) when
        data has been recorded but no link is in place, for whatever reason.
        If there is a link to a real sound file, that is covered above.
        If there is no sound file, then the below will result in the default
        (current) schema."""
        # log.info("forms at this point: {}".format(self.forms))
        for pslocopt in pslocopts:
            for fieldlocopt in fieldlocopts: #for older name schema
                for legacy in ['_', None]:
                    for tags in [ None, 1 ]:
                        args=[self.senseid]
                        if tags is not None:
                            args+=[self.node.tag]
                            if self.node.tag == 'field':
                                args+=[self.node.get("type")]
                        if not self.analang in self.forms:
                            log.error("No {} analang in {} (forms: {})".format(
                                        self.analang,self.senseid,self.forms))
                            return
                        args+=[self.forms[self.analang][self.ftype]]
                        if self.gloss: #could be None still, if no senseid given
                            args+=[
                                    self.gloss
                                    ]
                        optargs=args[:]
                        optargs.insert(0,pslocopt) #put first
                        optargs.insert(3,fieldlocopt) #put after self.node.tag
                        log.log(3,optargs)
                        wavfilename=''
                        argsthere=[x for x in optargs if x is not None]
                        for arg in argsthere:
                            wavfilename+=arg
                            if argsthere.index(arg) < len(argsthere)-1:
                                wavfilename+='_'
                        if legacy == '_': #There was a schema that had an extra '_'.
                            wavfilename+='_'
                        wavfilename=rx.urlok(wavfilename) #one character check
                        filenames+=[wavfilename+'.wav']
        return filenames
    def parseelement(self,node):
        self.node=node #We don't have access to this here
        for i in node: # Example, lc, lx, pl, and imp
            if i.tag == 'form': #language forms, not glosses, etc, below.
                self.forms.getformfromnode(i)
            elif (((i.tag == 'translation') and
                (i.get('type') == 'Frame translation')) or
                ((i.tag == 'gloss'))):
                for ii in i:
                    if (ii.tag == 'form'):
                        self.forms.getformfromnode(ii) #glosses
            elif ((i.tag == 'field') and (i.get('type') == 'location')):
                self.check=unlist([j.text for j in i.findall('form/text')])
            elif ((i.tag == 'field') and (i.get('type') == 'tone')):
                self.tonegroups=[j.text for j in i.findall('form/text')]
        if node.tag == 'citation':
            self.ftype='lc'
        elif node.tag == 'lexeme': #used?
            self.ftype='lx'
        elif node.tag == 'field':
            self.ftype=node.get('type')
        elif self.ps in self.frames and (self.check in self.frames[self.ps] and
                                'field' in self.frames[self.ps][self.check]):
            self.ftype=self.frames[self.ps][self.check]['field']
        else:
            log.error("Couldn't get filed type. Frames: {}".format(self.frames))
            log.error("Node tag:{}; type: {}; ps: {}; check: {}; analang: {}; audiolang: {}"
                    "".format(
                            node.tag,
                            node.get('type'),
                            getattr(self,'ps',"AttrNotFound"),
                            getattr(self,'check',"AttrNotFound"),
                            getattr(self,'analang',"AttrNotFound"),
                            getattr(self,'audiolang',"AttrNotFound")
                                )
                    )
        for lang in [self.analang, self.audiolang]:
            if lang in self.forms:
                try:
                    self.forms[lang][self.ftype]=self.forms[lang]
                except TypeError:
                    self.forms[lang]={self.ftype:self.forms[lang]}
    def __init__(self, parent, node, senseid=None, **kwargs):
        if not isinstance(node,lift.ET.Element):
            log.error("You should pass an element ({}) to FramedDataExample!"
                        "".format(type(node)))
            return
        self.senseid=senseid
        super(FramedDataElement, self).__init__(parent)
        self.parseelement(node) #example element, not sense or entry:
        self.reallangs()
        if not self.forms:
            log.error("Sorry, somehow {} didn't result in forms: {}; {}/{}"
                    "".format(senseid,self.forms,node,type(node)))
            return
        if hasattr(self,'tonegroups') and unlist(self.tonegroups) == 'NA':
            log.error("Sorry, this example was skipped in sorting")
            self.framed='NA'
            return
        self.applynoframe() #because we want self.framed=self.forms
        self.makeaudiofilename() #generate self.filename and self.filenameURL
        """This is what we're pulling from:
        <example>
            <form lang="gnd"><text>ga təv</text></form>
            <translation type="Frame translation">
                <form lang="fr"><text>lieu (m), place (f) (pl)</text></form>
            </translation>
            <field type="tone">
                <form lang="fr"><text>1</text></form>
            </field>
            <field type="location">
                <form lang="fr"><text>Plural</text></form>
            </field>
        </example>
        """
        # log.info("FramedDataElement initalization done, with forms: {}"
        #             "".format(self.forms))
class MainApplication(ui.Window):
    def setmasterconfig(self): #,program
        """Configure variables for the root window (master)"""
        for rc in [0,2]:
            self.parent.grid_rowconfigure(rc, weight=3)
            self.parent.grid_columnconfigure(rc, weight=3)
    def __init__(self,parent,exit=0):
        start_time=time.time() #this enables boot time evaluation
        """Things that belong to a ui.Frame go after this:"""
        super(MainApplication,self).__init__(parent,
                exit=False
                )
        """Pick one of the following three screensizes (or don't):"""
        # self.fullscreen()
        # self.quarterscreen()
        # self.master.minsize(1200,400)
        """Do I want this?"""
        # self.parent.maxsize(
        #                     self.parent.winfo_screenwidth()-200,
        #                     self.parent.winfo_screenheight()-200
        #                     )
        #Might be needed for M$ windows:root.state('zoomed')
        # super().__init__(parent,class_="AZT")
        self.withdraw()
        """Set up the frame in this (mainapplication) frame. This will be
        'placed' in the middle of the mainapplication frame, which is
        gridded into the center of the root window. This configuration keeps
        the frame with all the visual stuff in the middle of the window,
        without letting the window shrink to really small."""
        """Pick one of these two placements:"""
        # self.frame.place(in_=self, anchor="c", relx=.5, rely=.5)
        # self.frame.grid(column=0, row=0)
        """This means make check with
        this app as parent
        the root window as base window, and
        the root window as the master window, from which new windows should
        inherit attributes
        """
        """Do any check tests here"""
        """Make the rest of the mainApplication window"""
        # e=(_("Exit"))
        """Do this after we instantiate the check, so menus can run check
        methods"""
        # ui.ContextMenu(self)
        # filechooser=FileChooser()
        tasks=TaskChooser(self)
        print("Finished loading main window in",time.time() - start_time," "
                                                                    "seconds.")
        """finished loading so destroy splash"""
        """Don't show window again until check is done"""
class SortButtonFrame(ui.ScrollingFrame):
    """This is the frame of sort group buttons."""
    def getanotherskip(self,parent,vardict):
        """This function presents a group of buttons for the user to choose
        from, after one for each tone group in that location/ps/profile in the
        database. It provides one for the user to indicate that the word doesn't
        belong in any of those (new group), and one to for the user to
        indicate that the word/frame combo doesn't work (skip)."""
        def firstok():
            vardict['ok'].set(True)
            remove(okb) #use this button exactly once
            differentbutton()
            sortnext()
        def different():
            vardict['NONEOFTHEABOVE'].set(True)
            sortnext()
        def skip():
            vardict['skip'].set(True)
            sortnext()
        def remove(x):
            x.destroy()
        def sortnext():
            self.sortitem.destroy()
        def differentbutton():
            vardict['NONEOFTHEABOVE']=ui.BooleanVar()
            difb=ui.Button(bf, text=newgroup,
                        cmd=different,
                        anchor="w",
                        font='instructions'
                        )
            difb.grid(column=0, row=0, sticky="ew")
        row=0
        firstOK=_("This word is OK in this frame")
        newgroup=_("Different")
        skiptext=_("Skip this item")
        """This should just add a button, not reload the frame"""
        row+=10
        bf=ui.Frame(parent)
        bf.grid(column=0, row=row, sticky="w")
        if not self.status.groups(wsorted=True):
            vardict['ok']=ui.BooleanVar()
            okb=ui.Button(bf, text=firstOK,
                            cmd=firstok,
                            anchor="w",
                            font='instructions'
                            )
            okb.grid(column=0, row=0, sticky="ew")
        else:
            differentbutton()
        vardict['skip']=ui.BooleanVar()
        skipb=ui.Button(bf, text=skiptext,
                        cmd=skip,
                        anchor="w",
                        font='instructions'
                        )
        skipb.grid(column=0, row=1, sticky="ew")
    def addgroupbutton(self,group):
        if self.exitFlag.istrue():
            return #just don't die
        scaledpady=int(50*program['scale'])
        b=ToneGroupButtonFrame(self.groupbuttons, self, self.exs,
                                group,
                                showtonegroup=True,
                                alwaysrefreshable=True,
                                bpady=scaledpady,
                                row=self.groupbuttons.row,
                                column=self.groupbuttons.col,
                                sticky='w')
        self.groupvars[group]=b.var()
        if not self.buttoncolumns or (self.buttoncolumns and
                                    self.groupbuttons.row+1<self.buttoncolumns):
            self.groupbuttons.row+=1
        else:
            self.groupbuttons.col+=1
            self.groupbuttons.col%=self.buttoncolumns # from 0 to cols-1
            if not self.groupbuttons.col:
                self.groupbuttons.row+=1
            elif self.groupbuttons.row+1 == self.buttoncolumns:
                self.groupbuttons.row=0
        # log.info("Next button at r:{}, c:{}".format(groupbuttons.row,
        #                                             groupbuttons.col))
        self.groupbuttonlist.append(b)
        self._configure_canvas()
    def addtonegroup(self):
        log.info("Adding a tone group!")
        values=[0,] #always have something here
        groups=self.status.groups(wsorted=True)
        for i in groups:
            try:
                values+=[int(i)]
            except:
                log.info('Tone group {} cannot be interpreted as an integer!'
                        ''.format(i))
        newgroup=max(values)+1
        groups.append(str(newgroup))
        return str(newgroup)
    def sortselected(self,senseid,framed):
        selectedgroups=selected(self.groupvars)
        log.info("selectedgroups: {}".format(selectedgroups))
        for k in self.groupvars:
            log.info("{} value: {}".format(k,self.groupvars[k].get()))
        if len(selectedgroups)>1:
            log.error("More than one group selected: {}".format(
                                                            selectedgroups))
            return 2
        groupselected=unlist(selectedgroups)
        if groupselected in self.groupvars:
            self.groupvars[groupselected].set(False)
        else:
            log.error("selected {}; not in {}".format(groupselected,self.groupvars))
            return
        if groupselected:
            if groupselected in ["NONEOFTHEABOVE",'ok']:
                """If there are no groups yet, or if the user asks for
                another group, make a new group."""
                group=self.addtonegroup()
                """And give the user a button for it, for future words
                (N.B.: This is only used for groups added during the current
                run. At the beginning of a run, all used groups have buttons
                created above.)"""
                """Can't thread this; the button needs to find data"""
                self.marksortgroup(senseid,framed,group,write=False)
                self.addgroupbutton(group)
                #adjust window for new button
                self.windowsize()
                log.debug('Group added: {}'.format(groupselected))
                """group with the above?"""
                """Group these last two?"""
            else:
                if groupselected == 'skip':
                    group='NA'
                else:
                    group=groupselected
                log.debug('Group selected: {} ({})'.format(group,
                                                            groupselected))
                """This needs to *not* operate on "exit" button."""
                """thread here?"""
                # self.marksortgroup(senseid,framed,group=group,write=False)
                t = threading.Thread(target=self.marksortgroup,
                                    args=(senseid,framed,group),
                                    kwargs={'write':False})
                t.start()
        else:
            log.debug('No group selected: {}'.format(groupselected))
            return 1 # this should only happen on Exit
        self.status.marksenseidsorted(senseid)
        self.maybewrite()
    def __init__(self, parent, task, groups, *args, **kwargs):
        super(SortButtonFrame, self).__init__(parent, *args, **kwargs)
        """Children of self.runwindow.frame.scroll.content"""
        self.groupbuttons=self.content.groups=ui.Frame(self.content,
                                                row=0,column=0,sticky="ew")
        self.content.anotherskip=ui.Frame(self.content, row=1,column=0)
        """Children of self.runwindow.frame.scroll.content.groups"""
        self.groupbuttons.row=0 #rows for this frame
        self.groupbuttons.col=0 #columns for this frame
        self.groupvars={}
        self.groupbuttonlist=list()
        # entryview=ui.Frame(self.runwindow.frame)
        """We need a few things from the task (which are needed still?)"""
        self.buttoncolumns=task.buttoncolumns
        self.exs=task.exs
        self.status=task.status
        self.marksortgroup=task.marksortgroup
        # self.check=task.params.check()
        # self.cvt=task.params.cvt()
        # self.ftype=task.params.ftype()
        # self.ps=task.slices.ps()
        # self.analang=task.analang
        # self.db=task.db
        self.maybewrite=task.maybewrite
        # self.updatestatus=task.updatestatus
        # self.toneframes=task.settings.toneframes
        for group in groups:
            self.addgroupbutton(group)
        """Children of self.runwindow.frame.scroll.content.anotherskip"""
        self.getanotherskip(self.content.anotherskip,self.groupvars)
        log.info("getanotherskip vardict (1): {}".format(self.groupvars))
class RecordButtonFrame(ui.Frame):
    def _start(self, event):
        log.log(3,"Asking PA to record now")
        self.recorder=sound.SoundFileRecorder(self.filenameURL,self.pa,
                                                                self.settings)
        log.debug("PA recorder made OK")
        self.recorder.start()
    def _stop(self, event):
        try:
            self.recorder.stop()
        except:
            log.info("Couldn't stop recorder; was it on?")
        """This is done in advance of recording now:"""
        self.b.destroy()
        self.makeplaybutton()
        self.makedeletebutton()
        self.addlink()
    def _redo(self, event):
        log.log(3,"I'm deleting the recording now")
        self.p.destroy()
        self.makerecordbutton()
        self.r.destroy()
    def makebuttons(self):
        if file.exists(self.filenameURL):
            self.makeplaybutton()
            self.makedeletebutton()
            self.addlink()
        else:
            self.makerecordbutton()
    def makerecordbutton(self):
        self.b=ui.Button(self,text=_('Record'),command=self.function)
        self.b.grid(row=0, column=0,sticky='w')
        self.b.bind('<ButtonPress>', self._start)
        self.b.bind('<ButtonRelease>', self._stop)
    def _play(self,event=None):
        log.debug("Asking PA to play now")
        self.player=sound.SoundFilePlayer(self.filenameURL,self.pa,
                                                                self.settings)
        tryrun(self.player.play)
    def makeplaybutton(self):
        self.p=ui.Button(self,text=_('Play'),command=self._play)
        #Not using these for now
        # self.p.bind('<ButtonPress>', self._play)
        # self.p.bind('<ButtonRelease>', self.function)
        self.p.grid(row=0, column=1,sticky='w')
        pttext=_("Click to hear this utterance")
        if program['praat']:
            pttext+='; '+_("right click to open in praat")
            self.p.bind('<Button-3>',lambda x: praatopen(self.filenameURL))
        self.pt=ui.ToolTip(self.p,pttext)
    def makedeletebutton(self):
        self.r=ui.Button(self,text=_('Redo'),command=self.function)
        self.r.grid(row=0, column=2,sticky='w')
        self.r.bind('<ButtonRelease>', self._redo)
        self.r.update_idletasks()
    def function(self):
        pass
    def addlink(self):
        if self.test:
            return
        self.db.addmediafields(self.node,self.filename,self.audiolang,
                                # ftype=ftype,
                                write=False)
        self.task.maybewrite()
        self.task.status.last('recording',update=True)
    def __init__(self,parent,task,framed=None,**kwargs): #filenames
        """Uses node to make framed data, just for soundfile name"""
        """Without node, this just populates a sound file, with URL as
        provided. The LIFT link to that sound file should already be there."""
        # This class needs to be cleanup after closing, with check.donewpyaudio()
        """Originally from https://realpython.com/playing-and-recording-
        sound-python/"""
        self.db=task.db
        self.id=id
        self.task=task
        try:
            task.pyaudio.get_format_from_width(1) #get_device_count()
        except:
            task.pyaudio=sound.AudioInterface()
        self.pa=task.pyaudio
        if not hasattr(task.settings,'soundsettings'):
            task.settings.loadsoundsettings()
        self.callbackrecording=True
        self.settings=task.settings.soundsettings
        self.chunk = 1024  # Record in chunks of 1024 samples (for block only)
        self.channels = 1 #Always record in mono
        self.test=kwargs.pop('test',None)
        if framed and framed.framed != 'NA':
            self.audiolang=framed.audiolang
            self.filename=framed.filename
            self.filenameURL=framed.filenameURL
            self.node=framed.node
        elif self.test:
            self.filename=self.filenameURL="test_{}_{}.wav".format(
                                        self.settings.fs, #soundsettings?
                                        self.settings.sample_format)
        else:
            t=_("No framed value, nor testing; can't continue...")
            log.error(t)
            ui.Label(self,text=t,borderwidth=1,font='default',
                    relief='raised').grid(row=0,column=0)
        ui.Frame.__init__(self,parent, **kwargs)
        """These need to happen after the frame is created, as they
        might cause the init to stop."""
        if task.settings.audiolang is None and self.test is not True:
            tlang=_("Set audio language to get record buttons!")
            log.error(tlang)
            ui.Label(self,text=tlang,borderwidth=1,
                relief='raised' #flat, raised, sunken, groove, and ridge
                ).grid(row=0,column=0)
            return
        if None in [self.settings.fs, self.settings.sample_format,
                    self.settings.audio_card_in,
                    self.settings.audio_card_out]:
            text=_("Set all sound card settings"
                    "\n(Do|Recording|Sound Card Settings)"
                    "\nand a record button will be here.")
            log.debug(text)
            ui.Label(self,text=text,borderwidth=1,
                relief='raised' #flat, raised, sunken, groove, and ridge
                ).grid(row=0,column=0)
            return
        self.makebuttons()
class ToneGroupButtonFrame(ui.Frame):
    def again(self):
        """Do I want this? something less drastic?"""
        for child in self.winfo_children():
            child.destroy()
        self.makebuttons()
        self.update_idletasks()
        if self.kwargs['playable'] and self._playable:
            self.player.play()
    def select(self):
        self._var.set(True)
    def sortnext(self):
        self.kwargs['canary'].destroy()
    def remove(self):
        self.destroy() # will this keep the variable around, if stored elsewhere?
    def selectnremove(self):
        self.select()
        self.remove()
    def selectnsortnext(self):
        self.select()
        self.sortnext()
    def selectnlabelize(self):
        self.select()
        self.kwargs['label']=True
        self.again()
        self.sortnext()
        # remove()
    def unsort(self):
        self.check.removesenseidfromgroup(self._senseid,sorting=False)
        self.refresh()
    def setcanary(self,canary):
        if canary.winfo_exists():
            self.kwargs['canary']=canary
        else:
            log.error("Not setting non-existant canary {}; ".format(canary))
    def var(self):
        return self._var
    def getexample(self,**kwargs):
        kwargs=exampletype(**kwargs)
        example=self.exs.getexample(self.group,**kwargs)
        if not example or 'senseid' not in example:
            if kwargs['wsoundfile']:
                log.error("self.exs.getexample didn't return an example "
                                    "with a soundfile; trying for one without")
                kwargs['wsoundfile']=False
                example=self.exs.getexample(self.group,**kwargs)
                if not example or 'senseid' not in example:
                    log.error("self.exs.getexample didn't return an example "
                                        "with or without sound file; returning")
                    return
            else:
                log.error("self.exs.getexample didn't return an example "
                        "(without needing a sound file); returning ({})"
                        "".format(example))
                return
        self._n=example['n']
        framed=example['framed']
        if framed is None:
            check=self.check.params.check()
            log.error("Apparently the framed example for tone group {} in "
                        "frame {} came back {}".format(group,check,example))
            return
        self._senseid=example['senseid']
        if framed.audiofileisthere():
            self._filenameURL=framed.filenameURL
        else:
            self._filenameURL=None
        self._text=framed.formatted(showtonegroup=self.kwargs['showtonegroup'])
        return 1
    def makebuttons(self):
        if self.kwargs['label']:
            self.labelbutton()
        elif self.kwargs['playable']:
            if self._senseid and self._filenameURL:
                self.playbutton()
                self._playable=True
            else: #Label if there is no sound file on any example.
                self.getexample() #shouldn't need renew=True
                self.labelbutton()
                self._playable=False
        else:
            self.selectbutton()
        if self._n > 1 or self.kwargs['alwaysrefreshable']:
            self.refreshbutton()
    """buttons"""
    def labelbutton(self):
        b=ui.Label(self, text=self._text,
                    column=1, row=0, sticky="ew",
                    **self.buttonkwargs()
                    )
    def playbutton(self):
        self.check.pyaudiocheck()
        self.check.soundsettingscheck()
        self.player=sound.SoundFilePlayer(self._filenameURL,self.check.pyaudio,
                                                    self.check.soundsettings)
        b=ui.Button(self, text=self._text,
                    cmd=self.player.play,
                    column=1, row=0,
                    sticky="nesw",
                    **self.buttonkwargs())
        bttext=_("Click to hear this utterance")
        if program['praat']:
            bttext+='; '+_("right click to open in praat")
            b.bind('<Button-3>',lambda x: praatopen(self._filenameURL))
        bt=ui.ToolTip(b,bttext)
        if self.kwargs['unsortable']:
            self.unsortbutton()
    def selectbutton(self):
        if self.kwargs['labelizeonselect']:
            cmd=self.selectnlabelize
        else:
            cmd=self.selectnsortnext
        b=ui.Button(self, text=self._text, cmd=cmd,
                    column=1, row=0, sticky="ew",
                    **self.buttonkwargs())
        bt=ui.ToolTip(b,_("Pick this Group"))
    def refresh(self):
        # if renew is True:
        log.info("Resetting tone group example ({}): {} of {} examples with "
                "kwargs: {}".format(self.group,self.exs[self.group],self._n,
                                                                self.kwargs))
        # del self[self.group]
        self.kwargs['renew']=True
        self.kwargs['alwaysrefreshable']=True
        self.getexample(**self.kwargs)
        self.again()
    def refreshbutton(self):
        tinyfontkwargs=self.buttonkwargs()
        del tinyfontkwargs['font'] #so it will fit in the circle
        bc=ui.Button(self, image=self.theme.photo['change'], #🔃 not in tck
                        cmd=self.refresh,
                        text=str(self._n),
                        compound='center',
                        column=0,
                        row=0,
                        sticky="nsew",
                        **tinyfontkwargs)
        bct=ui.ToolTip(bc,_("Change example word"))
    def unsortbutton(self):
        t=_("<= remove *this* *word* from \nthe group (sort into another, later)")
        usbkwargs=self.buttonkwargs()
        usbkwargs['wraplength']=usbkwargs['wraplength']*2/3
        b_unsort=ui.Button(self,text = t,
                            cmd=self.unsort,
                            column=2,row=0,padx=50,
                            **usbkwargs
                            )
    def buttonkwargs(self):
        """This is a method to allow pulling these args after updating kwargs"""
        bkwargs=self.kwargs.copy()
        for arg in self.unbuttonargs:
            del bkwargs[arg]
        return bkwargs #only the kwargs appropriate for buttons
    def __init__(self, parent, check, exdict, group, **kwargs):
        self.exs=exdict
        self.check=check #this is the task/check
        self.group=group
        # self,parent,group,row,column=0,label=False,canary=None,canary2=None,
        # alwaysrefreshable=False,playable=False,renew=False,unsortable=False,
        # **kwargs
        # From check, need
        # check=self.params.check()
        # setframe
        # self.getex
        # self.exs[group]
        # self.parent.photo (inherit?)
        self.parent=parent
        # inherit(self)
        # make sure these variables are there:
        kwargs['font']=kwargs.pop('font','read')
        kwargs['anchor']=kwargs.get('anchor','w')
        kwargs['showtonegroup']=kwargs.pop('showtonegroup',False)
        kwargs['wraplength']=kwargs.pop('wraplength',False)
        # kwargs['refreshcount']=kwargs.pop('refreshcount',-1)+1
        # kwargs['sticky']=kwargs.pop('sticky',"ew")
        frameargs={} #kwargs.copy()
        defaults={'sticky':'',
                    'rowspan': 1,
                    'columnspan': 1
                    }
        for f in ['row','column','sticky',
                    'rowspan',
                    'columnspan',
                    'padx',
                    'pady',
                    'ipadx',
                    'ipady',
                    ]:
            frameargs[f]=kwargs.pop(f,defaults.get(f,0))
        self.unbuttonargs=['renew','canary','labelizeonselect',
                            'label','playable','unsortable',
                            'alwaysrefreshable','wsoundfile',
                            'showtonegroup',
                            ]
        for arg in self.unbuttonargs:
            kwargs[arg]=kwargs.pop(arg,False)
        if kwargs['playable']:
            kwargs['wsoundfile']=True
        #set this for buttons:
        kwargs['ipady']=kwargs.pop('bipady',defaults.get('bipady',15))
        kwargs['ipady']=kwargs.pop('bipadx',defaults.get('bipadx',15))
        kwargs['pady']=kwargs.pop('bpady',defaults.get('bpady',0))
        kwargs['pady']=kwargs.pop('bpadx',defaults.get('bpadx',0))
        self.kwargs=kwargs
        self._var=ui.BooleanVar()
        super(ToneGroupButtonFrame,self).__init__(parent, **frameargs)
        if self.getexample(**kwargs):
            self.makebuttons()
        # """Should I do this outside the class?"""
        # self.grid(column=column, row=row, sticky=sticky)
class Splash(ui.Window):
    def __init__(self, parent):
        parent.withdraw()
        super(Splash, self).__init__(parent,exit=0)
        title=(_("{name} Dictionary and Orthography Checker").format(
                                                        name=program['name']))
        self.title(title)
        v=_("Version: {}".format(program['version']))
        text=_("Your dictionary database is loading...\n\n"
                "{name} is a computer program that accelerates community"
                "-based language development by facilitating the sorting of a "
                "beginning dictionary by vowels, consonants and tone. "
                "(more in help:about)").format(name=program['name'])
        l=ui.Label(self.frame, text=title, pady=10,
                        font='title',anchor='c',padx=25,
                        row=0,column=0,sticky='we'
                        )
        m=ui.Label(self.frame, text=v, anchor='c',padx=25,
                        row=1,column=0,sticky='we'
                        )
        n=ui.Label(self.frame, image=self.theme.photo['transparent'],text='',
                        row=2,column=0,sticky='we'
                        )
        o=ui.Label(self.frame, text=text, padx=50,
                wraplength=int(self.winfo_screenwidth()/2),
                row=3,column=0,sticky='we'
                )
        self.withdraw() #don't show until placed
        self.update_idletasks()
        self.w = self.winfo_reqwidth()
        x=int(self.master.winfo_screenwidth()/2-(self.w/2))
        self.h = self.winfo_reqheight()
        y=int(self.master.winfo_screenheight()/2 -(self.h/2))
        self.geometry('+%d+%d' % (x, y))
        self.deiconify() #show after placement
        self.update()
class Analysis(object):
    """Currently for tone, but sorting out values by group"""
    """The following two functions analyze the similarity of UF groups and
    locations/checks with respect to the correlation between other and
    the surface tone group value for that UF-check combination."""
    def allvaluesbycheck(self):
        self.valuesbycheck=dictofchilddicts(self.valuesbygroupcheck,
                                                remove=['NA',None])
    def allvaluesbygroup(self):
        self.valuesbygroup=dictofchilddicts(self.valuesbycheckgroup,
                                                remove=['NA',None])
    def compareUFs(self): #was prioritize
        """Prioritize groups by similarity of location:value pairings"""
        """This is already in the order to compare"""
        self.comparisonUFs=dictscompare(self.valuesbygroupcheck,
                                        ignore=['NA',None,'None'],
                                        flat=False)
        self.orderedUFs=flatten(self.comparisonUFs)
        log.debug("structured groups: {}".format(self.comparisonUFs))
    def comparechecks(self):
        """Prioritize locations by similarity of location:value pairings"""
        """we need to switch the hierarchy to make this comparison"""
        vbcg=self.valuesbycheckgroup={}
        for group in self.valuesbygroupcheck:
            for check in self.valuesbygroupcheck[group]:
                """This removes the 'values' layer, and promotes check
                above group"""
                try:
                    vbcg[check][group]=self.valuesbygroupcheck[group][check]
                except KeyError:
                    vbcg[check]={}
                    vbcg[check][group]=self.valuesbygroupcheck[group][check]
        self.comparisonchecks=dictscompare(vbcg,
                                            ignore=['NA',None,'None'],
                                            flat=False)
        self.orderedchecks=flatten(self.comparisonchecks)
        log.debug("structured locations: {}".format(self.comparisonchecks))
    def checkgroupsbysenseid(self):
        """outputs dictionary keyed to [senseid][location]=group"""
        self.senseiddict={}
        for senseid in self.senseids:
            self.senseiddict[senseid]={}
            for check in self.checks:
                group=self._db.get("example/tonefield/form/text",
                    senseid=senseid,location=check).get('text')
                if group: #store location:group by senseid
                    self.senseiddict[senseid][check]=group
        # log.info("Done collecting groups by location for each senseid.")
        return self.senseiddict #was output
    def sorttoUFs(self):
        """Input is a dict keyed by location, valued with location:group dicts
        Returns groups by location:value correspondences."""
        # This is the key analytical step that moves us from a collection of
        # surface forms (each pronunciation group in a given context) to the
        # underlying form (which behaves the same as others in its group,
        # across all contexts).
        if not hasattr(self,'senseiddict'):
            log.error("You have to run checkgroupsbysenseid first")
            return
        unnamed={}
        # Collect all unique combinations of location:group pairings.
        for senseid in self.senseiddict:
            #sort into groups by dict values (combinations location:group pairs)
            k=str(self.senseiddict[senseid])
            try:
                unnamed[k].append(senseid)
            except KeyError:
                unnamed[k]=[senseid]
        # log.info("Done collecting combinations of groups values "
        #         "by location: {}".format(unnamed))
        # self.groups={}
        self.valuesbygroupcheck={}
        self.senseidsbygroup={}
        ks=list(unnamed) #keep sorting order
        for k in ks:
            x=ks.index(k)+1
            name=self.ps+'_'+self.profile+'_'+str(x)
            # self.groups[name]={}
            # self.groups[name]['values']=ast.literal_eval(k) #return str to dict
            self.valuesbygroupcheck[name]=ast.literal_eval(k) #return str to dict
            # self.groups[name]['senseids']=unnamed[k]
            self.senseidsbygroup[name]=unnamed[k]
            for senseid in unnamed[k]:
                self._db.addtoneUF(senseid,name,analang=self.analang,
                                    write=False)
        # log.info("Done adding senseids to groups.")
        # return self.groups
    def tonegroupsbyUFcheckfromLIFT(self):
        #returns dictionary keyed by [group][location]=groupvalue
        values=self.valuesbygroupcheck={}
        # Collect check:value correspondences, by sense
        for group in self.senseidsbygroup:
            values[group]={}
            for check in self.checks: #just make them all, delete empty later
                values[group][check]=list()
                for senseid in self.senseidsbygroup[group]:
                    groupvalue=self._db.get("example/tonefield/form/text",
                                            senseid=senseid, location=check,
                                            ).get('text')
                    if groupvalue:
                        if unlist(groupvalue) not in values[group][check]:
                            values[group][check]+=groupvalue
                log.log(3,"values[{}][{}]: {}".format(group,check,
                                                    values[group][check]))
                if not values[group][check]:
                    log.info(_("Removing empty {} key from {} values"
                                "").format(check,group))
                    del values[group][check] #don't leave key:None pairs
        # log.info("Done collecting groups by location/check for each UF group.")
    def senseidsbyUFsfromLIFT(self):
        """This returns a dict of {UFtonegroup:[senseids]}"""
        log.debug(_("Looking for sensids by UF tone groups for {}-{}").format(
                    self.profile, self.ps
                    ))
        self.senseidsbygroup={}
        """Still working on one ps-profile combo at a time."""
        for senseid in self.senseids: #I should be able to make this a regex...
            group=firstoflist(self._db.get('sense/toneUFfield/form/text',
                                                senseid=senseid).get('text'))
            if group is not None:
                try:
                    self.senseidsbygroup[group].append(senseid)
                except:
                    self.senseidsbygroup[group]=[senseid]
        return self.senseidsbygroup #?
    def donoUFanalysis(self):
        log.info("Reading tone group analysis from UF tone fields")
        self.senseidsbyUFsfromLIFT() # > self.senseidsbygroup
        self.tonegroupsbyUFcheckfromLIFT() # > self.valuesbygroupcheck
        self.doanyway()
    def do(self):
        log.info("Starting tone group analysis from lift examples")
        self.checkgroupsbysenseid() # > self.senseiddict
        self.sorttoUFs() # > self.senseidsbygroup and self.valuesbygroupcheck
        self._db.write()
        self.doanyway()
        self._status.last('analysis',update=True)
    def doanyway(self):
        """compare(x=UFs/checks) give self.comparison(x) and self.ordered(x)"""
        self.comparechecks() #also self.valuesbygroupcheck -> …checkgroup
        self.compareUFs()
        self.allvaluesbycheck() # >self.valuesbycheck
        self.allvaluesbygroup() # >self.valuesbygroup
    def setslice(self,**kwargs):
        self.ps=kwargs.get('ps',self._slices.ps())
        self.profile=kwargs.get('profile',self._slices.profile())
        self.checks=self._status.checks(ps=self.ps,profile=self.profile)
        self.senseids=self._slices.senseids(ps=self.ps,profile=self.profile)
    def __init__(self, params, slices, status, db, **kwargs):
        super(Analysis, self).__init__()
        self._params=params
        self._slices=slices
        self._status=status
        self._db=db
        self.analang=self._params.analang()
        self.setslice(**kwargs)
class SliceDict(dict):
    """This stores and returns current ps and profile only; there is no check
    here that the consequences of the change are done (done in check)."""
    def count(self):
        try:
            return self[(self._profile,self._ps)]
        except KeyError:
            return 0
    def scount(self,scount=None):
        """This just stores/returns the values in a dict, keyed by [ps][s]"""
        if scount is not None:
            self._scount=scount
        return self._scount
    def makepsok(self):
        pss=self.pss()
        if not hasattr(self,'_ps') or self._ps not in pss:
            self.ps(pss[0])
    def makeprofileok(self):
        if not hasattr(self,'_ps'):
            self.makepsok()
        profiles=self.profiles()
        try:
            profiles+=self.adhoc()[self._ps].keys()
        except KeyError:
            log.info("There seem to be no ad hoc {} groups.".format(self._ps))
        if (not hasattr(self,'_profile')
                or self._profile not in profiles):
            self.profile(profiles[0])
    def pss(self):
        return self._pss
    def ps(self,ps=None):
        pss=self.pss()
        if ps is not None and ps in pss:
            """This needs to renew checks, if t == 'T'"""
            self._ps=ps
            self.makeprofileok() #keyed by ps
            self.renewsenseids()
        elif ps is not None:
            log.error("You asked to change to ps {}, which isn't in the list "
                        "of pss: {}".format(ps,pss))
        else:
            # self.makepsok()
            return self._ps
    def profiles(self,ps=None):
        """This returns profiles for either a specified ps or the current one"""
        if ps is None:
            ps=self.ps()
        return self._profiles[ps]
    def profile(self,profile=None):
        if profile is not None and profile in self.profiles(self._ps):
            self._profile=profile
            self.renewsenseids()
        else:
            # self.makeprofileok() #is this actually needed here? check elsewhere
            return self._profile
    def nextps(self):
        pss=self.pss()
        try:
            index=sepss.index(self._ps)
            if index+1 == len(pss):
                self.ps(pss[0]) #cycle back
            else:
                self.ps(pss[index+1])
        except ValueError: #i.e., it's not in the list
            self.makepsok()
        return self.ps()
    def slicepriority(self,arg=None):
        """arg is to throw away, rather than break a fn where others get
        and set. This is now calculated, not read from file and set here."""
        self.validate()
        self._sliceprioritybyps={}
        try:
            s=self._slicepriority=[x for x in self._valid.items()]
            s.sort(key=lambda x: int(x[1]),reverse=True)
            log.debug("self._valid: {}".format(self._valid))
            for ps in dict.fromkeys([x[1] for x in self._valid]):
                s=self._sliceprioritybyps[ps]=[x for x in self._valid.items()
                                                            if x[0][1] == ps]
                s.sort(key=lambda x: int(x[1]),reverse=True)
        except Exception as e:
            log.error("Most likely a non-integer found when looking for an "
                        "integer in {} (error: {})".format(s,e))
    def pspriority(self):
        if self._slicepriority is not None:
            self._pss=list(dict.fromkeys([x[0][1]
                                for x in self._slicepriority]))[:self.maxpss]
    def profilepriority(self):
        if not hasattr(self,'_profiles'):
            self._profiles={}
        for ps in self.pss():
            slicesbyhzbyps=self._sliceprioritybyps[ps]
            if slicesbyhzbyps is not None:
                self._profiles[ps]=list(dict.fromkeys([x[0][0]
                                for x in slicesbyhzbyps]))[:self.maxprofiles]
    def valid(self, ps=None):
        if ps is None:
            return self._valid
        elif ps in self._validbyps:
            return self._validbyps[ps]
        else:
            log.error("You asked for valid ps data, but that ps isn't there.")
    def validate(self):
        self._valid={}
        self._validbyps={}
        for k in [x for x in self if x[0] != 'Invalid']:
            self._valid[k]=self[k]
        for ps in dict.fromkeys([x[1] for x in self._valid]):
            self._validbyps[ps]=[x for x in self._valid if x[1] == ps]
        log.info("valid: {}".format(self._valid))
        log.info("validbyps: {}".format(self._validbyps))
    def inslice(self,senseids):
        senseidstochange=set(self._senseids).intersection(senseids)
        return senseidstochange
    def senseids(self,ps=None,profile=None):
        """This returns an up to date list of senseids in the curent slice
        (because changing ps or profile calls renewsenseids), or else the
        specified slice"""
        # list(self._senseidsbyps[self._ps][self._profile])
        if not ps and not profile:
            return self._senseids #this is always the current slice
        else:
            if not ps:
                ps=self._ps
            if not profile:
                profile=self._profile
            return list(self._profilesbysense[ps][profile]) #specified slice
    def senseidsbyps(self,ps):
        return self._senseidsbyps[ps]
    def makesenseidsbyps(self):
        """These are not distinguished by profile, just ps"""
        self._senseidsbyps={}
        for ps in self._profilesbysense:
            self._senseidsbyps[ps]=[]
            for prof in self._profilesbysense[ps]:
                self._senseidsbyps[ps]+=self._profilesbysense[ps][prof]
    def renewsenseids(self):
        self._senseids=[]
        try:
            self._senseids+=list(self._profilesbysense[self._ps][self._profile])
        except KeyError:
            log.info("assuming {} is an ad hoc profile.".format(self._profile))
        try:
            self._senseids+=list(self._adhoc[self._ps][self._profile])
        except KeyError:
            log.info("assuming {} is a regular profile.".format(self._profile))
    def adhoc(self,ids=None, **kwargs):
        """If passed ids, add them. Otherwise, return dictionary."""
        if ids is not None:
            ps=kwargs.get('ps',self.ps())
            profile=kwargs.get('profile',self.profile())
            if ps not in self._adhoc:
                 self._adhoc[ps]={}
            self._adhoc[ps][profile]=ids
        return self._adhoc
    def adhoccounts(self,ps=None):
        if ps is None:
            ps=self._ps
        if not hasattr(self,'_adhoccounts'):
            self.updateadhoccounts()
        if not self._adhoccounts:
            return {}
        # return [x for x in self._adhoccounts if x[1] == ps]
        return self._adhoccounts #this should return a dictionary
    def updateadhoccounts(self):
        """This iterates across self.profilesbysense to provide counts for each
        ps-profile combination (aggregated for profile='Invalid'??!?)
        it should only be called when creating/adding to self.profilesbysense"""
        profilecountInvalid=0
        wcounts=list()
        for ps in self._adhoc:
            for profile in self._adhoc[ps]:
                count=len(self._adhoc[ps][profile])
                wcounts.append((count, profile, ps))
        self._adhoccounts={}
        for i in sorted(wcounts,reverse=True):
            self._adhoccounts[(i[1],i[2])]=i[0]
    def updateslices(self):
        """This iterates across self.profilesbysense to provide counts for each
        ps-profile combination (aggravated for profile='Invalid')
        It sets this dictionary class with k:v of (profile,ps):count.
        it should only be called when creating/adding to self.profilesbysense"""
        profilecountInvalid=0
        wcounts=list()
        for ps in self._profilesbysense:
            for profile in self._profilesbysense[ps]:
                if profile == 'Invalid':
                    profilecountInvalid+=len(self._profilesbysense[ps][profile])
                count=len(self._profilesbysense[ps][profile])
                wcounts.append((count, profile, ps))
        for i in sorted(wcounts,reverse=True):
            self[(i[1],i[2])]=i[0] #[(profile, ps)]=count
        log.info('Invalid entries found: {}'.format(profilecountInvalid))
    def __init__(self,checkparameters,adhoc,profilesbysense): #dict
        """The slice dictionary depends on check parameters (and not vice versa)
        because changes in slice options (ps or profile) change check options,
        and not vice versa (check options are only presented based on current
        cvt and slice)"""
        super(SliceDict, self).__init__()
        self.checkparameters=checkparameters
        self.profilecountsValid=0
        self.profilecounts=0
        self.maxprofiles=None
        self.maxpss=None
        self._adhoc=adhoc
        self._profilesbysense=profilesbysense #[ps][profile]
        self.updateslices() #any time we add to self._profilesbysense
        """These two are only done here, as the only change with new data"""
        self.slicepriority()
        self.pspriority()
        self.profilepriority() #this is a dict with ps keys, so can do once.
        self.makesenseidsbyps()
        """This will be redone, but should be done now, too."""
        self.makeprofileok() #so the next won't fail
        self.renewsenseids()
class ToneFrames(dict):
    def addframe(self,ps,name,defn):
        """This needs to change checks"""
        if not isinstance(defn,dict):
            log.error("The supplied frame definition isn't a dictionary: {}"
                        "".format(defn))
        elif name in self:
            log.error("The supplied frame name is already there: {} ({})"
                        "".format(name,defn))
        else:
            if not ps in self:
                self[ps]={}
            self[ps][name]=defn
    def __init__(self, dict):
        super(ToneFrames, self).__init__()
        for k in dict:
            self[k]=dict[k]
class StatusDict(dict):
    """This stores and returns current ps and profile only; there is no check
    here that the consequences of the change are done (done in check)."""
    """I should think about what 'do' means here: sort? verify? record?"""
    def checktosort(self,**kwargs):
        check=kwargs.get('check',self._checkparameters.check())
        cvt=kwargs.get('cvt',self._checkparameters.cvt())
        ps=kwargs.get('ps',self._slicedict.ps())
        profile=kwargs.get('profile',self._slicedict.profile())
        if (cvt not in self or
                ps not in self[cvt] or
                profile not in self[cvt][ps] or
                check not in self[cvt][ps][profile] or
                self[cvt][ps][profile][check]['tosort'] == True):
            return True
    def checktojoin(self,**kwargs):
        check=kwargs.get('check',self._checkparameters.check())
        cvt=kwargs.get('cvt',self._checkparameters.cvt())
        ps=kwargs.get('ps',self._slicedict.ps())
        profile=kwargs.get('profile',self._slicedict.profile())
        if (cvt in self and
                ps in self[cvt] and
                profile in self[cvt][ps] and
                check in self[cvt][ps][profile] and
                ('tojoin' not in self[cvt][ps][profile][check] or #old schema
                self[cvt][ps][profile][check]['tojoin'] == True)):
            return True
    def profiletojoin(self,**kwargs):
        profile=kwargs.get('profile',self._slicedict.profile())
        cvt=kwargs.get('cvt',self._checkparameters.cvt())
        ps=kwargs.get('ps',self._slicedict.ps())
        checks=self.checks()
        for check in checks: #any check
            if (cvt in self and
                ps in self[cvt] and
                profile in self[cvt][ps] and
                check in self[cvt][ps][profile] and
                ('tojoin' not in self[cvt][ps][profile][check] or #old schema
                self[cvt][ps][profile][check]['tojoin'] == True)):
                return True
    def profiletosort(self,**kwargs):
        profile=kwargs.get('profile',self._slicedict.profile())
        cvt=kwargs.get('cvt',self._checkparameters.cvt())
        ps=kwargs.get('ps',self._slicedict.ps())
        checks=self.checks()
        for check in checks: #any check
            if (cvt not in self or
                ps not in self[cvt] or
                profile not in self[cvt][ps] or
                check not in self[cvt][ps][profile] or
                self[cvt][ps][profile][check]['tosort'] == True):
                return True
    def nextprofile(self, **kwargs):
        """This function is here (not in slices) in order for it to be sensitive
        to different kinds of profiles, via **kwargs"""
        kwargs=grouptype(**kwargs)
        # self.makeprofileok()
        profiles=self.profiles(**kwargs)
        if not profiles:
            log.error("There are no such profiles! kwargs: {}".format(kwargs))
            return
        """"TypeError: string indices must be integers"""
        profile=self._slicedict.profile()
        nextprofile=profiles[0]
        if profile in profiles:
            idx=profiles.index(profile)
            if idx != len(profiles)-1:
                nextprofile=profiles[idx+1]
        self._slicedict.profile(nextprofile)
        return True
    def nextcheck(self, **kwargs):
        kwargs=grouptype(**kwargs)
        check=self._checkparameters.check()
        checks=self.checks(**kwargs)
        if not checks:
            log.error("There are no such checks! kwargs: {}".format(kwargs))
            return
        nextcheck=checks[0] #default
        if check in checks:
            idx=checks.index(check)
            if idx != len(checks)-1: # i.e., not already last
                nextcheck=checks[idx+1] #overwrite default in this one case
        self._checkparameters.check(nextcheck)
        return True
    def nextgroup(self, **kwargs):
        kwargs=grouptype(**kwargs)
        group=self.group()
        groups=self.groups(**kwargs)
        if not groups:
            log.error("There are no such groups! kwargs: {}".format(kwargs))
            return
        nextgroup=groups[0] #default
        if group in groups:
            idx=groups.index(group)
            if idx != len(groups)-1: # i.e., not already last
                nextgroup=groups[idx+1] #overwrite default in this one case
        self.group(nextgroup)
    def profiles(self, **kwargs):
        kwargs=grouptype(**kwargs)
        profiles=self._slicedict.profiles() #already limited to current ps
        p=[]
        for kwargs['profile'] in profiles:
            checks=self.checks(**kwargs)
            if kwargs['wsorted'] and not checks:
                log.log(4,"No Checks for this profile, returning.")
                continue #you won't find any profiles to do, either...
            if (
                (not kwargs['wsorted'] and not kwargs['tosort']) or
                (kwargs['tosort'] and self.profiletosort(**kwargs)) or
                (kwargs['wsorted'] and [i for j in
                            # [self.groups(profile=profile,check=check,**kwargs)
                            [self.groups(**kwargs)
                            # for check in checks]
                            for kwargs['check'] in checks]
                                        for i in j
                                        ]) or
                kwargs['tojoin'] and self.profiletojoin(**kwargs)
                ):
                p+=[kwargs['profile']]
        log.log(4,"Profiles with kwargs {}: {}".format(kwargs,p))
        return p
    def checks(self, **kwargs):
        """This method is designed for tone, which depends on ps, not profile.
        we'll need to rethink it, when working on CV checks, which depend on
        profile, and not ps."""
        kwargs=grouptype(**kwargs)
        cs=[]
        checks=self.updatechecksbycvt(**kwargs)
        for kwargs['check'] in checks:
            if (
                (not kwargs['wsorted'] and not kwargs['tosort']
                and not kwargs['toverify']
                and not kwargs['tojoin']
                ) or
                # """These next two assume current ps-profile slice"""
                kwargs['wsorted'] and self.groups(**kwargs) or
                kwargs['tosort'] and self.checktosort(**kwargs) or
                kwargs['toverify'] and self.groups(**kwargs) or
                kwargs['tojoin'] and self.checktojoin(**kwargs)
                ):
                cs+=[kwargs['check']]
        log.log(4,"Checks with {}: {}".format(kwargs,cs))
        return cs
    def groups(self,g=None, **kwargs): #was groupstodo
        log.log(4,"groups kwargs: {}".format(kwargs))
        kwargs=grouptype(**kwargs)
        kwargs=self.checkslicetypecurrent(**kwargs)
        """Without a kwarg, this returns prioritization in advance of sorting,
        before actual sort groups exist. So that usage only has meaning for
        segmental checks, and should not be used for tone. For tone usage,
        ALWAYS specify a kwarg here."""
        """I don't know how to prioritize CV checks yet, if ever..."""
        sn=self.node(**kwargs)
        if kwargs['wsorted']: #this used to be the default: get or set sorted groups
            self._groups=sn['groups']
            if g is not None:
                self._groups=sn['groups']=g
            return self._groups
        if kwargs['toverify']:
            return list(set(sn['groups'])-set(sn['done']))
        if kwargs['torecord']:
            return list(set(sn['groups'])-set(sn['recorded']))
        else: #give theoretical possibilities (C or V only)
            """The following two are meaningless, without with kwargs above"""
            if kwargs['cvt'] in ['CV','T']:
                return None
            """This is organized class:(segment,count)"""
            thispsdict=self._slicedict.scount()[kwargs['ps']]
            if kwargs['cvt'] == 'V': #There is so far only one V grouping
                todo=[i[0] for i in thispsdict['V']] #that's all that's there, for now.
            elif kwargs['cvt'] == 'C':
                todo=list() #because there are multiple C groupings
                for s in thispsdict:
                    if s != 'V':
                        todo.extend([i[0] for i in thispsdict[s]])
                        #list of tuples
            return todo
    def senseidstosort(self): #,ps=None,profile=None
        return self._idstosort
    def senseidssorted(self): #,ps=None,profile=None
        return self._idssorted
    def renewsenseidstosort(self,todo,done):
        """This takes arguments to remove and rebuild these lists"""
        """todo and done should be lists of senseids"""
        """this takes as arguments lists extracted from LIFT by the check"""
        if not hasattr(self,'_idssorted'):
            self._idssorted=[]
        if not hasattr(self,'_idstosort'):
            self._idstosort=[]
        self._idssorted.clear()
        self._idssorted.extend(done)
        self._idstosort.clear()
        self._idstosort.extend(todo)
    def marksenseidsorted(self,senseid):
        self._idssorted.append(senseid)
        if senseid in self._idstosort:
            self._idstosort.remove(senseid)
        if not self._idstosort:
            self.tosort(False)
            log.log(4,"Tosort now {} (marksenseidsorted)".format(self.tosort()))
    def marksenseidtosort(self,senseid):
        if not hasattr(self,'_idstosort') or not self._idstosort:
            self.tosort(True)
        self._idstosort.append(senseid)
        log.log(4,"Tosort now {} (marksenseidtosort)".format(self.tosort()))
        if senseid in self._idssorted:
            self._idssorted.remove(senseid)
    def store(self):
        """This will just store to file; reading will come from check."""
        log.log(4,"Saving status dict to file")
        config=ConfigParser()
        config['status']=self #getattr(o,s)
        with open(self._filename, "w", encoding='utf-8') as file:
            config.write(file)
    def dict(self): #needed?
        for k in self:
            v[k]=self[k]
        return v
    def dictcheck(self,**kwargs):
        kwargs=self.checkslicetypecurrent(**kwargs)
        try:
            """Build this explicitly to avoid recursion group-check-node"""
            """presorted is the most recently added key"""
            t=self[kwargs['cvt']][kwargs['ps']][kwargs['profile']][kwargs['check']]
            s=t['groups']
            s=t['done']
            s=t['recorded']
            s=t['tosort']
        except (KeyError,TypeError):
            self.build(**kwargs)
    def build(self,**kwargs):
        """this makes sure that the dictionary structure is there for work you
        are about to do"""
        kwargs=checkslicetype(**kwargs) #fills in with None
        """Only build up to a None value"""
        """If anything is defined, give no defaults"""
        """Any defined variable after any default is an error"""
        """We don't want to mix default and specified values here, so
        unspecified after specified is None, and not built"""
        if (kwargs['cvt'] is None and kwargs['ps'] is not None
                or kwargs['ps'] is None and kwargs['profile'] is not None
                or kwargs['profile'] is None and kwargs['check'] is not None
                ):
            log.error("You have to define all values prior to the last: "
                                    "{}".format(kwargs))
        elif kwargs['cvt'] is not None:
            log.log(4,"At least cvt value defined; using them: {}"
                                            "".format(kwargs))
        else: #all None:
            for k in ['cvt','ps','profile','check']:
                del kwargs[k]
            kwargs=self.checkslicetypecurrent(**kwargs) #use current values
        changed=False
        """cvt should never be None here. Once an attribute is None, the rest
        should be, too."""
        if not kwargs['cvt']:
            log.error("Sorry, no cvt defined! ({})".format(kwargs['cvt']))
            raise
        if kwargs['cvt'] not in self:
            self[kwargs['cvt']]={}
            changed=True
        base=self[kwargs['cvt']]
        if kwargs['ps'] is not None:
            if kwargs['ps'] not in base:
                base[kwargs['ps']]={}
                changed=True
            base=base[kwargs['ps']]
        if kwargs['profile'] is not None:
            if kwargs['profile'] not in base:
                base[kwargs['profile']]={}
                changed=True
            base=base[kwargs['profile']]
        if kwargs['check'] is not None:
            if kwargs['check'] not in base:
                base[kwargs['check']]={}
                changed=True
            base=base[kwargs['check']]
        if None not in [kwargs['ps'],kwargs['profile'],kwargs['check']]:
            if isinstance(base,list):
                log.info("Updating {}-{} status dict to new schema".format(
                                            kwargs['profile'],kwargs['check']))
                groups=base
                base=self[kwargs['cvt']][kwargs['ps']][kwargs['profile']][
                                                        kwargs['check']]={}
                base['groups']=groups
                base['done']=[]
                base['recorded']=[]
                base['tosort']=True
                base['presorted']=False
                changed=True
            for key in ['groups','done','recorded']:
                if key not in base:
                    log.log(4,"Adding {} key to {}-{} status dict".format(
                                        key,kwargs['profile'],kwargs['check']))
                    base[key]=list()
                    changed=True
            if 'tosort' not in base:
                log.log(4,"Adding tosort key to {}-{} status dict".format(
                                        key,kwargs['profile'],kwargs['check']))
                base['tosort']=True
                changed=True
            if 'presorted' not in base:
                log.log(4,"Adding presorted key to {}-{} status dict".format(
                                        key,kwargs['profile'],kwargs['check']))
                base['presorted']=False
                changed=True
        if changed == True:
            self.store()
    def cull(self):
        """This iterates across the whole dictionary, and removes empty nodes.
        Only do this when you're cleaning up, not about to start new work."""
        ts=list(self)
        for t in ts:
            pss=list(self[t])
            for ps in pss:
                profiles=list(self[t][ps]) #actual, not theoretical
                for profile in profiles:
                    checks=list(self[t][ps][profile]) #actual, not theoretical
                    for check in checks:
                        node=self[t][ps][profile][check]
                        if type(node) is list:
                            if not node:
                                del self[t][ps][profile][check]
                        elif node['groups'] == []:
                            if node['done'] != []:
                                log.error("groups verified, but not present!")
                            del self[t][ps][profile][check]
                    if self[t][ps][profile] == {}:
                        del self[t][ps][profile]
                if self[t][ps] == {}:
                    del self[t][ps]
            if self[t] == {}:
                del self[t]
    """The following four methods address where to find what in this dict"""
    def updatechecksbycvt(self,**kwargs):
        """This just pulls the correct list from the dict, and updates params"""
        """It doesn't allow for input, as other fns do"""
        cvt=kwargs.get('cvt',self._checkparameters.cvt())
        if cvt not in self._checksdict:
            self._checksdict[cvt]={}
            self.renewchecks(**kwargs)
        if cvt == 'T':
            """This depends on ps and self.toneframes"""
            ps=kwargs.get('ps',self._slicedict.ps())
            if ps not in self._checksdict[cvt]:
                self._checks=[] #there may be none defined
            else:
                self._checks=self._checksdict[cvt][ps]
        else:
            profile=kwargs.get('profile',self._slicedict.profile())
            if profile not in self._checksdict[cvt]:
                self.renewchecks(**kwargs) #should be able to find something
            self._checks=self._checksdict[cvt][profile]
        return self._checks
    def renewchecks(self,**kwargs):
        """This should only need to be done on a boot, when a new tone frame
        is defined, or when working on a new syllable profile for CV checks."""
        """This depends on cvt and profile, for CV checks"""
        """replaces self.checkspossible"""
        """replaces setnamesbyprofile"""
        cvt=kwargs.get('cvt',self._checkparameters.cvt())
        # t=self._checkparameters.cvt()
        if not cvt:
            log.error("No type is set; can't renew checks!")
        if cvt not in self._checksdict:
            self._checksdict[cvt]={}
        if cvt == 'T':
            toneframes=self.toneframes()
            for ps in self._slicedict.pss():
                if ps in toneframes:
                    self._checksdict[cvt][ps]=list(toneframes[ps])
        else:
            """This depends on profile only"""
            profile=kwargs.get('profile',self._slicedict.profile())
            n=profile.count(cvt)
            log.debug('Found {} instances of {} in {}'.format(n,cvt,profile))
            self._checksdict[cvt][profile]=list()
            for i in range(n): # get max checks and lesser
                if i+1 >6:
                    log.info("We aren't doing checks with more than 6 "
                            "consonants or vowels ({} in {}); If you need "
                            "that, please let me know.".format(i+1,profile))
                    continue
                """This is a list of (code, name) tuples"""
                syltuples=self._checkparameters._checknames[cvt][i+1] #range+1 = syl
                self._checksdict[cvt][profile].extend(
                                                    [t[0] for t in syltuples])
                # log.info("Check codes to date: {}".format(
                #                                 self._checksdict[cvt][profile]
                #                                         ))
            self._checksdict[cvt][profile].sort(
                                            key=lambda x:len(x[0]),reverse=True)
            log.info("Check codes found: {}".format(
                                                self._checksdict[cvt][profile]
                                                    ))
    def node(self,**kwargs):
        """This will fail if fed None values"""
        kwargs=self.checkslicetypecurrent(**kwargs)
        self.dictcheck(**kwargs)
        return self[kwargs['cvt']][kwargs['ps']][kwargs['profile']][
                                                                kwargs['check']]
    def tojoin(self,v=None,**kwargs):
        kwargs=self.checkslicetypecurrent(**kwargs) # current value defaults
        sn=self.node(**kwargs)
        ok=[None,True,False]
        if 'tojoin' not in sn:
            sn['tojoin']=True
        self._tojoinbool=sn['tojoin']
        if v is not None:
            self._tojoinbool=sn['tojoin']=v
        return self._tojoinbool
    def presorted(self,v=None,**kwargs):
        kwargs=self.checkslicetypecurrent(**kwargs) # current value defaults
        sn=self.node(**kwargs)
        ok=[None,True,False]
        if v not in ok:
            log.error("presorted value ({}) invalid: OK values: {}".format(v,ok))
        self._presortedbool=sn['presorted']
        if v is not None:
            self._presortedbool=sn['presorted']=v
        return self._presortedbool
    def tosort(self,v=None,**kwargs):
        kwargs=self.checkslicetypecurrent(**kwargs) # current value defaults
        sn=self.node(**kwargs)
        ok=[None,True,False]
        if v not in ok:
            log.error("Tosort value ({}) invalid: OK values: {}".format(v,ok))
        self._tosortbool=sn['tosort']
        if v is not None:
            self._tosortbool=sn['tosort']=v
        return self._tosortbool
    def verified(self,g=None,**kwargs): #cvt=None,ps=None,profile=None,check=None):
        sn=self.node(**kwargs)
        self._verified=sn['done']
        if g is not None:
            self._verified=g
        return self._verified
    def recorded(self,g=None,**kwargs): #cvt=None,ps=None,profile=None,check=None):
        sn=self.node(**kwargs)
        self._recorded=sn['recorded']
        if g is not None:
            self._recorded=g
        return self._recorded
    def update(self,group=None,verified=False,write=True):
        """This function updates the status variable, not the lift file."""
        changed=False
        if group is None:
            group=self.group()
        log.info("Verification before update (verifying {} as {}): {}".format(
                                                group,verified,self.verified()))
        self.build()
        n=self.node()
        if verified == True:
            if group not in n['done']:
                n['done'].append(group)
                changed=True
        if verified == False:
            if group in n['done']:
                n['done'].remove(group)
                changed=True
        if write and changed:
            self.store()
        log.info("Verification after update: {}".format(self.verified()))
        return changed
    def group(self,group=None):
        """This maintains the group we are actually on, pulled from data
        located by current slice and parameters"""
        if group is not None:
            self._group=group
        else:
            return str(getattr(self,'_group',None))
    def renamegroup(self,j,k,**kwargs):
        sn=self.node(**kwargs)
        if j in sn['done']:
            sn['done'][sn['done'].index(j)]=k
        if j in sn['groups']:
            sn['groups'][sn['groups'].index(j)]=k
        if self.group() == j:
            self.group(k)
    def makegroupok(self,**kwargs):
        kwargs=grouptype(**kwargs)
        groups=self.groups(**kwargs)
        if not hasattr(self,'_group'):
             self._group=None #define this attr, one way or another
        if groups != []:
            if self._group not in groups:
                self.group(groups[0])
    def makecvtok(self):
        cvt=self._checkparameters.cvt()
        cvts=self._checkparameters.cvts()
        if cvt not in cvts:
            self._checkparameters.cvt(cvts[0])
    def makecheckok(self, **kwargs): #result None w/no checks
        check=self._checkparameters.check()
        checks=self.checks(**kwargs)
        if check not in checks:
            if checks:
                self._checkparameters.check(checks[0])
            else:
                self._checkparameters.check(unset=True)
    def toneframes(self):
        return self._toneframes
    def checkslicetypecurrent(self,**kwargs):
        """This fills in current values; it shouldn't leave None anywhere."""
        i=kwargs.copy()
        for k,v in i.items():
            if v is None:
                del kwargs[k]
        kwargs['cvt']=kwargs.get('cvt',self._checkparameters.cvt())
        kwargs['ps']=kwargs.get('ps',self._slicedict.ps())
        kwargs['profile']=kwargs.get('profile',self._slicedict.profile())
        kwargs['check']=kwargs.get('check',self._checkparameters.check())
        log.log(4,"Returning checkslicetypecurrent kwargs {}".format(kwargs))
        return kwargs
    def last(self,task,update=False,**kwargs):
        sn=self.node(**kwargs)
        if 'last' not in sn:
            sn['last']={}
        if update:
            sn['last'][task]=now()
            self.store()
        if task in sn['last']:
            return sn['last'][task]
    def __init__(self,checkparameters,slicedict,toneframes,filename,dict):
        """To populate subchecks, use self.groups()"""
        self._filename=filename
        super(StatusDict, self).__init__()
        for k in [i for i in dict if i is not None]:
            self[k]=dict[k]
        self._checkparameters=checkparameters
        self._slicedict=slicedict
        self._toneframes=toneframes
        self._checksdict={}
        self._cvchecknames={}
class CheckParameters(dict):
    """This stores and returns current cvt/type and check only; there is not check
    here that the setting is valid (done in status), nor that the consequences
    of the change are done (done in check)."""
    """None of this is language/project dependent, nor with mutable options"""
    def verify(self):
        t=self.cvt()
        if t not in self._cvts:
            self.cvt(self.cvts()[0])
        """The following are not (yet?) renewed here"""
        check=self.check()
        if check not in self.checks():
            self.check(self.checks()[0])
        group=self.group()
        if check not in self.groups():
            self.group(self.groups()[0])
    def cvt(self,cvt=None):
        """This needs to change checks"""
        if cvt is not None:
            self._cvt=cvt
        elif not hasattr(self,'_cvt'):
            self._cvt=None
        return self._cvt
    def cvts(self):
        """This depends on nothing, so can go anywhere, and shouldn't need to
        rerun. This is a convenience wrapper only."""
        return list(self._cvts)
    def cvtdict(self):
        """This depends on nothing, so can go anywhere, and shouldn't need to
        rerun. This is a convenience wrapper only."""
        return self._cvts
    def check(self,check=None,unset=False):
        """This needs to change/clear subchecks"""
        if unset or check:
            self._check=check
        elif not hasattr(self,'_check'):
            self._check=None
        return self._check
    def cvcheckname(self,code=None):
        if self.cvt() == 'T':
            code='T'
        if not code:
            code=self.check()
        return self._cvchecknames[code]
    def cvchecknamesdict(self):
        """I reconstruct this here so I can look up names intuitively, having
        built the named checks by type and number of syllables."""
        self._cvchecknames={}
        for t in self._checknames:
            for s in self._checknames[t]:
                for tup in self._checknames[t][s]:
                    self._cvchecknames[tup[0]]=tup[1]
    def analang(self,analang=None):
        if analang:
            self._analang=analang
        elif not hasattr(self,'_analang'):
            self._analang=None
        return self._analang
    def ftype(self,ftype=None):
        if ftype:
            self._ftype=ftype
        elif not hasattr(self,'_ftype'):
            self._ftype='lc'
        return self._ftype
    def __init__(self,analang): # had, do I need check? to write?
        """replaces setnamesall"""
        """replaces self.checknamesall"""
        super(CheckParameters, self).__init__()
        self._analang=analang
        self._cvts={
                'V':{'sg':_('Vowel'),'pl':_('Vowels')},
                'C':{'sg':_('Consonant'),'pl':_('Consonants')},
                'CV':{'sg':_('Consonant-Vowel combination'),
                        'pl':_('Consonant-Vowel combinations')},
                'T':{'sg':_('Tone'),'pl':_('Tones')},
                }
        self._checknames={
            "T":{
                1:[("T", _("Tone melody"))]},
            "V":{
                1:[("V1", _("First/only Vowel"))],
                2:[
                    ("V1=V2", _("Same First/only Two Vowels")),
                    ("V1xV2", _("Correspondence of First/only Two Vowels")),
                    ("V2", _("Second Vowel"))
                    ],
                3:[
                    ("V1=V2=V3", _("Same First/only Three Vowels")),
                    ("V3", _("Third Vowel")),
                    ("V2=V3", _("Same Second Two Vowels")),
                    ("V2xV3", _("Correspondence of Second Two Vowels"))
                    ],
                4:[
                    ("V1=V2=V3=V4", "Same First/only Four Vowels"),
                    ("V4", "Fourth Vowel")
                    ],
                5:[
                    ("V1=V2=V3=V4=V5", "Same First/only Five Vowels"),
                    ("V5", "Fifth Vowel")
                    ],
                6:[
                    ("V1=V2=V3=V4=V5=V6", "Same First/only Six Vowels"),
                    ("V6", "Sixth Vowel")
                    ]
                },
            "C":{
                1:[("C1", _("First/only Consonant"))],
                2:[
                    ("C2", _("Second Consonant")),
                    ("C1=C2",_("Same First/only Two Consonants")),
                    ("C1xC2", _("Correspondence of First/only Two Consonants"))
                    ],
                3:[
                    ("C2=C3",_("Same Second Two Consonants")),
                    ("C2xC3", _("Correspondence of Second Two Consonants")),
                    ("C3", _("Third Consonant")),
                    ("C1=C2=C3",_("Same First Three Consonants"))
                    ],
                4:[
                    ("C4", "Fourth Consonant"),
                    ("C1=C2=C3=C4","Same First Four Consonants")
                    ],
                5:[
                    ("C5", "Fifth Consonant"),
                    ("C1=C2=C3=C4=C5","Same First Five Consonants")
                    ],
                6:[
                    ("C6", "Sixth Consonant"),
                    ("C1=C2=C3=C4=C5=C6","Same First Six Consonants")
                    ]
                },
            "CV":{
                1:[
                    # ("#CV1", "Word-initial CV"),
                    ("C1xV1", _("Correspondence of C1 and V1")),
                    # ("CV1", "First/only CV")
                    ],
                2:[
                    # ("CV2", "Second CV"),
                    ("C2xV2", _("Correspondence of C2 and V2")),
                    ("CV1=CV2",_("Same First/only Two CVs")),
                    # ("CV2#", "Word-final CV")
                    ],
                3:[
                    ("CV1=CV2=CV3",_("Same First/only Three CVs")),
                    ("CV3", _("Third CV"))
                    ],
                4:[
                    ("CV1=CV2=CV3=CV4","Same First/only Four CVs"),
                    ("CV4", "Fourth CV")
                    ],
                5:[
                    ("CV1=CV2=CV3=CV4=CV5","Same First/only Five CVs"),
                    ("CV5", "Fifth CV")
                    ],
                6:[
                    ("CV1=CV2=CV3=CV4=CV5=CV6","Same First/only Six CVs"),
                    ("CV6", "Sixth CV")
                    ]
                },
        }
        self.cvchecknamesdict()
class ConfigParser(configparser.ConfigParser):
    def write(self,*args,**kwargs):
        configparser.ConfigParser.write(self,*args,**kwargs,
                                            space_around_delimiters=False)
    def __init__(self):
        super(ConfigParser, self).__init__(
        converters={'list':list},
        delimiters=(' = ', ' : ')
        )
        self.optionxform=str
        self.allow_no_value=True
        # self.converters={'list':list} #lambda x: [i.strip() for i in x.split(',')]
class ErrorNotice(ui.Window):
    """this is for things that I want the user to know, without having
    to find it in the logs."""
    def __init__(self, text, parent=None, title="Error!", wait=False):
        if not parent:
            parent=program['root']
        if title == "Error!":
            title=_("Error!")
        super(ErrorNotice, self).__init__(parent,title=title)
        self.title = title
        self.text = text
        l=ui.Label(self.frame, text=text, row=0, column=0, ipadx=25)
        l.wrap()
        self.attributes("-topmost", True)
        if wait:
            self.wait_window(self)
class Repository(object):
    """docstring for Mercurial Repository."""
    def choruscheck(self):
        rescues=[]
        for file in self.files:
            if file.endswith('.ChorusRescuedFile'):
                rescues.append(file)
        if rescues:
            error=_("You have the following files ( in {}) that need to be "
                    "resolved from Chorus merges:\n {}"
                    "").format(self.url,'\n'.join(rescues))
            log.error(error)
            ErrorNotice(error,title=_("Chorus Rescue files found!"))
            if me:
                exit()
    def add(self,file):
        if not self.alreadythere(file):
            args=["add", str(file)]
            r=self.do(args)
            if r:
                log.info("Hg add: {}".format(r))
            else:
                log.info("Hg add OK".format(r))
    def commit(self,file=None):
        args=["commit", file, '-m', "Autocommit from AZT"]
        if me: #I only want to commit manually to people's repos
            log.info("Not committing as asked: {}".format(args))
            return
        r=self.do([i for i in args if i is not None])
        if r:
            log.info("Hg commit: {}".format(r))
        else:
            log.info("Hg commit OK".format(r))
    def diff(self):
        args=["diff"]
        self.do(args)
    def status(self):
        args=["status"]
        log.info(self.do(args))
    def log(self):
        args=["log"]
        log.info(self.do(args))
    def root(self):
        args=["root"]
        self.root=self.do(args)
    def files(self):
        args=["files"]
        self.files=self.do(args).split('\n')
    def do(self,args):
        cmd=[program['hg'],'--cwd',str(self.url)] #-R
        cmd.extend(args)
        try:
            output=subprocess.check_output(cmd, shell=False)
        except subprocess.CalledProcessError as e:
            output=e.output
        except Exception as e:
            log.info(_("Call to Mercurial ({}) failed: {}").format(args,e))
            return e
        try:
            t=output.decode(sys.stdout.encoding).strip()
        except:
            t=output
        return t
    def alreadythere(self,url):
        if str(file.getreldir(self.url,url)) in self.files:
            log.info(_("URL {} is already in repo {}".format(url,self.url)))
            return True
        else:
            log.info(_("URL {} is not already in repo {}:\n{}".format(url,self.url,self.files)))
    def ignore(self,file):
        if not hasattr(self,'hgignore') or file not in self.hgignore:
            with open(self.hgignorefile,'a') as f:
                f.write(file+'\n')
            self.getignorecontents()
    def ignorecheck(self):
        self.hgignorefile=file.getdiredurl(self.url,'.hgignore')
        if str(self.hgignorefile) in self.files or me:
            log.info("Not creating .hgignore.")
            return
        """First time basic setup here"""
        for x in ['pdf','xcf','XLingPaperPDFTemp','backupBeforeLx2LcConversion',
                    '.txt', '.7z', '.zip']:
            self.ignore(x)
        self.add(self.hgignorefile)
        self.commit()
    def getignorecontents(self):
        with open(self.hgignorefile,'r') as f:
            self.hgignore=f.readlines()
    def __init__(self, url):
        if not program['hg']:
            log.error("Mercurial isn't found on this computer; no repo object.")
            return
        super(Repository, self).__init__()
        self.url = url
        self.files()
        self.choruscheck()
        self.ignorecheck()
        log.info("Mercurial repository object initialized, with {} files."
                "".format(len(self.files)))
class ResultWindow(ui.Window):
    def __init__(self, parent, nowait=False,msg=None,title=None):
        """Can't test for widget/window if the attribute hasn't been assigned,"
        but the attribute is still there after window has been killed, so we
        need to test for both."""
        if title is None:
            title=(_("Result Window"))
        super().__init__(parent,title=title)
        self.lift()
        if not nowait:
            self.wait(msg=msg)
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
    def __init__(self):
        self.value=None
"""These are non-method utilities I'm actually using."""
def now():
    # datetime.datetime.utcnow().isoformat()[:-7]+'Z'
    return datetime.datetime.utcnow().isoformat()#[:-7]+'Z'
def interfacelang(lang=None,magic=False):
    global i18n
    global _
    """Attention: for this to work, _ has to be defined globally (here, not in
    a class or module.) So I'm getting the language setting in the class, then
    calling the module (imported globally) from here."""
    if lang:
        curlang=interfacelang()
        try:
            log.debug("Magic: {}".format(str(_)))
            magic=True
        except:
            log.debug("Looks like translation magic isn't defined yet; making")
        if lang != curlang or magic == False:
            if lang is not None: #lang is not None:
                log.debug("Setting Interface language: {}".format(lang))
                i18n[lang].install()
            else:
                log.debug("Setting Default Interface language: {}".format(curlang))
                i18n[curlang].install()
        else:
            log.debug("Apparently we're trying to set the same interface "
                                            "language: {}={}".format(lang,curlang))
        log.debug(_("Translation seems to be working, using {}"
                                                    "".format(interfacelang())))
    else:
        for lang in i18n:
            try:
                _
                if i18n[lang] == _.__self__:
                    return lang
            except:
                log.debug("_ doesn't look defined yet, returning 'en' as current "
                                                            "interface language.")
                return 'en'
def dictofchilddicts(self,remove=None):
    # This takes a dict[x][y] and returns a dict[y], with all unique values
    # listed for all dict[*][y].
    o={}
    for x in self:
        for y in self[x]:
            if y not in o:
                o[y]=[]
            if type(self[x][y]) is list:
                for z in self[x][y]:
                    o[y].append(z)
            else:
                o[y].append(self[x][y])
    log.info("o:{}".format(o))
    for y in o:
        o[y]= list(dict.fromkeys(o[y]))
        if type(remove) is list:
            for a in remove:
                if a in o[y]:
                    o[y].remove(a)
    return o
def flatten(l):
    log.debug("list to flatten: {}".format(l))
    if type(l) is not list:
        log.debug("{} is not a list; returning nothing.".format(l))
        return
    if l == [] or type(l[0]) is not list:
        log.debug("The first element of {} is not a list; returning nothing."
                    "".format(l))
        return
    return [i for j in l for i in j] #flatten list of lists
def addxofytocorrectplaceinlistoflists(x,y,o):
    for k in o:
        if y in k and k.index(y) == len(k)-1:
            k.append(x)
            return o
        elif y in k and k.index(y) == 0:
            k.insert(0,x)
            return o
        elif y in k:
            o.append([x])
            return o
    #only add for y not in k after going through all of o
    o.append([x])
    return o
def addxofytolistoflists(x,y,o):
    if x not in [i for j in o for i in j]:
        if y in [i for j in o for i in j]:
            o=addxofytocorrectplaceinlistoflists(x,y,o)
        else:
            o.append([x])
    return o
def dictscompare(dicts,ignore=[],flat=True):
    keyswoignore=[k for k in dicts if dicts[k] not in ignore]
    if len(keyswoignore) <= 1:
        log.debug("One or less dict: {}; just returning key.".format(dicts))
        return [keyswoignore] #This should be a list of lists
    l=dictscompare11(dicts,ignore=ignore)
    o=list([],)
    for c in l:
        for x,y in [c[0]]:
            o=addxofytolistoflists(x,y,o)
            o=addxofytolistoflists(y,x,o)
    if flat == False:
        return o
    else:
        return [i for j in o for i in j]
def dictscompare11(dicts,ignore=[]):
    values={}
    for d1 in dicts:
        for d2 in dicts:
            if d2 == d1 or (d2,d1) in values:
                continue
            values[(d1,d2)]=dictcompare(dicts[d1],dicts[d2],ignore=ignore)[0]
    valuelist=[(x,values[x]) for x in values.keys()]
    valuelist.sort(key=lambda x: x[1],reverse=True)
    return valuelist
def dictcompare(x,y,ignore=[]):
    pairs = dict()
    unpairs=dict()
    for k in x:
        if k not in ignore and x[k] not in ignore:
            if k in y and y[k] not in ignore: #Only compare *same* keys
                if x[k] == y[k]:
                    pairs[k] = x[k]
                else:
                    unpairs[k] = (x[k],y[k])
    if len(pairs)+len(unpairs) == 0:
        r=0 #this beats a div0 error
    else:
        r=len(pairs)/(len(pairs)+len(unpairs))
    return (r,pairs,unpairs)
def selected(groupvars):
    return [k for k in groupvars
            if groupvars[k] is not None #necessary?
            if groupvars[k].get() #only those marked True
            ]
def exampletype(**kwargs):
    if not kwargs:
        print(exampletype)
    for arg in ['wglosses']:
        kwargs[arg]=kwargs.get(arg,True)
    for arg in ['renew','wsoundfile']:
        kwargs[arg]=kwargs.get(arg,False)
    log.log(4,"Returning exampletype kwargs {}".format(kwargs))
    return kwargs
def checkslicetype(**kwargs):
    for arg in ['cvt','ps','profile','check']:
        kwargs[arg]=kwargs.get(arg,None)
    log.log(4,"Returning checkslicetype kwargs {}".format(kwargs))
    return kwargs
def grouptype(**kwargs):
    for arg in ['wsorted','tosort','toverify','tojoin','torecord','comparison']:
        kwargs[arg]=kwargs.get(arg,False)
    log.log(4,"Returning grouptype kwargs {}".format(kwargs))
    return kwargs
def unlist(l,ignore=[None]):
    if l and isinstance(l[0],lift.ET.Element):
         log.error("unlist should only be used on text (not node) lists ({})"
                    "".format(l))
         log.error("Element[0] text: {}".format(l[0].text))
         return
    return firstoflist(l,all=True,ignore=ignore)
def firstoflist(l,othersOK=False,all=False,ignore=[None]):
    #rename to unlist
    """This takes a list composed of one item, and returns the item.
    with othersOK=True, it discards n=2+ items; with othersOK=False,
    it throws an error if there is more than one item in the list."""
    if type(l) is not list:
        return l
    if (l is None) or (l == []):
        return
    if all: #don't worry about othersOK yet
        if len(l) > 1:
            ox=[t(v) for v in l[:len(l)-2]] #Should probably always give text
            l=ox+[_(' and ').join([t(v) for v in l[len(l)-2:] if v not in ignore])]
                # for i in range(int(len(output)/2))]
        else:
            l[0]=t(l[0]) #for lists of a single element
        return ', '.join(x for x in l if x not in ignore)
    elif len(l) == 1 or (othersOK == True):
        return l[0]
    elif othersOK == False: #(i.e., with `len(list) != 1`)
        print('Sorry, something other than one list item found: {}'
                '\nDid you mean to use "othersOK=True"? Returning nothing!'
                ''.format(l))
def t(element):
    if type(element) is str:
        return element
    elif element is None:
        return str(None)
    else:
        try:
            return element.text
        except:
            log.debug("Apparently you tried to pull text out of a non element, "
            "and it's not a simple string, either: {}".format(element))
def nonspace(x):
    """Return a space instead of None (for the GUI)"""
    if x is not None:
        return x
    else:
        return " "
def nn(x,oneperline=False,twoperline=False):
    """Don't print "None" in the UI..."""
    if type(x) is list or type(x) is tuple:
        output=[]
        for y in x:
            output+=[nonspace(y)]
        if twoperline: #join every other with ', ', then all with '\n'
            return '\n'.join([', '.join([str(v) for v in output[i*2:i*2 + 2]])
                        for i in range(int(len(output)/2)+1)])
        elif oneperline:
            return '\n'.join(output)
        else:
            return ' '.join(output)
    else:
        return nonspace(x)
def propagate(self,attr):
    """This function pushes an attribute value to all children with that
    attribute already set, for widgets that are already there (changing fonts)
    """
    log.info(self.winfo_children())
    for child in self.winfo_children():
        log.log(2,"working on {}".format(child))
        if hasattr(child,attr):
            log.log(2,"Found {} value for {} attr, setting {} value".format(
            getattr(child,attr),attr,getattr(self,attr)
            ))
            setattr(child,attr,getattr(self,attr))
            propagate(child,attr=attr)
def donothing():
    log.debug("Doing Nothing!")
    pass
def pathseparate(path):
    os=platform.system()
    if os == "Windows":
        sep=';'
    elif os == "Linux":
        sep=':'
    else:
        log.error("What operating system are you running? ({})".format(os))
    return path.split(sep)
def findpath():
    spargs={
            'shell' : False
            }
    try:
        path=os.getenv('PATH')
        #CSIDL_COMMON_DESKTOPDIRECTORY
        #CSIDL_DEFAULT_DESKTOP
        # CSIDL_DESKTOPDIRECTORY
        # CSIDL_DESKTOP
        #subprocess.check_output(["echo","%PATH%"], **spargs)
        log.info("PATH is {}".format(path))
        return path
    except Exception as e:
        log.info("No path found! ({})".format(e))
def findexecutable(exe):
    exeOS=exe
    os=platform.system()
    if os == 'Linux':
        which='which'
        if exe == 'sendpraat':
            exeOS='sendpraat-linux'
    elif os == 'Windows':
        which='where'
        if exe == 'sendpraat':
            exeOS='sendpraat-win.exe'
    elif os == 'Darwin': #MacOS
         which='which'
         if exe == 'sendpraat':
             exeOS='sendpraat-mac'
    else:
        log.error("Sorry, I don't know this OS: {}".format(os))
    # log.info("Looking for {} on {}...".format(exe,os))
    try:
        exeURL=subprocess.check_output([which,exeOS], shell=False)
        program[exe]=exeURL.decode(sys.stdout.encoding).strip()
    except subprocess.CalledProcessError as e:
        log.info("Executable {} search output: {}".format(exe,e.output))
    except Exception as e:
        log.info(_("Search for {} on {} failed: {}").format(exe,os,e))
        return e
    """This needs to be able to handle two answers in series; is this a list of
    two items, or just a long string, maybe with \n?"""
    if exe in program:
        # log.info("program: {}".format(program[exe]))
        # log.info("program type: {}".format(type(program[exe])))
        program[exe]=program[exe].replace('\r','').split('\n') #this will make a list, either way
        for e in program[exe][:]: #Make a copy, to iterate through changes
            #don't allow 'I could find this online for you' values
            if 'Microsoft' in e and 'WindowsApps' in e:
                program[exe].remove(e)
        program[exe]=[i for i in program[exe] if i is not None]
    if exe not in program or program[exe] == []:
        program[exe]=None
    elif len(program[exe]) == 1:
        program[exe]=unlist(program[exe])
        log.info("Executable {} found at {}".format(exe,program[exe]))
    else:
        log.info("Executable {} found multiple items: {}".format(exe,program[exe]))
    if exe == 'praat' and program[exe] and not praatversioncheck():
        findexecutable('sendpraat') #only ask if it would be useful
def praatversioncheck():
    praatvargs=[program['praat'], "--version"]
    versionraw=subprocess.check_output(praatvargs, shell=False)
    try:
        version=pkg_resources.parse_version(
                versionraw.decode(sys.stdout.encoding).strip()
                                        )
    except:
        version=versionraw
    # This is the version at which we don't need sendpraat anymore
    # and where "--hide-picture" becomes available.
    justpraatversion=pkg_resources.parse_version(
                                            'Praat 6.2.04 (December 18 2021)')
    log.info("Found Praat version {}".format(str(version)))
    if version>=justpraatversion:
        log.info("Praat version at or greater than {}".format(justpraatversion))
        return True
    else:
        log.info("Praat version less than {}".format(justpraatversion))
        return False
def pythonmodules():
    log.info("Installing python dependencies")
    if not program['python']:
        log.error("Can't find python; how am I doing this? Put it in your PATH")
        sys.exit()
    installs=[
            ['--upgrade', 'pip', 'setuptools', 'wheel'],
            ['numpy'],
            ['pyaudio'],
            ['Pillow', 'lxml'],
            ['patiencediff']
            ]
    for install in installs:
        pyargs=[program['python'], '-m', 'pip', 'install']
        pyargs.extend(install)
        log.info("Running `{}`".format(' '.join(pyargs)))
        try:
            o=subprocess.check_output(pyargs,shell=False,
                                        stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            o=e.output
        try:
            log.info(o.decode(sys.stdout.encoding).strip())
        except:
            log.info(o) #just give bytes, if encoding isn't correct
def praatopen(file,newpraat=False,event=None):
    """sendpraat is now looked for only where praat version is before
    'Praat 6.2.04 (December 18 2021)', when new functionality was added to
    praat, to allow successive calls to go to the same window.
    The same version also introduced the '--hide-picture' command line option,
    so we only use that when praatversioncheck() passes.
    """
    if not newpraat and 'sendpraat' in program and program['sendpraat']:
        """sendpraat sends the command to a running praat instance. If there
        isn't one, just open praat."""
        praatargs=[program['sendpraat'], "praat", "Read from file... '{}'"
                                                    "".format(file)]
        try:
            o=subprocess.check_output(praatargs,shell=False,
                                        stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            o=e.output
        try:
            t=o.decode(sys.stdout.encoding).strip()
        except:
            t=o
        if t == "sendpraat: Program praat not running.":
            praatopen(file,newpraat=True)
        else:
            log.info("praatoutput: {}".format(t))
    elif program['praat']:
        log.info(_("Trying to call Praat at {}...").format(program['praat']))
        if 'sendpraat' not in program: #don't care about exe, just version check
            praatargs=[program['praat'], "--hide-picture","--open", file]
        else:
            praatargs=[program['praat'], "--open", file]
        subprocess.Popen(praatargs,shell=False) #not run; continue here
    else:
        log.info(_("Looks like I couln't find Praat..."))
def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt): #ignore Ctrl-C
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    log.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
def openweburl(url):
    webbrowser.open_new(url)
def ofromstr(x):
    """This interprets a string as a python object, if possible"""
    """This is needed to interpret [x,y] as a list and {x:y} as a dictionary."""
    try:
        return ast.literal_eval(x)
    except (SyntaxError,ValueError) as e:
        # log.debug("Assuming ‘{}’ is a string ({})".format(x,e))
        return x
def tryrun(cmd):
    try:
        cmd()
    except Exception as e:
        text=_("{} command error: {}\n({})").format(cmd.__name__,e,cmd)
        log.error(text)
        ErrorNotice(text,title=_("{} command error!").format(cmd.__name__))
def sysrestart():
    os.execv(sys.argv[0], sys.argv)
    sys.exit()
def main():
    global program
    log.info("Running main function on {} ({})".format(platform.system(),
                                    platform.platform())) #Don't translate yet!
    root = program['root']=ui.Root(program=program)
    program['theme']=root.theme #ui.Theme(program)
    log.info("Theme name: {}".format(program['theme'].name))
    root.program=program
    root.wraplength=root.winfo_screenwidth()-300 #exit button
    root.wraplength=int(root.winfo_screenwidth()*.7) #exit button
    root.withdraw()
    if platform.system() != 'Linux': #this is only for MS Windows!
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
        log.info("MS Windows screen size: {}".format(screensize))
    # log.info(root.winfo_class())
    # root.className="azt"
    # root.winfo_class("azt")
    # log.info(root.winfo_class())
    """Translation starts here:"""
    myapp = TaskChooser(root) #TaskChooser MainApplication
    myapp.mainloop()
    logsetup.shutdown()
def mainproblem():
    try:
        log.info(_("Starting up help line..."))
        # _
    except:
        def _(x):
            return x
        log.info(_("Starting up help line..."))
    if program['testing'] and me:
        sys.exit()
        exit()
    file=logsetup.writelzma()
    try: #Make this work whether root has run/still runs or not.
        newtk=False
        program['root'].winfo_exists()
        log.info("Root there!")
        errorroot = program['root']
        for w in errorroot.winfo_children():
            w.destroy()
    except:
        errorroot = ui.Root(program=program)
        errorroot.wraplength=int(errorroot.winfo_screenwidth()*.7) #exit button
        newtk=True
        log.info(_("Starting with new root"))
    errorroot.withdraw()
    errorw=ui.Window(errorroot)
    errorw.title(_("Serious Problem!"))
    errorw.mainwindow=True
    l=ui.Label(errorw.frame,text=_("Hey! You found a problem! (details and "
            "solution below)"),justify='left',font='title',
            row=0,column=0
            )
    if exceptiononload:
        durl=('https://github.com/kent-rasmussen/azt/blob/main/INSTALL.md'
                '#dependencies')
        m=ui.Label(errorw.frame,text=_("\nPlease see {}").format(durl),
            justify='left', font='instructions',
            row=1,column=0
            )
        m.bind("<Button-1>", lambda e: openweburl(durl))
        m2=ui.Label(errorw.frame,
            text=_("I have tried to install some Python dependencies for you. "
                    "If everything but ‘patiencediff’ installed "
                    "(see log below), just close this window and {0} "
                    "will restart. "
                    "\nIf you see connectivity errors, check your internet "
                    "connection before running {0} again; we need to "
                    "download some stuff for this.").format(program['name']),
            justify='left', font='instructions',
            wraplength=errorroot.wraplength,
            row=2,column=0
            )
    lcontents=logsetup.contents(50)
    addr=program['Email']
    eurl='mailto:{}?subject=Please help with A→Z+T installation'.format(addr)
    eurl+=('&body=Please replace this text with a description of what you '
            'just tried.'.format(file))
    eurl+=("%0d%0aIf the log below doesn't include the text 'Traceback (most "
            "recent call last): ', or if it happened after a longer work "
            "session, please attach "
            "your compressed log file ({})".format(file))
    eurl+='%0d%0a--log info--%0d%0a{}'.format('%0d%0a'.join(lcontents))
    n=ui.Label(errorw.frame,text=_("\n\nIf this information doesn't help "
        "you fix this, please click on this text to Email me your log (to {})"
        "").format(addr),justify='left', font='default',
        row=3,column=0
        )
    n.bind("<Button-1>", lambda e: openweburl(eurl))
    o=ui.Label(errorw.frame,text=_("The end of {} / {} are below:"
                                "").format(logsetup.getlogfilename(),file),
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
    if not me:
        o.bind("<Button-1>", lambda e: openweburl(eurl))
    scroll.tobottom()
    ui.Button(errorw.outsideframe,text=_("Restart {}").format(program['name']),
                cmd=sysrestart,
                row=1,column=2)
    errorw.wait_window(errorw)
    if newtk: #likely never work/needed?
        errorroot.mainloop() #This has to be the last thing
"""functions which are not (no longer?) used"""
def name(x):
    try:
        name=x.__name__ #If x is a function
        return name
    except:
        name=x.__class__.__name__ #If x is a class instance
        return "class."+name
if __name__ == "__main__":
    """These things need to be done outside of a function, as we need global
    variables."""
    try:
        import ctypes
        log.debug("Scale factor: {}".format(
                    ctypes.windll.shcore.GetScaleFactorForDevice(0)))
    except:
        pass
    sys.excepthook = handle_exception
    thisexe = file.getfile(__file__)
    if hasattr(sys,'_MEIPASS') and sys._MEIPASS is not None:
        program['aztdir']=sys._MEIPASS
    else:
        program['aztdir'] = thisexe.parent
    mt=datetime.datetime.fromtimestamp(thisexe.stat().st_mtime)
    try:
        with file.getdiredurl(program['aztdir'],'.git/HEAD').open(mode='r') as f:
            branchURL=file.getfile(f.read()) #f contains a git branch URL
            branch=branchURL.name.strip()
            if branch != 'main':
                program['version'] += " ({})".format(branch)
    except FileNotFoundError:
        log.info(".git/HEAD File Not Found; assuming this is the main branch.")
    """Not translating yet"""
    log.info("Running {} v{} (main.py updated to {})".format(
                                    program['name'],program['version'],mt))
    log.info("Working directory is {} on {} ".format(program['aztdir'],
                                                    platform.uname().node))
    log.info("Loglevel is {}; starting at {}".format(loglevel,
                                    datetime.datetime.utcnow().isoformat()))
    transdir=file.gettranslationdirin(program['aztdir'])
    i18n={}
    i18n['en'] = gettext.translation('azt', transdir, languages=['en_US'])
    i18n['fr'] = gettext.translation('azt', transdir, languages=['fr_FR'])
    #'sendpraat' now in 'praat', if useful
    for exe in ['praat','hg','ffmpeg','lame','git','python','python3']:
        findexecutable(exe)
    if program['python3']: #be sure we're using python v3
        program['python']=program.pop('python3')
    # i18n['fub'] = gettext.azttranslation('azt', transdir, languages=['fub'])
    if exceptiononload:
        pythonmodules()
        mainproblem()
    else:
        try:
            import profile
            profile.run('main()', 'userlogs/profile.tmp')
            import pstats
            p = pstats.Stats('userlogs/profile.tmp')
            p.sort_stats('cumulative').print_stats(10)
            # main()
        except FileNotFoundError:
            main()
        except SystemExit:
            log.info("Shutting down by user request")
        except KeyboardInterrupt:
            log.info("Shutting down by keyboard interrupt")
        except Exception as e:
            log.exception("Unexpected exception! %s",e)
            mainproblem()
        except:
            import traceback
            log.error("uncaught exception: %s", traceback.format_exc())
            mainproblem()
    sys.exit()
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
        formsbycvs(C,V,"C1","V1")
    def timetest():
                times=1000000000
                out1=timeit.timeit(test, number=times)
                print(out1)
    #timetest() #see which C variable takes more computing time
