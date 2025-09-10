#!/usr/bin/env python3
# coding=UTF-8
# from tkinter import Frame,Tk
# from tkinter import Tk as tkinter.Tk
import pyaudio
import wave
import logsetup
log=logsetup.getlog(__name__)
# logsetup.setlevel('INFO',log) #for this file
logsetup.setlevel('DEBUG',log) #for this file
try:
    import asr
    log.info("ASR loaded OK")
except Exception as e:
    log.error("Exception importing ASR: {}".format(e))
# import soundfile
import file
import sys
import math        #?import needed modules
try:
    import numpy
except ModuleNotFoundError:
    log.error("This isn't going to work, but you can hopefully reboot after"
            "installing Numpy.")
    raise
try:
    _
except:
    def _(x):
        return x
class AudioInterface(pyaudio.PyAudio):
    def stop(self):
        self.terminate()
        log.info("PyAudio Terminated")
    done=close=finished=stop
    def __init__(self):
        log.debug("PA Version: {}".format(pyaudio.get_portaudio_version()))
        log.debug("PA Version: {}".format(pyaudio.get_portaudio_version_text()))
        super(AudioInterface,self).__init__()
class SoundSettings(object):
    def test(self,pa):
        filenameURL="test_{}_{}_{}.wav".format(self.fs,self.sample_format,
                                                    self.audio_card_in)
        self.print1()
        try:
            recorder=SoundFileRecorder(filenameURL,pa,self)
            recorder.start()
            time.sleep(1)
            recorder.stop()
            log.info("Finished recording!")
        except Exception as e:
            log.info("Problem recording! %s ({})".format(e))
            return 1
        player=SoundFilePlayer(filenameURL,pa,self)
        # for i in range(5):
        try:
            player.play()
        except BaseException as e:
            log.debug("Hey, It didn't work! ({})".format(e))
        except:
            log.info("Problem playing! %s")
            return 1
    def print1(self):
        values=[]
        for setting in ['audio_card_in','sample_format','fs','audio_card_out']:
            values+=[setting,getattr(self,setting)]
        log.info("{}: {}; {}: {}; {}: {}; {}: {}".format(*values))
    def print(self):
        for setting in ['audio_card_in','sample_format','fs','audio_card_out']:
            log.info("{}: {}".format(setting,getattr(self,setting)))
    def default_in(self):
        self.audio_card_in=[k for k,v in self.cards['dict'].items()
                                    if k in self.cards['in']
                                    if 'default' in v]
        if self.audio_card_in:
            self.audio_card_in=self.audio_card_in[0]
        else:
            self.audio_card_in=min(self.cards['in'])
    def default_out(self):
        self.audio_card_out=[k for k,v in self.cards['dict'].items()
                                    if k in self.cards['out']
                                    if 'default' in v]
        if self.audio_card_out:
            self.audio_card_out=self.audio_card_out[0]
        else:
            self.audio_card_out=min(self.cards['out'])
    def default_fs(self):
        self.fs=max(self.cards['in'][self.audio_card_in])
    def default_sf(self):
        self.sample_format=min(self.cards['in'][self.audio_card_in][self.fs])
    def max_sf(self):
        self.sample_format=max(self.cards['in'][self.audio_card_in][self.fs])
    def defaults(self):
        self.default_in()
        self.default_out()
        self.default_fs()
        self.default_sf()
    def next_card_in(self):
        ins=sorted(self.cards['in'].keys())
        insi=ins.index(self.audio_card_in)
        if insi == len(ins)-1:
            return 1
        else:
            self.audio_card_in=ins[insi+1]
            log.debug("next_card_in {} (of {})".format(self.audio_card_in,ins))
            self.default_fs()
            self.default_sf()
    def next_card_out(self):
        outs=sorted(self.cards['out'].keys())
        outsi=outs.index(self.audio_card_out)
        if outsi == len(outs)-1:
            return 1
        else:
            self.audio_card_out=outs[outsi+1]
            log.debug("next_card_out {} (of {})".format(self.audio_card_out,outs))
            # self.default_fs()
            # self.default_sf()
    def next_fs(self):
        log.debug("next_fs")
        exit=False
        fss=sorted(self.cards['in'][self.audio_card_in].keys(),reverse=True)
        fssi=fss.index(self.fs)
        if fssi == len(fss)-1:
            exit=self.next_card_in()
            if exit == False:
                self.default_fs()
        else:
            self.fs=fss[fssi+1]
        return exit
    def next_sf(self):
        log.debug("next_sf")
        exit=False
        sfs=sorted(self.cards['in'][self.audio_card_in][self.fs],reverse=True)
        sfsi=sfs.index(self.sample_format)
        if sfsi == len(sfs)-1:
            exit=self.next_fs()
            if exit == False:
                self.default_sf()
        else:
            self.sample_format=sfs[sfsi+1]
        return exit
    def next(self):
        return self.next_sf()
    def getactual(self,test=False):
        self.cards={'in':{},'out':{},'dict':{}}
        hostinfo = self.pyaudio.get_host_api_info_by_index(0)
        numdevices = hostinfo.get('deviceCount')
        for i in range(numdevices):
            devinfo=self.pyaudio.get_device_info_by_host_api_device_index(0, i)
            d={'code':i,'name':devinfo['name']}
            if (devinfo.get('maxInputChannels')) > 0: #microphone
                log.info("Input Device id {} - {} ({}/{}); channels in: {}; "
                        "out: {}".format(i,d['name'], devinfo['index'],
                        numdevices-1, devinfo['maxInputChannels'],
                        devinfo['maxOutputChannels']))
                self.cards['in'][i]={}
            if (devinfo.get('maxOutputChannels')) > 0: #speaker
                log.info("Output Device id {} - {} ({}/{}); channels in: {}; "
                        "out: {}".format(i,d['name'], devinfo['index'],
                        numdevices-1, devinfo['maxInputChannels'],
                        devinfo['maxOutputChannels']))
                self.cards['out'][i]={}
            self.cards['dict'][i]=devinfo['name']
        for card in self.cards['in'].copy():
            self.cards['in'][card]={}
            for fs in self.hypothetical['fss']:
                self.cards['in'][card][fs]=list()
                for sf in self.hypothetical['sample_formats']:
                    try:
                        if test:
                            ifs=self.pyaudio.is_format_supported(rate=fs,
                                                            input_device=card,
                                                            input_channels=1,
                                                            input_format=sf)
                        self.cards['in'][card][fs].append(sf)
                    except ValueError as e:
                        log.info("Config not supported; no worries: rate={}; "
                            "output_device={}; "
                            "output_channels=1, "
                            "output_format={} ({})".format(fs,card,sf,e))
                if self.cards['in'][card][fs] == []:
                    del self.cards['in'][card][fs]
            if self.cards['in'][card] == {}:
                del self.cards['in'][card]
        for card in self.cards['out'].copy():
            self.cards['out'][card]={}
            for fs in self.hypothetical['fss']:
                self.cards['out'][card][fs]=list()
                for sf in self.hypothetical['sample_formats']:
                    try:
                        if test:
                            ifs=self.pyaudio.is_format_supported(rate=fs,
                                                            output_device=card,
                                                            output_channels=1,
                                                            output_format=sf)
                        self.cards['out'][card][fs].append(sf)
                    except ValueError as e:
                        log.info("Config not supported; no worries: rate={}; "
                            "output_device={}; "
                            "output_channels=1, "
                            "output_format={} ({})".format(fs,card,sf,e))
                if self.cards['out'][card][fs] == []:
                    del self.cards['out'][card][fs]
            if self.cards['out'][card] == {}:
                del self.cards['out'][card]
    def printactuals(self):
        for io in ['in','out']:
            for card in self.cards[io]:
                log.debug("{} {} ({}):".format(io,self.cards['dict'][card],
                                                                        card))
                for fs in self.cards[io][card]:
                    for sf in self.cards[io][card][fs]:
                        log.debug('\t{}_{}'.format(self.hypothetical['fss'][fs],
                                    self.hypothetical['sample_formats'][sf]))
    def sample_format_numpy(self):
        d={
            pyaudio.paInt32:numpy.int32,
            pyaudio.paInt24:numpy.int24,
            pyaudio.paInt16:numpy.int16,
            }
        return d[self.sample_format]
    def sethypothetical(self):
        self.hypothetical={}
        self.hypothetical['fss']={192000:'192khz',
                                96000:'96khz',
                                44100:'44.1khz',
                                28000:'28khz',
                                8000:'8khz'
                                }
        self.hypothetical['sample_formats']={
                                            # pyaudio.paFloat32:'32 bit float',
                                            pyaudio.paInt32:'32 bit integer',
                                            pyaudio.paInt24:'24 bit integer',
                                            pyaudio.paInt16:'16 bit integer',
                                            # pyaudio.paInt8:'8 bit integer'
                                            }
    def makedefaultifnot(self):
        if (not hasattr(self,'audio_card_in')
                or self.audio_card_in not in self.cards['in']
                or self.audio_card_in not in self.cards['dict']
                ):
            self.default_in()
        if (not hasattr(self,'fs') or
                self.fs not in self.cards['in'][self.audio_card_in]):
            self.default_fs()
        if (not hasattr(self,'sample_format') or
                self.sample_format not in self.cards['in'][self.audio_card_in][
                                                                    self.fs]):
            self.default_sf()
        if (not hasattr(self,'audio_card_out')
                or self.audio_card_out not in self.cards['out']
                or self.audio_card_out not in self.cards['dict']
                ):
            self.default_out()
    def check(self):
        # log.info(_("Testing speaker settings:"))
        # self.max_sf()
        try:
            ifs=self.pyaudio.is_format_supported(rate=self.fs,
                                            output_device=self.audio_card_out,
                                            output_channels=1,
                                            output_format=self.sample_format)
        except ValueError as e:
            # log.info("{}; {}".format(e,type(e)))
            if 'Device unavailable' in e.args[0]:
                self.next_card_out()
                self.check()
            log.info("Config not supported; no worries: rate={}; "
                "output_device={}; "
                "output_channels=1, "
                "output_format={} ({})".format(self.fs,self.audio_card_out,
                                                self.sample_format,e))
        # log.info(_("Testing microphone settings:"))
        try:
            ifs=self.pyaudio.is_format_supported(rate=self.fs,
                                                input_device=self.audio_card_in,
                                                input_channels=1,
                                                input_format=self.sample_format)
        except ValueError as e:
            # log.info("{}; {}".format(e,type(e)))
            if 'Device unavailable' in e.args[0]:
                self.next_card_in()
                self.check()
            if 'Invalid sample rate' in e.args[0]:
                self.next_sf()
                # self.next_fs()
                self.check()
                log.info("Config not supported; no worries: rate={}; "
                "output_device={}; "
                "output_channels=1, "
                "output_format={} ({})".format(self.fs,self.audio_card_in,
                                                self.sample_format,e))
    def initial_ASR_kwargs(self,language_object):
        log.info("setting initial_ASR_kwargs")
        try:
            langs=language_object.supported_ancestor_codes_prioritized()
            # log.info("Done with supported_ancestor_codes_prioritized")
        except Exception as e: #e.g., if language_object is None
            log.info(f"Exception: {e}")
            langs=['en']
        self.asr_repos={}
        self.asr_kwargs={'sister_languages':langs}
        log.info(f"Done with initial self.asr_kwargs: {self.asr_kwargs}")
    def reload_ASR(self):
        self.get_changed_kwargs()
        #This just returns if no kwargs:
        self.asr.load_models_by_kwarg(**self.changed_kwargs['repos'])
        #this redoes everything, so needs all kwargs
        self.asr.load_postprocess_by_kwarg(**self.asr_kwargs)
    def load_ASR(self):
        """Only do this if there is no ASR; reload above."""
        try:
            assert isinstance(self.asr,asr.ASRtoText)
            self.reload_ASR()
            log.info("ASR reloaded")
        except (AssertionError,AttributeError) as e:
            log.info(f"Loading ASR ({e})")
            self.asr=asr.ASRtoText(**self.asr_kwargs)
            self.asr_kwargs=copy.deepcopy(self.asr.kwarg_defaults)
            log.info("ASR loaded")
    def tally_asr_repo(self,reponame):
        log.info(f"{self.asr_repos=} ({type(self.asr_repos)})")
        utils.setnesteddictval(self.asr_repos,1,reponame,addval=True)
    def asr_repo_tally(self,d=None):
        # log.info(f"{d=} ({type(d)})")
        if d and isinstance(d,dict):
            self.asr_repos=d
        return self.asr_repos
    def asr_kwarg_dict(self,d):
        if d and isinstanced(d,dict):
            self.asr_kwargs=d
        return self.asr_kwargs
    def get_changed_kwargs(self):
        if not hasattr(self,'asr') or not isinstance(self.asr,asr.ASRtoText):
            return 1 # will need to reload anyway
        changed_kwargs={k:v for k,v in self.asr_kwargs.items()
                        if not hasattr(self.asr,k) or
                            v != getattr(self.asr,k)
                        }
        self.changed_kwargs={
            'repos':{k:v for k,v in changed_kwargs.items()
                         if k in self.asr.repo_modelnames}, #incl 'show_tone'
            'postprocess':{k:v for k,v in changed_kwargs.items()
                             if k in self.asr.postprocess_kwargs},
            'sister_languages':(changed_kwargs['sister_languages']
                        if 'sister_languages' in changed_kwargs else []),
            }
        self.changed_kwargs['all']={**self.changed_kwargs['repos'],
                                    **self.changed_kwargs['postprocess'],
                    'sister_languages':self.changed_kwargs['sister_languages']}
    def file_ok(self,filename):
        return (file.exists(filename) and
                file.getsize(filename) > self.min_audio_file_size)
    def __init__(self,pyaudio=None,analang_obj=None):
        if not pyaudio:
            pyaudio = AudioInterface()
        self.pyaudio=pyaudio
        self.sethypothetical()
        self.getactual()
        self.makedefaultifnot()
        #I may want to tweak this; the point is to exclude accidental recordings
        # 44.8khz @1s = 14.6k
        self.min_audio_file_size=5000
        # self.defaults() #pick best of actuals
        try:
            assert 'asr' in sys.modules
            self.initial_ASR_kwargs(analang_obj) #overwritten by UI or file
            self.asrOK=True
        except Exception as e:
            log.error("Exception loading ASR: {}".format(e))
            self.asrOK=False
        self.check()
        # self.printactuals()
        self.chunk=1024
        self.channels=1 #Always record in mono
