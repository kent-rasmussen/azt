#!/usr/bin/env python3
# coding=UTF-8
from tkinter import Frame,Tk
# from tkinter import Tk as tkinter.Tk
import pyaudio
import wave
import file
import logging
log = logging.getLogger(__name__)

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
        self.audio_card_in=min(self.cards['in'])
    def default_out(self):
        self.audio_card_out=min(self.cards['out'])
    def default_fs(self):
        self.fs=max(self.cards['in'][self.audio_card_in])
    def default_sf(self):
        self.sample_format=min(self.cards['in'][self.audio_card_in][self.fs])
    def defaults(self):
        self.default_in()
        self.default_out()
        self.default_fs()
        self.default_sf()
    def next_card_in(self):
        ins=sorted(self.cards['in'].keys())
        log.debug("next_card_in (of {})".format(ins))
        insi=ins.index(self.audio_card_in)
        if insi == len(ins)-1:
            return 1
        else:
            self.audio_card_in=ins[insi+1]
            self.default_fs()
            self.default_sf()
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
    def getactual(self):
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
        for card in self.cards['in']:
            self.cards['in'][card]={}
            for fs in self.hypothetical['fss']:
                self.cards['in'][card][fs]=list()
                for sf in self.hypothetical['sample_formats']:
                    try:
                        ifs=self.pyaudio.is_format_supported(rate=fs,
                            input_device=card,input_channels=1,
                            input_format=sf)
                    except ValueError as e:
                        pass
                    if ifs == True:
                        self.cards['in'][card][fs].append(sf)
                if self.cards['in'][card][fs] == []:
                    del self.cards['in'][card][fs]
            if self.cards['in'][card] == {}:
                del self.cards['in'][card]
        for card in self.cards['out']:
            self.cards['out'][card]={}
            for fs in self.hypothetical['fss']:
                self.cards['out'][card][fs]=list()
                for sf in self.hypothetical['sample_formats']:
                    try:
                        ifs=self.pyaudio.is_format_supported(rate=fs,
                            output_device=card,output_channels=1,
                            output_format=sf)
                    except ValueError as e:
                        pass
                    if ifs == True:
                        self.cards['out'][card][fs].append(sf)
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
    def sethypothetical(self):
        self.hypothetical={}
        self.hypothetical['fss']={192000:'192khz',
                                96000:'96khz',
                                44100:'44.1khz',
                                28000:'28khz',
                                8000:'8khz'
                                }
        self.hypothetical['sample_formats']={
                                            pyaudio.paFloat32:'32 bit float',
                                            pyaudio.paInt32:'32 bit integer',
                                            pyaudio.paInt24:'24 bit integer',
                                            pyaudio.paInt16:'16 bit integer',
                                            pyaudio.paInt8:'8 bit integer'
                                            }
    def check(self):
        if self.audio_card_in not in self.cards['in']:
            self.default_in()
        if self.fs not in self.cards['in'][self.audio_card_in]:
            self.default_fs()
        if self.sample_format not in self.cards['in'][self.audio_card_in][
                                                                    self.fs]:
            self.default_sf()
        if self.audio_card_out not in self.cards['out']:
            self.default_out()
    def __init__(self,pyaudio):
        self.pyaudio=pyaudio
        self.sethypothetical()
        self.getactual()
        self.defaults() #pick best of actuals
        self.printactuals()
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
            if '(no default output device)' in sys.exc_info()[0]:
                self.settings.audio_card_out=None
            return
    def streamclose(self):
        if hasattr(self,'stream'):
            self.stream.stop_stream()
            self.stream.close()
    def getformat(self):
        format=self.pa.get_format_from_width(self.wf.getsampwidth())
        return format
    def play(self):
        log.debug("I'm playing the recording now")
        self.streamclose() #just in case
        timeout=5 #seconds or None
        process=False
        # process=True #This takes precedence
        thread=False #over this
        self.wf = wave.open(self.filenameURL, 'rb')
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
            log.debug("{} doesn't seem to be a supported card; giving up."
                        "".format(self.settings.audio_card_out))
            return
        elif rate not in self.settings.cards['out'][
                                                self.settings.audio_card_out]:
            log.debug("{} doesn't seem to be a supported rate; giving up."
                        "".format(rate))
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
            if format not in self.settings.cards['out'][
                                            self.settings.audio_card_out][rate]:
                log.debug("{} doesn't seem to be a supported format ({}); "
                "giving up.".format(format,format not in self.settings.cards[
                                    'out'][self.settings.audio_card_out][rate]))
                return
            framesleft = frames
            self.data = self.wf.readframes(self.settings.chunk)
            while len(self.data) > 0:
                try:
                    self.stream.write(self.data,exception_on_underflow=True)
                except:
                    log.exception("Other exception trying to play "
                                "sound! %s {}".format(sys.exc_info()[0]))
                    raise
                try:
                    self.data = self.wf.readframes(self.chunk)
                except:
                    log.exception("Unexpected exception trying to read "
                                "frames %s {}".format(sys.exc_info()[0]))
                    raise
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
        file.remove(self.filenameURL) #don't do this until recording new file.
        try:
            self.wf = wave.open(self.filenameURL, 'wb')
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
        else:
            log.error("Nothing recorded!")
    def stop(self):
        log.log(3,"I'm stopping recording now")
        if hasattr(self,'stream'):
            self.stream.stop_stream()
        self.fileclose()
        self.streamclose()
    def __init__(self,filenameURL,pyaudio,settings):
        log.debug("Initializing Recording")
        self.callbackrecording=True
        self.pa=pyaudio
        self.settings=settings
        self.filenameURL=filenameURL
