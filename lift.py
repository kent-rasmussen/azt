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
import copy
log = logging.getLogger(__name__)
try: #Allow this module to be used without translation
    _
except:
    def _(x):
        return x
"""This returns the root node of an ElementTree tree (the entire tree as
nodes), to edit the XML."""
class Object(object):
    pass
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
        self.urls={} #store urls generated
        """Problems reading a valid LIFT file are dealt with in main.py"""
        try:
            self.read() #load and parse the XML file. (Should this go to check?)
        except:
            raise BadParseError(self.filename)
        return #for testing, for now
        backupbits=[filename,'_',
                    datetime.datetime.utcnow().isoformat()[:-16], #once/day
                    '.txt']
        self.backupfilename=''.join(backupbits)
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
        # self.findduplicateexamples() #Fix this!
        """Think through where this belongs; what classes/functions need it?"""
        log.info("Language initialization done.")
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
    def retarget(self,urlobj,target):
        k=self.urlkey(urlobj.kwargs)
        urlobj.kwargs['retarget']=target
        k2=self.urlkey(urlobj.kwargs)
        if k2 not in self.urls:
            self.urls[k2]=copy.deepcopy(urlobj)
            self.urls[k2].retarget(target)
        return self.urls[k2]
    def urlkey(self,kwargs):
        kwargscopy=kwargs.copy() #for only differences that change the URL
        kwargscopy.pop('showurl',False)
        k=tuple(sorted([(str(x),str(y)) for (x,y) in kwargscopy.items()]))
        return k
    def get(self, target, **kwargs):
        return self.getfrom(self.nodes, target, **kwargs)
    def getfrom(self, node, target, **kwargs):
        # base=kwargs['base']=node.tag #in case this is specified, but shouldn't be
        # log.info("base: {}".format(base))
        what=kwargs.get('what','node')
        path=kwargs.get('path',[])
        if type(path) is not list:
            path=kwargs['path']=[path]
        showurl=kwargs.get('showurl',False)
        kwargs['target']=target #not kwarg here, but we want it to be one for LiftURL
        k=self.urlkey(kwargs)
        if k in self.urls:
            return self.urls[k] #These are LiftURL objects
        link=LiftURL(base=node,**kwargs) #needs base and target to be sensible; attribute?
        # if showurl:
        #     log.info("Using URL {}".format(url))
        # return link.getwurl(node,what=what) #'what' comes in a kwarg, if wanted
        return link #.get(node,what=what) #get="text", "node" or an attribute name
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
            nodeset=node.findall(url) #This is the only place we need self=lift
        except BaseException as e:
            log.error("Problem getting url: {} ({})".format(url,e))
            return
        output=[]
        attr=urlnattr['attr']
        for n in nodeset:
            if attr == 'nodetext':
                if n is not None:
                    log.log(1,"Returning node text")
                    output+=[n.text]
            elif attr == 'node':
                if n is not None:
                    log.log(1,"Returning whole node")
                    output+=[n]
            else:
                log.log(1,"Returning node attribute")
                output+=[n.get(attr)]
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
            log.debug("removing empty verification node from this sense")
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
    def addexamplefields(self,**kwargs):
        # ,guid,senseid,analang,glosslang,glosslang2,forms,
        # fieldtype,location,fieldvalue,ps=None
        # This fuction will add an XML node to the lift tree, like a new
        # example field.
        # The program should know before calling this, that there isn't
        # already the relevant node --since it is agnostic of what is already
        # there.
        log.info(_("Adding values (in lift.py) : {}").format(kwargs))
        # showurl=kwargs.get('showurl',False)
        senseid=kwargs.get('senseid')
        location=kwargs.get('location')
        node=self.getsensenode(senseid=senseid)
        if node is None:
            log.info("Sorry, this didn't return a node: {}".format(senseid))
            return
        fieldtype=kwargs.get('fieldtype')
        tonevalue=kwargs.get('fieldvalue')
        # Logic to check if this example already here
        # This function returns a text node (from any one of a number of
        # example nodes, which match form, gloss and location) containing a
        # tone sorting value, or None (if no example nodes match form, gloss
        # and location)
        #We're adding a node to kwargs here.
        # exfieldvalue=self.get('examplebylocation',senseid=senseid,location=location)
        exfieldvalue=lift.get('example/field/form/text',
                                    path=['location','tonefield'],
                                    senseid=senseid,
                                    fieldtype='tone',location=location,
                                    # tonevalue=fieldvalue,
                                    what='node')
        # Do this for all duplicates, which should be removed later anyway.
        # I.e., don't leave inconsisted data in the database.
        if len(exfieldvalue) > 0:
            for e in exfieldvalue:
                e.text=tonevalue
        else: #If not already there, make it.
            log.info("Didn't find that example already there, creating it...")
            analang=kwargs.get('analang')
            glosslang=kwargs.get('glosslang')
            glosslang2=kwargs.get('glosslang2',None)
            db=kwargs.get('db')
            forms=db.forms
            glosses=db.glosses
            glosslangs=db.glosslangs
            p=Node(node, tag='example')
            p.makeformnode(analang,db.analang)
            """Until I have reason to do otherwise, I'm going to assume these
            fields are being filled in in the glosslang language."""
            fieldgloss=Node(p,'translation',attrib={'type':
                                                        'Frame translation'})
            for lang in glosslangs:
                if lang != None and hasattr(forms,lang):
                    fieldgloss.makeformnode(lang,getattr(forms,lang))
            exfieldvalue=p.makefieldnode(fieldtype,glosslang,gimmetext=True)
            p.makefieldnode('location',glosslang,text=location)
            p.makefieldnode('tone',glosslang,text=tonevalue)
        # exfieldvalue.text=fieldvalue #change this *one* value, either way.
        senseid=kwargs.get('senseid')
        if 'guid' in kwargs:
            guid=kwargs.get('guid')
            self.updatemoddatetime(guid=guid,senseid=senseid)
        else:
            self.updatemoddatetime(senseid=kwargs['senseid'])
        if self.debug == True:
            log.info("add langform: {}".format(forms.analang))
            log.info("add tone: {}".format(fieldvalue))
            log.info("add gloss: {}".format(forms.glosslang))
            if glosslang2 != None:
                log.info("add gloss2: {}".format(forms.glosslang2))
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
    def exampleisnotsameasnew(self, **kwargs):
        # guid,senseid,analang, glosslang, glosslang2, forms, fieldtype,
        # location,fieldvalue,example,ps=None,
        # """This checks all the above information, to see if we're dealing with
        # the same example or not. Stop and return nothing at first node that
        # doesn't match (from form, translation and location). If they all match,
        # then return the tone value node to change."""
        tonevalue='' # set now, will change later, or not...
        log.info("Looking for bits that don't match")
        showurl=kwargs.get('showurl',False)
        db=kwargs.get('db')
        log.info("kwargs: {}".format(kwargs))
        log.info("db: {}; forms: {}".format(db,db.forms))
        analang=db.analangs[0]
        location=db.location
        forms=db.forms
        glosses=db.glosses
        glosslangs=db.glosslangs
        glosslang=kwargs.get('glosslang')
        glosslang2=kwargs.get('glosslang2',None)
        try:
            example=kwargs.get('example')
        except:
            log.info("Hey! You gave me an empty example?!")
            return
        for node in example:
            try:
                log.info('Node: {} ; {}'.format(node.tag,
                                                node.find('.//text').text))
            except:
                log.info('Node: {} ; Likely no text node!'.format(node.tag))
            if (node.tag == 'form'):
                if ((node.get('lang') == analang)
                and (node.find('text').text != forms[analang])):
                    log.info('{} == {}; {} != {}'.format(node.get('lang'),
                            analang, node.find('text').text, forms[analang]))
                    return
            elif ((node.tag == 'translation') and
                                (node.get('type') == 'Frame translation')):
                for form in node.findall('form'):
                    l=form.get('lang')
                    if l is None:
                        log.info("translation lang empty; can't test it")
                        continue
                    glform=db.glosses[l] #getattr(glosses,l,None)
                    if (l in glosslangs and form.find('text').text != glform):
                        log.info('{} translation "{}" != "{}"'.format(l,
                                    node.find('form/text').text, glform))
                        return
            elif (node.tag == 'field'):
                if (node.get('type') == 'location'):
                    thislocation=node.find('form/text').text
                    if thislocation != location: #not node.find('form/text').text
                        log.info('location {} not {}'.format(thislocation,location))
                        return
                if (node.get('type') == 'tone'):
                    for form in node:
                        l=form.get('lang')
                        if l in glosslangs:
                            """This is set once per example, since this
                            function runs on an example node"""
                            tonevalue=form.find('text')
                            log.debug('tone value found: {}'.format(
                                                            tonevalue.text))
                        else:
                            log.info("Not the same lang for tone form: {}"
                                        "".format(l))
                            return
            else:
                log.debug("Not sure what kind of node I'm dealing with! ({})"
                                                            "".format(node.tag))
        return tonevalue
    def exampleissameasnew(self, **kwargs):
        # ,guid,senseid,analang, glosslang,glosslang2,forms, fieldtype,
        # location,fieldvalue,node,ps=None
        """This looks for any example in the given sense node, with the same
        form, gloss, and location values"""
        # showurl=kwargs.get('showurl',False)
        node=kwargs.get('node')
        # analang=kwargs.get('analang')
        # glosslang=kwargs.get('glosslang')
        # location=kwargs.get('location')
        db=kwargs.get('db')
        # glosslang2=kwargs.get('glosslang2',None)
        # try:
        #     example=kwargs.get('example')
        log.info('Looking for an example node matching these form and gloss '
                'elements: {}\n(from these: {})'.format(db.forms,db.__dict__))
        examples=node.findall('example')
        for example in examples:
            log.info(_("Looking at example {} ({} of {})").format(example,
                                    examples.index(example)+1, len(examples)))
            valuenode=self.exampleisnotsameasnew(**kwargs, example=example)
            if valuenode is None:
                log.debug('=> This is not the example we are looking '
                            'for: {}'.format(valuenode))
                continue
            log.info(_("Found it? {}".format(type(valuenode))))
            # log.info(_("Found it? {}: {}".format(type(valuenode),valuenode.text)))
            if isinstance(valuenode,ET.Element): #None: #i.e., they *are* the same node
                log.info(_("Found it! {}: {}".format(type(valuenode),
                                                            valuenode.text)))
                return valuenode #if you find the example, we're done looking
    def findduplicateforms(self):
        """This removes duplicate form nodes in lx or lc nodes, not much point.
        """
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
            forms=Object() #?!?!
            forms.forms=Object()
            setattr(forms,'analangs',analangs)
            setattr(forms,'glosslangs',glosslangs)
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
                        setattr(forms,'analang',formnodetext.text)
                        setattr(forms.forms,lang,forms.analang)
                        # forms[lang]=formnodetext.text#
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
                        if len(glosslangs) >0:
                            forms.glosslang2=formnodetext.text
                            setattr(forms.forms,lang,forms.glosslang2)
                        else:
                            forms.glosslang=formnodetext.text
                            setattr(forms.forms,lang,forms.glosslang)
                        # forms[lang]=formnodetext.text#
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
                examples=sense.findall('example') #'senselocations'
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
                                                db=ex1[0],
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
        prettyprint(node)
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
        node=self.geturlnattr('exfieldvaluenode',senseid=senseid,
                                    fieldtype=fieldtype,
                                    location=location,
                                    fieldvalue=fieldvalue
        )
        # url=urlnattr['url']
        if showurl==True:
            log.info(url)
        # node=self.nodes.find(url) #this should always find just one node
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
            write=True
        except:
            log.error("There was a problem writing to partial file: {}"
                    "".format(filename+'.part'))
        if write:
            try:
                os.replace(filename+'.part',filename)
            except:
                log.error("There was a problem writing {} file to {} "
                "directory. This is what's here: {}".format(
                    pathlib.Path(filename).name, pathlib.Path(filename).parent,
                    os.listdir(pathlib.Path(filename).parent)))
    def analangs(self):
        log.log(1,_("Looking for analangs in lift file"))
        self.audiolangs=[]
        self.analangs=[]
        lxl=self.get('lang',base='entry',path=['lexeme'],target='form')
        lcl=self.get('lang',base='entry',path=['citation'],target='form')
        pronl=self.get('lang',base='entry',path=['pronunciation'],target='form')
        possibles=list(dict.fromkeys(lxl+lcl+pronl))
        log.info(_("Possible analysis language codes found: {}".format(possibles)))
        for glang in ['fr','en']:
            if glang in possibles:
                for form in ['citation','lexeme']:
                    gforms=self.get(form,base='entry',target=form+'/form',analang=glang)
                    if 0< len(gforms):
                        # log.info("LWC lang {} found in {} field: {}".format(
                        #     glang,form,self.get(form,analang=glang)))
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
        g=self.get('lang',base='sense',target='gloss')
        d=self.get('lang',base='sense',target='definition')
        self.glosslangs=list(dict.fromkeys(g+d))
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
        return dict(self.get('type',base='field',target='field')).fromkeys()#nfields=0
        # return self.get('fieldname',guid=guid,lang=lang)#nfields=0
    def getsenseids(self): #get the number entries in a lift file.
        self.senseids=self.get('senseid',base='sense',target='sense') #,showurl=True
        self.nsenseids=len(self.senseids) #,guid,lang,fieldtype,location
        # log.info(self.nsenseids)
    def getguids(self): #get the number entries in a lift file.
        self.guids=self.get('guid',base='entry',target='entry') #,showurl=True
        # log.info(self.guids)
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
        c['pvd']={}
        c['pvd'][2]=['bh','dh','gh','gb']
        c['pvd'][1]=['b','B','d','g','ɡ','G']
        c['p']={}
        c['p'][2]=['kk','kp']
        c['p'][1]=['p','P','ɓ','Ɓ','t','ɗ','ɖ','c','k']
        c['fvd']={}
        c['fvd'][2]=['bh','vh','zh']
        c['fvd'][1]=['j','J','v','z','Z','ʒ','ð','ɣ']
        c['f']={}
        c['f'][2]=['ch','ph','sh','hh']
        c['f'][1]=['F','f','s','ʃ','θ','x','h']
        c['avd']={}
        c['avd'][2]=['dj','dz','dʒ']
        c['a']={}
        c['a'][3]=['chk']
        c['a'][2]=['ts','tʃ']
        c['lfvd']={}
        c['lfvd'][2]=['zl','zl']
        c['lfvd'][1]=['ɮ']
        c['lf']={}
        c['lf'][2]=['sl']
        c['lf'][1]=['ɬ']
        c['pn']={}
        """If these appear, they should always be single consonants."""
        c['pn'][2]=['ᵐb','ᵐp','ᵐv','ᵐf','ⁿd','ⁿt','ᵑg','ⁿg','ᵑg','ⁿk','ᵑk',
                    'ⁿj','ⁿs','ⁿz']
        x={} #dict to put all hypothetical segements in, by category
        for nglyphs in [3,2,1]:
            if nglyphs == 3:
                consvar='Ctg'
                dconsvar='Dtg'
            elif nglyphs == 2:
                consvar='Cdg'
                dconsvar='Ddg'
            elif nglyphs == 1:
                consvar='C'
                dconsvar='D'
            x[consvar]=list() #to store valid consonants in
            x[dconsvar]=list() #to store valid depressor consonants in
            for stype in c:
                if c[stype].get(nglyphs) is not None:
                    # if 'vd' in stype:
                    #     x[dconsvar]+=c[stype][nglyphs]
                    # else:
                        x[consvar]+=c[stype][nglyphs]
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
        x['N']=["ng'",'mm','ŋŋ','m','M','N','n','ŋ','ɲ'] #no longer:'ny',
        # x['NC']=list((n+char for char in x['C'] for n in x['N']))
        # x['NCG']=list((n+char+g for char in x['C'] for n in x['N']
        #                                             for g in x['G']))
        """Non-Nasal/Glide Sonorants"""
        x['S']=['l','r']
        x['Sdg']=['rh','wh']
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
                'Â', 'Ê', 'Î', 'Ô', 'Û',
                'ã', 'ẽ', 'ĩ', 'õ', 'ũ'
                ]
        x['Vdg']=['ou','ei','ɨʉ','ai', #requested by bfj
                'óu','éi','ɨ́ʉ','ái',
                'òu','èi','ɨ̀ʉ','ài',
                'yi','yu','yɨ','yʉ'] #requested by Jane
        x['Vtg']=[]

        x['d']=["̀","́","̂","̌","̄","̃"
                , "᷉","̋","̄","̏","̌","̂","᷄","᷅","̌","᷆","᷇","᷉" #from IPA keyboard
                ,"̈" #COMBINING DIAERESIS
                ] #"à","á","â","ǎ","ā","ã"[=́̀̌̂̃ #vowel diacritics
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
                log.debug('hypotheticals[{}][{}]: {}'.format(lang,stype,
                                                    str(x[stype])))
                log.debug('actuals[{}][{}]: {}'.format(lang,stype,
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
class Node(ET.Element):
    def makefieldnode(self,type,lang,text=None,gimmetext=False):
        n=Node(self,'field',attrib={'type':type})
        nn=n.makeformnode(lang,text,gimmetext=gimmetext)
        if gimmetext:
            return nn
    def makeformnode(self,lang,text=None,gimmetext=False):
        n=Node(self,'form',attrib={'lang':lang})
        nn=Node(n,'text')
        if text is not None:
            nn.text=text
        if gimmetext:
            return nn
    def __init__(self, parent, tag, attrib={}, **kwargs):
        super(Node, self).__init__(tag, attrib, **kwargs)
        parent.append(self)
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
class LiftURL():
    def get(self,what='node'):
        log.info(self.__dict__)
        n=self.base.findall(self.url)
        if n != []:
            log.debug("found: {} (x{}), looking for {}".format(n[:1],len(n),what))
        what=self.unalias(what)
        if n == [] or what is None or what == 'node':
            return n
        elif what == 'text':
            r=[i.text for i in n]
            log.debug(r)
            return r
        else:
            r=[i.get(what) for i in n]
            log.debug(r)
            return r
    def build(self,tag,liftattr=None,myattr=None,attrs=None):
        buildanother=False
        noseparator=False
        log.log(21,"building {}, @dict:{}, @{}={}, on top of {}".format(tag,
                                attrs,liftattr,myattr, self.currentnodename()))
        b=tag
        if attrs is None:
            attrs={liftattr: myattr}
        for attr in attrs:
            if (None not in [attr,attrs[attr]] and attrs[attr] in self.kwargs
                                and self.kwargs[attrs[attr]] is not None):
                b+="[@{}='{}']".format(attr,self.kwargs[attrs[attr]])
        if ((liftattr is None or (liftattr in self.kwargs #no lift attribute
                                and self.kwargs[liftattr] is None))
                and tag == 'text' and myattr in self.kwargs #text value to match
                                        and self.kwargs[myattr] is not None):
            b="[{}='{}']".format(tag,self.kwargs[myattr])
            noseparator=True
            if tag == 'text' and tag in self.targettail:
                buildanother=True #the only way to get text node w/o value
        self.url+=[b]
        if noseparator:
            l=self.url
            self.url=[i for i in l[:len(l)-2]]+[''.join([i for i in l[len(l)-2:]])]
        else:
            self.level['cur']+=1
        self.level[self.alias.get(tag,tag)]=self.level['cur']
        log.log(21,"Path so far: {}".format(self.drafturl()))
        if buildanother:
            self.build(tag)
    def parent(self):
        self.level['cur']-=2 #go up for this and its parent
        self.build("..")
    def entry(self):
        self.build("entry","guid","guid")
        self.bearchildrenof("entry")
    def text(self,value):
        self.baselevel()
        self.build("text",myattr="value")
    def form(self,value=None,lang=None):
        self.baselevel()
        self.kwargs['value']=self.kwargs.get(value,None) #location and tonevalue
        log.log(21,"form kwargs: {}".format(self.kwargs))
        self.build("form","lang","lang") #OK if lang is None
        if value is not None:
            self.text("value")
    def citation(self):
        self.baselevel()
        self.build("citation")
        self.form("lcform","analang")
    def lexeme(self):
        self.baselevel()
        self.build("lexical-unit")
        self.form("lxform","analang")
    def pronunciation(self):
        self.baselevel()
        self.build("pronunciation")
        self.kwargs['ftype']='location'
        attrs={"name":"ftype",'value':'location'}
        self.trait(attrs=attrs)
        self.form("pronunciation",'analang')
    def trait(self,attrs={}):
        self.baselevel()
        self.build("trait",attrs=attrs)
    def sense(self):
        self.baselevel()
        self.build("sense","id","senseid")
        self.bearchildrenof("sense")
    def ps(self):
        self.baselevel()
        self.build("grammatical-info","value","ps")
    def gloss(self):
        self.baselevel()
        self.build("gloss","lang","glosslang")
    def definition(self):
        self.baselevel()
        self.build("definition","lang","glosslang")
        self.form("definition","glosslang")
    def example(self):
        self.baselevel()
        self.build("example")
        self.maybeshow('form')
        self.maybeshow('translation')
        self.maybeshow('locationfield')
        self.maybeshow('tonefield')
    def translation(self):
        self.baselevel()
        self.kwargs['ftype']='Frame translation'
        self.kwargs['formtext']='translationvalue'
        self.build("translation","type","ftype")
        self.form("translationvalue",'glosslang')
    def field(self):
        self.baselevel()
        self.build("field","type","ftype")
    def locationfield(self):
        self.baselevel()
        self.kwargs['ftype']='location'
        self.kwargs['formtext']='location'
        self.field()
        self.form("location",'glosslang')
    def tonefield(self):
        self.baselevel()
        self.kwargs['ftype']='tone'
        self.kwargs['formtext']='tonevalue'
        self.field()
        self.form("tonevalue",'glosslang')
    def morphtype(self):
        if morphtype in self.kwargs:
            attrs={'name':"morph-type",'value':self.kwargs[morphtype]}
        self.trait(attrs) # <trait name="morph-type" value="stem" />
    def attrdonothing(self):
        pass
    def maybeshow(self,nodename,parent=None):
        # for arg in args:
        #     log.info("maybeshow arg: {}".format(arg))
        if self.shouldshow(nodename): #We need it for a child to show, etc
            self.show(nodename,parent)
    def show(self,nodename,parent=None): #call this directly if you know you want it
        if nodename == 'form': #args:value,lang
            if parent is None:
                log.error("Sorry, I can't tell what form to pass to this field;"
                            "\nWhat is its parent?")
                return
            else:
                args=self.formargsbyparent(parent)
        elif nodename == 'text': #args:value,lang
            args=['formtext'] #This needs to be smarter; different kinds of formtext
        else:
            args=list()
        for arg in args:
            log.debug("show arg: {}".format(arg))
        if len(args) == 0:
            getattr(self,nodename)()
        else:
            getattr(self,nodename)(*args)
    def formargsbyparent(self,parent):
        args=list()
        if parent in ['gloss', 'definition']:
            args.append(parent)
            args.append('glosslang')
        if parent in ['lexeme', 'citation', 'example']:
            if parent == 'example':
                if 'audiolang' not in self.kwargs:
                    args.append('exampleform')
                else:
                    args.append('exampleaudio')
                    args.append('analang')
                    return args
            else:
                args.append(parent)
            args.append('analang')
        return args
    def lift(self):
        log.error("LiftURL is trying to make a lift node; this should never "
                "happen; exiting!")
        exit()
    def bearchildrenof(self,parent):
        log.debug("bearing children of {} ({})".format(parent,
                                                        self.children[parent]))
        for i in self.children[parent]:
            log.debug("bearchildrenof i: {}".format(i))
            self.maybeshow(i,parent)
    def levelup(self,target):
        while self.level.get(target,self.level['cur']+1) < self.level['cur']:
            self.parent()
    def baselevel(self):
        parents=self.parentsof(self.callerfn())
        for target in parents: #self.levelsokfor[self.callerfn()]: #targets: #targets should be ordered, with best first
            if target in self.level and self.level[target] == self.level['cur']:
                return #if we're on an acceptable level, just stop
            elif target in self.level:
                self.levelup(target)
            elif parents.index(target) < len(parents)-1:
                log.debug("level {} not in {}; checking the next one...".format(
                                                            target,self.level))
            else:
                log.error("last level {} (of {}) not in {}; this is a problem!"
                            "".format(target,parents,self.level))
                log.error("this is where we're at: {}\n  {}".format(self.kwargs,
                                                            self.drafturl()))
                printurllog()
                exit()
    def maybeshowtarget(self,parent):
        # parent here is a node ancestor to the current origin, which may
        # or may not be an ancestor of targethead. If it is, show it.
        f=self.getfamilyof(parent,x=[])
        log.log(21,"Maybeshowtarget: {} (family: {})".format(parent,f))
        if self.targethead in f:
            if parent in self.level:
                log.log(21,"Maybeshowtarget: leveling up to {}".format(parent))
                self.levelup(parent)
            else:
                log.log(21,"Maybeshowtarget: showing {}".format(parent))
                self.show(parent)
            self.showtargetinhighestdecendance(parent)
            return True
    def showtargetinlowestancestry(self,nodename):
        log.log(21,"Running showtargetinlowestancestry for {}/{} on {}".format(
                                    self.targethead,self.targettail,nodename))
        #If were still empty at this point, just do the target if we can
        if nodename == [] and self.targethead in self.children[self.basename]:
            self.show(self.targethead)
            return
        gen=nodename
        g=1
        r=giveup=False
        while not r and giveup is False:
            log.debug("Trying generation {}".format(g))
            gen=self.parentsof(gen)
            for p in gen:
                r=self.maybeshowtarget(p)
                if r:
                    break
            g+=1
            if g>10:
                giveup=True
        if giveup is True:
            log.error("Hey, I've looked back {} generations, and I don't see"
                    "an ancestor of {} (target) which is also an ancestor of "
                    "{} (current node).".format(g,self.targethead,nodename))
    def showtargetinhighestdecendance(self,nodename):
        log.debug("Running showtargetinhighestdecendance for {} on {}".format(
                                                    self.targethead,nodename))
        children=self.children[nodename]
        grandchildren=[i for child in children
                                if child in self.children
                                for i in self.children[child]
                                    ]
        greatgrandchildren=[i for child in children
                                if child in self.children
                                for grandchild in self.children[child]
                                    if grandchild in self.children
                                    for i in self.children[grandchild]
                                    ]
        log.debug("Looking for {} in children of {}: {}".format(
                                            self.targethead,nodename,children))
        log.debug("Grandchildren of {}: {}".format(nodename,grandchildren))
        log.debug("Greatgrandchildren of {}: {}".format(
                                                nodename,greatgrandchildren))
        if self.targethead in children:
            log.debug("Showing '{}', child of {}".format(self.targethead,nodename))
            self.show(self.targethead,nodename)
        elif self.targethead in grandchildren:
            log.debug("Found target ({}) in grandchildren of {}: {}".format(
                        self.targethead,nodename,grandchildren))
            for c in children:
                if c in self.children and self.targethead in self.children[c]:
                    log.debug("Showing '{}', nearest ancenstor".format(c))
                    self.show(c,nodename) #others will get picked up below
                    self.showtargetinhighestdecendance(c)
        elif self.targethead in greatgrandchildren:
            log.debug("Found target ({}) in gr8grandchildren of {}: {}".format(
                                self.targethead,nodename,greatgrandchildren))
            for c in children:
                for cc in grandchildren:
                    if cc in self.children and self.targethead in self.children[cc]:
                        log.debug("Showing '{}', nearest ancenstor".format(c))
                        self.show(c,nodename) #others will get picked up below
                        self.showtargetinhighestdecendance(c)
        else:
            log.error("Target not found in children, grandchildren, or "
                        "greatgrandchildren!")
    def nodesatlevel(self,levelname='cur'):
        if levelname not in self.level:
            return []
        cur=[x for x,y in self.level.items() if y == self.level[levelname]
                and x != levelname] #obviously not that one...
        cur.reverse()
        return cur
    def parsetargetlineage(self):
        if '/' in self.target: #if target lineage is given
            self.targetbits=self.target.split('/')
            log.debug("{} : {}".format(self.target,self.targetbits))
            self.targethead=self.targetbits[0]
            self.targettail=self.targetbits[1:]
        else:
            self.targethead=self.target
            self.targetbits=[self.targethead,]
            self.targettail=[]
        if 'form' in self.targethead:
            log.error("Looking for {} as the head of a target is going to "
            "cause problems, as it appears in too many places, and is likely "
            "to not give the desired results. Fix this, and try again. (whole "
            "target: {})".format(self.targethead,self.target))
            exit()
    def currentnodename(self):
        last=self.url[-1:]
        if len(last)>0:
            n=last[0].split('[')[0]
            return self.getalias(n)
    def unalias(self,nodename):
        if nodename in self.alias.values():
            for k in self.alias:
                if self.alias[k] == nodename:
                    return k
        return nodename #else
    def getalias(self,nodename):
        return self.alias.get(nodename,nodename)
    def retarget(self,target):
        self.url=[self.url]
        self.target=target
        self.parsetargetlineage()
        self.maketarget()
        self.makeurl()
    def maketarget(self):
        """start by breaking up target, if expressed as lineage. This is needed
        to target form, with example/form distinct from example/field/form.
        Without target='example/form', target form will always find field/form,
        even if field has a sibling form (as it typically would) under example.
        Once the level of the lineage head is decided, the rest of the lineage
        is added."""
        # Now operate on the head of the target lineage
        log.debug("URL (before {} target): {}".format(self.target,self.drafturl()))
        if self.getalias(self.targethead) not in self.level: #If the target hasn't been made yet.
            log.debug(self.url)
            i=self.currentnodename()
            log.debug("URL base: {}; i: {}".format(self.basename,i))
            if i is None: #if it is, skip down in any case.
                i=self.basename
            log.debug("URL bit list: {}; i: {}".format(self.url,i))
            if type(i) == list:
                i=i[0] #This should be a string
            f=self.getfamilyof(i,x=[])
            log.debug("Target: {}; {} family: {}".format(self.targethead,i,f))
            if self.targethead in f:
                self.showtargetinhighestdecendance(i) #should get targethead
                    # return #only do this for the first you find (last placed).
            else:#Continue here if target not a current level node decendent:
                self.showtargetinlowestancestry(i)
            # Either way, we finish by making the target tail, and leveling up.
        if self.targettail is not None:
            for b in self.targettail:
                n=self.targetbits.index(b)
                bp=self.targetbits[n-1].split('[')[0]#just the node, not attrs
                afterbp=self.drafturl().split(self.unalias(bp))
                log.log(21,"b: {}; bp: {}; afterbp: {}".format(b,bp,afterbp))
                if len(afterbp) <=1 or b not in afterbp[1]:
                    log.log(21,"showing target element {}: {} (of {})".format(n,b,bp))
                    self.levelup(bp)
                    self.show(b,parent=bp)
        self.levelup(self.targetbits[-1])#leave last in target, whatever else
    def drafturl(self):
        return '/'.join(self.url)
    def makeurl(self):
        self.url='/'.join(self.url)
    def printurl(self):
        print(self.url)
    def usage(self):
        log.info("Basic usage of this class includes the following kwargs:\n"
                "\tbase: node from which we are pulling (should be supplied)\n"
                "\ttarget: node we are looking for\n"
                "\tget: thing we want: node (default)/'text'/attribute name\n"
                "Below here implies an entry node:\n"
                "\tguid: id used to identify a lift entry\n"
                "\tlxform: form to find in lexeme form fields\n"
                "\tlcform: form to find in citation form fields\n"
                "\tmorphtype: type of morpheme (stem, affix, etc)\n"
                "\tpronunciation: form to find in pronunciation form fields\n"
                "Below here implies a sense node:\n"
                "\tsenseid: id used to identify a lift sense\n"
                "\tdefinition: definition of sense\n"
                "\tgloss: gloss (one word definition) of sense\n"
                "Below here implies an example node:\n"
                "\ttranslation: Translation of example forms\n"
                "\ttonevalue: value of an example tone group (from sorting)\n"
                ""
                )
    def shouldshow(self,node):
        c=self.getfamilyof(node,x=[])
        # This fn is not called by showtargetinhighestgeneration or maketarget
        if node == self.targethead: #do this later
            log.debug("skipping node {}, in target:{}".format(node,self.target))
            return False #not self.targetlastsibling()
        elif self.attrneeds(node,c):
            return True
        elif self.kwargsneeds(node,c):
            return True
        elif self.pathneeds(node,c):
            return True
        else:
            return False
    def getfamilyof(self,node,x):
        log.debug("running kwargshaschildrenof.gen on '{}'".format(node))
        if type(node) is str:
            node=[node]
        for i in node:
            log.debug("running kwargshaschildrenof.gen on '{}'".format(i))
            if i is not '':
                ii=self.children.get(i,'')
                log.debug("Found '{}' this time!".format(ii))
                if ii is not '':
                    x+=ii
                    self.getfamilyof(ii,x)
        return x
    def pathneeds(self,node,children):
        path=self.path
        log.debug("Path: {}; children: {}".format(path,children))
        if node in path and node not in self.level:
            log.debug("Parent ({}) in path: {}".format(node,path))
            return True
        if children != []:
            childreninpath=set(children) & set(path)
            if childreninpath != set():
                pathnotdone=childreninpath-set(self.level)
                if pathnotdone != set():
                    log.debug("Found descendant of {} in path, which isn't "
                        "already there: {}".format(node, pathnotdone))
                    return True
        return False
    def attrneeds(self,node,children):
        log.debug("looking attr(s) of {} in {}".format([node]+children,
                                                                    self.attrs))
        for n in [node]+children:
            if n in self.attrs:
                log.debug("looking attr(s) of {} in {}".format(n,self.attrs))
                common=set(self.attrs[n])&set(list(self.kwargs)+[self.what])
                if common != set():
                    log.debug("Found attr(s) {} requiring {}".format(common,n))
                    return True
            else:
                log.debug("{} not found in {}".format(n,self.attrs.keys()))
        return False
    def kwargsneeds(self,node,children):
        if node in self.kwargs:
            log.debug("Parent ({}) in kwargs: {}".format(node,self.kwargs))
            return True
        if children != []:
            log.debug("Looking for descendants of {} ({}) in kwargs: {}".format(
                                                node,children,self.kwargs))
            childreninkwargs=set(children) & set(self.kwargs)
            if childreninkwargs != set():
                log.debug("Found descendants of {} in kwargs: {}".format(node,
                                                            childreninkwargs))
                pathnotdone=childreninkwargs-set(self.level)
                if pathnotdone != set():
                    log.debug("Found descendants of {} in kwargs, which aren't "
                                    "already there: ".format(node,pathnotdone))
                    return True
        return False
    def callerfn(self):
        return sys._getframe(2).f_code.co_name #2 gens since this is a fn, too
    def parentsof(self,nodenames):
        log.debug("children: {}".format(self.children.items()))
        log.debug("key pair: {}".format(
                ' '.join([str(x) for x in self.children.items() if nodenames in x[1]])))
        p=[]
        if type(nodenames) != list:
            nodenames=[nodenames]
        for nodename in nodenames:
            i=[x for x,y in self.children.items() if nodename in y]
            i.reverse()
            p+=i
        plist=list(dict.fromkeys(p))
        log.debug("parents of {}: {}".format(nodenames,plist))
        return plist
    def setattrsofnodes(self):
        self.attrs={} #These are atttributes we ask for, which require the field
        self.attrs['entry']=['guid']
        self.attrs['sense']=['senseid']
        self.attrs['tonefield']=['tonevalue']
        self.attrs['locationfield']=['location']
    def setchildren(self):
        """These are the kwargs that imply a field. field names also added to
        ensure that depenents get picked up.
        """
        # use self.alias.get(tag,tag) where needed!
        self.children={}
        self.children['lift']=['entry']
        self.children['entry']=['lexeme','pronunciation','sense',
                                            'citation','morphtype','trait']
        self.children['sense']=['ps','definition','gloss',
                                            'example','field']
        self.children['example']=['form','translation','locationfield',
                                            'tonefield','field']
        self.children['field']=['form']
        self.children['lexeme']=['form']
        self.children['citation']=['form']
        self.children['form']=['text']
        self.children['pronunciation']=['field','trait']
        self.children['translation']=['form']
    def setaliases(self):
        self.alias={}
        self.alias['lexical-unit']='lexeme'
        self.alias['grammatical-info']='ps'
        self.alias['id']='senseid'
    def __init__(self, *args,**kwargs):
        #First, see if this one already exists:
        self.base=kwargs['base']
        if type(kwargs['base']) is Lift:
            self.base=kwargs['base'].nodes
        basename=self.basename=self.base.tag
        super(LiftURL, self).__init__()
        log.debug("LiftURL called with {}".format(kwargs))
        self.kwargs=kwargs
        # base=self.basename=self.kwargs.pop('base','lift') # where do we start?
        target=self.target=self.kwargs.pop('target','entry') # what do we want?
        self.parsetargetlineage()
        self.what=self.kwargs.pop('what','node') #This should always be there
        self.path=kwargs.pop('path',[])
        self.url=[]
        self.level={'cur':0,basename:0}
        self.guid=self.senseid=self.attrdonothing
        self.setchildren()
        self.setaliases()
        self.setattrsofnodes()
        self.bearchildrenof(basename)
        log.debug("Making Target now.")
        self.maketarget()
        self.makeurl()
        log.log(21,"Final URL: {}".format(self.url))
        # self.printurl()
"""Functions I'm using, but not in a class"""
def prettyprint(node):
    # This fn is for seeing the Element contents before writing them (in case of
    # ElementTree errors that aren't otherwise understandable).
    t=0
    def do(node,t):
        for child in node:
            log.info("{}{} {}: {}".format('\t'*t,child.tag,child.attrib,
                "" if child.text is None
                    or set(['\n','\t',' ']).issuperset(child.text)
                    else child.text))
            t=t+1
            do(child,t)
            t=t-1
    do(node,t)
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
def another():
    #This should be a class, constructed...
    a=attribdict={}
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
                "/lexical-unit/form[@lang='{analang}']"
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
                "/citation/form[@lang='{analang}']"
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
    a['definitionnode']={
        'cm': 'use to get definition nodes of entries',
        'url':(("entry[@guid='{guid}']"
                "/sense[@id='{senseid}']"
                "/grammatical-info[@value='{ps}']/.."
                "/definition"
                "/form[@lang='{glosslang}']"
                ),['guid','senseid','ps','glosslang']),
        'attr':'node'}
    a['definition']={
        'cm': 'use to get definitions of entries',
        'url':(("entry[@guid='{guid}']"
                "/sense[@id='{senseid}']"
                "/grammatical-info[@value='{ps}']/.."
                "/definition"
                "/form[@lang='{glosslang}']/text"
                ),['guid','senseid','ps','glosslang']),
        'attr':'nodetext'}
    a['glossnode']={
        'cm': 'use to get gloss nodes',
        'url':(("entry[@guid='{guid}']"
                "/sense[@id='{senseid}']"
                "/grammatical-info[@value='{ps}']/.."
                "/gloss[@lang='{glosslang}']"
                ),['guid','senseid','ps','glosslang']),
        'attr':'node'}
    a['gloss']={
        'cm': 'use to get glosses of entries',
        'url':(("entry[@guid='{guid}']"
                "/sense[@id='{senseid}']"
                "/grammatical-info[@value='{ps}']/.."
                "/gloss[@lang='{glosslang}']/text"
                ),['guid','senseid','ps','glosslang']),
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
    a['exfieldvaluenode']={
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
        'attr':'node'}
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
    #URLs for sense nodes:
    a['senselocations']={
        'cm': 'use to get location of fields at the example level, for a '
                'given sense',
        'url':(("example"
                "/field[@type='location']"
                "/form[@lang='{glosslang}']/text"
                ),['glosslang']),
        'attr':'text'}
    a['examplewfieldlocvaluefromsense']={
        'cm': 'use to get an example with a given tone/exfield '
                            'when you have the sense node.',
        'url':(("example/field[@type='location']"
                    "/form[text='{location}']/../.."
                    "/field[@type='{fieldtype}']"
                    "/form[text='{fieldvalue}']/../.."
                    ),['location','fieldtype','fieldvalue']),
            'attr':'nodetext'}
    #URLs for example nodes:
    a['exampletest']={
        'cm': 'use to get an example with a given tone/exfield '
                            'when you have the sense node.',
        'url':(("field[@type='location']"
                    "/form[text='{location}']/../.."
                    "/field[@type='{fieldtype}']"
                    "/form[text='{fieldvalue}']/../.."
                    ),['location','fieldtype','fieldvalue']),
            'attr':'nodetext'}
    a['glossofexample']={
        'cm': 'use to get glosses/translations of examples',
        'url':(("translation[@type='Frame translation']"
                    "/form[@lang='{glosslang}']/text"
                ),['glosslang']),
        'attr':'nodetext'}
    a['formofexample']={
        'cm': 'use to get analang forms of examples',
        'url':(("form[@lang='{lang}']/text"
                ),['lang']),
        'attr':'nodetext'}
def printurllog():
    log.info('\n'+'\n'.join([str(x)+'\n  '+str(y) for x,y in lift.urls.items()]))
if __name__ == '__main__':
    import time #for testing; remove in production
    # def _(x):
    #     return str(x)
    """To Test:"""
    # loglevel='Debug'
    loglevel='INFO'
    print('loglevel=',loglevel)
    from logsetup import *
    log=logsetup(loglevel)
    # filename="/home/kentr/Assignment/Tools/WeSay/dkx/MazHidi_Lift.lift"
    # filename="/home/kentr/Assignment/Tools/WeSay/gnd/gnd.lift.bak.txt"
    # filename="/home/kentr/Assignment/Tools/WeSay/bfj/bfj.lift"
    # filename="/home/kentr/Assignment/Tools/WeSay/gnd/gnd.lift"
    filename="/home/kentr/Assignment/Tools/WeSay/CAWL_demo/SILCAWL.lift"
    lift=Lift(filename,nsyls=2)
    senseids=["begin_7c6fe6a9-9918-48a8-bc3a-e88e61efa8fa",
            'widen_fceb550d-fc99-40af-a288-0433add4f15',
            'flatten_9fb3d2b4-bc9e-4451-b475-36ee10316e40',
            'swallow_af9c3f8f-71e6-4b9a-805c-f6a148dcab8c',
            'frighten_ecffd944-2861-495f-ae38-e7e9cdad45db',
            'prevent_929504ce-35bb-48fe-ae95-8674a97e625f']
    guids=['dd3c93bb-0019-4dce-8d7d-21c1cb8a6d4d',
        '09926cec-8be1-4f66-964e-4fdd8fa75fdc',
        '2902d6b3-89be-4723-a0bb-97925a905e7f',
        '9ba02d67-3a44-4b7f-8f39-ea8e510df402',
        'eece7037-3d55-45c7-b765-95546e5fccc6']
    locations=['Progressive','Isolation']#,'Progressive','Isolation']
    glosslang='en'
    pss=["Verb","Noun"]
    analang='bfj'
    # b=LiftURL(bob='ḿe',
    #             # guid=guid,
    #             # senseid=senseid,
    #             # location=location,
    #             # glosslang=glosslang,
    #             # ps=ps,
    #             # base='sense',
    #             target="sense",
    #             # tonevalue=3,
    #             )
    # get entries: lift.get("entry")
        # lift.get("entry",what='guid')
    # get senses: lift.get("sense")
        # lift.get("sense",what='id')
    # get *all* pss: lift.get("ps",what='value')
    # Never ask for just the form! give the parent, to get a particular form:
    # lift.get("lexeme/form",what='text')
    # lift.get("example/form",what='text')
    # lift.get("citation/form",what='text')
    # just 1 of each pss: dict.fromkeys(lift.get("ps",what='value'))
    # get tone value: lift.get("text", location=location, path=['tonefield'],
    #                             what='text')
    # for ps in dict.fromkeys(lift.get("ps",what='value')):
    #         log.info(ps)
        # for tonevalue in dict.fromkeys(lift.get('text',path=["tonefield"],what='text')):
        #     log.info(tonevalue)
    # log.info('\n'.join([str(x) for x in lift.urls.items()]))
    # exit()
    def test():
        for fieldvalue in [2,2]:
            for location in locations:
            # # for guid in guids:
                for senseid in ['prevent_929504ce-35bb-48fe-ae95-8674a97e625f']:
                    url=lift.get('example/field/form/text',
                                                path=['location','tonefield'], #get this one first
                                                senseid=senseid,
                                                fieldtype='tone',location=location,
                                                tonevalue=fieldvalue,
                                                # what='node'
                                                ) #'text'
                    exfieldvalue=url.get('text')
                    for e in exfieldvalue:
                        log.info("exfieldvalue: {}".format(e))
                    url_sense=lift.retarget(url,"sense")
                    # Bind lift object to each url object; or can we store
                    # this in a way that allows for non-recursive storage
                    # only of the url object by the lift object?
                    ids=url_sense.get('senseid')
                    log.info("senseids: {}".format(ids))
                    for id in [x for x in ids if x is not None]:
                        log.info("senseid: {}".format(id))
                    url_entry=lift.retarget(url,"entry")
                    idsentry=url_entry.get('guid')
                    for id in [x for x in idsentry if x is not None]:
                        log.info("guid: {}".format(id))

                    # example=lift.get('example',
                    #                             path=['location','tonefield'], #get this one first
                    #                             senseid=senseid,
                    #                             fieldtype='tone',location=location,
                    #                             tonevalue=fieldvalue,
                    #                             what='node')
                    # sense=lift.get('sense',
                    #                             path=['location','tonefield'], #get this one first
                    #                             senseid=senseid,
                    #                             fieldtype='tone',location=location,
                    #                             tonevalue=fieldvalue,
                    #                             what='node')
        return
                # log.info(lift.get("example/form",what='text',ps=ps,#"sense", #target
                #         # tonevalue=tonevalue,
                #         # guid=guid,#
                #         path=['lexeme','tonefield'], senseid=senseid,
                #         # senseid=senseid,
                #         # showurl=True
                #         ))
                # log.info(lift.get("citation/form",what='text',ps=ps,#"sense", #target
                #         # tonevalue=tonevalue,
                #         # guid=guid,#
                #         path=['lexeme','tonefield'], senseid=senseid,
                #         # senseid=senseid,
                #         # showurl=True
                #         ))
            # log.info(lift.get("sense", #target
            #     # guid=guid,
            #     senseid=senseid,
            #     # showurl=True
            #     ))
                # log.info(lift.get("text", #target
                #     ps=ps,# guid=guid,
                #     senseid=senseid,
                #     location=location,
                #     path=['tonefield'],
                #     what='text'
                #     # showurl=True
                #     ))
                # path=['pronunciation'],# senseid=senseid,
                # guid=guid,
                # glosslang=glosslang,
                # ps=ps,
                # base='sense',
                # tonevalue=3,
                # )
    test()
    printurllog()
    quit()
    import timeit
    def timetest():
                times=50
                out1=timeit.timeit(test, number=times)
                print(out1)
    timetest()
    # log.info(lift.urls)
    # lift.write()
    # log.info('\n'.join([str(x) for x in lift.urls.items()]))
    exit()# print('l:',l)
    showurl=True
    for i in l:
        ll=lift.getfrom(i,'example',location="1ss",showurl=showurl)
        if ll != []:
            # print("ll:",ll)
            for ii in ll:
                lll=lift.getfrom(ii,'text',analang='en',
                        path=['example/form'],
                        # exampleform="to begin",
                        what='text',
                        showurl=showurl)
                # print(lll)
                # for iii in lll:
                #     print(iii.text)
                # lllt=lift.getfrom(ii,'text',analang='en',glosslang='fr',
                #                     path='translation',what='text',
                #                     showurl=showurl)
                # if lll != []:
                #     print("lll:",', '.join(lll))
                showurl=False
        # showurl=False
    log.info(lift.urls)
    # log.info("Done with above")
    # fieldtype='tone'
    # fieldvalue='1'
    # for i in l:
    #     r=i.findall("field[@type='location']"
    #             "/form[text='{}']/../.."
    #             "/field[@type='{}']"
    #             "/form[text='{}']/../..".format(location,fieldtype,fieldvalue)
    #             )
    #     for ii in r:
    #         loc=i.find("field[@type='location']/form/text")
    #         val=i.find("field[@type='{}']/form/text".format(fieldtype))
    #         log.info("{}: {}, {}".format(i,loc.text,val.text))
    # print(b.url)
    # print(bb.url)
    exit()
    # senseid='26532c2e-fedf-4111-85d2-75b34ed31dd8'
    senseid='skin (of man)_d56b5a5d-7cbf-49b9-a2dd-24eebb0ae462'
    lift.modverificationnode(senseid,vtype="V",add="another value3",rm="Added value")
    lift.modverificationnode(senseid,vtype="V",rm="another value3",add="another value2")
    lift.modverificationnode(senseid,vtype="V",rm="another value3",add="another value4")
    """Functions to run on a database from time to time"""
    # lift.findduplicateforms()
    # lift.findduplicateexamples()
    # lift.convertalltodecomposed()
    """Careful with this!"""
    # lift.write()
    exit()