class SoundFilePlayer(object):
    def playcallback(self, in_data, frame_count, time_info, status):
        data = self.wf.readframes(frame_count)
        return (data, pyaudio.paContinue)
    def soundcheck(self,rate,channels):
        log.debug("checking for support")
        format=self.getformat()
        if None in [rate,format,channels]: #This should never happen here.
            log.error("Problem playing on {} card on {} channels with {} rate, "
            "{} format".format(self.settings.audio_card_out,channels,rate,
                                                                        format))
            return
        for setting in [rate,format,channels]:
            log.debug(setting)
        try:
            ok=self.pa.is_format_supported(float(rate),
                output_format=format,
                output_device=self.settings.audio_card_out,
                output_channels=channels)
        except TypeError as e:
            log.exception("Unsupported config TypeError trying to play sound! %s",
            e)
            raise
            return
        except ValueError as e:
            log.exception("Unsupported config ValueError trying to play sound! %s",
            e)
            raise
            return
        return ok
    def paopen(self):
        self.paclose()
        self.pa = AudioInterface()
    def paclose(self):
        self.streamclose() #i.e., if there
        if hasattr(self,'pa'):
            self.pa.close()
    def streamopen(self,rate,channels):
        if hasattr(self,'stream'):
            self.stream.close()
        format=self.getformat()
        try:
            self.stream = self.pa.open(format=format,
                output_device_index=self.settings.audio_card_out,
                channels=channels,
                rate=rate,
                output=True)
        except ValueError as e:
            log.debug("Valuerror: {}".format(e))
            raise
            return
        except OSError as e:
            log.debug("OSError: {}".format(e))
            if '(no default output device)' in str(e):
                self.settings.audio_card_out=None
            return
    def streamclose(self):
        # if hasattr(self,'stream'):
        try:
            self.stream.stop_stream()
            self.stream.close()
        except Exception as e:
            log.info("Stream didn't stop and close; was it open? {}".format(e))
    def getformat(self):
        format=self.pa.get_format_from_width(self.wf.getsampwidth())
        return max(format,2)
    def play(self,event=None):
        log.debug("I'm playing the recording now ({})".format(self.filenameURL))
        self.streamclose() #just in case
        timeout=5 #seconds or None
        process=False
        # process=True #This takes precedence
        thread=False #over this
        self.wf = wave.open(str(self.filenameURL), 'rb')
        frames = self.wf.getnframes()
        rate=int(self.wf.getframerate())
        duration = frames / float(rate)
        channels=self.wf.getnchannels()
        self.chunk = self.settings.chunk * channels
        format = self.getformat()
        log.debug("Trying to play with {} card, {} rate, {} format, and "
                "{} channels".format(self.settings.audio_card_out,rate,format,
                                                                    channels))
        if self.settings.audio_card_out not in self.settings.cards['out']:
            log.debug(f"{self.settings.audio_card_out} doesn't seem to be "
                    f"a supported output card ({self.settings.cards['out']})"
                    "; giving up.")
            self.settings.default_out()
            self.play()
            return
        elif rate not in self.settings.cards['out'][
                                                self.settings.audio_card_out]:
            log.debug(f"{rate} doesn't seem to be a supported rate "
                f"({self.settings.cards['out'][self.settings.audio_card_out]})"
                    "; giving up.")
            self.settings.default_out()
            self.play()
            return
        def block():
            self.streamopen(rate,channels)
            if not hasattr(self,'stream'):
                log.info("Sorry, couldn't make stream!")
                return
            log.debug("running play block with args "
                        "output_device_index={}, channels={}, "
                        "rate={}, duration={}, format={}".format(
                        self.settings.audio_card_out,
                        channels,rate,duration,format))
            if (format not in self.settings.cards['out'][
                                            self.settings.audio_card_out][rate]
                    and format != 1): #play this format, for now.
                log.debug("{} doesn't seem to be a supported format ({}); "
                "giving up.".format(format,format not in self.settings.cards[
                                    'out'][self.settings.audio_card_out][rate]))
                return
            framesleft = frames
            self.data = self.wf.readframes(self.settings.chunk)
            while len(self.data) > 0:
                try:
                    self.stream.write(self.data)#,exception_on_underflow=True)
                except:
                    log.exception("Other exception trying to play "
                                f"sound! {sys.exc_info()[0]}")
                    log.info("The above may indicate a systemic problem!")
                    # raise
                try:
                    self.data = self.wf.readframes(self.chunk)
                except OSError as e:
                    if "Output underflowed" in e.arg[0]:
                        self.streamopen(rate,channels)
                    log.exception("Unexpected exception trying to read "
                                f"frames {sys.exc_info()[0]}")
                    log.info("The above may indicate a systemic problem!")
                    # raise
            log.debug("apparently we're out of data")
            self.streamclose()
        def callback(): #This just isn't working faithfully, for some reason.
            log.info("Playing {} sample rate with card {} on {} channels with "
                "{} format".format(rate,self.settings.audio_card_out,channels,
                                                                        format))
            try:
                log.debug("trying stream...")
                self.stream = self.pa.open(
                    output_device_index=self.settings.audio_card_out,
                    format=format,
                    channels=channels,
                    rate=rate,
                    output=True,
                    stream_callback=self.playcallback)
                log.debug("Starting stream...")
                self.stream.start_stream()
                log.debug("Keeping stream active...")
                while (self.stream.is_active()) and (not self.stream.is_stopped()):
                    try:
                        log.debug(format/8*1024)
                    except:
                        log.error("No stream to write!")
                        return
                    time.sleep(0.1)
                    log.log(3,"Keeping stream active (again)...")
                log.log(3,"Stopping stream...")
                self.stream.stop_stream()
                log.log(3,"Stream stopped.")
            except Exception as e:
                log.exception("Can't play file! %s",e)
                return
        if process:
            from multiprocessing import Process
            log.info("Running as multi-process")
            p = Process(target=block)
        elif thread:
            from threading import Thread
            log.info("Running as threaded")
            p = Thread(target=block)
        else:
            log.info("Running in line")
            block()
        if process or thread:
            p.exception = None
            try:
                p.start()
            except BaseException as e:
                log.error("Exception!", traceback.format_exc())
                p.exception = e
            p.join(timeout) #finish this after timeout, in any case
            if p.exception:
                log.error("Exception2!", traceback.format_exc())
                raise p.exception
            if process:
                p.terminate() #for processes, not threads
        self.wf.close()
        # soundfile.SoundFile.close()
    def __init__(self,filenameURL,pyaudio,settings):
        self.pa=pyaudio
        self.filenameURL=filenameURL
        self.settings=settings
