
from .manager import ConfigParser, write_ini, read_ini
from .project import ProjectConfig
from .ui import UIConfig
from .audio import AudioConfig
from .alphabet import AlphabetConfig
from .contributors import ContributorsConfig
from .data import DataConfig
from .reports import ReportsConfig
from .app import AppConfig


class AppSettingsManager:
    """Pre-project settings manager (before any LIFT file is loaded).
    Stores last opened filename, list of known filenames, and UI language.
    Config file: <aztdir>/azt.<user>.<hostname>.preproject.json
    """
    def __init__(self, base_path, hostname=None, user=None):
        self.app = AppConfig(base_path, hostname, user)

    @property
    def filename(self):
        return self.app.get_filename()

    @filename.setter
    def filename(self, value):
        self.app.set_filename(value)

    @property
    def filenames(self):
        return self.app.get_filenames()

    @property
    def ui_lang(self):
        return self.app.get_ui_lang()

    @ui_lang.setter
    def ui_lang(self, value):
        self.app.set_ui_lang(value)

class SettingsManager:
    """
    Centralized settings manager that provides access to all domains.
    Use get(attr)/set(attr, value) for routing to the correct domain.
    """
    def __init__(self, base_path, hostname=None, user=None):
        self.project = ProjectConfig(base_path, hostname, user)
        self.ui = UIConfig(base_path, hostname, user)
        self.audio = AudioConfig(base_path, hostname, user)
        self.alphabet = AlphabetConfig(base_path, hostname, user)
        self.contributors = ContributorsConfig(base_path, hostname, user)
        self.data = DataConfig(base_path, hostname, user)
        self.reports = ReportsConfig(base_path, hostname, user)
        self._domains = {
            'project': self.project,
            'ui': self.ui,
            'audio': self.audio,
            'alphabet': self.alphabet,
            'contributors': self.contributors,
            'data': self.data,
            'reports': self.reports,
        }

    def domain_for(self, attr):
        """Return the ConfigManager instance that owns the given attribute."""
        from migration.converters import Converter
        domain_name = Converter.domain_for_attr(attr)
        if domain_name and domain_name in self._domains:
            return self._domains[domain_name]
        return None

    def get(self, attr, default=None):
        """Get a setting value by attribute name, routing to the correct domain."""
        domain = self.domain_for(attr)
        if domain is not None:
            return domain.get(attr, default)
        return default

    def set(self, attr, value):
        """Set a setting value by attribute name, routing to the correct domain."""
        domain = self.domain_for(attr)
        if domain is not None:
            domain.set(attr, value)

    def save_all(self):
        for domain in self._domains.values():
            domain.save()


# ---------------------------------------------------------------------------
# Settings: full settings class combining backend logic with UI (SettingsUI)
# ---------------------------------------------------------------------------

import gettext as _gettext
_builtins_gettext = _gettext.gettext
import sys
import importlib
import threading
import configparser as _configparser
import migration
from . import manager
from utilities import logsetup as _logsetup
from utilities import file
from utilities.utilities import *

_log = _logsetup.getlog(__name__)


from utilities.error_handler import notify_error as ErrorNotice

from utilities.i18n import _
from utilities import rx
from backend.core.lexicon import Tone, Segments, WordCollection, Parse
from backend.core.analysis import SliceDict, StatusDict
from backend.core.analysis_inputs import Glosslangs, ToneFrames



from frontend.config.settings_ui import SettingsUI


