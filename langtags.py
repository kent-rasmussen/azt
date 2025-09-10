#!/usr/bin/env python3
# coding=UTF-8
import langcodes
import ethnologue_language_relationships as iso
import ethnologue_macrolanguages_members
import rx,os
import json
import urllib.request #as request
import file
import copy
from file import localfile
import logsetup
log=logsetup.getlog(__name__)
logsetup.setlevel('DEBUG',log) #for this file
log.info(f"Importing {__name__}")
# import language_data #optional, for stats and names
"""Users should be able to type in the name of their language as they
know/understand it, without knowing the iso or other codes. Based on what they
type, we want to give a (short) selection of possible language options for them
to pick from: including official name, other names, iso and other codes,
region/country, and linguistic parent (and maybe siblings?)
"""
"""Methods/functions here should be able to return iso or other codes from
whatever input is provided, as some lists have one, and some the other."""

"""This package defines one class, named Language, which contains the results of parsing a language tag. Language objects have the following fields, any of which may be unspecified:
language: the code for the language itself.
script: the 4-letter code for the writing system being used.
territory: the 2-letter or 3-digit code for the country or similar region whose usage of the language appears in this text.
extlangs: a list of more specific language codes that follow the language code. (This is allowed by the language code syntax, but deprecated.)
variants: codes for specific variations of language usage that aren't covered by the script or territory codes. (Optional variant subtags, separated by hyphens, each composed of five to eight letters, or of four characters starting with a digit; Variant subtags are registered with IANA and not associated with any external standard.)
extensions: information that's attached to the language code for use in some specific system, such as Unicode collation orders.
private: a code starting with x- that has no defined meaning.

maybe pull ldml from https://ldml.api.sil.org/langtags.json, then add PUA
"""
tag_is_valid=langcodes.tag_is_valid
tone_code='-x-tone'
phonetic_code='-x-ipa'
audio_code='-Zxxx-x-audio'
machine_transcription_code='_MT'
try:
    import whisper_codes_names
except (ModuleNotFoundError,NameError):
    """dict of lowercase language name keys valued to a language code"""
    from transformers.models.whisper.tokenization_whisper import TO_LANGUAGE_CODE
    by_iso={langcodes.Language.get(code).to_alpha3(variant=variant):(code,name)
                                    for name,code in TO_LANGUAGE_CODE.items()
                                for variant in ['B','T']}
    by_whisper_code={code:(langcodes.Language.get(code).to_alpha3(),name)
                                    for name,code in TO_LANGUAGE_CODE.items()}
    by_name={name:(langcodes.Language.get(code).to_alpha3(),code)
                                    for name,code in TO_LANGUAGE_CODE.items()}
    with open(localfile('whisper_codes_names.py'),'w') as f:
        f.write(f'by_name={str(by_name)}\n')
        f.write(f'by_iso={str(by_iso)}\n')
        f.write(f'by_whisper_code={str(by_whisper_code)}')
    import whisper_codes_names
macrolanguage_members=ethnologue_macrolanguages_members.dict
def dict_by(key):
    return {p:[j for j in iso.list if key in j if p == j[key]]
                for p in set([i[key] for i in iso.list if key in i])}
def whisper_codes_alpha3():
    return [langcodes.Language.get(i).to_alpha3() for i in whisper_languages().values()]

def validate_private(x, delim='-', prefix='x'):
    """validate 'An optional private-use subtag, composed of the letter x
    and a hyphen followed by subtags of one to eight characters each,
    separated by hyphens.'
    Add 'x' prefix if not present
    split any subtags of more than eight characters every eight characters
    """
    if type(x) is str:
        x=rx.split(f'[;,\\s_{delim}]+', x)
        for ni,i in enumerate(x):
            if len(i) > 8:
                new_i=''
                for nj,j in enumerate(i):
                    if (nj+1)%8:
                        new_i+=j
                    else:
                        new_i+=j+'-'
                x[ni]=new_i
        if x[0] != prefix:
            x.insert(0,prefix)
        x=delim.join(x)
        print(f'{x} is final string!')
        return x
    print(f'{x} is not a string!')
def langcode(x,glosslang=None): #This must return str!
    # print("working on",x,type(x))
    if langcodes.tag_is_valid(x):
        return x
    else: #redundant, but allows subclassing langcodes.Language
        try: #find gives exception on not found
            lang_obj=langcodes.Language.find(x,language=glosslang)
            return str(lang_obj)
        except LookupError as e:
            lang_obj=langcodes.Language.find(x)
            return str(lang_obj)
            print(f"language {x} not found ({e})")
    """return code from language name"""
