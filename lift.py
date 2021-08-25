#!/usr/bin/env python3
# coding=UTF-8
"""This module controls manipulation of LIFT files and objects"""
""""(Lexical Interchange FormaT), both for reading and writing"""
from xml.etree import ElementTree as ET
import xmlfns
import sys
import pathlib
import threading
import shutil
import datetime
import re #needed?
import os
import rx
import logging
import ast #For string list interpretation
log = logging.getLogger(__name__)
try: #Allow this module to be used without translation
    _
except:
    def _(x):
        return x
"""This returns the root node of an ElementTree tree (the entire tree as
nodes), to edit the XML."""
class TreeParsed(object):
    def __init__(self, lift):
        self=Tree(lift).parsed
        log.info(self.glosslang)
        Tree.__init__(self, db, guid=guid)
class Error(Exception):
    """Base class for exceptions in this module."""
    pass
class BadParseError(Error):
    def __init__(self, filename):
        self.filename = filename
class Lift(object): #fns called outside of this class call self.nodes here.
    """The job of this class is to expose the LIFT XML as python object
    attributes. Nothing more, not thing else, should be done here."""
    def __init__(self, filename,nsyls=None):
        self.debug=False
        self.filename=filename #lift_file.liftstr()
        self.logfile=filename+".changes"
        """Problems reading a valid LIFT file are dealt with in main.py"""
        try:
            self.read() #load and parse the XML file. (Should this go to check?)
        except:
            raise BadParseError(self.filename)
        backupbits=[filename,'_',
                    datetime.datetime.utcnow().isoformat()[:-16], #once/day
                    '.txt']
        self.backupfilename=''.join(backupbits)
        self.initattribs()
        self.getguids() #sets: self.guids and self.nguids
        self.getsenseids() #sets: self.senseids and self.nsenseids
        log.info("Working on {} with {}, entries "
                    "and {} senses".format(filename,self.nguids,self.nsenseids))
        """These three get all possible langs by type"""
        self.glosslangs() #sets: self.glosslangs
        self.analangs() #sets: self.analangs, self.audiolangs
        self.pss=self.pss() #log.info(self.pss)
        self.getformstosearch() #sets: self.formstosearch[lang][ps] #no guids
        """This is very costly on boot time, so this one line is not used:"""
        # self.getguidformstosearch() #sets: self.guidformstosearch[lang][ps]
        self.citationforms=self.citationforms()
        self.lexemes=self.lexemes()
        self.defaults=[ #these are lift related defaults
                    'analang',
                    'glosslang',
                    'glosslang2',
                    'audiolang'
                ]
        self.slists() #sets: self.c self.v, not done with self.segmentsnotinregexes[lang]
        self.extrasegments() #tell me if there's anything not in a V or C regex.
        self.findduplicateforms()
        self.findduplicateexamples()
        """Think through where this belongs; what classes/functions need it?"""
        log.info("Language initialization done.")
    def initattribs(self):
        # """This dictionary defines where to find each node in the xml {url},
        # and what we're looking for in each case (node, node text, or attribute
        # value."""
        # """Make all urls fully specified for guid, lang, etc; they will be
        # removed if the relevant variable is None."""
        # """In the following language attributes, the field <form> can
        # exist in multiple fields, so pay attention to the difference
        # between
        #     form='{analang}'   (always in the language to be analyzed:
        #                                                 lexeme, citation)
        #     form='{glosslang}' (always in a gloss language:
        #                                                 gloss, definition)
        #     form='{lang}'      (either: field --under entry, sense, or
        #                                                     pronunciation)
        # Controlling this difference allows for things like getting an entry
        # with a form in a particular language, and a gloss in a particular
        # (other) language, and/or a tone description (<field>) in a
        # particular (yet another) language.
        # For now, I'm just going to assume people write meta descriptions
        # in their primary gloss language.
        # url here is a tuple with a base URL and a list of variable names
        # that will be added to it later (and/or removed, if None). The URL
        # should have each in {braces}, and the variable list each in
        # 'quotes', as those are strings/names of variables, to be assigned
        # values later. In any case, the names and number of arguments
        # should match --except for duplicates in the URL, which
        # should occur only once in the variable list. I'm keeping the order
        # the same as far as possible, but that doesn't ultimately matter."""
        a=self.attribdict={}
        a['template']={
            'cm': "Give a prose description here",
            'url': (("url in the XML file, variables OK"
            ),['guid','senseid','ps']),
            'attr': 'script'}
        a['entry']= {
            'cm': 'use to get entries with a given guid or senseid',
            'url':(("entry[@guid='{guid}']/sense[@id='{senseid}']/.."
                    ),['guid','senseid']),
            'attr':'node'}
        a['example']={
            'cm': 'use to get examples with a given guid or senseid',
            'url':(("entry[@guid='{guid}']/sense[@id='{senseid}']/example"
                    ),['guid','senseid']),
            'attr':'node'}
        a['examplebylocation']={
            'cm': 'use to get examples with a given guid or senseid',
            'url':(("entry[@guid='{guid}']/sense[@id='{senseid}']/example"
                    "/field[@type='location']/form[text='{location}']/../.."
                    ),['guid','senseid','location']),
            'attr':'node'}
        a['guidbyps']={
            'cm': 'use to get guids of entries with a given ps',
            'url':(("entry[@guid='{guid}']/sense[@id='{senseid}']"
                    "/grammatical-info[@value='{ps}']/../.."
                    ),['guid','senseid','ps']),
            'attr':'guid'}
        a['senseidbyps']={
            'cm': 'use to get ids of senses with a given ps',
            'url':(("entry/sense[@id='{senseid}']"
                    "/grammatical-info[@value='{ps}']/.."
                    ),['senseid','ps']),
            'attr':'id'}
        a['guidwanyps']={
            'cm': 'use to get guids of entries with any ps',
            'url':(("entry[@guid='{guid}']"
                    "/lexical-unit/form[@lang='{analang}']/../.."
                    "/sense[@id='{senseid}']/grammatical-info[@value]/../.."
                    ),['guid','analang','senseid']),
            'attr':'guid'}
        a['senseidwanyps']={
            'cm': 'use to get ids of senses with any ps',
            'url':(("entry[@guid='{guid}']"
                    "/lexical-unit/form[@lang='{analang}']/../.."
                    "/sense[@id='{senseid}']/grammatical-info[@value]/.."
                    ),['guid','analang','senseid']),
            'attr':'id'}
        a['guidbypronfield']={
            'cm': 'use to get guids of entries with fields at the '
                'pronunciation level',
            'url':(("entry[@guid='{guid}']"
                "/lexical-unit/form[@lang='{analang}']/../.."
                "/sense[@id='{senseid}']/grammatical-info[@value='{ps}']/../.."
                "/pronunciation"
                "/trait[@name='location'][@value='{location}']/.."
                "/form[@lang='{analang}']/.."
                #lang could be any:
                "/field[@type='{fieldtype}']/form[@lang='{lang}']/../../.."
                ),['guid','analang','senseid','ps','location',
                                            'fieldtype','lang']),
            'attr':'guid'}
        a['guidbypronfieldvalue']={
            'cm': 'use to get guids of entries with fields at the '
                    'pronunciation level',
            'url':(("entry[@guid='{guid}']"
                "/lexical-unit/form[@lang='{analang}']/../.."
                "/sense[@id='{senseid}']/grammatical-info[@value='{ps}']/../.."
                    "/pronunciation"
                    "/trait[@name='location'][@value='{location}']/.."
                    "/form[@lang='{analang}']/.."
                    "/field[@type='{fieldtype}']"
                    "/form[@lang='{lang}'][text='{fieldvalue}']"
                    "/../../.." # ^ lang could be any
                    ),['guid','analang','senseid','ps','location',
                                    'fieldtype','lang','fieldvalue']),
            'attr':'guid'}
        a['senseidbyexfieldvalue']={
            'cm': 'use to get guids of entries with fields at the '
                    'example level',
            'url':(("entry[@guid='{guid}']"
                    # "/lexical-unit/form[@lang='{analang}']/../.."
                    "/sense[@id='{senseid}']"
                        "/grammatical-info[@value='{ps}']/.."
                        "/example"
                        "/field[@type='location']"
                        "/form[@lang='{glosslang}'][text='{location}']"
                        "/../.."
                        "/field[@type='{fieldtype}']"
                        "/form[@lang='{glosslang}']"
                        "[text='{fieldvalue}']/../../.."
                    ),['guid','analang','senseid','ps','glosslang',
                                'location','fieldtype','fieldvalue']),
            'attr':'id'}
        a['guidbyexfieldvalue']={
            'cm': 'use to get guids of entries with fields at the '
                    'example level',
            'url':(("entry[@guid='{guid}']"
                    "/lexical-unit/form[@lang='{analang}']/../.."
                    "/sense"
                        "/grammatical-info[@value='{ps}']/.."
                        "/example"
                        "/field[@type='location']"
                        "/form[@lang='{glosslang}'][text='{location}']"
                        "/../.."
                        "/field[@type='{fieldtype}']"
                        "/form[@lang='{glosslang}']"
                        "[text='{fieldvalue}']/../../../.."
                    ),['guid','analang','ps','location','glosslang',
                                            'fieldtype','fieldvalue']),
            'attr':'guid'}
        a['guidbysensefield']={
            'cm': 'use to get guids of entries with fields at the '
                    'sense level',
            'url':(("entry[@guid='{guid}']"
                    "/lexical-unit/form[@lang='{analang}']/../.."
                    "/sense"
                    "/grammatical-info[@value='{ps}']/.."
                    "/field[@type='{fieldtype}']/../.."
                    ),['guid','analang','ps','fieldtype']),
            'attr':'guid'}
        a['guidbyentryfield']={
            'cm': 'use to get guids of entries with fields at the '
                                                        'entry level',
            'url':(("entry[@guid='{guid}']"
                    "/lexical-unit/form[@lang='{analang}']/../.."
                    "/sense[@id='{senseid}']"
                    "/grammatical-info[@value='{ps}']/../.."
                    "/field[@type='{fieldtype}']/.."
                    ),['guid','analang','senseid','ps','fieldtype']),
            'attr':'guid'}
        a['guidbylang']={
            'cm': 'use to get guids of all entries with lexeme of a '
                            'given lang (or not)',
            'url':(("entry[@guid='{guid}']"
                    "/lexical-unit/form[@lang='{analang}']/../.."
                    ),['guid','analang']),
            'attr':'guid'}
        a['guidbysenseid']={
            'cm': 'use to get guids of sense with particular id',
            'url':(("entry[@guid='{guid}']"
                    "/sense[@id='{senseid}']/.."
                    ),['guid','senseid']),
            'attr':'guid'}
        a['guid']={
            'cm': 'use to get guids of all entries (no qualifications)',
            'url':(("entry[@guid='{guid}']"
                    ),['guid']),
            'attr':'guid'}
        a['senseid']={
            'cm': 'use to get ids of all senses (no qualifications)',
            'url':(("entry"
                    "/sense[@id='{senseid}']"
                    ),['senseid']),
            'attr':'id'}
        a['senseidbytoneUFgroup']={
            'cm': 'use to get ids of all senses by tone group',
            'url':(("entry"
                    "/sense[@id='{senseid}']"
                    "/field[@type='{fieldtype}']"
                    "/form[@lang='{lang}'][text='{form}']/../.."
                    ),['senseid','fieldtype','lang','form']),
            'attr':'id'}
        a['guidbylexeme']={
            'cm': 'use to get guid by ps and lexeme in the specified '
                                'language (no reference to fields)',
            'url':(("entry[@guid='{guid}']"
                    "/sense[@id='{senseid}']"
                    "/grammatical-info[@value='{ps}']/../.."
                    "/lexical-unit"
                    "/form[@lang='{analang}'][text='{form}']"
                    "/../.." # ^ [.=’text'] not until python 3.7
                    ),['guid','senseid','ps','analang','form']),
            'attr':'guid'}
        a['guidbysense']={
            'cm': 'use to get guid by ps and citation form in the '
                        'specified language (no reference to fields)',
            'url':(("entry[@guid='{guid}']"
                    "/sense[@id='{senseid}']/.."
                    ),['guid','senseid']),
            'attr':'guid'}
        a['senseidbylexeme']={
            'cm': 'use to get senseid by ps and lexeme in the '
                        'specified language (no reference to fields)',
            'url':(("entry[@guid='{guid}']"
                    "/lexical-unit"
                    "/form[@lang='{analang}'][text='{form}']/../.."
                    "/sense[@id='{senseid}']"
                    "/grammatical-info[@value='{ps}']/.."
                    ),['guid','analang','form','senseid','ps']),
            'attr':'id'}
        a['guidbycitation']={
            'cm': 'use to get guid by ps and citation form in the '
                        'specified language (no reference to fields)',
            'url':(("entry[@guid='{guid}']"
                    "/sense[@id='{senseid}']"
                    "/grammatical-info[@value='{ps}']/../.."
                    "/citation"
                    "/form[@lang=guid'{analang}'][text='{form}']"
                    "/../.." # ^ [].=’text'] not until python 3.7
                    ),['guid','senseid','ps','analang','form']),
            'attr':'guid'}
        a['toneUFfieldvalue']={
            'cm': 'use to get tone UF values of all senses within the '
                    'constraints specified.',
            'url':(("entry[@guid='{guid}']"
                    "/sense[@id='{senseid}']"
                    "/grammatical-info[@value='{ps}']/.."
                    "/field[@type='{fieldtype}']"
                    "/form[@lang='{lang}']/text"
                    ),['guid','senseid','ps','fieldtype','lang']),
            'attr':'nodetext'}
        a['lexemenode']={
            'cm': 'use to get lexemes of all entries with a form '
                    'in the specified language (no reference to fields)',
            'url':(("entry[@guid='{guid}']"
                    "/sense[@id='{senseid}']"
                    "/grammatical-info[@value='{ps}']/../.."
                    "/lexical-unit/form[@lang='{analang}']/.."
                    ),['guid','senseid','ps','analang']),
            'attr':'node'}
        a['lexeme']={
            'cm': 'use to get lexemes of all entries with a form in '
                    'the specified language (no reference to fields)',
            'url':(("entry[@guid='{guid}']"
                    "/sense[@id='{senseid}']"
                    "/grammatical-info[@value='{ps}']/../.."
                    "/lexical-unit/form[@lang='{analang}']/text"
                    ),['guid','senseid','ps','analang']),
            'attr':'nodetext'}
        a['citationnode']={
            'cm': 'use to get citation forms of one or all entries '
                    'with a form in the specified language (no '
                    'reference to fields)',
            'url':(("entry[@guid='{guid}']"
                    "/sense[@id='{senseid}']"
                    "/grammatical-info[@value='{ps}']/../.."
                    "/citation/form[@lang='{analang}']/.."
                    ),['guid','senseid','ps','analang']),
            'attr':'node'}
        a['citation']={
            'cm': 'use to get citation forms of one or all entries '
            'with a form in the specified language (no reference '
            'to fields)',
            'url':(("entry[@guid='{guid}']"
                    "/sense[@id='{senseid}']"
                    "/grammatical-info[@value='{ps}']/../.."
                    "/citation/form[@lang='{analang}']/text"
                    ),['guid','senseid','ps','analang']),
            'attr':'nodetext'}
        a['definition']={
            'cm': 'use to get glosses of entries',
            'url':(("entry[@guid='{guid}']"
                    "/sense[@id='{senseid}']"
                    "/grammatical-info[@value='{ps}']/.."
                    "/definition"
                    "/form[@lang='{glosslang}']/text"
                    ),['guid','senseid','ps','glosslang']),
            'attr':'nodetext'}
        a['gloss']={
            'cm': 'use to get glosses of entries',
            'url':(("entry[@guid='{guid}']"
                    "/sense[@id='{senseid}']"
                    "/grammatical-info[@value='{ps}']/.."
                    "/gloss[@lang='{glosslang}']/text"
                    ),['guid','senseid','ps','glosslang']),
            'attr':'nodetext'}
        a['glossofexample']={
            'cm': 'use to get glosses/translations of examples',
            'url':(("translation[@type='Frame translation']"
                        "/form[@lang='{glosslang}']/text"
                    ),['glosslang']),
            'attr':'nodetext'}
        a['formofexample']={
            'cm': 'use to get analang forms of examples',
            'url':(("form[@lang='{analang}']/text"
                    ),['analang']),
            'attr':'nodetext'}
        a['fieldnode']={
            'cm': 'use to get whole field nodes (to modify)',
            'url':(("entry[@guid='{guid}']"
                    "/sense[@id='{senseid}']"
                    "/grammatical-info[@value='{ps}']/../.."
                    "/field[@type='{fieldtype}']/form[@lang='{lang}']"
                    "/.."
                    ),['guid','senseid','ps','fieldtype','lang']),
            'attr':'node'}
        a['fieldname']={
            'cm': 'use to get value(s) for type of field in sense',
            'url':(("entry[@guid='{guid}']"
                    "/sense[@id='{senseid}']"
                    "/grammatical-info[@value='{ps}']/../.."
                    "/field"
                    ),['guid','senseid','ps']),
            'attr':'type'}
        a['fieldvalue']={
            'cm': 'use to get value(s) for field(s) of a specified '
                    '(or all) type(s) with a form in the specified (or '
                    'any) language for one or all entries (no '
                    'reference to fields, nor to lexeme form language)',
            'url':(("entry[@guid='{guid}']"
                    "/sense[@id='{senseid}']"
                    "/grammatical-info[@value='{ps}']/../.."
                    "/field[@type='{fieldtype}']"
                    "/form[@lang='{lang}']/text" #This can be ANY lang.
                    ),['guid','senseid','ps','fieldtype','lang']),
            'attr':'nodetext'}
        a['pronunciationbylocation']={
            'cm': 'use to get value(s) for pronunciation information '
                                            'for a given location',
            'url':(("entry[@guid='{guid}']"
                    "/sense[@id='{senseid}']"
                    "/grammatical-info[@value='{ps}']/../.."
                    "/pronunciation"
                    "/trait[@name='location'][@value='{location}']"
                    "/../form[@lang='{analang}']/text"
                    ),['guid','senseid','ps','location','analang']),
            'attr':'nodetext'}
        a['pronunciationfieldname']={
            'cm': 'use to get value(s) for a field type of a specified '
            '(or not) location',
            'url':(("entry[@guid='{guid}']"
                    "/sense[@id='{senseid}']"
                    "/grammatical-info[@value='{ps}']/../.."
                    "/pronunciation"
                    "/trait[@name='location'][@value='{location}']"
                    "/../field"),['guid','senseid','ps','location']),
            'attr':'type'}
        a['pronunciationfieldvalue']={
            'cm': 'use to get value(s) for <<document later>>',
            'url':(("entry[@guid='{guid}']"
                    "/sense[@id='{senseid}']"
                    "/grammatical-info[@value='{ps}']/../.."
                    "/pronunciation"
                    "/trait[@name='location'][@value='{location}']/.."
                    "/field[@type='{fieldtype}']"
                    "/form[@lang='{lang}']/text"
                    ),['guid','senseid','ps','location','fieldtype',
                    'lang']), #not necessarily glosslang or analang...
            'attr':'nodetext'}
        a['exfieldvalue']={
            'cm': 'use to get values of fields at the example level',
            'url':(("entry[@guid='{guid}']"
                    # "/lexical-unit/form[@lang='{analang}']/../.."
                    "/sense[@id='{senseid}']"
                        "/grammatical-info[@value='{ps}']/.."
                        "/example"
                        "/field[@type='location']"
                        "/form[@lang='{glosslang}']"
                            "[text='{location}']/../.."
                        "/field[@type='{fieldtype}']"
                        "/form[@lang='{glosslang}']/text"
                    ),['guid','analang','senseid','ps','glosslang',
                                            'location','fieldtype']),
            'attr':'nodetext'}
        a['examplewfieldlocvaluefromsense']={
            'cm': 'use to get an example with a given tone/exfield '
                                'when you have the sense node.',
            'url':(("example/field[@type='location']"
                        "/form[text='{location}']/../.."
                        "/field[@type='{fieldtype}']"
                        "/form[text='{fieldvalue}']/../.."
                        ),['location','fieldtype','fieldvalue']),
                'attr':'nodetext'}
        a['exfieldlocation']={
            'cm': 'use to get location of fields at the example level',
            'url':(("entry[@guid='{guid}']"
                    "/lexical-unit/form[@lang='{analang}']/../.."
                    "/sense[@id='{senseid}']"
                    "/grammatical-info[@value='{ps}']/.."
                    "/example"
                    "/field[@type='location']"
                    "/form[@lang='{glosslang}']/text"
                    ),['guid','analang','senseid','ps','glosslang']),
            'attr':'nodetext'}
        a['pronunciationfieldlocation']={
            'cm': 'use to get value(s) for pronunciation location'
                                                        '/context',
            'url':(("entry[@guid='{guid}']"
                    "/sense[@id='{senseid}']"
                    "/grammatical-info[@value='{ps}']/../.."
                    "/pronunciation"
                    "/field[@type='{fieldtype}']/.."
                    "/trait[@name='location']"
                    ),['guid','senseid','ps','fieldtype']),
            'attr':'value'}
        a['pronunciation']={
            'cm': 'use to get value(s) for pronunciation in fields '
                                            'with location specified',
            'url':(("entry[@guid='{guid}']"
                    "/sense[@id='{senseid}']"
                    "/grammatical-info[@value='{ps}']/../.."
                    "/pronunciation"
                    "/trait[@name='location'][@value='{location}']/.."
                    "/form[@lang='{glosslang}']/text"
                    ),['guid','senseid','ps','location','glosslang']),
            'attr':'nodetext'}
        a['lexemelang']={
            'cm': "analysis languages used in lexemes",
            'url':(("entry[@guid='{guid}']"
                    "/sense[@id='{senseid}']"
                    "/grammatical-info[@value='{ps}']/../.."
                    "/lexical-unit/form"
                    ),['guid','senseid','ps']),
            'attr': 'lang'}
        a['citationlang']={
            'cm': "analysis languages used in citation forms",
            'url':(("entry[@guid='{guid}']"
                    "/sense[@id='{senseid}']"
                    "/grammatical-info[@value='{ps}']/../.."
                    "/citation/form"
                    ),['guid','senseid','ps']),
            'attr': 'lang'}
        a['pronunciationlang']={
            'cm': "analysis languages used in citation forms",
            'url':(("entry[@guid='{guid}']"
                    "/sense[@id='{senseid}']"
                    "/grammatical-info[@value='{ps}']/../.."
                    "/pronunciation/form"
                    ),['guid','senseid','ps']),
            'attr': 'lang'}
        a['glosslang']={
            'cm': "gloss languages used in glosses",
            'url':(("entry[@guid='{guid}']"
                    "/sense[@id='{senseid}']"
                    "/grammatical-info[@value='{ps}']/.."
                    "/gloss"
                    ),['guid','senseid','ps']),
            'attr': 'lang'}
        a['defnlang']={
            'cm': "gloss languages used in definitions",
            'url':(("entry[@guid='{guid}']"
                    "/sense[@id='{senseid}']"
                    "/grammatical-info[@value='{ps}']/.."
                    "/definition"
                    "/form"),['guid','senseid','ps']),
            'attr': 'lang'}
        a['illustration']={
            'cm': "Illustration by entry",
            'url': (("entry[@guid='{guid}']"
                    "/sense[@id='{senseid}']/illustration"
                    ),['guid','senseid','ps']),
            'attr': 'href'}
        a['ps']={
            'cm': "Part of speech, or grammatical category",
            'url': (("entry[@guid='{guid}']"
                    "/sense[@id='{senseid}']"
                    "/grammatical-info"
                    ),['guid','senseid']),
            'attr': 'value'}
        print(self.attribdict)
    def geturlnattr(self, attribute, **kwargs):
        if attribute == 'attributes':
            return self.attribdict.keys()
        if attribute not in self.attribdict:
            log.info("Sorry, {} isn't defined yet. This is what's "
                                "available:".format(attribute))
            for line in list(self.attribdict.keys()):
                try:
                    log.info(' '.join(line, '\t',self.attribdict[line]['cm']))
                except:
                    log.info('{}\tUNDOCUMENTED?!?!'.format(line))
            log.info("This is where that key was called; fix it, and try again:")
        """I should also add/remove pronunciation or other systematic things here"""
        url=self.attribdict[attribute]['url']
        for field in url[1]:
            if field not in kwargs:
                kwargs[field]=None
        url=(url[0],kwargs)
        url=buildurl(url)
        log.log(2,'After buildurl: {}'.format(url))
        url=removenone(url)
        log.log(2,'After removenone: {}'.format(url))
        log.log(1,'Ori: {}'.format(self.attribdict[attribute]['url']))
        return {'url':url,'attr':self.attribdict[attribute]['attr']}
    def get(self, attribute, **kwargs):
        """kwargs are guid=None, senseid=None, analang=None,
            glosslang=None, lang=None, ps=None, form=None, fieldtype=None,
            location=None, fieldvalue=None, showurl=False):"""
        """This needs to work when there are multiple languages, etc.
        I think we should iterate over possibilities, if none are specified.
        over lang, what else?
        NB: this would create nested dictionaries... We need to be able to
        access them consistently later."""
        """I need to be careful to not mix up lang=glosslang and lang=analang:
        @lang should only be used here when referring to a <field> field."""
        if attribute == 'Test':
            from random import randint
            guid=self.guids[randint(0, len(self.guids))-1]
            log.info("Showing info for randomly selected *entry*: {}".format(guid))
            for attribute in self.geturlnattr('attributes'):
                log.info('{}: {}'.format(attribute,self.get(attribute,guid=guid)))#,showurl=True
            senseid=self.senseids[randint(0, len(self.senseids))-1]
            log.info("Showing info for randomly selected *sense*: {}".format(senseid))
            for attribute in self.geturlnattr('attributes'):
                log.info('{}: {}'.format(attribute,self.get(attribute,senseid=senseid)))#,showurl=True
            return
        log.log(3,'kwargs: {}'.format(kwargs))
        """pull output from urlnattr, where first is string with {}, second
        is strings naming fields. convert those names to field values here,
        once those fields/values have been defined.
        """
        """This is slightly faster than kwargs"""
        # was: urlnattr=attributesettings(attribute,guid,senseid,analang,
        #         glosslang, lang,ps,form,
        #         fieldtype,location,
        #         fieldvalue=fieldvalue
        urlnattr=self.geturlnattr(attribute, **kwargs)
        url=urlnattr['url']
        if 'showurl' in kwargs and kwargs['showurl']==True:
            log.info(url)
        try:
            nodeset=self.nodes.findall(url) #This is the only place we need self=lift
        except BaseException as e:
            log.error("Problem getting url: {} ({})".format(url,e))
            return
        output=[]
        attr=urlnattr['attr']
        for node in nodeset:
            if attr == 'nodetext':
                if node is not None:
                    log.log(1,"Returning node text")
                    output+=[node.text]
            elif attr == 'node':
                if node is not None:
                    log.log(1,"Returning whole node")
                    output+=[node]
            else:
                log.log(1,"Returning node attribute")
                output+=[node.get(attr)]
        return output
    def makenewguid(self):
        from random import randint
        log.info("Making a new unique guid")
        """f'{int:x}:' gives int in lowercase hexidecimal"""
        def gimmeint():
            return f'{randint(0, 15):x}'
        def rxi(y):
            o=''
            for i in range(y):
                o+=gimmeint()
            return o
        allguids=self.guids+self.senseids
        guid=allguids[0]
        while guid in allguids:
            guid=rxi(8)+'-'+rxi(4)+'-'+rxi(4)+'-'+rxi(4)+'-'+rxi(12)
        return guid
    def addentry(self, showurl=False, **kwargs):
        # kwargs are ps, analang, glosslang, langform, glossform,glosslang2,
        # glossform2
        log.info("Adding an entry")
        self.makenewguid()
        guid=senseid=self.makenewguid()
        while guid == senseid:
            senseid=self.makenewguid()
        log.info('newguid: {}'.format(guid))
        log.info('newsenseid: {}'.format(senseid))
        now=getnow()
        analang=kwargs['analang']
        entry=ET.SubElement(self.nodes, 'entry', attrib={
                                'dateCreated':now,
                                'dateModified':now,
                                'guid':guid,
                                'id':(kwargs['form'][analang]+'_'+str(guid))
                                })
        lexicalunit=ET.SubElement(entry, 'lexical-unit', attrib={})
        form=ET.SubElement(lexicalunit, 'form',
                                        attrib={'lang':analang})
        text=ET.SubElement(form, 'text')
        text.text=kwargs['form'][analang]
        """At some point, I'll want to distinguish between these two"""
        citation=ET.SubElement(entry, 'citation', attrib={})
        form=ET.SubElement(citation, 'form', attrib={'lang':analang})
        text=ET.SubElement(form, 'text')
        text.text=kwargs['form'][analang]
        del kwargs['form'][analang] #because we're done with this.
        sense=ET.SubElement(entry, 'sense', attrib={'id':senseid})
        grammaticalinfo=ET.SubElement(sense, 'grammatical-info',
                                            attrib={'value':kwargs['ps']})
        definition=ET.SubElement(sense, 'definition')
        for glosslang in kwargs['form']: #now just glosslangs
            form=ET.SubElement(definition, 'form',
                                attrib={'lang':glosslang})
            text=ET.SubElement(form, 'text')
            text.text=kwargs['form'][glosslang]
            gloss=ET.SubElement(sense, 'gloss',
                                attrib={'lang':glosslang})
            text=ET.SubElement(gloss, 'text')
            text.text=kwargs['form'][glosslang]
        self.write()
        """Since we added a guid and senseid, we want to refresh these"""
        self.getguids()
        self.getsenseids()
        return senseid
    def modverificationnode(self,senseid,vtype,add=None,rm=None,addifrmd=False):
        nodes=self.addverificationnode(senseid,vtype=vtype)
        vf=nodes[0]
        sensenode=nodes[1]
        if vf is None:
            log.info("Sorry, this didn't return a node: {}".format(senseid))
            return
        if vf.text is not None:
            log.log(2,"{}; {}".format(vf.text, type(vf.text)))
            try:
                l=ast.literal_eval(vf.text)
            except SyntaxError: #if the literal eval doesn't work, it's a string
                l=vf.text
            log.log(2,"{}; {}".format(l, type(l)))
            if type(l) != list: #in case eval worked, but didn't produce a list
                log.log(2,"One item: {}; {}".format(l, type(l)))
                l=[l,]
        else:
            log.log(2,"empty verification list found")
            l=list()
        changed=False
        if rm != None and rm in l:
            i=l.index(rm) #be ready to replace
            l.remove(rm)
            changed=True
        else:
            i=len(l)
        if (add != None and add not in l #if there, v-if rmd, or not changing
                and (addifrmd == False or changed == True)):
            l.insert(i,add) #put where removed from, if done.
            changed=True
        vf.text=str(l)
        if changed == True:
            self.updatemoddatetime(senseid=senseid)
        log.log(2,"Empty node? {}; {}".format(vf.text,l))
        if l == []:
            log.debug("removing empty node")
            sensenode.remove(vf)
        else:
            log.log(2,"Not removing empty node")
    def addverificationnode(self,senseid,vtype):
        node=self.getsensenode(senseid=senseid)
        if node is None:
            log.info("Sorry, this didn't return a node: {}".format(senseid))
            return
        vf=node.find("field[@type='{} {}']".format(vtype,"verification"))
        if vf == None:
            vf=ET.SubElement(node, 'field',
                                attrib={'type':"{} verification".format(vtype)})
        return (vf,node)
    def getentrynode(self,senseid,showurl=False):
        """Get the sense node"""
        urlnattr=self.geturlnattr('entry',senseid=senseid)
        url=urlnattr['url']
        if showurl==True:
            log.info(url)
        node=self.nodes.find(url) #this should always find just one node
        return node
    def getsensenode(self,senseid,showurl=False):
        """Get the sense node"""
        urlnattr=self.geturlnattr('senseid',senseid=senseid)
        url=urlnattr['url']
        if showurl==True:
            log.info(url)
        node=self.nodes.find(url) #this should always find just one node
        return node
    def addexamplefields(self,showurl=False,**kwargs):
        # ,guid,senseid,analang,glosslang,glosslang2,forms,
        # fieldtype,location,fieldvalue,ps=None
        # This fuction will add an XML node to the lift tree, like a new
        # example field.
        # The program should know before calling this, that there isn't
        # already the relevant node --since it is agnostic of what is already
        # there.
        log.info("Adding {} value to {} location in {} fieldtype {} senseid {} "
                "guid (in lift.py)".format(kwargs['fieldvalue'],
                                        kwargs['location'],kwargs['fieldtype'],
                                        kwargs['senseid'],kwargs['guid']))
        node=self.getsensenode(senseid=kwargs['senseid'])
        if node is None:
            log.info("Sorry, this didn't return a node: {}".format(
                                                            kwargs['senseid']))
            return
        # Logic to check if this example already here
        # This function returns a text node (from any one of a number of
        # example nodes, which match form, gloss and location) containing a
        # tone sorting value, or None (if no example nodes match form, gloss
        # and location)
        #We're adding a node to kwargs here.
        exfieldvalue=self.exampleissameasnew(**kwargs,node=node,showurl=False)
        if exfieldvalue is None: #If not already there, make it.
            log.info("Didn't find that example already there, creating it...")
            p=ET.SubElement(node, 'example')
            form=ET.SubElement(p,'form',attrib={'lang':kwargs['analang']})
            t=ET.SubElement(form,'text')
            t.text=kwargs['forms'][kwargs['analang']]
            """Until I have reason to do otherwise, I'm going to assume these
            fields are being filled in in the glosslang language."""
            fieldgloss=ET.SubElement(p,'translation',attrib={'type':
                                                        'Frame translation'})
            for lang in [kwargs['glosslang'],kwargs['glosslang2']]:
                if lang != None:
                    form=ET.SubElement(fieldgloss,'form',
                                        attrib={'lang':lang})
                    glosstext=ET.SubElement(form,'text')
                    glosstext.text=kwargs['forms'][lang]
            exfield=ET.SubElement(p,'field',
                                    attrib={'type':kwargs['fieldtype']})
            form=ET.SubElement(exfield,'form',
                                    attrib={'lang':kwargs['glosslang']})
            exfieldvalue=ET.SubElement(form,'text')
            locfield=ET.SubElement(p,'field',attrib={'type':'location'})
            form=ET.SubElement(locfield,'form',
                                    attrib={'lang':kwargs['glosslang']})
            fieldlocation=ET.SubElement(form,'text')
            fieldlocation.text=kwargs['location']
        else:
            if self.debug == True:
                log.info("=> Found that example already there")
        exfieldvalue.text=kwargs['fieldvalue'] #change this *one* value, either way.
        if 'guid' in kwargs:
            self.updatemoddatetime(guid=kwargs['guid'],senseid=kwargs['senseid'])
        else:
            self.updatemoddatetime(senseid=kwargs['senseid'])
        if self.debug == True:
            log.info("add langform: {}".format(kwargs['forms'][kwargs['analang']]))
            log.info("add tone: {}".format(['fieldvalue']))
            log.info("add gloss: {}".format(kwargs['forms'][kwargs['glosslang']]))
            if glosslang2 != None:
                log.info(' '.join("add gloss2:", kwargs['forms'][kwargs['glosslang2']]))
    def forminnode(self,node,value):
        # Returns True if `value` is in *any* text node child of any form child
        # of node: [node/'form'/'text' = value]
        for f in node.findall('form'):
            for t in f.findall('text'):
                if t.text == value:
                    return True
        return False
    def convertalltodecomposed(self):
        for form in self.nodes.findall('.//form'):
            if form.get('lang') in self.analangs:
                for t in form.findall('.//text'):
                    t.text=rx.makeprecomposed(t.text)
    def exampleisnotsameasnew(self, showurl=False, **kwargs):
        # guid,senseid,analang, glosslang, glosslang2, forms, fieldtype,
        # location,fieldvalue,example,ps=None,
        # """This checks all the above information, to see if we're dealing with
        # the same example or not. Stop and return nothing at first node that
        # doesn't match (from form, translation and location). If they all match,
        # then return the tone value node to change."""
        tonevalue='' # set now, will change later, or not...
        log.log(3,"Looking for bits that don't match")
        if kwargs['example'] == None:
            log.info("Hey! You gave me an empty example!")
            return
        for node in kwargs['example']:
            try:
                log.log(2,'Node: {} ; {}'.format(node.tag,
                                                node.find('.//text').text))
            except:
                log.log(2,'Node: {} ; Likely no text node!'.format(node.tag))
            if (node.tag == 'form'):
                if ((node.get('lang') == kwargs['analang'])
                and (node.find('text').text != kwargs['forms'][kwargs['analang']])):
                    log.log(3,'{} == {}; {} != {}'.format(node.get('lang'),
                            kwargs['analang'], node.find('text').text, kwargs['forms'][kwargs['analang']]))
                    return
            elif ((node.tag == 'translation') and
                                (node.get('type') == 'Frame translation')):
                for form in node.find('form'):
                    if (((form.get('lang') == kwargs['analang']) and
                        (not self.forminnode(node,
                            kwargs['forms'][kwargs['analang']]))) or
                        (('glosslang2' in kwargs) and
                        (kwargs['glosslang2'] != None) and
                        (form.get('lang') == kwargs['glosslang2']) and
                        (not self.forminnode(node,
                            kwargs['forms'][kwargs['glosslang2']])))):
                        log.log(5,'translation {} != {}'.format(
                                    node.find('form/text').text, kwargs['forms']))
                        return
            elif (node.tag == 'field'):
                if (node.get('type') == 'location'):
                    if not self.forminnode(node,kwargs['location']):
                        log.log(3,'location {} not in {}'.format(
                                                    kwargs['location'],node))
                        return
                if (node.get('type') == 'tone'):
                    for form in node:
                        if ((form.get('lang') == kwargs['glosslang'])
                        or (form.get('lang') == kwargs['glosslang2'])):
                            """This is set once per example, since this
                            function runs on an example node"""
                            tonevalue=form.find('text')
                            log.debug('tone value found: {}'.format(
                                                            tonevalue.text))
                        else:
                            log.info("Not the same lang for tone form: {}"
                                        "".format(form.get('lang')))
                            return
            else:
                log.debug("Not sure what kind of node I'm dealing with! ({})"
                                                            "".format(node.tag))
        return tonevalue
    def exampleissameasnew(self,showurl=False, **kwargs):
        # ,guid,senseid,analang, glosslang,glosslang2,forms, fieldtype,
        # location,fieldvalue,node,ps=None
        """This looks for any example in the given sense node, with the same
        form, gloss, and location values"""
        if self.debug == True:
            log.info('Looking for an example node matching these form and gloss'
                'elements: {}'.format(forms))
        for example in kwargs['node'].findall('example'):
            valuenode=self.exampleisnotsameasnew(**kwargs, example=example
                            # guid,senseid,analang,
                            # glosslang,glosslang2,forms,
                            # fieldtype,
                            # location,fieldvalue,example,ps=None
                            ,showurl=False)
            if valuenode != '': #None: #i.e., they *are* the same node
                return valuenode #if you find the example, we're done looking
            else: #if not, just keep looking, at next example node
                log.debug('=> This is not the example we are looking '
                            'for: {}'.format(valuenode))
    def findduplicateforms(self):
        for entry in self.nodes:
            for node in entry:
                if ((node.tag == 'lexical-unit') or (node.tag == 'citation')):
                    forms=node.findall('form')
                    removed=list()
                    for form in forms:
                        f1i=forms.index(form)
                        for form2 in forms:
                            f2i=forms.index(form2)
                            if (f2i <= f1i) or (form2 in removed):
                                log.log(3,"{} <= {} or form {} already removed; "
                                            "continuing.".format(f2i,f2i,f1i))
                                continue
                            if (form.get('lang') == form2.get('lang') and
                            form.find('text').text == form2.find('text').text):
                                log.debug("Found {} {} {}".format(f1i,
                                                    form.get('lang'),
                                                    form.find('text').text,
                                                    ))
                                log.debug("Found {} {} {}".format(f2i,
                                                    form2.get('lang'),
                                                    form2.find('text').text
                                                    ))
                                log.debug("Removing form {} {} {}".format(f2i,
                                                    form2.get('lang'),
                                                    form2.find('text').text
                                                    ))
                                node.remove(form2)
                                removed.append(form2)
                            else:
                                log.log(3,"Not removing form")
        self.write()
    def findduplicateexamples(self):
        def getexdict(example):
            analangs=[]
            otheranalangs=[]
            glosslangs=[]
            forms={}
            analang=''
            glosslang=''
            glosslang2=''
            location=''
            tonevalue=''
            log.log(3,"Working on example {} (this sense: {})".format(exn,exindex))
            formnodes=example.findall('form') #multiple/sense
            translationformnodes=example.findall(
                        "translation[@type='Frame translation']/form") #just one/sense
            if formnodes != None:
                for formnode in formnodes:
                    lang=formnode.get('lang')
                    formnodetext=formnode.find('text')
                    if formnodetext is not None:
                        analangs.append(lang)
                        forms[lang]=formnodetext.text
                    else:
                        log.log(3,"No formnodetext! (lang: {})".format(lang))
                if analangs != []:
                    log.log(2,"Analangs: {}".format(analangs))
                    analang=analangs[0]
                    if len(analangs) >1:
                        otheranalangs=analangs[1:]
                else:
                    analang=None
            else:
                log.error("No form node!")
            if translationformnodes != None:
                for formnode in translationformnodes:
                    lang=formnode.get('lang')
                    formnodetext=formnode.find('text')
                    if formnodetext != None:
                        glosslangs.append(lang)
                        forms[lang]=formnodetext.text
                    else:
                        log.log(4,"No glossformnodetext! ({}; lang: {})".format(
                                                            lang,formnodetext))
                log.log(2,"glosslangs: {}".format(glosslangs))
                if len(glosslangs) >1:
                    glosslang2=glosslangs[1]
                else:
                    glosslang2=None
                    log.log(3,"No glosslang2formnodetext; hope that's OK!")
                if len(glosslangs) >0:
                    glosslang=glosslangs[0]
                else:
                    glosslang=None
                    log.log(4,"No glosslangformnodetext!")
            else:
                log.log(4,"No translation node!")
            #We don't care about form[@lang] for these:
            locationnode=example.find("field[@type='location']/form/text")
            valuenode=example.find("field[@type='tone']/form/text")
            if locationnode != None:
                location=locationnode.text
            else:
                location=None
            if valuenode != None:
                tonevalue=valuenode.text
            else:
                tonevalue='' #this means an empty/missing tone node only.
            return (forms, analang, glosslang, glosslang2, location, tonevalue,
                                                                otheranalangs)
        def compare(x,y):
            same=0
            for i in range(len(x)):
                if x[i] == y[i]:
                    log.log(2,"{} =".format(x[i]))
                    log.log(2,"{}".format(y[i]))
                    same+=1
                else:
                    log.log(2,"{} ≠".format(x[i]))
                    log.log(2,"{}!".format(y[i]))
                    same=False
            return same
        forms={}
        entries=self.nodes.findall('entry')
        exn=0
        for entry in entries:
            entindex=entries.index(entry)
            log.log(2,"Working on entry {}: {}".format(entindex,
                                                        entry.get('guid')))
            senses=entry.findall('sense')
            for sense in senses:
                senseindex=senses.index(sense)
                log.log(3,"Working on sense {}: {}".format(senseindex,
                                                        sense.get('id')))
                examples=sense.findall('example')
                for example in examples:
                    #If empty node, remove it
                    if len(example) == 0:
                        log.info("Deleting Empty example in {}".format(
                                                            entry.get('guid')))
                        sense.remove(example)
                        continue
                    exn+=1
                    exindex=list(examples).index(example)
                    ex1=getexdict(example)
                    if ex1[1] == None:
                        log.info("No analang found for example {} in {}"
                                "".format(ex2index,sense.get('id')))
                        continue
                    for example2 in examples:
                        ex2index=list(examples).index(example2)
                        if exindex >= ex2index:
                            log.log(2,"Comparing example {} with example {}; "
                                    "skipping.".format(exindex,ex2index))
                            continue
                        else:
                            log.log(2,"Comparing example {} with example {}."
                                    "".format(exindex,ex2index))
                        #here we replicate/skip exampleissameasnew
                        ex2=getexdict(example2)
                        if ex2[1] == None:
                            log.info("No analang found for example {} in {}"
                                        "".format(ex2index,sense.get('id')))
                            continue
                        othertonevalue=self.exampleisnotsameasnew(
                                                node=sense,
                                                example=example2,
                                                forms=ex1[0],
                                                analang=ex1[1],
                                                glosslang=ex1[2],
                                                glosslang2=ex1[3],
                                                location=ex1[4]
                                                # ,showurl=True
                                                )
                        if othertonevalue == None:
                            log.log(2,"No same node found!")
                        elif not ((othertonevalue == ex1[5]) or
                                ((type(othertonevalue) is ET.Element) and
                                (othertonevalue.text == ex1[5]))):
                            try:
                                log.log(3,"Same node, different value! ({}!={})"
                                            "; copying over {}?{}".format(
                                        othertonevalue.text,
                                        ex1[5],type(othertonevalue.text),
                                        type(ex1[5])))
                                if ((othertonevalue.text == '') or
                                            (othertonevalue.text == None)):
                                    log.log(3,"empty othertonevalue node")
                                    othertonevalue.text == ex1[5]
                                    ex2=getexdict(example)
                                elif ((ex1[5] == '') or (ex1[5] == None)):
                                    log.log(3,"empty ex1 tonevalue node")
                                    t=example.find("field[@type='tone']/form/"
                                                "text")
                                    if t is not None:
                                        log.log(2,"tone node there, adding "
                                                                    "tonevalue")
                                        t.text=othertonevalue.text
                                    else:
                                        log.log(2,"No tone node there, adding")
                                        fld=ET.SubElement(example,'field',
                                                        attrib={'type':'tone'})
                                        f=ET.SubElement(fld,'form',
                                                        attrib={'lang':ex1[2]})
                                        g=ET.SubElement(f,'text')
                                        g.text=othertonevalue.text
                                    ex1=getexdict(example)
                                else:
                                    log.error("Huh? tonevalue nodes: {}; {} in "
                                                "{}".format(othertonevalue,
                                                ex1[5], sense.get('id')))
                            except:
                                log.log(2,"Same text, different value! ({}!={})"
                                            "; copying over {}?{}".format(
                                            othertonevalue,
                                            ex1[5],type(othertonevalue),
                                            type(ex1[5])))
                                if (ex2[5] == '') or (ex2[5] == None):
                                    log.log(2,"empty ex2 tonevalue node")
                                    t=example2.find("field[@type='tone']/"
                                                "form/text")
                                    if t is not None:
                                        t.text=ex1[5]
                                    else:
                                        fld=ET.SubElement(example2,'field',
                                                        attrib={'type':'tone'})
                                        f=ET.SubElement(fld,'form',
                                                        attrib={'lang':ex1[2]})
                                        g=ET.SubElement(f,'text')
                                        g.text=ex1[5]
                                    ex2=getexdict(example)
                                else:
                                    log.error("Huh? tonevalues: {}; {} in {}"
                                                "".format(othertonevalue,
                                                ex1[5], sense.get('id')))
                            compare(ex1,ex2) #This compares tuples
                        if (othertonevalue != None) and (ex2[5] == ex1[5]):
                            try:
                                log.log(2,"Same node, same value! ({}={}-{})"
                                            "".format(
                                            ex1[5],othertonevalue.text,ex2[5]))
                            except:
                                log.log(2,"Same text, same value! ({}={}-{})"
                                            "".format(
                                            ex1[5],othertonevalue,ex2[5]))
                            compare(ex1,ex2) #This compares tuples
                            if (ex1[6] == []) and (ex2[6] == []):
                                log.info("No second analang; removing second "
                                    "example from {}.".format(sense.get('id')))
                                if example2 in sense:
                                    sense.remove(example2)
                            for lang in ex1[6]:
                                if lang in ex2[6]:
                                    log.log(2,"Language {} found in both "
                                                    "examples.".format(lang))
                                    if ex1[0][lang] == ex2[0][lang]:
                                        log.log(2,"Language {} content same in "
                                                "both examples.".format(lang))
                                        if example2 in sense:
                                            try:
                                                log.info("Removing second "
                                                        "example from {}."
                                                        "".format(
                                                            sense.get('id')))
                                            except:
                                                log.info("Removing second "
                                                    "example from {}".format(
                                                    sense.get('id')))
                                            sense.remove(example2)
                                    else:
                                        #Don't remove here
                                        log.log(3,"Language {} content "
                                                "DIFFERENT".format(lang))
                                else:
                                    if example2 in sense:
                                        try:
                                            log.info("Removing second example "
                                                    "from {}".format(
                                                            sense.get('id')))
                                        except:
                                            log.info("Removing second example "
                                                    "from {}".format(
                                                            sense.get('id')))
                                        sense.remove(example2)
                            for lang in ex2[6]:
                                if lang not in ex1[6]:
                                    if example in sense:
                                        try:
                                            log.info("Removing first example."
                                                    "from {}".format(
                                                            sense.get('id')))
                                        except:
                                            log.info("Removing first example."
                                                    "from {}".format(
                                                            sense.get('id')))
                                        sense.remove(example)
        self.write()
    def addtoneUF(self,senseid,group,analang,guid=None,showurl=False):
        urlnattr=self.geturlnattr('senseid',senseid=senseid) #give the sense.
        url=urlnattr['url']
        if showurl==True:
            log.info(url)
        node=self.nodes.find(url) #this should always find just one node
        if node is None:
            log.info(' '.join("Sorry, this didn't return a node:",guid,senseid))
            return
        t=None
        for field in node.findall('field'):
            if field.get('type') == 'tone':
                f=field.findall('form')
                f2=field.find('form')
                t=f2.find('text')
                for fs in f:
                    t2=fs.find('text')
        if t is None:
            p=ET.SubElement(node, 'field',attrib={'type':'tone'})
            f=ET.SubElement(p,'form',attrib={'lang':analang})
            t=ET.SubElement(f,'text')
        t.text=group
        self.updatemoddatetime(guid=guid,senseid=senseid)
        # self.write()
        """<field type="tone">
        <form lang="en"><text>toneinfo for sense.</text></form>
        </field>"""
    def addmediafields(self,node, url,lang, showurl=False):#lang=Check.audiolang
        """This fuction will add an XML node to the lift tree, like a new
        example field."""
        """The program should know before calling this, that there isn't
        already the relevant node --since it is agnostic of what is already
        there."""
        log.info("Adding {} value to {} location".format(url,node))
        possibles=node.findall("form[@lang='{lang}']/text".format(lang=lang))
        for possible in possibles:
            log.debug(possibles.index(possible))
            if hasattr(possible,'text'):
                if possible.text == url:
                    log.debug("This one is already here; not adding.")
                    return
        form=ET.SubElement(node,'form',attrib={'lang':lang})
        t=ET.SubElement(form,'text')
        t.text=url
        """Can't really do this without knowing what entry or sense I'm in..."""
        self.write()
    def addmodcitationfields(self,entry,langform,lang):
        citation=entry.find('citation')
        if citation is None:
            citation=ET.SubElement(entry, 'citation')
        form=citation.find("form[@lang='{lang}']".format(lang=lang))
        if form is None:
            form=ET.SubElement(citation,'form',attrib={'lang':lang})
        t=form.find('text')
        if t is None:
            t=ET.SubElement(form,'text')
        t.text=langform
    def addpronunciationfields(self,guid,senseid,analang,
                                glosslang,glosslang2,
                                lang,forms,
                                # langform,glossform,gloss2form,
                                fieldtype,
                                location,fieldvalue,ps=None,showurl=False):
        """This fuction will add an XML node to the lift tree, like a new
        pronunciation field."""
        """The program should know before calling this, that there isn't
        already the relevant node."""
        # urlnattr=attributesettings(attribute,guid,analang,glosslang,lang,ps,form,
        #                                 fieldtype,location)
        urlnattr=self.geturlnattr('guid',guid=guid) #just give me the entry.
        url=urlnattr['url']
        if showurl==True:
            log.info(url)
        node=self.nodes.find(url) #this should always find just one node
        # nodes=self.nodes.findall(url) #this is a list
        p=ET.SubElement(node, 'pronunciation')
        form=ET.SubElement(p,'form',attrib={'lang':analang})
        t=ET.SubElement(form,'text')
        t.text=langform
        field=ET.SubElement(p,'field',attrib={'type':fieldtype})
        form=ET.SubElement(field,'form',attrib={'lang':lang})
        t2=ET.SubElement(form,'text')
        t2.text=fieldvalue
        fieldgloss=ET.SubElement(p,'field',attrib={'type':'gloss'})
        form=ET.SubElement(fieldgloss,'form',attrib={'lang':glosslang})
        t3=ET.SubElement(form,'text')
        t3.text=glossform
        trait=ET.SubElement(p,'trait',attrib={'name':'location', 'value':location})
        self.updatemoddatetime(guid=guid,senseid=senseid)
        # self.write()
        """End here:""" #build up, or down?
        #node.append('pronunciation')
        """<pronunciation>
            <form lang="gnd"><text>dìve</text></form>
            <field type="tone">
                <form lang="gnd"><text>LM</text></form>
            </field>
            <trait name="location" value="Isolation"/>
        </pronunciation>
        <pronunciation>
            <form lang="gnd"><text>Languageform here</text></form>
            <field type="tone"><form lang="en"><text>HL representation</text></form></field>
            <field type="gloss"><form lang="fr"><text>Gloss here</text></form></field>
            <trait name="location" value="With Other Stuff" />
        </pronunciation>
        """
    def rmexfields(self,guid=None,senseid=None,analang=None,
                    glosslang=None,langform=None,glossform=None,fieldtype=None,
                    location=None,fieldvalue=None,ps=None,showurl=False):
        #We need fieldvalue here to be able to remove 'NA'.
        urlnattr=self.geturlnattr('senseid',senseid=senseid) #just give me the sense.
        url=urlnattr['url']
        if showurl==True:
            log.info(url)
        node=self.nodes.find(url) #this should always find just one node
        log.debug("removing LIFT fields location={},fieldtype={},fieldvalue={}"
                    "".format(location,fieldtype,fieldvalue))
        urlnattr2=self.geturlnattr('examplewfieldlocvaluefromsense',
                                    location=location,
                                    fieldtype=fieldtype,fieldvalue=fieldvalue
                                    )
        url2=urlnattr2['url']
        if showurl==True:
            log.info("url for examples: {} (n={}".format(url2,len(node.findall(
                                                                        url2))))
        for example in node.findall(url2):
            node.remove(example)
            # """<field type="tone"><form lang="fr"><text>1</text></form></field>"""
            # """<field type="location"><form lang="fr"><text>Plural</text></form></field>"""
            # for child in node:
            #     print (child.tag, child.attrib)
            # for child in example:
            #     print ('child:',child.tag, child.attrib, child.text)
            #     for grandchild in child:
            #         print ('grandchild:',grandchild.tag, grandchild.attrib, grandchild.text)
            # log.info("Continuing on to the next example node now:")
            # log.info("Continuing again to the next example node now:")
        self.updatemoddatetime(guid=guid,senseid=senseid)
        # self.write()
    def updateexfieldvalue(self,guid=None,senseid=None,analang=None,
                    glosslang=None,langform=None,glossform=None,fieldtype=None,
                    location=None,fieldvalue=None,ps=None,
                    newfieldvalue=None,showurl=False):
        """This updates the fieldvalue, based on current value. It assumes
        there is a field already there; use addexamplefields if not"""
        urlnattr=self.geturlnattr('exfieldvalue',senseid=senseid,
                                    fieldtype=fieldtype,
                                    location=location,
                                    fieldvalue=fieldvalue
        ) #just give me the sense.
        url=urlnattr['url']
        if showurl==True:
            log.info(url)
        node=self.nodes.find(url) #this should always find just one node
        # for value in node.findall(f"field[@type=location]/"
        #                             f"form[text='{location}']"
        #                                 f"[@type='{fieldtype}']/"
        #                             f"form[text='{fieldvalue}']/text"):
        #     # """<field type="tone"><form lang="fr"><text>1</text></form></field>"""
        #     # """<field type="location"><form lang="fr"><text>Plural</text></form></field>"""
        node.text=newfieldvalue #remove(example)
        self.updatemoddatetime(guid=guid,senseid=senseid)
        # self.write()
    def updatemoddatetime(self,guid=None,senseid=None,analang=None,
                    glosslang=None,langform=None,glossform=None,fieldtype=None,
                    location=None,fieldvalue=None,ps=None,
                    newfieldvalue=None,showurl=False):
        """This updates the fieldvalue, ignorant of current value."""
        urlnattr=self.geturlnattr('entry',guid=guid,senseid=senseid) #just entry
        url=urlnattr['url']
        if showurl==True:
            log.info(url)
        node=self.nodes.find(url) #this should always find just one node
        node.attrib['dateModified']=getnow()
    def read(self):
        """this parses the lift file into an entire ElementTree tree,
        for reading or writing the LIFT file."""
        self.tree=ET.parse(self.filename)
        """This returns the root node of an ElementTree tree (the entire
        tree as nodes), to edit the XML."""
        self.nodes=self.tree.getroot()
    def writegzip(self,dir=None,filename=None):
        import gzip
        if filename is None:
            filename=self.filename
        compressed=filename+'_'+getnow()+'.gz'
        if dir != None:
             compressed=os.path.join(dir,compressed)
        data=self.write()
        with open(filename,'r') as d:
            data=d.read()
            with gzip.open(compressed, "wt") as f:
                f.write(data)
                f.close()
                d.close()
        return compressed
    def writelzma(self,filename=None):
        try:
            import lzma
        except ImportError:
            from backports import lzma
        """This writes changes back to XML."""
        """When this goes into production, change this:"""
        #self.tree.write(self.filename, encoding="UTF-8")
        if filename is None:
            filename=self.filename
        compressed=filename+'_'+getnow()+'.7z'
        data=self.write()
        with open(filename,'r') as d:
            data=d.read()
            # with lzma.LZMAFile(compressed,'w') as t:
            with lzma.open(compressed, "wt") as f:
                f.write(data)
                f.close()
                # t.write(d)
                # t.close()
                d.close()
        return compressed
    def write(self,filename=None):
        """This writes changes back to XML."""
        if filename is None:
            filename=self.filename
        write=0
        replace=0
        remove=0
        xmlfns.indent(self.nodes)
        self.tree=ET.ElementTree(self.nodes)
        try:
            self.tree.write(filename+'.part', encoding="UTF-8")
            write=1
        except:
            log.error("There was a problem writing to file: {}"
                    "".format(filename))
        if write == 1:
            try:
                os.replace(filename+'.part',filename)
            except:
                log.error("There was a problem writing to file. This is what's "
                "here: {}".format(os.listdir(str(pathlib.Path(filename)+'.part')
                                                                            )))
    def analangs(self):
        log.log(1,_("Looking for analangs in lift file"))
        self.audiolangs=[]
        self.analangs=[]
        possibles=list(dict.fromkeys(self.get('lexemelang')+self.get('citation'
                                        'lang')+self.get('pronunciationlang')))
        log.info(_("Possible analysis language codes found: {}".format(possibles)))
        for glang in ['fr','en']:
            if glang in possibles:
                for form in ['citation','lexeme']:
                    gforms=self.get(form,analang=glang)
                    if 0< len(gforms):
                        log.info("LWC lang {} found in {} field: {}".format(
                            glang,form,self.get(form,analang=glang)))
                        """For Saxwe, and others who have fr or en encoding errors"""
                        if len(gforms) <= 10:
                            log.info("Only {} examples of LWC lang {} found "
                                "in {} field; is this correct?".format(
                                                len(gforms),glang,form))
                        #     possibles.remove(glang) #not anymore
        for lang in possibles:
            if 'audio' in lang:
                log.debug(_("Audio language {} found.".format(lang)))
                self.audiolangs+=[lang]
            else:
                self.analangs+=[lang]
        if self.audiolangs == []:
            log.debug(_('No audio languages found in Database; creating one '
            'for each analysis language.'))
            for self.analang in self.analangs:
                self.audiolangs+=[f'{self.analang}-Zxxx-x-audio']
        log.debug('Audio languages: {}'.format(self.audiolangs))
        log.debug('Analysis languages: {}'.format(self.analangs))
    def glosslangs(self):
        self.glosslangs=list(dict.fromkeys(self.get('glosslang')+self.get(
                                                                'defnlang')))
        log.debug(_("gloss languages found: {}".format(self.glosslangs)))
    def glossordefn(self,guid=None,senseid=None,lang='ALL',ps=None
                    ,showurl=False):
        if lang == None: #This allows for a specified None='give me nothing'
            return
        elif lang == 'ALL':
            lang=None #this is how the script gives all, irrespective of lang.
        forms=self.get('gloss',guid=guid,senseid=senseid,glosslang=lang,ps=ps,
                        showurl=showurl) #,showurl=True
        if forms == []:
            formsd=self.get('definition',guid=guid,senseid=senseid,
                        glosslang=lang,
                        showurl=showurl)
            forms=list()
            for form in formsd:
                forms.append(rx.glossifydefn(form))
        return forms
    def citationorlexeme(self,guid=None,senseid=None,lang=None,ps=None
                        ,showurl=False):
        """I think this was a nice idea, but unnecessary; ability to use guid
        or senseid is more important."""
        # if guid is None:
        #     try:
        #         for guid in self.guidsvalidwps:
        #             return self.citationorlexeme(guid=guid,senseid=senseid,
        #                                             lang=lang,ps=ps,
        #                                             showurl=showurl)
        #     except:
        #         for guid in self.guids:
        #             return self.citationorlexeme(guid=guid,senseid=senseid,
        #                                             lang=lang,ps=ps,
        #                                             showurl=showurl)
        # else:
        forms=self.get('citation',guid=guid,senseid=senseid,analang=lang,
                        showurl=showurl,
                        ps=ps
                        ) #,showurl=True
        if forms == []: #for the whole db this will not work if even one gloss is filled out
            forms=self.get('lexeme',guid=guid,senseid=senseid,analang=lang,
                            showurl=showurl,
                            ps=ps
                            )
        return forms
    def fields(self,guid=None,lang=None): #get all the field types in a given entry
        return self.get('fieldname',guid=guid,lang=lang)#nfields=0
    def getsenseids(self): #get the number entries in a lift file.
        self.senseids=self.get('senseid') #,showurl=True
        self.nsenseids=len(self.senseids) #,guid,lang,fieldtype,location
    def getguids(self): #get the number entries in a lift file.
        self.guids=self.get('guid') #,showurl=True
        self.nguids=len(self.guids) #,guid,lang,fieldtype,location
    def nc(self):
        nounclasses="1 2 3 4 5 6 7 8 9 10 11 12 13 14"
    # def nlist(self): #This variable gives lists, to iterate over.
    #     # prenasalized=['mb','mp','mbh','mv','mf','nd','ndz','ndj','nt','ndh','ng','ŋg','ŋg','nk','ngb','npk','ngy','nj','nch','ns','nz']  #(graphs that preceede a consonant)
    #     ntri=["ng'"]
    #     ndi=['mm','ny','ŋŋ']
    #     nm=['m','m','M','n','n','ŋ','ŋ','ɲ']
    #     nasals=ntri+ndi+nm
    #     actuals={}
    #     for lang in self.analangs:
    #         unsorted=self.inxyz(lang,nasals)
    #         """Make digraphs appear first, so they are matched if present"""
    #         actuals[lang]=sorted(unsorted,key=len, reverse=True)
    #     return actuals
    # def glist(self): #This variable gives lists, to iterate over.
    #     glides=['ẅ','y','Y','w','W']
    #     actuals={}
    #     for lang in self.analangs:
    #         unsorted=self.inxyz(lang,glides) #remove the symbols which are not in the data.
    #         """Make digraphs appear first, so they are matched if present"""
    #         actuals[lang]=sorted(unsorted,key=len, reverse=True)
    #     return actuals
    def clist(self): #This variable gives lists, to iterate over.
        log.log(2,"Creating CV lists from scratch")
        """These are all possible forms, that I have ever run across.
        If I find something new (or you tell me!) we can add it here.
        Forms not actually in the data get removed below."""
        """Note, objects will be found in the order listed, so put the
        larger/longer objects first, if you ever want to find them ('ts' must
        precede 't', or you will only find t+s=CC, not ts=C)"""
        """This is a dictionary of theoretically possible segment graphs,
        by category and number of glyphs, with consonant dictionaries nested
        inside it, by category."""
        c={}
        c['p']={}
        c['p'][2]=['bh','dh','kp','gh','gb','kk']
        c['p'][1]=['p','P','b','ɓ','Ɓ','B','t','d','ɗ','ɖ','c','k','g','ɡ','G']
        c['f']={}
        c['f'][2]=['ch','ph','bh','vh','sh','zh','hh']
        c['f'][1]=['j','J','F','f','v','s','z','Z','ʃ','ʒ','θ','ð','x','ɣ','h']
        c['a']={}
        c['a'][3]=['chk']
        c['a'][2]=['dj','ts','dz','tʃ','dʒ']
        c['lf']={}
        c['lf'][2]=['sl','zl','zl']
        c['lf'][1]=['ɬ','ɮ']
        c['pn']={}
        """If these appear, they should be single consonants."""
        c['pn'][2]=['ᵐb','ᵐp','ᵐv','ᵐf','ⁿd','ⁿt','ᵑg','ⁿg','ᵑg','ⁿk','ᵑk',
                    'ⁿj','ⁿs','ⁿz']
        x={} #dict to put all hypothetical segements in, by category
        x['C']=list() #to store valid consonants in
        for nglyphs in [3,2,1]:
            for stype in c:
                if c[stype].get(nglyphs) is not None:
                    x['C']+=c[stype][nglyphs]
        # s['g']={}
        # x['NC']=['mbh','ndz','ndj','ndh','ngb','npk','ngy','nch','mb','mp',
        #         'mv','mf','nd','nt','ng','ŋg','ŋg','nk','nj','ns','nz']
        x['ʔ']=['ʔ',
                "ꞌ", #Latin Small Letter Saltillo
                "'", #Tag Apostrophe
                'ʼ'  #modifier letter apostrophe
                ]
        x['G']=['ẅ','y','Y','w','W']
        # x['CG']=list((char+g for char in x['C'] for g in x['G']))
        x['N']=["ng'",'mm','ny','ŋŋ','m','M','n','ŋ','ɲ']
        # x['NC']=list((n+char for char in x['C'] for n in x['N']))
        # x['NCG']=list((n+char+g for char in x['C'] for n in x['N']
        #                                             for g in x['G']))
        """Non-Nasal/Glide Sonorants"""
        x['S']=['rh','wh','l','r']
        # x['CS']=list((char+s for char in x['C'] for s in x['S']))
        # x['NCS']=list((n+char+s for char in x['C'] for n in x['N']
        #                                             for s in x['S']))
        # self.treatlabializepalatalizedasC=False
        # if self.treatlabializepalatalizedasC==True:
        #     lp={}
        #     lp['lab']=list(char+'w' for char in c)
        #     lp['pal']=list(char+'y' for char in c)
        #     lp['labpal']=list(char+'y' for char in lp['lab'])
        #     lp['labpal']+=list(char+'w' for char in lp['pal'])
        #     for stype in sorted(lp.keys()): #larger graphs first
        #         c=lp[stype]+c
        x['V']=[
                #decomposed first:
                #tilde (decomposed):
                'ã', 'ẽ', 'ɛ̃', 'ə̃', 'ɪ̃', 'ĩ', 'õ', 'ɔ̃', 'ũ', 'ʊ̃',
                #Combining Greek Perispomeni (decomposed):
                'a͂', 'i͂', 'o͂', 'u͂',
                #single code point vowels:
                'a', 'e', 'i', 'ə', 'o', 'u',
                'A', 'E', 'I', 'Ə', 'O', 'U',
                'ɑ', 'ɛ', 'ɨ', 'ɔ', 'ʉ',
                'æ', 'ʌ', 'ɪ', 'ï', 'ö', 'ʊ',
                #for those using precomposed letters:
                'à', 'è', 'ì', 'ò', 'ù',
                'À', 'È', 'Ì', 'Ò', 'Ù',
                'á', 'é', 'í', 'ó', 'ú',
                'Á', 'É', 'Í', 'Ó', 'Ú',
                'â', 'ê', 'î', 'ô', 'û',
                'Â', 'Ê', 'Î', 'Ô', 'Û'
                ]
        x['d']=["̀","́","̂","̌","̄","̃"] #"à","á","â","ǎ","ā","ã"[=́̀̌̂̃ #vowel diacritics
        x['ː']=[":","ː"] # vowel length markers
        x['b']=['=','-'] #affix boundary markers
        x['o']=['<','&lt;','&gt;','>','›','»','‹','«',''] #macron here?
        # """We need to address long and idiosyncratic vowel orthographies,
        # especially for Cameroon. This should also include diacritics, together
        # or separately."""
        # """At some point, we may want logic to include only certain
        # elements in c. The first row is in pretty much any language."""
        actuals={}
        log.log(3,'hypotheticals: {}'.format(x))
        self.s={} #wipe out an existing dictionary
        for lang in self.analangs:
            if lang not in self.s:
                self.s[lang]={}
            for stype in x:
                self.s[lang][stype]=rx.inxyz(self,lang,x[stype])
                log.log(3,'hypotheticals[{}][{}]: {}'.format(lang,stype,
                                                    str(x[stype])))
                log.log(3,'actuals[{}][{}]: {}'.format(lang,stype,
                                                str(self.s[lang][stype])))
    def slists(self):
        self.segmentsnotinregexes={}
        self.clist()
    # def segmentin(self, lang, glyph):
    #     """This actually allows for dygraphs, etc., so I'm keeping it."""
    #     """check each form and lexeme in the lift file (not all files
    #     use both)."""
    #     for form in self.citationforms[lang] + self.lexemes[lang]:
    #         if re.search(glyph,form): #see if the glyph is there
    #             return glyph #find it and stop looking, or return nothing
    # def inxyz(self, lang, segmentlist): #This calls the above script for each character.
    #     actuals=list()
    #     for i in segmentlist:
    #         s=self.segmentin(lang,i)
    #         #log.info(s) #to see the following run per segment
    #         if s is not None:
    #             actuals.append(s)
    #     return list(dict.fromkeys(actuals))
    def getguidformstosearchbyps(self,ps,lang=None):
        if lang is None:
            lang=self.analang
        self.guidformstosearch[lang][ps]={} #Erases all previous data!!
        for guid in self.get('guidbyps',lang=lang,ps=ps):
            form=self.get('citation',guid=guid,lang=lang,ps=ps)
            if len(form) == 0: #no items returned
                form=self.get('lexeme',guid=guid,lang=lang,ps=ps)
            self.guidformstosearch[lang][ps][guid]=form
    def getsenseidformstosearchbyps(self,ps,lang=None):
        if lang is None:
            lang=self.analang
        self.senseidformstosearch[lang][ps]={} #Erases all previous data!!
        for senseid in self.get('senseidbyps',lang=lang,ps=ps):
            form=self.get('citation',senseid=senseid,lang=lang,ps=ps)
            if len(form) == 0: #no items returned
                form=self.get('lexeme',senseid=senseid,lang=lang,ps=ps)
            self.senseidformstosearch[lang][ps][senseid]=form
    def getguidformstosearch(self):
        # import time
        """This outputs a dictionary of form {analang: {guid:form}*}*, where
        form is citation if available, or else lexeme. This is to be flexible
        for entries in process of analysis, and to have a dictionary to check
        with regexes for output."""
        self.guidformstosearch={}
        self.senseidformstosearch={}
        for lang in self.analangs:
            self.guidformstosearch[lang]={} #This will erase all previous data!!
            self.senseidformstosearch[lang]={}
            for ps in self.pss: #I need to break this up.
                # start_time=time.time()
                self.getguidformstosearchbyps(ps,lang=lang)
                self.getsenseidformstosearchbyps(ps,lang=lang)
                #"n",str(time.time() - start_time),"seconds.")
        #log.info(self.guidformstosearch)
    def getformstosearchbyps(self,ps,lang=None):
        if lang is None:
            lang=self.analang
        self.formstosearch[lang][ps]={} #Erases all previous data!!
        #for guid in self.get('guidbynofield',lang=lang,ps=ps):
        # forms=self.citationorlexeme(lang=lang,ps=ps)
        """This actually needs this logic here, since formstosearch hasn't
        been made yet."""
        forms=self.get('citation',analang=lang,ps=ps)
        # if len(forms) == 0: #no items returned, I should probably combine
                            #this at some point, list(dict.fromkeys(form1+form2))
        forms+=self.get('lexeme',analang=lang,ps=ps)
        # forms1=self.get('citation',lang=lang,ps=ps)
        # forms2=self.get('lexeme',lang=lang,ps=ps)
        # forms=list(dict.fromkeys(forms1+forms2))
        self.formstosearch[lang][ps]=forms
    def getformstosearch(self):
        # import time
        """This outputs a dictionary of form {analang: {guid:form}*}*, where
        form is citation if available, or else lexeme. This is to be flexible
        for entries in process of analysis, and to have a dictionary to check
        with regexes for output."""
        self.formstosearch={}
        for lang in self.analangs:
            self.formstosearch[lang]={} #This will erase all previous data!!
            for ps in self.pss+[None]: #I need to break this up.
                # start_time=time.time()
                self.getformstosearchbyps(ps,lang=lang)
                #"n",str(time.time() - start_time),"seconds.")
        # log.info(self.formstosearch)
    def citationforms(self): #outputs generator object with each form in LIFT file.
        """This produces a dictionary, of forms for each language."""
        #return self.get('citationform')
        output={}
        for lang in self.analangs:
            output[lang]=self.get('citation',analang=lang)
            #output[lang]=list()
            #for form in self.nodes.findall(f"entry/citation/form[@lang='{lang}']/text"):
            #    output[lang]+=[form.text] #print the text of the <text> node above
        #log.info(output.keys()) #to see which languages are found
        return output
    def lexemes(self):
        output={}
        for lang in self.analangs:
            output[lang]=self.get('lexeme',analang=lang) #list()
            #for form in self.nodes.findall(f"entry/lexical-unit/form[@lang='{lang}']/text"):
            #    output[lang]+=[form.text] #print the text of the <text> node above
        #log.info(output.keys()) #to see which languages are found
        return output
    def extrasegments(self):
        # start_time=time.time() #this enables boot time evaluation
        for lang in self.analangs:
            self.segmentsnotinregexes[lang]=list()
            extras=list()
            """This is not a particularly sophisticated test. I should be
            also looking for consonant glyphs that occur between vowels,
            and vice versa. Later."""
            # nonwordforming=re.compile('[() \[\]\|,\-!@#$*?]')
            invalid=['(',')',' ','[',']','|',',','-','!','@','#','$','*','?'
                        ,'\n']
            for form in [x for x in self.citationforms[lang]+self.lexemes[lang]
                            if x != None]:
                for x in form:
                    if ((x not in invalid) and
                            (x not in [item for sublist in self.s[lang].values()
                                for item in sublist])):
                        self.segmentsnotinregexes[lang].append(x)
                        log.debug('Missing {} from {} {}'.format(x,lang,form))
            if len(self.segmentsnotinregexes[lang]) > 0:
                log.info("The following segments are not in your {} "
                "regex's: {}".format(lang,
                list(dict.fromkeys(self.segmentsnotinregexes[lang]).keys())))
            else:
                print("No problems!")
                log.info(_("Your regular expressions look OK for {} (there are "
                    "no segments in your {} data that are not in a regex). "
                    "".format(lang,lang)))
                log.info("Note, this doesn't say anything about digraphs or "
                    "complex segments which should be counted as a single "
                    "segment.")
                log.info("--those may not be covered by your regexes.")
                print("No problems!")

        # log.log(2,"{} (lift.extrasegments run time): {}".format(
        #         time.time()-start_time,self.segmentsnotinregexes))
    def pss(self): #get all POS values in the LIFT file
        return list(dict.fromkeys(self.get('ps')))
        #pss=list()
        #for ps in self.nodes.findall(f"entry/sense/grammatical-info"):
        #    thisps=ps.attrib.get('value')
        #    if thisps not in pss and thisps is not None:
        #        pss.append(thisps)
        #return pss #return the list
        """CONTINUE HERE: Making things work for the new lift.get() paradigm."""
    def formsbyps(self,ps): #self is LIFT! #should be entriesbyps
        """This function just pulls all entries of a particular
        grammatical category"""
        """This function, and others like it, should pull from the profiles
        data variable, which should be redesigned so it can recompile
        quickly for changes in form."""
        output=[]
        winfoentries=[]
        x=0
        y=0
        z=0
        zz=0
        if ps is None:
            entries=self.nodes.findall(f"entry")
            #gi1=self.nodes.findall(f".//grammatical-info")
            #log.info(' '.join('Entries found:',len(entries)))#for gi in entry.find(f"grammatical-info"):
            #log.info(' '.join('Ps found:',len(gi1)))#for gi in entry.find(f"grammatical-info"):
            for entry in entries:
                gi=entry.find(f".//grammatical-info") #.get('value')
                #if gi is not None and len(gi)>1:
                #    log.info(gi)
                #    log.info(' '.join(x,y,z,zz))
                #    exit()
                #    x+=1
                if gi is None: #entry.find(f".//grammatical-info") is None:
                #    y+=1
                    output+=[entry] #add this item to a list, not it's elements
                #elif gi is not None: #entry.find(f".//grammatical-info") is not None:
                #    z+=1
                #    log.info(type(gi))
                #    log.info(gi.get('value'))
                #    log.info(len(gi))
                #    winfoentries+=[entry]
                #else:
                #    zz+=1
                #    log.info("Huh?")
        else:
            #log.info(ps)
            # for self.db.get('')
            for entry in self.nodes.findall(f"entry/sense/grammatical-info[@value='{ps}']/../.."):
                #log.info('Skipping this for now...')
                output+=[entry] #add this item to a list, not it's elements
        #log.info(' '.join('Entries without ps:',len(output)))
        #log.info(' '.join('Entries with ps:',len(winfoentries)))
        #log.info(' '.join('Total entries found (Should be 2468):',len(output)+len(winfoentries)))
        #log.info(' '.join('multiple:',x,'no ps:',y,'wps',z,'totalps:',y+z,'huh:',zz))
        #exit()
        return output #list of entry nodes
    def guidformsbyregex(self,regex,ps=None,analang=None): #self is LIFT!
        # from multiprocessing.dummy import Pool as ThreadPool
        """This function takes in a ps and compiled regex,
        and outputs a dictionary of {guid:form} form."""
        if analang is None:
            analang=self.analang
        #log.info(regex)
        output={}
        def checkformsbyps(self,analang,ps):
            for form in self.formstosearch[analang][ps]:
                if regex.search(form): #re.search(regex,form): #,showurl=True
                    for guid in self.get('guidbylexeme',form=form,ps=ps):
                        output[guid]=form
            return output
        if ps == 'All': #When I'm looking through each ps, not ps=None (e.g., invalid).
            for ps in self.pss+[None]:
                output.update(checkformsbyps(self,analang,ps)) #adds dict entries
            return output
        else:
            output.update(checkformsbyps(self,analang,ps))
            return output
        for entry in entries:
            def debug():
                log.info(len(entry))
                log.info(str(entry.tag))
                log.info(str(entry.get('guid')))
                log.info(entry.attrib) #('value'))
                log.info(str(entry.find('lexical-unit')))
                log.info(str(entry.find('citation')))
                log.info(str(entry.find('form')))
                log.info(self.get('lexeme',guid=entry.get('guid')))
                log.info(self.get('lexeme',guid=entry.get('guid'))[0])
                exit()
            #debug()
            """FIX THIS!!!"""
            form=self.get('lexeme',guid=entry.get('guid')) #self.formbyid(entry.get('guid'))[0] #just looking for one at this point.
            log.info("Apparently there are no/multiple forms for this entry...")
        return output
    def senseidformsbyregex(self,regex,analang,ps=None): #self is LIFT!
        """This function takes in a ps and compiled regex,
        and outputs a dictionary of {senseid:form} form."""
        # if analang is None:
        #     analang=self.analang
        output={}
        def checkformsbyps(self,analang,ps):
            for form in self.formstosearch[analang][ps]:
                if regex.search(form): #re.search(regex,form): #,showurl=True
                    for senseid in self.get('senseidbylexeme',form=form,ps=ps):
                        output[senseid]=form
            return output
        if ps == 'All': #When I'm looking through each ps, not ps=None (e.g., invalid).
            for ps in self.pss+[None]:
                output.update(checkformsbyps(self,analang,ps)) #adds dict entries
            return output
        else:
            output.update(checkformsbyps(self,analang,ps))
            return output
        for entry in entries:
            def debug():
                log.info(len(entry))
                log.info(str(entry.tag))
                log.info(str(entry.get('guid')))
                log.info(entry.attrib) #('value'))
                log.info(str(entry.find('lexical-unit')))
                log.info(str(entry.find('citation')))
                log.info(str(entry.find('form')))
                log.info(self.get('lexeme',guid=entry.get('guid')))
                log.info(self.get('lexeme',guid=entry.get('guid'))[0])
                exit()
            #debug()
            """FIX THIS!!!"""
            form=self.get('lexeme',guid=entry.get('guid')) #self.formbyid(entry.get('guid'))[0] #just looking for one at this point.
            log.info("Apparently there are no/multiple forms for this entry...")
        return output
    def formbyid(self,guid,lang=None): #This is the language version, use without entry.
        """bring this logic into get()"""
        form=self.get('citation',guid=guid,lang=lang) #self.nodes.findall(f"entry[@guid='{guid}']/citation/form[@lang='{self.xyz}']/text")
        if form == []: #default to lexical form for missing citation forms.
            form=self.get('lexeme',guid=guid,lang=lang) #form=self.nodes.findall(f"entry[@guid='{guid}']/lexical-unit/form[@lang='{self.xyz}']/text")
            if form == []:
                return None
        #log.info(form)
        return form #[0].text #print the text of the <text> node above
    def psbyid(self,guid): #This is the language version, use without entry.
        #return self.nodes.find(f"entry[@guid='{guid}']/sense/grammatical-info").get('value')
        #return ps.attrib.get('value')
        ps=self.nodes.find(f"entry[@guid='{guid}']/sense/grammatical-info")
        if ps is not None:
            return ps.attrib.get('value')
    def formsnids(self): #outputs [guid, form] tuples for each entry in the lexicon. Is this more efficient than using idsbyformregex?
        for entry in self.nodes.findall(f"entry"):
            for form in entry.findall(f"./citation/form[@lang='{self.xyz}']/text"): #Not lexeme-unit..…
                yield entry.get('guid'), form.text #print the text of the <text> node above
                #figure out how to filter this by part of speech
    def idsbylexemeregex(self,regex): #outputs [guid, ps, form] tuples for each entry in the LIFT file lexeme which matches the regex.
        for ps in pss(): #for each POS
            for entry in self.nodes.findall(f"entry/sense/grammatical-info[@value='{ps}']/../.."): #for each entry
                for form in entry.findall(f"./lexical-unit/form[@lang='{self.xyz}']/text"): #for each CITATION form this needs to see lexeme forms, too..…
                #for form in entry.findall(f"./citation/form[@lang='{xyz}']/text"): #for each CITATION form this needs to see lexeme forms, too..…
                    # if re.search(regex,form.text): #check if the form matches the regex
                    if regex.search(form.text): #check if the form matches the regex
                        yield entry.get('guid'), ps, form.text #print the tuple (may want to augment this some day to include other things)
    def idsbylexemeregexnps(self,ps,regex): #outputs [guid, ps, form] tuples for each entry in the LIFT file lexeme which matches the regex and ps.
        """This puts out a dictionary with guid keys and (ps,form) tuples
        for values. I need to rework this. I think not use it anymore..."""
        output={}
        for form in self.formstosearch[self.analang][ps]:
            # form=self.formstosearch[self.analang][ps][guid]
            # log.info(form)
            if regex.search(form):
            # if len(form) == 1 and regex.search(form):
                output[guid]=form
        return output
            #exit()

        for entry in self.nodes.findall(f"entry/sense/grammatical-info[@value='{ps}']/../../lexical-unit/form[@lang='{self.analang}']/../.."):
            form=entry.find(f"lexical-unit/form[@lang='{self.analang}']/text")
            if regex.search(form.text): #re.search(regex,form.text):
                output[entry.get('guid')]=(ps, form.text)
        return output
    def wordcountbyps(self,ps):
        count=0
        if ps is None:
            #entries=
            #gi1=self.nodes.findall(f".//grammatical-info")
            #log.info(' '.join('Entries found:',len(entries)))#for gi in entry.find(f"grammatical-info"):
            #log.info(' '.join('Ps found:',len(gi1)))#for gi in entry.find(f"grammatical-info"):
            for entry in self.nodes.findall(f"entry"):
                #gi= #.get('value')
                if entry.find(f".//grammatical-info") is None: #entry.find(f".//grammatical-info") is None:
                #    y+=1
                    count+=1
        else:
            for entry in self.nodes.findall(f"entry/sense/grammatical-info[@value='{ps}']/../.."): #for each entry
                count+=1
        return count
    def formsregex(self,regex): #UNUSED? outputs [guid, form] tuples where the form matches a regex. This might make sense for a tuple with lexeme-unit, citation, and plural.
        for entry in formsnids():
            if regex.search(entry[1]): #check regex against the form part of the tuple output by formsnids
                yield entry[0] #print id part of the tuple output by formsnids