class Settings(SettingsUI):
    """Full Settings class: backend logic + UI methods from SettingsUI."""
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
                                'nominalps',
                                'verbalps',
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
            err=file.move(getattr(self,legacy), getattr(self,fileattr))
            if err:
                _log.error(err)
        if hasattr(self,fileattr):
            return getattr(self,fileattr)
        else:
            _log.error(_("No file name for setting {setting}!").format(setting=setting))
    def loadandconvertlegacysettingsfile(self,setting='defaults'):
        #This should be removed at some point Only used when find old file NAME
        savefile=self.settingsfile(setting)
        legacy=savefile.with_suffix('.py')
        _log.info(_("Going to make {legacy_name} into {savefile}").format(legacy_name=legacy,savefile=savefile))
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
            _log.debug(_("Trying for {setting} settings in {legacy_name}").format(setting=setting, legacy_name=legacy))
            spec = importlib.util.spec_from_file_location(setting,legacy)
            module = importlib.util.module_from_spec(spec)
            sys.modules[setting] = module
            spec.loader.exec_module(module)
            for s in self.settings[setting]['attributes']:
                if s in oldnames and hasattr(module,oldnames[s]):
                    setattr(o,s,getattr(module,oldnames[s]))
                    _log.info(_("Imported and upgraded {s}/{old}: {val}").format(
                                                    s=s,old=oldnames[s],val=getattr(o,s)))
                elif hasattr(module,s):
                    setattr(o,s,getattr(module,s))
                    _log.info(_("Imported {s}: {val}").format(s=s,val=getattr(o,s)))
                else:
                    _log.info(_("Attribute {s} not found").format(s=s))
            _log.info(_("Importing {setting} settings done.").format(setting=setting))
        except Exception as e:
            _log.error(_("Problem importing {legacy} ({error})").format(legacy=legacy,error=e))
        # b/c structure changed:
        if 'glosslangs' in self.settings[setting]['attributes']:
            self.glosslangs=[]
            for lang in ['glosslang','glosslang2']:
                if hasattr(module,lang):
                    self.glosslangs.append(getattr(module,lang))
                    try:
                        delattr(self,lang) #because this would be made above
                    except AttributeError:
                        _log.info(_("attribute {lang} doesn't seem to be there").format(lang=lang))
        dict1=self.makesettingsdict(setting=setting)
        self.storesettingsfile(setting=setting) #do last
        self.loadsettingsfile(setting=setting) #verify write and read
        dict2=self.makesettingsdict(setting=setting)
        """Now we verify that each value read the same each time"""
        for s in dict1:
            if s in dict2 and str(dict1[s]) == str(dict2[s]):
                _log.info(_("Attribute {s} verified as {val1}={val2}").format(s=s,
                                            val1=str(dict1[s]), val2=str(dict2[s])))
            elif s in dict2:
                _log.error(_("Problem with attribute {s}; {val1}≠{val2}").format(s=s,
                                            val1=str(dict1[s]), val2=str(dict2[s])))
            else:
                _log.error(_("Attribute {s} didn't make it back").format(s=s))
                _log.error(_("You should send in an error report for this."))
                exit()
        _log.info(_("Settings file {legacy} converted to {savefile}, with each value verified.")
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
                _log.debug(_("{file} doesn't exist!").format(file=savefile))
                legacy=savefile.with_suffix('.py')
                if file.exists(legacy):
                    _log.debug(_("But legacy file {legacy} does; converting!").format(legacy=legacy))
                    self.loadandconvertlegacysettingsfile(setting=setting)
            if file.exists(savefile): #Keep around .ini and .dat
                for r in self.program.data_repo:
                    self.program.data_repo[r].add(savefile)
        #This line as is causes merge conflicts unnecessarilyː
        # self.repo_commit() #this will be taken up later, or else done again
    def moveattrstoobjects(self):
        # _log.info("Glosslangs (in moveattrstoobjects): {}".format(self.glosslangs.langs()))
        # _log.info(f"moveattrstoobjects done: {self.attrs_moved_to_object}")
        to_do=set(self.fndict)-self.attrs_moved_to_object
        _log.info(f"moveattrstoobjects to do: {to_do}")
        for attr in to_do:
            if hasattr(self,attr):
                _log.info(_("moving attr {attr} to object ({val})").format(attr=attr,val=getattr(self,attr)))
                self.fndict[attr](getattr(self,attr))
                # _log.info("Glosslangs (in moveattrstoobjects): {}".format(self.glosslangs.langs()))
                if attr not in ['glosslangs']: #obj and attr have same name...
                    delattr(self,attr)
                self.attrs_moved_to_object.add(attr)
            else:
                _log.info(_("attr {attr} not found!").format(attr=attr))
        _log.info(_("attrs_moved_to_object={val}").format(val=self.attrs_moved_to_object))
        # _log.info("Glosslangs (in moveattrstoobjects): {}".format(self.glosslangs.langs()))
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
            # fns['status']=self.program.alphabet.status
            # fns['status']=self.program.status #I think this is redundant
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
            # except this one, which pretends to set but doesn't (throws arg away)
            fns['profilecounts']=self.program.slices.slicepriority
            fns['giturls']=self.program.data_repo['git'].remoteurls
            fns['asr_repos']=self.program.soundsettings.asr_repo_tally
            fns['asr_kwargs']=self.program.soundsettings.asr_kwarg_dict
            fns['hgurls']=self.program.data_repo['hg'].remoteurls
        except Exception as e:
            _log.error(_("Only finished settingsobjects up to {keys} ({error})").format(keys=fns.keys(),error=e))
            self.moveattrstoobjects() #always do this next
            return []
        _log.info(_("Finished settingsobjects up to {keys}").format(keys=fns.keys()))
        self.moveattrstoobjects() #always do this next
    def makesettingsdict(self,setting='defaults'):
        """This returns a dictionary of values, keyed by a set of settings"""
        """It pulls from objects if it can, otherwise from self attributes
        (if there), for backwards compatibility, when converting from legacy
        files before the objects are created."""
        d={}
        if setting == 'soundsettings':
            o=self.soundsettings
        elif setting == 'profiledata':
            o=getattr(self.program, 'profiles', self)
        else:
            o=self
        for s in self.settings[setting]['attributes']:
            # _log.info("Looking for {} attr".format(s))
            # _log.info("{} attr value: {}".format(s,getattr(o,s,'Not Found!')))
            """This dictionary of functions isn't made until after the objects,
            at the end of settings init. So this block is not used in
            conversion, only in later saves."""
            if hasattr(self,'fndict') and s in self.fndict:
                # _log.info("Trying to dict {} attr".format(s))
                try:
                    d[s]=self.fndict[s]()
                    # _log.info("Value {}={} found in object".format(s,d[s]))
                except:
                    _log.error(_("Value of {attr} not found in object").format(attr=s))
            elif hasattr(o,s):
                if getattr(o,s) or setting == 'soundsettings': #store Falses
                    d[s]=getattr(o,s)
                # _log.info("Set to dict self.{} with value {}, type {}"
                #         "".format(s,d[s],type(d[s])))
            # else:
            #     _log.error("Couldn't find {} in {}".format(s,setting))
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
            if isinstance(v,_configparser.SectionProxy):
                continue #don't store expty section headers
            elif hasattr(self,'fndict') and s in self.fndict:
                # _log.info("Trying to read {} to object with value {} and fn "
                #             "{}".format(s,v,self.fndict[s]))
                self.fndict[s](v)
            elif s == 'status' and not hasattr(self.program,'status'): #Only load this once
                self.makestatus({k:v[k] for k in v if k != 'DEFAULT'})
            elif (isinstance(v,dict) and
                hasattr(o,s) and isinstance(getattr(o,s),dict)):
                getattr(o,s).update(v)
            else:
                # _log.info("Trying to read {} to {} with value {}, type {}"
                #             "".format(s,o,v,type(v)))
                setattr(o,s,v)
        return settingsdict
    def storesettingsfile(self,setting='defaults'):
        if setting in ['status', 'toneframes']:
            d=getattr(self.program, setting)
        else:
            d=self.makesettingsdict(setting=setting)

        if setting in self.domain_mapping:
            for domain_name in self.domain_mapping[setting]:
                domain_mgr = getattr(self.mgr, domain_name)
                # We need to filter and update the domain data
                domain_attrs = migration.converters.Converter.DOMAIN_MAPPING[domain_name]
                domain_data = {k: v for k, v in d.items() if k in domain_attrs}
                if domain_data:
                    current_data = domain_mgr.load()
                    current_data.update(domain_data)
                    domain_mgr.save(current_data)
                    _log.info(_("Stored {setting} settings in new {domain} domain").format(setting=setting, domain=domain_name))

        # Legacy storage for backup/compatibility
        filename=self.settingsfile(setting)
        if not filename:
             return
        write_ini(filename, d)
    def loadsettingsfile(self,setting='defaults'):
        # Check domain-specific manager first
        if setting in self.domain_mapping:
            for domain_name in self.domain_mapping[setting]:
                domain_mgr = getattr(self.mgr, domain_name)
                data = domain_mgr.load()
                if data:
                    _log.info(_("Loaded {setting} settings from new {domain} domain").format(setting=setting, domain=domain_name))
                    self.readsettingsdict(data)
        # Still fallback to legacy reader for now to ensure absolute compatibility
        # during the transition if JSON files were not yet created or migrated.
        filename=self.settingsfile(setting)
        if not filename or not filename.exists():
            return
        _log.info(_("Fallback check for {setting} settings in {file}").format(setting=setting, file=filename))
        sections, d = read_ini(filename, setting)
        if not sections and setting not in ['status','toneframes']:
            if setting == 'adhocgroups':
                self.adhocgroups={}
            return
        if setting == 'status':
            self.makestatus({k:d[k] for k in d if k != 'DEFAULT'})
            _log.info(_("makestatus: {status}").format(status=self.program.status))
        elif setting == 'toneframes':
            self.program.toneframes.source({k:d[k] for k in d if k != 'DEFAULT'})
            _log.info(_("maketoneframes: {frames}").format(frames=self.program.toneframes))
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
                        'writeeverynwrites':[],
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
            elif default in ['writeeverynwrites']:
                setattr(self, default, 1)
            else:
                setattr(self, default, None)
    def settingsinit(self):
        _log.info(_("Initializing settings."))
        # self.defaults is already there, from settingsfilecheck
        self.initdefaults() #provides self.defaultstoclear, needed?
        self.cleardefaults() #this resets all to none (to be set below)
    def getdirectories(self):
        self.directory=file.getfilenamedir(self.liftfilename)
        if not file.exists(self.directory):
            _log.info(_("Looks like there's a problem with your directory... {file}\n{dir}")
                    .format(file=self.liftfilename,dir=self.directory))
            exit()
        self.settingsfilecheck()
        self.imagesdir=file.getimagesdir(self.directory)
        self.audiodir=file.getaudiodir(self.directory)
        # _log.info('self.audiodir: {}'.format(self.audiodir))
        self.reportsdir=file.getreportdir(self.directory)
        self.exportsdir=file.getexportdir(self.directory)
        self.reportbasefilename=file.getdiredurl(self.reportsdir,
                                                    self.liftnamebase)
        self.reporttoaudiorelURL=file.getreldir(self.reportsdir, self.audiodir)
        # _log.info('self.reportsdir: {}'.format(self.reportsdir))
        # _log.info('self.reportbasefilename: {}'.format(self.reportbasefilename))
        # _log.info('self.reporttoaudiorelURL: {}'.format(self.reporttoaudiorelURL))
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
        _log.info(_("Looking for untracked files to add to repositories"))
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
            _log.info(_("{repo} currently has {count} files").format(repo=r,count=len(present)))
            for f in maindirfiles:
                # _log.info("{}".format([file.getreldirposix(self.program.data_repo[r].url,f)]))
                # _log.info("working on {}".format(file.getreldirposix(self.program.data_repo[r].url,f)))
                _log.info(_("working on {file}").format(file=file.getfile(f)))
                # f=file.getreldirposix(self.program.data_repo[r].url,f)
                if file.exists(f):# They won't always be there
                    self.program.data_repo[r].add(file.getreldirposix(self.program.data_repo[r].url,f))
            # In case I run into formatting issues again:
            # _log.info(', '.join(list(self.program.data_repo[r].files)[:5]))
            # _log.info(', '.join([file.getreldir(self.program.data_repo[r].url,i) for i in file.getfilesofdirectory(self.audiodir, '*.wav')][:5]))
            # If we ever support mp3, we should add it here:
            # _log.info("{}".format([file.getreldirposix(self.program.data_repo[r].url,i)
            #         for i in file.getfilesofdirectory(self.audiodir,
            #                                             '*.wav')]))
            # _log.info("{}".format(set(file.getreldirposix(self.program.data_repo[r].url,i)
            #         for i in file.getfilesofdirectory(self.audiodir,
            #                                             '*.wav'))))
            audiohere=set([file.getreldirposix(self.program.data_repo[r].url,i)
                    for i in file.getfilesofdirectory(self.audiodir,
                                                        '*.wav')])
            audio=audiohere-present
            _log.info(_("{wav_count} wav files to check for the {repo} repo (of {total_count} files total "
                    "here)").format(wav_count=len(audio),repo=r,total_count=len(audiohere)))
            _log.info(_("head of wav files in repo: {files}").format(files=list(present)[:10]))
            _log.info(_("head of wav files here: {files}").format(files=list(audiohere)[:10]))
            _log.info(_("head of wav files to check: {files}").format(files=list(audio)[:10]))
            for f in audio:
                self.program.data_repo[r].add(f) #These should exist, from ls above
                # if threading.active_count()<maxthreads:
                #     t = threading.Thread(target=ifnotthereadd, args=(f,r))
                #     t.start()
                # _log.info(_("trackuntrackedfiles waiting for {count} audio file threads."
                #         ).format(count=threading.active_count()))
                # if t:
                #     t.join()
                # self.program.data_repo[r].add(f)
            for ext in ['png','jpg','gif']:
                # _log.info(_("Image Directory: {dir}").format(dir=self.imagesdir))
                # _log.info("Found image files: {}".format(nn([i for i in
                # file.getfilesofdirectory(self.imagesdir,
                #                         '*.'+ext)], oneperline=True)))
                i=set([file.getreldirposix(self.program.data_repo[r].url,i)
                        for i in file.getfilesofdirectory(self.imagesdir,
                                                '*.'+ext)]
                        )-present
                _log.info(_("{count} {extension} files to check for the {repo} repo")
                        .format(count=len(i),extension=ext,repo=r))
                for f in i:
                    self.program.data_repo[r].add(f) #These should exist, from ls above
                    # if threading.active_count()<maxthreads:
                    #     u = threading.Thread(target=ifnotthereadd, args=(f,r))
                    #     u.start()
                    # _log.info("trackuntrackedfiles waiting for {} {} file "
                    #     "threads.".format(threading.active_count(),ext))
                        # if u:
                        #     u.join()
        _log.info(_("trackuntrackedfiles finished."))
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
    def guess_nominalps(self):
        topn=3 #just in case N and V aren't the first two, finish with top
        n_opts=['N','n','Noun','noun', 'Nom','nom','S','s',
                'Sustantivo','sustantivo']
        _log.info(_("Looking for any of {opts} in {pss}"
                    "").format(opts=n_opts, pss=self.program.db.pss))
        for ps in reversed(self.program.db.pss[:topn]):
            if ps in n_opts:
                self.nominalps=ps
                break
        if not hasattr(self,'nominalps'): #don't leave without something
            self.nominalps='Noun'
    def guess_verbalps(self):
        topn=3 #just in case N and V aren't the first two, finish with top
        v_opts=['V','v','Verb','verb', 'Verbe','verbe', 'Verbo','verbo']
        _log.info(_("Looking for any of {opts} in {pss}"
                    "").format(opts=v_opts, pss=self.program.db.pss))
        for ps in reversed(self.program.db.pss[:topn]):
            if ps in v_opts:
                self.verbalps=ps
                break
        if not hasattr(self,'verbalps'): #don't leave without something
            self.verbalps='Verb'
    def pss(self):
        nones=[None,'','None','null','Null']
        if getattr(self,'nominalps',None) not in nones:
            log.info(_("Found nominal ps {ps} in settings").format(ps=self.nominalps))
        else:
            self.guess_nominalps()
        if getattr(self,'verbalps',None) not in nones:
            log.info(_("Found verbal ps {ps} in settings").format(ps=self.verbalps))
        else:
            self.guess_verbalps()
        try:
            _log.info(_("Using '{noun}' for nouns, and '{verb}' for verbs").format(
                noun=self.nominalps,
                verb=self.verbalps))
        except AttributeError:
            _log.info(_("Problem with finding a nominal and verbal lexical "
            "category (looked in first two of [{pss}])")
            .format(pss=self.program.db.pss))
    def makesecondformfieldsOK(self):
        if self.nominalps not in self.secondformfield:
            self.program.mainwindow.getsecondformfieldN()
        if self.verbalps not in self.secondformfield:
            self.program.mainwindow.getsecondformfieldV()
    def secondformfieldsOK(self):
        if (self.nominalps in self.secondformfield and
            self.verbalps in self.secondformfield):
            return True
    def fields(self):
        """I think this is lift specific; may move it to defaults, if not."""
        # _log.info(self.program.db.fieldnames)
        try:
            self.fieldnames=self.program.db.fieldnames[self.analang]
        except KeyError:
            self.fieldnames=[]
        _log.info(_("Fields found in lexicon: {fields}").format(fields=self.fieldnames))
    def guess_nominal_secondformfield(self):
        self.plopts=['Plural', 'plural', 'pl', 'Pluriel', 'pluriel']
        for opt in self.plopts:
            if opt in self.fieldnames:
                self.secondformfield[self.nominalps]=self.pluralname=opt
                break
        try:
            _log.info(_("Plural field name: {name}").format(name=self.pluralname))
            for entry in self.program.db.entries:
                entry.fieldvalue(self.pluralname,self.analang) # get the right field!
        except AttributeError:
            _log.info(_('Looks like there is no Plural field in the database'))
            self.pluralname=None
    def guess_verbal_secondformfield(self):
        self.impopts=['Imperative', 'imperative', 'imp', 'Imp', 
                        'Imperatif', 'imperatif']
        for opt in self.impopts:
            if opt in self.fieldnames:
                self.secondformfield[self.verbalps]=self.imperativename=opt
                break
        try:
            _log.info(_("Imperative field name: {name}").format(name=self.imperativename))
            for entry in self.program.db.entries:
                entry.fieldvalue(self.imperativename,self.analang) # get the right field!
        except AttributeError:
            _log.info(_('Looks like there is no Imperative field in the database'))
            self.imperativename=None
    def secondformfields(self):
        if hasattr(self,'secondformfield') and self.secondformfield:
            if self.nominalps in self.secondformfield:
                self.pluralname=self.secondformfield[self.nominalps]
            elif self.nominalps:
                self.guess_nominal_secondformfield()
            if self.verbalps in self.secondformfield:
                self.imperativename=self.secondformfield[self.verbalps]
            elif self.verbalps:
                self.guess_verbal_secondformfield()
        else:
            self.secondformfield={}
            self.guess_nominal_secondformfield()
            self.guess_verbal_secondformfield()
    def reloadstatusdatabycvtpsprofile(self,**kwargs):
        # This reloads the status info only for current slice
        # These are specified in iteration, pulled from object if called direct
        if kwargs.get('reporttime'):
            start_time=nowruntime()
        kwargs['cvt']=kwargs.get('cvt',self.program.params.cvt())
        kwargs['ps']=kwargs.get('ps',self.program.slices.ps())
        kwargs['profile']=kwargs.get('profile',self.program.slices.profile())
        if kwargs.get('reporttime'):
            _log.info(_("Refreshing {cvt} {ps} {profile} status settings from LIFT")
                .format(cvt=kwargs['cvt'],ps=kwargs['ps'],profile=kwargs['profile']))
        checks=self.program.status.checks(**kwargs)
        kwargs['store']=False #do below
        for kwargs['check'] in checks:
            # _log.info("Working on {}".format(c))
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
        _log.info(_("Refreshing {ps} {cvt} status settings from LIFT").format(
                                                                ps=kwargs['ps'],
                                                                cvt=kwargs['cvt']))
        profiles=self.program.slices.profiles(ps=kwargs['ps']) #This depends on ps only
        for kwargs['profile'] in profiles:
            # _log.info("Working on {}".format(p))
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
                # _log.info(f"{k} is in both dictionaries! ({k in x=} {k in y=})")
                if isinstance(x[k],dict) and isinstance(y[k],dict):
                    report(x[k],y[k],k)
        report(x,y)
    def reloadstatusdata(self):
        _log.info(_("Refreshing all status settings from LIFT"))
        self.storesettingsfile() #default, not status
        self.program.db.load_ps_profiles()
        d=self.program.db.annotation_values_by_ps_profile()
        t=self.program.db.tone_values_by_ps_profile()
        # _log.info(f"Found this LIFT file: {self.program.db.filename}")
        # _log.info(f"Found these LIFT annotations: {d}")
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
                    # _log.info(f"storing {k} unverified values: {groups}")
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
            # _log.info("Marking sense {} tosort (v: {})".format(sense.id,v))
            if not kwargs.get('cvt'): #default, not on iteration
                self.program.status.marksensetosort(sense)
            tosort=True
        else:
            # _log.info("Marking sense {} sorted (v: {})".format(sense.id,v))
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
        # _log.info("updatesortingstatus called with store={} and kwargs: {}"
        #         "".format(store,kwargs))
        cvt=kwargs.get('cvt',self.program.params.cvt())
        ps=kwargs.get('ps',self.program.slices.ps())
        profile=kwargs.get('profile',self.program.slices.profile())
        check=kwargs.get('check',self.program.params.check())
        kwargs['wsorted']=True #ever not?
        senses=self.program.slices.senses(ps=ps,profile=profile)
        # _log.info("Working on {} {} {} senses (first 5): {}".format(len(senses),
        #                                                             ps,profile,
        #                                                             senses[:5]))
        _log.info(_("Working on {count} sense.ids (first 5): {ids}").format(count=len(senses),
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
            # _log.info("Working on sense {}".format(sense.id))
            self.categorizebygrouping(fn,sense,**kwargs)
        """update 'tosort' status"""
        """update status groups"""
        sorted=set(self._groups)
        self.program.status.groups(list(sorted),**kwargs)
        if store:
            # _log.info(f"updatesortingstatus storing {kwargs=} {self.program.status=}")
            self.storesettingsfile(setting='status')
    def dont_guessanalang(self):
        """Analang should be easily deduceable from the lift file, and/or
        explicit in the settings."""
        self.analang=self.program.db.analang
        _log.info(_("analang in use: {analang} (If you don't like this, change it in the menus)").format(analang=self.analang))
        return
        #have this call set()?
        """if there's only one analysis language, use it."""
        nlangs=len(self.program.db.analangs)
        _log.debug(_("Found {n} analangs: {langs}").format(n=nlangs, langs=self.program.db.analangs))
        lxwdata=self.program.db.nentrieswlexemedata
        lcwdata=self.program.db.nentrieswcitationdata
        lxwdatamax=lcwdatamax=None
        for lang in [l for l in lcwdata if lcwdata[l] > 0]:
            if not lcwdatamax or lcwdata[lcwdatamax] < lcwdata[lang]:
                lcwdatamax=lang
        for lang in [l for l in lxwdata if lxwdata[l] > 0]:
            if not lxwdatamax or lxwdata[lxwdatamax] < lxwdata[lang]:
                lxwdatamax=lang
        _log.info(_("Most citation data in [{lang}] ({data})").format(lang=lcwdatamax,data=lcwdata))
        _log.info(_("Most lexeme data in [{lang}] ({data})").format(lang=lxwdatamax,data=lxwdata))
        if not nlangs:
            errortext=_("There don't seem to be any language forms in your "
            "database!")
            basename=file.getfilenamebase(self.liftfilename)
            parent=file.getfilenamebase(file.getfilenamedir(self.liftfilename))
            if parent == basename and langtags.tag_is_valid(basename):
                self.analang=parent
                errortext+=_("\n(guessing [{lang}]; if that's not correct, exit now "
                            "and fix it!)").format(lang=self.analang)
                _log.info(errortext)
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
            _log.debug(_("Only one analang in file; using it: ({lang})").format(
                                                        lang=self.program.db.analangs[0]))
            """If there are more than two analangs in the database, check if one
            of the first two is three letters long, and the other isn't"""
        elif nlangs == 2:
            if ((len(self.program.db.analangs[0]) == 3) and
                langtags.tag_is_valid(self.program.db.analangs[0]) and
                (lcwdatamax == self.program.db.analangs[0] or
                    lxwdatamax == self.program.db.analangs[0]) and
                (len(self.program.db.analangs[1]) != 3)):
                _log.debug(_("Looks like I found an iso code with data for "
                                "analang! ({lang})").format(lang=self.program.db.analangs[0]))
                self.analang=self.program.db.analangs[0] #assume this is the iso code
                self.analangdefault=self.program.db.analangs[0] #In case it gets changed.
            elif ((len(self.program.db.analangs[1]) == 3) and
                langtags.tag_is_valid(self.program.db.analangs[1]) and
                (lcwdatamax == self.program.db.analangs[1] or
                    lxwdatamax == self.program.db.analangs[1]) and
                    (len(self.program.db.analangs[0]) != 3)):
                _log.debug(_("Looks like I found an iso code with data for "
                                "analang! ({lang})").format(lang=self.program.db.analangs[1]))
                self.analang=self.program.db.analangs[1] #assume this is the iso code
                self.analangdefault=self.program.db.analangs[1] #In case it gets changed.
            elif (lcwdatamax in self.program.db.analangs and
                            langtags.tag_is_valid(lcwdatamax)):
                self.analang=lcwdatamax
                _log.debug(_("Neither analang looks like an iso code, taking the "
                "one with most citation data: {langs}").format(langs=self.program.db.analangs))
            elif (lxwdatamax in self.program.db.analangs and
                            langtags.tag_is_valid(lxwdatamax)):
                self.analang=lxwdatamax
                _log.debug(_("Neither analang looks like an iso code, taking the "
                "one with most lexeme data: {langs}").format(langs=self.program.db.analangs))
            else:
                self.analang=self.program.db.analangs[0]
                _log.debug(_("Neither analang looks like an iso code, nor has much"
                "data; taking the first one: {langs}").format(langs=self.program.db.analangs))
        else: #for three or more analangs, take the first plausible iso code
            if (lcwdatamax in self.program.db.analangs and
                        langtags.tag_is_valid(lxwdatamax)):
                self.analang=lcwdatamax
                _log.debug(_("The language with the most citation data looks like "
                "an iso code; using: {langs}").format(langs=self.program.db.analangs))
            elif lcwdatamax == lxwdatamax and lxwdatamax in self.program.db.analangs:
                self.analang=lxwdatamax
                _log.debug(_("The language with the most citation data is also "
                    "the language with the most lexeme data; using: {langs}").format(
                                                            langs=self.program.db.analangs))
            elif (lxwdatamax in self.program.db.analangs and
                        langtags.tag_is_valid(lxwdatamax)):
                self.analang=lxwdatamax
                _log.debug(_("The language with the most lexeme data looks like "
                "an iso code; using: {langs}").format(langs=self.program.db.analangs))
            else:
                for n in range(1,nlangs+1): # end with first
                    self.analang=self.program.db.analangs[-n]
                    _log.debug(_('trying {analang}').format(analang=self.analang))
                    if len(self.program.db.analangs[-n]) == 3:
                        _log.debug(_("Looks like I found an iso code for "
                                "analang! ({lang})").format(lang=self.program.db.analangs[n-1]))
                        break #stop iterating, and keep this one.
        _log.info(_("analang guessed: {lang} (If you don't like this, change it in "
                    "the menus)").format(lang=self.analang))
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
            _log.info(_("Only one glosslang!"))
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
        if hasattr(self.program, 'status'):
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
            if isinstance(self.program.task,WordCollection):
                self.program.task.getword() #update UI for glosses
        if 'secondformfield' in self.attrschanged:
            self.attrschanged.remove('secondformfield')
        soundattrs=self.settings['soundsettings']['attributes']
        soundattrschanged=set(soundattrs) & set(self.attrschanged)
        for a in soundattrschanged:
            self.storesettingsfile(setting='soundsettings')
            self.attrschanged.remove(a)
            break
        if self.attrschanged != []:
            _log.error(_("Remaining changed attribute! ({attr})").format(
                                                        attr=self.attrschanged))

        # Trigger update of all visible status frames via their bound variables
        status = getattr(self.program.mainwindow, 'status', None)
        if status:
            # We use try/except in case the status frame doesn't have the method yet
            try:
                status.update_all_labels()
            except AttributeError:
                pass
        
        # Also check taskchooser status just in case it's visible but not 'mainwindow'
        tc = getattr(self.program, 'taskchooser', None)
        if tc:
            tc_status = getattr(tc, 'status', None)
            if tc_status and tc_status != status:
                try:
                    tc_status.update_all_labels()
                except AttributeError:
                    pass
    def maketoneframes(self,dict={}):
        ToneFrames(dict,self.program)
        # ToneFrames(getattr(self,'toneframes',{}))
    def makestatus(self,dict={}):
        # _log.info("Making status object with value {}".format(self.program.status))
        StatusDict(self.settingsfile('status'), dict, self.program)
        # _log.info("Made status object with value {}".format(self.program.status))
    def localize_langnames(self):
        self.languagenames={i:_(self.languagenames[i]) for i in self.languagenames}
    def langnames(self,langs={}):
        """This is for getting the prose name for a language from a code."""
        """It should ultimately use a xyz.ldml file, produced (at least)
        by WeSay, but for now is just a dict."""
        _log.info(_("Setting up language names {langs}").format(langs=langs))
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
                                'bfj':"Chufie'"})
        try:
            self.localize_langnames() #in case run by Taskchooser
        except AttributeError:
            Settings.localize_langnames(self) #in case run by Liftchooser
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
    def setrefreshdelay(self):
        """This sets the main window refresh delay, in miliseconds"""
        if (hasattr(self.program.mainwindow,'runwindow') and
                self.program.mainwindow.runwindow.winfo_exists()):
            self.refreshdelay=10000 #ten seconds if working in another window
        elif isinstance(self,Parse) and not hasattr(self,'parser'):
            self.refreshdelay=1 #1 msecond if waiting for parser settings
        else:
            self.refreshdelay=1000 #one second if not working in another window
    def __init__(self,program):
        self.program=program
        self.program.settings=self
        self.ui_vars = {} # Stores tkinter.StringVar for reactive UI
        # self.taskchooser = self.program.taskchooser
        self.liftfilename=self.program.filename
        self.directory=file.getfilenamedir(self.liftfilename)

        # Get base path for settings files
        self.liftnamebase=rx.pymoduleable(file.getfilenamebase(self.liftfilename))
        basename=file.getdiredurl(self.directory,self.liftnamebase)

        # Trigger migration if necessary
        migrator = migration.MigrationManager(basename)
        if migrator.migrate():
            _log.info(_("Settings migrated to new format."))

        # Initialize new modular SettingsManager
        self.mgr = SettingsManager(basename)

        self.getdirectories() #incl settingsfilecheck and repocheck
        self.settingsinit() #init, clear, fields
        self.loadsettingsfile()
        self.loadsettingsfile(setting='profiledata')
        """I think I need this before setting up regexs"""
        self.langnames(self.program.interfacelangs)
        _tc = getattr(self.program, 'taskchooser', None)
        if _tc is not None and hasattr(_tc,'analang'): #i.e., new file
            self.analang=_tc.analang #I need to keep this alive until objects are done
            self.storesettingsfile() #write analang to file
        _log.info(_("Settings initialized"))
        # self.post_lift_init()
    def post_lift_init(self):
        """These settings require the LIFt db be up and parsed already"""
        self.dont_guessanalang() #needed for regexs
        if not self.analang:
            _log.error(_("No analysis language; exiting."))
            return
        #set the field names used in this db:
        log.info(f"{self.secondformfield=}")
        self.pss() #sets self.nominalps and self.verbalps
        self.fields() #just reports
        self.secondformfields() #sets self.pluralname and self.imperativename
        self.langnames()
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
        # self.makeeverythingok() #do in task
        """The following might be OK here, but need to be OK later, too."""
        # """The following should only be done after word collection"""
        # if self.taskchooser.donew['collectionlc']:
        #     self.ifcollectionlc()
        self.attrschanged=[]
        _log.info(_("Settings (Post lift) initialized"))
    def post_params_init(self):
        self.program.profiles.run()
    def get_ui_var(self, attr, value=None):
        """Get or create a tkinter.StringVar for the given attribute."""
        if attr not in self.ui_vars:
            # Lazy import to avoid circular dependency and only use if UI is present
            from frontend import ui
            var = ui.StringVar(value=str(value) if value is not None else str(getattr(self, attr, "")))
            self.ui_vars[attr] = var
        return self.ui_vars[attr]
