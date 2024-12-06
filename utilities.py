#!/usr/bin/env python3
# coding=UTF-8
import ast
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
