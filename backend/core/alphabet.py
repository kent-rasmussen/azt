# coding=UTF-8
from utilities.utilities import *
from utilities.i18n import _
from utilities import logsetup,file
log=logsetup.getlog(__name__)

from utilities.error_handler import notify_error as ErrorNotice

from backend.core.sorting_engine import Sort

def chart_example_rank(cls, glyph, keys):
    """Rank a candidate example word for `glyph` (class 'C' or 'V') from its
    verified segment keys (getcvverificationkeys actualkeys, e.g.
    {'C1':'b','V1':'a','C1=C2':'g'}), per Kent's DECIDED rule (agenda
    default_image_page_ordering, 2026-07-11):
      0 — the glyph is the ONLY distinct segment of its class in the word
          (all C slots == the glyph for a C-glyph; e.g. CVCV with C1=C2);
      1 — else the glyph is word-initial for its class (C1 / V1);
      2 — else merely present.
    Lower is better. Whether the word has a picture is gated by the caller —
    only pictured words are eligible at all."""
    slots={}
    for k,v in (keys or {}).items():
        parts=str(k).split('=')
        if parts and all(p and p[0]==cls and p[1:].isdigit() for p in parts):
            for p in parts:
                slots[p]=v
    if slots and all(v==glyph for v in slots.values()):
        return 0
    if slots.get(cls+'1')==glyph:
        return 1
    return 2

# ── booklet page ordering (Kent 2026-07-11): 'a' first, then vowels in
# facing pairs (LEFT = most frequent remaining, RIGHT = its most similar
# sound), then consonants likewise — voiced/voiceless and near neighbors
# oppose each other. Similarity from compact feature tables; symbols the
# tables don't know pair by frequency (distance 99 ties → frequency). ──

_SEG_NORMALIZE = { # common digraph spellings → the IPA the tables know
    'sh':'ʃ','zh':'ʒ','ch':'tʃ','ny':'ɲ','gn':'ɲ','ng':'ŋ',
    'th':'θ','dh':'ð','kh':'x','gh':'ɣ','ph':'ɸ','bh':'β','ꞌ':'ʔ',"'":'ʔ',
}
_VOWEL_FEAT = { # (height 0=high…2.5=low, backness 0=front…2=back, rounded)
    'i':(0,0,0),'ɪ':(0.5,0,0),'ɩ':(0.5,0,0),'y':(0,0,1),'e':(1,0,0),
    # 'a' is FRONT low (cardinal [a]) — so an a-less inventory seeds with æ
    # ("the 'a' of this language" — Kent 2026-07-13), then ɑ, then ʌ.
    'ɛ':(1.5,0,0),'æ':(2,0,0),'a':(2.5,0,0),'ɑ':(2.5,2,0),'ə':(1.25,1,0),
    'ɨ':(0,1,0),'ʉ':(0,1,1),'u':(0,2,1),'ʊ':(0.5,2,1),'ɷ':(0.5,2,1),
    'o':(1,2,1),'ɔ':(1.5,2,1),'ʌ':(1.5,2,0),'ø':(1,0,1),'œ':(1.5,0,1),
}
_CONS_FEAT = { # (place 0=labial…4=glottal, manner 0=stop…4=glide, voiced)
    'p':(0,0,0),'b':(0,0,1),'m':(0,2,1),'ɸ':(0,1,0),'β':(0,1,1),
    'f':(0.5,1,0),'v':(0.5,1,1),'θ':(1,1,0),'ð':(1,1,1),
    't':(1,0,0),'d':(1,0,1),'n':(1,2,1),'s':(1,1,0),'z':(1,1,1),
    'ts':(1,0.5,0),'l':(1,3,1),'r':(1,3.5,1),'ɾ':(1,3.5,1),
    'ʃ':(1.5,1,0),'ʒ':(1.5,1,1),'tʃ':(1.5,0.5,0),'dʒ':(1.5,0.5,1),
    'c':(2,0,0),'ɟ':(2,0,1),'ɲ':(2,2,1),'j':(2,4,1),
    'k':(3,0,0),'g':(3,0,1),'ŋ':(3,2,1),'x':(3,1,0),'ɣ':(3,1,1),'w':(3,4,1),
    'q':(3.5,0,0),'ʔ':(4,0,0),'h':(4,1,0),
    'y':(2,4,1), # orthographic y = the palatal glide (IPA j)
}

def _seg_features(g, cls):
    import unicodedata
    table=_VOWEL_FEAT if cls=='V' else _CONS_FEAT
    g=str(g).lower()
    for cand in (g,_SEG_NORMALIZE.get(g)):
        if cand and cand in table:
            return table[cand]
    base=''.join(c for c in unicodedata.normalize('NFD',g)
                 if not unicodedata.combining(c))
    for cand in (base,_SEG_NORMALIZE.get(base),base[:1]):
        if cand and cand in table:
            return table[cand]
    return None

def segment_distance(a, b, cls):
    """Smaller = more similar. 99.0 when either symbol is unknown to the
    tables (caller's tie-break then decides)."""
    fa=_seg_features(a,cls); fb=_seg_features(b,cls)
    if fa is None or fb is None:
        return 99.0
    if cls=='V':
        return 2*abs(fa[0]-fb[0])+abs(fa[1]-fb[1])+abs(fa[2]-fb[2])
    return abs(fa[0]-fb[0])+abs(fa[1]-fb[1])+0.5*abs(fa[2]-fb[2])

