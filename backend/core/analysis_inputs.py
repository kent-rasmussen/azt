# coding=UTF-8
from utilities.i18n import _
from utilities import logsetup
log=logsetup.getlog(__name__)

import sys
import collections
# import re
# import datetime
# import tkinter as tk
from utilities.utilities import *
from utilities import file, htmlfns
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

from utilities.error_handler import notify_error as ErrorNotice

from backend.core.lexicon import Tone

class Glosslangs(list):
    """docstring for Glosslangs."""
    def sanitycheck(self):
        """First, remove any duplicates."""
        self.langs(list(set(self)))
        if None in self.langs():
            self.rm(None)
        if len(self) > 2:
            self=self[:2]
            return
        if len(self) < 1:
            ErrorNotice(_("Hey, you have no gloss languages set!"))
    def lang1(self,lang=False):
        if self and lang is False: #i.e., not specified
            return self[0]
        if self:
            self[0]=lang #before others
        else:
            self.append(lang)
        self.sanitycheck()
    def lang2(self,lang=None):
        if len(self) >1:
            if not lang:
                return self[1]
            elif self[0] != lang:
                self[1]=lang
        elif len(self) == 1:
            self.append(lang)
        else:
            log.debug("Tried to set second glosslang, without first set.")
        self.sanitycheck()
    def langs(self,langs=None):
        if langs is None:
            return self
        else:
            n=min(len(langs),2)
            for i in [0,1]:
                if i < len(langs):
                    self[i]=langs[i]
                elif i < len(self):
                    self.pop(i)
    def rm(self,lang):
        """This could be either position, and if lang1 will promote lang2"""
        self.remove(lang)
    def __init__(self, langlist=None):
        super(Glosslangs, self).__init__()
        if langlist:
            self.extend(langlist)

class ToneFrames(dict):
    def addframe(self,ps,name,defn):
        """This needs to change checks"""
        if not isinstance(defn,dict):
            log.error(_("The supplied frame definition isn't a dictionary: {defn}"
                        "").format(defn=defn))
        elif name in self:
            log.error(_("The supplied frame name is already there: {name} ({defn})"
                        "").format(name=name,defn=defn))
        else:
            if not ps in self:
                self[ps]={}
            self[ps][name]=defn
    def store(self):
        log.info(_("Saving toneframes dict to file"))
        self.program.settings.storesettingsfile('toneframes')
    #def write
    def source(self,dict=None):
        if dict:
            updated=False
            for ps in dict:
                self[ps]=dict[ps]
                for name in self[ps]:
                    try:
                        if 'field' not in self[ps][name]:
                            updated=True
                            self[ps][name]['field']='lc'
                    except TypeError as e:
                        log.info(_("problem with frame at ps:{ps}, name:{name} ({error})"
                                "").format(ps=ps,name=name,error=e))
            if updated:
                log.info(_("updated toneframes for field; you should save it!"))
        return self
    def __init__(self, program, dict=None):
        self.program=program
        self.program.toneframes=self
        super(ToneFrames, self).__init__()
        self.source(dict)

