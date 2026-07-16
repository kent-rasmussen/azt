#!/usr/bin/env python3
# coding=UTF-8
import io
import os
import tarfile
import soundfile
# No import cycle: file.py pulls file_sound in lazily (inside a function).
from utilities.file import (escapecommas, exists, getfilenamefrompath,
                            findexecutable)
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
                except Exception:
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
            # scipy, not librosa (librosa dropped 2026-07-16: its numba/
            # llvmlite dependencies are a recurring pip-resolution storm,
            # and scipy is already in the tree via transformers).
            from math import gcd
            from scipy.signal import resample_poly
            g=gcd(int(hz),int(self.samplerate))
            return resample_poly(self.read(), int(hz)//g,
                                 int(self.samplerate)//g)
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
# writefilename moved to utilities/file.py: it is not an audio function and
# must be available even when `soundfile` is absent (and it needs file._app_settings).
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
