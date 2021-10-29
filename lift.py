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
import collections
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
        backupbits=[filename,'_',
                    datetime.datetime.utcnow().isoformat()[:-16], #once/day
                    '.txt']
        self.backupfilename=''.join(backupbits)
        self.getguids() #sets: self.guids and self.nguids
        self.getsenseids() #sets: self.senseids and self.nsenseids
        log.info("Working on {} with {} entries "
                    "and {} senses".format(filename,self.nguids,self.nsenseids))
        """These three get all possible langs by type"""
        self.glosslangs() #sets: self.glosslangs
        self.analangs() #sets: self.analangs, self.audiolangs
        self.pss=self.pss() #log.info(self.pss)
        """This is very costly on boot time, so this one line is not used:"""
        # self.getguidformstosearch() #sets: self.guidformstosearch[lang][ps]
        self.lcs=self.citations()
        self.lxs=self.lexemes()
        self.locations=self.getlocations()
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
        self.morphtypes=self.getmorphtypes()
        log.info("Language initialization done.")
    def retarget(self,urlobj,target,showurl=False):
        k=self.urlkey(urlobj.kwargs)
        urlobj.kwargs['retarget']=target
        k2=self.urlkey(urlobj.kwargs)
        if k2 not in self.urls:
            self.urls[k2]=copy.deepcopy(urlobj)
            self.urls[k2].retarget(target)
        if showurl:
            log.info("URL for retarget: {}".format(self.urls[k2].url))
        return self.urls[k2]
    def urlkey(self,kwargs):
        kwargscopy=kwargs.copy() #for only differences that change the URL
        kwargscopy.pop('showurl',False)
        k=tuple(sorted([(str(x),str(y)) for (x,y) in kwargscopy.items()]))
        return k
    def get(self, target, node=None, **kwargs):
        """This method calls for a URL object, if it's not already there.
        Followup methods include
            LiftURL.get() on that object: to get the desired text/attr/node
            lift.retarget(): to move from one url to a parent (e.g., the sense
                node containing a found example) before LiftURL.get() again
        get entries: lift.get("entry").get()
            lift.get("entry".get('guid'))
        get senses: lift.get("sense").get()
            lift.get("sense".get('senseid'))
        get *all* pss: lift.get("ps").get('value')
        Never ask for just the form! give the parent, to get a particular form:
        lift.get("lexeme/form").get('text')
        lift.get("example/form").get('text')
        lift.get("example/translation/form").get('text')
        lift.get("citation/form").get('text')
        just 1 of each pss: dict.fromkeys(lift.get("ps").get('value'))
        get tone value (from example):
            lift.get("example/tonefield/form/text",location=location).get('text')
        get tone value (from sense, UF):
        lift.get('tonefield/form/text', senseid=senseid).get('text')
        lift.get('sense/tonefield/form/text', senseid=senseid).get('text')
        location: lift.get('locationfield', senseid=senseid).get('text')
        """
        if node is None:
            node=self.nodes
        what=kwargs.get('what','node')
        path=kwargs.get('path',[])
        if type(path) is not list:
            path=kwargs['path']=[path]
        showurl=kwargs.get('showurl',False)
        kwargs['target']=target # we want target to be kwarg for LiftURL
        k=self.urlkey(kwargs)
        if k not in self.urls:
            self.urls[k]=LiftURL(base=node,**kwargs) #needs base and target to be sensible; attribute?
        else:
            log.info("URL key found, using: {} ({})".format(k,self.urls[k].url))
            if self.urls[k].base == node:
                log.log(4,"Same base {}, moving on.".format(node))
            else:
                log.log(4,"Different base of same tag ({}; {}≠{}), rebasing."
                                    "".format(node.tag,self.urls[k].base,node))
                self.urls[k].rebase(node)
        if showurl:
            log.info("Using URL {}".format(self.urls[k].url))
        return self.urls[k] #These are LiftURL objects
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
        return self.get('entry',senseid=senseid).get()
    def getsensenode(self,senseid,showurl=False):
        return self.get('sense',senseid=senseid).get()[0]
    def addmodexamplefields(self,**kwargs):
        log.info(_("Adding values (in lift.py) : {}").format(kwargs))
        #These should always be there:
        senseid=kwargs.get('senseid')
        location=kwargs.get('location')
        fieldtype=kwargs.get('fieldtype','tone') # needed? ever not 'tone'?
        exfieldvalue=self.get("tonefield", senseid=senseid, location=location
                            ).get('node')
        # Set values for any duplicates, too. Don't leave inconsisted data.
        tonevalue=kwargs.get('fieldvalue') #don't test for this above
        if len(exfieldvalue) > 0:
            for e in exfieldvalue:
                e.text=tonevalue
        else: #If not already there, make it.
            log.info("Didn't find that example already there, creating it...")
            sensenode=self.getsensenode(senseid=senseid)
            if sensenode is None:
                log.info("Sorry, this didn't return a node: {}".format(senseid))
                return
            analang=kwargs.get('analang')
            db=kwargs.get('db') #This an object with values
            forms=db.forms
            glosslangs=db.glosslangs
            p=Node(sensenode, tag='example')
            p.makeformnode(analang,forms[analang])
            """Until I have reason to do otherwise, I'm going to assume these
            fields are being filled in in the glosslang language."""
            fieldgloss=Node(p,'translation',attrib={'type':'Frame translation'})
            for lang in glosslangs:
                if lang in forms:
                    fieldgloss.makeformnode(lang,forms[lang])
            exfieldvalue=p.makefieldnode(fieldtype,glosslangs[0],text=tonevalue,
                                                                gimmetext=True)
            p.makefieldnode('location',glosslangs[0],text=location)
        self.write()
        self.updatemoddatetime(senseid=senseid)
    def forminnode(self,node,value):
        """Returns True if `value` is in *any* text node child of any form child
        of node: [node/'form'/'text' = value] Is this needed?"""
        for f in node.findall('form'):
            for t in f.findall('text'):
                if t.text == value:
                    return True
        return False
    def convertalltodecomposed(self):
        """Do we want/need this? Not using anywhere..."""
        for form in self.nodes.findall('.//form'):
            if form.get('lang') in self.analangs:
                for t in form.findall('.//text'):
                    t.text=rx.makeprecomposed(t.text)
    def findduplicateforms(self):
        """This removes duplicate form nodes in lx or lc nodes, not much point.
        """
        dup=False
        for entry in self.nodes:
            formparents=entry.findall('lexical-unit')+entry.findall('citation')
            for fp in formparents:
                for lang in self.analangs:
                    forms=fp.findall('form[@lang="{}"]'.format(lang))
                    if len(forms) >1:
                        log.info("Found multiple form fields in an entry: {}"
                                "".format([x.find('text').text for x in forms]))
                        dup=True
        if not dup:
            log.info("No duplicate form fields were found in the lexicon.")
    def findduplicateexamples(self):
        dup=False
        senses=self.nodes.findall('entry/sense')
        for sense in senses:
            for l in self.locations:
                examples=sense.findall('example/field[@type="location"]/'
                                        'form[text="{}"]/../..'.format(l)) #'senselocations'
                if len(examples)>1:
                    log.error("Found multiple/duplicate examples (of the same "
                        "location ({}) in the same sense: {})"
                    "".format(l,[x.find('form/text').text for x in examples]))
                    """Before implementing the following, we need a test for
                    presence of audio file link, and different tone values,
                    including which to preserve if different (i.e., not '')"""
                    # for e in examples[1:]:
                    #     sense.remove(e)
                    dup=True
        if dup:
            pass #not yet: self.write()
        else:
            log.info("No duplicate examples (same sense and location) were "
                    "found in the lexicon.")
    def addtoneUF(self,senseid,group,analang,guid=None,showurl=False):
        node=self.get('sense',senseid=senseid).get() #give the sense.
        if node == []:
            log.info("Sorry, this didn't return a node: guid {}; senseid {}"
                                        "".format(guid,senseid))
            return
        t=self.get('field/form/text',node=node[0],ftype='tone').get()
        if t == []:
            p=Node(node[0],'field',attrib={'type':'tone'})
            p.makeformnode(analang,text=group)
        else:
            t[0].text=group
        self.updatemoddatetime(guid=guid,senseid=senseid)
        self.write()
        """<field type="tone">
        <form lang="en"><text>toneinfo for sense.</text></form>
        </field>"""
    def addmediafields(self,node, url,lang, showurl=False):
        """This fuction will add an XML node to the lift tree, like a new
        example field."""
        """The program should know before calling this, that there isn't
        already the relevant node --since it is agnostic of what is already
        there."""
        log.info("Adding {} value to {} location".format(url,node))
        possibles=node.findall("form[@lang='{lang}']/text".format(lang=lang))
        for possible in possibles:
            log.debug("Checking possible: {} (index: {})".format(possible,
                                                    possibles.index(possible)))
            if hasattr(possible,'text'):
                if possible.text == url:
                    log.debug("This one is already here; not adding.")
                    return
        form=Node(node,'form',attrib={'lang':lang})
        t=form.maketextnode(text=url)
        prettyprint(node)
        """Can't really do this without knowing what entry or sense I'm in..."""
        self.write()
    def addmodcitationfields(self,entry,langform,lang):
        citation=entry.find('citation')
        if citation is None:
            citation=Node(entry, 'citation')
            citation.makeformnode(lang=lang,text=langform)
    def addpronunciationfields(self,**kwargs):
        """This fuction will add an XML node to the lift tree, like a new
        pronunciation field."""
        """The program should know before calling this, that there isn't
        already the relevant node."""
        guid=kwargs.get('guid',None)
        senseid=kwargs.get('senseid',None)
        if guid is not None:
            node=self.get('entry',guid=guid,showurl=True).get()[0]
        elif senseid is not None:
            node=self.get('entry',senseid=senseid,showurl=True).get()[0]
        analang=kwargs.get('analang')
        glosslang=kwargs.get('glosslang')
        langform=kwargs.get('langform')
        glossform=kwargs.get('glossform')
        fieldtype=kwargs.get('fieldtype','tone')
        fieldvalue=kwargs.get('fieldvalue')
        location=kwargs.get('location')
        p=Node(node, 'pronunciation')
        p.makeformnode(lang=analang,text=langform)
        p.makefieldnode(type=fieldtype,lang=glosslang,text=fieldvalue)
        p.makefieldnode(type='gloss',lang=glosslang,text=glossform)
        p.maketraitnode(type='location',value=location)
        if senseid is not None:
            self.updatemoddatetime(senseid=senseid)
        elif guid is not None:
            self.updatemoddatetime(guid=guid)
        self.write()
        """End here:""" #build up, or down?
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
    def updatemoddatetime(self,guid=None,senseid=None):
        """This updates the fieldvalue, ignorant of current value."""
        if senseid is not None:
            surl=self.get('sense',senseid=senseid) #url object
            for s in surl.get():
                s.attrib['dateModified']=getnow() #node
            eurl=self.get('entry',senseid=senseid) #url object
            for e in eurl.get():
                e.attrib['dateModified']=getnow() #node
        elif guid is not None: #only if no senseid given
            for e in self.get('entry',guid=guid).get():
                e.attrib['dateModified']=getnow()
        self.write()
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
        """These are ordered by frequency in the database"""
        self.audiolangs=[]
        self.analangs=[]
        lxl=self.get('lexeme/form').get('lang')
        lcl=self.get('citation/form').get('lang')
        pronl=self.get('pronunciation/form').get('lang')
        langsbycount=collections.Counter(lxl+lcl+pronl)
        self.analangs=[i[0] for i in langsbycount.most_common()]
        log.info(_("Possible analysis language codes found: {}".format(
                                                                self.analangs)))
        for glang in set(['fr','en']) & set(self.analangs):
            c=langsbycount[glang]
            if 0< c:
                """For Saxwe, and others who have fr or en encoding errors"""
                if c <= 10:
                    log.info("Only {} examples of LWC lang {} found; is this "
                            "correct?".format(c,glang))
        for lang in self.analangs:
            if 'audio' in lang:
                log.debug(_("Audio language {} found.".format(lang)))
                self.audiolangs+=[lang]
                self.analangs.remove(lang)
        if self.audiolangs == []:
            log.debug(_('No audio languages found in Database; creating one '
            'for each analysis language.'))
            for self.analang in self.analangs:
                self.audiolangs+=[f'{self.analang}-Zxxx-x-audio']
        log.info('Audio languages: {}'.format(self.audiolangs))
        log.info('Analysis languages: {}'.format(self.analangs))
    def glosslangs(self):
        """These are ordered by frequency in the database"""
        g=self.get('gloss').get('lang')
        d=self.get('definition/form').get('lang')
        self.glosslangs=[i[0] for i in collections.Counter(g+d).most_common()]
        log.info(_("gloss languages found: {}".format(self.glosslangs)))
    def fields(self,guid=None,lang=None): # all field types in a given entry
        f=list(dict.fromkeys(self.get('field').get('type')))
        return f
    def getlocations(self,guid=None,lang=None): # all field locations in a given entry
        l=list(dict.fromkeys(self.get('example/locationfield').get('text')))
        log.info('Locations found in Examples: {}'.format(l))
        return l
    def getsenseids(self):
        self.senseids=self.get('sense').get('senseid')
        self.nsenseids=len(self.senseids)
    def getguids(self):
        self.guids=self.get('entry').get('guid')
        self.nguids=len(self.guids)
    """Set up"""
    def nc(self):
        nounclasses="1 2 3 4 5 6 7 8 9 10 11 12 13 14"
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
        x['ʔ']=['ʔ',
                "ꞌ", #Latin Small Letter Saltillo
                "'", #Tag Apostrophe
                'ʼ'  #modifier letter apostrophe
                ]
        x['G']=['ẅ','y','Y','w','W']
        x['N']=["ng'",'mm','ŋŋ','m','M','N','n','ŋ','ɲ'] #no longer:'ny',
        """Non-Nasal/Glide Sonorants"""
        x['S']=['l','r']
        x['Sdg']=['rh','wh']
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
                log.debug('Actual Segments found [{}][{}]: {}'.format(lang,stype,
                                                str(self.s[lang][stype])))
        log.info('Actual Segments found: {}'.format(self.s))
    def slists(self):
        self.segmentsnotinregexes={}
        self.clist()
    # def getformstosearch(self):
    #     """This outputs a dictionary of form {analang: {guid:form}*}*, where
    #     form is citation if available, or else lexeme. This is to be flexible
    #     for entries in process of analysis, and to have a dictionary to check
    #     with regexes for output."""
    #     fts={}
    #     for lang in self.analangs:
    #         fts[lang]={} #This will erase all previous data!!
    #         for ps in self.pss+[None]: #I need to break this up.
    #             fts[lang][ps]={}
    #             for s in self.get('sense',analang=lang,ps=ps).get('senseid'):
    #                 f=self.citation(senseid=s,analang=lang)
    #                 # if f == []:
    #                 #     f=self.lexeme(senseid=s,analang=lang)
    #                 for fi in f:
    #                     if fi in fts[lang][ps]:
    #                         fts[lang][ps][fi].append(s)
    #                     else:
    #                         fts[lang][ps][fi]=[s]
    #     log.debug("Found the following forms to search: {}".format(
    #                                                         fts))
    #     return fts
    """Get stuff"""
    def gloss(self,**kwargs):
        return self.get('gloss/text', **kwargs).get('text')
    def glosses(self,**kwargs):
        output={} # This produces a dictionary, of forms for each language
        for lang in self.glosslangs:
            kwargs['glosslang']=lang
            output[lang]=self.gloss(**kwargs)#.get('text')
        return output
    def definition(self,**kwargs):
        truncate=kwargs.pop('truncate',False)
        forms=self.get('definition', **kwargs).get('text')
        if truncate:
            forms=[rx.glossifydefn(f) for f in forms]
        return forms
    def definitions(self,**kwargs):
        output={} # This produces a dictionary, of forms for each language
        for lang in self.glosslangs:
            kwargs['glosslang']=lang
            output[lang]=self.definition(**kwargs)
        return output
    def glossordefn(self,**kwargs):
        forms=self.gloss(**kwargs)
        if forms == []:
            log.info("Missing gloss form; looking for definition form.({})"
                    "".format(kwargs))
            kwargs['truncate']=True
            forms=self.definition(**kwargs)
        return forms
    def glossesordefns(self,**kwargs):
        output={} # This produces a dictionary, of forms for each language
        for lang in self.glosslangs:
            kwargs['glosslang']=lang
            output[lang]=self.gloss(**kwargs)
            if output[lang] == []:
                kwargs['truncate']=True
                forms=self.definition(**kwargs)
        return output
    def citationorlexeme(self,**kwargs):
        """This produces a list; specify senseid and analang as you like."""
        output=self.citation(**kwargs)
        if output == []:
            output=self.lexeme(**kwargs)
            log.info("Missing citation form; looking for lexeme form.({})"
                    "".format(kwargs))
        return output
    def citation(self,**kwargs):
        """This produces a list; specify senseid and analang as you like."""
        output=self.get('citation/form/text',**kwargs).get('text')
        return output
    def citations(self,**kwargs):
        output={} # This produces a dictionary, of forms for each language
        for lang in self.analangs:
            kwargs['analang']=lang
            output[lang]=self.citation(**kwargs) #.get('text')
        log.info("Found the following citation forms: {}".format(output))
        return output
    def lexeme(self,**kwargs):
        """This produces a list; specify senseid and analang as you like."""
        output=self.get('lexeme/form/text',**kwargs).get('text')
        return output
    def lexemes(self,**kwargs):
        output={} # This produces a dictionary, of forms for each language.
        for lang in self.analangs:
            kwargs['analang']=lang
            output[lang]=self.lexeme(**kwargs)
        log.info("Found the following lexemes: {}".format(output))
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
            for form in [x for x in self.lcs[lang]+self.lxs[lang]
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
    def ps(self,**kwargs): #get POS values, limited as you like
        return self.get('ps',**kwargs).get('value')
    def pss(self): #get all POS values in the LIFT file
        p=list(dict.fromkeys(self.ps()))
        log.info("Found these ps values: {}".format(p))
        return p
    def getmorphtypes(self): #get all morph-type values in the LIFT file
        m=collections.Counter(self.get('morphtype',showurl=True).get('value')
                                                                ).most_common()
        log.info("Found these morph-type values: {}".format(m))
        return m
        """CONTINUE HERE: Making things work for the new lift.get() paradigm."""
class Node(ET.Element):
    def makefieldnode(self,type,lang,text=None,gimmetext=False):
        n=Node(self,'field',attrib={'type':type})
        nn=n.makeformnode(lang,text,gimmetext=gimmetext)
        if gimmetext:
            return nn
    def makeformnode(self,lang,text=None,gimmetext=False):
        n=Node(self,'form',attrib={'lang':lang})
        nn=n.maketextnode(text,gimmetext=gimmetext) #Node(n,'text')
        if gimmetext:
            return nn
    def maketextnode(self,text=None,gimmetext=False):
        n=Node(self,'text')
        if text is not None:
            n.text=str(text)
        if gimmetext:
            return n.text
    def maketraitnode(self,type,value,gimmenode=False):
        n=Node(self,'trait',attrib={'name':type, 'value':str(value)})
        if gimmenode:
            return n
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
        self.lc=db.citationorlexeme(guid=guid,lang=self.analang)
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
        log.log(4,self.__dict__)
        n=self.base.findall(self.url)
        if n != []:
            log.log(4,"found: {} (x{}), looking for {}".format(n[:1],len(n),what))
        what=self.unalias(what)
        if n == [] or what is None or what == 'node':
            return n
        elif what == 'text':
            r=[i.text for i in n]
            log.log(4,r)
            return r
        else:
            r=[i.get(what) for i in n]
            log.log(4,r)
            return r
    def build(self,tag,liftattr=None,myattr=None,attrs=None):
        buildanother=False
        noseparator=False
        log.log(4,"building {}, @dict:{}, @{}={}, on top of {}".format(tag,
                                attrs,liftattr,myattr, self.currentnodename()))
        b=tag
        if attrs is None:
            attrs={liftattr: myattr}
        for attr in attrs:
            if (None not in [attr,attrs[attr]] and attrs[attr] in self.kwargs
                                and self.kwargs[attrs[attr]] is not None):
                if "'" in self.kwargs[attrs[attr]]:
                    b+="[@{}=\"{}\"]".format(attr,self.kwargs[attrs[attr]])
                else:
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
        log.log(4,"Path so far: {}".format(self.drafturl()))
        if buildanother:
            self.build(tag)
    def parent(self):
        self.level['cur']-=2 #go up for this and its parent
        self.build("..")
    def entry(self):
        self.build("entry","guid","guid")
        self.bearchildrenof("entry")
    def text(self,value=None):
        self.baselevel()
        self.build("text",myattr=value)
    def form(self,value=None,lang=None):
        self.baselevel()
        self.kwargs['value']=self.kwargs.get(value,None) #location and tonevalue
        log.log(4,"form kwargs: {}".format(self.kwargs))
        self.build("form","lang",lang) #OK if lang is None
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
        # self.form("translationvalue",'glosslang')
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
        """I assume we will never use sense/tonefield and example/tonefield
        in the same url..."""
        self.level['tonefield']=self.level['cur']+1 #so this won't repeat
        self.field()
        if 'tonevalue' in self.kwargs:
            self.kwargs['formtext']='tonevalue'
            self.form("tonevalue",'glosslang')
        else: #dont' force a text node with no text value
            self.kwargs['formtext']=None
            self.form(lang='glosslang')
    def morphtype(self,attrs={}):
        if 'morphtype' in self.kwargs:
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
            log.log(4,"show arg: {}".format(arg))
        if len(args) == 0:
            getattr(self,nodename)()
        else:
            getattr(self,nodename)(*args)
    def formargsbyparent(self,parent):
        args=list()
        if parent in ['gloss', 'definition','translation']:
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
        log.log(4,"bearing children of {} ({})".format(parent,
                                                        self.children[parent]))
        for i in self.children[parent]:
            log.log(4,"bearchildrenof i: {}".format(i))
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
                return
            elif parents.index(target) < len(parents)-1:
                log.log(4,"level {} not in {}; checking the next one...".format(
                                                            target,self.level))
            else:
                log.error("last level {} (of {}) not in {}; this is a problem!"
                            "".format(target,parents,self.level))
                log.error("this is where we're at: {}\n  {}".format(self.kwargs,
                                                            self.drafturl()))
                exit()
    def maybeshowtarget(self,parent):
        # parent here is a node ancestor to the current origin, which may
        # or may not be an ancestor of targethead. If it is, show it.
        f=self.getfamilyof(parent,x=[])
        log.log(4,"Maybeshowtarget: {} (family: {})".format(parent,f))
        if self.targethead in f:
            if parent in self.level:
                log.log(4,"Maybeshowtarget: leveling up to {}".format(parent))
                self.levelup(parent)
            else:
                log.log(4,"Maybeshowtarget: showing {}".format(parent))
                self.show(parent)
            self.showtargetinhighestdecendance(parent)
            return True
    def showtargetinlowestancestry(self,nodename):
        log.log(4,"Running showtargetinlowestancestry for {}/{} on {}".format(
                                    self.targethead,self.targettail,nodename))
        #If were still empty at this point, just do the target if we can
        if nodename == [] and self.targethead in self.children[self.basename]:
            self.show(self.targethead)
            return
        gen=nodename
        g=1
        r=giveup=False
        while not r and giveup is False:
            log.log(4,"Trying generation {}".format(g))
            gen=self.parentsof(gen)
            for p in gen:
                r=self.maybeshowtarget(p)
                if r:
                    break
            g+=1
            if g>10:
                giveup=True
        if giveup is True:
            log.error("Hey, I've looked back {} generations, and I don't see "
                    "an ancestor of {} (target) which is also an ancestor of "
                    "{} (current node).".format(g,self.targethead,nodename))
    def showtargetinhighestdecendance(self,nodename):
        log.log(4,"Running showtargetinhighestdecendance for {} on {}".format(
                                                    self.targethead,nodename))
        if nodename in self.children:
            children=self.children[nodename]
        else:
            log.log(4,"Node {} has no children, so not looking further for "
                        "descendance.".format(nodename))
            return
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
        gggrandchildren=[i for child in children
                                if child in self.children
                                for grandchild in self.children[child]
                                    if grandchild in self.children
                                    for ggrandchild in self.children[grandchild]
                                        if ggrandchild in self.children
                                        for i in self.children[ggrandchild]
                                    ]
        log.log(4,"Looking for {} in children of {}: {}".format(
                                            self.targethead,nodename,children))
        log.log(4,"Grandchildren of {}: {}".format(nodename,grandchildren))
        log.log(4,"Greatgrandchildren of {}: {}".format(
                                                nodename,greatgrandchildren))
        if self.targethead in children:
            log.log(4,"Showing '{}', child of {}".format(self.targethead,nodename))
            self.show(self.targethead,nodename)
        elif self.targethead in grandchildren:
            log.log(4,"Found target ({}) in grandchildren of {}: {}".format(
                        self.targethead,nodename,grandchildren))
            for c in children:
                if c in self.children and self.targethead in self.children[c]:
                    log.log(4,"Showing '{}', nearest ancenstor".format(c))
                    self.show(c,nodename) #others will get picked up below
                    self.showtargetinhighestdecendance(c)
        elif self.targethead in greatgrandchildren:
            log.log(4,"Found target ({}) in gr8grandchildren of {}: {}".format(
                                self.targethead,nodename,greatgrandchildren))
            for c in children:
                for cc in grandchildren:
                    if cc in self.children and self.targethead in self.children[cc]:
                        log.log(4,"Showing '{}', nearest ancenstor".format(c))
                        self.show(c,nodename) #others will get picked up below
                        self.showtargetinhighestdecendance(c)
        elif self.targethead in gggrandchildren:
            log.log(4,"Found target ({}) in gggrandchildren of {}: {}".format(
                                self.targethead,nodename,gggrandchildren))
            for c in children:
                for cc in grandchildren:
                    for ccc in greatgrandchildren:
                        if ccc in self.children and self.targethead in self.children[ccc]:
                            log.log(4,"Showing '{}', nearest ancenstor".format(c))
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
            log.log(4,"{} : {}".format(self.target,self.targetbits))
            self.targethead=self.targetbits[0]
            self.targettail=self.targetbits[1:]
        else:
            self.targethead=self.target
            self.targetbits=[self.targethead,]
            self.targettail=[]
        if 'form' in self.targethead and 'form' not in self.children[
                                                self.getalias(self.basename)]:
            log.error("Looking for {} as the head of a target is going to "
            "cause problems, as it appears in too many places, and is likely "
            "to not give the desired results. Fix this, and try again. (whole "
            "target: {})".format(self.targethead,self.target))
            exit()
    def tagonly(self,nodename):
        return nodename.split('[')[0]
    def currentnodename(self):
        last=self.url[-1:]
        if len(last)>0:
            n=self.tagonly(last[0])
            return self.getalias(n)
    def unalias(self,nodename):
        """This returns the names used in the LIFT file"""
        if nodename in self.alias.values():
            for k in self.alias:
                if self.alias[k] == nodename:
                    return k
        return nodename #else
    def getalias(self,nodename):
        """This returns the names I typically use"""
        return self.alias.get(nodename,nodename)
    def rebase(self,rebase):
        """This just changes the node set from which the url draws.
        because different bases (within the whole lift file) would result in
        the same URL, but not the same data, we need to tell this object which
        base (e.g. which example) to take data from. This method should *not*
        change type of base (e.g. from example to sense); that is for retarget.
        """
        self.base=rebase
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
        log.log(4,"URL (before {} target): {}".format(self.target,self.drafturl()))
        if self.getalias(self.targethead) not in self.level: #If the target hasn't been made yet.
            log.log(4,self.url)
            i=self.currentnodename()
            log.log(4,"URL base: {}; i: {}".format(self.basename,i))
            if i is None: #if it is, skip down in any case.
                i=self.basename
            log.log(4,"URL bit list: {}; i: {}".format(self.url,i))
            if type(i) == list:
                i=i[0] #This should be a string
            f=self.getfamilyof(i,x=[])
            log.log(4,"Target: {}; {} family: {}".format(self.targethead,i,f))
            if self.targethead in f:
                self.showtargetinhighestdecendance(i) #should get targethead
                    # return #only do this for the first you find (last placed).
            else:#Continue here if target not a current level node decendent:
                self.showtargetinlowestancestry(i)
            # Either way, we finish by making the target tail, and leveling up.
        if self.targettail is not None:
            log.log(4,"Adding targettail {} to url: {}".format(self.targettail,
            self.drafturl()))
            for b in self.targettail:
                log.log(4,"Adding targetbit {} to url: {}".format(b,self.drafturl()))
                n=self.targetbits.index(b)
                bp=self.tagonly(self.targetbits[n-1]) #.split('[')[0]#just the node, not attrs
                afterbp=self.drafturl().split(self.unalias(bp))
                log.log(4,"b: {}; bp: {}; afterbp: {}".format(b,bp,afterbp))
                    log.log(4,"showing target element {}: {} (of {})".format(n,b,bp))
                if len(afterbp) <=1 or b not in afterbp[-1]:
                    log.log(4,"showing target element {}: {} (of {})".format(n,b,bp))
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
        if node in self.level:
            return False
        elif node == self.targethead: #do this later
            return False
        elif self.attrneeds(node,c):
            return True
        elif self.kwargsneeds(node,c):
            return True
        elif self.pathneeds(node,c):
            return True
        else:
            return False
    def getfamilyof(self,node,x):
        log.log(4,"running kwargshaschildrenof.gen on '{}'".format(node))
        if type(node) is str:
            node=[node]
        for i in node:
            log.log(4,"running kwargshaschildrenof.gen on '{}'".format(i))
            if i is not '':
                ii=self.children.get(i,'')
                log.log(4,"Found '{}' this time!".format(ii))
                if ii is not '':
                    x+=ii
                    self.getfamilyof(ii,x)
        return x
    def pathneeds(self,node,children):
        path=self.path
        log.log(4,"Path: {}; children: {}".format(path,children))
        if node in path and node not in self.level:
            log.log(4,"Parent ({}) in path: {}".format(node,path))
            return True
        if children != []:
            childreninpath=set(children) & set(path)
            if childreninpath != set():
                pathnotdone=childreninpath-set(self.level)
                if pathnotdone != set():
                    log.log(4,"Found descendant of {} in path, which isn't "
                        "already there: {}".format(node, pathnotdone))
                    return True
        return False
    def attrneeds(self,node,children):
        log.log(4,"looking for attr(s) of {} in {}".format([node]+children,
                                                                    self.attrs))
        for n in [node]+children:
            if n in self.attrs:
                log.log(4,"looking for attr(s) of {} in {}".format(n,self.attrs))
                common=set(self.attrs[n])&set(list(self.kwargs)+[self.what])
                if common != set():
                    log.log(4,"Found attr(s) {} requiring {}".format(common,n))
                    return True
            else:
                log.log(4,"{} not found in {}".format(n,self.attrs.keys()))
        return False
    def kwargsneeds(self,node,children):
        if node in self.kwargs:
            log.log(4,"Parent ({}) in kwargs: {}".format(node,self.kwargs))
            return True
        if children != []:
            log.log(4,"Looking for descendants of {} ({}) in kwargs: {}".format(
                                                node,children,self.kwargs))
            childreninkwargs=set(children) & set(self.kwargs)
            if childreninkwargs != set():
                log.log(4,"Found descendants of {} in kwargs: {}".format(node,
                                                            childreninkwargs))
                pathnotdone=childreninkwargs-set(self.level)
                if pathnotdone != set():
                    log.log(4,"Found descendants of {} in kwargs, which aren't "
                                    "already there: ".format(node,pathnotdone))
                    return True
        return False
    def callerfn(self):
        return sys._getframe(2).f_code.co_name #2 gens since this is a fn, too
    def parentsof(self,nodenames):
        log.log(4,"children: {}".format(self.children.items()))
        log.log(4,"key pair: {}".format(
                ' '.join([str(x) for x in self.children.items() if nodenames in x[1]])))
        p=[]
        if type(nodenames) != list:
            nodenames=[nodenames]
        for nodename in nodenames:
            i=[x for x,y in self.children.items() if nodename in y]
            i.reverse()
            p+=i
        plist=list(dict.fromkeys(p))
        log.log(4,"parents of {}: {}".format(nodenames,plist))
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
                                            'example','tonefield','field']
        self.children['example']=['form','translation','locationfield',
                                            'tonefield','field']
        self.children['field']=['form']
        self.children['lexeme']=['form']
        self.children['definition']=['form']
        self.children['citation']=['form']
        self.children['form']=['text']
        self.children['gloss']=['text']
        self.children['pronunciation']=['field','trait','form']
        self.children['translation']=['form']
    def setaliases(self):
        self.alias={}
        self.alias['lexical-unit']='lexeme'
        self.alias['grammatical-info']='ps'
        self.alias['id']='senseid'
        self.alias['ftype']='fieldtype'
        self.alias["field[@type='tone']"]='tonefield'
    def __init__(self, *args,**kwargs):
        self.base=kwargs['base']
        self.setaliases()
        basename=self.basename=self.getalias(self.base.tag)
        super(LiftURL, self).__init__()
        log.info("LiftURL called with {}".format(kwargs))
        self.kwargs=kwargs
        target=self.target=self.kwargs.pop('target','entry') # what do we want?
        self.setchildren()
        self.parsetargetlineage()
        self.what=self.kwargs.pop('what','node') #This should always be there
        self.path=kwargs.pop('path',[])
        self.url=[]
        self.level={'cur':0,basename:0}
        self.guid=self.senseid=self.attrdonothing
        self.setattrsofnodes()
        self.bearchildrenof(basename)
        log.log(4,"Making Target now.")
        self.maketarget()
        self.makeurl()
        log.log(4,"Final URL: {}".format(self.url))
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
def printurllog(lift):
    log.info('\n'+'\n'.join([str(x)+'\n  '+str(y.url) for x,y in lift.urls.items()]))
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
    # filename="/home/kentr/Assignment/Tools/WeSay/bse/SIL CAWL Wushi.lift"
    # filename="/home/kentr/Assignment/Tools/WeSay/bfj/bfj.lift"
    # filename="/home/kentr/Assignment/Tools/WeSay/gnd/gnd.lift"
    # filename="/home/kentr/Assignment/Tools/WeSay/eto/eto.lift"
    # filename="/home/kentr/Assignment/Tools/WeSay/tsp/TdN.lift"
    # filename="/home/kentr/Assignment/Tools/WeSay/eto/eto.lift"
    # filename="/home/kentr/Assignment/Tools/WeSay/bqg/Kusuntu.lift"
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
                                                showurl=True# what='node'
                                                ) #'text'
                    exfieldvalue=url.get('text')
                    for e in exfieldvalue:
                        log.info("exfieldvalue: {}".format(e))
                    url_sense=lift.retarget(url,"sense")
                    # Bind lift object to each url object; or can we store
                    # this in a way that allows for non-recursive storage
                    # only of the url object by the lift object?
                    ids=url_sense.get('senseid')
                    # log.info("senseids: {}".format(ids))
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
    for subcheck in range(5):
        lift.get("sense", location=locations[0], tonevalue=subcheck,
                        path=['tonefield'],showurl=True).get('senseid')
    exit()
    for senseid in senseids:
        exnode=lift.get('example',showurl=True,senseid=senseid,
                        location=locations[1]).get()
        print('exnode:',exnode)
        # if len(exnode)>0:
        prettyprint(exnode)
        for e in exnode:
            # print('e:',e)
            # prettyprint(e)
            audio=lift.get('form/text',node=e,showurl=True,#en-Zxxx-x-audio
                                        analang='en-Zxxx-x-audio').get('text')
        print('audio:',audio)
    exit()
    g=lift.glossordefn(#self,guid,
                                # senseid,
                                analang='en',
                                senseid='continue, resume_d174612b-b3c0-4073-bff0-58fd098252a9',
                                glosslang='fr',glosslang2=None,
                                lang='swh',#forms,
                                # langform="TestForm",
                                # glossform="testgloss",#gloss2form,
                                # fieldtype='tone',
                                # location='Plural',
                                # fieldvalue=45,
                                # ps=None,
                                showurl=True)
                                # lift.write()
                                # analang=kwargs.get('analang')
                                # glosslang=kwargs.get('glosslang')
                                # langform=kwargs.get('langform')
                                # glossform=kwargs.get('glossform')
                                # fieldtype=kwargs.get('fieldtype','tone')
                                # fieldvalue=kwargs.get('fieldvalue')
                                # location=kwargs.get('location')

    print(g)
    for i in g:
        print(i)
    quit()
    import timeit
    def timetest():
                times=50
                out1=timeit.timeit(test, number=times)
                print(out1)
    timetest()
    # log.info(lift.urls)
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
