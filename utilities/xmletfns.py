#!/usr/bin/env python3
# coding=UTF-8
from xml.etree import ElementTree as ET
from utilities import logsetup
#This should not be imported with from xmletfns import *
log=logsetup.getlog(__name__)
import urllib.parse
import datetime
from utilities.i18n import _
ElementTree=ET.ElementTree
Element=ET.Element
parse=ET.parse
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
        log.info(_("didn’t prettyprint {}").format(node))
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
        iterateforincludes(child,ns,results)
    return results
def getincluded(filename,iterated=False):
    from utilities import file
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
        log.info(_("Found reference to filename {}").format(r))
        getincluded(r)
class BadParseError(Exception):
    """Mirrors io_put.lift.BadParseError (importing lift here would be
    circular — lift imports this module)."""
class XML(object): #fns called outside of this class call self.nodes here.
    """The job of this class is to expose the XML as python object
    attributes. Nothing more, not thing else, should be done here."""
    def __init__(self, filename, tostrip=False): #may need tostrip for LIFT
        self.debug=False
        self.filename=filename #lift_file.liftstr()
        self.urls={} #store urls generated
        """Problems reading a valid file are dealt with elsewhere"""
        try:
            self.read() #load and parse the XML file.
        except Exception:
            raise BadParseError(self.filename)
        # ONE PER RUN, AND NO COLONS. The time is deliberate — these are
        # per-run backups, not daily ones, whatever the old `#once/day`
        # comment said. What was not deliberate is the FORMAT: it was built
        # by `isoformat()[:-16]`, a slice that only means anything at one
        # exact string length, and what reached the disk carried a clock
        # time. A clock time has colons, and Windows forbids them in
        # filenames, so the backup simply did not get written there:
        #
        #   There was a problem writing to partial file:
        #   ...\nm1.lift_ 16:31:48.374013+00:00.txt.part
        #   ([Errno 22] Invalid argument)
        #
        # — Kim's Windows 11 machine, 2026-09-24. `strftime` says what it
        # means, keeps per-run precision to the second, and cannot produce a
        # character any of the three platforms rejects.
        backupbits=[filename,'_',
                    datetime.datetime.now(datetime.timezone.utc
                                          ).strftime('%Y-%m-%dT%H%M%S'),
                    '.txt'] #one per run
        self.backupfilename=''.join(backupbits)
        # self.diagnostics()
        log.info(_("XML initialization done."))
    def get(self, *args,**kwargs):
        ET.get(self,*args,**kwargs)
    def diagnostics(self):
        prettyprint(self.nodes)
    def read(self):
        """this parses the xml file into an entire ElementTree tree,
        for reading or writing the XML file."""
        log.info(_("Reading XML file: {}").format(self.filename))
        self.tree,self.nodes=readxml(self.filename)
        # self.tree=ET.parse(self.filename)
        # self.nodes=self.tree.getroot()
        """This returns the root node of an ElementTree tree (the entire
        tree as nodes), to edit the XML."""
if __name__ == '__main__':
    f='/home/kentr/Assignment/Production/CACBLD/Phonology First_paper.xml'
    getincluded(f)
