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
        # log.info("subbing {} for {} in {}, using {}".format(value,c,t,
        #                                             regexdict[c]))
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
    """This fn takes a list (or set) of graphemes and
        orders them longest first
        separates with '|'
        (group) if kwarg['group']=True
    """
    # This '|' delimited list should never go inside of [^ ], as it will be
    # misinterpreted!!
    # This provides the form with or without one grouping
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
    # log.info("making regex {} with kwargs:{}".format(regex,kwargs))
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
        except ValueError as e:
            log.error('Regex Value compile problem ({};{})'.format(e,regex))
        except Exception as e:
            log.error('Regex compile problem ({};{})'.format(e,regex))
    return regex
class RegexDict(dict):
    """This makes and stores all the regex's needed for A−Z+T (for now)"""
    """distinguish and interpret should only be set once, on boot"""
    """This should probably reference/store another class of regexs which
    would have strings and compiled versions?"""
    """This needs to output"""
    def nX(self,x,n):
        """Make a variable to find the nth occurrance of x
        Start by being clear which graphs count, and which don't.
        These should mutually exclude each other.
        n is the occurance to look for, e.g., C3 is n=3.
        """
        # log.info(f"Working with {self.sdict[x]}")
        if x in ['C','V']:
            sin=[j for i in [x]+self.distinguished(x,value=False)
                for j in self.sdict[i]]
        else:
            sin=self.sdict[x]
        sout=[j for i in self.sdict #keys only here
            if i not in [x]+self.distinguished(x,value=False)
            for j in self.sdict[i]
            ]
        # log.info("Using segments in: {} out: {}".format(sin,sout))
        overlap=set(sin) & set(sout)
        if overlap:
            log.error("Your in/out segment lists overlap: {}".format(overlap))
            # log.error("in: {}".format(segmentsin))
            # log.error("out: {}".format(segmentsout))
        # for each of in/out, make a dict keyed by length, with value listing glyphs
        # with that length (automatically separate trigraphs, digraphs, etc)
        sindict={n:[i for i in sin if len(i) == n]
                    for n in range(1,len(max(sin,key=len, default=''))+1)}
        soutdict={n:[i for i in sout if len(i) == n]
                    for n in range(1,len(max(sout,key=len, default=''))+1)}
        # Convert those value lists to a string of alternations, for each key
        sin={k:slisttoalternations(sindict[k]) for k in sindict}
        sin.update({'all':slisttoalternations([i for j in sindict.values()
                                                for i in j])})
        sout={k:slisttoalternations(soutdict[k]) for k in soutdict}
        sout.update({'all':slisttoalternations([i for j in soutdict.values()
                                                for i in j])})
        # Make a list, longest first
        strlist=[sout[i] for i in range(max([j for j in sout.keys()
                                            if str(j).isdigit()],default=0),
                                        0,-1)]
        #join list of alternations to one long alternation
        notS='|'.join(strlist)
        strlist+=['('+sin['all']+')'] #look for, capture this
        #This needs to multiply as a unit, while getting each subpart separately:
        oneS='(('+notS+')*('+sin['all']+'))'
        #We need to keep each alternation set a unit, and keep all but last in \1
        if n-1:
            priors='('+oneS*(n-1)+')'
        else:
            priors=''
        #anchor the begining, not the end:
        nS='^('+priors+'('+notS+')*)('+sin['all']+')'
        # log.info("Compiling X{} regex {}".format(n,nS))
        self.setnXrx(x,n,nS)
    def makegroup(self,x,**kwargs):
        """this makes (x|y) format from C+D+N, etc.,
        Distinctions should already be accounted for in the variable (x)
        length and compilation are managed in s"""
        # log.info(f"Making a regex group with kwargs {kwargs}")
        return s(self.glyphsforvariable(x),**kwargs)
    def glyphsforvariable(self,stype): #self.sdict
        """This returns a set of all the graphemes for a single group,
        stype: a capital symbolic representation of the group of letters,
                e.g., N for nasals, D for depressors, etc.
                -joined by '+' when added together (to make a larger set).
        This script does NOT distinguish between
        --location (final, non-final), (this should already be done)
        --what should be distinguished (this should already be done)
        --glyph length (polyn) (this is done later)
        """
        graphemeset=set()
        graphemevariables=stype.split('+')
        # Collect variables that are both given and in the dict:
        for x in set(self.sdict) & set(graphemevariables):
            # track that all given variables are used (or throw error):
            graphemeset|=set([i for i in self.sdict[x]])
            graphemevariables.remove(x)
        if graphemevariables:
            raise KeyError("stype {} leaves {}, which is duplicated or not in "
            "dict keys: {}".format(stype, graphemevariables, self.sdict.keys()))
        return graphemeset
    def interpretationsanitycheck(self,x):
        for i in self.interpret:
            if i in x and i != self.interpret[i]:
                raise ValueError("Syllable profile {} contains {}, which "
                "should be {} (according to your settings)"
                "".format(x,i,self.interpret[i]))
    def interpreted(self,x,**kwargs):
        """This fn expands C, or V into a regex matching all that should be
        interpreted as C, with an extra optional group for each new symbol.
        It strips 'wd' suffix, setting kwargs[final]=True when found."""
        """Linguistics Note: I'm assuming that if CG and CS should each be
        interpreted as C, the combo would be CGS, rather than CSG (due to
        sonority hierarchy). If this assumption fails, we should revisit this.
        Not sure what to do with order conflicts between 'VN' and 'Vː'; is there
        an orthographic convention for this?"""
        """Because the syllable profile analysis will have been simplified by
        the interpretation settings, here we return the regex to include all
        possible complexity."""
        output=x
        result=''
        kwargs['compile']=kwargs['word']=False
        if 'wd' in x:
            kwargs['final']=True
            x=x.strip('wd')
        if x in ['C','V']:
            basedone=False
            interplist=['NC','CG','CS','VV','VN'] #in this order!
            assert set(interplist) >= set(self.interpret) #error on new values
            for interp in interplist:
                if x in interp and self.interpret[interp] == x:
                    # log.info("complex interpretation! ({}={})".format(interp,x))
                    for i in interp:
                        """This works because of the ordering of interplist.
                        There is only one pre-C segment, then C, then G and/or S
                        """
                        if i in ['C','V'] and not basedone: #just do this once!
                                r=self.makegroup(
                                    self.undistinguished(i,**kwargs),
                                    **{**kwargs, 'compile':False})
                                if r == '()':
                                    # log.info(f"r is {r}, so returning empty")
                                    return r #don't add to nothing
                                # log.info(f"r is {r} {type(r)}; continuing")
                                result+=r
                                basedone=True
                        else: #get just this group
                            result+=self.makegroup(i)
                            result+='?' # this group is optional in the regex
        if not result:
            result=self.makegroup(self.undistinguished(x,**kwargs), #final?
                                    **{**kwargs, 'compile':False})
        # log.info("returning {}".format(result))
        return result
    def undistinguished(self,variableset,**kwargs):
        """This function converts C or V (or others) into a variable
        representing each class that should be included, based on
        self.distinguished values and (non-)final position."""
        v_ori=variableset
        if kwargs.get('final'):
            for wd in self.distinguished(variableset,False,**kwargs):
                variableset+='+'+wd.replace('wd','')
        else:
            for x in self.distinguished(variableset,False,**kwargs):
                variableset+='+'+x
        # log.info("Returning {} for {} {}".format(variableset,v_ori,kwargs))
        return variableset
    def distinguished(self,x,value=True,**kwargs): #self.distinguish
        """This outputs a list of all segment types which are distinguished
        (from C or V) in the given position (or NOT distinguished,
        if value=False) —evidently, not including C or V."""
        if x == 'C':
            l=['G','N','S','D','ʔ']
            if kwargs.get('final'):
                l=[i+'wd' for i in l]
            dset=set(l)
        elif x == 'V':
            dset=set(['̀','ː'])
        else:
            dset=set()
        dset&=set(self.distinguish) #limit dset to what is there, in case
        if value:
            return [i for i in dset if self.distinguish[i]]
        else:
            return [i for i in dset if not self.distinguish[i]]
    def setnXrx(self,s,n,nS):
        # These should always be all glyphs
        # log.info("Setting {}{} value {}".format(s,n,nS))
        self.rxuncompiled[s+str(n)]=nS
        self.rx[s+str(n)]=make(nS, compile=True)
    def setrx(self, c, crx, **kwargs):
        polyn=kwargs.get('polyn') #put this in the correct place
        if not crx or crx == '()':
            return #don't make or store empty regexs; they match everywhere
        # log.info("Setting {} with {} value {}".format(c,polyn,crx))
        if len(c) == 1:
            setnesteddictval(self.rxuncompiled,crx,c,polyn)
            setnesteddictval(self.rx, make(crx, **{**kwargs,'compile':True}),
                            c, polyn)
        else:
            self.rxuncompiled[c]=crx
            self.rx[c]=make(crx, **{**kwargs,'compile':True})
    def getrx(self, c, **kwargs):
        if len(c) == 1:
            return self.rx[c][kwargs.get('polyn')]
        else:
            return self.rx[c]
    def getrxuncompiled(self, c, **kwargs):
        if len(c) == 1:
            return self.rxuncompiled[c][kwargs.get('polyn')]
        else:
            return self.rxuncompiled[c]
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
