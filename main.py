#!/usr/bin/env python3
# coding=UTF-8
"""Consider making the above work for a venv"""
"""This file runs the actual GUI for lexical file manipulation/checking"""
program={'name':'A-Z+T',
        'tkinter':True, #for some day
        'production':False, #True for making screenshots (default theme)
        'testing':False, #normal error screens and logs
        'Demo':False, #will get set otherwise later if it is
        'version':'0.9.16', #This is a string...
        'testversionname':'testing', #always have some real test branch here
        'url':'https://github.com/kent-rasmussen/azt',
        'Email':'kent_rasmussen@sil.org'
        }
# program['testing']=True # eliminates Error screens and zipped logs, repos
exceptiononload=False
exceptiononloadingmymodule=False
import platform
program['hostname']=platform.uname().node
import py_modules #This tries importing, and installs on failure
import file
if file.getfile(__file__).parent.parent.stem == 'raspy': # if program['hostname'] == 'karlap':
    program['testing']=True #eliminates Error screens and zipped logs
    me=True
    loglevel='INFO'
    # program['testlift']='eng' #portion of filename
    program['testlift']='Demo_en' #portion of filename
    # program['testtask']='WordCollectnParse' #Will convert from string to class later
    # program['testtask']='SortV' #Will convert from string to class later
else:
    me=False
    program['production']=True #True for making screenshots (default theme)
    program['testing']=False #True eliminates Error screens and zipped logs
    loglevel='INFO'
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
from utilities import *
import logsetup
log=logsetup.getlog(__name__) #not ever a module
logsetup.setlevel(loglevel)
"""My modules, which should log as above"""
import lift
import parser
import openclipart
# import profiles #confirm obsolescence and remove!
import setdefaults
import xlp
import urls
import htmlfns
import executables
import export
import langtags
import alphabet_chart
program['languages']=langtags.Languages()
try:
    import sound
    import transcriber
    import sound_ui
    program['nosound']=False
except:
    program['nosound']=True
    log.error("Problem importing Sound/pyaudio. Is it installed? {}".format(e))
    exceptiononload=True
"""Other people's stuff"""
try:
    from packaging import version
except Exception as e:
    log.error("Problem importing packaging.version; installed? {}".format(e))
    exceptiononload=True
import datetime
try:
    # Python 3.11+
    program['start_time'] = datetime.datetime.now(datetime.UTC)
except AttributeError as e:
    # Python <=3.11
    program['start_time'] = datetime.datetime.utcnow()
import threading
import multiprocessing
import itertools
import importlib.util
import collections
from random import randint
if program['tkinter']:
    import tkinter #as gui
    import tkinter.font
    import tkinter.scrolledtext
    if not program['testing']:
        import tkintermod
        tkinter.CallWrapper = tkintermod.TkErrorCatcher
    import ui_tkinter as ui
"""else:
    import kivy
"""
import time
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

class HasMenus():
    def helpnewinterface(self):
        title=_("{azt} Dictionary and Orthography Checker") \
                .format(azt=program['name'])
        window=ui.Window(self, title=title)
        text=_("{name} has a new interface, starting mid January 2022. You "
                "should still be able to do everything you did before, though "
                "you will probably get to each function a bit differently "
                "—hopefully more intuitively."
                "\nTasks are organized into Data Collection and Analysis, "
                "and you can switch between them with the button in the upper "
                "right of the main {name} window."
                "\nEither window allows you to run reports."
                "").format(name=program['name'])
        url='{}/TASKS.md'.format(program['docsurl'])
        webtext=_("For more information on {name} tasks, please check out the "
                "documentation at {url} ").format(name=program['name'],url=url)
        ui.Label(window.frame, image=self.frame.theme.photo['icon'],
                text=title, font='title',compound='bottom',
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
        title=(_("{azt} Dictionary and Orthography Checker").format(azt=program['name']))
        window=ui.Window(self, title=title)
        version=program['version']
        ui.Label(window.frame,
                text=_("version: {version}").format(version=version),
                anchor='c',padx=50,
                row=1,column=0,sticky='we'
                        )
        versiondate=_("updated to {date} ({relative_date})").format(
                        date=program['repo'].lastcommitdate(),
                        relative_date=program['repo'].lastcommitdaterelative())
        ui.Label(window.frame,
                text=versiondate,
                anchor='c',padx=50,
                row=2,column=0,sticky='we'
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
        mailtext=_("or write me at {email}.").format(email=program['Email'])
        ui.Label(window.frame, text=title,
                font='title',anchor='c',padx=50,
                row=0,column=0,sticky='we')
        f=ui.ScrollingFrame(window.frame,
                            row=3,column=0,sticky='we')
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
        ui.ToolTip(webl, _("See {azt} online").format(azt=program['name']))
        murl='mailto:{}?subject= {} question'.format(program['Email'],
                                                    program['name'])
        maill.bind("<Button-1>", lambda e: openweburl(murl))
        ui.ToolTip(maill, _("Send me an Email (from your mail client)"))
    def reverttomainazt(self,event=None):
        #This doesn't care which (test) version one is on
        r=program['repo'].reverttomain()
        log.info("reverttomainazt: {}".format(r))
        self.updateazt()
        if r:
            program['taskchooser'].restart()
    def trytestazt(self,event=None):
        #This only goes to the test version at the top of this file
        r=program['repo'].testversion()
        log.info("trytestazt: {}".format(r))
        self.updateazt()
        if r:
            program['taskchooser'].restart()
    def _removemenus(self,event=None):
        # log.info(_("Hiding menus? (vars={vars}, self:{self}, event={event})")
        #             .format(vars=vars(self), self=self, event=event))
        if hasattr(self,'menubar'):
            self.menubar.destroy()
            # log.info(_("now {vars}").format(vars=vars(self)))
            self.menu=False
            # log.info(_("now {vars}").format(vars=vars(self)))
            self.setcontext()
        log.info(_("done with _removemenus"))
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
    def newfile_page(self):
        self._new_w=ui.Window(program['root'],title=_("Start New LIFT Database"))
        defaults={'pady':20,'column':0,'sticky':'w','gridwait':True}
        self.title_frame=ui.Frame(self._new_w.frame, row=0, **defaults)
        self.code_frame=ui.Frame(self._new_w.frame, row=1, **defaults)
        self.code_label=ui.Label(self.code_frame, text=_('code: '),
                                font='readbig', row=0, **defaults)
        self.use_code_button=ui.Button(self.code_frame,
                                        text='<= '+_("Use this code"),
                                        command=self._new_w.destroy,
                                        font='readbig', padx=20,
                                        state='disabled',
                                        **{**defaults,'column':1}
                                    )
        self.entryframe=ui.Frame(self._new_w.frame, row=2, **defaults)
        log.info("newfile_page done")
    def set_up_variables(self):
        self.analang_entry=ui.StringVar()
        self.variant_entry=ui.StringVar()
        self.territory_entry=ui.StringVar()
    def startnewfile(self):
        program['root'].unbind_all('<Button-1>')
        program['root'].unbind_all('<Return>')
        self.newfile_page()
        title=_("What is your language code?")
        text=_("Type the name of your language in the field, then find and select the full name below.")
        self.no_country_text=_("Multiple/all territories")
        t=ui.Label(self.title_frame, text=title, font='title', column=0, row=0)
        l=ui.Label(self.title_frame, text=text, column=0, row=1)
        l.wrap()
        self.set_up_variables()
        self.title_frame.grid()
        self.make_lang_entry()
        self._new_w.mainwindow=False
        t.wait_window(self._new_w)
        if not self._new_w.exitFlag.istrue(): #true w/ X or Exit, not "Use..."
            return self.analang_code_complete()
    def make_lang_entry(self):
        """This should be pulled into it's own class, so we can source it here and in sound_ui the same way."""
        self.trace_analang_entry()
        self.entry_field=ui.EntryField(self.entryframe,
                                        text=self.analang_entry,
                                        font='normal',
                                        width=10,
                                        row=1,
                                        column=0,
                                        sticky='w')
        self.list_of_possibles=ui.ListBox(self.entryframe,
                                        command=self.lang_name_selected,
                                        font='default',
                                        height=1,
                                        width=10,
                                        row=2,
                                        column=0,
                                        gridwait=True,
                                        sticky='w')
        self.entryframe.grid()
        self.entry_field.grid()
        self.entry_field.focus_set()
    def trace_analang_entry(self):
        # log.info("trace_analang_entry")
        self.analang_entry.trace=self.analang_entry.trace_add('write',
                                                            self.show_possibles)
        # log.info("trace_analang_entry OK")
    def untrace_analang_entry(self):
        # log.info("untrace_analang_entry")
        try:
            self.analang_entry.trace_remove('write',self.analang_entry.trace)
            # log.info("untrace_analang_entry OK")
        except:
            pass
    def show_possibles(self,*args):
        value=self.analang_entry.get()
        log.info(f"Updating Possibles for ‘{value}’")
        self.entry_field.configure(width=max(10,len(value)))
        if hasattr(self,'subtags_frame') and self.subtags_frame.winfo_exists():
            self.subtags_frame.destroy()
        if not value:
            self.list_of_possibles.grid_remove()
            self.iso=''
            self.update_code() #remove code and button
            return
        self.list_of_possibles.delete(0, "end")
        self.list_of_possibles.grid()
        self.l_codes=program['languages'].get_codes(value)
        log.info(f"found these codes for {value}: {self.l_codes}")
        self.l_codes=list(self.l_codes)[:20] #preserve order from here on out
        if not self.list_of_possibles.winfo_viewable():
            self.list_of_possibles.dogrid()
        if not self.l_codes:
            # log.info("no l_codes")
            self.options=[f"Error: ‘{value}’ not found"]
            # log.info("get OK")
            self.list_of_possibles.config(state='disabled')
        else:
            # log.info("yes l_codes")
            objs=[program['languages'].get_obj(i) for i in self.l_codes]
            # log.info("get_obj OK")
            self.options=[i.full_display() for i in objs]
            # log.info("options OK")
            self.list_of_possibles.config(state='normal')
        # log.info(f"self.options: {self.options}")
        for i in self.options:
            self.list_of_possibles.insert("end", i)
        max_value_len=max([len(self.list_of_possibles.get(i))
                    for i in range(len(self.list_of_possibles.get(0,'end')))])
        self.list_of_possibles.configure(width=max(10,max_value_len),
                                        height=min(4,len(self.options)))
        log.info(f"Done updating possibles for ‘{value}’")
    def lang_name_selected(self,*args):
        log.info("lang_name_selected")
        if not self.list_of_possibles.curselection():
            return
        this_index=self.list_of_possibles.curselection()[0]
        self.iso=self.l_codes[this_index]
        self.update_code()
        log.info(f"iso: {self.iso}")
        value=self.list_of_possibles.get(this_index)
        self.untrace_analang_entry() #don't redo possibles here
        self.analang_entry.set(value)
        self.trace_analang_entry()
        self.entry_field.configure(width=max(10,len(value)))
        self.list_of_possibles.grid_remove()
        self.show_subtag_frames()
    def update_code(self,*args):
        log.info(f"Updating code {self.iso=}")
        if not self.iso:
            self.code_label.grid_remove()
            self.use_code_button.grid_remove()
            self.check_tag_validity()
            self._new_w.update_idletasks()
            return
        self.code=self.iso
        if self.territory_entry.get():
            self.code+='-'+self.territory_entry.get()
        if self.variant_entry.get():
            self.code+='-x-'+self.variant_entry.get().lower() #in case caps
        self.code_label['text']=f"code: {self.code}"
        self.code_label.grid()
        self.use_code_button.grid()
        self.check_tag_validity()
    def show_private_use(self,event=None):
        """The user needs to ask to see this field"""
        self.show_private_w.grid_remove()
        instructions=ui.Label(self.private_use_frame, r=0, c=0, colspan=2,
                                text=_("give two to eight (2-8) characters "
                                        "to identify your dialect"))
        prefix=ui.Label(self.private_use_frame, text='x-',
                                                r=1, c=0, sticky='e')
        self.entry_field_2=ui.EntryField(self.private_use_frame,
                                        textvariable=self.variant_entry,
                                        font='normal', width=10,
                                        row=1, column=1,
                                        sticky='w')
        self.variant_entry.trace_add('write', self.update_code)
        self.entry_field_2.focus_set()
    def territory_selected(self,*args):
        this_index=self.list_of_territories.curselection()[0]
        if this_index:
            name=self.list_of_territories.get(this_index)
            code=[k for k,v in program['languages'].region_codes_names.items()
                        if name == v].pop()
            self.territory_entry.set(code)
        else:
            self.territory_entry.set('')
        self.update_code()
    def show_subtag_frames(self):
        # log.info("show_subtag_frames")
        defaults={'pady':20,'padx':20,'sticky':'w','gridwait':True}
        self.subtags_frame=ui.Frame(self._new_w.frame, row=3, **defaults)
        self.private_use_frame=ui.Frame(self.subtags_frame, **defaults)
        self.territory_frame=ui.Frame(self.subtags_frame,
                                        column=1, **defaults)
        self.show_private_w=ui.Button(self.private_use_frame,
                            text=_("I'm working on a dialect of this language"),
                            command=self.show_private_use,
                            r=0,c=0
                        )
        self.subtags_frame.grid()
        self.private_use_frame.grid()
        lang_obj=program['languages'].get_obj(self.iso)
        if len(lang_obj.regions) > 1:
            self.territory_frame.grid()
            instructions=_("This language is spoken in multiple territories; "
                            "where are you working?")
            territory_instructions=ui.Label(self.territory_frame,
                                            text=instructions,
                                            row=0,
                                            column=0,
                                            # gridwait=True,
                                            sticky='w')
            max_len=max([len(i) for i in lang_obj.regions])
            options=[self.no_country_text]+list(lang_obj.regions)
            self.list_of_territories=ui.ListBox(self.territory_frame,
                                        command=self.territory_selected,
                                        optionlist=options,
                                        font='default',
                                        height=min(5,len(lang_obj.regions)+1),
                                        width=max_len,
                                        row=1,
                                        column=0,
                                        # gridwait=True,
                                        sticky='w')
        elif len(lang_obj.regions):
            self.territory_frame.destroy()
        else:
            self.territory_frame.destroy()
        self.use_code_button.grid()
    def check_tag_validity(self):
        log.info("check_tag_validity")
        for code in [langtags.tone_code,
                    langtags.phonetic_code,
                    langtags.audio_code]:
            if code in self.code:
                self.use_code_button.configure(state='disabled')
                self.use_code_button['text']=f"‘{code}’ invalid"
                return
        if langtags.tag_is_valid(self.code):
            # log.info("tag valid")
            self.use_code_button.configure(state='normal')
        else:
            # log.info(f"tag not valid {self.code=}")
            self.use_code_button.configure(state='disabled')
    def analang_code_complete(self):
        log.info("analang_code_complete")
        self.analang=self.code
        if not self.analang:
            return
        try:
            self.analang_obj=program['languages'].get_obj(self.analang)
        except langcodes.tag_parser.LanguageTagError:
            log.info(f"{self.analang_obj} didn't parse.")
        if not self.analang_obj.is_valid():
            log.error(f"It looks like your code ({self.analang}) isn't valid "
                        f"({self.analang_obj.full_display()})")
        if not langtags.tag_is_valid(self.analang):
            e=ErrorNotice(_("That doesn't look like an ethnologue code ({analang})")
                        .format(analang=self.analang),wait=True)
        dir=file.gethome()
        newfile=file.getnewlifturl(dir,self.analang)
        if not newfile:
            ErrorNotice(_("Problem creating file; does the directory "
                        "already exist?"),wait=True)
            return
        if file.exists(newfile):
            ErrorNotice(_("The file {newfile} already exists!").format(newfile=newfile),
                                                                wait=True)
            return
        self.newdirname=newfile.parent
        self.wait=ui.Wait(parent=program['root'],msg=_("Setting up new LIFT file now."))
        log.info("Beginning Copy of stock to new LIFT file.")
        self.cawldb=loadCAWL()
        self.stripcawldb()
        self.cawldb.analang=self.analang
        self.cawldb.getentries() #this needs analang
        self.cawldb.getsenses()
        self.fillcawldbimages()
        self.copytonewfile(newfile)
        self.wait.close()
        self.newfilelocation(newfile)
        log.info("analang_code_complete complete")
        return str(newfile)
    def clonefromUSB(self):
        def makenewrepo(repoclass,mediadir):
            repo=repoclass(mediadir)
            if (hasattr(repo,'files') #fails if no exe
                and repo.exists()): #tests for .code dir
                    log.info(_("Found {code} Repository! ({mediadir})").format(code=repo.code, mediadir=mediadir))
                    dirname=repo.dirname
                    # log.info("repo in {} directory".format(dirname))
                    newdirname=file.getfile(homedir).joinpath(dirname)
                    if newdirname.suffix == '.'+repo.code: #strip this on clone
                        newdirname=newdirname.with_suffix('')
                    if file.exists(newdirname):
                        # log.info("Exists!")
                        msg=_("The directory {newdirname} already exists, so I'm "
                                "not going to copy your data there."
                                "\nDo you already have your data on your "
                                "computer? \nIf so, click '{other}' on the next "
                                "screen.").format(newdirname=newdirname,other=self.other)
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
            ErrorNotice(_("I can't find your home directory ({homedir}); please "
                        "submit a bug report!").format(homedir=homedir))
        newrepo=None
        newrepo=makenewrepo(Git,mediadir)
        if not newrepo:
            log.info("trying with Mercurial")
            newrepo=makenewrepo(Mercurial,mediadir)
        if not newrepo: # if there, already exists
            log.error(_("Couldn't find a repository at {mediadir}").format(mediadir=mediadir))
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
                            "your new file. ({newfile})").format(newfile=newfile))
        else:
            msg=_("It looks like the repository was cloned, but "
                        "I can't find just one lift file."
                        "\nTell {azt} which file you want to "
                        "Analyze on the next page.").format(azt=program['name'])
            # log.info(msg)
            ErrorNotice(msg,wait=True)
    def findrepolift(self,repo):
        # log.info("Looking for just one LIFT file ({}).".format(repo.files))
        l=[i for i in repo.files if str(i).endswith('.lift')]
        if len(l) == 1:
            log.info("Found just one LIFT file: {}".format(l))
            return l[0]
        else:
            # I could, if this becomes a problem, return the shortest filename,
            # or on that contains the ISO code, but I think this is sane enough
            # for now —anyone with more than one *.lift file should know what
            # they're doing
            log.info(_("returned more or less than one lift file! ({list})")
                    .format(list=l))
    def fillcawldbimages(self,cawldb=None,newdirname=None,wait=None):
        log.info("Filling in empty image fields where possible")
        if not cawldb:
            cawldb=self.cawldb
        if not newdirname:
            newdirname=self.newdirname
        if not wait:
            wait=self.wait
        todo=cawldb.senses
        newimagedir=file.getimagesdir(newdirname)
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
                dir=file.fullpathname(sense.imgselectiondir)
                # log.info("Found CAWL sense without image field")
                if file.exists(dir):
                    urls=file.getfilesofdirectory(dir)
                    if urls:
                        filename=sense.imagename() #new file name
                        # log.info("Working with image filename {}".format(filename))
                        for u in urls:
                            if '__' in str(u) and '.png' in str(u): #best file
                                # log.info("Found best image {}; \ngoing to put "
                                #         "in {}".format(u,self.newdirname))
                                saveimagefile(u,filename, copyto=newimagedir)
                        if not file.exists(file.getdiredurl(newimagedir,
                                                                filename)):
                            #just take the first one
                            saveimagefile(urls[0],filename, copyto=newimagedir)
                        sense.illustrationvalue(filename)
                # log.info("Setting progress {}".format(todo.index(sense)*100/len(todo)))
                if wait:
                    wait.progress(todo.index(sense)*100/len(todo))
    def storedefaultsettings(self,basename):
        filename=basename.with_suffix('.CheckDefaults.ini')
        config=ConfigParser()
        config['default']={
                            'glosslangs':['fr'],
                            'buttoncolumns':2
                            }
        header=(_("# This transitional settings file was made on {date} on {node}").format(
                                                    date=now(),node=platform.uname().node)
                )
        header+=(_("\n# It should only be used to get a new demo started."))
        with open(filename, 'w', encoding='utf-8') as file:
            file.write(header+'\n\n')
            config.write(file)
        log.info(f"Stored config {dict(config['default'])} for next run.")
    def makeCAWLdemo(self):
        title=_("Make a Demo LIFT Database")
        w=ui.Window(program['root'],title=title)
        w.withdraw()
        w.mainwindow=False
        t=ui.Label(w.frame, text=title, font='title', row=0, column=0)
        inst=_("Which language would you like to study, in this demonstration "
                "of what {azt} can do?").format(azt=program['name'])
        t=ui.Label(w.frame, text=inst, row=1, column=0, columnspan=2)
        self.cawldb=loadCAWL()
        Settings.langnames(self,self.cawldb.glosslangs)
        opts=[(i,self.languagenames[i]) for i in self.cawldb.glosslangs]
        # log.info("Options: {}".format(opts))
        s=ui.ScrollingButtonFrame(w.frame,
                                    optionlist=opts,
                                    command=self.submitdemolang,
                                    window=w, sticky='',
                                    column=0, row=2)
        w.deiconify()
        w.wait_window(w)
        if not hasattr(self,'demolang') or not self.demolang:
            log.info("User exited without selecting a language.")
            return
        else:
            log.info("User selected a language: {}.".format(self.demolang))
        self.stripcawldb()
        self.wait=ui.Wait(parent=program['root'],
                        msg=_("Making Demo Database \n(will restart)"))
        homedir=file.gethome() #don't ask where to put it
        self.newdirname=file.getfile(homedir).joinpath('Demo_'+self.demolang)
        file.makedir(self.newdirname)
        newfilebasename=self.newdirname.joinpath('Demo_'+self.demolang)
        newfile=newfilebasename.with_suffix('.lift')
        if file.exists(newfile):
            self.wait.close()
            ErrorNotice(_("File {newfile} already exists! \nUse it?").format(newfile=newfile),
                        wait=True,
                        button=(_("Yes!"),lambda event,x=str(newfile):
                                self.setfilenameandcontinue(x,restart=True))
                        )
            return
        # else:
        #     log.info(f"{newfile=} doesn't exist already!")
        self.cawldb.analang=self.demolang
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
        self.storedefaultsettings(newfilebasename)
        return str(newfile)
    def stripcawldb(self):
        for n in (self.cawldb.nodes.findall('entry/lexical-unit')+
                    self.cawldb.nodes.findall('entry/citation')):
            for f in n.findall('form'):
                n.remove(f)
        log.info("Stripped stock LIFT file.")
    def submitdemolang(self,choice,window): #event=None):
        log.info(_("picked {choice}, from {glosslangs}").format(choice=choice, glosslangs=self.cawldb.glosslangs))
        if choice in self.cawldb.glosslangs:
            self.demolang=choice
            window.destroy()
    def copytonewfile(self,newfile):
        if 'Demo' in str(newfile):
            type=_("demo")
        else:
            type=_("empty")
        log.info(_("Trying to write {type} LIFT file to {newfile}").format(type=type, newfile=newfile))
        try:
            self.cawldb.write(str(newfile))
        except Exception as e:
            log.error("Exception: {}".format(e))
        log.info(_("Tried to write {type} LIFT file to {newfile}").format(type=type, newfile=newfile))
        if file.exists(newfile):
            log.info("Wrote {} LIFT file to {}".format(type,newfile))
    def newfilelocation(self,newfile):
        #Do users care about this?
        return #not for now
        msg=_("Your new LIFT file is at {newfile}."
                "\nIf you don't want it there, close {azt} and move the whole "
                "{folder} folder wherever you like."
                "\nThen open {azt} and tell it where you put the LIFT file."
                ).format(newfile=newfile,
                        folder=file.getfilenamedir(newfile),
                        azt=program['name'])
        # log.info(msg)
        ErrorNotice(msg,title=_("New LIFT file location"),wait=True)
    def setfilename(self, choice, window, event=None):
        log.info(f"Calling setfilename with {choice=} {window=} {event=}")
        self.withdraw()
        restart=False
        if choice == 'New':
            name=self.startnewfile()
        elif choice == 'Other':
            name=file.lift()
        elif choice == 'Clone':
            log.info("trying clone from USB")
            name=self.clonefromUSB()
            restart=True
        elif choice == 'Demo':
            log.info("Making a CAWL demo database")
            name=self.makeCAWLdemo()
            restart=True
        else:
            name=choice
        # log.info(f"{self.name if hasattr(self,'name') else "no self.name!"}")
        log.info(f"{name}")
        if name:
            self.setfilenameandcontinue(name,restart)
        elif not hasattr(self,'name') or not self.name: #If not either, trust that Demo is working
            self.deiconify() #let user pick again
    def setfilenameandcontinue(self,name,restart=False,event=None):
        log.info(_("Running setfilenameandcontinue with "
                    "name={name} and restart={restart}").format(name=name, restart=restart))
        self.name=self.filechooser.name=name
        file.writefilename(name)
        self.destroy()
        if (hasattr(program['taskchooser'],'splash') and
                    program['taskchooser'].splash.winfo_exists()):
            program['taskchooser'].splash.deiconify()
        if restart:
            sysrestart()
    def displayname(self,filename):
        """Ultimately, it would be nice to return some lift-internal name here"""
        log.info(f"working on {filename}")
        name=file.getfilenamefrompath(filename)
        if file.parentfrompath(filename)+'.lift' == name:
            return name
        else:
            return file.fileandparentfrompath(filename)
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
            optionlist+=[(f,self.displayname(f)) for f in filenamelist]
            self.other=_("Select another database on my computer") #use later
        else:
            self.other=_("Select a database on my computer") #use later
        optionlist+=[('Other',self.other)]
        optionlist+=[('Demo',_("Make a demo database to try out {azt}"
                                ).format(azt=program['name']))]
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
                text=text, font='title', compound='top',
                column=1, row=1, ipadx=20)
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
        log.info("getfilename returned {}".format(self.name))
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
        if self.name and 'Demo' in str(self.name):
            program['Demo']=True
            file.writefilename() #clear this to select next time
class FileParser(object):
    """This class parses the LIFT file, once we know which it is."""
    def loaddatabase(self,analang=None):
        try:
            #This program key will only be available after this finishes
            program['db']=lift.LiftXML(str(self.name),analang)
        except lift.BadParseError:
            text=_("{filename} doesn't look like a well formed lift file; please "
                    "try again.").format(filename=self.name)
            log.info("'lift_url.py' removed.")
            if program['root'].exitFlag.istrue():
                log.info(text)
                return
            else:
                ErrorNotice(text,title=_('LIFT parse error'),wait=True)
            file.writefilename() #just clear the default
            raise #Then force a quit and retry
        except Exception as e:
            text=_("There seems to be a (non-XML) problem loading your "
            "database ({filename}); I will remove it as default so you can open "
            "another").format(filename=self.name)
            log.error(text)
            ErrorNotice(text,title=_('LIFT non-parse error'),wait=True)
            file.writefilename()
            raise
    def dailybackup(self):
        if not file.exists(program['db'].backupfilename):
            program['db'].write(program['db'].backupfilename)
        else:
            print(_("Apparently we've run this before today; not backing "
            "up again."))
    def getwritingsystemsinfo(self):
        """This doesn't actually do anything yet, as we can't parse ldml."""
        program['db'].languagecodes=program['db'].analangs+program['db'].glosslangs
        program['db'].languagepaths=file.getlangnamepaths(self.name,
                                                    program['db'].languagecodes)
    def __init__(self,name,analang=None):
        super(FileParser, self).__init__()
        self.name=name
        # splash.progress(15)
        self.loaddatabase(analang)
        # splash.progress(25)
        if program['root'].exitFlag.istrue():
            return
        self.dailybackup()
        # splash.progress(35)
        # splash.progress(45)
        self.getwritingsystemsinfo()
class Menus(ui.Menu):
    """this is the overall menu set, from which each will be selected."""
    def command(self,parent,label,cmd):
        parent.add_command(label=label, command=cmd)
    def cascade(self,parent,label,newmenuname,index=False):
        setattr(self,newmenuname, ui.Menu(parent, tearoff=0))
        if index is not False:
            parent.insert_cascade(label=label,
                                    menu=getattr(self,newmenuname),
                                    index=index)
        else:
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
    def fillcawl(self):
        w=ui.Wait(program['root'],msg=_("Filling images..."))
        try:
            LiftChooser.fillcawldbimages(self, cawldb=program['db'], newdirname=program['db'].lift_home, wait=w)
        except Exception as e:
            log.error(f"Error filling images: {e}")
        w.close()
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
    def redoadvanced(self):
        log.info("Redoing the Advanced menu")
        title=_("Advanced")
        i=self.index(title)
        # log.info(f"Advanced is currently index {i}")
        # self.parent.withdraw()
        self.delete(_("Advanced"))
        # self.advancedmenu.destroy()
        self.advanced(index=i)
        self.parent.update_idletasks()
        # self.parent.deiconify()
    def advanced(self,index=False):
        self.cascade(self,_("Advanced"),'advancedmenu',index=index)
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
                (_("Fill CAWL Images"), self.fillcawl),
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
                self.parent.soundcheck),]
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
        # While this remains broken, leave off. Is it worth fixing?
        # options=[(_("Add/Modify Ad Hoc Sorting Group"),
        #                                         self.parent.addmodadhocsort),]
        options=[]
        if isinstance(self.parent,SortT):
            options.extend([(_("Add Tone frame"), self.parent.addframe)])
        group=program['status'].group()
        if not group:
            group=_("Select")
        options.extend([(_("Resort skipped data"), self.parent.tryNAgain),
                        (_("Reverify current group ({group})").format(group=group),
                                                        self.parent.reverify),
                        (_("Join Sort Groups"), self.parent.redo_join),
                        (_("Join Glyphs (Letters)"), self.parent.redo_joinglyphs)
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
                helpitems+=[(_("Set up {azt} source on USB").format(azt=program['name']),
                                program['repo'].clonetoUSB)]
            helpitems+=[(_("Update {azt}").format(azt=program['name']), updateazt)]
            if program['repo'].branch == 'main':
                helpitems+=[(_("Try {azt} test version").format(azt=program['name']),
                                self.parent.trytestazt)]
            else:
                helpitems+=[(_("Revert to {azt} main version").format(azt=program['name']),
                                self.parent.reverttomainazt)]
        helpitems+=[(_("What's with the New Interface?"),
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
    def newrow(self):
        self.irow+=1
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
    def proselabel(self,**kwargs):
        if not kwargs.get('parent'):
            parent=self.proseframe
            column=self.opts['labelcolumn']
            columnspan=self.opts['columnspan']
            ipadx=self.opts['labelxpad']
        else:
            parent=kwargs.get('parent')
            column=parent.ncolumns() #just do the next in this line
            columnspan=1
            ipadx=0
        text=kwargs.get('text',kwargs.get('label'))
        if not self.mainrelief:
            l=ui.Label(parent, text=text,font='report',anchor='w')
        else:
            l=ui.Button(parent,text=text,font='report',anchor='w',
                relief=self.mainrelief)
        l.grid(column=column, row=self.irow, columnspan=columnspan,
                ipadx=ipadx, sticky='w')
        if kwargs.get('cmd'):
            l.bind('<ButtonRelease-1>',kwargs.get('cmd'))
        if kwargs.get('tt'):
            ttl=ui.ToolTip(l,kwargs.get('tt'))
    def button(self,text,fn,**kwargs): #=opts['labelcolumn']
        """cmd overrides the standard button command system."""
        ttt=kwargs.pop('tttext',None)
        b=ui.Button(self.proseframe, choice=text, text=text, anchor='c',
                        cmd=fn, width=self.opts['width'],
                        column=0, row=self.irow,
                        columnspan=self.opts['columnspan'],
                        wraplength=int(program['root'].wraplength/4),
                        **kwargs)
        if ttt:
            tt=ui.ToolTip(b,ttt)
        return b
    """These functions point to program['taskchooser'] functions, betcause we don't
    know who this frame's parent is"""
    def makeproseframe(self):
        if hasattr(self,'proseframe'):
            self.proseframe.destroy()
        self.proseframe=ui.Frame(self,row=0,column=0,sticky='nw')
    def updateinterfacelang(self):
        self.labels['interfacelang']['text'].set(self.interfacelanglabel())
    def interfacelanglabel(self):
        # for l in program['taskchooser'].interfacelangs:
        #     if l['code']==interfacelang():
        #         interfacelanguagename=l['name']
        return (_("Using {lang}").format(lang=program['settings'].languagenames[interfacelang()]))
    def interfacelangline(self):
        self.labels['interfacelang']={
                        'text':ui.StringVar(value=self.interfacelanglabel()),
                        'columnplus':1,
                        'cmd':self.task.getinterfacelang,
                        'tt':_("change the interface language")}
        self.proselabel(**self.labels['interfacelang'])
    def updateanalang(self):
        self.labels['analangline']['text'].set(self.analanglabel())
    def analanglabel(self):
        analang=program['params'].analang()
        langname=program['settings'].languagenames[analang]
        return (_("Studying {lang}").format(lang=langname))
    def analangline(self):
        self.newrow()
        if program['params'].analang() not in program['settings'].languagenames:
            cmd=self.task.getanalangname
            tt=_("Set analysis language Name")
        else:
            cmd=self.task.getanalang
            tt=_("Change analysis language")
        self.labels['analangline']={
                                'text':ui.StringVar(value=self.analanglabel()),
                                'columnplus':1,
                                'cmd':cmd,
                                'tt':tt}
        self.proselabel(**self.labels['analangline'])
    def updateglosslangs(self):
        self.labels['glosslang']['text'].set(self.glosslanglabel())
        self.labels['glosslang2']['text'].set(self.glosslanglabel2())
    def glosslanglabel(self):
        lang=program['settings'].glosslangs.lang1()
        return (_("Meanings in {lang}").format(lang=program['settings'].languagenames[lang]))
    def glosslanglabel2(self):
        if len(program['settings'].glosslangs) >1:
            glosslang2=program['settings'].glosslangs.lang2()
            return (_("and {lang}").format(lang=program['settings'].languagenames[glosslang2]))
        else:
            return _("only")
    def glosslangline(self):
        self.newrow()
        line=ui.Frame(self.proseframe,row=self.irow,column=0,
                        columnspan=3,sticky='w') #3 cols is the width of frame
        self.labels['glosslang']={'text':ui.StringVar(value=self.glosslanglabel()),
                                'columnplus':1,
                                # 'rowplus':1,
                                'cmd':self.task.getglosslang,
                                'parent':line,
                                'tt':_("change this gloss language")
                                    if len(program['settings'].glosslangs) >1
                                    else _("change this glosslang")
                                    }
        self.proselabel(**self.labels['glosslang'])
        self.labels['glosslang2']={'text':ui.StringVar(value=self.glosslanglabel2()),
                                'columnplus':1,
                                'cmd':self.task.getglosslang2,
                                'parent':line,
                                'tt':_("add another gloss language")}
        self.proselabel(**self.labels['glosslang2'])
    def updatefields(self):
        for ps in [program['settings'].nominalps, program['settings'].verbalps]:
            if 'fields'+ps in self.labels:
                self.labels['fields'+ps]['text'].set(self.fieldslabel(ps))
    def fieldslabel(self,ps):
        if ps in program['settings'].secondformfield:
            field=program['settings'].secondformfield[ps]
        else:
            field='<unset>'
        return (_("Using second form field ‘{field}’ ({ps})").format(field=field, ps=ps))
    def fieldsline(self):
        # log.info("Starting fieldsline w/self {} ({})".format(self,type(self)))
        # log.info("Starting fieldsline w/task {} ({})".format(self.task,
        #                                                     type(self.task)))
        for ps in [program['settings'].nominalps, program['settings'].verbalps]:
            self.newrow()
            line=ui.Frame(self.proseframe,row=self.irow,column=0,
                            columnspan=3,sticky='w') #3 cols is the width of frame
            # These shouldn't need to be updated:
            if ps == program['settings'].nominalps:
                cmd=self.task.getsecondformfieldN
            else:
                cmd=self.task.getsecondformfieldV
            if ps not in program['settings'].secondformfield and (
                    isinstance(self.task,Parse) or (
                    isinstance(self.task,WordCollection
                    ) and self.task.ftype not in ['lx','lc'])):
                cmd()
                # return #just do one at a time
            self.labels['fields'+ps]={
                            'text':ui.StringVar(value=self.fieldslabel(ps)),
                            'columnplus':1,
                            'cmd':cmd,
                            'parent':line,
                            'tt':_("change this field")}
            self.proselabel(**self.labels['fields'+ps])
    def updateprofile(self):
        self.labels['profile']['text'].set(self.profilelabel())
        self.labels['ps']['text'].set(self.pslabel())
    def profilelabel(self):
        profile=program['slices'].profile()
        if not profile:
            profile=_("<no syllable profile>")
        return (_("Looking at {profile}").format(profile=profile))
    def updateps(self):
        self.labels['ps']['text'].set(self.pslabel())
        self.makesliceattrs()
        self.maybeboard()
    def pslabel(self):
        count=program['slices'].count()
        ps=program['slices'].ps()
        if not ps:
            ps=_("<no grammatical category>")
        return (_("{ps} words ({count})").format(ps=ps, count=count))
    def sliceline(self):
        self.newrow()
        line=ui.Frame(self.proseframe,row=self.irow,column=0,
                        columnspan=3,sticky='w')
        self.labels['profile']={'text':ui.StringVar(value=self.profilelabel()),
                                'columnplus':1,
                                'rowplus':1,
                                'cmd':self.task.getprofile,
                                'parent':line,
                                'tt':_("change this syllable profile")}
        self.proselabel(**self.labels['profile'])
        self.labels['ps']={'text':ui.StringVar(value=self.pslabel()),
                                'columnplus':1,
                                'cmd':self.task.getps,
                                'parent':line,
                                'tt':_("change this grammatical category")}
        self.proselabel(**self.labels['ps'])
    def updatecvt(self):
        self.labels['cvt']['text'].set(self.cvtlabel())
        self.makesliceattrs()
        self.maybeboard()
    def cvtlabel(self):
        return (_("Checking {cvt},").format(cvt=program['params'].cvtdict()[self.cvt]['pl']))
    def cvtline(self):
        self.newrow()
        line=ui.Frame(self.proseframe,row=self.irow,column=0,
                        columnspan=3,sticky='w')
        self.labels['cvt']={'text':ui.StringVar(value=self.cvtlabel()),
                                'columnplus':1,
                                'rowplus':1,
                                'cmd':self.task.getcvt,
                                'parent':line,
                                'tt':_("change to other check types")}
        self.proselabel(**self.labels['cvt'])
        #this continues on the same line:
        if self.cvt == 'T':
            self.toneframe(line)
            self.tonegroup(line)
        else:
            self.cvcheck(line)
            self.cvgroup(line)
    def updatetoneframe(self):
        self.labels['toneframe']['text'].set(self.toneframelabel())
    def toneframelabel(self):
        """this label follows a comma, so no caps"""
        checks=program['status'].checks()
        check=program['params'].check()
        if not checks:
            return _("no tone frames defined.")
        elif check not in checks:
            return _("no tone frame selected.")
        else:
            return (_("working on ‘{check}’ tone frame").format(check=check))
    def toneframe(self,line):
        # log.info("toneframes: {}".format(program['toneframes']))
        # log.info("maketoneframes: {}".format(program['toneframes']))
        # log.info("checks: {}; check: {}".format(getattr(self,'checks'),
        #                                         getattr(self,'check')))
        self.labels['toneframe']={'text':ui.StringVar(value=self.toneframelabel()),
                                'columnplus':1,
                                'cmd':self.task.getcheck,
                                'parent':line,
                                'tt':_("change this tone frame")}
        self.proselabel(**self.labels['toneframe'])
    def updatetonegroup(self):
        self.labels['tonegroup']['text'].set(self.tonegrouplabel())
    def tonegrouplabel(self):
        if None in [program['params'].check(), program['status'].group()]:
            program['params'].check(), program['status'].group()
            return _("(no framed group)")
        else:
            return (_("(framed group: ‘{group}’)").format(group=program['status'].group()))
    def tonegroup(self,line):
        check=program['params'].check()
        group=program['status'].group()
        profile=program['slices'].profile()
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
        self.labels['tonegroup']={'text':ui.StringVar(value=self.tonegrouplabel()),
                                'columnplus':2,
                                'cmd':cmd,
                                'parent':line,
                                'tt':_("change this check")}
        self.proselabel(**self.labels['tonegroup'])
    def updatecvcheck(self):
        self.labels['cvcheck']['text'].set(self.cvchecklabel())
    def cvchecklabel(self):
        return (_("working on {check}").format(check=program['params'].cvcheckname()))
    def cvcheck(self,line):
        self.labels['cvcheck']={'text':ui.StringVar(value=self.cvchecklabel()),
                                'columnplus':1,
                                'cmd':self.task.getcheck,
                                'parent':line,
                                'tt':_("change this check")}
        self.proselabel(**self.labels['cvcheck'])
    def updatecvgroup(self):
        self.labels['cvgroup']['text'].set(self.cvgrouplabel())
    def cvgrouplabel(self):
        if not program['params'].check() or 'x' in program['params'].check():
            return
        if program['status'].group():
            return (f"= {program['status'].group()}")
        else:
            return (_("(All groups)"))
    def cvgroup(self,line):
        self.labels['cvgroup']={'text':ui.StringVar(value=self.cvgrouplabel()),
                                'columnplus':2,
                                'cmd':self.task.getgroup,
                                'parent':line,
                                'tt':_("change this group")
                                if program['status'].group()
                                else _("specify one group")
                                }
        self.proselabel(**self.labels['cvgroup'])
    def updatebuttoncolumns(self):
        self.labels['buttoncolumns']['text'].set(self.buttoncolumnslabel())
    def buttoncolumnslabel(self):
        b=program['settings'].buttoncolumns
        if b:
            return (_("Using {n} button columns").format(n=b))
        else:
            return (_("Not using multiple button columns"))
    def buttoncolumnsline(self):
        # log.info(t)
        tt=_("Click here to change the number of columns used for sort buttons")
        self.newrow()
        self.labels['buttoncolumns']={'text':ui.StringVar(value=self.buttoncolumnslabel()),
                                'columnplus':1,
                                'cmd':self.task.getbuttoncolumns,
                                'tt':tt}
        self.proselabel(**self.labels['buttoncolumns'])
    def updatemaxprofiles(self):
        self.labels['maxes']['text'].set(self.maxprofileslabel())
    def maxprofileslabel(self):
        return (_("Max profiles: {max_profiles}; ").format(max_profiles=program['settings'].maxprofiles))
    def updatemaxpss(self):
        self.labels['maxes']['text'].set(self.maxpsslabel())
    def maxpsslabel(self):
        return (_("Max lexical categories: {max_pss}").format(max_pss=program['settings'].maxpss))
    def maxes(self):
        self.newrow()
        line=ui.Frame(self.proseframe,row=self.irow,column=0,
                        columnspan=3,sticky='w')
        self.labels['maxprofiles']={
                        'text':ui.StringVar(value=self.maxprofileslabel()),
                        'columnplus':1,
                        'cmd':self.task.getmaxprofiles,
                        'parent':line,
                        'tt':_("change this max")}
        self.proselabel(**self.labels['maxprofiles'])
        self.opts['columnplus']=1
        self.labels['maxpss']={'text':ui.StringVar(value=self.maxpsslabel()),
                                'columnplus':1,
                                'cmd':self.task.getmaxpss,
                                'parent':line,
                                'tt':_("change this check")}
        self.proselabel(**self.labels['maxpss'])
    def updatemulticheckscope(self):
        self.labels['cvgroup']['text'].set(self.multicheckscopelabel())
    def multicheckscopelabel(self):
        t=(_("Run all checks for {checks}").format(checks=unlist(self.task.cvtstodoprose())))
    def multicheckscope(self):
        if not hasattr(self.task,'cvtstodo'):
            self.task.cvtstodo=['V']
        self.newrow()
        line=ui.Frame(self.proseframe,row=self.irow,column=0,
                        columnspan=3,sticky='w')
        self.labels['multicheckscope']={
                        'text':ui.StringVar(value=self.multicheckscopelabel()),
                        'columnplus':1,
                        'cmd':self.task.getmulticheckscope,
                        'parent':line,
                        'tt':_("change this check")}
        self.proselabel(**self.labels['multicheckscope'])
    def updateparserasklevel(self):
        self.labels['parserasklevel']['text'].set(self.parserasklevellabel())
    def parserasklevellabel(self):
        try:
            ls=self.task.parser.levels() # we need this anyway, and a parser test
            return (_("Parse with confirmation at {parser_levels}").format(parser_levels=ls[self.task.parser.ask]))
        except AttributeError as e:
            log.info(f"Error loading parser levels: {e}")
            return
    def updateparserautolevel(self):
        self.labels['parserautolevel']['text'].set(self.parserautolevellabel())
    def parserautolevellabel(self):
        try:
            ls=self.task.parser.levels()
            return (_("Parse automatically at {parser_levels}").format(parser_levels=ls[self.task.parser.auto]))
        except AttributeError as e:
            log.info(f"Error loading parser levels: {e}")
            return
    def parserlevels(self):
        self.newrow()
        line=ui.Frame(self.proseframe,row=self.irow,column=0,
                        columnspan=3,sticky='w')
        self.labels['parserasklevel']={
                        'text':ui.StringVar(value=self.parserasklevellabel()),
                        'columnplus':1,
                        'cmd':self.task.getparserasklevel,
                        'parent':line,
                        'tt':_("change this confirmed parse level")}
        self.proselabel(**self.labels['parserasklevel'])
        self.newrow()
        line=ui.Frame(self.proseframe,row=self.irow,column=0,
                        columnspan=3,sticky='w')
        self.labels['parserautolevel']={
                        'text':ui.StringVar(value=self.parserautolevellabel()),
                        'columnplus':1,
                        'cmd':self.task.getparserautolevel,
                        'parent':line,
                        'tt':_("change this auto parse level")}
        self.proselabel(**self.labels['parserautolevel'])
    def updatesensetodo(self):
        self.labels['sensetodo']['text'].set(self.sensetodolabel())
    def sensetodolabel(self):
        t=self.task
        if hasattr(t,'sensetodo') and t.sensetodo is not None:
            return _("Parsing {sense}").format(sense=t.sensetodo.formatted(t.analang,t.glosslangs))
        else:
            return _("Parsing all words")
    def sensetodo(self):
        self.newrow()
        line=ui.Frame(self.proseframe,row=self.irow,column=0,
                        columnspan=3,sticky='w')
        self.labels['sensetodo']={
                            'text':ui.StringVar(value=self.sensetodolabel()),
                            'columnplus':1,
                            'cmd':self.task.getsensetodo,
                            'parent':line,
                            'tt':_("change this sense to do")}
        self.proselabel(**self.labels['sensetodo'])
    def redofinalbuttons(self):
        if hasattr(self,'bigbutton') and self.bigbutton.winfo_exists():
            self.bigbutton.destroy()
        self.finalbuttons()
    def finalbuttons(self):
        # self.opts['row']+=6
        self.newrow()
        try:
            kwargs=self.task.dobuttonkwargs()
            self.bigbutton=self.button(**kwargs)
        except Exception as e:
            log.error(f"Problem: {e}")
    def makesecondfieldsOK(self):
        """Not called anywhere?"""
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
        self.leaderboard=ui.Frame(self,row=0,column=1,sticky='') #nesw
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
        if isinstance(self.task,TranscribeS):
            self.makeglyphtable()
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
        ui.Label(titleframe, text=_('Progress for'), font='title',
                row=0,column=1,sticky='nwe',padx=10)
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
    def updateprogresstable(self):
        """This could be a method called in creation, then again when updates
        are needed. I should controll activebackground and commands, setting
        and clering the one or the other, according to current settings.
        Maybe could iterate across all, maybe calculate the right column and row
        should access self.checks and self.profiles for indexes"""
        if profile == curprofile and check == curcheck:
            tb.configure(background=tb['activebackground'])
            tb.configure(command=donothing)
    def makeglyphbutton(self,glyph):
        f=self.glyphbuttons[glyph]=ui.Frame(self.glyphscroll.content,
                            r=self.glyphscroll.content.nrows())
                            # r=len(self.glyphscroll.content.winfo_children()))
        l=ui.Label(f, text=glyph, font='read', width=3, c=0, sticky="EW")
        fn=lambda x=glyph:self.task.makewindow(x)
        bf=SortGlyphGroupButtonFrame(f, self.task,
                                    group=glyph,
                                    on_select=fn,
                                    column=1, sticky="W")
        if not bf.hasexample:
            log.info(f"deleting empty button for ‘{glyph}’")
            l.destroy()
            bf.destroy()
    def makeglyphtable(self):
        self.glyphscroll=ui.ScrollingFrame(self.leaderboard,row=1,column=0)
        self.glyphbuttons={}
        self.updateglyphbuttons()
    def updateglyphbuttons(self):
        """This ultimately should cover all C or V, across checks and
        ps-profiles"""
        # groups=program['status'].all_groups_verified_for_cvt()
        groups=set(program['alphabet'].glyphs())
        for k in set(self.glyphbuttons)-groups:
            self.glyphbuttons[k].destroy()
        for k in groups-set(self.glyphbuttons):
            self.makeglyphbutton(k)
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
            program['settings'].setprofile(profile)
            program['settings'].setcheck(check)
            self.maybeboard()
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
        # log.info("program['toneframes']: {}".format(program['toneframes']))
        try:
            frames=list(program['toneframes'][ps].keys())
        except KeyError:
            frames=list()
        allchecks=program['status'].allcheckswdata()
        self.checks=list(dict.fromkeys(allchecks)) #could unsort slices priority
        # log.info("allchecks dicted: {}".format(allchecks))
        if self.cvt != 'T': #don't resort tone frames
            self.checks.sort(key= lambda x:(len(x),x),reverse=True) #longest first
        # log.info("allchecks sorted: {}".format(allchecks))
        profiles.sort(key=lambda x:(x.count(self.cvt),len(x)))
        self.profiles=['colheader']+profiles+['next']
        ungroups=0
        unsorted_icon='[X]'
        if program['settings'].showdetails:
            verified=_("verified")
            unsorted=_("unsorted")
            # t='+ = {} \n! = {}'.format(tv,tu)
            t=f"+ = {verified} \n{unsorted_icon} = {unsorted}"
            h=ui.Label(self.leaderboardtable,text=t,font='small')
            h.grid(row=row,column=0,sticky='e')
            h.bind('<ButtonRelease-1>', refresh)
            htip=_("Refresh table, \nsave settings")
            th=ui.ToolTip(h,htip)
        r=list(program['status'][cvt][ps])
        # log.info("Table rows possible: {}".format(r))
        # log.info("Table columns possible: {}".format(allchecks))
        # log.info("toneframes possible: {}".format(frames))
        for profile in self.profiles: #keep this for later updates
            column=0
            if profile in ['colheader','next']+list(program['status'][cvt][
                                                            ps].keys()):
                """header first"""
                if profile in program['status'][cvt][ps]:
                    if program['status'][cvt][ps][profile] == {}:
                        continue
                    #Make row header
                    t=profile
                    if program['settings'].showdetails:
                        t+=(" ({len(program['settings'].profilesbysense[ps][profile])})")
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
                            relief='flat',cmd=program['settings'].setprofile)
                    brh.grid(row=row,column=column,sticky='e')
                    brht=ui.ToolTip(brh,_("Go to the next syllable profile"))
                """then checks"""
                for check in self.checks+['next']:
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
                                cmd=lambda todo=True:program['settings'].setcheck(
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
                                g+='+' #these should be strings
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
                            donenum=''
                        elif (not program['settings'].showdetails or
                            (type(totalnum) is int and type(donenum) is int)):
                            # donenum='{}/{}'.format(donenum,totalnum)
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
                            tips.extend([(_("{count} groups to verify!")
                                        ).format(count=nunverified)])
                        if not tips:
                            tips.extend([_("Sorted and verified!")])
                        tip='\n'.join(tips)
                        tb.grid(row=row,column=column,ipadx=0,ipady=0,
                                                                sticky='nesw')
                        ttb=ui.ToolTip(tb,tip)
            row+=1
        if ungroups > 0:
            log.error(_("You have more groups verified than there are, in {count} "
                        "cells").format(count=ungroups))
        # self.frame.update()
    def __init__(self, parent, task, **kwargs):
        # log.info("Remaking status frame")
        self.setopts()
        self.irow=0 #frame internal rows
        self.parent=parent
        self.task=task #this is the window that called it; task or chooser
        self.mainrelief=kwargs.pop('relief',None) #not for frame
        self.labels={} #make a place to store these
        kwargs['padx']=25
        kwargs['gridwait']=True
        super(StatusFrame, self).__init__(parent, **kwargs)
        self.makeui()
    def makesliceattrs(self):
        if not isinstance(self.task,WordCollection):
            self.cvt=program['params'].cvt()
            self.ps=program['slices'].ps()
            self.profile=program['slices'].profile()
            self.check=program['params'].check()
            self.checks=program['status'].checks()
    def makeui(self):
        self.makeproseframe()
        self.interfacelangline()
        self.analangline()
        self.glosslangline()
        if isinstance(self.task,Segments) and not isinstance(self.task,TranscribeS):
            self.fieldsline()
        if ('slices' in program and
                not isinstance(self.task,(TaskChooser,
                                            Parse,
                                            TranscribeS,
                                            WordCollection))
                ):
            self.makesliceattrs()
            if isinstance(self.task,Multislice): #any cvt
                self.maxes()
            else:
                self.sliceline()
            if isinstance(self.task,Multicheck): #segments only
                self.multicheckscope()
            elif not (isinstance(self.task,ReportCitationT) or
                        isinstance(self.task,JoinUFgroups)
                        ):
                self.cvtline()
            if isinstance(self.task,Sort) and not isinstance(self.task,Transcribe):
                self.buttoncolumnsline()
        if isinstance(self.task,Parse):
            self.parserlevels()
            self.sensetodo()
        self.maybeboard()
        self.finalbuttons()
        # self.dogrid()
class Settings(object):
    """docstring for Settings."""
    def interfacelangwrapper(self,choice=None,window=None):
        # log.info(f"going to set interface lang {choice}")
        if choice:
            interfacelang(choice) #change the UI *ONLY*; no object attributes
            self.set('interfacelang',choice,window) #set variable for the future
            self.langnames() #relocalize
            program['taskchooser'].mainwindowis.status.makeui()
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
                    log.info(_("Found {name} Repository!"
                                ).format(name=repo[r].repotypename))
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
                                'askedlxtolc',
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
                                    # 'profilecounts',
                                    'scount',
                                    'sextracted',
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
                                            'asr_kwargs',
                                            'asr_repos'
                                            ]},
            'alphabet':{
                                'file':'alphabetsettingsfile',
                                'attributes':[
                                            'status',
                                            'glyphdict',
                                            'alphabet_order',
                                            'alphabet_ncolumns',
                                            'alphabet_chart_title',
                                            'alphabet_exids',
                                            'alphabet_pagesize',
                                            'glyph_members',
                                            'glyphs_distinguished'
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
            log.error(_("No file name for setting {setting}!").format(setting=setting))
    def loadandconvertlegacysettingsfile(self,setting='defaults'):
        #This should be removed at some point Only used when find old file NAME
        savefile=self.settingsfile(setting)
        legacy=savefile.with_suffix('.py')
        log.info(_("Going to make {legacy_name} into {savefile}").format(legacy_name=legacy,savefile=savefile))
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
            log.debug(_("Trying for {setting} settings in {legacy_name}").format(setting=setting, legacy_name=legacy))
            spec = importlib.util.spec_from_file_location(setting,legacy)
            module = importlib.util.module_from_spec(spec)
            sys.modules[setting] = module
            spec.loader.exec_module(module)
            for s in self.settings[setting]['attributes']:
                if s in oldnames and hasattr(module,oldnames[s]):
                    setattr(o,s,getattr(module,oldnames[s]))
                    log.info(_("Imported and upgraded {s}/{old}: {val}").format(
                                                    s=s,old=oldnames[s],val=getattr(o,s)))
                elif hasattr(module,s):
                    setattr(o,s,getattr(module,s))
                    log.info(_("Imported {s}: {val}").format(s=s,val=getattr(o,s)))
                else:
                    log.info(_("Attribute {s} not found").format(s=s))
            log.info(_("Importing {setting} settings done.").format(setting=setting))
        except Exception as e:
            log.error(_("Problem importing {legacy} ({error})").format(legacy=legacy,error=e))
        # b/c structure changed:
        if 'glosslangs' in self.settings[setting]['attributes']:
            self.glosslangs=[]
            for lang in ['glosslang','glosslang2']:
                if hasattr(module,lang):
                    self.glosslangs.append(getattr(module,lang))
                    try:
                        delattr(self,lang) #because this would be made above
                    except AttributeError:
                        log.info(_("attribute {lang} doesn't seem to be there").format(lang=lang))
        dict1=self.makesettingsdict(setting=setting)
        self.storesettingsfile(setting=setting) #do last
        self.loadsettingsfile(setting=setting) #verify write and read
        dict2=self.makesettingsdict(setting=setting)
        """Now we verify that each value read the same each time"""
        for s in dict1:
            if s in dict2 and str(dict1[s]) == str(dict2[s]):
                log.info(_("Attribute {s} verified as {val1}={val2}").format(s=s,
                                            val1=str(dict1[s]), val2=str(dict2[s])))
            elif s in dict2:
                log.error(_("Problem with attribute {s}; {val1}≠{val2}").format(s=s,
                                            val1=str(dict1[s]), val2=str(dict2[s])))
            else:
                log.error(_("Attribute {s} didn't make it back").format(s=s))
                log.error(_("You should send in an error report for this."))
                exit()
        log.info(_("Settings file {legacy} converted to {savefile}, with each value verified.")
                .format(legacy=legacy,savefile=savefile))
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
        self.alphabetsettingsfile=basename.with_suffix(".Alphabet.ini")
        self.settingsbyfile() #This just sets self.settings
        for setting in self.settings:
            savefile=self.settingsfile(setting)#self.settings[setting]['file']
            if not file.exists(savefile):
                log.debug(_("{file} doesn't exist!").format(file=savefile))
                legacy=savefile.with_suffix('.py')
                if file.exists(legacy):
                    log.debug(_("But legacy file {legacy} does; converting!").format(legacy=legacy))
                    self.loadandconvertlegacysettingsfile(setting=setting)
            if str(savefile).endswith('.dat') and file.exists(savefile):
                for r in self.repo:
                    self.repo[r].add(savefile)
        for r in self.repo:
            self.repo[r].commit()
    def moveattrstoobjects(self):
        # log.info("Glosslangs (in moveattrstoobjects): {}".format(self.glosslangs.langs()))
        # log.info(f"moveattrstoobjects done: {self.attrs_moved_to_object}")
        to_do=set(self.fndict)-self.attrs_moved_to_object
        log.info(f"moveattrstoobjects to do: {to_do}")
        for attr in to_do:
            if hasattr(self,attr):
                log.info(_("moving attr {attr} to object ({val})").format(attr=attr,val=getattr(self,attr)))
                self.fndict[attr](getattr(self,attr))
                # log.info("Glosslangs (in moveattrstoobjects): {}".format(self.glosslangs.langs()))
                if attr not in ['glosslangs']: #obj and attr have same name...
                    delattr(self,attr)
                self.attrs_moved_to_object.add(attr)
            else:
                log.info(_("attr {attr} not found!").format(attr=attr))
        log.info(_("attrs_moved_to_object={val}").format(val=self.attrs_moved_to_object))
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
            fns['status']=program['alphabet'].status
            fns['glyphdict']=program['alphabet'].glyphdict
            fns['glyph_members']=program['alphabet'].glyph_members
            fns['glyphs_distinguished']=program['alphabet'].distinguished
            fns['alphabet_order']=program['alphabet'].order#self.alpha_order
            fns['alphabet_ncolumns']=self.alpha_ncolumns
            fns['alphabet_exids']=self.alpha_exids
            fns['alphabet_chart_title']=self.alpha_chart_title
            fns['alphabet_pagesize']=self.alpha_pagesize
            #This seems to break here:
            fns['ps']=program['slices'].ps
            fns['profile']=program['slices'].profile
            # except this one, which pretends to set but doesn't (throws arg away)
            fns['profilecounts']=program['slices'].slicepriority
            fns['asr_repos']=program['soundsettings'].asr_repo_tally
            fns['asr_kwargs']=program['soundsettings'].asr_kwarg_dict
            fns['giturls']=self.repo['git'].remoteurls
            fns['hgurls']=self.repo['hg'].remoteurls
        except Exception as e:
            log.error(_("Only finished settingsobjects up to {keys} ({error})").format(keys=fns.keys(),error=e))
            self.moveattrstoobjects() #always do this next
            return []
        log.info(_("Finished settingsobjects up to {keys}").format(keys=fns.keys()))
        self.moveattrstoobjects() #always do this next
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
            # log.info("{} attr value: {}".format(s,getattr(o,s,'Not Found!')))
            """This dictionary of functions isn't made until after the objects,
            at the end of settings init. So this block is not used in
            conversion, only in later saves."""
            if hasattr(self,'fndict') and s in self.fndict:
                # log.info("Trying to dict {} attr".format(s))
                try:
                    d[s]=self.fndict[s]()
                    # log.info("Value {}={} found in object".format(s,d[s]))
                except:
                    log.error(_("Value of {attr} not found in object").format(attr=s))
            elif hasattr(o,s):
                if getattr(o,s) or setting == 'soundsettings': #store Falses
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
    def readsettingsdict(self,settingsdict):
        """This takes a dictionary keyed by attribute names"""
        # d=settingsdict
        if 'fs' in settingsdict:
            o=self.soundsettings
        else:
            o=self
        for s in settingsdict:
            v=settingsdict[s]
            if isinstance(v,configparser.SectionProxy):
                continue #don't store expty section headers
            elif hasattr(self,'fndict') and s in self.fndict:
                # log.info("Trying to read {} to object with value {} and fn "
                #             "{}".format(s,v,self.fndict[s]))
                self.fndict[s](v)
            elif (isinstance(v,dict) and
                hasattr(o,s) and isinstance(getattr(o,s),dict)):
                getattr(o,s).update(v)
            else:
                # log.info("Trying to read {} to {} with value {}, type {}"
                #             "".format(s,o,v,type(v)))
                setattr(o,s,v)
        return settingsdict
    def no_settings_change(self,filename,d):
        config=ConfigParser()
        config.read(filename,encoding='utf-8')
        if d == config:
            return True
    def storesettingsfile(self,setting='defaults'):
        #There are too many calls to this; why?
        filename=self.settingsfile(setting)
        config=ConfigParser()
        if setting in ['status', 'toneframes']:
            # log.info("storesettingsfile for {}".format(setting))
            d=program[setting]
        else:
            d=self.makesettingsdict(setting=setting)
        if self.no_settings_change(filename,d):
            log.info(_("no settings change; not writing."))
            return
        if setting in ['soundsettings']:
            log.info(_("Sound settings currently: {settings}").format(settings=d))
        config['default']={}
        # log.info("storing settings file {}".format(setting))
        for s in [i for i in d if i not in [None,'None']]:
            v=d[s]
            # log.info(f"Ready to store {type(v)} type data for {s}: {v}")
            if isinstance(v, dict):
                config[s]=indenteddict(v)
            else:
                config['default'][s]=str(v)
        if config['default'] == {}:
            del config['default']
        header=(_("# This settings file was made on {date} on {node}").format(
                                                    date=now(),
                                                    node=platform.uname().node)
                )
        # log.info(f"Ready to write {type(config)} type data: {config}")
        # config.output() #this logs out the whole config
        with open(filename, 'w', encoding='utf-8') as file:
            file.write(header+'\n\n')
            config.write(file)
    def loadsettingsfile(self,setting='defaults'):
        filename=self.settingsfile(setting)
        config=ConfigParser()
        config.read(filename,encoding='utf-8')
        log.info(_("Trying for {setting} settings in {file}").format(setting=setting, file=filename))
        if not config.sections() and setting not in ['status','toneframes']:
            if setting == 'adhocgroups':
                self.adhocgroups={}
            return
        d={}
        # log.info("Found {} sections: {}".format(setting,config.sections()))
        for section in config: #self.settings[setting]['attributes']:
            # log.info('\n'.join([': '.join([k,config[section][k]])
            #                             for k in config[section]]))
            if 'default' in config and section in ['default','DEFAULT']:
                for k in config[section]:
                    # log.info("Moving {}.{}={} to object".format(section,k,
                    #                                         config[section][k]))
                    d[k]=ofromstr(config['default'][k])
                # d[section]=ofromstr(config['default'][section])
            else:
                log.info(_("working in non-default section {section}").format(section=section))
                # log.debug("Trying for {} settings in {}".format(section, setting))
                if len(config[section].values())>0:
                    # log.info("Found Dictionary value for {} ({})".format(
                    #                                 section,config[section]))
                    for s in config[section]:
                        # log.info(f"Found value {s}: {config[section][s]}")
                        if section in ['status','toneframes']:
                            d[ofromstr(s)]=ofromstr(config[section][s])
                            # log.info(f"{s} item {ofromstr(s)} is {d[ofromstr(s)]}")
                        else:
                            try:
                                d[section][ofromstr(s)]=ofromstr(
                                                            config[section][s])
                            except KeyError:
                                d[section]={ofromstr(s):ofromstr(
                                                            config[section][s])}
                        """Make sure strings become python data"""
                else:
                    # log.debug("Found String/list/other value for {}: ({})"
                    #         "".format(section,len(config[section].values())))
                    d[section]=ofromstr(config[section])
        if setting == 'status':
            # log.info("setting {} is {}".format(setting,d))
            self.makestatus({k:d[k] for k in d if k != 'DEFAULT'})
            log.info(_("makestatus: {status}").format(status=program['status']))
        elif setting == 'toneframes':
            # log.info("setting {} is {}".format(setting,d))
            self.maketoneframes({k:d[k] for k in d if k != 'DEFAULT'})
            log.info(_("maketoneframes: {frames}").format(frames=program['toneframes']))
        else:
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
                        'showdetails':[],
                        'askedlxtolc':[],
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
        log.info(_("Initializing settings."))
        # self.defaults is already there, from settingsfilecheck
        self.initdefaults() #provides self.defaultstoclear, needed?
        self.cleardefaults() #this resets all to none (to be set below)
    def getdirectories(self):
        self.directory=file.getfilenamedir(self.liftfilename)
        if not file.exists(self.directory):
            log.info(_("Looks like there's a problem with your directory... {file}\n{dir}")
                    .format(file=self.liftfilename,dir=self.directory))
            exit()
        self.repocheck()
        self.settingsfilecheck()
        self.imagesdir=file.getimagesdir(self.directory)
        self.audiodir=file.getaudiodir(self.directory)
        # log.info('self.audiodir: {}'.format(self.audiodir))
        self.reportsdir=file.getreportdir(self.directory)
        self.exportsdir=file.getexportdir(self.directory)
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
            log.info(_("{repo} currently has {count} files").format(repo=r,count=len(present)))
            for f in maindirfiles:
                # log.info("{}".format([file.getreldirposix(self.repo[r].url,f)]))
                # log.info("working on {}".format(file.getreldirposix(self.repo[r].url,f)))
                log.info(_("working on {file}").format(file=file.getfile(f)))
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
            log.info(_("{wav_count} wav files to check for the {repo} repo (of {total_count} files total "
                    "here)").format(wav_count=len(audio),r=r,total_count=len(audiohere)))
            log.info(_("head of wav files in repo: {files}").format(files=list(present)[:10]))
            log.info(_("head of wav files here: {files}").format(files=list(audiohere)[:10]))
            log.info(_("head of wav files to check: {files}").format(files=list(audio)[:10]))
            for f in audio:
                self.repo[r].add(f) #These should exist, from ls above
                # if threading.active_count()<maxthreads:
                #     t = threading.Thread(target=ifnotthereadd, args=(f,r))
                #     t.start()
                # log.info(_("trackuntrackedfiles waiting for {count} audio file threads."
                #         ).format(count=threading.active_count()))
                # if t:
                #     t.join()
                # self.repo[r].add(f)
            for ext in ['png','jpg','gif']:
                # log.info(_("Image Directory: {dir}").format(dir=self.imagesdir))
                # log.info("Found image files: {}".format(nn([i for i in
                # file.getfilesofdirectory(self.imagesdir,
                #                         '*.'+ext)], oneperline=True)))
                i=set([file.getreldirposix(self.repo[r].url,i)
                        for i in file.getfilesofdirectory(self.imagesdir,
                                                '*.'+ext)]
                        )-present
                log.info(_("{count} {extension} files to check for the {repo} repo")
                        .format(count=len(i),extension=ext,repo=r))
                for f in i:
                    self.repo[r].add(f) #These should exist, from ls above
                    # if threading.active_count()<maxthreads:
                    #     u = threading.Thread(target=ifnotthereadd, args=(f,r))
                    #     u.start()
                    # log.info("trackuntrackedfiles waiting for {} {} file "
                    #     "threads.".format(threading.active_count(),ext))
                        # if u:
                        #     u.join()
        log.info(_("trackuntrackedfiles finished."))
    def alpha_order(self,value=[]):
        return program['alphabet'].order(value)
    def alpha_exids(self,value=dict()):
        if value:
            self._alphabet_exids=value
        return getattr(self,'_alphabet_exids',value)
    def alpha_ncolumns(self,value=0):
        if value:
            self._alphabet_ncolumns=value
        return getattr(self,'_alphabet_ncolumns',5)
    def alpha_chart_title(self,value=''):
        if value:
            self._alphabet_chart_title=value
        return getattr(self,'_alphabet_chart_title',value)
    def alpha_pagesize(self,value=''):
        if value:
            self._alphabet_pagesize=value
        return getattr(self,'_alphabet_pagesize','A4')
    def pss(self):
        log.info(_("checking these lexical category names for plausible noun "
                "and verb names: {pss}").format(pss=program['db'].pss))
        topn=3 #just in case N and V aren't the first two, finish with top
        log.info(_("Looking at pss {pss}").format(pss=program['db'].pss))
        for ps in reversed(program['db'].pss[:topn]):
            log.info(_("Looking at ps {ps}").format(ps=ps))
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
            log.info(_("Using ‘{noun}’ for nouns, and ‘{verb}’ for verbs").format(
                noun=self.nominalps,
                verb=self.verbalps))
        except AttributeError:
            log.info(_("Problem with finding a nominal and verbal lexical "
            "category (looked in first two of [{pss}])")
            .format(pss=program['db'].pss))
        if self.secondformfield:
            if self.nominalps in self.secondformfield:
                self.pluralname=self.secondformfield[self.nominalps]
            if self.verbalps in self.secondformfield:
                self.imperativename=self.secondformfield[self.verbalps]
    def makesecondformfieldsOK(self):
        if self.nominalps not in self.secondformfield:
            program['taskchooser'].mainwindowis.getsecondformfieldN()
        if self.verbalps not in self.secondformfield:
            program['taskchooser'].mainwindowis.getsecondformfieldV()
    def secondformfieldsOK(self):
        if (self.nominalps in self.secondformfield and
            self.verbalps in self.secondformfield):
            return True
    def fields(self):
        """I think this is lift specific; may move it to defaults, if not."""
        # log.info(program['db'].fieldnames)
        try:
            fieldnames=program['db'].fieldnames[self.analang]
        except KeyError:
            fieldnames=[]
        self.secondformfield={}
        log.info(_("Fields found in lexicon: {fields}").format(fields=fieldnames))
        self.plopts=['Plural', 'plural', 'pl', 'Pluriel', 'pluriel']
        self.impopts=['Imperative', 'imperative', 'imp', 'Imp', 'Imperatif',
                                                    'imperatif']
        for opt in self.plopts:
            if opt in fieldnames:
                self.secondformfield[self.nominalps]=self.pluralname=opt
        try:
            log.info(_("Plural field name: {name}").format(name=self.pluralname))
            for entry in program['db'].entries:
                entry.fieldvalue(self.pluralname,self.analang) # get the right field!
        except AttributeError:
            log.info(_('Looks like there is no Plural field in the database'))
            self.pluralname=None
        for opt in self.impopts:
            if opt in fieldnames:
                self.secondformfield[self.verbalps]=self.imperativename=opt
        try:
            log.info(_("Imperative field name: {name}").format(name=self.imperativename))
            for entry in program['db'].entries:
                entry.fieldvalue(self.imperativename,self.analang) # get the right field!
        except AttributeError:
            log.info(_('Looks like there is no Imperative field in the database'))
            self.imperativename=None
    def checkforpolygraphsindata(self):
        for lang in program['db'].s:
            for sclass in [sc for sc in program['db'].s[lang]
                                if ('dg' in sc or 'tg' in sc or 'qg' in sc)]:
                if program['db'].s[lang][sclass]:
                    return True
    def askaboutpolygraphs(self,onboot=False):
        def nochanges():
            log.info(_("Trying to make no changes"))
            if not pgw.exitFlag.istrue():
                pgw.destroy()
            if foundchanges():
                log.info(_("Found changes, but not storing them; returning 1."))
                return 1
        def makechanges():
            log.info(_("Changes called for; like it or not, redoing analysis."))
            pgw.destroy()
            if not foundchanges():
                log.info(_("User asked for changes to polygraph settings, but "
                        "no changes found."))
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
            log.info(_("No changes found to polygraph settings, continuing."))
        oktext=_("OK")
        azt=program['name']
        if onboot:
            nochangetext=_("Exit {azt} with no changes").format(azt=program['name'])
        else:
            nochangetext=_("Exit with no changes")
        log.info(_("Asking about Digraphs and Trigraphs!"))
        titlet=_("{azt} Digraphs and Trigraphs").format(azt=program['name'])
        hasdata=self.checkforpolygraphsindata()
        #From wherever this is opened, it should withdraw and deiconify that
        pgw=ui.Window(program['taskchooser'].mainwindowis,title=titlet,exit=False)
        t=_("Which of the following letter sequences from your data "
            "refer to a single sound?")
        log.info(_("working with db.analangs: {analangs} and params.analang: {analang}")
                .format(analangs=program['db'].analangs, analang=program['params'].analang()))
        lnames=[self.languagenames[y] for y in set(
                    program['db'].analangs+[program['params'].analang()]
                                                )]
        if len(lnames)>1:
            t+=(_(" (Answer for each of {names}.)").format(names=unlist(lnames)))
        else:
            t+=(_(" (in {names})").format(names=unlist(lnames)))
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
        t=_("If you expect one (already in your data) that isn't listed "
            "here, please click here to Email me, and I can add it.")
        row+=1
        t2=ui.Label(pgw.frame,text=t,column=0, row=row)
        eurl='mailto:{}?subject=New trigraph or digraph to add (today)'.format(
                                                            program['Email'])
        t2.bind("<Button-1>", lambda e: openweburl(eurl))
        if hasdata:
            t=_("Making changes will restart {name} and trigger another syllable profile analysis. \n"
                "If you don't want that, click ‘{btn}’.").format(name=program['name'], btn=nochangetext)
        else:
            t=_("\n*** There don't seem to be any possible digraphs or trigraphs "
                "in your data ***\n")
        row+=1
        t3=ui.Label(pgw.frame,text=t,column=0, row=row)
        helpurl='{}/POLYGRAPHS.md'.format(program['docsurl'],program['Email'])
        t=_("See {url} for further instructions.").format(url=helpurl)
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
        if hasdata:
            row+=1
            b=ui.Button(pgw.frame,text=oktext,command=makechanges, width=15,
                    column=0, row=row, sticky='e',padx=15)
        pgw.wait_window(pgw)
        if not program['taskchooser'].exitFlag.istrue():
            return nochanges() #this is the default exit behavior
    def polygraphLWCdefaults(self):
        lwcdefaults={'en':{'D':{'gh':True,
                        		'bb':True,
                        		'dd':True,
                        		'gg':True,
                        		'gu':True,
                        		'mb':False,
                        		'nd':False,
                        		'dw':False,
                        		'gw':False,
                        		'zl':False},
                        	'C':{'ckw':False,
                        		'thw':False,
                        		'tch':True,
                        		'cc':True,
                        		'pp':True,
                        		'pt':False,
                        		'tt':True,
                        		'ck':True,
                        		'qu':True,
                        		'mp':False,
                        		'nt':False,
                        		'nk':False,
                        		'tw':False,
                        		'kw':False,
                        		'ch':True,
                        		'ph':True,
                        		'sh':True,
                        		'hh':True,
                        		'ff':True,
                        		'sc':False,
                        		'ss':True,
                        		'th':True,
                        		'sw':False,
                        		'hw':True,
                        		'ts':False,
                        		'sl':False},
                        	'G':{'yw':False},
                        	'N':{'mm':True,
                        		'ny':False,
                        		'gn':True,
                        		'nn':True,
                        		'nw':False},
                        	'S':{'rh':True,
                        		'wh':True,
                        		'll':True,
                        		'rr':True,
                        		'lw':False,
                        		'rw':False},
                        	'V':{'ou':True,
                        		'ei':True,
                        		'ai':True,
                        		'yi':True,
                        		'ea':True,
                        		'ay':True,
                        		'ee':True,
                        		'ey':True,
                        		'ie':True,
                        		'oa':True,
                        		'oo':True,
                        		'ow':True,
                        		'ue':True,
                        		'oe':True,
                        		'au':True,
                        		'oi':True,
                        		'eau':True}},
                     'fr':{'D':{'gh':False,
                         		'bb':False,
                         		'dd':False,
                         		'gg':False,
                         		'gu':True,
                         		'mb':False,
                         		'nd':False,
                         		'dw':False,
                         		'gw':False,
                         		'zl':False},
                         	'C':{'ckw':False,
                         		'thw':False,
                         		'tch':True,
                         		'cc':True,
                         		'pp':True,
                         		'pt':False,
                         		'tt':False,
                         		'ck':False,
                         		'qu':True,
                         		'mp':False,
                         		'nt':False,
                         		'nk':False,
                         		'tw':False,
                         		'kw':False,
                         		'ch':True,
                         		'ph':True,
                         		'sh':False,
                         		'hh':False,
                         		'ff':False,
                         		'sc':False,
                         		'ss':True,
                         		'th':True,
                         		'sw':False,
                         		'hw':False,
                         		'ts':False,
                         		'sl':False},
                         	'G':{'yw':False},
                         	'N':{'mm':False,
                         		'ny':False,
                         		'gn':True,
                         		'nn':False,
                         		'nw':False},
                         	'S':{'rh':True,
                         		'wh':True,
                         		'll':True,
                         		'rr':True,
                         		'lw':False,
                         		'rw':False},
                         	'V':{'ou':True,
                         		'ei':True,
                         		'ai':True,
                         		'yi':False,
                         		'ea':True,
                         		'ay':False,
                         		'ee':False,
                         		'ey':False,
                         		'ie':True,
                         		'oa':True,
                         		'oo':True,
                         		'ow':False,
                         		'ue':True,
                         		'oe':True,
                         		'au':True,
                         		'oi':True,
                         		'eau':True}
                    }   }
        if program['params'].analang in lwcdefaults:
            log.info(_("It looks like you're working on your LWC; using {lang} digraph defaults")
                    .format(lang=self.languagenames[program['params'].analang]))
            return lwcdefaults[program['params'].analang] #in case trying out a demo
        try:
            log.info(_("Using your interface language ({lang}) digraph defaults")
                    .format(lang=self.languagenames[interfacelang()]))
            return lwcdefaults[interfacelang()] #assume this general framework
        except KeyError:
            log.info(_("It looks like neither your LWC ({analang}) nor your interface language ({interlang}) "
                    "has a set of digraph defaults, so not providing any")
                    .format(analang=self.languagenames[program['params'].analang],
                            interlang=self.languagenames[interfacelang()]))
            return {} #let users build from scratch
    def polygraphcheck(self):
        log.info(_("Checking for Digraphs and Trigraphs!"))
        # log.info("Language settings: {}".format(program['db'].s))
        firstrun=False
        if not hasattr(self,'polygraphs'):
            firstrun=True
            self.polygraphs={}
        for lang in program['db'].analangs:
            if lang not in program['db'].s:
                log.error(_("Language {lang} found without segment settings."
                            ).format(lang=lang))
                continue
            if lang not in self.polygraphs:
                self.polygraphs[lang]=self.polygraphLWCdefaults()
            for sclass in [sc for sc in program['db'].s[lang]
                                    if ('dg' in sc or 'tg' in sc or 'qg' in sc)]:
                pclass=sclass.replace('dg','').replace('tg','').replace('qg','')
                if pclass not in self.polygraphs[lang]:
                    self.polygraphs[lang][pclass]={}
                for pg in program['db'].s[lang][sclass]:
                    # log.info("checking for {} ({}/{}) in {}"
                    #         "".format(pg,pclass,sclass,self.polygraphs))
                    # Don't show user this on first boot; only when new
                    # characters show up
                    if not firstrun and pg not in self.polygraphs[lang][pclass]:
                        log.info(_("{polygraph} ({pclass}/{sclass}) has no Di/Trigraph setting; "
                        "prompting user for info.").format(polygraph=pg,pclass=pclass,sclass=sclass))
                        if self.askaboutpolygraphs(onboot=True):
                            log.info(_("Asked about polgraphs, but user "
                                        "exited, so exiting {name}"
                                        ).format(name=program['name']))
                            program['taskchooser'].mainwindowis.on_quit()
                        return
        log.info("Di/Trigraph settings seem complete; moving on.")
    def checkinterpretations(self):
        """This sets sane defaults, if not there"""
        if (not hasattr(self,'distinguish')) or (self.distinguish is None):
            self.distinguish={}
        if (not hasattr(self,'interpret')) or (self.interpret is None):
            self.interpret={}
        for var in self.profilelegit+[i+'wd' for i in self.profilesegments]:
            if var in ['C','V']:
                continue
            if ((var not in self.distinguish) or
                (type(self.distinguish[var]) is not bool)):
                self.distinguish[var]=False
            """These defaults are not settable, yet:"""
            if var in ["̀",'ː']: #typically word-forming
                self.distinguish[var]=False
            if var in ['<','=','.']: #typically not word-forming
                self.distinguish[var]=True
        for var in ['NC','CG','CS','VV','VN']:
            if ((var not in self.interpret) or
                (type(self.interpret[var]) is not str) or
                not(1 <=len(self.interpret[var])<= 2)):
                if 'V' in var:
                    self.interpret[var]=var
                else:
                    self.interpret[var]='CC'
        if self.interpret['VV']=='Vː' and self.distinguish['ː']==False:
            self.interpret['VV']='VV'
        log.log(2,"self.distinguish: {}".format(self.distinguish))
    def addtoprofilesbysense(self,sense,ps,profile):
        # log.info("kwargs: {}".format(kwargs))
        # This will die if ps and profile aren't in kwargs:
        setnesteddictval(self.profilesbysense,[sense],ps,profile,addval=True)
        try:
            self.profilesbysense[ps][profile]+=[sense]
        except KeyError:
            try:
                self.profilesbysense[ps][profile]=[sense]
            except KeyError:
                self.profilesbysense[ps]={profile:[sense]}
                # self.profilesbysense[ps][profile]=[sense]
    def addtoformstosearch(self,sense,form,ps,oldform=None):
        setnesteddictval(self.formstosearch,[sense],ps,form,addval=True)
        # log.info("Added {} id={}".format(form,sense.id))
        if oldform:
            try:
                self.formstosearch[ps][oldform].remove(sense)
                log.info(_("Removed {form} ({val})").format(form=form,val=self.formstosearch[ps][form]))
            except ValueError:
                log.error(_("Apparently {sense} isn't under {form}?").format(sense=sense, form=form))
            if not self.formstosearch[ps][oldform]:
                del self.formstosearch[ps][oldform] #don't leave form wo sense
                log.info(_("Deleted key of empty list"))
    def getprofileofentry(self,entry):
        getattr(entry,ftype).textvaluebylang(self.analang)
        #CONTINUE HERE
    def getprofileofsense(self,sense,ps):
        #Convert to iterate over local variables
        # form=sense.textvaluebyftypelang('lc',program['params'].analang())
        form=sense.textvaluebyftypelang(self.profilesbysense['ftype'],
                                        self.profilesbysense['analang'])
        """This adds to self.sextracted, too"""
        if not form:
            return form,None #This is just for logging
        profile=self.rxdict.profileofform(form,ps=ps)
        self.extractsegmentsfromform(form,ps=ps)
        if not set(self.profilelegit).issuperset(profile):
            profile='Invalid'
        setnesteddictval(self.profilesbysense,[sense],ps,profile,addval=True)
        setnesteddictval(self.formstosearch,[sense],ps,form,addval=True)
        sense.cvprofilevalue(self.profilesbysense['ftype'],profile) #store this for future reference
        return form,profile #This is just for logging
    def getprofilesbyps(self,ps):
        # start_time=nowruntime()
        # log.info(_("Processing {ps} syllable profiles").format(ps=ps))
        senses=program['db'].sensesbyps[ps]
        self.sextracted[ps]={} #start over, don't add to if there
        n=self._getprofiles(senses,ps)
        log.info(_("Processed {n} forms to {ps} syllable profiles").format(n=n,ps=ps))
        # logfinished(start_time)
    def _getprofiles(self,senses,ps):
        # This goes fast, even on a large database; do we need the wait?
        n=0
        todo=len(senses)
        # if todo>750:
        #     msg=_("getting profiles for {ps} lexical category").format(ps=ps)
        #     program['taskchooser'].wait(msg)
        for sense in senses:
            n+=1
            # if False: #for testing without backgrounding
            if n%100:
                t = threading.Thread(target=self.getprofileofsense,
                                    args=(sense,ps))
                t.start()
            else:
                form,profile=self.getprofileofsense(sense,ps)
                log.debug(_("{count}: {form} > {profile}").format(count=str(n)+'/'+str(todo),form=form,
                                            profile=profile))
            # if todo>750:
            #     program['taskchooser'].waitprogress(n*100/todo)
        try:
            t.join()
        except UnboundLocalError:
            pass #not backgrounding...
        # if todo>750:
        #     program['taskchooser'].waitdone()
        return n
    def getprofilesbyentry(self):
        for entry in program['db'].entries:
            for sense in entry.senses:
                sense.lxvalue()
    def getprofiles(self):
        """This is called after settings finished init/load from files"""
        #This is for analysis from scratch
        self.profileswdatabyentry={}
        self.profilesbysense={}
        self.profilesbysense['Invalid']=[]
        self.profilesbysense['analang']=program['db'].analang
        self.profilesbysense['ftype']=program['params'].ftype()
        self.profiledguids=[]
        self.formstosearch={}
        self.sextracted={} #don't add to old data
        self.notifyuserofextrasegments() #analang set by now, depends db only
        self.polygraphcheck() #depends only on self.polygraph
        self.checkinterpretations() #checks/sets values for distinguish/interpret
        # log.info("Interpretation: \n{}".format(
        #         '\n'.join([k+': '+self.interpret[k] for k in self.interpret])
        #         ))
        # log.info("Distinguishing: \n{}".format(
        #         '\n'.join([k+': '+str(self.distinguish[k]) for k in self.distinguish])
        #         ))
        self.setupCVrxs() #creates self.s and self.rxdict
        for ps in program['db'].pss: #45s on English db
            self.getprofilesbyps(ps)
        """Do I want this? better to keep the adhoc groups separate"""
        """We will *never* have slices set up by this time; read from file."""
        if hasattr(self,'adhocgroups'):
            for ps in self.adhocgroups:
                for a in self.adhocgroups[ps]:
                    log.debug("Adding {} to {} ps-profile: {}".format(a,ps,
                                                self.adhocgroups[ps][a]))
                    these=[program['db'].sensedict[i]
                            for i in self.adhocgroups[ps][a]]
                    setnesteddictval(self.profilesbysense,these,ps,a)
                    # log.debug("resulting profilesbysense: {}".format(
                    #                         self.profilesbysense[ps][a]))
        else:
            self.adhocgroups={}
        SliceDict(self.adhocgroups,self.profilesbysense)
        if program['slices'].profile():
            self.getscounts()
        self.storesettingsfile(setting='profiledata')
    def extractsegmentsfromform(self,form,ps):
        for s in set(self.profilelegit) & set(self.rxdict.rx):
            # log.info('s: {}; rx: {}'.format(s, self.rxdict.rx[s]))
            # log.info(f"srx output: {self.rxdict.rx[s][0].findall(form)}")
            for i in [j for j in self.rxdict.rx[s][0].findall(form) if j]:
                i=''.join(i).lower() #('o', 'e') > 'oe', no upper case
                # log.info('found polygraph ‘{}’'.format(i))
                setnesteddictval(self.sextracted,1,ps,s,i,addval=True)
    def getscounts(self):
        """This depends on self.sextracted, from getprofiles, so should only
        run when that changes."""
        scount={}
        for ps in self.sextracted: # was program['db'].pss[self.analang]:
            scount[ps]={}
            for s in self.rxdict.rx:
                try:
                    scount[ps][s]=sorted([(x,self.sextracted[ps][s][x])
                        for x in self.sextracted[ps][s]],key=lambda x:x[1],
                                                                reverse=True)
                except KeyError as e:
                    pass
                    # log.info(_("{error} KeyError reading {ps}-{s} from sextracted"
                    #             "").format(error=e,ps=ps,s=s))
        program['slices'].scount(scount) #send to object
    def notifyuserofextrasegments(self):
        analang=program['db'].analang
        if analang not in program['db'].segmentsnotinregexes:
            return
        invalids=program['db'].segmentsnotinregexes[analang]
        ninvalids=len(invalids)
        extras=list(dict.fromkeys(invalids).keys())
        if ninvalids >10 and analang != 'en':
            text=_("Your {lang} database has the following symbols, which are "
                "excluding {count} words from being analyzed: \n{symbols}") \
                .format(lang=analang,count=ninvalids,symbols=extras)
            title=_("More than Ten Invalid Characters Found!")
            self.warning=ErrorNotice(text,title=title)
    def slists(self):
        """This sets up the lists of segments, by types. For the moment, it
        just pulls from the segment types in the lift database."""
        log.info(_("Found db.analangs: {langs}").format(langs=program['db'].analangs))
        log.info(_("Found params analang: {lang}").format(lang=program['params'].analang()))
        self.s={l:{} for l in set(program['db'].analangs+ #analang from database
                                [program['db'].analang]) #inferred analang
                }
        for lang in set(self.s)&set(program['db'].s):
            """These should always be there, no matter what"""
            for sclass in [x for x in program['db'].s[lang]
                                        if 'dg' not in x
                                        and 'tg' not in x
                                        and 'qg' not in x
                                        ]: #Just populate each list now
                try:
                    assert sclass in self.polygraphs[lang]
                    pgthere=[k for k,v in self.polygraphs[lang][sclass].items() if v]
                    log.debug(_("Polygraphs for {lang} in {sclass}: {pgs}").format(lang=lang,sclass=sclass,
                                                                    pgs=pgthere))
                    self.s[lang][sclass]=pgthere
                except (AssertionError,AttributeError):
                    self.s[lang][sclass]=list()
                self.s[lang][sclass]+=program['db'].s[lang][sclass]
                """These lines just add to a C list, for a later regex"""
            log.info(_("Segment lists for {lang} language: {segments}").format(lang=lang,
                                                                segments=self.s[lang]))
        for lang in set(self.s)-set(program['db'].s): #in case no language data
            self.s[lang]=program['db'].hypotheticals
            log.info(_("Segment lists for {lang} language: {segments}").format(lang=lang,
                                                                segments=self.s[lang]))
    def setvalidcharacters(self):
        """These are sent to rxdict, but the top two are also used here"""
        self.profilesegments=['N','G','S','D','C','V','ʔ']
        self.profilelegit=['̃','N','G','S','D','C','Ṽ','V','ʔ','ː',"̀",'=','<','.']
        self.invalidchars=[' ','...',')','(<field type="tone"><form lang="gnd"><text>']
    def addtoCVrxs(self,s):
        """This method is just to add a new grapheme while running, so we
        don't have to restart between C/V changes."""
        if not hasattr(self,'analang'): #in case running after startup
            self.analang=program['db'].analang
        cvt=program['params'].cvt()
        analang=program['db'].analang
        if cvt in ['C', 'V'] and s not in self.s[analang][cvt]:
            self.s[analang][cvt]+=[s]
            # log.info("Compiling rx list: {}".format(self.s[self.analang][cvt]))
            self.rxdict.makeglyphregex(cvt)
            # log.info("Compiled rx list: {}".format(self.rx[cvt]))
    def compileCVrxforsclass(self,sclass):
        # this is now all in regexdict, and isn't called anywhere
        """This does sorting by length to make longest first"""
        analang=program['db'].analang
        # log.info("compileCVrxforsclass RXs: {}".format(self.rx))
    def setupCVrxs(self):
        self.slists() #makes s; depends on polygraphs
        analang=program['db'].analang
        glyphs_present=program['status'].all_groups_verified_anywhere()
        for cvt in glyphs_present:
            if cvt == 'V':
                there=self.s[analang][cvt]
            else:
                there=[i
                        for k in ({'C'}|{ki for ki in self.distinguish
                            if not self.distinguish[ki]})&set(self.s[analang])
                        for j in self.s[analang][k]
                        if k in self.s[analang]
                        for i in j
                    ]
            self.s[analang][cvt].extend(glyphs_present[cvt]-set(there))
        self.rxdict=rx.RegexDict(distinguish=self.distinguish,
                                interpret=self.interpret,
                                sdict=self.s[program['db'].analang],
                                profilelegit=self.profilelegit,
                                invalidchars=self.invalidchars,
                                profilesegments=self.profilesegments)
        #Each glyph variable found in the language gets a regex for each length,
        # plus 0 to find them all together – since we're looking for glyphs.
    def reloadstatusdatabycvtpsprofile(self,**kwargs):
        # This reloads the status info only for current slice
        # These are specified in iteration, pulled from object if called direct
        if kwargs.get('reporttime'):
            start_time=nowruntime()
        kwargs['cvt']=kwargs.get('cvt',program['params'].cvt())
        kwargs['ps']=kwargs.get('ps',program['slices'].ps())
        kwargs['profile']=kwargs.get('profile',program['slices'].profile())
        if kwargs.get('reporttime'):
            log.info(_("Refreshing {cvt} {ps} {profile} status settings from LIFT")
                .format(cvt=kwargs['cvt'],ps=kwargs['ps'],profile=kwargs['profile']))
        checks=program['status'].checks(**kwargs)
        kwargs['store']=False #do below
        for kwargs['check'] in checks:
            # log.info("Working on {}".format(c))
            program['status'].build(**kwargs)
            """this just populates groups and the tosort boolean."""
            self.updatesortingstatus(**kwargs)
        if kwargs.get('reporttime'):
            logfinished(start_time)
    def reloadstatusdatabycvtps(self,**kwargs):
        # This reloads the status info as relevant on a particular page (ps and
        # cvt), so it needs to be iterated over, or done for each page switch,
        # if desired.
        # These are specified in iteration, pulled from object if called by menu
        if kwargs.get('reporttime'):
            start_time=nowruntime()
        kwargs['cvt']=kwargs.get('cvt',program['params'].cvt())
        kwargs['ps']=kwargs.get('ps',program['slices'].ps())
        log.info(_("Refreshing {ps} {cvt} status settings from LIFT").format(
                                                                ps=kwargs['ps'],
                                                                cvt=kwargs['cvt']))
        profiles=program['slices'].profiles(ps=kwargs['ps']) #This depends on ps only
        for kwargs['profile'] in profiles:
            # log.info("Working on {}".format(p))
            self.reloadstatusdatabycvtpsprofile(**kwargs)
        if kwargs.get('store',True):
            self.storesettingsfile(setting='status')
        if kwargs.get('reporttime'):
            logfinished(start_time)
    def verification_keys_in_group_dict(self,x,y):
        """Check for problems before moving on. I don't know why, but mature
        databases develop verification data for groups that no longer exist,
        so we want to exclude those below. to keep from throwing errors, we
        check that the group dictionary as all the keys the verification
        dictionary has"""
        def report(x,y,key=None):
            """Is dict y a subset of dict x, wrt their key hierarchies?"""
            if set(y)-set(x):#not (k in x and k in y):#set(x[k])^set(y[k]):
                text=(f"{set(y)-set(x)} keys not in {key if key else 'dict'}!")
                ErrorNotice(text,wait=True)
                sysshutdown()
            for k in y: #don't care about k in x but not y
                # log.info(f"{k} is in both dictionaries! ({k in x=} {k in y=})")
                if isinstance(x[k],dict) and isinstance(y[k],dict):
                    report(x[k],y[k],k)
        report(x,y)
    def reloadstatusdata(self):
        log.info(_("Refreshing all status settings from LIFT"))
        self.storesettingsfile() #default, not status
        program['db'].load_ps_profiles()
        d=program['db'].annotation_values_by_ps_profile()
        # log.info(f"Found this LIFT file: {program['db'].filename}")
        # log.info(f"Found these LIFT annotations: {d}")
        program['status'].clear_all_groups()
        #The above because the following only modifies current profiles & checks
        k={}
        for k['ps'],profile_dict in d.items():
            for k['profile'],check_dict in profile_dict.items():
                for k['check'],groups in check_dict.items():
                    k['cvt']=program['params'].cvt_of_check(k['check'])
                    groups=[i for i in groups if i]
                    # log.info(f"storing {k} unverified values: {groups}")
                    program['status'].groups(groups, wsorted=True, **k)
        """Verification data should not be read from LIFT. A single lift entry
        may be verified to belong to a particular sort group, without that sort
        group being verified in it's entirety, especially not since another
        word has been added to it.
        """
        """Now remove what didn't get data"""
        program['status'].cull() #this removes empties, and limits done to groups
        if None in program['status']: #This should never be there
            del program['status'][None]
        program['status'].store()
    def categorizebygrouping(self,fn,sense,**kwargs):
        #Don't complain if more than one found:
        check=kwargs.get('check',program['params'].check())
        v=fn(
            program['status'].task(),
            sense,check)
        if v in ['','None',None]: #unlist() returns strings
            # log.info("Marking sense {} tosort (v: {})".format(sense.id,v))
            if not kwargs.get('cvt'): #default, not on iteration
                program['status'].marksensetosort(sense)
            tosort=True
        else:
            # log.info("Marking sense {} sorted (v: {})".format(sense.id,v))
            if not kwargs.get('cvt'): #default, not on iteration
                program['status'].marksensesorted(sense.id)
            if v not in ['NA','ALLOK']:
                self._groups.append(v)
    def updatesortingstatus(self, store=True, **kwargs):
        """This reads LIFT to create lists for sorting, populating lists of
        sorted and unsorted senses, as well as sorted (but not verified) groups.
        So don't iterate over it. Instead, use checkforsensestosort to just
        confirm tosort status"""
        """To get this from the object, use status.tosort(), todo() or done()"""
        # log.info("updatesortingstatus called with store={} and kwargs: {}"
        #         "".format(store,kwargs))
        cvt=kwargs.get('cvt',program['params'].cvt())
        ps=kwargs.get('ps',program['slices'].ps())
        profile=kwargs.get('profile',program['slices'].profile())
        check=kwargs.get('check',program['params'].check())
        kwargs['wsorted']=True #ever not?
        senses=program['slices'].senses(ps=ps,profile=profile)
        # log.info("Working on {} {} {} senses (first 5): {}".format(len(senses),
        #                                                             ps,profile,
        #                                                             senses[:5]))
        log.info(_("Working on {count} sense.ids (first 5): {ids}").format(count=len(senses),
                                                    ids=[i.id for i in senses[:5]]))
        program['status'].renewsensestosort([],[]) #will repopulate
        self._groups=[]
        if cvt == 'T': #we need to be able to iterate over cvt, to rebuild
            fn=Tone.getitemgroup
        else:
            fn=Segments.getitemgroup #This pulls from annotation, not form
        """I think this is the problem why valid groupslike aʲ are getting dropped."""
        """continue here"""
        for sense in senses:
            # log.info("Working on sense {}".format(sense.id))
            self.categorizebygrouping(fn,sense,**kwargs)
        """update 'tosort' status"""
        """update status groups"""
        sorted=set(self._groups)
        program['status'].groups(list(sorted),**kwargs)
        if store:
            # log.info(f"updatesortingstatus storing {kwargs=} {program['status']=}")
            self.storesettingsfile(setting='status')
    def dont_guessanalang(self):
        """Analang should be easily deduceable from the lift file, and/or
        explicit in the settings."""
        self.analang=program['db'].analang
        log.info(_("analang in use: {analang} (If you don't like this, change it in the menus)").format(analang=self.analang))
        return
        #have this call set()?
        """if there's only one analysis language, use it."""
        nlangs=len(program['db'].analangs)
        log.debug(_("Found {n} analangs: {langs}").format(n=nlangs, langs=program['db'].analangs))
        lxwdata=program['db'].nentrieswlexemedata
        lcwdata=program['db'].nentrieswcitationdata
        lxwdatamax=lcwdatamax=None
        for lang in [l for l in lcwdata if lcwdata[l] > 0]:
            if not lcwdatamax or lcwdata[lcwdatamax] < lcwdata[lang]:
                lcwdatamax=lang
        for lang in [l for l in lxwdata if lxwdata[l] > 0]:
            if not lxwdatamax or lxwdata[lxwdatamax] < lxwdata[lang]:
                lxwdatamax=lang
        log.info(_("Most citation data in [{lang}] ({data})").format(lang=lcwdatamax,data=lcwdata))
        log.info(_("Most lexeme data in [{lang}] ({data})").format(lang=lxwdatamax,data=lxwdata))
        if not nlangs:
            errortext=_("There don't seem to be any language forms in your "
            "database!")
            basename=file.getfilenamebase(self.liftfilename)
            parent=file.getfilenamebase(file.getfilenamedir(self.liftfilename))
            if parent == basename and langtags.tag_is_valid(basename):
                self.analang=parent
                errortext+=_("\n(guessing [{lang}]; if that's not correct, exit now "
                            "and fix it!)").format(lang=self.analang)
                log.info(errortext)
            else:
                program['taskchooser'].splash.withdraw()
                errortext+=_("\nFurthermore, your LIFT file doesn't seem to "
                            "indicate your language code: \n{file} "
                            "\nchange that or add some data "
                            "to your database, so I know what language we're "
                            "working on. "
                            "\nOr select a different database on "
                            "the next screen."
                            ).format(file=self.liftfilename)
                e=ErrorNotice(errortext,title=_("Error!"),wait=True)
                file.writefilename() #just clear the default; let user move on
                sysrestart()
        elif nlangs == 1:
            self.analang=program['db'].analangs[0]
            log.debug(_("Only one analang in file; using it: ({lang})").format(
                                                        lang=program['db'].analangs[0]))
            """If there are more than two analangs in the database, check if one
            of the first two is three letters long, and the other isn't"""
        elif nlangs == 2:
            if ((len(program['db'].analangs[0]) == 3) and
                langtags.tag_is_valid(program['db'].analangs[0]) and
                (lcwdatamax == program['db'].analangs[0] or
                    lxwdatamax == program['db'].analangs[0]) and
                (len(program['db'].analangs[1]) != 3)):
                log.debug(_("Looks like I found an iso code with data for "
                                "analang! ({lang})").format(lang=program['db'].analangs[0]))
                self.analang=program['db'].analangs[0] #assume this is the iso code
                self.analangdefault=program['db'].analangs[0] #In case it gets changed.
            elif ((len(program['db'].analangs[1]) == 3) and
                langtags.tag_is_valid(program['db'].analangs[1]) and
                (lcwdatamax == program['db'].analangs[1] or
                    lxwdatamax == program['db'].analangs[1]) and
                    (len(program['db'].analangs[0]) != 3)):
                log.debug(_("Looks like I found an iso code with data for "
                                "analang! ({lang})").format(lang=program['db'].analangs[1]))
                self.analang=program['db'].analangs[1] #assume this is the iso code
                self.analangdefault=program['db'].analangs[1] #In case it gets changed.
            elif (lcwdatamax in program['db'].analangs and
                            langtags.tag_is_valid(lcwdatamax)):
                self.analang=lcwdatamax
                log.debug(_("Neither analang looks like an iso code, taking the "
                "one with most citation data: {langs}").format(langs=program['db'].analangs))
            elif (lxwdatamax in program['db'].analangs and
                            langtags.tag_is_valid(lxwdatamax)):
                self.analang=lxwdatamax
                log.debug(_("Neither analang looks like an iso code, taking the "
                "one with most lexeme data: {langs}").format(langs=program['db'].analangs))
            else:
                self.analang=program['db'].analangs[0]
                log.debug(_("Neither analang looks like an iso code, nor has much"
                "data; taking the first one: {langs}").format(langs=program['db'].analangs))
        else: #for three or more analangs, take the first plausible iso code
            if (lcwdatamax in program['db'].analangs and
                        langtags.tag_is_valid(lxwdatamax)):
                self.analang=lcwdatamax
                log.debug(_("The language with the most citation data looks like "
                "an iso code; using: {langs}").format(langs=program['db'].analangs))
            elif lcwdatamax == lxwdatamax and lxwdatamax in program['db'].analangs:
                self.analang=lxwdatamax
                log.debug(_("The language with the most citation data is also "
                    "the language with the most lexeme data; using: {langs}").format(
                                                            langs=program['db'].analangs))
            elif (lxwdatamax in program['db'].analangs and
                        langtags.tag_is_valid(lxwdatamax)):
                self.analang=lxwdatamax
                log.debug(_("The language with the most lexeme data looks like "
                "an iso code; using: {langs}").format(langs=program['db'].analangs))
            else:
                for n in range(1,nlangs+1): # end with first
                    self.analang=program['db'].analangs[-n]
                    log.debug(_('trying {analang}').format(analang=self.analang))
                    if len(program['db'].analangs[-n]) == 3:
                        log.debug(_("Looks like I found an iso code for "
                                "analang! ({lang})").format(lang=program['db'].analangs[n-1]))
                        break #stop iterating, and keep this one.
        log.info(_("analang guessed: {lang} (If you don't like this, change it in "
                    "the menus)").format(lang=self.analang))
    def guessaudiolang(self):
        nlangs=len(program['db'].audiolangs)
        """if there's only one audio language, use it."""
        if program['db'].audiolang:
            self.audiolang=program['db'].audiolang
        else: #for three or more analangs, take the first plausible iso code
            for n in range(nlangs):
                if self.analang in program['db'].audiolangs[n]:
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
            log.info(_("Only one glosslang!"))
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
            if isinstance(program['taskchooser'].task,WordCollection):
                program['taskchooser'].task.getword() #update UI for glosses
        if 'secondformfield' in self.attrschanged:
            self.attrschanged.remove('secondformfield')
        soundattrs=self.settings['soundsettings']['attributes']
        soundattrschanged=set(soundattrs) & set(self.attrschanged)
        for a in soundattrschanged:
            self.storesettingsfile(setting='soundsettings')
            self.attrschanged.remove(a)
            break
        if self.attrschanged != []:
            log.error(_("Remaining changed attribute! ({attr})").format(
                                                        attr=self.attrschanged))
    def makeparameters(self):
        CheckParameters()
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
        log.info(_("Setting {attr} variable with value: {val} ({old})").format(
                attr=attribute,val=choice,
                old=getattr(self,attribute,"Not Present")))
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
                log.info(_("**Changed {attr}; should restart!**").format(attr=attribute))
            elif refresh == True:
                self.refreshattributechanges()
        else:
            log.debug(_("No change: {attr} == {val}").format(attr=attribute,val=choice))
    def statusisup(self):
        """Use this for when a setting should ignore status frame updates"""
        return (hasattr(program['taskchooser'].mainwindowis,'status') and
                type(program['taskchooser'].mainwindowis.status) is StatusFrame)
    def setsecondformfieldN(self,choice,window=None):
        self.secondformfield[self.nominalps]=self.pluralname=choice
        if self.statusisup():
            program['taskchooser'].mainwindowis.status.updatefields()
        self.attrschanged.append('secondformfield')
        for entry in program['db'].entries:
            entry.plvalue(self.pluralname) # get the right field!
        self.refreshattributechanges()
        if window:
            window.destroy()
    def setsecondformfieldV(self,choice,window=None):
        self.secondformfield[self.verbalps]=self.imperativename=choice
        if self.statusisup():
            program['taskchooser'].mainwindowis.status.updatefields()
        self.attrschanged.append('secondformfield')
        for entry in program['db'].entries:
            """Doesn't do anything??!?"""
            entry.fieldvalue(self.imperativename,program['params'].analang) # get the right field!
        self.refreshattributechanges()
        if window:
            window.destroy()
    def setprofile(self,choice=None,window=None):
        if not choice:
            choice=program['status'].nextprofile()
        program['slices'].profile(choice)
        program['taskchooser'].mainwindowis.status.updateprofile()
        if program['params'].cvt() != 'T': #profiles don't determine tone checks
            #in case checks changed:
            firstcheck=program['status'].updatechecksbycvt()[0]
            if program['params'].check() != firstcheck:
                program['params'].check(firstcheck)
                self.attrschanged.append('check')
        self.attrschanged.append('profile')
        self.refreshattributechanges()
        if window:
            window.destroy()
    def setcvt(self,choice,window=None):
        program['params'].cvt(choice)
        self.attrschanged.append('cvt')
        if self.statusisup():
            program['taskchooser'].mainwindowis.status.updatecvt()
        self.refreshattributechanges()
        if (not hasattr(program['taskchooser'],'task') or
                not program['taskchooser'].task.mainwindow):
            log.info(_("No task, apparently, so not worried about changing cvt"))
        elif isinstance(program['taskchooser'].task,Transcribe):
            log.info(_("Switching Transcribe tasks"))
            newtaskclass=getattr(sys.modules[__name__],'Transcribe'+choice)
            program['status'].makecheckok() #this is intentionally broad: *any* check
            program['taskchooser'].maketask(newtaskclass)
        elif isinstance(program['taskchooser'].task,Sort):
            # log.info("Switching Sort tasks")
            newtaskclass=getattr(sys.modules[__name__],'Sort'+choice)
            program['status'].makecheckok() #this is intentionally broad: *any* check
            program['taskchooser'].maketask(newtaskclass)
        else:
            log.info(_("Not Sorting or Transcribing; chilling with cvt change."))
        if window:
            window.destroy()
    def setanalang(self,choice,window):
        """This is only used when more than one analang exists in the database"""
        log.info(_("Setting Analysis Language to {lang}").format(lang=choice))
        program['params'].analang(choice)
        program['taskchooser'].mainwindowis.status.updateanalang()
        self.attrschanged.append('analang')
        self.refreshattributechanges()
        window.destroy()
        program['taskchooser'].restart()
    def setgroup(self,choice,window):
        log.debug(_("setting group: {group}").format(group=choice))
        program['status'].group(choice)
        if program['params'].cvt() == 'T':
            program['taskchooser'].mainwindowis.status.updatetonegroup()
        else:
            program['taskchooser'].mainwindowis.status.updatecvgroup()
        if isinstance(program['taskchooser'].task,Sort) and (
                hasattr(program['taskchooser'].task,'menu') and
                        program['taskchooser'].task.menu):
            program['taskchooser'].task.menubar.redoadvanced()
        window.destroy()
        log.debug(_("group {group} set: {val}").format(group=choice, val=program['status'].group()))
    def setgroup_comparison(self,choice,window):
        """This doesn't show up on the status window"""
        if hasattr(self,'group_comparison'):
            log.debug(_("group_comparison: {val}").format(val=self.group_comparison))
        self.set('group_comparison',choice,window,refresh=False)
        log.debug(_("group_comparison: {val}").format(val=self.group_comparison))
    def setcheck(self,choice=None,window=None,**kwargs):
        if not choice:
            choice=program['status'].nextcheck(**kwargs)
        program['params'].check(choice)
        if program['params'].cvt() == 'T':
            program['taskchooser'].mainwindowis.status.updatetoneframe()
        else:
            program['taskchooser'].mainwindowis.status.updatecvcheck()
        self.attrschanged.append('check')
        self.refreshattributechanges()
        if window:
            window.destroy()
    def setbuttoncolumns(self,choice,window=None):
        self.buttoncolumns=program['taskchooser'].mainwindowis.buttoncolumns=choice
        if self.statusisup():
            program['taskchooser'].mainwindowis.status.updatebuttoncolumns()
        if window:
            window.destroy()
    def setmaxprofiles(self,choice,window):
        self.maxprofiles=choice
        program['taskchooser'].mainwindowis.status.updatemaxprofiles()
        window.destroy()
    def setmaxpss(self,choice,window):
        self.maxpss=choice
        program['taskchooser'].mainwindowis.status.updatemaxpss()
        window.destroy()
    def setmulticheckscope(self,choice,window):
        self.cvtstodo=program['taskchooser'].task.cvtstodo=choice
        program['taskchooser'].mainwindowis.status.updatemulticheckscope()
        window.destroy()
    def setglosslang(self,choice,window):
        self.glosslangs.lang1(choice)
        program['taskchooser'].mainwindowis.status.updateglosslangs()
        self.attrschanged.append('glosslangs')
        self.refreshattributechanges()
        window.destroy()
    def setglosslang2(self,choice,window):
        if choice:
            self.glosslangs.lang2(choice)
        elif len(self.glosslangs)>1:
            self.glosslangs.pop(1) #if lang2 is None
        program['taskchooser'].mainwindowis.status.updateglosslangs()
        self.attrschanged.append('glosslangs')
        self.refreshattributechanges()
        window.destroy()
    def setparserasklevel(self,choice,window):
        program['taskchooser'].parser.asklevel(choice)
        program['taskchooser'].mainwindowis.status.updateparserasklevel()
        window.destroy()
    def setparserautolevel(self,choice,window):
        program['taskchooser'].parser.autolevel(choice)
        program['taskchooser'].mainwindowis.status.updateparserautolevel()
        window.destroy()
    def setps(self,choice,window):
        program['slices'].ps(choice)
        program['taskchooser'].mainwindowis.status.updateps()
        self.attrschanged.append('ps')
        self.refreshattributechanges()
        window.destroy()
    def setexamplespergrouptorecord(self,choice,window):
        self.set('examplespergrouptorecord',choice,window)
    def localize_langnames(self):
        self.languagenames={i:_(self.languagenames[i]) for i in self.languagenames}
    def langnames(self,langs={}):
        """This is for getting the prose name for a language from a code."""
        """It should ultimately use a xyz.ldml file, produced (at least)
        by WeSay, but for now is just a dict."""
        log.info(_("Setting up language names"))
        #ET.register_namespace("", 'palaso')
        ns = {'palaso': 'urn://palaso.org/ldmlExtensions/v1'}
        node=None
        if not hasattr(self,'languagenames'):
            self.languagenames={}
        #return localized strings to English, so they can localize again
        self.languagenames.update({'fr':"French", 
                                'en':"English",
                                'es':"Spanish",
                                'ar':"Arabic",
                                'zh':"Chinese",
                                'pt':"Portuguese",
                                'id':"Indonesian",
                                'ind':"Indonesian",
                                'ha':"Hausa",
                                'hau':"Hausa",
                                'swc':"Congo Swahili",
                                'swh':"Swahili",
                                'gnd':"Zulgo",
                                'fub':"Fulfulde",
                                'bfj':"Chufie’"})
        self.localize_langnames()
        if hasattr(self,'adnlangnames') and self.adnlangnames:
            d.update(self.adnlangnames) #from settings
        # print(type(self.analang),type(program['db'].analangs),type(program['db'].glosslangs))
        if not langs:
            langs=program['db'].analangs+program['db'].glosslangs
            if hasattr(self,'analang'):
                langs.append(self.analang)
        langs=set(langs)
        self.languagenames.update({i:_("Language with code [{code}]").format(code=i) 
                                    for i in langs
                                    if i not in self.languagenames
                                    })
        # for xyz in langs+program['interfacelangs']:
        #     default=_("Language with code [{code}]").format(code=xyz)
        #     # log.info(' '.join('Looking for language name for',xyz))
        #     setnesteddictobjectval(self,'languagenames',
        #                             d.get(xyz,default),
        #                             xyz)
        """This provides an ldml node implement this some day"""
        #log.info(' '.join(tree.nodes.find(f"special/palaso:languageName", namespaces=ns)))
        #nsurl=tree.nodes.find(f"ldml/special/@xmlns:palaso")
        """This doesn't seem to be working; I should fix it, but there
        doesn't seem to be reason to generalize it for now."""
        # tree=ET.parse(self.languagepaths[xyz])
        # tree.nodes=tree.getroot()
        # node=tree.nodes.find(f"special/palaso:languageName", namespaces=ns)
        # if node is not None:
        #     self.languagenames[xyz]=node.get('value')
        #     log.info(' '.join('found',self.languagenames[xyz]))
        # if not hasattr(self,'adnlangnames') or self.adnlangnames is None:
        #     self.adnlangnames={}
        # if (hasattr(self,'adnlangnames') and
        #         self.adnlangnames and
        #         xyz in self.adnlangnames and
        #         self.adnlangnames[xyz]):
        #     self.languagenames[xyz]=self.adnlangnames[xyz]
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
        self.setvalidcharacters()
        # self.settingsfilecheck()
        self.settingsinit() #init, clear, fields
        self.loadsettingsfile()
        self.loadsettingsfile(setting='profiledata')
        """I think I need this before setting up regexs"""
        self.langnames(program['interfacelangs'])
        if hasattr(taskchooser,'analang'): #i.e., new file
            self.analang=taskchooser.analang #I need to keep this alive until objects are done
            self.storesettingsfile() #write analang to file
        log.info(_("Settings initialized"))
    def post_lift_init(self):
        """These settings require the LIFt db be up and parsed already"""
        self.dont_guessanalang() #needed for regexs
        if not self.analang:
            log.error(_("No analysis language; exiting."))
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
        self.attrs_moved_to_object=set()
        self.settingsobjects() #should do this more; can be redone!
        self.trackuntrackedfiles()
        if not self.buttoncolumns:
            self.setbuttoncolumns(1)
        # these two make the objects
        self.loadsettingsfile(setting='status')
        self.loadsettingsfile(setting='toneframes')
        self.loadsettingsfile(setting='adhocgroups')
        self.loadsettingsfile(setting='alphabet')
        self.makeeverythingok()
        """The following might be OK here, but need to be OK later, too."""
        # """The following should only be done after word collection"""
        # if self.taskchooser.donew['collectionlc']:
        #     self.ifcollectionlc()
        self.attrschanged=[]
        log.info(_("Settings (Post lift) initialized"))
class TaskDressing(HasMenus,ui.Window):
    """This Class covers elements that belong to (or should be available to)
    all tasks, e.g., menus and button appearance."""
    def taskicon(self):
        return program['theme'].photo['icon'] #default
    def tasktitle(self):
        return _("Unnamed {name} Task ({type})").format(name=program['name'],
                                                type=type(self).__name__)
    def _taskchooserbutton(self):
        if isinstance(self,TaskChooser) and not self.showreports:
            if self.datacollection:
                text=_("Analyze & Decide")
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
    def shutdowntask(self):
        program['taskchooser'].task=self # in case this hasn't been set yet
        self.withdraw()
        program['taskchooser'].gettask()
    def mainlabelrelief(self,relief=None,refresh=False,event=None):
        #set None to make this a label instead of button:
        reliefs=["raised", "groove", "sunken", "ridge", "flat"]
        if self.mainrelief and self.mainrelief in reliefs:
            program['taskchooser'].mainreliefnext=\
            program['taskchooser'].task.mainreliefnext=\
            self.mainreliefnext=reliefs[(reliefs.index(self.mainrelief)+1
                                                            )%len(reliefs)]
        log.info(_("setting button relief to {relief}, with refresh={refresh}").format(relief=relief,
                                                                    refresh=refresh))
        # None "raised" "groove" "sunken" "ridge" "flat"
        self.status.mainrelief=\
        program['taskchooser'].mainrelief=\
        program['taskchooser'].task.mainrelief=\
        self.mainrelief=relief
    def _showbuttons(self,event=None):
        todo=getattr(self,'mainreliefnext','flat')
        self.mainlabelrelief(relief=todo,refresh=True)
        program['taskchooser'].mainwindowis.status.makeui()
        self.setcontext()
    def _hidebuttons(self,event=None):
        self.mainlabelrelief(relief=None,refresh=True)
        program['taskchooser'].mainwindowis.status.makeui()
        self.setcontext()
    def correlatemenus(self):
        """I don't think I want this. Rather, menus must always be asked for."""
        log.info(_("Menus: {menu}; {chooser_menu} (chooser)").format(menu=self.menu,chooser_menu=program['taskchooser'].menu))
        if hasattr(self,'task'):
            log.info(_("Menus: {menu}; {task_menu} (task)").format(menu=self.menu,task_menu=self.task.menu))
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
    def _hidedetails(self):
        # log.info("Hiding group names")
        program['settings'].set('showdetails', False, refresh=True)
        program['taskchooser'].mainwindowis.status.maybeboard()
        self.setcontext()
    def _showdetails(self):
        # log.info("Showing group names")
        program['settings'].set('showdetails', True, refresh=True)
        program['taskchooser'].mainwindowis.status.maybeboard()
        self.setcontext()
    def setcontext(self,context=None):
        if self.exitFlag.istrue() or not self.winfo_exists():
            return
        self.context.menuinit() #This is a ContextMenu() method
        if not hasattr(self,'menu') or not self.menu:
            self.context.menuitem(_("Show Menus"),self._setmenus)
        else:
            self.context.menuitem(_("Hide Menus"),self._removemenus)
        if hasattr(program['taskchooser'],'mainrelief') and not program['taskchooser'].mainrelief:
            self.context.menuitem(_("Show Buttons"), self._showbuttons)
        else:
            self.context.menuitem(_("Hide Buttons"), self._hidebuttons)
        if hasattr(self,'fontthemesmall') and not self.fontthemesmall:
            self.context.menuitem(_("Smaller Fonts"),self.setfontssmaller)
        else:
            self.context.menuitem(_("Larger Fonts"),self.setfontsdefault)
        if getattr(program['settings'], 'showdetails'):
            self.context.menuitem(_("Hide details"),self._hidedetails)
        else:
            self.context.menuitem(_("Show details"),self._showdetails)
    def maketitle(self):
        title=_("{name} Dictionary and Orthography Checker: {task}").format(
                                            name=program['name'],task=self.tasktitle())
        if program['theme'].name != 'greygreen':
            log.info(_("Using theme ‘{theme}’ on {task}.").format(theme=program['theme'].name,
                                                        task=self.tasktitle()))
            title+=f' ({program['theme'].name})'
        self.title(title)
        t=ui.Label(self.frame, font='title',
                text=self.tasktitle(),
                row=0, column=0, columnspan=2)
        tasks=_("Tasks")
        t.tt=ui.ToolTip(t,text=_("click on the task you want to do"))
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
                log.info(_("Didn't find {attr} in {settings}").format(attr=attr,settings=program['settings']))
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
        """There are two threads of this method running or waiting at all times,
        one for the taskchooser and another for the task. this should probably
        be converted to a more tkinter native update, like with
        StringVar().set()"""
        if 'slices' not in program:
            # slices is done by taskchooser on boot, but later
            # don't update both taskchooser and task, just the visible one
            self.trystatusframelater(dict)
            return #don't die, but don't do this until ready, either
        dictnow={
                # 'mainrelief':self.mainrelief,
                # 'showdetails':program['settings'].showdetails, #attr, not task.method
                'self.fontthemesmall':self.fontthemesmall,
                # 'buttonkwargs':self.dobuttonkwargs(),
                # 'iflang':program['settings'].interfacelangwrapper(),
                # 'analangname':program['settings'].languagenames[self.analang],
                # 'analang':program['params'].analang(),
                # 'glang1':self.glosslangs.lang1(),
                # 'glang2':self.glosslangs.lang2(),
                # 'secondformfield':str(program['settings'].secondformfield),
                # 'maxprofiles':program['settings'].maxprofiles,
                # 'maxpss':program['settings'].maxpss
                }
        # if 'slices' in program:
        dictnow.update({
            # 'cvt':program['params'].cvt(),
            # 'check':program['params'].check(),
            # 'ps':program['slices'].ps(),
            # 'profile':program['slices'].profile(),
            # 'group':program['status'].group(),
            'tableiteration':self.tableiteration,
            })
        if isinstance(self,Multicheck):
            dictnow.update({'cvtstodo':self.task.cvtstodo})
        if isinstance(self,Parse):
            try:
                dictnow.update({
                    # 'parserasklevel':self.parser.ask,
                    # 'parserautolevel':self.parser.auto,
                    'sense.id':self.task.sensetodo,
                    })
            except AttributeError as e:
                log.info(_("looks like the parser isn't up yet ({error})").format(error=e))
        """Call this just once. If nothing changed, wait; if changes, run,
        then run again."""
        if dict == dictnow:
            # log.info("No dict changes; no updating the UI: {}".format(dictnow))
            self.trystatusframelater(dictnow)
            return
        log.info(_("Dict changes; checking attributes and updating the UI."))
        # log.info(f"dictori: {dict}")
        # log.info(f"dictnow: {dictnow}")
        if program['taskchooser'].donew['collectionlc']:
            program['settings'].makeeverythingok()
        #This will probably need to be reworked
        if self.exitFlag.istrue():
            return
        hidewhileworking=self.winfo_viewable()
        status=StatusFrame(self.frame, self,
                            relief=self.mainrelief,
                            row=1, column=0, sticky='nw')
        if hidewhileworking:
            self.withdraw()
        if hasattr(self,'status') and self.status.winfo_exists():
            self.status.destroy()
        self.status=status
        self.status.dogrid()
        if hidewhileworking:
            self.deiconify()
        program['settings'].storesettingsfile()
        self.makestatusframe(dictnow) #this method
        log.info(_("{type} makestatusframe iteration finished").format(type=type(self)))
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
                t+=_("\n=> You are no longer distinguishing {items}.").format(
                                    items=unlist([x.replace('wd','#') for x in d]))
            i=[y for y in changed.keys() if changed[y][1] is not False]
            if len(i) >0:
                t+=_("\n=> Your interpretation of {items} changed.").format(
                                                            items=unlist(i))
            t+=_("\nHere is the full info, in form setting: (from, to): {changed}."
                    "").format(changed=changed)
            t+=_("\n\nAnywhere you have sorted a group based on your "
            "old interpretation settings, you should sort/verify "
            "that data again, as there is a possiblity that "
            "you have mixed unrelated groups.").format(changed=changed)
            ui.Label(w.frame,text=t,wraplength=int(
                        self.frame.winfo_screenwidth()/2)).grid(row=1,column=0)
            for n,ps in enumerate(program['slices'].pss()):
                i=[x for x in program['slices'].profiles(ps)
                                    if set(d).intersection(set(x))]
                if i:
                    p=_("{ps} Profiles to check: {profiles}").format(ps=ps,profiles=i)
                    log.info(p)
                    l=ui.Label(w.frame,text=p,row=2+n,column=0)
                    l.wrap()
            ok=Object(value=False)
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
                            log.error(_("Changed to value ({new}) doesn't match "
                            "current setting for ‘{setting}’: {current}").format(new=changed[s][1],
                                                        setting=s,current=self.distinguish[s]))
                    elif s in program['settings'].interpret:
                        if program['settings'].interpret[s]==changed[s][1]:
                            program['settings'].interpret[s]=changed[s][0] #(oldvar,newvar):
                        else:
                            log.error(_("Changed to value ({new}) doesn't match "
                            "current setting for ‘{setting}’: {current}").format(new=changed[s][1],
                                                        setting=s,current=self.interpret[s]))
            r=True #only false if changes made, and user exits notice
            changed={}
            for typ in ['distinguish', 'interpret']:
                for s in getattr(program['settings'],typ):
                    if s in options.vars: # and s in getattr(program['settings'],typ):
                        newvar=options.vars[s].get()
                        oldvar=getattr(program['settings'],typ)[s]
                        if oldvar != newvar:
                            changed[s]=(oldvar,newvar)
                            getattr(program['settings'],typ)[s]=newvar
            # log.debug('self.distinguish: {}'.format(program['settings'].distinguish))
            # log.debug('self.interpret: {}'.format(program['settings'].interpret))
            if changed:
                # log.info('There was a change; we need to redo the analysis now.')
                log.info(_('The following changed (from,to): {changed}').format(changed=changed))
                r=notice(changed)
                if r:
                    self.runwindow.on_quit()
                    program['settings'].storesettingsfile(setting='profiledata')
                    program['taskchooser'].restart()
                else:
                    undo(changed)
            else:
                self.runwindow.on_quit()
        def buttonframeframe(s):
            f=ui.Frame(self.runwindow.scroll.content,
                        row=options.get('r'),
                        column=options.get('c'),
                        sticky='ew', padx=options.padx, pady=options.pady)
            bffl=ui.Label(f,text=textdict[s],justify=ui.LEFT,
                            anchor='c',
                            row=1,column=0,
                            sticky='ew',
                            padx=options.padx,
                            pady=options.pady)
            bffl.wrap()
            for opt in optdict[s]:
                bffrb=ui.RadioButtonFrame(f,
                                        horizontal=True,
                                        variable=options.vars[s],
                                        optionlist=optdict[s],
                                        row=1,column=1)
            options.next('r')
        def exsframe(x):
            text=_("In your data, {item} includes {examples}").format(item=x,examples=', '.join(exsdict[x]))
            f=ui.Frame(self.runwindow.scroll.content,
                        row=options.get('r'),
                        column=options.get('c'),
                        sticky='ew')
            bffl=ui.Label(f,text=text,
                            font='read',
                            anchor='c',
                            row=1,column=options.column,
                            sticky='ew',
                            padx=options.padx,
                            pady=options.pady)
            bffl.wrap()
            options.next('r')
        self.getrunwindow()
        program['settings'].checkinterpretations()
        analang=program['params'].analang()
        options=Options(r=0,padx=50,pady=0,c=0,vars={},frames={})
        for s in program['settings'].distinguish: #Should be already set.
            options.vars[s] = ui.BooleanVar()
            options.vars[s].set(program['settings'].distinguish[s])
        for s in program['settings'].interpret: #This should already be set, even by default
            options.vars[s] = ui.StringVar()
            options.vars[s].set(program['settings'].interpret[s])
        """Page title and instructions"""
        self.runwindow.title(_("Set Parameters for Segment Interpretation"))
        mwframe=self.runwindow.frame
        title=_("Interpret {lang} Segments"
                ).format(lang=program['settings'].languagenames[analang])
        titl=ui.Label(mwframe,text=title,font='title',
                justify=ui.LEFT,anchor='c',
                row=options.get('r'), column=options.get('c'),
                sticky='ew', padx=options.padx, pady=10)
        options.next('r')
        text=_("Here you can view and set parameters that change how {name} "
        "interprets {lang} segments (consonant and vowel glyphs/characters)"
                ).format(name=program['name'],lang=program['settings'].languagenames[analang])
        instr=ui.Label(mwframe,text=text,justify=ui.LEFT,anchor='c',
                    row=options.get('r'), column=options.get('c'),
                    sticky='ew', padx=options.padx, pady=options.pady)
        instr.wrap()
        """The rest of the page"""
        self.runwindow.scroll=ui.ScrollingFrame(mwframe,row=2,column=0)
        # log.debug('self.distinguish: {}'.format(program['settings'].distinguish))
        # log.debug('self.interpret: {}'.format(program['settings'].interpret))
        """I considered offering these to the user conditionally, but I don't
        see a subset of them that would only be relevant when another is
        selected. For instance, a user may NOT want to distinguish all Nasals,
        yet distinguish word final nasals. Or CG sequences, but not other G's
        --or distinguish G, but leave as CG (≠C). So I think these are all
        independent boolean selections."""
        if analang in program['db'].s:
            vars=[k for k in program['db'].s[analang].keys()
                    if not 'dg' in k
                    if not 'tg' in k
                    if not 'qg' in k
                    ]
            log.info(_("Variable keys to check: {vars}").format(vars=vars))
        else:
            ErrorNotice(_("Something happened! "
                        "(language not keyed in segment dictionary)"))
            return
        exsdict={}
        for var in vars:
            # log.info("Getting examples of {}".format(var))
            exsdict[var]=program['db'].s[analang][var]
            if var in program['settings'].polygraphs[analang]:
                exsdict[var]+=[k for k,v in
                        program['settings'].polygraphs[analang][var].items()
                        if program['settings'].polygraphs[analang][var][k]
                                ]
            # log.info("Examples of {}: {}".format(var,exsdict[var]))
        textdict={'ʔ':_('Distinguish glottal stops (ʔ) '
                        'initially and medially?'),
                'ʔwd':_('Distinguish glottal stops word finally (ʔ#)?'),
                'N':_('Distinguish Nasals (N) initially and medially?'),
                'Nwd':_('Distinguish Nasals word finally (N#)?'),
                'NC':_('How to interpret Nasal-Consonant (NC) sequences?'),
                'D':_('Distinguish likely depressor consonants (D) '
                        'initially and medially?'),
                'Dwd':_('Distinguish likely depressor consonants word finally '
                        '(D#)?'),
                'G':_('Distinguish Glides (G) initially and medially?'),
                'Gwd':_('Distinguish Glides word finally (G#)?'),
                'CG':_('How to interpret Consonant-Glide (CG) sequences?'),
                'S':_('Distinguish Non-Nasal/Glide Sonorants (S) '
                        'initially and medially?'),
                'Swd':_('Distinguish Non-Nasal/Glide Sonorants word finally '
                        '(S#)?'),
                'CS':_('How to interpret Consonant-Sonorant (CS) sequences?'),
                'VN':_('How to interpret Vowel-Nasal (VN) sequences? '
                        '(after NC interpretation above)'),
                'VV':_('How to interpret the *same* vowel letter twice '
                        'in a row (VV)? ')
                }
        optdict={'ʔ':[(True,'ʔ≠C'),(False,'ʔ=C')],
                'ʔwd':[(True,'ʔ#≠C#'),(False,'ʔ#=C#')],
                'N':[(True,'N≠C'),(False,'N=C')],
                'Nwd':[(True,'N#≠C#'),(False,'N#=C#')],
                'NC':[('NC','NC=NC (≠C, ≠CC)'),
                        ('C','NC=C (≠NC, ≠CC)'),
                        ('CC','NC=CC (≠NC, ≠C)')
                        ],
                'D':[(True,'D≠C'),(False,'D=C')],
                'Dwd':[(True,'D#≠C#'),(False,'D#=C#')],
                'G':[(True,'G≠C'),(False,'G=C')],
                'Gwd':[(True,'G#≠C#'),(False,'G#=C#')],
                'CG':[('CG','CG=CG (≠C, ≠CC)'),
                        ('C','CG=C (≠CG, ≠CC)'),
                        ('CC','CG=CC (≠CG, ≠C)')],
                'S':[(True,'S≠C'),(False,'S=C')],
                'Swd':[(True,'S#≠C#'),(False,'S#=C#')],
                'CS':[('CS','CS=CS (≠C, ≠CC)'),
                        ('C','CS=C (≠CS, ≠CC)'),
                        ('CC','CS=CC (≠CS, ≠C)')],
                'VN':[('VN','VN=VN (≠Ṽ)'), ('Ṽ','VN=Ṽ (≠VN)')],
                'VV':[('VV','VV=VV (≠V)'), ('V','VV=V (≠VV)')]
                }
        exsframe('C')
        for var in [i for i in vars if i not in ['C','V','VN']
                                    if i in exsdict and exsdict[i]]:
            # log.info("Doing var {}".format(var))
            exsframe(var)
            todo=[i for i in textdict if var in i]
            # log.info("Doing vars {}".format(todo))
            for var in todo:
                buttonframeframe(var)
        exsframe('V')
        todo=[i for i in textdict if 'V' in i]
        for v in todo:
            buttonframeframe(v)
        """Submit button, etc"""
        self.runwindow.frame2d=ui.Frame(mwframe,
                                        row=3,
                                        column=options.get('c'),
                                        sticky='e', padx=options.padx,
                                        pady=options.pady)
        sub_btn=ui.Button(self.runwindow.frame2d, text=_('Use these settings'),
                          command = submitform,
                          row=0,column=1,sticky='nw',
                          pady=options.pady)
        nbtext=_("If you make changes, this button==> \nwill "
                "restart the program to reanalyze your data.")
        sub_nb=ui.Label(self.runwindow.frame2d, text = nbtext,
                        anchor='e',
                        row=0,column=0,sticky='e',
                        pady=options.pady)
        self.runwindow.waitdone()
    def getinterfacelang(self,event=None):
        log.info(_("Asking for interface language..."))
        azt=program['name']
        window=ui.Window(self, title=_('Select Interface Language'))
        ui.Label(window.frame, text=_('What language do you want {name} '
                                'to address you in?').format(name=azt)
                ).grid(column=0, row=0)
        options=[{'code':i,'name':program['settings'].languagenames[i]}
                for i in program['interfacelangs']]
        log.info(_("asking with these options: {options}").format(options=options))
        ui.ButtonFrame(window.frame,
                                optionlist=options,
                                command=program['settings'].interfacelangwrapper,
                                window=window,
                                column=0, row=1
                                )
    def getanalangname(self,event=None):
        log.info(_("this sets the language name"))
        def submit(event=None):
            if namevar.get():
                program['settings'].languagenames[self.analang]=namevar.get()
                #This stores to file:
                setnesteddictobjectval(program['settings'],'adnlangnames',
                                    namevar.get(),self.analang)
            else:
                if self.analang in program['settings'].languagenames:
                    del program['settings'].languagenames[self.analang]
                if self.analang in program['settings'].adnlangnames:
                    del program['settings'].adnlangnames[self.analang]
                program['settings'].langnames([self.analang]) #refreshes w/above
            program['settings'].storesettingsfile()
            program['taskchooser'].mainwindowis.status.updateanalang() #ui
            window.destroy()
        window=ui.Window(self,title=_('Enter Analysis Language Name'))
        curname=program['settings'].languagenames[self.analang]
        defaultname=_("Language with code [{code}]").format(code=self.analang)
        t=_("How do you want to display the name of {name}").format(name=curname)
        namevar=ui.StringVar()
        log.info(f"{curname} = {defaultname}? {curname == defaultname}")
        if curname != defaultname:
            t+=_(", with ISO 639-3 code [{code}]").format(code=self.analang)
            namevar.set(curname)
        t+='?' # _("Language with code [{}]").format(xyz)
        ui.Label(window.frame,text=t,row=0,column=0,sticky='e',columnspan=2)
        name = ui.EntryField(window.frame,text=namevar,
                            row=1,column=0,
                            sticky='e')
        name.focus_set()
        name.bind('<Return>',submit)
        ui.Button(window.frame,text=_('OK'),cmd=submit,row=1,column=1,sticky='w')
    def getanalang(self,event=None):
        if len(program['db'].analangs) <2: #The user probably wants to change display.
            self.getanalangname()
            return
        log.info(_("this sets the language"))
        # fn=inspect.currentframe().f_code.co_name
        window=ui.Window(self,title=_('Select Analysis Language'))
        if program['db'].analangs is None :
            ui.Label(window.frame,
                          text=_('Error: please set Lift file first! ({file})').format(
                          file=program['db'].filename)
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
        for lang in set(program['db'].glosslangs)|set(
                                            program['settings'].glosslangs[1:]):
            langs.append({'code':lang,
                            'name':program['settings'].languagenames[lang]})
        if program['settings'].glosslangs.lang2():
            langs.append({'code':None,
                    'name':_('just use {name}').format(name=program['settings'].languagenames[
                                    program['settings'].glosslangs.lang2()])})
        buttonFrame1=ui.ButtonFrame(window.frame,
                                 optionlist=langs,
                                 command=program['settings'].setglosslang,
                                 window=window,
                                 column=0, row=4
                                 )
    def getglosslang2(self,event=None):
        window=ui.Window(self,title=_('Select Second Gloss Language'))
        text=_('What other language do you want to use for glosses?')
        ui.Label(window.frame, text=text, column=0, row=1)
        langs=list()
        for lang in set(program['db'].glosslangs)|set(program['settings'].glosslangs[:1]):
            if lang == program['settings'].glosslangs[0]:
                continue
            langs.append({'code':lang,
                            'name':program['settings'].languagenames[lang]})
        langs.append({'code':None,
                    'name':_('just use {name}').format(name=program['settings'].languagenames[
                                    program['settings'].glosslangs.lang1()])})
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
            if cvt in ['CV','VC'] and (isinstance(self.task,Sort) or
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
            log.info(_("Evidently there isn't a parser running ({error})").format(error=e))
            return
    def getparserasklevel(self,event=None):
        log.info(_("Asking for parserasklevel..."))
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
        log.info(_("Asking for parserautolevel..."))
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
        log.info(_("Asking for ps..."))
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
        log.info(_("Asking for profile..."))
        # self.refreshattributechanges()
        ps=program['slices'].ps()
        if not ps:
            text=(_("No Grammatical Category? ")+""
                    f" ({list(program['settings'].profilesbysense)})")
            ErrorNotice(text, parent=self, wait=True)
        elif program['settings'].profilesbysense[ps] is None: #likely never happen...
            text=_('Error: please set Grammatical category with profiles '
                    'first! (not {ps})').format(ps=ps)
            ErrorNotice(text, parent=self, wait=True)
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
                log.error(_("No profiles of {type} type found!").format(type=kwargs))
            # log.info("count types: {}, {}".format(type(profilecounts),
            #                                         type(profilecountsAdHoc)))
            window=ui.Window(self,title=_('Select Syllable Profile'))
            ui.Label(window.frame, text=_('What ({ps}) syllable profile do you '
                                    'want to work with?').format(ps=ps)
                                    ).grid(column=0, row=0)
            optionslist = [{'code':x,'description':profilecounts[(x,ps)]} for x in profiles]
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
        program['taskchooser'].mainwindowis.status.updatesensetodo()
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
                if k.unformatted(self.analang,self.glosslangs
                                ).startswith(choice)]
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
        kcounts=collections.Counter([k.unformatted(self.analang,
                                                    self.glosslangs)[0]
                                    for k in senses
                                    if k.unformatted(self.analang,
                                                    self.glosslangs)
                                    ]
                                    ).most_common()
        if len(kcounts)<15: #When few choices, use first two letters
            kcounts=collections.Counter([k.unformatted(self.analang,
                                                    self.glosslangs)[:2]
                                        for k in senses
                                        if k.unformatted(self.analang,
                                                    self.glosslangs)
                                        ]
                                        ).most_common()
        letters=[{'code':k,'description':v} for k,v in kcounts]
        # log.info("Counts: {}".format(kcounts))
        # letters=list([(k,k,v) for k,v in kcounts])
        log.info("letters: {}".format(letters))
        if not letters:
            log.info(_("No senses; sort something?"))
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
            log.info(_("setting {custom} (not {other})").format(custom=custom.get(), other=othername))
            if custom.get() == othername:
                text=_("That name is already used!")
                log.error(text)
                self.errorlabel['text']=text
                return
            setcmd(custom.get())
            window.on_quit()
        title=_('Make Custom Second Form Field for {ps}').format(ps=ps)
        window=ui.Window(self,title=title)
        #should never be othername
        l=ui.Label(window,
                text=_("What field name do you want to use for {ps} words?"
                        ).format(ps=ps),
                row=0,column=0)
        custom=ui.StringVar()
        formfield = ui.EntryField(window, render=True,
                                    text=custom,
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
        window.wait_window()
    def getsecondformfield(self,ps,opts,othername,setcmd,other=False):
        """'other' is used when fields already present in the database
        do not include a good option. 'Othername' is used to exclude another
        grammatical category, e.g., verb fields for a noun second form.
        If there are no such fields in the db (e.g., if you just started
        a new db for word collection), the user will go straight to selecting
        from default options, or providing a custom name for the new field"""
        def getother():
            """Current db fields aren't enough, ask for default or custom"""
            window.destroy()
            self.getsecondformfield(ps=ps,
                                    opts=opts,
                                    othername=othername,
                                    setcmd=setcmd,
                                    other=True)
        def getcustom():
            """Current db fields and custom names aren't enough, get custom"""
            window.destroy()
            self.getcustomsecondformfield(ps=ps,
                                    # opts=opts,
                                    othername=othername,
                                    setcmd=setcmd,
                                    # other=True
                                    )
        log.info(_("Asking for ‘{ps}’ second form field...").format(ps=ps))
        try:
            assert other == False
            othernames=[i for i in program['db'].fieldnames[self.analang]
                    if i != othername and i not in ['lc','lx']]
        except (KeyError,AssertionError):
            othernames=[]
        if othernames:
            if len(othernames)-1:
                text=_("Select a database field "
                        "to use for second forms of ‘{ps}’ words").format(ps=ps)
                otherbuttontext=_("None of these; make a new field")
            else:
                text=_("Select the ‘{field}’ database field "
                        "for second forms of ‘{ps}’ words").format(field=othernames[0],ps=ps)
                otherbuttontext=_("No; make a new field")
            cmd=getother
            optionslist=othernames
        else:
            setcmd(opts[0])
            # ErrorNotice(_("No suitable database fields were found for second "
            #             f"forms of ‘{ps}’ words; using ‘{opts[0]}’."))
            return
            # text=_("No suitable database fields were found; what name "
            #         f"do you want to use for second forms of ‘{ps}’ words?")
            # otherbuttontext=_("None of these work; make my own field")
            # cmd=getcustom
            # optionslist=opts
        title=_('Select Second Form Field for {ps}').format(ps=ps)
        window=ui.Window(self,title=title)
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
        otherbutton=ui.Button(buttonFrame1.content,
                            text=otherbuttontext,
                            column=0, row=1,
                            cmd=cmd
                            )
        if self.winfo_viewable():
            self.withdraw()
            window.wait_window(window)
            self.deiconify()
        else:
            window.wait_window(window)
    def getmulticheckscope(self,event=None):
            log.info(_("Asking for multicheckscope..."))
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
        """Not called anywhere?"""
        if program['settings'].nominalps not in program['settings'].secondformfield:
            self.getsecondformfieldN()
        if program['settings'].verbalps not in program['settings'].secondformfield:
            self.getsecondformfieldV()
        return (program['settings'].secondformfield[program['settings'].verbalps],
                program['settings'].secondformfield[program['settings'].nominalps])
    def getbuttoncolumns(self,event=None):
        log.info(_("Asking for number of button columns..."))
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
        log.info(_("this sets the check"))
        log.info(_("Getting the check name..."))
        checks=program['status'].checks(**kwargs)
        self.withdraw()
        window=ui.Window(self,title=_('Select Check'))
        window.withdraw()
        if not checks:
            if program['params'].cvt() == 'T':
                btext=_("Define a New Tone Frame")
                text=_("You don't seem to have any tone frames set up.\n"
                "Click '{button}' below to define a tone frame. \nPlease "
                "pay attention to the instructions, and if \nthere's anything "
                "you don't understand, or if you're not \nsure what a tone "
                "frame is, please ask for help. \nWhen you are done making "
                "frames, click ‘Exit’ to continue.").format(button=btext)
                cmd=lambda w=window: self.addframe(window=w)
            else:
                btext=_("Return to {name}, to fix settings").format(name=program['name'])
                text=_("I can't find any checks for type {cvt}, ps {ps}, profile {profile}."
                        " Probably that means there is a problem with your "
                        " settings, or with your syllable profile analysis"
                        "").format(cvt=cvt,ps=ps,profile=profile)
                cmd=window.destroy
            ui.Label(window.frame, text=text, column=0, row=0, ipady=25)
            b=ui.Button(window.frame, text=btext,
                    cmd=cmd,
                    anchor='c',
                    column=0, row=1,sticky='')
            window.deiconify()
            b.wait_window(window)
            self.deiconify()
            log.info("Done getting checks without a check")
        elif guess is True:
            #kwargs with tosort,wsorted don't seem to ever be passed (yet)...
            program['status'].makecheckok(**kwargs) #tosort=tosort,wsorted=wsorted)
            window.destroy() #never shown
            self.deiconify()
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
            if program['params'].cvt() == 'T':
                newb=ui.Button(buttonFrame1.bf,
                            text=_("New Frame"),
                            cmd=lambda w=window: self.addframe(window=w),
                            row=count+1)
            window.deiconify()
            buttonFrame1.wait_window(window)
            self.deiconify()
        """Make sure we got a value"""
        if program['params'].check() not in checks:
            return 1
    def _getglyph(self,window,event=None, **kwargs):
        log.info(_("Asking for a group (_getglyph kwargs: {kwargs})").format(kwargs=kwargs))
        glyphs=program['alphabet'].glyphs()
        glyph=program['alphabet'].glyph()
        cvt=kwargs.get('cvt',program['params'].cvt())
        purpose=kwargs.get('purpose','to work with')
        text=[_("What"),program['params'].cvtdict()[cvt]['sg'],
                _("do you want {purpose}?").format(purpose=purpose)]
        if kwargs.get('comparison'):
            g2=list(glyphs)[:]
            g2.remove(program['alphabet'].glyph())
            # log.info(f"_getglyph comparison options: {g2} ({type(g2)}))")
            if not g2:
                window.destroy()
                ErrorNotice(text=_("There don't seem to be any glyphs "
                            "to compare with!"))
                return
            optionlist=g2
            command=program['settings'].setgroup_comparison
            text.insert(1,_("other"))
        else:
            optionlist=glyphs
            command=program['alphabet'].glyph
        ui.Label(window.frame,
                      text=' '.join(text),
                      column=0, row=0)
        buttonFrame1=ui.ScrollingButtonFrame(window.frame,
                                 optionlist=optionlist,
                                 command=command,
                                 window=window,
                                 column=0, row=4
                                 )
        log.info("Done making _getglyph buttonframe")
    def _getgroup(self,window,event=None, **kwargs):
        """Window is called in getgroup"""
        log.info(_("Asking for a group (_getgroup kwargs: {kwargs})").format(kwargs=kwargs))
        purpose=kwargs.get('purpose','to work with')
        ps=kwargs.get('ps',program['slices'].ps())
        cvt=kwargs.get('cvt',program['params'].cvt())
        profile=kwargs.get('profile',program['slices'].profile())
        check=kwargs.get('check',program['params'].check())
        if (cvt == 'T' and None in [cvt, ps, profile, check]):
            ErrorNotice(parent=window.frame,
                          text=_("You need to set "
                          "\nCheck type (as Tone, currently {type}) "
                          "\nGrammatical category (currently {ps})"
                          "\nSyllable Profile (currently {profile}), and "
                          "\nTone Frame (currently {check})"
                          "\nBefore choosing a sort group!"
                          "").format(type=program['params'].cvtdict()[cvt]['sg'], ps=ps,
                          profile=profile, check=check), column=0, row=0)
            return 1
        kwargs=grouptype(**kwargs) #this just fills in False
        groups=program['status'].groups(cvt=cvt,**kwargs)
        if not groups:
            ErrorNotice(parent=window.frame,
                          text=_("It looks like you don't have {ps}-{profile} lexemes "
                          "grouped in the ‘{check}’ check yet \n({kwargs})."
                          "").format(ps=ps,profile=profile,check=check,kwargs=kwargs), column=0, row=0)
            return
        if kwargs.get('intfirst') and kwargs.get('guess'):
            l=[int(i) for i in program['status'].groups(cvt=cvt,**kwargs)
                                    if str(i).isdecimal()]
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
        cvt_name=program['params'].cvtdict()[cvt]['sg']
        if kwargs.get('comparison'):
            g2=list(groups)
            g2.remove(program['status'].group()) #group() is not cvt aware
            if not g2:
                window.destroy()
                ErrorNotice(text=_("There don't seem to be any groups "
                            "to compare with!"))
                return
            if len(g2) == 1:
                program['settings'].setgroup_comparison(g2[0],window)
                return
            ui.Label(window.frame,
                      text=_(f"What {cvt_name} do you want to {purpose}?"),
                      column=0, row=0)
            buttonFrame1=ui.ScrollingButtonFrame(window.frame,
                            optionlist=g2,
                            command=program['settings'].setgroup_comparison,
                            window=window,
                            column=0, row=4
                            )
        else:
            ui.Label(window.frame,
                      text=_("What {type} do you want to {purpose}?").format(type=cvt_name,purpose=purpose),
                      column=0, row=0)
            # window.scroll=ui.ScrollingFrame(window.frame)
            # window.scroll.grid(column=0, row=1)
            # groups+=[(None,'All')] #put this first, some day (now confuses ui)
            # log.info("Groups: {}".format(groups))
            buttonFrame1=ui.ScrollingButtonFrame(window.frame,
                                     optionlist=[(None,_("All"))]+groups,
                                     command=program['settings'].setgroup,
                                     window=window,
                                     column=0, row=4
                                     )
        log.info("Done making _getgroup buttonframe")
    def getglyph(self,event=None,**kwargs): #guess=False,
        def title_mod(x):
            if purpose_title:
                return ' '.join([x,_("to"),purpose_title])
            else:
                return x
        cvt=kwargs.get('cvt',program['params'].cvt())
        if cvt in ['V','C']:
            purpose_title=kwargs.get('purpose','').capitalize()
            cvt_name=program['params'].cvtdict()[cvt]['sg']
            w=ui.Window(self, title=title_mod(_('Select {type} Glyph').format(type=cvt_name)))
            self._getglyph(w,**kwargs)
            # w.wait_window(window=w)
            return w #so others can wait for this
    def getgroup(self,event=None,**kwargs): #guess=False,
        def title_mod(x):
            if purpose_title:
                return ' '.join([x,_("to"),purpose_title])
            else:
                return x
        """I need to think though how to get this to wait appropriately
        both for single C/V selection, and for CxV selection"""
        # log.info("this sets the group")
        kwargs=grouptype(**kwargs) #if any should be True, set in wrappers above
        # log.info("getgroup kwargs: {}".format(kwargs))
        program['settings'].refreshattributechanges()
        purpose_title=kwargs.get('purpose','').capitalize()
        cvt=kwargs.get('cvt',program['params'].cvt())
        if cvt == 'V':
            w=ui.Window(self,title=title_mod(_('Select Vowel')))
            self._getgroup(w,**kwargs)
            # w.wait_window(window=w)
        elif cvt == 'C':
            w=ui.Window(self,title=title_mod(_('Select Consonant')))
            self._getgroup(w,**kwargs)
            # self.frame.wait_window(window=w)
        elif cvt == 'CV':
            w=ui.Window(self,title=title_mod(_('Select Consonant/Vowel')))
            CV=''
            for kwargs['cvt'] in ['C','V']:
                self._getgroup(**kwargs)
                CV+=program['status'].group()
            program['status'].group(CV)
            # cvt = 'CV'
        elif cvt == 'T':
            w=ui.Window(self,title=title_mod(_('Select Framed Tone Group')))
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
        log.info(_("this sets the number of examples per group to record"))
        self.npossible=[
            {'code':1,'name':_("1 - Bare minimum, just one per group")},
            {'code':5,'name':_("5 - Some, but not all, of most groups")},
            {'code':100,'name':_("100 - All examples in most databases")},
            {'code':1000,'name':_("1000 - All examples in VERY large databases")}
                        ]
        title=_('Select Number of Examples per Group to Record')
        window=ui.Window(self, title=title)
        text=_("The {name} tone report splits sorted data into "
                "draft underlying tone melody groups. "
                # ", with distinct values for each of your tone frames. This "
                # "exhaustively finds differences between groups of lexical "
                # "senses, but often "
                # "misses similarities between groups, which might be "
                # "distinguished only because a single word was skipped or sorted "
                # "incorrectly.\n\n"
                "Even before a linguist has been able to evaluate these "
                "groups, it may be helpful to record your sorted data. "
                "{name} can give you a window for each lexicon sense in a tone "
                "group, with a record button for each sorted sense-frame "
                "combination. "
                "\n\nThose "
                "windows will be presented to the user from one tone report "
                "group after "
                "another, until all groups have had one page presented. Then "
                "{name} will "
                "repeat this process, until it has done a number of "
                "rounds equal to the number selected below. "
                # "\n\nIf a "
                # "group has fewer examples than this number, that group will be "
                # "skipped once done. "
                "\nPicking a larger number could delay opening "
                "the recording window; picking a smaller number could mean "
                "data not getting recorded. "
                "Up to how many examples do you want to record for each group?"
                "").format(name=program['name'])
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
        log.info(_("Shutting down runwindow"))
        if not self.exitFlag.istrue():
            self.deiconify()
        if program['taskchooser'].towrite:
            log.info(_("Final write to lift"))
            self.maybewrite(definitely=True)
        else:
            log.info(_("No final write to lift"))
        ui.Window.cleanup(self) #Exitable; currently does nothing else
    def getrunwindow(self,msg=None,title=None):
        """Can't test for widget/window if the attribute hasn't been assigned,"
        but the attribute is still there after window has been killed, so we
        need to test for both."""
        def releasefullscreen(event):
            self.runwindow.attributes('-fullscreen', False)
            self.runwindow.bind('<Double-Button-1>', takefullscreen)
        def takekioskscreen(event):
            ##This provides a kiosk mode, with no window dressings and all
            ##screen real estate used.
            self.runwindow.attributes('-fullscreen', True)
            ##This seems the same as above, but doesn't remove on fullscreen=F:
            # screen_width = program['root'].winfo_screenwidth()
            # screen_height = program['root'].winfo_screenheight()
            # self.runwindow.geometry(f"{screen_width}x{screen_height}+0+0")
            self.runwindow.bind('<Double-Button-1>', releasefullscreen)
        def takefullscreen(event):
            #This maximizes window, though leaves dressing in place:
            # self.runwindow.update_idletasks() #necessary?
            # self.runwindow.attributes('-zoomed', True)
            # seems the same as above:
            self.runwindow.wm_attributes('-zoomed', True)
            self.runwindow.bind('<Double-Button-1>', releasefullscreen)
        if title is None:
            title=(_("Run Window"))
        if self.exitFlag.istrue():
            return
        self.clear_runwindow()
        self.runwindow=ui.Window(self,title=title,withdrawn=True)
        self.runwindow.title(title)
        takekioskscreen(None)
        self.runwindow.bind('<Escape>', releasefullscreen)
        self.runwindow.cleanup=self.runwindowcleanup
        if msg: #withdraw one way or another, but just waitdone to return
            self.runwindow.wait(msg=msg,thenshow=True)
        self.withdraw() #this is the parent of the runwindow, the task
    def isrunwindow(self):
        log.info(f"{hasattr(self,'runwindow')=}")
        widgets=[self]
        if hasattr(self,'runwindow'):
            widgets+=[self.runwindow]
        for w in widgets:
            log.info(f"{w} {w.winfo_exists()=}")
            log.info(f"{w} {w.winfo_ismapped()=}")
            log.info(f"{w} {w.winfo_viewable()=}")
            log.info(f"{w} {w.iswaiting()=}")
            log.info(f"{w} {w.state()=}")
            log.info(f"{w} {w.winfo_toplevel() == w=}")
    def clear_runwindow(self):
        if hasattr(self,'runwindow'):
            self.runwindow.destroy()
            delattr(self,'runwindow')
    """Functions that everyone needs"""
    def updateazt(self,event=None):
        updateazt()
    def maybewrite(self,definitely=False):
        program['taskchooser'].maybewrite(definitely=definitely)
    def killall(self):
        log.info(_("Shutting down Task"))
        try:
            towrite=program['taskchooser'].towrite
        except AttributeError:
            towrite=self.towrite #if taskchooser; shouldn't happen, but in case.
        self.wait(msg=_("Closing down {name} and storing changes").format(
                                                                name=program['name']
                                                                ))
        if towrite:
            log.info(_("Final write to lift"))
            self.maybewrite(definitely=True)
        else:
            log.info(_("No final write to lift"))
        program['settings'].trackuntrackedfiles()
        self.waitdone() #Don't confuse user; there's more input to come, maybe
        for r in program['settings'].repo:
            program['settings'].repo[r].share()
            log.info(_("Done maybe committing/pushing to {repo}").format(repo=r))
        log.info(_("Saving settings for next time"))
        program['settings'].storesettingsfile() #in case we added repos
        if isinstance(self,Sound):
            program['settings'].storesettingsfile(setting='soundsettings')
        log.info(_("Settings saved"))
        log.info(_("Killing window"))
        ui.Window.killall(self) #Exitable
        log.info(_("Window killed"))
    def track_thread(self,x):
        log.info(_("Thread for {thread} started").format(thread=x))
        self.thread_names.append(x)
    def untrack_thread(self,x):
        if x in self.thread_names:
            log.info(_("Finishing thread for {thread}").format(thread=x))
            self.thread_names.remove(x)
        else:
            log.info(_("Didn't find thread for {thread}; can't mark finished.").format(thread=x))
    def thread_update(self):
        if self.thread_names:
            log.info(_("{count} threads running: {threads}").format(count=len(self.thread_names), threads=self.thread_names))
            if (not hasattr(self,'thread_update_thread') or 
                self.thread_update_thread not in self.tk.call('after', 'info')):
                self.thread_update_thread=self.after(1000,self.thread_update)
            # log.info(f"Will update by {id=} in 1s {type(id)=}")
        else:
            log.info(_("Finished with all threads running"))
    def __init__(self,parent):
        log.info(_("Initializing TaskDressing"))
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
        # log.info(f"Ready to Inherit for {type(self)} ({program})")
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
        ui.Window.__init__(self,parent,withdrawn=True)
        self.mainwindow=True
        self.maketitle()
        ui.ContextMenu(self)
        self.tableiteration=0
        self.makestatusframe()
        self.withdraw() #made visible by chooser when complete
        self._taskchooserbutton()
        self._removemenus() #self.correlatemenus()
        self.thread_names=list()
        # back=ui.Button(self.outsideframe,text=_("Tasks"),cmd=program['taskchooser'])
        # self.setfontsdefault()
class TaskChooser(TaskDressing):
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
            return _("Analysis & Decision Tasks")
    def dobuttonkwargs(self):
        return {'text':_("Reports"),
                'fn':self.choosereports,
                'font':'title',
                'compound':'top', #image bottom, left, right, or top of text
                'image':program['theme'].photo['iconReportLogo'],
                'sticky':'ew'
                }
    def choosereports(self):
        self.status.bigbutton.destroy()
        self.showreports=True
        self.setmainwindow(self)
        self.gettask()
    def makeexampledict(self):
        ExampleDict()
    def guidtriage(self): #obsolete
        # import time
        log.info(_("Doing guid triage and other variables —this takes awhile..."))
        start_time=nowruntime()
        self.guids=program['db'].guids
        self.guidsinvalid=[] #nothing, for now...
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
    def guidtriagebyps(self): #obsolete
        log.info(_("Doing guid triage by ps... This also takes awhile?..."))
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
                self.status.bigbutton.destroy()
        except AttributeError:
            log.info(_("There doesn't seem to be a big button"))
        if not self.showreports:
            self.status.finalbuttons()
        if not self.mainwindow:
            # self.correlatemenus() #not even if moving to this window
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
            bpr=3
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
                        wraplength=int(program['root'].wraplength*.02125/bpr),
                        anchor='n',
                        sticky='nesw',
                        columnspan=columnspan
                        )
            try:
                ui.ToolTip(b, o[0].tooltip(None))
            except AttributeError:
                log.info(_("Task {task} doesn't seem to have a tooltip.").format(task=o[0]))
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
        log.info(_("starting from option list {options}").format(options=optionlist))
        optionlist=[i for i in optionlist if not issubclass(i[0],Sound)]
        # log.info("getting default from option list {}".format(
        #                                             [i[1] for i in optionlist]))
        if program['testing'] and 'testtask' in program:
            self.maketask(program['testtask'])
        else: #we need better logic here
            if SortV in [i[0] for i in optionlist]:
                self.maketask(SortV)
            else:
                self.maketask(WordCollectnParsewRecordings)
                #optionlist[-1][0]) #last item, the code
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
            log.info(_("No mainwindowis found."))
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
                    ExportData,
                    AlphabetChart,
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
                    # WordCollectionPlural, #What is the value of this
                    # WordCollectionImperative, #What is the value of this
                    WordCollectionCitationwRecordings,
                    WordCollectnParse,
                    WordCollectnParsewRecordings,
                    RecordCitation
                    ]
            if self.doneenough['collectionlc']:
                """Do these next"""
                tasks.append(SortSyllables)
                tasks.append(SortV)
                tasks.append(SortC)
                tasks.append(SortT)
                if self.doneenough['sortT']:
                    tasks.append(RecordCitationT)
            # if self.donew['parsedlx']:
            #     tasks.append(SortRoots)
        else: #i.e., analysis tasks
            tasks=[WordsParse]
            if self.doneenough['sort']:
                tasks.append(TranscribeV)
                tasks.append(TranscribeC)
            #this maybe should depend on recordedT:
            if self.doneenough['sortT']:
                tasks.append(TranscribeT)
            if self.doneenough['analysis']:
                tasks.append(JoinUFgroups)
            if me:
                # tasks.append(ParseWords)
                # tasks.append(ParseWords)
                # tasks.append(ParseSlice)
                # tasks.append(ParseSliceWords)
                tasks.append(ReportConsultantCheck)
        # if (program['testing'] and 'testtask' in program and
        #         program['testtask'] not in tasks):
        #     if self.showreports == isinstance(program['testtask'],Report):
        #         tasks.append(program['testtask'])
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
                    tasktuples.append((task,str(task), task.taskicon(task)))
                else:
                    tasktuples.append((task,str(task),None))
        log.info(_("Tasks available ({count}): {tasks}").format(count=len(tasktuples),
                    tasks=[i[1] for i in tasktuples]))
        return tasktuples
    def convertlxtolc(self,window):
        try:
            window.destroy()
            backup=self.filename+'_backupBeforeLx2LcConversion'
            program['db'].write(backup)
            program['db'].convertlxtolc()
            # program['db'].write(self.file.name+str(now()))
            program['db'].write()
            conversionlogfile=logsetup.writelzma()
            ErrorNotice(_("The conversion is done now, so {name} will quit. You may "
                    "want to inspect your current file ({file}) and the backup "
                    "({backup}) to confirm this did what you wanted, before "
                    "opening {name} again. In case there are any issues, the "
                    "log file is also saved in {log}").format(name=program['name'],
                                                file=self.filename,
                                                backup=backup,
                                                log=conversionlogfile),
                    title=_("Conversion Done!"),
                    wait=True)
            self.restart()
        except Exception as e:
            ErrorNotice(_(f"There was a problem converting fields as you asked; you "
                "should fix this before moving on."))
    def asktoconvertlxtolc(self):
        title=_("Convert lexeme field data to citation form fields?")
        url='{}/CITATIONFORMS.md'.format(program['docsurl'])
        w=ui.Window(program['root'],title=title,exit=False)
        lexemesdone=list(program['db'].nentrieswlexemedata.values())#[program['settings'].analang]
        citationsdone=list(program['db'].nentrieswcitationdata.values())#[program['settings'].analang]
        nbtext1=_("You have {lexemes} entries with lexeme data, and only {citations} with "
                "citation data.").format(lexemes=lexemesdone,citations=citationsdone)
        instructions=_("Typically, dictionary work starts by collecting "
                        "citation forms, and later moves to analyzing those "
                        "forms into lexemes (meaningful, but not necessarily "
                        "pronounceable, word parts). Sometimes, people store "
                        "those citation forms in lexeme fields, though this "
                        "is typically in error. {name} can help you analyze your "
                        "citation forms into lexeme forms, but they first need "
                        "to be moved to the correct fields in your database."
                        "".format(name=program['name']))
        Question=_("Do you want {name} to move data from your lexeme fields to "
                    "citation fields, for each entry with no citation field "
                    "data?").format(name=program['name'])
        infot=_("See {url} for more information.").format(url=url)
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
        info.tt=ui.ToolTip(info, text=_("go to {url}").format(url=url))
        info.bind('<Button-1>', lambda e: openweburl(url))
        for l in [lt,nb,lq,lnb]:
            l.wrap()
        return w
    def getcawlmissing(self):
        cawls=program['db'].get('cawlfield/form/text').get('text')
        # log.info("CAWL ({}): {}".format(len(cawls),cawls))
        self.cawlmissing=[]
        for i in range(1700):
            if '{:04}'.format(i+1) not in cawls:
                self.cawlmissing.append(i+1)
        if len(self.cawlmissing) < 10:
            log.info(_("CAWL missing ({count}): {missing}").format(count=len(self.cawlmissing),
                                                        missing=self.cawlmissing))
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
        # There should never be more lexemes than citation forms.
        for l in lexemesdone:
            if not program['settings'].askedlxtolc and (l not in citationsdone
                                or citationsdone[l] < lexemesdone[l]):
                w=self.asktoconvertlxtolc()
                w.wait_window(w) # wait for this answer before moving on
                program['settings'].askedlxtolc=True
                program['settings'].storesettingsfile()
                break #just ask this once
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
        log.info(f"sorts: {sorts}")
        if me:
            enough=0
        else:
            enough=6 #for demonstrating; is 25 a reasonable minimum?
        # log.info("looking at sorts now: {}".format(sorts))
        for l in sorts:
            if program['db'].audiolang:
                al=program['db'].audiolang
            else:
                maybeals=[i for i in program['db'].audiolangs if l in i]
                if maybeals:
                    al=maybeals[0]
                    log.info(_("Using audiolang {audio} for analang {analang}")
                                .format(audio=al,analang=l))
                else:
                    log.info(_("Couldn't find plausible audiolang (among {audios}) "
                        "for analang {analang}").format(audios=program['db'].audiolangs,analang=l))
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
                log.info(_("Finished looking at [{lang}]{field} field: {status}").format(lang=l, field=f, status=self.doneenough))
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
        log.info(_("Analysis of what you're done with: {status}").format(status=self.donew))
        log.info(_("You're done enough with: {status}").format(status=self.doneenough))
    def restart(self,filename=None):
        log.info(_("Restarting from TaskChooser"))
        file.writefilename(self.filename)
        if hasattr(self,'warning') and self.warning.winfo_exists():
            self.warning.destroy()
        # log.info("towrite: {}; writing: {}".format(self.towrite,self.writing))
        if self.towrite: #Do even if not closed by user
            log.info(_("Final write to lift"))
            self.maybewrite(definitely=True)
        try:
            self.task.withdraw() #so users don't do stuff while waiting
        except (AttributeError,tkinter.TclError):
            log.info("There doesn't seem to be a task to hide; moving on.")
        try:
            self.task.runwindow.withdraw() #so users don't do stuff while waiting
        except (AttributeError,tkinter.TclError):
            log.info(_("There doesn't seem to be a runwindow to hide; moving on."))
        while self.writing:
            # log.info("towrite: {}; writing: {}; taskwrite: {}".format(
            #     self.towrite,self.writing,program['taskchooser'].writing))
            log.info(_("Waiting to finish writing to lift"))
            time.sleep(1)
            self.check_if_write_done() #because after() isn't working here...
        # log.info("Not writing to lift")
        sysrestart()
    def changedatabase(self):
        log.debug("Preparing to change database name.")
        try:
            self.task.withdraw() #so users don't do stuff while waiting
        except (AttributeError,tkinter.TclError):
            log.info(_("There doesn't seem to be a task to hide; moving on."))
        curname = self.filename
        log.info(_("Current database: {name}").format(name=curname))
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
        log.info(_("Current database: {name}").format(name=self.filename))
        if self.filename and curname != self.filename:
            log.info(_("User selected a new database; restarting with it."))
            self.restart()
        else:
            log.info(_("User didn't select a new database; continuing."))
            self.task.deiconify()
        # self.restart(self.filename)
    def timetowrite(self):
        """only write to file every self.writeeverynwrites times you might.
        current defaiult is every write possible (writeeverynwrites=1)
        change this in your project settings if your power is stable and you
        want to write less."""
        self.writeable+=1 #and tally here each time this is asked
        return not self.writeable%program['settings'].writeeverynwrites
    def schedule_write_check(self):
        """Schedule `check_if_write_done()` function after x seconds."""
        x=1
        # log.info("Scheduling check after {x} seconds")
        program['root'].after(x*1000, self.check_if_write_done)
        # log.info("Scheduled check")
        # program['taskchooser'].after(5000, self.check_if_write_done, t)
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
            log.info(_("Done writing to lift ({status}).").format(status=program['db'].write_OK))
            if not program['db'].write_OK:
                ErrorNotice(_("Write to lift returned "
                            "‘{error}’.").format(error=program['db'].write_error),wait=True)
            self.writing=False
            if self.towrite:
                log.info(_("Found previous request to write; doing again."))
                self._write()
        else:
            # Otherwise check again later.
            # log.info("schedule_write_check writing to lift.")
            self.schedule_write_check()
    def _write(self):
        self.towrite=False
        self.writethread = threading.Thread(target=program['db'].write)
        self.writing=True
        log.info(_("Writing to lift..."))
        self.writethread.start()
        self.schedule_write_check()
    def maybewrite(self,definitely=False):
        write=self.timetowrite() #just call this once!
        if (write and not self.writing):# or definitely:bad idea to overwrite write
            self._write()
        elif write:
            # log.info(_("Already writing to lift; I trust this new mod will "
            #         "get picked up later..."))
            #This tells A−Z+T that something hasn't been written yet, so it will force a write on shutdown.
            self.towrite=True
            # self.schedule_write()
    def usbcheck(self):
        if self.splash.exitFlag.istrue():
            return
        self.splash.withdraw()
        for r in program['settings'].repo.values():
            # log.info("checking repo {} for USB drive".format(r))
            r.share()
        self.splash.draw()
    # def getinterfacelangs(self):
    # # global i18n
    #     return [{'code':i,'name':program['settings'].languagenames[i]}
    #             for i in program['interfacelangs']]
    # # {'code':'fr','name':'Français'},
    # #         {'code':'en','name':'English'},
    # #         {'code':'fub','name':'Fulfulde'}
    # #         ]
    def __init__(self,parent):
        program['taskchooser']=self
        self.towrite=False
        self.writing=False
        self.datacollection=True # everyone starts here?
        self.showreports=False
        self.showingreports=False
        self.filename=FileChooser().name #new file self.analang set here
        self.splash = Splash(self)
        self.splash.draw()
        Settings(self) #pick up self.analang from file
        assert 'settings' in program
        # self.interfacelangs=self.getinterfacelangs()
        FileParser(self.filename,program['settings'].analang)
        self.splash.progress(55)
        self.setmainwindow(self)
        program['settings'].post_lift_init()
        self.splash.progress(65)
        self.whatsdone()
        self.splash.progress(80)
        log.info(_("Settings: {settings}").format(settings=program['settings']))
        super().__init__(parent)
        # TaskDressing.__init__(self,parent) #I think this should be after settings
        program['settings'].getprofiles()
        Alphabet() #after slicedict is up
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
            e=_("You don't have the sound module installed. For best use of {name},"
                "you should switch back to the main branch, connect to the "
                "internet, and restart. In the mean time. You won't be able "
                "to record or play audio!"
                ).format(name=program['name'])
            ErrorNotice(e)
        self.splash.progress(100)
        if self.splash.exitFlag.istrue():
            sysshutdown()
        self.splash.destroy()
        self.makeexampledict() #needed for makestatus, needs params,slices,data
        self.maxprofiles=5 # how many profiles to check before moving on to another ps
        self.maxpss=2 #don't automatically give more than two grammatical categories
        log.info(_("done setting up taskChooser"))
        self.makedefaulttask() #normal default
        # self.gettask() # let the user pick
        """Do I want this? Rather give errors..."""
class ExportData(ui.Window):
    """docstring for ExportData."""
    def taskicon(self):
        return program['theme'].photo['USBdrive']
    def tooltip(self):
        return _("This tells you how much data you could export now, and "
                    "allows you to export it.")
    def tasktitle(self):
        return _("Export Data")
    def dobuttonkwargs(self):
        text=_("Export Data")
        tttext=_("This tells you how much data you could export now, and "
                    "allows you to export it.")
        return {'text':text,
                # 'fn':pass,
                # column=0,
                'font':'title',
                'compound':'bottom', #image bottom, left, right, or top of text
                'image':program['taskchooser'].theme.photo['USBdrive'],
                'sticky':'ew',
                'tttext':tttext
                }
    def on_quit(self):
        ui.Window.on_quit(self)
        program['taskchooser'].gettask()
    def switch(self,event=None):
        if self.exportclass == export.Lexicon:
            self.exportclass=export.Examples
        else:
            self.exportclass=export.Lexicon
        self.report_data()
    def do_export(self,event=None):
        self.done_notice=ui.Label(self.frame,
                                    text=_("In Progress..."),
                                    anchor='c',padx=50,
                                    row=4,column=0,columnspan=2,sticky='we'
                                )
        for i in self.export.export():
            self.progress(i*100)
        self.progress(100)
        self.done_notice['text']=_(f"Done!\n(saved to {self.export.save_dir})")
    def report_data(self,check=None,event=None):
        if hasattr(self,'button') and isinstance(self.button,dict):
            for i in self.button.values():
                i.destroy()
            del self.button
        for o in ['info','button',
                    'export_button', 'switch_button',
                    'done_notice']:
            try:
                getattr(self,o).destroy()
            except:
                pass
        self.update()
        self.export=self.exportclass(
                lift=program['db'],
                analang=program['params'].analang(),
                audiolang=program['params'].audiolang(),
                audiodir=program['settings'].audiodir,
                save_dir=program['settings'].exportsdir,
                check=check,
                max_rows_total=self.max_rows_total,
                max_rows_per_file=self.max_rows_per_file,
                )
        self.info=ui.Label(self.frame,
            text=_("Checking work done..."),
            anchor='c',padx=50,
            row=0,column=0,sticky='we'
        )
        self.button_frame=ui.Frame(self.frame,
                                    row=2,column=0,
                                    )
        self.progress(0,self.frame,row=3,column=0)
        for i in self.export.report():
            self.progress(i*100)
        self.info['text']=self.export.info
        self.export_button=ui.Button(self.button_frame,
                text=_("Export"),
                anchor='c',padx=50,
                row=0,column=1,sticky='we'
        )
        if self.exportclass == export.Lexicon:
            self.switch_button=ui.Button(self.button_frame,
                    text=_("Check Examples"),
                    anchor='c',padx=50,
                    row=0,column=0,sticky='w'
            )
            if self.slices:
                allchecks=program['status'].allcheckswCVdata()
                self.button={c:ui.Button(self.button_frame,
                                        text=_(f"Just {c} data"),
                                        anchor='c',padx=50,
                                        row=allchecks.index(c)+1,
                                        column=0,sticky='w'
                                        )
                        for c in allchecks
                            }
                for c in self.button:
                    self.button[c].bind("<Button-1>",
                                        lambda event,x=c: self.report_data(x))

        else:
            self.switch_button=ui.Button(self.button_frame,
                    text=_("Check Lexicon"),
                    anchor='c',padx=50,
                    row=0,column=0,sticky='w'
            )
        self.export_button.bind("<Button-1>",self.do_export)
        self.switch_button.bind("<Button-1>",self.switch)
    def __init__(self, arg):
        self.exportclass=export.Lexicon
        title=(_(f"{program['name']} Data Export"))
        ui.Window.__init__(self,program['root'], title=title)
        self.slices=False #allow user to output data for each check
        self.max_rows_total=None
        self.max_rows_per_file=None
        self.report_data()
class Alphabet():
    """This class stores two dictionaries for alphabet glyphs:
    glyphdict: keyed on C and V, values contain a list of all verified consonants
                and vowels, respectively. Macrogroup verification means that no
                sortgroup has been added to a macrogroup (glyph) since it was
                verified, either through presorting or manual sorting.
                This is the source for the AlphabetChart, so there will be a
                period between completing a check and verifying all consonants
                including data for that check, where AlphabetChart work will not
                be possible. (this may not be true, but may be)
    glyph_members: keyed on glyphs, values contain a list of codes for verified
                groups which are currently sorted into that glyph. This is
                saved to disk for recovery, but it's contents are rather
                ephemeral. That is, a code such as Noun_CVCV_lc_V2_ie might not
                remain valid for a set of words if syllable profiles are
                reanalyzed, but more importantly, as groups are renamed.
                That is, when sorting, one might have Noun_CVCV_lc_V2_ie and
                Noun_CVCV_lc_V1_i in one group (e.g., 'ɨ'), but once that
                sorting is confirmed, all words in all relevant groups should
                have their annotations updated (C above), meaning the code
                would be updated, too (i.e., Noun_CVCV_lc_V2_ɨ). This is
                even before forms are updated to their annotations.
    On verification of *all groups*, the following will be updated:
        1. lift verification field (e.g., <field type="CVCV lc verification">).
        2. form annotation values (e.g., <annotation name="V1" value="i" />)
        3. forms are updated to annotations per usual (where not NA or int().)
    Once this happens, the old sorting data is useless, and will need to be
    reconstructed if needed, since forms and annotations have been updated.

    I hope it would be sufficient to have no changes to annotations or forms
    until all is confirmed, then force it all to happen at once (maybe backup
    before doing so?)

    program['slices'].senses() is sensitive to ps and profile, and pulls from syllableprofiles
    iterating over that with sense.annotationvaluedictbyftypelang(ftype,lang)
    should provide the different checks and values for each sense.

    I need a button that allows iteration over a group with groups inside of it.
    """
    my_settings=['order']
    def order(self,order=[]):
        if order:
            self._order=order
        return getattr(self,'_order',[])
    def status(self,status={}):
        if status:
            self._status=status
        return getattr(self,'_status',{})
    def glyphdict(self,glyphdict={}):
        """This dict stores glyphs which are verified. When a glyph macrogroup
        has an item added to it, the glyph macrogroup is removed from here.
        integer values should be stored as strings."""
        if glyphdict:
            conflict=glyphdict['C']&glyphdict['V']
            if conflict:
                ErrorNotice(_("You have the glyph(s) ‘{conflict}’ as consonant "
                            "and as vowel! ({glyphs})").format(conflict=conflict,glyphs=glyphdict),wait=True)
                raise
            self._glyphdict={k:{str(i) for i in v} for k,v in glyphdict.items()}
        return getattr(self,'_glyphdict',{'V':set(),'C': set()})
    def glyph_members(self,gm={}):
        """This dict stores sorting information; items are sorted in and out of
        the values keyed by each glyph. Integer keys should be stored as
        strings."""
        if gm:
            self._glyph_members={str(k):v for k,v in gm.items()}
        return getattr(self,'_glyph_members',{})
    def rename_glyph(self,x,y):
        gm=self.glyph_members()
        if y in gm:
            log.error(_("'glyph_members' contains {new}; not renaming {old}").format(new=y, old=x))
            return
        gd=self.glyphdict()
        for k in gd:
            if y in gd[k]:
                log.error(_("'glyphdict' contains {new}; not renaming {old}").format(new=y, old=x))
                return
        log.info(_("'rename_glyph' can safely rename {old} to {new}").format(old=x, new=y))
        self.glyph_members({y if k == x else k:v for k,v in gm.items()})
        # log.info(f"'glyph_members' renamed {x} to {y}")
        self.glyphdict({k:{y if i == x else i for i in v} for k,v in gd.items()})
        # log.info(f"'glyphdict' renamed {x} to {y}")
        for t in list(self.distinguished_by_cvt()):
            if x in t:
                self.undistinguish(t)
                self.distinguish((y if t[0]==x else t[0],y if t[1]==x else t[1]))
    def rename_glyph_member(self,item,newitem):
        """Leave verification status alone"""
        d=self.glyph_members()
        for glyph,items in d.items():
            if item in items:
                d[glyph].remove(item)
                d[glyph].add(newitem)
    def join_glyphs(self,x,y):
        log.info(f"Running Alphabet.join_glyphs")
        d=self.glyph_members()
        for i in x:
            # log.info(f"Checking {i} for conflicts in {y} {d[y]}")
            if self.conflicting_items(i,y):
                ErrorNotice(_(f"item {i} conflicts with glyph {y}"),wait=True)
                return
        for i in y:
            # log.info(f"Checking {i} for conflicts in {x} {d[x]}")
            if self.conflicting_items(i,x):
                ErrorNotice(_(f"item {i} coflicts with glyph {x}"),wait=True)
                return
        # log.info(f"No conflicts found.")
        for i in list(d[x]):
            # log.info(f"Removing {i} from {x}.")
            self.rm_glyph_member(i,x)
            # log.info(f"Adding {i} to {y}.")
            self.add_glyph_member(i,y)
        self.save_settings()
        log.info(f"Alphabet.join_glyphs done.")
        # remove glyph from glyph_members
    def distinguished(self,glyphs_distinguished={}):
        if not hasattr(self,'_distinguished'):
            self._distinguished={'V':set(),'C': set()}
        if glyphs_distinguished.keys() == {'V','C'}:
            self._distinguished=glyphs_distinguished
        elif glyphs_distinguished:
            log.error(_("{glyphs} provided, but without good keys").format(glyphs=glyphs_distinguished))
            raise
        return self._distinguished
    def distinguished_by_cvt(self,**kwargs):
        cvt=kwargs.get('cvt',program['params'].cvt())
        return self.distinguished()[cvt]
    def distinguish(self, g, **kwargs):
        self.distinguished_by_cvt().add(g)
    def undistinguish(self, g, **kwargs):
        self.distinguished_by_cvt().remove(g)
    def undistinguish_any_with(self,g):
        d=self.distinguished_by_cvt()
        for j in [i for i in d if g in i]:
            d.remove(j)
    def predistinguish(self,tuple_set):
        """This is here to keep users from seeing trivial glyph distinction prompts.
        Trivial here is defined as:
            —all members of each of a set of glyphs have already 
                been distinguished from all members of the other glyph, 
                when they were compared as sort groups
        This can only apply when all members are 'conflicting' groups (i.e., 
            same conflict_code), as they are the only ones who have been 
            compared as sort groups
        Given that glyph membership cannot include more than one 'conflicting' 
            group, the easiest criteria is to exclude those with more than 
            one group, as these would necessarily contain groups which had not been 
            previously compared. (if this is not the case, it is a problem; 
            it should have been removed by remove_conflicting_items on sort) 
        so we ask, for each glyph pairing presented:
            Is there no more than one member for each?
            Are each 'conflicting'?
            Are each distinguished as sort groups?
                (the last two in have_only_distinguished_items)
        """
        def nmembers(g):
            return len(gm[g])
        gm=self.glyph_members()
        for t in tuple_set:
            log.info(_("Working on {tuple} ({counts};{max}=)").format(tuple=t, counts=[i for i in map(nmembers,t)], max=max(map(nmembers,t))))
            if max(map(nmembers,t)) <= 1 and self.have_only_distinguished_items(*t):
                log.info(_("Distinguishing {glyph1} and {glyph2}").format(glyph1=gm[t[0]], glyph2=gm[t[1]]))
                self.distinguish(t)
            else:
                log.info(_("Not distinguishing {glyph1} and {glyph2}").format(glyph1=gm[t[0]], glyph2=gm[t[1]]))
                self.distinguish(t)
    def add_glyph_member(self,item,glyph):
        """This is sort into"""
        self.mark_glyph_not_done(glyph)
        d=self.glyph_members()
        if glyph not in d:
            d[glyph]=set()
        d[glyph].add(item)
        self.glyph_members(d)
        log.info(_("Alphabet.add_glyph_member done."))
    def rm_glyph_member(self,item,glyph=None):
        #If this raises KeyError, use discard
        d=self.glyph_members()
        if glyph:
            d[glyph].remove(item)
        else:
            for glyph in [g for g,m in d.items() if item in m]:
                d[glyph].remove(item)
        for glyph in [k for k,v in d.items() if v == set()]:
            del d[glyph]
            self.mark_glyph_not_done(glyph) #no members is also not verified
        if d:
            self.glyph_members(d) # Adding empty dict does nothing; see below
        elif hasattr(self,'_glyph_members'):
            delattr(self,'_glyph_members')
        log.info(_("Alphabet.rm_glyph_member done."))
    def mark_glyph_done(self,glyph,cvt):
        """Mark Verified"""
        d=self.glyphdict()
        d[cvt].add(glyph)
        log.info(_("‘{glyph}’ added to verified list").format(glyph=glyph))
        return self.glyphdict(d)
    def mark_glyph_not_done(self,glyph,cvt=None):
        """Mark Unverified"""
        d=self.glyphdict()
        if cvt:
            d[cvt].remove(glyph) #leave cvt in place, even if empty
        else:
            for cvt in [cvt for cvt,glyphs in d.items() if glyph in glyphs]:
                d[cvt].remove(glyph)
        log.info(_("‘{glyph}’ removed from verified list").format(glyph=glyph))
        return self.glyphdict(d)
    def cull_glyphdict(self):
        """This limits the verified glyphs to those that actually have members.
        """
        d=self.glyph_members()
        for cvt,glyphs in self.glyphdict().items():
            for i in list(glyphs):
                if i not in d:
                    self.mark_glyph_not_done(i,cvt)
    def cvt_of_item(self,x):
        check=self.parse_verificationcode(x)['check']
        return program['params'].cvt_of_check(check)
    def conflict_code(self,code):
        return code.split('_')[:4]
    def verificationcode(self,**kwargs):
        ps=kwargs.get('ps',program['slices'].ps())
        profile=kwargs.get('profile',program['slices'].profile())
        ftype=kwargs.get('ftype',self.ftype)
        check=kwargs.get('check',program['params'].check())
        group=kwargs.get('group',program['status'].group())
        return '_'.join([ps,profile,ftype,check,group])
    def parse_verificationcode(self,code):
        ps,profile,ftype,check,group=code.split('_')
        return {'ps':ps,'profile':profile,'ftype':ftype,
                'check':check,'group':group}
    def refresh_items(self):
        self.items_present=set()
        k={'ftype':self.ftype} #ftype may need to iterate some day
        program['settings'].reloadstatusdata() # culled here
        d=program['status'].dict()
        for k['cvt'],ps_d in d.items(): #read cvt from status
            for k['ps'],pr_d in ps_d.items():
                for k['profile'],ch_d in pr_d.items():
                    for k['check'],ch_v in ch_d.items():
                        for k['group'] in [i for i in ch_v['done']
                                            if i not in ['NA']]: #only verified
                            # log.info(f"Adding item for {k}")
                            self.items_present.add(self.verificationcode(**k))
        self.cull_glyph_members()
    def cull_glyph_members(self):
        """This removes items from the sorting piles if they don't exist"""
        for glyph,members in list(self.glyph_members().items()):
            for i in list(members):
                if i not in self.items_present:
                    self.rm_glyph_member(i,glyph)
        self.save_settings()
    def glyphstoverify(self):
        """Which glyphs are sorted, but not verified yet (or added to since)?"""
        sorted=set(self.glyphs()) #this is constrained by cvt
        return sorted-{i for k,v in self.glyphdict().items() for i in v}
    def itemstosort(self):
        return sorted(self._itemstomacrosort)
    def renew_items_tomacrosort(self): 
        self._itemsmacrosorted=set()
        self._itemstomacrosort=set()
        self.refresh_items()
        for item in self.items_present:
            if item in [i for j in self.glyph_members().values() for i in j]:
                self._itemsmacrosorted.add(item)
            else:
                self._itemstomacrosort.add(item)
        return self._itemstomacrosort
    def mark_item_macrosorted(self,item,**kwargs):
        self._itemsmacrosorted.add(item)
        if item in self._itemstomacrosort:
            self._itemstomacrosort.remove(item)
    def mark_item_tomacrosort(self,item,**kwargs):
        self._itemstomacrosort.add(item)
        if item in self._itemsmacrosorted:
            self._itemsmacrosorted.remove(item)
    def presort_item(self,item):
        """Because this will work automatically:
        1. We don't want to assign groups to new int() letters
        2. We don't want to kick out groups that are already there.
        Let the user decide to do either, if necessary.        """
        glyph=self.parse_verificationcode(item)['group']
        log.info(_("presort_item moving {item} into ‘{glyph}’").format(item=item, glyph=glyph))
        if not glyph.isdigit() and not self.conflicting_items(item,glyph):
            self.mark_item_glyph(item,glyph)
    def have_only_distinguished_items(self,x,y):
        log.info(_("Running have_only_distinguished_items on {x} and {y}").format(x=x, y=y))
        gm=self.glyph_members()
        for i in gm[x]:
            for j in gm[y]:
                if (self.conflict_code(i) != self.conflict_code(j) or
                            not program['status'].isdistinguished(
                                    self.parse_verificationcode(j)['group'],
                                    **self.parse_verificationcode(i))):
                    log.info(_("Found undistinguished items {item1} and {item2}").format(item1=i, item2=j))
                    return False
        return True
    def conflicting_items(self,item,glyph):
        d=self.glyph_members()
        if glyph not in d:
            return [] #keep iterable
        compare=self.conflict_code(item)
        r=list()
        for i in list(d[glyph]):
            if self.conflict_code(i) == compare:
                r.append(i)
        return r
    def remove_conflicting_items(self,item,glyph):
        conflicts=self.conflicting_items(item,glyph)
        for i in conflicts:
            ErrorNotice(_("Removing {item} from ‘{glyph}’ to make room for {new}").format(item=i,glyph=glyph,new=item),
                        wait=True)
            self.remove_item_from_glyph(i)
    def mark_item_glyph(self,item,glyph):#maybe move to Alphabet Sort
        self.rm_glyph_member(item) # in case elsewhere
        self.remove_conflicting_items(item,glyph) #other group from same check
        self.add_glyph_member(item,glyph)
        self.mark_item_macrosorted(item)
        if item in self.glyph_members()[glyph]:
            log.info(_("mark_item_glyph added ‘{item}’ to ‘{glyph}’").format(item=item, glyph=glyph))
        else:
            log.info(_("mark_item_glyph failed to add ‘{item}’ to ‘{glyph}’").format(item=item, glyph=glyph))
            # log.info(f"{self.glyph_members()=}")
    def remove_item_from_glyph(self,item,glyph=None):
        self.rm_glyph_member(item,glyph) # in case elsewhere
        self.cull_glyphdict() #without knowing glyph or cvt
        self.mark_item_tomacrosort(item)
    def update_symbols(self):
        """I need to rethink this method entirely. How to make sure all symbols
        are available to the alphabet chart?
        """
        order=program['settings'].alpha_order()
        """this is a dict keyed by C,V; iterate appropriately!"""
        glyphdict=self.glyphdict()
        """Extra symbols not in order"""
        extras={i for i in items if not i.isdecimal()}-set(self.order())
        log.info(f"adding to {cv}: {extras=}")
        """Add to beginning of order"""
        order=sorted(extras)+self.order() #put new symbols first
        #only actually present:
        """limit to those symbols actually verified somewhere (iterate appropriately)"""
        order=[i for i in self.order() if i in items]
        """store new order"""
        self.order(order)
    def glyph(self,glyph=False,window=False):
        """This maintains the glyph we are actually on:
        False: don't set a glyph
        None: there is no current glyph
        """
        if glyph is not False: #this needs to be able to be specified None
            if glyph:
                glyph=str(glyph)# in case an int() group gets through
            self._glyph=glyph
        if window and window.winfo_exists():
            window.destroy()
        return getattr(self,'_glyph',None)# this needs to be booleanable
    def glyphs(self):
        return [k for k,v in self.glyph_members().items()
                        if [i for i in v
                            if self.cvt_of_item(i) == program['params'].cvt()]
                ]
    def save_settings(self):
        program['settings'].storesettingsfile(setting='alphabet')
    def __init__(self, **kwargs):
        program['alphabet']=self
        self.ftype=program['params'].ftype()
        program['settings'].settingsobjects() #should do this more; can be redone!
        self.renew_items_tomacrosort()
        self.save_settings()
class AlphabetChart(alphabet_chart.OrderAlphabet):
    my_settings=[
                    'exids',
                    # 'order',
                    'ncolumns','chart_title',
                    'pagesize'
                ]+Alphabet.my_settings#?
    def taskicon(self):
        return program['theme'].photo['alpha_icon']
    def tooltip(self):
        return _("This task helps you organize an alphabet and select words "
            "with pictures to represent each letter.")
    def tasktitle(self):
        return _("Alphabet Chart") # for Citation Forms
    def save_settings(self):
        for k in self.my_settings: #defined in module
            value=getattr(self,k)
            if isinstance(value,ui.Variable):
                value=value.get()
                log.info(_("found ‘{key}’ ui.Variable: {value}").format(key=k, value=value))
            else:
                log.info(_("Didn't find ‘{key}’ ui.Variable: {value}").format(key=k, value=value))
            getattr(program['settings'],'alpha_'+k)(value)
        program['settings'].storesettingsfile(setting='alphabet')
    def __init__(self, parent, **kwargs):
        self.program=program
        super().__init__(parent)
        self.mainwindow=False #don't exit on close
class Senses(object):
    """docstring for Senses."""
    def groups(self,**kwargs): #toverify=True
        return program['status'].groups(**kwargs)
    def group(self,value=None,**kwargs):#get/set
        return program['status'].group(value,**kwargs)
    def notdonewarning(self):
        buttontxt=_("Sort!")
        text=_("Hey, you're not done with {ps} {profile} words by {check}!"
                "\nCome back when you have time; restart where you left "
                "off by pressing ‘{button}’").format(ps=self.ps,profile=self.profile,check=self.check,
                                                button=buttontxt)
        # self.withdraw()
        if not program['Demo']: #Should anyone see this?
            ErrorNotice(text=text,title=_("Not Done!"),parent=self,wait=True)
        # self.deiconify()
    def checktosort(self):
        return program['status'].checktosort() #bool tosort on cur check
    def itemstosort(self):
        return program['status'].sensestosort()
    def itemssorted(self):
        return program['status'].sensessorted()
    def tosort(self):
        return program['status'].tosort() #returns bool
    def updatesortingstatus(self):
        return program['settings'].updatesortingstatus()
    def verificationcode(self,**kwargs):
        check=kwargs.get('check',program['params'].check())
        group=kwargs.get('group',program['status'].group())
        # log.info("about to return {}={}".format(check,group))
        return check+'='+group
    def __init__(self):
        super().__init__()
class Segments(Senses):
    """docstring for Segments."""
    def buildregex(self,**kwargs):
        """include profile (of those available for ps and check),
        and subcheck (e.g., a: CaC\2)."""
        """Provides self.regex"""
        profile=kwargs.get('profile',program['slices'].profile())
        if profile is None:
            log.info(_("You haven't picked a syllable profile yet."))
            return
        self.regex=self.rxdict.makeprofileforcheck(
                        profile=profile,
                        check=kwargs.get('check',program['params'].check()),
                        group=kwargs.get('group',program['status'].group()),
                        groupcomparison=getattr(self,'groupcomparison',False)
                                                    )
    def buildregexnocheck(self,**kwargs):
        """This is the same as above, but should get all senses of a profile, regardless of check and value"""
        profile=kwargs.get('profile',program['slices'].profile())
        self.regex=self.rxdict.fromCV(profile,
                            word=True, compile=True, caseinsensitive=True)
    def ifregexadd(self,regex,form,id):
        # This fn is just to make this threadable
        if regex.search(form):
            self.output+=id
    def formspsprofile(self,**kwargs):
        """I think I want to move away from this"""
        log.info(_("Asked for forms to search for a data slice (only do once!)"))
        ps=kwargs.get('ps',program['slices'].ps())
        d=program['settings'].formstosearch[ps] #{form:sense}
        # log.info("Looking at {} entries".format(len(d)))
        return {k:d[k] for k in d
                        if set(d[k]) & set(program['slices'].senses(**kwargs))}
    def sensesbyforminregex(self,regex,**kwargs):
        """This function takes in a compiled regex,
        and outputs a list of senses."""
        ps=kwargs.get('ps',program['slices'].ps())
        # log.info("Kwargs keys: {} (formstosearch n={})".format(kwargs.keys(),
        #                                 len(kwargs['formstosearch'])))
        # log.info("Reduced to {} entries".format(len(dicttosearch)))
        # log.info("Looking for senses by regex {}".format(regex))
        self.output=[s for s in program['slices'].senses(**kwargs)
                                                    # program['db'].senses
                        if s.ftypes[self.ftype].textvaluebylang(self.analang)
                        if regex.search(
                        s.ftypes[self.ftype].textvaluebylang(self.analang)
                                        )
                    ]
        # log.info("Found senses: {}".format(self.output))
        return self.output
    def presortgroups(self,**kwargs):
        if program['status'].presorted(**kwargs):
            log.info(_("Presorting for this check/slice already done! ({args})"
                        "").format(args=kwargs))
            return
        log.info(_("Presorting"))
        cvt=kwargs.get('cvt',program['params'].cvt())
        ps=kwargs.get('ps',program['slices'].ps())
        profile=kwargs.get('profile',program['slices'].profile())
        # check=kwargs.get('check',program['params'].check())
        groups=program['status'].groups(wsorted=True,**kwargs)
        groups=program['status'].groups(cvt=cvt)
        #multiprocess from here?
        msg=_("Presorting ({check}={groups})").format(check=program['params'].check(),groups=groups)
        log.info(msg)
        w=self.getrunwindow(msg=msg)
        program['status'].renewsensestosort([],[]) #will repopulate
        # test this before implementing it:
        # kwargs['formstosearch']=self.formsthisprofile(**kwargs)
        """Find all relevant senseids, remove sorted ids for each group,
        them mark the remaining senses NA, then offer them to user in
        a modified verify page (new instructions, for those that DON'T
        fit the test)"""
        self.buildregexnocheck()
        # log.info(f"(presortgroups-buildregexnocheck) "
        #         f"cvt: {cvt}, profile: {profile}, "
        #         f"check: {check}; self.regex: {self.regex}")
        unsortedids=set(self.sensesbyforminregex(self.regex,ps=ps))
        for group in [i for i in groups if not i.isdigit()]:
            self.buildregex(group=group,cvt=cvt,profile=profile)
            # log.info(f"(presortgroups-buildregex) group: {group}, cvt: {cvt}, "
            #         f"profile: {profile}, "
            #         f"check: {check}; self.regex: {self.regex}")
            s=set(self.sensesbyforminregex(self.regex,ps=ps))
            if s: #senses just for this group
                self.presort(list(s),group)
                unsortedids-=s
        log.info(_("unsortedids ({count}): {ids}").format(
                                        count=len(unsortedids),
                                        ids=unsortedids
                                        ))
        if unsortedids:
            self.presort(unsortedids,group='NA')
            program['status'].group('NA')
            self.verify() #do this here, just this once.
        program['status'].presorted(True)
        program['status'].store() #after all the above
        self.maybewrite()
        self.runwindow.waitdone()
    def presort(self,senses,group):
        ftype=program['params'].ftype()
        for sense in senses:
            t = threading.Thread(target=self.marksortgroup,
                            args=(sense,group),
                            kwargs={#'check':check,
                                    # 'ftype':ftype,
                                    })
            t.start()
        t.join()
        # program['status'].marksensesorted(sense) #now in marksortgroup
        self.updatestatus(group=group) # marks the group unverified.
    def check_with_conflicting_value(self,annodict,check):
        """This tests for data where two checks should have the same value
        (e.g., V1 or V2 and V1=V2), but don't.
        Any piece overlapping is a problem, e.g., C1=C2 must agree with C2=C3.
        """
        not_conflicting=[None, 'NA'] #these values don't conflict; move on
        if annodict[check] in not_conflicting:
            return
        checkbits=check.split('=')
        for key in [i for i in annodict.keys() if i != check]:
            if annodict[key] in not_conflicting:
                continue
            keybits=key.split('=')
            """At least one must have 2+ elements, and they must share 1+
            element, but not their value."""
            if (len(keybits+checkbits) > 2 and set(keybits)&set(checkbits) and
                                    annodict[check] != annodict[key]):
                return True
    def updateformtoannotations(self,sense,check=None,write=False):
        """This should take a sense and check, in normal usage.
        provide self.ftype prior to this
        If we want to update forms to *all* annotations, don't give check.
        Iterate across a few or many senses.
        Iterate also across ftypes, to catch them all...
        that would likely need more smarts for affix and root distinction."""
        def maybe_add_polygraph(pg):
            sc=program['params'].cvt()
            scvalue=program['settings'].polygraphs[self.analang][sc][value]
            if not scvalue:
                scvalue=True
                program['settings'].setupCVrxs() #costly; only when needed!
        formvalue=sense.textvaluebyftypelang(self.ftype,self.analang)
        if not formvalue:
            log.info(_("updateformtoannotations didn't return a form value for "
                    "{id}, {check}, {ftype}, {ana}").format(id=sense.id, check=check, ftype=self.ftype, ana=self.analang))
            return
        # log.info("fnode: {}; text: {}".format(fnode,t.text))
        annodict=sense.annotationvaluedictbyftypelang(self.ftype,self.analang)
        conflict_text=_("Not updating ‘{form}’ (conflict in {anno}.").format(form=formvalue, anno=annodict)
        error_nb=_("\nCheck the log for any further conflicts")
        error=False
        if check: #just update to this annotation
            value=annodict[check]
            if value is None or value.isdigit(): #don't update to unnamed groups
                # log.info(f"Not updating {sense.id} form {formvalue} to "
                #         f"{check}={value}")
                return
            elif self.check_with_conflicting_value(annodict,check):
                if not self.updateconflictwarned:
                    ErrorNotice(conflict_text+error_nb)
                    self.updateconflictwarned=True
                else:
                    log.error(conflict_text)
                return
            elif value not in [None, 'NA']: #should I act on ''?
                formvalue=self.rxdict.update(formvalue,check,value)
                #This should update formstosearch:
                if formvalue != f:
                    program['settings'].addtoformstosearch(sense,f,formvalue)
                if len(value)>1:
                    maybe_add_polygraph(value)
                    
        else: #update to all annotations
            for check,value in annodict.items():
                if self.check_with_conflicting_value(annodict,check):
                    if not self.updateconflictwarned:
                        ErrorNotice(conflict_text+error_nb)
                        self.updateconflictwarned=True
                    else:
                        log.error(conflict_text)
                    error=True
                elif value in ['NA']:
                    pass #don't make changes for NA checks
                else:
                    # log.info(f"updateformtoannotations {check}={value},{formvalue}")
                    formvalue=self.rxdict.update(formvalue,check,value)
                    # log.info(f"updateformtoannotations {check}={value},{formvalue}")
        if not error:
            sense.textvaluebyftypelang(self.ftype,self.analang,formvalue)
        if write:
            self.maybewrite()
    def setitemgroup(self,item,check,group,**kwargs):
        # log.info(_("Setting segment sort group"))
        item.annotationvaluebyftypelang(self.ftype,self.analang,check,group)
    def updateformsallchecks(self):
        log.info(_("updateformsallchecks"))
        for sense in program['db'].senses: #do the whole dictionary
            self.updateformtoannotations(sense)
        #     u = threading.Thread(target=self.updateformtoannotations,
        #                         args=(sense), # w/o check, all done
        #                         )
        #     u.start()
        # try:
        #     u.join()
        # except:
        #     pass
        self.maybewrite()#after iteration
    def updateformsbycheck(self):
        for sense in self.getsensesincheck():
            u = threading.Thread(target=self.updateformtoannotations,
                                args=(sense,self.check), # w/o check, all done
                                )
            u.start()
        try:
            u.join()
        except:
            pass
        self.maybewrite()#after iteration
    def update_annotations_to_glyphs(self):
        for k in program['alphabet'].glyph_members():
            self.update_annotations_by_glyph(k)
    def update_annotations_by_glyph(self,glyph):
        """Once all sorting into groups and macrogroups is done, align groups to
        macrogroups.
        I need to think how to do this without risking merging groups:
        Go through glyph_members, and for each item with glyph≠group, change.
            if the new item exists already, rename it (int) first.
            int() groups will be renamed in iteration, since glyph≠group
        this may be more efficiently done with verification fields.
        
        This method does more than just annotations:
        
        LIFT verification,
        form data

        """
        def newform(x): #move this to alphabet
            return '_'.join(x.split('_')[:4]+[glyph])
        # log.info("update_annotations_by_glyph: checking if it is safe to "
        #         f"update items in ‘{glyph}’")
        gm=program['alphabet'].glyph_members()
        """If an annotation change would effectively join groups, e.g., Noun_CVCVC_lc_V1_ea
        would become Noun_CVCVC_lc_V1_ee, which already exists, stop. 
        """
        for item in gm[glyph]:
            if (item.split('_')[-1] != glyph and
                newform(item) in [i for j in gm.values() for i in j]):
                log.error(_("Conflict: cannot rename ‘{item}’ to ‘{glyph}’; "
                    "‘{new}’ already exists.").format(item=item, glyph=glyph, new=newform(item)))
                return
        log.info(_("update_annotations_by_glyph safely: ‘{members}’ to ‘{glyph}’").format(members=gm[glyph], glyph=glyph))
        for item in list(gm[glyph]):
            kwargs=program['alphabet'].parse_verificationcode(item)
            senses=program['slices'].inslice(
                            self.getsensesincheckgroup(**kwargs),
                            **kwargs)
            # log.info(f"Found {len(senses)} senses for {item}: {[i.id for i in senses]}")
            for sense in senses: #ps-profile only
                thread_name='_'.join([sense.id,glyph])
                u = threading.Thread(target=self.marksortgroup,
                                    args=(sense,glyph),
                                    kwargs={**{k:v for k,v in kwargs.items()
                                            if k != 'group'},
                                    # remove for testing this fn:
                                    # 'nocheck': True, #no lift verify
                                            'thread_name':thread_name,
                                            'not_sorting':True,
                                            'updateverification':True,
                                            'updateforms':False}) 
                                            #update all annotations first, then forms 
                self.track_thread(thread_name) #don't race the thread
                u.start()
            program['status'].renamegroup(kwargs.pop('group'),glyph,**kwargs)
            #above should rename throughout status 
            program['alphabet'].rename_glyph_member(item,newform(item))
        self.thread_update()
        try:
            u.join()
            log.info(_("Finished update_annotations_by_glyph threads for ‘{glyph}’").format(glyph=glyph))
        except UnboundLocalError: #if u.start() never happened...
            pass
        log.info(_("update_annotations_by_glyph done with ‘{members}’ to ‘{glyph}’").format(members=gm[glyph], glyph=glyph))
    def default_glyphs(self):
        return [i for i in 
                program['alphabet'].glyphdict()[program['params'].cvt()]
                if i.isdigit()]
    def name_new_glyphs(self):
        """Everything referenced here needs to refer to macrogroups ONLY.
        Users should never be changing the name of an individual sort group.
        This method is for default named groups (int), to see that they have
        some name, and is automatically enforced.
        Changes requested by the user are handled in TranscribeC/V
        """
        glyphs=self.default_glyphs()
        program['alphabet'].glyphdict()[program['params'].cvt()]
        if program['params'].cvt() == 'C':
            transcribe=TranscribeC
        elif program['params'].cvt() == 'V':
            transcribe=TranscribeV
        else:
            log.error(_("Not sure what to do with this glyph "
                "({cvt}; {glyphs})").format(cvt=program['params'].cvt(), glyphs=glyphs))
        w=transcribe(self)
        self.withdraw()
        w.waitdone()
        problems=[]
        while digits := self.default_glyphs():
            glyph=digits[0]
            log.info(_("working on {glyph} of {digits}").format(glyph=glyph, digits=digits))
            w.makewindow(glyph)
            if w.window_failed:
                #This removes verification, thus to do status:
                program['alphabet'].mark_glyph_not_done(glyph)
                problems.append(glyph)
            elif not w.ok_done: #user exits without 'OK'
                break
        w.destroy() #just this window, not parent
        self.deiconify()
        if digits or problems:
            log.error(_("User exited with work still to do: {digits} {problems}").format(digits=digits, problems=problems))
        return not bool(digits)
    def rename_macrogroup(self,x,y,updatestatus=False):
        for item in list(program['alphabet'].glyph_members()[x]):
            kwargs=program['alphabet'].parse_verificationcode(item)
            log.info(_("Updating verification from ‘{old}’ to ‘{new}’ for {args}").format(old=x, new=y, args=kwargs))
            self.rename_group_verification(x,y,**kwargs)
        #Do the above first, before glyph_members changes
        program['alphabet'].rename_glyph(x,y)
        self.update_annotations_by_glyph(y)
        if updatestatus: #only update status if forms
            program['settings'].reloadstatusdata()
    def getsensesincheck(self):
        return [
                i for i in program['db'].senses
                if i.ftypes[self.ftype].annotationkeyinlang(self.check)
                ]
    def getsensesingroup(self,check,group):
        ftype=program['params'].ftype()
        lang=program['params'].analang()
        return [
                i for i in program['db'].senses
                if i.ftypes[ftype].annotationvaluebylang(lang,check) == group
                ]
    def getitemgroup(self,item,check):
        # ftype=program['params'].ftype() #not helpful for Tone.getitemgroup
        return item.annotationvaluebyftypelang(self.ftype,self.analang,check)
    def __init__(self, parent):
        self.updateconflictwarned=False
        self.dodone=True
        self.dodoneonly=False #don't give me other words
        self.ftype=program['params'].ftype()
        self.rxdict=program['settings'].rxdict
class Sound(object):
    """This holds all the Sound methods, mostly for playing."""
    def donewpyaudio(self):
        try:
            self.pyaudio.terminate()
        except:
            log.info(_("Apparently self.pyaudio doesn't exist, or isn't initialized."))
    def pyaudiocheck(self):
        try:
            self.pyaudio.pa.get_format_from_width(1) #just check if its OK
        except:
            self.pyaudio=sound.AudioInterface()
    def makesoundsettings(self):
        if not hasattr(program['settings'],'soundsettings'):
            self.pyaudiocheck() #in case self.pyaudio isn't there yet
            program['settings'].soundsettings=sound.SoundSettings(self.pyaudio,
                        analang_obj=program['languages'].get_obj(self.analang)
                                                                )
    def loadsoundsettings(self):
        self.makesoundsettings()
        program['settings'].loadsettingsfile(setting='soundsettings')
        program['soundsettings']=program['settings'].soundsettings
        if program['hostname'] == 'karlap' and (
                        'cache_dir' not in program['soundsettings'].asr_kwargs
                        ):
            program['soundsettings'].asr_kwargs[
                                            'cache_dir']='/media/kentr/hfcache'
    def storesoundsettings(self):
        program['settings'].storesettingsfile(setting='soundsettings')
    def quittask(self):
        self.soundsettingswindow.destroy()
        program['taskchooser'].gettask()
        self.on_quit()
    def soundsettingscheck(self):
        if not hasattr(program['settings'],'soundsettings'):
            self.loadsoundsettings()
    def missingsoundattr(self):
        # log.info(dir(program['settings'].soundsettings))
        ss=program['settings'].soundsettings
        for s in ['fs', 'sample_format',
                    'audio_card_in',
                    'audio_card_out']:
            if hasattr(ss,s):
                if s+'s' in ss.hypothetical and (getattr(ss,s)
                                                not in ss.hypothetical[s+'s']):
                    log.info(_("Sound setting {setting} invalid; asking again").format(setting=s))
                    return True
                elif 'audio_card' in s and (getattr(ss,s)
                                                    not in ss.cards['dict']):
                    log.info(_("Sound setting {setting} invalid; asking again").format(setting=s))
                    return True
            else:
                log.info(_("Missing sound setting {setting}; asking again").format(setting=s))
                return True
        program['settings'].soundsettingsok=True
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
        return node.hassoundfile(recheck)
    def _configure_sound(self,event=None):
        sound_ui.SoundSettingsWindow(self)
    def setcontext(self,context=None):
        TaskDressing.setcontext(self)
        self.context.menuitem(_("Sound settings"),self._configure_sound)
        self.analang=program['db'].analang
    def __init__(self):
        self.audiodir=program['settings'].audiodir
        self.audiolang=program['params'].audiolang()
        self.program=program #make available to sound_ui
        self.soundcheck()
class Record(Sound): #TaskDressing
    """This holds all the Sound methods specific for Recording."""
    def makelabelsnrecordingbuttons(self,parent,node,r,c):
        # log.info("Making buttons for {} (in {})".format(node,parent))
        t=node.formatted(self.analang,self.glosslangs)
        lxl=ui.Label(parent, text=t,row=r,column=c+1,sticky='w')
        lcb=sound_ui.RecordButtonFrame(parent,self,node,
                                        row=r,column=c,sticky='w')
    def cleanup_pa(self,parentframe):
        import gc
        for w in parentframe.content.winfo_children():
            if type(w) is sound_ui.RecordButtonFrame:
                w.recorder.streamclose()
                w.player.streamclose()
        parentframe.destroy() #for now, at least
        gc.collect()
    def showentryformstorecordpage(self):
        #The info we're going for is stored above sense, hence guid.
        if self.runwindow.exitFlag.istrue():
            log.info(_('no runwindow; quitting!'))
            return
        if not self.runwindow.frame.winfo_exists():
            log.info(_('no runwindow frame; quitting!'))
            return
        self.runwindow.resetframe()
        ps=program['slices'].ps()
        profile=program['slices'].profile()
        count=program['slices'].count()
        text=_("Record {profile} {ps} Words: click ‘Record’, talk, "
                "and release ({count} words)").format(profile=profile,ps=ps,
                                                count=count)
        log.info(text)
        instr=ui.Label(self.runwindow.frame, anchor='w',text=text)
        instr.grid(row=0,column=0,sticky='w')
        senses=program['slices'].senses(ps=ps,profile=profile)
        if not senses: #i.e., no profile analysis yet
            senses=program['db'].senses
        nperpage=5
        pages=[senses[i:i+nperpage] for i in range(0,len(senses),nperpage)]
        log.info(_("pages: {pages}").format(pages=pages))
        for page in pages:
            if self.runwindow.exitFlag.istrue():
                return
            self.runwindow.wait(thenshow=True)
            buttonframes=ui.ScrollingFrame(self.runwindow.frame,
                                            row=1,column=0,sticky='w')
            row=0
            done=list()
            # log.info("Looking through entries now")
            for row,entry in enumerate([i.entry for i in page]):
                self.runwindow.column=0
                if entry.guid in done: #only the first of multiple senses
                    continue
                else:
                    done.append(entry.guid)
                """These following two have been shifted down a level, and will
                now return a list of form elements, each. Something will need to be
                adjusted here..."""
                ftypes=['lc','pl','imp']
                # for f in ftypes:
                #     log.info(f"{f}: {entry.sense.nodebyftype(f)}, "
                #                 f"{type(entry.sense.nodebyftype(f))}")
                for node in [entry.sense.nodebyftype(f) for f in ftypes
                                if entry.sense.nodebyftype(f)]:
                    self.runwindow.column+=2
                    # sense['nodetoshow']=sense[node]
                    self.makelabelsnrecordingbuttons(buttonframes.content,node,
                        row,self.runwindow.column)
                # row+=1
            # log.info("Done iterating for one page")
            ui.Button(buttonframes.content,column=1,row=row,
                        text=_("Next {count} words").format(count=nperpage),
                        cmd=lambda x=buttonframes:self.cleanup_pa(x))
            # log.info("Showing waitwindow now")
            self.runwindow.waitdone()
            buttonframes.wait_window(buttonframes)
        if not self.runwindow.exitFlag.istrue():
            self.runwindow.wait_window(self.runwindow.frame)
    def showentryformstorecord(self,justone=False):
        # Save these values before iterating over them
        #Convert to iterate over local variables
        self.getrunwindow()
        if justone or not program['slices'].valid():
            self.showentryformstorecordpage()
        else:
            #store for later
            ps=program['slices'].ps()
            profile=program['slices'].profile()
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
                    text='({} {}/{})'.format(*progress)
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
                    log.info(_("Not showing example with text {text}").format(text=text))
                    continue
                row+=1
                """If I end up pulling from example nodes elsewhere, I should
                probably make this a function, like getframeddata"""
                if not text:
                    exit()
                rb=sound_ui.RecordButtonFrame(examplesframe,self,example)
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
            self.runwindow.on_quit()
            self.showtonegroupexs()
        if (not(hasattr(self,'examplespergrouptorecord')) or
            (type(self.examplespergrouptorecord) is not int)):
            self.examplespergrouptorecord=100
            program['settings'].storesettingsfile()
        self.makeanalysis()
        self.analysis.donoUFanalysis()
        torecord=self.analysis.sensesbygroup
        ntorecord=len(torecord) #number of groups
        nexs=len([k for i in torecord for j in torecord[i] for k in j])
        nslice=program['slices'].count()
        log.info(_("Found {analyzed} analyzed of {total} examples in slice").format(analyzed=nexs, total=nslice))
        skip=False
        if ntorecord == 0:
            log.error(_("How did we get no UR tone groups? {profile}-{ps}"
                    "\nHave you run the tone report recently?"
                    "\nDoing that for you now...").format(
                            profile=program['slices'].profile(),
                            ps=program['slices'].ps()
                                                         ))
            self.analysis.do()
            self.showtonegroupexs()
            return
        batch={}
        # log.info(f"program['db'].sensedict ({len(program['db'].sensedict)}): "
        #         f"{program['db'].sensedict}")
        for i in range(self.examplespergrouptorecord):
            batch[i]=[]
            for ufgroup in torecord:
                print(i,len(torecord[ufgroup]),ufgroup,torecord[ufgroup])
                if len(torecord[ufgroup]) > i: #no done piles.
                    # sense=[program['db'].sensedict[torecord[ufgroup][i]]] #list of one
                    sense=torecord[ufgroup][i] #list of one
                else:
                    print("Not enough examples, moving on:",i,ufgroup)
                    continue
                log.info(_('Giving user the number {count} example from tone '
                        'group {group}').format(count=i,group=ufgroup))
                exited=self.showsenseswithexamplestorecord([sense],
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
        log.info(_("Looking for file names for {node} ({tag})").format(node=node, tag=node.tag))
        ps=program['slices'].ps()
        print("ps:",ps)
        if ps:
            pslocopts=[ps]
        else:
            pslocopts=[]
        # Except for data generated early in 2021, profile should not be there,
        # because it can change with analysis. But we include here to pick up
        # old files, in case they are there but not linked.
        # First option (legacy):
        # pslocopts.insert(0,ps+'_'+self.parent.taskchooser.slices.profile())
        profile=program['slices'].profile()
        if ps and profile:
            pslocopts.insert(0,ps+'_'+profile)
        fieldlocopts=[None] #none is OK
        try:
            l=node.locationvalue()
            #the last option is taken, if none are found
            pslocopts.insert(0,ps+'-'+l) #the first option.
            fieldlocopts.append(l) #make this the last option.
        except AttributeError:
            # log.info(_("doesn't look like an example node; not offering location"))
            pass
                    # Yes, these allow for location to be present twice, but
                # that should never be found, nor offered
        if not pslocopts:
            pslocopts=[None] #make this an iterable, none is OK
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
                            log.error(_("No {ana} analang in "
                                "{id}! (OK if recording first; "
                                "forms: {forms})").format(ana=self.analang,
                                id=node.sense.id,
                                forms=node.textvaluedict()))
                        args+=[form] #[self.ftype]]
                        for l in self.glosslangs:
                            args+=[node.glossbylang(l)]
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
        """If node is already marked with sound file attributes, we're done"""
        if self.hassoundfile(node):
            return
        """Otherwise, generate prioritized list of name options"""
        filenames=self.filenameoptions(node)
        """if any of the generated filenames are there, stop at the first one"""
        for f in filenames:
            if self.audioexists(f):
                log.info(_("Audiofile {file} found at {url}").format(file=f, url=self.audioURL(f)))
                node.textvaluebylang(lang=program['params'].audiolang(),value=f)
                if self.hassoundfile(node,recheck=True):
                    log.info("file {} linked in LIFT".format(node.audiofileURL))
                break
        """If none found, be ready to write with last/highest priority option"""
        f=filenames[-1]
        log.debug(_("No audio file found, but ready to record: "
                    )+"{file}; {url_label}:{url}".format(file=f, url_label=_("url"), url=self.audioURL(f)))
        """Should be able to just send f"""
        node.audiofilenametoput=f #don't write this until we actually record
        node.audiofileURL=self.audioURL(f)
        log.info(_("Finishing makeaudiofilename with {file} "
                "and {url}").format(file=node.audiofilenametoput, url=node.audiofileURL))
    def mikecheck(self):
        """This starts and stops the UI"""
        self.withdraw()
        self.pyaudiocheck()
        #will need to add sound_ui in here, once generalized:
        self.soundsettingswindow=sound_ui.SoundSettingsWindow(self)
        self.soundsettingswindow.protocol("WM_DELETE_WINDOW", self.quittask)
        if not self.soundsettingswindow.exitFlag.istrue():
            self.soundsettingswindow.wait_window(self.soundsettingswindow)
        self.donewpyaudio()
        self.deiconify()
        if not self.exitFlag.istrue() and self.soundsettingswindow.winfo_exists():
            self.soundsettingswindow.destroy()
    def _configure_transcription(self,event=None):
        sound_ui.ASRModelSelectionWindow(self)
    def setcontext(self,context=None):
        Sound.setcontext(self)
        self.context.menuitem(_("Transcription settings"),
                                    self._configure_transcription)
    def __init__(self,parent):
        Sound.__init__(self)
        self.soundsettings.load_ASR() #after file settings are loaded
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
            log.info(_("Limiting segment work to this slice"))
            all=[i.entry for i in program['slices'].senses()]
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
        log.info(_("To do: ({count}) First 5: {items}").format(count=len(todo),items=todo[:5]))
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
                    "morpheme in {name} \n(consonants and vowels only)?"
                    "").format(name=program['settings'].languagenames[lang])
            ok=_('Use this form')
            skip=None
        else:
            text=_("What does ‘{form}’ mean in {lang}?").format(
                            form=self.runwindow.form[self.analang],
                            lang=program['settings'].languagenames[lang])
            ok=_("Use this {lang} gloss for ‘{form}’").format(
                            lang=program['settings'].languagenames[lang],
                            form=self.runwindow.form[self.analang])
            self.runwindow.glosslangs.append(lang)
            skip = _("Skip {lang} gloss").format(lang=program['settings'].languagenames[lang])
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
                                    text=self.runwindow.form[lang],
                                    font='readbig',
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
        self.runwindow.lift()
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
        title=_("Add {lang} morpheme to the dictionary").format(
                            lang=program['settings'].languagenames[self.analang])
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
        """get the new sense back from this function, which generates it"""
        if not self.runwindow.exitFlag.istrue(): #don't do this if exited
            self.runwindow.withdraw() #or wait?
            sense=program['db'].addentry(ps='',analang=self.analang,
                            glosslangs=self.runwindow.glosslangs,
                            form=self.runwindow.form)
            # Update profile information in the running instance, and in the file.
            self.runwindow.on_quit()
            """The following are useless without ps information, so they will
            have to come later."""
    def addCAWLentries(self):
        text=_("Adding CAWL entries to fill out, in established database.")
        self.wait(msg=text)
        log.info(text)
        self.cawldb=loadCAWL()
        added=[]
        modded=[]
        for n in program['taskchooser'].cawlmissing:
            log.info(_("Working on SILCAWL line #{line:04}.").format(line=n))
            e=self.cawldb.get('entry', path=['cawlfield'],
                                    cawlvalue='{:04}'.format(n),
                                    ).get('node')[0] #certain to be there
            try:
                eps=self.cawldb.get('sense/ps',node=e,
                                    # showurl=True
                                    ).get('node')[0]
                #This is reading values from template, which are 'Noun' & 'Verb'
                epsv=eps.get('value')
            except IndexError:
                log.info(_("line {line} w/o lexical category; leaving.").format(line=n))
                eps=epsv=None
            if epsv == 'Noun': #don't translate!
                log.info(_("Found a noun, using {ps}").format(ps=program['settings'].nominalps))
                eps.set('value',program['settings'].nominalps)
            elif epsv == 'Verb': #don't translate!
                log.info(_("Found a verb, using {ps}").format(ps=program['settings'].verbalps))
                eps.set('value',program['settings'].verbalps)
            else:
                log.error(_("Not sure what to do with ps {ps} ({node})").format(ps=epsv,node=eps))
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
                    log.info(_("Found gloss of SILCAWL line #{line:04} ({gloss}); "
                            "adding info to that entry.").format(line=n,gloss=g))
                    program['db'].fillentryAwB(entry[0],e)
                    modded.append(n)
                    break
            if not entry: #i.e., no match for any self.glosslangs gloss
                tnodes=e.findall('lexical-unit/form/text')
                for tn in tnodes:
                    tn.text=''
                log.info(_("Gloss of SILCAWL line #{line:04} ({gloss}) not found; "
                        "copying over that entry.").format(line=n,gloss=g))
                program['db'].nodes.append(e)
                added.append(n)
        if added or modded:
            program['db'].write()
            title=_("Entries Added!")
            text=_("Added {count} entries from the SILCAWL").format(count=len(added))
            if len(added)<100:
                text+=': ({})'.format(added)
            text+=_("\nModded {} entries with new information from the "
                    "SILCAWL").format(len(modded))
            if len(modded)<100:
                text+=': ({})'.format(modded)
            program['taskchooser'].getcawlmissing()
            self.dobuttonkwargs()
        else:
            title=_("Error trying to add SILCAWL entries")
            text=_("We seem to have not added or modded any entries, which "
                    "shouldn't happen! (missing: {missing})"
                    "").format(missing=program['taskchooser'].cawlmissing)
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
            log.info(_("Not storing {id}, by request").format(id=self.sense.id))
        if self.index < len(self.entries)-1:
            self.index+=1
        else:
            self.index=1
        self.getword()
    def backword(self,nostore=True):
        self.dirfn=self.backword
        if not nostore:
            self.storethisword()
        else:
            log.info(_("Not storing {id}, by request").format(id=self.sense.id))
        if self.index == 0:
            self.index=len(self.entries)-1
        else:
            self.index-=1
        self.getword()
    def storethisword(self):
        log.info(_("Trying to store {value} ({type})").format(value=self.var.get(),type=self.ftype))
        try:
            if self.ftype in ['lc','lx']:
                self.sense.textvaluebyftypelang(self.ftype,
                                            self.analang,
                                            self.var.get())
            elif self.ftype == 'pl':
                self.entry.plvalue(
                    program['settings'].secondformfield[program['settings'].nominalps],
                    self.var.get())
                # lift.prettyprint(self.entry.pl)
            elif self.ftype == 'imp':
                self.entry.fieldvalue(
                        program['settings'].secondformfield[program['settings'].verbalps],
                        self.var.get())
            # self.entry.lc.textvaluebylang(self.analang,self.var.get())
            self.maybewrite() #only if above is successful
            # lift.prettyprint(self.entry)
        # except KeyError:
        except AttributeError as e:
            log.info(_("Not storing word (WordCollection): {error}").format(error=e))
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
    def selectlocalimage(self,w=None,event=None):#w is window to close on OK
        log.info(_("Select a local image"))
        title = _("Select Example Image File"),
        filetypes=[
                ("PNG Image File",'.[Pp][Nn][Gg]'),
                ("GIF Image File",'.[Gg][Ii][Ff]'),
                ("BMP Image File",'.[Bb][Mm][Pp]'),
                ]
        f=file.askopenfilename(title=title,filetypes=filetypes)
        if f and file.exists(f):
            self.markimage(f,w)
    def showimagestoselect(self,files):
        self.imagecolumns=3
        self.imagepixels=0
        pixelopts=range(200,1000,100)
        colopts=range(1,9)
        def makegrid(cols=0,pixels=0):
            if cols:
                self.imagecolumns=iteratelistitem(colopts,
                                                    self.imagecolumns,cols)
            if pixels:
                if not self.imagepixels: #allows native resolution until tweaked
                    self.imagepixels=pixelopts[int(len(pixelopts)/2)]
                self.imagepixels=iteratelistitem(pixelopts,
                                                    self.imagepixels,pixels)
            if hasattr(self.selectionwindow,'sf'):
                self.selectionwindow.sf.destroy()
            self.selectionwindow.sf=ui.ScrollingFrame(
                        self.selectionwindow.frame,row=2,column=0)
            for n,f in enumerate(files):
                # log.info("Using row {}, col {}".format(n//cols,n%cols))
                    i=ImageFrame(self.selectionwindow.sf.content,url=f,
                                pixels=self.imagepixels,
                                row=n//self.imagecolumns,
                                column=n%self.imagecolumns,
                                sticky='nsew')
                    if i.image:
                        i.bindchildren('<ButtonRelease-1>',
                                        lambda event,x=f,w=self.selectionwindow:
                                                self.markimage(x,w))
            """activate and inactivate buttons as appropriate"""
            for t in bdict:
                if t == pixelopts:
                    val=self.imagepixels
                else:
                    val=self.imagecolumns
                for v in bdict[t]:
                    if not val or t.index(val)+v in range(0,len(t)):
                        bdict[t][v]["state"] = "normal"
                    else:
                        bdict[t][v]["state"] = "disabled"
            self.selectionwindow.update_idletasks()
        log.info(_("Select from these images: \n{files}").format(files='\n'.join(
                                                    [str(i) for i in files])))
        self.selectionwindow=ui.Window(self)
        title=_("Select a good image for {glosses}").format(glosses=self.glossesthere)
        self.selectionwindow.title(title)
        t=ui.Label(self.selectionwindow.frame,text=title, font='title',
                    row=0,column=0)
        currentimage=scaleimageifthere(self.sense)
        if currentimage:
            t['image']=currentimage
            t['compound']='right'
        imageparameters=ui.Frame(self.selectionwindow.frame,
                                row=1, column=0, sticky='e')
        fontsize='small'
        parameterseparation=10
        ui.Button(imageparameters,text=_("Browse"), font='small',
            command=lambda x=self.selectionwindow:self.selectlocalimage(w=x),
            ipady=0,row=0,column=imageparameters.ncolumns())
        ui.Label(imageparameters,text="", font=fontsize,
                    width=parameterseparation,
                    row=0,column=imageparameters.ncolumns())
        bdict={pixelopts:{},colopts:{}}
        bdict[pixelopts][-1]=ui.Button(imageparameters,text='-', font=fontsize,
                            command=lambda x=-1:makegrid(pixels=x),ipady=0,
                            width=1,row=0,column=imageparameters.ncolumns())
        ui.Label(imageparameters,text=_("Image Size"), font=fontsize, padx=2,
                    row=0,column=imageparameters.ncolumns())
        bdict[pixelopts][1]=ui.Button(imageparameters,text='+', font=fontsize,
                            command=lambda x=1:makegrid(pixels=x),ipady=0,
                            width=1,row=0,column=imageparameters.ncolumns())
        ui.Label(imageparameters,text="", font=fontsize,
                    width=parameterseparation,
                    row=0,column=imageparameters.ncolumns())
        bdict[colopts][-1]=ui.Button(imageparameters,text='-', font=fontsize,
                            command=lambda x=-1:makegrid(cols=x),ipady=0,
                            width=1,row=0,column=imageparameters.ncolumns())
        ui.Label(imageparameters,text=_("Columns"), font=fontsize, padx=2,
                    row=0,column=imageparameters.ncolumns())
        bdict[colopts][1]=ui.Button(imageparameters,text="+", font=fontsize,
                            command=lambda x=1:makegrid(cols=x),ipady=0,
                            width=1,row=0,column=imageparameters.ncolumns())
        makegrid()
    def getimagefiles(self):
        dir=file.fullpathname(self.sense.imgselectiondir)
        if file.exists(dir):
            return dir,[i for i in file.getfilesofdirectory(dir)
                                if "terms.txt" not in str(i)]
        else:
            log.info(_("{dir} doesn't seem to exist.").format(dir=dir))
    def selectimageormoveon(self,event=None):
        if self.selectimage():
            self.nextword(nostore=False)
    def selectimage(self,event=None):
        dir,files=self.getimagefiles()
        n=len(files)
        if n >50:
            ErrorNotice(_("There are too many images to show! ({count})").format(count=n))
            files=files[:10]
        if not files:
            log.info(_("{dir} seems there, but empty.").format(dir=dir))
            self.getopenclipart()
            dir,files=self.getimagefiles()
        if files:
            self.showimagestoselect(files)
        else:
            log.info(_("There don't seem to be any images to show."))
            return 1
    def downloadallCAWLimages(self):
        for self.sense in program['db'].senses:
            if not file.exists(self.sense.imgselectiondir):
                self.getopenclipart(nogui=True)
    def getopenclipart(self,event=None,nogui=False):
        log.info(_("Not getting from openclipart.org"))
        return #this isn't really what we want right now
        if not self.sense.collectionglosses:
            log.info(_("No English glosses to search OpenClipart.org! ({glosses})").format(glosses=self.sense.glosses))
            if self.sense.imgselectiondir:
                # logic to pull English terms from folder names
                self.sense.collectionglosses=[i for i in
                                        str(self.sense.imgselectiondir).split('/')[-1].split('_')
                                        if not isinteger(i)]
        self.wait(msg=_("Dowloading images from OpenClipart.org\n{glosses}"
                        "").format(glosses=" ".join(self.sense.collectionglosses)),
                    cancellable=True)
        log.info(_("Glosses: {glosses}").format(glosses=self.sense.collectionglosses))
        scraper=htmlfns.ImageScraper()
        for gloss in self.sense.collectionglosses:
            kwargs={'per_page':50,
                    'query':gloss #just one word at a time is less restrictive
                    }
            terms=urls.urlencode(kwargs)
            url='https://openclipart.org/search/?'+terms
            # https://publicdomainvectors.org/en/search/head
            # These two are more full-colored images, rather than line drawings:
            # https://pixabay.com/images/search/head/
            # https://pxhere.com/en/photos?q=head&search=had
            try:
                html=htmlfns.getdecoded(url)
            except urls.MaxRetryError as e:
                self.waitdone()
                msg=_("Problem downloading webpage; check your "
                            "internet connection!\n\n{error}").format(error=e)
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
        log.info(_("Found {count} images: {images}").format(count=len(self.images),images=self.images))
        if self.images:
            file.makedir(self.sense.imgselectiondir)
        problems=0
        for i in self.images:
            if self.waitcancelled:
                break
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
                log.error(_("Problem downloading image: {error}").format(error=e))
                problems+=1
            self.waitprogress(self.images.index(i)*100/len(self.images))
        if (me and not nogui) or len(self.images) < 5:
            text=_("Found {count} images!").format(count=len(self.images))
            if problems:
                text+=_("\nProblems downloading {count} images").format(count=problems)
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
        log.info(_("doing word frame"))
        self.wordframe=ui.Frame(self.wordsframe,row=1,column=0,sticky='ew')
        self.prog=ui.Label(self.wordframe, text='', row=1, column=3,
                            font='small')
        self.glossesline=ui.Label(self.wordframe, text='',
                                    font='read',
                                    row=1, column=0, columnspan=3, sticky='ew')
        back=ui.Button(self.wordframe,text=_("Back"),cmd=self.backword,
                        row=4, column=0, sticky='w',anchor='w')
        self.instructions2=ui.Label(self.wordframe,text='',font='small',
                        row=4, column=1, sticky='ew',anchor='c')
        next=ui.Button(self.wordframe,text=_("Next"),cmd=self.nextword,
                        row=4, column=2, sticky='e',anchor='e')
        self.var=ui.StringVar()
        self.lxenter=ui.EntryField(self.wordframe,text=self.var,
                                font='readbig',
                                row=5,column=0,columnspan=3,
                                sticky='ew')
        if isinstance(self.task,Parse):
            self.parsebutton=ui.Label(self.wordframe,
                                        text=self.cparsetext,
                                        row=6, column=1,
                                        sticky='w',
                                        anchor='w')
        next.bind_all('<Up>',lambda event: self.backword(nostore=True))
        next.bind_all('<Prior>',lambda event: self.backword(nostore=True))
        next.bind_all('<Down>',lambda event: self.nextword(nostore=True))
        next.bind_all('<Next>',lambda event: self.nextword(nostore=True))
    def updatereturnbind(self):
        log.info(_("Updating binding ({state})").format(state=self.state()))
        if self.state() == 'withdrawn':
            self.unbind_all('<Return>')
        else: #only bind to non-withdrawn window
            # try: #re-institute this section once pics have good defaults
            #     assert self.wordframe.pic.hasimage
            self.lxenter.bind_all('<Return>',
                                lambda event: self.nextword(nostore=False))
            #     log.info("Return now moves to next word")
            # except AssertionError:
            #     self.wordframe.pic.bind_all('<Return>',
            #                                         self.selectimageormoveon)
            #     log.info("Return now selects image, or moves on")
    def set_up_transcription(self):
        pass
    def getword(self):
        program['taskchooser'].withdraw()# not sure why necessary
        # log.info("sensetodo: {}".format(getattr(self,'sensetodo',None)))
        # log.info("wordframe: {}".format(getattr(self,'wordframe',None)))
        # log.info("index: {}".format(self.index))
        if getattr(self,'sensetodo',None) is not None:
            # log.info("Sense to do: {}".format(self.sensetodo))
            # log.info("self.sensetodo.entry: {}".format(self.sensetodo.formatted(self.analang,self.glosslangs)))
            self.entry=self.sensetodo.entry
            self.sensetodo=None
            try:
                self.index=self.entries.index(self.entry)
            except Exception as e:
                log.info(_("self.entry doesn't seem to be in entries; OK for now"))
            self.instructions['text']=self.getinstructions() #in case changed
            self.dowordframe()
        elif not self.entries:
            text=_("It looks like you're done filling out the empty "
            "entries in your database! Congratulations! \nYou can still add words "
            "through the button on the left ({text})."
            "").format(text=self.dobuttonkwargs()['text'])
            self.killwordframe()
            self.instructions['text']=text
            self.instructions.wrap()
            return
        else:
            self.dowordframe()
            self.entry=self.entries[self.index]
        log.info(_("sensetodo: {todo}").format(todo=getattr(self,'sensetodo',None)))
        log.info(_("wordframe: {frame}").format(frame=getattr(self,'wordframe',None)))
        self.prog['text']='({}/{})'.format(self.index+1,self.nentries)
        # log.info("entries: {}".format(self.entries))
        log.info(_("index: {index}").format(index=self.index))
        self.sense=self.entry.sense
        glosses={}
        for g in set(self.glosslangs) & set(self.sense.glosses):
            glosses[g]=', '.join(self.sense.formattedgloss(g,quoted=True))
        self.glossesthere=' — '.join([glosses[i] for i in glosses if i])
        # log.info("glosses there: {}".format(self.glossesthere))
        if not self.glossesthere:
            log.info(_("entry {id} doesn't have glosses; not showing.").format(id=self.entry.get('id')))
            self.dirfn(nostore=True)
        self.glossesline['text']=self.glossesthere
        self.glossesline.wrap()
        if isinstance(getattr(self.wordframe,'pic',None),ImageFrame):
            self.wordframe.pic.changesense(self.sense)
        else:
            self.wordframe.pic=ImageFrame(self.wordframe, self.sense,
                                            pixels=300,
                                            row=2, column=0,
                                            columnspan=3, sticky='')
        self.updatereturnbind()
        """I don't want this on every ImageFrame, just here"""
        self.wordframe.pic.bindchildren('<ButtonRelease-1>', self.selectimage)
        default=self.sense.textvaluebyftypelang(self.ftype,self.analang)
        if not default:
            default=''
        self.var.set(default)
        self.set_up_transcription() #for tasks with it
        if isinstance(self.task,Parse):
            log.info(self.currentformsforuser(entry=self.entry))
            self.updateparseUI()
            if self.cparsetext.get():
                self.parsebutton.bind('<ButtonRelease-1>',
                                        lambda event,
                                        entry=self.entry:self.parse_foreground(
                                        entry=entry))
            else:
                self.parsebutton.unbind('<ButtonRelease-1>')
        self.lxenter.focus_set()
        self.frame.grid_columnconfigure(1,weight=1)
        self.deiconify()
        self.lift()
        self.wordframe.update_idletasks()
    def __init__(self, parent):
        Segments.__init__(self,parent)
        self.dodone=False
class WordCollectionwRecordings(WordCollection,Record):
    def getinstructions(self):
        return _("Record a word in your language that goes with these "
                "meanings."
                "\nGive just a single word (not a phrase) wherever possible."
                # "\nClick-Speak-Release on the record button."
                )
    def set_up_transcription(self):
        self.set_transcription_fields()
        self.set_transcription_frame(row=3,column=0,colspan=2) #instructions2
    def set_transcription_fields(self,**kwargs):
        ftype=kwargs.pop('ftype',self.ftype)
        self.transcription_var=ui.StringVar()
        self.transcription_ipa_var=ui.StringVar()
        self.transcription_tone_var=ui.StringVar()
        self.transcription_var.trace_add('write', self.show_drafts)
        self.transcription_ipa_var.trace_add('write', self.store_phonetic)
        self.transcription_tone_var.trace_add('write', self.store_tone)
        if ftype not in self.entry.fields: #Need this to record to
            if ftype == 'lx':
                self.entry.lx=lift.Lexeme(self.entry)
            elif ftype == 'lc':
                self.entry.lx=lift.Citation(self.entry)
            else:
                self.entry.fields[ftype]=lift.Field(self.entry,ftype=ftype)
    def set_transcription_frame(self,**kwargs):
        ftype=kwargs.pop('ftype',self.ftype)
        try:
            self.wordframe.recordFrame.destroy()#don't leave this around!
        except:
            pass
        log.info(f"setting frame with settings: {self.soundsettings}")
        self.wordframe.recordFrame=sound_ui.RecordnTranscribeButtonFrame(
                        self.wordframe,
                        self, #task
                        self.entry.fields[ftype],#node,
                        transcription_var=self.transcription_var,
                        transcription_ipa_var=self.transcription_ipa_var,
                        transcription_tone_var=self.transcription_tone_var,
                        # show_transcriptions=True, #this typically in Entry
                        # show_transcriptions_ipa=True,
                        show_tone=True,
                        shown='none',
                        sticky='ew',
                        **kwargs
                    )
    def show_drafts(self,*args):
        # log.info(f"show_drafts got args {args}")
        instructions2=("click on the best option(s) above\n "
                        "correct the consonants and vowels below.")
        try:
            self.wordframe.draftFrame.destroy()
        except:
            pass
        content=self.wordframe.recordFrame.recorder.transcriptions
        log.info(f"Recorder returned {len(content)} transcriptions")
        if len(content) == 1:
            self.var.set(list(content.values())[0]) #value of first (only) option
            return
        c,r=self.wordframe.recordFrame.grid_size()
        self.wordframe.draftFrame=ui.Frame(self.wordframe.recordFrame,
                                            column=c,
                                            row=0
                                        )
        self.wordframe.toneFrame=ui.Label(self.wordframe.recordFrame,
                                            column=c,
                                            row=1
                                        )
        # log.info(f"{content=}")
        content=sorted(content.items(),key=lambda x: len(x[1]))
        # log.info(f"{content=}")
        aspect=3/4 #float OK
        nrows=max(3,int((len(content)*aspect)**.5))
        buttons=0
        max_len=20 #don't want words kicking buttons off the page...
        for repo,line in content:
            ui.Button(self.wordframe.draftFrame,
                text=line[:max_len],
                command=lambda x=repo,y=line:self.draft_entry(x,y),
                column=buttons//nrows,
                row=buttons%nrows,
            )
            buttons+=1
        self.instructions2['text']=instructions2
        if self.transcription_tone_var.get():
            self.wordframe.toneFrame['text']=self.transcription_tone_var.get()
        else:
            self.wordframe.toneFrame['text']=''

    def draft_entry(self,repo,value,*args):
        # This just fills in the visible field. Dictionary may be
        # overwritten on confirmation later
        # This is only called when a user clicks on a button, not
        # automatically, so it should always overwrite the entry field
        program['soundsettings'].tally_asr_repo(repo)
        self.var.set(value)
        self.update_idletasks()
        program['settings'].storesettingsfile(setting='soundsettings')
        log.info(program['soundsettings'].asr_repo_tally())
    def store_phonetic(self,*args):
        #Need to fix this; format isn't correct
        self.entry.fieldvalue(self.ftype,
                        program['db'].phoneticlangname(machine=True),
                        value=self.transcription_ipa_var.get().split('\n')[0]
                        )
    def store_tone(self,*args):
        self.entry.fieldvalue(self.ftype,
                        program['db'].tonelangname(machine=True),
                        value=self.transcription_tone_var.get()
                        )
    def __init__(self, parent):
        Record.__init__(self,parent)
        WordCollection.__init__(self,parent)
class WordCollectionLexeme(TaskDressing,WordCollection):
    def tooltip(self):
        return _("Don't use this task.")
    def tasktitle(self):
        return _("Word Collection for Lexeme Forms")
    def __init__(self, parent): #frame, filename=None
        """This should never really be used, though I made it first, so I've
        left it"""
        self.ftype=program['params'].ftype('lx') #lift.Entry.citationformnodeofentry
        TaskDressing.__init__(self,parent)
        WordCollection.__init__(self,parent)
        log.info("Initializing {}".format(self.tasktitle()))
        #Status frame is 0,0
        self.getwords()
class WordCollectionCitation(TaskDressing,WordCollection):
    def tooltip(self):
        return _("This task helps you collect words in citation form.")
    def tasktitle(self):
        return _("Add Words") # for Citation Forms
    def __init__(self, parent): #frame, filename=None
        self.ftype=program['params'].ftype('lc') #lift.Entry.citationformnodeofentry
        TaskDressing.__init__(self,parent)
        WordCollection.__init__(self,parent)
        log.info("Initializing {}".format(self.tasktitle()))
        #Status frame is 0,0
        self.getwords()
class WordCollectionCitationwRecordings(WordCollectionwRecordings,TaskDressing):
    def tooltip(self):
        return _("This task helps you collect words in citation form through "
                "recordings with automatic transcription drafts.")
    def tasktitle(self):
        return _("Add Words with Audio") # for Citation Forms
    def __init__(self, parent): #frame, filename=None
        self.ftype=program['params'].ftype('lc') #lift.Entry.citationformnodeofentry
        TaskDressing.__init__(self,parent)
        WordCollectionwRecordings.__init__(self,parent)
        log.info("Initializing {}".format(self.tasktitle()))
        self.getwords()
class WordCollectionPlural(TaskDressing,WordCollection):
    def tooltip(self):
        return _("This task helps you collect plural word forms.")
    def tasktitle(self):
        return _("Add plural forms")
    def __init__(self, parent):
        self.ftype=program['params'].ftype('pl')
        TaskDressing.__init__(self,parent)
        WordCollection.__init__(self,parent)
        if not program['settings'].secondformfieldsOK():
            ErrorNotice(_("To collect Plural forms, you must first "
                            "define which fields should contain those forms"),
                            wait=True)
            self.shutdowntask()
            return
        log.info("Initializing {}".format(self.tasktitle()))
        #Status frame is 0,0
        # self.nodetag='citation' #lift.Entry.citationformnodeofentry
        self.getwords()
class WordCollectionImperative(TaskDressing,WordCollection):
    def tooltip(self):
        return _("This task helps you collect imperative word forms.")
    def tasktitle(self):
        return _("Add imperative forms")
    def __init__(self, parent):
        self.ftype=program['params'].ftype('imp')
        TaskDressing.__init__(self,parent)
        WordCollection.__init__(self,parent)
        if not program['settings'].secondformfieldsOK():
            ErrorNotice(_("To collect Imperative forms, you must first "
                            "define which fields should contain those forms"),
                            wait=True)
            self.shutdowntask()
            return
        log.info("Initializing {}".format(self.tasktitle()))
        #Status frame is 0,0
        # self.nodetag='citation' #lift.Entry.citationformnodeofentry
        self.getwords()
class Parse(Segments):
    """docstring for Parse."""
    def getgloss(self,ftype=None):
        return ', '.join([', '.join(self.parser.sense.formattedgloss(l,
                                                            ftype=ftype,
                                                            quoted=True))
                        for l in self.glosslangs])
    def userconfirmation(self,*args):
        log.info("asking for user confirmation")
        # Return True or False only
        def do(x):
            log.info("doing {}".format(x))
            if type(x) is ui.StringVar:
                log.info("Found StringVar: {}".format(x.get()))
                self.fixroot(x.get())
                #keep userresponse.value 'False'
                self.userresponse.rootchange=True
            else:
                #The only True value here should be for "good parse, continue".
                self.userresponse.value=x
            self.l.destroy()
            # log.info("self.l destroyed")
        def enterroot():
            # log.info("Building extra root fields")
            ui.Label(self.responseframe,
                        text=_("root:"),
                        row=0,column=3,padx=(10,0),sticky='ew')
            roottext = ui.StringVar(self.responseframe, value=lx)
            self.roottextfield=ui.EntryField(self.responseframe,
                                                text=roottext,
                                                row=0,column=4,sticky='ew')
            ui.Button(self.responseframe,
                        text=_("OK"),
                        command=lambda x=roottext: do(x),
                        row=0,column=5,padx=(10,0),sticky='ew')
            self.roottextfield.bind('<Return>', lambda event,
                                                            x=roottext: do(x))
            # log.info("Extra root fields built")
            # log.info("Waiting (again)")
        def undosf():
            log.info("Running undosf")
            log.info(self.currentformnotice())
            if self.sense.psvalue() == self.nominalps: #unset value
                self.entry.plvalue(program['settings'].pluralname, value=False)
            elif self.sense.psvalue() == self.verbalps:
                self.entry.fieldvalue(program['settings'].imperativename,
                                            self.analang, value=False) #unset value
            program['db'].write()
            log.info(self.currentformnotice())
            do(False)
        level, lx, lc, sf, ps, afxs = args
        if self.exitFlag.istrue():
            return
        w=ui.Window(self,noexit=True)
        w.title(_("Confirm this combination of affixes?"))
        self.userresponse.value=False
        self.userresponse.rootchange=False
        # gloss=self.getgloss()
        # text=_("Parse looks good ({}):").format(self.parser.levels()[level])
        # text+=("\n{} {}"
        #         "\n{} {}"
        #         "\n{} {}: {} ({})"
        #         ).format(#self.parser.levels()[level],
        #                 lc,afxs[0],sf,afxs[1],
        #                 ps,_("root"),lx,gloss,
        #                 )
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
        self.l=ui.Label(self.lcframe,
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
                    ipadx=10,
                    row=0,column=0,sticky='nsew')
        ui.Button(self.responseframe,
                    text=_("No!"),
                    command=lambda x=False: do(x),
                    ipadx=10,
                    row=0,column=1,sticky='nsew')
        self.correctframe=ui.Frame(self.responseframe,
                                    row=0,column=2,
                                    sticky='ew',padx=(10,0))
        ui.Button(self.correctframe,
                    text=_("wrong root!"),
                    command=enterroot,
                    row=0,column=0,sticky='ew')
        ui.Button(self.correctframe,
                    text=_("wrong {}!".format(self.secondformfield[self.sense.psvalue()])),
                    command=undosf,
                    row=1,column=0,sticky='ew')
        self.noticeframe=ui.Frame(w.frame,row=3,column=0)
        t=_("This parse looks good ({})\n").format(self.parser.levels()[level])
        ui.Label(self.noticeframe,text=t+self.currentformnotice(),
                    font='small',justify='l',
                    row=0,column=0)
        if self.iswaiting():
            # log.info("Window almost built; unpausing")
            self.waitpause()
        # log.info("exit flag for w({}):{}; self({}):{}"
        #         "".format(w,w.exitFlag,self,self.exitFlag))
        # log.info("Window built; waiting")
        w.wait_window(self.l) #canary on label, not window
        if w.exitFlag.istrue():
            # log.info("Exited parse! (self.userresponse.value:{})"
            #         "".format(self.userresponse.value))
            self.waitdone()
            self.exited=True
        else:
            # log.info("Didn't exit parse! (self.userresponse.value:{})"
            #         "".format(self.userresponse.value))
            # w.on_quit()
            w.destroy()
            if self.iswaiting():
                self.waitunpause()
            if self.userresponse.rootchange:
                self.trythreeforms() #kick this back up a level
            else:
                # log.info("User responded {}".format(self.userresponse.value))
                return self.userresponse.value
    def selectsffromlist(self,l):
        def formattuple(l):
            pfx,sfx=l[-1]
            root=l[2]
            return '-'.join([i for i in [pfx,root,sfx] if i])
            if pfx:
                pfx+='-'
            if sfx:
                sfx='-'+sfx
            if pfx or sfx:
                rootafxs=[root,'affixes:',pfx,sfx]
            else:
                rootafxs=[root]
            return "{} ({} root: {})".format(*l[:2],' '.join(rootafxs))
        def neither():
            # These count askparsed; evaluated and moving on
            self.parsecatalog.addneither(self.parser.sense.id)
            #don't leave 'neither' with ps indication
            self.parser.sense.rmpsnode()
            # self.parser.rmpssubclassnode() #leave this for posterity?
            t.destroy()
        # log.info("Selecting from option list: {}".format(l))
        if self.exitFlag.istrue():
            return
        if self.iswaiting():
            self.waitpause()
        ln=[(i,formattuple(i)) for i in l if i[1] == self.nominalps
                        if len(i[-1]) == 2] #each must have (only) pfx and sfx
        ln+=[('ON',_("Other {}").format(self.secondformfield[self.nominalps]))]
        # log.info("noun option list: {}".format(ln))
        lv=[(i,formattuple(i)) for i in l if i[1] == self.verbalps
                         if len(i[-1]) == 2] #each must have (only) pfx and sfx
        lv+=[('OV',_("Other {}").format(self.secondformfield[self.verbalps]))]
        # log.info("verb option list: {}".format(lv))
        w=ui.Window(self)
        w.title(_("Select second form"))
        t=ui.Label(w.frame,
                    text=_("What is the {} or {} of \n‘{}’ ({})?"
                        "").format(
                        self.secondformfield[self.nominalps],
                        self.secondformfield[self.verbalps],
                        self.parser.entry.lcvalue(),
                        self.getgloss()
                                ),
                    font='title',
                    row=0,column=0,columnspan=2)
        t.wrap()
        if ln:
            noun=ui.Frame(w.frame, row=1, column=0, sticky='n')
            ImageFrame(noun,self.sense,ftype='pl',row=0,column=0, sticky='')
            ui.Label(noun,
                    text=_("Select {} form").format(
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
                    text=_("Select {} form").format(
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
            r=self.asksegments(ps=ps)
            if r in [None,1] or self.exited: #i.e., returned OK or not this ps
                break
    def asksegmentsotherps(self):
        pss=[i for i in [self.nominalps, self.verbalps]
                    if i != self.parser.sense.psvalue()]
        for ps in pss:
            self.asksegments(ps=ps)
    def updateparseUI(self):
        self.cparsetext.set(self.currentformsforuser(entry=self.entry))
    def currentformsforuser(self,entry=None):
        if entry is not None:
            self.parser.entry=entry
            self.parser.sense=entry.sense
        lx,lc,pl,imp = self.parser.texts()
        if lx:
            return _("{root}: {} ({ps}), {sfname}: {}"
                ).format(lx,''.join([i for i in [pl,imp] if i]),
                        root=_("Root"),
                        ps=self.parser.sense.psvalue(),
                        sfname=self.secondformfield[self.nominalps] if pl
                        else self.secondformfield[self.verbalps]
                        )
        if lc and (pl or imp):
            return _("Citation: {}, {sfname}: {}"
                ).format(lc,''.join([i for i in [pl,imp] if i]),
                        # root=_("root"),
                        # ps=self.parser.sense.psvalue(),
                        sfname=self.secondformfield[self.nominalps] if pl
                        else self.secondformfield[self.verbalps]
                        )
        if lc:
            return _(f"Citation: {lc}")
        else:
            return ""
    def currentformnotice(self):
        return _("currently: ")+("{} ({ps} {root}), {}, {} ({pl}), {} ({imp})"
                ).format(*self.parser.texts(),
                        root=_("root"),
                        ps=self.parser.sense.psvalue(),
                        pl=self.secondformfield[self.nominalps],
                        imp=self.secondformfield[self.verbalps]
                        )
    def asksegments(self,ps=None):
        def do(event=None):
            self.parser.sense.psvalue(ps)
            if ps == self.nominalps:
                # tag='pl'
                fn=self.parser.entry.plvalue
            elif ps == self.verbalps:
                # tag='imp'
                fn=self.parser.entry.fieldvalue
            # lift.prettyprint(self.parser.entry.imp)
            # lift.prettyprint(self.parser.entry.pl)
            # log.info("value: {}".format(segments.get()))
            # lift.prettyprint(self.parser.entry.imp)
            # lift.prettyprint(self.parser.entry.pl)
            fn(self.secondformfield[ps],segments.get())
            # log.info("v: {}".format(fn(self.secondformfield[ps],self.analang)))
            # self.parser.nodetextvalue(tag,segments.get())
            b.destroy()
        def next(event=None):
            segments.set("")
            b.destroy()
            # w.on_quit()
        if self.exitFlag.istrue():
            return
        if not ps:
            return asksegmentsnops()
        log.info("asking for second form segments for ‘{}’ ps: {} ({}; {})"
                "".format(self.parser.entry.lcvalue(),
                            ps,self.parser.sense.id,
                            self.parsecatalog.parsen()))
        sfname=self.secondformfield[ps]
        if self.iswaiting():
            self.waitpause()
        w=ui.Window(self)
        w.title(_("Type second form"))
        l=ui.Label(w.frame,
                text=_("What {} form goes with ‘{}’ ({})?"
                    "").format(sfname,
                            self.parser.entry.lcvalue(),
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
        segments.set(self.parser.entry.lcvalue())
        e=ui.EntryField(w.frame,text=segments,
                        row=2,column=0)
        b=ui.Button(w.frame,text=_("OK"),cmd=do,
                        row=3,column=0, sticky='e')
        ui.Button(w.frame,text=_("Not a {}").format(ps),cmd=next,
                        row=3,column=1, sticky='e')
        ui.Label(w.frame,text=self.currentformnotice(),
                    font='small',justify='l',
                    row=4,column=0,columnspan=2)
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
    def done(self):
        lx, lc, pl, imp = self.parser.texts()
        ps=self.parser.sense.psvalue()
        log.info("Currently working with lx: {}, lc: {}, pl: {}, imp: {}, ps: "
                "{}".format(lx,lc,pl,imp,ps))
        log.info("Done: {}".format(bool(lx)&bool(lc)&(
                                    bool(pl)|bool(imp))&
                                    bool(ps)))
        return bool(lx)&bool(lc)&(bool(pl)|bool(imp))&bool(ps)
    def tryoneform(self):
        log.info("Asking for second form selected (parse w/one form)")
        r=self.parser.oneform()
        # log.info("r: {}".format(r))
        # log.info("psvalue: {}".format(self.parser.sense.psvalue()))
        if r:
            self.selectsffromlist(r)
            log.info("Done selecting from {}".format(r))
        #User responding "neither noun nor verb" gives no psvalue, so stop here.
        if not self.exited and not self.done() and self.parser.sense.psvalue():
            self.tryaskform()
    def trytwoforms(self):
        log.info("Trying for parse with two forms")
        r=self.parser.twoforms()
        # return level, lx, lc, sf, self.ps, afxs #from self.parser.twoforms
        if not r:
            log.info("Auto parsed {} with two forms".format(self.sense.id))
            return
        elif isinstance(r,tuple) and self.userconfirmation(*r):
            self.parser.doparsetolx(r[1],*r[4:]) #pass root, too
        elif not isinstance(r,tuple) and r > 1:
            log.info("I need to figure out what to do with suppletive forms!")
            return
        if (not self.exited and
            not self.done() and
            # rootchange kicks back, so just finish here on rootchange:
            not self.userresponse.rootchange):
            self.tryoneform()
    def trythreeforms(self):
        log.info("Trying for parse with three forms")
        r=self.parser.threeforms()
        #This gives r= tuple to check, or 1 if skipped. no UI = no self.exit set
        # log.info("reponse: {} ({})".format(r,type(r)))
        if not r:
            log.info("Auto parsed {} with three forms (returned {})"
                    "".format(self.sense.id,r))
            return
        elif isinstance(r,tuple) and self.userconfirmation(*r):
                # return level, lx, lc, sf, self.ps, afxs #from self.parser.threeforms
            log.info("Confirmed parsing of ‘{}’ root from ‘{}’ and ‘{}’ as {}"
                        "".format(*r[1:5]))
            log.info("adding {} affix set {}".format(*r[4:]))
            self.parser.addaffixset(*r[4:])#self.ps,afxs)
            self.parser.sense.pssubclassvalue(r[-1])
            return
        if (not self.exited and
            not self.done() and
            # rootchange kicks back, so just finish here on rootchange:
            not self.userresponse.rootchange):
            self.trytwoforms()
    def fixroot(self,root):
        log.info("Fixing Root {} > {}".format(
                            self.parser.entry.lxvalue(),
                            root))
        self.parser.entry.lxvalue(root) #setting
        self.updateparseUI()
    def parse_foreground(self,**kwargs):
        self.withdraw()
        self.updatereturnbind()
        self.parse(**kwargs)
        self.updateparseUI()
        if self.iswaiting():
            self.waitdone()
        if self.winfo_exists():
            self.deiconify()
            self.updatereturnbind()
    def parse(self,**kwargs):
        # These functions return nothing when the parse goes through, 1 when
        # not done. If the user exits, self.exited is set
        self.exited=False
        r=True #i.e., do the next fn
        if not kwargs:
            kwargs={
                'sense':self.sense
                }
        self.parser.parseentry(**kwargs) #sets entry, sense, and sense.id for parser
        log.info("lx: {}, lc: {}, pl: {}, imp: {}".format(*self.parser.texts()))
        if min(self.parser.auto, self.parser.ask) <= 4:# and not badps:
            r=self.trythreeforms() #other functions will be triggered from here.
        else:
            log.info("Not parsing; auto: {}, ask: {}".format(self.parser.auto,
                                                            self.parser.ask))
        # badps is OK here, but don't do twoforms if threeforms worked
            # log.info("trytwoforms returned {}".format(r))
            # log.info("tryoneform returned {}".format(r))
            # log.info("Asking for second form typed")
    def tryaskform(self):
        try:
            r=self.asksegments(ps=self.parser.sense.psvalue())
            if r == 1:
                r=self.asksegmentsotherps()
                assert r != 1
        except Exception as e:
            log.info("Exeption: {}".format(e))
            self.asksegmentsnops()
        if not self.exited:
            self.submitparse()
    def submitparse(self):
        try:
            self.parsecatalog.addparsed(self.sense.id)
        except: #upgrade to this
            self.parsecatalog.addparsed(kwargs['entry'].sense.id)
        self.maybewrite()
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
    def sensestoparse(self,senses=None,all=False,n=-1): #n/limit=-1#1000
        s=self.initsensetodo()# This returns and resets
        if s:
            return s
        if not senses:
            senses=program['db'].senses[:n]
        if all:
            return senses #if provided, assume all
        else:
            try:
                return set(senses)-set(self.parsecatalog.parsed)
            except AttributeError:
                return set(senses)
    def getparses(self,**kwargs):
        log.info("parses already tried: {}".format(self.parsecatalog.parsen()))
        self.wait(_("Parsing (ask: {} auto: {})").format(self.parser.ask,
                                                        self.parser.auto
                                                    ))
        senses=self.sensestoparse(**kwargs)
        todo=len(senses)
        for n,self.sense in enumerate(senses):
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
            self.wait(_("Loading Affixes"))
            # for i in collector.do():
            for i in collector.getfromlift():
                # log.info("Progress: {}".format(i))
                self.waitprogress(i)
            self.parsecatalog.report()
            self.waitdone()
    def showwhenready(self):
        try:
            assert self.status.winfo_exists()
            log.info("showing")
            self.deiconify()
        except:
            log.info("not showing")
            self.after(1,self.showwhenready)
    def storethisword(self):
        try:
            v=self.var.get()
            if v:
                self.entry.fields[self.ftype].textvaluebylang(self.analang,v)
                if not self.done():
                    self.parse_foreground(entry=self.entry)
            self.maybewrite() #only if above is successful
            self.updateparseUI()
            log.info(f"Storing word: {self.sense.id} ({self.analang}:{v})")
        except AttributeError as e:
            log.info("Not storing word (Parse): {}".format(e))
    def waitforOKsecondfields(self):
        while not program['settings'].secondformfieldsOK():
            after(10*100,callback=self.waitforOKsecondfields) # wait a second
    def __init__(self, parent): #frame, filename=None
        self.byslice=False
        self.initsensetodo()
        Segments.__init__(self,parent)
        self.parent=parent
        self.secondformfield=program['settings'].secondformfield
        self.nominalps=program['settings'].nominalps
        self.verbalps=program['settings'].verbalps
        self.loadfromlift=True
        # program['settings'].makesecondformfieldsOK() #do elsewhere
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
        # self.ftype=program['params'].ftype('lx') #I think once we parse, we want this
        # self.nodetag='citation'
        self.dodone=True #give me words with citation done
        self.checkeach=False #don't confirm each word (default)
        self.dodoneonly=True #don't give me other words
        self.userresponse=Object(rootchange=False,value=False)
        self.cparsetext=ui.StringVar() #store UI parse info here
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
class WordCollectnParse(Parse,WordCollection,TaskDressing):
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
    def __init__(self, parent):
        log.info("Initializing {}".format(self.tasktitle()))
        self.ftype=program['params'].ftype('lc') #always correct?
        # self.nodetag='citation'
        TaskDressing.__init__(self,parent)
        Parse.__init__(self,parent)
        WordCollection.__init__(self,parent)
        program['taskchooser'].withdraw()
        fn=self.getwords()#?
class WordCollectnParsewRecordings(Parse,WordCollectionwRecordings,TaskDressing):
    """This task collects words, from the SIL CAWL, or one by one.
    First in citation form, then pl or imperativewith Parse"""
    def taskicon(self):
        return program['theme'].photo['iconWordRec']
    def tooltip(self):
        return _("This task helps you collect and parse words by recording "
                "them, with an automatic draft.")
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
                'image':program['theme'].photo['WordRec'],
                'sticky':'ew',
                'tttext':tttext
                }
    def tasktitle(self):
        return _("Add and Parse Words with Audio") # for Citation Forms
    def __init__(self, parent):
        log.info("Initializing {}".format(self.tasktitle()))
        self.ftype=program['params'].ftype('lc') #always correct?
        # self.nodetag='citation'
        TaskDressing.__init__(self,parent)
        Parse.__init__(self,parent)
        WordCollectionwRecordings.__init__(self,parent)
        program['taskchooser'].withdraw()
        fn=self.getwords()#?
class WordsParse(Parse,WordCollection,TaskDressing):
    def taskicon(self):
        return program['theme'].photo['iconWord']
    def tooltip(self):
        return _("This task helps you parse words you collected earlier.")
    def tasktitle(self):
        return _("Parse Already Collected Words") # for Citation Forms
    def dobuttonkwargs(self):
        pass
    def __init__(self, parent):
        log.info("Initializing {}".format(self.tasktitle()))
        self.ftype=program['params'].ftype('lc') #always correct?
        # self.nodetag='citation'
        TaskDressing.__init__(self,parent)
        Parse.__init__(self,parent)
        WordCollection.__init__(self,parent)
        # if not program['settings'].secondformfieldsOK():
        #     ErrorNotice(_("To parse, you must first define which fields "
        #                     "should contain secondary forms"),
        #                     wait=True)
        #     self.shutdowntask()
        #     return
        self.dodone=True #give me words with citation done
        self.checkeach=True #confirm each word (not default)
        self.dodoneonly=True #don't give me other words
        self.userresponse=Object()
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
                    text=_("This is a check placeholder."),
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
            # log.info("First status frame, or no example yet ({}).".format(e))
            pass
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
        #order glosslangs first, then other options:
        self.langs=[self.analangftypecode()]+program['settings'].glosslangs+[
                                    l for l in program['db'].glosslangs
                                    if l not in program['settings'].glosslangs]
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
        nothing='______'
        for n,l in enumerate(self.langs):
            langname=program['settings'].languagenames[self.stripftypecode(l)]
            if l in self.forms:
                log.info("Working on {}".format(langname))
                if l == self.stripftypecode(l): #no change means gloss
                    tintro=_("Gloss in {}:").format(langname)
                    if l in program['settings'].glosslangs:
                        ltttext=_("current gloss language")
                    else:
                        ltttext=_("additional gloss language")
                        b=ui.Button(self.fds,text='X',
                                    cmd=lambda l=l:self.skiplang(l),
                                    column=0,row=n+1,sticky='e')
                        b.tt=ui.ToolTip(b, _("Skip {}").format(langname))
                else:
                    tintro=_("{}:").format(langname)
                    ltttext=_("analysis language")
                li=ui.Label(self.fds,text=tintro,column=1,row=n+1)
                li.tt=ui.ToolTip(li, ltttext)
                lineframe=ui.Frame(self.fds,column=2,row=n+1)
                if 'Language ' in langname:
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
                        text='<'+_("No {} frame info").format(
                                program['settings'].languagenames[l])+'>'
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
        self.parent.withdraw() #just in case it's visible
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
            self.w.title('{} {}'.format(context,lang))
        else:
            self.w.title(_("New {} Tone frame for {}: Name the Frame").format(
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
                                text=v,
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
            if tried > program['db'].nsenses*1.5: #give up looking randomly
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
            if tried> program['db'].nsenses*3.5:
                errortext=_("I've tried (randomly, then through each) {} "
                "times, and not found one "
                "of your {} senses with data in each of these languages: "
                "{}. \nAre you asking for gloss "
                "languages which actually have data in your database? \nOr, are "
                "you missing gloss fields (i.e., you have only 'definition' "
                "fields)?").format(tried,program['db'].nsenses,langs)
                log.error(errortext)
                return #errortext
        log.debug("Found entry {} with glosses {}".format(sense.id,f))
        return f
    def __init__(self,parent):
        ui.Window.__init__(self,parent)
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
class Tone(Senses):
    """This keeps stuff used for Tone checks."""
    def makeanalysis(self,**kwargs):
        """was, now iterable, for multiple reports at a time:"""
        if not hasattr(self,'analysis'):
            self.analysis=Analysis(**kwargs)
        else:
            self.analysis.setslice(**kwargs)
    def checkforsensestosort(self,cvt=None,ps=None,profile=None,check=None):
        """This method just asks if any sense in the given slice is unsorted.
        It stops when it finds the first one."""
        """use if sorting sense lists aren't needed"""
        """This is redundant with updatesortingstatus()"""
        if cvt is None:
            cvt=program['slices'].cvt()
        if ps is None:
            ps=program['slices'].ps()
        if profile is None:
            profile=program['slices'].profile()
        if check is None:
            check=program['slices'].check()
        senses=program['slices'].senses(ps=ps,profile=profile)
        vts=False
        for sense in senses:
            if sense.tonevaluebyframe(self,frame):
                vts=True
                break #This is just a True/False for the group, not lists
        program['status'].dictcheck(cvt=cvt,ps=ps,profile=profile,check=check)
        program['status'].tosort(vts,cvt=cvt,ps=ps,profile=profile,check=check)
    def settonevariablesiterable(self,cvt='T',ps=None,profile=None,check=None):
        """This is currently called in iteration, but doesn't refresh groups,
        so it probably isn't useful anymore."""
        self.checkforsensestosort(cvt=cvt,ps=ps,profile=profile,check=check)
    def settonevariables(self):
        """This is currently called before sorting. This is a waste, if you're
        not going to sort afterwards –unless you need the groups."""
        self.updatesortingstatus() #this gets groups, too
    def addframe(self,**kwargs):
        if 'window' in kwargs:
            kwargs['window'].destroy() #in any case; if fails, try again.
        self.withdraw()
        t=ToneFrameDrafter(self)
        if not t.exitFlag.istrue():
            self.wait_window(t)
    def aframe(self):
        self.runwindow.on_quit()
        self.addframe()
        self.addwindow.wait_window(self.addwindow)
        self.runcheck()
    def presortgroups(self):
        #simpler than calling and uncalling..…
        pass
    def updateformtoannotations(self,*args,**kwargs):
        #simpler than calling and uncalling..…
        pass
    def setitemgroup(self,item,check,group,**kwargs):
        """ftype should be set at the beginning of work and not changed often,
        so shouldn't need to be specified here
        """
        # """here kwargs should include framed, if you want this to update the
        # form information in the example"""
        ps=item.psvalue()
        # log.info("Setting tone sort group")
        # if not ftype:
        #     log.error("No field type!")
        #     return
        try:
            """Fine if check isn't there; will be caught with exception"""
            # providing both ftype and frame isn't necessary, but allows check
            # that they align:
            assert check in item.examples
            f=item.formattedform(self.analang,self.ftype,
                                program['toneframes'][ps][check])
            # log.info("Setting form to {}".format(f))
            item.examples[check].textvaluebylang(
                                    lang=self.analang,
                                    value=f)
            log.info("Setting tone sort group to ‘{}’".format(group))
            item.examples[check].tonevalue(group)
            for g in (set(self.glosslangs)& #selected
                        set(program['toneframes'][ps][check])& #defined
                        set(item.ftypes[self.ftype])): # form in lexicon
                for f in item.formattedgloss(g,
                                        program['toneframes'][ps][check])[:1]:
                    # log.info("Setting {} translation to {}".format(g,f))
                    item.examples[check].translationvalue(g,f)
            item.examples[check].lastAZTsort()
        except (KeyError,AssertionError) as e:
            # log.info(f"Adding a new example to store ‘{check}’ values ({e})")
            item.newexample(check,
                            program['toneframes'][ps][check],
                            self.analang,
                            self.glosslangs,
                            group)
        # log.info("Done setting tone sort group")
    def getsensesinUFgroup(self,group):
        return [
                i for i in program['db'].senses
                if i.uftonevalue() == group
                ]
    def getsensesingroup(self,check,group):
        return [
                i for i in program['db'].senses
                if i.tonevaluebyframe(check) == group
                ]
    def getitemgroup(self,item,check):
        """This works without ftype, as each frame only has one"""
        return item.tonevaluebyframe(check)
    def getUFgroupofsense(self,sense):
        return sense.uftonevalue()
    def name_new_glyphs(self):
        pass
    def __init__(self):
        pass
class Sort(object):
    """This class takes methods common to all sort checks, and gives sort
    checks a common identity."""
    def get_check(self):
        return program['params'].check()
    def get_ps(self):
        return program['slices'].ps()
    def get_profile(self):
        return program['slices'].profile()
    def get_ftype(self):
        return program['params'].ftype()
    def get_frame(self):
        if self.cvt != 'T': # not for segmental checks
            return 
        frames=program['toneframes'].get(self.ps)
        if frames and self.check in frames:
            return frames.get(self.check)
        else:
            text=_(f"Looking for tone check ‘{self.check}’, but not "
                    f"in {self.ps} frames: {frames}")
            ErrorNotice(text,wait=True)
    def getsensesincheckgroup(self,**kwargs):
        check=kwargs.get('check',program['params'].check())
        group=kwargs.get('group',program['status'].group())
        return self.getsensesingroup(check, group)
    def rmverification(self,sense,profile,check):
        self.modverification(sense,profile,check)
    def modverification(self,sense,profile,check,add=None):
        """
        'add' here should be a single compiled 'check=group' code
        These fns all take value kwarg, with a default lang generated there
        This and other methods should be making this:
        field type="CVCVC lc verification">
                <form lang="{xyz}-x-py">
                    <text>['V1=ə', …
        # This could all be moved to operate on sense.fields[key]...
        # Would require pushing down protections for string values, and probably
        # making a class for verification nodes
        """
        added=None
        assert not add or check in add
        # add=Nonelog.info("Modifying verification node {} (to add {})".format(
        #                                                             key,add))
        # if key in sense.fields:
        #     lift.prettyprint(sense.fields[key])
        values=sense.verificationtextvalue(profile,self.ftype) #always returns list
        # log.info(f"Found verificationtextvalue values {values}")
        if add and not values:
            # log.info("No values found; just adding {}".format(add))
            v=sense.verificationtextvalue(profile,self.ftype,value=[add])
            return #if more complex, continue
        for code in [i for i in values if check in '='.join(i.split('=')[:-1])]:
            #look for a code for the *whole* current check, replace or remove.
            if add:
                if add != code:
                    log.info(f"Switching {add} for {code} in {profile} {sense.id}")
                    values[values.index(code)]=add
                    added=add
                add=None #only once, not also below
            else:
                values.remove(code) #covered in the above
        if add: #i.e., still, after switching out current values for changes
            values.append(add)
            added=add
        v=sense.verificationtextvalue(profile,self.ftype,value=values)
    def updatestatuslift(self,verified=False,**kwargs):
        """This should be called only by update status, when there is an actual
        change in status to write to file."""
        check=kwargs.get('check',program['params'].check())
        group=kwargs.get('group',program['status'].group())
        profile=kwargs.get('profile',program['slices'].profile())
        ftype=kwargs.get('ftype',program['params'].ftype())
        # profile=program['slices'].profile()
        senses=self.getsensesincheckgroup()
        value=self.verificationcode(check=check,group=group)
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
        for sense in program['slices'].inslice(senses): #only for this ps-profile
            self.modverification(sense,profile,check,add)
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
            if profilevar.get() == '':
                log.debug("Give a name for this adhoc sort group!")
                return
            self.runwindow.on_quit()
            ids=[]
            for var in [x for x in vars if len(x.get()) >1]:
                # log.info("var {}: {}".format(vars.index(var),var.get()))
                ids.append(var.get())
            # log.info("ids: {}".format(ids))
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
        allpssenses=program['slices'].sensesbyps(ps)
        if len(allpssenses)>70:
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
        namefield = ui.EntryField(qframe,text=profilevar)
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
        for idn,sense in enumerate(allpssenses):
            log.debug("id: {}; index: {}; row: {}".format(sense.id,idn,row))
            # idn=allpssenses.index(sense)
            vars.append(ui.StringVar())
            adhocslices=program['slices'].adhoc()
            if (ps in adhocslices and profile in adhocslices[ps] and
                                        sense in adhocslices[ps][profile]):
                vars[idn].set(sense)
            else:
                vars[idn].set(0)
            forms=sense.formatted()
            log.debug("forms: {}".format(forms))
            ui.CheckButton(scroll.content, text = forms,
                                variable = vars[idn],
                                onvalue = id, offvalue = 0,
                                ).grid(row=row,column=0,sticky='ew')
            row+=1
        scroll.grid(row=3,column=0,sticky='ew')
        self.runwindow.waitdone()
        self.runwindow.wait_window(scroll)
    def removeitemfromgroup(self,item,**kwargs):
        #leave these in kwargs for use below:
        check=kwargs.get('check',program['params'].check())
        group=kwargs.get('group',program['status'].group())
        write=kwargs.pop('write',True) #avoid duplicate
        sorting=kwargs.get('sorting',True) #Default to verify button
        log.info(_("Removing sense {} from subcheck {}".format(item.id,group)))
        #This should only *mod* if already there
        self.setitemgroup(item,check,'',**kwargs)
        tgroups=self.getitemgroup(item,check)
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
        rm=self.verificationcode(check=check,group=group)
        profile=kwargs.get('profile',program['slices'].profile())
        item.rmverificationvalue(profile,self.ftype,rm)
        program['status'].last('sort',update=True)
        program['examples'].clear_cache(**kwargs) #anything should still be in kwargs
        if write:
            self.maybewrite()
        if sorting:
            program['status'].marksensetosort(item)
    def ncheck(self):
        r=program['status'].nextcheck(tosort=True)
        if r:
            program['settings'].setcheck(r)
        else:
            program['settings'].setcheck(toverify=True)
        #if neither, this should call nprofile
        try:
            self.runwindow.on_quit()
        except AttributeError:
            log.info("Looks like we wanted to kill a non-existent runwindow.")
        self.runcheck()
    def nprofile(self):
        r=program['status'].nextprofile(tosort=True)
        if r:
            program['settings'].setprofile(r)
        else:
            program['settings'].setprofile(toverify=True)
        #if neither, this should give up with a congrats and comment to pick another ps
        try:
            self.runwindow.on_quit()
        except AttributeError:
            log.info("Looks like we wanted to kill a non-existent runwindow.")
        self.runcheck()
    def nps(self):
        program['slices'].nextps()
        r=program['status'].nextprofile(tosort=True)
        if not r:
            program['status'].nextprofile(toverify=True)
        try:
            self.runwindow.on_quit()
        except AttributeError:
            log.info("Looks like we wanted to kill a non-existent runwindow.")
        self.runcheck()
    def runcheck(self):
        program['settings'].storesettingsfile()
        # t=(_('Run Check'))
        log.info("Running check...")
        cvt=program['params'].cvt()
        self.check=program['params'].check()
        self.profile=program['slices'].profile()
        if not self.profile:
            self.getprofile()
            self.profile=program['slices'].profile()
        """further specify check check in maybesort, where you can send the user
        on to the next setting"""
        if (self.check not in program['status'].checks() #tosort=True
                # and check not in program['status'].checks(toverify=True)
                # and check not in program['status'].checks(tojoin=True)
                ):
            exit=self.getcheck()
            if exit and not self.exitFlag.istrue():
                return #if the user didn't supply a check
        self.presortgroups()
        self.updatesortingstatus() # Not just tone anymore
        self.maybesort(firstrun=True)
    def confirmverificationgroup(self,sense,profile,check):
        """This does the one field storing a list of verified values
        for all checks"""
        """This results in NO group change where a group hasn't been confirmed!
        """
        log.info(_("Confirming that current group and verification code match "
                    "before making changes."))
        annogroup=self.getitemgroup(sense,check) #Segment or Tone
        vals=sense.verificationtextvalue(profile,self.ftype)
        curvalues=[i.split('=')[-1]  #last (value), if multiple
                    for i in sense.verificationtextvalue(profile,ftype)
                    if check in i]
        # Length is relevant here because V1 must match V1=V2, if present
        nvals=len(set(curvalues))
        if nvals == 1:
            curvalue=curvalues[0]
        elif nvals >1:
            log.error("Too many values for verification node; fix this!"
                        " ({}; {}; {})".format(curvalues,vals,sense.id))
            curvalue=None
        elif nvals == 0:
            log.error("No values for verification node! ({})"
                        "".format(vals))
            curvalue=None
        if curvalue == annogroup: #only update if starting w/ same value
            # log.info(f"Confirmed curent verification group ‘{curvalue}’ "
            #         f"matches annotation group ‘{curvalue}’")
            return True
        elif not curvalue:
            log.error("Problem updating verification to {}; current "
                        "value not there (should be {})"
                        "".format(group, annogroup))
        else: #not sure what to do here; maybe  throw bigger error?
            log.error("Problem updating verification to {}; current "
                        "value ({}) is there, but not the same as "
                        "current sort group ({})."
                        "".format(group, curvalue, annogroup))
    def marksortgroup(self,sense,group,**kwargs):
        # group=kwargs.get('group',program['status'].group())
        check=kwargs.get('check',program['params'].check())
        profile=kwargs.get('profile',program['slices'].profile())
        # ftype=kwargs.get('ftype',program['params'].ftype())
        nocheck=kwargs.get('nocheck',False)
        guid=None
        # log.info(f"marksortgroup ready to updateverification {kwargs.get('thread_name')}")
        if kwargs.get('updateverification'):
            add=self.verificationcode(check=check,group=group)
            # Checking and verifying that the current group and verification
            # values match may be excessive, as well as undesirable, without
            # any other way to fix discrepancies:
            noconfirmation=True #Should test w/wo this; time difference?
            # confirmverificationgroup checks if current annotation matches
            # current verification. So this needs to happen first:
            if noconfirmation or self.confirmverificationgroup(sense, profile,
                                                                check):
                self.modverification(sense,profile,check,add)
        else: #unless specifically doing otherwise, marking should unverify:
            self.rmverification(sense,profile,check)
        # log.info(f"marksortgroup ready to set {kwargs.get('thread_name')}")
        self.setitemgroup(sense,check,group)
        # log.info(f"marksortgroup ready to check set worked {kwargs.get('thread_name')}")
        if not nocheck:
            newgroup=self.getitemgroup(sense,check)
            if newgroup != group:
                log.error("Field addition failed! LIFT says {}, not {}.".format(
                                                    newgroup,group))
            # else:
            #     log.info("Field addition succeeded! LIFT says {}, which is {}."
            #                             "".format(newgroup,group))
        # log.info(f"marksortgroup ready to updateforms {kwargs.get('thread_name')}")
        if kwargs.get('updateforms'):
            if self.ftype != program['params'].ftype():
                ErrorNotice(f"{ftype=} differs from "
                            f"{program['params'].ftype()=}; this is a problem!",
                            wait=True)
            self.updateformtoannotations(sense,check)
        # log.info(f"marksortgroup ready to marksorted {kwargs.get('thread_name')}")
        if not kwargs.get('not_sorting'): #default is sorting
            #This unverifies without updateverification=True:
            self.marksorted(sense,group,kwargs.get('updateverification'))
        # log.info(f"marksortgroup ready to write {kwargs.get('thread_name')}")
        if kwargs.get('write'):
            self.maybewrite() #Not iterated over.
        # if kwargs.get('thread_name'):
        #     log.info(f"Finishing marksortgroup for {kwargs.get('thread_name')}")
        # log.info(f"marksortgroup ready to untrack {kwargs.get('thread_name')}")
        if kwargs.get('thread_name'):
            self.untrack_thread(kwargs.get('thread_name'))
        if not nocheck:
            return newgroup
    def marksorted(self,sense,group,verified=False):
        """These functions are only appropriate when sorting or unsorting senses.
        when moving stuff around between groups (in renaming groups), these don't 
        apply.
        """
        program['status'].marksensesorted(sense)
        program['status'].last('sort',update=True) #this will always be a change
        program['status'].tojoin(True)
        self.updatestatus(group=group,
                            verified=verified,
                            writestatus=True) # write just this once
    def resetsortbutton(self):
        # This attribute/fn is used to track whether something has been done
        # since the user last asked for a sort. We don't want the user in an
        # endless line of work (especially if the task at hand is to do a number
        # of tasks in one profile), but on the other hand, if the selected
        # profile is already done when the sort button is pressed, assume the
        # user wants the next profile.
        self.did={'sort':False,
                    'verify': False,
                    'join': False,
                    'macropresort': False,
                    'macrosorttoglyphs': False,
                    'verifyglyphs': False,
                    'joinglyphs': False,
                }
    def redo_join(self):
        w=self.getgroup(purpose='join')
        self.wait_window(w)
        self.group=program['status'].group()
        program['status'].undistinguish_any_with(g=self.group) #should be correct at this point
        self.maybesort(firstrun=True)
    def redo_joinglyphs(self,glyph=False):
        if not glyph:
            self.wait_window(self.getglyph(purpose='join'))
        self.group=program['alphabet'].glyph(glyph)
        program['alphabet'].undistinguish_any_with(g=self.group) #should be correct at this point
        self.maybesort(firstrun=True)
    def maybesort(self,firstrun=False):
        """This should look for one group to verify at a time, with sorting
        in between, then join and repeat"""
        def tosortupdate():
            log.info("maybesort tosortbool:{}; tosort:{}; sorted (first 5):{}"
                    "".format(
                                self.tosort(),
                                self.itemstosort(),
                                self.itemssorted()[:5]
                                ))
        def exitstatuses():
            try:
                log.info("Self exit status: {}".format(self.exitFlag.istrue()))
                log.info("Parent exit status: {}".format(self.parent.exitFlag.istrue()))
                log.info("Parent return status: {}".format(self.returned))
                log.info("Runwindow exit status: {}".format(self.runwindow.exitFlag.istrue()))
                log.info("Taskchooser exit status: {}".format(program['taskchooser'].exitFlag.istrue()))
            except Exception as e:
                log.info("Exception: {}".format(e))
        def warnorcontinue(return_value): #mostly for testing
            if self.exitFlag.istrue():
                log.info("the task is exited; done with maybesort")
                pass #just return, below, if the task is exited
            elif return_value:
                log.info("runwindow finished; restarting maybesort")
                self.after(10,self.maybesort) #if neither exited, continue
            else:
                log.info("the runwindow didn't finish; Not done with maybesort")
                self.notdonewarning() #warn if runwindow exited, but not task
            return return_value #pass along
        if firstrun:
            self.resetsortbutton()
        log.info(f"Starting maybesort with {[k for k,v in self.did.items() if v]}")
        if self.exitFlag.istrue(): #if the task has been shut down, stop
            return
        program['settings'].reloadstatusdata() # culled here
        if self.itemstosort() is False:
            self.updatesortingstatus() # Not just tone anymore
        cvt=program['params'].cvt()
        self.check=self.get_check()
        self.ps=self.get_ps()
        self.profile=self.get_profile()
        self.ftype=self.get_ftype()
        log.info("Maybe Sort")
        if self.checktosort(): # w/o parameters, tests current check
            log.info("Running Sort")
            if warnorcontinue(self.sort()):
                self.did['sort']=True
            return
        log.info("Maybe Verify")
        groupstoverify=self.groups(toverify=True)
        if groupstoverify:
            log.info("Running Verify")
            log.info("Going to verify the first of these groups now: {}".format(
                                    self.groups(toverify=True)))
            if program['status'].group() not in groupstoverify:
                program['status'].group(groupstoverify[0]) #just pick the first now
            if warnorcontinue(self.verify()):
                self.did['verify']=True
            return
        log.info("Maybe Join")
        self.did['join']=False #runs multiple times, so clear here
        if self.to_distinguish():
            log.info("Running Join")
            warnorcontinue(self.join()) #1 here is now done; did.join intenally
            return
        """Up to this point, we sort into and out of (via verify) groups tracked
        by lift form annotations, and track groups marked as verified in lift
        profile-ftype verification fields (with 'check=group' values in a list).
        So far, we have just established which words belong in which groups!
            No forms are updated yet
            New groups (with default integer names) still have them
            annotation fields just track which words are in which group.
            verification fields track group verification (and membership)
            NONE of these group names mean ANYTHING yet —some derive from
                their original transcription, but that is coincidental.
        The next section will sort these group names in and out of alphabet
        fields, as the user tells us which groups should be represented by the
        same letter. After which all these fields will be updated.
        """
        log.info(f"Maybe Macrosort (with {[k for k,v in self.did.items() if v]})")
        if items := program['alphabet'].renew_items_tomacrosort():
            if not any({v for k,v in self.did.items() if 'glyphs' in k}):
                """only presort if arriving here before any other glyph
                operation this run:
                run with presort after an aborted sort run (redundant, but OK)
                run with no presort until after verify
                run with no presort until after join>verify
                this variable is updated/cleared on each bigbutton press, and
                on each automatic continue to a new profile or check.
                """
                for item in list(items):
                    program['alphabet'].presort_item(item) #only if no conflict
            # log.info(f"{program['alphabet'].itemstosort()=}")
            log.info("Running Macrosort")
            if warnorcontinue(self.sort(macrosort=True)):
                self.did['macrosorttoglyphs']=True
            return
        log.info("Maybe Verifyglyphs")
        glyphstoverify=program['alphabet'].glyphstoverify()
        if glyphstoverify:
            log.info(f"Going to verify these glyphs now: {glyphstoverify}")
            if program['alphabet'].glyph() not in glyphstoverify:
                program['alphabet'].glyph(list(glyphstoverify)[0])
            log.info("Running Verifyglyphs")
            if warnorcontinue(self.verify(macrosort=True)):
                self.did['verifyglyphs']=True
            log.info(f"Finished Verifyglyphs with {self.did=}")
            return
        log.info("Maybe Joinglyphs")
        self.did['joinglyphs']=False #runs multiple times, so clear here
        program['alphabet'].predistinguish(self.to_distinguish(macrosort=True))
        if self.to_distinguish(macrosort=True):
            log.info("Running Joinglyphs")
            warnorcontinue(self.join(macrosort=True))
            return
        # After all macrogroups are sorted out correctly, make all named:
        """These last three sections sort the previously verified sort groups
        in and out of alphabet dictionaries, so we now know:
            which words belong in which ps-profile-ftype-check group
            which ps-profile-ftype-check groups belong in which glyphs
        With this in hand, we now need to
            make sure that all glyphs have real names
            update lift form annotations to the appropriate glyph value
            update profile-ftype verifications to the appropriate glyph value
        THEN
            We can safely update forms to match their annotations.
        """
        """The first time user has been asked what glyph to use for a group;
        it will allow limited switching of group names, e.g., if 1 should be
        <b>, which already exists: b>2,1>b,2>? Do other changes later."""
        if self.default_glyphs():
            if warnorcontinue(self.name_new_glyphs()): #iterative: all int(); forced continue or quit.
                return
        """all int() groups and macrogroups are gone at this point!"""
        self.update_annotations_to_glyphs() #Iterates over all glyphs
        # The above aligns all annotations and verifications
        # the below updates forms IF annotations agree
        self.updateformsallchecks() #whole db annotations>forms
        """The following is to iterate to the next work to do. So we want
        everything for a check to be complete to be done by now.
        A user may want to change the name of a group; if so, they should stop
        the sort process, and go name the macrogroup.
        """
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
        done=_(f"All ‘{self.profile}’ groups in the ‘{self.check}’ "
                f"{self.checktypename[cvt]} are verified and distinct!")
                #only on first two ifs:
        if fn:
            done+='\n'+_("Moving on to the next {}!".format(next))
        ErrorNotice(text=done,title=_("Done!"),wait=True,parent=self)
        self.status.maybeboard()
        if fn:
            fn() #only on first two ifs, calls runcheck w/resetsortbutton
    def present_sense(self,sense):
        log.info(f"presenting to sort {sense.id}")
        frame=self.get_frame()
        text=sense.formatted(self.analang, self.glosslangs, self.ftype, frame)
        self.buttonframe.sortitem=ui.Frame(self.runwindow.frame, column=1, row=1, sticky='nw',
                            border=True)
        l=ui.Label(self.buttonframe.sortitem,
                                text=text,font='readbig', sticky='w',
                                # pady=scaledpady
                                )
        l['image']=scaleimageifthere(sense)
        l['compound']='left'
        l.wrap()
        return self.buttonframe.sortitem
    def present_group(self,item):
        log.info(f"presenting group {item}")
        kwargs=program['alphabet'].parse_verificationcode(item)
        self.buttonframe.sortitem=ui.Frame(self.runwindow.frame, border=True,
                                            column=1, row=1, sticky='nw')
        align_w_ggbfs=ui.Label(self.buttonframe.sortitem,text='',
                                width=5,sticky='')
        tosort_frame=SortGroupButtonFrame(self.buttonframe.sortitem,
                                        self, 
                                        show_check=True,
                                        label=True,
                                        sticky='', **kwargs
                                        )
        if tosort_frame.hasexample:
            return self.buttonframe.sortitem
        else:
            log.info(f"No example for {item}; not sorting.")
            program['alphabet'].mark_item_macrosorted(item) #don't keep sorting
            tosort_frame.destroy()
    def current_tosort(self,macrosort=False):
        """These are all ordered lists (either by order of listbuilding, or by
        sorted(). Items not on the original list get tacked onto the end, still
        in order. This allows the user to see a consistently rising progress
        number, even if the to do number rises as well.)"""
        if macrosort:
            tosort=program['alphabet'].itemstosort()
        else:
            tosort=program['status'].sensestosort()
        return self.first_sort+[i for i in tosort if i not in self.first_sort]
    def presenttosort(self,item,macrosort=False):
        # log.info(f"presenting to sort {item}")
        #Keep the same total throughout a given sort:
        tosort=self.current_tosort(macrosort=macrosort)
        progress=(str(tosort.index(item)+1)+'/'+str(len(tosort)))
        """After the first entry, sort by groups."""
        if self.runwindow.exitFlag.istrue():
            return #1,1
        ui.Label(self.groupsFrame, text=progress, font='report', anchor='e',
                    column=1, row=0, sticky='e')
        if macrosort:
            self.sortitem=self.present_group(item)
        else:
            self.sortitem=self.present_sense(item)
        self.runwindow.waitdone()
        log.info(f"Going to wait for {self.sortitem}")
        if not self.sortitem:
            log.info(f"{self.sortitem=} empty; returning")
            return
        try:
            self.buttonframe.set_canary(self.sortitem)
            self.runwindow.deiconify() # not until here
        except Exception as e:
            log.error(f"topresent Exception: {e}")
        self.runwindow.update_idletasks()
        self.runwindow.wait_window(window=self.sortitem)
        if not self.runwindow.exitFlag.istrue():
            return item
    def pageicon(self,macrosort=False):
        if not macrosort:
            r = self.check
            if 1 < self.profile.count(self.cvt) == r.count(self.cvt):
                r = self.cvt+'=' #use this any time all S is in check.
            if r in self.frame.theme.photo: # Remove once all supported
                return r
        return self.cvt #fail safe for the time being
    def add_int_group(self,macrosort=False):
        log.info("Adding a new group!")
        if macrosort:
            groups=program['alphabet'].glyphs()
        else:
            groups=program['status'].groups(wsorted=True)
        values=[int(i) for i in groups if i.isdigit()]+[0] #in case none
        newgroup=max(values)+1
        groups.append(str(newgroup))
        if not macrosort: #for macrosort, marksortgroup does this
            program['status'].groups(groups,wsorted=True)
            program['status'].store()
        log.info(f"Groups (appended): {groups}")
        return str(newgroup)
    def sortselected(self, item, macrosort=False):
        selected=self.buttonframe.get_selected()
        log.info("selected groups: {}".format(selected))
        if len(selected)>1:
            log.error("More than one group selected: {}".format(selected))
            return 2
        self.buttonframe.reset_selected()
        if not selected:
            log.debug('No group selected: {}'.format(selected))
            return 1 # this should only happen on Exit
        category=selected[0]
        if category in ["NONEOFTHEABOVE",'ok']:
            """If there are no groups yet, or if the user asks for
            another group, make a new group."""
            category=self.add_int_group(macrosort=macrosort)
            """Add button later, after marking sort group"""
        else:
            if category == 'skip':
                category='NA'
        if macrosort:
            program['alphabet'].mark_item_glyph(item, category)
        else:
            self.marksortgroup(item, category, nocheck=True) # that marking worked
        if category not in list(self.buttonframe.groupvars)+['NA']:
            self.buttonframe.addgroupbutton(category)
        self.maybewrite()
    def sort(self,macrosort=False):
        """This window/frame/function shows one item at a time, 
        for the user to select its category based on buttons defined below.
            sort groups: senses (with pic?) sorted into sort groups
                one ps and profile at a time (of course) 
            macrosort: ps-profile-check-ftype sort groups sorted into glyph groups (in a SGBF)
                across ps and profile
        In the event that the item isn't like any available category, a new one is
        formed, and added to the list of comparatives (which is autogenerated,
        to update whenever a category is added or taken out). Whenever a category is
        selected, the item being iterated through is marked as the same category,
        and that category is marked as unverified.
        As a sort function, items are unlabelled for content, reflecting either
        initial transcription (for segments) or an integer
            --we just need a unique name, in any case.
        Items can be sorted into established glyph characters, which have meaningful names.
        we cannot have two groups from the same sort go into the
        same alphabet letter; this would essentially join them.
        This could lead a user into an endless cycle, if they try to put
        both groups in the same macrogroup.
        Because of this, we should include a sane option to return
        to self.join(), and maybe a note? If the same pair of sorts happens a
        couple times in a row?
        This function should exit 1 on completion, otherwise None
        """
        log.info(f'Running sort: ({macrosort=})')
        """Titles"""
        if self.cvt == 'T':
            context=_("tone melody")
            descripttext=_("in ‘{}’ frame").format(self.check)
        else:
            context=program['params'].cvcheckname(self.check)
            descripttext=_("by {}").format(self.check)
        if macrosort:
            current_list_fn=program['alphabet'].itemstosort
            self.first_sort=list(current_list_fn()) #current list
            groups=program['alphabet'].glyphs()
            log.info(f"{program['alphabet'].glyph_members()=}")
            log.info(f"{self.exitFlag.istrue()=}")
            buttonclass=SortGlyphGroupButtonFrame
            img_mod='glyphs'
            instr_mod=''
        else:
            current_list_fn=self.itemstosort
            self.first_sort=list(current_list_fn()) #current list
            groups=[i for i in self.groups(wsorted=True) if i != 'NA']
            buttonclass=SortGroupButtonFrame
            img_mod=''
            instr_mod=_(f" (by {context})")
        instructions=_(f"...belongs in which group{instr_mod}?")
        log.info(f"Going to sort these items: {self.first_sort}")
        log.info("Into these groups: {}".format(groups))
        if not self.first_sort or self.exitFlag.istrue():
            return 1
        log.info(f"Getting Runwindow")
        self.getrunwindow() #after we know this will do something
        ui.Label(self.runwindow.frame, image=f'sort{img_mod}', 
                row=0, column=0, rowspan=3, sticky='new', anchor='center')
        ui.Label(self.runwindow.frame,
                image=self.pageicon(macrosort=macrosort),
                image_pixels=270, #250=65%;270=70%
                row=3,column=0,rowspan=3,sticky='nw') 
        self.runwindow.frame.rowconfigure(1, weight = 0) #word to sort
        self.runwindow.frame.rowconfigure(2, weight = 1) #prompt and groups
        self.runwindow.frame.columnconfigure(0, weight = 0) #icons
        self.runwindow.frame.columnconfigure(1, weight = 1) #words
        self.groupsFrame=ui.Frame(self.runwindow.frame, column=1, row=2,
                            rowspan=2, pady=0, sticky='new')
        ui.Label(self.groupsFrame, text=instructions, font='instructions',
                anchor='c', sticky='sew')
        self.buttonframe=SortButtonFrame(self.groupsFrame, self, groups, 
                                        macrosort=macrosort,
                                        row=1, sticky='new', columnspan=2)
        # log.info(f"Sort SBF done {macrosort=}")
        """Stuff that changes by lexical entry
        The second frame, for the other two buttons, which also scroll"""
        while current_list_fn():
            if self.runwindow.exitFlag.istrue():
                return
            item=self.presenttosort(current_list_fn()[0], macrosort=macrosort)
            # log.info("presenttosort done")
            if not self.runwindow.exitFlag.istrue() and item is not None:
                self.sortselected(item, macrosort=macrosort)
                self.buttonframe.updatecounts()
        if macrosort: #generalize
            program['alphabet'].save_settings()
            program['settings'].storesettingsfile('alphabet')
        self.runwindow.on_quit()
        return 1
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
        program['status'].verified(done)
        self.runcheck()
    def verifyselected(self, macrosort=False):
        selected=self.buttonframe.get_selected()
        log.info(f"verifyselected removing {selected}")
        if macrosort:
            for item in selected:
                program['alphabet'].remove_item_from_glyph(item, self.group)
        else:
            raise "This doesn't belong here yet!"# wrong: this should unsort!
            self.marksortgroup(item, category, nocheck=True) # that marking
        self.maybewrite()
    def verify(self,menu=False,macrosort=False):
        def updatestatus(verified=False):
            if macrosort:
                log.info(f"Updating ‘{group}’ status as {verified=}")
                if verified:
                    program['alphabet'].mark_glyph_done(group,cvt=self.cvt)
                else:
                    program['alphabet'].mark_glyph_not_done(group)
                log.info(f"{program['alphabet'].glyphstoverify()=}")
                program['alphabet'].save_settings()
            else:
                log.info("Updating status with {}, {}, {}".format(check,group,verified))
                program['status'].last('verify',update=True)
                self.updatestatus(verified=verified,writestatus=True)
            self.maybewrite()
        log.info(f"Running verify! {macrosort=}")
        """verify group of items sorted into a glyph."""
        """Show items each in a row, users mark those that are different,
        and we remove that group designation from the item (so it
        will show up on the next sorting).
        macrosort: verifying each sort group belongs in glyph
        sort groups: verifying each sense belongs in sort group 
        After all entries have been verified as "the same",
        click a button at the bottom of the screen for "verify", or "these are
        all the same", or some such. register with addresults (or elsewhere?).
        """
        #This function should exit 0 on a window close, 1 on all ok.
        title=_(f"Verify {program['settings'].languagenames[self.analang]}")
        if macrosort:
            item_name=_("Letter")
            img_mod='glyphs'
            groups=list(program['alphabet'].glyphstoverify()) #needed for progress
            self.group=group=program['alphabet'].glyph()
            self.currentsortitems=items=program['alphabet'].glyph_members()[group]
            if group.isdigit():
                title+=f" letter group"
            else:
                title+=f" letter ‘{group}’"
            checks={program['alphabet'].parse_verificationcode(i)['check']
                    for i in items}
            oktext=_("These all should use the same letter")
            if not group.isdigit():
                oktext+=f" (currently ‘{group}’)"
            instructions=_("Read this list aloud. Note where each "
                f"was sorted ({', '.join(sorted(checks))})."
                "\nClick on any with a different "
                f"{program['params'].cvtname()} sound in that place.")
        else:
            check=program['params'].check()
            checks=[]
            img_mod=''
            item_name=_(f"{check} Group")
            checkname=program['params'].cvcheckname()
            groups=self.groups(toverify=True) #needed for progress
            self.group=group=program['status'].group()
            self.currentsortitems=items=program['examples'].sensesinslicegroup(group,check)
            if group == 'NA':
                oktext=_(f'These all DO NOT have {checkname}')
                #These words seem to NOT have ‘{checkname}’. 
                instructions=_(f"Read this list aloud, and click on any that "
                            f"DOES have ‘{checkname}’.")
                title+=f" for ‘{check.replace('=','≠')}’ (NOT {program['params'].cvcheckname()})"
            else:
                oktext=_(f'These all have the same {checkname}')
                instructions=_("Read this list aloud. Click on any with a "
                            f"different {checkname} sound.")
                title+=f" for ‘{check}’ ({program['params'].cvcheckname()})"
            if group in program['status'].verified():
                log.info("‘{}’ already verified, continuing.".format(group))
                return 1
            if program['params'].cvt() == 'T' and 'examples' not in program:
                log.error(_("Not verifying tone examples which don't exist."))
                return 
        # The title for this page changes by group, below.
        if (n:=len(items)) == 1:
            log.info(_(f"The {item_name} ‘{group}’ only has {n} example; verified."))
            updatestatus(True) #on coming *in* with one
            return 1
        program['status'].build()
        last=False
        if not items: #then remove the group
            groups=self.groups(wsorted=True) #from which to remove, put back
            # log.info("Groups: {}".format(self.groups(toverify=True)))
            verified=False
            log.info("Group ‘{}’ has no examples; continuing.".format(group))
            # log.info("Groups: {}".format(self.groups(toverify=True)))
            updatestatus(False)
            log.info("Group-groups: {}-{}".format(group,groups))
            if group in groups:
                groups.remove(group)
            # log.info("Group-groups: {}-{}".format(group,groups))
            program['status'].groups(groups,wsorted=True)
            log.info("All groups: {}".format(self.groups(wsorted=True)))
            log.info("Groups to verify: {}"
                        "".format(self.groups(toverify=True)))
            return
        elif len(items) == 1:
            log.info(_("Group ‘{}’ only has {} example; marking verified and "
                    "continuing.").format(group,len(items)))
            updatestatus(True)
            return 1
        self.getrunwindow(msg=_(f"preparing to verify the {item_name} ‘{group}’"))
        titles=ui.Frame(self.runwindow.frame,
                        column=1, row=0, columnspan=1, sticky='w')
        ui.Label(titles, text=title, font='title', column=0, row=0, sticky='w')
        """Move this to bool vars, like for sort"""
        if hasattr(self,'groupselected'): #so it doesn't get in way later.
            delattr(self,'groupselected')
        row=0
        column=0
        if group in groups:
            if len(groups)-1:
                prog=(f"({len(groups)} remaining)")
            else:
                prog=(f"(last)")
            ui.Label(titles,text=prog,anchor='w',padx=10,column=1,sticky='ew')
        ui.Label(self.runwindow.frame,
                image=self.pageicon(macrosort),
                text='',row=0,column=0,sticky='nw')
        i=ui.Label(titles, text=instructions,
                row=1, column=0, columnspan=2, sticky='wns')
        i.wrap()
        if group != 'NA':
            ui.Label(self.runwindow.frame, image=f'verify{img_mod}',
                        text='', row=1,column=0,
                        sticky='nws')
        """Scroll after instructions"""
        """put entry buttons here."""
        if macrosort:
             self.buttonframe=SortButtonFrame(self.runwindow.frame, self,
                                        list(items),
                                        macrosort=True,
                                        show_check=True,
                                        remove_on_click=True, column=1,
                                        row=1, sticky='new', columnspan=2)
        else:
            self.buttonframe=ui.ScrollingFrame(self.runwindow.frame,
                                    row=1,column=1,
                                    sticky='wsn')
            bc=self.buttoncolumns if len(items) >= self.min_to_multicolumn else 1
            for item in items:
                if self.runwindow.exitFlag.istrue():
                    return
                if item is None: #needed?
                    continue
                n=len(self.buttonframe.content.winfo_children())
                self.verifybutton(self.buttonframe.content,item,
                                        row=n//bc, 
                                        column=n%bc,
                                        label=False)
        self.verifycanary=ui.Frame(self.buttonframe.content,
                            row=self.buttonframe.content.nrows(),
                            sticky='ew') #Keep on own row
        b=ui.Button(self.verifycanary, text=oktext,
                        cmd=self.verifycanary.destroy,
                        anchor='w',
                        font='instructions',
                        column=0, row=0, sticky='ew')
        if self.runwindow.exitFlag.istrue():
            return
        self.runwindow.waitdone()
        self.runwindow.deiconify() # not until here
        self.runwindow.wait_window(self.verifycanary)
        if self.runwindow.exitFlag.istrue(): #i.e., user exited, not hit OK
            return
        log.debug("User selected ‘{}’, moving on.".format(oktext))
        if macrosort:
            self.verifyselected(macrosort=True)
            if len(self.buttonframe.groupbuttonlist) > 1:
                updatestatus(True)
            else:
                updatestatus(False) #on *finishing* with one/none
        else:
                updatestatus(True)
        self.runwindow.on_quit()
        return 1
    def verifybutton(self,parent,sense,row,column=0,label=False,**kwargs):
        """This should maybe take examples as input, rather than senses"""
        # This must run one subcheck at a time. If the subcheck changes,
        # it will fail.
        # should move to specify location and fieldvalue in button lambda
        def notok():
            if len(self.currentsortitems) > 2:
                self.removeitemfromgroup(sense,sorting=True,write=False)
                self.currentsortitems.remove(sense)
            else:
                for i in self.currentsortitems:
                    self.removeitemfromgroup(i,sorting=True,write=False)
                self.verifycanary.destroy()
            self.maybewrite()
            bf.destroy()
        if 'font' not in kwargs:
            kwargs['font']='read'
        if 'anchor' not in kwargs:
            kwargs['anchor']='w'
        #This should be pulling from the example, as it is there already
        check=program['params'].check()
        frame=self.get_frame()
        text=sense.formatted(self.analang, self.glosslangs, self.ftype, frame)
        if program['settings'].lowverticalspace:
            ipady=0
        else:
            ipady=15*program['scale']
        if label==True:
            b=ui.Label(parent, text=text,
                    column=column, row=row,
                    sticky='ew',
                    ipady=ipady,
                    **kwargs
                    )
        else:
            bf=ui.Frame(parent, pady=1, padx=1, column=column, row=row,
                        sticky='w', border=True
                        ) #This will be killed by removeitemfromgroup
            b=ui.Button(bf, text=text, pady='0',
                    cmd=notok,
                    column=column, row=0,
                    sticky='ew',
                    ipady=ipady, #Inside the buttons...
                    **kwargs
                    )
        b['image']=scaleimageifthere(sense)
        b['compound']='left'
    def reset_selected(self):
        for k in self.groupvars:
            self.groupvars[k].set(False)
    def get_selected(self):
        return [k for k in self.groupvars
                if self.groupvars[k] is not None #necessary?
                if self.groupvars[k].get() #only those marked True
                ]
    def group_pairs_to_distinguish(self, macrosort=False):
        if macrosort:
            groups=program['alphabet'].glyphs()
        else:
            groups=[i for i in program['status'].verified() if i != 'NA']
        return set(itertools.combinations(groups, 2))
    def to_distinguish(self, macrosort=False):
        if macrosort:
            d=program['alphabet'].distinguished_by_cvt()
        else:
            d=program['status'].distinguished()
        #whatever ordering was stored, remove either if there
        return self.group_pairs_to_distinguish(macrosort=macrosort
                                                )-d-{(y,x) for x,y in d}
    def join(self,macrosort=False):
        def move_on_cleanly():
            # self.runwindow.withdraw()
            # self.last_pair=pair_frame.winfo_children()
            # self.last_pair=self.current_pair
            for w in self.current_pair:
                buttons[w].grid_remove() #don't destroy buttons with canary
            # for w in pair_frame.winfo_children():
            #     w.grid_remove() #don't destroy buttons with canary
            self.canary.destroy()
        def join_pair():
            lpr=sorted(self.current_pair,key=str) #put a number first (to remove)
            log.info(f"User selected {lpr} to join, joining them ({macrosort=}).")
            msg=_("Now we're going to move group ‘{0}’ into "
                "‘{1}’, removing ‘{0}’ and marking ‘{1}’ unverified.".format(*lpr))
            self.runwindow.wait(msg=msg)
            """All the senses we're looking at, by ps/profile"""
            if macrosort:
                log.info(f"Running join_pair! {macrosort=}")
                program['alphabet'].join_glyphs(*lpr)
                log.info(f"join_pair done {macrosort=}")
            else:
                self.updatebygroupsense(*lpr) #calls marksortgroup on all
                self.updatestatus(group=lpr[1], #no longer by updatebygroupsense
                                verified=False, #b/c joined
                                writestatus=True)
            self.did[f'join{img_mod}']=True
            self.runwindow.on_quit()
        def distinguish_pair():
            if macrosort:
                program['alphabet'].distinguish(self.current_pair)
                program['alphabet'].save_settings()
            else:
                program['status'].distinguish(self.current_pair)
                program['status'].store()
            move_on_cleanly()
        log.info(f"Running join! {macrosort=}")
        """This window allows the user to join groups that sound the same. """
        """This should move to a presentation of permutations (choose two), so
        the user gets a series of "are x and y the same (or different?)?"
        questions that can be easily answered, that we can force to be addressed
        thoroughly (rather than let the user decide that he has looked at each).
        """
        #This function should exit 1 on a window close, 0/None on all ok.
        cvt=program['params'].cvt()
        check=program['params'].check()
        ps=program['slices'].ps()
        profile=program['slices'].profile()
        pairs=list(self.to_distinguish(macrosort=macrosort))
        npairs=len(pairs) #leave this alone, for progress
        if not pairs:
            log.debug("No groups to distinguish!")
            return
        self.getrunwindow()
        oktext=_('These are each different from the other(s)')
        if macrosort:
            buttonclass=SortGlyphGroupButtonFrame
            img_mod='glyphs'
            title_mod="Letter"
            join_icon='joinglyphs'
            title_mod_2=''
        else:
            buttonclass=SortGroupButtonFrame
            img_mod=''
            title_mod="Sort"
            title_mod_2=f" (‘{check}’)"
            join_icon='join'
        title=_(f"Review {title_mod} Groups{title_mod_2}")
        self.runwindow.frame.titles=ui.Frame(self.runwindow.frame,
                                            column=1, row=0,
                                            columnspan=1, sticky='ew'
                                            )
        ltitle=ui.Label(self.runwindow.frame.titles, text=title,
                font='title', anchor='w',
                column=0, row=0, sticky='ew',
                )
        self.progress=ui.Progressbar(self.runwindow.frame.titles,
                                row=1, sticky='ew')
        ui.Label(self.runwindow.frame,
                image=self.pageicon(),
                text='',row=0,column=0,sticky='nw')
        ui.Label(self.runwindow.frame,
                image=f'join{img_mod}', image_pixels=300,
                image_scaleto='width',
                text='',
                row=1,column=0,rowspan=2,sticky='nw'
                )
        response_button_frame=ui.Frame(self.runwindow.frame,
                                        column=1, row=2, pady=10, sticky='news')
        ui.Button(response_button_frame,
                text=_("Same"), font='read',
                image=f'join{img_mod}_same', compound="bottom",
                image_pixels=200, image_scaleto='width',
                cmd=join_pair,
                column=0, padx=10, ipadx=10, sticky='nsw')
        ui.Button(response_button_frame,
                text=_("Different"), font='read',
                image=f'join{img_mod}_different', compound="bottom",
                image_pixels=200, image_scaleto='width',
                cmd=distinguish_pair,
                column=1, padx=10, ipadx=10, sticky='nes')
        if pairs:
            self.runwindow.waitdone()
        buttons={}
        pair_frame=ui.Frame(self.runwindow.frame, column=1, row=1)
        # self.last_pair=[]
        while pairs:
            self.progress.current(1 -len(pairs)/npairs)
            self.current_pair=pairs[0]
            log.info(f"Working on {self.current_pair} {len(pairs)} remaining "
                    f"of {npairs}")
            r=0
            for group in self.current_pair:
                if group in buttons:
                    buttons[group].grid(row=r)
                else:
                    buttons[group]=buttonclass(pair_frame, self,
                            group=group,
                            showtonegroup=True,
                            label=True,
                            row=r, sticky='w')
                r=1
            # for p in self.last_pair:
            #     buttons[p].grid_remove() #after creation; bounce less
            # self.last_pair=self.current_pair
            self.canary=ui.Label(pair_frame,text='',col=1)
            # self.runwindow.deiconify()
            pair_frame.wait_window(self.canary)
            if self.did[f'join{img_mod}']:
                return 1
            if self.runwindow.exitFlag.istrue():
                log.info("Runwindow exited.")
                return
            pairs=list(self.to_distinguish(macrosort=macrosort))
            log.info(f"Runwindow still open, continuing to next in {pairs}.")
        self.runwindow.on_quit()
        return 1
    def tryNAgain(self):
        check=program['params'].check()
        if check in program['status'].checks():
            senses=self.getsensesincheckgroup(group='NA')
        else:
            #Give an error window here
            log.error("Not Trying again; set a check first!")
            self.getrunwindow(msg=_("Resetting unSorted items"))
            buttontxt=_("Sort!")
            text=_("Not Trying Again; set a tone frame first!")
            ui.Label(self.runwindow.frame, text=text).grid(row=0,column=0)
            return
        for item in senses:
            self.removeitemfromgroup(item)
        self.runcheck()
    def rename_group(self,x,y,updatestatus=True):
        self.updatebygroupsense(x,y,
                                updatestatus=updatestatus,
                                updateforms=True)
        self.rename_group_verification(x,y)
    def rename_group_verification(self,x,y,**kwargs):
        v=program['status'].verified(**kwargs)
        if x in v:
            log.info(f"Found verified value to change: {x}>{y}")
            v.remove(x)
            v.append(y)
            program['status'].verified(g=v,**kwargs)
    def updatebygroupsense(self,x,y,updateforms=False,updatestatus=True):
        """This needs to apply during sorting and without, when sorting variables 
        and status may not be available.
        This method does not change the sorting status of any sense, but moves a 
        sense from one sort group to another.
        use not_sorting=True to prevent requiring sorting variables.
        """
        """Generalize this for segments"""
        # This function updates the field value and verification status (which
        # contains the field value) in the lift file.
        # This is all the words in the database with the given
        # check:value correspondence (for a given ps/profile)
        check=program['params'].check()
        lst2=self.getsensesingroup(check,x) #by annotations, for C/V
        # We are agnostic of verification status of any given entry, so just
        # use this to change names, not to mark verification status (do that
        # with self.updatestatuslift())
        # rm=self.verificationcode(check=check,group=oldvalue)
        # add=self.verificationcode(check=check,group=newvalue)
        """The above doesn't test for profile, so we restrict that next"""
        profile=program['slices'].profile()
        senses=program['slices'].inslice(lst2)
        ftype=program['params'].ftype()
        if not senses:
            log.info("No senses for {}={}".format(check,x))
            return
        for sense in senses:
            u = threading.Thread(target=self.marksortgroup,
                                args=(sense,y),
                                kwargs={#'check':check,
                                        # 'ftype':ftype,
                                        # remove for testing this fn:
                                        # 'nocheck': True, #don't verify from lift
                                        'thread_name':'_'.join([sense.id,y]),
                                        'not_sorting':True,
                                        'updateverification':True,
                                        'updateforms':updateforms})
            u.start()
        u.join()
        if updatestatus: #update status even if not updating forms
            program['settings'].reloadstatusdata()
        for t in list(program['status'].distinguished()):
            if x in t:
                program['status'].undistinguish(t)
                program['status'].distinguish((y if t[0]==x else t[0],y if t[1]==x else t[1]))
        self.maybewrite() #once done iterating over senses
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
        self.min_to_multicolumn=6 #don't use buttoncolumns with less
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
        self.analang=program['db'].analang
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
        logfinished(start_time,msg=_("setting up background reports {}").format(done))
        log.info(_("Starting reports that didn't work in the background: {}").format(unbackground))
        for kwargs in unbackground:
            # log.info("reportmulti unbackground with kwargs {}".format(kwargs))
            self.wait(msg=kwargs)
            self.reportfn(**kwargs) #run what failed in background here
            self.waitdone()
        logfinished(start_time,msg=_("all reports ({})").format(all))
    def tonegroupreport(self,usegui=True,**kwargs):
        """This should iterate over at least some profiles; top 2-3?
        those with 2-4 verified frames? Selectable with radio buttons?"""
        start_time=nowruntime()
        #default=True redoes the UF analysis (removing any joining/renaming)
        ftype=kwargs.get('ftype',program['params'].ftype())
        def examplestoXLP(examples,parent):
            # log.info("examples : {} ({})".format(examples,type(examples)))
            counts['senses']+=1
            for example in [e for e in examples if self.analang in e.forms]:
                # skip empty examples:
                # if self.analang not in example.forms:
                #     continue
                counts['examples']+=1
                if program['settings'].audiolang in example.forms:
                    counts['audio']+=1
                self.nodetoXLP(example,parent=parent,listword=True,
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
        startnotice=_("Starting report {} {}").format(ps,profile)
        log.info(startnotice)
        program['settings'].storesettingsfile()
        waitmsg=_("{} {} Tone Report in Process\n({})").format(ps,profile,
                                                                timestamps)
        if usegui:
            resultswindow=ResultWindow(self.parent,msg=waitmsg)
        bits=[str(self.reportbasefilename),
                rx.urlok(ps),
                rx.urlok(profile),
                'ToneReport']
        if not default:
            bits.append('mod')
        self.tonereportfile='_'.join(bits)+'.txt'
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
                if len(self.analysis.sensesbygroup[i]) >= self.minwords
                ]
        dontshow=[i for i in self.analysis.orderedUFs
                if len(self.analysis.sensesbygroup[i]) < self.minwords
                ]
        if dontshow:
            log.info("Not showing groups with less than {} words: {}".format(
                                                        self.minwords,dontshow))
        checks=self.analysis.orderedchecks
        r = open(self.tonereportfile, 'w', encoding='utf-8')
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
                if kwargs.get('usegui'):
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
                        row=window.row,column=0, sticky='w'
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
                        ycounts=lambda x:len(self.analysis.sensesbygroup[x]),
                        xcounts=lambda y:len(self.analysis.valuesbycheck[y]))
        #Can I break this for multithreading?
        for group in grouplist: #These already include ps-profile
            log.info("building report for {} ({}/{}, n={})".format(group,
                grouplist.index(group)+1,len(grouplist),
                len(self.analysis.sensesbygroup[group])
                ))
            sectitle=_('\n{}'.format(str(group)))
            s1=xlp.Section(s1parent,title=sectitle)
            output(window,r,sectitle)
            l=list()
            for x in self.analysis.valuesbygroupcheck[group]:
                values=self.analysis.valuesbygroupcheck[group][x]
                # log.info("X Values: {} ({})".format(values,type(values)))
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
                    values=self.analysis.valuesbygroupcheck[group][check]
                    # log.info("Values: {} ({})".format(values,type(values)))
                    headtext='{}: {}'.format(check,', '.join(
                                            [i for i in values if i is not None]
                                                            ))
                    e1=xlp.Example(s1,id,heading=headtext)
                    for sense in self.analysis.sensesbygroup[group]:
                        # sense=program['db'].sensedict[sense]
                        #This is for window/text output only, not in XLP file
                        text=sense.formatted(self.analang,self.glosslangs)
                        #This is put in XLP file:
                        if check in sense.examples:
                            examples=[sense.examples[check]] #list just one here
                            examplestoXLP(examples,e1)
                        if text not in textout:
                            output(window,r,text)
                            textout.append(text)
                    if not e1.node.find('listWord'):
                        s1.node.remove(e1.node) #Don't show examples w/o data
            else:
                for sense in self.analysis.sensesbygroup[group]:
                    #This is put in XLP file:
                    examples=list(sense.examples.values())
                    log.info("{} exs found: {}".format(len(examples), examples))
                    if examples != []:
                        id=self.idXLP(sense)+'_examples'
                        headtext=text.replace('\t',' ')
                        e1=xlp.Example(s1,id,heading=headtext)
                        log.info(_("Asking for the following {} examples from "
                                    "id {}: {}"
                                    ).format(len(examples),sense.id,examples))
                        examplestoXLP(examples,e1)
                    else:
                        self.nodetoXLP(sense.ftypes[ftype],
                                        parent=s1,
                                        showgroups=showgroups)
                    output(window,r,text)
        sectitle=_('{} {} Data Summary').format(ps,profile)
        s2=xlp.Section(s1parent,title=sectitle)
        try:
            eps='{:.2}'.format(float(counts['examples']/counts['senses']))
        except ZeroDivisionError:
            eps=_("Div/0")
        try:
            audiopercent='{:.2%}'.format(float(counts['audio']/counts['examples']))
        except ZeroDivisionError:
            audiopercent=_("Div/0%")
        ptext=_("This report contains {} senses, {} examples, and "
                "{} sound files. That is an average of {} examples/sense, and "
                "{} of examples with sound files."
                "").format(counts['senses'],counts['examples'],counts['audio'],
                            eps,audiopercent)
        ps2=xlp.Paragraph(s2,text=ptext)
        if 'xlpr' not in kwargs:
            xlpr.close(me=me)
        text=_("Finished in {} seconds.").format(nowruntime()-start_time)
        text=logfinished(start_time,msg=_("report {} {}").format(ps,profile))
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
            msg=_("Looks like that didn't work; "
                            # "you may need "
                            # "to run a report first, or "
                            "trying again not in "
                            "the background ({})."
                        ).format(kwargs)
            log.info(msg)
            # ErrorNotice(msg)
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
            if kwargs.get('usegui'):
                self.waitdone()
            xlpr.cleanup()
            return
        """"Do I need this?"""
        print(_("Getting results of Search request"))
        c1 = 'Any'
        c2 = 'Any'
        """nn() here keeps None and {} from the output, takes one string,
        list, or tuple."""
        # kwargs['formstosearch']=self.formspsprofile(**kwargs)
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
            ufgroupsnsenses=analysis.sensesbygroup.items()
            kwargs['sectlevel']=4
            t=_("{} checks".format(program['params'].cvtdict()[kwargs['cvt']]['sg']))
            for kwargs['ufgroup'],kwargs['ufsenses'] in ufgroupsnsenses:
                if 'ufgroup' in kwargs:
                    log.info("Going to run {} report for UF group {}"
                            "".format(program['params'].cvtdict()[kwargs['cvt']]['sg'],
                                    kwargs['ufgroup']))
                sid=' '.join([t,"for",kwargs['ufgroup']])
                s2=xlp.Section(si,sid) #,level=2
                iterateUFgroups(s2,**kwargs)
        else:
            kwargs['ufgroup']=_("All")
            iterateUFgroups(si,**kwargs)
        xlpr.close(me=me)
        if usegui:
            self.runwindow.waitdone()
            if not hasattr(self,'results'): #i.e., showing results in window
                self.runwindow.on_quit()
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
        group=kwargs.get('group',program['status'].group())
            #this is only for adhoc "big button" reports.

        if isinstance(self, Multislice) and 'psprofiles' in kwargs:
            reporttype=' '.join([ps+' ('+'-'.join(kwargs['psprofiles'][ps])+')'
                                    for ps in kwargs['psprofiles']
                                ])
            if len(reporttype) > 200: #this should be more than enough chars
                reporttype=' '.join([ps+' ('+kwargs['psprofiles'][ps][0]+'-etc)'
                                for ps in kwargs['psprofiles']][:1]+['etc'])

        else:
            reporttype=' '.join([ps,profile])
        if isinstance(self,Multicheck):
            reporttype+=' '+'-'.join(self.cvtstodo)
        elif not isinstance(self,Tone) or isinstance(self,Segments):
            reporttype+='-'+check
            if group and not 'x' in check:
                reporttype+='='+group
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
        reportfileXLP='_'.join(bits)+'.xml'
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
        checkprose='{} {} {} {}={}'.format(kwargs['ps'],
                                    kwargs['profile'],
                                    kwargs['ufgroup'],
                                    kwargs['check'],
                                    kwargs['group'])
        if ('x' in kwargs['check'] and hasattr(self,'groupcomparison')
                    and self.groupcomparison):
            checkprose+='-'+self.groupcomparison
        if group.isdigit() or (hasattr(self,'groupcomparison') and
                                self.groupcomparison.isdigit()):
            log.info(_("Skipping check {} because it would break the regex"
                        "").format(checkprose))
            skipthisone=True
        if skipthisone:
            return
        # log.info(checkprose)
        """possibly iterating over all these parameters, used by buildregex"""
        self.buildregex(**kwargs)
        # log.info(f"{checkprose} (wordsbypsprofilechecksubcheckp-buildregex); \n"
        #             f"regex: {self.regex}")
        matches=set(self.sensesbyforminregex(self.regex,**kwargs))
        if 'ufsenses' in kwargs:
            matches=matches&set(kwargs['ufsenses'])
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
            setnesteddictval(self.checkcounts,n,ps,profile,ufg,c,group,othergroup)
        if n>0:
            titlebits='x'+ps+profile+check+group
            if 'x' in check:
                titlebits+='x'+othergroup
            if 'ufgroup' in kwargs:
                titlebits+=kwargs['ufgroup']
            id=rx.id(titlebits)
            rxcomment=("These items were found with this regex:\n"
                        f"{self.regex}")
            ex=xlp.Example(parent,id,heading=checkprose,comment=rxcomment)
            if hasattr(self,'basicreported') and '=' in check:
                # log.info(self.basicreported.keys())
                # log.info("Adding to basicreported for keys {}"
                #         "".format(check.split('=')))
                for c in check.split('='):
                    # log.info("adding {} matches".format(len(matches)))
                    setnesteddictval(self.basicreported,matches,c,addval=True)
            for sense in matches:
                node=sense.ftypes[ftype]
                self.nodetoXLP(node,parent=ex,listword=True) #showgroups?
                if usegui and hasattr(self,'results'): #i.e., showing results in window
                    self.results.row+=1
                    col=0
                    for t in [node.textvaluebylang(self.analang)]+[
                                node.glossbylang(l) for l in self.glosslangs]:
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
                        # log.info(f"Going to compare {kwargs['group']} with "
                        #         f"{self.groupcomparison}")
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
            g=node.glossbylang(lang)
            if g:
                bits+=g
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
        audio=node.textvaluebylang(program['db'].audiolang)
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
                xlp.Gloss(ex,lang,node.glossbylang(lang))
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
            print(ps, [i.id for i in self.profilesbysense[ps]])
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
                sid=' '.join([t,"for",kwargs['ufgroup'],kwargs['profile'],
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
        if kwargs.get('usegui'): #i.e., showing results in window
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
            if kwargs.get('usegui'):
                self.waitdone()
            xlpr.cleanup()
            return
        si=xlp.Section(xlpr,"Introduction")
        p=xlp.Paragraph(si,instr)
        sys.stdout = open(self.basicreportfile, 'w', encoding='utf-8')
        print(instr)
        log.info(instr)
        #There is no runwindow here...
        self.basicreported={}
        self.checkcounts={}
        # self.printprofilesbyps() #don't really need this
        # self.printcountssorted() #don't really need this
        t=_("This report covers {} Grammatical categories, "
            "with {} syllable profiles in each. "
            "This is of course configurable, but I assume you don't want "
            "everything."
            "".format("the top "+str(program['settings'].maxpss)
                        if program['settings'].maxpss
                        else 'all', #fix this!
                        "the top "+str(program['settings'].maxprofiles)
                                    if program['settings'].maxprofiles
                                    else 'all'))
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
                # kwargs['formstosearch']=self.formspsprofile(**kwargs)
                t=_("{} {}s".format(kwargs['profile'],kwargs['ps']))
                s2=xlp.Section(s1,t,level=2)
                log.info(t)
                if self.byUFgroup:
                    self.makeanalysis(**kwargs)
                    self.analysis.donoUFanalysis()
                    ufgroupsnids=[(i,j) for i,j in
                                self.analysis.sensesbygroup.items()
                                #don't report small groups
                                if len(j) >= self.minwords]
                    kwargs['sectlevel']=4
                    for kwargs['ufgroup'],kwargs['ufsenses'] in ufgroupsnids:
                        if 'ufgroup' in kwargs:
                            log.info("Going to run report for UF group {}"
                                    "".format(kwargs['ufgroup']))
                        sid=' '.join([t,"for",kwargs['ufgroup']])
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
        if kwargs.get('usegui'):
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
                            table=xlp.Table(s3s,caption+' Correspondences')
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
                                    table=xlp.Table(s3s,caption+' Correspondences')
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
        self.status.redofinalbuttons() #because the fns changed
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
        self.status.redofinalbuttons() #because the fns changed
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
        self.status.redofinalbuttons() #because the fns changed
class SortSyllables(Sort,Segments,TaskDressing):
    def taskicon(self):
        return program['theme'].photo['iconWord']
    def tasktitle(self):
        return _("Sort Word Syllables") #Citation Form Sorting in Tone Frames
    def tooltip(self):
        return _("This task helps you sort words in citation form by whole "
                "word syllable profiles.")
    def dobuttonkwargs(self):
        return {'text':_("Sort!"),
                'fn':self.runcheck,
                # column=0,
                'font':'title',
                'compound':'bottom', #image bottom, left, right, or top of text
                'image':program['theme'].photo['Word'], #self.cvt
                'sticky':'ew'
                }
    def presortgroups(self):
        """organize all the words that belong to the top X syllable profiles,
        and mark them belonging to groups defined by profile"""
        """These groups should be sorted into and out of as for others"""
        """cvprofilevalue should have set value on boot, so we shouldn't
        recalculate it here. but once sorted, we shouldn't override on each
        boot.
        We should likely store different values, one that is calculated,
        the other is user data
        """
        ps=program['slices'].ps()
        for sense in program['db'].sensesbyps[ps]:
            valuelist=[k for k in program['settings'].profilesbysense[ps]
                        if sense in program['settings'].profilesbysense[ps][k]]
            if valuelist:
                sense.cvprofilevalue(program['params'].ftype(),valuelist[0])
    def runcheck(self):
        program['settings'].storesettingsfile()
        log.info("Running check...")
        cvt=program['params'].cvt()
        check=program['params'].check()
        profiles=program['slices'].profiles()
        """further specify check check in maybesort, where you can send the user
        on to the next setting"""
        self.presortgroups()
        self.updatesortingstatus() # Not just tone anymore
        self.maybesort(firstrun=True)
    def __init__(self, parent):
        program['params'].cvt('S') #syllable
        TaskDressing.__init__(self,parent)
        Sort.__init__(self, parent)
        Segments.__init__(self,parent)
class SortCV(Sort,Segments,TaskDressing):
    """docstring for SortCV."""
    def __init__(self, parent):
        TaskDressing.__init__(self,parent)
        Sort.__init__(self, parent)
        Segments.__init__(self,parent)
class SortV(Sort,Segments,TaskDressing):
    def taskicon(self):
        return 'iconV'#program['theme'].photo['iconV']
    def tasktitle(self):
        return _("Sort Vowels") #Citation Form Sorting in Tone Frames
    def tooltip(self):
        return _("This task helps you sort words in citation form by vowels.")
    def dobuttonkwargs(self):
        return {'text':_("Sort!"),
                'fn':self.runcheck,
                'font':'title',
                'compound':'bottom', #image bottom, left, right, or top of text
                'image':program['theme'].photo['V'], #self.cvt
                'sticky':'ew'
                }
    def __init__(self, parent):
        program['params'].cvt('V')
        TaskDressing.__init__(self,parent)
        Sort.__init__(self, parent)
        Segments.__init__(self,parent)
class SortC(Sort,Segments,TaskDressing):
    def taskicon(self):
        return 'iconC'#program['theme'].photo['iconC']
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
        program['params'].cvt('C')
        TaskDressing.__init__(self,parent)
        Sort.__init__(self, parent)
        Segments.__init__(self,parent)
class SortT(Sort,Tone,TaskDressing):
    def taskicon(self):
        return 'iconT'#program['theme'].photo['iconT']
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
        sense=None
        program['db'].addpronunciationfields(
                                    guid,sense.id,self.analang,self.glosslangs,
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
    def updateerror(self):
        self.errorlabel['text'] = ''
    def updateform(self,event=None):
        self.updateerror()
        self.set_ok_w_form()
    def refresh_status_buttons(self,*args):
        for i in [args]:
            if (i in self.status.glyphbuttons 
                    and self.status.glyphbuttons[i].winfo_exists()):
                self.status.glyphbuttons[self.group].destroy()
                self.status.glyphbuttons[new].destroy()
    def switchgroups(self,comparison=None):
        #this doesn't save!
        if (not hasattr(self,'group') or not hasattr(self,'group_comparison')
            and not comparison):
            log.error(_("Missing either group or comparison, without value "
                        "specified; can't switch them."))
            return
        log.info(f"Swtiching groups; using ‘{self.group_comparison}’ for "
                f"‘{self.group}’")
        #actually change the data, not the group settings:
        #This method should go somewhere more reasonable:
        g=self.add_int_group(self) #Don't merge groups!
        if self.cvt == 'T':
            fn=self.rename_group
        else:
            fn=self.rename_macrogroup
        fn(self.group,g,updatestatus=False)
        fn(self.group_comparison,self.group,updatestatus=False)
        fn(g,self.group_comparison)
        self.refresh_status_buttons(g,self.group_comparison)
        # program['settings'].setgroup(gc)
        self.runwindow.on_quit()
        self.makewindow() #The other group needs a name, too!
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
        # log.info("self.groups: {}".format(self.groups))
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
    def polygraphwarn(self,newvalue):
        if len(newvalue) != 1 or len(self.group) != 1:
            warning=_("This name change (‘{}’ > ‘{}’) impacts your "
                        "digraph and trigraph settings."
                        ).format(self.group,newvalue)
            if len(newvalue) > 1:
                warning+=_("\n{} will add ‘{}’ to those settings."
                            ).format(program['name'],newvalue)
                if newvalue not in program['settings'].polygraphs[self.analang][self.cvt]:
                    program['settings'].polygraphs[self.analang][self.cvt][newvalue]=True
                    program['settings'].storesettingsfile('profiledata')
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
            log.info(warning)
            # self.err=ErrorNotice(warning,parent=self,title=title)
    def submitform(self):
        newvalue=self.transcriber.formfield.get()
        if newvalue == '':
            noname=_("Give a name for this group!")
            log.debug(noname)
            self.errorlabel['text'] = noname
            return 1
        elif newvalue != self.group and newvalue in self.groups:
            deja=_("Sorry, there is already a group with "
                            "that label; see comparison below. \n"
                            "If you want to join the "
                            "groups, go back and do it in the sort task.")
            log.debug(deja)
            self.errorlabel['text'] = deja
            self.setgroup_comparison(newvalue)
            return 1
        if program['params'].cvt() != 'T': #Warning only on segmental changes
            self.polygraphwarn(newvalue)
            #These should each make one change only, checking for overwrites
            self.rename_macrogroup(self.group,newvalue)
            program['alphabet'].glyph(newvalue)
            self.refresh_status_buttons(self.group,newvalue)
        else:
            """updateforms=True doesn't seem to be working for segments"""
            self.updatebygroupsense(self.group,newvalue,updateforms=True)
            #NO: this should update formstosearch and profile data.
            # log.info("Doing renamegroup: {}>{}".format(self.group,newvalue))
            program['status'].renamegroup(self.group,newvalue) #status file only
            # log.info("Doing updategroups")
            self.updategroups() #updates self.groups self.group self.othergroups self.groupsdone
            program['settings'].storesettingsfile(setting='status')
            """Update regular expressions here!!"""
        self.maybewrite()
        self.ok_done=True
        # update forms, even if group doesn't change:
        if hasattr(self,'group_comparison'):
            delattr(self,'group_comparison') # in either case
        self.runwindow.on_quit()
    def next(self):
        log.debug("running next group")
        error=self.submitform()
        if not error:
            # log.debug("group: {}".format(group))
            ints=[i for i in program['status'].groups(wsorted=True)
                    if i.isdigit()]
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
    def setgroup_comparison(self,group=None,**kwargs):
        if group:
            program['settings'].set('group_comparison',group)
        else:
            #this returns its window:
            w=self.getglyph(comparison=True,**kwargs)
            if w and w.winfo_exists(): #This window may be already gone
                log.info("Waiting for {}".format(w))
                w.wait_window(w)
        log.info(f"Groups: {self.group} (of {self.groups}); "
                f"{program['settings'].group_comparison}?")
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
            self.compframe.bf2=SortGlyphGroupButtonFrame(
                                    self.compframe.compframeb,
                                    self,
                                    group=self.group_comparison,
                                    showtonegroup=True,
                                    playable=True,
                                    unsortable=False, #no space, bad idea
                                    alwaysrefreshable=True,
                                    font='default',
                                    wraplength=self.buttonframew
                                    )
            self.compframe.bf2.grid(row=0, column=0, sticky='w')
            self.compframe.b2=ui.Button(self.compframe.compframeb,
                                        text=self.switch_text,
                                        cmd=self.switchgroups,
                                        row=0, column=1, sticky='w')
            self.compframe.b2tt=ui.ToolTip(self.compframe.b2, self.switch_tt)
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
            log.info(_("This should never happen (renamegroup/"
                        "comparisonbuttons)"))
        self.sub_c['text']=t
    def __init__(self,parent): #frame, filename=None
        TaskDressing.__init__(self, parent)
        program['settings'].makeeverythingok()
        self.ftype=program['params'].ftype()
        self.mistake=False #track when a user has made a mistake
        self.analang=program['params'].analang()
        program['status'].makecheckok()
        Sound.__init__(self)
class TranscribeS(Transcribe,Segments):
    macrosort=True
    def done(self):
        log.info("Transcribe done")
        self.submitform()
        program['alphabet'].save_settings()
        self.donewpyaudio()
    def go_back(self):
        log.info("Transcribe done for now (going back)")
        self.runwindow.on_quit()
        self.donewpyaudio()
        self.parent.redo_joinglyphs(self.group)
    def set_ok_w_form(self):
        form=self.transcriber.formfield.get()
        self.oktext.set(f"OK: use ‘{form}’ for this sound")
        if form:
            self.ok_button['state'] = 'normal'
        else:
            self.ok_button['state'] = 'disabled'
    def makewindow(self, glyph=None, event=None):
        self.ok_done=False
        if glyph:
            self.group=program['alphabet'].glyph(glyph)
        else:
            self.group=program['alphabet'].glyph()
        if not isinstance(self.group, str):
            log.info(f"Group not string! ({self.group}, {type(self.group)})")
        cvt=program['params'].cvt()
        self.groups=program['alphabet'].glyphs()
        # self.groups=program['status'].all_groups_verified_for_cvt()
        self.otherglyphs=set(self.groups)-{self.group}
        padx=50
        if program['settings'].lowverticalspace:
            log.info("Using low vertical space setting")
            pady=0
        else:
            pady=10
        self.buttonframew=int(program['screenw']/3.5)
        title=[program['params'].cvtdict()[cvt]['sg'],_("letter")]
        getformtext=_("What letter(s) do you want to use for this {} "
                        "group?").format(program['params'].cvtdict()[cvt]['sg'])
        if self.group.isdigit():
            title.insert(0,_("Name"))
            getformtext+=_("\nBecause this is a new group, you need to give it "
                            "some name now.")
            initval=''
        else:
            title.insert(0,_("Rename"))
            title.append(f"‘{self.group}’")
            initval=self.group
        self.getrunwindow(title=title)
        titlel=ui.Label(self.runwindow.frame,text=' '.join(title),
                        font='title',
                        row=0,column=0,sticky='ew',padx=padx,pady=pady
                        )
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
                                initval=initval,
                                soundsettings=self.soundsettings,
                                chars=self.glyphspossible,
                                row=0,column=0,sticky=''
                                )
        self.transcriber.formfield.bind('<KeyRelease>', self.updateform) #apply function after key
        """to here"""
        infoframe=ui.Frame(inputfeedbackframe,
                            row=0,column=1,sticky=''
                            )
        """Make this a pad of buttons, rather than a label, so users can
        go directly where they want to be"""
        g=nn(self.otherglyphs,perline=len(self.otherglyphs)//3)
        # log.info(f"{self.groups=}, {self.otherglyphs=}; {g=}")
        glyphslabel=ui.Label(infoframe,
                            text=f"Don't use Other Groups:\n{g}",
                            column=1,
                            sticky='new',
                            padx=padx,
                            rowspan=2
                            )
        self.errorlabel=ui.Label(infoframe,text='',
                            fg='red',
                            wraplength=int(self.frame.winfo_screenwidth()/3),
                            row=2,column=1,sticky='nsew'
                            )
        ui.Button(infoframe, #don't make this too wide
                    text=_("Go back and join \nwith one of\n← these groups"),
                    command=self.go_back,
                    column=2,
                    rowspan=2,
                    sticky='nsew'
                    )
        examplesframe=ui.Frame(self.runwindow.frame,
                                row=4,column=0,sticky='',
                                # border=1
                                )
        # self.oktext=_("OK")
        self.oktext=ui.StringVar()
        # self.transcriber.formfield
        self.ok_button=ui.Button(examplesframe, 
                                # text=self.oktext,
                                textvariable=self.oktext,
                                font='title',
                                row=0,
                                column=1,
                                sticky='ns',
                                padx=padx,
                                ipadx=30,
                                ipady=20,
                                pady=20,
                                command=self.done
        )
        self.updateform() #updates button state
        cmd=lambda x=self.group:self.transcriber.set_value(x)
        b=SortGlyphGroupButtonFrame(examplesframe, self,
                                group=self.group,
                                showtonegroup=True,
                                on_select=cmd,
                                playable=True,
                                alwaysrefreshable=True,
                                row=0, column=0, sticky='w',
                                wraplength=self.buttonframew
                                )
        self.window_failed=False
        if not b.hasexample:
            self.clear_runwindow()
            self.window_failed=True
            return
        self.compframe=ui.Frame(examplesframe,
                    highlightthickness=10,
                    highlightbackground=self.frame.theme.white,
                    pady=20, row=1, column=0, sticky='',
                    columnspan=2
                    ) #no hlfg here
        t=_('Compare with another group')
        fn=self.setgroup_comparison
        self.sub_c=ui.Button(self.compframe,
                            text = t,
                            command = lambda:fn(),
                            row=0,column=0
                            )
        self.comparisonbuttons()
        self.runwindow.waitdone()
        self.sub_c.wait_window(self.runwindow) #then move to next step
        if hasattr(self,'status'): #i.e., working from Transcribe task directly
            self.status.updateglyphbuttons()
        """Store these variables above, finish with (destroying window with
        local variables):"""
    def __init__(self, parent):
        self.switch_text=_("Switch letters with this group")
        self.switch_tt=_("This switches letters for the two groups, and "
                            "updates each of them")
        Transcribe.__init__(self,parent)
        Segments.__init__(self,parent)
class TranscribeV(TranscribeS):
    def tasktitle(self):
        return _("Vowel Letters")
    def tooltip(self):
        return _("This task helps you decide on your vowel letters.")
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
        self.cvt=program['params'].cvt('V')
        super().__init__(parent)
class TranscribeC(TranscribeS):
    def tasktitle(self):
        return _("Consonant Letters")
    def tooltip(self):
        return _("This task helps you decide on your consonant letters.")
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
        self.cvt=program['params'].cvt('C')
        super().__init__(parent)
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
    def done(self):
        log.info("Transcribe done")
        self.submitform()
        self.donewpyaudio()
    def set_ok_w_form(self):
        pass #maybe use some day?
    def makewindow(self, group=None, event=None):
        if group:
            self.group=program['status'].group(group)
        """Go through this and tease apart what is needed for tone complexity,
        and move that to tone.
        Note to user: you can't pick these group names (switch later, not here)
        Make another function to switch letters between groups."""
        # log.info("Making transcribe window")
        def changegroupnow(event=None):
            w=program['taskchooser'].getgroup(wsorted=True)
            self.runwindow.wait_window(w)
            if not w.exitFlag.istrue():
                self.runwindow.on_quit()
                self.makewindow()
        cvt=program['params'].cvt()
        ps=program['slices'].ps()
        profile=program['slices'].profile()
        check=program['params'].check()
        self.buttonframew=int(program['screenw']/3.5)
        if not check:
            self.getcheck(guess=True)
            if check is None:
                # log.info("I asked for a check name, but didn't get one.")
                return
        if not program['status'].groups(wsorted=True):
            log.error(_("I don't have any sorted data for check: {}, "
                        "ps-profile: {}-{},").format(check,ps,profile))
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
        self.transcriber=transcriber.Transcriber(inputfeedbackframe,
                                initval=self.group,
                                soundsettings=self.soundsettings,
                                chars=self.glyphspossible,
                                row=0,column=0,sticky=''
                                )
        self.transcriber.formfield.bind('<KeyRelease>', self.updateerror)
        infoframe=ui.Frame(inputfeedbackframe,
                            row=0,column=1,sticky=''
                            )
        """Make this a pad of buttons, rather than a label, so users can
        go directly where they want to be"""
        g=nn(self.othergroups,perline=len(self.othergroups)//5)
        # log.info("There: {}, NTG: {}; g:{}".format(self.groups,
        #                                             self.othergroups,g))
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
                                group=self.group,
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
    def __init__(self, parent): #frame, filename=None
        self.switch_text=_("Switch transcriptions with this group")
        self.switch_tt=_("This doesn't save the curent group")
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
            if uf == '':
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
                if group in self.analysis.sensesbygroup: #selected ones only
                    log.debug(_("Changing values from {} to {} for the "
                            "following sense.ids: {}").format(group,uf,
                            [i.id for i in self.analysis.sensesbygroup[group]]))
                    for sense in self.analysis.sensesbygroup[group]:
                        sense.uftonevalue(uf)
            self.maybewrite()
            self.runwindow.on_quit()
            program['status'].last('joinUF',update=True)
            self.tonegroupsjoinrename() #call again, in case needed
        self.makeanalysis()
        def redo(timestamps=_("By manual request")):
            self.wait(_("Redoing Tone Analysis")+'\n'+timestamps)
            self.analysis.do()
            self.waitdone()
            # self.runwindow.on_quit()
            self.tonegroupsjoinrename(redo=True) #call again, in case needed
        def done():
            self.runwindow.on_quit()
        ps=kwargs.get('ps',program['slices'].ps())
        profile=kwargs.get('profile',program['slices'].profile())
        analysisOK,joinedsince,timestamps=program['status'].isanalysisOK(**kwargs) #Should specify which lasts...
        if not analysisOK:
            if not kwargs.get('redo'):
                #otherwise, the user will almost certainly be upset to have to do it later
                redo(timestamps)
            else:
                txt=_("The analysis still isn't OK after retrying; "
                        f"Check your settings and try again (e.g., "
                        f"{ps} {profile} checks: {program['status'].checks()})")
                ErrorNotice(txt,wait=True,parent=self)
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
        namefield = ui.EntryField(qframe,text=named)
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
            self.runwindow.on_quit()
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
            n=len(self.analysis.sensesbygroup[group])
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
        log.info("Using these regexs: {}".format(self.rxdict))
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
        log.info(_('Ps-Profile-Check OK; doing getresults! ({}/{}/{})').format(
                                                 ps,check,profile))
        self.getresults()
    def __init__(self, parent): #frame, filename=None
        program['params'].ftype('lc')
        Segments.__init__(self,parent)
        self.do=self.getresults
        program['status'].group(None) #default to reports with all groups
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
        # self.status.redofinalbuttons() #because the fns changed
class ReportCitationMulticheckBackground(Multicheck,Background,ReportCitation):
    """docstring for ReportCitation."""
    def tasktitle(self):
        return _("Alphabet Report (checks)") # on One Data Slice
    def __init__(self, parent):
        ReportCitation.__init__(self,parent)
        Multicheck.__init__(self)
        Background.__init__(self)
class ReportCitationMultichecksliceBackground(Multicheckslice,Background,ReportCitation):
    """docstring for ReportCitation."""
    def tasktitle(self):
        return _("Alphabet Report (slices/checks)") # on One Data Slice
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
        return _("Alphabet Report by Tone group (checks)") # on One Data Slice
    def __init__(self, parent):
        ReportCitationByUF.__init__(self, parent)
        Multicheck.__init__(self)
        Background.__init__(self)
class ReportCitationByUFMultichecksliceBackground(Multicheckslice,Background,ReportCitationByUF):
    """docstring for ReportCitation."""
    def tasktitle(self):
        return _("Alphabet Report by Tone Group (slices/checks)") # on One Data Slice
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
    def lang1(self,lang=False):
        if self and lang is False: #i.e., not specified
            return self[0]
        if self:
            self[0]=lang #before others
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
        if isinstance(node,lift.et.Element):
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
        #This returns all the senses with a given tone value
        senses=program['taskchooser'].task.getsensesingroup(check,group)
        if not senses:
            log.error("There don't seem to be any sensids in this check tone "
                "group, so I can't get you an example. ({} {})"
                "".format(check,group))
            return []
        """The above doesn't test for profile, so we restrict that next"""
        log.info("senses ({}): {}".format(len(senses),
                                            [i.id for i in senses][:5]))
        sensesinslice=program['slices'].inslice(senses)
        log.info("sensesinslice ({}): {}".format(len(sensesinslice),
                                            [i.id for i in sensesinslice][:5]))
        if not sensesinslice:
            log.error("There don't seem to be any sensids from that check tone "
                "group in this slice-group, so I can't get you an example. "
                "({}-{}, {} {})"
                "".format(program['slices'].ps(),program['slices'].profile(),check,group))
            return []
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
        return node.hassoundfile()
    def exampletypeok(self,node,**kwargs):
        # log.info(f"exampletypeok checking {node} for {kwargs=}")
        kwargs=exampletype(**kwargs)
        if node is None:
            return
        # log.info(f"exampletypeok looking at {node=}")
        if kwargs['wglosses'] and not self.hasglosses(node):
            log.info("Gloss check failed for {}".format(node.sense.id))
            return
        if not self.hassoundfile(node) and kwargs['wsoundfile']:
            # log.info("Audio file check failed for {}".format(node.sense.id))
            return
        # log.info(f"exampletypeok returning True")
        return True
    def prefetch_examples(self, groups, all_for_cvt=False, **kwargs):
        """
        Antigravity: Optimized method to pre-fetch examples for multiple groups at once.
        This avoids iterating over the entire database for each group.
        """
        check = kwargs.get('check', program['params'].check())
        ftype = kwargs.get('ftype', program['params'].ftype())
        log.info(f"Prefetching examples for {len(groups)} groups...")
        # Prepare codes mapping to avoid repeated calls and initialize cache
        group_to_code = {}
        for group in groups:
            code = program['alphabet'].verificationcode(**{**kwargs, 'group': group})
            if code not in self.nodes_by_code:
                self.nodes_by_code[code] = [] # Initialize
                group_to_code[group] = code
        if not group_to_code:
            log.info("All groups already cached.")
            return
        # Iterate once over the database
        if program['params'].cvt() == 'T':
            # T: Tone examples
            senses = program['slices'].inslice(program['db'].senses)
            for s in senses:
                group = s.tonevaluebyframe(check)
                if group in group_to_code:
                    if check in s.examples:
                        self.nodes_by_code[group_to_code[group]].append(s.examples[check])
        elif all_for_cvt:
            # all_for_cvt: Any ps-profile
            senses = program['db'].senses
            for s in senses:
                vals = s.annotationvaluedictbyftypelang(ftype, program['db'].analang).values()
                # Check if any of our target groups are in this sense's values
                # This might be slightly expensive if vals is large, but usually it's small
                for group in groups: 
                    if group in group_to_code and group in vals:
                        if ftype in s.ftypes:
                            self.nodes_by_code[group_to_code[group]].append(s.ftypes[ftype])
        else: 
            # Standard case: Other FormParent nodes
            senses = program['slices'].inslice(program['db'].senses, **kwargs)
            for s in senses:
                val = s.annotationvaluebyftypelang(ftype, program['db'].analang, check)
                group = str(val)
                if group in group_to_code:
                    if ftype in s.ftypes:
                        self.nodes_by_code[group_to_code[group]].append(s.ftypes[ftype])
        log.info("Prefetch complete.")
    def getexamples(self,group,all_for_cvt=False,**kwargs):
        check=kwargs.pop('check',program['params'].check())
        ftype=kwargs.pop('ftype',program['params'].ftype())
        if program['params'].cvt() == 'T': # example nodes
            nodes=[s.examples[check] for s in program['slices'].inslice(
                                                        program['db'].senses)
                        if s.tonevaluebyframe(check) == group
                        ]
        elif all_for_cvt:
            nodes=[s.ftypes[ftype] for s in program['db'].senses #any ps-profile
                        if group in s.annotationvaluedictbyftypelang(ftype,
                                                program['db'].analang).values()
                    ]
        else: # Other FormParent nodes
            nodes=[s.ftypes[ftype] for s in program['slices'].inslice(
                                                        program['db'].senses,
                                                        **kwargs)
                        if s.annotationvaluebyftypelang(ftype,
                                                    program['db'].analang,
                                                    check
                                                        ) == str(group) #result str
                    ]
        return nodes
    def clear_cache(self,**kwargs):
        code=program['alphabet'].verificationcode(**kwargs)
        if code in self.nodes_by_code:
            del self.nodes_by_code[code]
    def getexample(self,group,**kwargs):
        # verificationcode fills in current values where not specified:
        code=program['alphabet'].verificationcode(**{**kwargs,'group':group})
        if code in self.nodes_by_code:#don't keep rerunning this on a given boot
            nodes=self.nodes_by_code[code]
        else:
            nodes=self.getexamples(group,**kwargs)
        if not nodes:
            # log.error(f"getexample has no example nodes for {group=}?")
            return 0,None
        n=len(nodes)
        # log.info(f"{n} nodes found by ExampleDict.getexample")
        exs_ok={i for i in nodes if self.exampletypeok(i,**kwargs)}
        # log.info(f"found {len(exs_ok)} examples with sound files")
        if kwargs.get('wsoundfile'):
            exs_ok_wo_soundfile={i for i in nodes
                            if self.exampletypeok(i,
                                            **{**kwargs, 'wsoundfile': False}
                                                )}
        else:
            exs_ok_wo_soundfile=set()
        # log.info(f"found {len(exs_ok_wo_soundfile)} examples w/o sound files")
        # include all, but with sound files first. Prioritize; give full count
        nodes=list(exs_ok)+list(exs_ok_wo_soundfile-exs_ok)
        if code in self and self[code] in nodes: #if stored value is in group
            # log.info(f"found stored example")
            if not kwargs['renew']:
                # log.info(f"returning stored example")
                node=self[code]
                kwargs['renew']=True
            else:
                # log.info(f"renewing stored example")
                txt=[_(f"Resetting to"),_(f"{code} example ({self[code]}), of "
                            f"{len(nodes)} examples with {kwargs=}")]
                i=nodes.index(self[code])
                if not kwargs.get('goback'):
                    txt.insert(1,_("next"))
                    if i == len(nodes)-1: #loop back on last
                        node=nodes[0]
                    else:
                        node=nodes[i+1]
                else:
                    txt.insert(1,_("previous"))
                    if i == 0: #loop back on last
                        node=nodes[len(nodes)-1]
                    else:
                        node=nodes[i-1]
                log.info(' '.join(txt))
        else:
            # log.info(f"Did not find stored example")
            node=nodes[0]
        self[code]=node #store for next iteration
        return len(nodes),node #self._outdict
    def __init__(self):
        super(ExampleDict, self).__init__({})
        self.nodes_by_code={}
        program['examples']=self
class SortButtonFrame(ui.ScrollingFrame):
    """This is the frame of sort group buttons."""
    def getanotherskip(self,parent,vardict):
        """This function presents a group of buttons for the user to choose
        from, after one for each tone group in that location/ps/profile in the
        database. It provides one for the user to indicate that the word doesn't
        belong in any of those (new group), and one to for the user to
        indicate that the word/frame combo doesn't work (skip).
        This happens only on init; it doesn't need to respond to changing 
        groups."""
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
            difb=ui.Button(bf1, text=newgroup,
                        cmd=different,
                        anchor='w',
                        relief='flat',
                        font='instructions',
                        column=0, row=0, sticky='ew')
        if self.cvt=='T':
            firstOK=_("This word fits in this frame")
        else:
            name=program['params'].cvcheckname(self.check)
            firstOK=_(f"This word has {name}")
        newgroup=_("Other")
        skiptext=_("Skip this item")
        if '=' in self.check:
            skiptext+=" ({})".format(self.check.replace('=','≠'))
        """This should just add a button, not reload the frame"""
        bf1=ui.Frame(parent, border=True, row=parent.nrows(), sticky='w')
        if not self.groups:
            # log.info("Making None sorted yet button")
            vardict['ok']=ui.BooleanVar()
            okb=ui.Button(bf1, text=firstOK,
                            cmd=firstok,
                            anchor='w',
                            relief='flat',
                            font='instructions',
                            column=0, row=0, sticky='ew')
        else:
            # log.info("Making different button")
            differentbutton()
        vardict['skip']=ui.BooleanVar()
        # log.info("Making skip button")
        bf2=ui.Frame(parent, border=True, row=parent.nrows(), sticky='w')
        skipb=ui.Button(bf2, text=skiptext,
                        cmd=skip,
                        anchor='w',
                        relief='flat',
                        font='instructions',
                        column=0, row=0, sticky='ew')
    def updatecounts(self):
        # log.info("Updating counts for each button")
        for b in self.groupbuttonlist:
            b.updatecount()
    def addgroupbutton(self,group):
        # log.info(f"SortButtonFrame addgroupbutton for {group}")
        if self.exitFlag.istrue():
            return #just don't die
        if program['settings'].lowverticalspace:
            # log.info("using lowverticalspace for addgroupbutton")
            scaledpady=0
        else:
            scaledpady=int(40*program['scale'])
        # log.info(f"This button at {self.groupbuttons.row=}, {self.groupbuttons.col=}")
        nbuttons=len(self.groupbuttons.winfo_children())
        r,c=nbuttons//self.buttoncolumns,nbuttons%self.buttoncolumns
        kwargs={'group':group} #this may be glyph, item code, or sort group
        if self.macrosort and not self.remove_on_click:
            frame_class=SortGlyphGroupButtonFrame #this takes glyph, calls other
        else:
            frame_class=SortGroupButtonFrame #this takes item code or sort group
        if self.macrosort and self.remove_on_click:
            kwargs=program['alphabet'].parse_verificationcode(group)
        b=frame_class(self.groupbuttons, self.task,
                        showtonegroup=True,
                        alwaysrefreshable=True,
                        remove_on_click=self.remove_on_click,
                        show_check=self.show_check,
                        row=r,
                        column=c,
                        sticky='w',
                        **kwargs
                    )
        # log.info(f'group buttons made')
        if not b.hasexample:
            log.info(f'No example found for {group}')
            b.destroy()
            return
        # log.info(f'group button example found')
        self.groupvars[group]=b.var()
        self.groupbuttonlist.append(b)
        log.info(f'Group added: {group}')
    def reset_selected(self):
        for k in self.groupvars:
            self.groupvars[k].set(False)
    def get_selected(self):
        # log.info(f"{[(i,self.groupvars[i].get()) for i in self.groupvars]}")
        return [k for k in self.groupvars
                if self.groupvars[k] is not None #necessary?
                if self.groupvars[k].get() #only those marked True
                ]
    def set_canary(self,canary):
        for b in self.groupbuttons.winfo_children():
            # self.groupbuttonlist: #might be necessary
            b.setcanary(canary)
        self.sortitem=canary    
    def __init__(self, parent, task, groups, *args, **kwargs):
        self.macrosort=kwargs.pop('macrosort',False)
        self.remove_on_click=kwargs.pop('remove_on_click',False)
        self.show_check=kwargs.pop('show_check',False)
        self.task=task
        self.groups=groups
        super(SortButtonFrame, self).__init__(parent, *args, **kwargs)
        """Children of self.runwindow.frame.scroll.content"""
        self.groupbuttons=self.content.groups=ui.Frame(self.content,sticky='ew')
        self.content.anotherskip=ui.Frame(self.content, row=1,column=0)
        """Children of self.runwindow.frame.scroll.content.groups"""
        self.groupbuttons.row=0 #rows for this frame
        self.groupbuttons.col=0 #columns for this frame
        self.groupvars={}
        self.groupbuttonlist=list()
        # entryview=ui.Frame(self.runwindow.frame)
        # """We need a few things from the task (which are needed still?)"""
        # self.task=program['status'].task()
        """These two methods each take an item and a category, into which the
        item is sorted. This should be generalizable."""
        self.check=program['params'].check()
        self.cvt=program['params'].cvt()
        self.maybewrite=program['taskchooser'].maybewrite
        waiting=task
        if self.macrosort and not self.remove_on_click:
            msg=_("Gathering groups"
                "\nOn the next screen, you will sort groups into letter groups")
            self.buttoncolumns=1
        elif self.macrosort:
            msg=_("Verifying groups"
                    "\nOn the next screen, you will verify groups as belonging together")
            self.buttoncolumns=1
        else:
            msg=_("Sorting words"
                    "\nOn the next screen, you will sort words into groups")
            self.buttoncolumns=program['status'].task().buttoncolumns
        waiting.wait(msg)
        
        # Prefetch examples for all groups at once to avoid O(N^2) lookup
        program['examples'].prefetch_examples(self.groups, **kwargs)
        
        for group in self.groups:
            self.addgroupbutton(group)
            waiting.waitprogress(100*self.groups.index(group)/len(self.groups))
        """Children of self.runwindow.frame.scroll.content.anotherskip"""
        if not self.remove_on_click:
            self.getanotherskip(self.content.anotherskip,self.groupvars)
        waiting.waitprogress(100)
        waiting.waitdone()
class _GroupButtonFrame(object):
    unbuttonargs=['renew','canary','labelizeonselect',
                        'label','playable','unsortable',
                        'alwaysrefreshable','wsoundfile',
                        'showtonegroup', 'remove_on_click',
                        'goback','all_for_cvt', 'on_select',
                        'show_check'
                        ]
    defaults={'sticky':'',
                'rowspan': 1,
                'columnspan': 1,
                'border':3, #frame boarder, thickness of black line
                'padx':2, #make this zero, or it will be 0/15... (below)
                'pady':1
            }
    frameargs=['row','column','sticky',
                'rowspan',
                'columnspan',
                'padx',
                'pady',
                'ipadx',
                'ipady',
                'border',
                ]
    def select(self):
        self._var.set(True)
    def sortnext(self):
        self.canary.destroy()
    def selectnsortnext(self):
        self.select()
        self.sortnext()
    def selectnlabelize(self):
        self.select()
        self.labelize()
        # self.kwargs['label']=True
        # self.again()
        self.sortnext()
        # remove()
    def labelize(self):
        self.button_select.destroy()
        self.labelbutton()
    def var(self):
        return self._var
class SortGroupButtonFrame(ui.Frame,_GroupButtonFrame):
    def again(self):
        """Do I want this? something less drastic?"""
        for child in self.winfo_children():
            child.destroy()
        self.makebuttons()
        self.update_idletasks()
        if self.kwargs['playable'] and self._playable:
            self.player.play()
    def backup(self,event=None):
        self.kwargs['goback']=True
        self.kwargs['alwaysrefreshable']=True
        self.getexample(**self.kwargs)
        self.again()
        self.kwargs['goback']=False #don't keep going on next
    def remove(self):
        # self.task.groupbuttonlist.remove(self)
        self.destroy() # will this keep the variable around, if stored elsewhere?
        if len(self.parent.winfo_children()) == 1: #When removing one of two
            # for now, let''s leave the other alone; keep glyph names
            # which have already been decided.
            # self.task.groupbuttonlist[0].selectnremove() #remove the other, too
            # log.info(f"{self=} ({type(self)})")
            # log.info(f"{self.task=} ({type(self.task)})")
            # log.info(f"{self.task.task=} ({type(self.task.task)})")
            self.task.verifycanary.destroy()
    def selectnremove(self):
        self.select()
        self.remove()
    def unsort(self):
        self.task.removeitemfromgroup(self._sense,sorting=False)
        self.refresh()
    def setcanary(self,canary):
        if canary.winfo_exists():
            self.canary=canary
        else:
            log.error("Not setting non-existant canary {}; ".format(canary))
    def getsenseofnode(self,node):
        if isinstance(node,lift.Example): #direct descendance
            self._sense=node.sense
        elif isinstance(node.parent,lift.Entry): #sibling of sense
            self._sense=node.parent.sense
    def getexample(self,**kwargs):
        kwargs=exampletype(**kwargs)
        n,node=self.exs.getexample(self.group,**kwargs)
        self.updatecount(n)
        self.hasexample=node is not None
        """now example.audiofileURL"""
        if node is not None and node.audiofileisthere:
            self._filenameURL=node.audiofileURL
        else:
            self._filenameURL=None
        if node is None:
            log.error(f"SortGroupButtonFrame.getexample returned None for {self.group} {kwargs}")
            return
        self.getsenseofnode(node)
        self._text=node.formatted(program['taskchooser'].analang,
                                    program['taskchooser'].glosslangs,
                                    ftype=program['params'].ftype(),
                                    frame=program['toneframes'].get(
                                                program['params'].check()),
                                    showtonegroup=self.kwargs['showtonegroup'])
        self._illustration=scaleimageifthere(node.sense)
        return 1
    def makebuttons(self):
        # log.info(f"Making buttons with {self.kwargs=}")
        self._playable=False
        if self.kwargs['label']:
            self.labelbutton()
        elif self.kwargs['playable'] and self._sense is not None and self._filenameURL:
                self.playbutton()
                self._playable=True
        else:
            self.selectbutton()
        if self.kwargs['unsortable']:
            self.unsortbutton()
        self.makerefreshbutton()
        if (self.check and self.kwargs.get('show_check') and
            not isinstance(self.parent, SortGlyphGroupButtonFrame)):
            self.make_check_button()
    """buttons"""
    def labelbutton(self):
        self.label=ui.Label(self, text=self._text,
                    column=1, row=0, sticky='ew',
                    **self.buttonkwargs()
                    )
        if hasattr(self,'_illustration'):
            self.label['image']=self._illustration
            self.label['compound']='left'
    def playbutton(self):
        self.player=sound.SoundFilePlayer(self._filenameURL,self.task.pyaudio,
                                            program['settings'].soundsettings)
        b=ui.Button(self, text=self._text,
                    cmd=self.player.play,
                    column=1, row=0,
                    sticky='nesw',
                    **self.buttonkwargs())
        if hasattr(self,'_illustration'):
            b['image']=self._illustration
            b['compound']='left'
        bttext=_("Click to hear this utterance")
        if program['praat']:
            bttext+='; '+_("right click to open in praat")
            b.bind('<Button-3>',
                    lambda x: executables.praatopen(program, self._filenameURL))
        bt=ui.ToolTip(b,bttext)
    def selectbutton(self):
        if self.kwargs.get('on_select'):
            cmd=self.kwargs['on_select']
        elif self.kwargs['labelizeonselect']:
            cmd=self.selectnlabelize
        elif self.kwargs['remove_on_click']:
            cmd=self.selectnremove
        else:
            cmd=self.selectnsortnext
        b=self.button_select=ui.Button(self, text=self._text, cmd=cmd,
                    column=1, row=0, sticky='ew',
                    **self.buttonkwargs())
        if hasattr(self,'_illustration'):
            b['image']=self._illustration
            b['compound']='left'
        bt=ui.ToolTip(b,_("Pick this group ({})").format(self.group))
    def refresh(self):
        log.info("SGBF refresh called")
        self.kwargs['renew']=True
        self.kwargs['alwaysrefreshable']=True
        self.getexample(**self.kwargs)
        self.again()
    def updatecount(self,n=None):
        # log.info("Updating count for group {} (n={})".format(self.group,n))
        if n is not None:
            self._n.set(n) #for cases where this is already calculated
        else:
            nodes=self.exs.getexamples(self.group,**self.kwargs)
            # log.info("Found {} examples: {}".format(len(nodes),nodes))
            self._n.set(len(nodes))
        if hasattr(self,'refreshbutton'):
            self.refresh_button_state()
    def refresh_button_state(self):
        if not self.refreshbutton.winfo_exists():
            return
        if self._n.get() <2:
            self.refreshbutton['state'] = 'disabled'
        else:
            self.refreshbutton['state'] = 'normal'
    def makerefreshbutton(self):
        tinyfontkwargs=self.buttonkwargs()
        del tinyfontkwargs['font'] #so it will fit in the circle
        tinyfontkwargs['borderwidth']=self.refresh_borderwidth
        # if isinstance(self.parent,SortGlyphGroupButtonFrame):
        #     tinyfontkwargs['column']=3 # for glyph groups
        self.refreshbutton=ui.Button(self, image=self.theme.photo['change'], #🔃 not in tck
                        cmd=self.refresh,
                        text=self._n,
                        compound='center',
                        # column=0,
                        row=0,
                        sticky='nsew',
                        **tinyfontkwargs)
        self.refreshbutton.bind('<ButtonRelease-3>',self.backup)
        bct=ui.ToolTip(self.refreshbutton,
                        text=_("Change example word; Right click to back up"))
        self.refresh_button_state()
    def make_check_button(self):
        ui.Label(self, text=self.check, column=self.ncolumns())
    def unsortbutton(self):
        t=_("<= resort *this* *word*")
        usbkwargs=self.buttonkwargs()
        usbkwargs['wraplength']=usbkwargs['wraplength']*2/3
        b_unsort=ui.Button(self,text = t,
                            cmd=self.unsort,
                            column=2,row=0,#padx=50,
                            **{**usbkwargs, 'font':'default'}
                            )
    def buttonkwargs(self):
        """This is a method to allow pulling these args after updating kwargs"""
        bkwargs=self.kwargs.copy()
        for arg in self.unbuttonargs+[i
                                    for i in ['ps', 'profile', 'ftype', 'check']
                                    if i in bkwargs]:
            del bkwargs[arg]
        bkwargs['relief']=self.button_relief
        bkwargs['borderwidth']=self.button_borderwidth
        return bkwargs #only the kwargs appropriate for buttons
    def __init__(self, parent, task, **kwargs):
        # log.info("Initializing buttons for group {}".format(group))
        self.exs=program['examples']
        self.task=task #the task/check OR the scrollingframe! use self.check.task
        try:
            self.code=program['alphabet'].verificationcode(**kwargs)
        except:
            pass #don't worry if that info isn't all there
        self.group=kwargs.pop('group') #must be here
        self.check=kwargs.get('check',None) #must be here for glyphs only
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
        # self.canary=kwargs.pop('canary',None)
        # kwargs['borderwidth']=kwargs.pop('borderwidth',5)
        # kwargs['refreshcount']=kwargs.pop('refreshcount',-1)+1
        # kwargs['sticky']=kwargs.pop('sticky',"ew")
        frameargs={} #kwargs.copy()
        self.button_relief='raised' #groove,ridge,sunken,raised,flat
        # self.button_borderwidth=7 # width of relief
        self.button_borderwidth=15 # width of relief
        self.refresh_borderwidth=10 # width of relief
        frameargs={f:kwargs.pop(f,self.defaults.get(f,0))
                    for f in self.frameargs}
        for arg in self.unbuttonargs:
            kwargs[arg]=kwargs.pop(arg,False)
        if kwargs['playable']:
            kwargs['wsoundfile']=True
        #set this for buttons:
        if program['settings'].lowverticalspace:
            # log.info("using lowverticalspace for SortGroupButtonFrame")
            max=0
        else:
            max=15
        for k in ['ipady','ipadx','pady','padx']: #outer pad in defaults
            kwargs[k]=kwargs.pop('b'+k,self.defaults.get(k,max))
        self.kwargs=kwargs
        self._var=kwargs.pop('var',ui.BooleanVar())
        self._n=ui.IntVar()
        super().__init__(parent, **frameargs)
        if self.getexample(**kwargs):
            self.makebuttons()
class SortGlyphGroupButtonFrame(ui.Frame,_GroupButtonFrame):
    def make_sgbf(self, item, **kwargs):
        """kwargs[group] (group from item) is not self.group (macro name)."""
        kwargs.update(program['alphabet'].parse_verificationcode(item))
        kwargs['column']=1 #specify other attributes shared with frame here
        kwargs['row']=0
        kwargs['gridwait']=True
        kwargs['var']=self.var()
        log.info(f"Ready to build SortGroupButtonFrame with {kwargs=}")
        self.items.append(SortGroupButtonFrame(self, self.task, **kwargs))
        log.info(f"Built SGBF for {item} ({self.items=})")
        if self.items[-1].hasexample:
            # log.info(f"Built {kwargs['group']} SortGroupButtonFrame with ex")
            self.hasexample=True
        else:
            # log.info(f"No {kwargs['group']} SortGroupButtonFrame ex; removing")
            self.items=self.items[:-1]
    def next_item(self,event=None):
        # log.info(f"next_item ({self.shown_index=})")
        if self.shown_index == len(self.items)-1: #loop back on last
            self.show_one()
        else:
            self.show_one(self.shown_index+1)
    def prev_item(self,event=None):
        # log.info(f"prev_item ({self.shown_index=})")
        if self.shown_index == 0: #loop back on first
            self.show_one(len(self.items)-1)
        else:
            self.show_one(self.shown_index-1)
    def show_one(self,index=0):
        for item in [i for i in self.items if self.items.index(i) != index]:
            item.grid_remove()
        self.items[index].grid()
        log.info(f"Showing item with {self.items[index].code}")
        # "={self.items[index].group}")
        self.check_label['text']=self.items[index].check
        self.shown_index=index
    def make_refresh(self):
        self.refresh_frame=ui.Frame(self,col=2,border=True,sticky='nsew')
        # self.check_label=ui.Label(self.refresh_frame, text='', #to show check
        #                             anchor='s',col=0)
        self.check_label=ui.Button(self.refresh_frame, text='', #to show check
                                        # textvariable=self._n,
                                        cmd=self.next_item,
                                        image=self.theme.photo['change'],
                                        borderwidth=5,
                                        compound='top',
                                        col=1)
        for w in [self.refresh_frame,self.check_label]:#,self.group_count]:
            ui.ToolTip(w,'click to change group')
            # w.bind('<Button-1>', self.next_item)
            w.bind('<Button-3>', self.prev_item, add='+') #nothing on n=1
    def updatecount(self,n=None):
        # log.info("Updating count for group {} (n={})".format(self.group,n))
        if n is not None:
            self._n.set(n) #for cases where this is already calculated
        else:
            # nodes=self.exs.getexamples(self.group)
            # log.info("Found {} examples: {}".format(len(nodes),nodes))
            self._n.set(len(self.items))
        if self._n.get() <2:
            self.check_label['state'] = 'disabled'
    def setcanary(self,canary):
        """This is needed because these buttons are reused across all words
        being sorted. so each word to sort is the canary, in tern, and it is
        reset with each new presented word/group to sort.
        """
        if canary.winfo_exists():
            for i in self.items:
                i.canary=canary #select on group button select
            self.canary=canary #select on glyph button select
        else:
            log.error("Not setting non-existant canary {}; ".format(canary))
    def __init__(self, parent, task, **kwargs):
        self.task=task #the task/check OR the scrollingframe! use self.check.task
        self.group=kwargs.pop('group')
        # self.check=kwargs.get('check')
        log.info(f"Building SortGlyphGroupButtonFrame for {self.group}")
        # self.showtonegroup=kwargs.pop('showtonegroup',False)
        # self.alwaysrefreshable=kwargs.pop('alwaysrefreshable',False)
        # self.remove_on_click=kwargs.pop('remove_on_click',False) #compatability
        kwargs=ui.GridinGridded.promotegridbkwargs(True,**kwargs)
        # kwargs=ui.GridinGridded.remove_gridbkwargs(True,**kwargs)
        # for k in ['padx', 'pady']:
        #     frameargs[k]=kwargs.get(k,1)
        # kwargs['border']=10
        frameargs={f:kwargs.pop(f,self.defaults.get(f,0))
                    for f in self.frameargs}
        super().__init__(parent, **frameargs)
        if self.group not in program['alphabet'].glyph_members():
            ui.Label(self,text=f"group ‘{self.group}’ isn't in glyphs! "
                    f"({list(program['alphabet'].glyph_members())})",
                    c=0)
            self.hasexample=True #make this error visible
            return
        self.glyph_label_frame=ui.Frame(self, col=0)
        if kwargs.get('on_select'):
            cmd=kwargs['on_select']
        else:
            cmd=self.selectnsortnext
        self.glyph_label=ui.Button(self.glyph_label_frame,
                                cmd=cmd,
                                text='?' if self.group.isdigit() else self.group,
                                font='readbig',
                                borderwidth=5,
                                width=5, col=0)
        self.grid_columnconfigure(0, weight=1, uniform="label")
        self.items=list()
        self.hasexample=False #make sure at least one of these has an example
        self._var=ui.BooleanVar()
        self._n=ui.IntVar()
        self.make_refresh()
        for item in program['alphabet'].glyph_members()[self.group]:
            log.info(f"Making Glyph member {item} button")
            self.make_sgbf(item, **kwargs)
        if self.items:
            self.updatecount()
            self.show_one()
        log.info(f"Built SortGlyphGroupButtonFrame for {self.group}")
class ImageFrame(ui.Frame):
    def getimage(self,reload=False):
        specifiedurl=False
        compiled=False
        if self.url and file.exists(self.url):
            i=self.url
            specifiedurl=True
        elif isinstance(self.sense,lift.Sense):
            if (hasattr(self.sense,'image')
                    and isinstance(self.sense.image,ui.Image)
                    and not reload):
                # log.info("Found Image, using")
                image=self.sense.image
                compiled=True
                self.hasimage=True
            else:
                i=getimagelocationURI(self.sense)
        # lift.prettyprint(self.sense.illustration)
        if not compiled:
            try:
                # log.info("trying to make image {}".format(i))
                image=ui.Image(i)
                self.hasimage=True
                # log.info("Image OK: {}".format(img))
            except tkinter.TclError as e:
                if ('value for "-file" missing' not in e.args[0] and
                        "couldn't recognize data in image file" not in e.args[0]):
                    log.info("ui.Image error: {}".format(e))
                image=self.theme.photo['NoImage']
                self.hasimage=False
                # log.info("Image null: {}".format(img))
            if not specifiedurl and self.hasimage: #don't assign "no image"
                self.sense.image=image
        # log.info("Image: {} ({})".format(image,type(image)))
        scaledimage(image,pixels=self.pixels)
        self.image=image.scaled #Imageframe.image = sense.image.scaled
    def pluralframe(self):
        ui.Label(self,text='',image=self.image,
                compound='bottom',
                sticky='e',
                ipadx=10,
                row=0,column=0)
        ui.Label(self,text='',image=self.image,
                compound='bottom',
                sticky='w',
                ipadx=10,
                row=0,column=1)
    def imperativeframe(self):
        try:
            image1=program['theme'].photo['Order!']
            scaledimage(image,pixels=300) #300 wide
            image2=self.image
            # log.info("image1.scaled: {} ({})".format(image1.scaled,type(image1.scaled)))
            # log.info("image2: {} ({})".format(image2,type(image2)))
            image1.scaled.paste(image2)
            bgl=ui.Label(verb,text='',image=image1.scaled,
                compound='center',
                sticky='ew',
                row=0,column=0)
        except:
            ui.Label(self,text='!',image=self.image,
                compound='left',sticky='ew',font='title',
                row=0,column=0)
    def citationframe(self):
        l=ui.Label(self,text='',image=self.image,
            compound='center',sticky='ew',
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
        if self.exitFlag.istrue():
            return
        self.labels['v']['text']=_("Version: {}".format(program['version']))
        self.labels['v2']['text']=_(
                            f"updated to {program['repo'].lastcommitdate()} " f"({program['repo'].lastcommitdaterelative()})")
        self.labels['textl']['text']=_("Your dictionary database is loading...")
        self.labels['text']['text']=_(f"{program['name']} is a computer "
                "program that accelerates community-based language development "
                "by facilitating the sorting of a beginning dictionary "
                "by vowels, consonants and tone. (more in help:about)")
        self.labels['titletext']['text']=(_("{name} Dictionary and Orthography "
                                        "Checker").format(name=program['name']))
        self.update_idletasks()
    def draw(self):
        # self.update_idletasks()
        # self.update()
        self.deiconify() #show after placement
    def progress(self,value):
        if self.exitFlag.istrue():
            return
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
                        'v2':ui.Label(self.frame, text='', anchor='c',padx=25,
                        row=2,column=0,sticky='we'
                        ),
                        'photo':ui.Label(self.frame, image='transparent',text='',
                        row=3,column=0,sticky='we'
                        ),
                        'textl':ui.Label(self.frame, text='', padx=50,
                                    wraplength=int(self.winfo_screenwidth()/2),
                                    row=4,column=0,sticky='we'
                                    ),
                        'text':ui.Label(self.frame, text='', padx=50,
                                    wraplength=int(self.winfo_screenwidth()/2),
                                    font='italic',
                                    row=6,column=0,sticky='we'
                                    )
                    }
        self.maketexts()
        self.title(self.labels['titletext']['text'])
        self.progressbar=ui.Progressbar(self.frame,
                                orient='horizontal',
                                mode='determinate', #or 'indeterminate'
                                row=5,column=0)
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
    def checkgroupsbysense(self):
        """outputs dictionary keyed to [sense][location]=group"""
        self.sensedict={}
        for sense in self.senses:
            self.sensedict[sense]={}
            for check in self.checks:
                group=sense.tonevaluebyframe(check)
                if group: #store location:group by sense
                    self.sensedict[sense][check]=[group]
        # log.info("Done collecting groups by location for each sense.")
        return self.sensedict
    def sorttoUFs(self):
        """Input is a dict keyed by location, valued with location:group dicts
        Returns groups by location:value correspondences."""
        # This is the key analytical step that moves us from a collection of
        # surface forms (each pronunciation group in a given context) to the
        # underlying form (which behaves the same as others in its group,
        # across all contexts).
        if not hasattr(self,'sensedict'):
            log.error("You have to run checkgroupsbysense first")
            return
        unnamed={}
        # Collect all unique combinations of location:group pairings.
        # log.info("sensedict: {}".format(self.sensedict))
        for sense in self.sensedict:
            #sort into groups by dict values (combinations location:group pairs)
            k=str(self.sensedict[sense])
            try:
                unnamed[k].append(sense)
            except KeyError:
                unnamed[k]=[sense]
        # log.info("Done collecting combinations of groups values "
        #         "by location: {}".format(unnamed))
        # self.groups={}
        self.valuesbygroupcheck={}
        self.sensesbygroup={}
        ks=list(unnamed) #keep sorting order
        for k in ks:
            x=ks.index(k)+1
            name=self.ps+'_'+self.profile+'_'+str(x)
            self.valuesbygroupcheck[name]=ofromstr(k) #return str to dict
            self.sensesbygroup[name]=unnamed[k]
            for sense in unnamed[k]:
                sense.uftonevalue(name)
        # log.info("Done adding senses to groups.")
        # return self.groups
    def tonegroupsbyUFcheckfromLIFT(self):
        #returns dictionary keyed by [group][location]=groupvalue
        values=self.valuesbygroupcheck={}
        # Collect check:value correspondences, by sense
        for group in self.sensesbygroup:
            values[group]={}
            for sense in self.sensesbygroup[group]:
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
    def sensesbyUFsfromLIFT(self):
        """This returns a dict of {UFtonegroup:[senses]}"""
        log.debug(_("Looking for sensids by UF tone groups for {}-{}").format(
                    self.profile, self.ps
                    ))
        self.sensesbygroup={g:[s for s in self.senses if s.uftonevalue() == g]
                            for g in set([s.uftonevalue() for s in self.senses])
                            if g}
        return self.sensesbygroup
    def donoUFanalysis(self):
        log.info("Reading tone group analysis from UF tone fields")
        self.sensesbyUFsfromLIFT() # > self.sensesbygroup
        self.tonegroupsbyUFcheckfromLIFT() # > self.valuesbygroupcheck
        self.doanyway()
    def do(self):
        log.info("Starting tone group analysis from lift examples")
        self.checkgroupsbysense() # > self.sensedict
        self.sorttoUFs() # > self.sensesbygroup and self.valuesbygroupcheck
        program['db'].write()
        self.doanyway()
        program['status'].last('analysis',update=True)
        program['status'].store()
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
        self.senses=program['slices'].senses(ps=self.ps,profile=self.profile)
    def __init__(self, **kwargs):
        super(Analysis, self).__init__()
        self.analang=program['db'].analang
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
            # log.info("There seem to be no ad hoc {} groups.".format(self._ps))
            pass #don't care
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
            self.renewsenses()
        elif ps:
            log.error(_("You asked to change to ps {}, which isn't in the list "
                        "of pss: {}").format(ps,pss))
        elif hasattr(self,'_ps'):
            return self._ps
        else:
            log.error("You asked for the ps, but I do't have any (pss: {})"
                        "".format(pss))
    def profiles(self,ps=None):
        """This returns profiles for either a specified ps or the current one"""
        if not ps:
            ps=self.ps()
        if ps and ps in self._profiles:
            # log.info("returning profiles: {}".format(self._profiles[ps]))
            return self._profiles[ps]
        else:
            return []
    def profile(self,profile=None):
        if profile and profile in self.profiles(self._ps):
            self._profile=profile
            self.renewsenses()
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
    def inslice(self,s=None,**kwargs):
        senses=self.senses(**kwargs) #if no kwargs, returns current
        if not s:
            return set(senses)
        elif isinstance(s,lift.Sense):
            return set(senses).intersection(set([s]))
        elif hasattr(s, '__iter__'):
            return set(senses).intersection(set(s))
        else:
            log.error("Not sure what happened here!")
    def senses(self,**kwargs): #ps=None,profile=None,
        if not kwargs:
            return self._senses #this is always the current slice
        ps=kwargs.get('ps',self._ps)
        profile=kwargs.get('profile',self._profile)
        if ps in self._profilesbysense and profile in self._profilesbysense[ps]:
            return self._profilesbysense[ps][profile]
            # return list(self._profilesbysense[ps][profile]) #specified slice
        else:
            return []
    def makesensesbyps(self):
        """These are not distinguished by profile, just ps"""
        self._sensesbyps={}
        for ps in self._profilesbysense:
            self._sensesbyps[ps]=[]
            for prof in self._profilesbysense[ps]:
                self._sensesbyps[ps]+=self._profilesbysense[ps][prof]
    def renewsenses(self):
        self._senses=[]
        try:
            self._senses+=list(self._profilesbysense[self._ps][self._profile])
        except KeyError:
            log.info("assuming {} is an ad hoc profile.".format(self._profile))
        try:
            self._senses+=list(self._adhoc[self._ps][self._profile])
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
        """This iterates across self._adhoc to provide counts for each
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
        e=_("Found {} valid data slices: {}").format(len(wcounts),self.keys())
        e+='\n'+_("Invalid entries found: {}/{}").format(profilecountInvalid,
                                                        sum(self.values(),
                                                        profilecountInvalid))
        if program['db'].analangs and not len(wcounts):
            e+='\n'+_("This may be a problem with your analysis language: {}"
                    "").format(program['db'].analang)
            e+='\n'+_("Or a problem with your database.")
            ErrorNotice(e,title=_("Data Problem!"),wait=True)
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
        self.maxpss=None #This only seems to be used in pspriority
        self._adhoc=adhoc
        self.analang=program['db'].analang
        if self.analang != profilesbysense['analang']:
            log.error(f"Problem: {self.analang=} != {profilesbysense['analang']=}")
            raise
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
        self.makesensesbyps()
        """This will be redone, but should be done now, too."""
        self.makeprofileok() #so the next won't fail
        self.renewsenses()
        program['settings'].settingsobjects() #should do this more; can be redone!
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
        #showing type here is just as good, since it's an object in any case
        #printing the object fails if it is a window that hasn't inited yet
        if task:
            log.info("Setting task {}".format(type(task)))
            self._task=task
        else:
            # log.info("Returning task {}".format(type(self._task)))
            return self._task
    def profiletosort(self):
        """Return whether there is a profile that has been unsorted"""
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
        return nextprofile
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
        return nextcheck
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
    def allcheckswCVdata(self):
        return list(set([i for j in [program['status'][cvt][ps][profile]
                                    for cvt in program['status']
                                    if cvt != 'T'
                                    for ps in program['status'][cvt]
                                    for profile in program['status'][cvt][ps]
                                    if ps in program['status'][cvt]
                                    ]
                                for i in j]))
    def allcheckswdata(self, **kwargs): #needs cvt and ps
        cvt=kwargs.get('cvt',program['params'].cvt())
        ps=kwargs.get('ps',program['slices'].ps())
        return list(set([i for j in [program['status'][cvt][ps][profile]
                                    for profile in program['status'][cvt][ps]
                                    ]
                            for i in j
                        ]))
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
        if not checks:
            return cs
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
    def all_groups_verified_anywhere(self):
        d=self.dict()
        return {cvt:set([i
                        for ps in d[cvt]
                        for profile in d[cvt][ps]
                        for check in d[cvt][ps][profile]
                        for i in d[cvt][ps][profile][check]['done']
                        if i not in ['NA']])
                for cvt in d
                }
    def all_groups_verified_for_cvt(self):
        return self.all_groups_verified_anywhere()[program['params'].cvt()]
    def groups(self,g=None, **kwargs):
        # log.info("groups kwargs: {}".format(kwargs))
        if kwargs.get('all_for_cvt'): #in this case, nothing else is relevant
            return self.all_groups_verified_for_cvt()
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
            #done is always a subset of groupsː
            sn['done']=sorted(set(sn['done'])&set(sn['groups']))
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
    def sensestosort(self):
        return getattr(self,'_sensestosort',False) #always return, even w/o attr
    def sensessorted(self):
        return self._sensessorted
    def renewsensestosort(self,todo,done):
        """This takes arguments to remove and rebuild these lists"""
        """todo and done should be lists of senses"""
        """this takes as arguments lists extracted from LIFT by the check"""
        if not hasattr(self,'_sensessorted'):
            self._sensessorted=[]
        if not hasattr(self,'_sensestosort'):
            self._sensestosort=[]
        self._sensessorted.clear()
        self._sensessorted.extend(done)
        self._sensestosort.clear()
        self._sensestosort.extend(todo)
    def marksensesorted(self,sense,**kwargs):
        self._sensessorted.append(sense)
        if sense in self._sensestosort:
            self._sensestosort.remove(sense)
        if not self._sensestosort:
            self.tosort(False,**kwargs) #this marks current, unless specified
            # log.info("Tosort now {} (marksensesorted)".format(self.tosort()))
    def marksensetosort(self,sense,**kwargs):
        self._sensestosort.append(sense)
        if sense in self._sensessorted:
            self._sensessorted.remove(sense)
        self.tosort(True,**kwargs) #this marks current, unless specified
        # log.info("Tosort now {} (marksensetosort)".format(self.tosort()))
    def store(self):
        """This will just store to file; reading will come from check."""
        log.info("Saving status dict to file")
        program['settings'].storesettingsfile('status')
        return
        config=ConfigParser()
        config.read(self._filename,encoding='utf-8')
        if config != self:
            log.info("config: {}".format(config.keys()))
            log.info("self: {}".format(self.keys()))
        for k in self:
            config[k]=indenteddict(self[k]) #getattr(o,s)
        with open(self._filename, 'w', encoding='utf-8') as file:
            config.write(file)
    def dict(self): #needed?
        return {k:self[k] for k in self}
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
    def clear_all_groups(self):
        """don't do this except when reloading! This only removes sort groups,
        which can be rebuilt from lift. Leave other stuff alone!"""
        ts=list(self)
        for t in ts:
            pss=list(self[t])
            for ps in pss:
                profiles=list(self[t][ps]) #actual, not theoretical
                for profile in profiles:
                    checks=list(self[t][ps][profile]) #actual, not theoretical
                    for check in checks:
                        node=self[t][ps][profile][check]
                        if 'groups' in node:
                            node['groups'] = []
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
                        elif 'groups' in node and node['groups'] == []:
                            del self[t][ps][profile][check]
                        elif 'done' in node and 'groups' in node:
                            node['done']=sorted(set(node['done']
                                                    )&set(node['groups']))
                        elif 'done' in node: #i.e., w/o groups
                            node['done']=[]
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
        if cvt in ['T','S']:
            """This depends on ps and program['toneframes']"""
            ps=kwargs.get('ps',program['slices'].ps())
            if ps not in self._checksdict[cvt]:
                self._checks=[] #there may be none defined
            else:
                self._checks=self._checksdict[cvt][ps]
        else:
            profile=kwargs.get('profile',program['slices'].profile())
            # log.info(f"Using profile {profile} for updatechecksbycvt")
            if not profile:
                return #if no data yet, no segmental checks, either
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
        profile=kwargs.get('profile',program['slices'].profile() if 'slices' in program else '')
        if cvt == 'T':
            for ps in program['slices'].pss():
                if ps in program['toneframes']:
                    self._checksdict[cvt][ps]=list(program['toneframes'][ps])
        elif cvt == 'S':
            for ps in program['slices'].pss():
                self._checksdict[cvt][ps]=program['params'].cvchecknamesdict().keys()
        elif profile:
            """This depends on profile only"""
            n=profile.count(cvt)
            # log.debug('Found {} instances of {} in {}'.format(n,cvt,profile))
            self._checksdict[cvt][profile]=list()
            for i in range(n): # get max checks and lesser
                if i+1 >6:
                    c=0
                    for ps in program['slices'].pss():
                        if (profile,ps) in program['slices']:
                            c+=program['slices'][(profile,ps)]
                    log.info(_("Not doing checks with more than 6 "
                            f"consonants or vowels; there are {i+1} " f"{program['params'].cvtdict()[cvt]['pl']} "
                            f"in {profile}); "
                            "If you need that, please let me know. "
                            f"({c} word(s).)"))
                    continue
                """This is a list of (code, name) tuples"""
                syltuples=program['params']._checknames[cvt][i+1] #range+1 = syl
                self._checksdict[cvt][profile].extend([t[0] for t in syltuples])
                # log.info("Check codes to date: {}".format(
                #                                 self._checksdict[cvt][profile]
                #                                         ))
            self._checksdict[cvt][profile].sort(key=len,reverse=True)
        else:
            log.info("Not Tone and no profile; not returning a check")
        # log.info(f"{self._checksdict[cvt][profile]=}")
    def node(self,**kwargs):
        """This will fail if fed None values"""
        kwargs=self.checkslicetypecurrent(**kwargs)
        if None in [kwargs['cvt'],kwargs['ps'],kwargs['profile'],
                                                            kwargs['check']]:
            log.error("None found in {} kwarg ({})".format([i for i in kwargs
                                                            if not kwargs[i]],
                                                            kwargs))
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
        """This returns whether or not (bool) there are items yet to sort
        in this group of sort items.
        """
        kwargs=self.checkslicetypecurrent(**kwargs) # current value defaults
        sn=self.node(**kwargs)
        ok=[None,True,False]
        if v not in ok:
            log.error("Tosort value ({}) invalid: OK values: {}".format(v,ok))
        self._tosortbool=sn['tosort']
        if v is not None:
            self._tosortbool=sn['tosort']=v
        return self._tosortbool
    def verified(self,g=None,**kwargs):
        sn=self.node(**kwargs)
        self._verified=sn['done']
        if g is not None:
            log.info(f"verified replacing {sn['done']} with {g} for {kwargs}")
            self._verified=sn['done']=g
        return self._verified
    def isdistinguished(self,other_group,**kwargs):
        g=kwargs.get('group') 
        for t in itertools.permutations((g,other_group)):
            if t in self.distinguished(**kwargs):
                return True
    def distinguished(self,**kwargs):
        sn=self.node(**kwargs)
        if 'distinguished' not in sn or sn['distinguished'] == {}:
            sn['distinguished']=set()
        return sn['distinguished']
    def distinguish(self,g, **kwargs):
        self.distinguished(**kwargs).add(g)
    def undistinguish(self,g, **kwargs):
        self.distinguished(**kwargs).remove(g)
    def undistinguish_any_with(self,g, **kwargs):
        # log.info(f"calling self.undistinguish_any_with with {kwargs=}")
        # log.info(f"{self.distinguished(**kwargs)=}")
        for j in [i for i in self.distinguished(**kwargs) if g in i]:
            self.undistinguish(j,**kwargs)
    def recorded(self,g=None,**kwargs):
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
        self.build()
        n=self.node()
        # log.info(f"verification update: {group=} as {verified=} in {n['done']}")
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
        return getattr(self,'_group',None)# this needs to be booleanable
    def renamegroup(self,j,k,**kwargs):
        # log.info(f"Status renaming {j}>{k} for {kwargs=}")
        sn=self.node(**kwargs)
        if j in sn['done']:
            sn['done'][sn['done'].index(j)]=k
        if j in sn['groups']:
            sn['groups'][sn['groups'].index(j)]=k
        if j in sn['recorded']:
            sn['recorded'][sn['recorded'].index(j)]=k
        if 'distinguished' in sn:
            for i in [l for l in sn['distinguished'] if j in l]:
                sn['distinguished'].remove(i)
                sn['distinguished'].add(tuple(k if m == j else m for m in i))
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
        if update and not kwargs.get('check'): #write cross-check tone analysis
            for kwargs['check'] in self.checks():
                self.last(task,update,**kwargs)
            return
        sn=self.node(**kwargs)
        if 'last' not in sn:
            sn['last']={}
        if update:
            sn['last'][task]=str(now())
        if kwargs.get('write'):
            self.store()
        if task in sn['last']:
            return sn['last'][task]
    def isanalysisOK(self,**kwargs):
        if 'check' in kwargs:
            a=self.last('analysis',**kwargs)
            s=self.last('sort',**kwargs)
            j=self.last('joinUF',**kwargs)
        else:
            log.info("checking for an OK analysis across all checks")
            analysisl=[]
            sortl=[]
            ufjoinl=[]
            self.renewchecks()
            # log.info(f"Working on checks ‘{self.checks()}’")
            # log.info(f"Working on updatechecksbycvt ‘{self.updatechecksbycvt()}’")
            for check in self.updatechecksbycvt():
                log.info(f"Working on check ‘{check}’")
                analysisl.append(self.last('analysis',**{**kwargs,'check':check}))
                sortl.append(self.last('sort',**{**kwargs,'check':check}))
                ufjoinl.append(self.last('joinUF',**{**kwargs,'check':check}))
            log.info(f"Collected analysisl: {analysisl}")
            log.info(f"Collected sortl: {sortl}")
            log.info(f"Collected ufjoinl: {ufjoinl}")
            # These are stored on file as strings
            a=min([datetime.datetime.fromisoformat(i) for i in analysisl if i],
                                                                    default='')
            s=max([datetime.datetime.fromisoformat(i) for i in sortl if i],
                                                                    default='')
            j=max([datetime.datetime.fromisoformat(i) for i in ufjoinl if i],
                                                                    default='')
        log.info(f"{a}>{s}?")
        if a and s:
            ok=fixnaivedatetime(a)>fixnaivedatetime(s)
        elif a:
            ok=True # b/c analysis would be more recent than last sorting
        else:
            ok=False # w/o info, trigger reanalysis
        if ok and j and fixnaivedatetime(j) > fixnaivedatetime(a):
            joinsinceanalysis=True #show groups on all non-default reports
        else:
            joinsinceanalysis=False
        annalysisoknotice=_("Last analysis at {};\n"
                    "last join at {}\n"
                    "last sort at {}\n(analysisOK={})"
                    "").format(a,j,s,ok)
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
class CheckParameters(object):
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
    def cvtname(self,cvt=None,n='sg'):
        if not cvt:
            cvt=self.cvt() #this shouldn't necessarily set current cvt.
        return self._cvts[cvt][n]
    def check(self,check=None,unset=False):
        """This needs to change/clear subchecks"""
        if unset or check:
            log.info("Setting check {}".format(check))
            self._check=check
        elif not hasattr(self,'_check'):
            log.info("Making check attribute ({})".format(check))
            self._check=None
        # log.info("Returning check {}".format(self._check))
        return self._check
    def checkcodes_by_cvt(self):
        self._checkcodes_by_cvt={cvt:{code_tuple[0]
                    for nsyl,code_list in syl_dict.items()
                    for code_tuple in code_list
                    }
                for cvt,syl_dict in self._checknames.items()
                }
        log.info(f"{self._checkcodes_by_cvt=}")
    def cvt_of_check(self,check):
        for cvt,codes in self._checkcodes_by_cvt.items():
            # log.info(f"{cvt=},{codes=}")
            if check in codes:
                return cvt
    def cvcheckname(self,code=None):
        if self.cvt() == 'T':
            code='T'
        if not code:
            code=self.check()
        try:
            return _(self._cvchecknames[code])
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
        return self._cvchecknames
    def analang(self,analang=None):
        if analang:
            log.info(f"Setting analysis language as {analang} ({self})")
            self._analang=analang
        # log.info(f"Returning analysis language as {self._analang} ({self})")
        return self._analang
    def audiolang(self,audiolang=None):
        if audiolang:
            self._audiolang=audiolang
        if hasattr(self,'_audiolang'):
            return self._audiolang
    def ftype(self,ftype=None):
        if ftype:
            self._ftype=ftype
        elif not hasattr(self,'_ftype'):
            self._ftype='lc'
        return self._ftype
    def secondfield(self,ps):
        fields=program['settings'].secondformfield
        if ps in fields:
            return fields[ps]
    def nominalpsfield(self):
        return self.secondfield(program['settings'].nominalps)
    def verbalpsfield(self):
        return self.secondfield(program['settings'].verbalps)
    def __init__(self):
        program['params']=self
        """replaces setnamesall"""
        """replaces self.checknamesall"""
        super(CheckParameters, self).__init__()
        self._analang=program['db'].analang
        self._audiolang=program['db'].audiolang
        self._cvts={
                'V':{'sg':'Vowel','pl':'Vowels'},
                'C':{'sg':'Consonant','pl':'Consonants'},
                'CV':{'sg':'Consonant-Vowel combination',
                        'pl':'Consonant-Vowel combinations'},
                'VC':{'sg':'Vowel-Consonant combination',
                        'pl':'Vowel-Consonant combinations'},
                'T':{'sg':'Tone','pl':'Tones'},
                }
        self._checknames={
            'S':{ 1:[('lc', _("Whole Citation Word Syllable Profile")),
                ('lx', _("Whole Root Syllable Profile")),
                ('pl', _(f"Whole {self.nominalpsfield()} Word "
                            "Syllable Profile")),
                ('imp', _(f"Whole {self.verbalpsfield()} Word "
                            "Syllable Profile")),
                ]},
            'T':{
                1:[('T', _("Tone Melody"))]},
            'V':{
                1:[('V1', _("First Vowel"))],
                2:[
                    ('V1=V2', _("Same First Two Vowels")),
                    ('V1xV2', _("Correspondence of First Two Vowels")),
                    ('V2', _("Second Vowel"))
                    ],
                3:[
                    ('V1=V2=V3', _("Same First Three Vowels")),
                    ('V3', _("Third Vowel")),
                    ('V2=V3', _("Same Second and Third Vowels")),
                    ('V2xV3', _("Correspondence of Second and Third Vowels"))
                    ],
                4:[
                    ('V1=V2=V3=V4', _("Same First Four Vowels")),
                    ('V3=V4', _("Same Third and Fourth Vowels")),
                    ('V3xV4', _("Correspondence of Third and Fourth Vowels")),
                    ('V4', _("Fourth Vowel"))
                    ],
                5:[
                    ('V1=V2=V3=V4=V5', _("Same First Five Vowels")),
                    ('V5', _("Fifth Vowel"))
                    ],
                6:[
                    ('V1=V2=V3=V4=V5=V6', _("Same First Six Vowels")),
                    ('V6', _("Sixth Vowel"))
                    ]
                },
            'C':{
                1:[('C1', _("First/only Consonant"))],
                2:[
                    ('C2', _("Second Consonant")),
                    ('C1=C2',_("Same First/only Two Consonants")),
                    ('C1xC2', _("Correspondence of First/only Two Consonants"))
                    ],
                3:[
                    ('C2=C3',_("Same Second Two Consonants")),
                    ('C2xC3', _("Correspondence of Second Two Consonants")),
                    ('C3', _("Third Consonant")),
                    ('C1=C2=C3',_("Same First Three Consonants"))
                    ],
                4:[
                    ('C4', _("Fourth Consonant")),
                    ('C1=C2=C3=C4',_("Same First Four Consonants"))
                    ],
                5:[
                    ('C5', _("Fifth Consonant")),
                    ('C1=C2=C3=C4=C5',_("Same First Five Consonants"))
                    ],
                6:[
                    ('C6', _("Sixth Consonant")),
                    ('C1=C2=C3=C4=C5=C6',_("Same First Six Consonants"))
                    ]
                },
            'CV':{
                1:[
                    # ('#CV1', _("Word-initial CV")),
                    ('CxV1', _("Correspondence of first CV")),
                    # ('CV1', _("First/only CV)")
                    ],
                2:[
                    # ('CV2', _("Second CV")),
                    ('CxV2', _("Correspondence of second CV")),
                    ('CV1=CV2',_("Same First/only Two CVs")),
                    # ('CV2#', _("Word-final CV"))
                    ],
                3:[
                    ('CxV3', _("Correspondence of third CV")),
                    ('CV1=CV2=CV3',_("Same First/only Three CVs")),
                    ('CV3', _("Third CV"))
                    ],
                4:[
                    ('CV1=CV2=CV3=CV4',_("Same First/only Four CVs")),
                    ('CV4', ("Fourth CV"))
                    ],
                5:[
                    ('CV1=CV2=CV3=CV4=CV5',_("Same First/only Five CVs")),
                    ('CV5', _("Fifth CV"))
                    ],
                6:[
                    ('CV1=CV2=CV3=CV4=CV5=CV6',_("Same First/only Six CVs")),
                    ('CV6', _("Sixth CV"))
                    ]
                },
            'VC':{
                1:[
                    ('VxC1', _("Correspondence of first VC")),
                    ],
                2:[
                    ('VxC2', _("Correspondence of second VC")),
                    # ('VC1=VC2',_("Same First/only Two VCs")),
                    ],
                3:[
                    ('VxC3', _("Correspondence of third VC")),
                    # ('VC1=VC2=VC3',_("Same First/only Three VCs")),
                    # ('VC3', _("Third VC"))
                    ],
                4:[
                    ('CV1=CV2=CV3=CV4',_("Same First/only Four CVs")),
                    ('CV4', _("Fourth CV"))
                    ],
                5:[
                    ('CV1=CV2=CV3=CV4=CV5',_("Same First/only Five CVs")),
                    ('CV5', _("Fifth CV"))
                    ],
                6:[
                    ('CV1=CV2=CV3=CV4=CV5=CV6',_("Same First/only Six CVs")),
                    ('CV6', _("Sixth CV"))
                    ]
                },
        }
        self.cvchecknamesdict()
        self.checkcodes_by_cvt()
class ConfigParser(configparser.ConfigParser):
    def output(self):
        for k in self:
            if isinstance(self[k],str):
                log.info(f"Config {k}: {self[k]}")
            else:
                for j in self[k]:
                    log.info(f"Config {k}/{j}: {self[k][j]}")
    def write(self,*args,**kwargs):
        configparser.ConfigParser.write(self,*args,**kwargs,
                                            space_around_delimiters=False)
    def __init__(self):
        super(ConfigParser, self).__init__(
        converters={'list':list},
        delimiters=(' = ', ' : '),
        allow_no_value=True
        )
        self.optionxform=str
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
        if not text:
            log.error(_("ErrorNotice got no text?"))
            return
        log.error(f"ErrorNotice: “{text}”")
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
        parent=kwargs.get('parent',program.get('root',ui.Root()))
        # log.info("parent: {}".format(kwargs['parent']))
        title=kwargs.get('title',_("Error!"))
        wait=kwargs.get('wait')
        button=kwargs.get('button')
        image=kwargs.get('image')
        super(ErrorNotice, self).__init__(parent,title=title,exit=False)
        self.withdraw()
        self.parent.withdraw()
        self.title = title
        self.text = text
        l=ui.Label(self.frame, text=text,
                    image=image,
                    compound='left',
                    row=0, column=1,
                    columnspan=2,
                    ipadx=25)
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
        self.deiconify()
        if wait:
            self.wait_window(self)
        if self.exitFlag.istrue():
            return
        if not isinstance(self.parent,ui.Root):
            self.parent.deiconify()
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
            args=['add', str(file)]
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
        w=ui.Window(program['root'],title=_("Commit Confirm"),exit=False)
        text=_("Do you want to commit language data via {} now?"
                ).format(self.repotypename)+'\n'+diff[:300]
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
        args=['commit', '-m', 'Autocommit from AZT', file]
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
            args=['diff']
            if cached:
                args+=['--cached']
            args+=['--stat']
            return self.do(args)
        # log.info("{} diff returned {}".format(self.repotypename,r))
    def status(self):
        args=['status']
        log.info(self.do(args))
    def clonefromUSB(self,directory):
        log.info("Preparing to clone to {} from USB repo".format(directory))
        #this should be a pathlib object
        # log.info("Continuing to clone to {} from USB repo".format(directory))
        # this needs from-to args
        args=['clone', self.nonbareclonearg, self.url, str(directory)]
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
                args=['clone', self.bareclonearg, '.', directory] #this needs from-to
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
        args=['log']
        log.info(self.do(args))
    def commithashes(self,url=None):
        r=self.do(['log', '--format=%H'],url=url)
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
    def share(self,remotes=None):
        if not remotes:
            remotes=self.findpresentremotes() #do once
        if not remotes:
            log.info("Couldn't find a local drive to share with via {}; "
                    "giving up".format(self.repotypename))
            return
        r=self.commit() #should always before pulling, at least here
        if r:
            r=self.pull(remotes)
        if r:
            r=self.push(remotes)
        return r #ok if we don't track results for each
    def fetch(self,remotes=None):
        if not remotes:
            remotes=self.findpresentremotes() #do once
        for remote in remotes:
            if self.code == 'git':
                args=['fetch',remote]
            elif self.code == 'hg':
                args=['pull',remote]
            # log.info("Pulling: {}".format(args))
            r=self.do(args)
            # log.info("Pull return: {}".format(r))
        return r #if we want results for each, do this once for each
    def pull(self,remotes=None):
        if not remotes:
            remotes=self.findpresentremotes() #do once
        if not remotes:
            log.info(_("Couldn't find a local drive to pull from via {}; "
                    "giving up").format(self.repotypename))
            return
        for remote in remotes:
            if self.code == 'git':
                args=['pull',remote,self.branch]
            elif self.code == 'hg':
                args=['pull','-u',remote,self.branch]
            # log.info("Pulling: {}".format(args))
            r=self.do(args)
            # log.info("Pull return: {}".format(r))
        return r #if we want results for each, do this once for each
    def push(self,remotes=None,setupstream=False):
        if not remotes:
            remotes=self.findpresentremotes() #do once
        if not remotes:
            log.info(_("Couldn't find a local drive to push to via {}; "
                    "giving up").format(self.repotypename))
            return
        for remote in remotes:
            args=['push']
            if setupstream:
                args+=['--set-upstream']
            args+=[remote,self.branch+':'+self.branch] #don't push across branches
            r=self.do(args)
            if r and 'The current branch master has no upstream branch.' in r:
                r=self.push(remotes=[remote],
                            #always keep branch names aligned.
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
        if thatrepohashes and 'fatal: not a git repository' in thatrepohashes:
            return False
        if thatrepohashes and 'does not have any commits yet' in thatrepohashes:
            thatrepohashes=[]
        thisrepohashes=self.commithashes()
        # log.info(thisrepohashes)
        if thisrepohashes and 'fatal: not a git repository' in thisrepohashes:
            return False
        if thisrepohashes and 'does not have any commits yet' in thisrepohashes:
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
            log.info(_("Repository at {} looks empty, so I'm assuming you "
            "just initialized it").format(directory))
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
                program['taskchooser'].withdraw()
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
                if not program['Demo']:
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
        args=['root']
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
        iwascalledby=callerfn()
        # log.info("iwascalledby1 {}".format(iwascalledby))
        if (not hasattr(self,'branch') and
                    'init' not in args and
                    iwascalledby != 'isbare'): #This calls before branchname...
            # log.info("do args: {}".format(args))
            # log.info("branch: {}".format(self.branch))
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
        try:
            output=subprocess.check_output(cmd,
                                            stderr=subprocess.STDOUT,
                                            shell=False)
            # log.info("Command output: \n{}; {}".format(output,type(output)))
        except subprocess.CalledProcessError as e:
            output=stouttostr(e.output)
            # log.info("Error output: \n{}; {}".format(output,type(output)))
            if me and (iwascalledby in ['pull'] and
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
            if 'The current branch master has no upstream branch.' in output:
                log.info("iwascalledby {}, but don't have upstream."
                            "".format(iwascalledby))
                if iwascalledby not in ['push']:
                    try:
                        assert self.code == 'git' #don't give hg notices here
                        ErrorNotice(output)
                    except (RuntimeError,AssertionError):
                        log.info(output)
                return output
            if iwascalledby in ['pull']: #needed for logic and reporting
                return output
            if iwascalledby not in ['getusernameargs','log']:
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
                    assert iwascalledby not in ['fetch']
                    assert 'ot a git repository' not in output
                    assert 'unknown option' not in output
                    assert 'does not have any commits yet' not in output
                    assert 'error: No such remote ' not in output
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
        # log.info("iwascalledby2 {}".format(iwascalledby))
        if iwascalledby in ['commithashes', #never log these, even w/output
                            'lastcommitdate',
                            'lastcommitdaterelative'
                            ]:
            pass
        elif t and iwascalledby not in ['diff', #These give massive output!
                                        'getfiles',
                                        ]:
            log.info("{} {} {}: {}".format(self.repotypename,
                                            iwascalledby,args[1:],t))
        elif iwascalledby not in ['add', #these should log only w/output
                                    'commit',
                                    ]:
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
        title=_("Warning: {type} Executable Missing!").format(type=self.repotypename)
        text=_("You "
                # "seem to be working on a repository of data ({0}), "
                # "\nwhich may be tracked by {1}, "
                # "\nbut "
                "you don't seem to have the {} executable installed in "
                "your computer's PATH.").format(
                                                # self.url,
                                                self.repotypename)
        if self.repotypename == 'Mercurial':
             text+='\n'+_("(Mercurial is used by Chorus and languagedepot.org)")
             if not self.exists():
                 log.info(_("No {0} repo, nor {0} executable; moving on."
                            ).format(self.repotypename))
                 return
        w=ui.Window(program.get('root',ui.Root()),title=title)
        w.withdraw()
        if self.repotypename == 'Git':
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
        mtt=ui.ToolTip(m,_("Go to {url}").format(url=self.installpage))
        if self.thisos == 'Windows':
            clickable1=_("(e.g., in Windows, install *this* file),"
                        ).format(self.wexeurl)
            clickable2=_("or see all your options at {}."
                        ).format(self.wdownloadsurl)
            n=ui.Label(w.frame, text=clickable1, column=0, row=2)
            n.bind("<Button-1>", lambda e: openweburl(self.wexeurl))
            ntt=ui.ToolTip(n,_("download {url}").format(url=self.wexeurl))
            o=ui.Label(w.frame, text=clickable2, column=0, row=3)
            o.bind("<Button-1>", lambda e: openweburl(self.wdownloadsurl))
            mtt=ui.ToolTip(o,_("Go to {url}").format(url=self.wdownloadsurl))
        # button=(_("Restart Now"),sysrestart) #This should be in task/chooser
        text=_("After you install {}, you should restart."
                ).format(self.repotypename)
        if self.repotypename == 'Git':
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
        for key in ['Thing'+str(i) for i in range(1,20)]:
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
        # This reads from file, not git/hg
        if self.bare:
            repoheadfile=self.branchnamefile
        else:
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
            log.error(_("Problem finding branch name: {error}").format(error=e))
    def setdescription(self):
        self.description=_("language data")
    def populate(self):
        #this is done on normal __init__, or after an init later on.
        #These are things that need an actual repository there
        self.bare=bool(self.isbare())
        log.info("Repo {} is bare: {}".format(self.url,self.bare))
        self.remotenames=self.getremotenames()
        self.branchname() #This is needed for the following
        self.getusernameargs()
        self.getfiles()
        self.ignorecheck()
        try:
            log.info(_("{} repository object initialized on branch {} at {} "
                    "for {}, with {} files."
                    "").format(self.repotypename, self.branch, self.url,
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
        # self.thisos='Windows'
        if self.thisos == 'Linux':
            self.installpage=('https://github.com/kent-rasmussen/azt/blob/main/'
                                'docs/SIMPLEINSTALL_LINUX.md')
        elif self.thisos == 'Windows':
            self.installpage=('https://github.com/kent-rasmussen/azt/blob/main/'
                                'docs/SIMPLEINSTALL.md')
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
        self.wdownloadsurl='https://www.mercurial-scm.org/wiki/Download'
        self.wexename='Mercurial-6.0-x64.exe'
        self.wexeurl=('https://www.mercurial-scm.org/release/windows/{}'
                        ''.format(self.wexename))
        self.pwd='--cwd'
        self.lsfiles='files'
        self.argstogetusername=['config', 'ui.username']
        self.bareclonearg='-U'
        self.nonbareclonearg=''
        super(Mercurial, self).__init__(url)
        # These files are just ignored in git, but if Chorus put something
        # there, we want to know
        if hasattr(self,'files'):
            self.choruscheck()
        else:
            self=None
class Git(Repository):
    def stash(self):
        r=self.do(['stash'])
        return r
    def unstash(self):
        r=self.do(['stash', 'apply'])
        return r
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
                # '*lift.*',
                '*.lift*txt',
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
        # log.info("Running isbare")
        r=self.do(['config', 'core.bare'])
        # log.info("isbare returns {}".format(r))
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
        # git config branch.$branchname.mergeoptions '-X ignore-space-change'
    def lastcommitdate(self):
        args=['log', '-1', '--format=%cd']
        r=self.do(args)
        # log.info(r)
        return r
    def lastcommitdaterelative(self):
        args=['log', '-1', '--format=%ar']
        r=self.do(args)
        # log.info(r)
        return r
    def getremotenames(self):
        args=['remote']
        r=self.do(args)
        if r:
            r=r.split('\n')
        else:
            r=[] # This should always be iterable
        log.info("Using these remotes: {}".format(r))
        return r
    def getremotenameurl(self,remotename):
        args=['remote', 'get-url', remotename]
        r=self.do(args)
        if 'error: No such remote ' not in r:
            return r
    def __init__(self, url):
        self.code='git'
        self.branchnamefile='HEAD'
        self.wdownloadsurl='https://git-scm.com/download/win'
        self.wexename='Git-2.33.0.2-64-bit.exe'
        self.wexeurl=('https://github.com/git-for-windows/git/releases/'
                        'download/v2.33.0.windows.2/{}').format(self.wexename)
        self.pwd='-C'
        self.lsfiles='ls-files'
        self.argstogetusername=['config', '--get', 'user.name']
        self.argstogetuseremail=['config', '--get', 'user.email']
        self.bareclonearg='--bare'
        self.nonbareclonearg=''
        super(Git, self).__init__(url)
class GitReadOnly(Git):
    def exewarning(self):
        pass #don't worry about it for this one
    def share(self,event=None):
        """This method should only ever pull or push, depending on who
        is doing it"""
        # this will mostly operate on all present sources (internet and USB),
        # reporting failures as appropriate. I hope users will be OK with that
        r={}
        if me: #no one else should push changes
            method=Repository.push
            # This doesn't mind if there is no USB:
            remotes=self.localremotes() #don't publish to internet this way
            log.info("remotes: {}".format(remotes))
            for remote in remotes: #iterate here to keep results
                r[remote+'/'+self.branch]=method(self,remotes=[remote])
            # self.stash()
            self.switchbranches()
            for remote in remotes: #iterate here to keep results
                r[remote+'/'+self.branch]=method(self,remotes=[remote])
            self.switchbranches()
            # self.unstash()
        else:
            method=Repository.pull
            #make sure we at least try the github remote:
            # User is asked for a USB if nothing is found here:
            remotes=self.findpresentremotes(firsttry=False) #don't ask
            homeurl=program['url']+'.git'
            remotes.extend([homeurl])
            log.info("remotes: {}".format(remotes))
            self.fetch(remotes)
            for remote in remotes:
                r[remote+'/'+self.branch]=method(self,remotes=[remote])
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
    def switchbranches(self):
        if self.branch == 'main':
            self.testversion()
        else:
            self.reverttomain()
    def reverttomain(self,event=None):
        r=self.checkout('main')
        """need to also
        git reset --hard origin/main
        """
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
    def __init__(self, parent, msg=None, title=None):
        """Can't test for widget/window if the attribute hasn't been assigned,"
        but the attribute is still there after window has been killed, so we
        need to test for both."""
        if title is None:
            title=(_("Result Window"))
        super().__init__(parent,title=title)
        self.lift()
        if msg:
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
    def __init__(self,**kwargs):
        for k in kwargs:
            setattr(self,k,kwargs[k])
"""These are non-method utilities I'm actually using."""
def fixnaivedatetime(d):
    """Assume naive was made wrt UTC (as has been my practice)"""
    return d.replace(tzinfo=datetime.timezone.utc)
def now():
    try:
        # Python 3.11+
        return datetime.datetime.now(datetime.UTC)#.isoformat() adds T
    except AttributeError as e:
        # Python <=3.11
        return datetime.datetime.now(datetime.timezone.utc)#.isoformat()
def nowruntime():
    #this returns a delta!
    try:
        # Python 3.11+
        return datetime.datetime.now(datetime.UTC)-program['start_time']
    except AttributeError as e:
        # Python <=3.11
        return datetime.datetime.utcnow()
        return datetime.datetime.utcnow()-program['start_time']
def logfinished(start=program['start_time'],msg=None):
    run_time=nowruntime()
    if type(start) is datetime.datetime: #only work with deltas
        start-=program['start_time']
    if msg:
        msg=str(msg)+' '
    else:
        msg=''
    try:
        m, s = divmod((run_time-start).total_seconds(), 60)
        text=_("Finished {msg}at {now} ({m:1.0f}m, {s:2.3f}s)").format(
            msg=msg, now=now(), m=m, s=s)
    except AttributeError:
        text=_("Finished {msg}at {now}, after {duration} seconds").format(
            msg=msg, now=now(), duration=run_time-start)
    log.info(text)
    return text
def interfacelang(lang=None,magic=False):
    global i18n
    global _
    """Attention: for this to work, _ has to be defined globally (here, not in
    a class or module.) So I'm getting the language setting in the class, then
    calling the module (imported globally) from here."""
    for l in i18n:
        try:
            _
            if i18n[l] == _.__self__:
                curlang=l
                magic=True
                break #i.e., if it is already set up correctly
        except NameError:
            curlang=None
            log.debug("_ doesn't look defined yet")
            break
    """Diagnostics of questionable value, with Magic above?"""
    try:
        if _.__module__ == 'gettext':
            # log.debug("Magic: {}".format(_.__module__))
            magic=True
        else:
            log.debug("Magic seems to be installed, but not gettext: {}"
            "".format(_.__module__))
    except NameError:
        log.debug("Looks like translation magic isn't defined yet; making")
    if lang:
        log.info(f"Asked to set lang {lang} with curlang {curlang}")
    if not lang and not curlang: #deduce, but don't override current setting.
        # log.info("checking for a local setting")
        code=file.uilang()
        if not code:
            # log.debug("local settings don't seem to have returned any "
            #         f"results ({code})")
            code=getlangfromlocale()
            if not code:
                log.debug("locale.getlocale doesn't seem to have "
                "returned any results: "
                f"{locale.getlocale()} (OS: {platform.system()})"
                "Using English user interface")
                log.debug("locale.getdefaultlocale output for "
                            f"comparison: {locale.getdefaultlocale()}")
                code='en' #I think loc=None normally means English on macOS
        if code in i18n:
            # log.info("returning {} (of {})".format(code,list(i18n)))
            lang=code
    if lang and lang != curlang and lang in i18n: # or not magic:
        log.debug("Setting Interface language: {}".format(lang))
        i18n[lang].install()
        file.uilang(lang)
        return lang
    return curlang
def getlangfromlocale():
    # log.debug("Looking for interface language in locale.")
    loc,enc=locale.getlocale()
    log.info("Found locale {}, encoding {}".format(loc,enc))
    if loc:
        code=loc.split('_')[0]
        if code not in i18n and code in ['English','Français','French']:
            if code == 'English':
                code='en'
            else:
                code='fr'
        # log.info("Using code {}".format(code))
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
def exampletype(**kwargs):
    if not kwargs:
        print("exampletype called without kwargs")
    for arg in ['wglosses']:
        kwargs[arg]=kwargs.get(arg,True)
    for arg in ['renew','wsoundfile']:
        kwargs[arg]=kwargs.get(arg,False)
    # log.info("Returning exampletype kwargs {}".format(kwargs))
    return kwargs
def checkslicetype(**kwargs):
    for arg in ['cvt','ps','profile','check']:
        kwargs[arg]=kwargs.get(arg,None)
    # log.info("Returning checkslicetype kwargs {}".format(kwargs))
    return kwargs
def grouptype(**kwargs):
    for arg in ['wsorted','tosort','toverify','tojoin','torecord','comparison',
                'todo'
                ]:
        kwargs[arg]=kwargs.get(arg,False)
    # log.info("Returning grouptype kwargs {}".format(kwargs))
    return kwargs
def ifone(l,nt=None):
    if l and not len(l)-1:
        return l[0]
def unlist(l,ignore=[None]):
    if l and isinstance(l[0],lift.et.Element):
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
        log.info(_('Sorry, something other than one list item found: {}'
                '\nDid you mean to use "othersOK=True"? Returning nothing!'
                '').format(l))
def t(element):
    if type(element) is str:
        return element
    elif element is None:
        return str(None)
    else:
        try:
            return element.text
        except:
            log.debug(_("Apparently you tried to pull text out of a non "
                        "element, and it's not a simple string, either: {}"
                        ).format(element))
def nonspace(x):
    """Return a space instead of None (for the GUI)"""
    if x is not None:
        return x
    else:
        return ' '
def nn(x,perline=False,oneperline=False,twoperline=False):
    """Don't print 'None' in the UI..."""
    if type(x) in (list, tuple, set):
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
        # log.info("working on {}".format(child))
        if hasattr(child,attr):
            # log.info("Found {} value for {} attr, setting {} value".format(
            #         getattr(child,attr),attr,getattr(self,attr)
            #         ))
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
def loadCAWL():
    stockCAWL=file.fullpathname('SILCAWL/SILCAWL.lift')
    if file.exists(stockCAWL):
        log.info("Found stock LIFT file: {}".format(stockCAWL))
    try:
        # cawldb=lift.Lift(str(stockCAWL))
        cawldb=lift.LiftXML(str(stockCAWL),tostrip=True)
        log.info("Parsed ET.")
        log.info("Got ET Root.")
    except lift.BadParseError as e:
        text=_("{} doesn't look like a well formed lift file; please "
                "try again. ({})").format(stockCAWL,e)
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
def scaledimage(image,pixels=150,scaleto='height'):
    image.scale(program['scale'],pixels=pixels,scaleto=scaleto)
def getimagelocationURI(sense):
    i=sense.illustrationvalue()
    for d in [program['settings'].imagesdir,program['settings'].directory]:
        if i and d:
            di=file.getdiredurl(d,i)
            if file.exists(di):
                return di
def compilesenseimage(sense):
    """This needs to capture ui.Image errors like this:
    except tkinter.TclError as e:
        if ('value for "-file" missing' not in e.args[0] and
                "couldn't recognize data in image file" not in e.args[0]):
            log.info("ui.Image error: {}".format(e))
    """
    uri=sense.illustrationURI()
    if uri and file.exists(uri):
        sense.image=ui.Image(uri)
    else:
        sense.image=None
def scale_image(image,pixels=65,scaleto='height'):
    return image.scale(program['scale'],pixels=pixels,scaleto=scaleto)
def scaleimageifthere(sense,pixels=65,scaleto='height'):
    if not getattr(sense,'image',False) or not isinstance(sense.image,ui.Image):
        try:
            compilesenseimage(sense)
        except tkinter.TclError as e:
            if ('value for "-file" missing' not in e.args[0] and
                    "couldn't recognize data in image file" not in e.args[0]):
                log.info("ui.Image error: {}".format(e))
    if sense.image:
        return scale_image(sense.image,pixels=pixels,scaleto=scaleto)
def pathseparate(path):
    os=platform.system()
    if os == 'Windows':
        sep=';'
    elif os == 'Linux':
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
        #subprocess.check_output(['echo',"%PATH%"], **spargs)
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
        log.info(_("Search for {exe} on {os} failed: {error}").format(exe=exe, os=os, error=e))
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
    if (exe == 'praat' and program[exe]
            and not exceptiononload
            and not praatversioncheck()):
        findexecutable('sendpraat') #only ask if it would be useful
    # os.environ['PATH'] += os.pathsep + os.path.join(os.getcwd(), 'node')
def sysexecutableversion():
    # args=[program['python'], '--version']
    args=[sys.executable, '--version']
    return stouttostr(subprocess.check_output(args, shell=False))
def praatversioncheck():
    def parseversion(x):
        return x.split()[1]
    praatvargs=[program['praat'], '--version']
    try:
        versionraw=subprocess.check_output(praatvargs, shell=False)
        #These lines could be used to see how a praat is outputting on a computer, where neither utf-8 nor uft-16.
        # for encoding in ['utf-8', 'utf-16', sys.stdout.encoding]:
        #     for errortag in ['backslashreplace','strict','ignore', 'replace']:
        #         try:
        #             log.info("{},{}.strip: {}".format(encoding, errortag,
        #                         versionraw.decode(encoding, errortag).strip()))
        #             log.info("{},{}: {}".format(encoding, errortag,
        #                         versionraw.decode(encoding, errortag)))
        #         except Exception as e:
        #             log.info("{},{} error".format(encoding, errortag))
    except Exception as e:
        log.info("Problem with praat version ({}), assuming recent".format(e))
        return True
    try:
        if b'\x00' in versionraw:
            characters=versionraw.decode('utf-16')
        else:
            characters=stouttostr(versionraw)
        # log.info("characters={}".format(characters))
        out=version.Version(parseversion(characters))
    except Exception as e:
        log.info("Problem getting parseable praat version ({})".format(e))
        out=versionraw
    # This is the version at which we don't need sendpraat anymore
    # and where '--hide-picture' becomes available.
    justpraatversion=version.Version(parseversion(
                                            'Praat 6.2.04 (December 18 2021)'))
    log.info("Found Praat version {}".format(str(out)))
    if out>=justpraatversion:
        log.info("Praat version at or greater than {}".format(justpraatversion))
        return True
    else:
        log.info("Praat version less than {}".format(justpraatversion))
        return False
def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt): #ignore Ctrl-C
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    log.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
def openweburl(url):
    webbrowser.open_new(url)
def sysshutdown():
    logsetup.shutdown()
    sys.exit()
def sysrestart(event=None):
    osys=platform.system()
    log.info("Hard shutting down now.")
    logsetup.shutdown()
    if osys == 'Linux':
        # log.info(f"restarting with {sys.argv[0]}?={program['python']} ({sys.argv}?)")
        # log.info(f"os.execl({sys.executable}, {sys.argv})")
        os.execl(sys.executable, sys.executable, *sys.argv)
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
        #                                     'with executable'.format(e))
        #                         subprocess.run([sys.executable,*sys.argv])
        #                     except Exception as e:
        #                         log.info("Failed ({}); giving up.".format(e))
    sys.exit()
def internetconnectionproblemin(x):
    problems=[
            'No route to host',
            'unable to access',
            'Could not resolve host',
            'Could not read from remote repository.'
            ]
    for p in problems:
        if p in x:
            return True
def isinterneturl(x):
    u=['ssh:',
        'https:',
        'http:'
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
        'Already up to date.'
        ]
    if [i for i in u if i in x if x]:
            return True
def updateazt(event=None,**kwargs): #should only be parent, for errorroot
    def tryagain(event=None):
        updateazt(**kwargs)
    log.info(_("Updating {azt}").format(azt=program['name']))
    if 'git' in program:
        parent=kwargs.get('parent')
        if not parent or not parent.winfo_exists(): #take kwarg if there
            if 'chooser' in program:
                kwargs['parent']=program['taskchooser'].mainwindowis
            else:
                kwargs['parent']=program['root']
        log.info("parent title: {}".format(kwargs['parent'].title()))
        w=ui.Wait(msg=_("Updating {azt}").format(azt=program['name']), **kwargs)
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
    # log.info("root program: {}".format(program))
    try:
        root = ui.Root(program=program)
    except tkinter.TclError as e:
        log.info("Evidently you can't make a root window? ({})".format(e))
        return
    # log.info("Theme ipady: {}".format(program['theme'].ipady))
    # log.info("Theme ipadx: {}".format(program['theme'].ipadx))
    # log.info("Theme pady: {}".format(program['theme'].pady))
    # log.info("Theme padx: {}".format(program['theme'].padx))
    lastcommit=program['repo'].lastcommitdate()
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
    # root.className='azt'
    # root.winfo_class("azt")
    # log.info(root.winfo_class())
    """Translation starts here:"""
    t = TaskChooser(root) #TaskChooser MainApplication
    t.mainloop()
    sysshutdown()
def mainproblem():
    def reverttomain(event=None):
        program['repo'].reverttomain()
        sysrestart()
        revertb.destroy()
    def testversion(event=None):
        program['repo'].testversion()
        sysrestart()
        tryb.destroy()
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
    file=str(logsetup.writelzma())
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
    if False and exceptiononload:
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
    eurl+='&body='
    eurl+=_("Please replace this text with a description of what you just did.")
    eurl+='%0d%0a'
    eurl+=_("If the log below doesn't include the text '{}', or if it happened "
            "after a longer work session, please attach "
            "your compressed log file").format(
            'Traceback (most recent call last): ')+' ('+(file)+')'
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
                text=_("Check for \n{azt} \nupdates").format(azt=program['name']),
                cmd=lambda x=errorw:updateazt(parent=x),
                row=0,column=0,
                pady=20)
        if program['repo'].branch != 'main':
            revertb=ui.Button(f,
                    text=_("Revert to \nmain branch \nof {azt}").format(azt=program['name']),
                    cmd=reverttomain,
                    row=1,column=0,
                    pady=20)
        else:
            tryb=ui.Button(f,
                    text=_("Try \ntesting branch \nof {azt}").format(azt=program['name']),
                    cmd=testversion,
                    row=1,column=0,
                    pady=20)
    ui.Button(f,text=_("Restart \n{azt}").format(azt=program['name']),
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
        return 'class.'+name
if __name__ == '__main__':
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
    print("looking in",transdir)
    print("with contents",os.listdir(transdir))
    i18n={
        i.split('_')[0]:gettext.translation('azt', transdir, languages=[i],
                                    # fallback=True
                                    )
        for i in os.listdir(transdir)
        if os.path.isdir(os.path.join(transdir, i))
    }
    i18n['en'] = gettext.translation('azt', transdir, languages=['en_US'],
                                    fallback=True
                                    )
    # i18n['fr'] = gettext.translation('azt', transdir, languages=['fr_FR'])
    # i18n['zh'] = gettext.translation('azt', transdir, languages=['zh_CN'])
    # i18n['ar'] = gettext.translation('azt', transdir, languages=['ar_SA'])
    program['interfacelangs']={i for i in i18n}
    interfacelang() #translation works from here
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
    mt=program['repo'].lastcommitdate()
    mtrel=program['repo'].lastcommitdaterelative()
    log.info(_("Running {} v{}, updated {} ({})").format(
                                program['name'],program['version'],mtrel,mt))
    log.info(_("Called with arguments {} {} / {}").format(sys.executable,
                                                    sys.argv[0], sys.argv))
    log.info("Executed by {}".format(sysexecutableversion()))
    text=_("Working directory is {} on {}, running on {} cores"
            ).format(program['aztdir'],
                    program['hostname'],
                    multiprocessing.cpu_count())
    try:
        import psutil
    except ModuleNotFoundError:
        import py_modules
        py_modules.pip_install(['psutil'])
    finally:
        text+=_(", at {mhz}Mhz").format(mhz=collections.Counter(
                [i.current for i in psutil.cpu_freq(percpu=True)]).most_common(1)[0][0])
    log.info(text)
    log.info(_("Computer identifies as {platform}").format(platform=platform.uname()))
    log.info(_("Loglevel is {level}; started at {time}")
            .format(level=loglevel, time=datetime.datetime.now(datetime.UTC).isoformat()[:-7]+'Z'))
    #'sendpraat' now in 'praat', if useful
    for exe in ['praat','hg','ffmpeg','lame',
                # 'python','python3'
                ]:
        findexecutable(exe)
    # if program['python3']: #be sure we're using python v3
    #     program['python']=program.pop('python3')
    # if not program['python']:
    program['python']=sys.executable
    if 'testtask' in program and type(program['testtask']) is str:
        log.info("Converting string ‘{}’ to class".format(program['testtask']))
        program['testtask']=getattr(sys.modules[__name__],
                                        program['testtask'])
    # i18n['fub'] = gettext.azttranslation('azt', transdir, languages=['fub'])
    if exceptiononload and not me:
        pythonmodules()
        # sysrestart()
        mainproblem()
    elif exceptiononloadingmymodule:
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
        formsbycvs(C,V,'C1','V1')
    def timetest():
                times=1000000000
                out1=timeit.timeit(test, number=times)
                print(out1)
    #timetest() #see which C variable takes more computing time
