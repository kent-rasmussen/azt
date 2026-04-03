# coding=UTF-8
"""Sort button frame widgets, extracted from ui_shell.py to break
circular dependencies between sorting_engine and ui_shell."""
from utilities.i18n import _
from utilities import logsetup
log=logsetup.getlog(__name__)
from frontend import ui_tkinter as ui
from utilities.utilities import exampletype
from utilities import file, executables
from io_put import lift, sound

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
        self.destroy() # will this keep the variable around, if stored elsewhere?
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
        from main import scaleimageifthere
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
        # self.button_borderwidth=7 # width of relief
        self.button_borderwidth=15 # width of relief
        self.refresh_borderwidth=10 # width of relief
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
