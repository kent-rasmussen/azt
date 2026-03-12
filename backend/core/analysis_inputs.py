# coding=UTF-8
import gettext
_ = gettext.gettext

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

def __getattr__(name):
    # Lazy load globals from main
    if name in ('counts', 'me', '_', 'ErrorNotice', 'askerror', 'sysrestart', 'pythonmodules', 'findexecutable', 'main', 'testversion', 'reverttomain', 'buttonwraplength', 'regexdict', 'interfacelang', 'nowruntime', 'callerfn', 'logfinished', 'nn', 'unlist', 'xlp', 'rx', 'exampletype', 'dictofchilddicts', 'dictscompare', 'flatten', 'grouptype', 't', 'openweburl', 'isinterneturl', 'scaleimageifthere', 'loadCAWL', 'saveimagefile', 'ImageFrame', 'TranscribeC', 'TranscribeV', 'TranscribeS', 'ResultWindow', 'Multislice', 'Multicheck', 'Tone', 'Segments', 'ToneFrames', 'CheckParameters', 'Glosslangs', 'Senses', 'WordCollection', 'Parse', 'Sort', 'HasMenus', 'Menus', 'StatusFrame', 'TaskDressing', 'TaskChooser', 'Repository', 'Mercurial', 'Git', 'GitReadOnly', 'Analysis', 'SliceDict', 'StatusDict', 'ExampleDict', 'DictbyLang', 'Settings', 'Entry', 'updateazt', 'LiftChooser', 'SortGroupButtonFrame'):
        import main
        return getattr(main, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

# Mirror main globals lazily to allow bare-name access
for name in ('counts', 'me', '_', 'ErrorNotice', 'askerror', 'sysrestart', 'pythonmodules', 'findexecutable', 'main', 'testversion', 'reverttomain', 'buttonwraplength', 'regexdict', 'interfacelang', 'nowruntime', 'callerfn', 'logfinished', 'nn', 'unlist', 'xlp', 'rx', 'exampletype', 'dictofchilddicts', 'dictscompare', 'flatten', 'grouptype', 't', 'openweburl', 'isinterneturl', 'scaleimageifthere', 'loadCAWL', 'saveimagefile', 'ImageFrame', 'TranscribeC', 'TranscribeV', 'TranscribeS', 'ResultWindow', 'Multislice', 'Multicheck', 'Tone', 'Segments', 'ToneFrames', 'CheckParameters', 'Glosslangs', 'Senses', 'WordCollection', 'Parse', 'Sort', 'HasMenus', 'Menus', 'StatusFrame', 'TaskDressing', 'TaskChooser', 'Repository', 'Mercurial', 'Git', 'GitReadOnly', 'Analysis', 'SliceDict', 'StatusDict', 'ExampleDict', 'DictbyLang', 'Settings', 'Entry', 'updateazt', 'LiftChooser', 'SortGroupButtonFrame'):
    if name not in globals():
        globals()[name] = LazyGlobal(name)

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
    def __init__(self, dict, program):
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
    def checkcodes_by_cvt(self):
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
        if not code:
            code=self.check()
        try:
            return _(self._cvchecknames[code])
        except KeyError:
            return None
    def cvchecknamesdict(self):
        """I reconstruct this here so I can look up names intuitively, having
        built the named checks by type and number of syllables."""
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
        if ps in fields:
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
                }
        self._checknames={
            'S':{ 1:[('lc', _("Whole Citation Word Syllable Profile")),
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
        self.cvchecknamesdict()
        self.checkcodes_by_cvt()

