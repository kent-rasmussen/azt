#!/usr/bin/env python3
# coding=UTF-8
"""This file runs the parser lexical files"""

import logsetup
log=logsetup.getlog(__name__)
logsetup.setlevel('INFO',log) #for this file
log.info("Importing parser.py")
import time
import collections
import difflib
import threading
try: #translation
    _
except:
    def _(x):
        return x
import xmletfns
import lift
import rx
from utilities import *
class AffixCollector(object):
    """This class does just one thing: call parse to collect affixes
    automatically to populate the catalog."""
    def progress(self):
        return 100*self.catalog.parsen()//self.nsenseids
    def parse(self,sense):
        kwargs={'sense':sense,
                # 'entry':ifone(self.dbnodes.findall('entry/sense[@id="{}"]/..'
                #                             ''.format(senseid))),
                }
        self.parser.parseentry(**kwargs)
        self.catalog.addparsed(kwargs['sense'])
    def do(self):
        for sense in self.senses:
            self.parse(sense) #this can add to lists
            yield self.progress()
    def getfromlift(self):
        log.info("looking in LIFT file for data")
        # log.info("looking in {}".format(self.dbnodes.findall("entry/sense/"
        #                             "trait[@name='{}-infl-class']"
        #                             "".format(self.pss[0])
        #                                 )))
        # log.info("Checking pss {}".format(self.pss))
        pstodo=len(self.pss) #do less common first:
        for n,ps in enumerate(self.pss[::-1]):
            # log.info("Checking ps {}".format(ps))
            results=self.dbnodes.findall("entry/sense/"
                                        "trait[@name='{}-infl-class']"
                                        "".format(ps)
                                        )
            sensenodes=self.dbnodes.findall("entry/sense/"
                                        "trait[@name='{}-infl-class']/.."
                                        "".format(ps)
                                        )
            # log.info("found results {}; {}".format(results,sensenodes))
            for sensenode in sensenodes:
                self.catalog.addparsed(sensenode.get('id'))
            rtodo=len(results)
            for nr,r in enumerate(results):
                self.catalog.addaffixset((ps,ofromstr(r.get('value'))))
                # log.info("ps progress: {} ({}/{})".format(100*n/pstodo,n,pstodo))
                # log.info("results progress: {} ({}/{})"
                #         "".format(100*nr/rtodo/pstodo,nr,rtodo))
                yield int((100*n/pstodo)+(100*(nr/rtodo/pstodo)))
    def __init__(self,catalog,db,**kwargs):
        self.parser=Engine(catalog)
        self.dbnodes=db.nodes
        self.senses=db.senses
        self.nsenses=len(db.senses) #don't keep calculating this
        self.pss=db.pss
        self.catalog=catalog
        log.info("Looking in LIFT file for data")
        if kwargs.get('loadfromlift'):
            for i in self.getfromlift():
                print(i)
        self.catalog.report()
        # self.do()
