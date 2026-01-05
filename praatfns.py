#!/usr/bin/env python3
# coding=UTF-8
import logsetup
log=logsetup.getlog(__name__)
logsetup.setlevel('INFO',log) #for this file
import os #,sys
import re
import numpy
import parselmouth
import tgt #TextGridTools
import file
from tqdm import tqdm
import time
try: #translation
    _
except NameError:
    def _(x):
        return x

print('parselmouth.VERSION:',parselmouth.VERSION)
print('parselmouth.PRAAT_VERSION:',parselmouth.PRAAT_VERSION)

# parselmouth.praat.call #for things not yet implemented
def soundfile_info(sf):
    #type(sf),
    return (sf.n_channels, sf.sampling_frequency)
def camel_to_pascal(x):
    return x[0].upper()+x[1:]
class Align():
    def remove_less_than_one_word(self):
        hz=self.files.sound.sampling_frequency
        n_to_find=int(self.one_word*hz/self.sample_each_n)
        # print("Last silence ends at "
        #         f"{self.silence_found[-1][1]*self.sample_each_n/hz}s")
        for n,i in enumerate(self.silence_found):
            # print(n,i)
            if n: #not on first
                # print(n-1,n,self.silence_found[n-1],i)
                utterance_length=i[0]-self.silence_found[n-1][1]
                utterance_length_s=utterance_length*self.sample_each_n/hz
                utterance_end_s=i[0]*self.sample_each_n/hz
                if utterance_length<n_to_find:
                    # print(f"Item {n} not long enough: "
                    #     f"{i[0]}—{self.silence_found[n-1][1]}"
                    #     f"({utterance_length}={utterance_length_s}, "
                    #     f"ending at {utterance_end_s}s); removing.")
                    self.silence_found[n-1]=(self.silence_found[n-1][0],
                                            self.silence_found[n][1])
                    self.silence_found.pop(n)
                    # exit()
    def remove_silence_without_falling_pitch(self):
        hz=self.files.sound.sampling_frequency #sampling, not pitch
        # print("Last silence ends at "
        #         f"{self.silence_found[-1][1]*self.sample_each_n/hz}s")
        #don't modify the list over which we're iterating:
        #remove from the end, so indexes are preserved:
        silence_found_ori=self.silence_found.copy()
        n_silences_ori=len(silence_found_ori)
        silence_found_ori.reverse()
        for n,i in enumerate(silence_found_ori):
            # print(f"Silence {n} of {len(silence_found_ori)}")
            if 0<n<len(silence_found_ori)-1: #not on first or last; file ends.
                # get_number_of_frames
                # print(f"Looking for sound in "
                #     f"{self.silence_found[n-1][1]} "
                #     f"({self.silence_found[n-1][1]*self.sample_each_n/hz}s)"
                #     f" to {i[0]} ({i[0]*self.sample_each_n/hz}s)")
                # print(f"Looking for sound in "
                #     f"{i[1]} "
                #     f"({i[1]*self.sample_each_n/hz}s)"
                #     f" to {self.silence_found[n+1][0]} "
                #     f"({self.silence_found[n+1][0]*self.sample_each_n/hz}s)")
                # print(f"Looking for sound in {i[1]} to {self.silence_found[n+1][0]}")
                # print(f"Pitch samples: {len(self.pitches_sampled)}")
                self.pitches_sampled.time_to_frame_number
                #self.pitches_sampled and self.silence_found have the same sampling
                previous=next=numpy.nan
                j=i[0]
                while numpy.isnan(previous) and j>=silence_found_ori[n+1][1]:
                    # previous=self.pitches_sampled.get_value_in_frame(j)
                    # p_sampled_time=self.pitches_sampled.frame_number_to_time(j)
                    p_sampled_time=j*self.sample_each_n/hz
                    previous=self.pitches_sampled.get_value_at_time(p_sampled_time)
                    # print("Previous pitch:",previous)
                    j-=1 #frame number goes down
                j=i[1]
                # print(silence_found_ori[n-1])
                # print(silence_found_ori[n])
                # print(silence_found_ori[n+1])
                # print(silence_found_ori[n+1][0])
                while (numpy.isnan(next) and
                        # n==len(silence_found_ori) or
                        j<=silence_found_ori[n-1][0]):
                    # next=self.pitches_sampled.get_value_in_frame(j)
                    # n_sampled_time=self.pitches_sampled.frame_number_to_time(j)
                    n_sampled_time=j*self.sample_each_n/hz
                    next=self.pitches_sampled.get_value_at_time(n_sampled_time)
                    # print("Next pitch:",next)
                    j+=1 #frame number goes up
                # print("Previous pitch:",previous)
                # print("Next pitch:",next)
                if next-previous<self.new_breath_pitch_rise_min:
                    print("Silence starting at "
                        f"{i[0]*self.sample_each_n/hz:.1f}s raises "
                        f"{next-previous:.1f}hz (from "
                        f"{previous:.1f}hz @{p_sampled_time:.1f}s to "
                        f"{next:.1f}hz @{n_sampled_time:.1f}s), so "
                        "doesn't seem like a breath reset; removing.")
                    # print(f"Going to remove {-(n+1)} of "
                    #         f"{len(self.silence_found)} items")
                    self.silence_found.pop(n_silences_ori-(n+1))
                # print(f"Previous Pitches: {previous[20:]}")
                # print(f"Next Pitches: {next[:20]}")
                # exit()
    def find_pitches(self):
        print("finding pitches")
        # to_pitch_ac
        # to_pitch
        # to_pitch_cc
        # to_pitch_shs
        # to_pitch_spinet
        self.pitches_sampled=self.files.sound.to_pitch(
            time_step=self.sample_each_n/self.files.sound.sampling_frequency,
            pitch_floor=50.0,#: Positive[float] = 75.0,
            pitch_ceiling=800.0,#: Positive[float] = 600.0
            # max_number_of_candidates: Positive[int] = 15,
            # very_accurate: bool = False,
            # silence_threshold: float = 0.03,
            # voicing_threshold: float = 0.45,
            # octave_cost: float = 0.01,
            # octave_jump_cost: float = 0.35,
            # voiced_unvoiced_cost: float = 0.14
            )
        print("found pitches")
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
        def next_threshold_2(n_found):
            d=abs(self.intensity_dict[self.intensity_threshold] - self.target)
            try:
                if d < best_delta:
                    best_delta=d
                    best_threshold=self.intensity_threshold
            except UnboundLocalError:
                best_delta=d
                best_threshold=self.intensity_threshold
        def next_threshold_1():
            if self.intensity_dict[self.intensity_threshold] > self.target:
                last_threshold_above_target=self.intensity_threshold
                try:
                    self.intensity_threshold=(last_threshold_below_target+
                                        self.intensity_threshold)/2
                except UnboundLocalError:
                    self.intensity_threshold/=1.5
            else:
                last_threshold_below_target=self.intensity_threshold
                try:
                    self.intensity_threshold=(last_threshold_above_target+
                                        self.intensity_threshold)/2
                except UnboundLocalError:
                    self.intensity_threshold*=1.25
            print(f"Working with {self.possible_range[1]} and "
                    f"{self.intensity_threshold}")
            self.intensity_threshold=numpy.min(numpy.array(
                                        [self.possible_range[1],
                                        self.intensity_threshold]))
            self.intensity_threshold=numpy.max(numpy.array(
                                        [self.possible_range[0],
                                        self.intensity_threshold]))
        def switch_ranges():
            lower_range=self.intensity_threshold<self.intensity_high_range[0]
            print(f"Switching ranges (to High:{lower_range}, "
                f"{self.intensity_threshold}<{self.intensity_high_range[0]})")
            self.intensity_threshold=(
                self.intensity_high_range[int(lower_range)
                    ]+self.possible_range[int(lower_range)]
                                        )/2
        def next_threshold_normal():
            # if low update possible range
            if not self.intensity_high_range:
                return next_threshold_1()
            # if not len(self.intensity_dict.keys())%5:
            #     switch_ranges()
            #     return
            self.upper_range=self.intensity_threshold>=self.intensity_high_range[1]
            print("self.upper_range:",self.upper_range,
                                    self.intensity_threshold,
                                    self.intensity_high_range[1])
            # if (self.upper_range and self.upper_range_done) or (
            #     not self.upper_range and self.lower_range_done):
            if self.upper_range:
                switch_ranges()
                return
            # print(f"self.intensity_high_range[{int(upper_range)}]:",self.intensity_high_range[int(upper_range)])
            # print("self.intensity_high_range:",self.intensity_high_range)
            # print("self.possible_range:",self.possible_range)
            # print(f"self.possible_range[{int(upper_range)}]:",self.possible_range[int(upper_range)])
            # print("self.intensity_threshold:",self.intensity_threshold)
            r=sorted([self.possible_range[int(self.upper_range)],
                    self.intensity_high_range[int(self.upper_range)]])
            print(f"looking for {self.intensity_threshold} in range {r}, "
                f"found {self.intensity_dict[self.intensity_threshold]} "
                f"(need {self.target})"
                )
                # upper_range=True
            if self.intensity_dict[self.intensity_threshold] > self.target:
                self.intensity_threshold=(
                    self.intensity_threshold+self.possible_range[
                                    int(self.upper_range)]
                                        )/2
            elif self.intensity_dict[self.intensity_threshold] < self.target:
                self.possible_range[int(self.upper_range)
                                    ]=self.intensity_threshold
                self.intensity_threshold=(
                    self.intensity_threshold+self.intensity_high_range[
                                    int(self.upper_range)]
                                        )/2
            else:
                print(f"Huh? ({self.intensity_threshold}, looking for "
                    f"{self.target} in {self.intensity_dict})")
            # self.silence_found=
        hz=self.files.sound.sampling_frequency
        self.intensity=self.files.sound.to_intensity(time_step=self.sample_each_n/hz)
        print("Intensity length:",len(self.intensity),len(self.intensity)/hz)
        self.intensity.subtract_mean()
        print("Intensity length:",len(self.intensity),len(self.intensity)/hz)
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
        start_at=int(self.untranscribed_intro*hz/self.sample_each_n)
        end_at=int((self.files.sound.n_samples-self.untranscribed_epilogue*hz
                    )/self.sample_each_n)
        print(f"Looking for sound gaps from {start_at} "
            f"({start_at*self.sample_each_n/hz}s) to {end_at} "
            f"({end_at*self.sample_each_n/hz//60}m "
            f"{end_at*self.sample_each_n/hz%60}s)")
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
        # print("self.intensity:",type(self.intensity))
        # print("self.intensity.TimeFrameSampled:",isinstance(self.intensity,parselmouth.TimeFrameSampled))
        # print("self.intensity.Vector:",isinstance(self.intensity,parselmouth.Vector))
        # quit()
        # for i in tqdm(range((end_at)//self.sample_each_n)):
        #     print(self.intensity.get_value(
        #         time=self.sample_each_n*(start_at+i)/hz))
        #     print(self.sample_each_n*(start_at+i)/hz)
        #     print(self.sample_each_n*(start_at+i))
        #     print(self.sample_each_n*(i))
        # intensity_vector=numpy.array([
        #     self.intensity.get_value(
        #         time=(start_at+self.sample_each_n*i)/hz,
        #         # interpolation="ENERGY"
        #         )# for i in tqdm(range(self.files.sound.n_samples//self.sample_each_n))
        #         for i in tqdm(range(start_at//self.sample_each_n,
        #                             end_at//self.sample_each_n))
        #     ])
        print("Intensity length:",len(self.intensity),len(self.intensity)/hz)
        intensity_vector=self.intensity.as_array().T
        # intensity_vector.flip()
        print(type(intensity_vector))
        print(intensity_vector.shape)
        min=numpy.nanmin(intensity_vector)
        max=numpy.nanmax(intensity_vector)
        self.possible_range=[min,max]
        print(f"Intensity ranges from {min} to {max}")
        # print('intensity_vector',intensity_vector[15:-15])
        self.target=len(self.texts_to_align)+1
        print(f"Looking for {self.target} sound gaps")
        self.intensity_dict={}
        self.find_pitches() #just once
        while True:
            if not min <= self.intensity_threshold <= max:
                print(f"intensity threshold {self.intensity_threshold} "
                    "out of bounds; exiting")
                exit()
            threshold_vector=numpy.array([meets_threshold(i)
                                        # for i in tqdm(intensity_vector)
                                        for i in intensity_vector
                                    ])
            threshold_vector[:start_at]=0
            threshold_vector[end_at:]=0
            # print("threshold_vector shape:",threshold_vector.shape)
            # print("threshold_vector length:",threshold_vector.shape[0],
            #         f"({threshold_vector.shape[0]*self.sample_each_n/hz}s)")
            threshold_vector=''.join([str(int(i)) for i in threshold_vector.T[0]])
            # print("threshold_vector ends at "
            #         f"{len(threshold_vector)*self.sample_each_n/hz}s")
            # print('threshold_vector',threshold_vector[15:-15])
            g=re.finditer(silence_regex,threshold_vector)
            self.silence_found=[i.span() for i in g]
            n_total=len(self.silence_found)
            print(f"first pass: {len(self.silence_found)}")
            self.remove_less_than_one_word()
            print(f"after remove_less_than_one_word: {len(self.silence_found)}")
            # n_found=len(self.silence_found)
            self.remove_silence_without_falling_pitch()
            print(f"after remove_silence_without_falling_pitch: {len(self.silence_found)}")
            n_found=len(self.silence_found)
            print(f"at threshhold {self.intensity_threshold:.2f}: {n_found} "
                f"matches found (of {n_total} total)")
            if self.intensity_threshold in self.intensity_dict:
                print(f"Giving up, having tried (to find {self.target}) "
                        "this:\n", self.intensity_dict)
                quit()
            self.intensity_dict[self.intensity_threshold]=n_found
            # exit()
            if n_found == self.target:
                # print("Looks good:")
                # for m in found:
                #     print(tuple([(i)*self.sample_each_n for i in m.span()]))
                break
            else:
                self.intensity_high_items=[i for i in list(self.intensity_dict)
                                            if self.intensity_dict[i]>self.target]
                if self.intensity_high_items:
                    # print(self.intensity_high_items)
                    self.intensity_high_range=(
                                    numpy.nanmin(self.intensity_high_items),
                                    numpy.nanmax(self.intensity_high_items))
                else:
                    self.intensity_high_range=False
                next_threshold_normal()
        #Convert back to absolute samples:
        # print("self.silence_found[:5]",[i.span() for i in self.silence_found[:5]
        #                         ])
        # print("self.silence_found[:5]",[(i.span()[0]*self.sample_each_n/hz+self.untranscribed_intro,
        #                                 i.span()[1]*self.sample_each_n/hz+self.untranscribed_intro)
        #                         for i in self.silence_found[:5]
        #                         ])
        # self.silence_boundaries=[tuple(start_at+(i*self.sample_each_n)
        #                                 for i in j.span())
        #                                 for j in self.silence_found]
        self.silence_boundaries=[(start_at+(i*self.sample_each_n),
                                    start_at+(j*self.sample_each_n))
                                        for i,j in self.silence_found]
        # print("self.silence_boundaries[:5]",[(i[0]/hz,i[1]/hz)
        #                                     for i in self.silence_boundaries[:5]])
        self.sound_begins=(re.match(any_silence_regex,threshold_vector
                                    ).span()[1]+start_at)*self.sample_each_n
        self.sound_ends=(re.search(final_silence_regex,threshold_vector
                                    ).span()[0]+start_at)*self.sample_each_n
        print("Sound from",self.sound_begins,f"({self.sound_begins/hz}) to",
            self.sound_ends,f"({self.sound_ends/hz})")
        # exit()# for t in tqdm(range(self.files.sound.n_samples)):
        #     print(self.intensity.get_value(time=t/hz))
    def silence_to_tier_annotations(self):
        # This should be +1 what''s wrong??!?
        assert len(self.silence_boundaries) == len(self.files.plaintext.clauses) +1
        # for num in [self.silence_boundaries,self.files.plaintext.clauses]:
        #     print(num[:5])
        tier=self.files.textgrid.add_tier(self.tier_name+
                            f'x{self.sample_each_n}_{int(self.upper_range)}')
        if self.upper_range:
            self.upper_range_done=True
        else:
            self.lower_range_done=True
        hz=self.files.sound.sampling_frequency
        # print("self.silence_boundaries[:5]:",[(i/hz,j/hz) for (i,j) in self.silence_boundaries[-5:]])
        for n,clause_text in enumerate(self.files.plaintext.clauses):
            # n+=len(self.files.plaintext.clauses)-7
            start=self.silence_boundaries[n][1]/hz
            # if n:
            #     start=self.silence_boundaries[n-1][1]/hz
            # else:
            #     start=self.sound_begins/hz
            if n == len(self.files.plaintext.clauses) -1:
                end=self.sound_ends/hz
            else:
                end=self.silence_boundaries[n+1][0]/hz
            try:
                print("start:",start,"end_time:",end,clause_text)
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
        self.new_breath_pitch_rise_min=15 #hz
        self.files=Files(file_name)
        if not hasattr(self.files,'sound'):
            print(_("Missing sound file; can't continue!"))
        if not hasattr(self.files,'plaintext'):
            print(_("Missing text file with whole text transcription!"))
        self.textgrid_name=self.files.file_w_ext('TextGrid')
        if (not os.path.isfile(self.textgrid_name) or
                        not os.path.getsize(self.textgrid_name)):
            print(_("Will write to {}, which isn't there yet.").format(self.textgrid_name))
            self.files.start_textgrid(self.textgrid_name)
        else:
            print(_("Will write to {}, adding tiers.").format(self.textgrid_name))
            self.files.read_textgrid(self.textgrid_name)
        # self.untranscribed_intro=7.5
        # self.untranscribed_epilogue=4.0
        self.untranscribed_intro=kwargs.get('untranscribed_intro')
        self.untranscribed_epilogue=kwargs.get('untranscribed_epilogue')
        if self.untranscribed_intro:
            print(_("Going to skip the first {} seconds "
                "of untranscribed audio").format(self.untranscribed_intro))
        else:
            self.untranscribed_intro=0
        if self.untranscribed_epilogue:
            print(_("Going to skip the last {} "
                "seconds of untranscribed audio").format(self.untranscribed_epilogue))
        else:
            self.untranscribed_epilogue=0
        self.texts_to_align=getattr(self.files.plaintext,self.attr_to_align)
        self.tier_name=f'{self.attr_to_align}__auto'
        for self.sample_each_n in [100]: #,10  ,1
            self.lower_range_done=self.upper_range_done=False
            # for i in range(2):
            self.find_silences()
            self.silence_to_tier_annotations()
        self.files.textgrid.write()
