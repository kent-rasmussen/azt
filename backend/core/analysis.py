# coding=UTF-8
import sys
import collections
# import re
# import datetime
# import tkinter as tk
from utilities.utilities import *
from utilities.times import now, fixnaivedatetime
from io_put import lift
from utilities import logsetup, htmlfns
log=logsetup.getlog(__name__)
# import time
# import webbrowser
# import os
# import platform
# import subprocess
# import threading
# import json
import itertools
import bisect
# import inspect
# import multiprocessing

from utilities.error_handler import notify_error as ErrorNotice

from utilities.i18n import _
from utilities import rx

class Entry(lift.Entry): #Not in use
    def __init__(self, db, guid, window=None, check=None, problem=None,
        *args, **kwargs):
        self.problem=problem #?!?
        """"This should go elsewhere, when a check is actually done."""
        self.checkresults={}
        lift.Entry.__init__(self, db, guid=guid)
    def addresult(self, check, result):
        """This could be stored under check[guid]; otherwise, how do we want
        to store and access this info?"""
        try:
            self.checkresults[check.name]
        except KeyError:
            self.checkresults[check.name]={}
        try:
            self.checkresults[check.name][check.subcheck]
        except KeyError:
            self.checkresults[check.name][check.subcheck]={}
        self.checkresults[check.name][check.subcheck]['result']=result
        log.info("Don't forget to write these changes to a file somewhere...")

class DictbyLang(dict):
    """docstring for DictbyLang."""
    def getformfromnode(self,node,truncate=False):
        #this assumes *one* value/lang, a second will overwrite.
        #this will comma separate text nodes, if there are multiple text nodes.
        if isinstance(node,lift.et.Element):
            lang=node.get('lang')
            if truncate: #this gives up to three words, no parens
                text=unlist([rx.glossifydefn(i.text).strip('‘’')
                                                for i in node.findall('text')
                                                if i is not None
                                                if i.text is not None
                                                ])
            else:
                text=unlist([i.text.strip('‘’') for i in node.findall('text')
                                                if i is not None
                                                if i.text is not None
                                                ])
            log.log(4,"Adding {text} to {self} dict under {lang}".format(text=t(text),self=self,lang=lang))
            self[lang]=text
        else:
            log.info("Not an element node: {node} ({type})".format(node=node,type=type(node)))
            log.info("node.stripped: {strip} ({len})".format(strip=node.strip(),len=len(node)))
    def frame(self,framedict,langs): #langs can/should be ordered
        """the frame only applies if there is a language value; I hope that's
        what we want..."""
        # log.info("Applying frame {} in these langs: {}".format(framedict,langs))
        # log.info("Using regex {}".format(rx.framerx))
        ftype=framedict['field']
        for l in [i for i in langs if i in framedict
                                    if i in self and self[i]
                                    if i != 'field'
                ]:
            # log.info("Using lang {}".format(l))
            if type(self[l]) is dict and ftype in self[l]:
                # log.info("Subbing {} into {}".format(self[l][ftype],framedict[l]))
                t=self[l][ftype]
            else:
                # log.info("Subbing {} into {}".format(self[l],framedict[l]))
                t=self[l]
            if self[l]:
                self.framed[l]=rx.framerx.sub(t,framedict[l])
            else:
                self.framed[l]=None
        # log.info("Applied frame: {}".format(self.framed))
    def __init__(self):
        super(DictbyLang, self).__init__()
        self.framed={}

class ExampleDict(dict):
    """This function finds examples in the lexicon for a given tone value,
    in a given tone frame (from check); thus, only sorted data."""
    def sensesinslicegroup(self,group,check):
        """Convert to senses before return"""
        #This returns all the senses with a given tone value
        senses=self.program.task.getsensesingroup(check,group)
        if not senses:
            log.error("There don't seem to be any sensids in this check tone "
                "group, so I can't get you an example. ({check} {group})"
                "".format(check=check,group=group))
            return []
        """The above doesn't test for profile, so we restrict that next"""
        log.info("senses ({n}): {ids}".format(n=len(senses),
                                            ids=[i.id for i in senses][:5]))
        sensesinslice=self.program.slices.inslice(senses)
        log.info("sensesinslice ({n}): {ids}".format(n=len(sensesinslice),
                                            ids=[i.id for i in sensesinslice][:5]))
        if not sensesinslice:
            log.error(f"There don't seem to be any sensids from that check tone "
                f"group in this slice-group, so I can't get you an example. "
                f"({self.program.slices.ps()}-{self.program.slices.profile()}, "
                f"{check} {group})")
            return []
        return list(set(senses)&set(sensesinslice))
    def hasglosses(self,node):
        # log.info("hasglosses sense: {}".format(sense.id))
        try:
            return node.translation.textvaluedict()
        except AttributeError:
            return node.sense.glosses
    def hassoundfile(self,node):
        """sets self.audiofileisthere and maybe self.audiofileURL"""
        """You want to do this even if you don't need it, as this checks and
        marks the example"""
        return node.hassoundfile()
    def exampletypeok(self,node,**kwargs):
        # log.info("exampletypeok checking {node} for kwargs={kwargs}".format(node=node, kwargs=kwargs))
        kwargs=exampletype(**kwargs)
        if node is None:
            return
        # log.info("exampletypeok looking at node={node}".format(node=node))
        if kwargs['wglosses'] and not self.hasglosses(node):
            log.info("Gloss check failed for {sense_id}".format(sense_id=node.sense.id))
            return
        if not self.hassoundfile(node) and kwargs['wsoundfile']:
            # log.info("Audio file check failed for {}".format(node.sense.id))
            return
        # log.info("exampletypeok returning True")
        return True
    def prefetch_examples(self, groups, all_for_cvt=False, **kwargs):
        """
        Antigravity: Optimized method to pre-fetch examples for multiple groups at once.
        This avoids iterating over the entire database for each group.
        """
        check = kwargs.get('check', self.program.params.check())
        ftype = kwargs.get('ftype', self.program.params.ftype())
        log.info("Prefetching examples for {n} groups...".format(n=len(groups)))
        # Prepare codes mapping to avoid repeated calls and initialize cache
        group_to_code = {}
        for group in groups:
            code = self.program.alphabet.verificationcode(**{**kwargs, 'group': group})
            if code not in self.nodes_by_code:
                self.nodes_by_code[code] = [] # Initialize
                group_to_code[group] = code
        if not group_to_code:
            log.info("All groups already cached.")
            return
        # Iterate once over the database
        if self.program.params.cvt() == 'T':
            # T: Tone examples
            senses = self.program.slices.inslice(self.program.db.senses)
            for s in senses:
                group = s.tonevaluebyframe(check)
                if group in group_to_code:
                    if check in s.examples:
                        self.nodes_by_code[group_to_code[group]].append(s.examples[check])
        elif all_for_cvt:
            # all_for_cvt: Any ps-profile
            senses = self.program.db.senses
            for s in senses:
                vals = s.annotationvaluedictbyftypelang(ftype, self.program.db.analang).values()
                # Check if any of our target groups are in this sense's values
                # This might be slightly expensive if vals is large, but usually it's small
                for group in groups: 
                    if group in group_to_code and group in vals:
                        if ftype in s.ftypes:
                            self.nodes_by_code[group_to_code[group]].append(s.ftypes[ftype])
        else: 
            # Standard case: Other FormParent nodes
            senses = self.program.slices.inslice(self.program.db.senses, **kwargs)
            for s in senses:
                val = s.annotationvaluebyftypelang(ftype, self.program.db.analang, check)
                group = str(val)
                if group in group_to_code:
                    if ftype in s.ftypes:
                        self.nodes_by_code[group_to_code[group]].append(s.ftypes[ftype])
        log.info("Prefetch complete.")
    def getexamples(self,group,all_for_cvt=False,**kwargs):
        check=kwargs.pop('check',self.program.params.check())
        ftype=kwargs.pop('ftype',self.program.params.ftype())
        if self.program.params.cvt() == 'T': # example nodes
            nodes=[s.examples[check] for s in self.program.slices.inslice(
                                                        self.program.db.senses)
                        if s.tonevaluebyframe(check) == group
                        ]
        elif all_for_cvt:
            nodes=[s.ftypes[ftype] for s in self.program.db.senses #any ps-profile
                        if group in s.annotationvaluedictbyftypelang(ftype,
                                                self.program.db.analang).values()
                    ]
        else: # Other FormParent nodes
            nodes=[s.ftypes[ftype] for s in self.program.slices.inslice(
                                                        self.program.db.senses,
                                                        **kwargs)
                        if s.annotationvaluebyftypelang(ftype,
                                                    self.program.db.analang,
                                                    check
                                                        ) == str(group) #result str
                    ]
        return nodes
    def clear_cache(self,**kwargs):
        code=self.program.alphabet.verificationcode(**kwargs)
        if code in self.nodes_by_code:
            del self.nodes_by_code[code]
    def getexample(self,group,**kwargs):
        # verificationcode fills in current values where not specified:
        code=self.program.alphabet.verificationcode(**{**kwargs,'group':group})
        if code in self.nodes_by_code:#don't keep rerunning this on a given boot
            nodes=self.nodes_by_code[code]
        else:
            nodes=self.getexamples(group,**kwargs)
        if not nodes:
            # log.error("getexample has no example nodes for group={group}?".format(group=group))
            return 0,None
        n=len(nodes)
        # log.info("{n} nodes found by ExampleDict.getexample".format(n=n))
        exs_ok={i for i in nodes if self.exampletypeok(i,**kwargs)}
        # log.info("found {n} examples with sound files".format(n=len(exs_ok)))
        if kwargs.get('wsoundfile'):
            exs_ok_wo_soundfile={i for i in nodes
                            if self.exampletypeok(i,
                                            **{**kwargs, 'wsoundfile': False}
                                                )}
        else:
            exs_ok_wo_soundfile=set()
        # log.info("found {n} examples w/o sound files".format(n=len(exs_ok_wo_soundfile)))
        # include all, but with sound files first. Prioritize; give full count
        nodes=list(exs_ok)+list(exs_ok_wo_soundfile-exs_ok)
        if code in self and self[code] in nodes: #if stored value is in group
            # log.info("found stored example")
            if not kwargs['renew']:
                # log.info("returning stored example")
                node=self[code]
                kwargs['renew']=True
            else:
                # log.info("renewing stored example")
                txt=[_("Resetting to"),_("{code} example ({value}), of "
                            "{n} examples with kwargs={kwargs}").format(code=code, value=self[code], n=len(nodes), kwargs=kwargs)]
                i=nodes.index(self[code])
                if not kwargs.get('goback'):
                    txt.insert(1,_("next"))
                    if i == len(nodes)-1: #loop back on last
                        node=nodes[0]
                    else:
                        node=nodes[i+1]
                else:
                    txt.insert(1,_("previous"))
                    if i == 0: #loop back on last
                        node=nodes[len(nodes)-1]
                    else:
                        node=nodes[i-1]
                log.info(' '.join(txt))
        else:
            # log.info("Did not find stored example")
            node=nodes[0]
        self[code]=node #store for next iteration
        return len(nodes),node #self._outdict
    def get_button_data(self, group, **kwargs):
        """Return display data for a sort button, or None if no example.
        Keeps LIFT node traversal and text formatting in the backend."""
        kwargs=exampletype(**kwargs)
        n, node = self.getexample(group, **kwargs)
        if node is None:
            return {'count': n}
        text = node.formatted(
            self.program.params.analang(),
            self.program.settings.glosslangs,
            ftype=self.program.params.ftype(),
            frame=self.program.toneframes.get(
                        self.program.params.check()),
            showtonegroup=kwargs.get('showtonegroup', False))
        return {
            'count': n,
            'text': text,
            'audio_url': node.audiofileURL if node.audiofileisthere else None,
            'sense': node.sense,
        }
    def __init__(self,program):
        super(ExampleDict, self).__init__({})
        self.nodes_by_code={}
        self.program=program
        self.program.examples=self

