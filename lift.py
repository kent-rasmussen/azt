#!/usr/bin/env python3
# coding=UTF-8
"""This module controls manipulation of LIFT files and objects"""
""""(Lexical Interchange FormaT), both for reading and writing"""
from xml.etree import ElementTree as ET
import sys
import pathlib
import threading
import shutil
import datetime
import re
import logging
log = logging.getLogger(__name__)
"""This returns the root node of an ElementTree tree (the entire tree as
nodes), to edit the XML."""
class TreeParsed(object):
    def __init__(self, lift):
        self=Tree(lift).parsed
        log.info(self.glosslang)
        Tree.__init__(self, db, guid=guid)
        #self.lift=lift
"""This function defines where to find each node in the xml {url}, and what
needs to be done {formfn} to transform it into the info we need."""
"""Add entry methods that use these same urls, with sub(entry/,'')."""
"""Think through an option for adding pronunciation or not. (autobuild?)"""
"""Make all urls fully specified for guid, lang, etc; they will come out if
not used."""
def attributesettings(
    attribute, guid=None, senseid=None, analang=None, glosslang=None,
    lang=None, ps=None, form=None, fieldtype=None,
    location=None, fieldvalue=None
    ):
    """There is a bit of an issue for language attributes.
    The field <form> can exist multiple fields, so pay attention to
    the difference between
        form='{analang}'   (always in the language to be analyzed:
                                                        lexeme, citation)
        form='{glosslang}' (always in a gloss/expat language:
                                                        gloss, definition)
        form='{lang}'      (either: field --under entry, sense, or
                                                            pronunciation)
    Controlling this difference allows for things like getting an entry with a
    form in a particular language, and a gloss in a particular (other) language,
    and/or a tone description (<field>) in a particular (yet another) language.
    For now, I'm just going to assume people write meta descriptions in their
    primary gloss language."""
    #log.info(ps)
    def script():
        pass
    attributes={
        'entry': {
            'cm': 'use to get entries with a given guid or senseid',
            'url':(f"entry[@guid='{guid}']"
                    #f"/lexical-unit/form[@lang='{analang}']/../.."
                    f"/sense[@id='{senseid}']/.."
                    ),
            'attr':'node'},
        'example': {
            'cm': 'use to get examples with a given guid or senseid',
            'url':(f"entry[@guid='{guid}']"
                    f"/sense[@id='{senseid}']"
                    f"/example"
                    ),
            'attr':'node'},
        'guidbyps': {
            'cm': 'use to get guids of entries with a given ps',
            'url':(f"entry[@guid='{guid}']"
                    #f"/lexical-unit/form[@lang='{analang}']/../.."
                    f"/sense[@id='{senseid}']/grammatical-info[@value='{ps}']/../.."
                    ),
            'attr':'guid'},
        'senseidbyps': {
            'cm': 'use to get ids of senses with a given ps',
            'url':(f"entry"
                    #f"/lexical-unit/form[@lang='{analang}']/../.."
                    f"/sense[@id='{senseid}']"
                    f"/grammatical-info[@value='{ps}']/.."
                    ),
            'attr':'id'},
        'guidwanyps': {
            'cm': 'use to get guids of entries with any ps',
            'url':(f"entry[@guid='{guid}']"
                    f"/lexical-unit/form[@lang='{analang}']/../.."
                    f"/sense[@id='{senseid}']/grammatical-info[@value]/../.."
                    #f"/pronunciation"
                    #f"/trait[@name='location'][@value='{location}']/.."
                    #f"/form[@lang='{lang}']/.."
                    #f"/field[@type='{fieldtype}']"
                    #f"/form[@lang='{lang}']/../../.."
                    ),
            'attr':'guid'},
        'senseidwanyps': {
            'cm': 'use to get ids of senses with any ps',
            'url':(f"entry[@guid='{guid}']"
                    f"/lexical-unit/form[@lang='{analang}']/../.."
                    f"/sense[@id='{senseid}']/grammatical-info[@value]/.."
                    #f"/pronunciation"
                    #f"/trait[@name='location'][@value='{location}']/.."
                    #f"/form[@lang='{lang}']/.."
                    #f"/field[@type='{fieldtype}']"
                    #f"/form[@lang='{lang}']/../../.."
                    ),
            'attr':'id'},
        'guidbypronfield': {
            'cm': 'use to get guids of entries with fields at the '
                    'pronunciation level',
            'url':(f"entry[@guid='{guid}']"
                    f"/lexical-unit/form[@lang='{analang}']/../.."
                    f"/sense[@id='{senseid}']/grammatical-info[@value='{ps}']/../.."
                    f"/pronunciation"
                    f"/trait[@name='location'][@value='{location}']/.."
                    f"/form[@lang='{analang}']/.."
                    f"/field[@type='{fieldtype}']"
                    f"/form[@lang='{lang}']/../../.." #lang could be any
                    ),
            'attr':'guid'},
        'guidbypronfieldvalue': {
            'cm': 'use to get guids of entries with fields at the '
                    'pronunciation level',
            'url':(f"entry[@guid='{guid}']"
                    f"/lexical-unit/form[@lang='{analang}']/../.."
                    f"/sense[@id='{senseid}']/grammatical-info[@value='{ps}']/../.."
                    f"/pronunciation"
                    f"/trait[@name='location'][@value='{location}']/.."
                    f"/form[@lang='{analang}']/.."
                    f"/field[@type='{fieldtype}']"
                    f"/form[@lang='{lang}'][text='{fieldvalue}']/../../.." #lang could be any
                    ),
            'attr':'guid'},
        'senseidbyexfieldvalue': {
            'cm': 'use to get guids of entries with fields at the '
                    'example level',
            'url':(f"entry[@guid='{guid}']"
                    f"/lexical-unit/form[@lang='{analang}']/../.."
                    f"/sense[@id='{senseid}']"
                        f"/grammatical-info[@value='{ps}']/.."
                        f"/example"
                        f"/field[@type='location']"
                        f"/form[@lang='{glosslang}'][text='{location}']/../.."
                        f"/field[@type='{fieldtype}']"
                        f"/form[@lang='{glosslang}'][text='{fieldvalue}']/../../.."
                    ),
            'attr':'id'},
        'guidbyexfieldvalue': {
            'cm': 'use to get guids of entries with fields at the '
                    'example level',
            'url':(f"entry[@guid='{guid}']"
                    f"/lexical-unit/form[@lang='{analang}']/../.."
                    f"/sense"
                        f"/grammatical-info[@value='{ps}']/.."
                        f"/example"
                        f"/field[@type='location']"
                        f"/form[@lang='{glosslang}'][text='{location}']/../.."
                        f"/field[@type='{fieldtype}']"
                        f"/form[@lang='{glosslang}'][text='{fieldvalue}']/../../../.."
                    ),
            'attr':'guid'},
        'guidbysensefield': {
            'cm': 'use to get guids of entries with fields at the sense level',
            'url':(f"entry[@guid='{guid}']"
                    f"/lexical-unit/form[@lang='{analang}']/../.."
                    f"/sense"
                    f"/grammatical-info[@value='{ps}']/.."
                    f"/field[@type='{fieldtype}']/../.."
                    ),
            'attr':'guid'},
        'guidbyentryfield': {
            'cm': 'use to get guids of entries with fields at the entry level',
            'url':(f"entry[@guid='{guid}']"
                    f"/lexical-unit/form[@lang='{analang}']/../.."
                    f"/sense[@id='{senseid}']/grammatical-info[@value='{ps}']/../.."
                    f"/field[@type='{fieldtype}']/.."
                    ),
            'attr':'guid'},
        'guidbylang': {
            'cm': 'use to get guids of all entries with lexeme of a given lang'
                    '(or not)',
            'url':(f"entry[@guid='{guid}']"
                    f"/lexical-unit/form[@lang='{analang}']/../.."),
            'attr':'guid'},
        'guidbysenseid': {
            'cm': 'use to get guids of sense with particular id',
            'url':(f"entry[@guid='{guid}']"
                    f"/sense[@id='{senseid}']/.."
                    #f"/lexical-unit/form[@lang='{lang}']/../.."
                    ),
            'attr':'guid'},
        'guid': {
            'cm': 'use to get guids of all entries (no qualifications)',
            'url':(f"entry[@guid='{guid}']"
                    #f"/lexical-unit/form[@lang='{lang}']/../.."
                    ),
            'attr':'guid'},
        'senseid': {
            'cm': 'use to get ids of all senses (no qualifications)',
            'url':(f"entry"
                    f"/sense[@id='{senseid}']"
                    #f"/lexical-unit/form[@lang='{lang}']/../.."
                    ),
            'attr':'id'},
        'senseidbytoneUFgroup': {
            'cm': 'use to get ids of all senses by tone group',
            'url':(f"entry"
                    f"/sense[@id='{senseid}']"
                    f"/field[@type='{fieldtype}']"
                    f"/form[@lang='{lang}'][text='{form}']/../.."
                    ),
            'attr':'id'},
        'guidbylexeme': {
            'cm': 'use to get guid by ps and lexeme '
                    'in the specified language (no reference to fields)',
            'url':(f"entry[@guid='{guid}']"
                    f"/sense[@id='{senseid}']/grammatical-info[@value='{ps}']/../.."
                    f"/lexical-unit/form[@lang='{analang}'][text='{form}']"
                    f"/../.."), # ^ [.=’text'] not until python 3.7
            'attr':'guid'},
        'guidbysense': {
            'cm': 'use to get guid by ps and citation form '
                    'in the specified language (no reference to fields)',
            'url':f"entry[@guid='{guid}']"
                    f"/sense[@id='{senseid}']/..",
            'attr':'guid'},
        'senseidbylexeme': {
            'cm': 'use to get senseid by ps and lexeme '
                    'in the specified language (no reference to fields)',
            'url':(f"entry[@guid='{guid}']"
                f"/lexical-unit/form[@lang='{analang}'][text='{form}']/../.."
                f"/sense[@id='{senseid}']/grammatical-info[@value='{ps}']/.."
                    ),
            'attr':'id'},
        'guidbycitation': {
            'cm': 'use to get guid by ps and citation form '
                    'in the specified language (no reference to fields)',
            'url':f"entry[@guid='{guid}']"
                    f"/sense[@id='{senseid}']/grammatical-info[@value='{ps}']/../.."
                    f"/citation/form[@lang=guid'{analang}'][text='{form}']"
                    f"/../..", # ^ [].=’text'] not until python 3.7
            'attr':'guid'},
        'toneUFfieldvalue': {
            'cm': 'use to get tone UF values of all senses within the '
                    'constraints specified.',
            'url':(f"entry[@guid='{guid}']"
                    f"/sense[@id='{senseid}']/grammatical-info[@value='{ps}']/.."
                    f"/field[@type='{fieldtype}']"
                    f"/form[@lang='{lang}']/text"),
            'attr':'nodetext'},
        'lexemenode': {
            'cm': 'use to get lexemes of all entries with a form '
                    'in the specified language (no reference to fields)',
            'url':(f"entry[@guid='{guid}']"
                    f"/sense[@id='{senseid}']/grammatical-info[@value='{ps}']/../.."
                    f"/lexical-unit/form[@lang='{analang}']/.."),
            'attr':'node'},
        'lexeme': {
            'cm': 'use to get lexemes of all entries with a form '
                    'in the specified language (no reference to fields)',
            'url':(f"entry[@guid='{guid}']"
                    f"/sense[@id='{senseid}']/grammatical-info[@value='{ps}']/../.."
                    f"/lexical-unit/form[@lang='{analang}']/text"),
            'attr':'nodetext'},
        'citationnode': {
            'cm': 'use to get citation forms of one or all entries with a form '
                    'in the specified language (no reference to fields)',
            'url':f"entry[@guid='{guid}']"
                    f"/sense[@id='{senseid}']/grammatical-info[@value='{ps}']/../.."
                    f"/citation/form[@lang='{analang}']/..",
            'attr':'node'},
        'citation': {
            'cm': 'use to get citation forms of one or all entries with a form '
                    'in the specified language (no reference to fields)',
            'url':f"entry[@guid='{guid}']"
                    f"/sense[@id='{senseid}']/grammatical-info[@value='{ps}']/../.."
                    f"/citation/form[@lang='{analang}']/text",
            'attr':'nodetext'},
        'definition': {
            'cm': 'use to get glosses of entries',
            'url':(f"entry[@guid='{guid}']"
                    f"/sense[@id='{senseid}']"
                    f"/grammatical-info[@value='{ps}']/.."
                    f"/definition"
                    f"/form[@lang='{glosslang}']/text"
                    #f"/sense"
                    ),
            'attr':'nodetext'},
        'gloss': {
            'cm': 'use to get glosses of entries',
            'url':(f"entry[@guid='{guid}']"
                    f"/sense[@id='{senseid}']"
                    f"/grammatical-info[@value='{ps}']/.."
                    # f"/sense"
                    f"/gloss[@lang='{glosslang}']/text"
                    ),
            'attr':'nodetext'},
        'fieldnode': {
            'cm': 'use to get whole field nodes (to modify)',
            'url':f"entry[@guid='{guid}']"
                    f"/sense[@id='{senseid}']/grammatical-info[@value='{ps}']/../.."
                    f"/field[@type='{fieldtype}']/form[@lang='{lang}']/..",
            'attr':'node'},
        'fieldname': {
            'cm': 'use to get value(s) for <<document later>>',
            'url':f"entry[@guid='{guid}']"
                    f"/sense[@id='{senseid}']/grammatical-info[@value='{ps}']/../.."
                    f"/field",
            'attr':'type'},
        'fieldvalue': {
            'cm': 'use to get value(s) for field(s) of a specified (or all) '
                    'type(s) with a form in the specified (or any) language '
                    'for one or all entries (no reference to fields, nor to '
                    'lexeme form language)',
            'url':(f"entry[@guid='{guid}']"
                    f"/sense[@id='{senseid}']/grammatical-info[@value='{ps}']/../.."
                    f"/field[@type='{fieldtype}']"
                    f"/form[@lang='{lang}']/text" #Which lang should this be?
                    ),
            'attr':'nodetext'},
        #Do before other pronunciation names/values
        'pronunciationbylocation': {
            'cm': 'use to get value(s) for pronunciation information for a '
                    'given location',
            'url':(f"entry[@guid='{guid}']"
                    f"/sense[@id='{senseid}']/grammatical-info[@value='{ps}']/../.."
                    f"/pronunciation"
                    f"/trait[@name='location'][@value='{location}']"
                    f"/../form[@lang='{analang}']/text"),
            'attr':'nodetext'},
        'pronunciationfieldname': {
            'cm': 'use to get value(s) for <<document later>>',
            'url':(f"entry[@guid='{guid}']"
                    f"/sense[@id='{senseid}']/grammatical-info[@value='{ps}']/../.."
                    f"/pronunciation"
                    f"/trait[@name='location'][@value='{location}']"
                    f"/../field"),
            'attr':'type'},
        'pronunciationfieldvalue': {
            'cm': 'use to get value(s) for <<document later>>',
            'url':(f"entry[@guid='{guid}']"
                    f"/sense[@id='{senseid}']/grammatical-info[@value='{ps}']/../.."
                    f"/pronunciation"
                    f"/trait[@name='location'][@value='{location}']/.."
                    f"/field[@type='{fieldtype}']"
                    f"/form[@lang='{lang}']/text"
                    ), #not necessarily glosslang or analang...
            'attr':'nodetext'},
        'exfieldvalue': {
            'cm': 'use to get values of fields at the example level',
            'url':(f"entry[@guid='{guid}']"
                    f"/lexical-unit/form[@lang='{analang}']/../.."
                    f"/sense[@id='{senseid}']"
                        f"/grammatical-info[@value='{ps}']/.."
                        f"/example"
                        f"/field[@type='location']"
                        f"/form[@lang='{glosslang}'][text='{location}']/../.."
                        f"/field[@type='{fieldtype}']"
                        f"/form[@lang='{glosslang}']/text" #"[text='{form}']/../../../.."
                    ),
            'attr':'nodetext'},
        'exfieldvaluefromsense': {
            'cm': 'use to get an example with a given tone/exfield when '
                    'you have the sense node.',
            'url':(f"example/field[@type='location']"
                                        f"/form[text='{location}']/../.."
                                        f"/field[@type='{fieldtype}']"
                                        f"/form[text='{fieldvalue}']/../.."),
                'attr':'nodetext'},
        'exfieldlocation': {
            'cm': 'use to get location of fields at the example level',
            'url':(f"entry[@guid='{guid}']"
                    f"/lexical-unit/form[@lang='{analang}']/../.."
                    f"/sense[@id='{senseid}']"
                        f"/grammatical-info[@value='{ps}']/.."
                        f"/example"
                        f"/field[@type='location']"
                        f"/form[@lang='{glosslang}']/text"
                        # f"/field[@type='{fieldtype}']"
                        # f"/form[@lang='{glosslang}']/text" #"[text='{form}']/../../../.."
                    ),
            'attr':'nodetext'},
        'pronunciationfieldlocation': {
            'cm': 'use to get value(s) for pronunciation location/context',
            'url':(f"entry[@guid='{guid}']"
                    f"/sense[@id='{senseid}']/grammatical-info[@value='{ps}']/../.."
                    f"/pronunciation"
                    f"/field[@type='{fieldtype}']/.."
                    f"/trait[@name='location']"
                    #f"/form[@lang='{lang}']/text"
                    ), #not necessarily glosslang or analang...
            'attr':'value'},
        'pronunciation': {
            'cm': 'use to get value(s) for pronunciation in fields with '
                    'location specified',
            'url':(f"entry[@guid='{guid}']"
                    f"/sense[@id='{senseid}']/grammatical-info[@value='{ps}']/../.."
                    f"/pronunciation"
                    f"/trait[@name='location'][@value='{location}']/.."
                    f"/form[@lang='{glosslang}']/text"
                    ),
            'attr':'nodetext'},
        'lexemelang':{
            'cm': "analysis languages used in lexemes",
            'url':(f"entry[@guid='{guid}']"
                    f"/sense[@id='{senseid}']/grammatical-info[@value='{ps}']/../.."
                    f"/lexical-unit/form"),
            'attr': 'lang'},
        'citationlang':{
            'cm': "analysis languages used in citation forms",
            'url':(f"entry[@guid='{guid}']"
                    f"/sense[@id='{senseid}']/grammatical-info[@value='{ps}']/../.."
                    f"/citation/form"),
            'attr': 'lang'},
        'glosslang':{
            'cm': "gloss languages used in glosses",
            'url':(f"entry[@guid='{guid}']"
                    f"/sense[@id='{senseid}']"
                    f"/grammatical-info[@value='{ps}']/.."
                    # f"/lexical-unit"
                    f"/gloss"
                    #f"/form"
                    ),
            'attr': 'lang'},
        'defnlang':{
            'cm': "gloss languages used in definitions",
            'url':(f"entry[@guid='{guid}']"
                    f"/sense[@id='{senseid}']"
                    f"/grammatical-info[@value='{ps}']/.."
                    f"/definition"
                    f"/form"),
            'attr': 'lang'},
        'illustration':{
            'cm': "Illustration by entry",
            'url': f"entry[@guid='{guid}']"
                    f"/sense[@id='{senseid}']/illustration",
            'attr': 'href'},
        'template':{
            'cm': "Give a prose description here",
            'url': f"url in the XML file, variables OK",
            'attr': 'script'},
        'ps':{
            'cm': "Part of speech, or grammatical category",
            'url': f"entry[@guid='{guid}']"
                    f"/sense[@id='{senseid}']"
                    f"/grammatical-info",
            'attr': 'value'}
        }
    if attribute == 'attributes':
        return attributes.keys()
    if attribute not in attributes:
        log.info(' '.join(["Sorry,",attribute,"isn't defined yet. This is what's available:"]))
        for line in list(attributes.keys()):
            try:
                log.info(' '.join(line, '\t',attributes[line]['cm']))
            except:
                log.info(' '.join(line, '\t',"UNDOCUMENTED?!?!", ))
        log.info("This is where that key was called; fix it, and try again:")
    """I should also add/remove pronunciation or other systematic things here"""
    url=attributes[attribute]['url']
    attributes[attribute]['url']=removenone(attributes[attribute]['url'])
    return attributes[attribute] #No idea why, but this returns faster with it..