class Catalog(object):
    """This needs to either call a UI for user response, or provide the UI an
    interface to provide prompt data, and receive the response."""
    def report(self):
        self.affixesbyform()
        try:
            for a in ['affixes','lcaffixes','sfaffixes']:#self.affixattrs()[3:]:
                log.info("{}: {}".format(a,
                {ps:getattr(self,a)[ps] for ps in getattr(self,a)
                        if getattr(self,a)[ps]}
                ))
        except AttributeError as e:
            log.info("apparently missing affixes ({})".format(e))
        try:
            for l in ['nops','badps','parsed','neither']:
                #output this to special files, not log:
                f = open(l+'.txt', 'w', encoding='utf-8') # to append, "a"
                f.write('\n'.join(getattr(self,l)))
                f.close()
                log.info("{} count: {}".format(l,len(getattr(self,l))))
        except AttributeError as e:
            log.info("apparently missing affixes ({})".format(e))
    def affixesbyform(self):
        try:
            self.lcaffixes={
                        ps:collections.Counter([i[0] for i in self.affixes[ps]])
                        for ps in self.affixes
                        if self.affixes[ps]
            }
            self.sfaffixes={
                        ps:collections.Counter([i[1] for i in self.affixes[ps]])
                        for ps in self.affixes
                        if self.affixes[ps]
            }
        except AttributeError as e:
            if "'Catalog' object has no attribute 'affixes'" in e.args[0]:
                log.info("evidently there have been no parses so far.")
    def parsen(self):
        try:
            return len(self.parsed)
        except AttributeError:
            return 0
    def neithern(self):
        return len(self.neither)
    def addnops(self,senseid):
        try:
            self.nops+=[senseid]
        except AttributeError:
            self.nops=[senseid]
    def addbadps(self,senseid):
        try:
            self.badps+=[senseid]
        except AttributeError:
            self.badps=[senseid]
    def addparsed(self,senseid):
        try:
            self.parsed+=[senseid]
        except AttributeError:
            self.parsed=[senseid]
    def addneither(self,senseid):
        try:
            self.neither+=[senseid]
        except AttributeError:
            self.neither=[senseid]
    def addaffixset(self,affixes):
        if len(affixes[1]) != 2:
            log.error("Tried to add affixes {} of len {}, not doing!".format(
                                                    affixes[1],len(affixes[1])
                                                    ))
            return
        try:
            self.affixes[affixes[0]].update([affixes[1]])
        except KeyError:
            self.affixes[affixes[0]]=collections.Counter([affixes[1]])
        except AttributeError:
            self.affixes={affixes[0]:collections.Counter([affixes[1]])}
    def __init__(self,task):
        # This needs a way of picking up custom analysis morphemes
        # Is the lx parsed already enough?
        log.info("Initializing parser catalog")
        try: # Get these from main.py:
            self.analang=task.analang
            self.fieldnames=task.secondformfield
            self.nominalps=task.nominalps
            self.verbalps=task.verbalps
        except AttributeError:
            log.info("Task not found; using defaults")
            self.analang='ndk'
            self.fieldnames={'n':'Plural',
                            'v':'Imperative'
                            }
            self.nominalps='n'
            self.verbalps='v'
