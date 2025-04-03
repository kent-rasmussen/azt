#!/usr/bin/env python3
# coding=UTF-8
from xml.etree import ElementTree as ET
import logsetup
#This should not be imported with from xmletfns import *
log=logsetup.getlog(__name__)
import file
import urllib
import datetime
def readxmltext(text):
    return ET.fromstring(text)
def readxml(filename):
    tree=ET.parse(filename)
    nodes=tree.getroot()
    return tree,nodes
def iselement(n):
    return isinstance(n,ET.Element)
def prettyprint(node):
    log=logsetup.getlog(__name__) #fn is imported as *, no not global log
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
                    else str(node.text)+' ('+str(type(node.text))+')'
                    )
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
    log=logsetup.getlog(__name__) #fn is imported as *, no not global log
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
class TreeParsed(object):
    def __init__(self, lift):
        self=Tree(lift).parsed
        log.info(self.glosslang)
        Tree.__init__(self, db, guid=guid)
class XML(object): #fns called outside of this class call self.nodes here.
    """The job of this class is to expose the XML as python object
    attributes. Nothing more, not thing else, should be done here."""
    def __init__(self, filename, tostrip=False): #may need tostrip for LIFT
        self.debug=False
        self.filename=filename #lift_file.liftstr()
        self.logfile=filename+".changes"
        self.urls={} #store urls generated
        """Problems reading a valid file are dealt with elsewhere"""
        try:
            self.read() #load and parse the XML file.
            log.info("XML read OK")
        except:
            raise BadParseError(self.filename)
        backupbits=[filename,'_',
                    datetime.datetime.utcnow().isoformat()[:-16], #once/day
                    '.txt']
        self.backupfilename=''.join(backupbits)
        # self.diagnostics()
        log.info("XML initialization done.")
    def get(self, *args,**kwargs):
        log.info("Using my get")
        ET.get(self,*args,**kwargs)
    def diagnostics(self):
        prettyprint(self.nodes)
    def read(self):
        """this parses the xml file into an entire ElementTree tree,
        for reading or writing the XML file."""
        log.info("Reading XML file: {}".format(self.filename))
        self.tree,self.nodes=readxml(self.filename)
        # self.tree=ET.parse(self.filename)
        # self.nodes=self.tree.getroot()
        log.info("Done reading XML file.")
        """This returns the root node of an ElementTree tree (the entire
        tree as nodes), to edit the XML."""
if __name__ == '__main__':
    f='/home/kentr/Assignment/Production/CACBLD/Emic First Phonology_paper.xml'
    getincluded(f)
