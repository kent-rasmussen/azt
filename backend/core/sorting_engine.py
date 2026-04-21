# coding=UTF-8
import sys
import collections
import re
import datetime
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
class Sort(object):
    """This class takes methods common to all sort checks, and gives sort
    checks a common identity."""
    @property
    def sort_ui(self):
        """Lazy-init presenter; available after task init wires program.sort_ui."""
        return self.program.sort_ui
    show_buttoncolumnsline=True #does this belong here?
    def get_check(self):
        return self.program.params.check()
    def get_ps(self):
        return self.program.slices.ps()
    def get_profile(self):
        return self.program.slices.profile()
    def get_ftype(self):
        return self.program.params.ftype()
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
    def getsensesincheckgroup(self,**kwargs):
        check=kwargs.get('check',self.program.params.check())
        group=kwargs.get('group',self.program.status.group())
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
        check=kwargs.get('check',self.program.params.check())
        group=kwargs.get('group',self.program.status.group())
        profile=kwargs.get('profile',self.program.slices.profile())
        ftype=kwargs.get('ftype',self.program.params.ftype())
        # profile=self.program.slices.profile()
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
        for sense in self.program.slices.inslice(senses): #only for this ps-profile
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
        padx=50
        pady=10
        p.label(self.ui.runwindow.frame,text=title,font='title',
                ).grid(row=0,column=0,sticky='ew')
        allpssenses=self.program.slices.sensesbyps(ps)
        if len(allpssenses)>70:
            self.ui.runwindow.waitdone()
            text=_("This is a large group ({count})! Are you in the right "
                    "lexical category?").format(count=len(allpssensids))
            log.error(text)
            w=p.label(self.ui.runwindow.frame,text=text)
            w.grid(row=1,column=0,sticky='ew')
            b=p.button(self.ui.runwindow.frame, text=_("OK"), command=w.destroy, anchor='c')
            b.grid(row=2,column=0,sticky='ew')
            self.ui.runwindow.wait_window(w)
            w.destroy()
        if self.ui.runwindow.exitFlag.istrue():
            return
        else:
            self.ui.runwindow.wait()
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
        self.ui.runwindow.waitdone()
        self.ui.runwindow.wait_window(scroll)
    def removeitemfromgroup(self,item,**kwargs):
        #leave these in kwargs for use below:
        check=kwargs.get('check',self.program.params.check())
        group=kwargs.get('group',self.program.status.group())
        write=kwargs.pop('write',True) #avoid duplicate
        sorting=kwargs.get('sorting',True) #Default to verify button
        log.info(_("Removing sense {id} from subcheck {group}").format(id=item.id,group=group))
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
        profile=kwargs.get('profile',self.program.slices.profile())
        item.rmverificationvalue(profile,self.ftype,rm)
        self.program.status.last('sort',update=True)
        self.program.examples.clear_cache(**kwargs) #anything should still be in kwargs
        if write:
            self.maybewrite()
        if sorting:
            self.program.status.marksensetosort(item)
    def ncheck(self):
        r=self.program.status.nextcheck(tosort=True)
        if r:
            self.program.settings.setcheck(r)
        else:
            self.program.settings.setcheck(toverify=True)
        #if neither, this should call nprofile
        try:
            self.ui.runwindow.on_quit()
        except AttributeError:
            log.info("Looks like we wanted to kill a non-existent runwindow.")
        self.runcheck()
    def nprofile(self):
        r=self.program.status.nextprofile(tosort=True)
        if r:
            self.program.settings.setprofile(r)
        else:
            self.program.settings.setprofile(toverify=True)
        #if neither, this should give up with a congrats and comment to pick another ps
        try:
            self.ui.runwindow.on_quit()
        except AttributeError:
            log.info("Looks like we wanted to kill a non-existent runwindow.")
        self.runcheck()
    def nps(self):
        self.program.slices.nextps()
        r=self.program.status.nextprofile(tosort=True)
        if not r:
            self.program.status.nextprofile(toverify=True)
        try:
            self.ui.runwindow.on_quit()
        except AttributeError:
            log.info("Looks like we wanted to kill a non-existent runwindow.")
        self.runcheck()
    def runcheck(self):
        self.program.settings.storesettingsfile()
        # t=(_('Run Check'))
        log.info("Running check...")
        cvt=self.program.params.cvt()
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
        try:
            self.ui.runwindow.winfo_viewable()
            w=self.ui.runwindow
        except:
            w=self.program.tk_root
        w.drive_work(gen, on_done=after_presort)
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
            # log.info(f"Confirmed curent verification group '{curvalue}' "
            #         f"matches annotation group '{curvalue}'")
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
        # group=kwargs.get('group',self.program.status.group())
        check=kwargs.get('check',self.program.params.check())
        profile=kwargs.get('profile',self.program.slices.profile())
        # ftype=kwargs.get('ftype',self.program.params.ftype())
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
                log.error("Field addition failed! LIFT says {new}, not {old}.".format(
                                                    new=newgroup,old=group))
            # else:
            #     log.info("Field addition succeeded! LIFT says {}, which is {}."
            #                             "".format(newgroup,group))
        # log.info(f"marksortgroup ready to updateforms {kwargs.get('thread_name')}")
        if kwargs.get('updateforms'):
            if self.ftype != self.program.params.ftype():
                ErrorNotice(_("{ftype} differs from {pftype}; this is a problem!").format(
                            ftype=ftype, pftype=self.program.params.ftype()),
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
        try:
            self.ui.runwindow.winfo_viewable()
            w=self.ui.runwindow
        except:
            w=self.program.tk_root
        if any(i.mature for i in self.program.data_repo.values()):
            log.info("Found mature repo; showing wait")
            w.wait_and_drive_work(
                        _("Reloading status data"),
                        self.program.settings.reloadstatusdata(), # culled here
                        on_done=self.program.settings.reloadstatusdata_cleanup)
        else:
            log.info("Found new repo; not showing wait")
            w.drive_work(self.program.settings.reloadstatusdata(), # culled here
                        on_done=self.program.settings.reloadstatusdata_cleanup)
        if not self.itemstosort():
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
        if self.to_distinguish():
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
        if self.cvt != 'T':
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
            """all int() groups and macrogroups are gone at this point!"""
            # Aligns all annotations and verifications, then updates forms
            try:
                self.ui.runwindow.winfo_viewable()
                w=self.ui.runwindow
            except:
                w=self.program.tk_root
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
        try:
            self.ui.runwindow.on_quit()
        except:
            pass
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
        try:
            self.ui.runwindow.winfo_viewable()
            w=self.ui.runwindow
        except:
            w=self.program.tk_root
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
        self.ui.runwindow.update_idletasks()
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
    def add_int_group(self,macrosort=False):
        log.info("Adding a new group!")
        if macrosort:
            groups=self.program.alphabet.glyphs()
        else:
            groups=self.program.status.groups(wsorted=True)
        values=[int(i) for i in groups if i.isdigit()]+[0] #in case none
        newgroup=max(values)+1
        groups.append(str(newgroup))
        if not macrosort: #for macrosort, marksortgroup does this
            self.program.status.groups(groups,wsorted=True)
            self.program.status.store()
        log.info("Groups (appended): {groups}".format(groups=groups))
        return str(newgroup)
    def sortselected(self, item, macrosort=False):
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
                self.sort_on_group_by_item(item)
                # self.maybesort(firstrun=True)
                return
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
            item_name=_("{check} Group").format(check=check)
            checkname=self.program.params.cvcheckname()
            groups=self.groups(toverify=True) #needed for progress
            self.group=group=self.program.status.group()
            self.currentsortitems=items=self.program.examples.sensesinslicegroup(group,check)
            if group == 'NA':
                oktext=_('These all DO NOT have {checkname}').format(checkname=checkname)
                #These words seem to NOT have '{checkname}'. 
                instructions=_("Read this list aloud, and click on any that "
                            "DOES have '{checkname}'.").format(checkname=checkname)
                title.append(_("for '{check}' (NOT {checkname})").format(check=check.replace('=','≠'), 
                                                            checkname=self.program.params.cvcheckname()))
            else:
                oktext=_('These all have the same {checkname} ({check})'
                            ).format(checkname=checkname,check=check)
                instructions=_("Read this list aloud. Click on any with a "
                            "different {checkname} sound.").format(checkname=checkname)
                title.append(_("for '{check}' ({checkname})").format(check=check, checkname=self.program.params.cvcheckname()))
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
            self.program.status.groups(groups,wsorted=True)
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
        self.ui.getrunwindow(msg=_("preparing to verify the {item_name} '{group}'").format(item_name=item_name, group=group))
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
            self.min_to_multicolumn, self.buttoncolumns, self.verifybutton)
        if self.verifycanary is None:
            return
        if self.ui.runwindow.exitFlag.istrue():
            return
        self.ui.runwindow.waitdone()
        self.ui.runwindow.deiconify() # not until here
        self.ui.runwindow.wait_window(self.verifycanary)
        if self.ui.runwindow.exitFlag.istrue(): #i.e., user exited, not hit OK
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
        else:
            d=self.program.status.distinguished(**kwargs)
        #whatever ordering was stored, remove either if there
        return self.group_pairs_to_distinguish(macrosort=macrosort
                                                )-d-{(y,x) for x,y in d}
    def join(self,macrosort=False):
        def move_on_cleanly():
            # self.ui.runwindow.withdraw()
            # self.last_pair=pair_frame.winfo_children()
            # self.last_pair=self.current_pair
            for w in self.current_pair:
                buttons[w].grid_remove() #don't destroy buttons with canary
            # for w in pair_frame.winfo_children():
            #     w.grid_remove() #don't destroy buttons with canary
            self.canary.destroy()
        def join_pair():
            lpr=sorted(self.current_pair,key=str) #put a number first (to remove)
            log.info("User selected {lpr} to join, joining them (macrosort={macrosort}).".format(lpr=lpr, macrosort=macrosort))
            msg=_("Now we're going to move group '{group1}' into "
                "'{group2}', removing '{group1}' and marking '{group2}' unverified.").format(group1=lpr[0], group2=lpr[1])
            self.ui.runwindow.wait(msg=msg)
            """All the senses we're looking at, by ps/profile"""
            if macrosort:
                log.info(f"Running join_pair! {macrosort=}")
                self.program.alphabet.join_glyphs(*lpr)
                log.info(f"join_pair done {macrosort=}")
            else:
                def join_pair_done():
                    self.program.settings.reloadstatusdata_cleanup()
                    self.updatestatus(group=lpr[1],
                                    verified=False,
                                    writestatus=True)
                    self.did[f'join{img_mod}']=True
                    self.ui.runwindow.on_quit()
                self.ui.runwindow.drive_work(
                    self.updatebygroupsense(*lpr),
                    on_done=join_pair_done)
                return
            self.did[f'join{img_mod}']=True
            self.ui.runwindow.waitdone()
            self.ui.runwindow.on_quit()
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
        pairs=get_pairs()
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
        if pairs:
            self.ui.runwindow.waitdone()
        buttons={}
        # self.last_pair=[]
        while pairs:
            self.progress.current(1 -len(pairs)/npairs)
            self.current_pair=pairs[0]
            log.info("Working on {pair} {count} remaining "
                    "of {total}".format(pair=self.current_pair, count=len(pairs), total=npairs))
            self.canary = self.sort_ui.build_join_pair(
                pair_frame, buttonclass, self, self.current_pair, buttons)
            # self.ui.runwindow.deiconify()
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
    def rename_group(self,x,y,updatestatus=True):
        for _ in self.updatebygroupsense(x,y,
                                updatestatus=updatestatus,
                                updateforms=True):
            pass  # consume generator synchronously
        if updatestatus:
            self.program.settings.reloadstatusdata_cleanup()
        self.rename_group_verification(x,y)
    def rename_group_verification(self,x,y,**kwargs):
        v=self.program.status.verified(**kwargs)
        if x in v:
            log.info("Found verified value to change: {old}>{new}".format(old=x, new=y))
            v.remove(x)
            v.append(y)
            self.program.status.verified(g=v,**kwargs)
    def updatebygroupsense(self,x,y,updateforms=False,updatestatus=True):
        """Generator: moves all senses from group x to group y.
        Yields 0-100 progress. Post-work (reloadstatusdata, distinguish
        updates, maybewrite) is handled after generator exhaustion.
        """
        check=self.program.params.check()
        lst2=self.getsensesingroup(check,x) #by annotations, for C/V
        profile=self.program.slices.profile()
        senses=self.program.slices.inslice(lst2)
        ftype=self.program.params.ftype()
        if not senses:
            log.info("No senses for {check}={value}".format(check=check,value=x))
            return
        kwargs={'not_sorting':True,
                'updateverification':True,
                'updateforms':updateforms
                }
        n=len(senses)
        for i, sense in enumerate(senses):
            self.marksortgroup(sense, y, **kwargs)
            yield i * 50 // n  # 0-50 for marksortgroup phase
        if updatestatus:
            yield from self.program.settings.reloadstatusdata() # 0-100 mapped to ~50 already
        for t in list(self.program.status.distinguished()):
            if x in t:
                self.program.status.undistinguish(t)
                self.program.status.distinguish((y if t[0]==x else t[0],y if t[1]==x else t[1]))
        self.maybewrite()
        log.info("updatebygroupsense finished converting {x} to {y}".format(x=x,y=y))
    def __init__(self, **kwargs):
        super().__init__(**kwargs) #is this needed?

