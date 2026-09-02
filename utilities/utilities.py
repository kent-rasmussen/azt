#!/usr/bin/env python3
# coding=UTF-8
import ast
import json
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

class Options:
    """A tiny attribute bag with row/column ('r'/'c'/'col') aliases and
    next()/prev() cursors — used to thread grid position through a window
    builder. Lives here (not main.py) so frontend builders can import it
    without a circular dependency on main."""
    def alias(self,o):
        return self.odict.get(o,o)
    def next(self,o):
        o=self.alias(o)
        setattr(self,o,getattr(self,o)+1)
    def prev(self,o):
        o=self.alias(o)
        setattr(self,o,getattr(self,o)-1)
    def get(self,o):
        o=self.alias(o)
        return getattr(self,o)
    def __init__(self,**kwargs):
        self.odict={'col':'column','c':'column',
                    'r':'row'
                    }
        for arg in kwargs:
            setattr(self,self.alias(arg),kwargs[arg])

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
def nowruntime():
    """Aware-UTC now, for run-duration deltas (start_time=nowruntime();
    … nowruntime()-start_time)."""
    return datetime.datetime.now(datetime.timezone.utc)
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
                '\nDid you mean to use “othersOK=True”?').format(list=l)
def t(element):
    if type(element) is str:
        return element
    elif element is None:
        return str(None)
    else:
        try:
            return element.text
        except AttributeError:
            return _("Apparently you tried to pull text out of a non "
                        "element, and it’s not a simple string, either: {element}"
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
    except AttributeError:
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
        return _("I can’t tell what operating system you’re running ({os})!").format(os=os)
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
def spawn_successor(reason=None):
    """Launch the successor and RETURN, without exiting or shutting down logging.

    The other half of a confirmed restart: `sysrestart` hands over and dies, so
    nothing is left to notice a successor that never comes up. This lets the
    caller keep its UI and its log, watch for the successor to signal that it is
    up, and recover if it does not. Returns the Popen handle, or None if the
    launch itself failed (in which case the caller still has a working app).

    ALWAYS Popen, on every platform. `os.execl` cannot be used here by
    definition — it replaces the process image, so there would be no caller left
    to wait. That also retires the last reason Linux was on exec at all
    (level 3 of restart_recovery_handshake), and it hands over
    AZT_PREDECESSOR_PIDS the way the Windows branch always has, which is what
    keeps the successor's duplicate gate from counting us.
    """
    thislog=logsetup.getlog(__name__)
    try:
        from utilities import restartmark
        restartmark.mark(reason=reason)
    except Exception as e:
        thislog.info("restart marker skipped: %s",e)
    try:
        env=dict(os.environ)
        prior=[p for p in env.get('AZT_PREDECESSOR_PIDS','').split(',') if p]
        env['AZT_PREDECESSOR_PIDS']=','.join((prior+[str(os.getpid())])[-8:])
        argv=[a for a in sys.argv if a != '--restart']
        child=subprocess.Popen([sys.executable, *argv, '--restart'], env=env)
        thislog.info("successor launched: pid %s (reason: %s)",child.pid,reason)
        return child
    except Exception:
        thislog.exception("could not launch successor")
        return None
def sysrestart(event=None,reason=None):
    """Hand over to a fresh copy and exit, WITHOUT waiting to be told it came up.

    The unconfirmed restart, for callers that only need to go: menu buttons, the
    branch switches, the VCS pages. `App.restart` is the CONFIRMED one — it holds
    a "Restarting…" dialog and waits for the successor's signal (see
    `spawn_successor` and `App._confirm_restart`), which is what a caller wants
    if a failure to come back would leave the user stranded.

    ONE PATH FOR EVERY PLATFORM (level 3 of restart_recovery_handshake), by
    delegating to `spawn_successor`, which is already that path. What this
    replaces:
      - `os.execl` on Linux. Unrecoverable by construction — the process image is
        replaced, so nothing survives to notice a successor that never starts —
        and already the odd one out, since `py_modules.ensure_venv` has used
        Popen everywhere all along. It also PRESERVED THE PID, which made the
        predecessor and successor indistinguishable by pid (observed 2026-09-01).
      - A `Windows`-only Popen branch, whose `AZT_PREDECESSOR_PIDS` handover was
        therefore Windows-only too. That handover is now REQUIRED on Linux as
        well: with Popen the predecessor lingers, and without the pid list the
        successor's duplicate gate can count it. It was never needed under exec
        because there was no predecessor left to count.
      - **A silent no-op on macOS.** `osys` matched neither branch, so a restart
        on Darwin fell through to `sys.exit()` — the app simply quit and never
        came back. Nobody has hit it, but it was there.

    If the launch FAILS we do not exit: an app that is still working beats an app
    that quit into nothing, which is the whole lesson of this item.
    """
    child=spawn_successor(reason=reason) #marks the breadcrumb, then launches
    if child is None:
        logsetup.getlog(__name__).error("restart aborted: could not launch a "
                "successor. Staying up — this copy still works.")
        return
    logsetup.shutdown()
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
def _tuplize(x):
    """Lists (and lists of lists) → tuples, recursively; anything else as-is.

    JSON has no tuple, so a decoded affix set comes back as nested LISTS — and
    the parser's Catalog uses the affix set as a Counter KEY
    (`Counter([affixes[1]])`), which requires it to be hashable. Without this
    every lookup silently misses, and an unhashable-type error is the LUCKY
    outcome."""
    if isinstance(x,(list,tuple)):
        return tuple(_tuplize(i) for i in x)
    return x
def affixset_to_str(afxtuple):
    """Serialise an affix set for storage in a LIFT `<trait>` value.

    JSON, not `str(tuple)`. The repr was the whole problem: when an affix is `'`,
    Python switches its quoting to `"` — and that value goes into a `"`-delimited
    XML attribute (Kent 2026-08-26, from a production lexicon that stopped being
    well-formed). ElementTree escapes it correctly, so AZT's own writer survived
    it, but nothing about `repr` is a defined interchange format and only
    `literal_eval` can read it back.

    JSON's own quotes become `&quot;` in the attribute — noisier to read raw, and
    deliberately accepted: Kent 2026-08-26, "most people can't read XML anyway…
    any time this information is human facing the escaping would be presented
    appropriately, so the simpler correct version is best"."""
    return json.dumps(afxtuple)
def affixset_from_str(s):
    """Read an affix set back, accepting BOTH formats — indefinitely.

    Field lexicons hold `str(tuple)` values written before this changed, so JSON
    first, then the old `ofromstr` (`ast.literal_eval`) path. Returns tuples
    either way (see `_tuplize`).

    THE FALLBACK IS LOAD-BEARING, NOT TRANSITIONAL — do not remove it once
    "everything has been migrated", because nothing migrates anything. There is
    no conversion pass: a trait is only rewritten as JSON when its sense is
    re-parsed, so a lexicon holds BOTH formats indefinitely, and a file may still
    be handed a `str(tuple)` value years from now. Verified on real data
    2026-08-27: `(('', ''), ('', 'z'))` and `[["", ""], ["'", "'"]]` sat in one
    file and both read.

    Never raises: a value that is neither is handed back as-is. The whole point
    of this change is that a malformed value must not take down a load."""
    if not isinstance(s,str):
        return _tuplize(s)
    try:
        return _tuplize(json.loads(s))
    except Exception:
        pass #not JSON: an older file, or something else entirely
    return _tuplize(ofromstr(s))
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
        # internal invariant: callers must pass a dict
        raise TypeError(_("setnesteddictval got dictionary of type {}").format(type(dictionary)))
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
                raise TypeError(_("you’re trying to add {val} ({vtype}) "
                                "to {dk} ({dktype}), but "
                                "one is a set and the other isn’t").format(
                                    val=val,vtype=type(val),
                                    dk=d[k],dktype=type(d[k])))
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
                "({vtype}) or index type ({itype})").format(
                    vtype=type(val),itype=type(initindex)))
