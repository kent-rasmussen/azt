# coding=UTF-8
"""This module is an interface to the base frontend classes."""
from utilities.i18n import _
from utilities import logsetup
log=logsetup.getlog(__name__)
import sys
import collections
import re
import datetime
import tkinter as tk
from frontend import ui_tkinter as ui
from utilities.utilities import *
from utilities import file, logsetup, htmlfns, executables
from io_put import lift
from backend import langtags
from backend.reporting.generator import Report
import langcodes
import settings

from frontend.error_notice import ErrorNotice

from utilities import rx
from backend.core.report_mixins import Multislice, Multicheck
from backend.core.lexicon import Tone, Segments, WordCollection, Parse
from backend.core.analysis import Analysis, StatusDict
from backend.core import templates
from io_put import sound
from io_put.cawl import loadCAWL


class HasMenus():
    def helpnewinterface(self):
        title=_("{azt} Dictionary and Orthography Checker") \
                .format(azt=self.program.name)
        window=ui.Window(self, title=title)
        text=_("{name} has a new interface, starting mid January 2022. You "
                "should still be able to do everything you did before, though "
                "you will probably get to each function a bit differently "
                "—hopefully more intuitively."
                "\nTasks are organized into Data Collection and Analysis, "
                "and you can switch between them with the button in the upper "
                "right of the main {name} window."
                "\nEither window allows you to run reports."
                "").format(name=self.program.name)
        url='{}/TASKS.md'.format(self.program.docsurl)
        webtext=_("For more information on {name} tasks, please check out the "
                "documentation at {url} ").format(name=self.program.name,url=url)
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
        title=(_("{azt} Dictionary and Orthography Checker").format(azt=self.program.name))
        window=ui.Window(self, title=title)
        version=self.program.version
        ui.Label(window.frame,
                text=_("version: {version}").format(version=version),
                anchor='c',padx=50,
                row=1,column=0,sticky='we'
                        )
        versiondate=_("updated to {date} ({relative_date})").format(
                        date=self.program.repo.lastcommitdate(),
                        relative_date=self.program.repo.lastcommitdaterelative())
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
                                                    name=self.program.name)
        webtext=_("For help with this tool, please check out the documentation "
                "at {url} ").format(url=self.program.url)
        mailtext=_("or write me at {email}.").format(email=self.program.Email)
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
        webl.bind("<Button-1>", lambda e: openweburl(self.program.url))
        ui.ToolTip(webl, _("See {azt} online").format(azt=self.program.name))
        murl='mailto:{}?subject= {} question'.format(self.program.Email,
                                                    self.program.name)
        maill.bind("<Button-1>", lambda e: openweburl(murl))
        ui.ToolTip(maill, _("Send me an Email (from your mail client)"))
    def reverttomainazt(self,event=None):
        #This doesn't care which (test) version one is on
        r=self.program.repo.reverttomain()
        log.info("reverttomainazt: {}".format(r))
        self.updateazt()
        if r:
            self.program.taskchooser.restart()
    def trytestazt(self,event=None):
        #This only goes to the test version at the top of this file
        r=self.program.repo.testversion()
        log.info("trytestazt: {}".format(r))
        self.updateazt()
        if r:
            self.program.taskchooser.restart()
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
        if getattr(self.parent,'is_sort_task',False):
            self.parameterslice()
    def fill_db_images(self):
        w=ui.Wait(self.program.tk_root,msg=_("Filling images..."))
        try:
            for p in self.program.db.fill_db_images(do_wait=True):
                w.progress(p)
        except Exception as e:
            log.error(f"Error filling images: {e}")
        w.close()
    def languages(self):
        """Language stuff"""
        self.cascade(self.changemenu,_("Languages"),'languagemenu')
        for m in [("Interface/computer language", self.program.ui_settings.getinterfacelang),
                    ("Analysis language",self.program.ui_settings.getanalang),
                    ("Analysis language Name",self.program.ui_settings.getanalangname),
                    ("Gloss language",self.program.ui_settings.getglosslang),
                    ("Another gloss language",self.program.ui_settings.getglosslang2)]:
            self.command(self.languagemenu,
                        label=_(m[0]),
                        cmd=m[1]
                        )
        """Word/data choice stuff"""
    def parameterslice(self):
        for m in [("Part of speech", self.program.ui_settings.getps),
                    ("Consonant-Vowel-Tone", self.program.ui_settings.getcvt),
                    ]:
            self.command(self.changemenu,
                        label=_(m[0]),
                        cmd=m[1]
                        )
        self.cascade(self.changemenu,_("Syllable profile"),'profilemenu')
        for m in [("Next", self.parent.status.nextprofile),
                    ("Choose", self.program.ui_settings.getprofile),
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
        if self.program.me:
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
                            self.program.taskchooser.changedatabase),
                (_("Digraph and Trigraph settings"),
                            self.program.settings.askaboutpolygraphs),
                (_("Segment Interpretation Settings"),
                            self.program.ui_settings.setSdistinctions),
                (_("Remake Status file (All: several minutes)"),
                            self.program.settings.reloadstatusdata),
                (_("Remake Status file (just this category)"),
                            self.program.settings.reloadstatusdatabycvtps),
                (_("Remake Status file (just this profile)"),
                        self.program.settings.reloadstatusdatabycvtpsprofile),
                (_("Fill CAWL Images"), self.fill_db_images),
                ]
        for m in options:
            self.command(self.advancedmenu,
                        label=_(m[0]),
                        cmd=m[1]
                        )
        if getattr(self.parent,'is_sound_task',False):
            self.sound()
        if getattr(self.parent,'is_sort_task',False):
            self.sort()
    def sound(self):
        self.advancedmenu.add_separator()
        options=[(_("Sound Settings"),
                self.parent.soundcheck),]
        if getattr(self.parent,'is_record_task',False):
            options+=[(_("Number of Examples to Record"),
                    self.program.taskchooser.getexamplespergrouptorecord),]
            # self.record()
        for m in options:
            self.command(self.advancedmenu,
                    label=_(m[0]),
                    cmd=m[1]
                    )
    def record(self):
        self.advancedmenu.add_separator()
        options=[(_("Number of Examples to Record"),
                self.program.taskchooser.getexamplespergrouptorecord),]
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
        if getattr(self.parent,'is_sort_tone_task',False):
            options.extend([(_("Add Tone frame"), self.parent.addframe)])
        group=self.program.status.group()
        if not group:
            group=_("Select")
        glyph=self.program.alphabet.glyph()
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
        from main import updateazt
        self.cascade(self,_("Help"),'helpmenu')
        helpitems=[(_("About"), self.parent.helpabout)]
        if self.program.git:
            # clonetoUSB should be called if updateazt doesn't have a source (incl internet)
            helpitems+=[(_("Update {azt}").format(azt=self.program.name), updateazt)]
            if 'git' in self.program.data_repo:
                helpitems+=[(_("Share data to USB"), self.program.data_repo['git'].share)]
            if self.program.repo.branch == 'main':
                helpitems+=[(_("Try {azt} test version").format(azt=self.program.name),
                                self.parent.trytestazt)]
            else:
                helpitems+=[(_("Revert to {azt} main version").format(azt=self.program.name),
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
        # if isinstance(parent,TaskDressing):
        if not parent.is_chooser:
            self.advanced()
        self.help()
        if self.program.me:
            self.command(self,self.program.taskchooser.filename,None)

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
                        wraplength=int(self.program.tk_root.wraplength/4),
                        **kwargs)
        if ttt:
            tt=ui.ToolTip(b,ttt)
        return b
    """These functions point to self.program.taskchooser functions, betcause we don't
    know who this frame's parent is"""
    def makeproseframe(self):
        if hasattr(self,'proseframe'):
            self.proseframe.destroy()
        self.proseframe=ui.Frame(self,row=0,column=0,sticky='nw')
    def updateinterfacelang(self):
        if 'interfacelang' not in self.labels:
            return
        self.labels['interfacelang']['text'].set(self.interfacelanglabel())
    def interfacelanglabel(self):
        # for l in self.program.taskchooser.interfacelangs:
        #     if l['code']==self.program.interfacelang():
        #         interfacelanguagename=l['name']
        return (_("Using {lang}").format(lang=self.program.settings.languagenames[self.program.interfacelang()]))
    def interfacelangline(self):
        self.labels['interfacelang']={
                        'text':self.program.settings.get_ui_var('interfacelang_label', self.interfacelanglabel()),
                        'columnplus':1,
                        'cmd':self.program.ui_settings.getinterfacelang,
                        'tt':_("change the interface language")}
        self.proselabel(**self.labels['interfacelang'])
    def updateanalang(self):
        if 'analangline' not in self.labels:
            return
        self.labels['analangline']['text'].set(self.analanglabel())
    def analanglabel(self):
        analang=self.program.params.analang()
        langname=self.program.settings.languagenames[analang]
        return (_("Studying {lang}").format(lang=langname))
    def analangline(self):
        self.newrow()
        if self.program.params.analang() not in self.program.settings.languagenames:
            cmd=self.program.ui_settings.getanalangname
            tt=_("Set analysis language Name")
        else:
            cmd=self.program.ui_settings.getanalang
            tt=_("Change analysis language")
        self.labels['analangline']={
                                'text':self.program.settings.get_ui_var('analang_label', self.analanglabel()),
                                'columnplus':1,
                                'cmd':cmd,
                                'tt':tt}
        self.proselabel(**self.labels['analangline'])
    def updateglosslangs(self):
        if 'glosslang' not in self.labels:
            return
        self.labels['glosslang']['text'].set(self.glosslanglabel())
        self.labels['glosslang2']['text'].set(self.glosslanglabel2())
    def glosslanglabel(self):
        lang=self.program.settings.glosslangs.lang1()
        return (_("Meanings in {lang}").format(lang=self.program.settings.languagenames[lang]))
    def glosslanglabel2(self):
        if len(self.program.settings.glosslangs) >1:
            glosslang2=self.program.settings.glosslangs.lang2()
            return (_("and {lang}").format(lang=self.program.settings.languagenames[glosslang2]))
        else:
            return _("only")
    def glosslangline(self):
        self.newrow()
        line=ui.Frame(self.proseframe,row=self.irow,column=0,
                        columnspan=3,sticky='w') #3 cols is the width of frame
        self.labels['glosslang']={'text':self.program.settings.get_ui_var('glosslang_label', self.glosslanglabel()),
                                'columnplus':1,
                                # 'rowplus':1,
                                'cmd':self.program.ui_settings.getglosslang,
                                'parent':line,
                                'tt':_("change this gloss language")
                                    if len(self.program.settings.glosslangs) >1
                                    else _("change this glosslang")
                                    }
        self.proselabel(**self.labels['glosslang'])
        self.labels['glosslang2']={'text':self.program.settings.get_ui_var('glosslang2_label', self.glosslanglabel2()),
                                'columnplus':1,
                                'cmd':self.program.ui_settings.getglosslang2,
                                'parent':line,
                                'tt':_("add another gloss language")}
        self.proselabel(**self.labels['glosslang2'])
    def updatefields(self):
        for ps in [self.program.settings.nominalps, self.program.settings.verbalps]:
            if 'fields'+ps in self.labels:
                self.labels['fields'+ps]['text'].set(self.fieldslabel(ps))
    def fieldslabel(self,ps):
        if ps in self.program.settings.secondformfield:
            field=self.program.settings.secondformfield[ps]
        else:
            field='<unset>'
        return (_("Using second form field '{field}' ({ps})").format(field=field, ps=ps))
    def fieldsline(self):
        # log.info("Starting fieldsline w/self {} ({})".format(self,type(self)))
        # log.info("Starting fieldsline w/task {} ({})".format(self.task,
        #                                                     type(self.task)))
        for ps in [self.program.settings.nominalps, self.program.settings.verbalps]:
            if not ps:
                continue
            self.newrow()
            line=ui.Frame(self.proseframe,row=self.irow,column=0,
                            columnspan=3,sticky='w') #3 cols is the width of frame
            # These shouldn't need to be updated:
            if ps == self.program.settings.nominalps:
                cmd=self.program.ui_settings.getsecondformfieldN
            else:
                cmd=self.program.ui_settings.getsecondformfieldV
            if ps not in self.program.settings.secondformfield and (
                    self.program.task.uses_second_forms or ( #Parse
                        self.program.task.ftype not in ['lx','lc'])):
                cmd() #Make sure these are defined where needed (i.e., parsing or collecting them.)
                # return #just do one at a time
            self.labels['fields'+ps]={
                            'text':self.program.settings.get_ui_var('fields'+ps+'_label', self.fieldslabel(ps)),
                            'columnplus':1,
                            'cmd':cmd,
                            'parent':line,
                            'tt':_("change this field")}
            self.proselabel(**self.labels['fields'+ps])
    def updateprofile(self):
        if 'profile' not in self.labels:
            return
        self.labels['profile']['text'].set(self.profilelabel())
        self.labels['ps']['text'].set(self.pslabel())
    def profilelabel(self):
        profile=self.program.slices.profile()
        if not profile:
            profile=_("<no syllable profile>")
        return (_("Looking at {profile}").format(profile=profile))
    def updateps(self):
        if 'ps' not in self.labels:
            return
        self.labels['ps']['text'].set(self.pslabel())
        self.makesliceattrs()
    def pslabel(self):
        count=self.program.slices.count()
        ps=self.program.slices.ps()
        if not ps:
            ps=_("<no grammatical category>")
        return (_("{ps} words ({count})").format(ps=ps, count=count))
    def sliceline(self):
        self.newrow()
        line=ui.Frame(self.proseframe,row=self.irow,column=0,
                        columnspan=3,sticky='w')
        self.labels['profile']={'text':self.program.settings.get_ui_var('profile_label', self.profilelabel()),
                                'columnplus':1,
                                'rowplus':1,
                                'cmd':self.program.ui_settings.getprofile,
                                'parent':line,
                                'tt':_("change this syllable profile")}
        self.proselabel(**self.labels['profile'])
        self.labels['ps']={'text':self.program.settings.get_ui_var('ps_label', self.pslabel()),
                                'columnplus':1,
                                'cmd':self.program.ui_settings.getps,
                                'parent':line,
                                'tt':_("change this grammatical category")}
        self.proselabel(**self.labels['ps'])
    def updatecvt(self):
        if 'cvt' not in self.labels:
            return
        self.labels['cvt']['text'].set(self.cvtlabel())
        self.makesliceattrs()
    def cvtlabel(self):
        return (_("Checking {cvt},").format(cvt=self.program.params.cvtdict()[self.cvt]['pl']))
    def cvtline(self):
        self.newrow()
        line=ui.Frame(self.proseframe,row=self.irow,column=0,
                        columnspan=3,sticky='w')
        self.labels['cvt']={'text':self.program.settings.get_ui_var('cvt_label', self.cvtlabel()),
                                'columnplus':1,
                                'rowplus':1,
                                'cmd':self.program.ui_settings.getcvt,
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
        if 'toneframe' not in self.labels:
            return
        self.labels['toneframe']['text'].set(self.toneframelabel())
    def toneframelabel(self):
        """this label follows a comma, so no caps"""
        checks=self.program.status.checks()
        check=self.program.params.check()
        if not checks:
            return _("no tone frames defined.")
        elif check not in checks:
            return _("no tone frame selected.")
        else:
            return (_("working on '{check}' tone frame").format(check=check))
    def toneframe(self,line):
        # log.info("toneframes: {}".format(self.program.toneframes))
        # log.info("maketoneframes: {}".format(self.program.toneframes))
        # log.info("checks: {}; check: {}".format(getattr(self,'checks'),
        #                                         getattr(self,'check')))
        self.labels['toneframe']={'text':self.program.settings.get_ui_var('toneframe_label', self.toneframelabel()),
                                'columnplus':1,
                                'cmd':self.program.task.getcheck,
                                'parent':line,
                                'tt':_("change this tone frame")}
        self.proselabel(**self.labels['toneframe'])
    def updatetonegroup(self):
        if 'tonegroup' not in self.labels:
            return
        self.labels['tonegroup']['text'].set(self.tonegrouplabel())
    def tonegrouplabel(self):
        if None in [self.program.params.check(), self.program.status.group()]:
            self.program.params.check(), self.program.status.group()
            return _("(no framed group)")
        else:
            return (_("(framed group: '{group}')").format(group=self.program.status.group()))
    def tonegroup(self,line):
        check=self.program.params.check()
        group=self.program.status.group()
        profile=self.program.slices.profile()
        # log.info("cvt: {}; check: {}".format(self.cvt,self.check))
        """Set appropriate conditions for each of these:"""
        if (not check or (check in self.program.status.checks(wsorted=True) and
            profile in self.program.status.profiles(wsorted=True))):
            cmd=self.program.task.getgroupwsorted
        elif (not check or (check in self.program.status.checks(tosort=True) and
            profile in self.program.status.profiles(tosort=True))):
            cmd=self.program.task.getgrouptosort
        elif (check in self.program.status.checks(toverify=True) and
            profile in self.program.status.profiles(toverify=True)):
            cmd=self.program.task.getgrouptoverify
        elif (check in self.program.status.checks(torecord=True) and
            profile in self.program.status.profiles(torecord=True)):
            cmd=self.program.task.getgrouptorecord
        else:
            cmd=None
        self.labels['tonegroup']={'text':self.program.settings.get_ui_var('tonegroup_label', self.tonegrouplabel()),
                                'columnplus':2,
                                'cmd':cmd,
                                'parent':line,
                                'tt':_("change this check")}
        self.proselabel(**self.labels['tonegroup'])
    def updatecvcheck(self):
        if 'cvcheck' not in self.labels:
            return
        self.labels['cvcheck']['text'].set(self.cvchecklabel())
    def cvchecklabel(self):
        return (_("working on {check}").format(check=self.program.params.cvcheckname()))
    def cvcheck(self,line):
        self.labels['cvcheck']={'text':self.program.settings.get_ui_var('cvcheck_label', self.cvchecklabel()),
                                'columnplus':1,
                                'cmd':self.program.task.getcheck,
                                'parent':line,
                                'tt':_("change this check")}
        self.proselabel(**self.labels['cvcheck'])
    def updatecvgroup(self):
        if 'cvgroup' not in self.labels:
            return
        self.labels['cvgroup']['text'].set(self.cvgrouplabel())
    def cvgrouplabel(self):
        if not self.program.params.check() or 'x' in self.program.params.check():
            return
        if self.program.status.group():
            return (f"= {self.program.status.group()}")
        else:
            return (_("(All groups)"))
    def cvgroup(self,line):
        self.labels['cvgroup']={'text':self.program.settings.get_ui_var('cvgroup_label', self.cvgrouplabel()),
                                'columnplus':2,
                                'cmd':self.program.task.getgroup,
                                'parent':line,
                                'tt':_("change this group")
                                if self.program.status.group()
                                else _("specify one group")
                                }
        self.proselabel(**self.labels['cvgroup'])
    def updatebuttoncolumns(self):
        if 'buttoncolumns' not in self.labels:
            return
        self.labels['buttoncolumns']['text'].set(self.buttoncolumnslabel())
    def buttoncolumnslabel(self):
        b=self.program.settings.buttoncolumns
        if b:
            return (_("Using {n} button columns").format(n=b))
        else:
            return (_("Not using multiple button columns"))
    def buttoncolumnsline(self):
        # log.info(t)
        tt=_("Click here to change the number of columns used for sort buttons")
        self.newrow()
        self.labels['buttoncolumns']={'text':self.program.settings.get_ui_var('buttoncolumns_label', self.buttoncolumnslabel()),
                                'columnplus':1,
                                'cmd':self.program.ui_settings.getbuttoncolumns,
                                'tt':tt}
        self.proselabel(**self.labels['buttoncolumns'])
    def updatemaxprofiles(self):
        if 'maxes' not in self.labels:
            return
        self.labels['maxes']['text'].set(self.maxprofileslabel())
    def maxprofileslabel(self):
        return (_("Max profiles: {max_profiles}; ").format(max_profiles=self.program.settings.maxprofiles))
    def updatemaxpss(self):
        if 'maxes' not in self.labels:
            return
        self.labels['maxes']['text'].set(self.maxpsslabel())
    def maxpsslabel(self):
        return (_("Max lexical categories: {max_pss}").format(max_pss=self.program.settings.maxpss))
    def maxes(self):
        self.newrow()
        line=ui.Frame(self.proseframe,row=self.irow,column=0,
                        columnspan=3,sticky='w')
        self.labels['maxprofiles']={
                        'text':self.program.settings.get_ui_var('maxprofiles_label', self.maxprofileslabel()),
                        'columnplus':1,
                        'cmd':self.program.ui_settings.getmaxprofiles,
                        'parent':line,
                        'tt':_("change this max")}
        self.proselabel(**self.labels['maxprofiles'])
        self.opts['columnplus']=1
        self.labels['maxpss']={'text':self.program.settings.get_ui_var('maxpss_label', self.maxpsslabel()),
                                'columnplus':1,
                                'cmd':self.program.ui_settings.getmaxpss,
                                'parent':line,
                                'tt':_("change this check")}
        self.proselabel(**self.labels['maxpss'])
    def updatemulticheckscope(self):
        if 'cvgroup' not in self.labels:
            return
        self.labels['cvgroup']['text'].set(self.multicheckscopelabel())
    def multicheckscopelabel(self):
        t=(_("Run all checks for {checks}").format(checks=unlist(self.program.ui_settings.cvtstodoprose())))
    def multicheckscope(self):
        if not hasattr(self.program.task,'cvtstodo'):
            self.program.task.cvtstodo=['V']
        self.newrow()
        line=ui.Frame(self.proseframe,row=self.irow,column=0,
                        columnspan=3,sticky='w')
        self.labels['multicheckscope']={
                        'text':self.program.settings.get_ui_var('multicheckscope_label', self.multicheckscopelabel()),
                        'columnplus':1,
                        'cmd':self.program.ui_settings.getmulticheckscope,
                        'parent':line,
                        'tt':_("change this check")}
        self.proselabel(**self.labels['multicheckscope'])
    def updateparserasklevel(self):
        if 'parserasklevel' not in self.labels:
            return
        self.labels['parserasklevel']['text'].set(self.parserasklevellabel())
    def parserasklevellabel(self):
        try:
            ls=self.program.task.parser.levels() # we need this anyway, and a parser test
            return (_("Parse with confirmation at {parser_levels}").format(parser_levels=ls[self.program.task.parser.ask]))
        except AttributeError as e:
            log.info(f"Error loading parser levels: {e}")
            return
    def updateparserautolevel(self):
        if 'parserautolevel' not in self.labels:
            return
        self.labels['parserautolevel']['text'].set(self.parserautolevellabel())
    def parserautolevellabel(self):
        try:
            ls=self.program.task.parser.levels()
            return (_("Parse automatically at {parser_levels}").format(parser_levels=ls[self.program.task.parser.auto]))
        except AttributeError as e:
            log.info(f"Error loading parser levels: {e}")
            return
    def parserlevels(self):
        self.newrow()
        line=ui.Frame(self.proseframe,row=self.irow,column=0,
                        columnspan=3,sticky='w')
        self.labels['parserasklevel']={
                        'text':self.program.settings.get_ui_var('parserasklevel_label', self.parserasklevellabel()),
                        'columnplus':1,
                        'cmd':self.program.task.getparserasklevel,
                        'parent':line,
                        'tt':_("change this confirmed parse level")}
        self.proselabel(**self.labels['parserasklevel'])
        self.newrow()
        line=ui.Frame(self.proseframe,row=self.irow,column=0,
                        columnspan=3,sticky='w')
        self.labels['parserautolevel']={
                        'text':self.program.settings.get_ui_var('parserautolevel_label', self.parserautolevellabel()),
                        'columnplus':1,
                        'cmd':self.program.task.getparserautolevel,
                        'parent':line,
                        'tt':_("change this auto parse level")}
        self.proselabel(**self.labels['parserautolevel'])
    def updatesensetodo(self):
        if 'sensetodo' not in self.labels:
            return
        self.labels['sensetodo']['text'].set(self.sensetodolabel())
    def sensetodolabel(self):
        t=self.program.task
        if hasattr(t,'sensetodo') and t.sensetodo is not None:
            return _("Parsing {sense}").format(sense=t.sensetodo.formatted(t.analang,t.glosslangs))
        else:
            return _("Parsing all words")
    def sensetodo(self):
        self.newrow()
        line=ui.Frame(self.proseframe,row=self.irow,column=0,
                        columnspan=3,sticky='w')
        self.labels['sensetodo']={
                            'text':self.program.settings.get_ui_var('sensetodo_label', self.sensetodolabel()),
                            'columnplus':1,
                            'cmd':self.program.task.getsensetodo,
                            'parent':line,
                            'tt':_("change this sense to do")}
        self.proselabel(**self.labels['sensetodo'])
    def redofinalbuttons(self):
        if hasattr(self,'bigbutton') and self.bigbutton.winfo_exists():
            self.bigbutton.destroy()
        self.finalbuttons()
    def finalbuttons(self):
        # self.opts['row']+=6
        if self.is_descendant_of(self.program.taskchooser):
            return
        self.newrow()
        # log.info(f"{self.is_descendant_of(self.program.taskchooser)=}")
        try:
            # log.info(f"{self.program.mainwindow=}")
            # assert not self.program.mainwindow.is_chooser
            # log.info(f"{self.program.task=}")
            kwargs=self.program.task.dobuttonkwargs()
            self.bigbutton=self.button(**kwargs)
        # except AssertionError:
        #     pass
        except Exception as e:
            log.error(f"Problem: {e}")
    def makesecondfieldsOK(self):
        """Not called anywhere?"""
        for ps in [self.program.settings.nominalps, self.program.settings.verbalps]:
            if ps not in self.program.settings.secondformfield and (
                isinstance(self.program.task,Parse) or (
                    isinstance(self.program.task,WordCollection) and
                    self.type not in ['lx','lc'])):
                if ps == self.program.settings.nominalps:
                    self.program.ui_settings.getsecondformfieldN()
                else:
                    self.program.ui_settings.getsecondformfieldV()
                return #just do one at a time
    """Right side"""
    def maybeboard(self):
        if hasattr(self,'leaderboard') and type(self.leaderboard) is ui.Frame:
            self.leaderboard.destroy()
        self.leaderboard=ui.Frame(self,row=0,column=1,sticky='') #nesw
        #Given the line above, much of the below can go, but not all?
        if self.program.task.no_leaderboard:
            return
        if self.program.task.icon_leaderboard or not self.program.taskchooser.doneenough['collectionlc']:
            self.makenoboard()
            return
        if self.program.task.glyph_leaderboard:
            self.makeglyphtable()
            return
        profileori=self.program.slices.profile()
        self.program.status.cull() #remove nodes with no data
        if self.cvt in self.program.status:
            if self.ps in self.program.status[self.cvt]: #because we cull, this == data is there.
                if self.cvt == 'T':
                    if self.ps in self.program.toneframes:
                        self.makeprogresstable()
                        return
                    else:
                        log.info("Ps {} not in toneframes ({})".format(self.ps,
                                self.program.toneframes))
                else:
                    self.makeprogresstable()
                    return
        else:
            log.info("cvt {} not in status {}".format(self.cvt,
                                                            self.program.status))
        self.makenoboard()
    def boardtitle(self):
        titleframe=ui.Frame(self.leaderboard)
        titleframe.grid(row=0,column=0,sticky='n')
        cvtdict=self.program.params.cvtdict()
        ui.Label(titleframe, text=_('Progress for'), font='title',
                row=0,column=1,sticky='nwe',padx=10)
        if not self.mainrelief:
            lps=ui.Label(titleframe,text=self.ps,anchor='c',font='title')
        else:
            lps=ui.Button(titleframe,text=self.ps, anchor='c',
                            relief=self.mainrelief, font='title')
        lps.grid(row=0,column=2,ipadx=0,ipady=0)
        ttps=ui.ToolTip(lps,_("Change Part of Speech"))
        lps.bind('<ButtonRelease-1>',self.program.ui_settings.getps)
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
        fn=lambda x=glyph:self.program.task.makewindow(x)
        bf=SortGlyphGroupButtonFrame(f, self.program.task,
                                    group=glyph,
                                    on_select=fn,
                                    column=1, sticky="W")
        if not bf.hasexample:
            log.info(f"deleting empty button for '{glyph}'")
            l.destroy()
            bf.destroy()
    def makeglyphtable(self):
        self.glyphscroll=ui.ScrollingFrame(self.leaderboard,row=1,column=0)
        self.glyphbuttons={}
        self.updateglyphbuttons()
    def updateglyphbuttons(self):
        """This ultimately should cover all C or V, across checks and
        ps-profiles"""
        # groups=self.program.status.all_groups_verified_for_cvt()
        groups=set(self.program.alphabet.glyphs())
        for k in set(self.glyphbuttons)-groups:
            self.glyphbuttons[k].destroy()
        for k in groups-set(self.glyphbuttons):
            self.makeglyphbutton(k)
    def activate_cell(self,cell):
        cell.inactive_background=cell['background'] #store for deactivate
        cell.inactive_command=cell['command'] #store for deactivate
        cell.configure(background=cell['activebackground'])
        cell.configure(command=donothing)
        self._active_cell=cell
    def deactivate_cell(self,cell):
        cell.configure(background=cell.inactive_background)
        cell.configure(command=cell.inactive_command)
    def updateprofilencheck(self,profile,check):
        new_cell=self._cells.get((profile,check))
        if new_cell and new_cell.winfo_exists():
            if self._active_cell and self._active_cell.winfo_exists():
                self.deactivate_cell(self._active_cell)
            self.activate_cell(new_cell)
        self.program.slices.profile(profile)
        self.program.params.check(check)
        self.updateprofile()
        if self.program.params.cvt() == 'T':
            self.updatetoneframe()
        else:
            self.updatecvcheck()
    def makeprogresstable(self):
        def groupfn(x):
            for i in x:
                try:
                    int(i)
                    # log.info("Integer {} fine".format(i))
                except:
                    # log.info("Problem with integer {}".format(i))
                    if self.program.settings.showdetails:
                        return nn(x,oneperline=True) #if any noninteger, all.
            return len(x) #to show counts only
        def refresh(event=None):
            # log.info("refreshing status table")
            self.program.settings.storesettingsfile()
            self.program.task.tableiteration+=1
        self._cells={}
        self._active_cell=None
        self.boardtitle()
        # leaderheader=Frame(self.leaderboard) #someday, make this not scroll...
        # leaderheader.grid(row=1,column=0)
        leaderscroll=ui.ScrollingFrame(self.leaderboard)
        leaderscroll.grid(row=1,column=0)
        self.leaderboardtable=leaderscroll.content
        row=0
        #put in a footer for next profile/frame
        cvt=self.program.params.cvt()
        ps=self.program.slices.ps()
        max_visible_profile_length=20
        allprofiles=self.program.slices.profiles()
        profiles=[i for i in allprofiles if len(i)<=max_visible_profile_length] #just sort here
        if skipped:=set(allprofiles)-set(profiles):
            log.error(f"Skipped insanely long profiles: {skipped}")
        curprofile=self.program.slices.profile()
        curcheck=self.program.params.check()
        # log.info("self.program.toneframes: {}".format(self.program.toneframes))
        try:
            frames=list(self.program.toneframes[ps].keys())
        except KeyError:
            frames=list()
        allchecks=self.program.status.allcheckswdata()
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
        if self.program.settings.showdetails:
            verified=_("verified")
            unsorted=_("unsorted")
            # t='+ = {} \n! = {}'.format(tv,tu)
            t=f"+ = {verified} \n{unsorted_icon} = {unsorted}"
            h=ui.Label(self.leaderboardtable,text=t,font='small')
            h.grid(row=row,column=0,sticky='e')
            h.bind('<ButtonRelease-1>', refresh)
            htip=_("Refresh table, \nsave settings")
            th=ui.ToolTip(h,htip)
        r=list(self.program.status[cvt][ps])
        # log.info("Table rows possible: {}".format(r))
        # log.info("Table columns possible: {}".format(allchecks))
        # log.info("toneframes possible: {}".format(frames))
        for profile in self.profiles: #keep this for later updates
            column=0
            if profile in ['colheader','next']+list(self.program.status[cvt][
                                                            ps].keys()):
                """header first"""
                if profile in self.program.status[cvt][ps]:
                    if self.program.status[cvt][ps][profile] == {}:
                        continue
                    #Make row header
                    t=profile
                    if self.program.settings.showdetails:
                        t+=(f" ({len(self.program.settings.profilesbysense[ps][profile])})")
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
                            relief='flat',cmd=self.program.settings.setprofile)
                    brh.grid(row=row,column=column,sticky='e')
                    brht=ui.ToolTip(brh,_("Go to the next syllable profile"))
                """then checks"""
                for check in self.checks+['next']:
                    column+=1
                    if profile == 'colheader':
                        if check == 'next': # end of column headers
                            # log.info("todo: {}".format(self.program.status.checks(todo=True)))
                            # log.info("tosort: {}".format(self.program.status.checks(tosort=True)))
                            # log.info("toverify: {}".format(self.program.status.checks(toverify=True)))
                            # log.info("tojoin: {}".format(self.program.status.checks(tojoin=True)))
                            if cvt == 'T' and not (
                                    self.program.status.checks(todo=True)
                                                    ):
                                cmd=self.program.task.addframe
                            else:
                                cmd=lambda todo=True:self.program.settings.setcheck(
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
                                        self.program.ui_settings.getcvt)
                    elif profile == 'next':
                        continue
                    elif check in self.program.status.checks(cvt=cvt,ps=ps,
                                                            profile=profile):
                        node=self.program.status.node(cvt=cvt,ps=ps,
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
                                self.program.settings.showdetails): #these should go together
                            donenum=unsorted_icon #don't say '0'
                        elif not totalnum and tosort:
                            donenum=''
                        elif (not self.program.settings.showdetails or
                            (type(totalnum) is int and type(donenum) is int)):
                            # donenum='{}/{}'.format(donenum,totalnum)
                            donenum=totalnum
                        else:
                            donenum=nn(totalwverified,oneperline=True)
                        if (tosort and totalnum and self.program.settings.showdetails):
                            donenum=str(donenum)+'\n'+unsorted_icon
                        tb=ui.Button(self.leaderboardtable,
                                relief='flat',
                                bd=0, #border
                                text=donenum,
                                cmd=lambda p=profile,
                                f=check:self.updateprofilencheck(profile=p, check=f),
                                anchor='c',
                                padx=0,pady=0
                                )
                        self._cells[(profile,check)]=tb
                        tips=[]
                        if tosort:
                            tips.extend([_("Words to sort!")])
                            if not self.program.settings.showdetails:
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
        # if profile == curprofile and check == curcheck:
        self.activate_cell(self._cells[(curprofile,curcheck)])
        if ungroups > 0:
            log.error(_("You have more groups verified than there are, in {count} "
                        "cells").format(count=ungroups))
        # self.frame.update()
    def __init__(self, parent, program, **kwargs):
        # log.info("Remaking status frame")
        self.setopts()
        self.irow=0 #frame internal rows
        self.parent=parent
        self.program=program
        # self.task=program.task #this is the window that called it; task or chooser
        self.mainrelief=kwargs.pop('relief',None) #not for frame
        self.labels={} #make a place to store these
        kwargs['padx']=25
        kwargs['gridwait']=True
        super(StatusFrame, self).__init__(parent, **kwargs)
        self.makeui()
    def makesliceattrs(self):
        if not isinstance(self.program.task,WordCollection):
            self.cvt=self.program.params.cvt()
            self.ps=self.program.slices.ps()
            self.profile=self.program.slices.profile()
            self.check=self.program.params.check()
            self.checks=self.program.status.checks()
    def makeui(self):
        self.makeproseframe()
        self.interfacelangline()
        self.analangline()
        self.glosslangline()
        # if isinstance(self.task,Segments) and not isinstance(self.task,TranscribeS):
        if not self.program.task or self.program.task.is_chooser:
            return
        if getattr(self.program.task,'show_second_fields'):
            self.fieldsline()
        if (hasattr(self.program, 'slices') and
                not getattr(self.program.task,'do_not_show_slices')):
                # isinstance(self.task,(TaskChooser,
                #                             Parse,
                #                             TranscribeS,
                #                             WordCollection))
                # ):
            self.makesliceattrs()
            if getattr(self.program.task,'multislice_max'):
            # if isinstance(self.task,Multislice): #any cvt
                self.maxes()
            else:
                self.sliceline()
            if getattr(self.program.task,'multicheck_scope'):
            # isinstance(self.task,Multicheck): #segments only
                self.multicheckscope()
            elif not getattr(self.program.task,'do_not_show_cvt'):
                # not (isinstance(self.task,ReportCitationT) or
                #         isinstance(self.task,JoinUFgroups)
                #         ):
                self.cvtline()
            if getattr(self.program.task,'show_buttoncolumnsline'):
                # isinstance(self.task,Sort) and not isinstance(self.task,Transcribe):
                self.buttoncolumnsline()
        if getattr(self.program.task,'show_parser_ui'):
            self.parserlevels()
            self.sensetodo()
        self.maybeboard()
        self.finalbuttons()

    def update_all_labels(self):
        """Update all reactive StringVar labels in the status frame."""
        self.updateinterfacelang()
        self.updateanalang()
        self.updateglosslangs()
        self.updatefields()
        self.updateprofile()
        self.updateps()
        self.updatecvt()
        self.updatetoneframe()
        self.updatetonegroup()
        self.updatecvcheck()
        self.updatecvgroup()
        self.updatebuttoncolumns()
        self.updatemaxprofiles()
        self.updatemaxpss()
        self.updatemulticheckscope()
        self.updateparserasklevel()
        self.updateparserautolevel()
        self.updatesensetodo()
        # self.maybeboard()
        # self.redofinalbuttons()

class TaskDressing(HasMenus,ui.Window):
    """This Class covers elements that belong to (or should be available to)
    all tasks, e.g., menus and button appearance."""
    taskicon = 'icon'
    tasktitle = None
    def _taskchooserbutton(self):
        if self.is_chooser and not self.showreports:
            if self.datacollection:
                text=_("Analyze & Decide")
            else:
                text=_("Collect Data")
        elif self.is_report:
            text=_("Reports")
            self.program.taskchooser.showreports=True
        else:
            text=_("Tasks")
        if hasattr(self,'chooserbutton'):
            self.chooserbutton.destroy()
        self.chooserbutton=ui.Button(self.outsideframe,text=text,
                                    font='small',
                                    cmd=self.program.taskchooser.gettask,
                                    row=0,column=2,
                                    sticky='ne')
    def shutdowntask(self):
        self.program.task=self # in case this hasn't been set yet
        self.withdraw()
        self.program.taskchooser.gettask()
    def mainlabelrelief(self,relief=None,refresh=False,event=None):
        #set None to make this a label instead of button:
        reliefs=["raised", "groove", "sunken", "ridge", "flat"]
        if self.mainrelief and self.mainrelief in reliefs:
            self.program.taskchooser.mainreliefnext=\
            self.program.task.mainreliefnext=\
            self.mainreliefnext=reliefs[(reliefs.index(self.mainrelief)+1
                                                            )%len(reliefs)]
        log.info(_("setting button relief to {relief}, with refresh={refresh}").format(relief=relief,
                                                                    refresh=refresh))
        # None "raised" "groove" "sunken" "ridge" "flat"
        self.status.mainrelief=\
        self.program.taskchooser.mainrelief=\
        self.program.task.mainrelief=\
        self.mainrelief=relief
    def _showbuttons(self,event=None):
        todo=getattr(self,'mainreliefnext','flat')
        self.mainlabelrelief(relief=todo,refresh=True)
        self.program.mainwindow.status.makeui()
        self.setcontext()
    def _hidebuttons(self,event=None):
        self.mainlabelrelief(relief=None,refresh=True)
        self.program.mainwindow.status.makeui()
        self.setcontext()
    def correlatemenus(self):
        """I don't think I want this. Rather, menus must always be asked for."""
        log.info(_("Menus: {menu}; {chooser_menu} (chooser)").format(menu=self.menu,chooser_menu=self.program.taskchooser.menu))
        if hasattr(self,'task'):
            log.info(_("Menus: {menu}; {task_menu} (task)").format(menu=self.menu,task_menu=self.task.menu))
        if self.menu != self.program.taskchooser.menu: #for tasks
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
        self.program.settings.set('showdetails', False, refresh=True)
        self.program.mainwindow.status.maybeboard()
        self.setcontext()
    def _showdetails(self):
        # log.info("Showing group names")
        self.program.settings.set('showdetails', True, refresh=True)
        self.program.mainwindow.status.maybeboard()
        self.setcontext()
    def setcontext(self,context=None):
        if self.exitFlag.istrue() or not self.winfo_exists():
            return
        self.context.menuinit() #This is a ContextMenu() method
        if self.program.me:
            self.context.menuitem(_("Change to another Database (Restart)"),
                            self.program.taskchooser.changedatabase)
        if 'git' in self.program.data_repo:
            self.context.menuitem(_("Share data to USB"), 
                                self.program.data_repo['git'].share)
        if not hasattr(self,'menu') or not self.menu:
            self.context.menuitem(_("Show Menus"),self._setmenus)
        else:
            self.context.menuitem(_("Hide Menus"),self._removemenus)
        if hasattr(self.program.taskchooser,'mainrelief') and not self.program.taskchooser.mainrelief:
            self.context.menuitem(_("Show Buttons"), self._showbuttons)
        else:
            self.context.menuitem(_("Hide Buttons"), self._hidebuttons)
        if hasattr(self,'fontthemesmall') and not self.fontthemesmall:
            self.context.menuitem(_("Smaller Fonts"),self.setfontssmaller)
        else:
            self.context.menuitem(_("Larger Fonts"),self.setfontsdefault)
        if getattr(self.program.settings, 'showdetails'):
            self.context.menuitem(_("Hide details"),self._hidedetails)
        else:
            self.context.menuitem(_("Show details"),self._showdetails)
    def _tasktitle(self):
        if callable(self.task.tasktitle):
            return self.task.tasktitle()
        if self.task.tasktitle:
            return _(self.task.tasktitle)
        return _("Unnamed {name} Task ({type})").format(
                                name=self.program.name,
                                type=type(self.task).__name__)
    def maketitle(self):
        title=_("{name} Dictionary and Orthography Checker: {task}").format(
                                            name=self.program.name,task=self._tasktitle())
        if self.program.theme.name != 'greygreen':
            log.info(_("Using theme '{theme}' on {task}.").format(theme=self.program.theme.name,
                                                        task=self._tasktitle()))
            title+=f' ({self.program.theme.name})'
        self.title(title)
        t=ui.Label(self.frame, font='title',
                text=self._tasktitle(),
                row=0, column=0, columnspan=2)
        tasks=_("Tasks")
        t.tt=ui.ToolTip(t,text=_("click on the task you want to do"))
        # t.bind("<Button-1>",self.program.taskchooser.gettask)
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
            if hasattr(self.program.settings,attr):
                setattr(self,attr,getattr(self.program.settings,attr))
            else:
                log.info(_("Didn't find {attr} in {settings}").format(attr=attr,settings=self.program.settings))
        # #For convenience:
        # self.analang=self.program.params.analang()
    def on_quit(self,**kwargs):
        # if hasattr(self, 'makestatusframe_after_id'):
        #     self.after_cancel(self.makestatusframe_after_id)
        if self.program.mainwindow is self:
            self.program.mainwindow=None #don't leave reference lying around
        super().on_quit(**kwargs)    
    def setmainwindow(self):
        # make an object reference, and a quick boolean:
        # no problem if self.program.mainwindow doesn't exist yet
        try:
            self.program.mainwindow.ismainwindow=False #keep only one of these
            self.program.mainwindow.withdraw() #until destroyed
        except AttributeError:
            pass
        self.program.mainwindow=self
        self.program.mainwindow.ismainwindow=True 
        # if not self.is_chooser:
        #     self.i_am_the_task()
    def makestatusframe(self,dict=None):
        if self.program.taskchooser.donew['collectionlc']:
            self.makeeverythingok()
        if self.exitFlag.istrue():
            return
        hidewhileworking=self.winfo_viewable()
        status=StatusFrame(self.frame, self.program,
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
        self.program.settings.storesettingsfile()
        log.info(_("{type} StatusFrame created").format(type=type(self)))
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
                                command=self.program.settings.setparserasklevel,
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
                                command=self.program.settings.setparserautolevel,
                                window=window,
                                column=0, row=1
                                            )
    def setsensetodo(self,choice,window):
        self.sense=self.sensetodo=choice
        self.program.mainwindow.status.updatesensetodo()
        window.destroy()
        task = getattr(self, 'task', self)
        if isinstance(task, WordCollection):
            self.withdraw()
            task.getword()
    def getsensetodobyletter(self,choice,window,event=None):
        window.on_quit()
        msg=_("Preparing to ask for a sense...")
        log.info(msg)
        senses=self.program.db.senses
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
        senses=self.program.db.senses
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
    def getcheck(self,guess=False,event=None,**kwargs):
        log.info(_("this sets the check"))
        log.info(_("Getting the check name..."))
        checks=self.program.status.checks(**kwargs)
        self.withdraw()
        window=ui.Window(self,title=_('Select Check'))
        window.withdraw()
        if not checks:
            if self.program.params.cvt() == 'T':
                btext=_("Define a New Tone Frame")
                text=_("You don't seem to have any tone frames set up.\n"
                "Click '{button}' below to define a tone frame. \nPlease "
                "pay attention to the instructions, and if \nthere's anything "
                "you don't understand, or if you're not \nsure what a tone "
                "frame is, please ask for help. \nWhen you are done making "
                "frames, click 'Exit' to continue.").format(button=btext)
                cmd=lambda w=window: self.addframe(window=w)
            else:
                btext=_("Return to {name}, to fix settings").format(name=self.program.name)
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
            self.program.status.makecheckok(**kwargs) #tosort=tosort,wsorted=wsorted)
            window.destroy() #never shown
            self.deiconify()
        else:
            log.info("Checks: {}".format(checks))
            if self.program.params.cvt() == 'T':
                checklist=checks
            else:
                checklist=[(c,self.program.params.cvcheckname(c)) for c in checks]
            text=_('What check do you want to do?')
            ui.Label(window.frame, text=text).grid(column=0, row=0)
            buttonFrame1=ui.ScrollingButtonFrame(window.frame,
                                    optionlist=checklist,
                                    command=self.program.settings.setcheck,
                                    window=window,
                                    column=0, row=4
                                    )
            count=len(buttonFrame1.bf.winfo_children())
            if self.program.params.cvt() == 'T':
                newb=ui.Button(buttonFrame1.bf,
                            text=_("New Frame"),
                            cmd=lambda w=window: self.addframe(window=w),
                            row=count+1)
            window.deiconify()
            buttonFrame1.wait_window(window)
            self.deiconify()
        """Make sure we got a value"""
        if self.program.params.check() not in checks:
            return 1
    def _getglyph(self,window,event=None, **kwargs):
        log.info(_("Asking for a group (_getglyph kwargs: {kwargs})").format(kwargs=kwargs))
        cvt=kwargs.get('cvt',self.program.params.cvt())
        if kwargs.get('toverify'):
            glyphs=self.program.alphabet.glyphdict()[cvt]
        else:
            glyphs=self.program.alphabet.glyphs()
        glyph=self.program.alphabet.glyph()
        purpose=kwargs.get('purpose','to work with')
        text=[_("What"),self.program.params.cvtdict()[cvt]['sg'],
                _("do you want {purpose}?").format(purpose=purpose)]
        if kwargs.get('comparison'):
            g2=list(glyphs)[:]
            g2.remove(self.program.alphabet.glyph())
            # log.info(f"_getglyph comparison options: {g2} ({type(g2)}))")
            if not g2:
                window.destroy()
                ErrorNotice(text=_("There don't seem to be any glyphs "
                            "to compare with!"))
                return
            optionlist=g2
            command=self.program.settings.setgroup_comparison
            text.insert(1,_("other"))
        else:
            optionlist=glyphs
            command=self.program.alphabet.glyph
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
        ps=kwargs.get('ps',self.program.slices.ps())
        cvt=kwargs.get('cvt',self.program.params.cvt())
        profile=kwargs.get('profile',self.program.slices.profile())
        check=kwargs.get('check',self.program.params.check())
        if (cvt == 'T' and None in [cvt, ps, profile, check]):
            ErrorNotice(parent=window.frame,
                          text=_("You need to set "
                          "\nCheck type (as Tone, currently {type}) "
                          "\nGrammatical category (currently {ps})"
                          "\nSyllable Profile (currently {profile}), and "
                          "\nTone Frame (currently {check})"
                          "\nBefore choosing a sort group!"
                          "").format(type=self.program.params.cvtdict()[cvt]['sg'], ps=ps,
                          profile=profile, check=check), column=0, row=0)
            return 1
        kwargs=grouptype(**kwargs) #this just fills in False
        groups=self.program.status.groups(cvt=cvt,**kwargs)
        if not groups:
            ErrorNotice(parent=window.frame,
                          text=_("It looks like you don't have {ps}-{profile} lexemes "
                          "grouped in the '{check}' check yet \n({kwargs})."
                          "").format(ps=ps,profile=profile,check=check,kwargs=kwargs), column=0, row=0)
            return
        if kwargs.get('intfirst') and kwargs.get('guess'):
            l=[int(i) for i in self.program.status.groups(cvt=cvt,**kwargs)
                                    if str(i).isdecimal()]
            if l:
                self.program.settings.setgroup(str(min(l)),window)
            else:
                self.program.status.nextgroup(cvt=cvt,**kwargs)
                window.destroy()
            return
        elif kwargs.get('guess') or (len(groups) == 1
                                        and not kwargs.get('comparison')):
            self.program.status.nextgroup(cvt=cvt,**kwargs)
            window.destroy()
            return
        cvt_name=self.program.params.cvtdict()[cvt]['sg']
        if kwargs.get('comparison'):
            g2=list(groups)
            g2.remove(self.program.status.group()) #group() is not cvt aware
            if not g2:
                window.destroy()
                ErrorNotice(text=_("There don't seem to be any groups "
                            "to compare with!"))
                return
            if len(g2) == 1:
                self.program.settings.setgroup_comparison(g2[0],window)
                return
            ui.Label(window.frame,
                      text=_(f"What {cvt_name} do you want to {purpose}?"),
                      column=0, row=0)
            buttonFrame1=ui.ScrollingButtonFrame(window.frame,
                            optionlist=g2,
                            command=self.program.settings.setgroup_comparison,
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
                                     command=self.program.settings.setgroup,
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
        cvt=kwargs.get('cvt',self.program.params.cvt())
        if cvt in ['V','C']:
            purpose_title=kwargs.get('purpose','').capitalize()
            cvt_name=self.program.params.cvtdict()[cvt]['sg']
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
        self.program.settings.refreshattributechanges()
        purpose_title=kwargs.get('purpose','').capitalize()
        cvt=kwargs.get('cvt',self.program.params.cvt())
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
                CV+=self.program.status.group()
            self.program.status.group(CV)
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
    def runwindowcleanup(self):
        log.info(_("Shutting down runwindow"))
        if not self.exitFlag.istrue():
            self.deiconify()
        if self.program.taskchooser.towrite:
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
        counts,ps_profile_counts=self.program.db.report_counts()
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
        from main import updateazt
        updateazt()
    def maybewrite(self,definitely=False):
        self.program.maybewrite(definitely=definitely)
    def killall(self):
        log.info(_("Shutting down Task"))
        try:
            towrite=self.program.taskchooser.towrite
        except AttributeError:
            towrite=self.towrite #if taskchooser; shouldn't happen, but in case.
        self.wait(msg=_("Closing down {name} and storing changes").format(
                                                                name=self.program.name
                                                                ))
        if towrite:
            log.info(_("Final write to lift"))
            self.maybewrite(definitely=True)
        else:
            log.info(_("No final write to lift"))
        self.program.settings.trackuntrackedfiles()
        self.waitdone() #Don't confuse user; there's more input to come, maybe
        for r in self.program.data_repo:
            self.program.data_repo[r].share()
            log.info(_("Done maybe committing/pushing to {repo}").format(repo=r))
        log.info(_("Saving settings for next time"))
        self.program.settings.storesettingsfile() #in case we added repos
        if getattr(self,'is_sound_task',False):
            self.program.settings.storesettingsfile(setting='soundsettings')
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
        log.info(_("Initializing TaskDressing for {task}").format(
                            task=self.task.__class__.__name__))
        self.parent=parent
        # self.program=parent.program should be set already
        self.menu=False #initialize once
        # if isinstance(self,TaskChooser):
        #     taskchooser=self
        # else:
        #     self.task=self
        #     taskchooser=self.parent
        #     self.program.status.task(self)
        # """Whenever this runs, it's the main window."""
        # taskchooser.mainwindowis=self
        """At some point, I need to think through which attributes are needed,
        and if I can get them all into objects, read/writeable with files."""
        """These are raw attributes from file"""
        """these are objects made by the task chooser"""
        # log.info(f"Ready to Inherit for {type(self)} ({program})")
        self.inherittaskattrs()
        # if hasattr(self,'task') and 
        if self.task.multicheck_scope:
            if hasattr(self.program.settings,'cvtstodo'):
                self.cvtstodo=self.program.settings.cvtstodo
            else:
                self.cvtstodo=['V']
        self.analang=self.program.params.analang() # Every task gets this here
        # super(TaskDressing, self).__init__(parent)
        for k in ['settings',
                    # 'menu',
                    'mainrelief','fontthemesmall',
                    'showdetails']:
            if not hasattr(self,k):
                    setattr(self,k,False)
        # Make the actual window
        ui.Window.__init__(self,parent,withdrawn=True)
        self.setmainwindow()
        self.maketitle()
        ui.ContextMenu(self)
        self.tableiteration=0
        self.makestatusframe()
        # self.withdraw() #made visible by chooser when complete
        self._taskchooserbutton()
        self._removemenus() #self.correlatemenus()
        self.takekioskscreen()
        self.thread_names=list()
        if not self.exitFlag.istrue():
            self.deiconify()
from frontend.sort_buttons import (SortButtonFrame, _GroupButtonFrame,
    SortGroupButtonFrame, SortGlyphGroupButtonFrame)
class ImageFrame(ui.Frame):
    """I need to remove class references from here where possible,
    and sort out a program reference"""
    def getimage(self,reload=False):
        """this converts self.url (str) to self.image (ui.Image)"""
        """reload allows the frame to be built once and reused;
        this may be with the same url (if user selected a new image 
        for the same sense)"""
        if not self.url:
            log.error("No url for ImageFrame")
            raise 
        if self.url in self.parent.theme.image_cache and not reload:
            self.image=self.parent.theme.image_cache[self.url]
        else:
            try:
                # log.info(_("trying to make image {image}").format(image=i))
                self.image=ui.Image(self.url)
                self.hasimage=True
                self.parent.theme.image_cache[self.url]=self.image
                # log.info(_("Image OK: {img}").format(img=img))
            except (tkinter.TclError,AttributeError) as e:
                if e.args and ('value for "-file" missing' not in e.args[0] and
                        "couldn't recognize data in image file" not in e.args[0]):
                    log.info(_("ui.Image error: {error}").format(error=e))
                log.info(f"No image for {self.sense}")
                self.image=self.theme.photo['NoImage'] #don't store!
                self.hasimage=False
        self.scale_image(pixels=self.pixels)
        # self.image=image.scaled #Imageframe.image = sense.image.scaled
    def scale_image(self,image=None,pixels=150,scaleto='height'):
        # This is here because ui.Image doens't have access to theme.scale
        if image is None:
            image=self.image
        image.scale(self.parent.theme.scale,pixels=pixels,scaleto=scaleto)
    def pluralframe(self):
        ui.Label(self,text='',image=self.image.scaled,
                compound='bottom',
                sticky='e',
                ipadx=10,
                row=0,column=0)
        ui.Label(self,text='',image=self.image.scaled,
                compound='bottom',
                sticky='w',
                ipadx=10,
                row=0,column=1)
    def imperativeframe(self):
        try:
            image1=self.program.theme.photo['Order!']
            self.scale_image(image=image1,pixels=300) #300 wide
            image2=self.image.scaled
            # log.info("image1.scaled: {} ({})".format(image1.scaled,type(image1.scaled)))
            # log.info("image2: {} ({})".format(image2,type(image2)))
            image1.scaled.paste(image2)
            bgl=ui.Label(verb,text='',image=image1.scaled,
                compound='center',
                sticky='ew',
                row=0,column=0)
        except:
            ui.Label(self,text='!',image=self.image.scaled,
                compound='left',sticky='ew',font='title',
                row=0,column=0)
    def citationframe(self):
        l=ui.Label(self,text='',image=self.image.scaled,
            compound='center',sticky='ew',
            anchor='center',
            row=0,column=0)
        # log.info(l.grid_info())
    def changeurl(self,url):
        if self.url != url:
            self.url=url
            self.reloadimage()
    def reloadimage(self):
        self.getimage(reload=True)
        for child in self.winfo_children():
            if isinstance(child,ui.Label):
                child['image']=self.image.scaled
    def __init__(self, parent, url, *args, **kwargs):
        """Parent: where it goes; url: what it shows"""
        """This is now called with url, not sense."""
        self.sense=sense #for sense.image only?
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
        self.labels['v']['text']=_("Version: {version}").format(version=self.program.version)
        self.labels['v2']['text']=_("updated to {date} ({date_rel})").format(date=self.program.source_repo.lastcommitdate(), date_rel=self.program.source_repo.lastcommitdaterelative())
        self.labels['textl']['text']=_("Your dictionary database is loading...")
        self.labels['text']['text']=_("{azt} is a computer "
                "program that accelerates community-based language development "
                "by facilitating the sorting of a beginning dictionary "
                "by vowels, consonants and tone. (more in help:about)").format(azt=self.program.name)
        self.labels['titletext']['text']=(_("{azt} Dictionary and Orthography "
                                        "Checker").format(azt=self.program.name))
        self.update_idletasks()
    def draw(self):
        # self.update_idletasks()
        # self.update()
        self.deiconify() #show after placement
    def progress(self,value):
        if self.exitFlag.istrue():
            return
        self.progressbar.current(value)
    def __init__(self, program):
        from main import updateazt
        self.program=program
        # try:
        #     parent.withdraw()
        #     noparent=False
        # except AttributeError:
        #     parent=self.program.tk_root
        super(Splash, self).__init__(self.program.tk_root,exit=0)
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
class LiftChooser(ui.Window,HasMenus):
    """this class allows the user to select a LIFT file, including options
    to start a new one (live or demo), or copy from USB."""
    def newfile_page(self):
        self._new_w=ui.Window(self.program.tk_root,title=_("Start New LIFT Database"))
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
        self.program.tk_root.unbind_all('<Button-1>')
        self.program.tk_root.unbind_all('<Return>')
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
        log.info(f"Updating Possibles for '{value}'")
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
        self.l_codes=self.program.languages.get_codes(value)
        log.info(f"found these codes for {value}: {self.l_codes}")
        self.l_codes=list(self.l_codes)[:20] #preserve order from here on out
        if not self.list_of_possibles.winfo_viewable():
            self.list_of_possibles.dogrid()
        if not self.l_codes:
            # log.info("no l_codes")
            self.options=[f"Error: '{value}' not found"]
            # log.info("get OK")
            self.list_of_possibles.config(state='disabled')
        else:
            # log.info("yes l_codes")
            objs=[self.program.languages.get_obj(i) for i in self.l_codes]
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
        log.info(f"Done updating possibles for '{value}'")
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
            code=[k for k,v in self.program.languages.region_codes_names.items()
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
        lang_obj=self.program.languages.get_obj(self.iso)
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
                self.use_code_button['text']=f"'{code}' invalid"
                return
        if langtags.tag_is_valid(self.code):
            # log.info("tag valid")
            self.use_code_button.configure(state='normal')
        else:
            # log.info(f"tag not valid {self.code=}")
            self.use_code_button.configure(state='disabled')
    def analang_code_complete(self):
        log.info("analang_code_complete")
        if not self.code:
            ErrorNotice(_("There doesn't seem to be an ethnologue code ({code})")
                        .format(code=self.code),wait=True)
            return
        self.wait(msg=_("Setting up new LIFT file now."),
                    showafterwait=True)
        log.info("Beginning Copy of stock to new LIFT file.")
        t=templates.CAWL(self.analang,newfile)
        if type(t) is str:
            ErrorNotice(t,wait=True)
            return
        self.template_obj=t
        for p in self.template_obj.fill_db_images():
            self.waitprogress(p)
        self.cawldb.write()
        self.wait.close()
        self.notify_newfilelocation(newfile)
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
        from backend.core.vcs import Git, Mercurial
        newrepo=makenewrepo(Git,mediadir)
        if not newrepo:
            log.info("trying with Mercurial")
            newrepo=makenewrepo(Mercurial,mediadir)
        if not newrepo: # if there, already exists
            log.error(_("Couldn't find a repository at {mediadir}").format(mediadir=mediadir))
        filename=self.findrepolift(newrepo) #find the lift file
        # log.info("found filename {}".format(filename))
        if filename: #this will be None, if no or multiple *.lift files
            # log.info("using filename {}".format(filename))
            newfile=newrepo.url.joinpath(filename) #make file a url
            # log.info("using newfile {}".format(newfile))
            if file.exists(newfile): #should always be there
                # log.info("notifying newfile {}".format(newfile))
                self.notify_newfilelocation(newfile) #tell user where to find it
                # log.info("returning newfile {}".format(newfile))
                return newfile
            else:
                log.error(_("looks like there was a problem finding "
                            "your new file. ({newfile})").format(newfile=newfile))
        else:
            msg=_("It looks like the repository was cloned, but "
                        "I can't find just one lift file."
                        "\nTell {azt} which file you want to "
                        "Analyze on the next page.").format(azt=self.program.name)
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
    def storedefaultsettings(self,basename):
        mgr=settings.SettingsManager(basename)
        mgr.project.set('glosslangs',['fr'])
        mgr.ui.set('buttoncolumns',2)
        log.info(f"Stored default settings for next run.")
    def makeCAWLdemo(self):
        title=_("Make a Demo LIFT Database")
        w=ui.Window(self.program.tk_root,title=title)
        w.withdraw()
        w.mainwindow=False
        t=ui.Label(w.frame, text=title, font='title', row=0, column=0)
        inst=_("Which language would you like to study, in this demonstration "
                "of what {azt} can do?").format(azt=self.program.name)
        t=ui.Label(w.frame, text=inst, row=1, column=0, columnspan=2)
        self.cawldb=loadCAWL()
        # self.program.settings doesn't exist yet!
        settings.Settings.langnames(self,self.cawldb.glosslangs)
        opts=[(i,self.languagenames[i]) 
                for i in self.cawldb.glosslangs]
        # log.info(f"{opts=}")
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
        self.wait=ui.Wait(parent=self.program.tk_root,
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
        self.cawldb.filename=newfile
        self.cawldb.analang=self.demolang
        self.cawldb.getentries()
        self.cawldb.getsenses()
        self.cawldb.convertglosstocitation(self.demolang)
        self.cawldb.get_imgdir() #problem!
        self.fill_db_images()
        self.copytonewfile(newfile)
        self.wait.close()
        self.notify_newfilelocation(newfile)
        self.storedefaultsettings(newfilebasename)
        return str(newfile)
    
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
    def notify_newfilelocation(self,newfile):
        #Do users care about this?
        return #not for now
        msg=_("Your new LIFT file is at {newfile}."
                "\nIf you don't want it there, close {azt} and move the whole "
                "{folder} folder wherever you like."
                "\nThen open {azt} and tell it where you put the LIFT file."
                ).format(newfile=newfile,
                        folder=file.getfilenamedir(newfile),
                        azt=self.program.name)
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
        self.program.filename=name
        file.writefilename(name)
        self.destroy()
        if (hasattr(self.program.taskchooser,'splash') and
                    self.program.taskchooser.splash.winfo_exists()):
            self.program.taskchooser.splash.deiconify()
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
    def __init__(self,program):
        # self.filechooser=chooser #main.FileChooser
        self.program=program
        # self.parent=self.program.tk_root
        super(LiftChooser, self).__init__(self.program.tk_root)
        self.title(_("Select LIFT Database"))
        ui.ContextMenu(self)
        text=_('What do you want to work on?') #LIFT database
        ui.Label(self.frame, text=text, font='title', column=0, row=0)
        optionlist=[('New',_("Start work on a new language"))]
        optionlist+=[('Clone',_("Copy work from a USB drive"))]
        filenamelist=file.getfilenames()
        if filenamelist:
            optionlist+=[(f,self.displayname(f)) for f in filenamelist]
            self.other=_("Select another database on my computer") #use later
        else:
            self.other=_("Select a database on my computer") #use later
        optionlist+=[('Other',self.other)]
        optionlist+=[('Demo',_("Make a demo database to try out {azt}"
                                ).format(azt=self.program.name))]
        buttonFrame1=ui.ScrollingButtonFrame(self.frame,
                                optionlist=optionlist,
                                command=self.setfilename,
                                window=self,
                                column=0, row=1,
                                bsticky='ew',
                                sticky=''
                                )
        # make mediadir look for *.git
        ui.Label(self.frame, image=self.program.theme.photo['small'],
                text=text, font='title', compound='top',
                column=1, row=1, ipadx=20)
        # if hasattr(self.program.taskchooser,'splash'):
        try:
            self.program.taskchooser.splash.withdraw()
        except:
            pass
        self.wait_window(self)


class Settings(object):
    def __init__(self, program):
        self.program = program
        self.program.ui_settings = self
    def getinterfacelang(self,event=None):
        log.info(_("Asking for interface language..."))
        azt=self.program.name
        window=ui.Window(self.program.mainwindow, title=_('Select Interface Language'))
        ui.Label(window.frame, text=_('What language do you want {name} '
                                'to address you in?').format(name=azt)
                ).grid(column=0, row=0)
        options=[{'code':i,'name':self.program.settings.languagenames[i]}
                for i in self.program.interfacelangs]
        log.info(_("asking with these options: {options}").format(options=options))
        ui.ButtonFrame(window.frame,
                                optionlist=options,
                                command=self.program.settings.interfacelangwrapper,
                                window=window,
                                column=0, row=1
                                )
    def getanalangname(self,event=None):
        log.info(_("this sets the language name"))
        def submit(event=None):
            if namevar.get():
                self.program.settings.languagenames[self.program.params.analang()]=namevar.get()
                #This stores to file:
                setnesteddictobjectval(self.program.settings,'adnlangnames',
                                    namevar.get(),self.program.params.analang())
            else:
                if self.program.params.analang() in self.program.settings.languagenames:
                    del self.program.settings.languagenames[self.program.params.analang()]
                if self.program.params.analang() in self.program.settings.adnlangnames:
                    del self.program.settings.adnlangnames[self.program.params.analang()]
                self.program.settings.langnames([self.program.params.analang()]) #refreshes w/above
            self.program.settings.storesettingsfile()
            self.program.mainwindow.status.updateanalang() #ui
            window.destroy()
        window=ui.Window(self.program.task,title=_('Enter Analysis Language Name'))
        curname=self.program.settings.languagenames[self.program.params.analang()]
        defaultname=_("Language with code [{code}]").format(code=self.program.params.analang())
        t=_("How do you want to display the name of {name}").format(name=curname)
        namevar=ui.StringVar()
        log.info(f"{curname} = {defaultname}? {curname == defaultname}")
        if curname != defaultname:
            t+=_(", with ISO 639-3 code [{code}]").format(code=self.program.params.analang())
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
        if len(self.program.db.analangs) <2: #The user probably wants to change display.
            self.getanalangname()
            return
        log.info(_("this sets the language"))
        # fn=inspect.currentframe().f_code.co_name
        window=ui.Window(self.program.task,title=_('Select Analysis Language'))
        if self.program.db.analangs is None :
            ui.Label(window.frame,
                          text=_('Error: please set Lift file first! ({file})').format(
                          file=self.program.db.filename)
                          ).grid(column=0, row=0)
        else:
            ui.Label(window.frame,
                          text=_('What language do you want to analyze?')
                          ).grid(column=0, row=1)
            langs=list()
            for lang in self.program.db.analangs:
                langs.append({'code':lang,
                                'name':self.program.settings.languagenames[lang]})
                # print(lang, self.program.taskchooser.languagenames[lang])
            buttonFrame1=ui.ButtonFrame(window.frame,
                                     optionlist=langs,
                                     command=self.program.settings.setanalang,
                                     window=window,
                                     column=0, row=4
                                     )
    def getglosslang(self,event=None):
        window=ui.Window(self.program.task,title=_('Select Gloss Language'))
        text=_('What Language do you want to use for glosses?')
        ui.Label(window.frame, text=text, column=0, row=1)
        langs=list()
        for lang in set(self.program.db.glosslangs)|set(
                                            self.program.settings.glosslangs[1:]):
            langs.append({'code':lang,
                            'name':self.program.settings.languagenames[lang]})
        if self.program.settings.glosslangs.lang2():
            langs.append({'code':None,
                    'name':_('just use {name}').format(name=self.program.settings.languagenames[
                                    self.program.settings.glosslangs.lang2()])})
        buttonFrame1=ui.ButtonFrame(window.frame,
                                 optionlist=langs,
                                 command=self.program.settings.setglosslang,
                                 window=window,
                                 column=0, row=4
                                 )
    def getglosslang2(self,event=None):
        window=ui.Window(self.program.task,title=_('Select Second Gloss Language'))
        text=_('What other language do you want to use for glosses?')
        ui.Label(window.frame, text=text, column=0, row=1)
        langs=list()
        for lang in set(self.program.db.glosslangs)|set(self.program.settings.glosslangs[:1]):
            if lang == self.program.settings.glosslangs[0]:
                continue
            langs.append({'code':lang,
                            'name':self.program.settings.languagenames[lang]})
        langs.append({'code':None,
                    'name':_('just use {name}').format(name=self.program.settings.languagenames[
                                    self.program.settings.glosslangs.lang1()])})
        buttonFrame1=ui.ButtonFrame(window.frame,
                                    optionlist=langs,
                                    command=self.program.settings.setglosslang2,
                                    window=window,
                                    column=0, row=4
                                    )
    def getcvt(self,event=None):
        log.debug(_("Asking for check cvt/type"))
        window=ui.Window(self.program.task,title=_('Select Check Type'))
        cvts=[]
        x=0
        tdict=self.program.params.cvtdict()
        for cvt in tdict:
            if cvt in ['CV','VC'] and getattr(self.task,'is_sort_task',False):
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
                                    command=self.program.settings.setcvt,
                                    window=window,
                                    column=0, row=1
                                    )
        return window
    def getps(self,event=None):
        log.info(_("Asking for ps..."))
        # self.refreshattributechanges()
        window=ui.Window(self.program.task, title=_('Select Lexical Category'))
        ui.Label(window.frame, text=_('What lexical category do you '
                                    'want to work with (Part of speech)?')
                ).grid(column=0, row=0)
        if hasattr(self,'additionalps') and self.program.settings.additionalps is not None:
            pss=self.program.db.pss+self.program.settings.additionalps #these should be lists
        else:
            pss=self.program.db.pss
        buttonFrame1=ui.ScrollingButtonFrame(window.frame,
                                            optionlist=pss,
                                            command=self.program.settings.setps,
                                            window=window,
                                            column=0, row=1
                                            )
    def getprofile(self,event=None,**kwargs):
        log.info(_("Asking for profile..."))
        # self.refreshattributechanges()
        ps=self.program.slices.ps()
        if not ps:
            text=(_("No Grammatical Category? ")+""
                    f" ({list(self.program.settings.profilesbysense)})")
            ErrorNotice(text, parent=self.program.task, wait=True)
        elif self.program.settings.profilesbysense[ps] is None: #likely never happen...
            text=_('Error: please set Grammatical category with profiles '
                    'first! (not {ps})').format(ps=ps)
            ErrorNotice(text, parent=self.program.task, wait=True)
        else:
            profilecounts=self.program.slices.valid()
            profilecountsAdHoc=self.program.slices.adhoccounts()
            profiles=self.program.status.profiles(**kwargs)
            if profilecountsAdHoc:
                adhocdict=self.program.slices.adhoc()
                profilecounts.update(profilecountsAdHoc)
                if ps in adhocdict:
                    profiles+=self.program.slices.adhoc()[ps].keys()
            profiles=dict.fromkeys(profiles)
            if not profiles:
                log.error(_("No profiles of {type} type found!").format(type=kwargs))
            # log.info("count types: {}, {}".format(type(profilecounts),
            #                                         type(profilecountsAdHoc)))
            window=ui.Window(self.program.task,title=_('Select Syllable Profile'))
            ui.Label(window.frame, text=_('What ({ps}) syllable profile do you '
                                    'want to work with?').format(ps=ps)
                                    ).grid(column=0, row=0)
            optionslist = [{'code':x,'description':profilecounts[(x,ps)]} for x in profiles]
            """What does this extra frame do?"""
            window.scroll=ui.Frame(window.frame)
            window.scroll.grid(column=0, row=1)
            buttonFrame1=ui.ScrollingButtonFrame(window.scroll,
                                    optionlist=optionslist,
                                    command=self.program.settings.setprofile,
                                    window=window,
                                    column=0, row=0
                                    )
            window.wait_window(window)
    def getsecondformfieldN(self,event=None):
        ps=self.program.settings.nominalps
        opts=self.program.settings.plopts
        othername=self.program.settings.imperativename
        setcmd=self.program.settings.setsecondformfieldN
        self.getsecondformfield(ps,opts,othername,setcmd)
    def getsecondformfieldV(self,event=None):
        # log.info(".impopts: {}".format(self.program.settings.impopts))
        ps=self.program.settings.verbalps
        opts=self.program.settings.impopts
        othername=self.program.settings.pluralname
        setcmd=self.program.settings.setsecondformfieldV
        self.getsecondformfield(ps,opts,othername,setcmd)
    def getcustomsecondformfield(self,ps,othername,setcmd):
        def updateerror(event=None):
            if event.keysym != 'Return':
                self.program.task.errorlabel['text'] = ''
        def submitform(event=None):
            log.info(_("setting {custom} (not {other})").format(custom=custom.get(), other=othername))
            if custom.get() == othername:
                text=_("That name is already used!")
                log.error(text)
                self.program.task.errorlabel['text']=text
                return
            setcmd(custom.get())
            window.on_quit()
        title=_('Make Custom Second Form Field for {ps}').format(ps=ps)
        window=ui.Window(self.program.task,title=title)
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
        self.program.task.errorlabel=ui.Label(window,text='',
                            fg='red',
                            wraplength=int(self.program.task.frame.winfo_screenwidth()/3),
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
        log.info(_("Asking for '{ps}' second form field...").format(ps=ps))
        try:
            assert other == False
            othernames=[i for i in self.program.db.fieldnames[self.program.params.analang()]
                    if i != othername and i not in ['lc','lx']]
        except (KeyError,AssertionError):
            othernames=[]
        if othernames:
            if len(othernames)-1:
                text=_("Select a database field "
                        "to use for second forms of '{ps}' words").format(ps=ps)
                otherbuttontext=_("None of these; make a new field")
            else:
                text=_("Select the '{field}' database field "
                        "for second forms of '{ps}' words").format(field=othernames[0],ps=ps)
                otherbuttontext=_("No; make a new field")
            cmd=getother
            optionslist=othernames
        else:
            setcmd(opts[0])
            # ErrorNotice(_("No suitable database fields were found for second "
            #             f"forms of '{ps}' words; using '{opts[0]}'."))
            return
            # text=_("No suitable database fields were found; what name "
            #         f"do you want to use for second forms of '{ps}' words?")
            # otherbuttontext=_("None of these work; make my own field")
            # cmd=getcustom
            # optionslist=opts
        title=_('Select Second Form Field for {ps}').format(ps=ps)
        window=ui.Window(self.program.task,title=title)
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
        if self.program.task.winfo_viewable():
            self.program.task.withdraw()
            window.wait_window(window)
            self.program.task.deiconify()
        else:
            window.wait_window(window)
    def getmulticheckscope(self,event=None):
            log.info(_("Asking for multicheckscope..."))
            window=ui.Window(self.program.task, title=_('Select Scope of Checks'))
            ui.Label(window.frame,
                    text=_('What kinds of checks to you want to run?')
                    ).grid(column=0, row=0)
            cvts=[[i] for i in self.program.params.cvts()]
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
                    'name':unlist([self.program.params.cvtdict()[i]['pl'] for i in opt])
                    }
                    for opt in cvtsdone
                    ]
            for opt in options:
                if len(opt['code']) == 1:
                    opt['name']+=' '+_("(only)")
            buttonFrame1=ui.ScrollingButtonFrame(window.frame,
                                    optionlist=options,
                                    command=self.program.settings.setmulticheckscope,
                                    window=window,
                                    column=0, row=1
                                                )
    def cvtstodoprose(self,cvtstodo=None):
        if not cvtstodo:
            cvtstodo=self.cvtstodo
        output=[]
        for cvt in self.cvtstodo:
            output+=[self.program.params.cvtdict()[cvt]['pl']]
        return output
    def secondfieldnames(self):
        """Not called anywhere?"""
        if self.program.settings.nominalps not in self.program.settings.secondformfield:
            self.getsecondformfieldN()
        if self.program.settings.verbalps not in self.program.settings.secondformfield:
            self.getsecondformfieldV()
        return (self.program.settings.secondformfield[self.program.settings.verbalps],
                self.program.settings.secondformfield[self.program.settings.nominalps])
    def getbuttoncolumns(self,event=None):
        log.info(_("Asking for number of button columns..."))
        window=ui.Window(self.program.task,title=_('Select Button Columns'))
        ui.Label(window.frame, text=_('How many columns do you want to use for '
                                        'the sort buttons?')
                                        ).grid(column=0, row=0)
        optionslist = list(range(1,4))
        buttonFrame1=ui.ButtonFrame(window.frame,
                                optionlist=optionslist,
                                command=self.program.settings.setbuttoncolumns,
                                window=window,
                                column=0, row=1
                                )
        window.wait_window(window)
    def getmaxpss(self,event=None):
        title=_('Select Maximum Number of Lexical Categories')
        window=ui.Window(self.program.task, title=title)
        text=_('How many lexical categories to report (2 = Noun and Verb) ?')
        ui.Label(window.frame, text=text, column=0, row=0)
        r=[x for x in range(1,10)]
        buttonFrame1=ui.ScrollingButtonFrame(window.frame,
                                optionlist=r,
                                command=self.program.settings.setmaxpss,
                                window=window,
                                column=0, row=1
                                )
        buttonFrame1.wait_window(window)
    def getmaxprofiles(self,event=None):
        title=_('Select Maximum Number of Syllable Profiles')
        window=ui.Window(self.program.task, title=title)
        text=_('How many syllable profiles to report?')
        ui.Label(window.frame, text=text, column=0, row=0)
        r=[x for x in range(1,10)]
        buttonFrame1=ui.ScrollingButtonFrame(window.frame,
                                optionlist=r,
                                command=self.program.settings.setmaxprofiles,
                                window=window,
                                column=0, row=1
                                )
        buttonFrame1.wait_window(window)
    def setSdistinctions(self):
        def notice(changed):
            def confirm():
                ok.value=True
                w.destroy()
            ti=_("Important Notice!")
            w=ui.Window(self.program.task,title=ti)
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
                        self.program.task.frame.winfo_screenwidth()/2)).grid(row=1,column=0)
            for n,ps in enumerate(self.program.slices.pss()):
                i=[x for x in self.program.slices.profiles(ps)
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
                    if s in self.program.settings.distinguish:
                        if self.program.settings.distinguish[s]==changed[s][1]:
                            self.program.settings.distinguish[s]=changed[s][0] #(oldvar,newvar):
                        else:
                            log.error(_("Changed to value ({new}) doesn't match "
                            "current setting for '{setting}': {current}").format(new=changed[s][1],
                                                        setting=s,current=self.distinguish[s]))
                    elif s in self.program.settings.interpret:
                        if self.program.settings.interpret[s]==changed[s][1]:
                            self.program.settings.interpret[s]=changed[s][0] #(oldvar,newvar):
                        else:
                            log.error(_("Changed to value ({new}) doesn't match "
                            "current setting for '{setting}': {current}").format(new=changed[s][1],
                                                        setting=s,current=self.interpret[s]))
            r=True #only false if changes made, and user exits notice
            changed={}
            for typ in ['distinguish', 'interpret']:
                for s in getattr(self.program.settings,typ):
                    if s in options.vars: # and s in getattr(self.program.settings,typ):
                        newvar=options.vars[s].get()
                        oldvar=getattr(self.program.settings,typ)[s]
                        if oldvar != newvar:
                            changed[s]=(oldvar,newvar)
                            getattr(self.program.settings,typ)[s]=newvar
            # log.debug('self.distinguish: {}'.format(self.program.settings.distinguish))
            # log.debug('self.interpret: {}'.format(self.program.settings.interpret))
            if changed:
                # log.info('There was a change; we need to redo the analysis now.')
                log.info(_('The following changed (from,to): {changed}').format(changed=changed))
                r=notice(changed)
                if r:
                    self.program.task.runwindow.on_quit()
                    self.program.settings.storesettingsfile(setting='profiledata')
                    self.program.taskchooser.restart()
                else:
                    undo(changed)
            else:
                self.program.task.runwindow.on_quit()
        def buttonframeframe(s):
            f=ui.Frame(self.program.task.runwindow.scroll.content,
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
            f=ui.Frame(self.program.task.runwindow.scroll.content,
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
        self.program.task.getrunwindow()
        self.program.settings.checkinterpretations()
        analang=self.program.params.analang()
        options=Options(r=0,padx=50,pady=0,c=0,vars={},frames={})
        for s in self.program.settings.distinguish: #Should be already set.
            options.vars[s] = ui.BooleanVar()
            options.vars[s].set(self.program.settings.distinguish[s])
        for s in self.program.settings.interpret: #This should already be set, even by default
            options.vars[s] = ui.StringVar()
            options.vars[s].set(self.program.settings.interpret[s])
        """Page title and instructions"""
        self.program.task.runwindow.title(_("Set Parameters for Segment Interpretation"))
        mwframe=self.program.task.runwindow.frame
        title=_("Interpret {lang} Segments"
                ).format(lang=self.program.settings.languagenames[analang])
        titl=ui.Label(mwframe,text=title,font='title',
                justify=ui.LEFT,anchor='c',
                row=options.get('r'), column=options.get('c'),
                sticky='ew', padx=options.padx, pady=10)
        options.next('r')
        text=_("Here you can view and set parameters that change how {name} "
        "interprets {lang} segments (consonant and vowel glyphs/characters)"
                ).format(name=self.program.name,lang=self.program.settings.languagenames[analang])
        instr=ui.Label(mwframe,text=text,justify=ui.LEFT,anchor='c',
                    row=options.get('r'), column=options.get('c'),
                    sticky='ew', padx=options.padx, pady=options.pady)
        instr.wrap()
        """The rest of the page"""
        self.program.task.runwindow.scroll=ui.ScrollingFrame(mwframe,row=2,column=0)
        # log.debug('self.distinguish: {}'.format(self.program.settings.distinguish))
        # log.debug('self.interpret: {}'.format(self.program.settings.interpret))
        """I considered offering these to the user conditionally, but I don't
        see a subset of them that would only be relevant when another is
        selected. For instance, a user may NOT want to distinguish all Nasals,
        yet distinguish word final nasals. Or CG sequences, but not other G's
        --or distinguish G, but leave as CG (≠C). So I think these are all
        independent boolean selections."""
        if analang in self.program.db.s:
            vars=[k for k in self.program.db.s[analang].keys()
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
            exsdict[var]=self.program.db.s[analang][var]
            if var in self.program.settings.polygraphs[analang]:
                exsdict[var]+=[k for k,v in
                        self.program.settings.polygraphs[analang][var].items()
                        if self.program.settings.polygraphs[analang][var][k]
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
        self.program.task.runwindow.frame2d=ui.Frame(mwframe,
                                        row=3,
                                        column=options.get('c'),
                                        sticky='e', padx=options.padx,
                                        pady=options.pady)
        sub_btn=ui.Button(self.program.task.runwindow.frame2d, text=_('Use these settings'),
                          command = submitform,
                          row=0,column=1,sticky='nw',
                          pady=options.pady)
        nbtext=_("If you make changes, this button==> \nwill "
                "restart the program to reanalyze your data.")
        sub_nb=ui.Label(self.program.task.runwindow.frame2d, text = nbtext,
                        anchor='e',
                        row=0,column=0,sticky='e',
                        pady=options.pady)
        self.program.task.runwindow.waitdone()
    def getexamplespergrouptorecord(self):
        log.info(_("this sets the number of examples per group to record"))
        self.npossible=[
            {'code':1,'name':_("1 - Bare minimum, just one per group")},
            {'code':5,'name':_("5 - Some, but not all, of most groups")},
            {'code':100,'name':_("100 - All examples in most databases")},
            {'code':1000,'name':_("1000 - All examples in VERY large databases")}
                        ]
        title=_('Select Number of Examples per Group to Record')
        window=ui.Window(self.program.task, title=title)
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
                "").format(name=self.program.name)
        t=ui.Label(window.frame, text=title, font='title',column=0, row=0)
        l=ui.Label(window.frame, text=text, justify='left',column=0, row=1)
        t.wrap()
        l.wrap()
        buttonFrame1=ui.ButtonFrame(window.frame,
                            optionlist=self.npossible,
                            command=self.program.settings.setexamplespergrouptorecord,
                            window=window,
                            column=0, row=4
                                )
        buttonFrame1.wait_window(window)
