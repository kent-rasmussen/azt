#!/usr/bin/env python3
# coding=UTF-8
import logsetup
from utilities import *
log=logsetup.getlog(__name__)
logsetup.setlevel('INFO',log) #for this file
import platform
import sys
import subprocess
import utilities

try:
     _('x')
except:
    def _(x):
        return str(x)

def pip_install(installs=[],secondtry=False):
    """With a list provided in installs, this installs only those modules.
    Otherwise, it tries to install everything needed by A−Z+T.
    Yes, this is excessive, but better than leaving users hanging if they can't
    resolve pip install issues."""
    if secondtry:
        log.info("Trying a second time, with '--force-reinstall'")
    else:
        log.info("Installing python dependencies")
    if platform.system() == 'Linux':
        log.info(_("If you have errors containing ˋportaudioˊ above, you should "
            "install pyaudio with your package manager."))
    # The following is here to see what version python will be looking for, and
    # why it didn't find what's there. It doesn't input to anything afterwards.
    log.info("FYI, looking for this platform: {}_{}".format(
                                                        platform.system(),
                                                        platform.processor()))
    installfolder='modulestoinstall/'
    installedsomething=False
    """Migrate this to `bin/pip install -r requirements.txt`"""
    if not installs:
        installs=[
            ['--upgrade', 'pip', 'setuptools', 'wheel'], #this is probably never needed
            ['urllib3'],
            ['numpy'],
            ['pyaudio'],
            ['Pillow'],
            ['lxml'],
            ['psutil'],
            ['soundfile'],
            ['librosa'],
            ['transformers'],
            ['langcodes'],
            ['pyautogui'],
            # ['mysql-connector-python', 'wave'], #needed for wave
            # 'pymysql', #or maybe this one
            ['whisper'],
            ['packaging'],
            ['patiencediff']
            ]
    else:
        installs=[installs] #do the whole list at once, if given a list
    log.info("Installs: {}".format(', '.join([i for j in installs for i in j])))
    for install in installs:
        thisinstalled=False
        pyargs=[sys.executable, '-m', 'pip', 'install',
        '-f', installfolder, #install the one in this folder, if there
        '--no-index' #This stops it from looking online
        ]
        npyargs=len(pyargs)
        if secondtry:
            pyargs.extend(['--force-reinstall'])
        pyargs.extend(install)
        log.info("Running `{}`".format(' '.join(pyargs)))
        try:
            o=subprocess.check_output(pyargs,shell=False,
                                        stderr=subprocess.STDOUT)
            o=utilities.stouttostr(o)
            if not o or "Successfully installed" in o:
                log.info("looks like it was successful; so I'm going to reboot "
                            "in a bit. Output follows:")
                thisinstalled=installedsomething=True
        except subprocess.CalledProcessError as e:
            o=utilities.stouttostr(e.output)
            if 'Could not find a version' in o:
                pyargs.remove('--no-index')
                log.info("Running `{}`".format(' '.join(pyargs)))
                try:
                    o=subprocess.check_output(pyargs,shell=False,
                                            stderr=subprocess.STDOUT)
                    o=utilities.stouttostr(o)
                    if not o or "Successfully installed" in o:
                        log.info("looks like it was at last successful; so "
                                "I'm going to reboot in a bit. Output follows:")
                        thisinstalled=installedsomething=True
                except subprocess.CalledProcessError as e:
                    o=utilities.stouttostr(e.output)
                    if "Could not find a version" in o:
                        errors=[i for i in o.splitlines() if "ERROR:" in i]
                        log.info(_("Please make sure your internet is connected, then "
                        "click {}\n{}".format(_("OK"),'\n'.join(errors))))
                        # ErrorNotice(text=t,parent=ui.Root(),wait=True)
                        log.info("Trying again, hopefully with internet")
                        try:
                            o=subprocess.check_output(pyargs,shell=False,
                                                stderr=subprocess.STDOUT)
                            o=utilities.stouttostr(o)
                            if not o or "Successfully installed" in o:
                                log.info("looks like it was at last successful;"
                                        " so I'm going to reboot in a bit. "
                                        "Output follows:")
                                thisinstalled=installedsomething=True
                        except Exception as e:
                            log.info(_("I'm going to give up now, sorry!\n{}"
                                "".format('\n'.join(errors))))
                            # ErrorNotice(text=t,parent=ui.Root(),wait=True)
                            log.error("Looks like there was an error, "
                                        "after all: {}".format(e))
        if not thisinstalled:
            log.info("Nothing installed. Output follows:")
        log.info(o) #just give bytes, if encoding isn't correct
    if not installedsomething and not secondtry:
        pip_install(secondtry=True) #force reinstalls, just once
