#!/usr/bin/env python3
# coding=UTF-8
import gettext
_ = gettext.gettext

from utilities import source_base_dir
import pathlib
import os as _os

# File dialog support — tkinter when available, zenity/kdialog fallback
try:
    if _os.environ.get('AZT_UI_BACKEND', '').lower() == 'webview':
        raise ImportError("webview backend — skip tkinter filedialog")
    from tkinter import filedialog
    from tkinter import Tk
    _has_tk_dialog = True
except ImportError:
    _has_tk_dialog = False

def _zenity_directory(title, initialdir):
    """Fallback directory picker using zenity (Linux) or input()."""
    import subprocess, shutil
    if shutil.which('zenity'):
        try:
            r = subprocess.run(['zenity', '--file-selection', '--directory',
                                '--title', title or 'Select Directory'],
                               capture_output=True, text=True)
            if r.returncode == 0 and r.stdout.strip():
                return r.stdout.strip()
        except Exception:
            pass
    # Last resort: console input
    return input(f"{title or 'Directory'} [{initialdir}]: ").strip() or None

def _zenity_openfile(**kwargs):
    """Fallback file picker using zenity (Linux) or input()."""
    import subprocess, shutil
    title = kwargs.get('title', 'Select File')
    if shutil.which('zenity'):
        try:
            r = subprocess.run(['zenity', '--file-selection',
                                '--title', title],
                               capture_output=True, text=True)
            if r.returncode == 0 and r.stdout.strip():
                return r.stdout.strip()
        except Exception:
            pass
    return input(f"{title}: ").strip() or ''

def _app_settings():
    """Lazy singleton for AppSettingsManager, keyed to the AZT root dir."""
    if not hasattr(_app_settings, '_instance') or _app_settings._instance is None:
        from settings import AppSettingsManager
        base = pathlib.Path(source_base_dir) / 'azt' if source_base_dir else None
        _app_settings._instance = AppSettingsManager(base) if base else None
    return _app_settings._instance
_app_settings._instance = None
import os
import stat
import platform
try:
    import soundfile
    soundfileOK=True
except ModuleNotFoundError:
    print("Module soundfile not installed; to use sound features, install.")
    soundfileOK=False
# import samplerate
# (librosa dropped 2026-07-16 — resampling now scipy; see file_sound.py)
import io
import tarfile
# packaging is imported lazily in praatversioncheck: this module loads on the
# BARE-venv bootstrap path (py_modules→logsetup→file), before pip deps exist.
from importlib import reload as modulereload
import subprocess
from utilities.encodings import stouttostr
joinpath=pathlib.Path.joinpath
cwd=pathlib.Path.cwd
def getfile(filename):
    if filename:
        return pathlib.Path(filename)
def getparent(filename):
    if filename:
        return pathlib.Path(filename).parent
def getfilenamefrompath(filename):
    if filename:
        return pathlib.Path(filename).name
def absolute_of_other(file1,file2):
    """If either file is a final subset of the other, it returns"""
    for a,b in [(file1,file2)]:
        for x,y in [(a,b),(b,a)]:
            if str(pathlib.PurePath(x)).endswith(str(pathlib.PurePath(y))):
                return x
def localfile(filename):
    print(f"Running from file {__file__}, in directory {os.path.dirname(__file__)}")
    return os.path.join(os.path.dirname(__file__),filename)
def replace(this,ontothat):
    os.replace(this,ontothat)
def getsize(x):
    return os.path.getsize(x)
def fileandparentfrompath(url):
    return getreldir(pathlib.Path(url).parent.parent, pathlib.Path(url))
def parentfrompath(url):
    return getreldir(pathlib.Path(url).parent.parent, pathlib.Path(url).parent)
def pathname_from_base_dir(filename):
    """This is full, relative to this file (in the program repo root)"""
    return pathlib.Path(source_base_dir).joinpath(filename)
def make_pathname_from_base_dir(filename):
    return makedir(pathname_from_base_dir(filename),silent=True)
def fullpathnamewrt(db,filename):
    """This is full, relative to the db file (use for lift or other non-program
    references)"""
    if exists(db):
        dir=db
    elif hasattr(db,'filename') and exists(db.filename): #for lift object
        dir=db.filename
    else:
        return f"{db} doesn't seem to exist, nor does {db}.filename"
    return pathlib.Path.joinpath(dir,filename)
def getfilenamedir(filename):
    return pathlib.Path(filename).parent
