#!/usr/bin/env python3
# coding=UTF-8
import gettext
_ = gettext.gettext

from utilities import source_base_dir
from tkinter import filedialog
from tkinter import Tk
import pathlib

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
import soundfile
# import samplerate
import librosa
import io
import tarfile
from packaging import version
from importlib import reload as modulereload
import subprocess
from utilities.encodings import stouttostr
joinpath=pathlib.Path.joinpath
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
def askfilename(self):
    text=(_("Please select a LIFT lexicon file to check"))
    tkinter.Label(self.status, text=text).grid(column=0,
    row=0)
    return lift() #this is a string
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
        return _("Tried to move {} to {}, but I can't find it "
                    "(or overwrite?).").format(file,newfile)
def remove(file):
    if exists(file):
        os.remove(file)
    elif exists(pathname_from_base_dir(file)):
        os.remove(pathname_from_base_dir(file))
    else:
        return _("Tried to remove {}, but I can't find it.").format(file)
def makedir(dir,**kwargs):
    if type(dir) is str:
        dir=getfile(dir)
    if dir and not exists(dir):
        dir.mkdir(parents=True)
    return getfile(dir)
def getnewlifturl(dir,xyz):
    dir=pathlib.Path(dir)
    dir=dir.joinpath(xyz)
    if exists_and_not_empty(dir):
        return _("The directory {} already exists and isn't empty! Not Continuing.").format(dir)
    else:
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
        except:
            return "Didn't find ui_lang.interfacelang"
    except:
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
def praatversioncheck(praat_exe):
    def parseversion(x):
        return x.split()[1]
    praatvargs=[praat_exe, '--version']
    try:
        versionraw=subprocess.check_output(praatvargs, shell=False)
        #These lines could be used to see how a praat is outputting on a computer, where neither utf-8 nor uft-16.
        # for encoding in ['utf-8', 'utf-16', sys.stdout.encoding]:
        #     for errortag in ['backslashreplace','strict','ignore', 'replace']:
        #         try:
        #             log.info("{},{}.strip: {}".format(encoding, errortag,
        #                         versionraw.decode(encoding, errortag).strip()))
        #             log.info("{},{}: {}".format(encoding, errortag,
        #                         versionraw.decode(encoding, errortag)))
        #         except Exception as e:
        #             log.info("{},{} error".format(encoding, errortag))
    except Exception as e:
        return True
    try:
        if b'\x00' in versionraw:
            characters=versionraw.decode('utf-16')
        else:
            characters=stouttostr(versionraw)
        # log.info("characters={}".format(characters))
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
        return _("Sorry, I don't know this OS: {os}").format(os=os)
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
class Buffered():
    def towavbuffer(self,hz=16000):
            with soundfile.SoundFile(self.buffer, mode='wb',
                                    samplerate=hz,
                                    channels=1,
                                    format=self.format if hasattr(self,'format')
                                                    else 'wav'
                                    ) as sfo:
                try:
                    sfo.write(self.downsampled(hz))
                except:
                    sfo.write(self.sound_obj.as_array().ravel())
    def totextbuffer(self):
        self.buffer.write(self.contents.encode())
    def bufferlen(self):
        return len(self.buffer.getbuffer())
    def closebuffer(self):
        self.buffer.close()
    def __init__(self,filename=None):
        self.buffer = io.BytesIO()
class PraatSoundObject(Buffered):
    def __init__(self,sound_obj,archivename,out_format): # file name or object
        super().__init__(sound_obj)
        self.archivename=os.path.basename(archivename)
        self.sound_obj=sound_obj
        self.out_format=out_format
class SoundFile(soundfile.SoundFile,Buffered):
    """This file name should be fully qualified; it will be archived without
    directory structure.
    """
    def downsampled(self,hz=None):
        if hz and self.samplerate != hz:
            return librosa.resample(self.read(),
                                    orig_sr=self.samplerate,
                                    target_sr=hz)
             # res_type='soxr_hq', fix=True, scale=False, axis=-1, **kwargs)
            # return samplerate.converters.resample(self.read(),
            #     hz/self.samplerate)
        else:
            return self.read()
    def __init__(self,file): # file name or object
        super().__init__(file)
        Buffered.__init__(self)
        if os.path.exists(file):#keep name if file
            self.archivename=os.path.basename(file)
        else:
            print(f"Problem with nonexistent file ({file})")
