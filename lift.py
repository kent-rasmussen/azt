#!/usr/bin/env python3
# coding=UTF-8
"""This module controls manipulation of LIFT files and objects"""
""""(Lexical Interchange FormaT), both for reading and writing"""
import logsetup
log=logsetup.getlog(__name__)
# logsetup.setlevel('INFO',log) #for this file
logsetup.setlevel('DEBUG',log) #for this file
log.info(f"Importing {__name__}")
# try:
#     from lxml import etree as ET
#     log.info("using lxml to parse XML")
#     lxml=True
# except:
try: #Allow this module to be used without translation
    _
except NameError:
    def _(x):
        return x
log.info(_("using xml.etree to parse XML"))
lxml=False
# from xmletfns import * # from xml.etree import ElementTree as ET
import xmletfns as et
import xmlfns, file
import sys
import pathlib
import threading
import shutil
import datetime
import re #needed?
import os
import rx
import ast #For string list interpretation
import copy
import collections
import langtags
"""This returns the root node of an ElementTree tree (the entire tree as
nodes), to edit the XML."""
class Object(object):
    pass
# class TreeParsed(object):
#     def __init__(self, lift):
#         self=Tree(lift).parsed
#         log.info(self.glosslang)
#         Tree.__init__(self, db, guid=guid)
class Error(Exception):
    """Base class for exceptions in this module."""
    pass
class BadParseError(Error):
    def __init__(self, filename):
        self.filename = filename