def getfilenamebase(filename):
    return pathlib.Path(filename).stem
def getlogdir():
    return make_pathname_from_base_dir('userlogs')
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
    if not os.path.exists(dir):
        os.mkdir(dir)
    return dir
def getreportdir(dirname):
    dir=pathlib.Path.joinpath(dirname,'reports')
    if not os.path.exists(dir):
        os.mkdir(dir)
    return dir
def getexportdir(dirname):
    dir=pathlib.Path.joinpath(dirname,'exports')
    if not os.path.exists(dir):
        os.mkdir(dir)
    return dir
def getreldir(origin,dest):
    return os.path.relpath(dest,origin)
    # return getfile(dest).relative_to(getfile(origin))
def getreldirposix(origin,dest):
    return getfile(os.path.relpath(dest,origin))
def getstylesheetdir(filename):
    dir=pathlib.Path.joinpath(getfilenamedir(filename),'xlpstylesheets')
    if not os.path.exists(dir):
        dir=pathlib.Path.joinpath(pathlib.Path(__file__).parent,'xlpstylesheets')
        if not os.path.exists(dir):
            return ("{} not there, not using a stylesheet!".format(dir))
    return dir
def gettransformsdir():
    dir=pathlib.Path.joinpath(pathlib.Path(__file__).parent,'xlptransforms')
    if not os.path.exists(dir):
        return "HELP! not sure why {} is not there!".format(dir)
    return dir
def exists(file):
    if file and os.path.exists(file):
        return True
def exists_and_not_empty(dir):
    if exists(dir) and len(getfilesofdirectory(dir)):
        return True
def rmdir(dir):
    os.rmdir(dir)
def move(file,newfile):
    if exists(file) and not exists(newfile):
        os.rename(file,newfile)
    else:
        return _("Tried to move {} to {}, but I can’t find it "
                    "(or overwrite?).").format(file,newfile)
def remove(file):
    if exists(file):
        os.remove(file)
    elif exists(pathname_from_base_dir(file)):
        os.remove(pathname_from_base_dir(file))
    else:
        return _("Tried to remove {}, but I can’t find it.").format(file)
def makedir(dir,**kwargs):
    if type(dir) is str:
        dir=getfile(dir)
    if dir and not exists(dir):
        dir.mkdir(parents=True)
    return getfile(dir)
def getnewlifturl(dir,xyz):
    """This returns what should be the new lift file path. It does not check
    if the directory exists or not --do that later."""
    dir=pathlib.Path(dir)
    dir=dir.joinpath(xyz)
    if not exists(dir):
        dir.mkdir()
    url=dir.joinpath(xyz)
    url=url.with_suffix('.lift')
    return url
def getdiredurl(dir,filename):
    if not dir:
        dir='.'
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
    return output
def getinterfacelang():
    # I haven't figured out a way to translate the strings here, hope that's OK.
    # This is because this fn is called by the mainapplication class before
    # anything else happens, including setting the ui interface language
    # (that's what this enables).
    try:
        import ui_lang
        try:
            return ui_lang.interfacelang
        except AttributeError:
            return "Didn't find ui_lang.interfacelang"
    except ImportError:
        return "Didn't find ui_lang.py"
def writeinterfacelangtofile(lang):
    file=pathlib.Path.joinpath(pathlib.Path(__file__).parent, "ui_lang.py")
    f = open(file, 'w', encoding='utf-8') # to append, "a"
    f.write('interfacelang="'+lang+'"'+'\n')
    f.close()
def getfilenames():
    """Return the list of known LIFT filenames that still exist on disk."""
    mgr = _app_settings()
    if mgr is None:
        return []
    return [i for i in mgr.filenames if exists(i)]
def uilang(lang=None):
    """Get or set the UI language in app-level config."""
    mgr = _app_settings()
    if mgr is None:
        return None
    if not lang:
        return mgr.ui_lang or None
    mgr.ui_lang = lang
def uitheme(theme=None):
    """Get or set the UI theme in app-level config."""
    mgr = _app_settings()
    if mgr is None:
        return None
    if not theme:
        return mgr.ui_theme or None
    mgr.ui_theme = theme
def writefilename(filename=''):
    """Store the last-opened LIFT filename in app-level config.
    Defined here (not in file_sound) because it is NOT an audio function and
    must be available even when the optional `soundfile` package is absent —
    otherwise `file.writefilename` vanishes and opening a project hangs."""
    mgr = _app_settings()
    if mgr is None:
        return "writefilename: app settings not available."
    mgr.filename = filename
    return filename
