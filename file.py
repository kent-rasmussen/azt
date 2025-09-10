#!/usr/bin/env python3
# coding=UTF-8
from tkinter import filedialog
from tkinter import Tk
import pathlib
import os
import stat
import platform
import soundfile
import samplerate
import io
import tarfile
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
def quote(x):
    x=str(x) #going to return a string anyway
    if '"' not in x:
        return '"'+x+'"'
    elif "'" not in x:
        return "'"+x+"'"
    else:
        log.error("Looks like ˋ{}ˊ contains single and double quotes!".format(x))
def getfile(filename):
    if filename:
        return pathlib.Path(filename)
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
def getexportdir(dirname):
    dir=pathlib.Path.joinpath(dirname,'exports')
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
            return samplerate.converters.resample(self.read(),
                hz/self.samplerate)
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
                        print(f"Found metadata file ‘{self.metadataname}’ with "
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
            else:
                log.info(f"skipping {t}")
        self.writeout()
        log.info(f"Added {n} rows of data to {self.archivename}" )
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
    filenames=[]
    try:
        import lift_url
        if hasattr(lift_url,'filenames') and lift_url.filenames:
            filenames=lift_url.filenames
    except:
        log.error("writefilename lift_url didn't import.")
    if filename and str(filename) not in filenames:
        filenames.append(str(filename))
    file=pathlib.Path.joinpath(pathlib.Path(__file__).parent, "lift_url.py")
    f = open(file, 'w', encoding='utf-8') # to append, "a"
    f.write('filename="'+str(filename)+'"\n')
    f.write('filenames='+str(filenames)+'\n')
    f.close()
    return filename
if __name__ == "__main__":
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
        "86ee-4c49-ba5b-2af75076798c_example_sɨ̀_pɛʼ_change_like_this_(IMP)_.wav")
        ]
    for i in range(len(files)):
        print(compare_paths(files[i],files[i]))
    exit()
    import itertools
    # p_list=list(itertools.permutations(files,2))
    p_list=list(itertools.combinations(files,2))
    for x,y in p_list:
        in_it=compare_paths(x,y)
        if in_it:
            print(files.index(x),files.index(y),in_it,'\n',
                    [i for i in [x,y] if i != str(in_it)],'\n')
    #     print("Good Windows paths")
    #
    # print("Good Linux paths")
    #
    # print(compare_paths(file3,file2))
    # print("Good Windows path w/incomplete filename")
    #
    # print(compare_paths(file1,file4))
    # print("Bad Windows path w/complete filename")
    # print(compare_paths(file5,file2))
    exit()
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
