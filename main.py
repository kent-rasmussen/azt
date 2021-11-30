#!/usr/bin/env python3
# coding=UTF-8
"""This file runs the actual GUI for lexical file manipulation/checking"""
program={'name':'A→Z+T'}
program['tkinter']=True
program['production']=True#False #True for making screenshots
program['version']='0.8.6oop' #This is a string...
program['url']='https://github.com/kent-rasmussen/azt'
program['Email']='kent_rasmussen@sil.org'
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
else:
    loglevel='DEBUG'
from logsetup import *
log=logsetup(loglevel)
"""My modules, which should log as above"""
import lift
import file
import profiles
import setdefaults
import xlp
try:
    import sound
except Exception as e:
    log.exception("Problem importing Sound/pyaudio. Is it installed? %s",e)
    exceptiononload=True #logwritelzma(log.filename) #in logsetup
"""Other people's stuff"""
import threading
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
import unicodedata
# #for some day..…
# from PIL import Image #, ImageTk
#import Image #, ImageTk
import re
import configparser
import rx
import inspect #this is for determining this file name and location
import reports
import sys
"""for tr:"""
import locale
import gettext
import sys
import inspect
import os
import pprint #for settings and status files, etc.
import subprocess
import webbrowser

class Check():
    """the parent is the *functional* head, the MainApplication."""
    """the frame is the *GUI* head, the frame sitting in the MainApplication."""
    def __init__(self, parent, frame, nsyls=None):
        self.start_time=time.time() #this enables boot time evaluation
        self.pp=pprint.PrettyPrinter()
        self.iterations=0
        # print(time.time()-self.start_time) # with this
        self.debug=parent.debug
        self.su=True #show me stuff others don't want/need
        self.su=False #not a superuser; make it easy on me!
        self.parent=parent #should be mainapplication frame
        self.frame=frame
        inherit(self)
        self.filename=file.getfilename()
        if not file.exists(self.filename):
            log.error("Didn't select a lexical database to check; exiting.")
            return
        filedir=file.getfilenamedir(self.filename)
        """We need this variable to make filenames for files that will be
        imported as python modules. To do that, they need to not have periods
        (.) in their filenames. So we take the base name from the lift file,
        and replace periods with underscores, to make our modules basename."""
        filenamebase=re.sub('\.','_',str(file.getfilenamebase(self.filename)))
        if not file.exists(filedir):
            log.info(_("Looks like there's a problem with your directory... {}"
                    "\n{}".format(self.filename,filemod)))
            exit()
        """This and the following bit should probably be in another lift
        class, in the main script. They make non lift-specific changes
        and assumptions about the database."""
        try:
            self.db=lift.Lift(self.filename,nsyls=nsyls)
        except lift.BadParseError:
            text=_("{} doesn't look like a well formed lift file; please "
                    "try again.").format(self.filename)
            print(text)
            log.info("'lift_url.py' removed.")
            window=Window(self)
            Label(window,text=text).grid(row=0,column=0)
            file.remove('lift_url.py') #whatever the problem was, remove it.
            window.wait_window(window) #Let the user see the error
            raise #Then force a quit and retry
        # self.db.filename=filename #in lift.py
        if not file.exists(self.db.backupfilename):
            self.db.write(self.db.backupfilename)
        else:
            print(_("Apparently we've run this before today; not backing "
            "up again."))
        # self.glosslangs=Glosslangs(None,None) #needed for upgrading
        self.settingsfilecheck(file.getdiredurl(filedir,filenamebase))
        self.imagesdir=file.getimagesdir(self.filename)
        self.audiodir=file.getaudiodir(self.filename)
        log.info('self.audiodir: {}'.format(self.audiodir))
        self.reportsdir=file.getreportdir(self.filename)
        self.reportbasefilename=file.getdiredurl(self.reportsdir, filenamebase)
        self.reporttoaudiorelURL=file.getreldir(self.reportsdir, self.audiodir)
        log.log(2,'self.reportsdir: {}'.format(self.reportsdir))
        log.log(2,'self.reportbasefilename: {}'.format(self.reportbasefilename))
        log.log(2,'self.reporttoaudiorelURL: {}'.format(self.reporttoaudiorelURL))
        # setdefaults.langs(self.db) #This will be done again, on resets
        self.loadsettingsfile(setting='toneframes')
        self.maketoneframes()
        self.loadsettingsfile(setting='adhocgroups')
        if nsyls is not None:
            self.nsyls=nsyls
        else:
            self.nsyls=2
        self.invalidchars=[' ','...',')','(<field type="tone"><form lang="gnd"><text>'] #multiple characters not working.
        self.invalidregex='( |\.|,|\)|\()+'
        # self.profilelegit=['#','̃','C','N','G','S','V','o'] #In 'alphabetical' order
        self.profilelegit=['#','̃','N','G','S','D','C','Ṽ','V','ʔ','ː',"̀",'=','<'] #'alphabetical' order

        """Are we OK without these?"""
        # self.guidtriage() #sets: self.guidswanyps self.guidswops self.guidsinvalid self.guidsvalid
        # self.guidtriagebyps() #sets self.guidsvalidbyps (dictionary keyed on ps)
        self.senseidtriage() #sets: self.senseidswanyps self.senseidswops self.senseidsinvalid self.senseidsvalid
        self.db.languagecodes=self.db.analangs+self.db.glosslangs
        self.db.languagepaths=file.getlangnamepaths(self.filename,
                                                        self.db.languagecodes)
        setdefaults.fields(self.db) #sets self.pluralname and self.imperativename
        self.initdefaults() #provides self.defaults, list to load/save
        self.cleardefaults() #this resets all to none (to be set below)
        """These two lines can import structured frame dictionaries; do this
        just to make the import, then comment them out again."""
        self.loadsettingsfile(setting='profiledata')
        """I think I need this before setting up regexs"""
        self.guessanalang() #needed for regexs
        log.info("analang guessed: {} (If you don't like this, change it in "
                    "the menus)".format(self.analang))
        self.maxprofiles=5 # how many profiles to check before moving on to another ps
        self.maxpss=2 #don't automatically give more than two grammatical categories
        self.loadsettingsfile() # overwrites guess above, stored on runcheck
        if self.analang is None:
            return
        self.notifyuserofextrasegments() #self.analang set by now
        if self.interfacelang not in [None, getinterfacelang()]:
            #set only when new value is loaded:
            setinterfacelang(self.interfacelang)
            self.parent.maketitle()
        self.langnames()
        self.polygraphcheck()
        self.checkinterpretations() #checks/sets values for self.distinguish
        self.slists() #lift>check segment dicts: s[lang][segmenttype]
        self.setupCVrxs() #creates self.rx dictionaries
        """The line above may need to go after this block"""
        if not hasattr(self,'profilesbysense') or self.profilesbysense == {}:
            log.info("Starting profile analysis at {}".format(time.time()
                                                            -self.start_time))
            log.debug("Starting ps-profile: {}-{}".format(ps,profile))
            self.getprofiles() #creates self.profilesbysense nested dicts
            for var in ['rx','profilesbysense','profilecounts']:
                log.debug("{}: {}".format(var,getattr(self,var)))
            log.debug("Middle ps-profile: {}-{}".format(ps,profile))
            self.storesettingsfile(setting='profiledata')
            log.debug("Ending ps-profile: {}-{}".format(ps,profile))
        self.makeparameters()
        self.makeslicedict()
        self.setnamesall() #sets self.checknamesall
        self.loadsettingsfile(setting='status')
        self.makestatus()
        #This can wait until runcheck, right?
        #     self.sortingstatus() #because this won't get set later #>checkdefaults?
        self.makeglosslangs()
        self.loadsettingsfile() # overwrites guess above, stored on runcheck
        #     self.guessglosslangs() #needed for the following
        self.datadict=FramedDataDict(self)
        log.info("Done initializing check; running first check check.")
        """Testing Zone"""
        #set None to make labels, else "raised" "groove" "sunken" "ridge" "flat"
        # n=self.db.getsensenode()
        # senseid="begin_7c6fe6a9-9918-48a8-bc3a-e88e61efa8fa"
        # RecordButtonFrame.makefilenames(check=self,senseid=senseid)
        # log.info(n)
        log.info("status type: {}".format(type(self.status)))
        self.mainlabelrelief()
        self.tableiteration=0
        self.checkcheck()
    def settingsfilecheck(self,basename):
        self.defaultfile=basename.with_suffix('.CheckDefaults.ini')
        self.toneframesfile=basename.with_suffix(".ToneFrames.ini")
        self.statusfile=basename.with_suffix(".VerificationStatus.dat")
        self.profiledatafile=basename.with_suffix(".ProfileData.dat")
        self.adhocgroupsfile=basename.with_suffix(".AdHocGroups.ini")
        self.soundsettingsfile=basename.with_suffix(".SoundSettings.ini")
        self.settingsbyfile() #This just sets the variable
        for setting in self.settings:#[setting]
            savefile=self.settingsfile(setting)#self.settings[setting]['file']
            if not file.exists(savefile):
                log.debug("{} doesn't exist!".format(savefile))
                legacy=savefile.with_suffix('.py')
                if file.exists(legacy):
                    log.debug("But legacy file {} does; converting!".format(legacy))
                    self.loadandconvertlegacysettingsfile(setting=setting)
    def checkforlegacyverification(self):
        start_time=time.time()
        n=0
        for ps in self.profilesbysense:
            for profile in self.profilesbysense[ps]:
                for senseid in self.profilesbysense[ps][profile]:
                    if profile is not 'Invalid':
                        node=self.db.legacyverificationconvert(senseid,vtype=profile,
                                                            lang=self.analang)
                        if node is not None:
                            n+=1
        self.db.write()
        log.info("Found {} legacy verification nodes in {} seconds".format(n,
                                                time.time()-start_time))
    """This should each be done only once, to make the objects from settings"""
    """self.profilesbysense and self.profilecounts are loaded from file, or
    created by analysis in init()"""
    def makeglosslangs(self):
        if not hasattr(self,'glosslangs'):
            self.guessglosslangs()
        self.glosslangs=Glosslangs(self.glosslangs)
    def maketoneframes(self):
        if not hasattr(self,'toneframes'):
            self.toneframes={}
        self.toneframes=ToneFrames(self.toneframes)
    def makeparameters(self):
        self.params=CheckParameters() #remove self.profilesbysense?
    def makeslicedict(self):
        if not hasattr(self,'adhocgroups'): #I.e., not loaded from file
            self.adhocgroups={}
        self.slices=SliceDict(self.params,self.adhocgroups,self.profilesbysense) #self.profilecounts
    def makestatus(self):
        log.info("makestatus")
        if not hasattr(self,'status'):
            self.status={}
        self.status=StatusDict(self.params,
                                self.slices,
                                self.toneframes,
                                self.settingsfile('status'),
                                self.status
                                )
        log.info("makestatus status type: {}".format(type(self.status)))
    def notifyuserofextrasegments(self):
        invalids=self.db.segmentsnotinregexes[self.analang]
        ninvalids=len(invalids)
        extras=list(dict.fromkeys(invalids).keys())
        if ninvalids >10:
            warning=Window(self, title="More than Ten Invalid Characters Found!")
            t=_("Your {} database has the following symbols, which are "
            "excluding {} words from being analyzed: \n{}"
                                    "".format(self.analang,ninvalids,extras))
            l=Label(warning, text=t)
            l.grid(row=0, column=0)
    """Guessing functions"""
    def guessanalang(self):
        #have this call set()?
        """if there's only one analysis language, use it."""
        nlangs=len(self.db.analangs)
        log.debug(_("Found {} analangs: {}".format(nlangs,self.db.analangs)))
        if nlangs == 1:
            self.analang=self.db.analangs[0]
            log.debug(_('Only one analang in file; using it: ({})'.format(
                                                        self.db.analangs[0])))
            """If there are more than two analangs in the database, check if one
            of the first two is three letters long, and the other isn't"""
        elif nlangs == 2:
            if ((len(self.db.analangs[0]) == 3) and
                (len(self.db.analangs[1]) != 3)):
                log.debug(_('Looks like I found an iso code for analang! '
                                        '({})'.format(self.db.analangs[0])))
                self.analang=self.db.analangs[0] #assume this is the iso code
                self.analangdefault=self.db.analangs[0] #In case it gets changed.
            elif ((len(self.db.analangs[1]) == 3) and
                    (len(self.db.analangs[0]) != 3)):
                log.debug(_('Looks like I found an iso code for analang! '
                                            '({})'.format(self.db.analangs[1])))
                self.analang=self.db.analangs[1] #assume this is the iso code
                self.analangdefault=self.db.analangs[1] #In case it gets changed.
            else:
                self.analang=self.db.analangs[0]
                log.debug('Neither analang looks like an iso code, taking the '
                'first one: {}'.format(self.db.analangs))
        else: #for three or more analangs, take the first plausible iso code
            for n in range(nlangs):
                if len(self.db.analangs[n]) == 3:
                    self.analang=self.db.analangs[n]
                    log.debug(_('Looks like I found an iso code for analang! '
                                            '({})'.format(self.db.analangs[n])))
                    return
            log.debug('None of more than three analangs look like an iso code, '
            'taking the first one: {}'.format(self.db.analangs))
            self.analang=self.db.analangs[0]
    def guessaudiolang(self):
        nlangs=len(self.db.audiolangs)
        """if there's only one audio language, use it."""
        if nlangs == 1: # print('Only one analang in database!')
            self.audiolang=self.db.audiolangs[0]
            """If there are more than two analangs in the database, check if one
            of the first two is three letters long, and the other isn't"""
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
    def getpss(self):
        pss=self.slices.pss() #make this one line, remove pss
        return pss
        #Why rebuild this here?
    def nextps(self,guess=False):
        """Make this smarter, but for now, just take value from the most
        populous tuple"""
        return self.slices.nextps()
    def nextprofile(self,guess=False):
        return self.slices.nextprofile()
    def nextframe(self,sort=True,guess=False):
        if len(todo) == 0:
            log.info("No frames to do; asking to define another one")
            self.addframe() #The above should change check, if completed.
            return
    def nextgroup(self,guess=False):
        def default():
            self.set('subcheck',priorities[0])
        cvt=self.params.cvt()
        if cvt != 'T': #only tone for now
            log.debug("Only working on tone for now, not {}".format(cvt))
            return
        if (not hasattr(self,'subchecksprioritized') or
                                cvt not in self.subchecksprioritized):
            self.getsubchecksprioritized()
        priorities=[x[0] for x in self.subchecksprioritized[cvt]
                            if x[0] is not None]
        if group in priorities:
            log.debug("group: {}".format(group))
            i=priorities.index(group)
            if len(priorities)>i+1:
                self.set('subcheck',priorities[i+1])
            else:
                default() #just iterate through for now
        else:
            default() #or guess == True): ever?
        log.debug("group: {}".format(group))
    def guesscvt(self):
        """For now, if cvt isn't set, start with Vowels."""
        self.set('cvt','V')
    def langnames(self):
        """This is for getting the prose name for a language from a code."""
        """It uses a xyz.ldml file, produced (at least) by WeSay."""
        #ET.register_namespace("", 'palaso')
        ns = {'palaso': 'urn://palaso.org/ldmlExtensions/v1'}
        node=None
        self.languagenames={}
        for xyz in self.db.analangs+self.db.glosslangs: #self.languagepaths.keys():
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
                self.languagenames[xyz]="Français"
            elif xyz == 'en':
                self.languagenames[xyz]="English"
            elif xyz == 'swc':
                self.languagenames[xyz]="Congo Swahili"
            elif xyz == 'swh':
                self.languagenames[xyz]="Swahili"
            elif xyz == 'gnd':
                self.languagenames[xyz]="Zulgo"
            elif xyz == 'fub':
                self.languagenames[xyz]="Fulfulde"
            elif xyz == 'bfj':
                self.languagenames[xyz]="Chufie’"
            else:
                self.languagenames[xyz]=_("Language with code "
                                                        "[{}]").format(xyz)
            if not hasattr(self,'adnlangnames') or self.adnlangnames is None:
                self.adnlangnames={}
            if xyz in self.adnlangnames and self.adnlangnames[xyz] is not None:
                self.languagenames[xyz]=self.adnlangnames[xyz]
    """User Input functions"""
    def getinterfacelang(self,event=None):
        log.info("Asking for interface language...")
        window=Window(self.frame, title=_('Select Interface Language'))
        Label(window.frame, text=_('What language do you want this program '
                                'to address you in?')
                ).grid(column=0, row=0)
        buttonFrame1=ButtonFrame(window.frame,
                                self.parent.interfacelangs,
                                self.setinterfacelangwrapper,
                                window
                                )
        buttonFrame1.grid(column=0, row=1)
    def checkinterpretations(self):
        if (not hasattr(self,'distinguish')) or (self.distinguish is None):
            self.distinguish={}
        if (not hasattr(self,'interpret')) or (self.interpret is None):
            self.interpret={}
        for var in ['G','Gwd','N','S','Swd','D','Dwd','Nwd','d','ː','ʔ','ʔwd']:
            if ((var not in self.distinguish) or
                (type(self.distinguish[var]) is not bool)):
                self.distinguish[var]=False
            if var == 'd':
                self.distinguish[var]=False #don't change this default, yet...
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
    def setSdistinctions(self):
        def notice(changed):
            def confirm():
                ok.value=True
                w.destroy()
            ti=_("Important Notice!")
            w=Window(self.frame,title=ti)
            til=Label(w.frame,text=ti,font=self.fonts['title'])
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
            Label(w.frame,text=t,wraplength=int(
                        self.frame.winfo_screenwidth()/2)).grid(row=1,column=0)
            for ps in pss:
                i=[x for x in self.profilesbysense[ps].keys()
                                    if set(d).intersection(set(x))]
                p="Profiles to check: {}".format(i)
                log.info(p)
                Label(w.frame,text=p).grid(row=2,column=0)
            ok=Object()
            ok.value=False
            b=Button(w.frame,text="OK, go ahead", command=confirm)
            b.grid(row=1,column=1)
            w.wait_window(w)
            return ok.value
        def submitform():
            def undo(changed):
                for s in changed:
                    if s in self.distinguish:
                        if self.distinguish[s]==changed[s][1]:
                            self.distinguish[s]=changed[s][0] #(oldvar,newvar):
                        else:
                            log.error("Changed to value ({}) doesn't match "
                            "current setting for ‘{}’: {}".format(changed[s][1],
                                                        s,self.distinguish[s]))
                    elif s in self.interpret:
                        if self.interpret[s]==changed[s][1]:
                            self.interpret[s]=changed[s][0] #(oldvar,newvar):
                        else:
                            log.error("Changed to value ({}) doesn't match "
                            "current setting for ‘{}’: {}".format(changed[s][1],
                                                        s,self.interpret[s]))
            r=True #only false if changes made, and user exits notice
            change=False
            changed={}
            for typ in ['distinguish', 'interpret']:
                for s in getattr(self,typ):
                    log.log(5,"Variable {} was: {}, now: {}, change: {}"
                            "".format(s,getattr(self,typ)[s],
                                        options.vars[s].get(),change))
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
                            change=True #I.e., something has changed
            log.debug('self.distinguish: {}'.format(self.distinguish))
            log.debug('self.interpret: {}'.format(self.interpret))
            if change:
                log.info('There was a change; we need to redo the analysis now.')
                self.storesettingsfile()
                log.info('The following changed (from,to): {}'.format(changed))
                if len(changed) >0:
                    r=notice(changed)
                # self.debug = True
                if self.debug != True and r:
                    self.reloadprofiledata()
                if r:
                    self.runwindow.destroy()
                else:
                    undo(changed)
            else:
                self.runwindow.destroy()
        def buttonframeframe(self):
            s=options.s
            f=options.frames[s]=Frame(self.runwindow.scroll.content)
            f.grid(row=options.get('r'),
                        column=options.get('c'),
                        sticky='ew', padx=options.padx, pady=options.pady)
            bffl=Label(f,text=options.text,justify=tkinter.LEFT,
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
                bffrb=RadioButtonFrame(f,
                                        var=options.vars[s],
                                        opts=options.opts)
                bffrb.grid(row=1,column=1)
            options.next('r') #self.runwindow.options['row']+=1
        self.getrunwindow()
        self.checkinterpretations()
        options=Options(r=0,padx=50,pady=10,c=0,vars={},frames={})
        for s in self.distinguish: #Should be already set.
            options.vars[s] = tkinter.BooleanVar()
            options.vars[s].set(self.distinguish[s])
        for s in self.interpret: #This should already be set, even by default
            options.vars[s] = tkinter.StringVar()
            options.vars[s].set(self.interpret[s])
        """Page title and instructions"""
        self.runwindow.title(_("Set Parameters for Segment Interpretation"))
        mwframe=self.runwindow.frame
        title=_("Interpret {} Segments"
                ).format(self.languagenames[self.analang])
        titl=Label(mwframe,text=title,font=self.fonts['title'],
                justify=tkinter.LEFT,anchor='c')
        titl.grid(row=options.get('r'), column=options.get('c'), #self.runwindow.options['column'],
                    sticky='ew', padx=options.padx, pady=10)
        options.next('r')
        text=_("Here you can view and set parameters that change how {} "
        "interprets {} segments \n(consonant and vowel glyphs/characters)"
                ).format(self.program['name'],self.languagenames[self.analang])
        instr=Label(mwframe,text=text,justify=tkinter.LEFT,anchor='c')
        instr.grid(row=options.get('r'), column=options.get('c'),
                    sticky='ew', padx=options.padx, pady=options.pady)
        """The rest of the page"""
        self.runwindow.scroll=ScrollingFrame(mwframe)
        self.runwindow.scroll.grid(row=2,column=0)
        log.debug('self.distinguish: {}'.format(self.distinguish))
        log.debug('self.interpret: {}'.format(self.interpret))
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
        options.text=_('Do you want to distinguish '
                        'initial and medial likely depressor consonants (D={})'
                        '\nfrom '
                        'other (simple/single) consonants?'
                        "").format(self.db.s[self.analang]['D'])
        options.opts=[(True,'D≠C'),(False,'D=C')]
        buttonframeframe(self)
        options.s='Dwd'
        options.text=_('Do you want to distinguish Word '
                        'Final likely depressor consonants (D={})'
                        '\nfrom '
                        'other (simple/single) consonants?'
                        "").format(self.db.s[self.analang]['D'])
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
        self.runwindow.frame2d=Frame(self.runwindow.scroll.content)
        self.runwindow.frame2d.grid(row=options.get('r'),
                    column=options.get('c'),
                    sticky='ew', padx=options.padx, pady=options.pady)
        sub_btn=Button(self.runwindow.frame2d,text = 'Use these settings',
                  command = submitform)
        sub_btn.grid(row=0,column=1,sticky='nw',pady=options.pady)
        nbtext=_("If you make changes, this button==> \nwill "
                "restart the program to reanalyze your data, \nwhich will "
                "take some time.")
        sub_nb=Label(self.runwindow.frame2d,text = nbtext, anchor='e')
        sub_nb.grid(row=0,column=0,sticky='e',
                    pady=options.pady)
        self.runwindow.waitdone()
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
            profile=profilevar.get()
            self.set('profile',profile,refresh=False) #checkcheck below
            #Add to dictionaries before updating them below
            log.debug("profile: {}".format(profile))
            """Fix this!"""
            self.slices.adhoc(ids)#[ps][profile]=ids
            """Is this OK?!?"""
            self.slices.updateslices()
            self.makecountssorted() #we need these to show up in the counts.
            self.storesettingsfile(setting='profiledata')#since we changed this.
            #so we don't have to do this again after each profile analysis
            self.storesettingsfile(setting='adhocgroups')
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
        Label(self.runwindow.frame,text=title,font=self.fonts['title'],
                ).grid(row=0,column=0,sticky='ew')
        allpssensids=self.slices.senseidsbyps()
        if len(allpssensids)>70:
            self.runwindow.waitdone()
            text=_("This is a large group ({})! Are you in the right "
                    "grammatical category?".format(len(allpssensids)))
            log.error(text)
            w=Label(self.runwindow.frame,text=text)
            w.grid(row=1,column=0,sticky='ew')
            b=Button(self.runwindow.frame, text="OK", command=w.destroy, anchor='c')
            b.grid(row=2,column=0,sticky='ew')
            self.runwindow.wait_window(w)
            w.destroy()
        if self.runwindow.exitFlag.istrue():
            return
        else:
            self.runwindow.wait()
        Label(self.runwindow.frame,text=title,font=self.fonts['title'],
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
        Label(self.runwindow.frame,text=text).grid(row=1,column=0,sticky='ew')
        qframe=Frame(self.runwindow.frame)
        qframe.grid(row=2,column=0,sticky='ew')
        text=_("What do you want to call this group for sorting {} words?"
                "".format(ps))
        Label(qframe,text=text).grid(row=0,column=0,sticky='ew',pady=20)
        if new:
            default=None
        else:
            default=profile
        profilevar=tkinter.StringVar(value=default)
        namefield = EntryField(qframe,textvariable=profilevar)
        namefield.grid(row=0,column=1)
        text=_("Select the {} words below that you want in this group, then "
                "click ==>".format(ps))
        Label(qframe,text=text).grid(row=1,column=0,sticky='ew',pady=20)
        sub_btn=Button(qframe,text = _("OK"),
                  command = submitform,anchor ='c')
        sub_btn.grid(row=1,column=1,sticky='w')
        vars=list()
        row=0
        scroll=ScrollingFrame(self.runwindow.frame)
        for id in allpssensids:
            log.debug("id: {}; index: {}; row: {}".format(id,
                                                    allpssensids.index(id),row))
            idn=allpssensids.index(id)
            vars.append(tkinter.StringVar())
            if id in self.slices.adhoc()[ps][profile]:
                vars[idn].set(id)
            else:
                vars[idn].set(0)
            framed=self.datadict.getframeddata(id)
            forms=framed.formatted(noframe=True)
            log.debug("forms: {}".format(forms))
            CheckButton(scroll.content, text = forms,
                                variable = vars[allpssensids.index(id)],
                                onvalue = id, offvalue = 0,
                                ).grid(row=row,column=0,sticky='ew')
            row+=1
        scroll.grid(row=3,column=0,sticky='ew')
        self.runwindow.waitdone()
        self.runwindow.wait_window(scroll)
    def addmorpheme(self):
        def makewindow(lang):
            def submitform(lang):
                self.runwindow.form[lang]=formfield.get()
                self.runwindow.frame2.destroy()
            def skipform(lang):
                self.runwindow.frame2.destroy() #Just move on.
            self.runwindow.frame2=Frame(self.runwindow)
            self.runwindow.frame2.grid(row=1,column=0,sticky='ew',padx=25,
                                                                        pady=25)
            if lang == self.analang:
                text=_("What is the form of the new {} "
                        "morpheme in {} \n(consonants and vowels only)?".format(
                                    ps,
                                    self.languagenames[lang]))
                ok=_('Use this form')
            elif lang in self.db.analangs:
                return
            else:
                text=_("What does {} ({}) mean in {}?".format(
                                            self.runwindow.form[self.analang],
                                            ps,
                                            self.languagenames[lang]))
                ok=_('Use this {} gloss for {}'.format(self.languagenames[lang],
                                            self.runwindow.form[self.analang]))
                self.runwindow.glosslangs.append(lang)
            getform=Label(self.runwindow.frame2,text=text,
                                                font=self.fonts['read'])
            getform.grid(row=0,column=0,padx=padx,pady=pady)
            form[lang]=tkinter.StringVar()
            eff=Frame(self.runwindow.frame2) #field rendering is better this way
            eff.grid(row=1,column=0)
            formfield = EntryField(eff, render=True, textvariable=form[lang])
            formfield.grid(row=1,column=0)
            formfield.rendered.grid(row=2,column=0,sticky='new')
            sub_btn=Button(self.runwindow.frame2,text = ok,
                      command = lambda x=lang:submitform(x),anchor ='c')
            sub_btn.grid(row=2,column=0,sticky='')
            if lang != self.analang:
                sub_btnNo=Button(self.runwindow.frame2,
                    text = _('Skip {} gloss').format(self.languagenames[lang]),
                    command = lambda lang=lang: skipform(lang))
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
        title=_("Add a {} {} morpheme to the dictionary").format(ps,
                            self.languagenames[self.analang])
        Label(self.runwindow,text=title,font=self.fonts['title'],
                justify=tkinter.LEFT,anchor='c'
                ).grid(row=0,column=0,sticky='ew',padx=padx,pady=pady)
        # Run the above script (makewindow) for each language, analang first.
        # The user has a chance to enter a gloss for any gloss language
        # already in the datbase, and to skip any as needed/desired.
        for lang in [self.analang]+self.db.glosslangs:
            if not self.runwindow.exitFlag.istrue():
                makewindow(lang)
        """get the new senseid back from this function, which generates it"""
        if not self.runwindow.exitFlag.istrue(): #don't do this if exited
            senseid=self.db.addentry(ps=ps,analang=self.analang,
                            glosslangs=self.runwindow.glosslangs,
                            form=self.runwindow.form)
            # Update profile information in the running instance, and in the file.
            self.getprofileofsense(senseid)
            self.status.updateslices()
            self.getscounts()
            self.storesettingsfile(setting='profiledata') #since we changed this.
            self.runwindow.destroy()
    def addframe(self):
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
                log.error(re.sub('\n','',text))
                if hasattr(self.addwindow,'framechk'):
                    self.addwindow.framechk.destroy()
                self.addwindow.framechk=Frame(self.addwindow.scroll.content)
                self.addwindow.framechk.grid(row=1,column=0,columnspan=3,sticky='w')
                l1=Label(self.addwindow.framechk,
                        text=text,
                        font=self.fonts['read'],
                        justify=tkinter.LEFT,anchor='w')
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
            senseid=self.gimmesenseidwgloss() #don't give exs w/o all glosses
            log.info('gimmesenseid result: {}'.format(senseid))
            """This will need to be updated to slices!"""
            if senseid not in [i for j in self.profilesbysense[self.ps].values()
                                                                    for i in j]:
                log.info('bad senseid; showing error')
                self.addwindow.framechk=Frame(self.addwindow.scroll.content)
                self.addwindow.framechk.grid(row=1,column=0,columnspan=3,sticky='w')
                lt=Label(self.addwindow.framechk,
                        text=senseid,
                        font=self.fonts['read'],
                        justify=tkinter.LEFT,anchor='w')
                lt.grid(row=0,column=0,#row=row,column=columnleft,
                        sticky='w',columnspan=2)
                del self.toneframes[self.ps][self.name]
                self.name=self.nameori
                return
            else:
                text=_("Examples for {} tone frame").format(namevar)
                log.info('gimmesenseid:{}'.format(senseid))
                # This needs self.toneframes
                log.info('getframeddata::')
                framed=self.datadict.getframeddata(senseid)
                log.info('getframeddata: {}'.format(framed.forms))
                framed.setframe(self.name)
                log.info('post setframe:{} ({})'.format(framed.framed,self.name))
                #At this point, remove this frame (in case we don't submit it)
                del self.toneframes[self.ps][self.name]
                self.name=self.nameori

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
            framed=self.datadict.getframeddata(senseid)
            framed.setframe(checktoadd)
            #At this point, remove this frame (in case we don't submit it)
            del self.toneframes[ps][checktoadd]
            """Display framed data"""
            if hasattr(self.addwindow,'framechk'):
                self.addwindow.framechk.destroy()
            self.addwindow.framechk=Frame(self.addwindow.scroll.content)
            self.addwindow.framechk.grid(row=1,column=0,columnspan=3,sticky='w')
            tf={}
            tfd={}
            padx=50
            pady=10
            row=0
            lt=Label(self.addwindow.framechk,
                    text="Examples for {} tone frame".format(checktoadd),
                    font=self.fonts['readbig'],
                    justify=tkinter.LEFT,anchor='w')
            lt.grid(row=row,column=columnleft,sticky='w',columnspan=2,
                    padx=padx,pady=pady)
            for lang in langs:
                row+=1
                tf[lang]=('form[{}]: {}'.format(lang,checkdefntoadd[lang]))
                tfd[lang]=('(ex: '+framed.forms.framed[lang]+')')
                l1=Label(self.addwindow.framechk,
                        text=tf[lang],
                        font=self.fonts['read'],
                        justify=tkinter.LEFT,anchor='w')
                l1.grid(row=row,column=columnleft,sticky='w',padx=padx,
                                                                pady=pady)
                l2=Label(self.addwindow.framechk,
                        text=tfd[lang],
                        font=self.fonts['read'],
                        justify=tkinter.LEFT,anchor='w')
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
            sub_btn=Button(self.addwindow.framechk,text = stext,
                      command = lambda x=checkdefntoadd,n=checktoadd: submit(x,n))
            sub_btn.grid(row=row,column=columnleft,sticky='w')
            log.info('sub_btn:{}'.format(stext))
            self.addwindow.scroll.tobottom()
            self.addwindow.scroll.windowsize() #make sure scroll's big enough
        def unchk(event):
            #This is here to keep people from thinking they are approving what's
            #next to this button, in case any variable has been changed.
            if hasattr(self.addwindow,'framechk'):
                self.addwindow.framechk.destroy()
        def submit(checkdefntoadd,name):
            # Having made and unset these, we now reset and write them to file.
            self.toneframes[ps][check]=checkdefntoadd
            self.status.renewchecks()
            self.storesettingsfile(setting='toneframes')
            self.addwindow.destroy()
        ps=self.slices.ps()
        wtitle=_("Define a New {} Tone Frame").format(ps)
        self.addwindow=Window(self.frame, title=wtitle)
        self.addwindow.scroll=ScrollingFrame(self.addwindow)
        self.addwindow.scroll.grid(row=0,column=0)
        self.addwindow.frame1=Frame(self.addwindow.scroll.content)
        self.addwindow.frame1.grid(row=0,column=0)
        row=0
        columnleft=0
        columnword=1
        columnright=2
        namevar=tkinter.StringVar()
        """Text and fields, before and after, dictionaries by language"""
        db={}
        langs=[self.analang]+self.glosslangs
        for context in ['before','after']:
            db[context]={}
            for lang in langs:
                db[context][lang]={}
                db[context][lang]['text']=tkinter.StringVar()
        t=(_("Add {} Tone Frame").format(ps))
        Label(self.addwindow.frame1,text=t+'\n',font=self.fonts['title']
                ).grid(row=row,column=columnleft,columnspan=3)
        row+=1
        t=_("What do you want to call the tone frame ?")
        finst=Frame(self.addwindow.frame1)
        finst.grid(row=row,column=0)
        Label(finst,text=t).grid(row=0,column=columnleft,sticky='e')
        name = EntryField(finst)
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
                                        self.languagenames[lang]))
                kind='form'
            else:
                ti[lang]=(_("Fill in the {} glossing "
                    "here \nas appropriate for the morphosyntactic context.\n("
                    "include a space to separate word glosses)"
                                ).format(self.languagenames[lang]))
                kind='gloss'
            tb[lang]=_("What text goes *before* \n<==the {} word *{}* "
                        "\nin the frame?"
                                ).format(self.languagenames[lang],kind)
            ta[lang]=_("What text goes *after* \nthe {} word *{}*==> "
                        "\nin the frame?"
                                ).format(self.languagenames[lang],kind)
        """Place the labels"""
        for lang in langs:
            f[lang]=Frame(self.addwindow.frame1)
            f[lang].grid(row=row,column=0)
            langrow=0
            Label(f[lang],text='\n'+ti[lang]+'\n').grid(
                                                row=langrow,column=columnleft,
                                                columnspan=3)
            langrow+=1
            Label(f[lang],text=tb[lang]).grid(row=langrow,
                                        column=columnright,sticky='w')
            Label(f[lang],text='word',padx=0,pady=0).grid(row=langrow,
                                                        column=columnword)
            db['before'][lang]['entryfield'] = EntryField(f[lang],
                                justify='right')
            db['before'][lang]['entryfield'].grid(row=langrow,
                                        column=columnleft,sticky='e')
            langrow+=1
            Label(f[lang],text=ta[lang]).grid(row=langrow,
                    column=columnleft,sticky='e')
            Label(f[lang],text='word',padx=0,pady=0).grid(row=langrow,
                    column=columnword)
            db['after'][lang]['entryfield'] = EntryField(f[lang],
                    justify='left')
            db['after'][lang]['entryfield'].grid(row=langrow,
                    column=columnright,sticky='w')
            for w in ['before','after']:
                db[w][lang]['entryfield'].bind('<Key>', unchk)
            row+=1
        row+=1
        text=_('See the tone frame around a word from the dictionary')
        chk_btn=Button(self.addwindow.frame1,text = text, command = chk)
        chk_btn.grid(row=row+1,column=columnleft,pady=100)
    def setsoundhz(self,choice,window):
        self.soundsettings.fs=choice
        window.destroy()
        self.soundcheckrefresh()
    def setsoundformat(self,choice,window):
        self.soundsettings.sample_format=choice
        window.destroy()
        self.soundcheckrefresh()
    def getsoundformat(self):
        log.info("Asking for audio format...")
        window=Window(self.frame, title=_('Select Audio Format'))
        Label(window.frame, text=_('What audio format do you '
                                    'want to work with?')
                ).grid(column=0, row=0)
        l=list()
        ss=self.soundsettings
        for sf in ss.cards['in'][ss.audio_card_in][ss.fs]:
            name=ss.hypothetical['sample_formats'][sf]
            l+=[(sf, name)]
        buttonFrame1=ButtonFrame(window.frame,l,self.setsoundformat,window)
        buttonFrame1.grid(column=0, row=1)
    def getsoundhz(self):
        log.info("Asking for sampling frequency...")
        window=Window(self.frame, title=_('Select Sampling Frequency'))
        Label(window.frame, text=_('What sampling frequency you '
                                    'want to work with?')
                ).grid(column=0, row=0)
        l=list()
        ss=self.soundsettings
        for fs in ss.cards['in'][ss.audio_card_in]:
            name=ss.hypothetical['fss'][fs]
            l+=[(fs, name)]
        buttonFrame1=ButtonFrame(window.frame,l,self.setsoundhz,window)
        buttonFrame1.grid(column=0, row=1)
    def setsoundcardindex(self,choice,window):
        self.soundsettings.audio_card_in=choice
        window.destroy()
        self.soundcheckrefresh()
    def setsoundcardoutindex(self,choice,window):
        self.soundsettings.audio_card_out=choice
        window.destroy()
        self.soundcheckrefresh()
    def getsoundcardindex(self):
        log.info("Asking for input sound card...")
        window=Window(self.frame, title=_('Select Input Sound Card'))
        Label(window.frame, text=_('What sound card do you '
                                    'want to record sound with with?')
                ).grid(column=0, row=0)
        l=list()
        for card in self.soundsettings.cards['in']:
            name=self.soundsettings.cards['dict'][card]
            l+=[(card, name)]
        buttonFrame1=ButtonFrame(window.frame,l,self.setsoundcardindex,window)
        buttonFrame1.grid(column=0, row=1)
    def getsoundcardoutindex(self):
        log.info("Asking for output sound card...")
        window=Window(self.frame, title=_('Select Output Sound Card'))
        Label(window.frame, text=_('What sound card do you '
                                    'want to play sound with?')
                ).grid(column=0, row=0)
        l=list()
        for card in self.soundsettings.cards['out']:
            name=self.soundsettings.cards['dict'][card]
            l+=[(card, name)]
        buttonFrame1=ButtonFrame(window.frame,l,self.setsoundcardoutindex,
                                                                        window)
        buttonFrame1.grid(column=0, row=1)
    """Set User Input"""
    def refreshattributechanges(self):
        """I need to think through these; what things must/should change when
        one of these attributes change? Especially when we've changed a few...
        """
        self.status.build()
        if 'cvt' in self.attrschanged:
            self.status.renewchecks()
            self.slices.makeprofileok()
            self.attrschanged.remove('cvt')
        if 'ps' in self.attrschanged:
            t=self.params.cvt()
            if t == 'T':
                self.status.renewchecks()
            self.attrschanged.remove('ps')
        if 'profile' in self.attrschanged:
            self.newattr.remove('profile')
        if 'check' in self.attrschanged:
            self.attrschanged.remove('check')
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
    def setinterfacelangwrapper(self,choice,window):
        setinterfacelang(choice) #change the UI *ONLY*; no object attributes
        file.writeinterfacelangtofile(choice) #>ui_lang.py, for startup
        self.set('interfacelang',choice,window) #set variable for the future
        self.storesettingsfile() #>xyz.CheckDefaults.py
        self.parent.maketitle() #because otherwise, this stays as is...
    def setprofile(self,choice,window):
        self.slices.profile(choice)
        self.attrschanged.append('profile')
        self.refreshattributechanges()
        window.destroy()
    def setcvt(self,choice,window):
        self.params.cvt(choice)
        self.attrschanged.append('cvt')
        self.refreshattributechanges()
    def setanalang(self,choice,window):
        self.set('analang',choice,window)
    def setgroup(self,choice,window):
        log.debug("group: {}".format(group))
        self.status.group(choice)
        # self.set('subcheck',choice,window)
        log.debug("group: {}".format(group))
    def setsubcheck_comparison(self,choice,window):
        if hasattr(self,'subcheck_comparison'):
            log.debug("subcheck_comparison: {}".format(self.subcheck_comparison))
        self.set('subcheck_comparison',choice,window,refresh=False)
        log.debug("subcheck_comparison: {}".format(self.subcheck_comparison))
    def setcheck(self,choice,window):
        self.params.check(choice)
        self.attrschanged.append('check')
        self.refreshattributechanges()
        window.destroy()
    def setglosslang(self,choice,window):
        self.glosslangs.lang1(choice)
        self.attrschanged.append('glosslangs')
        self.refreshattributechanges()
        window.destroy()
    def setglosslang2(self,choice,window):
        if choice is not None:
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
    def getgroup(self,guess=False,cvt=None,event=None,comparison=False):
        log.info("this sets the subcheck")
        self.refreshattributechanges()
        if cvt is None:
            cvt=self.params.cvt()
        if cvt == "V":
            w=Window(self.frame,title=_('Select Vowel'))
            self.getV(window=w)
            w.wait_window(window=w)
        elif cvt == "C":
            w=Window(self.frame,title=_('Select Consonant'))
            self.getC(w)
            self.frame.wait_window(window=w)
        elif cvt == "CV":
            CV=''
            for cvt in ['C','V']:
                self.getsubcheck(cvt=cvt)
                CV+=group
            group=CV
            cvt = "CV"
        elif cvt == "T":
            w=Window(self.frame,title=_('Select Framed Tone Group'))
            self.getframedtonegroup(window=w,guess=guess,
                                                        comparison=comparison)
            # windowT.wait_window(window=windowT) #?!?
        return w #so others can wait for this
    def getps(self,event=None):
        log.info("Asking for ps...")
        self.refreshattributechanges()
        window=Window(self.frame, title=_('Select Grammatical Category'))
        Label(window.frame, text=_('What grammatical category do you '
                                    'want to work with (Part of speech)?')
                ).grid(column=0, row=0)
        if self.additionalps is not None:
            pss=self.db.pss+self.additionalps #these should be lists
        else:
            pss=self.db.pss
        buttonFrame1=ScrollingButtonFrame(window.frame,pss,self.setps,window)
        buttonFrame1.grid(column=0, row=1)
    def getprofile(self,event=None):
        log.info("Asking for profile...")
        self.refreshattributechanges()
        window=Window(self.frame,title=_('Select Syllable Profile'))
        ps=self.slices.ps()
        if self.profilesbysense[ps] is None: #likely never happen...
            Label(window.frame,
            text=_('Error: please set Grammatical category with profiles '
                    'first!')+' (not '+str(ps)+')'
            ).grid(column=0, row=0)
        else:
            profilecounts=self.slices.valid()
            profilecountsAdHoc=self.slices.adhoccounts()
            pcall=profilecounts+profilecountsAdHoc
            Label(window.frame, text=_('What ({}) syllable profile do you '
                                    'want to work with?'.format(ps))
                                    ).grid(column=0, row=0)
            optionslist = [(x[0],pcall[x]) for x in pcall]
            window.scroll=Frame(window.frame)
            window.scroll.grid(column=0, row=1)
            buttonFrame1=ScrollingButtonFrame(window.scroll,
                                    optionslist,self.setprofile,
                                    window
                                    )
            buttonFrame1.grid(column=0, row=0)
    def getcvt(self,event=None):
        log.debug(_("Asking for check cvt/type"))
        window=Window(self.frame,title=_('Select Check Type'))
        cvts=[]
        x=0
        tdict=self.params.cvtdict()
        for cvt in tdict:
            cvts.append({})
            cvts[x]['name']=tdict[cvt]['pl']
            cvts[x]['code']=cvt
            x+=1
        Label(window.frame, text=_('What part of the sound system do you '
                                    'want to work with?')
            ).grid(column=0, row=0)
        buttonFrame1=ButtonFrame(window.frame,cvts,self.setcvt,window)
        buttonFrame1.grid(column=0, row=1)
    """Settings to and from files"""
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
                        'subcheck_comparison':[],
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
                                'maxprofiles'
                                ]},
            'profiledata':{
                                'file':'profiledatafile',
                                'attributes':[
                                    'distinguish',
                                    'interpret',
                                    'polygraphs',
                                    "profilecounts",
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
    def cleardefaults(self,field=None):
        if field==None:
            fields=self.settings['defaults']['attributes']
        else:
            fields=self.defaultstoclear[field]
        for default in fields: #self.defaultstoclear[field]:
            setattr(self, default, None)
            """These can be done in checkcheck..."""
    def restart(self):
        self.parent.parent.destroy()
        main()
    def changedatabase(self):
        log.debug("Removing lift_url.py, so user will be asked again for LIFT")
        self.filename=None #since this will still be in memory
        file.removelifturl()
        self.restart()
    def reloadprofiledata(self):
        self.storesettingsfile()
        self.profilesbysense={}
        self.storesettingsfile(setting='profiledata')
        self.restart()
    def reloadstatusdata(self):
        # This fn is very inefficient, as it iterates over everything in
        # profilesbysense, creating status dictionaries for all of that, in
        # order to populate it if found —before removing empty entires.
        # This also has no access to verification information, which comes only
        # from verifyT()
        self.storesettingsfile()
        pss=self.slices.pss() #this depends on nothing
        for t in self.params.cvts(): #this depends on nothing
            for ps in pss:
                profiles=self.slices.profiles(ps=ps) #This depends on ps only
                for profile in profiles:
                    checks=self.status.checks()
                    for c in checks:
                        self.status.build(t,ps,profile,c)
                        """this just populates groups and the tosort boolean."""
                        self.settonevariablesiterable(cvt=t, ps=ps,
                                                profile=profile, check=check)
        """Now remove what didn't get data"""
        self.status.cull()
        if None in self.status: #This should never be there
            del self.status[None]
        self.storesettingsfile(setting='status')
    def settingsfile(self,setting):
        fileattr=self.settings[setting]['file']
        if hasattr(self,fileattr):
            return getattr(self,fileattr)
        else:
            log.error("No file name for setting {}!".format(setting))
    def settingsobjects(self):
        """These should each push and pull values to/from objects"""
        fns={}
        try: #these objects may not exist yet
            fns['cvt']=self.params.cvt
            fns['check']=self.params.check
            fns['glosslang']=self.glosslangs.lang1
            fns['glosslang2']=self.glosslangs.lang2
            fns['glosslangs']=self.glosslangs.langs
            fns['check']=self.params.check
            fns['ps']=self.slices.ps
            fns['profile']=self.slices.profile
            # except this one, which pretends to set but doesn't (throws arg away)
            fns['profilecounts']=self.slices.slicepriority
            return fns
        except:
            log.error("Only finished settingsobjects up to {}".format(fns))
            return []
    def makesettingsdict(self,setting='defaults'):
        """This returns a dictionary of values, keyed by a set of settings"""
        """It pulls from objects if it can, otherwise from self attributes
        (if there), for backwards compatibility"""
        d={}
        objectfns=self.settingsobjects()
        if setting == 'soundsettings':
            o=self.soundsettings
        else:
            o=self
        for s in self.settings[setting]['attributes']:
            if s in objectfns:
                log.debug("Trying to dict {} attr".format(s))
                try:
                    d[s]=objectfns[s]()
                    log.debug("Value {}={} found in object".format(s,d[s]))
                except:
                    log.debug("Value of {} not found in object".format(s))
            elif hasattr(o,s):# and getattr(o,s) is not None:
                d[s]=getattr(o,s)
                log.debug("Trying to dict self.{} with value {}, type {}"
                        "".format(s,d[s],type(d[s])))
            else:
                log.error("Couldn't find {} in {}".format(s,setting))
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
        objectfns=self.settingsobjects()
        if 'fs' in dict:
            o=self.soundsettings
        else:
            o=self
        for s in dict:
            v=d[s]
            if s in objectfns:
                log.debug("Trying to read {} to object with value {} and fn "
                            "{}".format(s,v,objectfns[s]))
                objectfns[s](v)
            else:
                log.debug("Trying to read {} to self with value {}, type {}"
                            "".format(s,v,type(v)))
                setattr(o,s,v)
        return d
    def storesettingsfile(self,setting='defaults',noobjects=False):
        filename=self.settingsfile(setting)
        config=ConfigParser()
        config['default']={}
        d=self.makesettingsdict(setting=setting)
        for s in d:
            v=d[s]
            if isinstance(v, dict):
                config[s]=v
            else:
                config['default'][s]=str(v)
        if config['default'] == {}:
            del config['default']
        with open(filename, "w", encoding='utf-8') as file:
            config.write(file)
    def makesoundsettings(self):
        if not hasattr(self,'soundsettings'):
            self.pyaudiocheck() #in case self.pyaudio isn't there yet
            self.soundsettings=sound.SoundSettings(self.pyaudio)
    def loadsoundsettings(self):
        self.makesoundsettings()
        self.loadsettingsfile(setting='soundsettings')
    def loadandconvertlegacysettingsfile(self,setting='defaults'):
        savefile=self.settingsfile(setting)
        legacy=savefile.with_suffix('.py')
        log.info("Going to make {} into {}".format(legacy,savefile))
        if setting == 'soundsettings':
            self.makesoundsettings()
            o=self.soundsettings
        else:
            o=self
        try:
            log.debug("Trying for {} settings in {}".format(setting, legacy))
            spec = importlib.util.spec_from_file_location(setting,legacy)
            module = importlib.util.module_from_spec(spec)
            sys.modules[setting] = module
            spec.loader.exec_module(module)
            for s in self.settings[setting]['attributes']:
                if hasattr(module,s):
                    setattr(o,s,getattr(module,s))
        except:
            log.error("Problem importing {}".format(legacy))
        if 'glosslangs' in self.settings[setting]['attributes']:
            self.glosslangs=[getattr(module,'glosslang'),
                        getattr(module,'glosslang2')] # b/c structure changed
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
    def loadsettingsfile(self,setting='defaults'):
        filename=self.settingsfile(setting)
        config=ConfigParser()
        config.read(filename)
        if len(config.sections()) == 0:
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
    """These should all go!"""
    def makestatusdictps(self,cvt=None,ps=None):
        if cvt is None:
            self.params.cvt()
        if ps is None:
            self.slices.ps()
        self.status.build(cvt=cvt,ps=ps)
        return
    def makestatusdictprofile(self,cvt=None,ps=None,profile=None):
        if cvt is None:
            self.params.cvt()
        if ps is None:
            self.slices.ps()
        if profile is None:
            self.slices.profile()
        self.status.build(cvt=cvt,ps=ps,profile=profile)
        return
    def makestatusdict(self,cvt=None,ps=None,profile=None,check=None):
        self.status.build()
        return
    def verifictioncode(self,check=None,subcheck=None):
        if subcheck is None: #do I ever want this to really be None?
            subcheck=self.params.subcheck()
        if check is None:
            check=self.params.check()
        return check+'='+subcheck
    def updatestatuslift(self,check=None,group=None,verified=False,refresh=True):
        if group is None: #do I ever want this to really be None?
            group=self.status.group()
        if check is None:
            check=self.params.check()
        profile=self.slices.profile()
        senseids=self.db.get("sense", location=check, tonevalue=group,
                            path=['tonefield']).get('senseid')
        value=self.verifictioncode(check,group)
        if verified == True:
            add=value
            rms=[]
        else:
            add=None
            rms=[value]
        """The above doesn't test for profile, so we restrict that next"""
        for senseid in self.slices.inslice(senseids): #only for this ps-profile
            rms+=self.db.getverificationnodevaluebyframe(senseid,
                            vtype=profile, analang=self.analang, frame=check)
            log.info("Removing {}".format(rms))
            self.db.modverificationnode(senseid,vtype=profile,add=add,rms=rms)
        if refresh == True:
            self.db.write() #for when not iterated over, or on last repeat
    def updatestatus(self,group=None,verified=False,refresh=True):
        #This function updates the status variable, not the lift file.
        self.status.update(group=group,verified=verified)
        return
    """Get from LIFT database functions"""
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
            ps=self.slices.ps()
        self.addpstoprofileswdata(ps=ps)
        if profile is None:
            profile=self.slices.profile()
        self.addprofiletoprofileswdata(ps=ps,profile=profile)
        self.profilesbysense[ps][profile]+=[senseid]
    def getscounts(self):
        """This depends on self.sextracted, from getprofiles, so should only
        run when that changes."""
        scount={}
        for ps in self.db.pss:
            scount[ps]={}
            for s in self.rx:
                scount[ps][s]=sorted([(x,self.sextracted[ps][s][x])
                    for x in self.sextracted[ps][s]],key=lambda x:x[1],
                                                                reverse=True)
        self.slices.scount(scount) #send to object
    def getprofileofsense(self,senseid):
        #Convert to iterate over local variables
        ps=unlist(self.db.ps(senseid=senseid))
        forms=self.db.citationorlexeme(senseid=senseid,analang=self.analang)
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
        self.makeadhocgroupsdict() #if no file, before iterating over variable
        """Do I want this? better to keep the adhoc groups separate"""
        adhoc=self.slices.adhoc()
        for ps in adhoc:
            for a in adhoc[ps]:
                log.debug("Adding {} to {} ps-profile: {}".format(a,ps,
                                            self.adhocgroups[ps][a]))
                self.addpstoprofileswdata(ps=ps) #in case the ps isn't already there
                #copy over stored values:
                self.profilesbysense[ps][a]=adhoc[ps][a]
                log.debug("resulting profilesbysense: {}".format(
                                        self.profilesbysense[ps][a]))
        self.slices.updateslices()
        self.getscounts() #after getprofileofsense
        # print('Done:',time.time()-self.start_time)
        if self.debug==True:
            for ps in self.profilesbysense:
                for profile in self.profilesbysense[ps]:
                    log.debug("ps: {}; profile: {} ({})".format(ps,profile,
                            len(self.profilesbysense[ps][profile])))
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
    def askaboutpolygraphs(self):
        def nochanges(changemarker):
            changemarker.value=False
            pgw.destroy()
        changemarker=Object()
        changemarker.value=True
        nochangetext=_("Exit with no changes")
        log.info("Asking about Digraphs and Trigraphs!")
        pgw=Window(self.frame,title="A→Z+T Digraphs and Trigraphs")
        t=_("Select which of the following graph sequences found in your data "
                "refer to a single sound (digraph or trigraph) in {}".format(
            unlist([self.languagenames[y] for y in self.db.analangs])))
        title=Label(pgw.frame,text=t)
        title.grid(column=0, row=0)
        t=_("If you use a digraph or trigraph that isn't listed here, please "
            "click here to Email me, and I can add it.")
        t2=Label(pgw.frame,text=t)
        t2.grid(column=0, row=1)
        t2.bind("<Button-1>", lambda e: openweburl(eurl))
        t=_("Closing this window will restart {} and trigger another syllable "
            "profile analysis. \nIf you don't want that, click ‘{}’ ==>".format(
                                                program['name'],nochangetext))
        t3=Label(pgw.frame,text=t)
        t3.grid(column=0, row=2)
        eurl='mailto:{}?subject=New trigraph or digraph to add (today)'.format(
                                                            program['Email'])
        b=Button(pgw.frame,text=nochangetext,
                    command=lambda x=changemarker:nochanges(x))
        b.grid(column=1, row=2)
        if not hasattr(self,'polygraphs'):
            self.polygraphs={}
        vars={}
        scroll=ScrollingFrame(pgw.frame)
        scroll.grid(row=3, column=0)
        row=0
        ncols=4 # increase this for wider window
        for lang in self.db.analangs:
            if lang not in self.polygraphs:
                self.polygraphs[lang]={}
            row+=1
            title=Label(scroll.content,text=self.languagenames[lang],
                                                        font=self.fonts['read'])
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
                    header=Label(scroll.content,
                    text=sclass.replace('dg',' (digraph)').replace('tg',
                                                            ' (trigraph)')+': ')
                    header.grid(column=0, row=row)
                col=1
                for pg in self.db.s[lang][sclass]:
                    vars[lang][pclass][pg] = tkinter.BooleanVar()
                    vars[lang][pclass][pg].set(
                                    self.polygraphs[lang][pclass].get(pg,False))
                    cb=CheckButton(scroll.content, text = pg, #.content
                                        variable = vars[lang][pclass][pg],
                                        onvalue = True, offvalue = False,
                                        )
                    cb.grid(column=col, row=row,sticky='nsew')
                    if col<= ncols:
                        col+=1
                    else:
                        col=1 #not header
                        row+=1
        pgw.wait_window(pgw)
        if changemarker.value and not self.exitFlag.istrue():
            log.info("Changes called for (like it or not!), redoing analysis.")
            for lang in self.db.analangs:
                for pc in vars[lang]:
                    for pg in vars[lang][pc]:
                        self.polygraphs[lang][pc][pg]=vars[lang][pc][pg].get()
            self.storesettingsfile(setting='profiledata')
            self.reloadprofiledata()
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
    def setupCVrxs(self):
        self.rx={}
        for sclass in list(self.s[self.analang]):
            if self.s[self.analang][sclass] != []: #don't make if empty
                self.rx[sclass]=rx.make(rx.s(self,sclass),compile=True)
        #Compile preferred regexs here
        for cc in ['CG','CS','NC','VN','VV']:
            ccc=cc.replace('C','[CSGDʔN]{1}')
            self.rx[cc]=re.compile(ccc)
        for c in ['N','S','G','ʔ','D']:
            if c == 'N': #i.e., before C
                self.rx[c+'_']=re.compile(c+'(?!([CSGDʔ]|\Z))') #{1}|
            elif c in ['ʔ','D']:
                self.rx[c+'_']=re.compile(c+'(?!\Z)')
            else:
                self.rx[c+'_']=re.compile('(?<![CSGDNʔ])'+c)
            self.rx[c+'wd']=re.compile(c+'(?=\Z)')
    def profileofformpreferred(self,form):
        """Simplify combinations where desired"""
        for c in ['N','S','G','ʔ','D']:
            if self.distinguish[c] is False:
                form=self.rx[c+'_'].sub('C',form)
            if self.distinguish[c+'wd'] is False:
                form=self.rx[c+'wd'].sub('C',form)
        for cc in ['CG','CS','NC','VN','VV']:
            form=self.rx[cc].sub(self.interpret[cc],form)
        return form
    def profileofform(self,form,ps):
        if form is None:
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
        if self.debug==True:
            self.iterations+=1
            if self.iterations>15:
                exit()
        # log.debug("{}: {}".format(formori,form))
        # log.info("Form before simplification:{}".format(form))
        form=self.profileofformpreferred(form)
        # log.info("Form after simplification:{}".format(form))
        return form
    def gimmeguid(self):
        idsbyps=self.db.get('guidbyps',lang=self.analang,ps=ps)
        return idsbyps[randint(0, len(idsbyps))]
    def gimmesenseidwgloss(self):
        tried=0
        gloss={}
        langs=[self.glosslang,self.glosslang2]
        for lang in langs:
            gloss[lang]=''
        while '' in gloss.values():
            senseid=self.gimmesenseid()
            for lang in langs:
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
    def gimmesenseid(self):
        idsbyps=self.db.get('sense',ps=ps).get('senseid')
        return idsbyps[randint(0, len(idsbyps)-1)]
    def framenamesbyps(self,ps):
        """Names for all tone frames defined for the language."""
        return self.status.checks()
        if hasattr(self,'toneframes') and self.toneframes is not None:
            if ps not in self.toneframes:
                self.toneframes[ps]={}
            else:
                return list(self.toneframes[ps].keys())
        #     else:
        #         return []
        # else:
        return []
    def frame1valuebynamepsprofile(self):
        """I think this function is obsolete."""
        """Define self.location based on lookup of check"""
        """This should be done after ps and check name are set"""
        self.location=self.toneframes[ps][check]['location']
    def framevaluesbynamepsprofile(self,ps,profile,name):
        """Tone group values actually used in a frame,
        by frame name, and by data ps and profile."""
        l=[]
        for guid in self.db.profileswdata[ps][profile]:
            group=self.db.get('pronunciationfieldvalue',guid=guid,
                                fieldtype='tone',
                                location=check)
            l+=group
        return list(dict.fromkeys(l))
    """Mediating between LIFT and the user"""
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
    """Making the main window"""
    def mainlabelrelief(self,relief=None,refresh=False,event=None):
        #set None to make this a label instead of button:
        log.log(3,"setting button relief to {}, with refresh={}".format(relief,
                                                                    refresh))
        self.mainrelief=relief # None "raised" "groove" "sunken" "ridge" "flat"
    def setrefreshdelay(self):
        """This sets the main window refresh delay, in miliseconds"""
        if hasattr(self,'runwindow') and self.runwindow.winfo_exists():
            self.refreshdelay=10000 #ten seconds if working in another window
        else:
            self.refreshdelay=1000 #one second if not working in another window
    def checkcheck(self,dict=None):
        """This checks for incompatible or missing variable values, and asks
        for them. If values are OK, they are displayed."""
        dictnow={'cvt':self.params.cvt(),
                'check':self.params.check(),
                'ps':self.slices.ps(),
                'profile':self.slices.profile(),
                'group':self.status.group(),
                'tableiteration':self.tableiteration
                }
        """Call this just once. If nothing changed, wait; if changes, run,
        then run again."""
        if dict == dictnow:
            self.setrefreshdelay()
            self.parent.after(self.refreshdelay, self.checkcheck, dictnow)
            return
        log.info("Dict changes; checking attributes and updating the UI.")
        inherit(self) #in case anything has changed (like font size)
        opts={
        'row':0,
        'labelcolumn':0,
        'valuecolumn':1,
        'buttoncolumn':2,
        'labelxpad':15,
        'width':None, #10
        'columnspan':3,
        'columnplus':0}
        def proselabel(opts,label,parent=None,cmd=None,tt=None):
            if parent is None:
                parent=self.frame.status
                column=opts['labelcolumn']
                row=opts['row']
                columnspan=opts['columnspan']
                ipadx=opts['labelxpad']
            else:
                column=0+opts['columnplus']
                row=0
                columnspan=1
                ipadx=0
            print(label, opts['labelcolumn'],opts['columnspan'])
            if self.mainrelief == None:
                l=Label(parent, text=label,font=self.fonts['report'],anchor='w')
            else:
                l=Button(parent,text=label,font=self.fonts['report'],anchor='w',
                    relief=self.mainrelief)
            l.grid(column=column, row=row, columnspan=columnspan,
                    ipadx=ipadx, sticky='w')
            if cmd is not None:
                l.bind('<ButtonRelease>',getattr(self,str(cmd)))
            if tt is not None:
                ttl=ToolTip(l,tt)
        def labels(parent,opts,label,value):
            Label(self.frame.status, text=label).grid(
                    column=opts['labelcolumn'], row=opts['row'],
                    ipadx=opts['labelxpad'], sticky='w'
                    )
            Label(self.frame.status, text=value).grid(
                    column=opts['valuecolumn'], row=opts['row'],
                    ipadx=opts['labelxpad'], sticky='w'
                    )
        def button(opts,text,fn=None,column=opts['labelcolumn'],**kwargs):
            """cmd overrides the standard button command system."""
            Button(self.frame.status, choice=text, text=text, anchor='c',
                            cmd=fn, width=opts['width'], **kwargs
                            ).grid(column=column, row=opts['row'],
                                    columnspan=opts['columnspan'])
        #If the user exits out before this point, just stop.
        try:
            self.frame.winfo_exists()
        except:
            self.frame.parent.waitdone()
            return
        self.makestatusframe() # wait is here, after the first time.
        #Don't guess this; default or user set only
        log.info('Interfacelang: {}'.format(getinterfacelang()))
        """This just gets the prose language name from the code"""
        for l in self.parent.interfacelangs:
            if l['code']==getinterfacelang():
                interfacelanguagename=l['name']
        t=(_("Using {}").format(interfacelanguagename))
        proselabel(opts,t,cmd='getinterfacelang')
        opts['row']+=1
        """We start with the settings that we can likely guess"""
        """Get Analang"""
        if self.analang not in self.db.analangs:
            self.guessanalang()
        if self.analang is None:
            log.info("find the language")
            self.getanalang()
            return
        if self.audiolang is None:
            self.guessaudiolang() #don't display this, but make it
        t=(_("Working on {}").format(self.languagenames[self.analang]))
        if (self.languagenames[self.analang] == _("Language with code [{}]"
                                                    "").format(self.analang)):
            proselabel(opts,t,cmd='getanalangname',
                                            tt=_("Set analysis language Name"))
        else:
            proselabel(opts,t,cmd='getanalang',
                                            tt=_("Change analysis language"))
        opts['row']+=1
        """Get glosslang"""
        for lang in self.glosslangs:
            if lang not in self.db.glosslangs:
                self.glosslangs.rm(lang)
        if len(self.glosslangs) == 0:
            self.guessglosslangs()
        t=(_("Meanings in {}").format(self.languagenames[self.glosslangs[0]]))
        tf=Frame(self.frame.status)
        tf.grid(row=opts['row'],column=0,columnspan=3,sticky='w')
        proselabel(opts,t,cmd='getglosslang',parent=tf)
        opts['columnplus']=1
        if len(self.glosslangs) >1:
            t=(_("and {}").format(self.languagenames[self.glosslangs[1]]))
        else:
            t=_("only")
        proselabel(opts,t,cmd='getglosslang2',parent=tf)
        opts['columnplus']=0
        opts['row']+=1
        self.status.makecvtok()
        cvt=self.params.cvt()
        """These settings must be set (for now); we can't guess them (yet)"""
        """Ultimately, we will pick the largest ps/profile combination as an
        initial default (obviously changeable, as are all)"""
        """Get ps"""
        self.slices.makepsok()
        """Get profile (this depends on ps)"""
        self.slices.makeprofileok()
        ps=self.slices.ps()
        profile=self.slices.profile()
        log.debug("ps:{}; profile:{}; self.profilesbysense type: {}".format(ps,profile,type(self.profilesbysense)))
        if ((ps in self.profilesbysense) and
                (profile in self.profilesbysense[ps])):
            count=len(self.profilesbysense[ps][profile])
        else:
            count=0
        tf=Frame(self.frame.status)
        tf.grid(row=opts['row'],column=0,columnspan=3,sticky='w')
        opts['row']+=1
        t=(_("Looking at {}").format(profile))
        proselabel(opts,t,cmd='getprofile',parent=tf)
        opts['columnplus']=1
        t=(_("{} words ({})").format(ps,count))
        proselabel(opts,t,cmd='getps',parent=tf)
        opts['columnplus']=0
        opts['row']+=1
        """Get cvt"""
        tf=Frame(self.frame.status)
        tf.grid(row=opts['row'],column=0,columnspan=3,sticky='w')
        t=(_("Checking {},").format(self.params.cvtdict()[cvt]['pl']))
        proselabel(opts,t,cmd='getcvt',parent=tf)
        """Get check"""
        check=self.params.check()
        if check == 'adhoc':
            tkadhoc()
        else:
            self.status.makecheckok() #this is intentionally broad: *any* check
        check=self.params.check()
        log.info("CVT: {}".format(cvt))
        if cvt == 'T': #self.name has different options by self.type
            opts['columnplus']=1
            if len(self.status.checks()) == 0:
                t=_("no tone frames defined.")
                check=None
            elif self.status.ischeckok():
                # check not in checks:
                t=_("no tone frame selected.")
                check=None
            else:
                t=(_("working on ‘{}’ tone frame").format(check))
            proselabel(opts,t,cmd='getcheck',parent=tf)
        """Get subcheck"""
        self.status.build() #makestatusdict()
        self.status.makegroupok()
        group=self.status.group()
        if cvt == 'T':
            opts['columnplus']=2
            if None in [check, group]:
                t=_("(no framed group)")
            else:
                t=(_("(framed group: ‘{}’)").format(group))
            proselabel(opts,t,cmd='getgroup',parent=tf)
            opts['columnplus']=0
        else:
            opts['columnplus']=1
            t=(_("working on {}".format(group))) #check[1]
            proselabel(opts,t,cmd='getcheck',parent=tf)
        """Final Button"""
        opts['row']+=1
        if cvt == 'T':
            t=(_("Sort!"))
        else:
            t=(_("Report!")) #because CV doesn't actually sort yet...
        button(opts,t,self.runcheck,column=0,
                font=self.fonts['title'],
                compound='bottom', #image bottom, left, right, or top of text
                image=self.photo[cvt]
                )
        opts['row']+=1
        if cvt == 'T':
            t=(_("Record Sorted Examples"))
        else:
            t=(_("Record Dictionary Words"))
        button(opts,t,self.record,column=0,
                compound='left', #image bottom, left, right, or top of text
                row=1,
                image=self.photo['record']
                )
        self.maybeboard()
        self.checkcheck(dictnow)
    def donewpyaudio(self):
        try:
            self.pyaudio.terminate()
        except:
            log.info("Apparently self.pyaudio doesn't exist, or isn't initialized.")
    def soundcheckrefreshdone(self):
        self.storesettingsfile(setting='soundsettings')
        self.soundsettingswindow.destroy()
    def soundcheckrefresh(self):
        self.soundsettingswindow.resetframe()
        row=0
        Label(self.soundsettingswindow.frame,
                text="Current Sound Card Settings:").grid(row=row,column=0)
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
            Label(self.soundsettingswindow.frame,text=l).grid(row=row,column=0)
            bc=Button(self.soundsettingswindow.frame, choice=text, #choice unused.
                            text=text, anchor='c',
                            cmd=cmd)
            bc.grid(row=row,column=1)
            row+=1
        br=RecordButtonFrame(self.soundsettingswindow.frame,self,test=True)
        br.grid(row=row,column=0)
        row+=1
        l=_("You may need to change your microphone "
            "\nand/or speaker sound card to get the "
            "\nsampling and format you want.")
        Label(self.soundsettingswindow.frame,
                text=l).grid(row=row,column=0)
        row+=1
        l=_("Make sure ‘record’ and ‘play’ \nwork well here, "
            "\nbefore recording real data!"
            "\n See also note in documentation about verifying these recordings"
            "in an external application, such as Praat.")
        Label(self.soundsettingswindow.frame,
                text=l,font=self.fonts['read']).grid(row=row,column=0)
        row+=1
        bd=Button(self.soundsettingswindow.frame,text=_("Done"),anchor='c',
                                            cmd=self.soundcheckrefreshdone)
        bd.grid(row=row,column=0)
    def pyaudiocheck(self):
        try:
            self.pyaudio.pa.get_format_from_width(1) #just check if its OK
        except:
            self.pyaudio=sound.AudioInterface()
    def soundsettingscheck(self):
        if not hasattr(self,'soundsettings'):
            self.loadsoundsettings()
    def soundcheck(self):
        #Set the parameters of what could be
        self.pyaudiocheck()
        self.soundsettingscheck()
        self.soundsettingswindow=Window(self.frame,
                                title=_('Select Sound Card Settings'))
        self.soundcheckrefresh()
        self.soundsettingswindow.wait_window(self.soundsettingswindow)
        self.donewpyaudio()
        if not self.exitFlag.istrue() and self.soundsettingswindow.winfo_exists():
            self.soundsettingswindow.destroy()
    def maybeboard(self):
        def checkfordone(): #has *anything* been sorted?
            if self.status.groups() >0:
                return True
        profileori=self.slices.profile()
        if hasattr(self,'leaderboard') and type(self.leaderboard) is Frame:
            self.leaderboard.destroy()
        self.leaderboard=Frame(self.frame)
        self.leaderboard.grid(row=0,column=1,sticky="") #nesw
        #Given the line above, much of the below can go, but not all?
        cvt=self.params.cvt()
        ps=self.slices.ps()
        self.status.cull() #remove nodes with no data
        if cvt in self.status:
            if ps in self.status[cvt]:
                if (hasattr(self,'noboard') and (self.noboard is not None)):
                    self.noboard.destroy()
                if cvt == 'T':
                    if ps in self.toneframes:
                        self.maketoneprogresstable()
                        return
                else:
                    log.info("Found CV verifications")
                    self.makeCVprogresstable()
                    return
        self.makenoboard()
    def boardtitle(self):
        titleframe=Frame(self.leaderboard)
        titleframe.grid(row=0,column=0,sticky='n')
        cvt=self.params.cvt()
        cvtdict=self.params.cvtdict()
        if self.mainrelief == None:
            lt=Label(titleframe, text=_(cvtdict[cvt]['sg']),
                                                    font=self.fonts['title'])
        else:
            lt=Button(titleframe, text=_(cvtdict[cvt]['sg']),
                                font=self.fonts['title'],relief=self.mainrelief)
        lt.grid(row=0,column=0,sticky='nwe')
        Label(titleframe, text=_('Progress for'), font=self.fonts['title']
            ).grid(row=0,column=1,sticky='nwe',padx=10)
        ps=self.slices.ps()
        if self.mainrelief == None:
            lps=Label(titleframe,text=ps,anchor='c',font=self.fonts['title'])
        else:
            lps=Button(titleframe,text=ps, anchor='c',
                            relief=self.mainrelief, font=self.fonts['title'])
        lps.grid(row=0,column=2,ipadx=0,ipady=0)
        ttt=ToolTip(lt,_("Change Check Type"))
        ttps=ToolTip(lps,_("Change Part of Speech"))
        lt.bind('<ButtonRelease>',self.getcvt)
        lps.bind('<ButtonRelease>',self.getps)
    def makenoboard(self):
        log.info("No Progress board")
        self.boardtitle()
        self.noboard=Label(self.leaderboard, image=self.photo['transparent'],
                    text='', pady=50, bg='red').grid(row=1,column=0,sticky='we')
        self.frame.update()
        self.frame.parent.waitdone()
        self.frame.parent.parent.deiconify()
    def makeCVprogresstable(self):
        self.boardtitle()
        self.leaderboardtable=Frame(self.leaderboard)
        self.leaderboardtable.grid(row=1,column=0)
        notext=_("Nothing to see here...")
        Label(self.leaderboardtable,text=notext).grid(row=1,column=0)
        self.frame.update()
        self.frame.parent.waitdone()
        self.frame.parent.parent.deiconify()
    def maketoneprogresstable(self):
        def groupfn(x):
            for i in x:
                try:
                    int(i)
                    log.log(3,"Integer {} fine".format(i))
                except:
                    log.log(3,"Problem with integer {}".format(i))
                    if not self.hidegroupnames:
                        return nn(x,oneperline=True) #if any is not an integer, all.
            return len(x) #to show counts only
        def updateprofilencheck(profile,check):
            self.slices.profile(profile)
            self.params.check(check)
            #run this in any case, rather than running it not at all, or twice
        def refresh(event=None):
            self.storesettingsfile()
            self.tableiteration+=1
        self.boardtitle()
        # leaderheader=Frame(self.leaderboard) #someday, make this not scroll...
        # leaderheader.grid(row=1,column=0)
        leaderscroll=ScrollingFrame(self.leaderboard)
        leaderscroll.grid(row=1,column=0)
        self.leaderboardtable=leaderscroll.content
        row=0
        #put in a footer for next profile/frame
        cvt=self.params.cvt()
        ps=self.slices.ps()
        profiles=self.slices.profiles()
        curprofile=self.slices.profile()
        curcheck=self.params.check()
        profiles=['colheader']+profiles+['next']
        frames=list(self.toneframes[ps].keys())
        ungroups=0
        tv=_("verified")
        tu=_("unsorted data")
        t="+ = {} \n! = {}".format(tv,tu)
        h=Label(self.leaderboardtable,text=t,font="small")
        h.grid(row=row,column=0,sticky='e')
        h.bind('<ButtonRelease>', refresh)
        htip=_("Refresh table, \nsave settings")
        th=ToolTip(h,htip)
        r=self.status[cvt][ps]
        log.debug("Table rows possible: {}".format(r))
        for profile in profiles:
            column=0
            if profile in ['colheader','next']+list(self.status[cvt][
                                                            ps].keys()):
                if profile in self.status[cvt][ps]:
                    if self.status[cvt][ps][profile] == {}:
                        continue
                    #Make row header
                    t="{} ({})".format(profile,len(self.profilesbysense[
                                                            ps][profile]))
                    h=Label(self.leaderboardtable,text=t)
                    h.grid(row=row,column=column,sticky='e')
                    if profile == curprofile and curcheck is None:
                        h.config(background=h.theme['activebackground']) #highlight
                        tip=_("Current profile \n(no frame set)")
                        ttb=ToolTip(h,tip)
                elif profile == 'next': # end of row headers
                    brh=Button(self.leaderboardtable,text=profile,
                                            relief='flat',cmd=self.status.nextprofile)
                    brh.grid(row=row,column=column,sticky='e')
                    brht=ToolTip(brh,_("Go to the next syllable profile"))
                for frame in frames+['next']:
                    column+=1
                    if profile == 'colheader':
                        if frame == 'next': # end of column headers
                            bch=Button(self.leaderboardtable,text=frame,
                                        relief='flat',cmd=self.status.nextcheck,
                                        font=self.fonts['reportheader'])
                            bch.grid(row=row,column=column,sticky='s')
                            bcht=ToolTip(bch,_("Go to the next tone frame"))
                        else:
                            Label(self.leaderboardtable,text=linebreakwords(
                                frame), font=self.fonts['reportheader']
                                ).grid(row=row,column=column,sticky='s',ipadx=5)
                    elif profile == 'next':
                        continue
                    elif frame in self.status[cvt][ps][profile]:
                        node=self.status[cvt][ps][profile][frame]
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
                        if self.hidegroupnames or (type(totalnum) is int and
                                                        type(donenum) is int):
                            donenum="+{}/{}".format(donenum,totalnum)
                        else:
                            donenum=nn(totalwverified,oneperline=True)
                        # This should only be needed on a new database
                        if tosort == True and donenum != '':
                            donenum='!'+str(donenum) #mark data to sort
                        tb=Button(self.leaderboardtable,
                                relief='flat',
                                bd=0, #border
                                text=donenum,
                                cmd=lambda p=profile,
                                f=frame:updateprofilencheck(profile=p, check=f),
                                anchor='c',
                                padx=0,pady=0
                                )
                        if profile == curprofile and frame == curcheck:
                            tb.configure(background=tb['activebackground'])
                            tb.configure(command=donothing)
                            tip=_("Current settings \nprofile: ‘{}’; \nframe: ‘{}’"
                                "".format(profile,frame))
                        else:
                            tip=_("Change to \nprofile: ‘{}’; \nframe: ‘{}’"
                                "".format(profile,frame))
                        tb.grid(row=row,column=column,ipadx=0,ipady=0,
                                                                sticky='nesw')
                        ttb=ToolTip(tb,tip)
            row+=1
        if ungroups > 0:
            log.error(_("You have more groups verified than there are, in {} "
                        "cells".format(ungroups)))
        self.frame.update()
    def setsu(self):
        self.su=True
    def unsetsu(self):
        self.su=False
    def makestatusframe(self):
        #This will probably need to be reworked
        if hasattr(self.frame,'status') and self.frame.status.winfo_exists():
            self.frame.status.destroy()
            self.frame.status=Frame(self.frame)
            self.frame.status.grid(row=0, column=0,sticky='nw')
        else:
            log.info("Apparently, this is my first time making the status frame.")
            self.frame.status=Frame(self.frame)
            self.frame.status.grid(row=0, column=0,sticky='nw')
    def makeresultsframe(self):
        if hasattr(self,'runwindow') and self.runwindow.winfo_exists:
            self.results = Frame(self.runwindow.frame,width=800)
            self.results.grid(row=0, column=0)
        else:
            log.error("Tried to get a results frame without a runwindow!")
    def setnamesall(self):
        self.checknamesall={
        "V":{
            1:[("V1", "First/only Vowel")],
            2:[
                ("V1=V2", "Same First/only Two Vowels"),
                ("V1xV2", "Correspondence of First/only Two Vowels"),
                ("V2", "Second Vowel")
                ],
            3:[
                ("V1=V2=V3", "Same First/only Three Vowels"),
                ("V3", "Third Vowel"),
                ("V2=V3", "Same Second Two Vowels"),
                ("V2xV3", "Correspondence of Second Two Vowels")
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
            1:[("C1", "First/only Consonant")],
            2:[
                ("C2", "Second Consonant"),
                ("C1=C2","Same First/only Two Consonants")
                ],
            3:[
                ("C2=C3","Same Second Two Consonants"),
                ("C3", "Third Consonant"),
                ("C1=C2=C3","Same First Three Consonants")
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
            1:[("#CV1", "Word-initial CV"),
                ("C1xV1", "Correspondence of C1 and V1"),
                ("CV1", "First/only CV")
                ],
            2:[("CV2", "Second CV"),
                ("C2xV2", "Correspondence of C2 and V2"),
                ("CV1=CV2","Same First/only Two CVs"),
                ("CV2#", "Word-final CV")
                ],
            3:[
                ("CV1=CV2=CV3","Same First/only Three CVs"),
                ("CV3", "Third CV")
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
        "T":{ #this is not obsolete; it is needed to allow T as self.type
            1:[
                ("T1", "Sort Words by tone melody"),
                ("T2", "Verify tone group")
            ]
        }
    }
    def getanalangname(self,event=None):
        log.info("this sets the language name")
        def submit(event=None):
            self.languagenames[self.analang]=name.get()
            if not hasattr(self,'adnlangnames') or self.adnlangnames is None:
                self.adnlangnames={}
            self.adnlangnames[self.analang]=self.languagenames[self.analang]
                # if self.analang in self.adnlangnames:
            self.storesettingsfile()
            window.destroy()
        window=Window(self.frame,title=_('Enter Analysis Language Name'))
        curname=self.languagenames[self.analang]
        defaultname=_("Language with code [{}]").format(self.analang)
        t=_("How do you want to display the name of {}").format(
                                                                        curname)
        if curname != defaultname:
            t+=_(", with ISO 639-3 code [{}]").format(self.analang)
        t+='?' # _("Language with code [{}]").format(xyz)
        Label(window.frame,text=t).grid(row=0,column=0,sticky='e',columnspan=2)
        name = EntryField(window.frame)
        name.grid(row=1,column=0,sticky='e')
        Button(window.frame,text='OK',cmd=submit).grid(
                                                    row=1,column=1,sticky='w')
        name.bind('<Return>',submit)
    def getanalang(self,event=None):
        if len(self.db.analangs) <2: #The user probably wants to change display.
            self.getanalangname()
            return
        log.info("this sets the language")
        # fn=inspect.currentframe().f_code.co_name
        window=Window(self.frame,title=_('Select Analysis Language'))
        if self.db.analangs is None :
            Label(window.frame,
                          text='Error: please set Lift file first! ('
                          +str(self.db.filename)+')'
                          ).grid(column=0, row=0)
        else:
            Label(window.frame,
                          text=_('What language do you want to analyze?')
                          ).grid(column=0, row=1)
            langs=list()
            for lang in self.db.analangs:
                langs.append({'code':lang, 'name':self.languagenames[lang]})
                print(lang, self.languagenames[lang])
            buttonFrame1=ButtonFrame(window.frame,
                                     langs,self.setanalang,
                                     window
                                     ).grid(column=0, row=4)
    def getglosslang(self,event=None):
        log.info("this sets the gloss")
        window=Window(self.frame,title=_('Select Gloss Language'))
        Label(window.frame,
                  text=_('What Language do you want to use for glosses?')
                  ).grid(column=0, row=1)
        langs=list()
        for lang in self.db.glosslangs:
            langs.append({'code':lang, 'name':self.languagenames[lang]})
        buttonFrame1=ButtonFrame(window.frame,
                                 langs,self.setglosslang,
                                 window
                                 ).grid(column=0, row=4)
    def getglosslang2(self,event=None):
        log.info("this sets the gloss")
        window=Window(self.frame,title='Select Gloss Language')
        text=_('What other language do you want to use for glosses?')
        Label(window.frame,text=text).grid(column=0, row=1)
        langs=list()
        for lang in self.db.glosslangs:
            if lang == self.glosslangs[0]:
                continue
            langs.append({'code':lang, 'name':self.languagenames[lang]})
        langs.append({'code':None, 'name':'just use '
                        +self.languagenames[self.glosslangs[0]]})
        buttonFrame1=ButtonFrame(window.frame,langs,self.setglosslang2,
                                 window
                                 ).grid(column=0, row=4)
    def getcheckspossible(self):
        """This splits by tone or not, because the checks available for
        segments depend on the number of segments in the selected syllable
        profile, but for tone, they don't; tone frames depend only on ps."""
        self.status.renewchecks()
        self.status.checks()
    def getcheck(self,guess=False,tosort=False,wsorted=False,event=None):
        log.info("this sets the check")
        # fn=inspect.currentframe().f_code.co_name
        log.info("Getting the check name...")
        checks=self.status.checks(tosort=tosort,wsorted=wsorted)
        window=Window(self.frame,title='Select Check')
        if checks == []:
            if self.params.cvt() == 'T':
                btext=_("Define a New Tone Frame")
                text=_("You don't seem to have any tone frames set up.\n"
                "Click '{}' below to define a tone frame. \nPlease "
                "pay attention to the instructions, and if \nthere's anything "
                "you don't understand, or if you're not \nsure what a tone "
                "frame is, please ask for help. \nWhen you are done making "
                "frames, click 'Exit' to continue.".format(btext))
                cmd=self.addframe
            else:
                btext=_("Return to A→Z+T, to fix settings")
                text=_("I can't find any checks for type {}, ps {}, profile {}."
                        " Probably that means there is a problem with your "
                        " settings, or with your syllable profile analysis"
                        "".format(cvt,ps,profile))
                cmd=window.destroy
            Label(window.frame, text=text).grid(column=0, row=0, ipady=25)
            b=Button(window.frame, text=btext,
                    cmd=cmd,
                    anchor='c')
            b.grid(column=0, row=1,sticky='')
            """I need to make this quit the whole program, immediately."""
            b2=Button(window.frame, text=_("Quit A→Z+T"),
                    cmd=self.parent.parent.destroy,
                    anchor='c')
            b2.grid(column=1, row=1,sticky='')
            b.wait_window(window)
        elif guess is True:
            self.status.makecheckok(tosort=tosort,wsorted=wsorted)
        else:
            text=_('What check do you want to do?')
            Label(window.frame, text=text).grid(column=0, row=0)
            buttonFrame1=ScrollingButtonFrame(window.frame,
                                    checks,
                                    self.setcheck,
                                    window
                                    )
            buttonFrame1.grid(column=0, row=4)
            buttonFrame1.wait_window(window)
        """Make sure we got a value"""
        if not self.status.ischeckok():
            return 1
    def getexamplespergrouptorecord(self):
        log.info("this sets the number of examples per group to record")
        self.npossible=[
            {'code':1,'name':"1 - Bare minimum, just one per group"},
            {'code':5,'name':"5 - Some, but not all, of most groups"},
            {'code':100,'name':"100 - All examples in most databases"},
            {'code':1000,'name':"1000 - All examples in VERY large databases"}
                        ]
        title=_('Select Number of Examples per Group to Record')
        window=Window(self.frame, title=title)
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
                "".format(self.program['name'])
                )
        Label(window.frame, text=title, font=self.fonts['title']).grid(column=0,
                                                                        row=0)
        Label(window.frame, text=text, justify='left').grid(column=0, row=1)
        buttonFrame1=ButtonFrame(window.frame,
                                self.npossible,
                                self.setexamplespergrouptorecord,
                                window
                                )
        buttonFrame1.grid(column=0, row=4)
        buttonFrame1.wait_window(window)
    def getframedtonegroup(self,window,event=None,guess=False,comparison=False):
        """Window is called in getsubcheck"""
        cvt=params.cvt()
        ps=slices.ps()
        profile=slices.profile()
        check=params.check()
        if (None in [cvt, ps, profile, check]
                or cvt != 'T'):
            Label(window.frame,
                          text="You need to set "
                          "\nCheck type (as Tone, currently {}) "
                          "\nGrammatical category (currently {})"
                          "\nSyllable Profile (currently {}), and "
                          "\nTone Frame (currently {})"
                          "\nBefore this function will do anything!"
                          "".format(self.params.typedict()[cvt]['sg'], ps,
                          profile, check)).grid(column=0, row=0)
            return 1
        else:
            g=self.status.groups()
            if len(g) == 0:
                Label(window.frame,
                          text="It looks like you haven't sorted {}-{} lexemes "
                          "into any groups in the ‘{}’ frame yet."
                          "".format(ps,profile,check)
                          ).grid(column=0, row=0)
            elif guess == True:
                self.setsubcheck(g[0],window) #don't ask, just set
            else:
                Label(window.frame,
                          text="What {}-{} tone group in the ‘{}’ frame do "
                          "you want to work with?".format(ps,profile,
                          check)).grid(column=0, row=0)
                window.scroll=Frame(window.frame)
                window.scroll.grid(column=0, row=1)
                if comparison is False:
                    buttonFrame1=ScrollingButtonFrame(window.scroll,g,
                                                self.setsubcheck,
                                                window=window
                                                ).grid(column=0, row=4)
                else:
                    buttonFrame1=ScrollingButtonFrame(window.scroll,g,
                                                self.setsubcheck_comparison,
                                                window=window
                                                ).grid(column=0, row=4)
    def getV(self,window,event=None):
        # fn=inspect.currentframe().f_code.co_name
        """Window is called in getsubcheck"""
        if ps is None:
            Label(window.frame,
                          text='Error: please set Grammatical category first! ('
                          +str(ps)+')'
                          ).grid(column=0, row=0)
        else:
            # Label(window.frame,
            #               ).grid(column=0, row=0)
            Label(window.frame,
                          text='What Vowel do you want to work with?'
                          ).grid(column=0, row=0)
            window.scroll=Frame(window.frame)
            window.scroll.grid(column=0, row=1)
            buttonFrame1=ScrollingButtonFrame(window.scroll,
                                     #self.db.v[self.analang],
                                     self.scount[ps][cvt],
                                     self.setsubcheck,
                                     window=window
                                     ).grid(column=0, row=4)
    def getC(self,window,event=None):
        # fn=inspect.currentframe().f_code.co_name
        """Window is called in getsubcheck"""
        if ps is None:
            text=_('Error: please set Grammatical category first! ')+'('
            +str(ps)+')'
            Label(window.frame,
                          text=text
                          ).grid(column=0, row=0)
        else:
            # Label(window.frame,
            #               ).grid(column=0, row=0)
            Label(window.frame,
                          text='What consonant do you want to work with?'
                          ).grid(column=0, row=0,sticky='nw')
            window.scroll=Frame(window.frame)
            window.scroll.grid(column=0, row=1)
            buttonFrame1=ScrollingButtonFrame(window.scroll,
                                    # self.db.c[self.analang],
                                    self.scount[ps][cvt],
                                    self.setsubcheck,
                                    window=window
                                    )
            buttonFrame1.grid(column=0, row=0)
    def getlocations(self):
        """This builds from LIFT"""
        self.locations=[]
        for senseid in self.slices.senseids():
            for location in [i for i in self.db.get('locationfield',
                senseid=senseid, showurl=True).get('text') if i is not None]:
                self.locations+=[location]
        self.locations=list(dict.fromkeys(self.locations))
    def wordsbypsprofilechecksubcheckp(self,parent='NoXLPparent',t="NoText!"):
        xlp.Paragraph(parent,t)
        print(t)
        log.debug(t)
        self.buildregex()
        log.log(2,"self.regex: {}; self.regexCV: {}".format(self.regex,
                                                        self.regexCV))
        matches=set(self.senseidformsbyregex(self.regex))
        for typenum in self.typenumsRun:
            # this removes senses already reported (e.g., in V1=V2)
            matches-=self.basicreported[typenum]
        log.log(2,"{} matches found!: {}".format(len(matches),matches))
        group=self.status.group()
        if 'x' in check:
            n=self.checkcounts[ps][profile][check][
                            group][self.subcheckcomparison]=len(matches)
        else:
            n=self.checkcounts[ps][profile][check][
                            group]=len(matches)
            if '=' in check:
                xname=re.sub('=','x',check, count=1)
                log.debug("looking for name {} in {}".format(xname,
                                                    self.checkcodesbyprofile))
                if xname in self.checkcodesbyprofile:
                    log.debug("Adding {} value to name {}".format(len(matches),
                                                                        xname))
                    #put the results in that group, too
                    log.debug(self.checkcounts)
                    if xname not in self.checkcounts[ps][profile]:
                        self.checkcounts[ps][profile][xname]={}
                    if group not in self.checkcounts[ps][
                                    profile][xname]:
                        self.checkcounts[ps][profile][xname][group]={}
                    self.checkcounts[ps][profile][xname][group][group
                                                                ]=len(matches)
                    log.debug(self.checkcounts)
        if n>0:
            titlebits='x'+ps+profile+check+group
            if 'x' in check:
                titlebits+='x'+self.subcheckcomparison
            id=rx.id(titlebits)
            ex=xlp.Example(parent,id)
            for senseid in matches:
                for typenum in self.typenumsRun:
                    self.basicreported[typenum].add(senseid)
                framed=self.datadict.getframeddata(senseid)
                self.framedtoXLP(framed,parent=ex,listword=True)
    def wordsbypsprofilechecksubcheck(self,parent='NoXLPparent'):
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
        check=self.params.check()
        group=self.status.group()
        if cvt in ['V','C']:
            groups=self.s[self.analang][cvt]
        """This sets each of the checks that are applicable for the given
        profile; self.basicreported is from self.basicreport()"""
        for typenum in self.basicreported:
            log.log(2, '{}: {}'.format(typenum,self.basicreported[typenum]))
        """setnamesbyprofile doesn't depend on ps"""
        self.checkcodesbyprofile=sorted([x[0] for x in self.setnamesbyprofile()],
                                        key=len,reverse=True)
        """check set here"""
        for check in self.checkcodesbyprofile:
            if check not in self.checkcounts[ps][profile]:
                self.checkcounts[ps][profile][check]={}
            self.typenumsRun=[typenum for typenum in self.typenums
                                        if re.search(typenum,check)]
            log.debug('check: {}; self.type: {}; self.typenums: {}; '
                        'self.typenumsRun: {}'.format(check,cvt,
                                                self.typenums,self.typenumsRun))
            if len(check) == 1:
                log.debug("Error! {} Doesn't seem to be list formatted.".format(
                                                                    check))
            if 'x' in check:
                log.debug('Hey, I cound a correspondence number!')
                if cvt in ['V','C']:
                    subcheckcomparisons=groups
                elif cvt == 'CV':
                    subchecks=self.s[self.analang]['C']
                    subcheckcomparisons=self.s[self.analang]['V']
                else:
                    log.error("Sorry, I don't know how to compare cvt: {}"
                                                        "".format(cvt))
                for group in groups:
                    if group not in self.checkcounts[ps][
                                                    profile][check]:
                        self.checkcounts[ps][profile][check][group]={}
                    for self.subcheckcomparison in subcheckcomparisons:
                        if group != self.subcheckcomparison:
                            t=_("{} {} {}={}-{}".format(ps,profile,
                                                check,group,
                                                self.subcheckcomparison))
                            self.wordsbypsprofilechecksubcheckp(parent=parent,
                                                                            t=t)
            else:
                for group in groups:
                    t=_("{} {} {}={}".format(ps,profile,check,
                                                                group))
                    self.wordsbypsprofilechecksubcheckp(parent=parent,t=t)
    def idXLP(self,framed):
        id='x' #string!
        bits=[
            self.params.cvt(),
            self.slices.ps(),
            self.slices.profile(),
            self.params.check(),
            self.status.group()
            ]
        for lang in self.glosslangs:
            if lang in framed.forms and framed.forms[lang] is not None:
                bits+=framed.forms[lang]
        for x in bits:
            if x is not None:
                id+=x
        return rx.id(id) #for either example or listword
    def framedtoXLP(self,framed,parent,listword=False,groups=True):
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
        if self.audiolang in framed.forms:
            url=file.getdiredrelURL(self.reporttoaudiorelURL,
                                                framed.forms[self.audiolang])
            el=xlp.LinkedData(ex,self.analang,framed.forms[self.analang],
                                                                    str(url))
        else:
            el=xlp.LangData(ex,self.analang,framed.forms[self.analang])
        if hasattr(framed,'tonegroup') and groups is True: #joined groups show each
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
    def getexsall(self,value):
        #This returns all the senseids with a given tone value
        check=self.params.check()
        senseids=self.db.get("sense", location=check, path=['tonefield'],
                            tonevalue=value
                            ).get('senseid')
        """The above doesn't test for profile, so we restrict that next"""
        senseidsinslice=self.slices.inslice(senseids)
        return list(senseidsinslice)
    def getex(self,value,notonegroup=True,truncdefn=False,renew=False):
        """This function finds examples in the lexicon for a given tone value,
        in a given tone frame (from check)"""
        senseids=self.getexsall(value)
        output={'n': len(senseids)}
        if (not hasattr(self,'exs')) or (self.exs is None):
            self.exs={} #in case this hasn't been set up by now
        if value in self.exs:
            if self.exs[value] in senseids: #if stored value is in group
                if renew == True:
                    log.info("Using next value for ‘{}’ group: ‘{}’".format(
                                value, self.exs[value]))
                    i=senseids.index(self.exs[value])
                    if i == len(senseids)-1: #loop back on last
                        senseid=senseids[0]
                    else:
                        senseid=senseids[i+1]
                    self.exs[value]=senseid
                else:
                    log.info("Using stored value for ‘{}’ group: ‘{}’".format(
                                value, self.exs[value]))
                    senseid=self.exs[value]
                framed=self.datadict.getframeddata(senseid)
                if framed.glosses() is not None:
                    output['senseid']=senseid
                    output['framed']=framed #this includes [n], above
                    return output
                else:
                    output=self.getex(value=value,notonegroup=notonegroup,
                                truncdefn=truncdefn,renew=True)
                    return output
        for i in range(len(senseids)): #just keep trying until you succeed
            senseid=senseids[randint(0, len(senseids))-1]
            framed=self.datadict.getframeddata(senseid)
            if framed.glosses() is not None:
                """As soon as you find one with form and gloss, quit."""
                self.exs[value]=senseid
                output['senseid']=senseid
                output['framed']=framed #this includes [n], above
                return output
            else:
                log.info("Example sense with empty field problem")
    def renamegroup(self,reverify=False):
        #reverify indicates when it is called from the verification window
        # (i.e.,) before the group is verified. This does two things differently:
        # 1. verifyT is only called when reverify=True
        # 2. self.nextsubcheck() button is only there when reverify=False
        def updatelabels(event=None):
            errorlabel['text'] = ''
            a=newname.get()
            try:
                int(a) #Is this interpretable as an integer (default group)?
                namehash.set('')
            except ValueError:
                x=hash_t.sub('T',newname.get())
                y=hash_sp.sub('#',x)
                z=hash_nbsp.sub('.',y)
                namehash.set(z)
        def updategroups():
            groupsthere=self.status[cvt][ps][profile][
                                                        check]['groups']
            groupsdone=self.status[cvt][ps][profile][check][
                                                                    'done']
            return groupsthere, groupsdone
        def submitform():
            updatelabels()
            newtonevalue=formfield.get()
            groupsthere, groupsdone = updategroups()
            if newtonevalue == "":
                noname=_("Give a name for this tone melody!")
                log.debug(noname)
                errorlabel['text'] = noname
                return 1
            if newtonevalue != group: #only make changes!
                if newtonevalue in groupsthere :
                    deja=_("Sorry, there is already a group with "
                                    "that label; If you want to join the "
                                    "groups, give it a different name now, "
                                    "and join it later".format(newtonevalue))
                    log.debug(deja)
                    errorlabel['text'] = deja
                    return 1
                self.updatebysubchecksenseid(group,newtonevalue)
                i=groupsthere.index(group) #put new value in the same place.
                groupsthere.remove(group)
                groupsthere.insert(i,newtonevalue)
                if group in groupsdone: #if verified, change the name there, too
                    i=groupsdone.index(group) #put new value in the same place.
                    groupsdone.remove(group)
                    groupsdone.insert(i,newtonevalue)
                group=newtonevalue
                self.getsubchecksprioritized() #We've changed this, so update
                self.storesettingsfile(setting='status')
            else: #move on, but notify in logs
                log.info("User selected ‘{}’, but with no change.".format(ok))
            if hasattr(self,'subcheck_comparison'):
                delattr(self,'subcheck_comparison') # in either case
            self.runwindow.destroy()
            if reverify == True: #don't do this if running from menus
                self.verifyT(menu=menu)
            return
        def addchar(x):
            if x == '':
                formfield.delete(0,tkinter.END)
            else:
                formfield.insert(tkinter.INSERT,x) #could also do tkinter.END
            updatelabels()
        def done():
            submitform()
            self.donewpyaudio()
        def next():
            log.debug("running next group")
            error=submitform()
            if not error:
                log.debug("group: {}".format(group))
                self.nextgroup()
                log.debug("group: {}".format(group))
                self.renamegroup(reverify=reverify)
        def nextcheck():
            log.debug("running next frame")
            error=submitform()
            if not error:
                log.debug("check: {}".format(check))
                self.status.nextcheck(wsorted=True)
                log.debug("check: {}".format(check))
                self.renamegroup(reverify=reverify)
        def nextprofile():
            log.debug("running next frame")
            error=submitform()
            if not error:
                log.debug("profile: {}".format(profile))
                self.status.nextprofile(wsorted=True)
                log.debug("profile: {}".format(profile))
                self.renamegroup(reverify=reverify)
        def setsubcheck_comparison():
            w=self.getsubcheck(comparison=True) #this returns its window
            w.wait_window(w)
            comparisonbuttons()
        def comparisonbuttons():
            try: #successive runs
                compframe.compframeb.destroy()
                log.info("Comparison frameb destroyed!")
            except: #first run
                log.info("Problem destroying comparison frame, making...")
            compframe.compframeb=Frame(compframe)
            compframe.compframeb.grid(row=1,column=0)
            t=_('Compare with another group')
            if (hasattr(self, 'subcheck_comparison')
                    and self.subcheck_comparison in groupsthere and
                    self.subcheck_comparison != group):
                log.info("Making comparison buttons for group {} now".format(
                                                    self.subcheck_comparison))
                t=_('Compare with another group ({})').format(
                                                    self.subcheck_comparison)
                compframe.bf2=self.tonegroupbuttonframe(compframe.compframeb,
                    self.subcheck_comparison,sticky='w',row=0,column=0,
                    playable=True,unsortable=False,alwaysrefreshable=True,
                    font=self.fonts['default'])
            elif not hasattr(self, 'subcheck_comparison'):
                log.info("No comparison found !")
            elif self.subcheck_comparison not in groupsthere:
                log.info("Comparison ({}) not in group list ({})"
                            "".format(self.subcheck_comparison,groupsthere))
            elif self.subcheck_comparison == group:
                log.info("Comparison ({}) same as subgroup ({}); not showing."
                            "".format(self.subcheck_comparison,group))
            else:
                log.info("This should never happen (renamegroup/"
                            "comparisonbuttons)")
            sub_c['text']=t
        cvt=self.params.cvt()
        ps=self.slices.ps()
        profile=self.slices.profile()

        check=self.params.check()
        if check == None:
            self.getcheck(guess=True)
            if check == None:
                log.info("I asked for a check name, but didn't get one.")
                return
        groupsthere, groupsdone = updategroups()
        group=self.status.group()
        if group is None or group not in groupsthere:
            self.getsubcheck(guess=True)
            if group == None:
                log.info("I asked for a framed tone group, but didn't get one.")
                return
        notthisgroup=groupsthere[:]
        if group in groupsthere:
            notthisgroup.remove(group)
        else:
            log.error(_("current group ({}) doesn't seem to be in list of "
                "groups: ({})\n\tThis may be because we're looking for data that "
                "isn't there, or maybe a setting is off.".format(group,
                                                                groupsthere)))
        newname=tkinter.StringVar(value=group)
        namehash=tkinter.StringVar()
        hash_t,hash_sp,hash_nbsp=rx.tonerxs()
        padx=50
        pady=10
        title=_("Rename {} {} tone group ‘{}’ in ‘{}’ frame"
                        ).format(ps,profile,group,check)
        self.getrunwindow(title=title)
        menu=self.runwindow.removeverifymenu()
        titlel=Label(self.runwindow.frame,text=title,font=self.fonts['title'])
        titlel.grid(row=0,column=0,sticky='ew',padx=padx,pady=pady)
        getformtext=_("What new name do you want to call this surface tone "
                        "group? A label that describes the surface tone form "
                        "in this context would be best, like ‘[˥˥˥ ˨˨˨]’")
        getform=Label(self.runwindow.frame,text=getformtext,
                font=self.fonts['read'],norender=True)
        getform.grid(row=1,column=0,sticky='ew',padx=padx,pady=pady)
        inputframe=Frame(self.runwindow.frame)
        inputframe.grid(row=2,column=0,sticky='')
        buttonframe=Frame(inputframe)
        buttonframe.grid(row=0,column=0,sticky='new')
        tonechars=['[', '˥', '˦', '˧', '˨', '˩', ']']
        spaces=[' ',' ','']
        for char in tonechars+spaces:
            if char == ' ':
                text=_('syllable break')
                column=0
                columnspan=int(len(tonechars)/2)+1
                row=1
            elif char == ' ':
                text=_('word break')
                columnspan=int(len(tonechars)/2)
                column=columnspan+1
                row=1
            elif char == '':
                text=_('clear entry')
                column=0
                columnspan=len(tonechars)
                row=2
            else:
                column=tonechars.index(char)
                text=char
                columnspan=1
                row=0
            Button(buttonframe,text = text,command = lambda x=char:addchar(x),
                    anchor ='c').grid(row=row,column=column,sticky='nsew',
                                    columnspan=columnspan)
        g=nn(notthisgroup,twoperline=True)
        log.info("There: {}, NTG: {}; g:{}".format(groupsthere,notthisgroup,g))
        groupslabel=Label(inputframe,text='Other Groups:\n{}'.format(g))
        groupslabel.grid(row=0,column=1,sticky='new',padx=padx,rowspan=2)
        fieldframe=Frame(inputframe)
        fieldframe.grid(row=1,column=0,sticky='new')
        formfield = EntryField(fieldframe,textvariable=newname)
        formfield.grid(row=1,column=0,sticky='new')
        formfield.bind('<KeyRelease>', updatelabels) #apply function after key
        errorlabel=Label(fieldframe,text='',fg='red',
                            wraplength=int(self.frame.winfo_screenwidth()/3))
        errorlabel.grid(row=1,column=1,sticky='nsew')
        formhashlabel=Label(fieldframe,textvariable=namehash, anchor ='c')
        formhashlabel.grid(row=2,column=0,sticky='new')
        fieldframe.grid_columnconfigure(0, weight=1)
        updatelabels()
        responseframe=Frame(self.runwindow.frame)
        responseframe.grid(row=3,column=0,sticky='',padx=padx,pady=pady)
        ok=_('Use this name and go to:')
        sub_lbl=Label(responseframe,text = ok, font=self.fonts['read'],)
        sub_lbl.grid(row=0,column=0,sticky='ns')
        t=_('main screen')
        sub_btn=Button(responseframe,text = t, command = done, anchor ='c')
        sub_btn.grid(row=0,column=1,sticky='ns')
        if reverify == False: #don't give this option if verifying
            t=_('next group')
            sub_btn=Button(responseframe,text = t,command = next,anchor ='c')
            sub_btn.grid(row=0,column=2,sticky='ns')
            t=_('next tone frame')
            sub_f=Button(responseframe,text = t,command = nextcheck)
            sub_f.grid(row=0,column=3,sticky='ns')
            t=_('next syllable profile')
            sub_p=Button(responseframe,text = t,command = nextprofile)
            sub_p.grid(row=0,column=4,sticky='ns')
        examplesframe=Frame(self.runwindow.frame)
        examplesframe.grid(row=4,column=0,sticky='')
        self.tonegroupbuttonframe(examplesframe,group,sticky='w',
            row=0,column=0,playable=True,alwaysrefreshable=True,unsortable=True)
        compframe=Frame(examplesframe,highlightthickness=10,
                    highlightbackground=self.theme['white']) #no hlfg here
        compframe.grid(row=0,column=1,sticky='e')
        t=_('Compare with another group')
        sub_c=Button(compframe,text = t,command = setsubcheck_comparison)
        sub_c.grid(row=0,column=0)
        comparisonbuttons()
        self.runwindow.waitdone()
        sub_btn.wait_window(self.runwindow) #then move to next step
        """Store these variables above, finish with (destroying window with
        local variables):"""
    def maybesort(self):
        """This should look for one group to verify at a time, with sorting
        in between, then join and repeat"""
        def notdonewarning(): #Use this!!
            self.getrunwindow(nowait=True)
            buttontxt=_("Sort!")
            text=_("Hey, you're not done with {} {} words in the {} frame!"
                    "\nCome back when you have time; restart where you left "
                    "off by pressing ‘{}’".format(ps,profile,check,buttontxt))
            Label(self.runwindow.frame, text=text).grid(row=0,column=0)
        def tosortupdate():
            log.info("maybesort tosortbool:{}; tosort:{}; sorted:{}".format(
                                self.status.tosort(),
                                self.status.senseidstosort(),
                                self.status.senseidssorted()
                                ))
        cvt=self.params.cvt()
        check=self.params.check()
        ps=self.slices.ps()
        profile=self.slices.profile()
        log.info("cvt:{}; ps:{}; profile:{}; check:{}".format(cvt,ps,profile,check))
        self.settonevariables()
        tosortupdate()
        log.info("Maybe SortT (from maybesort)")
        if self.status.checktosort(check):
            log.info("SortT (from maybesort)")
            quit=self.sortT()
            if quit == True:
                if not self.exitFlag.istrue():
                    notdonewarning()
                return
        tosortupdate()
        log.info("Going to verify the first of these groups now: {}".format(
                                            self.status.groupstoverify(check)))
        log.info("Maybe verifyT (from maybesort)")
        groupstoverify=self.status.groupstoverify(check)
        if groupstoverify:
            self.status.group(groupstoverify[0]) #just pick the first now
            log.info("verifyT (from maybesort)")
            exitv=self.verifyT()
            """This menu should be gone altogether, from this window"""
            self.runwindow.removeverifymenu() #remove verification windows here, if made
            if exitv == True: #fix this!
                if not self.exitFlag.istrue():
                    notdonewarning()
                return
            self.maybesort()
            return
        # Offer to join in any case:
        log.info("joinT (from maybesort)")
        exit=self.joinT()
        log.debug("exit: {}".format(exit))
        if exit == True:
            if not self.exitFlag:
                self.notdonewarning()
            #This happens when the user exits the window
            log.debug("exiting joinT True")
            #Give an error window here
            return
        elif exit == False:
            def nframe():
                r=self.status.nextcheck(tosort=True)
                if not r:
                    self.status.nextcheck(toverify=True)
                self.runwindow.destroy()
                self.runcheck()
            def aframe():
                self.runwindow.destroy()
                self.addframe()
                self.addwindow.wait_window(self.addwindow)
                self.runcheck()
            def nprofile():
                r=self.status.nextprofile(tosort=True)
                if not r:
                    self.status.nextprofile(toverify=True)
                self.runwindow.destroy()
                self.runcheck()
            def nps():
                self.nextps()
                r=self.status.nextprofile(tosort=True)
                if not r:
                    self.status.nextprofile(toverify=True)
                self.runwindow.destroy()
                self.runcheck()
            self.getrunwindow()
            done=_("All ‘{}’ tone groups in the ‘{}’ frame are verified and "
                    "distinct!".format(profile,check))
            row=0
            if self.exitFlag.istrue():
                return
            Label(self.runwindow.frame, text=done).grid(row=row,column=0,
                                                        columnspan=2)
            row+=1
            Label(self.runwindow.frame, text='',
                        image=self.photo[cvt]
                        ).grid(row=row,column=0,columnspan=2)
            row+=1
            ctosort=self.status.checks(tosort=True)
            ctoverify=self.status.checks(toverify=True)
            ptosort=self.status.profiles(tosort=True)
            ptoverify=self.status.profiles(toverify=True)
            Label(self.runwindow.frame,text=_("Continue to")).grid(columnspan=2,
                                                            row=row,column=0)
            row+=1
            if ctosort or ctoverify:
                b1=Button(self.runwindow.frame, anchor='c',
                    text=_("Next frame to sort"),
                    command=nframe)
                b1t=ToolTip(b1,_("Automatically pick "
                                "the next tone frame to sort for "
                                "the ‘{}’ profile.".format(profile)))
            else:
                b1=Button(self.runwindow.frame, anchor='c',
                    text=_("Define a new frame"),
                    command=aframe)
                b1t=ToolTip(b1,_("You're done with tone frames already defined "
                                "for the ‘{}’ profile. If you want to continue "
                                "with this profile, define a new frame here."
                                "".format(profile)))
            b1.grid(row=row,column=0,sticky='e')
            if ptosort or ptoverify:
                b2=Button(self.runwindow.frame, anchor='c',
                    text=_("Next syllable profile to sort"),
                    command=nprofile)
                b2t=ToolTip(b2,_("You're done with ‘{0}’ tone frames already "
                                "defined for the ‘{1}’ profile. Click here to "
                                "Automatically select the next syllable "
                                "profile for ‘{0}’.".format(ps, profile)))
            else:
                b2=Button(self.runwindow.frame, anchor='c',
                    text=_("Next Grammatical Category"),
                    command=nps)
                b2t=ToolTip(b2,_("You're done with tone frames already "
                                "defined for the top ‘{}’ syllable profiles. "
                                "Click here to automatically select the next "
                                "grammatical category.".format(ps)))
            b2.grid(row=row,column=1,sticky='w')
            w=int(max(b1.winfo_reqwidth(),b2.winfo_reqwidth())/(
                                            self.frame.winfo_screenwidth()/150))
            log.log(2,"b1w:{}; b2w: {}; maxb1b2w: {}".format(
                                    b1.winfo_reqwidth(),b2.winfo_reqwidth(),w))
            b1.config(width=w)
            b2.config(width=w)
            self.runwindow.waitdone()
            return
    def sortT(self):
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
        log.info('Running sortT:')
        self.getrunwindow()
        """sortingstatus() checks by ps,profile,check (frame),
        for the presence of a populated fieldtype='tone'. So any time any of
        the above is changed, this variable should be reset."""
        """Can't do this test suite unless there are unsorted entries..."""
        """things that don't change in this fn"""
        self.updatesortingstatus() #<===shouldn't need
        thissort=self.status.senseidstosort()[:] #current list
        log.info("Going to sort these senseids: {}".format(self.status.senseidstosort()))
        groups=self.status.groups()
        check=self.params.check()
        """Children of runwindow.frame"""
        if self.exitFlag.istrue():
            return
        titles=Frame(self.runwindow.frame)
        titles.grid(row=0, column=0, sticky="ew", columnspan=2)
        Label(self.runwindow.frame, image=self.parent.photo['sortT'],
                        text='',bg=self.theme['background']
                        ).grid(row=1,column=0,rowspan=3,sticky='nw')
        scroll=self.runwindow.frame.scroll=ScrollingFrame(self.runwindow.frame)
        scroll.grid(row=2, column=1, sticky="new")
        """Titles"""
        title=_("Sort {} Tone (in ‘{}’ frame)").format(
                                        self.languagenames[self.analang],
                                        check)
        Label(titles, text=title,font=self.fonts['title'],anchor='c').grid(
                                            column=0, row=0, sticky="ew")
        instructions=_("Select the one with the same tone melody as")
        Label(titles, text=instructions, font=self.fonts['instructions'],
                anchor='c').grid(column=0, row=1, sticky="ew")
        """Children of self.runwindow.frame.scroll.content"""
        groupbuttons=scroll.content.groups=Frame(scroll.content)
        groupbuttons.grid(row=0,column=0,sticky="ew")
        scroll.content.anotherskip=Frame(scroll.content)
        scroll.content.anotherskip.grid(row=1,column=0)
        """Children of self.runwindow.frame.scroll.content.groups"""
        groupbuttons.row=0 #rows for this frame
        groupvars={}
        for group in groups:
            groupvars[group]=self.tonegroupbuttonframe(groupbuttons,
                                                        group,
                                                        row=groupbuttons.row,
                                                        unsortable=False,
                                                        alwaysrefreshable=True)
            groupbuttons.row+=1
        """Children of self.runwindow.frame.scroll.content.anotherskip"""
        if len(groups) != 1: #in that case, done below
            self.getanotherskip(scroll.content.anotherskip,groupvars)
        """Stuff that changes by lexical entry
        The second frame, for the other two buttons, which also scroll"""
        while self.status.tosort() and not self.runwindow.exitFlag.istrue():
            if len(groups) == 1: #only rerun when moving to 1 button
                self.getanotherskip(scroll.content.anotherskip,groupvars)
            """Pull this variable from self."""
            groupselected=None
            """these just pull the current lists from the object"""
            senseids=self.status.senseidstosort()
            sorted=self.status.senseidssorted()
            log.info("senseids: {}-{} ({})".format(senseids,sorted,self.status.tosort()))
            senseid=senseids[0]
            progress=(str(thissort.index(senseid)+1)+'/'+str(len(thissort)))
            framed=self.datadict.getframeddata(senseid)
            framed.setframe(check)
            """After the first entry, sort by groups."""
            log.debug('self.tonegroups: {}'.format(self.status.groups()))
            Label(titles, text=progress, font=self.fonts['report'], anchor='w'
                                            ).grid(column=1, row=0, sticky="ew")
            text=framed.formatted()
            entryview=Frame(self.runwindow.frame)
            self.sortitem=Label(entryview, text=text,font=self.fonts['readbig'])
            entryview.grid(column=1, row=1, sticky="new")
            self.sortitem.grid(column=0,row=0, sticky="w",pady=50)
            self.sortitem.wrap()
            self.runwindow.waitdone()
            self.runwindow.wait_window(window=self.sortitem)
            if self.runwindow.exitFlag.istrue():
                return 1
            selected=[k for k in groupvars if groupvars[k] is not None
                                            if groupvars[k].get()] #should just be one, but find it
            log.info("selected: {}".format(selected))
            if len(selected)>1:
                log.error("More than one group selected: {}".format(selected))
                return 2
            groupselected=unlist(selected)
            groupvars[groupselected].set(False)
            if groupselected:
                if groupselected in ["NONEOFTHEABOVE",'ok']:
                    """If there are no groups yet, or if the user asks for another
                    group, make a new group."""
                    groupselected=self.addtonegroup()
                    groupbuttons.row+=1 #add to above.
                    """Add the new group to the database"""
                    self.addtonefieldex(senseid,framed,groupselected)
                    """And give the user a button for it, for future words
                    (N.B.: This is only used for groups added during the current
                    run. At the beginning of a run, all used groups have buttons
                    created above.)"""
                    groupvars[groupselected]=self.tonegroupbuttonframe(
                                                    groupbuttons,
                                                    groupselected,
                                                    unsortable=False,
                                                    row=groupbuttons.row,
                                                    alwaysrefreshable=True)
                    #adjust window for new button
                    scroll.windowsize()
                    log.debug('Group added: {}'.format(groupselected))
                    """group with the above?"""
                    """Group these last two?"""
                elif groupselected == 'skip':
                    self.addtonefieldex(senseid,framed,'NA')
                else: #before making a new button, or now, add fields to the sense.
                    """This needs to *not* operate on "exit" button."""
                    self.addtonefieldex(senseid,framed,groupselected)
            else:
                return 1 # this should only happen on Exit
            self.status.marksenseidsorted(senseid)
        self.runwindow.resetframe()
        return
    def reverify(self):
        group=self.status.group()
        check=self.params.check()
        log.info("Reverifying a framed tone group, at user request: {}-{}"
                    "".format(check,group))
        if not self.status.ischeckok():
            self.getcheck() #guess=True
        done=self.status.verified()
        if group not in done:
            self.getgroup()
            if group == None:
                log.info("I asked for a framed tone group, but didn't get one.")
                return
        else:
            done.remove(group)
        self.maybesort()
    def verifyT(self,menu=False):
        log.info("Running verifyT!")
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
        groups=self.status.groups()
        group=self.status.group()
        # The title for this page changes by group, below.
        self.getrunwindow(msg="preparing to verify group: {}".format(group))
        # if menu == True:
        #     self.runwindow.doverifymenu()
        # ContextMenu(self.runwindow, context='verifyT') #once for all
        oktext='These all have the same tone'
        instructions=_("Read down this list to verify they all have the same "
            "tone melody. Select any word with a different tone melody to "
            "remove it from the list.")
        """group is set here, but probably OK"""
        self.makestatusdict()
        last=False
        if self.runwindow.exitFlag.istrue():
            return 1
        if group in self.status.verified():
            log.info("‘{}’ already verified, continuing.".format(group))
            return
        senseids=self.getexsall(group)
        if len(senseids) <= 1:
            if len(senseids) == 1:
                verified=True
                log.info("Group ‘{}’ only has {} example; marking verified and "
                        "continuing.".format(group,len(senseids)))
            if len(senseids) == 0:
                verified=False
                log.info("Group ‘{}’ only has {} example; removing and "
                "continuing.".format(group,len(senseids)))
            self.updatestatus(verified=verified)
            self.updatestatuslift(check,group,verified=verified)
            if not verified:
                groups.remove(group)
            return
        title=_("Verify {} Tone Group ‘{}’ (in ‘{}’ frame)").format(
                                    self.languagenames[self.analang],
                                    group,
                                    check
                                    )
        titles=Frame(self.runwindow.frame)
        titles.grid(column=0, row=0, columnspan=2, sticky="w")
        Label(titles, text=title,
                font=self.fonts['title']
                ).grid(column=0, row=0, sticky="w")
        """Move this to bool vars, like for sortT"""
        if hasattr(self,'groupselected'): #so it doesn't get in way later.
            delattr(self,'groupselected')
        row=0
        column=0
        if group in groups:
            progress=('('+str(groups.index(group)+1)+'/'+str(len(
                                                            groups))+')')
            Label(titles, text=progress,anchor='w'
                                ).grid(row=0,column=1,sticky="ew")
        Label(titles, text=instructions).grid(row=1,column=0, columnspan=2,
                                                                sticky="wns")
        Label(self.runwindow.frame, image=self.parent.photo['verifyT'],
                        text='',
                        bg=self.theme['background']
                        ).grid(row=1,column=0,rowspan=3,sticky='nwse')
        """Scroll after instructions"""
        self.sframe=ScrollingFrame(self.runwindow.frame)
        self.sframe.grid(row=1,column=1,columnspan=2,sticky='wsne')
        row+=1
        """put entry buttons here."""
        for senseid in senseids:
            if senseid is None: #needed?
                continue
            self.verifybutton(self.sframe.content,senseid,
                                row, column,
                                label=False)
            row+=1
        bf=Frame(self.sframe.content)
        bf.grid(row=row, column=0, sticky="ew")
        b=Button(bf, text=oktext,
                        cmd=lambda:returndictndestroy(self, #destroy frame!
                                    self.runwindow.frame,
                                    {'groupselected':"ALLOK"}),
                        anchor="w",
                        font=self.fonts['instructions']
                        )
        b.grid(column=0, row=0, sticky="ew")
        if self.runwindow.exitFlag.istrue():
            return 1
        self.sframe.windowsize()
        self.runwindow.waitdone()
        b.wait_window(bf)
        if (self.runwindow.exitFlag.istrue() or
                                        not hasattr(self,'groupselected')):
            return 1
        elif self.groupselected == "ALLOK":
            log.debug("User selected ‘{}’, moving on.".format(oktext))
            self.updatestatus(verified=True)
            self.updatestatuslift(check,group,verified=True)
            # self.checkcheck() #now after verifyT is done
        else:
            log.debug("User did NOT select ‘{}’, assuming we'll come "
                    "back to this!!".format(oktext))
        #Once done verifying each group:
        if self.runwindow.exitFlag.istrue():
            return 1
        else:
            self.runwindow.waitdone()
            return 0
    def verifybutton(self,parent,senseid,row,column=0,label=False,**kwargs):
        # This must run one subcheck at a time. If the subcheck changes,
        # it will fail.
        # should move to specify location and fieldvalue in button lambda
        if 'font' not in kwargs:
            kwargs['font']=self.fonts['read']
        if 'anchor' not in kwargs:
            kwargs['anchor']='w'
        #This should be pulling from the example, as it is there already
        framed=self.datadict.getframeddata(senseid)
        check=self.params.check()
        framed.setframe(check)
        text=framed.formatted(notonegroup=True)
        if label==True:
            b=Label(parent, text=text,
                    **kwargs
                    ).grid(column=column, row=row,
                            sticky="ew",
                            ipady=15)
        else:
            bf=Frame(parent, pady='0') #This will be killed by removesenseidfromsubcheck
            bf.grid(column=0, row=row, sticky='ew')
            b=Button(bf, text=text, pady='0',
                    cmd=lambda p=bf,s=senseid:removesenseidfromsubcheck(
                                                    self,p,s),
                    **kwargs
                    ).grid(column=column, row=0,
                            sticky="ew",
                            ipady=15 #Inside the buttons...
                            )
    def joinT(self):
        log.info("Running joinT!")
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
        groups=self.status.groups()
        if len(groups) <2:
            log.debug("No tone groups to distinguish!")
            if not self.exitFlag.istrue():
                self.runwindow.waitdone()
            return 0
        title=_("Review Groups for {} Tone (in ‘{}’ frame)").format(
                                        self.languagenames[self.analang],
                                        check
                                        )
        oktext=_('These are all different')
        introtext=_("Congratulations! \nAll your {} with profile ‘{}’ are "
                "sorted into the groups exemplified below (in the ‘{}’ frame). "
                "Do any of these have the same tone melody? "
                "If so, click on the two groups. If not, click ‘{}’."
                ).format(ps,profile,check,oktext)
        log.debug(introtext)
        if hasattr(self,'groupselected'):
            delattr(self,'groupselected') # self.groupselected=None
        self.runwindow.resetframe()
        self.runwindow.frame.titles=Frame(self.runwindow.frame)
        self.runwindow.frame.titles.grid(column=0, row=0, columnspan=2, sticky="w")
        Label(self.runwindow.frame.titles, text=title,
                font=self.fonts['title']
                ).grid(column=0, row=0, sticky="w")
        i=Label(self.runwindow.frame.titles, text=introtext)
        i.grid(row=1,column=0, sticky="w")
        Label(self.runwindow.frame, image=self.parent.photo['joinT'],
                        text='',
                        bg=self.theme['background']
                        ).grid(row=2,column=0,rowspan=2,sticky='nw')
        self.sframe=ScrollingFrame(self.runwindow.frame)
        self.sframe.grid(row=2,column=1)
        self.sortitem=self.sframe.content
        row=0
        canary=Label(self.runwindow,text='')
        canary.grid(row=5,column=5)
        canary2=Label(self.runwindow,text='')
        canary2.grid(row=5,column=5)
        for group in groups:
            self.tonegroupbuttonframe(self.sortitem,group,row,notonegroup=False,
                                unsortable=False,canary=canary,canary2=canary2)
            row+=1
        """If all is good, destroy this frame."""
        b=Button(self.sortitem, text=oktext,
                    cmd=lambda:returndictnsortnext(self,
                    self.runwindow.frame,
                    {'groupselected':"ALLOK"},
                    canary=canary,canary2=canary2
                    ),
                    anchor="c",
                    font=self.fonts['instructions']
                    )
        b.grid(column=0, row=row, sticky="ew")
        self.runwindow.waitdone()
        self.runwindow.frame.wait_window(canary)
        #On first button press/exit:
        if self.runwindow.exitFlag.istrue():
            return 1
        if hasattr(self,'groupselected'):
            if self.groupselected == "ALLOK":
                print(f"User selected ‘{oktext}’, moving on.")
                delattr(self,'groupselected')
                return 0
            else:
                group1=self.groupselected
                delattr(self,'groupselected')
                if group1 in groups:
                    row=groups.index(group1)
                else:
                    log.error("Group ‘{}’ isn't found in list {}!".format(
                                group1,groups))
                    row=len(groups)+1
                self.tonegroupbuttonframe(self.sortitem,group1,row,
                                        notonegroup=False,unsortable=False,
                                        label=True, font=self.fonts['readbig'],
                                        canary=canary,canary2=canary2)
                log.debug('self.tonegroups: {}; group1: {}'.format(groups,
                    group1))
                self.runwindow.wait_window(canary2)
                #On second button press/exit:
                if self.runwindow.exitFlag.istrue(): #i.e., user exits by now
                    return 1
                if hasattr(self,'groupselected'):
                    if self.groupselected == "ALLOK":
                        print(f"User selected ‘{oktext}’, moving on.")
                        delattr(self,'groupselected')
                        return 0
                    else:
                        msg=_("Now we're going to move group ‘{0}’ into "
                            "‘{1}’, marking ‘{1}’ unverified.".format(
                            group1,self.groupselected))
                        self.runwindow.wait(msg=msg)
                        log.debug(msg)
                        """All the senses we're looking at, by ps/profile"""
                        self.updatebysubchecksenseid(group1,self.groupselected)
                        groups.remove(group1)
                        self.updatestatuslift(group=group1,refresh=False) #done above
                        self.updatestatus(group=group1,refresh=False) #not verified=True --since joined.
                        self.updatestatuslift(group=self.groupselected) #done above
                        self.updatestatus(group=self.groupselected) #not verified=True --since joined.
                        self.maybesort() #go back to verify, etc.
        """'These are all different' doesn't need to be saved anywhere, as this
        can happen at any time. Just move on to verification, where each group's
        sameness will be verified and recorded."""
    def updatebysubchecksenseid(self,oldtonevalue,newtonevalue,verified=False):
        # This function updates the field value and verification status (which
        # contains the field value) in the lift file.
        # This is all the words in the database with the given
        # location:value correspondence (any ps/profile)
        lst2=self.db.get('sense',location=check,tonevalue=oldtonevalue
                                                                ).get('senseid')
        # We are agnostic of verification status of any given entry, so don't
        # use this to change names, not to mark verification status (do that
        # with self.updatestatuslift())
        rm=self.verifictioncode(check,oldtonevalue)
        add=self.verifictioncode(check,newtonevalue)
        """The above doesn't test for profile, so we restrict that next"""
        senseids=self.slices.inslice(lst2)
        for senseid in senseids:
            """This updates the fieldvalue from 'fieldvalue' to
            'newfieldvalue'."""
            self.db.addmodexamplefields(senseid=senseid,fieldtype='tone',
                                location=check,#fieldvalue=oldtonevalue,
                                fieldvalue=newtonevalue)
            self.db.modverificationnode(senseid=senseid,vtype=profile,
                                                add=add,rms=[rm],addifrmd=True)
        self.db.write() #once done iterating over senseids
    def addtonegroup(self):
        log.info("Adding a tone group!")
        values=[0,] #always have something here
        groups=self.status.groups()
        for i in groups:
            try:
                values+=[int(i)]
            except:
                log.info('Tone group {} cannot be interpreted as an integer!'
                        ''.format(i))
        newgroup=max(values)+1
        groups.append(str(newgroup))
        return str(newgroup)
    def addtonefieldex(self,senseid,framed,groupselected):
        guid=None
        if groupselected is None or groupselected == '':
            log.error("groupselected: {}; this should never happen"
                        "".format(groupselected))
            exit()
        check=self.params.check()
        log.debug("Adding {} value to {} location in 'tone' fieldtype, "
                "senseid: {} guid: {} (in main_lift.py)".format(
                    groupselected,
                    check,
                    senseid,
                    guid))
        self.db.addmodexamplefields( #This should only mod if already there
                                    senseid=senseid,
                                    analang=self.analang,
                                    fieldtype='tone',location=check,
                                    framed=framed,
                                    fieldvalue=groupselected
                                    )
        tonegroup=unlist(self.db.get("example/tonefield/form/text",
                        senseid=senseid, location=check).get('text'))
        if tonegroup != groupselected:
            log.error("Field addition failed! LIFT says {}, not {}.".format(
                                                tonegroup,groupselected))
        else:
            log.info("Field addition succeeded! LIFT says {}, which is {}."
                                        "".format(tonegroup,groupselected))
        self.updatestatus(group=groupselected) #this marks the group unverified.
        self.db.write() #This is never iterated over; just one entry at a time.
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
    def getsenseidsbytoneUFgroups(self):
        """This returns a dict of {UFtonegroup:[senseids]}"""
        log.debug(_("Looking for sensids by UF tone groups for {}-{}").format(
                    self.slices.profile(), self.slices.ps())
                    )
        sorted={}
        """Still working on one ps-profile combo at a time."""
        self.getidstosort() #just in case this changed
        for senseid in self.slices.senseids(): #I should be able to make this a regex...
            toneUFgroup=firstoflist(self.db.get('sense/tonefield/form/text',
                                                senseid=senseid).get('text'))
            if toneUFgroup is not None:
                if toneUFgroup not in sorted:
                    sorted[toneUFgroup]=[]
                sorted[toneUFgroup]+=[senseid]
        """drop this"""
        self.toneUFgroups=list(dict.fromkeys(sorted))
        log.debug("UFtonegroups (getsenseidsbytoneUFgroups): {}".format(
                                                            self.toneUFgroups))
        return sorted
    def gettoneUFgroups(self): #obsolete?
        """This returns just the list of UF tone groups in the current slice"""
        log.debug("Looking for UF tone groups for {}-{} slice".format(profile,
                                                                    ps))
        toneUFgroups=[]
        """Still working on one ps-profile combo at a time."""
        for senseid in self.slices.senseids():
            toneUFgroups+=self.db.get('sense/tonefield/form/text',
                                                    senseid=senseid).get('text')
        self.toneUFgroups=list(dict.fromkeys(toneUFgroups))
    def gettonegroups(self,ps=None,profile=None,check=None,renew=False):
        """This returns (non-UF) tonegroups from the LIFT file. It should not
        be used to affirm that often; sortT/joinT manage this."""
        """This depends on ps, profile, and check, but can take current or
        specified values"""
        """To read groups from the status object, use self.status.groups()"""
        if check == None:
            check=self.params.check()
        if profile == None:
            self.slices.profile()
        if ps == None:
            self.slices.ps()
        if not renew:
            self.status.groups(ps=ps,profile=profile,check=check)
            return
        log.log(3,"Looking for tone groups for {} frame".format(check))
        tonegroups=[]
        """This takes current for any NONE values"""
        senseids=self.slices.senseids(ps=ps,profile=profile)
        for senseid in senseids:
            tonegroup=self.db.get("example/tonefield/form/text",
                                senseid=senseid, location=check).get('text')
            if unlist(tonegroup) in ['NA','','ALLOK', None]:
                log.error("tonegroup {} found in sense {} under location {}!"
                    "".format(tonegroup,senseid,check))
            else:
                tonegroups+=tonegroup
        groups=list(dict.fromkeys(tonegroups))
        log.debug("gettonegroups groups: {}".format(groups))
        for value in ['NA', '', None]:
            if value in groups:
                log.error("Found (and removing) value {} in {}-{} for {} "
                    "frame: {}".format(value, ps, profile, check, groups))
                groups.remove(value)
        log.debug('gettonegroups ({}): {}'.format(check, groups))
        """This takes current for any NONE values"""
        self.status.dictcheck(ps=ps,profile=profile,check=check)
        self.status.groups(groups,ps=ps,profile=profile,check=check) #set
        verified=self.status.done(ps=ps,profile=profile,check=check) #read
        for v in verified:
            if v not in groups:
                log.error("Removing verified group {} not in actual groups: {}!"
                            "".format(v, groups))
                verified.remove(v)
        self.status.done(verified,ps=ps,profile=profile,check=check) #set
        self.storesettingsfile(setting='status')
    def marksortedguid(self,guid):
        """I think these are only valuable during a check, so we don't have to
        constantly refresh sortingstatus() from the lift file."""
        """These four functions should be generalizable"""
        self.guidssorted.append(guid)
        self.guidstosort.remove(guid)
    def marktosortguid(self,guid):
        self.guidstosort.append(guid)
        self.guidssorted.remove(guid)
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
    def updatesortingstatus(self):
        """This reads LIFT to create lists for sorting, populating lists of
        sorted and unsorted senses. So don't iterate over it. Instead, use
        checkforsenseidstosort to just confirm tosort status"""
        """To get this from the object, use status.tosort(), todo() or done()"""
        check=self.params.check()
        senseids=self.slices.senseids()
        self.status.renewsenseidstosort([],[])
        for senseid in senseids:
            v=unlist(self.db.get("example/tonefield/form/text", senseid=senseid,
                                location=check,showurl=True).get('text'))
            log.info("Found tone value (updatesortingstatus): {} ({})".format(v,type(v)))
            if v in ['','None']: #unlist() returns strings
                log.info("Marking senseid {} tosort (v: {})".format(senseid,v))
                self.status.marksenseidtosort(senseid)
            else:
                log.info("Marking senseid {} sorted (v: {})".format(senseid,v))
                self.status.marksenseidsorted(senseid)
        if len(self.status.senseidstosort()) >0:
            log.info("updatesortingstatus shows senseidstosort remaining")
            vts=True
        else:
            log.info("updatesortingstatus shows no senseidstosort remaining")
            vts=False
        self.status.tosort(vts)
        log.info("updatesortingstatus senseids tosort: {}".format(self.status.senseidstosort()))
        log.info("updatesortingstatus senseids sorted: {}".format(self.status.senseidssorted()))
        log.info("tosort (end of updatesortingstatus): {}".format(self.status.tosort()))
    def settonevariablesiterable(self,cvt='T',ps=None,profile=None,check=None):
        """This is currently called in iteration"""
        self.checkforsenseidstosort(cvt=cvt,ps=ps,profile=profile,check=check)
        self.gettonegroups() #reads from self.status, without renew=True
    def settonevariables(self):
        """This is currently called before sorting. This is a waste, if you're
        not going to sort afterwards"""
        self.updatesortingstatus()
        """This is safe to iterate over"""
        self.gettonegroups() #reads from self.status, without renew=True
    def tryNAgain(self):
        check=self.params.check()
        if check in self.params.checks():
            senseids=self.status.senseids()
        else:
            #Give an error window here
            log.error("Not Trying again; set a tone frame first!")
            self.getrunwindow(nowait=True)
            buttontxt=_("Sort!")
            text=_("Not Trying Again; set a tone frame first!")
            Label(self.runwindow.frame, text=text).grid(row=0,column=0)
            return
        for senseid in senseids: #this is a ps-profile slice
            self.db.addmodexamplefields(senseid=senseid,fieldtype='tone',
                            location=check,fieldvalue='', #just clear this
                            oldfieldvalue='NA', showurl=True #if this
                            )
        self.maybesort() #Because we want to go right into sorting...
    def getanotherskip(self,parent,vardict):
        """This function presents a group of buttons for the user to choose
        from, one for each tone group in that location/ps/profile in the
        database, plus one for the user to indicate that the word doesn't
        belong in any of those (new group), plus one to for the user to
        indicate that the word/frame combo doesn't work (skip)."""
        def firstok():
            vardict['ok'].set(True)
            remove(okb) #use this button exactly once
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
        row=0
        firstOK=_("This word is OK in this frame")
        newgroup=_("Different")
        skip=_("Skip this word/phrase")
        """This should just add a button, not reload the frame"""
        row+=10
        bf=Frame(parent)
        bf.grid(column=0, row=row, sticky="ew")
        if self.status.groups() == []:
            vardict['ok']=tkinter.BooleanVar()
            okb=Button(bf, text=firstOK,
                            cmd=firstok,
                            anchor="w",
                            font=self.fonts['instructions']
                            )
            okb.grid(column=0, row=0, sticky="ew")
            # row+=1
        else:
            vardict['NONEOFTHEABOVE']=tkinter.BooleanVar()
            difb=Button(bf, text=newgroup,
                        cmd=different,
                        anchor="w",
                        font=self.fonts['instructions']
                        )
            difb.grid(column=0, row=0, sticky="ew")
        # row+=1
        vardict['skip']=tkinter.BooleanVar()
        skipb=Button(bf, text=skip,
                        cmd=skip,
                        # cmd=lambda:returndictnsortnext(self,parent,
                        #             {'groupselected':"NA"}),
                        anchor="w",
                        font=self.fonts['instructions']
                        )
        skipb.grid(column=0, row=1, sticky="ew")
    def tonegroupbuttonframe(self,parent,group,row,column=0,label=False,canary=None,canary2=None,alwaysrefreshable=False,playable=False,renew=False,unsortable=False,**kwargs):
        def again():
            self.tonegroupbuttonframe(
                parent=parent,unsortable=unsortable,
                group=group,notonegroup=notonegroup,
                canary=canary,canary2=canary2,
                row=row,column=column,label=label,
                alwaysrefreshable=alwaysrefreshable, font=font,
                playable=playable,renew=renew,refreshcount=refreshcount,**kwargs)
        def select():
            var.set(True)
        def sortnext():
            self.sortitem.destroy()
        def remove():
            parent.destroy()
        def selectnremove():
            select()
            remove()
        def selectnsortnext():
            select()
            sortnext()
        def selectnlabelize():
            select()
            label=True
            again()
            sortnext()
            remove()
        def unsort():
            removesenseidfromsubcheck(self,bf,senseid)
            self.tonegroupbuttonframe(
                parent=parent,unsortable=unsortable,
                group=group,notonegroup=notonegroup,
                canary=canary,canary2=canary2,
                row=row,column=column,label=label,
                alwaysrefreshable=alwaysrefreshable, font=font,
                playable=playable,renew=True,refreshcount=refreshcount,**kwargs)
        var=tkinter.BooleanVar()
        font=kwargs.pop('font',self.fonts['read'])
        kwargs['anchor']=kwargs.get('anchor','w')
        notonegroup=kwargs.pop('notonegroup',True)
        refreshcount=kwargs.pop('refreshcount',-1)+1
        sticky=kwargs.pop('sticky',"ew")
        example=self.getex(group,notonegroup=notonegroup,renew=renew)
        check=self.params.check()
        if example is None:
            log.error("Apparently the example for tone group {} in check {} "
                        "came back {}".format(group,check,example))
            return
        renew=kwargs.pop('renew',False)
        if renew is True:
            log.info("Resetting tone group example ({}): {} of {} examples"
                    "".format(group,self.exs[group],example['n']))
            del self.exs[group]
        framed=example['framed']
        framed.setframe(check)
        if framed is None:
            log.error("Apparently the framed example for tone group {} in "
                        "frame {} came back {}".format(group,check,example))
            return
        text=framed.formatted()
        """This should maybe be brought up a level in frames?"""
        bf=Frame(parent)
        bf.grid(column=column, row=row, sticky=sticky)
        if label==True:
            b=Label(bf, text=text, font=font, **kwargs)
            b.grid(column=1, row=0, sticky="ew", ipady=15) #Inside the buttons
        elif playable == True:
            url=RecordButtonFrame.makefilenames(None,self, #not Classy...
                                                example['senseid'])
            diredurl=str(file.getdiredurl(self.audiodir,url))
            thefileisthere=file.exists(diredurl)
            log.info("fileisthere: {} ({})".format(diredurl,url))
            if thefileisthere:
                self.pyaudiocheck()
                self.soundsettingscheck()
                self.player=sound.SoundFilePlayer(diredurl,self.pyaudio,self.
                                                                soundsettings)
                b=Button(bf, text=text, cmd=self.player.play, font=font)
                bttext=_("Click to hear this utterance")
                if program['praatisthere']:
                    bttext+='; '+_("right click to open in praat")
                    b.bind('<Button-3>',lambda x: praatopen(diredurl))
                bt=ToolTip(b,bttext)
                senseid=framed['senseid']
                if unsortable:
                    t=_("<= remove *this* *word* from \nthe group (sort into another, later)")
                    b_unsort=Button(bf,text = t, cmd=unsort, anchor ='c')
                    b_unsort.grid(row=0,column=2,padx=50)
            else: #Refresh if this should be playable but there no sound file.
                if refreshcount < len(self.getexsall(group)):
                    self.tonegroupbuttonframe(
                    parent=parent,
                    group=group,notonegroup=notonegroup,
                    canary=canary,canary2=canary2,
                    row=row,column=column,label=label, font=font,
                    alwaysrefreshable=alwaysrefreshable,unsortable=unsortable,
                    playable=playable,renew=True,refreshcount=refreshcount,
                                                                    **kwargs)
                else:
                    self.tonegroupbuttonframe(
                    parent=parent,
                    group=group,notonegroup=notonegroup,
                    canary=canary,canary2=canary2, font=font,
                    row=row,column=column,label=True, #give up on buttons
                    alwaysrefreshable=alwaysrefreshable,unsortable=unsortable,
                    playable=False, #give up on playing
                    renew=True,refreshcount=refreshcount,**kwargs)
                return #In either case, stop making the current frame.
            b.grid(column=1, row=0, sticky="nesw", ipady=15) #Inside the buttons
        else:
            b=Button(bf, text=text, font=font,
                    cmd=selectnsortnext,
                                                                    **kwargs)
            b.grid(column=1, row=0, sticky="ew", ipady=15) #Inside the buttons
            bt=ToolTip(b,_("Pick this Group"))
        if example['n'] > 1 or alwaysrefreshable == True:
            bc=Button(bf, image=self.parent.photo['change'], #🔃 not in tck
                            cmd=lambda p=parent:self.tonegroupbuttonframe(
                                parent=parent,unsortable=unsortable,
                                group=group,notonegroup=notonegroup,
                                canary=canary,canary2=canary2, font=font,
                                row=row,column=column,label=label,
                                alwaysrefreshable=True, #once refreshed, keep it
                                playable=playable,renew=True,**kwargs),
                            text=str(example['n']),
                            compound='center',
                            **kwargs)
            bc.grid(column=0, row=0, sticky="nsew", ipady=15) #In buttonframe
            bct=ToolTip(bc,_("Change example word"))
        return var
    def printentryinfo(self,guid):
        outputs=[nn(self.db.citationorlexeme(guid=guid))]
        for lang in self.glosslangs:
            outputs.append(nn(self.db.glossordefn(guid=guid,glosslang=lang)))
        outputs.append(nn(self.db.get('pronunciationfieldvalue',
                                        fieldtype='tone',
                                        location=group,guid=guid)))
        return '\t'.join(outputs)
    def guesssubcheck(self):
        """obsolete"""
        cvt=self.params.cvt()
        if cvt == 'CV': #Dunno how to guess this yet...
            if group in ([x[0] for x in self.subchecksprioritized['V']+
                                self.subchecksprioritized['C']+
                                self.subchecksprioritized['T']
                                ]):
                self.subcheck=self.scount[ps]['C'][0]+self.scount[ps]['V'][0]
        else:
            self.subcheck=firstoflist(self.subchecksprioritized[cvt],
                                                            othersOK=True)[0]
    def getsubchecksprioritized(self):
        """Tone doesn't have subchecks, so we just make it 'None' here."""
        """I really should be able to order these..."""
        check=self.params.check()
        ps=self.slices.ps()
        profile=self.slices.profile()
        log.debug("ps: {}, profile: {}, name: {}".format(ps,profile,check))
        self.subchecksprioritized={
        "V":self.scount[ps]['V'], #self.db.v[self.analang],
        "C":self.scount[ps]['C'], #self.db.c[self.analang],
        "CV":''}#,
        cvt=self.params.cvt()
        if cvt == 'T':
            self.subchecksprioritized['T']=[(x,None) for x in self.status['T'][
                ps][profile][check]['groups']+[None]]
    """Doing stuff"""
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
            self.runwindow=Window(self.frame,title=title)
        self.runwindow.title(title)
        self.runwindow.lift()
        if nowait != True:
            self.runwindow.wait(msg=msg)
    def runcheck(self):
        self.storesettingsfile() #This is not called in checkcheck.
        t=(_('Run Check'))
        log.info("Running check...")
        i=0
        ps=self.slices.ps()
        group=self.status.group()
        if None in [self.analang, ps, group]:
            log.debug(_("'Null' value (what does this mean?): {} {} {}").format(
                                        self.analang, ps, group))
        cvt=self.params.cvt()
        check=self.params.check()
        profile=self.slices.ps()
        if not self.status.ischeckok():
            exit=self.getcheck()
            if exit:
                self.runcheck()
            return #if the user didn't supply a check
        if cvt == 'T':
            self.settonevariables() #here, or later?
            self.maybesort()
        elif None not in [check,group]: #do the CV checks
            self.getresults()
        else:
            window=Window(self.frame)
            text=_('Error: please set Check/Subcheck first! ({}/{})').format(
                                                     check,group)
            Label(window,text=text).grid(column=0, row=i)
            i+=1
            return
    def record(self):
        if cvt == 'T':
            self.showtonegroupexs()
        else:
            self.showentryformstorecord()
    def makelabelsnrecordingbuttons(self,parent,sense):
        framed=self.datadict.getframeddata(sense['nodetoshow'])
        t=framed.formatted(noframe=True)
        for g in sense['glosses']:
            t+='\t‘'+g
            if ('plnode' in sense) and (sense['nodetoshow'] is sense['plnode']):
                t+=" (pl)"
            if ('impnode' in sense) and (sense['nodetoshow'] is sense['impnode']):
                t+="!"
            t+='’'
        lxl=Label(parent, text=t)
        lcb=RecordButtonFrame(parent,self,id=sense['guid'], #reconfigure!
                                        framed=framed,node=sense['nodetoshow'],
                                        gloss=sense['gloss'])
        lcb.grid(row=sense['row'],column=sense['column'],sticky='w')
        lxl.grid(row=sense['row'],column=sense['column']+1,sticky='w')
    def showentryformstorecordpage(self,ps=None,profile=None):
        #The info we're going for is stored above sense, hence guid.
        if self.runwindow.exitFlag.istrue():
            log.info('no runwindow; quitting!')
            return
        if not self.runwindow.frame.winfo_exists():
            log.info('no runwindow frame; quitting!')
            return
        self.runwindow.resetframe()
        self.runwindow.wait()
        count=self.slices.count()
        text=_("Record {} {} Words: click ‘Record’, talk, "
                "and release ({} words)".format(profile,ps,
                                                count))
        instr=Label(self.runwindow.frame, anchor='w',text=text)
        instr.grid(row=0,column=0,sticky='w')
        buttonframes=ScrollingFrame(self.runwindow.frame)
        buttonframes.grid(row=1,column=0,sticky='w')
        row=0
        done=list()
        for senseid in self.profilesbysense[ps][profile]:
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
                sense['gloss'].append(firstoflist(self.db.glossordefn(
                                                guid=sense['guid'],
                                                glosslang=lang
                                                ),othersOK=True))
            if self.db.pluralname is not None:
                sense['plnode']=firstoflist(self.db.get('field',
                                        guid=sense['guid'],
                                        lang=self.analang,
                                        fieldtype=self.db.pluralname).get())
            if self.db.imperativename is not None:
                sense['impnode']=firstoflist(self.db.get('field',
                                        guid=sense['guid'],
                                        lang=self.analang,
                                        fieldtype=self.db.imperativename).get())
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
    def showentryformstorecord(self,justone=True):
        # Save these values before iterating over them
        #Convert to iterate over local variables
        self.getrunwindow()
        if justone==True:
            self.showentryformstorecordpage()
        else:
            for psprofile in self.status.valid(): #self.profilecountsValid:
                if self.runwindow.exitFlag.istrue():
                    return 1
                ps=psprofile[2]
                profile=psprofile[1]
                nextb=Button(self.runwindow,text=_("Next Group"),
                                        cmd=self.runwindow.resetframe) # .frame.destroy
                nextb.grid(row=0,column=1,sticky='ne')
                self.showentryformstorecordpage(ps=ps,profile=profile)
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
        instr=Label(self.runwindow.frame, anchor='w',text=text)
        instr.grid(row=0,column=0,sticky='w',columnspan=2)
        if (self.entriestoshow is None) and (senses is None):
            Label(self.runwindow.frame, anchor='w',
                    text=_("Sorry, there are no entries to show!")).grid(row=1,
                                    column=0,sticky='w')
            return
        if self.runwindow.frame.skip == False:
            skipf=Frame(self.runwindow.frame)
            skipb=Button(skipf, text=linebreakwords(_("Skip to next undone")),
                        cmd=skipf.destroy)
            skipf.grid(row=1,column=1,sticky='w')
            skipb.grid(row=0,column=0,sticky='w')
            skipb.bind('<ButtonRelease>', setskip)
        if senses is None:
            senses=self.entriestoshow
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
                                                    self.audiolang) == False)):
                continue
            row=0
            if self.runwindow.exitFlag.istrue():
                return 1
            entryframe=Frame(self.runwindow.frame)
            entryframe.grid(row=1,column=0)
            if progress is not None:
                progressl=Label(self.runwindow.frame, anchor='e',
                    font=self.fonts['small'],
                    text="({} {}/{})".format(*progress)
                    )
                progressl.grid(row=0,column=2,sticky='ne')
            """This is the title for each page: isolation form and glosses."""
            titleframed=self.datadict.getframeddata(senseid)
            if titleframed.analang is None:
                entryframe.destroy() #is this ever needed?
                continue
            text=titleframed.formatted(noframe=True,notonegroup=True)
            Label(entryframe, anchor='w', font=self.fonts['read'],
                    text=text).grid(row=row,
                                    column=0,sticky='w')
            """Then get each sorted example"""
            self.runwindow.frame.scroll=ScrollingFrame(entryframe)
            self.runwindow.frame.scroll.grid(row=1,column=0,sticky='w')
            examplesframe=Frame(self.runwindow.frame.scroll.content)
            examplesframe.grid(row=0,column=0,sticky='w')
            examples.reverse()
            for example in examples:
                if (skip == True and
                    lift.examplehaslangform(example,self.audiolang) == True):
                    continue
                """These should already be framed!"""
                framed=self.datadict.getframeddata(example)
                if framed.forms[self.analang] is None: # when?
                    continue
                row+=1
                """If I end up pulling from example nodes elsewhere, I should
                probably make this a function, like getframeddata"""
                text=framed.formatted()
                rb=RecordButtonFrame(examplesframe,self,id=senseid,node=example,
                                    form=nn(framed.forms[self.analang]),
                                    gloss=nn(framed.forms[self.glosslang])
                                    ) #no gloss2; form/gloss just for filename
                rb.grid(row=row,column=0,sticky='w')
                Label(examplesframe, anchor='w',text=text
                                        ).grid(row=row, column=1, sticky='w')
            row+=1
            d=Button(examplesframe, text=_("Done/Next"),command=entryframe.destroy)
            d.grid(row=row,column=0)
            self.runwindow.waitdone()
            examplesframe.wait_window(entryframe)
            if self.runwindow.exitFlag.istrue():
                return 1
            if self.runwindow.frame.skip == True:
                return 'skip'
    def showtonegroupexs(self):
        def next():
            self.nextprofile()
            self.runwindow.destroy()
            self.showtonegroupexs()
        if (not(hasattr(self,'examplespergrouptorecord')) or
            (type(self.examplespergrouptorecord) is not int)):
            self.examplespergrouptorecord=100
            self.storesettingsfile()
        torecord=self.getsenseidsbytoneUFgroups()
        ntorecord=len(torecord) #number of groups
        nexs=len([k for i in torecord for j in torecord[i] for k in j])
        nslice=self.slices.nsenseids()
        log.info("Found {} analyzed of {} examples in slice".format(nexs,nslice))
        exit()
        skip=False
        if ntorecord == 0:
            log.error(_("How did we get no UR tone groups? {}-{}"
                    "\nHave you run the tone report recently?"
                    "\nDoing that for you now...").format(profile,ps))
            self.tonegroupreport(silent=True)
            self.showtonegroupexs()
            return
        batch={}
        for i in range(self.examplespergrouptorecord):
            batch[i]=[]
            for toneUFgroup in torecord: #self.toneUFgroups:
                print(i,len(torecord[toneUFgroup]),toneUFgroup,torecord[toneUFgroup])
                if len(torecord[toneUFgroup]) > i: #no done piles.
                    senseid=[torecord[toneUFgroup][i]] #list of one
                else:
                    print("Not enough examples, moving on:",i,toneUFgroup)
                    continue
                log.info(_('Giving user the number {} example from tone '
                        'group {}'.format(i,toneUFgroup)))
                exited=self.showsenseswithexamplestorecord(senseid,
                            (toneUFgroup, i+1, self.examplespergrouptorecord),
                            skip=skip)
                if exited == 'skip':
                    skip=True
                if exited == True:
                    return
        if not (self.runwindow.exitFlag.istrue() or self.exitFlag.istrue()):
            self.runwindow.waitdone()
            self.runwindow.resetframe()
            Label(self.runwindow.frame, anchor='w',font=self.fonts['read'],
            text=_("All done! Sort some more words, and come back.")
            ).grid(row=0,column=0,sticky='w')
            Button(self.runwindow.frame,
                    text=_("Continue to next syllable profile"),
                    command=next).grid(row=1,column=0)
        self.donewpyaudio()
    def senseidformsbyregex(self,regex,):
        """This function takes in a compiled regex,
        and outputs a list/dictionary of senseid/{senseid:form} form."""
        output=[] #This is just a list of senseids now: (Do we need the dict?)
        for form in self.formstosearch[ps]:
            if regex.search(form):
                output+=self.formstosearch[ps][form]
        return output
    def getresults(self):
        self.getrunwindow()
        self.makeresultsframe()
        self.adhocreportfileXLP=''.join([str(self.reportbasefilename)
                                        ,'_',str(ps)
                                        ,'-',str(profile)
                                        ,'_',str(check)
                                        ,'_ReportXLP.xml'])
        xlpr=xlpr=self.xlpstart()
        """"Do I need this?"""
        self.results.grid(column=0,
                        row=self.runwindow.frame.grid_info()['row']+1,
                        columnspan=5,
                        sticky=(tkinter.N, tkinter.S, tkinter.E, tkinter.W))
        print(_("Getting results of Search request"))
        c1 = "Any"
        c2 = "Any"
        i=0
        """nn() here keeps None and {} from the output, takes one string,
        list, or tuple."""
        text=(_("{} roots of form {} by {}".format(ps,profile,
                                                            check)))
        Label(self.results, text=text).grid(column=0, row=i)
        self.runwindow.wait()
        si=xlp.Section(xlpr,text)
        # p=xlp.Paragraph(si,instr)
        font=self.frame.fonts['read']
        self.results.scroll=ScrollingFrame(self.results)
        self.results.scroll.grid(column=0, row=1)
        senseid=0 # in case the following doesn't find anything:
        for group in self.s[self.analang][cvt]:
            log.debug('group: {}'.format(group))
            self.buildregex() #It would be nice fo this to iterate through...
            senseidstocheck=self.senseidformsbyregex(self.regex)
            if len(senseidstocheck)>0:
                id=rx.id('x'+ps+profile+check+group)
                ex=xlp.Example(si,id)
            for senseid in senseidstocheck: #self.senseidformstosearch[lang][ps]
                # where self.regex(self.senseidformstosearch[lang][ps][senseid]):
                """This regex is compiled!"""
                framed=self.datadict.getframeddata(senseid) #not framed!
                o=framed.formatted(noframe=True)
                self.framedtoXLP(framed,parent=ex,listword=True)
                if self.debug ==True:
                    o=entry.lexeme,entry.citation,nn(entry.gloss),
                    nn(entry.gloss2),nn(entry.illustration)
                    print(o)
                def makeimg():
                    img = tkinter.PhotoImage(file = lift_file.liftdirstr()+
                    "/pictures/button.png")
                    if o[4] is not None:
                        img = tkinter.PhotoImage(file = lift_file.liftdirstr()+'/'
                        +o[4])
                        #use this template to add other pictures to GUI.
                    else:
                        img = tkinter.PhotoImage(file = lift_file.liftdirstr()+
                            "/pictures/button.png")
                        #Resizing image to fit on button
                        image = Image.open(img)
                        photoimage = image.resize((34, 26), Image.ANTIALIAS)
                        photo = ImageTk.PhotoImage(image)
                        photoimage = image.subsample(3, 3)
                        tkinter.Button(self.results, width=800, image=photoimage).grid(column=0)
                i+=1
                # b=Button(self.results.scroll.content,
                #         choice=senseid, text=o,
                #         window=self.runwindow.frame,
                #         row=i, column=0, font=font, command=self.picked)
                col=0
                for lang in [self.analang]+self.glosslangs:
                    col+=1
                    if lang in framed.forms:
                        Label(self.results.scroll.content,
                            text=framed.forms[lang], font=font,
                            anchor='w',padx=10).grid(row=i, column=col,
                                                        sticky='w')
                if self.su==True:
                    notok=Button(self.results.scroll.content,
                            choice=senseid, text='X',
                            window=self.runwindow.frame,
                            width=15, row=i,
                            column=1, command=self.notpicked)
        xlpr.close()
        self.runwindow.waitdone()
        if senseid == 0: #i.e., nothing was found above
            print(_('No results!'))
            Label(self.results, text=_("No results for ")+self.regexCV+"!"
                            ).grid(column=0, row=i+1)
            return
    def buildregex(self):
        """include profile (of those available for ps and check),
        and subcheck (e.g., a: CaC\2)."""
        """Provides self.regexCV and self.regex"""
        self.regexCV=None #in case this was run before.
        log.log(2,'profile:',profile)
        log.log(2,'cvt:',cvt)
        maxcount=re.subn(cvt, cvt, profile)[1]
        if profile is None:
            print("It doesn't look like you've picked a syllable profile yet.")
            return
        """Don't need this; only doing count=1 at a time. Let's start with
        the easier ones, with the first occurrance changed."""
        if self.debug is True:
            print('maxcount='+str(maxcount))
            print(check)
        self.regexCV=str(profile) #Let's set this before changing it.
        """One pass for all regexes, S3, then S2, then S1, as needed."""
        cvts=['V','C']
        cvt=self.params.cvt()
        group=self.status.group()
        if 'x' in check:
            if self.subcheckcomparison in self.s[self.analang]['C']:
                cvts=['C','V']
        for t in cvts:
            if t not in cvt:
                continue
            S=str(cvt)
            regexS='[^'+S+']*'+S #This will be a problem if S=NC or CG...
            compared=False
            for occurrence in reversed(range(maxcount)):
                occurrence+=1
                if re.search(S+str(occurrence),check) is not None:
                    """Get the (n=occurrence) S, regardless of intervening
                    non S..."""
                    regS='^('+regexS*(occurrence-1)+'[^'+S+']*)('+S+')'
                    if 'x' in check:
                        if compared == False: #occurrence == 2:
                            replS='\\1'+self.subcheckcomparison
                            compared=True
                        else: #if occurrence == 1:
                            replS='\\1'+group
                    else:
                        replS='\\1'+group
                    self.regexCV=re.sub(regS,replS,self.regexCV, count=1)
        if self.debug ==True:
            print('profile='+str(profile)+str(type(profile)))
            print('cvt='+str(cvt)+str(type(cvt)))
            print('check='+str(check)+str(type(check)))
            print('group='+str(group)+str(type(group)))
            print('self.regexCV='+str(self.regexCV)+str(type(self.regexCV)))
        """Final step: convert the CVx code to regex, and store in self."""
        self.regex=rx.fromCV(self,lang=self.analang,
                            word=True, compile=True)
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
                    cell=xlp.Cell(r,content=linebreakwords(hxcontents),
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
    def tonegroupsjoinrename(self):
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
            for group in groups: #all group variables
                groupsselected+=[group.get()] #value, name if selected, 0 if not
            groupsselected=[x for x in groupsselected if x != '']
            log.info("groupsselected:{}".format(groupsselected))
            if uf in self.toneUFgroups and uf not in groupsselected:
                deja=_("That name is already there! (did you forget to include "
                        "the ‘{}’ group?)".format(uf))
                log.debug(deja)
                errorlabel['text'] = deja
                return
            for group in groupsselected:
                if group in senseidsbygroup: #selected ones only
                    log.debug("Changing values from {} to {} for the following "
                            "senseids: {}".format(group,uf,
                                                    senseidsbygroup[group]))
                    for senseid in senseidsbygroup[group]:
                        self.db.addtoneUF(senseid,uf,analang=self.analang)
            self.db.write()
            self.runwindow.destroy()
            self.tonegroupsjoinrename() #call again, in case needed
        def done():
            self.runwindow.destroy()
        def refreshgroups():
            senseidsbygroup=self.getsenseidsbytoneUFgroups()
        self.getrunwindow()
        title=_("Join/Rename Draft Underlying {}-{} tone groups".format(
                                                        ps,profile))
        self.runwindow.title(title)
        padx=50
        pady=10
        rwrow=gprow=qrow=0
        t=Label(self.runwindow.frame,text=title,font=self.fonts['title'])
        t.grid(row=rwrow,column=0,sticky='ew')
        text=_("This page allows you to join the {0}-{1} draft underlying tone "
                "groups created for you by {2}, \nwhich are almost certainly "
                "too small for you. \nLooking at a draft report, and making "
                "your own judgement about which groups belong together, select "
                "all the groups that belong together, and give that new group "
                "a name. Afterwards, you can do this again for other groups "
                "that should be joined. \nIf for any reason you want to undo "
                "the groups you create here (e.g., you make a mistake or sort "
                "new data), just run the default report, which will redo the "
                "default analysis, which will replace these groupings with new "
                "split groupings. \nTo see a report based on what you do "
                "here, run the tone reports in the Advanced menu (without "
                "analysis). ".format(ps,profile,self.program['name']))
        rwrow+=1
        i=Label(self.runwindow.frame,text=text)
        i.grid(row=rwrow,column=0,sticky='ew')
        rwrow+=1
        qframe=Frame(self.runwindow.frame)
        qframe.grid(row=rwrow,column=0,sticky='ew')
        text=_("What do you want to call this UF tone group for {}-{} words?"
                "".format(ps,profile))
        qrow+=1
        q=Label(qframe,text=text)
        q.grid(row=qrow,column=0,sticky='ew',pady=20)
        named=tkinter.StringVar() #store the new name here
        namefield = EntryField(qframe,textvariable=named)
        namefield.grid(row=qrow,column=1)
        namefield.bind('<Key>', clearerror)
        errorlabel=Label(qframe,text='',fg='red')
        errorlabel.grid(row=qrow,column=2,sticky='ew',pady=20)
        text=_("Select the groups below that you want in this {} group, then "
                "click ==>".format(ps))
        qrow+=1
        d=Label(qframe,text=text)
        d.grid(row=qrow,column=0,sticky='ew',pady=20)
        senseidsbygroup=self.getsenseidsbytoneUFgroups() #dict keyed by group
        sub_btn=Button(qframe,text = _("OK"), command = submitform, anchor ='c')
        sub_btn.grid(row=qrow,column=1,sticky='w')
        done_btn=Button(qframe,text = _("Done —no change"), command = done,
                                                                    anchor ='c')
        done_btn.grid(row=qrow,column=2,sticky='w')
        groups=list()
        rwrow+=1
        scroll=ScrollingFrame(self.runwindow.frame)
        scroll.grid(row=rwrow,column=0,sticky='ew')
        groupvalues=self.tonegroupsbyUFlocation(senseidsbygroup)
        locations=list(dictofchilddicts(groupvalues).keys())
        nheaders=0
        # ufgroups= # order by structured groups? Store this somewhere?
        self.toneUFgroups.sort(key=len)
        for group in self.toneUFgroups: #make a variable and button to select
            idn=self.toneUFgroups.index(group)
            if idn % 5 == 0: #every five rows
                for location in locations:
                    cbh=Label(scroll.content, text=location, font='small')
                    cbh.grid(row=idn+nheaders,
                            column=locations.index(location)+2,sticky='ew')
                nheaders+=1
            groups.append(tkinter.StringVar())
            n=len(senseidsbygroup[group])
            buttontext=group+' ({})'.format(n)
            cb=CheckButton(scroll.content, text = buttontext,
                                variable = groups[idn],
                                onvalue = group, offvalue = 0,
                                )
            cb.grid(row=idn+nheaders,column=0,sticky='ew')
            for location in groupvalues[group]:
                gvalue=unlist(groupvalues[group][location])
                cbl=Label(scroll.content, text=gvalue) #font='small'?
                cbl.grid(row=idn+nheaders,column=locations.index(location)+2,sticky='ew')
        self.runwindow.waitdone()
        self.runwindow.wait_window(scroll)
    def tonegroupsbyUFlocation(self,senseidsbygroup):
        #returns dictionary keyed by [group][location]=groupvalue
        values={}
        self.getlocations()
        locations=self.locations[:]
        # Collect location:value correspondences, by sense
        for group in senseidsbygroup:
            values[group]={}
            for location in locations: #just make them all, delete empty later
                values[group][location]=list()
                for senseid in senseidsbygroup[group]:
                    groupvalue=self.db.get("example/tonefield/form/text",
                                            senseid=senseid, location=location,
                                            ).get('text')
                    if groupvalue != []:
                        if unlist(groupvalue) not in values[group][location]:
                            values[group][location]+=groupvalue
                log.log(3,"values[{}][{}]: {}".format(group,location,
                                                    values[group][location]))
                if values[group][location] == []:
                    log.info(_("Removing empty {} key from {} values"
                                "").format(location,group))
                    del values[group][location] #don't leave key:None pairs
        log.info("Done collecting groups by location for each UF group.")
        return values
    def tonegroupsbysenseidlocation(self):
        #outputs dictionary keyed to [senseid][location]=group
        self.getlocations()
        output={}
        locations=self.locations[:]
        # Collect location:value correspondences, by sense
        for senseid in self.status.senseids():
            output[senseid]={}
            for location in locations:
                group=self.db.get("example/tonefield/form/text",
                    senseid=senseid,location=location,showurl=True).get('text')
                if group != []:
                    output[senseid][location]=group #Save this info by senseid
        log.info("Done collecting groups by location for each senseid.")
        return output
    def groupUFsfromtonegroupsbylocation(self,output):
        # returns groups by location:value correspondences.
        # Look through all the location:value combos (skip over senseids)
        # this is, critically, a dictionary of each location:value
        # correspondence for a given sense. So each groupvalue contains
        # multiple location keys, each with a value value, and the sum of all
        # the location:value correspondences for a sense defines the group
        # --which is distinct from another group which shares some
        # (but not all) of those location:value correspondences.
        # This is the key analytical step that moves us from a collection of
        # surface forms (each pronunciation group in a given context) to the
        # underlying form (which behaves the same as others in its group,
        # across all contexts).
        groups={}
        groupvalues=[]
        # Collect all unique combinations of location:group pairings.
        for value in output.values(): #iterate over all loc:group dictionaries
            if value not in groupvalues: #Just give each once
                groupvalues+=[value]
        log.info("Done collecting combinations of groups values by location.")
        # find the senseids for each set of location:value correspondences.
        x=1 #first group number
        for value in groupvalues:
            group=ps+'_'+profile+'_'+str(x)
            groups[group]={}
            groups[group]['values']=value
            groups[group]['senseids']=[]
            x+=1
        log.info('Groups set up; adding senseids to groups now. ({})'.format(groups.keys()))
        return groups
    def senseidstogroupUFs(self,output,groups):
        for senseid in self.status.senseids():
            for group in groups:
                if str(output[senseid]) == str(groups[group]['values']):
                    groups[group]['senseids']+=[senseid]
                    self.db.addtoneUF(senseid,group,analang=self.analang)
        self.db.write()
        log.info("Done adding senseids to groups.")
        return groups #after filling it out with senseids
    def prioritizegroupUFs(self,groups):
        """Prioritize groups by similarity of location:value pairings"""
        valuesbygroup={}
        #Move values dictionaries up a level, for comparison
        for group in groups:
            valuesbygroup[group]=groups[group]['values']
        return dictscompare(valuesbygroup,ignore=['NA',None],flat=False)
    def prioritizelocations(self,groups,locations):
        """Prioritize locations by similarity of location:value pairings"""
        valuesbylocation={}
        #Move values dictionaries up a level, for comparison
        for location in locations:
            valuesbylocation[location]={}
            for group in groups:
                if location in groups[group]['values']:
                    valuesbylocation[location][group]=groups[group]['values'][
                                                                    location]
        return dictscompare(valuesbylocation,ignore=['NA',None],flat=False)
    def tonegroupreport(self,silent=False,bylocation=False,default=True):
        #default=True redoes the UF analysis (removing any joining/renaming)
        def examplestoXLP(examples,parent,groups=True):
            if not default:
                groups=True #show groups on all non-default reports
            for example in examples:
                framed=self.datadict.getframeddata(example)
                for langs in [self.analang]+self.glosslangs:
                    if framed.forms[lang] is not None: #If all None, don't.
                        self.framedtoXLP(framed,parent=parent,listword=True,
                                                                groups=groups)
                        return
        log.info("Starting report...")
        self.storesettingsfile()
        self.getrunwindow()
        bits=[str(self.reportbasefilename),ps,profile,"ToneReport"]
        if default == False:
            bits.append('mod')
        self.tonereportfile='_'.join(bits)+".txt"
        start_time=time.time()
        """Split here"""
        if default == True:
            #Do the draft UF analysis, from scratch
            output=self.tonegroupsbysenseidlocation() #collect senseid-locations
            if self.locations == []:
                log.error("Hey, sort some morphemes in at least one frame before "
                            "trying to make a tone report!")
                self.runwindow.waitdone()
                return
            groups=self.groupUFsfromtonegroupsbylocation(output) #make groups
            groups=self.senseidstogroupUFs(output,groups) #fillin group senseids
            groupstructuredlist=self.prioritizegroupUFs(groups)
            locationstructuredlist=self.prioritizelocations(groups,
                                                                self.locations)
            grouplist=flatten(groupstructuredlist)
            locations=flatten(locationstructuredlist)
            log.debug("structured locations: {}".format(locationstructuredlist))
            log.debug("structured groups: {}".format(groupstructuredlist))
            toreport={}
            groupvalues={}
            for group in groups:
                toreport[group]=groups[group]['senseids']
                groupvalues[group]={}
                for location in groups[group]['values']: #locations:
                    groupvalues[group][location]=list(groups[group]['values'][
                                                                    location])
        else:
            #make a report without having redone the UF analysis
            #The following line puts out a dictionary keyed by UF group name:
            toreport=self.getsenseidsbytoneUFgroups()
            groupvalues=self.tonegroupsbyUFlocation(toreport)
            grouplist=self.toneUFgroups
            locations=self.locations[:]
        valuesbylocation=dictofchilddicts(groupvalues,remove=['NA',None])
        log.debug("groups (tonegroupreport): {}".format(grouplist))
        log.debug("locations (tonegroupreport): {}".format(locations))
        log.debug("valuesbylocation: {}".format(valuesbylocation))
        r = open(self.tonereportfile, "w", encoding='utf-8')
        title=_("Tone Report")
        self.runwindow.title(title)
        self.runwindow.scroll=ScrollingFrame(self.runwindow.frame)
        self.runwindow.scroll.grid(row=0,column=0)
        window=self.runwindow.scroll.content
        window.row=0
        xlpr=self.xlpstart(reporttype='Tone',bylocation=bylocation,
                                                                default=default)
        s1=xlp.Section(xlpr,title='Introduction')
        text=_("This report follows an analysis of sortings of {} morphemes "
        "(roots or affixes) across the following frames: {}. {} stores these "
        "sortings in lift examples, which are output here, with any glossing "
        "and sound file links found in each lift sense example. "
        "Each group in "
        "this report is distinct from the others, in terms of its grouping "
        "across the multiple frames used. Sound files should be available "
        "through links, if the audio directory with those files is in the same "
        "directory as this file.".format(ps,self.locations,
                                            self.program['name']))
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
            if silent == False:
                Label(window,text=text,font=window.fonts['report']).grid(
                                        row=window.row,column=0, sticky="w")
            window.row+=1
        t=_("Summary of Frames by Draft Underlying Melody")
        if len(locations) > 6:
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
                "".format(self.program['name'],str(groupstructuredlist),
                                                str(locationstructuredlist)))
        else:
            ptext+=_("This is a non-default report, where a user has changed "
            "the default (hyper-split) groups created by {}.".format(
                                                        self.program['name']))
        p0=xlp.Paragraph(s1s,text=ptext)
        m=7 #only this many columns in a table
        for slice in range(int(len(locations)/m)+1):
            locslice=locations[slice*m:(slice+1)*m]
            if len(locslice) >0:
                self.buildXLPtable(s1s,caption+str(slice),yterms=grouplist,
                            xterms=locslice,
                            values=lambda x,y:nn(unlist(groupvalues[y][x],
                                ignore=[None, 'NA'])),
                            ycounts=lambda x:len(toreport[x]),
                            xcounts=lambda y:len(valuesbylocation[y]))
        #Can I break this for multithreading?
        for group in grouplist: #These already include ps-profile
            log.info("building report for {} ({}/{}, n={})".format(group,
                grouplist.index(group)+1,len(grouplist),len(toreport[group])))
            sectitle=_('\n{}'.format(str(group)))
            s1=xlp.Section(xlpr,title=sectitle)
            output(window,r,sectitle)
            l=list()
            for x in groupvalues[group]:
                l.append("{}: {}".format(x,', '.join(groupvalues[group][x])))
            text=_('Values by frame: {}'.format('\t'.join(l)))
            p1=xlp.Paragraph(s1,text)
            output(window,r,text)
            if bylocation == True:
                textout=list()
                for location in groupvalues[group]: #locations:
                    id=rx.id('x'+sectitle+location)
                    headtext='{}: {}'.format(location,', '.join(groupvalues[
                                                            group][location]))
                    e1=xlp.Example(s1,id,heading=headtext)
                    for senseid in toreport[group]:
                        #This is for window/text output only, not in XLP file
                        framed=self.datadict.getframeddata(senseid)
                        text=framed.formatted(noframe=True,notonegroup=True)
                        #This is put in XLP file:
                        examples=self.db.get('example',location=location,
                                                senseid=senseid).get()
                        examplestoXLP(examples,e1,groups=False)
                        if text not in textout:
                            output(window,r,text)
                            textout.append(text)
                    if not e1.node.find('listWord'):
                        s1.node.remove(e1.node) #Don't show examples w/o data
            else:
                for senseid in toreport[group]: #groups[group]['senseids']:
                    #This is for window/text output only, not in XLP file
                    framed=self.datadict.getframeddata(senseid)
                    text=framed.formatted(noframe=True, notonegroup=True)
                    #This is put in XLP file:
                    examples=self.db.get('example',senseid=senseid).get()
                    log.log(2,"{} examples found: {}".format(len(examples),
                                                                    examples))
                    if examples != []:
                        id=self.idXLP(framed)+'_examples'
                        log.log(2,"Using id {}".format(id))
                        headtext=text.replace('\t',' ')
                        e1=xlp.Example(s1,id,heading=headtext)
                        examplestoXLP(examples,e1)
                    output(window,r,text)
        self.runwindow.waitdone()
        xlpr.close()
        text=("Finished in "+str(time.time() - start_time)+" seconds.")
        output(window,r,text)
        text=_("(Report is also available at ("+self.tonereportfile+")")
        output(window,r,text)
        r.close()
    def xlpstart(self,reporttype='adhoc',bylocation=False,default=True):
        if reporttype == 'Tone':
            if bylocation == True:
                reporttype='Tone-bylocation'
        elif not re.search('Basic',reporttype): #We don't want this in the title
            reporttype=str(check)
        reporttype=' '.join([ps,profile,reporttype])
        bits=[str(self.reportbasefilename),rx.id(reporttype),"ReportXLP"]
        if default == False:
            bits.append('mod')
        reportfileXLP='_'.join(bits)+".xml"
        xlpreport=xlp.Report(reportfileXLP,reporttype,
                        self.languagenames[self.analang])
        langsalreadythere=[]
        for lang in [self.analang]+self.glosslangs:
            if lang is not None and lang not in langsalreadythere:
                xlpreport.addlang({'id':lang,'name': self.languagenames[lang]})
                langsalreadythere.append(lang)
        return xlpreport
    def basicreport(self,cvtstodo=['V']):
        """We iterate across these values in this script, so we save current
        values here, and restore them at the end."""
        #Convert to iterate over local variables
        typeori=cvt
        psori=self.slices.ps()
        profileori=self.slices.profile()
        start_time=time.time() #move this to function?
        instr=_("The data in this report is given by most restrictive test "
                "first, followed by less restrictive tests (e.g., V1=V2 "
                "before V1 or V2). Additionally, each word only "
                "appears once per segment in a given position, so a word that "
                "occurs in a more restrictive environment will not appear in "
                "the later less restrictive environments. But where multiple "
                "examples of a segment type occur with different values, e.g., "
                "V1≠V2, those words will appear multiple times, e.g., for "
                "both V1=x and V2=y.")
        self.basicreportfile=''.join([str(self.reportbasefilename)
                                            ,'_',''.join(typestodo)
                                            ,'_BasicReport.txt'])
        xlpr=self.xlpstart(reporttype='Basic '+''.join(typestodo))
        si=xlp.Section(xlpr,"Introduction")
        p=xlp.Paragraph(si,instr)
        sys.stdout = open(self.basicreportfile, "w", encoding='utf-8')
        print(instr)
        log.info(instr)
        #There is no runwindow here...
        self.parent.waitdone() #non-widget parent deiconifies no window...
        self.basicreported={}
        self.checkcounts={}
        self.printprofilesbyps()
        self.printcountssorted()
        t=_("This report covers the following top two Grammatical categories, "
            "with the top {} syllable profiles in each. "
            "This is of course configurable, but I assume you don't want "
            "everything.".format(self.maxprofiles))
        log.info(t)
        print(t)
        p=xlp.Paragraph(si,t)
        for ps in self.pss[0:2]: #just the first two (Noun and Verb)
            if ps not in self.checkcounts:
                self.checkcounts[ps]={}
            profiles=self.slices.profiles()
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
                if profile not in self.checkcounts[ps]:
                    self.checkcounts[ps][profile]={}
                t=_("{} {}s".format(profile,ps))
                s2=xlp.Section(s1,t,level=2)
                print(t)
                log.info(t)
                for cvt in typestodo:
                    t=_("{} checks".format(self.params.typedict()[cvt]['sg']))
                    print(t)
                    log.info(t)
                    sid=" ".join([t,"for",profile,ps+'s'])
                    s3=xlp.Section(s2,sid,level=3)
                    maxcount=re.subn(cvt, cvt, profile)[1]
                    """Get these reports from C1/V1 to total number of C/V"""
                    self.typenums=[cvt+str(n+1) for n in range(maxcount)]
                    for typenum in self.typenums:
                        if typenum not in self.basicreported:
                            self.basicreported[typenum]=set()
                    self.wordsbypsprofilechecksubcheck(s3)
        t=_("Summary coocurrence tables")
        s1s=xlp.Section(xlpr,t)
        for ps in self.checkcounts:
            s2s=xlp.Section(s1s,ps,level=2)
            for profile in self.checkcounts[ps]:
                s3s=xlp.Section(s2s,' '.join([ps,profile]),level=3)
                for name in self.checkcounts[ps][profile]:
                    rows=list(self.checkcounts[ps][profile][name])
                    nrows=len(rows)
                    if nrows == 0:
                        continue
                    if 'x' in name:
                        cols=list(self.checkcounts[ps][profile][name][rows[0]])
                    else:
                        cols=['n']
                    ncols=len(cols)
                    if ncols == 0:
                        continue
                    caption=' '.join([ps,profile,name])
                    t=xlp.Table(s3s,caption)
                    for x1 in ['header']+list(range(nrows)):
                        if x1 != 'header':
                            x1=rows[x1]
                        h=xlp.Row(t)
                        for x2 in ['header']+list(range(ncols)):
                            log.debug("x1: {}; x2: {}".format(x1,x2))
                            if x2 != 'header':
                                x2=cols[x2]
                            log.debug("x1: {}; x2: {}".format(x1,x2))
                            log.debug("countbyname: {}".format(self.checkcounts[
                                    ps][profile][name]))
                            if x1 != 'header' and x2 not in ['header','n']:
                                log.debug("value: {}".format(self.checkcounts[
                                    ps][profile][name][x1][x2]))
                            if x1 == 'header' and x2 == 'header':
                                log.debug("header corner")
                                cell=xlp.Cell(h,content=name,header=True)
                            elif x1 == 'header':
                                log.debug("header row")
                                cell=xlp.Cell(h,content=x2,header=True)
                            elif x2 == 'header':
                                log.debug("header column")
                                cell=xlp.Cell(h,content=x1,header=True)
                            else:
                                log.debug("Not a header")
                                if x2 == 'n':
                                    value=self.checkcounts[ps][
                                                    profile][name][x1]
                                else:
                                    value=self.checkcounts[ps][
                                                    profile][name][x1][x2]
                                cell=xlp.Cell(h,content=value)
        log.info(self.checkcounts)
        xlpr.close()
        log.info("Finished in {} seconds.".format(str(time.time()-start_time)))
        sys.stdout.close()
        sys.stdout=sys.__stdout__ #In case we want to not crash afterwards...:-)
        self.frame.parent.waitdone()
        self.type=typeori
    """These are old paradigm CV funcs, with too many arguments, and guids"""
    def picked(self,choice,**kwargs):
        return
        if self.debug == True:
            print(entry.__dict__)
        entry.addresult(check, result='OK') #let's not translate this...
        debug()
        window=Window(parent, title='Same! '+entry.lexeme+': '
                        +entry.guid)
        result=(entry.citation,nn(entry.plural),nn(entry.imperative),
                    nn(entry.ps),nn(entry.gloss))
        tkinter.Button(window.frame, width=80, text=result,
            command=window.destroy).grid(column=0, row=0)
        window.exitButton=''
    def notpicked(self,choice):
        """I should think through what I want for this button/script."""
        if entry is None:
            log.info("No entry!")
            """Probably a bad idea"""
            entry=Entry(db, parent, window, check, guid=choice)
        if self.debug==True:
            print(entry.__dict__)
        entry.addresult(check, result='NOTok')
        window=Window(parent, title='notpicked: Different! '
                        +entry.lexeme+': '+entry.guid)
        result=entry.citation,nn(entry.plural),nn(entry.imperative),nn(entry.ps),
        nn(entry.gloss)
        Label(window.frame, width=40, text=result).grid(row=0,column=0)
        q=(_("What is wrong with this word?"))
        Label(window.frame, text=q).grid(column=0, row=1)
        if check.name == "V1=V2":
            bcv1nv2=(_("Two different vowels (V1≠V2)"))
            bscv1isv2nsc=(_("Vowels are the same, but the wrong vowel"))
            problemopts=[("badCheck",bcv1nv2),
                ("badSubcheck",bscv1isv2nsc+" (V1=V2≠"+check.subcheck+")")]
        else:
            log.info("Sorry, that check isn't set up yet.")
        buttonFrame1=ButtonFrame(window.frame,window,check,entry,list=problemopts,
                                    command=Check.fixdiff,width="50")
        buttonFrame1.grid(column=0, row=3)
        i=4 #start at this row
        print(result)
    def fixV12(parent, window, check, entry, choice):
        """This and following scripts represent a structure of the program
        which is way more complex than we want. We have to think through how
        to organize the functions and windows in such a way as the UI is
        straightforward and completely unconfusing."""
        window.title=(_("TITLE!"))
        Label(window.frame, text=entry.citation+' - '+entry.gloss,
                        anchor=tkinter.W).grid(column=0, row=0, columnspan=2)
        q1=_("It looks like the vowels are the same, but not the correct vowel;"
            " let's fix that.")
        Label(window.frame, text=q1,anchor=tkinter.W).grid(column=0, row=2,
                                                                columnspan=2)
        q2=_("What are the two vowels?")
        Label(window.frame, text=q2,anchor=tkinter.W).grid(column=0, row=3,
                                                                columnspan=1)
        ButtonFrame1=ButtonFrame(window.frame,window,check,entry,
                                list=check.db.vowels(),command=Check.fixVs)
        ButtonFrame1.grid(column=0, row=4)
    def fixV1(parent, window, check, entry, choice):
        t=(_('fixV1:Different data to be fixed! '))+entry.lexeme+': '+entry.guid
        print(t)
        check.fix='V1'
        #window.destroy()
        #window=Window(self.frame,, title=t, entry=entry, backcmd=fixdiff)
        window.resetframe()
        t2=(_("It looks like the vowels aren't the same; let's fix that."))
        Label(window.frame, text=t2, justify=tkinter.LEFT).grid(column=0,
                                                                    row=0,
                                                                columnspan=2)
        t3=(_("What is the first vowel? (C_CV)"))
        Label(window.frame, text=t3, anchor=tkinter.W).grid(column=0,
                                                                row=1,
                                                                columnspan=1)
        ButtonFrame1=ButtonFrame(window.frame,window,check,entry,
                                list=check.db.vowels(),command=Check.newform)
        ButtonFrame1.grid(column=0, row=2)
    def fixV2(parent, window, check, entry, choice):
        check.fix='V2'
        t=(_('fixV2:Different data to be fixed! '))+entry.lexeme+': '+entry.guid
        t=(_("What is the second vowel?"))
        Label(window.frame, text=t,justify=tkinter.LEFT).grid(column=0, row=1, columnspan=1)
        ButtonFrame1=ButtonFrame(window.frame,window,check,entry,
                                    list=check.db.vowels(),command=Check.newform)
        ButtonFrame1.grid(column=0, row=2)
    def fixdiff(parent, window, check, entry, choice):
        """We need to fix problems in a more intuitively obvious way"""
        entry.problem=choice
        entry.addresult(check, result=entry.problem)
        if self.debug==True:
            print(entry.__dict__)
        window.destroy()
        window=Window(self.frame.parent, entry=entry, backcmd=notpickedback)
        Label(window, text="Let's fix those problems").grid(column=0, row=0)
        if entry.problem == "badCheck": #This isn't the right check for this entry --re.search("V1≠V2",difference):
            window.destroy()
            t=(_("fixVs:Different vowels! "))+entry.lexeme+': '+entry.guid
            window=Window(self.frame, title=t, entry=entry, backcmd=Check.fixdiff)
            Check.fixV1(parent, window, check, entry, choice)
            window.wait_window(window=window)
            window=Window(self.frame, title=t, entry=entry, backcmd=Check.fixdiff)
            Check.fixV2(parent, window, check, entry, choice) #I should make this wait until the first one finishes..…
            window.wait_window(window=window)
            window=Window(self.frame, title=t, entry=entry, backcmd=Check.fixdiff)
            Check.fixVs(parent, window, check, entry, choice)
        elif entry.problem == "badSubcheck": #This isn't the right subcheck for this entry --re.search("V1=V2≠"+Vo,difference): #
            window.destroy()
            t=(_("fixVs:Same Vowel, but wrong one! "))+entry.lexeme+': '+entry.guid
            window=Window(self.frame, title=t, entry=entry, backcmd=Check.fixdiff)
            Check.fixV12(parent, window, check, entry, choice)
        else:
            log.info("Huh? I don't understand what the user wants.")
        Check.fixVs
    def fixVs(parent, window, check, entry, choice):
        #This isn't working yet.
        log.info("running fixVs!!!!???!??!?!?!?")

        #I need to rework this to work more generally..….
        Label(window.frame, text="I will make the following changes:").grid(column=0, row=0)
        lexemeNew=entry.newform #newform(entry.lexeme,'v12',check.subcheck,choice)
        citationNew = re.sub(entry.lexeme, lexemeNew, entry.citation)
        Label(window.frame, text="citation: "+entry.citation+" → "+citationNew).grid(column=0, row=1)
        Label(window.frame, text="lexeme: "+entry.lexeme+" → "+lexemeNew).grid(column=0, row=2)
        fields={}
        if entry.plural is not None:
            pluralNew = re.sub(entry.lexeme, lexemeNew, entry.plural)
            Label(window.frame, text="plural: "+plural+" → "+pluralNew).grid(column=0, row=3)
            fields={'Plural'}
        if entry.imperative is not None:
            imperativeNew = re.sub(entry.lexeme, lexemeNew, entry.imperative)
            Label(window.frame, text="imperative: "+entry.imperative+" → "+imperativeNew).grid(column=0, row=4)
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
        tkinter.Button(window, width=10, text="OK", command=ok).grid(row=1,column=0)
        #This is where we should call addresult, and write to file.
        tkinter.Button(window, width=15, text="Not OK (Go Back)", command=notok).grid(row=1,column=1)
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
        entry.newform=re.sub(r, sub, baseform)
        print('newform: '+entry.newform)
        def old2():
            for x in baseform:
                if self.debug==True:
                    print("exchanging "+check.subcheck+" for "+choice)
                    print(ximin,xi,ximax)
                    if x == check.subcheck:
                        log.info("x == check.subcheck")
                    if xi >= ximin and xi <= ximax:
                        log.info("xi >= ximin  and xi <= ximax") # <= ximax ):
                    if ximin <= xi:
                        log.info("ximin <= xi") # <= ximax ):
                    if xi <= ximax:
                        log.info("xi <= ximax") # <= ximax ):
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
        if self.debug==True:
            print (str(len(self.checkresults))+': '+str(self.checkresults))
            print (str(len(self.checkresults[check.name]))+': '
                +str(self.checkresults[check.name]))
            print (str(len(self.checkresults[check.name][check.subcheck]))
                +': '+str(self.checkresults[check.name][check.subcheck]))
            print (str(len(self.checkresults))+': '+str(self.checkresults))
            print(self.checkresults)
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
    def appendformsbylang(self,forms,langs,quote=False):
        for l in [f for f in forms if f in langs]:
            if quote:
                self.append("‘"+forms[l]+"’")
            else:
                self.append(forms[l])
    def __init__(self, *args):
        super(DataList, self).__init__()
        self.extend(args)
class Glosslangs(DataList):
    """docstring for Glosslangs."""
    def lang1(self,lang=None):
        if lang is None:
            return self[0]
        if len(self) > 1 and self[1] == lang: #don't have same language twice
            self.pop(1)
        if len(self) > 0:
            self[0]=lang
        else:
            self.append(lang)
    def lang2(self,lang=None):
        if lang is None and len(self) >1:
            return self[1]
        if len(self) > 1 and self[0] != lang:
            self[1]=lang
        if len(self) == 1:
            self.append(lang)
        else:
            log.debug("Tried to set second glosslang, without first set.")
    def langs(self,langs=None):
        if langs is None:
            return self
        else:
            while len(langs) >=2 and langs[0] == langs[1]:
                del langs[1]
            self.clear()
            self.append(langs[:2])
    def rm(self,lang):
        """This could be either position, and if lang1 will promote lang2"""
        self.remove(lang)
    def __init__(self, *args):
        super(Glosslangs, self).__init__()
        self.extend(args)
class DictbyLang(dict):
    """docstring for DictbyLang."""
    def getformfromnode(self,node,truncate=False):
        #this assumes *one* value/lang, a second will overwrite.
        #this will comma separate text nodes, if there are multiple text nodes.
        if isinstance(node,lift.ET.Element):
            lang=node.get('lang')
            if truncate: #this gives up to three words, no parens
                text=rx.glossifydefn(unlist(node.findall('text')))
            else:
                text=unlist(node.findall('text'))
            log.info("Adding {} to {} dict under {}".format(t(text),self,lang))
            self[lang]=text
        else:
            log.info("Not an element node: {} ({})".format(node,type(node)))
            log.info("node.stripped: {} ({})".format(node.strip(),len(node)))
    def frame(self,framedict,langs): #langs can/should be ordered
        """the frame only applies if there is a language value; I hope that's
        what we want..."""
        log.info("Applying frame {} in these langs: {}".format(framedict,langs))
        log.info("Using regex {}".format(rx.framerx))
        for l in [i for i in langs if i in framedict if i in self and self[i] != []]:
            log.info("Using lang {}".format(l))
            if self[l] is not None:
                self.framed[l]=rx.framerx.sub(self[l],framedict[l])
            else:
                self.framed[l]=None
        log.info("Applied frame: {}".format(self.framed))
    def __init__(self):
        super(DictbyLang, self).__init__()
        self.framed={}
class ExampleDict(dict):
    def senseidsinslicegroup(self,group):
        #This returns all the senseids with a given tone value
        check=self.params.check()
        senseids=self.db.get("sense", location=check, path=['tonefield'],
                            tonevalue=group
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
        else:
            self._outdict['audiofileisthere']=False
        return self._outdict['audiofileisthere']
    def exampletypeok(self,senseid,**kwargs):
        kwargs=exampletype(**kwargs)
        if senseid is None:
            return
        framed=self.frame(senseid)
        log.info("exampletypeok framed: {}".format(framed))
        # framed=self.datadict.getframeddata(senseid)
        if kwargs['wglosses'] and not self.hasglosses(framed):
            log.info("Gloss check failed for {}".format(senseid))
            return
        if kwargs['wsoundfile'] and not self.hassoundfile(framed):
            log.info("Audio file check failed for {}".format(senseid))
            return
        self._outdict['senseid']=senseid
    def frame(self,senseid):
        return self.datadict.getframeddata(senseid)
    def getexample(self,group,**kwargs):
        # exampletype(**kwargs) #needed?
        # wglosses=False,wsoundfile=False): #truncdefn=False, notonegroup=True,
        """This function finds examples in the lexicon for a given tone value,
        in a given tone frame (from check)"""
        senseids=self.senseidsinslicegroup(group)
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
        while not self.exampletypeok(senseid,**kwargs) and tries<n*2:
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
                    else:
                        log.info("Using next value for ‘{}’ group: ‘{}’"
                                "".format(group, self[group]))
                        i=senseids.index(self[group])
                        if i == len(senseids)-1: #loop back on last
                            senseid=senseids[0]
                        else:
                            senseid=senseids[i+1]
                else:
                    senseid=senseids[randint(0, len(senseids))-1]
            elif n == 1:
                senseid=senseids[0]
            else:
                log.debug("n: {}".format(n))
                senseid=senseids[randint(0, n-1)]
        if senseid is None: #not self.hasglosses(senseid):
            log.info("Apparently I tried for a senseid {} times, and couldn't "
            "find one matching your needs ({}) glosses (out of {} possible "
            "senses). This is probably a systematic problem to fix.".format(
                                                                tries,kwargs,n))
        else:
            self._outdict['senseid']=senseid
            self[group]=senseid #save for next time
            return self._outdict
    def __init__(self,params,slices,db,datadict):
        self.params=params
        self.slices=slices
        self.db=db
        self.datadict=datadict
        super(ExampleDict, self).__init__()
class FramedDataDict(dict):
    def updatelangs(self):
        self.analang=self.check.analang
        self.glosslangs=self.check.glosslangs
        log.debug("analang: {}; glosslangs: {}".format(self.analang,self.glosslangs))
    def getframeddata(self, source, **kwargs):
        self.updatelangs()
        if source not in self:
            log.debug("source {} not there, making...".format(source))
            self[source]=FramedData(self,source,**kwargs)
        else:
            log.debug("source {} alread there, using...".format(source))
            self[source].updatelangs()
        return self[source]
    def __init__(self, check, **kwargs):
        super(FramedDataDict, self).__init__()
        self.frames=check.toneframes #[ps][name]
        self.db=check.db
        self.check=check
class FramedData(object):
    """This populates an object with attributes to format data for display,
    by senseid"""
    """Sometimes this script is called to make the example fields, other
    times to display it. If source is a senseid, it pulls form/gloss/etc
    information from the entry. If source is an example, it pulls that info
    from the example. The info is formatted uniformly in either case."""
    def formatted(self,notonegroup=True,noframe=False):
        if notonegroup:
            toformat=DataList()
        else:
            toformat=DataList(self.tonegroup)
        if noframe:
            toformat.appendformsbylang(self.forms,self.analang,quote=False)
            toformat.appendformsbylang(self.forms,self.glosslangs,quote=True)
        else:
            if not hasattr(self,'framed'):
                self.applyframe() #self.noframe() #Assume no frame if not excplicitly applied
            toformat.appendformsbylang(self.framed,self.analang,quote=False)
            toformat.appendformsbylang(self.framed,self.glosslangs,quote=True)
        return ' '.join(toformat) #put it all together
    def setframe(self,frame):
        """This should never be done on an example, which should
        already be framed. Also, self.ps won't be defined, so you'll get
        a key error."""
        if hasattr(self, 'ps') and frame is not None:
            self.frame=self.frames[self.ps][frame]
            self.applyframe()
        else:
            self.applynoframe() #enforce the docstring above
    def applynoframe(self):
        self.framed=self.forms
    def applyframe(self):
        log.info("setframe::")
        if not self._noframe and hasattr(self,'frame'):
            self.forms.frame(self.frame,[self.analang]+self.glosslangs)
            self.framed=self.forms.framed
            log.info("setframe framed: {}".format(self.forms.framed))
        else:
            self.applynoframe()
    def gettonegroup(self):
        """This is only done by parsesense. parseexample gets it otherwise."""
        if None not in [self.location,self.senseid]:
            self.tonegroups=self.db.get('example/tonefield/form/text',
                            senseid=senseid, location=self.location).get('text')
    def tonegroup(self):
        if self.tonegroups is not None: # wanted&found
            tonegroup=unlist(self.tonegroups)
            if tonegroup is not None:
                try:
                    int(tonegroup)
                except:
                    self.tonegroup=tonegroup #only for named groups
    def parsesense(self,db,senseid):
        self.senseid=senseid
        self.ps=unlist(db.ps(senseid=senseid)) #there should be just one
        self.forms[self.analang]=db.citationorlexeme(senseid=senseid,
                                                    analang=self.analang)
        self.forms.update(db.glossesordefns(senseid=senseid))
        for f in self.forms:
            self.forms[f]=unlist(self.forms[f])
        self.gettonegroup()
    def parseexample(self,example):
        self.senseid=None #We don't have access to this here
        for i in example:
            if i.tag == 'form': #language forms, not glosses, etc, below.
                self.forms.getformfromnode(i)
            elif (((i.tag == 'translation') and
                (i.get('type') == 'Frame translation')) or
                ((i.tag == 'gloss'))):
                for ii in i:
                    if (ii.tag == 'form'):
                        self.forms.getformfromnode(ii) #glosses
            elif ((i.tag == 'field') and (i.get('type') == 'tone')):
                self.tonegroups=i.findall('form/text') #always be list of one
    def glosses(self):
        g=DictbyLang()
        l=0
        for lang in self.glosslangs:
            if lang in self.forms:
                g[lang]=self.forms[lang]
                if g[lang] is not None:
                    l+=len(g[lang])
        if l >0:
            return g
        else:
            return None
    def updatelangs(self):
        self.analang=self.parent.analang
        self.glosslangs=self.parent.glosslangs
        log.debug("analang: {}; glosslangs: {}".format(self.analang,self.glosslangs))
    def __init__(self, parent, source, **kwargs):
        super(FramedData, self).__init__()
        self.parent=parent
        self.frames=parent.frames
        self.updatelangs()
        self.db=parent.db #kwargs.pop('db',None) #not needed for examples
        self.location=kwargs.pop('location',None) #not needed for noframe
        self._noframe=kwargs.pop('noframe',False)
        """Generalize these, and manage with methods:"""
        # self.notonegroup=kwargs.pop('notonegroup',False)
        # truncdefn=kwargs.pop('truncdefn',False)
        # self.frame=kwargs.pop('frame',None) #not needed for noframe
        #These really must be there, and ordered with first first
        #to put data:
        self.forms=DictbyLang()
        #defaults to set upfront
        self.tonegroups=None
        self.tonegroup=None
        self.senseid=None
        """Build dual logic here. We use this to frame senses & examples"""
        if isinstance(source,lift.ET.Element):
            self._noframe=True #Examples should already be framed
            self.parseexample(source) #example element, not sense or entry:
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
        elif type(source) is str and len(source) >= 36:#senseid can be guid+form
            self.parsesense(self.db,source)
        else:
            log.error('Neither Element nor senseid was found!'
                        '\nThis is almost certainly not what you want!'
                        '\nFYI, I was looking for {}'.format(source))
            return source
        log.info("FramedData initalization done.")
        log.info("FramedData forms: {}".format(self.forms))
        # log.info("FramedData framed: {}".format(self.framed))
        """The following is the same for senses or examples"""
class ExitFlag(object):
    def istrue(self):
        # log.debug("Returning {} exitflag".format(self.value))
        return self.value
    value=get=istrue
    def true(self):
        self.value=True
    def false(self):
        self.value=False
    def __init__(self):
        self.false()
class Window(tkinter.Toplevel):
    def resetframe(self):
        if self.parent.exitFlag.istrue():
            return
        if self.winfo_exists(): #If this has been destroyed, don't bother.
            if hasattr(self,'frame') and type(self.frame) is Frame:
                self.frame.destroy()
            self.frame=Frame(self.outsideframe)
            self.frame.grid(column=0,row=0,sticky='nsew')
    def wait(self,msg=None):
        if hasattr(self,'ww') and self.ww.winfo_exists() == True:
            log.debug("There is already a wait window: {}".format(self.ww))
            return
        self.ww=Wait(self,msg)
    def waitdone(self):
        # if self.exitFlag.istrue():
        #     return
        # else:
        #     print(self.exitFlag.istrue())
        # if hasattr(self,'ww') and self.ww.winfo_exists():
        try:
            self.ww.close()
        except tkinter.TclError:
            pass
    def removeverifymenu(self,event=None):
        #This removes menu from the verify window
        if hasattr(self,'menubar'):
            self.menubar.destroy()
            self.parent.verifymenu=False
            self.setcontext(context='verifyT')
            return True #i.e., removed, to maybe replace later
    # def doverifymenu(self):
    #     #This adds a menu to the verify window
    #     log.debug("Trying self.menubar")
    #     self.menubar = Menu(self, tearoff=0)
    #     log.debug("Done self.menubar")
    #     # This points to check via the window's parent (check.frame) and its
    #     # parent, the MainApplication, which has a check attribute...
    #     self.menubar.add_command(label=_("Rename Group"),
    #         command=lambda c=self.parent.parent.check,v=True:Check.renamegroup(
    #                 c,reverify=True))
    #     self.config(menu=self.menubar)
    #     self.parent.verifymenu=True
    #     self.setcontext(context='verifyT')
    # def setcontext(self,context=None): #set context for different windows
    #     # This is called by contextMenu(), & maybe other things context changers
    #     if not hasattr(self, 'context') or type(self.context) != ContextMenu:
    #         log.info("There isn't a context menu, so not setting the context.")
    #         return
    #     self.context.menuinit() #This is a ContextMenu() method
    #     if context == 'verifyT': #parameter, NOT self.context, menu object...
    #         if ((not hasattr(self.parent,'verifymenu')) or
    #                 (self.parent.verifymenu == False)):
    #             self.context.menuitem(_("Show Menu"),self.doverifymenu)
    #         else:
    #             self.context.menuitem(_("Hide Menu"),self.removeverifymenu)
    def __init__(self, parent, backcmd=False, exit=True, title="No Title Yet!",
                choice=None, *args, **kwargs):
        self.parent=parent
        inherit(self)
        """Things requiring tkinter.Window below here"""
        super(Window, self).__init__()
        # super(Window, self).__init__(class_="AZT")
        # self.config(className="azt")
        self['background']=self.theme['background']
        """Is this section necessary for centering on resize?"""
        for rc in [0,2]:
            self.grid_rowconfigure(rc, weight=3)
            self.grid_columnconfigure(rc, weight=3)
        self.photo = parent.photo #need this before making the frame
        # self.photowhite = parent.photowhite #this, too.
        self.outsideframe=Frame(self)
        """Give windows some margin"""
        self.outsideframe['padx']=25
        self.outsideframe['pady']=25
        self.outsideframe.grid(row=1, column=1,sticky='we')
        parentname=name(parent)
        selfname=name(self)
        if self.debug==True:
            log.info("Current window:")
            print(parent)
            print(window)
            print ("    parent.name: "+parentname)
            print ("    check: "+selfname)
            log.info("End current window descriptions")
        self.iconphoto(False, self.photo['icon']) #don't want this transparent
        self.title(title)
        # self.parent=parent
        self.resetframe()
        self.exitFlag=ExitFlag() #This overwrites inherited exitFlag
        setexitflag(self,self.exitFlag)
        if exit is True:
            e=(_("Exit")) #This should be the class, right?
            self.exitButton=tkinter.Button(self.outsideframe, width=10, text=e,
                                command=lambda s=self:on_quit(s),
                                activebackground=self.theme['activebackground'],
                                background=self['background']
                                            )
            self.exitButton.grid(column=2,row=2)
        if backcmd is not False: #This one, too...
            b=(_("Back"))
            cmd=lambda:backcmd(parent, window, check, entry, choice)
            self.backButton=tkinter.Button(self.outsideframe, width=10, text=b,
                                command=cmd,
                                activebackground=self.theme['activebackground'],
                                background=self.theme['background']
                                            )
            self.backButton.grid(column=3,row=2)
class Menu(tkinter.Menu):
    def pad(self,label):
        w=5 #Make menus at least w characters wide
        if len(label) <w:
            spaces=" "*(w-len(label))
            label=spaces+label+spaces
        return label
    def add_command(self,label,command):
        label=self.pad(label)
        tkinter.Menu.add_command(self,label=label,command=command)
    def add_cascade(self,label,menu):
        label=self.pad(label)
        tkinter.Menu.add_cascade(self,label=label,menu=menu)
    def __init__(self,parent,**kwargs):
        super().__init__(parent,**kwargs)
        self.parent=parent
        inherit(self)
        self['font']=self.fonts['default']
        #Blend with other widgets:
        # self['activebackground']=self.theme['activebackground']
        # self['background']=self.theme['background']
        # stand out from other widgets:
        self['activebackground']=self.theme['background']
        self['background']='white'
class MainApplication(Frame):
    def wait(self,msg=None):
        # This and the following are only to build the main screen
        if hasattr(self.parent,'ww') and self.parent.ww.winfo_exists() == True:
            log.debug("Already a wait window: {}".format(self.parent.ww))
            return
        self.parent.ww=Wait(self.parent,msg)
    def waitdone(self):
        log.log(3,"Closing Wait window, and bringing up main window again.")
        if hasattr(self.parent,'ww'):
            self.parent.ww.close()
    def fullscreen(self):
        w, h = self.parent.winfo_screenwidth(), self.parent.winfo_screenheight()
        self.parent.geometry("%dx%d+0+0" % (w, h))
    def quarterscreen(self):
        w, h = self.parent.winfo_screenwidth(), self.parent.winfo_screenheight()
        w=w/2
        h=h/2
        self.parent.geometry("%dx%d+0+0" % (w, h))
    def _showbuttons(self,event=None):
        self.check.mainlabelrelief(relief='flat',refresh=True)
        self.setcontext()
    def _hidebuttons(self,event=None):
        self.check.mainlabelrelief(relief=None,refresh=True)
        self.setcontext()
    def _removemenus(self,event=None):
        if hasattr(self,'menubar'):
            self.menubar.destroy()
            self.menu=False
            self.setcontext()
    def _setmenus(self,event=None):
        check=self.check
        self.menubar = Menu(self.parent)
        changemenu = Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label=_("Change"), menu=changemenu)
        """Language stuff"""
        languagemenu = Menu(changemenu, tearoff=0)
        changemenu.add_cascade(label=_("Languages"), menu=languagemenu)
        languagemenu.add_command(label=_("Interface/computer language"),
                        command=lambda x=check:Check.getinterfacelang(x))
        languagemenu.add_command(label=_("Analysis language"),
                        command=lambda x=check:Check.getanalang(x))
        languagemenu.add_command(label=_("Analysis language Name"),
                        command=lambda x=check:Check.getanalangname(x))
        languagemenu.add_command(label=_("Gloss language"),
                        command=lambda x=check:Check.getglosslang(x))
        languagemenu.add_command(label=_("Another gloss language"),
                        command=lambda x=check:Check.getglosslang2(x))
        """Word/data choice stuff"""
        changemenu.add_command(label=_("Part of speech"),
                        command=lambda x=check:Check.getps(x))
        changemenu.add_command(label=_("Consonant-Vowel-Tone"),
                        command=lambda x=check:Check.getcvt(x))
        profilemenu = Menu(changemenu, tearoff=0)
        changemenu.add_cascade(label=_("Syllable profile"), menu=profilemenu)
        profilemenu.add_command(label=_("Next"),
                        command=lambda x=check:Check.nextprofile(x))
        profilemenu.add_command(label=_("Choose"),
                        command=lambda x=check:Check.getprofile(x))
        """What to check stuff"""
        cvt=check.params.cvt()
        ps=check.slices.ps()
        profile=check.slices.profile()
        if None not in [ps, profile, cvt]:
            if cvt == 'T':
                changemenu.add_separator()
                framemenu = Menu(changemenu, tearoff=0)
                changemenu.add_cascade(label=_("Tone Frame"), menu=framemenu)
                framemenu.add_command(label=_("Next"),
                        command=lambda x=check.status:StatusDict.nextcheck(x))
                framemenu.add_command(label=_("Next to sort"),
                        command=lambda x=check.status:StatusDict.nextcheck(x,
                                                                tosort=True))
                framemenu.add_command(label=_("Next with data already sorted"),
                        command=lambda x=check.status:StatusDict.nextcheck(x,
                                                                wsorted=True))
                framemenu.add_command(label=_("Choose"),
                                command=lambda x=check:Check.getcheck(x))
            else:
                changemenu.add_separator()
                changemenu.add_command(label=_("Location in word"),
                        command=lambda x=check:Check.getcheck(x))
                if check.check is not None:
                    changemenu.add_command(label=_("Segment(s) to check"),
                        command=lambda x=check:Check.getgroup(x,tosort=True)) #any
        """Do"""
        domenu = Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label=_("Do"), menu=domenu)
        reportmenu = Menu(self.menubar, tearoff=0)
        reportmenu.add_command(label=_("Tone by sense"),
                        command=lambda x=check:Check.tonegroupreport(x))
        reportmenu.add_command(label=_("Tone by location"
                        ),command=lambda x=check:Check.tonegroupreport(x,
                                                            bylocation=True))
        reportmenu.add_command(label=_("Basic Vowel report (to file)"),
                        command=lambda x=check:Check.basicreport(x,cvtstodo=['V']))
        reportmenu.add_command(label=_("Basic Consonant report (to file)"),
                        command=lambda x=check:Check.basicreport(x,cvtstodo=['C']))
        reportmenu.add_command(label=_("Basic report on Consonants and Vowels "
                                                                "(to file)"),
                command=lambda x=check:Check.basicreport(x,cvtstodo=['C','V']))
        domenu.add_cascade(label=_("Reports"), menu=reportmenu)
        recordmenu = Menu(self.menubar, tearoff=0)
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
                        command=lambda x=check:Check.joinT(x))
        """Advanced"""
        advancedmenu = Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label=_("Advanced"), menu=advancedmenu)
        filemenu = Menu(self.menubar, tearoff=0)
        filemenu.add_command(label=_("Dictionary Morpheme"),
                        command=lambda x=check:Check.addmorpheme(x))
        advancedmenu.add_command(label=_("Add Tone frame"),
                        command=lambda x=check:Check.addframe(x))
        advancedmenu.add_command(label=_("Transcribe/(re)name Framed Tone Group"),
                                command=lambda x=check:Check.renamegroup(x))
        advtonemenu = Menu(self.menubar, tearoff=0)
        advancedmenu.add_cascade(label=_("Tone Reports"), menu=advtonemenu)
        advtonemenu.add_command(label=_("Name/join UF Tone Groups"),
                        command=lambda x=check:Check.tonegroupsjoinrename(x))
        advtonemenu.add_command(label=_("Custom groups by sense"),
                                command=lambda x=check:Check.tonegroupreport(x,
                                                                default=False))
        advtonemenu.add_command(label=_("Custom groups by location"),
                                command=lambda x=check:Check.tonegroupreport(x,
                                                bylocation=True, default=False))
        redomenu = Menu(self.menubar, tearoff=0)
        redomenu.add_command(label=_("Previously skipped data"),
                                command=lambda x=check:Check.tryNAgain(x))
        advancedmenu.add_cascade(label=_("Redo"), menu=redomenu)
        advancedmenu.add_cascade(label=_("Add other"), menu=filemenu)
        redomenu.add_command(
                        label=_("Verification of current framed group"),
                        command=lambda x=check:Check.reverify(x))
        redomenu.add_command(
                        label=_("Digraph and Trigraph settings (Restart)"),
                        command=lambda x=check:Check.askaboutpolygraphs(x))
        redomenu.add_command(
                        label=_("Syllable Profile Analysis (Restart)"),
                        command=lambda x=check:Check.reloadprofiledata(x))
        redomenu.add_command(
                        label=_("Change to another Database (Restart)"),
                        command=lambda x=check:Check.changedatabase(x))
        redomenu.add_command(
                        label=_("Verification Status file (several minutes)"),
                        command=lambda x=check:Check.reloadstatusdata(x))
        advancedmenu.add_command(
                        label=_("Segment Interpretation Settings"),
                        command=lambda x=check:Check.setSdistinctions(x))
        advancedmenu.add_command(
                        label=_("Add/Modify Ad Hoc Sorting Group"),
                        command=lambda x=check:Check.addmodadhocsort(x))
        advancedmenu.add_command(
                label=_("Number of Examples to Record"),
                command=lambda x=check:Check.getexamplespergrouptorecord(x))
        """Unused for now"""
        # settingsmenu = Menu(menubar, tearoff=0)
        # changestuffmenu.add_cascade(label=_("Settings"), menu=settingsmenu)
        """help"""
        helpmenu = Menu(self.menubar, tearoff=0)
        helpmenu.add_command(label=_("About"),
                        command=self.helpabout)
        self.menubar.add_cascade(label=_("Help"), menu=helpmenu)
        self.parent.config(menu=self.menubar)
        self.menu=True
        self.setcontext()
        self.unbind_all('<Enter>')
    def helpabout(self):
        window=Window(self)
        title=(_("{name} Dictionary and Orthography Checker".format(name=self.program['name'])))
        window.title(title)
        Label(window.frame, text=_("version: {}").format(program['version']),anchor='c',padx=50
                        ).grid(row=1,column=0,sticky='we')
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
                                                    name=self.program['name'])
        webtext=_("For help with this tool, please check out the documentation "
                "at {url} ").format(url=self.program['url'])
        mailtext=_("or write me at {}.").format(self.program['Email'])
        Label(window.frame, text=title,
                        font=self.fonts['title'],anchor='c',padx=50
                        ).grid(row=0,column=0,sticky='we')
        f=ScrollingFrame(window.frame)
        f.grid(row=2,column=0,sticky='we')
        Label(f.content, image=self.photo['small'],text='',
                        bg=self.theme['background']
                        ).grid(row=0,column=0,sticky='we')
        l=Label(f.content, text=text, padx=50,
                wraplength=int(self.winfo_screenwidth()/2)
                ).grid(row=1,column=0,pady=(50,0),sticky='we')
        webl=Label(f.content, text=webtext, padx=50,#pady=50,
                wraplength=int(self.winfo_screenwidth()/2)
                )
        webl.grid(row=2,column=0,sticky='we')
        maill=Label(f.content, text=mailtext, padx=50,#pady=50,
                wraplength=int(self.winfo_screenwidth()/2)
                )
        maill.grid(row=3,column=0,sticky='we')
        webl.bind("<Button-1>", lambda e: openweburl(self.program['url']))
        murl='mailto:{}?subject= A→Z+T question'.format(self.program['Email'])
        maill.bind("<Button-1>", lambda e: openweburl(murl))
    def maketitle(self):
        title=_("{name} Dictionary and Orthography Checker").format(
                                                    name=self.program['name'])
        if self.master.themename != 'greygreen':
            print(f"Using theme '{self.master.themename}'.")
            title+=_(' ('+self.master.themename+')')
        self.parent.title(title)
    def setimages(self):
        # Program icon(s) (First should be transparent!)
        #Use this:
        log.info("Scaling images; please wait...") #threading?
        # threading.Thread(target=thread_function, args=(arg1,),kwargs={'arg2': arg2})
        # if process:
        #     from multiprocessing import Process
        #     log.info("Running as multi-process")
        #     p = Process(target=block)
        # elif thread:
        #     from threading import Thread
        #     log.info("Running as threaded")
        #     p = Thread(target=block)
        # else:
        #     log.info("Running in line")
        #     block()
        # if process or thread:
        #     p.exception = None
        #     try:
        #         p.start()
        #     except BaseException as e:
        #         log.error("Exception!", traceback.format_exc())
        #         p.exception = e
        #     p.join(timeout) #finish this after timeout, in any case
        #     if p.exception:
        #         log.error("Exception2!", traceback.format_exc())
        #         raise p.exception
        #     if process:
        #         p.terminate() #for processes, not threads
        # x and y here express a float as two integers, so 0.7 = 7/10, because
        # the zoom and subsample fns only work on integers
        y=25 #10 #Higher number is better resolution (x*y/y), more time to process
        y=int(y) # These all must be integers
        x=int(program['scale']*y)
        self.parent.photo={}
        def mkimg(name,relurl):
            imgurl=file.fullpathname(relurl)
            if x != y: # should scale if off by >2% either way
                self.parent.photo[name] = tkinter.PhotoImage(
                                        file = imgurl).zoom(x,x).subsample(y,y)
            else: #if close enough...
                self.parent.photo[name] = tkinter.PhotoImage(file = imgurl)
        for name,relurl in [ ('transparent','images/AZT stacks6.png'),
                            ('small','images/AZT stacks6_sm.png'),
                            ('icon','images/AZT stacks6_icon.png'),
                            ('T','images/T alone clear6.png'),
                            ('C','images/Z alone clear6.png'),
                            ('V','images/A alone clear6.png'),
                            ('CV','images/ZA alone clear6.png'),
                            ('backgrounded','images/AZT stacks6.png'),
                            #Set images for tasks
                            ('verifyT','images/Verify List.png'),
                            ('sortT','images/Sort List.png'),
                            ('joinT','images/Join List.png'),
                            ('record','images/Microphone alone_sm.png'),
                            ('change','images/Change Circle_sm.png'),
                            ('checkedbox','images/checked.png'),
                            ('uncheckedbox','images/unchecked.png')
                        ]:
            mkimg(name,relurl)
        log.info("Done scaling images")
        self.parent.renderings={} #initialize this somewhere...
    def settheme(self):
        setthemes(self.parent)
        #Select from lightgreen, green, pink, lighterpink, evenlighterpink,
        #purple, Howard, Kent, Kim, yellow, greygreen1, lightgreygreen,
        #greygreen, highcontrast, tkinterdefault
        defaulttheme='greygreen'
        multiplier=99 #The default theme will be this more frequent than others.
        pot=list(self.parent.themes.keys())+([defaulttheme]*
                                        (multiplier*len(self.parent.themes)-1))
        self.parent.themename='Kent' #for the colorblind (to punish others...)
        self.parent.themename='highcontrast' #for low light environments
        self.parent.themename=pot[randint(0, len(pot))-1] #mostly defaulttheme
        if ((platform.uname().node == 'karlap')
                and (program['production'] is not True)):
            self.parent.themename='Kim' #for my development
        """These versions might be necessary later, but with another module"""
        if self.parent.themename not in self.parent.themes:
            print("Sorry, that theme doesn't seem to be set up. Pick from "
            "these options:",self.parent.themes.keys())
            exit()
        self.parent.theme=self.parent.themes[self.parent.themename]
        self.parent['background']=self.parent.theme['background']
    def setfontsdefault(self):
        log.log(2,self.parent.winfo_children())
        setfonts(self.parent)
        if len(self.parent.winfo_children()) >0:
            propagate(self.parent,attr='fonts')
            log.log(2,self.fonts['default']['size'])
        self.fonttheme='default'
        if hasattr(self,'context'): #don't do this before ContextMenu is there
            self.setcontext()
            if hasattr(self,'check'):
                self.check.checkcheck() #redraw the main window (not on boot)
    def setfontssmaller(self):
        setfonts(self.parent,fonttheme='smaller')
        propagate(self.parent,attr='fonts')
        log.log(2,self.fonts['default']['size'])
        self.fonttheme='smaller'
        self.setcontext()
        if hasattr(self,'check'):
            self.check.checkcheck() #redraw the main window
    def hidegroupnames(self):
        self.check.set('hidegroupnames', True, refresh=True)
        self.setcontext()
    def showgroupnames(self):
        self.check.set('hidegroupnames', False, refresh=True)
        self.setcontext()
    def setmasterconfig(self,program):
        self.parent.debug=False #needed?
        """Configure variables for the root window (master)"""
        for rc in [0,2]:
            self.parent.grid_rowconfigure(rc, weight=3)
            self.parent.grid_columnconfigure(rc, weight=3)
        self.settheme()
        self.setimages()
        #if resolutionsucks==True or windows==True:
            # setfonts(self.parent,fonttheme='small')
        #else:
        self.setfontsdefault()
        self.parent.wraplength=self.parent.winfo_screenwidth()-300 #exit button
        self.parent.program=program
    def setcontext(self,context=None):
        self.context.menuinit() #This is a ContextMenu() method
        if not hasattr(self,'menu') or self.menu == False:
            self.context.menuitem(_("Show Menus"),self._setmenus)
        else:
            self.context.menuitem(_("Hide Menus"),self._removemenus)
        if hasattr(self.check,'mainrelief') and self.check.mainrelief == None:
            self.context.menuitem(_("Show Buttons"),self._showbuttons)
        else:
            self.context.menuitem(_("Hide Buttons"),self._hidebuttons)
        if self.fonttheme == 'default':
            self.context.menuitem(_("Smaller Fonts"),self.setfontssmaller)
        else:
            self.context.menuitem(_("Larger Fonts"),self.setfontsdefault)
        if self.check.hidegroupnames:
            self.context.menuitem(_("Show group names"),self.showgroupnames)
        else:
            self.context.menuitem(_("Hide group names"),self.hidegroupnames)
    def __init__(self,parent,program):
        start_time=time.time() #this enables boot time evaluation
        # print(time.time()-start_time) # with this
        self.parent=parent
        self.exitFlag = ExitFlag()
        setexitflag(parent,self.exitFlag)
        self.setmasterconfig(program)
        inherit(self) # do this after setting config.
        #set up languages before splash window:
        self.interfacelangs=file.getinterfacelangs()
        interfacelang=file.getinterfacelang()
        if interfacelang is None:
            setinterfacelang('fr')
        else:
            setinterfacelang(interfacelang)
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
        """Things that belong to a tkinter.Frame go after this:"""
        super().__init__(parent)
        # super().__init__(parent,class_="AZT")
        parent.withdraw()
        splash = Splash(self)
        self.grid(row=1, column=1,  #This is inbetween rc=[0,2], above.
                sticky=tkinter.N+tkinter.E+tkinter.S+tkinter.W
                )
        """Set up the frame in this (mainapplication) frame. This will be
        'placed' in the middle of the mainapplication frame, which is
        gridded into the center of the root window. This configuration keeps
        the frame with all the visual stuff in the middle of the window,
        without letting the window shrink to really small."""
        self.frame=Frame(self)
        """Give the main window some margin"""
        self.frame['padx']=25
        self.frame['pady']=25
        self.frame.grid(row=0, column=0)
        """Pick one of these two placements:"""
        # self.frame.place(in_=self, anchor="c", relx=.5, rely=.5)
        # self.frame.grid(column=0, row=0)
        parent.iconphoto(True, self.photo['icon'])
        self.maketitle()
        # self.introtext=_()
        # l=Label(self.frame, text=self.introtext, font=self.fonts['title'])
        # l.grid(row=0, column=0, columnspan=2)
        nsyls=None #this will give the default (currently 5)
        """This means make check with
        this app as parent
        the root window as base window, and
        the root window as the master window, from which new windows should
        inherit attributes
        make syllable profile data analysis up to nsyls syllables
        (more is more load time.)
        """
        self.check=Check(self,self.frame,nsyls=nsyls)
        """Do any check tests here"""
        """Make the rest of the mainApplication window"""
        e=(_("Exit"))
        #If the user exits out before this point, just stop.
        if self.check is None:
            l=Label(self.frame,text="Sorry, I couldn't find enough data!")
            l.grid(row=0,column=0)
        try:
            self.check.frame.winfo_exists()
        except:
            return
        exit=tkinter.Button(self.frame, text=e,
                            command=lambda s=self.parent:on_quit(s),
                            width=15,bg=self.theme['background'],
                            activebackground=self.theme['activebackground'])
        exit.grid(row=2, column=1, sticky='ne')
        """Do this after we instantiate the check, so menus can run check
        methods"""
        ContextMenu(self)
        print("Finished loading main window in",time.time() - start_time," "
                                                                    "seconds.")
        """finished loading so destroy splash"""
        splash.destroy()
        parent.deiconify()
        """Don't show window again until check is done"""
