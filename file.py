#!/usr/bin/env python3
# coding=UTF-8
from tkinter import filedialog
from tkinter import Tk
import pathlib
import os
import logging
log = logging.getLogger(__name__)
try: #Allow this module to be used without translation
    _
except:
    def _(x):
        return x

def fullpathname(filename):
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = pathlib.Path(__file__).parent
    return pathlib.Path.joinpath(
                                base_path,
                                filename)
def askfilename(self):
    log.info('Apparently there is no last lift file url; asking...')
    text=(_("Please select a LIFT lexicon file to check"))
    tkinter.Label(self.status, text=text).grid(column=0,
    row=0)
    return lift() #this is a string
def getfilenamedir(filename):
    return pathlib.Path(filename).parent
def getfilenamebase(filename):
    return pathlib.Path(filename).stem
def getimagesdir(filename):
    dir=pathlib.Path.joinpath(getfilenamedir(filename),'images')
    if not os.path.exists(dir):
        os.mkdir(dir)
    return dir
def getaudiodir(filename):
    dir=pathlib.Path.joinpath(getfilenamedir(filename),'audio')
    log.debug("Looking for {}".format(dir))
    if not os.path.exists(dir):
        log.debug("{} not there, making it!".format(dir))
        os.mkdir(dir)
    return dir
def getreportdir(filename):
    dir=pathlib.Path.joinpath(getfilenamedir(filename),'reports')
    log.debug("Looking for {}".format(dir))
    if not os.path.exists(dir):
        log.debug("{} not there, making it!".format(dir))
        os.mkdir(dir)
    return dir
def getreldir(origin,dest):
    return os.path.relpath(dest,origin)
def getstylesheetdir(filename):
    dir=pathlib.Path.joinpath(getfilenamedir(filename),'xlpstylesheets')
    log.debug("Looking for {}".format(dir))
    if not os.path.exists(dir):
        log.debug("{} not there, not using your stylesheet!\nIf you want to "
        "use your own XLingPaper styesheet for these reports, make that "
        "directory, and put the stylesheet in it. For now, using a default "
        "stylesheet.".format(dir))
        dir=pathlib.Path.joinpath(pathlib.Path(__file__).parent,'xlpstylesheets')
        if not os.path.exists(dir):
            log.debug("{} not there, not using a stylesheet!".format(dir))
            return
    return dir
def gettransformsdir():
    dir=pathlib.Path.joinpath(pathlib.Path(__file__).parent,'xlptransforms')
    log.debug("Looking for {}".format(dir))
    if not os.path.exists(dir):
        log.error("HELP! not sure why {} is not there!".format(dir))
        # os.mkdir(dir)
    return dir

def exists(file):
    if os.path.exists(file):
        return True
    else:
        return False
def remove(file):
    if exists(file):
        os.remove(file)
    elif exists(fullpathname(file)):
        os.remove(fullpathname(file))
    else:
        log.debug(_("Tried to remove {}, but I can't find it.").format(file))
def getdiredurl(dir,filename):
    return pathlib.Path.joinpath(dir,filename)
def getdiredrelURL(reldir,filename):
    return pathlib.PurePath(reldir).joinpath(filename)
def getlangnamepaths(filename, langs):
    output={}
    wsdir=pathlib.Path.joinpath(pathlib.Path(filename).parent, 'WritingSystems')
    for lang in langs:
        #filename=pathlib.Path.joinpath(wsdir, lang +'.ldml')
        output[lang]=str(pathlib.Path.joinpath(wsdir, lang +'.ldml'))
        log.log(1,filename)
    log.log(1,output)
    return output
def getinterfacelangs():
    return [{'code':'fr','name':'Français'},
            {'code':'en','name':'English'},
            {'code':'fub','name':'Fulfulde'}
            ]
def getinterfacelang():
    # I haven't figured out a way to translate the strings here, hope that's OK.
    # This is because this fn is called by the mainapplication class before
    # anything else happens, including setting the ui interface language
    # (that's what this enables).
    try:
        import ui_lang
        log.log(2,"ui_lang.py imported fine.") #Sorry, no translation!
        try:
            log.debug('Boot ui_lang: {}'.format(ui_lang.interfacelang))
            return ui_lang.interfacelang
        except:
            log.error("Didn't find ui_lang.interfacelang") #No translation!
    except:
        log.error("Didn't find ui_lang.py") #Sorry, no translation!