class Entry(object): # what does "object do here?"
    #import lift.put as put #class put:
    #import get #class put:
    def __init__(self, db, guid=None, *args, **kwargs):
        if guid is None:
            log.info("Sorry, I was kidding about that; I really do need the entry's guid.")
            exit()
        #self.language=globalvariables.xyz #Do I want this here? It doesn't really add anything.. How can I check internal language? If there are more writing systems, do I want to find them?
        #self.ps=lift_get.ps(self.guid) #do this is lift_get Entry class, inherit from there.
        self.guid=guid
        self.db=db #Do I want this?
        """Probably should rework this... How to get entry fields?"""
        # self.nodes=self.db.nodes.find(f"entry[@guid='{self.guid}']") #get.nodes(self)
        #log.info(self.nodes.get('guid'))
        #probably should trim all of these..…
        """These depend on check analysis, should move..."""
        self.analang=self.db.analangs[0]
        self.glosslang=self.db.glosslangs[0]
        self.glosslang2=self.db.glosslangs[1]
        """get(self,attribute,guid=None,analang=None,glosslang=None,lang=None,
        ps=None,form=None,fieldtype=None,location=None,showurl=False)"""
        # self.lexeme=db.get('lexeme',guid=guid) #don't use this!
        self.citation=db.citationorlexeme(guid=guid,lang=self.analang)
        self.gloss=db.glossordefn(guid=guid,lang=self.glosslang)
        self.gloss2=db.glossordefn(guid=guid,lang=self.glosslang2)
        # self.citation=get.citation(self,self.analang)
        # self.gloss=get.obentrydefn(self, self.db.glosslang) #entry.get.gloss(self, self.db.glosslang, guid)
        # self.gloss2=get.gloss(self, self.db.glosslang2, guid)
        # self.plural=db.get('plural',guid=guid)
        # log.info("Looking for pronunciation field locations...")
        self.tone={}
        for location in self.db.get('pronunciationfieldlocation',guid=guid,
            fieldtype='tone'):
            # log.info(' '.join('Found:', location))
            self.tone[location]=db.get('pronunciationfieldvalue',guid=guid,location=location,fieldtype='tone')
        """These depend on check analysis, should move..."""
        #self.plural=db.get('fieldvalue',guid=guid,lang=self.analang,fieldtype=db.pluralname)
        #self.imperative=db.get('fieldvalue',guid=guid,lang=self.analang,fieldtype=db.imperativename)
        # self.imperative=db.get('imperative',guid=guid)
        self.ps=db.get('ps',guid=guid)
        self.illustration=db.get('illustration',guid=guid)
