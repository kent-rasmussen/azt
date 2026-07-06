#!/usr/bin/env python3
# coding=UTF-8
"""Wave-file I/O and playback/record streams.

Audio device state (PyAudio handle, cards, rates, ASR) lives in
``backend.core.sound``. This module holds only the I/O classes that read
and write WAV files via PyAudio streams.
"""
import pyaudio
import wave
import sys
import traceback

import numpy

from utilities import logsetup, file
from backend.core.sound import AudioInterface, SoundSettings

log = logsetup.getlog(__name__)
logsetup.setlevel('DEBUG', log)

try:
    _
except NameError:
    def _(x):
        return x


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
        if not hasattr(self,'stream'):
            return   # nothing opened yet (e.g. first play) — not an error
        try:
            self.stream.stop_stream()
            self.stream.close()
        except Exception as e:
            log.info("Stream didn't stop and close; was it open? {}".format(e))
    def getformat(self):
        format=self.pa.get_format_from_width(self.wf.getsampwidth())
        return max(format,2)
    def _output_rate(self):
        """A sample rate the current OUTPUT card supports, read from settings
        (self.settings.cards['out'][audio_card_out] — the same dict play()'s
        rate check uses). Prefer 44100, else the supported rate closest to it.
        Falls back to 44100 if the card list can't be read."""
        try:
            rates=[int(r) for r in
                   self.settings.cards['out'][self.settings.audio_card_out]]
        except (KeyError, AttributeError, TypeError):
            rates=[]
        if not rates:
            return 44100
        if 44100 in rates:
            return 44100
        return min(rates, key=lambda r: abs(r-44100))
    def _playable_wav(self, src):
        """The PyAudio/wave playback path only reads WAV. If src is already WAV,
        return it; if it's compressed (m4a/aac/… — e.g. audio recorded on the
        phone), decode it to a cached temp WAV via ffmpeg (the decoder the ASR
        path already uses), resampled to a rate the OUTPUT card supports.
        Returns a WAV path, or None if decoding failed."""
        if src.lower().endswith('.wav'):
            return src
        cache=getattr(self,'_decoded_cache',None)
        if cache is None:
            cache=self._decoded_cache={}
        out=cache.get(src)
        if out and file.exists(out):
            return out
        import subprocess, tempfile, os
        out=os.path.join(tempfile.gettempdir(),
                         os.path.basename(src)+'.play.wav')
        rate=self._output_rate()
        try:
            # resample to a rate the OUTPUT card supports (phone recordings are
            # often 48000, which some cards reject); -ac 1 mono.
            subprocess.run(['ffmpeg','-y','-i',src,'-ac','1','-ar',str(rate),out],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                           check=True)
        except Exception as e:
            log.error("Couldn't decode '{}' for playback via ffmpeg: {}".format(
                                                                        src,e))
            return None
        cache[src]=out
        return out
    def play(self,event=None):
        log.debug("I'm playing the recording now ({})".format(self.filenameURL))
        playURL=self._playable_wav(str(self.filenameURL))
        if playURL is None:
            log.error("Can't play '{}': couldn't decode it to WAV.".format(
                                                            self.filenameURL))
            return
        self.streamclose() #just in case
        timeout=5 #seconds or None
        process=False
        thread=False
        self.wf = wave.open(playURL, 'rb')
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
                    and format != 1):
                log.debug("{} doesn't seem to be a supported format ({}); "
                "giving up.".format(format,format not in self.settings.cards[
                                    'out'][self.settings.audio_card_out][rate]))
                return
            framesleft = frames
            self.data = self.wf.readframes(self.settings.chunk)
            while len(self.data) > 0:
                try:
                    self.stream.write(self.data)
                except Exception:
                    log.exception("Other exception trying to play "
                                f"sound! {sys.exc_info()[0]}")
                    log.info("The above may indicate a systemic problem!")
                try:
                    self.data = self.wf.readframes(self.chunk)
                except OSError as e:
                    if "Output underflowed" in e.arg[0]:
                        self.streamopen(rate,channels)
                    log.exception("Unexpected exception trying to read "
                                f"frames {sys.exc_info()[0]}")
                    log.info("The above may indicate a systemic problem!")
            log.debug("apparently we're out of data")
            self.streamclose()
        def callback():
            import time
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
                    except Exception:
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
            p.join(timeout)
            if p.exception:
                log.error("Exception2!", traceback.format_exc())
                raise p.exception
            if process:
                p.terminate()
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
        self.streamclose()
        if hasattr(self,'pa'):
            self.pa.close()
    def streamclose(self):
        if hasattr(self,'stream'):
            self.stream.close()
    def start(self):
        log.log(3,"I'm recording now")
        self.file_write_OK=False
        if hasattr(self,'fulldata'):
            delattr(self,'fulldata')
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
        try:
            self.wf = wave.open(str(self.file_tmp), 'wb')
            self.wf.setnchannels(self.settings.channels)
            self.wf.setsampwidth(self.pa.get_sample_size(
                                                self.settings.sample_format))
            self.wf.setframerate(self.settings.fs)
            log.log(3,"File opened to write ({}): {}".format(self.wf,
                                                            self.filenameURL))
        except Exception:
            log.error("Trouble opening file to write ({}): {}".format(self.wf,
                                                            self.filenameURL))
    def fileclose(self):
        import time
        while hasattr(self,'stream') and self.stream.is_active():
            time.sleep(0.1)
        if hasattr(self,'fulldata'):
            self.wf.writeframes(self.fulldata)
            self.wf.close()
        if self.settings.file_ok(self.file_tmp):
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
            finally:
                wav_writer.close()
        print(type(self.wf16k))
        return self.wf16k
    def get_asr(self):
        try:
            self.asr=self.settings.asr
        except AttributeError:
            self.settings.load_ASR()
            self.asr=self.settings.asr
    def get_transcriptions(self):
        self.get_asr()
        self.asr.sister_languages=self.settings.asr_kwargs['sister_languages']
        self.asr.show_tone=self.settings.asr_kwargs['show_tone']
        self.asr.get_transcriptions(str(self.filenameURL))
        self.error_text=self.asr.error_text
        self.transcriptions=self.asr.transcriptions
        self.transcriptions_ipa=self.asr.transcriptions_ipa
        self.tone_melody=getattr(self.asr,'tone_melody',None)
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
        ' ':0
        }
    def compile(self,pitches='˥˥ ˩˩ ˧˩'):
        self.wavdata=numpy.zeros(int(self.secpersylbreak*self.bitrate))
        words=str(pitches).split(' ')
        for w in words:
            syllables=w.split(' ')
            for syl in syllables:
                badchars=set(syl)-set(['˥','˦','˧','˨','˩'])
                for c in badchars:
                    syl=syl.replace(c,'')
                contour=done=0
                for n,c in enumerate(syl):
                    log.info("character: {} ({})".format(c,n))
                    tohz=fromhz=self.pitchdict[c]
                    if n+1 < len(syl) and c != syl[n+1]:
                        tohz=self.pitchdict[syl[n+1]]
                        contour=1
                    elif n+1 == len(syl) and c != syl[n-1]:
                        done=1
                    nframes=self.framespersyl//(len(syl)-contour)
                    hz=fromhz
                    if fromhz != tohz:
                        dhz=tohz-fromhz
                        hz=numpy.arange(fromhz,tohz-dhz/2,(tohz-fromhz)/nframes/2,
                                        dtype=numpy.float32)
                        print(hz)
                    step=1
                    if not done:
                        self.wavdata=numpy.append(self.wavdata,numpy.sin(
                                0.8*numpy.pi*(numpy.arange(
                                                    nframes,dtype=numpy.float32
                                                        )*hz)/self.bitrate
                                            )
                                    ).astype(numpy.float32)
            self.wavdata=numpy.append(self.wavdata,numpy.zeros(int(self.secperwordbreak*self.bitrate),dtype=numpy.float32))
        with wave.open('test'+__name__+'.wav','wb') as f:
            f.setnchannels(self.settings.channels)
            f.setsampwidth(self.p.get_sample_size(self.format))
            f.setframerate(self.bitrate)
            f.writeframes(self.wavdata)
            f.close()
        self.wavdata = self.wavdata.astype(numpy.float32).tobytes()
    def __init__(self,pyAudio=None,settings=None):
        if not pyAudio:
            self.p = AudioInterface()
        else:
            self.p = pyAudio
        if not settings:
            self.settings=SoundSettings(self.p)
        else:
            self.settings=settings
        self.format=pyaudio.paFloat32
        self.bitrate = 64000
        self.hz = 350
        self.secpersyl = .4
        self.secpersylbreak = .05
        self.secperwordbreak = .15
        self.deltaHL = 40
        self.stream = self.p.open(format = self.format,
                        channels = 2,
                        rate = self.bitrate,
                        output = True)
        self.setparameters()


if __name__ == "__main__":
    """Set volume, somehow!!"""
    analang='tbt'
    from backend import langtags
    languages=langtags.Languages()
    language=languages.get_obj(analang)
    soundsettings=SoundSettings(analang_obj=language)
    log.info(f"soundsettings.asr_kwargs: {soundsettings.asr_kwargs}")
    b=BeepGenerator()
    b.compile()
    b.play()
    log.info("Done!")
