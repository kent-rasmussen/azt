#!/usr/bin/env python3
## coding=UTF-8
import re
import time
import logsetup
log=logsetup.getlog(__name__)
# logsetup.setlevel('INFO',log) #for this file
logsetup.setlevel('DEBUG',log) #for this file
"""This is called from a number of places"""
framerx=re.compile('__') #replace this w/data in frames.
def slashdash(x):
    return sub(r'/',r'-',x)
def urlok(x):
    x=str(x) # just in case we pass a path object
    #These should each be tuple of
    # 1. a simple list of characters to strip,
    # 2. replacement
    d=("̀́̂̌̄̃᷉̋̄̏̌̂᷄᷅̌᷆᷇᷉̈","")
    # * . " / \ [ ] : ; | , # illegal in MS Windows
    p=(r"][\. /?*\\:;\|,\"><'",'_')
    l=("əéèêɛ",'e')
    o=("ô",'o')
    for i in [d,p,l]:
        x=re.sub('['+i[0]+']',i[1],x)
    return x
def splitxpath(x):
    """Confirm that r is correct here"""
    tag,*features=split(r'[\]\[]',x)
    attrib={}
    for f in [i for i in features if i]:
        # print('-'+f)
        key,val=split('=',f)
        key=split('^@',key)
        val=val.strip('"\'')
        # print(key,val)
        attrib[key[1]]=val
    return tag,attrib
def escapeattr(x):
    x=str(x)
    if "'" in x:
        return '\"'+x+'\"'
    else:
        return "'"+x+"'"    #b+="[@{}=\"{}\"]".format(attr,self.kwargs[attrs[attr]])
# This doesn't seem to be able to work:
# def removepicreldir(x):
#     dirs=[
#             r'pictures/',
#             r'pictures\\'
#             ]
#     for d in dirs:
#         if x.startswith(d):
#             x=x.split(d)[-1]
#     return x
def split(delre,str):
    return re.split(delre,str)
def countxiny(x,y):
    return re.subn(x, x, y)[1]
def linebreakwords(x):
    return re.sub(' ','\n',x)
def pymoduleable(x):
    """Confirm that r is correct here"""
    return re.sub(r'\.','_', str(x))
def delinebreak(x):
    return re.sub('\n','',x)
def stripquotes(x):
    try:
        return x.strip('‘’')
    except:
        return x
"""passthrough fns"""
IGNORECASE=re.IGNORECASE
def sub(*args,**kwargs):
    # pattern, repl, string, count=0, flags=0
    # log.info("Running re.sub with args: {} and kwargs: {}".format(args,kwargs))
    return re.sub(*args,**kwargs)
def compile(x):
    return re.compile(x, re.UNICODE)
def id(x):
    x=x.replace('˥','4').replace('˦','3').replace('˧','2'
        ).replace('˨','1').replace('˩','0')
    """Confirm that r is correct here"""
    return re.sub(r'[][  .!=\(\),\'/?ꞌ\n:;+*]','_',x) #remove charcters that are invalid for ids
def tonerxs():
    return (re.compile('[˥˦˧˨˩]+', re.UNICODE),
            re.compile(' ', re.UNICODE),
            re.compile(' ', re.UNICODE))
def update(t,regexdict,check,value,matches=[]):
    tori=t
    for c in reversed(check.split('=')):
        log.info("subbing {} for {} in {}, using {}".format(value,c,t,
                                                    regexdict[c]))
        # log.info("found {}".format(regexdict[c].search(t)))
        match=regexdict[c].search(t)
        if match:
            matches.append(match.groups()[-1])
            t=match.expand('\\g<1>'+value)+t[match.end():]
    log.info("updated {} > {}".format(tori,t))
    for match in matches:
        if len(match)>1:
            log.info(_("NOTICE: we just matched (to remove) a set of "
            "symbols representing one sound ({}). Until you are done "
            "with it, we will leave it there, so both forms will be "
            "found. Once you are done with it, remove it from the "
            "polygraph settings.").format(match))
    return t
def texmllike(x):
    """This attempts to implement TeXMLLikeCharacterConversion.java from
    XLingPaper"""
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
        '>': "\\textgreater{}",
        '.\u200b ': ".\\  ",
        '\u200c ': ".\\ \\ ",
        '\u200d ': ".~"
    }
    for y in repls:
        print("Replacing",y,"with",repls[y])
        x=x.replace(y,repls[y])
    """Confirm that r is correct here"""
    x=re.sub(r'\\\\textless{}(([\?!/]|tex:)[^\\\\]*)\\\\textgreater{}',"<\\1>",x)
    return x
