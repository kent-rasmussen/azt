# coding=UTF-8
import sys
import collections
import re
import datetime
import time
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
import itertools
# import inspect
# import multiprocessing

log=logsetup.getlog(__name__)

from utilities.error_handler import notify_error as ErrorNotice

from utilities.i18n import _
from backend.core.lexicon import Tone
from backend.core.categories import Categories
from backend.core.analysis import SyllableSliceDict


class SyllablePrep(object):
    """Task 1 (syllable PREP) driver — see docs/syllable_sort_redesign.md. Mixed
    into SortSyllables BEFORE Sort so runcheck routes the three primitive checks
    (#C/C#/syls) through a DEDICATED per-slice verify loop (maybeverifysyllables),
    NOT maybesort — prep never sorts/joins/macrosorts, only verifies one ≤MAX_SLICE
    slice at a time. Each slice is a single-page list, so the XWayland
    page-transition freeze is designed out. Once every slice is verified
    (params.syllable_prep_complete) runcheck hands off to Task 2 (the profile-class
    profile sort) via the inherited Sort.runcheck/maybesort."""

    def syllable_slices(self,rebuild=False):
        """The current ps's prep-slice object (built/assigned + status synced)."""
        ps=self.program.slices.ps()
        ftype=self.program.params.ftype()
        sl=getattr(self.program,'syllable_slices',None)
        if sl is None or rebuild or sl.ps!=ps or sl.ftype!=ftype:
            sl=SyllableSliceDict(self.program,ps,ftype)
        sl.build()
        return sl

    def runcheck(self):
        ps=self.program.slices.ps()
        if self.program.params.syllable_prep_complete(ps):
            # Task 1 done → Task 2 (profile-class profile sort) on the shared engine.
            # Point the engine at the profile (ftype) check, not a stale primitive.
            self.program.params.check(self.program.params.ftype())
            return super().runcheck()
        # Task 1: seed the per-word primitives by orthography (Syllables.
        # presortgroups), assign stable ≤MAX_SLICE slices, then drive per-slice
        # verify. No maybesort.
        self.program.settings.storesettingsfile()
        gen=self.presortgroups()
        def after_presort():
            # The per-slice lookahead preload (verify_slice) keeps each slice's
            # images cached; the 1.3.18/.19 full-wordlist preload was a DIAG (cache-
            # exoneration test) that hoarded all ~1700 images → ~4 GB RSS. Removed:
            # cache is exonerated for the FREEZE, and we're now testing whether that
            # 4 GB was slowing the per-item RENDER (memory/X pressure).
            self.syllable_slices(rebuild=True) #assign slices + sync status groups
            self.maybeverifysyllables(firstrun=True)
        self._get_safe_window().drive_work(gen,on_done=after_presort)

    def maybeverifysyllables(self,firstrun=False):
        """Event-driven prep loop. Builds the next unverified slice's content into
        ONE reused run window and returns; the OK button (canary <Destroy>) marks
        the slice verified and advances. Two deliberate choices, both to dodge the
        XWayland deadlock the segmental page loop already dodges:
          1. REUSE one run window across all slices (rebuild only its content) —
             never destroy+recreate the kiosk-fullscreen window per slice. The
             per-slice teardown/recreate (a fullscreen map still in flight) right
             before a blocking call is what wedged; segmental builds the window
             once and only its page loop rebuilds content.
          2. No wait_window — advance from the button callback. Belt-and-suspenders
             so even the once-built window is never blocked-on mid-transition."""
        if self.ui.exitFlag.istrue():
            return
        sl=self.syllable_slices()
        nxt=sl.next_unverified_slice()
        if nxt is None:
            # Every prep slice verified → Task 1 complete. Close the reused window,
            # refresh the board (now the Task-2 profile-class board), tell the user.
            rw=getattr(self.ui,'runwindow',None)
            if rw is not None and rw.winfo_exists() and not rw.exitFlag.istrue():
                rw.on_quit()
            self.status.maybeboard()
            ErrorNotice(text=_("All the syllable groups are checked! You can now "
                        "sort the words by syllable profile."),
                        title=_("Done!"),wait=False,parent=self)
            return
        check,group,idx=nxt
        self.program.params.check(check)
        self.check=check
        self.ps=sl.ps
        self.profile=sl.sentinel
        self.verify_slice(sl,check,group,idx)

    def select_prep_slice(self,check,group,idx):
        """User clicked a prep-board cell: SELECT that slice as the next one to
        verify (override app navigation) and move the board highlight — but do NOT
        launch. The user then clicks 'Sort!' (runcheck), which starts there. Stored
        on program so it survives runcheck's SyllableSliceDict rebuild. (Other sort
        tasks select-then-Sort; this matches them. A future change may switch to
        click-to-launch.)"""
        self.program.syllable_preferred_slice=(check,group,idx)
        self.status.update_active_prep_cell()

    def _prep_runwindow(self):
        """The reused prep run window: keep the existing one (just clear its frame
        for the next slice), creating one only if there isn't a live one. Reusing
        it means no fullscreen destroy/recreate transition between slices."""
        rw=getattr(self.ui,'runwindow',None)
        if rw is not None and rw.winfo_exists() and not rw.exitFlag.istrue():
            for w in list(rw.frame.winfo_children()):
                w.destroy()
            return rw
        self.ui.getrunwindow()
        return self.ui.runwindow

    def verify_slice(self,sl,check,group,idx):
        """Read-aloud verify of ONE slice (single page, content built into the
        reused window — no Wait dialog, no wait_window). Flag-outs move via the
        misfit rule (verifybutton.notok reads self._prep_verify); OK destroys the
        canary, which marks the slice verified and advances."""
        items=sl.members_in_slice(check,group,idx)
        items.sort(key=lambda s:sl.slice_key(check,s))
        nslices=len(sl.slices_of(check,group))
        if len(items)<=1:
            sl.mark_slice(check,group,idx,verified=True) #nothing to read aloud
            self.after(10,self.maybeverifysyllables) #auto-advance
            return
        desc=self.program.params.syllable_group_name(check,group)
        if nslices>1:
            desc=_("{desc} (part {x} of {y})").format(desc=desc,x=idx+1,y=nslices)
        title=[_("Verify {language}").format(
                language=self.program.settings.languagenames[self.analang]),desc]
        oktext=_("These are all {desc}").format(desc=desc)
        instructions=_("Read this list aloud. Click on any that are NOT "
                    "{desc}.").format(desc=desc)
        prep=_("Loading the words that are {desc}…").format(desc=desc)
        self.currentsortitems=items
        self.program.status.group(group)
        self.group=group
        self._prep_verify=(sl,check,group,idx)
        rw=self._prep_runwindow()
        if rw is None or rw.exitFlag.istrue():
            self._prep_verify=None
            return
        self.buttonframe,self.verifycanary=self.sort_ui.build_verify_layout(
            rw,title,self.pageicon(False),instructions,
            None,'',group,items,self,False,oktext,
            self.min_to_multicolumn,self.buttoncolumns,self.verifybutton,
            join_fn=self.join,prep=prep)
        if self.verifycanary is None or rw.exitFlag.istrue():
            self._prep_verify=None
            return
        # OK (canary.destroy) or a window-close both fire <Destroy>; defer so we
        # don't act mid-teardown, then advance unless the user quit.
        self.verifycanary.bind('<Destroy>',
            lambda e=None,c=check,g=group,i=idx:
                self.after(10,lambda:self._finish_prep_slice(sl,c,g,i)))
        # This slice is now up and the user is reading it aloud — a window during
        # which the next slices' images can be decoded+resized off the Tk thread,
        # so their build is just the cheap PhotoImage compile. (The I/O-bound
        # per-slice build cost is the real wedge at larger slices; this hides it.)
        try:
            self.sort_ui.preload_images(
                sl.preload_uris(check,group,idx,sl.preload_lookahead))
        except Exception as e:
            log.info("syllable preload skipped: %s", e)

    def _finish_prep_slice(self,sl,check,group,idx):
        self._prep_verify=None
        rw=getattr(self.ui,'runwindow',None)
        if rw is None or not rw.winfo_exists() or rw.exitFlag.istrue():
            # User closed the window → pause prep (no advance). Refresh the board
            # so the slices verified before closing show their ✓ when the task
            # window comes back, matching the per-completion maybeboard() the
            # other sort checks fire (e.g. sorting_engine.py nextcheck path).
            self.status.maybeboard()
            return #user closed the window → pause prep (no advance)
        sl.mark_slice(check,group,idx,verified=True)
        self.maybewrite()
        # Reuse the SAME window for the next slice (no on_quit/recreate churn).
        self.after(10,self.maybeverifysyllables)