class ContextMenu:
    def updatebindings(self):
        def bindthisncheck(w):
            log.log(2,"{};{}".format(w,w.winfo_children()))
            if type(w) is not tkinter.Canvas: #ScrollingFrame:
                w.bind('<Enter>', self._bind_to_makemenus)
            for child in w.winfo_children():
                bindthisncheck(child)
        self.parent.bind('<Leave>', self._unbind_to_makemenus) #parent only
        bindthisncheck(self.parent)
    def undo_popup(self,event=None):
        if hasattr(self,'menu'):
            log.log(2,"undo_popup Checking for ContextMenu.menu: {}".format(
                                                            self.menu.__dict__))
            try:
                self.root.destroy() #Tk()
                log.log(3,"popup parent/root destroyed")
            except:
                log.log(3,"popup parent/root not destroyed!")
            finally:
                self.parent.unbind_all('<Button-1>')
    def menuinit(self):
        try:
            self.root=tkinter.Tk()
            self.root.withdraw()
            inherit(self.root,self.parent)
            self.menu = Menu(self.root, tearoff=0)
            log.log(3,"menuinit done: {}".format(self.menu.__dict__))
        except:
            log.error("Problem initializing context menu")
    def menuitem(self,msg,cmd):
        self.menu.add_command(label=msg,command=cmd)
    def dosetcontext(self):
        try:
            log.log(3,"setcontext: {}".format(self.parent.setcontext))
            self.parent.setcontext(context=self.context)
        except:
            log.error("You need to have a setcontext() method for the "
                        "parent of this context menu ({}), to set menu "
                        "items under appropriate conditions ({}): {}.".format(
                            self.parent,self.context,self.parent.setcontext))
    def do_popup(self,event):
        try:
            self.menu.tk_popup(event.x_root, event.y_root)
        except:
            log.log(4,"Problem with self.menu.tk_popup; setting context")
            self.dosetcontext()
            self.menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.menu.grab_release() #allows click on main window
    def _bind_to_makemenus(self,event): #all needed to cover all of window
        self.parent.bind_all('<Button-3>',self.do_popup) #_all
        self.parent.bind_all('<Button-1>',self.undo_popup)
    def _unbind_to_makemenus(self,event):
        self.parent.unbind_all('<Button-3>')
    def __init__(self,parent,context=None):
        self.parent=parent
        self.parent.context=self
        self.context=context #where the menu is showing (e.g., verifyT)
        self.updatebindings()
