"""Headless backend for audio device settings, PyAudio handle, ASR state,
and recording-task filename helpers.

This module holds *runtime* audio state (device enumeration, format
validation, ASR kwargs). Persistent user config lives in ``settings/audio.py``
(``AudioConfig``) — the two are intentionally separate.
"""
import copy
import sys
import pyaudio
from utilities import file, rx, logsetup
from utilities import utilities as utils
log = logsetup.getlog(__name__)
try:
    import numpy
except ModuleNotFoundError:
    log.error("This isn't going to work, but you can hopefully reboot after "
              "installing Numpy.")
    raise
from backend import asr
log.info("ASR loaded OK")

try:
    _
except NameError:
    def _(x):
        return x


class AudioInterface(pyaudio.PyAudio):
    def stop(self):
        self.terminate()
        log.info("PyAudio Terminated")
    done = close = finished = stop
    def __init__(self):
        log.debug("PA Version: {}".format(pyaudio.get_portaudio_version()))
        log.debug("PA Version: {}".format(pyaudio.get_portaudio_version_text()))
        super().__init__()


class SoundSettings(object):
    """Runtime audio device and ASR configuration.

    Owns the PyAudio handle, enumerates available cards, validates
    rate/format combinations, and manages ASR kwargs/state. Load/save to
    the settings file is routed through here so device state has a single
    home.
    """

    # Settings that must be valid before playback is usable. Record tasks
    # additionally need ``audio_card_in`` — pass ``include_input=True``.
    required_attrs = ['fs', 'sample_format', 'audio_card_out']

    def test(self, pa):
        # only used from __main__; kept for parity
        import time
        filenameURL = "test_{}_{}_{}.wav".format(self.fs, self.sample_format,
                                                 self.audio_card_in)
        self.print1()
        try:
            from io_put.sound import SoundFileRecorder, SoundFilePlayer
            recorder = SoundFileRecorder(filenameURL, pa, self)
            recorder.start()
            time.sleep(1)
            recorder.stop()
            log.info("Finished recording!")
        except Exception as e:
            log.info("Problem recording! %s ({})".format(e))
            return 1
        player = SoundFilePlayer(filenameURL, pa, self)
        try:
            player.play()
        except BaseException as e:
            log.debug("Hey, It didn't work! ({})".format(e))
        except:
            log.info("Problem playing! %s")
            return 1

    def print1(self):
        values = []
        for setting in ['audio_card_in', 'sample_format', 'fs', 'audio_card_out']:
            values += [setting, getattr(self, setting)]
        log.info("{}: {}; {}: {}; {}: {}; {}: {}".format(*values))

    def print(self):
        for setting in ['audio_card_in', 'sample_format', 'fs', 'audio_card_out']:
            log.info("{}: {}".format(setting, getattr(self, setting)))

    def default_in(self):
        self.audio_card_in = [k for k, v in self.cards['dict'].items()
                              if k in self.cards['in']
                              if 'default' in v]
        if self.audio_card_in:
            self.audio_card_in = self.audio_card_in[0]
        elif self.cards['in']:
            self.audio_card_in = min(self.cards['in'])
        else:
            log.error("I can't find any input card!")
            raise

    def default_out(self):
        self.audio_card_out = [k for k, v in self.cards['dict'].items()
                               if k in self.cards['out']
                               if 'default' in v]
        if self.audio_card_out:
            self.audio_card_out = self.audio_card_out[0]
        else:
            self.audio_card_out = min(self.cards['out'])

    def default_fs(self):
        if self.audio_card_in in self.cards['in']:
            self.fs = max(self.cards['in'][self.audio_card_in])
        else:
            self.fs = max(self.cards['out'][self.audio_card_out])

    def default_sf(self):
        if self.audio_card_in in self.cards['in']:
            self.sample_format = min(self.cards['in'][self.audio_card_in][self.fs])
        else:
            self.sample_format = max(self.cards['out'][self.audio_card_out][self.fs])

    def max_sf(self):
        if self.audio_card_in in self.cards['in']:
            self.sample_format = max(self.cards['in'][self.audio_card_in][self.fs])
        else:
            self.sample_format = max(self.cards['out'][self.audio_card_out][self.fs])

    def defaults(self):
        self.default_out()
        self.default_in()
        self.default_fs()
        self.default_sf()

    def next_card_in(self):
        ins = sorted(self.cards['in'].keys())
        insi = ins.index(self.audio_card_in)
        if insi == len(ins) - 1:
            return 1
        else:
            self.audio_card_in = ins[insi + 1]
            self.default_fs()
            self.default_sf()

    def next_card_out(self):
        outs = sorted(self.cards['out'].keys())
        outsi = outs.index(self.audio_card_out)
        if outsi == len(outs) - 1:
            return 1
        else:
            self.audio_card_out = outs[outsi + 1]

    def next_fs(self):
        exit = False
        fss = sorted(self.cards['in'][self.audio_card_in].keys(), reverse=True)
        fssi = fss.index(self.fs)
        if fssi == len(fss) - 1:
            exit = self.next_card_in()
            if exit == False:
                self.default_fs()
        else:
            self.fs = fss[fssi + 1]
        return exit

    def next_sf(self):
        exit = False
        sfs = sorted(self.cards['in'][self.audio_card_in][self.fs], reverse=True)
        sfsi = sfs.index(self.sample_format)
        if sfsi == len(sfs) - 1:
            exit = self.next_fs()
            if exit == False:
                self.default_sf()
        else:
            self.sample_format = sfs[sfsi + 1]
        return exit

    def next(self):
        return self.next_sf()

    def getactual(self, test=False):
        self.cards = {'in': {}, 'out': {}, 'dict': {}}
        hostinfo = self.pyaudio.get_host_api_info_by_index(0)
        numdevices = hostinfo.get('deviceCount')
        for i in range(numdevices):
            devinfo = self.pyaudio.get_device_info_by_host_api_device_index(0, i)
            d = {'code': i, 'name': devinfo['name']}
            if (devinfo.get('maxInputChannels')) > 0:
                self.cards['in'][i] = {}
            if (devinfo.get('maxOutputChannels')) > 0:
                self.cards['out'][i] = {}
            self.cards['dict'][i] = devinfo['name']
        for card in self.cards['in'].copy():
            self.cards['in'][card] = {}
            for fs in self.hypothetical['fss']:
                self.cards['in'][card][fs] = list()
                for sf in self.hypothetical['sample_formats']:
                    try:
                        if test:
                            self.pyaudio.is_format_supported(rate=fs,
                                                             input_device=card,
                                                             input_channels=1,
                                                             input_format=sf)
                        self.cards['in'][card][fs].append(sf)
                    except ValueError:
                        pass
                if self.cards['in'][card][fs] == []:
                    del self.cards['in'][card][fs]
            if self.cards['in'][card] == {}:
                del self.cards['in'][card]
        for card in self.cards['out'].copy():
            self.cards['out'][card] = {}
            for fs in self.hypothetical['fss']:
                self.cards['out'][card][fs] = list()
                for sf in self.hypothetical['sample_formats']:
                    try:
                        if test:
                            self.pyaudio.is_format_supported(rate=fs,
                                                             output_device=card,
                                                             output_channels=1,
                                                             output_format=sf)
                        self.cards['out'][card][fs].append(sf)
                    except ValueError:
                        pass
                if self.cards['out'][card][fs] == []:
                    del self.cards['out'][card][fs]
            if self.cards['out'][card] == {}:
                del self.cards['out'][card]

    def printactuals(self):
        for io in ['in', 'out']:
            for card in self.cards[io]:
                log.debug("{} {} ({}):".format(io, self.cards['dict'][card],
                                               card))
                for fs in self.cards[io][card]:
                    for sf in self.cards[io][card][fs]:
                        log.debug('\t{}_{}'.format(self.hypothetical['fss'][fs],
                                  self.hypothetical['sample_formats'][sf]))

    def sample_format_numpy(self):
        d = {
            pyaudio.paInt32: numpy.int32,
            pyaudio.paInt24: numpy.int24,
            pyaudio.paInt16: numpy.int16,
        }
        return d[self.sample_format]

    def sethypothetical(self):
        self.hypothetical = {}
        self.hypothetical['fss'] = {192000: '192khz',
                                    96000: '96khz',
                                    44100: '44.1khz',
                                    28000: '28khz',
                                    8000: '8khz'}
        self.hypothetical['sample_formats'] = {
            pyaudio.paInt32: '32 bit integer',
            pyaudio.paInt24: '24 bit integer',
            pyaudio.paInt16: '16 bit integer',
        }

    def makedefaultifnot(self):
        if (not hasattr(self, 'audio_card_out')
                or self.audio_card_out not in self.cards['out']
                or self.audio_card_out not in self.cards['dict']):
            self.default_out()
        if (not hasattr(self, 'audio_card_in')
                or self.audio_card_in not in self.cards['in']
                or self.audio_card_in not in self.cards['dict']):
            self.default_in()
        if (not hasattr(self, 'fs') or
                ((self.audio_card_in not in self.cards['in'] or
                  self.fs not in self.cards['in'][self.audio_card_in]) and
                 self.fs not in self.cards['out'][self.audio_card_out])):
            self.default_fs()
        if (not hasattr(self, 'sample_format') or
                ((self.audio_card_in not in self.cards['in'] or
                  self.fs not in self.cards['in'][self.audio_card_in] or
                  self.sample_format not in self.cards['in'][self.audio_card_in][self.fs])
                 and self.sample_format not in self.cards['out'][self.audio_card_out][self.fs])):
            self.default_sf()

    def check(self):
        try:
            self.pyaudio.is_format_supported(rate=self.fs,
                                             output_device=self.audio_card_out,
                                             output_channels=1,
                                             output_format=self.sample_format)
        except ValueError as e:
            if 'Device unavailable' in e.args[0]:
                self.next_card_out()
                self.check()
        try:
            self.pyaudio.is_format_supported(rate=self.fs,
                                             input_device=self.audio_card_in,
                                             input_channels=1,
                                             input_format=self.sample_format)
        except ValueError as e:
            if 'Device unavailable' in e.args[0]:
                self.next_card_in()
                self.check()
            if 'Invalid sample rate' in e.args[0]:
                self.next_sf()
                self.check()

    def initial_ASR_kwargs(self, language_object):
        log.info("setting initial_ASR_kwargs")
        try:
            langs = language_object.supported_ancestor_codes_prioritized()
        except Exception as e:
            log.info(f"Exception: {e}")
            langs = ['en']
        self.asr_repos = {}
        self.asr_kwargs = {'sister_languages': langs}
        log.info(f"Done with initial self.asr_kwargs: {self.asr_kwargs}")

    def reload_ASR(self):
        self.get_changed_kwargs()
        self.asr.load_models_by_kwarg(**self.changed_kwargs['repos'])
        self.asr.load_postprocess_by_kwarg(**self.asr_kwargs)

    def load_ASR(self):
        """Only do this if there is no ASR; reload above."""
        try:
            assert isinstance(self.asr, asr.ASRtoText)
            self.reload_ASR()
            log.info("ASR reloaded")
        except (AssertionError, AttributeError) as e:
            log.info(f"Loading ASR ({e})")
            self.asr = asr.ASRtoText(self.program, **self.asr_kwargs)
            self.asr_kwargs = copy.deepcopy(self.asr.kwarg_defaults)
            log.info("ASR loaded")

    def tally_asr_repo(self, reponame):
        log.info(f"{self.asr_repos=} ({type(self.asr_repos)})")
        utils.setnesteddictval(self.asr_repos, 1, reponame, addval=True)

    def asr_repo_tally(self, d=None):
        if d and isinstance(d, dict):
            self.asr_repos = d
        return self.asr_repos

    def asr_kwarg_dict(self, d):
        if d and isinstance(d, dict):
            self.asr_kwargs = d
        return self.asr_kwargs

    def get_changed_kwargs(self):
        if not hasattr(self, 'asr') or not isinstance(self.asr, asr.ASRtoText):
            return 1
        changed_kwargs = {k: v for k, v in self.asr_kwargs.items()
                          if not hasattr(self.asr, k) or v != getattr(self.asr, k)}
        self.changed_kwargs = {
            'repos': {k: v for k, v in changed_kwargs.items()
                      if k in self.asr.repo_modelnames},
            'postprocess': {k: v for k, v in changed_kwargs.items()
                            if k in self.asr.postprocess_kwargs},
            'sister_languages': (changed_kwargs['sister_languages']
                                 if 'sister_languages' in changed_kwargs else []),
        }
        self.changed_kwargs['all'] = {**self.changed_kwargs['repos'],
                                      **self.changed_kwargs['postprocess'],
                                      'sister_languages': self.changed_kwargs['sister_languages']}

    def file_ok(self, filename):
        return (file.exists(filename) and
                file.getsize(filename) > self.min_audio_file_size())

    def min_audio_file_size(self):
        return self.fs * self.min_audio_length_ms / 1000

    def confirm_pyaudio(self):
        if (hasattr(self.program, 'pyaudio')
                and isinstance(self.program.pyaudio, AudioInterface)):
            self.pyaudio = self.program.pyaudio
        else:
            self.pyaudio = self.program.pyaudio = AudioInterface()

    # === Absorbed from former ``Sound`` mixin ===

    def done_pyaudio(self):
        """Terminate the PyAudio handle if running."""
        try:
            self.pyaudio.terminate()
        except Exception:
            log.info("Apparently self.pyaudio doesn't exist, or isn't initialized.")

    def check_missing_attrs(self, include_input=False):
        """Return True if any required setting is missing or invalid."""
        attrs = list(self.required_attrs)
        if include_input:
            attrs = ['audio_card_in'] + attrs
        for s in attrs:
            if hasattr(self, s):
                if s + 's' in self.hypothetical and (
                        getattr(self, s) not in self.hypothetical[s + 's']):
                    log.info(f"Sound setting {s} invalid; asking again")
                    return True
                elif 'audio_card' in s and (
                        getattr(self, s) not in self.cards['dict']):
                    log.info(f"Sound setting {s} invalid; asking again")
                    return True
            else:
                log.info(f"Missing sound setting {s}; asking again")
                return True
        return False

    def soundcheck(self, include_input=False):
        """Revalidate format against hardware, then check required attrs.
        Returns True if a mic-check UI pass is needed.
        """
        self.check()
        return self.check_missing_attrs(include_input=include_input)

    def load_from_file(self):
        """Pull persisted values in through the Settings file loader."""
        self.program.settings.loadsettingsfile(setting='soundsettings')
        if self.program.hostname == 'karlap' and (
                'cache_dir' not in self.asr_kwargs):
            self.asr_kwargs['cache_dir'] = '/media/kentr/hfcache'

    def store_to_file(self):
        """Persist values out through the Settings file writer."""
        self.program.settings.storesettingsfile(setting='soundsettings')

    @classmethod
    def ensure(cls, program, analang_obj=None):
        """Return ``program.soundsettings``, creating and loading it if
        missing. Idempotent; safe to call from every sound-using task.
        """
        ss = getattr(program.settings, 'soundsettings', None)
        if ss is None:
            log.info("Making new soundsettings object")
            ss = cls(program, analang_obj=analang_obj)
            program.settings.soundsettings = ss
            program.soundsettings = ss
            ss.load_from_file()
        elif not hasattr(program, 'soundsettings'):
            program.soundsettings = ss
        return ss

    def __init__(self, program, pyaudio=None, analang_obj=None):
        self.program = program
        self.confirm_pyaudio()
        self.sethypothetical()
        self.getactual()
        self.makedefaultifnot()
        # Exclude accidental recordings: 44.8 kHz @ 1 s = 14.6 k
        self.min_audio_length_ms = 500
        try:
            assert 'backend.asr' in sys.modules, "ASR module not loaded"
            self.initial_ASR_kwargs(analang_obj)
            self.asrOK = True
        except (Exception, AssertionError) as e:
            log.error("Exception loading ASR: {}".format(e))
            self.asrOK = False
        self.check()
        self.chunk = 1024
        self.channels = 1