class CheckParameters(object):
    """This stores and returns current cvt/type and check only; there is not check
    here that the setting is valid (done in status), nor that the consequences
    of the change are done (done in check)."""
    """None of this is language/project dependent, nor with mutable options"""
    def verify(self):
        t=self.cvt()
        if t not in self._cvts:
            self.cvt(self.cvts()[0])
        """The following are not (yet?) renewed here"""
        check=self.check()
        if check not in self.checks():
            self.check(self.checks()[0])
        group=self.group()
        if check not in self.groups():
            self.group(self.groups()[0])
    def cvt(self,cvt=None):
        """This needs to change checks"""
        if cvt is not None:
            self._cvt=cvt
        elif not hasattr(self,'_cvt'):
            self._cvt=None
        return self._cvt
    def cvts(self):
        """This depends on nothing, so can go anywhere, and shouldn't need to
        rerun. This is a convenience wrapper only."""
        return list(self._cvts)
    def cvtdict(self):
        """This depends on nothing, so can go anywhere, and shouldn't need to
        rerun. This is a convenience wrapper only."""
        return self._cvts
    def cvtname(self,cvt=None,n='sg'):
        if not cvt:
            cvt=self.cvt() #this shouldn't necessarily set current cvt.
        return self._cvts[cvt][n]
    # --- syllable PROFILE-CLASS helpers (the cvt='S' slice = Beg+count+End,
    #     DERIVED by composing the three confirmed primitives — NOT a sorted
    #     group-of-groups; contrast the segmental macrogroup/glyph) ---
    SYLLABLE_SLICE_SENTINEL='whole-word' #profile dim while doing the 3 primitives
    SYLLABLE_PREP_PS='*' #ps dim sentinel: PREP is wordlist-wide. The three
                #primitives (#C/C#/syls) are ps-INDEPENDENT form facts, so their
                #slices and verify state live under one shared ps key, not per-ps.
                #ps re-enters only downstream as the (profile × ps) segmental slice.
    def compose_profile_class(self,beg,syls,end):
        # e.g. 'C2V'. beg/end are single 'C'/'V'; syls is the (possibly multi-
        # digit) count — so no delimiter is needed and parse is positional.
        return '{}{}{}'.format(beg,syls,end)
    def parse_profile_class(self,key):
        # Inverse of compose: first char = beg, last char = end, middle = syls.
        key=str(key)
        if len(key)>=3 and key[0] in 'CV' and key[-1] in 'CV' and key[1:-1].isdigit():
            return (key[0],key[1:-1],key[-1])
        return (None,None,None)  # sentinel / not a profile class
    def profile_class_of_sense(self,sense,ftype=None):
        """Compose a sense's Beg+count+End profile class from its three primitive
        annotations (#C / syls / C#). None until all three are set."""
        ftype=ftype or self.ftype()
        analang=self.program.db.analang
        beg=sense.annotationvaluebyftypelang(ftype,analang,'#C')
        syls=sense.annotationvaluebyftypelang(ftype,analang,'syls')
        end=sense.annotationvaluebyftypelang(ftype,analang,'C#')
        if not (beg and syls and end):
            return None
        return self.compose_profile_class(beg,syls,end)
    def profile_fits_class(self,profile,beg,syls,end):
        """Is `profile` (a CV string) consistent with a class's primitives? Uses
        the SAME derivations that define the primitives (word_initial/final,
        syllable_count), so 'legal' here means exactly 'would seed to this class'.
        Handles richer symbols (G, digraphs, '=') the way the primitives do
        (anything non-vowel is consonantal)."""
        if not profile:
            return False
        try:
            n=int(syls)
        except (TypeError,ValueError):
            return False
        return (self.word_initial(profile)==beg
                and self.word_final(profile)==end
                and self.syllable_count(profile)==n)
    def _distribute_extra(self,total,k,cap):
        """Yield length-k tuples (each 0..cap) summing to `total` — the 'extra'
        length added to each slot beyond its baseline 1. Used to enumerate profile
        candidates by increasing total length (simplest first)."""
        if k==0:
            if total==0:
                yield ()
            return
        for first in range(0,min(cap,total)+1):
            if total-first<=cap*(k-1):
                for rest in self._distribute_extra(total-first,k-1,cap):
                    yield (first,)+rest
    def legal_profiles_for_class(self,beg,syls,end,exclude=(),limit=12,percap=2):
        """Propose NEW legal CV profiles for a (beg,syls,end) profile class,
        SIMPLEST-FIRST (all-length-1 baseline, then minimal doublings), skipping
        any in `exclude` (already-sorted profiles), stopping at `limit`. Anything
        rarer is set by hand on the free-entry page. `percap` = max extra length
        per slot (so each C-cluster / V-run is 1..1+percap long; default 1–3). The
        class skeleton = one C-cluster before the 1st V iff beg=C, one between each
        adjacent V-run pair (syls-1 interludes), one after the last V iff end=C.
        See ADR 0003 / cv_group_creation_merging."""
        try:
            N=int(syls)
        except (TypeError,ValueError):
            return []
        if N<1 or beg not in ('C','V') or end not in ('C','V'):
            return []
        slots=[]
        if beg=='C':
            slots.append('C')
        for i in range(N):
            slots.append('V')
            if i<N-1:
                slots.append('C')  # interlude between this V-run and the next
        if end=='C':
            slots.append('C')
        k=len(slots)
        exclude=set(exclude)
        out=[]; seen=set(); extra=0
        while extra<=percap*k and len(out)<limit:
            for dist in self._distribute_extra(extra,k,percap):
                prof=''.join(slots[i]*(1+dist[i]) for i in range(k))
                if prof in seen:
                    continue
                seen.add(prof)
                if prof in exclude:
                    continue
                out.append(prof)
                if len(out)>=limit:
                    break
            extra+=1
        return out
    def unused_profiles_for_class(self,beg,syls,end,limit=12):
        """legal_profiles_for_class MINUS the profiles already sorted into this
        class (its status node 'groups') — i.e. the pickable NEW options. Kept
        separate from legal_profiles_for_class so that stays a pure example
        generator (callers that 'just want an example' don't pay the exclusion)."""
        cls=self.compose_profile_class(beg,syls,end)
        try:
            node=self.program.status.node(cvt='S',ps=self.program.slices.ps(),
                                          profile=cls,check=self.ftype())
            inuse=set(node.get('groups',[]))
        except Exception:
            inuse=set()
        return self.legal_profiles_for_class(beg,syls,end,exclude=inuse,limit=limit)
    # --- the three primitives, derived by orthography from a profile string.
    # Canonical home (they used to live on the Syllables task mixin) so they can
    # be reached OFF the live task — e.g. assign_slices' orthographic placement on
    # the board-render rebuild, where program.task may not be a syllable task.
    # Pure functions of the profile string.
    VOWEL_SYMS=('V','Ṽ') #vowel symbols in a computed profile string
    def word_initial(self,profile):
        return 'V' if profile and profile[0] in self.VOWEL_SYMS else 'C'
    def word_final(self,profile):
        return 'V' if profile and profile[-1] in self.VOWEL_SYMS else 'C'
    def syllable_count(self,profile):
        # number of maximal vowel-runs (vowel-sequences separated by consonants)
        n=0; inrun=False
        for ch in (profile or ''):
            v=ch in self.VOWEL_SYMS
            if v and not inrun:
                n+=1
            inrun=v
        return max(n,1)  # every word is at least one syllable (0 is nonsense)
    def seed_sense_primitives(self,sense,ftype,analang):
        """Seed a sense's #C/C#/syls primitive annotations (and the profile
        annotation) from its CV profile, IDEMPOTENTLY — the single seeding rule
        shared by the load-time pass and the prep-task presort, so they can't
        drift. Prefers the confirmed profile, falling back to the machine analysis
        (so a word whose plain profile hasn't synced yet, e.g. 'always', is still
        analyzable). Returns a tag for the caller's counters:
          'seeded'    — first bucketing from a valid profile (all three set)
          'defaulted' — un-analyzable → #C=C/#C#=C, syls intentionally left unset
          'syls'      — backfilled a missing syls on an already-bucketed, now-
                        analyzable word (the bug that stranded words like 'always')
          None        — already complete / nothing to do."""
        av=sense.annotationvaluebyftypelang
        if av(ftype,analang,'syls')=='0':       # normalise a nonsensical 0
            av(ftype,analang,'syls','1')
        profile=sense.cvprofilevalue(ftype) or sense.cvprofilemachinevalue(ftype)
        valid=bool(profile) and profile!='Invalid'
        if not av(ftype,analang,'#C'):          # not yet bucketed
            if valid:
                av(ftype,analang,'#C',self.word_initial(profile))
                av(ftype,analang,'C#',self.word_final(profile))
                av(ftype,analang,'syls',str(self.syllable_count(profile)))
                av(ftype,analang,ftype,profile)
                return 'seeded'
            # Un-analyzable (capitalised, multi-word, out-of-alphabet …): the
            # word-initial/final checks are CLOSED binaries with no sort page, so
            # default both to consonant to bucket the word; leave syls unset.
            av(ftype,analang,'#C','C'); av(ftype,analang,'C#','C')
            return 'defaulted'
        if not av(ftype,analang,'syls') and valid: # backfill a missing syls
            av(ftype,analang,'syls',str(self.syllable_count(profile)))
            if not av(ftype,analang,ftype):
                av(ftype,analang,ftype,profile)
            return 'syls'
        return None
    # --- reconciling a machine CV profile with the user's CONFIRMED primitives.
    # A machine analysis can contradict what the user verified — e.g. 'CVCV' for a
    # word confirmed C_1_C. constrain_profile reconciles it SYLLABLES-FIRST, then
    # edges, so we never "fix" an edge by deleting a syllable's vowel:
    #   1. Syllable count. A profile's count is ambiguous between its vowel-
    #      SEQUENCE count (VV=1, a diphthong) and its INDIVIDUAL-vowel count (VV=2,
    #      hiatus). If the confirmed `syls` lies in [sequences .. individuals] the
    #      profile is already consistent — leave the vowels alone. Otherwise adjust
    #      vowel runs — REMOVING a run (when over) or ADDING one (when under) —
    #      preferring an edge run whose removal OR addition also satisfies that
    #      edge's C/V constraint (one move, two fixes).
    #   2. Edges. Add/remove CONSONANTS only so the first segment matches #C and the
    #      last matches C#. We never delete a syllable's vowel just to fix an edge —
    #      vowels change ONLY in step 1, and only to reconcile the count.
    #   3. Fallback. If still inconsistent, emit the canonical 'CV' per syllable
    #      (+ final C if C#=C, − initial C if #C=V) — guaranteed consistent, flagged
    #      so the caller logs it.
    # Returns a dict {profile, changed, fallback, valid}; the caller logs (deduped).
    # See docs/sort_syllables_design.md.
    SEGMENT_BASES=set('NGSDCVʔ')|{'Ṽ'} # base segment chars; everything else (length
                                        # ː, tone, '.', '=', '<', combining marks)
                                        # is a MODIFIER that rides the prior segment
    PROFILE_CONSTRAINT={
        'enabled':True,    # master switch for the whole reconciliation
        'force_resort':False, # TESTING ONLY. Normally the constrained profile is
                          # written to the presort/data form only while it's still
                          # UNCONFIRMED; this also overwrites an already-(pre)sorted
                          # profile, so you can SEE the constraint act on existing
                          # data. It CLOBBERS confirmed sort results — never leave
                          # it on for real work, and don't save over good data.
    }
    def _profile_segments(self,profile):
        """Split a profile into segments: a base char (consonant/vowel class) plus
        any following MODIFIER chars — so 'Vː' is ONE segment, not two."""
        segs=[]
        for ch in (profile or ''):
            if ch in self.SEGMENT_BASES or not segs:
                segs.append(ch)
            else:
                segs[-1]+=ch # modifier attaches to the preceding segment
        return segs
    def _segment_type(self,seg):
        """'V' if a segment carries a vowel-class char, else 'C'."""
        return 'V' if any(c in self.VOWEL_SYMS for c in seg) else 'C'
    def _vowel_runs(self,segs):
        """(start, stop) index ranges of each maximal vowel-segment run."""
        runs=[]; i=0; n=len(segs)
        while i<n:
            if self._segment_type(segs[i])=='V':
                j=i
                while j<n and self._segment_type(segs[j])=='V':
                    j+=1
                runs.append((i,j)); i=j
            else:
                i+=1
        return runs
    def profile_vowel_runs(self,profile):
        """Vowel-SEQUENCE count of a profile (VV = one). The LOW end of a profile's
        ambiguous syllable count; the high end is its individual-vowel count."""
        return len(self._vowel_runs(self._profile_segments(profile)))
    def _individual_vowels(self,segs):
        return sum(1 for s in segs if self._segment_type(s)=='V')
    def profile_satisfies(self,profile,beg=None,end=None,syls=None):
        """True iff `profile` is consistent with the confirmed primitives: first
        segment is beg's type, last is end's type, and `syls` lies in the profile's
        ambiguity range [vowel-sequences .. individual-vowels]."""
        segs=self._profile_segments(profile)
        if not segs:
            return False
        if beg and self._segment_type(segs[0])!=beg:
            return False
        if end and self._segment_type(segs[-1])!=end:
            return False
        if syls is not None:
            try:
                target=int(syls)
            except (TypeError,ValueError):
                target=None
            if target is not None and not (len(self._vowel_runs(segs))
                                            <=target<=self._individual_vowels(segs)):
                return False
        return True
    def _default_profile(self,beg=None,end=None,syls=None):
        """The guaranteed-consistent fallback: 'CV' per syllable, + final C if
        C#=C, − initial C if #C=V."""
        try:
            s=max(int(syls),1)
        except (TypeError,ValueError):
            s=1
        p='CV'*s
        if end=='C':
            p+='C'
        if beg=='V':
            p=p[1:]
        return p
    def _reduce_vowel_runs(self,segs,target,beg,end):
        """Drop vowel runs until there are `target` of them, preferring an edge run
        whose removal ALSO satisfies that edge's C constraint (two fixes), else the
        trailing run."""
        runs=self._vowel_runs(segs)
        while len(runs)>max(target,0):
            if beg=='C' and runs[0][0]==0:            # leading vowel run; #C wants C
                a,b=runs[0]
            elif end=='C' and runs[-1][1]==len(segs): # trailing vowel run; C# wants C
                a,b=runs[-1]
            else:                                     # otherwise trim from the end
                a,b=runs[-1]
            segs=segs[:a]+segs[b:]
            runs=self._vowel_runs(segs)
        return segs
    def _add_vowel_runs(self,segs,target,beg,end):
        """Add isolated vowels until there are `target` runs, but ONLY at an edge
        that wants a vowel and lacks one (two fixes: +1 syllable AND the V edge).
        Interior insertion is unknowable, so any shortfall is left for the fallback."""
        if beg=='V' and (not segs or self._segment_type(segs[0])=='C') \
                and len(self._vowel_runs(segs))<target:
            segs=['V']+segs
        if end=='V' and (not segs or self._segment_type(segs[-1])=='C') \
                and len(self._vowel_runs(segs))<target:
            segs=segs+['V']
        return segs
    def constrain_profile(self,profile,beg=None,end=None,syls=None,cfg=None):
        """Reconcile a machine profile with the confirmed primitives — syllables
        first, then edges (see the block comment above). Returns a dict
        {profile, changed, fallback, valid}; primitives given as None are not
        constrained."""
        cfg=cfg or self.PROFILE_CONSTRAINT
        if not cfg.get('enabled') or not profile or profile=='Invalid':
            return {'profile':profile,'changed':False,'fallback':False,'valid':True}
        orig=profile
        try:
            target=int(syls)
        except (TypeError,ValueError):
            target=None
        segs=self._profile_segments(profile)
        # 1. SYLLABLES — only when `syls` is outside the profile's ambiguity range.
        if target is not None:
            seqs=len(self._vowel_runs(segs)); indiv=self._individual_vowels(segs)
            if target<seqs:               # too many vowel sequences → remove
                segs=self._reduce_vowel_runs(segs,target,beg,end)
            elif target>indiv:            # too few vowels → add (edge-aware only)
                segs=self._add_vowel_runs(segs,target,beg,end)
        # 2. EDGES — consonants only; never touch the (now-correct) vowels.
        if beg=='C' and segs and self._segment_type(segs[0])=='V':
            segs=['C']+segs
        elif beg=='V':
            while segs and self._segment_type(segs[0])=='C':
                segs.pop(0)
        if end=='C' and segs and self._segment_type(segs[-1])=='V':
            segs=segs+['C']
        elif end=='V':
            while segs and self._segment_type(segs[-1])=='C':
                segs.pop()
        new=''.join(segs)
        # 3. FALLBACK if reconciliation didn't land a consistent profile.
        fallback=False
        if not self.profile_satisfies(new,beg,end,target):
            new=self._default_profile(beg,end,target); fallback=True
        valid=self.profile_satisfies(new,beg,end,target)
        return {'profile':new,'changed':new!=orig,'fallback':fallback,'valid':valid}
    def is_syllable_primitive_check(self,check=None):
        # the three sorts that establish the profile class (run on the whole
        # wordlist); none of them join.
        return (check or self.check()) in ('#C','C#','syls')
    def is_syllable_boolean_check(self,check=None):
        # the CLOSED binary checks: no new-group ("Other"), no sort page (the
        # presort defaults every word). syls is NOT here — it's a small but OPEN
        # class (users may create new counts), so it keeps a sort page.
        return (check or self.check()) in ('#C','C#')
    def is_word_final_check(self,check=None):
        # a check about the END of the word — its verify list reads more
        # naturally sorted from the end of the word (the 'C#' primitive).
        return (check or self.check())=='C#'
    def syllable_prep_complete(self,ps=None):
        """Task 1 (syllable PREP) is done when EVERY slice of all three primitive
        checks (#C/C#/syls) is verified. PREP is wordlist-wide, so the verify state
        lives under the SYLLABLE_PREP_PS sentinel (not the passed ps, which is
        ignored — kept only for caller compatibility). The per-(group,slice) state
        is synthetic group ids in the sentinel-profile status node (see
        SyllableSliceDict). This one predicate gates the Task-1 board, the Task-2
        board, and SortSyllables.runcheck — single source of truth."""
        status=self.program.status
        for chk in ('#C','C#','syls'):
            try:
                n=status.node(cvt='S',ps=self.SYLLABLE_PREP_PS,
                              profile=self.SYLLABLE_SLICE_SENTINEL,check=chk)
            except Exception:
                return False
            g=set(n.get('groups',[])); d=set(n.get('done',[]))
            if not g or not (g<=d):
                return False
        return True
    # --- profile class → prose (the configurable renderer; tune to user feedback) ---
    def profile_class_begend_name(self,beg,end):
        w={'C':_("consonant"),'V':_("vowel")}
        return _("{beg}-initial, {end}-final").format(
                            beg=w.get(beg,beg),end=w.get(end,end))
    def profile_class_initial_name(self,beg):
        return {'C':_("consonant initial"),'V':_("vowel initial")}.get(beg,beg)
    def profile_class_final_name(self,end):
        return {'C':_("consonant final"),'V':_("vowel final")}.get(end,end)
    def syllable_group_name(self,check,group):
        """Human name for a specific 'S' group within a check — for verify
        title/instructions/button (e.g. 'consonant initial', '2 syllables')."""
        if check=='#C':
            return self.profile_class_initial_name(group)
        if check=='C#':
            return self.profile_class_final_name(group)
        if check=='syls':
            return self.profile_class_count_name(group)
        return str(group)  # profile check: the profile string itself
    def syllable_check_name(self,check=None):
        """Human name for a prep primitive CHECK itself (not a group within it),
        for the status line — so #C/C#/syls don't all read alike (they share one
        ftype, which is what cvcheckname keyed on)."""
        return {'#C':_("word-initial sounds"),
                'C#':_("word-final sounds"),
                'syls':_("syllable counts")}.get(check or self.check())
    def profile_class_count_name(self,syls):
        return _("{n} syllables").format(n=syls)
    def profile_class_prose(self,beg,syls,end):
        return _("{begend} ({count})").format(
                            begend=self.profile_class_begend_name(beg,end),
                            count=self.profile_class_count_name(syls))
    def check(self,check=None,unset=False):
        """This needs to change/clear subchecks"""
        if unset or check:
            log.info(_("Setting check {check}").format(check=check))
            self._check=check
        elif not hasattr(self,'_check'):
            log.info(_("Making check attribute ({check})").format(check=check))
            self._check=None
        # log.info(_("Returning check {check}").format(check=self._check))
        return self._check
    def build_checknames(self):
        self._checknames={
            'S':{ 1:[
                ('#C',_("Consonant Intial")),
                ('C#',_("Consonant Final")),
                ('syls',_("Syllable Count")),
                ('lc', _("Whole Citation Word Syllable Profile")),
                ('lx', _("Whole Root Syllable Profile")),
                ('pl', _("Whole {field} Word Syllable Profile"
                        "").format(field=self.nominalps_secondfield())),
                ('imp', _("Whole {field} Word Syllable Profile"
                        "").format(field=self.verbalps_secondfield())),
                ]},
            'T':{
                1:[('T', _("Tone Melody"))]},
            'V':{
                1:[('V1', _("First Vowel"))],
                2:[
                    ('V1=V2', _("First Two Same Vowels")),
                    ('V1xV2', _("Correspondence of First Two Vowels")),
                    ('V2', _("Second Vowel"))
                    ],
                3:[
                    ('V1=V2=V3', _("First Three Same Vowels")),
                    ('V3', _("Third Vowel")),
                    ('V2=V3', _("Second and Third Same Vowels")),
                    ('V2xV3', _("Correspondence of Second and Third Vowels"))
                    ],
                4:[
                    ('V1=V2=V3=V4', _("First Four Same Vowels")),
                    ('V3=V4', _("Third and Fourth Same Vowels")),
                    ('V3xV4', _("Correspondence of Third and Fourth Vowels")),
                    ('V4', _("Fourth Vowel"))
                    ],
                5:[
                    ('V1=V2=V3=V4=V5', _("First Five Same Vowels")),
                    ('V5', _("Fifth Vowel"))
                    ],
                6:[
                    ('V1=V2=V3=V4=V5=V6', _("First Six Same Vowels")),
                    ('V6', _("Sixth Vowel"))
                    ]
                },
            'C':{
                1:[('C1', _("First/only Consonant"))],
                2:[
                    ('C2', _("Second Consonant")),
                    ('C1=C2',_("First Two Same Consonants")),
                    ('C1xC2', _("Correspondence of First Two Consonants"))
                    ],
                3:[
                    ('C2=C3',_("Second and Third Same Consonants")),
                    ('C2xC3', _("Correspondence of Second and Third Consonants")),
                    ('C3', _("Third Consonant")),
                    ('C1=C2=C3',_("First Three Same Consonants"))
                    ],
                4:[
                    ('C4', _("Fourth Consonant")),
                    ('C1=C2=C3=C4',_("First Four Same Consonants"))
                    ],
                5:[
                    ('C5', _("Fifth Consonant")),
                    ('C1=C2=C3=C4=C5',_("First Five Same Consonants"))
                    ],
                6:[
                    ('C6', _("Sixth Consonant")),
                    ('C1=C2=C3=C4=C5=C6',_("First Six Same Consonants"))
                    ]
                },
            'CV':{
                1:[
                    # ('#CV1', _("Word-initial CV")),
                    ('CxV1', _("Correspondence of first CV")),
                    # ('CV1', _("First/only CV)")
                    ],
                2:[
                    # ('CV2', _("Second CV")),
                    ('CxV2', _("Correspondence of second CV")),
                    ('CV1=CV2',_("Same First/only Two CVs")),
                    # ('CV2#', _("Word-final CV"))
                    ],
                3:[
                    ('CxV3', _("Correspondence of third CV")),
                    ('CV1=CV2=CV3',_("Same First/only Three CVs")),
                    ('CV3', _("Third CV"))
                    ],
                4:[
                    ('CV1=CV2=CV3=CV4',_("Same First/only Four CVs")),
                    ('CV4', _("Fourth CV"))
                    ],
                5:[
                    ('CV1=CV2=CV3=CV4=CV5',_("Same First/only Five CVs")),
                    ('CV5', _("Fifth CV"))
                    ],
                6:[
                    ('CV1=CV2=CV3=CV4=CV5=CV6',_("Same First/only Six CVs")),
                    ('CV6', _("Sixth CV"))
                    ]
                },
            'VC':{
                1:[
                    ('VxC1', _("Correspondence of first VC")),
                    ],
                2:[
                    ('VxC2', _("Correspondence of second VC")),
                    # ('VC1=VC2',_("Same First/only Two VCs")),
                    ],
                3:[
                    ('VxC3', _("Correspondence of third VC")),
                    # ('VC1=VC2=VC3',_("Same First/only Three VCs")),
                    # ('VC3', _("Third VC"))
                    ],
                4:[
                    ('CV1=CV2=CV3=CV4',_("Same First/only Four CVs")),
                    ('CV4', _("Fourth CV"))
                    ],
                5:[
                    ('CV1=CV2=CV3=CV4=CV5',_("Same First/only Five CVs")),
                    ('CV5', _("Fifth CV"))
                    ],
                6:[
                    ('CV1=CV2=CV3=CV4=CV5=CV6',_("Same First/only Six CVs")),
                    ('CV6', _("Sixth CV"))
                    ]
                },
        }
    def assure_checknames(self):
        if not hasattr(self,'_checknames'):
            self.build_checknames()
    def checkcodes_by_cvt(self):
        self.assure_checknames()
        self._checkcodes_by_cvt={cvt:{code_tuple[0]
                    for nsyl,code_list in syl_dict.items()
                    for code_tuple in code_list
                    }
                for cvt,syl_dict in self._checknames.items()
                }
        log.info(_("self._checkcodes_by_cvt={codes}").format(codes=self._checkcodes_by_cvt))
    def cvt_of_check(self,check):
        for cvt,codes in self._checkcodes_by_cvt.items():
            # log.info(f"{cvt=},{codes=}")
            if check in codes:
                return cvt
    def cvcheckname(self,code=None):
        if self.cvt() == 'T':
            code='T'
        elif self.cvt() == 'S':
            # The three prep primitives (#C/C#/syls) share one ftype ('lc'), so
            # keying the name by ftype made them all read identically. Name them
            # by the actual primitive instead; fall back to ftype for Task-2
            # (profile) sorting.
            if self.is_syllable_primitive_check():
                return self.syllable_check_name()
            code=self.ftype()
        if not code:
            code=self.check()
        try:
            return _(self._cvchecknames[code])
        except KeyError:
            return None
    def cvchecknamesdict(self):
        """I reconstruct this here so I can look up names intuitively, having
        built the named checks by type and number of syllables."""
        self.assure_checknames()
        self._cvchecknames={}
        for t in self._checknames:
            for s in self._checknames[t]:
                for tup in self._checknames[t][s]:
                    self._cvchecknames[tup[0]]=tup[1]
        return self._cvchecknames
    def analang(self,analang=None):
        if analang:
            log.info(_("Setting analysis language as {analang} ({self})").format(analang=analang, self=self))
            self._analang=analang
        # log.info(_("Returning analysis language as {analang} ({self})").format(analang=self._analang, self=self))
        return self._analang
    def audiolang(self,audiolang=None):
        if audiolang:
            self._audiolang=audiolang
        if hasattr(self,'_audiolang'):
            return self._audiolang
    def ftype(self,ftype=None):
        if ftype:
            self._ftype=ftype
        elif not hasattr(self,'_ftype'):
            self._ftype='lc'
        return self._ftype
    def secondfield(self,ps):
        fields=self.program.settings.secondformfield
        if fields and ps in fields:
            return fields[ps]
    def nominalps_secondfield(self):
        return self.secondfield(self.program.settings.nominalps)
    def verbalps_secondfield(self):
        return self.secondfield(self.program.settings.verbalps)
    def __init__(self, program):
        self.program=program
        self.program.params=self
        """replaces setnamesall"""
        """replaces self.checknamesall"""
        super(CheckParameters, self).__init__()
        self._analang=self.program.db.analang
        self._audiolang=self.program.db.audiolang
        self._cvts={
                'V':{'sg':'Vowel','pl':'Vowels'},
                'C':{'sg':'Consonant','pl':'Consonants'},
                'CV':{'sg':'Consonant-Vowel combination',
                        'pl':'Consonant-Vowel combinations'},
                'VC':{'sg':'Vowel-Consonant combination',
                        'pl':'Vowel-Consonant combinations'},
                'T':{'sg':'Tone','pl':'Tones'},
                'S':{'sg':'Syllable Profile','pl':'Syllable Profiles'},
                }
        self.cvchecknamesdict()
        self.checkcodes_by_cvt()

