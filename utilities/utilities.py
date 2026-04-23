#!/usr/bin/env python3
# coding=UTF-8
import ast
import inspect #this is for determining this file name and location
# import logsetup
import datetime
import sys
import logging
import platform
import os
import subprocess
import webbrowser
from utilities import logsetup
from utilities.encodings import *
log = logging.getLogger(__name__)
from utilities.i18n import _
"""Functions moved from main.py"""
class Object:
    def __init__(self,**kwargs):
        for k in kwargs:
            setattr(self,k,kwargs[k])

def dictofchilddicts(dict,remove=None):
    # This takes a dict[x][y] and returns a dict[y], with all unique values
    # listed for all dict[*][y].
    # log.info("Working on dict {}".format(dict))
    o={}
    for x in dict:
        for y in dict[x]:
            if y not in o:
                o[y]=[]
            if isinstance(dict[x][y],list):
                for z in dict[x][y]:
                    o[y].append(z)
            else:
                o[y].append(dict[x][y])
    # log.info("o1:{}".format(o))
    for y in o:
        o[y]= list(dict.fromkeys(o[y]))
        if type(remove) is list:
            for a in remove:
                if a in o[y]:
                    o[y].remove(a)
    # log.info("o2:{}".format(o))
    return o
def flatten(l):
    if type(l) is not list:
        return _("{item} is not a list!").format(item=l)
    if l == [] or type(l[0]) is not list:
        return _("The first element of {list} is not a list!").format(list=l)
    return [i for j in l for i in j] #flatten list of lists
def addxofytocorrectplaceinlistoflists(x,y,o):
    for k in o:
        if y in k and k.index(y) == len(k)-1:
            k.append(x)
            return o
        elif y in k and k.index(y) == 0:
            k.insert(0,x)
            return o
        elif y in k:
            o.append([x])
            return o
    #only add for y not in k after going through all of o
    o.append([x])
    return o
def addxofytolistoflists(x,y,o):
    if x not in [i for j in o for i in j]:
        if y in [i for j in o for i in j]:
            o=addxofytocorrectplaceinlistoflists(x,y,o)
        else:
            o.append([x])
    return o
def dictscompare(dicts,ignore=[],flat=True):
    keyswoignore=[k for k in dicts if dicts[k] not in ignore]
    if len(keyswoignore) <= 1:
        # log.debug(_("One or less dict: {dicts}; just returning key.").format(dicts=dicts))
        return [keyswoignore] #This should be a list of lists
    l=dictscompare11(dicts,ignore=ignore)
    o=list([],)
    for c in l:
        for x,y in [c[0]]:
            o=addxofytolistoflists(x,y,o)
            o=addxofytolistoflists(y,x,o)
    if flat == False:
        return o
    else:
        return [i for j in o for i in j]
def dictscompare11(dicts,ignore=[]):
    values={}
    for d1 in dicts:
        for d2 in dicts:
            if d2 == d1 or (d2,d1) in values:
                continue
            values[(d1,d2)]=dictcompare(dicts[d1],dicts[d2],ignore=ignore)[0]
    valuelist=[(x,values[x]) for x in values.keys()]
    valuelist.sort(key=lambda x: x[1],reverse=True)
    return valuelist
def dictcompare(x,y,ignore=[]):
    pairs = dict()
    unpairs=dict()
    for k in x:
        if k not in ignore and x[k] not in ignore:
            if k in y and y[k] not in ignore: #Only compare *same* keys
                if x[k] == y[k]:
                    pairs[k] = x[k]
                else:
                    unpairs[k] = (x[k],y[k])
    if len(pairs)+len(unpairs) == 0:
        r=0 #this beats a div0 error
    else:
        r=len(pairs)/(len(pairs)+len(unpairs))
    return (r,pairs,unpairs)
