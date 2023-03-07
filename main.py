#!/usr/bin/env python3
# coding=UTF-8
"""This file runs the actual GUI for lexical file manipulation/checking"""
program={'name':'A-Z+T',
        'tkinter':True, #for some day
        'production':False, #True for making screenshots (default theme)
        'testing':False, #normal error screens and logs
        'version':'0.9.9', #This is a string...
        'testversionname':'testing', #always have some real test branch here
        'url':'https://github.com/kent-rasmussen/azt',
        'Email':'kent_rasmussen@sil.org'
        }
# program['testing']=True # eliminates Error screens and zipped logs, repos
exceptiononload=False
import platform
program['hostname']=platform.uname().node
import file
if file.getfile(__file__).parent.parent.stem == 'raspy': # if program['hostname'] == 'karlap':
    program['testing']=True #eliminates Error screens and zipped logs
    me=True
    loglevel=6
    # program['testlift']='eng' #portion of filename
    program['testlift']='Demo_en' #portion of filename
    program['testtask']='WordCollectnParse' #Will convert from string to class later
else:
    me=False
    program['production']=True #True for making screenshots (default theme)
    program['testing']=False #True eliminates Error screens and zipped logs
    loglevel='DEBUG'
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
import logsetup
log=logsetup.getlog('root') #not ever a module
logsetup.setlevel(loglevel)
"""My modules, which should log as above"""
import lift
import parser
import openclipart
# import profiles
import setdefaults
import xlp
import urls
import htmlfns
from utilities import *
try:
    import sound
    import transcriber
    program['nosound']=False
except Exception as e:
    program['nosound']=True
    log.error("Problem importing Sound/pyaudio. Is it installed? {}".format(e))
    exceptiononload=True
"""Other people's stuff"""
import datetime
program['start_time'] = datetime.datetime.utcnow()
import threading
import multiprocessing
import itertools
import importlib.util
import collections
from random import randint
if program['tkinter']:
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
import time
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

class HasMenus():
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
        url='{}/TASKS.md'.format(program['docsurl'])
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
        murl='mailto:{}?subject= {} question'.format(program['Email'],
                                                    program['name'])
        maill.bind("<Button-1>", lambda e: openweburl(murl))
    def reverttomainazt(self,event=None):
        #This doesn't care which (test) version one is on
        r=program['repo'].reverttomain()
        log.info("reverttomainazt: {}".format(r))
        if r:
            program['taskchooser'].restart()
    def trytestazt(self,event=None):
        #This only goes to the test version at the top of this file
        self.updateazt()
        r=program['repo'].testversion()
        log.info("trytestazt: {}".format(r))
        if r:
            program['taskchooser'].restart()
    def _removemenus(self,event=None):
        log.info(_("Hiding menus?"))
        if hasattr(self,'menubar'):
            self.menubar.destroy()
            self.menu=False
            self.setcontext()
    def _setmenus(self,event=None):
        # check=self.check
        log.info(_("Showing menus"))
        self.menubar=Menus(self)
        self.config(menu=self.menubar)
        self.menu=True
        self.setcontext()
        self.unbind_all('<Enter>')
    def setcontext(self,context=None):
        self.context.menuinit() #This is a ContextMenu() method
        if not hasattr(self,'menu') or not self.menu:
            self.context.menuitem(_("Show Menus"),self._setmenus)
        else:
            self.context.menuitem(_("Hide Menus"),self._removemenus)
class LiftChooser(ui.Window,HasMenus):
    """this class allows the user to select a LIFT file, including options
    to start a new one (live or demo), or copy from USB."""
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
        dir=file.gethome()
        newfile=file.getnewlifturl(dir,analang.get())
        self.newdirname=newfile.parent
        if not newfile:
            ErrorNotice(_("Problem creating file; does the directory "
                        "already exist?"),wait=True)
            return
        if file.exists(newfile):
            ErrorNotice(_("The file {} already exists! {}").format(newfile),
                                                                wait=True)
            return
        self.wait=ui.Wait(parent=program['root'],msg=_("Setting up new LIFT file now."))
        log.info("Beginning Copy of stock to new LIFT file.")
        self.cawldb=loadCAWL()
        self.stripcawldb()
        self.cawldb.getentries()
        self.cawldb.getsenses()
        self.fillcawldbimages()
        self.copytonewfile(newfile)
        self.wait.close()
        self.newfilelocation(newfile)
        return str(newfile)
    def clonefromUSB(self):
        def makenewrepo(repoclass,mediadir):
            repo=repoclass(mediadir)
            if (hasattr(repo,'files') #fails if no exe
                and repo.exists()): #tests for .code dir
                    log.info(_("Found {} Repository! ({})").format(repo.code,
                                                                    mediadir))
                    dirname=repo.dirname
                    # log.info("repo in {} directory".format(dirname))
                    newdirname=file.getfile(homedir).joinpath(dirname)
                    if newdirname.suffix == '.'+repo.code: #strip this on clone
                        newdirname=newdirname.with_suffix('')
                    if file.exists(newdirname):
                        # log.info("Exists!")
                        msg=_("The directory {} already exists, so I'm "
                                "not going to copy your data there."
                                "\nDo you already have your data on your "
                                "computer? \nIf so, click '{}' on the next "
                                "screen.").format(newdirname,self.other)
                        log.info(msg)
                        ErrorNotice(msg,wait=True)
                        return
                    log.info("cloning repo to {} directory".format(newdirname))
                    repo.clonefromUSB(newdirname)
                    newrepo=repoclass(newdirname)
                    if newrepo.exists():
                        return newrepo
            else:
                log.info("No {} repo at {}".format(repoclass,mediadir))
        log.info("starting clone from USB")
        mediadir=file.getmediadirectory() #ask where it is
        homedir=file.gethome() #don't ask where to put it
        # log.info("Media dir: {}; home: {}".format(mediadir,homedir))
        if not mediadir:
            return
        if not file.exists(homedir): #this should never happen
            ErrorNotice(_("I can't find your home directory ({}); please "
                        "submit a bug report!").format(homedir))
        newrepo=None
        newrepo=makenewrepo(Git,mediadir)
        if not newrepo:
            log.info("trying with Mercurial")
            newrepo=makenewrepo(Mercurial,mediadir)
        if not newrepo: # if there, already exists
            log.error(_("Couldn't find a repository at {}").format(mediadir))
        filename=self.findrepolift(newrepo) #find the lift file
        # log.info("found filename {}".format(filename))
        if filename: #this will be None, if no or multiple *.lift files
            # log.info("using filename {}".format(filename))
            newfile=newrepo.url.joinpath(filename) #make file a url
            # log.info("using newfile {}".format(newfile))
            if file.exists(newfile): #should always be there
                # log.info("notifying newfile {}".format(newfile))
                self.newfilelocation(newfile) #tell user where to find it
                # log.info("returning newfile {}".format(newfile))
                return newfile
            else:
                log.error(_("looks like there was a problem finding "
                            "your new file. ({})").format(newfile))
        else:
            msg=_("It looks like the repository was cloned, but "
                        "I can't find just one lift file."
                        "\nTell {} which file you want to "
                        "Analyze on the next page.").format(program['name'])
            # log.info(msg)
            ErrorNotice(msg,wait=True)
    def findrepolift(self,repo):
        # log.info("Looking for just one LIFT file.")
        l=[i for i in repo.files if str(i).endswith('.lift')]
        if len(l) == 1:
            log.info("Found just one LIFT file: {}".format(l))
            return l[0]
        else:
            # I could, if this becomes a problem, return the shortest filename,
            # or on that contains the ISO code, but I think this is sane enough
            # for now —anyone with more than one *.lift file should know what
            # they're doing
            log.info(_("returned more or less than one lift file! ({})"
                    ).format(l))
    def fillcawldbimages(self):
        log.info("Filling in empty image fields where possible")
        todo=self.cawldb.senses
        # log.info("Filling in {} image fields".format(len(todo)))
        # log.info("Writing to {}".format(file.getimagesdir(self.newdirname)))
        for sense in todo:
            # log.info("Working on line number {}".format(sense.cawln))
            # log.info("Working on sense {}".format(sense.id))
            # log.info("Working with image field {}".format(sense.illustrationvalue()))
            # log.info("Working with image directory {}".format(sense.imgselectiondir))
            # log.info("Image directory present: {}".format(file.exists(sense.imgselectiondir)))
            # log.info("Working with image files {}".format(
            #                                 file.getfilesofdirectory(sense.imgselectiondir)))
            if sense.cawln and not sense.illustrationvalue():
                # log.info("Found CAWL sense without image field")
                if file.exists(sense.imgselectiondir):
                    urls=file.getfilesofdirectory(sense.imgselectiondir)
                    if urls:
                        filename=sense.imagename() #new file name
                        # log.info("Working with image filename {}".format(filename))
                        saveimagefile(urls[0],filename,copyto=file.getimagesdir(self.newdirname)) #just take the first one
                        sense.illustrationvalue(filename)
                # log.info("Setting progress {}".format(todo.index(sense)*100/len(todo)))
                self.wait.progress(todo.index(sense)*100/len(todo))
    def makeCAWLdemo(self):
        title=_("Make a Demo LIFT Database")
        w=ui.Window(program['root'],title=title)
        w.wait(_("Loading Demo Template"))
        w.mainwindow=False
        t=ui.Label(w.frame, text=title, font='title', row=0, column=0)
        inst=_("Which language would you like to study, in this demonstration "
                "of what {} can do?").format(program['name'])
        t=ui.Label(w.frame, text=inst, row=1, column=0, columnspan=2)
        self.cawldb=loadCAWL()
        Settings.langnames(self,self.cawldb.glosslangs)
        opts=[(i,self.languagenames[i]) for i in self.cawldb.glosslangs]
        log.info("Options: {}".format(opts))
        s=ui.ScrollingButtonFrame(w.frame,
                                    optionlist=opts,
                                    command=self.submitdemolang,
                                    window=w, sticky='',
                                    column=0, row=2)
        w.waitdone()
        w.wait_window(w)
        if not hasattr(self,'demolang') or not self.demolang:
            log.info("User exited without selecting a language.")
            return
        else:
            log.info("User selected a language: {}.".format(self.demolang))
        log.info("Done waiting")
        self.stripcawldb()
        self.wait=ui.Wait(parent=program['root'],
                        msg=_("Making Demo Database \n(will restart)"))
        homedir=file.gethome() #don't ask where to put it
        log.info(homedir)
        self.newdirname=file.getfile(homedir).joinpath('Demo_'+self.demolang)
        log.info(self.newdirname)
        file.makedir(self.newdirname)
        newfile=self.newdirname.joinpath('Demo_'+self.demolang+'.lift')
        self.cawldb.getentries()
        self.cawldb.getsenses()
        self.cawldb.convertglosstocitation(self.demolang)
        self.fillcawldbimages()
        log.info(newfile)
        self.copytonewfile(newfile)
        log.info("copytonewfile done")
        self.wait.close()
        self.newfilelocation(newfile)
        log.info("newfilelocation done")
        return str(newfile)
    def stripcawldb(self):
        for n in (self.cawldb.nodes.findall('entry/lexical-unit')+
                    self.cawldb.nodes.findall('entry/citation')):
            for f in n.findall('form'):
                n.remove(f)
        log.info("Stripped stock LIFT file.")
    def submitdemolang(self,choice,window): #event=None):
        log.info("picked {}, from {}".format(choice,self.cawldb.glosslangs))
        if choice in self.cawldb.glosslangs:
            self.demolang=choice
            window.destroy()
    def copytonewfile(self,newfile):
        if 'Demo' in str(newfile):
            type="demo"
        else:
            type="empty"
        log.info("Trying to write {} LIFT file to {}".format(type,newfile))
        try:
            self.cawldb.write(str(newfile))
        except Exception as e:
            log.error("Exception: {}".format(e))
        log.info("Tried to write {} LIFT file to {}".format(type,newfile))
        if file.exists(newfile):
            log.info("Wrote {} LIFT file to {}".format(type,newfile))
    def newfilelocation(self,newfile):
        #Do users care about this?
        return #not for now
        msg=_("Your new LIFT file is at {n}."
                "\nIf you don't want it there, close {azt} and move the whole "
                "{f} folder wherever you like."
                "\nThen open {azt} and tell it where you put the LIFT file."
                ).format(n=newfile,
                        f=file.getfilenamedir(newfile),
                        azt=program['name'])
        # log.info(msg)
        ErrorNotice(msg,title=_("New LIFT file location"),wait=True)
    def setfilename(self,choice,window, event=None):
        self.withdraw()
        if choice == 'New':
            name=self.startnewfile()
        elif choice == 'Other':
            name=file.lift()
        elif choice == 'Clone':
            log.info("trying clone from USB")
            name=self.clonefromUSB()
        elif choice == 'Demo':
            log.info("Making a CAWL demo database")
            name=self.makeCAWLdemo()
        else:
            name=choice
        log.info("self.name: {}".format(name))
        self.deiconify()
        if name:
            self.name=self.filechooser.name=name
            file.writefilename(name)
            self.destroy()
            if hasattr(program['taskchooser'],'splash'):
                program['taskchooser'].splash.deiconify()
    def __init__(self,chooser,filenamelist):
        self.filechooser=chooser
        self.parent=program['root']
        super(LiftChooser, self).__init__(self.parent)
        self.title(_("Select LIFT Database"))
        ui.ContextMenu(self)
        text=_('What do you want to work on?') #LIFT database
        ui.Label(self.frame, text=text, font='title', column=0, row=0)
        optionlist=[('New',_("Start work on a new language"))]
        optionlist+=[('Clone',_("Copy work from a USB drive"))]
        if filenamelist:
            optionlist+=[(f,f) for f in filenamelist] #keep everything a tuple
            self.other=_("Select another database on my computer") #use later
        else:
            self.other=_("Select a database on my computer") #use later
        optionlist+=[('Other',self.other)]
        optionlist+=[('Demo',_("Make a demo database to try out {}"
                                ).format(program['name']))]
        buttonFrame1=ui.ScrollingButtonFrame(self.frame,
                                optionlist=optionlist,
                                command=self.setfilename,
                                window=self,
                                column=0, row=1,
                                bsticky='ew',
                                sticky=''
                                )
        # make mediadir look for *.git
        ui.Label(self.frame, image=program['theme'].photo['small'],
                text=text, font='title', column=1, row=1, ipadx=20)
        # if hasattr(program['taskchooser'],'splash'):
        try:
            program['taskchooser'].splash.withdraw()
        except:
            pass
class FileChooser(object):
    """This class loads the LIFT database from settings, or asks if not there.
    """
    def askwhichlift(self,filenamelist):
        # put right click menu here
        self.name=None # in case of exit
        window=LiftChooser(self,filenamelist)
        window.wait_window(window)
        if not self.name: #If not set, for any reason
            return 1
    def __init__(self):
        self.name=file.getfilename() #returns filename if there, else filenames
        if type(self.name) is not list and not file.exists(self.name):
                self.name=None #don't return a file that isn't there
        if not self.name or isinstance(self.name,list): #nothing or a selection
            if (self.name and program['testing']
                            and 'testlift' in program and program['testlift']):
                # log.info("self.name0: {}".format(self.name))
                for f in self.name:
                    # log.info("f: {} ({})".format(f,program['testlift']))
                    if program['testlift'] in f:
                        self.name=f
                        # log.info("self.name0.5: {}".format(self.name))
                        break
            if isinstance(self.name,list):
                # log.info("self.name1: {}".format(self.name))
                r=self.askwhichlift(self.name)
                if r:
                    sysshutdown()
        # log.info("self.name: {}".format(self.name))
        if (not self.name or not file.exists(self.name)) and (
                            not program['root'].exitFlag.istrue()):
            return
        if self.name and 'Demo' in self.name:
            file.writefilename() #clear this to select next time
class FileParser(object):
    """This class parses the LIFT file, once we know which it is."""
    def loaddatabase(self):
        try:
            #This program key will only be available after this finishes
            program['db']=lift.Lift(str(self.name))
        except lift.BadParseError:
            text=_("{} doesn't look like a well formed lift file; please "
                    "try again.").format(self.name)
            log.info("'lift_url.py' removed.")
            if program['root'].exitFlag.istrue():
                log.info(text)
                return
            else:
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
        if not file.exists(program['db'].backupfilename):
            program['db'].write(program['db'].backupfilename)
        else:
            print(_("Apparently we've run this before today; not backing "
            "up again."))
    def senseidtriage(self):
        self.senseids=program['db'].senseids
        self.senseidsinvalid=[] #nothing, for now...
        print(len(self.senseidsinvalid),'senses with invalid data found.')
        program['db'].senseidsinvalid=self.senseidsinvalid
        self.senseidsvalid=[]
        for senseid in self.senseids:
            if senseid not in self.senseidsinvalid:
                self.senseidsvalid+=[senseid]
        print(len(self.senseidsvalid),'senses with valid data remaining.')
        self.senseidswanyps=[i for k in program['db'].sensesbyps
                            if k
                            for i in program['db'].sensesbyps[k]
                            ]
        log.info('{} senses w/ ps data found.'.format(len(self.senseidswanyps)))
        self.senseidsvalidwops=[]
        self.senseidsvalidwps=[]
        for senseid in self.senseidsvalid:
            if senseid in self.senseidswanyps:
                self.senseidsvalidwps+=[senseid]
            else:
                self.senseidsvalidwops+=[senseid]
        program['db'].senseidsvalidwps=self.senseidsvalidwps #This is what we'll search
        print(len(self.senseidsvalidwops),'senses with valid data but no ps data.')
        print(len(self.senseidsvalidwps),'senses with valid data and ps data.')
    def getwritingsystemsinfo(self):
        """This doesn't actually do anything yet, as we can't parse ldml."""
        program['db'].languagecodes=program['db'].analangs+program['db'].glosslangs
        program['db'].languagepaths=file.getlangnamepaths(self.name,
                                                    program['db'].languagecodes)
    def __init__(self,name):
        super(FileParser, self).__init__()
        self.name=name
        # splash.progress(15)
        self.loaddatabase()
        # splash.progress(25)
        if program['root'].exitFlag.istrue():
            return
        self.dailybackup()
        # splash.progress(35)
        self.senseidtriage() #sets: self.senseidswanyps self.senseidswops self.senseidsinvalid self.senseidsvalid
        # splash.progress(45)
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
                            program['taskchooser'].changedatabase),
                (_("Digraph and Trigraph settings"),
                            program['settings'].askaboutpolygraphs),
                (_("Segment Interpretation Settings"),
                            self.parent.setSdistinctions),
                (_("Remake Status file (All: several minutes)"),
                            program['settings'].reloadstatusdata),
                (_("Remake Status file (just this category)"),
                            program['settings'].reloadstatusdatabycvtps),
                (_("Remake Status file (just this profile)"),
                        program['settings'].reloadstatusdatabycvtpsprofile),
                ]
        for m in options:
            self.command(self.advancedmenu,
                        label=_(m[0]),
                        cmd=m[1]
                        )
        if isinstance(self.parent,Sound):
            self.sound()
        if isinstance(self.parent,Sort):
            self.sort()
    def sound(self):
        self.advancedmenu.add_separator()
        options=[(_("Sound Settings"),
                self.parent.mikecheck),]
        if isinstance(self.parent,Record):
            options+=[(_("Number of Examples to Record"),
                    program['taskchooser'].getexamplespergrouptorecord),]
            # self.record()
        for m in options:
            self.command(self.advancedmenu,
                    label=_(m[0]),
                    cmd=m[1]
                    )
    def record(self):
        self.advancedmenu.add_separator()
        options=[(_("Number of Examples to Record"),
                program['taskchooser'].getexamplespergrouptorecord),]
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
            if not program['repo'].localremotes():
                helpitems+=[(_("Set up {} source on USB"
                                ).format(program['name']),
                                program['repo'].clonetoUSB)]
            helpitems+=[(_("Update {}").format(program['name']), updateazt)]
            if program['repo'].branch == 'main':
                helpitems+=[(_("Try {} test version").format(program['name']),
                                self.parent.trytestazt)]
            else:
                helpitems+=[(_("Revert to {} main version"
                                ).format(program['name']),
                                self.parent.reverttomainazt)]
        helpitems+=[("What's with the New Interface?",
                        self.parent.helpnewinterface)
                    ]
        for m in helpitems:
            self.command(self.helpmenu,
                        label=_(m[0]),
                        cmd=m[1]
                        )
    def __init__(self, parent):
        self.parent=parent #this should always be the window where they appear
        super(Menus, self).__init__(parent)
        if isinstance(parent,TaskDressing):
            self.advanced()
        self.help()
        if me:
            self.command(self,program['taskchooser'].filename,None)
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
            l.bind('<ButtonRelease-1>',cmd)
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
    """These functions point to program['taskchooser'] functions, betcause we don't
    know who this frame's parent is"""
    def makeproseframe(self):
        self.proseframe=ui.Frame(self,row=0,column=0)
    def interfacelangline(self):
        for l in program['taskchooser'].interfacelangs:
            if l['code']==interfacelang():
                interfacelanguagename=l['name']
        t=(_("Using {}").format(interfacelanguagename))
        self.proselabel(t,cmd=self.task.getinterfacelang)
        self.opts['row']+=1
    def analangline(self):
        analang=program['params'].analang()
        langname=program['settings'].languagenames[analang]
        t=(_("Studying {}").format(langname))
        if (langname == _("Language with code [{}]").format(analang)):
            self.proselabel(t,cmd=self.task.getanalangname,
                                            tt=_("Set analysis language Name"))
        else:
            self.proselabel(t,cmd=self.task.getanalang,
                                            tt=_("Change analysis language"))
        self.opts['row']+=1
    def glosslangline(self):
        lang1=program['settings'].languagenames[program['settings'].glosslangs.lang1()]
        t=(_("Meanings in {}").format(lang1))
        line=ui.Frame(self.proseframe,row=self.opts['row'],column=0,
                        columnspan=3,sticky='w') #3 cols is the width of frame
        self.opts['row']+=1
        self.proselabel(t,cmd=self.task.getglosslang,
                            parent=line)
        self.opts['columnplus']=1
        if len(program['settings'].glosslangs) >1:
            lang2=program['settings'].languagenames[program['settings'].glosslangs.lang2()]
            t=(_("and {}").format(lang2))
        else:
            t=_("only")
        self.proselabel(t,cmd=self.task.getglosslang2,
                            parent=line)
        self.opts['columnplus']=0
    def fieldsline(self):
        # log.info("Starting fieldsline w/self {} ({})".format(self,type(self)))
        # log.info("Starting fieldsline w/task {} ({})".format(self.task,
        #                                                     type(self.task)))
        for ps in [program['settings'].nominalps, program['settings'].verbalps]:
            if ps in program['settings'].secondformfield:
                field=program['settings'].secondformfield[ps]
            else:
                field='<unset>'
            t=(_("Using second form field ‘{}’ ({})").format(field,ps))
            line=ui.Frame(self.proseframe,row=self.opts['row'],column=0,
                            columnspan=3,sticky='w') #3 cols is the width of frame
            self.opts['row']+=1
            if ps == program['settings'].nominalps:
                cmd=self.task.getsecondformfieldN
            else:
                cmd=self.task.getsecondformfieldV
            if field == '<unset>' and (isinstance(self.task,Parse) or (
                isinstance(self.task,WordCollection) and
                self.type not in ['lx','lc'])):
                cmd()
                return #just do one at a time
            self.proselabel(t, cmd=cmd, parent=line)
    def sliceline(self):
        count=program['slices'].count()
        line=ui.Frame(self.proseframe,row=self.opts['row'],column=0,
                        columnspan=3,sticky='w')
        self.opts['row']+=1
        t=(_("Looking at {}").format(self.profile))
        self.proselabel(t,cmd=self.task.getprofile,
                            parent=line)
        self.opts['columnplus']=1
        t=(_("{} words ({})").format(self.ps,count))
        self.proselabel(t,cmd=self.task.getps,parent=line)
        self.opts['columnplus']=0
    def cvtline(self):
        line=ui.Frame(self.proseframe,row=self.opts['row'],column=0,
                        columnspan=3,sticky='w')
        self.opts['row']+=1
        t=(_("Checking {},").format(
                                program['params'].cvtdict()[self.cvt]['pl']))
        self.proselabel(t,cmd=self.task.getcvt,parent=line)
        #this continues on the same line:
        if self.cvt == 'T':
            self.toneframe(line)
            self.tonegroup(line)
        else:
            self.cvcheck(line)
            self.cvgroup(line)
    def toneframe(self,line):
        self.opts['columnplus']=1
        # log.info("toneframes: {}".format(program['toneframes']))
        # log.info("maketoneframes: {}".format(program['toneframes']))
        # log.info("checks: {}; check: {}".format(getattr(self,'checks'),
        #                                         getattr(self,'check')))
        if not self.checks:
            t=_("no tone frames defined.")
            # self.check=None
        elif self.check not in self.checks:
            t=_("no tone frame selected.")
            # self.check=None
        else:
            t=(_("working on ‘{}’ tone frame").format(self.check))
        self.proselabel(t,cmd=self.task.getcheck,
                            parent=line)
    def tonegroup(self,line):
        self.opts['columnplus']=2
        check=program['params'].check()
        group=program['status'].group()
        profile=program['slices'].profile()
        if None in [check, group]:
            t=_("(no framed group)")
        else:
            t=(_("(framed group: ‘{}’)").format(group))
        # log.info("cvt: {}; check: {}".format(self.cvt,self.check))
        """Set appropriate conditions for each of these:"""
        if (not check or (check in program['status'].checks(wsorted=True) and
            profile in program['status'].profiles(wsorted=True))):
            cmd=self.task.getgroupwsorted
        elif (not check or (check in program['status'].checks(tosort=True) and
            profile in program['status'].profiles(tosort=True))):
            cmd=self.task.getgrouptosort
        elif (check in program['status'].checks(toverify=True) and
            profile in program['status'].profiles(toverify=True)):
            cmd=self.task.getgrouptoverify
        elif (check in program['status'].checks(torecord=True) and
            profile in program['status'].profiles(torecord=True)):
            cmd=self.task.getgrouptorecord
        else:
            cmd=None
        log.info("check: {}; profile: {}; \n{}-{}; \n{}-{}; \n{}-{};"
                    "".format(check,profile,
                                program['status'].checks(wsorted=True),
                                program['status'].profiles(wsorted=True),
                                program['status'].checks(tosort=True),
                                program['status'].profiles(tosort=True),
                                program['status'].checks(toverify=True),
                                program['status'].profiles(toverify=True),
                                program['status'].checks(torecord=True),
                                program['status'].profiles(torecord=True)))
        self.proselabel(t,cmd=cmd,parent=line)
        self.opts['columnplus']=0
    def cvcheck(self,line):
        self.opts['columnplus']=1
        t=(_("working on {}".format(program['params'].cvcheckname())))
        self.proselabel(t,cmd=self.task.getcheck,
                        parent=line)
        # self.opts['row']+=1
    def cvgroup(self,line):
        if program['status'].group():
            t=(_("= {}".format(program['status'].group())))
        else:
            t=(_("(All groups)"))
        self.opts['columnplus']=2
        self.proselabel(t,cmd=self.task.getgroup,
                        parent=line)
        # self.opts['row']+=1
    def buttoncolumnsline(self):
        self.opts['row']+=1
        if program['settings'].buttoncolumns:
            t=(_("Using {} button columns").format(program['settings'].buttoncolumns))
        else:
            t=(_("Not using multiple button columns").format(self.check))
        # log.info(t)
        tt=_("Click here to change the number of columns used for sort buttons")
        self.proselabel(t,cmd=self.task.getbuttoncolumns,
                        tt=tt)
    def maxes(self):
        line=ui.Frame(self.proseframe,row=self.opts['row'],column=0,
                        columnspan=3,sticky='w')
        self.opts['row']+=1
        t=(_("Max profiles: {}; ".format(program['settings'].maxprofiles)))
        self.proselabel(t,cmd=self.task.getmaxprofiles,
                        parent=line)
        self.opts['columnplus']=1
        t=(_("Max lexical categories: {}".format(program['settings'].maxpss)))
        self.proselabel(t,cmd=self.task.getmaxpss,
                        parent=line)
    def multicheckscope(self):
        if not hasattr(self.task,'cvtstodo'):
            self.task.cvtstodo=['V']
        line=ui.Frame(self.proseframe,row=self.opts['row'],column=0,
                        columnspan=3,sticky='w')
        self.opts['row']+=1
        log.info(self.task.cvtstodoprose())
        t=(_("Run all checks for {}").format(unlist(self.task.cvtstodoprose())))
        self.proselabel(t,cmd=self.task.getmulticheckscope,
                        parent=line)
    def parserlevels(self):
        try:
            ls=self.task.parser.levels() # we need this anyway, and a parser test
        except AttributeError as e:
            log.info(e)
            return
        line=ui.Frame(self.proseframe,row=self.opts['row'],column=0,
                        columnspan=3,sticky='w')
        self.opts['row']+=1
        t=(_("Parse with confirmation at {}").format(ls[self.task.parser.ask]))
        self.proselabel(t,cmd=self.task.getparserasklevel,
                        parent=line)
        line=ui.Frame(self.proseframe,row=self.opts['row'],column=0,
                        columnspan=3,sticky='w')
        self.opts['row']+=1
        t=(_("Parse automatically at {}").format(ls[self.task.parser.auto]))
        self.proselabel(t,cmd=self.task.getparserautolevel,
                        parent=line)
    def sensetodo(self):
        line=ui.Frame(self.proseframe,row=self.opts['row'],column=0,
                        columnspan=3,sticky='w')
        self.opts['row']+=1
        t=self.task
        if t.sensetodo:
            txt=_("Parsing {}").format(
            t.sensetodo.formatted(t.analang,t.glosslangs)
            )
        else:
            txt=_("Parsing all words")
        self.proselabel(txt,cmd=t.getsensetodo,parent=line)
    def redofinalbuttons(self):
        if hasattr(self,'bigbutton') and self.bigbutton.winfo_exists():
            self.bigbutton.destroy()
        self.finalbuttons()
    def finalbuttons(self):
        # self.opts['row']+=6
        self.opts['row']+=1
        if hasattr(self.task,'dobuttonkwargs'):
            self.bigbutton=self.button(**self.task.dobuttonkwargs())
    def makesecondfieldsOK(self):
        for ps in [program['settings'].nominalps, program['settings'].verbalps]:
            if ps not in program['settings'].secondformfield and (
                isinstance(self.task,Parse) or (
                    isinstance(self.task,WordCollection) and
                    self.type not in ['lx','lc'])):
                if ps == program['settings'].nominalps:
                    self.task.getsecondformfieldN()
                else:
                    self.task.getsecondformfieldV()
                return #just do one at a time
    """Right side"""
    def maybeboard(self):
        if hasattr(self,'leaderboard') and type(self.leaderboard) is ui.Frame:
            self.leaderboard.destroy()
        if hasattr(self,'noboard'): # and type(self.leaderboard) is ui.Frame:
            self.noboard.destroy()
        self.leaderboard=ui.Frame(self,row=0,column=1,sticky="") #nesw
        #Given the line above, much of the below can go, but not all?
        if (
            # isinstance(self.task,Report) or
            isinstance(self.task,TaskChooser) or
            isinstance(self.task,WordCollection) or
            isinstance(self.task,Parse)
            ):
            return
        if (
            isinstance(self.task,Record) or
            isinstance(self.task,JoinUFgroups) or
            not program['taskchooser'].doneenough['collectionlc']):
            self.makenoboard()
            return
        profileori=program['slices'].profile()
        program['status'].cull() #remove nodes with no data
        if self.cvt in program['status']:
            if self.ps in program['status'][self.cvt]: #because we cull, this == data is there.
                if self.cvt == 'T':
                    if self.ps in program['toneframes']:
                        self.makeprogresstable()
                        return
                    else:
                        log.info("Ps {} not in toneframes ({})".format(self.ps,
                                program['toneframes']))
                else:
                    log.info("Found CV verifications")
                    self.makeprogresstable()
                    return
        else:
            log.info("cvt {} not in status {}".format(self.cvt,
                                                            program['status']))
        self.makenoboard()
    def boardtitle(self):
        titleframe=ui.Frame(self.leaderboard)
        titleframe.grid(row=0,column=0,sticky='n')
        cvtdict=program['params'].cvtdict()
        # if not self.mainrelief:
        #     lt=ui.Label(titleframe, text=_(cvtdict[self.cvt]['sg']),
        #                                             font='title')
        # else:
        #     lt=ui.Button(titleframe, text=_(cvtdict[self.cvt]['sg']),
        #                         font='title',relief=self.mainrelief)
        # lt.grid(row=0,column=0,sticky='nwe')
        # ttt=ui.ToolTip(lt,_("Change Check Type"))
        # lt.bind('<ButtonRelease-1>',program['taskchooser'].mainwindowis.getcvt)
        ui.Label(titleframe, text=_('Progress for'), font='title'
            ).grid(row=0,column=1,sticky='nwe',padx=10)
        if not self.mainrelief:
            lps=ui.Label(titleframe,text=self.ps,anchor='c',font='title')
        else:
            lps=ui.Button(titleframe,text=self.ps, anchor='c',
                            relief=self.mainrelief, font='title')
        lps.grid(row=0,column=2,ipadx=0,ipady=0)
        ttps=ui.ToolTip(lps,_("Change Part of Speech"))
        lps.bind('<ButtonRelease-1>',self.task.getps)
    def makenoboard(self):
        log.info("No Progress board")
        try:
            self.boardtitle()
        except:
            log.info("Problem making board title")
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
                    # log.info("Integer {} fine".format(i))
                except:
                    # log.info("Problem with integer {}".format(i))
                    if program['settings'].showdetails:
                        return nn(x,oneperline=True) #if any noninteger, all.
            return len(x) #to show counts only
        def updateprofilencheck(profile,check):
            # log.info("running updateprofilencheck({},{})".format(profile,check))
            program['slices'].profile(profile)
            program['params'].check(check)
            # log.info("now {},{}".format(program['slices'].profile(),
            #                             program['params'].check()))
            #run this in any case, rather than running it not at all, or twice
        def refresh(event=None):
            # log.info("refreshing status table")
            program['settings'].storesettingsfile()
            self.task.tableiteration+=1
        self.boardtitle()
        # leaderheader=Frame(self.leaderboard) #someday, make this not scroll...
        # leaderheader.grid(row=1,column=0)
        leaderscroll=ui.ScrollingFrame(self.leaderboard)
        leaderscroll.grid(row=1,column=0)
        self.leaderboardtable=leaderscroll.content
        row=0
        #put in a footer for next profile/frame
        cvt=program['params'].cvt()
        ps=program['slices'].ps()
        profiles=program['slices'].profiles()[:] #just sort here
        curprofile=program['slices'].profile()
        curcheck=program['params'].check()
        try:
            frames=list(program['toneframes'][ps].keys())
        except KeyError:
            frames=list()
        allchecks=[]
        for profile in profiles:
            if profile in program['status'][cvt][ps]:
                #make sure the table has all columns needed for any profile
                allchecks+=program['status'][cvt][ps][profile].keys()
        allchecks=list(dict.fromkeys(allchecks)) #could unsort slices priority
        if self.cvt != 'T': #don't resort tone frames
            allchecks.sort(key=len,reverse=True) #longest first
        profiles.sort(key=lambda x:(x.count(self.cvt),len(x)))
        profiles=['colheader']+profiles+['next']
        ungroups=0
        unsortedtext='[X]'
        if program['settings'].showdetails:
            tv=_("verified")
            tu=_("unsorted")
            # t="+ = {} \n! = {}".format(tv,tu)
            t="+ = {} \n{} = {}".format(tv,unsortedtext,tu)
            h=ui.Label(self.leaderboardtable,text=t,font="small")
            h.grid(row=row,column=0,sticky='e')
            h.bind('<ButtonRelease-1>', refresh)
            htip=_("Refresh table, \nsave settings")
            th=ui.ToolTip(h,htip)
        r=list(program['status'][cvt][ps])
        log.debug("Table rows possible: {}".format(r))
        for profile in profiles:
            column=0
            if profile in ['colheader','next']+list(program['status'][cvt][
                                                            ps].keys()):
                if profile in program['status'][cvt][ps]:
                    if program['status'][cvt][ps][profile] == {}:
                        continue
                    #Make row header
                    t=profile
                    if program['settings'].showdetails:
                        t+=" ({})".format(
                                len(program['settings'].profilesbysense[ps][profile]))
                    h=ui.Label(self.leaderboardtable,text=t,
                                row=row,
                                column=column,
                                sticky='e',
                                padx=10)
                    if profile == curprofile and curcheck is None:
                        h.config(background=h.theme.activebackground) #highlight
                        tip=_("Current profile \n(no check set)")
                        ttb=ui.ToolTip(h,tip)
                elif profile == 'next': # end of row headers
                    brh=ui.Button(self.leaderboardtable,text=_(profile),
                            font='reportheader',
                            relief='flat',cmd=program['settings'].setnextprofile)
                    brh.grid(row=row,column=column,sticky='e')
                    brht=ui.ToolTip(brh,_("Go to the next syllable profile"))
                for check in allchecks+['next']:
                    column+=1
                    if profile == 'colheader':
                        if check == 'next': # end of column headers
                            # log.info("todo: {}".format(program['status'].checks(todo=True)))
                            # log.info("tosort: {}".format(program['status'].checks(tosort=True)))
                            # log.info("toverify: {}".format(program['status'].checks(toverify=True)))
                            # log.info("tojoin: {}".format(program['status'].checks(tojoin=True)))
                            if cvt == 'T' and not (
                                    program['status'].checks(todo=True)
                                                    ):
                                cmd=self.task.addframe
                            else:
                                cmd=lambda todo=True:program['settings'].setnextcheck(
                                                                    todo=todo)
                            bch=ui.Button(self.leaderboardtable,text=_(check),
                                        relief='flat',
                                        cmd=cmd,
                                        font='reportheader',
                                        row=row,column=column,sticky='s')
                            bcht=ui.ToolTip(bch,_("Go to the next check"))
                        else:
                            l=ui.Label(self.leaderboardtable,
                                    text=rx.linebreakwords(check),
                                    font='reportheader',
                                    row=row,column=column,sticky='s',ipadx=5)
                            l.bind('<ButtonRelease-1>',
                                        self.task.getcvt)
                    elif profile == 'next':
                        continue
                    elif check in program['status'].checks(cvt=cvt,ps=ps,
                                                            profile=profile):
                        node=program['status'].node(cvt=cvt,ps=ps,
                                                        profile=profile,
                                                        check=check)
                        if len(node['done']) > len(node['groups']):
                            ungroups+=1
                        #At this point, these should be there
                        done=node['done']
                        total=node['groups']
                        tosort=node['tosort']
                        totalwverified=[]
                        nunverified=len(set(total)-set(done))
                        for g in total:
                            if g in done:
                                g='+'+g #these should be strings
                                # g='?'+g #these should be strings
                                # g='<'+g+'>' #these should be strings
                            totalwverified+=[g]
                        donenum=groupfn(done)
                        totalnum=groupfn(total)
                        if (not totalnum and
                                tosort and
                                program['settings'].showdetails): #these should go together
                            donenum=unsortedtext #don't say '0'
                        elif not totalnum and tosort:
                            donenum=""
                        elif (not program['settings'].showdetails or
                            (type(totalnum) is int and type(donenum) is int)):
                            # donenum="{}/{}".format(donenum,totalnum)
                            donenum=totalnum
                        else:
                            donenum=nn(totalwverified,oneperline=True)
                        if (tosort and totalnum and program['settings'].showdetails):
                            donenum=str(donenum)+'\n'+unsortedtext
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
                        tips=[]
                        if tosort:
                            tips.extend([_("Words to sort!")])
                            if not program['settings'].showdetails:
                                tb.configure(highlightthickness=3)
                                tb.configure(highlightbackground=tb.theme.white)
                        if nunverified:
                            tips.extend([_("{} groups to verify!"
                                        ).format(nunverified)])
                        if not tips:
                            tips.extend([_("Sorted and verified!")])
                        tip='\n'.join(tips)
                        tb.grid(row=row,column=column,ipadx=0,ipady=0,
                                                                sticky='nesw')
                        ttb=ui.ToolTip(tb,tip)
            row+=1
        if ungroups > 0:
            log.error(_("You have more groups verified than there are, in {} "
                        "cells".format(ungroups)))
        # self.frame.update()
    def __init__(self, parent, task, **kwargs):
        self.setopts()
        self.parent=parent
        self.task=task #this is the window that called it; task or chooser
        self.mainrelief=kwargs.pop('relief',None) #not for frame
        kwargs['padx']=25
        super(StatusFrame, self).__init__(parent, **kwargs)
        self.makeproseframe()
        self.interfacelangline()
        self.analangline()
        self.glosslangline()
        if isinstance(self.task,Segments):
            self.fieldsline()
        if ('slices' in program and
                not isinstance(self.task,TaskChooser) and
                not isinstance(self.task,Parse)):
            self.cvt=program['params'].cvt()
            self.ps=program['slices'].ps()
            self.profile=program['slices'].profile()
            self.check=program['params'].check()
            self.checks=program['status'].checks()
            if isinstance(self.task,Multislice): #any cvt
                self.maxes()
            else:
                self.sliceline()
            if isinstance(self.task,Multicheck): #segments only
                self.multicheckscope()
            elif not isinstance(self.task,ReportCitationT):
                self.cvtline()
            if isinstance(self.task,Sort) and not isinstance(self.task,Transcribe):
                self.buttoncolumnsline()
        if isinstance(self.task,Parse):
            self.parserlevels()
            self.sensetodo()
        self.maybeboard()
        self.finalbuttons()
class Settings(object):
    """docstring for Settings."""
    def interfacelangwrapper(self,choice=None,window=None):
        if choice:
            interfacelang(choice) #change the UI *ONLY*; no object attributes
            self.set('interfacelang',choice,window) #set variable for the future
            self.storesettingsfile() #>xyz.CheckDefaults.py
            #because otherwise, this stays as is...
            program['taskchooser'].mainwindowis.maketitle()
        else:
            return interfacelang()
    def repocheck(self):
        log.info(_("Checking for a data repository"))
        # self.repo={}
        self.repo=dict() #then copy to class attribute if there
        # return #for now, until fixed
        if not program['testing']:
            repo={ #start with local variable:
                    'git': Git(self.directory),
                    'hg': Mercurial(self.directory),
                    }
            for r in repo:
                if (hasattr(repo[r],'files') #fails if no exe
                        and repo[r].exists()): #tests for .code dir
                    log.info(_("Found {} Repository!"
                                ).format(repo[r].repotypename))
                    self.repo[r]=repo[r]
                elif r == 'git' and 'git' in program and program['git']:
                    #don't worry about hg, if not there already
                    log.info(_("No Git data repository found; creating."))
                    repo[r].init()
                    repo[r].add(self.liftfilename)
                    repo[r].commit()
                    self.repo[r]=repo[r]
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
                                'showdetails',
                                'maxprofiles',
                                'menu',
                                'mainrelief',
                                'fontthemesmall',
                                'secondformfield',
                                'soundsettingsok',
                                'buttoncolumns',
                                'showoriginalorthographyinreports',
                                'lowverticalspace',
                                'giturls',
                                'hgurls',
                                'aztrepourls',
                                'minimumwordstoreportUFgroup',
                                'writeeverynwrites'
                                ]},
            'profiledata':{
                                'file':'profiledatafile',
                                'attributes':[
                                    'analang',
                                    'ftype',
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
        #This should be removed at some point
        savefile=self.settingsfile(setting)
        legacy=savefile.with_suffix('.py')
        log.info("Going to make {} into {}".format(legacy,savefile))
        if setting == 'soundsettings':
            self.soundsettings=sound.SoundSettings()
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
                    try:
                        delattr(self,lang) #because this would be made above
                    except AttributeError:
                        log.info("attribute {} doesn't seem to be there".format(lang))
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
        if setting == 'soundsettings':
            self.soundsettings.pyaudio.stop() # when done here
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
        for setting in self.settings:
            savefile=self.settingsfile(setting)#self.settings[setting]['file']
            if not file.exists(savefile):
                log.debug("{} doesn't exist!".format(savefile))
                legacy=savefile.with_suffix('.py')
                if file.exists(legacy):
                    log.debug("But legacy file {} does; converting!".format(legacy))
                    self.loadandconvertlegacysettingsfile(setting=setting)
            if str(savefile).endswith('.dat') and file.exists(savefile):
                for r in self.repo:
                    self.repo[r].add(savefile)
        for r in self.repo:
            self.repo[r].commit()
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
            fns['cvt']=program['params'].cvt
            fns['check']=program['params'].check
            fns['ftype']=program['params'].ftype
            fns['analang']=program['params'].analang
            fns['glosslang']=self.glosslangs.lang1
            fns['glosslang2']=self.glosslangs.lang2
            fns['glosslangs']=self.glosslangs.langs
            # fns['toneframes']=program['toneframes']
            # fns['status']=program['status']
            fns['aztrepourls']=program['repo'].remoteurls
            fns['giturls']=self.repo['git'].remoteurls
            fns['hgurls']=self.repo['hg'].remoteurls
            fns['ps']=program['slices'].ps
            fns['profile']=program['slices'].profile
            # except this one, which pretends to set but doesn't (throws arg away)
            fns['profilecounts']=program['slices'].slicepriority
        except Exception as e:
            log.error("Only finished settingsobjects up to {} ({})".format(fns.keys(),e))
            return []
        log.info("Finished settingsobjects up to {}".format(fns.keys()))
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
            # log.info("{} attr value: {}".format(s,getattr(self,s,'Not Found!')))
            """This dictionary of functions isn't made until after the objects,
            at the end of settings init. So this block is not used in
            conversion, only in later saves."""
            if hasattr(self,'fndict') and s in self.fndict:
                # log.info("Trying to dict {} attr".format(s))
                try:
                    d[s]=self.fndict[s]()
                    # log.info("Value {}={} found in object".format(s,d[s]))
                except:
                    log.error("Value of {} not found in object".format(s))
            elif hasattr(o,s) and getattr(o,s):
                d[s]=getattr(o,s)
                # log.info("Set to dict self.{} with value {}, type {}"
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
                # log.info("Trying to read {} to object with value {} and fn "
                #             "{}".format(s,v,self.fndict[s]))
                self.fndict[s](v)
            else:
                # log.info("Trying to read {} to {} with value {}, type {}"
                #             "".format(s,o,v,type(v)))
                setattr(o,s,v)
        return d
    def storesettingsfile(self,setting='defaults',noobjects=False):
        #There are too many calls to this; why?
        filename=self.settingsfile(setting)
        config=ConfigParser()
        if setting in ['status', 'toneframes']:
            d=program[setting]
        else:
            d=self.makesettingsdict(setting=setting)
        # config.read(filename,encoding='utf-8')
        # if d == config:
        #     log.info("no settings change; not writing.")
        #     return
        # else:
        #     log.info("Settings from file: {}".format(dict(config['default'])))
        #     log.info("Settings currently: {}".format(d))
        config['default']={}
        # log.info("storing settings file {}".format(setting))
        for s in [i for i in d if i not in [None,'None']]:
            v=d[s]
            # log.info("Ready to store {} type data: {}".format(type(v),v))
            if isinstance(v, dict):
                config[s]=indenteddict(v)
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
        log.debug("Trying for {} settings in {}".format(setting, filename))
        if not config.sections() and setting not in ['status','toneframes']:
            if setting == "adhocgroups":
                self.adhocgroups={}
            return
        d={}
        log.info("Found {} sections: {}".format(setting,config.sections()))
        for section in config: #self.settings[setting]['attributes']:
            # log.info('\n'.join([': '.join([k,config[section][k]])
            #                             for k in config[section]]))
            if 'default' in config and section in ['default','DEFAULT']:
                for k in config[section]:
                    log.info("Moving {}.{}={} to object".format(section,k,
                                                            config[section][k]))
                    d[k]=ofromstr(config['default'][k])
                # d[section]=ofromstr(config['default'][section])
            else:
                log.info("working in non-default section {}".format(section))
                # log.debug("Trying for {} settings in {}".format(section, setting))
                if len(config[section].values())>0:
                    # log.debug("Found Dictionary value for {} ({})".format(
                    #                                 section,config[section]))
                    d[section]={}
                    for s in config[section]:
                        # log.debug("Found value {}: {}"
                        #             "".format(s,config[section][s]))
                        d[section][s]={}
                        """Make sure strings become python data"""
                        d[section][ofromstr(s)]=ofromstr(config[section][s])
                else:
                    log.debug("Found String/list/other value for {}: ({})"
                            "".format(section,len(config[section].values())))
                    d[section]=ofromstr(config[section])
        if setting == 'status':
            # log.info("setting {} is {}".format(setting,d))
            self.makestatus({k:d[k] for k in d if k != 'DEFAULT'})
            log.info("makestatus: {}".format(program['status']))
        elif setting == 'toneframes':
            # log.info("setting {} is {}".format(setting,d))
            self.maketoneframes({k:d[k] for k in d if k != 'DEFAULT'})
            log.info("maketoneframes: {}".format(program['toneframes']))
        else:
            self.readsettingsdict(d)
        if hasattr(self,'interfacelang'):
            interfacelang(self.interfacelang)
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
                        'showdetails':[],
                        'maxprofiles':[]
                        }
    def cleardefaults(self,field=None):
        if field==None:
            fields=self.settings['defaults']['attributes']
        else:
            fields=self.defaultstoclear[field]
        for default in fields: #self.defaultstoclear[field]:
            if default in ['lowverticalspace']:
                setattr(self, default, True)
            else:
                setattr(self, default, None)
    def settingsinit(self):
        log.info("Initializing settings.")
        # self.defaults is already there, from settingsfilecheck
        self.initdefaults() #provides self.defaultstoclear, needed?
        self.cleardefaults() #this resets all to none (to be set below)
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
        # log.info('self.audiodir: {}'.format(self.audiodir))
        self.reportsdir=file.getreportdir(self.directory)
        self.reportbasefilename=file.getdiredurl(self.reportsdir,
                                                    self.liftnamebase)
        self.reporttoaudiorelURL=file.getreldir(self.reportsdir, self.audiodir)
        # log.info('self.reportsdir: {}'.format(self.reportsdir))
        # log.info('self.reportbasefilename: {}'.format(self.reportbasefilename))
        # log.info('self.reporttoaudiorelURL: {}'.format(self.reporttoaudiorelURL))
        # setdefaults.langs(program['db']) #This will be done again, on resets
    def trackuntrackedfiles(self):
        # return #until this doesn't cause problems
        # This method is here to pick up files that are there, but not tracked,
        # either in constructing a repository, or as a result of changes by other
        # editors (e.g., WeSay).
        # This is for new files, not changes to known files; that is done
        # on close.
        # def ifnotthereadd(f,repo):
        #     # print('ifnotthereadd')
        #     if f not in self.repo[repo].files:
        #         # print('ifnotthereadd',f,2)
        #         self.repo[repo].add(f)
        log.info(_("Looking for untracked files to add to repositories"))
        maxthreads=8 #This causes problems with lots of threads
        maindirfiles=[self.liftfilename,
                        self.toneframesfile,
                        self.statusfile,
                        self.profiledatafile,
                        # I don't know if anyone is using this, but if so, they share...
                        self.adhocgroupsfile,
                        #self.defaultfile # This probably shouldn't be shared
                        # self.soundsettingsfile #per computer, definitely don't share!
                        ]
        program['root'].update() #update GUI before threading
        # for r in self.repo:
        r='git' #only look for this; don't duplicate repos unnecessarily
        if r in self.repo:
            t=u=None
            present=set(self.repo[r].files)
            log.info("{} currently has {} files".format(r,len(present)))
            for f in maindirfiles:
                # log.info("{}".format([file.getreldirposix(self.repo[r].url,f)]))
                # log.info("working on {}".format(file.getreldirposix(self.repo[r].url,f)))
                log.info("working on {}".format(file.getfile(f)))
                # f=file.getreldirposix(self.repo[r].url,f)
                if file.exists(f):# They won't always be there
                    self.repo[r].add(file.getreldirposix(self.repo[r].url,f))
            # In case I run into formatting issues again:
            # log.info(', '.join(list(self.repo[r].files)[:5]))
            # log.info(', '.join([file.getreldir(self.repo[r].url,i) for i in file.getfilesofdirectory(self.audiodir, '*.wav')][:5]))
            # If we ever support mp3, we should add it here:
            # log.info("{}".format([file.getreldirposix(self.repo[r].url,i)
            #         for i in file.getfilesofdirectory(self.audiodir,
            #                                             '*.wav')]))
            # log.info("{}".format(set(file.getreldirposix(self.repo[r].url,i)
            #         for i in file.getfilesofdirectory(self.audiodir,
            #                                             '*.wav'))))
            audiohere=set([file.getreldirposix(self.repo[r].url,i)
                    for i in file.getfilesofdirectory(self.audiodir,
                                                        '*.wav')])
            audio=audiohere-present
            log.info("{} wav files to check for the {} repo (of {} files total "
                    "here)".format(len(audio),r,len(audiohere)))
            log.info("head of wav files in repo: {}".format(list(present)[:10]))
            log.info("head of wav files here: {}".format(list(audiohere)[:10]))
            log.info("head of wav files to check: {}".format(list(audio)[:10]))
            for f in audio:
                self.repo[r].add(f) #These should exist, from ls above
                # if threading.active_count()<maxthreads:
                #     t = threading.Thread(target=ifnotthereadd, args=(f,r))
                #     t.start()
                # log.info(_("trackuntrackedfiles waiting for {} audio file threads."
                #         ).format(threading.active_count()))
                # if t:
                #     t.join()
                # self.repo[r].add(f)
            for ext in ['png','jpg','gif']:
                # log.info("Image Directory: {}".format(self.imagesdir))
                # log.info("Found image files: {}".format(nn([i for i in
                # file.getfilesofdirectory(self.imagesdir,
                #                         '*.'+ext)], oneperline=True)))
                i=set([file.getreldirposix(self.repo[r].url,i)
                        for i in file.getfilesofdirectory(self.imagesdir,
                                                '*.'+ext)]
                        )-present
                log.info("{} {} files to check for the {} repo"
                        "".format(len(i),ext,r))
                for f in i:
                    self.repo[r].add(f) #These should exist, from ls above
                    # if threading.active_count()<maxthreads:
                    #     u = threading.Thread(target=ifnotthereadd, args=(f,r))
                    #     u.start()
                    # log.info("trackuntrackedfiles waiting for {} {} file "
                    #     "threads.".format(threading.active_count(),ext))
                    # if u:
                    #     u.join()
        log.info("trackuntrackedfiles finished.")
    def pss(self):
        log.info("checking these lexical category names for plausible noun "
                "and verb names: {}".format(program['db'].pss))
        topn=3 #just in case N and V aren't the first two, finish with top
        log.info("Looking at pss {}".format(program['db'].pss))
        for ps in reversed(program['db'].pss[:topn]):
            log.info("Looking at ps {}".format(ps))
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
            # else:
            #     log.error("Not sure what to do with top {} ps {}".format(
            #                                                         topn,ps))
        if not hasattr(self,'nominalps'):
                self.nominalps='Noun'
        if not hasattr(self,'verbalps'):
                self.verbalps='Verb'
        try:
            log.info("Using ‘{}’ for nouns, and ‘{}’ for verbs".format(
                self.nominalps,
                self.verbalps))
        except AttributeError:
            log.info("Problem with finding a nominal and verbal lexical "
            "category (looked in first two of [{}])"
            "".format(program['db'].pss))
        if self.secondformfield:
            if self.nominalps in self.secondformfield:
                self.pluralname=self.secondformfield[self.nominalps]
            if self.verbalps in self.secondformfield:
                self.imperativename=self.secondformfield[self.verbalps]
    def fields(self):
        """I think this is lift specific; may move it to defaults, if not."""
        # log.info(program['db'].fieldnames)
        try:
            fieldnames=program['db'].fieldnames[self.analang]
        except KeyError:
            fieldnames=[]
        self.secondformfield={}
        log.info(_("Fields found in lexicon: {}".format(str(fieldnames))))
        self.plopts=['Plural', 'plural', 'pl', 'Pluriel', 'pluriel']
        self.impopts=['Imperative', 'imperative', 'imp', 'Imp', 'Imperatif',
                                                    'imperatif']
        for opt in self.plopts:
            if opt in fieldnames:
                self.secondformfield[self.nominalps]=self.pluralname=opt
        try:
            log.info(_('Plural field name: {}').format(self.pluralname))
            for entry in program['db'].entries:
                entry.plvalue(self.pluralname,self.analang) # get the right field!
        except AttributeError:
            log.info(_('Looks like there is no Plural field in the database'))
            self.pluralname=None
        for opt in self.impopts:
            if opt in fieldnames:
                self.secondformfield[self.verbalps]=self.imperativename=opt
        try:
            log.info(_('Imperative field name: {}'.format(self.imperativename)))
            for entry in program['db'].entries:
                entry.impvalue(self.imperativename,self.analang) # get the right field!
        except AttributeError:
            log.info(_('Looks like there is no Imperative field in the database'))
            self.imperativename=None
    def askaboutpolygraphs(self,onboot=False):
        def nochanges():
            log.info("Trying to make no changes")
            if not pgw.exitFlag.istrue():
                pgw.destroy()
            if foundchanges():
                log.info("Found changes, but not storing them; returning 1.")
                return 1
        def makechanges():
            log.info("Changes called for; like it or not, redoing analysis.")
            pgw.destroy()
            if not foundchanges():
                log.info("User asked for changes to polygraph settings, but "
                        "no changes found.")
                return
            for lang in program['db'].analangs:
                for pc in vars[lang]:
                    for pg in vars[lang][pc]:
                        self.polygraphs[lang][pc][pg]=vars[lang][pc][pg].get()
            self.storesettingsfile(setting='profiledata')
            program['taskchooser'].restart()
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
        if onboot:
            nochangetext=_("Exit {} with no changes".format(program['name']))
        else:
            nochangetext=_("Exit with no changes")
        log.info("Asking about Digraphs and Trigraphs!")
        titlet=_("{} Digraphs and Trigraphs").format(program['name'])
        #From wherever this is opened, it should withdraw and deiconify that
        pgw=ui.Window(program['taskchooser'].mainwindowis,title=titlet,exit=False)
        t=_("Which of the following letter sequences "
            "refer to a single sound?")
        lnames=[self.languagenames[y] for y in program['db'].analangs]
        if len(lnames)>1:
            t+=_(" (Answer for each of {}.)".format(unlist(lnames)))
        else:
            t+=_(" (in {})".format(unlist(lnames)))
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
        t=_("If you expect one that isn't listed "
            "here, please click here to Email me, and I can add it.")
        row+=1
        t2=ui.Label(pgw.frame,text=t,column=0, row=row)
        eurl='mailto:{}?subject=New trigraph or digraph to add (today)'.format(
                                                            program['Email'])
        t2.bind("<Button-1>", lambda e: openweburl(eurl))
        t=_("Making changes will restart {} and trigger another syllable "
            "profile analysis. \nIf you don't want that, click ‘{}’."
            # "\nEither way, you won't get past this window until you answer "
            # "this question."
            # "\nIf you just started this database, and are unsure what to do, "
            # "you are probably OK to leave them all selected."
            # "\nYou can always come back here and make changes as you need."
            "".format(program['name'],nochangetext))
        row+=1
        t3=ui.Label(pgw.frame,text=t,column=0, row=row)
        helpurl='{}/POLYGRAPHS.md'.format(program['docsurl'],program['Email'])
        t=_("See {} for further instructions.").format(helpurl)
        row+=1
        t4=ui.Label(pgw.frame,text=t,column=0, row=row)
        t4.bind("<Button-1>", lambda e: openweburl(helpurl))
        if not hasattr(self,'polygraphs'):
            self.polygraphs={}
        vars={}
        row+=1
        scroll=ui.ScrollingFrame(pgw.frame, row=row, column=0)
        srow=0
        ncols=4 # increase this for wider window
        for lang in program['db'].analangs:
            if lang not in self.polygraphs:
                self.polygraphs[lang]={}
            srow+=1
            title=ui.Label(scroll.content,text=self.languagenames[lang],
                                                        font='read')
            title.grid(column=0, row=srow, columnspan=ncols)
            vars[lang]={}
            # log.info("sclasses: {}".format(program['db'].s[lang]))
            for sclass in [sc for sc in program['db'].s[lang] #Vtg, Vdg, Ctg, Cdg, etc
                                if ('dg' in sc or 'tg' in sc or 'qg' in sc)]:
                pclass=sclass.replace('dg','').replace('tg','').replace('qg','')
                if pclass not in self.polygraphs[lang]:
                    self.polygraphs[lang][pclass]={}
                if pclass not in vars[lang]:
                    vars[lang][pclass]={}
                if len(program['db'].s[lang][sclass])>0:
                    srow+=1
                    header=ui.Label(scroll.content,
                    text=sclass.replace('dg',' (digraph)').replace(
                                        'tg',' (trigraph)').replace(
                                        'qg',' (quatregraph)')+': ')
                    header.grid(column=0, row=srow)
                col=1
                # log.info("pgs: {}".format(program['db'].s[lang][sclass]))
                for pg in program['db'].s[lang][sclass]:
                    vars[lang][pclass][pg] = ui.BooleanVar()
                    vars[lang][pclass][pg].set(
                                    self.polygraphs[lang][pclass].get(pg,True))
                    cb=ui.CheckButton(scroll.content, text = pg, #.content
                                        variable = vars[lang][pclass][pg],
                                        onvalue = True, offvalue = False,
                                        )
                    cb.grid(column=col, row=srow,sticky='nsew')
                    if col<= ncols:
                        col+=1
                    else:
                        col=1 #not header
                        srow+=1
        row+=1
        b=ui.Button(pgw.frame,text=oktext,command=makechanges, width=15,
                    column=0, row=row, sticky='e',padx=15)
        pgw.wait_window(pgw)
        if not program['taskchooser'].exitFlag.istrue():
            return nochanges() #this is the default exit behavior
    def polygraphcheck(self):
        log.info("Checking for Digraphs and Trigraphs!")
        # log.info("Language settings: {}".format(program['db'].s))
        if not hasattr(self,'polygraphs'):
            self.polygraphs={}
        for lang in program['db'].analangs:
            if lang not in program['db'].s:
                log.error(_("Language {} found without segment settings."
                            ).format(lang))
                continue
            if lang not in self.polygraphs:
                self.polygraphs[lang]={}
            for sclass in [sc for sc in program['db'].s[lang]
                                    if ('dg' in sc or 'tg' in sc or 'qg' in sc)]:
                pclass=sclass.replace('dg','').replace('tg','').replace('qg','')
                if pclass not in self.polygraphs[lang]:
                    self.polygraphs[lang][pclass]={}
                for pg in program['db'].s[lang][sclass]:
                    # log.info("checking for {} ({}/{}) in {}"
                    #         "".format(pg,pclass,sclass,self.polygraphs))
                    if pg not in self.polygraphs[lang][pclass]:
                        log.info("{} ({}/{}) has no Di/Trigraph setting; "
                        "prompting user for info.".format(pg,pclass,sclass))
                        if self.askaboutpolygraphs(onboot=True):
                            log.info(_("Asked about polgraphs, but user "
                                        "exited, so exiting {}"
                                        ).format(program['name']))
                            program['taskchooser'].mainwindowis.on_quit()
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
    def addtoprofilesbysense(self,senseid,ps,profile):
        # log.info("kwargs: {}".format(kwargs))
        # This will die if ps and profile aren't in kwargs:
        try:
            self.profilesbysense[ps][profile]+=[senseid]
        except KeyError:
            try:
                self.profilesbysense[ps][profile]=[senseid]
            except KeyError:
                self.profilesbysense[ps]={}#[profile]=[senseid]
                self.profilesbysense[ps][profile]=[senseid]
    def addtoformstosearch(self,senseid,form,ps,oldform=None):
        try:
            if senseid not in self.formstosearch[ps][form]: #don't duplicate
                self.formstosearch[ps][form].append(senseid)
        except KeyError: # either ps or form is missing, nothing to append to
            try: #if it's just form
                self.formstosearch[ps][form]=[senseid]
            except KeyError: #ps is missing, build from scratch
                self.formstosearch[ps]={form:[senseid,]}
        # log.info("Added {} id={}".format(form,senseid))
        if oldform:
            try:
                self.formstosearch[ps][oldform].remove(senseid)
                log.info("Removed {} ({})".format(form,self.formstosearch[ps][form]))
            except ValueError:
                log.error(_("Apparently {} isn't under {}?".format(senseid,form)))
            if not self.formstosearch[ps][oldform]:
                del self.formstosearch[ps][oldform] #don't leave form wo senseid
                log.info("Deleted key of empty list")
    def getprofileofentry(self,entry):
        getattr(entry,ftype).textvaluebylang(self.analang)
        #CONTINUE HERE
    def getprofileofsense(self,sense,ps):
        #Convert to iterate over local variables
        form=sense.textvaluebyftypelang('lc',program['params'].analang())
        """This adds to self.sextracted, too"""
        profile=self.profileofform(form,ps=ps)
        # log.info("getprofileofsense Profile: {}".format(profile))
        if not set(self.profilelegit).issuperset(profile):
            profile='Invalid'
        self.addtoprofilesbysense(sense.id, ps=ps, profile=profile)
        self.addtoformstosearch(sense.id, form, ps=ps)
        return form,profile
    def getprofilesbyps(self,ps):
        start_time=nowruntime()
        log.info("Processesing {} syllable profiles".format(ps))
        senses=program['db'].sensesbyps[ps]
        self.sextracted[ps]={} #start over, don't add to if there
        n=self._getprofiles(senses,ps)
        log.info("Processed {} forms to syllable profile".format(n))
        logfinished(start_time)
    def _getprofiles(self,senses,ps):
        n=0
        todo=len(senses)
        # log.info("RXs: {}".format(self.rx))
        if todo>750:
            program['taskchooser'].wait(msg="getting profiles for {}".format(ps))
        for sense in senses:
            n+=1
            if n%100:
                t = threading.Thread(target=self.getprofileofsense,
                                    args=(sense,ps))
                t.start()
            else:
                form,profile=self.getprofileofsense(sense,ps)
                log.debug("{}: {}; {}".format(str(n)+'/'+str(todo),form,
                                            profile))
            if todo>750:
                program['taskchooser'].waitprogress(n*100/todo)
        t.join()
        if todo>750:
            program['taskchooser'].waitdone()
        return n
    def getprofilesbyentry(self):
        for entry in program['db'].entries:
            for sense in entry.senses:
                sense.lx.textvaluebylang(self.analang)
    def getprofiles(self):
        """This is called after settings finished init/load from files"""
        #This is for analysis from scratch
        self.profileswdatabyentry={}
        self.profilesbysense={}
        self.profilesbysense['Invalid']=[]
        self.profilesbysense['analang']=program['params'].analang()
        self.profilesbysense['ftype']=program['params'].ftype()
        self.profiledguids=[]
        self.profiledsenseids=[]
        self.formstosearch={}
        self.sextracted={} #don't add to old data
        self.notifyuserofextrasegments() #analang set by now, depends db only
        self.polygraphcheck() #depends only on self.polygraph
        self.checkinterpretations() #checks/sets values for distinguish/interpret
        self.setupCVrxs() # self.rx (calls slists, needs distinguish)
        for ps in program['db'].pss: #45s on English db
            # self.sextracted[ps]={}
            # for s in self.rx:
            #     self.sextracted[ps][s]={}
            self.getprofilesbyps(ps)
        # self.getprofilesbyentry()
        #Convert to iterate over local variables
        """Do I want this? better to keep the adhoc groups separate"""
        """We will *never* have slices set up by this time; read from file."""
        if hasattr(self,'adhocgroups'):
            for ps in self.adhocgroups:
                for a in self.adhocgroups[ps]:
                    log.debug("Adding {} to {} ps-profile: {}".format(a,ps,
                                                self.adhocgroups[ps][a]))
                    #copy over stored values:
                    try:
                        self.profilesbysense[ps][a]=self.adhocgroups[ps][a]
                    except KeyError: #in case the ps isn't already there
                        self.profilesbysense[ps]={a:self.adhocgroups[ps][a]}
                    # log.debug("resulting profilesbysense: {}".format(
                    #                         self.profilesbysense[ps][a]))
        else:
            self.adhocgroups={}
        SliceDict(self.adhocgroups,self.profilesbysense) #self.profilecounts
        if program['slices'].profile():
            self.getscounts()
        self.storesettingsfile(setting='profiledata')
    def profileofformpreferred(self,form):
        """Simplify combinations where desired"""
        c=['N','S','G','ʔ','D']
        o=["̀",'<','=','ː']
        cc=['CG','CS','NC','VN','VV']
        for g in [i for i in c+o if i in form]:
            #Remove this glyph variable wherever it occurs:
            if not self.distinguish[g]:
                if g in o:
                    # log.info("Using self.rx[{}]={}".format(g,self.rx[g]))
                    # If I ever want to pull these based on word position, this
                    # should be updated. This just pulls all of a given o set.
                    form=self.rx[g][0].sub('',form)
                else:
                    # This and following rx in this method search for variables,
                    # not glyphs, so don't use a polyglyph dictionary layer.
                    form=self.rx[g+'_'].sub('C',form) #no polygraphs here
            #Remove this glyph variable word finally:
            if 'wd' in g and not self.distinguish[c+'wd']:
                form=self.rx[g+'wd'].sub('C',form) #no polygraphs here
                # log.debug("{}wd regex result: {}".format(c,form))
        for cc in [i for i in cc if i in form]:
            form=self.rx[cc].sub(self.interpret[cc],form) #no polygraphs here
        return form
    def profileofform(self,form,ps):
        if not form or not ps:
            # log.info("Either no form ({}) or no ps ({}); returning".format(form,ps))
            return "Invalid"
        # log.debug("profiling {}...".format(form))
        formori=form
        """priority sort alphabets (need logic to set one or the other)"""
        """Look for any C, don't find N or G"""
        # self.profilelegit=['#','̃','C','N','G','S','V']
        """Look for word boundaries, N and G before C (though this doesn't
        work, since CG is captured by C first...)"""
        # self.profilelegit=['#','̃','N','G','S','C','Ṽ','V','d','b']
        # log.info("Searching {} ordered as: {}".format(form,self.profilelegit))
        # log.info("Searching with these regexes: {}".format(self.rx))
        # log.info('self.sextracted: ‘{}’'.format(self.sextracted))
        for s in set(self.profilelegit) & set(self.rx.keys()):
            # log.info('s: {}; rx: {}'.format(s, self.rx[s]))
            for i in self.rx[s][0].findall(form): #find any polygraph match
                # log.info('found polygraph ‘{}’'.format(i))
                try:
                    self.sextracted[ps][s][i]+=1 #self.rx[s].subn('',form)[1] #just the count
                    # log.info('added to polygraph key: {}'.format(i))
                    # log.info('self.sextracted[{}]: ‘{}’'.format(ps,
                    #                                     self.sextracted[ps]))
                except KeyError as e:
                    try:
                        # log.info('self.sextracted[{}]: ‘{}’'.format(ps,
                        #                                 self.sextracted[ps]))
                        self.sextracted[ps][s][i]=1
                        # log.info('made new polygraph key: {}:{} ({})'.format(s,i,e))
                        # log.info('self.sextracted[{}]: ‘{}’'.format(ps,
                        #                                 self.sextracted[ps]))
                    except KeyError as e:
                        try:
                            # log.info('self.sextracted[{}]: ‘{}’'.format(ps,
                            #                                 self.sextracted[ps]))
                            self.sextracted[ps][s]={i:1}
                            # log.info('made new s key: {}:{} ({})'.format(s,i,e))
                            # log.info('self.sextracted[{}]: ‘{}’'.format(ps,
                            #                                 self.sextracted[ps]))
                        except KeyError:
                            self.sextracted[ps]={s:{i:1}}
                            # log.info('made new ps key: {}:{}:{}'.format(ps,s,i))
                            # log.info('self.sextracted[{}]: ‘{}’'.format(ps,
                            #                                 self.sextracted[ps]))
                except AttributeError:
                    try:
                        self.sextracted={ps:{s:{i:1}}}
                        # log.info('made sextracted attribute')
                        # log.info('self.sextracted[{}]: ‘{}’'.format(ps,
                        #                                 self.sextracted[ps]))
                    except Exception as e:
                        log.error("Ouch! No idea what happened! ({})"
                                    "".format(e))
        for polyn in range(4,0,-1): #find and sub longer forms first
            for s in set(self.profilelegit) & set(self.rx.keys()):
                if polyn in self.rx[s]:
                    form=self.rx[s][polyn].sub(s,form) #replace with profile variable
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
        for ps in self.sextracted: # was program['db'].pss[self.analang]:
            scount[ps]={}
            for s in self.rx:
                try:
                    scount[ps][s]=sorted([(x,self.sextracted[ps][s][x])
                        for x in self.sextracted[ps][s]],key=lambda x:x[1],
                                                                reverse=True)
                except KeyError as e:
                    pass
                    # log.info(_("{} KeyError reading {}-{} from sextracted"
                    #             "").format(e,ps,s))
        program['slices'].scount(scount) #send to object
    def notifyuserofextrasegments(self):
        analang=program['params'].analang()
        if analang not in program['db'].segmentsnotinregexes:
            return
        invalids=program['db'].segmentsnotinregexes[analang]
        ninvalids=len(invalids)
        extras=list(dict.fromkeys(invalids).keys())
        if ninvalids >10 and analang != 'en':
            text=_("Your {} database has the following symbols, which are "
                "excluding {} words from being analyzed: \n{}"
                "".format(analang,ninvalids,extras))
            title=_("More than Ten Invalid Characters Found!")
            self.warning=ErrorNotice(text,title=title)
    def slists(self):
        """This sets up the lists of segments, by types. For the moment, it
        just pulls from the segment types in the lift database."""
        log.info("Found db.analangs: {}".format(program['db'].analangs))
        log.info("Found params analang: {}".format(program['params'].analang()))
        self.s={l:{} for l in set(program['db'].analangs+
                                [program['params'].analang()])
                }
        for lang in program['db'].analangs:
            """These should always be there, no matter what"""
            for sclass in [x for x in program['db'].s[lang]
                                        if 'dg' not in x
                                        and 'tg' not in x
                                        and 'qg' not in x
                                        ]: #Just populate each list now
                try:
                    assert sclass in self.polygraphs[lang]
                    pgthere=[k for k,v in self.polygraphs[lang][sclass].items() if v]
                    log.debug("Polygraphs for {} in {}: {}".format(lang,sclass,
                                                                    pgthere))
                    self.s[lang][sclass]=pgthere
                except (AssertionError,AttributeError):
                    self.s[lang][sclass]=list()
                self.s[lang][sclass]+=program['db'].s[lang][sclass]
                """These lines just add to a C list, for a later regex"""
            log.info("Segment lists for {} language: {}".format(lang,
                                                                self.s[lang]))
    def setinvalidcharacters(self):
        self.invalidchars=[' ','...',')','(<field type="tone"><form lang="gnd"><text>'] #multiple characters not working.
        self.invalidregex='( |\.|,|\)|\()+'
        # self.profilelegit=['#','̃','C','N','G','S','V','o'] #In 'alphabetical' order
        self.profilelegit=['#','̃','N','G','S','D','C','Ṽ','V','ʔ','ː',"̀",'=','<'] #'alphabetical' order
    def addtoCVrxs(self,s):
        """This method is just to add a new grapheme while running, so we
        don't have to restart between C/V changes."""
        if not hasattr(self,'analang'): #in case running after startup
            self.analang=program['params'].analang()
        cvt=program['params'].cvt()
        if cvt in ['C', 'V'] and s not in self.s[self.analang][cvt]:
            self.s[self.analang][cvt]+=[s]
            # log.info("Compiling rx list: {}".format(self.s[self.analang][cvt]))
            self.compileCVrxforsclass(cvt)
            # log.info("Compiled rx list: {}".format(self.rx[cvt]))
    def compileCVrxforsclass(self,sclass):
        """This does sorting by length to make longest first"""
        analang=program['params'].analang()
        if sclass not in self.rx:
            self.rx[sclass]={}
        for pn in range(4,-1,-1):
            self.rx[sclass][pn]=rx.s(self.s[analang],sclass,
                                polyn=pn, #limit by glyph length, 0=everything
                                compile=True)
            if self.rx[sclass][pn] == rx.compile('()'):
                # log.info("Empty Regex; removing.")
                del self.rx[sclass][pn]
        # log.info("compileCVrxforsclass RXs: {}".format(self.rx))
        sin=self.s[analang][sclass]
        sout=[i for k,v in self.s[analang].items()
                if (k not in [sclass,'<','='] # no affix boundary or punctuation
                     and (k in ['C','V'] or self.distinguish.get(k)))
                for i in v
                ]
        # log.info("Looking for sclass {} in {}".format(sclass,self.s[self.analang]))
        for n in range(1,7): #just get the Nth C or V, don't worry about polygraphs
            self.rx[sclass+str(n)]=rx.nX(sin,sout,n) #no polygraphs here
    def setupCVrxs(self):
        self.slists() #makes s; depends on polygraphs
        sclassesC=['N','S','G','ʔ','D']
        self.rx={}
        analang=program['params'].analang()
        if not self.s[analang]:
            return # this is pointless until there is data
        #Each glyph variable found in the language gets a regex for each length,
        # plus 0 to find them all together – since we're looking for glyphs.
        for sclass in list(self.s[analang])+['C']: #be sure to do C last
            if self.s[analang][sclass] != []: #don't make if empty
                if sclass in sclassesC and (not hasattr(self,'distinguish')
                        or not self.distinguish.get(sclass)):
                    self.s[analang]['C']+=self.s[analang][sclass]
                    continue
                self.compileCVrxforsclass(sclass)
        #Compile preferred regexs here
        for cc in ['CG','CS','NC','VN','VV']:
            ccc=cc.replace('C','[CSGDʔN]{1}')
            self.rx[cc]=rx.compile(ccc) #no polygraphs here
        for c in sclassesC: #no polygraphs for these, since we're looking for
            # glyph variables, not glyphs.
            # (?!) – negative lookahead
            # (?=) – positive lookahead
            # (?<=) – positive lookbehind
            # (?<!) – negative lookbehind
            if c == 'N':
                #i.e., neither before C nor before word end
                self.rx[c+'_']=rx.compile(c+'(?!([CSGDʔ]|\Z))')
            elif c in ['ʔ','D']:
                self.rx[c+'_']=rx.compile(c+'(?!\Z)') #not word final
            else:
                self.rx[c+'_']=rx.compile('(?<![CSGDNʔ])'+c) #not after C
            self.rx[c+'wd']=rx.compile(c+'(?=\Z)') # word final
    def reloadstatusdatabycvtpsprofile(self,**kwargs):
        # This reloads the status info only for current slice
        # These are specified in iteration, pulled from object if called direct
        start_time=nowruntime()
        kwargs['cvt']=kwargs.get('cvt',program['params'].cvt())
        kwargs['ps']=kwargs.get('ps',program['slices'].ps())
        kwargs['profile']=kwargs.get('profile',program['slices'].profile())
        log.info("Refreshing {} {} {} status settings from LIFT"
                "".format(kwargs['cvt'],kwargs['ps'],kwargs['profile']))
        checks=program['status'].checks(**kwargs)
        kwargs['store']=False #do below
        for kwargs['check'] in checks:
            # log.info("Working on {}".format(c))
            program['status'].build(**kwargs)
            """this just populates groups and the tosort boolean."""
            self.updatesortingstatus(**kwargs)
        logfinished(start_time)
    def reloadstatusdatabycvtps(self,**kwargs):
        # This reloads the status info as relevant on a particular page (ps and
        # cvt), so it needs to be iterated over, or done for each page switch,
        # if desired.
        # These are specified in iteration, pulled from object if called by menu
        start_time=nowruntime()
        kwargs['cvt']=kwargs.get('cvt',program['params'].cvt())
        kwargs['ps']=kwargs.get('ps',program['slices'].ps())
        log.info("Refreshing {} {} status settings from LIFT".format(
                                                                kwargs['ps'],
                                                                kwargs['cvt']))
        profiles=program['slices'].profiles(ps=kwargs['ps']) #This depends on ps only
        for kwargs['profile'] in profiles:
            # log.info("Working on {}".format(p))
            self.reloadstatusdatabycvtpsprofile(**kwargs)
        if kwargs.get('store',True):
            self.storesettingsfile(setting='status')
        logfinished(start_time)
    def reloadstatusdata(self):
        # This fn is very inefficient, as it iterates over everything in
        # profilesbysense, creating status dictionaries for all of that, in
        # order to populate it if found —before removing empty entires.
        # This also has no access to verification information, which comes only
        # from verify()
        start_time=nowruntime()
        log.info("Refreshing all status settings from LIFT")
        w=ui.Wait(parent=program['root'],msg=_("Reloading status data"))
        self.storesettingsfile()
        pss=program['slices'].pss() #this depends on nothing
        pss=program['db'].pss
        #This limits reload to what is there (i.e., only V, if only V has been done)
        # cvts=[i for i in program['params'].cvts() if i in program['status']]
        cvts=program['params'].cvts()
        if not cvts:
            cvts=[i for i in program['params'].cvts()]
        for cvt in [i for i in cvts if i != 'CV']: #this depends on nothing
            # log.info("Working on {}".format(t))
            for ps in pss:
                # log.info("Working on {}".format(ps))
                self.reloadstatusdatabycvtps(cvt=cvt,ps=ps,store=False)
        """Now remove what didn't get data"""
        program['status'].cull()
        if None in program['status']: #This should never be there
            del program['status'][None]
        program['status'].store()
        logfinished(start_time)
        w.close()
    def categorizebygrouping(self,fn,sense,**kwargs):
        #Don't complain if more than one found:
        check=kwargs.get('check',program['params'].check())
        v=fn(
            program['status'].task(),
            sense,check)
        if v in ['','None',None]: #unlist() returns strings
            log.info("Marking senseid {} tosort (v: {})".format(sense.id,v))
            if not kwargs.get('cvt'): #default, not on iteration
                program['status'].marksenseidtosort(sense.id)
            tosort=True
        else:
            log.info("Marking senseid {} sorted (v: {})".format(sense.id,v))
            if not kwargs.get('cvt'): #default, not on iteration
                program['status'].marksenseidsorted(sense.id)
            if v not in ['NA','ALLOK']:
                self._groups.append(v)
    def updatesortingstatus(self, store=True, **kwargs):
        """This reads LIFT to create lists for sorting, populating lists of
        sorted and unsorted senses, as well as sorted (but not verified) groups.
        So don't iterate over it. Instead, use checkforsenseidstosort to just
        confirm tosort status"""
        """To get this from the object, use status.tosort(), todo() or done()"""
        # log.info("updatesortingstatus called with store={} and kwargs: {}"
        #         "".format(store,kwargs))
        cvt=kwargs.get('cvt',program['params'].cvt())
        ps=kwargs.get('ps',program['slices'].ps())
        profile=kwargs.get('profile',program['slices'].profile())
        check=kwargs.get('check',program['params'].check())
        kwargs['wsorted']=True #ever not?
        senseids=program['slices'].senseids(ps=ps,profile=profile)
        log.info("Working on {} senseids: {}".format(len(senseids),senseids))
        program['status'].renewsenseidstosort([],[]) #will repopulate
        self._groups=[]
        if cvt == 'T': #we need to be able to iterate over cvt, to rebuild
            fn=Tone.getsensegroup
        else:
            fn=Segments.getsensegroup
        for sense in [program['db'].sensedict[i] for i in senseids]:
            log.info("Working on sense {}".format(sense.id))
            self.categorizebygrouping(fn,sense,**kwargs)
        #     t = threading.Thread(target=self.categorizebygrouping,
        #                     args=(fn,senseid),
        #                     kwargs=kwargs)
        #     t.start()
        # try:
        #     t.join()
        # except UnboundLocalError:
        #     log.info("The threading didn't happen, or is done already")
        """update 'tosort' status"""
        """update status groups"""
        sorted=set(self._groups)
        program['status'].groups(list(sorted),**kwargs)
        verified=set(program['status'].verified(**kwargs)) #read
        """This should pull verification status from LIFT, someday"""
        program['status'].verified(list(verified&sorted),**kwargs) #set
        log.info("updatesortingstatus results ({}): sorted: {}, verified: {}, "
                "tosort: {}".format(kwargs,sorted,verified,
                                    program['status'].tosort(**kwargs)))
        if store:
            # log.info("updatesortingstatus kwargs: {}".format(kwargs))
            self.storesettingsfile(setting='status')
    def guessanalang(self):
        #have this call set()?
        """if there's only one analysis language, use it."""
        nlangs=len(program['db'].analangs)
        log.debug(_("Found {} analangs: {}".format(nlangs,program['db'].analangs)))
        lxwdata=program['db'].nentrieswlexemedata
        lcwdata=program['db'].nentrieswcitationdata
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
            else:
                program['taskchooser'].splash.withdraw()
                errortext+=_("\nFurthermore, your LIFT file doesn't seem to "
                            "indicate your language code: \n{} "
                            "\nchange that or add some data "
                            "to your database, so I know what language we're "
                            "working on. "
                            "\nOr select a different database on "
                            "the next screen."
                            ).format(self.liftfilename)
                e=ErrorNotice(errortext,title=_("Error!"),wait=True)
                file.writefilename() #just clear the default; let user move on
                sysrestart()
            # program['db'].pss=program['db'].getpssbylang(self.analang) #redo this, specify
            # return
        elif nlangs == 1:
            self.analang=program['db'].analangs[0]
            log.debug(_('Only one analang in file; using it: ({})'.format(
                                                        program['db'].analangs[0])))
            """If there are more than two analangs in the database, check if one
            of the first two is three letters long, and the other isn't"""
        elif nlangs == 2:
            if ((len(program['db'].analangs[0]) == 3) and
                (lcwdatamax == program['db'].analangs[0] or
                    lxwdatamax == program['db'].analangs[0]) and
                (len(program['db'].analangs[1]) != 3)):
                log.debug(_('Looks like I found an iso code with data for '
                                'analang! ({})'.format(program['db'].analangs[0])))
                self.analang=program['db'].analangs[0] #assume this is the iso code
                self.analangdefault=program['db'].analangs[0] #In case it gets changed.
            elif ((len(program['db'].analangs[1]) == 3) and
                (lcwdatamax == program['db'].analangs[1] or
                    lxwdatamax == program['db'].analangs[1]) and
                    (len(program['db'].analangs[0]) != 3)):
                log.debug(_('Looks like I found an iso code with data for '
                                'analang! ({})'.format(program['db'].analangs[1])))
                self.analang=program['db'].analangs[1] #assume this is the iso code
                self.analangdefault=program['db'].analangs[1] #In case it gets changed.
            elif lcwdatamax in program['db'].analangs:
                self.analang=lcwdatamax
                log.debug('Neither analang looks like an iso code, taking the '
                'one with most citation data: {}'.format(program['db'].analangs))
            elif lxwdatamax in program['db'].analangs:
                self.analang=lxwdatamax
                log.debug('Neither analang looks like an iso code, taking the '
                'one with most lexeme data: {}'.format(program['db'].analangs))
            else:
                self.analang=program['db'].analangs[0]
                log.debug('Neither analang looks like an iso code, nor has much'
                'data; taking the first one: {}'.format(program['db'].analangs))
        else: #for three or more analangs, take the first plausible iso code
            if lcwdatamax in program['db'].analangs and len(lcwdatamax) == 3:
                self.analang=lcwdatamax
                log.debug('The language with the most citation data looks like '
                'an iso code; using: {}'.format(program['db'].analangs))
            elif lcwdatamax == lxwdatamax and lxwdatamax in program['db'].analangs:
                self.analang=lxwdatamax
                log.debug('The language with the most citation data is also '
                    'the language with the most lexeme data; using: {}'.format(
                                                            program['db'].analangs))
            elif lxwdatamax in program['db'].analangs and len(lxwdatamax) == 3:
                self.analang=lxwdatamax
                log.debug('The language with the most lexeme data looks like '
                'an iso code; using: {}'.format(program['db'].analangs))
            else:
                for n in range(1,nlangs+1): # end with first
                    self.analang=program['db'].analangs[-n]
                    log.debug(_('trying {}').format(self.analang))
                    if len(program['db'].analangs[-n]) == 3:
                        log.debug(_('Looks like I found an iso code for '
                                'analang! ({})'.format(program['db'].analangs[n-1])))
                        break #stop iterating, and keep this one.
        log.info("analang guessed: {} (If you don't like this, change it in "
                    "the menus)".format(self.analang))
    def guessaudiolang(self):
        nlangs=len(program['db'].audiolangs)
        """if there's only one audio language, use it."""
        if nlangs == 0 and self.analang:
            self.audiolang=lift.Lift.makeaudiolangname(self) #program['db'].audiolangs[0]
        if nlangs == 1:
            self.audiolang=program['db'].audiolangs[0]
        elif nlangs == 2:
            if ((self.analang in program['db'].audiolangs[0]) and
                (self.analang not in program['db'].audiolangs[1])):
                self.audiolang=program['db'].audiolangs[0]
                log.info("Analang in first of two audiolangs only, selecting "
                                            "{}".format(self.audiolang))
            elif ((self.analang in program['db'].audiolangs[1]) and
                    (self.analang not in program['db'].audiolangs[0])):
                self.audiolang=program['db'].audiolangs[1]
                log.info("Analang in second of two audiolangs only, selecting "
                                            "{}".format(self.audiolang))
            elif ((self.analang in program['db'].audiolangs[1]) and
                    (self.analang in program['db'].audiolangs[0])):
                self.audiolang=sorted(program['db'].audiolangs,key = len)[0]
                log.info("Analang in both of two audiolangs only, selecting "
                "shorter: {}".format(self.audiolang))  #assume is more basic
        else: #for three or more analangs, take the first plausible iso code
            for n in range(nlangs):
                if self.analang in program['db'].analangs[n]:
                    self.audiolang=program['db'].audiolangs[n]
                    return
    def makeglosslangs(self):
        if self.glosslangs:
            self.glosslangs=Glosslangs(self.glosslangs)
        else:
            self.glosslangs=Glosslangs()
    def checkglosslangs(self):
        if self.glosslangs:
            for lang in self.glosslangs:
                if lang not in program['db'].glosslangs:
                    self.glosslangs.rm(lang)
        if not self.glosslangs:
            self.guessglosslangs()
    def guessglosslangs(self):
        """if there's only one gloss language, use it."""
        if len(program['db'].glosslangs) == 1:
            log.info('Only one glosslang!')
            self.glosslangs.lang1(program['db'].glosslangs[0])
            """if there are two or more gloss languages, just pick the first
            two, and the user can select something else later (the gloss
            languages are not for CV profile analaysis, but for info after
            checking, when this can be reset."""
        elif len(program['db'].glosslangs) > 1:
            self.glosslangs.lang1(program['db'].glosslangs[0])
            self.glosslangs.lang2(program['db'].glosslangs[1])
        else:
            print("Can't tell how many glosslangs!",len(program['db'].glosslangs))
    def guesscvt(self):
        """For now, if cvt isn't set, start with Vowels."""
        self.set('cvt','V')
    def refreshattributechanges(self):
        """I need to think through these; what things must/should change when
        one of these attributes change? Especially when we've changed a few...
        """
        if not hasattr(self,'attrschanged'):
            return
        if 'status' in program:
            program['status'].build()
        t=program['params'].cvt()
        if 'cvt' in self.attrschanged:
            program['status'].updatechecksbycvt()
            program['status'].makecheckok()
            self.attrschanged.remove('cvt')
        if 'ps' in self.attrschanged:
            if t == 'T':
                program['status'].updatechecksbycvt()
            self.attrschanged.remove('ps')
        if 'profile' in self.attrschanged:
            if t != 'T':
                program['status'].updatechecksbycvt()
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
        CheckParameters(self.analang,self.audiolang)
    def maketoneframes(self,dict={}):
        ToneFrames(dict)
        # ToneFrames(getattr(self,'toneframes',{}))
    def makestatus(self,dict={}):
        # log.info("Making status object with value {}".format(program['status']))
        StatusDict(self.settingsfile('status'),dict)
        # log.info("Made status object with value {}".format(program['status']))
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
                # self.reloadprofiledata()
                log.info("**Changed {}; should restart!**".format(attribute))
            elif refresh == True:
                self.refreshattributechanges()
        else:
            log.debug(_('No change: {} == {}'.format(attribute,choice)))
    def setsecondformfieldN(self,choice,window=None):
        self.secondformfield[self.nominalps]=self.pluralname=choice
        self.attrschanged.append('secondformfield')
        for entry in program['db'].entries:
            entry.plvalue(self.pluralname,program['params'].analang) # get the right field!
        self.refreshattributechanges()
        if window:
            window.destroy()
    def setsecondformfieldV(self,choice,window=None):
        self.secondformfield[self.verbalps]=self.imperativename=choice
        self.attrschanged.append('secondformfield')
        for entry in program['db'].entries:
            entry.impvalue(self.imperativename,program['params'].analang) # get the right field!
        self.refreshattributechanges()
        if window:
            window.destroy()
    def setnextprofile(self):
        r=program['status'].nextprofile()
        if r:
            firstcheck=program['status'].updatechecksbycvt()[0]
            if program['params'].check() != firstcheck:
                program['params'].check(firstcheck)
                self.attrschanged.append('check')
            self.attrschanged.append('profile')
            self.refreshattributechanges()
    def setprofile(self,choice,window):
        program['slices'].profile(choice)
        #in case checks changed:
        firstcheck=program['status'].updatechecksbycvt()[0]
        if program['params'].check() != firstcheck:
            program['params'].check(firstcheck)
            self.attrschanged.append('check')
        self.attrschanged.append('profile')
        self.refreshattributechanges()
        window.destroy()
    def setcvt(self,choice,window=None):
        program['params'].cvt(choice)
        self.attrschanged.append('cvt')
        self.refreshattributechanges()
        if (not hasattr(program['taskchooser'],'task') or
                not program['taskchooser'].task.mainwindow):
            log.info("No task, apparently, so not worried about changing cvt")
        elif isinstance(program['taskchooser'].task,Transcribe):
            log.info("Switching Transcribe tasks")
            newtaskclass=getattr(sys.modules[__name__],'Transcribe'+choice)
            program['status'].makecheckok() #this is intentionally broad: *any* check
            program['taskchooser'].maketask(newtaskclass)
        elif isinstance(program['taskchooser'].task,Sort):
            # log.info("Switching Sort tasks")
            newtaskclass=getattr(sys.modules[__name__],'Sort'+choice)
            program['status'].makecheckok() #this is intentionally broad: *any* check
            program['taskchooser'].maketask(newtaskclass)
        else:
            log.info("Not Sorting or Transcribing; chilling with cvt change.")
        if window:
            window.destroy()
    def setanalang(self,choice,window):
        program['params'].analang(choice)
        self.attrschanged.append('analang')
        self.refreshattributechanges()
        window.destroy()
        program['taskchooser'].restart()
    def setgroup(self,choice,window):
        # log.debug("group: {}".format(choice))
        program['status'].group(choice)
        # log.debug("group: {}".format(choice))
        window.destroy()
        # log.debug("group: {}".format(choice))
    def setgroup_comparison(self,choice,window):
        if hasattr(self,'group_comparison'):
            log.debug("group_comparison: {}".format(self.group_comparison))
        self.set('group_comparison',choice,window,refresh=False)
        log.debug("group_comparison: {}".format(self.group_comparison))
    def setnextcheck(self,**kwargs):
        program['status'].nextcheck(**kwargs)
        self.attrschanged.append('check')
        self.refreshattributechanges()
    def setcheck(self,choice,window=None):
        program['params'].check(choice)
        self.attrschanged.append('check')
        self.refreshattributechanges()
        if window:
            window.destroy()
    def setbuttoncolumns(self,choice,window=None):
        self.buttoncolumns=program['taskchooser'].mainwindowis.buttoncolumns=choice
        if window:
            window.destroy()
    def setmaxprofiles(self,choice,window):
        self.maxprofiles=choice
        window.destroy()
    def setmaxpss(self,choice,window):
        self.maxpss=choice
        window.destroy()
    def setmulticheckscope(self,choice,window):
        self.cvtstodo=program['taskchooser'].task.cvtstodo=choice
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
    def setparserasklevel(self,choice,window):
        program['taskchooser'].parser.asklevel(choice)
        window.destroy()
    def setparserautolevel(self,choice,window):
        program['taskchooser'].parser.autolevel(choice)
        window.destroy()
    def setps(self,choice,window):
        program['slices'].ps(choice)
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
        # log.info("setsoundcardindex: {}".format(choice))
        self.soundsettings.audio_card_in=choice
        window.destroy()
    def setsoundcardoutindex(self,choice,window):
        # log.info("setsoundcardoutindex: {}".format(choice))
        self.soundsettings.audio_card_out=choice
        window.destroy()
    def langnames(self,langs=None):
        """This is for getting the prose name for a language from a code."""
        """It should ultimately use a xyz.ldml file, produced (at least)
        by WeSay, but for now is just a dict."""
        log.info("Setting up language names")
        #ET.register_namespace("", 'palaso')
        ns = {'palaso': 'urn://palaso.org/ldmlExtensions/v1'}
        node=None
        self.languagenames={}
        if not langs:
            langs=[self.analang]+program['db'].analangs+program['db'].glosslangs
        for xyz in langs:
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
            program['status'].makecvtok()
            program['slices'].makepsok()
            program['slices'].makeprofileok()
            program['status'].makecheckok() #this is intentionally broad: *any* check
        except KeyError as e:
            log.info(_("Maybe status/slices aren't set up yet."))
        # program['status'].makegroupok(wsorted=True)
    def setrefreshdelay(self):
        """This sets the main window refresh delay, in miliseconds"""
        if (hasattr(program['taskchooser'].mainwindowis,'runwindow') and
                program['taskchooser'].mainwindowis.runwindow.winfo_exists()):
            self.refreshdelay=10000 #ten seconds if working in another window
        elif isinstance(self,Parse) and not hasattr(self,'parser'):
            self.refreshdelay=1 #1 msecond if waiting for parser settings
        else:
            self.refreshdelay=1000 #one second if not working in another window
    def __init__(self,taskchooser):
        program['settings']=self
        self.liftfilename=taskchooser.filename
        self.getdirectories() #incl settingsfilecheck and repocheck
        self.setinvalidcharacters()
        # self.settingsfilecheck()
        self.settingsinit() #init, clear, fields
        self.loadsettingsfile()
        self.loadsettingsfile(setting='profiledata')
        """I think I need this before setting up regexs"""
        if hasattr(taskchooser,'analang'): #i.e., new file
            self.analang=taskchooser.analang #I need to keep this alive until objects are done
            program['db'].getpss() #redo this, specify
        else:
            self.guessanalang() #needed for regexs
        if not self.analang:
            log.error("No analysis language; exiting.")
            return
        #set the field names used in this db:
        self.pss() #sets self.nominalps and self.verbalps
        self.fields() #sets self.pluralname and self.imperativename
        self.langnames()
        self.guessaudiolang()
        self.loadsettingsfile() # overwrites guess above, stored on runcheck
        self.makeglosslangs()
        self.checkglosslangs() #if stated aren't in db, guess
        self.makeparameters() #depends on nothing but self.analang
        self.settingsobjects() #should do this more; can be redone!
        self.moveattrstoobjects()
        self.trackuntrackedfiles()
        if not self.buttoncolumns:
            self.setbuttoncolumns(1)
        # these two make the objects
        self.loadsettingsfile(setting='status')
        self.loadsettingsfile(setting='toneframes')
        self.loadsettingsfile(setting='adhocgroups')
        self.makeeverythingok()
        """The following might be OK here, but need to be OK later, too."""
        # """The following should only be done after word collection"""
        # if self.taskchooser.donew['collectionlc']:
        #     self.ifcollectionlc()
        self.attrschanged=[]
class TaskDressing(HasMenus,ui.Window):
    """This Class covers elements that belong to (or should be available to)
    all tasks, e.g., menus and button appearance."""
    def taskicon(self):
        return program['theme'].photo['icon'] #default
    def tasktitle(self):
        return _("Unnamed {} Task ({})".format(program['name'],
                                                type(self).__name__))
    def _taskchooserbutton(self):
        if isinstance(self,TaskChooser) and not self.showreports:
            if self.datacollection:
                text=_("Analyze")
            else:
                text=_("Collect Data")
        elif isinstance(self,Report):
            text=_("Reports")
            program['taskchooser'].showreports=True
        else:
            text=_("Tasks")
        if hasattr(self,'chooserbutton'):
            self.chooserbutton.destroy()
        self.chooserbutton=ui.Button(self.outsideframe,text=text,
                                    font='small',
                                    cmd=program['taskchooser'].gettask,
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
    def correlatemenus(self):
        log.info("Menus: {}; {} (chooser)".format(self.menu,program['taskchooser'].menu))
        if hasattr(self,'task'):
            log.info("Menus: {}; {} (task)".format(self.menu,self.task.menu))
        if self.menu != program['taskchooser'].menu: #for tasks
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
    def hidedetails(self):
        # log.info("Hiding group names")
        program['settings'].set('showdetails', False, refresh=True)
        self.setcontext()
    def showdetails(self):
        # log.info("Showing group names")
        program['settings'].set('showdetails', True, refresh=True)
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
        if hasattr(program['settings'],
                    'showdetails') and program['settings'].showdetails:
            self.context.menuitem(_("Hide details"),self.hidedetails)
        else:
            self.context.menuitem(_("Show details"),self.showdetails)
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
        tasks=_("Tasks")
        t.tt=ui.ToolTip(t,text=_("click ‘{}’ to change tasks").format(tasks))
        # t.bind("<Button-1>",program['taskchooser'].gettask)
    def fullscreen(self):
        w, h = self.parent.winfo_screenwidth(), self.parent.winfo_screenheight()
        self.parent.geometry("%dx%d+0+0" % (w, h))
    def quarterscreen(self):
        w, h = self.parent.winfo_screenwidth(), self.parent.winfo_screenheight()
        w=w/2
        h=h/2
        self.parent.geometry("%dx%d+0+0" % (w, h))
    def inherittaskattrs(self):
        for attr in ['file',
                    'mainrelief',
                    'fontthemesmall',
                    'buttoncolumns',
                    'showdetails'
                    ]:
            if hasattr(self.parent,attr):
                setattr(self,attr,getattr(self.parent,attr))
        # Make these directly available:
        for attr in [
                    'glosslangs',
                    'buttoncolumns',
                    ]:
            if hasattr(program['settings'],attr):
                setattr(self,attr,getattr(program['settings'],attr))
            else:
                log.info("Didn't find {} in {}".format(attr,program['settings']))
        #For convenience:
        self.analang=program['params'].analang()
    def makecvtok(self):
        # log.info("cvt: {}".format(program['params'].cvt()))
        if isinstance(self,Tone) and not program['params'].cvt() == 'T':
            program['settings'].setcvt('T')
        if isinstance(self,Segments) and (program['params'].cvt()
                                                    not in ['V','C','CV']):
            program['settings'].setcvt('V')
    def trystatusframelater(self,dict):
        program['settings'].setrefreshdelay()
        self.parent.after(program['settings'].refreshdelay,self.makestatusframe,dict)
    def makestatusframe(self,dict=None):
        dictnow={
                'mainrelief':self.mainrelief,
                'showdetails':program['settings'].showdetails, #attr, not task.method
                'self.fontthemesmall':self.fontthemesmall,
                'buttonkwargs':self.dobuttonkwargs(),
                'iflang':program['settings'].interfacelangwrapper(),
                'analang':program['params'].analang(),
                'glang1':self.glosslangs.lang1(),
                'glang2':self.glosslangs.lang2(),
                'secondformfield':str(program['settings'].secondformfield),
                'maxprofiles':program['settings'].maxprofiles,
                'maxpss':program['settings'].maxpss
                }
        if 'slices' in program:
            dictnow.update({
                'cvt':program['params'].cvt(),
                'check':program['params'].check(),
                'ps':program['slices'].ps(),
                'profile':program['slices'].profile(),
                'group':program['status'].group(),
                'tableiteration':self.tableiteration,
                })
            if isinstance(self,Multicheck):
                dictnow.update({'cvtstodo':self.task.cvtstodo})
        if isinstance(self,Parse):
            if not hasattr(self,'parser'):
                log.info("No parser yet; waiting")
                self.trystatusframelater(dictnow)
                return
            else:
                dictnow.update({
                    'parserasklevel':self.parser.ask,
                    'parserautolevel':self.parser.auto,
                    'senseid':self.task.sensetodo,
                    })
        """Call this just once. If nothing changed, wait; if changes, run,
        then run again."""
        if dict == dictnow:
            # log.info("No dict changes; no updating the UI: {}".format(dictnow))
            self.trystatusframelater(dictnow)
            return
        # log.info("Dict changes; checking attributes and updating the UI. ({})"
        #                                                     "".format(dictnow))
        if program['taskchooser'].donew['collectionlc']:
            program['settings'].makeeverythingok()
        #This will probably need to be reworked
        if self.exitFlag.istrue():
            return
        if hasattr(self.frame,'status') and self.frame.status.winfo_exists():
            self.frame.status.destroy()
        self.frame.status=StatusFrame(self.frame, self,
                                        relief=self.mainrelief,
                                        row=1, column=0, sticky='nw')
        self.frame.update_idletasks()
        program['settings'].storesettingsfile()
        self.makestatusframe(dictnow)
    def setSdistinctions(self):
        def notice(changed):
            def confirm():
                ok.value=True
                w.destroy()
            ti=_("Important Notice!")
            w=ui.Window(self,title=ti)
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
                    if s in program['settings'].distinguish:
                        if program['settings'].distinguish[s]==changed[s][1]:
                            program['settings'].distinguish[s]=changed[s][0] #(oldvar,newvar):
                        else:
                            log.error("Changed to value ({}) doesn't match "
                            "current setting for ‘{}’: {}".format(changed[s][1],
                                                        s,self.distinguish[s]))
                    elif s in program['settings'].interpret:
                        if program['settings'].interpret[s]==changed[s][1]:
                            program['settings'].interpret[s]=changed[s][0] #(oldvar,newvar):
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
            log.debug('self.distinguish: {}'.format(program['settings'].distinguish))
            log.debug('self.interpret: {}'.format(program['settings'].interpret))
            if changed:
                log.info('There was a change; we need to redo the analysis now.')
                log.info('The following changed (from,to): {}'.format(changed))
                self.storesettingsfile()
                r=notice(changed)
                if r:
                    self.runwindow.destroy()
                    self.storesettingsfile(setting='profiledata')
                    program['taskchooser'].restart()
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
        program['settings'].checkinterpretations()
        analang=program['params'].analang()
        options=Options(r=0,padx=50,pady=10,c=0,vars={},frames={})
        for s in program['settings'].distinguish: #Should be already set.
            options.vars[s] = ui.BooleanVar()
            options.vars[s].set(program['settings'].distinguish[s])
        for s in program['settings'].interpret: #This should already be set, even by default
            options.vars[s] = ui.StringVar()
            options.vars[s].set(program['settings'].interpret[s])
        """Page title and instructions"""
        self.runwindow.title(_("Set Parameters for Segment Interpretation"))
        mwframe=self.runwindow.frame
        title=_("Interpret {} Segments"
                ).format(program['settings'].languagenames[analang])
        titl=ui.Label(mwframe,text=title,font='title',
                justify=ui.LEFT,anchor='c')
        titl.grid(row=options.get('r'), column=options.get('c'), #self.runwindow.options['column'],
                    sticky='ew', padx=options.padx, pady=10)
        options.next('r')
        text=_("Here you can view and set parameters that change how {} "
        "interprets {} segments \n(consonant and vowel glyphs/characters)"
                ).format(program['name'],program['settings'].languagenames[analang])
        instr=ui.Label(mwframe,text=text,justify=ui.LEFT,anchor='c')
        instr.grid(row=options.get('r'), column=options.get('c'),
                    sticky='ew', padx=options.padx, pady=options.pady)
        """The rest of the page"""
        self.runwindow.scroll=ui.ScrollingFrame(mwframe)
        self.runwindow.scroll.grid(row=2,column=0)
        log.debug('self.distinguish: {}'.format(program['settings'].distinguish))
        log.debug('self.interpret: {}'.format(program['settings'].interpret))
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
        if analang in program['db'].s and 'D' in program['db'].s[analang]:
            depressors=program['db'].s[analang]['D']
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
        window=ui.Window(self, title=_('Select Interface Language'))
        ui.Label(window.frame, text=_('What language do you want {} '
                                'to address you in?').format(program['name'])
                ).grid(column=0, row=0)
        buttonFrame1=ui.ButtonFrame(window.frame,
                                optionlist=program['taskchooser'].interfacelangs,
                                command=program['settings'].interfacelangwrapper,
                                window=window,
                                column=0, row=1
                                )
    def getanalangname(self,event=None):
        log.info("this sets the language name")
        def submit(event=None):
            program['settings'].languagenames[self.analang]=namevar.get()
            if (not hasattr(program['settings'],'adnlangnames') or
                    not program['settings'].adnlangnames):
                program['settings'].adnlangnames={}
            if "Language with code [" not in namevar.get():
                program['settings'].adnlangnames[self.analang]=namevar.get()
                # if self.analang in self.adnlangnames:
            program['settings'].storesettingsfile()
            window.destroy()
        window=ui.Window(self,title=_('Enter Analysis Language Name'))
        curname=program['settings'].languagenames[self.analang]
        defaultname=_("Language with code [{}]").format(self.analang)
        t=_("How do you want to display the name of {}").format(curname)
        if curname != defaultname:
            t+=_(", with ISO 639-3 code [{}]").format(self.analang)
        t+='?' # _("Language with code [{}]").format(xyz)
        ui.Label(window.frame,text=t,row=0,column=0,sticky='e',columnspan=2)
        namevar=ui.StringVar()
        name = ui.EntryField(window.frame,textvariable=namevar,
                            row=1,column=0,
                            sticky='e')
        name.focus_set()
        name.bind('<Return>',submit)
        ui.Button(window.frame,text='OK',cmd=submit,row=1,column=1,sticky='w')
    def getanalang(self,event=None):
        if len(program['db'].analangs) <2: #The user probably wants to change display.
            self.getanalangname()
            return
        log.info("this sets the language")
        # fn=inspect.currentframe().f_code.co_name
        window=ui.Window(self,title=_('Select Analysis Language'))
        if program['db'].analangs is None :
            ui.Label(window.frame,
                          text='Error: please set Lift file first! ('
                          +str(program['db'].filename)+')'
                          ).grid(column=0, row=0)
        else:
            ui.Label(window.frame,
                          text=_('What language do you want to analyze?')
                          ).grid(column=0, row=1)
            langs=list()
            for lang in program['db'].analangs:
                langs.append({'code':lang,
                                'name':program['settings'].languagenames[lang]})
                # print(lang, program['taskchooser'].languagenames[lang])
            buttonFrame1=ui.ButtonFrame(window.frame,
                                     optionlist=langs,
                                     command=program['settings'].setanalang,
                                     window=window,
                                     column=0, row=4
                                     )
    def getglosslang(self,event=None):
        window=ui.Window(self,title=_('Select Gloss Language'))
        text=_('What Language do you want to use for glosses?')
        ui.Label(window.frame, text=text, column=0, row=1)
        langs=list()
        for lang in program['db'].glosslangs:
            langs.append({'code':lang,
                            'name':program['settings'].languagenames[lang]})
        buttonFrame1=ui.ButtonFrame(window.frame,
                                 optionlist=langs,
                                 command=program['settings'].setglosslang,
                                 window=window,
                                 column=0, row=4
                                 )
    def getglosslang2(self,event=None):
        window=ui.Window(self,title='Select Second Gloss Language')
        text=_('What other language do you want to use for glosses?')
        ui.Label(window.frame, text=text, column=0, row=1)
        langs=list()
        for lang in program['db'].glosslangs:
            if lang == program['settings'].glosslangs[0]:
                continue
            langs.append({'code':lang,
                            'name':program['settings'].languagenames[lang]})
        langs.append({'code':None, 'name':'just use '
                +program['settings'].languagenames[program['settings'].glosslangs.lang1()]})
        buttonFrame1=ui.ButtonFrame(window.frame,
                                    optionlist=langs,
                                    command=program['settings'].setglosslang2,
                                    window=window,
                                    column=0, row=4
                                    )
    def getcvt(self,event=None):
        log.debug(_("Asking for check cvt/type"))
        window=ui.Window(self,title=_('Select Check Type'))
        cvts=[]
        x=0
        tdict=program['params'].cvtdict()
        for cvt in tdict:
            if cvt == 'CV' and (isinstance(self.task,Sort) or
                                isinstance(self.task,Transcribe)):
                continue
            cvts.append({})
            cvts[x]['name']=tdict[cvt]['pl']
            cvts[x]['code']=cvt
            x+=1
        ui.Label(window.frame, text=_('What part of the sound system do you '
                                    'want to work with?')
            ).grid(column=0, row=0)
        buttonFrame1=ui.ButtonFrame(window.frame,
                                    optionlist=cvts,
                                    command=program['settings'].setcvt,
                                    window=window,
                                    column=0, row=1
                                    )
        return window
    def getparserlevels(self,event=None):
        try:
            levels=self.parser.levels()
            levels=[(k,levels[k]) for k in levels]
            levels.sort(key=lambda x:x[0],reverse=True)
            return levels
        except AttributeError as e:
            log.info("Evidently there isn't a parser running ({})".format(e))
            return
    def getparserasklevel(self,event=None):
        log.info("Asking for parserasklevel...")
        levels=self.getparserlevels()
        if not levels:
            return
        window=ui.Window(self, title=_('Select Parser Ask Level'))
        ui.Label(window.frame, text=_('What level of parsing match do you want '
                                    'the parser to confirm with you?'),
                                    column=0, row=0)
        buttonFrame1=ui.ScrollingButtonFrame(
                                window.frame,
                                optionlist=levels,
                                command=program['settings'].setparserasklevel,
                                window=window,
                                column=0, row=1
                                            )
    def getparserautolevel(self,event=None):
        log.info("Asking for parserautolevel...")
        levels=self.getparserlevels()
        if not levels:
            return
        window=ui.Window(self, title=_('Select Parser Auto Level'))
        ui.Label(window.frame, text=_('What level of parsing match do you want '
                                    'the parser to do automatically?'),
                                    column=0, row=0)
        buttonFrame1=ui.ScrollingButtonFrame(
                                window.frame,
                                optionlist=levels,
                                command=program['settings'].setparserautolevel,
                                window=window,
                                column=0, row=1
                                            )
    def getps(self,event=None):
        log.info("Asking for ps...")
        # self.refreshattributechanges()
        window=ui.Window(self, title=_('Select Lexical Category'))
        ui.Label(window.frame, text=_('What lexical category do you '
                                    'want to work with (Part of speech)?')
                ).grid(column=0, row=0)
        if hasattr(self,'additionalps') and program['settings'].additionalps is not None:
            pss=program['db'].pss+program['settings'].additionalps #these should be lists
        else:
            pss=program['db'].pss
        buttonFrame1=ui.ScrollingButtonFrame(window.frame,
                                            optionlist=pss,
                                            command=program['settings'].setps,
                                            window=window,
                                            column=0, row=1
                                            )
    def getprofile(self,event=None,**kwargs):
        log.info("Asking for profile...")
        # self.refreshattributechanges()
        window=ui.Window(self,title=_('Select Syllable Profile'))
        ps=program['slices'].ps()
        if program['settings'].profilesbysense[ps] is None: #likely never happen...
            ui.Label(window.frame,
            text=_('Error: please set Grammatical category with profiles '
                    'first!')+' (not '+str(ps)+')'
            ).grid(column=0, row=0)
        else:
            profilecounts=program['slices'].valid()
            profilecountsAdHoc=program['slices'].adhoccounts()
            profiles=program['status'].profiles(**kwargs)
            if profilecountsAdHoc:
                adhocdict=program['slices'].adhoc()
                profilecounts.update(profilecountsAdHoc)
                if ps in adhocdict:
                    profiles+=program['slices'].adhoc()[ps].keys()
            profiles=dict.fromkeys(profiles)
            if not profiles:
                log.error("No profiles of {} type found!".format(kwargs))
            # log.info("count types: {}, {}".format(type(profilecounts),
            #                                         type(profilecountsAdHoc)))
            ui.Label(window.frame, text=_('What ({}) syllable profile do you '
                                    'want to work with?'.format(ps))
                                    ).grid(column=0, row=0)
            optionslist = [(x,profilecounts[(x,ps)]) for x in profiles]
            """What does this extra frame do?"""
            window.scroll=ui.Frame(window.frame)
            window.scroll.grid(column=0, row=1)
            buttonFrame1=ui.ScrollingButtonFrame(window.scroll,
                                    optionlist=optionslist,
                                    command=program['settings'].setprofile,
                                    window=window,
                                    column=0, row=0
                                    )
            window.wait_window(window)
    def setsensetodo(self,choice,window):
        self.sense=self.sensetodo=choice
        window.destroy()
        if isinstance(self,WordCollection):
            self.withdraw()
            self.getword()
    def getsensetodobyletter(self,choice,window,event=None):
        window.on_quit()
        msg=_("Preparing to ask for a sense...")
        log.info(msg)
        senses=program['db'].senses
        todo=len(senses)
        list=[(k,k.formatted(self.analang,self.glosslangs))
                for k in senses
                if k.formatted(self.analang,self.glosslangs).startswith(choice)]
        list.sort(key=lambda x:x[1])
        window=ui.Window(self, title=_('Select Lexical Item'))
        ui.Label(window.frame, text=_('What sense do you want to work with?'),
                            column=0, row=0)
        buttonFrame1=ui.ScrollingButtonFrame(window.frame,
                                            optionlist=list,
                                            command=self.setsensetodo,
                                            window=window,
                                            column=0, row=1
                                            )
        window.lift()
    def getsensetodo(self,event=None):
        msg=_("Preparing to ask for a sense letter...")
        log.info(msg)
        # self.wait(msg=msg)
        senses=program['db'].senses
        todo=len(senses)
        kcounts=collections.Counter([k.formatted(self.analang,self.glosslangs)[0]
                                            for k in senses]
                                    ).most_common()
        if len(kcounts)<15: #When few choices, use first two letters
            kcounts=collections.Counter([k.formatted(self.analang,
                                                    self.glosslangs)[:2]
                                            for k in senses]
                                    ).most_common()

        letters=[{'code':k,'description':v} for k,v in kcounts]
        # log.info("Counts: {}".format(kcounts))
        # letters=list([(k,k,v) for k,v in kcounts])
        log.info("letters: {}".format(letters))
        if not letters:
            log.info("No senseids; sort something?")
            return
        letters=[{'code':None,'description':_("All words")}
        ]+letters
        window=ui.Window(self, title=_('Select Lexical Item'))
        ui.Label(window.frame, text=_('What letter does your sense start with?'),
                            column=0, row=0)
        buttonFrame1=ui.ScrollingButtonFrame(window.frame,
                                            optionlist=letters,
                                            command=self.getsensetodobyletter,
                                            window=window,
                                            column=0, row=1
                                            )
        window.lift()
    def getsecondformfieldN(self,event=None):
        ps=program['settings'].nominalps
        opts=program['settings'].plopts
        othername=program['settings'].imperativename
        setcmd=program['settings'].setsecondformfieldN
        self.getsecondformfield(ps,opts,othername,setcmd)
    def getsecondformfieldV(self,event=None):
        # log.info(".impopts: {}".format(program['settings'].impopts))
        ps=program['settings'].verbalps
        opts=program['settings'].impopts
        othername=program['settings'].pluralname
        setcmd=program['settings'].setsecondformfieldV
        self.getsecondformfield(ps,opts,othername,setcmd)
    def getcustomsecondformfield(self,ps,othername,setcmd):
        def updateerror(event=None):
            if event.keysym != 'Return':
                self.errorlabel['text'] = ''
        def submitform(event=None):
            log.info("setting {} (not {})".format(custom.get(), othername))
            if custom.get() == othername:
                text=_("That name is already used!")
                log.error(text)
                self.errorlabel['text']=text
                return
            setcmd(custom.get())
            window.on_quit()
        title=_('Make Custom Second Form Field for {}').format(ps)
        window=ui.Window(self,title=title)
        #should never be othername
        l=ui.Label(window,
                text=_("What field name do you want to use for {} words?"
                        ).format(ps),
                row=0,column=0)
        custom=ui.StringVar()
        formfield = ui.EntryField(window, render=True,
                                    textvariable=custom,
                                    row=1,column=0,
                                    sticky='')
        formfield.focus_set()
        formfield.bind('<Return>',submitform)
        formfield.bind('<KeyRelease>',updateerror)
        self.errorlabel=ui.Label(window,text='',
                            fg='red',
                            wraplength=int(self.frame.winfo_screenwidth()/3),
                            row=2,column=0,sticky='nsew'
                            )
    def getsecondformfield(self,ps,opts,othername,setcmd,other=False):
        def getother():
            window.destroy()
            self.getsecondformfield(ps=ps,
                                    opts=opts,
                                    othername=othername,
                                    setcmd=setcmd,
                                    other=True)
        def getcustom():
            window.destroy()
            self.getcustomsecondformfield(ps=ps,
                                    # opts=opts,
                                    othername=othername,
                                    setcmd=setcmd,
                                    # other=True
                                    )
        log.info("Asking for ‘{}’ second form field...".format(ps))
        try:
            assert other == False
            othernames=[i for i in program['db'].fieldnames[self.analang]
                    if i != othername]
        except (KeyError,AssertionError):
            othernames=[]
        title=_('Select Second Form Field for {}').format(ps)
        window=ui.Window(self,title=title)
        if othernames:
            text=_("What is the database field for second forms for ‘{}’ words?"
            "".format(ps))
            optionslist=othernames
        else:
            text=_("What database field name do you want to use for second "
            "forms for {} words?".format(ps))
            optionslist=opts
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
        if othernames:
            otherbutton=ui.Button(buttonFrame1.content,
                            text=_("None of these; make a new field"),
                            column=0, row=1,
                            cmd=getother
                            )
        else:
            otherbutton=ui.Button(buttonFrame1.content,
                            text=_("None of these work; make my own field"),
                            column=0, row=1,
                            cmd=getcustom
                            )
        window.wait_window(window)
    def getmulticheckscope(self,event=None):
            log.info("Asking for multicheckscope...")
            window=ui.Window(self, title=_('Select Scope of Checks'))
            ui.Label(window.frame,
                    text=_('What kinds of checks to you want to run?')
                    ).grid(column=0, row=0)
            cvts=[[i] for i in program['params'].cvts()]
            cvts.remove(['T'])
            cvtsdone=cvts[:]
            # log.info("{};{}".format(len(cvts),cvts))
            for j in cvts[:2]+[[i[0] for i in cvts[:2]]]:
                cvtsdone+=[j+i for i in cvts
                            if i[0] not in j
                            if set(j+i) not in [set(i) for i in cvtsdone]]
                # log.info("{};{}".format(len(cvtsdone),cvtsdone))
            cvtsdone+=[[i[0] for i in cvts]]
            options=[{'code':opt,
                    'name':unlist([program['params'].cvtdict()[i]['pl'] for i in opt])
                    }
                    for opt in cvtsdone
                    ]
            for opt in options:
                if len(opt['code']) == 1:
                    opt['name']+=' '+_("(only)")
            buttonFrame1=ui.ScrollingButtonFrame(window.frame,
                                    optionlist=options,
                                    command=program['settings'].setmulticheckscope,
                                    window=window,
                                    column=0, row=1
                                                )
    def cvtstodoprose(self,cvtstodo=None):
        if not cvtstodo:
            cvtstodo=self.cvtstodo
        output=[]
        for cvt in self.cvtstodo:
            output+=[program['params'].cvtdict()[cvt]['pl']]
        return output
    def secondfieldnames(self):
        if program['settings'].nominalps not in program['settings'].secondformfield:
            self.getsecondformfieldN()
        if program['settings'].verbalps not in program['settings'].secondformfield:
            self.getsecondformfieldV()
        return (program['settings'].secondformfield[program['settings'].verbalps],
                program['settings'].secondformfield[program['settings'].nominalps])
    def getbuttoncolumns(self,event=None):
        log.info("Asking for number of button columns...")
        window=ui.Window(self,title=_('Select Button Columns'))
        ui.Label(window.frame, text=_('How many columns do you want to use for '
                                        'the sort buttons?')
                                        ).grid(column=0, row=0)
        optionslist = list(range(1,4))
        buttonFrame1=ui.ButtonFrame(window.frame,
                                optionlist=optionslist,
                                command=program['settings'].setbuttoncolumns,
                                window=window,
                                column=0, row=1
                                )
        window.wait_window(window)
    def getmaxpss(self,event=None):
        title=_('Select Maximum Number of Lexical Categories')
        window=ui.Window(self, title=title)
        text=_('How many lexical categories to report (2 = Noun and Verb) ?')
        ui.Label(window.frame, text=text, column=0, row=0)
        r=[x for x in range(1,10)]
        buttonFrame1=ui.ScrollingButtonFrame(window.frame,
                                optionlist=r,
                                command=program['settings'].setmaxpss,
                                window=window,
                                column=0, row=1
                                )
        buttonFrame1.wait_window(window)
    def getmaxprofiles(self,event=None):
        title=_('Select Maximum Number of Syllable Profiles')
        window=ui.Window(self, title=title)
        text=_('How many syllable profiles to report?')
        ui.Label(window.frame, text=text, column=0, row=0)
        r=[x for x in range(1,10)]
        buttonFrame1=ui.ScrollingButtonFrame(window.frame,
                                optionlist=r,
                                command=program['settings'].setmaxprofiles,
                                window=window,
                                column=0, row=1
                                )
        buttonFrame1.wait_window(window)
    def getcheck(self,guess=False,event=None,**kwargs):
        log.info("this sets the check")
        # fn=inspect.currentframe().f_code.co_name
        log.info("Getting the check name...")
        checks=program['status'].checks(**kwargs)
        window=ui.Window(self,title='Select Check')
        if not checks:
            if program['params'].cvt() == 'T':
                btext=_("Define a New Tone Frame")
                text=_("You don't seem to have any tone frames set up.\n"
                "Click '{}' below to define a tone frame. \nPlease "
                "pay attention to the instructions, and if \nthere's anything "
                "you don't understand, or if you're not \nsure what a tone "
                "frame is, please ask for help. \nWhen you are done making "
                "frames, click ‘Exit’ to continue.".format(btext))
                cmd=self.task.addframe
            else:
                btext=_("Return to {}, to fix settings").format(program['name'])
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
            program['status'].makecheckok(tosort=tosort,wsorted=wsorted)
        else:
            log.info("Checks: {}".format(checks))
            if program['params'].cvt() == 'T':
                checklist=checks
            else:
                checklist=[(c,program['params'].cvcheckname(c)) for c in checks]
            text=_('What check do you want to do?')
            ui.Label(window.frame, text=text).grid(column=0, row=0)
            buttonFrame1=ui.ScrollingButtonFrame(window.frame,
                                    optionlist=checklist,
                                    command=program['settings'].setcheck,
                                    window=window,
                                    column=0, row=4
                                    )
            count=len(buttonFrame1.bf.winfo_children())
            if program['taskchooser'] is self:
                task=self.mainwindowis
            else:
                task=self
            if program['params'].cvt() == 'T':
                newb=ui.Button(buttonFrame1.bf,
                            text=_("New Frame"),
                            cmd=lambda w=window: task.addframe(window=w),
                            row=count+1)
            buttonFrame1.wait_window(window)
        """Make sure we got a value"""
        if program['params'].check() not in checks:
            return 1
    def _getgroup(self,window,event=None, **kwargs):
        # fn=inspect.currentframe().f_code.co_name
        """Window is called in getgroup"""
        log.info("_getgroup kwargs: {}".format(kwargs))
        ps=kwargs.get('ps',program['slices'].ps())
        cvt=kwargs.get('cvt',program['params'].cvt())
        profile=kwargs.get('profile',program['slices'].profile())
        check=kwargs.get('check',program['params'].check())
        if (cvt == 'T' and None in [cvt, ps, profile, check]):
            ErrorNotice(parent=window.frame,
                          text=_("You need to set "
                          "\nCheck type (as Tone, currently {}) "
                          "\nGrammatical category (currently {})"
                          "\nSyllable Profile (currently {}), and "
                          "\nTone Frame (currently {})"
                          "\nBefore choosing a sort group!"
                          "").format(program['params'].cvtdict()[cvt]['sg'], ps,
                          profile, check), column=0, row=0)
            return 1
        kwargs=grouptype(**kwargs) #this just fills in False
        groups=program['status'].groups(cvt=cvt,**kwargs)
        if not groups:
            ErrorNotice(parent=window.frame,
                          text=_("It looks like you don't have {}-{} lexemes "
                          "grouped in the ‘{}’ check yet \n({})."
                          "").format(ps,profile,check,kwargs, column=0, row=0))
            return
        if kwargs.get('intfirst') and kwargs.get('guess'):
            l=[int(i) for i in program['status'].groups(cvt=cvt,**kwargs)
                                    if str(i).isdigit()]
            if l:
                program['settings'].setgroup(str(min(l)),window)
            else:
                program['status'].nextgroup(cvt=cvt,**kwargs)
                window.destroy()
            return
        elif kwargs.get('guess') or (len(groups) == 1
                                        and not kwargs.get('comparison')):
            program['status'].nextgroup(cvt=cvt,**kwargs)
            window.destroy()
            return
        if kwargs.get('comparison'):
            g2=groups[:]
            g2.remove(program['status'].group()) #group() is not cvt aware
            if not g2:
                window.destroy()
                ErrorNotice(text=_("There don't seem to be any groups "
                            "to compare with!"))
                return
            if len(g2) == 1:
                program['settings'].setgroup_comparison(g2[0],window)
                return
            buttonFrame1=ui.ScrollingButtonFrame(window.frame,
                            optionlist=g2,
                            command=program['settings'].setgroup_comparison,
                            window=window,
                            column=0, row=4
                            )
        else:
            ui.Label(window.frame,
                      text=_("What {} do you want to work with?").format(
                                      program['params'].cvtdict()[cvt]['sg']),
                      column=0, row=0)
            # window.scroll=ui.ScrollingFrame(window.frame)
            # window.scroll.grid(column=0, row=1)
            # groups+=[(None,'All')] #put this first, some day (now confuses ui)
            # log.info("Groups: {}".format(groups))
            buttonFrame1=ui.ScrollingButtonFrame(window.frame,
                                     optionlist=groups+[(None,'All')],
                                     command=program['settings'].setgroup,
                                     window=window,
                                     column=0, row=4
                                     )
        log.info("Done making buttonframe")
    def getgroup(self,event=None,**kwargs): #guess=False,
        """I need to think though how to get this to wait appropriately
        both for single C/V selection, and for CxV selection"""
        log.info("this sets the group")
        kwargs=grouptype(**kwargs) #if any should be True, set in wrappers above
        log.info("getgroup kwargs: {}".format(kwargs))
        program['settings'].refreshattributechanges()
        cvt=kwargs.get('cvt',program['params'].cvt())
        if cvt == "V":
            w=ui.Window(self,title=_('Select Vowel'))
            self._getgroup(window=w,**kwargs)
            # w.wait_window(window=w)
        elif cvt == "C":
            w=ui.Window(self,title=_('Select Consonant'))
            self._getgroup(w,**kwargs)
            # self.frame.wait_window(window=w)
        elif cvt == "CV":
            w=ui.Window(self,title=_('Select Consonant/Vowel'))
            CV=''
            for kwargs['cvt'] in ['C','V']:
                self._getgroup(**kwargs)
                CV+=program['status'].group()
            program['status'].group(CV)
            # cvt = "CV"
        elif cvt == "T":
            w=ui.Window(self,title=_('Select Framed Tone Group'))
            self._getgroup(window=w,**kwargs) #guess=guess,
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
        window=ui.Window(self, title=title)
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
                            command=program['settings'].setexamplespergrouptorecord,
                            window=window,
                            column=0, row=4
                                )
        buttonFrame1.wait_window(window)
    def runwindowcleanup(self):
        log.info("Shutting down runwindow")
        if self.exitFlag.istrue() and program['taskchooser'].towrite:
            log.info("Final write to lift")
            self.maybewrite(definitely=True)
        else:
            log.info("No final write to lift")
        ui.Window.cleanup(self) #Exitable
    def getrunwindow(self,nowait=False,msg=None,title=None):
        """Can't test for widget/window if the attribute hasn't been assigned,"
        but the attribute is still there after window has been killed, so we
        need to test for both."""
        def releasefullscreen(event):
            self.runwindow.attributes('-fullscreen', False)
        if title is None:
            title=(_("Run Window"))
        if self.exitFlag.istrue():
            return
        if hasattr(self,'runwindow') and self.runwindow.winfo_exists():
            log.info("Runwindow already there! Resetting frame...")
            self.runwindow.resetframe() #I think I'll always want this here...
        else:
            self.runwindow=ui.Window(self,title=title)
        self.runwindow.title(title)
        self.runwindow.attributes('-fullscreen', True)
        self.runwindow.bind('<Escape>', releasefullscreen)
        self.runwindow.bind('<Double-Button-1>', releasefullscreen)
        self.runwindow.lift()
        self.runwindow.cleanup=self.runwindowcleanup
        if not nowait:
            self.runwindow.wait(msg=msg)
    """Functions that everyone needs"""
    def updateazt(self,event=None):
        updateazt()
    def verifictioncode(self,**kwargs):
        check=kwargs.get('check',program['params'].check())
        group=kwargs.get('group',program['status'].group())
        # log.info("about to return {}={}".format(check,group))
        return check+'='+group
    def maybewrite(self,definitely=False):
        program['taskchooser'].maybewrite(definitely=definitely)
    def killall(self):
        log.info("Shutting down Task")
        try:
            towrite=program['taskchooser'].towrite
        except AttributeError:
            towrite=self.towrite #if taskchooser; shouldn't happen, but in case.
        self.wait(msg=_("Closing down {} and storing changes").format(
                                                                program['name']
                                                                ))
        if towrite:
            log.info("Final write to lift")
            self.maybewrite(definitely=True)
        else:
            log.info("No final write to lift")
        program['settings'].trackuntrackedfiles()
        self.waitdone() #Don't confuse user; there's more input to come, maybe
        for r in program['settings'].repo:
            program['settings'].repo[r].share()
            log.info("Done maybe committing/pushing to {}".format(r))
        log.info("Saving settings for next time")
        program['settings'].storesettingsfile() #in case we added repos
        log.info("Settings saved")
        log.info("Killing window")
        ui.Window.killall(self) #Exitable
        log.info("Window killed")
    def __init__(self,parent):
        log.info("Initializing TaskDressing")
        self.parent=parent
        self.menu=False #initialize once
        if isinstance(self,TaskChooser):
            taskchooser=self
        else:
            self.task=self
            taskchooser=self.parent
            program['status'].task(self)
        """Whenever this runs, it's the main window."""
        taskchooser.mainwindowis=self
        """At some point, I need to think through which attributes are needed,
        and if I can get them all into objects, read/writeable with files."""
        """These are raw attributes from file"""
        """these are objects made by the task chooser"""
        self.inherittaskattrs()
        if hasattr(self,'task') and isinstance(self.task,Multicheck):
            if hasattr(program['settings'],'cvtstodo'):
                self.cvtstodo=program['settings'].cvtstodo
            else:
                self.cvtstodo=['V']
        self.analang=program['params'].analang() # Every task gets this here
        # super(TaskDressing, self).__init__(parent)
        for k in ['settings',
                    # 'menu',
                    'mainrelief','fontthemesmall',
                    'showdetails']:
            if not hasattr(self,k):
                    setattr(self,k,False)
        self.makecvtok() #this just enforces a good cvt value
        # Make the actual window
        ui.Window.__init__(self,parent)
        self.mainwindow=True
        self.withdraw() #made visible by chooser when complete
        self.maketitle()
        ui.ContextMenu(self)
        self.tableiteration=0
        self.makestatusframe()
        self._taskchooserbutton()
        self.correlatemenus()
        # back=ui.Button(self.outsideframe,text=_("Tasks"),cmd=program['taskchooser'])
        # self.setfontsdefault()
class TaskChooser(TaskDressing,ui.Window):
    """This class stores the hierarchy of tasks to do in A-Z+T, plus the
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
                'image':program['theme'].photo['iconReportLogo'],
                'sticky':'ew'
                }
    def choosereports(self):
        self.frame.status.bigbutton.destroy()
        self.showreports=True
        self.setmainwindow(self)
        self.gettask()
    def makeexampledict(self):
        program['examples']=ExampleDict()
    def guidtriage(self):
        # import time
        log.info("Doing guid triage and other variables —this takes awhile...")
        start_time=nowruntime()
        self.guids=program['db'].guids
        self.guidsinvalid=[] #nothing, for now...
        self.senseids=program['db'].senseids
        self.senseidsinvalid=[] #nothing, for now...
        print(len(self.guidsinvalid),'entries with invalid data found.')
        program['db'].guidsinvalid=self.guidsinvalid
        self.guidsvalid=[]
        for guid in self.guids:
            if guid not in self.guidsinvalid:
                self.guidsvalid+=[guid]
        print(len(self.guidsvalid),'entries with valid data remaining.')
        self.guidswanyps=program['db'].get('guidwanyps') #any ps value works here.
        print(len(self.guidswanyps),'entries with ps data found.')
        self.guidsvalidwops=[]
        self.guidsvalidwps=[]
        for guid in self.guidsvalid:
            if guid in self.guidswanyps:
                self.guidsvalidwps+=[guid]
            else:
                self.guidsvalidwops+=[guid]
        program['db'].guidsvalidwps=self.guidsvalidwps #This is what we'll search
        print(len(self.guidsvalidwops),'entries with valid data but no ps data.')
        print(len(self.guidsvalidwps),'entries with valid data and ps data.')
        # for var in [self.guids, self.guidswanyps, self.guidsvalidwops, self.guidsvalidwps, self.guidsinvalid, self.guidsvalid]:
        #     print(len(var),str(var))
        # for guid in self.guidswanyps:
        #     if guid not in self.formstosearch[self.analangs[0]][None]:
        #         guids+=[guid]
        # print(len(guids),guids)
        logfinished(start_time)
    def guidtriagebyps(self):
        log.info("Doing guid triage by ps... This also takes awhile?...")
        self.guidsvalidbyps={}
        """use program['db'].entriesbyps or program['db'].sensesbyps"""
        for ps in program['db'].pss:
            self.guidsvalidbyps[ps]=program['db'].get('guidbyps',ps=ps)
    def gettask(self,event=None):
        """This function allows the user to select from any of tasks whose
        prerequisites are minimally satisfied."""
        # if self.reports:
        self.withdraw()
        try:
                self.frame.status.bigbutton.destroy()
        except AttributeError:
            log.info("There doesn't seem to be a big button")
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
        elif optionlist_maxi > 9:
            bpr=4
        columnspan=1
        for n,o in enumerate(optionlist):
            if n is optionlist_maxi and int(n/bpr):
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
        self.deiconify()
    def makedefaulttask(self):
        """This function makes the task after the highest optimally
        satisfied task"""
        """The above is prerequisite to the below, so it is here. It could be
        elsewhere, but that led to numerous repetitions."""
        optionlist=self.makeoptions()
        # task,title,icon
        log.info("starting from option list {}".format(optionlist))
        optionlist=[i for i in optionlist if not issubclass(i[0],Sound)]
        # log.info("getting default from option list {}".format(
        #                                             [i[1] for i in optionlist]))
        if program['testing'] and 'testtask' in program:
            self.maketask(program['testtask'])
        else:
            self.maketask(optionlist[-1][0]) #last item, the code
    def maketask(self,taskclass): #,filename=None
        self.unsetmainwindow()
        try:
            if self.task.waiting():
                self.task.waitdone()
            self.task.on_quit() #destroy and set flag
        except AttributeError:
            log.info(_("No task, apparently; not destroying."))
        self.task=taskclass(self) #filename
        if not self.task.exitFlag.istrue():# and not isinstance(self.task,Parse):
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
    def makeoptions(self):
        """This function (and probably a few dependent functions, maybe
        another class) provides a list of functions with prerequisites
        that are minimally and/or optimally satisfied."""
        """So far that distinction isn't being made. For instance, we should
        not offer recordingT as default if all examples have sound files, yet
        a user may well want to go back and look at those recordings, and maybe
        rerecord some."""
        self.whatsdone()
        if self.showreports:
            tasks=[
                    ReportCitationBackground,
                    ReportCitationMulticheckBackground,
                    ReportCitationMultichecksliceBackground
                    ]
            if self.doneenough['collectionlc']:
                """This currently takes way too much time. Until it gets
                mutithreaded, it will not be an option"""
            if self.doneenough['sortT']:
                tasks.append(ReportCitationTBackground)
                tasks.append(ReportCitationTLBackground)
                tasks.append(ReportCitationMultisliceTBackground)
                tasks.append(ReportCitationMultisliceTLBackground)
            if self.doneenough['analysis']:
                tasks.append(ReportCitationByUFBackground)
                tasks.append(ReportCitationByUFMulticheckBackground)
                tasks.append(ReportCitationByUFMultichecksliceBackground)
        elif self.datacollection:
            tasks=[
                    WordCollectionCitation,
                    WordCollectionPlural,
                    WordCollectionImperative,
                    WordCollectnParse
                    # WordCollectionLexeme
                    ]
            if self.doneenough['collectionlc']:
                tasks.append(RecordCitation)
                """Do these next"""
                tasks.append(SortV)
                tasks.append(SortC)
                tasks.append(SortT)
                if self.doneenough['sortT']:
                    tasks.append(RecordCitationT)
            # if self.donew['parsedlx']:
            #     tasks.append(SortRoots)
        else: #i.e., analysis tasks
            tasks=[]
            if self.doneenough['sort']:
                tasks.append(TranscribeV)
                tasks.append(TranscribeC)
            #this maybe should depend on recordedT:
            if self.doneenough['sortT']:
                tasks.append(TranscribeT)
            if self.doneenough['analysis']:
                tasks.append(JoinUFgroups)
            if me:
                tasks.append(ParseWords)
                # tasks.append(ParseWords)
                # tasks.append(ParseSlice)
                # tasks.append(ParseSliceWords)
                tasks.append(ReportConsultantCheck)
        if (program['testing'] and 'testtask' in program and
                program['testtask'] not in tasks):
            if self.showreports == isinstance(program['testtask'],Report):
                tasks.append(program['testtask'])
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
        log.info("Tasks available ({}): {}".format(len(tasktuples),
                    [i[1] for i in tasktuples]))
        return tasktuples
        # [(Check,"Citation Form Sorting in Tone Frames"),
        #         (WordCollection,"Placeholder for future checks"),
        #         (Placeholder,"Placeholder for future checks")
        #         ]bum
    def convertlxtolc(self,window):
        window.destroy()
        backup=self.filename+"_backupBeforeLx2LcConversion"
        program['db'].write(backup)
        program['db'].convertlxtolc()
        # program['db'].write(self.file.name+str(now()))
        program['db'].write()
        conversionlogfile=logsetup.writelzma()
        ErrorNotice(_("The conversion is done now, so {0} will quit. You may "
                    "want to inspect your current file ({1}) and the backup "
                    "({2}) to confirm this did what you wanted, before "
                    "opening {0} again. In case there are any issues, the "
                    "log file is also saved in {3}").format(program['name'],
                                                self.filename,
                                                backup,
                                                conversionlogfile),
                    title=_("Conversion Done!"),
                    wait=True)
        self.restart()
    def asktoconvertlxtolc(self):
        title=_("Convert lexeme field data to citation form fields?")
        url="{}/CITATIONFORMS.md".format(program['docsurl'])
        w=ui.Window(self,title=title,exit=False)
        lexemesdone=list(program['db'].nentrieswlexemedata.values())#[program['settings'].analang]
        citationsdone=list(program['db'].nentrieswcitationdata.values())#[program['settings'].analang]
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
        cawls=program['db'].get('cawlfield/form/text').get('text')
        # log.info("CAWL ({}): {}".format(len(cawls),cawls))
        self.cawlmissing=[]
        for i in range(1700):
            if "{:04}".format(i+1) not in cawls:
                self.cawlmissing.append(i+1)
        if len(self.cawlmissing) < 10:
            log.info("CAWL missing ({}): {}".format(len(self.cawlmissing),
                                                        self.cawlmissing))
    def whatsdone(self):
        """I should probably have a roundtable with people to discuss these
        numbers, to see that we agree the decision points are rational."""
        #This should probably not be redone entirely each time a task is done
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
        nentries=program['db'].nguids
        lexemesdone=program['db'].nentrieswlexemedata
        citationsdone=program['db'].nentrieswcitationdata
        log.info("lexemesdone by lang: {}".format(lexemesdone))
        log.info("citationsdone by lang: {}".format(citationsdone))
        #There should never be more lexemes than citation forms.
        # for l in lexemesdone:
        #     if l not in citationsdone or citationsdone[l] < lexemesdone[l]:
        #         w=self.asktoconvertlxtolc()
        #         w.wait_window(w) # wait for this answer before moving on
        #         break #just ask this once
        self.getcawlmissing()
        log.info("nfields in db: {}".format(program['db'].nfields))
        log.info("wannotations in db: {}".format(program['db'].nfieldswannotations))
        sorts={k:v for (k,v) in program['db'].nfields.items()
                                            if 'sense/example' in v}
        sorts.update({k:v for (k,v) in program['db'].nfieldswannotations.items()
                                            if 'sense/example' not in v})
        # log.info("nfields by lang (updated): {}".format(sorts))
        sortsrecorded=program['db'].nfieldswsoundfiles
        log.info("nfieldswsoundfiles by lang: {}".format(sortsrecorded))
        sortsnotrecorded={}
        if me:
            enough=0
        else:
            enough=25
        # log.info("looking at sorts now: {}".format(sorts))
        for l in sorts:
            maybeals=[i for i in program['db'].audiolangs if l in i]
            if maybeals:
                al=maybeals[0]
                log.info("Using audiolang {} for analang {}"
                            "".format(al,l))
            else:
                log.info("Couldn't find plausible audiolang (among {}) "
                        "for analang {}".format(program['db'].audiolangs,l))
            if al not in sortsrecorded:
                sortsrecorded[al]={}
            sortsnotrecorded[l]={}
            for f in sorts[l]:
                """I don't think I can faithfully distinguish between
                sorting on lc v other fields here, at least not yet"""
                if f == 'sense/example':
                    #sorting is never done; mark when the top slices are done?
                    if sorts[l][f] >= enough: #what is a reasonable number here?
                        self.doneenough['sortT']=True
                else:
                    if sorts[l][f] >= enough: #what is a reasonable number here?
                        self.doneenough['sort']=True
                #This is a bit of a hack, but no analang nor audiolang yet.
                if f not in sortsrecorded[al]:
                    sortsrecorded[al]={f:0}
                sortsnotrecorded[l][f]=sorts[l][f]-sortsrecorded[al][f]
                if f == 'sense/example':
                    if not sortsnotrecorded[l][f]:
                        self.donew['recordedT']=True
                    if sortsrecorded[al][f] >= enough:
                        self.doneenough['recordedT']=True
                    # Needed? Any time sorting is done, show recording
                    # if not sortsrecorded[f][al]:
                    #     self.donew['torecordT']=True
                    if sortsnotrecorded[l][f] < enough:
                        self.doneenough['torecordT']=True
                else:
                    if not sortsnotrecorded[l][f]:
                        self.donew['recorded']=True
                    if sortsrecorded[al][f] >= enough:
                        self.doneenough['recorded']=True
                    #see above
                    if sortsnotrecorded[l][f] < enough:
                        self.doneenough['torecord']=True
                # log.info("Finished looking at [{}]{} field: {}".format(l,f,self.doneenough))
        # log.info("nfieldswosoundfiles by lang: {}".format(sortsnotrecorded))
        for lang in program['db'].nentrieswlexemedata:
            remaining=program['db'].nentrieswcitationdata[lang
                                        ]-program['db'].nentrieswlexemedata[lang]
            if not remaining:
                self.donew['parsedlx']=True
            if remaining < 100:
                self.doneenough['parsedlx']=True
                break
        for lang in citationsdone:
            if nentries-citationsdone[lang] < 50 and not len(self.cawlmissing):
                self.donew['collectionlc']=True
            if citationsdone[lang] > 200: #was 705
                self.doneenough['collectionlc']=True#I need to think through this
            # log.info("checking '{}'".format(f))
        for f in [i for j in program['db'].sensefieldnames.values() for i in j]:
            if 'verification' in f:
                # log.info("Found ‘verification’ in ‘{}’".format(f))
                #I need to tweak this, it should follow tone (only) reports:
                #maybe read this from status?
                #This ideally follows transcription
                #This should maybe be relevant by slice (analyzed or not yet)
                self.doneenough['analysis']=True
                break
            # log.info("‘verification’ not in ‘{}’".format(f))
        log.info("Analysis of what you're done with: {}".format(self.donew))
        log.info("You're done enough with: {}".format(self.doneenough))
    def restart(self,filename=None):
        log.info("Restarting from TaskChooser")
        file.writefilename(self.filename)
        if hasattr(self,'warning') and self.warning.winfo_exists():
            self.warning.destroy()
        # log.info("towrite: {}; writing: {}".format(self.towrite,self.writing))
        if self.towrite: #Do even if not closed by user
            log.info("Final write to lift")
            self.maybewrite(definitely=True)
        try:
            self.task.withdraw() #so users don't do stuff while waiting
        except (AttributeError,tkinter.TclError):
            log.info("There doesn't seem to be a task to hide; moving on.")
        try:
            self.task.runwindow.withdraw() #so users don't do stuff while waiting
        except (AttributeError,tkinter.TclError):
            log.info("There doesn't seem to be a runwindow to hide; moving on.")
        while self.writing:
            # log.info("towrite: {}; writing: {}; taskwrite: {}".format(
            #     self.towrite,self.writing,program['taskchooser'].writing))
            log.info("Waiting to finish writing to lift")
            time.sleep(1)
            self.check_if_write_done() #because after() isn't working here...
        # log.info("Not writing to lift")
        sysrestart()
    def changedatabase(self):
        log.debug("Preparing to change database name.")
        try:
            self.task.withdraw() #so users don't do stuff while waiting
        except (AttributeError,tkinter.TclError):
            log.info("There doesn't seem to be a task to hide; moving on.")
        curname = self.filename
        log.info(_("Current database: {}").format(curname))
        window=LiftChooser(self,file.getfilenames())
        window.wait_window(window)
        if hasattr(self,'name') and self.name:
            self.filename=self.name
        # text=_("{} will now exit; restart to work with the new database."
        #         "".format(program['name']))
        # ErrorNotice(text,title=_("Change Database"),wait=True)
        # program['root'].destroy()
        # subprocess.call?
        # __name__
        # main()
        log.info(_("Current database: {}").format(self.filename))
        if self.filename and curname != self.filename:
            log.info(_("User selected a new database; restarting with it."))
            self.restart()
        else:
            log.info(_("User didn't select a new database; continuing."))
            self.task.deiconify()
        # self.restart(self.filename)
    def timetowrite(self):
        """only write to file every self.writeeverynwrites times you might."""
        self.writeable+=1 #and tally here each time this is asked
        return not self.writeable%program['settings'].writeeverynwrites
    def schedule_write_check(self):
        """Schedule `check_if_write_done()` function after five seconds."""
        log.info("Scheduling check")
        program['root'].after(2000, self.check_if_write_done)
        # log.info("Scheduled check")
        # program['taskchooser'].after(5000, self.check_if_write_done, t)
    def check_if_write_done(self):
        # If the thread has finished, allow another write.
        log.info("Checking if writing done to lift.")
        try:
            done=not self.writethread.is_alive()
        except AttributeError:
            done=True
        except Exception as e:
            log.info("Exception: {}".format(e))
            log.info("writethread: {}".format(hasattr(self,'writethread')))
        if done:
            log.info("Done writing to lift.")
            self.writing=False
        else:
            # Otherwise check again later.
            log.info("schedule_write_check writing to lift.")
            self.schedule_write_check()
    def maybewrite(self,definitely=False):
        write=self.timetowrite() #just call this once!
        if (write and not self.writing) or definitely:
            self.towrite=False
            self.writethread = threading.Thread(target=program['db'].write)
            self.writing=True
            log.info("Writing to lift...")
            self.writethread.start()
            self.schedule_write_check()
        elif write:
            log.info("Already writing to lift; I trust this new mod will "
                    "get picked up later...")
            self.towrite=True
    def usbcheck(self):
        self.splash.withdraw()
        for r in program['settings'].repo.values():
            # log.info("checking repo {} for USB drive".format(r))
            r.share()
        self.splash.draw()
    def __init__(self,parent):
        program['taskchooser']=self
        self.towrite=False
        self.writing=False
        self.datacollection=True # everyone starts here?
        self.showreports=False
        self.showingreports=False
        self.interfacelangs=getinterfacelangs()
        self.filename=FileChooser().name
        self.splash = Splash(self)
        self.splash.draw()
        self.splash.progress(25)
        FileParser(self.filename)
        self.splash.progress(55)
        self.setmainwindow(self)
        Settings(self)
        self.splash.progress(65)
        self.whatsdone()
        self.splash.progress(80)
        TaskDressing.__init__(self,parent) #I think this should be after settings
        program['settings'].getprofiles()
        # self.withdraw()
        self.splash.progress(90)
        self.setmainwindow(self)
        if program['root'].exitFlag.istrue():
            return
        # self.guidtriage() #sets: self.guidswanyps self.guidswops self.guidsinvalid self.guidsvalid
        # self.guidtriagebyps() #sets self.guidsvalidbyps (dictionary keyed on ps)
        """Can whatsdone be joined with makedefaulttask? they appear together
        elsewhere."""
        self.splash.maketexts() #update for translation change
        if not program['settings'].writeeverynwrites: #0/None are not sensible values
            program['settings'].writeeverynwrites=1
            program['settings'].storesettingsfile()
        self.usbcheck()
        self.writeable=0 #start the count
        if program['nosound']:
            e=_("You don't have the sound module installed. For best use of {},"
                "you should switch back to the main branch, connect to the "
                "internet, and restart. In the mean time. You won't be able "
                "to record or play audio!"
                ).format(program['name'])
            ErrorNotice(e)
        self.splash.progress(100)
        self.splash.destroy()
        self.makeexampledict() #needed for makestatus, needs params,slices,data
        self.maxprofiles=5 # how many profiles to check before moving on to another ps
        self.maxpss=2 #don't automatically give more than two grammatical categories
        self.makedefaulttask() #normal default
        # self.gettask() # let the user pick
        """Do I want this? Rather give errors..."""
class Segments(object):
    """docstring for Segments."""
    def buildregex(self,**kwargs):
        """include profile (of those available for ps and check),
        and subcheck (e.g., a: CaC\2)."""
        """Provides self.regexCV and self.regex"""
        cvt=kwargs.get('cvt',program['params'].cvt())
        # ps=kwargs.get('ps',program['slices'].ps())
        profile=kwargs.get('profile',program['slices'].profile())
        check=kwargs.get('check',program['params'].check())
        group=kwargs.get('group',program['status'].group())
        maxcount=rx.countxiny(cvt, profile)
        if profile is None:
            print("It doesn't look like you've picked a syllable profile yet.")
            return
        """Don't need this; only doing count=1 at a time. Let's start with
        the easier ones, with the first occurrance changed."""
        self.regexCV=str(profile) #Let's set this before changing it.
        # log.info("self.regexCV: {}".format(self.regexCV))
        """One pass for all regexes, S3, then S2, then S1, as needed."""
        # log.info("maxcount: {}".format(maxcount))
        # log.info("check: {}".format(check))
        # log.info("group: {}".format(group))
        # log.info("self.groupcomparison: {}".format(self.groupcomparison))
        S=str(cvt) #should this ever be cvt? Do I ever want CV1xCV2,CV1=CV2?
        regexS='.*?'+S #This will be a problem if S=NC or CG...
        # log.info("regexS: {}".format(regexS))
        if 'x' in check and cvt in ['V','C']:
            replScomp='\\1'+self.groupcomparison
            replS='\\1'+group
            compared=False
            # log.info("Making regex for {} check with group {} and "
            # "comparison {} ({})".format(check,group,self.groupcomparison,replS))
        elif 'x' in check:
            replS='\\1'+group+self.groupcomparison
            compared=True #well, don't do two runs, in any case.
        else:
            # log.info("Not comparing: {}".format(check))
            replS='\\1'+group
            # log.info("Making regex for {} check with group {} ({})"
            #         "".format(check,group,replS))
        for occurrence in reversed(range(maxcount)):
            occurrence+=1
            # log.info("S+str(occurrence): {}".format(S+str(occurrence)))
            # log.info("Check (less x): {}".format(check.replace('x','')))
            if S+str(occurrence) in check.replace('x',''):
                """Get the (n=occurrence) S, regardless of intervening
                non S..."""
                # log.info("regexS: {}".format(regexS))
                # regS='^('+regexS*(occurrence-1)+'[^'+S+']*)('+S+')'
                regS='^('+regexS*(occurrence-1)+'.*?)('+S+')'
                # log.info("regS: {}".format(regS))
                # log.info("regexS: {}".format(regexS))
                # log.info("regS: {}".format(regS))
                # log.info("replS: {}".format(replS))
                # log.info("self.regexCV: {}".format(self.regexCV))
                if 'x' in check and not compared:
                    self.regexCV=rx.sub(regS,replScomp,self.regexCV, count=1)
                    compared=True
                else:
                    self.regexCV=rx.sub(regS,replS,self.regexCV, count=1)
                # log.info("self.regexCV: {}".format(self.regexCV))
        #     else:
        #         log.info("{} not found in {}".format(S+str(occurrence),
        #                                             check.replace('x','')))
        # log.info("self.regexCV (buildregex): {}".format(self.regexCV))
        """Final step: convert the CVx code to regex, and store in self."""
        self.regex=rx.fromCV(self.regexCV, program['settings'].s[self.analang],
                            program['settings'].distinguish,
                            word=True, compile=True)
    def ifregexadd(self,regex,form,id):
        # This fn is just to make this threadable
        if regex.search(form):
            self.output+=id
    def formspsprofile(self,**kwargs):
        log.info("Asked for forms to search for a data slice (only do once!)")
        ps=kwargs.get('ps',program['slices'].ps())
        d=program['settings'].formstosearch[ps]
        # log.info("Looking at {} entries".format(len(d)))
        return {k:d[k] for k in d
                        if set(d[k]) & set(program['slices'].senseids(**kwargs))}
    def senseidformsbyregex(self,regex,**kwargs):
        """This function takes in a compiled regex,
        and outputs a list/dictionary of senseid/{senseid:form} form."""
        ps=kwargs.get('ps',program['slices'].ps())
        self.output=[]
        # log.info("Kwargs keys: {} (formstosearch n={})".format(kwargs.keys(),
        #                                 len(kwargs['formstosearch'])))
        dicttosearch=kwargs.get('formstosearch')
        if not dicttosearch:
            dicttosearch=self.formspsprofile(**kwargs)
        # log.info("Reduced to {} entries".format(len(dicttosearch)))
        # log.info("Looking for senses by regex {}".format(regex))
        self.output=[
                    j for k,v in dicttosearch.items()
                    if k and regex.search(k)
                    for j in v
                    ]
        # for form,id in [i for i in dicttosearch.items() if i[0]]:
        #     # log.info("Looking for form {}, with id {}".format(form,id))
        #     t = threading.Thread(target=self.ifregexadd,
        #                         args=(regex,form,id))
        #     t.start()
        # try:
        #     t.join()
        # except:
        #     log.info("Looks like no forms in senseidstocheck: {}".format(
        #                                                 dicttosearch))
        # log.info("Found senses: {}".format(self.output))
        return self.output
    def presortgroups(self,**kwargs):
        if program['status'].presorted(**kwargs):
            log.info(_("Presorting for this check/slice already done! ({})"
                        "").format(kwargs))
            return
        log.info(_("Presorting"))
        cvt=kwargs.get('cvt',program['params'].cvt())
        ps=kwargs.get('ps',program['slices'].ps())
        profile=kwargs.get('profile',program['slices'].profile())
        check=kwargs.get('check',program['params'].check())
        senseids=[]
        groups=program['status'].groups(wsorted=True,**kwargs)
        groups=program['status'].groups(cvt=cvt)
        #multiprocess from here?
        msg=_("Presorting ({}={})").format(check,groups)
        log.info(msg)
        w=self.getrunwindow(msg=msg)
        # test this before implementing it:
        # kwargs['formstosearch']=self.formsthisprofile(**kwargs)
        for group in [i for i in groups if isnoninteger(i)]:
            self.buildregex(group=group,cvt=cvt,profile=profile,check=check)
            # log.info("self.regex: {}; self.regexCV: {}".format(self.regex,
            #                                             self.regexCV))
            s=set(self.senseidformsbyregex(self.regex,ps=ps))
            if s: #senseids just for this group
                self.presort(list(s),check,group)
        program['status'].presorted(True)
        program['status'].store() #after all the above
        self.runwindow.waitdone()
    def presort(self,senseids,check,group):
        ftype=program['params'].ftype()
        for senseid in senseids:
            sense=program['db'].sensedict[senseid]
            t = threading.Thread(target=self.marksortgroup,
                            args=(sense,group),
                            kwargs={'check':check,
                                    'ftype':ftype,
                                    # 'framed':framed,
                                    'nocheck':False
                                    })
            t.start()
        t.join()
        self.updatestatus(group=group) # marks the group unverified.
    def updateformtextnodebycheck(self,t,check,value):
        """update this to read and write objects"""
        tori=t.text[:]
        matches=[]
        t=rx.update(t,program['settings'].rx,check,value)
        for c in reversed(check.split('=')):
            log.info("subbing {} for {} in {}, using {}".format(value,c,tori,
                                                    program['settings'].rx[c]))
            log.info("found {}".format(program['settings'].rx[c].search(t.text)))
            match=program['settings'].rx[c].search(t.text)
            if match:
                matches.append(match.groups()[-1])
                t.text=match.expand('\\g<1>'+value)+t.text[match.end():]
            # t.text=program['settings'].rx[c].sub('\\g<1>'+value,t.text)
        log.info("updated {} > {}".format(tori,t.text))
        #now that we've potentially added a grapheme, see that it will be found.
        program['settings'].addtoCVrxs(value)
        #this should update polygraphs; if so, trigger reanalysis (instead of above)
    def updateformtoannotations(self,sense,ftype,check=None,write=False):
        """This should take a sense and ftype (and maybe check, not sure)
        and update that form on the basis of the annotations made to date.
        This should be something that can be done for just one check, or all,
        and iterated across a few or many senseids.
        This might be best iterating across ftypes, to catch them all...
        that would likely need more smarts for affix and root distinction."""
        formvalue=sense.textvaluebyftypelang(self.analang)
        if not formvalue:
            log.info("updateformtoannotations didn't return a form value for "
                    "senseid={}, ftype={}, analang={}"
                    "".format(sense.id,ftype,self.analang))
            return
        # log.info("fnode: {}; text: {}".format(fnode,t.text))
        if check: #just update to this annotation
            value=sense.annotationvaluebyftypelang(self,ftype,self.analang,check)
            if value is not None:
                f=rx.update(formvalue,program['settings'].rx,check,value)
                sense.textvaluebyftypelang(self.analang,f)
                log.info("Done with updateformtextnodebycheck")
                #This should update formstosearch:
                if formvalue != f:
                    program['settings'].addtoformstosearch(senseid,f,formvalue)
                    log.info("Done with addtoformstosearch")
                if len(value)>1:
                    sc=program['params'].cvt()
                    program['settings'].polygraphs[self.analang][sc][value]=True
            else:
                write=False #in case it isn't already
        else: #update to all annotations
            annodict=sense.annotationvaluedictbyftypelang(ftype,self.analang)
            # log.info("annodict: {}".format(annodict))
            for check,value in annodict.items():
                f=rx.update(formvalue,program['settings'].rx,check,value)
                sense.textvaluebyftypelang(self.analang,f)
        program['taskchooser'].datadict.clearsense(senseid) #so this will refresh
        if write:
            self.maybewrite()
    def setsensegroup(self,sense,ftype,check,group,**kwargs):
        # log.info("Setting segment sort group")
        sense.annotationvaluebyftypelang(ftype,self.analang,check,group)
    def getsensesingroup(self,check,group):
        ftype=program['params'].ftype()
        lang=program['params'].analang()
        return [
                i for i in program['db'].senses
                if i.ftypes[ftype].annotationvaluebylang(lang,check) == group
                ]
        # fkwargs={
        #         ftype+'annotationname':check,
        #         ftype+'annotationvalue':group
        #         }
        # return program['db'].get("sense", **fkwargs).get('senseid')
    def getsensegroup(self,sense,check):
        ftype=program['params'].ftype()
        return sense.annotationvaluebyftypelang(ftype,self.analang,check)
                                                # ftype,lang,name,value
    def __init__(self, parent):
        self.dodone=True
        self.dodoneonly=False #don't give me other words
class WordCollection(Segments):
    """This task collects words, from the SIL CAWL, or one by one."""
    def taskicon(self):
        return program['theme'].photo['iconWord']
    def dobuttonkwargs(self):
        if program['taskchooser'].cawlmissing:
            fn=self.addCAWLentries
            text=_("Add remaining CAWL entries")
            tttext=_("This will add entries from the Comparative African "
                    "Wordlist (CAWL) which aren't already in your database "
                    "(you are missing {} CAWL tags). If the appropriate "
                    "glosses are found in your database, CAWL tags will be "
                    "merged with those entries."
                    "\nDepending on the number of entries, this may take "
                    "awhile.").format(len(program['taskchooser'].cawlmissing))
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
                'image':program['taskchooser'].theme.photo['Word'],
                'sticky':'ew',
                'tttext':tttext
                }
    def getlisttodo(self,**kwargs):
        """Whichever field is being asked for (self.nodetag), this fn returns
        which are left to do."""
        if hasattr(self,'byslice') and self.byslice:
            log.info("Limiting segment work to this slice")
            all=[program['db'].sensedict[i].entry for i in program['slices'].senseids()]
        else:
            all=program['db'].entries
        if self.dodone and not self.dodoneonly: #i.e., all data
            return all
        done=[i for i in all
                    if i.sense.textvaluebyftypelang(self.ftype,self.analang)]
        if self.dodone: #i.e., dodoneonly
            return done
        # At this point, done isn't wanted
        todo=[x for x in all if x not in done] #set-set may be better
        log.info("To do: ({}) First 5: {}".format(len(todo),todo[:5]))
        return todo
    def getinstructions(self):
        return _("Type the word in your language that goes with these meanings."
                "\nGive a single word (not a phrase) wherever possible."
                "\nJust type consonants and vowels; don't worry about tone "
                "for now.")
    def getwords(self):
        self.entries=self.getlisttodo()
        self.nentries=len(self.entries)
        self.index=0
        self.wordsframe=ui.Frame(self.frame,row=1,column=1,sticky='ew')
        self.instructions=ui.Label(self.wordsframe,
                                    text=self.getinstructions(),
                                    row=0, column=0)
        self.dirfn=self.nextword
        r=self.getword()
    def promptstrings(self,lang):
        if lang == self.analang:
            text=_("What is the form of the new "
                    "morpheme in {} \n(consonants and vowels only)?"
                    "".format(program['settings'].languagenames[lang]))
            ok=_('Use this form')
            skip=None
        else:
            text=_("What does ‘{}’ mean in {}?".format(
                            self.runwindow.form[self.analang],
                            program['settings'].languagenames[lang]))
            ok=_('Use this {} gloss for ‘{}’'.format(
                            program['settings'].languagenames[lang],
                            self.runwindow.form[self.analang]))
            self.runwindow.glosslangs.append(lang)
            skip = _('Skip {} gloss').format(program['settings'].languagenames[lang])
        return {'lang':lang, 'prompt':text, 'ok':ok, 'skip':skip}
    def submitform(self,lang):
        self.runwindow.form[lang]=self.runwindow.form[lang].get()
        self.runwindow.frame2.destroy()
    def promptwindow(self,lang):
        def skipform(event=None):
            del self.runwindow.form[lang]
            self.runwindow.frame2.destroy() #Just move on.
        strings=self.promptstrings(lang)
        self.runwindow.frame2=ui.Frame(self.runwindow.frame,
                                        row=1,column=0,
                                        sticky='ew',
                                        padx=25,pady=25)
        getform=ui.Label(self.runwindow.frame2,text=strings['prompt'],
                        font='read',row=0,column=0,
                        padx=self.runwindow.padx,
                        pady=self.runwindow.pady)
        #field rendering is better in another frame:
        eff=ui.Frame(self.runwindow.frame2,row=1,column=0)
        #variable and field for entry:
        self.runwindow.form[lang]=ui.StringVar()
        formfield = ui.EntryField(eff, render=True,
                                    textvariable=self.runwindow.form[lang],
                                    row=1,column=0,
                                    sticky='')
        formfield.focus_set()
        formfield.bind('<Return>',lambda event,l=lang:self.submitform(l))
        formfield.rendered.grid(row=2,column=0,sticky='new')
        sub_btn=ui.Button(self.runwindow.frame2,text = strings['ok'],
                            command = self.submitform,
                            anchor ='c',row=2,column=0,sticky='')
        if strings['skip']:
            sub_btnNo=ui.Button(self.runwindow.frame2,
                                text = strings['skip'],
                                command = skipform,
                                row=1,column=1,sticky='')
        self.runwindow.waitdone()
        sub_btn.wait_window(self.runwindow.frame2) #then move to next step
    def addmorpheme(self):
        self.getrunwindow()
        self.runwindow.form={}
        self.runwindow.glosslangs=list()
        form={}
        self.runwindow.padx=50
        self.runwindow.pady=10
        self.runwindow.title(_("Add Morpheme to Dictionary"))
        title=_("Add {} morpheme to the dictionary").format(
                            program['settings'].languagenames[self.analang])
        ui.Label(self.runwindow.frame,text=title,font='title',
                justify=ui.LEFT,
                anchor='c',sticky='ew',
                row=0,column=0,
                padx=self.runwindow.padx,
                pady=self.runwindow.pady)
        # Run the above script (makewindow) for each language, analang first.
        # The user has a chance to enter a gloss for any gloss language
        # already in the datbase, and to skip any as needed/desired.
        for lang in [self.analang]+program['db'].glosslangs:
            if lang in self.runwindow.form:
                continue #Someday: how to do monolingual form/gloss here
            if not self.runwindow.exitFlag.istrue():
                x=self.promptwindow(lang)
                if x:
                    return
        """get the new senseid back from this function, which generates it"""
        if not self.runwindow.exitFlag.istrue(): #don't do this if exited
            self.runwindow.withdraw() #or wait?
            senseid=program['db'].addentry(ps='',analang=self.analang,
                            glosslangs=self.runwindow.glosslangs,
                            form=self.runwindow.form)
            # Update profile information in the running instance, and in the file.
            self.runwindow.destroy()
            """The following are useless without ps information, so they will
            have to come later."""
            # if program['taskchooser'].donew['collectionlc']:
            #     program['settings'].getprofileofsense(senseid)
            #     program['slices'].updateslices()
            #     program['settings'].getscounts()
            #     program['settings'].storesettingsfile(setting='profiledata') #since we changed this.
    def addCAWLentries(self):
        text=_("Adding CAWL entries to fill out, in established database.")
        self.wait(msg=text)
        log.info(text)
        self.cawldb=loadCAWL()
        added=[]
        modded=[]
        for n in program['taskchooser'].cawlmissing:
            log.info("Working on SILCAWL line #{:04}.".format(n))
            e=self.cawldb.get('entry', path=['cawlfield'],
                                    cawlvalue="{:04}".format(n),
                                    ).get('node')[0] #certain to be there
            try:
                eps=self.cawldb.get('sense/ps',node=e,
                                    # showurl=True
                                    ).get('node')[0]
                epsv=eps.get('value')
            except IndexError:
                log.info("line {} w/o lexical category; leaving.".format(n))
                eps=epsv=None
            if epsv == "Noun":
                log.info("Found a noun, using {}".format(program['settings'].nominalps))
                eps.set('value',program['settings'].nominalps)
            elif epsv == "Verb":
                log.info("Found a verb, using {}".format(program['settings'].verbalps))
                eps.set('value',program['settings'].verbalps)
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
                entry=program['db'].get('entry',gloss=g,glosslang=lang,
                                        ).get('node') #maybe []
                if entry:
                    log.info("Found gloss of SILCAWL line #{:04} ({}); "
                            "adding info to that entry.".format(n,g))
                    program['db'].fillentryAwB(entry[0],e)
                    modded.append(n)
                    break
            if not entry: #i.e., no match for any self.glosslangs gloss
                tnodes=e.findall('lexical-unit/form/text')
                for tn in tnodes:
                    tn.text=''
                log.info("Gloss of SILCAWL line #{:04} ({}) not found; "
                        "copying over that entry.".format(n,g))
                program['db'].nodes.append(e)
                added.append(n)
        if added or modded:
            program['db'].write()
            title=_("Entries Added!")
            text=_("Added {} entries from the SILCAWL").format(len(added))
            if len(added)<100:
                text+=": ({})".format(added)
            text+=_("\nModded {} entries with new information from the "
                    "SILCAWL").format(len(modded))
            if len(modded)<100:
                text+=": ({})".format(modded)
            program['taskchooser'].getcawlmissing()
            self.dobuttonkwargs()
        else:
            title=_("Error trying to add SILCAWL entries")
            text=_("We seem to have not added or modded any entries, which "
                    "shouldn't happen! (missing: {})"
                    "".format(program['taskchooser'].cawlmissing))
        self.waitdone()
        log.info(text)
        ErrorNotice(text,title=title)
    def nextword(self,nostore=False):
        self.dirfn=self.nextword
        # log.info("running nextword (nostore = {})".format(nostore))
        if not nostore:
            # log.info("storing nextword (nostore = {})".format(nostore))
            self.storethisword()
        else:
            log.info("Not storing {}, by request".format(self.sense.id))
        if self.index < len(self.entries)-1:
            self.index+=1
        self.getword()
    def backword(self,nostore=True):
        self.dirfn=self.backword
        if not nostore:
            self.storethisword()
        else:
            log.info("Not storing {}, by request".format(self.sense.id))
        if self.index == 0:
            self.index=len(self.entries)-1
        else:
            self.index-=1
        self.getword()
    def storethisword(self):
        log.info("Trying to store {} ({})".format(self.var.get(),self.ftype))
        try:
            if self.ftype in ['lc','lx']:
                self.sense.textvaluebyftypelang(self.ftype,
                                            self.analang,
                                            self.var.get())
            elif self.ftype == 'pl':
                self.entry.plvalue(
                        program['settings'].secondformfield[program['settings'].nominalps],
                        self.analang,
                        self.var.get())
                # lift.prettyprint(self.entry.pl)
            elif self.ftype == 'imp':
                self.entry.impvalue(
                        program['settings'].secondformfield[program['settings'].verbalps],
                        self.analang,
                        self.var.get())
            # self.entry.lc.textvaluebylang(self.analang,self.var.get())
            self.maybewrite() #only if above is successful
            # lift.prettyprint(self.entry)
        # except KeyError:
        except AttributeError as e:
            log.info("Not storing word (WordCollection): {}".format(e))
    def markimage(self,url,w=None):
        """return to file, LIFT"""
        log.info("Selected image {}".format(url))
        if w:
            w.on_quit()
        filename=self.sense.imagename() #new file name
        saveimagefile(url,filename)
        self.sense.illustrationvalue(filename)
        self.maybewrite()
        self.wordframe.pic.reloadimage()
        self.updatereturnbind()
    def selectlocalimage(self,event=None):
        log.info("Select a local image")
        f=file.askopenfilename()
        if f and file.exists(f):
            self.markimage(f)
    def showimagestoselect(self,files):
        log.info("Select from these images: \n{}".format('\n'.join(
                                                    [str(i) for i in files])))
        self.selectionwindow=ui.Window(self)
        title=_("Select a good image for {}".format(self.glossesthere))
        self.selectionwindow.title(title)
        t=ui.Label(self.selectionwindow.frame,text=title, font='title',
                    row=0,column=0)
        sf=ui.ScrollingFrame(self.selectionwindow.frame,row=1,column=0)
        cols=4
        for n,f in enumerate(files+['local']):
            # log.info("Using row {}, col {}".format(n//cols,n%cols))
            if f == 'local':
                ui.Button(sf.content,text=_("local file"),
                    cmd=self.selectlocalimage,
                    row=n//cols,column=n%cols,sticky='nsew')
            else:
                i=ImageFrame(sf.content,url=f,pixels=0,
                            row=n//cols, column=n%cols,
                            sticky='nsew')
                if i.image:
                    i.bindchildren('<ButtonRelease-1>',
                                    lambda event,x=f,w=self.selectionwindow:
                                            self.markimage(x,w))
    def getimagefiles(self):
        if file.exists(self.sense.imgselectiondir):
            return file.getfilesofdirectory(self.sense.imgselectiondir)
    def selectimage(self,event=None):
        files=self.getimagefiles()
        if not files:
            self.getopenclipart()
        files=self.getimagefiles()
        if files: #still
            self.showimagestoselect(files)
    def downloadallCAWLimages(self):
        for self.sense in program['db'].senses:
            if not file.exists(self.sense.imgselectiondir):
                self.getopenclipart(nogui=True)
    def getopenclipart(self,event=None,nogui=False):
        self.wait(msg="Dowloading images from OpenClipart.org\n{}"
                        "".format(" ".join(self.sense.collectionglosses)))
        log.info("Glosses: {}".format(self.sense.collectionglosses))
        scraper=htmlfns.ImageScraper()
        for gloss in self.sense.collectionglosses:
            kwargs={'per_page':50,
                    "query":gloss #just one word at a time is less restrictive
                    }
            terms=urls.urlencode(kwargs)
            url='https://openclipart.org/search/?'+terms
            try:
                html=htmlfns.getdecoded(url)
            except urls.MaxRetryError as e:
                msg=_("Problem downloading webpage; check your "
                            "internet connection!\n\n{}".format(e))
                log.error(msg)
                ErrorNotice(msg)
                return
            scraper.feed(html)
            logo=[i for i in scraper.images
                                    if 'openclipart-logo-2019.svg' in i['src']]
            # log.info("scraper.images: ({})".format(scraper.images))
            # log.info("logo: ({})".format(logo))
            if logo and logo[0] in scraper.images:
                # log.info("found logo! ({})".format(logo[0]))
                scraper.images.remove(logo[0])
        self.images=[]
        for i in scraper.images:
            if i not in self.images:
                self.images.append(i)
        log.info("Found {} images: {}".format(len(self.images),self.images))
        if self.images:
            file.makedir(self.sense.imgselectiondir)
        problems=0
        for i in self.images:
            url=htmlfns.imgurl(i['src'])
            num=i['src'].split('/')[-1]
            i['filename']='_'.join([num,rx.urlok(i.get('alt','noalt'))])
            # log.info("{} ({})".format(url,i['filename']))
            log.info("{}".format(i['filename']))
            try:
                pic=htmlfns.getbinary(url, timeout=10)
                # log.info("response data type: {}".format(type(response.data)))
                i['fqdn']=file.getdiredurl(self.sense.imgselectiondir,
                                        i['filename'])
                with open(i['fqdn'],'wb') as d:
                    d.write(pic)
            except urls.MaxRetryError as e:
                log.error("Problem downloading image: {}".format(e))
                problems+=1
            self.waitprogress(self.images.index(i)*100/len(self.images))
        if (me and not nogui) or len(self.images) < 5:
            text="Found {} images!".format(len(self.images))
            if problems:
                text+=_("\nProblems downloading {} images".format(problems))
            ErrorNotice(text,
                        button=(_("Select local image"),self.selectlocalimage))
        self.waitdone()
    def killwordframe(self):
        f=getattr(self,'wordframe',None)
        if isinstance(f,ui.Frame) and f.winfo_exists():
            # log.info("Destroying word frame")
            f.destroy()
            # log.info("Destroy done")
        # else:
        #     log.info("Not destroying word frame {}".format(isinstance(f,ui.Frame)))
        #     log.info("word frame: {}".format(f))
        #     if f:
        #         log.info("word frame exists: {}".format(f.winfo_exists()))
    def dowordframe(self):
        f=getattr(self,'wordframe',None)
        if isinstance(f,ui.Frame) and f.winfo_exists():
            # log.info("Skipping word frame; already exists!")
            return
        log.info("doing word frame")
        self.wordframe=ui.Frame(self.wordsframe,row=1,column=0,sticky='ew')
        self.prog=ui.Label(self.wordframe, text='', row=1, column=3,
                            font='small')
        self.glossesline=ui.Label(self.wordframe, text='',
                                    font='read',
                                    row=1, column=0, columnspan=3, sticky='ew')
        back=ui.Button(self.wordframe,text=_("Back"),cmd=self.backword,
                        row=4, column=0, sticky='w',anchor='w')
        next=ui.Button(self.wordframe,text=_("Next"),cmd=self.nextword,
                        row=4, column=2, sticky='e',anchor='e')
        self.var=ui.StringVar()
        self.lxenter=ui.EntryField(self.wordframe,textvariable=self.var,
                                row=3,column=0,columnspan=3,
                                sticky='ew')
        next.bind_all('<Up>',lambda event: self.backword(nostore=True))
        next.bind_all('<Prior>',lambda event: self.backword(nostore=True))
        next.bind_all('<Down>',lambda event: self.nextword(nostore=True))
        next.bind_all('<Next>',lambda event: self.nextword(nostore=True))
    def updatereturnbind(self):
        try:
            assert self.wordframe.pic.hasimage
            self.lxenter.bind_all('<Return>',
                                lambda event: self.nextword(nostore=False))
        except AssertionError:
            self.wordframe.pic.bind_all('<Return>', self.selectimage)
    def getword(self):
        program['taskchooser'].withdraw()# not sure why necessary
        # log.info("sensetodo: {}".format(getattr(self,'sensetodo',None)))
        # log.info("wordframe: {}".format(getattr(self,'wordframe',None)))
        if getattr(self,'sensetodo',None):
            log.info("Sense to do: {}".format(self.sensetodo))
            self.instructions['text']=self.getinstructions() #in case changed
            self.dowordframe()
        elif not self.entries:
            text=_("It looks like you're done filling out the empty "
            "entries in your database! Congratulations! You can still add words "
            "through the button on the left ({})."
            "".format(self.dobuttonkwargs()['text']))
            self.killwordframe()
            self.instructions['text']=text
            self.instructions.wrap()
            return
        else:
            self.dowordframe()
        log.info("sensetodo: {}".format(getattr(self,'sensetodo',None)))
        log.info("wordframe: {}".format(getattr(self,'wordframe',None)))
        self.prog['text']="({}/{})".format(self.index+1,self.nentries)
        # log.info("entries: {}".format(self.entries))
        log.info("index: {}".format(self.index))
        if getattr(self,'sensetodo',None):
            self.entry=self.sensetodo.entry
        else:
            self.entry=self.entries[self.index]
        self.sense=self.entry.sense
        glosses={}
        for g in set(self.glosslangs) & set(self.sense.glosses):
            glosses[g]=', '.join(self.sense.formattedgloss(g,quoted=True))
        self.glossesthere=' — '.join([glosses[i] for i in glosses if i])
        # log.info("glosses there: {}".format(self.glossesthere))
        if not self.glossesthere:
            log.info("entry {} doesn't have glosses; not showing."
                    "".format(self.entry.get('id')))
            self.dirfn(nostore=True)
        self.glossesline['text']=self.glossesthere
        self.glossesline.wrap()
        if isinstance(getattr(self.wordframe,'pic',None),ImageFrame):
            self.wordframe.pic.changesense(self.sense)
        else:
            self.wordframe.pic=ImageFrame(self.wordframe, self.sense,
                                            row=2, column=0,
                                            columnspan=3, sticky='')
        self.updatereturnbind()
        """I don't want this on every ImageFrame, just here"""
        self.wordframe.pic.bindchildren('<ButtonRelease-1>', self.selectimage)
        default=self.sense.textvaluebyftypelang(self.ftype,self.analang)
        if not default:
            default=''
        self.var.set(default)
        self.lxenter.focus_set()
        self.frame.grid_columnconfigure(1,weight=1)
        self.deiconify()
        self.lift()
        self.wordframe.update_idletasks()
    def __init__(self, parent):
        Segments.__init__(self,parent)
        self.dodone=False
class WordCollectionLexeme(TaskDressing,WordCollection):
    def tooltip(self):
        return _("Don't use this task.")
    def tasktitle(self):
        return _("Word Collection for Lexeme Forms")
    def __init__(self, parent): #frame, filename=None
        """This should never really be used, though I made it first, so I've
        left it"""
        TaskDressing.__init__(self,parent)
        WordCollection.__init__(self,parent)
        log.info("Initializing {}".format(self.tasktitle()))
        #Status frame is 0,0
        self.ftype=program['params'].ftype('lx') #lift.Entry.citationformnodeofentry
        self.getwords()
class WordCollectionCitation(TaskDressing,WordCollection):
    def tooltip(self):
        return _("This task helps you collect words in citation form.")
    def tasktitle(self):
        return _("Add Words") # for Citation Forms
    def __init__(self, parent): #frame, filename=None
        TaskDressing.__init__(self,parent)
        WordCollection.__init__(self,parent)
        log.info("Initializing {}".format(self.tasktitle()))
        #Status frame is 0,0
        self.ftype=program['params'].ftype('lc') #lift.Entry.citationformnodeofentry
        self.getwords()
class WordCollectionPlural(TaskDressing,WordCollection):
    def tooltip(self):
        return _("This task helps you collect plural word forms.")
    def tasktitle(self):
        return _("Add plural forms")
    def __init__(self, parent):
        TaskDressing.__init__(self,parent)
        WordCollection.__init__(self,parent)
        log.info("Initializing {}".format(self.tasktitle()))
        #Status frame is 0,0
        self.ftype=program['params'].ftype('pl')
        # self.nodetag='citation' #lift.Entry.citationformnodeofentry
        self.getwords()
class WordCollectionImperative(TaskDressing,WordCollection):
    def tooltip(self):
        return _("This task helps you collect imperative word forms.")
    def tasktitle(self):
        return _("Add imperative forms")
    def __init__(self, parent):
        TaskDressing.__init__(self,parent)
        WordCollection.__init__(self,parent)
        log.info("Initializing {}".format(self.tasktitle()))
        #Status frame is 0,0
        self.ftype=program['params'].ftype('imp')
        # self.nodetag='citation' #lift.Entry.citationformnodeofentry
        self.getwords()
class Parse(Segments):
    """docstring for Parse."""
    def getgloss(self,ftype=None):
        return ", ".join([", ".join(self.parser.sense.formattedgloss(l,
                                                            ftype=ftype,
                                                            quoted=True))
                        for l in self.glosslangs])
    def userconfirmation(self,*args):
        log.info("asking for user confirmation")
        # Return True or False only
        def do(x):
            self.userresponse.value=x
            l.destroy()
        level, lx, lc, sf, ps, afxs = args
        if self.exitFlag.istrue():
            return
        w=ui.Window(self,noexit=True)
        w.title(_("Confirm this combination of affixes?"))
        self.userresponse.value=False
        gloss=self.getgloss()
        text=_("This parse looks good ({}): "
                "\n{} {}"
                "\n{} {}"
                "\n{} root: {} ({})"
                ).format(self.parser.levels()[level],
                        lc,afxs[0],sf,afxs[1],
                        ps,lx,gloss,
                        )
        glosslc=self.getgloss()
        if ps == self.nominalps:
            ftype='pl'
        elif ps == self.verbalps:
            ftype='imp'
        glosssf=self.getgloss(ftype=ftype)
        self.presentationframe=ui.Frame(w.frame,row=1,column=0,sticky='ew')
        self.lcframe=ui.Frame(self.presentationframe,
                                row=0,column=0,
                                padx=10,
                                sticky='ew')
        lcmorphs=list(afxs[0])
        lcmorphs.insert(1,lx)
        l=ui.Label(self.lcframe,
                text='-'.join([i for i in lcmorphs if i]),font='title',
                row=0,column=0)
        ImageFrame(self.lcframe,self.sense,
                    row=1,column=0,sticky='')
        ui.Label(self.lcframe,
                text=glosslc,font='readbig',
                row=2,column=0)
        self.sfframe=ui.Frame(self.presentationframe,
                                row=0,column=1,
                                padx=10,
                                sticky='ew')
        sfmorphs=list(afxs[1])
        sfmorphs.insert(1,lx)
        ui.Label(self.sfframe,
                text='-'.join([i for i in sfmorphs if i]),font='title',
                row=0,column=1)
        ImageFrame(self.sfframe,self.sense,ftype=ftype,
                    row=1,column=1,sticky='')
        ui.Label(self.sfframe,
                text=glosssf,font='readbig',
                row=2,column=1)
        self.responseframe=ui.Frame(w.frame,row=2,column=0,sticky='ew')
        ui.Button(self.responseframe,
                    text=_("Yes!"),
                    command=lambda x=True: do(x),
                    row=0,column=0,sticky='ew')
        ui.Button(self.responseframe,
                    text=_("No!"),
                    command=lambda x=False: do(x),
                    row=0,column=1,sticky='ew')
        self.noticeframe=ui.Frame(w.frame,row=3,column=0)
        t=_("This parse looks good ({})\n").format(self.parser.levels()[level])
        ui.Label(self.noticeframe,text=t+self.currentformnotice(),
                    font='small',justify='l',
                    row=0,column=0)
        if self.iswaiting():
            self.waitpause()
        w.wait_window(l) #canary on label, not window
        # log.info("exit flag for w({}):{}; self({}):{}"
        #         "".format(w,w.exitFlag,self,self.exitFlag))
        if w.exitFlag.istrue():
            # log.info("Exited parse!")
            self.waitdone()
            self.exited=True
        else:
            # w.on_quit()
            w.destroy()
            if self.iswaiting():
                self.waitunpause()
            # log.info("User responded {}".format(self.userresponse.value))
            return self.userresponse.value
    def selectsffromlist(self,l):
        def formattuple(l):
            pfx,sfx=l[-1]
            if pfx:
                pfx+='-'
            if sfx:
                sfx='-'+sfx
            if pfx or sfx:
                rootafxs=[l[2],'affixes:',pfx,sfx]
            else:
                rootafxs=[l[2]]
            return "{} ({} root: {})".format(*l[:2],' '.join(rootafxs))
        def neither():
            # These count askparsed; evaluated and moving on
            self.parsecatalog.addneither(self.parser.sense.id)
            #don't leave 'neither' with ps indication
            self.parser.sense.rmpsnode()
            # self.parser.rmpssubclassnode() #leave this for posterity?
            t.destroy()
        # l=(sf,ps,root,lcafxs,sfafxs)
        # log.info("full option list: {}".format(l))
        if self.exitFlag.istrue():
            return
        if self.iswaiting():
            self.waitpause()
        ln=[(i,formattuple(i)) for i in l if i[1] == self.nominalps]
        ln+=[('ON',_("Another {}").format(self.secondformfield[self.nominalps]))]
        # log.info("noun option list: {}".format(ln))
        lv=[(i,formattuple(i)) for i in l if i[1] == self.verbalps]
        lv+=[('OV',_("Another {}").format(self.secondformfield[self.verbalps]))]
        # log.info("verb option list: {}".format(lv))
        w=ui.Window(self)
        w.title(_("Select second form"))
        t=ui.Label(w.frame,
                    text="What is the {} or {} of \n‘{}’ ({})?"
                        "".format(
                        self.secondformfield[self.nominalps],
                        self.secondformfield[self.verbalps],
                        self.parser.entry.lc.textvaluebylang(self.analang),
                        self.getgloss()
                                ),
                    font='title',
                    row=0,column=0,columnspan=2)
        t.wrap()
        if ln:
            noun=ui.Frame(w.frame, row=1, column=0, sticky='n')
            ImageFrame(noun,self.sense,ftype='pl',row=0,column=0, sticky='')
            ui.Label(noun,
                    text="Select {} form".format(
                                        self.secondformfield[self.nominalps]),
                    row=1,column=0,
                    columnspan=2)
            bfn=ui.ScrollingButtonFrame(noun, optionlist=ln, window=t,
                                        command=self.parser.dooneformparse,
                                        row=2, column=0,
                                        columnspan=2
                                        )
        if lv:
            verb=ui.Frame(w.frame, row=1, column=1, sticky='n')
            ImageFrame(verb,self.sense,ftype='imp',row=0,column=0, sticky='')
            ui.Label(verb,
                    text="Select {} form".format(
                                        self.secondformfield[self.verbalps]),
                    row=1,column=0)
            bfv=ui.ScrollingButtonFrame(verb, optionlist=lv, window=t,
                                        command=self.parser.dooneformparse,
                                        row=2, column=0)
        neitherb=ui.Button(w.frame, text=_("Neither"),
                        command=neither,
                        row=1, column=2, sticky='ns')
        ui.Label(w.frame,text=self.currentformnotice(),
                    font='small',justify='l',
                    row=2,column=0,columnspan=3)
        w.bind_all('<Escape>', lambda event:w.on_quit)
        w.wait_window(t)
        if w.exitFlag.istrue():
            self.exited=True
        # w.on_quit()
        w.destroy()
        if self.iswaiting():
            self.waitunpause()
    def asksegmentsnops(self):
        for ps in [self.nominalps, self.verbalps]:
            r=self.asksegments(ps)
            if not r or self.exited: #i.e., returned OK
                break
    def currentformnotice(self):
        return _("currently: {} ({ps} root), {}, {} ({pl}), {} ({imp})"
                ).format(*self.parser.texts(),
                        ps=self.parser.sense.psvalue(),
                        pl=self.secondformfield[self.nominalps],
                        imp=self.secondformfield[self.verbalps]
                        )
    def asksegments(self,ps):
        def do(event=None):
            self.parser.sense.psvalue(ps)
            if ps == self.nominalps:
                # tag='pl'
                fn=self.parser.entry.plvalue
            elif ps == self.verbalps:
                # tag='imp'
                fn=self.parser.entry.impvalue
            # lift.prettyprint(self.parser.entry.imp)
            # lift.prettyprint(self.parser.entry.pl)
            # log.info("value: {}".format(segments.get()))
            # lift.prettyprint(self.parser.entry.imp)
            # lift.prettyprint(self.parser.entry.pl)
            fn(self.secondformfield[ps],self.analang,segments.get())
            # log.info("v: {}".format(fn(self.secondformfield[ps],self.analang)))
            # self.parser.nodetextvalue(tag,segments.get())
            b.destroy()
        def next(event=None):
            segments.set("")
            b.destroy()
            # w.on_quit()
        if self.exitFlag.istrue():
            return
        log.info("asking for second form segments for ‘{}’ ps: {} ({}; {})"
                "".format(self.parser.entry.lc.textvaluebylang(self.analang),
                            ps,self.parser.senseid,
                            self.parsecatalog.parsen()))
        sfname=self.secondformfield[ps]
        if self.iswaiting():
            self.waitpause()
        w=ui.Window(self)
        w.title(_("Type second form"))
        l=ui.Label(w.frame,
                text="What {} form goes with ‘{}’ ({})?"
                    "".format(sfname,
                            self.parser.entry.lc.textvaluebylang(self.analang),
                            self.getgloss()),
                font='title',
                row=0,column=0,columnspan=2)
        l.wrap()
        if ps == self.nominalps:
            ftype='pl'
        elif ps == self.verbalps:
            ftype='imp'
        ImageFrame(w.frame,self.parser.sense,ftype=ftype,row=0,column=2)
        segments=ui.StringVar()
        segments.set(self.parser.entry.lc.textvaluebylang(self.analang))
        e=ui.EntryField(w.frame,textvariable=segments,
                        row=1,column=0)
        b=ui.Button(w.frame,text=_("OK"),cmd=do,
                        row=2,column=0, sticky='e')
        ui.Button(w.frame,text=_("Not a {}").format(ps),cmd=next,
                        row=2,column=1, sticky='e')
        ui.Label(w.frame,text=self.currentformnotice(),
                    font='small',justify='l',
                    row=3,column=0,columnspan=2)
        e.focus_set()
        e.bind('<Return>',do)
        w.wait_window(b)
        if w.exitFlag.istrue():
            self.exited=True
        if self.iswaiting():
            self.waitunpause()
        # w.on_quit()
        w.destroy()
        if not segments.get():
            return 1
        elif not self.exited:
            self.trytwoforms()
    def tryoneform(self):
        log.info("Asking for second form selected (parse w/one form)")
        r=self.parser.oneform()
        if r:
            self.selectsffromlist(r)
            log.info("Done selecting from {}".format(r))
        else:
            return 1 #no forms to select from, or exited; move on
        if self.parser.on:
            # log.info("asking for other noun segments")
            self.asksegments(self.nominalps)
        elif self.parser.ov:
            # log.info("asking for other verb segments")
            self.asksegments(self.verbalps)
        if not self.exited:
            log.info("User seems to have selected a second form, or neither")
    def trytwoforms(self):
        log.info("Trying for parse with two forms")
        r=self.parser.twoforms()
        # return level, lx, lc, sf, self.ps, afxs #from self.parser.twoforms
        if not r:
            log.info("Auto parsed {} with two forms".format(self.sense.id))
            return
        elif r and isinstance(r,tuple) and self.userconfirmation(*r):
            self.parser.doparsetolx(r[1],*r[4:]) #pass root, too
            return
        return 1 #do not return empty list, bool = False
    def trythreeforms(self):
        log.info("Trying for parse with three forms")
        r=self.parser.threeforms()
        #This gives r= tuple to check, or 1 if skipped. no UI = no self.exit set
        # log.info("reponse: {} ({})".format(r,type(r)))
        if not r:
            log.info("Auto parsed {} with three forms (returned {})"
                    "".format(self.sense.id,r))
            return
        elif r and isinstance(r,tuple) and self.userconfirmation(*r):
            # return level, lx, lc, sf, self.ps, afxs #from self.parser.threeforms
            log.info("r={}".format(r))
            log.info("sending {}".format(r[4:]))
            log.info("sending {}; {}".format(*r[4:]))
            self.parser.addaffixset(*r[4:])#self.ps,afxs)
            self.parser.sense.pssubclassvalue(r[-1])
            return
        return r
    def parse(self,**kwargs):
        # These functions return nothing when the parse goes through, 1 when
        # not done. If the user exits, self.exited is set
        self.exited=False
        r=True #i.e., do the next fn
        if not kwargs:
            kwargs={
                'sense':self.sense
                }
        self.parser.parseentry(**kwargs) #sets entry, sense, and senseid for parser
        log.info("lx: {}, lc: {}, pl: {}, imp: {}".format(*self.parser.texts()))
        if min(self.parser.auto, self.parser.ask) <= 4:# and not badps:
            r=self.trythreeforms()
        # badps is OK here, but don't do twoforms if threeforms worked
        if r and not self.exited:
            r=self.trytwoforms()
            # log.info("trytwoforms returned {}".format(r))
        if r and not self.exited: #and still here
            r=self.tryoneform()
            # log.info("tryoneform returned {}".format(r))
        if r and not self.exited:
            # log.info("Asking for second form typed")
            self.asksegmentsnops()
        if not self.exited:
            try:
                self.parsecatalog.addparsed(self.sense.id)
            except: #upgrade to this
                self.parsecatalog.addparsed(kwargs['entry'].sense.id)
            self.maybewrite()
        # if self.parent.iswaiting():
        #     self.parent.waitdone()
        # self.parent.deiconify()
        if self.iswaiting():
            self.waitdone()
        self.deiconify()
    def initsensetodo(self):
        try:
            r=self.sensetodo
            self.sensetodo=None
        except AttributeError:
            if hasattr(self,'sensetodo'):
                log.info("self.sensetodo: {}".format(self.sensetodo.id))
            r=self.sensetodo=None
        if r:
            return [r] #only return this once.
        else:
            return [] #list, either way
    def senseidstoparse(self,senseids=None,all=False,n=-1): #n/limit=-1#1000
        s=self.initsensetodo()# This returns and resets
        if s:
            return s
        if not senseids:
            senseids=program['db'].senseids[:n]
        if all:
            return senseids #if provided, assume all
        else:
            try:
                return set(senseids)-set(self.parsecatalog.parsed)
            except AttributeError:
                return set(senseids)
    def getparses(self,**kwargs):
        log.info("parses already tried: {}".format(self.parsecatalog.parsen()))
        # for senseid in set(program['db'].senseids)-set(self.parsecatalog.parsed):
        #     self.parse(senseid)
        self.wait("Parsing (ask: {} auto: {})".format(self.parser.ask,
                                                        self.parser.auto
                                                    ))
        senseids=self.senseidstoparse(**kwargs)
        todo=len(senseids)
        for n,self.sense in enumerate(
                                [program['db'].sensedict[i] for i in senseids]):
            self.parse() #this can add to lists
            if self.exited:
                break
            if self.iswaiting():
                self.waitprogress(100*n//todo)
            # else:
            #     break
        self.waitdone()
        # log.info("total parses tried: {}".format(self.parsecatalog.parsen()))
        self.parsecatalog.report()
    # def getparse(self,senseid):
    #     if senseid not in self.parsed:
    #         self.parse(sense) #this can add to lists
    def nextparserasklevel(self):
        auto=self.parser.auto
        ask=self.parser.ask
        if ask:
            ask-=1 #start a new level with user confirmations
        log.info("Moving to parser levels auto: {} ask: {}".format(auto,ask))
        self.parser.setlevels(auto=auto,ask=ask)
    def nextparserautolevel(self):
        auto=self.parser.auto
        ask=self.parser.ask
        if auto:
            auto-=1 #catch up automation (stop asking at this level)
        log.info("Moving to parser levels auto: {} ask: {}".format(auto,ask))
        self.parser.setlevels(auto=auto,ask=ask)
    def initparsecatalog(self):
        # This method allows us to restart the affix database if needed,
        # like if there is a bad affix making bad autoparses...
        self.pss=program['db'].pss
        self.parsecatalog=self.parent.parsecatalog=parser.Catalog(self)
        collector=parser.AffixCollector(self.parsecatalog,program['db'])
        if self.loadfromlift:
            self.wait("Loading Affixes")
            # for i in collector.do():
            for i in collector.getfromlift():
                # log.info("Progress: {}".format(i))
                self.waitprogress(i)
            self.parsecatalog.report()
            self.waitdone()
    def showwhenready(self):
        try:
            assert self.frame.status.winfo_exists()
            log.info("showing")
            self.deiconify()
        except:
            log.info("not showing")
            self.after(1,self.showwhenready)
    def __init__(self, parent): #frame, filename=None
        self.byslice=False
        self.initsensetodo()
        Segments.__init__(self,parent)
        self.parent=parent
        self.secondformfield=program['settings'].secondformfield
        self.nominalps=program['settings'].nominalps
        self.verbalps=program['settings'].verbalps
        self.loadfromlift=True
        if hasattr(parent,'parsecatalog'):
            self.parsecatalog=parent.parsecatalog
        else:
            self.initparsecatalog()
        if hasattr(parent,'parser'):
            self.parser=parent.parser
        else:
            self.parser=parent.parser=parser.Engine(self.parsecatalog,self)
            #These should come from settings
            self.parser.autolevel(5) #no auto
            self.parser.asklevel(0)
        self.ftype=program['params'].ftype('lc') #Is this always correct?
        # self.nodetag='citation'
        self.dodone=True #give me words with citation done
        self.checkeach=False #don't confirm each word (default)
        self.dodoneonly=True #don't give me other words
        self.userresponse=Object()
        self.showwhenready()
class ParseWords(Parse,TaskDressing):
    def taskicon(self):
        return program['theme'].photo['iconWord']
    def tooltip(self):
        return _("This task will help you parse your citation forms, "
                "automatically and with confirmation.")
    def dobuttonkwargs(self):
        fn=self.getparses
        text=_("Parse!")
        tttext=_("{} tries to do as much as possible automatically, and "
                "according to the level you have set for confirmation."
                ).format(program['name'])
        return {'text':text,
                'fn':fn,
                # column=0,
                'font':'title',
                'compound':'bottom', #image bottom, left, right, or top of text
                'image':program['theme'].photo['Word'],
                'sticky':'ew',
                'tttext':tttext
                }
    def tasktitle(self):
        return _("Parse Words")
    def __init__(self, parent): #frame, filename=None
        log.info("Initializing {}".format(self.tasktitle()))
        TaskDressing.__init__(self,parent)
        Parse.__init__(self,parent)
        # self.checkeach=True #confirm each word
class WordCollectnParse(WordCollection,Parse,TaskDressing):
    """This task collects words, from the SIL CAWL, or one by one.
    First in citation form, then pl or imperativewith Parse"""
    def taskicon(self):
        return program['theme'].photo['iconWord']
    def tooltip(self):
        return _("This task helps you collect and parse words.")
    def dobuttonkwargs(self):
        if program['taskchooser'].cawlmissing:
            fn=self.addCAWLentries
            text=_("Add remaining CAWL entries")
            tttext=_("This will add entries from the Comparative African "
                    "Wordlist (CAWL) which aren't already in your database "
                    "(you are missing {} CAWL tags). If the appropriate "
                    "glosses are found in your database, CAWL tags will be "
                    "merged with those entries."
                    "\nDepending on the number of entries, this may take "
                    "awhile.").format(len(program['taskchooser'].cawlmissing))
        else:
            text=_("Add a Word")#?
            fn=self.addmorpheme#?
            tttext=_("This adds any word, but is best used after filling out a "
                    "wordlist, if the word you want to add isn't there "
                    "already.")
        return {'text':text,
                'fn':fn,
                # column=0,
                'font':'title',
                'compound':'bottom', #image bottom, left, right, or top of text
                'image':program['theme'].photo['Word'],
                'sticky':'ew',
                'tttext':tttext
                }
    def tasktitle(self):
        return _("Add and Parse Words") # for Citation Forms
    def storethisword(self):
        try:
            v=self.var.get()
            if v:
                self.withdraw()
                self.entry.lc.textvaluebylang(self.analang,v)
                self.parse(entry=self.entry)
            # if hasattr(self,'sensetodo') and self.sensetodo:
            self.sensetodo=None
            self.maybewrite() #only if above is successful
            log.info("Storing word: {}".format(self.sense.id))
        except AttributeError as e:
            log.info("Not storing word (WordCollectnParse): {}".format(e))
        self.deiconify()
    def __init__(self, parent):
        log.info("Initializing {}".format(self.tasktitle()))
        self.ftype=program['params'].ftype('lc') #always correct?
        # self.nodetag='citation'
        TaskDressing.__init__(self,parent)
        Parse.__init__(self,parent)
        WordCollection.__init__(self,parent)
        program['taskchooser'].withdraw()
        #This should either be adapted to use parse or not by keyword, or have
        # another method for addnParse
        # if me:
        #     self.downloadallCAWLimages()
        fn=self.getwords()#?
class ParseSlice(Parse):
    def tasktitle(self):
        return _("Parse One Slice")
    def tooltip(self):
        return _("This task will help you parse your citation forms, "
                "for one slice(?PS??!?) of the dictionary at a time.")
    def __init__(self, parent): #frame, filename=None
        Parse.__init__(self,parent)
        self.byslice=True #give me words in a selected slice (make this selectable?)
class ParseSliceWords(ParseSlice):
    def tasktitle(self):
        return _("Parse One Slice, word by word")
    def tooltip(self):
        return _("This task will help you parse your citation forms, "
                "for one slice of the dictionary at a time.")
    def __init__(self, parent): #frame, filename=None
        ParseSlice.__init__(self,parent)
        self.checkeach=True #confirm each word
class Placeholder(TaskDressing):
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
                "awhile.").format(len(program['taskchooser'].cawlmissing))
        return {'text':text,
                'fn':fn,
                # column=0,
                'font':'title',
                'compound':'bottom', #image bottom, left, right, or top of text
                'image':program['theme'].photo['icon'],
                'sticky':'ew',
                'tttext':tttext
                }
    def tasktitle(self):
        return _("Placeholder Check2")
    def __init__(self, parent): #frame, filename=None
        TaskDressing.__init__(self,parent)
        log.info("Initializing {}".format(self.tasktitle()))
        for r in range(5):
            ui.Label(self.frame,
                    text="This is a check placeholder.",
                    row=r, column=0)
class ToneFrameDrafter(ui.Window):
    def addback(self,lang,event=None):
        self.forms[lang]={
                        'before':'',
                        'after':''
                        }
        self.status()
    def skiplang(self,lang,event=None):
        del self.forms[lang]
        self.status()
    def analangftypecode(self):
        return '_'.join([self.analang,self.forms['field']])
    def stripftypecode(self,x):
        return x.removesuffix('_'+self.forms['field'])
    def status(self):
        if self.exitFlag.istrue():
            return
        try:
            self.fds.destroy()
            self.exf.destroy()
        except AttributeError:
            log.info("Probably the first time running status.")
        self.fds=ui.Frame(self.content,row=1,column=0)
        if 'field' not in self.forms:
            d=program['params'].ftype()
            log.info("Didn't find field type; setting current ({}).".format(d))
            self.forms['field']=d
        if 'name' not in self.forms:
            log.info("Didn't find a name; prompting.")
            self.promptwindow()
            if ('name' not in self.forms or #not started
                    isinstance(self.forms['name'],ui.StringVar) #i.e., not saved
                    or not self.forms['name']): # empty
                log.info("Name form not entered. Exiting. ({})"
                        "".format(self.forms['name']))
                self.on_quit()
            # log.info(self.forms)
            # log.info(self.exitFlag.istrue())
            return
        # log.info("Found name")
        # log.info("Starting status with self.form: {}".format(self.forms))
        text=self.forms['name']
        if text == '':
            text=_("Give a frame name!")
        nametext=_("Frame name:")
        # log.info("Frame name: {}".format(text))
        relief='raised' #flat, raised, sunken, groove, and ridge
        frameparams=ui.Frame(self.fds,columnspan=4,column=0,row=0,pady=50,
                            # highlightthickness=5,
                            # highlightbackground=self.theme.activebackground
                            )
        nameframe=ui.Frame(frameparams,columnspan=2,column=0,row=0,padx=50)
        namelabel=ui.Label(nameframe,text=nametext,column=0,row=0)
        namebutton=ui.Button(nameframe, relief=relief,
                            cmd=self.promptwindow,
                            text=text,column=1,row=0)
        text=_("Set the frame name for status table and reports")
        ui.ToolTip(namebutton,text)
        fieldname=_("Field to frame:")
        ftypeframe=ui.Frame(frameparams,column=2,row=0)
        ftypelabel=ui.Label(ftypeframe,text=fieldname,column=0,row=0)
        ftypebutton=ui.Button(ftypeframe,text=self.fieldtypename(),
                            cmd=self.getfieldtype,
                            relief=relief,
                            column=1,row=0)
        ui.ToolTip(ftypelabel)
        self.forms['field']
        self.langs=[self.analangftypecode()]+program['db'].glosslangs
                                    # [i for
                                    # i in program['db'].glosslangs #in db
                                    # # if i != self.analang
                                    # ]
        for l in [self.analangftypecode()]+program['settings'].glosslangs: #actually selected
            try:
                self.forms[l]['after']=self.forms[l].get('after','')
            except KeyError: #i.e., if no l in self.forms
                self.forms[l]={'after':''}
            self.forms[l]['before']=self.forms[l].get('before','')
        # log.info("Langs done: {}".format(langs))
        # log.info("self.langs: {}".format(self.langs))
        # log.info("Langs in process: {}".format(langsbeforeonly))
        # log.info("Langs langstodo: {}".format(langstodo))
        nothing='______'#"<"+_("nothing")+">"
        for n,l in enumerate(self.langs):
            langname=program['settings'].languagenames[self.stripftypecode(l)]
            if l in self.forms:
                log.info("Working on {}".format(langname))
                if l == self.stripftypecode(l):
                    tintro=_("Gloss in {}:").format(langname)
                    b=ui.Button(self.fds,text='X',
                            cmd=lambda l=l:self.skiplang(l),
                            column=0,row=n+1,sticky='e')
                    b.tt=ui.ToolTip(b, _("Skip {}").format(langname))
                else:
                    tintro=_("{}:").format(langname)
                ui.Label(self.fds,text=tintro,column=1,row=n+1)
                lineframe=ui.Frame(self.fds,column=2,row=n+1)
                if "Language " in langname:
                    tword=_("<word>")
                else:
                    tword=_("<{0} word>").format(langname)
                try:
                    text=self.forms[l]['before']
                    if text == '':
                        text=nothing
                except KeyError:
                    try:
                        self.forms[l]={'before':''}
                        text=nothing
                    except:
                        text="<"+_("No {} frame info").format(
                                program['settings'].languagenames[l])+">"
                button=ui.Button(lineframe,text=text,
                                relief=relief,
                                cmd=lambda l=l, context='before':
                                        self.promptwindow(l,context),
                                column=1,row=0,padx=0,ipadx=0)
                ui.ToolTip(button)
                if l not in self.forms:
                    continue
                ui.Label(lineframe,text=tword,column=2,row=0,padx=0,ipadx=0)
                try:
                    text=self.forms[l]['after']
                    if text == '':
                        text=nothing
                except KeyError:
                    if 'before' in self.forms[l]:
                        self.forms[l]={'after':''} #in case it got deleted
                        text=nothing
                button=ui.Button(lineframe,text=text,
                                relief=relief,
                                cmd=lambda l=l, context='after':
                                        self.promptwindow(l,context),
                                column=3,row=0,padx=0,ipadx=0)
                ui.ToolTip(button)
            else:
                text=_("Add {0} gloss").format(langname)
                button=ui.Button(self.fds,text=text,
                                relief=relief,
                                font='small',
                                cmd=lambda l=l: self.addback(l),
                                columnspan=2,column=0,row=n+1,padx=0,ipadx=0)
                ui.ToolTip(button,_("Add {} values for this frame").format(
                                    langname
                                    ))
        text=_("Get Example")
        exemplify=ui.Button(self.fds,text=text,cmd=self.exemplified,
                            columnspan=2,column=0,row=n+2)
        exemplify.update_idletasks()
    def setfieldtype(self,choice,window):
        self.forms['field']=choice
        window.on_quit()
        self.status()
    def fieldtypename(self):
        return [i[1] for i in self.fieldtypes()
                    if i[0] == self.forms['field']][0]
    def fieldtypes(self):
        # try:
        #     log.info("{}".format(program['settings'].pluralname))
        #     log.info("{}".format(program['settings'].imperativename))
        #     log.info("{}".format(program['settings'].secondformfield[program['settings'].verbalps]))
        #     log.info("{}".format(program['settings'].secondformfield[program['settings'].nominalps]))
        # except Exception as e:
        #     log.error("Exception in ps-land:{}".format(e))
        opts=[
                ('lc', _("Citation form")),
                ('lx', _("Lexeme form")),
                ]
        """These should maybe be switched over to just pl and imp"""
        if self.ps == program['settings'].nominalps:
            opts.append((program['settings'].pluralname, _("Plural form")))
        elif self.ps == program['settings'].verbalps:
            opts.append((program['settings'].imperativename, _("Imperative form")))
        return [(i,j) for (i,j) in opts if i]
    def getfieldtype(self,event=None):
        w=ui.Window(self,
                        row=1,column=0,
                        sticky='ew',
                        padx=25,pady=25)
        w.title(_("Select which field to frame"))
        ui.ButtonFrame(w.frame,optionlist=self.fieldtypes(),
                        command=self.setfieldtype,
                        window=w,
                        row=0,column=0)
    def exemplified(self,event=None):
        log.info("Giving example now")
        checktoadd=self.forms['name']
        if hasattr(self,'exf'):
            self.exf.destroy()
        self.exf=ui.Frame(self.content,row=2,column=0,sticky='w')
        if checktoadd in ['', None]:
            text=_('Sorry, empty name! \nPlease provide at least \na frame '
                'name, to distinguish it \nfrom other frames.')
            log.error(rx.delinebreak(text))
            l1=ui.Label(self.exf,
                        text=text,
                        font='read',
                        justify=ui.LEFT,anchor='w',
                        row=0,column=0,
                        sticky='w')
            return
        #don't give exs w/o all glosses
        """Define the new frame"""
        checkdefntoadd={'field':self.forms['field']}
        log.info("Ready to add frame with this form info: {}".format(self.forms))
        # log.info("Ready to add frame with this lookingfor info: {}".format(self.lookingfor))
        for lang in [i for i in self.forms #self.lookingfor
                            if 'before' in self.forms[i]
                            if 'after' in self.forms[i]
                ]: #just the defined languages
            before=self.forms[lang]['before']
            after=self.forms[lang]['after']
            checkdefntoadd[lang]=str(before+'__'+after)
        formdict=self.gimmesenseformdictwftypengloss(checkdefntoadd)
        #This should only pull from current ps
        # log.info('formdict result: {}'.format(formdict))
        padx=50
        pady=10
        row=0
        text=_("Examples for {} {} tone frame").format(checktoadd,
                                                        self.fieldtypename())
        lt=ui.Label(self.exf,
                text=text,
                font='readbig',
                justify=ui.LEFT,anchor='w',
                row=row,column=0,
                sticky='w',#columnspan=2,
                padx=padx,pady=pady)
        if not formdict:
            l1=ui.Label(self.exf,
                    text=_("None!"),
                    font='read',
                    justify=ui.LEFT,anchor='w',
                    row=row,column=0,
                    sticky='w',
                    padx=padx,pady=pady)
            return
        for lang,forms in formdict.items():
            row+=1
            text=('[{}]: {}'.format(lang,forms))#framed.forms.framed[lang]))
            l1=ui.Label(self.exf,
                    text=text,
                    font='read',
                    justify=ui.LEFT,anchor='w',
                    row=row,column=0,
                    sticky='w',
                    padx=padx,pady=pady)
            log.info('langlabel:{}'.format(text))
        """toneframes={'Nom':
                        {'name/location (e.g.,"By itself")':
                            {'analang.xyz': '__',
                            'glosslang.xyz': 'a __'},
                            'glosslang2.xyz': 'un __'},
                    }   }
        """
        row+=1
        stext=_('Use {} tone frame'.format(checktoadd))
        subframe=ui.Frame(self.exf,row=row,column=0,sticky='w')
        sub_btn=ui.Button(subframe,text = stext,
                          command = lambda x=checkdefntoadd,
                                            n=checktoadd: self.submit(x,n),
                          row=0,column=0,
                          )
        ui.Label(subframe, text=_("<= No changes after this! \nPlease check that "
                                "the above looks good on several examples!"),
                                justify='left', row=0, column=1, padx=15)
        # log.info('sub_btn:{}'.format(stext))
        sub_btn.update_idletasks()
    def promptstrings(self,lang=None,context=None):
        #None of this changes in editing. Is that what we want?
        if lang:
            lname=program['settings'].languagenames[self.stripftypecode(lang)]
            text=_("Fill in the {} frame forms below.\n(include a "
                "space to separate word forms)"
                ).format(lname)
            if lang != self.stripftypecode(lang): #i.e., analang
                kind=_('form')
                ok=_('Use this form')
            else:
                kind=_('gloss')
                ok=_('Use this {} form {} the dictionary gloss'.format(lname,
                                _(context)))
                self.glosslangs.append(lang)
            if context == 'before':
                text+='\n'+_("What text goes *before* \n<==the {} word *{}* "
                        "\nin the frame?").format(lname,kind)
            elif context == 'after':
                text+='\n'+_("What text goes *after* \nthe {} word *{}*==> "
                        "\nin the frame?").format(lname,kind)
        else:
            text=_("What do you want to call this new {} tone frame for {}?"
                    ).format(self.ps,
                            program['settings'].languagenames[self.analang])
            ok=_("Use this name")
        return {'lang':lang, 'prompt':text, 'ok':ok}
    def promptwindow(self,lang=None,context=None,event=None):
        def submitform(event=None):
            log.info("context: {}; lang: {}".format(context,lang))
            log.info("Form: {}".format(self.forms))
            clearNull()
            if lang and context:
                log.info("Form.get: {}".format(v.get()))
                log.info("type: {}".format(type(v)))
                log.info("value: {}".format(v.__dict__))
                self.forms[lang][context]=v.get()
            else:
                log.info("name.get: {}".format(v.get()))
                self.forms['name']=v.get()
            log.info("Forms: {}".format(self.forms))
            self.w.on_quit()
            self.status()
        def clearNull(event=None):
            if v.get() == null:
                v.set('')
        def setNull(event=None):
            if v.get() == '':
                v.set(null)
        log.info("context: {}; lang: {}".format(context,lang))
        strings=self.promptstrings(lang,context)
        self.w=ui.Window(self,
                        row=1,column=0,
                        sticky='ew',
                        padx=25,pady=25)
        if lang and context:
            self.w.title("{} {}".format(context,lang))
        else:
            self.w.title("New {} Tone frame for {}: Name the Frame".format(
                        self.ps,program['settings'].languagenames[self.analang]))
        self.withdraw() #Don't show status when asking for a value
        getform=ui.Label(self.w.frame,text=strings['prompt'],
                        font='read',row=0,column=0,
                        wraplength=program['root'].wraplength/2,
                        padx=self.padx,
                        pady=self.pady)
        #field rendering is better in another frame, with no sticky!:
        eff=ui.Frame(self.w.frame,row=1,column=0,sticky='')
        null=initval='<no content>'
        if lang and context:
            try:
                initval=self.forms[lang][context]
                v=ui.StringVar(self,initval)
            except KeyError:
                v=ui.StringVar(self,initval)
                try:
                    self.forms[lang][context]=v
                except KeyError:
                    self.forms[lang]={context:v} #because this isn't there yet
        else:
            try:
                initval=self.forms['name']
                v=ui.StringVar(self,initval)
            except KeyError:
                v=self.forms['name']=ui.StringVar(self,initval)
        formfield = ui.EntryField(eff, render=True,
                                textvariable=v,
                                row=1,column=0,
                                sticky='')
        formfield.focus_set()
        formfield.bind('<Return>',submitform)
        formfield.bind('<FocusIn>',clearNull)
        formfield.bind('<FocusOut>',setNull)
        formfield.rendered.grid(row=2,column=0,sticky='new')
        sub_btn=ui.Button(self.w.frame,text = strings['ok'],
                            command = submitform,
                            anchor ='c',row=2,column=0,sticky='')
        sub_btn.wait_window(formfield) #then move to next step
        if not self.exitFlag.istrue():
            self.deiconify()
    def submit(self,checkdefntoadd,checktoadd,event=None):
        log.info("Submitting {} frame with these values: {}".format(
                                                checktoadd,checkdefntoadd
                                                ))
        # Having made and unset these, we now reset and write them to file.
        program['toneframes'].addframe(self.ps,checktoadd,checkdefntoadd)
        program['status'].renewchecks() #renew (not update), because of new frame
        # log.info("object: {}".format(program['toneframes']))
        program['settings'].storesettingsfile(setting='toneframes')
        program['settings'].setcheck(checktoadd) #assume we will use this now
        self.task.deiconify()
        self.destroy()
    def gimmesense(self,sense=None,next=False,**kwargs):
        sensesbyps=program['db'].sensesbyps[self.ps]
        if next and sense:
            # log.info("trying {} sense {}/{}".format(self.ps,
            #                                     sensesbyps.index(sense)+1,
            #                                     len(sensesbyps)))
            try:
                return sensesbyps[sensesbyps.index(sense)+1]
            except IndexError:
                return sensesbyps[0]
        else:
            sense=sensesbyps[randint(0, len(sensesbyps)-1)]
            # log.info("returning random {} sense {}".format(self.ps,sense.id))
            return sense
    def gimmesenseformdictwftypengloss(self,framedef,**kwargs):
        tried=0
        langs=[i for i in framedef if i not in ['name','field']]
        glosslangs=[i for i in langs if i == self.stripftypecode(i)]
        # log.info("checking for these langs: {}".format(langs))
        # log.info("checking for this frame: {}".format(framedef))
        ftype=framedef['field']
        while not tried or None in f.values():
            f={lang:None for lang in langs} #start each with a clean slate
            if tried > program['db'].nsenseids*1.5: #give up looking randomly
                sense=self.gimmesense(sense,next=True)
            else:
                sense=self.gimmesense()
            f.update(sense.formatteddictbylang(self.analang, #This is xyz_ftype
                                        glosslangs,
                                        # program['settings'].glosslangs,
                                        frame=framedef
                                            ))
            # log.info("Analang form found: {}".format(f[self.analang]))
            tried+=1
            log.info("Values found: {}".format(f))
            if tried> program['db'].nsenseids*3.5:
                errortext=_("I've tried (randomly, then through each) {} "
                "times, and not found one "
                "of your {} senses with data in each of these languages: "
                "{}. \nAre you asking for gloss "
                "languages which actually have data in your database? \nOr, are "
                "you missing gloss fields (i.e., you have only 'definition' "
                "fields)?").format(tried,program['db'].nsenseids,langs)
                log.error(errortext)
                return #errortext
        log.debug("Found entry {} with glosses {}".format(sense.id,f))
        return f
    def __init__(self,parent):
        ui.Window.__init__(self,parent)
        parent.withdraw()
        self.task=parent #this should always be called by a window task
        self.analang=parent.analang
        self.ps=program['slices'].ps()
        self.forms={}
        # we want to start this net wide, to cover future usage
        # At some point, I may want to distinguish the analang from its gloss
        # in the same language code. They have different values in LIFT, and
        # there might be reason to distinguish them in the frame definitions.
        # But until I figure out how i want to do that, each language should
        # just appear once.
        self.glosslangs=list()
        self.padx=50
        self.pady=10
        title=_("Define a New {} Tone Frame for {}").format(self.ps,
                        program['settings'].languagenames[self.analang])
        self.title(title)
        t=(_("Add {} Tone Frame for {}").format(self.ps,
                        program['settings'].languagenames[self.analang]))#+'\n'?
        ui.Label(self.frame,text=t,font='title',row=0,column=0)
        self.scroll=ui.ScrollingFrame(self.frame,row=1,column=0)
        self.content=self.scroll.content
        self.status()
class Tone(object):
    """This keeps stuff used for Tone checks."""
    def makeanalysis(self,**kwargs):
        """was, now iterable, for multiple reports at a time:"""
        if not hasattr(self,'analysis'):
            self.analysis=Analysis(**kwargs)
        else:
            self.analysis.setslice(**kwargs)
    def checkforsenseidstosort(self,cvt=None,ps=None,profile=None,check=None):
        """This method just asks if any senseid in the given slice is unsorted.
        It stops when it finds the first one."""
        """use if sorting senseid lists aren't needed"""
        """This is redundant with updatesortingstatus()"""
        if cvt is None:
            cvt=program['slices'].cvt()
        if ps is None:
            ps=program['slices'].ps()
        if profile is None:
            profile=program['slices'].profile()
        if check is None:
            check=program['slices'].check()
        senseids=program['slices'].senseids(ps=ps,profile=profile)
        vts=False
        for senseid in senseids:
            v=unlist(program['db'].get("example/tonefield/form/text", senseid=senseid,
                                                    location=check).get('text'))
            if v not in ['',None]:
                vts=True
                break
        program['status'].dictcheck(cvt=cvt,ps=ps,profile=profile,check=check)
        program['status'].tosort(vts,cvt=cvt,ps=ps,profile=profile,check=check) #set
    def settonevariablesiterable(self,cvt='T',ps=None,profile=None,check=None):
        """This is currently called in iteration, but doesn't refresh groups,
        so it probably isn't useful anymore."""
        self.checkforsenseidstosort(cvt=cvt,ps=ps,profile=profile,check=check)
    def settonevariables(self):
        """This is currently called before sorting. This is a waste, if you're
        not going to sort afterwards –unless you need the groups."""
        self.updatesortingstatus() #this gets groups, too
    def addframe(self,**kwargs):
        if 'window' in kwargs:
            kwargs['window'].destroy() #in any case; if fails, try again.
        ToneFrameDrafter(self)
    def aframe(self):
        self.runwindow.destroy()
        self.addframe()
        self.addwindow.wait_window(self.addwindow)
        self.runcheck()
    def presortgroups(self):
        #simpler than calling and uncalling..…
        pass
    def updateformtoannotations(self,*args,**kwargs):
        #simpler than calling and uncalling..…
        pass
    def setsensegroup(self,sense,ftype,check,group,**kwargs):
        """here kwargs should include framed, if you want this to update the
        form information in the example"""
        # log.info("Setting tone sort group")
        if not ftype:
            log.error("No field type!")
            return
        try:
            """Fine if check isn't there; will be caught with exception"""
            f=sense.formattedform(self.analang,ftype,
                                program['toneframes'][self.ps][check])
            log.info("Setting form to {}".format(f))
            sense.examples[check].textvaluebylang(
                                    lang=self.analang,
                                    value=f)
            log.info("Setting tone sort group to ‘{}’".format(group))
            sense.examples[check].tonevalue(group)
            for g in (set(self.glosslangs)& #selected
                        set(program['toneframes'][self.ps][check])& #defined
                        set(sense.ftypes[ftype])): # form in lexicon
                for f in sense.formattedgloss(g,
                                        program['toneframes'][self.ps][check])[:1]:
                    log.info("Setting {} translation to {}".format(g,f))
                    sense.examples[check].translationvalue(g,f)
            sense.examples[check].lastAZTsort()
        except KeyError:
            sense.newexample(check,
                            program['toneframes'][self.ps][check],
                            self.analang,
                            self.glosslangs,
                            group)
        # log.info("Done setting tone sort group")
    def getsensesinUFgroup(self,group):
        return [
                i for i in program['db'].senses
                if i.uftonevalue() == group
                ]
        # return program['db'].get('sense',
        #                     toneUFvalue=group,
        #                     # path=['example'],
        #                     # showurl=True
        #                     ).get('senseid')
    def getsensesingroup(self,check,group):
        return [
                i for i in program['db'].senses
                if i.tonevaluebyframe(check) == group
                ]
        # return program['db'].get('sense',location=check,
        #                             tonevalue=group,
        #                             path=['example'],
        #                             showurl=True
        #                     ).get('senseid')
    def getsensegroup(self,sense,check):
        return sense.tonevaluebyframe(check)
    def getUFgroupofsense(self,sense):
        return sense.uftonevalue()
        # return program['db'].get("sense/field/form/text",
        #                     path=["toneUFfield"],
        #                     senseid=senseid,
        #                     # showurl=True
        #                     ).get('text')
    def __init__(self):
        pass
class Sort(object):
    """This class takes methods common to all sort checks, and gives sort
    checks a common identity."""
    def getsensesincheckgroup(self,**kwargs):
        check=kwargs.get('check',program['params'].check())
        group=kwargs.get('group',program['status'].group())
        return self.getsensesingroup(check, group)
    def modverification(self,sense,profile,ftype,check,add=None):
        values=sense.verificationtextvalue(profile,ftype)
        if add and not values:
            sense.verificationtextvalue(profile,ftype,value=add)
        elif values:
            for code in values[:]:
                if add and check in code:
                    log.info("Removing {}".format(code))
                    values[values.index(code)]=add
                    add=None #only once
                elif check in code:
                    values.remove(code)
            sense.verificationtextvalue(profile,ftype,None, values) #default lang
    def updatestatuslift(self,verified=False,**kwargs):
        """This should be called only by update status, when there is an actual
        change in status to write to file."""
        check=kwargs.get('check',program['params'].check())
        group=kwargs.get('group',program['status'].group())
        profile=kwargs.get('profile',program['slices'].profile())
        ftype=kwargs.get('ftype',program['params'].ftype())
        # profile=program['slices'].profile()
        senses=self.getsensesincheckgroup()
        value=self.verifictioncode(check=check,group=group)
        # The above gives a check=group string, which should be escaped later
        if verified == True:
            add=value
            rms=[]
        else:
            add=None
            rms=[value]
        log.info("Modding {} verification add {}, remove {}".format(profile,
                                                                    add,rms))
        """The above doesn't test for profile, so we restrict that next"""
        for senseid in program['slices'].inslice(senseids): #only for this ps-profile
            sense=program['db'].sensedict[senseid]
            self.modverification(sense,profile,ftype,check,add)
        if kwargs.get('write'):
            self.maybewrite() #for when not iterated over, or on last repeat
    def updatestatus(self,verified=False,**kwargs):
        #This function updates the status variable, not the lift file.
        group=kwargs.get('group',program['status'].group())
        write=kwargs.get('write')
        wstatus=kwargs.get('writestatus')
        r=program['status'].update(group=group,verified=verified,writestatus=wstatus)
        if r: #only do this if there is a change in status
            self.updatestatuslift(group=group,verified=verified,write=write)
            return r
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
            program['settings'].set('profile',newprofile,refresh=False)
            #Add to dictionaries before updating them below
            log.debug("profile: {}".format(newprofile))
            """Fix this!"""
            program['slices'].adhoc(ids,profile=newprofile)#[ps][profile]=ids
            program['settings'].storesettingsfile(setting='adhocgroups')#since we changed this.
            """Is this OK?!?"""
            program['slices'].updateslices() #This pulls from profilesbysense
            # self.makecountssorted() #we need these to show up in the counts.
            #so we don't have to do this again after each profile analysis
        self.getrunwindow()
        profile=program['slices'].profile()
        ps=program['slices'].ps()
        if profile in [x[0] for x in program['slices'].profiles()]: #profilecountsValid]:
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
        allpssensids=program['slices'].senseidsbyps(ps)
        if len(allpssensids)>70:
            self.runwindow.waitdone()
            text=_("This is a large group ({})! Are you in the right "
                    "lexical category?".format(len(allpssensids)))
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
                "senses to sort, within the '{0}' lexical category. \nYou "
                "should only do this if the '{0}' lexical category is so "
                "small that sorting them by syllable profile gives you "
                "unusably small slices of your database."
                "\nIf you want to compare words that are currently in "
                "different grammatical categories, put them first into the "
                "same lexical category in another tool (e.g., FLEx or "
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
        for senseid in allpssensids:
            log.debug("id: {}; index: {}; row: {}".format(senseid,
                                                    allpssensids.index(senseid),
                                                    row))
            idn=allpssensids.index(senseid)
            vars.append(ui.StringVar())
            adhocslices=program['slices'].adhoc()
            if (ps in adhocslices and profile in adhocslices[ps] and
                                        senseid in adhocslices[ps][profile]):
                vars[idn].set(senseid)
            else:
                vars[idn].set(0)
            forms=sense.formatted()
            log.debug("forms: {}".format(forms))
            ui.CheckButton(scroll.content, text = forms,
                                variable = vars[allpssensids.index(senseid)],
                                onvalue = id, offvalue = 0,
                                ).grid(row=row,column=0,sticky='ew')
            row+=1
        scroll.grid(row=3,column=0,sticky='ew')
        self.runwindow.waitdone()
        self.runwindow.wait_window(scroll)
    def removesensefromgroup(self,sense,**kwargs):
        check=kwargs.get('check',program['params'].check())
        group=kwargs.get('group',program['status'].group())
        ftype=kwargs.get('ftype',program['params'].ftype())
        write=kwargs.pop('write',True) #avoid duplicate
        sorting=kwargs.get('sorting',True) #Default to verify button
        log.info(_("Removing senseid {} from subcheck {}".format(sense.id,group)))
        #This should only *mod* if already there
        self.setsensegroup(sense,ftype,check,'',**kwargs)
        tgroups=self.getsensegroup(sense,check)
        log.info("Checking that removal worked")
        if tgroups in [[],'',[''],None]:
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
        profile=kwargs.get('profile',program['slices'].profile())
        sense.rmverificationvalue(profile,ftype,rm)
        program['status'].last('sort',update=True)
        if write:
            self.maybewrite()
        if sorting:
            program['status'].marksenseidtosort(sense.id)
    def ncheck(self):
        r=program['status'].nextcheck(tosort=True)
        if not r:
            program['status'].nextcheck(toverify=True)
        #if neither, this should call nprofile
        try:
            self.runwindow.destroy()
        except AttributeError:
            log.info("Looks like we wanted to kill a non-existent runwindow.")
        self.runcheck()
    def nprofile(self):
        r=program['status'].nextprofile(tosort=True)
        if not r:
            program['status'].nextprofile(toverify=True)
        #if neither, this should give up with a congrats and comment to pick another ps
        try:
            self.runwindow.destroy()
        except AttributeError:
            log.info("Looks like we wanted to kill a non-existent runwindow.")
        self.runcheck()
    def nps(self):
        program['slices'].nextps()
        r=program['status'].nextprofile(tosort=True)
        if not r:
            program['status'].nextprofile(toverify=True)
        try:
            self.runwindow.destroy()
        except AttributeError:
            log.info("Looks like we wanted to kill a non-existent runwindow.")
        self.runcheck()
    def runcheck(self):
        program['settings'].storesettingsfile()
        # t=(_('Run Check'))
        log.info("Running check...")
        cvt=program['params'].cvt()
        check=program['params'].check()
        profile=program['slices'].profile()
        if not profile:
            self.getprofile()
        """further specify check check in maybesort, where you can send the user
        on to the next setting"""
        if (check not in program['status'].checks() #tosort=True
                # and check not in program['status'].checks(toverify=True)
                # and check not in program['status'].checks(tojoin=True)
                ):
            exit=self.getcheck()
            if exit and not self.exitFlag.istrue():
                return #if the user didn't supply a check
        self.presortgroups()
        program['settings'].updatesortingstatus() # Not just tone anymore
        self.resetsortbutton() #track what is done since each button press.
        self.maybesort()
    def marksortgroup(self,sense,group,**kwargs):
        # group=kwargs.get('group',program['status'].group())
        # framed=kwargs.get('framed',None)
        check=kwargs.get('check',program['params'].check())
        profile=kwargs.get('profile',program['slices'].profile())
        ftype=kwargs.get('ftype',program['params'].ftype())
        nocheck=kwargs.get('nocheck',False)
        guid=None
        if kwargs.get('updateverification'):
            """This does the one field storing a list of verified values
            for all checks"""
            oldgroup=self.getsensegroup(sense,check) #Segment or Tone
            vals=sense.verificationtextvalue(profile,ftype)
            if vals:
                curvervaluecodes=[i for i in vals if check in vals]
            else:
                curvervaluecodes=[]
            if len(set(curvervaluecodes)) >1:
                log.error("Too many values for verification node! ({})"
                            "".format(curvervaluecodes))
            firstcode=firstoflist(curvervaluecodes)
            if firstcode:
                curvervalue=firstcode.split('=')[-1] #last, if multiple
            else:
                curvervalue=None
            if curvervalue == oldgroup: #only update if starting the same
                add=self.verifictioncode(check=check,group=group)
                self.modverification(sense,profile,ftype,check,add)
            elif not curvervalue:
                log.error("Problem updating verification to {}; current value "
                            "not there (should be {})".format(group, oldgroup))
            else: #not sure what to do here; maybe should throw bigger error?
                log.error("Problem updating verification to {}; current value "
                            "({}) is there, but not the same as current sort "
                            "group ({})."
                            "".format(group, curvervalue, oldgroup))
        log.debug("Adding {} value for {} check, "
                "senseid: {} guid: {} (in main_lift.py)".format(
                    group,
                    check,
                    sense.id,
                    guid))
        self.setsensegroup(sense,ftype,check,group)
        if not nocheck:
            newgroup=unlist(self.getsensegroup(sense,check))
            if newgroup != group:
                log.error("Field addition failed! LIFT says {}, not {}.".format(
                                                    newgroup,group))
            else:
                log.info("Field addition succeeded! LIFT says {}, which is {}."
                                        "".format(newgroup,group))
        if kwargs.get('updateforms'):
            self.updateformtoannotations(sense,ftype,check=check)
        program['status'].last('sort',update=True) #this will always be a change
        program['status'].tojoin(True)
        self.updatestatus(group=group,writestatus=True) # write just this once
        if kwargs.get('write'):
            self.maybewrite() #This is never iterated over; just one entry at a time.
        if not nocheck:
            return newgroup
    def notdonewarning(self):
        self.getrunwindow(nowait=True)
        buttontxt=_("Sort!")
        text=_("Hey, you're not done with {} {} words by {}!"
                "\nCome back when you have time; restart where you left "
                "off by pressing ‘{}’".format(self.ps,self.profile,self.check,
                                                buttontxt))
        ui.Label(self.runwindow.frame, text=text).grid(row=0,column=0)
    def resetsortbutton(self):
        # This attribute/fn is used to track whether something has been done
        # since the user last asked for a sort. We don't want the user in an
        # endless line of work (especially if the task at hand is to do a number
        # of tasks in one profile), but on the other hand, if the selected
        # profile is already done when the sort button is pressed, assume the
        # user wants the next profile.
        self.did={'sort':False,
                    'verify': False,
                    'join': False}
    def maybesort(self):
        """This should look for one group to verify at a time, with sorting
        in between, then join and repeat"""
        def tosortupdate():
            log.info("maybesort tosortbool:{}; tosort:{}; sorted:{}".format(
                                program['status'].tosort(),
                                program['status'].senseidstosort(),
                                program['status'].senseidssorted()
                                ))
        def exitstatuses():
            try:
                log.info("Self exit status: {}".format(self.exitFlag.istrue()))
                log.info("Parent exit status: {}".format(self.parent.exitFlag.istrue()))
                log.info("Runwindow exit status: {}".format(self.runwindow.exitFlag.istrue()))
                log.info("Taskchooser exit status: {}".format(program['taskchooser'].exitFlag.istrue()))
            except Exception as e:
                log.info("Exception: {}".format(e))
        def warnorcontinue(): #mostly for testing
            if self.exitFlag.istrue():
                pass #just return, below, if the task is exited
            elif self.runwindow.exitFlag.istrue():
                self.notdonewarning() #warn if runwindow exited, but not task
            else:
                self.maybesort() #if neither exited, continue
        # exitstatuses()
        if self.exitFlag.istrue(): #if the task has been shut down, stop
            return
        cvt=program['params'].cvt()
        self.check=program['params'].check()
        self.ps=program['slices'].ps()
        self.profile=program['slices'].profile()
        log.info("cvt:{}; ps:{}; profile:{}; check:{}".format(cvt,self.ps,
                                                    self.profile,self.check))
        tosortupdate()
        log.info("Maybe Sort (from maybesort)")
        if program['status'].checktosort(): # w/o parameters, tests current check
            log.info("Sort (from maybesort)")
            self.sort()
            self.did['sort']=True
            # exitstatuses()
            warnorcontinue()
            return
        log.info("Going to verify the first of these groups now: {}".format(
                                    program['status'].groups(toverify=True)))
        log.info("Maybe verify (from maybesort)")
        groupstoverify=program['status'].groups(toverify=True)
        if groupstoverify:
            if program['status'].group() not in groupstoverify:
                program['status'].group(groupstoverify[0]) #just pick the first now
            log.info("verify (from maybesort)")
            self.verify()
            self.did['verify']=True
            # exitstatuses()
            warnorcontinue()
            return
        if program['status'].tojoin():
            log.info("join (from maybesort)")
            self.join()
            self.did['join']=True
            # exitstatuses()
            warnorcontinue()
            return
        # exitstatuses()
        # At this point, there should be nothing to sort, verify or join, so we
        # move on to the next group.
        ctosort=program['status'].checks(tosort=True)
        ctoverify=program['status'].checks(toverify=True)
        ptosort=program['status'].profiles(tosort=True)
        ptoverify=program['status'].profiles(toverify=True)
        # log.info("ctosort: {},ctoverify: {},ptosort: {},ptoverify: {}"
        #         "".format(ctosort,ctoverify,ptosort,ptoverify))
        if ctosort or ctoverify:
            next=_("check")
            fn=self.ncheck
        elif (ptosort or ptoverify) and True not in self.did.values():
            # If there is a profile to do, but you havent done anything since
            # the last 'sort!' button press, then move on to the next profile.
            next=_("profile")
            fn=self.nprofile
        else:
            fn=None
        done=_("All ‘{}’ groups in the ‘{}’ {} are verified and "
                "distinct!").format(
                                    self.profile,self.check,
                                    self.checktypename[cvt])
                #only on first two ifs:
        if fn:
            done+='\n'+_("Moving on to the next {}!".format(next))
        ErrorNotice(text=done,title=_("Done!")) #all
        if fn:
            fn() #only on first two ifs
    def presenttosort(self):
        scaledpady=int(50*program['scale'])
        groupselected=None
        """these just pull the current lists from the object"""
        senseids=program['status'].senseidstosort()
        sorted=program['status'].senseidssorted()
        try:
            sense=program['db'].sensedict[senseids[0]]
        except IndexError:
            log.info("maybe ran out of senseids?")
            return
        progress=(str(self.thissort.index(sense.id)+1)+'/'+str(len(self.thissort)))
        """After the first entry, sort by groups."""
        # log.debug('groups: {}'.format(program['status'].groups(wsorted=True)))
        if self.runwindow.exitFlag.istrue():
            return #1,1
        ui.Label(self.titles, text=progress, font='report', anchor='w'
                                        ).grid(column=1, row=0, sticky="ew")
        if self.cvt == 'T' and self.check not in program['toneframes'][self.ps]:
            text=_("Looking for tone check ‘{}’, but not in {} frames: {}"
                        "").format(self.check,self.ps,program['toneframes'][self.ps])
            log.error(text)
        else:
            text=sense.formatted(self.analang,self.glosslangs,
                            program['params'].ftype(),
                            program['toneframes'][self.ps].get(self.check))
        entryview=ui.Frame(self.runwindow.frame, column=1, row=1, sticky="new")
        self.sortitem=self.buttonframe.sortitem=ui.Label(entryview,
                                text=text,font='readbig',
                                column=0,row=0, sticky="w",
                                pady=scaledpady
                                )
        self.sortitem['image']=sense.illustrationvalue()
        self.sortitem['compound']="left"
        self.sortitem.wrap()
        self.runwindow.waitdone()
        for b in self.buttonframe.groupbuttonlist:
            b.setcanary(self.sortitem)
        self.runwindow.wait_window(window=self.sortitem)
        if not self.runwindow.exitFlag.istrue():
            return sense#.id,framed #where to from here?
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
        self.thissort=program['status'].senseidstosort()[:] #current list
        log.info("Going to sort these senseids: {}"
                "".format(program['status'].senseidstosort()))
        groups=program['status'].groups(wsorted=True)
        log.info("Current groups: {}".format(groups))
        """Children of runwindow.frame"""
        if self.exitFlag.istrue():
            return
        self.titles=ui.Frame(self.runwindow.frame, row=0, column=1,
                                                    sticky="ew", columnspan=1)
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
            context=program['params'].cvcheckname(self.check)
            descripttext=("by {}").format(self.check)
        title=_("Sort {} {} ({})").format(
                                        program['settings'].languagenames[self.analang],
                                        context,
                                        descripttext)
        ui.Label(self.titles, text=title,font='title',anchor='c',
                                            column=0, row=0, sticky="ew")
        instructions=_("Select the one with the same {} as").format(context)
        ui.Label(self.titles, text=instructions, font='instructions',
                anchor='c', column=0, row=1, sticky="ew")
        """Stuff that changes by lexical entry
        The second frame, for the other two buttons, which also scroll"""
        while (program['status'].tosort() and
                program['status'].senseidstosort() and
                not self.runwindow.exitFlag.istrue()):
            tosort=self.presenttosort()
            """thread here? No, this updates the UI, as well as writing data"""
            if not self.runwindow.exitFlag.istrue() and tosort:
                self.buttonframe.sortselected(tosort)
        if not self.runwindow.exitFlag.istrue():
            self.runwindow.resetframe()
    def reverify(self):
        group=program['status'].group()
        check=program['params'].check()
        log.info("Reverifying a framed tone group, at user request: {}-{}"
                    "".format(check,group))
        if check not in program['status'].checks(wsorted=True):
            self.getcheck() #guess=True
        done=program['status'].verified()
        if group not in done:
            log.info("Group ({}) not in groups ({}); asking."
                    "".format(group,done))
            w=self.getgroup(wsorted=True)
            w.wait_window(w)
            group=program['status'].group()
            if group not in done: #i.e., still
                log.info("I asked for a framed tone group, but didn't get one.")
                return
        done.remove(group)
        program['settings'].updatesortingstatus() # Not just tone anymore
        self.maybesort()
    def verify(self,menu=False):
        def updatestatus(v):
            log.info("Updating status with {}, {}, {}".format(check,group,v))
            self.updatestatus(verified=v,writestatus=True)
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
        check=program['params'].check()
        groups=program['status'].groups(toverify=True) #needed for progress
        group=program['status'].group()
        # The title for this page changes by group, below.
        self.getrunwindow(msg="preparing to verify {} group: {}".format(check,
                                                                        group))
        oktext='These all have the same {}'.format(program['params'].cvcheckname())
        instructions=_("Read down this list to verify they all have the same "
            "{0} sound. Click on any word with a different {0} sound to "
            "remove it from the list.").format(program['params'].cvcheckname())
        """group is set here, but probably OK"""
        program['status'].build()
        last=False
        if self.runwindow.exitFlag.istrue():
            return 1
        if group in program['status'].verified():
            log.info("‘{}’ already verified, continuing.".format(group))
            return
        senses=program['examples'].sensesinslicegroup(group,check)
        if not senses: #then remove the group
            groups=program['status'].groups(wsorted=True) #from which to remove, put back
            # log.info("Groups: {}".format(program['status'].groups(toverify=True)))
            verified=False
            log.info("Group ‘{}’ has no examples; continuing.".format(group))
            # log.info("Groups: {}".format(program['status'].groups(toverify=True)))
            updatestatus(False)
            log.info("Group-groups: {}-{}".format(group,groups))
            if group in groups:
                groups.remove(group)
            # log.info("Group-groups: {}-{}".format(group,groups))
            program['status'].groups(groups,wsorted=True)
            log.info("All groups: {}".format(program['status'].groups(wsorted=True)))
            log.info("Groups to verify: {}"
                        "".format(program['status'].groups(toverify=True)))
            return
        elif len(senses) == 1:
            log.info("Group ‘{}’ only has {} example; marking verified and "
                    "continuing.".format(group,len(senses)))
            updatestatus(True)
            return
        title=_("Verify {} Group ‘{}’ for ‘{}’ ({})").format(
                                    program['settings'].languagenames[self.analang],
                                    group,
                                    check,
                                    program['params'].cvcheckname()
                                    )
        titles=ui.Frame(self.runwindow.frame,
                        column=1, row=0, columnspan=1, sticky="w")
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
        i=ui.Label(titles, text=instructions,
                row=1, column=0, columnspan=2, sticky="wns")
        i.wrap()
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
        for sense in senses:
            if sense is None: #needed?
                continue
            self.verifybutton(self.sframe.content,sense,
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
        bf.grid(row=max(row+1,self.buttoncolumns+1), column=0, sticky="ew",
                        columnspan=self.buttoncolumns+1) #Keep on own row
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
        program['status'].last('verify',update=True)
        updatestatus(True)
    def verifybutton(self,parent,sense,row,column=0,label=False,**kwargs):
        """This should maybe take examples as input, rather than senses"""
        # This must run one subcheck at a time. If the subcheck changes,
        # it will fail.
        # should move to specify location and fieldvalue in button lambda
        def notok():
            self.removesensefromgroup(sense,sorting=True,write=False)
            self.maybewrite()
            bf.destroy()
        if 'font' not in kwargs:
            kwargs['font']='read'
        if 'anchor' not in kwargs:
            kwargs['anchor']='w'
        #This should be pulling from the example, as it is there already
        check=program['params'].check()
        text=sense.formatted(self.analang,self.glosslangs,
                            ftype=program['params'].ftype(),
                            frame=program['toneframes'][self.ps].get(check))
        if program['settings'].lowverticalspace:
            ipady=0
        else:
            ipady=15*program['scale']
        if label==True:
            b=ui.Label(parent, text=text,
                    column=column, row=row,
                    sticky="ew",
                    ipady=ipady,
                    **kwargs
                    )
        else:
            bf=ui.Frame(parent, pady='0') #This will be killed by removesenseidfromgroup
            bf.grid(column=column, row=row, sticky='ew')
            b=ui.Button(bf, text=text, pady='0',
                    cmd=notok,
                    column=column, row=0,
                    sticky="ew",
                    ipady=ipady, #Inside the buttons...
                    **kwargs
                    )
        b['image']=sense.illustrationvalue()
        b['compound']="left"
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
        cvt=program['params'].cvt()
        check=program['params'].check()
        ps=program['slices'].ps()
        profile=program['slices'].profile()
        groups=program['status'].groups(wsorted=True) #these should be verified, too.
        if len(groups) <2:
            log.debug("No tone groups to distinguish!")
            if not self.exitFlag.istrue():
                self.runwindow.waitdone()
            program['status'].tojoin(False)
            return 0
        title=_("Review Groups for {} Tone (in ‘{}’ frame)").format(
                                        program['settings'].languagenames[self.analang],
                                        check
                                        )
        oktext=_('These are all different')
        introtext=_("Congratulations! \nAll your {} with profile ‘{}’ are "
                "sorted into the groups exemplified below (in the ‘{}’ frame). "
                "Do any of these have the same {}? "
                "If so, click on two groups to join. "
                "If not, just click ‘{ok}’."
                ).format(ps,profile,check,program['params'].cvcheckname(),ok=oktext)
        log.debug(introtext)
        self.runwindow.resetframe()
        self.runwindow.frame.titles=ui.Frame(self.runwindow.frame,
                                            column=1, row=0,
                                            columnspan=1, sticky="ew"
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
            b[group]=SortGroupButtonFrame(self.sortitem, self, group,
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
            program['status'].tojoin(False)
            self.runwindow.destroy()
            return 0
        elif ngroupstojoin > 2:
            log.info("User selected ‘{}’ with {} groups selected, This is "
                    "probably a mistake ({} selected)."
                    "".format(oktext,ngroupstojoin,groupstojoin))
            return self.join() #try again
        else:
            log.info("User selected {} groups selected, joining "
                    "them. ({} selected)."
                    "".format(ngroupstojoin,groupstojoin))
            msg=_("Now we're going to move group ‘{0}’ into "
                "‘{1}’, marking ‘{1}’ unverified.".format(*groupstojoin))
            self.runwindow.wait(msg=msg)
            log.debug(msg)
            """All the senses we're looking at, by ps/profile"""
            # log.info("Join about to run updatebygroupsenseid(*groupstojoin)")
            self.updatebygroupsense(*groupstojoin)
            groups.remove(groupstojoin[0])
            write=False #for the first
            for group in groupstojoin: #not verified=True --since joined
                self.updatestatus(group=group,write=write)
                write=True #For second group
            self.maybesort() #go back to verify, etc.
        """'These are all different' doesn't need to be saved anywhere, as this
        can happen at any time. Just move on to verification, where each group's
        sameness will be verified and recorded."""
    def tryNAgain(self):
        check=program['params'].check()
        if check in program['status'].checks():
            senses=self.getsensesincheckgroup(group='NA')
            # program['slices'].senseids()
            # ftype=program['toneframes'][check]['field'] #this must match check!
        else:
            #Give an error window here
            log.error("Not Trying again; set a check first!")
            self.getrunwindow(nowait=True)
            buttontxt=_("Sort!")
            text=_("Not Trying Again; set a tone frame first!")
            ui.Label(self.runwindow.frame, text=text).grid(row=0,column=0)
            return
        for sense in senses: #this is a ps-profile slice
            self.removesensefromgroup(sense)
            # program['db'].addmodexamplefields(senseid=senseid,fieldtype='tone',
            #                 location=check,#ftype=ftype,
            #                 fieldvalue='', #just clear this
            #                 oldfieldvalue='NA', showurl=True #if this
            #                 )
        self.runcheck()
    def updatebygroupsense(self,oldvalue,newvalue,updateforms=False):
        """Generalize this for segments"""
        # This function updates the field value and verification status (which
        # contains the field value) in the lift file.
        # This is all the words in the database with the given
        # location:value correspondence (for a given ps/profile)
        check=program['params'].check()
        lst2=self.getsensesingroup(check,oldvalue) #by annotations, for C/V
        # We are agnostic of verification status of any given entry, so just
        # use this to change names, not to mark verification status (do that
        # with self.updatestatuslift())
        rm=self.verifictioncode(check=check,group=oldvalue)
        add=self.verifictioncode(check=check,group=newvalue)
        """The above doesn't test for profile, so we restrict that next"""
        profile=program['slices'].profile()
        senses=program['slices'].inslice(lst2)
        ftype=program['params'].ftype()
        if not senses:
            log.info("No senses for {}={}".format(check,oldvalue))
            return
        for sense in senses:
            """This updates the fieldvalue from 'fieldvalue' to
            'newfieldvalue'."""
            u = threading.Thread(target=self.marksortgroup,
                                args=(sense,newvalue),
                                kwargs={'check':check,
                                        'ftype':ftype,
                                        'nocheck': True, #don't verify from lift
                                        'updateverification':True,
                                        'updateforms':updateforms})
            # if updateforms:
            #     # self.updateformtoannotations(senseid,ftype,check)
            #     t = threading.Thread(target=self.updateformtoannotations,
            #                     args=(senseid,ftype),
            #                     kwargs={'check':check})
            # v = threading.Thread(target=program['db'].modverificationnode,
            #                     # args=(senseid,group),
            #                     kwargs={'senseid':senseid,
            #                             'vtype':profile,
            #                             'analang':self.analang,
            #                             'add':add,
            #                             'rms':[rm],
            #                             'addifrmd':True})
            # for i in [u,v]:
            #     i.start()
            u.start()
            # self.setsenseidgroup(senseid,ftype,check,newvalue)
            # self.updateformtoannotations(senseid,ftype,check)
            # program['db'].modverificationnode(senseid=senseid,
            #                 vtype=profile,
            #                 analang=self.analang,
            #                 add=add,rms=[rm],
            #                 addifrmd=True)
        # for i in [u,v]:
        #     i.join()
        u.join()
        if updateforms:
            #NO: this should update formstosearch and profile data.
            #?
            program['settings'].reloadstatusdatabycvtpsprofile()
        self.maybewrite() #once done iterating over senseids
    def __init__(self, parent):
        program['settings'].makeeverythingok()
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
        program['params'].ftype('lc') #current default
        self.cvt=program['params'].cvt()
        #for testing only!!
        # if program['settings'].pluralname:
        #     program['params'].ftype(program['settings'].pluralname)
        # if program['settings'].imperativename:
        # program['params'].ftype(self.imperativename)
        self.checktypename={'T':'frame',
                        'C':'check',
                        'V':'check',
                        'CV':'check',
                        }
        self.analang=program['params'].analang()
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
        window=ui.Window(self.soundsettingswindow,
                    title=_('Select Input Sound Card'))
        ui.Label(window.frame, text=_('What sound card do you '
                                    'want to record sound with with?')
                ).grid(column=0, row=0)
        l=list()
        for card in self.soundsettings.cards['in']:
            name=self.soundsettings.cards['dict'][card]
            l+=[(card, name)]
        buttonFrame1=ui.ScrollingButtonFrame(window.frame,
                                    optionlist=l,
                                    command=program['settings'].setsoundcardindex,
                                    window=window,
                                    column=0, row=1
                                    )
    def getsoundcardoutindex(self,event=None):
        log.info("Asking for output sound card...")
        window=ui.Window(self.soundsettingswindow,
                title=_('Select Output Sound Card'))
        ui.Label(window.frame, text=_('What sound card do you '
                                    'want to play sound with?')
                ).grid(column=0, row=0)
        l=list()
        for card in self.soundsettings.cards['out']:
            name=self.soundsettings.cards['dict'][card]
            l+=[(card, name)]
        buttonFrame1=ui.ScrollingButtonFrame(window.frame,
                                    optionlist=l,
                                    command=program['settings'].setsoundcardoutindex,
                                    window=window,
                                    column=0, row=1
                                    )
    def getsoundformat(self,event=None):
        log.info("Asking for audio format...")
        window=ui.Window(self.soundsettingswindow,
                        title=_('Select Audio Format'))
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
                                    command=program['settings'].setsoundformat,
                                    window=window,
                                    column=0, row=1
                                    )
    def getsoundhz(self,event=None):
        log.info("Asking for sampling frequency...")
        window=ui.Window(self.soundsettingswindow,
                        title=_('Select Sampling Frequency'))
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
                                    command=program['settings'].setsoundhz,
                                    window=window,
                                    column=0, row=1
                                    )
    def makesoundsettings(self):
        if not hasattr(program['settings'],'soundsettings'):
            self.pyaudiocheck() #in case self.pyaudio isn't there yet
            program['settings'].soundsettings=sound.SoundSettings(self.pyaudio)
    def loadsoundsettings(self):
        self.makesoundsettings()
        program['settings'].loadsettingsfile(setting='soundsettings')
        program['soundsettings']=program['settings'].soundsettings
    def soundcheckrefreshdone(self):
        program['settings'].storesettingsfile(setting='soundsettings')
        self.soundsettingswindow.destroy()
    def quittask(self):
        self.soundsettingswindow.destroy()
        program['taskchooser'].gettask()
        self.on_quit()
    def soundcheckrefresh(self,dict=None):
        self.soundsettings.makedefaultifnot()
        dictnow={
                'audio_card_in':self.soundsettings.audio_card_in,
                'fs':self.soundsettings.fs,
                'sample_format': self.soundsettings.sample_format,
                'audio_card_out': self.soundsettings.audio_card_out
                }
        """Call this just once. If nothing changed, wait; if changes, run,
        then run again."""
        if self.soundsettingswindow.exitFlag.istrue() or self.exitFlag.istrue():
            self.soundsettingswindow.on_quit()
            self.on_quit()
            return
        if dict == dictnow:
            program['settings'].setrefreshdelay()
            self.parent.after(program['settings'].refreshdelay,
                                self.soundcheckrefresh,
                                dictnow)
            return
        log.info("sound settings dict: {}".format(dict))
        self.soundsettingswindow.resetframe()
        self.soundsettingswindow.scroll=ui.ScrollingFrame(
                                                self.soundsettingswindow.frame,
                                                row=0,column=0)
        self.soundsettingswindow.content=self.soundsettingswindow.scroll.content
        row=0
        ui.Label(self.soundsettingswindow.content, font='title',
                text=_("Confirm Sound Card Settings"),
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
            l.bind('<ButtonRelease-1>',cmd) #getattr(self,str(cmd)))
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
        if not hasattr(program['settings'],'soundsettings'):
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
        program['settings'].soundsettingsok=True
    def mikecheck(self):
        #move this to Record, after confirming that can be safely done.
        self.pyaudiocheck()
        self.soundsettingswindow=ui.Window(self, exit=False,
                                title=_('Select Sound Card Settings'))
        self.soundsettingswindow.protocol("WM_DELETE_WINDOW", self.quittask)
        self.soundcheckrefresh()
        if not self.soundsettingswindow.exitFlag.istrue():
            self.soundsettingswindow.wait_window(self.soundsettingswindow)
        self.donewpyaudio()
        if not self.exitFlag.istrue() and self.soundsettingswindow.winfo_exists():
            self.soundsettingswindow.destroy()
    def soundcheck(self):
        #just make sure settings are there
        self.soundsettingscheck()
        self.soundsettings=program['settings'].soundsettings
        self.soundsettings.check()
        if not self.exitFlag.istrue() and self.missingsoundattr():
            self.mikecheck() #if not, get them
            return
    def audioexists(self,relfilename):
        return file.exists(self.audioURL(relfilename))
    def audioURL(self,relfilename):
        return str(file.getdiredurl(self.audiodir,relfilename))
    def hassoundfile(self,node,recheck=False):
        """sets self.audiofileisthere and maybe self.audiofileURL"""
        return node.hassoundfile(program['params'].audiolang(),
                                self.audiodir,recheck)
    def __init__(self):
        self.audiodir=program['settings'].audiodir
        self.audiolang=program['params'].audiolang()
        self.soundcheck()
class Record(Sound,TaskDressing):
    """This holds all the Sound methods specific for Recording."""
    def makelabelsnrecordingbuttons(self,parent,node,r,c):
        # log.info("Making buttons for {} (in {})".format(sense['nodetoshow'],sense))
        t=node.formatted(self.analang,self.glosslangs)
        lxl=ui.Label(parent, text=t)
        lcb=RecordButtonFrame(parent,self,node)
        lcb.grid(row=r,column=c,sticky='w')
        lxl.grid(row=r,column=c+1,sticky='w')
    def showentryformstorecordpage(self):
        #The info we're going for is stored above sense, hence guid.
        if self.runwindow.exitFlag.istrue():
            log.info('no runwindow; quitting!')
            return
        if not self.runwindow.frame.winfo_exists():
            log.info('no runwindow frame; quitting!')
            return
        self.runwindow.resetframe()
        ps=program['slices'].ps()
        profile=program['slices'].profile()
        count=program['slices'].count()
        text=_("Record {} {} Words: click ‘Record’, talk, "
                "and release ({} words)".format(profile,ps,
                                                count))
        log.info(text)
        instr=ui.Label(self.runwindow.frame, anchor='w',text=text)
        instr.grid(row=0,column=0,sticky='w')
        senseids=program['slices'].senseids(ps=ps,profile=profile)
        nperpage=10
        pages=[senseids[i:i+nperpage] for i in range(0,len(senseids),nperpage)]
        log.info("pages: {}".format(pages))
        for page in pages:
            if self.runwindow.exitFlag.istrue():
                return
            self.runwindow.wait()
            buttonframes=ui.ScrollingFrame(self.runwindow.frame,
                                            row=1,column=0,sticky='w')
            row=0
            done=list()
            for row,entry in enumerate([program['db'].sensedict[i].entry
                                            for i in page]):
                self.runwindow.column=0
                if entry.guid in done: #only the first of multiple senses
                    continue
                else:
                    done.append(entry.guid)
                """These following two have been shifted down a level, and will
                now return a list of form elements, each. Something will need to be
                adjusted here..."""
                ftypes=['lc','pl','imp']
                for node in [entry.sense.nodebyftype(f) for f in ftypes
                                if entry.sense.nodebyftype(f)]:
                    self.runwindow.column+=2
                    # sense['nodetoshow']=sense[node]
                    self.makelabelsnrecordingbuttons(buttonframes.content,node,
                        row,self.runwindow.column)
                # row+=1
            ui.Button(buttonframes.content,column=1,row=row,
                        text=_("Next {} words").format(nperpage),
                        cmd=buttonframes.destroy)
            self.runwindow.waitdone()
            buttonframes.wait_window(buttonframes)
        if not self.runwindow.exitFlag.istrue():
            self.runwindow.wait_window(self.runwindow.frame)
    def showentryformstorecord(self,justone=False):
        # Save these values before iterating over them
        #Convert to iterate over local variables
        self.getrunwindow()
        if justone:
            self.showentryformstorecordpage()
        else:
            #store for later
            ps=program['slices'].ps()
            prifile=program['slices'].profile()
            for psprofile in program['slices'].valid(): #self.profilecountsValid:
                if self.runwindow.exitFlag.istrue():
                    return 1
                program['slices'].ps(psprofile[1])
                program['slices'].profile(psprofile[0])
                nextb=ui.Button(self.runwindow,text=_("Next Group"),
                                        cmd=self.runwindow.resetframe) # .frame.destroy
                nextb.grid(row=0,column=1,sticky='ne')
                self.showentryformstorecordpage()
            #return to initial
            program['slices'].ps(ps)
            program['slices'].profile(profile)
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
        if (program['settings'].entriestoshow is None) and (senses is None):
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
            skipb.bind('<ButtonRelease-1>', setskip)
        if senses is None:
            senses=program['settings'].entriestoshow
        for sense in senses:
            log.debug("Working on {} with skip: {}".format(sense.id,
                                                    self.runwindow.frame.skip))
            examples=list(sense.examples.values())
            # program['db'].get('example',senseid=senseid).get()
            if examples == []:
                log.debug(_("No examples! Add some, then come back."))
                continue
            if ((self.runwindow.frame.skip == True) and
                (lift.atleastoneexamplehaslangformmissing(examples,
                                    program['settings'].audiolang) == False)):
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
            text=sense.formatted(self.analang,self.glosslangs)
            if not text:
                entryframe.destroy() #is this ever needed?
                continue
            ui.Label(entryframe, anchor='w', font='read',
                    text=text).grid(row=row,
                                    column=0,sticky='w')
            """Then get each sorted example"""
            self.runwindow.frame.scroll=ui.ScrollingFrame(entryframe)
            self.runwindow.frame.scroll.grid(row=1,column=0,sticky='w')
            examplesframe=ui.Frame(self.runwindow.frame.scroll.content)
            examplesframe.grid(row=0,column=0,sticky='w')
            # examples.reverse()
            for example in examples:
                if (skip == True and
                    lift.examplehaslangform(example,program['settings'].audiolang) == True):
                    continue
                # """These should already be framed!"""
                text=example.formatted(self.analang,self.glosslangs)
                if not text:
                    #Don't show the whole dictionary of frames here:
                    log.info("Not showing example with text {}".format(text))
                    continue
                row+=1
                """If I end up pulling from example nodes elsewhere, I should
                probably make this a function, like getframeddata"""
                if not text:
                    exit()
                rb=RecordButtonFrame(examplesframe,self,example)
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
            program['status'].nextprofile()
            self.runwindow.destroy()
            self.showtonegroupexs()
        if (not(hasattr(self,'examplespergrouptorecord')) or
            (type(self.examplespergrouptorecord) is not int)):
            self.examplespergrouptorecord=100
            program['settings'].storesettingsfile()
        self.makeanalysis()
        self.analysis.donoUFanalysis()
        torecord=self.analysis.senseidsbygroup
        ntorecord=len(torecord) #number of groups
        nexs=len([k for i in torecord for j in torecord[i] for k in j])
        nslice=program['slices'].count()
        log.info("Found {} analyzed of {} examples in slice".format(nexs,nslice))
        skip=False
        if ntorecord == 0:
            log.error(_("How did we get no UR tone groups? {}-{}"
                    "\nHave you run the tone report recently?"
                    "\nDoing that for you now...").format(
                            program['slices'].profile(),
                            program['slices'].ps()
                                                        ))
            self.analysis.do()
            self.showtonegroupexs()
            return
        batch={}
        for i in range(self.examplespergrouptorecord):
            batch[i]=[]
            for ufgroup in torecord:
                print(i,len(torecord[ufgroup]),ufgroup,torecord[ufgroup])
                if len(torecord[ufgroup]) > i: #no done piles.
                    sense=[program['db'].sensedict[torecord[ufgroup][i]]] #list of one
                else:
                    print("Not enough examples, moving on:",i,ufgroup)
                    continue
                log.info(_('Giving user the number {} example from tone '
                        'group {}'.format(i,ufgroup)))
                exited=self.showsenseswithexamplestorecord(sense,
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
    def filenameoptions(self,node):
        # This depends on self.analang and program['slices'].profile; otherwise, it
        # could be moved to a FieldParent method
        """This should generate possible filenames, with preferred (current
        schema) last, as that will be used if none are found."""
        ps=program['slices'].ps()
        pslocopts=[ps]
        # Except for data generated early in 2021, profile should not be there,
        # because it can change with analysis. But we include here to pick up
        # old files, in case they are there but not linked.
        # First option (legacy):
        # pslocopts.insert(0,ps+'_'+self.parent.taskchooser.slices.profile())
        pslocopts.insert(0,ps+'_'+program['slices'].profile())
        fieldlocopts=[None]
        try:
            l=node.locationvalue()
            #the last option is taken, if none are found
            pslocopts.insert(0,ps+'-'+l) #the first option.
            fieldlocopts.append(l) #make this the last option.
        except AttributeError:
            log.info("doesn't look like an example node; not offering location")
            pass
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
                        args=[node.sense.id]
                        if tags:
                            args+=[node.tag]
                            if node.tag == 'field':
                                args+=[node.ftype]
                        form=node.textvaluebylang(self.analang)
                        if not form:
                            log.error("No {} analang in {} (forms: {})".format(
                                                        self.analang,
                                                        node.sense.id,
                                                        node.textvaluedict()))
                            return
                        args+=[form] #[self.ftype]]
                        for l in self.glosslangs:
                            args+=[node.gloss(l)]
                        optargs=args[:]
                        optargs.insert(0,pslocopt) #put first
                        optargs.insert(3,fieldlocopt) #put after self.node.tag
                        # log.info("optargs: {}".format(optargs))
                        wavfilename='_'.join([x for x in optargs if x])
                        if legacy == '_': #There was a schema that had an extra '_'.
                            wavfilename+='_'
                        wavfilename=rx.urlok(wavfilename) #one character check
                        filenames+=[wavfilename+'.wav']
        return filenames
    def makeaudiofilename(self,node):
        """If node is already marked with woudn file attributes, we're done"""
        if self.hassoundfile(node):
            return
        """Otherwise, generate prioritized list of name options"""
        filenames=self.filenameoptions(node)
        """if any of the generated filenames are there, stop at the first one"""
        for f in filenames:
            if self.audioexists(f):
                log.info("Audiofile {} found at {}".format(f, self.audioURL(f)))
                node.textvaluebylang(lang=program['params'].audiolang,value=f)
                if self.hassoundfile(node,recheck=True):
                    log.info("file {} linked in LIFT".format(node.audiofileURL))
                break
        """If none found, be ready to write with last/highest priority option"""
        f=filenames[-1]
        log.debug("No audio file found, but ready to record: "
                    "{}; url:{}".format(f, self.audioURL(f)))
        """Should be able to just send f"""
        node.audiofilenametoput=f #don't write this until we actually record
        node.audiofileURL=self.audioURL(f)
    def __init__(self,parent):
        TaskDressing.__init__(self,parent)
        Sound.__init__(self)
        self.mikecheck() #only ask for settings check if recording
class Report(object):
    def consultantcheck(self):
        program['settings'].reloadstatusdata()
        self.bylocation=False
        self.tonegroupreportcomprehensive()
        self.bylocation=True
        self.tonegroupreportcomprehensive()
    def tonegroupreportcomprehensive(self,**kwargs):
        """Should set this to do all analyses upfront, then run all in the
        background"""
        kwargs['psprofiles']=self.psprofilestodo()
        kwargs['xlpr']=self.xlpstart(reporttype='MultisliceTone',**kwargs)
        log.info("Starting comprehensive reports for {}".format(
                                                        kwargs['psprofiles']))
        kwargs['usegui']=False
        for kwargs['ps'] in kwargs['psprofiles']:
            for kwargs['profile'] in kwargs['psprofiles'][kwargs['ps']]:
                # self.tonegroupreport(**kwargs) #ps=ps,profile=profile)
                self.tonegroupreport(**kwargs) #ps=ps,profile=profile)
            """Not working:"""
            # with multiprocessing.Pool(processes=4) as pool:
            #     pool.map(self.tonegroupreport,[
            #             {'ps':ps,'profile':p,'usegui':False} for p in d[ps]])
        kwargs['xlpr'].close(me=me)
    def reportmulti(self,**kwargs):
        """This backgrounds multiple reports at a time, not multiple sections
        in one report"""
        # threading.Thread(target=self.tonegroupreport,kwargs=kwargs).start()
        start_time=nowruntime()
        log.info("reportmulti starting with fn {} and kwargs {} ".format(
                    self.reportfn.__name__,kwargs))
        kwargs['usegui']=False
        # log.info("reportmulti continuing with kwargs {}".format(kwargs))
        if hasattr(program['settings'],'maxpss') and program['settings'].maxpss:
            pss=program['slices'].pss()[:program['settings'].maxpss]
        else:
            pss=[program['slices'].ps()]
        d={}
        for ps in pss:
            if (hasattr(program['settings'],'maxprofiles') and
                    program['settings'].maxprofiles):
                d[ps]=program['slices'].profiles(ps=ps)[:program['settings'].maxprofiles]
            else:
                d[ps]=[program['slices'].profile()]
        log.info("Starting background reports for {}".format(d))
        unbackground=[]
        all=[]
        for kwargs['ps'] in pss:
            for kwargs['profile'] in d[kwargs['ps']]:
                # kwargs['ps']=ps
                # kwargs['profile']=profile
                # log.info("reportmulti background with kwargs {}".format(kwargs))
                t=multiprocessing.Process(target=self.reportfn,
                                            kwargs=kwargs)
                t.start()
                log.info(_("Starting XLP background report with kwargs {}"
                            ).format(kwargs))
                all+=[kwargs.copy()]
                time.sleep(0.2) #give it 200ms before checking if it returned already
                if not t.is_alive():
                    ErrorNotice(_("Looks like that didn't work; you may need "
                                    "to run a report first, or not do it in "
                                    "the background ({})."
                                ).format(kwargs))
                    unbackground+=[kwargs.copy()]
        done=all[:]
        for k in unbackground:
            done.remove(k)
        logfinished(start_time,msg="setting up background reports {}".format(done))
        log.info(_("Starting reports that didn't work in the background: {}").format(unbackground))
        for kwargs in unbackground:
            # log.info("reportmulti unbackground with kwargs {}".format(kwargs))
            self.wait(msg=kwargs)
            self.reportfn(**kwargs) #run what failed in background here
            self.waitdone()
        logfinished(start_time,msg="all reports ({})".format(all))
    def tonegroupreport(self,usegui=True,**kwargs):
        """This should iterate over at least some profiles; top 2-3?
        those with 2-4 verified frames? Selectable with radio buttons?"""
        start_time=nowruntime()
        #default=True redoes the UF analysis (removing any joining/renaming)
        ftype=kwargs.get('ftype',program['params'].ftype())
        def examplestoXLP(examples,parent,senseid):
            counts['senses']+=1
            for example in examples:
                # skip empty examples:
                if self.analang not in example.forms:
                    continue
                counts['examples']+=1
                if program['settings'].audiolang in example.forms:
                    counts['audio']+=1
                self.nodetoXLP(example,parent=parent,
                                                listword=True,
                                                showgroups=showgroups)
        analysisOK,showgroups,timestamps=program['status'].isanalysisOK(**kwargs)
        silent=kwargs.get('silent',False)
        default=kwargs.get('default',True)
        ps=kwargs.get('ps',program['slices'].ps())
        profile=kwargs.get('profile',program['slices'].profile())
        checks=program['status'].checks(wsorted=True,**kwargs)
        if not checks:
            if 'profile' in kwargs:
                log.error("{} {} came up with no checks.".format(ps,profile))
                return
            self.getprofile(wsorted=True)
        startnotice=("Starting report {} {}".format(ps,profile))
        log.info(startnotice)
        program['settings'].storesettingsfile()
        waitmsg=_("{} {} Tone Report in Process\n({})").format(ps,profile,
                                                                timestamps)
        if usegui:
            resultswindow=ResultWindow(self.parent,msg=waitmsg)
        bits=[str(self.reportbasefilename),
                rx.urlok(ps),
                rx.urlok(profile),
                "ToneReport"]
        if not default:
            bits.append('mod')
        self.tonereportfile='_'.join(bits)+".txt"
        checks=program['status'].checks(wsorted=True,**kwargs)
        if not checks:
            error=_("Hey, sort some morphemes in at least one frame before "
                        "trying to make a tone report!")
            log.error(error)
            if usegui:
                resultswindow.waitdone()
                resultswindow.destroy()
                ErrorNotice(error)
            return
        start_time=nowruntime()
        counts={'senses':0,'examples':0, 'audio':0}
        self.makeanalysis(**kwargs)
        # log.info("Caller function: {}".format(callerfn()))
        if analysisOK:
            log.info(_("Looks like the analysis is good; moving on."))
            self.analysis.donoUFanalysis() #based on (sense) UF fields
        elif callerfn() == 'run': #self.tonegroupreportmulti
            log.info(_("Sorry, the analysis isn't good, and we're running "
                    "in the background. That isn't going to work, so I'm "
                    "stopping here."))
            return
        else:
            log.info(_("Looks like the analysis isn't good, but we're not "
                    "in the background, so I'm doing a new analysis now."))
            self.analysis.do() #full analysis from scratch, output to UF fields
        """These are from LIFT, ordered by similarity for the report."""
        if not self.analysis.orderedchecks or not self.analysis.orderedUFs:
            log.error("Problem with checks: {} (in {} {})."
                    "".format(checks,ps,profile))
            log.error("valuesbygroupcheck: {}, valuesbycheckgroup: {}"
                        "".format(self.analysis.valuesbygroupcheck,
                                    self.analysis.valuesbycheckgroup))
            log.error("Ordered checks is {}, ordered UFs: {}"
                    "".format(self.analysis.orderedchecks,
                            self.analysis.orderedUFs))
            log.error("comparisonUFs: {}, comparisonchecks: {}"
                    "".format(self.analysis.comparisonUFs,
                            self.analysis.comparisonchecks))
        grouplist=[i for i in self.analysis.orderedUFs
                if len(self.analysis.senseidsbygroup[i]) >= self.minwords
                ]
        checks=self.analysis.orderedchecks
        r = open(self.tonereportfile, "w", encoding='utf-8')
        title=_("Tone Report")
        if usegui:
            resultswindow.scroll=ui.ScrollingFrame(resultswindow.frame)
            resultswindow.scroll.grid(row=0,column=0)
            window=resultswindow.scroll.content
            window.row=0
        else:
            window=None
        if 'xlpr' in kwargs:
            xlpr=kwargs['xlpr']
            s1parent=s0=xlp.Section(xlpr,title='{} {}'.format(ps,profile))
        else:
            s1parent=xlpr=self.xlpstart(reporttype='Tone',
                            ps=ps,
                            profile=profile,
                            # bylocation=self.bylocation,
                            default=default
                            )
            if not hasattr(xlpr,'node'):
                log.info(_("Problem creating report; see previous messages."))
                if kwargs['usegui']:
                    self.waitdone()
                xlpr.cleanup()
                return
        title=_('Introduction to {} {}').format(ps,profile)
        s1=xlp.Section(s1parent,title=title)
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
        t=_("Summary of Frames by {} {} Draft Underlying Melody").format(ps,profile)
        m=7 #only this many columns in a table
        # Don't bother with lanscape if we're splitting the table in any case.
        if m >= len(checks) > 6:
            landscape=True
        else:
            landscape=False
        s1s=xlp.Section(s1parent,t,landscape=landscape)
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
                        str(self.analysis.comparisonUFs),
                        str(self.analysis.comparisonchecks)))
        else:
            ptext+=_("This is a non-default report, where a user has changed "
            "the default (hyper-split) groups created by {}.".format(
                                                        program['name']))
        p0=xlp.Paragraph(s1s,text=ptext)
        self.analysis.orderedchecks=list(self.analysis.valuesbycheckgroup)
        for slice in range(int(len(self.analysis.orderedchecks)/m)+1):
            locslice=self.analysis.orderedchecks[slice*m:(slice+1)*m]
            if len(locslice) >0:
                self.buildXLPtable(s1s,caption+str(slice),
                        yterms=grouplist,
                        xterms=locslice,
                        values=lambda x,y:nn(unlist(
                self.analysis.valuesbygroupcheck[y][x],ignore=[None, 'NA']
                                            )),
                        ycounts=lambda x:len(self.analysis.senseidsbygroup[x]),
                        xcounts=lambda y:len(self.analysis.valuesbycheck[y]))
        #Can I break this for multithreading?
        for group in grouplist: #These already include ps-profile
            log.info("building report for {} ({}/{}, n={})".format(group,
                grouplist.index(group)+1,len(grouplist),
                len(self.analysis.senseidsbygroup[group])
                ))
            sectitle=_('\n{}'.format(str(group)))
            s1=xlp.Section(s1parent,title=sectitle)
            output(window,r,sectitle)
            l=list()
            for x in self.analysis.valuesbygroupcheck[group]:
                l.append("{}: {}".format(x,', '.join(
                    [i for i in self.analysis.valuesbygroupcheck[group][x]
                                                            if i is not None]
                        )))
            if not l:
                l=[_('<no frames with a sort value>')]
            # spaces>nbsp in key:value, only between k:v pairs
            text=_('Values by frame: {}'
                    ).format('; '.join([i.replace(' ',' ') for i in l]))
            log.info(text)
            p1=xlp.Paragraph(s1,text)
            output(window,r,text)
            if self.bylocation:
                textout=list()
                #This is better than checks, just whats there for this group
                for check in self.analysis.valuesbygroupcheck[group]:
                    id=rx.id('x'+sectitle+check)
                    headtext='{}: {}'.format(check,', '.join(
                            [i for i in
                            self.analysis.valuesbygroupcheck[group][check]
                            if i is not None]
                                            ))
                    e1=xlp.Example(s1,id,heading=headtext)
                    for senseid in self.analysis.senseidsbygroup[group]:
                        sense=program['db'].sensedict[senseid]
                        #This is for window/text output only, not in XLP file
                        text=sense.formatted(noframe=True,showtonegroup=False)
                        #This is put in XLP file:
                        if check in sense.examples:
                            examples=[sense.examples[check]]
                            examplestoXLP(examples,e1,senseid)
                        if text not in textout:
                            output(window,r,text)
                            textout.append(text)
                    if not e1.node.find('listWord'):
                        s1.node.remove(e1.node) #Don't show examples w/o data
            else:
                for senseid in self.analysis.senseidsbygroup[group]:
                    #This is for window/text output only, not in XLP file
                    sense=program['db'].sensedict[senseid]
                    #This is put in XLP file:
                    examples=sense.examples
                    log.info("{} exs found: {}".format(len(examples), examples))
                    if examples != []:
                        id=self.idXLP(sense)+'_examples'
                        headtext=text.replace('\t',' ')
                        e1=xlp.Example(s1,id,heading=headtext)
                        log.info("Asking for the following {} examples from id "
                                "{}: {}".format(len(examples),senseid,examples))
                        examplestoXLP(examples,e1,senseid)
                    else:
                        self.nodetoXLP(sense.ftypes[ftype],
                                        parent=s1,
                                        # ftype=ftype,
                                        showgroups=showgroups)
                    output(window,r,text)
        sectitle=_('{} {} Data Summary').format(ps,profile)
        s2=xlp.Section(s1parent,title=sectitle)
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
        if 'xlpr' not in kwargs:
            xlpr.close(me=me)
        text=_("Finished in {} seconds.").format(nowruntime()-start_time)
        text=logfinished(start_time,msg="report {} {}".format(ps,profile))
        logfinished(start_time)
        output(window,r,text)
        text=_("(Report is also available at ({})").format(self.tonereportfile)
        output(window,r,text)
        r.close()
        if usegui:
            resultswindow.waitdone()
            if me:
                resultswindow.on_quit()
        program['status'].last('report',update=True)
    def makeresultsframe(self):
        if hasattr(self,'runwindow') and self.runwindow.winfo_exists:
            self.results = ui.Frame(self.runwindow.frame,width=800)
            self.results.grid(column=0,
                            row=self.runwindow.frame.grid_info()['row']+1,
                            columnspan=5,
                            sticky=(ui.N, ui.S, ui.E, ui.W))
            self.results.scroll=ui.ScrollingFrame(self.results)
            self.results.scroll.grid(column=0, row=1)
            self.results.row=0
        else:
            log.error("Tried to get a results frame without a runwindow!")
    def background(self,fn,**kwargs):
        kwargs['usegui']=False
        t=multiprocessing.Process(target=fn,
                                    kwargs=kwargs)
        t.start()
        log.info(_("Starting XLP background report with kwargs {}"
                    ).format(kwargs))
        time.sleep(0.2) #give it 200ms before checking if it returned already
        if not t.is_alive():
            ErrorNotice(_("Looks like that didn't work; "
                            "you may need "
                            "to run a report first, or "
                            "trying again not in "
                            "the background ({})."
                        ).format(kwargs))
            fn(**kwargs)
    def getresults(self,**kwargs):
        def iterateUFgroups(parent,**kwargs):
            checks=[kwargs['check']]
            #Use this to distinguish "=" checks from "≠" checks, in that order
            if 'x' in kwargs['check'] and kwargs['cvt'] not in ['CV','VC']: #CV has no C=V...
                checks=[rx.sub('x','=',kwargs['check'],count=1)]+checks
            for kwargs['check'] in checks:
                self.docheckreport(parent,**kwargs) #this needs parent
            self.coocurrencetables(xlpr)
        log.info("getresults starting with kwargs {}".format(kwargs))
        usegui=kwargs['usegui']=kwargs.get('usegui',True)
        # log.info("getresults continuing with kwargs {}".format(kwargs))
        if usegui:
            self.getrunwindow()
            self.makeresultsframe() #not for now, causing problems
        kwargs['cvt']=kwargs.get('cvt',program['params'].cvt())
        kwargs['ps']=kwargs.get('ps',program['slices'].ps())
        kwargs['profile']=kwargs.get('profile',program['slices'].profile())
        kwargs['check']=kwargs.get('check',program['params'].check())
        self.adhocreportfileXLP='_'.join([str(self.reportbasefilename)
                                        ,str(kwargs['ps'])+'-'+str(kwargs['profile'])
                                        ,str(kwargs['check'])
                                        ,'ReportXLP.xml'])
        self.checkcounts={}
        log.info("Starting XLP report with these kwargsː {}".format(kwargs))
        xlpr=self.xlpstart(**kwargs)
        if not hasattr(xlpr,'node'):
            log.info(_("Problem creating report; see previous messages."))
            if kwargs['usegui']:
                self.waitdone()
            xlpr.cleanup()
            return
        """"Do I need this?"""
        print(_("Getting results of Search request"))
        c1 = "Any"
        c2 = "Any"
        """nn() here keeps None and {} from the output, takes one string,
        list, or tuple."""
        kwargs['formstosearch']=self.formspsprofile(**kwargs)
        text=(_("{} roots of form {} by {}".format(kwargs['ps'],
                                                    kwargs['profile'],
                                                    kwargs['check'])))
        if usegui: #i.e., showing results in window
            ui.Label(self.results, text=text).grid(column=0, row=self.results.row)
            self.runwindow.wait()
        si=xlp.Section(xlpr,text)
        if self.byUFgroup:
            self.makeanalysis()
            self.analysis.donoUFanalysis()
            # torecord=analysis.senseidsbygroup
            ufgroupsnsenseids=analysis.senseidsbygroup.items()
            kwargs['sectlevel']=4
            t=_("{} checks".format(program['params'].cvtdict()[kwargs['cvt']]['sg']))
            for kwargs['ufgroup'],kwargs['ufsenseids'] in ufgroupsnsenseids:
                if 'ufgroup' in kwargs:
                    log.info("Going to run {} report for UF group {}"
                            "".format(program['params'].cvtdict()[kwargs['cvt']]['sg'],
                                    kwargs['ufgroup']))
                sid=" ".join([t,"for",kwargs['ufgroup']])
                s2=xlp.Section(si,sid) #,level=2
                iterateUFgroups(s2,**kwargs)
        else:
            kwargs['ufgroup']=_("All")
            iterateUFgroups(si,**kwargs)
            # These lines get all senseids, to test that we're not losing any, below
        # This is the first of three blocks to uncomment (on line, then logs)
        # self.regexCV=profile
        # self.regex=rx.fromCV(self,lang=self.analang,
        #                     word=True, compile=True)
        # rxsenseidsinslice=self.senseidformsbyregex(self.regex)
        # senseidsinslice=program['slices'].senseids()
        # log.info("nrxsenseidsinslice: {}".format(len(rxsenseidsinslice)))
        # log.info("nsenseidsinslice: {}".format(len(senseidsinslice)))
        # senseidsnotsearchable=set(senseidsinslice)-set(rxsenseidsinslice)
        # log.info("senseidsnotsearchable: {}".format(len(senseidsnotsearchable)))
        # log.info("senseidsnotsearchable: {}".format(senseidsnotsearchable))
        xlpr.close(me=me)
        if usegui:
            self.runwindow.waitdone()
            if not hasattr(self,'results'): #i.e., showing results in window
                self.runwindow.on_quit()
        # Report on testing blocks above
        # log.info("senseids remaining (rx): ({}) {}".format(
        #                                                 len(rxsenseidsinslice),
        #                                                 rxsenseidsinslice))
        # log.info("senseids remaining: ({}) {}".format(len(senseidsinslice),
        #                                                     senseidsinslice))
        n=0
        for ps in self.checkcounts:
            for profile in self.checkcounts[ps]:
                for ufg in self.checkcounts[ps][profile]:
                    for check in self.checkcounts[ps][profile][ufg]:
                        for group in self.checkcounts[ps][profile][ufg][check]:
                            i=self.checkcounts[ps][profile][ufg][check][group]
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
            text=_("No results for {}/{} ({})!").format(kwargs['profile'],
                                                        kwargs['check'],
                                                        kwargs['ps'])
            log.info(text)
            if usegui: #i.e., showing results in window
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
        ps=kwargs.get('ps',program['slices'].ps())
        profile=kwargs.get('profile',program['slices'].profile())
        default=kwargs.get('default',True)
        check=kwargs.get('check',program['params'].check())
            #this is only for adhoc "big button" reports.

        if isinstance(self, Multislice) and 'psprofiles' in kwargs:
            reporttype=' '.join(
                        [' '.join([ps]+
                                ['('+'-'.join(kwargs['psprofiles'][ps])+')'
                                            ])
                                for ps in kwargs['psprofiles']
                                ])
        else:
            reporttype=' '.join([ps,profile])
        if isinstance(self,Multicheck):
            reporttype+=' '+'-'.join(self.cvtstodo)
        elif not isinstance(self,Tone) or isinstance(self,Segments):
            reporttype+='-'+check
        else:
            if self.bylocation:
                reporttype+='Tone-bylocation'
            else:
                reporttype+='Tone'
        if self.byUFgroup:
                reporttype+='byUFgroup'
        bits=[str(self.reportbasefilename),rx.id(reporttype),"ReportXLP"]
        if not default:
            bits.append('mod')
        reportfileXLP='_'.join(bits)+".xml"
        xlpreport=xlp.Report(reportfileXLP,reporttype,
                        program['settings'].languagenames[self.analang],
                        program # who is calling this report?
                        )
        # langsalreadythere=[]
        if hasattr(xlpreport,'node'): #otherwise, this will fail
            for lang in set([self.analang]+self.glosslangs)-set([None]):
                xlpreport.addlang({'id':lang,
                                    'name': program['settings'].languagenames[lang]})
        return xlpreport
    def wordsbypsprofilechecksubcheckp(self,parent,**kwargs):
        # log.info("Kwargs (wordsbypsprofilechecksubcheckp): {}".format(kwargs))
        usegui=kwargs['usegui']=kwargs.get('usegui',True)
        cvt=kwargs['cvt']=kwargs.get('cvt',program['params'].cvt())
        ps=kwargs['ps']=kwargs.get('ps',program['slices'].ps())
        profile=kwargs['profile']=kwargs.get('profile',program['slices'].profile())
        check=kwargs['check']=kwargs.get('check',program['params'].check())
        group=kwargs['group']=kwargs.get('group',program['status'].group())
        ftype=kwargs['ftype']=kwargs.get('ftype',program['params'].ftype())
        skipthisone=False
        checkprose="{} {} {} {}={}".format(kwargs['ps'],
                                    kwargs['profile'],
                                    kwargs['ufgroup'],
                                    kwargs['check'],
                                    kwargs['group'])
        if ('x' in kwargs['check'] and hasattr(self,'groupcomparison')
                    and self.groupcomparison):
            checkprose+='-'+self.groupcomparison
        if isinteger(group) or (hasattr(self,'groupcomparison') and
                                isinteger(self.groupcomparison)):
            log.info(_("Skipping check {} because it would break the regex"
                        "").format(checkprose))
            skipthisone=True
        if skipthisone:
            return
        log.info(checkprose)
        """possibly iterating over all these parameters, used by buildregex"""
        self.buildregex(**kwargs)
        # log.info("{}; regexCV: {}"
        #         # "; \nregex: {}"
        #         "".format(
        #         checkprose,
        #         self.regexCV,
        #         # self.regex
        #         )         )
        matches=set(self.senseidformsbyregex(self.regex,**kwargs))
        if 'ufsenseids' in kwargs:
            matches=matches&set(kwargs['ufsenseids'])
        if hasattr(self,'basicreported') and check in self.basicreported:
            # log.info("Removing {} entries already found from {} entries found "
            #         "by {} check".format(len(self.basicreported[check]),
            #                             len(matches),
            #                             check))
            # log.info("Entries found ({}):".format(len(matches)))
            matches-=self.basicreported[check]
            # log.info("{} entries remaining.".format(len(matches)))
        ufg=kwargs['ufgroup']
        n=len(matches)
        # log.info("{} matches found!: {}".format(len(matches),matches))
        if 'x' not in check:
            ncheckssimple=len(check.split('=')) #how many syllables impacted
            chks=check.split('=')+[check] #each and all together
            for r in range(1,ncheckssimple): #make other splits (e.g., V2=V3)
                chks+=check.split('=',r)+check.rsplit('=',r)
            for c in set(chks): #get each bit, and whole, too
                try:
                    self.checkcounts[ps][profile][ufg][c][group]+=n
                except KeyError:
                    try:
                        self.checkcounts[ps][profile][ufg][c][group]=n
                    except KeyError:
                        try:
                            self.checkcounts[ps][profile][ufg][c]={group:n}
                        except KeyError:
                            try:
                                self.checkcounts[ps][profile][ufg]={c:{group:n}}
                            except KeyError:
                                try:
                                    self.checkcounts[ps][profile]={ufg:{c:{
                                                                    group:n}}}
                                except KeyError:
                                    self.checkcounts[ps]={profile:{ufg:{c:{
                                                                    group:n}}}}
                                    # log.info("ps: {}, profile: {}, check: {}, "
                                    #         "group: {}".format(ps,profile,c,group))
        if 'x' in check or len(check.split('=')) == 2:
            if 'x' in check:
                othergroup=self.groupcomparison
                c=check
            else: #if len(check.split('=')) == 2:
                """put X=Y data in XxY"""
                othergroup=group
                c=rx.sub('=','x',check, count=1) #copy V1=V2 into V1xV2
            try:
                self.checkcounts[ps][profile][ufg][c][
                                                group][othergroup]=n
            except KeyError:
                try:
                    self.checkcounts[ps][profile][ufg][c][
                                                group]={othergroup:n}
                except KeyError:
                    try:
                        self.checkcounts[ps][profile][ufg][c]={group:{
                                                    othergroup:n}}
                    except KeyError:
                        try:
                            self.checkcounts[ps][profile][ufg]={c:{group:{
                                                    othergroup:n}}}
                        except KeyError:
                            try:
                                self.checkcounts[ps][profile]={ufg:{c:{
                                            group:{othergroup:n}}}}
                            except KeyError:
                                self.checkcounts[ps]={profile:{ufg:{c:{
                                            group:{othergroup:n}}}}}
        if n>0:
            titlebits='x'+ps+profile+check+group
            if 'x' in check:
                titlebits+='x'+othergroup
            if 'ufgroup' in kwargs:
                titlebits+=kwargs['ufgroup']
            id=rx.id(titlebits)
            ex=xlp.Example(parent,id,heading=checkprose)
            if hasattr(self,'basicreported') and '=' in check:
                # log.info(self.basicreported.keys())
                # log.info("Adding to basicreported for keys {}"
                #         "".format(check.split('=')))
                for c in check.split('='):
                    # log.info("adding {} matches".format(len(matches)))
                    try:
                        # log.info("to {} matches for {}".format(
                        #         len(self.basicreported[c]),c))
                        self.basicreported[c]|=matches
                        # log.info("Last entries: {}".format(
                        #                 list(self.basicreported[c])[-5:]))
                    except KeyError:
                        # log.info("to a new key for {}".format(c))
                        self.basicreported[c]=matches
                        # log.info("First entries: {}".format(
                        #                     list(self.basicreported[c])[:5]))
            for sense in [program['db'].sensedict[m] for m in matches]:
                node=sense.ftypes[ftype]
                self.nodetoXLP(node,parent=ex,listword=True) #showgroups?
                if usegui and hasattr(self,'results'): #i.e., showing results in window
                    self.results.row+=1
                    col=0
                    for t in [node.textvaluebylang(self.analang)]+[
                                node.gloss(l) for l in self.glosslangs]:
                        col+=1
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
        kwargs['cvt']=kwargs.get('cvt',program['params'].cvt()) #only send on one
        ps=kwargs.get('ps',program['slices'].ps())
        kwargs['profile']=kwargs.get('profile',program['slices'].profile())
        #CV checks depend on profile, too
        if isinstance(self,Multicheck):
            checksunordered=program['status'].checks(**kwargs)
            checks=self.orderchecks(checksunordered)
            # log.info("Going to do these checks: {}".format(checksunordered))
            log.info("Going to do checks in this order: {}".format(checks))
        else:
            checks=[kwargs.get('check',program['params'].check())]
            """check set here"""
        for kwargs['check'] in checks: #self.checkcodesbyprofile:
            """multithread here"""
            self.docheckreport(parent,**kwargs)
    def orderchecks(self,checklist):
        checks=sorted([i for i in checklist if '=' in i], key=len, reverse=True)
        checks+=sorted([i for i in checklist if '=' not in i
                                                if 'x' not in i], key=len)
        checks+=sorted([i for i in checklist if 'x' in i], key=len)
        return checks
    def docheckreport(self,parent,**kwargs):
        kwargs['cvt']=kwargs.get('cvt',program['params'].cvt())
        kwargs['ps']=kwargs.get('ps',program['slices'].ps())
        kwargs['profile']=kwargs.get('profile',program['slices'].profile())
        kwargs['check']=kwargs.get('check',program['params'].check())
        # log.info("docheckreport starting with kwargs {}".format(kwargs))
        groups=program['status'].groups(**kwargs)
        group=program['status'].group()
        self.ncvts=rx.split('[=x]',kwargs['check'])
        if 'x' in kwargs['check']:
            log.debug('Hey, I cound a correspondence number!')
            if kwargs['cvt'] in ['V','C']:
                groupcomparisons=groups
            elif kwargs['cvt'] == 'CV':
                groups=program['status'].groups(cvt='C')
                groupcomparisons=program['status'].groups(cvt='V')
            elif kwargs['cvt'] == 'VC':
                groups=program['status'].groups(cvt='V')
                groupcomparisons=program['status'].groups(cvt='C')
            else:
                log.error("Sorry, I don't know how to compare cvt: {}"
                                                    "".format(kwargs['cvt']))
            log.info("Going to run report for groups {}".format(groups))
            log.info("With comparison groups {}".format(groupcomparisons))
            for kwargs['group'] in groups:
                for self.groupcomparison in groupcomparisons:
                    if kwargs['group'] != self.groupcomparison:
                        self.wordsbypsprofilechecksubcheckp(parent,**kwargs)
        elif group:
            log.info("Going to run subcheckp just for group {}".format(group))
            self.wordsbypsprofilechecksubcheckp(parent,group=group,**kwargs)
        elif groups:
            log.info("Going to run subcheckp for groups {}".format(groups))
            for kwargs['group'] in groups:
                self.wordsbypsprofilechecksubcheckp(parent,**kwargs)
    def idXLP(self,node):
        """node here is either a ftype node or example"""
        id='x' #string!
        bits=[
            program['params'].cvt(),
            program['slices'].ps(),
            program['slices'].profile(),
            ]
        try:
            bits.append(node.locationvalue()) #for examples
            bits.append(node.tonevalue())
        except AttributeError:
            try:
                bits.append(node.ftype) #for sense fields
            except AttributeError:
                bits.append(node.id) #for senses
        for lang in self.glosslangs:
            if lang in node.parent.sense.glosses:
                bits+=node.gloss(lang) #parent.sense.formattedgloss(glosslang)
        for x in bits:
            if x is not None:
                id+=x
        return rx.id(id) #for either example or listword
    def nodetoXLP(self,node,parent,listword=False,showgroups=True):
        """This will likely only work when called by
        wordsbypsprofilechecksubcheck; but is needed because it must return if
        the word is found, leaving wordsbypsprofilechecksubcheck to continue"""
        """parent is an example in the XLP report"""
        """Node here should be a field/FormParent, including an example, but
        NOT a sense (FieldParent)"""
        id=self.idXLP(node)
        if listword == True:
            ex=xlp.ListWord(parent,id)
        else:
            exx=xlp.Example(parent,id) #the id goes here...
            ex=xlp.Word(exx) #This doesn't have an id
        audio=node.textvaluebylang(program['settings'].audiolang)
        form=node.textvaluebylang(self.analang)
        # log.info("Found form {} and audio {}".format(form,audio))
        if audio:
            # log.info("Found audio!")
            url=file.getdiredrelURLposix(self.reporttoaudiorelURL,audio)
            el=xlp.LinkedData(ex,self.analang,form,str(url))
        else:
            # log.info("Found audio not!")
            el=xlp.LangData(ex,self.analang,form)
        phonetic=node.parent.sense.textvaluebyftypelang('ph',self.analang)
        if program['settings'].showoriginalorthographyinreports and phonetic:
            elph=xlp.LangData(ex,self.analang,phonetic)
        if hasattr(node,'tonevalue') and showgroups: #joined groups show each
            elt=xlp.LangData(ex,self.analang,node.tonevalue())
        for lang in self.glosslangs:
            if lang in node.parent.sense.glosses:
                xlp.Gloss(ex,lang,node.gloss(lang))
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
        if (program['settings'].audiolang in framed.forms and
                    ftype in framed.forms[program['settings'].audiolang] and
                    framed.forms[program['settings'].audiolang][ftype]):
            url=file.getdiredrelURLposix(self.reporttoaudiorelURL,
                                framed.forms[program['settings'].audiolang][ftype])
            el=xlp.LinkedData(ex,self.analang,framed.forms[self.analang][ftype],
                                                                    str(url))
        else:
            el=xlp.LangData(ex,self.analang,framed.forms[self.analang][ftype])
        if program['settings'].showoriginalorthographyinreports and (
                    'ph' in framed.forms[self.analang] and
                    framed.forms[self.analang]['ph']):
            elph=xlp.LangData(ex,self.analang,framed.forms[self.analang]['ph'])
        if hasattr(framed,'tonegroup') and showgroups: #joined groups show each
            elt=xlp.LangData(ex,self.analang,framed.tonegroup)
        for lang in self.glosslangs:
            if lang in framed.forms:
                xlp.Gloss(ex,lang,framed.forms[lang])
    def printcountssorted(self):
        #This is only used in the basic report
        log.info("Ranked and numbered syllable profiles, by lexical category:")
        nTotal=0
        nTotals={}
        for line in program['slices']: #profilecounts:
            profile=line[0]
            ps=line[1]
            nTotal+=program['slices'][line]
            if ps not in nTotals:
                nTotals[ps]=0
            nTotals[ps]+=program['slices'][line]
        print('Profiled data:',nTotal)
        """Pull this?"""
        for ps in program['slices'].pss():
            if ps == 'Invalid':
                continue
            log.info("Part of Speech {}:".format(ps))
            for line in program['slices'].valid(ps=ps):
                profile=line[0]
                ps=line[1]
                log.info("{}: {}".format(profile,program['slices'][line]))
            print(ps,"(total):",nTotals[ps])
    def printprofilesbyps(self):
        #This is only used in the basic report
        log.info("Syllable profiles actually in senses, by lexical category:")
        for ps in self.profilesbysense:
            if ps in ['Invalid','analang']:
                continue
            print(ps, self.profilesbysense[ps])
    def psprofilestodo(self):
        if isinstance(self,Multislice):
            return {ps:program['slices'].profiles(ps=ps)[:program['settings'].maxprofiles]
                for ps in program['slices'].pss()[:program['settings'].maxpss]
                }
        else:
            return {program['slices'].ps():[program['slices'].profile()]}
    def basicreport(self,usegui=True,**kwargs):
        """This does both multiple slices (starting with largest) and
        multiple checks (all available per profile).
        These should be separated"""
        """We iterate across these values in this script, so we save current
        values here, and restore them at the end."""
        def iteratecvt(parent,**kwargs):
            if 'ufgroup' not in kwargs:
                kwargs['ufgroup']=_("All")
            for kwargs['cvt'] in self.cvtstodo:
                t=_("{} checks".format(program['params'].cvtdict()[
                                                        kwargs['cvt']]['sg']))
                # print(t)
                log.info(t)
                sid=" ".join([t,"for",kwargs['ufgroup'],kwargs['profile'],
                            kwargs['ps']+'s'])
                s34=xlp.Section(parent,sid,level=kwargs['sectlevel'])
                maxcount=rx.countxiny(kwargs['cvt'], kwargs['profile'])
                # re.subn(cvt, cvt, profile)[1]
                self.wordsbypsprofilechecksubcheck(s34,**kwargs)
        #Convert to iterate over local variables
        log.info("basicreport starting with kwargs {}".format(kwargs))
        instr=_("The data in this report is given by most restrictive test "
                "first, followed by less restrictive tests (e.g., V1=V2 "
                "before V1 or V2). Additionally, each word only "
                "appears once per segment in a given position, so a word that "
                "occurs in a more restrictive environment will not appear in "
                "the later less restrictive environments. But where multiple "
                "examples of a segment type occur with different values, e.g., "
                "V1≠V2, those words will appear multiple times, e.g., for "
                "both V1=x and V2=y.")
        kwargs['usegui']=usegui
        if kwargs['usegui']: #i.e., showing results in window
            self.wait(msg=_("Running {}").format(self.tasktitle()))
        self.basicreportfile=''.join([str(self.reportbasefilename)
                                        ,'_',''.join(sorted(self.cvtstodo)[:2])
                                        ,'_MultisliceReport.txt'])
        kwargs['psprofiles']=self.psprofilestodo()
        log.info("kwargs['psprofiles']={}".format(kwargs['psprofiles']))
        reporttype='Multislice '+'-'.join(self.cvtstodo)
        xlpr=self.xlpstart(**kwargs)
        if not hasattr(xlpr,'node'):
            log.info(_("Problem creating report; see previous messages."))
            if kwargs['usegui']:
                self.waitdone()
            xlpr.cleanup()
            return
        si=xlp.Section(xlpr,"Introduction")
        p=xlp.Paragraph(si,instr)
        sys.stdout = open(self.basicreportfile, "w", encoding='utf-8')
        print(instr)
        log.info(instr)
        #There is no runwindow here...
        self.basicreported={}
        self.checkcounts={}
        # self.printprofilesbyps() #don't really need this
        # self.printcountssorted() #don't really need this
        t=_("This report covers the following top two Grammatical categories, "
            "with the top {} syllable profiles in each. "
            "This is of course configurable, but I assume you don't want "
            "everything.".format(program['settings'].maxprofiles))
        log.info(t)
        print(t)
        p=xlp.Paragraph(si,t)
        for kwargs['ps'] in kwargs['psprofiles']:
            profiles=kwargs['psprofiles'][kwargs['ps']]
            t=_("{} data: (profiles: {})".format(kwargs['ps'],profiles))
            log.info(t)
            print(t)
            s1=xlp.Section(xlpr,t)
            t=_("This section covers the following top syllable profiles "
                "which are found in {}s: {}".format(kwargs['ps'],profiles))
            p=xlp.Paragraph(s1,t)
            log.info(t)
            for kwargs['profile'] in profiles:
                kwargs['formstosearch']=self.formspsprofile(**kwargs)
                t=_("{} {}s".format(kwargs['profile'],kwargs['ps']))
                s2=xlp.Section(s1,t,level=2)
                log.info(t)
                if self.byUFgroup:
                    self.makeanalysis(**kwargs)
                    self.analysis.donoUFanalysis()
                    # torecord=analysis.senseidsbygroup
                    ufgroupsnids=[(i,j) for i,j in
                                self.analysis.senseidsbygroup.items()
                                #don't report small groups
                                if len(j) >= self.minwords]
                    kwargs['sectlevel']=4
                    for kwargs['ufgroup'],kwargs['ufsenseids'] in ufgroupsnids:
                        if 'ufgroup' in kwargs:
                            log.info("Going to run report for UF group {}"
                                    "".format(kwargs['ufgroup']))
                        sid=" ".join([t,"for",kwargs['ufgroup']])
                        s3=xlp.Section(s2,sid,level=3)
                        iteratecvt(parent=s3,**kwargs)
                        # for check in self.checks: #self.checkcodesbyprofile:
                        #     """multithread here"""
                        #     self.docheckreport(parent,check=check,cvt=cvt,**kwargs)
                else:
                    kwargs['sectlevel']=3
                    iteratecvt(parent=s2,**kwargs)
        self.coocurrencetables(xlpr)
        log.info(self.checkcounts)
        xlpr.close(me=me)
        sys.stdout.close()
        sys.stdout=sys.__stdout__ #In case we want to not crash afterwards...:-)
        if kwargs['usegui']:
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
                for ufg in self.checkcounts[ps][profile]:
                    checks=self.orderchecks(self.checkcounts[ps][profile][ufg])
                    columncounts={}
                    # Divide checks into those with multiple columns, and others
                    xchecks=[i for i in checks if 'x' in i]
                    # eventually, this should have logic to see how wide each
                    # table is, and whether it makes sense to put it where.
                    # short tables should go next to short tables, but no more
                    # than two (or one) wide table in a row
                    if len(xchecks)>4: #only so many tables wide on a page
                        xchecksVx=[i for i in xchecks if i.startswith('V')]
                        xchecksCx=[i for i in xchecks if (not i.startswith('V')
                                                        and i.startswith('Cx'))]
                        xchecksCyx=[i for i in xchecks if (not i.startswith('V')
                                                    and not i.startswith('Cx'))]
                    else:
                        xchecksVx=xchecks
                        xchecksCx=[]
                        xchecksCyx=[]
                    onecolchecks=[i for i in checks if 'x' not in i]
                    # Put all single column tables into one dataset:
                    for check in onecolchecks:
                        counts=self.checkcounts[ps][profile][ufg][check]
                        for row in counts:
                            try:
                                columncounts[row][check]=counts[row]
                            except (KeyError,UnboundLocalError):
                                try:
                                    columncounts[row]={check:counts[row]}
                                except (KeyError,UnboundLocalError):
                                    columncounts={row:{check:counts[row]}}
                    # Test the other checks, to see if any is wider than tall:
                    for xchecks in [i for i in
                                        [xchecksVx,xchecksCx,xchecksCyx] if i]:
                        wide=False
                        for check in xchecks:
                            counts=self.checkcounts[ps][profile][ufg][check]
                            for r in [i for i in counts if counts[i]]:
                                if len([i for i in counts[r] if counts[r][i]]
                                        )>len([i for i in counts if counts[i]]):
                                        wide=True
                        if not wide:
                            #if all are not wide, join them into one row
                            caption=' '.join([ufg,ps,profile,check])
                            table=xlp.Table(s3s,caption)
                            row=xlp.Row(table)
                            for check in xchecks:
                                counts=self.checkcounts[ps][profile][ufg][check]
                                if (len(list(counts)) and
                                        len([counts[k] for k in counts])):
                                    cell=xlp.Cell(row)
                                    caption=' '.join([ufg,ps,profile,check])
                                    tableb=xlp.Table(cell,caption,numbered=False)
                                    log.debug("Counts by ({}-{}) check: {}".format(
                                                                    ufg,
                                                                    check,
                                                                    counts))
                                    self.coocurrencetable(tableb,check,counts)
                        else:
                            #if they are wide, just leave them in their own tables:
                            for check in xchecks:
                                counts=self.checkcounts[ps][profile][ufg][check]
                                if (len(list(counts)) and
                                        len([counts[k] for k in counts])):
                                    log.debug("Counts by ({}-{}) check: {}".format(
                                                                        ufg,
                                                                        check,
                                                                        counts))
                                    caption=' '.join([ufg,ps,profile,check])
                                    table=xlp.Table(s3s,caption)
                                    self.coocurrencetable(table,check,counts)
                    #Finally, do all single column tables in one table:
                    if (columncounts and len(list(columncounts)) and
                            len([columncounts[k] for k in columncounts])):
                        log.debug("Counts by ({}-{}) check: {}".format(ufg,
                                                            check,columncounts))
                        caption=' '.join([ufg,ps,profile,check])
                        table=xlp.Table(s3s,caption)
                        self.coocurrencetable(table,'x',columncounts)
    def coocurrencetable(self,table,check,counts):
        """This needs to work with an additional layer, for UF groups"""
        """Basic report doesn't seem to put out any data"""
        if 'x' in check:
            rows=[r for r,c in counts.items()
                    if [c[v] for v in c
                        if c[v]
                        ]
                ]
            cols=sorted(set(ck
                            for r,c in counts.items()
                            for ck,cv in c.items()
                            if c[ck]
                            ))
        else:
            rows=[r for r,c in counts.items()
                    if c
                ]
            cols=[check]
        maxcols=20
        if not rows:
            table.destroy()
            return
        if len(cols) >maxcols: #break table
            ncols=int(len(cols)/2)+1
            colsa=cols[:ncols]
            colsb=cols[ncols:]
            countsa={r:{ck:c[ck]
                        for ck,cv in c.items()
                        if ck in colsa
                        } for r,c in counts.items()
                    }
            countsb={r:{ck:c[ck]
                        for ck,cv in c.items()
                        if ck in colsb
                        } for r,c in counts.items()
                    }
            table1row=xlp.Row(table)
            table1cell=xlp.Cell(table1row)
            table1=xlp.Table(table1cell,numbered=False)
            self.coocurrencetable(table1,check,countsa)
            table2row=xlp.Row(table)
            table2cell=xlp.Cell(table2row)
            table2=xlp.Table(table2cell,numbered=False)
            self.coocurrencetable(table2,check,countsb)
            return
        for x1 in ['header']+rows:
            h=xlp.Row(table)
            for x2 in ['header']+cols:
                # log.debug("x1: {}; x2: {}".format(x1,x2))
                # if x1 != 'header' and x2 not in ['header','n']:
                #     log.debug("value: {}".format(self.checkcounts[
                #         ps][profile][name][x1][x2]))
                if x1 == 'header' and x2 == 'header':
                    # log.debug("header corner")
                    # cell=xlp.Cell(h,content=name,header=True)
                    cell=xlp.Cell(h,content=check,header=True)
                elif x1 == 'header':
                    # log.debug("header row")
                    cell=xlp.Cell(h,content=x2,header=True)
                elif x2 == 'header':
                    # log.debug("header column")
                    cell=xlp.Cell(h,content=x1,header=True)
                else:
                    # log.debug("Not a header")
                    if x2 == check:
                        value=counts[x1]
                    else:
                        try:
                            value=counts[x1][x2]
                        except KeyError:
                            value=''
                    if not value:
                        value=''
                    cell=xlp.Cell(h,content=value)
    def __init__(self):
        self.reportbasefilename=program['settings'].reportbasefilename
        self.reporttoaudiorelURL=program['settings'].reporttoaudiorelURL
        self.distinguish=program['settings'].distinguish
        self.profilesbysense=program['settings'].profilesbysense
        if program['settings'].minimumwordstoreportUFgroup:
            self.minwords=program['settings'].minimumwordstoreportUFgroup
        else: #provide a default, return to settings file for modification
            self.minwords=program['settings'].minimumwordstoreportUFgroup=3
        self.s=program['settings'].s
        self.byUFgroup=False
        if not isinstance(self,Multicheck) and not program['params'].check():
            self.getcheck()
class Multislice(object):
    """This class just triggers which settings are visible to the user, and
    updates changes from child classes"""
    def __init__(self):
        # log.info("Setting up Multislice report, with {}".format(dir()))
        """I think these two should go:"""
        self.frame.status.redofinalbuttons() #because the fns changed
class MultisliceS(Multislice):
    def __init__(self):
        self.do=self.basicreport
        program['status'].group(None)
        Multislice.__init__(self)
class MultisliceT(Multislice):
    def __init__(self):
        self.do=self.tonegroupreportcomprehensive
        Multislice.__init__(self)
class Multicheck(object):
    def __init__(self):
        """This should only be used for segmental checks; tone reports are
        always multiple checks"""
        program['status'].group(None)
        log.info("Setting up Multicheck report, based on {}".format(dir()))
        self.do=self.basicreport
        self.frame.status.redofinalbuttons() #because the fns changed
class Multicheckslice(Multicheck,MultisliceS):
    def __init__(self):
        Multicheck.__init__(self)
        MultisliceS.__init__(self)
class ByUF(Tone):
    def __init__(self):
        Tone.__init__(self) #Nothing here; just make methods available
        self.byUFgroup=True
        log.info("doing report by UF groups")
class Background(object):
    """This class runs a report function in the background, where possible"""
    def __init__(self):
        log.info("Setting up background report, based on {}"
                "".format(self.do.__name__))
        self.do=lambda fn=self.do:self.background(fn)
        self.frame.status.redofinalbuttons() #because the fns changed
class SortCV(Sort,Segments,TaskDressing):
    """docstring for SortCV."""
    def __init__(self, parent):
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
        #window=ui.Window(self,, title=t, entry=entry, backcmd=fixdiff)
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
        window=ui.Window(self.parent, entry=entry, backcmd=notpickedback)
        ui.Label(window, text="Let's fix those problems").grid(column=0, row=0)
        if entry.problem == "badCheck": #This isn't the right check for this entry --re.search("V1≠V2",difference):
            window.destroy()
            t=(_("fixVs:Different vowels! "))+entry.lexeme+': '+entry.guid
            window=ui.Window(self, title=t, entry=entry, backcmd=Check.fixdiff)
            Check.fixV1(parent, window, check, entry, choice)
            window.wait_window(window=window)
            window=ui.Window(self, title=t, entry=entry, backcmd=Check.fixdiff)
            Check.fixV2(parent, window, check, entry, choice) #I should make this wait until the first one finishes..…
            window.wait_window(window=window)
            window=ui.Window(self, title=t, entry=entry, backcmd=Check.fixdiff)
            Check.fixVs(parent, window, check, entry, choice)
        elif entry.problem == "badSubcheck": #This isn't the right subcheck for this entry --re.search("V1=V2≠"+Vo,difference): #
            window.destroy()
            t=(_("fixVs:Same Vowel, but wrong one! "))+entry.lexeme+': '+entry.guid
            window=ui.Window(self, title=t, entry=entry, backcmd=Check.fixdiff)
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
class SortV(Sort,Segments,TaskDressing):
    def taskicon(self):
        return program['theme'].photo['iconV']
    def tasktitle(self):
        return _("Sort Vowels") #Citation Form Sorting in Tone Frames
    def tooltip(self):
        return _("This task helps you sort words in citation form by vowels.")
    def dobuttonkwargs(self):
        return {'text':_("Sort!"),
                'fn':self.runcheck,
                # column=0,
                'font':'title',
                'compound':'bottom', #image bottom, left, right, or top of text
                'image':program['theme'].photo['V'], #self.cvt
                'sticky':'ew'
                }
    def __init__(self, parent):
        # ui.Window.__init__(self,parent)
        TaskDressing.__init__(self,parent)
        program['params'].cvt('V')
        Sort.__init__(self, parent)
        Segments.__init__(self,parent)
        # super(SortV, self).__init__()
        # Sort.__init__(self)
class SortC(Sort,Segments,TaskDressing):
    def taskicon(self):
        return program['theme'].photo['iconC']
    def tasktitle(self):
        return _("Sort Consonants") #Citation Form Sorting in Tone Frames
    def tooltip(self):
        return _("This task helps you sort words in citation form by consonants.")
    def dobuttonkwargs(self):
        return {'text':_("Sort!"),
                'fn':self.runcheck,
                # column=0,
                'font':'title',
                'compound':'bottom', #image bottom, left, right, or top of text
                'image':program['theme'].photo['C'], #self.cvt
                'sticky':'ew'
                }
    def __init__(self, parent):
        TaskDressing.__init__(self,parent)
        program['params'].cvt('C')
        Sort.__init__(self, parent)
        Segments.__init__(self,parent)
        # super(SortC, parent).__init__()
        # Sort.__init__(self)
class SortT(Sort,Tone,TaskDressing):
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
                'image':program['theme'].photo['T'], #self.cvt
                'sticky':'ew'
                }
    def __init__(self, parent): #frame, filename=None
        Tone.__init__(self)
        TaskDressing.__init__(self,parent)
        program['params'].cvt('T')
        Sort.__init__(self, parent)
        # log.info("status: {}".format(type(program['status'])))
        # Not sure what this was for (XML?):
        self.pp=pprint.PrettyPrinter()
        """Are we OK without these?"""
        log.info("Done initializing check.")
        """Testing Zone"""
    def addtonefieldpron(self,guid,framed): #unused; leads to broken lift fn
        senseid=None
        program['db'].addpronunciationfields(
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
class Transcribe(Sound,Sort,TaskDressing):
    def updateerror(self,event=None):
        self.errorlabel['text'] = ''
    def switchgroups(self,comparison=None):
        #this doesn't save!
        if (not hasattr(self,'group') or not hasattr(self,'group_comparison')
            and not comparison):
            log.error(_("Missing either group or comparison, without value "
                        "specified; can't switch them."))
            return
        g=self.group
        if comparison:
            gc=comparison
        else:
            gc=self.group_comparison
        program['status'].group(gc)
        program['settings'].set('group_comparison',g)
        # program['settings'].setgroup(gc)
        self.runwindow.destroy()
        self.makewindow()
    def submitandswitch(self):
        if hasattr(self,'group_comparison'):
            comparison=self.group_comparison
        else:
            self.errorlabel['text'] = _("Sorry, pick a comparison first!")
            return 1
        error=self.submitform()
        if not error:
            self.switchgroups(comparison)
    def updategroups(self):
        # Update locals group, groups, and othergroups from objects
        self.groups=program['status'].groups(wsorted=True)
        log.info("self.groups: {}".format(self.groups))
        self.groupsdone=program['status'].verified()
        self.group=program['status'].group()
        # log.info("group: {}, groups: {}".format(self.group,self.groups))
        if not self.groups:
            ErrorNotice(_("No groups in that slice; try another!"))
            return
        # log.info("group: {}, groups: {}".format(self.group,self.groups))
        if self.group is None or self.group not in self.groups:
            w=self.getgroup(wsorted=True, guess=True, intfirst=True)
            if w.winfo_exists():
                w.wait_window(w)
            self.group=program['status'].group()
            if not self.group:
                log.info("I asked for a framed tone group, but didn't get one.")
                return
        # log.info("group: {}, groups: {}".format(self.group,self.groups))
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
    def unsubmit(self,event=None):
        log.info("Undoing...")
        self.mistake=True
    def submitform(self):
        newvalue=self.transcriber.formfield.get()
        if newvalue == "":
            noname=_("Give a name for this group!")
            log.debug(noname)
            self.errorlabel['text'] = noname
            return 1
        if newvalue == "∅": #proxy for no segments
            newvalue=''
        if newvalue != self.group: #only make changes!
            showpolygraphs=False
            diff=False
            if newvalue in self.groups:
                deja=_("Sorry, there is already a group with "
                                "that label; If you want to join the "
                                "groups, give it a different name now, "
                                "and join it later".format(newvalue))
                log.debug(deja)
                self.errorlabel['text'] = deja
                return 1
            if program['params'].cvt() != 'T': #Warning only on segmental changes
                if len(newvalue) != 1 or len(self.group) != 1:
                    warning=_("This name change (‘{}’ > ‘{}’) impacts your "
                                "digraph and trigraph settings."
                                ).format(self.group,newvalue)
                    if len(newvalue) > 1:
                        warning+=_("\n{} will add ‘{}’ to those settings."
                                    ).format(program['name'],newvalue)
                    if len(self.group) > 1:
                        warning+=_("\n{} will *not* remove ‘{}’ from "
                                    "those settings, because you may still be "
                                    "using it elsewhere."
                                    ).format(program['name'],self.group)
                    warning+=_("\n\n**If this isn't what you wanted, "
                                "fix and confirm your digraph and "
                                "trigraph settings in the menu "
                                "\n(this will make {} restart and redo "
                                "the syllable profile analysis)."
                                ).format(program['name'])
                    title=_("Syllable profile change?")
                    #Just state this and move on to making changes:
                    self.err=ErrorNotice(warning,parent=self,title=title)
            self.updatebygroupsense(self.group,newvalue,updateforms=True)
            #NO: this should update formstosearch and profile data.
            # log.info("Doing renamegroup: {}>{}".format(self.group,newvalue))
            program['status'].renamegroup(self.group,newvalue) #status file, not LIFT
            # log.info("Doing updategroups")
            self.updategroups()
            program['settings'].storesettingsfile(setting='status')
            """Update regular expressions here!!"""
        else: #move on, but notify in logs
            log.info("User selected ‘{}’, but with no change.".format(
                                                                self.oktext))
            # update forms, even if group doesn't change. I should have a test
            # for when this is needed..…
            group=program['status'].group()
            if isnoninteger(group): #Don't do this for default groups
                ftype=program['params'].ftype()
                check=program['params'].check()
                log.info("updating for type {} check {}, group ‘{}’"
                        "".format(ftype,check,group))
                senses=self.getsensesincheckgroup()
                log.info("modding senseids {}".format(senseids))
                for sense in senses:
                    u = threading.Thread(target=self.updateformtoannotations,
                                        args=(sense,ftype),
                                        kwargs={'check':check})
                    # self.updateformtoannotations(senseid,ftype,check=check)
                    u.start()
                if senseids:
                    u.join()
                #NO: this should update formstosearch and profile data.
                # program['settings'].reloadstatusdatabycvtpsprofile()
                self.maybewrite()
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
            ints=[i for i in program['status'].groups(wsorted=True) if isinteger(i)]
            if ints:
                log.info("Found integer groups: {}".format(ints))
                program['status'].group(str(min(ints)))#Look for integers first
            else:
                log.info("Didn't Find integer groups: {}".format(
                    program['status'].groups(wsorted=True)))
                program['status'].nextgroup(wsorted=True)
            # log.debug("group: {}".format(group))
            self.makewindow()
    def nextcheck(self):
        log.debug("running next check")
        error=self.submitform()
        if not error:
            # log.debug("check: {}".format(check))
            program['status'].nextcheck(wsorted=True)
            # log.debug("check: {}".format(check))
            self.makewindow()
    def nextprofile(self):
        log.debug("running next profile")
        error=self.submitform()
        if not error:
            # log.debug("profile: {}".format(profile))
            program['status'].nextprofile(wsorted=True)
            # log.debug("profile: {}".format(profile))
            self.makewindow()
    def setgroup_comparison(self):
        w=self.getgroup(comparison=True,wsorted=True) #this returns its window
        if w and w.winfo_exists(): #This window may be already gone
            log.info("Waiting for {}".format(w))
            w.wait_window(w)
        log.info("Groups: {} (of {}); {}?".format(self.group,
                                            self.groups,
                                            # self.group_comparison,
                                            program['settings'].group_comparison))
        if hasattr(program['settings'],'group_comparison'):
            self.group_comparison=program['settings'].group_comparison
        if self.errorlabel['text'] == _("Sorry, pick a comparison first!"):
            self.updateerror()
        self.comparisonbuttons()
    def comparisonbuttons(self):
        try: #successive runs
            self.compframe.compframeb.destroy()
            log.info("Comparison frameb destroyed!")
        except: #first run
            log.info("Problem destroying comparison frame, making...")
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
            self.compframe.bf2=SortGroupButtonFrame(self.compframe.compframeb,
                                    self,
                                    self.group_comparison,
                                    showtonegroup=True,
                                    playable=True,
                                    unsortable=False, #no space, bad idea
                                    alwaysrefreshable=True,
                                    font='default',
                                    wraplength=self.buttonframew
                                    )
            self.compframe.bf2.grid(row=0, column=0, sticky='w')
            self.compframe.b2=ui.Button(self.compframe.compframeb,
                                        text=_("Switch Groups"),
                                        cmd=self.switchgroups,
                                        row=0, column=1, sticky='w')
            self.compframe.b2tt=ui.ToolTip(self.compframe.b2,
                                        _("This doesn't save the curent group"))
            # self.maybeswitchmenu=ui.ContextMenu(self.compframe)
            # self.maybeswitchmenu.menuitem(_("Switch to this group"),
            #                                 self.switchgroups)
        elif not hasattr(self, 'group_comparison'):
            log.info("No comparison found !")
        elif self.group_comparison not in self.groups:
            log.info("Comparison ({}) not in group list ({})"
                        "".format(self.group_comparison,self.groups))
        elif self.group_comparison == self.group:
            log.info("Comparison ({}) same as subgroup ({}); not showing."
                        "".format(self.group_comparison,self.group))
        else:
            log.info("This should never happen (renamegroup/"
                        "comparisonbuttons)")
        self.sub_c['text']=t
    def makewindow(self):
        # log.info("Making transcribe window")
        def changegroupnow(event=None):
            log.info("changing group now")
            w=program['taskchooser'].getgroup(wsorted=True)
            self.runwindow.wait_window(w)
            if not w.exitFlag.istrue(): #Not sure why this works; may break later.
            #     log.info("w ExitFlag is true!")
            # else:
                self.runwindow.on_quit()
                self.makewindow()
        cvt=program['params'].cvt()
        ps=program['slices'].ps()
        profile=program['slices'].profile()
        check=program['params'].check()
        self.buttonframew=int(program['screenw']/3.5)
        if not check:
            self.getcheck(guess=True)
            if check == None:
                log.info("I asked for a check name, but didn't get one.")
                return
        if not program['status'].groups(wsorted=True):
            log.error("I don't have any sorted data for check: {}, "
                        "ps-profile: {}-{},".format(check,ps,profile))
            return
        groupsok=self.updategroups()
        if not groupsok:
            log.error("Problem with log; check earlier message.")
            return
        padx=50
        if program['settings'].lowverticalspace:
            log.info("Using low vertical space setting")
            pady=0
        else:
            pady=10
        title=_("Rename {} {} {} group ‘{}’ in ‘{}’ frame"
                        ).format(ps,profile,
                        program['params'].cvtdict()[cvt]['sg'],
                        self.group,check)
        self.getrunwindow(title=title)
        titlel=ui.Label(self.runwindow.frame,text=title,font='title',
                        row=0,column=0,sticky='ew',padx=padx,pady=pady
                        )
        getformtext=_("What new name do you want to call this {} "
                        "group?").format(program['params'].cvtdict()[cvt]['sg'])
        if cvt == 'T':
            getformtext+=_("\nA label that describes the surface tone form "
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
                                chars=self.glyphspossible,
                                row=0,column=0,sticky=''
                                )
        self.transcriber.formfield.bind('<KeyRelease>', self.updateerror) #apply function after key
        """to here"""
        infoframe=ui.Frame(inputfeedbackframe,
                            row=0,column=1,sticky=''
                            )
        """Make this a pad of buttons, rather than a label, so users can
        go directly where they want to be"""
        g=nn(self.othergroups,perline=len(self.othergroups)//5)
        log.info("There: {}, NTG: {}; g:{}".format(self.groups,
                                                    self.othergroups,g))
        groupslabel=ui.Label(infoframe,
                            text='Other Groups:\n{}'.format(g),
                            row=0,column=1,
                            sticky='new',
                            padx=padx,
                            rowspan=2
                            )
        groupslabel.bind('<ButtonRelease-1>',changegroupnow)
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
        buttons=[
                (_('main screen'), self.done),
                (_('next group'), self.next)]
        if cvt == 'T':
            buttons+=[(_('next tone frame'), self.nextcheck)]
        else:
            buttons+=[(_('next check'), self.nextcheck)]
        buttons+=[(_('next syllable profile'), self.nextprofile),
                (_('comparison group'), self.submitandswitch)
                ]
        for button in buttons:
            column+=1
            ui.Button(responseframe,text = button[0], command = button[1],
                                anchor ='c',
                                row=0,column=column,sticky='ns'
                                )
        examplesframe=ui.Frame(self.runwindow.frame,
                                row=4,column=0,sticky=''
                                )
        b=SortGroupButtonFrame(examplesframe, self,
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
    def __init__(self,parent): #frame, filename=None
        TaskDressing.__init__(self, parent)
        program['settings'].makeeverythingok()
        self.mistake=False #track when a user has made a mistake
        program['status'].makecheckok()
        Sound.__init__(self)
class TranscribeV(Transcribe,Segments):
    def tasktitle(self):
        return _("Vowel Letters")
    def tooltip(self):
        return _("This task helps you decide on your vowel letters.")
    def dobuttonkwargs(self):
        return {'text':_("Transcribe Vowel Groups"),
                'fn':self.makewindow,
                'font':'title',
                'compound':'top', #image bottom, left, right, or top of text
                'image':program['theme'].photo['TranscribeV'], #self.cvt
                'sticky':'ew'
                }
    def taskicon(self):
        return program['theme'].photo['iconTranscribeV']
    def __init__(self, parent): #frame, filename=None
        self.glyphspossible=[ #'a','e','i','o','u','ɛ','ɔ','ɨ','ʉ']
        #tilde (decomposed):
        'ã', 'ẽ', 'ɛ̃', 'ə̃', 'ɪ̃', 'ĩ', 'õ', 'ɔ̃', 'ũ', 'ʊ̃',
        #Combining Greek Perispomeni (decomposed):
        'a͂', 'i͂', 'o͂', 'u͂',
        #single code point vowels:
        'a', 'e', 'i', 'ə', 'o', 'u',
        # 'A', 'E', 'I', 'Ə', 'O', 'U',
        'ɑ', 'ɛ', 'ɨ', 'ɔ', 'ʉ', 'ɩ',
        'æ', 'ʌ', 'ɪ', 'ï', 'ö', 'ʊ',
        #for those using precomposed letters:
        # 'à', 'è', 'ì', 'ò', 'ù',
        # # 'À', 'È', 'Ì', 'Ò', 'Ù',
        # 'á', 'é', 'í', 'ó', 'ú',
        # # 'Á', 'É', 'Í', 'Ó', 'Ú',
        # 'â', 'ê', 'î', 'ô', 'û',
        # # 'Â', 'Ê', 'Î', 'Ô', 'Û',
        # 'ã', 'ẽ', 'ĩ', 'õ', 'ũ'
        ]
        Transcribe.__init__(self,parent)
        program['params'].cvt('V')
class TranscribeC(Transcribe,Segments):
    def tasktitle(self):
        return _("Consonant Letters")
    def tooltip(self):
        return _("This task helps you decide on your consonant letters.")
    def dobuttonkwargs(self):
        return {'text':_("Transcribe Consonant Groups"),
                'fn':self.makewindow,
                'font':'title',
                'compound':'top', #image bottom, left, right, or top of text
                'image':program['theme'].photo['TranscribeC'], #self.cvt
                'sticky':'ew'
                }
    def taskicon(self):
        return program['theme'].photo['iconTranscribeC']
    def __init__(self, parent): #frame, filename=None
        self.glyphspossible=[#'p','b','k','g','d','t',]
        'bh','dh','gh','gb',
        'b',#'B',
        'd','g','ɡ', #,'G' messes with profiles
        'kk','kp',
        'p',#'P',
        'ɓ',#'Ɓ',
        't','ɗ','ɖ','c','k','q',
        'vh','zh',
        'j',#'J',
        'v','z',#'Z',
        'ʒ','ð','ɣ',
        'ch','ph','sh','hh','pf','bv',
        # 'F',
        'f','s','ʃ','θ','x','h', #not 'S'
        'dj','dz','dʒ',
        'chk',
        'ts','tʃ',
        'zl',
        'ɮ',
        'sl',
        'ɬ',
        'ʔ',
                "ꞌ", #Latin Small Letter Saltillo
                "'", #Tag Apostrophe
                'ʼ', #modifier letter apostrophe
        'ẅ','y',#'Y',
        'w',#'W',
        'm',#'M',
        'n','ŋ','ɲ','ɱ', #'N', messed with profiles
        'mm','ŋŋ','ny',
        "ng'",
        # """Non-Nasal/Glide Sonorants"""
        'l','r',
        'rh','wh',
        ]
        Transcribe.__init__(self,parent)
        program['params'].cvt('C')
class TranscribeT(Transcribe,Tone):
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
                'image':program['theme'].photo['Transcribe'], #self.cvt
                'sticky':'ew'
                }
    def taskicon(self):
        return program['theme'].photo['iconTranscribe']
    def __init__(self, parent): #frame, filename=None
        Tone.__init__(self)
        self.glyphspossible=None
        Transcribe.__init__(self,parent)
        program['params'].cvt('T')
class JoinUFgroups(Tone,TaskDressing):
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
                'image':program['theme'].photo['JoinUF'], #self.cvt
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
            if uf in self.analysis.orderedUFs and uf not in groupsselected:
                deja=_("That name is already there! (did you forget to include "
                        "the ‘{}’ group?)".format(uf))
                log.debug(deja)
                errorlabel['text'] = deja
                return
            for group in groupsselected:
                if group in self.analysis.senseidsbygroup: #selected ones only
                    log.debug("Changing values from {} to {} for the following "
                            "senseids: {}".format(group,uf,
                                        self.analysis.senseidsbygroup[group]))
                    for senseid in self.analysis.senseidsbygroup[group]:
                        program['db'].addtoneUF(senseid,uf,analang=self.analang,
                        write=False)
            self.maybewrite()
            self.runwindow.destroy()
            program['status'].last('joinUF',update=True)
            self.tonegroupsjoinrename() #call again, in case needed
        self.makeanalysis()
        def redo(timestamps="By manual request"):
            self.wait(_("Redoing Tone Analysis")+'\n'+timestamps)
            self.analysis.do()
            self.waitdone()
            # self.runwindow.destroy()
            self.tonegroupsjoinrename() #call again, in case needed
        def done():
            self.runwindow.destroy()
        ps=kwargs.get('ps',program['slices'].ps())
        profile=kwargs.get('profile',program['slices'].profile())
        analysisOK,joinedsince,timestamps=program['status'].isanalysisOK(**kwargs) #Should specify which lasts...
        if not analysisOK:
            redo(timestamps) #otherwise, the user will almost certainly be upset to have to do it later
            return
        self.getrunwindow(msg=_("Preparing to join draft underlying form groups"
                                "")+'\n'+timestamps)
        self.update()
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
        self.analysis.donoUFanalysis()
        nheaders=0
        if not self.analysis.orderedUFs:
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
        for group in self.analysis.orderedUFs: #make a variable and button to select
            idn=self.analysis.orderedUFs.index(group)
            if idn % 5 == 0: #every five rows
                col=1
                for check in self.analysis.orderedchecks:
                    col+=1
                    cbh=ui.Label(scroll.content, text=check, font='small')
                    cbh.grid(row=idn+nheaders,
                            column=col,sticky='ew')
                nheaders+=1
            groupvars.append(ui.StringVar())
            n=len(self.analysis.senseidsbygroup[group])
            buttontext=group+' ({})'.format(n)
            cb=ui.CheckButton(scroll.content, text = buttontext,
                                variable = groupvars[idn],
                                onvalue = group, offvalue = 0,
                                )
            cb.grid(row=idn+nheaders,column=0,sticky='ew')
            # analysis.valuesbygroupcheck[group]:
            col=1
            for check in self.analysis.orderedchecks:
                col+=1
                if check in self.analysis.valuesbygroupcheck[group]:
                    cbl=ui.Label(scroll.content,
                        text=unlist(
                                self.analysis.valuesbygroupcheck[group][check]
                                    )
                            )
                    cbl.grid(row=idn+nheaders,column=col,sticky='ew')
        self.runwindow.waitdone()
        self.runwindow.wait_window(scroll)
    def __init__(self, parent):
        Tone.__init__(self)
        TaskDressing.__init__(self, parent)
class RecordCitation(Record,Segments):
    def tooltip(self):
        return _("This task helps you record words in isolation forms.")
    def dobuttonkwargs(self):
        return {'text':_("Record Dictionary Words"),
                'fn':self.showentryformstorecord,
                'font':'title',
                'compound':'top', #image bottom, left, right, or top of text
                'image':program['theme'].photo['WordRec'],
                'sticky':'ew'
                }
    def tasktitle(self):
        return _("Record Words") #Citation Forms
    def taskicon(self):
        return program['theme'].photo['iconWordRec']
    def __init__(self, parent): #frame, filename=None
        Segments.__init__(self,parent)
        # ui.Window.__init__(self,parent)
        # TaskDressing.__init__(self,parent)
        Record.__init__(self,parent)
class RecordCitationT(Record,Tone):
    def tooltip(self):
        return _("This task helps you record words in tone frames, in citation form.")
    def dobuttonkwargs(self):
        return {'text':_("Record Words in Tone Frames"),
                'fn':self.showtonegroupexs,
                'font':'title',
                'compound':'top', #image bottom, left, right, or top of text
                'image':program['theme'].photo['TRec'],
                'sticky':'ew'
                }
    def taskicon(self):
        return program['theme'].photo['iconTRec']
    def tasktitle(self):
        return _("Record Tone") #Citation Form Sorting in Tone Frames
    def __init__(self, parent): #frame, filename=None
        Tone.__init__(self)
        Record.__init__(self,parent)
class ReportCitation(Report,Segments,TaskDressing):
    """docstring for ReportCitation."""
    def tasktitle(self):
        return _("Alphabet Report (Not background)") # on One Data Slice
    def taskicon(self):
        return program['theme'].photo['iconReport']
    def tooltip(self):
        return _("This report gives you reports for one lexical "
                "category, in one syllable profile. \nIt does "
                "one of three sets of reports: \n- Vowel, \n- Consonant, or "
                "\n- Consonant-Vowel Correspondence")
    def dobuttonkwargs(self):
        return {'text':"Report!",
                'fn':self.do,
                'font':'title',
                'compound':'bottom', #image bottom, left, right, or top of text
                'image':program['theme'].photo['Report'],
                'sticky':'ew'
                }
    def runcheck(self):
        """This needs to get stripped down and updated for just this check"""
        program['settings'].storesettingsfile()
        t=(_('Run Check'))
        log.info("Running report...")
        log.info("Using these regexs: {}".format(program['settings'].rx))
        # exit() #for testing
        i=0
        cvt=program['params'].cvt()
        if cvt == 'T':
            w=program['taskchooser'].getcvt()
            w.wait_window(w)
            cvt=program['params'].cvt()
            if cvt == 'T':
                ErrorNotice(_("Pick Consonants, Vowels, or CV for this report."))
                return
        ps=program['slices'].ps()
        if not ps:
            self.getps()
        check=program['params'].check()
        profile=program['slices'].profile()
        if not profile:
            self.getprofile()
        if not profile or not ps:
            window=ui.Window(self)
            text=_('Error: please set Ps-Profile first! ({}/{}/{})').format(
                                                     ps,check,profile)
            ui.Label(window,text=text).grid(column=0, row=i)
            i+=1
            return
        self.getresults()
    def __init__(self, parent): #frame, filename=None
        Segments.__init__(self,parent)
        self.do=self.getresults
        TaskDressing.__init__(self,parent)
        Report.__init__(self)
class ReportCitationBackground(Background,ReportCitation):
    """docstring for ReportCitation."""
    def tasktitle(self):
        return _("Alphabet Report") # on One Data Slice
    def __init__(self, parent):
        ReportCitation.__init__(self,parent)
        Background.__init__(self)
        """Does the above not work? was turned off..."""
        # self.do=lambda fn=self.getresults:self.background(fn)
        # self.frame.status.redofinalbuttons() #because the fns changed
class ReportCitationMulticheckBackground(Multicheck,Background,ReportCitation):
    """docstring for ReportCitation."""
    def tasktitle(self):
        return _("Alphabet Report (Multicheck)") # on One Data Slice
    def __init__(self, parent):
        ReportCitation.__init__(self,parent)
        Multicheck.__init__(self)
        Background.__init__(self)
class ReportCitationMultichecksliceBackground(Multicheckslice,Background,ReportCitation):
    """docstring for ReportCitation."""
    def tasktitle(self):
        return _("Alphabet Report (Multislice, Multicheck)") # on One Data Slice
    def __init__(self, parent):
        ReportCitation.__init__(self,parent)
        Multicheckslice.__init__(self)
        Background.__init__(self)
class ReportCitationByUF(ByUF,ReportCitation):
    """docstring for ReportCitation."""
    def tasktitle(self):
        return _("Alphabet Report by Tone group (not background)") # on One Data Slice
    def __init__(self, parent):
        ReportCitation.__init__(self, parent)
        ByUF.__init__(self)
class ReportCitationByUFMulticheckBackground(Multicheck,Background,ReportCitationByUF):
    """docstring for ReportCitation."""
    def tasktitle(self):
        return _("Alphabet Report by Tone group (Multicheck)") # on One Data Slice
    def __init__(self, parent):
        ReportCitationByUF.__init__(self, parent)
        Multicheck.__init__(self)
        Background.__init__(self)
class ReportCitationByUFMultichecksliceBackground(Multicheckslice,Background,ReportCitationByUF):
    """docstring for ReportCitation."""
    def tasktitle(self):
        return _("Alphabet Report by Tone Group (Multislice, Multicheck)") # on One Data Slice
    def __init__(self, parent):
        ReportCitationByUF.__init__(self,parent)
        Multicheckslice.__init__(self)
        Background.__init__(self)
class ReportCitationByUFBackground(ByUF,ReportCitationBackground):
    """docstring for ReportCitation."""
    def tasktitle(self):
        return _("Alphabet Report by Tone group") # on One Data Slice
    def __init__(self, parent):
        ReportCitationBackground.__init__(self, parent)
        ByUF.__init__(self)
class ReportCitationMultislice(MultisliceS,ReportCitation):
    """docstring for ReportCitation."""
    def tasktitle(self):
        return _("Multislice Alphabet Report") # on Citation Forms
    def dobuttonkwargs(self):
        return {'text':"Report!",
                'fn':self.do,
                # column=0,
                'font':'title',
                'compound':'bottom', #image bottom, left, right, or top of text
                'image':program['theme'].photo['VCCVRepcomp'],
                'sticky':'ew'
                }
    def __init__(self, parent): #frame, filename=None
        ReportCitation.__init__(self,parent)
        self.cvtstodo=['V','C','CV']
        MultisliceS.__init__(self)
class ReportConsultantCheck(Report,Tone,TaskDressing):
    """docstring for ReportCitationT."""
    def tasktitle(self):
        return _("Consultant Check")
    def taskicon(self):
        return program['theme'].photo['icontall']
    def tooltip(self):
        return _("This task automates work normally done before a consultant "
                "check: \n- reloads status data, and \n- runs comprehensive tone "
                "reports, \n  - by location and \n  - by lexeme sense.")
    def dobuttonkwargs(self):
        return {'text':"Start!\nProfiles first!",
                'fn':self.consultantcheck,
                # column=0,
                'font':'title',
                'compound':'bottom', #image bottom, left, right, or top of text
                'image':program['theme'].photo['icontall'],
                'sticky':'ew'
                }
    def __init__(self, parent): #frame, filename=None
        Tone.__init__(self)
        TaskDressing.__init__(self,parent)
        Report.__init__(self)
class ReportCitationT(Report,Tone,TaskDressing):
    """docstring for ReportCitationT."""
    def tasktitle(self):
        return _("Tone Report (not backgrounded)")
    def taskicon(self):
        return program['theme'].photo['iconTRep']
    def tooltip(self):
        return _("This report gives you report for one lexical "
                "category, in one syllable profile. \nIt does "
                "this for all data sorted in tone frames, organized by word.")
    def dobuttonkwargs(self):
        return {'text':"Report!",
                'fn':self.do,
                'font':'title',
                'compound':'bottom', #image bottom, left, right, or top of text
                'image':program['theme'].photo['TRep'],
                'sticky':'ew'
                }
    def __init__(self, parent):
        Tone.__init__(self)
        self.do=self.tonegroupreport
        TaskDressing.__init__(self,parent)
        Report.__init__(self)
        self.bylocation=False
class ReportCitationTBackground(Background,ReportCitationT):
    """docstring for ReportCitationT."""
    def tasktitle(self):
        return _("Tone Report")
    def taskicon(self):
        return program['theme'].photo['iconTRep']
    def tooltip(self):
        return _("This report gives you report for one lexical "
                "category, in one syllable profile. \nIt does "
                "this for all data sorted in tone frames.")
    def dobuttonkwargs(self):
        return {'text':"Report!",
                'fn':self.do,
                'font':'title',
                'compound':'bottom', #image bottom, left, right, or top of text
                'image':program['theme'].photo['TRep'],
                'sticky':'ew'
                }
    def __init__(self, parent):
        ReportCitationT.__init__(self,parent)
        Background.__init__(self)
class ReportCitationTL(ReportCitationT):
    """docstring for ReportCitationT."""
    def tasktitle(self):
        return _("Tone Report (by frames, not backgrounded)")
    def tooltip(self):
        return _("This report gives you report for one lexical "
                "category, in one syllable profile. \nIt does "
                "this for all data sorted in tone frames, organized by frame.")
    def __init__(self, parent):
        ReportCitationT.__init__(self,parent)
        self.bylocation=True
class ReportCitationTLBackground(Background,ReportCitationTL):
    """docstring for ReportCitationT."""
    def tasktitle(self):
        return _("Tone Report (by frames)")
    def taskicon(self):
        return program['theme'].photo['iconTRep']
    def tooltip(self):
        return _("This report gives you report for one lexical "
                "category, in one syllable profile. \nIt does "
                "this for all data sorted in tone frames, organized by frame.")
    def dobuttonkwargs(self):
        return {'text':"Report!",
                'fn':self.do,
                'font':'title',
                'compound':'bottom', #image bottom, left, right, or top of text
                'image':program['theme'].photo['TRep'],
                'sticky':'ew'
                }
    def __init__(self, parent):
        ReportCitationTL.__init__(self,parent)
        Background.__init__(self)
class ReportCitationMultisliceT(MultisliceT,ReportCitationT):
    """docstring for ReportCitationT."""
    def tasktitle(self):
        return _("Multislice Tone Report (not background)")
    def taskicon(self):
        return program['theme'].photo['iconTRepcomp']
    def tooltip(self):
        return _("This report gives you reports across multiple lexical "
                "categories, and across multiple syllable profiles. \nIt does "
                "this for all data sorted in tone frames, organized by word.")
    def dobuttonkwargs(self):
        return {'text':"Report!",
                'fn':self.do,
                'font':'title',
                'compound':'bottom', #image bottom, left, right, or top of text
                'image':program['theme'].photo['TRepcomp'],
                'sticky':'ew'
                }
    def __init__(self, parent):
        ReportCitationT.__init__(self,parent)
        MultisliceT.__init__(self)
class ReportCitationMultisliceTL(MultisliceT,ReportCitationTL):
    """docstring for ReportCitationT."""
    def tasktitle(self):
        return _("Multislice Tone Report (not background)")
    def taskicon(self):
        return program['theme'].photo['iconTRepcomp']
    def tooltip(self):
        return _("This report gives you reports across multiple lexical "
                "categories, and across multiple syllable profiles. \nIt does "
                "this for all data sorted in tone frames, organized by word.")
    def dobuttonkwargs(self):
        return {'text':"Report!",
                'fn':self.do,
                'font':'title',
                'compound':'bottom', #image bottom, left, right, or top of text
                'image':program['theme'].photo['TRepcomp'],
                'sticky':'ew'
                }
    def __init__(self, parent):
        ReportCitationTL.__init__(self,parent)
        MultisliceT.__init__(self)
class ReportCitationMultisliceTBackground(Background,ReportCitationMultisliceT):
    """docstring for ReportCitationT."""
    def tasktitle(self):
        return _("Multislice Tone Report")
    def taskicon(self):
        return program['theme'].photo['iconTRepcomp']
    def tooltip(self):
        return _("This report gives you reports across multiple lexical "
                "categories, and across multiple syllable profiles. \nIt does "
                "this for all data sorted in tone frames, organized by word.")
    def dobuttonkwargs(self):
        return {'text':"Report!",
                'fn':self.do,
                'font':'title',
                'compound':'bottom', #image bottom, left, right, or top of text
                'image':program['theme'].photo['TRepcomp'],
                'sticky':'ew'
                }
    def __init__(self, parent):
        ReportCitationMultisliceT.__init__(self,parent)
        Background.__init__(self)
class ReportCitationMultisliceTLBackground(Background,ReportCitationMultisliceTL):
    """docstring for ReportCitationT."""
    def tasktitle(self):
        return _("Multislice Tone Report (by location)")
    def taskicon(self):
        return program['theme'].photo['iconTRepcomp']
    def tooltip(self):
        return _("This report gives you reports across multiple lexical "
                "categories, and across multiple syllable profiles. \nIt does "
                "this for all data sorted in tone frames, organized by word.")
    def __init__(self, parent):
        ReportCitationMultisliceTL.__init__(self,parent)
        Background.__init__(self)
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
class Glosslangs(list):
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
        # log.info("Applying frame {} in these langs: {}".format(framedict,langs))
        # log.info("Using regex {}".format(rx.framerx))
        ftype=framedict['field']
        for l in [i for i in langs if i in framedict
                                    if i in self and self[i]
                                    if i != 'field'
                ]:
            # log.info("Using lang {}".format(l))
            if type(self[l]) is dict and ftype in self[l]:
                # log.info("Subbing {} into {}".format(self[l][ftype],framedict[l]))
                t=self[l][ftype]
            else:
                # log.info("Subbing {} into {}".format(self[l],framedict[l]))
                t=self[l]
            if self[l]:
                self.framed[l]=rx.framerx.sub(t,framedict[l])
            else:
                self.framed[l]=None
        # log.info("Applied frame: {}".format(self.framed))
    def __init__(self):
        super(DictbyLang, self).__init__()
        self.framed={}
class ExampleDict(dict):
    """This function finds examples in the lexicon for a given tone value,
    in a given tone frame (from check); thus, only sorted data."""
    def sensesinslicegroup(self,group,check):
        """Convert to senses before return"""
        #This returns all the senseids with a given tone value
        senses=program['taskchooser'].task.getsensesingroup(check,group)
        if not senses:
            log.error("There don't seem to be any sensids in this check tone "
                "group, so I can't get you an example. ({} {})"
                "".format(check,group))
            return
        """The above doesn't test for profile, so we restrict that next"""
        sensesinslice=program['slices'].inslice(senses)
        if not sensesinslice:
            log.error("There don't seem to be any sensids from that check tone "
                "group in this slice-group, so I can't get you an example. "
                "({}-{}, {} {})"
                "".format(program['slices'].ps(),program['slices'].profile(),check,group))
            return
        # return list(senseidsinslice)
        # return senses, not senseids
        return list(set(senses)&set(sensesinslice))
    def hasglosses(self,node):
        # log.info("hasglosses sense: {}".format(sense.id))
        try:
            return node.translation.textvaluedict()
        except AttributeError:
            return node.sense.glosses
    def hassoundfile(self,node):
        """sets self.audiofileisthere and maybe self.audiofileURL"""
        """You want to do this even if you don't need it, as this checks and
        marks the example"""
        return node.hassoundfile(program['params'].audiolang(),
                                program['settings'].audiodir)
    def exampletypeok(self,node,**kwargs):
        kwargs=exampletype(**kwargs)
        if not node:
            return
        # log.info("exampletypeok framed: {}".format(framed))
        if kwargs['wglosses'] and not self.hasglosses(node):
            log.info("Gloss check failed for {}".format(node.sense.id))
            return
        if not self.hassoundfile(node) and kwargs['wsoundfile']:
            log.info("Audio file check failed for {}".format(node.sense.id))
            return
        return True
    def getexample(self,group,**kwargs):
        check=program['params'].check()
        ftype=program['params'].ftype()
        if program['params'].cvt() == 'T': # example nodes
            nodes=[v.examples[check] for k,v in program['db'].sensedict.items()
                        if k in program['slices'].inslice(program['db'].sensedict)
                        if check in v.examples
                        if v.examples[check].tonevalue() == group
                        ]
        else: # Other FormParent nodes
            nodes=[v.ftypes[ftype] for k,v in program['db'].sensedict.items()
                        if k in program['slices'].inslice(program['db'].sensedict)
                        if ftype in v.ftypes
                        if v.ftypes[ftype].annotationvaluebylang(
                                                    program['params'].analang(),
                                                    check
                                                                ) == group
                    ]
        if not nodes:
            log.error("There don't seem to be any nodes in this "
                    "check-group/ftype-slice.")
            return 0,None
        # else:
        #     log.info("Found {} examples in the {} sort group for the {} check: "
        #             "{}.".format(len(senseids),group,check,senseids))
        n=len(nodes)
        tries=0
        node=None #do this once, anyway...
        """hasglosses sets the framed and senseid keys"""
        # log.debug("ExampleDict getexample kwargs: {}".format(kwargs))
        while not self.exampletypeok(node,**kwargs) and tries<n*2:
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
                log.info("group in self")
                if self[group] in nodes: #if stored value is in group
                    log.info("self[group] in examples")
                    if not kwargs['renew']:
                        log.info("Using stored value for ‘{}’ group: ‘{}’"
                                "".format(group, self[group]))
                        node=self[group]
                        #don't do this if clause more than once
                        kwargs['renew']=True
                    else:
                        log.info("renewing")
                        i=nodes.index(self[group])
                        if not kwargs.get('goback'):
                            log.info("not going back")
                            if i == len(nodes)-1: #loop back on last
                                node=nodes[0]
                            else:
                                node=nodes[i+1]
                        else:
                            log.info("going back")
                            if i == 0: #loop back on last
                                node=nodes[len(nodes)-1]
                            else:
                                node=nodes[i-1]
                        log.info("Using next value for ‘{}’ group: ‘{}’"
                                "".format(group, self[group]))
                else:
                    log.info("self[group] not in examples")
                    node=nodes[0] #randint(0, len(senseids))-1]
            elif n == 1:
                log.info("group not in self, one exemplaire")
                node=nodes[0]
            else:
                log.info("group not in self, multiple exemplaires")
                log.debug("n: {}".format(n))
                node=nodes[randint(0, n-1)]
            self[group]=node #store for next iteration
        if tries == n*2: #senseid is None: #not self.hasglosses(senseid):
            log.info("Apparently I tried for a senseid {} times, and couldn't "
            "find one matching your needs ({}) glosses (out of {} possible "
            "senses). This is probably a systematic problem to fix.".format(
                                                                tries,kwargs,n))
        else:
            self[group]=node #save for next time
            return len(nodes),node #self._outdict
    def __init__(self):
        super(ExampleDict, self).__init__({})
class MainApplication(ui.Window):
    def setmasterconfig(self): #,program
        """Configure variables for the root window (master)"""
        for rc in [0,2]:
            self.parent.grid_rowconfigure(rc, weight=3)
            self.parent.grid_columnconfigure(rc, weight=3)
    def __init__(self,parent,exit=0):
        start_time=nowruntime() #this enables boot time evaluation
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
        logfinished(start_time)
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
        if '=' in self.check:
            skiptext+=" ({})".format(self.check.replace('=','≠'))
        """This should just add a button, not reload the frame"""
        row+=10
        bf=ui.Frame(parent)
        bf.grid(column=0, row=row, sticky="w")
        if not program['status'].groups(wsorted=True):
            # log.info("Making None sorted yet button")
            vardict['ok']=ui.BooleanVar()
            okb=ui.Button(bf, text=firstOK,
                            cmd=firstok,
                            anchor="w",
                            font='instructions'
                            )
            okb.grid(column=0, row=0, sticky="ew")
        else:
            # log.info("Making different button")
            differentbutton()
        vardict['skip']=ui.BooleanVar()
        # log.info("Making skip button")
        skipb=ui.Button(bf, text=skiptext,
                        cmd=skip,
                        anchor="w",
                        font='instructions'
                        )
        skipb.grid(column=0, row=1, sticky="ew")
    def addgroupbutton(self,group):
        if self.exitFlag.istrue():
            return #just don't die
        if program['settings'].lowverticalspace:
            # log.info("using lowverticalspace for addgroupbutton")
            scaledpady=0
        else:
            scaledpady=int(40*program['scale'])
        b=SortGroupButtonFrame(self.groupbuttons, self,
                                group,
                                showtonegroup=True,
                                alwaysrefreshable=True,
                                bpady=0,
                                bipady=scaledpady,
                                row=self.groupbuttons.row,
                                column=self.groupbuttons.col,
                                sticky='w')
        if not b.hasexample:
            return
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
        groups=program['status'].groups(wsorted=True)
        for i in groups:
            try:
                values+=[int(i)]
            except:
                log.info('Tone group {} cannot be interpreted as an integer!'
                        ''.format(i))
        newgroup=max(values)+1
        groups.append(str(newgroup))
        program['status'].groups(groups,wsorted=True)
        program['status'].store()
        # log.info("Groups (appended): {}".format(groups))
        # log.info("Groups (appended): {}".format(program['status'].groups(wsorted=True)))
        return str(newgroup)
    def sortselected(self,sense):
        """Probably should just be sense"""
        selectedgroups=selected(self.groupvars)
        # log.info("selectedgroups: {}".format(selectedgroups))
        # for k in self.groupvars:
        #     log.info("{} value: {}".format(k,self.groupvars[k].get()))
        if len(selectedgroups)>1:
            log.error("More than one group selected: {}".format(
                                                            selectedgroups))
            return 2
        groupselected=unlist(selectedgroups)
        if groupselected in self.groupvars:
            self.groupvars[groupselected].set(False)
        else:
            log.error("selected {}; not in {}".format(groupselected,
                                                        self.groupvars))
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
                self.marksortgroup(sense,group)
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
                t = threading.Thread(target=self.marksortgroup,
                                    args=(sense,group),
                                    kwargs={
                                            'nocheck':True
                                            })
                t.start()
        else:
            log.debug('No group selected: {}'.format(groupselected))
            return 1 # this should only happen on Exit
        program['status'].marksenseidsorted(sense.id)
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
        self.task=task
        self.buttoncolumns=task.buttoncolumns
        self.marksortgroup=task.marksortgroup
        self.check=program['params'].check()
        self.maybewrite=program['taskchooser'].maybewrite
        # self.updatestatus=task.updatestatus
        for group in groups:
            self.addgroupbutton(group)
        """Children of self.runwindow.frame.scroll.content.anotherskip"""
        self.getanotherskip(self.content.anotherskip,self.groupvars)
        self._configure_canvas()
        log.info("getanotherskip vardict (1): {}".format(self.groupvars))
class RecordButtonFrame(ui.Frame):
    def _start(self, event):
        log.log(3,"Asking PA to record now")
        self.recorder=sound.SoundFileRecorder(self._filenameURL,self.pa,
                                            program['settings'].soundsettings)
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
        if file.exists(self._filenameURL):
            self.makeplaybutton()
            self.makedeletebutton()
            self.addlink()
        else:
            self.makerecordbutton()
    def makerecordbutton(self):
        self.b=ui.Button(self, command=self.function,
                        image='record',
                        ipadx=20, ipady=15
                        )
        self.b.grid(row=0, column=0,sticky='w')
        self.b.bind('<ButtonPress-1>', self._start)
        self.b.bind('<ButtonRelease-1>', self._stop)
        self.bt=ui.ToolTip(self.b,_("press-speak-release"))
    def _play(self,event=None):
        log.debug("Asking PA to play now")
        self.player=sound.SoundFilePlayer(self._filenameURL,self.pa,
                                            program['settings'].soundsettings)
        tryrun(self.player.play)
    def makeplaybutton(self):
        self.p=ui.Button(self, text='‣', command=self._play,
                        font='readbig',
                        ipadx=20, ipady=0
                        )
        #Not using these for now
        # self.p.bind('<ButtonPress>', self._play)
        # self.p.bind('<ButtonRelease>', self.function)
        self.p.grid(row=0, column=1,sticky='w')
        pttext=_("Click to hear")
        if program['praat']:
            pttext+='; '+_("right click to open in praat")
            self.p.bind('<Button-3>',lambda x: praatopen(self._filenameURL))
        self.pt=ui.ToolTip(self.p,pttext)
    def makedeletebutton(self):
        self.r=ui.Button(self,text='×',font='read',command=self.function,
                        row=0, column=2, sticky='nsw')
        self.r.bind('<ButtonRelease-1>', self._redo)
        self.rt=ui.ToolTip(self.r,_("Try again"))
        self.r.update_idletasks()
    def function(self):
        pass
    def addlink(self):
        if self.test:
            return
        program['db'].addmediafields(self.node,self.filename,
                                program['params'].audiolang,
                                # ftype=ftype,
                                write=False)
        self.task.maybewrite()
        program['status'].last('recording',update=True)
    def __init__(self,parent,task,node=None,**kwargs): #filenames
        """Uses node to make framed data, just for soundfile name"""
        """Without node, this just populates a sound file, with URL as
        provided. The LIFT link to that sound file should already be there."""
        # This class needs to be cleanup after closing, with check.donewpyaudio()
        """Originally from https://realpython.com/playing-and-recording-
        sound-python/"""
        self.id=id
        self.task=task
        try:
            task.pyaudio.get_format_from_width(1) #get_device_count()
        except:
            task.pyaudio=sound.AudioInterface()
        self.pa=task.pyaudio
        if not hasattr(program['settings'],'soundsettings'):
            task.loadsoundsettings()
        self.callbackrecording=True
        self.chunk = 1024  # Record in chunks of 1024 samples (for block only)
        self.channels = 1 #Always record in mono
        self.test=kwargs.pop('test',None)
        if node:# and framed.framed != 'NA':
            task.makeaudiofilename(node) #should fill out the following
            self.filename=node.textvaluebylang(program['params'].audiolang)
            if not self.filename: #should have above or below
                self.filename=node.audiofilenametoput
            self._filenameURL=node.audiofileURL
            self.node=node
        elif self.test:
            self.filename=self._filenameURL="test_{}_{}.wav".format(
                                program['settings'].soundsettings.fs,
                                program['settings'].soundsettings.sample_format)
        else:
            t=_("No framed value, nor testing; can't continue...")
            log.error(t)
            ui.Label(self,text=t,borderwidth=1,font='default',
                    relief='raised').grid(row=0,column=0)
        ui.Frame.__init__(self,parent, **kwargs)
        """These need to happen after the frame is created, as they
        might cause the init to stop."""
        if program['settings'].audiolang is None and self.test is not True:
            tlang=_("Set audio language to get record buttons!")
            log.error(tlang)
            ui.Label(self,text=tlang,borderwidth=1,
                relief='raised' #flat, raised, sunken, groove, and ridge
                ).grid(row=0,column=0)
            return
        if None in [program['settings'].soundsettings.fs,
                    program['settings'].soundsettings.sample_format,
                    program['settings'].soundsettings.audio_card_in,
                    program['settings'].soundsettings.audio_card_out]:
            text=_("Set all sound card settings"
                    "\n(Do|Recording|Sound Card Settings)"
                    "\nand a record button will be here.")
            log.debug(text)
            ui.Label(self,text=text,borderwidth=1,
                relief='raised' #flat, raised, sunken, groove, and ridge
                ).grid(row=0,column=0)
            return
        self.makebuttons()
class SortGroupButtonFrame(ui.Frame):
    def again(self):
        """Do I want this? something less drastic?"""
        for child in self.winfo_children():
            child.destroy()
        self.makebuttons()
        self.update_idletasks()
        if self.kwargs['playable'] and self._playable:
            self.player.play()
    def backup(self,event=None):
        log.info("Resetting tone group example ({}): {} of {} examples with "
                "kwargs: {}".format(self.group,self.exs[self.group],self._n,
                                                                self.kwargs))
        self.kwargs['goback']=True
        self.kwargs['alwaysrefreshable']=True
        self.getexample(**self.kwargs)
        self.again()
        self.kwargs['goback']=False #don't keep going on next
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
        self._n,node=self.exs.getexample(self.group,**kwargs)
        self.hasexample=False
        if not node:
            if kwargs['wsoundfile']:
                log.error("self.exs.getexample didn't return an example "
                                    "with a soundfile; trying for one without")
                kwargs['wsoundfile']=False
                self._n,node=self.exs.getexample(self.group,**kwargs)
                if not node:
                    log.error("self.exs.getexample didn't return an example "
                                        "with or without sound file; returning")
                    return
            else:
                log.error("self.exs.getexample didn't return an example "
                        "(without needing a sound file); returning ({})"
                        "".format(node))
                return
        self.hasexample=True
        """now example.audiofileURL"""
        if node.audiofileisthere:
            self._filenameURL=node.audiofileURL
        else:
            self._filenameURL=None
        self._text=node.formatted(program['taskchooser'].analang,
                                    program['taskchooser'].glosslangs,
                                    ftype=program['params'].ftype(),
                                    frame=program['toneframes'].get(
                                                program['params'].check()),
                                    showtonegroup=self.kwargs['showtonegroup'])
        self._illustration=node.sense.illustrationvalue()
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
        if hasattr(self,'_illustration'):
            b['image']=self._illustration
            b['compound']="left"
    def playbutton(self):
        self.check.pyaudiocheck()
        self.check.soundsettingscheck()
        self.player=sound.SoundFilePlayer(self._filenameURL,self.check.pyaudio,
                                            program['settings'].soundsettings)
        b=ui.Button(self, text=self._text,
                    cmd=self.player.play,
                    column=1, row=0,
                    sticky="nesw",
                    **self.buttonkwargs())
        if hasattr(self,'_illustration'):
            b['image']=self._illustration
            b['compound']="left"
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
        if hasattr(self,'_illustration'):
            b['image']=self._illustration
            b['compound']="left"
        bt=ui.ToolTip(b,_("Pick this group ({})").format(self.group))
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
        bc.bind('<ButtonRelease-3>',self.backup)
        bct=ui.ToolTip(bc,text=_("Change example word; Right click to back up"))
    def unsortbutton(self):
        t=_("<= resort *this* *word*")
        usbkwargs=self.buttonkwargs()
        usbkwargs['wraplength']=usbkwargs['wraplength']*2/3
        b_unsort=ui.Button(self,text = t,
                            cmd=self.unsort,
                            column=2,row=0,#padx=50,
                            **usbkwargs
                            )
    def buttonkwargs(self):
        """This is a method to allow pulling these args after updating kwargs"""
        bkwargs=self.kwargs.copy()
        for arg in self.unbuttonargs:
            del bkwargs[arg]
        return bkwargs #only the kwargs appropriate for buttons
    def __init__(self, parent, check, group, **kwargs):
        log.info("Initializing buttons for group {}".format(group))
        self.exs=program['examples']
        self.check=check #the task/check OR the scrollingframe! use self.check.task
        self.group=group
        # self,parent,group,row,column=0,label=False,canary=None,canary2=None,
        # alwaysrefreshable=False,playable=False,renew=False,unsortable=False,
        # **kwargs
        # From check, need
        # check=program['params'].check()
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
                            'goback'
                            ]
        for arg in self.unbuttonargs:
            kwargs[arg]=kwargs.pop(arg,False)
        if kwargs['playable']:
            kwargs['wsoundfile']=True
        #set this for buttons:
        if program['settings'].lowverticalspace:
            log.info("using lowverticalspace for SortGroupButtonFrame")
            maxpad=0
        else:
            maxpad=15
        kwargs['ipady']=kwargs.pop('bipady',defaults.get('bipady',maxpad))
        kwargs['ipadx']=kwargs.pop('bipadx',defaults.get('bipadx',maxpad))
        kwargs['pady']=kwargs.pop('bpady',defaults.get('bpady',0))
        kwargs['padx']=kwargs.pop('bpadx',defaults.get('bpadx',0))
        self.kwargs=kwargs
        self._var=ui.BooleanVar()
        super(SortGroupButtonFrame,self).__init__(parent, **frameargs)
        if self.getexample(**kwargs):
            self.makebuttons()
        # """Should I do this outside the class?"""
        # self.grid(column=column, row=row, sticky=sticky)
class ImageFrame(ui.Frame):
    def getimage(self,reload=False):
        specifiedurl=False
        compiled=False
        if self.url and file.exists(self.url):
            i=self.url
            specifiedurl=True
        elif isinstance(self.sense,lift.Sense):
            if (hasattr(self.sense,'img')
                    and isinstance(self.sense.img,ui.Image)
                    and not reload):
                log.info("Found Image, using")
                img=self.sense.img
                compiled=True
            else:
                i=self.sense.illustrationvalue()
                for d in [program['settings'].imagesdir,program['settings'].directory]:
                    if i and d:
                        di=file.getdiredurl(d,i)
                        if file.exists(di):
                            i=di
                            break
        # log.info("trying to make image @{}".format(self.sense.illustration.valuename))
        # lift.prettyprint(self.sense.illustration)
        if not compiled:
            try:
                # log.info("trying to make image {}".format(i))
                img=ui.Image(i)
                self.hasimage=True
                # log.info("Image OK: {}".format(img))
            except tkinter.TclError as e:
                if ('value for "-file" missing' not in e.args[0] and
                        "couldn't recognize data in image file" not in e.args[0]):
                    log.info("ui.Image error: {}".format(e))
                img=self.theme.photo['NoImage']
                self.hasimage=False
                # log.info("Image null: {}".format(img))
            if not specifiedurl:
                self.sense.img=img
        # log.info("Image: {}".format(img))
        img.scale(program['scale'],pixels=self.pixels,resolution=self.resolution)
        self.image=img.scaled
    def pluralframe(self):
        ui.Label(self,text='',image=self.image,
                compound="bottom",
                sticky='e',
                ipadx=10,
                row=0,column=0)
        ui.Label(self,text='',image=self.image,
                compound="bottom",
                sticky='w',
                ipadx=10,
                row=0,column=1)
    def imperativeframe(self):
        try:
            image1=program['theme'].photo['Order!']
            image1.scale(program['scale'],pixels=300,resolution=10) #300 wide
            image2=self.image
            # log.info("image1.scaled: {} ({})".format(image1.scaled,type(image1.scaled)))
            # log.info("image2: {} ({})".format(image2,type(image2)))
            image1.scaled.paste(image2)
            bgl=ui.Label(verb,text='',image=image1.scaled,
                compound="center",
                sticky='ew',
                row=0,column=0)
        except:
            ui.Label(self,text='!',image=self.image,
                compound="left",sticky='ew',font='title',
                row=0,column=0)
    def citationframe(self):
        l=ui.Label(self,text='',image=self.image,
            compound="center",sticky='ew',
            anchor='center',
            row=0,column=0)
        # log.info(l.grid_info())
    def changesense(self,sense):
        if self.sense != sense:
            self.sense=sense
            self.reloadimage()
    def reloadimage(self):
        self.getimage(reload=True)
        for child in self.winfo_children():
            if isinstance(child,ui.Label):
                child['image']=self.image
    def __init__(self, parent, sense=None, *args, **kwargs):
        """Parent: where it goes; Sense: what it shows"""
        if not isinstance(sense,lift.Sense) and 'url' not in kwargs:
            log.error("ImageFrame called without sense or url!")
            return
        self.sense=sense
        #These shouldn't go to frame:
        self.url=kwargs.pop('url',None)
        self.ftype=kwargs.pop('ftype',None)
        self.pixels=kwargs.pop('pixels',150)
        self.resolution=kwargs.pop('resolution',10)
        super(ImageFrame, self).__init__(parent, *args, **kwargs)
        self.getimage()
        if self.ftype == 'pl':
            self.pluralframe()
        elif self.ftype == 'imp':
            self.imperativeframe()
        else:
            self.citationframe()
class Splash(ui.Window):
    def maketexts(self):
        self.labels['v']['text']=_("Version: {}".format(program['version']))
        self.labels['text']['text']=_("Your dictionary database is loading...\n"
                "\n{name} is a computer program that accelerates community"
                "-based language development by facilitating the sorting of a "
                "beginning dictionary by vowels, consonants and tone. "
                "(more in help:about)").format(name=program['name'])
        self.labels['titletext']['text']=(_("{name} Dictionary and Orthography "
                                        "Checker").format(name=program['name']))
        self.update_idletasks()
    def draw(self):
        # self.update_idletasks()
        # self.update()
        self.deiconify() #show after placement
    def progress(self,value):
        self.progressbar.current(value)
    def __init__(self, parent):
        try:
            parent.withdraw()
            noparent=False
        except AttributeError:
            parent=program['root']
        super(Splash, self).__init__(parent,exit=0)
        self.withdraw() #don't show until placed
        self.labels={'titletext':ui.Label(self.frame, text='', pady=10,
                        font='title',anchor='c',padx=25,
                        row=0,column=0,sticky='we'
                        ),
                        'v':ui.Label(self.frame, text='', anchor='c',padx=25,
                        row=1,column=0,sticky='we'
                        ),
                        'photo':ui.Label(self.frame, image=self.theme.photo['transparent'],text='',
                        row=2,column=0,sticky='we'
                        ),
                        'text':ui.Label(self.frame, text='', padx=50,
                                    wraplength=int(self.winfo_screenwidth()/2),
                                    row=3,column=0,sticky='we'
                                    )
                    }
        self.maketexts()
        self.title(self.labels['titletext']['text'])
        self.progressbar=ui.Progressbar(self.frame,
                                orient='horizontal',
                                mode='determinate', #or 'indeterminate'
                                row=4,column=0)
        self.w = self.winfo_reqwidth()
        x=int(self.master.winfo_screenwidth()/2-(self.w/2))
        self.h = self.winfo_reqheight()
        y=int(self.master.winfo_screenheight()/2 -(self.h/2))
        self.geometry('+%d+%d' % (x, y))
        self.labels['v'].bind('<Button-1>', lambda e,x=self:updateazt(parent=x))
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
                group=program['db'].get("example/tonefield/form/text",
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
            self.valuesbygroupcheck[name]=ofromstr(k) #return str to dict
            # self.groups[name]['senseids']=unnamed[k]
            self.senseidsbygroup[name]=unnamed[k]
            for senseid in unnamed[k]:
                program['db'].addtoneUF(senseid,name,analang=self.analang,
                                    write=False)
        # log.info("Done adding senseids to groups.")
        # return self.groups
    def tonegroupsbyUFcheckfromLIFT(self):
        #returns dictionary keyed by [group][location]=groupvalue
        values=self.valuesbygroupcheck={}
        # Collect check:value correspondences, by sense
        for group in self.senseidsbygroup:
            values[group]={}
            for senseid in self.senseidsbygroup[group]:
                sense=program['db'].sensedict[senseid]
                for check in sense.examples:
                    try:
                        values[group][check].add(sense.tonevaluebyframe(check))
                    except KeyError:
                        values[group][check]=set([sense.tonevaluebyframe(check)])
            #maybe need this:
            for check in values[group]:
                values[group][check]=[i for i in values[group][check] if i]
            # log.info("values[{}][{}]: {}".format(group,check,
            #                                     values[group][check]))
        # log.info("Done collecting groups by location/check for each UF group.")
    def senseidsbyUFsfromLIFT(self):
        """This returns a dict of {UFtonegroup:[senseids]}"""
        log.debug(_("Looking for sensids by UF tone groups for {}-{}").format(
                    self.profile, self.ps
                    ))
        self.senseidsbygroup={}
        """Still working on one ps-profile combo at a time."""
        for senseid in self.senseids: #I should be able to make this a regex...
            group=firstoflist(program['db'].get('sense/toneUFfield/form/text',
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
        program['db'].write()
        self.doanyway()
        program['status'].last('analysis',update=True)
    def doanyway(self):
        """compare(x=UFs/checks) give self.comparison(x) and self.ordered(x)"""
        self.comparechecks() #also self.valuesbygroupcheck -> …checkgroup
        self.compareUFs()
        self.allvaluesbycheck() # >self.valuesbycheck
        self.allvaluesbygroup() # >self.valuesbygroup
    def setslice(self,**kwargs):
        self.ps=kwargs.get('ps',program['slices'].ps())
        self.profile=kwargs.get('profile',program['slices'].profile())
        self.checks=program['status'].checks(ps=self.ps,profile=self.profile)
        self.senseids=program['slices'].senseids(ps=self.ps,profile=self.profile)
    def __init__(self, **kwargs):
        super(Analysis, self).__init__()
        self.analang=program['params'].analang()
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
        if not pss:
            self._ps=None #only before data collection
            log.info("I don't have a ps to use; I hope that's OK!")
        elif not hasattr(self,'_ps') or self._ps not in pss:
            self.ps(pss[0])
    def makeprofileok(self):
        if not hasattr(self,'_ps'):
            self.makepsok()
        profiles=self.profiles()
        if not profiles:
            self._profile=None #only before data collection
            log.info("I don't have a profile to use; I hope that's OK!")
            return
        try:
            profiles+=self.adhoc()[self._ps].keys()
        except KeyError:
            log.info("There seem to be no ad hoc {} groups.".format(self._ps))
        if (not hasattr(self,'_profile')
                or self._profile not in profiles):
            self.profile(profiles[0])
    def pss(self):
        return getattr(self,'_pss',[])
    def ps(self,ps=None):
        pss=self.pss()
        if ps and ps in pss:
            """This needs to renew checks, if t == 'T'"""
            self._ps=ps
            self.makeprofileok() #keyed by ps
            self.renewsenseids()
        elif ps:
            log.error("You asked to change to ps {}, which isn't in the list "
                        "of pss: {}".format(ps,pss))
        elif hasattr(self,'_ps'):
            return self._ps
        else:
            log.error("You asked for the ps, but I do't have any (pss: {})"
                        "".format(pss))
    def profiles(self,ps=None):
        """This returns profiles for either a specified ps or the current one"""
        if not ps:
            ps=self.ps()
        if ps:
            # log.info("returning profiles: {}".format(self._profiles[ps]))
            return self._profiles[ps]
        else:
            return []
    def profile(self,profile=None):
        if profile and profile in self.profiles(self._ps):
            self._profile=profile
            self.renewsenseids()
        else:
            # self.makeprofileok() #is this actually needed here? check elsewhere
            return getattr(self,'_profile',None)
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
            # log.info("self._slicepriority: {}".format(self._slicepriority))
            # log.debug("self._valid: {}".format(self._valid))
            for ps in dict.fromkeys([x[1] for x in self._valid]):
                s=self._sliceprioritybyps[ps]=[x for x in self._valid.items()
                                                            if x[0][1] == ps]
                s.sort(key=lambda x: int(x[1]),reverse=True)
                # log.info("self._sliceprioritybyps[{}]: {}"
                #             "".format(ps,self._sliceprioritybyps[ps]))
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
        #These are keyed by (profile,ps) tuples
        self._valid={}
        self._validbyps={}
        # log.info("slices: {} ({})".format(len(self),list(self)[:10]))
        for k in [x for x in self if x[0] != 'Invalid']:
            self._valid[k]=self[k]
        # log.info("slices valid: {} ({})".format(len(self._valid),
        #                                         list(self._valid)[:10]))
        for ps in dict.fromkeys([x[1] for x in self._valid]):
            self._validbyps[ps]=[x for x in self._valid if x[1] == ps]
        # log.info("slices validbyps: {} ({})".format(len(self._validbyps),
        #                                             list(self._validbyps)[:10]))
        # log.info("valid: {}".format(self._valid))
        # log.info("validbyps: {}".format(self._validbyps))
    def inslice(self,s):
        if isinstance(s,lift.Sense):
            return set(self._senses).intersection(s)
        else:
            senseidstochange=set(self._senseids).intersection(s)
            return senseidstochange
    def senses(self,**kwargs): #ps=None,profile=None,
        if not ps and not profile:
            return self._senses #this is always the current slice
        ps=kwargs.get('ps',self._ps)
        profile=kwargs.get('profile',self._profile)
        if ps in self._profilesbysense and profile in self._profilesbysense[ps]:
            return [program['db'].sensedict[i]
                        for i in self._profilesbysense[ps][profile]]
            # return list(self._profilesbysense[ps][profile]) #specified slice
        else:
            return []
    def senseids(self,**kwargs): #ps=None,profile=None,
        """This returns an up to date list of senseids in the curent slice
        (because changing ps or profile calls renewsenseids), or else the
        specified slice"""
        # list(self._senseidsbyps[self._ps][self._profile])
        if 'ps' not in kwargs and 'profile' not in kwargs:
            return self._senseids #this is always the current slice
        ps=kwargs.get('ps',self._ps)
        profile=kwargs.get('profile',self._profile)
        if ps in self._profilesbysense and profile in self._profilesbysense[ps]:
            return list(self._profilesbysense[ps][profile]) #specified slice
        else:
            return []
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
        self._senses=[program['db'].sensedict[i] for i in self._senseids]
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
                else:
                    count=len(self._profilesbysense[ps][profile])
                    wcounts.append((count, profile, ps))
        for i in sorted(wcounts,reverse=True):
            self[(i[1],i[2])]=i[0] #[(profile, ps)]=count
        e="Found {} valid data slices: {}".format(len(wcounts),self.keys())
        e+='\n'+"Invalid entries found: {}/{}".format(profilecountInvalid,
                                                        sum(self.values(),
                                                        profilecountInvalid))
        if program['db'].analangs and not len(wcounts):
            e+='\n'+"This may be a problem with your analysis language: {}".format(
            program['params'].analang())
            e+='\n'+"Or a problem with your database."
            ErrorNotice(e,title="Data Problem!",wait=True)
        log.info(e)
    def __init__(self,adhoc,profilesbysense): #dict
        """The slice dictionary depends on check parameters (and not vice versa)
        because changes in slice options (ps or profile) change check options,
        and not vice versa (check options are only presented based on current
        cvt and slice)"""
        program['slices']=self
        super(SliceDict, self).__init__()
        self.profilecountsValid=0
        self.profilecounts=0
        self.maxprofiles=None
        self.maxpss=None
        self._adhoc=adhoc
        self.analang=profilesbysense['analang']
        self._profilesbysense={k:v for k,v in profilesbysense.items()
                                                if k not in ['analang','ftype']}
        if not self._profilesbysense:
            ErrorNotice(_("There doesn't seem to be any profile data, but "
                        "you asked for a slice dictionary. This is a problem; "
                        "please report it!"))
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
    #def write
    def source(self,dict=None):
        if dict:
            updated=False
            for ps in dict:
                self[ps]=dict[ps]
                for name in self[ps]:
                    try:
                        if 'field' not in self[ps][name]:
                            updated=True
                            self[ps][name]['field']='lc'
                    except TypeError as e:
                        log.info("problem with frame at ps:{}, name:{} ({})"
                                "".format(ps,name,e))
            if updated:
                log.info("updated toneframes for field; you should save it!")
        return self
    def __init__(self, dict):
        program['toneframes']=self
        super(ToneFrames, self).__init__()
        self.source(dict)
class StatusDict(dict):
    """This stores and returns current ps and profile only; there is no check
    here that the consequences of the change are done (done in check)."""
    """I should think about what 'do' means here: sort? verify? record?"""
    def task(self,task=None):
        if task:
            self._task=task
        else:
            return self._task
    def checktosort(self,**kwargs):
        check=kwargs.get('check',program['params'].check())
        cvt=kwargs.get('cvt',program['params'].cvt())
        ps=kwargs.get('ps',program['slices'].ps())
        profile=kwargs.get('profile',program['slices'].profile())
        if (cvt not in self or
                ps not in self[cvt] or
                profile not in self[cvt][ps] or
                check not in self[cvt][ps][profile] or
                self[cvt][ps][profile][check]['tosort'] == True):
            return True
    def checktojoin(self,**kwargs):
        check=kwargs.get('check',program['params'].check())
        cvt=kwargs.get('cvt',program['params'].cvt())
        ps=kwargs.get('ps',program['slices'].ps())
        profile=kwargs.get('profile',program['slices'].profile())
        if (cvt in self and
                ps in self[cvt] and
                profile in self[cvt][ps] and
                check in self[cvt][ps][profile] and
                ('tojoin' not in self[cvt][ps][profile][check] or #old schema
                self[cvt][ps][profile][check]['tojoin'] == True)):
            return True
    def profiletojoin(self,**kwargs):
        profile=kwargs.get('profile',program['slices'].profile())
        cvt=kwargs.get('cvt',program['params'].cvt())
        ps=kwargs.get('ps',program['slices'].ps())
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
        profile=kwargs.get('profile',program['slices'].profile())
        cvt=kwargs.get('cvt',program['params'].cvt())
        ps=kwargs.get('ps',program['slices'].ps())
        checks=self.checks()
        for check in checks: #any check
            if (cvt not in self or
                ps not in self[cvt] or
                profile not in self[cvt][ps] or
                check not in self[cvt][ps][profile] or
                self[cvt][ps][profile][check]['tosort'] == True):
                return True
    def nextprofile(self, event=None, **kwargs):
        """This function is here (not in slices) in order for it to be sensitive
        to different kinds of profiles, via **kwargs"""
        # log.info("Running nextprofile")
        kwargs=grouptype(**kwargs)
        # self.makeprofileok()
        profiles=self.profiles(**kwargs)
        if not profiles:
            log.error("There are no such profiles! kwargs: {}".format(kwargs))
            return
        """"TypeError: string indices must be integers"""
        profile=program['slices'].profile()
        nextprofile=profiles[0]
        if profile in profiles:
            idx=profiles.index(profile)
            if idx != len(profiles)-1:
                nextprofile=profiles[idx+1]
        program['slices'].profile(nextprofile)
        return True
    def nextcheck(self, event=None, **kwargs):
        kwargs=grouptype(**kwargs)
        check=program['params'].check()
        checks=self.checks(**kwargs)
        if not checks:
            log.error("There are no such checks! kwargs: {}".format(kwargs))
            return
        nextcheck=checks[0] #default
        if check in checks:
            idx=checks.index(check)
            if idx != len(checks)-1: # i.e., not already last
                nextcheck=checks[idx+1] #overwrite default in this one case
        program['params'].check(nextcheck)
        return True
    def nextgroup(self, **kwargs):
        kwargs=grouptype(**kwargs)
        group=self.group()
        groups=self.groups(**kwargs)
        log.info("At {} of ({}) groups.".format(group,groups))
        if not groups:
            log.error("There are no such groups! kwargs: {}".format(kwargs))
            return
        nextgroup=groups[0] #default
        if group in groups:
            idx=groups.index(group)
            if idx != len(groups)-1: # i.e., not already last
                nextgroup=groups[idx+1] #overwrite default in this one case
        self.group(nextgroup)
        group=self.group()
        log.info("At {} of ({}) groups.".format(group,groups))
    def profiles(self, **kwargs):
        kwargs=grouptype(**kwargs)
        profiles=program['slices'].profiles() #already limited to current ps
        p=[]
        for kwargs['profile'] in profiles:
            checks=self.checks(**kwargs)
            if kwargs['wsorted'] and not checks:
                log.log(4,"No Checks for this profile, returning.")
                continue #you won't find any profiles to do, either...
            if (
                (not kwargs['wsorted'] and not kwargs['tosort']
                and not kwargs['toverify'] and not kwargs['tojoin']
                ) or
                (kwargs['tosort'] and self.profiletosort(**kwargs)) or
                (kwargs['wsorted'] and [i for j in
                            # [self.groups(profile=profile,check=check,**kwargs)
                            [self.groups(**kwargs)
                            # for check in checks]
                            for kwargs['check'] in checks]
                                        for i in j
                                        ]) or
                (kwargs['toverify'] and [i for j in
                            # [self.groups(profile=profile,check=check,**kwargs)
                            [self.groups(**kwargs)
                            # for check in checks]
                            for kwargs['check'] in checks]
                                        for i in j
                                        ]) or
                kwargs['tojoin'] and self.profiletojoin(**kwargs)
                ):
                p+=[kwargs['profile']]
        # log.info("Profiles with kwargs {}: {}".format(kwargs,p))
        return p
    def checks(self, **kwargs):
        """This method is designed for tone, which depends on ps, not profile.
        we'll need to rethink it, when working on CV checks, which depend on
        profile, and not ps."""
        kwargs=grouptype(**kwargs)
        tosortkwargs=kwargs.copy()
        tosortkwargs['tosort']=True
        toverifykwargs=kwargs.copy()
        toverifykwargs['toverify']=True
        tojoinkwargs=kwargs.copy()
        tojoinkwargs['tojoin']=True
        cs=[]
        checks=self.updatechecksbycvt(**kwargs)
        if isinstance(self.task(),Sort) or isinstance(self.task(),Transcribe):
            checks=[i for i in checks if 'x' not in i]
        for kwargs['check'] in checks:
            tosortkwargs['check']=toverifykwargs['check']=tojoinkwargs['check']=kwargs['check']# log.info("{} tosort: {}".format(kwargs['check'],self.checktosort(**tosortkwargs)))
            # log.info("{} tosort: {}".format(kwargs['check'],self.groups(**toverifykwargs)))
            # log.info("{} tosort: {}".format(kwargs['check'],self.checktojoin(**tojoinkwargs)))
            if (
                (not kwargs['wsorted'] and not kwargs['tosort']
                and not kwargs['toverify']
                and not kwargs['tojoin']
                and not kwargs['todo']
                ) or
                # """These next two assume current ps-profile slice"""
                kwargs['wsorted'] and self.groups(**kwargs) or
                kwargs['tosort'] and self.checktosort(**kwargs) or
                kwargs['toverify'] and self.groups(**kwargs) or
                kwargs['tojoin'] and self.checktojoin(**kwargs) or
                    (kwargs['todo'] and (self.checktosort(**tosortkwargs) or
                                        self.groups(**toverifykwargs) or
                                        self.checktojoin(**tojoinkwargs)
                                        )
                    )
                ):
                cs+=[kwargs['check']]
        # log.info("Checks with {}: {}".format(kwargs,cs))
        return cs
    def groups(self,g=None, **kwargs): #was groupstodo
        # log.info("groups kwargs: {}".format(kwargs))
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
            return sorted(self._groups)
        if kwargs['toverify']:
            return sorted(set(sn['groups'])-set(sn['done']))
        if kwargs['torecord']:
            return sorted(set(sn['groups'])-set(sn['recorded']))
        else: #give theoretical possibilities (C or V only)
            """The following two are meaningless, without with kwargs above"""
            if kwargs['cvt'] in ['CV','VC','T']:
                return None
            """This is organized class:(segment,count)"""
            thispsdict=program['slices'].scount()[kwargs['ps']]
            if kwargs['cvt'] == 'V': #There is so far only one V grouping
                todo=[i[0] for i in thispsdict['V']] #that's all that's there, for now.
            elif kwargs['cvt'] == 'C':
                todo=list() #because there are multiple C groupings
                for s in thispsdict:
                    if s != 'V':
                        todo.extend([i[0] for i in thispsdict[s]])
            todo=sorted(set(todo)|set(sn['groups'])) #either way, add current groups
            # log.info("Returning groups: {}".format(todo))
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
    def marksenseidsorted(self,senseid,**kwargs):
        self._idssorted.append(senseid)
        if senseid in self._idstosort:
            self._idstosort.remove(senseid)
        if not self._idstosort:
            self.tosort(False,**kwargs) #this marks current, unless specified
            # log.info("Tosort now {} (marksenseidsorted)".format(self.tosort()))
    def marksenseidtosort(self,senseid,**kwargs):
        # if not hasattr(self,'_idstosort') or not self._idstosort:
        self._idstosort.append(senseid)
        if senseid in self._idssorted:
            self._idssorted.remove(senseid)
        self.tosort(True,**kwargs) #this marks current, unless specified
        # log.info("Tosort now {} (marksenseidtosort)".format(self.tosort()))
    def store(self):
        """This will just store to file; reading will come from check."""
        log.info("Saving status dict to file")
        config=ConfigParser()
        # config.read(self._filename,encoding='utf-8')
        # if config != self:
        #     log.info("config: {}".format(config.keys()))
        #     log.info("self: {}".format(self.keys()))
        config['status']=indenteddict(self) #getattr(o,s)
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
            return
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
        # if changed == True:
        #     self.store()
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
        # log.info("Running updatechecksbycvt")
        cvt=kwargs.get('cvt',program['params'].cvt())
        if cvt not in self._checksdict:
            self._checksdict[cvt]={}
            self.renewchecks(**kwargs)
        if cvt == 'T':
            """This depends on ps and program['toneframes']"""
            ps=kwargs.get('ps',program['slices'].ps())
            if ps not in self._checksdict[cvt]:
                self._checks=[] #there may be none defined
            else:
                self._checks=self._checksdict[cvt][ps]
        else:
            profile=kwargs.get('profile',program['slices'].profile())
            if profile not in self._checksdict[cvt]:
                self.renewchecks(**kwargs) #should be able to find something
            self._checks=self._checksdict[cvt][profile]
        # log.info("Returning these checks: {}".format(self._checks))
        return self._checks
    def renewchecks(self,**kwargs):
        """This should only need to be done on a boot, when a new tone frame
        is defined, or when working on a new syllable profile for CV checks."""
        """This depends on cvt and profile, for CV checks"""
        """replaces self.checkspossible"""
        """replaces setnamesbyprofile"""
        # log.info("Running renewchecks")
        cvt=kwargs.get('cvt',program['params'].cvt())
        # t=program['params'].cvt()
        if not cvt:
            log.error("No type is set; can't renew checks!")
        if cvt not in self._checksdict:
            self._checksdict[cvt]={}
        if cvt == 'T':
            for ps in program['slices'].pss():
                if ps in program['toneframes']:
                    self._checksdict[cvt][ps]=list(program['toneframes'][ps])
        else:
            """This depends on profile only"""
            profile=kwargs.get('profile',program['slices'].profile())
            n=profile.count(cvt)
            # log.debug('Found {} instances of {} in {}'.format(n,cvt,profile))
            self._checksdict[cvt][profile]=list()
            for i in range(n): # get max checks and lesser
                if i+1 >6:
                    log.info("We aren't doing checks with more than 6 "
                            "consonants or vowels ({} in {}); If you need "
                            "that, please let me know.".format(i+1,profile))
                    continue
                """This is a list of (code, name) tuples"""
                syltuples=program['params']._checknames[cvt][i+1] #range+1 = syl
                self._checksdict[cvt][profile].extend([t[0] for t in syltuples])
                # log.info("Check codes to date: {}".format(
                #                                 self._checksdict[cvt][profile]
                #                                         ))
            self._checksdict[cvt][profile].sort(key=len,reverse=True)
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
    def update(self,group=None,verified=False,writestatus=True):
        """This function updates the status variable, not the lift file."""
        changed=False
        if group is None:
            group=self.group()
        # log.info("Verification before update (verifying {} as {}): {}".format(
        #                                         group,verified,self.verified()))
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
        if writestatus and changed:
            self.store()
        # log.info("Verification after update: {}".format(self.verified()))
        return changed
    def group(self,group='<unspecified>'):
        """This maintains the group we are actually on, pulled from data
        located by current slice and parameters"""
        if group != '<unspecified>': #this needs to be able to be specified None
            self._group=group
        else:
            return getattr(self,'_group',None)# this needs to be booleanable
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
        cvt=program['params'].cvt()
        cvts=program['params'].cvts()
        if cvt not in cvts:
            program['params'].cvt(cvts[0])
    def makecheckok(self, **kwargs): #result None w/no checks
        check=program['params'].check()
        checks=self.checks(**kwargs)
        if check not in checks:
            if checks:
                program['params'].check(checks[0])
            else:
                program['params'].check(unset=True)
    def toneframedefn(self):
        d=program['toneframes'][program['slices'].ps()][program['params'].check()]
        return d
    def checkslicetypecurrent(self,**kwargs):
        """This fills in current values; it shouldn't leave None anywhere."""
        i=kwargs.copy()
        for k,v in i.items():
            if v is None:
                del kwargs[k]
        kwargs['cvt']=kwargs.get('cvt',program['params'].cvt())
        kwargs['ps']=kwargs.get('ps',program['slices'].ps())
        kwargs['profile']=kwargs.get('profile',program['slices'].profile())
        kwargs['check']=kwargs.get('check',program['params'].check())
        log.log(4,"Returning checkslicetypecurrent kwargs {}".format(kwargs))
        return kwargs
    def last(self,task,update=False,**kwargs):
        sn=self.node(**kwargs)
        if 'last' not in sn:
            sn['last']={}
        if update:
            sn['last'][task]=now()
        if kwargs.get('write'):
            self.store()
        if task in sn['last']:
            return sn['last'][task]
    def isanalysisOK(self,**kwargs):
        a=self.last('analysis',**kwargs)
        s=self.last('sort',**kwargs)
        j=self.last('joinUF',**kwargs)
        if a and s:
            ok=a>s
        elif a:
            ok=True # b/c analysis would be more recent than last sorting
        else:
            ok=False # w/o info, trigger reanalysis
        if ok and j and j > a:
            joinsinceanalysis=True #show groups on all non-default reports
        else:
            joinsinceanalysis=False
        annalysisoknotice=("Last analysis at {};\n"
                    "last join at {}\n"
                    "last sort at {}\n(analysisOK={})"
                    "".format(a,j,s,ok))
        log.info(annalysisoknotice)
        return ok, joinsinceanalysis, annalysisoknotice
    def source(self,dict=None):
        if dict:
            for k in [i for i in dict if i is not None]:
                self[k]=dict[k]
        return self
    def __init__(self,filename,dict):
        """To populate subchecks, use self.groups()"""
        program['status']=self
        self._filename=filename
        self._task=program.get('defaulttask',WordCollectnParse)
        super(StatusDict, self).__init__()
        self.source(dict)
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
        try:
            return self._cvchecknames[code]
        except KeyError:
            return None
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
    def audiolang(self,audiolang=None):
        if audiolang:
            self._audiolang=audiolang
        elif not hasattr(self,'_audiolang'):
            self._audiolang=None
        return self._audiolang
    def ftype(self,ftype=None):
        if ftype:
            self._ftype=ftype
        elif not hasattr(self,'_ftype'):
            self._ftype='lc'
        return self._ftype
    def __init__(self,analang,audiolang): # had, do I need check? to write?
        program['params']=self
        """replaces setnamesall"""
        """replaces self.checknamesall"""
        super(CheckParameters, self).__init__()
        self._analang=analang
        self._audiolang=audiolang
        self._cvts={
                'V':{'sg':_('Vowel'),'pl':_('Vowels')},
                'C':{'sg':_('Consonant'),'pl':_('Consonants')},
                'CV':{'sg':_('Consonant-Vowel combination'),
                        'pl':_('Consonant-Vowel combinations')},
                'VC':{'sg':_('Vowel-Consonant combination'),
                        'pl':_('Vowel-Consonant combinations')},
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
                    ("CxV1", _("Correspondence of first CV")),
                    # ("CV1", "First/only CV")
                    ],
                2:[
                    # ("CV2", "Second CV"),
                    ("CxV2", _("Correspondence of second CV")),
                    ("CV1=CV2",_("Same First/only Two CVs")),
                    # ("CV2#", "Word-final CV")
                    ],
                3:[
                    ("CxV3", _("Correspondence of third CV")),
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
            "VC":{
                1:[
                    ("VxC1", _("Correspondence of first VC")),
                    ],
                2:[
                    ("VxC2", _("Correspondence of second VC")),
                    # ("VC1=VC2",_("Same First/only Two VCs")),
                    ],
                3:[
                    ("VxC3", _("Correspondence of third VC")),
                    # ("VC1=VC2=VC3",_("Same First/only Three VCs")),
                    # ("VC3", _("Third VC"))
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
    """kwarg button is a tuple: (text,command)"""
    def destroy(self, event=None):
        ui.Window.destroy(self)
    def withdraw(self, event=None):
        ui.Window.withdraw(self)
    def __init__(self, text, **kwargs):
        # parent=None, title="Error!", wait=False, button=False,):
        if not text:
            log.error(_("ErrorNotice got no text?"))
            return
        log.info("Making ErrorNotice: {}".format(text))
        # log.info("parent: {}".format(kwargs['parent']))
        # log.info("program: {}".format(program))
        # log.info("program['root']: {}".format(program['root']))
        # log.info("program['root'].exitFlag: {}".format(program['root'].exitFlag))
        # log.info("program['root'].exitFlag.istrue(): {}".format(program['root'].exitFlag.istrue()))
        try:
            assert not program['root'].exitFlag.istrue()
        except Exception as e:
            if 'parent' not in kwargs:
                log.info("Exception: {}".format(e))
                log.error(_("Couldn't find a parent; error message follows"))
                log.error(text)
                return
        parent=kwargs.get('parent',program.get('root',ui.Root))
        # log.info("parent: {}".format(kwargs['parent']))
        title=kwargs.get('title',_("Error!"))
        wait=kwargs.get('wait')
        button=kwargs.get('button')
        image=kwargs.get('image')
        super(ErrorNotice, self).__init__(parent,title=title,exit=False)
        self.title = title
        self.text = text
        l=ui.Label(self.frame, text=text,
                    row=0, column=1,
                    columnspan=2,
                    ipadx=25)
        if image:
            if isinstance(image, ui.Image):
                l['image']=image.scaled
            elif isinstance(image,str):
                l['image']=self.theme.photo[image]
            l['compound']='left'
        l.wrap()
        if button and type(button) is tuple:
            b=ui.Button(self.frame, text=button[0],
                    cmd=None,
                    row=1, column=1, sticky='e')
            b.bind('<ButtonRelease>',self.withdraw)
            b.bind('<ButtonRelease>',button[1],add='+')
            b.bind('<ButtonRelease>',self.destroy,add='+')
        b=ui.Button(self.frame, text=_("OK"),
                cmd=self.on_quit,
                row=1, column=2, sticky='nse')
        self.attributes("-topmost", True)
        if wait:
            self.wait_window(self)
class Repository(object):
    """SuperClass for Repository classes"""
    def checkout(self,branchname):
        args=['checkout',branchname]
        r=self.do(args)
        log.info(r)
        self.branchname() #because this changes
        # if r:
        #     r=self.pull()
        #     log.info(r)
        return r
    def add(self,file):
        #This function must be used to see changes
        # log.info("self.bare: {}".format(self.bare))
        if not self.bare:
            if not self.alreadythere(file):
                log.info(_("Adding {}, which is not already there.").format(file))
                self.files+=[file] #keep this up to date
                # self.getfiles() #this was more work
            else:
                log.info(_("Adding {}, which is already there.").format(file))
            args=["add", str(file)]
            self.do(args)
        else:
            log.info("Not adding {} to bare repo {}".format(file,self.url))
    def commitconfirm(self,diff): #don't run the diff again...
        def ok(event=None):
            self.commitconfirmed=nowruntime()
            yes.destroy()
        def notok(event=None):
            self.commitdenied=nowruntime()
            w.on_quit()
        def recent(x):
            if (x-nowruntime()).total_seconds()<5*60:
                return True
        if hasattr(self,'commitconfirmed') and recent(self.commitconfirmed):
            log.info(_("Asked for commit confirm; returning auto True"))
            return True
        elif hasattr(self,'commitdenied') and recent(self.commitdenied):
            log.info(_("Asked for commit confirm; returning auto False"))
            return False
        log.info(_("Asked for commit confirm; asking user"))
        w=ui.Window(program['root'],title="Commit Confirm",exit=False)
        text=_("Do you want to commit language data via {} now?\n{}"
                ).format(self.repotypename,diff[:300])
        # text="some other text"
        prompt=ui.Label(w,text=text,row=0,column=0,sticky='')
        bf=ui.Frame(w,row=1,column=0,sticky='')
        yes=ui.Button(bf,text=_("Yes"),command=ok,
                        row=1,column=0,sticky='w',
                        padx=50)
        no=ui.Button(bf,text=_("No"),command=notok,
                        row=1,column=1,sticky='e',
                        padx=50)
        w.lift()
        yes.wait_window(yes)
        if not w.exitFlag.istrue():
            w.on_quit()
            log.info("Me not committing when asked to by {}".format(
                                                            program['name']))
            return True
    def commit(self,file=None):
        #I may need to rearrange these args:
        if self.bare or self.code == 'hg': #don't commit here, at least for now
            return True
        if not file and self.code == 'git':
            file='-a' # 'git commit -a' is equivalent to 'hg commit'.
        args=["commit", '-m', "Autocommit from AZT", file]
        #don't try to commit without changes; it clogs the log
        diff=self.diff()
        diffcached=self.diff(cached=True)
        difftext=''
        for d in [diff,diffcached]:
            if d:
                difftext+=d
        if difftext and (not me or self.commitconfirm(difftext)):
            r=self.do([i for i in args if i is not None])
            return r
        # if theres no diff, or I don't want to commit, still share commits:
        return True
    def diff(self,cached=False):
        if not self.bare:
            args=["diff"]
            if cached:
                args+=['--cached']
            args+=['--stat']
            return self.do(args)
        # log.info("{} diff returned {}".format(self.repotypename,r))
    def status(self):
        args=["status"]
        log.info(self.do(args))
    def clonefromUSB(self,directory):
        log.info("Preparing to clone to {} from USB repo".format(directory))
        #this should be a pathlib object
        # log.info("Continuing to clone to {} from USB repo".format(directory))
        # this needs from-to args
        args=["clone", self.nonbareclonearg, self.url, str(directory)]
        msg=_("Copying from {} to {}; this may take some time."
                    "").format(self.url, directory)
        log.info(msg)
        w=ui.Wait(program['root'],msg=msg)
        log.info(self.do(args))
        w.close()
    def clonetoUSB(self,event=None):
        # log.info("Trying to run clonetoUSB")
        directory=self.clonetobaredirname()
        log.info("directory: {}".format(directory))
        if directory:
            if not self.addifis(directory):
                args=["clone", self.bareclonearg, '.', directory] #this needs from-to
                msg=_("Copying to {}; this may take some time."
                            "").format(directory)
                w=ui.Wait(program['root'],msg=msg)
                log.info(self.do(args))
                self.addremote(directory)
                w.close()
            else:
                log.info(_("Found a related repository; added to settings."))
        else:
            log.info(_("No directory given; not cloning."))
    def log(self):
        args=["log"]
        log.info(self.do(args))
    def commithashes(self,url=None):
        r=self.do(["log", "--format=%H"],url=url)
        if not url:
            url=self.url
        if r and 'fatal' not in r:
            log.info("Found {} commits for {}".format(len(r),url))
            return r.split('\n')
        else:
            log.info("Found no commits; is {} a {} repo?".format(url,
                                                            self.repotypename))
            # log.info("commithashes: {}".format(r))
            if r:
                return r #need to pass errors for processing
            else:
                return []
    def share(self,remotes=None,branch=None):
        if not remotes:
            remotes=self.findpresentremotes() #do once
        if not remotes:
            log.info("Couldn't find a local drive to share with via {}; "
                    "giving up".format(self.repotypename))
            return
        r=self.commit() #should always before pulling, at least here
        if r:
            r=self.pull(remotes,branch)
        if r:
            r=self.push(remotes,branch)
        return r #ok if we don't track results for each
    def pull(self,remotes=None,branch=None):
        if not remotes:
            remotes=self.findpresentremotes() #do once
        if not remotes:
            log.info(_("Couldn't find a local drive to pull from via {}; "
                    "giving up").format(self.repotypename))
            return
        if not branch:
            branch=self.branch
        for remote in remotes:
            args=["pull",remote,branch+':'+branch]
            r=self.do(args)
            # log.info("Pull return: {}".format(r))
        return r #if we want results for each, do this once for each
    def push(self,remotes=None,branch=None,setupstream=False):
        if not remotes:
            remotes=self.findpresentremotes() #do once
        if not remotes:
            log.info(_("Couldn't find a local drive to push to via {}; "
                    "giving up").format(self.repotypename))
            return
        if not branch:
            branch=self.branch
        for remote in remotes:
            args=["push"]
            if setupstream:
                args+=['--set-upstream']
            args+=[remote,branch+':'+branch]
            r=self.do(args)
            if r and "The current branch master has no upstream branch." in r:
                r=self.push(remotes=[remote],
                            #always keep branch names aligned.
                            branch=self.branch,
                            setupstream=True)
            # log.info(r)
        return r #ok if we don't track results for each
    def isrelated(self,directory):
        # log.info("Checking if {} \n\tis related to {}".format(directory,
        #                                                         self.url))
        # log.info(self.remotenames)
        if self.remotenames and directory in self.remotenames:
            log.info("Found {} in settings; assuming related".format(directory))
            return True #This should always be
        #Git doesn't seem to care if repos are related, but I do...
        thatrepohashes=self.commithashes(directory)
        # log.info(thatrepohashes)
        if thatrepohashes and "fatal: not a git repository" in thatrepohashes:
            return False
        if thatrepohashes and "does not have any commits yet" in thatrepohashes:
            thatrepohashes=[]
        thisrepohashes=self.commithashes()
        # log.info(thisrepohashes)
        if thisrepohashes and "fatal: not a git repository" in thisrepohashes:
            return False
        if thisrepohashes and "does not have any commits yet" in thisrepohashes:
            thisrepohashes=[]
        # with open(rx.urlok(self.url),'a') as f:
        #     for l in thisrepohashes:
        #         f.write(l+'\n')
        # with open(rx.urlok(directory),'a') as f:
        #     for l in thatrepohashes:
        #         f.write(l+'\n')
        commonhashes=set(thisrepohashes)&set(thatrepohashes)
        log.info("found {} common commits: {}".format(len(commonhashes),
                                                    list(commonhashes)[:10]))
        if len(commonhashes) >1: #just in case we find one...
            return True
        elif not len(thatrepohashes):
            log.info("Repository at {} looks empty, so I'm assuming you "
            "just initialized it".format(directory))
            log.info("This use case should probably go away!! Are we "
                "initializing empty repos somewhere, or asking the user to?")
            return True
        error=_("The directory {} doesn't seem to have a repository related "
                "to {}; removing.").format(directory,self.url)
        log.info(error)
        self.removeremote(directory)
    def addifis(self,directory):
        # N.B.: I think file.exists will always fail for internet repos
        # For now, add them to git
        if directory and file.exists(directory):
            # log.info("Found existing directory: {}".format(directory))
            if self.isrelated(directory):
                log.info("Found related repository: {}".format(directory))
                self.addremote(directory)
                return str(directory)
            else:
                self.removeremote(directory) #don't clutter settings
    def clonetobaredirname(self):
        d=file.getfile(file.getmediadirectory())
        if d:
            if d == d.with_suffix('.'+self.code):
                return d
            else:
                return d.joinpath(self.dirname).with_suffix('.'+self.code)
    def findpresentremotes(self,remote=None,firsttry=True):
        def clonetoUSB(event=None):
            # log.info("Trying to event clonetoUSB")
            self.clonetoUSB()
        l=[]
        remotesinsettings=self.remoteurls().values()
        # log.info("remotesinsettings: {}".format(remotesinsettings))
        #add to list only what is there now AND related
        # the related test will remove it if there AND NOT related.
        # Otherwise, we leave it for later, in case it just isn't there now.
        l.extend([d for d in remotesinsettings if self.addifis(d)])
        if self.remotenames:
            # log.info("self.remotenames: {}".format(self.remotenames))
            l.extend(self.remotenames)
        # log.info("remotesinsettings there: {}".format(l))
        if l:
            log.info("returning remotes:{}".format(l))
            return l
        # If we're still here, offer the user one chance to plug in a drive.
        # but just do this once; don't annoy the user.
        elif self.code == 'git' and firsttry: # and me:
            # Show this only once per run, if a user doesn't have settings
            if remotesinsettings or not self.directorydontask:
                text=_(
                # "{} can't find your {} {} backup. "
                # "If you have a USB drive for your {} {} backup, insert it now."
                "Please insert your {} USB now." #, if you have it
                "").format(
                # program['name'],
                # self.repotypename,
                self.description)
                # clonetoUSB here will ask for a directory to put it, but won't
                # clone if the target would be there, related or not.
                # Either way, we check again for present remotes, so the cost
                # of clicking this button (instead of 'exit') when you have a
                # drive already set up is an extra file dialog —hopefully OK.
                button=(_("Create new USB"),clonetoUSB)
                e=ErrorNotice(text,
                            title=_("No {} {} USB backup found"
                                    ).format(self.repotypename,
                                            self.description),
                            button=button,
                            image='USBdrive',
                            wait=True
                            )
                # log.info(self.remoteurls())
                # log.info(self.remoteurls().values())
                #At this point, the user will have cloned or not already.
                if self.remoteurls().values(): #this will have new clone value
                    return self.findpresentremotes(firsttry=False)
                else: #if still nothing, don't ask again on this run.
                    self.directorydontask=True
                    return [] #must return an interable, in any case
            else:
                return []
        else:
            return []
    def root(self):
        args=["root"]
        self.root=self.do(args)
    def getfiles(self):
        args=self.leaveunicodealonesargs()
        args+=[self.lsfiles]
        # log.info("{} getfiles args: {}".format(self.code,args))
        r=self.do(args)
        if r:
            self.files=[file.getfile(i) for i in r.split('\n')]
        else:
            self.files=[]
    def do(self,args,**kwargs):
        # log.info("do args: {}".format(args))
        if not hasattr(self,'branch') and 'init' not in args:
            return #don't try to do things without an actual repo
        cmd=[self.cmd,self.pwd] #-R
        if 'url' in kwargs and kwargs['url']:
            cmd.extend([str(kwargs['url'])])
        else:
            cmd.extend([str(self.url)])
        try:
            cmd.extend(self.usernameargs)
        except AttributeError as e:
            if hasattr(self,'files'): #only complain if initialized
                log.info("usernameargs not found ({})".format(e))
                    # "; OK if initializing "
                    # "the repo."
                    # "\nYou may also get a 'fatal: not a git repository...' "
                    # "notice, if the repo isn't there yet. "
        cmd.extend([a for a in args if a]) #don't give null args
        # log.info("{} cmd args: {}".format(self.code,cmd))
        iwascalledby=callerfn()
        try:
            output=subprocess.check_output(cmd,
                                            stderr=subprocess.STDOUT,
                                            shell=False)
            # log.info("Command output: \n{}; {}".format(output,type(output)))
        except subprocess.CalledProcessError as e:
            output=stouttostr(e.output)
            # log.info("Error output: \n{}; {}".format(output,type(output)))
            if me and (iwascalledby in ["pull"] and
                        'rejected' not in output and
                        self.code == 'git'):
                log.info(_("Call to {} ({}) gave error: \n{}\nMerging.").format(
                                                        self.repotypename,
                                                        ' '.join(args),
                                                        output))
                if output and 'fatal' not in output:
                    r=self.mergetool(**kwargs)
                    if r and 'fatal' not in r:
                        self.pull(**kwargs)
            if "The current branch master has no upstream branch." in output:
                log.info("iwascalledby {}, but don't have upstream."
                            "".format(iwascalledby))
                if iwascalledby not in ["push"]:
                    try:
                        assert self.code == 'git' #don't give hg notices here
                        ErrorNotice(output)
                    except (RuntimeError,AssertionError):
                        log.info(output)
                return output
            if iwascalledby in ["pull"]: #needed for logic and reporting
                return output
            if iwascalledby not in ["getusernameargs","log"]:
                txt=_("Call to {} ({}) gave error: \n{}").format(
                                                        self.repotypename,
                                                        ' '.join(
                                                        [str(i) for i in
                                                        args #one or the other
                                                        # cmd #this gives git ...
                                                        ]),
                                                        output)
                try:
                    assert self.code == 'git' #don't give hg notices here
                    #these are states we don't want to bother the user with:
                    assert output #git config core.bare gives zero error output
                    assert 'ot a git repository' not in output
                    assert "unknown option" not in output
                    assert "does not have any commits yet" not in output
                    assert "error: No such remote " not in output
                    ErrorNotice(txt)
                except (RuntimeError,AssertionError):
                    log.info(txt)
                    return output
            return
        except Exception as e:
            text=_("Call to {} ({}) failed: {}").format(
                                                        self.repotypename,
                                                        args,e)
            try:
                assert self.code == 'git' #don't give hg notices here
                ErrorNotice(text)
            except (RuntimeError,AssertionError):
                log.info(text)
            return
        t=stouttostr(output)
        #These give massive output!
        if t and iwascalledby not in ['diff','getfiles','commithashes']:
            log.info("{} {} {}: {}".format(self.repotypename,
                                            iwascalledby,args[1:],t))
        elif iwascalledby not in ['add','commit','commithashes']:
            log.info("{} {} {} OK".format(self.repotypename,
                                            iwascalledby,args[1:]))
        return t
    def alreadythere(self,url):
        self.getfiles()
        if file.getreldir(self.url,url) in self.files: # as str
            # log.info(_("URL {} is already in repo {}".format(url,self.url)))
            return True
        # else:
        #     log.info(_("URL {} is not already in repo {}:\n{}"
        #                 "".format(url,self.url,self.files)))
    def ignore(self,file):
        if not hasattr(self,'ignored') or file not in self.ignored:
            with open(self.ignorefile,'a') as f:
                f.write(file+'\n')
            self.getignorecontents() #make sure this is up to date
    def ignorecheck(self):
        self.ignorefile=file.getdiredurl(self.url,'.'+self.code+'ignore')
        self.getignorecontents() #make sure this is up to date
        """These should all be ignored"""
        for x in self.ignorelist():
            self.ignore(x)
        self.add(self.ignorefile)
        self.commit()
    def getignorecontents(self):
        #This reads file contents to attribute
        try: #in case the file doesn't exist yet
            with open(self.ignorefile) as f:
                self.ignored=[i.rstrip() for i in f.readlines()]
            # log.info("self.ignored for {} now {}".format(self.code,self.ignored))
        except FileNotFoundError as e:
            log.info("Hope this is OK: {}".format(e))
    def exists(self,f=None):
        if not f:
            f=self.deltadir
            log.info("Checking repo existence via {}".format(f))
        return file.exists(f)
    def exewarning(self):
        title=_("Warning: {} Executable Missing!".format(self.repotypename))
        text=_("You "
                # "seem to be working on a repository of data ({0}), "
                # "\nwhich may be tracked by {1}, "
                # "\nbut "
                "you don't seem to have the {} executable installed in "
                "your computer's PATH.").format(
                                                # self.url,
                                                self.repotypename)
        if self.repotypename == "Mercurial":
             text+='\n'+_("(Mercurial is used by Chorus and languagedepot.org)")
             if not self.exists():
                 log.info(_("No {0} repo, nor {0} executable; moving on."
                            ).format(self.repotypename))
                 return
        w=ui.Window(program.get('root',ui.Root()),title=title)
        w.withdraw()
        if self.repotypename == "Git":
             text+='\n'+_("(Git is used by {0} to track changes in your "
                        "data, and to keep {0} up to date)"
                        ).format(program['name'])
        clickable=_("Please see {} for installation recommendations"
                    ).format(self.installpage)
        l=ui.Label(w.frame, text=text, column=0, row=0)
        l.wrap()
        m=ui.Label(w.frame, text=clickable, column=0, row=1)
        m.wrap()
        m.bind("<Button-1>", lambda e: openweburl(self.installpage))
        mtt=ui.ToolTip(m,_("Go to {}").format(self.installpage))
        if self.thisos == "Windows":
            clickable1=_("(e.g., in Windows, install *this* file),"
                        ).format(self.wexeurl)
            clickable2=_("or see all your options at {}."
                        ).format(self.wdownloadsurl)
            n=ui.Label(w.frame, text=clickable1, column=0, row=2)
            n.bind("<Button-1>", lambda e: openweburl(self.wexeurl))
            ntt=ui.ToolTip(n,_("download {}").format(self.wexeurl))
            o=ui.Label(w.frame, text=clickable2, column=0, row=3)
            o.bind("<Button-1>", lambda e: openweburl(self.wdownloadsurl))
            mtt=ui.ToolTip(o,_("Go to {}").format(self.wdownloadsurl))
        # button=(_("Restart Now"),sysrestart) #This should be in task/chooser
        text=_("After you install {}, you should restart."
                ).format(self.repotypename)
        if self.repotypename == "Git":
            text+='\n'+_("You can keep using {} without installing {}, but "
                        "it is not recommended, and you will continue to see "
                        "this warning."
                        " And sooner or later that's going to get really annoying"
                        ).format(program['name'],self.repotypename)
        r=ui.Label(w.frame, text=text, column=0, row=4)
        r.wrap()
        rb=ui.Button(w.frame, text=_("Restart Now"), column=1, row=4,
                    cmd=sysrestart) #This should be in task/chooser
        rbtt=ui.ToolTip(rb,_("Install {} first, then do this"
                            ).format(self.repotypename))
        w.deiconify()
        w.lift()
    def getusernameargs(self):
        #This populates self.usernameargs, once per init.
        re=None
        r=self.do(self.argstogetusername)
        if hasattr(self,'argstogetuseremail'):
            re=self.do(self.argstogetuseremail)
        if r:
            log.info("Using {} username '{}'".format(self.repotypename,r))
            if re:
                log.info("Using {} useremail '{}'".format(self.repotypename,re))
        else:
            r=program['name']+'-'+program['hostname']
            log.info("No {} username found; using '{}'"
                    "".format(self.repotypename,r))
        if not re:
            re=program['name']+'@'+program['hostname']
            log.info("No {} useremail found; using '{}'"
            "".format(self.repotypename,re))
        self.usernameargs=self.argstoputuserids(r,re)
    def addUSBremote(self):
        # This should be a directory (or parent) with existing repo
        self.addremote(self.clonetobaredirname())
    def addremote(self,remote):
        #This may take in paths, but needs to compare strings
        remotes=self.remoteurls()
        # log.info("remote: {}; type: {}".format(remote,type(remote)))
        # log.info("remotes: {}; types: {}".format(remotes.values(),
        #                                     type(list(remotes.values())[-1])))
        if not remote or str(remote) in remotes.values(): # compare str w str
            return
        for key in ["Thing"+str(i) for i in range(1,20)]:
            if key not in remotes: #don't overwrite keys
                log.info("Setting {} key with {} value".format(key,remote))
                remotes[key]=str(remote)
                self.remoteurls(remotes) #save
                log.info("URL Settings now {}".format(self.remoteurls()))
                return
    def localremotes(self):
        return [i for d in self.remoteurls().values()
                for i in [self.addifis(d)]
                if i
                if not self.isinternet(i)]
    def isinternet(self,remote):
        log.info("self.remotenames: {}; remote: {}".format(self.remotenames,remote))
        if remote in self.remotenames:
            remote=self.getremotenameurl(remote)
        if isinterneturl(remote):
            return True
    def removeremote(self,remote):
        # This is one of two functions that touch self._remotes directly
        for k,v in self.remoteurls().items():
            if v == remote:
                del self._remotes[k]
    def remoteurls(self,remotes=None):
        # This is one of two functions that touch self._remotes directly
        # This returns a copy of the dict, so don't operate on it directly.
        # Rather, read and write using this function.
        # log.info("returning remote urls: {}".format(getattr(self,'_remotes',{})))
        if remotes and type(remotes) is dict:
            self._remotes=remotes
        elif remotes:
            log.info("You passed me a remotes value that isn't a dict?")
        else:
            return getattr(self,'_remotes',{}).copy() #so I can iterate and change
    def branchname(self):
        repoheadfile='.'+self.code+'/'+self.branchnamefile
        log.info("Looking for {} branch name in {}".format(self.repotypename,
                                                            repoheadfile))
        try:
            with file.getdiredurl(self.url,repoheadfile).open() as f:
                c=f.read()
                # log.info("Found repo head info {}".format(c))
                if c:
                    self.branch=c.split('/')[-1].strip()
                    log.info("Found branch: {}".format(self.branch))
            # return self.branch
        except Exception as e:
            log.error(_("Problem finding branch name: {}").format(e))
    def setdescription(self):
        self.description=_("language data")
    def populate(self):
        #this is done on normal __init__, or after an init later on.
        #These are things that need an actual repository there
        self.bare=bool(self.isbare())
        log.info("Repo {} is bare: {}".format(self.url,self.bare))
        self.remotenames=self.getremotenames()
        self.getusernameargs()
        self.getfiles()
        self.ignorecheck()
        self.branchname()
        try:
            log.info("{} repository object initialized on branch {} at {} "
                    "for {}, with {} files."
                    "".format(self.repotypename, self.branch, self.url,
                        self.description, len(self.files)))
        except FileNotFoundError:
            log.info("{} repository object initialized at {} "
                    "for {}, with {} files."
                    "".format(self.repotypename, self.url,
                        self.description, len(self.files)))
    def __init__(self, url):
        super(Repository, self).__init__()
        self.url = url
        self.dirname = file.getfilenamefrompath(self.url)
        self.repotypename=self.__class__.__name__
        self.thisos=platform.system()
        self.directorydontask=False #set on init, track first request rejection
        # For testing:
        # self.thisos="Windows"
        if self.thisos == "Linux":
            self.installpage=("https://github.com/kent-rasmussen/azt/blob/main/"
                                "docs/SIMPLEINSTALL_LINUX.md")
        elif self.thisos == 'Windows':
            self.installpage=("https://github.com/kent-rasmussen/azt/blob/main/"
                                "docs/SIMPLEINSTALL.md")
        self.cmd=program[self.code]
        self.deltadir=file.getdiredurl(self.url,'.'+self.code)
        self.setdescription()
        if (not file.exists(self.deltadir) # and self.code == 'git':
            and str(self.url).endswith('.'+self.code)):# or self.code == 'hg':
            self.deltadir=self.url
        if not file.exists(self.deltadir):
            log.info("Not a {} repo ({})? Returning".format(self.repotypename,
                                                            self.url))
            return
        if not self.cmd:
            log.info("Found no {} executable!".format(self.repotypename))
            self.exewarning()
            return #before getting a file list!
        self.populate() #get files, etc.
class Mercurial(Repository):
    def ignorelist(self):
        return ['*.pdf','*.xcf',
                '*.hg','*~',
                ]
    def leaveunicodealonesargs(self):
        return []
    def argstoputuserids(self,username,email):
        return ['--config','ui.username={}'.format(username)] # just one field
    def choruscheck(self):
        rescues=[]
        for file in self.files:
            if str(file).endswith('.ChorusRescuedFile'):
                rescues.append(file)
        if rescues:
            error=_("You have the following files ( in {}) that need to be "
                    "resolved from Chorus merges:\n {}"
                    "").format(self.url,'\n'.join(rescues))
            log.error(error)
            ErrorNotice(error,title=_("Chorus Rescue files found!"))
            if me:
                exit()
    def makebare(self):
        args=['update', 'null']
    def isbare(self):
        # any return implies a working directory parent (not bare)
        return not self.do(['parent'])
    def getremotenames(self):
        pass
    def __init__(self, url):
        self.code='hg'
        self.branchnamefile='branch'
        # self.cmd=program['hg']
        self.wdownloadsurl="https://www.mercurial-scm.org/wiki/Download"
        self.wexename="Mercurial-6.0-x64.exe"
        self.wexeurl=("https://www.mercurial-scm.org/release/windows/{}"
                        "".format(self.wexename))
        self.pwd='--cwd'
        self.lsfiles='files'
        self.argstogetusername=['config', 'ui.username']
        self.bareclonearg="-U"
        self.nonbareclonearg=""
        super(Mercurial, self).__init__(url)
        # These files are just ignored in git, but if Chorus put something
        # there, we want to know
        if hasattr(self,'files'):
            self.choruscheck()
        else:
            self=None
class Git(Repository):
    def ignorelist(self):
        return ['*.pdf','*.xcf',
                'XLingPaperPDFTemp/**',
                '*backupBeforeLx2LcConversion',
                '*.txt', '*.7z', '*.zip','*ori',
                '__pycache__/**', '*(copy)*',
                'lift_url.py',
                'ui_lang.py',
                '*~',
                'userlogs/**',
                'test*wav',
                'excess/**',
                'images/archive/**',
                'images/scaled/**',
                'reports/**',
                '*.ChorusNotes',
                '*.WeSayUserMemory',
                '*.WeSayConfig*',
                '*.WeSayUserConfig',
                '*.ChorusRescuedFile',
                '*.git',
                '*.ini',
                '*lift.*',
                ]
    def mergetool(self,**kwargs):
        args=['mergetool', '--tool=xmlmeld']
        r=self.do(args,**kwargs)
        log.info(r)
        return r
        # git mergetool --tool=<tool>' may be set to one of the following:
		# araxis
		# kdiff3
		# meld
    def makebare(self):
        args=['config', '--bool', 'core.bare', 'true']
    def isbare(self):
        r=self.do(['config', 'core.bare'])
        if r != 'false': # if it is, don't return, i.e., False.
            return r # pass on the config value, if not 'false', which == True
    def leaveunicodealonesargs(self):
        return ['-c','core.quotePath=false']
    def argstoputuserids(self,username,email):
        return ['-c', 'user.name={}'.format(username),
                '-c', 'user.email={}'.format(str(email))]
    def init(self):
        args=['init', '--initial-branch=main']
        r=self.do(args)
        if 'unknown option' in r:
            args=['init']
            r=self.do(args)
        log.info("init: {}".format(r))
        self.populate() #because this won't have been done yet
        # git config branch.$branchname.mergeoptions "-X ignore-space-change"
    def lastcommitdate(self):
        args=['log', '-1', '--format=%cd']
        r=self.do(args)
        # log.info(r)
        return r
    def getremotenames(self):
        args=['remote']
        r=self.do(args)
        if r:
            r=r.split('\n')
        log.info("Using these remotes: {}".format(r))
        return r
    def getremotenameurl(self,remotename):
        args=['remote', 'get-url', remotename]
        r=self.do(args)
        if "error: No such remote " not in r:
            return r
    def __init__(self, url):
        self.code='git'
        self.branchnamefile='HEAD'
        self.wdownloadsurl="https://git-scm.com/download/win"
        self.wexename="Git-2.33.0.2-64-bit.exe"
        self.wexeurl=("https://github.com/git-for-windows/git/releases/"
                        "download/v2.33.0.windows.2/{}".format(self.wexename))
        self.pwd='-C'
        self.lsfiles='ls-files'
        self.argstogetusername=['config', '--get', 'user.name']
        self.argstogetuseremail=['config', '--get', 'user.email']
        self.bareclonearg="--bare"
        self.nonbareclonearg=""
        super(Git, self).__init__(url)
class GitReadOnly(Git):
    def exewarning(self):
        pass #don't worry about it for this one
    def share(self,event=None):
        """This method should only ever pull or push, depending on who
        is doing it"""
        # this will mostly operate on all present sources (internet and USB),
        # reporting failures as appropriate. I hope users will be OK with that
        if me: #no one else should push changes
            method=Repository.push
            remotes=self.localremotes() #don't publish to internet this way
        else:
            method=Repository.pull
            #make sure we at least try the github remote:
            remotes=self.findpresentremotes(firsttry=False) #don't ask
            homeurl=program['url']+'.git'
            remotes.extend([homeurl])
        r={}
        log.info("remotes: {}".format(remotes))
        for branch in ['main',program['testversionname']]:
            for remote in remotes:
                r[remote+'/'+branch]=method(self,branch=branch,remotes=[remote])
        return r
        """I'm going to need to stash and stash apply here, I think"""
        remotes=self.findpresentremotes() #do once
        if not remotes:
            return
        branches = ['main',program['testversionname']]
        fns = [self.testversion, self.reverttomain]
        if self.branch != 'main':
            branches.reverse()
            fns.reverse()
        try:
            for i in range(2):
                log.info("Running index {} ({} {})".format(i,branches[i],fns[i]))
                #not pulling here, as not sharing in that direction.
                r=Repository.push(self,remotes=remotes,branch=branches[i])
                if r:
                    r=fns[i]()
        except Exception as e:
            ErrorNotice(e)
    def reverttomain(self,event=None):
        r=self.checkout('main')
        log.info(r)
        if self.branch == 'main':
            return True
        else:
            ErrorNotice(r)
    def testversion(self,event=None):
        r=self.checkout(program['testversionname'])
        log.info(r)
        if self.branch == program['testversionname']:
            return True
        else:
            ErrorNotice(r)
    def add(self,file):
        pass
    def commit(self,file=None):
        pass
    def setdescription(self):
        self.description=_("AZT source")
    def __init__(self, url):
        super(GitReadOnly, self).__init__(url)
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
    return datetime.datetime.utcnow().isoformat()#[:-7]+'Z'
def nowruntime():
    #this returns a delta!
    return datetime.datetime.utcnow()-program['start_time']
def logfinished(start=program['start_time'],msg=None):
    run_time=nowruntime()
    if type(start) is datetime.datetime: #only work with deltas
        start-=program['start_time']
    if msg:
        msg=str(msg)+' '
    else:
        msg=''
    text=_("Finished {}at {} ({:1.0f}m, {:2.3f}s)"
            "").format(msg,now(),*divmod((run_time-start).total_seconds(),60))
    log.info(text)
    return text
def interfacelang(lang=None,magic=False):
    global i18n
    global _
    """Attention: for this to work, _ has to be defined globally (here, not in
    a class or module.) So I'm getting the language setting in the class, then
    calling the module (imported globally) from here."""
    if lang:
        curlang=interfacelang()
        try:
            if _.__module__ == 'gettext':
                log.debug("Magic: {}".format(_.__module__))
                magic=True
            else:
                log.debug("Magic seems to be installed, but not gettext: {}"
                            "".format(_.__module__))
        except:
            log.debug("Looks like translation magic isn't defined yet; making")
        if lang != curlang or magic == False:
            if lang is not None:
                log.debug("Setting Interface language: {}".format(lang))
                i18n[lang].install()
                log.debug("New Magic: {}".format(_.__module__))
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
                log.debug("_ doesn't look defined yet, returning interface "
                            "language from locale.")
                loc,enc=locale.getdefaultlocale()
                if loc:
                    code=loc.split('_')[0]
                else:
                    log.debug("locale.getdefaultlocale doesn't seem to have "
                    "returned any results: {} (OS: {}); using French user "
                    "interface".format(
                                        locale.getdefaultlocale(),
                                        platform.system()))
                    code='en' #I think loc=None normally means English on macOS
                if code in i18n:
                    return code
def dictofchilddicts(dict,remove=None):
    # This takes a dict[x][y] and returns a dict[y], with all unique values
    # listed for all dict[*][y].
    # log.info("Working on dict {}".format(dict))
    o={}
    for x in dict:
        for y in dict[x]:
            if y not in o:
                o[y]=[]
            if isinstance(dict[x][y],list):
                for z in dict[x][y]:
                    o[y].append(z)
            else:
                o[y].append(dict[x][y])
    # log.info("o1:{}".format(o))
    for y in o:
        o[y]= list(dict.fromkeys(o[y]))
        if type(remove) is list:
            for a in remove:
                if a in o[y]:
                    o[y].remove(a)
    # log.info("o2:{}".format(o))
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
def quote(x):
    #does this fail on non-string x?
    if isinstance(x,dict) or isinstance(x,int) or isinstance(x,list):
        return str(x) #don't put brackets around this, just make it a string
    if "'" not in x:
        return "'"+x+"'"
    elif '"' not in x:
        return '"'+x+'"'
    else:
        log.error("Looks like ˋ{}ˊ contains single and double quotes!".format(x))
def indenteddict(indict):
    outdict={}
    # log.info("working on dict with keys {}".format(indict.keys()))
    for j in indict:
        # log.info("working on {}".format(j))
        if isinstance(indict[j], dict):
            # log.info("printing indented dict for {} key".format(j))
            # config[s][j]='\n'.join(['{'+i+':'+str(v[j][i])+'}'
            #                             for i in v[j].keys()])
            if True in [isinstance(i, dict) for i in indict[j].values()]:
                # log.info("printing double indented dict for {}: {} "
                #             "keys".format(j,indict[j].keys()))
                outdict[j]='{'+',\n'.join(
                    [quote(k)+":{"+',\n\t'.join(
                                        [quote(i)+":"+quote(indict[j][k][i])
                                            for i in indict[j][k]#.keys()
                                            # for k in indict[j].keys()
                                            if i #and i in indict[j][k].keys()
                                        ]
                                                )+'}'
                    for k in indict[j]#.keys()
                    if k #and k in indict[j].keys()
                    # if k
                    ]
                                            )+'}'
                # '\n\t\t'.join(str({i:v[j][k][i]
                #                             for i in v[j][k]}))
            else:
                log.info("printing indented dict for {} "
                        "key".format(j))
                outdict[j]='{'+',\n'.join([quote(i)+":"+quote(indict[j][i])
                                        for i in indict[j]#.keys()
                                        if i])+'}'
        elif indict[j]:
            # log.info("printing unindented dict for {} "
            #         "key".format(j))
            outdict[j]=str(indict[j]) #don't quote booleans!
    return outdict
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
    for arg in ['wsorted','tosort','toverify','tojoin','torecord','comparison',
                'todo'
                ]:
        kwargs[arg]=kwargs.get(arg,False)
    # log.info("Returning grouptype kwargs {}".format(kwargs))
    return kwargs
def isnoninteger(x):
    try:
        int(x)
    except (ValueError,TypeError):
        return True
def isinteger(x):
    try:
        int(x)
        return True
    except (ValueError,TypeError):
        return False
def ifone(l,nt=None):
    if l and not len(l)-1:
        return l[0]
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
            ox=[t(v) for v in l[:len(l)-2] if v] #Should probably always give text
            l=ox+[_(' and ').join([t(v) for v in l[len(l)-2:]
                                        if v not in ignore
                                        if v])]
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
def nn(x,perline=False,oneperline=False,twoperline=False):
    """Don't print "None" in the UI..."""
    if type(x) is list or type(x) is tuple:
        output=[]
        for y in x:
            output+=[nonspace(y)]
        if perline: #join every other with ', ', then all with '\n'
            return '\n'.join([', '.join([str(v) for v in output[i*perline:i*perline + perline]])
                        for i in range(int(len(output)/perline)+1)])
        elif twoperline: #join every other with ', ', then all with '\n'
            return '\n'.join([', '.join([str(v) for v in output[i*2:i*2 + 2]])
                        for i in range(int(len(output)/2)+1)])
        elif oneperline:
            return '\n'.join([str(i) for i in output])
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
def pickshortest(l):
    shortestlength=min([len(i) for i in l])
    for i in l:
        if len(i) == shortestlength:
            return i
def getinterfacelangs():
    return [{'code':'fr','name':'Français'},
            {'code':'en','name':'English'},
            {'code':'fub','name':'Fulfulde'}
            ]
def loadCAWL():
    stockCAWL=file.fullpathname('SILCAWL/SILCAWL.lift')
    if file.exists(stockCAWL):
        log.info("Found stock LIFT file: {}".format(stockCAWL))
    try:
        # cawldb=lift.Lift(str(stockCAWL))
        cawldb=lift.Lift(str(stockCAWL),tostrip=True)
        log.info("Parsed ET.")
        log.info("Got ET Root.")
    except lift.BadParseError:
        text=_("{} doesn't look like a well formed lift file; please "
                "try again.").format(stockCAWL)
        ErrorNotice(text,wait=True)
        return
    except Exception as e:
        log.info("Error: {}".format(e))
    log.info("Parsed stock LIFT file to tree/nodes.")
    return cawldb
def saveimagefile(url,filename,copyto=None):
    # log.info("Preparing to write image to new file")
    if not copyto:
        copyto=program['settings'].imagesdir
    fqdn=file.getdiredurl(copyto,filename) #new url
    # log.info("Preparing to write image to {}".format(fqdn))
    with open(fqdn,'wb') as f:
        # log.info("opened new file")
        with open(url,'rb') as u:
            # log.info("opened old file")
            f.write(u.read())
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
    # # This breaks search for testing:
    # if exe in ['hg']: #'git',
    #     program[exe]=None
    #     return
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
        program[exe]=stouttostr(exeURL)
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
        program[exe]=pickshortest(program[exe])
        log.info("Using shortest executable path: {}".format(program[exe]))
    if exe == 'praat' and program[exe] and not praatversioncheck():
        findexecutable('sendpraat') #only ask if it would be useful
    # os.environ["PATH"] += os.pathsep + os.path.join(os.getcwd(), 'node')
def praatversioncheck():
    praatvargs=[program['praat'], "--version"]
    versionraw=subprocess.check_output(praatvargs, shell=False)
    try:
        version=pkg_resources.parse_version(stouttostr(versionraw))
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
    if platform.system() == 'Linux':
        log.info("If you have errors containing ˋportaudioˊ above, you should "
            "install pyaudio with your package manager.")
    log.info("FYI, looking for this platform: {}_{}".format(
                                                        platform.system(),
                                                        platform.processor()))
    # The above is there to see what version python will be looking for, and
    # why it didn't find what's there. It doesn't input to any of the following.
    installfolder='modulestoinstall/'
    installedsomething=False
    if not program['python']:
        log.error("Can't find python; how am I doing this? Put it in your PATH")
        sys.exit()
    installs=[
            # ['--upgrade', 'pip', 'setuptools', 'wheel'], #this is probably never needed
            ['numpy'],
            ['pyaudio'],
            ['Pillow', 'lxml'],
            ['psutil'],
            ['patiencediff']
            ]
    for install in installs:
        pyargs=[program['python'], '-m', 'pip', 'install',
                    '-f', installfolder, #install the one in this folder, if there
                    '--no-index' #This stops it from looking online
                    ]
        npyargs=len(pyargs)
        # if install[0] == 'pyaudio':
        #     install[0]+='==0.2.13'
        pyargs.extend(install)
        log.info("Running `{}`".format(' '.join(pyargs)))
        try:
            o=subprocess.check_output(pyargs,shell=False,
                                        stderr=subprocess.STDOUT)
            o=stouttostr(o)
            if not o:
                log.info("looks like it was successful; so I'm going to reboot "
                            "in a bit. ({})".format(o))
                installedsomething=True
        except subprocess.CalledProcessError as e:
            o=stouttostr(e.output)
            if 'Could not find a version' in o:
                del pyargs[npyargs-1] #pull no-index
                log.info("Running `{}`".format(' '.join(pyargs)))
                try:
                    o=subprocess.check_output(pyargs,shell=False,
                                            stderr=subprocess.STDOUT)
                    o=stouttostr(o)
                    if not o:
                        log.info("looks like it was at last successful; so "
                                "I'm going to reboot in a bit. ({})".format(o))
                        installedsomething=True
                except subprocess.CalledProcessError as e:
                    o=stouttostr(e.output)
        log.info(o) #just give bytes, if encoding isn't correct
    if installedsomething:
        sysrestart()
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
            t=stouttostr(o)
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
def tryrun(cmd):
    try:
        cmd()
    except Exception as e:
        text=_("{} command error: {}\n({})").format(cmd.__name__,e,cmd)
        log.error(text)
        ErrorNotice(text,title=_("{} command error!").format(cmd.__name__))
def sysshutdown():
    logsetup.shutdown()
    sys.exit()
def sysrestart(event=None):
    osys=platform.system()
    log.info("Hard shutting down now.")
    logsetup.shutdown()
    if osys == "Linux":
        os.execv(sys.argv[0], sys.argv)
        # log.info("Trying argv[0] with args {}, {} and {}".format(sys.executable,
        #                                                         sys.argv[0],
        #                                                         sys.argv))
        # try:
        #     log.info("Trying argv[0]")
        #     os.execv(sys.argv[0], sys.argv)
        # except Exception as e:
        #     log.info("Failed ({}); Trying executable".format(e))
        #     os.execv(sys.executable, sys.argv)
    elif osys == 'Windows':
        # log.info("Trying subprocess.run with executable".format(e))
        subprocess.run([sys.executable,*sys.argv])
        # log.info("Trying execv")
        # # try:
        # #     os.execv(sys.executable, sys.argv)
        # # except Exception as e:
        # # log.info("Failed ({}); Trying execl".format(e))
        # # try:
        # #     os.execl(sys.executable, sys.argv)
        # # except Exception as e:
        # try:
        #     log.info("Trying os.execv sys.argv[0]")
        #     os.execv(sys.argv[0], sys.argv)
        #     # os.execvp(sys.executable, sys.argv)
        # except Exception as e:
        #     try:
        #         log.info("Failed ({}); Trying execl".format(e))
        #         os.execl(sys.argv[0], *sys.argv)
        #     except Exception as e:
        #         try:
        #             log.info("Failed ({}); Trying spawnv".format(e))
        #             os.spawnv(os.P_NOWAIT, sys.argv[0], sys.argv)
        #         except Exception as e:
        #             try:
        #                 log.info("Failed ({}); Trying spawnl".format(e))
        #                 os.spawnl(os.P_NOWAIT, sys.argv[0], *sys.argv)
        #             except Exception as e:
        #                 try:
        #                     log.info("Failed ({}); Trying subprocess.run"
        #                                 "".format(e))
        #                     subprocess.run([*sys.argv])# also try run(sys.argv)
        #                 except Exception as e:
        #                     try:
        #                         log.info("Failed ({}); Trying subprocess.run "
        #                                     "with executable".format(e))
        #                         subprocess.run([sys.executable,*sys.argv])
        #                     except Exception as e:
        #                         log.info("Failed ({}); giving up.".format(e))
    sys.exit()
def internetconnectionproblemin(x):
    problems=[
            "No route to host",
            "unable to access",
            "Could not resolve host",
            "Could not read from remote repository."
            ]
    for p in problems:
        if p in x:
            return True
def isinterneturl(x):
    u=['ssh:',
        "https:",
        "http:"
        ]
    if [i for i in u if i in x if x]:
            return True
def updated(x):
    #put strings that indicate a repo was updated here
    if not uptodate(x) and 'fatal: ' not in x:
        return True
def uptodate(x):
    #These are repo already up to date messages
    u=['Everything up-to-date',
        "Already up to date."
        ]
    if [i for i in u if i in x if x]:
            return True
def stouttostr(x):
    # This fn is necessary (and problematic) because not all computers seem to
    # reply to subprocess.check_output with the same kind of data. I have even
    # seen a computer say it was using unicode, but not return unicode
    # data (I think because it was replacing translated text, but didn't
    # replace the same encoding). Another dumb thing that I need to account for.
    if type(x) is str:
        return x.strip()
    if not sys.stdout.encoding:
        log.error("I can't tell the terminal's encoding, sorry!")
    else:
        try:
            return x.decode(sys.stdout.encoding,
                            errors='backslashreplace').strip()
        except Exception as e:
            #if the computer doesn't know what encoding it is actually using,
            # this should give us some info to debug.
            log.error(_("Can't decode this (in {}; {}):"
                        ).format(sys.stdout.encoding, e))
            log.error(x)
    return x #not sure if this is a good idea, but this should probably raise...
def updateazt(event=None,**kwargs): #should only be parent, for errorroot
    def tryagain(event=None):
        updateazt(**kwargs)
    log.info(_("Updating {}").format(program['name']))
    if 'git' in program:
        parent=kwargs.get('parent')
        if not parent or not parent.winfo_exists(): #take kwarg if there
            if 'chooser' in program:
                kwargs['parent']=program['taskchooser'].mainwindowis
            else:
                kwargs['parent']=program['root']
        log.info("parent title: {}".format(kwargs['parent'].title()))
        w=ui.Wait(msg=_("Updating {}").format(program['name']), **kwargs)
        r=program['repo'].share() #t is a dict of main and testing results
        w.close()
        if r:
            t='\n'.join([i for j in r.items() #each tuple
                        for k in j #each tuple item
                        if k #don't give empty items
                        for i in [l for l in k.split('\n')# each tuple item line
                                if 'hint: ' not in l][:10] #first 10 w/o hint
                                ])
        else:
            t=_("No results! Is there a {} source available?"
                ).format(program['name'])
        # log.info("git raw output: {} ({})".format(r,type(r)))
        # log.info("git output: {} ({})".format(t,type(t)))
        button=False
        if internetconnectionproblemin(t):
            t=t+_('\n(Check your internet connection and try again)')
            button=(_("Try Again"),tryagain)
        elif not me:
            if [i for i in r.values() if 'fatal: ' in i]: #any fatal problem
                t+='\n'+_("(Problem! You will likely need help with this.)")
            elif [i for i in r.values() if updated(i)]: #anything updated
                t+='\n'+_("(Restart {} to use this update)"
                        ).format(program['name'])
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
def main():
    global program
    log.info("Running main function on {} ({})".format(platform.system(),
                                    platform.platform())) #Don't translate yet!
    # program['theme']=ui.Theme(program,ipady=0)
    try:
        root = program['root']=ui.Root(program=program,
                                    # ipady=0,
                                    # ipadx=10,
                                    # pady=20,
                                    # padx=30,
                                    )
    except tkinter.TclError as e:
        log.info("Evidently you can't make a root window? ({})".format(e))
        return
    program['theme']=root.theme #ui.Theme(program)
    log.info("Theme name: {}".format(program['theme'].name))
    # log.info("Theme ipady: {}".format(program['theme'].ipady))
    # log.info("Theme ipadx: {}".format(program['theme'].ipadx))
    # log.info("Theme pady: {}".format(program['theme'].pady))
    # log.info("Theme padx: {}".format(program['theme'].padx))
    lastcommit=program['repo'].lastcommitdate()
    root.program=program
    root.wraplength=root.winfo_screenwidth()-300 #exit button
    root.wraplength=int(root.winfo_screenwidth()*.7) #exit button
    root.withdraw()
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
        log.info("MS Windows screen size: {}".format(screensize))
    # log.info(root.winfo_class())
    # root.className="azt"
    # root.winfo_class("azt")
    # log.info(root.winfo_class())
    """Translation starts here:"""
    t = TaskChooser(root) #TaskChooser MainApplication
    t.mainloop()
    sysshutdown()
def mainproblem():
    def reverttomain(event=None):
        program['repo'].reverttomain()
        revertb.destroy()
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
        try:
            errorroot = ui.Root(program=program)
            errorroot.wraplength=int(errorroot.winfo_screenwidth()*.7) #exit button
            newtk=True
            log.info(_("Starting with new root"))
        except tkinter.TclError as e:
            log.info("Evidently you can't make a root window? ({})".format(e))
            log.info("This was your error:\n{}".format(logsetup.contents(50)))
            return
    errorroot.withdraw()
    errorw=ui.Window(errorroot)
    errorw.title(_("Serious Problem!"))
    errorw.mainwindow=True
    l=ui.Label(errorw.frame,text=_("Hey! You found a problem! (details and "
            "solution below)"),justify='left',font='title',
            row=0,column=0
            )
    if exceptiononload:
        durl='{}/INSTALL.md#dependencies'.format(program['docsurl'])
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
    eurl='mailto:{}?subject=Please help with {} installation'.format(addr,
                                                                program['name'])
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
    f=ui.Frame(errorw.outsideframe,row=1,column=2)
    if program['git']:
        ui.Button(f,
                text=_("Check for \n{} \nupdates").format(program['name']),
                cmd=lambda x=errorw:updateazt(parent=x),
                row=0,column=0,
                pady=20)
        if program['repo'].branch != 'main':
            revertb=ui.Button(f,
                    text=_("Revert to \nmain branch \nof {}").format(program['name']),
                    cmd=reverttomain,
                    row=1,column=0,
                    pady=20)
    ui.Button(f,text=_("Restart \n{}").format(program['name']),
                cmd=sysrestart, #This should be in task/chooser
                row=2,column=0,
                pady=20)
        # log.info(_("Done making update menu"))
    errorw.wait_window(errorw)
    if newtk: #likely never work/needed?
        errorroot.mainloop() #This has to be the last thing
"""functions which are not (no longer?) used"""
def callerfn():
    #Not this function, nor the one that called it, but the one that called that
    return inspect.getouterframes(inspect.currentframe())[2].function
def callerfnparent():
    #Not this function, nor the one that called it, but the one that called that
    return inspect.getouterframes(inspect.currentframe())[1].function
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
    # log.info("TaskChooser MRO: {}".format(TaskChooser.mro()))
    # log.info("ui.Window MRO: {}".format(ui.Window.mro()))
    # log.info("ui.Exitable MRO: {}".format(ui.Exitable.mro()))
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
    #This isn't helpful where things are copied to disk later:
    mt=datetime.datetime.fromtimestamp(thisexe.stat().st_mtime)
    """Not translating yet"""
    transdir=file.gettranslationdirin(program['aztdir'])
    i18n={}
    i18n['en'] = gettext.translation('azt', transdir, languages=['en_US'])
    i18n['fr'] = gettext.translation('azt', transdir, languages=['fr_FR'])
    interfacelang(interfacelang()) #translation works from here
    findexecutable('git')
    program['repo']=GitReadOnly(program['aztdir']) #this needs root for errors
    try:
        branch=program['repo'].branch
    except AttributeError:
        branch='main'
        log.info("Repo has no branch attribute; assuming main branch.")
    if branch != 'main':
        program['version'] += " ({})".format(branch)
    program['docsurl']=('https://github.com/kent-rasmussen/azt/blob/{}/docs'
        '').format(branch)
    log.info(_("Running {} v{} (main.py updated to {})").format(
                                    program['name'],program['version'],mt))
    log.info(_("Called with arguments ({}) {} / {}").format(sys.executable,
                                                    sys.argv[0], sys.argv))
    text=_("Working directory is {} on {}, running on {} cores"
            ).format(program['aztdir'],
                    program['hostname'],
                    multiprocessing.cpu_count())
    try:
        import psutil
        text+=", at {}Mhz".format(psutil.cpu_freq(percpu=True))
    except ModuleNotFoundError:
        log.info("No psutil; no cpu info.")
    log.info(text)
    log.info(_("Computer identifies as {}").format(platform.uname()))
    log.info(_("Loglevel is {}; started at {}").format(loglevel,
                                        program['start_time'].isoformat()))
    #'sendpraat' now in 'praat', if useful
    for exe in ['praat','hg','ffmpeg','lame','python','python3']:
        findexecutable(exe)
    if program['python3']: #be sure we're using python v3
        program['python']=program.pop('python3')
    if not program['python']:
        program['python']=sys.executable
    if 'testtask' in program and type(program['testtask']) is str:
        log.info("Converting string ‘{}’ to class".format(program['testtask']))
        program['testtask']=getattr(sys.modules[__name__],
                                        program['testtask'])
    # i18n['fub'] = gettext.azttranslation('azt', transdir, languages=['fub'])
    if exceptiononload:
        pythonmodules()
        # sysrestart()
        mainproblem()
    else:
        try:
            main()
            # import profile
            # profile.run('main()', 'userlogs/profile.tmp')
            # import pstats
            # p = pstats.Stats('userlogs/profile.tmp')
            # p.sort_stats('cumulative').print_stats(10)
            # main()
        # except FileNotFoundError:
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
