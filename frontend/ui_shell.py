# coding=UTF-8
"""This module is an interface to the base frontend classes."""
import sys
import collections
import re
import datetime
import tkinter as tk
from frontend import ui_tkinter as ui
from utilities.utilities import *
from utilities import file, logsetup, htmlfns
from io_put import lift
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

log=logsetup.getlog(__name__)

def __getattr__(name):
    # Lazy load globals from main
    if name in ('program', 'counts', 'me', '_', 'ErrorNotice', 'askerror', 'sysrestart', 'pythonmodules', 'findexecutable', 'main', 'testversion', 'reverttomain', 'buttonwraplength', 'regexdict', 'interfacelang', 'nowruntime', 'callerfn', 'logfinished', 'nn', 'unlist', 'xlp', 'rx', 'exampletype', 'dictofchilddicts', 'dictscompare', 'flatten', 'grouptype', 't', 'openweburl', 'isinterneturl', 'scaleimageifthere', 'loadCAWL', 'saveimagefile', 'ImageFrame', 'TranscribeC', 'TranscribeV', 'TranscribeS', 'ResultWindow', 'Multislice', 'Multicheck', 'Tone', 'Segments', 'ToneFrames', 'CheckParameters', 'Glosslangs', 'Senses', 'WordCollection', 'Parse', 'Sort', 'HasMenus', 'Menus', 'StatusFrame', 'TaskDressing', 'TaskChooser', 'Repository', 'Mercurial', 'Git', 'GitReadOnly', 'Analysis', 'SliceDict', 'StatusDict', 'ExampleDict', 'DictbyLang', 'Settings', 'Entry', 'updateazt', 'LiftChooser', 'SortGroupButtonFrame'):
        import main
        return getattr(main, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

# Mirror main globals lazily to allow bare-name access
for name in ('program', 'counts', 'me', '_', 'ErrorNotice', 'askerror', 'sysrestart', 'pythonmodules', 'findexecutable', 'main', 'testversion', 'reverttomain', 'buttonwraplength', 'regexdict', 'interfacelang', 'nowruntime', 'callerfn', 'logfinished', 'nn', 'unlist', 'xlp', 'rx', 'exampletype', 'dictofchilddicts', 'dictscompare', 'flatten', 'grouptype', 't', 'openweburl', 'isinterneturl', 'scaleimageifthere', 'loadCAWL', 'saveimagefile', 'ImageFrame', 'TranscribeC', 'TranscribeV', 'TranscribeS', 'ResultWindow', 'Multislice', 'Multicheck', 'Tone', 'Segments', 'ToneFrames', 'CheckParameters', 'Glosslangs', 'Senses', 'WordCollection', 'Parse', 'Sort', 'HasMenus', 'Menus', 'StatusFrame', 'TaskDressing', 'TaskChooser', 'Repository', 'Mercurial', 'Git', 'GitReadOnly', 'Analysis', 'SliceDict', 'StatusDict', 'ExampleDict', 'DictbyLang', 'Settings', 'Entry', 'updateazt', 'LiftChooser', 'SortGroupButtonFrame'):
    if name not in globals():
        globals()[name] = LazyGlobal(name)

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
        glyph=program['alphabet'].glyph()
        if not glyph:
            glyph=_("Select")
        options.extend([(_("Resort skipped data"), self.parent.tryNAgain),
                        (_("Presort this group again"), self.parent.re_presort),
                        (_("Reverify current group ({group})").format(group=group),
                                                        self.parent.reverify),
                        (_("Join Sort Groups"), self.parent.redo_join),
                        (_("Reverify Glyph (Letters; {glyph})").format(glyph=glyph), 
                                                    self.parent.reverify_glyph),
                        (_("Join Glyphs (Letters)"), self.parent.redo_joinglyphs),
                        (_("Update Forms"), self.parent.manual_form_update)
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
            # clonetoUSB should be called if updateazt doesn't have a source (incl internet)
            helpitems+=[(_("Update {azt}").format(azt=program['name']), updateazt)]
            if 'git' in program['settings'].repo:
                helpitems+=[(_("Share data to USB"), program['settings'].repo['git'].share)]
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
        dont_show=['NA']
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
                        t+=(f" ({len(program['settings'].profilesbysense[ps][profile])})")
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
                        done=[i for i in node['done'] if i not in dont_show]
                        total=[i for i in node['groups'] if i not in dont_show]
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
                            donenum=unsorted_icon #don't say '0'
                        elif not totalnum and tosort:
                            donenum=''
                        elif (not program['settings'].showdetails or
                            (type(totalnum) is int and type(donenum) is int)):
                            # donenum='{}/{}'.format(donenum,totalnum)
                            donenum=totalnum
                        else:
                            donenum=nn(totalwverified,oneperline=True)
                        if (tosort and totalnum and program['settings'].showdetails):
                            donenum=str(donenum)+'\n'+unsorted_icon
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
        if me:
            self.context.menuitem(_("Change to another Database (Restart)"),
                            program['taskchooser'].changedatabase)
        if 'git' in program['settings'].repo:
            self.context.menuitem(_("Share data to USB"), 
                                program['settings'].repo['git'].share)
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
        self.makestatusframe_after_id=self.after(
                                            program['settings'].refreshdelay,
                                            self.makestatusframe,
                                            dict)
    def on_quit(self,**kwargs):
        self.after_cancel(self.makestatusframe_after_id)
        super().on_quit(**kwargs)
    def makestatusframe(self,dict=None):
        """There are two threads of this method running or waiting at all times,
        one for the taskchooser and another for the task. this should probably
        be converted to a more tkinter native update, like with
        StringVar().set()"""
        if self.exitFlag.istrue():
            return
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
            'tableiteration':self.tableiteration
            })
        if isinstance(self,Multicheck):
            dictnow.update({'cvtstodo':self.task.cvtstodo})
        if isinstance(self,Parse):
            try:
                dictnow.update({
                    # 'parserasklevel':self.parser.ask,
                    # 'parserautolevel':self.parser.auto,
                    'sense.id':self.task.sensetodo
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
        cvt=kwargs.get('cvt',program['params'].cvt())
        if kwargs.get('toverify'):
            glyphs=program['alphabet'].glyphdict()[cvt]
        else:
            glyphs=program['alphabet'].glyphs()
        glyph=program['alphabet'].glyph()
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
        if title is None:
            title=(_("Run Window"))
        if self.exitFlag.istrue():
            return
        self.clear_runwindow()
        self.runwindow=ui.Window(self,title=title,withdrawn=True)
        self.runwindow.title(title)
        self.runwindow.takekioskscreen()
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
    def show_report(self,event=None):
        counts,ps_profile_counts=program['db'].report_counts()
        fields=['citation', 'lexical-unit', 'Plural', 'Imperative']
        l=[f"{field}:\t{counts[field]}" for field in fields 
                        if field in counts]
        ErrorNotice("\n".join(l))
        for ps in [i for i in ps_profile_counts if i in ['Noun','Verb']]:
            l=[f"{ps}:\n{'\n'.join([f'{profile}:\t{ps_profile_counts[ps][profile]}' 
                                for profile in ps_profile_counts[ps]])}" 
               ]
            ErrorNotice("\n".join(l))
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
        self.takekioskscreen()
        self.thread_names=list()

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
            self.optionsframe.grid_columnconfigure(c, weight=1, uniform=c)
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
                self.maketask(program['default_task'])
                #optionlist[-1][0]) #last item, the code
    def maketask(self,taskclass,**kwargs): #,filename=None
        self.unsetmainwindow()
        try:
            if self.task.waiting():
                self.task.waitdone()
            self.task.on_quit() #destroy and set flag
        except AttributeError:
            log.info(_("No task, apparently; not destroying."))
        if type(taskclass) is str:
            taskclass=getattr(sys.modules[__name__],taskclass)
        self.task=taskclass(self,**kwargs) #filename
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
                    AlphabetComparisonPages,
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
        # text=_("{name} will now exit; restart to work with the new database."
        #         "").format(name=program['name'])
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
                program['settings'].repo_commit()
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
        #this currently defaults to write every time asked; can up writeeverynwrites when stable.
        if (write or definitely) and not self.writing:# or definitely:bad idea to overwrite write
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
            #on boot, pull in changes becore committing
            r.share(noclone=True,nocommit=True) 
        self.splash.draw()
    def on_quit(self,**kwargs):
        super().on_quit(**kwargs)
        self.parent.on_quit(**kwargs)
    # def getinterfacelangs(self):
    # # global i18n
    #     return [{'code':i,'name':program['settings'].languagenames[i]}
    #             for i in program['interfacelangs']]
    # # {'code':'fr','name':'Français'},
    # #         {'code':'en','name':'English'},
    # #         {'code':'fub','name':'Fulfulde'}
    # #         ]
    def __init__(self,program):
        self.program=program
        program.taskchooser=self
        self.towrite=False
        self.writing=False
        self.datacollection=True # everyone starts here?
        self.showreports=False
        self.showingreports=False
        self.splash = Splash(self)
        self.splash.draw()
        assert 'settings' in program
        # self.interfacelangs=self.getinterfacelangs()
        FileParser(self.filename,self.program.settings.analang)
        self.splash.progress(55)
        self.setmainwindow(self)
        self.program.settings.post_lift_init()
        self.splash.progress(65)
        self.whatsdone()
        self.splash.progress(80)
        log.info(_("Settings: {settings}").format(settings=self.program.settings))
        super().__init__(self.program.tk_root)
        # TaskDressing.__init__(self,parent) #I think this should be after settings
        self.program.settings.getprofiles()
        Alphabet() #after slicedict is up
        # self.withdraw()
        self.splash.progress(90)
        self.setmainwindow(self)
        if self.program.tk_root.exitFlag.istrue():
            return
        # self.guidtriage() #sets: self.guidswanyps self.guidswops self.guidsinvalid self.guidsvalid
        # self.guidtriagebyps() #sets self.guidsvalidbyps (dictionary keyed on ps)
        """Can whatsdone be joined with makedefaulttask? they appear together
        elsewhere."""
        self.splash.maketexts() #update for translation change
        if not self.program.settings.writeeverynwrites: #0/None are not sensible values
            self.program.settings.writeeverynwrites=1
            self.program.settings.storesettingsfile()
        self.usbcheck()
        self.writeable=0 #start the count
        if self.program.nosound:
            e=_("You don't have the sound module installed. For best use of {name},"
                "you should switch back to the main branch, connect to the "
                "internet, and restart. In the mean time. You won't be able "
                "to record or play audio!"
                ).format(name=self.program.name)
            ErrorNotice(e)
        self.splash.progress(100)
        if self.splash.exitFlag.istrue():
            sysshutdown()
        self.splash.destroy()
        self.maxprofiles=5 # how many profiles to check before moving on to another ps
        self.maxpss=2 #don't automatically give more than two grammatical categories
        log.info(_("done setting up taskChooser"))
        self.makedefaulttask() #normal default
        # self.gettask() # let the user pick
        """Do I want this? Rather give errors..."""