class LiftXML(object): #fns called outside of this class call self.nodes here.
    """This should maybe be subclassed under XML, from xmletfns"""
    """The job of this class is to expose the LIFT XML as python object
    attributes. Nothing more, not thing else, should be done here."""
    def __init__(self, filename, analang=None, tostrip=False):
        # analang is optional because we don't always care (CAWL).
        self.debug=False
        self.filename=filename #lift_file.liftstr()
        self.logfile=filename+".changes"
        self.urls={} #store urls generated
        """Problems reading a valid LIFT file are dealt with in main.py"""
        try:
            self.read() #load and parse the XML file. (Should this go to check?)
        except:
            raise BadParseError(self.filename)
        self.getglosslangs() #sets: self.glosslangs
        if tostrip:
            return #we're done, if this is a template read
        backupbits=[filename,'_',
                    str(datetime.datetime.now(datetime.UTC))[10:], #once/day
                    '.txt']
        self.backupfilename=''.join(backupbits)
        """I should skip some checks in certain cases, like working with the
        CAWL template"""
        self.getanalangs(analang) #sets: self.analangs, self.audiolangs
        self.getentries() #need self.analang by here
        self.getsenses()
        self.getpss() #all ps values, in a prioritized list
        self.slicebyerror()
        self.load_ps_profiles()
        self.slicebyid()
        self.slicebylx()
        self.slicebylc() #1.14s
        #the following should probably replaced by getsenseidsbyps everywhere
        """These three get all possible langs by type"""
        self.legacylangconvert() #update from any old language forms to xyz-x-py
        self.getentrieswanalangdata() #sets: self.(n)entriesw(lexeme|citation)data
        self.getsenseswglosslangdata() #sets: self.nsensesw(gloss|defn)data
        #HERE
        self.getfieldnames() #sets self.fieldnames (of entry)
        self.getsensefieldnames() #sets self.sensefieldnames (fields of sense)
        self.legacyverificationconvert() #data to form nodes (no name changes)
        self.getfieldswsoundfiles() #sets self.nfields & self.nfieldswsoundfiles
        log.info(_("Working on {file} with {nguids} entries, with lexeme data counts: {lex_counts}, "
                   "citation data counts: {citation_counts} and {nsenseids} senses")
                .format(file=filename, nguids=self.nguids, lex_counts=self.nentrieswlexemedata,
                        citation_counts=self.nentrieswcitationdata, nsenseids=self.nsenseids))
        log.info(_("Found gloss data counts: {gloss_counts}, definition counts: {def_counts}")
                .format(gloss_counts=self.nsenseswglossdata, def_counts=self.nsenseswdefndata))
        #This may be superfluous:
        self.getsenseidsbyps() #sets: self.senseidsbyps and self.nsenseidsbyps
        """This is very costly on boot time, so this one line is not used:"""
        # self.getguidformstosearch() #sets: self.guidformstosearch[lang][ps]
        self.lcs=self.citations()
        self.lxs=self.lexemes()
        self.getlocations()
        self.defaults=[ #these are lift related defaults
                    'analang',
                    'glosslangs',
                    'audiolang'
                ]
        self.slists() #sets: self.c self.v, not done with self.segmentsnotinregexes[lang]
        self.extrasegments() #tell me if there's anything not in a V or C regex.
        # self.findduplicateforms()
        self.findduplicateexamples()
        """Think through where this belongs; what classes/functions need it?"""
        self.morphtypes=self.getmorphtypes()
        self.get_audiodir()
        self.get_imgdir()
        self.get_reportdir()
        log.info(_("Language initialization done."))
    def tonelangname(self,machine=False):
        try:
            bits=[self.tonelang]
        except AttributeError:
            bits=[self.analang,langtags.tone_code]
        if machine:
            bits+=[langtags.machine_transcription_code]
        log.info(f"{bits=}")
        return ''.join(bits)
    def audiolangname(self):
        try:
            return self.audiolang
        except AttributeError:
            bits=[self.analang,langtags.audio_code]
            log.info(f"{bits=}")
            return ''.join(bits)
    def phoneticlangname(self,machine=False):
        try:
            bits=[self.phoneticlang]
        except AttributeError:
            bits=[self.analang,langtags.phonetic_code]
        if machine:
            bits+=[langtags.machine_transcription_code]
        log.info(f"{bits=}")
        return ''.join(bits)
    def get_audiodir(self):
        self.lift_home=file.getparent(self.filename)
        self.audiodir=file.getaudiodir(self.lift_home)
        for s in self.senses:
            for fp in list(s.fields.values())+list(s.examples.values()): #dicts
                if self.audiolang in fp.forms:
                    try:
                        filename=fp.textvaluebylang(self.audiolang)
                        totry=file.getdiredurl(self.audiodir,filename)
                        assert file.exists(totry)
                        log.info(_("Found {file_url_totry}; assuming audiodir={audiodir}")
                                .format(file_url_totry=totry, audiodir=self.audiodir))
                        return
                    except:# Exception as e:
                        # log.info(f"Exception: {e}")
                        pass
        log.info(_("No audio found in audiodir={audiodir}, but will put new audio "
                "there; if your audio is elsewhere, fix this.").format(audiodir=self.audiodir))
    def get_imgdir(self):
        self.imgdir=file.getimagesdir(self.lift_home)
        for s in self.senses:
            try:
                totry=file.getdiredurl(self.imgdir,s.illustrationvalue())
                assert file.exists(totry)
                log.info(_("Found {file_url_totry}; assuming imgdir={imgdir}")
                        .format(file_url_totry=totry, imgdir=self.imgdir))
                return
            except:# Exception as e:
                # log.info(f"Exception: {e}")
                pass
        log.info(_("No images found in imgdir={imgdir}, but will put new images "
                "there; if your images are elsewhere, fix this.").format(imgdir=self.imgdir))
    def get_reportdir(self):
        self.reportdir=file.getreportdir(self.lift_home)
    def convert_langtag(self,current_lang,new_lang):
        """This method is only for established databases who need to change
        langauge codes, typically because of an error or underdifferentiated
        code. It will only be available by manual calling in this module, not anywhere in the UI —at least until I can come up with a way to prevent
        its abuse.
        """
        present_langs=[i.get('lang') for i in self.nodes.findall(".//*[@lang]")]
        lang_stats=collections.Counter(present_langs).most_common()
        langs=set(present_langs)
        if current_lang in self.glosslangs:
            log.error(_("‘{lang}’ is a gloss lang! ({langs})!").format(lang=current_lang, langs=self.glosslangs))
            return
        if current_lang == new_lang:
            log.error(_("‘{new}’ is the same as ‘{current}’!")
                .format(new=new_lang, current=current_lang))
            return
        if current_lang not in langs:
            log.error(_("‘{current}’ not in langs={langs}!")
                    .format(current=current_lang, langs=langs))
            return
        if new_lang in langs:
            log.error(_("‘{new}’ already in langs={langs}!")
                    .format(new=new_lang, langs=langs))
            return
        log.info(_("found ‘{current}’, and not ‘{new}’ in langs={langs}.")
                .format(current=current_lang, new=new_lang, langs=langs))
        target_nodes=[i for i in
                            self.nodes.findall(f".//*[@lang='{current_lang}']")]
        for n in target_nodes:
            n.set('lang',new_lang)
        receptor_nodes=[i for i in
                            self.nodes.findall(f".//*[@lang='{new_lang}']")]
        target_nodes=[i for i in
                            self.nodes.findall(f".//*[@lang='{current_lang}']")]
        log.info(_('Found {n} receptor nodes with {lang}.')
                .format(n=len(receptor_nodes), lang=new_lang))
        log.info(_('Found {n} target nodes with {lang}.')
                .format(n=len(target_nodes), lang=current_lang))
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
        lift.get('toneUFfield/form/text', senseid=senseid).get('text')
        lift.get('sense/toneUFfield/form/text', senseid=senseid).get('text')
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
            if showurl:
                log.debug("Calling LiftURL with {}".format(kwargs))
            self.urls[k]=LiftURL(base=node,**kwargs) #needs base and target to be sensible; attribute?
        else:
            log.log(4,"URL key found: {} ({})".format(k,self.urls[k].url))
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
        allguids=list(self.guids)+list(self.senseids)
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
        entry=et.SubElement(self.nodes, 'entry', attrib={
                                'dateCreated':now,
                                'dateModified':now,
                                'guid':guid,
                                'id':(kwargs['form'][analang]+'_'+str(guid))
                                })
        lexicalunit=et.SubElement(entry, 'lexical-unit', attrib={})
        """Just adding citation, not lexeme forms, with this function,
        though we need the lexeme field (above) to be there"""
        # form=et.SubElement(lexicalunit, 'form',
        #                                 attrib={'lang':analang})
        # text=et.SubElement(form, 'text')
        # text.text=kwargs['form'][analang]
        """At some point, I'll want to distinguish between these two"""
        citation=et.SubElement(entry, 'citation', attrib={})
        form=et.SubElement(citation, 'form', attrib={'lang':analang})
        text=et.SubElement(form, 'text')
        text.text=kwargs['form'][analang]
        del kwargs['form'][analang] #because we're done with this.
        sense=et.SubElement(entry, 'sense', attrib={'id':senseid})
        grammaticalinfo=et.SubElement(sense, 'grammatical-info',
                                            attrib={'value':kwargs['ps']})
        definition=et.SubElement(sense, 'definition')
        for glosslang in kwargs['form']: #now just glosslangs
            form=et.SubElement(definition, 'form',
                                attrib={'lang':glosslang})
            text=et.SubElement(form, 'text')
            text.text=kwargs['form'][glosslang]
            gloss=et.SubElement(sense, 'gloss',
                                attrib={'lang':glosslang})
            text=et.SubElement(gloss, 'text')
            text.text=kwargs['form'][glosslang]
        self.write()
        """Since we added a guid and senseid, we want to refresh these"""
        self.getguids()
        self.getsenseids()
        return senseid
    def evaluatenode(self,node):
        if node is None:
            log.info("Sorry, this didn't return a node: {}".format(node))
            return
        if node.text is not None:
            try:
                l=ast.literal_eval(node.text)
            except SyntaxError: #if the literal eval doesn't work, it's a string
                l=node.text
            if type(l) != list: #in case eval worked, but didn't produce a list
                log.log(2,"One item: {}; {}".format(l, type(l)))
                l=[l,]
        else:
            log.log(2,"empty verification list found")
            l=list()
        return l
    """Make this a class!!!"""
    def legacylangconvert(self):
        formnodes=self.nodes.findall(".//form")
        formlangs=set([i.get('lang') for i in formnodes])
        langs=self.analangs+self.glosslangs
        langs=set([i for i in langs if i])
        log.info("looking to convert pylangs for {}".format(langs))
        for lang in langs:
            for flang in pylanglegacy(lang),pylanglegacy2(lang):
                if flang in formlangs:
                    log.info("Found {}; converting to {}".format(flang,
                                                        pylang(lang)))
                    for n in self.nodes.findall(".//form[@lang='{}']"
                                                "".format(flang)):
                        # log.info("{}; {}".format(n.tag,n.attrib))
                        n.set('lang',pylang(lang))
    def modverificationnode(self,senseid,vtype,ftype,analang,**kwargs):
        """I think this is obsolete"""
        # use self.verificationtextvalue(profile,ftype,lang=None,value=None)
        """this node stores a python symbolic representation, specific to an
        analysis language"""
        showurl=kwargs.get('showurl')
        add=kwargs.get('add',None)
        rms=kwargs.get('rms',[])
        addifrmd=kwargs.get('addifrmd',False) #not using this anywhere; point?
        textnode, fieldnode, sensenode=self.addverificationnode(
                                            senseid,vtype,ftype,analang)
        # prettyprint(textnode)
        # prettyprint(fieldnode)
        l=self.evaluatenode(textnode) #this is the python evaluation of textnode
        # log.info("l (before): {}>".format(l))
        # prettyprint(textnode)
        changed=False
        i=len(l)
        for rm in rms:
            if rm != None and rm in l:
                i=l.index(rm) #be ready to replace
                l.remove(rm)
                changed=True
        if (add != None and add not in l #if there, v-if rmd, or not changing
                and (addifrmd == False or changed == True)):
            l.insert(i,add) #put where removed from, if done.
            changed=True
        textnode.text=str(l)
        # log.info("l (after): {}> (changed: {})".format(l,changed))
        # prettyprint(textnode)
        if changed:
            self.updatemoddatetime(senseid=senseid,write=kwargs.get('write'))
        # log.info("Empty node? {}; {}".format(textnode.text,l))
        if not l:
            log.debug("removing empty verification node from this sense")
            sensenode.remove(fieldnode)
        # else:
        #     log.info("Not removing empty node")
    def getverificationnodevaluebyframe(self,senseid,vtype,ftype,analang,frame):
        # use self.verificationtextvalue(profile,ftype,lang=None,value=None)
        raise
        # log.info("{}; {}; {}; {}; {}".format(senseid,vtype,ftype,analang,frame))
        nodes=self.getverificationnode(senseid,vtype,ftype,analang)
        vft=nodes[0] #this is a text node
        l=self.evaluatenode(vft) #this is the python evaluation of vf.text
        # log.info("text: {}; vf: {}".format(l,vf.text))
        values=[]
        if l is not None:
            for field in l:
                # log.info("field value: {}".format(field))
                if frame in field:
                    values.append(field)
        return values
    def legacyverificationconvert(self):
        # This is used only on boot, to categorically convert any fields where
        # text was kept in the field, rather than in a form node
        # start_time=time.time() testing only
        nfixed=0
        # This is used in cases where form@lang wasn't specified, so now we make
        # it up, and trust the user can fix if this is guessed wrong
        try:
            assert self.analang
            lang=pylang(self.analang)
        except (AttributeError,AssertionError):
            return #if there is no analang, there are no legacy fields either
        #any verification field, anywhere:
        allfieldnames=[i.get('type') for i in self.nodes.findall(".//field")]
        fieldnames=[i for i in set(allfieldnames) if i and 'verification' in i]
        for fieldname in fieldnames:
            vf=self.nodes.findall(".//field[@type='{}']".format(fieldname))
            for f in vf:
                if not nodehasform(f):
                    nfixed+=1
                    log.info("Found legacy verification node ({}):"
                                "".format(fieldname))
                    et.prettyprint(f)
                    t=f.text
                    f.text=None
                    Node.makeformnode(f,lang=lang,text=t)
                    log.info("Converted to:")
                    et.prettyprint(f)
        # log.info("Found {} legacy verification nodes in {} seconds".format(
        log.info("Found {} legacy verification nodes".format(
                                                    nfixed,
                                                    # time.time()-start_time)
                                                    ))
    def getverificationnode(self,senseid,vtype,ftype,analang):
        raise
        sensenode=node=self.getsensenode(senseid=senseid)
        if node is None:
            log.info("Sorry, this didn't return a node: {}".format(senseid))
            return
        pylang=pylang(analang)
        vf=sensenode.find("field[@type='{} {} verification']/form[@lang='{}']"
                            "/text/../..".format(vtype,ftype,pylang))
        vft=sensenode.find("field[@type='{} {} verification']/form[@lang='{}']"
                            "/text".format(vtype,ftype,pylang))
        return vft,vf,sensenode #textnode, fieldnode, sensenode
    def addverificationnode(self,senseid,vtype,ftype,analang):
        # use self.verificationtextvalue(profile,ftype,lang=None,value=None)
        raise
        # This no longer accounts for legacy fields, as those should be
        # converted at boot.
        vft,vf,sensenode=self.getverificationnode(senseid,vtype,ftype,analang)
        # log.info("vft: {}, vf: {}, sensenode: {}".format(vft,vf,sensenode))
        # prettyprint(vft)
        # prettyprint(vf)
        t=None #this default will give no text node value
        if not isinstance(vft,et.Element): #only then add fields
            # log.info("Empty vft; adding verification field")
            vf=Node(sensenode, tag='field',
                            attrib={'type':"{} {} verification".format(vtype,
                                                                        ftype)})
            vft=vf.makeformnode(lang=pylang(analang),text=t,gimmetext=True)
        return vft,vf,sensenode #textnode, fieldnode, sensenode
    def getentries(self):
        self.entries=[Entry(self.nodes,i,annotationlang=self.annotationlang)
                            for i in self.nodes
                            if i.tag == 'entry']
        # log.info(f"{len(self.entries)=}")
        self.entries=[i for i in self.entries if len(i.sense)]
        self.nentries=len(self.entries)
        # log.info(f"{self.nentries=}")
    def getsenses(self):
        self.senses=[i for j in self.entries for i in j.senses]
        self.nsenses=len(self.senses)
        # log.info(f"{self.nsenses=}")
    def slicebyid(self):
        self.entrydict={i.guid:i for i in self.entries}
        self.sensedict={i.id:i for i in self.senses}
        self.guids=self.entrydict.keys()
        self.nguids=len(self.guids)
        self.senseids=self.sensedict.keys()
        self.nsenseids=len(self.guids)
    def slicebyps(self):
        #This can be converted to by profile in main.py
        self.entriesbyps={ps:[i for i in self.entries
                                if i.sense.psvalue() == ps
                                ]
                            for ps in self.pss
                            }
        self.sensesbyps={ps:[i for i in self.senses if i.psvalue() == ps]
                            for ps in self.pss
                            }
    def slicebyps_profile(self):
        self.sensesbyps_profile={ps:{profile:[i for i in self.sensesbyps[ps]
                                            if i.cvprofilevalue() == profile]
                                    for profile in {i.cvprofilevalue()
                                                    for i in self.sensesbyps[ps]
                                                    }
                                    }
                                for ps in self.sensesbyps
                                }
        # log.info(f"{self.sensesbyps_profile=}")
    def get_ps_profiles(self):
        """just a set of each profile by ps keys"""
        self.ps_profiles={k:{i.cvprofilevalue() for i in v if i}
                            for k,v in self.sensesbyps.items()
                            }
        # log.info(f"{self.ps_profiles=}")
    def load_ps_profiles(self):
        self.slicebyps()
        self.slicebyps_profile()
        self.get_ps_profiles()
    def annotation_values_by_ps_profile(self):
        # sort out cvt (e.g., V1 is 'V') later
        return {ps:{profile:{check:{v
                            for sense in self.sensesbyps_profile[ps][profile]
                            for c,v in sense.annotationvaluedictbyftypelang(
                                            'lc',self.analang).items()
                            if v
                            if c==check
                                    }
                            for sense in self.sensesbyps_profile[ps][profile]
                            for check in sense.annotationkeysbyftypelang(
                                                    'lc',self.analang)
                            }
                    for profile in self.ps_profiles[ps]
                    if profile
                    }
                for ps in self.ps_profiles
                }
    def verification_values_by_ps_profile(self):
        # sort out cvt (e.g., V1 is 'V') later
        return {ps:{profile:{check:{v for k,v
                                    in {i for j in [
                                    sense.getcvverificationkeys('lc')[1].items()
                                for sense in self.sensesbyps_profile[ps][profile]
                                                    ]
                                    for i in j
                                        }
                                    if k == check
                                    if v
                                    }
                            for check in {i for j in [
                                 sense.getcvverificationkeys('lc')[1].keys()
                            for sense in self.sensesbyps_profile[ps][profile]
                                                    ]
                                        for i in j
                                            }
                            }
                    for profile in self.ps_profiles[ps]
                    # if profile
                    }
                for ps in self.ps_profiles
                }
    def slicebyerror(self):
        keys=set([(i.cawln,', '.join(i.collectionglosses)) for i in self.senses
                    if not i.imgselectiondir
                ])
        errors={k:
                    [i.id for i in self.senses
                            if not i.imgselectiondir
                            if i.cawln == k[0]
                            if ', '.join(i.collectionglosses) == k[1]
                    ]
                for k in keys
                }
        # log.info("Errors ({}): {}".format(len(errors),errors))
        if keys:
            log.info("keys ({}): {}".format(len(keys),list(keys)[:min(len(keys)-1,5)]))
        for cawl,glosses in list(errors)[:min(len(errors),5)]:
            log.error("Neither CAWL line nor English glosses point "
                "to a real directory, so I can't tell which image "
                "directory to use for these senses. "
                "\nFurthermore, I don't have both the line and glosses, "
                "so I can't construct a directory name to write to: "
                "{}-{} ({}): {}"
                "".format(cawl,glosses,len(errors[(cawl,glosses)]),
                errors[(cawl,glosses)][:min(len(errors[(cawl,glosses)]),5)]))
    def slicebylx(self):
        #This can be converted to by profile in main.py
        self.entriesbylx={l:{t:[j for j in self.entries
                                    if t == j.lx.textvaluebylang(l)
                                ]
                            for t in [i.lx.textvaluebylang(l)
                                        for i in self.entries]
                            if t #don't give None keys
                            }
                            for l in self.analangs
                        }
    def slicebylc(self):
        #This can be converted to by profile in main.py
        self.entriesbylc={l:{t:[j for j in self.entries
                                    if t == j.lc.textvaluebylang(l)
                                ]
                            for t in [i.lc.textvaluebylang(l)
                                        for i in self.entries]
                            if t #don't give None keys
                            }
                            for l in self.analangs
                        }
    def slicebypl(self):
        """Is this used? if so, 'Plural' here should be generalized."""
        #This can be converted to by profile in main.py
        self.entriesbypl={l:{t:[j for j in self.entries
                                    if t == j.fieldvalue('Plural',l)
                                ]
                            for t in [i.fieldvalue('Plural',l)
                                        for i in self.entries]
                            }
                            for l in self.analangs
                        }
    def slicebyimp(self):
        """Is this used? if so, .imp should be updated."""
        raise
        #This can be converted to by profile in main.py
        self.entriesbyimp={l:{i.imp.textvaluebylang(l):i}
                            for i in self.entries
                            if hasattr(i,'imp')
                            for l in self.analangs
                            if l in i.imp.forms
                        }
    def slicebyftype(self):
        self.entriesbyftype={f:{l:{i.fields[f].textvaluebylang(lang=l):i}}
                            for i in self.entries
                            for f in i.fields
                            for l in self.analangs
                            if l in i.fields[f].forms
                            }
        self.sensesbyftype={f:{l:{t:[i for i in self.senses
                                    if f in i.fields
                                    if t == i.fields[f].textvaluebylang(l)
                                    ]
                                }}
                            for i in self.senses
                            for f in i.fields
                            for l in self.analangs
                            if l in i.fields[f].forms
                            for t in [i.fields[f].textvaluebylang(l)]
                            }
        # log.info("senses: {}".format(self.senses))
        # log.info("nsenses: {}".format(len(self.senses)))
    def getentrynode(self,**kwargs):
        if not kwargs:
            return self.entries #these are class Entry
        else:
            return self.get('entry',**kwargs).get() #these are not
    def getsensenode(self,**kwargs):
        # log.info("senseid: {}".format(senseid))
        x=self.get('sense',**kwargs,
                    # showurl=True
                    ).get()
        # log.info("x: {}".format(x))
        if x:
            return x[0]
    def addmodexamplefields(self,**kwargs):
        """WRONG: framed now contains a dictionary for analang, to store different
        forms for lx, lc, pl and imp. So we need to find that (only) by
        framed.framed[analang][ftype] glosses are still by
        framed.framed[analang], as those fields are not typically glossed
        independently
        """
        log.info(_("Adding values (in lift.py) : {}").format(kwargs))
        #These should always be there:
        senseid=kwargs.get('senseid')
        location=kwargs.get('location')
        fieldtype=kwargs.get('fieldtype','tone') # needed? ever not 'tone'?
        oldtonevalue=kwargs.get('oldfieldvalue',None)
        showurl=kwargs.get('showurl',False)
        # ftype=kwargs.get('ftype')
        if not oldtonevalue:
            exfieldvalue=self.get("example/tonefield/form/text",
                                senseid=senseid,
                                location=location,
                                showurl=showurl
                                ).get('node')
        else:
            exfieldvalue=self.get("example/tonefield/form/text",
                            senseid=senseid,
                            tonevalue=oldtonevalue, #to clear just "NA" values
                            showurl=showurl,
                            location=location
                                ).get('node')
            # Set values for any duplicates, too. Don't leave inconsisted data.
        tonevalue=kwargs.get('fieldvalue') #don't test for this above
        analang=kwargs.get('analang')
        write=kwargs.get('write',False)
        framed=kwargs.get('framed',None)
        if framed:
            forms=framed.framed #because this should always be framed, with correct form
            glosslangs=framed.glosslangs
        if exfieldvalue:
            for e in exfieldvalue:
                e.text=tonevalue
            # If we modify the tone value, check for form and gloss conformity:
            if framed: #if it's specified, that is...
                formvaluenode=self.get("example/form/text", senseid=senseid,
                    analang=analang, location=location, showurl=True).get('node')
                if formvaluenode:
                    formvaluenode=formvaluenode[0]
                    if forms[analang] != formvaluenode.text:
                        log.debug("Form changed! ({}≠{})".format(
                                                        forms[analang],
                                                        formvaluenode.text))
                        formvaluenode.text=forms[analang]
                elif analang in forms:
                    log.error("Found example with tone value field, but no form "
                            "field? ({}-{}); adding".format(senseid,location))
                    example=self.get("example", senseid=senseid,
                        location=location, showurl=True).get('node')
                    Node.makeformnode(example[0],analang,forms[analang])
                glossesnode=self.get("example/translation",
                                    senseid=senseid,
                                    location=location,
                                    showurl=showurl
                                    ).get('node')
                #If the glosslang data isn't all provided, ignore it.
                for lang in [g for g in glosslangs if g in forms and forms[g]]:
                    glossvaluenode=self.get("form/text",
                                node=glossesnode[0], senseid=senseid,
                                glosslang=lang,
                                location=location,
                                showurl=showurl
                                ).get('node')
                    log.debug("glossvaluenode: {}".format(glossvaluenode))
                    if glossvaluenode:
                        glossvaluenode=glossvaluenode[0]
                        if forms[lang] != glossvaluenode.text:
                            log.debug("Gloss changed! ({}≠{})".format(forms[lang],
                                                            glossvaluenode.text))
                            glossvaluenode.text=forms[lang]
                    elif lang in forms:
                        log.debug("Gloss missing for lang {}; adding".format(lang))
                        Node.makeformnode(glossesnode[0],lang,forms[lang])
        elif not framed:
            log.error("No node found, nor form info provided! {}-{}"
                        "".format(senseid,location))
        else: #If not already there, make it.
            log.info("Didn't find that example already there, creating it...")
            sensenode=self.getsensenode(senseid=senseid)
            if sensenode is None:
                log.info("Sorry, this didn't return a node: {}".format(senseid))
                return
            attrib={'source': 'AZT sort on {}'.format(getnow())}
            p=Node(sensenode, tag='example', attrib=attrib)
            p.makeformnode(analang,forms[analang])
            """Until I have reason to do otherwise, I'm going to assume these
            fields are being filled in in the glosslang language."""
            fieldgloss=Node(p,tag='translation',attrib={'type':'Frame translation'})
            for lang in glosslangs:
                if lang in forms:
                    fieldgloss.makeformnode(lang,forms[lang])
            exfieldvalue=p.makefieldnode(fieldtype,glosslangs[0],text=tonevalue,
                                                                gimmetext=True)
            p.makefieldnode('location',glosslangs[0],text=location)
        if write:
            self.write()
        self.updatemoddatetime(senseid=senseid,write=write)
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
        def noninteger(x):
            try:
                int(x)
            except (ValueError,TypeError):
                return x
        emptytextnode=EmptyTextNodePlaceholder()
        dup=False
        senses=self.nodes.findall('entry/sense')
        for sense in senses:
            t = threading.Thread(target=self.findduplicateexample,
                            args=(sense,noninteger,emptytextnode))
            t.start()
    def findduplicateexample(self,sense,noninteger,emptytextnode):
        senseid=sense.get('id')
        for l in self.locations:
            examples=sense.findall('example/field[@type="location"]/'
                                    'form[text="{}"]/../..'.format(l)) #'senselocations'
            if len(examples)>1:
                log.error("Found multiple/duplicate examples (of the same "
                    "location ({}) in the same sense ({}): {})"
                "".format(l,senseid,[
                    x.findall('form[@lang="{}"]/text'.format(lang)).text
                        for x in examples
                        for lang in self.analangs
                        if len(x.find('form[@lang="{}"]/text'.format(lang)))]))
                """Before implementing the following, we need a test for
                presence of audio file link, and different tone values,
                including which to preserve if different (i.e., not '')"""
                # for e in examples[1:]:
                #     sense.remove(e)
                dup=True
                nodes={}
                uniq={}
                first={}
                langs=self.analangs+self.glosslangs
                for n in self.analangs:
                    nodes['al-'+n]=[]
                for n in self.glosslangs:
                    nodes['gl-'+n]=[]
                for n in ['value']:
                    nodes[n]=[]
                for example in examples:
                    for lang in self.analangs:
                        # log.info("looking for {} (analang) data".format(lang))
                        l=example.findall("form[@lang='{}']/text"
                                            "".format(lang))
                        """I actually don't want data from alternate analangs.
                        A→Z+T should be producing examples with exactly
                        one analang (at least for now), so if I find one
                        here, that should be good."""
                        # if not l:
                        #     log.info("empty node found for {}".format(lang))
                        #     l=[emptytextnode] #must distinguish empty/missing nodes
                        nodes['al-'+lang].extend(l)
                    for lang in self.glosslangs:
                        # log.info("looking for {} (glosslang) data".format(lang))
                        g=example.findall("translation/form[@lang='{}']"
                                        "/text".format(lang))
                        if not g:
                            # log.info("No text node found for {}".format(lang))
                            g=[emptytextnode]
                        for gi in g:
                            # if gi.text and ('‘' in gi.text or '’' in gi.text):
                                gi.text=rx.stripquotes(gi.text)
                        nodes['gl-'+lang].extend(g)
                    #This should ultimately have [@lang='{}'].analang
                    t=example.findall("field[@type='tone']/form/text")
                    if not t:
                        log.info("empty tone node found")
                        t=[emptytextnode]
                    nodes['value'].extend(t)
                for n in nodes:
                    """Collect all distinct values, not considering
                    missing nodes (None) or values that differ only by
                    initial or final quotes. Notably, i.text as None is
                    allowed, as this is an important difference to track"""
                    uniq[n]=list(set([rx.stripquotes(textornone(i))
                                        for i in nodes[n]
                                        if i is not None]))
                if [n for n in uniq if len(uniq[n]) >1]: #any multiples
                    # if not [l for l in langs if len(uniq[l]) >1]: #nonlang
                    if not [l for l in uniq if len(uniq[l]) >1
                                                if l != 'value']: #nonlang
                        nonint=[noninteger(j) for j in uniq['value'] #nonint
                                            if noninteger(j) is not None]
                        nonnone=[j for j in uniq['value'] #nonint
                                            if j is not None]
                        if not nonint or len(nonint) >1:
                            if nonnone and len(nonnone) == 1:
                                """This is where we save an integer tone
                                value, and ditch a None value."""
                                log.info("A single non-None value found: {}"
                                        "".format(nonnone[0]))
                                savevalue=nonnone[0]
                            else:
                                log.info("Sorry, I don't know how to combine "
                                    "these example values: {} ({}) "
                                    "(senseid: {})"
                                    "".format(uniq[n],n,senseid))
                                continue
                        else: #only one noninteger tone value
                            savevalue=nonint[0]
                            log.info("A single non-integer value found: {}"
                                    "".format(nonint[0]))
                        log.info("These examples have the same "
                                    "language data, so we will merge their "
                                    "tone values, if possible. ({})"
                                    "".format(uniq))
                        for example in examples:
                            #This should ultimately have [@lang='{}'].analang
                            l=[i.text for i in example.findall(
                                                'form[@lang="{}"]/text'
                                                ''.format(self.analangs[0]))
                                    if i]
                            url=("field[@type='tone']/form[text='{}']"
                                "".format(savevalue))
                            if not example.find(url):
                                et=example.find(
                                    "field[@type='tone']/form/text"
                                    )
                                if not et:
                                    et=emptytextnode
                                log.info("Removing duplicate ({}) "
                                "example with value: {}"
                                "".format(l, et.text))
                                sense.remove(example)
                            else:
                                log.info("Keeping duplicate ({}) "
                                "example with value: {}".format(l,
                                    savevalue))
                    else:
                        log.info("It looks like we are dealing with "
                            "different language data in the examples, so "
                            "you  will need to resolve this manually: {}"
                            "".format(uniq))
                else:
                    log.info("It looks like all examples have all the same "
                        "values, so we're deleting all but the first: {}"
                        "".format(uniq))
                    for example in examples[1:]:
                        sense.remove(example)
        #     self.write()
        # else:
        # if not dup:
        #     log.info("No duplicate examples (same sense and location) were "
        #             "found in the lexicon.")
    def addtoneUF(self,senseid,group,analang,guid=None,**kwargs):
        showurl=kwargs.get('showurl',False)
        write=kwargs.get('write',True)
        node=self.get('sense',senseid=senseid,showurl=showurl).get()
        if node == []:
            log.info("Sorry, this didn't return a node: guid {}; senseid {}"
                                        "".format(guid,senseid))
            return
        t=self.get('field/form/text',node=node[0],ftype='tone',
                    showurl=showurl
                    ).get()
        if t == []:
            # log.info("No sense level tone field found, making")
            p=Node(node[0],tag='field',attrib={'type':'tone'})
            p.makeformnode(analang,text=group)
        else:
            # log.info("Sense level tone field found ({}), using".format(
            #                                                         t[0].text
            #                                                         ))
            t[0].text=group
        # t=self.get('field/form/text',node=node[0],ftype='tone',
        #             showurl=True
        #             ).get()
        # log.info("Sense level tone field now ‘{}’.".format(t[0].text))
        # prettyprint(node[0])
        self.updatemoddatetime(guid=guid,senseid=senseid,write=write)
        """<field type="tone">
        <form lang="en"><text>toneinfo for sense.</text></form>
        </field>"""
    def addmediafields(self, node, url, lang,**kwargs):
        """This fuction will add an XML node to the lift tree, like a new
        example field."""
        """The program should know before calling this, that there isn't
        already the relevant node --since it is agnostic of what is already
        there."""
        showurl=kwargs.get('showurl',False)
        write=kwargs.get('write',True)
        # log.info("Adding {} value to {} location".format(url,node))
        possibles=node.findall("form[@lang='{lang}']/text".format(lang=lang))
        for possible in possibles:
            # log.info("Checking possible: {} (index: {})".format(possible,
            #                                         possibles.index(possible)))
            if hasattr(possible,'text'):
                if possible.text == url:
                    # log.info("This one is already here; not adding.")
                    return
        form=Node(node,tag='form',attrib={'lang':lang})
        t=form.maketextnode(text=url)
        # prettyprint(node)
        """Can't really do this without knowing what entry or sense I'm in..."""
        if write:
            self.write()
    def addmodcitationfields(self,entry,langform,lang):
        citation=entry.find('citation')
        if citation is None:
            citation=Node(entry, tag='citation')
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
        glosslangs=kwargs.get('glosslangs')
        forms=kwargs.get('framed').forms
        fieldtype=kwargs.get('fieldtype','tone')
        fieldvalue=kwargs.get('fieldvalue')
        location=kwargs.get('location')
        p=Node(node, tag='pronunciation')
        p.makeformnode(lang=analang,text=forms[analang])
        p.makefieldnode(type=fieldtype,lang=glosslangs[0],text=fieldvalue)
        for lang in glosslangs:
            p.makefieldnode(type='gloss',lang=lang,text=forms[lang])
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
    def updatemoddatetime(self,guid=None,senseid=None,write=True):
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
        if write:
            self.write()
    def read(self):
        """this parses the lift file into an entire ElementTree tree,
        for reading or writing the LIFT file."""
        log.info("Reading LIFT file: {}".format(self.filename))
        self.tree,self.nodes=et.readxml(self.filename)
        self.nodes=Lift(self,self.nodes)
        # self.tree=et.parse(self.filename)
        # self.nodes=self.tree.getroot()
        log.info("Done reading LIFT file.")
        """This returns the root node of an ElementTree tree (the entire
        tree as nodes), to edit the XML."""
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
    def writebackup(self):
        self.write(self.backupfilename)
    def write(self,filename=None):
        """This writes changes back to XML."""
        if filename is None:
            filename=self.filename
        # log.info(f"{filename=} ({type(filename)=})")
        write=0
        nodes=self.nodes
        xmlfns.indent(self.nodes)
        tree=et.ElementTree(self.nodes)
        try:
            tmp=filename+'.part'
            if file.exists(tmp):
                file.remove(tmp)
            # log.info(f"{tmp=} ({type(tmp)=})")
            tree.write(tmp, encoding="UTF-8")
            write=True
        except Exception as e:
            error=_("There was a problem writing to partial file: "
                f"{tmp} ({e})")
            log.error(error)
        if write:
            try:
                os.replace(tmp,filename)
                self.write_OK=True
                self.write_error=None
                return
            except:
                error=_("There was a problem writing "
                    f"{pathlib.Path(filename).name} file to " f"{pathlib.Path(filename).parent} "
                    "directory. This is what's here: "
                    f"{os.listdir(pathlib.Path(filename).parent)}")
                log.error(error)
        self.write_OK=False
        self.write_error=error
    def getanalangs(self,analang=None):
        """These are ordered by frequency in the database"""
        def e_pluribus_unum(langtype):
            langtypepl=langtype+'s'
            if len(getattr(self,langtypepl)) == 1:
                setattr(self,langtype,getattr(self,langtypepl)[0])
                log.info(f'One {langtype} found: {getattr(self,langtype)}')
            elif (hasattr(self,'analang') and
                    self.analang+codes[langtypepl] in getattr(self,langtypepl)):
                setattr(self,langtype,self.analang+codes[langtypepl])
            else:
                log.info(f'Multiple/no {langtypepl}: {getattr(self,langtypepl)}')
                setattr(self,langtype,None)#fix this later, but have attr
        langs=[i.get('lang') for i in self.nodes.findall('entry/citation/form'
                                    )+self.nodes.findall('entry/lexical-unit/form'
                                    )+self.nodes.findall('entry/pronunciation/form')]
        codes={'audiolangs':langtags.audio_code,
            'phoneticlangs':langtags.phonetic_code,
            'tonelangs':langtags.tone_code,
            'machine':langtags.machine_transcription_code
        }
        l_ordered=[i[0] for i in collections.Counter(langs).most_common()] #tups
        # log.info(f"Found these languages in lc/lx/ph fields: {l_ordered} ({len(langs)})")
        for l in ['audiolangs','tonelangs','phoneticlangs']:
            setattr(self,l,[i for i in l_ordered if codes[l] in i
                                                and codes['machine'] not in i])
            l_ordered=[i for i in l_ordered if i not in getattr(self,l)]
        self.analangs=[i for i in l_ordered if langtags.tag_is_valid(i)
                                            and codes['machine'] not in i]
        l_ordered=[i for i in l_ordered if i not in self.analangs]
        tryname=file.getfilenamebase(self.filename)
        if analang in self.analangs:
            log.info(_("Using analang={analang} from settings.").format(analang=analang))
            self.analangs=[analang]
        elif tryname in self.analangs:
            log.info(_("Found file name base in possible analysis languages; "
                    "assuming that and moving on. To select another "
                    "analysis language for this database, change it in the "
                    "settings."))
            self.analangs=[tryname]
        elif not self.analangs:
            if langtags.tag_is_valid(tryname):
                log.info(_("No language data yet: extrapolating analysis "
                    f"language from file name ({tryname})."))
                self.analangs=[tryname]
        else:
            log.error("I can't find a plausible analang! "
                        f"(from ‘{l_ordered}’)")
        # log.info(_("Possible analysis language codes found: {langs}").format(langs=self.analangs))
        for glang in set(['fr','en']) & set(self.analangs):
            log.info(f"Examples of LWC lang {glang} found; is this correct?")
        e_pluribus_unum('analang')
        for l in ['audiolangs','tonelangs','phoneticlangs']:
            if not getattr(self,l):
                log.debug(_('No {lang} found in Database; creating one '
                        'from settings.').format(lang=l))
                setattr(self,l,[i+codes[l] for i in getattr(self,'analangs')])
            elif self.analang and self.analang+codes[l] not in getattr(self,l):
                getattr(self,l).append(self.analang+codes[l])
        for l in ['audiolang','tonelang','phoneticlang']:
            e_pluribus_unum(l)
        if l_ordered:
            log.error(_("Language codes {langs} found in data, "
                        "but not in settings. Check your settings!")
                    .format(langs=l_ordered))
    def getglosslangs(self):
        """These are ordered by frequency in the database"""
        g=self.get('gloss').get('lang')
        d=self.get('definition/form').get('lang')
        self.glosslangs=[i[0] for i in collections.Counter(g+d).most_common()]
        log.info(_("gloss languages found: {langs}").format(langs=self.glosslangs))
        self.annotationlang=self.glosslangs[0]
        log.info(_("Using first gloss language for new annotations: {lang}").format(lang=self.glosslangs[0]))
    def getfieldnames(self,guid=None,lang=None): # all field types in a given entry
        self.fieldnames={l:set([k
                                    for i in self.entries
                                    for k in i.fields
                                    if l in i.fields[k].forms
                                    ])
                                for l in self.analangs+self.glosslangs
                                if [k for i in self.entries #no set()
                                    for k in i.fields
                                    if l in i.fields[k].forms
                                    ]
                                }
        log.info('Fields found in Entries: {}'.format(self.fieldnames))
    def getsensefieldnames(self,guid=None,lang=None): # all field types in a given entry
        self.sensefieldnames={l:set([k
                                    for i in self.senses
                                    for k in i.fields
                                    if l in i.fields[k].forms
                                    if k
                                    ])
                                for i in self.senses
                                for k in i.fields
                                for l in i.fields[k].forms
                                }
        log.info('Fields found in Senses: {}'.format(self.sensefieldnames))
    def getlocations(self,guid=None,lang=None): # all field locations in a given entry
        self.locations=list(dict.fromkeys(self.get('example/locationfield/form/text',
                                                    what='text',
                                                    # showurl=True
                                                    ).get('text')))
        log.info('Locations found in Examples: {}'.format(self.locations))
    def getsenseidsbyps(self,ps=None):
        if ps:
            d=self.get('sense',ps=ps).get('senseid')
            try:
                self.senseidsbyps[ps]=d
            except AttributeError:
                self.senseidsbyps={ps:d}
            nd=len(self.senseidsbyps[ps])
            try:
                self.nsenseidsbyps[ps]=nd
            except AttributeError:
                self.nsenseidsbyps={ps:nd}
            log.info("Found {} senses with lexical category {}".format(
                                                    self.nsenseidsbyps[ps],ps))
        else:
            # start=time.time()
            self.senseidsbyps={ps:self.get('sense',ps=ps).get('senseid')
                                for ps in self.pss}
            self.nsenseidsbyps={ps:len(self.senseidsbyps[ps])
                                for ps in self.senseidsbyps}
            # print(time.time()-start)
    def getsenseids(self):
        self.senseids=[i.id for i in self.senses]
        self.nsenseids=len(self.senseids)
    def getentrieswanalangdata(self):
        #do each of these, then cull
        self.getentrieswlexemedata() #sets: self.(n)entrieswlexemedata
        self.getentrieswcitationdata() #sets: self.(n)entrieswcitationdata
        for lang in self.analangs.copy():
            if (not self.nentrieswlexemedata[lang] and
                not self.nentrieswcitationdata[lang]):
                self.analangs.remove(lang)
            elif not (self.nentrieswlexemedata[lang] > self.nguids/100 or
                        self.nentrieswcitationdata[lang] > self.nguids/100
                    ):
                log.info("Analysis language ˋ{}ˊ appears in in less than "
                        "1% of entries ({}): {} "
                        "".format(lang,
                                    (self.nentrieswcitationdata[lang]+
                                    self.nentrieswlexemedata[lang]),
                                    [i.get('id')
                                    for i in (self.entrieswlexemedata[lang]+
                                            self.entrieswcitationdata[lang])
                                    ],
                                ))
    def getentrieswcitationdata(self):
        self.entrieswcitationdata={lang:[
                                    i for j in self.entriesbylc[lang].values()
                                    for i in j
                                        ]
                                    for lang in self.analangs
                                    }
        self.nentrieswcitationdata={lang:len(self.entrieswcitationdata[lang])
                                    for lang in self.entrieswcitationdata
                                    }
    def getentrieswlexemedata(self):
        self.entrieswlexemedata={lang:[
                                    i for j in self.entriesbylx[lang].values()
                                    for i in j
                                        ]
                                    for lang in self.analangs
                                    }
        self.nentrieswlexemedata={lang:len(self.entrieswlexemedata[lang])
                                    for lang in self.entrieswlexemedata
                                    }
    def getfieldswsoundfiles(self):
        """This is NOT sensitive to sense level fields, which is where we store
        analysis and verification. This should just pick up entry form fields,
        or CAWL numbers, etc, which shouldn't be coded for analang."""
        self.fieldswannotations={}
        self.fieldswsoundfiles={}
        self.nfieldswsoundfiles={}
        self.nfieldswannotations={}
        self.fields={}
        self.nfields={}
        # for l in self.fieldnames:
        #     del self.fieldnames[l] #for testing cases without fields!
        fieldopts={k:k for k in ['sense/example',
                                'citation',
                                'lexical-unit']}
        fieldopts.update(
                            {f:'field[@type="{}"]'.format(f)
                                    for l in self.analangs
                                    if l in self.fieldnames
                                    for f in self.fieldnames[l]
                                    })
        # log.info("fieldopts: {}".format(fieldopts))
        for lang in self.analangs:
            self.fields[lang]={}
            self.fieldswannotations[lang]={}
            # fieldswsoundfiles[lang]={}
            self.nfields[lang]={}
            # self.nfieldswsoundfiles[lang]={}
            self.nfieldswannotations[lang]={}
            for field in fieldopts:
                self.fields[lang][field]=[i for i in
                    self.nodes.findall('entry/{}/form[@lang="{}"]/text'
                                        ''.format(fieldopts[field],lang))
                                        if i.text
                                        ]
                self.nfields[lang][field]=len(self.fields[lang][field])
                self.fieldswannotations[lang][field]=[i for i in
                    self.nodes.findall('entry/{}/form[@lang="{}"]/annotation'
                                        ''.format(fieldopts[field],lang))
                                        if i.get('value')
                                                ]
                self.nfieldswannotations[lang][field]=len(
                                        self.fieldswannotations[lang][field])
        #get actual audiolangs here; relate to analangs elsewhere
        for lang in self.audiolangs:
            self.fieldswsoundfiles[lang]={}
            self.nfieldswsoundfiles[lang]={}
            for field in fieldopts:
                self.fieldswsoundfiles[lang][field]=[i for i in
                    self.nodes.findall('entry/{}/form[@lang="{}"]/text'
                                        ''.format(fieldopts[field],lang))
                                        if i.text
                                                ]
                self.nfieldswsoundfiles[lang][field]=len(self.fieldswsoundfiles
                                                                [lang][field])
                log.info("Found {} fieldswsoundfiles for {}/{}".format(
                            self.nfieldswsoundfiles[lang][field],field,lang))
        # log.info("Found {} fieldswsoundfiles".format(self.nfieldswsoundfiles))
    def report_counts(self):
        # log.info(f"{self.nentrieswcitationdata=}")# in nfields
        # log.info(f"{self.nentrieswlexemedata=}")# in nfields
        if self.analang not in self.nfields:
            log.info(f"{self.analang=} not found in {self.nfields=}")
            return
        counts=self.nfields[self.analang]
        ps_profile_counts={ps:{profile:len(self.sensesbyps_profile[ps][profile])
                                    for profile in self.sensesbyps_profile[ps]
                                } 
                                    for ps in self.sensesbyps_profile 
                                    }
        log.info(f"{self.nfields=} \n"
                f"{counts['Plural']+counts.get('Imperative',0)==counts['lexical-unit']=} \n"
                f"{ps_profile_counts=}")
        return counts,ps_profile_counts
        # log.info(f"{self.nfieldswannotations=}")
    def getsenseswglosslangdata(self):
        #do each of these, then cull in the second one
        self.getsenseswglossdata() #sets: self.nentrieswglossdata
        self.getsenseswdefndata() #sets: self.nentrieswdefndata
        for lang in self.glosslangs.copy():
            if not self.nsenseswdefndata[lang] and (
                                    not self.nsenseswglossdata[lang]):
                self.glosslangs.remove(lang) #do this just once
    def getsenseswglossdata(self):
        senseswglossdata={lang:[
                                i for i in self.senses
                                if i.glossvaluesbylang(lang)
                                ]
                                for lang in self.glosslangs
                            }
        self.nsenseswglossdata={lang:len(senseswglossdata[lang])
                                    for lang in senseswglossdata
                                }
        for lang in [l for l in self.nsenseswglossdata if
                        0 < self.nsenseswglossdata[l] < self.nguids/100]:
                log.info("Glosslang ˋ{}ˊ appears in less than "
                        "1% ({}) of sense glosses: {}"
                        "".format(lang,self.nsenseswglossdata[lang],
                                [i.get('id') for i in senseswglossdata[lang]]
                                    ))
    def getsenseswdefndata(self):
        senseswdefndata={lang: [i for i in self.senses
                                # for lang in self.glosslangs
                                if i.definition.textvaluebylang(lang)
                                ]
                        for lang in self.glosslangs}
        self.nsenseswdefndata={lang:len(senseswdefndata[lang])
                                for lang in senseswdefndata}
        for lang in [l for l in self.nsenseswdefndata if
                        0 < self.nsenseswdefndata[l] < self.nguids/100]:
                log.info("Glosslang ˋ{}ˊ appears in less than "
                        "1% ({}) of sense definitions: {}"
                        "".format(lang,self.nsenseswdefndata[lang],
                                    [i.get('id') for i in senseswdefndata[lang]]
                                    ))
    def getguids(self):
        self.guids=self.get('entry').get('guid')
        self.nguids=len(self.guids)
    def fillentryAwB(self,a,b):
        """This is for filling in a database with SIL CAWL info; it doesn't
        treat lexeme or citation, etc. info, just sense/gloss, CAWL, and
        semantic domain fields."""
        """Nothing (yet?) fancy for testing for each having a node, nor
        combining them; only moves if A node is absent or empty."""
        asense=a.find('sense')
        agloss={}
        """Start by getting info from node A to match against"""
        for n in [i for i in asense if i.tag == 'gloss']:
            lang=n.get('lang')
            agloss[lang]=n.find('text')
            if agloss[lang]:
                agloss[lang]=agloss[lang].text
        """For now, these two are either there or not."""
        asilcawl=asense.find("field[@type='SILCAWL']")
        if isinstance(asilcawl,et.Element):
            asilcawlt=asilcawl.find('form/text').text
        else:
            asilcawlt=EmptyTextNodePlaceholder()
        asdn=asense.find("trait[@name='semantic-domain-ddp4']")
        if isinstance(asdn,et.Element):
            asd=asdn.get('value')
        else:
            asd=None
        """Then test if node B has the more info, and if so, add to A"""
        bsense=b.find('sense')
        for n in [i for i in bsense if i.tag == 'gloss']:
            lang=n.get('lang')
            if n.find('text') and (lang not in agloss or not agloss[lang]):
                asense.append(n) #append the node wholesale, not values.
        bsilcawl=bsense.find("field[@type='SILCAWL']")
        bsilcawlt=bsilcawl.find('form/text').text
        if isinstance(bsilcawl,et.Element): #Should always be, but just to be sure
            if not asilcawlt or bsilcawlt != asilcawlt:
                asense.append(bsilcawl) #copy over if empty or not the same
            #     log.info("yes,")
            # try:
            #     log.info("bsilcawl copied over to asense?: {}/{}".format(
            #     asilcawl.find('form/text').text,
            #     bsilcawl.find('form/text').text
            #     ))
            # except:
            #     log.info("bsilcawl copied over to asense?: {}/{}".format(
            #     asilcawl,
            #     bsilcawl.find('form/text').text
            #     ))
        bsdn=bsense.find("trait[@name='semantic-domain-ddp4']")
        bsd=bsdn.get('value')
        if bsd: #Should always be, but just to be sure
            if not asd or bsd != asd:
                asense.append(bsdn) #copy over if empty or not the same
            #     try:
            #         log.info("bsdn copied over to asense: {}/{}".format(
            #         asdn.get('value'),
            #         bsdn.get('value')
            #         ))
            #     except:
            #         log.info("bsdn copied over to asense: {}/{}".format(
            #         asdn,
            #         bsdn.get('value')
            #         ))
            # else:
            #     log.info("bsdn not copied over to asense: {}/{}".format(
            #     asdn.get('value'),
            #     bsdn.get('value')
            #     ))
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
        # Don't include any profile-legit characters in these variables, or they
        # will get picked up again during the analysis
        c={}
        c['pvd']={}
        c['pvd'][2]=['bh','dh','gh','gb',
                    'bb','dd','gg', 'gu', #French
                    # 'gw','dw', 'ɗw', #gnd
                    'mb','nd','ŋg',
                    'Mb', 'Bw', #tsh
                    ]
        c['pvd'][3]=[
                    # 'ndw', 'ŋgw' #gnd
                    ]
        c['pvd'][1]=['b','B','d','g','ɡ', #,'G' messes with profiles
                    'ག', #/ɡa/
                    'ད', #/da/
                    'བ', #/ba/
                    ]
        c['p']={}
        c['p'][2]=['kk','kp','cc','pp','pt','tt','ck',
                    'qu', #French
                    'mp', 'nt', 'nk', 'ŋk',
                    # 'kw','tw',
                    'Pk','Pw' #tsh
                    'pʰ','tʰ','kʰ','qʰ',
                    'p̚', 't\u031A','k\u031A','q\u031A',#IPA
                    ] #gnd
        c['p'][1]=['p','P','ɓ','Ɓ','t','ɗ','ɖ','c','k','q',
                    'ç', #French
                    'ཀ', #/ka/
                    'ཁ', #/kʰa/
                    'ཏ', #/ta/
                    'ཐ', #/tʰa/
                    'པ', #/pa/
                    'ཕ', #/pʰa/
                    ]
        c['fvd']={}
        c['fvd'][2]=['bh','vh','zh',
                    # 'zw' #gnd
                    ]
        c['fvd'][1]=['j','J','v','z','Z','ʒ','ð','ɣ','ʑ',
                    'ཇ', #/dʒa/
                    'ཛ', #/dza/
                    ] #problems w x?
        c['f']={}
        c['f'][3]=['sch']
        c['f'][2]=['ch','ph','sh','hh','pf','bv','ff','sc','ss','th',
                    # 'hw','sw' #gnd
                    ]
        #Assuming x is voiceless, per IPA and most useage...
        c['f'][1]=['F','f','s','ʃ','θ','x','h', #not 'S'
                    'ɦ','χ','ʂ','ɕ','ʁ','ʑ','ʐ' #IPA
                    'ཞ','ཞ', #/ʒa/
                    'ཟ', #/za/
                    'ར', #/ra/
                    'ལ', #/la/
                    'ཧ', #/ha/
                    'འ', #/ɦa/
                    'ཤ', #/ʃa/
                    'ས', #/sa/
                    'ཡ', #/ja/ #This and the next are here because these are
                    'ཝ', #/wa/ #clearly consonants, in this syllabic form
                ]
        c['avd']={}
        c['avd'][2]=['dj','dz','dʒ','dʐ','dʑ']
        c['avd'][3]=['n'+i for i in c['avd'][2]]
        # c['avd'][3]=['ndz','ndʐ','ndʑ'
        #             # 'dzw' #gnd
        #             ]
        # c['avd'][4]=['ndzw'] #gnd
        c['a']={}
        c['a'][1]=['ཅ', #/tʃa/
                    'ཆ', #/tʃʰa/
                    'ཙ', #/tsa/
                    'ཚ', #/tsʰa/
                    ]
        c['a'][2]=['ts','tʃ','tʂ','tɕ']
        c['a'][3]=['chk','tch']
        c['a'][3].extend([i+'ʰ' for i in c['a'][2]])
        c['a'][3].extend(['n'+i for i in c['a'][2]])
        c['lfvd']={}
        # c['lfvd'][3]=['zlw']
        c['lfvd'][2]=['zl']
        c['lfvd'][1]=['ɮ']
        c['lf']={}
        # c['lf'][3]=['slw']
        c['lf'][2]=['sl']
        c['lf'][1]=['ɬ']
        c['pn']={}
        """If these appear, they should always be single consonants."""
        c['pn'][2]=['ᵐb','ᵐp','ᵐv','ᵐf','ⁿd','ⁿt','ᵑg','ⁿg','ᵑg','ⁿk','ᵑk',
                    'ⁿj','ⁿs','ⁿz',
                ]
        self.hypotheticals=x={} #dict to put all hypothetical segements in, by category
        c['G']={1:['ẅ','y','Y','w','W']}
        c['N']={1:['m','M','n','ŋ','ɲ','ɱ','ɳ',#'N', messed with profiles
                    'ང', #/ŋa/
                    'ན', #/na/
                    'མ', #/ma/
                    'ཉ', #/ɲa/
                    ]}
        c['N'][2]=['mm','ŋŋ','ny','gn','nn']
        c['N'][3]=["ng'"]
        """Non-Nasal/Glide Sonorants"""
        c['S']={1:['l','r']}
        c['S'][2]=['rh','wh','ll','rr',
                    # 'rw','lw' #gnd
                    ]
        for stype in c:
            if stype in ['ʔ','G','N','S']: #'V'?
                consvar=stype
            elif 'vd' in stype:
                consvar='D'
            else:
                consvar='C'
            for nglyphs in [i for i in range(5) if i in c[stype]]:
                for glyph in [i for i in c[stype][nglyphs]
                                if not set(['w','ʷ'])&set(i)
                                ]:
                    try:
                        c[stype][nglyphs+1]+=[glyph+'w']
                    except KeyError:
                        c[stype][nglyphs+1]=[glyph+'w']
            for nglyphs,varsfx in [(4,'qg'),(3,'tg'),(2,'dg'),(1,'')]:
                if c[stype].get(nglyphs):
                    try:
                        x[consvar+varsfx]+=c[stype][nglyphs]
                    except KeyError:
                        x[consvar+varsfx]=c[stype][nglyphs]
        x['ʔ']=['ʔ',
                "ꞌ", #Latin Small Letter Saltillo
                "'", #Tag Apostrophe
                'ʼ'  #modifier letter apostrophe
                ]
        x['V']=[
                #decomposed first:
                #tilde (decomposed):
                'ã', 'ẽ', 'ɛ̃', 'ə̃', 'ɪ̃', 'ĩ', 'õ', 'ɔ̃', 'ũ', 'ʊ̃',
                #Combining Greek Perispomeni (decomposed):
                'a͂', 'i͂', 'o͂', 'u͂',
                #single code point vowels:
                'a', 'e', 'i', 'ə', 'o', 'u',
                'A', 'E', 'I', 'Ə', 'O', 'U',
                'ɑ', 'ɛ', 'ɨ', 'ɔ', 'ʉ', 'ɩ',
                'æ', 'ʌ', 'ɪ', 'ï', 'ö', 'ʊ',
                #for those using precomposed letters:
                'à', 'è', 'ì', 'ò', 'ù',
                'À', 'È', 'Ì', 'Ò', 'Ù',
                'á', 'é', 'í', 'ó', 'ú',
                'Á', 'É', 'Í', 'Ó', 'Ú',
                'â', 'ê', 'î', 'ô', 'û',
                'Â', 'Ê', 'Î', 'Ô', 'Û',
                'ã', 'ẽ', 'ĩ', 'õ', 'ũ',
                'œ','ë', #French
                'ɯ', 'ɤ', 'ˠ', 'ø', #IPA
                'ཨ','ཨ', #/a/
                'ི', #/i/
                'ུ', #/u/
                'ེ', #/e/
                'ོ', #/o/
                ]
        x['Vdg']=['ou','ei','ɨʉ','ai', #requested by bfj
                'óu','éi','ɨ́ʉ','ái',
                'òu','èi','ɨ̀ʉ','ài',
                'yi','yu','yɨ','yʉ', #requested by Jane
                'ai','ea','ou','ay', #For English
                'ee','ei','ey','ie',
                'oa','oo','ow','ue',
                'ai','ei','oe','ae', # for French
                'au','ée','ea','oi',
                'eu','ie','ou',
                ]
        x['Vtg']=['aie','eau']

        x["̀"]=["̀","́","̂","̌","̄","̃"
                , "᷉","̋","̄","̏","̌","̂","᷄","᷅","̌","᷆","᷇","᷉" #from IPA keyboard
                ,"̈" #COMBINING DIAERESIS
                ] #"à","á","â","ǎ","ā","ã"[=́̀̌̂̃ #vowel diacritics
        x['ː']=[":","ː"] # vowel length markers
        x['=']=['=','-','།','་'] #affix boundary markers (incl Tibetan)
        x['.']=['་']
        x['<']=['<','&lt;','&gt;','>','›','»','‹','«','',
                # ';','"','.' #pull these; they shouldn't appear in words
                ] #macron here?
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
                # log.debug('hypotheticals[{}][{}]: {}'.format(lang,stype,
                #                                     str(x[stype])))
                # log.debug('Actual Segments found [{}][{}]: {}'.format(lang,stype,
                #                                 str(self.s[lang][stype])))
        log.info('Actual Segments found: {}'.format(self.s))
    def slists(self):
        self.segmentsnotinregexes={}
        self.clist()
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
        forms=self.get('definition/form/text', **kwargs).get('text')
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
                output[lang]=self.definition(**kwargs)
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
    def citationnode(self,**kwargs):
        """This produces a list; specify senseid and analang as you like."""
        output=self.get('citation',**kwargs).get('node')
        return output
    def citations(self,**kwargs):
        output={} # This produces a dictionary, of forms for each language
        for lang in self.analangs:
            kwargs['analang']=lang
            output[lang]=[i for i in self.citation(**kwargs) if i] #.get('text')
        # log.info("Found the following citation forms: {}".format(output))
        return output
    def lexeme(self,**kwargs):
        """This produces a list; specify senseid and analang as you like."""
        output=self.get('lexeme/form/text',**kwargs).get('text')
        return output
    def lexemenode(self,**kwargs):
        """This produces a list; specify senseid and analang as you like."""
        output=self.get('lexeme',**kwargs).get('node')
        return output
    def lexemes(self,**kwargs):
        output={} # This produces a dictionary, of forms for each language.
        for lang in self.analangs:
            kwargs['analang']=lang
            output[lang]=[i for i in self.lexeme(**kwargs) if i]
        # log.info("Found the following lexemes: {}".format(output))
        return output
    def pronunciationnode(self,**kwargs):
        """This produces a list; specify senseid and analang as you like."""
        output=self.get('pronunciation',**kwargs).get('node')
        return output
    def fieldnode(self,**kwargs):
        """This produces a list; specify senseid and analang as you like."""
        if 'node' in kwargs:
            return [kwargs['node']]
        if 'ftype' not in kwargs or not kwargs['ftype']:
            log.error("I don't know what field you want: {}".format(kwargs))
            return []
        elif kwargs['ftype'] == 'lc':
            return self.citationnode(**kwargs)
        elif kwargs['ftype'] == 'lx':
            return self.lexemenode(**kwargs)
        elif kwargs['ftype'] == 'ph':
            return self.pronunciationnode(**kwargs)
        if 'floc' not in kwargs:
            log.error("I don't know where the field should be (floc should be "
                "either 'sense' or 'entry'; assuming 'entry'): {}"
                "".format(kwargs))
            kwargs['floc']='entry'
        if 'annotationname' in kwargs:
            kwargs[kwargs['ftype']+'annotationname']=kwargs.pop('annotationname')
        if 'annotationvalue' in kwargs:
            kwargs[kwargs['ftype']+'annotationvalue']=kwargs.pop('annotationvalue')
        output=self.get(kwargs['floc']+'/field',**kwargs).get('node')
        return output
    def fieldtext(self,**kwargs):
        """This should take @lang to limit forms by lang, not @analang."""
        """Actually, for now, lx and lc take analang, the secondary forms take
        lang. I should fix this, after preparing. I'm ready to make the change
        in LiftURL, but it will impact other things that are currently working
        """
        t=[]
        for kwargs['node'] in self.fieldnode(**kwargs):
            # log.info("Getting text from node {}".format(node))
            t.extend(self.get('text',**kwargs).get('text'))
        return t
    def fieldvalue(self,**kwargs):
        t=[]
        for kwargs['node'] in self.fieldnode(**kwargs):
            t.extend(self.get('annotation',**kwargs).get('value'))
        return t
    def fieldformnode(self,**kwargs):
        t=[]
        for kwargs['node'] in self.fieldnode(**kwargs):
            t.extend(self.get('form',**kwargs).get())
        return t
    def annotatefield(self,**kwargs):
        if not ('name' in kwargs and 'value' in kwargs):
            log.error("To annotate, I need @name and @value.")
            return
        if not 'analang' in kwargs: #for get(form), below
            log.error("Attention! form annotation without @analang specification "
            "will annotate *all* language forms, which is almost certainly not "
            "what you want! continuing anyway...")
        anndict={ #don't let these pass through as is
                'name': kwargs.pop('name'),
                'value': kwargs.pop('value')
                }
        # kwargs['annotationname']=anndict['name'] #look for value in fieldnode()
        # node=kwargs.pop('node') #because base node changes
        # log.info("Looking w/{}".format(kwargs))
        for kwargs['node'] in self.fieldnode(**kwargs): #these take any annotationname
            for form in self.get('form',
                                lang=kwargs['analang'],
                                **kwargs).get('node'):
                # log.info("Looking in form {} w/{}".format(form,kwargs))
                kwargs.pop('node') #avoid duplication conflict, reset on next iteration
                ann=self.get('annotation', node=form,
                            annotationname=anndict['name'], #only use this here
                            **kwargs).get('node') #name!
                # log.info("Found {}".format(ann))
                for a in ann:
                    a.set('value',anndict['value'])
                if not ann:
                    a=Node(form, tag='annotation', **anndict)
    def extrasegments(self):
        for lang in self.analangs:
            self.segmentsnotinregexes[lang]={}
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
                        try:
                            self.segmentsnotinregexes[lang][x]+=[form]
                        except KeyError:
                            self.segmentsnotinregexes[lang][x]=[form]
                        # log.debug('Missing {} from {} {}'.format(x,lang,form))
            if len(self.segmentsnotinregexes[lang]) > 0:
                log.info("Some symbols do not appear as a unit in "
                    f"your {lang} regex's. This is fine if they exist with "
                    "other symbols exclusively: "
                    f"{self.segmentsnotinregexes[lang]}")
            else:
                print("No problems!")
                log.info(_("Your regular expressions look OK for {lang} (there are "
                    "no segments in your {lang} data that are not in a regex). "
                    "".format(lang=lang)))
                log.info("Note, this doesn't say anything about digraphs or "
                    "complex segments which should be counted as a single "
                    "segment.")
                log.info("--those may not be covered by your regexes.")
    def getpss(self):
        self.pss=[i[0] for i in collections.Counter(
                                            [i.psvalue() for i in self.senses]
                                                    ).most_common() if i[0]]
    def ps(self,**kwargs): #get POS values, limited as you like
        if kwargs:
            return self.get('ps',**kwargs).get('value')
        else:
            return collections.Counter([i.psvalue() for i in self.senses])
    def getpssbylang(self,analang=None): #get all POS values in the LIFT file
        ordered={}
        if analang: #if one specified (after not initially found with data)
            analangs=self.analangs+[analang]
        else:
            analangs=self.analangs
        for lang in analangs:
            counted = collections.Counter(self.ps(lang=lang))
            ordered[lang] = [value for value, count in counted.most_common()
                            if value] #don't include '' or None!
        log.info("Found these ps values, by frequency: {}".format(ordered))
        return ordered
    def getmorphtypes(self): #get all morph-type values in the LIFT file
        m=collections.Counter(self.get('morphtype').get('value')).most_common()
        log.info("Found these morph-type values: {}".format(m))
        return m
        """CONTINUE HERE: Making things work for the new lift.get() paradigm."""
    def copylctolx(self):
        # This is a copy operation, leaving lc in place
        for e in self.getentrynode(**kwargs):
            log.info("Looking at entry w/guid: {}".format(e.guid))
            log.info("Found {}".format(e.lc.forms))
            for lang in e.lc.forms:
                    # log.info("Copying {} from lang {}".format(lcft.text,lcfl))
                """This finds or creates, by lang:"""
                lx=e.lx.textvaluebylang(lang)
                lc=e.lc.textvaluebylang(lang)
                log.info("Copying citation ‘{}’ to lexeme (was {}) for "
                        "lang {}".format(lc,lx,lang))
                e.lx.textvaluebylang(lang,lc) #overwrite in any case
                    # if not lx.text: #don't overwrite info
                    #     lcft.text='' #don't clear
    def convertlxtolc(self,**kwargs):
        # This is a move operation, removing 'from' when done, unless 'to'
        # is both there and different
        kwargs['fromtag']='lexical-unit'
        kwargs['totag']='citation'
        self.convertxtoy(**kwargs)
    def convert1xto1y(self,entry,lang=None,**kwargs):
        if kwargs['fromtag'] in ['definition','gloss']:
            parent=entry.senses[0] #just take first one, for now
        else: #parent of node to find may be sense or entry
            parent=entry
        # log.info("Found entry parent node {}".format(parent))
        if kwargs['fromtag'] == 'gloss':
            froms=parent.glosses
        if kwargs['fromtag'] == 'definition':
            froms=[parent.definition] #just one
        else:
            froms=parent.findall(kwargs['fromtag']) # I need form node, not text node
        # log.info("Found {} entry {} fields".format(len(froms),
        #                                             kwargs['fromtag']))
        for f in froms:
            log.info("Looking at {} {} of entry w/guid: {}"
                    "".format(getattr(f,'lang',''),f.tag,entry.get("guid")))
            if lang:
                if f.tag in ['definition','gloss'] and f.lang != lang:
                    continue
                elif f.tag in ['definition','gloss']:
                    nodes=[f]
                else:
                    nodes=[i for i in Node.childrenwtext(f)
                                if i.get('lang') == lang]
            else:
                nodes=Node.childrenwtext(f)
            log.info("Found {}".format(nodes))
            for ff in nodes:
                # log.info("Working on {}".format(ff))
                ffl=ff.lang
                try:
                    fft=ff.textvaluebylang(lang)
                except AttributeError:
                    fft=ff.textvalue()
                # log.info("Moving {} {} from lang {}".format(ff.tag,fft,ffl))
                """This finds or creates, by lang:""" #This gives text node
                # For now, assuming everything goes to entry:
                if kwargs['totag'] == 'citation':
                    to=entry.lc
                elif kwargs['totag'] == 'gloss':
                    to=entry.glosses[ffl][0]
                else:
                    log.info("convert1xto1y no totag: {}".format(kwargs['totag']))
                    raise
                try:
                    totext=to.textvaluebylang(lang)
                except AttributeError:
                    totext=to.textvalue()
                log.info("Moving {} {}/{} ‘{}’ to {}/{} (was {}) for lang {}"
                        "".format(entry.get("guid"),kwargs['fromtag'],f.tag,fft,
                                    kwargs['totag'],to.tag,totext,ffl))
                if not totext:#,value
                    if f.tag == 'definition' and to.tag == 'citation':
                        to.textvaluebylang(lang,rx.glossdeftoform(fft))
                        # to.text=rx.glossdeftoform(fft.text)
                    if f.tag == 'gloss' and to.tag == 'citation':
                        to.textvaluebylang(lang,rx.glossdeftoform(fft))
                        # to.text=rx.glossdeftoform(fft.text)
                    else:
                        to.textvaluebylang(lang,fft)
                if (to.textvaluebylang(lang) == fft and not kwargs.get('keep')):
                    try:
                        ff.textvaluebylang(lang,'')
                    except AttributeError:
                        ff.textvalue('')
                if (f.tag in ['definition','gloss'] and
                            to.tag == 'citation'):
                    return # just do one
    def convertxtoy(self,lang=None,**kwargs):
        # convert to Entry
        log.info("kwargs: {}".format(kwargs))
        #don't pass these to getentrynode
        f=kwargs.pop('fromtag')
        t=kwargs.pop('totag')
        k=kwargs.pop('keep',False)
        log.info("kwargs: {}".format(kwargs))
        if 'entries' in kwargs:
            entries=kwargs['entries']
        else:
            entries=self.getentrynode(**kwargs) #if no kwargs, all lift.Entries
        log.info("Looking at {} entries ({})".format(len(entries),entries))
        for e in entries:
            log.info("Looking at entry {} ({})".format(e.get('guid'),lang))
            self.convert1xto1y(e,lang,fromtag=f,totag=t,keep=k)
            # if e.get('guid') == '29febd49-9f74-4f6b-8256-21f81d6ba0f2':
            #     prettyprint(e)
            # exit()
    def convertdefntogloss(self,**kwargs):
        # This is a move operation, removing 'from' when done, unless 'to'
        # is both there and different
        kwargs['fromtag']='definition'
        kwargs['totag']='gloss'
        self.convertxtoy(**kwargs)
    def convertglosstocitation(self,lang,**kwargs):
        # This is a move operation, removing 'from' when done, unless 'to'
        # is both there and different
        #This should only ever happen for one lang at a time, to make a demo db
        for sense in self.senses:
            sense.textvaluebyftypelang('lc',lang,
                                        rx.glossdeftoform(
                                        sense.formattedgloss(lang)[0]  #first item of list
                                                            )
                                        )