class Renderer(object):
    def __init__(self,test=False,**kwargs):
        try:
            import PIL.ImageFont
            import PIL.ImageTk
            import PIL.ImageDraw
            import PIL.Image
        except:
            log.info("Seems like PIL is not installed; skipping Renderer init.")
            self.img=None
            return
        font=kwargs['font'].actual() #should always be there
        xpad=ypad=fspacing=font['size']
        fname=font['family']
        fsize=int(font['size']*1.33)
        fspacing=10
        fonttype=''
        if font['weight'] == 'bold':
            fonttype+='B'
        if font['slant'] == 'italic':
            fonttype+='I'
        if fonttype == '':
            fonttype='R'
        text=kwargs['text'] #should always be there
        text=text.replace('\t','    ') #Not sure why, but tabs aren't working.
        wraplength=kwargs['wraplength'] #should always be there
        log.log(2,"Rendering ‘{}’ text with font: {}".format(text,font))
        if (('justify' in kwargs and
                        kwargs['justify'] in [tkinter.LEFT,'left']) or
            ('anchor' in kwargs and
                        kwargs['anchor'] in [tkinter.E,"e"])):
            align="left"
        else:
            align="center" #also supports "right"
        if fname in ["Andika","Andika SIL"]:
            file='Andika-{}.ttf'.format('R') #There's only this one
            filenostaves='Andika-tstv-{}.ttf'.format(fonttype)
        elif fname in ["Charis","Charis SIL"]:
            file='CharisSIL-{}.ttf'.format(fonttype)
            filenostaves='CharisSIL-tstv-{}.ttf'.format(fonttype)
        elif fname in ["Gentium","Gentium SIL"]:
            if fonttype == 'B':
                fonttype='R'
            if fonttype == 'BI':
                fonttype='I'
            file='Gentium-{}.ttf'.format(fonttype)
            filenostaves='Gentium-tstv-{}.ttf'.format(fonttype)
        elif fname in ["Gentium Basic","Gentium Basic SIL"]:
            file='GenBas{}.ttf'.format(fonttype)
            filenostaves='GenBas-tstv-{}.ttf'.format(fonttype)
        elif fname in ["Gentium Book Basic","Gentium Book Basic SIL"]:
            file='GenBkBas{}.ttf'.format(fonttype)
            filenostaves='GenBkBas-tstv-{}.ttf'.format(fonttype)
        elif fname in ["DejaVu Sans"]:
            fonttype=fonttype.replace('B','Bold').replace('I','Oblique').replace('R','')
            if len(fonttype)>0:
                fonttype='-'+fonttype
            file='DejaVuSans{}.ttf'.format(fonttype)
            filenostaves='DejaVuSans-tstv-{}.ttf'.format(fonttype)
        else:
            log.error("Sorry, I have no info on font {}".format(fname))
            return
        try:
            font = PIL.ImageFont.truetype(font=filenostaves, size=fsize)
            log.log(2,"Using No Staves font")
        except:
            log.debug("Couldn't find No Staves font, going without")
            font = PIL.ImageFont.truetype(font=file, size=fsize)
        img = PIL.Image.new("1", (10,10), 255)
        draw = PIL.ImageDraw.Draw(img)
        w, h = draw.multiline_textsize(text, font=font, spacing=fspacing)
        textori=text
        lines=textori.split('\n') #get everything between manual linebreaks
        for line in lines:
            li=lines.index(line)
            words=line.split(' ') #split by words/spaces
            nl=x=y=0
            while y < len(words):
                y+=1
                l=' '.join(words[x+nl:y+nl])
                w, h = draw.multiline_textsize(l, font=font, spacing=fspacing)
                log.log(2,"Round {} Words {}-{}:{}, width: {}/{}".format(y,x+nl,
                                                y+nl,l,w,wraplength))
                if w>wraplength:
                    words.insert(y+nl-1,'\n')
                    x=y-1
                    nl+=1
            line=' '.join(words) #Join back words
            lines[li]=line
        text='\n'.join(lines) #join back sections between manual linebreaks
        log.debug(text)
        w, h = draw.multiline_textsize(text, font=font, spacing=fspacing)
        log.log(2,"Final size w: {}, h: {}".format(w,h))
        black = 'rgb(0, 0, 0)'
        white = 'rgb(255, 255, 255)'
        img = PIL.Image.new("RGBA", (w+xpad, h+ypad), (255, 255, 255,0 )) #alpha
        draw = PIL.ImageDraw.Draw(img)
        draw.multiline_text((0+xpad//2, 0+ypad//4), text,font=font,fill=black,
                                                                align=align)
        self.img = PIL.ImageTk.PhotoImage(img)
class Label(tkinter.Label):
    def wrap(self):
        availablexy(self)
        self.config(wraplength=self.maxwidth)
        log.log(3,'self.maxwidth (Label class): {}'.format(self.maxwidth))
    def __init__(self, parent, column=0, row=1, norender=False,**kwargs):
        """These have non-None defaults"""
        self.parent=parent
        if 'text' not in kwargs or kwargs['text'] is None:
            kwargs['text']=''
        if 'font' in kwargs:
            if isinstance(kwargs['font'],tkinter.font.Font):
                pass #use as is
            elif kwargs['font'] in parent.fonts: #if font key (e.g., 'small')
                kwargs['font']=parent.fonts[kwargs['font']] #change key to font
            else:
                kwargs['font']=parent.fonts['default']
        else:
            kwargs['font']=parent.fonts['default']
        inherit(self)
        if hasattr(self,'wraplength'):
            defaultwr=self.wraplength
        else:
            defaultwr=0
        kwargs['wraplength']=kwargs.get('wraplength',defaultwr)
        d=set(["̀","́","̂","̌","̄","̃", "᷉","̋","̄","̏","̌","̂","᷄","᷅","̌","᷆","᷇","᷉"])
        sticks=set(['˥','˦','˧','˨','˩',' '])
        if set(kwargs['text']) & (sticks|d) and not norender:
            # log.info(kwargs['font']['size'])
            style=(kwargs['font']['family'], # from kwargs['font'].actual()
                    kwargs['font']['size'],kwargs['font']['weight'],
                    kwargs['font']['slant'],kwargs['font']['underline'],
                    kwargs['font']['overstrike'])
            # log.info("style: {}".format(style))
            renderings=self.parent.renderings
            # log.info("renderings: {}".format(renderings))
            if style not in renderings:
                renderings[style]={}
            if kwargs['wraplength'] not in renderings[style]:
                renderings[style][kwargs['wraplength']]={}
            thisrenderings=renderings[style][kwargs['wraplength']]
            if (kwargs['text'] in thisrenderings and
                    thisrenderings[kwargs['text']] is not None):
                log.log(5,"text {} already rendered with {} wraplength, using."
                        "".format(kwargs['text'],kwargs['wraplength']))
                kwargs['image']=thisrenderings[kwargs['text']]
                kwargs['text']=''
            elif 'image' in kwargs and kwargs['image'] is not None:
                log.error("You gave an image and tone characters in the same "
                "label? ({},{})".format(image,kwargs['text']))
                return
            else:
                log.log(5,"Sticks found! (Generating image for label)")
                i=Renderer(**kwargs)
                self.tkimg=i.img
                if self.tkimg is not None:
                    thisrenderings[kwargs['text']]=kwargs['image']=self.tkimg
                    kwargs['text']=''
        else:
            kwargs['text']=nfc(kwargs['text'])
        tkinter.Label.__init__(self, parent, **kwargs)
        self['background']=self.theme['background']
class EntryField(tkinter.Entry):
    def renderlabel(self,grid=False,event=None):
        v=self.get()
        if hasattr(self,'rendered'): #Get grid info before destroying old one
            mygrid=self.rendered.grid_info()
            grid=True
            self.rendered.destroy()
        self.rendered=Label(self.parent,text=v)
        d=["̀","́","̂","̌","̄","̃", "᷉","̋","̄","̏","̌","̂","᷄","᷅","̌","᷆","᷇","᷉"]
        if set(d) & set(v):
            if grid:
                self.rendered.grid(**mygrid)
            elif hasattr(self,'rendergrid'):
                self.rendered.grid(**self.rendergrid)
            else:
                log.error("Help! I have no idea what happened!")
            delattr(self,'rendergrid')
        elif grid:
                self.rendergrid=mygrid
    def __init__(self, parent, render=False, **kwargs):
        self.parent=parent
        inherit(self)
        if 'font' not in kwargs:
            kwargs['font']=self.fonts['default']
        super().__init__(parent,**kwargs)
        if render is True:
            self.bind('<KeyRelease>', self.renderlabel)
            self.renderlabel()
        self['background']=self.theme['offwhite'] #because this is for entry...
class RadioButton(tkinter.Radiobutton):
    def __init__(self, parent, column=0, row=0, sticky='w', **kwargs):
        self.parent=parent
        inherit(self)
        if 'font' not in kwargs:
            kwargs['font']=self.fonts['default']
        kwargs['activebackground']=self.theme['activebackground']
        kwargs['selectcolor']=self.theme['activebackground']
        super().__init__(parent,**kwargs)
        self.grid(column=column, row=row, sticky=sticky)
class RadioButtonFrame(Frame):
    def __init__(self, parent, horizontal=False,**kwargs):
        for vars in ['var','opts']:
            if (vars not in kwargs):
                print('You need to set {} for radio button frame!').format(vars)
            else:
                setattr(self,vars,kwargs[vars])
                del kwargs[vars] #we don't want this going to the button.
        column=0
        sticky='w'
        self.parent=parent
        inherit(self)
        super(RadioButtonFrame,self).__init__(parent,**kwargs)
        kwargs['background']=self.theme['background']
        kwargs['activebackground']=self.theme['activebackground']
        row=0
        for opt in self.opts:
            value=opt[0]
            name=opt[1]
            log.log(3,"Value: {}; name: {}".format(value,name))
            RadioButton(self,variable=self.var, value=value, text=nfc(name),
                                                column=column,
                                                row=row,
                                                sticky=sticky,
                                                indicatoron=0,
                                                **kwargs)
            if horizontal:
                column+=1
            else:
                row+=1
class Button(tkinter.Button):
    def nofn(self):
        pass
    def __init__(self, parent, choice=None, window=None,
                command=None, column=0, row=1, norender=False,**kwargs):
        self.parent=parent
        inherit(self)
        """For button"""
        if 'anchor' not in kwargs:
            kwargs['anchor']="w"
        if 'text' not in kwargs:
            kwargs['text']=''
        if 'wraplength' not in kwargs:
            kwargs['wraplength']=parent.wraplength
        if 'font' in kwargs:
            if isinstance(kwargs['font'],tkinter.font.Font):
                pass #use as is
            elif kwargs['font'] in parent.fonts: #if font key (e.g., 'small')
                kwargs['font']=parent.fonts[kwargs['font']] #change key to font
            else:
                kwargs['font']=parent.fonts['default']
        else:
            kwargs['font']=parent.fonts['default']
        """For image rendering of button text"""
        sticks=set(['˥','˦','˧','˨','˩',' '])
        if set(kwargs['text']) & sticks and not norender:
            style=(kwargs['font']['family'], # from kwargs['font'].actual()
                    kwargs['font']['size'],kwargs['font']['weight'],
                    kwargs['font']['slant'],kwargs['font']['underline'],
                    kwargs['font']['overstrike'])
            # log.info("style: {}".format(style))
            renderings=self.parent.renderings
            # log.info("renderings: {}".format(renderings))
            if style not in renderings:
                renderings[style]={}
            if kwargs['wraplength'] not in renderings[style]:
                renderings[style][kwargs['wraplength']]={}
            thisrenderings=renderings[style][kwargs['wraplength']]
            if (kwargs['text'] in thisrenderings and
                    thisrenderings[kwargs['text']] is not None):
                log.log(5,"text {} already rendered with {} wraplength, using."
                        "".format(kwargs['text'],kwargs['wraplength']))
                kwargs['image']=thisrenderings[kwargs['text']]
                kwargs['text']=''
            elif 'image' in kwargs and kwargs['image'] is not None:
                log.error("You gave an image and tone characters in the same "
                "button text? ({},{})".format(image,kwargs['text']))
                return
            else:
                log.log(5,"sticks found! (Generating image for button)")
                i=Renderer(**kwargs)
                self.tkimg=i.img
                if self.tkimg is not None:
                    thisrenderings[kwargs['text']]=kwargs['image']=self.tkimg
                    kwargs['text']=''
        kwargs['text']=nfc(kwargs['text'])
        """For Grid"""
        if 'sticky' in kwargs:
            sticky=kwargs['sticky']
            del kwargs['sticky'] #we don't want this going to the button.
        else:
            sticky="W"+"E"
        kwargs['activebackground']=self.theme['activebackground']
        kwargs['background']=self.theme['background']
        if self.debug == True:
            for arg in kwargs:
                print("Button "+arg+": "+kwargs[arg])
        # `command` is my hacky command specification, with lots of args added.
        # cmd is just the command passing through.
        if 'cmd' in kwargs and kwargs['cmd'] is not None:
            cmd=kwargs['cmd']
            del kwargs['cmd'] #we don't want this going to the button as is.
        elif command is None:
            cmd=self.nofn
        else:
            """This doesn't seem to be working, but OK to avoid it..."""
            if window is not None:
                if choice is not None:
                    cmd=lambda w=window:command(choice,window=w)
                else:
                    cmd=lambda w=window:command(window=w)
            else:
                if choice is not None:
                    cmd=lambda :command('choice')
                else:
                    cmd=lambda :command()
        tkinter.Button.__init__(self, parent, command=cmd, **kwargs)
        self.grid(column=column, row=row, sticky=sticky)
class CheckButton(tkinter.Checkbutton):
    def __init__(self, parent, **kwargs):
        self.parent=parent
        inherit(self)
        super(CheckButton,self).__init__(parent,
                                bg=self.theme['background'],
                                activebackground=self.theme['activebackground'],
                                image=self.photo['uncheckedbox'],
                                selectimage=self.photo['checkedbox'],
                                indicatoron=False,
                                compound='left',
                                font=self.fonts['read'],
                                anchor='w',
                                **kwargs
                                )
class RecordButtonFrame(Frame):
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
            log.info("didn't stop recorder; was it on?")
        if self.test is not True:
            self.addlink()
        self.b.destroy()
        self.makeplaybutton()
        self.makedeletebutton()
    def _redo(self, event):
        log.log(3,"I'm deleting the recording now")
        self.p.destroy()
        self.makerecordbutton()
        self.r.destroy()
    def makebuttons(self):
        if file.exists(self.filenameURL):
            self.makeplaybutton()
            self.makedeletebutton()
        else:
            self.makerecordbutton()
    def makerecordbutton(self):
        self.b=Button(self,text=_('Record'),command=self.function)
        self.b.grid(row=0, column=0,sticky='w')
        self.b.bind('<ButtonPress>', self._start)
        self.b.bind('<ButtonRelease>', self._stop)
    def _play(self,event=None):
        log.debug("Asking PA to play now")
        self.player=sound.SoundFilePlayer(self.filenameURL,self.pa,
                                                                self.settings)
        self.player.play()
    def makeplaybutton(self):
        self.p=Button(self,text=_('Play'),command=self._play)
        #Not using these for now
        # self.p.bind('<ButtonPress>', self._play)
        # self.p.bind('<ButtonRelease>', self.function)
        self.p.grid(row=0, column=1,sticky='w')
        pttext=_("Click to hear this utterance")
        if program['praatisthere']:
            pttext+='; '+_("right click to open in praat")
            self.p.bind('<Button-3>',lambda x: praatopen(self.filenameURL))
        self.pt=ToolTip(self.p,pttext)
    def makedeletebutton(self):
        self.r=Button(self,text=_('Redo'),command=self.function)
        self.r.grid(row=0, column=2,sticky='w')
        self.r.bind('<ButtonRelease>', self._redo)
    def addlink(self):
        #this checks for and doesn't add if already there.
        self.db.addmediafields(self.node,self.filename,self.audiolang)
    def function(self):
        pass
    def makefilenames(self=None,check=None,senseid=None):
        if self is not None: #i.e., this is called by class
            if self.test==True:
                return "test_{}_{}.wav".format(self.settings.fs,
                                                self.settings.sample_format)
            if None in [self.id, self.node, self.gloss]:
                log.debug("Sorry, unless testing we need all these "
                        "arguments; exiting.")
                return
            form=self.form
            node=self.node
            check=self.check
            id=self.id
            gloss=self.gloss
            # audio=None
        else: #self is None, i.e., this method called on something else.
            if None in [check, senseid]:
                return
            id=senseid
            node=firstoflist(check.db.get('example',senseid=senseid,
                                location=check.name).get())
            if node is None:
                # This should never be!
                log.error("Looks like a node came back 'None'; this may be "
                            "from multiple examples with the same frame; check"
                            "the log for details on what {} found".format(
                            check.program['name']
                            ))
                nodes=check.db.get('examplebylocation',senseid=senseid,
                                    location=check.name)
                for node in nodes:
                    for child in node:
                        log.error("Node{}: {}; tag:{}; attrib:{}".format(
                            nodes.index(node),child,child.tag, child.attrib,
                                                                    child.text))
                        for grandchild in child:
                            log.error("Node{}c: {}; tag:{}; attrib:{}".format(
                                nodes.index(node),grandchild,grandchild.tag,
                                            grandchild.attrib,grandchild.text))
                            for ggchild in grandchild:
                                log.error("Node{}cg: {}; tag:{}; attrib:{}; text:{}".format(
                                    nodes.index(node),ggchild,ggchild.tag,
                                                ggchild.attrib,ggchild.text))
            gloss=unlist(check.db.get('translation/form/text',node=node,
                            glosslang=check.glosslangs[0],showurl=True).get('text'))
            form=unlist(check.db.get('form/text',node=node,showurl=True,
                                            analang=check.analang).get('text'))
            log.log(4,"gloss: {}".format(gloss))
            log.log(4,"form: {}".format(form))
        audio=check.db.get('form/text',node=node,showurl=True,
                                        analang=check.audiolang).get('text')
        log.log(4,"audio: {}".format(audio))
        audio=unlist(audio)
        if gloss is None:
            gloss=t(check.db.get('gloss',senseid=senseid,
                                    glosslang=check.glosslangs[0]).get('text'))
        if form is None and node is not None:
            form=t(node.find(f"form[@lang='{check.analang}']/text"))
        if audio is not None:
            filenameURL=str(file.getdiredurl(check.audiodir,audio))
            if file.exists(filenameURL):
                log.debug("Audio file found! using name: {}; diredname: {}"
                    "".format(audio, filenameURL))
                return audio
            else:
                log.debug("Audio link found, but no file found! Making options."
                    "\n{}; diredname: {}".format(audio, filenameURL))
        pslocopts=[check.ps]
        # Except for data generated early in 2021, profile should not be there,
        # because it can change with analysis. But we include here to pick up
        # old files, in case they are there but not linked.
        pslocopts.insert(0,check.ps+'_'+check.profile) # first option (legacy).
        fieldlocopts=[None]
        if (node.tag == 'example'):
            l=node.find("field[@type='location']//text")
            if hasattr(l,'text') and l.text is not None:
                #the last option is taken, if none are found
                pslocopts.insert(0,check.ps+'-'+l.text) #the first option.
                fieldlocopts.append(l.text) #make this the last option.
                # Yes, these allow for location to be present twice, but
                # that should never be found, nor offered
        if not hasattr(check, 'rx'): #remove diacritics:
            check.rx={'d':rx.make(rx.s(check,'d'),compile=True)}
        filenames=[]
        # We iterate over lots of filename schemas, to preserve legacy data.
        for pslocopt in pslocopts:
            for fieldlocopt in fieldlocopts: #for older name schema
                for legacy in ['_', None]:
                    for tags in [ None, 1 ]:
                        args=[id]
                        if tags is not None:
                            args+=[node.tag]
                            if node.tag == 'field':
                                args+=[node.get("type")]
                        args+=[form]
                        args+=[gloss]
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
        #test if any of the generated filenames are there
        for filename in filenames:
            filenameURL=str(file.getdiredurl(check.audiodir,filename))
            log.debug("Looking for Audio file: {}; filename possibilities: {}; "
                "url:{}".format(filename, filenames, filenameURL))
            if file.exists(filenameURL):
                log.debug("Audiofile found! using name: {}; possibilities: {}; "
                    "url:{}".format(filename, filenames, filenameURL))
                return filename
        #if you don't find any, take the *last* values
        log.debug("No audio file found! using name: {}; names: {}; url:{}"
                "".format(filename, filenames, filenameURL))
        return filename
    def __init__(self,parent,check,id=None,node=None,form=None,gloss=None,test=False,**kwargs):
        # This class needs to be cleanup after closing, with check.donewpyaudio()
        """Originally from https://realpython.com/playing-and-recording-
        sound-python/"""
        self.db=check.db
        self.node=node #This should never be more than one node...
        framed=kwargs.pop('framed',None) #Either this or the next two...
        if framed is not None:
            formdefault=framed.forms[check.analang]
            glossdefault=framed.forms[check.glosslangs[0]]
        else:
            formdefault=None
            glossdefault=None
        self.form=kwargs.pop('form',formdefault)
        self.gloss=kwargs.pop('gloss',glossdefault)
        self.id=id
        self.gloss=gloss
        self.check=check
        try:
            check.pyaudio.get_format_from_width(1) #get_device_count()
        except:
            check.pyaudio=sound.AudioInterface()
        self.pa=check.pyaudio
        if not hasattr(check,'soundsettings'):
            check.loadsoundsettings()
        self.callbackrecording=True
        self.settings=check.soundsettings
        self.chunk = 1024  # Record in chunks of 1024 samples (for block only)
        self.channels = 1 #Always record in mono
        self.audiolang=check.audiolang
        self.test=test
        self.filename=self.makefilenames()
        self.filenameURL=str(file.getdiredurl(check.audiodir,self.filename))
        if (file.exists(self.filenameURL) and self.test == False
                and check.audiolang is not None):
            self.addlink() #just in case an old file doesn't have links
        Frame.__init__(self,parent, **kwargs)
        """These need to happen after the frame is created, as they
        might cause the init to stop."""
        if check.audiolang is None and self.test is not True:
            tlang=_("Set audio language to get record buttons!")
            log.error(tlang)
            Label(self,text=tlang,borderwidth=1,
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
            Label(self,text=text,borderwidth=1,
                relief='raised' #flat, raised, sunken, groove, and ridge
                ).grid(row=0,column=0)
            return
        self.makebuttons()
class ButtonFrame(Frame):
    def __init__(self,parent,
                    optionlist,command,
                    window=None,
                    **kwargs
                    ):
        self.parent=parent
        inherit(self)
        if self.debug == True:
            for kwarg in kwargs:
                print("ButtonFrame",kwarg,":",kwargs[kwarg])
        Frame.__init__(self,parent)
        gimmenull=False # When do I want a null option added to my lists? ever?
        self['background']=self.theme['background']
        i=0
        """Make sure list is in the proper format: list of dictionaries"""
        if type(optionlist) is not list:
            print("optionlist is Not a list!",optionlist,type(optionlist))
            return
        elif (optionlist is None) or (len(optionlist) == 0):
            print("list is empty!",type(optionlist))
            return
            """Assuming from here on that the first list item represents
            the format of the whole list; hope that's true!"""
        elif optionlist[0] is dict:
            print("looks like options are already in dictionary format.")
        elif (type(optionlist[0]) is str) or (type(optionlist[0]) is int):
            """when optionlist is a list of strings/codes/integers"""
            print("looks like options are just a list of codes; making dict.")
            optionlist = [({'code':optionlist[i], 'name':optionlist[i]}
                            ) for i in range(0, len(optionlist))]
        elif type(optionlist[0]) is tuple:
            if type(optionlist[0][1]) is str:
                """when optionlist is a list of binary tuples (codes,names)"""
                print("looks like options are just a list of (codes,names) "
                        "tuples; making dict.")
                optionlist = [({'code':optionlist[i][0],
                                'name':optionlist[i][1]}
                                ) for i in range(0, len(optionlist))]
            elif type(optionlist[0][1]) is int:
                """when optionlist is a list of binary tuples (codes,counts)"""
                print("looks like options are just a list of (codes,counts) "
                        "tuples; making dict.")
                optionlist = [({'code':optionlist[i][0],
                                'description':optionlist[i][1]}
                                ) for i in range(0, len(optionlist))]
        if not 'name' in optionlist[0].keys(): #duplicate name from code.
            for i in range(0, len(optionlist)):
                optionlist[i]['name']=optionlist[i]['code']
        if gimmenull == True:
            optionlist.append(({code:"Null",name:"None of These"}))
        for choice in optionlist:
            if choice['name'] == ["Null"]:
                command=newvowel #come up with something better here..…
            if 'description' in choice.keys():
                print(choice['name'],str(choice['description']))
                text=choice['name']+' ('+str(choice['description'])+')'
            else:
                text=choice['name']
            """commands are methods, so this normally includes self (don't
            specify it here). x= as a lambda argument allows us to assign the
            variable value now (in the loop across choices). Otherwise, it will
            maintain a link to the variable itself, and give the last value it
            had to all the buttons... --not what we want!
            """
            cmd=lambda x=choice['code'], w=window:command(x,window=w)
            b=Button(self,text=text,choice=choice['code'],
                    window=window,cmd=cmd,#width=self.width,
                    row=i,
                    **kwargs
                    )
            i=i+1
class ScrollingButtonFrame(ScrollingFrame,ButtonFrame):
    """This needs to go inside another frame, for accurrate grid placement"""
    def __init__(self,parent,optionlist,command,window=None,**kwargs):
        ScrollingFrame.__init__(self,parent)
        self.bf=ButtonFrame(parent=self.content,
                            optionlist=optionlist,
                            command=command,
                            window=window,
                            **kwargs)
        self.bf.grid(row=0, column=0)
class Wait(Window): #tkinter.Toplevel?
    def close(self):
        self.update_idletasks()
        self.parent.deiconify()
        self.destroy()
    def __init__(self, parent=None,msg=None):
        self.parent=parent
        self.parent.withdraw()
        global program
        super(Wait, self).__init__(parent,exit=False)
        self.withdraw() #don't show until we're done making it
        inherit(self)
        self.attributes("-topmost", True)
        self['background']=parent['background']
        self.photo = parent.photo #need this before making the frame
        title=(_("Please Wait! {name} Dictionary and Orthography Checker "
                        "in Process").format(name=self.program['name']))
        self.title(title)
        text=_("Please Wait...")
        self.l=Label(self.outsideframe, text=text,
                font=self.fonts['title'],anchor='c')
        self.l.grid(row=0,column=0,sticky='we')
        if msg is not None:
            self.l1=Label(self.outsideframe, text=msg,
                font=self.fonts['default'],anchor='c')
            self.l1.grid(row=1,column=0,sticky='we')
        self.l2=Label(self.outsideframe, image=self.photo['small'],text='',
                        bg=self['background']
                        )
        self.l2.grid(row=2,column=0,sticky='we',padx=50,pady=50)
        self.deiconify() #show after the window is built
        #for some reason this has to follow the above, or you get a blank window
        self.update_idletasks() #updates just geometry
class Splash(Window):
    def __init__(self, parent):
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
        Label(self, text=title, pady=10,
                        font=self.fonts['title'],anchor='c',padx=25
                        ).grid(row=0,column=0,sticky='we')
        Label(self, text=v, anchor='c',padx=25
                        ).grid(row=1,column=0,sticky='we')
        Label(self, image=self.photo['transparent'],text='',
                        bg=self.theme['background']
                        ).grid(row=2,column=0,sticky='we')
        l=Label(self, text=text, padx=50,
                wraplength=int(self.winfo_screenwidth()/2)
                ).grid(row=3,column=0,sticky='we')
        self.withdraw() #don't show until placed
        self.update_idletasks()
        self.w = self.winfo_reqwidth()
        x=int(self.master.winfo_screenwidth()/2-(self.w/2))
        self.h = self.winfo_reqheight()
        y=int(self.master.winfo_screenheight()/2 -(self.h/2))
        self.geometry('+%d+%d' % (x, y))
        self.deiconify() #show after placement
        self.update()
class ToolTip(object):
    """
    create a tooltip for a given widget
    modified from https://stackoverflow.com/, originally from
    www.daniweb.com/programming/software-development/code/484591/a-tooltip-class-for-tkinter
    Modified to include a delay time by Victor Zaccardo, 25mar16
    """
    def __init__(self, widget, text='widget info'):
        self.waittime = 500     #miliseconds
        self.wraplength = 180   #pixels
        self.dispx = 25
        self.dispy = 20
        self.widget = widget
        self.text = text
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)
        self.widget.bind("<ButtonPress>", self.leave)
        self.id = None
        self.tw = None
    def enter(self, event=None):
        self.event=event
        self.schedule()
    def entertip(self, event=None):
        self.dispx=-self.dispx
        self.dispy=-self.dispy
    def leave(self, event=None):
        self.unschedule()
        self.hidetip()
    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(self.waittime, self.showtip)
    def unschedule(self):
        id = self.id
        self.id = None
        if id:
            self.widget.after_cancel(id)
    def showtip(self, event=None):
        self.widget.unbind("<Leave>")
        x = y = 0
        x, y, cx, cy = self.widget.bbox("insert")
        # #based on widgets (flashy):
        # x += self.widget.winfo_rootx() + self.dispx
        # y += self.widget.winfo_rooty() + self.dispy
        #based on mouse click (much better):
        x += self.event.x_root +5 #+ self.dispx
        y += self.event.y_root #+ self.dispy
        # creates a toplevel window
        self.tw = tkinter.Toplevel(self.widget)
        self.tw.bind("<Enter>", self.entertip)
        # Leaves only the label and removes the app window
        self.tw.wm_overrideredirect(True)
        self.tw.wm_geometry("+%d+%d" % (x, y))
        label = tkinter.Label(self.tw, text=self.text, justify='left',
                       background="#ffffff", relief='solid', borderwidth=1,
                       wraplength = self.wraplength)
        label.pack(ipadx=1)
        self.widget.bind("<Leave>", self.leave)
    def hidetip(self):
        tw = self.tw
        self.tw= None
        if tw:
            tw.destroy()
class SliceDict(dict):
    """This stores and returns current ps and profile only; there is no check
    here that the consequences of the change are done (done in check)."""
    def count(self):
        return self[(self._profile,self._ps)]
    def scount(self,scount=None):
        """This just stores/returns the values in a dict, keyed by [ps][s]"""
        if scount is not None:
            self._scount=scount
        return self._scounts
    def makepsok(self):
        pss=self.pss()
        if not hasattr(self,'_ps') or self._ps not in pss:
            self.ps(pss[0])
    def makeprofileok(self):
        if not hasattr(self,'_ps'):
            self.makepsok()
        profiles=self.profiles(self._ps)
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
            self.makepsok()
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
            self.makeprofileok()
            return self._profile
    def nextps(self):
        self.makepsok()
        index=self._pss.index(self._ps)
        if index+1 == len(self._pss):
            self.ps(self._pss[0]) #cycle back
        else:
            self.ps(self._pss[index+1])
        return self._ps
    def nextprofile(self):
        self.makeprofileok()
        index=self._profiles.index(self._profile)
        if index+1 == len(self._profiles):
            self.profile(self._profiles[0]) #cycle back
        else:
            self.profile(self._profiles[index+1])
        return self._profile
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
        """This returns an up to date list of senseids in the curent slice, or
        else the specified slice"""
        # list(self._senseidsbyps[self._ps][self._profile])
        if ps is None and profile is None:
            return self._senseids #this is always the current slice
        else:
            if ps is None:
                ps=self._ps
            if profile is None:
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
        self._senseids=list(self._profilesbysense[self._ps][self._profile])
    def adhoc(self,ids=None):
        """If passed ids, add them. Otherwise, return dictionary."""
        if ids is not None:
            ps=self._ps
            if ps not in self._adhoc:
                 self._adhoc[ps]={}
            self._adhoc[ps][profile]=ids
        return self._adhoc
    def adhoccounts(self,ps=None):
        if ps is None:
            ps=self._ps
        return [x for x in self._adhoccounts if x[1] == ps]
    def updateadhoccounts(self):
        """This iterates across self.profilesbysense to provide counts for each
        ps-profile combination (aggravated for profile='Invalid')
        it should only be called when creating/adding to self.profilesbysense"""
        profilecountInvalid=0
        wcounts=list()
        for ps in self._adhoc:
            for profile in self._adhoc[ps]:
                count=len(self._adhoc[ps][profile])
                wcounts.append((count, profile, ps))
        for i in sorted(wcounts,reverse=True):
            self._adhoccounts[(i[1],i[2])]=i[0]
    def updateslices(self):
        """This iterates across self.profilesbysense to provide counts for each
        ps-profile combination (aggravated for profile='Invalid')
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
            self[(i[1],i[2])]=i[0]
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
    def checktosort(self,check=None):
        if check is None:
            check=self._checkparameters.check()
        cvt=self._checkparameters.cvt()
        ps=self._slicedict.ps()
        profile=self._slicedict.profile()
        if (check not in self[cvt][ps][profile] or
                self[cvt][ps][profile][check]['tosort'] == True):
            return True
    def profiletosort(self,profile=None):
        if profile is None:
            profile=self._slicedict.profile()
        cvt=self._checkparameters.cvt()
        ps=self._slicedict.ps()
        checks=self.updatechecksbycvt() #not keyed by profile
        for check in checks:
            if (check not in self[cvt][ps][profile] or
                    self[cvt][ps][profile][check]['tosort'] == True):
                return True
    def groupstoverify(self,check=None):
        """This assumes we have already run checktosort, so we won't do that"""
        if check is None:
            check=self._checkparameters.check()
        cvt=self._checkparameters.cvt()
        ps=self._slicedict.ps()
        profile=self._slicedict.profile()
        groups=self[cvt][ps][profile][check]['groups']
        done=self[cvt][ps][profile][check]['done']
        groupstoverify=set(groups)-set(done)
        log.debug("Check: {}; groupstodo: {}; groups: {}; done: {}; "
                "".format(check, groupstoverify, groups, done))
        if len(groupstoverify) >0: #len(groups) == 0 or excessive
            log.debug("{} check has sorted groups left to "
                    "verify: {} (groups: {})".format(check,groupstoverify,
                                                                    groups))
        return list(groupstoverify)
    def nextprofile(self, tosort=False, wsorted=False, toverify=False):
        ps=self._slicedict.ps()
        # self.makeprofileok()
        profiles=self.profiles(tosort=tosort,wsorted=wsorted,toverify=toverify)
        self.isprofileok(tosort=tosort,wsorted=wsorted,toverify=toverify)
        """"TypeError: string indices must be integers"""
        profile=self._slicedict.profile()
        nextprofile=profiles[0]
        if profile in profiles:
            idx=profiles.index(profile)
            if idx != len(profiles)-1:
                nextprofile=profiles[idx+1]
        self._slicedict.profile(nextprofile)
    def nextcheck(self, tosort=False, wsorted=False, toverify=False):
        check=self._checkparameters.check()
        checks=self.checks(tosort=tosort,wsorted=wsorted,toverify=toverify)
        if len(checks) == 0:
            log.error("There are no such checks! tosort: {}; wsorted: {}"
                        "".format(tosort,wsorted))
            return
        nextcheck=checks[0] #default
        if check in checks:
            idx=checks.index(check)
            if idx != len(checks)-1: # i.e., not already last
                nextcheck=checks[idx+1] #overwrite default in this one case
        self._checkparameters.check(nextcheck)
    def profiles(self, wsorted=False, tosort=False, toverify=False):
        profiles=self._slicedict.profiles() #already limited to current ps
        checks=self.checks(wsorted=wsorted,tosort=tosort)
        for profile in profiles:
            profileswcheckssorted=[i for j
                            in [self.groups(profile=profile,check=check)
                            for check in checks]
                            for i in j
                            ]
            for check in checks:
                log.info("groups found: {} (p:{};c:{})".format(
                        self.groups(profile=profile,check=check),profile,check
                        ))
            log.info("Looking for groups in checks in profiles: {} "
                    "\nwith tosort ({}); wsorted ({})"
                    "\nw Checks: {}"
                    "\nw Profiles: {}".format(
                                            profileswcheckssorted,
                                            tosort,wsorted,
                                            checks,profiles))
        p=[]
        for profile in profiles:
            if (
                (not wsorted and not tosort) or
                (tosort and self.profiletosort(profile)) or
                (wsorted and [i for j in
                [self.groups(profile=profile,check=check) for check in checks]
                                for i in j
                            ])
                ):
                p+=[profile]
        log.info("Profiles with tosort ({}); wsorted ({}): {}"
                    "".format(tosort,wsorted,p))
        return p
    def checks(self, wsorted=False, tosort=False, toverify=False):
        """This method is designed for tone, which depends on ps, not profile.
        we'll need to rethink it, when working on CV checks, which depend on
        profile, and not ps."""
        cs=[]
        checks=self.updatechecksbycvt()
        for check in checks:
            if (
                (not wsorted and not tosort) or
                # """These next two assume current ps-profile slice"""
                (wsorted and self.groups(check=check)) or
                (tosort and self.checktosort(check)) or
                (toverify and self.groupstoverify(check=check))
                ):
                cs+=[check]
        log.info("Checks with tosort ({}); wsorted ({}): {}"
                    "".format(tosort,wsorted,cs))
        return cs
    def groupstodo(self):
        """This returns prioritization in advance of sorting, before actual
        sort groups exist. So this only has meaning for segmental checks,
        and should not be used for tone."""
        """I don't know how to prioritize CV checks yet, if ever..."""
        cvt=self.checkparameters.cvt()
        ps=self.slicedict.ps()
        self.slicedict.scount()# [ps][s]=list()(x,n),)
        if cvt == 'V':
            todo=[self.scount[ps]['V']] #that's all that's there, for now.
        if cvt == 'C':
            todo=list()
            for s in self.scount[ps]:
                if s != 'V':
                    todo.extend(self.scount[ps][s]) #list of tuples
        if cvt in ['CV','T']:
            return None
    def senseidstosort(self,ps=None,profile=None):
        return self._idstosort
    def senseidssorted(self,ps=None,profile=None):
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
            log.info("Tosort now {} (marksenseidsorted)".format(self.tosort()))
    def marksenseidtosort(self,senseid):
        self._idstosort.append(senseid)
        self.tosort(True)
        log.info("Tosort now {} (marksenseidtosort)".format(self.tosort()))
        if senseid in self._idssorted:
            self._idssorted.remove(senseid)
    def store(self):
        """This will just store to file; reading will come from check."""
        log.info("Saving status dict to file")
        config=ConfigParser()
        config['status']=self #getattr(o,s)
        with open(self._filename, "w", encoding='utf-8') as file:
            config.write(file)
    def dict(self): #needed?
        for k in self:
            v[k]=self[k]
        return v
    def dictcheck(self,cvt=None,ps=None,profile=None,check=None):
        if cvt is None:
            cvt=self._checkparameters.cvt()
        if ps is None:
            ps=self._slicedict.ps()
        if profile is None:
            profile=self._slicedict.profile()
        if check is None:
            check=self._checkparameters.check()
        try:
            t=self[cvt][ps][profile][check]['groups']
        except KeyError:
            self.build(cvt=cvt,ps=ps,profile=profile,check=check)
    def build(self,upto=None,cvt=None,ps=None,profile=None,check=None):
        """this makes sure that the dictionary structure is there for work you
        are about to do"""
        # uptoOK=['type','ps','profile','check']:
        # if upto is not None and upto not in uptoOK:
        #     log.error("Bad upto value: {} (ok values: {})".format(upto,uptoOK))
        """Only build up to a None value"""
        """If anything is defined, give no defaults"""
        """Any defined variable after any default is an error"""
        """We don't want to mix default and specified values here, so
        unspecified after specified is None, and not built"""
        if (cvt is None and ps is not None
                or ps is None and profile is not None
                or profile is None and check is not None
                ):
            log.error("You have to define all values prior to the last: "
                                    "{}-{}-{}-{}".format(cvt,ps,profile,check))
        elif cvt is not None:
            log.debug("At least cvt value defined; using them: {}-{}-{}-{}"
                                            "".format(cvt,ps,profile,check))
        else:
            check=self._checkparameters.check()
            profile=self._slicedict.profile()
            ps=self._slicedict.ps()
            cvt=self._checkparameters.cvt()
        changed=False
        if cvt not in self:
            self[cvt]={}
            changed=True
        if ps not in self[cvt] and ps is not None:
            self[cvt][ps]={}
            changed=True
        if profile not in self[cvt][ps] and profile is not None:
            self[cvt][ps][profile]={}
            changed=True
        if check not in self[cvt][ps][profile] and check is not None:
            self[cvt][ps][profile][check]={}
            changed=True
        if None not in [ps,profile,check]:
            if isinstance(self[cvt][ps][profile][check],list):
                log.info("Updating {}-{} status dict to new schema".format(
                                                            profile,check))
                groups=self[cvt][ps][profile][check]
                self[cvt][ps][profile][check]={}
                self[cvt][ps][profile][check]['groups']=groups
                changed=True
            for key in ['groups','done']:
                if key not in self[cvt][ps][profile][check]:
                    log.info("Adding {} key to {}-{} status dict".format(
                                                    key,profile,check))
                    self[cvt][ps][profile][check][key]=list()
                    changed=True
            if 'tosort' not in self[cvt][ps][profile][check]:
                log.info("Adding tosort key to {}-{} status dict".format(
                                                    key,profile,check))
                self[cvt][ps][profile][check]['tosort']=True
                changed=True
        if changed == True:
            self.store()
    def cull(self):
        """This iterates across the whole dictionary, and removes empty nodes.
        Only do this when you're cleaning up, not about to start new work."""
        for t in self:
            pss=list(self[t])
            for ps in pss:
                profiles=list(self[t][ps]) #actual, not theoretical
                for profile in profiles:
                    checks=list(self[t][ps][profile]) #actual, not theoretical
                    for check in checks:
                        node=self[t][ps][profile][check]
                        if node['groups'] == []:
                            if node['done'] != []:
                                log.error("groups verified, but not present!")
                            del self[t][ps][profile][check]
                    if profile == {}:
                        del self[t][ps][profile]
                if ps == {}:
                    del self[t][ps]
            if t == {}:
                del self[t]
    """The following four methods address where to find what in this dict"""
    def updatechecksbycvt(self):
        """This just pulls the correct list from the dict, and updates params"""
        """It doesn't allow for input, as other fns do"""
        cvt=self._checkparameters.cvt()
        if not hasattr(self,'_checksdict'):
            self._checksdict={}
        if cvt not in self._checksdict:
            self._checksdict[cvt]={}
            self.renewchecks()
        if cvt == 'T':
            """This depends on ps and self.toneframes"""
            ps=self._slicedict.ps()
            if ps not in self._checksdict[cvt]:
                self._checks=[] #there may be none defined
            else:
                self._checks=self._checksdict[cvt][ps]
        else:
            profile=self._slicedict.profile()
            if profile not in self._checksdict[cvt]:
                self.renewchecks() #It should always be able to find something
            self._checks=self._checksdict[cvt][profile]
        return self._checks
    def renewchecks(self):
        """This should only need to be done on a boot or when a new tone frame
        is defined."""
        """This depends on cvt and profile, for CV checks"""
        """replaces getcheckspossible"""
        """replaces framenamesbyps"""
        """replaces self.checkspossible"""
        """replaces setnamesbyprofile"""
        if not hasattr(self,'_checksdict'):
            self._checksdict={}
        t=self._checkparameters.cvt()
        if t not in self._checksdict:
            self._checksdict[t]={}
        if t == 'T':
            toneframes=self.toneframes()
            for ps in self._slicedict.pss():
                if ps in toneframes:
                    self._checksdict[t][ps]=list(toneframes[ps])
        else:
            """This depends on profile only"""
            profile=self._slicedict.profile()
            n=profile.count(t)
            log.debug('Found {} instances of {} in {}'.format(n,t,profile))
            self._checksdict[t][profile]=list()
            for i in range(n): # get max checks and lesser
                self._checksdict[t][profile]+=self._checkparameters._Schecks[t][i+1] #b/c range
            self._checksdict[t][profile].sort(key=lambda x:len(x[0]),reverse=True)
    def node(self,cvt=None,ps=None,profile=None,check=None):
        """Do I want this to take non-real options?"""
        if cvt is None:
            cvt=self._checkparameters.cvt()
        if ps is None:
            ps=self._slicedict.ps()
        if profile is None:
            profile=self._slicedict.profile()
        if check is None:
            check=self._checkparameters.check()
        self.dictcheck(cvt=cvt,ps=ps,profile=profile,check=check)
        return self[cvt][ps][profile][check]
    def tosort(self,v=None,cvt=None,ps=None,profile=None,check=None):
        sn=self.node(cvt=cvt,ps=ps,profile=profile,check=check)
        ok=[None,True,False]
        if v not in ok:
            log.error("Tosort value ({}) invalid: OK values: {}".format(v,ok))
        self._tosortbool=sn['tosort']
        # log.error("Tosort value currently {}".format(self._tosort))
        if v is not None:
            # log.error("Setting tosort value to {}".format(v))
            self._tosortbool=sn['tosort']=v
        return self._tosortbool
    def verified(self,g=None,cvt=None,ps=None,profile=None,check=None):
        sn=self.node(cvt=cvt,ps=ps,profile=profile,check=check)
        self._verified=sn['done']
        if g is not None:
            self._verified=g
        return self._verified
    def groups(self,g=None,cvt=None,ps=None,profile=None,check=None):
        """Do I want this to take non-real options?"""
        sn=self.node(cvt=cvt,ps=ps,profile=profile,check=check)
        self._groups=sn['groups']
        if g is not None:
            self._groups=sn['groups']=g
        return self._groups
    def update(self,group=None,verified=False,refresh=True):
        """This function updates the status variable, not the lift file."""
        if group is None:
            group=self.group()
        log.info("Verification before update (verifying {} as {}): {}".format(
                                                group,verified,self.verified()))
        self.build()
        n=self.node()
        if verified == True:
            if group not in n['done']:
                n['done'].append(group)
        if verified == False:
            if group in n['done']:
                n['done'].remove(group)
        if refresh == True:
            self.store()
        log.info("Verification after update: {}".format(self.verified()))
    def group(self,group=None):
        """This maintains the group we are actually on, pulled from data
        located by current slice and parameters"""
        if group is not None:
            self._group=group
        else:
            return getattr(self,'_group',None)
    def makegroupok(self):
        groups=self.groups()
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
    def isprofileok(self, wsorted=False, tosort=False,toverify=False):
        profile=self._slicedict.profile()
        profiles=self.profiles(wsorted=wsorted,tosort=tosort,toverify=toverify)
        if profile in profiles:
            return True
    def ischeckok(self, wsorted=False, tosort=False, toverify=False):
        check=self._checkparameters.check()
        checks=self.checks(wsorted=wsorted,tosort=tosort,toverify=toverify)
        if check in checks:
            return True
    def makecheckok(self, wsorted=False, tosort=False):
        check=self._checkparameters.check()
        checks=self.checks(wsorted=wsorted, tosort=tosort)
        if check not in checks and checks != []:
                self._checkparameters.check(checks[0])
    def toneframes(self):
        return self._toneframes
    def __init__(self, checkparameters, slicedict, toneframes, filename, dict):
        """To populate subchecks, use self.groups()"""
        self._filename=filename
        super(StatusDict, self).__init__()
        for k in [i for i in dict if i is not None]:
            self[k]=dict[k]
        self._checkparameters=checkparameters
        self._slicedict=slicedict
        self._toneframes=toneframes
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
        else:
            return self._cvt
    def cvts(self):
        """This depends on nothing, so can go anywhere, and shouldn't need to
        rerun. This is a convenience wrapper only."""
        return list(self._cvts)
    def cvtdict(self):
        """This depends on nothing, so can go anywhere, and shouldn't need to
        rerun. This is a convenience wrapper only."""
        return self._cvts
    def check(self,check=None):
        """This needs to change/clear subchecks"""
        if check is not None:
            self._check=check
            # self.renewsubchecks() to status
        else:
            return self._check
    def __init__(self): # had, do I need check? to write?
        """replaces setnamesall"""
        """replaces self.checknamesall"""
        super(CheckParameters, self).__init__()
        """This replaces typedict"""
        self._cvts={
                'V':{'sg':_('Vowel'),'pl':_('Vowels')},
                'C':{'sg':_('Consonant'),'pl':_('Consonants')},
                'CV':{'sg':_('Consonant-Vowel combination'),
                        'pl':_('Consonant-Vowel combinations')},
                'T':{'sg':_('Tone'),'pl':_('Tones')},
                }
        self._Schecks={
            "V":{
                1:[("V1", "First/only Vowel")],
                2:[
                    ("V1=V2", "Same First/only Two Vowels"),
                    ("V1xV2", "Correspondence of First/only Two Vowels"),
                    ("V2", "Second Vowel")
                    ],
                3:[
                    ("V1=V2=V3", "Same First/only Three Vowels"),
                    ("V3", "Third Vowel"),
                    ("V2=V3", "Same Second Two Vowels"),
                    ("V2xV3", "Correspondence of Second Two Vowels")
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
                1:[("C1", "First/only Consonant")],
                2:[
                    ("C2", "Second Consonant"),
                    ("C1=C2","Same First/only Two Consonants"),
                    ("C1xC2", "Correspondence of First/only Two Consonants")
                    ],
                3:[
                    ("C2=C3","Same Second Two Consonants"),
                    ("C2xC3", "Correspondence of Second Two Consonants"),
                    ("C3", "Third Consonant"),
                    ("C1=C2=C3","Same First Three Consonants")
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
                1:[("#CV1", "Word-initial CV"),
                    ("C1xV1", "Correspondence of C1 and V1"),
                    ("CV1", "First/only CV")
                    ],
                2:[("CV2", "Second CV"),
                    ("C2xV2", "Correspondence of C2 and V2"),
                    ("CV1=CV2","Same First/only Two CVs"),
                    ("CV2#", "Word-final CV")
                    ],
                3:[
                    ("CV1=CV2=CV3","Same First/only Three CVs"),
                    ("CV3", "Third CV")
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
        """These two are only done here, as the only change with new data"""
        self.slicepriority()
        self.pspriority()
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
    def checktosort(self,check=None):
        if check is None:
            check=self._checkparameters.check()
        cvt=self._checkparameters.cvt()
        ps=self._slicedict.ps()
        profile=self._slicedict.profile()
        if (check not in self[cvt][ps][profile] or
                self[cvt][ps][profile][check]['tosort'] == True):
            return True
    def profiletosort(self,profile=None):
        if profile is None:
            profile=self._slicedict.profile()
        cvt=self._checkparameters.cvt()
        ps=self._slicedict.ps()
        checks=self.updatechecksbycvt() #not keyed by profile
        for check in checks:
            if (check not in self[cvt][ps][profile] or
                    self[cvt][ps][profile][check]['tosort'] == True):
                return True
    def groupstoverify(self,check=None):
        """This assumes we have already run checktosort, so we won't do that"""
        if check is None:
            check=self._checkparameters.check()
        cvt=self._checkparameters.cvt()
        ps=self._slicedict.ps()
        profile=self._slicedict.profile()
        groups=self[cvt][ps][profile][check]['groups']
        done=self[cvt][ps][profile][check]['done']
        groupstoverify=set(groups)-set(done)
        log.debug("Check: {}; groupstodo: {}; groups: {}; done: {}; "
                "".format(check, groupstoverify, groups, done))
        if len(groupstoverify) >0: #len(groups) == 0 or excessive
            log.debug("{} check has sorted groups left to "
                    "verify: {} (groups: {})".format(check,groupstoverify,
                                                                    groups))
        return list(groupstoverify)
    def nextprofile(self, tosort=False, wsorted=False, toverify=False):
        ps=self._slicedict.ps()
        # self.makeprofileok()
        profiles=self.profiles(tosort=tosort,wsorted=wsorted,toverify=toverify)
        self.isprofileok(tosort=tosort,wsorted=wsorted,toverify=toverify)
        """"TypeError: string indices must be integers"""
        profile=self._slicedict.profile()
        nextprofile=profiles[0]
        if profile in profiles:
            idx=profiles.index(profile)
            if idx != len(profiles)-1:
                nextprofile=profiles[idx+1]
        self._slicedict.profile(nextprofile)
    def nextcheck(self, tosort=False, wsorted=False, toverify=False):
        check=self._checkparameters.check()
        checks=self.checks(tosort=tosort,wsorted=wsorted,toverify=toverify)
        if len(checks) == 0:
            log.error("There are no such checks! tosort: {}; wsorted: {}"
                        "".format(tosort,wsorted))
            return
        nextcheck=checks[0] #default
        if check in checks:
            idx=checks.index(check)
            if idx != len(checks)-1: # i.e., not already last
                nextcheck=checks[idx+1] #overwrite default in this one case
        self._checkparameters.check(nextcheck)
    def profiles(self, wsorted=False, tosort=False, toverify=False):
        profiles=self._slicedict.profiles() #already limited to current ps
        checks=self.checks(wsorted=wsorted,tosort=tosort)
        for profile in profiles:
            profileswcheckssorted=[i for j
                            in [self.groups(profile=profile,check=check)
                            for check in checks]
                            for i in j
                            ]
            for check in checks:
                log.info("groups found: {} (p:{};c:{})".format(
                        self.groups(profile=profile,check=check),profile,check
                        ))
            log.info("Looking for groups in checks in profiles: {} "
                    "\nwith tosort ({}); wsorted ({})"
                    "\nw Checks: {}"
                    "\nw Profiles: {}".format(
                                            profileswcheckssorted,
                                            tosort,wsorted,
                                            checks,profiles))
        p=[]
        for profile in profiles:
            if (
                (not wsorted and not tosort) or
                (tosort and self.profiletosort(profile)) or
                (wsorted and [i for j in
                [self.groups(profile=profile,check=check) for check in checks]
                                for i in j
                            ])
                ):
                p+=[profile]
        log.info("Profiles with tosort ({}); wsorted ({}): {}"
                    "".format(tosort,wsorted,p))
        return p
    def checks(self, wsorted=False, tosort=False, toverify=False):
        """This method is designed for tone, which depends on ps, not profile.
        we'll need to rethink it, when working on CV checks, which depend on
        profile, and not ps."""
        cs=[]
        checks=self.updatechecksbycvt()
        for check in checks:
            if (
                (not wsorted and not tosort) or
                # """These next two assume current ps-profile slice"""
                (wsorted and self.groups(check=check)) or
                (tosort and self.checktosort(check)) or
                (toverify and self.groupstoverify(check=check))
                ):
                cs+=[check]
        log.info("Checks with tosort ({}); wsorted ({}): {}"
                    "".format(tosort,wsorted,cs))
        return cs
    def groupstodo(self):
        """This returns prioritization in advance of sorting, before actual
        sort groups exist. So this only has meaning for segmental checks,
        and should not be used for tone."""
        """I don't know how to prioritize CV checks yet, if ever..."""
        cvt=self.checkparameters.cvt()
        ps=self.slicedict.ps()
        self.slicedict.scount()# [ps][s]=list()(x,n),)
        if cvt == 'V':
            todo=[self.scount[ps]['V']] #that's all that's there, for now.
        if cvt == 'C':
            todo=list()
            for s in self.scount[ps]:
                if s != 'V':
                    todo.extend(self.scount[ps][s]) #list of tuples
        if cvt in ['CV','T']:
            return None
    def senseidstosort(self,ps=None,profile=None):
        return self._idstosort
    def senseidssorted(self,ps=None,profile=None):
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
            log.info("Tosort now {} (marksenseidsorted)".format(self.tosort()))
    def marksenseidtosort(self,senseid):
        self._idstosort.append(senseid)
        self.tosort(True)
        log.info("Tosort now {} (marksenseidtosort)".format(self.tosort()))
        if senseid in self._idssorted:
            self._idssorted.remove(senseid)
    def store(self):
        """This will just store to file; reading will come from check."""
        log.info("Saving status dict to file")
        config=ConfigParser()
        config['status']=self #getattr(o,s)
        with open(self._filename, "w", encoding='utf-8') as file:
            config.write(file)
    def dict(self): #needed?
        for k in self:
            v[k]=self[k]
        return v
    def dictcheck(self,cvt=None,ps=None,profile=None,check=None):
        if cvt is None:
            cvt=self._checkparameters.cvt()
        if ps is None:
            ps=self._slicedict.ps()
        if profile is None:
            profile=self._slicedict.profile()
        if check is None:
            check=self._checkparameters.check()
        try:
            t=self[cvt][ps][profile][check]['groups']
        except KeyError:
            self.build(cvt=cvt,ps=ps,profile=profile,check=check)
    def build(self,upto=None,cvt=None,ps=None,profile=None,check=None):
        """this makes sure that the dictionary structure is there for work you
        are about to do"""
        # uptoOK=['type','ps','profile','check']:
        # if upto is not None and upto not in uptoOK:
        #     log.error("Bad upto value: {} (ok values: {})".format(upto,uptoOK))
        """Only build up to a None value"""
        """If anything is defined, give no defaults"""
        """Any defined variable after any default is an error"""
        """We don't want to mix default and specified values here, so
        unspecified after specified is None, and not built"""
        if (cvt is None and ps is not None
                or ps is None and profile is not None
                or profile is None and check is not None
                ):
            log.error("You have to define all values prior to the last: "
                                    "{}-{}-{}-{}".format(cvt,ps,profile,check))
        elif cvt is not None:
            log.debug("At least cvt value defined; using them: {}-{}-{}-{}"
                                            "".format(cvt,ps,profile,check))
        else:
            check=self._checkparameters.check()
            profile=self._slicedict.profile()
            ps=self._slicedict.ps()
            cvt=self._checkparameters.cvt()
        changed=False
        if cvt not in self:
            self[cvt]={}
            changed=True
        if ps not in self[cvt] and ps is not None:
            self[cvt][ps]={}
            changed=True
        if profile not in self[cvt][ps] and profile is not None:
            self[cvt][ps][profile]={}
            changed=True
        if check not in self[cvt][ps][profile] and check is not None:
            self[cvt][ps][profile][check]={}
            changed=True
        if None not in [ps,profile,check]:
            if isinstance(self[cvt][ps][profile][check],list):
                log.info("Updating {}-{} status dict to new schema".format(
                                                            profile,check))
                groups=self[cvt][ps][profile][check]
                self[cvt][ps][profile][check]={}
                self[cvt][ps][profile][check]['groups']=groups
                changed=True
            for key in ['groups','done']:
                if key not in self[cvt][ps][profile][check]:
                    log.info("Adding {} key to {}-{} status dict".format(
                                                    key,profile,check))
                    self[cvt][ps][profile][check][key]=list()
                    changed=True
            if 'tosort' not in self[cvt][ps][profile][check]:
                log.info("Adding tosort key to {}-{} status dict".format(
                                                    key,profile,check))
                self[cvt][ps][profile][check]['tosort']=True
                changed=True
        if changed == True:
            self.store()
    def cull(self):
        """This iterates across the whole dictionary, and removes empty nodes.
        Only do this when you're cleaning up, not about to start new work."""
        for t in self:
            pss=list(self[t])
            for ps in pss:
                profiles=list(self[t][ps]) #actual, not theoretical
                for profile in profiles:
                    checks=list(self[t][ps][profile]) #actual, not theoretical
                    for check in checks:
                        node=self[t][ps][profile][check]
                        if node['groups'] == []:
                            if node['done'] != []:
                                log.error("groups verified, but not present!")
                            del self[t][ps][profile][check]
                    if profile == {}:
                        del self[t][ps][profile]
                if ps == {}:
                    del self[t][ps]
            if t == {}:
                del self[t]
    """The following four methods address where to find what in this dict"""
    def updatechecksbycvt(self):
        """This just pulls the correct list from the dict, and updates params"""
        """It doesn't allow for input, as other fns do"""
        cvt=self._checkparameters.cvt()
        if not hasattr(self,'_checksdict'):
            self._checksdict={}
        if cvt not in self._checksdict:
            self._checksdict[cvt]={}
            self.renewchecks()
        if cvt == 'T':
            """This depends on ps and self.toneframes"""
            ps=self._slicedict.ps()
            if ps not in self._checksdict[cvt]:
                self._checks=[] #there may be none defined
            else:
                self._checks=self._checksdict[cvt][ps]
        else:
            profile=self._slicedict.profile()
            if profile not in self._checksdict[cvt]:
                self.renewchecks() #It should always be able to find something
            self._checks=self._checksdict[cvt][profile]
        return self._checks
    def renewchecks(self):
        """This should only need to be done on a boot or when a new tone frame
        is defined."""
        """This depends on cvt and profile, for CV checks"""
        """replaces getcheckspossible"""
        """replaces framenamesbyps"""
        """replaces self.checkspossible"""
        """replaces setnamesbyprofile"""
        if not hasattr(self,'_checksdict'):
            self._checksdict={}
        t=self._checkparameters.cvt()
        if t not in self._checksdict:
            self._checksdict[t]={}
        if t == 'T':
            toneframes=self.toneframes()
            for ps in self._slicedict.pss():
                if ps in toneframes:
                    self._checksdict[t][ps]=list(toneframes[ps])
        else:
            """This depends on profile only"""
            profile=self._slicedict.profile()
            n=profile.count(t)
            log.debug('Found {} instances of {} in {}'.format(n,t,profile))
            self._checksdict[t][profile]=list()
            for i in range(n): # get max checks and lesser
                self._checksdict[t][profile]+=self._checkparameters._Schecks[t][i+1] #b/c range
            self._checksdict[t][profile].sort(key=lambda x:len(x[0]),reverse=True)
    def node(self,cvt=None,ps=None,profile=None,check=None):
        """Do I want this to take non-real options?"""
        if cvt is None:
            cvt=self._checkparameters.cvt()
        if ps is None:
            ps=self._slicedict.ps()
        if profile is None:
            profile=self._slicedict.profile()
        if check is None:
            check=self._checkparameters.check()
        self.dictcheck(cvt=cvt,ps=ps,profile=profile,check=check)
        return self[cvt][ps][profile][check]
    def tosort(self,v=None,cvt=None,ps=None,profile=None,check=None):
        sn=self.node(cvt=cvt,ps=ps,profile=profile,check=check)
        ok=[None,True,False]
        if v not in ok:
            log.error("Tosort value ({}) invalid: OK values: {}".format(v,ok))
        self._tosortbool=sn['tosort']
        # log.error("Tosort value currently {}".format(self._tosort))
        if v is not None:
            # log.error("Setting tosort value to {}".format(v))
            self._tosortbool=sn['tosort']=v
        return self._tosortbool
    def verified(self,g=None,cvt=None,ps=None,profile=None,check=None):
        sn=self.node(cvt=cvt,ps=ps,profile=profile,check=check)
        self._verified=sn['done']
        if g is not None:
            self._verified=g
        return self._verified
    def groups(self,g=None,cvt=None,ps=None,profile=None,check=None):
        """Do I want this to take non-real options?"""
        sn=self.node(cvt=cvt,ps=ps,profile=profile,check=check)
        self._groups=sn['groups']
        if g is not None:
            self._groups=sn['groups']=g
        return self._groups
    def update(self,group=None,verified=False,refresh=True):
        """This function updates the status variable, not the lift file."""
        if group is None:
            group=self.group()
        log.info("Verification before update (verifying {} as {}): {}".format(
                                                group,verified,self.verified()))
        self.build()
        n=self.node()
        if verified == True:
            if group not in n['done']:
                n['done'].append(group)
        if verified == False:
            if group in n['done']:
                n['done'].remove(group)
        if refresh == True:
            self.store()
        log.info("Verification after update: {}".format(self.verified()))
    def group(self,group=None):
        """This maintains the group we are actually on, pulled from data
        located by current slice and parameters"""
        if group is not None:
            self._group=group
        else:
            return getattr(self,'_group',None)
    def makegroupok(self):
        groups=self.groups()
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
    def isprofileok(self, wsorted=False, tosort=False,toverify=False):
        profile=self._slicedict.profile()
        profiles=self.profiles(wsorted=wsorted,tosort=tosort,toverify=toverify)
        if profile in profiles:
            return True
    def ischeckok(self, wsorted=False, tosort=False, toverify=False):
        check=self._checkparameters.check()
        checks=self.checks(wsorted=wsorted,tosort=tosort,toverify=toverify)
        if check in checks:
            return True
    def makecheckok(self, wsorted=False, tosort=False):
        check=self._checkparameters.check()
        checks=self.checks(wsorted=wsorted, tosort=tosort)
        if check not in checks and checks != []:
                self._checkparameters.check(checks[0])
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
        log.info("Returning checkslicetypecurrent kwargs {}".format(kwargs))
        return kwargs
    def __init__(self,checkparameters,slicedict,exs,toneframes,filename,dict):
        """To populate subchecks, use self.groups()"""
        self._filename=filename
        super(StatusDict, self).__init__()
        for k in [i for i in dict if i is not None]:
            self[k]=dict[k]
        self._checkparameters=checkparameters
        self._slicedict=slicedict
        self._examplesbygroup=exs
        self._toneframes=toneframes
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
        else:
            return self._cvt
    def cvts(self):
        """This depends on nothing, so can go anywhere, and shouldn't need to
        rerun. This is a convenience wrapper only."""
        return list(self._cvts)
    def cvtdict(self):
        """This depends on nothing, so can go anywhere, and shouldn't need to
        rerun. This is a convenience wrapper only."""
        return self._cvts
    def check(self,check=None):
        """This needs to change/clear subchecks"""
        if check is not None:
            self._check=check
            # self.renewsubchecks() to status
        else:
            return self._check
    def __init__(self): # had, do I need check? to write?
        """replaces setnamesall"""
        """replaces self.checknamesall"""
        super(CheckParameters, self).__init__()
        """This replaces typedict"""
        self._cvts={
                'V':{'sg':_('Vowel'),'pl':_('Vowels')},
                'C':{'sg':_('Consonant'),'pl':_('Consonants')},
                'CV':{'sg':_('Consonant-Vowel combination'),
                        'pl':_('Consonant-Vowel combinations')},
                'T':{'sg':_('Tone'),'pl':_('Tones')},
                }
        self._Schecks={
            "V":{
                1:[("V1", "First/only Vowel")],
                2:[
                    ("V1=V2", "Same First/only Two Vowels"),
                    ("V1xV2", "Correspondence of First/only Two Vowels"),
                    ("V2", "Second Vowel")
                    ],
                3:[
                    ("V1=V2=V3", "Same First/only Three Vowels"),
                    ("V3", "Third Vowel"),
                    ("V2=V3", "Same Second Two Vowels"),
                    ("V2xV3", "Correspondence of Second Two Vowels")
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
                1:[("C1", "First/only Consonant")],
                2:[
                    ("C2", "Second Consonant"),
                    ("C1=C2","Same First/only Two Consonants"),
                    ("C1xC2", "Correspondence of First/only Two Consonants")
                    ],
                3:[
                    ("C2=C3","Same Second Two Consonants"),
                    ("C2xC3", "Correspondence of Second Two Consonants"),
                    ("C3", "Third Consonant"),
                    ("C1=C2=C3","Same First Three Consonants")
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
                1:[("#CV1", "Word-initial CV"),
                    ("C1xV1", "Correspondence of C1 and V1"),
                    ("CV1", "First/only CV")
                    ],
                2:[("CV2", "Second CV"),
                    ("C2xV2", "Correspondence of C2 and V2"),
                    ("CV1=CV2","Same First/only Two CVs"),
                    ("CV2#", "Word-final CV")
                    ],
                3:[
                    ("CV1=CV2=CV3","Same First/only Three CVs"),
                    ("CV3", "Third CV")
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
def getinterfacelang():
    for lang in i18n:
        try:
            _
            if i18n[lang] == _.__self__:
                return lang
        except:
            log.debug("_ doesn't look defined yet, returning 'en' as current "
                                                        "interface language.")
            return 'en'
def setinterfacelang(lang,magic=False):
    global aztdir
    global i18n
    global _
    """Attention: for this to work, _ has to be defined globally (here, not in
    a class or module.) So I'm getting the language setting in the class, then
    calling the module (imported globally) from here."""
    curlang=getinterfacelang()
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
                                                "".format(getinterfacelang())))
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
    if len(dicts) == 1:
        log.debug("Just one dict: {}; just returning key.".format(dicts))
        return [list(dicts.keys()),] #This should be a list of lists
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
    log.info("Returning exampletype kwargs {}".format(kwargs))
    return kwargs
def checkslicetype(**kwargs):
    for arg in ['cvt','ps','profile','check']:
        kwargs[arg]=kwargs.get(arg,None)
    log.info("Returning checkslicetype kwargs {}".format(kwargs))
    return kwargs
def grouptype(**kwargs):
    for arg in ['wsorted','tosort','toverify','torecord','comparison']:
        kwargs[arg]=kwargs.get(arg,False)
    log.info("Returning grouptype kwargs {}".format(kwargs))
    return kwargs
def name(x):
    try:
        name=x.__name__ #If x is a function
        return name
    except:
        name=x.__class__.__name__ #If x is a class instance
        return "class."+name
def unlist(l,ignore=[None]):
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
    if all == True: #don't worry about othersOK yet
        if len(l) > 1:
            ox=[t(v) for v in l[:len(l)-2]] #Should probably always give text
            l=ox+[' and '.join([t(v) for v in l[len(l)-2:] if v not in ignore])]
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
def linebreakwords(x):
    log.debug("working on {}".format(x))
    return re.sub(' ','\n',x)
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
def setthemes(self):
    self.themes={'lightgreen':{
                        'background':'#c6ffb3',
                        'activebackground':'#c6ffb3',
                        'offwhite':None,
                        'highlight': 'red',
                        'white': 'white'}, #lighter green
                'green':{
                        'background':'#b3ff99',
                        'activebackground':'#c6ffb3',
                        'offwhite':None,
                        'highlight': 'red',
                        'white': 'white'},
                'pink':{
                        'background':'#ff99cc',
                        'activebackground':'#ff66b3',
                        'offwhite':None,
                        'highlight': 'red',
                        'white': 'white'},
                'lighterpink':{
                        'background':'#ffb3d9',
                        'activebackground':'#ff99cc',
                        'offwhite':None,
                        'highlight': 'red',
                        'white': 'white'},
                'evenlighterpink':{
                        'background':'#ffcce6',
                        'activebackground':'#ffb3d9',
                        'offwhite':'#ffe6f3',
                        'highlight': 'red',
                        'white': 'white'},
                'purple':{
                        'background':'#ffb3ec',
                        'activebackground':'#ff99e6',
                        'offwhite':'#ffe6f9',
                        'highlight': 'red',
                        'white': 'white'},
                'Howard':{
                        'background':'green',
                        'activebackground':'red',
                        'offwhite':'grey',
                        'highlight': 'red',
                        'white': 'white'},
                'Kent':{
                        'background':'red',
                        'activebackground':'green',
                        'offwhite':'grey',
                        'highlight': 'red',
                        'white': 'white'},
                'Kim':{
                        'background':'#ffbb99',
                        'activebackground':'#ffaa80',
                        'offwhite':'#ffeee6',
                        'highlight': 'red',
                        'white': 'white'},
                'yellow':{
                        'background':'#ffff99',
                        'activebackground':'#ffff80',
                        'offwhite':'#ffffe6',
                        'highlight': 'red',
                        'white': 'white'},
                'greygreen1':{
                        'background':'#62d16f',
                        'activebackground':'#4dcb5c',
                        'offwhite':'#ebf9ed',
                        'highlight': 'red',
                        'white': 'white'},
                'lightgreygreen':{
                        'background':'#9fdfca',
                        'activebackground':'#8cd9bf',
                        'offwhite':'#ecf9f4',
                        'highlight': 'red',
                        'white': 'white'},
                'greygreen':{
                        'background':'#8cd9bf',
                        'activebackground':'#66ccaa', #10% darker than the above
                        'offwhite':'#ecf9f4',
                        'highlight': 'red',
                        'white': 'white'}, #default!
                'highcontrast':{
                        'background':'white',
                        'activebackground':'#e6fff9', #10% darker than the above
                        'offwhite':'#ecf9f4',
                        'highlight': 'red',
                        'white': 'white'},
                'tkinterdefault':{
                        'background':None,
                        'activebackground':None,
                        'offwhite':None,
                        'highlight': 'red',
                        'white': 'white'}
                }
def setfonts(self,fonttheme='default'):
    log.info("Setting fonts with {} theme".format(fonttheme))
    if fonttheme == 'smaller':
        default=12*program['scale']
    else:
        default=18*program['scale']
    normal=int(default*4/3)
    big=int(default*5/3)
    title=bigger=int(default*2)
    small=int(default*2/3)
    default=int(default)
    log.info("Default font size: {}".format(default))
    andika="Andika"# not "Andika SIL"
    charis="Charis SIL"
    self.fonts={
            'title':tkinter.font.Font(family=charis, size=title), #Charis
            'instructions':tkinter.font.Font(family=charis,
                                        size=normal), #Charis
            'report':tkinter.font.Font(family=charis, size=small),
            'reportheader':tkinter.font.Font(family=charis, size=small,
                                                # underline = True,
                                                slant = 'italic'
                                                ),
            'read':tkinter.font.Font(family=charis, size=big),
            'readbig':tkinter.font.Font(family=charis, size=bigger,
                                        weight='bold'),
            'small':tkinter.font.Font(family=charis, size=small),
            'default':tkinter.font.Font(family=charis, size=default)
                }
    # print(self.fonts)
    """additional keyword options (ignored if font is specified):
    family - font family i.e. Courier, Times
    size - font size (in points, |-x| in pixels)
    weight - font emphasis (NORMAL, BOLD)
    slant - ROMAN, ITALIC
    underline - font underlining (0 - none, 1 - underline)
    overstrike - font strikeout (0 - none, 1 - strikeout)
    """
def inherit(self,parent=None,attr=None):
    """This function brings these attributes from the parent, to inherit
    from the root window, through all windows, frames, and scrolling frames, etc
    """
    if attr is None:
        attrs=['fonts','theme','debug','wraplength','photo','renderings',
                'program','exitFlag']
    else:
        attrs=[attr]
    if parent==None:
        parent=self.parent
    for attr in attrs:
        if hasattr(parent,attr):
            setattr(self,attr,getattr(parent,attr))
def propagate(self,attr):
    """This function pushes an attribute value to all children with that
    attribute already set.
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
def nfc(x):
    #This makes (pre)composed characters, e.g., vowel and accent in one
    return unicodedata.normalize('NFC', str(x))
def nfd(x):
    #This makes decomposed characters. e.g., vowel + accent
    return unicodedata.normalize('NFD', str(x))
def findpraat():
    log.info("Looking for Praat...")
    spargs={
            # 'stdout':subprocess.PIPE, 'stderr':subprocess.PIPE,
            # 'capture_output' : 'True',
            'shell' : False
            }
    program['praatisthere']=False
    try: #am I on typical Linux?
        praat=subprocess.check_output(["which","praat"], **spargs)
    except Exception as e:
        log.info("No praat found! ({})".format(e))
        try: #am I on typical MS Windows?
            praat=subprocess.check_output(["where.exe","Praat.exe"], **spargs)
        except Exception as e:
            log.info("No Praat.exe found! ({})".format(e))
            try: #am I on typical Mac OS?
                praat=subprocess.check_output(["which","Praat"], **spargs)
            except Exception as e:
                log.info("No Praat found! ({})".format(e))
                return
    praat=praat.decode("utf-8").strip()
    log.info("Praat found at {}".format(praat))
    program['praatisthere']=True
    program['praat']=praat
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
def findhg():
    path=findpath()
    paths=pathseparate(path)
    log.info("path items: {}".format(paths))
    for path in paths:
        if path and file.exists(path):
            log.info("path: {}".format(path))
            array = os.listdir(path)
    log.info("Looking for Mercurial (Hg)...")
    spargs={
            'shell' : False
            }
    program['hgisthere']=False
    try: #am I on typical Linux?
        hg=subprocess.check_output(["which","hg"], **spargs)
    except Exception as e:
        log.info("No Mercurial found! ({})".format(e))
        try: #am I on typical MS Windows?
            hg=subprocess.check_output(["where.exe","Hg.exe"], **spargs)
        except Exception as e:
            log.info("No Hg.exe found! ({})".format(e))
            try: #am I on typical Mac OS?
                hg=subprocess.check_output(["which","Hg"], **spargs)
            except Exception as e:
                log.info("No Mercurial found! ({})".format(e))
                return
    hg=hg.decode("utf-8").strip()
    log.info("Mercurial found at {}".format(hg))
    program['hgisthere']=True
    program['hg']=hg
def praatopen(file,event=None):
    if program['praatisthere']:
        log.info(_("Trying to call Praat at {}...").format(praat))
    else:
        log.info(_("Looks like I couln't find Praat..."))
    #This should use the actual executable found earlier...
    praatargs=[praat, "--open", file]
    try:
        subprocess.Popen(praatargs,shell=False) #not run; continue here
    except Exception as e:
        log.info(_("Call to Praat failed: {}").format(e))
def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt): #ignore Ctrl-C
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    log.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
def setexitflag(self,exitFlag):
    # This is here because it needs to be available to multiple classes
    # when functions may continue after window closure, but GUI shouldn't
    print("Setting window exit flag False (on window creation)!")
    self.exitFlag = exitFlag
    self.protocol("WM_DELETE_WINDOW", lambda s=self:on_quit(s))
def openweburl(url):
    webbrowser.open_new(url)
def ofromstr(x):
    """This interprets a string as a python object, if possible"""
    """This is needed to interpret [x,y] as a list and {x:y} as a dictionary."""
    try:
        return ast.literal_eval(x)
    except (SyntaxError,ValueError) as e:
        log.debug("Assuming ‘{}’ is a string ({})".format(x,e))
        return x
def on_quit(self):
    # Do this when a window closes, so any window functions can know
    # to just stop, rather than trying and throwing an error. This doesn't
    # do anything but set the flag value on exit, the logic to stop needs
    # to be elsewhere, e.g., if `self.exitFlag.istrue(): return`
    def killall():
        self.destroy()
        sys.exit()
    if hasattr(self,'exitFlag'): #only do this if there is an exitflag set
        print("Setting window exit flag True!")
        self.exitFlag.true()
    if type(self) is tkinter.Tk: #exit afterwards if main window
        killall()
    else:
        self.destroy() #do this for everything
def main():
    global program
    log.info("Running main function on {} ({})".format(platform.system(),
                                    platform.platform())) #Don't translate yet!
    root = program['root']=tkinter.Tk()
    #this computer: (this doesn't pick up changes, so just doing it here)
    h = root.winfo_screenheight()
    w = root.winfo_screenwidth()
    wmm = root.winfo_screenmmwidth()
    hmm = root.winfo_screenmmheight()
    #this computer as a ratio of mine, 1080 (286mm) x 1920 (508mm):
    hx=h/1080
    wx=w/1920
    hmmx=hmm/286
    wmmx=wmm/508
    log.info("screen height: {} ({}mm, ratio: {}/{})".format(h,hmm,hx,hmmx))
    log.info("screen width: {} ({}mm, ratio: {}/{})".format(w,wmm,wx,wmmx))
    xmin=min(hx,wx,hmmx,wmmx)
    xmax=max(hx,wx,hmmx,wmmx)
    if xmax-1 > 1-xmin:
        program['scale']=xmax
    else:
        program['scale']=xmin
    if program['scale'] < 1.02 and program['scale'] > 0.98:
        log.info("Probably shouldn't scale in this case (scale: {})".format(
                                                            program['scale']))
        program['scale']=1
    log.info("Largest variance from 1:1 ratio: {} (this will be used to scale "
            "stuff.)".format(program['scale']))
    if platform.system() != 'Linux': #this is only for MS Windows!
        import ctypes
        user32 = ctypes.windll.user32
        screensize = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
        log.info("MS Windows screen size: {}".format(screensize))
    # log.info(root.winfo_class())
    # root.className="azt"
    # root.winfo_class("azt")
    # log.info(root.winfo_class())
    """Translation starts here:"""
    myapp = MainApplication(root,program)
    myapp.mainloop()
    logshutdown() #in logsetup
def mainproblem():
    log.info("Starting up help line...")
    file=logwritelzma(log.filename)
    try: #Make this work whether root has run/still runs or not.
        program['root'].winfo_exists()
        log.info("Root there!")
        errorroot = Window(program['root']) #tkinter.Toplevel(program['root'])
    except:
        errorroot = tkinter.Tk()
        setthemes(errorroot)
        errorroot.theme=errorroot.themes['greygreen']
        errorroot['background']=errorroot.theme['background']
        errorroot.protocol("WM_DELETE_WINDOW", lambda s=errorroot:on_quit(errorroot))
    errorroot.title("Serious Problem!")
    try:
        char="Charis SIL"
        titlefont=tkinter.font.Font(family=char, size=36)
        noticefont=tkinter.font.Font(family=char,size=24)
        defaultfont=tkinter.font.Font(family=char, size=12)
    except:
        titlefont=noticefont=defaultfont=tkinter.font.Font(family=char, size=12)
    l=Label(errorroot,text="Hey! You found a problem! (details and "
            "solution below)",justify='left',font=titlefont)
    l.grid(row=0,column=0)
    if exceptiononload:
        durl=('https://github.com/kent-rasmussen/azt/blob/main/INSTALL.md'
                '#dependencies')
        m=Label(errorroot,text="\nPlease see {}".format(durl),
            justify='left', font=noticefont)
        m.grid(row=1,column=0)
        m.bind("<Button-1>", lambda e: openweburl(durl))
    lcontents=logcontents(log,25)
    addr=program['Email']
    eurl='mailto:{}?subject=Please help with A→Z+T installation'.format(addr)
    eurl+=('&body=Please replace this text with a description of what you '
            'just tried.'.format(file))
    eurl+=("%0d%0aIf the log below doesn't include the text 'Traceback (most "
            "recent call last): ', or if it happened after a longer work "
            "session, please attach "
            "your compressed log file ({})".format(file))
    eurl+='%0d%0a--log info--%0d%0a{}'.format('%0d%0a'.join(lcontents))
    n=Label(errorroot,text="\n\nIf this information doesn't help "
        "you fix this, please click on this text to Email me your log (to {})"
        "".format(addr),justify='left', font=defaultfont)
    n.grid(row=2,column=0)
    n.bind("<Button-1>", lambda e: openweburl(eurl))
    o=Label(errorroot,text="\n\nThe end of {} / {} are below:"
                "\n\n{}".format(log.filename,file,''.join(lcontents)),
                justify='left',
                font=defaultfont)
    o.grid(row=3,column=0)
    o.bind("<Button-1>", lambda e: openweburl(eurl))
    errorroot.mainloop()
    # errorroot.wait_window(errorroot)
    sys.exit()
    exit()
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
    if hasattr(sys,'_MEIPASS') and sys._MEIPASS is not None:
        aztdir=sys._MEIPASS
    else:
        filename = inspect.getframeinfo(inspect.currentframe()).filename
        aztdir = os.path.dirname(os.path.abspath(filename))
    """Not translating yet"""
    log.info('Running {} v{} in {} on {} with loglevel {} at {}'.format(
                                    program['name'],program['version'],aztdir,
                                    platform.uname().node,
                                    loglevel,
                                    datetime.datetime.utcnow().isoformat()))
    transdir=aztdir+'/translations/'
    i18n={}
    i18n['en'] = gettext.translation('azt', transdir, languages=['en_US'])
    i18n['fr'] = gettext.translation('azt', transdir, languages=['fr_FR'])
    findpraat()
    findhg()
    # i18n['fub'] = gettext.azttranslation('azt', transdir, languages=['fub'])
    if exceptiononload:
        mainproblem()
    else:
        try:
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
        m=tkinter.Toplevel()
        m.title("Program Name Here")
        tkinter.Label(m, text='This application checks lexical data, as part '
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
