# coding=UTF-8
"""Sort button frame widgets, extracted from ui_shell.py to break
circular dependencies between sorting_engine and ui_shell."""
from utilities.i18n import _
from utilities import logsetup
log=logsetup.getlog(__name__)
from frontend import ui
from utilities import file, executables
try:
    from io_put import sound
except Exception as e:
    # optional (pyaudio & friends): sorting must work on a nosound machine —
    # this import killed boot on any install where pyaudio failed (2026-07-16).
    sound=None
    log.info(f"sound stack unavailable ({e}); play buttons will fall back "
             "to plain labels")

class SortButtonFrame(ui.ScrollingFrame):
    """This is the frame of sort group buttons."""
    def _profile_class_name(self):
        """The current syllable PROFILE CLASS for display in button labels, e.g.
        'C2V' (the stored key is already delimiter-free — see
        compose_profile_class)."""
        return str(self.program.slices.profile())
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
        if self.macrosort:
            newgroup=_("Other {check}").format(check=_("Letter"))
        else:
            newgroup=_("Other {check}").format(check=self.check)
        skiptext=_("Skip this item")
        if '=' in self.check and not self.macrosort:
            skiptext+=f" ({self.check.replace('=','≠')})"
        """This should just add a button, not reload the frame"""
        # The 'S' word-initial/word-final checks are CLOSED binaries — no
        # new-group ("Other"). (syls is open: it keeps the normal buttons.)
        closed=(self.cvt=='S'
                and self.program.params.is_syllable_boolean_check(self.check))
        # The 'S' PROFILE check: a new group is a new CV-profile WITHIN the class,
        # which must be a REAL, primitive-consistent value — so its new-group
        # affordance is the two-page picker (pick_syllable_profile), never the
        # integer stub add_int_group the other checks use. See ADR 0003.
        syl_profile=(self.cvt=='S'
                and not self.program.params.is_syllable_primitive_check(self.check))
        bf1=ui.Frame(parent, border=True, row=parent.nrows(), sticky='w')
        if closed:
            pass #fixed groups only; no "Other"/new-group button
        elif syl_profile:
            ui.Button(bf1, text=_("Other {cls} profile").format(
                            cls=self._profile_class_name()),
                        cmd=self.pick_syllable_profile,
                        anchor='w', relief='flat', font='instructions',
                        column=0, row=0, sticky='ew')
        elif not self.groups:
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
        # 'Not {profile}' — the presented word doesn't belong in its presorted CV
        # profile; unverify it (clears the profile DATA + sort-group annotation,
        # rebuilds slices) and advance so it's re-derived next presort. In the
        # choice list, after 'Other …' and before 'Skip'. Segmental/tone profile
        # sorts only (the syllable Task-2 has its own profile-class escape below).
        def notprofile():
            todo=self.task.itemstosort()
            if todo:
                self.task.unverify_profile(todo[0])
            sortnext() #advance with NO group chosen → maybesort restarts w/o it
        if (self.program.slices.profile() and self.cvt!='S'
                and not self.macrosort):
            bfnp=ui.Frame(parent, border=True, row=parent.nrows(), sticky='w')
            ui.Button(bfnp, text=_("Not {profile}").format(
                            profile=self.program.slices.profile()),
                        cmd=notprofile, anchor='w', relief='flat',
                        font='instructions', column=0, row=0, sticky='ew')
        vardict['skip']=ui.BooleanVar()
        # log.info("Making skip button")
        bf2=ui.Frame(parent, border=True, row=parent.nrows(), sticky='w')
        skipb=ui.Button(bf2, text=skiptext,
                        cmd=skip,
                        anchor='w',
                        relief='flat',
                        font='instructions',
                        column=0, row=0, sticky='ew')
        # 'S' profile sort: escape hatch — "this word isn't in this profile class".
        if (self.cvt=='S'
                and not self.program.params.is_syllable_primitive_check(self.check)):
            bf3=ui.Frame(parent, border=True, row=parent.nrows(), sticky='w')
            ui.Button(bf3, text=_("This word doesn’t belong in this {cls} profile "
                        "at all…").format(cls=self._profile_class_name()),
                        cmd=self.syllable_escape_window,
                        anchor='w', relief='flat', font='instructions',
                        column=0, row=0, sticky='ew')
    def syllable_escape_window(self):
        """The word in front of the user is in the wrong profile class. Offer the
        four one-axis moves (flip word-initial / flip word-final / Shorter /
        Longer); each re-buckets the word into a fully-named destination cell and
        advances. See docs/sort_syllables_design.md."""
        params=self.program.params
        ftype=self.task.ftype
        analang=self.program.db.analang
        senses=self.task.itemstosort()
        if not senses:
            return
        sense=senses[0]
        beg=sense.annotationvaluebyftypelang(ftype,analang,'#C')
        end=sense.annotationvaluebyftypelang(ftype,analang,'C#')
        syls=sense.annotationvaluebyftypelang(ftype,analang,'syls')
        try:
            n=int(syls)
        except (TypeError,ValueError):
            n=1
        flip=lambda v:'V' if v=='C' else 'C'
        # (button label = destination profile-class prose, primitive check, new value)
        moves=[(params.profile_class_prose(flip(beg),syls,end),'#C',flip(beg)),
                (params.profile_class_prose(beg,syls,flip(end)),'C#',flip(end))]
        if n>1:
            moves.append((_("Shorter — ")+params.profile_class_prose(beg,str(n-1),end),
                        'syls',str(n-1)))
        moves.append((_("Longer — ")+params.profile_class_prose(beg,str(n+1),end),
                        'syls',str(n+1)))
        w=ui.Window(self, title=_("Where does this word belong?"), exit=False)
        def apply(check,value):
            # flip one primitive → the word's profile class changes → it leaves this
            # slice. Persist immediately (power-fault tolerant), then ADVANCE within
            # the current class (don't kick the user out): drop the word from the
            # live to-sort list and set _notprofile_advance so sortselected advances
            # instead of reading the now-empty selection as Exit (which fired the
            # spurious 'not done' warning). The word re-derives into its new class,
            # unsorted, to be handled there later. Mirrors 'Not {profile}'.
            sense.annotationvaluebyftypelang(ftype,analang,check,value)
            try:
                tosort=self.program.status.sensestosort()
                if tosort and sense in tosort:
                    tosort.remove(sense)
            except Exception as e:
                log.info("escape tosort-drop skipped: %s", e)
            self.task._notprofile_advance=True
            self.program.status_dirty=True   # current slice rebuilds (minus this word)
            self.task.maybewrite()
            w.destroy()
            if getattr(self,'sortitem',None):
                self.sortitem.destroy()  # advance to the next word
        for r,(label,check,value) in enumerate(moves):
            ui.Button(w.frame, text=label, cmd=lambda c=check,v=value:apply(c,v),
                        anchor='w', font='instructions', row=r, column=0, sticky='ew')
        ui.Button(w.frame, text=_("Cancel"), cmd=w.destroy,
                    anchor='c', font='instructions', row=len(moves), column=0, sticky='ew')
    def pick_syllable_profile(self):
        """'Other {profile class} profile' — page 1. Offer a short, sane list of
        NEW legal profiles for this class (generated simplest-first, excluding the
        profiles already sorted here), plus 'Other…' → a by-hand entry page.
        Picking one sorts the current word into that real, primitive-consistent
        profile (via sortselected's _pending_new_profile path). See ADR 0003 /
        cv_group_creation_merging."""
        params=self.program.params
        beg,syls,end=params.parse_profile_class(self.program.slices.profile())
        if beg is None:
            log.info("pick_syllable_profile: no profile class set; ignoring.")
            return
        options=params.unused_profiles_for_class(beg,syls,end,limit=12)
        cls=self._profile_class_name()
        w=ui.Window(self,title=_("Which {cls} profile?").format(cls=cls),exit=False)
        ui.Label(w.frame,text=_("Which profile fits this word?"),
                    font='instructions',row=0,column=0,sticky='ew')
        r=1
        for prof in options:
            ui.Button(w.frame,text=prof,
                        cmd=lambda p=prof:self._resolve_new_profile(w,p),
                        anchor='w',font='normal',row=r,column=0,sticky='ew')
            r+=1
        if not options:
            ui.Label(w.frame,text=_("(every simple profile here is already used)"),
                        font='instructions',row=r,column=0,sticky='ew'); r+=1
        # Nav at the bottom, after the options.
        ui.Button(w.frame,text=_("Other… (set a profile by hand)"),
                    cmd=lambda:self._syllable_profile_freeentry(w,beg,syls,end),
                    anchor='w',relief='flat',font='normal',
                    row=r,column=0,sticky='ew'); r+=1
        ui.Button(w.frame,text=_("Cancel — go back"),cmd=w.destroy,
                    anchor='w',relief='flat',font='normal',
                    row=r,column=0,sticky='ew')
    def _resolve_new_profile(self,w,profile):
        """A profile was chosen/entered: record it so sortselected marks the
        current word into it (the normal new-group path), close the picker, and
        advance by destroying the sort item (ends the sort wait)."""
        self._pending_new_profile=profile
        try:
            w.destroy()
        except Exception:
            pass
        if getattr(self,'sortitem',None):
            self.sortitem.destroy()
    def _syllable_profile_freeentry(self,page1,beg,syls,end):
        """'Other {profile class} profile' — page 2. Type a profile by hand, with a
        warning to work with a linguist and a Back button. The entry is validated
        against the class primitives (word-initial/final + syllable count) before
        it is accepted."""
        page1.destroy()
        params=self.program.params
        p=self.program.sort_ui
        cls=self._profile_class_name()
        # The profiles already IN PLAY for this class (same set the side column
        # lists) — used to EXCLUDE them from the "e.g." examples too, so the hint
        # never suggests one the user is told not to re-enter.
        inplay=sorted(g for g in (self.groups or []) if g not in ('NA',))
        # Example PROFILES (not the class key) in this class — the two simplest that
        # are NOT already in play. legal_profiles_for_class has no upper bound, so
        # even after excluding the in-play ones it still yields more. The class key
        # (C2V) is NOT a typeable profile, so it must never appear here.
        eg=' or '.join(params.legal_profiles_for_class(
                    beg,syls,end,exclude=set(inplay),limit=2))
        w=ui.Window(self,title=_("Set a {cls} profile by hand").format(cls=cls),
                    exit=False)
        warn=ui.Label(w.frame,text='\n'.join([
            _("⚠ Setting a profile by hand is a linguist’s "
            "call — work with your language team."),
            _("A wrong profile mis-describes the "
            "word’s syllable structure."),
            _("This one must be {beg}-initial, {end}-final, and "
            "{n} syllable(s)").format(beg=beg,end=end,n=syls),
            _("(use C and V, e.g. {eg}).").format(eg=eg)]),
            font='instructions',row=0,column=0,columnspan=2,sticky='ew')
        warn.wrap()
        var=p.string_var(value='')
        p.entry_field(w.frame,text=var).grid(row=1,column=0,sticky='ew')
        msg=ui.Label(w.frame,text='',font='instructions',row=2,column=0,
                    columnspan=2,sticky='ew')
        def submit():
            prof=(var.get() or '').strip().upper()
            if not params.profile_fits_class(prof,beg,syls,end):
                msg.configure(text=_("‘{p}’ isn’t {beg}-initial, {end}-final, {n} "
                    "syllable(s) — try again.").format(
                        p=prof or '—',beg=beg,end=end,n=syls))
                return
            # New or already-existing profile both flow through the pending path
            # (sortselected's addgroupbutton is guarded against double-adding).
            self._resolve_new_profile(w,prof)
        ui.Button(w.frame,text=_("Use this profile"),cmd=submit,anchor='c',
                    font='instructions',row=3,column=0,sticky='ew')
        ui.Button(w.frame,text=_("← Back"),
                    cmd=lambda:(w.destroy(),self.pick_syllable_profile()),
                    anchor='c',font='instructions',row=3,column=1,sticky='ew')
        # Second column: the profiles already IN PLAY for this class (computed
        # above), so the user can see what NOT to re-enter (this page is for a NEW
        # profile) — the same set excluded from the examples.
        side=ui.Frame(w.frame)
        side.grid(row=0,column=2,rowspan=4,sticky='nw',padx=12)
        ui.Label(side,text=_("\nAlready in play here —\ndon’t re-enter these:"),
                    font='instructions',row=0,column=0,sticky='w')
        for i,g in enumerate(inplay or [_("(none yet)")]):
            ui.Label(side,text=g,font='normal',row=i+1,column=0,sticky='w')
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
            scaledpady=int(40*self.theme.scale)
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
    def reflow(self):
        """Recompute the scroll content's size SYNCHRONOUSLY (vs the debounced,
        <Configure>-driven reflow). Call once the full geometry is settled (after
        the run window's update()): the content is a canvas-embedded frame, so a
        reflow that runs mid-build can pin it to a partial height. With
        ``_hug_content`` set (in __init__), _do_configure_interior also sizes the
        scroll frame's own height to its content's reqheight, so the viewport hugs
        the buttons. Safe no-op if there's no scroll."""
        try:
            self._do_configure_interior()  # scrollregion + canvas size + hug height
        except Exception as e:
            log.info("SortButtonFrame.reflow failed: %s", e)
    def __init__(self, parent, task, groups, *args, **kwargs):
        self.macrosort=kwargs.pop('macrosort',False)
        self.remove_on_click=kwargs.pop('remove_on_click',False)
        self.show_check=kwargs.pop('show_check',False)
        self.task=task
        self.program=self.task.program
        self.groups=groups
        super(SortButtonFrame, self).__init__(parent, *args, **kwargs)
        # The sort (item-at-a-time) page holds a small set of group buttons and
        # wants the scroll viewport to HUG them — so any later content growth (a
        # new group button created mid-sort, or a slow example image) re-sizes the
        # frame and never clips Other/Not-profile/Skip. The macrosort VERIFY page
        # (remove_on_click) can hold many items, so it keeps a fixed scrolling
        # viewport instead. See ScrollingFrame._do_configure_interior.
        self._hug_content = not self.remove_on_click
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
        if self.macrosort and not self.remove_on_click:
            msg=[_("Gathering groups"),
                _("On the next screen, you will sort groups of words into letter groups")]
            self.buttoncolumns=1
        elif self.macrosort:
            msg=[_("Verifying groups"),
                _("On the next screen, you will verify groups of words as belonging together")]
            self.buttoncolumns=1
        else:
            msg=[_("Sorting words"),
                _("On the next screen, you will sort words into groups "
                "by {cvt}").format(cvt=self.program.params.cvcheckname())]
            self.buttoncolumns=self.task.buttoncolumns
        with task.waiting('\n'.join(msg)):
            # Prefetch examples for all groups at once to avoid O(N^2) lookup
            self.program.examples.prefetch_examples(self.groups, **kwargs)

            for i, group in enumerate(self.groups):
                self.addgroupbutton(group)
                task.waitprogress(i * 100 // max(len(self.groups),1))
            if not self.remove_on_click:
                self.getanotherskip(self.content.anotherskip,self.groupvars)
        # Force one scroll reflow now that ALL group buttons + skip exist. The
        # content is a canvas-embedded frame: if a reflow ran MID-BUILD (the event
        # loop pumped during a slow example load for a later group — e.g. the 2 s
        # compound V1=V2 regex/image), it pinned the content window to the partial
        # height; further buttons then grow the REQUESTED height but not the pinned
        # actual height, so content's <Configure> never re-fires and the scrollregion
        # stays clamped to the first button (later buttons + skip clipped,
        # unscrollable). Re-arm a reflow (run window's update() flushes it with the
        # full reqheight) — the verify path does the equivalent via resume_configure.
        try:
            self.content.master.master._configure_interior()
        except Exception as e:
            log.info("SortButtonFrame scroll reflow re-arm failed: %s", e)
class _GroupButtonFrame(object):
    unbuttonargs=['renew','canary','labelizeonselect',
                        'label','playable','unsortable',
                        'alwaysrefreshable','wsoundfile',
                        'showtonegroup', 'remove_on_click',
                        'goback','all_for_cvt', 'on_select',
                        'show_check',
                        'gridwait', #frame-only: must NOT reach child buttons,
                        #or they grid_remove themselves and never restore
                        #(macrosort glyph-member buttons rendered blank)
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
    def getexample(self,**kwargs):
        kwargs['showtonegroup']=self.kwargs.get('showtonegroup', False)
        data=self.exs.get_button_data(self.group, **kwargs)
        self.updatecount(data['count'])
        self.hasexample='text' in data
        if not self.hasexample:
            self._filenameURL=None
            log.error(_("SortGroupButtonFrame.getexample returned None for {group} {kwargs}").format(group=self.group, kwargs=kwargs))
            return
        self._filenameURL=data['audio_url']
        self._sense=data['sense']
        self._text=data['text']
        self._illustration=None
        if self._sense is None:
            return 1
        self._illustration=self.program.sort_ui.set_sense_illustration(self._sense)
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
        if sound is None: #no sound stack on this machine; show a plain label
            self.labelbutton()
            return
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
        if (self.program.praat
                and not str(self._filenameURL).lower().endswith('.m4a')):
            # praat can't read m4a: no bind, and no tooltip advertising it
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
        # cvprofile on a line ABOVE the check, in ONE label (same cell) so the
        # profile difference is visible (CVCC over V1 vs CVC over V1) WITHOUT
        # adding a grid row / making the button taller.
        profile=self.kwargs.get('profile')
        text=f"{profile}\n{self.check}" if profile else self.check
        ui.Label(self, text=text, column=self.ncolumns())
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
        """this should take the ui parent and logical/backend parent (task)"""
        # log.info(_("Initializing buttons for group {group}").format(group=group))
        self.task=task #NOT the task/check OR the scrollingframe! use self.check.task
        self.program=self.task.program
        self.exs=self.program.examples
        try:
            self.code=self.program.alphabet.verificationcode(**kwargs)
        except Exception:
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
        log.debug(_("Ready to build SortGroupButtonFrame with {kwargs}").format(kwargs=kwargs))
        self.items.append(SortGroupButtonFrame(self, self.task, **kwargs))
        log.debug(_("Built SGBF for {item} ({items})").format(item=item, items=self.items))
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
        """this should take the ui parent and logical/backend parent (task)"""
        self.task=task #NOT the task/check OR the scrollingframe! use self.check.task
        self.program=self.task.program
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
            ui.Label(self,text=_("group ‘{group}’ isn’t in glyphs! "
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
            log.debug(_("Making Glyph member {item} button").format(item=item))
            self.make_sgbf(item, **kwargs)
        if self.items:
            self.updatecount()
            self.show_one()
        log.info(_("Built SortGlyphGroupButtonFrame for {group}").format(group=self.group))
