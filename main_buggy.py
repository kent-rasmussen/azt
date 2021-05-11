#!/usr/bin/env python3
# coding=UTF-8
"""This file just checks that the bug reporting is working"""
program={'name':'A→Z+T'}
program['version']='0.8' #This is a string...
import platform
loglevel='DEBUG'
from logsetup import *
log=logsetup(loglevel)

def main():
    log.infos("Running main function") #Don't translate yet!
    logshutdown()
if __name__ == "__main__":
    log.info('Running {} v{} in {} on {} with loglevel {} at {}'.format(
                                    program['name'],program['version'],'aztdir',
                                    platform.uname().node,
                                    loglevel,
                                    datetime.datetime.utcnow().isoformat()))
    try:
        main()
    except Exception as e:
        log.exception("Unexpected exception! %s",e)
        logwritelzma(log.filename) #in logsetup
    exit()