class Analysis(object):
    """Currently for tone, but sorting out values by group"""
    """The following two functions analyze the similarity of UF groups and
    locations/checks with respect to the correlation between other and
    the surface tone group value for that UF-check combination."""
    def allvaluesbycheck(self):
        self.valuesbycheck=dictofchilddicts(self.valuesbygroupcheck,
                                                remove=['NA',None])
    def allvaluesbygroup(self):
        self.valuesbygroup=dictofchilddicts(self.valuesbycheckgroup,
                                                remove=['NA',None])
    def compareUFs(self): #was prioritize
        """Prioritize groups by similarity of location:value pairings"""
        """This is already in the order to compare"""
        self.comparisonUFs=dictscompare(self.valuesbygroupcheck,
                                        ignore=['NA',None,'None'],
                                        flat=False)
        self.orderedUFs=flatten(self.comparisonUFs)
        log.debug(_("structured groups: {groups}").format(groups=self.comparisonUFs))
    def comparechecks(self):
        """Prioritize locations by similarity of location:value pairings"""
        """we need to switch the hierarchy to make this comparison"""
        vbcg=self.valuesbycheckgroup={}
        for group in self.valuesbygroupcheck:
            for check in self.valuesbygroupcheck[group]:
                """This removes the 'values' layer, and promotes check
                above group"""
                try:
                    vbcg[check][group]=self.valuesbygroupcheck[group][check]
                except KeyError:
                    vbcg[check]={}
                    vbcg[check][group]=self.valuesbygroupcheck[group][check]
        self.comparisonchecks=dictscompare(vbcg,
                                            ignore=['NA',None,'None'],
                                            flat=False)
        self.orderedchecks=flatten(self.comparisonchecks)
        log.debug(_("structured locations: {locs}").format(locs=self.comparisonchecks))
    def checkgroupsbysense(self):
        """outputs dictionary keyed to [sense][location]=group"""
        self.sensedict={}
        for sense in self.senses:
            self.sensedict[sense]={}
            for check in self.checks:
                group=sense.tonevaluebyframe(check)
                if group: #store location:group by sense
                    self.sensedict[sense][check]=[group]
        # log.info(_("Done collecting groups by location for each sense."))
        return self.sensedict
    def sorttoUFs(self):
        """Input is a dict keyed by location, valued with location:group dicts
        Returns groups by location:value correspondences."""
        # This is the key analytical step that moves us from a collection of
        # surface forms (each pronunciation group in a given context) to the
        # underlying form (which behaves the same as others in its group,
        # across all contexts).
        if not hasattr(self,'sensedict'):
            log.error(_("You have to run checkgroupsbysense first"))
            return
        unnamed={}
        # Collect all unique combinations of location:group pairings.
        # log.info(_("sensedict: {sensedict}").format(sensedict=self.sensedict))
        for sense in self.sensedict:
            #sort into groups by dict values (combinations location:group pairs)
            k=str(self.sensedict[sense])
            try:
                unnamed[k].append(sense)
            except KeyError:
                unnamed[k]=[sense]
        # log.info(_("Done collecting combinations of groups values "
        #         "by location: {unnamed}").format(unnamed=unnamed))
        # self.groups={}
        self.valuesbygroupcheck={}
        self.sensesbygroup={}
        ks=list(unnamed) #keep sorting order
        for k in ks:
            x=ks.index(k)+1
            name=self.ps+'_'+self.profile+'_'+str(x)
            self.valuesbygroupcheck[name]=ofromstr(k) #return str to dict
            self.sensesbygroup[name]=unnamed[k]
            for sense in unnamed[k]:
                sense.uftonevalue(name)
        # log.info(_("Done adding senses to groups."))
        # return self.groups
    def tonegroupsbyUFcheckfromLIFT(self):
        #returns dictionary keyed by [group][location]=groupvalue
        values=self.valuesbygroupcheck={}
        # Collect check:value correspondences, by sense
        for group in self.sensesbygroup:
            values[group]={}
            for sense in self.sensesbygroup[group]:
                for check in sense.examples:
                    try:
                        values[group][check].add(sense.tonevaluebyframe(check))
                    except KeyError:
                        values[group][check]=set([sense.tonevaluebyframe(check)])
            #maybe need this:
            for check in values[group]:
                values[group][check]=[i for i in values[group][check] if i]
            # log.info(_("values[{group}][{check}]: {values}").format(group=group,check=check,
            #                                     values=values[group][check]))
        # log.info(_("Done collecting groups by location/check for each UF group."))
    def sensesbyUFsfromLIFT(self):
        """This returns a dict of {UFtonegroup:[senses]}"""
        log.debug(_("Looking for sensids by UF tone groups for {profile}-{ps}").format(
                    profile=self.profile, ps=self.ps
                    ))
        self.sensesbygroup={g:[s for s in self.senses if s.uftonevalue() == g]
                            for g in set([s.uftonevalue() for s in self.senses])
                            if g}
        return self.sensesbygroup
    def donoUFanalysis(self):
        log.info(_("Reading tone group analysis from UF tone fields"))
        self.sensesbyUFsfromLIFT() # > self.sensesbygroup
        self.tonegroupsbyUFcheckfromLIFT() # > self.valuesbygroupcheck
        self.doanyway()
    def do(self):
        log.info(_("Starting tone group analysis from lift examples"))
        self.checkgroupsbysense() # > self.sensedict
        self.sorttoUFs() # > self.sensesbygroup and self.valuesbygroupcheck
        self.program.db.write()
        self.doanyway()
        self.program.status.last('analysis',update=True)
        self.program.status.store()
    def doanyway(self):
        """compare(x=UFs/checks) give self.comparison(x) and self.ordered(x)"""
        self.comparechecks() #also self.valuesbygroupcheck -> …checkgroup
        self.compareUFs()
        self.allvaluesbycheck() # >self.valuesbycheck
        self.allvaluesbygroup() # >self.valuesbygroup
    def setslice(self,**kwargs):
        self.ps=kwargs.get('ps',self.program.slices.ps())
        self.profile=kwargs.get('profile',self.program.slices.profile())
        self.checks=self.program.status.checks(ps=self.ps,profile=self.profile)
        self.senses=self.program.slices.senses(ps=self.ps,profile=self.profile)
    def __init__(self, program, **kwargs):
        super(Analysis, self).__init__()
        self.program=program
        self.analang=self.program.db.analang
        self.setslice(**kwargs)

