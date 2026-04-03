# coding=UTF-8
from utilities.i18n import _
from utilities import logsetup
log=logsetup.getlog(__name__)

import sys
import collections
# import re
# import datetime
# import tkinter as tk
from frontend import ui_tkinter as ui
from utilities.utilities import *
from io_put import lift
from utilities import file, htmlfns
# import time
# import webbrowser
# import os
# import platform
# import subprocess
# import threading
# import json
# import itertools
# import inspect
# import multiprocessing
import migration
import settings


from frontend.error_notice import ErrorNotice

from backend.core.analysis import Analysis
from backend.core.sorting_engine import Sort


class SettingsUI(object):
    """UI methods for Settings — backend logic is in settings.Settings"""
    def interfacelangwrapper(self,choice=None,window=None):
        # log.info(f"going to set interface lang {choice}")
        if choice:
            self.program.interfacelang(choice) #change the UI *ONLY*; no object attributes
            self.set('interfacelang',choice,window) #set variable for the future
            self.langnames() #relocalize
            self.program.mainwindow.status.makeui()
            self.storesettingsfile() #>xyz.CheckDefaults.py
            #because otherwise, this stays as is...
            self.program.mainwindow.maketitle()
        else:
            return self.program.interfacelang()
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
            for lang in self.program.db.analangs:
                for pc in vars[lang]:
                    for pg in vars[lang][pc]:
                        self.polygraphs[lang][pc][pg]=vars[lang][pc][pg].get()
            self.storesettingsfile(setting='profiledata')
            self.program.taskchooser.restart()
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
        azt=self.program.name
        if onboot:
            nochangetext=_("Exit {azt} with no changes").format(azt=self.program.name)
        else:
            nochangetext=_("Exit with no changes")
        log.info(_("Asking about Digraphs and Trigraphs!"))
        titlet=_("{azt} Digraphs and Trigraphs").format(azt=self.program.name)
        hasdata=self.checkforpolygraphsindata()
        #From wherever this is opened, it should withdraw and deiconify that
        pgw=ui.Window(self.program.mainwindow,title=titlet,exit=False)
        t=_("Which of the following letter sequences from your data "
            "refer to a single sound?")
        log.info(_("working with db.analangs: {analangs} and params.analang: {analang}")
                .format(analangs=self.program.db.analangs, analang=self.program.params.analang()))
        lnames=[self.languagenames[y] for y in set(
                    self.program.db.analangs+[self.program.params.analang()]
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
                                                            self.program.Email)
        t2.bind("<Button-1>", lambda e: openweburl(eurl))
        if hasdata:
            t=_("Making changes will restart {name} and trigger another syllable profile analysis. \n"
                "If you don't want that, click '{btn}'.").format(name=self.program.name, btn=nochangetext)
        else:
            t=_("\n*** There don't seem to be any possible digraphs or trigraphs "
                "in your data ***\n")
        row+=1
        t3=ui.Label(pgw.frame,text=t,column=0, row=row)
        helpurl='{}/POLYGRAPHS.md'.format(self.program.docsurl,self.program.Email)
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
        for lang in self.program.db.analangs:
            if lang not in self.polygraphs:
                self.polygraphs[lang]={}
            srow+=1
            title=ui.Label(scroll.content,text=self.languagenames[lang],
                                                        font='read')
            title.grid(column=0, row=srow, columnspan=ncols)
            vars[lang]={}
            # log.info("sclasses: {}".format(self.program.db.s[lang]))
            for sclass in [sc for sc in self.program.db.s[lang] #Vtg, Vdg, Ctg, Cdg, etc
                                if ('dg' in sc or 'tg' in sc or 'qg' in sc)]:
                pclass=sclass.replace('dg','').replace('tg','').replace('qg','')
                if pclass not in self.polygraphs[lang]:
                    self.polygraphs[lang][pclass]={}
                if pclass not in vars[lang]:
                    vars[lang][pclass]={}
                if len(self.program.db.s[lang][sclass])>0:
                    srow+=1
                    header=ui.Label(scroll.content,
                    text=sclass.replace('dg',' (digraph)').replace(
                                        'tg',' (trigraph)').replace(
                                        'qg',' (quatregraph)')+': ')
                    header.grid(column=0, row=srow)
                col=1
                # log.info("pgs: {}".format(self.program.db.s[lang][sclass]))
                for pg in self.program.db.s[lang][sclass]:
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
        if not self.program.taskchooser.exitFlag.istrue():
            return nochanges() #this is the default exit behavior
    def notifyuserofextrasegments(self):
        analang=self.program.db.analang
        if analang not in self.program.db.segmentsnotinregexes:
            return
        invalids=self.program.db.segmentsnotinregexes[analang]
        ninvalids=len(invalids)
        extras=list(dict.fromkeys(invalids).keys())
        if ninvalids >10 and analang != 'en':
            text=_("Your {lang} database has the following symbols, which are "
                "excluding {count} words from being analyzed: \n{symbols}") \
                .format(lang=analang,count=ninvalids,symbols=extras)
            title=_("More than Ten Invalid Characters Found!")
            self.warning=ErrorNotice(text,title=title)
    def statusisup(self):
        """Use this for when a setting should ignore status frame updates"""
        from frontend.ui_shell import StatusFrame
        return (hasattr(self.program.mainwindow,'status') and
                type(self.program.mainwindow.status) is StatusFrame)
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
            if hasattr(self, 'ui_vars') and attribute in self.ui_vars:
                self.ui_vars[attribute].set(str(choice))
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
    def setsecondformfieldN(self,choice,window=None):
        self.secondformfield[self.nominalps]=self.pluralname=choice
        if self.statusisup():
            self.program.mainwindow.status.updatefields()
        self.attrschanged.append('secondformfield')
        for entry in self.program.db.entries:
            entry.plvalue(self.pluralname) # get the right field!
        self.refreshattributechanges()
        if window:
            window.destroy()
    def setsecondformfieldV(self,choice,window=None):
        self.secondformfield[self.verbalps]=self.imperativename=choice
        if self.statusisup():
            self.program.mainwindow.status.updatefields()
        self.attrschanged.append('secondformfield')
        for entry in self.program.db.entries:
            """Doesn't do anything??!?"""
            entry.fieldvalue(self.imperativename,self.program.params.analang) # get the right field!
        self.refreshattributechanges()
        if window:
            window.destroy()
    def setprofile(self,choice=None,window=None):
        if not choice:
            choice=self.program.status.nextprofile()
        self.program.slices.profile(choice)
        self.program.mainwindow.status.updateprofile()
        if self.program.params.cvt() != 'T': #profiles don't determine tone checks
            #in case checks changed:
            firstcheck=self.program.status.updatechecksbycvt()[0]
            if self.program.params.check() != firstcheck:
                self.program.params.check(firstcheck)
                self.attrschanged.append('check')
        self.attrschanged.append('profile')
        self.refreshattributechanges()
        if window:
            window.destroy()
    def setcvt(self,choice,window=None):
        task_base=self.program.task_base()
        self.program.params.cvt(choice)
        self.attrschanged.append('cvt')
        if self.statusisup():
            self.program.mainwindow.status.updatecvt()
        self.refreshattributechanges()
        if not self.program.task:
            log.info(_("No task, apparently, so not worried about changing cvt"))
        elif self.program.task.cvt_sensitive: #Sort and Transcribe
        # isinstance(self.program.task,Transcribe):
            log.info(_("Switching {task_base} tasks").format(task_base=task_base))
            # newtaskclass=getattr(sys.modules[__name__],task_base+choice)
            newtaskclass=task_base+choice
            self.program.status.makecheckok() #this is intentionally broad: *any* check
            self.program.taskchooser.maketask(newtaskclass)
        # elif isinstance(self.program.task,Sort):
        #     # log.info("Switching Sort tasks")
        #     newtaskclass=getattr(sys.modules[__name__],'Sort'+choice)
        #     self.program.status.makecheckok() #this is intentionally broad: *any* check
        #     self.program.taskchooser.maketask(newtaskclass)
        else:
            log.info(_("Not Sorting or Transcribing; chilling with cvt change."))
        if window:
            window.destroy()
    def setanalang(self,choice,window):
        """This is only used when more than one analang exists in the database"""
        log.info(_("Setting Analysis Language to {lang}").format(lang=choice))
        self.program.params.analang(choice)
        self.program.mainwindow.status.updateanalang()
        self.attrschanged.append('analang')
        self.refreshattributechanges()
        window.destroy()
        self.program.taskchooser.restart()
    def setgroup(self,choice,window):
        log.debug(_("setting group: {group}").format(group=choice))
        self.program.status.group(choice)
        if self.program.params.cvt() == 'T':
            self.program.mainwindow.status.updatetonegroup()
        else:
            self.program.mainwindow.status.updatecvgroup()
        if isinstance(self.program.task,Sort) and (
                hasattr(self.program.task,'menu') and
                        self.program.task.menu):
            self.program.task.menubar.redoadvanced()
        window.destroy()
        log.debug(_("group {group} set: {val}").format(group=choice, val=self.program.status.group()))
    def setgroup_comparison(self,choice,window):
        """This doesn't show up on the status window"""
        if hasattr(self,'group_comparison'):
            log.debug(_("group_comparison: {val}").format(val=self.group_comparison))
        self.set('group_comparison',choice,window,refresh=False)
        log.debug(_("group_comparison: {val}").format(val=self.group_comparison))
    def setcheck(self,choice=None,window=None,**kwargs):
        if not choice:
            choice=self.program.status.nextcheck(**kwargs)
        self.program.params.check(choice)
        if self.program.params.cvt() == 'T':
            self.program.mainwindow.status.updatetoneframe()
        else:
            self.program.mainwindow.status.updatecvcheck()
        self.attrschanged.append('check')
        self.refreshattributechanges()
        if window:
            window.destroy()
    def setbuttoncolumns(self,choice,window=None):
        self.buttoncolumns=self.program.mainwindow.buttoncolumns=choice
        if self.statusisup():
            self.program.mainwindow.status.updatebuttoncolumns()
        if window:
            window.destroy()
    def setmaxprofiles(self,choice,window):
        self.maxprofiles=choice
        self.program.mainwindow.status.updatemaxprofiles()
        window.destroy()
    def setmaxpss(self,choice,window):
        self.maxpss=choice
        self.program.mainwindow.status.updatemaxpss()
        window.destroy()
    def setmulticheckscope(self,choice,window):
        self.cvtstodo=self.program.task.cvtstodo=choice
        self.program.mainwindow.status.updatemulticheckscope()
        window.destroy()
    def setglosslang(self,choice,window):
        self.glosslangs.lang1(choice)
        self.program.mainwindow.status.updateglosslangs()
        self.attrschanged.append('glosslangs')
        self.refreshattributechanges()
        window.destroy()
    def setglosslang2(self,choice,window):
        if choice:
            self.glosslangs.lang2(choice)
        elif len(self.glosslangs)>1:
            self.glosslangs.pop(1) #if lang2 is None
        self.program.mainwindow.status.updateglosslangs()
        self.attrschanged.append('glosslangs')
        self.refreshattributechanges()
        window.destroy()
    def setparserasklevel(self,choice,window):
        self.program.taskchooser.parser.asklevel(choice)
        self.program.mainwindow.status.updateparserasklevel()
        window.destroy()
    def setparserautolevel(self,choice,window):
        self.program.taskchooser.parser.autolevel(choice)
        self.program.mainwindow.status.updateparserautolevel()
        window.destroy()
    def setps(self,choice,window):
        self.program.slices.ps(choice)
        self.program.mainwindow.status.updateps()
        self.attrschanged.append('ps')
        self.refreshattributechanges()
        window.destroy()
    def setexamplespergrouptorecord(self,choice,window):
        self.set('examplespergrouptorecord',choice,window)

if __name__ == '__main__':
    # global _
    # try: #translation
    #     _
    # except NameError:
    #     def _(x):
    #         return x
    # from dummy import App,TaskChooser
    from main import App,TaskChooser
    program=App({'version':'0.0b',
                'name':'test',
                'hostname':'test',
                'testing':False,
                'exceptiononload':False,
                'theme':'Kim'})
    program.taskchooser=TaskChooser()
    program.taskchooser.filename="test.lift"
    program.testing=True
    from settings import Settings
    Settings(program)