def getfilename():
    """Return a single filename if it exists on disk, else return the list."""
    mgr = _app_settings()
    if mgr is None:
        return []
    fn = mgr.filename
    if fn and exists(fn):
        return fn
    return getfilenames()
def gethome():
    home=pathlib.Path.home()
    print(home)
    if platform.uname().node == 'karlap':
        home=pathlib.Path.joinpath(home, "Assignment","Tools","WeSay")
    return home
def getdirectory(title=None,home=None):
    if not home:
        home=gethome()
    if not title:
        title=_("Select a new location for your LIFT Lexicon and other Files")
    if _has_tk_dialog:
        Tk().withdraw()
        f=filedialog.askdirectory(initialdir = home, title = title)
    else:
        f=_zenity_directory(title, home)
    if f:
        return f
def getfilesofdirectory(dir,regex='*'):
    # return pathlib.Path(dir).iterdir()
    return [i for i in pathlib.Path(dir).glob(regex)]
def makewritablebyeveryone(path):
    os.chmod(path,
            stat.S_IRUSR|stat.S_IWUSR|stat.S_IXUSR|
            stat.S_IRGRP|stat.S_IWGRP|stat.S_IXGRP|
            stat.S_IROTH|stat.S_IWOTH|stat.S_IXOTH
            )
def getmediadirectory(mediatype=None):
    if platform.system() == 'Linux':
        media=getdiredurl('/media/',os.getlogin())
    else:
        media=None
    if mediatype:
        prompt=_("Please select where to find the {} media locally"
                ).format(mediatype)
    else:
        prompt=_("Please select where to find the media locally")
    return getdirectory(prompt, media)
def askopenfilename(**kwargs):
    if _has_tk_dialog:
        return filedialog.askopenfilename(**kwargs)
    return _zenity_openfile(**kwargs)
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
def praatversioncheck(praat_exe):
    def parseversion(x):
        return x.split()[1]
    praatvargs=[praat_exe, '--version']
    try:
        versionraw=subprocess.check_output(praatvargs, shell=False)
    except Exception as e:
        return True
    from packaging import version #lazy: see module-top note
    try:
        if b'\x00' in versionraw:
            characters=versionraw.decode('utf-16')
        else:
            characters=stouttostr(versionraw)
        out=version.Version(parseversion(characters))
    except Exception as e:
        out=versionraw
    # This is the version at which we don't need sendpraat anymore
    # and where '--hide-picture' becomes available.
    justpraatversion=version.Version(parseversion(
                                            'Praat 6.2.04 (December 18 2021)'))
    if out>=justpraatversion:
        return True
    else:
        return False
def findexecutable(exe):
    exeOS=exe
    os=platform.system()
    if os == 'Linux':
        which='which'
        if exe == 'sendpraat':
            exeOS='sendpraat-linux'
    elif os == 'Windows':
        which='where'
        if exe == 'sendpraat':
            exeOS='sendpraat-win.exe'
    elif os == 'Darwin': #MacOS
        which='which'
        if exe == 'sendpraat':
            exeOS='sendpraat-mac'
    else:
        return _("Sorry, I don’t know this OS: {os}").format(os=os)
    exeURL=None
    try:
        exeURL=subprocess.check_output([which,exeOS], shell=False)
        exeURL=stouttostr(exeURL)
    except subprocess.CalledProcessError as e:
        pass
    except Exception as e:
        return e
    if exeURL:
        exeURL=exeURL.replace('\r','').split('\n')#this will make a list, either way
        for e in exeURL[:]: #Make a copy, to iterate through changes
            #don't allow 'I could find this online for you' values
            if 'Microsoft' in e and 'WindowsApps' in e:
                exeURL.remove(e)
        exeURL=[i for i in exeURL if i is not None]
        if len(exeURL) == 1:
            exeURL=exeURL[0]
        else:
            exeURL=sorted(exeURL,key=len)[0]
    if (exe == 'praat' and exeURL and not praatversioncheck(exeURL)):
        findexecutable('sendpraat') #only ask if it would be useful
    return exeURL
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
    return writefilename(filename)
def escapecommas(x):
    if ',' in x:
        if not '"' in x:
            return '"'+x+'"'
        print("potential problem with {x} in data")
    return x
if soundfileOK:
    from .file_sound import *
