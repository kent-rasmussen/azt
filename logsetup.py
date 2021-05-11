#!/usr/bin/env python3
# coding=UTF-8
import datetime
import logging
import lzma
import re
log = logging.getLogger(__name__)

def logshutdown(): #Not sure I'll ever need this...
    logging.shutdown()
def logsetup(loglevel):
    """This function needs to run before importing any of my modules, which
    I'd like to have log stuff. So I put it here, so it won't clog up the
    top of main.py"""
    logfile='log_'+datetime.datetime.utcnow().isoformat()[:-16]+'.txt'
    levels=['DEBUG','INFO','WARNING','ERROR','CRITICAL']
    if (type(loglevel) is not int) and (loglevel.upper() not in levels):
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
    log = logging.getLogger()
    log.filename=logfile
    if type(loglevel) is int:
        log.setLevel(loglevel)
    else:
        log.setLevel(getattr(logging, loglevel.upper()))
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
    file = logging.FileHandler(logfile,mode='w', encoding='utf-8')
    file.setLevel(0) #Let the loglevel determine what to show
    file.setFormatter(timelessformat)
    log.addHandler(console)
    log.addHandler(file)
    def test(log):
        log.debug("Debug!")
        log.info("Info!")
        log.warning("Warning!")
        log.error("Error!")
        log.exception("Exception!") #this expects exception info
        log.critical("Critical!")
    return log
def logwritelzma(filename):
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
    with open(filename,'r') as d:
        log.debug("Logfile {} opened.".format(filename))
        with lzma.open(compressed, "wt") as f:
            log.debug("LZMA file {} opened.".format(compressed))
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
        with lzma.open(compressed) as ch:
            data2 = ch.read().decode("utf-8")
            log.debug("LZMA file {} decompressed.".format(compressed))
        if data2 == data:
            log.debug("Data before compression the same as after "
                        "decompression.")
        else:
            decompressed=filename+'_decompressed'
            log.error("Data before compression NOT the same as after "
                    "decompression; writing decompressed back to file {}!"
                    "".format(decompressed))
            with open(decompressed,'w') as chd:
                chd.write(data2)
                log.debug("Decompressed file {} written to disk."
                    "".format(decompressed))
    return compressed
