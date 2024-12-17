#!/usr/bin/env python3
## coding=UTF-8
import re
import time
import logsetup
from utilities import *
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
    for i in [d,p,l,o]:
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
def search(*args,**kwargs):
    return re.search(*args,**kwargs)
def compile(x):
    return re.compile(x, re.UNICODE)
def id(x):
    translations=[('˥˦˧˨˩', '43210'),
    (r'][  .!=(),\'/?:;+*'+'\n','_'),
    (r"][. /?*\:;|,\"><'‘’",'_'),
    ("éèê",'e'),#ɛə
    ("ô",'o')
    ]
    for t in translations:
        if len(t[0]) == len(t[1]):
            t={t[0][i]:t[1][i] for i in range(len(t[0]))}
        else:
            for i in t[0]:
                print(i)
            t={i:t[1] for i in t[0]}
        x=x.translate(str.maketrans(t))
    """Confirm that r is correct here"""
    return x
def tonerxs():
    return (re.compile('[˥˦˧˨˩]+', re.UNICODE),
            re.compile(' ', re.UNICODE),
            re.compile(' ', re.UNICODE))
def update(t,regexdict,check,value,matches=[]):
    tori=t
    for c in reversed(check.split('=')):
        log.info("subbing {} for {} in {}, using {}".format(value,c,t,
                                                    regexdict[c]))
        match=regexdict[c].search(t)
        if match:
            matches.append(match.groups()[-1])
            t=match.expand('\\g<1>'+value)+t[match.end():]
    # log.info("updated {} > {}".format(tori,t))
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
def s(graphemeset, **kwargs):
    """join a list into regex format, sort for longer first, to capture
    the largest units possible."""
    polyn=kwargs.get('polyn')
    if polyn: #use all if 0
        #make the above limited by len here
        graphemeset=[i for i in graphemeset if len(i) == polyn]
    output=slisttoalternations(graphemeset,group=True)
    if kwargs.get('compile'):
        # log.info("Compiling {}[{}] regex {} (word={})"
        #         "".format(stype,polyn,output,word))
        return make(output, **kwargs)
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
class RegexDict(dict):
    """This makes and stores all the regex's needed for A−Z+T (for now)"""
    """distinguish and interpret should only be set once, on boot"""
    """This should probably reference/store another class of regexs which
    would have strings and compiled versions?"""
    """This needs to output"""
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
    def fromCV(self, CVs, **kwargs): #check, lang
        """CVs is a regex variable (regexCV), which may be a combination of
        specific glyphs and variables (e.g., 'C','V') in it. This should NOT
        contain characters in positions that are not distinguished!"""
        """It outputs a language specific regex (compiled if compile=True,
        whole word word=True)."""
        if type(CVs) is not str:
            log.error("regexCV is not string! ({})".format(CVs))
        self.interpretationsanitycheck(CVs)
        try:
            if kwargs.get('compile'):
                log.info("Processed to here")
                return self.getrx(CVs, **kwargs)
            else:
                return self.getrxuncompiled(CVs)
        except Exception as e:
            # log.info("Getrx Exception: {}".format(e))
            pass
        log.info("No rx found in rxdict; making {}".format(CVs))
        CVs_ori=CVs
        regex=list()
        this='C'
        for wd in self.distinguished('C',True,final=True): #doesn't include C
            # If Xwd is distinguished, replace it now
            # log.info("{} in distinguishedTrueFinal for {}".format(wd,CVs))
            s=wd.replace('wd','')
            if s in CVs: #otherwise, waste and recursion
                CVs=re.sub(wd.replace('wd','$'),
                        #This should not be compiled:
                        self.makegroup(wd.replace('wd',''),
                                        polyn=kwargs.get('polyn')),
                                        CVs)
        # log.info("Replacing final distinguished (non-C): {}".format(CVs))
        for wd in self.distinguished('C',False,final=True): #sanity check only
            # log.info("{} in distinguishedFalseFinal for {}".format(wd,CVs))
            s=wd.replace('wd','')
            if s in CVs and CVs.endswith(s) and len(CVs)-1: #Don't object if len=1
                raise KeyError("CV profile {} ends with {}, which is not "
                            "distinguished there".format(CVs_ori,s))
        rxthis=self.interpreted('C',final=True, **kwargs)
        if rxthis: #confirm there are segments to find first
            CVs=re.sub('C$',rxthis,CVs)
        # else:
        #     log.error("No rxthis? ({}): {}".format(this,self.sdict))
        # log.info("Replacing final distinguished (C): {}".format(CVs))
        # At this point, all word final Consonant variables should be gone;
        # the following is for non-final distinguished consonants.
        for x in self.distinguished('C',True,final=False):
            # log.info("{} in distinguishedTrueNon-Finalfor {}".format(x,CVs))
            if x in CVs:
                CVs=re.sub(x,
                        # self.fromCV(x, causes recursion?
                        self.makegroup(x,
                        polyn=kwargs.get('polyn')), #Should not be compiled!
                        CVs)
                log.info("Now {}".format(CVs))
        for x in self.distinguished('C',False,final=False): #sanity check only
            # log.info("{} in distinguishedFalseNon-Final for {}".format(x,CVs))
            if s in CVs and x in CVs and len(CVs)-1: #Don't object if len=1
                raise KeyError("CV profile {} contains {}, which is not "
                                "distinguished there".format(CVs_ori,x))
        # log.info("Replacing non-final distinguished (C): {}".format(CVs))
        # Only V and non-final C should be left at this point.
        for svar in ['C','V']: #no contrast for vowels word finally, as of now
            # interpreted never returns compiled
            rxthis=self.interpreted(svar,final=False, **kwargs)
            if rxthis: #confirm there are segments to find first
                CVs=re.sub(svar,rxthis,CVs)
            # else:
            #     log.error("No rxthis? ({}): {}".format(this,self.sdict))
        # log.info("Replacing other Cs and Vs: {}".format(CVs))
        CVs=re.sub(r'\)([^(?]+)\(',')(\\1)(',CVs) #this puts parens around everything
        log.info('Going to compile {} into this regex : {}'.format(CVs_ori,CVs))
        self.setrx(CVs_ori, CVs, **kwargs)
        return self.getrx(CVs_ori, **kwargs)
    def profileofform(self,form,ps):
        if not form or not ps:
            # log.info("Either no form ({}) or no ps ({}); returning".format(form,ps))
            return 'Invalid'
        profile=form
        for polyn in range(4,0,-1): #find and sub longer forms first
            for s in set(self.profilelegit) & set(self.rx):
                if polyn in self.rx[s]:
                    # log.info(f"Checking for {s} with {self.rx[s][polyn]}")
                    profile=self.rx[s][polyn].sub(s,profile)
        # log.info(f"ready to return {formori}>{form}")
        return profile
    def makeprofileforcheck(self,**kwargs):
        check=kwargs.get("check")
        replS='\\1'+kwargs.get("group")
        regexCV=str(kwargs.get("profile"))
        groupcomparison=kwargs.get("groupcomparison")
        if groupcomparison:
            log.info(f"going to make {check} profile for {kwargs.get("group")} "
                    f"and {groupcomparison}")
        for cvt in ['CxV','VxC','C','V']:
            if cvt in check:
                S=str(cvt).replace('x','')
                regexS='.*?'+S
                maxcount=countxiny(S, regexCV)
                break
        #don't compare CVs or VCs with each other (e.g., CV1xCV2):
        if 'x' in check and 'CxV' not in check and 'VxC' not in check:
            replScomp='\\1'+groupcomparison
            compared=False
            # log.info("Making regex for {} check with group {} and "
            # "comparison {} ({})".format(check,group,self.groupcomparison,replS))
        elif 'x' in check:
            replS=replS+groupcomparison
            compared=True #well, don't do two runs, in any case.
            # log.info("Making regex for {} check with group {} ({})"
            #         "".format(check,group,replS))
        for occurrence in reversed(range(maxcount)):
            occurrence+=1
            # log.info("S+str(occurrence): {}".format(S+str(occurrence)))
            # log.info("Check (less x): {}".format(check.replace('x','')))
            if S+str(occurrence) in check.replace('x',''):
                """Get the (n=occurrence) S, regardless of intervening
                non S..."""
                regS='^('+regexS*(occurrence-1)+'.*?)('+S+')'
                if 'x' in check and not compared:
                    regexCV=sub(regS,replScomp,regexCV, count=1)
                    compared=True
                else:
                    regexCV=sub(regS,replS,regexCV, count=1)
        """Final step: convert the CVx code to regex, and store in self."""
        return self.fromCV(regexCV,
                            word=True, compile=True, caseinsensitive=True)
    """These make regexs to manipulate syllable profile patterns"""
    def makeprofileregexs(self):
        """These are just to find (combinations of) variables in syllable
        profiles"""
        self.rx_profile={} #these look for profile variables
        sclassesC=['N','S','G','ʔ','D']
        o=["̀",'<','=','ː']
        for posC in ['^C','C$']:
            self.rx_profile[posC]=compile(posC)
        for c in self.distinguish:
            if 'wd' in c or c in o: # positive lookahead: word final
                self.rx_profile[c]=compile(c.strip('wd')+r'(?=\Z)')
            else: # negative lookahead: not word final
                self.rx_profile[c+'_']=compile(c+r'(?!\Z)')
        for cc in self.interpret:
            self.rx_profile[cc]=compile(cc) #no polygraphs here
    """These make rxs to find glyphs given a variable (C,V,N,G,S,etc), any
        or first, second, etc occurrance"""
    def makeglyphregex(self,c,**kwargs):
        """We are doing a few things here:
        1. regex to find all glyphs of a variable (n=0)>rx[v][0]
        2. regex to find glyphs of a variable with length=n>rx[v][n]
        3. regex to find the nth occurance of a variable (e.g., C3) >rx[Cn]
        All of these should respect interpret/distinguish and finality!
        """
        for pn in range(4,-1,-1):
            # log.info(f"Trying pn {pn} for {c}; final={kwargs.get('final')}")
            kwargs['polyn']=pn
            try:
                self.setrx(c,self.interpreted(c,
                                **kwargs), #limit glyphs in interpreted
                                **kwargs) #store in correct place
            except TypeError as e:
                log.error("{}({}): {}".format(c,pn,self.rx[c]))
                raise
        # log.info(f"compileCVrxforsclass {c} RXs: {self.rx[c]}")
        # log.info("Looking for sclass {} in {}".format(c,self.sdict))
        return #I don't think we use this next bit, but may some day
        for n in range(1,7): #just the Nth C or V, no polygraph distinction
            self.nX(c,n) #no polygraphs here
        # log.info(f"makeglyphregexs self.rx: {self.rx}")
    def makeglyphregexs(self):
        todo=['C','V','Cwd']+[k for k in self.distinguish if self.distinguish[k]
                                and self.sdict[k.strip('wd')]] #only if there
        notdo=set(self.sdict)-set(todo)
        log.info(f"Going to make rxs for {todo}; not doing {notdo}")
        for c in todo:
            self.makeglyphregex(c)
    def __init__(self,**kwargs):
        super(dict, self).__init__()
        self.count=0
        """At some point, I should think about distinguishing interpretation of
        VV as V, V:, or VV depending on V1=V2 or V1≠V2."""
        #distinguish,interpret,sdict,profilelegit,invalidchars,profilesegments
        for k in kwargs:
            setattr(self,k,kwargs[k])
        self.rx={} #This holds rx's keyed by variable to find all glyphs.
        self.rxuncompiled={} #uncompiled versions
        self.makeprofileregexs()
        self.makeglyphregexs()
