# coding=UTF-8
"""Mixin for group/category management operations on linguistic data.
Provides methods for creating, renaming, and reassigning groups without
pulling in sort presentation, verification UI, or check navigation."""
from utilities import logsetup
from utilities.error_handler import notify_error as ErrorNotice
from utilities.i18n import _

log=logsetup.getlog(__name__)

class Categories:
    def get_check(self):
        return self.program.params.check()
    def get_ps(self):
        return self.program.slices.ps()
    def get_profile(self):
        return self.program.slices.profile()
    def get_ftype(self):
        return self.program.params.ftype()
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
        values=sense.verificationtextvalue(profile,self.ftype) #always returns list
        if add and not values:
            v=sense.verificationtextvalue(profile,self.ftype,value=[add])
            return #if more complex, continue
        # EXACT match on the check part, not a substring one. A verification
        # code is '<check>=<group>', split on the LAST '=' because checks are
        # themselves compound ('C1=C2=C3'). Using `in` here meant the SHORTER
        # check matched the LONGER sibling's code — verifying under 'C1=C2'
        # found both 'C1=C2=NA' and 'C1=C2=C3=NA', replaced the first, set
        # add=None, and then fell into the remove branch for the second. So
        # every pass over 'C1=C2' silently DELETED 'C1=C2=C3's verification,
        # and the two checks unverified each other forever: the field screen
        # cycled "Tous les groupes … sont vérifiés et distincts!" through
        # C1=C2=C3 → C1=C2 → C1=C2=C3 → … (Kent 2026-07-31). Most visible on
        # NA, whose membership overlaps heavily across an '=' check and its
        # compound siblings.
        for code in [i for i in values if '='.join(i.split('=')[:-1])==check]:
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
    def confirmverificationgroup(self,sense,profile,check):
        """This does the one field storing a list of verified values
        for all checks"""
        """This results in NO group change where a group hasn't been confirmed!
        """
        log.info(_("Confirming that current group and verification code match "
                    "before making changes."))
        annogroup=self.getitemgroup(sense,check) #Segment or Tone
        vals=sense.verificationtextvalue(profile,self.ftype)
        # EXACT check match, for the same reason as modverification above.
        # The old `if check in i` was justified by "V1 must match V1=V2, if
        # present" — which is exactly backwards: a code's check part is
        # everything before the LAST '=', so 'V1' and 'V1=V2' are different
        # checks with different groups, and conflating them is what let one
        # unverify the other. The collision needs two checks where one name is a
        # PREFIX of the other ('C1=C2' alongside 'C1=C2=C3'); NA is where it
        # showed, because an NA code's check part is compound whenever the check
        # is (Kent 2026-07-31: "x=y=NA is NECESSARILY a compound check").
        curvalues=[i.split('=')[-1]  #last (value), if multiple
                    for i in sense.verificationtextvalue(profile,self.ftype)
                    if '='.join(i.split('=')[:-1])==check]
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
            return True
        elif not curvalue:
            log.error("Problem updating verification; current "
                        "value not there (should be {})"
                        "".format(annogroup))
        else: #not sure what to do here; maybe  throw bigger error?
            log.error("Problem updating verification; current "
                        "value ({}) is there, but not the same as "
                        "current sort group ({})."
                        "".format(curvalue, annogroup))
    def marksortgroup(self,sense,group,**kwargs):
        check=kwargs.get('check',self.program.params.check())
        profile=kwargs.get('profile',self.program.slices.profile())
        nocheck=kwargs.get('nocheck',False)
        if kwargs.get('updateverification'):
            add=self.verificationcode(check=check,group=group)
            noconfirmation=True #Should test w/wo this; time difference?
            if noconfirmation or self.confirmverificationgroup(sense, profile,
                                                                check):
                self.modverification(sense,profile,check,add)
        else: #unless specifically doing otherwise, marking should unverify:
            self.rmverification(sense,profile,check)
        self.setitemgroup(sense,check,group)
        # This group's membership just changed, so the cached example nodes for
        # it are stale. removeitemfromgroup has always cleared the cache; ADDING
        # never did, so ExampleDict.getexample kept serving the prefetched
        # node list and every group's button under-counted by however many words
        # had been sorted into it since boot — 76 where a recompute said 84,
        # 3 where it said 4 (Kent's DIAG, 2026-08-24). `group` is positional
        # here, so put it in the kwargs the code is built from, exactly as
        # getexample does.
        self.program.examples.clear_cache(**{**kwargs,'group':group,
                                            'check':check})
        if not nocheck:
            newgroup=self.getitemgroup(sense,check)
            if newgroup != group:
                log.error("Field addition failed! LIFT says {new}, not {old}.".format(
                                                    new=newgroup,old=group))
        if kwargs.get('updateforms'):
            if self.ftype != self.program.params.ftype():
                ErrorNotice(_("{ftype} differs from {pftype}; this is a problem!").format(
                            ftype=self.ftype, pftype=self.program.params.ftype()),
                            wait=True)
            self.updateformtoannotations(sense,check)
        if not kwargs.get('not_sorting'): #default is sorting
            #This unverifies without updateverification=True. Coerce to a real
            #bool: kwargs.get(...) returns None when the key is absent (the
            #normal sorting case), and status.update() compares `verified ==
            #False` exactly — None matches neither branch, so the group would
            #never leave 'done' (e.g. verify a word out, then sort it back in:
            #the group stayed verified and maybesort reported "all done").
            self.marksorted(sense,group,bool(kwargs.get('updateverification')))
        if kwargs.get('write'):
            self.maybewrite() #Not iterated over.
        if kwargs.get('thread_name'):
            self.untrack_thread(kwargs.get('thread_name'))
        if not nocheck:
            return newgroup
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
            log.debug(f"add_int_group status.groups: {self.program.status.groups(wsorted=True)}")
            self.program.status.groups(groups,wsorted=True)
            log.debug(f"add_int_group status.groups: {self.program.status.groups(wsorted=True)}")
            self.program.status.store()
        log.info("Groups (appended): {groups}".format(groups=groups))
        return str(newgroup)
    def rename_group(self,x,y,updatestatus=True):
        for _progress in self.updatebygroupsense(x,y,
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