def code_to_iso(x):
    return langcodes.Language.get(x).to_alpha3()
def territorycode(name):
    """return code from territory"""
def whisper_languages(lang=None):
    """This returns a dict of lowercase keys valued to a language code"""
    from transformers.models.whisper.tokenization_whisper import TO_LANGUAGE_CODE
    if lang:
        print(f"Found {len(TO_LANGUAGE_CODE)} languages supported by whisper. ({lang}={lang.lower() in TO_LANGUAGE_CODE})")
    return TO_LANGUAGE_CODE
def whisper_language_names():
    return sorted(whisper_languages().keys())
def whisper_language_codes():
    return sorted(whisper_languages().values())

class SisterLanguages(object):
    """docstring for SisterLanguages."""
    def load_fleurs():
        """Make this load from https://huggingface.co/datasets/google/fleurs"""
    def load_mms_data(self):
        from mms_language_support import data
        self.mms_data=data
    def mms_support(self,type):
        if type not in self.mms_types:
            log.error(f"MMS supports the following types: {self.mms_types}")
        return {k for k in self.mms_data if self.mms_data[k][type]}
    def lookup_name_mms(self,name): #could be multiple
        return [k for k in self.mms_data if name.lower() in
                                            self.mms_data[k]['name'].lower()]
    def load_whisper_dict(self):
        self.whisper_dict=whisper_languages()
    def whisper_codes_alpha3(self):
        return {langcodes.Language.get(i).to_alpha3()
                    for i in self.whisper_dict.values()}
    def lookup_name_whisper(self,name):
        return [whisper_codes_names.by_name[i][0]
                    for i in whisper_codes_names.by_name
                    if name.lower() in i]
    def lookup_name(self,name):
        code=self.lookup_name_whisper(name) # returns a list
        code.extend(self.lookup_name_mms(name)) # returns a list
        return [i for i in code if i]
    def __init__(self):
        super(SisterLanguages, self).__init__()
        self.mms_types=['asr', 'tts', 'lid']
        self.load_mms_data()
        self.mms_asr_support=self.mms_support('asr')
        self.mms_lid_support=self.mms_support('lid')
        self.mms_tts_support=self.mms_support('tts')
        self.load_whisper_dict()
        self.whisper_support=self.whisper_codes_alpha3()
        log.info(f"Whisper language support for {len(self.whisper_dict)} "
                "languages")
        log.info(f"Facebook MMS language support for {len(self.mms_data)} "
                f"languages ({len(self.mms_support('asr'))} for ASR)")
