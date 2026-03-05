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
import openclipart
# import profiles #confirm obsolescence and remove!
# import setdefaults
import urls
from utilities import htmlfns, rx, executables
from backend import langtags,parser
import alphabet_chart
import alphabet_comparison
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
import sys
import os
import pprint #for settings and status files, etc.
import subprocess
import webbrowser

from backend.reporting.generator import Report
from backend.core.lexicon import Senses, Segments, WordCollection, Parse, Tone
from backend.core.sorting_engine import Sort
from frontend.ui_shell import HasMenus, Menus, StatusFrame, TaskDressing, TaskChooser
from backend.core.vcs import Repository, Mercurial, Git, GitReadOnly
from backend.core.analysis import Analysis, SliceDict, StatusDict, ExampleDict, DictbyLang, Entry
from backend.core.analysis_inputs import ToneFrames, CheckParameters, Glosslangs
from frontend.config.settings_ui import Settings
class LiftChooser(ui.Window,HasMenus):
    """this class allows the user to select a LIFT file, including options
    to start a new one (live or demo), or copy from USB."""
    def newfile_page(self):
        self._new_w=ui.Window(program.root,title=_("Start New LIFT Database"))
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
        program.root.unbind_all('<Button-1>')
        program.root.unbind_all('<Return>')
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
        self.l_codes=program.languages.get_codes(value)
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
            objs=[program.languages.get_obj(i) for i in self.l_codes]
            # log.info("get_obj OK")
            self.options=[i.full_display() for i in objs]
            # log.info("options OK")
            self.list_of_possibles.config(state='normal')
        # log.info(f"self.options: {self.options}")
        for i in self.options:
            self.list_of_possibles.insert("end", i)
        max_value_len=max([0]+[len(self.list_of_possibles.get(i))
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
            code=[k for k,v in program.languages.region_codes_names.items()
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
        lang_obj=program.languages.get_obj(self.iso)
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
            self.analang_obj=program.languages.get_obj(self.analang)
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
        self.wait=ui.Wait(parent=program.root,msg=_("Setting up new LIFT file now."))
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
        log.info(f"{mediadir=}")
        homedir=file.gethome() #don't ask where to put it
        # log.info("Media dir: {}; home: {}".format(mediadir,homedir))
        if not mediadir:
            log.info(f"No media directory {mediadir=} {homedir=}")
            return
        log.info(f"Media directory {mediadir=} {homedir=}")
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
                        "Analyze on the next page.").format(azt=program.name)
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
                dir=file.pathname_from_base_dir(sense.imgselectiondir)
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
        mgr=settings.SettingsManager(basename)
        mgr.project.set('glosslangs',['fr'])
        mgr.ui.set('buttoncolumns',2)
        log.info(f"Stored default settings for next run.")
    def makeCAWLdemo(self):
        title=_("Make a Demo LIFT Database")
        w=ui.Window(program.root,title=title)
        w.withdraw()
        w.mainwindow=False
        t=ui.Label(w.frame, text=title, font='title', row=0, column=0)
        inst=_("Which language would you like to study, in this demonstration "
                "of what {azt} can do?").format(azt=program.name)
        t=ui.Label(w.frame, text=inst, row=1, column=0, columnspan=2)
        self.cawldb=loadCAWL()
        # program.settings.langnames(self.cawldb.glosslangs)
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
        self.wait=ui.Wait(parent=program.root,
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
                        azt=program.name)
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
        if (hasattr(program.taskchooser,'splash') and
                    program.taskchooser.splash.winfo_exists()):
            program.taskchooser.splash.deiconify()
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
        self.parent=program.root
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
                                ).format(azt=program.name))]
        buttonFrame1=ui.ScrollingButtonFrame(self.frame,
                                optionlist=optionlist,
                                command=self.setfilename,
                                window=self,
                                column=0, row=1,
                                bsticky='ew',
                                sticky=''
                                )
        # make mediadir look for *.git
        ui.Label(self.frame, image=program.theme.photo['small'],
                text=text, font='title', compound='top',
                column=1, row=1, ipadx=20)
        # if hasattr(program.taskchooser,'splash'):
        try:
            program.taskchooser.splash.withdraw()
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
            if (self.name and program.testing
                            and hasattr(program, 'testlift') and program.testlift):
                # log.info("self.name0: {}".format(self.name))
                for f in self.name:
                    # log.info("f: {} ({})".format(f,program.testlift))
                    if program.testlift in f:
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
                            not program.root.exitFlag.istrue()):
            return
        if self.name and 'Demo' in str(self.name):
            program.Demo=True
            file.writefilename() #clear this to select next time
class FileParser(object):
    """This class parses the LIFT file, once we know which it is."""
    def loaddatabase(self,analang=None):
        try:
            #This program key will only be available after this finishes
            program.db=lift.LiftXML(str(self.name),analang)
        except lift.BadParseError:
            text=_("{filename} doesn't look like a well formed lift file; please "
                    "try again.").format(filename=self.name)
            log.info("'lift_url.py' removed.")
            if program.root.exitFlag.istrue():
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
        if not file.exists(program.db.backupfilename):
            program.db.write(program.db.backupfilename)
        else:
            print(_("Apparently we've run this before today; not backing "
            "up again."))
    def getwritingsystemsinfo(self):
        """This doesn't actually do anything yet, as we can't parse ldml."""
        program.db.languagecodes=program.db.analangs+program.db.glosslangs
        program.db.languagepaths=file.getlangnamepaths(self.name,
                                                    program.db.languagecodes)
    def __init__(self,name,analang=None):
        super(FileParser, self).__init__()
        self.name=name
        # splash.progress(15)
        self.loaddatabase(analang)
        # splash.progress(25)
        if program.root.exitFlag.istrue():
            return
        self.dailybackup()
        # splash.progress(35)
        # splash.progress(45)
        self.getwritingsystemsinfo()
        # self.dogrid()
        # back=ui.Button(self.outsideframe,text=_("Tasks"),cmd=program.taskchooser)
        # self.setfontsdefault()