class Engine(object):
    """This class takes data fields (lc, pl, and imp) and parses and analyzes
    them into analysis fields lx, ps, and pssubclass (defined by affix
    groupings). This is done by order of certainty:
    4. The following are true:
        - At least three fields present: lx, lc and (pl or imp)
        - Second form (pl or imp) present for ps as indicated in the entry.
        - lx is a proper subset of lc and second form
    0: At least two fields present: lc and (pl or imp)
    1: Level 0, but one field parses with a known affix set (prefix, suffix)
    2: Level 1, and the other field also parses with a known affix set
    3: Level 2, and affixes are already known together.
    """
    def levels(self):
        return {
        5: _("Never"),#"This level is never satisfied",
        4: _("Three fields parse with matching ps"),
        0: _("Two fields, which don't parse"),
        1: _("One field of two parses"),
        2: _("Two fields each parse"),
        3: _("Two fields parse together")
        }
    def evaluateroothyp(self,roothyp,ps,lcafxs,sfafxs):
        # we look for individual matches here to go faster, but also
        # because there should be only one sequence of segments that can
        # reconstruct a given form from a given root, and it is either
        # there *somewhere*, or not. If there, we'll deal with the
        # presence of this correspondence later.
        # take ps arg, rather than depend on self.ps, which may be wrong
        q=0
        try:
            if lcafxs in self.catalog.lcaffixes[ps]:
                # log.info("lc reconstructs with {}+{} (already there)"
                #         "".format(roothyp,lcafxs))
                q+=1
        except (AttributeError,KeyError):
            pass
        try:
            if sfafxs in self.catalog.sfaffixes[ps]:
                # log.info("sf reconstructs with {}+{} (already there)"
                #     "".format(roothyp,sfafxs))
                q+=1
        except (AttributeError,KeyError):
            pass
        try:
            if q == 2 and (lcafxs, sfafxs) in self.catalog.affixes[ps]:
                # User informed of this later
                q+=1
                if ps == self.ps:
                    q+=1
        except (AttributeError,KeyError):
            pass
        return q
    def texts(self):
        try:
            return (
                self.entry.lx.textvaluebylang(self.analang),
                self.entry.lc.textvaluebylang(self.analang),
                self.entry.plvalue(self.fieldnames[self.nominalps],
                                                            self.analang),
                self.entry.impvalue(self.fieldnames[self.verbalps],
                                                            self.analang))
        except AttributeError as e:
            # if "'Engine' object has no attribute 'lxnode'" in e.args[0]:

            log.info("missing node on {} ({})".format(self.senseid,e.args[0]))
            raise
        except KeyError as e:
            # if "'Engine' object has no attribute 'lxnode'" in e.args[0]:

            log.info(f"missing field {e.args[0]} in fieldnames")
            return ("","","","")
    def addaffixset(self,ps,afxtuple):
        self.catalog.addaffixset((ps,afxtuple))
        self.catalog.addparsed(self.senseid)
        if self.auto < 4:
            log.info("adding {}".format(afxtuple))
    def doparsetolx(self,root,ps,afxtuple):
        #This stores root, ps, and affixes, once decided on
        log.info("executing doparsetolx with root: {} ({}) and affixes: {}"
                "".format(root,ps,afxtuple))
        self.entry.lx.textvaluebylang(self.analang,root)
        self.sense.psvalue(ps)
        self.sense.pssubclassvalue(afxtuple)
        self.addaffixset(ps,afxtuple)
        self.catalog.affixesbyform()
    def getfields(self):
        #This sets ps if only one second form field found
        lx, lc, pl, imp = self.texts()
        sf = None
        if pl and not imp:
            log.info("looks like a noun; parsing plural")
            self.sense.psvalue(self.nominalps)
            sf = pl
        elif imp and not pl:
            log.info("looks like a verb; parsing imperative")
            self.sense.psvalue(self.verbalps)
            sf = imp
        elif imp and pl:
            log.info("This entry has both plural and imperative??")
            if self.ps == self.nominalps:
                log.info("Found nominal ps {}; using...".format(self.ps))
                sf = pl
            elif self.ps == self.verbalps:
                log.info("Found verbal ps {}; using...".format(self.ps))
                sf = imp
            else:
                log.info("Found other ps {}; skipping...".format(self.ps))
        else:
            log.info("This entry has neither plural nor imperative?? skipping.")
        return lx, lc, sf, pl, imp
    def bestrootbyps(self,roots,ps,lc,sf):
        if not roots:
            return (0,'')
        bestsofar=(0,max(roots,key=len)) # return this or better
        for roothyp in roots:
            lcafxs=tuple(lc.split(roothyp))
            sfafxs=tuple(sf.split(roothyp))
            r=self.evaluateroothyp(roothyp,ps,lcafxs,sfafxs)
            if r == 4: # we're done
                bestsofar=(r,roothyp)
                break
            elif r > bestsofar[0] or (r and r == bestsofar[0] and
                                        len(roothyp) < len(bestsofar[1])):
                log.info("Marking new bestsofar: {}".format((r,roothyp)))
                bestsofar=(r,roothyp)
        return bestsofar
    def twoforms(self):
        if self.ask > 4:
            log.info("Asking for the impossible!")
            return 1
        lx, lc, pl, imp = self.texts()
        if lx and not lc: #switch them, both in node and in local variables
            self.parser.entry.lc.textvaluebylang(self.analang,lx)
            self.parser.entry.lx.textvaluebylang(self.analang,'')
        if not (lc and (pl or imp)): #this only parses nouns and verbs
            log.info("Missing forms! (lc:{}; pl:{} imp:{})".format(lc, pl, imp))
            return 1
        # log.info("Two There! (lc:{}; pl:{} imp:{}): Parse!".format(lc, pl, imp))
        # These return an empty list for empty sf
        nroots=roothypgenerator(lc,pl)
        vroots=roothypgenerator(lc,imp)
        # Test possible roots for matches with present affix combos:
        # 0: No matches, just returned longest
        # 1: *one* form built on this root with found affix combo
        # 2: both forms built on this root with found affix combos
        # 3: both forms built with affix combos already together elsewhere
        # 4: also has matching ps
        # Test as N and V, even if marked otherwise
        bestn=self.bestrootbyps(nroots,self.nominalps,lc,pl)
        bestv=self.bestrootbyps(vroots,self.verbalps,lc,imp)
        if max(bestn[0], bestv[0]) < self.ask:
            log.info("Neither Noun ({}) nor Verb ({}) is good enough (ask: {})"
                    "".format(bestn[0], bestv[0], self.ask))
            return 1 # We won't do this one anyway; give up now.
        noun=verb=False #figure this out next
        if not (bestn[1] or bestv[1]):
            log.info("No nroot of value ({}:{}): {}".format(lc,pl,nroots))
            log.info("No vroot of value ({}:{}): {}".format(lc,imp,vroots))
            return 1 #no found affixes built either form, do manually
        if bestn[1] and bestv[1]:
            # This shouldn't happen often: both forms have lc lcs which build
            # at least one form with a known affix
            log.info("Noun roots found ({}:{}): {}".format(lc,pl,nroots))
            log.info("Verb roots found ({}:{}): {}".format(lc,imp,vroots))
            # As both were found, we need to decide which is better:
            if bestn[0] > bestv[0]:
                log.info("Noun looks better (n:{}; v:{})".format(bestn,bestv))
                self.askuserifweshouldaddthisps()
                noun=True
            elif bestv[0] > bestn[0]:
                log.info("Verb looks better (n:{}; v:{})".format(bestn,bestv))
                self.askuserifweshouldaddthisps()
                verb=True
            elif bestv[0]: #non-zero
                if len(bestn[1]) > len(bestv[1]): #shorter roots, longer affixes
                    log.info("Verb slightly better ({}/{})".format(bestv,bestn))
                    self.askuserifweshouldaddthisps()
                    verb=True
                elif len(bestn[1]) < len(bestv[1]):
                    log.info("Noun slightly better ({}/{})".format(bestn,bestv))
                    self.askuserifweshouldaddthisps()
                    noun=True
                else:
                    log.info("Noun=verb ({}/{})".format(bestn,bestv))
                    self.reportpsproblemtouser()
                    return 1
        elif bestn[1]:
            self.sense.psvalue(self.nominalps)
            noun=True
        elif bestv[1]:
            self.sense.psvalue(self.verbalps)
            verb=True
        else:
            log.error("Logical problem! n:{}; v:{} ({})"
                        "".format(noun,verb,self.senseid))
            raise
        if noun:
            best=bestn
            sf=pl
            ps=self.nominalps
        elif verb:
            best=bestv
            sf=imp
            ps=self.verbalps
        else:
            log.error("Neither noun nor verb! This shouldn't happen! ({})"
                        "".format(self.senseid))
            raise
        sfafxs=tuple(sf.split(best[1]))
        lcafxs=tuple(lc.split(best[1]))
        # log.info("Best match: {}".format(best))
        if best[0] == 4:
            log.info("Excellent match; "
                    "Found root {} in lc: {} and sf: {}, "
                    "with this combination of affixes ({}) already "
                    "present, already with each other in this ps, which is "
                    "already marked in the entry"
                    "".format(best[1], lc, sf, (lcafxs, sfafxs))
                    )
        elif best[0] == 3:
            log.info("Very good match; "
                    "Found root {} in lc: {} and sf: {}, "
                    "with this combination of affixes ({}) already "
                    "present, already with each other in this ps"
                    "".format(best[1], lc, sf, (lcafxs, sfafxs))
                    )
        elif best[0] == 2:
            log.info("Good match; found root {} in lc: {} and sf: {}, "
                "with each combination of affixes ({}) already "
                "present, but not with each other"
                "".format(best[1], lc, sf, (lcafxs, sfafxs))
                    )
        elif best[0] == 1: #Good match, but with one present affix set
            log.info("OK match; found root {} in lc: {} or sf: {}, "
                    "but without the other set already present; asking."
                    "".format(best[1], lc, sf, (lcafxs, sfafxs))
                    )
        else: #Good match, but not with neither affix set present
            log.info("Found root {} in lc: {} and sf: {}, but without "
                    "matching affixes ({}) already present."
                    "".format(best[1], lc, sf, (lcafxs, sfafxs))
                    )
        if best[0] >= self.auto:
            log.info("Level {} match, parsing automatically (auto: {})"
                    "".format(best[0],self.auto))
            self.doparsetolx(best[1],ps,(lcafxs, sfafxs))
            return
        elif best[0] >= self.ask:
        # and self.askusertoconfirmaffixcombo(
        #                                 lc, sf, best[1], ps, (lcafxs, sfafxs)
            log.info("Level {} match, parsing with confirmation (ask: {})"
                    "".format(best[0],self.ask))
            return *best, lc, sf, ps, (lcafxs, sfafxs)
            # self.doparsetolx(best[1],ps,(lcafxs, sfafxs))
            # return 1
        else:
            log.info("{}/{} skipping ({}) lx:{}; lc:{}; sf:{}; imp:{}; ps:{} {}"
                    "".format(self.auto,self.ask,best[0],lx,lc,pl,imp,
                                self.ps,self.senseid))
            return 1
    def threeforms(self):
        # Return 1 if not done (incl. skipped)
        # some day, this should be smarter, to handle reduplication and other
        # cases that might split on the root into more than two pieces
        #
        # This should parse only absolutely done *and consistent* data,
        # as a basis for parsing less clear data:
        # - 3 forms (lx, lc and pl or imp) with corresponding ps
        # - lx is a subset of each of the other two forms
        # N.B.: this being complete and consistent does not mean that it is
        # correct —hence the next line to skip this to manually parse these
        if min(self.auto, self.ask) > 4: #for manual reparsing of what looks obvious
            # log.info("No auto parsing this run")
            return 1
        lx, lc, pl, imp = self.texts()
        afxs=None
        # log.info("testing for self.ps (threeforms)")
        if lx and lc and (pl or imp) and getattr(self,'ps',None):
            if lx in lc:
                if self.ps == self.nominalps and pl and lx in pl:
                    afxs=(tuple(lc.split(lx)),tuple(pl.split(lx)))
                    sf=pl
                elif self.ps == self.verbalps and imp and lx in imp:
                    afxs=(tuple(lc.split(lx)),tuple(imp.split(lx)))
                    sf=imp
        if afxs and 4 >= self.auto:
            log.info("Atumatic parse on three forms with ps (auto: {})"
                    "".format(self.auto))
            self.addaffixset(self.ps,afxs)
            return
        elif afxs and 4 >= self.ask:
            log.info("Match with three forms with ps, asking for confirmation "
                    "(ask: {})".format(self.ask))
            return 4, lx, lc, sf, self.ps, afxs
        return 1
    def doifallbutps(self, lx, lc, pl, imp):
        """This is for when you have three forms, but no known affix combos,
        nor ps marked. probably not very useful.
        """
        if lx and lc and (pl or imp) and (lx in lc):
            afn=afv=None
            if lx in pl:
                afn=(self.nominalps,(tuple(lc.split(lx)),tuple(pl.split(lx))))
            if lx in imp:
                afv=(self.verbalps,(tuple(lc.split(lx)),tuple(imp.split(lx))))
            if afn and afv:
                log.error("Parsed both pl and imp? Problem! ({})"
                            "".format(self.senseid))
                return
            elif afn or afv:
                log.info("All There and subset! (lx:{}; lc:{}; pl:{}); "
                        "imp:{}): Ready to mark ps and get affixes."
                        "".format(lx, lc, pl, imp))
                if afn:
                    self.sense.psvalue(self.nominalps)
                    self.catalog.addaffixset(afn)
                elif afv:
                    self.sense.psvalue(self.verbalps)
                    self.catalog.addaffixset(afv)
                return 1 #The only successful parse exit point
            else:
                log.info("Looks like {} isn't a subset of {} or {} ({})"
                            "".format(lx,pl,imp,ps.node))
        else:
            log.info("Looks like a form is missing, or {} isn't a subset of {}"
                        "({};{})".format(lx,lc,pl,imp))
    def dooneformparse(self,x,window):
        # x is (sf,ps,root,lcafxs,sfafxs)
        log.info("User selected {}".format(x))
        if not type(x) is tuple:
            if x=='ON':
                self.sense.psvalue(self.nominalps)
            elif x=='OV':
                self.sense.psvalue(self.verbalps)
            else:
                log.info("Not a tuple, nor known: ({}, {})".format(x,type(x)))
            window.destroy() #actually a canary button
            return
        self.doparsetolx(x[2],x[1],(x[3],x[4]))
        if x[1] == self.nominalps:
            self.entry.plvalue(self.fieldnames[x[1]],self.analang,x[0])
        elif x[1] == self.verbalps:
            self.entry.impvalue(self.fieldnames[x[1]],self.analang,x[0])
        else:
            log.error("Parsed but neither noun nor verb?")
        window.destroy() #actually a canary button
    def oneform(self):
        # log.info("This is where we set up request for the second form")
        lx, lc, pl, imp = self.texts()
        # if not lc and not pl and not imp:
        #     # log.info("senseid: {}".format(self.senseid))
        #     log.info(self.senseid)
        # log.info("lx: {}, lc: {}, pl: {}, imp: {}".format(*self.texts()))
        if lx and not lc: #switch them, both in node and in local variables
            self.parser.entry.lc.textvaluebylang(self.analang,lx)
            self.parser.entry.lx.textvaluebylang(self.analang,'')
        if not lc:
            log.info("No citation form!")
            return
        possibilities=[]
        try:
            for ps in [self.nominalps, self.verbalps]:
                if not ps in self.catalog.affixes: # move on now
                    continue
                for lcafxs in self.catalog.lcaffixes[ps]:
                    # log.info("lcafxs: {} ({})".format(lcafxs,type(lcafxs)))
                    if lc.startswith(lcafxs[0]) and lc.endswith(lcafxs[1]):
                        root=rx.sub('^'+lcafxs[0],'',
                                    rx.sub(lcafxs[1]+'$','',lc,1)
                                                        ,1)
                        # log.info("root: {} ({}; {})".format(root,ps,lcafxs))
                        collected=[]
                        for afxs in self.catalog.affixes[ps]:
                            if afxs[0] == lcafxs:
                                sfafxs=afxs[1]
                                sf=root.join(sfafxs)
                                # log.info("sf: {} ({}; {}, {})"
                                #         "".format(sf,ps,root,sfafx))
                                possibilities+=[(sf,ps,root,lcafxs,sfafxs)]
                                collected+=[sfafxs]
                                # store This pair as priority
                        for sfafxs in self.catalog.sfaffixes[ps]:
                            if sfafxs not in collected:
                                sf=root.join(sfafxs)
                                # log.info("sf2: {} ({}; {}, {})"
                                #         "".format(sf,ps,root,sfafxs))
                                possibilities+=[(sf,ps,root,lcafxs,sfafxs)]
                                collected+=[sfafxs]
                                # store these as secondary
        except AttributeError as e:
            if "'Catalog' object has no attribute '" in e.args[0]:
                log.info("Missing affix attribute; moving on ({})".format(e))
                possibilities=[]
            else:
                log.error("Not sure what happened: {}".format(e))
                # log.info("ps: {}; lcafxs: {}; sfafxs: {}"
                #             "".format(ps,lcafxs,sfafxs))
                raise
        except Exception as e:
            log.error("Not sure what happened: {}".format(e))
            # log.info("ps: {}; lcafxs: {}".format(ps,lcafxs))
            # log.info("sfafxs: {}".format(sfafxs))
            raise
        # log.info("oneform possibilities output: {}".format(possibilities))
        return possibilities
    def missingnodecheck(self):
        nodes=['lx','lc']
        if self.ps == self.nominalps:
            nodes+=['pl']
        elif self.ps == self.verbalps:
            nodes+=['imp']
        # else:
        #     log.info("Looks like non-NV; skipping second field check")
        #     # nodes+=['pl','imp']
        for node in nodes:
            if not lift.iselement(getattr(self,node+'node')):
                log.info("Missing {} node!".format(node))
    def pscheck(self):
        # Return False if any problem
        if not self.ps: #any value is OK
            self.catalog.addnops(self.senseid)
        elif set(self.ps)-set(self.fieldnames): #any non-NV=bad
            log.info("ps found: {} ({})".format(self.ps,self.senseid))
            self.catalog.addbadps(self.senseid)
        else:
            return True #not (self.nops or self.badps)
    def parseentry(self, sense=None, senseid=None, entry=None):
        """I should likely remove self.senseid, as redundant with self.sense.id"""
        self.on=self.ov=False
        # if self.auto < 4:
        #     log.info("Called with args {};{}".format(entry, senseid))
        # self.affixes=None # everyone needs this
        if sense:
            self.sense=sense
            self.senseid=sense.id #save for later
            self.entry=sense.entry
        elif senseid:
            self.senseid=senseid #save for later
            log.error("given senseid, but can't really get sense")
            self.sense=entry.sense
            self.entry=sense.entry
        elif entry:
            self.entry=entry
            self.sense=self.entry.sense
            self.senseid=self.sense.id #save for later
        else:
            log.error("Need one of sense, senseid, or entry!")
            return
        """Do I want to add this here? if so, must overright rigorously,
        to avoid old values"""
        self.ps=self.sense.psvalue()
        # log.info("sense: {}".format(self.sense))
        # log.info("entry: {}".format(self.entry))
        # log.info("psnode: {}".format(psnode))
        # if not (min(self.auto,self.ask) < 4 or self.pscheck()):
        #     log.info("Returning because self.auto ({}) < 4 or "
        #             "self.ask ({}) < 4 or pscheck: {}"
        #             "".format(self.auto,self.ask,self.pscheck()))
        #     return 1# stop here if collecting affixes & w/o ps or non-NV ps
        # log.info("self.secondformfield: {}".format(self.secondformfield))
        # log.info("ps: {}".format(self.ps))
    def asklevel(self,l=None):
        ls=self.levels()
        if isinstance(l,int) and l in ls:
            self.ask=l
        log.info("Parser set to ask for ‘{}’".format(ls[self.ask]))
    def autolevel(self,l=None):
        ls=self.levels()
        if isinstance(l,int) and l in ls:
            self.auto=l
        log.info("Parser set to auto for ‘{}’".format(ls[self.auto]))
    def setlevels(self,auto=5,ask=4): #default for first auto run
        self.auto=auto
        self.ask=ask
    def __init__(self, catalog, *args, **kwargs):
        super(Engine, self).__init__()
        #These things shouldn't change from one parse to another:
        self.setlevels() #call later to do more work automatically, or if asked
        self.catalog=catalog
        self.fieldnames=self.catalog.fieldnames
        self.nominalps=self.catalog.nominalps
        self.verbalps=self.catalog.verbalps
        self.analang=self.catalog.analang
