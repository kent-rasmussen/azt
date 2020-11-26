## coding=UTF-8
import re
"""This is called from a number of places"""
def c(self,lang=None): #join a list into regex format
    if lang is None:
        lang=self.analang
    return '|'.join(self.c[lang]) #include all possible glyphs from consonants()
def v(self,lang=None): #Why does this give me nothing for gnd?!?!?
    if lang is None:
        lang=self.analang
    if len(self.diacritics()[lang]) >0:
        return '['+str().join(self.v[lang])+']['+str().join(self.diacritics()[lang])+']*' #If we end up using glyphs for vowels with diacritics, we'll want |.join() here, without the '[]'.
    else: #i.e., if there are no diacritics, don't include them (so things don't break)
        return '['+str().join(self.v[lang])+']' #If we end up using glyphs for vowels with diacritics, we'll want |.join() here, without the '[]'.
def make(regex, word=False, compile=False):
    #print(regex)
    if word == True:
        regex='^'+regex+'$'
    if compile == True:
        try:
            regex=re.compile(regex, re.UNICODE)
        except:
            print('Regex problem!')
    #print(regex) #Don't worry, this truncates, but works.
    #if regex.match('pasw'):
    #    print('Matched! Exiting.')
    #    exit()
    return regex
def fromCV(db, CVs, word=False, compile=False):
    """ this inputs regex variable (regexCV), a tuple of two parts:
    1. abbreviations with 'C' and 'V' in it, and/or variables for actual
    segments or back reference, e.g., 1 for \1 or 2 for \2, and 'c' or 'v'.
    2. dictionary of variable meanings (e.g., {'v':'e'}).
    e.g., for total variable: CVs=("CvC2",{'v':'e'})
    CAUTION: if you don't have this dictionary, CVs[0] is just one letter...
    It outputs language specific regex (compiled if compile=True,
    whole word word=True)."""
    #print('Running cvregex')
    #print(CVs)
    #print(type(CVs))
    #if CVs == "Invalid": #This only seems to work for one character...
    #    regex=list(char+'+' for char in self.invalidchars)
    #    #print(regex, type(regex))
    #    #regex=[' +']
    #    rjoined='|'.join(regex)
    #    regex='('+rjoined+')' #
    #    #regex="('"+rjoined+"')" #
    #    #print(regex, type(regex))
    #    #exit()
    #else:
    if type(CVs) is str:
        CVs=tuple((CVs,))
    regex=list()
    references=('\1','\2','\3','\4')
    references=range(1,5) #(1,2,3,4)
    variables=('v','c')
    def CVproblem():
        print("Error! check your CV template; it should only have 'C' "
                "and 'V' in it, or 'x' references ("+x+')')
        exit()
    #print(v(lift),lift.analang)
    for x in CVs[0]:
        if x == "V":
            rnext="("+v(db)+")" #[lift.analang]
        elif x == "C":
            rnext="("+c(db)+")"
        elif x in db.c[db.analang]+db.v[db.analang]:
            rnext="("+x+")"
        else:
            try:
                if int(x) in references:
                    rnext="(\\"+x+")"
                else:
                    CVproblem()
            except:
                CVproblem()
        regex.append(rnext)
    regexjoined=str().join(regex)
    #print(regex)
    #print(regexjoined)
    #if len(CVs)>3:
    #    exit()
    return make(regexjoined,word=word, compile=compile)