class Record(object):
    """Headless mixin for recording-task filename/node logic.

    Depends on the task having ``self.program``, ``self.analang``, and
    ``self.glosslangs``. Audio device state is reached via
    ``self.program.soundsettings``.
    """

    def audioURL(self, relfilename):
        return str(file.getdiredurl(self.program.settings.audiodir, relfilename))

    def audioexists(self, relfilename):
        return file.exists(self.audioURL(relfilename))

    def hassoundfile(self, node, recheck=False):
        return node.hassoundfile(recheck)

    def filenameoptions(self, node):
        ps = self.program.slices.ps()
        if ps:
            pslocopts = [ps]
        else:
            pslocopts = []
        profile = self.program.slices.profile()
        if ps and profile:
            pslocopts.insert(0, ps + '_' + profile)
        fieldlocopts = [None]
        try:
            l = node.locationvalue()
            pslocopts.insert(0, ps + '-' + l)
            fieldlocopts.append(l)
        except AttributeError:
            pass
        if not pslocopts:
            pslocopts = [None]
        filenames = []
        form = node.textvaluebylang(self.analang)
        if not form:
            log.error("filenameoptions: no {ana} analang in "
                      "{id}!".format(ana=self.analang, id=node.sense.id))
        for pslocopt in pslocopts:
            for fieldlocopt in fieldlocopts:
                for legacy in ['_', None]:
                    for tags in [None, 1]:
                        args = [node.sense.id]
                        if tags:
                            args += [node.tag]
                            if node.tag == 'field':
                                args += [node.ftype]
                        args += [form]
                        for l in self.glosslangs:
                            args += [node.glossbylang(l)]
                        optargs = args[:]
                        optargs.insert(0, pslocopt)
                        optargs.insert(3, fieldlocopt)
                        wavfilename = '_'.join([x for x in optargs if x])
                        if legacy == '_':
                            wavfilename += '_'
                        wavfilename = rx.urlok(wavfilename)
                        filenames += [wavfilename + '.wav']
        return filenames

    def makeaudiofilename(self, node):
        if self.hassoundfile(node):
            return
        filenames = self.filenameoptions(node)
        for f in filenames:
            if self.audioexists(f):
                node.textvaluebylang(lang=self.program.params.audiolang(), value=f)
                break
        f = filenames[-1]
        node.audiofilenametoput = f
        node.audiofileURL = self.audioURL(f)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