def textof(node,value=None):
    try:
        if value is not None: #allow clearing with ''
            node.text=value
        return node.text
    except AttributeError:
        if node:
            log.info("{} doesn't seem to have a text attribute".format(n))
        # else:
        #     log.info("{} doesn't seem to exist".format(n))
def ifonetattr(l,nt=None):
    if l and not len(l)-1:
        return l[0].text
def ifone(l):
    if l and not len(l)-1:
        return l[0]
def roothypgenerator(a,b):
    if not (a and b):
        return [] #don't try to match nothing, but return an iterable anyway.
    m=difflib.SequenceMatcher(None,a,b).find_longest_match()
    # print(m.size)
    t=a[m.a:m.a+m.size]
    try:
        assert t == b[m.b:m.b+m.size]
    except AssertionError:
        log.error("Problem with SequenceMatcher: {} != {} "
                "(a={},b={},match={})".format(t,b[m.b:m.b+m.size],a,b,m))
        raise #this is worth always getting right, at least for now
    l=[]
    for i in range(m.size):
        for j in range(0,m.size-i):
            l+=[t[i:m.size-j]]
    l.sort(key=len,reverse=True)
    return l #SequenceMatcher worked correctly, return sequential subsets
def now():
    t=datetime.datetime.utcnow()
    log.info("now {} ({})".format(t,t-start))