class Languages(dict):
    def fix_data(self):
        qafar_names={'localname': 'Qafar', 'localnames': ['Qafar af']}
        self.full_codes['aa-Arab-ET'].update(qafar_names)
    def reload_json(self):
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; '
                        'x64; rv:77.0) Gecko/20100101 Firefox/77.0'}
        request = urllib.request.Request(self.url, headers=headers)
        r = urllib.request.urlopen(request)
        content=r.read().decode('utf-8')
        with open(localfile(self.url.split('/')[-1]),'w') as f:
            f.write(content)
        self.load_json()
    def load_json(self):
        try:
            with open(localfile(self.url.split('/')[-1]),'r') as f:
                data = json.load(f)
        except FileNotFoundError:
            self.reload_json()
            return
        self.full_codes={i['full']:i for i in data if 'full' in i}
        self.fix_data()
        self.all_tags={k:i for i in data if 'tags' in i for k in i['tags'] }
        self.all_tags.update({k:i for i in data if 'tag' in i
                                for k in [i['tag']]})
        region_dict_list=[i for i in data if 'full' not in i
                                            if 'regions' in i]
        if len(region_dict_list) != 1:
            log.error("Problem with region list (not exactly one list dict): "
                        f"\n{region_dict_list}")
        self.region_codes=region_dict_list[0]['regions']
        self.region_codes_names={i['region']:i['regionname'] for i in data
                                            if 'full' in i and 'regionname' in i
                                }
        api_dict_list=[i for i in data if 'api' in i]
        if len(api_dict_list) != 1:
            log.error("Problem with api list (not exactly one list dict)")
        self.data_version=api_dict_list[0]['api']
        self.data_date=api_dict_list[0]['date']
        phonetic_labels_dict_list=[i for i in data if i['tag'] == '_phonvar']
        if len(phonetic_labels_dict_list) != 1:
            log.error("Problem with phonetic variable list "
                        "(not exactly one list dict)")
        self.phonetic_labels=phonetic_labels_dict_list[0]['variants']
        metadata=[i for i in data if 'full' not in i
                                    if 'regions' not in i
                                    if 'api' not in i
                                    if i['tag'] != '_phonvar'
                                ]
        log.info(f"Loaded JSON language data with {len(self.full_codes)} "
            "full language codes "
            f"and {len(self.region_codes)} regions ("
            f"v{self.data_version}; {self.data_date})")
        log.info(f"found phonetic labels {self.phonetic_labels}")
        log.info(f"Remaining metadata: {metadata}")
    def load_by_iso(self):
        self.by_iso=dict_by('language code')
        for i in self.by_iso:
            if len(self.by_iso[i])-1:
                print(f"More than one ({len(self.by_iso[i])}) {i} entry found ! "
                    f" ({self.by_iso[i]})")
                exit()
        self.by_iso={k:v[0] for k,v in self.by_iso.items()}
    def lookup_name(self,name):
        return [k for k in self.by_iso
                            if name.lower() in (
                                [self.by_iso[k].get('localname','').lower(),
                                    self.by_iso[k].get('name','').lower()] or
                        [i.lower() for i in self.by_iso[k].get('names',[])] or
                        [i.lower() for i in self.by_iso[k].get('localnames',[])]
                                        )
                ]
    def get_codes(self,input,first_wins=False):
        codes=[]
        try:
            # log.info(f"code {input} is iso: {input in self.all_iso_codes}")
            code=langcodes.standardize_tag(input)
            # log.info(f"standardized {input} code: {code}")
            obj=Language(code,self)
            if obj.is_valid():
                if first_wins:
                    return [code]
                codes.append(code)
        except (langcodes.tag_parser.LanguageTagError,
                AssertionError,
                LookupError) as e:
            # log.info(f"Language tag parsing error: {e}")
            pass
        from language_data.names import name_to_code,code_to_names
        """name_to_code can also have a "language" kwarg to look up a
        language name in a given language. Without this, it looks up a
        language name in *ANY* language."""
        code=name_to_code('language',input)
        if code:
            if first_wins:
                # log.info(f"found {input} in language_data list "
                #     f"with code(s) {code}")
                return [code]
            codes.append(code)
            # log.info(f"Names: {code_to_names(code)}")
        code=self.lookup_name(input) #this outputs a list of possibles
        if code:
            if first_wins:
                # log.info(f"found {input} in Ethnologue list with "
                #     f"code(s) {code}")
                return [code]
            codes.extend(code)
        code=self.sisters.lookup_name(input) #this outputs a list of possibles
        if code:
            if first_wins:
                # log.info(f"found {code} code(s) for {input} in Sisters list")
                return [code]
            codes.extend(code)
        # log.info(f"Finishing with codes {codes}")
        codes=set([langcodes.standardize_tag(i) for i in codes])
        # log.info(f"Finished with codes {codes}")
        return codes
    def get_code(self,lang):
        codes=self.get_codes(lang,first_wins=True)
        # log.info("Finished getting codes")
        if len(codes)>1:
            log.info("Please select one of the following: \n"
                f"{'\n'.join([f'{l}: {langcodes.Language(l).display_name()}' for l in codes])}")
            exit()
        elif codes:
            return codes.pop() #just one
    def get_obj(self,input): #input can be code or name
        try:
            return Language(input,self) #if this works, we're done
        except:
            code=self.get_code(input)
            if code:
                # log.info("Trying to make language element now")
                return Language(code,self)
            else:
                log.error(f"Input {input} didn't result in a code!")
    def get_objs(self,input): #input can be code or name
        codes=self.get_codes(input)
        return [Language(code,self) for code in codes]
    def descendants_of(self,group_list):
        group_set=set(group_list)
        d={k for k in self.by_iso
            if group_set & set(self.by_iso[k]['lineage']) == group_set}
        # include macrolanguages of these langs, too:
        d|={k for k,v in macrolanguage_members.items() if v&d}
        print(f"Found {len(d)} descendants of {group_list}")
        return d
    def __init__(self,**kwargs):
        self.url="https://ldml.api.sil.org/langtags.json"
        super(Languages, self).__init__(**kwargs)
        self.sisters=SisterLanguages()
        # self.reload_json() #Forces online usage
        self.load_json()
        self.load_by_iso()
        self.all_iso_codes=set(self.by_iso) | set(macrolanguage_members)
        self.all_valid_codes=self.all_iso_codes|set(whisper_language_codes())
