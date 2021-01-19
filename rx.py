## coding=UTF-8
import re
import logging
log = logging.getLogger(__name__)
"""This is called from a number of places"""
def s(self,stype,lang=None):
    """join a list into regex format, sort for longer first, to capture
    the largest units possible."""
    if (lang == None) and (hasattr(self,'analang')):
        log.debug(_('telling rx.s which lang to use'))
        lang=self.analang
        log.debug(_("Using analang: {}".format(self.analang)))
    log.debug(_("Looking in self.s[{}]: {}".format(lang,self.s)))
    if stype in self.s[lang]:
        return "("+'|'.join(sorted(self.s[lang][stype],key=len,reverse=True))+")"
    # if hasattr(self,stype): #should be one of c,v,g,n
    #     return "("+'|'.join(sorted(getattr(self,stype)[lang]))+")"
def make(regex, word=False, compile=False):
    if (re.match('^[^(]*\|',regex)) or (re.search('\|[^)]*$',regex)):
        log.error('Regex problem! (need parentheses around segments!):',regex)
        exit()
    if word == True:
        """To make alternations and references work correctly, this should
        already have parentheses () around each S."""
        regex='^'+regex+'$'
    if compile == True:
        try:
            regex=re.compile(regex, re.UNICODE)
        except:
            log.error('Regex problem!')
    return regex
def fromCV(db, CVs, lang, word=False, compile=False):
    """ this inputs regex variable (regexCV), a tuple of two parts:
    1. abbreviations with 'C' and 'V' in it, and/or variables for actual
    segments or back reference, e.g., 1 for \1 or 2 for \2, and 'c' or 'v'.
    2. dictionary of variable meanings (e.g., {'v':'e'}).
    e.g., for total variable: CVs=("CvC2",{'v':'e'})
    CAUTION: if you don't have this dictionary, CVs[0] is just one letter...
    It outputs language specific regex (compiled if compile=True,
    whole word word=True)."""
    """lang should be check.analang"""
    if type(CVs) is str:
        CVs=tuple((CVs,))
    regex=list()
    references=('\1','\2','\3','\4')
    references=range(1,5)
    variables=('v','c')
    def CVproblem():
        log.error("Error! check your CV template; it should only have 'C' "
                "and 'V' in it, or 'x' references ("+x+')')
        exit()
    for x in CVs[0]:
        if x in ["V","C","N","G","S"]:
            rnext=s(db,x,lang) #this should have parens for each S
        elif x in sum(db.s[lang].values(),[]):
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
