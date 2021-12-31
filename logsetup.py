#!/usr/bin/env python3
# coding=UTF-8
import datetime
import logging
import lzma
import re
import pathlib
import os
import sys
log = logging.getLogger(__name__) #this is the root; set level in main.py
def shutdown(): #Not sure I'll ever need this...
    logging.shutdown()
class SubLog(logging.Logger):
    """docstring for Log."""
    def __init__(self,loglevel):
        super(SubLog, self).__init__(loglevel)
class Log(logging.Logger): #
    """This class is inefficient, basically a group of sublogs not properly
    under a Root Log. I can't figure out how to subclass and use the root
    hierarchy, but this is working for now."""
    def __init__(self,loglevel=None):
        caller=sys._getframe(1).f_globals['__name__']
        if caller == '__main__':
            caller=pathlib.Path(sys._getframe(1).f_globals['__file__']).stem
        if not loglevel:
            loglevel=log.getEffectiveLevel()
        elif type(loglevel) is str:
            loglevel=loglevel.upper()
        print("Called by {} with level {}".format(caller,loglevel))
        super(Log, self).__init__(caller)
        """This is only supposed to work on its first call"""
        logging.basicConfig(level=loglevel, format='%(message)s')
        """This function needs to run before importing any of my modules, which
        I'd like to have log stuff. So I put it here, so it won't clog up the
        top of main.py"""
        logfile='log_'+datetime.datetime.utcnow().isoformat()[:-16]+'.txt'
        levels=['DEBUG','INFO','WARNING','ERROR','CRITICAL']
        if (loglevel and
                type(loglevel) is not int and
                loglevel.upper() not in levels):
            print("Loglevel: {}".format(loglevel))
            print("Please select one of the following debug levels (that and above "
                "will print):"
                "\nDEBUG:    Detailed information, typically of interest only when "
                "diagnosing problems."
                "\nINFO:     Confirmation that things are working as expected."
                "\nWARNING:  An indication that something unexpected happened, "
                "or indicative of some problem in the near future (e.g. "
                "‘disk space low’). The software is still working as expected."
                "\nERROR:    Due to a more serious problem, the software has not been "
                "able to perform some function."
                "\nCRITICAL: A serious error, indicating that the program itself "
                "may be unable to continue running.")
            exit()
        self.logdir=self.getlogdir()
        self.filename=pathlib.Path.joinpath(self.logdir,logfile)
        if loglevel:
            if type(loglevel) is int:
                self.setLevel(loglevel)
            else:
                self.setLevel(getattr(logging, loglevel.upper()))
        else:
            log.info("No log level specified, staying with default: {}".format(
                    logging.root.level))
        print("Using log level {}".format(logging.root.level))
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
        file = logging.FileHandler(self.filename,mode='w', encoding='utf-8')
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
    def getlogdir(self):
        dir=pathlib.Path.joinpath(pathlib.Path(__file__).parent,'userlogs')
        print("Looking for {}".format(dir))
        if not os.path.exists(dir):
            log.debug("{} not there, making it!".format(dir))
            os.mkdir(dir)
        return dir
    def contents(self,lastlines=0):
        with open(self.filename,'r', encoding='utf-8') as d:
            return d.readlines()[-lastlines:]
    def writelzma(self,filename=None):
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
        compressedurl=pathlib.Path.joinpath(self.logdir,compressed)
        if not filename:
            filename=self.filename
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
