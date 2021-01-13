#!/usr/bin/env python3
# coding=UTF-8
import datetime
import logging
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
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, loglevel.upper()))
    simpleformat = logging.Formatter('%(message)s')
    fullformat = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s '
                                    '- %(message)s')
    rootformat = logging.Formatter('%(asctime)s '
                                    # '- %(name)s '
                                    '- %(levelname)s '
                                    '- %(message)s')
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    console.setFormatter(simpleformat)
    file = logging.FileHandler(logfile,mode='w', encoding='utf-8')
    file.setLevel(logging.DEBUG)
    file.setFormatter(fullformat)
    logger.addHandler(console)
    logger.addHandler(file)
    def test(logger):
        logger.debug("Debug!")
        logger.info("Info!")
        logger.warning("Warning!")
        logger.error("Error!")
        logger.exception("Exception!") #this expects exception info
        logger.critical("Critical!")
    # test(logger)
    return logger