class EmptyTextNodePlaceholder(object):
    """Just be able to return self.text when asked."""
    def __init__(self):
        # super(EmptyTextNodePlaceholder, self).__init__()
        self.text = None
class Node(et.Element):
    def makefieldnode(self,type,lang,text=None,gimmetext=False):
        n=Node(self,tag='field',attrib={'type':type})
        nn=n.makeformnode(lang,text,gimmetext=gimmetext)
        if gimmetext:
            return nn
        else:
            return n
    def makeformnode(self,lang,text=None,gimmetext=False):
        n=Form(self,attrib={'lang':lang})
        if text:
            n.textvalue(text)
        if gimmetext:
            return n.textnode
        else:
            return n
    def maketextnode(self,text=None,gimmetext=False):
        n=Text(self)
        if text is not None: # allow '' to clear
            n.text=str(text)
        if gimmetext:
            return n
    def maketraitnode(self,type,value,gimmenode=False):
        """obsolete!"""
        n=Node(self,tag='trait',attrib={'name':type, 'value':str(value)})
        if gimmenode:
            return n
    def childrenwtext(self):
        if self.tag == 'gloss':
            if i.findall('text'):
                return [self]
        else:
            return [i for i in self
                        if i.findall('text') and
                        [j for j in i.findall('text') if j.text]
                    ]
    def checkforsecondchild(self,tag):
        """This is only for non-Multiple, single occurrence fields"""
        if len(self.findall(tag)) > 1:
            log.error("{} node in entry {} has multiple forms for {} tag. "
                    "This is not legal LIFT; please fix this!"
                    "".format(self.tag,self.entry.guid,tag))
    def tagattrib(self,node,**kwargs):
        if isinstance(node,et.Element):
            tag=node.tag
            kwargs.pop('tag','') #in case this is there, too.
            attrib=node.attrib
            kwargs.pop('attrib','') #in case this is there, too.
        else: #i.e., if making a node from scratch
            try:
                tag=kwargs.pop('tag') #don't pass these twice
                attrib=kwargs.pop('attrib',kwargs) #{})
            except KeyError:
                log.error("When making a node, add tag and attrib (dict) "
                            "to kwargs")
                raise
        # if kwargs:
        #     log.info("These kwargs are not being passed on: {}".format(kwargs))
        return tag,attrib
    def isnode(self):
        return isinstance(self,et.Element) #allow boolean True w/o children
    def __init__(self, parent, node=None, **kwargs):
        self.parent=parent
        tag,attrib=self.tagattrib(node,**kwargs) #this pulls from either
        # log.info("Calling with tag: {}, attrib: {}, kwargs: {}".format(
        #                                                 tag, attrib, kwargs
        #                                                     ))
        super(Node, self).__init__(tag, attrib) # **kwargs gives extra attrs
        if isinstance(node,et.Element): #make sure to get all of it
            for child in node:
                self.append(child)
            for attr in ['text', 'tail']:
                setattr(self,attr,getattr(node,attr))
        elif node:
            log.error("Non-et.Element Node provided ? (parent: {}, {}:{})"
                    "".format(self.parent,type(node),node))
            raise
        if isinstance(parent,et.Element):
            if isinstance(node,et.Element): #put back where it came from
                # log.info("replacing with new node: {}".format(self))
                self.index=[i for i in parent].index(node)
                parent.remove(node)
                parent.insert(self.index,self)
            else:
                parent.append(self) # add new elements after other children
            self.db=parent.db #keep this available
        elif isinstance(parent,LiftXML): # root element parent is object
            self.db=parent
        # if self.tag not in ['text','form','gloss']:
        #     log.info(f"Init done for {self.tag} node with {[i for i in self]}")