def open_file(path):
    """Opens a file with the default application in a cross-platform way."""
    import subprocess, os, platform
    
    # Never BLOCK the UI thread on the viewer (2026-07-13): xdg-open can sit
    # on a desktop portal for a long time; Popen dispatches and returns.
    if platform.system() == 'Darwin':       # macOS
        subprocess.Popen(('open', path))
    elif platform.system() == 'Windows':    # Windows
        os.startfile(path)
    else:                                   # linux variants
        subprocess.Popen(('xdg-open', path))
def mailto_configured():
    """Is a mail client registered for mailto:? True / False / None (unknown).

    ASKED, NOT ATTEMPTED, and that is the point. The first version of this
    inferred the answer from what happened when it dispatched the URL, and on
    Linux that inference is simply WRONG (Kent 2026-09-02, watching a user click
    "send log": the folder opened, no mail client appeared, and nothing was
    said). xdg-open does document exit 3 as "no application found", but in a
    live desktop session it delegates to `gio open`/kde-open/etc., and those
    exit 0 whether or not anything handled the scheme — so the caller was told
    "a client took it" and stayed quiet. Exit codes describe the launcher, not
    the handler.

    Asking is also better placed in time: the answer arrives BEFORE the click
    appears to do nothing, instead of after a dispatch that may sit on a desktop
    portal for thirty seconds.

      * Linux — `xdg-mime query default x-scheme-handler/mailto` names the
        .desktop file, and prints nothing when there is no handler. This is the
        registration itself, which is what we asked about.
      * Windows — the HKEY_CLASSES_ROOT\\mailto\\shell\\open\\command key IS the
        association; reading it needs no subprocess and cannot be slow. (Its
        absence is what makes os.startfile raise WinError 1155.)
      * macOS — no cheap query without pyobjc, so None: `open` remains the only
        real test, and open_mailto still reports its exit code.

    None means "say nothing" everywhere: a false "you have no email program" is
    worse than silence, because it sends the user off to configure something
    that already works."""
    thislog=logsetup.getlog(__name__)
    osys=platform.system()
    try:
        if osys == 'Windows':
            import winreg
            try:
                with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT,
                            r'mailto\shell\open\command') as k:
                    cmd=winreg.QueryValueEx(k,'')[0]
                return bool(str(cmd).strip())
            except FileNotFoundError:
                thislog.info("no mailto: handler registered (no HKCR\\mailto)")
                return False
        if osys == 'Darwin':
            return None
        r=subprocess.run(['xdg-mime','query','default',
                    'x-scheme-handler/mailto'],capture_output=True,timeout=15)
        if r.returncode != 0:
            thislog.info("xdg-mime query failed ({}): {}".format(
                        r.returncode,r.stderr[:200]))
            return None #xdg-utils missing or broken: not an answer about mail
        handler=r.stdout.decode('utf-8','replace').strip()
        if not handler:
            thislog.info("no mailto: handler registered (xdg-mime says none)")
            return False
        thislog.info("mailto: handler is {}".format(handler))
        return True
    except Exception as e:
        thislog.info("could not ask about the mailto: handler ({})".format(e))
        return None
