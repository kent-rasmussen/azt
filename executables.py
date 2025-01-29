#!/usr/bin/env python3
# coding=UTF-8
import logsetup
log=logsetup.getlog(__name__)
logsetup.setlevel('INFO',log) #for this file
import subprocess
"""This module should eventually old everything that depends on subprocess,
maybe including a class to store program, or other common dependencies"""

def praatopen(program,file,newpraat=False,event=None):
    """sendpraat is now looked for only where praat version is before
    'Praat 6.2.04 (December 18 2021)', when new functionality was added to
    praat, to allow successive calls to go to the same window.
    The same version also introduced the '--hide-picture' command line option,
    so we only use that when praatversioncheck() passes.
    """
    if not newpraat and 'sendpraat' in program and program['sendpraat']:
        """sendpraat sends the command to a running praat instance. If there
        isn't one, just open praat."""
        praatargs=[program['sendpraat'], 'praat', 'Read from file... "{}"'
                                                    "".format(file)]
        try:
            o=subprocess.check_output(praatargs,shell=False,
                                        stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            o=e.output
        try:
            t=stouttostr(o)
        except:
            t=o
        if t == 'sendpraat: Program praat not running.':
            praatopen(file,newpraat=True)
        else:
            log.info("praatoutput: {}".format(t))
    elif program['praat']:
        log.info(_("Trying to call Praat at {}...").format(program['praat']))
        if 'sendpraat' not in program: #don't care about exe, just version check
            praatargs=[program['praat'], '--hide-picture','--open', file]
        else:
            praatargs=[program['praat'], '--open', file]
        subprocess.Popen(praatargs,shell=False) #not run; continue here
    else:
        log.info(_("Looks like I couln't find Praat..."))