def noparenscontent(x): #pull all content in parentheses
    if isinstance(x,str):
        """Confirm that r is correct here"""
        return re.sub(r'\(.*\)','',x)
def noparens(x): #pull just the parens
    if isinstance(x,str):
        """Confirm that r is correct here"""
        return re.sub(r'\(|\)','',x)
def glossdeftoform(x):
    # i=x
    x=noparenscontent(x)
    if isinstance(x,str):
        # x=re.sub('\(.*\)','',x)
        x=re.sub(',.*','',x) #stop at any comma
        x=re.sub('^ *','',x) #no leading spaces
        x=re.sub(' .*','',x) #just use the first word
        # x=re.sub('^(([^() ]+)( [^() ]+){,2})(.*)*$','\\1',x) #up to three words, no parens
        # x=re.sub(',$','',x)
        # x=re.sub(', ',',',x)
        # x=re.sub(' ','.',x)
        # log.info("glossdeftoform: {} > {}".format(i,x))
        return x
def glossifydefn(x):
    if isinstance(x,str):
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
def fixunicodeerrorsWindows(x):
    errordict={
                'É”': 'ɔ',
                'É›': 'ɛ',
                'É²': 'ɲ',
                'Å‹': 'ŋ',
                'Ã®': 'î',
                'Ã´': 'ô',
                'Ã¯': 'ï',
                'Ã»': 'û',
                'Ã ': 'à',
                'â€˜': '',
                'â€™': '',
                'Å“': 'œ',
                'Ã¢': 'â'
                }
    for e in errordict:
        if e in x:
            x=re.sub(e,errordict[e],x)
    return x
    # ls |grep 'É”\|É›\|É²\|Å‹\|Ã®\|Ã´\|Ã¯\|Ã»\|Ã \|â€˜\|â€™\|Å“\|Ã¢'
    # mv `ls |grep 'É”\|É›\|É²\|Å‹\|Ã®\|Ã´\|Ã¯\|Ã»\|Ã \|â€˜\|â€™\|Å“\|Ã¢'` messedup/
    # rename -n 's/É”/ɔ/g;s/É›/ɛ/g;s/É²/ɲ/g;s/Å‹/ŋ/g;s/Ã®/î/g;s/Ã´/ô/g;s/Ã¯/ï/g;s/Ã»/û/g;s/Ã /à/g;s/â€˜//g;s/â€™//g;s/Å“/œ/g;s/Ã¢/â/g' *
def stripdiacritics(check,x):
    if 'd' in check.rx:
        return check.rx['d'].sub('',x)
    return x
def segmentin(forms, glyph):
    # """This actually allows for dygraphs, etc., so I'm keeping it."""
    # for form in forms: # as: self.citationforms[lang] + self.lexemes[lang]
        if re.search(glyph,' '.join([x for x in forms if x != None])): #see if the glyph is there
            # log.info("Found glyph '{}'".format(glyph))
            return glyph #find it and stop looking, or return nothing
        # log.info("Found not glyph '{}'".format(glyph))
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
def slisttoalternations(graphemeset,group=False):
    # This '|' delimited list should never go inside of [^ ], as it will be
    # misinterpreted!!
    # This provides the form to go in [^ ] lists or alone, with a one grouping
    # around the list, but with longer graphemes first (trigraphs, then
    # digraphs and decomposed characters)
    output='|'.join(sorted(graphemeset,key=len,reverse=True))
    if group:
        output='('+output+')'
    return output
def s(sdict, stype, polyn=0, word=False, compile=False): #settings lang=None
    """join a list into regex format, sort for longer first, to capture
    the largest units possible."""
    """stype is a capital symbolic representation of the group of letters,
    e.g., N for nasals, D for depressors, etc. """
    """sdict should be a dictionary value keyed by check/settings.s[analang]"""
    graphemeset=set()
    if '+' in stype:
        log.info("s looking for {} in these keys: {}".format(stype,sdict))
    graphemevariables=stype.split('+')
    for x in set(sdict) & set(graphemevariables):
        graphemeset|=set(sdict[x])
        graphemevariables.remove(x)
    if graphemevariables:
        raise KeyError("stype {} leaves {}, which is not in dict keys: {}"
                    "".format(stype, graphemevariables, sdict.keys()))
    if polyn:
        #make the above limited by len here
        graphemeset=[i for i in graphemeset if len(i) == polyn]
    output=slisttoalternations(graphemeset,group=True)
    if compile:
        # log.info("Compiling {}[{}] regex {} (word={})"
        #         "".format(stype,polyn,output,word))
        return make(output, word=word, compile=compile)
    else:
        return output