if __name__ == "__main__":
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt): #ignore Ctrl-C
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        log.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
    import sys
    sys.excepthook = handle_exception
    # sysdefault=6
    # pulse=12
    # default=14
    # self.sample_format=4
    # self.fs=96000
    # print(pyaudio.paInt8)
    import time
    import timeit
    loglevel=5
    from logsetup import *
    log=logsetup(loglevel)
    try: #Allow this module to be used without translation
        _
    except:
        def _(x):
            return x
    pa = AudioInterface()
    times=100
    class Test:
        def test1():
            pa.get_device_count()
        def test2():
            pa.get_host_api_count()
        def test3():
            pa.get_default_host_api_info()
        def test4():
            pass #pa.get_host_api_info_by_type(pyaudio.paInDevelopment)
        def test5():
            pa.get_host_api_info_by_index(0)
        def test6():
            pa.get_device_info_by_host_api_device_index(0,0)
        def test7():
            pa.get_device_count()
        def test8():
            pa.get_default_input_device_info()
        def test9():
            pa.get_default_output_device_info()
        def test10():
            pa.get_device_info_by_index(0)
        def test11():
            pa.get_sample_size(1)
        def test12():
            pa.get_format_from_width(1)
    for i in range(1,13):
        cmd=getattr(Test,'test'+str(i))
        # cmd
        out=timeit.timeit(cmd, number=times)
        print(i,out)
    exit()

    try:
        pa = AudioInterface()
        settings=SoundSettings(pa)
        # settings.fs=96000
        # settings.sample_format=pyaudio.paInt24
        settings.audio_card_in=0
        settings.audio_card_out=7
        # stream = pa.open(
        #     input_device_index=settings.audio_card_in,
        #     format=settings.sample_format,
        #     channels=settings.channels,
        #     rate=settings.fs,
        #     input=True,
        #     stream_callback=SoundFileRecorder.recordcallback)# settings.channels=0
        # log.debug(stream)
        time.sleep(1)
        done=settings.test(pa)
        time.sleep(1)
        # player=SoundFilePlayer('test_44100_4_6.wav',settings)
        # for i in range(5):
        # player.play()
        # try:
        # except BaseException as e:
        #     log.debug("Hey, It didn't work! ({})".format(e))
        # exit()
        while done != True:
            done=settings.next()
            settings.test(pa)
            time.sleep(1)
    except:
        log.error("uncaught exception: %s", traceback.format_exc())