if __name__ == "__main__":
    import datetime
    start=datetime.datetime.utcnow()
    filename="/home/kentr/Assignment/Tools/WeSay/Demo_ndk/ndk.lift"
    db=lift.Lift(filename)
    senseids=[
            '4813f41d-9ea7-4944-8df0-3a0a308e6e0c',
            '4096e0d8-847d-4366-8a1e-4dfafde05df0',
            '942e7b83-2541-444a-8814-2127b083a62e',
            'd94c260c-0414-4dac-aa3a-b887417dc1e9',
            '9f1181df-38b8-48c1-8856-f50c6145f139',
            'b45b4d81-d551-4323-b1f5-bc3b237e073b',
            'beee0d1a-46e6-4b24-9cc3-abcaf1636cb6',
            '73a5a776-e8c9-445f-b20e-aeeb3020a5f6',
            'a4509e21-a8b6-4202-94db-c751d8daae33',
            'e14179ad-35a6-4360-82b4-009c57771429',
            '898b311a-2157-42df-885f-b259a903ef89',
            '9a4c32a8-2d75-4a6d-840a-fad1ecb4fdcb',
            'ebdd32e9-e949-4c46-adb7-5dafbaf7c52c',
            'bba4e818-6169-472f-a626-f8323d2d2cb8',
            '78aa1a15-7784-4188-a1b8-f63a34ca0cb5',
            'ca9d097b-38b6-4273-8863-31e18bc24c0f',
            '898b311a-2157-42df-885f-b259a903ef89'
            ]
    senseidsoneform=[
                    "a4fec312-db00-4bc6-ad36-c28a89b67c0c",
                    'ce49b092-f6b4-4198-910a-aeb6f933e77f',
                    # '4813f41d-9ea7-4944-8df0-3a0a308e6e0c',
                    # '942e7b83-2541-444a-8814-2127b083a62e',
                    # 'd94c260c-0414-4dac-aa3a-b887417dc1e9',
                    # '73a5a776-e8c9-445f-b20e-aeeb3020a5f6',

                    # 'ee1a083a-52fb-4205-861b-56b4d0e54f8a',
                    # 'e60fae62-af97-424a-91d7-791d89455c0a',
                    # '3a2e70b8-fe93-4468-87fa-f4997237df7c',
                    # 'aa7ba7fc-95ce-414b-b17f-d744de154418',
                    # '049c0d09-7c24-487e-afcd-f49fb2c227fa',
                    # '1a3bdac7-9066-450e-93e8-f783d0cbbab7',
                    # '6a5e1a48-c646-4ad3-9e50-a333b800af32',
                    # '957474fb-2073-4688-a724-102c3076d4a5',
                    # '16004c65-72c8-4616-88c7-01da30ee6f8a',
                    # '8f6ceaed-a335-4dbe-9086-3d30700e2891',
                    # '4001bae1-7ec6-4111-83ca-13ea8986b986',
                    ]
    catalog=Catalog(db)
    # afxc=AffixCollector(catalog,db,loadfromlift=True) #don't run this if you don't want automatic parsing
    afxc=AffixCollector(catalog,db) #don't run this if you don't want automatic parsing
    for i in afxc.getfromlift():
        pass
    catalog.report()
    # now()
    db.write('userlogs/Test_getparses{}.lift'.format(0))
    # catalog.report()
    parser=Engine(catalog)
    parser.autolevel(5)
    parser.asklevel(0)
    for senseid in senseidsoneform:
        kwargs={'senseid':senseid,
                'entry':ifone(db.nodes.findall('entry/sense[@id="{}"]/..'
                                                    ''.format(senseid))),
                }
        parser.parseentry(**kwargs)
        parser.oneform()
    db.write('userlogs/Test_getparses1.lift')
    now()
    exit()
