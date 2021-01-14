#!/usr/bin/env python3
# coding=UTF-8
from tkinter import filedialog
from tkinter import Tk
import pathlib
import os
import logging
log = logging.getLogger(__name__)

# import os
def fullpathname(filename):
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = pathlib.Path(__file__).parent #os.path.abspath(".")
    return pathlib.Path.joinpath(
                                # pathlib.Path(__file__).parent,
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
# def getimagefilename(*args):
#     wavfilename=''
#     for arg in args:
#         log.debug(type(arg),type(args))
#         wavfilename+=arg
#         if args.index(arg) < len(args):
#             wavfilename+='_'
#     # wavfilename+='.wav' #add this elsewhere
#     return pathlib.Path.joinpath(wavfilename)
def getlangnamepaths(filename, langs):
    #lift=getfilename()
    output={}
    wsdir=pathlib.Path.joinpath(pathlib.Path(filename).parent, 'WritingSystems')
    for lang in langs:
        #filename=pathlib.Path.joinpath(wsdir, lang +'.ldml')
        output[lang]=str(pathlib.Path.joinpath(wsdir, lang +'.ldml'))
        log.debug(filename)
    log.debug(output)
    return output
def getinterfacelang(self):
    """This is called by the mainapplication class before anything else happens,
    including setting the ui interface language (that's what this enables). So
    I haven't figured out a way to translate the strings here, and I trust that
    will be OK."""
    self.interfacelangs=[{'code':'fr','name':'Français'},
                            {'code':'en','name':'English'},
                            {'code':'fub','name':'Fulfulde'}
                            ]
    try:
        import ui_lang
        log.debug("lift_url.py imported fine.") #Sorry, no translation!
        try:
            self.interfacelang=ui_lang.interfacelang
            log.debug('filename: '+filename)
        except:
            log.error("Didn't find ui_lang.interfacelang") #Sorry, no translation!
            self.interfacelang=None
    except:
        log.error("Didn't find ui_lang.py") #Sorry, no translation!
        self.interfacelang=None
def writeinterfacelangtofile(lang):
    file=pathlib.Path.joinpath(pathlib.Path(__file__).parent, "ui_lang.py")
    f = open(file, 'w', encoding='utf-8') # to create writeable file (deleting existing), "a") #to append
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
    # try:
    #     return filename
    # except:
    #     text=(_("Sorry, you don't seem to have selected a LIFT lexicon file."))
    #     tkinter.Label(self.status, text=text).grid(column=0,row=1)
    #     #window.
    #     self.window.wait_window(window=self.window)
    #     self.destroy()
def lift():
    Tk().withdraw() # we don't want a full GUI, so keep the root window from appearing
    filename=filedialog.askopenfilename(initialdir = "$HOME",#filetypes=[('LIFT','*.lift')],
                                    title = _("Select LIFT Lexicon File"))
    log.debug('filename:'+str(filename))
    if filename is (): #Try one more time...
        log.warning("Sorry, did you select a file? Trying again.")
        filename=filedialog.askopenfilename(initialdir = "$HOME",
                                    title = _("Select LIFT Lexicon File"),)
        if filename is (): #still, then give up.
            log.warning("Sorry, did you select a file? Giving up.")
            # return None
    log.debug('filename: {}'.format(str(filename)))
    """Assuming this file is still in lift/, this works. Once out,
    remove a parent"""
    file=pathlib.Path.joinpath(pathlib.Path(__file__).parent, "lift_url.py")
    f = open(file, 'w', encoding='utf-8') # to create writeable file (deleting existing), "a") #to append
    f.write('filename="'+filename+'"'+'\n')
    f.close()
    return filename
    #print (filename)
    #saveasfilename =  filedialog.asksaveasfilename(initialdir = "$HOME",title = "Select file to save as",)
    #print (saveasfilename)

if __name__ == "__main__":
    import sys
    # import ws_environment
    import datetime
    import shutil
    def _(x):
        str(x)
    # import globalvariables
    # wsfolder=ws_environment.getwsfolder()
    # langdir=ws_environment.getlangdir()
    # xyz=globalvariables.xyz
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
    lift=lift()
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
    if exists(lift):
        log.info("Lift file is " + str(lift))
    else:
        log.info("Sorry, problem with non-existent lift file " + str(lift))
        usage()
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