class SliceDict(dict):
    """This stores and returns current ps and profile only; there is no check
    here that the consequences of the change are done (done in check)."""
    def count(self):
        # _profile/_ps may not exist yet: a sort task can be loaded before the
        # slices are built, and cvt='S' tracks its slice in _S_profile_class (not
        # _profile) so _profile is never set. Treat "no slice yet" as count 0.
        # (A dedicated syllable SliceDict would remove this special-casing.)
        try:
            return self[(self._profile,self._ps)]
        except (KeyError, AttributeError):
            return 0
    def scount(self,scount=None):
        """This just stores/returns the values in a dict, keyed by [ps][s]"""
        if scount is not None:
            self._scount=scount
        return self._scount
    def makepsok(self):
        pss=self.pss()
        if not pss:
            self._ps=None #only before data collection
            log.info(_("I don’t have a ps to use; I hope that’s OK!"))
        elif not hasattr(self,'_ps') or self._ps not in pss:
            self.ps(pss[0])
    def makeprofileok(self):
        if not hasattr(self,'_ps'):
            self.makepsok()
        profiles=self.profiles()
        if not profiles:
            self._profile=None #only before data collection
            log.info(_("I don’t have a profile to use; I hope that’s OK!"))
            return
        try:
            profiles+=self.adhoc()[self._ps].keys()
        except KeyError:
            # log.info(_("There seem to be no ad hoc {ps} groups.").format(ps=self._ps))
            pass #don't care
        if (not hasattr(self,'_profile')
                or self._profile not in profiles):
            self.profile(profiles[0])
    def pss(self):
        """This comes from pspriority, so will be limited
        by self.maxpss"""
        return getattr(self,'_pss',[])
    def ps(self,ps=None):
        pss=self.pss()
        if ps and ps in pss:
            """This needs to renew checks, if t == 'T'"""
            self._ps=ps
            self.makeprofileok() #keyed by ps
            self.renewsenses()
        elif ps:
            log.error(_("You asked to change to ps {ps}, which isn’t in the list "
                        "of pss: {pss}").format(ps=ps,pss=pss))
        elif hasattr(self,'_ps'):
            return self._ps
        else:
            log.error(_("You asked for the ps, but I don’t have any (pss: {pss})"
                        "").format(pss=pss))
    def profiles(self,ps=None):
        """This returns profiles for either a specified ps or the current one.
        For cvt='S' the 'profiles' (slices) are the Beg+count+End profile classes
        present in the ps — DERIVED from the words' primitive annotations. Read
        from the WHOLE ps wordlist (db.sensesbyps), not _profilesbysense, so a
        profile class whose words are all still unprofiled still shows up (its
        words need sorting)."""
        if not ps:
            ps=self.ps()
        if self.program.params.cvt()=='S':
            params=self.program.params
            pcs={params.profile_class_of_sense(s)
                            for s in self.program.db.sensesbyps.get(ps,[])}
            pcs.discard(None)
            return sorted(pcs)
        if ps and ps in self._profiles:
            # log.info(_("returning profiles: {profiles}").format(profiles=self._profiles[ps]))
            return self._profiles[ps]
        else:
            return []
    def profile(self,profile=None):
        # For cvt='S' the slice is a Beg+count+End profile class, not a CV
        # profile. The 3 primitive checks (#C/C#/syls) run on the whole wordlist
        # (sentinel profile); the profile check runs within the current
        # profile class. See docs/sort_syllables_design.md.
        params=self.program.params
        if params.cvt()=='S':
            sentinel=params.SYLLABLE_SLICE_SENTINEL
            if profile is None: #getter
                if params.is_syllable_primitive_check():
                    return sentinel
                return getattr(self,'_S_profile_class',None) or sentinel
            self._S_profile_class=profile #setter: the current profile-class slice
            self.renewsenses()
            return
        if profile and profile in self.profiles(self._ps):
            self._profile=profile
            self.renewsenses()
        else:
            # self.makeprofileok() #is this actually needed here? check elsewhere
            return getattr(self,'_profile',None)
    def nextps(self):
        pss=self.pss()
        try:
            index=sepss.index(self._ps)
            if index+1 == len(pss):
                self.ps(pss[0]) #cycle back
            else:
                self.ps(pss[index+1])
        except ValueError: #i.e., it's not in the list
            self.makepsok()
        return self.ps()
    def slicepriority(self,arg=None):
        """arg is to throw away, rather than break a fn where others get
        and set. This is now calculated, not read from file and set here."""
        self.validate()
        self._sliceprioritybyps={}
        try:
            s=self._slicepriority=[x for x in self._valid.items()]
            s.sort(key=lambda x: int(x[1]),reverse=True)
            # log.info(_("self._slicepriority: {priority}").format(priority=self._slicepriority))
            # log.debug(_("self._valid: {valid}").format(valid=self._valid))
            for ps in dict.fromkeys([x[1] for x in self._valid]):
                s=self._sliceprioritybyps[ps]=[x for x in self._valid.items()
                                                            if x[0][1] == ps]
                s.sort(key=lambda x: int(x[1]),reverse=True)
                # log.info(_("self._sliceprioritybyps[{ps}]: {priority}"
                #             "").format(ps=ps,priority=self._sliceprioritybyps[ps]))
        except Exception as e:
            log.error(_("Most likely a non-integer found when looking for an "
                        "integer in {s} (error: {e})").format(s=s,e=e))
    def pspriority(self):
        if self._slicepriority is not None:
            self._pss=list(dict.fromkeys([x[0][1]
                                for x in self._slicepriority]))[:self.maxpss]
    def profilepriority(self):
        if not hasattr(self,'_profiles'):
            self._profiles={}
        for ps in self.pss():
            slicesbyhzbyps=self._sliceprioritybyps[ps]
            if slicesbyhzbyps is not None:
                self._profiles[ps]=list(dict.fromkeys([x[0][0]
                                for x in slicesbyhzbyps]))[:self.maxprofiles]
    def valid(self, ps=None):
        if ps is None:
            return self._valid
        elif ps in self._validbyps:
            return self._validbyps[ps]
        else:
            log.error(_("You asked for valid ps data, but that ps isn’t there."))
    def validate(self):
        #These are keyed by (profile,ps) tuples
        self._valid={}
        self._validbyps={}
        # log.info(_("slices: {length} ({content})").format(length=len(self),content=list(self)[:10]))
        for k in [x for x in self if x[0] != 'Invalid']:
            self._valid[k]=self[k]
        # log.info(_("slices valid: {length} ({content})").format(length=len(self._valid),
        #                                         content=list(self._valid)[:10]))
        for ps in dict.fromkeys([x[1] for x in self._valid]):
            self._validbyps[ps]=[x for x in self._valid if x[1] == ps]
        # log.info(_("slices validbyps: {length} ({content})").format(length=len(self._validbyps),
        #                                             content=list(self._validbyps)[:10]))
        # log.info(_("valid: {valid}").format(valid=self._valid))
        # log.info(_("validbyps: {validbyps}").format(validbyps=self._validbyps))
    def inslice(self,s=None,**kwargs):
        senses=self.senses(**kwargs) #if no kwargs, returns current
        if not s:
            return set(senses)
        elif isinstance(s,lift.Sense):
            return set(senses).intersection(set([s]))
        elif hasattr(s, '__iter__'):
            return set(senses).intersection(set(s))
        else:
            log.error(_("Not sure what happened here!"))
    def senses(self,**kwargs): #ps=None,profile=None,
        # cvt='S': sentinel profile → the whole wordlist (the 3 primitive
        # checks); a profile-class profile → just the words in that Beg+count+End
        # slice (the profile check). See sort_syllables_design.md.
        params=self.program.params
        if params.cvt()=='S':
            ps=kwargs.get('ps',self._ps)
            # 'S' works the WHOLE ps wordlist — NOT _profilesbysense/_sensesbyps,
            # which hold only words with a CONFIRMED cvprofile (getprofileofsense
            # adds a word only when `confirmed`). Syllable sorting's JOB is to give
            # unprofiled words a profile, so they MUST appear here — as UNSORTED
            # (no lc annotation → white border → presented to sort). Bucketing is
            # by profile class (the confirmed primitives), independent of cvprofile.
            # (This restores the documented intent; the old _sensesbyps read
            # silently hid every unprofiled word from the board and maybesort.)
            allps=self.program.db.sensesbyps.get(ps,[])
            profile=kwargs.get('profile',self.profile())
            if not profile or profile==params.SYLLABLE_SLICE_SENTINEL:
                return allps
            return [s for s in allps if params.profile_class_of_sense(s)==profile]
        if not kwargs:
            return self._senses #this is always the current slice
        ps=kwargs.get('ps',self._ps)
        profile=kwargs.get('profile',self._profile)
        if ps in self._profilesbysense and profile in self._profilesbysense[ps]:
            return self._profilesbysense[ps][profile]
            # return list(self._profilesbysense[ps][profile]) #specified slice
        else:
            return []
    def makesensesbyps(self):
        """These are not distinguished by profile, just ps"""
        self._sensesbyps={}
        for ps in self._profilesbysense:
            self._sensesbyps[ps]=[]
            for prof in self._profilesbysense[ps]:
                self._sensesbyps[ps]+=self._profilesbysense[ps][prof]
    def renewsenses(self):
        self._senses=[]
        if self.program.params.cvt()=='S':
            #'S' current slice = whole wordlist (primitives) or the current
            # profile class (profile check); senses() resolves which.
            self._senses=list(self.senses(ps=self._ps))
            return
        try:
            self._senses+=list(self._profilesbysense[self._ps][self._profile])
        except KeyError:
            log.info(_("assuming {profile} is an ad hoc profile.").format(profile=self._profile))
        try:
            self._senses+=list(self._adhoc[self._ps][self._profile])
        except KeyError:
            log.info(_("assuming {profile} is a regular profile.").format(profile=self._profile))
    def adhoc(self,ids=None, **kwargs):
        """If passed ids, add them. Otherwise, return dictionary."""
        if ids is not None:
            ps=kwargs.get('ps',self.ps())
            profile=kwargs.get('profile',self.profile())
            if ps not in self._adhoc:
                 self._adhoc[ps]={}
            self._adhoc[ps][profile]=ids
        return self._adhoc
    def adhoccounts(self,ps=None):
        if ps is None:
            ps=self._ps
        if not hasattr(self,'_adhoccounts'):
            self.updateadhoccounts()
        if not self._adhoccounts:
            return {}
        # return [x for x in self._adhoccounts if x[1] == ps]
        return self._adhoccounts #this should return a dictionary
    def updateadhoccounts(self):
        """This iterates across self._adhoc to provide counts for each
        ps-profile combination (aggregated for profile='Invalid'??!?)
        it should only be called when creating/adding to self.profilesbysense"""
        profilecountInvalid=0
        wcounts=list()
        for ps in self._adhoc:
            for profile in self._adhoc[ps]:
                count=len(self._adhoc[ps][profile])
                wcounts.append((count, profile, ps))
        self._adhoccounts={}
        for i in sorted(wcounts,reverse=True):
            self._adhoccounts[(i[1],i[2])]=i[0]
    def updateslices(self):
        """This iterates across self.profilesbysense to provide counts for each
        ps-profile combination (aggravated for profile='Invalid')
        It sets this dictionary class with k:v of (profile,ps):count.
        it should only be called when creating/adding to self.profilesbysense"""
        profilecountInvalid=0
        wcounts=list()
        for ps in self._profilesbysense:
            for profile in self._profilesbysense[ps]:
                if profile == 'Invalid':
                    profilecountInvalid+=len(self._profilesbysense[ps][profile])
                else:
                    count=len(self._profilesbysense[ps][profile])
                    wcounts.append((count, profile, ps))
        for i in sorted(wcounts,reverse=True):
            self[(i[1],i[2])]=i[0] #[(profile, ps)]=count
        e=_("Found {count} valid data slices: {keys}"
            ).format(count=len(wcounts),keys=list(self.keys())[:10])
        e+='\n'+_("Invalid entries found: {invalid}/{total}").format(invalid=profilecountInvalid,
                                                        total=sum(self.values(),
                                                        profilecountInvalid))
        if (self.program.db.analangs and not len(wcounts)
                and profilecountInvalid):
            # entries were analyzed and ALL failed to slice — a real problem
            # (probably the analysis language). 0 slices from 0 entries (a
            # fresh project before collection) is expected: log only, no
            # modal (the "Found 0 valid data slices: [] / 0/0" nag).
            e+='\n'+_("This may be a problem with your analysis language: {lang}"
                    "").format(lang=self.program.db.analang)
            e+='\n'+_("Or a problem with your database.")
            ErrorNotice(e,title=_("Data Problem!"),wait=True)
        log.info(e)
    def __init__(self,adhoc,profilesbysense,program): #dict
        """The slice dictionary depends on check parameters (and not vice versa)
        because changes in slice options (ps or profile) change check options,
        and not vice versa (check options are only presented based on current
        cvt and slice)"""
        self.program=program
        self.program.slices=self
        super(SliceDict, self).__init__()
        self.profilecountsValid=0
        self.profilecounts=0
        self.maxprofiles=None
        self.maxpss=None #This only seems to be used in pspriority
        self._adhoc=adhoc
        self.analang=self.program.db.analang
        if self.analang != profilesbysense['analang']:
            log.error(_("Problem: {analang} != {profile_analang}").format(analang=self.analang, profile_analang=profilesbysense['analang']))
            raise
        self._profilesbysense={k:v for k,v in profilesbysense.items()
                                                if k not in ['analang','ftype']}
        if not self._profilesbysense:
            ErrorNotice(_("There doesn’t seem to be any profile data, but "
                        "you asked for a slice dictionary. This is a problem; "
                        "please report it!"))
        self.updateslices() #any time we add to self._profilesbysense
        """These two are only done here, as the only change with new data"""
        self.slicepriority()
        self.pspriority()
        self.profilepriority() #this is a dict with ps keys, so can do once.
        self.makesensesbyps()
        """This will be redone, but should be done now, too."""
        self.makeprofileok() #so the next won't fail
        self.renewsenses()
        self.program.settings.settingsobjects() #should do this more; can be redone!