class Lift(Node):
    def __init__(self, parent, node, **kwargs):
        kwargs['tag']='lift'
        super(Lift, self).__init__(parent, node, **kwargs)
class Text(Node):
    def __init__(self, parent, node=None, **kwargs):
        kwargs['tag']='text'
        super(Text, self).__init__(parent, node, **kwargs)
        if self.text:
            self.text=self.text.replace('\n','').strip() #don't allow spaces or newlines on edges, no newlines anywhere
class ValueNode(Node):
    def myvalue(self,value=None):
        if value:
            self.set(self.valuename,value)
        elif value == '':
            del self.attrib[self.valuename]
        return self.get(self.valuename)
    def __init__(self, parent, node=None, **kwargs):
        self.valuename='value' #default
        super(ValueNode, self).__init__(parent, node, **kwargs)
class Annotation(ValueNode):
    def __init__(self, parent, node=None, **kwargs):
        kwargs['tag']='annotation'
        if 'attrib' in kwargs and 'name' not in kwargs['attrib']:
            log.error("No name for this annotation! ({})".format(kwargs))
        super(Annotation, self).__init__(parent, node, **kwargs)
class Trait(ValueNode):
    def __init__(self, parent, node=None, **kwargs):
        kwargs['tag']='trait'
        super(Trait, self).__init__(parent, node, **kwargs)