def propose_page_sequence(vowels, consonants, freq):
    """The page list per Kent's rule. Pure: takes glyph iterables + a
    {glyph: count} frequency dict; returns the ordered glyph list."""
    out=[]
    for cls,glyphs,seed in (('V',vowels,'a'),('C',consonants,None)):
        remaining=sorted({str(g) for g in glyphs if str(g) not in ('NA','')},
                         key=lambda g:(-freq.get(g,0),g))
        if seed is not None and remaining:
            if seed not in remaining:
                # No literal 'a' in this inventory (e.g. only ɑ/æ/ʌ):
                # page 1 is the vowel MOST SIMILAR to 'a' — the faithful
                # reading of "the first page should be 'a'" (Kent
                # 2026-07-13, after 'e' led an a-less inventory).
                seed=min(remaining,
                         key=lambda g:(segment_distance(seed,g,cls),
                                       -freq.get(g,0),g))
            out.append(seed); remaining.remove(seed)
        while remaining:
            left=remaining.pop(0) # most frequent remaining → LEFT page
            out.append(left)
            if remaining:         # its most similar sound → facing RIGHT page
                right=min(remaining,
                          key=lambda g:(segment_distance(left,g,cls),
                                        -freq.get(g,0),g))
                remaining.remove(right); out.append(right)
    return out

