# coding=UTF-8
import sys
import collections
# import re
# import datetime
# import tkinter as tk
from utilities.utilities import *
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
# import itertools
# import inspect
# import multiprocessing

from frontend.error_notice import ErrorNotice

from utilities.i18n import _
from utilities import rx

def __getattr__(name):
    # Lazy load globals from main
    if name in ('unlist',):
        import main
        return getattr(main, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

# Mirror main globals lazily to allow bare-name access
for name in ('unlist',):
    if name not in globals():
        globals()[name] = LazyGlobal(name)

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
        except:
            self.checkresults[check.name]={}
        try:
            self.checkresults[check.name][check.subcheck]
        except:
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
        try:
            return self[(self._profile,self._ps)]
        except KeyError:
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
            log.info(_("I don't have a ps to use; I hope that's OK!"))
        elif not hasattr(self,'_ps') or self._ps not in pss:
            self.ps(pss[0])
    def makeprofileok(self):
        if not hasattr(self,'_ps'):
            self.makepsok()
        profiles=self.profiles()
        if not profiles:
            self._profile=None #only before data collection
            log.info(_("I don't have a profile to use; I hope that's OK!"))
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
            log.error(_("You asked to change to ps {ps}, which isn't in the list "
                        "of pss: {pss}").format(ps=ps,pss=pss))
        elif hasattr(self,'_ps'):
            return self._ps
        else:
            log.error(_("You asked for the ps, but I don't have any (pss: {pss})"
                        "").format(pss=pss))
    def profiles(self,ps=None):
        """This returns profiles for either a specified ps or the current one"""
        if not ps:
            ps=self.ps()
        if ps and ps in self._profiles:
            # log.info(_("returning profiles: {profiles}").format(profiles=self._profiles[ps]))
            return self._profiles[ps]
        else:
            return []
    def profile(self,profile=None):
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
            log.error(_("You asked for valid ps data, but that ps isn't there."))
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
        e=_("Found {count} valid data slices: {keys}").format(count=len(wcounts),keys=self.keys())
        e+='\n'+_("Invalid entries found: {invalid}/{total}").format(invalid=profilecountInvalid,
                                                        total=sum(self.values(),
                                                        profilecountInvalid))
        if self.program.db.analangs and not len(wcounts):
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
            ErrorNotice(_("There doesn't seem to be any profile data, but "
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
        checks=self.updatechecksbycvt(**kwargs)
        # if isinstance(self.task(),Sort) or isinstance(self.task(),Transcribe):
        if kwargs.get('no_correspondence_checks'):
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
        log.info(d)
        log.info({cvt:set([check #i
                        for ps in d[cvt]
                        for profile in d[cvt][ps]
                        for check in d[cvt][ps][profile]
                        # for i in d[cvt][ps][profile][check]['done']
                        # if 'done' in d[cvt][ps][profile][check]
                        # if i not in ['NA']
                        ])
                for cvt in d if cvt != 'T'
                })
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
            return sorted(self._groups)
        if kwargs['toverify']:
            #done is always a subset of groupsː
            sn['done']=sorted(set(sn['done'])&set(sn['groups']))
            return sorted(set(sn['groups'])-set(sn['done']))
        if kwargs['torecord']:
            return sorted(set(sn['groups'])-set(sn['recorded']))
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
        log.info(_("Saving status dict to file"))
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
        if cvt in ['T','S']:
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
            for ps in self.program.slices.pss():
                self._checksdict[cvt][ps]=self.program.params.cvchecknamesdict().keys()
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
            sn['groups'].add(k)
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
                log.info(_("Working on check '{check}'").format(check=check))
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
        log.info(f"StatusDict initialized with contents {self}")