class Ps(ValueNode):
    def __init__(self, parent, node=None, **kwargs):
        kwargs['tag']='grammatical-info'
        super(Ps, self).__init__(parent, node, **kwargs)
class Form(Node):
    def gettext(self):
        self.textnode=Text(self,self.find('text'))
    def getannotations(self):
        self.annotations={i.get('name'):Annotation(self,i) for i in self
                                            if i.tag == 'annotation'
                        }
    def annotationvaluedict(self):
        return {name:self.annotationvalue(name)
                for name in self.annotations}
    def annotationkeys(self):
        return list(self.annotations)
    def annotationvalue(self,name,value=None):
        if name in self.annotations:
            return self.annotations[name].myvalue(value)
        elif value:
            self.annotations[name]=Annotation(self,attrib={'name':name,
                                                        'value':value})
        else:                                                        
            return None
    def textquoted(self):
        r=quote(self.textnode.text)
        shownot=['lc','example','Frame translation']#lx?
        if hasattr(self.parent,'ftype') and self.parent.ftype not in shownot:
            r+="("+self.parent.ftype+")"
        return r
    def textvalue(self,value=None):
        if value is not None: #leave room to clear value with False
            # log.info("Setting textvalue to ‘{}’ ({})".format(value,type(value)))
            self.textnode.text=value
        else:
            return self.textnode.text
    def __init__(self, parent, node=None, **kwargs):
        kwargs['tag']='form'
        super(Form, self).__init__(parent, node, **kwargs)
        self.gettext()
        self.getannotations()
        self.lang=self.get("lang")
class FormParent(Node):
    def getanalang(self):
        return self.db.analang
    def getlang(self,lang=None): #,shortest=False
        """The number of languages in FormParent forms doesn't really tell what
        makes a good default language choice. Some fields typically only have
        one form, in a given language (e.g., 'translation' and
        Fields with ftype=verification, tone, cvprofile, or location).
        Other fields (e.g., lc, lx, pl, imp, example) normally take
        multiple forms ()"""
        # this allows forms to be specified for any lang, so long as there is
        # just one. Ultimately, we should specify which language these fields
        # should be encoded in, and what to do when the UI lang is different.
        # right now, this is most relevant for tone and location fields, which
        # are not really language specific (though may be specified in one lang
        # or another)
        if lang:
            # log.info("using lang specified: {}".format(lang))
            return lang
        # langs=list(self.parent.entry.lc.langs()) #languages of forms already present
        analang=self.getanalang()
        # min(list(self.parent.entry.lc.langs()),key=len)
        # self.parent.entry.lc.getlang(shortest=True)
        # if shortest:
        #     return min(langs,key=len)
        """Fields with variable ftypes are used for pl and imp, each of which
        can have at least analang and audiolang form nodes. Those are currently
        made by methods that require lang be specified. When updated to use
        they should be wrapped by a method that maintains this requirement."""
        if isinstance(self, Field):
            possibles=list(self.langs()) #This is self.forms.keys()
            if len(possibles) == 1:
                return possibles[0]
            elif 'verification' in self.ftype:
                return pylang(analang)
                # log.info("using verification pylang {}".format(lang))
            elif 'tone' in self.ftype:
                return tonelang(analang)
            elif 'cvprofile' in self.ftype:
                return profilelang(analang)
            elif self.ftype in ['location', 'SILCAWL']:
                return self.annotationlang
            elif analang in possibles:
                return analang
            else:
                log.error("Apparently I left a field type off the list? "
                            "Plural and imperative fields need lang specified. "
                            f"({self.ftype})")
                raise
        elif isinstance(self, (Lexeme, Citation)):
            return analang
        elif isinstance(self, (Example, Definition, Translation,Pronunciation)):
            log.error(f"{type(self)} node is asking for a language; this "
                        "should already be specified.")
            raise
        else:
            log.error("Apparently I left a node type off the list? "
                        f"({type(self)})")
            raise
            # log.info("returning shortest lang ({}) of {}".format(lang,langs))
    def langftypecode(self,lang):
        return '_'.join([lang,self.ftype])
    def stripftypecode(self,x):
        return x.removesuffix('_'+self.ftype)
    def textvaluedict(self):
        return {lang:self.forms[lang].textvalue()
                for lang in self.forms}
    def textquotedbylang(self,lang):
        try:
            return self.forms[lang].textquoted()
        except KeyError:
            return None
    def textvaluebylang(self,lang=None,value=None):
        if not lang:
            lang=self.getlang(lang)
        if lang not in self.forms:
            # log.info(f"Missing ‘{lang}’ lang in textvaluebylang: {self.forms=}")
            if value is not None: #only make if we're populating it, allow ''
                self.forms[lang]=Form(self,attrib={'lang':lang})
            else:
                return None
        if value is False:
            self.remove(self.forms[lang])
            del self.forms[lang]
            return
        return self.forms[lang].textvalue(value)
    def annotationvaluedictbylang(self,lang):
        return self.forms[lang].annotationvaluedict()
    def annotationkeysbylang(self,lang):
        lang=self.getlang(lang) #This might be better more internally
        try:
            return self.forms[lang].annotationkeys()
        except KeyError:
            pass #make this check easy on the log; it iterates over all senses
            # log.error(f"{self.sense.id}-{self.ftype} has no {lang} form "
            #             f"(only {self.forms.keys()})")
        except Exception as e:
            log.error(f"annotationkeysbylang Exception! ({e})")
    def annotationkeyinlang(self,check,lang=None):
        lang=self.getlang(lang) #This might be better more internally
        keys=self.annotationkeysbylang(lang)
        return keys and check in keys
    def annotationvaluebylang(self,lang,name,value=None):
        lang=self.getlang(lang) #This might be better more internally
        try:
            return self.forms[lang].annotationvalue(name,value)
        except KeyError:
            if value:
                log.error(f"{self.sense.id}-{self.ftype} has no {lang} form; "
                        f"can't apply {value=} (only {self.forms.keys()})")
        except Exception as e:
            log.error("annotationvaluebylang Exception! ({})".format(e))
    def checkforsecondchildanylang(self,lang):
        if len(self.findall('form')) > 1:
            log.error("{} node in entry {} has multiple forms. "
                    "While this is legal LIFT, it is probably an error, and "
                    "will lead to unexpected behavior."
                    "".format(self.tag,self.parent.entry.guid,lang))
    def checkforsecondchildbylang(self):
        for lang in self.forms:
            if len(self.findall('form[@lang="{}"]'.format(lang))) > 1:
                try:
                    num=self.find('field[@type="location"]/form/text').text
                except:
                    num="?"
                guid=(self.parent.entry.guid if hasattr(self.parent,'entry')
                                            else self.parent.guid)
                log.error(f"{self.tag} node {num} in entry {guid} has multiple "
                    "forms for ‘{lang}’ lang. While this is legal LIFT, "
                    "it is almost certainly an error, and will lead to "
                    "unexpected behavior.")
                forms=self.findall(f'form[@lang="{lang}"]')
                texts=[i.find('text').text for i in forms
                                                if hasattr(i.find('text'),'text')]
                if texts and texts[0] == texts[1]:
                    log.info(f"texts {texts[0]} & {texts[1]} are the same, so "
                        "deleting the second")
                    self.remove(forms[1])
                elif set('/\\')&set(texts[0]) or set('/\\')&set(texts[1]):
                    absolute=file.absolute_of_other(*texts[:2])
                    if absolute:
                        log.info(f"texts ‘{texts[0]}’ & ‘{texts[1]}’ are not "
                        f"the same, but {absolute} seems to be an absolute (or "
                        "more absolute) version of the other, so removing it.")
                        self.remove(forms[texts.index(absolute)])
                    else:
                        log.info(f"texts ‘{texts[0]}’ & ‘{texts[1]}’ are not "
                            "the same. At least one seems to contain "
                            "a directory, but I can't find an absolute path "
                            "to remove.")
                else:
                    log.info(f"texts ‘{texts[0]}’ & ‘{texts[1]}’ are not "
                        "the same, and neither seems to contain a directory,"
                        "so I'm not sure what to do.")
    def getforms(self):
        self.forms={
                    lang:Form(self,self.find('form[@lang="{}"]'.format(lang)))
                        for lang in [i.get('lang')
                                    for i in self.findall('form')]
                        if lang
                    }
        self.checkforsecondchildbylang()
    def langs(self):
        return self.forms.keys()
    def formattedbylang(self,lang,frame):
        """This function is safe to give formatted analang material, since it
        is not used for glosses, which are Form nodes, not FormParent nodes"""
        t=self.textvaluebylang(lang)
        if t and frame:
            try: #process analang correctly, if distinct
                t=rx.framerx.sub(t,frame[self.langftypecode(lang)])
            except KeyError:
                t=rx.framerx.sub(t,frame[lang])
        return t
    def formatted(self,analang,glosslangs,ftype=None,frame=None,**kwargs):
        # Don't die on showtonegroup
        if (ftype and ftype != self.ftype) or (frame and 'field' in frame and
                                                frame['field'] != self.ftype):
            try:
                log.error("Problem; asked for ftype {}, but working on {} node "
                        "with {} frame"
                        "".format(ftype,self.ftype,frame.get('field')))
            except AttributeError:
                log.error("Problem; asked for ftype {}, but working on {} node "
                        "with no frame".format(ftype,self.ftype))
            return
        l=[self.formattedbylang(analang,frame)]
        if not [i for i in l if i]:
            log.info("No {} form found; just giving glosses".format(ftype))
        try:
            for lang in [i for i in glosslangs
                            if i in self.sense.glosses]:
                for g in self.sense.formattedgloss(lang,ftype,frame,quoted=True):
                    #This is always a list
                    if self.ftype == 'pl':
                        g+=_(" (pl)")
                    elif self.ftype == 'imp':
                        g+="!"
                    l.append(g)
            return ' '.join([i for i in l if i]) #put it all together
        except IndexError:
            log.info(_("This entry doesn't seem to have a sense."))
        except AttributeError:
            log.info(_("This doesn't seem to be called on a child of entry "
                    "({entry} child of {parent}), or the entry's first sense ({sense}) doesn't "
                    "have gloss languages ({glosses})."
                    ).format(entry=type(self),parent=type(self.parent),
                            sense=self.sense.id,
                            glosses=self.sense.glosses.keys()))
    def getsense(self):
        if hasattr(self.parent,'senses') and self.parent.senses:
            # we want a common reference point for glosses, first sense is OK
            self.sense=self.parent.sense
    def glossbylang(self,lang):
        return ', '.join(self.parent.sense.formattedgloss(lang))
    def hassoundfile(self,recheck=False):
        """self.audiofileisthere is stored and read here both for lexical and
        example fields."""
        """"These attributes are not stored in lift; they depend on the work
        environment, so are set on each use. audiodir should be the
        fully qualified filesystem path, not a relative one (e.g., 'audio')"""
        if hasattr(self,'audiofileisthere') and not recheck:
            return self.audiofileisthere
        if rel:=self.textvaluebylang(self.db.audiolang):
            # try: #get audiofileURL or fail
            abs=file.getdiredurl(self.db.audiodir,rel)
                                # self.textvaluebylang(self.db.audiolang))
            # log.info(f"Working with absolute audio filename: {abs}")
            if bool(abs) and file.exists(abs):
                self.audiofileisthere=True
                self.audiofileURL=abs
                return True
        self.audiofileisthere=False #If not in lift *and* file system
    def __init__(self, parent, node=None, **kwargs):
        super(FormParent, self).__init__(parent, node, **kwargs)
        self.getforms()
        self.getsense()
        self.ftype=self.get('type',self.tag)
        self.annotationlang=parent.annotationlang
class Gloss(Form):
    def __init__(self, parent, node=None, **kwargs):
        kwargs['tag']='gloss'
        super(Gloss, self).__init__(parent, node, **kwargs)
        self.lang=self.get("lang")
class Translation(FormParent):
    """From Docs: Each translation is of a single type and contains all the
    translations of that type into multiple languages and writing systems."""
    def __init__(self, parent, node=None, **kwargs):
        kwargs['tag']='translation'
        # kwargs['attrib']={'type':'Frame translation'}
        super(Translation, self).__init__(parent, node, **kwargs)
        self.set('type','Frame translation')
class Field(FormParent):
    def __init__(self, parent, node=None, **kwargs):
        kwargs['tag']='field'
        super(Field, self).__init__(parent, node, **kwargs)
        self.ftype=self.get('type',kwargs.get('ftype')) #make a field with kwargs
        # log.info("Made field with type {}, texts {}".format(self.ftype,
        #                                                 self.textvaluedict()))
class Definition(FormParent):
    def __init__(self, parent, node=None, **kwargs):
        kwargs['tag']='definition'
        super(Definition, self).__init__(parent, node, **kwargs)
class Lexeme(FormParent):
    def __init__(self, parent, node=None, **kwargs):
        kwargs['tag']='lexical-unit'
        super(Lexeme, self).__init__(parent, node, **kwargs)
        self.ftype='lx'
class Citation(FormParent):
    def __init__(self, parent, node=None, **kwargs):
        kwargs['tag']='citation'
        super(Citation, self).__init__(parent, node, **kwargs)
        self.ftype='lc'
class FieldParent(object):
    """This is needed because some fields are under Entry, others under sense"""
    def checkforsecondfieldbytype(self,type,tag=None):
        """This just logs an error with a return if found"""
        if not tag:
            tag='field'
        if len(self.findall('{}[@type="{}"]'.format(tag,type))) > 1:
            values=[i.textvaluebylang() for i in self.findall(f'{tag}[@type="{type}"]')]
            log.error("{} node in entry {} has multiple {} nodes of ‘{}’ type. "
                    "While this is legal LIFT, it is probably an error, and "
                    f"will lead to unexpected behavior. ({values=})"
                    "".format(self.tag,self.entry.guid,tag,type))
            return 1
    def getfields(self):
        """This converts XML field nodes to Field objects, and indexes them
        under this parent."""
        # log.info(f"FieldParent {self.tag} field types: {[i.get('type')
        #                                     for i in self.findall('field')]}")
        # self.fields={node.ftype:node for node in self
        #                 if isinstance(node,Node) #I.e., already brought in
        #                 and nod.tag == 'field'
        #             }
        # use the above updated with this if fields aren't picked up correctly
        self.fields={
                    node.get('type'):Field(self,node)
                        for node in self.findall('field')
                        if not isinstance(node,Node) #I.e., already brought in
                    }
        # log.info(f"FieldParent {self.tag} getfields {self.fields=}")
        for type in self.fields:
            self.checkforsecondfieldbytype(type)
    def newfield(self,type,lang=None,value=None):
        """use fieldvalue below"""
        raise
        if not value:
            log.info(_("We normally shouldn't create empty fields: {lang}/{value}")
                    .format(lang=lang, value=value))
        if type in self.fields:
            log.error(_("There is already a {type} field here! ({fields})")
                    .format(type=type, fields=self.fields))
            return
        self.fields.update({type:Field(self,type=type)}) #make field
        # without lang here, annotationlang is used; value=None does nothing
        self.fields[type].textvaluebylang(lang=lang,value=value) #set value?
    def fieldvalue(self,type,lang=None,value=None):
        """lang=None is OK for fields with just one form@lang node, or if
        self.ftype contains 'verification', 'tone', 'cvprofile', 'location',
        or 'SILCAWL'
        """
        try:
            assert isinstance(self.fields[type],et.Element)
            # log.info("found ET node")
        except (AssertionError,KeyError):
            found=self.find(f'field[type="{type}"]')
            # log.info(f"found new XML node {found}")
            if isinstance(found,et.Element) or value:
                if isinstance(found,et.Element):
                    val_lang = found.getlang()
                    val_val = found.textvaluebylang()
                    log.error(_("This should never happen; somehow an XML field "
                        "was not picked up on boot, but was found just now. "
                        "type: {type}, lang: {lang}, "
                        "value: {value}, "
                        "parent: {parent}").format(type=type, lang=val_lang, value=val_val, parent=self.parent))
                    raise
                if self.checkforsecondfieldbytype(type):
                    log.error(_("This should definitely never happen; somehow "
                        "multiple XML fields are found with type {type}.")
                        .format(type=type))
                # node=None creates a new field node, forms nodes below
                self.fields.update({type:Field(self,node=found,type=type)})
                self.checkforsecondfieldbytype(type) #b/c new field made
            else:
                return None
        # specify value as kwarg because not specifying lang
        fv=self.fields[type].textvaluebylang(lang=lang,value=value)
        # log.info(f"fieldvalue returning {fv=} for {self.sense.id}-{type}")
        return fv
    def __init__(self):
        # log.info("Initializing field parent for {}".format(self))
        if not hasattr(self,'annotationlang'):
            self.annotationlang=self.parent.annotationlang
        self.getfields()
        # log.info("Initialized field parent for {}".format(self))