def removenone(url):
    """Remove any attribute reference whose value is 'None'. I only use
    '@name="location"' when using @value, so also remove it if @value=None."""
    nonattr=re.compile('(\[@name=\'location\'\])*\[[^\[]+None[^\[]+\]')
    newurl=nonattr.sub('',url)
    return newurl
class Error(Exception):
    """Base class for exceptions in this module."""
    pass

class BadParseError(Error):
    def __init__(self, filename):
        self.filename = filename
class Lift(object): #fns called outside of this class call self.nodes here.
    """The job of this class is to expose the XML as python object
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
        # log.info(self.backupfilename)
        # exit()
        self.getguids() #sets: self.guids and self.nguids
        self.getsenseids() #sets: self.senseids and self.nsenseids
        log.info("Working on {} with {}, entries "
                    "and {} senses".format(filename,self.nguids,self.nsenseids))
        """These three get all possible langs by type"""
        self.glosslangs() #sets: self.glosslangs
        self.analangs() #sets: self.analangs, self.audiolangs
        self.pss=self.pss() #log.info(self.pss)
        self.getformstosearch() #sets: self.formstosearch[lang][ps] #no guids
        """This is very costly on boot time"""
        # self.getguidformstosearch() #sets: self.guidformstosearch[lang][ps]
        self.citationforms=self.citationforms() #lang='gnd'
        self.lexemes=self.lexemes()
        self.defaults=[ #these are lift related defaults; check in lift_do
                    'analang',
                    'glosslang',
                    'glosslang2',
                    'audiolang'
                    #'ps',script
                    #'profile',
                    #'type',
                    #'name',
                    #'regexCV',
                    #'subcheck'
                ]
        self.slists() #sets: self.c self.v, not done with self.segmentsnotinregexes[lang]
        self.extrasegments() #tell me if there's anything not in a V or C regex.
        """Think through where this belongs; what classes/functions need it?"""
        # self.addexamplefields(guid=None,
        #                 senseid='72ad850a-d049-4bdc-b6ee-cd58403f4b71',
        #                 analang='gnd',
        #                 glosslang='fr',
        #                 langform='dzəɓər only',
        #                 glossform='cloison tu',
        #                 fieldtype='tone',
        #                 location='Isolation2',
        #                 fieldvalue='[˦˦˦]',
        #                 # ps=None,
        #                 showurl=False)
                                    # self.get('Test')
        # self.addpronunciationfields(guid='005779ea-63b5-4c14-ab79-a32a2a21ac90',
        #     analang=self.analangs[0],glosslang=self.glosslangs[0],lang='en',
        # langform="Languageform here",glossform="Gloss here",fieldtype='tone',location='With Other Stuff',fieldvalue='HL representation',ps=None,showurl=True)
        # self.write()
        # self.addentry(guid='5',senseid='57',ps='Noun',analang='gnx',
        #                 glosslang='fr',langform='gnxform',glossform='frforme',
        #                 now='January 5, 2020',glosslang2='fub',
        #                 glossform2='fub fub')
        log.info("Language initialization done.")
    def get(self,attribute, guid=None, senseid=None, analang=None,
            glosslang=None, lang=None, ps=None, form=None, fieldtype=None,
            location=None, fieldvalue=None, showurl=False):
        """This needs to work when there are multiple languages, etc.
        I think we should iterate over possibilities, if none are specified.
        over lang, what else?
        NB: this would create nested dictionaries... We need to be able to
        access them consistently later."""
        """I need to be careful to not mix up lang=glosslang and lang=analang:
        @lang should only be used here when referring to a <field> field."""
        if attribute == 'Test':
            from random import randint
            # log.info(randint(0, len(self.guids)))
            guid=self.guids[randint(0, len(self.guids))-1]
            log.info("Showing info for randomly selected entry: "+guid)
            for attribute in attributesettings('attributes'):
                log.info(' '.join(attribute,self.get(attribute,guid=guid)))#,showurl=True
                # log.info('senseid',attribute,self.get(attribute,senseid=senseid))#,showurl=True
            senseid=self.senseids[randint(0, len(self.senseids))-1]
            log.info("Showing info for randomly selected sense: "+senseid)
            for attribute in attributesettings('attributes'):
                # log.info('guid',attribute,self.get(attribute,guid=guid))#,showurl=True
                log.info(' '.join(attribute,self.get(attribute,senseid=senseid)))#,showurl=True
            return
        # urlnfn=attributesettings(attribute, guid=guid, lang=lang, ps=ps, fieldtype=fieldtype, location=location)
        """This is slightly faster than kwargs"""
        urlnattr=attributesettings(attribute,guid,senseid,analang,glosslang,
                                        lang,ps,form,
                                        fieldtype,location,
                                        fieldvalue=fieldvalue)
        # log.info(' '.join(attribute,guid,senseid,analang,glosslang,
        #                                 lang,ps,form,
        #                                 fieldtype,location,
        #                                 fieldvalue))
        #url=self.attributes[attribute]['url']
        #url=attributesettings(attribute, guid, lang, fieldtype, location)['url']
        url=urlnattr['url']
        if showurl==True:
            log.info(url)
        #url=removenone(url) do in earlier fn
        # if attribute == 'example':
        #     log.info(url)
        #     nodeset=self.nodes.findall("entry/sense[@id='f024c2d9-a1c9-4f50-99cc-3a1e097e4b86']/example")
        # else:
        nodeset=self.nodes.findall(url) #This is the only place we need self=lift
        # log.info(nodeset.findall('form'))
        output=[]
        #fn=self.attributes[attribute]['formfn']
        #fn=attributesettings(attribute, guid, lang, fieldtype, location)['formfn']
        attr=urlnattr['attr']
        # log.info(' '.join(attribute,attr,nodeset,len(nodeset)))
        for node in nodeset:
            # for attr in attrs:
                # log.info(' '.join(attribute,attr))
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
            #log.info(' '.join('Node:',node))
            # output+=[fn(node)]
            #output+=[self.attributes[attribute]['formfn'](node)]
            #output+=[self.attributesettings(attribute, guid, lang, fieldtype, location)['formfn'](node)]
        return output #list(dict.fromkeys(output)) #Do I need to remove dups?
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
        # log.info(guid)
        return guid
    def addentry(self,ps,analang,glosslang,langform,glossform,glosslang2=None,
        glossform2=None,showurl=False):
        log.info("Adding an entry")
        self.makenewguid()
        guid=senseid=self.makenewguid()
        while guid == senseid:
            senseid=self.makenewguid()
        log.info(' '.join('newguid:',guid))
        log.info(' '.join('newsenseid:',senseid))
        now=getnow()
        entry=ET.SubElement(self.nodes, 'entry', attrib={
                                'dateCreated':now,
                                'dateModified':now,
                                'guid':guid,
                                'id':(langform+'_'+str(guid))
                                })
        lexicalunit=ET.SubElement(entry, 'lexical-unit', attrib={})
        form=ET.SubElement(lexicalunit, 'form', attrib={'lang':analang})
        text=ET.SubElement(form, 'text')
        text.text=langform
        """At some point, I'll want to distinguish between these two"""
        citation=ET.SubElement(entry, 'citation', attrib={})
        form=ET.SubElement(citation, 'form', attrib={'lang':analang})
        text=ET.SubElement(form, 'text')
        text.text=langform
        sense=ET.SubElement(entry, 'sense', attrib={'id':senseid})
        grammaticalinfo=ET.SubElement(sense, 'grammatical-info',
                                            attrib={'value':ps})
        definition=ET.SubElement(sense, 'definition')
        form=ET.SubElement(definition, 'form', attrib={'lang':glosslang})
        text=ET.SubElement(form, 'text')
        text.text=glossform
        gloss=ET.SubElement(sense, 'gloss', attrib={'lang':glosslang})
        text=ET.SubElement(gloss, 'text')
        text.text=glossform
        if (glosslang2 is not None) and (glossform2 is not None):
            form=ET.SubElement(definition, 'form', attrib={'lang':glosslang2})
            text=ET.SubElement(form, 'text')
            text.text=glossform2
            gloss=ET.SubElement(sense, 'gloss', attrib={'lang':glosslang2})
            text=ET.SubElement(gloss, 'text')
            text.text=glossform
        # self.updatemoddatetime(guid=guid,senseid=senseid)
        self.write()
        """Since we added a guid and senseid, we want to refresh these"""
        self.getguids()
        self.getsenseids()
        return senseid
    def addexamplefields(self,guid,senseid,analang,
                                glosslang,glosslang2,forms,
                                fieldtype,
                                location,fieldvalue,ps=None,showurl=False):
        """This fuction will add an XML node to the lift tree, like a new
        example field."""
        """The program should know before calling this, that there isn't
        already the relevant node --since it is agnostic of what is already
        there."""
        log.info("Adding {} value to {} location in {} fieldtype {} senseid {}"
                "guid (in lift.py)".format(fieldvalue,location,fieldtype,
                                                            senseid,guid))
        """Get the sense node"""
        urlnattr=attributesettings('senseid',senseid=senseid)
        url=urlnattr['url']
        if showurl==True:
            log.info(url)
        node=self.nodes.find(url) #this should always find just one node
        if node is None:
            log.info(' '.join("Sorry, this didn't return a node:",guid,senseid))
            return
        """Logic to check if this example already exists"""
        """This function returns a text node (from any one of a number of
        example nodes, which match form, gloss and location) containing a
        tone sorting value, or None (if no example nodes match form, gloss
        and location)"""
        exfieldvalue=self.exampleissameasnew(guid,senseid,analang,glosslang,
                            glosslang2,
                            forms,
                            fieldtype,
                            location,fieldvalue,node,ps=None,showurl=False)
        if exfieldvalue is None: #If not already there, make it.
            log.info("Didn't find that example already there, creating it...")
            p=ET.SubElement(node, 'example')
            form=ET.SubElement(p,'form',attrib={'lang':analang})
            t=ET.SubElement(form,'text')
            t.text=forms[analang]
            """Until I have reason to do otherwise, I'm going to assume these
            fields are being filled in in the glosslang language."""
            fieldgloss=ET.SubElement(p,'translation',attrib={'type':
                                                        'Frame translation'})
            for lang in [glosslang,glosslang2]:
                if lang != None:
                    form=ET.SubElement(fieldgloss,'form',attrib={'lang':lang})
                    glosstext=ET.SubElement(form,'text')
                    glosstext.text=forms[lang]
            exfield=ET.SubElement(p,'field',attrib={'type':fieldtype})
            form=ET.SubElement(exfield,'form',attrib={'lang':glosslang})
            exfieldvalue=ET.SubElement(form,'text')
            locfield=ET.SubElement(p,'field',attrib={'type':'location'})
            form=ET.SubElement(locfield,'form',attrib={'lang':glosslang})
            fieldlocation=ET.SubElement(form,'text')
            fieldlocation.text=location
        else:
            if self.debug == True:
                log.info("=> Found that example already there")
        exfieldvalue.text=fieldvalue #change this *one* value, either way.
        self.updatemoddatetime(guid=guid,senseid=senseid)
        self.write()
        if self.debug == True:
            log.info("add langform: {}".format(forms[analang]))
            log.info("add tone: {}".format(fieldvalue))
            log.info("add gloss: {}".format(forms[glosslang]))
            if glosslang2 != None:
                log.info(' '.join("add gloss2:", forms[glosslang2]))
        """This is what we're adding/modifying here:
        <example>
            <form lang="gnd"><text>dìve</text></form>
            <translation type="Frame translation">
                <form lang="gnd"><text>constructed gloss here</text></form>
            </translation>
            <field type="tone">
                <form lang="gnd"><text>LM</text></form>
            </field>
            <field type="location">
                <form lang="gnd"><text>Isolation</text></form>
            </field>
        </example>
        """
    def forminnode(self,node,value):
        """Returns True if value is in *any* text node child of any form child
        of node: [node/'form'/'text' = value]
        """
        for f in node.findall('form'):
            for t in f.findall('text'):
                if t.text == value:
                    return True
        return False
    def exampleisnotsameasnew(self,guid,senseid,analang,
                                glosslang,glosslang2,
                                forms,
                                fieldtype,
                                location,fieldvalue,example,ps=None,
                                showurl=False):
        """This checks all the above information, to see if we're dealing with
        the same example or not. Stop and return nothing at first node that
        doesn't match (from form, translation and location). If they all match,
        then return the tone value node to change."""
        if self.debug == True:
            log.info("Looking for bits that don't match")
        for node in example:
            if self.debug == True:
                log.info('Node: {} ; {}'.format(node.tag,
                                                node.find('.//text').text))
            if (node.tag == 'form'):
                if ((node.get('lang') == analang)
                and (node.find('text').text != forms[analang])):
                    if self.debug == True:
                        log.info('{} == {}; {}  != {}'.format(node.get('lang'),
                            analang, node.find('text').text, forms[analang]))
                    return
            elif ((node.tag == 'translation') and
                                (node.get('type') == 'Frame translation')):
                if ((not self.forminnode(node,forms[glosslang])) and
                    ((glosslang2 == None) or
                    (not self.forminnode(node,forms[glosslang2])))):
                    if self.debug == True:
                        log.info(' '.join('translation',node.find('form/text').text, '!=',
                                                                        forms))
                    return
            elif (node.tag == 'field'):
                if (node.get('type') == 'location'):
                    if not self.forminnode(node,location):
                        if self.debug == True:
                            log.info(' '.join('location',location,'not in',node))
                        return
                if (node.get('type') == 'tone'):
                    for form in node:
                        if ((form.get('lang') == glosslang)
                        or (form.get('lang') == glosslang2)):
                            """This is set once per example, since this
                            function runs on an example node"""
                            tonevalue=form.find('text')
                            if self.debug == True:
                                log.info('tone value found: {}'.format(
                                                            tonevalue.text))
                        else:
                            log.info("Not the same lang for tone form")
                            return
            else:
                log.info(' '.join("Not sure what kind of node I'm dealing with!",node.tag))
        return tonevalue
    def exampleissameasnew(self,guid,senseid,analang,
                                glosslang,glosslang2,forms,
                                fieldtype,
                                location,fieldvalue,node,ps=None,showurl=False):
        """This looks for any example in the given sense node, with the same
        form, gloss, and location values"""
        if self.debug == True:
            log.info('Looking for an example node matching these form and gloss'
                'elements: {}'.format(forms))
        for example in node.findall('example'):
            valuenode=self.exampleisnotsameasnew(guid,senseid,analang,
                            glosslang,glosslang2,forms,
                            fieldtype,
                            location,fieldvalue,example,ps=None,showurl=False)
            if valuenode != None: #i.e., they *are* the same node
                return valuenode #if you find the example, we're done looking
            else: #if not, just keep looking, at next example node
                if self.debug == True:
                    log.info('=> This is not the example we are looking '
                            'for: {}'.format(valuenode))
    def addtoneUF(self,senseid,group,analang,guid=None,showurl=False):
        # log.info(' '.join("Adding",group,"draft underlying form value to", senseid,
        #                                 "senseid",guid,"guid (in lift.py)"))
        urlnattr=attributesettings('senseid',senseid=senseid) #just give me the sense.
        url=urlnattr['url']
        if showurl==True:
            log.info(url)
        node=self.nodes.find(url) #this should always find just one node
        if node is None:
            log.info(' '.join("Sorry, this didn't return a node:",guid,senseid))
            return
        t=None
        for field in node.findall('field'):
            # log.info(' '.join('field',field))
            # log.info(' '.join('fieldtype',field.get('type')))
            if field.get('type') == 'tone':
                # log.info(field.find('form'))
                f=field.findall('form')
                # log.info(' '.join('f',f))
                f2=field.find('form')
                # log.info(' '.join('f2',f2))
                # log.info(f.get('lang'))
                t=f2.find('text')
                # log.info(' '.join('t',t))
                for fs in f:
                    t2=fs.find('text')
                    # log.info(' '.join('t2',t2))
        # log.info(t)
        # try:
        #     t
        # except NameError:
        if t is None:
            p=ET.SubElement(node, 'field',attrib={'type':'tone'})
            f=ET.SubElement(p,'form',attrib={'lang':analang})
            t=ET.SubElement(f,'text')
        # else:
        #     pass
        t.text=group
        self.updatemoddatetime(guid=guid,senseid=senseid)
        self.write()
        """<field type="tone">
        <form lang="en"><text>toneinfo for sense.</text></form>
        </field>"""
    def addmediafields(self,node, url,
                        lang, #this should be Check.audiolang
                        showurl=False):
        """This fuction will add an XML node to the lift tree, like a new
        example field."""
        """The program should know before calling this, that there isn't
        already the relevant node --since it is agnostic of what is already
        there."""
        log.info(' '.join("Adding",url,"value to", node,"location"))
        form=ET.SubElement(node,'form',attrib={'lang':lang})
        t=ET.SubElement(form,'text')
        t.text=url
        """Can't really do this without knowing what entry or sense I'm in..."""
        # self.updatemoddatetime(guid=guid,senseid=senseid)
        self.write()
        def debug():
            log.info(' '.join("add langform:", langform))
            log.info(' '.join("add tone:", fieldvalue))
            log.info(' '.join("add gloss:", glossform))
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
        urlnattr=attributesettings('guid',guid) #just give me the entry.
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
        def debug():
            log.info(' '.join("add langform:", langform))
            log.info(' '.join("add tone:", fieldvalue))
            log.info(' '.join("add gloss:", glossform))
        # debug()
        self.updatemoddatetime(guid=guid,senseid=senseid)
        self.write()
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
        urlnattr=attributesettings('senseid',senseid=senseid) #just give me the sense.
        url=urlnattr['url']
        if showurl==True:
            log.info(url)
        node=self.nodes.find(url) #this should always find just one node
        urlnattr2=attributesettings('exfieldvaluefromsense',location=None,
                                    fieldtype=fieldtype,fieldvalue=fieldvalue
                                    )
        url2=urlnattr2['url']
        if showurl==True:
            log.info(url2)
        for example in node.findall(url2):
            # """<field type="tone"><form lang="fr"><text>1</text></form></field>"""
            # """<field type="location"><form lang="fr"><text>Plural</text></form></field>"""
            for child in node:
                print (child.tag, child.attrib)
            for child in example:
                print (child.tag, child.attrib)
            node.remove(example)
        self.updatemoddatetime(guid=guid,senseid=senseid)
        self.write()
    def updateexfieldvalue(self,guid=None,senseid=None,analang=None,
                    glosslang=None,langform=None,glossform=None,fieldtype=None,
                    location=None,fieldvalue=None,ps=None,
                    newfieldvalue=None,showurl=False):
        """This updates the fieldvalue, based on current value. It assumes
        there is a field already there; use addexamplefields if not"""
        urlnattr=attributesettings('exfieldvalue',senseid=senseid,
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
        self.write()
    def updatemoddatetime(self,guid=None,senseid=None,analang=None,
                    glosslang=None,langform=None,glossform=None,fieldtype=None,
                    location=None,fieldvalue=None,ps=None,
                    newfieldvalue=None,showurl=False):
        """This updates the fieldvalue, ignorant of current value."""
        urlnattr=attributesettings('entry',guid=guid,senseid=senseid #,
                                    # fieldtype=fieldtype,
                                    # location=location,
                                    # fieldvalue=fieldvalue
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
        node.attrib['dateModified']=getnow() #text=newfieldvalue #remove(example)
        self.write()
    def read(self):
        """this parses the lift file into an entire ElementTree tree,
        for reading or writing the LIFT file."""
        self.tree=ET.parse(self.filename)
        """This returns the root node of an ElementTree tree (the entire
        tree as nodes), to edit the XML."""
        self.nodes=self.tree.getroot()
    def write(self,filename=None):
        """This writes changes back to XML."""
        """When this goes into production, change this:"""
        #self.tree.write(self.filename, encoding="UTF-8")
        if filename is None:
            filename=self.filename
        self.tree.write(filename, encoding="UTF-8")
    def analangs(self):
        log.log(1,_("Looking for analangs in lift file"))
        self.audiolangs=[]
        self.analangs=[]
        possibles=list(dict.fromkeys(self.get('lexemelang')+self.get('citationlang')))
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
        if forms == []: #for the whole db this will not work if even one gloss is filled out
            forms=self.get('definition',guid=guid,senseid=senseid,
                        glosslang=lang,
                        showurl=showurl)
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
    def nlist(self): #This variable gives lists, to iterate over.
        # prenasalized=['mb','mp','mbh','mv','mf','nd','ndz','ndj','nt','ndh','ng','ŋg','ŋg','nk','ngb','npk','ngy','nj','nch','ns','nz']  #(graphs that preceede a consonant)
        ntri=["ng'"]
        ndi=['mm','ny','ŋŋ']
        nm=['m','m','M','n','n','ŋ','ŋ','ɲ']
        nasals=ntri+ndi+nm
        actuals={}
        for lang in self.analangs:
            unsorted=self.inxyz(lang,nasals)
            """Make digraphs appear first, so they are matched if present"""
            actuals[lang]=sorted(unsorted,key=len, reverse=True)
        return actuals
    def glist(self): #This variable gives lists, to iterate over.
        glides=['ẅ','y','Y','w','W']
        actuals={}
        for lang in self.analangs:
            unsorted=self.inxyz(lang,glides) #remove the symbols which are not in the data.
            """Make digraphs appear first, so they are matched if present"""
            actuals[lang]=sorted(unsorted,key=len, reverse=True)
        return actuals
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
        c['p'][1]=['p','P','b','ɓ','Ɓ','B','t','d','ɗ','ɖ','c','k','g','ɡ','G',
                                                                'ʔ',"ꞌ",'ʼ']
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
        x['G']=['ẅ','y','Y','w','W']
        x['CG']=list((char+g for char in x['C'] for g in x['G']))
        x['N']=["ng'",'mm','ny','ŋŋ','m','M','n','ŋ','ɲ']
        x['NC']=list((n+char for char in x['C'] for n in x['N']))
        x['NCG']=list((n+char+g for char in x['C'] for n in x['N']
                                                    for g in x['G']))
        """Non-Nasal/Glide Sonorants"""
        x['S']=['rh','wh','l','r']
        x['CS']=list((char+s for char in x['C'] for s in x['S']))
        x['NCS']=list((n+char+s for char in x['C'] for n in x['N']
                                                    for s in x['S']))
        # self.treatlabializepalatalizedasC=False
        # if self.treatlabializepalatalizedasC==True:
        #     lp={}
        #     lp['lab']=list(char+'w' for char in c)
        #     lp['pal']=list(char+'y' for char in c)
        #     lp['labpal']=list(char+'y' for char in lp['lab'])
        #     lp['labpal']+=list(char+'w' for char in lp['pal'])
        #     for stype in sorted(lp.keys()): #larger graphs first
        #         c=lp[stype]+c
        x['V']=['a', 'á', 'i', 'ɨ', 'ï', 'í','ɪ', 'u', 'ʉ', 'ʊ', 'ɑ', 'e', 'ɛ', 'o',
                'ɔ', 'ʌ', 'ə', 'æ', 'a͂', 'o͂', 'i͂', 'u͂', 'ə̃', 'ã', 'ĩ', 'ɪ̃',
                'õ', 'ɛ̃', 'ẽ', 'ɔ̃', 'ũ', 'ʊ̃', 'I', 'U', 'E', 'O']
        x['d']=["̀","́","̂","̌","̄","̃"] #"à","á","â","ǎ","ā","ã"[=́̀̌̂̃ #vowel diacritics
        """We need to address long and idiosyncratic vowel orthographies,
        especially for Cameroon. This should also include diacritics, together
        or separately."""
        """At some point, we may want logic to include only certain
        elements in c. The first row is in pretty much any language."""
        actuals={}
        log.log(3,'hypotheticals: {}'.format(x))
        self.s={} #wipe out an existing dictionary
        for lang in self.analangs:
            if lang not in self.s:
                self.s[lang]={}
            for stype in x:
                self.s[lang][stype]=self.inxyz(lang,x[stype])
                log.log(3,'hypotheticals[{}][{}]: {}'.format(lang,stype,
                                                    str(x[stype])))
                log.log(3,'actuals[{}][{}]: {}'.format(lang,stype,
                                                str(self.s[lang][stype])))
    def slists(self):
        self.segmentsnotinregexes={}
        self.clist()
    def segmentin(self, lang, glyph):
        """This actually allows for dygraphs, etc., so I'm keeping it."""
        """check each form and lexeme in the lift file (not all files
        use both)."""
        for form in self.citationforms[lang] + self.lexemes[lang]:
            if re.search(glyph,form): #see if the glyph is there
                return glyph #find it and stop looking, or return nothing
    def inxyz(self, lang, segmentlist): #This calls the above script for each character.
        actuals=list()
        for i in segmentlist:
            s=self.segmentin(lang,i)
            #log.info(s) #to see the following run per segment
            if s is not None:
                actuals.append(s)
        return list(dict.fromkeys(actuals))
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
        forms=self.get('citation',lang=lang,ps=ps)
        # if len(forms) == 0: #no items returned, I should probably combine
                            #this at some point, list(dict.fromkeys(form1+form2))
        forms+=self.get('lexeme',lang=lang,ps=ps)
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
        for lang in self.analangs:
            self.segmentsnotinregexes[lang]=list()
            extras=list()
            """This is not a particularly sophisticated test. I should be
            also looking for consonant glyphs that occur between vowels,
            and vice versa. Later."""
            # nonwordforming=re.compile('[() \[\]\|,\-!@#$*?]')
            invalid=['(',')',' ','[',']','|',',','-','!','@','#','$','*','?'
                        ,'\n']
            for form in self.citationforms[lang]+self.lexemes[lang]:
                for x in form:
                    # x=nonwordforming.sub('', x)
                    # log.info(' '.join('Checking',x,'from',lang,form))
                    if ((x not in invalid) and (not re.search(x,
                                        str().join(sum(self.s[lang].values(),
                                        []))+str().join(extras)))):
                        self.segmentsnotinregexes[lang].append(x)
                        log.debug('Missing {} from {} {}'.format(x,lang,form))
            if len(self.segmentsnotinregexes[lang]) > 0:
                log.info("The following segments are not in your {} "
                "regex's: {}".format(lang,
                list(dict.fromkeys(self.segmentsnotinregexes[lang]).keys())))
            else:
                log.info(_("Your regular expressions look OK for {0} (there are "
                    "no segments in your {0} data that are not in a regex). "
                    "Note, this doesn't \nsay anything about digraphs or "
                    "complex segments which should be counted as a single "
                    "segment --those may not be covered by \n"
                    "your regexes.".format(lang)))
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
        if ps is 'All': #When I'm looking through each ps, not ps=None (e.g., invalid).
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
        if ps is 'All': #When I'm looking through each ps, not ps=None (e.g., invalid).
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
                    if re.search(regex,form.text): #check if the form matches the regex
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
            if re.search(regex,entry[1]): #check regex against the form part of the tuple output by formsnids
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
    def list2glyphs(x): #This takes a list and concatenates it into a single string.
        return str().join(x)
    def monograph(monographs): #probably not needed, for cbeta() only.
        inxyz=list()
        for i in monographs:
            if re.search('^.$',i): #looking only at digraphs
                inxyz.append(i)
                #s=i[0]
                #log.info(s) #to see the following run per segment
                #if i not in inxyz:
                #    inxyz.append(i)
        return removedups(inxyz)

    def digraph1(digraphs): #probably not needed, for cbeta() only.
        inxyz=list()
        for i in digraphs:
            if re.search('^..$',i): #looking only at digraphs
                inxyz.append(i[0])
                #s=i[0]
                #log.info(s) #to see the following run per segment
                #if s not in inxyz:
                #    inxyz.append(s)
        return inxyz
    def digraph2(digraphs): #probably not needed, for cbeta() only.
        inxyz=list()
        for i in digraphs:
            if re.search('^..$',i): #looking only at digraphs
                inxyz.append(i[1])
                #log.info(s) #to see the following run per segment
                #if s not in inxyz:
                #    inxyz.append(s)
        return inxyz
    def trigraph1(trigraphs): #probably not needed, for cbeta() only.
        inxyz=list()
        for i in trigraphs:
            if re.search('^...$',i): #looking only at digraphs
                s=i[0] #re.search('^.',i)
                #log.info(i) #to see the following run per trigraph
                if  s not in inxyz: #s.group() is not None and
                    inxyz.append(s)
        return inxyz
    def trigraph2(trigraphs): #probably not needed, for cbeta() only.
        inxyz=list()
        for i in trigraphs:
            if re.search('^...$',i): #looking only at digraphs
                s=i[1] #re.search('^.',i)
                #log.info(i) #to see the following run per trigraph
                if  s not in inxyz: #s.group() is not None and
                    inxyz.append(s)
        return inxyz
    def trigraph3(trigraphs): #probably not needed, for cbeta() only.
        inxyz=list()
        for i in trigraphs:
            if re.search('^...$',i): #looking only at digraphs
                s=i[2] #re.search('^.',i)
                #log.info(i) #to see the following run per trigraph
                if  s not in inxyz: #s.group() is not None and
                    inxyz.append(s)
        return inxyz
    def polygraph1(x):
        return digraph1(x)+trigraph1(x) #probably not needed for anything, including cbeta().
"""Functions I'm using, but not in a class"""
def getnow():
    return datetime.datetime.utcnow().isoformat()[:-7]+'Z'

if __name__ == '__main__':
    import time #for testing; remove in production
    def _(x):
        str(x)
    """To Test:"""
    filename="/home/kentr/Assignment/Tools/WeSay/dkx/MazHidi_Lift.lift"
    filename="/home/kentr/Assignment/Tools/WeSay/gnd/gnd.lift"
    filename="/home/kentr/Assignment/Tools/WeSay/gnd/gnd.lift.bak.txt"
    lift=Lift(filename,nsyls=2)
    senseid='bfff97e7-2e3b-40e1-beb1-e682d120b773'
    forms={
        'gnd':'səba',
        'fr':'travail (m) commun (pour doter une fille ou une femme)',
        'fub':'surga'
        }
    location='Isolation'
    guid=None
    analang='gnd'
    glosslang='fr'
    glosslang2=None #'fub'
    fieldtype='tone'
    fieldvalue='!?!?'
    # lift.debug=True
    lift.addexamplefields(guid,senseid,analang,
                                glosslang,glosslang2,forms,
                                # langform,glossform,gloss2form,
                                fieldtype,
                                location,fieldvalue)
    exit()
    guid='130cefa9-63aa-45e7-9996-b17e67870014'
    guid='0007124e-a769-4eb5-a7c0-4ff3af5a3206'
    lang='gnd'
    name='Plural'
    import profiles
    lift.analang='gnd'
    lift.glosslang='fr'
    lift.ps='Nom'
    lift.profile='CVC'
    profiles.get(lift)
    outputs=[]
    # ['72ad850a-d049-4bdc-b6ee-cd58403f4b71',]: #
    for senseid in lift.profileswdatabysense[lift.ps][lift.profile].keys():
        output=lift.get('exfieldlocation',senseid=senseid,
            fieldtype='tone',showurl=True)
        # output=lift.get('exfieldvalue', senseid=senseid,
        #     fieldtype='tone', location=name, showurl=True)
        log.info(' '.join(senseid,output))
        outputs+=output
    log.info(len(outputs))
    # for ps in lift.pss:
    #     # log.info(len(lift.senseidformstosearch[lang][ps][guid]))
    #     log.info(' '.join(ps,len(lift.senseidformstosearch[lang][ps])))
    # log.info(' '.join(lift.get('lexeme', #, guid='0007124e-a769-4eb5-a7c0-4ff3af5a3206',
    #     #fieldtype='tone', location='Plural',
    #     showurl=True)))
        #log.info(hasattr(lift,'db'))
    # lift.get('Test')
    log.info(lift.nodes.get('producer'))
    #Not needed now:
    #Lift.profiles.get(lift, nsyls=lift.nsyls)
    #Not working now?
    exit()
    times=100
    log.info("Timing...")
    start_time=time.time() #move this to function?
    for x in range(times):
        # lift=Lift(filename,nsyls=2)
        c=Entry(lift,guid)
    log.info(' '.join("Finished",times,"iterations in",time.time() - start_time," seconds."))
    lang=None
    guid=None
    fieldtype=None
    location=None
    def getfieldscheck(lift,guid,lang,fieldtype,location):
        lexeme=lift.get('pronunciationfieldname',guid,lang,fieldtype,location)
        #log.info(lexeme)
        lexeme=lift.get('pronunciationfieldvalue',guid,lang,fieldtype,location)
        #log.info(lexeme)
        lexeme=lift.get('pronunciation',guid,lang,fieldtype,location)
        #log.info(lexeme)
    exit()
    times=100
    for fn in [getfieldscheck]:
        start_time=time.time() #move this to function?
        for x in range(times):
            fn(lift,guid,lang,fieldtype,location) #log.info(' '.join(fn,timeit.timeit(fn, setup=setup, number=times)))
        log.info(' '.join("Finished",times,"iterations of",fn," in",time.time() - start_time," seconds."))
    exit()
    e=Entry(lift,guid)
    log.info(e.nodes)
    #get.gloss(lift)
    gloss='Dummy'
    log.info(get.gloss(lift,None,guid=None))
    log.info('lift_get.Lift() all:')
    def objectliftall(lift,guid):
        gloss=get.gloss(lift,None,guid=None) #lift.glosslang
        return gloss
    gloss=objectliftall(lift,guid)
    log.info(' '.join('\t',gloss))

    log.info('ET.lift all:')
    def etliftall(lift,guid):
        gloss=get.gloss(lift.nodes,None,guid=None) #lift.glosslang
        return gloss
    gloss=etliftall(lift,guid)
    log.info(' '.join('\t',gloss))

    log.info('lift_get.Lift():')
    def objectlift(lift,guid):
        #gloss=get.obliftdefn(lift,guid,lang=lift.glosslang) #get.gloss(lift,None,guid) #lift.glosslang
        gloss=get.gloss(lift,None,guid) #lift.glosslang
        return gloss
    gloss=objectlift(lift,guid)
    log.info(' '.join('\t',gloss))

    log.info('lift_get.Entry():')
    def objectentry(lift,guid):
        entry=Entry(lift,guid) #for lift_get.Entry()
        gloss=entry.gloss
        return gloss
    gloss=objectentry(lift,guid)
    log.info(' '.join('\t',gloss))

    log.info('ET.entry:')
    def etentry(lift,guid):
        entry=lift.nodes.find(f"entry[@guid='{guid}']") #for nodeset
        #gloss=get.etentrydefn(entry,lang=lift.glosslang) #get.gloss(entry,None,guid) #lift.glosslang
        get.gloss(entry,None,guid) #lift.glosslang
        return gloss
    gloss=etentry(lift,guid)
    log.info(' '.join('\t',gloss))

    log.info('ET.lift:')
    def etlift(lift,guid):
        #gloss=get.etliftdefn(lift.nodes,guid,lang=lift.glosslang) #get.gloss(lift.nodes,None,guid) #lift.glosslang
        get.gloss(lift.nodes,None,guid) #lift.glosslang
        return gloss
    gloss=etlift(lift,guid)
    log.info(' '.join('\t',gloss))
    #exit()
    exit()
    times=100
    for fn in [getfieldscheck,objectliftall,etliftall,objectlift,etlift,objectentry,etentry]:
        start_time=time.time() #move this to function?
        for x in range(times):
            fn(lift,guid) #log.info(' '.join(fn,timeit.timeit(fn, setup=setup, number=times))
        log.info(' '.join("Finished",fn," in",time.time() - start_time," seconds."))

        #C=lift_get.cbeta() #This might need some formatting to work in a regex above.
        #out2=C,timeit.timeit(test, number=times)
        #log.info(out1)
        #log.info(out2)

    #lift.nodes=Tree(lift).parsed