class TextFile(Buffered):
    """This is here to make default data import CSV files from constructed
    python data. Instantiate with the column headers to change from default,
    and/or give another file name
    """
    def add(self,line):
        """This can contain newlines, to add multiples at a time"""
        try:
            self.contents+='\n'+line
        except AttributeError:
            self.contents=line
        except TypeError as e:
            print(f"TypeError: {type(self.contents)} != {type(line)} ({e})")
    def __init__(self,contents=None,archivename='metadata.csv'):
        Buffered.__init__(self)
        self.archivename=archivename
        if contents:
            self.add(contents)
class TarBall(Buffered):
    """This takes a list of files or objects and a file name, and makes
    a compressed tarball out of it"""
    def addtextfile(self,tf):
        """This adds the text file to the archive"""
        assert isinstance(tf,TextFile)
        tf.totextbuffer()
        self.writebuffertotar(tf)
        tf.closebuffer()
    def addsoundobject(self,obj,archivename,out_format):
        sf=PraatSoundObject(obj,archivename,out_format) # <= open from object
        sf.towavbuffer() # make another SoundFile to write to, downsampled
        self.writebuffertotar(sf)
        sf.closebuffer()
    def addsoundfile(self,file):
        sf=SoundFile(file) # <= open from disk; no downsample here
        sf.towavbuffer() # make another SoundFile to write to, downsampled
        self.writebuffertotar(sf)
        sf.closebuffer()
    def writebuffertotar(self,fileobj):
        info = tarfile.TarInfo(fileobj.archivename)
        info.size = fileobj.bufferlen()
        fileobj.buffer.seek(0)
        self.tar.addfile(info, fileobj=fileobj.buffer)
    def add_to_metadata(self,filename,*text):
        line_elements=[escapecommas(os.path.basename(filename))]+[
                                    escapecommas(i) for i in text]
        self.metadata.add(','.join(line_elements))
    def add_soundfile_w_metadata(self,t):
        if exists(t[0]) and len(t[1]): #actual file and some translation
            self.addsoundfile(t[0])
            self.add_to_metadata(*t)
            return True
    def open_metadata(self):
        if not (hasattr(self,'metadata') and isinstance(self.metadata,TextFile)):
            self.metadata=TextFile(self.metadata_header)
    def append_archive(self):
        try:
            with tarfile.open(self.archivename, 'r:'+self.ext) as in_tar:
                self.tar=tarfile.open(self.archivetempname, mode='w:'+self.ext)
                print(f"Found archive {self.archivename} "
                    f"with {len(in_tar.getnames())} files (including metadata)")
                for member in in_tar.getmembers():
                    if member.name != self.metadataname:
                        self.tar.addfile(member, in_tar.extractfile(member))
                    else: #Load this for appending, not to self.tar
                        self.metadata=TextFile(in_tar.extractfile(
                                            self.metadataname).read().decode())
                        rows=self.metadata.contents.split('\n')
                        print(f"Found metadata file '{self.metadataname}' with "
                            f"{len(rows)} rows (including header)")
                print(f"Imported {len(self.tar.getnames())} files (w/o "
                        "metadata)")
        except FileNotFoundError as e:
            print(f"Looks like {self.archivename} isn't already there; "
                    "creating.")
    def open_archive(self):
        if not (hasattr(self,'tar') and isinstance(self.tar,tarfile.TarFile)):
            self.tar=tarfile.open(self.archivetempname, "w:"+self.ext)
        self.open_metadata()
    def tarstatus(self):
        print('type:',type(self.tar))
        for t in [self.tar]:
            print(t.getnames())
            print(t.getmembers())
            print(t.list(verbose=True))
            print(t.list(verbose=False))
    def populate(self,tuples):
        """This takes a list of tuples with fq file names and transcriptions,
        and outputs the archive."""
        n=0
        for t in tuples:
            if self.add_soundfile_w_metadata(t):
                n+=1
                if not n%100:
                    print(f"{n} rows done.")
                yield n
        self.writeout()
        return f"Added {n} rows of data to {self.archivename}"
    def writeout(self):
        self.addtextfile(self.metadata) #this wasn't added earlier
        self.tar.close() # complete write to self.archivetempname
        try:
            assert tarfile.is_tarfile(self.archivetempname)
            assert (not os.path.isfile(self.archivename) or
                        tarfile.is_tarfile(self.archivename))
            os.replace(self.archivetempname, self.archivename)
        except Exception as e:
            print(f"problem writing file ({str(e)})")
        return
    def __init__(self,outputdir,archivename,metadata_header=None,append=False):
        Buffered.__init__(self)
        if metadata_header:
            self.metadata_header=metadata_header
        else:
            self.metadata_header='file_name,sentence'
        self.ext="xz"
        archivename=os.path.join(outputdir,archivename)
        self.archivename=archivename+".tar."+self.ext
        self.archivetempname=f"{outputdir}/tmp_{getfilenamefrompath(self.archivename)}"
        self.metadataname="metadata.csv"
        self.hz=16000
        if append:
            self.append_archive()
        elif os.path.isfile(self.archivename):
            if tarfile.is_tarfile(self.archivename):
                print(f"Going to overwrite tarfile {self.archivename}")
            else:
                print(f"Going to overwrite non-tarfile {self.archivename}")
        self.open_archive()