class Example(FormParent,FieldParent):
    def locationvalue(self,loc=None):
        """this should use fieldvalue(self,type,lang=None,value
        """
        return self.fieldvalue('location',value=loc)
    def tonevalue(self,value=None):
        # log.info("Fields @tonevalue: {}".format(self.fields))
        return self.fieldvalue('tone',value=value)
    def translationvalue(self,lang=None,value=None):
        try:
            assert isinstance(self.translation,et.Element)
            return self.translation.textvaluebylang(lang,value) # w/wo value
        except AssertionError:
            if value: #don't make field if not setting value
                # log.info(f"Adding new translation field {lang} = {value} ({e})")
                t=Translation(self)
                t.textvaluebylang(lang,value)
            else:
                return None
    def glossbylang(self,lang):
        return self.translationvalue(lang)
    def lastAZTsort(self):
        try:
            assert isinstance(self.lastsort,et.Element)
        except (AssertionError,AttributeError):
            found=self.find('trait[@name="Latest A-Z+T Sort"]')
            self.lastsort=Trait(self, found, name="Latest A-Z+T Sort")
        return self.lastsort.myvalue(getnow())
    def setguid(self):
        # only do this on sorting!
        self.set('source','AZT sorted first on {}'.format(getnow()))
    def getguid(self):
        self.get('source')
    def gettranslations(self):
        #There may be other @types of translation nodes; we use this one.
        self.translation=Translation(self,self.find(
                                    'translation[@type="Frame translation"]'))
        self.checkforsecondfieldbytype("Frame translation",tag='translation')
    def formatted(self,analang,glosslangs,showtonegroup=False,**kwargs):
        # **kwargs is so we don't die on ftype, frame args
        l=[]
        if showtonegroup:
            try:
                int(self.tonevalue())  #only for named groups
            except ValueError:
                l.append(self.tonevalue())
        l.append(self.textvaluebylang(analang))
        for lang in glosslangs:
            l.append(self.translation.textquotedbylang(lang))
        return ' '.join([i for i in l if i]) #put it all together
    def __init__(self, parent, node=None, **kwargs):
        kwargs['tag']='example'
        super(Example, self).__init__(parent, node, **kwargs)
        self.entry=parent.entry #make a common reference point for sense/entry
        self.sense=parent
        FieldParent.__init__(self) #tone and location values
        # log.info("Example fields: {}".format(self.fields))
        # These two are collected by FieldParent:
        self.checkforsecondfieldbytype('location')
        self.checkforsecondfieldbytype('tone')
        self.gettranslations()
class Pronunciation(FormParent,FieldParent):
    def __init__(self, parent, node=None, **kwargs):
        kwargs['tag']='pronunciation'
        super(Pronunciation, self).__init__(parent, node, **kwargs)
        self.entry=parent.entry #make a common reference point for sense/entry
        FieldParent.__init__(self) #tone and location values
        # These two are collected by FieldParent:
        self.checkforsecondfieldbytype('location')
        self.checkforsecondfieldbytype('tone')
class Illustration(ValueNode):
    def __init__(self, parent, node=None, **kwargs):
        kwargs['tag']='illustration'
        super(Illustration, self).__init__(parent, node, **kwargs)
        self.valuename='href'
class Sense(Node,FieldParent):
    def getglosses(self):
        """This differs from a FormParent, in that self.glosses contains
        a list of objects, as multiple gloss entries seem to be a thing"""
        self.glosses={
                    lang:[Gloss(self,i) for i in self
                        if i.tag == 'gloss' and lang==i.get('lang')
                        ]
                            for lang in [i.get('lang') for i in self]
                            if lang
                    }
        # log.info("Found {} gloss(es)".format(len(self.glosses)))
        # log.info("Found gloss(es): {}".format(self.glosses))
        # Openclipart only has English keywords
        # This should give appropriate splitting on commas,
        # without extra spaces, nor splitting phrases by spaces
        self.collectionglosses=[rx.noparens(i).strip()
                                    for k in self.sense.glosses.get('en',[])
                                    if k.textvalue()
                                    for i in k.textvalue().split(',')
                                ]
        self.collectionglossesunderlined=rx.urlok('_'.join([rx.slashdash(i)
                                        for j in self.collectionglosses
                                        for i in j.split()
                                        if i]))
        rootimgdir='images/toselect/'
        self.imgselectiondir=None
        #These first two depend on real directories being there
        if self.cawln:
            self.imgselectiondir=[i for i in file.getfilesofdirectory(
                            rootimgdir,
                            regex='_'.join([self.cawln,self.collectionglossesunderlined])+'*'                                )]
        elif self.collectionglossesunderlined:
            self.imgselectiondir=[i for i in file.getfilesofdirectory(
                                    rootimgdir,
                                    regex='*_'+self.collectionglossesunderlined)]
        if self.imgselectiondir: #unlist if there
            self.imgselectiondir=self.imgselectiondir[0]
            return
        if self.cawln and self.collectionglosses and not self.imgselectiondir:
            bits=[self.cawln,self.collectionglossesunderlined]
            # log.info("I didn't find a real directory present, but I'm ready "
            # "to write to {}".format(''.join([rootimgdir,'_'.join(bits)])))
            self.imgselectiondir=file.makedir(''.join([ #This may not be a real directory
                                                rootimgdir,
                                                '_'.join(bits)
                                                ]))
            return
    def imagename(self):
        # log.info("Making image name")
        affix='.png' #not sure why this isn't there already...
        if self.cawln:
            return '_'.join([self.cawln,self.collectionglossesunderlined])+affix
        else:
            return '_'.join([self.id,self.collectionglossesunderlined])+affix
    def glossbylang(self,lang):
        """This returns just the first, to be compatible with
        example.glossbylang"""
        gs=self.glossvaluesbylang(lang)
        if gs:
            return gs[0]
    def glossvaluesbylang(self,lang):
        try:
            assert isinstance(self.glosses[lang][0],et.Element)
            return [i.gettext() for i in self.glosses[lang]]
        except KeyError:
            # log.info("No gloss for lang {}".format(lang))
            pass
    def getdefinitions(self):
        self.definition=Definition(self,self.find('definition'))
        self.checkforsecondchild('definition')
    def newexample(self,loc,frame,analang,glosslangs,tonevalue):
        if loc in self.examples:
            log.error(_("There is already a {location} example here! ({examples})")
                    .format(location=loc, examples=self.examples))
            return
        self.examples.update({loc:Example(self)})
        # without lang here, annotationlang is used; value=None does nothing
        formvalue=self.formattedform(analang,
                                    # ftype, #shouldn't be needed
                                    frame=frame)
        self.examples[loc].textvaluebylang(lang=analang,value=formvalue) #form
        self.examples[loc].tonevalue(tonevalue)
        self.examples[loc].locationvalue(loc)
        for g in glosslangs:
            for f in self.formattedgloss(g,frame=frame)[:1]: #don't put multiples here
                self.examples[loc].translationvalue(g,f)
        self.examples[loc].setguid()
        self.examples[loc].lastAZTsort()
        # prettyprint(self.examples[loc])
    def getexamples(self):
        # log.info("getting examples for sense {}".format(self.id))
        # actual locations found in actual examples:
        locations=list(set([i.text for i in self.findall(
                            'example/field[@type="location"]/'
                            'form/text')
                            ]))
        if locations:
            exs={}
            # log.info("Locations: {}".format(locations))
            for loc in locations:
                # log.info("Examples ({}): {}".format(loc,
                #                         [i for i in self.findall('example')
                #                         if i.findtext('field[@type="location"]/'
                #                                     'form/text') == loc
                #                         ]))
                # for python 3.7+, use
                # self.find(
                #             'example/field[@type="location"]/'
                #             'form/text[.="{}"]/../../..'.format(loc))
                exs[loc]=[i for i in self.findall('example')
                                if i.findtext('field[@type="location"]/'
                                            'form/text') == loc
                            ]
                if len(exs[loc]) == 1:
                    continue
                elif len(exs[loc]) > 1:
                    log.error(_("{tag} node in entry {guid} has multiple examples with "
                                "location {loc}. While this is legal LIFT, it is probably an error, "
                                "and will lead to unexpected behavior.").format(tag=self.tag, guid=self.parent.guid, loc=loc))
                else:
                    log.error(_("{tag} node in entry {guid} has no examples with "
                                "location {loc}? This is a logical error in A−Z+T ").format(tag=self.tag, guid=self.parent.guid, loc=loc))
                    raise
        # only make location keys with examples where found
        self.examples={loc:Example(self, exs[loc][0]) for loc in locations}
    def getpssubclass(self):
        for n in self.findall('trait[@name="{}-infl-class"]'
                                ''.format(self.psvalue())):
            self.pssubclass=Trait(self,n) #only if found
    def tonevaluebyframe(self,frame,value=None):
        try:
            return self.examples[frame].tonevalue(value)
        except KeyError:
            # log.info("There is no {} example in sense {}".format(frame,self.id))
            pass
    def cvprofileuservalue(self,ftype='lc',value=None):
        type='cvprofile-user_'+ftype
        if value:
            log.info(_("setting {id} to {type} = {value}")
                    .format(id=self.id, type=type, value=value))
        else:
            val_fv = self.fieldvalue(type,value=value)
            log.info(_("returning {id} {type} value: {value}")
                    .format(id=self.id, type=type, value=val_fv))
        #w/o lang, 'value' must be kwarg:
        return self.fieldvalue(type,value=value)
    def cvprofilevalue(self,ftype='lc',value=None):
        type='cvprofile_'+ftype
        return self.fieldvalue(type,value=value) #wo lang, 'value' must be kwarg
    def uftonevalue(self,value=None):
        return self.fieldvalue('tone',value)
    def pssubclassvalue(self,value=None):
        try:
            assert isinstance(self.pssubclass,et.Element)
        except (AssertionError,AttributeError):
            found=self.find('trait[@name="{}-infl-class"]'
                            ''.format(self.psvalue()))
            if isinstance(found,et.Element) or value:
                self.pssubclass=Trait(self,found,
                                    name="{}-infl-class".format(self.psvalue()))
                                    # value=value)
            else:
                return None
        return self.pssubclass.myvalue(value)
    def rmpsnode(self):
        if (hasattr(self,'ps') and isinstance(self.ps,et.Element)
                                and self.ps in self):
            self.remove(self.ps)
        else:
            log.info(_("psnode {ps} not found in sense {sense} ({id})")
                    .format(ps=self.ps, sense=self, id=self.id))
    def rmpssubclassnode(self):
        if isinstance(self.pssubclass,et.Element):
            self.remove(self.pssubclass)
        else:
            log.info(_("pssubclass {subclass} not found in sense {sense} ({id})")
                    .format(subclass=self.pssubclass, sense=self, id=self.id))
    def psvalue(self,value=None):
        try:
            assert isinstance(self.ps,et.Element)
        except (AssertionError,AttributeError):
            found=self.find('grammatical-info')
            if isinstance(found,et.Element) or value:
                self.ps=Ps(self, found)
            else:
                return None
        return self.ps.myvalue(value)
    def annotationvaluedictbyftypelang(self,ftype,lang):
        try:
            return self.ftypes[ftype].annotationvaluedictbylang(lang)
        except KeyError:
            # log.info("No {} type to pull annotation dict from".format(ftype))
            return {}
    def annotationkeysbyftypelang(self,ftype,lang):
        try:
            return self.ftypes[ftype].annotationkeysbylang(lang)
        except KeyError:
            # log.info("No {} type to pull annotation dict from".format(ftype))
            return []
    def nodebyftype(self,ftype):
        try:
            return self.ftypes[ftype]
        except KeyError:
            # log.info("No {} type to pull ({})".format(ftype,self.ftypes))
            pass
    def textvaluebyftypelang(self,ftype,lang,value=None):
        if ftype in self.ftypes:
            return self.ftypes[ftype].textvaluebylang(lang,value)
        # try:
        # except KeyError:
        #     pass
            # log.info("No {} type ({})".format(ftype,self.ftypes))
    def annotationvaluebyftypelang(self,ftype,lang,name,value=None):
        try:
            return self.ftypes[ftype].annotationvaluebylang(lang,name,value)
        except KeyError:
            # log.info("No {} type to pull annotation from".format(ftype))
            pass
    def getcawlline(self):
        if 'SILCAWL' in self.fields:
            self.cawln=self.fields['SILCAWL'].textvaluebylang()
        else:
            self.cawln=None
    def illustrationURI(self):
        v=self.illustrationvalue()
        if v:
            return file.getdiredurl(self.db.imgdir,v)
    def illustrationvalue(self,value=None):
        try:
            assert isinstance(self.illustration,et.Element)
            # if value:
            #     self.illustration.myvalue(value)
        except (AssertionError,AttributeError):
            found=self.find('illustration')
            if isinstance(found,et.Element) or value:
                self.illustration=Illustration(self, found)
            else:
                return None
        return self.illustration.myvalue(value)
    def formattedform(self,analang,ftype=None,frame=False):
        if not ftype:
            if frame:
                ftype=frame['field']
            else:
                ftype='lc'
        try:
            return self.ftypes[ftype].formattedbylang(analang,frame)
        except KeyError:
            log.info(_("No {type} type ({ftypes})").format(type=ftype, ftypes=self.ftypes))
    def formattedgloss(self,glosslang,ftype=None,frame=False,quoted=False):
        """This outputs a list that can be joined as needed"""
        # log.info("formattedgloss called with glosslang={}, ftype={}, frame={}, "
        #         "quoted={}"
        #         "".format(glosslang,ftype,frame,quoted))
        if glosslang not in self.glosses:
            return [_("No {lang} gloss found!").format(lang=glosslang)]
        if frame and glosslang not in frame:
            return [_("No {lang} field in frame!").format(lang=glosslang)]
        if not ftype:
            if frame:
                ftype=frame['field']
            else:
                ftype='lc'
        t=[]
        for gloss in self.glosses[glosslang]: #unlist each gloss for one lang
            # log.info("gloss forms starting: {}".format(t))
            # log.info("gloss: {} ({})".format(gloss.textvalue(),glosslang))
            g=gloss.textvalue()
            if ftype:
                if ftype == 'imp':
                    g+='!'
                elif ftype != 'lc':
                    g+=' ('+ftype+')'
            if frame:
                # log.info("gloss form to sub: {}".format(g))
                g=rx.framerx.sub(g,frame[glosslang])
                # log.info("gloss form subbed: {}".format(g))
            if quoted:
                g=quote(g)
                # log.info("gloss form quoted: {}".format(g))
            t.append(g)
            # log.info("gloss forms formatted: {}".format(t))
        # log.info("gloss forms returned: {}".format(t))
        return t
    def formatteddictbylang(self,analang,glosslangs,ftype=None,frame=None):
        if frame and ftype and not frame['field'] == ftype:
            val_ff = frame['field']
            log.error(_("ftype mismatch! ({val}/{type})").format(val=val_ff, type=ftype))
            return
        elif frame and not ftype:
            ftype=frame['field']
        log.info(_("Found glosses {glosses}").format(glosses=self.glosses))
        log.info(_("asked for glosslangs {langs}").format(langs=glosslangs))
        log.info(_("looking for langs {langs}").format(langs=[i for i in glosslangs if i in self.glosses]))
        d={lang:', '.join(self.formattedgloss(lang,ftype,frame,quoted=True))
            for lang in [i for i in glosslangs if i in self.glosses]}
        #don't overwrite gloss in analang, if both there:
        d[self.nodebyftype(ftype).langftypecode(analang)
            ]=self.formattedform(analang,ftype,frame)
        return d
    def formattedexample(self,analang,glosslangs,loc,showtonegroup=False):
        if loc in self.examples:
            return self.examples[loc].formatted(analang,glosslangs,
                                                showtonegroup)
    def formatted(self,analang,glosslangs,ftype=0,frame=0): #,showtonegroup=0):
        """This uses frame definition, not name"""
        """As a format of the sense, there should be no tonegroup to show"""
        if frame and not frame['field'] == ftype:
            val_ff = frame['field']
            log.error(_("ftype mismatch! ({val}/{type})").format(val=val_ff, type=ftype))
            return
        elif frame and not ftype:
            ftype=frame['field']
        l=[]
        glosses=[]
        # log.info("frame: {}".format(frame))
        # log.info("1 forms: {}".format(l))
        t=self.formattedform(analang,ftype,frame)
        l.append(t)
        # l.append(t+':') this or the above
        l.append('—') #this is just a visual break between the form and glosses
        # l.append(' ')
        # log.info("2 forms: {}".format(l))
        for lang in [i for i in glosslangs if i in self.glosses if not frame or i in frame]:
            glosses+=self.formattedgloss(lang,ftype,frame,quoted=True) # list
        if glosses:
            l+=glosses
        else:
            txt=(f"Asked for glosslangs {glosslangs}, "
                f"found glosses for {list(self.glosses)}")
            if frame:
                txt+=f" and frame translations for {list(frame)}"
            log.info(txt)
            l+=[_("{langs} gloss languages not in frame!").format(langs=' & '.join(glosslangs))]
        # log.info("Returning forms: {}".format(l))
        return ' '.join([i for i in l if i]) #put it all together
    def unformatted(self,analang,glosslangs,ftype=0): #,showtonegroup=0):
        """This uses frame definition, not name"""
        """As a format of the sense, there should be no tonegroup to show"""
        if not ftype:
            ftype='lc'
        l=[]
        t=self.ftypes[ftype].textvaluebylang(analang)
        l.append(t)
        for lang in [i for i in glosslangs if i in self.glosses]:
            l+=[rx.noparens(i).strip() for i in
                 self.formattedgloss(lang,ftype,quoted=False)] #always a list
        return ' '.join([i for i in l if i]) #put it all together
    def rmverificationvalue(self,profile,ftype,value):
        #This treats value as a list object, wrapped by verificationtextvalue
        v=self.verificationtextvalue(profile,ftype)
        try:
            v.remove(value)
            self.verificationtextvalue(profile,ftype,value=v) #remove on []
        except Exception as e:
            log.info(_("tried to remove what wasn't there? ({error})").format(error=e))
    def rmverificationnode(self,profile,ftype):
        key=self.verificationkey(profile,ftype)
        # log.info(f"Removing {key} verification from {self}")
        self.remove(self.fields[key])
        del self.fields[key]
    def verificationkey(self,profile,ftype):
        if ftype in ['alphabet', 'alpha']:
            return f'{ftype} verification'
        else:
            return f'{profile} {ftype} verification'
    def verificationtextvalue(self,profile,ftype,lang=None,value=None):
        """value here is the list of verification codes, stored as a string"""
        """Without lang arg, value must be sent as a kwarg."""
        key=self.verificationkey(profile,ftype)
        #This is an explicit empty value=[], not the default (None)
        if value == [] and key in self.fields: #i.e., if reduced to nothing
            self.rmverificationnode(profile,ftype) #remove what's there
        #Because of the line above, or other situation with no value or field:
        if not value and key not in self.fields: #if value, add field below
            return [] #return empty list to fill, don't add or remove
        #This is stored as a list in text, so return it to a python list:
        # if value:
        #     log.info(f"setting value {value} ({type(value)})")
        # else:
        #     log.info("getting value")
        if value is None: #don't send str(None)!
            v=self.fieldvalue(key)
        else:
            v=self.fieldvalue(key,value=str(value))
        # log.info(f"Set ‘{key}’ fieldvalue {str(value)} = {v}")
        if v: #fieldvalue returns None on no node
            v=xmlfns.stringtoobject(v) #must come and go to XML as string
            # log.info(f"verificationtextvalue returning {v=} ({type(v)=}; "
            #     f"set {value=})")
            return v
        else:
            # log.info(f"verificationtextvalue returning [] ({v=}; {type(v)=})")
            return []
    def getcvverificationkeys(self,ftype):
        profile=self.cvprofilevalue(ftype=ftype)
        if not profile or profile in ['Invalid']:
            # log.info(f"getcvverificationkeys returning w/o profile")
            return {},{} #verificationtextvalue fails on None profile
        counts={c:profile.count(c) for c in profile}
        actual=self.verificationtextvalue(profile,ftype)
        # log.info(f"Checking if {actual} covers {profile} profile.")
        #only split on last '='
        actualkeys={'='.join(i.split('=')[:-1]):i.split('=')[-1] for i in actual}
        # log.info(f"getcvverificationkeys: {self.id=}; {type(self.id)=}")
        # log.info(f"getcvverificationkeys: {counts=}; {type(counts)=}")
        # log.info(f"getcvverificationkeys: {actualkeys=}; {type(actualkeys)=}")
        return counts,actualkeys
    def cvverificationforcheck(self,ftype,check):
        counts,actualkeys=self.getcvverificationkeys(ftype)
        # try:
        # except TypeError:
        #     # print("Missing profile or verication dictionary; skipping")
        #     return
        if check in actualkeys:
            return actualkeys[check]
    def cvverificationdone(self,ftype):
        """This returns True if all segmental checks are finished."""
        counts,actualkeys=self.getcvverificationkeys(ftype)
        if not (counts and actualkeys):
            return
        for c in counts:
            for i in range(counts[c]):
                if not c+str(i+1) in actualkeys.keys():
                    # log.info(f"missing {c+str(i+1)} in {actualkeys} (at least)")
                    return
        # log.info("Looks Good!")
        return True
    def examplesforASRtraining(self):
        for location in self.examples: # each location should be here.
            example=self.examples[location]
            if example.hassoundfile():
                # log.info(f"Found soundfile {example.audiofileURL}")
                translation=example.textvaluebylang(self.db.analang)
                if translation:
                    # log.info(f"Ex {self.id}-{location} ready for ASR training")
                    # log.info(f"Found value for transcription in lang {analang}")
                    i=(example.audiofileURL,translation)
                    try:
                        r+=[i]
                    except:
                        r=[i]
        try:
            return r
        except (UnboundLocalError,NameError):
            return []
    def lexicalformsforASRtraining(self, no_verify_check=False, check=None):
        for ftype in self.ftypes: #includes pl and imp if there
            i=()
            if self.ftypes[ftype].hassoundfile():
                if check:# e.g., V1=?
                    value=self.cvverificationforcheck(ftype,check)
                else: #word form
                    value=self.ftypes[ftype].textvaluebylang(self.db.analang)
                    if not (no_verify_check or self.cvverificationdone(ftype)):
                        value=None
                if value:
                    # log.info(f"{self.id}-{ftype} ready for ASR training"
                    #                 f" (no_verify_check: {no_verify_check}; "
                    #                 f"check: {check})"
                    #             )
                    i=(self.ftypes[ftype].audiofileURL,value)
                    try: #catch each ftype for sense
                        r+=[i]
                    except:
                        r=[i]
        try:
            return r
        except (UnboundLocalError,NameError):
            return []
    def __init__(self, parent, node=None, **kwargs):
        kwargs['tag']='sense'
        Node.__init__(self, parent, node, **kwargs)
        self.entry=parent #make a common reference point for sense/entry
        FieldParent.__init__(self)
        self.getcawlline()
        self.sense=self
        self.id=self.get('id')
        self.psvalue() #set if there
        self.pssubclassvalue() #set if there
        """ftypes for pl and imp are set on three other occasions:
        1. Boot, if found on setting (for all entries)
        2. on setting/changing field name (for all entries)
        3. on creating a new field (for that entry)
        Otherwise, do not expect these to be there!
        """
        self.ftypes={'lx': self.entry.lx,
                    'lc': self.entry.lc
                    }
        self.getglosses()
        self.getdefinitions()
        self.getexamples()
        self.illustrationvalue() #set if there
        # log.info([i.textvalue() for i in self.glosses['en']])
        # log.info("Initialized sense for {}".format(self))
