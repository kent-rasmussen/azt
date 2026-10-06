from contextlib import ExitStack, contextmanager
from .manager import read_ini
from .project import ProjectConfig
from .ui import UIConfig
from .audio import AudioConfig
from .alphabet import AlphabetConfig
from .contributors import ContributorsConfig
from .data import DataConfig
from .tone_frames import ToneFramesConfig
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

    @property
    def ui_theme(self):
        return self.app.get_ui_theme()

    @ui_theme.setter
    def ui_theme(self, value):
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
        self.tone_frames = ToneFramesConfig(base_path, hostname, user)
        self.reports = ReportsConfig(base_path, hostname, user)
        self._domains = {
            'project': self.project,
            'ui': self.ui,
            'audio': self.audio,
            'alphabet': self.alphabet,
            'contributors': self.contributors,
            'data': self.data,
            'tone_frames': self.tone_frames,
            'reports': self.reports,
        }
        # One-time relocation: toneframes briefly landed in the data domain
        # (1.10.1); move any such key to its own file so the two can't diverge.
        if 'toneframes' in self.data.data:
            if not self.tone_frames.get('toneframes'):
                self.tone_frames.save({'toneframes': self.data.data['toneframes']})
            del self.data.data['toneframes']
            self.data.save()

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

    @contextmanager
    def batch(self):
        """Defer writes across all domains for the duration of the block; each
        domain writes at most once on exit. Use to wrap a run of set()/store
        calls that don't read their file back mid-block. Example:
            with program.settings.mgr.batch():
                ...many settings.set(...) calls..."""
        with ExitStack() as stack:
            for domain in self._domains.values():
                stack.enter_context(domain.batch())
            yield self


# ---------------------------------------------------------------------------
# Settings: full settings class combining backend logic with UI (SettingsUI)
# ---------------------------------------------------------------------------

import sys
import importlib
import threading
import configparser as _configparser
import itertools
import migration
from . import manager
from utilities import logsetup as _logsetup
from utilities import file
from utilities.utilities import *

_log = _logsetup.getlog(__name__)


from utilities.error_handler import notify_error as ErrorNotice

from utilities.i18n import _
from utilities import rx
from backend.core.lexicon import Tone, Segments, Syllables, WordCollection, Parse
from backend.core.analysis import SliceDict, StatusDict
from backend.core.analysis_inputs import Glosslangs, ToneFrames



from frontend.config.settings_ui import SettingsUI