def make(regex, **kwargs):
    # if (re.match('^[^(]*\|',regex)) or (re.search('\|[^)]*$',regex)):
    #     log.error('Regex problem! (need parentheses around segments!):',regex)
    #     exit()
    word=kwargs.get('word')
    compile=kwargs.get('compile')
    caseinsensitive=kwargs.get('caseinsensitive')
    if kwargs.get('word'):
        """To make alternations and references work correctly, this should
        already have parentheses () around each S."""
        regex='^'+regex+'$'
    if kwargs.get('caseinsensitive'):
        flags=re.UNICODE|re.IGNORECASE
    else:
        flags=re.UNICODE
    if kwargs.get('compile'):
        try:
            regex=re.compile(regex, flags=flags)
        except:
            log.error('Regex problem!')
    return regex
def nX(segmentsin,segmentsout,n):
    #Start by being clear which graphs count, and which don't.
    # these should mutually exclude each other.
    overlap=set(segmentsin) & set(segmentsout)
    if overlap:
        log.error("Your in/out segment lists overlap: {}".format(overlap))
        # log.error("in: {}".format(segmentsin))
        # log.error("out: {}".format(segmentsout))
    # for each of in/out, make a dict keyed by length, with value listing glyphs
    # with that length (automatically separate trigraphs, digraphs, etc)
    sindict={n:[i for i in segmentsin if len(i) == n]
                for n in range(1,len(max(segmentsin,key=len, default=''))+1)}
                #?default='' b/c can be empty sometimes, early on
    soutdict={n:[i for i in segmentsout if len(i) == n]
                for n in range(1,len(max(segmentsout,key=len, default=''))+1)}
                #default='' b/c can be empty sometimes, early on
    # Convert those value lists to a string of alternations, for each key
    sin={k:slisttoalternations(sindict[k]) for k in sindict}
    sin.update({'all':slisttoalternations([i for j in sindict.values()
                                            for i in j])})
    sout={k:slisttoalternations(soutdict[k]) for k in soutdict}
    sout.update({'all':slisttoalternations([i for j in soutdict.values()
                                            for i in j])})
    # Make a list, longest first
    # this probably doesn't need the isdigit test
    strlist=[sout[i] for i in range(max([j for j in sout.keys()
                                        if str(j).isdigit()],default=0),
                                    0,-1)]
    #join list of alternations to one long alternation
    notS='|'.join(strlist)
    strlist+=['('+sin['all']+')'] #look for, capture this
    #This needs to multiply as a unit, while getting each subpart separately:
    oneS='(('+notS+')*('+sin['all']+'))'#.join(strlist)
    #We need to keep each alternation set a unit, and keep all but last in \1
    if n-1:
        priors='('+oneS*(n-1)+')'
    else:
        priors=''
    nS='('+priors+'('+notS+')*)('+sin['all']+')'
    # for n,i in enumerate([sin,sout,oneS,notS,nS]):
    #     print(n,i)
    # log.info("Compiling X{} regex {}".format(n,nS))
    return make(nS, compile=True)