def writeinterfacelangtofile(lang):
    file=pathlib.Path.joinpath(pathlib.Path(__file__).parent, "ui_lang.py")
    f = open(file, 'w', encoding='utf-8') # to append, "a"
    f.write('interfacelang="'+lang+'"'+'\n')
    f.close()
def getfilename():
    try:
        import lift_url
        if exists(lift_url.filename): #tests if file exists at url
            log.debug("lift_url.py imported fine, and url points to a file.")
            return lift_url.filename
        else:
            log.debug("lift_url imported, but didn't contain a url that points "
                        "to a file: {}".format(str(lift_url.filename)))
            return lift()
    except:
        log.debug("lift_url didn't import")
        return lift()
def lift():
    Tk().withdraw() # we don't want a full GUI, so keep the root window from appearing
    filename=filedialog.askopenfilename(initialdir = "$HOME",#filetypes=[('LIFT','*.lift')],
                                    title = _("Select LIFT Lexicon File"))
    log.debug('filename:'+str(filename))
    if filename == (): #Try one more time...
        log.warning("Sorry, did you select a file? Trying again.")
        filename=filedialog.askopenfilename(initialdir = "$HOME",
                                    title = _("Select LIFT Lexicon File"),)
        if filename == (): #still, then give up.
            log.warning("Sorry, did you select a file? Giving up.")
    log.debug('filename: {}'.format(str(filename)))
    """Assuming this file is still in lift/, this works. Once out,
    remove a parent"""
    file=pathlib.Path.joinpath(pathlib.Path(__file__).parent, "lift_url.py")
    f = open(file, 'w', encoding='utf-8') # to append, "a"
    f.write('filename="'+filename+'"'+'\n')
    f.close()
    return filename
if __name__ == "__main__":
    import sys
    import datetime
    import shutil
    def usage():
        log.info("usage for one entry:")
        log.info(" python3 " + pathlib.Path(__file__).name + " <forms|ids|tones|prontones|glosses|gloss2s|plurals|pses|all|cards|lxnglosses> <lift file> <guid>")
        log.info("usage for all entries in lift file:")
        log.info(" python3 " + pathlib.Path(__file__).name + " <forms|ids|tones|prontones|glosses|gloss2s|plurals|pses|all|cards|lxnglosses|ids2testN|ids2testV> <lift file>")
        exit() #if there is a problem with the usage, we don't want to keep going...
    def liftori():
        global wsfolder
        global xyz
        return pathlib.Path.joinpath(wsfolder, xyz, xyz +'.lift')
    def liftstr():
        global wsfolder
        global xyz
        return str(pathlib.Path.joinpath(wsfolder, xyz, xyz +'.lift'))
    def liftdirstr():
        global wsfolder
        global xyz
        return str(pathlib.Path.joinpath(wsfolder, xyz))

    # def baklift():
    #     global wsfolder
    #     global xyz
    #     now=datetime.datetime.now()
    #     return pathlib.Path.joinpath(wsfolder, xyz, xyz + '.lift' + str(now))
    # lift=lift()
    # baklift=baklift()

    #Varify that these files and folders exist as appropriate:
    # if wsfolder.exists():
    #     log.info("WeSay Folder is " + str(wsfolder))
    # else:
    #     log.info("Sorry, problem with non-existent WeSay folder " + str(wsfolder))
    #     usage()
    # if langdir.exists():
    #     log.info("Lang Directory is " + str(langdir))
    # else:
    #     log.info("Sorry, problem with non-existent language directory " + str(langdir))
    #     usage()
    # if exists(lift):
    #     log.info("Lift file is " + str(lift))
    # else:
    #     log.info("Sorry, problem with non-existent lift file " + str(lift))
    #     usage()
    # if baklift.exists():
    #     log.info("Sorry, lift file backup already exists " + str(baklift))
    #     usage()
    # else:
    #     log.info("Lift file backup is " + str(baklift))


    # def bak():
    #     now=datetime.datetime.now()
    #     log.info("Running at " + str(now))
    #     global lift
    #     global baklift
    #     #lift=lift()
    #     #baklift=baklift()
    #     shutil.copyfile(lift, baklift)
    #     log.info(lift, "backed up.")
    # bak() #do I want this running each time anything happens?