def exampletype(**kwargs):
    if not kwargs:
        print("exampletype called without kwargs")
    for arg in ['wglosses']:
        kwargs[arg]=kwargs.get(arg,True)
    for arg in ['renew','wsoundfile']:
        kwargs[arg]=kwargs.get(arg,False)
    # log.info("Returning exampletype kwargs {}".format(kwargs))
    return kwargs
def checkslicetype(**kwargs):
    for arg in ['cvt','ps','profile','check']:
        kwargs[arg]=kwargs.get(arg,None)
    # log.info("Returning checkslicetype kwargs {}".format(kwargs))
    return kwargs
def grouptype(**kwargs):
    for arg in ['wsorted','tosort','toverify','tojoin','torecord','comparison',
                'todo'
                ]:
        kwargs[arg]=kwargs.get(arg,False)
    # log.info("Returning grouptype kwargs {}".format(kwargs))
    return kwargs
def ifone(l,nt=None):
    if l and not len(l)-1:
        return l[0]
def firstoflist(l,othersOK=False,all=False,ignore=[None]):
    #rename to unlist
    """This takes a list composed of one item, and returns the item.
    with othersOK=True, it discards n=2+ items; with othersOK=False,
    it throws an error if there is more than one item in the list."""
    if type(l) is not list:
        return l
    if (l is None) or (l == []):
        return
    if all: #don't worry about othersOK yet
        if len(l) > 1:
            ox=[t(v) for v in l[:len(l)-2] if v] #Should probably always give text
            l=ox+[_(' and ').join([t(v) for v in l[len(l)-2:]
                                        if v not in ignore
                                        if v])]
                # for i in range(int(len(output)/2))]
        else:
            l[0]=t(l[0]) #for lists of a single element
        return ', '.join(x for x in l if x not in ignore)
    elif len(l) == 1 or (othersOK == True):
        return l[0]
    elif othersOK == False: #(i.e., with `len(list) != 1`)
        return _('Sorry, something other than one list item found: {list}'
                '\nDid you mean to use "othersOK=True"?').format(list=l)
def t(element):
    if type(element) is str:
        return element
    elif element is None:
        return str(None)
    else:
        try:
            return element.text
        except:
            return _("Apparently you tried to pull text out of a non "
                        "element, and it's not a simple string, either: {element}"
                        ).format(element=element)
def nonspace(x):
    """Return a space instead of None (for the GUI)"""
    if x is not None:
        return x
    else:
        return ' '
def nn(x,perline=False,oneperline=False,twoperline=False):
    """Don't print 'None' in the UI..."""
    if type(x) in (list, tuple, set):
        output=[]
        for y in x:
            output+=[nonspace(y)]
        if perline: #join every other with ', ', then all with '\n'
            return '\n'.join([', '.join([str(v) for v in output[i*perline:i*perline + perline]])
                        for i in range(int(len(output)/perline)+1)])
        elif twoperline: #join every other with ', ', then all with '\n'
            return '\n'.join([', '.join([str(v) for v in output[i*2:i*2 + 2]])
                        for i in range(int(len(output)/2)+1)])
        elif oneperline:
            return '\n'.join([str(i) for i in output])
        else:
            return ' '.join(output)
    else:
        return nonspace(x)
def donothing():
    return _("Doing Nothing!")
def name(x):
    try:
        name=x.__name__ #If x is a function
        return name
    except:
        name=x.__class__.__name__ #If x is a class instance
        return 'class.'+name
def internetconnectionproblemin(x):
    problems=[
            'No route to host',
            'unable to access',
            'Could not resolve host',
            'Could not read from remote repository.'
            ]
    for p in problems:
        if p in x:
            return True
def isinterneturl(x):
    u=['ssh:',
        'https:',
        'http:',
        'git@github.com:'
        ]
    if [i for i in u if i in x if x]:
            return True
def updated(x):
    #put strings that indicate a repo was updated here
    if not uptodate(x) and 'fatal: ' not in x:
        return True
def uptodate(x):
    #These are repo already up to date messages
    u=['Everything up-to-date',
        'Already up to date.'
        ]
    if [i for i in u if i in x if x]:
            return True
