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
    def tag(self):
        """Never put out non-standard tags"""
        return langcodes.standardize_tag(self)
    def is_valid(self):
        return langcodes.Language.is_valid(langcodes.Language.get(self.tag()))
    def maximize(self):
        return langcodes.Language.maximize(langcodes.Language.get(self.tag()))
    def __init__(self,**kwargs):
        super(Language, self).__init__(**kwargs)
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
