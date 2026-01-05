# coding=UTF-8
import logsetup
log=logsetup.getlog(__name__)
# logsetup.setlevel('INFO',log) #for this file
logsetup.setlevel('DEBUG',log) #for this file
try: #translation
    _
except NameError:
    def _(x):
        return x
"""This module is for setting defaults automatically (for either "
"a check or database?)."""
"""It may also be where list choice options are prioritized
for automatic running."""
"""I need to think about databases with only one of gloss/definition,
and lexeme/citation. And for those that have a mix, presumably going from one
to another. I think I want to be sensitive to the presence/absence of the
preferred field on the entry level. So I probably just need a third field
for each gloss/glossonly/defn, and citation/citationonly/lexeme. """
def getaudiolangs(self):
    """if there's only one gloss language, use it."""
    if not hasattr(self,'audiolangs'):
        self.audiolangs=self.db.audiolangs
    if len(self.audiolangs) == 1:
        log.debug('Only one audiolang!')
        self.audiolang=self.audiolangs[0]
    else:
        log.error(_("More than one audiolang! Set this up! (exiting)"))
        exit()

def langs(self):
    """This should be able to run on a check or lift class."""
    getanalangs(self) #self.guessanalang()
    getglosslangs(self) #self.guessglosslangs()
    getaudiolangs(self)
    log.info('Analysis Language: '+self.analang)
    log.info('Audio Recording Language: '+self.audiolang)
    log.info('Gloss Language: '+self.glosslang)
    log.info('Second Gloss Language: '+self.glosslang2)
    log.info(_("If you don't like these selections, they can be changed later."))
    log.info(_("If you're working on a multilingual dictionary, we need to "
            "figure out how to deal with that, later.  :-)"))
    self.languagecodes=[self.analangs]+[self.glosslangs]
def count(self):
    """Return the number of occurrances of subcategories, for a given category.
    or perhaps just return the largest (unverified?) category....
    probably wrap this into multiple scrips:
    all categories
    all subcategories
    all unverified categories
    return number or category (both useful...)
    """
def ps(self):
    """Pick the ps with the greatest number, or greatest profile number
    inside it..."""
def profile(self):
    """Pick the prifile with the greatest number..."""
def subcheck(self):
    """If there's only one subcheck, pick it."""
def checkname(self):
    """If there's only one check available (for the ps/profile combo),
    pick it."""
