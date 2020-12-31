## coding=UTF-8
import re
"""This is called from a number of places"""
def s(self,stype,lang=None): #join a list into regex format
    if hasattr(self,stype): #should be one of c,v,g,n
        if lang is None: #This causes an error, as lift.analang doesn't exist
            lang=self.analang #This should be generalized for all analangs
        return '|'.join(getattr(self,stype)[lang])
def make(regex, word=False, compile=False):
    if word == True:
        regex='^'+regex+'$'
    if compile == True:
        try:
            regex=re.compile(regex, re.UNICODE)
        except:
            print('Regex problem!')
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
    if type(CVs) is str:
        CVs=tuple((CVs,))
    regex=list()
    references=('\1','\2','\3','\4')
    references=range(1,5)
    variables=('v','c')
    def CVproblem():
        print("Error! check your CV template; it should only have 'C' "
                "and 'V' in it, or 'x' references ("+x+')')
        exit()
    for x in CVs[0]:
        if x in ["V","C","N","G"]:
            rnext="("+s(db,x.lower())+")"
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
    return make(regexjoined,word=word, compile=compile)