class Settings(SettingsUI):
    """Full Settings class: backend logic + UI methods from SettingsUI."""
    # Candidate second-form field names. Class attributes so they (and the
    # not-found state of the guessed names below) exist even when the UI
    # asks before guess_*_secondformfield has run:
    plopts=['Plural', 'plural', 'pl', 'Pluriel', 'pluriel']
    impopts=['Imperative', 'imperative', 'imp', 'Imp',
                'Imperatif', 'imperatif']
    pluralname=None
    imperativename=None
    domain_mapping = {
            'defaults': ['project', 'ui'],
            'soundsettings': ['audio'],
            'alphabet': ['alphabet'],
            'contributors': ['contributors'],
            'status': ['data'],
            'toneframes': ['tone_frames'],
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
                                'syllable_max_slice',
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
                                            # The NAMES the indices above were
                                            # chosen as. PortAudio renumbers
                                            # devices between runs, so an
                                            # index alone can validate cleanly
                                            # and point at a different
                                            # microphone; SoundSettings
                                            # .resolve_cards() re-points the
                                            # index by name at load, or drops
                                            # the setting when the device is
                                            # gone. (2026-09-10)
                                            'audio_card_in_name',
                                            'audio_card_out_name',
                                            'asr_kwargs',
                                            'asr_repos',
                                            'asr_in_process'
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
            from backend.core import sound
            self.soundsettings=sound.SoundSettings(self.program)
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
                        _log.info(_("attribute {lang} doesn’t seem to be there").format(lang=lang))
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
                _log.error(_("Attribute {s} didn’t make it back").format(s=s))
                _log.error(_("You should send in an error report for this."))
                raise AttributeError(s)
        _log.info(_("Settings file {legacy} converted to {savefile}, with each value verified.")
                .format(legacy=legacy,savefile=savefile))
        if setting == 'soundsettings':
            self.soundsettings.audio.stop() # when done here
    def settingsfilecheck(self):
        """We need the namebase variable to make filenames for files
        that will be imported as python modules. To do that, they need
        to not have periods (.) in their filenames. So we take the base
        name from the lift file, and replace periods with underscores,
        to make our modules basename."""
        self.liftnamebase=rx.pymoduleable(file.getfilenamebase(
                                                            self.liftfilename))
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
            savefile=self.settingsfile(setting)
            if not file.exists(savefile):
                _log.debug(_("{file} doesn’t exist!").format(file=savefile))
                legacy=savefile.with_suffix('.py')
                if file.exists(legacy):
                    _log.debug(_("But legacy file {legacy} does; converting!").format(legacy=legacy))
                    self.loadandconvertlegacysettingsfile(setting=setting)
            if file.exists(savefile): #Keep around .ini and .dat
                for r in self.program.data_repo:
                    self.program.data_repo[r].add(savefile)
    def moveattrstoobjects(self):
        to_do=set(self.fndict)-self.attrs_moved_to_object
        _log.debug(f"moveattrstoobjects to do: {to_do}")
        for attr in to_do:
            if hasattr(self,attr):
                _log.debug(_("moving attr {attr} to object ({val})").format(attr=attr,val=getattr(self,attr)))
                self.fndict[attr](getattr(self,attr))
                if attr not in ['glosslangs']: #obj and attr have same name...
                    delattr(self,attr)
                self.attrs_moved_to_object.add(attr)
            else:
                _log.debug(_("attr {attr} not found!").format(attr=attr))
        _log.debug(_("attrs_moved_to_object={val}").format(val=self.attrs_moved_to_object))
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
            fns['aztrepourls']=self.program.source_repo.remoteurls
            fns['glyphdict']=self.program.alphabet.glyphdict
            fns['glyph_members']=self.program.alphabet.glyph_members
            fns['glyphs_distinguished']=self.program.alphabet.distinguished
            fns['alphabet_order']=self.program.alphabet.order
            fns['alphabet_ncolumns']=self.alpha_ncolumns
            fns['alphabet_exids']=self.alpha_exids
            fns['alphabet_chart_title']=self.alpha_chart_title
            fns['alphabet_copyright']=self.alpha_copyright
            fns['alphabet_pagesize']=self.alpha_pagesize
            fns['contributors']=self.alphabet_contributors
            fns['ps']=self.program.slices.ps
            fns['profile']=self.program.slices.profile
            fns['profilecounts']=self.program.slices.slicepriority
            fns['giturls']=self.program.data_repo['git'].remoteurls
            fns['asr_repos']=self.program.soundsettings.asr_repo_tally
            fns['asr_kwargs']=self.program.soundsettings.asr_kwarg_dict
            fns['hgurls']=self.program.data_repo['hg'].remoteurls
        except Exception as e:
            # Expected during progressive startup (objects appear in stages);
            # ERROR here reads as a crash, so log at info.
            _log.info(_("Only finished settingsobjects up to {keys} ({error})").format(keys=fns.keys(),error=e))
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
            # fndict is created after objects, at end of settings init;
            # not used during legacy conversion, only in later saves.
            if hasattr(self,'fndict') and s in self.fndict:
                try:
                    d[s]=self.fndict[s]()
                except (AttributeError, KeyError):
                    _log.error(_("Value of {attr} not found in object").format(attr=s))
                    raise AttributeError(s)
            elif hasattr(o,s):
                val=getattr(o,s)
                # Persist Falses for BOOLEAN settings too (e.g. showdetails,
                # lowverticalspace) — the old truthy-only test silently dropped a
                # `False` display pref, so "hide details" never stuck. Non-bool
                # falsy (None / '' / []) is still skipped as "unset".
                if val or setting == 'soundsettings' or isinstance(val,bool):
                    d[s]=val
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
        if 'fs' in settingsdict:
            o=self.soundsettings
        else:
            o=self
        for s in settingsdict:
            v=settingsdict[s]
            if isinstance(v,_configparser.SectionProxy):
                continue #don't store expty section headers
            elif hasattr(self,'fndict') and s in self.fndict:
                self.fndict[s](v)
            elif s == 'status' and not hasattr(self.program,'status'): #Only load this once
                d={k:v[k] for k in v if k != 'DEFAULT'}
                # _log.info(_("makestatus from file: {status}").format(status=d))
                self.makestatus(d)
            elif s == 'toneframes':
                # program.toneframes IS the data object (like status above);
                # the generic setattr below would park the dict on settings
                # and the loaded frames would never be seen. (The legacy .ini
                # path had this case; the JSON path lost it in the migration.)
                d={k:v[k] for k in v if k != 'DEFAULT'}
                _log.info("Loaded tone frames: %s",
                          {ps:list(d[ps]) for ps in d})
                if hasattr(self.program,'toneframes'):
                    self.program.toneframes.source(d)
                else:
                    self.maketoneframes(d)
            elif s == 'secondformfield':
                # NOT the generic dict-update below: a stored `<unset>` is a
                # display placeholder that reads as a defined value to every
                # guard testing presence, and the setter's refusal cannot
                # reach a file written before it existed.
                self.load_second_form_fields(v)
            elif (isinstance(v,dict) and
                hasattr(o,s) and isinstance(getattr(o,s),dict)):
                getattr(o,s).update(v)
            else:
                setattr(o,s,v)
        return settingsdict
    def storesettingsfile(self,setting='defaults'):
        if setting in ['status', 'toneframes']:
            # program.status / program.toneframes ARE the data objects, keyed
            # by their own structure (e.g. cvt for status), NOT flat
            # attribute->value dicts. The domain block below filters keys
            # against the domain's attribute names, so wrap the object under
            # its attribute name; otherwise the filter matches nothing,
            # domain_data is empty, and the object is silently never written
            # (status — incl. presorted — was being lost on every reboot).
            d={setting: getattr(self.program, setting)}
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

        # Legacy .ini/.dat files are no longer written.
        # Migration to JSON domain files is complete.
    def loadsettingsfile(self,setting='defaults'):
        # Check domain-specific manager first
        json_had_data=False
        if setting in self.domain_mapping:
            for domain_name in self.domain_mapping[setting]:
                domain_mgr = getattr(self.mgr, domain_name)
                data = domain_mgr.load()
                if data:
                    self.readsettingsdict(data)
                    json_had_data=True #this domain's JSON has real content
                if setting == 'status' and not hasattr(self.program,'status'):
                    self.makestatus({}) #make status anyway, just once
        # The legacy .ini/.dat reader below is migration-ONLY. Once the JSON
        # domain has any content it is authoritative, so the legacy reader must
        # not run: it overwrites JSON-loaded data with the frozen pre-migration
        # file and wipes recent work on every boot. This previously only guarded
        # settings whose name is itself a JSON key (status/toneframes); domains
        # spread across attributes (alphabet's glyph_members/glyphdict/
        # glyphs_distinguished, defaults, profiledata, soundsettings) were left
        # exposed and kept getting clobbered — so we now skip whenever the JSON
        # domain supplied data at all.
        if json_had_data:
            return
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
            _log.info(_("makestatus legacy: {status}").format(status=self.program.status))
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
                            'profile'
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
                        'profile':[],
                        'cvt':[
                            'check',
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
        for default in fields:
            if default in ['lowverticalspace']:
                setattr(self, default, True)
            elif default in ['writeeverynwrites']:
                setattr(self, default, 1)
            else:
                setattr(self, default, None)
    def settingsinit(self):
        _log.info(_("Initializing settings."))
        self.initdefaults()

        self.cleardefaults() #this resets all to none (to be set below)
    def getdirectories(self):
        self.directory=file.getfilenamedir(self.liftfilename)
        if not file.exists(self.directory):
            _log.info(_("Looks like there’s a problem with your directory... "
                        "{file}\n{dir}")
                        .format(file=self.liftfilename,dir=self.directory))
            raise FileNotFoundError(self.directory)
        self.settingsfilecheck()
        self.imagesdir=file.getimagesdir(self.directory)
        self.audiodir=file.getaudiodir(self.directory)
        self.reportsdir=file.getreportdir(self.directory)
        self.exportsdir=file.getexportdir(self.directory)
        self.reportbasefilename=file.getdiredurl(self.reportsdir,
                                                    self.liftnamebase)
        self.reporttoaudiorelURL=file.getreldir(self.reportsdir, self.audiodir)
    def trackuntrackedfiles(self):
        """Pick up files that exist but aren't tracked in the git repo,
        either from constructing a repository or changes by other editors
        (e.g., WeSay). For new files only; changes to known files are
        handled on close."""
        _log.info(_("Looking for untracked files to add to repositories"))
        maindirfiles=[self.liftfilename,
                        self.toneframesfile,
                        self.statusfile,
                        self.profiledatafile,
                        self.adhocgroupsfile,
                        ]
        self.program.tk_root.update() #update GUI before threading
        r='git' #only look for this; don't duplicate repos unnecessarily
        if r in self.program.data_repo:
            present=set(self.program.data_repo[r].files)
            _log.info(_("{repo} currently has {count} files").format(repo=r,count=len(present)))
            for f in maindirfiles:
                _log.info(_("working on {file}").format(file=file.getfile(f)))
                if file.exists(f):
                    self.program.data_repo[r].add(file.getreldirposix(self.program.data_repo[r].url,f))
            audiohere=set([file.getreldirposix(self.program.data_repo[r].url,i)
                    for i in file.getfilesofdirectory(self.audiodir,
                                                        '*.wav')])
            audio=audiohere-present
            _log.info(_("{wav_count} wav files to check for the {repo} repo (of {total_count} files total "
                    "here)").format(wav_count=len(audio),repo=r,total_count=len(audiohere)))
            for f in audio:
                self.program.data_repo[r].add(f)
            for ext in ['png','jpg','gif']:
                i=set([file.getreldirposix(self.program.data_repo[r].url,i)
                        for i in file.getfilesofdirectory(self.imagesdir,
                                                '*.'+ext)]
                        )-present
                _log.info(_("{count} {extension} files to check for the {repo} repo")
                        .format(count=len(i),extension=ext,repo=r))
                for f in i:
                    self.program.data_repo[r].add(f)
        _log.info(_("trackuntrackedfiles finished."))
    def alpha_order(self,value=[]):
        return self.program.alphabet.order(value)
    def alpha_exids(self,value=dict()):
        if value: #don't allow integer keys; load them first, converting, then
            # overwrite if that string is elsewhere in the dict
            self._alphabet_exids={str(k):value[k] for k in value if type(k) is int}
            self._alphabet_exids.update({str(k):value[k] for k in value if type(k) is not int})
        if hasattr(self,'_alphabet_exids'):
            return self._alphabet_exids
        # Same store-before-default rule as _alpha: without it, a save made
        # before any pick had been loaded wrote {} over the user's examples.
        try:
            stored=self.mgr.get('alphabet_exids',None)
        except Exception:
            stored=None
        return stored if stored else value
    def _alpha(self,key,value,default):
        """One shape for every alphabet setting: set-if-given, else read.

        THE READ FALLS BACK TO alphabet.json BEFORE ANY HARDCODED DEFAULT
        (Kent 2026-07-31: "it IS reading from alphabet.json, and putting
        default values there which overwrite user preferences"). These
        accessors are what `makesettingsdict` serialises the file FROM, so an
        accessor that answered a placeholder — because its private attr hadn't
        been populated this session — wrote that placeholder straight over the
        user's stored value on the next save. Consulting the store first makes
        a save idempotent: with nothing new to set, it rewrites what is
        already there."""
        attr='_alphabet_'+key
        if value not in (None,'',[],{},0,False):
            setattr(self,attr,value)
        if hasattr(self,attr):
            return getattr(self,attr)
        try:
            stored=self.mgr.get('alphabet_'+key,None)
        except Exception as e:
            _log.info("alphabet_{} not readable from the domain store "
                      "({}); using the default".format(key,e))
            stored=None
        return default if stored in (None,'',[],{}) else stored
    def alpha_ncolumns(self,value=0):
        return self._alpha('ncolumns',value,5)
    def alpha_chart_title(self,value=''):
        return self._alpha('chart_title',value,'')
    def alpha_copyright(self,value=''):
        return self._alpha('copyright',value,_("Set Alphabet Copyright!"))
    def alphabet_contributors(self,value=None):
        if value is not None:
            self._contributors=value
        return getattr(self,'_contributors',[])
    def alpha_pagesize(self,value=''):
        return self._alpha('pagesize',value,'A4')
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
            _log.info(_("Using ‘{noun}’ for nouns, and ‘{verb}’ for verbs").format(
                noun=self.nominalps,
                verb=self.verbalps))
        except AttributeError:
            _log.info(_("Problem with finding a nominal and verbal lexical "
            "category (looked in first two of [{pss}])")
            .format(pss=self.program.db.pss))
    # `makesecondformfieldsOK` DELETED 2026-09-29 with the rest of the
    # second-form dialog cluster (plan 7 of
    # the second-form flags audit). It called
    # `mainwindow.getsecondformfieldN/V`, which are gone; its only remaining
    # mention was already commented out in `Parse.__init__`. What replaced it
    # is `StatusFrame.assure_second_forms`, which opens the field in place
    # instead of raising a chooser window.
    #: What the status line SHOWS when a second-form field has no value.
    #: It is a display string and must never be stored — but it was, and
    #: reached `project.json` (Kent, 2026-09-17: `"Verb": "<unset>"`, with
    #: "is that going to get us into trouble?"). It is defined HERE, in the
    #: layer that must refuse it, so the display and the guard cannot drift
    #: apart; `ui_shell.fieldsvalue` shows it and `setsecondformfield*`
    #: rejects it.
    UNSETFIELD='<unset>'

    def secondformfieldset(self,ps):
        """Has `ps` a real second-form field? Presence is not enough.

        The placeholder counts as UNSET wherever the question is asked.
        Three separate consumers were fooled by the stored placeholder —
        this predicate, `assure_second_forms`, and anything reading the
        value in order to find a LIFT field of that name (which would have
        gone looking for a field literally called `<unset>`)."""
        if not ps or ps not in self.secondformfield:
            return False
        return str(self.secondformfield[ps]).strip() not in (
                    '', self.UNSETFIELD)

    def load_second_form_fields(self,stored):
        """Apply the SETTERS' REFUSAL to what the settings file hands us.

        `_refuse_unset_field` stops `<unset>` being stored from now on, but a
        `project.json` written before it existed already holds
        `"Verb": "<unset>"` (Kent, 2026-09-17: "is that going to get us into
        trouble?"), and a refusal at the setter cannot reach a file. So the
        same predicate runs on the way IN, and the entry never becomes a
        live setting.

        DROPPED, NOT BLANKED. The dict's KEYS are load-bearing —
        `parser.pscheck` treats them as the set of legal parts of speech —
        so a key whose value is the placeholder tells one consumer "this ps
        is configured" while telling `secondformfieldset` "unset". That
        split is exactly how the placeholder fooled three consumers at once.
        Without the key, `secondformfields` falls through to
        `guess_*_secondformfield`, which is what an unanswered field has
        always done.

        Nothing is lost by dropping it: the second-form gate
        (`Segments.second_forms_ready`) already reads the placeholder as
        unset, so a project carrying one was being asked for the field
        anyway. What this stops is the placeholder reaching LIFT as a field
        NAME — Parse indexes the dict directly, so it would have asked "what
        is the `<unset>` of x?" and written the answer into a field called
        `<unset>`.

        The file keeps its copy until something next writes settings; the
        live dict is what every reader uses, and `makesettingsdict` builds
        the next write from that."""
        if not isinstance(stored,dict):
            return
        clean={ps:v for ps,v in stored.items()
               if not self._refuse_unset_field(ps,v)}
        if not hasattr(self,'secondformfield') or not isinstance(
                                    self.secondformfield,dict):
            self.secondformfield={}
        self.secondformfield.update(clean)

    def missing_second_form_pss(self):
        """Which parts of speech still have no second-form field, in order.

        ONE PREDICATE, THREE CALLERS. `assure_second_forms` opens the first of
        these, and the Parse page gate names them in the notice it shows while
        it waits — both were about to build this list themselves, and a second
        copy of "what counts as set" is exactly how the stored `<unset>`
        fooled three consumers at once (see `secondformfieldset`)."""
        return [ps for ps in (self.nominalps, self.verbalps)
                if ps and not self.secondformfieldset(ps)]

    # `secondformfieldsOK` DELETED 2026-09-29 with `_WordCollectionSecondForm`,
    # its last caller (plan 2). It asked "are BOTH fields set?", which was the
    # right question only for a task that refused to start without them —
    # and that refusal was a dead end, since the window that refused offered
    # no way to set one. `missing_second_form_pss` above answers the same
    # question usefully (WHICH are missing, so the page can open that one),
    # and `secondformfieldset` answers it per ps.
    def fields(self):
        try:
            self.fieldnames=self.program.db.fieldnames[self.analang]
        except KeyError:
            self.fieldnames=[]
        _log.info(_("Fields found in lexicon: {fields}").format(fields=self.fieldnames))
    def guess_nominal_secondformfield(self):
        for opt in self.plopts: #class attribute; always present
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
        for opt in self.impopts: #class attribute; always present
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
    def register_second_forms(self):
        """Point every sense's `pl`/`imp` at the fields the user named.

        THE LAYER THAT KNOWS DOES THE TELLING. `lift.py` builds `lx` and
        `lc` itself because they are LIFT's own tags; `pl` and `imp` mean
        "whichever field this project keeps plurals in", which is a setting
        and none of lift's business (Kent, 2026-09-29, on the alternative:
        if lift knows nothing about why, "then there is no ftype population
        on load"). So there is none — this runs once the names are settled
        and lift is simply told.

        ONE PASS FOR STORED AND GUESSED ALIKE. A pre-load read of the
        project settings was considered and rejected: it is possible
        (`secondformfield` is in the same domain as `analang`, which
        `file_parser` already reads before loading), but it answers nothing
        in the three cases that matter — a project with no stored name,
        where `guess_*_secondformfield` can only run AFTER the database is
        loaded because it walks the entries; a rename mid-session; and a
        stored `<unset>`, which a raw domain read has no predicate to
        refuse. Since this pass must exist for those, a second path
        covering only the easy case would be duplication.

        UNSET MEANS UNSET: gated on `secondformfieldset`, so the
        `<unset>` placeholder never becomes a key, and re-pointing a
        renamed field drops the old one (`Sense.set_ftype`).

        Never raises: a settings change must not fail because a mapping
        could not be refreshed."""
        db=getattr(self.program,'db',None)
        senses=getattr(db,'senses',None)
        if not senses:
            _log.info("no senses to register second forms on yet")
            return
        pairs=[(code, self.secondformfield.get(ps)
                        if self.secondformfieldset(ps) else None)
               for code, ps in (('pl',self.nominalps),('imp',self.verbalps))]
        found={code:0 for code, name in pairs}
        for sense in senses:
            for code, name in pairs:
                try:
                    if sense.set_ftype(code,name):
                        found[code]+=1
                except Exception as e:
                    _log.info("could not register %s on a sense (%r)",code,e)
        _log.info("second forms registered: %s of %d senses (%s)",
                  found, len(senses),
                  {code:name for code, name in pairs})

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
        # OCCASION 1: the names are settled now, whether they came from the
        # settings file or from a guess over the database. Both routes end
        # here, which is why this is one call and not two.
        self.register_second_forms()
        # AND THE CHECK NAMES, for the same reason and at the same moment.
        # `build_checknames` runs in `CheckParameters.__init__`, BEFORE any
        # of this is known, so `second_form_checks` found no field and the
        # `pl`/`imp` entries were never built — and `_cvchecknames` had no
        # name to give them. The syllable sort's chooser then fell back to
        # the bare code and offered "pl" as an option (Kent, 2026-09-30:
        # "working on {ftype} should list label, not 'pl'").
        #   Plan 5 made RENAMING rebuild these (`_checknames_follow_the_
        # field`); discovering the name at boot never did, which is the
        # same gap `register_second_forms` above exists to close.
        try:
            self.program.params.rebuild_checknames()
        except Exception as e:
            _log.info("could not rebuild check names after the second form "
                      "fields settled (%r)", e)
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
            self.program.status.build(**kwargs)
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
            if set(y)-set(x):
                text=(f"{set(y)-set(x)} keys not in {key if key else 'dict'}!")
                ErrorNotice(text,wait=True)
                sysshutdown()
            for k in y:
                if isinstance(x[k],dict) and isinstance(y[k],dict):
                    report(x[k],y[k],k)
        report(x,y)
    def scrub_foreign_status(self):
        """Remove check nodes that were never checks from program.status.

        NEEDED because the status cycle cannot self-heal: StatusDict.__init__
        copies the stored dict in verbatim, dictcheck/build only ADD branches,
        and storesettingsfile dumps the whole object back over the JSON — so a
        bad node loaded at boot is written straight back out, every run, for
        ever. It also survived the LIFT data that produced it, the status file
        being independent of the lexicon.

        DELIBERATELY NARROWER THAN THE WRITE GATE. The gate in
        generate_status_by_annotations refuses anything cvt_of_check can't
        place (fail closed — right for what we ADD). Deleting on that test
        would be wrong: a check code from an older build, or an older '-slice'
        spelling, also fails it, and those may hold real verification work the
        user did. So removal is limited to names we affirmatively know are not
        ours (is_foreign_annotation — the collab daemon's merge markers), and
        every removal is named in the log. Fail closed on writes, conservative
        on deletes."""
        status=getattr(self.program,'status',None)
        if not status:
            return
        foreign=self.program.params.is_foreign_annotation
        gone=[]
        for cvt in list(status):
            for ps in list(status.get(cvt) or {}):
                for profile in list(status[cvt].get(ps) or {}):
                    node=status[cvt][ps].get(profile) or {}
                    if not hasattr(node,'items'):
                        continue
                    for check in [c for c in list(node) if foreign(c)]:
                        del node[check]
                        gone.append((cvt,ps,profile,check))
        if gone:
            _log.warning("Removed %s status node(s) for names that are not "
                    "checks: %s. These were written into the status file "
                    "before the write gate existed, under whichever cvt was "
                    "selected at the time, and could not clear on their own.",
                    len(gone),gone[:20])
            self.storesettingsfile(setting='status')
    def generate_status_by_annotations(self,**kwargs):
        _log.info(_("Refreshing annotations from LIFT"))
        # Clear anything an earlier build let in, before adding to it.
        self.scrub_foreign_status()
        start_at=kwargs.get('startat',0)
        end_at=kwargs.get('endat',100)
        # Both of these read annotations off ONE word form's node, so they have
        # to be asked for the form the session is actually working on — the
        # default 'lc' silently reported citation data under any other form.
        ftype=self.program.params.ftype()
        d=self.program.db.annotation_values_by_ps_profile(ftype)
        # LIFT-derived 'done' (group verified as a whole = every member carries
        # its <check>=<group> code). Recomputed here so verified state can't go
        # stale in the status file — a join no longer drops sibling groups.
        verified=self.program.db.verified_groups_by_ps_profile(ftype)
        k={}
        for k['ps'],profile_dict in d.items():
            for k['profile'],check_dict in profile_dict.items():
                for k['check'],groups in check_dict.items():
                    if k['check'].isdigit():
                        continue
                    k['cvt']=self.program.params.cvt_of_check(k['check'])
                    if k['cvt'] is None:
                        # NOT ONE OF OUR CHECKS — don't put it in the status
                        # tree. azt's checks are internally defined
                        # (Analysis.renewchecks), and _checkcodes_by_cvt is that
                        # registry, so cvt_of_check returning None IS the
                        # allow-list test; it needs no separate list, and it
                        # fails CLOSED. Tone is unaffected: frame names aren't
                        # check codes, which is why generate_status_by_tone_groups
                        # is a separate generator that hardcodes cvt='T'.
                        #   Without this, a name that isn't a check did NOT get
                        # parked harmlessly under a None key: node() →
                        # checkslicetypecurrent (analysis.py:2062-2065) DELETES
                        # None kwargs and substitutes the CURRENT value, so the
                        # foreign name was filed under whichever cvt happened to
                        # be selected when the refresh ran — a real branch, and a
                        # different one from run to run. That is why it shows up
                        # in the status field's check list. It was then PERSISTED
                        # to the data domain and reloaded at every boot
                        # (loadsettingsfile loads status once, from JSON), so it
                        # outlived the LIFT data that produced it. The live case
                        # is the collab daemon's
                        # <annotation name="azt-lift-conflict" value="ours|theirs"/>
                        # merge marker (azt_collabd/lift_merge.py:45), which shares
                        # this name space and reached the status field as a check
                        # with groups 'ours'/'theirs' that can never verify
                        # (Kent 2026-09-02).
                        # Say only what is established. The first version of
                        # this line explained every rejected name as a collab
                        # merge marker, and the first one it actually reported
                        # was '#C-slice' — azt's OWN bookkeeping annotation,
                        # nothing to do with the daemon (Kent saw it,
                        # 2026-09-02). Naming a cause the code has not
                        # established is the same fault as announcing an action
                        # before its gate: it sends the reader in the wrong
                        # direction, and costs a round trip. So report the fact,
                        # and add the daemon note ONLY for a name that really is
                        # one of theirs.
                        if not getattr(self,'_said_notacheck',set()):
                            self._said_notacheck=set()
                        if k['check'] not in self._said_notacheck:
                            self._said_notacheck.add(k['check'])
                            extra=''
                            if self.program.params.is_foreign_annotation(
                                                            k['check']):
                                extra=(" This one is written by the collab "
                                    "daemon, not by a sort: a conflict marker "
                                    "means the merge kept BOTH sides of an "
                                    "entry, and the DATA wants a look.")
                            _log.warning("Not a check, so not going into the "
                                    "status: %r.%s", k['check'], extra)
                        continue
                    groups=[i for i in groups if i]
                    self.program.status.groups(groups, wsorted=True, **k)
                    # Segmental only: 'S' (syllable-prep) done is per-slice, not
                    # group-coded, so leave it to the prep driver.
                    if k['cvt'] in ('V','C'):
                        _verif=verified.get(k['ps'],{}).get(k['profile'],{}
                                    ).get(k['check'],set())
                        done=sorted(_verif & set(groups))
                        self.program.status.node(**k)['done']=done
                    yield start_at + (end_at-start_at) * len(k)/len(d) #maybe more detail later
    def generate_status_by_tone_groups(self,**kwargs):
        _log.info(_("Refreshing tone data from LIFT"))
        start_at=kwargs.get('startat',0)
        end_at=kwargs.get('endat',100)
        t=self.program.db.tone_values_by_ps_profile()
        k={}
        k['cvt']='T'
        for k['ps'],profile_dict in t.items():
            for k['profile'],check_dict in profile_dict.items():
                for k['check'],groups in check_dict.items():
                    self.program.status.groups(groups, wsorted=True, **k)
                    yield start_at + (end_at-start_at) * len(k)/len(t) #maybe more detail later
    def reloadstatusdata(self):
        _log.info(_("Refreshing all status settings from LIFT"))
        self.storesettingsfile() #default, not status
        ftype=self.program.params.ftype()
        self.program.db.load_ps_profiles(ftype)
        # CLEAR-THEN-REBUILD IS ONLY SAFE IF THERE IS SOMETHING TO REBUILD
        # FROM. This became form-dependent on 2026-09-30, when the profile
        # readers learnt to follow the chosen word form: run on a form nobody
        # has profiled yet and the rebuild sources nothing, so the clear
        # stands alone and the status file loses every group — for a form
        # that was never the one the groups describe. Segmental status nodes
        # carry no form in their key, so there is nothing here to tell them
        # apart afterwards.
        #   An empty picture on a form with no data is CORRECT (Kent,
        # 2026-09-30: "near-emtpy: yes, that's what I expecte") — it is
        # destroying the other form's record on the way past that is not. A
        # genuinely empty project hits this too and loses nothing, since
        # there was nothing to clear.
        if not any(self.program.db.ps_profiles.values()):
            _log.warning("Not refreshing status from LIFT: no word carries a "
                    "CV profile for the %r form, so there is nothing to "
                    "rebuild from and clearing would discard the status built "
                    "under another form. Switch the form back first.",ftype)
            return
        self.program.status.clear_all_groups()
        for i in itertools.chain(self.generate_status_by_annotations(end_at=50),
                                self.generate_status_by_tone_groups(start_at=50)):
            yield i
    def reloadstatusdata_cleanup(self):
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
            if not kwargs.get('cvt'): #default, not on iteration
                self.program.status.marksensetosort(sense)
            tosort=True
        else:
            if not kwargs.get('cvt'): #default, not on iteration
                self.program.status.marksensesorted(sense.id)
            # NA IS TRACKED, ALWAYS (Kent 2026-07-30: "it has to be in groups on
            # disk, but excluded from MOST uses"). It used to be dropped here for
            # any check without '=', which made group membership disagree with the
            # full status remake (generate_status_by_annotations takes groups
            # straight from the annotations, where NA is just another value). Since
            # `cull` reduces done to done∩groups, NA's stored verification was
            # culled away on the next per-slice rebuild — so users re-verified NA
            # with no word added, which is the one case where re-verifying is
            # wrong.
            #
            # Whether NA is OFFERED for verification is a different question, and
            # now lives where to-verify is computed (StatusDict.groups); whether it
            # is SHOWN is each use site's business (sort() filters it from the
            # button list, group_pairs_to_distinguish and pending_distinctions drop
            # it, glyphstoverify and senses_for_glyph skip it).
            # ALLOK (fully verified) is never a sort group.
            if v not in ['ALLOK']:
                self._groups.append(v)
    def updatesortingstatus(self, store=True, **kwargs):
        """This reads LIFT to create lists for sorting, populating lists of
        sorted and unsorted senses, as well as sorted (but not verified) groups.
        So don't iterate over it. Instead, use checkforsensestosort to just
        confirm tosort status"""
        cvt=kwargs.get('cvt',self.program.params.cvt())
        ps=kwargs.get('ps',self.program.slices.ps())
        profile=kwargs.get('profile',self.program.slices.profile())
        check=kwargs.get('check',self.program.params.check())
        kwargs['wsorted']=True #ever not?
        senses=self.program.slices.senses(ps=ps,profile=profile)
        _log.debug(_("Working on {count} sense.ids (first 5): {ids}").format(count=len(senses),
                                                    ids=[i.id for i in senses[:5]]))
        self.program.status.renewsensestosort([],[]) #will repopulate
        self._groups=[]
        if cvt == 'T': #we need to be able to iterate over cvt, to rebuild
            fn=Tone.getitemgroup
        elif cvt == 'S': #whole-word syllable profile, read from cvprofile field
            fn=Syllables.getitemgroup
        else:
            fn=Segments.getitemgroup #This pulls from annotation, not form
        for sense in senses:
            self.categorizebygrouping(fn,sense,**kwargs)
        sorted=set(self._groups)
        log.debug(f"sorted (check={check}, NA_in_groups={self._groups.count('NA')}): {sorted}")
        self.program.status.groups(list(sorted),**kwargs)
        log.debug(f"status.groups: {self.program.status.groups(**kwargs)}")
        if store:
            self.storesettingsfile(setting='status')
    def dont_guessanalang(self):
        """Analang should be easily deduceable from the lift file, and/or
        explicit in the settings."""
        self.analang=self.program.db.analang
        _log.info(_("analang in use: {analang} (If you don’t like this, change it in the menus)").format(analang=self.analang))
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
            # NAMING THE FIELD CHANGES WHICH CHECKS EXIST. `pl` exists only
            # once the nominal field is named and `imp` only once the verbal
            # one is (see `CheckParameters.second_form_checks`), so this
            # branch used to drop the flag and refresh NOTHING — the new
            # check was built but never offered, and a renamed field left
            # the old name on screen. Plan 5 of
            # the second-form flags audit.
            #   Only for cvt 'S': the second-form checks are whole-word
            #   syllable-profile checks and appear nowhere else.
            if t == 'S':
                try:
                    self.program.status.updatechecksbycvt()
                    self.program.status.makecheckok()
                except Exception as e:
                    _log.info(_("Could not refresh checks after the second "
                                "form field changed: {error}").format(error=e))
            self.attrschanged.remove('secondformfield')
        if 'ftype' in self.attrschanged:
            # THE WORD CHECK CHANGED, so the page is looking at a different
            # set of words. The collection page's todo list is built from
            # the word form (`getlisttodo`, lexicon.py), so it reloads — the
            # gloss-language precedent two branches up, data refreshed into
            # the same widgets rather than a rebuilt page. Kent, 2026-09-17,
            # on switching to plurals mid-page: "this workflow shouldn't
            # break us."
            #   `reload_for_word_check`, not `loadwords`: two page types
            # answer to a form change and they do different things. A
            # collection page reloads its word list (and must use
            # `loadwords`, since `getwords` would grid a SECOND
            # `wordsframe`); `SortSyllables` rebuilds its `(ps, ftype)`
            # slices and its board, because everything it shows is keyed on
            # the form. Plan 2 and plan 6 of the second-form flags audit.
            # THE CHECK FOLLOWS THE FORM, and must be settled BEFORE the
            # page reloads or the page rebuilds against the old one. For
            # cvt 'S' the check list is `[ftype()]`, so a changed form makes
            # the standing check invalid and `makecheckok` picks the only
            # valid one — no new mechanism, just the call that was missing
            # (Kent, 2026-09-30: "this means we'll need a makecheckOK, since
            # the check will need to align with the ftype, should it ever
            # change").
            #   And it chains: `makecheckok` settles the group in turn, so
            # one call takes ftype → check → group.
            try:
                self.program.status.makecheckok()
            except Exception as e:
                _log.info("could not realign the check with the form (%r)",e)
            task=getattr(self.program,'task',None)
            if hasattr(task,'reload_for_word_check'):
                try:
                    task.reload_for_word_check()
                except Exception as e:
                    _log.info(_("Could not reload after the word check "
                                "changed: {error}").format(error=e))
            self.attrschanged.remove('ftype')
        if 'showdetails' in self.attrschanged:
            # Display-only pref: persist it now (defaults→ui domain) so the choice
            # survives a restart, and clear it from attrschanged so it doesn't fall
            # through to the "Remaining changed attribute!" error / accumulate.
            self.storesettingsfile()
            self.attrschanged.remove('showdetails')
        # THE GROUP MUST BELONG TO THE CHECK, and until 2026-09-30 nothing
        # ever said so: `StatusDict.makegroupok` was written for exactly this
        # and had NO CALLERS anywhere in the app. A group belongs to a
        # (cvt, ps, profile, check) slice, so any of the branches above can
        # invalidate it — which is why this is one call at the end rather
        # than a line in each.
        #   The symptom Kent brought: the syllable sort's line read
        # "Checking Syllable Profiles, working on Whole Citation Word
        # Syllable Profile = C". `C` is a stage-1 answer to `#C`/`C#`; the
        # check was stage 2, whose groups are cvprofiles. The display was
        # honest and the STATE was mixed across the two stages.
        #   An older patch treated the same class at the label:
        # `cvgrouplabel` still carries a comment about the frame showing
        # "working on First Vowel None" after an x-check phase.
        #   Never raises: a settings refresh must not fail over this.
        try:
            self.program.status.makegroupok()
        except Exception as e:
            _log.info("could not settle the group against the current "
                      "check (%r)", e)
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
        ToneFrames(self.program,dict) #signature is (program, dict)
    def makestatus(self,dict={}):
        StatusDict(self.settingsfile('status'), dict, self.program)
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
                                'ln-CD':"Lingala (DRC)",
                                'wes':"Kamtok (Cameroon)",
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
        self.ui_vars = {}
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
    def post_lift_init(self):
        """These settings require the LIFt db be up and parsed already"""
        self.dont_guessanalang() #needed for regexs
        if not self.analang:
            _log.error(_("No analysis language; exiting."))
            return
        #set the field names used in this db:
        log.debug(f"{self.secondformfield=}")
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
        self.attrschanged=[]
        _log.info(_("Settings (Post lift) initialized"))
    def post_params_init(self):
        self.program.profiles.run()
    def get_ui_var(self, attr, value=None):
        """Get or create a StringVar for the given attribute.

        A SUPPLIED VALUE IS APPLIED, NOT DISCARDED — which is the fix, not
        the design (2026-09-29). These vars are cached for the SESSION, and
        every status label asks for one with the text it has just computed:

            get_ui_var('cvt_label', self.cvtvalue())

        On the second task of a session that computed text was thrown away
        and the caller got the previous task's label back, so the settings
        line froze at whatever wrote it first. Nothing repainted it on a
        plain task open either, because `update_all_labels` runs on settings
        CHANGES. Kent, 2026-09-29, having opened Sort Consonants and come
        back: "just went to SortC and back, and it still said vowels" — on a
        page whose cvt is unambiguously 'C'. The VALUE was right on every
        page; the label was one task behind, session-wide, for
        `cvt_label`, `cvcheck_label`, `ps_label`, `fields<ps>_label` and the
        rest of the family.

        Callers that pass nothing (the `trace_add` registrations) are
        unaffected: they want the var, not a value."""
        if attr not in self.ui_vars:
            # Lazy import to avoid circular dependency and only use if UI is present
            from frontend import ui
            var = ui.StringVar(value=str(value) if value is not None else str(getattr(self, attr, "")))
            self.ui_vars[attr] = var
        elif value is not None:
            self.ui_vars[attr].set(str(value))
        return self.ui_vars[attr]