class Entry(Node,FieldParent): # what does "object do here?"
    """I have only converted nodes to classes as needed; other items
    have been left alone.
    """
    def getsenses(self):
        self.senses=[Sense(self,i) for i in self if i.tag == 'sense']
        try:
            self.sense=self.senses[0] #for when I really just need one
        except IndexError:
            self.sense=[]
            log.info(_("Removing entry with no senses: {guid}").format(guid=self.guid))
            return 1
    def getlx(self):
        self.lx=Lexeme(self,self.find('lexical-unit'))
        self.checkforsecondchild('lexical-unit')
    def getlc(self):
        self.lc=Citation(self,self.find('citation'))
        self.checkforsecondchild('citation')
    def getph(self):
        v=self.find('pronunciation')
        if v:
            self.ph=Pronunciation(self,v)
        self.checkforsecondchild('pronunciation')
    def lxvalue(self,value=None):
        return self.lx.textvaluebylang(self.db.analang,value)
    def lcvalue(self,value=None):
        return self.lc.textvaluebylang(self.db.analang,value)
    def plvalue(self,ftype,value=None):
        return self.fieldvalue(ftype,self.db.analang,value)
    def impvalue(self,ftype,value=None):
        return self.fieldvalue(ftype,self.db.analang,value)
    def phvalue(self,ftype,lang,value=None):
        try:
            assert self.ph.get('type') == ftype
            log.info(_("phonetic form is correct type ({type})").format(type=ftype))
        except AssertionError:
            log.error(_("Asked for ftype {type}, but found phonetic field which is {val}")
                    .format(type=ftype, val=self.ph.get('type')))
        except AttributeError:
            if value:
                # For now, this just takes the first one. We aren't using this.
                self.ph=Pronunciation(self,self.find('pronunciation'))
                self.ph.getsense()
                for sense in self.senses:
                    sense.ftypes['ph']=self.ph
                # prettyprint(self.imp)
                self.checkforsecondfieldbytype(ftype)
                self.getfields() #needed?
            else:
                return None
        return self.ph.textvaluebylang(lang,value)
    def copy_ph_form_to_lc(self):
        try:
            ph=self.ph.textvaluebylang(lang='wmg')
            self.lc.textvaluebylang(lang='wmg',value=ph)
        except Exception as e:
            log.info(_("Exception: ({error}; guid={guid})").format(error=e, guid=self.guid))
    def copy_ph_form_and_media_to_lc(self):
        try:
            wav=self.ph.find('media').get('href')
            ph=self.ph.textvaluebylang(lang='wmg')
            self.lc.textvaluebylang(lang=self.db.audiolang,value=wav)
            self.lc.textvaluebylang(lang='wmg',value=ph)
        except Exception as e:
            log.info(_("Exception: ({error}; guid={guid})").format(error=e, guid=self.guid))
    def __init__(self, parent, node=None, **kwargs):
        kwargs['tag']='entry'
        self.annotationlang=kwargs.pop('annotationlang','en')
        Node.__init__(self, parent, node, **kwargs)
        self.guid=self.get('guid')
        FieldParent.__init__(self)
        self.entry=self #make a common reference point for sense/entry
        # log.info(f"Entry {self.guid} init {[i for i in self]=}")
        self.getlx()
        self.getlc()
        self.getph()
        r=self.getsenses() #this needs lx and lc already
        if r: #If no senses, stop here
            log.info(_("Stopping here b/c no senses found."))
            return
        for l in ['lx','lc','ph']:
            if hasattr(self,l):
                getattr(self,l).getsense() #this needs senses already
        self.fields.update({
                    'lx':self.lx,
                    'lc':self.lc,
                    })
        if hasattr(self,'ph'):
            self.fields.update({'ph':self.ph})
        self.tone={}
class Language(object):
    def __init__(self, xyz):
        """define consonants and vowels here?regex's belong where?"""
        self.tree=et.parse(lift.languages[xyz]) #this parses the lift file into an entire ElementTree tree, for reading or writing the LIFT file.
        #self.object=Tree(filename)
        self.nodes=self.tree.getroot() #.parsed #This returns the root node of an ElementTree tree (the entire tree as nodes), to edit the XML.
        #self.tree=et.parse(lift)
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
            log.log(4,_("found: {val} (x{n}), looking for {what}")
                    .format(val=n[:1], n=len(n), what=what))
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
        # log.info("building {}, @dict:{}, @{}={}, on top of {}".format(tag,
        #                         attrs,liftattr,myattr, self.currentnodename()))
        b=tag
        if attrs is None:
            attrs={liftattr: myattr}
        for attr in attrs:
            if (None not in [attr,attrs[attr]] and attrs[attr] in self.kwargs
                                and self.kwargs[attrs[attr]] is not None):
                b+="[@{}={}]".format(attr,rx.escapeattr(self.kwargs[attrs[attr]]))
        if ((liftattr is None or (liftattr in self.kwargs #no lift attribute
                                and self.kwargs[liftattr] is None))
                and tag == 'text' and myattr in self.kwargs #text value to match
                                        and self.kwargs[myattr] is not None):
            b="[{}={}]".format(tag,rx.escapeattr(self.kwargs[myattr]))
            noseparator=True
            if tag == 'text' and tag in self.targettail:
                buildanother=True #the only way to get text node w/o value
        self.url+=[b]
        if noseparator:
            l=self.url
            self.url=[i for i in l[:len(l)-2]]+[''.join([i for i in l[len(l)-2:]])]
        else:
            self.level['cur']+=1
        self.level[self.getalias(tag)]=self.level['cur']
        log.log(4,_("Path so far: {url}").format(url=self.drafturl()))
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
    def form(self,value=None,lang=None,annodict={}):
        self.baselevel()
        #This holds the name of the kwarg key that holds the text value
        self.kwargs['value']=self.kwargs.get(value,None) #location and tonevalue
        if not lang and 'lang' in self.kwargs: #in case not called by parent
            lang='lang' #this is the kwargs key to use
        # log.info("form kwargs: {}, lang={}".format(self.kwargs,lang))
        self.build("form","lang",lang) #OK if lang is None
        if self.kwargs.get('annodict') and not annodict:
            annodict=self.kwargs.pop('annodict')
        if annodict:
            self.annotation(annodict)
        # log.info("Looking for {}".format(self.what))
        if self.kwargs['value'] or self.what == 'text':
            self.text("value")
        # self.bearchildrenof("form")
    def annotation(self,attrs={}):
        self.baselevel()
        if not attrs: #probably should never depend on this
            attrs={'name': 'annotationname'}
        if 'annotationvalue' in self.kwargs:
            attrs['value']='annotationvalue'
        self.build("annotation",attrs=attrs)
    def citation(self):
        self.baselevel()
        self.build("citation")
        if set(['lcannotationname','lcannotationvalue']) & set(self.kwargs):
            attrs={'name': 'lcannotationname'}
            if 'lcannotationvalue' in self.kwargs:
                attrs['value']='lcannotationvalue'
        else:
            attrs={}
        # self.form("lcform","lang",annodict=attrs)
        self.form("lcform","analang",annodict=attrs)
    def lexeme(self):
        self.baselevel()
        self.build("lexical-unit")
        if set(['lxannotationname','lxannotationvalue']) & set(self.kwargs):
            attrs={'name': 'lxannotationname'}
            if 'lxannotationvalue' in self.kwargs:
                attrs['value']='lxannotationvalue'
        else:
            attrs={}
        # self.form("lxform","lang",annodict=attrs)
        self.form("lxform","analang",annodict=attrs)
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
        self.bearchildrenof("ps")
    def pssubclass(self):
        """<trait name='{ps}-infl-class' value='{pssubclass}'"""
        log.log(4,_("Kwargs: {kwargs}").format(kwargs=self.kwargs))
        self.kwargs['pssubclassname']='{}-infl-class'.format(self.kwargs['ps'])
        attrs={'name': 'pssubclassname'}
        if 'pssubclass' in self.kwargs:
            self.kwargs['pssubclassvalue']='pssubclass'
            attrs['value']='pssubclassvalue'
        log.log(4,_("Attrs: {attrs}").format(attrs=attrs))
        self.trait(attrs)
    def gloss(self):
        self.baselevel()
        self.build("gloss","lang","glosslang")
        if 'gloss' in self.kwargs and self.kwargs['gloss']:
            self.text("gloss")
    def definition(self):
        self.baselevel()
        self.build("definition")
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
        # log.info("kwargs: {}".format(self.kwargs))
        if 'ftype' in self.kwargs:
            ftype=self.kwargs['ftype']
            if set([ftype+'annotationname',ftype+'annotationvalue']) & set(self.kwargs):
                attrs={'name': ftype+'annotationname'}
                if ftype+'annotationvalue' in self.kwargs:
                    attrs['value']=ftype+'annotationvalue'
            else:
                attrs={}
        elif 'lang' in self.kwargs:
                self.form(lang='lang')
        else:
            log.error(_("You asked for a field, without specifying ftype or "
                        "lang; not adding form fields."))
            return
        #This was causing duplicate form nodes for locationfield
        # self.form(ftype+"form","analang",annodict=attrs)
    def locationfield(self):
        self.baselevel()
        self.kwargs['ftype']='location'
        self.kwargs['formtext']='location'
        self.field()
        #This was causing duplicate form nodes
        #But not a needed one for 'example'
        self.form("location",'glosslang')
    def toneUFfield(self):
        self.baselevel()
        self.kwargs['ftype']='tone'
        """I assume we will never use sense/tonefield and example/tonefield
        in the same url..."""
        self.level['toneUFfield']=self.level['cur']+1 #so this won't repeat
        self.field()
        if 'toneUFvalue' in self.kwargs:
            self.kwargs['formtext']='toneUFvalue'
            self.form("toneUFvalue",'glosslang')
            self.kwargs['formtext']=None
        else: #don't force a text node with no text value
            self.kwargs['formtext']=None
            self.form(lang='glosslang')
    def tonefield(self):
        # log.info("Making tone field")
        self.baselevel()
        self.kwargs['ftype']='tone'
        self.level['tonefield']=self.level['cur']+1 #so this won't repeat
        self.field()
        if 'tonevalue' in self.kwargs:
            self.kwargs['formtext']='tonevalue'
            self.form("tonevalue",'glosslang')
            self.kwargs['formtext']=None
        else: #don't force a text node with no text value
            self.kwargs['formtext']=None
            self.form(lang='glosslang')
    def cawlfield(self):
        log.log(4,_("Making CAWL field"))
        self.baselevel()
        self.kwargs['ftype']='SILCAWL'
        self.level['cawlfield']=self.level['cur']+1 #so this won't repeat
        self.field()
        if 'cawlvalue' in self.kwargs:
            self.kwargs['formtext']='cawlvalue'
            self.form("cawlvalue",'glosslang')
            self.kwargs['formtext']=None
        else: #don't force a text node with no text value
            self.kwargs['formtext']=None
            self.form(lang='glosslang')
    def morphtype(self,attrs={}):
        self.kwargs['morphtypename']='morph-type'
        if 'morphtype' in self.kwargs: #This is needed
            attrs={'name':"morphtypename",'value':'morphtype'}
            self.trait(attrs) # <trait name="morph-type" value="stem" />
    def illustration(self):
        # log.info("Making illustration")
        self.baselevel()
        self.build("illustration")
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
                log.error(_("Sorry, I can't tell what form to pass to this field;"
                            "\nWhat is its parent?"))
                return
            else:
                args=self.formargsbyparent(parent)
        elif nodename == 'text': #args:value,lang
            args=['formtext'] #This needs to be smarter; different kinds of formtext
        else:
            args=list()
        for arg in args:
            log.log(4,_("show arg: {arg}").format(arg=arg))
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
        log.error(_("LiftURL is trying to make a lift node; this should never "
                "happen; exiting!"))
        exit()
    def bearchildrenof(self,parent):
        # log.info("bearing children of {} ({})".format(parent,
        #                                                 self.children[parent]))
        for i in self.children[parent]:
            # log.info("bearchildrenof i: {}".format(i))
            self.maybeshow(i,parent)
    def levelup(self,target):
        while self.level.get(target,self.level['cur']+1) < self.level['cur']:
            self.parent()
    def baselevel(self):
        # log.info("baselevel for {}".format(self.callerfn()))
        # log.info("@{}".format(self.url))
        parents=self.parentsof(self.callerfn())
        for target in parents: #self.levelsokfor[self.callerfn()]: #targets: #targets should be ordered, with best first
            target=target.split('/')[-1] #.split('[')[0] #just the last level tag
            # log.info("tag of target: {}".format(target))
            if target in self.level and self.level[target] == self.level['cur']:
                # log.info("level of target: {}".format(self.level[target]))
                # log.info("current level: {}".format(self.level['cur']))
                # log.info("levels: {}".format(self.level))
                return #if we're on an acceptable level, just stop
            elif target in self.level:
                # log.info("level of target (2): {}".format(self.level[target]))
                # log.info("current level: {}".format(self.level['cur']))
                self.levelup(target)
                return
            elif parents.index(target) < len(parents)-1:
                # log.info("level {} not in {}; checking the next one...".format(
                #                                             target,self.level))
                continue
            else:
                val_url = self.drafturl()
                log.error(_("last level {target} (of {parents}) not in {level}; this is a problem!")
                        .format(target=target, parents=parents, level=self.level))
                log.error(_("this is where we're at: {kwargs}\n  {url}")
                        .format(kwargs=self.kwargs, url=val_url))
                exit()
    def maybeshowtarget(self,parent):
        # parent here is a node ancestor to the current origin, which may
        # or may not be an ancestor of targethead. If it is, show it.
        f=self.getfamilyof(parent,x=[])
        log.log(4,_("Maybeshowtarget: {parent} (family: {family})").format(parent=parent, family=f))
        if self.targethead in f:
            if parent in self.level:
                log.log(4,_("Maybeshowtarget: leveling up to {parent}").format(parent=parent))
                self.levelup(parent)
            else:
                log.log(4,_("Maybeshowtarget: showing {parent}").format(parent=parent))
                self.show(parent)
            self.showtargetinhighestdecendance(parent)
            return True
    def showtargetinlowestancestry(self,nodename):
        log.log(4,_("Running showtargetinlowestancestry for {head}/{tail} on {node}")
                .format(head=self.targethead, tail=self.targettail, node=nodename))
        #If were still empty at this point, just do the target if we can
        if nodename == [] and self.targethead in self.children[self.basename]:
            self.show(self.targethead)
            return
        gen=nodename
        g=1
        r=giveup=False
        while not r and giveup is False:
            log.log(4,_("Trying generation {g}").format(g=g))
            gen=self.parentsof(gen)
            for p in gen:
                r=self.maybeshowtarget(p)
                if r:
                    break
            g+=1
            if g>10:
                giveup=True
        if giveup is True:
            log.error(_("Hey, I've looked back {g} generations, and I don't see "
                    "an ancestor of {head} (target) which is also an ancestor of "
                    "{node} (current node).").format(g=g, head=self.targethead, node=nodename))
    def showtargetinhighestdecendance(self,nodename):
        log.log(4,_("Running showtargetinhighestdecendance for {head} on {node}")
                .format(head=self.targethead, node=nodename))
        if nodename in self.children:
            children=self.children[nodename]
        else:
            log.log(4,_("Node {node} has no children, so not looking further for "
                        "descendance.").format(node=nodename))
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
        log.log(4,_("Looking for {head} in children of {node}: {children}")
                .format(head=self.targethead, node=nodename, children=children))
        log.log(4,_("Grandchildren of {node}: {grandchildren}")
                .format(node=nodename, grandchildren=grandchildren))
        log.log(4,_("Greatgrandchildren of {node}: {greatgrandchildren}")
                .format(node=nodename, greatgrandchildren=greatgrandchildren))
        if self.targethead in children:
            log.log(4,_("Showing '{head}', child of {node}")
                    .format(head=self.targethead, node=nodename))
            self.show(self.targethead,nodename)
        elif self.targethead in grandchildren:
            log.log(4,_("Found target ({head}) in grandchildren of {node}: {grandchildren}")
                    .format(head=self.targethead, node=nodename, grandchildren=grandchildren))
            for c in children:
                if c in self.children and self.targethead in self.children[c]:
                    log.log(4,_("Showing '{c}', nearest ancenstor").format(c=c))
                    self.show(c,nodename) #others will get picked up below
                    self.showtargetinhighestdecendance(c)
        elif self.targethead in greatgrandchildren:
            log.log(4,_("Found target ({head}) in gr8grandchildren of {node}: {grandchildren}")
                    .format(head=self.targethead, node=nodename, grandchildren=greatgrandchildren))
            for c in children:
                for cc in grandchildren:
                    if cc in self.children and self.targethead in self.children[cc]:
                        log.log(4,_("Showing '{c}', nearest ancenstor").format(c=c))
                        self.show(c,nodename) #others will get picked up below
                        self.showtargetinhighestdecendance(c)
        elif self.targethead in gggrandchildren:
            log.log(4,_("Found target ({head}) in gggrandchildren of {node}: {grandchildren}")
                    .format(head=self.targethead, node=nodename, grandchildren=gggrandchildren))
            for c in children:
                for cc in grandchildren:
                    for ccc in greatgrandchildren:
                        if ccc in self.children and self.targethead in self.children[ccc]:
                            log.log(4,_("Showing '{c}', nearest ancenstor").format(c=c))
                            self.show(c,nodename) #others will get picked up below
                            self.showtargetinhighestdecendance(c)
        else:
            log.error(_("Target not found in children, grandchildren, or "
                        "greatgrandchildren!"))
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
            log.log(4,_("{target} : {bits}").format(target=self.target, bits=self.targetbits))
            self.targethead=self.targetbits[0]
            self.targettail=self.targetbits[1:]
        else:
            self.targethead=self.target
            self.targetbits=[self.targethead,]
            self.targettail=[]
        if 'form' in self.targethead and 'form' not in self.children[
                                                self.getalias(self.basename)]:
            log.error(_("Looking for {head} as the head of a target is going to "
            "cause problems, as it appears in too many places, and is likely "
            "to not give the desired results. Fix this, and try again. (whole "
            "target: {target})").format(head=self.targethead, target=self.target))
            exit()
    def tagonly(self,nodename):
        return nodename.split('[')[0]
    def currentnodename(self):
        last=self.url[-1:]
        if last:
            n=self.tagonly(last[0])
            return self.getalias(n)
    def unalias(self,nodename):
        """This returns the names used in the LIFT URL"""
        return self.alias.get(nodename,nodename)
    def getalias(self,nodename):
        """This returns the names I typically use"""
        if nodename in self.alias.values():
            for k in self.alias:
                if self.alias[k] == nodename:
                    return k
        return nodename #else
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
        # log.info("URL (before {} target): {}".format(self.target,self.drafturl()))
        if self.getalias(self.targethead) not in self.level: #If the target hasn't been made yet.
            # log.info(self.url)
            i=self.currentnodename()
            # log.info("URL base: {}; i: {}".format(self.basename,i))
            if i is None: #if it is, skip down in any case.
                i=self.basename
            # log.info("URL bit list: {}; i: {}".format(self.url,i))
            if type(i) == list:
                i=i[0] #This should be a string
            f=self.getfamilyof(i,x=[])
            # log.info("Target: {}; {} family: {}".format(self.targethead,i,f))
            if self.targethead in f:
                self.showtargetinhighestdecendance(i) #should get targethead
                    # return #only do this for the first you find (last placed).
            else:#Continue here if target not a current level node decendent:
                self.showtargetinlowestancestry(i)
            # Either way, we finish by making the target tail, and leveling up.
        if self.targettail is not None:
            # log.info("Adding targettail {} to url: {}".format(self.targettail,
            #                                                 self.drafturl()))
            for b in self.targettail:
                # log.info("Adding targetbit {} to url: {}".format(b,self.drafturl()))
                n=self.targetbits.index(b)
                bp=self.tagonly(self.targetbits[n-1]) #.split('[')[0]#just the node, not attrs
                afterbp=self.drafturl().split(self.unalias(bp))
                # log.info("b: {}; bp: {}; afterbp: {}".format(b,bp,afterbp))
                # log.info("showing target element {}: {} (of {})".format(n,b,bp))
                if (len(afterbp) <=1 #nothing after parent
                        or self.unalias(b) not in afterbp[-1] #this item not after parent
                        or (b in self.level and
                            bp in self.level and
                            self.level[b]!=self.level[bp]+1)): #this not child of parent
                    # log.info("showing target element {}: {} (of {})".format(n,b,bp))
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
        log.info(_("Basic usage of this class includes the following kwargs:\n"
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
                "\ttonevalue: value of an example tone group (from sorting)\n"))
    def shouldshow(self,node):
        # This fn is not called by showtargetinhighestgeneration or maketarget
        if node in self.level:
            return False
        elif node == self.targethead: #do this later
            return False
        c=self.getfamilyof(node,x=[])
        if self.attrneeds(node,c):
            # log.info("attrneeds {}; {}".format(node,c))
            return True
        elif self.kwargsneeds(node,c):
            # log.info("kwargsneeds {}; {}".format(node,c))
            return True
        elif self.pathneeds(node,c):
            # log.info("pathneeds {}; {}".format(node,c))
            return True
        else:
            return False
    def getfamilyof(self,node,x):
        # log.info("running kwargshaschildrenof.gen on '{}'".format(node))
        if type(node) is str:
            node=[node]
        for i in node:
            if i not in x:
                # log.info("running kwargshaschildrenof.gen on '{}'".format(i))
                ii=self.children.get(i)
                # log.info("Found '{}' this time!".format(ii))
                if ii and ii not in x:
                    x=self.getfamilyof(ii,x)
                    x+=ii
        return x
    def pathneeds(self,node,children):
        path=self.path
        # log.info("Path: {}; children: {}".format(path,children))
        if node in path and node not in self.level:
            # log.info("Parent ({}) in path: {}".format(node,path))
            return True
        if children != []:
            childreninpath=set(children) & set(path)
            if childreninpath != set():
                pathnotdone=childreninpath-set(self.level)
                if pathnotdone != set():
                    if not pathnotdone-set(['annotation']) and ( #only anno...
                                    node not in ['form','annotation']
                                                         ):
                        return #otherwise this brings in way too much
                    # log.info("Found descendant of {} in path, which isn't "
                    #     "already there: {}".format(node, pathnotdone))
                    return True
        return False
    def attrneeds(self,node,children):
        nodes=[node]+children
        # log.info("looking for attr(s) of {} in {}".format(nodes,self.attrs))
        # log.info("Building on url {}".format(self.drafturl()))
        for n in nodes:
            if n in self.attrs and not (n in self.path or n in self.target):
                # log.info("looking for attr(s) of {} in {}".format(n,self.attrs))
                if n == 'annotation' and node not in ['form','annotation']:
                    return #otherwise this brings in way too much
                common=set(self.attrs[n])&set(list(self.kwargs)+[self.what])
                if common != set():
                    # log.info("Found attr(s) {} requiring {}".format(common,n))
                    return True
            # elif n in self.path or n in self.target:
            #     log.info("found {} in path or target; skipping kwarg check.".format(n))
            # else:
            #     log.info("{} not found in {}".format(n,self.attrs.keys()))
        return False
    def kwargsneeds(self,node,children):
        if node in self.kwargs:
            # log.info("Parent ({}) in kwargs: {}".format(node,self.kwargs))
            return True
        elif children != []:
            for child in children:
                if child in self.path or child in self.target:
                    # log.info("found {} in path or target; skipping kwarg check.".format(child))
                    return
            # log.info("Looking for descendants of {} ({}) in kwargs: {}".format(
            #                                     node,children,self.kwargs))
            childreninkwargs=set(children) & set(self.kwargs)
            if childreninkwargs != set():
                # log.info("Found descendants of {} in kwargs: {}".format(node,
                #                                             childreninkwargs))
                pathnotdone=childreninkwargs-set(self.level)
                if pathnotdone != set():
                    # log.info("Found descendants of {} in kwargs, which aren't "
                    #                 "already there: ".format(node,pathnotdone))
                    return True
        return False
    def callerfn(self):
        return sys._getframe(2).f_code.co_name #2 gens since this is a fn, too
    def parentsof(self,nodenames):
        # log.info("children: {}".format(self.children.items()))
        # log.info("key pair: {}".format(
        #         ' '.join([str(x) for x in self.children.items()
        #                             if nodenames in x[1]])))
        p=[]
        if type(nodenames) != list:
            nodenames=[nodenames]
        for nodename in nodenames:
            i=[x for x,y in self.children.items() if nodename in y]
            i.reverse()
            p+=i
        plist=list(dict.fromkeys(p))
        # log.info("parents of {}: {}".format(nodenames,plist))
        return plist
    def setattrsofnodes(self):
        """These are atttributes we ask for, which require the field. This
        should not be used for an attribute that requires either of two fields
        (like glosslang, which doesn't require both gloss *and* definition)"""
        self.attrs={}
        self.attrs['entry']=['guid']
        self.attrs['morphtype']=['morphtype']
        self.attrs['sense']=['senseid']
        self.attrs['pssubclass']=['pssubclass']
        self.attrs['tonefield']=['tonevalue']
        self.attrs['toneUFfield']=['toneUFvalue']
        self.attrs['locationfield']=['location']
        self.attrs['cawlfield']=['fvalue']
        self.attrs['annotation']=['annotationname','annotationvalue']
        self.attrs['citation']=['lcannotationname','lcannotationvalue']
        self.attrs['lexeme']=['lxannotationname','lxannotationvalue']
        # glosslang may be asking for a definition...
        # self.attrs['gloss']=['glosslang'] #do I want this?
    def setchildren(self):
        """These are the kwargs that imply a field. field names also added to
        ensure that depenents get picked up.
        """
        # use self.alias.get(tag,tag) where needed!
        self.children={}
        self.children['lift']=['entry']
        self.children['entry']=['lexeme','morphtype','pronunciation','sense',
                                'field',
                                'citation','trait']
        self.children['sense']=['ps','definition','gloss','illustration',
                                'example','toneUFfield','cawlfield','field'
                                            ]
        self.children['ps']=['pssubclass','trait']
        self.children['example']=['form','translation','locationfield',
                                            'tonefield','field']
        self.children['field']=['form']
        self.children['lexeme']=['form']
        self.children['definition']=['form']
        self.children['citation']=['form']
        self.children['form']=['text','annotation']
        self.children['gloss']=['text']
        self.children['pronunciation']=['field','trait','form']
        self.children['translation']=['form']
    def setaliases(self):
        self.alias={}
        self.alias['lexeme']='lexical-unit'
        self.alias['morphtype']="trait[@name='morph-type']"
        self.alias['senseid']='id'
        self.alias['ps']='grammatical-info'
        if 'ps' in self.kwargs: #this isn't used without ps
            self.alias['pssubclass']="trait[@name='{}-infl-class']".format(
                                                            self.kwargs['ps'])
        self.alias['fieldtype']='ftype'
        self.alias['toneUFfield']="field[@type='tone']"
        self.alias['tonefield']="field[@type='tone']"
        self.alias['locationfield']="field[@type='location']"
    def __init__(self, *args,**kwargs):
        self.base=kwargs['base']
        self.kwargs=kwargs
        self.setaliases()
        # log.info("init kwargs: {}".format(self.kwargs))
        basename=self.basename=self.getalias(self.base.tag)
        super(LiftURL, self).__init__()
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
        log.log(4,_("Making Target now."))
        self.maketarget()
        self.makeurl()
        log.log(4,_("Final URL: {url}").format(url=self.url))
        # self.printurl()
