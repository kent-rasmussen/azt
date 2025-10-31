#!/usr/bin/env python3
# coding=UTF-8
import ast
# import logsetup
import datetime
import sys
if __name__ == '__main__':
    try: #Allow this module to be used without translation
        _
    except:
        def _(x):
            return x
    import logsetup
    log=logsetup.getlog(__name__)
    logsetup.setlevel('DEBUG',log) #for this file
    log.info(f"Importing {__name__}")
"""Function Decorators"""
def marktime(f,*args,**kwargs):
    def timed(*args,**kwargs):
        start_time=datetime.datetime.now(datetime.UTC)
        r=f(*args,**kwargs)
        print("Function",f.__class__.__name__,datetime.datetime.now(datetime.UTC)-start_time)
        return r
    return timed
def stouttostr(x):
    # This fn is necessary (and problematic) because not all computers seem to
    # reply to subprocess.check_output with the same kind of data. I have even
    # seen a computer say it was using unicode, but not return unicode
    # data (I think because it was replacing translated text, but didn't
    # replace the same encoding). Another dumb thing that I need to account for.
    if type(x) is str:
        return x.strip()
    if not sys.stdout.encoding:
        log.error("I can't tell the terminal's encoding, sorry!")
    else:
        try:
            return x.decode(sys.stdout.encoding,
                            errors='backslashreplace').strip()
        except Exception as e:
            #if the computer doesn't know what encoding it is actually using,
            # this should give us some info to debug.
            log.error(_("Can't decode this (in {}; {}):"
                        ).format(sys.stdout.encoding, e))
            log.error(x)
    return x #not sure if this is a good idea, but this should probably raise...
def ofromstr(x):
    """This interprets a string as a python object, if possible"""
    """This is needed to interpret [x,y] as a list and {x:y} as a dictionary."""
    try:
        return ast.literal_eval(x)
    except (SyntaxError,ValueError) as e:
        # log.debug("Assuming ‘{}’ is a string ({})".format(x,e))
        return x
def tryrun(cmd):
    try:
        cmd()
    except Exception as e:
        text=_("{} command error: {}\n({})").format(cmd.__name__,e,cmd)
        log.error(text)
def quote(x):
    #does this fail on non-string x?
    if isinstance(x,dict) or isinstance(x,int) or isinstance(x,list):
        return str(x) #don't put brackets around this, just make it a string
    if "'" not in x:
        return "'"+x+"'"
    elif '"' not in x:
        return '"'+x+'"'
    else:
        log.error("Looks like ˋ{}ˊ contains single and double quotes!".format(x))
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
        try:
            log.info(f"The dictionary at {object}.{dictname} doesn't seem "
                    "to exist, or is null; creating.")
        except NameError:
            print(f"The dictionary at {object}.{dictname} doesn't seem "
                    "to exist, or is null; creating.")
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
        print(f"setnesteddictval got dictionary of type {type(dictionary)}")
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
                raise TypeError(f"you're trying to add {val} ({type(val)}) "
                                f"to {d[k]} ({type(d[k])}), but "
                                "one is a set and the other isn't")
            else:
                d[k]+=val
        else:
            # print(f"For keys {keys} assigning value {val}")
            d[k]=val
def iteratelistitem(l,item,val,circular=False):
    try:
        initindex=l.index(item)
    except ValueError as e:
        return f"Item {item} not in list {l}, not iterating."
    if type(val) is int and type(initindex) is int:
        newindex=initindex+val
        if circular:
            newindex=newindex%len(l)
        elif 0 > newindex or newindex >= len(l):
            print("requested index out of bounds; not moving.")
            newindex=initindex
        return l[newindex]
    else:
        return ("problem with iteration value type "
                f"({type(val)}) or index type ({type(initindex)})")
if __name__ == '__main__':
    log=logsetup.getlog(__name__)
    # logsetup.setlevel('INFO',log) #for this file
    logsetup.setlevel('DEBUG',log) #for this file
    quote("'\"'")
