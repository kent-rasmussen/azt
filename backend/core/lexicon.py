# coding=UTF-8
import sys
import collections
import re
import datetime
# import tkinter as tk
from backend.core.analysis import Analysis
from backend import parser
from utilities.utilities import *
from utilities import file, logsetup, htmlfns
from io_put import lift
# from tasks.tasks import TranscribeC, TranscribeV
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

from utilities.error_handler import notify_error as ErrorNotice

from utilities.i18n import _
from utilities import rx
from io_put.cawl import loadCAWL
import threading


class Senses(object):
    """This was started because some tasks primarily handle senses 
    (with their various forms), whereas others handle examples.
    This refactoring was interrupted, though, so should likely
    be reconsidered. (see Tone class below)"""
    def groups(self,**kwargs): #toverify=True
        return self.program.status.groups(**kwargs)
    def group(self,value=None,**kwargs):#get/set
        return self.program.status.group(value,**kwargs)
    def notdonewarning(self):
        buttontxt=_("Sort!")
        text=_("Hey, you’re not done with {ps} {profile} words by {check}!"
                "\nCome back when you have time; restart where you left "
                "off by pressing ‘{button}’").format(ps=self.ps,profile=self.profile,check=self.check,
                                                button=buttontxt)
        # self.ui.withdraw()
        # Make sure no verify/sort build is still streaming via drive_work — a
        # long tail would starve this modal's event loop, leaving it black and
        # unresponsive (input frozen) until the build drained.
        rw=getattr(self.ui,'runwindow',None)
        # The run window is frequently ALREADY DESTROYED here — "not done" means
        # the user closed it — so every Tk call on it must be guarded, or it
        # raises "bad window path name", which propagates out of the after()
        # callback and out of mainloop, freezing the app.
        def _safe(fn,default='?'):
            try:
                return fn()
            except Exception:
                return default
        rw_exists=bool(rw) and _safe(lambda: bool(rw.winfo_exists()), False)
        if rw_exists:
            _safe(rw.cancel_drive_work)
        log.info("notdonewarning: rw_exists=%s iswaiting=%s viewable=%s",
                 rw_exists,
                 _safe(lambda: rw.iswaiting()) if rw else None,
                 _safe(lambda: rw.winfo_viewable()) if rw else None)
        if not self.program.Demo: #Should anyone see this?
            ErrorNotice(text=text,title=_("Not Done!"),parent=self,wait=True)
        # self.ui.deiconify()
    def checktosort(self):
        return self.program.status.checktosort() #bool tosort on cur check
    def itemstosort(self):
        return self.program.status.sensestosort()
    def itemssorted(self):
        return self.program.status.sensessorted()
    def tosort(self):
        return self.program.status.tosort() #returns bool
    def updatesortingstatus(self,**kwargs):
        return self.program.settings.updatesortingstatus(**kwargs)
    def verificationcode(self,**kwargs):
        check=kwargs.get('check',self.program.params.check())
        group=kwargs.get('group',self.program.status.group())
        # log.info("about to return {}={}".format(check,group))
        return check+'='+group
    @property
    def lex_ui(self):
        return self.program.lex_ui
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
class Segments(Senses):
    """docstring for Segments."""
    show_second_fields=True
    def buildregex(self,**kwargs):
        """include profile (of those available for ps and check),
        and subcheck (e.g., a: CaC\2)."""
        """Provides self.regex"""
        profile=kwargs.get('profile',self.program.slices.profile())
        if profile is None:
            log.info(_("You haven’t picked a syllable profile yet."))
            return
        self.regex=self.rxdict.makeprofileforcheck(
                        profile=profile,
                        check=kwargs.get('check',self.program.params.check()),
                        group=kwargs.get('group',self.program.status.group()),
                        groupcomparison=getattr(self,'groupcomparison',False)
                                                    )
    def buildregexnocheck(self,**kwargs):
        """This is the same as above, but should get all senses of a profile, regardless of check and value"""
        profile=kwargs.get('profile',self.program.slices.profile())
        self.regex=self.rxdict.fromCV(profile,
                            word=True, compile=True, caseinsensitive=True)
    def ifregexadd(self,regex,form,id):
        # This fn is just to make this threadable
        if regex.search(form):
            self.output+=id
    def formspsprofile(self,**kwargs):
        """I think I want to move away from this"""
        log.info(_("Asked for forms to search for a data slice (only do once!)"))
        ps=kwargs.get('ps',self.program.slices.ps())
        d=self.program.profiles.formstosearch[ps] #{form:sense}
        # log.info("Looking at {} entries".format(len(d)))
        return {k:d[k] for k in d
                        if set(d[k]) & set(self.program.slices.senses(**kwargs))}
    def sensesbyforminregex(self,regex,**kwargs):
        """This function takes in a compiled regex,
        and outputs a list of senses."""
        ps=kwargs.get('ps',self.program.slices.ps())
        # log.info("Kwargs keys: {} (formstosearch n={})".format(kwargs.keys(),
        #                                 len(kwargs['formstosearch'])))
        # log.info("Reduced to {} entries".format(len(dicttosearch)))
        # log.info("Looking for senses by regex {}".format(regex))
        self.output=[s for s in self.program.slices.senses(**kwargs)
                                                    # self.program.db.senses
                        if s.ftypes[self.ftype].textvaluebylang(self.analang)
                        if regex.search(
                        s.ftypes[self.ftype].textvaluebylang(self.analang)
                                        )
                    ]
        # log.info("Found senses: {}".format(self.output))
        return self.output
    def presortgroups(self,**kwargs):
        if self.program.status.presorted(**kwargs):
            log.info(_("Presorting for this check/slice already done! ({args})"
                        "").format(args=kwargs))
            return
        log.info(_("Presorting"))
        cvt=kwargs.get('cvt',self.program.params.cvt())
        ps=kwargs.get('ps',self.program.slices.ps())
        profile=kwargs.get('profile',self.program.slices.profile())
        groups=self.program.status.groups(wsorted=True,**kwargs)
        groups=self.program.status.groups(cvt=cvt)
        msg=_("Presorting ({check}={groups})").format(check=self.program.params.check(),groups=groups)
        log.info(msg)
        w=self.ui.getrunwindow(msg=msg)
        self.program.status.renewsensestosort([],[]) #will repopulate
        check=self.program.params.check()
        # Presort is a best-effort GUESS, and we constrain on cvprofile
        # MEMBERSHIP (data), never re-derive shape by regex (analysis —
        # cvprofile is authoritative). For a single positional check (C1, C2,
        # V1, …: no '='/'x') we guess each member's group from THAT position
        # alone via the positional matcher (rxdict.rx[check] — start-anchored,
        # captures the first consonant and ignores the rest of the form): a
        # 'p'-initial word joins the other 'p' words even if the rest of the
        # form doesn't parse as the profile (e.g. an apparently-CV word the
        # user has recorded as CVC). Wrong guesses are corrected by the user at
        # verify. '=' checks keep the whole-form match (equality needs both
        # positions) but also draw their universe from membership so the
        # not-equal remainder reaches NA. Any other check falls back to the
        # form-seed.
        posrx=None
        if '=' not in (check or '') and 'x' not in (check or ''):
            posrx=self.rxdict.rx.get(check)
        if posrx is not None or '=' in (check or ''):
            unsortedids=set(self.program.slices.senses(ps=ps,profile=profile))
        else:
            self.buildregexnocheck()
            unsortedids=set(self.sensesbyforminregex(self.regex,ps=ps))
        posgroups={} #position value (C1 guess) -> senses; only for positional checks
        if posrx is not None:
            for sense in unsortedids:
                form=sense.ftypes[self.ftype].textvaluebylang(self.analang)
                m=posrx.search(form) if form else None
                if m and m.groups():
                    posgroups.setdefault(m.groups()[-1],set()).add(sense)
        filteredgroups=[i for i in groups if not i.isdigit()]
        ngroups=len(filteredgroups)
        for gi, group in enumerate(filteredgroups):
            if posrx is not None:
                s=set(posgroups.get(group,()))
            else:
                self.buildregex(group=group,cvt=cvt,profile=profile)
                s=set(self.sensesbyforminregex(self.regex,ps=ps))
            if s:
                yield from self.presort(list(s),group,
                    startat=gi*80//max(ngroups,1),
                    endat=(gi+1)*80//max(ngroups,1))
                unsortedids-=s
            yield gi * 80 // max(ngroups,1)
        log.info(_("unsortedids ({count}): {ids}").format(
                                        count=len(unsortedids),
                                        ids=unsortedids
                                        ))
        if '=' in (check or '') and unsortedids:
            # ONLY equality checks auto-populate NA. For an '=' check the
            # not-equal remainder (e.g. C1≠C2) IS the check's result set, so it
            # goes to NA and the user verifies it out by hand — it rides the
            # normal verify loop (layer-3: NA is kept in the group list for '='
            # checks) and is deliberately NOT marked done here.
            #
            # For every OTHER check, words the presort couldn't place are left
            # UNSORTED (to-sort) and simply get presented to sort — NA is NOT a
            # catch-all. NA means the USER skipped the word (taboo, unknown, …)
            # and is terminal; only a user gesture during sorting puts a word
            # there, and it stays out of the verify loop because
            # categorizebygrouping excludes NA from the group list for non-'='
            # checks.
            yield from self.presort(unsortedids,group='NA',startat=80,endat=95)
            self.program.status.group('NA')
        self.program.status.presorted(True)
        self.program.status.store() #after all the above
        self.maybewrite()
        yield 100
    def presort(self,senses,group,startat=0,endat=100):
        """Generator: marks senses into group, yields progress from startat to endat."""
        n=len(senses)
        for i, sense in enumerate(senses):
            self.marksortgroup(sense, group)
            yield startat + (endat-startat) * i // max(n,1)
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
    def build_form_from_verified(self,sense,ftype=None):
        """Build a word's surface form FROM SCRATCH from its confirmed cvprofile +
        the VERIFIED segment values — the authoritative rebuild (contrast the
        conform/patch path, which only mends an existing, maybe-corrupt form).

        ONLY valid once EVERY profile slot is verified: gated by
        `sense.cvverificationdone(ftype)` (the same all-verified predicate data
        export uses). Walks the confirmed profile; for each class occurrence (C1,
        V1, C2, …) takes the verified value from `getcvverificationkeys`' actualkeys
        and concatenates. Returns the built form, or None if not fully verified /
        any slot value missing (e.g. a boundary '='-profile the gate rejects) /
        any slot verified into a still-unnamed (digit-placeholder or NA) group.
        Because it's assembled from verified segments, it can't corrupt — and it
        doesn't depend on profileofform reading the result correctly."""
        ftype=ftype or self.ftype
        if not sense.cvverificationdone(ftype):
            return None
        profile=sense.cvprofilevalue(ftype)
        counts,actualkeys=sense.getcvverificationkeys(ftype)
        if not (profile and actualkeys):
            return None
        seen={}; out=[]
        for cls in profile:
            seen[cls]=seen.get(cls,0)+1
            val=actualkeys.get('{}{}'.format(cls,seen[cls]))
            if val is None: # gate should preclude this; be safe
                return None
            if val=='NA' or val.isdigit():
                # Verified into a group whose NAME is still a digit placeholder
                # (e.g. V1='1'): the verification stands, but an unnamed group
                # must never be written into the form ('bʊsh'→'b1sh'). Defer the
                # build until the group is named — same guard as the patch paths
                # (do_not_do_these) and the conform INSERT.
                log.info("DIAG-formconform BUILD-DEFER %s: %s%s verified into "
                         "unnamed group %r; not building until named",
                         sense.id, cls, seen[cls], val)
                return None
            out.append(val)
        return ''.join(out)
    def updateformtoannotations(self,sense,check=None,write=False):
        """This should take a sense and check, in normal usage.
        provide self.ftype prior to this
        If we want to update forms to *all* annotations, don't give check.
        Iterate across a few or many senses.
        Iterate also across ftypes, to catch them all...
        that would likely need more smarts for affix and root distinction."""
        def maybe_add_polygraph(pg):
            sc=self.program.params.cvt()
            scvalue=self.program.profiles.polygraphs[self.analang][sc][value]
            if not scvalue:
                scvalue=True
                self.program.profiles.setupCVrxs() #costly; only when needed!
        def do_not_do_these(value,check=None):
            # Only SEGMENTAL checks update the form: those are the ones with a
            # position regex in rxdict.rx (V1, C1, …). The syllable-prep primitives
            # (#C, C#, syls) and the profile check (lc) have no regex — feeding them
            # to rxdict.update raises KeyError (e.g. rx['#C']). Skip any check whose
            # '='-parts aren't all segmental.
            if check is not None and not all(c in self.rxdict.rx
                                             for c in check.split('=')):
                return True
            return value in ['NA',None] or (check and check.isdigit()) or value.isdigit()
        form_ori=formvalue=sense.textvaluebyftypelang(self.ftype,self.analang)
        if not formvalue:
            log.info(_("updateformtoannotations didn’t return a form value for "
                    "{id}, {check}, {ftype}, {ana}").format(id=sense.id, check=check, ftype=self.ftype, ana=self.analang))
            return
        # log.info("fnode: {}; text: {}".format(fnode,t.text))
        annodict=sense.annotationvaluedictbyftypelang(self.ftype,self.analang)
        conflict_text=_("Not updating ‘{form}’ (conflict in {anno}.").format(form=formvalue, anno=annodict)
        error_nb=_("Check the log for any further conflicts")
        error=False
        # AUTHORITATIVE path: if EVERY segment is verified, build the form FROM
        # SCRATCH from the confirmed profile + verified segment values — don't patch
        # the existing (maybe-corrupted) form. Gated by cvverificationdone. Only on a
        # whole-word update (no single check); partially-verified words fall through
        # to the conform/patch stopgap below.
        if not check:
            built=self.build_form_from_verified(sense)
            if built is not None:
                if built!=form_ori:
                    key=max([int(i) for i in annodict.keys() if i.isdigit()]+[-1])+1
                    sense.annotationvaluebyftypelang(self.ftype,self.analang,
                                                     str(key),form_ori)
                sense.textvaluebyftypelang(self.ftype,self.analang,built)
                log.info("DIAG-formconform RESULT %s BUILD %r→%r profile=%s "
                         "(from verified segments)", sense.id, form_ori, built,
                         sense.cvprofilevalue(self.ftype))
                if write:
                    self.maybewrite()
                return
        # DIAG-formconform (grep this): the confirmed cvprofile is the TARGET the
        # updated form must still read as. Log the starting picture per word so the
        # whole from>to + profile-conforming story is visible.
        confirmed=sense.cvprofilevalue(self.ftype)
        ps=sense.psvalue()
        # PRIMITIVES CONSTRAIN the profile (item Model): if the word's verified
        # #C/C#/syls make the confirmed cvprofile inconsistent — e.g. 'tribe' has
        # syls=1 but its cvprofile still reads 2-syl 'CCVCV' — conform to the
        # primitive-CONSTRAINED profile ('CCVC'), not the raw one. constrain_profile
        # never yields a syls-violating shape, so this is the authoritative target.
        target=confirmed
        av=sense.annotationvaluebyftypelang
        beg=av(self.ftype,self.analang,'#C'); end=av(self.ftype,self.analang,'C#')
        syls=av(self.ftype,self.analang,'syls')
        if confirmed and confirmed!='Invalid' and beg and end and syls:
            r=self.program.params.constrain_profile(confirmed,beg,end,syls)
            if r.get('profile') and r['profile']!=confirmed:
                log.info("DIAG-formconform CONSTRAIN %s: cvprofile %s + (#C=%s C#=%s "
                         "syls=%s) → target %s", sense.id, confirmed, beg, end, syls,
                         r['profile'])
                target=r['profile']
        # Segmental verified values (V1=…, C1=…) for the one-line RESULT scan (below):
        # only checks whose '='-parts are all segmental (in rxdict.rx), skipping
        # primitives/lc/slices/old-form annos.
        segstr=', '.join('{}={}'.format(c,v) for c,v in annodict.items()
            if v and all(p in self.rxdict.rx for p in c.split('=')))
        if check: #just update to this annotation
            value=annodict[check]
            if value is None or value.isdigit(): #don't update to unnamed groups
                # log.info(f"Not updating {sense.id} form {formvalue} to "
                #         f"{check}={value}")
                return
            elif self.check_with_conflicting_value(annodict,check):
                if not self.updateconflictwarned:
                    ErrorNotice('\n'.join([conflict_text,error_nb]))
                    self.updateconflictwarned=True
                else:
                    log.error(conflict_text)
                return
            elif not do_not_do_these(value,check):
                #value not in [None, 'NA']: #should I act on ''?
                prev=formvalue
                formvalue=self.rxdict.update(formvalue,check,value)
                #This should update formstosearch (prev→new; `f` was undefined):
                if formvalue != prev:
                    self.program.profiles.addtoformstosearch(sense,prev,formvalue)
                if len(value)>1:
                    maybe_add_polygraph(value)
        else: #update to all annotations
            for check,value in annodict.items():
                if do_not_do_these(value,check):
                    continue #don't make changes for NA checks
                elif self.check_with_conflicting_value(annodict,check):
                    if not self.updateconflictwarned:
                        ErrorNotice('\n'.join([conflict_text,error_nb]))
                        self.updateconflictwarned=True
                    else:
                        log.error(conflict_text)
                    error=True
                else:
                    prev=formvalue
                    formvalue=self.rxdict.update(formvalue,check,value)
                    log.info("DIAG-formconform CHECK %s %s=%s: %r>%r",
                             sense.id, check, value, prev, formvalue)
        if not error:
            # Conform the candidate form to the word's TARGET profile (the confirmed
            # cvprofile, CONSTRAINED to the verified primitives above): the form must
            # re-parse (profileofform) to it. Applying verified segment values
            # positionally (rxdict.update) can leave the form the wrong SHAPE ('heart'
            # CVCC → 'hot' CVC) or with unpronounced/stray segments (silent 'e' →
            # CVCV; a doubled or mis-read consonant). So:
            #   • already reads as target → commit;
            #   • else CONFORM via _conform_form_to_profile — DROP segments the
            #     profile doesn't want (trailing OR internal: silent 'e', a stray/
            #     doubled C) and INSERT a missing slot from its verified value — then
            #     re-verify. Dropping IS the goal (the profile is authoritative about
            #     which segments exist);
            #   • if it still can't reach the profile → refuse + flag, unchanged.
            # All paths logged DIAG-formconform (grep). Check conformance whenever
            # there's a valid target — NOT only when the update changed the form: a
            # form already non-conforming (e.g. a prior update corrupted 'year' to
            # 'ieer', which doesn't read as CVC) must still be caught/conformed, not
            # slip through as UNCHANGED just because this update was a no-op.
            if target and target!='Invalid':
                got=self.rxdict.profileofform(formvalue,ps)
                if got==target:
                    log.info("DIAG-formconform OK %s: %r>%r reads %s",
                             sense.id, form_ori, formvalue, target)
                else:
                    self.rxdict.profileofform(formvalue,ps,diag=True) # breakdown on failure only
                    conf=self._conform_form_to_profile(formvalue,target,annodict,ps)
                    if conf:
                        newform,drops,ins=conf
                        log.info("DIAG-formconform CONFORM %s: %r>%r>%r (dropped=%s "
                                 "inserted=%s) → %s", sense.id, form_ori, formvalue,
                                 newform, drops, ins, target)
                        formvalue=newform
                    else:
                        log.error("DIAG-formconform RESULT %s REFUSE %r✗%r reads %s "
                                 "target=%s segs=[%s] (left unchanged)", sense.id,
                                 form_ori, formvalue, got, target, segstr)
                        if not self.updateconflictwarned:
                            ErrorNotice('\n'.join([_("Not updating ‘{old}’ → ‘{new}’: "
                                "it can’t be made to read as its profile {prof} "
                                "(reads as {got}).").format(old=form_ori,new=formvalue,
                                prof=target,got=got),
                                _("Confirmed segments: {segs}").format(
                                    segs=segstr or _("(none)")),
                                _("Left unchanged — review by hand."),error_nb]))
                            self.updateconflictwarned=True
                        return
            sense.textvaluebyftypelang(self.ftype,self.analang,formvalue)
            if form_ori != formvalue:
                key=max([int(i) for i in annodict.keys() if i.isdigit()]+[-1])+1
                sense.annotationvaluebyftypelang(self.ftype,self.analang,
                                                    str(key),form_ori)
                log.info("DIAG-formconform RESULT %s COMMIT %r→%r target=%s segs=[%s] "
                         "(old form saved as anno %s)", sense.id, form_ori, formvalue,
                         target, segstr, key)
            else:
                log.info("DIAG-formconform RESULT %s UNCHANGED %r target=%s segs=[%s]",
                         sense.id, form_ori, target, segstr)
        else:
            log.info("DIAG-formconform RESULT %s REFUSE(conflict) %r target=%s segs=[%s]",
                     sense.id, form_ori, target, segstr)
        if write:
            self.maybewrite()
    def _conform_form_to_profile(self, form, target, annodict, ps):
        """DRAFT (internal drops/inserts): rebuild `form` so profileofform==target.
        Segment the form (rxdict.segmentsofform), then walk it against the target
        profile: keep a segment whose class the target wants here; DROP one the
        target doesn't (trailing OR INTERNAL — a silent 'e', a stray/doubled C);
        when the target needs a slot the form lacks, INSERT that slot's VERIFIED
        value (Cn/Vn from annodict) — a justified insert only; an unverified missing
        slot → give up. Greedy (prefers drops), so the rebuilt form is RE-CHECKED
        with profileofform; if it doesn't read as target, return None (caller
        refuses — never a corrupt commit). Returns (newform, dropped, inserted) or
        None. Logs DIAG-formconform. See rebuild_updateformstoannotations item."""
        segs=self.rxdict.segmentsofform(form)
        seg_profile=''.join(c for _,c in segs)
        if seg_profile!=self.rxdict.profileofform(form,ps):
            # greedy tokenizer diverged from the oracle; the final re-check still
            # protects correctness, but note it so odd cases are explainable.
            log.info("DIAG-formconform SEG-DIVERGE %r: segments=%s profileofform=%s",
                     form, seg_profile, self.rxdict.profileofform(form,ps))
        def slot(cls,idx):            # nth (0-based) occurrence of cls → 'C1','V2',…
            return '{}{}'.format(cls,idx+1)
        tcount={}; ti=si=0; out=[]; dropped=[]; inserted=[]
        while ti<len(target) or si<len(segs):
            tcls=target[ti] if ti<len(target) else None
            scls=segs[si][1] if si<len(segs) else None
            if tcls is not None and scls==tcls:               # class matches → keep
                out.append(segs[si][0]); si+=1
                tcount[tcls]=tcount.get(tcls,0)+1; ti+=1
            elif scls is not None:                            # form has an extra → DROP
                dropped.append(segs[si][0]); si+=1
            else:                                             # form lacks a slot → INSERT
                name=slot(tcls,tcount.get(tcls,0))
                val=annodict.get(name)
                if not val or val=='NA' or (isinstance(val,str) and val.isdigit()):
                    log.info("DIAG-formconform INSERT-UNJUSTIFIED %r: target %s slot "
                             "%s has no verified value; giving up", form, target, name)
                    return None
                out.append(val); inserted.append((name,val))
                tcount[tcls]=tcount.get(tcls,0)+1; ti+=1
        newform=''.join(out)
        got=self.rxdict.profileofform(newform,ps)
        if got!=target:
            log.info("DIAG-formconform ALIGN-FAIL %r→%r reads %s not target %s "
                     "(dropped=%s inserted=%s)", form, newform, got, target,
                     dropped, inserted)
            return None
        return newform, dropped, inserted
    def setitemgroup(self,item,check,group,**kwargs):
        # log.info(_("Setting segment sort group"))
        item.annotationvaluebyftypelang(self.ftype,self.analang,check,group)
    def updateformsallchecks(self):
        """Generator: updates forms from annotations for every sense."""
        log.info(_("updateformsallchecks"))
        senses=self.program.db.senses
        n=len(senses)
        for i, sense in enumerate(senses):
            self.updateformtoannotations(sense)
            yield i * 100 // n if n else 100
        self.maybewrite()
    def updateformsbycheck(self):
        """Generator: updates forms from annotations for current check."""
        senses=list(self.getsensesincheck())
        n=len(senses)
        for i, sense in enumerate(senses):
            self.updateformtoannotations(sense,self.check)
            yield i * 100 // n if n else 100
        self.maybewrite()
    def update_annotations_to_glyphs(self):
        """Generator: updates annotations for all glyphs, yields 0-100 progress.
        Errors collected in self.update_annotations_errors."""
        glyphs=list(self.program.alphabet.glyph_members())
        nglyphs=len(glyphs)
        errors=[]
        for gi, k in enumerate(glyphs):
            gen=self.update_annotations_by_glyph(k)
            for p in gen:
                yield gi * 100 // max(nglyphs,1)
            if self.update_annotations_error:
                errors.append(self.update_annotations_error)
        self.update_annotations_errors=errors
    def update_annotations_by_glyph(self,glyph):
        """Generator: aligns groups to macrogroups, yields 0-100 progress.
        Returns error string (via self.update_annotations_error) if conflict detected.
        """
        def newform(x): #move this to alphabet
            return '_'.join(x.split('_')[:4]+[glyph])
        gm=self.program.alphabet.glyph_members()
        for item in gm[glyph]:
            if item.split('_')[-1] in ['NA']:
                continue
            if (item.split('_')[-1] != glyph and
                newform(item) in [i for j in gm.values() for i in j]):
                txt=_("Conflict: cannot rename ‘{item}’ to ‘{glyph}’; "
                    "‘{new}’ already exists.").format(item=item, glyph=glyph, new=newform(item))
                log.error(txt)
                self.update_annotations_error=txt
                return
        self.update_annotations_error=None
        log.info(_("update_annotations_by_glyph safely: ‘{members}’ to ‘{glyph}’").format(members=gm[glyph], glyph=glyph))
        items=list(gm[glyph])
        nitems=len(items)
        for ii, item in enumerate(items):
            kwargs=self.program.alphabet.parse_verificationcode(item)
            senses=self.program.slices.inslice(
                            self.getsensesincheckgroup(**kwargs),
                            **kwargs)
            for sense in senses:
                self.marksortgroup(sense, glyph,
                                   **{k:v for k,v in kwargs.items()
                                      if k != 'group'},
                                   not_sorting=True,
                                   updateverification=True,
                                   updateforms=False)
            self.program.status.renamegroup(kwargs.pop('group'),glyph,**kwargs)
            self.program.alphabet.rename_glyph_member(item,newform(item))
            yield ii * 100 // max(nitems,1)
        log.info(_("update_annotations_by_glyph done with ‘{members}’ to ‘{glyph}’").format(members=gm[glyph], glyph=glyph))
    def default_glyphs(self):
        return [i for i in 
                self.program.alphabet.glyphdict()[self.program.params.cvt()]
                if i.isdigit()]
    def name_new_glyphs(self):
        """Everything referenced here needs to refer to macrogroups ONLY.
        Users should never be changing the name of an individual sort group.
        This method is for default named groups (int), to see that they have
        some name, and is automatically enforced.
        Changes requested by the user are handled in TranscribeC/V
        """
        from tasks.transcribe_glyph import (GlyphTranscribeHelper,
                                             VOWEL_GLYPHS, CONSONANT_GLYPHS)
        glyphs=self.default_glyphs()
        self.program.alphabet.glyphdict()[self.program.params.cvt()]
        cvt=self.program.params.cvt()
        if cvt == 'C':
            glyphspossible=CONSONANT_GLYPHS
        elif cvt == 'V':
            glyphspossible=VOWEL_GLYPHS
        else:
            log.error(_("Not sure what to do with this glyph "
                "({cvt}; {glyphs})").format(cvt=cvt, glyphs=glyphs))
            return False
        w=GlyphTranscribeHelper(self, glyphspossible=glyphspossible)
        # "Go back and join with one of ← these groups": wire the helper's go_back
        # to flag the current glyph. Without this, on_go_back was None, so the
        # button just closed the window → "not done" warning (the regression).
        # We un-distinguish the flagged glyph and return True so warnorcontinue
        # restarts maybesort onto the join-glyphs step (which runs BEFORE
        # name_new_glyphs) — same effect as redo_joinglyphs, but via the normal
        # after()-restart rather than a nested maybesort.
        self._glyph_go_back=None
        w.on_go_back=lambda:setattr(self,'_glyph_go_back',w.group)
        self.ui.withdraw()
        problems=[]
        while digits := self.default_glyphs():
            glyph=digits[0]
            log.info(_("working on {glyph} of {digits}").format(glyph=glyph, digits=digits))
            w.makewindow(glyph)
            if self._glyph_go_back is not None:
                g=self._glyph_go_back
                self._glyph_go_back=None
                w.destroy()
                self.ui.deiconify()
                self.group=self.program.alphabet.glyph(g)
                self.program.alphabet.undistinguish_any_with(g=self.group)
                self._skip_predistinguish_once=True #don't re-hide the pair to join
                return True  # → maybesort restarts → join-glyphs step picks it up
            if w.window_failed:
                #This removes verification, thus to do status:
                self.program.alphabet.mark_glyph_not_done(glyph)
                problems.append(glyph)
            elif not w.ok_done: #user exits without 'OK'
                break
        w.destroy()
        self.ui.deiconify()
        if digits or problems:
            log.error(_("User exited with work still to do: {digits} {problems}").format(digits=digits, problems=problems))
        return not bool(digits)
    def rename_macrogroup(self,x,y,updatestatus=False):
        for item in list(self.program.alphabet.glyph_members()[x]):
            kwargs=self.program.alphabet.parse_verificationcode(item)
            log.info(_("Updating verification from ‘{old}’ to ‘{new}’ for {args}").format(old=x, new=y, args=kwargs))
            self.rename_group_verification(x,y,**kwargs)
        #Do the above first, before glyph_members changes
        self.program.alphabet.rename_glyph(x,y)
        for i in self.update_annotations_by_glyph(y):
            pass  # consume generator synchronously
        if updatestatus:
            for i in self.program.settings.reloadstatusdata():
                pass
            self.program.settings.reloadstatusdata_cleanup()
    def getsensesincheck(self):
        return [
                i for i in self.program.db.senses
                if i.ftypes[self.ftype].annotationkeyinlang(self.check)
                ]
    def getsensesingroup(self,check,group):
        ftype=self.program.params.ftype()
        lang=self.program.params.analang()
        return [
                i for i in self.program.db.senses
                # str(group): group names are strings in LIFT (and via the example
                # path, analysis.py:217), but a default integer group can reach here
                # as an int — then "3"==3 is False, the verify codes ZERO members,
                # and the next full-reload recompute reads the group as NOTDONE
                # (the groups-keep-unverifying bug). Match the str-guarded siblings.
                if i.ftypes[ftype].annotationvaluebylang(lang,check) == str(group)
                ]
    def getitemgroup(self,item,check):
        # ftype=self.program.params.ftype() #not helpful for Tone.getitemgroup
        return item.annotationvaluebyftypelang(self.ftype,self.analang,check)
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.updateconflictwarned=False
        self.dodone=True
        self.dodoneonly=False #don't give me other words
        self.ftype=self.program.params.ftype()
        self.rxdict=self.program.profiles.rxdict
class Consonants():
    cvt='C'
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
class Vowels():
    cvt='V'
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
class WordCollection(Segments):
    """This task collects words, from the SIL CAWL, or one by one."""
    taskicon = 'iconWord'
    do_not_show_slices=True
    no_leaderboard=True
    def run_addCAWLentries(self):
        text=_("Adding CAWL entries to fill out, in established database.")
        self.ui.wait_and_drive_work(text, self.addCAWLentries())
    def dobuttonkwargs(self):
        if self.program.taskchooser.cawlmissing:
            fn=self.run_addCAWLentries
            text=_("Add remaining CAWL entries")
            tttext=_("This will add entries from the Comparative African "
                    "Wordlist (CAWL) which aren’t already in your database "
                    "(you are missing {} CAWL tags). If the appropriate "
                    "glosses are found in your database, CAWL tags will be "
                    "merged with those entries."
                    "\nDepending on the number of entries, this may take "
                    "awhile.").format(count=len(self.program.taskchooser.cawlmissing))
        else:
            text=_("Add a Word")
            fn=self.addmorpheme
            tttext=_("This adds any word, but is best used after filling out a "
                    "wordlist, if the word you want to add isn’t there "
                    "already.")
        return {'text':text,
                'fn':fn,
                # column=0,
                'font':'title',
                'compound':'bottom', #image bottom, left, right, or top of text
                'image':self.program.taskchooser.theme.photo['Word'],
                'sticky':'ew',
                'tttext':tttext
                }
    def getlisttodo(self,**kwargs):
        """Whichever field is being asked for (self.nodetag), this fn returns
        which are left to do."""
        if hasattr(self,'byslice') and self.byslice:
            log.info(_("Limiting segment work to this slice"))
            all=[i.entry for i in self.program.slices.senses()]
        else:
            all=self.program.db.entries
        if self.program.settings.start_at_entry:
            log.info("Starting at entry {}".format(self.program.settings.start_at_entry))
            if not self.program.settings.end_at_entry:
                log.info("end_at_entry not found; finishing to the end")
                self.program.settings.end_at_entry=len(all)
            else:
                log.info("Ending at entry {}".format(self.program.settings.end_at_entry))
            all=all[self.program.settings.start_at_entry:self.program.settings.end_at_entry]
            log.info("Working on {} entries".format(len(all)))
        else:
            log.info("start_at_entry not found")
        # DIAG-todo (2026-07-13, Kent: parse/no-parse variants presented
        # DIFFERENT words, and Add-and-Parse said "all done" falsely): one
        # line per build naming the basis this task's list keys on.
        log.info("DIAG-todo %s: ftype=%r dodone=%s dodoneonly=%s all=%d",
                 type(self).__name__, self.ftype,
                 getattr(self,'dodone',None), getattr(self,'dodoneonly',None),
                 len(all))
        if self.dodone and not self.dodoneonly: #i.e., all data
            return all
        done=[i for i in all
                    if i.sense.textvaluebyftypelang(self.ftype,self.analang)]
        if self.dodone: #i.e., dodoneonly
            log.info("DIAG-todo %s: done-only=%d",type(self).__name__,len(done))
            return done
        # At this point, done isn't wanted
        todo=[x for x in all if x not in done] #set-set may be better
        log.info(_("To do: ({count}) First 5: {items}").format(count=len(todo),items=todo[:5]))
        return todo
    def getinstructions(self):
        return _("Type the word in your language that goes with these meanings."
                "\nGive a single word (not a phrase) wherever possible."
                "\nJust type consonants and vowels; don’t worry about tone "
                "for now.")
    def getwords(self):
        p = self.lex_ui
        self.entries=self.getlisttodo()
        self.nentries=len(self.entries)
        self.index=0
        # A5 in-place reload: resume at the word the user was on. Guid-keyed
        # (not index) because the todo list may have shifted with the merged
        # data. Set in getword(); handed over by reload_database.
        anchor=getattr(self.program,'_reload_anchor',None)
        if anchor and anchor.get('guid'):
            guids=[getattr(e,'guid',None) for e in self.entries]
            if anchor['guid'] in guids:
                self.index=guids.index(anchor['guid'])
                log.info("word collection: resuming at %s (reload anchor)",
                         anchor['guid'])
            self.program._reload_anchor=None
        self.wordsframe=p.frame(self.ui.frame,row=1,column=1,sticky='ew')
        self.instructions=p.label(self.wordsframe,
                                    text=self.getinstructions(),
                                    row=0, column=0)
        self.dirfn=self.nextword
        r=self.getword()
    def promptstrings(self,lang):
        if lang == self.analang:
            text=_("What is the form of the new "
                    "morpheme in {name} \n(consonants and vowels only)?"
                    "").format(name=self.program.settings.languagenames[lang])
            ok=_('Use this form')
            skip=None
        else:
            text=_("What does ‘{form}’ mean in {lang}?").format(
                            form=self.ui.runwindow.form[self.analang],
                            lang=self.program.settings.languagenames[lang])
            ok=_("Use this {lang} gloss for ‘{form}’").format(
                            lang=self.program.settings.languagenames[lang],
                            form=self.ui.runwindow.form[self.analang])
            self.ui.runwindow.glosslangs.append(lang)
            skip = _("Skip {lang} gloss").format(lang=self.program.settings.languagenames[lang])
        return {'lang':lang, 'prompt':text, 'ok':ok, 'skip':skip}
    def submitform(self,lang):
        self.ui.runwindow.form[lang]=self.ui.runwindow.form[lang].get()
        self.ui.runwindow.frame2.destroy()
    def promptwindow(self,lang):
        p = self.lex_ui
        def skipform(event=None):
            del self.ui.runwindow.form[lang]
            self.ui.runwindow.frame2.destroy() #Just move on.
        strings=self.promptstrings(lang)
        self.ui.runwindow.frame2=p.frame(self.ui.runwindow.frame,
                                        row=1,column=0,
                                        sticky='ew',
                                        padx=25,pady=25)
        getform=p.label(self.ui.runwindow.frame2,text=strings['prompt'],
                        font='read',row=0,column=0,
                        padx=self.ui.runwindow.padx,
                        pady=self.ui.runwindow.pady)
        #field rendering is better in another frame:
        eff=p.frame(self.ui.runwindow.frame2,row=1,column=0)
        #variable and field for entry:
        self.ui.runwindow.form[lang]=p.string_var()
        formfield = p.entry_field(eff, render=True,
                                    text=self.ui.runwindow.form[lang],
                                    font='readbig',
                                    row=1,column=0,
                                    sticky='')
        formfield.focus_set()
        formfield.bind('<Return>',lambda event,l=lang:self.submitform(l))
        formfield.rendered.grid(row=2,column=0,sticky='new')
        sub_btn=p.button(self.ui.runwindow.frame2,text = strings['ok'],
                            command = self.submitform,
                            anchor ='c',row=2,column=0,sticky='')
        if strings['skip']:
            sub_btnNo=p.button(self.ui.runwindow.frame2,
                                text = strings['skip'],
                                command = skipform,
                                row=1,column=1,sticky='')
        self.ui.runwindow.lift()
        self.ui.runwindow.waitdone()
        sub_btn.wait_window(self.ui.runwindow.frame2) #then move to next step
    def addmorpheme(self):
        p = self.lex_ui
        self.ui.getrunwindow()
        self.ui.runwindow.form={}
        self.ui.runwindow.glosslangs=list()
        form={}
        self.ui.runwindow.padx=50
        self.ui.runwindow.pady=10
        self.ui.runwindow.title(_("Add Morpheme to Dictionary"))
        title=_("Add {lang} morpheme to the dictionary").format(
                            lang=self.program.settings.languagenames[self.analang])
        p.label(self.ui.runwindow.frame,text=title,font='title',
                justify=p.LEFT,
                anchor='c',sticky='ew',
                row=0,column=0,
                padx=self.ui.runwindow.padx,
                pady=self.ui.runwindow.pady)
        # Run the above script (makewindow) for each language, analang first.
        # The user has a chance to enter a gloss for any gloss language
        # already in the datbase, and to skip any as needed/desired.
        for lang in [self.analang]+self.program.db.glosslangs:
            if lang in self.ui.runwindow.form:
                continue #Someday: how to do monolingual form/gloss here
            if not self.ui.runwindow.exitFlag.istrue():
                x=self.promptwindow(lang)
                if x:
                    return
        """get the new sense back from this function, which generates it"""
        if not self.ui.runwindow.exitFlag.istrue(): #don't do this if exited
            self.ui.runwindow.withdraw() #or wait?
            sense=self.program.db.addentry(ps='',analang=self.analang,
                            glosslangs=self.ui.runwindow.glosslangs,
                            form=self.ui.runwindow.form)
            # Update profile information in the running instance, and in the file.
            self.ui.runwindow.on_quit()
            """The following are useless without ps information, so they will
            have to come later."""
    def addCAWLentries(self):
        """Generator: adds CAWL entries, yields 0-100 progress."""
        # move this to templates!!
        text=_("Adding CAWL entries to fill out, in established database.")
        log.info(text)
        self.cawldb=loadCAWL()
        added=[]
        modded=[]
        missing=self.program.taskchooser.cawlmissing
        ntotal=len(missing)
        for ni, n in enumerate(missing):
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
                log.info(_("Found a noun, using {ps}").format(ps=self.program.settings.nominalps))
                eps.set('value',self.program.settings.nominalps)
            elif epsv == 'Verb': #don't translate!
                log.info(_("Found a verb, using {ps}").format(ps=self.program.settings.verbalps))
                eps.set('value',self.program.settings.verbalps)
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
                entry=self.program.db.get('entry',gloss=g,glosslang=lang,
                                        ).get('node') #maybe []
                if entry:
                    log.info(_("Found gloss of SILCAWL line #{line:04} ({gloss}); "
                            "adding info to that entry.").format(line=n,gloss=g))
                    self.program.db.fillentryAwB(entry[0],e)
                    modded.append(n)
                    break
            if not entry: #i.e., no match for any self.glosslangs gloss
                tnodes=e.findall('lexical-unit/form/text')
                for tn in tnodes:
                    tn.text=''
                log.info(_("Gloss of SILCAWL line #{line:04} ({gloss}) not found; "
                        "copying over that entry.").format(line=n,gloss=g))
                self.program.db.nodes.append(e)
                added.append(n)
            yield ni * 100 // max(ntotal,1)
        if added or modded:
            self.program.db.write()
            title=_("Entries Added!")
            text=_("Added {count} entries from the SILCAWL").format(count=len(added))
            if len(added)<100:
                text+=': ({})'.format(added)
            text+=_("\nModded {count} entries with new information from the "
                    "SILCAWL").format(count=len(modded))
            if len(modded)<100:
                text+=': ({})'.format(modded)
            self.program.taskchooser.getcawlmissing()
            self.dobuttonkwargs()
        else:
            title=_("Error trying to add SILCAWL entries")
            text=_("We seem to have not added or modded any entries, which "
                    "shouldn’t happen! (missing: {missing})"
                    "").format(missing=self.program.taskchooser.cawlmissing)
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
        log.info(_("WordCollection trying to store {value} ({type})").format(value=self.var.get(),type=self.ftype))
        try:
            if self.ftype in ['lc','lx']:
                self.sense.textvaluebyftypelang(self.ftype,
                                            self.analang,
                                            self.var.get())
            elif self.ftype == 'pl':
                self.entry.plvalue(
                    self.program.settings.secondformfield[self.program.settings.nominalps],
                    self.var.get())
                # lift.prettyprint(self.entry.pl)
            elif self.ftype == 'imp':
                self.entry.fieldvalue(
                        self.program.settings.secondformfield[self.program.settings.verbalps],
                        self.var.get())
            # self.entry.lc.textvaluebylang(self.analang,self.var.get())
            self.maybewrite() #only if above is successful
            # lift.prettyprint(self.entry)
        # except KeyError:
        except AttributeError as e:
            log.info(f"Not storing word (WordCollection): {e}")
        except AssertionError as e:
            log.info(f"Not storing empty value (WordCollection): {e} {self.var=} "
                    f"{type(self.var)=}")
        except Exception as e:
            log.info(f"Exception storing word (WordCollection): {e}")
    def markimage(self,url,w=None):
        """return to file, LIFT"""
        log.info("Selected image {}".format(url))
        if w:
            w.on_quit()
        filename=self.sense.imagename() #new file name
        self.sense.illustrationvalue(filename)
        self.sense.save_illustration_to_file(url)
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
        p = self.lex_ui
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
            self.selectionwindow.sf=p.scrolling_frame(
                        self.selectionwindow.frame,row=2,column=0)
            for n,f in enumerate(files):
                # log.info("Using row {}, col {}".format(n//cols,n%cols))
                    i=p.image_frame(self.selectionwindow.sf.content,url=f,
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
        self.selectionwindow=p.window(self)
        title=_("Select a good image for {glosses}").format(glosses=self.glossesthere)
        self.selectionwindow.title(title)
        t=p.label(self.selectionwindow.frame,text=title, font='title',
                    row=0,column=0)
        if self.sense.image:
            self.sense.image.scale(t.theme.scale, pixels=65, scaleto='height')
            t['image']=self.sense.image.scaled
            t['compound']='right'
        imageparameters=p.frame(self.selectionwindow.frame,
                                row=1, column=0, sticky='e')
        fontsize='small'
        parameterseparation=10
        p.button(imageparameters,text=_("Browse"), font='small',
            command=lambda x=self.selectionwindow:self.selectlocalimage(w=x),
            ipady=0,row=0,column=imageparameters.ncolumns())
        p.label(imageparameters,text="", font=fontsize,
                    width=parameterseparation,
                    row=0,column=imageparameters.ncolumns())
        bdict={pixelopts:{},colopts:{}}
        bdict[pixelopts][-1]=p.button(imageparameters,text='-', font=fontsize,
                            command=lambda x=-1:makegrid(pixels=x),ipady=0,
                            width=1,row=0,column=imageparameters.ncolumns())
        p.label(imageparameters,text=_("Image Size"), font=fontsize, padx=2,
                    row=0,column=imageparameters.ncolumns())
        bdict[pixelopts][1]=p.button(imageparameters,text='+', font=fontsize,
                            command=lambda x=1:makegrid(pixels=x),ipady=0,
                            width=1,row=0,column=imageparameters.ncolumns())
        p.label(imageparameters,text="", font=fontsize,
                    width=parameterseparation,
                    row=0,column=imageparameters.ncolumns())
        bdict[colopts][-1]=p.button(imageparameters,text='-', font=fontsize,
                            command=lambda x=-1:makegrid(cols=x),ipady=0,
                            width=1,row=0,column=imageparameters.ncolumns())
        p.label(imageparameters,text=_("Columns"), font=fontsize, padx=2,
                    row=0,column=imageparameters.ncolumns())
        bdict[colopts][1]=p.button(imageparameters,text="+", font=fontsize,
                            command=lambda x=1:makegrid(cols=x),ipady=0,
                            width=1,row=0,column=imageparameters.ncolumns())
        makegrid()
    def getimagefiles(self):
        dir=file.pathname_from_base_dir(self.sense.imgselectiondir)
        if file.exists(dir):
            return dir,[i for i in file.getfilesofdirectory(dir)
                                if "terms.txt" not in str(i)]
        else:
            log.info(_("{dir} doesn’t seem to exist.").format(dir=dir))
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
            log.info(_("There don’t seem to be any images to show."))
            return 1
    def downloadallCAWLimages(self):
        for self.sense in self.program.db.senses:
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
        self.ui.wait(msg=_("Dowloading images from OpenClipart.org\n{glosses}"
                        "").format(glosses=" ".join(self.sense.collectionglosses)),
                    cancellable=True)
        # try/finally guarantees the download dialog closes even if an
        # unexpected error (not just the handled MaxRetryError) is raised.
        try:
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
            if (self.program.me and not nogui) or len(self.images) < 5:
                text=_("Found {count} images!").format(count=len(self.images))
                if problems:
                    text+=_("\nProblems downloading {count} images").format(count=problems)
                ErrorNotice(text,
                            button=(_("Select local image"),self.selectlocalimage))
        finally:
            self.ui.waitdone()
    def killwordframe(self):
        f=getattr(self,'wordframe',None)
        if hasattr(f,'winfo_exists') and f.winfo_exists():
            # log.info("Destroying word frame")
            f.destroy()
            # log.info("Destroy done")
        # else:
        #     log.info("Not destroying word frame {}".format(isinstance(f,ui.Frame)))
        #     log.info("word frame: {}".format(f))
        #     if f:
        #         log.info("word frame exists: {}".format(f.winfo_exists()))
    def dowordframe(self):
        p = self.lex_ui
        f=getattr(self,'wordframe',None)
        if hasattr(f,'winfo_exists') and f.winfo_exists():
            # log.info("Skipping word frame; already exists!")
            return
        log.info(_("doing word frame"))
        self.wordframe=p.frame(self.wordsframe,row=1,column=0,sticky='ew')
        self.prog=p.label(self.wordframe, text='', row=1, column=3,
                            font='small')
        self.glossesline=p.label(self.wordframe, text='',
                                    font='read',
                                    row=1, column=0, columnspan=3, sticky='ew')
        back=p.button(self.wordframe,text=_("Back"),cmd=self.backword,
                        row=4, column=0, sticky='w',anchor='w')
        self.instructions2=p.label(self.wordframe,text='',font='small',
                        row=4, column=1, sticky='ew',anchor='c')
        next=p.button(self.wordframe,text=_("Next"),cmd=self.nextword,
                        row=4, column=2, sticky='e',anchor='e')
        self.var=p.string_var()
        self.lxenter=p.entry_field(self.wordframe,textvariable=self.var,
                                font='readbig',
                                row=5,column=0,columnspan=3,
                                sticky='ew')
        if isinstance(self.task,Parse):
            self.parsebutton=p.label(self.wordframe,
                                        text=self.cparsetext,
                                        row=6, column=1,
                                        sticky='w',
                                        anchor='w')
        next.bind_all('<Up>',lambda event: self.backword(nostore=True))
        next.bind_all('<Prior>',lambda event: self.backword(nostore=True))
        next.bind_all('<Down>',lambda event: self.nextword(nostore=True))
        next.bind_all('<Next>',lambda event: self.nextword(nostore=True))
    def updatereturnbind(self):
        """Move to UI?"""
        """ I no longer want users to select words here. They should be 
        immutable at this point, like glosses.
        """
        log.info(_("Updating binding ({state})").format(state=self.state()))
        if self.state() == 'withdrawn':
            self.unbind_all('<Return>')
        else: #only bind to non-withdrawn window
            self.lxenter.bind_all('<Return>',
                                lambda event: self.nextword(nostore=False))
    def set_up_transcription(self):
        pass
    def getword(self):
        p = self.lex_ui
        self.program.taskchooser.withdraw()# not sure why necessary
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
                log.info(_("self.entry doesn’t seem to be in entries; OK for now"))
            self.instructions['text']=self.getinstructions() #in case changed
            self.dowordframe()
        elif not self.entries:
            if getattr(self,'dodoneonly',False):
                # done-only tasks (e.g., Parse Already Collected Words): an
                # empty list means nothing has been collected yet — the
                # opposite of "all done".
                text=_("There are no already-collected words to work on "
                "here yet. \nCollect some words first (e.g., through an "
                "“Add Words” task), then come back to this task.")
            else:
                text=_("It looks like you’re done filling out the empty "
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
        # A5 in-place reload: remember where the user IS, so a reload
        # relaunch resumes here (consumed in getwords; see reload_database).
        self._record_anchor={'guid': getattr(self.entry,'guid',None)}
        glosses={}
        for g in set(self.glosslangs) & set(self.sense.glosses):
            glosses[g]=', '.join(self.sense.formattedgloss(g,quoted=True))
        self.glossesthere=' — '.join([glosses[i] for i in glosses if i])
        # log.info("glosses there: {}".format(self.glossesthere))
        if not self.glossesthere:
            log.info(_("entry {id} doesn’t have glosses; not showing.").format(id=self.entry.get('id')))
            self.dirfn(nostore=True)
        self.glossesline['text']=self.glossesthere
        self.glossesline.wrap()
        url=self.sense.illustrationURI()
        if hasattr(getattr(self.wordframe,'pic',None),'changeurl'):
            self.wordframe.pic.changeurl(url)
        else:
            self.wordframe.pic=p.image_frame(self.wordframe, url,
                                            pixels=300,
                                            show_none=True,
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
        self.ui.frame.grid_columnconfigure(1,weight=1)
        self.ui.deiconify()
        self.lift()
        self.wordframe.update_idletasks()
    def setcontext(self):
        super().setcontext()
        self.context.menuitem(_("Show Report"),self.show_report)
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.dodone=False
class Parse(Segments):
    """docstring for Parse."""
    invariablesegmentalroots=True #Not used; otherwise, ask, or else just check each
    do_not_show_slices=True
    show_parser_ui=True
    uses_second_forms=True
    no_leaderboard=True
    def getgloss(self,ftype=None):
        return ', '.join([', '.join(self.parser.sense.formattedgloss(l,
                                                            ftype=ftype,
                                                            quoted=True))
                        for l in self.glosslangs])
    def userconfirmation(self,*args):
        p = self.lex_ui
        log.info("asking for user confirmation")
        # Return True or False only
        def do(x):
            log.info("doing {}".format(x))
            if hasattr(x, 'get') and hasattr(x, 'set'):
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
            p.label(self.responseframe,
                        text=_("root:"),
                        row=0,column=3,padx=(10,0),sticky='ew')
            roottext = p.string_var(self.responseframe, value=lx)
            self.roottextfield=p.entry_field(self.responseframe,
                                                text=roottext,
                                                row=0,column=4,sticky='ew')
            p.button(self.responseframe,
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
                self.entry.plvalue(self.program.settings.pluralname, value=False)
            elif self.sense.psvalue() == self.verbalps:
                self.entry.fieldvalue(self.program.settings.imperativename,
                                            self.analang, value=False) #unset value
            self.program.db.write()
            log.info(self.currentformnotice())
            do(False)
        level, lx, lc, sf, ps, afxs = args
        if self.ui.exitFlag.istrue():
            return
        w=p.window(self,exit=False)
        w.title(_("Confirm this combination of affixes?"))
        self.userresponse.value=False
        self.userresponse.rootchange=False
        # gloss=self.getgloss()
        # text=_("Parse looks good ({level}):").format(level=self.parser.levels()[level])
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
        self.presentationframe=p.frame(w.frame,row=1,column=0,sticky='ew')
        self.lcframe=p.frame(self.presentationframe,
                                row=0,column=0,
                                padx=10,
                                sticky='ew')
        lcmorphs=list(afxs[0])
        lcmorphs.insert(1,lx)
        self.l=p.label(self.lcframe,
                text='-'.join([i for i in lcmorphs if i]),font='title',
                row=0,column=0)
        url=self.sense.illustrationURI()
        # citation (singular) side: single image; plural/imperative imagery
        # belongs only on the second-form side
        p.image_frame(self.lcframe, url,
                    row=1, column=0, sticky='')
        p.label(self.lcframe,
                text=glosslc,font='readbig',
                row=2,column=0)
        self.sfframe=p.frame(self.presentationframe,
                                row=0,column=1,
                                padx=10,
                                sticky='ew')
        sfmorphs=list(afxs[1])
        sfmorphs.insert(1,lx)
        p.label(self.sfframe,
                text='-'.join([i for i in sfmorphs if i]),font='title',
                row=0,column=1)
        url=self.sense.illustrationURI()
        p.image_frame(self.sfframe, url, ftype=ftype,
                    row=1, column=1, sticky='')
        p.label(self.sfframe,
                text=glosssf,font='readbig',
                row=2,column=1)
        self.responseframe=p.frame(w.frame,row=2,column=0,sticky='ew')
        p.button(self.responseframe,
                    text=_("Yes!"),
                    command=lambda x=True: do(x),
                    ipadx=10,
                    row=0,column=0,sticky='nsew')
        p.button(self.responseframe,
                    text=_("No!"),
                    command=lambda x=False: do(x),
                    ipadx=10,
                    row=0,column=1,sticky='nsew')
        self.correctframe=p.frame(self.responseframe,
                                    row=0,column=2,
                                    sticky='ew',padx=(10,0))
        p.button(self.correctframe,
                    text=_("wrong root!"),
                    command=enterroot,
                    row=0,column=0,sticky='ew')
        p.button(self.correctframe,
                    text=_("wrong {field}!").format(field=self.secondformfield[self.sense.psvalue()]),
                    command=undosf,
                    row=1,column=0,sticky='ew')
        self.noticeframe=p.frame(w.frame,row=3,column=0)
        t=_("This parse looks good ({level})\n").format(level=self.parser.levels()[level])
        p.label(self.noticeframe,text=t+self.currentformnotice(),
                    font='small',justify='l',
                    row=0,column=0)
        if self.ui.iswaiting():
            # log.info("Window almost built; unpausing")
            self.ui.waitpause()
        # log.info("exit flag for w({}):{}; self({}):{}"
        #         "".format(w,w.exitFlag,self,self.exitFlag))
        # log.info("Window built; waiting")
        w.wait_window(self.l) #canary on label, not window
        if w.exitFlag.istrue():
            # log.info("Exited parse! (self.userresponse.value:{})"
            #         "".format(self.userresponse.value))
            self.ui.waitdone()
            self.exited=True
        else:
            # log.info("Didn't exit parse! (self.userresponse.value:{})"
            #         "".format(self.userresponse.value))
            # w.on_quit()
            w.destroy()
            if self.ui.iswaiting():
                self.ui.waitunpause()
            if self.userresponse.rootchange:
                self.trythreeforms() #kick this back up a level
            else:
                # log.info("User responded {}".format(self.userresponse.value))
                return self.userresponse.value
    def selectsffromlist(self,l):
        p = self.lex_ui
        def formattuple(l):
            pfx,sfx=l[-1]
            root=l[2]
            return '-'.join([i for i in [pfx,root,sfx] if i])
        # log.info("Selecting from option list: {}".format(l))
        if self.ui.exitFlag.istrue():
            return
        if self.ui.iswaiting():
            self.ui.waitpause()
        cands={ps:[(i,formattuple(i)) for i in l if i[1] == ps
                        if len(i[-1]) == 2] #each must have (only) pfx and sfx
                for ps in [self.nominalps, self.verbalps]}
        other={self.nominalps:'ON', self.verbalps:'OV'}
        ftypes={self.nominalps:'pl', self.verbalps:'imp'}
        # One ps at a time: the ps with the most analytical possibilities
        # is offered first; ties (including no possibilities either way)
        # offer the noun first (stable sort keeps the list order).
        order=sorted([self.nominalps, self.verbalps],
                        key=lambda ps:-len(cands[ps]))
        for ps in order:
            if self.ui.exitFlag.istrue():
                break
            sfname=self.secondformfield[ps]
            w=p.window(self)
            w.title(_("Select second form"))
            t=p.label(w.frame,
                        text=_("What is the {sfname} of \n‘{lc}’ ({gloss})?"
                            "").format(
                            sfname=sfname,
                            lc=self.parser.entry.lcvalue(),
                            gloss=self.getgloss()
                                    ),
                        font='title',
                        row=0,column=0,columnspan=2)
            t.wrap()
            url=self.sense.illustrationURI()
            p.image_frame(w.frame, url, ftype=ftypes[ps],
                        row=1, column=0, sticky='')
            opts=cands[ps]+[(other[ps],
                        _("Other {field}").format(field=sfname))]
            p.scrolling_button_frame(w.frame, optionlist=opts, window=t,
                                        command=self.parser.dooneformparse,
                                        row=2, column=0)
            p.button(w.frame, text=_("Not a {ps}").format(ps=ps),
                            cmd=t.destroy, #decline: move on to the next ps
                            row=1, column=1, sticky='ns')
            p.label(w.frame,text=self.currentformnotice(),
                        font='small',justify='l',
                        row=3,column=0,columnspan=2)
            w.wait_window(t)
            if w.exitFlag.istrue():
                self.exited=True
            w.destroy()
            if self.exited or self.done() or self.parser.sense.psvalue():
                break #selected a parse, or an 'Other' (typed form follows)
        else: #declined every ps: count askparsed; evaluated and moving on
            self.parsecatalog.addneither(self.parser.sense.id)
            #don't leave 'neither' with ps indication
            self.parser.sense.rmpsnode()
            # self.parser.rmpssubclassnode() #leave this for posterity?
        if self.ui.iswaiting():
            self.ui.waitunpause()
    def asksegmentsnops(self):
        #no analytical possibilities to go on here: offer the noun first
        for ps in [self.nominalps, self.verbalps]:
            r=self.asksegments(ps=ps)
            if r is None or self.exited: #form given (or exited): done;
                break                    #r=1 (not this ps): ask the next ps
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
            return _("{root}: {forms} ({ps}), {sfname}: {forms2}"
                ).format(root=_("Root"),
                        forms=lx,
                        forms2=''.join([i for i in [pl,imp] if i]),
                        ps=self.parser.sense.psvalue(),
                        sfname=self.secondformfield[self.nominalps] if pl
                        else self.secondformfield[self.verbalps]
                        )
        if lc and (pl or imp):
            return _("Citation: {citation}, {sfname}: {forms}"
                ).format(citation=lc,
                        forms=''.join([i for i in [pl,imp] if i]),
                        # root=_("root"),
                        # ps=self.parser.sense.psvalue(),
                        sfname=self.secondformfield[self.nominalps] if pl
                        else self.secondformfield[self.verbalps]
                        )
        if lc:
            return _("Citation: {citation}").format(citation=lc)
        else:
            return ""
    def currentformnotice(self):
        lx, lc, pl, imp = self.parser.texts()
        return _("currently: ")+("{lx} ({ps} {root}), {lc}, {pl} ({pl_name}), {imp} ({imp_name})"
                ).format(lx=lx, lc=lc, pl=pl, imp=imp,
                        root=_("root"),
                        ps=self.parser.sense.psvalue(),
                        pl_name=self.secondformfield[self.nominalps],
                        imp_name=self.secondformfield[self.verbalps]
                        )
    def asksegments(self,ps=None):
        p = self.lex_ui
        def do(event=None):
            self.parser.sense.psvalue(ps)
            if ps == self.nominalps:
                # tag='pl'
                fn=self.parser.entry.plvalue
            elif ps == self.verbalps:
                # tag='imp'
                fn=self.parser.entry.impvalue
            fn(self.secondformfield[ps],segments.get())
            b.destroy()
        def next(event=None):
            segments.set("")
            b.destroy()
        if self.ui.exitFlag.istrue():
            return
        if not ps:
            return asksegmentsnops()
        log.info("asking for second form segments for '{}' ps: {} ({}; {})"
                "".format(self.parser.entry.lcvalue(),
                            ps,self.parser.sense.id,
                            self.parsecatalog.parsen()))
        sfname=self.secondformfield[ps]
        if self.ui.iswaiting():
            self.ui.waitpause()
        w=p.window(self)
        w.title(_("Type second form"))
        l=p.label(w.frame,
                text=_("What {sfname} form goes with ‘{lc}’ ({gloss})?"
                    "").format(sfname=sfname,
                            lc=self.parser.entry.lcvalue(),
                            gloss=self.getgloss()),
                font='title',
                row=0,column=0,columnspan=2)
        l.wrap()
        if ps == self.nominalps:
            ftype='pl'
        elif ps == self.verbalps:
            ftype='imp'
        url=self.parser.sense.illustrationURI()
        p.image_frame(w.frame, url, ftype=ftype, row=0, column=2)
        segments=p.string_var()
        segments.set(self.parser.entry.lcvalue())
        e=p.entry_field(w.frame,text=segments,
                        row=2,column=0)
        b=p.button(w.frame,text=_("OK"),cmd=do,
                        row=3,column=0, sticky='e')
        p.button(w.frame,text=_("Not a {ps}").format(ps=ps),cmd=next,
                        row=3,column=1, sticky='e')
        p.label(w.frame,text=self.currentformnotice(),
                    font='small',justify='l',
                    row=4,column=0,columnspan=2)
        e.focus_set()
        e.bind('<Return>',do)
        w.wait_window(b)
        if w.exitFlag.istrue():
            self.exited=True
        if self.ui.iswaiting():
            self.ui.waitunpause()
        segments_ok=bool(segments.get())
        w.destroy()
        if not segments_ok:
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
            log.info("Confirmed parsing of '{}' root from '{}' and '{}' as {}"
                        "".format(*r[1:5]))
            log.info("adding {} affix set {}".format(*r[4:]))
            self.parser.addaffixset(*r[4:])#self.ps,afxs)
            self.parser.sense.pssubclassvalue(r[-1])
            return
        else:
            log.info(f"No parse (trythreeforms).")
        log.info(f"{self.exited=}")
        log.info(f"{self.done()=}")
        log.info(f"{self.userresponse.rootchange=}")
        if (not self.exited and
            not self.done() and
            # rootchange kicks back, so just finish here on rootchange:
            not self.userresponse.rootchange):
            self.trytwoforms()
        log.info("Finished trying three forms")
    def fixroot(self,root):
        log.info("Fixing Root {} > {}".format(
                            self.parser.entry.lxvalue(),
                            root))
        self.parser.entry.lxvalue(root) #setting
        self.updateparseUI()
    def parse_foreground(self,**kwargs):
        self.ui.withdraw()
        self.updatereturnbind()
        self.userresponse.rootchange=False #reset for each root
        self.parse(**kwargs)
        self.updateparseUI()
        if self.ui.iswaiting():
            self.ui.waitdone()
        if self.winfo_exists():
            self.ui.deiconify()
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
        except Exception as e: #upgrade to this
            log.error("Exception submitting parse (do I need access to entry "
                        "for entry.sense.id?): {}".format(e))
            raise e
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
            senses=self.program.db.senses[:n]
        if all:
            return senses #if provided, assume all
        else:
            try:
                return set(senses)-set(self.parsecatalog.parsed)
            except AttributeError:
                return set(senses)
    def getparses(self,**kwargs):
        """Generator: parses senses, yields 0-100 progress."""
        log.info("parses already tried: {}".format(self.parsecatalog.parsen()))
        senses=self.sensestoparse(**kwargs)
        todo=len(senses)
        for n,self.sense in enumerate(senses):
            self.parse() #this can add to lists
            if self.exited:
                break
            yield n * 100 // max(todo,1)
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
        # like if there is a bad affix making bad autoparses...
        self.pss=self.program.db.pss
        self.program.parsecatalog=parser.Catalog(self)
        collector=parser.AffixCollector(self.program.parsecatalog,
                                        self.program.db)
        if self.loadfromlift:
            with self.ui.waiting(_("Loading Affixes")):
                # for i in collector.do():
                for i in collector.getfromlift():
                    # log.info("Progress: {}".format(i))
                    self.waitprogress(i)
                self.program.parsecatalog.report()
    def showwhenready(self):
        try:
            assert self.status.winfo_exists()
            log.info("self.status found; showing parser UI")
            self.ui.deiconify()
        except Exception:
            self.ready_waits=getattr(self,'ready_waits',0)+1
            if self.ready_waits < self.try_times:
                log.info("self.status not found; waiting 100ms before showing parser UI")
                self.after(self.try_each_ms,self.showwhenready)
            else:
                log.error("self.status not found after {} tries @ {}ms; giving up"
                        "".format(self.try_times,self.try_each_ms))
    def storethisword(self):
        log.info(_("Parse trying to store {value} ({type})").format(value=self.var.get(),type=self.ftype))
        try:
            v=self.var.get()
            assert v
            self.entry.fields[self.ftype].textvaluebylang(self.analang,v)
            if not self.done():
                self.parse_foreground(entry=self.entry)
            self.maybewrite() #only if above is successful
            self.updateparseUI()
            log.info(f"Storing word: {self.sense.id} ({self.analang}:{v})")
        except AssertionError as e:
            log.info(f"Not storing empty value (Parse): {e} {self.var=} "
                    f"{type(self.var)=}")
        except AttributeError as e:
            log.info(f"Not storing word (Parse): {e}")
        except Exception as e:
            log.info(f"Exception storing word (Parse): {e}")
    def waitforOKsecondfields(self):
        while not self.program.settings.secondformfieldsOK():
            after(10*100,callback=self.waitforOKsecondfields) # wait a second
    def __init__(self, **kwargs): #frame, filename=None
        self.byslice=False
        self.initsensetodo()
        super().__init__(**kwargs)
        self.secondformfield=self.program.settings.secondformfield
        self.nominalps=self.program.settings.nominalps
        self.verbalps=self.program.settings.verbalps
        self.loadfromlift=True
        # self.program.settings.makesecondformfieldsOK() #do elsewhere
        if not hasattr(self.program,'parsecatalog'):
            self.initparsecatalog()
        self.parsecatalog=self.program.parsecatalog
        # else:
        if not hasattr(self.program,'parser'):
            self.program.parser=parser.Engine(self.parsecatalog,self)
        #     self.parser=self.program.parser
        # else:
        #     self.parser=
        self.parser=self.program.parser
            #These should come from settings
        self.parser.autolevel(5) #no auto
        self.parser.asklevel(0)
        self.ftype=self.program.params.ftype('lc') #Is this always correct?
        # self.ftype=self.program.params.ftype('lx') #I think once we parse, we want this
        # self.nodetag='citation'
        # dodone/dodoneonly are deliberately NOT set here: the Add-and-Parse
        # collection variants must present the SAME full wordlist as the plain
        # collection tasks (Segments defaults: all entries, in db order).
        # Setting dodoneonly=True here made a fresh project's Add-and-Parse
        # list EMPTY (0 collected words) and falsely congratulate "all done".
        # Tasks that really want only-already-collected words (WordsParse,
        # ParseSlice) set dodoneonly=True in their own __init__.
        self.checkeach=False #don't confirm each word (default)
        self.userresponse=Object(rootchange=False,value=False)
        p = self.lex_ui
        self.cparsetext=p.string_var() #store UI parse info here
        self.try_each_ms=100
        self.try_times=100
        self.showwhenready()
class Tone(Senses):
    """This keeps stuff used for Tone checks."""
    """This may want to depend on a new class Examples, since it's
    examples that have tone values, not senses."""
    """Is this a valid and consistent distinction, or should those 
    methods just show here? if there is a 1:1 relationship
    Segments:Senses
    Tone:examples
    then they should be collapsed.
    """
    def makeanalysis(self,**kwargs):
        """was, now iterable, for multiple reports at a time:"""
        if not hasattr(self,'analysis'):
            self.analysis=Analysis(self.program, **kwargs)
        else:
            self.analysis.setslice(**kwargs)
    def checkforsensestosort(self,cvt=None,ps=None,profile=None,check=None):
        """This method just asks if any sense in the given slice is unsorted.
        It stops when it finds the first one."""
        """use if sorting sense lists aren't needed"""
        """This is redundant with updatesortingstatus()"""
        if cvt is None:
            cvt=self.program.slices.cvt()
        if ps is None:
            ps=self.program.slices.ps()
        if profile is None:
            profile=self.program.slices.profile()
        if check is None:
            check=self.program.slices.check()
        senses=self.program.slices.senses(ps=ps,profile=profile)
        vts=False
        for sense in senses:
            if sense.tonevaluebyframe(self,frame):
                vts=True
                break #This is just a True/False for the group, not lists
        self.program.status.dictcheck(cvt=cvt,ps=ps,profile=profile,check=check)
        self.program.status.tosort(vts,cvt=cvt,ps=ps,profile=profile,check=check)
    def settonevariablesiterable(self,cvt='T',ps=None,profile=None,check=None):
        """This is currently called in iteration, but doesn't refresh groups,
        so it probably isn't useful anymore."""
        self.checkforsensestosort(cvt=cvt,ps=ps,profile=profile,check=check)
    def settonevariables(self):
        """This is currently called before sorting. This is a waste, if you're
        not going to sort afterwards –unless you need the groups."""
        self.updatesortingstatus() #this gets groups, too
    def addframe(self,**kwargs):
        from tasks.tasks import ToneFrameDrafter #local: backend can't import tasks at module level
        if 'window' in kwargs:
            kwargs['window'].destroy() #in any case; if fails, try again.
        self.ui.withdraw()
        t=ToneFrameDrafter(self)
        if not t.exitFlag.istrue():
            self.ui.wait_window(t)
    def aframe(self):
        self.ui.runwindow.on_quit()
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
                                self.program.toneframes[ps][check])
            # log.info("Setting form to {}".format(f))
            item.examples[check].textvaluebylang(
                                    lang=self.analang,
                                    value=f)
            log.info("Setting tone sort group to '{}'".format(group))
            item.examples[check].tonevalue(group)
            for g in (set(self.glosslangs)& #selected
                        set(self.program.toneframes[ps][check])& #defined
                        set(item.ftypes[self.ftype])): # form in lexicon
                for f in item.formattedgloss(g,
                                        self.program.toneframes[ps][check])[:1]:
                    # log.info("Setting {} translation to {}".format(g,f))
                    item.examples[check].translationvalue(g,f)
            item.examples[check].lastAZTsort()
        except (KeyError,AssertionError) as e:
            # log.info(f"Adding a new example to store '{check}' values ({e})")
            item.newexample(check,
                            self.program.toneframes[ps][check],
                            self.analang,
                            self.glosslangs,
                            group)
        # log.info("Done setting tone sort group")
    def getsensesinUFgroup(self,group):
        return [
                i for i in self.program.db.senses
                if i.uftonevalue() == group
                ]
    def getsensesingroup(self,check,group):
        return [
                i for i in self.program.db.senses
                if i.tonevaluebyframe(check) == str(group) #str: see Segments variant
                ]
    def getitemgroup(self,item,check):
        """This works without ftype, as each frame only has one"""
        return item.tonevaluebyframe(check)
    def getUFgroupofsense(self,sense):
        return sense.uftonevalue()
    def name_new_glyphs(self):
        pass
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # if program is not None:
        #     self.program=program
class Syllables(Senses):
    """Cyclical syllable sort (see docs/sort_syllables_design.md). FOUR checks:
    three primitive sorts on the WHOLE wordlist — '#C' (word-initial C/V),
    'C#' (word-final C/V), 'syls' (syllable count) — whose outcomes compose into
    a Beg+count+End **profile class** (the 'S' slice, DERIVED from the three
    primitives — not a sorted group-of-groups); then the whole-word profile sort
    for the current word-form (the ftype: lc/lx/pl/imp) WITHIN each profile class.
    All four live on the annotation channel (like segments); the
    surface form is never rewritten. Used before Segments in the MRO so these
    overrides win while Segments supplies shared helpers.

    Primitives are seeded by orthography from the computed profile (the user then
    judges by ear). The profile annotation is named by the ftype; the three
    primitives by their check code."""
    def updateformtoannotations(self,*args,**kwargs):
        pass  # never rewrite the surface form
    def name_new_glyphs(self):
        pass  # no glyph phase
    # --- annotation channel (mirrors Segments; kept here so the 'S' routing in
    #     updatesortingstatus/getexamples stays pointed at Syllables) ---
    def getitemgroup(self,item,check):
        return item.annotationvaluebyftypelang(self.ftype,self.analang,check)
    def setitemgroup(self,item,check,group,**kwargs):
        item.annotationvaluebyftypelang(self.ftype,self.analang,check,group)
    def getsensesingroup(self,check,group):
        return [i for i in self.program.db.senses
                if i.annotationvaluebyftypelang(self.ftype,self.analang,check)
                    ==str(group)] #str: see Segments variant
    # --- the three primitives: canonical impl is on params (also reached off-task
    #     by the board-render rebuild); these delegate so existing self._word_*/
    #     _syllable_count callers (presortgroups, etc.) stay unchanged ---
    def _word_initial(self,profile):
        return self.program.params.word_initial(profile)
    def _word_final(self,profile):
        return self.program.params.word_final(profile)
    def _syllable_count(self,profile):
        return self.program.params.syllable_count(profile)
    def profile_class(self,sense,**kwargs):
        """The 'S' slice = Beg+count+End profile class, composed on the fly from
        the three primitive annotations. Delegates to params (the single source of
        the profile-class format). Returns e.g. 'C2V', or None if not all set."""
        return self.program.params.profile_class_of_sense(sense,ftype=self.ftype)
    def presortgroups(self,**kwargs):
        """Seed each word's four attributes by orthography so the obvious
        bucketing is pre-done; the user then verifies each (by ear) and fixes
        strays via the escape hatch. Idempotent: only FILLS attributes that are
        missing (a word with no word-initial annotation yet is unbucketed), so
        confirmed/corrected values are preserved and re-running just fills gaps —
        no early-return guard, which lets a word a prior presort skipped (e.g.
        an un-analyzable form) get bucketed on the next run. Generator 0–100."""
        ftype=self.program.params.ftype()
        analang=self.analang
        # PREP is wordlist-wide: the three primitives (#C/C#/syls) are
        # ps-INDEPENDENT form facts, so seed EVERY word, not just the current ps.
        # ps re-enters only downstream as the (profile × ps) segmental slice.
        senses=self.program.db.senses
        n=max(len(senses),1)
        # Per-sense seeding is the shared params.seed_sense_primitives rule (also
        # run at LIFT load), so the two paths can't drift. Tally what it did.
        tally={'seeded':0,'defaulted':0,'syls':0}
        for i,sense in enumerate(senses):
            tag=self.program.params.seed_sense_primitives(sense,ftype,analang)
            if tag in tally:
                tally[tag]+=1
            yield i*100//n
        log.info("Presort (wordlist-wide): total=%d seeded=%d defaulted→#C=C=%d "
                "syls-backfilled=%d", n, tally['seeded'], tally['defaulted'],
                tally['syls'])
        if tally['syls']:
            log.info("Presort: backfilled syls for %d already-bucketed word(s) "
                    "that had #C/C# but no syllable count — they re-enter the "
                    "syls check.", tally['syls'])
        if tally['defaulted']:
            log.info(_("{n} word(s) couldn’t be auto-analyzed; defaulted "
                    "word-initial AND word-final to consonant. Review the "
                    "consonant groups for outliers.").format(n=tally['defaulted']))
        self.program.status.presorted(True)
        self.program.status.store()
        self.maybewrite()
        yield 100
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