class Sort(Categories):
    """This class takes methods common to all sort checks, and gives sort
    checks a common identity."""
    show_buttoncolumnsline=True #does this belong here?

    def _get_safe_window(self):
        """Return runwindow if it exists and is viewable, else tk_root."""
        try:
            assert self.ui.runwindow.winfo_exists(),"runwindow attr may be there, but no widget"
            return self.ui.runwindow
        except (AttributeError,AssertionError) as e:
            log.info(str(e))
            return self.ui.getrunwindow()

    def _safe_quit_runwindow(self):
        """Quit runwindow if it exists, silently ignore if not."""
        try:
            self.ui.runwindow.on_quit()
        except AttributeError:
            log.info("Looks like we wanted to kill a non-existent runwindow.")
    @property
    def sort_ui(self):
        """Lazy-init presenter; available after task init wires program.sort_ui."""
        return self.program.sort_ui
    def get_frame(self):
        if self.cvt != 'T': # not for segmental checks
            return 
        frames=self.program.toneframes.get(self.ps)
        if frames and self.check in frames:
            return frames.get(self.check)
        else:
            text=_("Looking for tone check '{check}', but not "
                    "in {ps} frames: {frames}").format(check=self.check, ps=self.ps, frames=frames)
            ErrorNotice(text,wait=True)
    def updatestatuslift(self,verified=False,**kwargs):
        """This should be called only by update status, when there is an actual
        change in status to write to file."""
        check=kwargs.get('check',self.program.params.check())
        group=kwargs.get('group',self.program.status.group())
        profile=kwargs.get('profile',self.program.slices.profile())
        ftype=kwargs.get('ftype',self.program.params.ftype())
        # profile=self.program.slices.profile()
        # Target the group ACTUALLY being (un)verified — not the current one.
        # getsensesincheckgroup() defaulted to status.group(), so unverifying a
        # specific group (e.g. join's updatestatus(group=lpr[1], verified=False))
        # stripped the verification code off whatever group happened to be
        # current — greedily unverifying an unrelated, already-done group.
        senses=self.getsensesincheckgroup(check=check,group=group)
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
        _inslice=list(self.program.slices.inslice(senses)) #only for this ps-profile
        # DIAG-done (temporary, poss. 1 root): EVERY verify write — list exactly
        # which senses get the code, the group NAME and its python TYPE (to catch a
        # glyph/int name flip), and the add/remove value. If the read-side later
        # shows a member with no code, compare: absent from this write
        # (getsensesincheckgroup/inslice missed it / wrong name) or failed to persist?
        log.info("DIAG-done write %s=%r (%s) profile=%s verified=%s add=%r rms=%r "
                 "-> coding %d/%d inslice senses: %s (full group %s)",
                 check, group, type(group).__name__, profile, verified, add, rms,
                 len(_inslice), len(senses), [s.id for s in _inslice],
                 [s.id for s in senses])
        # Syllable PROFILE check (check==ftype): verification lives ONLY in the
        # plain …-x-cvprofile form (the single source of truth) — NOT as an
        # lc=<profile> code in the <profile-class> lc verification field. So set/clear
        # …-x-cvprofile and DON'T write a code. Every other check (segmental
        # V1/C1…, primitives) keeps its check=group code.
        if self.cvt=='S' and check==ftype:
            for sense in self.program.slices.inslice(senses):
                sense.cvprofilevalue(ftype, group if verified else False)
        else:
            for sense in _inslice:
                self.modverification(sense,profile,check,add)
        if kwargs.get('write'):
            self.maybewrite() #for when not iterated over, or on last repeat
    def updatestatus(self,verified=False,**kwargs):
        #This function updates the status variable, not the lift file.
        group=kwargs.get('group',self.program.status.group())
        write=kwargs.get('write')
        wstatus=kwargs.get('writestatus')
        r=self.program.status.update(group=group,verified=verified,writestatus=wstatus)
        if r: #only do this if there is a change in status
            self.updatestatuslift(group=group,verified=verified,write=write)
            return r
    def addmodadhocsort(self):
        p = self.sort_ui
        def submitform():
            if profilevar.get() == '':
                log.debug("Give a name for this adhoc sort group!")
                return
            self.ui.runwindow.on_quit()
            ids=[]
            for var in [x for x in vars if len(x.get()) >1]:
                # log.info("var {}: {}".format(vars.index(var),var.get()))
                ids.append(var.get())
            # log.info("ids: {}".format(ids))
            newprofile=profilevar.get()
            self.program.settings.set('profile',newprofile,refresh=False)
            #Add to dictionaries before updating them below
            log.debug("profile: {}".format(newprofile))
            """Fix this!"""
            self.program.slices.adhoc(ids,profile=newprofile)#[ps][profile]=ids
            self.program.settings.storesettingsfile(setting='adhocgroups')#since we changed this.
            """Is this OK?!?"""
            self.program.slices.updateslices() #This pulls from profilesbysense
            # self.makecountssorted() #we need these to show up in the counts.
            #so we don't have to do this again after each profile analysis
        self.ui.getrunwindow()
        profile=self.program.slices.profile()
        ps=self.program.slices.ps()
        if profile in [x[0] for x in self.program.slices.profiles()]: #profilecountsValid]:
            new=True
            title=_("New Ad Hoc Sort Group for {ps} Group").format(ps=ps)
        else:
            new=False
            title=_("Modify Existing Ad Hoc Sort Group for {group} Group").format(group=ps)
        self.ui.runwindow.title(title)
        p.label(self.ui.runwindow.frame,text=title,font='title',
                ).grid(row=0,column=0,sticky='ew')
        allpssenses=self.program.slices.sensesbyps(ps)
        if len(allpssenses)>70:
            self.ui.runwindow.waitdone()
            text=_("This is a large group ({count})! Are you in the right "
                    "lexical category?").format(count=len(allpssenses))
            log.error(text)
            w=p.label(self.ui.runwindow.frame,text=text)
            w.grid(row=1,column=0,sticky='ew')
            b=p.button(self.ui.runwindow.frame, text=_("OK"), command=w.destroy, anchor='c')
            b.grid(row=2,column=0,sticky='ew')
            self.ui.runwindow.wait_window(w)
            w.destroy()
        if self.ui.runwindow.exitFlag.istrue():
            return
        self.ui.runwindow.wait()
        try:
            p.label(self.ui.runwindow.frame,text=title,font='title',
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
                    "").format(ps=ps)
            inst=p.label(self.ui.runwindow.frame,text=text,
                    row=1,column=0,sticky='ew'
                    )
            inst.wrap()
            qframe=p.frame(self.ui.runwindow.frame)
            qframe.grid(row=2,column=0,sticky='ew')
            text=_("What do you want to call this group for sorting {ps} words?"
                    "").format(ps=ps)
            instq=p.label(qframe,text=text,
                    row=0,column=0,sticky='ew',pady=20)
            if new:
                default=None
            else:
                default=profile
            profilevar=p.string_var(value=default)
            namefield = p.entry_field(qframe,text=profilevar)
            namefield.grid(row=0,column=1)
            text=_("Select the {ps} words below that you want in this group, then "
                    "click ==>").format(ps=ps)
            p.label(qframe,text=text).grid(row=1,column=0,sticky='ew',pady=20)
            sub_btn=p.button(qframe,text = _("OK"),
                      command = submitform,anchor ='c')
            sub_btn.grid(row=1,column=1,sticky='w')
            vars=list()
            row=0
            scroll=p.scrolling_frame(self.ui.runwindow.frame)
            for idn,sense in enumerate(allpssenses):
                log.debug("id: {}; index: {}; row: {}".format(sense.id,idn,row))
                # idn=allpssenses.index(sense)
                vars.append(p.string_var())
                adhocslices=self.program.slices.adhoc()
                if (ps in adhocslices and profile in adhocslices[ps] and
                                            sense in adhocslices[ps][profile]):
                    vars[idn].set(sense)
                else:
                    vars[idn].set(0)
                forms=sense.formatted()
                log.debug("forms: {}".format(forms))
                p.check_button(scroll.content, text = forms,
                                    variable = vars[idn],
                                    onvalue = id, offvalue = 0,
                                    ).grid(row=row,column=0,sticky='ew')
                row+=1
            scroll.grid(row=3,column=0,sticky='ew')
        finally:
            self.ui.runwindow.waitdone()
        self.ui.runwindow.wait_window(scroll)
    def ncheck(self):
        r=self.program.status.nextcheck(tosort=True)
        if r:
            self.program.settings.setcheck(r)
        else:
            self.program.settings.setcheck(toverify=True)
        #if neither, this should call nprofile
        self._safe_quit_runwindow()
        self.runcheck()
    def nprofile(self):
        r=self.program.status.nextprofile(tosort=True)
        if r:
            self.program.settings.setprofile(r)
        else:
            self.program.settings.setprofile(toverify=True)
        self._safe_quit_runwindow()
        self.runcheck()
    def nps(self):
        self.program.slices.nextps()
        r=self.program.status.nextprofile(tosort=True)
        if not r:
            self.program.status.nextprofile(toverify=True)
        self._safe_quit_runwindow()
        self.runcheck()
    def _affirm_scope_text(self,affirmable,ftype):
        """Human summary of WHAT 'Trust' would affirm, so the choice isn't blind:
        each unprofiled+affirmable word with its confirmed primitives (#C/C#/syls)
        and the machine profile that would become its trusted profile. Lists them
        when fewer than 10; otherwise just the count, to keep the dialog legible."""
        analang=self.program.db.analang
        n=len(affirmable)
        if n>=10:
            return _("{n} words here would be affirmed to their machine profile.").format(n=n)
        av=lambda s,c: s.annotationvaluebyftypelang(ftype,analang,c) or '?'
        lines=[]
        for s in affirmable:
            form=s.textvaluebyftypelang(ftype,analang) or '—'
            machine=s.cvprofilemachinevalue(ftype)
            # Show what Trust would ACTUALLY assign: the machine profile CONSTRAINED
            # to the word's primitives (what affirm_machine_profiles does), not the
            # raw machine read.
            trusted=self.program.profiles.constrain_presort_profile(s,machine,ftype) \
                    or machine or '?'
            lines.append("{f}  (#C={b} C#={e} syls={y})  → {m}".format(
                f=form, b=av(s,'#C'), e=av(s,'C#'), y=av(s,'syls'), m=trusted))
        return '\n'.join(lines)
    def offer_profile_setup(self,at_open=False):
        """A segmental/tone sort works on syllable-profile DATA. If a word in this
        ps lacks a confirmed profile but HAS an affirmable machine analysis, warn —
        offer to affirm the machine analysis or go sort syllable profiles first
        (those words won't be sorted for anything until profiled). Fires when the
        sort page OPENS, on the 'Sort!' press, and when advancing to a new
        profile/check — but only ONCE per batch of newly-unsorted words: the gate
        (_offered_profile_setup) is re-armed by unverify_profile ('Not {profile}'),
        so a freshly unsorted word triggers it again without nagging otherwise.
        Does NOT launch the syllable task itself — the caller tears down this task
        first, THEN launches, so the two sort boards never coexist.
        Returns the user's choice ('affirm'/'sort'/'cancel') or None if not
        offered."""
        if self.program.params.cvt()=='S': # the syllable sort has its own flow
            return None
        # Once-per-batch gate: set when we offer (below), cleared by
        # unverify_profile when a word is sent back via 'Not {profile}'.
        if getattr(self,'_offered_profile_setup',False):
            return None
        ftype=self.program.params.ftype()
        ps=self.program.slices.ps()
        senses=self.program.db.sensesbyps.get(ps,[])
        # Only count words that affirming/sorting could actually profile: no
        # confirmed profile yet, but a real machine analysis to affirm. Words with
        # no/Invalid machine analysis can never be affirmed, so they must not keep
        # the prompt alive forever (once affirmed, 'Trust' fully silences it).
        def _affirmable(s):
            return (not s.cvprofilevalue(ftype)
                    and s.cvprofilemachinevalue(ftype) not in (None,'','Invalid'))
        _affirm=[s for s in senses if _affirmable(s)]
        if not _affirm:
            return None # nothing left that affirming/sorting would profile
        self._offered_profile_setup=True
        note=_("Some of these words have no syllable profile yet, so "
                # "Segmental and tone sorts work on syllable-profile data — "
                # "a word that hasn't been sorted (or affirmed) for its "
                # "syllable profile "
                "they won't be sorted here either.")
        scope=self._affirm_scope_text(_affirm,ftype)
        choice=self.sort_ui.offer_profile_setup(self.ui,note,scope)
        if choice=='affirm':
            self.program.profiles.affirm_machine_profiles() # fill holes
            # …and repair existing trusted profiles: constrain any that violate
            # their verified primitives and realign drifted sort-group annotations
            # (the stale 'lc' the old raw affirm left). Idempotent on clean data.
            self.program.profiles.reconcile_profiles_to_primitives()
            if at_open and getattr(self,'status',None):
                self.status.maybeboard() # refresh the now-populated profile board
        # 'sort' no longer launches here; the caller tears down this task first,
        # then opens SortSyllables (teardown-before-launch).
        return choice
    def runcheck(self):
        self.program.settings.storesettingsfile()
        # t=(_('Run Check'))
        log.info("Running check...")
        cvt=self.program.params.cvt()
        # The missing-profiles offer also fires here (on 'Sort!' and on advancing
        # to a new profile/check via ncheck/nprofile). On 'sort' we tear down THIS
        # live segmental task BEFORE opening the syllable sort, so the two boards
        # never coexist (the old concurrent-window bug). 'cancel' just aborts.
        if cvt!='S':
            choice=self.offer_profile_setup()
            if choice=='sort':
                self._safe_quit_runwindow()
                self.program.taskchooser.maketask('SortSyllables')
                return
            # 'affirm' / 'cancel' / None → keep sorting the words that DO have a
            # profile. 'cancel' means "not now" (set the rest aside), NOT abort the
            # whole check — so fall through and continue instead of returning.
        self.check=self.program.params.check()
        self.profile=self.program.slices.profile()
        if not self.profile:
            self.getprofile()
            self.profile=self.program.slices.profile()
        """further specify check check in maybesort, where you can send the user
        on to the next setting"""
        if (self.check not in self.program.status.checks() #tosort=True
                # and check not in self.program.status.checks(toverify=True)
                # and check not in self.program.status.checks(tojoin=True)
                ):
            exit=self.getcheck()
            if exit and not self.ui.exitFlag.istrue():
                return #if the user didn't supply a check
        gen=self.presortgroups()
        def after_presort():
            self.updatesortingstatus() # Not just tone anymore
            self.maybesort(firstrun=True)
        self._get_safe_window().drive_work(gen, on_done=after_presort)
    def marksorted(self,sense,group,verified=False):
        """These functions are only appropriate when sorting or unsorting senses.
        when moving stuff around between groups (in renaming groups), these don't 
        apply.
        """
        self.program.status.marksensesorted(sense)
        self.program.status.last('sort',update=True) #this will always be a change
        self.program.status.tojoin(True)
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
        self.ui.wait_window(w)
        self.group=self.program.status.group()
        self.program.status.undistinguish_any_with(g=self.group) #should be correct at this point
        self.maybesort(firstrun=True)
    def redo_joinglyphs(self,glyph=False):
        if not glyph:
            self.ui.wait_window(self.getglyph(purpose='join'))
        self.group=self.program.alphabet.glyph(glyph)
        self.program.alphabet.undistinguish_any_with(g=self.group) #should be correct at this point
        self._skip_predistinguish_once=True #don't let predistinguish re-hide it
        self.maybesort(firstrun=True)
    def maybesort(self,firstrun=False):
        """This should look for one group to verify at a time, with sorting
        in between, then join and repeat"""
        def tosortupdate():
            log.info("maybesort tosortbool:{tosortbool}; tosort:{tosort}; sorted (first 5):{sorted}"
                    "".format(
                                tosortbool=self.tosort(),
                                tosort=self.itemstosort(),
                                sorted=self.itemssorted()[:5]
                                ))
        def exitstatuses():
            try:
                log.info("Self exit status: {status}".format(status=self.ui.exitFlag.istrue()))
                log.info("Parent exit status: {status}".format(status=self.parent.exitFlag.istrue()))
                log.info("Parent return status: {status}".format(status=self.returned))
                log.info("Runwindow exit status: {status}".format(status=self.ui.runwindow.exitFlag.istrue()))
                log.info("Taskchooser exit status: {status}".format(status=self.program.taskchooser.exitFlag.istrue()))
            except Exception as e:
                log.info("Exception: {}".format(e))
        def warnorcontinue(return_value): #mostly for testing
            if self.ui.exitFlag.istrue():
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
        log.info("Starting maybesort with did={did}".format(did=[k for k,v in self.did.items() if v]))
        if self.ui.exitFlag.istrue(): #if the task has been shut down, stop
            return
        w=self._get_safe_window()
        # Refresh sorting status SYNCHRONOUSLY before the decision logic below
        # reads it. This used to drive the *global* reloadstatusdata() through
        # the async drive_work(), which (a) deferred its continuation via
        # after() so sort()/verify() ran before the reload finished — reading
        # a freshly-cleared, not-yet-repopulated groups dict ("No groups to
        # sort into!") — and (b) re-derived the entire lexicon every pass.
        # Neither is needed: only the CURRENT slice can have changed since the
        # last pass (a sort/verify/join mutates only the current check's
        # annotations), and maybesort's navigation reads sibling checks'/
        # profiles' tosort flags, which stay valid from their last build. So
        # rebuild just the current (cvt, ps, profile) — its checks — which
        # also avoids re-running load_ps_profiles() (already done once at LIFT
        # load) and the global clear_all_groups(). Skip even that when nothing
        # was written and we're still on the same slice. updatesortingstatus
        # overwrites the shared _sensestosort, so rebuild the current check
        # LAST so its to-sort list is the one left standing.
        slice_now=(self.program.params.cvt(), self.program.slices.ps(),
                    self.program.slices.profile(), self.program.params.check())
        if (firstrun or getattr(self.program,'status_dirty',True)
                or getattr(self,'_last_built_slice',None)!=slice_now):
            if any(i.mature for i in self.program.data_repo.values()):
                log.info("Found mature repo; showing wait")
                w.wait(_("Reloading status data"))
            else:
                log.info("Found new repo; not showing wait")
            self.program.settings.reloadstatusdatabycvtpsprofile() # current slice only
            self.program.settings.reloadstatusdata_cleanup() # cull: cheap; keeps done<=groups, stores
            if w.iswaiting():
                w.waitdone()
            self.updatesortingstatus(store=False) # current check LAST: fix shared _sensestosort
            self.program.status_dirty=False
            self._last_built_slice=slice_now
        elif not self.itemstosort():
            self.updatesortingstatus() # Not just tone anymore
        cvt=self.program.params.cvt()
        self.check=self.get_check()
        self.ps=self.get_ps()
        self.profile=self.get_profile()
        self.ftype=self.get_ftype()
        log.info("Maybe Sort")
        if self.checktosort(): # w/o parameters, tests current check
            if warnorcontinue(self.sort()):
                self.did['sort']=True
            return
        log.info("Maybe Verify")
        _vn=self.program.status.node()
        log.info("DIAG-join-verify maybesort node check=%s done=%s groups=%s",
                 self.program.params.check(),_vn.get('done'),_vn.get('groups'))
        groupstoverify=self.groups(toverify=True)
        if groupstoverify:
            log.info("Going to verify the first of these groups now: {groups}".format(
                                    groups=self.groups(toverify=True)))
            if self.program.status.group() not in groupstoverify:
                self.program.status.group(groupstoverify[0]) #just pick the first now
            if warnorcontinue(self.verify()):
                self.did['verify']=True
            return
        log.info("Maybe Join")
        self.did['join']=False #runs multiple times, so clear here
        # The 'S' primitive checks (#C/C#/syls) are closed/determined classes —
        # no joining. Only the profile check (within a profile class) joins.
        syl_primitive=(self.cvt=='S'
                        and self.program.params.is_syllable_primitive_check())
        if self.to_distinguish() and not syl_primitive:
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
        if self.cvt not in ('T','S'):
            log.info("Maybe Macrosort (with {did})".format(did=[k for k,v in self.did.items() if v]))
            if items := self.program.alphabet.renew_items_tomacrosort(self.cvt):
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
                        self.program.alphabet.presort_item(item) #only if no conflict
                # log.info("{items}".format(items=self.program.alphabet.itemstosort()))
                log.info("Running Macrosort")
                if warnorcontinue(self.sort(macrosort=True)):
                    self.did['macrosorttoglyphs']=True
                return
            log.info("Maybe Verifyglyphs")
            glyphstoverify=self.program.alphabet.glyphstoverify()
            if glyphstoverify:
                log.info("Going to verify these glyphs now: {glyphs}".format(glyphs=glyphstoverify))
                if self.program.alphabet.glyph() not in glyphstoverify:
                    self.program.alphabet.glyph(list(glyphstoverify)[0])
                log.info("Running Verifyglyphs")
                if warnorcontinue(self.verify(macrosort=True)):
                    self.did['verifyglyphs']=True
                log.info("Finished Verifyglyphs with {did}".format(did=self.did))
                return
            log.info("Maybe Joinglyphs")
            self.did['joinglyphs']=False #runs multiple times, so clear here
            # predistinguish hides "trivially distinct" single-member glyph pairs
            # from the join page (alphabet.predistinguish). Skip it for ONE pass
            # right after the user INTENTIONALLY un-distinguished a glyph to join it
            # (name_new_glyphs "go back and join" / redo_joinglyphs) — otherwise it
            # immediately re-distinguishes the very pair they asked to join, off the
            # sort-group-level state the glyph-level un-distinguish didn't clear.
            if getattr(self,'_skip_predistinguish_once',False):
                self._skip_predistinguish_once=False #one pass only
                log.info("Skipping predistinguish: user just chose go-back-and-join")
            else:
                self.program.alphabet.predistinguish(self.to_distinguish(macrosort=True))
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
                # name_new_glyphs returned without naming them all — the user
                # exited / went back from the naming page. Return to the task
                # instead of falling through to the form-update + navigation
                # below, which assumes every glyph is named ("all int() groups
                # ... are gone") and would advance the sort to the next activity.
                return
            """all int() groups and macrogroups are gone at this point!"""
            # Aligns all annotations and verifications, then updates forms
            w=self._get_safe_window()
            def after_annotations():
                if any(i.mature for i in self.program.data_repo.values()):
                    w.wait_and_drive_work(
                    _("Updating forms..."),
                    self.updateformsallchecks())
                else:
                    w.drive_work(self.updateformsallchecks())
            w.wait_and_drive_work(
                _("Updating annotations..."),
                self.update_annotations_to_glyphs(),
                on_done=after_annotations)
        """The following is to iterate to the next work to do. So we want
        everything for a check to be complete to be done by now.
        A user may want to change the name of a group; if so, they should stop
        the sort process, and go name the macrogroup.
        """
        # At this point, there should be nothing to sort, verify or join, so we
        # move on to the next group.
        ctosort=self.program.status.checks(tosort=True)
        ctoverify=self.program.status.checks(toverify=True)
        ptosort=self.program.status.profiles(tosort=True)
        ptoverify=self.program.status.profiles(toverify=True)
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
        done=_("All '{profile}' groups in the '{check}' "
                "{typename} are verified and distinct!").format(profile=self.profile,
                check=self.check, typename=self.checktypename)
                #only on first two ifs:
        if fn:
            done+='\n'+_("Moving on to the next {next_thing}!").format(next_thing=next)
        ErrorNotice(text=done,title=_("Done!"),wait=True,parent=self)
        self.status.maybeboard()
        if fn:
            fn() #only on first two ifs, calls runcheck w/resetsortbutton
    def update_to_cvt(self):
        log.info(_("Group is on a different CVT; updating to that to sort."))
        self._safe_quit_runwindow()
        self.program.taskchooser.maketask(f"Sort{self.program.params.cvt()}",
                                        sort_immediately=self.group)
    def sort_on_group_by_item(self,item):
        kwargs=self.program.alphabet.parse_verificationcode(item)
        log.info(_("Found a group that needs sorting ({item}); switch to sort on it."
                ).format(item=item))
        self.program.params.check(kwargs.get('check'))
        self.program.slices.ps(kwargs.get('ps'))
        self.program.slices.profile(kwargs.get('profile'))
        self.program.params.ftype(kwargs.get('ftype'))
        cvt=self.program.params.cvt(kwargs.get('cvt'))
        if cvt != self.cvt:
            self.update_to_cvt() #this calls runcheck later
        else:
            self.runcheck()
    def item_needs_sorting(self,item):
        #Check if the item needs to sort into a glyph
        if self.program.alphabet.item_is_tomacrosort(item): #refresh and check by cvt!
            log.info(f"{item} needs to macrosort")
            return True
        #Check if the glyph of the item is fully distinct
        glyph=self.program.alphabet.glyph_of_item(item)
        if glyph in [i for j in self.to_distinguish(macrosort=True) for i in j]:
            log.info(f"{item} needs to distinguish")
            return True
        #check if the item is in a ps-profile group with unsorted senses
        kwargs=self.program.alphabet.parse_verificationcode(item)
        self.updatesortingstatus(**kwargs) #this might not be the most efficient
        if self.itemstosort():
            log.info(f"{kwargs['group']} needs to sort (with {kwargs=})")
            return True
        #check if the sort group is fully distinct in its ps-profile group 
        group=kwargs['group']
        if group in [i for j in self.to_distinguish(**kwargs) for i in j]:
            log.info(f"{kwargs['group']} needs to distinguish (with {kwargs=})")
            return True
    def manual_form_update(self):
        default_glyphs=[k for k in self.program.alphabet.glyph_members() if k.isdigit()]
        cvts=[self.program.alphabet.cvt_of_glyph(i) for i in default_glyphs]
        #These shouldn't die on empty groups:
        if max([len(i) for i in cvts]+[1]) > 1:
            ErrorNotice(_("You have at least one unnamed glyph with ambiguous status as "
                        "Consonant or Vowel: {cvts}").format(cvts=cvts),
                        wait=True)
            return
        if min([len(i) for i in cvts]+[1]) < 1:
            ErrorNotice(_("You have at least one unnamed glyph with NO status as "
                        "Consonant or Vowel: {cvts}").format(cvts=cvts),
                        wait=True)
            return
        #Iterate across what's there, and sort on first problem. Come back and 
        # get the others later
        for glyph in default_glyphs:
            for item in self.program.alphabet.glyph_members()[glyph]:
                if self.item_needs_sorting(item):
                    ErrorNotice(_("Item {i} needs sorting (check log for details), so "
                                "not updating forms yet. "
                                "\nFinish sorting, then ask again.").format(i=item),
                        wait=True)
                    self.sort_on_group_by_item(item) #this ends on runcheck
                    return
        for i in default_glyphs:
            cvt=list(self.program.alphabet.cvt_of_glyph(i))[0] #should be exactly one already
        # cvt={next(iter(i)) for i in cvts}
        # if default_glyphs:
            ErrorNotice(_("You have {cvts} glyphs that need names still "
                        "({default_glyphs})!"
                        "\nGoing to start with {i} ({cvt})"
                            ).format(cvts=cvts,cvt=cvt,
                                    default_glyphs=default_glyphs,
                                    i=i),
                            wait=True)
            if self.cvt != cvt:
                self.program.params.cvt(cvt)
            self.name_new_glyphs() #keep cvt the same
            return
        w=self._get_safe_window()
        def after_annotations():
            error=self.update_annotations_errors
            if error:
                txt=_("Problem updating annotations to glyphs:")
                txt+=f'\n{'\n'.join(error)}\n\n'
                txt+=_("try again?")
                ErrorNotice(txt,wait=True)
                return
            log.info(_("Glyph annotations updated OK"))
            log.info("Going to update forms now")
            if any(i.mature for i in self.program.data_repo.values()):
                w.wait_and_drive_work(
                    _("Updating forms..."),
                    self.updateformsallchecks())
            else:
                w.drive_work(self.updateformsallchecks())
        w.wait_and_drive_work(
            _("Updating annotations..."),
            self.update_annotations_to_glyphs(),
            on_done=after_annotations)
        log.info("Done updating forms")
    def present_sense(self,sense):
        log.info("presenting to sort {sense_id}".format(sense_id=sense.id))
        frame=self.get_frame()
        text=sense.formatted(self.analang, self.glosslangs, self.ftype, frame)
        return self.sort_ui.build_present_sense(
            self.ui.runwindow.frame, self.buttonframe, text, sense)
    def unverify_profile(self,sense):
        """'Not {profile}' — DEFER, don't disrupt. Clear the word's CONFIRMED
        profile DATA (plain …-x-cvprofile) and its profile sort-group annotation
        so it leaves this profile and gets re-profiled later. Then:
          - drop it from the CURRENT in-memory slice so maybesort won't re-present
            it, WITHOUT the O(lexicon) load_ps_profiles() rebuild (that single
            rebuild is deferred to the missing-profiles offer / SortSyllables);
          - re-arm the offer (clear _offered_profile_setup) so the gate fires once
            for this freshly unsorted word.
        Crucially this launches NOTHING: the current sort-verify-join continues;
        the syllable task only opens later, if the user picks 'sort' at the offer."""
        ftype=self.program.params.ftype()
        sense.cvprofilevalue(ftype, False)                       # clear confirmed data
        sense.annotationvaluebyftypelang(ftype, self.analang, ftype, '') # clear group
        # Drop the word from the two in-memory places it lives, so it is not
        # re-presented — WITHOUT the O(lexicon) load_ps_profiles rebuild (deferred):
        #   1) the profile slice that updatesortingstatus REBUILDS the to-sort list
        #      from (slices._profilesbysense[ps][profile], read via slices.senses).
        #      Miss this and the next page's rebuild simply re-adds the word — NOT
        #      db.sensesbyps_profile, which the sort loop never reads.
        #   2) the LIVE to-sort list the current sort() loop reads each iteration
        #      (status._sensestosort via itemstosort).
        try:
            ps=self.program.slices.ps(); profile=self.program.slices.profile()
            # Drop from BOTH profile structures so they stay consistent: the sort
            # loop reads slices._profilesbysense, while verified_groups_by_ps_profile
            # (the 'done' derivation) reads db.sensesbyps_profile. Leaving the word in
            # the latter keeps it counted as a member — and, being uncoded, it can
            # unverify groups it no longer belongs to.
            for container in (getattr(self.program.slices,'_profilesbysense',{}),
                              getattr(self.program.db,'sensesbyps_profile',{})):
                slice_senses=container.get(ps,{}).get(profile)
                if slice_senses and sense in slice_senses:
                    slice_senses.remove(sense)
        except Exception as e:
            log.info("unverify_profile slice-drop skipped: %s", e)
        try:
            tosort=self.program.status.sensestosort()
            if tosort and sense in tosort:
                tosort.remove(sense)
        except Exception as e:
            log.info("unverify_profile tosort-drop skipped: %s", e)
        self._offered_profile_setup=False  # re-arm the offer for this new word
        self._notprofile_advance=True      # tell sortselected to advance, not Exit
        self.program.status_dirty=True     # current slice rebuilds (minus this word)
        self.maybewrite()
    def rebuild_syllable_profile_done(self):
        """Recompute the syllable PROFILE node's 'groups' + 'done' with the SAME
        membership+verification model segmental sorting uses (see ADR 0003 and
        io_put/lift.verified_groups_by_ps_profile):
          - a profile GROUP is the set of words carrying that lc ANNOTATION (the
            sort membership) — NOT a cvprofilevalue bucket;
          - the group is 'done' (gets '+') iff every member is VERIFIED, i.e. its
            …-x-cvprofile form matches its lc annotation (the syllable verify
            mark, the counterpart of the segmental '<check>=<group>' code).
        A word with NO lc annotation is UNSORTED: it is not a group here (the
        board flags its class with a white border and maybesort presents it to
        sort — the 'tosort' path), so it must NOT become a phantom '—' group.
        Keying groups (membership) and done (verification) on the ONE annotation
        key is what keeps maybesort's groups-done from silently dropping
        sorted-but-unverified words. Keyed on the 'S'/profile-class/ftype node the
        board + maybesort read."""
        ftype=self.program.params.ftype()
        analang=self.program.db.analang
        by={}  # {ps: {profile_class: {annotation group: every-member-verified bool}}}
        for s in self.program.db.senses:
            ps=s.psvalue()
            pc=self.program.params.profile_class_of_sense(s, ftype=ftype)
            if not (ps and pc):
                continue
            ann=s.annotationvaluebyftypelang(ftype, analang, ftype)
            if not ann or ann in ('NA','Invalid'):
                continue  # unsorted → no group membership (sort phase handles it)
            # Verified iff the confirmed …-x-cvprofile matches the sort annotation;
            # a group is done only if EVERY member is verified that way.
            verified=(s.cvprofilevalue(ftype)==ann)
            grps=by.setdefault(ps,{}).setdefault(pc,{})
            grps[ann]=grps.get(ann,True) and verified
        for ps,pcs in by.items():
            for pc,grps in pcs.items():
                node=self.program.status.node(cvt='S',ps=ps,profile=pc,check=ftype)
                done=sorted(g for g,ok in grps.items() if ok)
                node['groups']=sorted(grps)
                node['done']=done
                # Trust the DISTINCTIONS too (status.json only, not LIFT): verified
                # profiles are distinct cvprofile strings that never meaningfully
                # merge, so mark every verified pair distinguished. Otherwise
                # maybesort's join step — which distinguishes pairs of VERIFIED
                # groups (group_pairs_to_distinguish) — re-fires and 'Sort!' jumps
                # to a spurious join instead of moving on to the unprofiled words.
                node['distinguished']=set(itertools.combinations(done,2))
        self.program.status.store()
    def present_group(self,item):
        log.info("presenting group {item}".format(item=item))
        kwargs=self.program.alphabet.parse_verificationcode(item)
        result = self.sort_ui.build_present_group(
            self.ui.runwindow.frame, self.buttonframe, self, item, kwargs)
        if result:
            return result
        else:
            log.info("No example for {item}; not sorting.".format(item=item))
            self.program.alphabet.mark_item_macrosorted(item) #don't keep sorting
    def current_tosort(self,macrosort=False):
        """These are all ordered lists (either by order of listbuilding, or by
        sorted(). Items not on the original list get tacked onto the end, still
        in order. This allows the user to see a consistently rising progress
        number, even if the to do number rises as well.)"""
        if macrosort:
            tosort=self.program.alphabet.itemstosort()
        else:
            tosort=self.program.status.sensestosort()
        return self.first_sort+[i for i in tosort if i not in self.first_sort]
    def presenttosort(self,item,macrosort=False):
        # log.info("presenting to sort {item}".format(item=item))
        #Keep the same total throughout a given sort:
        tosort=self.current_tosort(macrosort=macrosort)
        progress=(str(tosort.index(item)+1)+'/'+str(len(tosort)))
        """After the first entry, sort by groups."""
        if self.ui.runwindow.exitFlag.istrue():
            return #1,1
        self.sort_ui.label(self.groupsFrame, text=progress, font='report', anchor='e',
                    column=1, row=0, sticky='e')
        if macrosort:
            self.sortitem=self.present_group(item)
        else:
            self.sortitem=self.present_sense(item)
        self.ui.runwindow.waitdone()
        log.info("Going to wait for {item}".format(item=self.sortitem))
        if not self.sortitem:
            log.info("{item} empty; returning".format(item=self.sortitem))
            return
        try:
            self.buttonframe.set_canary(self.sortitem)
            self.ui.runwindow.deiconify() # not until here
        except Exception as e:
            log.error("topresent Exception: {e}".format(e=e))
        # Drained update(), NOT update_idletasks(): on XWayland a bare
        # update_idletasks leaves the just-mapped window's paint/<Configure> backlog
        # un-flushed, so later group buttons (the 2nd group) + skip/OK don't render
        # and the scroll region can stay stale and clip them — the same partial
        # paint the verify page hit, fixed there with update() (build_verify_layout).
        try:
            self.ui.runwindow.update()
        except Exception as e:
            log.info("presenttosort commit update() failed: %s", e)
        # Synchronous scroll reflow now that update() settled the FULL geometry. The
        # deferred re-arm in SortButtonFrame can fire mid-build with a partial height
        # (during a slow example-image load) and get consumed before the later rows
        # (2nd group, Other/Not-profile/Skip) are counted, leaving them clipped and
        # unscrollable. Recompute here, when reqheight is final.
        if hasattr(self,'buttonframe') and hasattr(self.buttonframe,'reflow'):
            self.buttonframe.reflow()
        self.ui.runwindow.wait_window(window=self.sortitem)
        if not self.ui.runwindow.exitFlag.istrue():
            return item
    def pageicon(self,macrosort=False):
        if not macrosort:
            r = self.check
            if 1 < self.profile.count(self.cvt) == r.count(self.cvt):
                r = self.cvt+'=' #use this any time all S is in check.
            if r in self.ui.frame.theme.photo: # Remove once all supported
                return r
        return self.cvt #fail safe for the time being
    def sortselected(self, item, macrosort=False):
        # 'Not {profile}' (unverify_profile) deferred this word and destroyed the
        # item WITHOUT selecting a group. Don't read that empty selection as Exit
        # (which would bail the whole check with a "not done" warning) — just
        # advance: the word is already dropped from the slice, so the sort() loop
        # presents the next one.
        if getattr(self,'_notprofile_advance',False):
            self._notprofile_advance=False
            self.buttonframe.reset_selected()
            return
        # Syllable 'Other {profile class} profile' picker resolved to a real,
        # primitive-consistent profile P (ADR 0003 / cv_group_creation_merging).
        # Mark the current word into P via the normal NEW-group path — NOT
        # add_int_group (which mints a meaningless integer). The picker advanced by
        # destroying the sort item, so this runs with no button selection.
        pending=getattr(self.buttonframe,'_pending_new_profile',None)
        if pending is not None and not macrosort:
            self.buttonframe._pending_new_profile=None
            self.buttonframe.reset_selected()
            self.marksortgroup(item, pending, nocheck=True)
            if pending not in list(self.buttonframe.groupvars)+['NA']:
                self.buttonframe.addgroupbutton(pending)
            self.maybewrite()
            return
        selected=self.buttonframe.get_selected()
        log.info("selected groups: {groups}".format(groups=selected))
        if len(selected)>1:
            log.error(_("More than one group selected: {groups}").format(groups=selected))
            return 2
        self.buttonframe.reset_selected()
        if not selected:
            log.debug('No group selected: {selected}'.format(selected=selected))
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
            recurring_conflicts=self.program.alphabet.mark_item_glyph(item, category)
            if recurring_conflicts:
                log.info("Recurring conflicts marking {item} into {category}: "
                        "{recurring_conflicts}"
                        "".format(item=item, category=category,
                                    recurring_conflicts=recurring_conflicts))
                kwargs=self.program.alphabet.parse_verificationcode(item)
                item_group=kwargs.pop('group')
            for i in recurring_conflicts:
                i_group=self.program.alphabet.parse_verificationcode(i)['group']
                self.program.status.undistinguish((i_group,item_group),**kwargs)
                self.program.status.undistinguish((item_group,i_group),**kwargs)
            if recurring_conflicts:
                # sort_on_group_by_item redirects via a nested runcheck/maybesort
                # that rebuilds the whole display — so this IS a restart. Return
                # truthy so the outer sort() loop bails (its `if r: return`) instead
                # of calling updatecounts() on the now-stale buttonframe the nested
                # rebuild left behind.
                self.sort_on_group_by_item(item)
                # self.maybesort(firstrun=True)
                return 1
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
        log.info('Running sort: (macrosort={macrosort})'.format(macrosort=macrosort))
        """Titles"""
        if self.cvt == 'T':
            context=_("tone melody")
            descripttext=_("in '{check}' frame").format(check=self.check)
        else:
            context=self.program.params.cvcheckname(self.check)
            descripttext=_("by {check}").format(check=self.check)
        instructions=_("...belongs in which group?")
        if macrosort:
            current_list_fn=self.program.alphabet.itemstosort
            self.first_sort=list(current_list_fn()) #current list
            groups=self.program.alphabet.glyphs()
            img_mod='glyphs'
        else:
            current_list_fn=self.itemstosort
            self.first_sort=list(current_list_fn()) #current list
            groups=[i for i in self.groups(wsorted=True) if i != 'NA']
            img_mod=''
            instructions+=' '+_("(by {context})").format(context=context)
        log.info("Going to sort these items: {items}".format(items=self.first_sort))
        log.info("Into these groups: {groups}".format(groups=groups))
        if not self.first_sort or self.ui.exitFlag.istrue():
            return 1
        log.info(f"Getting Runwindow")
        self.ui.getrunwindow() #after we know this will do something
        self.groupsFrame, self.buttonframe = self.sort_ui.build_sort_layout(
            self.ui.runwindow, img_mod, self.pageicon(macrosort=macrosort),
            instructions, self, groups, macrosort)
        # log.info("Sort SBF done macrosort={macrosort}".format(macrosort=macrosort))
        """Stuff that changes by lexical entry
        The second frame, for the other two buttons, which also scroll"""
        while current_list_fn():
            if self.ui.runwindow.exitFlag.istrue():
                return
            item=self.presenttosort(current_list_fn()[0], macrosort=macrosort)
            # log.info("presenttosort done")
            if not self.ui.runwindow.exitFlag.istrue() and item is not None:
                r=self.sortselected(item, macrosort=macrosort)
                if r: #on restarting to maybesort
                    return
                self.buttonframe.updatecounts()
        if macrosort: #generalize
            self.program.alphabet.save_settings()
            self.program.settings.storesettingsfile('alphabet')
        self.ui.runwindow.on_quit()
        return 1
    def re_presort(self):
        self.program.status.presorted(False)
        self.runcheck()
    def reverify_glyph(self):
        done=self.program.alphabet.glyphdict()[self.cvt]
        if not self.program.alphabet.glyph() in self.program.alphabet.glyphdict()[self.cvt]:
            w=self.getglyph(toverify=True) #assumes system cvt
            w.wait_window(w)
            glyph=self.program.alphabet.glyph()
            if glyph not in done: #i.e., still
                log.info(_("I asked for a glyph, but didn't get one ")+''
                        f"({glyph} not in {done}).")
                return
        self.program.alphabet.mark_glyph_not_done(glyph)
        # done.remove(group)
        # self.program.status.verified(done)
        self.reverifying=True
        self.runcheck()
    def reverify(self):
        group=self.program.status.group()
        check=self.program.params.check()
        log.info("Reverifying a framed tone group, at user request: {check}-{group}"
                    "".format(check=check,group=group))
        if check not in self.program.status.checks(wsorted=True):
            self.getcheck() #guess=True
        done=self.program.status.verified()
        if group not in done:
            log.info("Group ({group}) not in groups ({done}); asking."
                    "".format(group=group,done=done))
            w=self.getgroup(wsorted=True)
            w.wait_window(w)
            group=self.program.status.group()
            if group not in done: #i.e., still
                log.info("I asked for a framed tone group, but didn't get one.")
                return
        done.remove(group)
        self.program.status.verified(done)
        self.reverifying=True
        self.runcheck()
    def verifyselected(self, macrosort=False):
        selected=self.buttonframe.get_selected()
        log.info("verifyselected removing {selected}".format(selected=selected))
        if macrosort:
            for item in selected:
                self.program.alphabet.remove_item_from_glyph(item, self.group)
        else:
            raise "This doesn't belong here yet!"# wrong: this should unsort!
            self.marksortgroup(item, category, nocheck=True) # that marking
        self.maybewrite()
    def verify(self,menu=False,macrosort=False):
        def updatestatus(verified=False):
            if macrosort:
                log.info("Updating '{group}' status as verified={verified}".format(group=group, verified=verified))
                if verified:
                    self.program.alphabet.mark_glyph_done(group,cvt=self.cvt)
                else:
                    self.program.alphabet.mark_glyph_not_done(group)
                log.info("self.program.alphabet.glyphstoverify()={glyphs}".format(glyphs=self.program.alphabet.glyphstoverify()))
                self.program.alphabet.save_settings()
            else:
                log.info("Updating status with {check}, {group}, {verified}".format(check=check,group=group,verified=verified))
                self.program.status.last('verify',update=True)
                self.updatestatus(verified=verified,writestatus=True)
            self.maybewrite()
        log.info(f"Running verify! {macrosort=} {getattr(self,'reverifying',False)=} "
                f"{type(getattr(self,'reverifying',False))=}")
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
        title=[_("Verify {language}").format(language=self.program.settings.languagenames[self.analang])]
        if macrosort:
            item_name=_("Letter")
            img_mod='glyphs'
            groups=list(self.program.alphabet.glyphstoverify()) #needed for progress
            self.group=group=self.program.alphabet.glyph()
            self.currentsortitems=items=self.program.alphabet.glyph_members()[group]
            if group.isdigit():
                title.append(_("letter group"))
            else:
                title.append(_("letter '{group}'").format(group=group))
            checks={self.program.alphabet.parse_verificationcode(i)['check']
                    for i in items}
            oktext=_("These all should use the same letter")
            if not group.isdigit():
                oktext+=_(" (currently '{group}')").format(group=group)
            instructions=_("Read this list aloud. Note where each "
                "was sorted ({checks})."
                "\nClick on any with a different "
                "{cvtname} sound in that place.").format(
                    checks=', '.join(sorted(checks)),
                    cvtname=self.program.params.cvtname())
        else:
            check=self.program.params.check()
            checks=[]
            img_mod=''
            checkname=self.program.params.cvcheckname()
            # Users don't know the raw check codes (lc/lx/pl/imp); for syllable
            # sorting (cvt 'S') show only the prose name, and these labels don't
            # take the "sound" grammar that the C/V/T segment labels do.
            is_syl=(self.program.params.cvt()=='S')
            if is_syl:
                item_name=self.program.params.cvtname() #e.g. "Syllable Profile"
            else:
                item_name=_("{check} Group").format(check=check)
            groups=self.groups(toverify=True) #needed for progress
            self.group=group=self.program.status.group()
            _t0=time.perf_counter()
            self.currentsortitems=items=self.program.examples.sensesinslicegroup(group,check)
            log.info("verify: sensesinslicegroup(%s,%s) → %d items in %.2fs",
                     check, group, len(items or []), time.perf_counter()-_t0)
            # Present the list in a sensible order, not a random pile of words.
            # Alphabetical by the word form; for word-final tests, alphabetical
            # from the END of the word (reverse the key) so like endings group.
            if items:
                def _formkey(s):
                    try:
                        return (s.formattedform(self.analang,self.ftype)
                                or '').casefold()
                    except Exception:
                        return ''
                if self.program.params.is_word_final_check(check):
                    items.sort(key=lambda s: _formkey(s)[::-1])
                else:
                    items.sort(key=_formkey)
            if group == 'NA':
                oktext=_('These all DO NOT have {checkname}').format(checkname=checkname)
                #These words seem to NOT have '{checkname}'.
                instructions=_("Read this list aloud, and click on any that "
                            "DOES have '{checkname}'.").format(checkname=checkname)
                title.append(_("for '{check}' (NOT {checkname})").format(check=check.replace('=','≠'),
                                                            checkname=checkname))
            elif is_syl:
                # Name the specific group being verified, e.g. "consonant
                # initial" / "vowel final" / "2 syllables" — not the raw check.
                desc=self.program.params.syllable_group_name(check,group)
                oktext=_("These are all {desc}").format(desc=desc)
                instructions=_("Read this list aloud. Click on any that are "
                            "NOT {desc}.").format(desc=desc)
                title.append(_("{desc}").format(desc=desc))
            else:
                oktext=_('These all have the same {checkname} ({check})'
                            ).format(checkname=checkname,check=check)
                instructions=_("Read this list aloud. Click on any with a "
                            "different {checkname} sound.").format(checkname=checkname)
                title.append(_("for '{check}' ({checkname})").format(check=check, checkname=checkname))
            if group in self.program.status.verified():
                log.info(_("'{group}' already verified, continuing.").format(group=group))
                return 1
            if self.program.params.cvt() == 'T' and not hasattr(self.program, 'examples'):
                log.error(_("Not verifying tone examples which don't exist."))
                return 
        # The title for this page changes by group, below.
        self.program.status.build()
        last=False
        if not items: #then remove the group
            groups=self.groups(wsorted=True) #from which to remove, put back
            # log.info("Groups: {}".format(self.groups(toverify=True)))
            verified=False
            log.info("Group '{group}' has no examples; continuing.".format(group=group))
            # log.info("Groups: {}".format(self.groups(toverify=True)))
            updatestatus(False)
            log.info("Group-groups: {group}-{groups}".format(group=group,groups=groups))
            if group in groups:
                groups.remove(group)
            # log.info("Group-groups: {group}-{groups}".format(group=group,groups=groups))
            log.info(f"verify status.groups: {self.program.status.groups(wsorted=True)}")
            self.program.status.groups(groups,wsorted=True)
            log.info(f"verify status.groups: {self.program.status.groups(wsorted=True)}")
            log.info("All groups: {groups}".format(groups=self.groups(wsorted=True)))
            log.info("Groups to verify: {groups}"
                        "".format(groups=self.groups(toverify=True)))
            return
        elif len(items) == 1 and not getattr(self,'reverifying',False):
            log.info(_("Group '{group}' only has {count} example; marking verified and "
                    "continuing.").format(group=group,count=len(items)))
            updatestatus(True)
            return 1
        self.reverifying=False
        # Prep message for the wait dialog shown while the (possibly large)
        # verify list builds. It tells the user what they're about to verify
        # and gives the first-page build a visible, acknowledged wait; the
        # window is revealed (waitdone) as soon as the first page is built, then
        # the rest streams in behind it. See build_verify_layout.
        if macrosort:
            prep=_("Preparing the {item_name} '{group}' to verify…").format(
                                            item_name=item_name, group=group)
        elif is_syl:
            prep=_("On the next page, you will verify all the words that are "
                   "{desc}.").format(desc=desc)
        elif group=='NA':
            prep=_("On the next page, you will verify the words that do NOT "
                   "have {checkname}.").format(checkname=checkname)
        else:
            prep=_("On the next page, you will verify the {checkname} "
                   "words.").format(checkname=checkname)
        # build_verify_layout owns the wait dialog now (it drives the first-page
        # build through wait_and_drive_work, which shows the progress bar, then
        # reveals the window); so create the run window WITHOUT a wait here.
        self.ui.getrunwindow()
        """Move this to bool vars, like for sort"""
        if hasattr(self,'groupselected'): #so it doesn't get in way later.
            delattr(self,'groupselected')
        if group in groups:
            if len(groups)-1:
                prog_text=_("({count} remaining)").format(count=len(groups))
            else:
                prog_text=_("(last group)")
        else:
            prog_text=None
        self.buttonframe, self.verifycanary = self.sort_ui.build_verify_layout(
            self.ui.runwindow, title, self.pageicon(macrosort), instructions,
            prog_text, img_mod, group, items, self, macrosort, oktext,
            self.min_to_multicolumn, self.buttoncolumns, self.verifybutton,
            join_fn=self.join, prep=prep)
        if self.verifycanary is None:
            return
        if self.ui.runwindow.exitFlag.istrue():
            return
        # Single page: the verify list is slice-bounded (≤MAX_SLICE for syllable
        # prep, one CV-profile in one ps for segmental), so it always fits one
        # page and there is no page transition to wedge XWayland. Wait on the
        # off-screen completion canary; the OK button at the end of the list
        # destroys it. exitFlag = the user quit instead of confirming.
        self.ui.runwindow.wait_window(self.verifycanary)
        if self.ui.runwindow.exitFlag.istrue(): #user exited, not hit OK
            return
        log.debug("User selected '{selection}', moving on.".format(selection=oktext))
        if macrosort:
            self.verifyselected(macrosort=True)
            if len(self.buttonframe.groupbuttonlist) > 1:
                updatestatus(True)
            else:
                updatestatus(False) #on *finishing* with one/none
        else:
                updatestatus(True)
        self.ui.runwindow.on_quit()
        return 1
    def verifybutton(self,parent,sense,row,column=0,label=False,**kwargs):
        """This should maybe take examples as input, rather than senses"""
        # This must run one subcheck at a time. If the subcheck changes,
        # it will fail.
        # should move to specify location and fieldvalue in button lambda
        def notok():
            # Syllable PREP (Task 1): a flagged word doesn't belong in this group;
            # MOVE it to its correct group (the misfit rule) instead of just
            # un-sorting it. Booleans flip to the other value; count asks ±1.
            pv=getattr(self,'_prep_verify',None)
            if pv:
                sl,check,group,idx=pv
                if check=='syls':
                    # Outline the clicked word so the chooser visibly refers to
                    # it. Recolouring the button background did nothing: in
                    # several themes activebackground == background (a no-op), and
                    # the illustration covers the face anyway. Use the button's
                    # focus-highlight BORDER instead — the same mechanism the prep
                    # board uses for unverified cells, which DOES render — in the
                    # theme accent ('highlight') colour. Restore on Cancel;
                    # Shorter/Longer destroy the button, so only Cancel restores.
                    orig_ht=b['highlightthickness']
                    orig_hb=b['highlightbackground']
                    b.configure(highlightthickness=3, highlightbackground=
                                getattr(b.theme,'highlight',None) or b.theme.white)
                    b.update_idletasks() # paint before the modal chooser opens
                    new=self.sort_ui.ask_syllable_count(self.ui.runwindow,
                                                        int(group))
                    if new is None:
                        if b.winfo_exists():
                            b.configure(highlightthickness=orig_ht,
                                        highlightbackground=orig_hb) #restore
                        return #leave the word where it is
                    sl.move_misfit(sense,check,target=str(new))
                else:
                    sl.move_misfit(sense,check)
                if sense in self.currentsortitems:
                    self.currentsortitems.remove(sense)
                if len(self.currentsortitems) < 2:
                    self.verifycanary.destroy()
                self.maybewrite()
                bf.destroy()
                return
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
        check=self.program.params.check()
        frame=self.get_frame()
        text=sense.formatted(self.analang, self.glosslangs, self.ftype, frame)
        if self.program.settings.lowverticalspace:
            ipady=0
        else:
            ipady=15*self.theme.scale
        b, bf = self.sort_ui.build_verify_button(
            parent, text, sense, label, notok, row, column, ipady, **kwargs)
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
            groups=self.program.alphabet.glyphs()
        else:
            groups=[i for i in self.program.status.verified() if i != 'NA']
        return set(itertools.combinations(groups, 2))
    def to_distinguish(self, macrosort=False, **kwargs):
        if macrosort:
            d=self.program.alphabet.distinguished_by_cvt()
            #whatever ordering was stored, remove either if there
            return self.group_pairs_to_distinguish(macrosort=True)-d-{(y,x) for x,y in d}
        # non-macrosort: shared with macrosort eligibility (analysis.py). Keys off
        # THIS slice's verified groups (kwargs), fixing the old current-slice bug.
        return self.program.status.pending_distinctions(**kwargs)
    def join(self,macrosort=False,sortgroup=None):
        def move_on_cleanly():
            # self.ui.runwindow.withdraw()
            # self.last_pair=pair_frame.winfo_children()
            # self.last_pair=self.current_pair
            for w in self.current_pair:
                buttons[w].grid_remove() #don't destroy buttons with canary
            # for w in pair_frame.winfo_children():
            #     w.grid_remove() #don't destroy buttons with canary
            self.canary.destroy()
        def _do_join(lpr):
            # lpr=[remove, keep]: move the first group into the second.
            log.info("Joining {lpr} (macrosort={macrosort}).".format(lpr=lpr, macrosort=macrosort))
            msg=_("Now we're going to move group '{group1}' into "
                "'{group2}', removing '{group1}' and marking '{group2}' unverified.").format(group1=lpr[0], group2=lpr[1])
            self.ui.runwindow.wait(msg=msg)
            """All the senses we're looking at, by ps/profile"""
            if not macrosort:
                # async path: drive_work owns the wait dialog and closes it
                # via waitdone() on StopIteration — do NOT waitdone() here.
                def join_pair_done():
                    self.program.settings.reloadstatusdata_cleanup()
                    _cn=self.program.status.node()
                    log.info("DIAG-join-verify post-cull node check=%s done=%s "
                             "groups=%s",self.program.params.check(),
                             _cn.get('done'),_cn.get('groups'))
                    self.updatestatus(group=lpr[1],
                                    verified=False,
                                    writestatus=True)
                    self.did[f'join{img_mod}']=True
                    self.ui.runwindow.on_quit()
                self.ui.runwindow.drive_work(
                    self.updatebygroupsense(*lpr),
                    on_done=join_pair_done)
                return
            # synchronous path: guarantee the dialog closes even if join_glyphs raises
            try:
                log.info(f"Running join_pair! {macrosort=}")
                self.program.alphabet.join_glyphs(*lpr)
                log.info(f"join_pair done {macrosort=}")
                self.did[f'join{img_mod}']=True
            finally:
                self.ui.runwindow.waitdone()
            self.ui.runwindow.on_quit()
        def join_pair():
            pair=self.current_pair
            # Syllable PROFILE join: both sides are REAL CV profiles (no isdigit
            # placeholder to break the tie — the picker+scrub keep integers out), so
            # the DIRECTION is a linguistic call: CVCV→CVCCV and CVCCV→CVCV are NOT
            # the same result, and one corrupts correct data. Ask which is correct
            # rather than picking by lexicographic accident. See ADR 0003.
            if self.cvt=='S' and not self.program.params.is_syllable_primitive_check():
                counts={g:len(self.getsensesincheckgroup(check=check,group=g))
                        for g in pair}
                def _on_choose(winner):
                    loser=next(g for g in pair if g!=winner)
                    _do_join([loser,winner])   # [remove, keep]
                self.sort_ui.choose_join_direction(
                    self.ui.runwindow, buttonclass, self, list(pair), counts,
                    _on_choose)  # on_back=None → just close, back to the join page
                return
            # Segmental/other: sorted(key=str) puts an isdigit() group first, so the
            # unnamed placeholder is removed into the real/named group.
            _do_join(sorted(pair,key=str))
        def distinguish_pair():
            if macrosort:
                self.program.alphabet.distinguish(self.current_pair)
                self.program.alphabet.save_settings()
            else:
                self.program.status.distinguish(self.current_pair)
                self.program.status.store()
            move_on_cleanly()
        def get_pairs():
            return sorted(self.to_distinguish(macrosort=macrosort))
        log.info("Running join! macrosort={macrosort}".format(macrosort=macrosort))
        """This window allows the user to join groups that sound the same. """
        """This should move to a presentation of permutations (choose two), so
        the user gets a series of "are x and y the same (or different?)?"
        questions that can be easily answered, that we can force to be addressed
        thoroughly (rather than let the user decide that he has looked at each).
        """
        #This function should exit 1 on a window close, 0/None on all ok.
        cvt=self.program.params.cvt()
        check=self.program.params.check()
        ps=self.program.slices.ps()
        profile=self.program.slices.profile()
        _bn=self.program.status.node()
        log.info("DIAG-join-verify join-start node check=%s done=%s groups=%s",
                 check,_bn.get('done'),_bn.get('groups'))
        pairs=get_pairs()
        if sortgroup: #sometimes we just limit this to one group
            pairs=[g for g in pairs if sortgroup in g]
        npairs=len(pairs) #leave this alone, for progress
        if not pairs:
            log.debug("No groups to distinguish!")
            return
        self.ui.getrunwindow()
        oktext=_('These are each different from the other(s)')
        if macrosort:
            img_mod='glyphs'
            title_mod="Letter"
            title_mod_2=''
        else:
            img_mod=''
            title_mod="Sort"
            title_mod_2=f" ('{check}')"
        buttonclass = self.sort_ui.group_button_class(macrosort)
        title=_("Review {title} Groups{mod}").format(title=title_mod,mod=title_mod_2)
        self.progress, response_button_frame, pair_frame = \
            self.sort_ui.build_join_layout(
                self.ui.runwindow, title, self.pageicon(), img_mod)
        self.sort_ui.build_join_buttons(
            response_button_frame, img_mod, join_pair, distinguish_pair)
        buttons={}
        # self.last_pair=[]
        while pairs:
            self.progress.current(1 -len(pairs)/npairs)
            self.current_pair=pairs[0]
            log.info("Working on {pair} {count} remaining "
                    "of {total}".format(pair=self.current_pair, count=len(pairs), total=npairs))
            self.canary = self.sort_ui.build_join_pair(
                pair_frame, buttonclass, self, self.current_pair, buttons)
            # Reveal the kiosk run window — getrunwindow() created it withdrawn,
            # and join (unlike sort's presenttosort) never deiconified it, so
            # wait_window blocked on a window the user could never see/dismiss.
            # Mirror presenttosort: waitdone (in case a wait covered the build),
            # then deiconify + render.
            self.ui.runwindow.waitdone()
            self.ui.runwindow.deiconify()
            self.ui.runwindow.update_idletasks()
            pair_frame.wait_window(self.canary)
            if self.did[f'join{img_mod}']:
                return 1
            if self.ui.runwindow.exitFlag.istrue():
                log.info("Runwindow exited.")
                return
            pairs=get_pairs()
        self.ui.runwindow.on_quit()
        return 1
    def tryNAgain(self):
        check=self.program.params.check()
        if check in self.program.status.checks():
            senses=self.getsensesincheckgroup(group='NA')
        else:
            #Give an error window here
            log.error("Not Trying again; set a check first!")
            self.ui.getrunwindow(msg=_("Resetting unSorted items"))
            buttontxt=_("Sort!")
            text=_("Not Trying Again; set a tone frame first!")
            self.sort_ui.label(self.ui.runwindow.frame, text=text).grid(row=0,column=0)
            return
        for item in senses:
            self.removeitemfromgroup(item)
        self.runcheck()
    def __init__(self, **kwargs):
        super().__init__(**kwargs) #is this needed?