class ExportData(ui.Window):
    """docstring for ExportData."""
    def taskicon(self):
        return program.theme.photo['USBdrive']
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
                'image':program.taskchooser.theme.photo['USBdrive'],
                'sticky':'ew',
                'tttext':tttext
                }
    def on_quit(self):
        ui.Window.on_quit(self)
        program.taskchooser.gettask()
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
        self.done_notice['text']=_("Done!\n(saved to {dir})").format(dir=self.export.save_dir)
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
                lift=program.db,
                analang=program.params.analang(),
                audiolang=program.params.audiolang(),
                audiodir=program.settings.audiodir,
                save_dir=program.settings.exportsdir,
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
                allchecks=program.status.allcheckswCVdata()
                self.button={c:ui.Button(self.button_frame,
                                        text=_("Just {check} data").format(check=c),
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
        title=(_("{azt} Data Export").format(azt=program.name))
        ui.Window.__init__(self,program.root, title=title)
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

    program.slices.senses() is sensitive to ps and profile, and pulls from syllableprofiles
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
            # Ensure we have sets for set operations
            glyphdict = {k: set(v) for k, v in glyphdict.items()}
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
            self._glyph_members={str(k):set(v) for k,v in gm.items()}
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
                ErrorNotice(_("item {item} conflicts with glyph {glyph}").format(item=i, glyph=y),wait=True)
                return
        for i in y:
            # log.info(f"Checking {i} for conflicts in {x} {d[x]}")
            if self.conflicting_items(i,x):
                ErrorNotice(_("item {item} conflicts with glyph {glyph}").format(item=i, glyph=x),wait=True)
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
            self._distinguished={k:set(v) for k,v in glyphs_distinguished.items()}
        elif glyphs_distinguished:
            log.error(_("{glyphs} provided, but without good keys").format(glyphs=glyphs_distinguished))
            raise
        return self._distinguished
    def distinguished_by_cvt(self,**kwargs):
        cvt=kwargs.get('cvt',program.params.cvt())
        return self.distinguished()[cvt]
    def distinguish(self, g, **kwargs):
        self.distinguished_by_cvt().add(g)
    def undistinguish(self, g, **kwargs):
        self.distinguished_by_cvt().discard(g) #don't throw error on remove
    def undistinguish_any_with(self,g):
        d=self.distinguished_by_cvt()
        for j in [i for i in d if g in i]:
            d.discard(j) #don't throw error on remove
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
        if glyph in ['NA']:
            ErrorNotice("Never mark NA glyphs done!")
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
    def cvt_of_glyph(self,glyph):
        """This should only be needed for glyphs that don't appear in glyphdict"""
        return {self.cvt_of_item(m) for m in self.glyph_members()[glyph]}
    def cvt_of_item(self,x):
        check=self.parse_verificationcode(x)['check']
        return program.params.cvt_of_check(check)
    def glyph_of_item(self,item):
        for glyph in self.glyph_members():
            if item in self.glyph_members()[glyph]:
                return glyph
    def conflict_code(self,code):
        return code.split('_')[:4]
    def verificationcode(self,**kwargs):
        ps=kwargs.get('ps',program.slices.ps())
        profile=kwargs.get('profile',program.slices.profile())
        ftype=kwargs.get('ftype',self.ftype)
        check=kwargs.get('check',program.params.check())
        group=kwargs.get('group',program.status.group())
        return '_'.join([ps,profile,ftype,check,group])
    def parse_verificationcode(self,code):
        ps,profile,ftype,check,group=code.split('_')
        return {'ps':ps,'profile':profile,'ftype':ftype,
                'check':check,'group':group}
    def refresh_items(self):
        self.items_present=set()
        k={'ftype':self.ftype} #ftype may need to iterate some day
        program.settings.reloadstatusdata() # culled here
        d=program.status.dict()
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
    def items_present_in_cvt(self,cvt):
        return [i for i in self.items_present if self.cvt_of_item(i) == cvt]
    def item_is_tomacrosort(self,item):
        """This is for one off checking, where a refresh is needed, as well as 
        confirmation what we're working with the correct cvt."""
        return item in self.renew_items_tomacrosort(self.cvt_of_item(item))
    def renew_items_tomacrosort(self,cvt): 
        self._itemsmacrosorted=set()
        self._itemstomacrosort=set()
        self.refresh_items()
        for item in self.items_present_in_cvt(cvt):
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
        if glyph in ['NA']: #just do this; no glyph for NA groups!
            self.mark_item_glyph(item,glyph) 
            return
        if glyph in self.conflicts and item in self.conflicts[glyph]:
            log.error("Not presorting, since it looks like we kicked this one out already.")
            return
        if glyph in self.unsorted and item in self.unsorted[glyph]:
            log.error("Not presorting, since it looks like we unsorted this one before.")
            return
        log.info(_("presort_item moving {item} into ‘{glyph}’").format(item=item, glyph=glyph))
        if not glyph.isdigit() and not self.conflicting_items(item,glyph):
            self.mark_item_glyph(item,glyph) #This should never produce conflicts
    def have_only_distinguished_items(self,x,y):
        log.info(_("Running have_only_distinguished_items on {x} and {y}").format(x=x, y=y))
        gm=self.glyph_members()
        for i in gm[x]:
            for j in gm[y]:
                if (self.conflict_code(i) != self.conflict_code(j) or
                            not program.status.isdistinguished(
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
        """This doesn't currently update SortGlyphGroupButtonFrame, but should"""
        conflicts=self.conflicting_items(item,glyph)
        if glyph in self.conflicts:
            recurring_conflicts=set(conflicts) & self.conflicts[glyph]
            self.conflicts[glyph]|=set(conflicts)
        else:
            recurring_conflicts=set()
            self.conflicts[glyph]=set(conflicts)
        if conflicts:
            if recurring_conflicts:
                text='\n'+_("This is the second time I've removed this item recently; "
                "so I'm going to ask you to consider joining them now.")
            else:
                text=''
            ErrorNotice(_("Removing {items} from ‘{glyph}’ to make room for {new}{text}"
                        ).format(items=conflicts,glyph=glyph,new=item,text=text),
                                wait=True)
        for i in conflicts:
            self.remove_item_from_glyph(i)
        return recurring_conflicts
    def mark_item_glyph(self,item,glyph):#maybe move to Alphabet Sort
        if self.parse_verificationcode(item)['group'] in ['NA'] and glyph not in ['NA']:
            ErrorNotice("Never mark NA sort groups other than in NA glyph!")
        self.rm_glyph_member(item) # in case elsewhere
        recurring_conflicts=self.remove_conflicting_items(item,glyph) #other group from same check
        self.add_glyph_member(item,glyph)
        self.mark_item_macrosorted(item)
        if item in self.glyph_members()[glyph]:
            log.info(_("mark_item_glyph added ‘{item}’ to ‘{glyph}’").format(item=item, glyph=glyph))
        else:
            log.info(_("mark_item_glyph failed to add ‘{item}’ to ‘{glyph}’").format(item=item, glyph=glyph))
            # log.info(f"{self.glyph_members()=}")
        return recurring_conflicts
    def remove_item_from_glyph(self,item,glyph=None):
        try:
            self.unsorted[glyph].add(item)
        except KeyError:
            self.unsorted[glyph]={item}
        self.rm_glyph_member(item,glyph) # in case elsewhere
        self.cull_glyphdict() #without knowing glyph or cvt
        self.mark_item_tomacrosort(item)
    def update_symbols(self):
        """I need to rethink this method entirely. How to make sure all symbols
        are available to the alphabet chart?
        """
        order=program.settings.alpha_order()
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
                            if self.cvt_of_item(i) == program.params.cvt()]
                ]
    def save_settings(self):
        program.settings.storesettingsfile(setting='alphabet')
    def __init__(self, **kwargs):
        program.alphabet=self
        self.ftype=program.params.ftype()
        program.settings.settingsobjects() #should do this more; can be redone!
        # self.renew_items_tomacrosort() #if needed, run then, with cvt
        self.save_settings()
        self.conflicts={} #keep track of what has been kicked out of a group before
        self.unsorted={}
class AlphabetChart(alphabet_chart.OrderAlphabet):
    my_settings=[
                    'exids',
                    # 'order',
                    'ncolumns','chart_title',
                    'copyright',
                    'pagesize'
                ]+Alphabet.my_settings#?
    def taskicon(self):
        return program.theme.photo['alpha_icon']
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
            getattr(program.settings,'alpha_'+k)(value)
        program.settings.storesettingsfile(setting='alphabet')
    def __init__(self, parent, **kwargs):
        self.program=program
        super().__init__(parent)
        self.mainwindow=False #don't exit on close
class AlphabetComparisonPages(alphabet_comparison.PageSetup):
    my_settings=[
                    'comparison_exids',
                    # 'order',
                    # 'ncolumns','chart_title',
                    'pagesize'
                ]
    def taskicon(self):
        return program.theme.photo['iconTranscribeV']
    def tooltip(self):
        return _("This task helps you compare alphabet letters with example words "
            "and pictures to represent each letter.")
    def tasktitle(self):
        return _("Alphabet Comparison Pages")
    def save_settings(self):
        for k in self.my_settings: #defined in module
            value=getattr(self,k)
            if isinstance(value,ui.Variable):
                value=value.get()
                log.info(_("found ‘{key}’ ui.Variable: {value}").format(key=k, value=value))
            else:
                log.info(_("Didn't find ‘{key}’ ui.Variable: {value}").format(key=k, value=value))
            getattr(program.settings,'alpha_'+k)(value)
        program.settings.storesettingsfile(setting='alphabet')
    def __init__(self, parent, **kwargs):
        self.program=program
        super().__init__(parent)
        self.mainwindow=False #don't exit on close
class Sound(object):
    """This holds all the Sound methods, mostly for playing."""
    settings_attrs=['fs', 'sample_format',
                    'audio_card_out']
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
        if not hasattr(program.settings,'soundsettings'):
            log.info("Making new soundsettings object")
            program.settings.soundsettings=sound.SoundSettings(self.pyaudio,
                        analang_obj=program.languages.get_obj(self.analang)
                        )
    def loadsoundsettings(self):
        self.makesoundsettings()
        program.settings.loadsettingsfile(setting='soundsettings')
        program.soundsettings=program.settings.soundsettings
        if program.hostname == 'karlap' and (
                        'cache_dir' not in program.soundsettings.asr_kwargs
                        ):
            program.soundsettings.asr_kwargs[
                                            'cache_dir']='/media/kentr/hfcache'
    def storesoundsettings(self):
        program.settings.storesettingsfile(setting='soundsettings')
    def quittask(self):
        self.soundsettingswindow.destroy()
        program.taskchooser.gettask()
        self.on_quit()
    def soundsettingscheck(self):
        if not hasattr(program.settings,'soundsettings'):
            self.loadsoundsettings()
    def missingsoundattr(self):
        # log.info(dir(program.settings.soundsettings))
        ss=program.settings.soundsettings
        for s in self.settings_attrs:
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
        program.settings.soundsettingsok=True
    def soundcheck(self):
        #just make sure settings are there
        self.soundsettingscheck()
        self.soundsettings=program.settings.soundsettings
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
        if hasattr(super(), 'setcontext'):
            super().setcontext(context)
        self.context.menuitem(_("Sound settings"),self._configure_sound)
        self.analang=program.db.analang
    def __init__(self,):
        self.audiodir=program.settings.audiodir
        self.audiolang=program.params.audiolang()
        self.program=program #make available to sound_ui
        self.soundcheck()
class Record(Sound): #TaskDressing
    """This holds all the Sound methods specific for Recording."""
    settings_attrs=['audio_card_in']+Sound.settings_attrs
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
        ps=program.slices.ps()
        profile=program.slices.profile()
        count=program.slices.count()
        text=_("Record {profile} {ps} Words: click ‘Record’, talk, "
                "and release ({count} words)").format(profile=profile,ps=ps,
                                                count=count)
        log.info(text)
        instr=ui.Label(self.runwindow.frame, anchor='w',text=text)
        instr.grid(row=0,column=0,sticky='w')
        senses=program.slices.senses(ps=ps,profile=profile)
        if not senses: #i.e., no profile analysis yet
            senses=program.db.senses
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
        if justone or not program.slices.valid():
            self.showentryformstorecordpage()
        else:
            #store for later
            ps=program.slices.ps()
            profile=program.slices.profile()
            for psprofile in program.slices.valid(): #self.profilecountsValid:
                if self.runwindow.exitFlag.istrue():
                    return 1
                program.slices.ps(psprofile[1])
                program.slices.profile(psprofile[0])
                nextb=ui.Button(self.runwindow,text=_("Next Group"),
                                        cmd=self.runwindow.resetframe) # .frame.destroy
                nextb.grid(row=0,column=1,sticky='ne')
                self.showentryformstorecordpage()
            #return to initial
            program.slices.ps(ps)
            program.slices.profile(profile)
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
        if (getattr(program.settings, 'entriestoshow', None) is None) and (senses is None):
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
            senses=program.settings.entriestoshow
        for sense in senses:
            log.debug("Working on {} with skip: {}".format(sense.id,
                                                    self.runwindow.frame.skip))
            examples=list(sense.examples.values())
            if examples == []:
                log.debug(_("No examples! Add some, then come back."))
                continue
            if ((self.runwindow.frame.skip == True) and
                (lift.atleastoneexamplehaslangformmissing(examples,
                                    program.settings.audiolang) == False)):
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
                    lift.examplehaslangform(example,program.settings.audiolang) == True):
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
            program.status.nextprofile()
            self.runwindow.on_quit()
            self.showtonegroupexs()
        if (not(hasattr(self,'examplespergrouptorecord')) or
            (type(self.examplespergrouptorecord) is not int)):
            self.examplespergrouptorecord=100
            program.settings.storesettingsfile()
        self.makeanalysis()
        self.analysis.donoUFanalysis()
        torecord=self.analysis.sensesbygroup
        ntorecord=len(torecord) #number of groups
        nexs=len([k for i in torecord for j in torecord[i] for k in j])
        nslice=program.slices.count()
        log.info(_("Found {analyzed} analyzed of {total} examples in slice").format(analyzed=nexs, total=nslice))
        skip=False
        if ntorecord == 0:
            log.error(_("How did we get no UR tone groups? {profile}-{ps}"
                    "\nHave you run the tone report recently?"
                    "\nDoing that for you now...").format(
                            profile=program.slices.profile(),
                            ps=program.slices.ps()
                                                         ))
            self.analysis.do()
            self.showtonegroupexs()
            return
        batch={}
        # log.info(f"program.db.sensedict ({len(program.db.sensedict)}): "
        #         f"{program.db.sensedict}")
        for i in range(self.examplespergrouptorecord):
            batch[i]=[]
            for ufgroup in torecord:
                print(i,len(torecord[ufgroup]),ufgroup,torecord[ufgroup])
                if len(torecord[ufgroup]) > i: #no done piles.
                    # sense=[program.db.sensedict[torecord[ufgroup][i]]] #list of one
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
        # This depends on self.analang and program.slices.profile; otherwise, it
        # could be moved to a FieldParent method
        """This should generate possible filenames, with preferred (current
        schema) last, as that will be used if none are found."""
        log.info(_("Looking for file names for {node} ({tag})").format(node=node, tag=node.tag))
        ps=program.slices.ps()
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
        profile=program.slices.profile()
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
        form=node.textvaluebylang(self.analang)
        if not form:
            log.error(_("filenameoptions: no {ana} analang in "
                "{id}! (OK if recording first; "
                "forms: {forms})").format(ana=self.analang,
                id=node.sense.id,
                forms=node.textvaluedict()))
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
                node.textvaluebylang(lang=program.params.audiolang(),value=f)
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
class Transcription(object):
    def _configure_transcription(self,event=None):
        # sound_ui.ASRModelSelectionWindow(self)
        pass # Placeholder for whatever user was adding
    def setcontext(self,context=None):
        if hasattr(super(), 'setcontext'):
            super().setcontext(context)
        self.context.menuitem(_("Transcription settings"),
                                    self._configure_transcription)
    def __init__(self):
        pass
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
        instructions2=(_("click on the best option(s) above"),
                        _("correct the consonants and vowels below."))
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
        self.instructions2['text']='\n'.join(instructions2)
        if self.transcription_tone_var.get():
            self.wordframe.toneFrame['text']=self.transcription_tone_var.get()
        else:
            self.wordframe.toneFrame['text']=''
    def draft_entry(self,repo,value,*args):
        # This just fills in the visible field. Dictionary may be
        # overwritten on confirmation later
        # This is only called when a user clicks on a button, not
        # automatically, so it should always overwrite the entry field
        program.soundsettings.tally_asr_repo(repo)
        self.var.set(value)
        self.update_idletasks()
        program.settings.storesettingsfile(setting='soundsettings')
        log.info(program.soundsettings.asr_repo_tally())
    def store_phonetic(self,*args):
        #Need to fix this; format isn't correct
        self.entry.fieldvalue(self.ftype,
                        program.db.phoneticlangname(machine=True),
                        value=self.transcription_ipa_var.get().split('\n')[0]
                        )
    def store_tone(self,*args):
        self.entry.fieldvalue(self.ftype,
                        program.db.tonelangname(machine=True),
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
        self.ftype=program.params.ftype('lx') #lift.Entry.citationformnodeofentry
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
        self.ftype=program.params.ftype('lc') #lift.Entry.citationformnodeofentry
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
        self.ftype=program.params.ftype('lc') #lift.Entry.citationformnodeofentry
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
        self.ftype=program.params.ftype('pl')
        TaskDressing.__init__(self,parent)
        WordCollection.__init__(self,parent)
        if not program.settings.secondformfieldsOK():
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
        self.ftype=program.params.ftype('imp')
        TaskDressing.__init__(self,parent)
        WordCollection.__init__(self,parent)
        if not program.settings.secondformfieldsOK():
            ErrorNotice(_("To collect Imperative forms, you must first "
                            "define which fields should contain those forms"),
                            wait=True)
            self.shutdowntask()
            return
        log.info("Initializing {}".format(self.tasktitle()))
        #Status frame is 0,0
        # self.nodetag='citation' #lift.Entry.citationformnodeofentry
        self.getwords()
class ParseWords(Parse,TaskDressing):
    def taskicon(self):
        return program.theme.photo['iconWord']
    def tooltip(self):
        return _("This task will help you parse your citation forms, "
                "automatically and with confirmation.")
    def dobuttonkwargs(self):
        fn=self.getparses
        text=_("Parse!")
        tttext=_("{azt} tries to do as much as possible automatically, and "
                "according to the level you have set for confirmation."
                ).format(azt=program.name)
        return {'text':text,
                'fn':fn,
                # column=0,
                'font':'title',
                'compound':'bottom', #image bottom, left, right, or top of text
                'image':program.theme.photo['Word'],
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
        return program.theme.photo['iconWord']
    def tooltip(self):
        return _("This task helps you collect and parse words.")
    def dobuttonkwargs(self):
        if program.taskchooser.cawlmissing:
            fn=self.addCAWLentries
            text=_("Add remaining CAWL entries")
            tttext=_("This will add entries from the Comparative African "
                    "Wordlist (CAWL) which aren't already in your database "
                    "(you are missing {count} CAWL tags). If the appropriate "
                    "glosses are found in your database, CAWL tags will be "
                    "merged with those entries."
                    "\nDepending on the number of entries, this may take "
                    "awhile.").format(count=len(program.taskchooser.cawlmissing))
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
                'image':program.theme.photo['Word'],
                'sticky':'ew',
                'tttext':tttext
                }
    def tasktitle(self):
        return _("Add and Parse Words") # for Citation Forms
    def __init__(self, parent):
        log.info("Initializing {}".format(self.tasktitle()))
        self.ftype=program.params.ftype('lc') #always correct?
        # self.nodetag='citation'
        TaskDressing.__init__(self,parent)
        Parse.__init__(self,parent)
        WordCollection.__init__(self,parent)
        program.taskchooser.withdraw()
        fn=self.getwords()#?
class WordCollectnParsewRecordings(Parse,WordCollectionwRecordings,TaskDressing):
    """This task collects words, from the SIL CAWL, or one by one.
    First in citation form, then pl or imperativewith Parse"""
    def taskicon(self):
        return program.theme.photo['iconWordRec']
    def tooltip(self):
        return _("This task helps you collect and parse words by recording "
                "them, with an automatic draft.")
    def dobuttonkwargs(self):
        if program.taskchooser.cawlmissing:
            fn=self.addCAWLentries
            text=_("Add remaining CAWL entries")
            tttext=_("This will add entries from the Comparative African "
                    "Wordlist (CAWL) which aren't already in your database "
                    "(you are missing {} CAWL tags). If the appropriate "
                    "glosses are found in your database, CAWL tags will be "
                    "merged with those entries."
                    "\nDepending on the number of entries, this may take "
                    "awhile.").format(count=len(program.taskchooser.cawlmissing))
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
                'image':program.theme.photo['WordRec'],
                'sticky':'ew',
                'tttext':tttext
                }
    def tasktitle(self):
        return _("Add and Parse Words with Audio") # for Citation Forms
    def __init__(self, parent):
        log.info("Initializing {}".format(self.tasktitle()))
        self.ftype=program.params.ftype('lc') #always correct?
        # self.nodetag='citation'
        TaskDressing.__init__(self,parent)
        Parse.__init__(self,parent)
        WordCollectionwRecordings.__init__(self,parent)
        program.taskchooser.withdraw()
        fn=self.getwords()#?
class WordsParse(Parse,WordCollection,TaskDressing):
    def taskicon(self):
        return program.theme.photo['iconWord']
    def tooltip(self):
        return _("This task helps you parse words you collected earlier.")
    def tasktitle(self):
        return _("Parse Already Collected Words") # for Citation Forms
    def dobuttonkwargs(self):
        pass
    def __init__(self, parent):
        log.info("Initializing {}".format(self.tasktitle()))
        self.ftype=program.params.ftype('lc') #always correct?
        # self.nodetag='citation'
        TaskDressing.__init__(self,parent)
        Parse.__init__(self,parent)
        WordCollection.__init__(self,parent)
        # if not program.settings.secondformfieldsOK():
        #     ErrorNotice(_("To parse, you must first define which fields "
        #                     "should contain secondary forms"),
        #                     wait=True)
        #     self.shutdowntask()
        #     return
        self.dodone=True #give me words with citation done
        self.checkeach=True #confirm each word (not default)
        self.dodoneonly=True #don't give me other words
        self.userresponse=Object()
        program.taskchooser.withdraw()
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
        return program.theme.photo['icon']
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
                "awhile.").format(count=len(program.taskchooser.cawlmissing))
        return {'text':text,
                'fn':fn,
                # column=0,
                'font':'title',
                'compound':'bottom', #image bottom, left, right, or top of text
                'image':program.theme.photo['icon'],
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
            d=program.params.ftype()
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
        ui.ToolTip(namebutton,text=_("Set the frame name for status table and reports"))
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
        self.langs=[self.analangftypecode()]+program.settings.glosslangs+[
                                    l for l in program.db.glosslangs
                                    if l not in program.settings.glosslangs]
        for l in [self.analangftypecode()]+program.settings.glosslangs: #actually selected
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
            langname=program.settings.languagenames[self.stripftypecode(l)]
            if l in self.forms:
                log.info("Working on {}".format(langname))
                if l == self.stripftypecode(l): #no change means gloss
                    tintro=_("Gloss in {lang}:").format(lang=langname)
                    if l in program.settings.glosslangs:
                        ltttext=_("current gloss language")
                    else:
                        ltttext=_("additional gloss language")
                        b=ui.Button(self.fds,text='X',
                                    cmd=lambda l=l:self.skiplang(l),
                                    column=0,row=n+1,sticky='e')
                        b.tt=ui.ToolTip(b, _("Skip {lang}").format(lang=langname))
                else:
                    tintro=_("{lang}:").format(lang=langname)
                    ltttext=_("analysis language")
                li=ui.Label(self.fds,text=tintro,column=1,row=n+1)
                li.tt=ui.ToolTip(li, ltttext)
                lineframe=ui.Frame(self.fds,column=2,row=n+1)
                if 'Language ' in langname:
                    tword=_("<word>")
                else:
                    tword=_("<{lang} word>").format(lang=langname)
                try:
                    text=self.forms[l]['before']
                    if text == '':
                        text=nothing
                except KeyError:
                    try:
                        self.forms[l]={'before':''}
                        text=nothing
                    except:
                        text='<'+_("No {lang} frame info").format(
                                lang=program.settings.languagenames[l])+'>'
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
                text=_("Add {lang} gloss").format(lang=langname)
                button=ui.Button(self.fds,text=text,
                                relief=relief,
                                font='small',
                                cmd=lambda l=l: self.addback(l),
                                columnspan=2,column=0,row=n+1,padx=0,ipadx=0)
                ui.ToolTip(button,_("Add {lang} values for this frame").format(
                                    lang=langname
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
        #     log.info("{}".format(program.settings.pluralname))
        #     log.info("{}".format(program.settings.imperativename))
        #     log.info("{}".format(program.settings.secondformfield[program.settings.verbalps]))
        #     log.info("{}".format(program.settings.secondformfield[program.settings.nominalps]))
        # except Exception as e:
        #     log.error("Exception in ps-land:{}".format(e))
        opts=[
                ('lc', _("Citation form")),
                ('lx', _("Lexeme form")),
                ]
        """These should maybe be switched over to just pl and imp"""
        if self.ps == program.settings.nominalps:
            opts.append((program.settings.pluralname, _("Plural form")))
        elif self.ps == program.settings.verbalps:
            opts.append((program.settings.imperativename, _("Imperative form")))
        return [(i,j) for (i,j) in opts if i]
    def getfieldtype(self,event=None):
        w=ui.Window(self,
                        # row=1,column=0,
                        # sticky='ew',
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
        text=_("Examples for {name} {field} tone frame").format(name=checktoadd,
                                                        field=self.fieldtypename())
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
        stext=_('Use {name} tone frame').format(name=checktoadd)
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
            lname=program.settings.languagenames[self.stripftypecode(lang)]
            text=_("Fill in the {lang} frame forms below.\n(include a "
                "space to separate word forms)"
                ).format(lang=lname)
            if lang != self.stripftypecode(lang): #i.e., analang
                kind=_('form')
                ok=_('Use this form')
            else:
                kind=_('gloss')
                ok=_("Use this {lang} form {context} the dictionary gloss").format(lang=lname,
                                context=_(context))
                self.glosslangs.append(lang)
            if context == 'before':
                text+='\n'+_("What text goes *before* \n<==the {lang} word *{kind}* "
                        "\nin the frame?").format(lang=lname,kind=kind)
            elif context == 'after':
                text+='\n'+_("What text goes *after* \nthe {lang} word *{kind}*==> "
                        "\nin the frame?").format(lang=lname,kind=kind)
        else:
            text=_("What do you want to call this new {ps} tone frame for {lang}?"
                    ).format(ps=self.ps,
                            lang=program.settings.languagenames[self.analang])
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
                        # row=1,column=0,
                        # sticky='ew',
                        padx=25,pady=25)
        if lang and context:
            self.w.title('{} {}'.format(context,lang))
        else:
            self.w.title(_("New {ps} Tone frame for {lang}: Name the Frame").format(
                        ps=self.ps,lang=program.settings.languagenames[self.analang]))
        self.withdraw() #Don't show status when asking for a value
        getform=ui.Label(self.w.frame,text=strings['prompt'],
                        font='read',row=0,column=0,
                        wraplength=program.root.wraplength/2,
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
        program.toneframes.addframe(self.ps,checktoadd,checkdefntoadd)
        program.status.renewchecks() #renew (not update), because of new frame
        # log.info("object: {}".format(program.toneframes))
        program.settings.storesettingsfile(setting='toneframes')
        program.settings.setcheck(checktoadd) #assume we will use this now
        self.task.deiconify()
        self.destroy()
    def gimmesense(self,sense=None,next=False,**kwargs):
        sensesbyps=program.db.sensesbyps[self.ps]
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
            if tried > program.db.nsenses*1.5: #give up looking randomly
                sense=self.gimmesense(sense,next=True)
            else:
                sense=self.gimmesense()
            f.update(sense.formatteddictbylang(self.analang, #This is xyz_ftype
                                        glosslangs,
                                        # program.settings.glosslangs,
                                        frame=framedef
                                            ))
            # log.info("Analang form found: {}".format(f[self.analang]))
            tried+=1
            log.info("Values found: {}".format(f))
            if tried> program.db.nsenses*3.5:
                errortext=_("I've tried (randomly, then through each) {count} "
                "times, and not found one "
                "of your {total} senses with data in each of these languages: "
                "{langs}. \nAre you asking for gloss "
                "languages which actually have data in your database? \nOr, are "
                "you missing gloss fields (i.e., you have only 'definition' "
                "fields)?").format(count=tried,total=program.db.nsenses,langs=langs)
                log.error(errortext)
                return #errortext
        log.debug("Found entry {} with glosses {}".format(sense.id,f))
        return f
    def __init__(self,parent):
        ui.Window.__init__(self,parent)
        self.task=parent #this should always be called by a window task
        self.analang=parent.analang
        self.ps=program.slices.ps()
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
        title=_("Define a New {ps} Tone Frame for {lang}").format(ps=self.ps,
                        lang=program.settings.languagenames[self.analang])
        self.title(title)
        t(f"Add {self.ps} Tone Frame for {program.settings.languagenames[self.analang]}")#+'\n'?
        ui.Label(self.frame,text=t,font='title',row=0,column=0)
        self.scroll=ui.ScrollingFrame(self.frame,row=1,column=0)
        self.content=self.scroll.content
        self.status()

    def store(self):
        log.info(_("Saving toneframes dict to file"))
        program.settings.storesettingsfile('toneframes')
class Multislice(object):
    """This class just triggers which settings are visible to the user, and
    updates changes from child classes"""
    def __init__(self):
        # log.info("Setting up Multislice report, with {dir}".format(dir=dir()))
        """I think these two should go:"""
        self.status.redofinalbuttons() #because the fns changed
class MultisliceS(Multislice):
    def __init__(self):
        self.do=self.basicreport
        program.status.group(None)
        Multislice.__init__(self)
class MultisliceT(Multislice):
    def __init__(self):
        self.do=self.tonegroupreportcomprehensive
        Multislice.__init__(self)
class Multicheck(object):
    def __init__(self):
        """This should only be used for segmental checks; tone reports are
        always multiple checks"""
        program.status.group(None)
        log.info("Setting up Multicheck report, based on {dir}".format(dir=dir()))
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
        log.info("Setting up background report, based on {name}"
                "".format(name=self.do.__name__))
        self.do=lambda fn=self.do:self.background(fn)
        self.status.redofinalbuttons() #because the fns changed
class SortSyllables(Sort,Segments,TaskDressing):
    def taskicon(self):
        return program.theme.photo['iconWord']
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
                'image':program.theme.photo['Word'], #self.cvt
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
        ps=program.slices.ps()
        for sense in program.db.sensesbyps[ps]:
            valuelist=[k for k in program.settings.profilesbysense[ps]
                        if sense in program.settings.profilesbysense[ps][k]]
            if valuelist:
                sense.cvprofilevalue(program.params.ftype(),valuelist[0])
    def runcheck(self):
        program.settings.storesettingsfile()
        log.info("Running check...")
        cvt=program.params.cvt()
        check=program.params.check()
        profiles=program.slices.profiles()
        """further specify check check in maybesort, where you can send the user
        on to the next setting"""
        self.presortgroups()
        self.updatesortingstatus() # Not just tone anymore
        self.maybesort(firstrun=True)
    def __init__(self, parent):
        program.params.cvt('S') #syllable
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
        return 'iconV'#program.theme.photo['iconV']
    def tasktitle(self):
        return _("Sort Vowels") #Citation Form Sorting in Tone Frames
    def tooltip(self):
        return _("This task helps you sort words in citation form by vowels.")
    def dobuttonkwargs(self):
        return {'text':_("Sort!"),
                'fn':self.runcheck,
                'font':'title',
                'compound':'bottom', #image bottom, left, right, or top of text
                'image':program.theme.photo['V'], #self.cvt
                'sticky':'ew'
                }
    def __init__(self, parent, **kwargs):
        program.params.cvt('V')
        TaskDressing.__init__(self,parent)
        Sort.__init__(self, parent)
        Segments.__init__(self,parent)
        if g:=kwargs.get("redo_glyph"):
            self.redo_joinglyphs(g)
        elif g:=kwargs.get("sort_immediately"):
            self.runcheck()
class SortC(Sort,Segments,TaskDressing):
    def taskicon(self):
        return 'iconC'#program.theme.photo['iconC']
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
                'image':program.theme.photo['C'], #self.cvt
                'sticky':'ew'
                }
    def __init__(self, parent, **kwargs):
        program.params.cvt('C')
        TaskDressing.__init__(self,parent)
        Sort.__init__(self, parent)
        Segments.__init__(self,parent)
        if g:=kwargs.get("redo_glyph"):
            self.redo_joinglyphs(g)
        elif g:=kwargs.get("sort_immediately"):
            self.runcheck()
class SortT(Sort,Tone,TaskDressing):
    def taskicon(self):
        return 'iconT'#program.theme.photo['iconT']
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
                'image':program.theme.photo['T'], #self.cvt
                'sticky':'ew'
                }
    def __init__(self, parent): #frame, filename=None
        Tone.__init__(self)
        TaskDressing.__init__(self,parent)
        program.params.cvt('T')
        Sort.__init__(self, parent)
        # log.info("status: {}".format(type(program.status)))
        # Not sure what this was for (XML?):
        self.pp=pprint.PrettyPrinter()
        """Are we OK without these?"""
        log.info("Done initializing check.")
        """Testing Zone"""
    def addtonefieldpron(self,guid,framed): #unused; leads to broken lift fn
        sense=None
        program.db.addpronunciationfields(
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
        newvalue=self.transcriber.formfield.get()
        if newvalue == '':
            noname=_("Give a name for this group!")
            log.debug(noname)
            self.errorlabel['text'] = noname
            return 1
        elif newvalue != self.group and newvalue in self.groups:
            deja=[_("Sorry, there is already a group with that label"),
                _("see comparison below.")]
            log.debug('; '.join(deja))
            self.errorlabel['text'] = ';\n '.join(deja)
            self.setgroup_comparison(newvalue)
            return 1
        self.errorlabel['text'] = ''
    def updateform(self,*args):
        self.set_ok_w_form(self.updateerror())
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
        log.info(_("Swtiching groups; using ‘{comp}’ for "
                "‘{group}’").format(comp=self.group_comparison, group=self.group))
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
        # program.settings.setgroup(gc)
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
        self.groups=program.status.groups(wsorted=True)
        # log.info("self.groups: {}".format(self.groups))
        self.groupsdone=program.status.verified()
        self.group=program.status.group()
        # log.info("group: {}, groups: {}".format(self.group,self.groups))
        if not self.groups:
            ErrorNotice(_("No groups in that slice; try another!"))
            return
        # log.info("group: {}, groups: {}".format(self.group,self.groups))
        if self.group is None or self.group not in self.groups:
            w=self.getgroup(wsorted=True, guess=True, intfirst=True)
            if w.winfo_exists():
                w.wait_window(w)
            self.group=program.status.group()
            if not self.group:
                log.info("I asked for a framed tone group, but didn't get one.")
                return
        # log.info("group: {}, groups: {}".format(self.group,self.groups))
        self.othergroups=self.groups[:]
        try:
            self.othergroups.remove(self.group)
        except ValueError:
            log.error(_("current group ({group}) doesn't seem to be in list of "
                "groups: ({groups})\n\tThis may be because we're looking for data "
                "that isn't there, or maybe a setting is off.").format(
                                                    group=self.group, groups=self.groups))
            return
        return 1
    def unsubmit(self,event=None):
        log.info("Undoing...")
        self.mistake=True
    def polygraphwarn(self,newvalue):
        if len(newvalue) != 1 or len(self.group) != 1:
            warning=[_("This name change (‘{group}’ > ‘{new}’) impacts your "
                        "digraph and trigraph settings."
                        ).format(group=self.group,new=newvalue)]
            if len(newvalue) > 1:
                warning.append(_("{azt} will add ‘{new}’ to those settings."
                            ).format(azt=program.name,new=newvalue))
                if newvalue not in program.settings.polygraphs[self.analang][self.cvt]:
                    program.settings.polygraphs[self.analang][self.cvt][newvalue]=True
                    program.settings.storesettingsfile('profiledata')
            if len(self.group) > 1:
                warning.append(_("{azt} will *not* remove ‘{group}’ from "
                            "those settings, because you may still be "
                            "using it elsewhere."
                            ).format(azt=program.name,group=self.group))
            warning.extend(['',_("**If this isn't what you wanted, "
                        "fix and confirm your digraph and "
                        "trigraph settings in the menu "
                        "\n(this will make {azt} restart and redo "
                        "the syllable profile analysis)."
                        ).format(azt=program.name)])
            title=_("Syllable profile change?")
            #Just state this and move on to making changes:
            log.info('\n'.join(warning))
            # self.err=ErrorNotice(warning,parent=self,title=title)
    def submitform(self):
        newvalue=self.transcriber.formfield.get()
        if program.params.cvt() != 'T': #Warning only on segmental changes
            self.polygraphwarn(newvalue)
            #These should each make one change only, checking for overwrites
            self.rename_macrogroup(self.group,newvalue)
            program.alphabet.glyph(newvalue)
            self.refresh_status_buttons(self.group,newvalue)
        else:
            """updateforms=True doesn't seem to be working for segments"""
            self.updatebygroupsense(self.group,newvalue,updateforms=True)
            #NO: this should update formstosearch and profile data.
            # log.info("Doing renamegroup: {}>{}".format(self.group,newvalue))
            program.status.renamegroup(self.group,newvalue) #status file only
            # log.info("Doing updategroups")
            self.updategroups() #updates self.groups self.group self.othergroups self.groupsdone
            program.settings.storesettingsfile(setting='status')
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
            ints=[i for i in program.status.groups(wsorted=True)
                    if i.isdigit()]
            if ints:
                log.info("Found integer groups: {ints}".format(ints=ints))
                program.status.group(str(min(ints)))#Look for integers first
            else:
                log.info("Didn't Find integer groups: {groups}".format(
                    groups=program.status.groups(wsorted=True)))
                program.status.nextgroup(wsorted=True)
            # log.debug("group: {}".format(group))
            self.makewindow()
    def nextcheck(self):
        log.debug("running next check")
        error=self.submitform()
        if not error:
            # log.debug("check: {}".format(check))
            program.status.nextcheck(wsorted=True)
            # log.debug("check: {}".format(check))
            self.makewindow()
    def nextprofile(self):
        log.debug("running next profile")
        error=self.submitform()
        if not error:
            # log.debug("profile: {}".format(profile))
            program.status.nextprofile(wsorted=True)
            # log.debug("profile: {}".format(profile))
            self.makewindow()
    def setgroup_comparison(self,group=None,**kwargs):
        if group:
            program.settings.set('group_comparison',group)
        else:
            #this returns its window:
            w=self.getglyph(comparison=True,**kwargs)
            if w and w.winfo_exists(): #This window may be already gone
                log.info("Waiting for {w}".format(w=w))
                w.wait_window(w)
        log.info(_("Groups: {group} (of {groups}); "
                "{comp}?").format(group=self.group, groups=self.groups, comp=program.settings.group_comparison))
        if hasattr(program.settings,'group_comparison'):
            self.group_comparison=program.settings.group_comparison
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
            log.info("Making comparison buttons for group {group} now".format(
                                                group=self.group_comparison))
            t=_('Compare with another group ({group})').format(
                                                group=self.group_comparison)
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
            log.info("Comparison ({comp}) not in group list ({groups})"
                        "".format(comp=self.group_comparison,groups=self.groups))
        elif self.group_comparison == self.group:
            log.info("Comparison ({comp}) same as subgroup ({group}); not showing."
                        "".format(comp=self.group_comparison,group=self.group))
        else:
            log.info(_("This should never happen (renamegroup/"
                        "comparisonbuttons)"))
        self.sub_c['text']=t
    def __init__(self,parent): #frame, filename=None
        TaskDressing.__init__(self, parent)
        program.settings.makeeverythingok()
        self.ftype=program.params.ftype()
        self.mistake=False #track when a user has made a mistake
        self.analang=program.params.analang()
        program.status.makecheckok()
        Sound.__init__(self)
class TranscribeS(Transcribe,Segments):
    macrosort=True
    def done(self):
        log.info("Transcribe done")
        self.submitform()
        program.alphabet.save_settings()
        self.donewpyaudio()
    def go_back(self):
        log.info("Transcribe done for now (going back)")
        self.runwindow.on_quit()
        self.donewpyaudio()
        program.taskchooser.maketask(f"Sort{program.params.cvt()}",
                                        redo_glyph=self.group)
    def set_ok_w_form(self,error=False):
        form=self.transcriber.formfield.get()
        self.oktext.set(_("OK: Add the letter ‘{form}’ {newline}to my alphabet "
                        "{newline}for this sound").format(form=form,newline="\n"))
        if form and not error:
            self.ok_button['state'] = 'normal'
        else:
            self.ok_button['state'] = 'disabled'
    def makewindow(self, glyph=None, event=None):
        self.pyaudiocheck() # seems to dissapear sometimes
        self.ok_done=False
        if glyph:
            self.group=program.alphabet.glyph(glyph)
        else:
            self.group=program.alphabet.glyph()
        if not isinstance(self.group, str):
            log.info("Group not a string! ({group}, {type})".format(group=self.group, type=type(self.group)))
        cvt=program.params.cvt()
        self.groups=program.alphabet.glyphs()
        # self.groups=program.status.all_groups_verified_for_cvt()
        self.otherglyphs=set(self.groups)-{self.group}
        padx=50
        if program.settings.lowverticalspace:
            log.info("Using low vertical space setting")
            pady=0
        else:
            pady=10
        self.buttonframew=int(program.screenw()/3.5)
        title=[program.params.cvtdict()[cvt]['sg'],_("letter")]
        getformtext=[_("What letter(s) will you use for this {sg} "
                        "group?").format(sg=program.params.cvtdict()[cvt]['sg'])]
        if self.group.isdigit():
            title.insert(0,_("Name New"))
            # getformtext.append(_("Because this is a new group, you need to give it "
            #                 "some name now."))
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
                        text='\n'.join(getformtext),
                        font='read',
                        norender=True,
                        row=1,column=0,sticky='ew',padx=padx,pady=pady
                        )
        getform.wrap()
        inputfeedbackframe=ui.Frame(self.runwindow.frame,
                            row=2,column=0,sticky=''
                            )
        self.transcriber=transcriber.Transcriber(inputfeedbackframe,
                                initval=initval,
                                soundsettings=self.soundsettings,
                                chars=self.glyphspossible,
                                row=0,column=0,sticky=''
                                )
        self.transcriber.newname.trace_add('write', self.updateform)
        infoframe=ui.Frame(inputfeedbackframe,
                            row=0,column=1,sticky=''
                            )
        """Make this a pad of buttons, rather than a label, so users can
        go directly where they want to be"""
        g=nn(self.otherglyphs,perline=len(self.otherglyphs)//3)
        # log.info("groups={groups}, otherglyphs={other}, g={g}".format(groups=self.groups, other=self.otherglyphs, g=g))
        glyphslabel=ui.Label(infoframe,
                            text='\n'.join([_("Don't use Other Groups:"),g]),
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
        return program.theme.photo['iconTranscribeV']
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
        self.cvt=program.params.cvt('V')
        super().__init__(parent)
class TranscribeC(TranscribeS):
    def tasktitle(self):
        return _("Consonant Letters")
    def tooltip(self):
        return _("This task helps you decide on your consonant letters.")
    def taskicon(self):
        return program.theme.photo['iconTranscribeC']
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
        self.cvt=program.params.cvt('C')
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
                'image':program.theme.photo['Transcribe'], #self.cvt
                'sticky':'ew'
                }
    def taskicon(self):
        return program.theme.photo['iconTranscribe']
    def done(self):
        log.info("Transcribe done")
        self.submitform()
        self.donewpyaudio()
    def set_ok_w_form(self):
        pass #maybe use some day?
    def makewindow(self, group=None, event=None):
        if group:
            self.group=program.status.group(group)
        """Go through this and tease apart what is needed for tone complexity,
        and move that to tone.
        Note to user: you can't pick these group names (switch later, not here)
        Make another function to switch letters between groups."""
        # log.info("Making transcribe window")
        def changegroupnow(event=None):
            w=program.taskchooser.getgroup(wsorted=True)
            self.runwindow.wait_window(w)
            if not w.exitFlag.istrue():
                self.runwindow.on_quit()
                self.makewindow()
        cvt=program.params.cvt()
        ps=program.slices.ps()
        profile=program.slices.profile()
        check=program.params.check()
        self.buttonframew=int(program.screenw/3.5)
        if not check:
            self.getcheck(guess=True)
            if check is None:
                # log.info("I asked for a check name, but didn't get one.")
                return
        if not program.status.groups(wsorted=True):
            log.error(_("I don't have any sorted data for check: {check}, "
                        "ps-profile: {ps}-{profile},").format(check=check,ps=ps,profile=profile))
            return
        groupsok=self.updategroups()
        if not groupsok:
            log.error("Problem with log; check earlier message.")
            return
        padx=50
        if program.settings.lowverticalspace:
            log.info("Using low vertical space setting")
            pady=0
        else:
            pady=10
        title=_("Rename {ps} {profile} {noun_sg} group ‘{group}’ in ‘{check}’ frame"
                        ).format(ps=ps,profile=profile,
                        noun_sg=program.params.cvtdict()[cvt]['sg'],
                        group=self.group,check=check)
        self.getrunwindow(title=title)
        titlel=ui.Label(self.runwindow.frame,text=title,font='title',
                        row=0,column=0,sticky='ew',padx=padx,pady=pady
                        )
        getformtext=[_("What new name do you want to call this {sg} "
                        "group?").format(sg=program.params.cvtdict()[cvt]['sg'])]
        if cvt == 'T':
            getformtext.append(_("A label that describes the surface tone form "
                        "in this context would be best, like ‘[˥˥˥ ˨˨˨]’"))
        getform=ui.Label(self.runwindow.frame,
                        text='\n'.join(getformtext),
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
                            text='\n'.join([_('Other Groups:'),g]),
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
        program.params.cvt('T')
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
                'image':program.theme.photo['JoinUF'], #self.cvt
                'sticky':'ew'
                }
    def taskicon(self):
        return program.theme.photo['iconJoinUF']
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
            log.info(f"groupsselected:{groupsselected}")
            if uf in self.analysis.orderedUFs and uf not in groupsselected:
                deja=_("That name is already there! (did you forget to include "
                        "the ‘{uf}’ group?)").format(uf=uf)
                log.debug(deja)
                errorlabel['text'] = deja
                return
            for group in groupsselected:
                if group in self.analysis.sensesbygroup: #selected ones only
                    log.debug(_("Changing values from {group} to {uf} for the "
                            "following sense.ids: {ids}").format(group=group,uf=uf,
                            ids=[i.id for i in self.analysis.sensesbygroup[group]]))
                    for sense in self.analysis.sensesbygroup[group]:
                        sense.uftonevalue(uf)
            self.maybewrite()
            self.runwindow.on_quit()
            program.status.last('joinUF',update=True)
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
        ps=kwargs.get('ps',program.slices.ps())
        profile=kwargs.get('profile',program.slices.profile())
        analysisOK,joinedsince,timestamps=program.status.isanalysisOK(**kwargs) #Should specify which lasts...
        if not analysisOK:
            if not kwargs.get('redo'):
                #otherwise, the user will almost certainly be upset to have to do it later
                redo(timestamps)
            else:
                txt=_("The analysis still isn't OK after retrying; "
                        "Check your settings and try again (e.g., "
                        "{ps} {profile} checks: {checks})").format(ps=ps, profile=profile, checks=program.status.checks())
                ErrorNotice(txt,wait=True,parent=self)
            return
        self.getrunwindow(msg=_("Preparing to join draft underlying form groups"
                                "")+'\n'+timestamps)
        self.update()
        title=_("Join/Rename Draft Underlying {ps}-{profile} tone groups").format(
                                                        ps=ps,profile=profile)
        self.runwindow.title(title)
        padx=50
        pady=10
        rwrow=gprow=qrow=0
        t=ui.Label(self.runwindow.frame,text=title,font='title')
        t.grid(row=rwrow,column=0,sticky='ew')
        redotext=_("Redo the analysis;\nstart these groups over")
        text=_("This page allows you to join the {ps}-{profile} draft underlying tone "
                "groups created for you by {program}, \nwhich are almost certainly "
                "too small for you. \nLooking at a draft report, and making "
                "your own judgement about which groups belong together, select "
                "all the groups that belong together in one group, and "
                "give that new group "
                "a name. You can then repeat this for other groups "
                "that should be joined. \nIf for any reason you want to undo "
                "the groups you create here, you can start over with an new "
                "analysis by pressing the ‘{redo}’ button. \nOtherwise, these "
                "joined groups will be reflected in reports until you sort "
                "more data.").format(ps=ps,profile=profile,program=program.name,
                                                redo=redotext.replace('\n',' '))
        rwrow+=1
        i=ui.Label(self.runwindow.frame,text=text,
                    row=rwrow,column=0,sticky='ew')
        i.wrap()
        ui.Button(self.runwindow.frame,text=redotext, cmd=redo,
                    row=rwrow,column=1,sticky='ew')
        rwrow+=1
        qframe=ui.Frame(self.runwindow.frame)
        qframe.grid(row=rwrow,column=0,sticky='ew')
        text=_("What do you want to call this UF tone group for {ps}-{profile} words?"
                "").format(ps=ps,profile=profile)
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
        text=_("Select the groups below that you want in this {ps} group, then "
                "click ==>").format(ps=ps)
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
            ErrorNotice(title=_("No draft UF groups found for {ps} words!"
                                "").format(ps=ps),
                        text=_("You don't seem to have any analyzed {ps} groups "
                        "to join/rename. Have you done a tone analyis for {ps} "
                        "words?").format(ps=ps)
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
            buttontext=f'{group} ({n})'
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
                'image':program.theme.photo['WordRec'],
                'sticky':'ew'
                }
    def tasktitle(self):
        return _("Record Words") #Citation Forms
    def taskicon(self):
        return program.theme.photo['iconWordRec']
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
                'image':program.theme.photo['TRec'],
                'sticky':'ew'
                }
    def taskicon(self):
        return program.theme.photo['iconTRec']
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
        return program.theme.photo['iconReport']
    def tooltip(self):
        return _("This report gives you reports for one lexical "
                "category, in one syllable profile. \nIt does "
                "one of three sets of reports: \n- Vowel, \n- Consonant, or "
                "\n- Consonant-Vowel Correspondence")
    def dobuttonkwargs(self):
        return {'text':_("Report!"),
                'fn':self.do,
                'font':'title',
                'compound':'bottom', #image bottom, left, right, or top of text
                'image':program.theme.photo['Report'],
                'sticky':'ew'
                }
    def runcheck(self):
        """This needs to get stripped down and updated for just this check"""
        program.settings.storesettingsfile()
        t=(_('Run Check'))
        log.info("Running report...")
        log.info("Using these regexs: {rx}".format(rx=self.rxdict))
        # exit() #for testing
        i=0
        cvt=program.params.cvt()
        if cvt == 'T':
            w=program.taskchooser.getcvt()
            w.wait_window(w)
            cvt=program.params.cvt()
            if cvt == 'T':
                ErrorNotice(_("Pick Consonants, Vowels, or CV for this report."))
                return
        ps=program.slices.ps()
        if not ps:
            self.getps()
        check=program.params.check()
        profile=program.slices.profile()
        if not profile:
            self.getprofile()
        if not profile or not ps:
            window=ui.Window(self)
            text=_('Error: please set Ps-Profile first! ({ps}/{check}/{profile})').format(
                                                     ps=ps,check=check,profile=profile)
            ui.Label(window,text=text).grid(column=0, row=i)
            i+=1
            return
        log.info(_('Ps-Profile-Check OK; doing getresults! ({ps}/{check}/{profile})').format(
                                                 ps=ps,check=check,profile=profile))
        self.getresults()
    def __init__(self, parent): #frame, filename=None
        program.params.ftype('lc')
        Segments.__init__(self,parent)
        self.do=self.getresults
        program.status.group(None) #default to reports with all groups
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
        return {'text':_("Report!"),
                'fn':self.do,
                # column=0,
                'font':'title',
                'compound':'bottom', #image bottom, left, right, or top of text
                'image':program.theme.photo['VCCVRepcomp'],
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
        return program.theme.photo['icontall']
    def tooltip(self):
        return _("This task automates work normally done before a consultant "
                "check: \n- reloads status data, and \n- runs comprehensive tone "
                "reports, \n  - by location and \n  - by lexeme sense.")
    def dobuttonkwargs(self):
        return {'text':'\n'.join([_("Start!"),_("Profiles first!")]),
                'fn':self.consultantcheck,
                # column=0,
                'font':'title',
                'compound':'bottom', #image bottom, left, right, or top of text
                'image':program.theme.photo['icontall'],
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
        return program.theme.photo['iconTRep']
    def tooltip(self):
        return _("This report gives you report for one lexical "
                "category, in one syllable profile. \nIt does "
                "this for all data sorted in tone frames, organized by word.")
    def dobuttonkwargs(self):
        return {'text':_("Report!"),
                'fn':self.do,
                'font':'title',
                'compound':'bottom', #image bottom, left, right, or top of text
                'image':program.theme.photo['TRep'],
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
        return program.theme.photo['iconTRep']
    def tooltip(self):
        return _("This report gives you report for one lexical "
                "category, in one syllable profile. \nIt does "
                "this for all data sorted in tone frames.")
    def dobuttonkwargs(self):
        return {'text':_("Report!"),
                'fn':self.do,
                'font':'title',
                'compound':'bottom', #image bottom, left, right, or top of text
                'image':program.theme.photo['TRep'],
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
        return program.theme.photo['iconTRep']
    def tooltip(self):
        return _("This report gives you report for one lexical "
                "category, in one syllable profile. \nIt does "
                "this for all data sorted in tone frames, organized by frame.")
    def dobuttonkwargs(self):
        return {'text':_("Report!"),
                'fn':self.do,
                'font':'title',
                'compound':'bottom', #image bottom, left, right, or top of text
                'image':program.theme.photo['TRep'],
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
        return program.theme.photo['iconTRepcomp']
    def tooltip(self):
        return _("This report gives you reports across multiple lexical "
                "categories, and across multiple syllable profiles. \nIt does "
                "this for all data sorted in tone frames, organized by word.")
    def dobuttonkwargs(self):
        return {'text':_("Report!"),
                'fn':self.do,
                'font':'title',
                'compound':'bottom', #image bottom, left, right, or top of text
                'image':program.theme.photo['TRepcomp'],
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
        return program.theme.photo['iconTRepcomp']
    def tooltip(self):
        return _("This report gives you reports across multiple lexical "
                "categories, and across multiple syllable profiles. \nIt does "
                "this for all data sorted in tone frames, organized by word.")
    def dobuttonkwargs(self):
        return {'text':_("Report!"),
                'fn':self.do,
                'font':'title',
                'compound':'bottom', #image bottom, left, right, or top of text
                'image':program.theme.photo['TRepcomp'],
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
        return program.theme.photo['iconTRepcomp']
    def tooltip(self):
        return _("This report gives you reports across multiple lexical "
                "categories, and across multiple syllable profiles. \nIt does "
                "this for all data sorted in tone frames, organized by word.")
    def dobuttonkwargs(self):
        return {'text':_("Report!"),
                'fn':self.do,
                'font':'title',
                'compound':'bottom', #image bottom, left, right, or top of text
                'image':program.theme.photo['TRepcomp'],
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
        return program.theme.photo['iconTRepcomp']
    def tooltip(self):
        return _("This report gives you reports across multiple lexical "
                "categories, and across multiple syllable profiles. \nIt does "
                "this for all data sorted in tone frames, organized by word.")
    def __init__(self, parent):
        ReportCitationMultisliceTL.__init__(self,parent)
        Background.__init__(self)
"""Task definitions end here"""
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
            name=program.params.cvcheckname(self.check)
            firstOK=_("This word has {name}").format(name=name)
        newgroup=_("Other {check}").format(check=self.check if not self.macrosort else _("Letter"))
        skiptext=_("Skip this item")
        if '=' in self.check and not self.macrosort:
            skiptext+=f" ({self.check.replace('=','≠')})"
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
        # log.info("SortButtonFrame addgroupbutton for {group}".format(group=group))
        if self.exitFlag.istrue():
            return #just don't die
        if program.settings.lowverticalspace:
            # log.info("using lowverticalspace for addgroupbutton")
            scaledpady=0
        else:
            scaledpady=int(40*program.scale)
        # log.info("This button at row={row}, col={col}".format(row=self.groupbuttons.row, col=self.groupbuttons.col))
        nbuttons=len(self.groupbuttons.winfo_children())
        r,c=nbuttons//self.buttoncolumns,nbuttons%self.buttoncolumns
        kwargs={'group':group} #this may be glyph, item code, or sort group
        if self.macrosort and not self.remove_on_click:
            frame_class=SortGlyphGroupButtonFrame #this takes glyph, calls other
        else:
            frame_class=SortGroupButtonFrame #this takes item code or sort group
        if self.macrosort and self.remove_on_click:
            kwargs=program.alphabet.parse_verificationcode(group)
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
        # log.info('group buttons made')
        if not b.hasexample:
            log.info('No example found for {group}'.format(group=group))
            b.destroy()
            return
        # log.info('group button example found')
        self.groupvars[group]=b.var()
        self.groupbuttonlist.append(b)
        log.info('Group added: {group}'.format(group=group))
    def reset_selected(self):
        for k in self.groupvars:
            self.groupvars[k].set(False)
    def get_selected(self):
        # log.info("{vars}".format(vars=[(i,self.groupvars[i].get()) for i in self.groupvars]))
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
        # self.task=program.status.task()
        """These two methods each take an item and a category, into which the
        item is sorted. This should be generalizable."""
        self.check=program.params.check()
        self.cvt=program.params.cvt()
        self.maybewrite=program.taskchooser.maybewrite
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
            self.buttoncolumns=program.status.task().buttoncolumns
        waiting.wait(msg)
        
        # Prefetch examples for all groups at once to avoid O(N^2) lookup
        program.examples.prefetch_examples(self.groups, **kwargs)
        
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
            # log.info("self={self} ({type})".format(self=self, type=type(self)))
            # log.info("self.task={task} ({type})".format(task=self.task, type=type(self.task)))
            # log.info("self.task.task={task} ({type})".format(task=self.task.task, type=type(self.task.task)))
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
            log.error("Not setting non-existant canary {canary}; ".format(canary=canary))
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
            log.error(_("SortGroupButtonFrame.getexample returned None for {group} {kwargs}").format(group=self.group, kwargs=kwargs))
            return
        self.getsenseofnode(node)
        self._text=node.formatted(program.taskchooser.analang,
                                    program.taskchooser.glosslangs,
                                    ftype=program.params.ftype(),
                                    frame=program.toneframes.get(
                                                program.params.check()),
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
                                            program.settings.soundsettings)
        b=ui.Button(self, text=self._text,
                    cmd=self.player.play,
                    column=1, row=0,
                    sticky='nesw',
                    **self.buttonkwargs())
        if hasattr(self,'_illustration'):
            b['image']=self._illustration
            b['compound']='left'
        bttext=_("Click to hear this utterance")
        if program.praat:
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
        bt=ui.ToolTip(b,_("Pick this group ({group})").format(group=self.group))
    def refresh(self):
        log.info("SGBF refresh called")
        self.kwargs['renew']=True
        self.kwargs['alwaysrefreshable']=True
        self.getexample(**self.kwargs)
        self.again()
    def updatecount(self,n=None):
        # log.info(_("Updating count for group {group} (n={n})").format(group=self.group,n=n))
        if n is not None:
            self._n.set(n) #for cases where this is already calculated
        else:
            nodes=self.exs.getexamples(self.group,**self.kwargs)
            # log.info(_("Found {count} examples: {nodes}").format(count=len(nodes),nodes=nodes))
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
        # log.info(_("Initializing buttons for group {group}").format(group=group))
        self.exs=program.examples
        self.task=task #the task/check OR the scrollingframe! use self.check.task
        try:
            self.code=program.alphabet.verificationcode(**kwargs)
        except:
            pass #don't worry if that info isn't all there
        self.group=kwargs.pop('group') #must be here
        self.check=kwargs.get('check',None) #must be here for glyphs only
        # self,parent,group,row,column=0,label=False,canary=None,canary2=None,
        # alwaysrefreshable=False,playable=False,renew=False,unsortable=False,
        # **kwargs
        # From check, need
        # check=program.params.check()
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
        if program.settings.lowverticalspace:
            # log.info(_("using lowverticalspace for SortGroupButtonFrame"))
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
        kwargs.update(program.alphabet.parse_verificationcode(item))
        kwargs['column']=1 #specify other attributes shared with frame here
        kwargs['row']=0
        kwargs['gridwait']=True
        kwargs['var']=self.var()
        # kwargs['playable']=True #This needs to apply with Sound...
        log.info(_("Ready to build SortGroupButtonFrame with {kwargs}").format(kwargs=kwargs))
        self.items.append(SortGroupButtonFrame(self, self.task, **kwargs))
        log.info(_("Built SGBF for {item} ({items})").format(item=item, items=self.items))
        if self.items[-1].hasexample:
            # log.info(_("Built {group} SortGroupButtonFrame with ex").format(group=kwargs['group']))
            self.hasexample=True
        else:
            # log.info(_("No {group} SortGroupButtonFrame ex; removing").format(group=kwargs['group']))
            self.items=self.items[:-1]
    def next_item(self,event=None):
        # log.info(_("next_item ({index})").format(index=self.shown_index))
        if self.shown_index == len(self.items)-1: #loop back on last
            self.show_one()
        else:
            self.show_one(self.shown_index+1)
    def prev_item(self,event=None):
        # log.info(_("prev_item ({index})").format(index=self.shown_index))
        if self.shown_index == 0: #loop back on first
            self.show_one(len(self.items)-1)
        else:
            self.show_one(self.shown_index-1)
    def show_one(self,index=0):
        for item in [i for i in self.items if self.items.index(i) != index]:
            item.grid_remove()
        self.items[index].grid()
        log.info(_("Showing item with {code}").format(code=self.items[index].code))
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
        # log.info(_("Updating count for group {group} (n={n})").format(group=self.group,n=n))
        if n is not None:
            self._n.set(n) #for cases where this is already calculated
        else:
            # nodes=self.exs.getexamples(self.group)
            # log.info(_("Found {count} examples: {nodes}").format(count=len(nodes),nodes=nodes))
            self._n.set(len(self.items))
        if self._n.get() <2 and self.check_label.winfo_exists():
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
            log.error(_("Not setting non-existant canary {canary}; ").format(canary=canary))
    def __init__(self, parent, task, **kwargs):
        self.task=task #the task/check OR the scrollingframe! use self.check.task
        self.group=kwargs.pop('group')
        # self.check=kwargs.get('check')
        log.info(_("Building SortGlyphGroupButtonFrame for {group}").format(group=self.group))
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
        if self.group not in program.alphabet.glyph_members():
            ui.Label(self,text=_("group ‘{group}’ isn't in glyphs! "
                    "({members})").format(group=self.group, members=list(program.alphabet.glyph_members())),
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
        for item in program.alphabet.glyph_members()[self.group]:
            log.info(_("Making Glyph member {item} button").format(item=item))
            self.make_sgbf(item, **kwargs)
        if self.items:
            self.updatecount()
            self.show_one()
        log.info(_("Built SortGlyphGroupButtonFrame for {group}").format(group=self.group))
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
                # log.info(_("Found Image, using"))
                image=self.sense.image
                compiled=True
                self.hasimage=True
            else:
                i=getimagelocationURI(self.sense)
        # lift.prettyprint(self.sense.illustration)
        if not compiled:
            try:
                # log.info(_("trying to make image {image}").format(image=i))
                assert i
                image=ui.Image(i)
                self.hasimage=True
                # log.info(_("Image OK: {img}").format(img=img))
            except (tkinter.TclError,AssertionError,AttributeError) as e:
                if e.args and ('value for "-file" missing' not in e.args[0] and
                        "couldn't recognize data in image file" not in e.args[0]):
                    log.info(_("ui.Image error: {error}").format(error=e))
                log.info(f"No image for {self.sense}")
                image=self.theme.photo['NoImage']
                self.hasimage=False
                # log.info(_("Image null: {img}").format(img=img))
            if not specifiedurl and self.hasimage: #don't assign "no image"
                self.sense.image=image
        # log.info(_("Image: {image} ({type})").format(image=image,type=type(image)))
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
            image1=program.theme.photo['Order!']
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
            log.error(_("ImageFrame called without sense or url!"))
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
        self.labels['v']['text']=_("Version: {version}").format(version=program.version)
        self.labels['v2']['text']=_("updated to {date} ({date_rel})").format(date=program.source_repo.lastcommitdate(), date_rel=program.source_repo.lastcommitdaterelative())
        self.labels['textl']['text']=_("Your dictionary database is loading...")
        self.labels['text']['text']=_("{azt} is a computer "
                "program that accelerates community-based language development "
                "by facilitating the sorting of a beginning dictionary "
                "by vowels, consonants and tone. (more in help:about)").format(azt=program.name)
        self.labels['titletext']['text']=(_("{azt} Dictionary and Orthography "
                                        "Checker").format(azt=program.name))
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
            parent=program.root
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
        # log.error(_("ErrorNotice: “{text}”").format(text=text))
        # log.info("parent: {}".format(kwargs['parent']))
        # log.info("program: {}".format(program))
        # log.info("program.root: {}".format(program.root))
        # log.info("program.root.exitFlag: {}".format(program.root.exitFlag))
        # log.info("program.root.exitFlag.istrue(): {}".format(program.root.exitFlag.istrue()))
        try:
            assert not program.root.exitFlag.istrue()
        except Exception as e:
            if 'parent' not in kwargs:
                log.info(_("Exception: {error}").format(error=e))
                log.error(_("Couldn't find a parent; error message follows"))
                log.error(text)
                return
        parent=kwargs.get('parent',getattr(program,'root',ui.Root()))
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
        # self.pull() # in case there's a source available
class ResultWindow(ui.Window):
    def __init__(self, parent, msg=None, title=None):
        """Can't test for widget/window if the attribute hasn't been assigned,
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
            and 'azt.mo' in os.listdir(os.path.join(transdir, i, 'LC_MESSAGES'))
            ]
        log.info("Found {langs}".format(langs=langs))
        self.i18n={'en': gettext.translation('azt', transdir, languages=['en_US'],
                                        fallback=True
                                    )}
        for i in langs:
            log.info("Loading translation for {}".format(i))
            try:
                self.i18n[i.split('_')[0]] = gettext.translation('azt', transdir, languages=[i])
            except:
                log.error("Failed to load translation for {}".format(i))
            finally:
                log.info("Translation for {} loaded".format(i))
        self.interfacelangs={i for i in self.i18n}
        lang=self.interfacelang() #translation works from here
        log.info(_("Translation is working now ({lang}).").format(lang=lang))
    def interfacelang(self,lang=None,magic=False):
        log.info("interfacelang called with lang {lang} and magic {magic}".format(lang=lang,magic=magic))
        # global i18n
        # global _
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
                code=getlangfromlocale()
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
            file.uilang(lang)
            log.info(_("Set Interface language: {lang}").format(lang=lang))
            return lang
        log.info(_("Returning current Interface language: {lang}").format(lang=curlang))
        return curlang
    def find_source_repo(self):
        # self.findexecutable('git') #done in repo init
        self.source_repo=GitReadOnly(self.aztdir) #this needs root for errors
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
        self.filename=FileChooser().name #new file self.analang set here
        Settings(self) #needs self.filename, pick up self.analang from file
        ExampleDict(self) #needed for makestatus, needs params,slices,data
        # SliceDict(adhoc,profilesbysense,self) #needs adhoc,profilesbysense
        # StatusDict(filename,dict,self) #needs filename,dict
        t = TaskChooser(self) #TaskChooser MainApplication
        t.mainloop()
        sysshutdown()
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
        if self.testing and self.me:
            sys.exit()
            exit()
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
    """functions which are not (no longer?) used"""

    def __init__(self,program):
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
        if self.aztdir.parent.stem == 'raspy': 
            # program.testing=True #eliminates Error screens and zipped logs and repo commits
            self.production=True #True for making screenshots (default theme)
            self.me=True
            self.loglevel='INFO'
            self.testlift='Demo_en' #portion of filename
            self.testtask='SortV' #Will convert from string to class later
            self.default_task='WordCollectnParse'
        else:
            self.me=False
            self.production=True #True for making screenshots (default theme)
            self.testing=False #True eliminates Error screens and zipped logs
            self.loglevel='INFO'
            self.default_task='WordCollectnParse'
        self.get_interface_languages()
        #This isn't helpful where things are copied to disk later:
        self.modified_time=times.modified(self.file)
        self.modified_time_relative=f'{times.now()-self.modified_time} ago'
        self.find_source_repo()
        self.disclosure()
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
            self.run_problem()
        except Exception as e:
            log.exception(_("Unexpected exception! {error}").format(error=e))
            self.run_problem()
        except:
            import traceback
            log.error("uncaught exception: %s", traceback.format_exc())
            self.run_problem()
        sys.exit()
"""These are non-method utilities I'm actually using."""
def runtime_to_now():
    #this returns a delta!
    return times.now()-program.start_time
def getlangfromlocale():
    # log.debug("Looking for interface language in locale.")
    loc,enc=locale.getlocale()
    log.info(f"Found locale {loc}, encoding {enc}")
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
        log.debug(_("{item} is not a list; returning nothing.").format(item=l))
        return
    if l == [] or type(l[0]) is not list:
        log.debug(_("The first element of {list} is not a list; returning nothing."
                    "").format(list=l))
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
        log.debug(_("One or less dict: {dicts}; just returning key.").format(dicts=dicts))
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
         log.error(_("unlist should only be used on text (not node) lists ({list})"
                    "").format(list=l))
         log.error(_("Element[0] text: {text}").format(text=l[0].text))
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
        log.info(_('Sorry, something other than one list item found: {list}'
                '\nDid you mean to use "othersOK=True"? Returning nothing!'
                '').format(list=l))
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
                        "element, and it's not a simple string, either: {element}"
                        ).format(element=element))
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
    log.debug(_("Doing Nothing!"))
    pass
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
def pathseparate(path):
    os=platform.system()
    if os == 'Windows':
        sep=';'
    elif os == 'Linux':
        sep=':'
    else:
        log.error(_("What operating system are you running? ({os})").format(os=os))
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
        log.info(_("PATH is {path}").format(path=path))
        return path
    except Exception as e:
        log.info(_("No path found! ({error})").format(error=e))
def sysexecutableversion():
    # args=[program.python, '--version']
    args=[sys.executable, '--version']
    return stouttostr(subprocess.check_output(args, shell=False))
def openweburl(url):
    webbrowser.open_new(url)
def sysshutdown():
    logsetup.shutdown()
    sys.exit()
def sysrestart(event=None):
    osys=platform.system()
    log.info(_("Hard shutting down now."))
    logsetup.shutdown()
    if osys == 'Linux':
        # log.info(f"restarting with {sys.argv[0]}?={program.python} ({sys.argv}?)")
        # log.info(f"os.execl({sys.executable}, {sys.argv})")
        os.execl(sys.executable, sys.executable, *sys.argv, '--restart')
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
        subprocess.run([sys.executable, *sys.argv, '--restart'])
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
        'http:',
        'git@github.com:'
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
                kwargs['parent']=program.root
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
