#!/usr/bin/env python3
# coding=UTF-8
"""file is imported lazily inside functions to avoid circular import."""

import logging
import logging.handlers
import tarfile
import datetime
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
    log.info("shutting down logging")
    logging.shutdown()
def getlog(name):
    return logging.getLogger(name)
def setlevel(loglevel,thislog=None):
    if not thislog:
        thislog=logging.root
    thislog.setLevel(loglevel)
    # log.info("Current {} logger level: {}".format(thislog,thislog.level))
def getlogfilename():
    for h in [i for i in logging.root.handlers if isinstance(i,logging.FileHandler)]:
        return h.baseFilename
def logformat(x):
    formats={'simpleformat':logging.Formatter('%(message)s'),
                'fullformat':logging.Formatter('%(asctime)s: %(name)s: '
                                    '%(levelname)s - %(message)s'),
                'timelessformat':logging.Formatter('%(name)s: %(levelname)s: '
                                    '%(message)s'),
                'rootformat':logging.Formatter('%(asctime)s: '
                                    # '- %(name)s '
                                    '%(levelname)s: '
                                    '%(message)s')
            }
    return formats[x]
def dorootloghandlers(self):
    console = logging.StreamHandler()
    console.setLevel(0) #Let the loglevel determine what to show
    console.setFormatter(logformat('simpleformat'))
    self.addHandler(console)
    tryfilehandler(self)
def tryfilehandler(self,lessiso=16):
    from utilities import file as _file
    logfile='log_'+datetime.datetime.utcnow().isoformat()[:-lessiso]+'.txt'
    filename=pathlib.Path.joinpath(_file.getlogdir(),logfile)
    try:
        handler = logging.handlers.RotatingFileHandler(filename, mode='w',
                                                    encoding='utf-8',
                                                    maxBytes=500000,
                                                    backupCount=5)
        handler.doRollover()# start at the beginning of a file
        handler.setLevel(0) #Let the loglevel determine what to show
        handler.setFormatter(logformat('timelessformat'))
        self.addHandler(handler)
    except PermissionError as e:
        log.info(f"Logfile permission problem ({e}); trying again.")
        tryfilehandler(self,lessiso=lessiso-3)
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
    from utilities import file as _file
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
    logdir=_file.getlogdir()
    compressedurl=logdir.joinpath(compressed)
    if not filename:
        filename=getlogfilename()
    log.info("Using filename {}".format(filename))
    filenames=list(logdir.glob(pathlib.Path(filename).name+'*'))
    f=tarfile.open(name=str(compressedurl)+'.tar.xz', mode='x:xz',
                    encoding='utf-8', preset=9,
                    debug=3
                    ) #as f:
    for fn in filenames:
        # log.info("Compressing file {}".format(fn))
        try:
            f.add(fn,arcname=pathlib.Path(fn).name)
            # log.info("Compressed file {}".format(fn))
        except Exception as e:
            log.info(e)
    log.info("Compressed files: {}".format(f.getnames()))
    f.close()
    """Probably can cut from here, once I see this is working on windows"""
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
if __name__ == "__main__":
    loglevel=10
    log=getlog('root') #not ever a module
    setlevel(loglevel)
    log.info("Hey, this is something.")
    writelzma()
    shutdown()
