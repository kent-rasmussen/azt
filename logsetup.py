#!/usr/bin/env python3
# coding=UTF-8
import datetime
import logging
def logshutdown(): #Not sure I'll ever need this...
    logging.shutdown()
def logsetup(loglevel):
    """This function needs to run before importing any of my modules, which
    I'd like to have log stuff. So I put it here, so it won't clog up the
    top of main.py"""
    logfile='log_'+datetime.datetime.utcnow().isoformat()[:-16]+'.txt'
    levels=['DEBUG','INFO','WARNING','ERROR','CRITICAL']
    if loglevel.upper() not in levels:
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
    console.setLevel(logging.DEBUG)
    console.setFormatter(simpleformat)
    file = logging.FileHandler(logfile,mode='w', encoding='utf-8')
    file.setLevel(logging.DEBUG)
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
    # test(log)
    return log