def pathseparate(path):
    os=platform.system()
    if os == 'Windows':
        sep=';'
    elif os == 'Linux':
        sep=':'
    else:
        return _("I can't tell what operating system you're running ({os})!").format(os=os)
    return path.split(sep)
def findpath():
    spargs={
            'shell' : False
            }
    try:
        path=os.getenv('PATH')
        #CSIDL_COMMON_DESKTOPDIRECTORY
        #CSIDL_DEFAULT_DESKTOP
        # CSIDL_DESKTOPDIRECTORY
        # CSIDL_DESKTOP
        #subprocess.check_output(['echo',"%PATH%"], **spargs)
        return path
    except Exception as e:
        return _("No path found! ({error})").format(error=e)
def sysexecutableversion():
    # args=[program.python, '--version']
    args=[sys.executable, '--version']
    return stouttostr(subprocess.check_output(args, shell=False))
def openweburl(url):
    webbrowser.open_new(url)
def sysshutdown():
    logsetup.shutdown()
    sys.exit()
def sysrestart(event=None):
    osys=platform.system()
    logsetup.shutdown()
    if osys == 'Linux':
        os.execl(sys.executable, sys.executable, *sys.argv, '--restart')
    elif osys == 'Windows':
        subprocess.run([sys.executable, *sys.argv, '--restart'])
    sys.exit()
if __name__ == '__main__':
    from utilities import logsetup
    log=logsetup.getlog(__name__)
    logsetup.setlevel('DEBUG',log) #for this file


"""Function Decorators"""
def marktime(f,*args,**kwargs):
    def timed(*args,**kwargs):
        start_time=datetime.datetime.now(datetime.UTC)
        r=f(*args,**kwargs)
        name=getattr(f,'__name__',f"of type {f.__class__.__name__}")
        print("Function",name,datetime.datetime.now(datetime.UTC)-start_time)
        return r
    return timed
def callerfn():
    #Not this function, nor the one that called it, but the one that called that
    return inspect.getouterframes(inspect.currentframe())[2].function
def callerfnparent():
    #Not this function, nor the one that called it, but the one that called that
    return inspect.getouterframes(inspect.currentframe())[1].function
def ofromstr(x):
    """This interprets a string as a python object, if possible"""
    """This is needed to interpret [x,y] as a list and {x:y} as a dictionary."""
    try:
        return ast.literal_eval(x)
    except (SyntaxError,ValueError) as e:
        # log.debug("Assuming '{}' is a string ({})".format(x,e))
        return x
def tryrun(cmd):
    try:
        cmd()
    except Exception as e:
        return _("{} command error: {}\n({})").format(cmd.__name__,e,cmd)
def quote(x):
    #does this fail on non-string x?
    if isinstance(x,dict) or isinstance(x,int) or isinstance(x,list):
        return str(x) #don't put brackets around this, just make it a string
    if "'" not in x:
        return "'"+x+"'"
    elif '"' not in x:
        return '"'+x+'"'
    else:
        return _("ˋ{}ˊ contains single and double quotes!").format(x)
def indenteddict(indict):
    outdict={}
    # log.info("working on dict with keys {}".format(indict.keys()))
    for j in indict:
        # log.info("working on {}".format(j))
        if isinstance(indict[j], dict):
            # log.info("printing indented dict for {} key".format(j))
            # config[s][j]='\n'.join(['{'+i+':'+str(v[j][i])+'}'
            #                             for i in v[j].keys()])
            if True in [isinstance(i, dict) for i in indict[j].values()]:
                # log.info("printing double indented dict for {}: {} "
                #             "keys".format(j,indict[j].keys()))
                outdict[j]='{'+',\n'.join(
                    [quote(k)+':{'+',\n\t'.join(
                                        [quote(i)+':'+quote(indict[j][k][i])
                                            for i in indict[j][k]#.keys()
                                            # for k in indict[j].keys()
                                            if i #and i in indict[j][k].keys()
                                        ]
                                                )+'}'
                    for k in indict[j]#.keys()
                    if k #and k in indict[j].keys()
                    # if k
                    ]
                                            )+'}'
                # '\n\t\t'.join(str({i:v[j][k][i]
                #                             for i in v[j][k]}))
            else:
                # log.info(_("printing indented dict for {} key").format(j))
                outdict[j]='{'+',\n'.join([quote(i)+':'+quote(indict[j][i])
                                        for i in indict[j]#.keys()
                                        if i])+'}'
        # elif indict[j]: #this doesn't print "False"
        else:
            # print(_(f"printing unindented dict for {j} key"))
            outdict[j]=str(indict[j]) #don't quote booleans!
    return outdict