class Alphabet():
    """This class stores two dictionaries for alphabet glyphs:
    glyphdict: keyed on C and V, values contain a list of all verified consonants
                and vowels, respectively. Macrogroup verification means that no
                sortgroup has been added to a macrogroup (glyph) since it was
                verified, either through presorting or manual sorting.
                This is the source for the AlphabetChart, so there will be a
                period between completing a check and verifying all consonants
                including data for that check, where AlphabetChart work will not
                be possible. (this may not be true, but may be)
    glyph_members: keyed on glyphs, values contain a list of codes for verified
                groups which are currently sorted into that glyph. This is
                saved to disk for recovery, but it's contents are rather
                ephemeral. That is, a code such as Noun_CVCV_lc_V2_ie might not
                remain valid for a set of words if syllable profiles are
                reanalyzed, but more importantly, as groups are renamed.
                That is, when sorting, one might have Noun_CVCV_lc_V2_ie and
                Noun_CVCV_lc_V1_i in one group (e.g., 'ɨ'), but once that
                sorting is confirmed, all words in all relevant groups should
                have their annotations updated (C above), meaning the code
                would be updated, too (i.e., Noun_CVCV_lc_V2_ɨ). This is
                even before forms are updated to their annotations.
    On verification of *all groups*, the following will be updated:
        1. lift verification field (e.g., <field type="CVCV lc verification">).
        2. form annotation values (e.g., <annotation name="V1" value="i" />)
        3. forms are updated to annotations per usual (where not NA or int().)
    Once this happens, the old sorting data is useless, and will need to be
    reconstructed if needed, since forms and annotations have been updated.

    I hope it would be sufficient to have no changes to annotations or forms
    until all is confirmed, then force it all to happen at once (maybe backup
    before doing so?)

    self.program.slices.senses() is sensitive to ps and profile, and pulls from syllableprofiles
    iterating over that with sense.annotationvaluedictbyftypelang(ftype,lang)
    should provide the different checks and values for each sense.

    I need a button that allows iteration over a group with groups inside of it.
    """
    my_settings=['order']
    def order(self,order=[]):
        if order:
            self._order=order
        return getattr(self,'_order',[])
    def status(self,status={}):
        if status:
            self._status=status
        return getattr(self,'_status',{})
    def glyphdict(self,glyphdict={}):
        """This dict stores glyphs which are verified. When a glyph macrogroup
        has an item added to it, the glyph macrogroup is removed from here.
        integer values should be stored as strings."""
        if glyphdict:
            # Ensure we have sets for set operations
            glyphdict = {k: set(v) for k, v in glyphdict.items()}
            conflict=glyphdict['C']&glyphdict['V']
            if conflict:
                ErrorNotice(_("You have the glyph(s) ‘{conflict}’ as consonant "
                            "and as vowel! ({glyphs})").format(conflict=conflict,glyphs=glyphdict),wait=True)
                raise
            self._glyphdict={k:{str(i) for i in v} for k,v in glyphdict.items()}
        return getattr(self,'_glyphdict',{'V':set(),'C': set()})
    def glyph_members(self,gm={}):
        """This dict stores sorting information; items are sorted in and out of
        the values keyed by each glyph. Integer keys should be stored as
        strings."""
        if gm:
            self._glyph_members={str(k):set(v) for k,v in gm.items()}
        return getattr(self,'_glyph_members',{})
    def rename_glyph(self,x,y):
        gm=self.glyph_members()
        if y in gm:
            log.error(_("‘glyph_members’ contains {new}; not renaming {old}").format(new=y, old=x))
            return
        gd=self.glyphdict()
        for k in gd:
            if y in gd[k]:
                log.error(_("‘glyphdict’ contains {new}; not renaming {old}").format(new=y, old=x))
                return
        log.info(_("‘rename_glyph’ can safely rename {old} to {new}").format(old=x, new=y))
        self.glyph_members({y if k == x else k:v for k,v in gm.items()})
        # log.info(f"'glyph_members' renamed {x} to {y}")
        self.glyphdict({k:{y if i == x else i for i in v} for k,v in gd.items()})
        # log.info(f"'glyphdict' renamed {x} to {y}")
        for t in list(self.distinguished_by_cvt()):
            if x in t:
                self.undistinguish(t)
                self.distinguish((y if t[0]==x else t[0],y if t[1]==x else t[1]))
    def rename_glyph_member(self,item,newitem):
        """Leave verification status alone"""
        d=self.glyph_members()
        for glyph,items in d.items():
            if item in items:
                d[glyph].remove(item)
                d[glyph].add(newitem)
    def join_glyphs(self,x,y):
        log.info(f"Running Alphabet.join_glyphs")
        d=self.glyph_members()
        for i in x:
            # log.info(f"Checking {i} for conflicts in {y} {d[y]}")
            if self.conflicting_items(i,y):
                ErrorNotice(_("item {item} conflicts with glyph {glyph}").format(item=i, glyph=y),wait=True)
                return
        for i in y:
            # log.info(f"Checking {i} for conflicts in {x} {d[x]}")
            if self.conflicting_items(i,x):
                ErrorNotice(_("item {item} conflicts with glyph {glyph}").format(item=i, glyph=x),wait=True)
                return
        # log.info(f"No conflicts found.")
        for i in list(d[x]):
            # log.info(f"Removing {i} from {x}.")
            self.rm_glyph_member(i,x)
            # log.info(f"Adding {i} to {y}.")
            self.add_glyph_member(i,y)
        self.save_settings()
        log.info(f"Alphabet.join_glyphs done.")
        # remove glyph from glyph_members
    def distinguished(self,glyphs_distinguished={}):
        if not hasattr(self,'_distinguished'):
            self._distinguished={'V':set(),'C': set()}
        if glyphs_distinguished.keys() == {'V','C'}:
            self._distinguished={k:set(v) for k,v in glyphs_distinguished.items()}
        elif glyphs_distinguished:
            log.error(_("{glyphs} provided, but without good keys").format(glyphs=glyphs_distinguished))
            raise
        return self._distinguished
    def distinguished_by_cvt(self,**kwargs):
        cvt=kwargs.get('cvt',self.program.params.cvt())
        return self.distinguished()[cvt]
    def distinguish(self, g, **kwargs):
        self.distinguished_by_cvt().add(g)
    def undistinguish(self, g, **kwargs):
        self.distinguished_by_cvt().discard(g) #don't throw error on remove
    def undistinguish_any_with(self,g):
        d=self.distinguished_by_cvt()
        for j in [i for i in d if g in i]:
            d.discard(j) #don't throw error on remove
    def predistinguish(self,tuple_set):
        """This is here to keep users from seeing trivial glyph distinction prompts.
        Trivial here is defined as:
            —all members of each of a set of glyphs have already
                been distinguished from all members of the other glyph,
                when they were compared as sort groups
        This can only apply when all members are 'conflicting' groups (i.e.,
            same conflict_code), as they are the only ones who have been
            compared as sort groups
        Given that glyph membership cannot include more than one 'conflicting'
            group, the easiest criteria is to exclude those with more than
            one group, as these would necessarily contain groups which had not been
            previously compared. (if this is not the case, it is a problem;
            it should have been removed by remove_conflicting_items on sort)
        so we ask, for each glyph pairing presented:
            Is there no more than one member for each?
            Are each 'conflicting'?
            Are each distinguished as sort groups?
                (the last two in have_only_distinguished_items)
        """
        def nmembers(g):
            return len(gm[g])
        gm=self.glyph_members()
        for t in tuple_set:
            log.info(_("Working on {tuple} ({counts};{max}=)").format(tuple=t, counts=[i for i in map(nmembers,t)], max=max(map(nmembers,t))))
            if max(map(nmembers,t)) <= 1 and self.have_only_distinguished_items(*t):
                log.info(_("Distinguishing {glyph1} and {glyph2}").format(glyph1=gm[t[0]], glyph2=gm[t[1]]))
                self.distinguish(t)
            else:
                log.info(_("Not distinguishing {glyph1} and {glyph2}").format(glyph1=gm[t[0]], glyph2=gm[t[1]]))
    def add_glyph_member(self,item,glyph):
        """This is sort into"""
        self.mark_glyph_not_done(glyph)
        d=self.glyph_members()
        if glyph not in d:
            d[glyph]=set()
        # DIAG-conflict (temporary): every add-path is supposed to resolve
        # conflict_code first, yet a same-slice pair is landing in one glyph. Log
        # the collision AND the call stack so we see which path skipped resolution.
        clash=[m for m in d[glyph]
               if m!=item and self.conflict_code(m)==self.conflict_code(item)]
        if clash:
            import traceback
            log.warning("DIAG-conflict: add_glyph_member('%s' -> glyph '%s') collides "
                        "with same-conflict_code %s. Stack:\n%s",
                        item, glyph, clash,
                        ''.join(traceback.format_stack(limit=8)))
        d[glyph].add(item)
        self.glyph_members(d)
        log.debug(_("Alphabet.add_glyph_member done."))
    def rm_glyph_member(self,item,glyph=None):
        #If this raises KeyError, use discard
        d=self.glyph_members()
        if glyph:
            d[glyph].remove(item)
        else:
            for glyph in [g for g,m in d.items() if item in m]:
                d[glyph].remove(item)
        for glyph in [k for k,v in d.items() if v == set()]:
            del d[glyph]
            self.mark_glyph_not_done(glyph) #no members is also not verified
        if d:
            self.glyph_members(d) # Adding empty dict does nothing; see below
        elif hasattr(self,'_glyph_members'):
            delattr(self,'_glyph_members')
        log.debug(_("Alphabet.rm_glyph_member done."))
    def prune_empty_glyph_members(self):
        """Drop glyph members whose sort group has no member senses — e.g. a group
        emptied by a profile-unsort ('Not {profile}'), whose word left the slice.
        Such a group has no example, so it would render as a wordless, exampleless
        letter group in the review (the 'getexample returned None' case). Tests
        MEMBERSHIP (getexamples), not displayability (getexample): a group with
        senses but no image is NOT pruned — only truly memberless ones."""
        d=self.glyph_members()
        stale=[]
        for glyph, items in d.items():
            for item in items:
                try:
                    kwargs=self.parse_verificationcode(item)
                    group=kwargs.pop('group')
                    if group in ['NA']:  # NA parks unsortable words; never prune
                        continue
                    if not self.program.examples.getexamples(group, **kwargs):
                        stale.append(item)
                except Exception as e:
                    log.info("prune_empty_glyph_members skip %s: %s", item, e)
        for item in stale:
            log.info("Pruning empty glyph member '%s' (no member senses)", item)
            self.rm_glyph_member(item)
        if stale:
            self.save_settings()
    def mark_glyph_done(self,glyph,cvt):
        """Mark Verified"""
        if glyph in ['NA']:
            ErrorNotice("Never mark NA glyphs done!")
        d=self.glyphdict()
        d[cvt].add(glyph)
        log.info(_("‘{glyph}’ added to verified list").format(glyph=glyph))
        return self.glyphdict(d)
    def mark_glyph_not_done(self,glyph,cvt=None):
        """Mark Unverified"""
        d=self.glyphdict()
        if cvt:
            d[cvt].remove(glyph) #leave cvt in place, even if empty
        else:
            for cvt in [cvt for cvt,glyphs in d.items() if glyph in glyphs]:
                d[cvt].remove(glyph)
        log.info(_("‘{glyph}’ removed from verified list").format(glyph=glyph))
        return self.glyphdict(d)
    def cull_glyphdict(self):
        """This limits the verified glyphs to those that actually have members.
        """
        d=self.glyph_members()
        for cvt,glyphs in self.glyphdict().items():
            for i in list(glyphs):
                if i not in d:
                    self.mark_glyph_not_done(i,cvt)
    def cvt_of_glyph(self,glyph):
        """This should only be needed for glyphs that don't appear in glyphdict"""
        return {self.cvt_of_item(m) for m in self.glyph_members()[glyph]}
    def cvt_of_item(self,x):
        check=self.parse_verificationcode(x)['check']
        return self.program.params.cvt_of_check(check)
    def glyph_of_item(self,item):
        gm = self.glyph_members()
        for glyph, members in gm.items():
            if item in members:
                return glyph
    def senses_for_glyph(self,glyph):
        """The senses VERIFIED into this glyph's macrogroup, NOT every word whose
        orthography happens to contain the glyph.

        Each glyph member is a verification code (ps_profile_ftype_check_group), so
        it defines BOTH a slice (ps, profile) and a sort value (check==group). We
        must NOT use the sort annotation (annotation[check]==group) to pick senses:
        that's the sort value, and verification is per-cvprofile — the same sort
        value can be verified in one profile and still in-progress in another, so
        sort-matching leaks unverified words across slices. Instead, per member,
        confine to that member's slice and keep only senses that carry the
        '<check>=<group>' VERIFICATION code (what a group-verify writes to every
        member; see verified_groups_by_ps_profile). Collate across whatever slices
        the glyph spans."""
        db=self.program.db
        out=[]; seen=set()
        for item in self.glyph_members().get(str(glyph),set()):
            kw=self.parse_verificationcode(item)
            if kw['group']=='NA':
                continue
            ps,profile,ftype,check,group=(kw['ps'],kw['profile'],kw['ftype'],
                                          kw['check'],kw['group'])
            code=check+'='+group
            try:
                slice_senses=db.sensesbyps_profile[ps][profile]
            except KeyError:
                continue
            for s in slice_senses:
                if id(s) in seen:
                    continue
                if code in set(s.verificationtextvalue(profile,ftype)):
                    seen.add(id(s)); out.append(s)
        return out
    def propose_comparison_examples(self,glyph,n=3):
        """Top-n PICTURED example words for one glyph → [sense_id,…] (may be
        shorter). Candidates = senses VERIFIED into the glyph
        (senses_for_glyph) with an existing illustration file, ranked by
        chart_example_rank (glyph-is-only-segment-of-its-class first, then
        word-initial). Kent 2026-07-11: the booklet's three examples use 'the
        same algorithm for the best, second and third best'."""
        g=str(glyph)
        members=self.glyph_members().get(g,set())
        if not members:
            return []
        classes={self.cvt_of_item(m) for m in members}
        cls='C' if 'C' in classes else ('V' if 'V' in classes else None)
        if cls is None:
            return []
        ranked=[]
        for i,s in enumerate(self.senses_for_glyph(g)):
            try:
                uri=s.illustrationURI()
                if not (uri and file.exists(uri)):
                    continue
                counts,keys=s.getcvverificationkeys(self.ftype)
            except Exception:
                continue
            ranked.append((chart_example_rank(cls,g,keys),i,s.id))
        ranked.sort()
        return [sid for _r,_i,sid in ranked[:n]]
    def propose_chart_example(self,glyph):
        """The single best pictured example (the chart's one word per glyph):
        head of the same ranking the booklet uses."""
        ids=self.propose_comparison_examples(glyph,n=1)
        return ids[0] if ids else None
    def glyph_frequency(self):
        """{glyph: n senses VERIFIED into it}. Kent 2026-07-13: page order
        should rank by the language's DONE words, not the whole-lexicon
        machine extraction (slices.scount() counts every form in the
        database — 'e' read ~640 in a barely-sorted Demo_en). A letter's
        frequency here = how many verified words back it (senses_for_glyph),
        which is also exactly the pool its example words draw from."""
        freq={}
        for g in self.glyph_members():
            try:
                freq[str(g)]=len(self.senses_for_glyph(g))
            except Exception:
                freq[str(g)]=0
        return freq
    def propose_page_order(self):
        """Booklet page order per Kent's 2026-07-11 rule: page 1 'a'; the rest
        of the vowels in facing pairs (LEFT = most frequent remaining, RIGHT =
        its most similar sound); then consonants likewise."""
        gd=self.glyphdict()
        return propose_page_sequence(gd.get('V',()),gd.get('C',()),
                                     self.glyph_frequency())
    def propose_chart_examples(self,glyphs,existing=None):
        """Fill-only-empties batch: {glyph: sense_id} proposals for the glyphs
        in `glyphs` whose `existing` value is falsy. Never returns entries for
        glyphs the user already chose (the never-clobber rule)."""
        existing=existing or {}
        out={}
        for glyph in glyphs:
            g=str(glyph)
            if existing.get(g):
                continue
            sid=self.propose_chart_example(g)
            if sid:
                out[g]=sid
        return out
    def conflict_code(self,code):
        return code.split('_')[:4]
    def verificationcode(self,**kwargs):
        ps=kwargs.get('ps',self.program.slices.ps())
        profile=kwargs.get('profile',self.program.slices.profile())
        ftype=kwargs.get('ftype',self.ftype)
        check=kwargs.get('check',self.program.params.check())
        group=kwargs.get('group',self.program.status.group())
        return '_'.join([ps,profile,ftype,check,group])
    def parse_verificationcode(self,code):
        ps,profile,ftype,check,group=code.split('_')
        return {'ps':ps,'profile':profile,'ftype':ftype,
                'check':check,'group':group}
    def refresh_items(self):
        self.items_present=set()
        self.items_existing=set()
        k={'ftype':self.ftype} #ftype may need to iterate some day
        for _ in self.program.settings.reloadstatusdata():
            pass
        self.program.settings.reloadstatusdata_cleanup() # culled here
        d=self.program.status.dict()
        for k['cvt'],ps_d in d.items(): #read cvt from status
            for k['ps'],pr_d in ps_d.items():
                for k['profile'],ch_d in pr_d.items():
                    for k['check'],ch_v in ch_d.items():
                        # EXISTENCE ≠ ELIGIBILITY (2026-07-10). A group EXISTS as
                        # long as it holds members ('groups'), whatever its verify/
                        # distinguish state — and existence is what glyph MEMBERSHIP
                        # keys on: unverifying a group (e.g. a join into it) must
                        # never cost it its glyph; the glyph re-verifies instead.
                        # Conflating the two made every join silently drain
                        # alphabet.json and re-demand macrosorts.
                        for k['group'] in [i for i in ch_v.get('groups',[])
                                            if i not in ['NA']]:
                            self.items_existing.add(self.verificationcode(**k))
                        # Macrosort-eligible = VERIFIED and fully DISTINGUISHED from
                        # EVERY verified sibling on this slice — i.e. in NO pending
                        # distinction pair (same computation the join step uses).
                        # Per-group: a group going pending only drops itself, not its
                        # finished siblings; a lone verified group is trivially done.
                        pend={g for pair in self.program.status.pending_distinctions(
                                    cvt=k['cvt'],ps=k['ps'],
                                    profile=k['profile'],check=k['check'])
                                for g in pair}
                        for k['group'] in [i for i in ch_v['done']
                                            if i not in ['NA'] and i not in pend]:
                            # log.info(f"Adding item for {k}")
                            self.items_present.add(self.verificationcode(**k))
        self.cull_glyph_members()
    def cull_glyph_members(self):
        """Remove glyph members whose group no longer EXISTS (no members in its
        status node — e.g. joined away, renamed). Keyed on items_existing, NOT
        items_present: an unverified or distinction-pending group keeps its
        glyph membership (the glyph re-verifies instead of the group being
        re-macrosorted). See refresh_items."""
        for glyph,members in list(self.glyph_members().items()):
            for i in list(members):
                if i not in self.items_existing:
                    self.rm_glyph_member(i,glyph)
        self.save_settings()
    def glyphstoverify(self):
        """Which glyphs are sorted, but not verified yet (or added to since)?"""
        sorted=set(self.glyphs()) #this is constrained by cvt
        return sorted-{i for k,v in self.glyphdict().items() for i in v}
    def itemstosort(self):
        return sorted(self._itemstomacrosort)
    def items_present_in_cvt(self,cvt):
        return [i for i in self.items_present if self.cvt_of_item(i) == cvt]
    def item_is_tomacrosort(self,item):
        """This is for one off checking, where a refresh is needed, as well as
        confirmation what we're working with the correct cvt."""
        return item in self.renew_items_tomacrosort(self.cvt_of_item(item))
    def kick_conflicting_glyph_members(self):
        """Defensive invariant: NO glyph may hold two members from the SAME slice
        (same `conflict_code` = ps_profile_ftype_check, different group). Same-slice
        groups that belong together should have been JOINED within the slice, never
        co-glyphed. However a conflict got in (stale persisted glyph_members, or a
        rename that bypassed the sort-time kick), remove all-but-one from the glyph
        so the kicked one(s) re-enter macrosort — and re-sorting one back into the
        same glyph re-triggers the existing recurring-conflict → join-within-slice
        offer. KEEP a non-digit (already-named) group if present; KICK the isdigit
        (unnamed) one(s) — they need sorting anyway, so the choice doesn't matter.
        Returns the kicked item codes (also logged DIAG-conflict)."""
        d=self.glyph_members()
        kicked=[]
        for glyph,members in list(d.items()):
            byslice={}
            for m in members:
                byslice.setdefault('_'.join(self.conflict_code(m)),[]).append(m)
            for _code,ms in byslice.items():
                if len(ms)<2:
                    continue
                nondigit=[m for m in ms
                          if not self.parse_verificationcode(m)['group'].isdigit()]
                keep=nondigit[0] if nondigit else ms[0]
                for m in ms:
                    if m!=keep:
                        self.remove_item_from_glyph(m,glyph)
                        kicked.append((m,glyph,keep))
        if kicked:
            log.warning("DIAG-conflict KICK: same-slice glyph conflict(s) resolved by "
                        "un-glyphing %s (kept sibling shown); they re-enter macrosort.",
                        kicked)
        return kicked
    def renew_items_tomacrosort(self,cvt):
        self._itemsmacrosorted=set()
        self._itemstomacrosort=set()
        self.refresh_items()
        self.prune_empty_glyph_members()  # drop groups emptied by profile-unsort
        self.kick_conflicting_glyph_members()  # un-glyph same-slice conflicts (→ re-sort)
        for item in self.items_present_in_cvt(cvt):
            if item in [i for j in self.glyph_members().values() for i in j]:
                self._itemsmacrosorted.add(item)
            else:
                self._itemstomacrosort.add(item)
        return self._itemstomacrosort
    def mark_item_macrosorted(self,item,**kwargs):
        self._itemsmacrosorted.add(item)
        if item in self._itemstomacrosort:
            self._itemstomacrosort.remove(item)
    def mark_item_tomacrosort(self,item,**kwargs):
        self._itemstomacrosort.add(item)
        if item in self._itemsmacrosorted:
            self._itemsmacrosorted.remove(item)
    def presort_item(self,item):
        """Because this will work automatically:
        1. We don't want to assign groups to new int() letters
        2. We don't want to kick out groups that are already there.
        Let the user decide to do either, if necessary.        """
        glyph=self.parse_verificationcode(item)['group']
        if glyph in ['NA']: #just do this; no glyph for NA groups!
            self.mark_item_glyph(item,glyph)
            return
        if glyph in self.conflicts and item in self.conflicts[glyph]:
            log.error("Not presorting, since it looks like we kicked this one out already.")
            return
        if glyph in self.unsorted and item in self.unsorted[glyph]:
            log.error("Not presorting, since it looks like we unsorted this one before.")
            return
        log.info(_("presort_item moving {item} into ‘{glyph}’").format(item=item, glyph=glyph))
        if not glyph.isdigit() and not self.conflicting_items(item,glyph):
            self.mark_item_glyph(item,glyph) #This should never produce conflicts
    def have_only_distinguished_items(self,x,y):
        log.info(_("Running have_only_distinguished_items on {x} and {y}").format(x=x, y=y))
        gm=self.glyph_members()
        for i in gm[x]:
            for j in gm[y]:
                if (self.conflict_code(i) != self.conflict_code(j) or
                            not self.program.status.isdistinguished(
                                    self.parse_verificationcode(j)['group'],
                                    **self.parse_verificationcode(i))):
                    log.info(_("Found undistinguished items {item1} and {item2}").format(item1=i, item2=j))
                    return False
        return True
    def conflicting_items(self,item,glyph):
        d=self.glyph_members()
        if glyph not in d:
            return [] #keep iterable
        compare=self.conflict_code(item)
        r=list()
        for i in list(d[glyph]):
            if self.conflict_code(i) == compare:
                r.append(i)
        return r
    def remove_conflicting_items(self,item,glyph):
        """This doesn't currently update SortGlyphGroupButtonFrame, but should"""
        conflicts=self.conflicting_items(item,glyph)
        if glyph in self.conflicts:
            recurring_conflicts=set(conflicts) & self.conflicts[glyph]
            self.conflicts[glyph]|=set(conflicts)
        else:
            recurring_conflicts=set()
            self.conflicts[glyph]=set(conflicts)
        if conflicts:
            if recurring_conflicts:
                text='\n'+_("This is the second time I’ve removed this item recently; "
                "so I’m going to ask you to consider joining them now.")
            else:
                text=''
            ErrorNotice(_("Removing {items} from ‘{glyph}’ to make room for {new}{text}"
                        ).format(items=conflicts,glyph=glyph,new=item,text=text),
                                wait=True)
        for i in conflicts:
            self.remove_item_from_glyph(i)
        return recurring_conflicts
    def mark_item_glyph(self,item,glyph):#maybe move to Alphabet Sort
        if self.parse_verificationcode(item)['group'] in ['NA'] and glyph not in ['NA']:
            ErrorNotice("Never mark NA sort groups other than in NA glyph!")
        self.rm_glyph_member(item) # in case elsewhere
        recurring_conflicts=self.remove_conflicting_items(item,glyph) #other group from same check
        self.add_glyph_member(item,glyph)
        self.mark_item_macrosorted(item)
        if item in self.glyph_members()[glyph]:
            log.info(_("mark_item_glyph added ‘{item}’ to ‘{glyph}’").format(item=item, glyph=glyph))
        else:
            log.info(_("mark_item_glyph failed to add ‘{item}’ to ‘{glyph}’").format(item=item, glyph=glyph))
            # log.info(f"{self.glyph_members()=}")
        return recurring_conflicts
    def remove_item_from_glyph(self,item,glyph=None):
        try:
            self.unsorted[glyph].add(item)
        except KeyError:
            self.unsorted[glyph]={item}
        self.rm_glyph_member(item,glyph) # in case elsewhere
        self.cull_glyphdict() #without knowing glyph or cvt
        self.mark_item_tomacrosort(item)
    def update_symbols(self):
        """I need to rethink this method entirely. How to make sure all symbols
        are available to the alphabet chart?
        """
        order=self.program.settings.alpha_order()
        """this is a dict keyed by C,V; iterate appropriately!"""
        glyphdict=self.glyphdict()
        """Extra symbols not in order"""
        extras={i for i in items if not i.isdecimal()}-set(self.order())
        log.info(f"adding to {cv}: {extras=}")
        """Add to beginning of order"""
        order=sorted(extras)+self.order() #put new symbols first
        #only actually present:
        """limit to those symbols actually verified somewhere (iterate appropriately)"""
        order=[i for i in self.order() if i in items]
        """store new order"""
        self.order(order)
    def glyph(self,glyph=False,window=False):
        """This maintains the glyph we are actually on:
        False: don't set a glyph
        None: there is no current glyph
        """
        if glyph is not False: #this needs to be able to be specified None
            if glyph:
                glyph=str(glyph)# in case an int() group gets through
            self._glyph=glyph
        if window and window.winfo_exists():
            window.destroy()
        return getattr(self,'_glyph',None)# this needs to be booleanable
    def glyphs(self):
        return [k for k,v in self.glyph_members().items()
                        if [i for i in v
                            if self.cvt_of_item(i) == self.program.params.cvt()]
                ]
    def save_settings(self):
        self.program.settings.storesettingsfile(setting='alphabet')
    def __init__(self, program):
        self.program=program
        self.program.alphabet=self
        self.ftype=self.program.params.ftype()
        self.program.settings.settingsobjects() #should do this more; can be redone!
        # self.renew_items_tomacrosort() #if needed, run then, with cvt
        # Defense-in-depth (2026-07-11 data wipe): NEVER let the init-time
        # save write empty glyph state over the settings file. If the push
        # above didn't populate us (whatever the reason), saving now could
        # only destroy data on disk — skip and say so.
        if self.glyph_members() or any(self.glyphdict().values()):
            self.save_settings()
        else:
            log.info("Alphabet init: no glyph state in memory; NOT saving "
                     "(protects any on-disk alphabet data)")
        self.conflicts={} #keep track of what has been kicked out of a group before
        self.unsorted={}