# Syllable PREP (Task 1) slicing — see docs/syllable_sort_redesign.md. Each group
# of the three primitive checks (#C/C#/syls) is cut into STABLE slices of at most
# MAX_SLICE words, so each verify is one modest, image-bearing list that builds
# like a normal segmental verify group (which works). Smaller = lighter build =
# fewer CAWL images loaded at once (each ~0.4s, and a big batch floods XWayland).
# Tunable via the 'syllable_max_slice' setting; raise it if your box is happy with
# larger slices, lower it if a slice is slow to appear.
MAX_SLICE=50 #default words-per-page; tune via the 'syllable_max_slice' setting
             #(raise for fewer/longer pages, lower for lighter ones). With
             #virtualized verify (1.3.32) the RENDER is ~visible-rows not ×N, so
             #slice size mainly trades page count against per-page image load.
             #Ceiling: rows×rowheight must stay under the X11 32767px scroll cap.
PRELOAD_LOOKAHEAD=2 #default # of upcoming slices to decode ahead in background
                    #(override via 'syllable_preload_lookahead')

class SyllableSliceDict(object):
    """Stable, per-group slicing for the syllable PREP task (Task 1). Deliberately
    NOT a SliceDict subclass and NOT program.slices: the CV-profile SliceDict
    stays C/V/T-only (plus the kept profile-class branches Task 2 reuses), and the
    prep slices live in their own object so the two never share an attribute set.

    Three independent partition checks, each over the whole wordlist for the ps:
        #C  word-initial  C/V   (groups 'C'→#C, 'V'→#V)
        C#  word-final    C/V   (groups 'C'→C#, 'V'→V#)
        syls syllable count     (groups '1','2','3',…)
    Each group's words are sorted whole-word (reversed for the word-final check)
    and packed into slices of ≤cap. A word's slice index is SESSION-LOCAL (held in
    self._idx, never written to the LIFT), so within a session slices are stable:
    removing a word shrinks its slice (no re-verify); only ADDING a word (a misfit
    moved in) needs the target slice re-verified. Across a restart the index is
    gone and slices recompute deterministically from the durable LIFT membership —
    same inputs give the same boundaries, so they only differ if words changed
    between sessions. Verify state per (group, slice) is the synthetic group id in
    the StatusDict node (persisted in data.json) but is itself a cache: build()
    re-derives 'done' from each word's primitive verification, so the durable
    truth — membership (<check> annotation) and confirmation (verification field)
    — is all in the LIFT. See docs/adr/0001-syllable-slice-index-ephemeral.md.
    """
    CHECKS=('#C','C#','syls')
    SEP='␟' #unit-separator: joins group+slice into a synthetic id, collision-free

    def __init__(self,program,ps,ftype):
        self.program=program
        self.ps=ps
        self.ftype=ftype
        self.analang=program.db.analang
        # Session-local slice index: {check: {sense_id: idx}}. NOT persisted —
        # the slice/page assignment is packing state, not a lexical fact, so it
        # is recomputed from the durable LIFT data (group membership + primitive
        # verification) each session. See docs/adr/0001-syllable-slice-index-ephemeral.md.
        self._idx={}
        self._cursor=None # last slice served by next_unverified_slice, so the
                          # verify pass walks forward and only wraps for re-opened
                          # slices at the end (not cutting back after each one)
        program.syllable_slices=self

    @property
    def max_slice(self):
        # attribute on the (legacy) Settings object, set by settings.setmaxslice and
        # persisted via DOMAIN_MAPPING['ui'] — like buttoncolumns. (settings has no
        # .get(); the old settings.get() call here silently fell back, so the setting
        # never actually applied.)
        v=getattr(self.program.settings,'syllable_max_slice',None)
        try:
            return int(v) if v else MAX_SLICE
        except (TypeError,ValueError):
            return MAX_SLICE

    @property
    def preload_lookahead(self):
        try:
            v=self.program.settings.get('syllable_preload_lookahead')
        except Exception:
            v=None
        return int(v) if v is not None and str(v).lstrip('-').isdigit() \
            else PRELOAD_LOOKAHEAD

    @property
    def sentinel(self):
        return self.program.params.SYLLABLE_SLICE_SENTINEL

    # --- synthetic id <-> (group, slice-index) ---
    def encode(self,group,idx):
        return '{}{}{}'.format(group,self.SEP,idx)
    def decode(self,sid):
        group,_sep,idx=str(sid).partition(self.SEP)
        return group,(int(idx) if idx.isdigit() else None)

    # --- per-word slice index: SESSION-LOCAL, never written to the LIFT ---
    # The index is packing state (which ≤cap page a word landed on), not a fact
    # about the word. Boundaries stay stable WITHIN a session (assign_slices only
    # fills words that have no index yet) and are recomputed deterministically
    # each session from the durable LIFT data. Group membership lives in the
    # <check> annotation and confirmation in the primitive verification field, so
    # nothing is lost across a restart — only the page boundaries recompute.
    def _slice_idx(self,sense,check):
        return self._idx.get(check,{}).get(sense.id)
    def _set_slice_idx(self,sense,check,idx):
        self._idx.setdefault(check,{})[sense.id]=int(idx)
    def _group_of(self,sense,check):
        return sense.annotationvaluebyftypelang(self.ftype,self.analang,check)

    # --- live membership (annotation-derived, so shrink/grow are free) ---
    def _psenses(self):
        # PREP is wordlist-wide: the three primitives are ps-independent form
        # facts, so membership spans ALL parts of speech, not self.ps. (Name kept
        # for churn; self.ps is now just a staleness token for the rebuild check.)
        try:
            return self.program.db.senses
        except (AttributeError,KeyError):
            return []
    def _members(self,check,group):
        return [s for s in self._psenses() if self._group_of(s,check)==group]
    def groups_of(self,check):
        gs={self._group_of(s,check) for s in self._psenses()}
        gs.discard(None); gs.discard('')
        if check=='syls':
            return sorted(gs,key=lambda g:(0,int(g)) if str(g).isdigit() else (1,str(g)))
        return sorted(gs) #'C' before 'V'
    def members_in_slice(self,check,group,idx):
        return [s for s in self._members(check,group)
                if self._slice_idx(s,check)==idx]
    def count(self,check,group,idx):
        return len(self.members_in_slice(check,group,idx))
    def slices_of(self,check,group):
        idxs={self._slice_idx(s,check) for s in self._members(check,group)}
        idxs.discard(None)
        return sorted(idxs)

    # --- whole-word sort key (reversed for the word-final check) ---
    def slice_key(self,check,sense):
        try:
            w=(sense.formattedform(self.analang,self.ftype) or '').casefold()
        except Exception:
            w=''
        return w[::-1] if self.program.params.is_word_final_check(check) else w

    # --- stable assignment: only fill words that have no slice index yet ---
    def assign_slices(self,check):
        cap=self.max_slice
        for group in self.groups_of(check):
            members=self._members(check,group)
            counts={}; unassigned=[]
            for s in members:
                idx=self._slice_idx(s,check)
                if idx is None:
                    unassigned.append(s)
                else:
                    counts[idx]=counts.get(idx,0)+1
            if not unassigned:
                continue
            # Mirror move_misfit so a from-scratch rebuild reproduces the
            # interactive layout from durable data alone (membership annotation +
            # the spelling-derived value): words whose SPELLING agrees with this
            # group sort in naturally (alphabetised with everyone); by-ear-only
            # members (spelling says another group — or unanalysable) go to the
            # END, so they fall into the last slice(s) as a cohort to re-verify.
            # See docs/adr/0001-syllable-slice-index-ephemeral.md.
            agreeing=[]; exceptions=[]
            for s in unassigned:
                (agreeing if self._orthographic_value(s,check)==group
                          else exceptions).append(s)
            agreeing.sort(key=lambda s:self.slice_key(check,s))
            exceptions.sort(key=lambda s:self.slice_key(check,s))
            max_idx=max(counts) if counts else -1
            for s in agreeing+exceptions:
                placed=False
                for i in range(0,max_idx+1):
                    if counts.get(i,0)<cap:
                        counts[i]=counts.get(i,0)+1
                        self._set_slice_idx(s,check,i); placed=True; break
                if not placed:
                    max_idx+=1; counts[max_idx]=1
                    self._set_slice_idx(s,check,max_idx)

    # --- StatusDict node for a check's slice verify-state (synthetic ids) ---
    def _node(self,check):
        # Wordlist-wide: verify state under the SYLLABLE_PREP_PS sentinel, shared
        # across all ps (NOT self.ps) — so a slice is verified once, not per-ps.
        return self.program.status.node(cvt='S',
                                        ps=self.program.params.SYLLABLE_PREP_PS,
                                        profile=self.sentinel,check=check)
    def _clear_slices(self,check):
        """Drop this check's session-local slice indices so assign_slices reassigns
        from scratch. Called when the cap changed (a deliberate, pre-verify
        reshape); it's also the natural starting state each session, since the
        in-memory index begins empty and is rebuilt from the LIFT membership."""
        self._idx[check]={}
    def build(self):
        """Assign any unsliced words and sync each check's node 'groups' to the
        current synthetic slice ids (emptied slices simply drop out). Idempotent,
        and the entry point that (re)builds the session-local index from the LIFT
        membership — on a fresh session every word is unassigned, so this packs
        them all. If the cap changed since the last build (the 'syllable_max_slice'
        setting was edited mid-session), re-slice that check once so the new cap
        takes effect — within-session indices are otherwise sticky. A normal misfit
        may push a slice one over the cap; that does NOT re-slice (the stored cap is
        unchanged), so stable slices stay stable. Writes NO LIFT data (the index is
        in-memory); the only persisted output is the node cache in data.json."""
        cap=self.max_slice
        changed=False # build() now runs on every prep-board render; only persist
                      # the node cache to data.json when it actually changed.
        for check in self.CHECKS:
            n=self._node(check)
            if n.get('slice_cap')!=cap:
                self._clear_slices(check) #cap changed → re-slice from scratch
                n['slice_cap']=cap; changed=True
            self.assign_slices(check)
            groups=sorted(self.encode(g,i) for g in self.groups_of(check)
                                           for i in self.slices_of(check,g))
            # 'done' is DERIVED from the LIFT (per-sense primitive verification),
            # so prep status survives a data.json loss and is reconstructed from
            # the standard durable source: a slice is done iff every current
            # member is confirmed for this check.
            done=[self.encode(g,i) for g in self.groups_of(check)
                  for i in self.slices_of(check,g)
                  if self._slice_confirmed(check,g,i)]
            if n.get('groups')!=groups:
                n['groups']=groups; changed=True
            if n.get('done')!=done:
                n['done']=done; changed=True
        if changed:
            self.program.status.store()
    def mark_slice(self,check,group,idx,verified=True):
        # Persist confirmation to the LIFT (per-sense primitive verification code),
        # the durable source of truth; the status 'done' list is a synced cache.
        for s in self.members_in_slice(check,group,idx):
            self._set_confirmed(s,check,group,verified)
        n=self._node(check); sid=self.encode(group,idx)
        done=n.setdefault('done',[])
        if verified and sid not in done:
            done.append(sid)
        elif not verified and sid in done:
            done.remove(sid)
        if sid not in n.setdefault('groups',[]):
            n['groups'].append(sid)
        self.program.status.store()
    def mark_for_reverify(self,check,group,idx):
        # A misfit moved into this slice → it's no longer fully confirmed. 'done'
        # is derived (all members confirmed) and the newcomer carries no code, so
        # the slice is already pending; just drop it from the cache. Do NOT strip
        # the existing members' confirmations (that would discard real user data).
        sid=self.encode(group,idx); n=self._node(check)
        if sid in n.get('done',[]):
            n['done'].remove(sid)
        self.program.status.store()
    # --- per-sense confirmation, durable in the LIFT (status 'done' is its cache) --
    def _confirmed(self,sense,check):
        return any(c.split('=')[0]==check
                   for c in sense.primitiveverification(self.ftype))
    def _set_confirmed(self,sense,check,group,verified=True):
        codes=[c for c in sense.primitiveverification(self.ftype)
               if c.split('=')[0]!=check] #drop any existing code for this check
        if verified:
            codes.append('{}={}'.format(check,group))
        sense.primitiveverification(self.ftype,value=codes)
    def _slice_confirmed(self,check,group,idx):
        members=self.members_in_slice(check,group,idx)
        return bool(members) and all(self._confirmed(s,check) for s in members)

    def _slice_pending(self,check,group,idx):
        return (self.encode(group,idx) not in set(self._node(check).get('done',[]))
                and self.count(check,group,idx)>=1)
    def _first_pending_slice(self):
        for check in self.CHECKS:
            for group in self.groups_of(check):
                for idx in self.slices_of(check,group):
                    if self._slice_pending(check,group,idx):
                        return (check,group,idx)
        return None
    def next_unverified_slice(self):
        # Board-click override (once): jump straight to the chosen slice, and
        # continue the pass from there. Stored on program so it survives the
        # SyllableSliceDict the runcheck rebuild makes between click and 'Sort!'.
        pref=getattr(self.program,'syllable_preferred_slice',None)
        self.program.syllable_preferred_slice=None
        if pref and self._slice_pending(*pref):
            self._cursor=pref
            return pref
        # Finish the CURRENT check before moving to the next section: within a
        # check, walk slices FORWARD from the last one served (all #C=C, then
        # #C=V; etc.) and WRAP to pick up any a misfit re-opened — so we neither
        # cut the user back mid-pass (V4 → C27 → V5…) NOR leave a check early
        # (finishing V# while a C# slice is still pending).
        order=self._slice_order()
        if not order:
            return None
        cur=getattr(self,'_cursor',None)
        if cur and cur[0] in self.CHECKS:
            seq=[t for t in order if t[0]==cur[0]]
            if cur in seq:
                i=seq.index(cur)+1
                seq=seq[i:]+seq[:i] #forward from the cursor, then wrap WITHIN the check
            for t in seq:
                if self._slice_pending(*t):
                    self._cursor=t
                    return t
        # Current check fully verified → the earliest still-pending slice in fixed
        # check order (#C, C#, syls). Normally that's just the next check; but if
        # an EARLIER check still has an unverified slice (e.g. one skipped via a
        # board click), go back THERE rather than skipping ahead to a later check.
        nxt=self._first_pending_slice()
        if nxt:
            self._cursor=nxt
        return nxt

    # --- background preload of upcoming slices (image decode is I/O-bound) ---
    def _slice_order(self):
        """All (check,group,idx) tuples in the order maybeverifysyllables walks
        them — so the preloader fetches exactly what the user will see next."""
        return [(c,g,i) for c in self.CHECKS for g in self.groups_of(c)
                        for i in self.slices_of(c,g)]
    def upcoming_slices(self,check,group,idx,n):
        """The next `n` still-pending slices after (check,group,idx)."""
        order=self._slice_order()
        try:
            start=order.index((check,group,idx))+1
        except ValueError:
            start=0
        out=[]
        for t in order[start:]:
            if len(out)>=n:
                break
            if self._slice_pending(*t):
                out.append(t)
        return out
    def preload_uris(self,check,group,idx,n):
        """Illustration URIs of the words in the next `n` pending slices (deduped,
        order preserved), for SortPresenter.preload_images()."""
        seen=set(); uris=[]
        for c,g,i in self.upcoming_slices(check,group,idx,n):
            for s in self.members_in_slice(c,g,i):
                u=s.illustrationURI(local_only=True) #images are data;
                                        #never fetch at display time
                if u and u not in seen:
                    seen.add(u); uris.append(u)
        return uris
    def all_uris(self):
        """Every slice's illustration URIs across all checks, deduped — for a
        full upfront preload. DIAG (1.3.18): drives the image cache to its full
        size at prep start, to confirm a large cache (~all illustrated words)
        does NOT break small-slice builds (the cache-exoneration test)."""
        seen=set(); uris=[]
        for c,g,i in self._slice_order():
            for s in self.members_in_slice(c,g,i):
                u=s.illustrationURI(local_only=True) #images are data;
                                        #never fetch at display time
                if u and u not in seen:
                    seen.add(u); uris.append(u)
        return uris

    # --- misfit: word flagged out of group A, heard as group B (this check) ---
    def _last_slice_idx(self,check,group):
        idxs=self.slices_of(check,group)
        return idxs[-1] if idxs else 0
    def _bracketing_slice(self,check,group,sense):
        """Existing slice index whose alphabetical neighbour the word sits beside
        (so it sorts in naturally), WITHOUT renumbering anyone."""
        ms=[s for s in self._members(check,group) if s is not sense
            and self._slice_idx(s,check) is not None]
        if not ms:
            return 0
        ms.sort(key=lambda s:self.slice_key(check,s))
        keys=[self.slice_key(check,s) for s in ms]
        pos=bisect.bisect_left(keys,self.slice_key(check,sense))
        neighbour=ms[min(pos,len(ms)-1)]
        return self._slice_idx(neighbour,check)
    def _orthographic_value(self,sense,check):
        """The check's value implied by the word's spelling (the presort rule),
        from the stored cvprofile field — to decide whether a word belongs in a
        group BY SPELLING (vs only by ear). Uses the params helpers (not the live
        task) so it works on the board-render rebuild too."""
        params=self.program.params
        profile=sense.cvprofilevalue(self.ftype)
        if not profile or profile=='Invalid':
            return None
        if check=='#C':
            return params.word_initial(profile)
        if check=='C#':
            return params.word_final(profile)
        if check=='syls':
            return str(params.syllable_count(profile))
        return None
    def move_misfit(self,sense,check,target=None):
        """Move a flagged word to group B. Binary checks: B is the other value.
        Count check: B is the caller-supplied target (Shorter/Longer). Place it by
        recompute-and-compare — natural slice if its spelling matches B, else B's
        last slice — then mark B's slice for re-verify. Group A just shrinks."""
        cur=self._group_of(sense,check)
        if check in ('#C','C#'):
            B='V' if cur=='C' else 'C'
        else:
            B=str(target) if target is not None else cur
        if B==cur:
            return None
        # Pick B's slice BEFORE moving the word in, so it isn't counted as an
        # existing B member (keeps "last slice" honest and avoids stale indices).
        if self._orthographic_value(sense,check)==B:
            idx=self._bracketing_slice(check,B,sense) #sorts in naturally
        else:
            idx=self._last_slice_idx(check,B) #only B by ear → all such at the end
        sense.annotationvaluebyftypelang(self.ftype,self.analang,check,B)
        self._set_slice_idx(sense,check,idx)
        self.mark_for_reverify(check,B,idx) #B gained a member → re-verify it
        return (B,idx)

