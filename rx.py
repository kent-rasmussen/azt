## coding=UTF-8
import re
import time
import logging
log = logging.getLogger(__name__)
"""This is called from a number of places"""
framerx=re.compile('__') #replace this w/data in frames.
def urlok(x):
    #These should each be tuple of
    # 1. a simple list of characters to strip,
    # 2. replacement
    d=("̀́̂̌̄̃᷉̋̄̏̌̂᷄᷅̌᷆᷇᷉̈","")
    p=("][\. /?",'_')
    l=("əéèê",'e')
    for i in [d,p,l]:
        x=re.sub('['+i[0]+']',i[1],x)
    return x
def id(x):
    x=x.replace('˥','4').replace('˦','3').replace('˧','2'
        ).replace('˨','1').replace('˩','0')
    return re.sub('[][  .!=\(\),\'/?ꞌ\n:;+]','_',x) #remove charcters that are invalid for ids
def tonerxs():
    return (re.compile('[˥˦˧˨˩]+', re.UNICODE),
            re.compile(' ', re.UNICODE),
            re.compile(' ', re.UNICODE))
def texmllike(x):
    repls={
        '\\': "\\textbackslash{}",
        '{': "\\{",
        '}': "\\}",
        '$': "\\textdollar{}",
        '[': "{[}", #"\\textsquarebracketleft{}",
        ']': "{]}", #"\\textsquarebracketright{}",
        '&lt;': "\\textless{}",
        '&le;': "\\textless{}=",
        '&gt;': "\\textgreater{}",
        '&ge;': "\\textgreater{}=",
        '&amp;': "\\&amp;",
        '#': "\\#",
        '^': "\\^{}",
        '_': "\\_",
        '~': "\\textasciitilde{}",
        '%': "\\%",
        '|': "\\textbar{}",
        '<': "\\textless{}",
        '>': "\\textgreater{}"
    }
    for y in repls:
        print("Replacing",y,"with",repls[y])
        x=x.replace(y,repls[y])
    x=re.sub('\\\\textless{}(([\?!/]|tex:)[^\\\\]*)\\\\textgreater{}',"<\\1>",x)
    return x
def glossifydefn(x):
    x=re.sub('^(([^() ]+)( [^() ]+){,2})(.*)*$','\\1',x) #up to three words, no parens
    x=re.sub(',$','',x)
    x=re.sub(', ',',',x)
    x=re.sub(' ','.',x)
    return x
def makeprecomposed(x):
    if x is None:
        return
    subs={'á':'á',
    'à':'à',
    'é':'é',
    'è':'è',
    'ê':'ê',
    'í':'í',
    'ì':'ì',
    'ó':'ó',
    'ò':'ò',
    'ú':'ú',
    'ù':'ù',
    }
    for s in subs:
        x=re.sub(s,subs[s],x)
    return x
def stripdiacritics(check,x):
    if 'd' in check.rx:
        return check.rx['d'].sub('',x)
    return x
def segmentin(forms, glyph):
    # """This actually allows for dygraphs, etc., so I'm keeping it."""
    # for form in forms: # as: self.citationforms[lang] + self.lexemes[lang]
        if re.search(glyph,' '.join([x for x in forms if x != None])): #see if the glyph is there
            return glyph #find it and stop looking, or return nothing
def inxyz(db, lang, segmentlist): #This calls the above script for each character.
    start_time=time.time() #this enables boot time evaluation
    actuals=list()
    forms=db.lcs[lang] + db.lxs[lang]
    for i in segmentlist:
        s=segmentin(forms,i)
        #log.info(s) #to see the following run per segment
        if s is not None:
            actuals.append(s)
    log.log(2,'{} {}'.format(time.time()-start_time, segmentlist)) # with this
    return list(dict.fromkeys(actuals))
def s(check,stype,lang=None):
    """join a list into regex format, sort for longer first, to capture
    the largest units possible."""
    if (lang == None) and (hasattr(check,'analang')):
        log.log(2,_('telling rx.s which lang to use'))
        lang=check.analang
        log.log(2,_("Using analang: {}".format(check.analang)))
    if stype == "C-ʔ":
        if 'ʔ' in check.s[lang]:
            list=set(check.s[lang]['C'])-set(check.s[lang]['ʔ'])
        else:
            list=set(check.s[lang]['C'])
    elif stype == "C-N":
        if 'N' in check.s[lang]:
            list=set(check.s[lang]['C'])-set(check.s[lang]['N'])
        else:
            list=set(check.s[lang]['C'])
    elif stype in check.s[lang]:
        list=check.s[lang][stype]
    else:
        log.error("Dunno why, but this isn't in lists: {}".format(stype))
        return
    return "("+'|'.join(sorted(list,key=len,reverse=True))+")"
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
def fromCV(check, lang, word=False, compile=False):
    """ this inputs regex variable (regexCV), a tuple of two parts:
    1. abbreviations with 'C' and 'V' in it, and/or variables for actual
    segments or back reference, e.g., 1 for \1 or 2 for \2, and 'c' or 'v'.
    2. dictionary of variable meanings (e.g., {'v':'e'}).
    e.g., for total variable: CVs=("CvC2",{'v':'e'})
    CAUTION: if you don't have this dictionary, CVs[0] is just one letter...
    It outputs language specific regex (compiled if compile=True,
    whole word word=True)."""
    """lang should be check.analang"""
    CVs=check.regexCV
    log.log(5,'CVs: {}'.format(CVs))
    if type(CVs) is not str:
        log.error("regexCV is not string! ({})".format(check.regexCV))
    regex=list()
    references=('\1','\2','\3','\4')
    references=range(1,5)
    # Replace word final C first, to get it out of the way:
    if check.distinguish['ʔwd'] and not check.distinguish['ʔ']:
        rxthis=s(check,'C-ʔ',lang) #Pull out C# first;exclude N# if appropriate.
        CVs=re.sub('C$',rxthis,CVs)
    if check.distinguish['Nwd'] and not check.distinguish['N']:
        rxthis=s(check,'C-N',lang) #Pull out C# first;exclude N# if appropriate.
        CVs=re.sub('C$',rxthis,CVs)
        log.log(2,'CVs: {}'.format(CVs))
    # if C includes [N,?], find C first; if it doesn't, move on to [N,?].
    # if we distinguish [N,?]# (only), C# is already gone, so other C's here.
    for x in ["V","C","N","ʔ","G","S"]:
        if x in check.s[lang]: #just pull out big ones first
            rxthis=s(check,x,lang) #this should have parens for each S
            CVs=re.sub(x,rxthis,CVs)
            log.log(2,'CVs: {}'.format(CVs))
    for x in references: #get capture group expressions
        CVrepl='\\\\{}'.format(str(x)) #this needs to be escaped to survive...
        log.log(3,'x: {}; repl: {}'.format(x,CVrepl))
        log.log(3,'CVs: {}'.format(CVs))
    CVs=re.sub('\)([^(]+)\(',')(\\1)(',CVs)
    log.log(5,'CVs: {}'.format(CVs))
    return make(CVs,word=word, compile=compile)
if __name__ == '__main__':
    x='ne [pas] plaire, ne pas agréer, ne pas'
    print(id(x))
    # s='ááààééèèííììóóòòúúùù'
    # s2=makeprecomposed(s)
    # print(s,s2)
