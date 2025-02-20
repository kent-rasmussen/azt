#!/usr/bin/env python3
# coding=UTF-8
import ast
import logsetup
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
        ErrorNotice(text,title=_("{} command error!").format(cmd.__name__))
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
        elif indict[j]:
            # log.info(_("printing unindented dict for {} key").format(j))
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
def setnesteddictval(dict,val,*keys,addval=False):
    """Include as many key layers as you like,
    put keys in order; dict,v,x,y gives dict[x][y]=v
    with addval, if val is int or list, it is added to value/list already there,
    or assigned if there is no current value.
    """
    dictlist=[] #keep dictionaries at each level in memory
    for n,k in enumerate(keys): #keys may repeat, can't use list.index()
        if dictlist:
            d=dictlist[-1]
        else:
            d=dict
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