class StatusDict(dict):
    """This stores and returns current ps and profile only; there is no check
    here that the consequences of the change are done (done in check)."""
    """I should think about what 'do' means here: sort? verify? record?"""
    def task(self,task=None):
        #showing type here is just as good, since it's an object in any case
        #printing the object fails if it is a window that hasn't inited yet
        if task:
            # log.info(_("Setting task {type}").format(type=type(task)))
            self._task=task
        else:
            # log.info(_("Returning task {type}").format(type=type(self._task)))
            return self._task
    def profiletosort(self):
        """Return whether there is a profile that has been unsorted"""
    def checktosort(self,**kwargs):
        check=kwargs.get('check',self.program.params.check())
        cvt=kwargs.get('cvt',self.program.params.cvt())
        ps=kwargs.get('ps',self.program.slices.ps())
        profile=kwargs.get('profile',self.program.slices.profile())
        if (cvt not in self or
                ps not in self[cvt] or
                profile not in self[cvt][ps] or
                check not in self[cvt][ps][profile] or
                self[cvt][ps][profile][check]['tosort'] == True):
            return True
    def checktojoin(self,**kwargs):
        check=kwargs.get('check',self.program.params.check())
        cvt=kwargs.get('cvt',self.program.params.cvt())
        ps=kwargs.get('ps',self.program.slices.ps())
        profile=kwargs.get('profile',self.program.slices.profile())
        if (cvt in self and
                ps in self[cvt] and
                profile in self[cvt][ps] and
                check in self[cvt][ps][profile] and
                ('tojoin' not in self[cvt][ps][profile][check] or #old schema
                self[cvt][ps][profile][check]['tojoin'] == True)):
            return True
    def profiletojoin(self,**kwargs):
        profile=kwargs.get('profile',self.program.slices.profile())
        cvt=kwargs.get('cvt',self.program.params.cvt())
        ps=kwargs.get('ps',self.program.slices.ps())
        checks=self.checks()
        for check in checks: #any check
            if (cvt in self and
                ps in self[cvt] and
                profile in self[cvt][ps] and
                check in self[cvt][ps][profile] and
                ('tojoin' not in self[cvt][ps][profile][check] or #old schema
                self[cvt][ps][profile][check]['tojoin'] == True)):
                return True
    def profiletosort(self,**kwargs):
        profile=kwargs.get('profile',self.program.slices.profile())
        cvt=kwargs.get('cvt',self.program.params.cvt())
        ps=kwargs.get('ps',self.program.slices.ps())
        checks=self.checks()
        for check in checks: #any check
            if (cvt not in self or
                ps not in self[cvt] or
                profile not in self[cvt][ps] or
                check not in self[cvt][ps][profile] or
                self[cvt][ps][profile][check]['tosort'] == True):
                return True
    def nextprofile(self, event=None, **kwargs):
        """This function is here (not in slices) in order for it to be sensitive
        to different kinds of profiles, via **kwargs"""
        # log.info("Running nextprofile")
        kwargs=grouptype(**kwargs)
        # self.makeprofileok()
        profiles=self.profiles(**kwargs)
        if not profiles:
            log.error(_("There are no such profiles! kwargs: {kwargs}").format(kwargs=kwargs))
            return
        """"TypeError: string indices must be integers"""
        profile=self.program.slices.profile()
        nextprofile=profiles[0]
        if profile in profiles:
            idx=profiles.index(profile)
            if idx != len(profiles)-1:
                nextprofile=profiles[idx+1]
        self.program.slices.profile(nextprofile)
        return nextprofile
    def nextcheck(self, event=None, **kwargs):
        kwargs=grouptype(**kwargs)
        check=self.program.params.check()
        checks=self.checks(**kwargs)
        if not checks:
            log.error(_("There are no such checks! kwargs: {kwargs}").format(kwargs=kwargs))
            return
        nextcheck=checks[0] #default
        if check in checks:
            idx=checks.index(check)
            if idx != len(checks)-1: # i.e., not already last
                nextcheck=checks[idx+1] #overwrite default in this one case
        self.program.params.check(nextcheck)
        return nextcheck
    def nextgroup(self, **kwargs):
        kwargs=grouptype(**kwargs)
        group=self.group()
        groups=self.groups(**kwargs)
        log.info(_("At {group} of ({groups}) groups.").format(group=group,groups=groups))
        if not groups:
            log.error(_("There are no such groups! kwargs: {kwargs}").format(kwargs=kwargs))
            return
        nextgroup=groups[0] #default
        if group in groups:
            idx=groups.index(group)
            if idx != len(groups)-1: # i.e., not already last
                nextgroup=groups[idx+1] #overwrite default in this one case
        self.group(nextgroup)
        group=self.group()
        log.info(_("At {group} of ({groups}) groups.").format(group=group,groups=groups))
    def profiles(self, **kwargs):
        kwargs=grouptype(**kwargs)
        profiles=self.program.slices.profiles() #already limited to current ps
        p=[]
        for kwargs['profile'] in profiles:
            checks=self.checks(**kwargs)
            if kwargs['wsorted'] and not checks:
                log.log(4,_("No Checks for this profile, returning."))
                continue #you won't find any profiles to do, either...
            if (
                (not kwargs['wsorted'] and not kwargs['tosort']
                and not kwargs['toverify'] and not kwargs['tojoin']
                ) or
                (kwargs['tosort'] and self.profiletosort(**kwargs)) or
                (kwargs['wsorted'] and [i for j in
                            # [self.groups(profile=profile,check=check,**kwargs)
                            [self.groups(**kwargs)
                            # for check in checks]
                            for kwargs['check'] in checks]
                                        for i in j
                                        ]) or
                (kwargs['toverify'] and [i for j in
                            # [self.groups(profile=profile,check=check,**kwargs)
                            [self.groups(**kwargs)
                            # for check in checks]
                            for kwargs['check'] in checks]
                                        for i in j
                                        ]) or
                kwargs['tojoin'] and self.profiletojoin(**kwargs)
                ):
                p+=[kwargs['profile']]
        # log.info(_("Profiles with kwargs {kwargs}: {profiles}").format(kwargs=kwargs,profiles=p))
        return p
    def allcheckswCVdata(self):
        return list(set([i for j in [self.program.status[cvt][ps][profile]
                                    for cvt in self.program.status
                                    if cvt != 'T'
                                    for ps in self.program.status[cvt]
                                    for profile in self.program.status[cvt][ps]
                                    if ps in self.program.status[cvt]
                                    ]
                                for i in j]))
    def allcheckswdata(self, **kwargs): #needs cvt and ps
        cvt=kwargs.get('cvt',self.program.params.cvt())
        ps=kwargs.get('ps',self.program.slices.ps())
        return list(set([i for j in [self.program.status[cvt][ps][profile]
                                    for profile in self.program.status[cvt][ps]
                                    ]
                            for i in j
                        ]))
    def checks(self, **kwargs):
        """This method is designed for tone, which depends on ps, not profile.
        we'll need to rethink it, when working on CV checks, which depend on
        profile, and not ps."""
        kwargs=grouptype(**kwargs)
        tosortkwargs=kwargs.copy()
        tosortkwargs['tosort']=True
        toverifykwargs=kwargs.copy()
        toverifykwargs['toverify']=True
        tojoinkwargs=kwargs.copy()
        tojoinkwargs['tojoin']=True
        cs=[]
        # No segmental data yet (e.g. a fresh recordings-only import before any
        # citation forms) -> updatechecksbycvt returns None. Treat as "no checks"
        # so the database still opens; makecheckok then unsets the current check.
        checks=self.updatechecksbycvt(**kwargs) or []
        # Correspondence ('x') checks — V1xV2, C1xC2, the CV/VC unit checks, etc.
        # — are a REPORTING construct: the cross-tab chart (e.g. V1×V2), which the
        # report builds by crossing the single-axis V1/V2 groups (docheckreport).
        # They are NOT something to ask the user to sort/verify by, so drop them
        # from a SORT task's check list. Gate on the live task being a sort task
        # (flag-based, replacing the old isinstance(Sort) check) — NOT on "is a
        # report", because reports often run with status.task() unset (None) in a
        # subprocess, and must keep the x-checks. A caller can still force the
        # filter via the no_correspondence_checks kwarg.
        no_corr=kwargs.get('no_correspondence_checks')
        if no_corr is None:
            no_corr=getattr(self.task(),'is_sort_task',False)
        # Correspondence checks exist only for segmental (C/V) types, where
        # check names are machine-generated so a bare 'x' is diagnostic. Tone
        # checks are USER-NAMED frames — a frame called e.g. 'Exists' must not
        # be swallowed by this filter.
        if no_corr and kwargs.get('cvt',self.program.params.cvt()) != 'T':
            checks=[i for i in checks if 'x' not in i]
        if not checks:
            return cs
        for kwargs['check'] in checks:
            tosortkwargs['check']=toverifykwargs['check']=tojoinkwargs['check']=kwargs['check']# log.info("{} tosort: {}".format(kwargs['check'],self.checktosort(**tosortkwargs)))
            # log.info("{} tosort: {}".format(kwargs['check'],self.groups(**toverifykwargs)))
            # log.info("{} tosort: {}".format(kwargs['check'],self.checktojoin(**tojoinkwargs)))
            if (
                (not kwargs['wsorted'] and not kwargs['tosort']
                and not kwargs['toverify']
                and not kwargs['tojoin']
                and not kwargs['todo']
                ) or
                # """These next two assume current ps-profile slice"""
                kwargs['wsorted'] and self.groups(**kwargs) or
                kwargs['tosort'] and self.checktosort(**kwargs) or
                kwargs['toverify'] and self.groups(**kwargs) or
                kwargs['tojoin'] and self.checktojoin(**kwargs) or
                    (kwargs['todo'] and (self.checktosort(**tosortkwargs) or
                                        self.groups(**toverifykwargs) or
                                        self.checktojoin(**tojoinkwargs)
                                        )
                    )
                ):
                cs+=[kwargs['check']]
        # log.info(_("Checks with {kwargs}: {checks}").format(kwargs=kwargs,checks=cs))
        return cs
    def all_groups_verified_anywhere(self):
        d=self.dict()
        # log.info(d)
        # log.info({cvt:set([check #i
        #                 for ps in d[cvt]
        #                 for profile in d[cvt][ps]
        #                 for check in d[cvt][ps][profile]
        #                 # for i in d[cvt][ps][profile][check]['done']
        #                 # if 'done' in d[cvt][ps][profile][check]
        #                 # if i not in ['NA']
        #                 ])
        #         for cvt in d if cvt != 'T'
        #         })
        #prints FIX!
        #{'Noun': {'done', 'recorded', 'last', 'presorted', 'tosort', 
                # 'groups', 'tojoin'}}
        return {cvt:set([i
                        for ps in d[cvt]
                        for profile in d[cvt][ps]
                        for check in d[cvt][ps][profile]
                        for i in d[cvt][ps][profile][check]['done']
                        if 'done' in d[cvt][ps][profile][check]
                        if i not in ['NA']])
                for cvt in d if cvt != 'T'
                }
    def all_groups_verified_for_cvt(self):
        return self.all_groups_verified_anywhere()[self.program.params.cvt()]
    def order_groups(self, groups):
        """Canonical presentation order for groups. Segment/tone groups are
        unrelated labels (plain alphabetical). Syllable profiles (cvt 'S') are
        related, so present them shortest→longest, then alphabetically (similar
        patterns sit together). [Secondary key may grow — see Kent's note.]"""
        if self.program.params.cvt()=='S':
            return sorted(groups, key=lambda g: (len(g), g))
        return sorted(groups)
    def groups(self,g=None, **kwargs):
        # log.info(_("groups kwargs: {kwargs}").format(kwargs=kwargs))
        if kwargs.get('all_for_cvt'): #in this case, nothing else is relevant
            return self.all_groups_verified_for_cvt()
        kwargs=grouptype(**kwargs)
        kwargs=self.checkslicetypecurrent(**kwargs)
        """Without a kwarg, this returns prioritization in advance of sorting,
        before actual sort groups exist. So that usage only has meaning for
        segmental checks, and should not be used for tone. For tone usage,
        ALWAYS specify a kwarg here."""
        """I don't know how to prioritize CV checks yet, if ever..."""
        sn=self.node(**kwargs)
        if kwargs['wsorted']: #this used to be the default: get or set sorted groups
            self._groups=sn['groups']
            if g is not None:
                self._groups=sn['groups']=g
            if not self._groups:
                log.info(_("No groups to sort into! (using {kwargs} node {sn})"
                    ).format(kwargs=kwargs,sn=sn))
                return []
            return self.order_groups(self._groups)
        if kwargs['toverify']:
            #done is always a subset of groupsː
            sn['done']=sorted(set(sn['done'])&set(sn['groups']))
            return self.order_groups(set(sn['groups'])-set(sn['done']))
        if kwargs['torecord']:
            return self.order_groups(set(sn['groups'])-set(sn['recorded']))
        else: #give theoretical possibilities (C or V only)
            """The following two are meaningless, without with kwargs above"""
            if kwargs['cvt'] in ['CV','VC','T']:
                return None
            """This is organized class:(segment,count)"""
            thispsdict=self.program.slices.scount()[kwargs['ps']]
            if kwargs['cvt'] == 'V': #There is so far only one V grouping
                todo=[i[0] for i in thispsdict['V']] #that's all that's there, for now.
            elif kwargs['cvt'] == 'C':
                todo=list() #because there are multiple C groupings
                for s in thispsdict:
                    if s != 'V':
                        todo.extend([i[0] for i in thispsdict[s]])
            todo=sorted(set(todo)|set(sn['groups'])) #either way, add current groups
            # log.info(_("Returning groups: {groups}").format(groups=todo))
            return todo
    def sensestosort(self):
        return getattr(self,'_sensestosort',False) #always return, even w/o attr
    def sensessorted(self):
        return self._sensessorted
    def renewsensestosort(self,todo,done):
        """This takes arguments to remove and rebuild these lists"""
        """todo and done should be lists of senses"""
        """this takes as arguments lists extracted from LIFT by the check"""
        if not hasattr(self,'_sensessorted'):
            self._sensessorted=[]
        if not hasattr(self,'_sensestosort'):
            self._sensestosort=[]
        self._sensessorted.clear()
        self._sensessorted.extend(done)
        self._sensestosort.clear()
        self._sensestosort.extend(todo)
    def marksensesorted(self,sense,**kwargs):
        self._sensessorted.append(sense)
        if sense in self._sensestosort:
            self._sensestosort.remove(sense)
        if not self._sensestosort:
            self.tosort(False,**kwargs) #this marks current, unless specified
            # log.info(_("Tosort now {tosort} (marksensesorted)").format(tosort=self.tosort()))
    def marksensetosort(self,sense,**kwargs):
        self._sensestosort.append(sense)
        if sense in self._sensessorted:
            self._sensessorted.remove(sense)
        self.tosort(True,**kwargs) #this marks current, unless specified
        # log.info(_("Tosort now {tosort} (marksensetosort)").format(tosort=self.tosort()))
    def store(self):
        """This will just store to file; reading will come from check."""
        # log.info(_("Saving status dict to file"))
        self.program.settings.storesettingsfile('status')
    def dict(self): #needed?
        return {k:self[k] for k in self}
    def dictcheck(self,**kwargs):
        kwargs=self.checkslicetypecurrent(**kwargs)
        try:
            """Build this explicitly to avoid recursion group-check-node"""
            """presorted is the most recently added key"""
            t=self[kwargs['cvt']][kwargs['ps']][kwargs['profile']][kwargs['check']]
            s=t['groups']
            s=t['done']
            s=t['recorded']
            s=t['tosort']
        except (KeyError,TypeError):
            self.build(**kwargs)
    def build(self,**kwargs):
        """this makes sure that the dictionary structure is there for work you
        are about to do"""
        kwargs=checkslicetype(**kwargs) #fills in with None
        """Only build up to a None value"""
        """If anything is defined, give no defaults"""
        """Any defined variable after any default is an error"""
        """We don't want to mix default and specified values here, so
        unspecified after specified is None, and not built"""
        if (kwargs['cvt'] is None and kwargs['ps'] is not None
                or kwargs['ps'] is None and kwargs['profile'] is not None
                or kwargs['profile'] is None and kwargs['check'] is not None
                ):
            log.error(_("You have to define all values prior to the last: "
                                    "{kwargs}").format(kwargs=kwargs))
        elif kwargs['cvt'] is not None:
            log.log(4,_("At least cvt value defined; using them: {kwargs}"
                                            "").format(kwargs=kwargs))
        else: #all None:
            for k in ['cvt','ps','profile','check']:
                del kwargs[k]
            kwargs=self.checkslicetypecurrent(**kwargs) #use current values
        changed=False
        """cvt should never be None here. Once an attribute is None, the rest
        should be, too."""
        if not kwargs['cvt']:
            log.error(_("Sorry, no cvt defined! ({cvt})").format(cvt=kwargs['cvt']))
            return
        if kwargs['cvt'] not in self:
            self[kwargs['cvt']]={}
            changed=True
        base=self[kwargs['cvt']]
        if kwargs['ps'] is not None:
            if kwargs['ps'] not in base:
                base[kwargs['ps']]={}
                changed=True
            base=base[kwargs['ps']]
        if kwargs['profile'] is not None:
            if kwargs['profile'] not in base:
                base[kwargs['profile']]={}
                changed=True
            base=base[kwargs['profile']]
        if kwargs['check'] is not None:
            if kwargs['check'] not in base:
                base[kwargs['check']]={}
                changed=True
            base=base[kwargs['check']]
        if None not in [kwargs['ps'],kwargs['profile'],kwargs['check']]:
            if isinstance(base,list):
                log.info(_("Updating {profile}-{check} status dict to new schema").format(
                                            profile=kwargs['profile'],check=kwargs['check']))
                groups=base
                base=self[kwargs['cvt']][kwargs['ps']][kwargs['profile']][
                                                        kwargs['check']]={}
                base['groups']=groups
                base['done']=[]
                base['recorded']=[]
                base['tosort']=True
                base['presorted']=False
                changed=True
            for key in ['groups','done','recorded']:
                if key not in base:
                    log.log(4,_("Adding {key} key to {profile}-{check} status dict").format(
                                        key=key,profile=kwargs['profile'],check=kwargs['check']))
                    base[key]=list()
                    changed=True
            if 'tosort' not in base:
                log.log(4,_("Adding tosort key to {profile}-{check} status dict").format(
                                        profile=kwargs['profile'],check=kwargs['check']))
                base['tosort']=True
                changed=True
            if 'presorted' not in base:
                log.log(4,_("Adding presorted key to {profile}-{check} status dict").format(
                                        profile=kwargs['profile'],check=kwargs['check']))
                base['presorted']=False
                changed=True
        # if changed == True:
        #     self.store()
    def clear_all_groups(self):
        """don't do this except when reloading! This only removes sort groups,
        which can be rebuilt from lift. Leave other stuff alone!"""
        ts=list(self)
        for t in ts:
            pss=list(self[t])
            for ps in pss:
                profiles=list(self[t][ps]) #actual, not theoretical
                for profile in profiles:
                    checks=list(self[t][ps][profile]) #actual, not theoretical
                    for check in checks:
                        node=self[t][ps][profile][check]
                        if 'groups' in node:
                            node['groups'] = []
    def cull(self):
        """This iterates across the whole dictionary, and removes empty nodes.
        Only do this when you're cleaning up, not about to start new work."""
        ts=list(self)
        for t in ts:
            pss=list(self[t])
            for ps in pss:
                profiles=list(self[t][ps]) #actual, not theoretical
                for profile in profiles:
                    # Normal sweep: drop a profile node with NO member words at all
                    # — no sense currently carries this profile (membership of any
                    # kind, not "sorted"/"verified"). Segmental cvts only (their
                    # profile dimension is the CV profile, tracked in db.ps_profiles);
                    # 'S' profile classes/sentinels and not-yet-computed ps are left alone.
                    members=getattr(self.program.db,'ps_profiles',None)
                    if (t!='S' and members is not None and ps in members
                            and profile not in members[ps]):
                        del self[t][ps][profile]
                        continue
                    checks=list(self[t][ps][profile]) #actual, not theoretical
                    for check in checks:
                        node=self[t][ps][profile][check]
                        if type(node) is list:
                            if not node:
                                del self[t][ps][profile][check]
                        elif 'groups' in node and node['groups'] == []:
                            del self[t][ps][profile][check]
                        elif 'done' in node and 'groups' in node:
                            node['done']=sorted(set(node['done']
                                                    )&set(node['groups']))
                        elif 'done' in node: #i.e., w/o groups
                            node['done']=[]
                    if self[t][ps][profile] == {}:
                        del self[t][ps][profile]
                if self[t][ps] == {}:
                    del self[t][ps]
            if self[t] == {}:
                del self[t]
    """The following four methods address where to find what in this dict"""
    def updatechecksbycvt(self,**kwargs):
        """This just pulls the correct list from the dict, and updates params"""
        """It doesn't allow for input, as other fns do"""
        # log.info("Running updatechecksbycvt")
        cvt=kwargs.get('cvt',self.program.params.cvt())
        if cvt not in self._checksdict:
            self._checksdict[cvt]={}
            self.renewchecks(**kwargs)
        if cvt == 'S':
            # The shared engine (Task 2) only does the profile-class PROFILE sort —
            # the current word-form's ftype check. The three primitive checks
            # (#C/C#/syls) are owned by the dedicated Task-1 prep driver
            # (SyllablePrep.maybeverifysyllables) and never ride maybesort. See
            # docs/syllable_sort_redesign.md.
            self._checks=[self.program.params.ftype()]
        elif cvt == 'T':
            """This depends on ps and self.program.toneframes"""
            ps=kwargs.get('ps',self.program.slices.ps())
            if ps not in self._checksdict[cvt]:
                self._checks=[] #there may be none defined
            else:
                self._checks=self._checksdict[cvt][ps]
        else:
            profile=kwargs.get('profile',self.program.slices.profile())
            # log.info(f"Using profile {profile} for updatechecksbycvt")
            if not profile:
                return #if no data yet, no segmental checks, either
            if profile not in self._checksdict[cvt]:
                self.renewchecks(**kwargs) #should be able to find something
            self._checks=self._checksdict[cvt][profile]
        # log.info("Returning these checks: {}".format(self._checks))
        return self._checks
    def renewchecks(self,**kwargs):
        """This should only need to be done on a boot, when a new tone frame
        is defined, or when working on a new syllable profile for CV checks."""
        """This depends on cvt and profile, for CV checks"""
        """replaces self.checkspossible"""
        """replaces setnamesbyprofile"""
        # log.info("Running renewchecks")
        cvt=kwargs.get('cvt',self.program.params.cvt())
        # t=self.program.params.cvt()
        if not cvt:
            log.error("No type is set; can't renew checks!")
        if cvt not in self._checksdict:
            self._checksdict[cvt]={}
        profile=kwargs.get('profile',self.program.slices.profile() if hasattr(self.program,'slices') else '')
        if cvt == 'T':
            for ps in self.program.slices.pss():
                if ps in self.program.toneframes:
                    self._checksdict[cvt][ps]=list(self.program.toneframes[ps])
        elif cvt == 'S':
            # Task 2 (shared engine) does only the profile-class profile check
            # (ftype); the #C/C#/syls primitives are the Task-1 prep driver's.
            # updatechecksbycvt computes this fresh; cached here for completeness.
            ftype=self.program.params.ftype()
            for ps in self.program.slices.pss():
                self._checksdict[cvt][ps]=[ftype]
        elif profile:
            """This depends on profile only"""
            n=profile.count(cvt)
            # log.debug('Found {} instances of {} in {}'.format(n,cvt,profile))
            self._checksdict[cvt][profile]=list()
            for i in range(n): # get max checks and lesser
                if i+1 >6:
                    c=0
                    for ps in self.program.slices.pss():
                            if (profile,ps) in self.program.slices:
                                c+=self.program.slices[(profile,ps)]
                    log.info(_("Not doing checks with more than 6 "
                            "consonants or vowels; there are {count} " "{type} "
                            "in {profile}); "
                            "If you need that, please let me know. "
                            "({words} word(s).)").format(
                                count=i+1,
                                type=self.program.params.cvtdict()[cvt]['pl'],
                                profile=profile,
                                words=c))
                    continue
                """This is a list of (code, name) tuples"""
                syltuples=self.program.params._checknames[cvt][i+1] #range+1 = syl
                self._checksdict[cvt][profile].extend([t[0] for t in syltuples])
                # log.info("Check codes to date: {}".format(
                #                                 self._checksdict[cvt][profile]
                #                                         ))
            self._checksdict[cvt][profile].sort(key=len,reverse=True)
        else:
            log.info("Not Tone and no profile; not returning a check")
        # log.info(f"{self._checksdict[cvt][profile]=}")
    def node(self,**kwargs):
        """This will fail if fed None values"""
        kwargs=self.checkslicetypecurrent(**kwargs)
        if None in [kwargs['cvt'],kwargs['ps'],kwargs['profile'],
                                                            kwargs['check']]:
            log.error(_("None found in {missing} kwarg ({kwargs})").format(missing=[i for i in kwargs
                                                            if not kwargs[i]],
                                                            kwargs=kwargs))
        self.dictcheck(**kwargs)
        return self[kwargs['cvt']][kwargs['ps']][kwargs['profile']][
                                                                kwargs['check']]
    def tojoin(self,v=None,**kwargs):
        kwargs=self.checkslicetypecurrent(**kwargs) # current value defaults
        sn=self.node(**kwargs)
        ok=[None,True,False]
        if 'tojoin' not in sn:
            sn['tojoin']=True
        self._tojoinbool=sn['tojoin']
        if v is not None:
            self._tojoinbool=sn['tojoin']=v
        return self._tojoinbool
    def presorted(self,v=None,**kwargs):
        kwargs=self.checkslicetypecurrent(**kwargs) # current value defaults
        sn=self.node(**kwargs)
        ok=[None,True,False]
        if v not in ok:
            log.error(_("presorted value ({value}) invalid: OK values: {ok}").format(value=v,ok=ok))
        self._presortedbool=sn['presorted']
        if v is not None:
            self._presortedbool=sn['presorted']=v
        return self._presortedbool
    def tosort(self,v=None,**kwargs):
        """This returns whether or not (bool) there are items yet to sort
        in this group of sort items.
        """
        kwargs=self.checkslicetypecurrent(**kwargs) # current value defaults
        sn=self.node(**kwargs)
        ok=[None,True,False]
        if v not in ok:
            log.error(_("Tosort value ({value}) invalid: OK values: {ok}").format(value=v,ok=ok))
        self._tosortbool=sn['tosort']
        if v is not None:
            self._tosortbool=sn['tosort']=v
        return self._tosortbool
    def verified(self,g=None,**kwargs):
        sn=self.node(**kwargs)
        self._verified=sn['done']
        if g is not None:
            log.info(_("verified replacing {done} with {group} for {kwargs}").format(done=sn['done'],group=g,kwargs=kwargs))
            self._verified=sn['done']=g
        return self._verified
    def isdistinguished(self,other_group,**kwargs):
        g=kwargs.get('group') 
        for t in itertools.permutations((g,other_group)):
            if t in self.distinguished(**kwargs):
                return True
    def distinguished(self,**kwargs):
        sn=self.node(**kwargs)
        if 'distinguished' not in sn or sn['distinguished'] == {}:
            sn['distinguished']=set()
        return sn['distinguished']
    def distinguish(self,g, **kwargs):
        self.distinguished(**kwargs).add(g)
    def undistinguish(self,g, **kwargs):
        self.distinguished(**kwargs).discard(g)
    def undistinguish_any_with(self,g, **kwargs):
        # log.info(f"calling self.undistinguish_any_with with {kwargs=}")
        # log.info(f"{self.distinguished(**kwargs)=}")
        for j in [i for i in self.distinguished(**kwargs) if g in i]:
            self.undistinguish(j,**kwargs)
    def pending_distinctions(self,**kwargs):
        """Verified-group pairs on THIS slice not yet distinguished (either
        ordering). Single source of truth for both the join step (to_distinguish)
        and macrosort eligibility: a group is fully distinguished iff it appears in
        NO pending pair — and a lone verified group (no pairs) is trivially done."""
        v=[g for g in self.node(**kwargs).get('done',[]) if g!='NA']
        d={tuple(x) for x in self.distinguished(**kwargs)}
        return {p for p in itertools.combinations(v,2)
                if p not in d and (p[1],p[0]) not in d}
    def recorded(self,g=None,**kwargs):
        sn=self.node(**kwargs)
        self._recorded=sn['recorded']
        if g is not None:
            self._recorded=g
        return self._recorded
    def update(self,group=None,verified=False,writestatus=True):
        """This function updates the status variable, not the lift file."""
        changed=False
        if group is None:
            group=self.group()
        self.build()
        n=self.node()
        # log.info(f"verification update: {group=} as {verified=} in {n['done']}")
        if verified == True:
            if group not in n['done']:
                n['done'].append(group)
                changed=True
        if verified == False:
            if group in n['done']:
                n['done'].remove(group)
                changed=True
        if writestatus and changed:
            self.store()
        # log.info("Verification after update: {}".format(self.verified()))
        return changed
    def group(self,group='<unspecified>'):
        """This maintains the group we are actually on, pulled from data
        located by current slice and parameters"""
        if group != '<unspecified>': #this needs to be able to be specified None
            self._group=group
        return getattr(self,'_group',None)# this needs to be booleanable
    def renamegroup(self,j,k,**kwargs):
        # log.info(f"Status renaming {j}>{k} for {kwargs=}")
        sn=self.node(**kwargs)
        if j in sn['done']:
            sn['done'][sn['done'].index(j)]=k
        if j in sn['groups']:
            # sn['groups'][sn['groups'].index(j)]=k
            sn['groups'].remove(j)
            sn['groups'].append(k)
        if j in sn['recorded']:
            sn['recorded'][sn['recorded'].index(j)]=k
        if 'distinguished' in sn:
            for i in [l for l in sn['distinguished'] if j in l]:
                sn['distinguished'].remove(i)
                sn['distinguished'].add(tuple(k if m == j else m for m in i))
        if self.group() == j:
            self.group(k)
    def makegroupok(self,**kwargs):
        kwargs=grouptype(**kwargs)
        groups=self.groups(**kwargs)
        if not hasattr(self,'_group'):
             self._group=None #define this attr, one way or another
        if groups != []:
            if self._group not in groups:
                self.group(groups[0])
    def makecheckok(self, **kwargs): #result None w/no checks
        check=self.program.params.check()
        checks=self.checks(**kwargs)
        if check not in checks:
            if checks:
                self.program.params.check(checks[0])
            else:
                self.program.params.check(unset=True)
    def toneframedefn(self):
        d=self.program.toneframes[self.program.slices.ps()][self.program.params.check()]
        return d
    def checkslicetypecurrent(self,**kwargs):
        """This fills in current values; it shouldn't leave None anywhere."""
        i=kwargs.copy()
        for k,v in i.items():
            if v is None:
                del kwargs[k]
        kwargs['cvt']=kwargs.get('cvt',self.program.params.cvt())
        kwargs['ps']=kwargs.get('ps',self.program.slices.ps())
        kwargs['profile']=kwargs.get('profile',self.program.slices.profile())
        kwargs['check']=kwargs.get('check',self.program.params.check())
        log.log(4,_("Returning checkslicetypecurrent kwargs {kwargs}").format(kwargs=kwargs))
        return kwargs
    def last(self,task,update=False,**kwargs):
        if update and not kwargs.get('check'): #write cross-check tone analysis
            for kwargs['check'] in self.checks():
                self.last(task,update,**kwargs)
            return
        sn=self.node(**kwargs)
        if 'last' not in sn:
            sn['last']={}
        if update:
            sn['last'][task]=str(now())
        if kwargs.get('write'):
            self.store()
        if task in sn['last']:
            return sn['last'][task]
    def isanalysisOK(self,**kwargs):
        if 'check' in kwargs:
            a=self.last('analysis',**kwargs)
            s=self.last('sort',**kwargs)
            j=self.last('joinUF',**kwargs)
        else:
            log.info(_("checking for an OK analysis across all checks"))
            analysisl=[]
            sortl=[]
            ufjoinl=[]
            self.renewchecks()
            # log.info(f"Working on checks '{self.checks()}'")
            # log.info(f"Working on updatechecksbycvt '{self.updatechecksbycvt()}'")
            for check in self.updatechecksbycvt():
                log.info(_("Working on check ‘{check}’").format(check=check))
                analysisl.append(self.last('analysis',**{**kwargs,'check':check}))
                sortl.append(self.last('sort',**{**kwargs,'check':check}))
                ufjoinl.append(self.last('joinUF',**{**kwargs,'check':check}))
            log.info(_("Collected analysisl: {list}").format(list=analysisl))
            log.info(_("Collected sortl: {list}").format(list=sortl))
            log.info(_("Collected ufjoinl: {list}").format(list=ufjoinl))
            # These are stored on file as strings
            a=min([datetime.datetime.fromisoformat(i) for i in analysisl if i],
                                                                    default='')
            s=max([datetime.datetime.fromisoformat(i) for i in sortl if i],
                                                                    default='')
            j=max([datetime.datetime.fromisoformat(i) for i in ufjoinl if i],
                                                                    default='')
        log.info(_("{a}>{s}?").format(a=a,s=s))
        if a and s:
            ok=fixnaivedatetime(a)>fixnaivedatetime(s)
        elif a:
            ok=True # b/c analysis would be more recent than last sorting
        else:
            ok=False # w/o info, trigger reanalysis
        if ok and j and fixnaivedatetime(j) > fixnaivedatetime(a):
            joinsinceanalysis=True #show groups on all non-default reports
        else:
            joinsinceanalysis=False
        annalysisoknotice=_("Last analysis at {analysis_time};\n"
                    "last join at {join_time}\n"
                    "last sort at {sort_time}\n(analysisOK={ok})"
                    "").format(analysis_time=a,
                                join_time=j,
                                sort_time=s,
                                ok=ok)
        log.info(annalysisoknotice)
        return ok, joinsinceanalysis, annalysisoknotice
    def __init__(self,filename,dict,program):
        """To populate subchecks, use self.groups()"""
        self.program=program
        self.program.status=self
        self._filename=filename
        # self._task=getattr(self.program,'defaulttask',WordCollectnParse)
        super(StatusDict, self).__init__()
        for k in dict:
            if k is None:
                continue
            self[k]=dict[k]
        self._checksdict={}
        self._cvchecknames={}
        # log.info(f"StatusDict initialized with contents {self}")
