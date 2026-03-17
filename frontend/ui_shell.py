# coding=UTF-8
"""This module is an interface to the base frontend classes."""
import gettext
_ = gettext.gettext
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

def __getattr__(name):
    # Lazy load globals from main
    if name in ('_', 'sysrestart', 'main',
                'interfacelang', 'nn', 'unlist', 'rx', 'exampletype',
                'grouptype', 't', 'openweburl', 'scaleimageifthere',
                'loadCAWL', 'saveimagefile', 'TranscribeS',
                'Multislice', 'Multicheck', 'Tone', 'Segments',
                'WordCollection', 'Parse', 'Sort',
                'TaskChooser', 'Mercurial', 'Git', 'Analysis',
                'StatusDict', 'Settings', 'updateazt',
                'Sound', 'SortT', 'JoinUFgroups', 'ReportCitationT',
                'sound', 'scaledimage', 'getimagelocationURI'):
        import main
        return getattr(main, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

# Mirror main globals lazily to allow bare-name access
for name in ('_', 'sysrestart', 'main',
             'interfacelang', 'nn', 'unlist', 'rx', 'exampletype',
             'grouptype', 't', 'openweburl', 'scaleimageifthere',
             'loadCAWL', 'saveimagefile', 'TranscribeS',
             'Multislice', 'Multicheck', 'Tone', 'Segments',
             'WordCollection', 'Parse', 'Sort',
             'TaskChooser', 'Mercurial', 'Git', 'Analysis',
             'StatusDict', 'Settings', 'updateazt',
             'Sound', 'SortT', 'JoinUFgroups', 'ReportCitationT',
             'sound', 'scaledimage', 'getimagelocationURI'):
    if name not in globals():
        globals()[name] = LazyGlobal(name)

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
        if isinstance(self.parent,Sort):
            self.parameterslice()
    def fillcawl(self):
        w=ui.Wait(self.program.tk_root,msg=_("Filling images..."))
        try:
            LiftChooser.fillcawldbimages(self, cawldb=self.program.db, newdirname=self.program.db.lift_home, wait=w)
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
                            self.parent.setSdistinctions),
                (_("Remake Status file (All: several minutes)"),
                            self.program.settings.reloadstatusdata),
                (_("Remake Status file (just this category)"),
                            self.program.settings.reloadstatusdatabycvtps),
                (_("Remake Status file (just this profile)"),
                        self.program.settings.reloadstatusdatabycvtpsprofile),
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
        if isinstance(self.parent,SortT):
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
        if isinstance(parent,TaskDressing):
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
        self.labels['interfacelang']['text'].set(self.interfacelanglabel())
    def interfacelanglabel(self):
        # for l in self.program.taskchooser.interfacelangs:
        #     if l['code']==interfacelang():
        #         interfacelanguagename=l['name']
        return (_("Using {lang}").format(lang=self.program.settings.languagenames[interfacelang()]))
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
        analang=self.program.params.analang()
        langname=self.program.settings.languagenames[analang]
        return (_("Studying {lang}").format(lang=langname))
    def analangline(self):
        self.newrow()
        if self.program.params.analang() not in self.program.settings.languagenames:
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
        self.labels['glosslang']={'text':ui.StringVar(value=self.glosslanglabel()),
                                'columnplus':1,
                                # 'rowplus':1,
                                'cmd':self.task.getglosslang,
                                'parent':line,
                                'tt':_("change this gloss language")
                                    if len(self.program.settings.glosslangs) >1
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
            self.newrow()
            line=ui.Frame(self.proseframe,row=self.irow,column=0,
                            columnspan=3,sticky='w') #3 cols is the width of frame
            # These shouldn't need to be updated:
            if ps == self.program.settings.nominalps:
                cmd=self.task.getsecondformfieldN
            else:
                cmd=self.task.getsecondformfieldV
            if ps not in self.program.settings.secondformfield and (
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
        profile=self.program.slices.profile()
        if not profile:
            profile=_("<no syllable profile>")
        return (_("Looking at {profile}").format(profile=profile))
    def updateps(self):
        self.labels['ps']['text'].set(self.pslabel())
        self.makesliceattrs()
        self.maybeboard()
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
        return (_("Checking {cvt},").format(cvt=self.program.params.cvtdict()[self.cvt]['pl']))
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
        self.labels['toneframe']={'text':ui.StringVar(value=self.toneframelabel()),
                                'columnplus':1,
                                'cmd':self.task.getcheck,
                                'parent':line,
                                'tt':_("change this tone frame")}
        self.proselabel(**self.labels['toneframe'])
    def updatetonegroup(self):
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
            cmd=self.task.getgroupwsorted
        elif (not check or (check in self.program.status.checks(tosort=True) and
            profile in self.program.status.profiles(tosort=True))):
            cmd=self.task.getgrouptosort
        elif (check in self.program.status.checks(toverify=True) and
            profile in self.program.status.profiles(toverify=True)):
            cmd=self.task.getgrouptoverify
        elif (check in self.program.status.checks(torecord=True) and
            profile in self.program.status.profiles(torecord=True)):
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
        return (_("working on {check}").format(check=self.program.params.cvcheckname()))
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
        if not self.program.params.check() or 'x' in self.program.params.check():
            return
        if self.program.status.group():
            return (f"= {self.program.status.group()}")
        else:
            return (_("(All groups)"))
    def cvgroup(self,line):
        self.labels['cvgroup']={'text':ui.StringVar(value=self.cvgrouplabel()),
                                'columnplus':2,
                                'cmd':self.task.getgroup,
                                'parent':line,
                                'tt':_("change this group")
                                if self.program.status.group()
                                else _("specify one group")
                                }
        self.proselabel(**self.labels['cvgroup'])
    def updatebuttoncolumns(self):
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
        self.labels['buttoncolumns']={'text':ui.StringVar(value=self.buttoncolumnslabel()),
                                'columnplus':1,
                                'cmd':self.task.getbuttoncolumns,
                                'tt':tt}
        self.proselabel(**self.labels['buttoncolumns'])
    def updatemaxprofiles(self):
        self.labels['maxes']['text'].set(self.maxprofileslabel())
    def maxprofileslabel(self):
        return (_("Max profiles: {max_profiles}; ").format(max_profiles=self.program.settings.maxprofiles))
    def updatemaxpss(self):
        self.labels['maxes']['text'].set(self.maxpsslabel())
    def maxpsslabel(self):
        return (_("Max lexical categories: {max_pss}").format(max_pss=self.program.settings.maxpss))
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
        for ps in [self.program.settings.nominalps, self.program.settings.verbalps]:
            if ps not in self.program.settings.secondformfield and (
                isinstance(self.task,Parse) or (
                    isinstance(self.task,WordCollection) and
                    self.type not in ['lx','lc'])):
                if ps == self.program.settings.nominalps:
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
            not self.program.taskchooser.doneenough['collectionlc']):
            self.makenoboard()
            return
        if isinstance(self.task,TranscribeS):
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
        def updateprofilencheck(profile,check):
            # log.info("running updateprofilencheck({},{})".format(profile,check))
            self.program.settings.setprofile(profile)
            self.program.settings.setcheck(check)
            self.maybeboard()
            # log.info("now {},{}".format(self.program.slices.profile(),
            #                             self.program.params.check()))
            #run this in any case, rather than running it not at all, or twice
        def refresh(event=None):
            # log.info("refreshing status table")
            self.program.settings.storesettingsfile()
            self.task.tableiteration+=1
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
        profiles=self.program.slices.profiles()[:] #just sort here
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
                                cmd=self.task.addframe
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
                                        self.task.getcvt)
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
        if isinstance(self.task,Segments) and not isinstance(self.task,TranscribeS):
            self.fieldsline()
        if (hasattr(self.program, 'slices') and
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
    taskicon = 'icon'
    tasktitle = None
    def _taskchooserbutton(self):
        if isinstance(self,TaskChooser) and not self.showreports:
            if self.datacollection:
                text=_("Analyze & Decide")
            else:
                text=_("Collect Data")
        elif isinstance(self,Report):
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
        self.program.taskchooser.task=self # in case this hasn't been set yet
        self.withdraw()
        self.program.taskchooser.gettask()
    def mainlabelrelief(self,relief=None,refresh=False,event=None):
        #set None to make this a label instead of button:
        reliefs=["raised", "groove", "sunken", "ridge", "flat"]
        if self.mainrelief and self.mainrelief in reliefs:
            self.program.taskchooser.mainreliefnext=\
            self.program.taskchooser.task.mainreliefnext=\
            self.mainreliefnext=reliefs[(reliefs.index(self.mainrelief)+1
                                                            )%len(reliefs)]
        log.info(_("setting button relief to {relief}, with refresh={refresh}").format(relief=relief,
                                                                    refresh=refresh))
        # None "raised" "groove" "sunken" "ridge" "flat"
        self.status.mainrelief=\
        self.program.taskchooser.mainrelief=\
        self.program.taskchooser.task.mainrelief=\
        self.mainrelief=relief
    def _showbuttons(self,event=None):
        todo=getattr(self,'mainreliefnext','flat')
        self.mainlabelrelief(relief=todo,refresh=True)
        self.program.taskchooser.mainwindowis.status.makeui()
        self.setcontext()
    def _hidebuttons(self,event=None):
        self.mainlabelrelief(relief=None,refresh=True)
        self.program.taskchooser.mainwindowis.status.makeui()
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
        self.program.taskchooser.mainwindowis.status.maybeboard()
        self.setcontext()
    def _showdetails(self):
        # log.info("Showing group names")
        self.program.settings.set('showdetails', True, refresh=True)
        self.program.taskchooser.mainwindowis.status.maybeboard()
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
        if callable(self.tasktitle):
            return self.tasktitle()
        if self.tasktitle:
            return _(self.tasktitle)
        return _("Unnamed {name} Task ({type})").format(
                                name=self.program.name,type=type(self).__name__)
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
    def trystatusframelater(self,dict):
        self.program.settings.setrefreshdelay()
        self.makestatusframe_after_id=self.after(
                                            self.program.settings.refreshdelay,
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
        if not hasattr(self.program, 'slices'):
            # slices is done by taskchooser on boot, but later
            # don't update both taskchooser and task, just the visible one
            self.trystatusframelater(dict)
            return #don't die, but don't do this until ready, either
        dictnow={
                # 'mainrelief':self.mainrelief,
                # 'showdetails':self.program.settings.showdetails, #attr, not task.method
                'self.fontthemesmall':self.fontthemesmall,
                # 'buttonkwargs':self.dobuttonkwargs(),
                # 'iflang':self.program.settings.interfacelangwrapper(),
                # 'analangname':self.program.settings.languagenames[self.analang],
                # 'analang':self.program.params.analang(),
                # 'glang1':self.glosslangs.lang1(),
                # 'glang2':self.glosslangs.lang2(),
                # 'secondformfield':str(self.program.settings.secondformfield),
                # 'maxprofiles':self.program.settings.maxprofiles,
                # 'maxpss':self.program.settings.maxpss
                }
        # if 'slices' in program:
        dictnow.update({
            # 'cvt':self.program.params.cvt(),
            # 'check':self.program.params.check(),
            # 'ps':self.program.slices.ps(),
            # 'profile':self.program.slices.profile(),
            # 'group':self.program.status.group(),
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
        if self.program.taskchooser.donew['collectionlc']:
            self.program.settings.makeeverythingok()
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
        self.program.settings.storesettingsfile()
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
                    self.runwindow.on_quit()
                    self.program.settings.storesettingsfile(setting='profiledata')
                    self.program.taskchooser.restart()
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
        self.runwindow.title(_("Set Parameters for Segment Interpretation"))
        mwframe=self.runwindow.frame
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
        self.runwindow.scroll=ui.ScrollingFrame(mwframe,row=2,column=0)
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
        azt=self.program.name
        window=ui.Window(self, title=_('Select Interface Language'))
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
                self.program.settings.languagenames[self.analang]=namevar.get()
                #This stores to file:
                setnesteddictobjectval(self.program.settings,'adnlangnames',
                                    namevar.get(),self.analang)
            else:
                if self.analang in self.program.settings.languagenames:
                    del self.program.settings.languagenames[self.analang]
                if self.analang in self.program.settings.adnlangnames:
                    del self.program.settings.adnlangnames[self.analang]
                self.program.settings.langnames([self.analang]) #refreshes w/above
            self.program.settings.storesettingsfile()
            self.program.taskchooser.mainwindowis.status.updateanalang() #ui
            window.destroy()
        window=ui.Window(self,title=_('Enter Analysis Language Name'))
        curname=self.program.settings.languagenames[self.analang]
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
        if len(self.program.db.analangs) <2: #The user probably wants to change display.
            self.getanalangname()
            return
        log.info(_("this sets the language"))
        # fn=inspect.currentframe().f_code.co_name
        window=ui.Window(self,title=_('Select Analysis Language'))
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
        window=ui.Window(self,title=_('Select Gloss Language'))
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
        window=ui.Window(self,title=_('Select Second Gloss Language'))
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
        window=ui.Window(self,title=_('Select Check Type'))
        cvts=[]
        x=0
        tdict=self.program.params.cvtdict()
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
                                    command=self.program.settings.setcvt,
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
    def getps(self,event=None):
        log.info(_("Asking for ps..."))
        # self.refreshattributechanges()
        window=ui.Window(self, title=_('Select Lexical Category'))
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
            ErrorNotice(text, parent=self, wait=True)
        elif self.program.settings.profilesbysense[ps] is None: #likely never happen...
            text=_('Error: please set Grammatical category with profiles '
                    'first! (not {ps})').format(ps=ps)
            ErrorNotice(text, parent=self, wait=True)
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
                                    command=self.program.settings.setprofile,
                                    window=window,
                                    column=0, row=0
                                    )
            window.wait_window(window)
    def setsensetodo(self,choice,window):
        self.sense=self.sensetodo=choice
        self.program.taskchooser.mainwindowis.status.updatesensetodo()
        window.destroy()
        if isinstance(self,WordCollection):
            self.withdraw()
            self.getword()
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
        log.info(_("Asking for '{ps}' second form field...").format(ps=ps))
        try:
            assert other == False
            othernames=[i for i in self.program.db.fieldnames[self.analang]
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
        window=ui.Window(self,title=_('Select Button Columns'))
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
        window=ui.Window(self, title=title)
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
        window=ui.Window(self, title=title)
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
        updateazt()
    def maybewrite(self,definitely=False):
        self.program.taskchooser.maybewrite(definitely=definitely)
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
        if isinstance(self,Sound):
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
        log.info(_("Initializing TaskDressing"))
        self.parent=parent
        self.program=parent.program
        self.menu=False #initialize once
        if isinstance(self,TaskChooser):
            taskchooser=self
        else:
            self.task=self
            taskchooser=self.parent
            self.program.status.task(self)
        """Whenever this runs, it's the main window."""
        taskchooser.mainwindowis=self
        """At some point, I need to think through which attributes are needed,
        and if I can get them all into objects, read/writeable with files."""
        """These are raw attributes from file"""
        """these are objects made by the task chooser"""
        # log.info(f"Ready to Inherit for {type(self)} ({program})")
        self.inherittaskattrs()
        if hasattr(self,'task') and isinstance(self.task,Multicheck):
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
            name=self.program.params.cvcheckname(self.check)
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
        if self.program.settings.lowverticalspace:
            # log.info("using lowverticalspace for addgroupbutton")
            scaledpady=0
        else:
            scaledpady=int(40*self.program.scale)
        # log.info("This button at row={row}, col={col}".format(row=self.groupbuttons.row, col=self.groupbuttons.col))
        nbuttons=len(self.groupbuttons.winfo_children())
        r,c=nbuttons//self.buttoncolumns,nbuttons%self.buttoncolumns
        kwargs={'group':group} #this may be glyph, item code, or sort group
        if self.macrosort and not self.remove_on_click:
            frame_class=SortGlyphGroupButtonFrame #this takes glyph, calls other
        else:
            frame_class=SortGroupButtonFrame #this takes item code or sort group
        if self.macrosort and self.remove_on_click:
            kwargs=self.program.alphabet.parse_verificationcode(group)
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
        # self.task=self.program.status.task()
        """These two methods each take an item and a category, into which the
        item is sorted. This should be generalizable."""
        self.check=self.program.params.check()
        self.cvt=self.program.params.cvt()
        self.maybewrite=self.program.taskchooser.maybewrite
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
            self.buttoncolumns=self.program.status.task().buttoncolumns
        waiting.wait(msg)
        
        # Prefetch examples for all groups at once to avoid O(N^2) lookup
        self.program.examples.prefetch_examples(self.groups, **kwargs)
        
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
        self._text=node.formatted(self.program.taskchooser.analang,
                                    self.program.taskchooser.glosslangs,
                                    ftype=self.program.params.ftype(),
                                    frame=self.program.toneframes.get(
                                                self.program.params.check()),
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
                                            self.program.settings.soundsettings)
        b=ui.Button(self, text=self._text,
                    cmd=self.player.play,
                    column=1, row=0,
                    sticky='nesw',
                    **self.buttonkwargs())
        if hasattr(self,'_illustration'):
            b['image']=self._illustration
            b['compound']='left'
        bttext=_("Click to hear this utterance")
        if self.program.praat:
            bttext+='; '+_("right click to open in praat")
            b.bind('<Button-3>',
                    lambda x: executables.praatopen(self.program, self._filenameURL))
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
        self.exs=self.program.examples
        self.task=task #the task/check OR the scrollingframe! use self.check.task
        try:
            self.code=self.program.alphabet.verificationcode(**kwargs)
        except:
            pass #don't worry if that info isn't all there
        self.group=kwargs.pop('group') #must be here
        self.check=kwargs.get('check',None) #must be here for glyphs only
        # self,parent,group,row,column=0,label=False,canary=None,canary2=None,
        # alwaysrefreshable=False,playable=False,renew=False,unsortable=False,
        # **kwargs
        # From check, need
        # check=self.program.params.check()
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
        if self.program.settings.lowverticalspace:
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
        kwargs.update(self.program.alphabet.parse_verificationcode(item))
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
        if self.group not in self.program.alphabet.glyph_members():
            ui.Label(self,text=_("group '{group}' isn't in glyphs! "
                    "({members})").format(group=self.group, members=list(self.program.alphabet.glyph_members())),
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
        for item in self.program.alphabet.glyph_members()[self.group]:
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
            image1=self.program.theme.photo['Order!']
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
        self.analang=self.code
        if not self.analang:
            return
        try:
            self.analang_obj=self.program.languages.get_obj(self.analang)
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
        self.wait=ui.Wait(parent=self.program.tk_root,msg=_("Setting up new LIFT file now."))
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
        w=ui.Window(self.program.tk_root,title=title)
        w.withdraw()
        w.mainwindow=False
        t=ui.Label(w.frame, text=title, font='title', row=0, column=0)
        inst=_("Which language would you like to study, in this demonstration "
                "of what {azt} can do?").format(azt=self.program.name)
        t=ui.Label(w.frame, text=inst, row=1, column=0, columnspan=2)
        self.cawldb=loadCAWL()
        # self.program.settings.langnames(self.cawldb.glosslangs)
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
        self.parent=self.program.tk_root
        self.program=program
        super(LiftChooser, self).__init__(self.parent)
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