class AlignWords(Align):
    def __init__(self,file_name,**kwargs):
        self.silence_to_find_in_s=.075 #100 miliseconds
        self.one_word=.1 #100ms, standard used by Praat
        self.attr_to_align='words'
        super().__init__(file_name=file_name, **kwargs)
class AlignClauses(Align):
    def __init__(self,file_name,**kwargs):
        self.silence_to_find_in_s=.2 #200 miliseconds
        self.one_word=.2 #.1=100ms, standard used by Praat
        # self.silence_to_find_in_s=.3 #150 miliseconds
        self.attr_to_align='clauses'
        super().__init__(file_name=file_name, **kwargs)
class IntervalTier(tgt.core.IntervalTier):
    def add_interval(self,start_time, end_time, text):
        try:
            i=tgt.core.Interval(start_time, end_time, text)
            tgt.core.IntervalTier.add_interval(self,i)
            return i
        except ValueError as e:
            print("Failed to make interval",start_time, end_time, text, e)
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
        import codecs
        try:
            log.info(f"trying tgt.io.read_textgrid with {file_name}")
            # tgt_text_grid=tgt.io.read_textgrid(file_name)
            with codecs.open(file_name, 'r', encoding='utf-8') as f:
            # Read whole file into memory ignoring empty lines and lines consisting
            # solely of a single double quote.
                stg = [line.strip() for line in f.readlines()
                    if line.strip() not in ['', '"']]
            log.info(f"stg: {stg[0:4]}")
            if ((stg[0] != 'File type = "ooTextFile"' or
                stg[1] != 'Object class = "TextGrid"') and
                (stg[0] != 'File type = "ooTextFile short"' or
                    stg[1] != '"TextGrid"')):
                raise Exception(_('Invalid TextGrid header: {0}\n{1}').format(stg[0], stg[1]))
            # tgt_text_grid=tgt.io.read_short_textgrid(file_name,stg)
            tgt_text_grid=tgt.io.read_long_textgrid(file_name,stg)
            log.info("tgt.io.read_textgrid completed successfully")
        except IndexError as e:
            log.info(f"found IndexError {e}; trying more generic read")
            raise
            tgt_text_grid=parselmouth.read(file_path=file_name)
        except UnicodeDecodeError as e:
            log.info(f"found UnicodeDecodeError {e}; trying utf-16")
            tgt_text_grid=tgt.io.read_textgrid(file_name,encoding='utf-16')
        except FileNotFoundError as e:
            log.info(f"found FileNotFoundError {e}; making a new file")
            tgt_text_grid=tgt.core.TextGrid(file_name)
        super().__init__(filename=file_name, **kwargs)
        for tier in tgt_text_grid.tiers:
            # print(tier.name)
            if self.has_tier(tier.name):
                print(_("Tier ‘{}’ is already there!").format(tier.name))
                print(_("Won't add "
                "{} "
                "annotations (first 5: "
                "{})").format(len(tier.annotations),[i.text for i in tier.annotations[:5]]))
            else:
                print(_("Tier ‘{}’ not there, adding!").format(tier.name))
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
        self.clauses=[i for i in re.split(regex, self.text) if i]
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
        print(f"Going to load Textgrid file {file}")
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
                if isinstance(e,IndexError):
                    log.info("Check for a malformed textgrid file, especially "
                    "with extra information, or linebreaks in content.")
                    raise
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
        # outputdir,archivename,metadata_header=None,append=False
        log.info(f"{os.path.dirname(self.files.textgrid.filename)},{self.files.textgrid.filename}")
        log.info(os.path.splitext(self.files.textgrid.filename))
        dirname=os.path.dirname(self.files.textgrid.filename)
        self.tarball=file.TarBall(dirname if dirname else '.',
                            os.path.splitext(self.files.textgrid.filename)[0],
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
            log.info(f"Tier ‘{tier_name}’ not in "
                    "{self.files.textgrid.get_tier_names()}")
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
            print(_("Please specify a tier name (-t) in "
                    "{}").format(self.files.textgrid.get_tier_names()))
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
            base=os.path.splitext(self.files.textgrid.filename)[0]
            this_sound_name=(f'{base}-{annotation.start_time}s.wav') #x seconds
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