def writefilename(filename=''):
    mgr = _app_settings()
    if mgr is None:
        return "writefilename: app settings not available."
    mgr.filename = filename
    return filename
if __name__ == "__main__":
    try: #Allow this module to be used without translation
        _
    except NameError:
        def _(x):
            return x
    files=[
        (r"C:\Users\camha\Documents\WeSay\bfj\audio\Verb-_HL_like_this_711e77ec-"
        "86ee-4c49-ba5b-2af75076798c_example_sɨ̀_pɛʼ_change_like_this_(IMP)_.wav"),
        (r"\audio\Verb-_HL_like_this_711e77ec-"
        "86ee-4c49-ba5b-2af75076798c_example_sɨ̀_pɛʼ_change_like_this_(IMP)_.wav"),
        (r"audio\Verb-_HL_like_this_711e77ec-"
        "86ee-4c49-ba5b-2af75076798c_example_sɨ̀_pɛʼ_change_like_this_(IMP)_.wav"),
        ("Verb-_HL_like_this_711e77ec-86ee-4c49-ba5b-2af75076798c_"
        "example_sɨ̀_pɛʼ_change_like_this_(IMP)_.wav"),
        ("/Users/camha/Documents/WeSay/bfj/audio/Verb-_HL_like_this_711e77ec-"
        "86ee-4c49-ba5b-2af75076798c_example_sɨ̀_pɛʼ_change_like_this_(IMP)_.wav"),
        ("/audio/Verb-_HL_like_this_711e77ec-"
        "86ee-4c49-ba5b-2af75076798c_example_sɨ̀_pɛʼ_change_like_this_(IMP)_.wav"),
        ("audio/Verb-_HL_like_this_711e77ec-"
        "86ee-4c49-ba5b-2af75076798c_example_sɨ̀_pɛʼ_change_like_this_(IMP)_.wav"),
        ("Verb-_HL_like_this_711e77ec-86ee-4c49-ba5b-2af75076798c_"
        "example_sɨ̀_pɛʼ_change_like_this_(IMP)_.wa"),
        (r":\Users\camha\Documents\WeSay\bfj\audio\Verb-_HL_like_this_711e77ec-"
        "86ee-4c49-ba5b-2af75076798c_example_sɨ̀_pɛʼ_change_like_this_(IMP)_.wav"),
        ("/home/kentr/Assignment/Tools/WeSay/bfj/audio/Verb-_HL_like_this_711e77ec-"
        "86ee-4c49-ba5b-2af75076798c_example_sɨ̀_pɛʼ_change_like_this_(IMP)_.wav")
        ]
    for i in files:
        print(i,"OK" if exists(i) else "doesn't exist on this filesystem")
    praat=findexecutable('praat')
# praatversioncheck(praat)
