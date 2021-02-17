#!/usr/bin/env python3
# coding=UTF-8
"""This file runs the actual GUI for lexical file manipulation/checking"""
program={'name':'A→Z+T'}
program['tkinter']=True
program['production']=False #True for making screenshots
program['version']='0.6.2' #This is a string...
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
class Check():
    """the parent is the *functional* head, the MainApplication."""
    """the frame is the *GUI* head, the frame sitting in the MainApplication."""
    def __init__(self, parent, frame, nsyls=None):
        self.start_time=time.time() #this enables boot time evaluation
        self.iterations=0
        # print(time.time()-self.start_time) # with this
        self.debug=parent.debug
        self.su=True #show me stuff others don't want/need
        self.su=False #not a superuser; make it easy on me!
        self.parent=parent #should be mainapplication frame
        self.frame=frame
        inherit(self)
        log.info("check.interfacelang: {}".format(self.interfacelang))
        # _=self._
        # self.fonts=parent.fonts
        # self.theme=parent.theme #Needed?
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
        for savefile in [self.defaultfile,self.toneframesfile,self.statusfile,
                        self.profiledatafile]:
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
        self.loadstatus()
        self.loadtoneframes()
        if nsyls is not None:
            self.nsyls=nsyls
        else:
            self.nsyls=2
        self.invalidchars=[' ','...','-',')','(<field type="tone"><form lang="gnd"><text>'] #multiple characters not working.
        self.invalidregex='( |\.|-|,|\)|\()+'
        """Are we OK without these?"""
        # self.guidtriage() #sets: self.guidswanyps self.guidswops self.guidsinvalid self.guidsvalid
        # self.guidtriagebyps() #sets self.guidsvalidbyps (dictionary keyed on ps)
        self.senseidtriage() #sets: self.senseidswanyps self.senseidswops self.senseidsinvalid self.senseidsvalid
        self.db.languagecodes=self.db.analangs+self.db.glosslangs
        self.db.languagepaths=file.getlangnamepaths(filename,
                                                        self.db.languagecodes)
        # profiles.get(self.db, nsyls=nsyls) #sets: db.profileswdata db.profiles
        setdefaults.fields(self.db) #sets self.pluralname and self.imperativename
        self.initdefaults() #provides self.defaults, list to load/save
        self.cleardefaults() #this resets all to none (to be set below)
        # self.analang=self.db.analang #inherit from the lang if not specified
        # self.glosslang=self.db.glosslang #inherit from the lang if not specified
        # self.glosslang2=self.db.glosslang2 #inherit from the lang if not specified
        # self.audiolang=self.db.audiolang
        # self.guessinterfacelang()
        log.info(_('Interface Language: {}'.format(self.parent.parent.interfacelang)))
        """These two lines can import structured frame dictionaries; do this
        just to make the import, then comment them out again."""
        # import toneframesbylang
        # self.toneframes=toneframesbylang.toneframes[self.analang]
        self.frameregex=re.compile('__') #replace this w/data in frames.
        # self.basicreport() #doing this by menu now
        self.loadprofiledata()
        # print('self.profilesbysense:',self.profilesbysense)
        """I think I need this before setting up regexs"""
        self.guessanalang() #needed for regexs
        log.debug("analang guessed: {} (If you don't like this, change it in "
                    "the menus)".format(self.analang))
        self.loaddefaults() # overwrites guess above, stored on runcheck
        self.langnames()
        self.checkinterpretations() #checks (and sets) values for self.distinguish
        if 'bfj' in self.db.s:
            bfjvdigraphs=(['ou','ei','ɨʉ','ai']+
            ['óu','éi','ɨ́ʉ','ái']+
            ['òu','èi','ɨ̀ʉ','ài'])
            self.db.s['bfj']['V']=bfjvdigraphs+self.db.s['bfj']['V']
            log.debug(self.db.s['bfj']['V'])
        self.slists() #lift>check segment dicts: s[lang][segmenttype]
        """The line above may need to go after this block"""
        if self.profilesbysense is None:
            log.info("Starting profile analysis at {}".format(time.time()
                                                            -self.start_time))
            self.setupCVrxs() #creates self.rx dictionaries
            self.getprofiles() #creates self.profilesbysense nested dicts
            self.makecountssorted() #creates self.profilecounts
            for var in ['rx','profilesbysense','profilecounts']:
                log.debug("{}: {}".format(var,getattr(self,var)))
        # self.guesspsprofile() # takes values of largest ps-profile filter
        self.storeprofiledata()
        self.setnamesall() #sets self.checknamesall
        # self.V=self.db.v #based on what is actually in the language (no groups)
        # self.C=self.db.c #this regex is basically each valid glyph in analang,
        log.info("Done initializing check; running first check check.")
        # self.profileofform()
        # exs=
        # print(len(exs))
        """Testing Zone"""
        # self.setupCVrxs()
        # self.profileofform('zukw')
        # exit()
        self.checkcheck()
    """Guessing functions"""
    def guessinterfacelang(self):
        """I'm asked to do this when the root window has the attribute set,
        but the check doesn't. So I'm testing for the check attribute here."""
        log.debug('guessinterfacelang: {}'.format(self.parent.parent.interfacelang))
        if self.interfacelang == None:
            if ((self.glosslang == None) or
                    (self.glosslang not in self.db.glosslangs)):
                self.guessglosslangs()
            self.parent.parent.interfacelang=self.glosslang
        setinterfacelang(self.glosslang)
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
    def guessps(self):
        """Make this smarter, but for now, just take value from the most
        populous tuple"""
        self.ps=self.profilecounts[0][2]
    def guessprofile(self):
        """Make this smarter, but for now, just take value from the most
        populous tuple"""
        self.profile=self.profilecounts[0][1]
    def guesscheckname(self):
        """Picks the longest name (the most restrictive fiter)"""
        # print(self.checkspossible)
        # print(sorted(self.checkspossible,
        #                         key=lambda s: len(s[0]),reverse=True))
        # print(firstoflist(sorted(self.checkspossible,
        #                         key=lambda s: len(s[0]),reverse=True),
        #                         othersOK=True))
        self.name=firstoflist(sorted(self.checkspossible,
        key=lambda s: len(s[0]),reverse=True),
        othersOK=True)[0]
    def guesstype(self):
                    """For now, if type isn't set, start with Vowels."""
                    self.type='V'
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
            # self.parent.parent.interfacelangs is set in file.py
            buttonFrame1=ButtonFrame(window.frame,
                                    self.parent.parent.interfacelangs,
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
                self.storedefaults()
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
        self.runwindow.ww.close()
    def addmorpheme(self):
        def submitform():
            self.runwindow.form=formfield.get()
            # chk()
            # self.storetoneframes()
            # self.storedefaults()
            self.runwindow.frame2.destroy()
        def submitgloss():
            self.runwindow.gloss=glossfield.get()
            self.runwindow.frame2.destroy()
        def submitgloss2():
            self.runwindow.gloss2=gloss2field.get()
            self.runwindow.frame2.destroy()
        def submitgloss2no():
            self.runwindow.gloss2=None #gloss2field.get()
            self.runwindow.frame2.destroy()
        self.getrunwindow()
        form=tkinter.StringVar()
        gloss=tkinter.StringVar()
        gloss2=tkinter.StringVar()
        padx=50
        pady=10
        self.runwindow.title(_("Add Morpheme to Dictionary"))
        title=_("Add a {} morpheme to the dictionary").format(
                            self.languagenames[self.analang])
        Label(self.runwindow,text=title,font=self.fonts['title'],
                justify=tkinter.LEFT,anchor='c'
                ).grid(row=0,column=0,sticky='ew',padx=padx,pady=pady)
        self.runwindow.frame2=Frame(self.runwindow)
        self.runwindow.frame2.grid(row=1,column=0,sticky='ew',padx=25,pady=25)
        getformtext=_("What is the form of the new {} "
                    "morpheme (consonants and vowels only)?".format(
                                self.languagenames[self.analang]))
        getform=Label(self.runwindow.frame2,text=getformtext,
                font=self.fonts['read'])
        getform.grid(row=0,column=0,padx=padx,pady=pady)
        formfield = EntryField(self.runwindow.frame2,textvariable=form)
        formfield.grid(row=1,column=0)
        sub_btn=Button(self.runwindow.frame2,text = 'Use this form',
                  command = submitform,anchor ='c')
        sub_btn.grid(row=2,column=0,sticky='')
        sub_btn.wait_window(self.runwindow.frame2) #then move to next step
        """repeat above for gloss"""
        self.runwindow.frame2=Frame(self.runwindow)
        self.runwindow.frame2.grid(row=1,column=0,sticky='ew',padx=25,pady=25)
        getglosstext=_("What does {} mean in {}?".format(self.runwindow.form,
                                        self.languagenames[self.glosslang]))
        getgloss=Label(self.runwindow.frame2,text=getglosstext,
                font=self.fonts['read'],
                justify=tkinter.LEFT,anchor='w')
        getgloss.grid(row=0,column=0,padx=padx,pady=pady)
        glossfield = EntryField(self.runwindow.frame2,textvariable=gloss)
        glossfield.grid(row=1,column=0)
        sub_btn=Button(self.runwindow.frame2,text = 'Use this gloss',
                  command = submitgloss)
        sub_btn.grid(row=2,column=0,sticky='')
        sub_btn.wait_window(self.runwindow.frame2) #then move to next step
        """repeat above for gloss2?"""
        if self.glosslang2 is not None:
            self.runwindow.frame2=Frame(self.runwindow,pady=25)
            self.runwindow.frame2.grid(row=1,column=0,sticky='ew',padx=25,pady=25)
            getgloss2text=_("What does {} mean in {}?".format(
                            self.runwindow.form,
                            self.languagenames[self.glosslang2]))
            getgloss2=Label(self.runwindow.frame2,text=getgloss2text,
                    font=self.fonts['read'],
                    justify=tkinter.LEFT,anchor='w')
            getgloss2.grid(row=0,column=0,sticky='w',padx=padx,pady=pady)
            gloss2field = EntryField(self.runwindow.frame2,textvariable=gloss2)
            gloss2field.grid(row=1,column=0)
            sub_btn=Button(self.runwindow.frame2,text = 'Use this gloss',
                      command = submitgloss2)
            sub_btn.grid(row=2,column=0,sticky='')
            sub_btnNo=Button(self.runwindow.frame2,
                        text = _('Skip {} gloss').format(
                            self.languagenames[self.glosslang2]),
                      command = submitgloss2no)
            sub_btnNo.grid(row=1,column=1,sticky='')
            sub_btn.wait_window(self.runwindow.frame2) #then move to next step
        # if hasattr(self.runwindow,'gloss2'):
        # else:
        # print(self.runwindow.form, self.runwindow.gloss, self.runwindow.gloss2)
            # print(self.runwindow.form, self.runwindow.gloss)
        # 2012-03-28T21:15:23Z Times are managed in lift.py
        """get the senseid back from this function, which generates it"""
        senseid=self.db.addentry(ps=self.ps,analang=self.analang,
                        glosslang=self.glosslang,langform=self.runwindow.form,
                        glossform=self.runwindow.gloss,
                        glosslang2=self.glosslang2,
                        glossform2=self.runwindow.gloss2)
        self.addtoprofilesbysense(senseid)
        self.storeprofiledata() #since we changed this.
        """Store these variables above, finish with (destroying window with
        local variables):"""
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
            """self.name is set here --I may need it, to correctly test
            the frames created..."""
            self.name=str(namevar)
            if self.name is '':
                text=_('Sorry, empty name! \nPlease provide at least \na frame '
                    'name, to distinguish it \nfrom other frames.')
                print(re.sub('\n','',text))
                if hasattr(window,'frame2'):
                    window.frame2.destroy()
                window.frame2=Frame(window.scroll.content)
                window.frame2.grid(row=1,column=0,columnspan=3,sticky='w')
                l1=Label(window.frame2,
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
            framed=self.getframeddata(senseid) #after defn above, before below!
            print(frame,framed)
            """Display framed data"""
            if hasattr(window,'frame2'):
                window.frame2.destroy()
            window.frame2=Frame(window.scroll.content)
            window.frame2.grid(row=1,column=0,columnspan=3,sticky='w')
            tf={}
            tfd={}
            padx=50
            pady=10
            row=0
            for lang in langs:
                print('frame[{}]:'.format(lang),frame[lang])
                tf[lang]=('form: '+frame[lang])
                tfd[lang]=('(ex: '+framed[lang]+')')
                l1=Label(window.frame2,
                        text=tf[lang],
                        font=self.fonts['read'],
                        justify=tkinter.LEFT,anchor='w')
                l1.grid(row=row,column=columnleft,sticky='w',padx=padx,
                                                                pady=pady)
                l2=Label(window.frame2,
                        text=tfd[lang],
                        font=self.fonts['read'],
                        justify=tkinter.LEFT,anchor='w')
                l2.grid(row=row,column=columnleft+1,sticky='w',padx=padx,
                                                                pady=pady)
                row+=1
            """toneframes={'Nom':
                            {'name/location (e.g.,"By itself")':
                                {'form>xyz': '__',
                                'gloss>xyz': 'a __'},
                                'gloss2>xyz': 'un __'},
                        }   }
            """
            row+=1
            sub_btn=Button(window.frame2,text = 'Use this tone frame',
                      command = submit)
            sub_btn.grid(row=row,column=columnright,sticky='w')
        def submit():
            chk()
            self.storetoneframes()
            # self.storedefaults()
            window.destroy()
        window=Window(self.frame, title=_("Define a new tone frame"))
        window.scroll=ScrollingFrame(window)
        window.frame1=Frame(window.scroll.content)
        window.frame1.grid(row=0,column=0)
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
        t=(_("Add {} tone frame").format(self.ps))
        Label(window.frame1,text=t+'\n',font=self.fonts['title']
                ).grid(row=row,column=columnleft,columnspan=3)
        row+=1
        t=_("What do you want to call the tone frame ?")
        finst=Frame(window.frame1)
        finst.grid(row=row,column=0)
        Label(finst,text=t).grid(row=0,column=columnleft,sticky='e')
        name = EntryField(finst,textvariable=namevar)
        name.grid(row=0,column=columnright,sticky='w')
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
            f[lang]=Frame(window.frame1)
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
            row+=1
        row+=1
        text=_('See the tone frame around a word from the dictionary')
        chk_btn=Button(window.frame1,text = text, command = chk)
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
    def getsoundcardindex(self):
        log.info("Asking for sampling frequency...")
        window=Window(self.frame, title=_('Select Sound Card'))
        Label(window.frame, text=_('What sound card do you '
                                    'want to work with?')
                ).grid(column=0, row=0)
        buttonFrame1=ButtonFrame(window.frame,
                                self.audio_card_indexes,self.setsoundcardindex,
                                window
                                )
        buttonFrame1.grid(column=0, row=1)
    """Set User Input"""
    def set(self,attribute,choice,window):
        """Before I can use this, I need to pass attribute through the button
        frame."""
        window.destroy()
        if getattr(self,attribute) != choice: #only set if different
            setattr(self,attribute,choice)
            """If there's something getting reset that shouldn't be, remove it
            from self.defaults[attribute]"""
            self.cleardefaults(attribute)
            if attribute not in ['fs',
                                'sample_format',
                                'audio_card_index']:
                self.checkcheck()
            if attribute in ['analang', 'interpret','distinguish']: #do the last two cause problems?
                self.reloadprofiledata()
        else:
            log.debug(_('No change: {} == {}'.format(attribute,choice)))
    def setinterfacelangwrapper(self,choice,window):
            self.set('interfacelang',choice,window) #set the check variable
            setinterfacelang(choice) #change the UI *ONLY* no object attributes
            # inherit(self,'interfacelang')
            self.storedefaults()
            for base in [self,self.parent.parent]:
                setattr(base,'interfacelang',choice)
                log.info("pre checkcheck {base}: {}".format(getattr(base,
                                                'interfacelang'),base=base))
            self.checkcheck()
    def setprofile(self,choice,window):
        self.set('profile',choice,window)
    def settype(self,choice,window):
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
        print(pss)
        buttonFrame1=ButtonFrame(window.frame,
                                pss,self.setps,
                                window
                                )
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
            Label(window.frame, text=_('What syllable profile do you '
                                    'want to work with?')
                                    ).grid(column=0, row=0)
            optionslist = sorted([({
                'code':profile,
                'description':len(self.profilesbysense[self.ps][profile])
                            }) for profile in self.profilesbysense[self.ps]],
                            key=lambda s: s['description'],reverse=True)
            if self.additionalprofiles is not None:
                optionslist+=[({
                'code':profile,
                'description':profile}) for profile in self.additionalprofiles]
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
        self.defaults={None:[
                            'analang', # independent of lift.analang?
                            'glosslang', # independent of lift.glosslang?
                            'glosslang2',
                            'audiolang',
                            'ps',
                            'profile',
                            'type',
                            'name',
                            'regexCV',
                            # 'toneframes', #this has [ps] keys, don't reset below!
                            'subcheck',
                            'additionalps',
                            # 'profilesbysense',
                            'entriestoshow',
                            'additionalprofiles',
                            'sample_format',
                            'fs',
                            'audio_card_index',
                            'interfacelang',
                            'examplespergrouptorecord',
                            'distinguish',
                            'interpret',
                            'adnlangnames',
                            'exs'
                            ],
                        'ps':[
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
                        'examplespergrouptorecord':[],
                        'distinguish':[],
                        'interpret':[],
                        'adnlangnames':[],
                        'exs':[]
                        }
    def cleardefaults(self,field=None):
        for default in self.defaults[field]:
            setattr(self, default, None)
            """These can be done in checkcheck..."""
    def restart(self):
        self.parent.parent.destroy()
        main()
    def reloadprofiledata(self):
        self.storedefaults()
        file.remove(self.profiledatafile)
        self.restart()
    def loadprofiledata(self):
        """This should just be imported, with all defaults in a dictionary
        variable in the file."""
        try:
            spec = importlib.util.spec_from_file_location("profiledata",
                                                        self.profiledatafile)
            module = importlib.util.module_from_spec(spec)
            sys.modules['profiledata'] = module
            spec.loader.exec_module(module)
            self.profilesbysense=module.profilesbysense
            self.profilecounts=module.profilecounts
            self.profilecountInvalid=module.profilecountInvalid
            self.scount=module.scount
        except:
            log.info("There doesn't seem to be a profile data file; "
                    "making one now (wait maybe three minutes).")
            self.profilesbysense=None
        return
    def loadtypedict(self):
        """I just need this to load once somewhere..."""
        self.typedict={
                'V':{'sg':_('Vowel'),'pl':_('Vowels')},
                'C':{'sg':_('Consonant'),'pl':_('Consonants')},
                'CV':{'sg':_('Consonant-Vowel combination'),'pl':_('Consonant-Vowel combinations')},
                'T':{'sg':_('Tone'),'pl':_('Tones')},
                }
    def loaddefaults(self,field=None):
        # _=self._
        """This should just be imported, with all defaults in a dictionary
        variable in the file."""
        try:
            spec = importlib.util.spec_from_file_location("checkdefaults",
                                                        self.defaultfile)
            d = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(d)
            for default in self.defaults[field]:
                if hasattr(d, default):
                    setattr(self,default,getattr(d,default))
                print(default, getattr(self,default))
        except:
            log.info("There doesn't seem to be a default file; "
                    "continuing without one.")
        return
    def storedefault(self,default):
        """This depends on storedefaults"""
        if self.debug == True:
            print("trying to store "+default)
            print(getattr(self,default))
        value=getattr(self,default)
        if type(value) is str:
            text=(default+'="'+getattr(self,default)+'"')
        else: #at least for dictionary values... what else?
            text=(default+'='+str(getattr(self,default)))
        self.f.write(text+'\n')
    def storedefaults(self):
        """I don't think this does what I thought it did..."""
        self.f = open(self.defaultfile, "w", encoding='utf-8')
        for default in self.defaults[None]:
            if self.debug==True:
                print(type(default))
                print(default+": "+str(hasattr(self, default))+": "+str(getattr(self,default)))
            if hasattr(self, default) and (getattr(self,default) is not None):
                self.storedefault(default)
        self.f.close()
    def loadtoneframes(self):
        try:
            spec = importlib.util.spec_from_file_location("toneframes",
                                                        self.toneframesfile)
            # print(spec)
            module = importlib.util.module_from_spec(spec)
            sys.modules['toneframes'] = module
            spec.loader.exec_module(module)
            self.toneframes=module.toneframes
        except:
            print("Problem importing",self.toneframesfile)
            self.toneframes={}
    def loadstatus(self):
        try:
            spec = importlib.util.spec_from_file_location("verificationstatus",
                                                        self.statusfile)
            # print(spec)
            module = importlib.util.module_from_spec(spec)
            sys.modules['verificationstatus'] = module
            spec.loader.exec_module(module)
            self.status=module.status
        except:
            print("Problem importing",self.statusfile)
            self.status={}
    def updatestatus(self,verified=False):
        #This function updates the status file, not the lift file.
        if self.type not in self.status:
            self.status[self.type]={}
        if self.ps not in self.status[self.type]:
            self.status[self.type][self.ps]={}
        if self.profile not in self.status[self.type][self.ps]:
            self.status[self.type][self.ps][self.profile]={}
        if self.name not in self.status[self.type][self.ps][self.profile]:
            self.status[self.type][self.ps][self.profile][self.name]=list()
        if verified == True:
            if self.subcheck not in (
                self.status[self.type][self.ps][self.profile][self.name]):
                self.status[self.type][self.ps][self.profile][self.name].append(
                                                                self.subcheck)
            else:
                log.info("Tried to set {} verified in {} {} {} {} but it was "
                        "already there.".format(self.subcheck,self.type,
                        self.ps,self.profile,self.name,))
        if verified == False:
            if self.subcheck in (
                            self.status[self.type][self.ps][self.profile]
                            [self.name]):
                self.status[self.type][self.ps][self.profile][self.name
                                                                ].remove(
                                                                self.subcheck)
            else:
                print("Tried to set",self.subcheck,"UNverified in",self.type,
                        self.ps,self.profile,self.name,"but it wasn't "
                        "there.")
        self.storestatus()
    def storeprofiledata(self):
        self.f = open(self.profiledatafile, "w", encoding='utf-8')
        text=[f"profilesbysense={self.profilesbysense}",
            f"profilecounts={self.profilecounts}",
            f"profilecountInvalid={self.profilecountInvalid}",
            f"scount={self.scount}"]
        for t in text:
            self.f.write(t+'\n')
        self.f.close()
        if self.debug==True:
            print(type(self.profilesbysense),self.profilesbysense)
            print(type(self.profilecounts),self.profilecounts)
            print(type(self.profilecountInvalid),self.profilecountInvalid)
    def storetoneframes(self):
        self.f = open(self.toneframesfile, "w", encoding='utf-8')
        text=f"toneframes={self.toneframes}"
        self.f.write(text+'\n')
        self.f.close()
        if self.debug==True:
            print(type(self.toneframes),self.toneframes)
    def storestatus(self):
        self.f = open(self.statusfile, "w", encoding='utf-8')
        text=f"status={self.status}"
        self.f.write(text+'\n')
        self.f.close()
        if self.debug==True:
            print(type(self.status),self.status)
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
    def getscounts(self):
        """This depends on self.sextracted, from getprofiles"""
        self.scount={}
        for ps in self.db.pss:
            self.scount[ps]={}
            for s in self.rx:
                self.scount[ps][s]=collections.Counter(self.sextracted[ps][s]).most_common()
    def getprofiles(self):
        self.profileswdatabyentry={}
        self.profilesbysense={}
        self.profilesbysense['Invalid']=[]
        self.profiledguids=[]
        self.profiledsenseids=[]
        profileori=self.profile #We iterate across this here
        psori=self.ps #We iterate across this here
        onlyCV={'C','N','G','S','V','#'}
        self.sextracted={} #Will store matching segments here
        for ps in self.db.pss:
            self.sextracted[ps]={}
            for s in self.rx:
                self.sextracted[ps][s]=list()
        todo=len(self.db.senseids)
        x=0
        for senseid in self.db.senseids:
            x+=1
            forms=self.db.citationorlexeme(senseid=senseid,lang=self.analang)
            for form in forms:
                self.profile=self.profileofform(form)
                if x % 10 is 0:
                    log.debug("{}: {}; {}".format(str(x)+'/'+str(todo),form,
                                                    self.profile))
                if onlyCV.issuperset(self.profile):
                    for self.ps in self.db.get('ps',senseid=senseid):
                        # print("Good profile!",form,profile)
                        self.addtoprofilesbysense(senseid)
                else:
                    # print("Invalid profile!",form,profile)
                    self.profilesbysense['Invalid']+=[senseid]
        self.getscounts()
        print('Done:',time.time()-self.start_time)
        # self.debug=True
        if self.debug==True:
            for ps in self.profilesbysense:
                if ps == 'Invalid':
                    print(ps,self.profile,len(self.profilesbysense[ps]))
                else:
                    for profile in self.profilesbysense[ps]:
                        print(ps,profile,len(self.profilesbysense[ps][profile]))
        self.profile=profileori
        self.ps=psori
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
        formori=form
        """priority sort alphabets (need logic to set one or the other)"""
        """Look for any C, don't find N or G"""
        priority=['#','̃','C','N','G','S','V']
        """Look for word boundaries, N and G before C (though this doesn't
        work, since CG is captured by C first...)"""
        priority=['#','̃','N','G','S','C','Ṽ','V','d','b']
        log.log(15,"Searching {} in this order: {}".format(form,
                        sorted(self.rx.keys(),
                        key=lambda cons: (-len(cons),
                                            [priority.index(c) for c in cons])
                        )))
        log.log(15,"Searching with these regexes: {}".format(self.rx))
        for s in sorted(self.rx.keys(),
                        key=lambda cons: (-len(cons),
                                            [priority.index(c) for c in cons])
                        ):
            log.log(3,'s: {}; rx: {}'.format(s, self.rx[s]))
            for ps in self.db.pss:
                self.sextracted[ps][s]+=self.rx[s].findall(form) #collect matches for that one variable
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
        return idsbyps[randint(0, len(idsbyps))]
    def framenamesbyps(self,ps):
        """Names for all tone frames defined for the language."""
        if self.toneframes is not None:
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
    def getframeddata(self,source,noframe=False,notonegroup=False):
        """This generates a dictionary of form {'form':outputform,
        'gloss':outputgloss} for display, by senseid"""
        """Sometimes this script is called to make the example fields, other
        times to display it. If source is a senseid, it pulls form/gloss/etc
        information from the entry. If source is an example, it pulls that info
        from the example. The info is formatted uniformly in either case."""
        output={}
        if self.debug == True:
            print(source, type(source))
            print('self.glosslang:',self.glosslang)
            print('self.glosslang2:',self.glosslang2)
        """Just in case there's a problem later..."""
        forms={}
        glosses={}
        gloss={}
        tonegroups=None
        """Build dual logic here:"""
        if isinstance(source,lift.ET.Element):
            if self.debug == True:
                log.info('Element found!')
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
                if ((node.tag == 'field') and
                                (subnode.get('type') == 'tone')):
                    tonegroups=node.findall('text')
            log.log(2,'forms: {}'.format(forms))
            for lang in glosses: #gloss doesn't seem to be defined above; glosses?
                log.log(2,'gloss[{}]: {}'.format(lang,glosses[lang]))
            log.log(2,'tonegroups: {}'.format(tonegroups))
            """convert from lists to single items without loosing data,
            then pull text from nodes"""
            form=t(firstoflist(forms[self.analang]))
            if self.audiolang in forms:
                voice=t(firstoflist(forms[self.audiolang]))
            else:
                voice=None
            for lang in glosses:
                if (lang == self.glosslang) or (lang == self.glosslang2):
                    gloss[lang]=t(firstoflist(glosses[lang]))
            tonegroup=t(firstoflist(tonegroups))
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
            if self.debug == True:
                log.info('36 character senseid string!')
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
            tonegroups=self.db.get('exfieldvalue', senseid=senseid,
                                fieldtype='tone', location=self.name)
            """convert from lists to single items without loosing data"""
            form=firstoflist(forms[self.analang])
            voice=firstoflist(forms[self.audiolang])
            for lang in glosses:
                gloss[lang]=firstoflist(glosses[lang])
                log.log(2,'gloss[{}]: {}'.format(lang,gloss[lang]))
            tonegroup=firstoflist(tonegroups)
        else:
            log.info('Neither Element nor senseid was found!')
            return output
        log.log(2,'form: {}'.format(form))
        for lang in gloss:
            log.log(2,'gloss:'.format(gloss[lang]))
        log.log(2,'tonegroup: {}'.format(tonegroup))
        """The following is the same for senses or examples"""
        if (notonegroup == False) and (tonegroup != None):
            try:
                int(tonegroup)
            except:
                output['tonegroup']=tonegroup #this is only for named groups
        if self.debug == True:
            print(forms,glosses[lang])
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
                form='noform'
            for lang in gloss:
                if gloss[lang] == None:
                    gloss[lang]='nogloss'
            if self.debug ==True:
                print(frame)
            output[self.analang]=self.frameregex.sub(form,frame[self.analang])
            for lang in gloss:
                """only give these if the frame has this gloss, *and* if
                the gloss is in the data (user selection is above)"""
                if ((lang == self.glosslang) or ((self.glosslang2 in frame)
                                                    and (gloss[lang] != None))):
                    output[lang]=self.frameregex.sub(gloss[lang],frame[lang])
        else:
            output[self.analang]=form
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
        #If the user exits out before this point, just stop.
        try:
            self.frame.winfo_exists()
        except:
            return
        self.makestatus()
        """We start with the settings that we can likely guess"""
        for base in [self,self.parent.parent]:
            log.info("{base}: {}".format(getattr(base,'interfacelang'),base=base))
        if self.interfacelang == None:
            log.info("No interface language! Guessing.")
            self.guessinterfacelang()
        else:
            if self.debug == True:
                log.info('interfacelang already set')
        """Get Analang"""
        if self.analang not in self.db.analangs:
            self.guessanalang()
        if (self.analang == None) or ():
            log.info("find the language")
            self.getanalang()
            return
        if self.audiolang == None:
            self.guessaudiolang() #don't display this, but make it
        """This just gets the prose language name from the code"""
        # self.parent.parent.interfacelangs is set in file.py
        for l in self.parent.parent.interfacelangs:
            if l['code']==self.parent.parent.interfacelang:
                interfacelanguagename=l['name']
        t=(_("Using {}").format(interfacelanguagename))
        proselabel(opts,t)
        opts['row']+=1
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
        if self.ps not in self.db.pss:
            self.guessps()
        if self.ps == None:
            log.info("find the ps")
            self.getps()
            return
        """Get profile (this depends on ps)"""
        if self.ps not in self.profilesbysense:
            log.error("{} doesn't seem to be in profiles by sense: {}. Do you "
                        "need to rerun your syllable profiles? Exiting.".format(
                        self.ps,self.profilesbysense.keys()
            ))
            exit()
        if self.profile not in self.profilesbysense[self.ps]:
            self.guessprofile()
        if self.profile == None:
            log.info("Select a syllable profile.")
            self.getprofile()
            return
        count=self.countbypsprofile(self.ps,self.profile)
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
            elif self.name not in self.toneframes[self.ps]:
                self.getcheck()
                return
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
            # t=(_("Checking {}, working on {}".format(
            #             self.typedict[self.type]['pl'],self.name)))
        """Get subcheck"""
        self.getsubchecksprioritized()
        print(self.subcheck,self.subchecksprioritized[self.type])
        if self.subcheck not in [x[0] for x in self.subchecksprioritized[self.type]]:
            self.guesssubcheck()
        print(self.subcheck,self.subchecksprioritized[self.type])
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
        self.storedefaults()
        self.checkcheck()
    def soundcheckrefresh(self):
        self.soundsettingswindow.resetframe() # Frame(self.soundsettingswindow.frame)
        # self.soundsettingswindow.frame.grid(row=1,column=0)
        row=0
        Label(self.soundsettingswindow.frame,
                text="Current Sound Card Settings:").grid(row=row,column=0)
        row+=1
        # row=0
        if self.fs is None:
            Label(self.soundsettingswindow.frame,
                                text='<unset>').grid(row=row,column=0)
        else:
            for ratedict in self.fss:
                if self.fs==ratedict['code']:
                    self.fsname=ratedict['name']
            Label(self.soundsettingswindow.frame,
                                text=self.fsname).grid(row=row,column=0)
        text=_("Change")
        Button(self.soundsettingswindow.frame, choice=text,
                        text=text, anchor='c',
                        cmd=self.getsoundhz).grid(row=row,column=1)
        row+=1
        if self.sample_format is None:
            Label(self.soundsettingswindow.frame,
                                text='<unset>').grid(row=row,column=0)
        else:
            for ratedict in self.sample_formats:
                if self.sample_format==ratedict['code']:
                    self.sample_formatname=ratedict['name']
            Label(self.soundsettingswindow.frame,
                        text=self.sample_formatname).grid(row=row,column=0)
        Button(self.soundsettingswindow.frame, choice=text,
                        text=text, anchor='c',
                        cmd=self.getsoundformat).grid(row=row,column=1)
        row+=1
        if self.audio_card_index is None:
            Label(self.soundsettingswindow.frame,
                                text='<unset>').grid(row=row,column=0)
        else:
            for ratedict in self.audio_card_indexes:
                if self.audio_card_index==ratedict['code']:
                    self.audio_card_indexname=ratedict['name']
            Label(self.soundsettingswindow.frame,
                        text=self.audio_card_indexname).grid(row=row,column=0)
        Button(self.soundsettingswindow.frame, choice=text,
                        text=text, anchor='c',
                        cmd=self.getsoundcardindex).grid(row=row,column=1)
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
        p = pyaudio.PyAudio()
        info = p.get_host_api_info_by_index(0)
        numdevices = info.get('deviceCount')
        for i in range(0, numdevices):
            if (p.get_device_info_by_host_api_device_index(0, i).get(
                                                    'maxInputChannels')) > 0:
                    log.info("Input Device id {} - {}".format(i,
                        p.get_device_info_by_host_api_device_index(0, i).get(
                                                                    'name')))
                    self.audio_card_indexes+=[{
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
        log.log(2,"fs: {}; sf: {}; ci: {}".format(
                        self.fs,self.sample_format,self.audio_card_index))
        # ButtonFram
        self.soundcheckrefresh()
        self.soundsettingswindow.wait_window(self.frame.status)
        self.soundsettingswindow.destroy()
    def maybeboard(self):
        if hasattr(self,'leaderboard') and type(self.leaderboard) is Frame:
            self.leaderboard.destroy()
        self.leaderboard=Frame(self.frame)
        self.leaderboard.grid(row=0,column=1,sticky="new")
        done=int()
        if self.type in self.status:
            if self.ps in self.status[self.type]:
                for profile in self.status[self.type][self.ps]:
                    done+=len(self.status[self.type][self.ps][profile])
                log.info('done: {}'.format(done))
                if done >0:
                    if (hasattr(self,'noboard') and (self.noboard is not None)): #.winfo_exists())):
                        self.noboard.destroy()
                    # except:
                    #     print("Apparently noboard hasn't been made.",
                    #         hasattr(self,'noboard'))#,self.noboard.winfo_exists())
                    if self.type == 'T':
                        if self.ps in self.toneframes:
                            self.maketoneprogresstable()
                        else:
                            self.makenoboard()
                            return
                    else:
                        log.info("Found CV verifications")
                        self.makeCVprogresstable()
                else:
                    self.makenoboard()
                    return
            else:
                self.makenoboard()
                return
        else:
            self.makenoboard()
            return
    def makenoboard(self):
        log.info("No Progress board")
        # self.leaderboard.destroy()
        self.noboard=Label(self.leaderboard, image=self.photo['transparent'],
                    text='', pady=50,
                    bg='red' #self.theme['background']
                    ).grid(row=0,column=1,sticky='we')
    def makeCVprogresstable(self):
        Label(self.leaderboard, text=_('{} Progress').format(self.typedict[self.type]['sg']), font=self.fonts['title']
                        ).grid(row=0,column=0,sticky='nwe')
        self.leaderboardtable=Frame(self.leaderboard)
        self.leaderboardtable.grid(row=1,column=0)
        Label(self.leaderboardtable,text=_("Nothing to see here..."),
                    # font=self.fonts['reportheader']
                    ).grid(
        row=1,column=0#,sticky='s'
        )
    def maketoneprogresstable(self):
        def groupfn(x):
            print(x)
            if x != [] and len(x[0])>1:
                return nn(x,oneperline=True) #to show groups...
            else:
                return len(x) #to show counts
        title=_('Tone Progress for {} Words'.format(self.ps))
        Label(self.leaderboard, text=title, font=self.fonts['title'],padx=25
                        ).grid(row=0,column=0,sticky='nwe')
        self.leaderboardtable=Frame(self.leaderboard)
        self.leaderboardtable.grid(row=1,column=0)
        row=0
        profiles=['header']+list(self.profilesbysense[self.ps].keys())
        frames=list(self.toneframes[self.ps].keys())
        for profile in profiles:
            column=0
            # print('row=',row,'column=',column,profile,'outside')
            if (profile == 'header') or (profile in
                                        self.status[self.type][self.ps]):
                if profile in self.status[self.type][self.ps]:
                    Label(self.leaderboardtable,text=profile).grid(
                    row=row,column=column,sticky='e'
                    )
                for frame in frames:
                    column+=1
                    # print('row=',row,'column=',column,profile,frame,'inside')
                    if profile == 'header':
                        Label(self.leaderboardtable,text=frame,
                                    font=self.fonts['reportheader']
                                    # angle=90,
                                    # wraplength=1
                                    ).grid(
                        row=row,column=column,sticky='s'
                        )
                    elif frame in self.status[self.type][self.ps][profile]:
                        done=self.status[self.type][self.ps][profile][frame]
                        Label(self.leaderboardtable,
                                text=groupfn(done)
                                ).grid(
                        row=row,column=column
                        )
            row+=1
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
        self.results = Frame(self.runwindow.frame,width=800)
        self.results.grid(row=0, column=0)
    def setnamesall(self):
        self.checknamesall={
        "V":{
            1:[("V1", "First/only Vowel")],
            2:[
                ("V1=V2", "Same First/only Two Vowels"),
                ("V2", "Second Vowel")
                ],
            3:[
                ("V1=V2=V3", "Same First/only Three Vowels"),
                ("V3", "Third Vowel"),
                ("V2=V3", "Same Second Two Vowels")
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
                ("CV1", "First/only CV")
                ],
            2:[("CV2", "Second CV"),
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
            self.checkspossible=self.setnamesbyprofile() #This shouln't return tone checks
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
            buttonFrame1=ButtonFrame(window.frame,
                                    self.checkspossible,
                                    self.setcheck,
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
        # for guid in self.guidstosort:
        #     for location in self.db.get('pronunciationfieldlocation',
        #         guid=guid, fieldtype='tone'):
        #         self.locations+=[location]
        for senseid in self.senseidstosort:
            for location in self.db.get('exfieldlocation',
                senseid=senseid, fieldtype='tone'):
                self.locations+=[location]
        self.locations=list(dict.fromkeys(self.locations))
    def topps(self,x='ALL'):
        """take the top x ps', irrespective of profile"""
        pss=list()
        if x == 'ALL':
            x=len(self.profilecounts)
        for count in range(x):
            pss+=[self.profilecounts[count][2]] #(count, profile, ps)
        # print(pss)
        return list(dict.fromkeys(pss))
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
        subchecks=self.s[self.analang][self.type]
        # if self.type == 'V':
        #     subchecks=self.s[self.analang]['V'] #(just the vowels
        # elif self.type == 'C':
        #     subchecks=self.s[self.analang]['C']
        # else:
        #     print("Sorry, not sure what I'm doing:",self.type)
        """This sets each of the checks that are applicable for the given
        profile; self.basicreported is from self.basicreport()"""
        for typenum in self.basicreported:
            log.log(2, '{}: {}'.format(typenum,self.basicreported[typenum]))
        """setnamesbyprofile doesn't depend on self.ps"""
        for codenname in sorted(self.setnamesbyprofile(),
                        key=lambda s: len(s[0]),reverse=True):
            """self.name set here"""
            self.name=codenname[0] #just codes, not names
            self.typenumsRun=[typenum for typenum in self.typenums
                                        if re.search(typenum,self.name)]
            log.debug('self.name: {}; self.type: {}; self.typenums: {}; '
                        'self.typenumsRun: {}'.format(self.name,self.type,
                                                self.typenums,self.typenumsRun))
            if len(self.name) == 1:
                log.debug("Error! {} Doesn't seem to be list formatted.".format(
                                                                    self.name))
            for self.subcheck in subchecks:
                t=_("{}={}".format(self.name,self.subcheck))
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
                    # matchestofind=
                    matches-=self.basicreported[typenum]
                log.log(2,"{} matches found!: {}".format(len(matches),matches))
                            # len(matches-self.basicreported[typenum]),
                            # matches-self.basicreported[typenum]))
                if len(matches)>0:
                    id=rx.id('x'+self.ps+self.profile+self.name+self.subcheck)
                    ex=xlp.Example(parent,id)
                    for senseid in matches:
                        for typenum in self.typenumsRun:
                            self.basicreported[typenum].add(senseid)
                        framed=self.getframeddata(senseid,noframe=True)
                        print('\t',framed['formatted'])
                        self.framedtoXLP(framed,parent=ex,listword=True)
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
                            # framed[self.audiolang])
        else:
            el=xlp.LangData(ex,self.analang,framed[self.analang])
        eg=xlp.Gloss(ex,self.glosslang,framed[self.glosslang])
        if ((self.glosslang2 != '') and (self.glosslang2 in framed)
                and (framed[self.glosslang2] != None)):
                eg2=xlp.Gloss(ex,self.glosslang2,framed[self.glosslang2])
    def makecountssorted(self):
        self.profilecounts={}
        wcounts=list()
        for ps in self.profilesbysense:
            # pscount=0
            if ps == 'Invalid': #Including these below causes trouble
                self.profilecountInvalid=len(self.profilesbysense[ps])
                # wcounts.append((count, None, ps))
            else:
                for profile in self.profilesbysense[ps]:
                    count=len(self.profilesbysense[ps][profile])
                    # pscount+=count
                    wcounts.append((count, profile, ps))
        self.profilecounts=sorted(wcounts,reverse=True)
        self.Scounts={}
    def printcountssorted(self):
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
    def getex(self,value,notonegroup=True):
        """This function finds examples in the lexicon for a given tone value,
        in a given tone frame (from check)"""
        senseids=self.getexsall(value)
        if self.exs == None:
            self.exs={} #in case this hasn't been set up by now
        if value in self.exs:
            if self.exs[value] in senseids: #if stored value is in group
                log.info("Using stored value for {} group: {}".format(value,
                                self.exs[value]))
                return self.getframeddata(self.exs[value],
                                            notonegroup=notonegroup)
        for i in range(len(senseids)): #just keep trying until you succeed
            senseid=senseids[randint(0, len(senseids))-1]
            framed=self.getframeddata(senseid,notonegroup=notonegroup)
            if ((framed[self.analang] != None) and
                    (framed[self.glosslang] != None)):
                """As soon as you find one with form and gloss, quit."""
                self.exs[value]=senseid
                return framed
            else:
                log.info("Example sense with empty field problem")
    def renamegroup(self):
        def submitform():
            newtonevalue=formfield.get()
            if newtonevalue in self.tonegroups:
                er=Window(self.runwindow)
                l=Label(er,text=_("Sorry, there is already a group with that "
                                "label; If you want to join the groups, "
                                "give it a different name now, and join "
                                "it after they are both verified ({} is "
                                "already in {})".format(newtonevalue,
                                                        self.tonegroups)))
                l.grid(row=0,column=0)
                self.gettonegroups()
                return
            self.updatebysubchecksenseid(self.subcheck,newtonevalue)
            self.subcheck=newtonevalue
            # print('Pre-rename tonegroups:',self.tonegroups)
            self.gettonegroups()
            # print('Post-rename tonegroups:',self.tonegroups)
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
        self.settonevariablesbypsprofile()
        if self.senseidsunsorted != []:
            quit=self.sortT()
            if quit == True:
                return 1
        """offer a chance to join groups before moving on
        Nope: do this after verifying piles!"""
        # self.getrunwindow()
        # self.joinT()
        # self.updatestatus(verified=False)
        if ((self.type in self.status) and
            (self.ps in self.status[self.type]) and
            (self.profile in self.status[self.type][self.ps]) and
            (self.name in self.status[self.type][self.ps][self.profile])):
            verified=self.status[self.type][self.ps][self.profile][self.name]
        else:
            verified=set()
        """Let's not leave groups in verified after they are gone"""
        # for group in verified:
        #     if group not in self.tonegroups:
        #         verified.remove(group)
        """if all items in the self.tonegroups exists in verified"""
        if set(self.tonegroups).issubset(verified):
            # self.getrunwindow()
            joined=self.joinT()
            if joined == True:
                """Don't know how many joins we'll need, nor the results of
                susequent verifications or sorts"""
                self.maybesort()
                self.runwindow.ww.close()
                return
            elif joined == False and self.runwindow.winfo_exists():
                self.runwindow.resetframe()
                Label(self.runwindow.frame, text=done).grid(row=0,column=0)
                Label(self.runwindow.frame, text='',
                            image=self.photo[self.type]
                            ).grid(row=1,column=0)
                print(done)
                return
        # elif self.runwindow.winfo_exists(): #pull this?
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
        self.runwindow.frame.scroll.grid(
                                column=1,row=2, sticky="new")
        """The frame for the groups buttons"""
        self.runwindow.frame.scroll.content.groups=Frame(
                                            self.runwindow.frame.scroll.content)
        self.runwindow.frame.scroll.content.groups.grid(row=0,column=0,
                                                                sticky="ew")
        self.runwindow.frame.scroll.content.groups.row=0 #rows for this frame
        """If we have tone groups already, make them now."""
        for group in self.tonegroups:
            self.tonegroupbuttonframe(self.runwindow.frame.scroll.content.groups,
            group,row=self.runwindow.frame.scroll.content.groups.row) #notonegroup?
            self.runwindow.frame.scroll.content.groups.row+=1
        """The second frame, for the other two buttons, which also scroll"""
        self.runwindow.frame.scroll.content.anotherskip=Frame(
                                            self.runwindow.frame.scroll.content)
        self.runwindow.frame.scroll.content.anotherskip.grid(row=1,column=0)
        self.getanotherskip(self.runwindow.frame.scroll.content.anotherskip)
        while self.senseidsunsorted != [] and self.runwindow.winfo_exists():
            self.groupselected=[] #reset this for each word!
            senseid=self.senseidsunsorted[0]
            progress=(str(self.senseidstosort.index(senseid)+1)+'/'
                        +str(todo))
            print(senseid,progress)
            framed=self.getframeddata(senseid)
            """After the first entry, sort by groups."""
            print('self.tonegroups:',self.tonegroups)
            # if self.tonegroups != []:
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
            self.runwindow.ww.close()
            self.runwindow.wait_window(window=self.sorting)
            if not self.runwindow.winfo_exists():
                return
            print("Group selected:",self.groupselected)
            if (self.groupselected == "NONEOFTHEABOVE"):
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
                        row=self.runwindow.frame.scroll.content.groups.row)
                print('Group added:',self.groupselected)
            else: #before making a new button, or now, add fields to the sense.
                """This needs to *not* operate on "exit" button."""
                if self.groupselected != []:
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
        self.settonevariablesbypsprofile()
        """self.subcheck is set here, but probably OK"""
        for self.subcheck in self.tonegroups:
            if self.subcheck in (self.status[self.type][self.ps][self.profile]
                                            [self.name]):
                print(self.subcheck, "already verified, continuing.")
                continue
            if not self.runwindow.winfo_exists():
                return
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
            self.groupselected='' #reset this so it doesn't get in our way later.
            row=0
            column=0
            if self.subcheck in self.tonegroups:
                progress=('('+str(self.tonegroups.index(self.subcheck)+1)+'/'
                                            +str(len(self.tonegroups))+')')
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
            for senseid in self.getexsall(self.subcheck):
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
            self.runwindow.ww.close()
            b.wait_window(bf)
            if self.groupselected == "ALLOK":
                print(f"User selected '{oktext}', moving on.")
                self.updatestatus(verified=True)
                self.checkcheck()
            else:
                print(f"User did NOT select '{oktext}', assuming we'll come "
                        "back to this!!")
        if self.runwindow.winfo_exists():
            self.maybesort()
    def verifybutton(self,parent,senseid,row,column=0,label=False,**kwargs):
        if 'font' not in kwargs:
            kwargs['font']=self.fonts['read']
        if 'anchor' not in kwargs:
            kwargs['anchor']='w'
        framed=self.getframeddata(senseid,notonegroup=True)
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
        print(introtext)
        self.groupselected=None
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
        self.settonevariablesbypsprofile()
        row=0
        canary=Label(self.runwindow,text='')
        canary.grid(row=5,column=5)
        canary2=Label(self.runwindow,text='')
        canary2.grid(row=5,column=5)
        for group in self.tonegroups:
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
        self.runwindow.ww.close()
        self.runwindow.frame.wait_window(canary)
        if self.groupselected != "ALLOK" and self.runwindow.winfo_exists():
            group1=self.groupselected
            row=self.tonegroups.index(group1)
            self.tonegroupbuttonframe(self.sorting,group1,row,notonegroup=False,
                                        label=True, font=self.fonts['readbig'],
                                        canary=canary,canary2=canary2)
            self.groupselected=None #don't want to leave this there...
            log.debug('self.tonegroups: {}; group1: {}'.format(self.tonegroups,
                                                                        group1))
            self.runwindow.wait_window(canary2)
            if self.groupselected == "ALLOK":
                print(f"User selected '{oktext}', moving on.")
                self.groupselected='' #reset
                return 0
            if self.groupselected != None:
                self.runwindow.wait()
                print("Now we're going to join groups",group1,"an"
                    "d",self.groupselected,".")
                """All the senses we're looking at, by ps/profile"""
                self.updatebysubchecksenseid(group1,self.groupselected)
                self.subcheck=group1
                self.updatestatus() #not verified=True --if any joined.
                self.subcheck=self.groupselected
                self.updatestatus() #not verified=True --if any joined.
                print('Mark',self.groupselected,'as unverified!!?!')
                # self.runwindow.ww.close()
                return 1
        elif self.groupselected == "ALLOK":
            print(f"User selected '{oktext}', moving on.")
            self.groupselected='' #reset
            return 0
        else:
            log.info("I don't understand the user input (closed window?): "
                    "{}".format(self.groupselected))
        """'These are all different' doesn't need to be saved anywhere, as this
        can happen at any time. just move on to verification, where each group's
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
        for i in self.tonegroups:
            try:
                values+=[int(i)]
            except:
                print('Tone group',i,'cannot be interpreted as an integer!')
        newgroup=max(values)+1
        self.tonegroups.append(str(newgroup))
        return str(newgroup)
    def addtonefieldex(self,senseid,framed):
        guid=None
        print("Adding",self.groupselected,"value to", self.name,"location "
                "in",'tone',"fieldtype",senseid,"senseid",
                guid,"guid (in main_lift.py)")
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
                                    fieldvalue=self.groupselected#,
                                    # ps=None #,showurl=True
                                    )
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
    def gettoneUFgroups(self):
        print("Looking for UF tone groups for",self.profile,self.ps)
        toneUFgroups=[]
        """Still working on one ps-profile combo at a time."""
        for senseid in self.senseidstosort: #I should be able to make this a regex...
            toneUFgroups+=self.db.get('toneUFfieldvalue', senseid=senseid,
                fieldtype='tone' # Including any lang at this point.
                # ,showurl=True
                )
            # print(tonegroups)
        self.toneUFgroups=list(dict.fromkeys(toneUFgroups))
        # if 'NA' in self.tonegroups:
        #     self.tonegroups.remove('NA')
        # self.debug = True
        if self.debug ==True:
            print('gettoneUFgroups:',self.toneUFgroups)
    def gettonegroups(self):
        print("Looking for tone groups for",self.name)
        tonegroups=[]
        # for guid in self.guidstosort: #I should be able to make this a regex...
        #     """For now, support both types of fields"""
        #     tonegroups+=self.db.get('pronunciationfieldvalue', guid=guid,
        #         fieldtype='tone', location=self.name) #,showurl=True
        #     print(tonegroups)
        for senseid in self.senseidstosort: #I should be able to make this a regex...
            tonegroups+=self.db.get('exfieldvalue', senseid=senseid,
                fieldtype='tone', location=self.name)#, showurl=True)
            # print(tonegroups)
        self.tonegroups=list(dict.fromkeys(tonegroups))
        if 'NA' in self.tonegroups:
            self.tonegroups.remove('NA')
        if self.debug ==True:
            print('gettonegroups:',self.tonegroups)
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
        self.senseidsunsorted.remove(senseid)
    def markunsortedsenseid(self,senseid):
        self.senseidsunsorted.append(senseid)
        self.senseidssorted.remove(senseid)
    def getidstosort(self):
        """These variables should not have to be reset between checks"""
        """If needed, this will break..."""
        # if ((self.ps not in self.profilesbysense) or
        #         (self.profile not in self.profilesbysense[self.ps])):
        #     profiles.wordsbypsprofile(self.db,self.ps,self.profile)
        # print('self.ps:',self.ps,self.profilesbysense.keys())
        # print('self.ps.keys:',self.ps,
        #         self.profilesbysense[self.ps].keys())
        # print('self.profile.keys:',self.profile,
        #         self.profilesbysense[self.ps][self.profile])
        # print(self.profilesbysense[self.ps][self.profile])
        self.senseidstosort=list(self.profilesbysense[self.ps]
                                                    [self.profile])
    def sortingstatus(self):
        self.getidstosort()
        self.senseidssorted=[]
        self.senseidsunsorted=[]
        for senseid in self.senseidstosort:
            if (self.db.get('exfieldvalue',
                            senseid=senseid,
                            location=self.name,
                            fieldtype='tone')
                            ) != []:
                self.senseidssorted+=[senseid]
            else:
                self.senseidsunsorted+=[senseid]
    def settonevariablesbypsprofile(self):
        """ps and profile should already be set before this is called, and if
        they change, this should be run again."""
        self.sortingstatus() #sets self.senseidssorted and senseidsunsorted
        self.gettonegroups() #sets self.tonegroups
    def tryNAgain(self):
        subcheckori=self.subcheck.copy()
        for self.subcheck in ['NA']:
            for senseid in self.senseidstosort:
                self.db.rmexfields(senseid=senseid,fieldtype='tone', #I might want to generalize this later...
                                location=self.name,fieldvalue=self.subcheck,
                                showurl=True
                                )
        self.subcheck=subcheckori
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
        if self.tonegroups == []:
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
    def tonegroupbuttonframe(self,parent,group,row,column=0,label=False,canary=None,canary2=None,**kwargs):
        if 'font' not in kwargs:
            kwargs['font']=self.fonts['read']
        if 'anchor' not in kwargs:
            kwargs['anchor']='w'
        if 'notonegroup' not in kwargs:
            notonegroup=True
        else:
            notonegroup=kwargs['notonegroup']
            del kwargs['notonegroup']
        if 'renew' in kwargs:
            if kwargs['renew'] == True:
                log.info("Resetting tone group example ({}): {}".format(group,
                                                            self.exs[group]))
                del self.exs[group]
            del kwargs['renew']
        framed=self.getex(group,notonegroup=notonegroup)
        if framed is None:
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
            bc=Button(bf, image=self.parent.photo['change'], #🔃 not in tck...
                    cmd=lambda p=parent:self.tonegroupbuttonframe(parent=parent,
                                group=group,notonegroup=notonegroup,
                                canary=canary,canary2=canary2,
                                row=row,column=column,label=label, renew=True)
                    ,**kwargs) #to Button
            bc.grid(column=1, row=0, sticky="nsew", ipady=15) #Inside buttons
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
                self.getsubcheck()
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
        # print(self.__dict__)
        # print(hasattr(self,'runwindow'))
        """Can't test for widget/window if the attribute hasn't been assigned,"
        but the attribute is still there after window has been killed, so we
        need to test for both."""
        if hasattr(self,'runwindow') and (self.runwindow.winfo_exists()):#(type(self.runwindow) is Window):
            # print(self.runwindow.winfo_exists())
            # print(type(self.runwindow))
            if self.debug == True:
                log.info("Runwindow already there! Resetting frame...")
            self.runwindow.resetframe() #I think I'll always want this here...
        else:
            t=(_("Run Window"))
            self.runwindow=Window(self.frame,title=t)
            self.runwindow.title(t)
        self.runwindow.wait()
    def runcheck(self):
        self.storedefaults() #This is not called in checkcheck.
        t=(_('Run Check'))
        log.info("Running check...")
        self.getrunwindow()
        # self.runwindow=Window(self.frame,title=t)
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
                self.maybesort()
            else: #do the CV checks
                self.getresults()
    def record(self):
        if ((self.fs == None) or (self.sample_format == None)
                or (self.audio_card_index == None)):
            self.soundcheck()
        self.storedefaults()
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
        self.runwindow.ww.close()
        self.runwindow.wait_window(self.runwindow.frame)
    def showentryformstorecord(self,justone=True):
        """Save these values before iterating over them"""
        psori=self.ps
        profileori=self.profile
        self.getrunwindow()
        if justone==True:
            self.showentryformstorecordpage()
        else:
            for psprofile in self.profilecounts:
                if self.runwindow.winfo_exists():
                    self.ps=psprofile[2]
                    self.profile=psprofile[1]
                    nextb=Button(self.runwindow,text=_("Next Group"),
                                            cmd=self.runwindow.resetframe) # .frame.destroy
                    nextb.grid(row=0,column=1,sticky='ne')
                    self.showentryformstorecordpage()
            self.ps=psori
            self.profile=profileori
    def showsenseswithexamplestorecord(self,senses=None):
        self.getrunwindow()
        """?Make this scroll!"""
        text=_("Words and phrases to record: click ‘Record’, talk, and release")
        instr=Label(self.runwindow.frame, anchor='w',text=text)
        instr.grid(row=0,column=0,sticky='w')
        if (self.entriestoshow is None) and (senses is None):
            Label(self.runwindow.frame, anchor='w',
                    text=_("Sorry, there are no entries to show!")).grid(row=1,
                                    column=0,sticky='w')
            return
        if senses is None:
            senses=self.entriestoshow
        for senseid in senses:
            print("Working on ",senseid)
            row=0
            if not self.runwindow.winfo_exists():
                return 1
            entryframe=Frame(self.runwindow.frame)
            entryframe.grid(row=1,column=0)
            """This is the title for each page: isolation form and glosses."""
            framed=self.getframeddata(senseid,noframe=True)
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
            examples=self.db.get('example',senseid=senseid)
            print('examples:',examples)
            if examples == []:
                text=_("No examples! Add some, then come back.")
                print(text)
                entryframe.destroy()
                Label(self.runwindow.frame, anchor='w', font=self.fonts['read'],
                        text=text).grid(row=1,column=0,sticky='w')
                continue #return #I want the "next" button...
            examples.reverse()
            for example in examples:
                """These should already be framed!"""
                framed=self.getframeddata(example,noframe=True)
                if framed[self.analang] is None:
                    continue
                row+=1
                """If I end up pulling from example nodes elsewhere, I should
                probably make this a function, like getframeddata"""
                text=framed['formatted']
                log.info('recordbuttonframetry')
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
            examplesframe.wait_window(entryframe)
    def showtonegroupexs(self):
        if (not(hasattr(self,'examplespergrouptorecord')) or
            (type(self.examplespergrouptorecord) is not int)):
            self.examplespergrouptorecord=5
            self.storedefaults()
        self.settonevariablesbypsprofile() #maybe not done before
        self.gettoneUFgroups()
        if self.toneUFgroups != []:
            torecord={}
            for toneUFgroup in self.toneUFgroups:
                torecord[toneUFgroup]=self.db.get('senseidbytoneUFgroup',
                                        fieldtype='tone', form=toneUFgroup)
            batch={}
            for i in range(self.examplespergrouptorecord):
                batch[i]=[]
                for toneUFgroup in self.toneUFgroups:
                    print(i,len(torecord[toneUFgroup]),toneUFgroup,torecord[toneUFgroup])
                    if len(torecord[toneUFgroup]) > i: #don't worry about small piles.
                        batch[i]+=[torecord[toneUFgroup][i]]
                    else:
                        print("Not enough examples, moving on:",i,toneUFgroup)
            print(_('Preparing to record examples from each tone group ({}) '
                    'with index').format(self.toneUFgroups),i)
            for i in range(self.examplespergrouptorecord):
                log.info(_('Giving user the number {} example from each tone '
                        'group ({}) with index'.format(i,self.toneUFgroups)))
                exited=self.showsenseswithexamplestorecord(batch[i])
                if exited == True:
                    return
            if self.runwindow.winfo_exists():
                Label(self.runwindow.frame, anchor='w',font=self.fonts['read'],
                text=_("All done! Sort some more words, and come back.")
                ).grid(row=0,column=0,rowspan=2,sticky='w')
            # self.runwindow.wait_window()
            #
        else:
            print("How did we get no UR tone groups?",self.profile,self.ps,
                    "\nHave you run the tone report recently?"
                    "\nDoing that for you now...")
            self.tonegroupreport(silent=True)
            self.showtonegroupexs()
    def getresults(self):
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
        self.runwindow.ww.close()
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
        # self.debug=True
        if self.debug == True:
            print('self.profile:',self.profile)
            print('self.type:',self.type)
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
        if self.type != 'T': #We don't want these subs for tone sorting
            S=str(self.type)
            regexS='[^'+S+']*'+S #This will be a problem if S=NC or CG...
            for occurrence in reversed(range(maxcount)):
                occurrence+=1
                if re.search(S+str(occurrence),self.name) != None:
                    """Get the (n=occurrence) S, regardless of intervening
                    non S..."""
                    regS='^('+regexS*(occurrence-1)+'[^'+S+']*)('+S+')'
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
    def tonegroupreport(self,silent=False):
        log.info("Starting report...")
        self.storedefaults()
        self.getrunwindow()
        self.tonereportfile=''.join([str(self.reportbasefilename),'_',
                            self.ps,'_',
                            self.profile,
                            ".ToneReport.txt"])
        start_time=time.time() #move this to function?
        self.getidstosort() #in case you didn't just run a check
        self.getlocations()
        output={}
        """Collect location:value correspondences, by sense"""
        for senseid in self.senseidstosort:
            output[senseid]={}
            for location in self.locations:
                output[senseid][location]={}
                group=self.db.get('exfieldvalue',senseid=senseid,
                    location=location,fieldtype='tone')
                log.debug(group)
                """Also include location:value for non-example fields"""
                """How to do this in a principled way?"""
                # for guid in self.db.get('guidbysenseid',senseid=senseid):
                #     group+=self.db.get('pronunciationfieldvalue',guid=guid,
                #         location=location,fieldtype='tone')
                # print(group)
                """Save this info by senseid"""
                output[senseid][location]=group
        log.info("Done organizing data; ready to report.")
        groups={}
        groupvalues=[]
        """Look through all the location:value combos (skip over senseids)
        this is, critically, a dictionary of each location:value correspondence
        for a given sense. So each groupvalue contains multiple location keys,
        each with a value value, and the sum of all the location:value
        correspondences for a sense defines the group --which is distinct from
        another group which shares some (but not all) of those location:value
        correspondences."""
        """For any non-linguists reading this, this is the key analytical step
        that moves us from a collection of surface forms (each pronunciation
        group in a given context) to the underlying form (which behaves the same
        as others in its group, across all contexts)."""
        # groupvalues=list(dict.fromkeys(output.values())) #can't hash this...
        for value in output.values(): #so we find unique values manually
            if value not in groupvalues:
                groupvalues+=[value]
        """For each set of location:value correspondences, find the senseids
        that have it."""
        x=1 #first group
        for value in groupvalues:
            groups[x]={}
            groups[x]['values']=value
            groups[x]['senseids']=[]
            x+=1
        log.info('Groups Done; Checking guids against groups.')
        for senseid in output.keys():
            for group in groups:
                if str(output[senseid]) == str(groups[group]['values']):
                    groups[group]['senseids']+=[senseid] #maybe don't need list here..…
                else:
                    pass
        """Add the guid information to the groups!!"""
        r = open(self.tonereportfile, "w", encoding='utf-8')
        title=_("Tone Report")
        self.runwindow.title(title)
        self.runwindow.scroll=ScrollingFrame(self.runwindow.frame)
        window=self.runwindow.scroll.content
        window.row=0
        xlpr=self.xlpstart(reporttype='Tone')
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
        for group in groups:
            groupname=self.ps+'_'+self.profile+'_'+str(group)
            text=_('\nGroup {}'.format(str(groupname)))
            s1=xlp.Section(xlpr,title=text)
            output(window,r,text)
            l=list()
            # print(groups[group]['values'])
            for x in groups[group]['values']:
                """This shouldn't crash if a word is lacking a value for a
                location. Just don't include that location in the group
                definition."""
                if (('values' in groups[group]) and (x in groups[group]['values'])
                    and (groups[group]['values'][x] !=[])):
                    log.debug('x: {}; values: {}'.format(x,str(groups[group]['values'][x])))
                    l.append(x+': '+str(groups[group]['values'][x][0]))
            text=_('Values by frame: {}'.format('\t'.join(l)))
            p1=xlp.Paragraph(s1,text)
            output(window,r,text)
            for senseid in groups[group]['senseids']:
                framed=self.getframeddata(senseid,noframe=True,
                                                notonegroup=True)
                text=framed['formatted']
                examples=self.db.get('example',senseid=senseid)
                log.log(2,"{} examples found: {}".format(len(examples),
                                                                    examples))
                if examples != []:
                    id=self.idXLP(framed)+'_examples'
                    log.log(2,"Using id {}".format(id))
                    e1=xlp.Example(s1,id)
                    for example in examples:
                        """These should already be framed!"""
                        framed=self.getframeddata(example,noframe=True)
                        self.framedtoXLP(framed,parent=e1,listword=True)
                # for form in self.db.citationorlexeme(senseid=senseid):
                #     for gloss in self.db.glossordefn(senseid=senseid,
                #                                     lang=self.glosslang):
                #         for gloss2 in self.db.glossordefn(senseid=senseid,
                #                                     lang=self.glosslang2):
                #             text='\t'+'\t'.join((form,"‘"+gloss+"’",
                #                                         "‘"+gloss2+"’"))
                output(window,r,text)
                self.db.addtoneUF(senseid,groupname,analang=self.analang)
        self.runwindow.ww.close()
        xlpr.close()
        text=("Finished in "+str(time.time() - start_time)+" seconds.")
        output(window,r,text)
        text=_("(Report is also available at ("+self.tonereportfile+")")
        output(window,r,text)
        r.close()
    def xlpstart(self,reporttype='adhoc'):
        if reporttype == 'Tone':
            reporttype=''.join([str(self.ps),'-',
                            str(self.profile),' ',
                            reporttype])
        elif reporttype != 'Basic': #If it is, we don't want these in the title.
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
    def basicreport(self):
        """We iterate across these values in this script, so we save current
        values here, and restore them at the end."""
        typeori=self.type
        psori=self.ps
        profileori=self.profile
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
                                            # ,'_',self.type,'_',str(pss)
                                            ,'.BasicReport.txt'])
        xlpr=self.xlpstart(reporttype='Basic')
        si=xlp.Section(xlpr,"Introduction")
        p=xlp.Paragraph(si,instr)
        sys.stdout = open(self.basicreportfile, "w", encoding='utf-8')
        print(instr)
        log.info(instr)
        self.frame.wait() #non-widget parent deiconifies no window...
        self.basicreported={}
        self.printprofilesbyps()
        self.makecountssorted() #This populates self.profilecounts
        self.printcountssorted()
        # num=1
        # num='ALL'
        num=5
        log.debug('self.topps(num):       {}'.format(self.topps(num)))
        log.debug('self.topprofiles(num): {}'.format(self.topprofiles(num)))
        # profilestodo={'Verb':['CVC']}
        profilestodo=self.topprofiles(num)
        t=_("This report covers the following top {} syllable profiles:"
            " {}. This is of course configurable, but I assume you don't want "
            "everything.".format(num,profilestodo))
        log.info(t)
        print(t)
        p=xlp.Paragraph(si,t)
        for self.ps in profilestodo: #keys are ps
            t=_("{} data".format(self.ps))
            log.info(t)
            print(t)
            s1=xlp.Section(xlpr,t)
            t=_("This section covers the following top {} syllable profiles "
                "which are found in {}s: {}".format(num,self.ps,
                                                    profilestodo[self.ps]))
            p=xlp.Paragraph(s1,t)
            log.info(t)
            print(t)
            for self.profile in profilestodo[self.ps]:
                t=_("{} {}s".format(self.profile,self.ps))
                s2=xlp.Section(s1,t,level=2)
                print(t)
                log.info(t)
                for self.type in self.s[self.analang]: # was ['V','C']:
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
        xlpr.close()
        sys.stdout.close()
        sys.stdout=sys.__stdout__ #In case we want to not crash afterwards...:-)
        self.frame.ww.close()
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
class Entry(lift.Entry):
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
            return #don't make another one...
        self.ww=Wait(self)
    def waitdone(self):
        pass
    def __init__(self, parent,
                backcmd=False, exit=True,
                title="No Title Yet!", choice=None,
                *args, **kwargs):
        self.parent=parent
        inherit(self)
        # _=self._
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
                                background=self.theme['background']
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
    def __init__(self, parent, **kwargs):
        self.parent = parent
        inherit(self)
        # _=self._
        """tkinter.Frame thingies below this"""
        super(Frame, self).__init__(parent,**kwargs)
        self['background']=parent['background']
        """Hang on to these for labels and buttons:"""
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
        # print("Configuring interior")
        # update the scrollbars to match the size of the inner frame
        size = (self.content.winfo_reqwidth(), self.content.winfo_reqheight())
        self.canvas.config(scrollregion="0 0 %s %s" % size)
        """This makes sure the canvas is as large as what you put on it"""
        if self.content.winfo_reqwidth() != self.canvas.winfo_width():
            # update the canvas's width to fit the inner frame
            self.canvas.config(width=self.content.winfo_reqwidth())
        self.windowsize()
    def windowsize(self):
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
        contentrw=self.content.winfo_reqwidth()
        contentrh=self.content.winfo_reqheight()
        for child in self.content.winfo_children():
            contentrw=max(contentrw,child.winfo_reqwidth())
            log.log(2,"{} ({})".format(child.winfo_reqwidth(),child))
        log.log(2,contentrw)
        log.log(2,self.parent.winfo_children())
        log.log(2,'self.winfo_width(): {}; contentrw: {}; self.maxwidth: {}'
                    ''.format(self.winfo_width(),contentrw,self.maxwidth))
        """If the current scrolling frame dimensions are smaller than the
        scrolling content, or else pushing the window off the screen, then make
        the scrolling window the smaller of
            -the scrolling content or
            -the max dimensions, from above."""
        # if self.winfo_width() < contentrw:
        #      self.config(width=contentrw)
        # if self.winfo_width() > self.maxwidth:
        #     self.config(width=self.maxwidth)
        if self.winfo_width() < contentrw:
            self.config(width=contentrw)
        if self.winfo_width() > self.maxwidth:
            self.config(width=self.maxwidth)
        # if self.winfo_height() < contentrh:
        #     self.config(height=contentrh)
        # if self.winfo_height() > self.maxheight:
        #     self.config(height=self.maxheight)
        if ((self.winfo_height() < contentrh)
                or (self.winfo_height() > self.maxheight)):
            self.config(height=min(self.maxheight,contentrh))
    def _configure_canvas(self, event):
        if self.content.winfo_reqwidth() != self.canvas.winfo_width():
            # update the inner frame's width to fill the canvas
            self.canvas.itemconfigure(self.content_id,
                                        width=self.canvas.winfo_width())
        self.windowsize()
    def __init__(self,parent):
        """Make this a Frame, with all the inheritances, I need"""
        self.parent=parent
        inherit(self)
        super(ScrollingFrame, self).__init__(parent)
        """Not sure if I want these... rather not hardcode."""
        log.debug(self.parent.winfo_children())
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        """With or without the following, it still scrolls through..."""
        self.grid_propagate(0) #make it not shrink to nothing

        """We might want horizonal bars some day? (also below)"""
        # xscrollbar = tkinter.Scrollbar(self, orient=tkinter.HORIZONTAL)
        # xscrollbar.grid(row=1, column=0, sticky=tkinter.E+tkinter.W)
        yscrollbar = tkinter.Scrollbar(self)
        yscrollbar.grid(row=0, column=1, sticky=tkinter.N+tkinter.S)
        """Should decide some day which we want when..."""
        yscrollbar.config(width=50) #make the scrollbars big!
        yscrollbar.config(width=0) #make the scrollbars invisible (use wheel)
        yscrollbar.config(width=15) #make the scrollbars useable...
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
        self.canvas.config(scrollregion=self.canvas.bbox("all"))
        """Make all this show up, and take up all the space in parent"""
        self.grid(row=0, column=0,sticky='nw')
        self.canvas.grid(row=0, column=0,sticky='nsew')
        # self.content.grid(row=0, column=0,sticky='nw')
        """We might want horizonal bars some day? (also above)"""
        # xscrollbar.config(command=self.canvas.xview)
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
class Menu(tkinter.Menu):
    def __init__(self,parent,**kwargs):
        super().__init__(parent,**kwargs)
        self.parent=parent
        inherit(self)
        self['font']=self.fonts['default']
        self['activebackground']=self.theme['activebackground']
        self['background']=self.theme['background']
class MainApplication(Frame):
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
        """Language stuff"""
        languagemenu = Menu(changemenu, tearoff=0)
        """Maybe this should be implied from first gloss language?"""
        # languagemenu.add_command(label=_("Interface language"),
        #                 command=lambda x=check:Check.getanalang(x))
        languagemenu.add_command(label=_("Interface/computer language"),
                        command=lambda x=check:Check.getinterfacelang(x))
        languagemenu.add_command(label=_("Analysis language"),
                        command=lambda x=check:Check.getanalang(x))
        languagemenu.add_command(label=_("Gloss language"),
                        command=lambda x=check:Check.getglosslang(x))
        languagemenu.add_command(label=_("Another gloss language"),
                        command=lambda x=check:Check.getglosslang2(x))
        changemenu.add_cascade(label=_("Languages"), menu=languagemenu)
        menubar.add_cascade(label=_("Change"), menu=changemenu)
        """Word/data choice stuff"""
        filtermenu = Menu(menubar, tearoff=0)
        filtermenu.add_command(label=_("Part of speech"),
                        command=lambda x=check:Check.getps(x))
        filtermenu.add_command(label=_("Syllable profile"),
                        command=lambda x=check:Check.getprofile(x))
        changemenu.add_cascade(label=_("Words"), menu=filtermenu)
        """What to check stuff"""
        checkmenu = Menu(menubar, tearoff=0)
        checkmenu.add_command(label=_("Sound type (Consonant, Vowel, or Tone)"),
                        command=lambda x=check:Check.gettype(x))
        if (check.ps is not None and check.profile is not None and
                                            check.type is not None):
            if check.type == 'T':
                checkmenutitle=_("Tone Frame")
            else:
                checkmenutitle=_("Location in word")
            checkmenu.add_command(label=checkmenutitle,
                        command=lambda x=check:Check.getcheck(x))
        if check.type != 'T' and check.name is not None:
            checkmenu.add_command(label=_("Segment(s) to check"),
                        command=lambda x=check:Check.getsubcheck(x))
            # checkmenu.add_command(label=_("Other report"),
            #             command=lambda x=check:Check.runcheck(x))
        changemenu.add_cascade(label=_("Options"), menu=checkmenu)
        """Do"""
        domenu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label=_("Do"), menu=domenu)
        reportmenu = Menu(menubar, tearoff=0)
        reportmenu.add_command(label=_("Tone report"),
                        command=lambda x=check:Check.tonegroupreport(x))
        reportmenu.add_command(label=_("Basic CV report (to file)"),
                        command=lambda x=check:Check.basicreport(x))
        domenu.add_cascade(label=_("Reports"), menu=reportmenu)
        recordmenu = Menu(menubar, tearoff=0)
        recordmenu.add_command(label=_("Sound Card Settings"),
                        command=lambda x=check:Check.soundcheck(x))
        recordmenu.add_command(label=_("Record tone group examples"),
                        command=lambda x=check:Check.showtonegroupexs(x))
        recordmenu.add_command(label=_("Record dictionary words, largest group first"),
                        command=lambda x=check:Check.showentryformstorecord(x,justone=False))
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
        # self.photo.thumbnail(50,50)
        f=ScrollingFrame(window.frame)
        f.grid(row=2,column=0,sticky='we')
        Label(f.content, image=self.photo['small'],text='',
                        bg=self.theme['background']
                        ).grid(row=0,column=0,sticky='we')
        l=Label(f.content, text=text, pady=50, padx=50,
                wraplength=int(self.winfo_screenwidth()/2)
                ).grid(row=1,column=0,sticky='we')
    def setmasterconfig(self,program):
        self.parent.debug=True #This puts out lots of console info...
        self.parent.debug=False #keep default here
        """Configure variables for the root window (master)"""
        for rc in [0,2]:
            self.parent.grid_rowconfigure(rc, weight=3)
            self.parent.grid_columnconfigure(rc, weight=3)
        setthemes(self.parent)
        theme='tkinterdefaults'
        theme='evenlighterpink'
        theme='purple'
        pot=list(self.parent.themes.keys())+(['greygreen']*
                                                (99*len(self.parent.themes)-1))
        self.parent.themename='highcontrast' #for low light environments
        self.parent.themename=pot[randint(0, len(pot))-1] #mostly 'greygreen'
        if platform.uname().node == 'karlap' and program['production'] is not True:
            self.parent.themename='Kim' #for my development
        """These versions might be necessary later, but with another module"""
        if self.parent.themename not in self.parent.themes:
            print("Sorry, that theme doesn't seem to be set up. Pick from "
            "these options:",self.parent.themes.keys())
            exit()
        self.parent.theme=self.parent.themes[self.parent.themename]
        self.parent['background']=self.parent.theme['background']
        """Set program icon(s) (First should be transparent!)"""
        imgurl=file.fullpathname('images/AZT stacks6.png')
        self.parent.photo={}
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
        imgurl=file.fullpathname('images/Verify List.png')
        self.parent.photo['verifyT'] = tkinter.PhotoImage(file = imgurl)
        imgurl=file.fullpathname('images/Sort List.png')
        self.parent.photo['sortT'] = tkinter.PhotoImage(file = imgurl)
        imgurl=file.fullpathname('images/Join List.png')
        self.parent.photo['joinT'] = tkinter.PhotoImage(file = imgurl)
        imgurl=file.fullpathname(
            '/usr/share/icons/gnome/24x24/devices/audio-input-microphone.png')
        # imgurl=file.fullpathname('images/Microphone card_sm.png')
        # imgurl=file.fullpathname('images/Microphone alone.png')
        imgurl=file.fullpathname('images/Microphone alone_sm.png')
        self.parent.photo['record'] = tkinter.PhotoImage(file = imgurl)
        imgurl=file.fullpathname('images/Change Circle_sm.png')
        self.parent.photo['change'] = tkinter.PhotoImage(file = imgurl)
        setfonts(self.parent)
        """allow for exit button (~200px)"""
        self.parent.wraplength=self.parent.winfo_screenwidth()-300
        file.getinterfacelang(self.parent)
        if self.parent.interfacelang == None:
            self.parent.interfacelang='fr' #default for now (just for first use).
        self.parent.program=program
        # self.setinterfacelang()
        self.parent._= setinterfacelang(self.parent.interfacelang)
    # def setinterfacelang(self):
    #     """Attention: this just calls the global function with the class
    #     variable as a parameter."""
    #     print(self.parent.interfacelang)
    #     setinterfacelang(self.parent.interfacelang)
    #     # if self.interfacelang == 'en':
    #     #     # interfacelang(lang=self.interfacelang)
    #     #     _ = gettext.gettext #for untranslated American English
    #     #     print(_("Translated!"))
    #     # else:
    #     #     interfacelang(lang=self.interfacelang)
    #     # file.writeinterfacelangtofile(self.interfacelang)
    # def setinterfacelangwrapper(self,choice,window):
    #         """This can't use Check.set, because checkcheck and attribute aren't
    #         in the same class"""
    #         # self.parent.interfacelang=choice
    #         # self.
    #         setinterfacelang(choice)
    #         window.destroy()
    #         self.check.checkcheck()
    # def getinterfacelang(self):
    #         print("Asking for interface language...")
    #         window=Window(self.frame, title=_('Select Interface Language'))
    #         Label(window.frame, text=_('What language do you want this program '
    #                                 'to address you in?')
    #                 ).grid(column=0, row=0)
    #         # pss=self.interfacelangs
    #         # print(pss)
    #         buttonFrame1=ButtonFrame(window.frame,
    #                                 self.parent.interfacelangs,self.setinterfacelangwrapper,
    #                                 window
    #                                 )
    #         buttonFrame1.grid(column=0, row=1)
    def __init__(self,parent,program):
        start_time=time.time() #this enables boot time evaluation
        # print(time.time()-start_time) # with this
        self.parent=parent
        self.setmasterconfig(program)
        inherit(self) # do this after setting config.
        # _=self._
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
        title=_("{name} Dictionary and Orthography Checker").format(name=self.program['name'])
        if self.master.themename != 'greygreen':
            print(f"Using theme '{self.master.themename}'.")
            title+=_(' ('+self.master.themename+')')
        parent.title(title)
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
        # self.maxheight=self.parent.winfo_screenheight()-self.otherrowheight
        self.config(wraplength=self.maxwidth)
        log.debug('self.maxwidth (Label): {}'.format(self.maxwidth))
    def __init__(self, parent, text, column=0, row=1, **kwargs):
        """These have non-None defaults"""
        if 'font' not in kwargs:
            kwargs['font']=parent.fonts['default']
        if 'wraplength' not in kwargs:
            kwargs['wraplength']=parent.wraplength
        self.theme=parent.theme
        self.parent=parent
        # print(kwargs.keys())
        # if 'photo' in kwargs:
        #     del kwargs['photo']
        # print(kwargs.keys())
        tkinter.Label.__init__(self, parent, text=nfc(text), **kwargs)
        self['background']=self.theme['background']
class EntryField(tkinter.Entry):
    def __init__(self, parent, **kwargs):
        self.parent=parent
        inherit(self)
        # self.theme=parent.theme
        if 'font' not in kwargs:
            kwargs['font']=self.fonts['default']
        super().__init__(parent,**kwargs)
        self['background']=self.theme['offwhite'] #because this is for entry...
class RadioButton(tkinter.Radiobutton):
    def __init__(self, parent, column=0, row=0, sticky='w', **kwargs):
        self.parent=parent
        inherit(self)
        # self.theme=parent.theme
        if 'font' not in kwargs:
            kwargs['font']=self.fonts['default']
        # self['background']=self.theme['background']
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
            # print("Making command in button class")
            # print('Button class',window,choice)
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
        # print("I'm opening the file to save the recording in now")
        file.remove(self.filenameURL) #don't do this until recording new file.
        self.wf = wave.open(self.filenameURL, 'wb')
        self.wf.setnchannels(self.channels)
        self.wf.setsampwidth(self.pa.get_sample_size(self.sample_format))
        self.wf.setframerate(self.fs)
    def fileclose(self):
        # print("I'm writing and closing the recording file now")
        while self.stream.is_active():
            time.sleep(0.1)
        if hasattr(self,'fulldata'):
            self.wf.writeframes(self.fulldata)
        else:
            log.debug("Nothing recorded!")
            # print(self.wf._nchannels)
        self.wf.close()
        if self.test is not True:
            self.db.addmediafields(self.node,self.filename,self.audiolang)
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
    def function(self):
        pass
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
        if self.test==True:
            self.filename=self.filenameURL=f'test_{check.fs}_{check.sample_format}.wav'
        else:
            if form==None:
                form=node.find(f"form[@lang='{check.analang}']/text").text
            wavfilename=''
            args=[check.ps, id, self.node.tag, form, gloss] #check.profile, <=Changes!
            for arg in args:
                wavfilename+=arg
                if args.index(arg) < len(args):
                    wavfilename+='_'
            self.filename = re.sub('[\. /?]+','_',str(wavfilename))+'.wav'
            self.filenameURL=str(file.getdiredurl(check.audiodir,self.filename))
            # self.filename=str('audio/'+filename)
            if ((id==None) or (node==None) or (form==None)
                or (gloss==None)):
                print("Sorry, unless testing we need all these "
                        "arguments; exiting.")
        super(RecordButtonFrame, self).__init__(parent, **kwargs)
        """These need to happen after the frame is created, as they
        might cause the init to stop."""
        if ((check.fs == None) or (check.sample_format == None)
                or (check.audio_card_index == None)):
            text=_("Sorry, you need to set the fs, sample_rate, and sound card!"
                    "\n(Change Stuff|Recording|Sound Card Settings)"
                    "\nSet these, and try again, and "
                    "\na record button will be here.")
            print(text)
            Label(self,text=text).grid(row=0,column=0)
            # check.soundcheck()
            return
        else:
            self.fs=check.fs
            self.sample_format=check.sample_format
            self.audio_card_index=check.audio_card_index
        self.makebuttons()
class ButtonFrame(Frame):
    def __init__(self,parent,
                    optionlist,command,
                    window=None,
                    # width='25',
                    **kwargs
                    ):
        self.parent=parent
        inherit(self)
        if self.debug == True:
            for kwarg in kwargs:
                print("ButtonFrame",kwarg,":",kwargs[kwarg])
        super().__init__(parent)
        gimmenull=False # When do I want a null option added to my lists? ever?
        self['background']=self.theme['background']
        i=0
        """Make sure list is in the proper format"""[0]
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
        elif type(optionlist[0]) is str:
            """when optionlist is a list of strings/codes"""
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
        if not 'name' in optionlist[0].keys(): #duplicate from code.
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
class ScrollingButtonFrame(ButtonFrame):
    """This needs to go inside another frame, for accurrate grid placement"""
    def __init__(self,parent,
                    optionlist,command,
                    window=None,
                    **kwargs
                    ):
        scroll=ScrollingFrame(parent)
        super().__init__(scroll.content,optionlist,command,window,**kwargs)
        self.grid(row=0,column=0)
class Wait(tkinter.Toplevel): #Window?
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
            if platform.uname().system == 'Linux':
                self.parent.withdraw()
            else:
                self.parent.iconify()
        except:
            log.debug("Not withdrawing parent.")
        super(Wait, self).__init__(bg=self.theme['background'])
        self.photo = parent.photo #need this before making the frame
        # self['background']=self.theme['background']
        self.outsideframe=Frame(self)
        title=(_("Please Wait! {name} Dictionary and Orthography Checker "
                        "in Process").format(name=self.program['name']))
        self.title(title)
        text=_("Please Wait...")
        self.l=Label(self, text=text,
                font=self.fonts['title'],anchor='c',padx=50,pady=50)
        self.l.grid(row=0,column=0,sticky='we')
        self.update_idletasks()
class Splash(Window):
    def __init__(self, parent):
        super(Splash, self).__init__(parent,exit=0)
        # _=self._
        # print(self.theme['background'])
        # print(self.theme['activebackground'])
        title=(_("{name} Dictionary and Orthography Checker").format(name=program[
                                                                    'name']))
        self.title(title)
        text=_("Your dictionary database is loading...\n\n"
                "{name} is a computer program that accelerates community"
                "-based language development by facilitating the sorting of a "
                "beginning dictionary by vowels, consonants and tone. "
                "(more in help:about)").format(name=program['name'])
        Label(self, text=title, pady=50,
                        font=self.fonts['title'],anchor='c',padx=25
                        ).grid(row=0,column=0,sticky='we')
        Label(self, image=self.photo['transparent'],text='',
                        bg=self.theme['background']
                        ).grid(row=1,column=0,sticky='we')
        l=Label(self, text=text, pady=50, padx=50,
                wraplength=int(self.winfo_screenwidth()/3)
                ).grid(row=2,column=0,sticky='we')
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
def setinterfacelang(lang):
    global aztdir
    global i18n
    global _
    """Attention: for this to work, _ has to be defined globally (here, not in
    a class or module.) So I'm getting the language setting in the class, then
    calling the module (imported globally) from here."""
    print('setinterfacelang:',lang)
    # if lang == 'en':
    #     # interfacelang(lang=self.interfacelang)
    #     # _ = gettext.gettext #for untranslated American English
    #     _ = lambda s: s
    #     print(_("Translated!"))
    # else:
    # interfacelang(lang=lang)
    print('aztdir',aztdir, 'lang:',lang)
    print(i18n[lang])
    print("Using interface", lang)
    i18n[lang].install()
    print(_("Translation seems to be working"))
    file.writeinterfacelangtofile(lang)
    # return _
def name(x):
    try:
        name=x.__name__ #If x is a function
        return name
    except:
        name=x.__class__.__name__ #If x is a class instance
        return "class."+name
def firstoflist(l,othersOK=False):
    """This takes a list composed of one item, and returns the item.
    with othersOK=True, it discards n=2+ items; with othersOK=False,
    it throws an error if there is more than one item in the list."""
    if type(l) is not list:
        return l
    if (l == None) or (l == []):
        return
    elif len(l) == 1 or (othersOK == True):
        return l[0]
    elif othersOK == False: #(i.e., with `len(list) != 1`)
        print('Sorry, something other than one list item found:',l,
                '\nDid you mean to use "othersOK=True"?')
def t(element):
    try:
        return element.text
    except:
        if element is None:
            return
        else:
            print('Apparently you tried to pull text out of a non element:',element)
def nonspace(x):
    """Return a space instead of None (for the GUI)"""
    if x is not None:
        return x
    else:
        return " "
def nn(x,oneperline=False):
    """Don't print "None" in the UI..."""
    if type(x) is list or type(x) is tuple:
        output=[]
        # print('List!')
        for y in x: #o='\t'.join(outputs)
            output+=[nonspace(y)]
        # return output
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
def setfonts(self):
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
                                                underline = True),
            'read':tkinter.font.Font(family="Andika SIL", size=big),
            'readbig':tkinter.font.Font(family="Andika SIL", size=bigger,
                                        weight='bold'),
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
                """Give me the tallest cell in this row"""
                if ((sib.row not in rowheight) or (sib.reqheight >
                                                        rowheight[sib.row])):
                    rowheight[sib.row]=sib.reqheight
            # else:
            #     print(wrows,'and',sib.rows,'share rows')
            if wcols & sib.cols == set(): #the empty set
                sib.reqwidth=sib.winfo_reqheight()
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
    log.debug("width: {}; self.maxheight: {}; self.maxwidth: {}".format(
                                self.parent.winfo_screenwidth(),
                                self.maxheight,
                                self.maxwidth))
    log.debug("cols: {}".format(colwidth))
    log.debug("rows: {}".format(rowheight))
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
    self.db.rmexfields(senseid=senseid,fieldtype='tone', #I might want to generalize this later...
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
        attrs=['fonts','theme','debug','wraplength','photo','program',
                '_','interfacelang']
    else:
        attrs=[attr]
    for attr in attrs:
        setattr(self,attr,getattr(self.parent,attr))
def nfc(x):
    return unicodedata.normalize('NFC', str(x))
    # print("self.fonts: {}, self.parent.fonts: {}".format(self.fonts,self.parent.fonts))
    # self.fonts=self.parent.fonts
    # self.theme=self.parent.theme
    # self.debug=self.parent.debug
    # self.wraplength=self.parent.wraplength
    # self.photo=self.parent.photo
    # # self.photowhite=self.parent.photowhite
    # self.program=self.parent.program
    # # self.photosmall=self.parent.photosmall
    # self._=self.parent._
    # self.interfacelang=self.parent.interfacelang
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
    # t = gettext.translation('dictionarychecker', aztdir)
    # _ = t.gettext
    i18n['en'] = gettext.translation('azt', transdir, languages=['en_US'])
    i18n['fr'] = gettext.translation('azt', transdir, languages=['fr_FR'])
    # i18n['fub'] = gettext.azttranslation('azt', transdir, languages=['fub'])
    # interfacelang('en')
    # # print(_('Tone'))
    # interfacelang('fr')
    try:
        main()
    except Exception as e:
        log.exception("Unexpected exception! %s",e)
        logwritelzma(log.filename)
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