class SoundFileRecorder(object):
    def recordcallback(self, in_data, frame_count, time_info, flag):
        log.log(3,"Callback Recording!")
        if not hasattr(self,'fulldata'):
            self.fulldata= in_data
        else:
            self.fulldata+=in_data
        return (self.fulldata, pyaudio.paContinue)
    def paopen(self):
        log.debug("Initializing PyAudio (but probably should't be...)")
        self.paclose()
        self.pa = AudioInterface()
    def paclose(self):
        self.streamclose() #i.e., if there
        if hasattr(self,'pa'):
            self.pa.close()
    def streamclose(self):
        if hasattr(self,'stream'):
            self.stream.close()
    def start(self):
        log.log(3,"I'm recording now")
        self.file_write_OK=False #either way, clear this now; catch any errors
        if hasattr(self,'fulldata'):
            delattr(self,'fulldata') #let's start each recording afresh.
        def callback(self):
            log.log(3,"Initializing Callback Recording")
            log.log(3,"input card={}({}), rate={}, format={} ({}), channels={}"
                    "".format(self.settings.cards['dict'][
                                                self.settings.audio_card_in],
                    self.settings.audio_card_in,
                    self.settings.hypothetical['fss'][self.settings.fs],
                    self.settings.hypothetical['sample_formats'][
                                                self.settings.sample_format],
                    self.settings.sample_format,self.settings.channels))
            try:
                log.log(3,"opening stream on {}".format(self.pa))
                self.stream = self.pa.open(
                    input_device_index=self.settings.audio_card_in,
                    format=self.settings.sample_format,
                    channels=self.settings.channels,
                    rate=self.settings.fs,
                    input=True,
                    stream_callback=self.recordcallback)
                log.log(3,"starting stream")
                self.stream.start_stream()
                log.log(3,"stream started")
            except Exception as e:
                log.error("Exception in Callback Recording! ({})".format(e))
                return
            self.fileopen()
            """input=True, p.open() method → stream.read() to read from
            microphone. output=True, stream.write() to the speaker."""
        def block(self):
            self.stream = self.pa.open(format=self.sample_format,
                    channels=self.settings.channels,
                    rate=self.settings.fs,
                    frames_per_buffer=self.settings.chunk,
                    input=True)
            self.frames = []
            for i in range(0, int(
                        self.settings.fs / self.settings.chunk * self.seconds)):
                data = self.stream.read(self.settings.chunk)
                self.frames.append(data)
        if self.callbackrecording==True:
            callback(self)
        else:
            block(self)
    def fileopen(self):
        #This fn is for recording, not playing
        try:
            self.wf = wave.open(str(self.file_tmp), 'wb')
            self.wf.setnchannels(self.settings.channels)
            self.wf.setsampwidth(self.pa.get_sample_size(
                                                self.settings.sample_format))
            self.wf.setframerate(self.settings.fs)
            log.log(3,"File opened to write ({}): {}".format(self.wf,
                                                            self.filenameURL))
        except:
            log.error("Trouble opening file to write ({}): {}".format(self.wf,
                                                            self.filenameURL))
    def fileclose(self):
        while hasattr(self,'stream') and self.stream.is_active():
            time.sleep(0.1)
        if hasattr(self,'fulldata'):
            self.wf.writeframes(self.fulldata)
            self.wf.close()
        if self.settings.file_ok(self.file_tmp):
            #don't do this until we have a good, new recording
            log.error(f"File recorded! ({file.getsize(self.file_tmp)})")
            self.file_write_OK=True
            file.replace(self.file_tmp,self.filenameURL)
        else:
            log.error("Nothing recorded! "
                        f"(file size: {file.getsize(self.file_tmp)})")
    def toaudiosample(self):
        import io

        with io.BytesIO() as self.wf16k:
            wav_writer = wave.open(self.wf16k, "wb")
            try:
                wav_writer.setframerate(16000)
                wav_writer.setsampwidth(self.settings.sample_format)
                wav_writer.setnchannels(1)
                wav_writer.writeframes(self.fulldata)
                # self.wf16k = wav_file.getvalue()
            finally:
                wav_writer.close()
        print(type(self.wf16k))
        return self.wf16k
        # from pydub import AudioSegment
        # return AudioSegment(self.fulldata,
        #         frame_rate=self.settings.fs,
        #         sample_width=self.settings.sample_format,
        #         channels=self.settings.channels
        #         )
        #         # set_frame_rate
    def stop(self):
        log.log(3,"I'm stopping recording now")
        if hasattr(self,'stream'):
            self.stream.stop_stream()
        self.fileclose()
        self.streamclose()
    def __init__(self,filenameURL,pyaudio,settings):
        log.debug("Initializing Recording to {}".format(filenameURL))
        self.callbackrecording=True
        self.pa=pyaudio
        self.settings=settings
        self.filenameURL=filenameURL
        self.file_tmp=str(self.filenameURL)+'.tmp'
