# coding=UTF-8
from utilities.utilities import *
from utilities import logsetup
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

    program.slices.senses() is sensitive to ps and profile, and pulls from syllableprofiles
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
                ErrorNotice(_("You have the glyph(s) '{conflict}' as consonant "
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
            log.error(_("'glyph_members' contains {new}; not renaming {old}").format(new=y, old=x))
            return
        gd=self.glyphdict()
        for k in gd:
            if y in gd[k]:
                log.error(_("'glyphdict' contains {new}; not renaming {old}").format(new=y, old=x))
                return
        log.info(_("'rename_glyph' can safely rename {old} to {new}").format(old=x, new=y))
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
        cvt=kwargs.get('cvt',program.params.cvt())
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
        d[glyph].add(item)
        self.glyph_members(d)
        log.info(_("Alphabet.add_glyph_member done."))
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
        log.info(_("Alphabet.rm_glyph_member done."))
    def mark_glyph_done(self,glyph,cvt):
        """Mark Verified"""
        if glyph in ['NA']:
            ErrorNotice("Never mark NA glyphs done!")
        d=self.glyphdict()
        d[cvt].add(glyph)
        log.info(_("'{glyph}' added to verified list").format(glyph=glyph))
        return self.glyphdict(d)
    def mark_glyph_not_done(self,glyph,cvt=None):
        """Mark Unverified"""
        d=self.glyphdict()
        if cvt:
            d[cvt].remove(glyph) #leave cvt in place, even if empty
        else:
            for cvt in [cvt for cvt,glyphs in d.items() if glyph in glyphs]:
                d[cvt].remove(glyph)
        log.info(_("'{glyph}' removed from verified list").format(glyph=glyph))
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
        return program.params.cvt_of_check(check)
    def glyph_of_item(self,item):
        for glyph in self.glyph_members():
            if item in self.glyph_members()[glyph]:
                return glyph
    def conflict_code(self,code):
        return code.split('_')[:4]
    def verificationcode(self,**kwargs):
        ps=kwargs.get('ps',program.slices.ps())
        profile=kwargs.get('profile',program.slices.profile())
        ftype=kwargs.get('ftype',self.ftype)
        check=kwargs.get('check',program.params.check())
        group=kwargs.get('group',program.status.group())
        return '_'.join([ps,profile,ftype,check,group])
    def parse_verificationcode(self,code):
        ps,profile,ftype,check,group=code.split('_')
        return {'ps':ps,'profile':profile,'ftype':ftype,
                'check':check,'group':group}
    def refresh_items(self):
        self.items_present=set()
        k={'ftype':self.ftype} #ftype may need to iterate some day
        program.settings.reloadstatusdata() # culled here
        d=program.status.dict()
        for k['cvt'],ps_d in d.items(): #read cvt from status
            for k['ps'],pr_d in ps_d.items():
                for k['profile'],ch_d in pr_d.items():
                    for k['check'],ch_v in ch_d.items():
                        for k['group'] in [i for i in ch_v['done']
                                            if i not in ['NA']]: #only verified
                            # log.info(f"Adding item for {k}")
                            self.items_present.add(self.verificationcode(**k))
        self.cull_glyph_members()
    def cull_glyph_members(self):
        """This removes items from the sorting piles if they don't exist"""
        for glyph,members in list(self.glyph_members().items()):
            for i in list(members):
                if i not in self.items_present:
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
    def renew_items_tomacrosort(self,cvt):
        self._itemsmacrosorted=set()
        self._itemstomacrosort=set()
        self.refresh_items()
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
        log.info(_("presort_item moving {item} into '{glyph}'").format(item=item, glyph=glyph))
        if not glyph.isdigit() and not self.conflicting_items(item,glyph):
            self.mark_item_glyph(item,glyph) #This should never produce conflicts
    def have_only_distinguished_items(self,x,y):
        log.info(_("Running have_only_distinguished_items on {x} and {y}").format(x=x, y=y))
        gm=self.glyph_members()
        for i in gm[x]:
            for j in gm[y]:
                if (self.conflict_code(i) != self.conflict_code(j) or
                            not program.status.isdistinguished(
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
                text='\n'+_("This is the second time I've removed this item recently; "
                "so I'm going to ask you to consider joining them now.")
            else:
                text=''
            ErrorNotice(_("Removing {items} from '{glyph}' to make room for {new}{text}"
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
            log.info(_("mark_item_glyph added '{item}' to '{glyph}'").format(item=item, glyph=glyph))
        else:
            log.info(_("mark_item_glyph failed to add '{item}' to '{glyph}'").format(item=item, glyph=glyph))
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
        order=program.settings.alpha_order()
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
                            if self.cvt_of_item(i) == program.params.cvt()]
                ]
    def save_settings(self):
        program.settings.storesettingsfile(setting='alphabet')
    def __init__(self, program):
        self.program=program
        program.alphabet=self
        self.ftype=program.params.ftype()
        self.program.settings.settingsobjects() #should do this more; can be redone!
        # self.renew_items_tomacrosort() #if needed, run then, with cvt
        self.save_settings()
        self.conflicts={} #keep track of what has been kicked out of a group before
        self.unsorted={}