def fromCV(CVs, sdict, distinguish, **kwargs): #check, lang
    """ this inputs regex variable (regexCV), a tuple of two parts:
    1. abbreviations with 'C' and 'V' in it, and/or variables for actual
    segments or back reference, e.g., 1 for \1 or 2 for \2, and 'c' or 'v'.
    2. dictionary of variable meanings (e.g., {'v':['e',...]}).
    e.g., for total variable: CVs=("CvC2",{'v':['e',...]})
    CAUTION: if you don't have this dictionary, CVs[0] is just one letter...
    It outputs language specific regex (compiled if compile=True,
    whole word word=True)."""
    """lang should be check.analang"""
    if type(CVs) is not str:
        log.error("regexCV is not string! ({})".format(CVs))
    CVs_ori=CVs
    sdict=sdict.copy()
    regex=list()
    references=('\1','\2','\3','\4')
    references=range(1,5)
    # Replace word final Consonants first, to get them out of the way:
    this='C'
    for wd in [i for i in distinguish if 'wd' in i]:
        if distinguish[wd]: # If distinguished, replace them now
            CVs=re.sub(wd.replace('wd','$'),s(sdict,wd.replace('wd','')),CVs)
        elif CVs.endswith(wd.replace('wd','')):
            raise KeyError("CV profile {} ends with {}, which is not "
                        "distinguished there".format(CVs_ori,
                                                    wd.replace('wd','')))
        else:
            this+='+'+wd.replace('wd','')
    #Pull out C# first; finds only relevant segments not distinguished from Cs
    rxthis=s(sdict,this)
    if rxthis:
        CVs=re.sub('C$',rxthis,CVs)
    else:
        log.error("No rxthis? ({}): {}".format(this,sdict))
    # At this point, all word final Consonant variables should be gone;
    # the following is for other word placement.
    for x in [i for i in distinguish if 'wd' not in i]:
        if distinguish[x]:
            CVs=re.sub(x,s(sdict,x),CVs)
        elif x in CVs:
            raise KeyError("CV profile {} contains {}, which is not "
                            "distinguished there".format(CVs_ori,x))
        else:
            sdict['C']+=sdict[x] #these are all consonants, if not distinguished
            del sdict[x] #don't leave this key there to find stuff below
    for x in sdict:
        rxthis=s(sdict,x) #this should have parens for each S
        CVs=re.sub(x,rxthis,CVs)
        # log.info('CVs: {}'.format(CVs))
    for x in references: #get capture group expressions
        CVrepl='\\\\{}'.format(str(x)) #this needs to be escaped to survive...
        # log.info('x: {}; repl: {}'.format(x,CVrepl))
        # log.info('CVs: {}'.format(CVs))
    """Confirm that r is correct here"""
    CVs=re.sub(r'\)([^(]+)\(',')(\\1)(',CVs) #?
    # log.info('Going to compile {} into this regex : {}'.format(CVs_ori,CVs))
    return make(CVs, **kwargs)
if __name__ == '__main__':
    x='ne [pas] plaire, (ne pas) agréer, ne pas'
    rgx='(ne pas) agréer'
    ts=['bobongo','bobingo']
    check='V1=V2=V3'
    value='a'
    sdict={'D': ['gh', 'bb', 'dd', 'gg', 'gu', 'mb', 'nd', 'dw', 'gw', 'zl', 'b', 'B', 'd', 'g', 'j', 'v', 'z'], 'C': ['ckw', 'thw', 'tch', 'cc', 'pp', 'pt', 'tt', 'ck', 'qu', 'tw', 'kw', 'ch', 'ph', 'sh', 'hh', 'ff', 'sc', 'ss', 'th', 'sw', 'hw', 'ts', 'sl', 'p', 'P', 't', 'c', 'k', 'q', 'f', 's', 'x', 'h'], 'G': ['yw', 'y', 'w'], 'N': ['mm', 'ny', 'gn', 'nn', 'nw', 'm', 'n'], 'S': ['rh', 'wh', 'll', 'rr', 'lw', 'rw', 'l', 'r'], 'ʔ': ["'"], 'V': ['ou', 'ei', 'ai', 'yi', 'ea', 'ay', 'ee', 'ey', 'ie', 'oa', 'oo', 'ow', 'ue', 'oe', 'au', 'oi', 'eau', 'a', 'e', 'i', 'o', 'u', 'I', 'O', 'é'], '̀': [], 'ː': [], '=': ['-'], '<': []}
    distinguish={'<': True, '=': True, 'G': True, 'Gwd': False, 'N': False, 'S': False, 'Swd': True, 'D': False, 'Dwd': False, 'Nwd': False, 'ʔ': False, 'ʔwd': True, '̀': False, 'ː': False}
    for CVs in [
    'CaCVC','CaCV','CaCVʔ',
    'CaCVS','CaGVC']:
        fromCV(CVs, sdict, distinguish, word=True, compile=True, caseinsensitive=True)
    # s='ááààééèèííììóóòòúúùù'
    # s2=makeprecomposed(s)
    # print(s,s2)