class Language(langcodes.Language):
    """maybe pull ldml from https://ldml.api.sil.org/langtags.json
    probably store in my repo (if permitted)
    update from time to time"""
    def reset_tag(self):
        self._str_tag=None
    def addprivate(self,tag):
        """If not reset, cached value will continue to be used"""
        # self.update_dict({'private':validate_private(tag)})
        self.private=validate_private(tag)
        self.reset_tag()
    def alpha23(self):
        iso=self.to_alpha3()
        if iso > self.tag_raw(): #if expanded, give both
            return f"{self.tag_raw()}/{iso}"
        else:
            return iso
    def unprivate(self):
        broader=self.broader_tags().remove['und']
        check in self.languages.by_iso
        self.privatex=self.private
        self.private=None
        self.reset_tag()
    def iso(self):
        r=self.to_alpha3()
        if r in macrolanguage_members:
            log.info(f"Language code {str(self)} is for a macrolanguage {r} "
                f"with members {macrolanguage_members[r]}")
            self.isos=macrolanguage_members[r]
        elif r not in self.languages.by_iso:
            log.error(f"Language with code {str(self)} > {r} "
                            "not in Ethnologue data!")
            return
        # log.info(f"returning {r} for iso of {self.tag_raw()}")
        return r
    def tag_raw(self):
        """Maybe put out non-standard tags"""
        return str(self)
    def tag(self):
        """Never put out non-standard tags"""
        return langcodes.standardize_tag(self)
    def is_valid(self):
        return langcodes.Language.is_valid(langcodes.Language.get(self.tag()))
    def fill_tag(self):
        self.maximize()
    def get_lineage(self):
        """This returns a single ordered list, of ancestors of a single
        language, or shared ancestors for a macrolanguage"""
        iso=self.iso()
        # log.info(f"{iso in self.languages.by_iso=}")
        # log.info(f"{iso in macrolanguage_members=}")
        if iso in self.languages.by_iso:
            self.lineage = self.languages.by_iso[iso]['lineage']
        elif iso in macrolanguage_members:
            self.lineages={iso:self.languages.by_iso[iso]['lineage']
                            for iso in self.isos
                            if iso in self.languages.by_iso
                        }
            # log.info(f"{self.lineages=}")
            self.lineage = self.shared_lineage()
        else:
            log.error(f"code ‘{iso}’ is not in self.languages.by_iso "
                        "or macrolanguage_members!?")
    def shared_lineage(self):
        result=[]
        lists=copy.deepcopy(list(self.lineages.values()))
        for i in range(min([len(v) for v in lists])):
            this_result=set([v.pop(0) for v in lists])
            if len(this_result) == 1:
                result.append(this_result.pop())
            else:
                # print(f"Ancestors differ at: {this_result}")
                return result
    def family(self):
        try:
            return self.lineage[0]
        except:
            log.error(f"code ‘{self.iso()}’ came back with no family!? "
                f"({self.lineages})")
    def get_regionname(self):
        tag=self.language
        if (tag in self.languages.all_tags and
            'region' in self.languages.all_tags[tag] and
            self.languages.all_tags[tag]['region'] in
            self.languages.region_codes_names):
            self.regions={self.languages.region_codes_names[
                        self.languages.all_tags[tag]['region']]}
        else:
            self.regions=set()
            # log.info(f"Found regions {self.regions}")
        if (tag in self.languages.all_tags and
                    'regions' in self.languages.all_tags[tag]):
            self.regions|={self.languages.region_codes_names[i]
                    if i in self.languages.region_codes_names else i
                    for i in self.languages.all_tags[tag]['regions']}
            # log.info(f"Found regions {self.regions}")
        if tag in macrolanguage_members:
            macro_regions={self.languages.region_codes_names[
                                    self.languages.all_tags[t]['region']]
                            for t in macrolanguage_members[tag]
                            if t in self.languages.all_tags and
                            'region' in self.languages.all_tags[t]
                        }
            self.regions|=macro_regions
            self.regions|={self.languages.region_codes_names[i]
                        for t in macrolanguage_members[tag]
                        if t in self.languages.all_tags and
                        'regions' in self.languages.all_tags[t]
                        for i in self.languages.all_tags[t]['regions']
            }
            # print(f"Found macrolanguage spoken in {', '.join(self.regions)}")
        if self.regions:
            if len(self.regions)>3:
                if tag in macrolanguage_members:
                    if len(macro_regions)<=3:
                        self.regionname=', '.join(macro_regions)
                        return
                    region=macro_regions[0]
                try:
                    region=self.languages.region_codes_names[
                                self.languages.all_tags[tag]['region']]
                except:
                    try:
                        region=self.languages.by_iso[tag]['country name']
                    except:
                        region=self.regions[0]
                self.regionname=f'{region}, etc'
            else:
                self.regionname=', '.join(self.regions)
        # else:
        #     print(f"No regionname! ({self.languages.by_iso[tag]})")
    def full_display(self):
        n=min(len(self.lineage),3)
        meta='/'.join(self.lineage[-n:])
        if hasattr(self,'regionname') and self.regionname:
            meta=f"{self.regionname}; {meta}"
        if self.private:
            meta=f"{self.private.removeprefix('x-')} dialect; {meta}"
        return (f"{self.display_name()} [{self.alpha23()}] ({meta})")
    def supported_ancestor_objs_prioritized(self):
        return [self.languages.get_obj(i)
                    for i in self.supported_ancestor_codes_prioritized()
                    if i]
    def supported_ancestor_codes_prioritized(self):
        d=self.supported_ancestors()
        sisters=[]
        if d:
            for o in ['both','whisper','mms_asr']: #in this order
                # log.info(f"self.sister_options[{o}]: {self.sister_options}")
                sisters.extend([
                        i for i in d[o]
                        if i not in sisters] #no repeats
                    )
        return sisters
    def supported_ancestors(self):
        # lineage=self.lineage() #for macrolanguages, just the shared bit
        for i in range(len(self.lineage),0,-1):
            all=self.languages.descendants_of(self.lineage[:i])
            ancestors={'whisper':all&self.languages.sisters.whisper_support,
                        'mms_asr':all&self.languages.sisters.mms_asr_support,
                        'mms_lid':all&self.languages.sisters.mms_lid_support,
                        'mms_tts':all&self.languages.sisters.mms_tts_support,
                        }
            total=[len(v) for k,v in ancestors.items()
                                if k in ['whisper','mms_asr']]
            if sum(total):
                ancestors['both']=ancestors['whisper']&ancestors['mms_asr']
                log.info(f"Support found for "
                    f"{'/'.join(self.lineage[:i])} languages: {ancestors}")
                return ancestors
    def report(self):
        log.info(f"{self.display_name()} ({self.display_name('fr')}; "
            f"tag ‘{self.tag()}’ "
            f"{'Valid' if self.is_valid() else 'Not valid'}, "
            f"from {self.tag_raw()} > {self.maximize()})")
        log.info(f"Family: {self.family()}")
        self.supported_ancestors()
        # print("Maximal Tag:",self.maximize(),
        #     f"({'Valid' if self.maximize().is_valid() else 'Not valid'})")
        # print("Unstandardized Tag:",self.tag_raw())
    def __init__(self,language,languages,**kwargs): #languages just for lookup?
        # print(language,languages)
        kwargs['language']=language
        if '-' in kwargs['language']:
            kwargs.update({t[0]:t[1] for t in langcodes.parse_tag(language)})
            # log.info(f"Updated {language=} to {kwargs=}")
        try:
            super(Language, self).__init__(**kwargs)
        except Exception as e:
            log.info(f"Language didn't init ({kwargs})")
            kwargs['language']=languages.get_code(language)
            log.info(f"Trying init again with {kwargs}")
            super(Language, self).__init__(**kwargs)
        self.languages=languages
        self.get_lineage() #I think the kproblem is here?
        self.fill_tag()
        self.get_regionname()
if __name__ == '__main__':
    print(f"{tag_is_valid('sw-x-ipa_MT')=}")
    ldict=Languages()
    for code in ['sw-x-ipa_MT','sw-TZ']:
        o=Language(code,ldict)
        print(o.full_display())
    for s in [
        # 'tem','temb','tembo','Tembo',
        #     'lug','lg',
        'swh','swc','zmb','english','Swahili',
            'tbt-x-xkivu','tbt-x-kivu-x','tbt-x-i','en'
            # 'en','eng'
            ]:
        if s in ldict.by_iso:
            print('country name:',ldict.by_iso[s]['country name'])
        else:
            o=ldict.get_obj(s)
            print(o.full_display())
