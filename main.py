#!/usr/bin/env python3
# coding=UTF-8
"""This file runs the actual GUI for lexical file manipulation/checking"""
program={'name':'A→Z+T'}
program['tkinter']=True
program['production']=True #True for making screenshots
program['version']='0.7+w_2' #This is a string...
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
    loglevel=5 #
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
"""Other people's stuff"""
import threading
import itertools
import importlib.util
import collections
from random import randint
if program['tkinter']==True:
    import tkinter #as gui
    import tkinter.font
    import tkinter.scrolledtext
    import tkintermod
    tkinter.CallWrapper = tkintermod.TkErrorCatcher
"""else:
    import kivy
"""
import time
import datetime
import pyaudio
import wave
import unicodedata
# #for some day..…
# from PIL import Image #, ImageTk
#import Image #, ImageTk
import re
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
        filename=file.getfilename()
        if not file.exists(filename):
            log.error("Select a lexical database to check; exiting.")
            exit()
        filedir=file.getfilenamedir(filename)
        """We need this variable to make filenames for files that will be
        imported as python modules. To do that, they need to not have periods
        (.) in their filenames. So we take the base name from the lift file,
        and replace periods with underscores, to make our modules basename."""
        filenamebase=re.sub('\.','_',str(file.getfilenamebase(filename)))
        if not file.exists(filedir):
            log.info(_("Looks like there's a problem with your directory... {}"
                    "\n{}".format(filename,filemod)))
            exit()
        """This and the following bit should probably be in another lift
        class, in the main script. They make non lift-specific changes
        and assumptions about the database."""
        try:
            self.db=lift.Lift(filename,nsyls=nsyls)
        except lift.BadParseError:
            text=_("{} doesn't look like a well formed lift file; please "
                    "try again.").format(filename)
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
        self.defaultfile=file.getdiredurl(filedir,
                                        filenamebase+".CheckDefaults.py")
        self.toneframesfile=file.getdiredurl(filedir,
                                        filenamebase+".ToneFrames.py")
        self.statusfile=file.getdiredurl(filedir,
                                        filenamebase+".VerificationStatus.py")
        self.profiledatafile=file.getdiredurl(filedir,
                                        filenamebase+".ProfileData.py")
        self.adhocgroupsfile=file.getdiredurl(filedir,
                                        filenamebase+".AdHocGroups.py")
        for savefile in [self.defaultfile,self.toneframesfile,self.statusfile,
                        self.profiledatafile,self.adhocgroupsfile]:
            if not file.exists(savefile):
                print(savefile, "doesn't exist!")
        self.imagesdir=file.getimagesdir(filename)
        self.audiodir=file.getaudiodir(filename)
        log.info('self.audiodir: {}'.format(self.audiodir))
        self.reportsdir=file.getreportdir(filename)
        self.reportbasefilename=file.getdiredurl(self.reportsdir, filenamebase)
        self.reporttoaudiorelURL=file.getreldir(self.reportsdir, self.audiodir)
        log.log(2,'self.reportsdir: {}'.format(self.reportsdir))
        log.log(2,'self.reportbasefilename: {}'.format(self.reportbasefilename))
        log.log(2,'self.reporttoaudiorelURL: {}'.format(self.reporttoaudiorelURL))
        # setdefaults.langs(self.db) #This will be done again, on resets
        self.settingsbyfile()
        self.loadsettingsfile(setting='toneframes')
        self.loadsettingsfile(setting='status')
        self.loadsettingsfile(setting='adhocgroups')
        if nsyls is not None:
            self.nsyls=nsyls
        else:
            self.nsyls=2
        self.invalidchars=[' ','...',')','(<field type="tone"><form lang="gnd"><text>'] #multiple characters not working.
        self.invalidregex='( |\.|,|\)|\()+'
        # self.profilelegit=['#','̃','C','N','G','S','V','o'] #In 'alphabetical' order
        self.profilelegit=['#','̃','N','G','S','C','Ṽ','V','d','b','o'] #'alphabetical' order
        """Are we OK without these?"""
        # self.guidtriage() #sets: self.guidswanyps self.guidswops self.guidsinvalid self.guidsvalid
        # self.guidtriagebyps() #sets self.guidsvalidbyps (dictionary keyed on ps)
        self.senseidtriage() #sets: self.senseidswanyps self.senseidswops self.senseidsinvalid self.senseidsvalid
        self.db.languagecodes=self.db.analangs+self.db.glosslangs
        self.db.languagepaths=file.getlangnamepaths(filename,
                                                        self.db.languagecodes)
        setdefaults.fields(self.db) #sets self.pluralname and self.imperativename
        self.initdefaults() #provides self.defaults, list to load/save
        self.cleardefaults() #this resets all to none (to be set below)
        """These two lines can import structured frame dictionaries; do this
        just to make the import, then comment them out again."""
        self.frameregex=re.compile('__') #replace this w/data in frames.
        self.loadsettingsfile(setting='profiledata')
        """I think I need this before setting up regexs"""
        self.guessanalang() #needed for regexs
        log.debug("analang guessed: {} (If you don't like this, change it in "
                    "the menus)".format(self.analang))
        self.maxprofiles=5 # how many profiles to check before moving on to another ps
        self.maxpss=2 #don't automatically give more than two grammatical categories
        self.loadsettingsfile() # overwrites guess above, stored on runcheck
        if self.interfacelang not in [None, getinterfacelang()]:
            #set only when new value is loaded:
            setinterfacelang(self.interfacelang)
            self.parent.maketitle()
        self.langnames()
        self.checkinterpretations() #checks/sets values for self.distinguish
        if 'bfj' in self.db.s:
            bfjvdigraphs=(['ou','ei','ɨʉ','ai']+
            ['óu','éi','ɨ́ʉ','ái']+
            ['òu','èi','ɨ̀ʉ','ài'])
            self.db.s['bfj']['V']=bfjvdigraphs+self.db.s['bfj']['V']
            log.debug(self.db.s['bfj']['V'])
        self.slists() #lift>check segment dicts: s[lang][segmenttype]
        self.setupCVrxs() #creates self.rx dictionaries
        """The line above may need to go after this block"""
        if not hasattr(self,'profilesbysense') or self.profilesbysense == {}:
            log.info("Starting profile analysis at {}".format(time.time()
                                                            -self.start_time))
            log.info("Starting ps-profile: {}-{}".format(self.ps,self.profile))
            self.getprofiles() #creates self.profilesbysense nested dicts
            for var in ['rx','profilesbysense','profilecounts']:
                log.debug("{}: {}".format(var,getattr(self,var)))
            log.info("Middle ps-profile: {}-{}".format(self.ps,self.profile))
            self.storesettingsfile(setting='profiledata')
            log.info("Ending ps-profile: {}-{}".format(self.ps,self.profile))
        self.getprofilestodo()
        self.getpss() #This is a prioritized list of all ps'
        self.setnamesall() #sets self.checknamesall
        if (hasattr(self,'ps') and (self.ps != None) and
            hasattr(self,'profile') and (self.profile != None) and
            hasattr(self,'name') and (self.name != None)):
            self.sortingstatus() #because this won't get set later #>checkdefaults?
        log.info("Done initializing check; running first check check.")
        """Testing Zone"""
        self.checkcheck()
    """Guessing functions"""
    def guessanalang(self):
        langspriority=collections.Counter(self.db.get('lexemelang')+
                                self.db.get('citationlang')).most_common()
        self.analang=langspriority[0][0]
        log.debug(_("Analysis language with the most fields ({}): {} ({})".format(langspriority[0][1],self.analang,langspriority)))
        return
        """if there's only one analysis language, use it."""
        nlangs=len(self.db.analangs)
        log.debug(_("Found {} analangs: {}".format(nlangs,self.db.analangs)))
        if nlangs == 1: # print('Only one analang in database!')
            self.analang=self.db.analangs[0]
            self.analangdefault=self.db.analangs[0] #In case the above gets changed.
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
            elif ((len(self.db.analangs[1]) == 3) and
                    (len(self.db.analangs[0]) != 3)):
                log.debug(_('Looks like I found an iso code for analang! '
                                            '({})'.format(self.db.analangs[1])))
                self.analang=self.db.analangs[1] #assume this is the iso code
            else:
                langspriority=collections.Counter(self.db.get('lexemelang')+
                                        self.db.get('citationlang')).most_common()
                log.debug("All: {}".format(self.db.get('lexemelang')+
                                        self.db.get('citationlang')))
                log.debug(collections.Counter(self.db.get('lexemelang')+
                                        self.db.get('citationlang')))
                log.debug('Found the following analangs: {}'.format(langspriority))
        else: #for three or more analangs, take the first plausible iso code
            for n in range(nlangs):
                if len(self.db.analangs[n]) == 3:
                    self.analang=self.db.analangs[n]
                    log.debug(_('Looks like I found an iso code for analang! '
                                            '({})'.format(self.db.analangs[n])))
                    return
    def guessaudiolang(self):
        """if there's only one audio language, use it."""
        nlangs=len(self.db.audiolangs)
        if nlangs == 1: # print('Only one analang in database!')
            self.audiolang=self.db.audiolangs[0]
            """If there are more than two analangs in the database, check if one
            of the first two is three letters long, and the other isn't"""
        elif nlangs == 2:
            if ((self.analang in self.db.audiolangs[0]) and
                (self.analang not in self.db.audiolangs[1])):
                log.info('Looks like I found an  audiolang!')
                self.audiolang=self.db.audiolangs[0] #assume this is the iso code
            elif ((self.analang in self.db.audiolangs[1]) and
                    (self.analang not in self.db.audiolangs[0])):
                log.info('Looks like I found an iso code for analang!')
                self.audiolang=self.db.audiolangs[1] #assume this is the iso code
        else: #for three or more analangs, take the first plausible iso code
            for n in range(nlangs):
                if self.analang in self.db.analangs[n]:
                    self.audiolang=self.db.audiolangs[n]
                    return
    def guessglosslangs(self):
        """if there's only one gloss language, use it."""
        if len(self.db.glosslangs) == 1:
            log.info('Only one glosslang!')
            self.glosslang=self.db.glosslangs[0]
            self.glosslang2=None
            """if there are two or more gloss languages, just pick the first
            two, and the user can select something else later (the gloss
            languages are not for CV profile analaysis, but for info after
            checking, when this can be reset."""
        elif len(self.db.glosslangs) > 1:
            self.glosslang=self.db.glosslangs[0]
            self.glosslang2=self.db.glosslangs[1]
        else:
            print("Can't tell how many glosslangs!",len(self.db.glosslangs))
    def getpss(self):
        #Why rebuild this here?
        if not hasattr(self,'profilecountsValid'):
            self.profilecountsValid=[]
            for x in [x for x in self.profilecounts if x[1]!='Invalid']:
                self.profilecountsValid.append(x)
        pssdups=[x[2] for x in self.profilecountsValid]
        self.pss=[]
        for ps in pssdups:
            if ps not in self.pss:
                self.pss.append(ps)
    def nextps(self,guess=False):
        """Make this smarter, but for now, just take value from the most
        populous tuple"""
        self.getpss()
        log.debug('Profiles in priority order: {}'.format(self.pss))
        if (guess == True) or (self.ps not in self.pss):
            self.set('ps',self.pss[0])
        else:
            index=self.pss.index(self.ps)
            log.debug("{} ps found in valid pss; "
                    "selecting next one in this list: {}".format(self.ps,
                                                                self.pss))
            self.set('ps',self.pss[index+1])
            if index >= self.maxpss:
                return 1 #We hit the max already, but give a valid profile
    def nextprofile(self,guess=False):
        if len(self.profilecountsValid) >0:
            profiles=[x[1] for x in self.profilecountsValid]
            if (guess == True) or (self.profile not in profiles):
                if self.profile not in profiles:
                    log.debug("{} profile not in valid profiles for "
                                "ps {}.".format(self.profile,self.ps))
                self.set('profile',self.profilecountsValid[0][1])
                if guess == True:
                    log.debug("Guessing {} profile, from valid profiles for "
                                "ps {}: {}.".format(self.profile,self.ps,
                                                    self.profilecountsValid))
            else:
                index=profiles.index(self.profile)
                log.debug("{} profile found in valid profiles for ps {}; "
                            "selecting next one in this list: {}".format(
                            self.profile,self.ps,self.profilecountsValid))
                self.set('profile',self.profilecountsValid[index+1][1])
                if index >= self.maxprofiles:
                    return 1 #We hit the max already, but give a valid profile
        else:
            log.error("For some reason, I don't see any Valid profiles for "
                        "ps {}. This is likely a problem with your syllable "
                        "profile analysis.".format(self.ps))
            self.set('profile',self.profilecounts[0][1])
        self.checkcheck()
    def nextframe(self):
        if len(self.framestodo) == 0:
            self.addframe() #The above should change self.name, if completed.
            return
        if self.name in self.framestodo:
            i=self.framestodo.index(self.name)
            if len(self.framestodo)>i+1:
                self.set('name',self.framestodo[i+1])
            else:
                self.addframe()
        else:
            self.set('name',self.framestodo[0])
        self.checkcheck()
    def guesscheckname(self):
        """Picks the longest name (the most restrictive fiter)"""
        self.set('name',firstoflist(sorted(self.checkspossible,
                                key=lambda s: len(s[0]),reverse=True),
                                othersOK=True)[0])
    def guesstype(self):
        """For now, if type isn't set, start with Vowels."""
        self.set('type','V')
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
            elif xyz == 'gnd':
                self.languagenames[xyz]="Zulgo"
            elif xyz == 'fub':
                self.languagenames[xyz]="Fulfulde"
            elif xyz == 'bfj':
                self.languagenames[xyz]="Chufie’"
            else:
                self.languagenames[xyz]=_("Language with code [{}]").format(xyz) #I need to fix this...
            self.languagenames[None]=None #just so we don't fail on None...
        if (hasattr(self,'adnlangnames') and (self.adnlangnames is not None)):
            for xyz in self.adnlangnames: #overwrite with user specified names
                self.languagenames[xyz]=self.adnlangnames[xyz]
    """User Input functions"""
    def getinterfacelang(self):
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
        if (not hasattr(self,'distinguish')) or (self.distinguish == None):
            self.distinguish={}
        if (not hasattr(self,'interpret')) or (self.interpret == None):
            self.interpret={}
        for var in ['G','N','S','Nwd','d','ː']:
            log.log(5,_("Variable {} current value: {}").format(var,
                                                            self.distinguish))
            if ((var not in self.distinguish) or
                (type(self.distinguish[var]) is not bool)):
                self.distinguish[var]=False
            if var == 'd':
                self.distinguish[var]=False #don't change this default, yet...
            log.log(2,_("Variable {} current value: {}").format(var,
                                                        self.distinguish[var]))
        for var in ['NC','CG','CS','VV','VN']:
            log.log(5,_("Variable {} current value: {}").format(var,
                                                            self.interpret))
            if ((var not in self.interpret) or
                (type(self.interpret[var]) is not str) or
                not(1 <=len(self.interpret[var])<= 2)):
                if (var == 'VV') or (var == 'VN'):
                    self.interpret[var]=var
                else:
                    self.interpret[var]='CC'
                log.log(2,_("Variable {} current value: {}").format(var,
                                                        self.interpret[var]))
        if self.interpret['VV']=='Vː' and self.distinguish['ː']==False:
            self.interpret['VV']='VV'
        log.log(2,"self.distinguish: {}".format(self.distinguish))
    def setSdistinctions(self):
        def submitform():
            change=False
            for type in ['distinguish', 'interpret']:
                for ss in getattr(self,type):
                    log.debug("Variable {} was: {}, now: {}, change: {}"
                            "".format(ss,
                            getattr(self,type)[ss],
                            var[ss].get(),change))
                    if ss in var:
                        if ((ss in getattr(self,type)) and
                                (getattr(self,type)[ss] != var[ss].get())):
                            getattr(self,type)[ss]=var[ss].get()
                            change=True
                        # elif ((ss in self.interpret) and
                        #         (self.interpret[ss] != var[ss].get())):
                        #     self.interpret[ss]=var[ss].get()
                        #     change=True
                log.debug("Variable {} was: {}, now: {}, change: {}"
                            "".format(ss,
                            getattr(self,type)[ss],
                            var[ss].get(),change))
                # if ss=='NCG':
                #     var[ss]=(var['NC'].get() and var['CG'].get())
            log.debug('self.distinguish:',self.distinguish)
            log.debug('self.interpret:',self.interpret)
            if change == True:
                log.info('There was a change; we need to redo the analysis now.')
                self.storesettingsfile()
                if self.debug != True:
                    self.reloadprofiledata()
            self.runwindow.destroy()
        def buttonframeframe(self):
            ss=self.runwindow.options['ss']
            self.runwindow.frames[ss]=Frame(self.runwindow.scroll.content)
            self.runwindow.frames[ss].grid(row=self.runwindow.options['row'],
                        column=self.runwindow.options['column'],sticky='ew',
                        padx=self.runwindow.options['padx'],
                        pady=self.runwindow.options['pady'])
            Label(self.runwindow.frames[ss],text=self.runwindow.options['text'],
                    justify=tkinter.LEFT,anchor='c'
                    ).grid(row=0,
                            column=self.runwindow.options['column'],
                            sticky='ew',
                            padx=self.runwindow.options['padx'],
                            pady=self.runwindow.options['pady'])
            RadioButtonFrame(self.runwindow.frames[ss],var=var[ss],
            opts=self.runwindow.options['opts']).grid(row=0,column=1)
            self.runwindow.options['row']+=1
        self.getrunwindow()
        self.checkinterpretations()
        var={}
        for ss in self.distinguish: #Should be already set.
            var[ss] = tkinter.BooleanVar()
            var[ss].set(self.distinguish[ss])
            print(ss, self.distinguish[ss])
        for ss in self.interpret: #This should already be set, even by default
            var[ss] = tkinter.StringVar()
            var[ss].set(self.interpret[ss])
            print(ss, self.interpret[ss])
        self.runwindow.options={}
        self.runwindow.options['row']=0
        self.runwindow.options['padx']=50
        self.runwindow.options['pady']=10
        self.runwindow.options['column']=0
        """Page title and instructions"""
        self.runwindow.title(_("Set Parameters for Segment Interpretation"))
        title=_("Interpret {} Segments"
                ).format(self.languagenames[self.analang])
        titl=Label(self.runwindow,text=title,font=self.fonts['title'],
                justify=tkinter.LEFT,anchor='c')
        titl.grid(row=self.runwindow.options['row'],
                    column=self.runwindow.options['column'],sticky='ew',
                    padx=self.runwindow.options['padx'],
                    pady=self.runwindow.options['pady'])
        self.runwindow.options['row']+=1
        text=_("Here you can view and set parameters that change how {} "
        "interprets {} segments \n(consonant and vowel glyphs/characters)"
                ).format(self.program['name'],self.languagenames[self.analang])
        instr=Label(self.runwindow,text=text,
                justify=tkinter.LEFT,anchor='c')
        instr.grid(row=self.runwindow.options['row'],
                    column=self.runwindow.options['column'],sticky='ew',
                    padx=self.runwindow.options['padx'],
                    pady=self.runwindow.options['pady'])
        """The rest of the page"""
        self.runwindow.scroll=ScrollingFrame(self.runwindow)
        self.runwindow.scroll.grid(row=2,column=0)
        self.runwindow.frames={}
        """I considered offering these to the user conditionally, but I don't
        see a subset of them that would only be relevant when another is
        selected. For instance, a user may NOT want to distinguish all Nasals,
        yet distinguish word final nasals. Or CG sequences, but not other G's
        --or distinguish G, but leave as CG (≠C). So I think these are all
        independent boolean selections."""
        self.runwindow.options['ss']='N'
        self.runwindow.options['text']=_('Do you want to distinguish '
                                        'all Nasals (N) \nfrom '
                                        'other (simple/single) consonants?')
        self.runwindow.options['opts']=[(True,'N≠C'),(False,'N=C')]
        buttonframeframe(self)
        self.runwindow.options['ss']='Nwd'
        self.runwindow.options['text']=_('Do you want to distinguish Word '
                                        'Final Nasals (N#) \nfrom other word '
                                        'final consonants?')
        self.runwindow.options['opts']=[(True,'N#≠C#'),(False,'N#=C#')]
        buttonframeframe(self)
        self.runwindow.options['ss']='G'
        self.runwindow.options['text']=_('Do you want to distinguish '
                                        'all Glides (G) \nfrom '
                                        'other (simple/single) consonants?')
        self.runwindow.options['opts']=[(True,'G≠C'),(False,'G=C')]
        buttonframeframe(self)
        self.runwindow.options['ss']='S'
        self.runwindow.options['text']=_('Do you want to distinguish '
                                        'all Non-Nasal/Glide Sonorants (S) '
                                    '\nfrom other (simple/single) consonants?')
        self.runwindow.options['opts']=[(True,'S≠C'),(False,'S=C')]
        buttonframeframe(self)
        self.runwindow.options['ss']='NC'
        self.runwindow.options['text']=_('How do you want to interpret '
                                        '\nNasal-Consonant (NC) sequences?')
        self.runwindow.options['opts']=[('NC','NC=NC (≠C, ≠CC)'),
                                    ('C','NC=C (≠NC, ≠CC)'),
                                    ('CC','NC=CC (≠NC, ≠C)')
                                    ]
        buttonframeframe(self)
        self.runwindow.options['ss']='CG'
        self.runwindow.options['text']=_('How do you want to interpret '
                                        '\nConsonant-Glide (CG) sequences?')
        self.runwindow.options['opts']=[('CG','CG=CG (≠C, ≠CC)'),
                                    ('C','CG=C (≠CG, ≠CC)'),
                                    ('CC','CG=CC (≠CG, ≠C)')]
        buttonframeframe(self)
        self.runwindow.options['ss']='VN'
        self.runwindow.options['text']=_('How do you want to interpret '
                                        '\nVowel-Nasal (VN) sequences?')
        self.runwindow.options['opts']=[('VN','VN=VN (≠Ṽ)'),
                                    ('Ṽ','VN=Ṽ (≠VN)')]
        buttonframeframe(self)
        """Submit button, etc"""
        self.runwindow.frame2d=Frame(self.runwindow.scroll.content)
        self.runwindow.frame2d.grid(row=self.runwindow.options['row'],
                    column=self.runwindow.options['column'],sticky='ew',
                    padx=self.runwindow.options['padx'],
                    pady=self.runwindow.options['pady'])
        sub_btn=Button(self.runwindow.frame2d,text = 'Use these settings',
                  command = submitform)
        sub_btn.grid(row=0,column=1,sticky='nw',
                    pady=self.runwindow.options['pady'])
        nbtext=_("If you make changes, this button==> \nwill "
                "restart the program to reanalyze your data, \nwhich will "
                "take some time.")
        sub_nb=Label(self.runwindow.frame2d,text = nbtext, anchor='e')
        sub_nb.grid(row=0,column=0,sticky='e',
                    pady=self.runwindow.options['pady'])
        self.runwindow.waitdone()
    def addmodadhocsort(self):
        def submitform():
            if profilevar.get() == "":
                log.debug("Give a name for this adhoc sort group!")
                return
            self.runwindow.destroy()
            self.senseidstosort=[]
            for var in [x for x in vars if len(x.get()) >1]:
                log.log(2,"var {}: {}".format(vars.index(var),var.get()))
                self.senseidstosort.append(var.get())
            log.log(2,"ids: {}".format(self.senseidstosort))
            self.set('profile',profilevar.get())
            #Add to dictionaries before updating them below
            self.makeadhocgroupsdict() # in case the variable or ps isn't there.
            self.adhocgroups[self.ps][self.profile]=self.profilesbysense[
                                    self.ps][self.profile]=self.senseidstosort
            self.makecountssorted() #we need these to show up in the counts.
            self.storesettingsfile(setting='profiledata')#since we changed this.
            #so we don't have to do this again after each profile analysis
            self.storesettingsfile(setting='adhocgroups')
            self.checkcheck()
        self.getrunwindow()
        if self.profile in [x[1] for x in self.profilecountsValid]:
            title=_("New Ad Hoc Sort Group for {} Group".format(self.ps))
        else:
            title=_("Modify Existing Ad Hoc Sort Group for {} Group".format(
                                                                    self.ps))
        self.runwindow.title(title)
        padx=50
        pady=10
        Label(self.runwindow,text=title,font=self.fonts['title'],
                ).grid(row=0,column=0,sticky='ew')
        allpssensids=list()
        for profile in self.profilesbysense[self.ps]:
            allpssensids+=list(self.profilesbysense[self.ps][profile])
        allpssensids=list(dict.fromkeys(allpssensids))
        if len(allpssensids)>70:
            self.runwindow.waitdone()
            text=_("This is a large group ({})! Are you in the right "
                    "grammatical category?".format(len(allpssensids)))
            log.error(text)
            w=Label(self.runwindow,text=text)
            w.grid(row=1,column=0,sticky='ew')
            b=Button(self.runwindow, text="OK", command=w.destroy, anchor='c')
            b.grid(row=2,column=0,sticky='ew')
            self.runwindow.wait_window(w)
            w.destroy()
        if not self.runwindow.winfo_exists():
            return
        else:
            self.runwindow.wait()
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
                "".format(self.ps))
        Label(self.runwindow,text=text).grid(row=1,column=0,sticky='ew')
        qframe=Frame(self.runwindow)
        qframe.grid(row=2,column=0,sticky='ew')
        text=_("What do you want to call this group for sorting {} words?"
                "".format(self.ps))
        Label(qframe,text=text).grid(row=0,column=0,sticky='ew',pady=20)
        if ((set(self.profilelegit).issuperset(self.profile)) or
                                            (self.profile == "Invalid")):
            default=None
        else:
            default=self.profile
        profilevar=tkinter.StringVar(value=default)
        namefield = EntryField(qframe,textvariable=profilevar)
        namefield.grid(row=0,column=1)
        text=_("Select the words below that you want in this group, then click "
                "==>".format(self.ps))
        Label(qframe,text=text).grid(row=1,column=0,sticky='ew',pady=20)
        sub_btn=Button(qframe,text = _("OK"),
                  command = submitform,anchor ='c')
        sub_btn.grid(row=1,column=1,sticky='w')
        vars=list()
        row=0
        scroll=ScrollingFrame(self.runwindow)
        for id in allpssensids:
            log.debug("id: {}; index: {}; row: {}".format(id,
                                                    allpssensids.index(id),row))
            idn=allpssensids.index(id)
            vars.append(tkinter.StringVar())
            if id in self.profilesbysense[self.ps][self.profile]:
                vars[idn].set(id)
            else:
                vars[idn].set(0)
            framed=self.getframeddata(id, noframe=True)
            log.debug("forms: {}".format(framed['formatted']))
            CheckButton(scroll.content, text = framed['formatted'],
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
                                    self.ps,
                                    self.languagenames[lang]))
                ok=_('Use this form')
            elif lang in self.db.analangs:
                return
            else:
                text=_("What does {} ({}) mean in {}?".format(
                                            self.runwindow.form[self.analang],
                                            self.ps,
                                            self.languagenames[lang]))
                ok=_('Use this {} gloss for {}'.format(self.languagenames[lang],
                                            self.runwindow.form[self.analang]))
                self.runwindow.glosslangs.append(lang)
            getform=Label(self.runwindow.frame2,text=text,
                                                font=self.fonts['read'])
            getform.grid(row=0,column=0,padx=padx,pady=pady)
            form[lang]=tkinter.StringVar()
            formfield = EntryField(self.runwindow.frame2,
                                    textvariable=form[lang])
            formfield.grid(row=1,column=0)
            sub_btn=Button(self.runwindow.frame2,text = ok,
                      command = lambda x=lang:submitform(x),anchor ='c')
            sub_btn.grid(row=2,column=0,sticky='')
            if lang != self.analang:
                sub_btnNo=Button(self.runwindow.frame2,
                        text = _('Skip {} gloss').format(
                            self.languagenames[lang]),
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
        title=_("Add a {} {} morpheme to the dictionary").format(self.ps,
                            self.languagenames[self.analang])
        Label(self.runwindow,text=title,font=self.fonts['title'],
                justify=tkinter.LEFT,anchor='c'
                ).grid(row=0,column=0,sticky='ew',padx=padx,pady=pady)
        # Run the above script (makewindow) for each language, analang first.
        # The user has a chance to enter a gloss for any gloss language
        # already in the datbase, and to skip any as needed/desired.
        for lang in [self.analang]+self.db.glosslangs:
            makewindow(lang)
        """get the new senseid back from this function, which generates it"""
        senseid=self.db.addentry(ps=self.ps,analang=self.analang,
                        glosslangs=self.runwindow.glosslangs,
                        form=self.runwindow.form)
        # Update profile information in the running instance, and in the file.
        self.getprofileofsense(senseid)
        self.updatecounts()
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
            namevar=name.get()
            # self.name is set here --I need it to correctly test the frames
            # created...
            self.nameori=self.name
            self.name=str(namevar)
            if self.name is '':
                text=_('Sorry, empty name! \nPlease provide at least \na frame '
                    'name, to distinguish it \nfrom other frames.')
                print(re.sub('\n','',text))
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
            print('self.name:',self.name)
            if self.toneframes is None:
                self.toneframes={}
            if not self.ps in self.toneframes:
                self.toneframes[self.ps]={}
            self.toneframes[self.ps][self.name]={}
            """Define the new frame"""
            frame=self.toneframes[self.ps][self.name]
            langs=[self.analang, self.glosslang]
            if self.glosslang2 != None:
                langs+=[self.glosslang2]
            for lang in langs:
                db['before'][lang]['text']=db['before'][lang][
                                                            'entryfield'].get()
                db['after'][lang]['text']=db['after'][lang][
                                                            'entryfield'].get()
                frame[lang]=str(
                    db['before'][lang]['text']+'__'+db['after'][lang]['text'])
            senseid=self.gimmesenseid()
            # This needs self.toneframes
            framed=self.getframeddata(senseid,truncdefn=True) #after defn above, before below!
            #At this point, remove this frame (in case we don't submit it)
            del self.toneframes[self.ps][self.name]
            self.name=self.nameori
            print(frame,framed)
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
                    text="Examples for {} tone frame".format(namevar),
                    font=self.fonts['readbig'],
                    justify=tkinter.LEFT,anchor='w')
            lt.grid(row=row,column=columnleft,sticky='w',columnspan=2,
                    padx=padx,pady=pady)
            for lang in langs:
                row+=1
                print('frame[{}]:'.format(lang),frame[lang])
                tf[lang]=('form[{}]: {}'.format(lang,frame[lang]))
                tfd[lang]=('(ex: '+framed[lang]+')')
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
            """toneframes={'Nom':
                            {'name/location (e.g.,"By itself")':
                                {'analang.xyz': '__',
                                'glosslang.xyz': 'a __'},
                                'glosslang2.xyz': 'un __'},
                        }   }
            """
            row+=1
            stext=_('Use {} tone frame'.format(namevar))
            sub_btn=Button(self.addwindow.framechk,text = stext,
                      command = lambda x=frame,n=namevar: submit(x,n))
            sub_btn.grid(row=row,column=columnleft,sticky='w')
            self.addwindow.scroll.windowsize() #make sure scroll's big enough
        def unchk(event):
            #This is here to keep people from thinking they are approving what's
            #next to this button, in case any variable has been changed.
            if hasattr(self.addwindow,'framechk'):
                self.addwindow.framechk.destroy()
        def submit(frame,name):
            # Having made and unset these, we now reset and write them to file.
            self.set('name',name)
            self.toneframes[self.ps][self.name]=frame
            self.storesettingsfile(setting='toneframes')
            self.addwindow.destroy()
            self.checkcheck()
        self.addwindow=Window(self.frame, title=_("Define a New Tone Frame"))
        self.addwindow.scroll=ScrollingFrame(self.addwindow)
        self.addwindow.frame1=Frame(self.addwindow.scroll.content)
        self.addwindow.frame1.grid(row=0,column=0)
        row=0
        columnleft=0
        columnword=1
        columnright=2
        namevar=tkinter.StringVar()
        """Text and fields, before and after, dictionaries by language"""
        db={}
        langs=[self.analang, self.glosslang]
        if self.glosslang2 != None:
            langs+=[self.glosslang2]
        for context in ['before','after']:
            db[context]={}
            for lang in langs:
                db[context][lang]={}
                db[context][lang]['text']=tkinter.StringVar()
        t=(_("Add {} Tone Frame").format(self.ps))
        Label(self.addwindow.frame1,text=t+'\n',font=self.fonts['title']
                ).grid(row=row,column=columnleft,columnspan=3)
        row+=1
        t=_("What do you want to call the tone frame ?")
        finst=Frame(self.addwindow.frame1)
        finst.grid(row=row,column=0)
        Label(finst,text=t).grid(row=0,column=columnleft,sticky='e')
        name = EntryField(finst,textvariable=namevar)
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
                                textvariable=db['before'][lang]['text'],
                                justify='right')
            db['before'][lang]['entryfield'].grid(row=langrow,
                                        column=columnleft,sticky='e')
            langrow+=1
            Label(f[lang],text=ta[lang]).grid(row=langrow,
                    column=columnleft,sticky='e')
            Label(f[lang],text='word',padx=0,pady=0).grid(row=langrow,
                    column=columnword)
            db['after'][lang]['entryfield'] = EntryField(f[lang],
                    textvariable=db['after'][lang]['text'],
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
        self.set('fs',choice,window)
        self.soundcheckrefresh()
    def setsoundformat(self,choice,window):
        self.set('sample_format',choice,window)
        self.soundcheckrefresh()
    def getsoundformat(self):
        log.info("Asking for audio format...")
        window=Window(self.frame, title=_('Select Audio Format'))
        Label(window.frame, text=_('What audio format do you '
                                    'want to work with?')
                ).grid(column=0, row=0)
        buttonFrame1=ButtonFrame(window.frame,
                                self.sample_formats,self.setsoundformat,
                                window
                                )
        buttonFrame1.grid(column=0, row=1)
    def getsoundhz(self):
        log.info("Asking for sampling frequency...")
        window=Window(self.frame, title=_('Select Sampling Frequency'))
        Label(window.frame, text=_('What sampling frequency you '
                                    'want to work with?')
                ).grid(column=0, row=0)
        buttonFrame1=ButtonFrame(window.frame,
                                self.fss,self.setsoundhz,
                                window
                                )
        buttonFrame1.grid(column=0, row=1)
    def setsoundcardindex(self,choice,window):
        self.set('audio_card_index',choice,window)
        self.soundcheckrefresh()
    def setsoundcardoutindex(self,choice,window):
        self.set('audioout_card_index',choice,window)
        self.soundcheckrefresh()
    def getsoundcardindex(self):
        log.info("Asking for input sound card...")
        window=Window(self.frame, title=_('Select Input Sound Card'))
        Label(window.frame, text=_('What sound card do you '
                                    'want to record sound with with?')
                ).grid(column=0, row=0)
        buttonFrame1=ButtonFrame(window.frame,
                                self.audio_card_indexes,self.setsoundcardindex,
                                window
                                )
        buttonFrame1.grid(column=0, row=1)
    def getsoundcardoutindex(self):
        log.info("Asking for output sound card...")
        window=Window(self.frame, title=_('Select Output Sound Card'))
        Label(window.frame, text=_('What sound card do you '
                                    'want to play sound with?')
                ).grid(column=0, row=0)
        buttonFrame1=ButtonFrame(window.frame,
                    self.audioout_card_indexes,self.setsoundcardoutindex,
                    window
                    )
        buttonFrame1.grid(column=0, row=1)
    """Set User Input"""
    def set(self,attribute,choice,window=None,refresh=True):
        #Normally, pass the attribute through the button frame,
        #otherwise, don't set window (which would be destroyed)
        #Set refresh=False (or anything but True) to not redo the main window
        #afterwards. Do this to save time if you are setting multiple variables.
        log.info("Setting {} variable with value: {}".format(attribute,choice))
        if window != None:
            window.destroy()
        if getattr(self,attribute) != choice: #only set if different
            setattr(self,attribute,choice)
            """If there's something getting reset that shouldn't be, remove it
            from self.defaultstoclear[attribute]"""
            self.cleardefaults(attribute)
            if attribute == 'ps': #so we don't have to keep resetting this
                self.getprofilestodo()
            if attribute == 'profile': #so we don't have to keep resetting this
                self.getframestodo()
            if attribute == 'name' and self.type == 'T':
                self.settonevariablesbypsprofile() #only on changing tone frame
            if (attribute not in ['fs','sample_format','audio_card_index']
                                                        and refresh == True):
                self.checkcheck()
            if attribute in ['analang', 'interpret','distinguish']: #do the last two cause problems?
                self.reloadprofiledata()
        else:
            log.debug(_('No change: {} == {}'.format(attribute,choice)))
    def setinterfacelangwrapper(self,choice,window):
        setinterfacelang(choice) #change the UI *ONLY*; no object attributes
        file.writeinterfacelangtofile(choice) #>ui_lang.py, for startup
        self.set('interfacelang',choice,window) #set variable for the future
        self.storesettingsfile() #>xyz.CheckDefaults.py
        self.parent.maketitle() #because otherwise, this stays as is...
        self.checkcheck()
    def setprofile(self,choice,window):
        self.set('profile',choice,window)
    def settype(self,choice,window):
        if not set(self.profilelegit).issuperset(self.profile):
            self.nextprofile(guess=True)
        self.set('type',choice,window)
    def setanalang(self,choice,window):
        self.set('analang',choice,window)
        self.reloadprofiledata()
    def setS(self,choice,window):
        self.set('subcheck',choice,window)
    def setcheck(self,choice,window):
        self.set('name',choice,window)
    def setglosslang(self,choice,window):
        self.set('glosslang',choice,window)
    def setglosslang2(self,choice,window):
        self.set('glosslang2',choice,window)
    def setps(self,choice,window):
        self.set('ps',choice,window)
    def setexamplespergrouptorecord(self,choice,window):
        self.set('examplespergrouptorecord',choice,window)
    def getsubcheck(self):
        log.info("this sets the subcheck")
        if self.type == "V":
            windowV=Window(self.frame,title=_('Select Vowel'))
            self.getV(window=windowV)
            windowV.wait_window(window=windowV)
        if self.type == "C":
            windowC=Window(self.frame,title=_('Select Consonant'))
            self.getC(windowC)
            self.frame.wait_window(window=windowC)
        if self.type == "CV":
            CV=''
            for self.type in ['C','V']:
                self.getsubcheck()
                CV+=self.subcheck
            self.subcheck=CV
            self.type = "CV"
            self.checkcheck()
    def getps(self):
        log.info("Asking for ps...")
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
    def getprofile(self):
        log.info("Asking for profile...")
        window=Window(self.frame,title=_('Select Syllable Profile'))
        if self.profilesbysense[self.ps] is None: #likely never happen...
            Label(window.frame,
            text=_('Error: please set Grammatical category with profiles '
                    'first!')+' (not '+str(self.ps)+')'
            ).grid(column=0, row=0)
        else:
            Label(window.frame, text=_('What ({}) syllable profile do you '
                                    'want to work with?'.format(self.ps))
                                    ).grid(column=0, row=0)
            optionslist = [(x[1],x[0]) for x in self.profilecountsValidwAdHoc]
            window.scroll=Frame(window.frame)
            window.scroll.grid(column=0, row=1)
            buttonFrame1=ScrollingButtonFrame(window.scroll,
                                    optionslist,self.setprofile,
                                    window
                                    )
            buttonFrame1.grid(column=0, row=0)
    def gettype(self):
        print(_("Asking for check type"))
        window=Window(self.frame,title=_('Select Check Type'))
        types=[]
        x=0
        for type in self.checknamesall:
            types.append({})
            types[x]['name']=self.typedict[type]['pl']
            types[x]['code']=type
            x+=1
        Label(window.frame, text=_('What part of the sound system do you '
                                    'want to work with?')
            ).grid(column=0, row=0)
        buttonFrame1=ButtonFrame(window.frame,types,self.settype,window)
        buttonFrame1.grid(column=0, row=1)
    """Settings to and from files"""
    def initdefaults(self):
        """Some of these defaults should be reset when setting another field.
        These are listed under that other field. If no field is specified
        (e.g., on initialization), then do all the fields with None key (other
        fields are NOT saved to file!).
        These are check related defaults; others in lift.get"""
        self.loadtypedict()
        self.defaultstoclear={'ps':[
                            'profile' #do I want this?
                            # 'name',
                            # 'subcheck'
                            ],
                        'analang':[
                            'glosslang',
                            'glosslang2',
                            'ps',
                            'profile',
                            'type',
                            'name',
                            'subcheck'
                            ],
                        'interfacelang':[],
                        'glosslang':[],
                        'glosslang2':[],
                        'name':[],
                        'subcheck':[
                            'regexCV'
                            ],
                        'profile':[
                            # 'name'
                            ],
                        'type':[
                            'name',
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
                        'exs':[],
                        'maxprofiles':[]
                        }
    def settingsbyfile(self):
        #Here we set which settings are stored in which files
        self.settings={'defaults':{
                            'file':'defaultfile',
                            'attributes':['analang',
                                'glosslang',
                                'glosslang2',
                                'audiolang',
                                'ps',
                                'profile',
                                'type',
                                'name',
                                'regexCV',
                                'subcheck',
                                'additionalps',
                                'entriestoshow',
                                'additionalprofiles',
                                'sample_format',
                                'fs',
                                'audio_card_index',
                                'audioout_card_index',
                                'interfacelang',
                                'examplespergrouptorecord',
                                'distinguish',
                                'interpret',
                                'adnlangnames',
                                'exs',
                                'maxprofiles'
                                ]},
            'profiledata':{
                                'file':'profiledatafile',
                                'attributes':[
                                    "profilecounts","profilecountInvalid",
                                    "scount",
                                    "sextracted",
                                    "profilesbysense",
                                    ]},
            'status':{
                                'file':'statusfile',
                                'attributes':['status']},
            'adhocgroups':{
                                'file':'adhocgroupsfile',
                                'attributes':['adhocgroups']},
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
    def reloadprofiledata(self):
        self.storesettingsfile()
        file.remove(self.profiledatafile)
        self.restart()
    def reloadstatusdata(self):
        self.storesettingsfile()
        file.remove(self.statusfile)
        #Call fn here.
        self.settingsbyfile(setting='status')
    def loadtypedict(self):
        """I just need this to load once somewhere..."""
        self.typedict={
                'V':{'sg':_('Vowel'),'pl':_('Vowels')},
                'C':{'sg':_('Consonant'),'pl':_('Consonants')},
                'CV':{'sg':_('Consonant-Vowel combination'),'pl':_('Consonant-Vowel combinations')},
                'T':{'sg':_('Tone'),'pl':_('Tones')},
                }
    def storesettingsfile(self,setting='defaults'):
        fileattr=self.settings[setting]['file']
        if hasattr(self,fileattr):
            filename=getattr(self,fileattr)
        self.f = open(filename, "w", encoding='utf-8')
        for s in self.settings[setting]['attributes']:
            if hasattr(self,s):
                v=getattr(self,s)
                if v != None:
                    self.f.write(s+'=')
                    pprint.pprint(v,stream=self.f)
                    log.log(3,"{}={} stored in {}.".format(s,v,filename))
                else:
                    log.log(3,"{}={}! Not stored in {}.".format(s,v,filename))
        self.f.close()
    def loadsettingsfile(self,setting='defaults'):
        fileattr=self.settings[setting]['file']
        if hasattr(self,fileattr):
            filename=getattr(self,fileattr)
        try:
            log.debug("Trying for {} settings in {}".format(setting, filename))
            spec = importlib.util.spec_from_file_location(setting,filename)
            module = importlib.util.module_from_spec(spec)
            #If this fails, check your file syntax carefully!
            # you may need coding=UTF-8 run run it for syntax errors
            sys.modules[setting] = module
            spec.loader.exec_module(module)
            for s in self.settings[setting]['attributes']:
                if hasattr(module,s):
                    log.debug("Found attribute {} with value {}".format(s,
                                getattr(module,s)))
                    setattr(self,s,getattr(module,s))
        except:
            log.error("Problem importing {}".format(filename))
            for s in self.settings[setting]['attributes']:
                log.log(3,"looking for self.{}".format(s))
                if hasattr(self,s):
                    log.log(3,"Using {}: {}".format(s,getattr(self,s)))
    def makeadhocgroupsdict(self, ps=None):
        # self.ps and self.profile should be set when this is called
        if ps == None:
            ps=self.ps
        if not hasattr(self,'adhocgroups'):
            self.adhocgroups={}
        if ps not in self.adhocgroups:
            self.adhocgroups[ps]={}
    def makestatusdict(self):
        # This depends on self.ps, self.profile, and self.name
        # This operates for exactly one context: wherever it is called.
        # Do this only where needed, when needed!
        changed=False
        if self.type not in self.status:
            self.status[self.type]={}
            changed=True
        if self.ps not in self.status[self.type]:
            self.status[self.type][self.ps]={}
            changed=True
        if self.profile not in self.status[self.type][self.ps]:
            self.status[self.type][self.ps][self.profile]={}
            changed=True
        if self.name not in self.status[self.type][self.ps][self.profile]:
            self.status[self.type][self.ps][self.profile][self.name]={}
            changed=True
        if type(self.status[self.type][self.ps][self.profile][self.name
                                                                    ]) is list:
            log.info("Updating {}-{} status dict to new schema".format(
                                                        self.profile,self.name))
            dn=self.status[self.type][self.ps][self.profile][self.name]
            self.status[self.type][self.ps][self.profile][self.name]={}
            self.status[self.type][self.ps][self.profile][self.name]['done']=dn
            changed=True
        for key in ['groups','done']:
            if key not in self.status[self.type][self.ps][self.profile][
                                                                self.name]:
                log.info("Adding {} key to {}-{} status dict".format(
                                                key,self.profile,self.name))
                self.status[self.type][self.ps][self.profile][self.name][
                                                                key]=list()
                changed=True
        if 'tosort' not in self.status[self.type][self.ps][self.profile][
                                                                self.name]:
            log.info("Adding tosort key to {}-{} status dict".format(
                                                key,self.profile,self.name))
            self.status[self.type][self.ps][self.profile][self.name][
                                                                'tosort']=True
            changed=True
        for key in ['groups','done']:
            for invalid in ['',None]:
                if invalid in self.status[self.type][self.ps][self.profile][
                                                                self.name][key]:
                    self.status[self.type][self.ps][self.profile][
                                                self.name][key].remove(invalid)
                    changed=True
        if changed == True:
            log.info("Saving status dict to file")
            self.storesettingsfile(setting='status')
    def updatestatus(self,verified=False):
        #This function updates the status variable, not the lift file.
        self.makestatusdict()
        if verified == True:
            if self.subcheck not in (
                self.status[self.type][self.ps][self.profile][self.name][
                                                                    'done']):
                self.status[self.type][self.ps][self.profile][self.name][
                                                'done'].append(self.subcheck)
            else:
                log.info("Tried to set {} verified in {} {} {} {} but it was "
                        "already there, and we're not done with the {} frame."
                        "".format(self.subcheck,self.type,
                        self.ps,self.profile,self.name,self.name))
        if verified == False:
            if self.subcheck in (
                            self.status[self.type][self.ps][self.profile]
                            [self.name]['done']):
                self.status[self.type][self.ps][self.profile][self.name
                                                ]['done'].remove(self.subcheck)
            else:
                print("Tried to set",self.subcheck,"UNverified in",self.type,
                        self.ps,self.profile,self.name,"but it wasn't "
                        "there.")
        self.storesettingsfile(setting='status')
    """Get from LIFT database functions"""
    def addpstoprofileswdata(self):
        if self.ps not in self.profilesbysense:
            self.profilesbysense[self.ps]={}
    def addprofiletoprofileswdata(self):
        if self.profile not in self.profilesbysense[self.ps]:
            self.profilesbysense[self.ps][self.profile]=[]
    def addtoprofilesbysense(self,senseid):
        self.addpstoprofileswdata()
        self.addprofiletoprofileswdata()
        self.profilesbysense[self.ps][self.profile]+=[senseid]
    def updatecounts(self):
        self.getscounts()
        self.makecountssorted()
    def getscounts(self):
        """This depends on self.sextracted, from getprofiles"""
        self.scount={}
        for ps in self.db.pss:
            self.scount[ps]={}
            for s in self.rx:
                self.scount[ps][s]=sorted([(x,self.sextracted[ps][s][x])
                    for x in self.sextracted[ps][s]],key=lambda x:x[1],reverse=True)
    def getprofileofsense(self,senseid):
        #Convert to iterate over local variables
        profileori=self.profile #We iterate across this here
        psori=self.ps #We iterate across this here
        forms=self.db.citationorlexeme(senseid=senseid,lang=self.analang)
        if forms == []:
            self.profile='Invalid'
            for self.ps in self.db.get('ps',senseid=senseid):
                self.addtoprofilesbysense(senseid)
            self.ps=psori
            return
        for form in forms:
            self.profile=self.profileofform(form)
            if not set(self.profilelegit).issuperset(self.profile):
                self.profile='Invalid'
            for self.ps in self.db.get('ps',senseid=senseid):
                self.addtoprofilesbysense(senseid)
        self.profile=profileori
        self.ps=psori
        return firstoflist(forms)
    def getprofiles(self):
        self.profileswdatabyentry={}
        self.profilesbysense={}
        self.profilesbysense['Invalid']=[]
        self.profiledguids=[]
        self.profiledsenseids=[]
        self.sextracted={} #Will store matching segments here
        for ps in self.db.pss:
            self.sextracted[ps]={}
            for s in self.rx:
                self.sextracted[ps][s]={}
        todo=len(self.db.senseids)
        x=0
        for senseid in self.db.senseids:
            x+=1
            form=self.getprofileofsense(senseid)
            if x % 10 is 0:
                log.debug("{}: {}; {}".format(str(x)+'/'+str(todo),form,
                                            self.profile))
        #Convert to iterate over local variables
        psori=self.ps #We iterate across this here
        self.makeadhocgroupsdict() #if no file, before iterating over variable
        for self.ps in self.adhocgroups:
            self.makeadhocgroupsdict() #in case there is no ps key
            for adhoc in self.adhocgroups[self.ps]:
                log.debug("Adding {} to {} ps-profile: {}".format(adhoc,self.ps,
                                            self.adhocgroups[self.ps][adhoc]))
                self.addpstoprofileswdata() #in case the ps isn't already there
                #copy over stored values:
                self.profilesbysense[self.ps][adhoc]=self.adhocgroups[
                                                                self.ps][adhoc]
                log.debug("resulting profilesbysense: {}".format(
                                        self.profilesbysense[self.ps][adhoc]))
        self.ps=psori
        self.updatecounts()
        print('Done:',time.time()-self.start_time)
        if self.debug==True:
            for ps in self.profilesbysense:
                for profile in self.profilesbysense[ps]:
                    log.debug("ps: {}; profile: {} ({})".format(ps,profile,
                            len(self.profilesbysense[ps][profile])))
    def slists(self):
        """This sets up the lists of segments, by types. For the moment, it
        just pulls from the segment types in the lift database."""
        if not hasattr(self,'s'):
            self.s={}
        for lang in self.db.analangs:
            if lang not in self.s:
                self.s[lang]={}
            """These should always be there, no matter what"""
            for sclass in self.db.s[lang]: #Just populate each list now
                self.s[lang][sclass]=self.db.s[lang][sclass]
                """These lines just add to a C list, for a later regex"""
                if ((sclass in self.distinguish) and #might distinguish, but
                    (self.distinguish[sclass]==False) and #don't want to
                    (sclass not in ['d','ː'])): #Not vowelesq!
                        log.debug("Adding {} to C for {}.".format(sclass,lang))
                        self.s[lang]['C']+=self.db.s[lang][sclass]
            log.info("Segment lists for {} language: {}".format(lang,
                                                                self.s[lang]))
    def setupCVrxs(self):
        # This takes the lists of segments by types (from slists), and turns
        # them into the regexes we need.
        # Note that C, S, and/or G may already be included in C lists, above,
        # but not deleted from self.s[self.analang] until the end of
        # this function.
        """IF VV=V and Vː=V and 'Vá=V', then include ː (and :?) in s['d']."""
        # First, reduce each list to what is actually found in the language
        for sclass in self.s[self.analang]:
            self.s[self.analang][sclass]=rx.inxyz(self.db,self.analang,
                                                self.s[self.analang][sclass])
        # Include plausible sequences of length and diacritics in V, if desired.
        # Excess list items will be removed by re.inxyz()
        if self.distinguish['d'] == False:
            self.s[self.analang]['V']+=list((v+d #do we ever have d+v?
                                    for v in self.s[self.analang]['V']
                                    for d in self.s[self.analang]['d']))
            self.s[self.analang]['V']+=list((d+v #supposedly good unicode...
                                    for v in self.s[self.analang]['V']
                                    for d in self.s[self.analang]['d']))
        if self.distinguish['ː'] == False:
            self.s[self.analang]['V']+=list((v+l
                                    for v in self.s[self.analang]['V']
                                    for l in self.s[self.analang]['ː']))
        if ((self.distinguish['d'] == False) and
                                            (self.distinguish['ː'] == False)):
            self.s[self.analang]['V']+=list((v+d+l
                                    for v in self.s[self.analang]['V']
                                    for d in self.s[self.analang]['d']
                                    for l in self.s[self.analang]['ː']))
            self.s[self.analang]['V']+=list((v+l+d #does this happen?
                                    for v in self.s[self.analang]['V']
                                    for d in self.s[self.analang]['d']
                                    for l in self.s[self.analang]['ː']))
            self.s[self.analang]['V']+=list((d+v+l #supposedly good unicode...
                                    for v in self.s[self.analang]['V']
                                    for d in self.s[self.analang]['d']
                                    for l in self.s[self.analang]['ː']))
        # Make lists that combine each of the remaining possibilities
        self.s[self.analang]['VV']=list((v+v
                                        for v in self.s[self.analang]['V']))
        if self.distinguish['ː'] == True:
            self.s[self.analang]['Vː']=list((v+l
                                    for v in self.s[self.analang]['V']
                                    for l in self.s[self.analang]['ː']))
        self.s[self.analang]['CG']=list((char+g
                                        for char in self.s[self.analang]['C']
                                        for g in self.s[self.analang]['G']))
        self.s[self.analang]['NC']=list((n+char
                                        for char in self.s[self.analang]['C']
                                        for n in self.s[self.analang]['N']))
        self.s[self.analang]['CS']=list((char+s
                                        for char in self.s[self.analang]['C']
                                        for s in self.s[self.analang]['S']))
        self.s[self.analang]['NCS']=list((n+char+s
                                        for char in self.s[self.analang]['C']
                                        for n in self.s[self.analang]['N']
                                        for s in self.s[self.analang]['S']))
        self.s[self.analang]['NCG']=list((n+char+g
                                        for char in self.s[self.analang]['C']
                                        for n in self.s[self.analang]['N']
                                        for g in self.s[self.analang]['G']))
        self.s[self.analang]['CSG']=list((char+s+g
                                        for char in self.s[self.analang]['C']
                                        for s in self.s[self.analang]['S']
                                        for g in self.s[self.analang]['G']))
        self.s[self.analang]['NCSG']=list((n+char+s+g
                                        for char in self.s[self.analang]['C']
                                        for n in self.s[self.analang]['N']
                                        for s in self.s[self.analang]['S']
                                        for g in self.s[self.analang]['G']))
        # Combine some of the above, depending on user settings
        if self.interpret['VV']=='V':
            self.s[self.analang]['V']+=self.s[self.analang]['VV']
        elif (self.interpret['VV']=='Vː') and (self.distinguish['ː']==True):
            self.s[self.analang]['Vː']+=self.s[self.analang]['VV']
        #I never want this, but for the above, because VV is just V+V:
        del self.s[self.analang]['VV']
        if self.interpret['VN']=='Ṽ':
            self.s[self.analang]['Ṽ']=list((v+n
                                            for v in self.s[self.analang]['V']
                                            for n in self.s[self.analang]['N']))
        # Unlike the above, the following have implied else: with ['XY']=XY.
        if self.interpret['CG']=='C':
            self.s[self.analang]['C']+=self.s[self.analang]['CG']
            del self.s[self.analang]['CG']
        elif self.interpret['CG']=='CC':
            del self.s[self.analang]['CG'] # leave it for 'C'
        if self.interpret['CS']=='C':
            self.s[self.analang]['C']+=self.s[self.analang]['CS']
            del self.s[self.analang]['CS']
        elif self.interpret['CS']=='CC':
            del self.s[self.analang]['CS'] # leave it for 'C'
        if self.interpret['NC']=='C':
            self.s[self.analang]['C']+=self.s[self.analang]['NC']
            del self.s[self.analang]['NC']
        elif self.interpret['NC']=='CC':
            del self.s[self.analang]['NC'] # leave it for 'C'
        if (self.interpret['NC']=='C') and (self.interpret['CG']=='C'):
            self.s[self.analang]['C']+=self.s[self.analang]['NCG']
            del self.s[self.analang]['NCG']
        if (self.interpret['NC']=='C') and (self.interpret['CS']=='C'):
            self.s[self.analang]['C']+=self.s[self.analang]['NCS']
            del self.s[self.analang]['NCS']
        if (self.interpret['CG']=='C') and (self.interpret['CS']=='C'):
            self.s[self.analang]['C']+=self.s[self.analang]['CSG']
            del self.s[self.analang]['CSG']
        if ((self.interpret['NC']=='C') and (self.interpret['CG']=='C')
                                        and (self.interpret['CS']=='C')):
            self.s[self.analang]['C']+=self.s[self.analang]['NCSG']
            del self.s[self.analang]['NCSG']
        #Finished joining lists; now make the regexs
        self.rx={}
        if self.distinguish['Nwd'] == True:
            self.s[self.analang]['Nwd']=self.db.s[self.analang]['N'] #make Nwd before deleting N
        for sclass in list(self.s[self.analang]):
            if ((sclass in self.distinguish) and
                    (self.distinguish[sclass]==False)):
                del self.s[self.analang][sclass]
            else:
                # check again for combinations not in the database
                self.s[self.analang][sclass]=rx.inxyz(self.db,self.analang,
                                                self.s[self.analang][sclass])
                if sclass in ['NCSG','CSG','NCS']:
                    log.debug("Class element on passing {}: {}".format(sclass,
                    self.s[self.analang][sclass]))
                    # exit()
                if self.s[self.analang][sclass] == []:
                    del self.s[self.analang][sclass]
                else:
                    log.debug("{} class sorted elements: {}".format(sclass,
                                                        str(rx.s(self,sclass))))
                    if sclass == 'Nwd': #word final, not just a list of glyphs:
                        self.rx['N#']=rx.make(rx.s(self,sclass)+'$',compile=True)
                    else:
                        self.rx[sclass]=rx.make(rx.s(self,sclass),compile=True)
    def profileofform(self,form):
        if form == None:
            return "Invalid"
        formori=form
        """priority sort alphabets (need logic to set one or the other)"""
        """Look for any C, don't find N or G"""
        # self.profilelegit=['#','̃','C','N','G','S','V']
        """Look for word boundaries, N and G before C (though this doesn't
        work, since CG is captured by C first...)"""
        # self.profilelegit=['#','̃','N','G','S','C','Ṽ','V','d','b']
        log.log(4,"Searching {} in this order: {}".format(form,
                        sorted(self.rx.keys(),
                        key=lambda cons: (-len(cons),
                                    [self.profilelegit.index(c) for c in cons])
                        )))
        log.log(4,"Searching with these regexes: {}".format(self.rx))
        for s in sorted(self.rx.keys(),
                        key=lambda cons: (-len(cons),
                                    [self.profilelegit.index(c) for c in cons])
                        ):
            log.log(3,'s: {}; rx: {}'.format(s, self.rx[s]))
            for ps in self.db.pss:
                for i in self.rx[s].findall(form):
                    if i not in self.sextracted[ps][s]:
                        self.sextracted[ps][s][i]=0
                    self.sextracted[ps][s][i]+=1 #self.rx[s].subn('',form)[1] #just the count
            if s is 'N#': #different regex key for this one.
                log.log(2,"Not in d or b, returning variable: {}".format(s))
                form=self.rx['Nwd'].sub(s,form) #replace with profile variable
            elif s not in ['d','b']:
                log.log(2,"Not in d or b, returning variable: {}".format(s))
                form=self.rx[s].sub(s,form) #replace with profile variable
            elif s == 'd':
                log.log(2,"in d; returning {} or nothing".format(s))
                if self.distinguish['d']==True:
                    form=self.rx[s].sub(s,form) #replace with 'Vd', etc.
                else:
                    form=self.rx[s].sub('',form) #remove
            # leaving boundary markers alone in profiles
            # elif s == 'b':
            #     form=self.rx[s].sub(s,form) #replace with profile variable
            # print(form)
            form=re.sub('#$','',form) #pull word final word boundary
            # print(form)
        """We could consider combining NC to C (or not), and CG to C (or not)
        here, after the 'splitter' profiles are formed..."""
        if self.debug==True:
            self.iterations+=1
            if self.iterations>15:
                exit()
        log.debug("{}: {}".format(formori,form))
        return form
    def gimmeguid(self):
        idsbyps=self.db.get('guidbyps',lang=self.analang,ps=self.ps)
        return idsbyps[randint(0, len(idsbyps))]
    def gimmesenseid(self):
        idsbyps=self.db.get('senseidbyps',lang=self.analang,ps=self.ps)
        return idsbyps[randint(0, len(idsbyps)-1)]
    def framenamesbyps(self,ps):
        """Names for all tone frames defined for the language."""
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
        """Define self.location based on lookup of self.name"""
        """This should be done after ps and check name are set"""
        self.location=self.toneframes[self.ps][self.name]['location']
    def framevaluesbynamepsprofile(self,ps,profile,name):
        """Tone group values actually used in a frame,
        by frame name, and by data ps and profile."""
        l=[]
        for guid in self.db.profileswdata[self.ps][self.profile]:
            group=self.db.get('pronunciationfieldvalue',guid=guid,
                                fieldtype='tone',
                                location=self.name)
            l+=group
        return list(dict.fromkeys(l))
    """Mediating between LIFT and the user"""
    def getframeddata(self,source,noframe=False,notonegroup=False,truncdefn=False):
        """This generates a dictionary of form {'form':outputform,
        'gloss':outputgloss} for display, by senseid"""
        """Sometimes this script is called to make the example fields, other
        times to display it. If source is a senseid, it pulls form/gloss/etc
        information from the entry. If source is an example, it pulls that info
        from the example. The info is formatted uniformly in either case."""
        output={}
        log.log(2,"{} {}".format(source, type(source)))
        log.log(2,'self.glosslang: {}'.format(self.glosslang))
        log.log(2,'self.glosslang2: {}'.format(self.glosslang2))
        """Just in case there's a problem later..."""
        forms={}
        glosses={}
        gloss={}
        tonegroups=None
        """Build dual logic here:"""
        if isinstance(source,lift.ET.Element):
            #This is an example element, not a sense or entry element...
            element=source
            for node in element:
                if (node.tag == 'form') and ((node.get('lang') == self.analang)
                        or (node.get('lang') == self.audiolang)):
                    forms[node.get('lang')]=node.findall('text')
                if (((node.tag == 'translation') and
                                (node.get('type') == 'Frame translation')) or
                    ((node.tag == 'gloss') and
                                    (node.get('lang') == self.glosslang))):
                    for subnode in node:
                        if (subnode.tag == 'form'):
                            glosses[subnode.get('lang')]=subnode.findall('text')
                if ((node.tag == 'field') and (node.get('type') == 'tone')):
                    #This should always be only one value:
                    tonegroups=node.findall('form/text')
            log.log(2,'forms: {}'.format(forms))
            for lang in glosses:
                log.log(2,'gloss[{}]: {}'.format(lang,glosses[lang]))
            """convert from lists to single items without loosing data,
            then pull text from nodes"""
            if self.analang in forms:
                form=t(firstoflist(forms[self.analang]))
            else:
                form=None
            if self.audiolang in forms:
                voice=t(firstoflist(forms[self.audiolang]))
            else:
                voice=None
            for lang in glosses:
                if (lang == self.glosslang) or (lang == self.glosslang2):
                    gloss[lang]=t(firstoflist(glosses[lang]))
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
        elif (type(source) is str) and (len(source) == 36): #source is sensedid
            #Asking for a sense, you get all tone groups, if self.name isn't set
            log.log(3,'36 character senseid string!')
            senseid=source
            output['senseid']=senseid
            forms[self.analang]=self.db.citationorlexeme(senseid=senseid,
                                            lang=self.analang,
                                            ps=self.ps)
            forms[self.audiolang]=self.db.citationorlexeme(senseid=senseid,
                                            lang=self.audiolang,
                                            ps=self.ps)
            for lang in [self.glosslang,self.glosslang2]:
                if lang != None:
                    glosses[lang]=self.db.glossordefn(senseid=senseid,lang=lang,
                                            ps=self.ps)
            #If frame is not defined (in self.name) this will output ALL values
            #for this sense!
            tonegroups=self.db.get('exfieldvalue', senseid=senseid,
                                fieldtype='tone', location=self.name)
            """convert from lists to single items without loosing data"""
            form=firstoflist(forms[self.analang])
            voice=firstoflist(forms[self.audiolang])
            for lang in glosses:
                gloss[lang]=firstoflist(glosses[lang])
                log.log(2,'gloss[{}]: {}'.format(lang,gloss[lang]))
        else:
            log.info('Neither Element nor senseid was found!')
            return output
        log.log(2,'form: {}'.format(form))
        for lang in gloss:
            log.log(2,'gloss:'.format(gloss[lang]))
        """The following is the same for senses or examples"""
        if notonegroup == False:
            #If I haven't defined self.name nor set notonegroup=True, this will
            # throw an error on a senseid above.
            tonegroup=t(firstoflist(tonegroups))
            log.log(2,'tonegroup: {}'.format(tonegroup))
            if tonegroup != None:
                try:
                    int(tonegroup)
                except:
                    output['tonegroup']=tonegroup #this is only for named groups
        if (self.glosslang2 == None) and (self.glosslang2 in gloss):
            del gloss[self.glosslang2] #remove this now, and lose checks later
        output[self.analang]=None
        for lang in list(gloss.keys())+[self.glosslang]:
            output[lang]=None
        text=('noform','nogloss')
        if noframe == False:
            frame=self.toneframes[self.ps][self.name]
            """Forms and glosses have to be strings, or the regex fails"""
            if form == None:
                form=nn(form) #'noform'
            for lang in gloss:
                if gloss[lang] == None:
                    gloss[lang]=nn(gloss[lang]) #'nogloss'
            log.log(2,frame)
            output[self.analang]=self.frameregex.sub(form,frame[self.analang])
            for lang in gloss:
                """only give these if the frame has this gloss, *and* if
                the gloss is in the data (user selection is above)"""
                if ((lang == self.glosslang) or ((self.glosslang2 in frame)
                                                    and (gloss[lang] != None))):
                    output[lang]=self.frameregex.sub(gloss[lang],frame[lang])
        else:
            output[self.analang]=nn(form) #for non-segmental forms
            for lang in gloss:
                output[lang]=gloss[lang]
        if voice != None:
            output[self.audiolang]=voice
        text=[str(output[self.analang]),"‘"+str(output[self.glosslang])+"’"]
        if self.glosslang2 in output:
            text+=["‘"+str(output[self.glosslang2])+"’"]
        if 'tonegroup' in output:
            text=[str(output['tonegroup'])]+text
        output['formatted']='\t'.join(text)
        return output
    def getframedentry(self,guid):
        """This is most likely obsolete"""
        """This generates output for selection and verification, by ps"""
        glosses={}
        form=firstoflist(self.db.citationorlexeme(guid,lang=self.analang,
                                                                ps=self.ps))
        glosses[self.glosslang]=firstoflist(self.db.glossordefn(guid,
                                        lang=self.glosslang, ps=self.ps))
        if self.glosslang2 != None:
            glosses[self.glosslang2]=firstoflist(self.db.glossordefn(guid,
                                            lang=self.glosslang2,ps=self.ps))
        frame=self.toneframes[self.ps][self.name]
        if self.debug ==True:
            print(forms,glosses,frame)
        outputform=None
        outputgloss={}
        outputform=self.frameregex.sub(form,frame[self.analang])
        for lang in glosses:
            if (lang != self.glosslang2) or (self.glosslang2 != None):
                outputgloss[lang]=self.frameregex.sub(glosses[lang],
                                            frame[lang])
        printoutput=('     ',outputform,
                    "‘"+str(outputgloss[self.glosslang])+"’")
        if self.glosslang2 != None:
            printoutput+="‘"+str(outputgloss[self.glosslang2])+"’"
        print(printoutput)
        return {self.analang:outputform,self.glosslang:outputgloss,
                                        self.glosslang2:outputgloss}
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
        self.senseidswanyps=self.db.get('senseidwanyps') #any ps value works here.
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
    def checkcheck(self):
        """This checks for incompatible or missing variable values, and asks
        for them. If values are OK, they are displayed."""
        opts={
        'row':0,
        'labelcolumn':0,
        'valuecolumn':1,
        'buttoncolumn':2,
        'labelxpad':15,
        'width':None #10
        }
        def proselabel(opts,label):
            print(label)
            Label(self.frame.status, text=label,font=self.fonts['report']).grid(
                    column=opts['labelcolumn'], row=opts['row'],
                    ipadx=opts['labelxpad'], sticky='w'
                    )
        def labels(opts,label,value):
            Label(self.frame.status, text=label).grid(
                    column=opts['labelcolumn'], row=opts['row'],
                    ipadx=opts['labelxpad'], sticky='w'
                    )
            Label(self.frame.status, text=value).grid(
                    column=opts['valuecolumn'], row=opts['row'],
                    ipadx=opts['labelxpad'], sticky='w'
                    )
        def button(opts,text,fn=None,column=opts['buttoncolumn'],**kwargs):
            """cmd overrides the standard button command system."""
            Button(self.frame.status, choice=text, text=text, anchor='c',
                            cmd=fn, width=opts['width'], **kwargs
                            ).grid(column=column, row=opts['row'])
        log.info("Running Check Check!")
        self.frame.parent.wait() #parent of application; root window
        #If the user exits out before this point, just stop.
        try:
            self.frame.winfo_exists()
        except:
            return
        self.makestatus()
        #Don't guess this; default or user set only
        log.info('Interfacelang: {}'.format(getinterfacelang()))
        """This just gets the prose language name from the code"""
        for l in self.parent.interfacelangs:
            if l['code']==getinterfacelang():
                interfacelanguagename=l['name']
        t=(_("Using {}").format(interfacelanguagename))
        proselabel(opts,t)
        opts['row']+=1
        """We start with the settings that we can likely guess"""
        """Get Analang"""
        if self.analang not in self.db.analangs:
            self.guessanalang()
        if (self.analang == None) or ():
            log.info("find the language")
            self.getanalang()
            return
        if self.audiolang == None:
            self.guessaudiolang() #don't display this, but make it
        t=(_("Working on {}").format(self.languagenames[self.analang]))
        proselabel(opts,t)
        opts['row']+=1
        """Get glosslang"""
        if self.glosslang not in self.db.glosslangs:
            self.guessglosslangs()
        if self.glosslang == None:
            log.info("find the gloss language")
            self.getglosslang()
            return
        """Get glosslang2 (None is OK here, meaning no second gloss language)"""
        if ((self.glosslang2 != None) and
                (self.glosslang not in self.db.glosslangs)):
            """I.e., if glosslang2 is set with a value not in the database"""
            self.guessglosslangs()
        if self.glosslang2 != None:
            t=(_("Meanings in {} and {}").format(
                                self.languagenames[self.glosslang],
                                self.languagenames[self.glosslang2]
                                ))
        else:
                t=(_("Meanings in {} only").format(
                                    self.languagenames[self.glosslang]
                                    ))
        proselabel(opts,t)
        opts['row']+=1
        """These settings must be set (for now); we can't guess them (yet)"""
        """Ultimately, we will pick the largest ps/profile combination as an
        initial default (obviously changeable, as are all)"""
        """Get ps"""
        if ((self.ps not in self.db.pss) or
                (self.ps not in self.profilesbysense)):
            self.nextps(guess=True)
        if self.ps == None:
            log.info("find the ps")
            self.getps()
            return
        """Get profile (this depends on ps)"""
        if ((self.profile not in self.profilesbysense[self.ps]) or
                                                        (self.profile == None)):
            self.nextprofile(guess=True)
            return
        if not set(self.profilelegit).issuperset(self.profile):
            self.type='T'
        count=self.countbypsprofile(self.ps,self.profile)
        if count == None:
            if ((self.ps in self.profilesbysense) and
                    (self.profile in self.profilesbysense[self.ps])):
                count=len(self.profilesbysense[self.ps][self.profile])
            else:
                count=0
        t=(_("Looking at {} {} words ({})").format(self.profile,self.ps,count))
        proselabel(opts,t)
        opts['row']+=1
        """Get type"""
        if self.type not in self.checknamesall:
            self.guesstype()
        if self.type == None:
            log.info("Select a check type (C, V, CV, Tone).")
            self.gettype()
            return
        """Get check"""
        self.getcheckspossible() #This sets self.checkspossible
        # if self.name not in self.checkspossible
        if self.name == 'adhoc':
            tkadhoc()
        elif self.type == 'T': #self.name has different options by self.type
            if self.ps not in self.toneframes:
                self.toneframes[self.ps]={}
            """self.name set here (But this is one I want to leave alone)"""
            """If there's only one tone frame, I don't care what the
            settings file says. Also ask if the settings file name isn't in the
            list of defined frames."""
            if len(self.toneframes[self.ps]) == 1:
                self.name=list(self.toneframes[self.ps].keys())[0]
            if self.name not in self.toneframes[self.ps]:
                t=(_("Checking {}, no defined tone frame yet.").format(
                                    self.typedict[self.type]['pl']))
                self.name=None
            else:
                t=(_("Checking {}, working on ‘{}’ tone frame").format(
                                    self.typedict[self.type]['pl'],self.name))
            proselabel(opts,t)
        else:
            print(self.name,'in', self.checkspossible,'?')
            if self.name not in [x[0] for x in self.checkspossible]: #setnamesbyprofile
                self.guesscheckname()
            if self.name == None: #no backup assumptions for CV checks, for now
                log.info("check selection dialog here, for now just running V1=V2")
                self.getcheck()
                return
        """Get subcheck"""
        self.getsubchecksprioritized()
        if self.subcheck not in [x[0] for x in self.subchecksprioritized[self.type]]:
            self.guesssubcheck()
        if self.type != 'T':
            if self.subcheck == None:
                log.info("Aparently I don't know yet what (e.g., consonant or "
                        "vowel) I'm testing.")
                self.getsubcheck()
                return
            else:
                t=(_("Checking {}, working on {} = {}".format(
                            self.typedict[self.type]['pl'],self.name,self.subcheck)))
                t=(_("Checking {}, working on {}".format(
                            self.typedict[self.type]['pl'],self.name)))
                proselabel(opts,t)
        """Final Button"""
        opts['row']+=1
        if self.type == 'T':
            t=(_("Sort!"))
        else:
            t=(_("Report!")) #because CV doesn't actually sort yet...
        button(opts,t,self.runcheck,column=0,
                compound='bottom', #image bottom, left, right, or top of text
                image=self.photo[self.type]
                )
        opts['row']+=1
        if self.type == 'T':
            t=(_("Record Sorted Examples"))
        else:
            t=(_("Record Dictionary Words"))
        button(opts,t,self.record,column=0,
                compound='left', #image bottom, left, right, or top of text
                row=1,
                image=self.photo['record']
                )
        self.maybeboard()
        self.parent.setmenus(self)
    def soundcheckrefreshdone(self):
        self.storesettingsfile()
        self.checkcheck()
    def soundcheckrefresh(self):
        self.soundsettingswindow.resetframe()
        row=0
        Label(self.soundsettingswindow.frame,
                text="Current Sound Card Settings:").grid(row=row,column=0)
        row+=1
        text=_("Change")
        for var, varset, cmd in [(self.fs,self.fss,self.getsoundhz),
            (self.sample_format,self.sample_formats,self.getsoundformat),
            (self.audio_card_index,self.audio_card_indexes,
                                                        self.getsoundcardindex),
            (self.audioout_card_index,self.audioout_card_indexes,
                                                    self.getsoundcardoutindex),
            ]:
            if var is None:
                Label(self.soundsettingswindow.frame,
                                text='<unset>').grid(row=row,column=0)
            else:
                for ratedict in varset:
                    if var==ratedict['code']:
                        l=ratedict['name'] # self.fsname=ratedict['name']
                        if cmd is self.getsoundcardindex:
                            l=_("Recording on {}").format(l)
                        if cmd is self.getsoundcardoutindex:
                            l=_("Playing on {}").format(l)
                        Label(self.soundsettingswindow.frame,
                                text=l).grid(row=row,column=0)
            Button(self.soundsettingswindow.frame, choice=text,
                            text=text, anchor='c',
                            cmd=cmd).grid(row=row,column=1)
            row+=1
        b=RecordButtonFrame(self.soundsettingswindow.frame,self,test=True)
        b.grid(row=row,column=0)
        row+=1
        bd=Button(self.soundsettingswindow.frame,text=_("Done"),
                                            cmd=self.soundcheckrefreshdone)
        bd.grid(row=row,column=0)
    def soundcheck(self):
        self.soundsettingswindow=Window(self.frame,
                                title=_('Select Sound Card Settings'))
        self.fss=[{'code':192000, 'name':'192khz'},
                    {'code':96000, 'name':'96khz'},
                    {'code':44100, 'name':'44.1khz'},
                    {'code':28000, 'name':'28khz'},
                    {'code':8000, 'name':'8khz'}
                    ]
        self.sample_formats=[{'code':pyaudio.paFloat32, 'name':'32 bit float'},
                            {'code':pyaudio.paInt32, 'name':'32 bit integer'},
                            {'code':pyaudio.paInt24, 'name':'24 bit integer'},
                            {'code':pyaudio.paInt16, 'name':'16 bit integer'},
                            {'code':pyaudio.paInt8, 'name':'8 bit integer'}
                            ]
        self.audio_card_indexes=[]
        self.audioout_card_indexes=[]
        p = pyaudio.PyAudio()
        info = p.get_host_api_info_by_index(0)
        numdevices = info.get('deviceCount')
        for i in range(0, numdevices):
            iinfo=p.get_device_info_by_host_api_device_index(0, i)
            log.debug("Looking at sound card {}".format(iinfo))
            if (iinfo.get(
                                                    'maxInputChannels')) > 0:
                    log.info("Input Device id {} - {}".format(i,
                        p.get_device_info_by_host_api_device_index(0, i).get(
                                                                    'name')))
                    self.audio_card_indexes+=[{
                            'code':i,
                            'name':p.get_device_info_by_host_api_device_index(
                            0, i).get('name')}]
            if (iinfo.get(
                                                    'maxOutputChannels')) > 0:
                    log.info("Output Device id {} - {}".format(i,
                        p.get_device_info_by_host_api_device_index(0, i).get(
                                                                    'name')))
                    self.audioout_card_indexes+=[{
                            'code':i,
                            'name':p.get_device_info_by_host_api_device_index(
                            0, i).get('name')}]
        log.log(2,"fs: {}; sf: {}; ci: {}".format(
                        self.fs,self.sample_format,self.audio_card_index))
        log.log(2,"fss: {}; sfs: {}; cis: {}".format(
                        self.fss,self.sample_formats,self.audio_card_indexes))
        if not hasattr(self,'fs') or self.fs not in [v['code'] for v
                                                in self.fss]:
            self.fs=None
        if (not hasattr(self,'sample_format') or
                (self.sample_format not in [v['code'] for v
                                                in self.sample_formats])):
            self.sample_format=None
        if (not hasattr(self,'audio_card_index') or
                (self.audio_card_index not in [v['code'] for v
                                                in self.audio_card_indexes])):
            self.audio_card_index=None
        if (not hasattr(self,'audioout_card_index') or
                (self.audioout_card_index not in [v['code'] for v
                                                in self.audioout_card_indexes])):
            self.audioout_card_index=None
        log.log(2,"fs: {}; sf: {}; ci: {}".format(
                        self.fs,self.sample_format,self.audio_card_index))
        # ButtonFram
        self.soundcheckrefresh()
        self.soundsettingswindow.wait_window(self.frame.status)
        if self.soundsettingswindow.winfo_exists:
            self.soundsettingswindow.destroy()
    def maybeboard(self):
        def checkfordone():
            for self.profile in self.status[self.type][self.ps]:
                for self.name in self.status[self.type][self.ps][self.profile]:
                    self.makestatusdict() #this should result in 'done' key:
                    if len(self.status[self.type][self.ps][self.profile][
                                                    self.name]['done']) >0:
                        return True
        profileori=self.profile
        nameori=self.name
        if hasattr(self,'leaderboard') and type(self.leaderboard) is Frame:
            self.leaderboard.destroy()
        self.leaderboard=Frame(self.frame)
        self.leaderboard.grid(row=0,column=1,sticky="") #nesw
        #Given the line above, much of the below can go, but not all?
        if hasattr(self,'status') and self.type in self.status:
            if self.ps in self.status[self.type]:
                done=checkfordone()
                self.profile=profileori
                self.name=nameori
                log.debug('maybeboard done: {}'.format(done))
                if done == True:
                    if (hasattr(self,'noboard') and (self.noboard is not None)):
                        self.noboard.destroy()
                    if self.type == 'T':
                        if self.ps in self.toneframes:
                            self.maketoneprogresstable()
                        else:
                            self.makenoboard()
                    else:
                        log.info("Found CV verifications")
                        self.makeCVprogresstable()
                else:
                    self.makenoboard()
            else:
                self.makenoboard()
        else:
            self.makenoboard()
    def makenoboard(self):
        log.info("No Progress board")
        # self.leaderboard.destroy()
        self.noboard=Label(self.leaderboard, image=self.photo['transparent'],
                    text='', pady=50,
                    bg='red' #self.theme['background']
                    ).grid(row=0,column=1,sticky='we')
        self.frame.parent.waitdone() # put this on every return!
    def makeCVprogresstable(self):
        Label(self.leaderboard, text=_('{} Progress').format(
            self.typedict[self.type]['sg']), font=self.fonts['title']
            ).grid(row=0,column=0,sticky='nwe')
        self.leaderboardtable=Frame(self.leaderboard)
        self.leaderboardtable.grid(row=1,column=0)
        Label(self.leaderboardtable,text=_("Nothing to see here..."),
                    # font=self.fonts['reportheader']
                    ).grid(
        row=1,column=0#,sticky='s'
        )
        self.frame.parent.waitdone() # put this on every return!
    def maketoneprogresstable(self):
        #This should depend on self.ps only, and refresh from self.status.
        def groupfn(x):
            for i in x:
                try:
                    int(i)
                    log.log(3,"Integer {} fine".format(i))
                except:
                    log.log(3,"Problem with integer {}".format(i))
                    return nn(x,oneperline=True) #if any is not an integer, all.
            return len(x) #to show counts only
        def updateprofilename(profile,name):
            #use refresh=False rather than run checkcheck twice.
            self.set('profile',profile,refresh=False)
            self.set('name',name)
        title=_('Tone Progress: {}'.format(self.ps))
        Label(self.leaderboard, text=title, font=self.fonts['title'],padx=25
                        ).grid(row=0,column=0)
        self.leaderboardtable=Frame(self.leaderboard)
        self.leaderboardtable.grid(row=1,column=0)
        row=0
        #put in a footer for next profile/frame
        profiles=['header']+list(self.profilesbysense[self.ps].keys())#+['footr']
        frames=list(self.toneframes[self.ps].keys())
        ungroups=0
        for profile in profiles:
            column=0
            if (profile == 'header') or (profile in
                                        self.status[self.type][self.ps]):
                if profile in self.status[self.type][self.ps]:
                    t="{} ({})".format(profile,len(self.profilesbysense[
                                                            self.ps][profile]))
                    Label(self.leaderboardtable,text=t).grid(
                    row=row,column=column,sticky='e'
                    )
                for frame in frames:
                    column+=1
                    if profile == 'header':
                        Label(self.leaderboardtable,text=linebreakwords(frame),
                                    font=self.fonts['reportheader']
                                    ).grid(
                        row=row,column=column,sticky='s',ipadx=5
                        )
                    elif frame in self.status[self.type][self.ps][profile]:
                        if not 'tosort' in self.status[self.type][self.ps][
                                                            profile][frame]:
                            tosort='?'
                        if not 'groups' in self.status[self.type][self.ps][
                                                            profile][frame]:
                            total='?'
                        if not 'done' in self.status[self.type][self.ps][
                                                            profile][frame]:
                            done='?'
                        if len(self.status[self.type][self.ps][profile][
                                frame]['done']) > len(self.status[self.type][
                                self.ps][profile][frame]['groups']):
                            ungroups+=1
                        #At this point, these should be there
                        done=self.status[self.type][self.ps][profile][
                                                                frame]['done']
                        total=self.status[self.type][self.ps][profile][
                                                                frame]['groups']
                        tosort=self.status[self.type][self.ps][profile][frame][
                                                                'tosort']
                        donenum=groupfn(done)
                        totalnum=groupfn(total)
                        log.log(3,"Done groups: {}/{}".format(donenum,type(
                                                                    donenum)))
                        log.log(3,"Total groups: {}/{}".format(totalnum,type(
                                                                    totalnum)))
                        if type(donenum) is int:
                            donenum=str(donenum)+'/'+str(totalnum)
                            log.log(3,"Total groups found: {}".format(donenum))
                        # This should only be needed on a new database
                        if tosort == True:
                            donenum='!'+str(donenum)
                        elif tosort == '?':
                            donenum='?'+str(donenum)
                        Button(self.leaderboardtable,
                                text=donenum,
                                cmd=lambda p=profile, f=frame:updateprofilename(
                                                                    profile=p,
                                                                    name=f),
                                anchor='c',
                                padx=0,pady=0
                                ).grid(
                        row=row,column=column,
                        ipadx=0,ipady=0
                        )
            row+=1
        log.error(_("You have more groups verified than there are: {}".format(
                                                                    ungroups)))
        self.frame.parent.waitdone() # put this on every return!
    def setsu(self):
        self.su=True
        self.checkcheck()
    def unsetsu(self):
        self.su=False
        self.checkcheck()
    def makestatus(self):
        try:
            self.frame.status.destroy()
        except:
            log.info("Apparently, this is my first time making the status frame.")
        self.frame.status=Frame(self.frame)
        self.frame.status.grid(row=0, column=0,sticky='nw') # as row 1?
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
    def setnamesbyprofile(self):
        """include check names appropriate for the given profile and segment
        type (e.g., V1=V2 requires at least two vowels). This function is
        agnostic of part of speech (self.ps)"""
        try:
            len(self.profile)
        except:
            log.info("It doesn't look like you've picked a syllable profile yet.")
            return
        if type(self.type) is not str:
            print("type not set!",self.type)
            return
        if self.type == 'T':
            log.info("This shouldn't happen! (setnamesbyprofile with self.type T)")
            return
        n=int(re.subn(self.type, self.type, self.profile)[1])
        print(n, 'instances of self.type', self.type, 'in', self.profile)
        names=list()
        for i in range(n):
            ilist=self.checknamesall[self.type][i+1]
            names+=ilist  #.append(, This is causing a list in a list..…
        return names
    def getanalang(self):
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
    def getglosslang(self):
        log.info("this sets the gloss")
        # fn=inspect.currentframe().f_code.co_name
        window=Window(self.frame,title=_('Select Gloss Language'))
        # if self.db.glosslang is None :
        #     Label(window.frame,
        #                   text='Error: please set Lift file first! ('
        #                   +str(self.db.filename)+')'
        #                   ).grid(column=0, row=0)
        # else:
        Label(window.frame,
                  text=_('What Language do you want to use for glosses?')
                  ).grid(column=0, row=1)
        langs=list()
        for lang in self.db.glosslangs:
            langs.append({'code':lang, 'name':self.languagenames[lang]})
            print(lang, self.languagenames[lang])
        buttonFrame1=ButtonFrame(window.frame,
                                 langs,self.setglosslang,
                                 window
                                 ).grid(column=0, row=4)
    def getglosslang2(self):
        log.info("this sets the gloss")
        # fn=inspect.currentframe().f_code.co_name
        window=Window(self.frame,title='Select Gloss Language')
        if self.db.filename is None :
            text=_('Error: please set Lift file first!')+' ('
            +str(self.db.filename)+')'
            Label(window.frame,text=text).grid(column=0, row=0)
        else:
            text=_('What other language do you want to use for glosses?')
            Label(window.frame,text=text).grid(column=0, row=1)
            langs=list()
            for lang in self.db.glosslangs:
                if lang == self.glosslang:
                    continue
                langs.append({'code':lang, 'name':self.languagenames[lang]})
                print(lang, self.languagenames[lang])
            langs.append({'code':None, 'name':'just use '
                            +self.languagenames[self.glosslang]})
            buttonFrame1=ButtonFrame(window.frame,langs,self.setglosslang2,
                                     window
                                     ).grid(column=0, row=4)
    def getcheckspossible(self):
        """This splits by tone or not, because the checks available for
        segments depend on the number of segments in the selected syllable
        profile, but for tone, they don't; tone frames depend only on ps."""
        if self.type=='T': #if it's a tone check, get from frames.
            self.checkspossible=self.framenamesbyps(self.ps)
        else:
            self.checkspossible=self.setnamesbyprofile() #tuples of CV checks
    def getcheck(self):
        log.info("this sets the check")
        # fn=inspect.currentframe().f_code.co_name
        log.info("Getting the check name...")
        self.getcheckspossible()
        window=Window(self.frame,title='Select Check')
        btext=_("Define a New Tone Frame")
        if self.checkspossible == []:
            text=_("You don't seem to have any tone frames set up.\n"
            "Click '{}' below to define a tone frame. \nPlease "
            "pay attention to the instructions, and if \nthere's anything "
            "you don't understand, or if you're not \nsure what a tone "
            "frame is, please ask for help. \nWhen you are done making frames, "
            "click 'Exit' to continue.".format(btext))
            Label(window.frame, text=text).grid(column=0, row=0, ipady=25)
            b=Button(window.frame, text=btext,
                    cmd=self.addframe,
                    anchor='c')
            b.grid(column=0, row=1,sticky='')
            """I need to make this quit the whole program, immediately."""
            b2=Button(window.frame, text=_("Quit A→Z+T"),
                    cmd=self.parent.parent.destroy,
                    anchor='c')
            b2.grid(column=1, row=1,sticky='')
            b.wait_window(window)
            self.checkcheck()
        else:
            text=_('What check do you want to do?')
            Label(window.frame, text=text).grid(column=0, row=0)
            buttonFrame1=ScrollingButtonFrame(window.frame,
                                    self.checkspossible,
                                    self.setcheck,
                                    window
                                    )
            buttonFrame1.grid(column=0, row=4)
            buttonFrame1.wait_window(window)
        if self.name != None:
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
    def getV(self,window):
        # fn=inspect.currentframe().f_code.co_name
        """Window is called in getsubcheck"""
        if self.ps is None or self.ps == "Null":
            Label(window.frame,
                          text='Error: please set Grammatical category first! ('
                          +str(self.ps)+')'
                          ).grid(column=0, row=0)
        else:
            # Label(window.frame,
            #               text='Working with Grammatical category: '+self.ps
            #               ).grid(column=0, row=0)
            Label(window.frame,
                          text='What Vowel do you want to work with?'
                          ).grid(column=0, row=0)
            window.scroll=Frame(window.frame)
            window.scroll.grid(column=0, row=1)
            buttonFrame1=ScrollingButtonFrame(window.scroll,
                                     #self.db.v[self.analang],
                                     self.scount[self.ps][self.type],
                                     self.setS,
                                     window=window
                                     ).grid(column=0, row=4)
    def getC(self,window):
        # fn=inspect.currentframe().f_code.co_name
        """Window is called in getsubcheck"""
        if self.ps is None or self.ps == "Null":
            text=_('Error: please set Grammatical category first! ')+'('
            +str(self.ps)+')'
            Label(window.frame,
                          text=text
                          ).grid(column=0, row=0)
        else:
            # Label(window.frame,
            #               text='Working with Grammatical category: '+self.ps
            #               ).grid(column=0, row=0)
            Label(window.frame,
                          text='What consonant do you want to work with?'
                          ).grid(column=0, row=0,sticky='nw')
            window.scroll=Frame(window.frame)
            window.scroll.grid(column=0, row=1)
            buttonFrame1=ScrollingButtonFrame(window.scroll,
                                    # self.db.c[self.analang],
                                    self.scount[self.ps][self.type],
                                    self.setS,
                                    window=window
                                    )
            buttonFrame1.grid(column=0, row=0)
    def getlocations(self):
        self.locations=[]
        for senseid in self.senseidstosort:
            for location in self.db.get('exfieldlocation',
                senseid=senseid, fieldtype='tone'):
                self.locations+=[location]
        self.locations=list(dict.fromkeys(self.locations))
    def topprofiles(self,x='ALL'):
        """take the top x ps-profile combos, return in ps:profile dict"""
        profiles={}
        if x == 'ALL':
            x=len(self.profilecounts)
        for count in range(x):
            if self.profilecounts[count][2] not in profiles:
                profiles[self.profilecounts[count][2]]=list()
            profiles[self.profilecounts[count][2]]+=[self.profilecounts[count][1]] #(count, profile, ps)
        # print(profiles)
        # profiles=list(dict.fromkeys(profiles))
        return profiles
    def countbypsprofile(self, ps, profile):
        for line in self.profilecounts:
            if line[1] == profile and line[2] == ps:
                return line[0]
    def getprofilestodo(self):
        log.debug(self.profilecounts)
        self.profilecountsValid=[]
        self.profilecountsValidwAdHoc=[]
        #self.profilecountsValid filters out Invalid, and also by self.ps...
        for x in [x for x in self.profilecounts if x[2]==self.ps
                                                if x[1]!='Invalid']:
            log.log(3,"profile count tuple: {}".format(x))
            if set(self.profilelegit).issuperset(x[1]):
                self.profilecountsValid.append(x)
            self.profilecountsValidwAdHoc.append(x)
        log.debug("Valid profiles for ps {}: {}".format(self.ps,
                                                    self.profilecountsValid))
        self.profilestodo=[x[1] for x in self.profilecountsValid if
                            self.profilecountsValid.index(x)<=self.maxprofiles]
        log.debug("self.profilestodo: {}".format(self.profilestodo))
    def getframestodo(self):
        #This iterates without using self.name, self.ps or self.profile.
        #This sets self.senseidstosort,self.senseids(un)sorted,&self.tonegroups
        self.framestodo=[]
        if self.ps not in self.toneframes:
            log.error("The ps {} doesn't seem to be in your tone frames "
            "file: {}".format(self.ps,self.toneframes.keys()))
            return
        for frame in self.toneframes[self.ps]:
            if frame not in self.status[self.type][self.ps][self.profile]:
                log.debug("{} frame Not started yet: {}".format(frame,tosort))
                self.framestodo.append(frame)
                continue
            groups=self.status[self.type][self.ps][self.profile][frame][
                                                                    'groups']
            done=self.status[self.type][self.ps][self.profile][frame]['done']
            groupstodo=list(set(self.status[self.type][self.ps][self.profile][
                                                frame]['groups'])-set(done))
            tosort=self.status[self.type][self.ps][self.profile][frame][
                                                                    'tosort']
            log.debug("Frame: {}; groupstodo: {}; groups: {}; done: {}; "
                    "tosort: {}".format(frame, groupstodo, groups, done,
                                                                        tosort))
            if tosort == True:
                log.debug("{} frame has elements left to sort: {}".format(
                                                            frame,tosort))
                self.framestodo.append(frame)
            elif len(groups) == 0 or len(groupstodo) >0:
                log.debug("{} frame is unstarted or has elements left to "
                        "verify: {} (groups: {})".format(frame,groupstodo,
                                                                        groups))
                self.framestodo.append(frame)
        log.debug("Frames to do: {}".format(self.framestodo))
    def wordsbypsprofilechecksubcheckp(self,parent='NoXLPparent',t="NoText!"):
        xlp.Paragraph(parent,t)
        print(t)
        log.debug(t)
        self.buildregex()
        log.log(2,"self.regex: {}; self.regexCV: {}".format(self.regex,
                                                        self.regexCV))
        matches=set(self.db.senseidformsbyregex(self.regex,
                                            self.analang,
                                            ps=self.ps).keys())
        for typenum in self.typenumsRun:
            # this removes senses already reported (e.g., in V1=V2)
            matches-=self.basicreported[typenum]
        log.log(2,"{} matches found!: {}".format(len(matches),matches))
        if 'x' in self.name:
            n=self.checkcounts[self.ps][self.profile][self.name][
                            self.subcheck][self.subcheckcomparison]=len(matches)
        else:
            n=self.checkcounts[self.ps][self.profile][self.name][
                            self.subcheck]=len(matches)
            if '=' in self.name:
                xname=re.sub('=','x',self.name, count=1)
                log.debug("looking for name {} in {}".format(xname,
                                                    self.checkcodesbyprofile))
                if xname in self.checkcodesbyprofile:
                    log.debug("Adding {} value to name {}".format(len(matches),
                                                                        xname))
                    #put the results in that group, too
                    log.debug(self.checkcounts)
                    if xname not in self.checkcounts[self.ps][self.profile]:
                        self.checkcounts[self.ps][self.profile][xname]={}
                    if self.subcheck not in self.checkcounts[self.ps][
                                    self.profile][xname]:
                        self.checkcounts[self.ps][self.profile][xname][
                                                        self.subcheck]={}
                    self.checkcounts[self.ps][self.profile][xname][
                                    self.subcheck][self.subcheck]=len(matches)
                    log.debug(self.checkcounts)
        if n>0:
            titlebits='x'+self.ps+self.profile+self.name+self.subcheck
            if 'x' in self.name:
                titlebits+='x'+self.subcheckcomparison
            id=rx.id(titlebits)
            ex=xlp.Example(parent,id)
            for senseid in matches:
                for typenum in self.typenumsRun:
                    self.basicreported[typenum].add(senseid)
                framed=self.getframeddata(senseid,noframe=True)
                print('\t',framed['formatted'])
                self.framedtoXLP(framed,parent=ex,listword=True)
    def wordsbypsprofilechecksubcheck(self,parent='NoXLPparent'):
        """This function iterates across self.name and self.subcheck values
        appropriate for the specified self.type, self.profile and self.name
        values (ps is irrelevant here).
        Because two functions called (buildregex and getframeddata) use
        self.name and self.subcheck to do their work, they and their
        dependents would need to be changed to fit a new paradigm, if we
        were to change the variable here. So rather, we store the current
        self.name and self.subcheck values, then iterate across logically
        possible values (as above), then restore the value."""
        """I need to find a way to limit these tests to appropriate
        profiles..."""
        nameori=self.name
        subcheckori=self.subcheck
        if self.type in ['V','C']:
            subchecks=self.s[self.analang][self.type]
        """This sets each of the checks that are applicable for the given
        profile; self.basicreported is from self.basicreport()"""
        for typenum in self.basicreported:
            log.log(2, '{}: {}'.format(typenum,self.basicreported[typenum]))
        """setnamesbyprofile doesn't depend on self.ps"""
        self.checkcodesbyprofile=sorted([x[0] for x in self.setnamesbyprofile()],
                                        key=len,reverse=True)
        """self.name set here"""
        for self.name in self.checkcodesbyprofile:
            if self.name not in self.checkcounts[self.ps][self.profile]:
                self.checkcounts[self.ps][self.profile][self.name]={}
            self.typenumsRun=[typenum for typenum in self.typenums
                                        if re.search(typenum,self.name)]
            log.debug('self.name: {}; self.type: {}; self.typenums: {}; '
                        'self.typenumsRun: {}'.format(self.name,self.type,
                                                self.typenums,self.typenumsRun))
            if len(self.name) == 1:
                log.debug("Error! {} Doesn't seem to be list formatted.".format(
                                                                    self.name))
            if 'x' in self.name:
                log.debug('Hey, I cound a correspondence number!')
                if self.type in ['V','C']:
                    subcheckcomparisons=subchecks
                elif self.type == 'CV':
                    subchecks=self.s[self.analang]['C']
                    subcheckcomparisons=self.s[self.analang]['V']
                else:
                    log.error("Sorry, I don't know how to compare type: {}"
                                                        "".format(self.type))
                for self.subcheck in subchecks:
                    if self.subcheck not in self.checkcounts[self.ps][
                                                    self.profile][self.name]:
                        self.checkcounts[self.ps][self.profile][self.name][
                                                            self.subcheck]={}
                    for self.subcheckcomparison in subcheckcomparisons:
                        if self.subcheck != self.subcheckcomparison:
                            t=_("{} {} {}={}-{}".format(self.ps,self.profile,
                                                self.name,self.subcheck,
                                                self.subcheckcomparison))
                            self.wordsbypsprofilechecksubcheckp(parent=parent,
                                                                            t=t)
            else:
                for self.subcheck in subchecks:
                    t=_("{} {} {}={}".format(self.ps,self.profile,self.name,
                                                                self.subcheck))
                    self.wordsbypsprofilechecksubcheckp(parent=parent,t=t)
        self.name=nameori
        self.subcheck=subcheckori
    def idXLP(self,framed):
        idbits='x'
        for x in [self.ps,self.profile,self.name,self.subcheck,
                    framed[self.analang],framed[self.glosslang]]:
            if x != None:
                idbits+=x
        return rx.id(idbits) #for either example or listword
    def framedtoXLP(self,framed,parent,listword=False):
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
        if self.audiolang in framed:
            url=file.getdiredrelURL(self.reporttoaudiorelURL,framed[self.audiolang])
            el=xlp.LinkedData(ex,self.analang,framed[self.analang],str(url))
        else:
            el=xlp.LangData(ex,self.analang,framed[self.analang])
        eg=xlp.Gloss(ex,self.glosslang,framed[self.glosslang])
        if ((self.glosslang2 != '') and (self.glosslang2 in framed)
                and (framed[self.glosslang2] != None)):
                eg2=xlp.Gloss(ex,self.glosslang2,framed[self.glosslang2])
    def makecountssorted(self):
        # This iterates across self.profilesbysense to provide counts for each
        # ps-profile combination (aggravated for profile='Invalid')
        # it should only be called when creating/adding to self.profilesbysense
        self.profilecounts={}
        self.profilecountInvalid=0
        wcounts=list()
        for ps in self.profilesbysense:
            for profile in self.profilesbysense[ps]:
                if profile == 'Invalid':
                    self.profilecountInvalid+=len(self.profilesbysense[ps][
                                                                    profile])
                count=len(self.profilesbysense[ps][profile])
                wcounts.append((count, profile, ps))
        self.profilecounts=sorted(wcounts,reverse=True)
        # self.Scounts={} #?
    def printcountssorted(self):
        #This is only used in the basic report
        log.info("Ranked and numbered syllable profiles, by grammatical category:")
        #{}
        # allkeys=[]
        nTotal=0
        # nInvalid=0
        nTotals={}
        # for k in self.profilesbysense:
        #     allkeys+=self.profilesbysense[k]
        for line in self.profilecounts:
            nTotal+=line[0]
            if line[2] not in nTotals:
                nTotals[line[2]]=0
            nTotals[line[2]]+=line[0]
            # if line[2] == 'Invalid':
            #     nInvalid+=line[0]
        print('Profiled data:',nTotal) #len(allkeys))
        """Pull this?"""
        print('Invalid entries found:',self.profilecountInvalid) # nTotals['Invalid']) #len(self.profilesbysense['Invalid']))
        for ps in self.profilesbysense:
            if ps == 'Invalid':
                continue
            for line in self.profilecounts: #sorted(wcounts, reverse=True):
                if line[2] == ps:
                    print(line[0],line[1])
            print(ps,"(total):",nTotals[ps])
    def printprofilesbyps(self):
        #This is only used in the basic report
        log.info("Syllable profiles actually in senses, by grammatical category:")
        for ps in self.profilesbysense:
            if ps is 'Invalid':
                continue
            print(ps, self.profilesbysense[ps])
    def senseidsincheck(self,senseids):
        """This function takes a list of senseids that match a criteria, and
        limits them to those that match the ps/profile combination we're
        working on"""
        lst1=self.senseidstosort #all in this ps/profile
        senseidstochange=set(lst1).intersection(senseids)
        return senseidstochange
    def getexsall(self,value):
        #This returns all the senseids with a given tone value
        senseids=self.db.get('senseidbyexfieldvalue',location=self.name,
                            fieldtype='tone',
                            fieldvalue=value
                            )
        senseidsincheck=self.senseidsincheck(senseids)
        return list(senseidsincheck)
    def getex(self,value,notonegroup=True,truncdefn=False):
        """This function finds examples in the lexicon for a given tone value,
        in a given tone frame (from check)"""
        senseids=self.getexsall(value)
        output={'n': len(senseids)}
        if (not hasattr(self,'exs')) or (self.exs == None):
            self.exs={} #in case this hasn't been set up by now
        if value in self.exs:
            if self.exs[value] in senseids: #if stored value is in group
                log.info("Using stored value for {} group: {}".format(value,
                                self.exs[value]))
                framed=self.getframeddata(self.exs[value],
                                            notonegroup=notonegroup,
                                            truncdefn=truncdefn)
                if (framed[self.glosslang] != None):
                    output['framed']=framed
                    return output
        for i in range(len(senseids)): #just keep trying until you succeed
            senseid=senseids[randint(0, len(senseids))-1]
            framed=self.getframeddata(senseid,notonegroup=notonegroup,
                                                            truncdefn=truncdefn)
            if (framed[self.glosslang] != None):
                """As soon as you find one with form and gloss, quit."""
                self.exs[value]=senseid
                output['framed']=framed
                return output
            else:
                log.info("Example sense with empty field problem")
    def renamegroup(self):
        def submitform():
            newtonevalue=formfield.get()
            if newtonevalue in self.status[self.type][self.ps][self.profile][
                                                        self.name]['groups']:
                er=Window(self.runwindow)
                l=Label(er,text=_("Sorry, there is already a group with that "
                                "label; If you want to join the groups, "
                                "give it a different name now, and join "
                                "it after they are both verified ({} is "
                                "already in {})".format(newtonevalue,
                                self.status[self.type][self.ps][self.profile][
                                                        self.name]['groups'])))
                l.grid(row=0,column=0)
                return
            self.updatebysubchecksenseid(self.subcheck,newtonevalue)
            self.subcheck=newtonevalue
            self.gettonegroups()
            self.verifysubwindow.destroy()
            self.verifyT()
        self.getrunwindow()
        newname=tkinter.StringVar()
        padx=50
        pady=10
        title=_("Rename {} {} tone group ‘{}’ in ‘{}’ frame"
                        ).format(self.ps,self.profile,self.subcheck,
                                    self.name)
        self.verifysubwindow=Window(self.runwindow.frame)
        self.verifysubwindow.title(title)
        Label(self.verifysubwindow,text=title,font=self.fonts['title'],
                justify=tkinter.LEFT,anchor='c'
                ).grid(row=0,column=0,sticky='ew',padx=padx,pady=pady)
        getformtext=_("What the new name do you want to call this surface tone "
                        "group? A label that describes the surface tone form "
                        "in this context would be best, like ‘[˥˥˥ ˨˨˨]’")
        getform=Label(self.verifysubwindow,text=getformtext,
                font=self.fonts['read'])
        getform.grid(row=0,column=0,padx=padx,pady=pady)
        formfield = EntryField(self.verifysubwindow,textvariable=newname)
        formfield.grid(row=1,column=0)
        sub_btn=Button(self.verifysubwindow,text = 'Use this name',
                  command = submitform,anchor ='c')
        sub_btn.grid(row=2,column=0,sticky='')
        sub_btn.wait_window(self.verifysubwindow) #then move to next step
        """Store these variables above, finish with (destroying window with
        local variables):"""
    def maybesort(self):
        done=(_("All tone groups in {} have been verified!").format(self.name))
        self.getrunwindow()
        if self.status[self.type][self.ps][self.profile][self.name][
                                                            'tosort'] == True:
            quit=self.sortT()
            if quit == True:
                return # didn't do anything: 1
            self.checkcheck() #since we probably added groups
        #status is populated by verifyT, and unpopulated by joinT
        if ((self.type in self.status) and
            (self.ps in self.status[self.type]) and
            (self.profile in self.status[self.type][self.ps]) and
            (self.name in self.status[self.type][self.ps][self.profile]) and
            ('done' in self.status[self.type][self.ps][self.profile][self.name])
            ):
            verified=self.status[self.type][self.ps][self.profile][self.name][
                                                                        'done']
        else:
            verified=set() #so the following doesn't crash...
        # if all items in the self.tonegroups exists in verified
        if set(self.status[self.type][self.ps][self.profile][self.name][
                                                'groups']).issubset(verified):
            exit=self.joinT()
            # This is recursive because we don't know how many joins we'll need,
            # nor the results of susequent verifications or sorts
            if exit == True:
                #if the user joins groups, update the main window and repeat
                # self.checkcheck()
                # self.maybesort()
                # self.runwindow.ww.close()
            #     return #if join window was closed.
            # elif joined == None:
                #This happens when the user exits the window
                window=self.getrunwindow()
                buttontxt=_("Sort!")
                text=_("Hey, you're not Done!\nCome back when you have time; "
                "restart where you left off by pressing '{}'".format(buttontxt))
                Label(self.runwindow.frame, text=text).grid(row=0,column=0)
                self.runwindow.waitdone()
                return
            elif exit == False:
                # self.updatestatus(verified=True,alldone=True)
                if self.runwindow.winfo_exists():
                    def nframe():
                        self.nextframe()
                        self.runwindow.destroy()
                        self.checkcheck() #redraw the table
                        self.runcheck()
                    def aframe():
                        self.runwindow.destroy()
                        self.addframe()
                        self.addwindow.wait_window(self.addwindow)
                        self.checkcheck() #redraw the table
                        self.runcheck()
                    def nprofile():
                        self.nextprofile()
                        self.runwindow.destroy()
                        self.checkcheck() #redraw the table
                        self.runcheck()
                    def nps():
                        self.nextps()
                        self.nextprofile(guess=True)
                        self.runwindow.destroy()
                        self.checkcheck() #redraw the table
                        self.runcheck()
                    self.runwindow.resetframe()
                    Label(self.runwindow.frame, text=done).grid(row=0,column=0,
                                                                columnspan=2)
                    Label(self.runwindow.frame, text='',
                                image=self.photo[self.type]
                                ).grid(row=1,column=0,columnspan=2)
                    self.runwindow.wait()
                    self.getframestodo()
                    self.getprofilestodo()
                    if len(self.framestodo) >0:
                        Button(self.runwindow.frame,
                            text=_("Continue to next frame"),
                            command=nframe).grid(row=2,column=0)
                    else:
                        Button(self.runwindow.frame,
                            text=_("Define a new frame"),
                            command=aframe).grid(row=2,column=0)
                    if ((self.profile in self.profilestodo) and
                    (self.profilestodo.index(self.profile) < self.maxprofiles)):
                        Button(self.runwindow.frame,
                            text=_("Continue to next syllable profile"),
                            command=nprofile).grid(row=2,column=1)
                    else:
                        Button(self.runwindow.frame,
                            text=_("Continue to next Grammatical Category"),
                            command=nps).grid(row=2,column=1)
                    self.runwindow.waitdone()
                    return
        # we only get here if a group is not verified (otherwise, return above)
        self.verifyT()
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
        """sortingstatus() checks by self.ps,self.profile,self.name (frame),
        for the presence of a populated fieldtype='tone'. So any time any of
        the above is changed, this variable should be reset."""
        """Can't do this test suite unless there are unsorted entries..."""
        def testsorting(self):
            if self.senseidsunsorted != []:
                self.marksortedsenseid(self.senseidsunsorted[0])
                print('self.guidsunsorted:',len(self.senseidsunsorted),
                        self.senseidsunsorted)
                print('self.guidssorted:',len(self.senseidssorted),
                        self.senseidssorted)
            if self.senseidssorted != []:
                self.markunsortedsenseid(self.senseidssorted[0])
                print('self.guidsunsorted:',len(self.senseidsunsorted),
                        self.senseidsunsorted)
                print('self.guidssorted:',len(self.senseidssorted),
                        self.senseidssorted)
            exit()
        todo=len(self.senseidstosort)
        title=_("Sort {} Tone (in ‘{}’ frame)").format(
                                        self.languagenames[self.analang],
                                        self.name)
        instructions=_("Select the one with the same tone melody as")
        self.runwindow.frame.scroll=ScrollingFrame(self.runwindow.frame)
        self.runwindow.frame.scroll.grid(column=1,row=2, sticky="new")
        """The frame for the groups buttons"""
        self.runwindow.frame.scroll.content.groups=Frame(
                                            self.runwindow.frame.scroll.content)
        self.runwindow.frame.scroll.content.groups.grid(row=0,column=0,
                                                                sticky="ew")
        self.runwindow.frame.scroll.content.groups.row=0 #rows for this frame
        """If we have tone groups already, make them now."""
        for group in self.status[self.type][self.ps][self.profile][self.name][
                                                                    'groups']:
            self.tonegroupbuttonframe(
                            self.runwindow.frame.scroll.content.groups,group,
                            row=self.runwindow.frame.scroll.content.groups.row,
                            alwaysrefreshable=True) #notonegroup?
            self.runwindow.frame.scroll.content.groups.row+=1
        """The second frame, for the other two buttons, which also scroll"""
        self.runwindow.frame.scroll.content.anotherskip=Frame(
                                            self.runwindow.frame.scroll.content)
        self.runwindow.frame.scroll.content.anotherskip.grid(row=1,column=0)
        self.getanotherskip(self.runwindow.frame.scroll.content.anotherskip)
        while (self.status[self.type][self.ps][self.profile][self.name][
                'tosort'] == True and self.runwindow.winfo_exists()):
        # while self.senseidsunsorted != [] and self.runwindow.winfo_exists():
            if hasattr(self,'groupselected'):
                delattr(self,'groupselected') #=[] #reset this for each word!
            senseid=self.senseidsunsorted[0]
            progress=(str(self.senseidstosort.index(senseid)+1)+'/'
                        +str(todo))
            print(senseid,progress)
            framed=self.getframeddata(senseid,truncdefn=True)
            """After the first entry, sort by groups."""
            log.debug('self.tonegroups: {}'.format(self.status[self.type][
                                self.ps][self.profile][self.name]['groups']))
            entryview=Frame(self.runwindow.frame)
            titles=Frame(self.runwindow.frame)
            Label(titles, text=title,
                    font=self.fonts['title'],
                    anchor='c').grid(column=0, row=0, sticky="ew")
            Label(titles, text=instructions,
                    font=self.fonts['instructions'],
                    anchor='c').grid(column=0, row=1, sticky="ew")
            Label(titles, text=progress,
                    font=self.fonts['report'],
                    anchor='w'
                    ).grid(column=1, row=0, sticky="ew")
            titles.grid(column=0, row=0, sticky="ew",
                                            columnspan=2)
            Label(self.runwindow.frame, image=self.parent.photo['sortT'],
                            text='',
                            bg=self.theme['background']
                            ).grid(row=1,column=0,rowspan=3,sticky='nw')
            text=(framed['formatted'])
            self.sorting=Label(entryview, text=text,
                    font=self.fonts['readbig']
                    )
            entryview.grid(column=1, row=1, sticky="new")
            self.sorting.grid(column=0,row=0, sticky="w",pady=50)
            self.sorting.wrap()
            self.runwindow.waitdone()
            self.runwindow.wait_window(window=self.sorting)
            if not self.runwindow.winfo_exists():
                return 1
            log.debug("Group selected:",self.groupselected)
            if hasattr(self,'groupselected'): # != []:
                if self.groupselected == "NONEOFTHEABOVE":
                    """If there are no groups yet, or if the user asks for another
                    group, make a new group."""
                    self.groupselected=self.addtonegroup()
                    """place this one just before the last two"""
                    print('Rows so far:',
                        self.runwindow.frame.scroll.content.groups.grid_size()[1])
                    self.runwindow.frame.scroll.content.groups.row+=1 #add to above.
                    """Add the new group to the database"""
                    self.addtonefieldex(senseid,framed)
                    """And give the user a button for it, for future words
                    (N.B.: This is only used for groups added during the current
                    run. At the beginning of a run, all used groups have buttons
                    created above.)"""
                    self.tonegroupbuttonframe(
                            self.runwindow.frame.scroll.content.groups,
                            self.groupselected,
                            row=self.runwindow.frame.scroll.content.groups.row,
                            alwaysrefreshable=True)
                    #adjust window for new button
                    self.runwindow.frame.scroll.windowsize()
                    print('Group added:',self.groupselected)
                else: #before making a new button, or now, add fields to the sense.
                    """This needs to *not* operate on "exit" button."""
                    self.addtonefieldex(senseid,framed)
            else:
                return 1 # this should only happen on Exit
            self.marksortedsenseid(senseid)
        self.runwindow.resetframe()
    def verifyT(self):
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
        if len(self.status[self.type][self.ps][self.profile][self.name][
                                                                'groups']) == 0:
            log.debug("No tone groups to verify!")
            return
        # The title for this page changes by group, below.
        self.getrunwindow()
        oktext='These all have the same tone'
        instructions=_("Read down this list to verify they all have the same "
            "tone melody. Select any word with a different tone melody to "
            "remove it from the list."
            ).format(self.subcheck,self.name,oktext)
        """Put a menu on this window to rename the group we're checking.
        This should be to a sensible transcription/description of the surface
        tone in this context, e.g., [˦˦˦  ˨˨˨]"""
        verifymenu = Menu(self.runwindow, tearoff=0)
        verifymenu.add_command(label=_("Rename Group"),
                        command=lambda :self.renamegroup())
        self.runwindow.config(menu=verifymenu)
        """self.subcheck is set here, but probably OK"""
        self.makestatusdict()
        for self.subcheck in self.status[self.type][self.ps][self.profile][
                                                        self.name]['groups']:
            if not self.runwindow.winfo_exists():
                return
            if self.subcheck in (self.status[self.type][self.ps][self.profile]
                                            [self.name]['done']):
                log.info("{} already verified, continuing.".format(
                                                                self.subcheck))
                continue
            senseids=self.getexsall(self.subcheck)
            if len(senseids) <2:
                self.updatestatus(verified=True)
                log.info("Group {} only has {} example; marking verified and "
                        "continuing.".format(self.subcheck,len(senseids)))
                continue
            self.runwindow.resetframe() #just once per group
            self.runwindow.wait()
            title=_("Verify {} Tone Group ‘{}’ (in ‘{}’ frame)").format(
                                        self.languagenames[self.analang],
                                        self.subcheck,
                                        self.name
                                        )
            titles=Frame(self.runwindow.frame)
            titles.grid(column=0, row=0, columnspan=2, sticky="w")
            Label(titles, text=title,
                    font=self.fonts['title']
                    ).grid(column=0, row=0, sticky="w")
            print(instructions)
            if hasattr(self,'groupselected'): #='' #so it doesn't get in way later.
                delattr(self,'groupselected')
            row=0
            column=0
            if self.subcheck in self.status[self.type][self.ps][self.profile][
                                                        self.name]['groups']:
                progress=('('+str(self.status[self.type][self.ps][self.profile][
                    self.name]['groups'].index(self.subcheck)+1)+'/'+str(len(
                    self.status[self.type][self.ps][self.profile][self.name][
                                                                'groups']))+')')
                Label(titles, text=progress,anchor='w'
                                    ).grid(row=0,column=1,sticky="ew")
            Label(titles, text=instructions).grid(row=1,column=0, columnspan=2,
                                                                    sticky="w")
            Label(self.runwindow.frame, image=self.parent.photo['verifyT'],
                            text='',
                            bg=self.theme['background']
                            ).grid(row=1,column=0,rowspan=3,sticky='nw')
            """Scroll after instructions"""
            self.sframe=ScrollingFrame(self.runwindow.frame)
            self.sframe.grid(row=1,column=1,columnspan=2,sticky='w')
            row+=1
            """put entry buttons here."""
            for senseid in senseids:
                self.verifybutton(self.sframe.content,senseid,
                                    row, column,
                                    label=False)
                row+=1
            if senseid == None:
                continue
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
            # b.bind('<mouseclick>',remove senseid from sensids)
            self.sframe.windowsize()
            self.runwindow.waitdone()
            b.wait_window(bf)
            if not self.runwindow.winfo_exists():
                return 1
            # I need to work on this later. How to distinguish buttons after
            # the window is gone? I think I have to count senseids in the group.
            # if not self.sframe.content.winfo_exists(): #This goes with window
            #     log.debug("It looks like all buttons were removed "
            #                 "(self.sframe.content.winfo_exists(): {}); "
            #                 "not marking verified.".format(
            #                             self.sframe.content.winfo_exists()))
            elif self.groupselected == "ALLOK":
                log.debug("User selected '{}', moving on.".format(oktext))
                self.updatestatus(verified=True)
                self.checkcheck()
            else:
                print(f"User did NOT select '{oktext}', assuming we'll come "
                        "back to this!!")
        #Once done verifying each group:
        if self.runwindow.winfo_exists():
            #verifyT is the last in maybesort, so try again in case it's needed.
            self.maybesort()
    def verifybutton(self,parent,senseid,row,column=0,label=False,**kwargs):
        # This must run one subcheck at a time. If the subcheck changes,
        # it will fail.
        # should move to specify location and fieldvalue in button lambda
        if 'font' not in kwargs:
            kwargs['font']=self.fonts['read']
        if 'anchor' not in kwargs:
            kwargs['anchor']='w'
        framed=self.getframeddata(senseid,notonegroup=True,truncdefn=True)
        text=(framed['formatted'])
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
        if len(self.status[self.type][self.ps][self.profile][self.name][
                                                            'groups']) <2:
            log.debug("No tone groups to distinguish!")
            return
        self.getrunwindow()
        title=_("Review Groups for {} Tone (in ‘{}’ frame)").format(
                                        self.languagenames[self.analang],
                                        self.name
                                        )
        oktext=_('These are all different')
        introtext=_("Congratulations! \nAll your {} with profile {} are sorted "
                "into the groups exemplified below (in the ‘{}’ frame). Do any "
                "of these have the same tone melody? "
                "If so, click on the two groups. If not, click ‘{}’."
                ).format(self.ps,self.profile,self.name,oktext)
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
        self.sorting=self.sframe.content
        row=0
        canary=Label(self.runwindow,text='')
        canary.grid(row=5,column=5)
        canary2=Label(self.runwindow,text='')
        canary2.grid(row=5,column=5)
        for group in self.status[self.type][self.ps][self.profile][self.name][
                                                                    'groups']:
            self.tonegroupbuttonframe(self.sorting,group,row,notonegroup=False,
                                        canary=canary,canary2=canary2)
            row+=1
        """If all is good, destroy this frame."""
        b=Button(self.sorting, text=oktext,
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
        if not self.runwindow.winfo_exists():
            return 1
        if hasattr(self,'groupselected'):
            if self.groupselected == "ALLOK":
                print(f"User selected '{oktext}', moving on.")
                delattr(self,'groupselected')
                return 0
            else:
                group1=self.groupselected
                delattr(self,'groupselected')
                if group1 in self.status[self.type][self.ps][self.profile][
                                                self.name]['groups']:
                    row=self.status[self.type][self.ps][self.profile][
                                            self.name]['groups'].index(group1)
                else:
                    log.error("Group {} isn't found in list {}!".format(group1,
                                self.status[self.type][self.ps][self.profile][
                                                        self.name]['groups']))
                    row=len(self.status[self.type][self.ps][self.profile][
                                                        self.name]['groups'])+1
                self.tonegroupbuttonframe(self.sorting,group1,row,
                                        notonegroup=False,
                                        label=True, font=self.fonts['readbig'],
                                        canary=canary,canary2=canary2)
                log.debug('self.tonegroups: {}; group1: {}'.format(self.status[
                    self.type][self.ps][self.profile][self.name]['groups'],
                    group1))
                self.runwindow.wait_window(canary2)
                #On second button press/exit:
                if not self.runwindow.winfo_exists(): #i.e., user exits by now
                    return 1
                if hasattr(self,'groupselected'):
                    if self.groupselected == "ALLOK":
                        print(f"User selected '{oktext}', moving on.")
                        delattr(self,'groupselected')
                        return 0
                    else:
                        self.runwindow.wait()
                        log.debug("Now we're going to join groups {} and {}, "
                            "marking them both unverified.".format(group1,
                                                            self.groupselected))
                        """All the senses we're looking at, by ps/profile"""
                        self.updatebysubchecksenseid(group1,self.groupselected)
                        self.status[self.type][self.ps][self.profile][
                                self.name]['groups'].remove(group1)
                        self.subcheck=group1
                        self.updatestatus() #not verified=True --if any joined.
                        self.subcheck=self.groupselected
                        self.updatestatus() #not verified=True --if any joined.
                        exit=self.joinT() #keep joining until OK or exit
                        return exit #pass return back up the chain
        """'These are all different' doesn't need to be saved anywhere, as this
        can happen at any time. Just move on to verification, where each group's
        sameness will be verified and recorded."""
    def updatebysubchecksenseid(self,oldtonevalue,newtonevalue):
        """This is all the words in the database with the given
        location:value correspondence (any ps/profile)"""
        lst2=self.db.get('senseidbyexfieldvalue',fieldtype='tone',
                                location=self.name,fieldvalue=oldtonevalue)
        """This intersects the two, to get only one location:value
        correspondence, only within the ps/profile combo we're looking
        at."""
        senseids=self.senseidsincheck(lst2)
        for senseid in senseids:
            """This updates the fieldvalue from 'fieldvalue' to
            'newfieldvalue'."""
            self.db.updateexfieldvalue(senseid=senseid,fieldtype='tone',
                                location=self.name,fieldvalue=oldtonevalue,
                                newfieldvalue=newtonevalue)
    def addtonegroup(self):
        log.info("Adding a tone group!")
        self.gettonegroups()
        values=[0,] #always have something here
        for i in self.status[self.type][self.ps][self.profile][self.name][
                                                                    'groups']:
            try:
                values+=[int(i)]
            except:
                log.info('Tone group {} cannot be interpreted as an integer!'
                        ''.format(i))
        newgroup=max(values)+1
        self.status[self.type][self.ps][self.profile][self.name]['groups'
                                                        ].append(str(newgroup))
        return str(newgroup)
    def addtonefieldex(self,senseid,framed):
        guid=None
        if self.groupselected == None or self.groupselected == '':
            log.error("groupselected: {}; this should never happen"
                        "".format(self.groupselected))
            exit()
        log.debug("Adding {} value to {} location in 'tone' fieldtype, "
                "senseid: {} guid: {} (in main_lift.py)".format(
                    self.groupselected,
                    self.name,
                    senseid,
                    guid))
        self.db.addexamplefields(
                                    guid=guid,senseid=senseid,
                                    analang=self.analang,
                                    glosslang=self.glosslang,
                                    glosslang2=self.glosslang2,
                                    forms=framed,
                                    # langform=framed[self.analang],
                                    # glossform=framed[self.glosslang],
                                    # gloss2form=framed[self.glosslang2],
                                    fieldtype='tone',location=self.name,
                                    fieldvalue=self.groupselected #,
                                    # ps=None #,showurl=True
                                    )
        tonegroup=firstoflist(self.db.get('exfieldvalue', senseid=senseid,
                    fieldtype='tone', location=self.name))
        if tonegroup != self.groupselected:
            log.error("Field addition failed! LIFT says {}, not {}.".format(
                                                tonegroup,self.groupselected))
        else:
            log.error("Field addition succeeded! LIFT says {}, == {}.".format(
                                                tonegroup,self.groupselected))
        self.subcheck=self.groupselected
        self.updatestatus() #this marks the group unverified.
    def addtonefieldpron(self,guid,framed):
        senseid=None
        self.db.addpronunciationfields(
                                    guid,senseid,self.analang,self.glosslang,
                                    self.glosslang2,
                                    lang='en',
                                    forms=framed,
                                    # langform=framed[self.analang],
                                    # glossform=framed[self.glosslang],
                                    # gloss2form=framed[self.glosslang2],
                                    fieldtype='tone',location=self.name,
                                    fieldvalue=self.groupselected,
                                    ps=None
                                    )
    def getsenseidsbytoneUFgroups(self):
        print("Looking for sensids by UF tone groups for",self.profile,self.ps)
        sorted={}
        """Still working on one ps-profile combo at a time."""
        self.getidstosort() #just in case this changed
        for senseid in self.senseidstosort: #I should be able to make this a regex...
            toneUFgroup=firstoflist(self.db.get('toneUFfieldvalue', senseid=senseid,
                fieldtype='tone' # Including any lang at this point.
                # ,showurl=True
                ))
            if toneUFgroup not in sorted:
                sorted[toneUFgroup]=[senseid]
            else:
                sorted[toneUFgroup]+=[senseid]
        self.toneUFgroups=list(dict.fromkeys(sorted))
        log.debug("UFtonegroups (getsenseidsbytoneUFgroups): {}".format(
                                                            self.toneUFgroups))
        return sorted
    def gettoneUFgroups(self): #obsolete?
        log.debug("Looking for UF tone groups for {}-{} slice".format(self.profile,
                                                                    self.ps))
        toneUFgroups=[]
        """Still working on one ps-profile combo at a time."""
        for senseid in self.senseidstosort: #I should be able to make this a regex...
            toneUFgroups+=self.db.get('toneUFfieldvalue', senseid=senseid,
                fieldtype='tone' # Including any lang at this point.
                # ,showurl=True
                )
        self.toneUFgroups=list(dict.fromkeys(toneUFgroups))
    def gettonegroups(self):
        # This depends on self.ps, self.profile, and self.name
        # And sortingstatus, or at least
        # This is where we go into the LIFT file to see what's actually there.
        # It should not be used to affirm that often; sortT/joinT manage this.
        log.log(3,"Looking for tone groups for {} frame".format(self.name))
        tonegroups=[]
        for senseid in self.senseidstosort: #This is a ps-profile slice
            tonegroup=self.db.get('exfieldvalue', senseid=senseid,
                        fieldtype='tone', location=self.name)#, showurl=True)
            if tonegroup in ['NA','', None]:
                log.error("tonegroup {} found in sense {} under location {}!"
                    "".format(tonegroup,senseid,self.name))
            else:
                tonegroups+=tonegroup
        groups=self.status[self.type][self.ps][self.profile][self.name][
                                    'groups']=list(dict.fromkeys(tonegroups))
        log.debug("gettonegroups groups: {}".format(groups))
        if groups != []:
            for value in ['NA', '', None]: #can None be an element in alist?
                if value in groups:
                    log.error("Found (and removing) value {} in {}-{} for {} "
                            "frame: {}".format(value,self.ps,self.profile,
                            self.name,groups))
                    # exit()
                    groups.remove(value)
        log.debug('gettonegroups ({}): {}'.format(self.name,groups))
        verified=self.status[self.type][self.ps][self.profile][self.name][
                                                                    'done']
        for v in verified:
            if v not in groups:
                log.error("Removing verified group {} not in actual groups: {}!"
                            "".format(v, groups))
                verified.remove(v)
        self.storesettingsfile(setting='status')
    def marksortedguid(self,guid):
        """I think these are only valuable during a check, so we don't have to
        constantly refresh sortingstatus() from the lift file."""
        """These four functions should be generalizable"""
        self.guidssorted.append(guid)
        self.guidsunsorted.remove(guid)
    def markunsortedguid(self,guid):
        self.guidsunsorted.append(guid)
        self.guidssorted.remove(guid)
    def marksortedsenseid(self,senseid):
        """I think these are only valuable during a check, so we don't have to
        constantly refresh sortingstatus() from the lift file."""
        self.senseidssorted.append(senseid)
        if senseid in self.senseidsunsorted:
            self.senseidsunsorted.remove(senseid)
            if len(self.senseidsunsorted) == 0:
                self.status[self.type][self.ps][self.profile][self.name][
                                                        'tosort']=False
        else:
            log.error("Sense id {} not found in unsorted senseids! ({}) "
                        "".format(senseid,self.senseidsunsorted))
    def markunsortedsenseid(self,senseid):
        self.senseidsunsorted.append(senseid)
        self.status[self.type][self.ps][self.profile][self.name]['tosort']=True
        if senseid in self.senseidssorted:
            self.senseidssorted.remove(senseid)
        else:
            log.error("Sense id {} not found in sorted senseids! ({}) "
                        "".format(senseid,self.senseidsunsorted))
    def getidstosort(self):
        #This depends on self.ps and self.profile, but not self.name
        """These variables should not have to be reset between checks"""
        self.senseidstosort=list(self.profilesbysense[self.ps]
                                                    [self.profile])
    def sortingstatus(self):
        #This should have self.ps, self.profile and self.name set already
        self.getidstosort() #This is a ps-profile slice, but reset per frame
        self.senseidssorted=[]
        self.senseidsunsorted=[]
        for senseid in self.senseidstosort:
            if (self.db.get('exfieldvalue',
                            senseid=senseid,
                            location=self.name, #because it's relevant to this
                            fieldtype='tone')
                            ) != []:
                self.senseidssorted+=[senseid]
            else:
                self.senseidsunsorted+=[senseid]
        if len(self.senseidsunsorted) >0:
            self.status[self.type][self.ps][self.profile][self.name][
                                                                'tosort']=True
        else:
            self.status[self.type][self.ps][self.profile][self.name][
                                                                'tosort']=False
    def settonevariablesbypsprofile(self):
        # This depends on self.ps, self.profile, and self.name
        # Do this only on changing frames:
        self.makestatusdict() #Fills an existing hole in status file sructure
        #The following depends on the above for structure
        self.sortingstatus() #sets self.senseidssorted and senseidsunsorted
        self.gettonegroups() #sets self.status...['groups'] for a frame
    def tryNAgain(self):
        for senseid in self.senseidstosort: #this is a ps-profile slice
            self.db.rmexfields(senseid=senseid,fieldtype='tone',
                                location=self.name,fieldvalue='NA',
                                showurl=True
                                )
        self.checkcheck() #redraw the table
        self.maybesort()
    def getanotherskip(self,parent):
        """This function presents a group of buttons for the user to choose
        from, one for each tone group in that location/ps/profile in the
        database, plus one for the user to indicate that the word doesn't
        belong in any of those (new group), plus one to for the user to
        indicate that the word/frame combo doesn't work (skip)."""
        row=0
        firstOK=_("This word is OK in this frame")
        newgroup=_("Different")
        skip=_("Skip this word/phrase")
        """This should just add a button, not reload the frame"""
        row+=10
        if self.status[self.type][self.ps][self.profile][self.name]['groups'
                                                                        ] == []:
            bf=Frame(parent)
            bf.grid(column=0, row=row, sticky="ew")
            b=Button(bf, text=firstOK,
                            cmd=lambda:returndictdestroynsortnext(self,bf,
                                        {'groupselected':"NONEOFTHEABOVE"}),
                            anchor="w",
                            font=self.fonts['instructions']
                            )
            b.grid(column=0, row=0, sticky="ew")
            row+=1
        b=Button(parent, text=newgroup,
                        cmd=lambda:returndictnsortnext(self,parent,
                                    {'groupselected':"NONEOFTHEABOVE"}),
                        anchor="w",
                        font=self.fonts['instructions']
                        )
        b.grid(column=0, row=row, sticky="ew")
        row+=1
        b2=Button(parent, text=skip,
                        cmd=lambda:returndictnsortnext(self,parent,
                                    {'groupselected':"NA"}),
                        anchor="w",
                        font=self.fonts['instructions']
                        )
        b2.grid(column=0, row=row+1, sticky="ew")
    def tonegroupbuttonframe(self,parent,group,row,column=0,label=False,canary=None,canary2=None,alwaysrefreshable=False,**kwargs):
        if 'font' not in kwargs:
            kwargs['font']=self.fonts['read']
        if 'anchor' not in kwargs:
            kwargs['anchor']='w'
        if 'notonegroup' not in kwargs:
            notonegroup=True
        else:
            notonegroup=kwargs['notonegroup']
            del kwargs['notonegroup']
        example=self.getex(group,notonegroup=notonegroup,truncdefn=True)
        if example is None:
            log.error("Apparently the example for tone group {} in frame {} "
                        "came back {}".format(group,self.name,example))
            return
        if 'renew' in kwargs:
            if kwargs['renew'] == True:
                log.info("Resetting tone group example ({}): {} of {} examples"
                        "".format(group,self.exs[group],example['n']))
                del self.exs[group]
            del kwargs['renew']
        framed=example['framed']
        if framed is None:
            log.error("Apparently the framed example for tone group {} in "
                        "frame {} came back {}".format(group,self.name,example))
            return
        text=(framed['formatted'])
        """This should maybe be brought up a level in frames?"""
        bf=Frame(parent)
        bf.grid(column=column, row=row, sticky="ew")
        if label==True:
            b=Label(bf, text=text, **kwargs)
            b.grid(column=0, row=0, sticky="ew", ipady=15) #Inside the buttons
        else:
            b=Button(bf, text=text,
                    cmd=lambda p=parent:returndictnsortnext(self,p,
                                        {'groupselected':group},
                                        canary=canary,canary2=canary2),**kwargs)
            b.grid(column=0, row=0, sticky="ew", ipady=15) #Inside the buttons
            if example['n'] > 1 or alwaysrefreshable == True:
                bc=Button(bf, image=self.parent.photo['change'], #🔃 not in tck
                                cmd=lambda p=parent:self.tonegroupbuttonframe(
                                    parent=parent,
                                    group=group,notonegroup=notonegroup,
                                    canary=canary,canary2=canary2,
                                    row=row,column=column,label=label,
                                    alwaysrefreshable=alwaysrefreshable,
                                    renew=True),
                                text=example['n'],
                                compound='left',
                                **kwargs)
                bc.grid(column=1, row=0, sticky="nsew", ipady=15) #In buttonframe
        return bf
    def printentryinfo(self,guid):
        outputs=[
                    nn(self.db.citationorlexeme(guid=guid)),
                    nn(self.db.glossordefn(guid=guid,lang=self.glosslang))
                ]
        if self.glosslang2 is not None: #only give this if the user wants it.
            outputs.append(nn(self.db.glossordefn(guid=guid,
                                        lang=self.glosslang2)))
        outputs.append(nn(self.db.get('pronunciationfieldvalue',
                                        fieldtype='tone',
                                        location=self.subcheck,guid=guid)))
        return '\t'.join(outputs)
    def guesssubcheck(self):
        if self.type == 'CV': #Dunno how to guess this yet...
            if self.subcheck in ([x[0] for x in self.subchecksprioritized['V']+
                                self.subchecksprioritized['C']+
                                self.subchecksprioritized['T']
                                ]):
                self.subcheck=self.scount[self.ps]['C'][0]+self.scount[self.ps]['V'][0]
        else:
            self.subcheck=firstoflist(self.subchecksprioritized[self.type],
                                                            othersOK=True)[0]
    def getsubchecksprioritized(self):
        """Tone doesn't have subchecks, so we just make it 'None' here."""
        """I really should be able to order these..."""
        self.subchecksprioritized={"V":self.scount[self.ps]['V'], #self.db.v[self.analang],
                                "C":self.scount[self.ps]['C'], #self.db.c[self.analang],
                                "CV":'',
                                "T":[(None,None),] #We should fix this some day
                                }
    """Doing stuff"""
    def getrunwindow(self):
        """Can't test for widget/window if the attribute hasn't been assigned,"
        but the attribute is still there after window has been killed, so we
        need to test for both."""
        if hasattr(self,'runwindow') and (self.runwindow.winfo_exists()):
            if self.debug == True:
                log.info("Runwindow already there! Resetting frame...")
            self.runwindow.resetframe() #I think I'll always want this here...
        else:
            t=(_("Run Window"))
            self.runwindow=Window(self.frame,title=t)
            self.runwindow.title(t)
        self.runwindow.wait()
    def runcheck(self):
        self.storesettingsfile() #This is not called in checkcheck.
        t=(_('Run Check'))
        log.info("Running check...")
        i=0
        if self.analang is None or self.analang == "Null":
            text=(_('Error: please set language first!')+' ('+
            str(self.analang)+')')
            Label(self.runwindow.frame, text=text
                          ).grid(column=0, row=i)
            i+=1
        if self.ps is None or self.ps == "Null":
            text=_('Error: please set Grammatical category first!')+' ('
            +str(self.ps)+')'
            Label(self.runwindow.frame,text=text).grid(column=0, row=i)
            i+=1
        if (((self.subcheck is None) or (self.subcheck == "Null"))
                and self.type != 'T'):
            Label(self.runwindow.frame,
                          text='Error: please set Subcheck first! ('
                          +str(self.subcheck)+')'
                          ).grid(column=0, row=i)
            i+=1
        if not (self.analang is None or self.analang == "Null" or
                self.ps is None or self.ps == "Null" or
                ((self.subcheck is None or self.subcheck == "Null") and
                self.type != 'T')):
            # def header():
            #     row=0
            #     texts=((_('Working with Language: ')+self.analang),
            #             (_('Working with Grammatical category: ')+self.ps),
            #             (_('Verifying: ')+self.subcheck))
            #     for text in texts:
            #         Label(self.runwindow.frame, text=text
            #                 ).grid(column=0, row=row)
            #         row+=1
            if self.type == 'T':
                if self.name not in self.toneframes[self.ps]:
                    exit=self.getcheck()
                    print(exit, self.name)
                    if exit is 1:
                        self.runcheck()
                    return
                self.getidstosort() #not a bad idea to refresh this here
                self.maybesort()
            else: #do the CV checks
                self.getresults()
    def record(self):
        if ((self.fs == None) or (self.sample_format == None)
                or (self.audio_card_index == None)):
            self.soundcheck()
        self.storesettingsfile()
        if self.type == 'T':
            self.showtonegroupexs()
        else:
            self.showentryformstorecord()
    def makelabelsnrecordingbuttons(self,parent,sense):
        t=self.getframeddata(sense['nodetoshow'],noframe=True)[
                                            self.analang]#+'\t'+sense['gloss']
        for g in ['gloss','gloss2']:
            if (g in sense) and (sense[g] is not None):
                t+='\t‘'+sense[g]
                if ('plnode' in sense) and (sense['nodetoshow'] is sense['plnode']):
                    t+=" (pl)"
                if ('impnode' in sense) and (sense['nodetoshow'] is sense['impnode']):
                    t+="!"
                t+='’'
        lxl=Label(parent, text=t)
        lcb=RecordButtonFrame(parent,self,id=sense['guid'],
                                            node=sense['nodetoshow'],
                                            gloss=sense['gloss'])
        lcb.grid(row=sense['row'],column=sense['column'],sticky='w')
        lxl.grid(row=sense['row'],column=sense['column']+1,sticky='w')
    def showentryformstorecordpage(self):
        if not self.runwindow.winfo_exists():
            log.info('no runwindow; quitting!')
            return
        if not self.runwindow.frame.winfo_exists():
            log.info('no runwindow frame; quitting!')
            return
        self.runwindow.resetframe()
        self.runwindow.wait()
        for psprofile in self.profilecounts:
            if self.ps==psprofile[2] and self.profile==psprofile[1]:
                count=psprofile[0]
        text=_("Record {} {} Words: click ‘Record’, talk, "
                "and release ({} words)".format(self.profile,self.ps,
                                                count))
        instr=Label(self.runwindow.frame, anchor='w',text=text)
        instr.grid(row=0,column=0,sticky='w')
        buttonframes=ScrollingFrame(self.runwindow.frame)
        buttonframes.grid(row=1,column=0,sticky='w')
        row=0
        done=list()
        for senseid in self.profilesbysense[self.ps][self.profile]:
            sense={}
            sense['column']=0
            sense['row']=row
            sense['guid']=firstoflist(self.db.get('guidbysense',
                                        senseid=senseid))
            if sense['guid'] in done: #only the first of multiple senses
                continue
            else:
                done.append(sense['guid'])
            sense['lxnode']=firstoflist(self.db.get('lexemenode',
                                                guid=sense['guid'],
                                                lang=self.analang))
            sense['lcnode']=firstoflist(self.db.get('citationnode',
                                                guid=sense['guid'],
                                                lang=self.analang))
            sense['gloss']=firstoflist(self.db.glossordefn(
                                                guid=sense['guid'],
                                                lang=self.glosslang
                                                ),othersOK=True)
            if ((hasattr(self,'glosslang2')) and
                    (self.glosslang2 is not None)):
                sense['gloss2']=firstoflist(self.db.glossordefn(
                                                guid=sense['guid'],
                                                lang=self.glosslang2
                                                ),othersOK=True)
            if ((sense['gloss'] is None) and
                    (('gloss2' in sense) and (sense['gloss2'] is None))):
                continue #We can't save the file well anyway; don't bother
            if self.db.pluralname is not None:
                sense['plnode']=firstoflist(self.db.get('fieldnode',senseid=sense['guid'],
                                        lang=self.analang,
                                        fieldtype=self.db.pluralname))
            if self.db.imperativename is not None:
                sense['impnode']=firstoflist(self.db.get('fieldnode',senseid=sense['guid'],
                                        lang=self.analang,
                                        fieldtype=self.db.imperativename))
            if sense['lcnode'] != None:
                # print('lcnode!')
                sense['nodetoshow']=sense['lcnode']
            else:
                # print('lxnode!')
                sense['nodetoshow']=sense['lxnode']
            self.makelabelsnrecordingbuttons(buttonframes.content,sense)
            for node in ['plnode','impnode']:
                if (node in sense) and (sense[node] != None):
                    sense['column']+=2
                    sense['nodetoshow']=sense[node]
                    self.makelabelsnrecordingbuttons(buttonframes.content,
                                                    sense)
            row+=1
        self.runwindow.waitdone()
        self.runwindow.wait_window(self.runwindow.frame)
    def showentryformstorecord(self,justone=True):
        """Save these values before iterating over them"""
        #Convert to iterate over local variables
        psori=self.ps
        profileori=self.profile
        self.getrunwindow()
        if justone==True:
            self.showentryformstorecordpage()
        else:
            for psprofile in self.profilecountsValid:
                if self.runwindow.winfo_exists():
                    self.ps=psprofile[2]
                    self.profile=psprofile[1]
                    nextb=Button(self.runwindow,text=_("Next Group"),
                                            cmd=self.runwindow.resetframe) # .frame.destroy
                    nextb.grid(row=0,column=1,sticky='ne')
                    self.showentryformstorecordpage()
            self.ps=psori
            self.profile=profileori
    def showsenseswithexamplestorecord(self,senses=None,progress=None,skip=False):
        def setskip(event):
            self.runwindow.frame.skip=True
            entryframe.destroy()
        self.getrunwindow()
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
            examples=self.db.get('example',senseid=senseid)
            if examples == []:
                log.debug(_("No examples! Add some, then come back."))
                continue
            if ((self.runwindow.frame.skip == True) and
                (lift.atleastoneexamplehaslangformmissing(
                                                    examples,
                                                    self.audiolang) == False)):
                continue
            row=0
            if not self.runwindow.winfo_exists():
                return 1
            entryframe=Frame(self.runwindow.frame)
            entryframe.grid(row=1,column=0)
            if progress is not None:
                progressl=Label(self.runwindow.frame, anchor='e',
                    font=self.fonts['small'],
                    text="({}/{})".format(*progress)
                    )
                progressl.grid(row=0,column=2,sticky='ne')
            """This is the title for each page: isolation form and glosses."""
            framed=self.getframeddata(senseid,noframe=True,notonegroup=True,
                                        truncdefn=True)
            if framed[self.analang]=='noform':
                entryframe.destroy()
                continue
            text=framed['formatted']
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
                framed=self.getframeddata(example,noframe=True,truncdefn=True)
                if framed[self.analang] is None:
                    continue
                row+=1
                """If I end up pulling from example nodes elsewhere, I should
                probably make this a function, like getframeddata"""
                text=framed['formatted']
                rb=RecordButtonFrame(examplesframe,self,id=senseid,node=example,
                                    form=nn(framed[self.analang]),
                                    gloss=nn(framed[self.glosslang])
                                    ) #no gloss2; form/gloss just for filename
                rb.grid(row=row,column=0,sticky='w')
                Label(examplesframe, anchor='w',text=text
                                        ).grid(row=row, column=1, sticky='w')
            row+=1
            d=Button(examplesframe, text=_("Done/Next"),command=entryframe.destroy)
            d.grid(row=row,column=0)
            self.runwindow.waitdone()
            examplesframe.wait_window(entryframe)
            if not self.runwindow.winfo_exists():
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
            self.examplespergrouptorecord=5
            self.storesettingsfile()
        torecord=self.getsenseidsbytoneUFgroups()
        skip=False
        if len(torecord) == 0:
            print("How did we get no UR tone groups?",self.profile,self.ps,
                    "\nHave you run the tone report recently?"
                    "\nDoing that for you now...")
            self.tonegroupreport(silent=True)
            self.showtonegroupexs()
            return
        batch={}
        for i in range(self.examplespergrouptorecord):
            batch[i]=[]
            for toneUFgroup in torecord: #self.toneUFgroups:
                print(i,len(torecord[toneUFgroup]),toneUFgroup,torecord[toneUFgroup])
                if len(torecord[toneUFgroup]) > i: #no small piles.
                    batch[i]+=[torecord[toneUFgroup][i]]
                else:
                    print("Not enough examples, moving on:",i,toneUFgroup)
        print(_('Preparing to record examples from each tone group ({}) '
                ).format(torecord.keys()))
        for i in range(self.examplespergrouptorecord):
            log.info(_('Giving user the number {} example from each tone '
                    'group ({})'.format(i,torecord.keys())))
            exited=self.showsenseswithexamplestorecord(batch[i],
                                        (i, self.examplespergrouptorecord),
                                        skip=skip)
            if exited == 'skip':
                skip=True
            if exited == True:
                return
        if self.runwindow.winfo_exists():
            self.runwindow.waitdone()
            self.runwindow.resetframe()
            Label(self.runwindow.frame, anchor='w',font=self.fonts['read'],
            text=_("All done! Sort some more words, and come back.")
            ).grid(row=0,column=0,sticky='w')
            Button(self.runwindow.frame,
                    text=_("Continue to next syllable profile"),
                    command=next).grid(row=1,column=0)
    def getresults(self):
        self.getrunwindow()
        self.makeresultsframe()
        self.adhocreportfileXLP=''.join([str(self.reportbasefilename)
                                        ,'_',str(self.ps)
                                        ,'-',str(self.profile)
                                        ,'_',str(self.name)
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
        text=(_("{} roots of form {} by {}".format(self.ps,self.profile,
                                                            self.name)))
        Label(self.results, text=text).grid(column=0, row=i)
        self.runwindow.wait()
        si=xlp.Section(xlpr,text)
        # p=xlp.Paragraph(si,instr)
        font=self.frame.fonts['read']
        self.results.scroll=ScrollingFrame(self.results)
        self.results.scroll.grid(column=0, row=1)
        senseid=0 # in case the following doesn't find anything:
        for self.subcheck in self.s[self.analang][self.type]:
            log.debug('self.subcheck: {}'.format(self.subcheck))
            self.buildregex() #It would be nice fo this to iterate through...
            # for senseid in self.profilesbysense[self.ps][self.profile]:
            # print(self.profilesbysense[self.ps][self.profile][0])
            # print(self.db.citationorlexeme(self.profilesbysense[self.ps][self.profile][0]))
            # print(firstoflist(self.db.citationorlexeme(self.profilesbysense[self.ps][self.profile][0])))
            senseidstocheck=self.db.senseidformsbyregex(self.regex,
                                                self.analang,
                                                ps=self.ps)
            # senseidstocheck= filter(lambda x: self.regex.search(
            #                         firstoflist(self.db.citationorlexeme(x))),
            #             self.profilesbysense[self.ps][self.profile])
            if len(senseidstocheck)>0:
                id=rx.id('x'+self.ps+self.profile+self.name+self.subcheck)
                ex=xlp.Example(si,id)
            for senseid in senseidstocheck: #self.senseidformstosearch[lang][ps]
                # where self.regex(self.senseidformstosearch[lang][ps][senseid]):
                """This regex is compiled!"""
                framed=self.getframeddata(senseid,noframe=True)
                # if self.regex(framed[self.analang]):
                o=framed['formatted']
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
                for lang in [self.analang, self.glosslang, self.glosslang2]:
                    col+=1
                    if lang != None:
                        Label(self.results.scroll.content,
                            text=framed[lang], font=font,
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
        log.log(2,'self.profile:',self.profile)
        log.log(2,'self.type:',self.type)
        maxcount=re.subn(self.type, self.type, self.profile)[1]
        if self.profile is None:
            print("It doesn't look like you've picked a syllable profile yet.")
            return
        """Don't need this; only doing count=1 at a time. Let's start with
        the easier ones, with the first occurrance changed."""
        if self.debug is True:
            print('maxcount='+str(maxcount))
            print(self.name)
        self.regexCV=str(self.profile) #Let's set this before changing it.
        """One pass for all regexes, S3, then S2, then S1, as needed."""
        types=['V','C']
        if 'x' in self.name:
            if self.subcheckcomparison in self.s[self.analang]['C']:
                types=['C','V']
        for type in types:
            if type not in self.type:
                continue
            S=str(self.type)
            regexS='[^'+S+']*'+S #This will be a problem if S=NC or CG...
            compared=False
            for occurrence in reversed(range(maxcount)):
                occurrence+=1
                if re.search(S+str(occurrence),self.name) != None:
                    """Get the (n=occurrence) S, regardless of intervening
                    non S..."""
                    regS='^('+regexS*(occurrence-1)+'[^'+S+']*)('+S+')'
                    if 'x' in self.name:
                        if compared == False: #occurrence == 2:
                            replS='\\1'+self.subcheckcomparison
                            compared=True
                        else: #if occurrence == 1:
                            replS='\\1'+self.subcheck
                    else:
                        replS='\\1'+self.subcheck
                    self.regexCV=re.sub(regS,replS,self.regexCV, count=1)
        if self.debug ==True:
            print('self.profile='+str(self.profile)+str(type(self.profile)))
            print('self.type='+str(self.type)+str(type(self.type)))
            print('self.name='+str(self.name)+str(type(self.name)))
            print('self.subcheck='+str(self.subcheck)+str(type(self.subcheck)))
            print('self.regexCV='+str(self.regexCV)+str(type(self.regexCV)))
        """Final step: convert the CVx code to regex, and store in self."""
        self.regex=rx.fromCV(self,lang=self.analang,
                            word=True, compile=True)
    def buildXLPtable(self,parent,caption,yterms,xterms,values,ycounts=None):
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
                    cell=xlp.Cell(r,content=linebreakwords(col),
                                header=True,
                                linebreakwords=True)
                elif col == 'header':
                    log.log(2,"header column")
                    if ycounts != None:
                        ccontents='{} ({})'.format(row,ycounts(row))
                    else:
                        ccontents='{}'.format(row)
                    cell=xlp.Cell(r,content=ccontents,
                                header=True)
                else:
                    log.log(2,"Not a header")
                    log.log(2,"value ({},{}):{}".format(col,row,
                                                        values(col,row)))
                    value=values(col,row)
                    cell=xlp.Cell(r,content=value)
    def tonegroupsjoinrename(self):
        def submitform():
            uf=named.get()
            log.debug("name: {}".format(uf))
            if uf == "":
                log.debug("Give a name for this UF tone group!")
                return
            if uf in self.toneUFgroups:
                log.debug("That name is already there!")
                return
            for group in groups: #all group variables
                groupstr=group.get() #value, name if selected, 0 if not
                if groupstr in senseidsbygroup: #selected ones only
                    log.debug("Changing values from {} to {} for the following "
                            "senseids: {}".format(groupstr,uf,
                                                    senseidsbygroup[groupstr]))
                    for senseid in senseidsbygroup[groupstr]:
                        self.db.addtoneUF(senseid,uf,analang=self.analang)
            self.runwindow.destroy()
            self.tonegroupsjoinrename() #call again, in case needed
        def done():
            self.runwindow.destroy()
        def refreshgroups():
            senseidsbygroup=self.getsenseidsbytoneUFgroups() #>self.toneUFgroups
        self.getrunwindow()
        title=_("Join/Rename Draft Underlying {}-{} tone groups".format(
                                                        self.ps,self.profile))
        self.runwindow.title(title)
        padx=50
        pady=10
        Label(self.runwindow,text=title,font=self.fonts['title'],
                ).grid(row=0,column=0,sticky='ew')
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
                "analysis). ".format(self.ps,self.profile,self.program['name']))
        Label(self.runwindow,text=text).grid(row=1,column=0,sticky='ew')
        qframe=Frame(self.runwindow)
        qframe.grid(row=2,column=0,sticky='ew')
        text=_("What do you want to call this UF tone group for {}-{} words?"
                "".format(self.ps,self.profile))
        Label(qframe,text=text).grid(row=0,column=0,sticky='ew',pady=20)
        named=tkinter.StringVar() #store the new name here
        namefield = EntryField(qframe,textvariable=named)
        namefield.grid(row=0,column=1)
        text=_("Select the groups below that you want in this group, then "
                "click ==>".format(self.ps))
        Label(qframe,text=text).grid(row=1,column=0,sticky='ew',pady=20)
        senseidsbygroup=self.getsenseidsbytoneUFgroups() #>self.toneUFgroups
        sub_btn=Button(qframe,text = _("OK"), command = submitform, anchor ='c')
        sub_btn.grid(row=1,column=1,sticky='w')
        done_btn=Button(qframe,text = _("Done —no change"), command = done,
                                                                    anchor ='c')
        done_btn.grid(row=1,column=2,sticky='w')
        groups=list()
        row=0
        scroll=ScrollingFrame(self.runwindow)
        for group in self.toneUFgroups: #make a variable and button to select
            idn=self.toneUFgroups.index(group)
            groups.append(tkinter.StringVar())
            CheckButton(scroll.content, text = group,
                                variable = groups[idn],
                                onvalue = group, offvalue = 0,
                                ).grid(row=row,column=0,sticky='ew')
            row+=1
        scroll.grid(row=3,column=0,sticky='ew')
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
            for senseid in senseidsbygroup[group]:
                for location in locations:
                    if location not in values[group]:
                        values[group][location]=list()
                    groupvalue=self.db.get('exfieldvalue',senseid=senseid,
                        location=location,fieldtype='tone')
                    # Save this info by group
                    if ((groupvalue is not []) and
                            (firstoflist(groupvalue) not in values[group][
                                                                    location])):
                        values[group][location]+=groupvalue
        log.info("Done collecting groups by location for each UF group.")
        return values
    def tonegroupsbysenseidlocation(self):
        #outputs dictionary keyed to [senseid][location]=group
        self.getidstosort() #in case you didn't just run a check
        self.getlocations()
        output={}
        locations=self.locations[:]
        # Collect location:value correspondences, by sense
        for senseid in self.senseidstosort:
            output[senseid]={}
            for location in locations:
                output[senseid][location]={}
                group=self.db.get('exfieldvalue',senseid=senseid,
                    location=location,fieldtype='tone')
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
            group=self.ps+'_'+self.profile+'_'+str(x)
            groups[group]={}
            groups[group]['values']=value
            groups[group]['senseids']=[]
            x+=1
        log.info('Groups set up; adding senseids to groups now. ({})'.format(groups.keys()))
        return groups
    def senseidstogroupUFs(self,output,groups):
        for senseid in self.senseidstosort:
            for group in groups:
                if str(output[senseid]) == str(groups[group]['values']):
                    groups[group]['senseids']+=[senseid]
                    self.db.addtoneUF(senseid,group,analang=self.analang)
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
                valuesbylocation[location][group]=groups[group]['values'][
                                                                    location]
        return dictscompare(valuesbylocation,ignore=['NA',None],flat=False)
    def tonegroupreport(self,silent=False,bylocation=False,default=True):
        #default=True redoes the UF analysis (removing any joining/renaming)
        log.info("Starting report...")
        self.storesettingsfile()
        self.getrunwindow()
        self.tonereportfile=''.join([str(self.reportbasefilename),'_',
                            self.ps,'_',
                            self.profile,
                            ".ToneReport.txt"])
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
                for location in locations:
                    groupvalues[group][location]=list(groups[group]['values'][
                                                                    location])
        else:
            #make a report without having redone the UF analysis
            #The following line puts out a dictionary keyed by UF group name:
            toreport=self.getsenseidsbytoneUFgroups()
            groupvalues=self.tonegroupsbyUFlocation(toreport)
            grouplist=self.toneUFgroups
            locations=self.locations[:]
        log.debug("groups (tonegroupreport): {}".format(grouplist))
        log.debug("locations (tonegroupreport): {}".format(locations))
        r = open(self.tonereportfile, "w", encoding='utf-8')
        title=_("Tone Report")
        self.runwindow.title(title)
        self.runwindow.scroll=ScrollingFrame(self.runwindow.frame)
        window=self.runwindow.scroll.content
        window.row=0
        xlpr=self.xlpstart(reporttype='Tone',bylocation=bylocation)
        s1=xlp.Section(xlpr,title='Introduction')
        text=_("This report follows an analysis of sortings of {} morphemes "
        "(roots or affixes) across the following frames: {}. {} stores these "
        "sortings in lift examples, which are output here, with any glossing "
        "and sound file links found in each lift sense example. "
        "Each group in "
        "this report is distinct from the others, in terms of its grouping "
        "across the multiple frames used. Sound files should be available "
        "through links, if the audio directory with those files is in the same "
        "directory as this file.".format(self.ps,self.locations,
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
        s1s=xlp.Section(xlpr,t)
        caption=' '.join([self.ps,self.profile])
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
        self.buildXLPtable(s1s,caption,yterms=grouplist,xterms=locations,
                            values=lambda x,y:nn(firstoflist(
                            groupvalues[y][x],all=True
                            )),
                            ycounts=lambda x:len(
                            toreport[x]
                            )
                            )
        for group in grouplist: #These already include ps-profile
            log.info("building report for {}".format(group))
            sectitle=_('\nGroup {}'.format(str(group)))
            s1=xlp.Section(xlpr,title=sectitle)
            output(window,r,sectitle)
            l=list()
            for x in groupvalues[group]:
                l.append(x+': '+str(groupvalues[group][x]))
            text=_('Values by frame: {}'.format('\t'.join(l)))
            p1=xlp.Paragraph(s1,text)
            output(window,r,text)
            if bylocation == True:
                textout=list()
                for location in locations:
                    id=rx.id('x'+sectitle+location)
                    e1=xlp.Example(s1,id)
                    for senseid in toreport[group]:
                        #This is for window/text output only, not in XLP file
                        framed=self.getframeddata(senseid,noframe=True,
                                                        notonegroup=True)
                        text=framed['formatted']
                        #This is put in XLP file:
                        examples=self.db.get('examplebylocation',
                                                location=location,
                                                senseid=senseid)
                        for example in examples:
                            # These should already be framed!
                            framed=self.getframeddata(example,noframe=True)
                            self.framedtoXLP(framed,parent=e1,listword=True)
                        if text not in textout:
                            output(window,r,text)
                            textout.append(text)
            else:
                for senseid in toreport[group]: #groups[group]['senseids']:
                    #This is for window/text output only, not in XLP file
                    framed=self.getframeddata(senseid,noframe=True,
                                                    notonegroup=True)
                    text=framed['formatted']
                    #This is put in XLP file:
                    examples=self.db.get('example',senseid=senseid)
                    log.log(2,"{} examples found: {}".format(len(examples),
                                                                    examples))
                    if examples != []:
                        id=self.idXLP(framed)+'_examples'
                        log.log(2,"Using id {}".format(id))
                        e1=xlp.Example(s1,id)
                        for example in examples:
                            # These should already be framed!
                            framed=self.getframeddata(example,noframe=True)
                            self.framedtoXLP(framed,parent=e1,listword=True)
                    output(window,r,text)
        self.runwindow.waitdone()
        xlpr.close()
        text=("Finished in "+str(time.time() - start_time)+" seconds.")
        output(window,r,text)
        text=_("(Report is also available at ("+self.tonereportfile+")")
        output(window,r,text)
        r.close()
    def xlpstart(self,reporttype='adhoc',bylocation=False):
        if reporttype == 'Tone':
            if bylocation == True:
                reporttype='Tone-bylocation'
            reporttype=''.join([str(self.ps),'-',
                            str(self.profile),' ',
                            reporttype])
        elif not re.search('Basic',reporttype): #We don't want this in the title
            reporttype=''.join([str(self.ps),'-',
                            str(self.profile),' ',
                            str(self.name)])
        reportfileXLP=''.join([str(self.reportbasefilename)
                                            ,'_',rx.id(reporttype)
                                            ,'_','ReportXLP.xml'])
        xlpreport=xlp.Report(reportfileXLP,reporttype,
                        self.languagenames[self.analang])
        for lang in [self.analang,self.glosslang,self.glosslang2]:
            if lang != None:
                xlpreport.addlang({'id':lang,'name': self.languagenames[lang]})
        return xlpreport
    def basicreport(self,typestodo=['V']):
        """We iterate across these values in this script, so we save current
        values here, and restore them at the end."""
        #Convert to iterate over local variables
        typeori=self.type
        psori=self.ps
        profileori=self.profile
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
        self.frame.parent.wait() #non-widget parent deiconifies no window...
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
        for self.ps in self.pss[0:2]: #just the first two (Noun and Verb)
            if self.ps not in self.checkcounts:
                self.checkcounts[self.ps]={}
            self.getprofilestodo()
            t=_("{} data: (profiles: {})".format(self.ps,self.profilestodo))
            log.info(t)
            print(t)
            s1=xlp.Section(xlpr,t)
            t=_("This section covers the following top syllable profiles "
                "which are found in {}s: {}".format(self.ps,self.profilestodo))
            p=xlp.Paragraph(s1,t)
            log.info(t)
            print(t)
            for self.profile in self.profilestodo:
                if self.profile not in self.checkcounts[self.ps]:
                    self.checkcounts[self.ps][self.profile]={}
                t=_("{} {}s".format(self.profile,self.ps))
                s2=xlp.Section(s1,t,level=2)
                print(t)
                log.info(t)
                for self.type in typestodo:
                    t=_("{} checks".format(self.typedict[self.type]['sg']))
                    print(t)
                    log.info(t)
                    sid=" ".join([t,"for",self.profile,self.ps+'s'])
                    s3=xlp.Section(s2,sid,level=3)
                    maxcount=re.subn(self.type, self.type, self.profile)[1]
                    """Get these reports from C1/V1 to total number of C/V"""
                    self.typenums=[self.type+str(n+1) for n in range(maxcount)]
                    for typenum in self.typenums:
                        if typenum not in self.basicreported:
                            self.basicreported[typenum]=set()
                    self.wordsbypsprofilechecksubcheck(s3)
        t=_("Summary coocurrence tables")
        s1s=xlp.Section(xlpr,t)
        for self.ps in self.checkcounts:
            s2s=xlp.Section(s1s,self.ps,level=2)
            for self.profile in self.checkcounts[self.ps]:
                s3s=xlp.Section(s2s,' '.join([self.ps,self.profile]),level=3)
                for name in self.checkcounts[self.ps][self.profile]:
                    rows=list(self.checkcounts[self.ps][self.profile][name])
                    nrows=len(rows)
                    if nrows == 0:
                        continue
                    if 'x' in name:
                        cols=list(self.checkcounts[self.ps][self.profile][name][rows[0]])
                    else:
                        cols=['n']
                    ncols=len(cols)
                    if ncols == 0:
                        continue
                    caption=' '.join([self.ps,self.profile,name])
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
                                    self.ps][self.profile][name]))
                            if x1 != 'header' and x2 not in ['header','n']:
                                log.debug("value: {}".format(self.checkcounts[
                                    self.ps][self.profile][name][x1][x2]))
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
                                    value=self.checkcounts[self.ps][
                                                    self.profile][name][x1]
                                else:
                                    value=self.checkcounts[self.ps][
                                                    self.profile][name][x1][x2]
                                cell=xlp.Cell(h,content=value)
        log.info(self.checkcounts)
        xlpr.close()
        log.info("Finished in {} seconds.".format(str(time.time()-start_time)))
        sys.stdout.close()
        sys.stdout=sys.__stdout__ #In case we want to not crash afterwards...:-)
        self.frame.parent.waitdone()
        self.type=typeori
        self.profile=profileori
        self.ps=psori
        self.checkcheck()
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
class Window(tkinter.Toplevel):
    def resetframe(self):
        if self.winfo_exists(): #If this has been destroyed, don't bother.
            if hasattr(self,'frame') and type(self.frame) is Frame:
                self.frame.destroy()
            self.frame=Frame(self.outsideframe)
            self.frame.grid(column=0,row=0,sticky='we')
    def wait(self):
        if hasattr(self,'ww') and self.ww.winfo_exists() == True:
            log.debug("There is already a wait window: {}".format(self.ww))
            return
        self.ww=Wait(self)
    def waitdone(self):
        self.ww.close()
    def __init__(self, parent,
                backcmd=False, exit=True,
                title="No Title Yet!", choice=None,
                *args, **kwargs):
        self.parent=parent
        inherit(self)
        """Things requiring tkinter.Window below here"""
        super(Window, self).__init__()
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
            print ("    self.name: "+selfname)
            log.info("End current window descriptions")
        self.iconphoto(False, self.photo['backgrounded']) #don't want this transparent
        self.title(title)
        # self.parent=parent
        self.resetframe()
        if exit is True:
            e=(_("Exit")) #This should be the class, right?
            self.exitButton=tkinter.Button(self.outsideframe, width=10, text=e,
                                command=self.destroy,
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
class Frame(tkinter.Frame):
    def windowsize(self):
        if not hasattr(self,'configured'):
            self.configured=0
        if self.configured>10:
            return
        availablexy(self)
        """The above script calculates how much screen is left to fill, these
        next two lines give a max widget size to stay in the window."""
        # height=self.parent.winfo_screenheight()-self.otherrowheight
        # width=self.parent.winfo_screenwidth()-self.othercolwidth
        # print('height=',self.parent.winfo_screenheight(),-self.otherrowheight)
        # print('width=',self.parent.winfo_screenwidth(),-self.othercolwidth)
        # print(height,width)
        """This is how much space the contents of the scrolling canvas is asking
        for. We don't need the scrolling frame to be any bigger than this."""
        """These lines are different than for the scrolling frame"""
        contentrw=self.winfo_reqwidth()
        contentrh=self.winfo_reqheight()
        """If the current scrolling frame dimensions are smaller than the
        scrolling content, or else pushing the window off the screen, then make
        the scrolling window the smaller of
            -the scrolling content or
            -the max dimensions, from above."""
        # if self.winfo_width() < contentrw:
        #      self.config(width=contentrw)
        # if self.winfo_width() > self.maxwidth:
        #     self.config(width=self.maxwidth)
        if ((self.winfo_width() < contentrw)
                or (self.winfo_width() > self.maxwidth)):
                self.config(width=min(self.maxwidth,contentrw))
        # if self.winfo_height() < contentrh:
        #     self.config(height=contentrh)
        # if self.winfo_height() > self.maxheight:
        #     self.config(height=self.maxheight)
        if ((self.winfo_height() < contentrh)
                or (self.winfo_height() > self.maxheight)):
            self.config(height=min(self.maxheight,contentrh))
        self.configured+=1
    def __init__(self, parent, **kwargs):
        self.parent = parent
        inherit(self)
        """tkinter.Frame thingies below this"""
        tkinter.Frame.__init__(self,parent,**kwargs)
        self['background']=parent['background']
class ScrollingFrame(Frame):
    def _bound_to_mousewheel(self, event):
        # with Windows OS
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheelMS)
        # with Linux OS
        self.canvas.bind_all("<Button-5>", self._on_mousewheelup)
        self.canvas.bind_all("<Button-4>", self._on_mousewheeldown)
    def _unbound_to_mousewheel(self, event):
        self.canvas.unbind_all("<MouseWheel>")
        self.canvas.unbind_all("<Button-4>")
        self.canvas.unbind_all("<Button-5>")
    def _on_mousewheelMS(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    def _on_mousewheelup(self, event):
        self.canvas.yview_scroll(1,"units")
    def _on_mousewheeldown(self, event):
        self.canvas.yview_scroll(-1,"units")
    def _configure_interior(self, event):
        #This configures self.content
        if not hasattr(self,'configured'):
            self.configured=0
        # print("Configuring interior")
        # update the scrollbars to match the size of the inner frame
        size = (self.content.winfo_reqwidth(), self.content.winfo_reqheight())
        self.canvas.config(scrollregion="0 0 %s %s" % size)
        """This makes sure the canvas is as large as what you put on it"""
        if self.configured <20:
            self.windowsize() #this needs to not keep running
            self.configured+=1
        if self.content.winfo_reqwidth() != self.canvas.winfo_width():
            # update the canvas's width to fit the inner frame
            self.canvas.config(width=self.content.winfo_reqwidth())
        if self.content.winfo_reqheight() != self.canvas.winfo_height():
            # update the canvas's width to fit the inner frame
            self.canvas.config(height=self.content.winfo_reqheight())
    def windowsize(self, event=None):
        availablexy(self) #>self.maxheight, self.maxwidth
        """This section deals with the content on the canvas (self.content)!!
        This is how much space the contents of the scrolling canvas is asking
        for. We don't need the scrolling frame to be any bigger than this."""
        contentrw=self.content.winfo_reqwidth()+self.yscrollbarwidth
        contentrh=self.content.winfo_reqheight()
        for child in self.content.winfo_children():
            log.debug("parent h: {}; child: {}; w:{}; h:{}".format(
                                        self.content.winfo_reqheight(),
                                        child,
                                        child.winfo_reqwidth(),
                                        child.winfo_reqheight()))
            contentrw=max(contentrw,child.winfo_reqwidth())
            contentrh+=child.winfo_reqheight()
            log.log(2,"{} ({})".format(child.winfo_reqwidth(),child))
            for grandchild in child.winfo_children():
                log.debug("child h: {}; grandchild: {}; w:{}; h:{}".format(
                                    child.winfo_reqheight(),
                                    grandchild,
                                    grandchild.winfo_reqwidth(),
                                    grandchild.winfo_reqheight()))
                contentrw=max(contentrw,grandchild.winfo_reqwidth())
                contentrh+=grandchild.winfo_reqheight()
                for greatgrandchild in grandchild.winfo_children():
                    log.debug("grandchild h: {}; greatgrandchild: {}; w:{}; h:{}".format(
                                        grandchild.winfo_reqheight(),
                                        greatgrandchild,
                                        greatgrandchild.winfo_reqwidth(),
                                        greatgrandchild.winfo_reqheight()))
                    contentrw=max(contentrw,greatgrandchild.winfo_reqwidth())
                    contentrh+=greatgrandchild.winfo_reqheight()
        log.log(2,contentrw)
        log.log(2,self.parent.winfo_children())
        log.log(2,'self.winfo_width(): {}; contentrw: {}; self.maxwidth: {}'
                    ''.format(self.winfo_width(),contentrw,self.maxwidth))
        """This section deals with the outer scrolling frame (self)!!
        If the current scrolling frame dimensions are smaller than the
        scrolling content, or else pushing the window off the screen, then make
        the scrolling window the smaller of
            -the scrolling content or
            -the max dimensions, from above."""
        #This should maybe be pulled out to another method?
        #scrolling window width
        if contentrw > self.maxwidth: #self.winfo_width() <
            width=self.maxwidth
        else:
            width=contentrw #self.config(width=contentrw)
        # if self.winfo_width() > self.maxwidth:
        #     self.config(width=self.maxwidth)
        #scrolling window height
        if contentrh > self.maxheight:
            height=self.maxheight #self.config(height=self.maxheight)
        else: #if self.winfo_height() < contentrh:
            height=contentrh# self.config(height=contentrh)
        self.config(height=height, width=width)
        # if self.winfo_height() > self.maxheight:
        #     self.config(height=self.maxheight)
    def _configure_canvas(self, event):
        #this configures self.canvas
        if self.content.winfo_reqwidth() != self.canvas.winfo_width():
            # update the inner frame's width to fill the canvas
            self.canvas.itemconfigure(self.content_id,
                                        width=self.canvas.winfo_width())
        # if self.winfo_height() > self.maxheight:
        #     self.config(height=self.maxheight)
    def __init__(self,parent,xscroll=False):
        """Make this a Frame, with all the inheritances, I need"""
        self.parent=parent
        inherit(self)
        Frame.__init__(self,parent)
        """Not sure if I want these... rather not hardcode."""
        log.debug(self.parent.winfo_children())
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        """With or without the following, it still scrolls through..."""
        self.grid_propagate(0) #make it not shrink to nothing

        """We might want horizonal bars some day? (also below)"""
        if xscroll == True:
            xscrollbar = tkinter.Scrollbar(self, orient=tkinter.HORIZONTAL)
            xscrollbar.grid(row=1, column=0, sticky=tkinter.E+tkinter.W)
        yscrollbar = tkinter.Scrollbar(self)
        yscrollbar.grid(row=0, column=1, sticky=tkinter.N+tkinter.S)
        """Should decide some day which we want when..."""
        self.yscrollbarwidth=50 #make the scrollbars big!
        self.yscrollbarwidth=0 #make the scrollbars invisible (use wheel)
        self.yscrollbarwidth=15 #make the scrollbars useable, but not obnoxious
        yscrollbar.config(width=self.yscrollbarwidth)
        yscrollbar.config(background=self.theme['background'])
        yscrollbar.config(activebackground=self.theme['activebackground'])
        yscrollbar.config(troughcolor=self.theme['background'])
        self.canvas = tkinter.Canvas(self)
        self.canvas.parent = self.canvas.master
        """make the canvas inherit these values like a frame"""
        self.canvas['background']=parent['background']
        inherit(self.canvas)
        """create a frame inside the canvas which will be scrolled with it
        Everthing that should scroll should be a child of this frame"""
        self.content = Frame(self.canvas)
        """This is needed for _configure_canvas"""
        self.content_id = self.canvas.create_window(0, 0, window=self.content,
                                           anchor=tkinter.NW)
        self.canvas.config(bd=0) #no border
        self.canvas.config(yscrollcommand=yscrollbar.set)
        if xscroll == True:
            self.canvas.config(xscrollcommand=xscrollbar.set)
        self.canvas.config(scrollregion=self.canvas.bbox("all"))
        """Make all this show up, and take up all the space in parent"""
        self.grid(row=0, column=0,sticky='nw')
        self.canvas.grid(row=0, column=0,sticky='nsew')
        # self.content.grid(row=0, column=0,sticky='nw')
        """We might want horizonal bars some day? (also above)"""
        if xscroll == True:
            xscrollbar.config(width=self.yscrollbarwidth)
            xscrollbar.config(background=self.theme['background'])
            xscrollbar.config(activebackground=self.theme['activebackground'])
            xscrollbar.config(troughcolor=self.theme['background'])
            xscrollbar.config(command=self.canvas.xview)
        yscrollbar.config(command=self.canvas.yview)
        """I'm not sure if I need this; rather not hardcode these ..."""
        # print('canvas.winfo_reqwidth:',self.canvas.winfo_reqwidth())
        # print('canvas.winfo_reqheight:',self.canvas.winfo_reqheight())
        """Bindings so the mouse wheel works correctly, etc."""
        self.canvas.bind('<Enter>', self._bound_to_mousewheel)
        self.canvas.bind('<Leave>', self._unbound_to_mousewheel)
        self.canvas.bind('<Destroy>', self._unbound_to_mousewheel)
        self.canvas.bind('<Configure>', self._configure_canvas)
        self.content.bind('<Configure>', self._configure_interior)
        self.bind('<Visibility>', self.windowsize)
class Menu(tkinter.Menu):
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
    def wait(self):
        if hasattr(self,'ww') and self.ww.winfo_exists() == True:
            log.debug("There is already a wait window: {}".format(self.ww))
            return
        self.ww=Wait(self.parent)
    def waitdone(self):
        self.ww.close()
    def fullscreen(self):
        w, h = self.parent.winfo_screenwidth(), self.parent.winfo_screenheight()
        self.parent.geometry("%dx%d+0+0" % (w, h))
    def quarterscreen(self):
        w, h = self.parent.winfo_screenwidth(), self.parent.winfo_screenheight()
        w=w/2
        h=h/2
        self.parent.geometry("%dx%d+0+0" % (w, h))
    def setmenus(self,check):
        menubar = Menu(self.parent)
        changemenu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label=_("Change"), menu=changemenu)
        """Language stuff"""
        languagemenu = Menu(changemenu, tearoff=0)
        changemenu.add_cascade(label=_("Languages"), menu=languagemenu)
        languagemenu.add_command(label=_("Interface/computer language"),
                        command=lambda x=check:Check.getinterfacelang(x))
        languagemenu.add_command(label=_("Analysis language"),
                        command=lambda x=check:Check.getanalang(x))
        languagemenu.add_command(label=_("Gloss language"),
                        command=lambda x=check:Check.getglosslang(x))
        languagemenu.add_command(label=_("Another gloss language"),
                        command=lambda x=check:Check.getglosslang2(x))
        """Word/data choice stuff"""
        changemenu.add_command(label=_("Part of speech"),
                        command=lambda x=check:Check.getps(x))
        changemenu.add_command(label=_("Consonant-Vowel-Tone"),
                        command=lambda x=check:Check.gettype(x))
        profilemenu = Menu(changemenu, tearoff=0)
        changemenu.add_cascade(label=_("Syllable profile"), menu=profilemenu)
        profilemenu.add_command(label=_("Next"),
                        command=lambda x=check:Check.nextprofile(x))
        profilemenu.add_command(label=_("Choose"),
                        command=lambda x=check:Check.getprofile(x))
        """What to check stuff"""
        if (check.ps != None and check.profile != None and
                                            check.type != None):
            if check.type == 'T':
                changemenu.add_separator()
                framemenu = Menu(changemenu, tearoff=0)
                changemenu.add_cascade(label=_("Tone Frame"), menu=framemenu)
                framemenu.add_command(label=_("Next"),
                                command=lambda x=check:Check.nextframe(x))
                framemenu.add_command(label=_("Choose"),
                                command=lambda x=check:Check.getcheck(x))
            else:
                changemenu.add_separator()
                changemenu.add_command(label=_("Location in word"),
                        command=lambda x=check:Check.getcheck(x))
                if check.name is not None:
                    changemenu.add_command(label=_("Segment(s) to check"),
                        command=lambda x=check:Check.getsubcheck(x))
        """Do"""
        domenu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label=_("Do"), menu=domenu)
        reportmenu = Menu(menubar, tearoff=0)
        reportmenu.add_command(label=_("Tone by sense"),
                        command=lambda x=check:Check.tonegroupreport(x))
        reportmenu.add_command(label=_("Tone by location"
                        ),command=lambda x=check:Check.tonegroupreport(x,
                                                            bylocation=True))
        reportmenu.add_command(label=_("Basic Vowel report (to file)"),
                        command=lambda x=check:Check.basicreport(x,typestodo=['V']))
        reportmenu.add_command(label=_("Basic Consonant report (to file)"),
                        command=lambda x=check:Check.basicreport(x,typestodo=['C']))
        reportmenu.add_command(label=_("Basic report on Consonants and Vowels "
                                                                "(to file)"),
                command=lambda x=check:Check.basicreport(x,typestodo=['C','V']))
        domenu.add_cascade(label=_("Reports"), menu=reportmenu)
        recordmenu = Menu(menubar, tearoff=0)
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
        advancedmenu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label=_("Advanced"), menu=advancedmenu)
        filemenu = Menu(menubar, tearoff=0)
        filemenu.add_command(label=_("Dictionary Morpheme"),
                        command=lambda x=check:Check.addmorpheme(x))
        advancedmenu.add_command(label=_("Add Tone frame"),
                        command=lambda x=check:Check.addframe(x))
        advtonemenu = Menu(menubar, tearoff=0)
        advancedmenu.add_cascade(label=_("Tone Reports"), menu=advtonemenu)
        advtonemenu.add_command(label=_("Join/Rename Tone Groups"),
                        command=lambda x=check:Check.tonegroupsjoinrename(x))
        advtonemenu.add_command(label=_("Custom groups by sense"),
                                command=lambda x=check:Check.tonegroupreport(x,
                                                                default=False))
        advtonemenu.add_command(label=_("Custom groups by location"),
                                command=lambda x=check:Check.tonegroupreport(x,
                                                bylocation=True, default=False))
        redomenu = Menu(menubar, tearoff=0)
        redomenu.add_command(label=_("Previously skipped data"),
                                command=lambda x=check:Check.tryNAgain(x))
        advancedmenu.add_cascade(label=_("Redo"), menu=redomenu)
        advancedmenu.add_cascade(label=_("Add other"), menu=filemenu)
        redomenu.add_command(
                        label=_("Syllable Profile Analysis (Restart)"),
                        command=lambda x=check:Check.reloadprofiledata(x))
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
        helpmenu = Menu(menubar, tearoff=0)
        helpmenu.add_command(label=_("About"),
                        command=self.helpabout)
        menubar.add_cascade(label=_("Help"), menu=helpmenu)
        self.parent.config(menu=menubar)
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
                " Recordings can be made up to 192khz/32float.\nFor help with "
                "this tool, please check out the documentation at "
                "{url} or write me at "
                "{Email}.".format(name=self.program['name'],
                                    url=self.program['url'],
                                    Email=self.program['Email']))
        Label(window.frame, text=title,
                        font=self.fonts['title'],anchor='c',padx=50
                        ).grid(row=0,column=0,sticky='we')
        f=ScrollingFrame(window.frame)
        f.grid(row=2,column=0,sticky='we')
        Label(f.content, image=self.photo['small'],text='',
                        bg=self.theme['background']
                        ).grid(row=0,column=0,sticky='we')
        l=Label(f.content, text=text, pady=50, padx=50,
                wraplength=int(self.winfo_screenwidth()/2)
                ).grid(row=1,column=0,sticky='we')
    def maketitle(self):
        title=_("{name} Dictionary and Orthography Checker").format(
                                                    name=self.program['name'])
        if self.master.themename != 'greygreen':
            print(f"Using theme '{self.master.themename}'.")
            title+=_(' ('+self.master.themename+')')
        self.parent.title(title)
    def setimages(self):
        # Program icon(s) (First should be transparent!)
        self.parent.photo={}
        imgurl=file.fullpathname('images/AZT stacks6.png')
        self.parent.photo['transparent'] = tkinter.PhotoImage(file = imgurl)
        imgurl=file.fullpathname('images/AZT stacks6_sm.png')
        self.parent.photo['small'] = tkinter.PhotoImage(file = imgurl)
        imgurl=file.fullpathname('images/T alone clear6.png')
        self.parent.photo['T'] = tkinter.PhotoImage(file = imgurl)
        imgurl=file.fullpathname('images/Z alone clear6.png')
        self.parent.photo['C'] = tkinter.PhotoImage(file = imgurl)
        imgurl=file.fullpathname('images/A alone clear6.png')
        self.parent.photo['V'] = tkinter.PhotoImage(file = imgurl)
        imgurl=file.fullpathname('images/ZA alone clear6.png')
        self.parent.photo['CV'] = tkinter.PhotoImage(file = imgurl)
        imgurl=file.fullpathname('images/AZT stacks6.png')
        self.parent.photo['backgrounded'] = tkinter.PhotoImage(file = imgurl)
        #Set images for tasks
        imgurl=file.fullpathname('images/Verify List.png')
        self.parent.photo['verifyT'] = tkinter.PhotoImage(file = imgurl)
        imgurl=file.fullpathname('images/Sort List.png')
        self.parent.photo['sortT'] = tkinter.PhotoImage(file = imgurl)
        imgurl=file.fullpathname('images/Join List.png')
        self.parent.photo['joinT'] = tkinter.PhotoImage(file = imgurl)
        # Other images
        imgurl=file.fullpathname('images/Microphone alone_sm.png')
        self.parent.photo['record'] = tkinter.PhotoImage(file = imgurl)
        imgurl=file.fullpathname('images/Change Circle_sm.png')
        self.parent.photo['change'] = tkinter.PhotoImage(file = imgurl)
        imgurl=file.fullpathname('images/checked.png')
        self.parent.photo['checkedbox'] = tkinter.PhotoImage(file = imgurl)
        imgurl=file.fullpathname('images/unchecked.png')
        self.parent.photo['uncheckedbox'] = tkinter.PhotoImage(file = imgurl)
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
        setfonts(self.parent)
        self.parent.wraplength=self.parent.winfo_screenwidth()-300 #exit button
        self.parent.program=program
    def __init__(self,parent,program):
        start_time=time.time() #this enables boot time evaluation
        # print(time.time()-start_time) # with this
        self.parent=parent
        self.setmasterconfig(program)
        inherit(self) # do this after setting config.
        #set up languages before splash window:
        self.interfacelangs=file.getinterfacelangs()
        interfacelang=file.getinterfacelang()
        if interfacelang == None:
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
        parent.iconphoto(True, self.photo['backgrounded'])
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
        try:
            self.check.frame.winfo_exists()
        except:
            return
        exit=tkinter.Button(self.frame, text=e, command=parent.destroy,
                            width=15,bg=self.theme['background'],
                            activebackground=self.theme['activebackground'])
        exit.grid(row=2, column=1, sticky='ne')
        """Do this after we instantiate the check, so menus can run check
        methods"""
        self.setmenus(self.check)
        print("Finished loading main window in",time.time() - start_time," "
                                                                    "seconds.")
        """finished loading so destroy splash"""
        splash.destroy()
        """show window again"""
        parent.deiconify()
class Label(tkinter.Label):
    def wrap(self):
        availablexy(self)
        self.config(wraplength=self.maxwidth)
        log.debug('self.maxwidth (Label class): {}'.format(self.maxwidth))
    def __init__(self, parent, text, column=0, row=1, **kwargs):
        """These have non-None defaults"""
        if 'font' not in kwargs:
            kwargs['font']=parent.fonts['default']
        if 'wraplength' not in kwargs:
            kwargs['wraplength']=parent.wraplength
        self.theme=parent.theme
        self.parent=parent
        tkinter.Label.__init__(self, parent, text=nfc(text), **kwargs)
        self['background']=self.theme['background']
class EntryField(tkinter.Entry):
    def __init__(self, parent, **kwargs):
        self.parent=parent
        inherit(self)
        if 'font' not in kwargs:
            kwargs['font']=self.fonts['default']
        super().__init__(parent,**kwargs)
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
    def __init__(self, parent, **kwargs):
        for vars in ['var','opts']:
            if (vars not in kwargs):
                print('You need to set {} for radio button frame!').format(vars)
            else:
                setattr(self,vars,kwargs[vars])
                print(self.__dict__)
                del kwargs[vars] #we don't want this going to the button.
                print(self.__dict__)
        column=0
        sticky='w'
        self.parent=parent
        inherit(self)
        super(RadioButtonFrame,self).__init__(parent,**kwargs)
        kwargs['background']=self.theme['background']
        kwargs['activebackground']=self.theme['activebackground']
        print('self.var:',self.var)
        print('self.opts:',self.opts)
        row=0
        for opt in self.opts:
            value=opt[0]
            name=opt[1]
            log.info("Value: {}; name: {}".format(value,name))
            RadioButton(self,variable=self.var, value=value, text=nfc(name),
                                                column=column,
                                                row=row,
                                                sticky=sticky,
                                                indicatoron=0,
                                                **kwargs)
            row+=1
class Button(tkinter.Button):
    def __init__(self, parent, text=None,
                choice=None, window=None, #some buttons have these, some don't
                command=None, column=0, row=1,
                **kwargs):
        """Remove these arguments; buttons shouldn't be passing them..."""
        """command is my hacky command specification, with lots of args added.
        cmd is just the command passing through."""
        self.parent=parent
        inherit(self)
        self.text=text
        """For Grid"""
        if 'sticky' in kwargs:
            sticky=kwargs['sticky']
            del kwargs['sticky'] #we don't want this going to the button.
        else:
            sticky="W"+"E"
        """For button"""
        if 'anchor' not in kwargs:
            kwargs['anchor']="w"
        if 'wraplength' not in kwargs:
            kwargs['wraplength']=parent.wraplength #we need this defined always or never...
        if 'font' not in kwargs:
            kwargs['font']=parent.fonts['default']
        kwargs['activebackground']=self.theme['activebackground']
        kwargs['background']=self.theme['background']
        if self.debug == True:
            for arg in kwargs:
                print("Button "+arg+": "+kwargs[arg])
        if 'cmd' in kwargs and kwargs['cmd'] is not None:
            cmd=kwargs['cmd']
            del kwargs['cmd'] #we don't want this going to the button as is.
        else:
            """This doesn't seem to be working, but OK to avoid it..."""
            if window != None:
                if choice is not None:
                    cmd=lambda w=window:command(choice,window=w)
                else:
                    cmd=lambda w=window:command(window=w)
            else:
                if choice != None:
                    cmd=lambda :command('choice')
                else:
                    cmd=lambda :command()
        tkinter.Button.__init__(self, parent, text=nfc(text), command=cmd,
                                **kwargs)
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
    def playcallback(self, in_data, frame_count, time_info, status):
        data = self.wf.readframes(frame_count)
        return (data, pyaudio.paContinue)
    def recordcallback(self, in_data, frame_count, time_info, flag):
        if not hasattr(self,'fulldata'):
            self.fulldata= in_data
        else:
            self.fulldata+=in_data
        return (self.fulldata, pyaudio.paContinue)
    def _start(self, event):
        # print("I'm recording now")
        if hasattr(self,'fulldata'):
            delattr(self,'fulldata') #let's start each recording afresh.
        self.pa = pyaudio.PyAudio()
        def callback(self):
            self.stream = self.pa.open(
                    input_device_index=self.audio_card_index,
                    format=self.sample_format,
                    channels=self.channels,
                    rate=self.fs,
                    input=True,
                    stream_callback=self.recordcallback)
            self.stream.start_stream()
            self.fileopen()
            """input=True, p.open() method → stream.read() to read from
            microphone. output=True, stream.write() to the speaker."""
        def block(self):
            self.stream = self.pa.open(format=self.sample_format,
                    channels=self.channels,
                    rate=self.fs,
                    frames_per_buffer=self.chunk,
                    input=True)
            self.frames = []
            for i in range(0, int(self.fs / self.chunk * self.seconds)):
                data = self.stream.read(self.chunk)
                self.frames.append(data)
        if self.callbackrecording==True:
            callback(self)
        else:
            block(self)
    def _stop(self, event):
        # print("I'm stopping recording now")
        if hasattr(self,'stream'):
            self.stream.stop_stream()
        self.fileclose()
        self.b.destroy()
        self.makeplaybutton()
        self.makedeletebutton()
    def _play(self, event):
        # print("I'm playing the recording now")
        self.wf = wave.open(self.filenameURL, 'rb')
        self.pa = pyaudio.PyAudio()
        """"block"""
        # stream = pa.open(format=pa.get_format_from_width(wf.getsampwidth()),
        #         channels=wf.getnchannels(),
        #         rate=wf.getframerate(),
        #         output=True)
        # data = wf.readframes(self.chunk)
        # while len(data) > 0:
        #     stream.write(data)
            # data = wf.readframes(self.chunk)
        """Callback"""
        # print('channels:',self.wf.getnchannels())
        # print('getframerate:',self.wf.getframerate())
        # print('getframerate:',self.wf.getsampwidth())
        # print('format:',self.pa.get_format_from_width(self.wf.getsampwidth()))
        stream = self.pa.open(
                output_device_index=self.audioout_card_index,
                format=self.pa.get_format_from_width(self.wf.getsampwidth()),
                channels=self.wf.getnchannels(),
                rate=self.wf.getframerate(),
                output=True,
                stream_callback=self.playcallback)
        stream.start_stream()
        while stream.is_active():
            time.sleep(0.1)
        stream.stop_stream()
        stream.close()
        self.wf.close()
        self.pa.terminate()
    def _redo(self, event):
        # print("I'm deleting the recording now")
        self.p.destroy()
        self.makerecordbutton()
        self.r.destroy()
    def fileopen(self):
        file.remove(self.filenameURL) #don't do this until recording new file.
        self.wf = wave.open(self.filenameURL, 'wb')
        self.wf.setnchannels(self.channels)
        self.wf.setsampwidth(self.pa.get_sample_size(self.sample_format))
        self.wf.setframerate(self.fs)
    def fileclose(self):
        while self.stream.is_active():
            time.sleep(0.1)
        if hasattr(self,'fulldata'):
            self.wf.writeframes(self.fulldata)
        else:
            log.debug("Nothing recorded!")
        self.wf.close()
        if self.test is not True:
            self.addlink()
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
    def makeplaybutton(self):
        self.p=Button(self,text=_('Play'),command=self.function)
        self.p.grid(row=0, column=1,sticky='w')
        self.p.bind('<ButtonPress>', self._play)
    def makedeletebutton(self):
        self.r=Button(self,text=_('Redo'),command=self.function)
        self.r.grid(row=0, column=2,sticky='w')
        self.r.bind('<ButtonRelease>', self._redo)
    def addlink(self):
        #this checks for and doesn't add it already there.
        self.db.addmediafields(self.node,self.filename,self.audiolang)
    def function(self):
        pass
    def makefilenames(self):
        if self.test==True:
            self.filename=self.filenameURL="test_{}_{}.wav".format(
                                        self.check.fs,self.check.sample_format)
        else:
            if ((self.id==None) or (self.node==None) #or (self.form==None)
                or (self.gloss==None)):
                print("Sorry, unless testing we need all these "
                        "arguments; exiting.")
            if self.form==None:
                self.form=self.node.find(f"form[@lang='{check.analang}']/text").text
            # make psprofile (if no audio file, the last in this list is used):
            psprofiles=[self.check.ps]
            if (self.node.tag == 'example'):
                l=self.node.find("field[@type='location']//text")
                if l is not None:
                    psprofiles+=[self.check.ps+'-'+l.text]
            if not hasattr(self.check, 'rx'):
                #ad hoc dictionary to remove diacritics:
                self.check.rx={'d':rx.make(rx.s(self.check,'d'),compile=True)}
            self.filenames=[]
            for psprofile in psprofiles:
                args=[psprofile, self.id, self.node.tag, rx.stripdiacritics(
                                                    self.check,self.form),
                                                    #check.profile, <=Changes!
                                                    self.gloss]
                wavfilename=''
                for arg in [x for x in args if x != None]:
                    wavfilename+=arg
                    if args.index(arg) < len(args):
                        wavfilename+='_'
                self.filenames+=[re.sub('[][\. /?]+','_',
                                                    str(wavfilename))+'.wav']
            #test if any of the filenames are there
            for self.filename in self.filenames:
                self.filenameURL=str(file.getdiredurl(self.check.audiodir,
                                                                self.filename))
                if file.exists(self.filenameURL):
                    log.debug("Audio file found! using name: {}; names: {}; "
                        "url:{}".format(self.filename, self.filenames,
                                                            self.filenameURL))
                    self.addlink()
                    return
            #if you don't find any, take the last values
            log.debug("No audio file found! using name: {}; names: {}; url:{}"
                    "".format(self.filename, self.filenames, self.filenameURL))
            return
    def __init__(self, parent, check, id=None, node=None, form=None,
                gloss=None, test=False,
                #choice=None, window=None, #some buttons have these, some don't
                #command=None,
                # column=0, row=1,
                **kwargs):
        """Originally from https://realpython.com/playing-and-recording-
        sound-python/"""
        self.db=check.db
        self.node=node #This should never be more than one node...
        self.form=form
        self.id=id
        self.gloss=gloss
        self.check=check
        self.callbackrecording=True
        self.chunk = 1024  # Record in chunks of 1024 samples
        # self.sample_format = pyaudio.paInt16  # 16 bits per sample
        self.channels = 1 #Always record in mono
        self.audiolang=check.audiolang
        # self.fs = 44100  # Record at 44100 samples per second
        # self.seconds = 3
        # self.toneframesfile=re.sub('\.','_',str(filename+".ToneFrames"))+'.py'
        """I'm trusting here that no one has been screwing with the check
        parameters"""
        self.test=test
        self.makefilenames()
        Frame.__init__(self,parent, **kwargs)
        """These need to happen after the frame is created, as they
        might cause the init to stop."""
        if ((check.fs == None) or (check.sample_format == None)
                or (check.audio_card_index == None)
                or (check.audioout_card_index == None)):
            text=_("Sorry, you need to set the fs, sample_rate, and sound card!"
                    "\n(Change Stuff|Recording|Sound Card Settings)"
                    "\nSet these, and try again, and "
                    "\na record button will be here.")
            print(text)
            Label(self,text=text).grid(row=0,column=0)
            return
        else:
            self.fs=check.fs
            self.sample_format=check.sample_format
            self.audio_card_index=check.audio_card_index
            self.audioout_card_index=check.audioout_card_index
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
        try:
            self.parent.deiconify()
        except:
            log.debug("Not deiconifying parent.")
        self.destroy()
    def __init__(self, parent=None):
        global program
        self.parent=parent
        inherit(self)
        try:
            self.parent.withdraw()
            # if platform.uname().system == 'Linux':
            #     self.parent.withdraw()
            # else:
            #     self.parent.iconify() #A window doesn't return on deiconify...
        except:
            log.debug("Not withdrawing parent.")
        super(Wait, self).__init__(parent)
        self['background']=parent['background']
        self.photo = parent.photo #need this before making the frame
        title=(_("Please Wait! {name} Dictionary and Orthography Checker "
                        "in Process").format(name=self.program['name']))
        self.title(title)
        text=_("Please Wait...")
        self.l=Label(self.outsideframe, text=text,
                font=self.fonts['title'],anchor='c')
        self.l.grid(row=0,column=0,sticky='we')
        Label(self.outsideframe, image=self.photo['small'],text='',
                        bg=self['background']
                        ).grid(row=1,column=0,sticky='we',padx=50,pady=50)
        self.update_idletasks()
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
        Label(self, text=title, pady=30,
                        font=self.fonts['title'],anchor='c',padx=25
                        ).grid(row=0,column=0,sticky='we')
        Label(self, text=v, pady=30,
                        anchor='c',padx=25
                        ).grid(row=1,column=0,sticky='we')
        Label(self, image=self.photo['transparent'],text='',
                        bg=self.theme['background']
                        ).grid(row=2,column=0,sticky='we')
        l=Label(self, text=text, pady=30, padx=50,
                wraplength=int(self.winfo_screenwidth()/3)
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
        i18n[lang].install()
    else:
        log.debug("Apparently we're trying to set the same interface "
                                        "language: {}={}".format(lang,curlang))
    log.debug(_("Translation seems to be working, using {}"
                                                "".format(getinterfacelang())))
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
def name(x):
    try:
        name=x.__name__ #If x is a function
        return name
    except:
        name=x.__class__.__name__ #If x is a class instance
        return "class."+name
def firstoflist(l,othersOK=False,all=False):
    """This takes a list composed of one item, and returns the item.
    with othersOK=True, it discards n=2+ items; with othersOK=False,
    it throws an error if there is more than one item in the list."""
    if type(l) is not list:
        return l
    if (l == None) or (l == []):
        return
    if all == True:
        return ', '.join(x for x in l if x is not None)
    elif len(l) == 1 or (othersOK == True):
        return l[0]
    elif othersOK == False: #(i.e., with `len(list) != 1`)
        print('Sorry, something other than one list item found: {}'
                '\nDid you mean to use "othersOK=True"? Returning nothing!'
                ''.format(l))
def t(element):
    try:
        return element.text
    except:
        if element is None:
            return
        elif element is str:
            log.debug("Apparently you tried to pull text out of a non element; "
            "turns out it's a simple string, so returning it: {}"
            "".format(element))
            return element
        else:
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
def nn(x,oneperline=False):
    """Don't print "None" in the UI..."""
    if type(x) is list or type(x) is tuple:
        output=[]
        for y in x:
            output+=[nonspace(y)]
        if oneperline == True:
            return '\n'.join(output)
        else:
            return ' '.join(output)
    else:
        return nonspace(x)
def setthemes(self):
    self.themes={'lightgreen':{
                        'background':'#c6ffb3',
                        'activebackground':'#c6ffb3',
                        'offwhite':None}, #lighter green
                'green':{
                        'background':'#b3ff99',
                        'activebackground':'#c6ffb3',
                        'offwhite':None},
                'pink':{
                        'background':'#ff99cc',
                        'activebackground':'#ff66b3',
                        'offwhite':None},
                'lighterpink':{
                        'background':'#ffb3d9',
                        'activebackground':'#ff99cc',
                        'offwhite':None},
                'evenlighterpink':{
                        'background':'#ffcce6',
                        'activebackground':'#ffb3d9',
                        'offwhite':'#ffe6f3'},
                'purple':{
                        'background':'#ffb3ec',
                        'activebackground':'#ff99e6',
                        'offwhite':'#ffe6f9'},
                'Howard':{
                        'background':'green',
                        'activebackground':'red',
                        'offwhite':'grey'},
                'Kent':{
                        'background':'red',
                        'activebackground':'green',
                        'offwhite':'grey'},
                'Kim':{
                        'background':'#ffbb99',
                        'activebackground':'#ffaa80',
                        'offwhite':'#ffeee6'},
                'yellow':{
                        'background':'#ffff99',
                        'activebackground':'#ffff80',
                        'offwhite':'#ffffe6'},
                'greygreen1':{
                        'background':'#62d16f',
                        'activebackground':'#4dcb5c',
                        'offwhite':'#ebf9ed'},
                'lightgreygreen':{
                        'background':'#9fdfca',
                        'activebackground':'#8cd9bf',
                        'offwhite':'#ecf9f4'},
                'greygreen':{
                        'background':'#8cd9bf',
                        'activebackground':'#66ccaa', #10% darker than the above
                        'offwhite':'#ecf9f4'},
                'highcontrast':{
                        'background':'white',
                        'activebackground':'#e6fff9', #10% darker than the above
                        'offwhite':'#ecf9f4'},
                'tkinterdefault':{
                        'background':None,
                        'activebackground':None,
                        'offwhite':None}
                }
def setfonts(self,fonttheme='default'):
    if fonttheme == 'small':
        default=12
        normal=14
        big=16
        bigger=24
        title=24
        small=10
    else:
        default=18
        normal=24
        big=30
        bigger=36
        title=36
        small=12
    self.fonts={
            'title':tkinter.font.Font(family="Charis SIL", size=title), #Charis
            'instructions':tkinter.font.Font(family="Andika SIL",
                                        size=normal), #Charis
            'report':tkinter.font.Font(family="Andika SIL", size=small),
            'reportheader':tkinter.font.Font(family="Andika SIL", size=small,
                                                # underline = True,
                                                slant = 'italic'
                                                ),
            'read':tkinter.font.Font(family="Andika SIL", size=big),
            'readbig':tkinter.font.Font(family="Andika SIL", size=bigger,
                                        weight='bold'),
            'small':tkinter.font.Font(family="Andika SIL", size=small),
            'default':tkinter.font.Font(family="Andika SIL", size=default)
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
def availablexy(self,w=None):
    if w is None: #initialize a first run
        w=self
        self.otherrowheight=0
        self.othercolwidth=0
    wrow=w.grid_info()['row']
    wcol=w.grid_info()['column']
    wrowmax=wrow+w.grid_info()['rowspan']
    wcolmax=wcol+w.grid_info()['columnspan']
    wrows=set(range(wrow,wrowmax))
    wcols=set(range(wcol,wcolmax))
    log.log(2,'wrow: {}; wrowmax: {}; wrows: {}; wcol: {}; wcolmax: {}; '
            'wcols: {} ({})'.format(wrow,wrowmax,wrows,wcol,wcolmax,wcols,w))
    rowheight={}
    colwidth={}
    for sib in w.parent.winfo_children():
        if sib.winfo_class() != 'Menu':
            sib.row=sib.grid_info()['row']
            sib.col=sib.grid_info()['column']
            """These are actual the row/col after the max in span,
            but this is what we want for range()"""
            sib.rowmax=sib.row+sib.grid_info()['rowspan']
            sib.colmax=sib.col+sib.grid_info()['columnspan']
            sib.rows=set(range(sib.row,sib.rowmax))
            sib.cols=set(range(sib.col,sib.colmax))
            # print('sib:',sib.row,sib.rowmax,sib.rows,sib.col,sib.colmax,sib.cols)
            # print('wrows & sib.rows:',wrows & sib.rows)
            # print('wcols & sib.cols:',wcols & sib.cols)
            if wrows & sib.rows == set(): #the empty set
                sib.reqheight=sib.winfo_reqheight()
                log.debug("sib {} reqheight: {}".format(sib,sib.reqheight))
                """Give me the tallest cell in this row"""
                if ((sib.row not in rowheight) or (sib.reqheight >
                                                        rowheight[sib.row])):
                    rowheight[sib.row]=sib.reqheight
            # else:
            #     print(wrows,'and',sib.rows,'share rows')
            if wcols & sib.cols == set(): #the empty set
                sib.reqwidth=sib.winfo_reqwidth()
                log.debug("sib {} width: {}".format(sib,sib.reqwidth))
                """Give me the widest cell in this column"""
                if ((sib.col not in colwidth) or (sib.reqwidth >
                                                        colwidth[sib.col])):
                    colwidth[sib.col]=sib.reqwidth
            # else:
            #     print(wcols,'and',sib.cols,'share columns')
    for row in rowheight:
        self.otherrowheight+=rowheight[row]
    for col in colwidth:
        self.othercolwidth+=colwidth[col]
    log.debug("self.othercolwidth: {}; self.otherrowheight: {}".format(
                self.othercolwidth,self.otherrowheight))
    if w.parent.winfo_class() != 'Toplevel':
        availablexy(self,w.parent)
    else:
        """This may not be the right way to do this, but this set of adjustments
        puts the window edge widgets on the edge of the screen. This calculation
        is done on the toplevel widget, after the above recursive function is
        done across all the other widgets (so we just get window decoration)."""
        titlebarHeight = 50 #not working: self.winfo_rooty() - self.winfo_y()
        borderSize= 0 #not working: self.winfo_rootx() - self.winfo_x()
        self.othercolwidth+=borderSize*2
        self.otherrowheight+=titlebarHeight+100
        self.maxheight=self.parent.winfo_screenheight()-self.otherrowheight
        self.maxwidth=self.parent.winfo_screenwidth()-self.othercolwidth
        log.log(2,"self.winfo_rootx(): {}".format(self.winfo_rootx()))
        log.log(2,"self.winfo_x(): {}".format(self.winfo_x()))
        log.log(2,"titlebarHeight: {}".format(titlebarHeight))
        log.log(2,"borderSize: {}".format(borderSize))
    log.log(2,"height: {}; width: {}; self.maxheight: {}; self.maxwidth: {}"
                "".format(
                                self.parent.winfo_screenheight(),
                                self.parent.winfo_screenwidth(),
                                self.maxheight,
                                self.maxwidth))
    log.log(2,"cols: {}".format(colwidth))
    log.log(2,"rows: {}".format(rowheight))
def returndictnsortnext(self,parent,values,canary=None,canary2=None):
    """Kills self.sorting, not parent."""
    for value in values:
        setattr(self,value,values[value])
        if canary == None:
            self.sorting.destroy() #from or window with button...
        elif canary.winfo_exists():
            canary.destroy() #Just delete the one
        elif canary2.winfo_exists():
            canary2.destroy() #or the other
        return value
def returndictdestroynsortnext(self,parent,values):
    """Kills self.sorting *and* parent."""
    # print(self,parent,values)
    for value in values:
        setattr(self,value,values[value])
        self.sorting.destroy() #from or window with button...
        parent.destroy() #from or window with button...
        return value
def returndictndestroy(self,parent,values): #Spoiler: the parent dies!
    """Self is where to store the dictionar(ies) in Values, parent is the
    window/frame to kill."""
    # print(self,parent,values)
    for value in values:
        setattr(self,value,values[value])
        parent.destroy() #from or window with button...
        return value
def removesenseidfromsubcheck(self,parent,senseid):
    self.db.rmexfields(senseid=senseid,fieldtype='tone',
                        location=self.name,fieldvalue=self.subcheck,
                        showurl=True
                        )
    self.markunsortedsenseid(senseid)
    parent.destroy() #.runwindow.resetframe()
def inherit(self,attr=None):
    """This function brings these attributes from the parent, to inherit
    from the root window, through all windows, frames, and scrolling frames, etc
    """
    if attr == None:
        attrs=['fonts','theme','debug','wraplength','photo','program']
    else:
        attrs=[attr]
    for attr in attrs:
        setattr(self,attr,getattr(self.parent,attr))
def nfc(x):
    #This makes (pre)composed characters, e.g., vowel and accent in one
    return unicodedata.normalize('NFC', str(x))
def nfd(x):
    #This makes decomposed characters. e.g., vowel + accent
    return unicodedata.normalize('NFD', str(x))
def main():
    global program
    log.info("Running main function") #Don't translate yet!
    root = tkinter.Tk()
    myapp = MainApplication(root,program)
    myapp.mainloop()
    logshutdown()
if __name__ == "__main__":
    """These things need to be done outside of a function, as we need global
    variables."""
    if hasattr(sys,'_MEIPASS') and sys._MEIPASS != None:
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
    # i18n['fub'] = gettext.azttranslation('azt', transdir, languages=['fub'])
    try:
        main()
    except Exception as e:
        log.exception("Unexpected exception! %s",e)
        logwritelzma(log.filename) #in logsetup
    exit()
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