def nesteddictadd1key(dict,key):
    if key not in dict:
        dict[key]={}
    return dict[key]
def setnesteddictobjectval(object,dictname,val,*keys,addval=False):
    if not hasattr(object,dictname) or not getattr(object,dictname):
        setattr(object,dictname,{})
    setnesteddictval(getattr(object,dictname),val,*keys,addval=addval)
def setnesteddictval(dictionary,val,*keys,addval=False):
    """dict must already exist as a dictionary object; this just modifies it.
    Include as many key layers as you like,
    put keys in order; dict,v,x,y gives dict[x][y]=v
    with addval, if val is int or list, it is added to value/list already there,
    or assigned if there is no current value.
    """
    if not isinstance(dictionary,dict):
        print(_("setnesteddictval got dictionary of type {}").format(type(dictionary)))
        exit() #This should never happen, would be my fault, and I should know
    dictlist=[] #keep dictionaries at each level in memory
    for n,k in enumerate(keys): #keys may repeat, can't use list.index()
        if dictlist:
            d=dictlist[-1]
        else:
            d=dictionary
        if n-len(keys)+1:
            dictlist.append(nesteddictadd1key(d,k))
        elif addval and k in d:
            # print(f"For keys {keys} adding value {val}")
            if type(val) == type(d[k]) == set:
                d[k]|=val
            elif type(val) == set or type(d[k]) == set:
                raise TypeError(_("you're trying to add {val} ({type(val)}) "
                                f"to {d[k]} ({type(d[k])}), but "
                                "one is a set and the other isn't"))
            else:
                d[k]+=val
        else:
            # print(f"For keys {keys} assigning value {val}")
            d[k]=val
def iteratelistitem(l,item,val,circular=False):
    try:
        initindex=l.index(item)
    except ValueError as e:
        return _("Item {item} not in list {l}, not iterating.")
    if type(val) is int and type(initindex) is int:
        newindex=initindex+val
        if circular:
            newindex=newindex%len(l)
        elif 0 > newindex or newindex >= len(l):
            print(_("requested index out of bounds; not moving."))
            newindex=initindex
        return l[newindex]
    else:
        return (_("problem with iteration value type "
                f"({type(val)}) or index type ({type(initindex)})"))
def open_file(path):
    """Opens a file with the default application in a cross-platform way."""
    import subprocess, os, platform
    
    if platform.system() == 'Darwin':       # macOS
        subprocess.call(('open', path))
    elif platform.system() == 'Windows':    # Windows
        os.startfile(path)
    else:                                   # linux variants
        subprocess.call(('xdg-open', path))
def unlist(l, ignore=[None]):
    from io_put import lift
    if l and isinstance(l[0], lift.et.Element):
        return _("unlist should only be used on text (not node) lists ({list})\n"
                "Element[0] text: {text}").format(list=l,text=l[0].text)
    return firstoflist(l, all=True, ignore=ignore)

if __name__ == '__main__':
    log=logsetup.getlog(__name__)
    # logsetup.setlevel('INFO',log) #for this file
    logsetup.setlevel('DEBUG',log) #for this file
    for s in ["'\"'","'p'"]:
        print(quote(s))
