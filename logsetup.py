#!/usr/bin/env python3
# coding=UTF-8
import datetime
import logging
import lzma
import re
import pathlib
import os
import sys
"""
DEBUG (10):    Detailed information, typically of interest only when
                diagnosing problems.
INFO (20):     Confirmation that things are working as expected.
WARNING (30):  An indication that something unexpected happened,
                or indicative of some problem in the near future (e.g.
                ‘disk space low’). The software is still working as expected.
ERROR (40):    Due to a more serious problem, the software has not been
                  able to perform some function.
CRITICAL (50): A serious error, indicating that the program itself
                  may be unable to continue running.
"""
def shutdown():
    logging.shutdown()
def getlog(name):
    return logging.getLogger(name)
def setlevel(loglevel,thislog=None):
    if not thislog:
        thislog=logging.root
    thislog.setLevel(loglevel)
    log.info("Current {} logger level: {}".format(thislog,thislog.level))
def getlogdir():
    """Can't do this in file, which depends on this..."""
    logdir=pathlib.Path.joinpath(pathlib.Path(__file__).parent,'userlogs')
    if not os.path.exists(logdir):
        log.debug("{} not there, making it!".format(logdir))
        os.mkdir(logdir)
    else:
        log.debug("Found {}".format(logdir))
    return logdir
def getlogfilename():
    for h in [i for i in logging.root.handlers if isinstance(i,logging.FileHandler)]:
        return h.baseFilename
def dorootloghandlers(self):
    logfile='log_'+datetime.datetime.utcnow().isoformat()[:-16]+'.txt'
    logdir=getlogdir()
    filename=pathlib.Path.joinpath(logdir,logfile)
    simpleformat = logging.Formatter('%(message)s')
    fullformat = logging.Formatter('%(asctime)s: %(name)s: %(levelname)s '
                                    '- %(message)s')
    timelessformat = logging.Formatter('%(name)s: %(levelname)s: '
                                    '%(message)s')
    rootformat = logging.Formatter('%(asctime)s: '
                                    # '- %(name)s '
                                    '%(levelname)s: '
                                    '%(message)s')
    console = logging.StreamHandler()
    console.setLevel(0) #Let the loglevel determine what to show
    console.setFormatter(simpleformat)
    file = logging.FileHandler(filename,mode='w', encoding='utf-8')
    file.setLevel(0) #Let the loglevel determine what to show
    file.setFormatter(timelessformat)
    self.addHandler(console)
    self.addHandler(file)
def test(self):
    self.debug("Debug!")
    self.info("Info!")
    self.warning("Warning!")
    self.error("Error!")
    self.exception("Exception!") #this expects exception info
    self.critical("Critical!")
def contents(self,lastlines=0):
    with open(getlogfilename(),'r', encoding='utf-8') as d:
        return d.readlines()[-lastlines:]
def writelzma(filename=None):
    try:
        import lzma
        log.debug("LZMA imported fine.")
    except ImportError:
        log.error("LZMA import error.")
        from backports import lzma
    """This writes changes back to XML."""
    """When this goes into production, change this:"""
    compressed='log_'+datetime.datetime.utcnow().isoformat()[:-7]+'Z'+'.xz'
    compressed=re.sub(':','-',compressed)
    logdir=getlogdir()
    compressedurl=pathlib.Path.joinpath(logdir,compressed)
    if not filename:
        filename=getlogfilename()
    with open(filename,'r', encoding='utf-8') as d:
        log.debug("Logfile {} opened.".format(filename))
        with lzma.open(compressedurl, "wt", encoding='utf-8') as f:
            log.debug("LZMA file {} opened.".format(compressedurl))
            data=d.read()
            log.debug("Logfile {} read (this and following will not be written "
                    "to compressed log file).".format(filename))
            f.write(data)
            log.debug("LZMA file {} written.".format(compressed))
            f.close()
            log.debug("LZMA file {} closed.".format(compressed))
            d.close()
            log.debug("Logfile {} closed (ready to return LZMA file).".format(
                                                                    filename))
        with lzma.open(compressedurl) as ch:
            data2 = ch.read().decode("utf-8")
            log.debug("LZMA file {} decompressed.".format(compressed))
            ch.close()
        if data2 == data:
            log.debug("Data before compression the same as after "
                        "decompression.")
    return compressedurl
log = logging.getLogger() #this is the root; set level with setlevel
setlevel('INFO') #If not set elsewhere
dorootloghandlers(log)
