#!/usr/bin/env python3
# coding=UTF-8
import langcodes
import rx
# import language_data #optional, for stats and names

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
def validate_private(x, delim='-', prefix='x'):
    """validate 'An optional private-use subtag, composed of the letter x
    and a hyphen followed by subtags of one to eight characters each,
    separated by hyphens.'
    Add 'x' prefix if not present
    split any subtags of more than eight characters every eight characters
    """
    if type(x) is str:#and delim in x:
        x=rx.split(f'[;,\\s_{delim}]+', x)
        # x=x.split(delim+' _')
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
def langcode(name):
    """return code from language name"""
def territorycode(name):
    """return code from territory"""
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
