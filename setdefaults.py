# coding=UTF-8
"""This module is for setting defaults automatically (for either "
"a check or database?)."""
"""It may also be where list choice options are prioritized
for automatic running."""
"""I need to think about databases with only one of gloss/definition,
and lexeme/citation. And for those that have a mix, presumably going from one
to another. I think I want to be sensitive to the presence/absence of the
preferred field on the entry level. So I probably just need a third field
for each gloss/glossonly/defn, and citation/citationonly/lexeme. """
def getanalangs(self):
    # self.analang='gnd'
    # return
    """if there's only one analysis language, use it."""
    # print(self.db.analangs,type(self.db.analangs))
    if not hasattr(self,'analangs'):
        self.analangs=self.db.analangs
    # print(self.analangs,type(self.analangs))
    if len(self.analangs) == 1:
        # print('Only one analang!')
        self.analang=self.analangs[0] #was globalvariables.xyz
        self.analangdefault=self.analangs[0] #In case the above gets changed.
    elif (len(self.analangs[0]) == 3) and (len(self.analangs[1]) != 3):
        print('Looks like I found an iso code for analang!')
        self.analang=self.analangs[0] #assume this is the iso code
    elif (len(self.analangs[1]) == 3) and (len(self.analangs[0]) != 3):
        print('Looks like I found an iso code for analang!')
        self.analang=self.analangs[1] #assume this is the iso code
def getaudiolangs(self):
    """if there's only one gloss language, use it."""
    # print(self.audiolang)
    # print(self.audiolangs)
    if not hasattr(self,'audiolangs'):
        self.audiolangs=self.db.audiolangs
    if len(self.audiolangs) == 1:
        # print('Only one audiolang!')
        self.audiolang=self.audiolangs[0]
    else:
        print("More than one audiolang! Set this up! (exiting)")
        exit()

def getglosslangs(self):
    """if there's only one gloss language, use it."""
    if not hasattr(self,'glosslangs'):
        self.glosslangs=self.db.glosslangs
    if len(self.glosslangs) == 1:
        print('Only one glosslang!')
        self.glosslang=self.glosslangs[0] #was self.glosslang=globalvariables.glosslang
        self.glosslang2=None #was globalvariables.glosslang2 #do we want this here, or in lift_do?
        """if there are two or more gloss languages, just pick the first two,
        and the user can select something else later (the gloss languages are not for
        CV profile analaysis, but for info after checking, when this can be reset."""
    elif len(self.glosslangs) > 1:
        # print('More than one glosslang!')
        self.glosslang=self.glosslangs[0] #was self.glosslang=globalvariables.glosslang
        self.glosslang2=self.glosslangs[1] #was globalvariables.glosslang2 #do we want this here, or in lift_do?
    else:
        print("Can't tell how many glosslangs!",len(self.glosslangs))
def getinterfacelang(self):
    """Normally run on check class"""
    if hasattr(self.parent,'interfacelang') and self.parent.interfacelang == None:
        self.parent.interfacelang=self.glosslang
    self.parent.setinterfacelang()
def langs(self):
    """This should be able to run on a check or lift class."""
    getanalangs(self)
    getglosslangs(self)
    getaudiolangs(self)
    print('Analysis Language: '+self.analang)
    print('Audio Recording Language: '+self.audiolang)
    print('Gloss Language: '+self.glosslang)
    print('Second Gloss Language: '+self.glosslang2)
    print("If you don't like these selections, they can be changed later.")
    print("If you're working on a multilingual dictionary, we need to "
            "figure out how to deal with that, later.  :-)")
    self.languagecodes=[self.analangs]+[self.glosslangs]
def fields(self):
    """I think this is lift specific; may move it to defaults, if not."""
    fields=self.fields()
    print("Fields found in lexicon: "+str(fields))
    plopts=('Plural', 'plural','pl','Pluriel','pluriel')
    impopts=('Imperative','imperative','imp','Imp')
    for opt in plopts:
        if opt in fields:
            self.pluralname=opt
    try:
        print('Plural field: '+self.pluralname)
    except:
        print('Looks like there is no Plural field in the database')
        self.pluralname=None
    for opt in impopts:
        if opt in fields:
            self.imperativename=opt
    try:
        print('Imperative field: '+self.imperativename)
    except:
        print('Looks like there is no Imperative field in the database')
        self.imperativename=None
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