class BeepGenerator(object):
    def play(self):
        # self.compile(pitches=str(pitches))
        self.stream.write(self.wavdata)
    def pause(self):
        self.stream.write(chr(0)*self.framespersyl)
    def done(self):
        self.stream.stop_stream()
        self.stream.close()
        self.p.stop()
    def bitratecheck(self):
        if self.hz > self.bitrate:
            self.bitrate = self.hz+100
    def longer(self):
        self.secpersyl*=1.1
        self.setparameters()
    def shorter(self):
        self.secpersyl/=1.1
        self.setparameters()
    def higher(self):
        self.hz*=1.05
        self.setparameters()
    def lower(self):
        self.hz/=1.05
        self.setparameters()
    def wider(self):
        self.deltaHL*=1.3
        self.setparameters()
    def narrower(self):
        self.deltaHL/=1.3
        self.setparameters()
    def setparameters(self):
        self.bitratecheck()
        self.framespersyl=int(self.secpersyl*self.bitrate)
        self.pitchdict={
        '˥':self.hz+self.deltaHL*2,
        '˦':self.hz+self.deltaHL,
        '˧':self.hz,
        '˨':self.hz-self.deltaHL,
        '˩':self.hz-self.deltaHL*2,
        ' ':0,
        ' ':0
        }
    def compile(self,pitches='˥˥ ˩˩ ˧˩'):#' ˦˧˨˩'):
        self.wavdata=numpy.zeros(int(self.secpersylbreak*self.bitrate))
        words=str(pitches).split(' ')
        # log.info("words: {}".format(words))
        for w in words:
            syllables=w.split(' ')
            # log.info("syllables: {}".format(syllables))
            for syl in syllables:
                badchars=set(syl)-set(['˥','˦','˧','˨','˩'])
                for c in badchars:
                    # log.info("replacing {}".format(c))
                    syl=syl.replace(c,'')
                contour=done=0
                for n,c in enumerate(syl):
                    log.info("character: {} ({})".format(c,n))
                    tohz=fromhz=self.pitchdict[c]
                    if n+1 < len(syl) and c != syl[n+1]: #not last, not next
                        tohz=self.pitchdict[syl[n+1]]
                        contour=1
                    elif n+1 == len(syl) and c != syl[n-1]: #last of contour
                        done=1
                    nframes=self.framespersyl//(len(syl)-contour)
                    hz=fromhz
                    if fromhz != tohz:
                        dhz=tohz-fromhz
                        hz=numpy.arange(fromhz,tohz-dhz/2,(tohz-fromhz)/nframes/2,
                                        dtype=numpy.float32)
                        print(hz)
                        # print(numpy.arange(nframes,dtype=numpy.float32).dtype)
                    step=1
                    # log.info("hz: {}-{} (len: {},{}-{})".format(
                    #             fromhz,tohz,len(syl)-contour,nframes,done))
                    if not done:
                        self.wavdata=numpy.append(self.wavdata,numpy.sin(
                                0.8*numpy.pi*(numpy.arange(#0,100,
                                                    nframes,dtype=numpy.float32
                                                        )*hz)/self.bitrate #/(len(syl)-contour))
                                            )
                                    ).astype(numpy.float32)
            self.wavdata=numpy.append(self.wavdata,numpy.zeros(int(self.secperwordbreak*self.bitrate),dtype=numpy.float32))
        with wave.open('test'+__name__+'.wav','wb') as f:
            f.setnchannels(self.settings.channels)
            # log.info(self.p.get_sample_size(self.format))
            f.setsampwidth(self.p.get_sample_size(self.format))
            f.setframerate(self.bitrate)
            f.writeframes(
                            # bytes(
                            self.wavdata#,'utf-8'
                            # )
                        )
            f.close()
        self.wavdata = self.wavdata.astype(numpy.float32).tobytes()
        # self.wavdata = self.wavdata.astype(numpy.float32).tostring()
    def __init__(self,pyAudio=None,settings=None):
        if not pyAudio:
            self.p = AudioInterface()     #initialize pyaudio
        else:
            self.p = pyAudio
        if not settings:
            self.settings=SoundSettings(self.p)
        else:
            self.settings=settings
        #See https://en.wikipedia.org/wiki/Bit_rate#Audio
        self.format=pyaudio.paFloat32
        self.bitrate = 64000     #number of frames per second/frameset.
        self.hz = 350     #Hz, waves per second, 261.63=C4-note.
        self.secpersyl = .4     #seconds to play sound
        self.secpersylbreak = .05
        self.secperwordbreak = .15
        self.deltaHL = 40 #difference between high and low, in hz
        self.stream = self.p.open(format = self.format,
                        channels = 2,
                        rate = self.bitrate,
                        output = True)
        self.setparameters()
        # self.play()