class Language(object):
    def __init__(self, xyz):
        """define consonants and vowels here?regex's belong where?"""
        self.tree=ET.parse(lift.languages[xyz]) #this parses the lift file into an entire ElementTree tree, for reading or writing the LIFT file.
        #self.object=Tree(filename)
        self.nodes=self.tree.getroot() #.parsed #This returns the root node of an ElementTree tree (the entire tree as nodes), to edit the XML.
        #self.tree=ET.parse(lift)
        #self.parsed=self.tree.getroot()
        self.code=xyz
class Unused():
    def removedups(x): #This removes duplicates from a list
        return list(dict.fromkeys(x))
"""Functions I'm using, but not in a class"""
def atleastoneexamplehaslangformmissing(examples,lang):
    for example in examples:
        if examplehaslangform(example,lang) == False:
            return True
    return False
def examplehaslangform(example,lang):
    if example.find("form[@lang='{}']".format(lang)):
        log.debug("langform found!")
        return True
    log.debug("No langform found!")
    return False
def buildurl(url):
    log.log(2,'BaseURL: {}'.format(url[0]))
    log.log(2,'Arguments: {}'.format(url[1]))
    return url[0].format(**url[1]) #unpack the dictionary
def removenone(url):
    """Remove any attribute reference whose value is 'None'. I only use
    '@name="location"' when using @value, so also remove it if @value=None."""
    nonattr=re.compile('(\[@name=\'location\'\])*\[[^\[]+None[^\[]+\]')
    newurl=nonattr.sub('',url)
    return newurl
def getnow():
    return datetime.datetime.utcnow().isoformat()[:-7]+'Z'

if __name__ == '__main__':
    import time #for testing; remove in production
    # def _(x):
    #     return str(x)
    """To Test:"""
    loglevel=5
    from logsetup import *
    log=logsetup(loglevel)
    filename="/home/kentr/Assignment/Tools/WeSay/dkx/MazHidi_Lift.lift"
    filename="/home/kentr/Assignment/Tools/WeSay/gnd/gnd.lift.bak.txt"
    filename="/home/kentr/Assignment/Tools/WeSay/bfj/bfj.lift"
    filename="/home/kentr/Assignment/Tools/WeSay/gnd/gnd.lift"
    lift=Lift(filename,nsyls=2)
    senseid='26532c2e-fedf-4111-85d2-75b34ed31dd8'
    lift.modverificationnode(senseid,add="another value3",rm="Added value")
    lift.modverificationnode(senseid,rm="another value3",add="another value2")
    lift.modverificationnode(senseid,rm="another value3",add="another value4")
    """Functions to run on a database from time to time"""
    # lift.findduplicateforms()
    # lift.findduplicateexamples()
    # lift.convertalltodecomposed()
    """Careful with this!"""
    # lift.write()
    exit()
