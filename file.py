#!/usr/bin/env python3
# coding=UTF-8
from tkinter import filedialog
from tkinter import Tk
import pathlib
import os
import stat
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
    if filename:
        return pathlib.Path(filename)
def getfilenamefrompath(filename):
    if filename:
        return pathlib.Path(filename).name
def fileandparentfrompath(url):
    return getreldir(pathlib.Path(url).parent.parent, pathlib.Path(url))
def parentfrompath(url):
    return getreldir(pathlib.Path(url).parent.parent, pathlib.Path(url).parent)
def fullpathname(filename):
    """This is full, relative to this file (in the program repo root)"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
        log.info("using base_path {}".format(base_path))
    except Exception:
        base_path = pathlib.Path(__file__).parent
    return pathlib.Path.joinpath(
                                base_path,
                                filename)
def fullpathnamewrt(db,filename):
    """This is full, relative to the db file (use for lift or other non-program
    references)"""
    if exists(db):
        dir=db
    elif hasattr(db,'filename') and exists(db.filename): #for lift object
        dir=db.filename
    else:
        log.error(f"{db} doesn't seem to exist, nor does {db}.filename")
    return pathlib.Path.joinpath(dir,filename)
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
    diropts=['images','pictures']
    for d in diropts:
        dir=pathlib.Path.joinpath(dirname,d)
        if getfilesofdirectory(dir):
            return dir
    #if nothing anywhere, just go with first.
    d=pathlib.Path.joinpath(dirname,diropts[0])
    if not os.path.exists(d):
        os.mkdir(d)
    return d
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
    if file and os.path.exists(file):
        return True
    # else:
    #     log.info("file {} doesn't exist!".format(file))
def rmdir(dir):
    os.rmdir(dir)
def move(file,newfile):
    if exists(file) and not exists(newfile):
        os.rename(file,newfile)
    else:
        log.debug(_("Tried to move {} to {}, but I can't find it "
                    "(or overwrite?).").format(file,newfile))
def remove(file):
    if exists(file):
        os.remove(file)
    elif exists(fullpathname(file)):
        os.remove(fullpathname(file))
    else:
        log.debug(_("Tried to remove {}, but I can't find it.").format(file))
def makedir(dir,**kwargs):
    if type(dir) is str:
        dir=getfile(dir)
    if dir and not exists(dir):
        dir.mkdir(parents=True)
    elif not kwargs.get('silent'):
        log.info("directory {} already exists!".format(dir))
    return getfile(dir)
def getnewlifturl(dir,xyz):
    dir=pathlib.Path(dir)
    dir=dir.joinpath(xyz)
    if exists(dir):
        log.error("The directory {} already exists! Not Continuing.".format(dir))
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
def getdiredrelURI(reldir,filename):
    return pathlib.Path(reldir).joinpath(filename).as_uri()
def getdiredrelURL(reldir,filename):
    return pathlib.Path(reldir).joinpath(filename)
def getdiredrelURLposix(reldir,filename):
    return pathlib.PurePath(reldir).joinpath(filename).as_posix()
    # This doesn't help:
    # return pathlib.PureWindowsPath(reldir).joinpath(filename).as_posix()
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
    # log.info("returning: {}".format(
    #                                 [i for i in
    #                                 getattr(lift_url,'filenames',[])
    #                                 if exists(i)]
    #                                 ))
    return [i for i in getattr(lift_url,'filenames',[]) if exists(i)]
def uilang(lang=None):
    """So far, there is just one value here; no need to load before writing"""
    if not lang:
        try:
            import ui_lang
            log.info(f"Found ui_lang value {ui_lang.ui_lang}")
            return ui_lang.ui_lang
        except:
            log.debug("ui_lang didn't import, or didn't have a value to return")
            return
    file=fullpathnamewrt(getfilenamedir(__file__),"ui_lang.py")
    # pathlib.Path.joinpath(pathlib.Path(__file__).parent, "ui_lang.py")
    with open(file, 'w', encoding='utf-8') as f:
        f.write('ui_lang="'+str(lang)+'"\n')
def getfilename():
    """This returns a single filename, if there, else a list if there"""
    try:
        import lift_url
    except:
        log.debug("getfilename lift_url didn't import")
        return [] #this should always be iterable
    if (hasattr(lift_url,'filename') and lift_url.filename and
            exists(lift_url.filename)):
        log.debug("lift_url.py imported fine, and url points to a file.")
        return lift_url.filename
    else:
        log.debug("lift_url imported, but didn't contain a url that points "
                    "to an existing file "
                    f"({getattr(lift_url,'filename',None)}): {dir(lift_url)}")
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
    l=[]
    for i in pathlib.Path(dir).glob(regex):
        l.extend([i])
    return l # we don't want a generator here
def makewritablebyeveryone(path):
    os.chmod(path,
            stat.S_IRUSR|stat.S_IWUSR|stat.S_IXUSR|
            stat.S_IRGRP|stat.S_IWGRP|stat.S_IXGRP|
            stat.S_IROTH|stat.S_IWOTH|stat.S_IXOTH
            )
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
    return getdirectory(prompt, media)
def askopenfilename(**kwargs):
    return filedialog.askopenfilename(**kwargs)
    # initialdir = home,#"$HOME",#filetypes=[('LIFT','*.lift')],
    #                                 title = _("Select LIFT Lexicon File"),
    #                                 filetypes=[
    #                                         # ("LIFT File",'.[Ll][Ii][Ff][Tt]','TEXT'),
    #                                         # ("LIFT File",'.LIFT .lift','TEXT'),
    #                                         ("LIFT File",'.LIFT','TEXT'),
    #                                         ("LIFT File",'.lift','TEXT'),
    #                                         # ("Git repository",'*.git'),
    #                                         ]
    #                                 )
def lift():
    Tk().withdraw() # we don't want a full GUI, so keep the root window from appearing
    home=gethome()
    filename=askopenfilename(initialdir = home,#"$HOME",#filetypes=[('LIFT','*.lift')],
                                    title = _("Select LIFT Lexicon File"),
                                    filetypes=[
                                            # ("LIFT File",'.[Ll][Ii][Ff][Tt]','TEXT'),
                                            # ("LIFT File",'.LIFT .lift','TEXT'),
                                            ("LIFT File",'.LIFT','TEXT'),
                                            ("LIFT File",'.lift','TEXT'),
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
    filenames=[]
    try:
        import lift_url
        if hasattr(lift_url,'filenames') and lift_url.filenames:
            filenames=lift_url.filenames
    except:
        log.error("writefilename lift_url didn't import.")
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
    def filetuple(i): #This is just for testing; we need real translations!
        return ('/home/kentr/Assignment/Tools/WeSay/gnd/audio/'+i,
            i.split('-unit_')[-1])
    filelist=[
                'Nom_fd97d4d3-b2cd-40f4-8543-d1e84b9697a2_lexical-unit_təɓah_palmier-rônier_.wav',
                'Nom_fda908b3-1153-48a5-8d7c-a310e34c2b93_lexical-unit_rəŋga_ruine_.wav',
                # 'Nom_fed71211-7f50-41e9-8533-132516027276_lexical-unit_simir_flèche_.wav'
            ]
    fqfilelist=[filetuple(i) for i in filelist]
    archivename='lexicon_test'
    archivedir='/home/kentr/bin/raspy/newASR/training_data/'
    t=TarBall(archivedir,archivename)
    t.populate(fqfilelist)
    t=TarBall(archivedir,archivename,append=True)
    file='Nom_fed71211-7f50-41e9-8533-132516027276_lexical-unit_simir_flèche_.wav'
    t.add_soundfile_w_metadata(filetuple(file))
    t.writeout()
    quit()
    