if __name__ == '__main__':
    x="ne [pas] ˥plai're, (ne pas) ˧agréer, ne pas\n][  .!=(),'/?:;+*][. /?*\:;|,\"><'‘’"
    i=id(x)
    print(x,i,"end")
    quit()
    rgx='(ne pas) agréer'
    ts=['bobongo','bobingo']
    check='V1=V2=V3'
    value='a'
    sdict={'D': ['gh', 'bb', 'dd', 'gg', 'gu', 'mb', 'nd', 'dw', 'gw', 'zl',
                'b', 'B', 'd', 'g', 'j', 'v', 'z'],
            'C': ['ckw', 'thw', 'tch', 'cc', 'pp', 'pt', 'tt', 'ck', 'qu', 'tw',
                'kw', 'ch', 'ph', 'sh', 'hh', 'ff', 'sc', 'ss', 'th', 'sw',
                'hw', 'ts', 'sl', 'p', 'P', 't', 'c', 'k', 'q', 'f', 's', 'x',
                'h'],
            'G': ['yw', 'y', 'w'],
            'N': ['mm', 'ny', 'gn', 'nn', 'nw', 'm', 'n'],
            'S': ['rh', 'wh', 'll', 'rr', 'lw', 'rw', 'l', 'r'],
            'ʔ': ["'"],
            'V': ['ou', 'ei', 'ai', 'yi', 'ea', 'ay', 'ee', 'ey', 'ie', 'oa',
                'oo', 'ow', 'ue', 'oe', 'au', 'oi', 'eau', 'a', 'e', 'i', 'o',
                'u', 'I', 'O', 'é'],
            '̀': [], 'ː': [], '=': ['-'], '<': []}
    distinguish={
                    'G': False, 'Gwd': False,
                    'S': False, 'Swd': False,
                    'D': True, 'Dwd': False,
                    'N': False, 'Nwd': True,
                    'ʔ': False, 'ʔwd': False,
                    '<': True, '=': True,
                    '̀': False, 'ː': False}
    interpret={'NC': 'C',
                'CG': 'C',
                'CS': 'C',
                'VV': 'VV',
                'VN': 'VN'}
    invalidchars=[' ','...',')','(<field type="tone"><form lang="gnd"><text>'] #multiple characters not working.
    invalidregex=r'( |\.|,|\)|\()+'
    # self.profilelegit=['#','̃','C','N','G','S','V','o'] #In 'alphabetical' order
    profilelegit=['̃','N','G','S','D','C','Ṽ','V','ʔ','ː',"̀",'=','<'] #'alphabetical' order (had '#'?)
    profilesegments=['N','G','S','D','C','V','ʔ']
    d=RegexDict(distinguish=distinguish,
                interpret=interpret,
                sdict=sdict,
                invalidchars=invalidchars,
                profilelegit=profilelegit,
                profilesegments=profilesegments
    )
    exit()
    log.info(d.distinguish)
    log.info(d.sdict)
    log.info(d.glyphsforvariable('C+D'))
    # exit()
    log.info(d.interpret)
    log.info("distinguished Final (True): {}".format(d.distinguished('C',True,final=True)))
    log.info("distinguished Final (False): {}".format(d.distinguished('C',False,final=True)))
    log.info("distinguished (True): {}".format(d.distinguished('C',True,final=False)))
    log.info("distinguished (False): {}".format(d.distinguished('C',False,final=False)))
    # d.interpreted('C',final="True")
    # d.interpreted('V',final="True")
    # d.interpreted('C',final="False")
    # d.interpreted('V',final="False")
    # exit()
    for CVs in ['C'+str(i) for i in range(1,6)]:
    # [
    # 'CVCVC','CVCV','CVCVS','CVCCVC','CVCCCVC','CACV','CACCVC','CVC'
    # # 'CaNCVC',
    # # 'CaCV','CaCVʔ',
    # # 'CaCVS','CaGVC'
    # ]:
        print(d.rxuncompiled[CVs])
        print('\n'+CVs,'\t(not)')
        # r=d.fromCV(CVs, word=True, compile=True, caseinsensitive=True)
        r=d.rx[CVs]
        for w in [
            # 'bambat','wambut','wambat',
            # 'bablat','wabwut','wablwat','wabwlat',
            # 'babat','wawut','walat',
            'no', 'non', 'bon', 'bono', 'bogon', 'bogono',
            'nonomon', 'pokemon', 'mblano', 'mbwana', 'mpsyaka'
            # "pa'at",'wapput','nappall',
            # 'bamban','wambun','wama',
            # 'bambay','wambuy','waya',
            # 'bambal','wambul','wala','wal',
            # 'wat','tat','taw','lat'
                ]:
            # print(type(r),r)
            if bool(r.match(w)):
                print(w)
            else:
                print('\t'+w)#,r.match(w))
    # s='ááààééèèííììóóòòúúùù'
    # s2=makeprecomposed(s)
    # print(s,s2)