def open_mailto(url,on_result=None):
    """Hand a mailto: URL to the mail client, and REPORT whether one took it.

    Ask mailto_configured() FIRST — see there for why this function's exit codes
    cannot answer "is there a mail client" on Linux. What is left here is the
    dispatch, plus the one platform where the attempt IS the only test:

      * Windows — os.startfile raises OSError (WinError 1155, "No application
        is associated…") when no handler is registered. Precise.
      * macOS — `open` exits nonzero when it cannot handle the URL. This is the
        only signal available there, since mailto_configured() returns None.
      * Linux — exit 3 is documented as "no application found" and is honoured
        when it appears, but 0 means only that the launcher ran, NOT that
        anything handled the URL, so 0 is reported as unknown rather than True.

    Runs OFF THE CALLING THREAD, because xdg-open can sit on a desktop portal
    for a long time and this must never block the UI — the reason open_file
    dispatches with Popen rather than run. `on_result(ok)` is called with True
    (a client took it), False (none is configured — tell the user), or None
    (cannot tell; say nothing, since a false alarm here is worse than silence).

    on_result RUNS ON THE WORKER THREAD, so it must not touch a widget: Tk is
    main-thread-only, and building a window from here is how a notice silently
    never appears (or the interpreter crashes). Marshal with root.after()."""
    import threading
    thislog=logsetup.getlog(__name__)
    def _work():
        ok=None
        try:
            osys=platform.system()
            if osys == 'Windows':
                try:
                    os.startfile(url)
                    ok=True
                except OSError as e:
                    thislog.info("no mail client for mailto: ({})".format(e))
                    ok=False
            elif osys == 'Darwin':
                r=subprocess.run(['open',url],capture_output=True,timeout=30)
                ok=(r.returncode == 0)
            else:
                r=subprocess.run(['xdg-open',url],capture_output=True,timeout=30)
                if r.returncode == 3: #documented: no application found
                    ok=False
                elif r.returncode == 0:
                    # NOT True. In a desktop session xdg-open delegates to `gio
                    # open`/kde-open, which exit 0 regardless of whether the
                    # scheme was handled — the fault that made a missing mail
                    # client silent (Kent 2026-09-02). mailto_configured() is
                    # the one that can answer this on Linux.
                    ok=None
                else:
                    #1 syntax, 2 file not found, 4 action failed — a handler may
                    #well exist and have failed for another reason, so don't
                    #claim "not configured".
                    thislog.info("xdg-open returned {} for mailto:".format(
                                r.returncode))
                    ok=None
        except Exception as e:
            thislog.info("could not dispatch mailto: ({})".format(e))
            ok=None
        if on_result:
            try:
                on_result(ok)
            except Exception:
                thislog.exception("mailto result handler failed")
    threading.Thread(target=_work,daemon=True,name='mailto').start()
