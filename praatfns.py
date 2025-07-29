#!/usr/bin/env python3
# coding=UTF-8
import os #,sys
import re
import numpy
import parselmouth
import tgt #TextGridTools
import file
from tqdm import tqdm
import time

print('parselmouth.VERSION:',parselmouth.VERSION)
print('parselmouth.PRAAT_VERSION:',parselmouth.PRAAT_VERSION)

# parselmouth.praat.call #for things not yet implemented
def soundfile_info(sf):
    #type(sf),
    return (sf.n_channels, sf.sampling_frequency)
def camel_to_pascal(x):
    return x[0].upper()+x[1:]
class Align():
    def find_silences(self):
        def meets_threshold(x):
            # print(x,self.intensity_threshold,x>=self.intensity_threshold)
            return x>=self.intensity_threshold
        def array_overview(x):
            print('Not a Number items:',numpy.count_nonzero(numpy.isnan(x)))
            print('array shape',x.shape)
            print('array average',numpy.nanmean(x))
            print('array min',numpy.nanmin(x))
            print('array max',numpy.nanmax(x))
            trues=numpy.count_nonzero(x == True)
            falses=numpy.count_nonzero(x == False)
            print('trues',trues)
            print('falses',falses)
            print('trues:falses',trues/falses)
            print('n_samples',self.files.sound.n_samples,'?=',trues+falses,
            self.files.sound.n_samples==trues+falses,
            (trues+falses)/self.files.sound.n_samples)
        def next_threshold_2(n_found,target):
            d=abs(n_found > target)
            try:
                if d < best_delta:
                    best_delta=d
                    best_threshold=self.intensity_threshold
            except UnboundLocalError:
                best_delta=d
                best_threshold=self.intensity_threshold

        def next_threshold_1(n_found,target):
            if n_found > target:
                last_threshold_above_target=self.intensity_threshold
                try:
                    self.intensity_threshold=(last_threshold_below_target+
                                        self.intensity_threshold)/2
                except UnboundLocalError:
                    self.intensity_threshold/=2
            else:
                last_threshold_below_target=self.intensity_threshold
                try:
                    self.intensity_threshold=(last_threshold_above_target+
                                        self.intensity_threshold)/2
                except UnboundLocalError:
                    self.intensity_threshold*=1.5
        # p
        self.intensity=self.files.sound.to_intensity()
        hz=self.files.sound.sampling_frequency
        # print(self.intensity)
        # print(type(self.intensity))
        intensity_mean=self.intensity.get_average()
        self.files.audio_length()
        print('average intensity',intensity_mean)
        print('sampling_frequency',hz,'hz')
        # every sample of a ten minute 44k audio takes 30 seconds to parse
        # every 10 samples of a ten minute 44k audio takes 3 seconds to parse
        # every 100 samples of a ten minute 44k audio takes 0 seconds to parse
        print(f'sampling every {self.sample_each_n} samples, every '
            f'{1000*self.sample_each_n/hz} '
            'milliseconds')
        # These convert seconds to samples:
        start_at=int(self.untranscribed_intro*hz)
        end_at=int(self.files.sound.n_samples-self.untranscribed_epilogue*hz)
        print(f"Looking for sound gaps from {start_at} "
            f"({start_at/hz}s) to {end_at} "
            f"({end_at/hz//60}m "
            f"{end_at/hz%60}s)")
        self.intensity_threshold=intensity_mean/1.5 #start here
        self.intensity_threshold=intensity_mean/2 #start here
        self.threshold_resolution=self.intensity_threshold/100
        print('sound threshold',self.intensity_threshold)
        print(f"Looking for silence of {self.silence_to_find_in_s} seconds")
        n_to_find=int(self.silence_to_find_in_s*hz/self.sample_each_n)
        print(f"Looking for {n_to_find} zeros in a row")
        silence_regex='(?<!^)0{'+str(n_to_find)+'}0*(?!$)'
        any_silence_regex='0*'
        final_silence_regex=any_silence_regex+'$'
        intensity_vector=numpy.array([
            self.intensity.get_value(
                time=self.sample_each_n*(start_at+i)/hz)
                # for i in tqdm(range(self.files.sound.n_samples//self.sample_each_n))
                for i in tqdm(range((end_at)//self.sample_each_n))
            ])
        min=numpy.nanmin(intensity_vector)
        max=numpy.nanmax(intensity_vector)
        print(f"Intensity ranges from {min} to {max}")
        print('intensity_vector',intensity_vector[15:-15])
        target=len(self.texts_to_align)-1
        print(f"Looking for {target} sound gaps")
        while True:
            if not min <= self.intensity_threshold <= max:
                print(f"intensity threshold {self.intensity_threshold} "
                    "out of bounds; exiting")
                exit()
            threshold_vector=numpy.array([meets_threshold(i)
                                        # for i in tqdm(intensity_vector)
                                        for i in intensity_vector
                                    ])
            threshold_vector=''.join([str(int(i)) for i in threshold_vector])
            # print('threshold_vector',threshold_vector[15:-15])
            g=re.finditer(silence_regex,threshold_vector)
            self.silence_found=list(g)
            n_found=len(self.silence_found)
            print(f"at threshhold {self.intensity_threshold:.2f}: {n_found} "
                "matches found")
            # exit()
            if n_found == target:
                # print("Looks good:")
                # for m in found:
                #     print(tuple([(i)*self.sample_each_n for i in m.span()]))
                break
            else:
                next_threshold_1(n_found,target)
        #Convert back to absolute samples:
        self.silence_boundaries=[tuple(start_at+i*self.sample_each_n for i in j.span())
                                        for j in self.silence_found]
        self.sound_begins=(re.match(any_silence_regex,threshold_vector
                                    ).span()[1]+start_at)*self.sample_each_n
        self.sound_ends=(re.search(final_silence_regex,threshold_vector
                                    ).span()[0]+start_at)*self.sample_each_n
        print("Sound from",self.sound_begins,"to",self.sound_ends)
        # for t in tqdm(range(self.files.sound.n_samples)):
        #     print(self.intensity.get_value(time=t/hz))
    def silence_to_tier_annotations(self):
        assert len(self.silence_boundaries) == len(self.files.plaintext.clauses) -1
        # for num in [self.silence_boundaries,self.files.plaintext.clauses]:
        #     print(num[:5])
        tier=self.files.textgrid.add_tier(self.tier_name+
                                            f'x{self.sample_each_n}')
        hz=self.files.sound.sampling_frequency
        for n,clause_text in enumerate(self.files.plaintext.clauses):
            if n:
                start=self.silence_boundaries[n-1][1]/hz
            else:
                start=self.sound_begins/hz
            if n == len(self.files.plaintext.clauses) -1:
                end=self.sound_ends/hz
            else:
                end=self.silence_boundaries[n][0]/hz
            try:
                tier.add_interval(start,
                                    end_time=end,
                                    text=clause_text)
                # print(len(tier.intervals),'intervals')
            except IndexError as e:
                if n:
                    print(f"Exception: {e}")
            except TypeError as e:
                pass
    def __init__(self,file_name,**kwargs):
        # super().__init__(file_name=file_name, **kwargs)
        self.files=Files(file_name)
        if not hasattr(self.files,'sound'):
            print("Missing sound file; can't continue!")
        if not hasattr(self.files,'plaintext'):
            print("Missing text file with whole text transcription!")
        self.textgrid_name=self.files.file_w_ext('TextGrid')
        if (not os.path.isfile(self.textgrid_name) or
                        not os.path.getsize(self.textgrid_name)):
            print(f"Will write to {self.textgrid_name}, which isn't there yet.")
            self.files.start_textgrid(self.textgrid_name)
        else:
            print(f"Will write to {self.textgrid_name}, adding tiers.")
            self.files.read_textgrid(self.textgrid_name)
        # self.untranscribed_intro=7.5
        # self.untranscribed_epilogue=4.0
        self.untranscribed_intro=kwargs.get('untranscribed_intro')
        self.untranscribed_epilogue=kwargs.get('untranscribed_epilogue')
        if self.untranscribed_intro:
            print(f"Going to skip the first {self.untranscribed_intro} seconds "
                "of untranscribed audio")
        else:
            self.untranscribed_intro=0
        if self.untranscribed_epilogue:
            print(f"Going to skip the last {self.untranscribed_epilogue} "
                "seconds of untranscribed audio")
        else:
            self.untranscribed_epilogue=0
        self.texts_to_align=getattr(self.files.plaintext,self.attr_to_align)
        self.tier_name=f'{self.attr_to_align}__auto'
        for self.sample_each_n in [100,10,1]:
            self.find_silences()
            self.silence_to_tier_annotations()
        self.files.textgrid.write()
class AlignWords(Align):
    def __init__(self,file_name,**kwargs):
        self.silence_to_find_in_s=.075 #100 miliseconds
        self.attr_to_align='words'
        super().__init__(file_name=file_name, **kwargs)
class AlignClauses(Align):
    def __init__(self,file_name,**kwargs):
        self.silence_to_find_in_s=.2 #200 miliseconds
        self.attr_to_align='clauses'
        super().__init__(file_name=file_name, **kwargs)
class IntervalTier(tgt.core.IntervalTier):
    def add_interval(self,start_time, end_time, text):
        try:
            i=tgt.core.Interval(start_time, end_time, text)
            tgt.core.IntervalTier.add_interval(self,i)
            return i
        except ValueError:
            print("Failed to make interval",start_time, end_time, text)
    def __init__(self,name,**kwargs):
        super().__init__(name=name, **kwargs)
class TextGrid(tgt.core.TextGrid):
    def write(self,**kwargs):
        tgt.io.write_to_file(self, self.filename,
                            # format='short',
                            format='long',
                            encoding='utf-8',
                            **kwargs)
    def add_tier(self,tier_name):
        tier=IntervalTier(tier_name)
        tgt.core.TextGrid.add_tier(self,tier)
        return tier
    def __init__(self,file_name,**kwargs):
        try:
            tgt_text_grid=tgt.io.read_textgrid(file_name)
        except UnicodeDecodeError:
            tgt_text_grid=tgt.io.read_textgrid(file_name,encoding='utf-16')
        except FileNotFoundError:
            tgt_text_grid=tgt.core.TextGrid(file_name)
        super().__init__(filename=file_name, **kwargs)
        for tier in tgt_text_grid.tiers:
            self.add_tier(tier.name)
            self.get_tier_by_name(tier.name).add_annotations(tier.annotations)
            print(tier.name)
            if self.has_tier(tier.name):
                print(f"Tier ‘{tier.name}’ is already there!")
                print("Won't add "
                f"{len(tier.annotations)} "
                "annotations (first 5: "
                f"{[i.text for i in tier.annotations[:5]]})")
            else:
                print(f"Tier ‘{tier.name}’ not there, adding!")
                self.add_tier(tier.name)
                self.get_tier_by_name(tier.name).add_annotations(tier.annotations)
            print("Done with",tier.name)
class TextFile():
    def get_lines(self):
        self.lines=self.text.split('\n')
    def get_sentences(self):
        self.sentences=self.text.split('.')
    def get_words(self):
        regex='|'.join(['\\'+i if i in ['?','.','-',' '] else i
                            for i in self.word_breaks])
        # print(regex)
        self.words=re.split(regex, self.text)
    def get_clauses(self):
        regex='|'.join(['\\'+i if i in ['?','.','-'] else i
                            for i in self.clause_breaks])
        # print(regex)
        self.clauses=re.split(regex, self.text)
    def info(self):
        self.get_clauses()
        self.get_words()
        return (
            f"Found {len(self.words)} words and {len(self.clauses)} clauses."
            )
    def info_long(self):
        # self.get_lines()
        # self.get_sentences()
        self.get_clauses()
        self.get_words()
        # print(len(lines))
        # print(len(sentences))
        return (
            f"Found {len(self.words)} words. First five(5):"
                f"\n{'\n'.join(self.words[:5])}\n"
            f"Found {len(self.clauses)} clauses. First five(5):"
                f"\n{'\n'.join(self.clauses[:5])}"
            )
    def normalize_text(self):
        counts={}
        for i in self.clause_breaks:
            self.text=i.join([self.clean_text(j) for j in self.text.split(i) if j])
            counts[i]=len(self.text.split(i))
        # print(f"Found {counts}")
        # print("Done normalizing text")
    def clean_text(self,x):
        return x.strip('1234567890 ')
    def __init__(self, **kwargs): #including file_name:str
        file_name=kwargs.get('file_name')
        assert os.path.isfile(file_name)
        # print(f"opening TextFile {file_name}")
        if kwargs.get('clause_breaks'):
            self.clause_breaks=kwargs.get('clause_breaks')
        else:
            self.clause_breaks=['.',',',':',';','–','--','\n','?']
        if kwargs.get('word_breaks'):
            self.word_breaks=kwargs.get('word_breaks')
        else: #some people miss spaces after clause markers...
            self.word_breaks=self.clause_breaks+[' ','-']
        with open(file_name,'r') as f:
            self.text=f.read()
        self.normalize_text()
class Files():
    def audio_length(self):
        l=self.sound.n_samples/self.sound.sampling_frequency
        m=int(l//60)
        s=l%60
        print("sound file length",'is',m,'minutes',s,'seconds')
    def soundfile_info(self):
        return soundfile_info(self.sound)
    def textgrid_info(self):
        # self.textgrid,
        return {i.name:len(i.annotations) for i in self.textgrid.tiers}
    def file_w_ext(self,ext):
        return os.path.splitext(self.file_name)[0]+f'.{ext}'
    def read_soundfile(self,file=None):
        if not file:
            file=self.file_name
        self.sound = parselmouth.Sound(file)
        print(f"Sound file {file} loaded {self.soundfile_info()}")
    def start_textgrid(self,file):#, encoding='UTF-16'
        self.textgrid=TextGrid(file)
        print(f"Textgrid file {file} started; tiers:annotations {self.textgrid_info()}.")
    def read_textgrid(self,file=None):#, encoding='UTF-16'
        if not file:
            file=self.file_name
        self.textgrid=TextGrid(file)
        print(f"Textgrid file {file} loaded; tiers:annotations {self.textgrid_info()}.")
    def read_plaintext(self,file=None):
        if not file:
            file=self.file_name
        # print(f"Looking for {file}")
        self.plaintext=TextFile(**{**self.kwargs,'file_name':file}) #file,
        print(f"Plaintext file {file} loaded; {self.plaintext.info()}")
    def try_x_file_options(self,x):
        # ext_options should always be a double iterable:
        for e in [j for k in self.filetypes[x]['ext_options'] for j in k]:
            try:
                lookingfor=self.file_w_ext(e)
                #move on if not there
                assert os.path.isfile(lookingfor) #analogous; raise if not text
                self.filetypes[x]['fn'](lookingfor)
                break
            except Exception as e:
                if len(e.args):
                    print(f"Exception {type(e)}: {e}")
                pass
    def parse_file_name(self):
        try: # Is file_name a sound file?
            self.read_soundfile() #self.file_name
            self.try_x_file_options('textgrid')
            self.try_x_file_options('plaintext')
            # print("Input was sound file")
        except parselmouth.PraatError: # maybe file_name is a textgrid?
            self.read_textgrid()
            self.try_x_file_options('sound')
            self.try_x_file_options('plaintext')
            # print("Input was textgrid file")
        # if hasattr(self,'plaintext'):
        #     print("plain text file available.")
        # else:
        #     print("plain text file NOT available.")
    def __init__(self, file_name:str, **kwargs):
        self.kwargs=kwargs
        try:
            self.file_name=file_name
            assert os.path.exists(self.file_name),"doesn't exist"
            self.datadir=os.path.dirname(self.file_name)
            # 'not' in case working in local directory
            assert not self.datadir or os.path.isdir(self.datadir),"is a directory"
        except Exception as e:
            print(f"File {file_name} {e}.")
            exit()
        # ext_options should always be a double iterable
        self.filetypes={
            'sound':{'ext_options':[(i,i.title(),i.upper())
                                    for i in ['wav','mp3']],
                    'fn':self.read_soundfile
                    },
            'textgrid': {'ext_options':[(i,i.title(),camel_to_pascal(i),
                                        i.upper(),i.lower())
                                        for i in ['textGrid']],
                        'fn':self.read_textgrid
                        },
            'plaintext': {'ext_options':[(i,i.title(),i.upper())
                                        for i in ['txt']],
                        'fn':self.read_plaintext
                        },
                    }
        self.parse_file_name()
class ExtractToArchive():
    def init_tarball(self,metadata_header=None,append=False):
        self.tarball=file.TarBall(os.path.splitext(
                                self.files.textgrid.filename)[0],
                                metadata_header=metadata_header,append=append)
    def finish_tarball(self):
        self.tarball.writeout()
    def get_text_in_annotation_times(self,tier_name,start,end):
        tier=self.files.textgrid.get_tiers_by_name(tier_name)
        # print(tier)
        # print(tier[0].intervals)
        interval=self.files.textgrid.get_tiers_by_name(tier_name
                    )[0].get_annotations_by_time((start+end)/2)
                # )[0].get_annotations_between_timepoints(start,end)
        # print(interval[0].start_time)
        # print(interval[0].end_time)
        # print(interval[0].text)
        try:
            return interval[0].text
        except:
            return ''
        # print(tier_name,tier_text)
        # print(tier_text)
    def get_tier(self,tier_name):
        if tier_name in self.files.textgrid.get_tier_names():
            tier=self.files.textgrid.get_tier_by_name(tier_name)
        elif tier_name:
            print(f"Tier {tier_name} not in {self.files.textgrid.tiers}")
            exit()
        elif len(self.files.textgrid.tiers) == 1:
            tier=self.files.textgrid.tiers[0]
        elif [i for i in self.files.textgrid.get_tier_names()
                                    if 'clauses' in i or 'words' in i]:
            for t in ['clauses','words']:
                try:
                    tier=self.files.textgrid.get_tier_by_name(
                    [i for i in self.files.textgrid.get_tier_names() if t in i]
                                                        )[0]
                    break
                except:
                    pass
        else:
            print("Please specify a tier name (-t) in "
                    f"{self.files.textgrid.get_tier_names()}")
            exit()
        return tier
    def __init__(
        self:'ExtractToArchive',
        # file_name:str,
        # tier_name:str,
        **kwargs) -> 'ExtractToArchive':
        # keep_other_tiers:bool=False,
        # make_soundfiles:bool=False,
        # make_subtitles:bool=False) -> 'ExtractToArchive':
        # print(kwargs)
        # file_name=kwargs.get('file_name')
        # self.file_name=kwargs.get('file_name')
        self.files=Files(**kwargs)
        tier=self.get_tier(kwargs.get('tier_name'))
        tier_name=tier.name
        if kwargs.get('keep_other_tiers'):
            other_tier_order=[i for i in self.files.textgrid.get_tier_names()
                                if i != tier_name]
            # print(other_tier_order)
            metadata_header=','.join(['file_name','sentence']+other_tier_order)
            self.init_tarball(metadata_header=metadata_header)
        else:
            self.init_tarball()
        sound_dict={}
        out_format=parselmouth.SoundFileFormat('WAV')
        for n,annotation in enumerate(tier.annotations):
            annotation.text=annotation.text.strip('1234567890 ')
            print(f"tier {tier_name} annotation number {n}: "
                f"start:{annotation.start_time} "
                f"end: {annotation.end_time} text: {annotation.text}")
            this_sound=self.files.sound.extract_part(
                                                from_time=annotation.start_time,
                                                to_time=annotation.end_time
                                                ).resample(new_frequency=16000
                                                ).convert_to_mono()
            # print(os.path.splitext(self.textgrid.filename))
            this_sound_name=(f'{os.path.splitext(
                                self.files.textgrid.filename)[0]}-'
                                f'{annotation.start_time}s.wav') #x seconds
            if kwargs.get('make_soundfiles'):
                this_sound.save(file_path=str(this_sound_name),
                                format=out_format)
            if kwargs.get('make_subtitles'):
                with open(os.path.splitext(this_sound_name)[0]+'.srt','w') as f:
                    f.write(f"0 --> {annotation.end_time-annotation.start_time}"
                            f"\n{annotation.text}\n")
            self.tarball.addsoundobject(this_sound,this_sound_name,out_format)
            texts=[annotation.text]
            if kwargs.get('keep_other_tiers'):
                for other_tier_name in other_tier_order:
                    text=self.get_text_in_annotation_times(other_tier_name,
                                                        annotation.start_time,
                                                        annotation.end_time)
                    texts+=[text]
                    # print(other_tier_name,text)
                    # print('filing:',texts)
            self.tarball.add_to_metadata(this_sound_name,*texts)
        self.finish_tarball()

if __name__ == '__main__':
    import argparse
    p=argparse.ArgumentParser(prog="Python Functions for Praat",
        description="This script takes a Praat textgrid or sound file as input."
                    "\nIf both are needed for a function, the other should "
                    "share the whole name, except extension. \n"
                    "MAKE ARCHIVE cuts the sound file according to "
                    "annotations on the selected textgrid tier, then saves "
                    "sound files and a metadata.csv file to a "
                    "<filename>.tar.xz compressed archive "
                    "in the same folder. This is the file "
                    "that will be used for ASR training.\n"
                    "ALIGN CLAUSES takes a sound file and a text "
                    "transcription file, and writes out a textgrid with draft "
                    "alignment of the sound file, according to clauses, "
                    "currently understood as orthographic periods, semicolons, "
                    "and m dashes(—).\n"
                    "Either function can output an srt file(s) for the new "
                    "sound files or textgrid."
                        )
    p.add_argument('file_name',help="name of the file (audio or textgrid)")
    p.add_argument('-t','--tier-name',
                    help="name of the textgrid tier with translations, "
                            "also to cut the soundfile",
                    required=False,
                    # dest='tier_name'
                    )
    p.add_argument('-m','--make-subtitles',
                    help="output textgrid content to srt files",
                    required=False,
                    action='store_true'
                    )
    p.add_argument('-A','--make-archive',
                    help="**Sound+Textrid --> Archive**  \n"
                    "Split sound with textgrid according to annotations "
                    "on a given textgrid tier, the put all files in a "
                    "<filename>.tar.xz compressed archive, along "
                    "with metadata.csv containing tier information by "
                    "sound file. This is the file "
                    "that will be used for ASR training.",
                    action='store_true'
                )
    p.add_argument('-k','--keep-other-tiers',
                    help="output text from other tiers "
                        "into other metadata columns "
                        "(each named after one tier)",
                    required=False,
                    action='store_true'
                    )
    p.add_argument('-s','--make-soundfiles',
                    help="output sound files (outside the archive)",
                    required=False,
                    action='store_true'
                    )
    p.add_argument('-C','--align-clauses',
                    help="**Sound+Text --> Textgrid**  \n"
                    "Split sound into a new Texgrid according to orthographic "
                    "clause boundaries",
                    action='store_true'
                )
    p.add_argument('-c','--clause-breaks',
                    help="Orthographic clause boundary markers. Use once for "
                    "each orthographic marker that you want to separate text "
                    "at clause level pauses",
                    action='append'
                )
    p.add_argument('-W','--align-words',
                    help="**Sound+Text --> Textgrid**  \n"
                    "Split sound into a new Texgrid according to orthographic "
                    "word boundaries",
                    action='store_true'
                )
    p.add_argument('-w','--word-breaks',
                    help="Orthographic word boundary markers. Use once for "
                    "each orthographic marker that you want to separate text "
                    "at word level pauses",
                    action='append'
                )
    p.add_argument('-a','--untranscribed-intro',
                    help="Number of seconds at the beginning of audio "
                    "not present in transcription",
                    type=float
                    # action='append'
                )
    p.add_argument('-z','--untranscribed-epilogue',
                    help="Number of seconds at the end of audio "
                    "not present in transcription",
                    type=float
                    # action='append'
                )
    kwargs=vars(p.parse_args())

    if kwargs.get('align_clauses'):
        AlignClauses(
                    # file_name=file_name
                    **kwargs)
    if kwargs.get('align_words'):
        AlignWords(
                    # file_name=file_name
                    **kwargs)
    if kwargs.get('make_archive'):
        ExtractToArchive(
                    # file_name=file_name,
                    # tier_name=kwargs.pop('tier'),
                    **kwargs) #TextGrid
    if not (kwargs.get('align_clauses') or kwargs.get('align_words') or
            kwargs.get('make_archive')):
        p.print_help()
        print()
        print("Please select at least one of 'align_clauses', 'align_words', "
            "or 'make_archive'")