class AlphabetChartData:
    """Backend data/logic mixin for alphabet chart. No UI imports."""
    my_settings = ['exids', 'order', 'ncolumns', 'chart_title', 'pagesize']

    def init_chart_data(self, **kwargs):
        # self.program = program
        self.show_at_least = 5
        self.ncolopts = range(1, 15)
        self.db = getattr(self.program, 'db', kwargs.get('db'))
        if hasattr(self.program, 'settings'):
            defs = {'ncolumns': 5, 'pagesize': 'A4', 'order': [], 'exids': {}, 'chart_title': ''}
            for k in self.my_settings:
                setattr(self, k, self.program.settings.mgr.get('alphabet_' + k, defs.get(k)))
            self.analangname = self.program.settings.languagenames[self.db.analang]
        else:
            for k in ['exids', 'order']:
                setattr(self, k, kwargs.get(k, 0))
            self.ncolumns = kwargs.get('ncolumns', False)
            if type(self.ncolumns) != int and not str(self.ncolumns).isdigit():
                self.ncolumns = 8
            self.analangname = self.db.analang
            self.pagesize = 'letter'
        self.imgdir = self.db.imgdir
        log.info(f"using {self.imgdir=}")
        if not self.order:
            log.info(f"No alphabetical order found; using all known glyphs")
            self.order = [str(i) for j in self.db.s[self.db.analang].values() for i in j]
            self.order.sort()
        if hasattr(self.program, 'alphabet'):
            gd = {str(i) for j in self.program.alphabet.glyphdict().values() for i in j}
            self.order = sorted(gd - set([str(i) for i in self.order])) + [str(i) for i in self.order if i in gd]
        self.order = [i for n, i in enumerate(self.order) if n == self.order.index(i)
                      if i not in ['NA']]
        log.info(f"Using this alphabetical order: {self.order}")
        log.info(f"Using these exids: {self.exids}")
        # DEFAULTS (Kent 2026-07-11, agenda default_image_page_ordering): a
        # NEW chart opens with every glyph's example ALREADY SET to a pictured
        # word — fill ONLY empty slots; a user's saved choice is never
        # overwritten. Rule: glyph-is-the-only-C/V-in-the-word first, then
        # word-initial, pictured words only (Alphabet.propose_chart_example).
        if hasattr(self.program,'alphabet'):
            try:
                proposed=self.program.alphabet.propose_chart_examples(
                    self.order,self.exids if isinstance(self.exids,dict) else {})
            except Exception as e:
                log.info("chart example proposal skipped: %s",e)
                proposed={}
            if proposed:
                if not isinstance(self.exids,dict):
                    self.exids={}
                self.exids.update(proposed)
                log.info("Proposed default examples for %d glyph(s): %s",
                         len(proposed),proposed)
        p = self.program.lex_ui
        if self.exids:
            for k in set(self.order) - set(self.exids):
                self.exids[str(k)] = None
            self.exobjs = {str(g): (self.db.sensedict[self.exids[g]]
                                    if self.exids[g] in self.db.sensedict
                                    else None)
                           for g in self.exids}
            for glyph, sense in [(k, v) for k, v in self.exobjs.items() if v is not None]:
                di = sense.illustrationURI()
                if file.exists(di):
                    try:
                        sense.image = p.image(di)
                    except Exception:
                        sense.image = None
                if hasattr(sense, 'image') and sense.image:
                    sense.image.scale(1, pixels=100, scaleto='height')
                else:
                    self.exobjs[str(glyph)] = None
                    self.exids[str(glyph)] = None
        else:
            self.exids = {str(g): None for g in self.order}
            self.exobjs = {str(g): None for g in self.order}
        self.buttons = {}
        self.order_bits = {}
        self.show_bits = {}
        self.show_pictured_only = False
        self.hide_vars = {}  # UI BooleanVars set up by task/UI class

    def save_settings(self):
        if not hasattr(self.program, 'settings'):
            return
        log.error("If you're seeing this, you have passed a settings module, "
                  "but there is no save_settings method in the parent class...")

    def _hidden(self, value=dict()):
        for i in value:
            self.hide_vars[i].set(value[i])
        return {i: self.hide_vars[i].get() for i in self.hide_vars}