def reveal_file(path):
    """Open the containing folder with `path` SELECTED, where the OS can.

    Not open_file(): that launches the file in its default application, which
    for a .tar.xz means an archive viewer, and the user still cannot find the
    file to attach it. What they need is the folder open with the thing
    highlighted, so attaching is one drag with no searching.

    This exists because a mailto: link CANNOT attach a file — RFC 6068 lists the
    headers a handler may honour and says attachment parameters must not be,
    since otherwise any web page could make a mail client exfiltrate a local
    file. So the error page can never hand the log over by itself, and "the file
    is at <path>" is not good enough for a field user (Kent 2026-09-02: "I can't
    count on people finding it on their own"). Highlighting it is the closest an
    app can get.

    Never blocks: xdg-open can sit on a desktop portal for a long time, so this
    dispatches and returns, as open_file does."""
    thislog=logsetup.getlog(__name__)
    p=os.path.abspath(str(path))
    osys=platform.system()
    try:
        if osys == 'Windows':
            # /select, needs the comma and NO space, and the path unquoted-ish;
            # explorer returns nonzero even on success, so don't check it.
            subprocess.Popen(['explorer','/select,{}'.format(p)])
            return True
        if osys == 'Darwin':
            subprocess.Popen(['open','-R',p]) # -R = reveal in Finder
            return True
        # Linux: no portable "select". Try the freedesktop file-manager
        # interface first (nautilus/dolphin/nemo implement ShowItems and DO
        # highlight), and fall back to opening the folder.
        try:
            subprocess.Popen(['dbus-send','--session','--print-reply',
                    '--dest=org.freedesktop.FileManager1',
                    '/org/freedesktop/FileManager1',
                    'org.freedesktop.FileManager1.ShowItems',
                    'array:string:file://{}'.format(p),'string:'],
                    stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            return True
        except Exception:
            subprocess.Popen(['xdg-open',os.path.dirname(p)])
            return True
    except Exception as e:
        thislog.info("could not reveal {}: {}".format(p,e))
        return False
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
