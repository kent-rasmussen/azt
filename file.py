#!/usr/bin/env python3
# coding=UTF-8
from tkinter import filedialog
from tkinter import Tk
import pathlib
import os
import platform
import logsetup
log=logsetup.getlog(__name__)
# logsetup.setlevel('INFO',log) #for this file
logsetup.setlevel('DEBUG',log) #for this file
from importlib import reload as modulereload
try: #Allow this module to be used without translation
    _
except:
    def _(x):
        return x
def getfile(filename):
    return pathlib.Path(filename)
def getfilenamefrompath(filename):
    return pathlib.Path(filename).name
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
def gettranslationdirin(exedir):
    dir=pathlib.Path.joinpath(exedir,'translations')
    return dir
def getimagesdir(dirname):
    dir=pathlib.Path.joinpath(dirname,'images')
    if not os.path.exists(dir):
        os.mkdir(dir)
    return dir
def getimagesdiralternate(dirname):
    dir=pathlib.Path.joinpath(dirname,'pictures') #WeSay uses this
    if os.path.exists(dir):
        return dir
def getaudiodir(dirname):
    dir=pathlib.Path.joinpath(dirname,'audio')
    log.debug("Looking for {}".format(dir))
    if not os.path.exists(dir):
        log.debug("{} not there, making it!".format(dir))
        os.mkdir(dir)
    return dir
def getreportdir(dirname):
    dir=pathlib.Path.joinpath(dirname,'reports')
    log.debug("Looking for {}".format(dir))
    if not os.path.exists(dir):
        log.debug("{} not there, making it!".format(dir))
        os.mkdir(dir)
    return dir
def getreldir(origin,dest):
    return os.path.relpath(dest,origin)
    # return getfile(dest).relative_to(getfile(origin))
def getreldirposix(origin,dest):
    return getfile(os.path.relpath(dest,origin))
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
def makedir(dir):
    if type(dir) is str:
        dir=getfile(dir)
    if not exists(dir):
        dir.mkdir(parents=True)
    else:
        log.info("directory {} already exists!".format(dir))
def getnewlifturl(dir,xyz):
    dir=pathlib.Path(dir)
    dir=dir.joinpath(xyz)
    if exists(dir):
        log.error("The directory {} already exits! Not Continuing.".format(dir))
        return
    else:
        dir.mkdir()
    url=dir.joinpath(xyz)
    url=url.with_suffix('.lift')
    return url
def getdiredurl(dir,filename):
    if type(dir) is str:
        dir=getfile(dir)
    return pathlib.Path.joinpath(dir,filename)
def getdiredrelURL(reldir,filename):
    return pathlib.Path(reldir).joinpath(filename)
def getdiredrelURLposix(reldir,filename):
    return pathlib.Path(reldir).joinpath(filename).as_posix()
    # return pathlib.PurePath(reldir).joinpath(filename)
def getlangnamepaths(filename, langs):
    output={}
    wsdir=pathlib.Path.joinpath(pathlib.Path(filename).parent, 'WritingSystems')
    for lang in langs:
        #filename=pathlib.Path.joinpath(wsdir, lang +'.ldml')
        output[lang]=str(pathlib.Path.joinpath(wsdir, lang +'.ldml'))
        log.log(1,filename)
    log.log(1,output)
    return output
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
def getfilenames():
    """This just returns the list, if there."""
    try: #b/c sometimes we come directly here
        import lift_url
    except:
        log.debug("getfilename lift_url didn't import")
    if hasattr(lift_url,'filenames') and lift_url.filenames:
        log.info("Returning filenames: {}".format(lift_url.filenames))
        return lift_url.filenames
def getfilename():
    """This returns a single filename, if there, else a list if there, else
    it asks for user input."""
    try:
        import lift_url
    except:
        log.debug("getfilename lift_url didn't import")
        return
    if (hasattr(lift_url,'filename') and lift_url.filename and
            exists(lift_url.filename)):
        log.debug("lift_url.py imported fine, and url points to a file.")
        return lift_url.filename
    else:
        log.debug("lift_url imported, but didn't contain a url that points "
                    "to a file: {}".format(dir(lift_url)))
        return getfilenames()
def gethome():
    home=pathlib.Path.home()
    if platform.uname().node == 'karlap':
        home=pathlib.Path.joinpath(home, "Assignment","Tools","WeSay")
    return home
def getdirectory(title=None,home=None):
    Tk().withdraw() # we don't want a full GUI, so keep the root window from appearing
    if not home:
        home=gethome()
    if not title:
        title=_("Select a new location for your LIFT Lexicon and other Files")
    f=filedialog.askdirectory(initialdir = home, title = title)
    if f:
        return f
def getfilesofdirectory(dir,regex='*'):
    # return pathlib.Path(dir).iterdir()
    return pathlib.Path(dir).glob(regex)
def getmediadirectory(mediatype=None):
    log.info("Looking for media directory")
    if platform.system() == 'Linux':
        media=getdiredurl('/media/',os.getlogin())
        log.info("media: {} ".format(media))
    else:
        media=None
    if mediatype:
        prompt=_("Please select where to find the {} media locally"
                ).format(mediatype)
    else:
        prompt=_("Please select where to find the media locally")
    return getdirectory(prompt, media,
                        )
def lift():
    Tk().withdraw() # we don't want a full GUI, so keep the root window from appearing
    home=gethome()
    filename=filedialog.askopenfilename(initialdir = home,#"$HOME",#filetypes=[('LIFT','*.lift')],
                                    title = _("Select LIFT Lexicon File"),
                                    filetypes=[
                                            ("LIFT File",'.[Ll][Ii][Ff][Tt]','TEXT'),
                                            ("lift File",'.lift','TEXT'),
                                            # ("Git repository",'*.git'),
                                            ]
                                    )
    if not filename:
        return
    if exists(filename):
        return writefilename(filename)
    log.debug('filename:'+str(filename))
    if not filename:
        log.warning("Sorry, did you select a file? Giving up.")
        return
    log.debug('filename: {}'.format(str(filename)))
    """Assuming this file is still in lift/, this works. Once out,
    remove a parent"""
    return writefilename(filename)
def writefilename(filename=''):
    try:
        import lift_url
        if hasattr(lift_url,'filenames') and lift_url.filenames:
            filenames=lift_url.filenames
    except:
        log.error("writefilename lift_url didn't import.")
        filenames=[]
    # log.info("filenames: {} ({})".format(filenames,filename))
    if filename and str(filename) not in filenames:
        filenames.append(str(filename))
    file=pathlib.Path.joinpath(pathlib.Path(__file__).parent, "lift_url.py")
    f = open(file, 'w', encoding='utf-8') # to append, "a"
    f.write('filename="'+str(filename)+'"\n')
    f.write('filenames='+str(filenames)+'\n')
    f.close()
    return filename
if __name__ == "__main__":
    import sys
    import datetime
    import shutil
    from tkinter import ttk
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
    # Create an instance of ttk
    log.info(lift())
    quit()
    s = ttk.Style()
    # log.info(
    for t in s.theme_names():
    # Use the window native theme
        s.theme_use(t)
        log.info(getmediadirectory(mediatype=t))
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
