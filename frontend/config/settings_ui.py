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
from frontend import ui_tkinter as ui
from utilities.utilities import *
from io_put import lift
from utilities import file, htmlfns
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
import migration
import settings


def __getattr__(name):
    # Lazy load globals from main
    if name in ('program', 'counts', 'me', '_', 'ErrorNotice', 'askerror', 'sysrestart', 'pythonmodules', 'findexecutable', 'main', 'testversion', 'reverttomain', 'buttonwraplength', 'regexdict', 'interfacelang', 'nowruntime', 'callerfn', 'logfinished', 'nn', 'unlist', 'xlp', 'rx', 'exampletype', 'dictofchilddicts', 'dictscompare', 'flatten', 'grouptype', 't', 'openweburl', 'isinterneturl', 'scaleimageifthere', 'loadCAWL', 'saveimagefile', 'ImageFrame', 'TranscribeC', 'TranscribeV', 'TranscribeS', 'ResultWindow', 'Multislice', 'Multicheck', 'Tone', 'Segments', 'ToneFrames', 'CheckParameters', 'Glosslangs', 'Senses', 'WordCollection', 'Parse', 'Sort', 'HasMenus', 'Menus', 'StatusFrame', 'TaskDressing', 'TaskChooser', 'Repository', 'Mercurial', 'Git', 'GitReadOnly', 'Analysis', 'SliceDict', 'StatusDict', 'ExampleDict', 'DictbyLang', 'Settings', 'Entry', 'updateazt', 'LiftChooser', 'SortGroupButtonFrame'):
        import main
        return getattr(main, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

# Mirror main globals lazily to allow bare-name access
for name in ('program', 'counts', 'me', '_', 'ErrorNotice', 'askerror', 'sysrestart', 'pythonmodules', 'findexecutable', 'main', 'testversion', 'reverttomain', 'buttonwraplength', 'regexdict', 'interfacelang', 'nowruntime', 'callerfn', 'logfinished', 'nn', 'unlist', 'xlp', 'rx', 'exampletype', 'dictofchilddicts', 'dictscompare', 'flatten', 'grouptype', 't', 'openweburl', 'isinterneturl', 'scaleimageifthere', 'loadCAWL', 'saveimagefile', 'ImageFrame', 'TranscribeC', 'TranscribeV', 'TranscribeS', 'ResultWindow', 'Multislice', 'Multicheck', 'Tone', 'Segments', 'ToneFrames', 'CheckParameters', 'Glosslangs', 'Senses', 'WordCollection', 'Parse', 'Sort', 'HasMenus', 'Menus', 'StatusFrame', 'TaskDressing', 'TaskChooser', 'Repository', 'Mercurial', 'Git', 'GitReadOnly', 'Analysis', 'SliceDict', 'StatusDict', 'ExampleDict', 'DictbyLang', 'Settings', 'Entry', 'updateazt', 'LiftChooser', 'SortGroupButtonFrame'):
    if name not in globals():
        globals()[name] = LazyGlobal(name)

class Settings(object):
    """docstring for Settings."""
    def interfacelangwrapper(self,choice=None,window=None):
        # log.info(f"going to set interface lang {choice}")
        if choice:
            interfacelang(choice) #change the UI *ONLY*; no object attributes
            self.set('interfacelang',choice,window) #set variable for the future
            self.langnames() #relocalize
            self.program.taskchooser.mainwindowis.status.makeui()
            self.storesettingsfile() #>xyz.CheckDefaults.py
            #because otherwise, this stays as is...
            self.program.taskchooser.mainwindowis.maketitle()
        else:
            return interfacelang()
    def settingsbyfile(self):
        #Here we set which settings are stored in which files
        self.settings={'defaults':{
                            'file':'defaultfile',
                            'attributes':['analang',
                                'glosslangs',
                                'audiolang',
                                'ps',
                                'profile',
                                'cvt',
                                'check',
                                'regexCV',
                                'additionalps',
                                'entriestoshow',
                                'additionalprofiles',
                                'interfacelang',
                                'examplespergrouptorecord',
                                'adnlangnames',
                                'maxpss',
                                'showdetails',
                                'maxprofiles',
                                'menu',
                                'mainrelief',
                                'fontthemesmall',
                                'secondformfield',
                                'soundsettingsok',
                                'buttoncolumns',
                                'showoriginalorthographyinreports',
                                'lowverticalspace',
                                'giturls',
                                'hgurls',
                                'aztrepourls',
                                'minimumwordstoreportUFgroup',
                                'askedlxtolc',
                                'start_at_entry',
                                'end_at_entry',
                                'writeeverynwrites'
                                ]},
            'profiledata':{
                                'file':'profiledatafile',
                                'attributes':[
                                    'analang',
                                    'ftype',
                                    'distinguish',
                                    'interpret',
                                    'polygraphs',
                                    # 'profilecounts',
                                    'scount',
                                    'sextracted',
                                    ]},
            'status':{
                                'file':'statusfile',
                                'attributes':['status']},
            'adhocgroups':{
                                'file':'adhocgroupsfile',
                                'attributes':['adhocgroups']},
            'soundsettings':{
                                'file':'soundsettingsfile',
                                'attributes':['sample_format',
                                            'fs',
                                            'audio_card_in',
                                            'audio_card_out',
                                            'asr_kwargs',
                                            'asr_repos'
                                            ]},
            'alphabet':{
                                'file':'alphabetsettingsfile',
                                'attributes':[
                                            'status',
                                            'glyphdict',
                                            'alphabet_order',
                                            'alphabet_ncolumns',
                                            'alphabet_chart_title',
                                            'alphabet_exids',
                                            'alphabet_pagesize',
                                            'glyph_members',
                                            'glyphs_distinguished',
                                            'alphabet_copyright'
                                        ]},
            'contributors':{
                                'file':'contributorsfile',
                                'attributes':['contributors']},
            'toneframes':{
                                'file':'toneframesfile',
                                'attributes':['toneframes']}
                                }
    def settingsfile(self,setting):
        fileattr=self.settings[setting]['file']
        legacy=fileattr+'_legacy'
        if (hasattr(self,legacy) and file.exists(getattr(self,legacy))):
            file.move(getattr(self,legacy), getattr(self,fileattr))
        if hasattr(self,fileattr):
            return getattr(self,fileattr)
        else:
            log.error(_("No file name for setting {setting}!").format(setting=setting))
    def loadandconvertlegacysettingsfile(self,setting='defaults'):
        #This should be removed at some point Only used when find old file NAME
        savefile=self.settingsfile(setting)
        legacy=savefile.with_suffix('.py')
        log.info(_("Going to make {legacy_name} into {savefile}").format(legacy_name=legacy,savefile=savefile))
        if setting == 'soundsettings':
            self.soundsettings=sound.SoundSettings()
            o=self.soundsettings
        else:
            o=self
        oldnames={'cvt':'type',
                    'check':'name',
                    'group':'subcheck'
                    }
        try:
            log.debug(_("Trying for {setting} settings in {legacy_name}").format(setting=setting, legacy_name=legacy))
            spec = importlib.util.spec_from_file_location(setting,legacy)
            module = importlib.util.module_from_spec(spec)
            sys.modules[setting] = module
            spec.loader.exec_module(module)
            for s in self.settings[setting]['attributes']:
                if s in oldnames and hasattr(module,oldnames[s]):
                    setattr(o,s,getattr(module,oldnames[s]))
                    log.info(_("Imported and upgraded {s}/{old}: {val}").format(
                                                    s=s,old=oldnames[s],val=getattr(o,s)))
                elif hasattr(module,s):
                    setattr(o,s,getattr(module,s))
                    log.info(_("Imported {s}: {val}").format(s=s,val=getattr(o,s)))
                else:
                    log.info(_("Attribute {s} not found").format(s=s))
            log.info(_("Importing {setting} settings done.").format(setting=setting))
        except Exception as e:
            log.error(_("Problem importing {legacy} ({error})").format(legacy=legacy,error=e))
        # b/c structure changed:
        if 'glosslangs' in self.settings[setting]['attributes']:
            self.glosslangs=[]
            for lang in ['glosslang','glosslang2']:
                if hasattr(module,lang):
                    self.glosslangs.append(getattr(module,lang))
                    try:
                        delattr(self,lang) #because this would be made above
                    except AttributeError:
                        log.info(_("attribute {lang} doesn't seem to be there").format(lang=lang))
        dict1=self.makesettingsdict(setting=setting)
        self.storesettingsfile(setting=setting) #do last
        self.loadsettingsfile(setting=setting) #verify write and read
        dict2=self.makesettingsdict(setting=setting)
        """Now we verify that each value read the same each time"""
        for s in dict1:
            if s in dict2 and str(dict1[s]) == str(dict2[s]):
                log.info(_("Attribute {s} verified as {val1}={val2}").format(s=s,
                                            val1=str(dict1[s]), val2=str(dict2[s])))
            elif s in dict2:
                log.error(_("Problem with attribute {s}; {val1}≠{val2}").format(s=s,
                                            val1=str(dict1[s]), val2=str(dict2[s])))
            else:
                log.error(_("Attribute {s} didn't make it back").format(s=s))
                log.error(_("You should send in an error report for this."))
                exit()
        log.info(_("Settings file {legacy} converted to {savefile}, with each value verified.")
                .format(legacy=legacy,savefile=savefile))
        if setting == 'soundsettings':
            self.soundsettings.pyaudio.stop() # when done here
    def settingsfilecheck(self):
        """We need the namebase variable to make filenames for files
        that will be imported as python modules. To do that, they need
        to not have periods (.) in their filenames. So we take the base
        name from the lift file, and replace periods with underscores,
        to make our modules basename."""
        self.liftnamebase=rx.pymoduleable(file.getfilenamebase(
                                                            self.liftfilename))
        # re.sub('\.','_', str(
        basename=file.getdiredurl(self.directory,self.liftnamebase)
        self.defaultfile_legacy=basename.with_suffix(f'.CheckDefaults.ini')
        self.defaultfile=basename.with_suffix(f'.{self.program.source_repo.username}'
                                                f'.{self.program.hostname}'
                                                '.CheckDefaults.ini')
        self.toneframesfile=basename.with_suffix(".ToneFrames.dat")
        self.statusfile=basename.with_suffix(".VerificationStatus.dat")
        self.profiledatafile=basename.with_suffix(".ProfileData.dat")
        self.adhocgroupsfile=basename.with_suffix(".AdHocGroups.dat")
        self.contributorsfile=basename.with_suffix(".Contributors.ini")
        self.soundsettingsfile_legacy=basename.with_suffix(".SoundSettings.ini")
        self.soundsettingsfile=basename.with_suffix(f'.{self.program.source_repo.username}'
                                                    f'.{self.program.hostname}'
                                                    ".SoundSettings.ini")
        self.alphabetsettingsfile=basename.with_suffix(".Alphabet.ini")
        self.settingsbyfile() #This just sets self.settings
        for setting in self.settings:
            savefile=self.settingsfile(setting)#self.settings[setting]['file']
            if not file.exists(savefile):
                log.debug(_("{file} doesn't exist!").format(file=savefile))
                legacy=savefile.with_suffix('.py')
                if file.exists(legacy):
                    log.debug(_("But legacy file {legacy} does; converting!").format(legacy=legacy))
                    self.loadandconvertlegacysettingsfile(setting=setting)
            if file.exists(savefile): #Keep around .ini and .dat
                for r in self.program.data_repo:
                    self.program.data_repo[r].add(savefile)
        #This line as is causes merge conflicts unnecessarilyː
        # self.repo_commit() #this will be taken up later, or else done again
    def repo_commit(self):
        for r in self.program.data_repo:
            self.program.data_repo[r].commit()
    def moveattrstoobjects(self):
        # log.info("Glosslangs (in moveattrstoobjects): {}".format(self.glosslangs.langs()))
        # log.info(f"moveattrstoobjects done: {self.attrs_moved_to_object}")
        to_do=set(self.fndict)-self.attrs_moved_to_object
        log.info(f"moveattrstoobjects to do: {to_do}")
        for attr in to_do:
            if hasattr(self,attr):
                log.info(_("moving attr {attr} to object ({val})").format(attr=attr,val=getattr(self,attr)))
                self.fndict[attr](getattr(self,attr))
                # log.info("Glosslangs (in moveattrstoobjects): {}".format(self.glosslangs.langs()))
                if attr not in ['glosslangs']: #obj and attr have same name...
                    delattr(self,attr)
                self.attrs_moved_to_object.add(attr)
            else:
                log.info(_("attr {attr} not found!").format(attr=attr))
        log.info(_("attrs_moved_to_object={val}").format(val=self.attrs_moved_to_object))
        # log.info("Glosslangs (in moveattrstoobjects): {}".format(self.glosslangs.langs()))
    def settingsobjects(self):
        """These should each push and pull values to/from objects"""
        self.fndict=fns={}
        try: #these objects may not exist yet
            fns['cvt']=self.program.params.cvt
            fns['check']=self.program.params.check
            fns['ftype']=self.program.params.ftype
            fns['analang']=self.program.params.analang
            fns['glosslang']=self.glosslangs.lang1
            fns['glosslang2']=self.glosslangs.lang2
            fns['glosslangs']=self.glosslangs.langs
            # fns['toneframes']=self.program.toneframes
            # fns['status']=self.program.status
            fns['aztrepourls']=self.program.source_repo.remoteurls
            fns['status']=self.program.alphabet.status
            fns['glyphdict']=self.program.alphabet.glyphdict
            fns['glyph_members']=self.program.alphabet.glyph_members
            fns['glyphs_distinguished']=self.program.alphabet.distinguished
            fns['alphabet_order']=self.program.alphabet.order#self.alpha_order
            fns['alphabet_ncolumns']=self.alpha_ncolumns
            fns['alphabet_exids']=self.alpha_exids
            fns['alphabet_chart_title']=self.alpha_chart_title
            fns['alphabet_copyright']=self.alpha_copyright
            fns['alphabet_pagesize']=self.alpha_pagesize
            fns['contributors']=self.alphabet_contributors
            #This seems to break here:
            fns['ps']=self.program.slices.ps
            fns['profile']=self.program.slices.profile
            # except this one, which pretends to set but doesn't (throws arg away)
            fns['profilecounts']=self.program.slices.slicepriority
            fns['giturls']=self.program.data_repo['git'].remoteurls
            fns['asr_repos']=self.program.soundsettings.asr_repo_tally
            fns['asr_kwargs']=self.program.soundsettings.asr_kwarg_dict
            fns['hgurls']=self.program.data_repo['hg'].remoteurls
        except Exception as e:
            log.error(_("Only finished settingsobjects up to {keys} ({error})").format(keys=fns.keys(),error=e))
            self.moveattrstoobjects() #always do this next
            return []
        log.info(_("Finished settingsobjects up to {keys}").format(keys=fns.keys()))
        self.moveattrstoobjects() #always do this next
    def makesettingsdict(self,setting='defaults'):
        """This returns a dictionary of values, keyed by a set of settings"""
        """It pulls from objects if it can, otherwise from self attributes
        (if there), for backwards compatibility, when converting from legacy
        files before the objects are created."""
        d={}
        if setting == 'soundsettings':
            o=self.soundsettings
        else:
            o=self
        for s in self.settings[setting]['attributes']:
            # log.info("Looking for {} attr".format(s))
            # log.info("{} attr value: {}".format(s,getattr(o,s,'Not Found!')))
            """This dictionary of functions isn't made until after the objects,
            at the end of settings init. So this block is not used in
            conversion, only in later saves."""
            if hasattr(self,'fndict') and s in self.fndict:
                # log.info("Trying to dict {} attr".format(s))
                try:
                    d[s]=self.fndict[s]()
                    # log.info("Value {}={} found in object".format(s,d[s]))
                except:
                    log.error(_("Value of {attr} not found in object").format(attr=s))
            elif hasattr(o,s):
                if getattr(o,s) or setting == 'soundsettings': #store Falses
                    d[s]=getattr(o,s)
                # log.info("Set to dict self.{} with value {}, type {}"
                #         "".format(s,d[s],type(d[s])))
            # else:
            #     log.error("Couldn't find {} in {}".format(s,setting))
        """This is the only glosslang > glosslangs conversion"""
        if 'glosslangs' in d and d['glosslangs'] in [None,[]]:
            if 'glosslang' in d and d['glosslang'] is not None:
                d['glosslangs']=[d['glosslang']]
                del d['glosslang']
                if 'glosslang2' in d and d['glosslang2'] is not None:
                    d['glosslangs'].append(d['glosslang2'])
                    del d['glosslang2']
        return d
    def readsettingsdict(self,settingsdict):
        """This takes a dictionary keyed by attribute names"""
        # d=settingsdict
        if 'fs' in settingsdict:
            o=self.soundsettings
        else:
            o=self
        for s in settingsdict:
            v=settingsdict[s]
            if isinstance(v,settings.manager.configparser.SectionProxy):
                continue #don't store expty section headers
            elif hasattr(self,'fndict') and s in self.fndict:
                # log.info("Trying to read {} to object with value {} and fn "
                #             "{}".format(s,v,self.fndict[s]))
                self.fndict[s](v)
            elif (isinstance(v,dict) and
                hasattr(o,s) and isinstance(getattr(o,s),dict)):
                getattr(o,s).update(v)
            else:
                # log.info("Trying to read {} to {} with value {}, type {}"
                #             "".format(s,o,v,type(v)))
                setattr(o,s,v)
        return settingsdict
    def storesettingsfile(self,setting='defaults'):
        if setting in ['status', 'toneframes']:
            d=program[setting]
        else:
            d=self.makesettingsdict(setting=setting)

        # Synchronize with new modular domains
        domain_mapping = {
            'defaults': ['project', 'ui'],
            'soundsettings': ['audio'],
            'alphabet': ['alphabet'],
            'contributors': ['contributors'],
            'status': ['data'],
            'toneframes': ['data'],
            'adhocgroups': ['data'],
            'profiledata': ['data']
        }

        if setting in domain_mapping:
            for domain_name in domain_mapping[setting]:
                domain_mgr = getattr(self.mgr, domain_name)
                # We need to filter and update the domain data
                domain_attrs = migration.converters.Converter.DOMAIN_MAPPING[domain_name]
                domain_data = {k: v for k, v in d.items() if k in domain_attrs}
                if domain_data:
                    current_data = domain_mgr.load()
                    current_data.update(domain_data)
                    domain_mgr.save(current_data)
                    log.info(_("Stored {setting} settings in new {domain} domain").format(setting=setting, domain=domain_name))

        # Legacy storage for backup/compatibility
        filename=self.settingsfile(setting)
        if not filename:
             return
        settings.write_ini(filename, d)
    def loadsettingsfile(self,setting='defaults'):
        # Check domain-specific manager first
        domain_mapping = {
            'defaults': ['project', 'ui'],
            'soundsettings': ['audio'],
            'alphabet': ['alphabet'],
            'contributors': ['contributors'],
            'status': ['data'],
            'toneframes': ['data'],
            'adhocgroups': ['data'],
            'profiledata': ['data']
        }

        if setting in domain_mapping:
            for domain_name in domain_mapping[setting]:
                domain_mgr = getattr(self.mgr, domain_name)
                data = domain_mgr.load()
                if data:
                    log.info(_("Loaded {setting} settings from new {domain} domain").format(setting=setting, domain=domain_name))
                    self.readsettingsdict(data)

        # Still fallback to legacy reader for now to ensure absolute compatibility 
        # during the transition if JSON files were not yet created or migrated.
        filename=self.settingsfile(setting)
        if not filename or not filename.exists():
            return

        log.info(_("Fallback check for {setting} settings in {file}").format(setting=setting, file=filename))
        sections, d = settings.read_ini(filename, setting)
        if not sections and setting not in ['status','toneframes']:
            if setting == 'adhocgroups':
                self.adhocgroups={}
            return
        if setting == 'status':
            self.makestatus({k:d[k] for k in d if k != 'DEFAULT'})
            log.info(_("makestatus: {status}").format(status=self.program.status))
        elif setting == 'toneframes':
            self.maketoneframes({k:d[k] for k in d if k != 'DEFAULT'})
            log.info(_("maketoneframes: {frames}").format(frames=self.program.toneframes))
        else:
            self.readsettingsdict(d)
    def initdefaults(self):
        """Some of these defaults should be reset when setting another field.
        These are listed under that other field. If no field is specified
        (e.g., on initialization), then do all the fields with None key (other
        fields are NOT saved to file!).
        These are check related defaults; others in lift.get"""
        self.defaultstoclear={'ps':[
                            'profile' #do I want this?
                            # 'name',
                            # 'subcheck'
                            ],
                        'analang':[
                            'glosslangs',
                            'ps',
                            'profile',
                            'cvt',
                            'check',
                            'subcheck'
                            ],
                        'interfacelang':[],
                        'glosslangs':[],
                        'check':[],
                        'subcheck':[
                            'regexCV'
                            ],
                        'group_comparison':[],
                        'profile':[
                            # 'name'
                            ],
                        'cvt':[
                            'check',
                            # 'subcheck'
                            ],
                        'fs':[],
                        'sample_format':[],
                        'audio_card_index':[],
                        'audioout_card_index':[],
                        'examplespergrouptorecord':[],
                        'distinguish':[],
                        'interpret':[],
                        'adnlangnames':[],
                        'showdetails':[],
                        'askedlxtolc':[],
                        'maxprofiles':[]
                        }
    def cleardefaults(self,field=None):
        if field==None:
            fields=self.settings['defaults']['attributes']
        else:
            fields=self.defaultstoclear[field]
        for default in fields: #self.defaultstoclear[field]:
            if default in ['lowverticalspace']:
                setattr(self, default, True)
            else:
                setattr(self, default, None)
    def settingsinit(self):
        log.info(_("Initializing settings."))
        # self.defaults is already there, from settingsfilecheck
        self.initdefaults() #provides self.defaultstoclear, needed?
        self.cleardefaults() #this resets all to none (to be set below)
    def getdirectories(self):
        self.directory=file.getfilenamedir(self.liftfilename)
        if not file.exists(self.directory):
            log.info(_("Looks like there's a problem with your directory... {file}\n{dir}")
                    .format(file=self.liftfilename,dir=self.directory))
            exit()
        self.settingsfilecheck()
        self.imagesdir=file.getimagesdir(self.directory)
        self.audiodir=file.getaudiodir(self.directory)
        # log.info('self.audiodir: {}'.format(self.audiodir))
        self.reportsdir=file.getreportdir(self.directory)
        self.exportsdir=file.getexportdir(self.directory)
        self.reportbasefilename=file.getdiredurl(self.reportsdir,
                                                    self.liftnamebase)
        self.reporttoaudiorelURL=file.getreldir(self.reportsdir, self.audiodir)
        # log.info('self.reportsdir: {}'.format(self.reportsdir))
        # log.info('self.reportbasefilename: {}'.format(self.reportbasefilename))
        # log.info('self.reporttoaudiorelURL: {}'.format(self.reporttoaudiorelURL))
        # setdefaults.langs(self.program.db) #This will be done again, on resets
    def trackuntrackedfiles(self):
        # return #until this doesn't cause problems
        # This method is here to pick up files that are there, but not tracked,
        # either in constructing a repository, or as a result of changes by other
        # editors (e.g., WeSay).
        # This is for new files, not changes to known files; that is done
        # on close.
        # def ifnotthereadd(f,repo):
        #     # print('ifnotthereadd')
        #     if f not in self.repo[repo].files:
        #         # print('ifnotthereadd',f,2)
        #         self.repo[repo].add(f)
        log.info(_("Looking for untracked files to add to repositories"))
        maxthreads=8 #This causes problems with lots of threads
        maindirfiles=[self.liftfilename,
                        self.toneframesfile,
                        self.statusfile,
                        self.profiledatafile,
                        # I don't know if anyone is using this, but if so, they share...
                        self.adhocgroupsfile,
                        #self.defaultfile # This probably shouldn't be shared
                        # self.soundsettingsfile #per computer, definitely don't share!
                        ]
        self.program.tk_root.update() #update GUI before threading
        # for r in self.repo:
        r='git' #only look for this; don't duplicate repos unnecessarily
        if r in self.program.data_repo:
            t=u=None
            present=set(self.program.data_repo[r].files)
            log.info(_("{repo} currently has {count} files").format(repo=r,count=len(present)))
            for f in maindirfiles:
                # log.info("{}".format([file.getreldirposix(self.program.data_repo[r].url,f)]))
                # log.info("working on {}".format(file.getreldirposix(self.program.data_repo[r].url,f)))
                log.info(_("working on {file}").format(file=file.getfile(f)))
                # f=file.getreldirposix(self.program.data_repo[r].url,f)
                if file.exists(f):# They won't always be there
                    self.program.data_repo[r].add(file.getreldirposix(self.program.data_repo[r].url,f))
            # In case I run into formatting issues again:
            # log.info(', '.join(list(self.program.data_repo[r].files)[:5]))
            # log.info(', '.join([file.getreldir(self.program.data_repo[r].url,i) for i in file.getfilesofdirectory(self.audiodir, '*.wav')][:5]))
            # If we ever support mp3, we should add it here:
            # log.info("{}".format([file.getreldirposix(self.program.data_repo[r].url,i)
            #         for i in file.getfilesofdirectory(self.audiodir,
            #                                             '*.wav')]))
            # log.info("{}".format(set(file.getreldirposix(self.program.data_repo[r].url,i)
            #         for i in file.getfilesofdirectory(self.audiodir,
            #                                             '*.wav'))))
            audiohere=set([file.getreldirposix(self.program.data_repo[r].url,i)
                    for i in file.getfilesofdirectory(self.audiodir,
                                                        '*.wav')])
            audio=audiohere-present
            log.info(_("{wav_count} wav files to check for the {repo} repo (of {total_count} files total "
                    "here)").format(wav_count=len(audio),repo=r,total_count=len(audiohere)))
            log.info(_("head of wav files in repo: {files}").format(files=list(present)[:10]))
            log.info(_("head of wav files here: {files}").format(files=list(audiohere)[:10]))
            log.info(_("head of wav files to check: {files}").format(files=list(audio)[:10]))
            for f in audio:
                self.program.data_repo[r].add(f) #These should exist, from ls above
                # if threading.active_count()<maxthreads:
                #     t = threading.Thread(target=ifnotthereadd, args=(f,r))
                #     t.start()
                # log.info(_("trackuntrackedfiles waiting for {count} audio file threads."
                #         ).format(count=threading.active_count()))
                # if t:
                #     t.join()
                # self.program.data_repo[r].add(f)
            for ext in ['png','jpg','gif']:
                # log.info(_("Image Directory: {dir}").format(dir=self.imagesdir))
                # log.info("Found image files: {}".format(nn([i for i in
                # file.getfilesofdirectory(self.imagesdir,
                #                         '*.'+ext)], oneperline=True)))
                i=set([file.getreldirposix(self.program.data_repo[r].url,i)
                        for i in file.getfilesofdirectory(self.imagesdir,
                                                '*.'+ext)]
                        )-present
                log.info(_("{count} {extension} files to check for the {repo} repo")
                        .format(count=len(i),extension=ext,repo=r))
                for f in i:
                    self.program.data_repo[r].add(f) #These should exist, from ls above
                    # if threading.active_count()<maxthreads:
                    #     u = threading.Thread(target=ifnotthereadd, args=(f,r))
                    #     u.start()
                    # log.info("trackuntrackedfiles waiting for {} {} file "
                    #     "threads.".format(threading.active_count(),ext))
                        # if u:
                        #     u.join()
        log.info(_("trackuntrackedfiles finished."))
    def alpha_order(self,value=[]):
        return self.program.alphabet.order(value)
    def alpha_exids(self,value=dict()):
        if value: #don't allow integer keys; load them first, converting, then
            # overwrite if that string is elsewhere in the dict
            self._alphabet_exids={str(k):value[k] for k in value if type(k) is int}
            self._alphabet_exids.update({str(k):value[k] for k in value if type(k) is not int})
        return getattr(self,'_alphabet_exids',value)
    def alpha_ncolumns(self,value=0):
        if value:
            self._alphabet_ncolumns=value
        return getattr(self,'_alphabet_ncolumns',5)
    def alpha_chart_title(self,value=''):
        if value:
            self._alphabet_chart_title=value
        return getattr(self,'_alphabet_chart_title',value)
    def alpha_copyright(self,value=''):
        if value:
            self._alphabet_copyright=value
        return getattr(self,'_alphabet_copyright',_("Set Alphabet Copyright!"))
    def alphabet_contributors(self,value=None):
        if value is not None:
            self._contributors=value
        return getattr(self,'_contributors',[])
    def alpha_pagesize(self,value=''):
        if value:
            self._alphabet_pagesize=value
        return getattr(self,'_alphabet_pagesize','A4')
    def pss(self):
        log.info(_("checking these lexical category names for plausible noun "
                "and verb names: {pss}").format(pss=self.program.db.pss))
        topn=3 #just in case N and V aren't the first two, finish with top
        log.info(_("Looking at pss {pss}").format(pss=self.program.db.pss))
        for ps in reversed(self.program.db.pss[:topn]):
            log.info(_("Looking at ps {ps}").format(ps=ps))
            if ps in ['N','n','Noun','noun',
                    'Nom','nom',
                    'S','s','Sustantivo','sustantivo'
                    ]:
                self.nominalps=ps
            elif ps in ['V','v','Verb','verb',
                    'Verbe','verbe',
                    'Verbo','verbo'
                    ]:
                self.verbalps=ps
            # else:
            #     log.error("Not sure what to do with top {} ps {}".format(
            #                                                         topn,ps))
        if not hasattr(self,'nominalps'):
                self.nominalps='Noun'
        if not hasattr(self,'verbalps'):
                self.verbalps='Verb'
        try:
            log.info(_("Using ‘{noun}’ for nouns, and ‘{verb}’ for verbs").format(
                noun=self.nominalps,
                verb=self.verbalps))
        except AttributeError:
            log.info(_("Problem with finding a nominal and verbal lexical "
            "category (looked in first two of [{pss}])")
            .format(pss=self.program.db.pss))
        if self.secondformfield:
            if self.nominalps in self.secondformfield:
                self.pluralname=self.secondformfield[self.nominalps]
            if self.verbalps in self.secondformfield:
                self.imperativename=self.secondformfield[self.verbalps]
    def makesecondformfieldsOK(self):
        if self.nominalps not in self.secondformfield:
            self.program.taskchooser.mainwindowis.getsecondformfieldN()
        if self.verbalps not in self.secondformfield:
            self.program.taskchooser.mainwindowis.getsecondformfieldV()
    def secondformfieldsOK(self):
        if (self.nominalps in self.secondformfield and
            self.verbalps in self.secondformfield):
            return True
    def fields(self):
        """I think this is lift specific; may move it to defaults, if not."""
        # log.info(self.program.db.fieldnames)
        try:
            fieldnames=self.program.db.fieldnames[self.analang]
        except KeyError:
            fieldnames=[]
        self.secondformfield={}
        log.info(_("Fields found in lexicon: {fields}").format(fields=fieldnames))
        self.plopts=['Plural', 'plural', 'pl', 'Pluriel', 'pluriel']
        self.impopts=['Imperative', 'imperative', 'imp', 'Imp', 'Imperatif',
                                                    'imperatif']
        for opt in self.plopts:
            if opt in fieldnames:
                self.secondformfield[self.nominalps]=self.pluralname=opt
        try:
            log.info(_("Plural field name: {name}").format(name=self.pluralname))
            for entry in self.program.db.entries:
                entry.fieldvalue(self.pluralname,self.analang) # get the right field!
        except AttributeError:
            log.info(_('Looks like there is no Plural field in the database'))
            self.pluralname=None
        for opt in self.impopts:
            if opt in fieldnames:
                self.secondformfield[self.verbalps]=self.imperativename=opt
        try:
            log.info(_("Imperative field name: {name}").format(name=self.imperativename))
            for entry in self.program.db.entries:
                entry.fieldvalue(self.imperativename,self.analang) # get the right field!
        except AttributeError:
            log.info(_('Looks like there is no Imperative field in the database'))
            self.imperativename=None
    def checkforpolygraphsindata(self):
        for lang in self.program.db.s:
            for sclass in [sc for sc in self.program.db.s[lang]
                                if ('dg' in sc or 'tg' in sc or 'qg' in sc)]:
                if self.program.db.s[lang][sclass]:
                    return True
    def askaboutpolygraphs(self,onboot=False):
        def nochanges():
            log.info(_("Trying to make no changes"))
            if not pgw.exitFlag.istrue():
                pgw.destroy()
            if foundchanges():
                log.info(_("Found changes, but not storing them; returning 1."))
                return 1
        def makechanges():
            log.info(_("Changes called for; like it or not, redoing analysis."))
            pgw.destroy()
            if not foundchanges():
                log.info(_("User asked for changes to polygraph settings, but "
                        "no changes found."))
                return
            for lang in self.program.db.analangs:
                for pc in vars[lang]:
                    for pg in vars[lang][pc]:
                        self.polygraphs[lang][pc][pg]=vars[lang][pc][pg].get()
            self.storesettingsfile(setting='profiledata')
            self.program.taskchooser.restart()
        def foundchanges():
            for lang in vars:
                if lang not in self.polygraphs:
                    return True
                for pc in vars[lang]:
                    if pc not in self.polygraphs[lang]:
                        return True
                    for pg in vars[lang][pc]:
                        if pg not in self.polygraphs[lang][pc]:
                            return True
                        v=vars[lang][pc][pg].get()
                        if self.polygraphs[lang][pc][pg]!=v:
                            return True
            log.info(_("No changes found to polygraph settings, continuing."))
        oktext=_("OK")
        azt=self.program.name
        if onboot:
            nochangetext=_("Exit {azt} with no changes").format(azt=self.program.name)
        else:
            nochangetext=_("Exit with no changes")
        log.info(_("Asking about Digraphs and Trigraphs!"))
        titlet=_("{azt} Digraphs and Trigraphs").format(azt=self.program.name)
        hasdata=self.checkforpolygraphsindata()
        #From wherever this is opened, it should withdraw and deiconify that
        pgw=ui.Window(self.program.taskchooser.mainwindowis,title=titlet,exit=False)
        t=_("Which of the following letter sequences from your data "
            "refer to a single sound?")
        log.info(_("working with db.analangs: {analangs} and params.analang: {analang}")
                .format(analangs=self.program.db.analangs, analang=self.program.params.analang()))
        lnames=[self.languagenames[y] for y in set(
                    self.program.db.analangs+[self.program.params.analang()]
                                                )]
        if len(lnames)>1:
            t+=(_(" (Answer for each of {names}.)").format(names=unlist(lnames)))
        else:
            t+=(_(" (in {names})").format(names=unlist(lnames)))
        row=0
        title=ui.Label(pgw.frame,text=titlet, font='title',
                        column=0, row=row
                        )
        title.wrap()
        row+=1
        b=ui.Button(pgw.frame,text=nochangetext,command=nochanges,
                    column=0, row=row, sticky='e')
        row+=1
        instr=ui.Label(pgw.frame,text=t,
                        column=0, row=row
                        )
        instr.wrap()
        t=_("If you expect one (already in your data) that isn't listed "
            "here, please click here to Email me, and I can add it.")
        row+=1
        t2=ui.Label(pgw.frame,text=t,column=0, row=row)
        eurl='mailto:{}?subject=New trigraph or digraph to add (today)'.format(
                                                            self.program.Email)
        t2.bind("<Button-1>", lambda e: openweburl(eurl))
        if hasdata:
            t=_("Making changes will restart {name} and trigger another syllable profile analysis. \n"
                "If you don't want that, click ‘{btn}’.").format(name=self.program.name, btn=nochangetext)
        else:
            t=_("\n*** There don't seem to be any possible digraphs or trigraphs "
                "in your data ***\n")
        row+=1
        t3=ui.Label(pgw.frame,text=t,column=0, row=row)
        helpurl='{}/POLYGRAPHS.md'.format(self.program.docsurl,self.program.Email)
        t=_("See {url} for further instructions.").format(url=helpurl)
        row+=1
        t4=ui.Label(pgw.frame,text=t,column=0, row=row)
        t4.bind("<Button-1>", lambda e: openweburl(helpurl))
        if not hasattr(self,'polygraphs'):
            self.polygraphs={}
        vars={}
        row+=1
        scroll=ui.ScrollingFrame(pgw.frame, row=row, column=0)
        srow=0
        ncols=4 # increase this for wider window
        for lang in self.program.db.analangs:
            if lang not in self.polygraphs:
                self.polygraphs[lang]={}
            srow+=1
            title=ui.Label(scroll.content,text=self.languagenames[lang],
                                                        font='read')
            title.grid(column=0, row=srow, columnspan=ncols)
            vars[lang]={}
            # log.info("sclasses: {}".format(self.program.db.s[lang]))
            for sclass in [sc for sc in self.program.db.s[lang] #Vtg, Vdg, Ctg, Cdg, etc
                                if ('dg' in sc or 'tg' in sc or 'qg' in sc)]:
                pclass=sclass.replace('dg','').replace('tg','').replace('qg','')
                if pclass not in self.polygraphs[lang]:
                    self.polygraphs[lang][pclass]={}
                if pclass not in vars[lang]:
                    vars[lang][pclass]={}
                if len(self.program.db.s[lang][sclass])>0:
                    srow+=1
                    header=ui.Label(scroll.content,
                    text=sclass.replace('dg',' (digraph)').replace(
                                        'tg',' (trigraph)').replace(
                                        'qg',' (quatregraph)')+': ')
                    header.grid(column=0, row=srow)
                col=1
                # log.info("pgs: {}".format(self.program.db.s[lang][sclass]))
                for pg in self.program.db.s[lang][sclass]:
                    vars[lang][pclass][pg] = ui.BooleanVar()
                    vars[lang][pclass][pg].set(
                                    self.polygraphs[lang][pclass].get(pg,True))
                    cb=ui.CheckButton(scroll.content, text = pg, #.content
                                        variable = vars[lang][pclass][pg],
                                        onvalue = True, offvalue = False,
                                        )
                    cb.grid(column=col, row=srow,sticky='nsew')
                    if col<= ncols:
                        col+=1
                    else:
                        col=1 #not header
                        srow+=1
        if hasdata:
            row+=1
            b=ui.Button(pgw.frame,text=oktext,command=makechanges, width=15,
                    column=0, row=row, sticky='e',padx=15)
        pgw.wait_window(pgw)
        if not self.program.taskchooser.exitFlag.istrue():
            return nochanges() #this is the default exit behavior
    def polygraphLWCdefaults(self):
        lwcdefaults={'en':{'D':{'gh':True,
                        		'bb':True,
                        		'dd':True,
                        		'gg':True,
                        		'gu':True,
                        		'mb':False,
                        		'nd':False,
                        		'dw':False,
                        		'gw':False,
                        		'zl':False},
                        	'C':{'ckw':False,
                        		'thw':False,
                        		'tch':True,
                        		'cc':True,
                        		'pp':True,
                        		'pt':False,
                        		'tt':True,
                        		'ck':True,
                        		'qu':True,
                        		'mp':False,
                        		'nt':False,
                        		'nk':False,
                        		'tw':False,
                        		'kw':False,
                        		'ch':True,
                        		'ph':True,
                        		'sh':True,
                        		'hh':True,
                        		'ff':True,
                        		'sc':False,
                        		'ss':True,
                        		'th':True,
                        		'sw':False,
                        		'hw':True,
                        		'ts':False,
                        		'sl':False},
                        	'G':{'yw':False},
                        	'N':{'mm':True,
                        		'ny':False,
                        		'gn':True,
                        		'nn':True,
                        		'nw':False},
                        	'S':{'rh':True,
                        		'wh':True,
                        		'll':True,
                        		'rr':True,
                        		'lw':False,
                        		'rw':False},
                        	'V':{'ou':True,
                        		'ei':True,
                        		'ai':True,
                        		'yi':True,
                        		'ea':True,
                        		'ay':True,
                        		'ee':True,
                        		'ey':True,
                        		'ie':True,
                        		'oa':True,
                        		'oo':True,
                        		'ow':True,
                        		'ue':True,
                        		'oe':True,
                        		'au':True,
                        		'oi':True,
                        		'eau':True}},
                     'fr':{'D':{'gh':False,
                         		'bb':False,
                         		'dd':False,
                         		'gg':False,
                         		'gu':True,
                         		'mb':False,
                         		'nd':False,
                         		'dw':False,
                         		'gw':False,
                         		'zl':False},
                         	'C':{'ckw':False,
                         		'thw':False,
                         		'tch':True,
                         		'cc':True,
                         		'pp':True,
                         		'pt':False,
                         		'tt':False,
                         		'ck':False,
                         		'qu':True,
                         		'mp':False,
                         		'nt':False,
                         		'nk':False,
                         		'tw':False,
                         		'kw':False,
                         		'ch':True,
                         		'ph':True,
                         		'sh':False,
                         		'hh':False,
                         		'ff':False,
                         		'sc':False,
                         		'ss':True,
                         		'th':True,
                         		'sw':False,
                         		'hw':False,
                         		'ts':False,
                         		'sl':False},
                         	'G':{'yw':False},
                         	'N':{'mm':False,
                         		'ny':False,
                         		'gn':True,
                         		'nn':False,
                         		'nw':False},
                         	'S':{'rh':True,
                         		'wh':True,
                         		'll':True,
                         		'rr':True,
                         		'lw':False,
                         		'rw':False},
                         	'V':{'ou':True,
                         		'ei':True,
                         		'ai':True,
                         		'yi':False,
                         		'ea':True,
                         		'ay':False,
                         		'ee':False,
                         		'ey':False,
                         		'ie':True,
                         		'oa':True,
                         		'oo':True,
                         		'ow':False,
                         		'ue':True,
                         		'oe':True,
                         		'au':True,
                         		'oi':True,
                         		'eau':True}
                    }   }
        if self.program.params.analang in lwcdefaults:
            log.info(_("It looks like you're working on your LWC; using {lang} digraph defaults")
                    .format(lang=self.languagenames[self.program.params.analang]))
            return lwcdefaults[self.program.params.analang] #in case trying out a demo
        try:
            log.info(_("Using your interface language ({lang}) digraph defaults")
                    .format(lang=self.languagenames[interfacelang()]))
            return lwcdefaults[interfacelang()] #assume this general framework
        except KeyError:
            log.info(_("It looks like neither your LWC ({analang}) nor your interface language ({interlang}) "
                    "has a set of digraph defaults, so not providing any")
                    .format(analang=self.languagenames[self.program.params.analang],
                            interlang=self.languagenames[interfacelang()]))
            return {} #let users build from scratch
    def polygraphcheck(self):
        log.info(_("Checking for Digraphs and Trigraphs!"))
        # log.info("Language settings: {}".format(self.program.db.s))
        firstrun=False
        if not hasattr(self,'polygraphs'):
            firstrun=True
            self.polygraphs={}
        for lang in self.program.db.analangs:
            if lang not in self.program.db.s:
                log.error(_("Language {lang} found without segment settings."
                            ).format(lang=lang))
                continue
            if lang not in self.polygraphs:
                self.polygraphs[lang]=self.polygraphLWCdefaults()
            for sclass in [sc for sc in self.program.db.s[lang]
                                    if ('dg' in sc or 'tg' in sc or 'qg' in sc)]:
                pclass=sclass.replace('dg','').replace('tg','').replace('qg','')
                if pclass not in self.polygraphs[lang]:
                    self.polygraphs[lang][pclass]={}
                for pg in self.program.db.s[lang][sclass]:
                    # log.info("checking for {} ({}/{}) in {}"
                    #         "".format(pg,pclass,sclass,self.polygraphs))
                    # Don't show user this on first boot; only when new
                    # characters show up
                    if not firstrun and pg not in self.polygraphs[lang][pclass]:
                        log.info(_("{polygraph} ({pclass}/{sclass}) has no Di/Trigraph setting; "
                        "prompting user for info.").format(polygraph=pg,pclass=pclass,sclass=sclass))
                        if self.askaboutpolygraphs(onboot=True):
                            log.info(_("Asked about polgraphs, but user "
                                        "exited, so exiting {name}"
                                        ).format(name=self.program.name))
                            self.program.taskchooser.mainwindowis.on_quit()
                        return
        log.info("Di/Trigraph settings seem complete; moving on.")
    def checkinterpretations(self):
        """This sets sane defaults, if not there"""
        if (not hasattr(self,'distinguish')) or (self.distinguish is None):
            self.distinguish={}
        if (not hasattr(self,'interpret')) or (self.interpret is None):
            self.interpret={}
        for var in self.profilelegit+[i+'wd' for i in self.profilesegments]:
            if var in ['C','V']:
                continue
            if ((var not in self.distinguish) or
                (type(self.distinguish[var]) is not bool)):
                self.distinguish[var]=False
            """These defaults are not settable, yet:"""
            if var in ["̀",'ː']: #typically word-forming
                self.distinguish[var]=False
            if var in ['<','=','.']: #typically not word-forming
                self.distinguish[var]=True
        for var in ['NC','CG','CS','VV','VN']:
            if ((var not in self.interpret) or
                (type(self.interpret[var]) is not str) or
                not(1 <=len(self.interpret[var])<= 2)):
                if 'V' in var:
                    self.interpret[var]=var
                else:
                    self.interpret[var]='CC'
        if self.interpret['VV']=='Vː' and self.distinguish['ː']==False:
            self.interpret['VV']='VV'
        log.log(2,"self.distinguish: {}".format(self.distinguish))
    def addtoprofilesbysense(self,sense,ps,profile):
        # log.info("kwargs: {}".format(kwargs))
        # This will die if ps and profile aren't in kwargs:
        setnesteddictval(self.profilesbysense,[sense],ps,profile,addval=True)
        try:
            self.profilesbysense[ps][profile]+=[sense]
        except KeyError:
            try:
                self.profilesbysense[ps][profile]=[sense]
            except KeyError:
                self.profilesbysense[ps]={profile:[sense]}
                # self.profilesbysense[ps][profile]=[sense]
    def addtoformstosearch(self,sense,form,ps,oldform=None):
        setnesteddictval(self.formstosearch,[sense],ps,form,addval=True)
        # log.info("Added {} id={}".format(form,sense.id))
        if oldform:
            try:
                self.formstosearch[ps][oldform].remove(sense)
                log.info(_("Removed {form} ({val})").format(form=form,val=self.formstosearch[ps][form]))
            except ValueError:
                log.error(_("Apparently {sense} isn't under {form}?").format(sense=sense, form=form))
            if not self.formstosearch[ps][oldform]:
                del self.formstosearch[ps][oldform] #don't leave form wo sense
                log.info(_("Deleted key of empty list"))
    def getprofileofentry(self,entry):
        getattr(entry,ftype).textvaluebylang(self.analang)
        #CONTINUE HERE
    def getprofileofsense(self,sense,ps):
        #Convert to iterate over local variables
        # form=sense.textvaluebyftypelang('lc',self.program.params.analang())
        form=sense.textvaluebyftypelang(self.profilesbysense['ftype'],
                                        self.profilesbysense['analang'])
        """This adds to self.sextracted, too"""
        if not form:
            return form,None #This is just for logging
        profile=self.rxdict.profileofform(form,ps=ps)
        self.extractsegmentsfromform(form,ps=ps)
        if not set(self.profilelegit).issuperset(profile):
            profile='Invalid'
        setnesteddictval(self.profilesbysense,[sense],ps,profile,addval=True)
        setnesteddictval(self.formstosearch,[sense],ps,form,addval=True)
        sense.cvprofilevalue(self.profilesbysense['ftype'],profile) #store this for future reference
        return form,profile #This is just for logging
    def getprofilesbyps(self,ps):
        # start_time=nowruntime()
        # log.info(_("Processing {ps} syllable profiles").format(ps=ps))
        senses=self.program.db.sensesbyps[ps]
        self.sextracted[ps]={} #start over, don't add to if there
        n=self._getprofiles(senses,ps)
        log.info(_("Processed {n} forms to {ps} syllable profiles").format(n=n,ps=ps))
        # logfinished(start_time)
    def _getprofiles(self,senses,ps):
        # This goes fast, even on a large database; do we need the wait?
        n=0
        todo=len(senses)
        # if todo>750:
        #     msg=_("getting profiles for {ps} lexical category").format(ps=ps)
        #     self.program.taskchooser.wait(msg)
        for sense in senses:
            n+=1
            # if False: #for testing without backgrounding
            if n%100:
                t = threading.Thread(target=self.getprofileofsense,
                                    args=(sense,ps))
                t.start()
            else:
                form,profile=self.getprofileofsense(sense,ps)
                log.debug(_("{count}: {form} > {profile}").format(count=str(n)+'/'+str(todo),form=form,
                                            profile=profile))
            # if todo>750:
            #     self.program.taskchooser.waitprogress(n*100/todo)
        try:
            t.join()
        except UnboundLocalError:
            pass #not backgrounding...
        # if todo>750:
        #     self.program.taskchooser.waitdone()
        return n
    def getprofilesbyentry(self):
        for entry in self.program.db.entries:
            for sense in entry.senses:
                sense.lxvalue()
    def getprofiles(self):
        """This is called after settings finished init/load from files"""
        #This is for analysis from scratch
        self.profileswdatabyentry={}
        self.profilesbysense={}
        self.profilesbysense['Invalid']=[]
        self.profilesbysense['analang']=self.program.db.analang
        self.profilesbysense['ftype']=self.program.params.ftype()
        self.profiledguids=[]
        self.formstosearch={}
        self.sextracted={} #don't add to old data
        self.notifyuserofextrasegments() #analang set by now, depends db only
        self.polygraphcheck() #depends only on self.polygraph
        self.checkinterpretations() #checks/sets values for distinguish/interpret
        # log.info("Interpretation: \n{}".format(
        #         '\n'.join([k+': '+self.interpret[k] for k in self.interpret])
        #         ))
        # log.info("Distinguishing: \n{}".format(
        #         '\n'.join([k+': '+str(self.distinguish[k]) for k in self.distinguish])
        #         ))
        self.setupCVrxs() #creates self.s and self.rxdict
        for ps in self.program.db.pss: #45s on English db
            self.getprofilesbyps(ps)
        """Do I want this? better to keep the adhoc groups separate"""
        """We will *never* have slices set up by this time; read from file."""
        if hasattr(self,'adhocgroups'):
            for ps in self.adhocgroups:
                for a in self.adhocgroups[ps]:
                    log.debug("Adding {} to {} ps-profile: {}".format(a,ps,
                                                self.adhocgroups[ps][a]))
                    these=[self.program.db.sensedict[i]
                            for i in self.adhocgroups[ps][a]]
                    setnesteddictval(self.profilesbysense,these,ps,a)
                    # log.debug("resulting profilesbysense: {}".format(
                    #                         self.profilesbysense[ps][a]))
        else:
            self.adhocgroups={}
        SliceDict(self.adhocgroups,self.profilesbysense,self.program)
        if self.program.slices.profile():
            self.getscounts()
        self.storesettingsfile(setting='profiledata')
    def extractsegmentsfromform(self,form,ps):
        for s in set(self.profilelegit) & set(self.rxdict.rx):
            # log.info('s: {}; rx: {}'.format(s, self.rxdict.rx[s]))
            # log.info(f"srx output: {self.rxdict.rx[s][0].findall(form)}")
            for i in [j for j in self.rxdict.rx[s][0].findall(form) if j]:
                i=''.join(i).lower() #('o', 'e') > 'oe', no upper case
                # log.info('found polygraph ‘{}’'.format(i))
                setnesteddictval(self.sextracted,1,ps,s,i,addval=True)
    def getscounts(self):
        """This depends on self.sextracted, from getprofiles, so should only
        run when that changes."""
        scount={}
        for ps in self.sextracted: # was self.program.db.pss[self.analang]:
            scount[ps]={}
            for s in self.rxdict.rx:
                try:
                    scount[ps][s]=sorted([(x,self.sextracted[ps][s][x])
                        for x in self.sextracted[ps][s]],key=lambda x:x[1],
                                                                reverse=True)
                except KeyError as e:
                    pass
                    # log.info(_("{error} KeyError reading {ps}-{s} from sextracted"
                    #             "").format(error=e,ps=ps,s=s))
        self.program.slices.scount(scount) #send to object
    def notifyuserofextrasegments(self):
        analang=self.program.db.analang
        if analang not in self.program.db.segmentsnotinregexes:
            return
        invalids=self.program.db.segmentsnotinregexes[analang]
        ninvalids=len(invalids)
        extras=list(dict.fromkeys(invalids).keys())
        if ninvalids >10 and analang != 'en':
            text=_("Your {lang} database has the following symbols, which are "
                "excluding {count} words from being analyzed: \n{symbols}") \
                .format(lang=analang,count=ninvalids,symbols=extras)
            title=_("More than Ten Invalid Characters Found!")
            self.warning=ErrorNotice(text,title=title)
    def slists(self):
        """This sets up the lists of segments, by types. For the moment, it
        just pulls from the segment types in the lift database."""
        log.info(_("Found db.analangs: {langs}").format(langs=self.program.db.analangs))
        log.info(_("Found params analang: {lang}").format(lang=self.program.params.analang()))
        self.s={l:{} for l in set(self.program.db.analangs+ #analang from database
                                [self.program.db.analang]) #inferred analang
                }
        for lang in set(self.s)&set(self.program.db.s):
            """These should always be there, no matter what"""
            for sclass in [x for x in self.program.db.s[lang]
                                        if 'dg' not in x
                                        and 'tg' not in x
                                        and 'qg' not in x
                                        ]: #Just populate each list now
                try:
                    assert sclass in self.polygraphs[lang]
                    pgthere=[k for k,v in self.polygraphs[lang][sclass].items() if v]
                    log.debug(_("Polygraphs for {lang} in {sclass}: {pgs}").format(lang=lang,sclass=sclass,
                                                                    pgs=pgthere))
                    self.s[lang][sclass]=pgthere
                except (AssertionError,AttributeError):
                    self.s[lang][sclass]=list()
                self.s[lang][sclass]+=self.program.db.s[lang][sclass]
                """These lines just add to a C list, for a later regex"""
            log.info(_("Segment lists for {lang} language: {segments}").format(lang=lang,
                                                                segments=self.s[lang]))
        for lang in set(self.s)-set(self.program.db.s): #in case no language data
            self.s[lang]=self.program.db.hypotheticals
            log.info(_("Segment lists for {lang} language: {segments}").format(lang=lang,
                                                                segments=self.s[lang]))
    def setvalidcharacters(self):
        """These are sent to rxdict, but the top two are also used here"""
        self.profilesegments=['N','G','S','D','C','V','ʔ']
        self.profilelegit=['̃','N','G','S','D','C','Ṽ','V','ʔ','ː',"̀",'=','<','.']
        self.invalidchars=[' ','...',')','(<field type="tone"><form lang="gnd"><text>']
    def addtoCVrxs(self,s):
        """This method is just to add a new grapheme while running, so we
        don't have to restart between C/V changes."""
        if not hasattr(self,'analang'): #in case running after startup
            self.analang=self.program.db.analang
        cvt=self.program.params.cvt()
        analang=self.program.db.analang
        if cvt in ['C', 'V'] and s not in self.s[analang][cvt]:
            self.s[analang][cvt]+=[s]
            # log.info("Compiling rx list: {}".format(self.s[self.analang][cvt]))
            self.rxdict.makeglyphregex(cvt)
            # log.info("Compiled rx list: {}".format(self.rx[cvt]))
    def compileCVrxforsclass(self,sclass):
        # this is now all in regexdict, and isn't called anywhere
        """This does sorting by length to make longest first"""
        analang=self.program.db.analang
        # log.info("compileCVrxforsclass RXs: {}".format(self.rx))
    def setupCVrxs(self):
        self.slists() #makes s; depends on polygraphs
        analang=self.program.db.analang
        glyphs_present=self.program.status.all_groups_verified_anywhere()
        for cvt in glyphs_present:
            if cvt == 'V':
                there=self.s[analang][cvt]
            else:
                there=[i
                        for k in ({'C'}|{ki for ki in self.distinguish
                            if not self.distinguish[ki]})&set(self.s[analang])
                        for j in self.s[analang][k]
                        if k in self.s[analang]
                        for i in j
                    ]
            self.s[analang][cvt].extend(glyphs_present[cvt]-set(there))
        self.rxdict=rx.RegexDict(distinguish=self.distinguish,
                                interpret=self.interpret,
                                sdict=self.s[self.program.db.analang],
                                profilelegit=self.profilelegit,
                                invalidchars=self.invalidchars,
                                profilesegments=self.profilesegments)
        #Each glyph variable found in the language gets a regex for each length,
        # plus 0 to find them all together – since we're looking for glyphs.
    def reloadstatusdatabycvtpsprofile(self,**kwargs):
        # This reloads the status info only for current slice
        # These are specified in iteration, pulled from object if called direct
        if kwargs.get('reporttime'):
            start_time=nowruntime()
        kwargs['cvt']=kwargs.get('cvt',self.program.params.cvt())
        kwargs['ps']=kwargs.get('ps',self.program.slices.ps())
        kwargs['profile']=kwargs.get('profile',self.program.slices.profile())
        if kwargs.get('reporttime'):
            log.info(_("Refreshing {cvt} {ps} {profile} status settings from LIFT")
                .format(cvt=kwargs['cvt'],ps=kwargs['ps'],profile=kwargs['profile']))
        checks=self.program.status.checks(**kwargs)
        kwargs['store']=False #do below
        for kwargs['check'] in checks:
            # log.info("Working on {}".format(c))
            self.program.status.build(**kwargs)
            """this just populates groups and the tosort boolean."""
            self.updatesortingstatus(**kwargs)
        if kwargs.get('reporttime'):
            logfinished(start_time)
    def reloadstatusdatabycvtps(self,**kwargs):
        # This reloads the status info as relevant on a particular page (ps and
        # cvt), so it needs to be iterated over, or done for each page switch,
        # if desired.
        # These are specified in iteration, pulled from object if called by menu
        if kwargs.get('reporttime'):
            start_time=nowruntime()
        kwargs['cvt']=kwargs.get('cvt',self.program.params.cvt())
        kwargs['ps']=kwargs.get('ps',self.program.slices.ps())
        log.info(_("Refreshing {ps} {cvt} status settings from LIFT").format(
                                                                ps=kwargs['ps'],
                                                                cvt=kwargs['cvt']))
        profiles=self.program.slices.profiles(ps=kwargs['ps']) #This depends on ps only
        for kwargs['profile'] in profiles:
            # log.info("Working on {}".format(p))
            self.reloadstatusdatabycvtpsprofile(**kwargs)
        if kwargs.get('store',True):
            self.storesettingsfile(setting='status')
        if kwargs.get('reporttime'):
            logfinished(start_time)
    def verification_keys_in_group_dict(self,x,y):
        """Check for problems before moving on. I don't know why, but mature
        databases develop verification data for groups that no longer exist,
        so we want to exclude those below. to keep from throwing errors, we
        check that the group dictionary as all the keys the verification
        dictionary has"""
        def report(x,y,key=None):
            """Is dict y a subset of dict x, wrt their key hierarchies?"""
            if set(y)-set(x):#not (k in x and k in y):#set(x[k])^set(y[k]):
                text=(f"{set(y)-set(x)} keys not in {key if key else 'dict'}!")
                ErrorNotice(text,wait=True)
                sysshutdown()
            for k in y: #don't care about k in x but not y
                # log.info(f"{k} is in both dictionaries! ({k in x=} {k in y=})")
                if isinstance(x[k],dict) and isinstance(y[k],dict):
                    report(x[k],y[k],k)
        report(x,y)
    def reloadstatusdata(self):
        log.info(_("Refreshing all status settings from LIFT"))
        self.storesettingsfile() #default, not status
        self.program.db.load_ps_profiles()
        d=self.program.db.annotation_values_by_ps_profile()
        t=self.program.db.tone_values_by_ps_profile()
        # log.info(f"Found this LIFT file: {self.program.db.filename}")
        # log.info(f"Found these LIFT annotations: {d}")
        self.program.status.clear_all_groups()
        #The above because the following only modifies current profiles & checks
        k={}
        for k['ps'],profile_dict in d.items():
            for k['profile'],check_dict in profile_dict.items():
                for k['check'],groups in check_dict.items():
                    if k['check'].isdigit():
                        continue
                    k['cvt']=self.program.params.cvt_of_check(k['check'])
                    groups=[i for i in groups if i]
                    # log.info(f"storing {k} unverified values: {groups}")
                    self.program.status.groups(groups, wsorted=True, **k)
        k['cvt']='T'
        for k['ps'],profile_dict in t.items():
            for k['profile'],check_dict in profile_dict.items():
                for k['check'],groups in check_dict.items():
                    self.program.status.groups(groups, wsorted=True, **k)
        """Verification data should not be read from LIFT. A single lift entry
        may be verified to belong to a particular sort group, without that sort
        group being verified in it's entirety, especially not since another
        word has been added to it.
        """
        """Now remove what didn't get data"""
        self.program.status.cull() #this removes empties, and limits done to groups
        if None in self.program.status: #This should never be there
            del self.program.status[None]
        self.program.status.store()
    def categorizebygrouping(self,fn,sense,**kwargs):
        #Don't complain if more than one found:
        check=kwargs.get('check',self.program.params.check())
        v=fn(
            self.program.status.task(),
            sense,check)
        if v in ['','None',None]: #unlist() returns strings
            # log.info("Marking sense {} tosort (v: {})".format(sense.id,v))
            if not kwargs.get('cvt'): #default, not on iteration
                self.program.status.marksensetosort(sense)
            tosort=True
        else:
            # log.info("Marking sense {} sorted (v: {})".format(sense.id,v))
            if not kwargs.get('cvt'): #default, not on iteration
                self.program.status.marksensesorted(sense.id)
            if v not in ['NA','ALLOK']:
                self._groups.append(v)
    def updatesortingstatus(self, store=True, **kwargs):
        """This reads LIFT to create lists for sorting, populating lists of
        sorted and unsorted senses, as well as sorted (but not verified) groups.
        So don't iterate over it. Instead, use checkforsensestosort to just
        confirm tosort status"""
        """To get this from the object, use status.tosort(), todo() or done()"""
        # log.info("updatesortingstatus called with store={} and kwargs: {}"
        #         "".format(store,kwargs))
        cvt=kwargs.get('cvt',self.program.params.cvt())
        ps=kwargs.get('ps',self.program.slices.ps())
        profile=kwargs.get('profile',self.program.slices.profile())
        check=kwargs.get('check',self.program.params.check())
        kwargs['wsorted']=True #ever not?
        senses=self.program.slices.senses(ps=ps,profile=profile)
        # log.info("Working on {} {} {} senses (first 5): {}".format(len(senses),
        #                                                             ps,profile,
        #                                                             senses[:5]))
        log.info(_("Working on {count} sense.ids (first 5): {ids}").format(count=len(senses),
                                                    ids=[i.id for i in senses[:5]]))
        self.program.status.renewsensestosort([],[]) #will repopulate
        self._groups=[]
        if cvt == 'T': #we need to be able to iterate over cvt, to rebuild
            fn=Tone.getitemgroup
        else:
            fn=Segments.getitemgroup #This pulls from annotation, not form
        """I think this is the problem why valid groupslike aʲ are getting dropped."""
        """continue here"""
        for sense in senses:
            # log.info("Working on sense {}".format(sense.id))
            self.categorizebygrouping(fn,sense,**kwargs)
        """update 'tosort' status"""
        """update status groups"""
        sorted=set(self._groups)
        self.program.status.groups(list(sorted),**kwargs)
        if store:
            # log.info(f"updatesortingstatus storing {kwargs=} {self.program.status=}")
            self.storesettingsfile(setting='status')
    def dont_guessanalang(self):
        """Analang should be easily deduceable from the lift file, and/or
        explicit in the settings."""
        self.analang=self.program.db.analang
        log.info(_("analang in use: {analang} (If you don't like this, change it in the menus)").format(analang=self.analang))
        return
        #have this call set()?
        """if there's only one analysis language, use it."""
        nlangs=len(self.program.db.analangs)
        log.debug(_("Found {n} analangs: {langs}").format(n=nlangs, langs=self.program.db.analangs))
        lxwdata=self.program.db.nentrieswlexemedata
        lcwdata=self.program.db.nentrieswcitationdata
        lxwdatamax=lcwdatamax=None
        for lang in [l for l in lcwdata if lcwdata[l] > 0]:
            if not lcwdatamax or lcwdata[lcwdatamax] < lcwdata[lang]:
                lcwdatamax=lang
        for lang in [l for l in lxwdata if lxwdata[l] > 0]:
            if not lxwdatamax or lxwdata[lxwdatamax] < lxwdata[lang]:
                lxwdatamax=lang
        log.info(_("Most citation data in [{lang}] ({data})").format(lang=lcwdatamax,data=lcwdata))
        log.info(_("Most lexeme data in [{lang}] ({data})").format(lang=lxwdatamax,data=lxwdata))
        if not nlangs:
            errortext=_("There don't seem to be any language forms in your "
            "database!")
            basename=file.getfilenamebase(self.liftfilename)
            parent=file.getfilenamebase(file.getfilenamedir(self.liftfilename))
            if parent == basename and langtags.tag_is_valid(basename):
                self.analang=parent
                errortext+=_("\n(guessing [{lang}]; if that's not correct, exit now "
                            "and fix it!)").format(lang=self.analang)
                log.info(errortext)
            else:
                self.program.taskchooser.splash.withdraw()
                errortext+=_("\nFurthermore, your LIFT file doesn't seem to "
                            "indicate your language code: \n{file} "
                            "\nchange that or add some data "
                            "to your database, so I know what language we're "
                            "working on. "
                            "\nOr select a different database on "
                            "the next screen."
                            ).format(file=self.liftfilename)
                e=ErrorNotice(errortext,title=_("Error!"),wait=True)
                file.writefilename() #just clear the default; let user move on
                sysrestart()
        elif nlangs == 1:
            self.analang=self.program.db.analangs[0]
            log.debug(_("Only one analang in file; using it: ({lang})").format(
                                                        lang=self.program.db.analangs[0]))
            """If there are more than two analangs in the database, check if one
            of the first two is three letters long, and the other isn't"""
        elif nlangs == 2:
            if ((len(self.program.db.analangs[0]) == 3) and
                langtags.tag_is_valid(self.program.db.analangs[0]) and
                (lcwdatamax == self.program.db.analangs[0] or
                    lxwdatamax == self.program.db.analangs[0]) and
                (len(self.program.db.analangs[1]) != 3)):
                log.debug(_("Looks like I found an iso code with data for "
                                "analang! ({lang})").format(lang=self.program.db.analangs[0]))
                self.analang=self.program.db.analangs[0] #assume this is the iso code
                self.analangdefault=self.program.db.analangs[0] #In case it gets changed.
            elif ((len(self.program.db.analangs[1]) == 3) and
                langtags.tag_is_valid(self.program.db.analangs[1]) and
                (lcwdatamax == self.program.db.analangs[1] or
                    lxwdatamax == self.program.db.analangs[1]) and
                    (len(self.program.db.analangs[0]) != 3)):
                log.debug(_("Looks like I found an iso code with data for "
                                "analang! ({lang})").format(lang=self.program.db.analangs[1]))
                self.analang=self.program.db.analangs[1] #assume this is the iso code
                self.analangdefault=self.program.db.analangs[1] #In case it gets changed.
            elif (lcwdatamax in self.program.db.analangs and
                            langtags.tag_is_valid(lcwdatamax)):
                self.analang=lcwdatamax
                log.debug(_("Neither analang looks like an iso code, taking the "
                "one with most citation data: {langs}").format(langs=self.program.db.analangs))
            elif (lxwdatamax in self.program.db.analangs and
                            langtags.tag_is_valid(lxwdatamax)):
                self.analang=lxwdatamax
                log.debug(_("Neither analang looks like an iso code, taking the "
                "one with most lexeme data: {langs}").format(langs=self.program.db.analangs))
            else:
                self.analang=self.program.db.analangs[0]
                log.debug(_("Neither analang looks like an iso code, nor has much"
                "data; taking the first one: {langs}").format(langs=self.program.db.analangs))
        else: #for three or more analangs, take the first plausible iso code
            if (lcwdatamax in self.program.db.analangs and
                        langtags.tag_is_valid(lxwdatamax)):
                self.analang=lcwdatamax
                log.debug(_("The language with the most citation data looks like "
                "an iso code; using: {langs}").format(langs=self.program.db.analangs))
            elif lcwdatamax == lxwdatamax and lxwdatamax in self.program.db.analangs:
                self.analang=lxwdatamax
                log.debug(_("The language with the most citation data is also "
                    "the language with the most lexeme data; using: {langs}").format(
                                                            langs=self.program.db.analangs))
            elif (lxwdatamax in self.program.db.analangs and
                        langtags.tag_is_valid(lxwdatamax)):
                self.analang=lxwdatamax
                log.debug(_("The language with the most lexeme data looks like "
                "an iso code; using: {langs}").format(langs=self.program.db.analangs))
            else:
                for n in range(1,nlangs+1): # end with first
                    self.analang=self.program.db.analangs[-n]
                    log.debug(_('trying {analang}').format(analang=self.analang))
                    if len(self.program.db.analangs[-n]) == 3:
                        log.debug(_("Looks like I found an iso code for "
                                "analang! ({lang})").format(lang=self.program.db.analangs[n-1]))
                        break #stop iterating, and keep this one.
        log.info(_("analang guessed: {lang} (If you don't like this, change it in "
                    "the menus)").format(lang=self.analang))
    def guessaudiolang(self):
        nlangs=len(self.program.db.audiolangs)
        """if there's only one audio language, use it."""
        if self.program.db.audiolang:
            self.audiolang=self.program.db.audiolang
        else: #for three or more analangs, take the first plausible iso code
            for n in range(nlangs):
                if self.analang in self.program.db.audiolangs[n]:
                    self.audiolang=self.program.db.audiolangs[n]
                    return
    def makeglosslangs(self):
        if self.glosslangs:
            self.glosslangs=Glosslangs(self.glosslangs)
        else:
            self.glosslangs=Glosslangs()
    def checkglosslangs(self):
        if self.glosslangs:
            for lang in self.glosslangs:
                if lang not in self.program.db.glosslangs:
                    self.glosslangs.rm(lang)
        if not self.glosslangs:
            self.guessglosslangs()
    def guessglosslangs(self):
        """if there's only one gloss language, use it."""
        if len(self.program.db.glosslangs) == 1:
            log.info(_("Only one glosslang!"))
            self.glosslangs.lang1(self.program.db.glosslangs[0])
            """if there are two or more gloss languages, just pick the first
            two, and the user can select something else later (the gloss
            languages are not for CV profile analaysis, but for info after
            checking, when this can be reset."""
        elif len(self.program.db.glosslangs) > 1:
            self.glosslangs.lang1(self.program.db.glosslangs[0])
            self.glosslangs.lang2(self.program.db.glosslangs[1])
        else:
            print("Can't tell how many glosslangs!",len(self.program.db.glosslangs))
    def guesscvt(self):
        """For now, if cvt isn't set, start with Vowels."""
        self.set('cvt','V')
    def refreshattributechanges(self):
        """I need to think through these; what things must/should change when
        one of these attributes change? Especially when we've changed a few...
        """
        if not hasattr(self,'attrschanged'):
            return
        if 'status' in program:
            self.program.status.build()
        t=self.program.params.cvt()
        if 'cvt' in self.attrschanged:
            self.program.status.updatechecksbycvt()
            self.program.status.makecheckok()
            self.attrschanged.remove('cvt')
        if 'ps' in self.attrschanged:
            if t == 'T':
                self.program.status.updatechecksbycvt()
            self.attrschanged.remove('ps')
        if 'profile' in self.attrschanged:
            if t != 'T':
                self.program.status.updatechecksbycvt()
            self.attrschanged.remove('profile')
        if 'check' in self.attrschanged:
            self.attrschanged.remove('check')
        if 'interfacelang' in self.attrschanged:
            self.attrschanged.remove('interfacelang')
        if 'glosslangs' in self.attrschanged:
            self.attrschanged.remove('glosslangs')
            if isinstance(self.program.taskchooser.task,WordCollection):
                self.program.taskchooser.task.getword() #update UI for glosses
        if 'secondformfield' in self.attrschanged:
            self.attrschanged.remove('secondformfield')
        soundattrs=self.settings['soundsettings']['attributes']
        soundattrschanged=set(soundattrs) & set(self.attrschanged)
        for a in soundattrschanged:
            self.storesettingsfile(setting='soundsettings')
            self.attrschanged.remove(a)
            break
        if self.attrschanged != []:
            log.error(_("Remaining changed attribute! ({attr})").format(
                                                        attr=self.attrschanged))
    def maketoneframes(self,dict={}):
        ToneFrames(dict,self.program)
        # ToneFrames(getattr(self,'toneframes',{}))
    def makestatus(self,dict={}):
        # log.info("Making status object with value {}".format(self.program.status))
        StatusDict(self.settingsfile('status'), dict, self.program)
        # log.info("Made status object with value {}".format(self.program.status))
    def set(self,attribute,choice,window=None,refresh=True):
        #Normally, pass the attribute through the button frame,
        #otherwise, don't set window (which would be destroyed)
        #Set refresh=False (or anything but True) to not redo the main window
        #afterwards. Do this to save time if you are setting multiple variables.
        log.info(_("Setting {attr} variable with value: {val} ({old})").format(
                attr=attribute,val=choice,
                old=getattr(self,attribute,"Not Present")))
        if window is not None:
            window.destroy()
        if not hasattr(self,attribute) or getattr(self,attribute) != choice: #only set if different
            setattr(self,attribute,choice)
            self.attrschanged.append(attribute)
            """If there's something getting reset that shouldn't be, remove it
            from self.defaultstoclear[attribute]"""
            self.cleardefaults(attribute)
            if attribute in ['analang',  #do the last two cause problems?
                                'interpret','distinguish']:
                # self.reloadprofiledata()
                log.info(_("**Changed {attr}; should restart!**").format(attr=attribute))
            elif refresh == True:
                self.refreshattributechanges()
        else:
            log.debug(_("No change: {attr} == {val}").format(attr=attribute,val=choice))
    def statusisup(self):
        """Use this for when a setting should ignore status frame updates"""
        return (hasattr(self.program.taskchooser.mainwindowis,'status') and
                type(self.program.taskchooser.mainwindowis.status) is StatusFrame)
    def setsecondformfieldN(self,choice,window=None):
        self.secondformfield[self.nominalps]=self.pluralname=choice
        if self.statusisup():
            self.program.taskchooser.mainwindowis.status.updatefields()
        self.attrschanged.append('secondformfield')
        for entry in self.program.db.entries:
            entry.plvalue(self.pluralname) # get the right field!
        self.refreshattributechanges()
        if window:
            window.destroy()
    def setsecondformfieldV(self,choice,window=None):
        self.secondformfield[self.verbalps]=self.imperativename=choice
        if self.statusisup():
            self.program.taskchooser.mainwindowis.status.updatefields()
        self.attrschanged.append('secondformfield')
        for entry in self.program.db.entries:
            """Doesn't do anything??!?"""
            entry.fieldvalue(self.imperativename,self.program.params.analang) # get the right field!
        self.refreshattributechanges()
        if window:
            window.destroy()
    def setprofile(self,choice=None,window=None):
        if not choice:
            choice=self.program.status.nextprofile()
        self.program.slices.profile(choice)
        self.program.taskchooser.mainwindowis.status.updateprofile()
        if self.program.params.cvt() != 'T': #profiles don't determine tone checks
            #in case checks changed:
            firstcheck=self.program.status.updatechecksbycvt()[0]
            if self.program.params.check() != firstcheck:
                self.program.params.check(firstcheck)
                self.attrschanged.append('check')
        self.attrschanged.append('profile')
        self.refreshattributechanges()
        if window:
            window.destroy()
    def setcvt(self,choice,window=None):
        self.program.params.cvt(choice)
        self.attrschanged.append('cvt')
        if self.statusisup():
            self.program.taskchooser.mainwindowis.status.updatecvt()
        self.refreshattributechanges()
        if (not hasattr(self.program.taskchooser,'task') or
                not self.program.taskchooser.task.mainwindow):
            log.info(_("No task, apparently, so not worried about changing cvt"))
        elif isinstance(self.program.taskchooser.task,Transcribe):
            log.info(_("Switching Transcribe tasks"))
            newtaskclass=getattr(sys.modules[__name__],'Transcribe'+choice)
            self.program.status.makecheckok() #this is intentionally broad: *any* check
            self.program.taskchooser.maketask(newtaskclass)
        elif isinstance(self.program.taskchooser.task,Sort):
            # log.info("Switching Sort tasks")
            newtaskclass=getattr(sys.modules[__name__],'Sort'+choice)
            self.program.status.makecheckok() #this is intentionally broad: *any* check
            self.program.taskchooser.maketask(newtaskclass)
        else:
            log.info(_("Not Sorting or Transcribing; chilling with cvt change."))
        if window:
            window.destroy()
    def setanalang(self,choice,window):
        """This is only used when more than one analang exists in the database"""
        log.info(_("Setting Analysis Language to {lang}").format(lang=choice))
        self.program.params.analang(choice)
        self.program.taskchooser.mainwindowis.status.updateanalang()
        self.attrschanged.append('analang')
        self.refreshattributechanges()
        window.destroy()
        self.program.taskchooser.restart()
    def setgroup(self,choice,window):
        log.debug(_("setting group: {group}").format(group=choice))
        self.program.status.group(choice)
        if self.program.params.cvt() == 'T':
            self.program.taskchooser.mainwindowis.status.updatetonegroup()
        else:
            self.program.taskchooser.mainwindowis.status.updatecvgroup()
        if isinstance(self.program.taskchooser.task,Sort) and (
                hasattr(self.program.taskchooser.task,'menu') and
                        self.program.taskchooser.task.menu):
            self.program.taskchooser.task.menubar.redoadvanced()
        window.destroy()
        log.debug(_("group {group} set: {val}").format(group=choice, val=self.program.status.group()))
    def setgroup_comparison(self,choice,window):
        """This doesn't show up on the status window"""
        if hasattr(self,'group_comparison'):
            log.debug(_("group_comparison: {val}").format(val=self.group_comparison))
        self.set('group_comparison',choice,window,refresh=False)
        log.debug(_("group_comparison: {val}").format(val=self.group_comparison))
    def setcheck(self,choice=None,window=None,**kwargs):
        if not choice:
            choice=self.program.status.nextcheck(**kwargs)
        self.program.params.check(choice)
        if self.program.params.cvt() == 'T':
            self.program.taskchooser.mainwindowis.status.updatetoneframe()
        else:
            self.program.taskchooser.mainwindowis.status.updatecvcheck()
        self.attrschanged.append('check')
        self.refreshattributechanges()
        if window:
            window.destroy()
    def setbuttoncolumns(self,choice,window=None):
        self.buttoncolumns=self.program.taskchooser.mainwindowis.buttoncolumns=choice
        if self.statusisup():
            self.program.taskchooser.mainwindowis.status.updatebuttoncolumns()
        if window:
            window.destroy()
    def setmaxprofiles(self,choice,window):
        self.maxprofiles=choice
        self.program.taskchooser.mainwindowis.status.updatemaxprofiles()
        window.destroy()
    def setmaxpss(self,choice,window):
        self.maxpss=choice
        self.program.taskchooser.mainwindowis.status.updatemaxpss()
        window.destroy()
    def setmulticheckscope(self,choice,window):
        self.cvtstodo=self.program.taskchooser.task.cvtstodo=choice
        self.program.taskchooser.mainwindowis.status.updatemulticheckscope()
        window.destroy()
    def setglosslang(self,choice,window):
        self.glosslangs.lang1(choice)
        self.program.taskchooser.mainwindowis.status.updateglosslangs()
        self.attrschanged.append('glosslangs')
        self.refreshattributechanges()
        window.destroy()
    def setglosslang2(self,choice,window):
        if choice:
            self.glosslangs.lang2(choice)
        elif len(self.glosslangs)>1:
            self.glosslangs.pop(1) #if lang2 is None
        self.program.taskchooser.mainwindowis.status.updateglosslangs()
        self.attrschanged.append('glosslangs')
        self.refreshattributechanges()
        window.destroy()
    def setparserasklevel(self,choice,window):
        self.program.taskchooser.parser.asklevel(choice)
        self.program.taskchooser.mainwindowis.status.updateparserasklevel()
        window.destroy()
    def setparserautolevel(self,choice,window):
        self.program.taskchooser.parser.autolevel(choice)
        self.program.taskchooser.mainwindowis.status.updateparserautolevel()
        window.destroy()
    def setps(self,choice,window):
        self.program.slices.ps(choice)
        self.program.taskchooser.mainwindowis.status.updateps()
        self.attrschanged.append('ps')
        self.refreshattributechanges()
        window.destroy()
    def setexamplespergrouptorecord(self,choice,window):
        self.set('examplespergrouptorecord',choice,window)
    def localize_langnames(self):
        self.languagenames={i:_(self.languagenames[i]) for i in self.languagenames}
    def langnames(self,langs={}):
        """This is for getting the prose name for a language from a code."""
        """It should ultimately use a xyz.ldml file, produced (at least)
        by WeSay, but for now is just a dict."""
        log.info(_("Setting up language names"))
        #ET.register_namespace("", 'palaso')
        ns = {'palaso': 'urn://palaso.org/ldmlExtensions/v1'}
        node=None
        if not hasattr(self,'languagenames'):
            self.languagenames={}
        #return localized strings to English, so they can localize again
        self.languagenames.update({'fr':"French", 
                                'en':"English",
                                'es':"Spanish",
                                'ar':"Arabic",
                                'zh':"Chinese",
                                'pt':"Portuguese",
                                'id':"Indonesian",
                                'ind':"Indonesian",
                                'ha':"Hausa",
                                'hau':"Hausa",
                                'swc':"Congo Swahili",
                                'swh':"Swahili",
                                'gnd':"Zulgo",
                                'fub':"Fulfulde",
                                'bfj':"Chufie’"})
        Settings.localize_langnames(self) #in case run by Taskchooser
        # self.localize_langnames()
        if hasattr(self,'adnlangnames') and self.adnlangnames:
            self.languagenames.update(self.adnlangnames) #from settings
        # print(type(self.analang),type(self.program.db.analangs),type(self.program.db.glosslangs))
        if not langs:
            langs=self.program.db.analangs+self.program.db.glosslangs
            if hasattr(self,'analang'):
                langs.append(self.analang)
        langs=set(langs)
        self.languagenames.update({i:_("Language with code [{code}]").format(code=i) 
                                    for i in langs
                                    if i not in self.languagenames
                                    })
        # for xyz in langs+self.program.interfacelangs:
        #     default=_("Language with code [{code}]").format(code=xyz)
        #     # log.info(' '.join('Looking for language name for',xyz))
        #     setnesteddictobjectval(self,'languagenames',
        #                             d.get(xyz,default),
        #                             xyz)
        """This provides an ldml node implement this some day"""
        #log.info(' '.join(tree.nodes.find(f"special/palaso:languageName", namespaces=ns)))
        #nsurl=tree.nodes.find(f"ldml/special/@xmlns:palaso")
        """This doesn't seem to be working; I should fix it, but there
        doesn't seem to be reason to generalize it for now."""
        # tree=ET.parse(self.languagepaths[xyz])
        # tree.nodes=tree.getroot()
        # node=tree.nodes.find(f"special/palaso:languageName", namespaces=ns)
        # if node is not None:
        #     self.languagenames[xyz]=node.get('value')
        #     log.info(' '.join('found',self.languagenames[xyz]))
        # if not hasattr(self,'adnlangnames') or self.adnlangnames is None:
        #     self.adnlangnames={}
        # if (hasattr(self,'adnlangnames') and
        #         self.adnlangnames and
        #         xyz in self.adnlangnames and
        #         self.adnlangnames[xyz]):
        #     self.languagenames[xyz]=self.adnlangnames[xyz]
    def makeeverythingok(self):
        try:
            self.program.status.makecvtok()
            self.program.slices.makepsok()
            self.program.slices.makeprofileok()
            self.program.status.makecheckok() #this is intentionally broad: *any* check
        except KeyError as e:
            log.info(_("Maybe status/slices aren't set up yet."))
        # self.program.status.makegroupok(wsorted=True)
    def setrefreshdelay(self):
        """This sets the main window refresh delay, in miliseconds"""
        if (hasattr(self.program.taskchooser.mainwindowis,'runwindow') and
                self.program.taskchooser.mainwindowis.runwindow.winfo_exists()):
            self.refreshdelay=10000 #ten seconds if working in another window
        elif isinstance(self,Parse) and not hasattr(self,'parser'):
            self.refreshdelay=1 #1 msecond if waiting for parser settings
        else:
            self.refreshdelay=1000 #one second if not working in another window
    def __init__(self,program):
        self.program=program
        self.program.settings=self
        # self.taskchooser = self.program.taskchooser
        self.liftfilename=self.program.filename
        self.directory=file.getfilenamedir(self.liftfilename)
        
        # Get base path for settings files
        self.liftnamebase=rx.pymoduleable(file.getfilenamebase(self.liftfilename))
        basename=file.getdiredurl(self.directory,self.liftnamebase)
        
        # Trigger migration if necessary
        migrator = migration.MigrationManager(basename)
        if migrator.migrate():
            log.info(_("Settings migrated to new format."))
        
        # Initialize new modular SettingsManager
        self.mgr = settings.SettingsManager(basename)
        
        self.getdirectories() #incl settingsfilecheck and repocheck
        self.setvalidcharacters()
        self.settingsinit() #init, clear, fields
        self.loadsettingsfile()
        self.loadsettingsfile(setting='profiledata')
        """I think I need this before setting up regexs"""
        self.langnames(self.program.interfacelangs)
        _tc = getattr(self.program, 'taskchooser', None)
        if _tc is not None and hasattr(_tc,'analang'): #i.e., new file
            self.analang=_tc.analang #I need to keep this alive until objects are done
            self.storesettingsfile() #write analang to file
        log.info(_("Settings initialized"))
    def post_lift_init(self):
        """These settings require the LIFt db be up and parsed already"""
        self.dont_guessanalang() #needed for regexs
        if not self.analang:
            log.error(_("No analysis language; exiting."))
            return
        #set the field names used in this db:
        self.pss() #sets self.nominalps and self.verbalps
        self.fields() #sets self.pluralname and self.imperativename
        self.langnames()
        self.guessaudiolang()
        self.loadsettingsfile() # overwrites guess above, stored on runcheck
        self.makeglosslangs()
        self.checkglosslangs() #if stated aren't in db, guess
        self.attrs_moved_to_object=set()
        self.settingsobjects() #should do this more; can be redone!
        self.trackuntrackedfiles()
        if not self.buttoncolumns:
            self.setbuttoncolumns(1)
        # these two make the objects
        self.loadsettingsfile(setting='status')
        self.loadsettingsfile(setting='toneframes')
        self.loadsettingsfile(setting='adhocgroups')
        self.loadsettingsfile(setting='alphabet')
        self.makeeverythingok()
        """The following might be OK here, but need to be OK later, too."""
        # """The following should only be done after word collection"""
        # if self.taskchooser.donew['collectionlc']:
        #     self.ifcollectionlc()
        self.attrschanged=[]
        log.info(_("Settings (Post lift) initialized"))

if __name__ == '__main__':
    # global _
    # try: #translation
    #     _
    # except NameError:
    #     def _(x):
    #         return x
    # from dummy import App,TaskChooser
    from main import App,TaskChooser
    program=App({'version':'0.0b',
                'name':'test',
                'hostname':'test',
                'testing':False,
                'exceptiononload':False,
                'theme':'Kim'})
    program.taskchooser=TaskChooser()
    program.taskchooser.filename="test.lift"
    program.testing=True
    Settings(program)