"""Functions I'm using, but not in a class"""
def pylanglegacy(analang):
     return 'py-'+analang
def pylanglegacy2(analang):
     return analang+'-py'
def pylang(analang):
     return analang+'-x-py'
def profilelang(analang):
     return analang+'-x-cvprofile'
def quote(x):
    return "‘"+str(x)+"’"
def textornone(x):
    try:
        return x.text
    except AttributeError:
        return x
def setlistsofanykey(dict):
    #This reduces a dictionary with lists as values to one list, without dups
    return set([i for l in dict for i in dict[l]])
def nodehasform(node):
    for child in node:
        if child.tag == 'form':
            return True
def atleastoneexamplehaslangformmissing(examples,lang):
    for example in examples:
        if examplehaslangform(example,lang) == False:
            return True
    return False
def examplehaslangform(example,lang):
    if example.find("form[@lang='{}']".format(lang)):
        log.debug(_("langform found!"))
        return True
    log.debug(_("No langform found!"))
    return False
def buildurl(url):
    val_u0 = url[0]
    log.log(2,_('BaseURL: {url}').format(url=val_u0))
    val_u1 = url[1]
    log.log(2,_('Arguments: {args}').format(args=val_u1))
    return url[0].format(**url[1]) #unpack the dictionary
def removenone(url):
    """Remove any attribute reference whose value is 'None'. I only use
    '@name="location"' when using @value, so also remove it if @value=None."""
    """Confirm that r is correct here"""
    nonattr=re.compile(r'(\[@name=\'location\'\])*\[[^\[]+None[^\[]+\]')
    newurl=nonattr.sub('',url)
    return newurl
def getnow():
    return datetime.datetime.now(datetime.UTC).isoformat()[:-7]+'Z'
    # return datetime.datetime.utcnow().isoformat()[:-7]+'Z'
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
    # filename="/home/kentr/Assignment/Tools/WeSay/dkx/MazHidi_Lift.lift"
    # filename="/home/kentr/Assignment/Tools/WeSay/bse/SIL CAWL Wushi.lift"
    # filename="/home/kentr/Assignment/Tools/WeSay/bfj/bfj.lift"
    # filename="/home/kentr/Assignment/Tools/WeSay/blm-x-rundu/blm-x-rundu.lift"
    # filename="/home/kentr/Assignment/Tools/WeSay/gnd/gnd.lift"
    # filename="/home/kentr/Assignment/Tools/WeSay/cky/Mushere Exported AZT file.lift"
    # filename="/home/kentr/bin/raspy/azt/userlogs/SILCAWL.lift_backupBeforeLx2LcConversion"
    # filename="/home/kentr/bin/raspy/azt/userlogs/SILCAWL.lift"
    # filename="/home/kentr/bin/raspy/azt/userlogs/SILCAWL_test.lift"
    # filename="/home/kentr/Assignment/Tools/WeSay/tiv/tiv.lift"
    # filename="/home/kentr/Assignment/Tools/WeSay/ETON_propre/Eton.lift"
    # filename="/home/kentr/Assignment/Tools/WeSay/tsp/TdN.lift"
    # filename="/home/kentr/Assignment/Tools/WeSay/tsp/TdN.lift_2021-12-06.txt"
    # filename="/home/kentr/Assignment/Tools/WeSay/eto/eto.lift"
    # filename="/home/kentr/Assignment/Tools/WeSay/eto/Eton.lift"
    # filename="/home/kentr/Assignment/Tools/WeSay/bqg/Kusuntu.lift"
    # filename="/home/kentr/Assignment/Tools/WeSay/bo/bo.lift"
    # filename="/home/kentr/Assignment/Tools/WeSay/wmg/wmg.lift"
    # filename="/home/kentr/Assignment/Tools/WeSay/Demo_en/Demo_en.lift"
    filename="/home/kentr/Assignment/Tools/WeSay/lol-x-his30103/lol-x-his30253.lift"
    import glob 
    filenames=glob.glob("/home/kentr/Assignment/Tools/WeSay/*-x-*/*.lift")
    lifts={}
    for filename in filenames:
        lifts[filename]=LiftXML(filename)
    for filename in filenames:
        lifts[filename].report_counts()
    exit()
    # filename="/home/kentr/Assignment/Tools/WeSay/Demo_gnd/gnd.lift"
    # filename="/home/kentr/bin/raspy/azt/SILCAWL/SILCAWL.lift"
    print(time.time())
    def writetofile(name):
        f = open(str(name)+'.txt', 'w', encoding='utf-8') # to append, "a"
        f.write(prettyprint(lift.nodes))
        f.close()
    lift.report_counts()
    # loc="Imperative"
    # formvalue="give!"
    # lang="en"
    # transvalue="donnez!"
    # translang='fr'
    # tonevalue='16'
    # frame={'field':'pl',
	# 	'en':'__s',
	# 	'swh':'__',
	# 	'fr':'__es'}
    # ftype='pl'
    # for ps in lift.sensesbyps_profile:
    #     for profile in lift.sensesbyps_profile[ps]:
    #         print(lift.sensesbyps_profile[ps][profile])
    #         print(f"{profile} in lift.ps_profiles[{ps}]: {profile in lift.ps_profiles[ps]}")
    # for ps in lift.ps_profiles:
    #     for profile in lift.ps_profiles[ps]:
    #         print('self.ps_profiles',ps,profile)
    #         print(lift.sensesbyps_profile[ps][profile])
    # for profile_dict in lift.sensesbyps_profile.values():
    #     for sense_list in profile_dict.values():
    #         for sense in sense_list:
    # lift.senses:
    # for ps in lift.sensesbyps_profile:
    #     # print([i.id for i in lift.sensesbyps_profile[ps][None] if i])
    #     # continue
    #     for profile,v in lift.sensesbyps_profile[ps].items():
    #         print(f"Found {len(v)} senses")
    #         for sense in lift.sensesbyps_profile[ps][profile]:
    #             print("working on sense",sense.id)
    #             i,o=sense.getcvverificationkeys('lc')
    #             print(o,type(o),[type(i) for i in o])
    # print('annotation:',lift.annotation_values_by_ps_profile())
    # print('verification:',lift.verification_values_by_ps_profile())
    # for s in lift.senses:
    #     if s.psvalue() == 'Noun' and s.cvprofilevalue() == 'CVCV':
    #         s.annotationvaluebyftypelang('lc','wmg','C1',value='')
    #         value=s.annotationvaluebyftypelang('lc','wmg','C1')
    #         log.info(f"Found noun at {s.id} w/C1=‘{value}’")
    # for e in lift.entries:
    #     e.copy_ph_form_to_lc()
    # lift.convertxtoy(lang='bo',fromtag='gloss', totag='citation')
    # sense=lift.sensedict['daytime_b27c251c-090e-4427-aa86-22b745409f8d']
    # sense=lift.sensedict['body_791094f2-a82b-4650-81d8-c3b6145d2be4']
    # sense=lift.sensedict['head_a8516acf-606c-4796-8fed-75b0c0f2c583']
    # sense=lift.sensedict['forehead_3e600f7e-74a3-4761-9bc3-09f3f01cd98b']
    # for sense in ['head_a8516acf-606c-4796-8fed-75b0c0f2c583',
    #                 'forehead_3e600f7e-74a3-4761-9bc3-09f3f01cd98b',
    #                 "voice box, larynx, Adam's apple_931554d7-b054-4f75-894c-2c28e2c6121f"]:
    #     sense=lift.sensedict[sense]
    #     print(sense.collectionglosses)
    # exit()
    # sense=lift.senses[0]
    # print(sense.cawln)
    # lift.convert_langtag('lol-x-his30253','lol-x-his30103')
    # lift.convert_langtag('en','en-US')
    # lift.convert_langtag('pt','en-US')
    # lift.convert_langtag('ha','en-US')
    # lift.convert_langtag('es','en-US')
    # lift.convert_langtag('xyz','en-US')
    # lift.convert_langtag('en','fr')
    # lift.convert_langtag('en','en')
    # lift.convert_langtag('ha-CL','en-US')
    # lift.convert_langtag('id','en-US')

    # lift.write()
    # exit()
