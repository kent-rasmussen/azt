#!/usr/bin/env python3
# coding=UTF-8
from xml.etree import ElementTree as ET
import logsetup
log=logsetup.getlog(__name__)
import file
import urllib

def readxml(filename):
    tree=ET.parse(filename)
    nodes=tree.getroot()
    return tree,nodes
def iselement(n):
    return isinstance(n,ET.Element)
def prettyprint(node):
    # This fn is for seeing the Element contents before writing them (in case of
    # ElementTree errors that aren't otherwise understandable).
    if not isinstance(node,ET.Element):
        log.info("didn't prettyprint {}".format(node))
        return
    t=0
    lines=[]
    def do(node,t):
            line="{}{} {}: {}".format('\t'*t,node.tag,node.attrib,
                    "" if node.text is None
                    or set(['\n','\t',' ']).issuperset(node.text)
                    else node.text)
            lines.append(line)
            log.info(line)
            t=t+1
            for child in node:
                do(child,t)
            t=t-1
    do(node,t)
    return '\n'.join(lines)
def getxmlns(nodes):
    xmlns=set()
    results=nodes.findall(".")
    for r in results:
        n=r.get("xmlns:xi")
        if n:
            xmlns+=n
    return xmlns
def iterateforincludes(node,ns,results=[]):
    results+=node.findall("xi:include",ns)
    # log.info("{} ({}): {}".format(node,len(results),results))
    for child in node:
        if child: #i.e., has children
            iterateforincludes(child,ns,results)
    return results
def getincluded(filename,iterated=False):
    # Each new files starts here
    filename=urllib.parse.unquote(str(filename), encoding='utf-8', errors='replace')
    # log.info("Looking at filename {}".format(filename))
    t,n=readxml(filename)
    # ns=getxmlns(n)
    dir=str(file.getfilenamedir(filename))
    # log.info("In filename dir {}".format(dir))
    ns={'xi':"http://www.w3.org/2001/XInclude"}
    results=iterateforincludes(n,ns,[])
    # log.info("{}: {}".format(len(results),results))
    for r in results:
        r=file.getdiredrelURL(dir,r.get('href'))
        log.info("Found reference to filename {}".format(r))
        getincluded(r)
if __name__ == '__main__':
    f='/home/kentr/Assignment/Production/CACBLD/Emic First Phonology_paper.xml'
    getincluded(f)