if __name__ == "__main__":
    """Set volume, somehow!!"""
    analang='tbt'
    import langtags
    languages=langtags.Languages()
    language=languages.get_obj(analang)
    # langtags.Language(analang,languages=languages)
    soundsettings=SoundSettings(analang_obj=language)
    log.info(f"soundsettings.asr_kwargs: {soundsettings.asr_kwargs}")
    b=BeepGenerator()
    b.compile()
    b.play()
    exit()
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt): #ignore Ctrl-C
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        log.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
    sys.excepthook = handle_exception
    # sysdefault=6
    # pulse=12
    # default=14
    # self.sample_format=4
    # self.fs=96000
    # print(pyaudio.paInt8)
    import time
    import timeit
    pa = AudioInterface()
    times=100
    # class Test:
    #     def test1():
    #         pa.get_device_count()
    #     def test2():
    #         pa.get_host_api_count()
    #     def test3():
    #         pa.get_default_host_api_info()
    #     def test4():
    #         pass #pa.get_host_api_info_by_type(pyaudio.paInDevelopment)
    #     def test5():
    #         pa.get_host_api_info_by_index(0)
    #     def test6():
    #         pa.get_device_info_by_host_api_device_index(0,0)
    #     def test7():
    #         pa.get_device_count()
    #     def test8():
    #         pa.get_default_input_device_info()
    #     def test9():
    #         pa.get_default_output_device_info()
    #     def test10():
    #         pa.get_device_info_by_index(0)
    #     def test11():
    #         pa.get_sample_size(1)
    #     def test12():
    #         pa.get_format_from_width(1)
    # for i in range(1,13):
    #     cmd=getattr(Test,'test'+str(i))
    #     # cmd
    #     out=timeit.timeit(cmd, number=times)
    #     print(i,out)
    # exit()

    try:
        pa = AudioInterface()
        settings=SoundSettings(pa)
        time.sleep(1)
        done=settings.test(pa)
        time.sleep(1)
        while done != True:
            done=settings.next()
            settings.test(pa)
            time.sleep(1)
    except:
        log.error("uncaught exception: %s", traceback.format_exc())