class AlphabetComparisonData:
    """Backend data/logic mixin for alphabet comparison. No UI imports."""

    def init_comparison_data(self, **kwargs):
        self.db = getattr(self.program, 'db', kwargs.get('db'))
        if hasattr(self.program, 'alphabet'):
            glyphdict = self.program.alphabet.glyphdict()
        else:
            glyphdict = self.program.glyphdict
        self.symbols = [i for j in glyphdict.values() for i in j]
        self.vowels = list(glyphdict['V'])
        self.consonants = list(glyphdict['C'])
        self.settings = self.load_settings()
        # DEFAULTS (Kent 2026-07-11, agenda default_image_page_ordering): an
        # unsaved booklet opens with the page order proposed ('a' first, then
        # vowels in facing similar-pairs by frequency, then consonants) and
        # each page's THREE examples pre-picked by the same ranking as the
        # chart. Unset values only; saved choices are never overwritten, and
        # nothing persists until the user saves (save_pages/save_examples).
        if hasattr(self.program, 'alphabet'):
            alph = self.program.alphabet
            try:
                if not self.settings.get('pages'):
                    self.settings['pages'] = alph.propose_page_order()
                    log.info("Proposed booklet page order: %s",
                             self.settings['pages'])
                for g in self.settings.get('pages') or []:
                    if not self.settings.get(g):
                        ex = alph.propose_comparison_examples(g)
                        if ex:
                            self.settings[g] = ex
            except Exception as e:
                log.info("booklet defaults proposal skipped: %s", e)

    def load_settings(self):
        try:
            reports_mgr = self.program.settings.mgr.reports
            return reports_mgr.load()
        except Exception as e:
            log.warning(f"Could not load settings via manager: {e}")
        return {}

    def save_settings_file(self):
        self.settings['booklet_title'] = self.title_var.get()
        self.settings['cover_image'] = self.selected_cover_path
        self.settings['logo_image'] = self.selected_logo_path
        self.settings['description_text'] = self.description_var.get()
        try:
            reports_mgr = self.program.settings.mgr.reports
            reports_mgr.save(self.settings)
            if hasattr(self.program, 'git') and self.program.git:
                self.program.data_repo['git'].add(reports_mgr.filename, force=True)
        except Exception as e:
            log.warning(f"Could not save settings via manager: {e}")

    def redo_pages_from_stats(self):
        """'Redo pages by current stats' (Kent 2026-07-13): re-propose the
        page ORDER from the current verified data, replacing the saved
        layout — the sanctioned alternative to hand-editing reports.json.
        Explicit gesture, so never-clobber stays intact elsewhere. Example
        words: filled only where a page has no saved choice (manual example
        picks survive a redo)."""
        try:
            alph = self.program.alphabet
            pages = alph.propose_page_order()
            if not pages:
                log.warning("redo pages: nothing verified to propose from")
                return
            self.settings['pages'] = pages
            for g in pages:
                if not self.settings.get(g):
                    ex = alph.propose_comparison_examples(g)
                    if ex:
                        self.settings[g] = ex
        except Exception as e:
            log.warning(f"redo pages proposal failed: {e}")
            return
        for f in list(getattr(self, 'pageFrames', [])):
            try:
                f.destroy()
            except Exception:
                pass
        self.pageFrames = []
        self.add_pages(*pages)
        self.save_pages()  # persist: this IS the user's explicit choice
    def save_pages(self):
        self.settings['pages'] = [i.glyph for i in self.pageFrames]
        self.save_settings_file()

    def save_examples(self):
        example_dict = {i.glyph: i.current_examples for i in self.pageFrames}
        self.settings.update(example_dict)
        self.save_settings_file()

    def generate_pdf(self):
        from io_put import alphabet_comparison_pdf
        from utilities import file
        import os

        def prepare_data(page):
            items = []
            for eid in page.current_examples:
                if eid and eid in self.db.sensedict:
                    sense = self.db.sensedict[eid]
                    word = sense.entry.lcvalue()
                    uri = sense.illustrationURI()
                    items.append((page.glyph, word, uri))
            return {'symbol': page.glyph, 'items': items}

        pages = [prepare_data(i) for i in self.pageFrames if i.glyph]

        extra_pages = []
        texts_dir = None
        parent_dir = os.path.dirname(self.db.reportdir)
        for folder in ['texts', 'textes', 'text', 'texte']:
            candidate = os.path.join(parent_dir, folder)
            if os.path.exists(candidate) and os.path.isdir(candidate):
                texts_dir = candidate
                break

        if texts_dir:
            from glob import glob as _glob
            txt_files = sorted(_glob(os.path.join(texts_dir, "*.txt")))
            log.info(f"Found {len(txt_files)} extra text files in {texts_dir}")
            for txt_path in txt_files:
                try:
                    with open(txt_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                    if not lines:
                        continue
                    if hasattr(self.program, 'repo'):
                        self.program.data_repo['git'].add(txt_path, force=True)
                    title_line = lines[0].strip()
                    body = "".join(lines[1:]).strip()
                    base_name = os.path.splitext(os.path.basename(txt_path))[0]
                    img_path = None
                    for ext in ['.jpg', '.jpeg', '.png', '.svg']:
                        img_cand = os.path.join(texts_dir, base_name + ext)
                        if os.path.exists(img_cand):
                            img_path = img_cand
                            if hasattr(self.program, 'git'):
                                self.program.data_repo['git'].add(img_cand, force=True)
                            break
                    extra_pages.append({
                        'type': 'extra_text',
                        'title': title_line,
                        'text': body,
                        'image': img_path
                    })
                except Exception as e:
                    log.error(f"Error reading extra text file {txt_path}: {e}")

        p = self.program.lex_ui
        page_names = [i['symbol'] for i in pages]
        suffix = "wTexts" if extra_pages else ""
        filename = '_'.join([_("Booklet"), *page_names,
                             f'{suffix}[{self.db.analang}]{self.font_var.get()}.pdf'])
        filepath = file.getdiredurl(self.db.reportdir, filename)

        if hasattr(self.program.settings, 'loadsettingsfile'):
            self.program.settings.loadsettingsfile(setting='contributors')
        contributors_list = self.program.settings.alphabet_contributors()
        copyright_text = self.copyright_var.get()
        title_text = self.title_var.get()
        description_text = self.description_var.get()
        made_with = f"Made with {self.program.name} ({self.program.url})"
        font_name = self.font_var.get()

        r = alphabet_comparison_pdf.create_comparison_chart(
            filepath, *pages,
            extra_pages=extra_pages,
            prose_count=self.prose_count_var.get(),
            title=title_text,
            cover_image=self.selected_cover_path,
            logo_image=self.selected_logo_path,
            contributors=contributors_list,
            description=description_text,
            copyright_text=copyright_text,
            made_with=made_with,
            font_name=font_name,
            analang=self.db.analang
        )
        log.info(f"Generated {filepath}")

        try:
            from utilities.utilities import open_file
            open_file(filepath)
        except Exception as e:
            log.warning(f"Could not open PDF automatically: {e}")
        if r == 'using_helvetica':
            q = p.window(self, title=_("Using Helvetica"))
            q_text = _("This PDF uses Helvetica because neither Charis nor Andika were found; "
                       "install one of them for better glyph treatment.")
            p.label(q.frame, text=q_text, sticky='news')
            q.lift()
            return
        q = p.window(self, title=_("Is this a final PDF?"))
        q_text = _("Are you done with this PDF?")
        q_button_text = _("Yes")
        q_text += '\n' + _("Click {yes} to store and share with your data.").format(yes=q_button_text)
        p.label(q.frame, text=q_text, sticky='news')
        p.button(q.frame, text=q_button_text,
                  cmd=lambda x=filepath: self.program.data_repo['git'].add(x, force=True),
                  r=1, sticky='news')
        q.lift()
