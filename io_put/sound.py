#!/usr/bin/env python3
# coding=UTF-8
"""Wave-file I/O and playback/record streams.

Audio device state (PyAudio handle, cards, rates, ASR) lives in
``backend.core.sound``. This module holds only the I/O classes that read
and write WAV files via PyAudio streams.
"""
import wave
import sys
import traceback

# The sound stack is OPTIONAL app-wide (program['nosound']): importing this
# module must never fail just because the audio library or numpy aren't
# installed — half the app imports it transitively, and a hard import here
# killed boot on any machine where pyaudio didn't build (2026-07-16). Guard
# the roots ONCE here (and in backend.core.sound) instead of at every
# importer.
try:
    import sounddevice
except Exception as _e:
    sounddevice=None
try:
    # Reading and writing the files themselves. Already a requirement, and it
    # is the natural partner to sounddevice: it hands back numpy arrays with
    # the right dtype, which is exactly what sounddevice takes.
    import soundfile
except Exception as _e:
    soundfile=None
try:
    import numpy
except Exception as _e:
    numpy=None

from utilities import logsetup, file
from utilities.i18n import _   # user-facing text lives here too (the wedge notice)
from utilities.error_handler import notify_user
from backend.core.sound import (AudioInterface, SoundSettings, AUDIO_OK,
                                spectral_ceiling, zero_runs, rate_is_fake)
# (The transitional `PYAUDIO_OK = AUDIO_OK` alias that stood here is gone: the
# streaming layer below is sounddevice now, so nothing is left to be
# transitional about.)

log = logsetup.getlog(__name__)
logsetup.setlevel('DEBUG', log)

try:
    _
except NameError:
    def _(x):
        return x


class SoundFilePlayer(object):
    """Play one sound file, without blocking the UI and without owning a
    stream that can wedge.

    PORTED to sounddevice 2026-09-09, and this class LOST about 150 lines,
    nearly all of which existed to survive PyAudio's blocking `write()`:

      * a manual chunk loop feeding `stream.write()`;
      * "Output underflowed" recovery that reopened the stream mid-file;
      * a worker thread, a 5 s `join` timeout, a wedge DEADLINE (clip length
        plus grace) and a GENERATION counter so an abandoned thread could
        discover it no longer owned `self.stream`;
      * on a wedge, abandoning the stream and LEAKING its device handle,
        because PortAudio forbids closing a stream inside a blocked write and
        doing it anyway corrupted the heap (2026-07-16);
      * and, added the same day this was ported, a cap on those leaks —
        because eight of them in one session took the sound card away from
        every other program on the machine, Praat included.

    `sounddevice.play()` hands the samples to PortAudio's own callback
    thread. It returns immediately, so the Tk main thread is never blocked —
    the property all that threading protected — and `sounddevice.stop()`
    stops and closes deterministically. There is no blocked write to be stuck
    inside, so there is nothing to abandon and nothing to leak. The wedge is
    not handled better; it is structurally absent.

    KEPT, because none of it was about the library: `_playable_wav`'s ffmpeg
    decode for phone recordings, `_output_rate`, and the settings guards.
    """

    def _dtype_for(self, path):
        """Read (and therefore play) as int, never float.

        This is what the old `getformat`'s `max(format, 2)` was doing:
        PyAudio's `get_format_from_width` maps a 4-byte sample to paFloat32,
        which mislabels 32-bit PCM, and `max(…, 2)` forced it back to
        paInt32. Kent (2026-09-09) "stopped short of" float32 deliberately
        after a bug he hit with it, so keeping the array integral keeps
        float32 out of the stream by construction — sounddevice takes the
        stream dtype FROM the array.
        """
        if soundfile is None:
            return 'int16'
        try:
            subtype = soundfile.info(path).subtype or ''
        except Exception as e:
            log.info("couldn't read the subtype of {} ({}); assuming 16-bit"
                     "".format(path, e))
            return 'int16'
        return 'int16' if '16' in subtype else 'int32'

    def streamclose(self):
        """Stop playback. Kept under its old name: tasks/sound.py:100 calls
        it when leaving a record page. There is no per-player stream to close
        any more, so this stops whatever is playing."""
        try:
            if sounddevice is not None:
                sounddevice.stop()
        except Exception as e:
            log.info("nothing to stop ({})".format(e))

    def _soundcheck_unused(self,rate,channels):
        """DEAD, kept only as the record of what it asked.

        It called `is_format_supported` before playing — and nothing called
        it: the only reference was inside the play path it was meant to
        guard, on a line that computed `getformat()` for it. The real check
        now lives one layer down, in `AudioInterface.supported()`, and the
        card table is genuinely probed (backend/core/sound.py::getactual),
        which is what this was trying to compensate for.
        """
        return None
    # `getformat()` is gone with the port: it asked PyAudio to turn a WAV's
    # sample WIDTH into a format constant, then clamped the result away from
    # paFloat32 (`max(format, 2)`). `_dtype_for()` above is the same decision
    # expressed as a dtype name, which is what sounddevice takes.
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
        """Playback reads via soundfile/libsndfile, which handles WAV, FLAC and
        OGG but NOT m4a/aac — so compressed audio (e.g. recorded on the phone
        by azt_recorder) is decoded to a cached temp WAV via ffmpeg (the
        decoder the ASR path already uses), resampled to a rate the OUTPUT
        card supports. Returns a WAV path, or None if decoding failed.

        STILL NEEDED after the sounddevice port (2026-09-09): the reason
        changed name but not substance. It used to say "the PyAudio/wave
        playback path only reads WAV"; libsndfile reads more than `wave` did,
        just not the patent-encumbered formats a phone produces."""
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
        if sounddevice is None or soundfile is None:
            log.error("no audio backend; can't play {}".format(
                                                        self.filenameURL))
            return
        # Read the whole clip, then hand it over. These are single words, so
        # RAM is not a consideration, and reading it here means the callback
        # thread never touches a file.
        try:
            data,rate=soundfile.read(playURL,dtype=self._dtype_for(playURL))
        except Exception as e:
            log.error("Couldn't read '{}' to play it: {}".format(playURL,e))
            return
        device=getattr(self.settings,'audio_card_out',None)
        log.debug("playing {}: {} frames at {} Hz as {} on device {}".format(
                    playURL,len(data),rate,data.dtype,device))
        # sounddevice.play() STOPS ANY PREVIOUS PLAY ITSELF and returns
        # immediately — PortAudio's callback thread does the work. That is
        # the whole reason ~150 lines went from this method: no chunk loop, no
        # worker thread, no join timeout, no wedge deadline, no generation
        # counter, and no abandoned streams leaking device handles.
        try:
            sounddevice.play(data,samplerate=rate,device=device)
            return
        except Exception as e:
            log.info("couldn't play on device {} ({}); trying this machine's "
                     "default output".format(device,e))
        # ONE retry, on the default device. A persisted card INDEX is not a
        # stable name for a device: PortAudio renumbers as the sound server
        # changes, so a saved audio_card_out can come to mean something else
        # or nothing (measured 2026-09-09 — a session recorded against
        # index 10 on a machine that later enumerated only 1-8).
        try:
            self.settings.default_out()
        except Exception as e:
            log.info("couldn't pick a default output ({})".format(e))
        try:
            sounddevice.play(data,samplerate=rate)
        except Exception as e:
            log.error("Couldn't play '{}' at all: {}".format(playURL,e))
    def __init__(self,filenameURL,audio,settings):
        # Renamed from `pyaudio` 2026-09-09: this module imported a module of
        # that name, which a parameter so called shadowed for the whole
        # method. `self.pa` keeps its name — "pa" is PortAudio, which stays
        # true whichever python binding reaches it (sounddevice, now).
        self.pa=audio
        self.filenameURL=filenameURL
        self.settings=settings


class SoundFileRecorder(object):
    """Record to a file, in blocks, without holding the whole take in RAM.

    PORTED to sounddevice 2026-09-09. Two things changed shape:

      * The old callback accumulated the ENTIRE recording in memory by
        repeatedly rebuilding a bytes object (`self.fulldata += in_data`) —
        quadratic in the number of blocks, and it also RETURNED that growing
        buffer as the callback's output, which is meaningless for an
        input-only stream. Blocks now go straight to disk as they arrive.
      * `fileclose()` then waited for the stream to go idle and wrote
        everything at the end, so a crash mid-take lost the whole recording.
        The file now has every block that arrived.

    Kept exactly: the `.tmp` file that is only renamed into place once
    `file_ok()` passes (`stop()`), which is what stops a failed take
    replacing a good recording, and `file_write_OK` for the UI.
    """

    # soundfile's names for what we record as. The keys are the dtype names
    # sounddevice takes; both live in backend/core/sound.SAMPLE_FORMATS.
    _SUBTYPES = {'int16': 'PCM_16', 'int32': 'PCM_32', 'float32': 'FLOAT'}

    def _subtype(self):
        fmt = getattr(self.settings, 'sample_format', 'int16')
        subtype = self._SUBTYPES.get(fmt)
        if subtype is None:
            log.info("no soundfile subtype for sample format {!r}; recording "
                     "16-bit".format(fmt))
            return 'PCM_16', 'int16'
        return subtype, fmt

    def streamclose(self):
        """Close the input stream if one is open. Kept under its old name:
        tasks/sound.py:99 calls it when leaving a record page."""
        stream = getattr(self, '_stream', None)
        if stream is None:
            return
        try:
            stream.stop()
            stream.close()
        except Exception as e:
            log.info("input stream didn't stop and close cleanly ({})"
                     "".format(e))
        self._stream = None
    def start(self):
        """Open the file and the input stream, and start filling one from the
        other. Returns immediately; PortAudio's thread does the work."""
        log.log(3,"I'm recording now")
        self.file_write_OK=False
        self._frames=[]          # kept for ASR (see toaudiosample)
        if sounddevice is None or soundfile is None:
            log.error("no audio backend; can't record {}".format(
                                                        self.filenameURL))
            return
        subtype,dtype=self._subtype()
        rate=int(self.settings.fs)
        channels=int(getattr(self.settings,'channels',1))
        device=getattr(self.settings,'audio_card_in',None)
        log.info("recording from device {} ({}) at {} Hz, {}, {} channel(s)"
                 "".format(device,
                           (getattr(self.settings,'cards',{}) or {}
                            ).get('dict',{}).get(device,'?'),
                           rate,dtype,channels))
        # (A warning stood here comparing `rate` against the device's own
        # `default_samplerate`, on the theory that asking for more implied
        # resampling. WITHDRAWN 2026-09-10, the day it was added: the
        # `pipewire` node reports 44100 and delivers a genuine 192 kHz, so it
        # fired on every rate above 44100 — always, and wrongly. A default
        # rate is not a maximum. The real test needs the RECORDING, and now
        # runs in _report_take once there is audio to look at.)
        try:
            # format='WAV' EXPLICITLY. soundfile infers the container from the
            # file extension, and we write to `<name>.wav.tmp` — so it saw
            # ".tmp", knew nothing about it, and refused: "No format specified
            # and unable to get format from file extension" (Kent
            # 2026-09-10). `wave.open` never cared, because it only ever wrote
            # WAV. The .tmp suffix is not negotiable — it is what keeps a
            # failed take from replacing a good recording — so the format has
            # to be stated instead of inferred.
            self._sf=soundfile.SoundFile(str(self.file_tmp),mode='w',
                                         samplerate=rate,channels=channels,
                                         subtype=subtype,format='WAV')
        except Exception as e:
            log.error("Couldn't open '{}' to record into: {}".format(
                                                        self.file_tmp,e))
            return

        # ── EVIDENCE, so a take can be CHECKED rather than assumed ─────────
        # Kent 2026-09-10, on sysdefault: "it just doesn't record well" — no
        # error, a file present, and something wrong with it. That is the worst
        # failure this code has, because a file that exists gets trusted: "we
        # can see when we're claiming a recording we aren't actually doing —
        # since that is a really bad thing."
        # These counters are what make the summary in fileclose() a
        # measurement instead of a claim. All are updated on PortAudio's
        # thread, so they stay to arithmetic on numbers already in hand.
        self._asked_rate=rate
        self._frames_in=0
        self._overflows=0
        self._peak=0.0
        self._t0=None
        # EXACTLY-ZERO SAMPLES, and the longest unbroken run of them.
        # Measured 2026-09-10: the same USB microphone read clean through its
        # raw ALSA device and, through `default`, delivered 13-100% of a quiet
        # capture as exact zeros — PipeWire noise suppression emitting digital
        # silence whenever it judges there is no speech. For speech
        # documentation that removes exactly the wrong material: breathy
        # release, final devoicing, weak fricatives. The waveform still looks
        # clean, the file passes `file_ok`, and nobody finds out.
        #   Analogue audio essentially never lands on exactly zero, and never
        # repeatedly, so a long run of them is not audio — it is a gate or a
        # dropout. Cheap to count here and it needs no knowledge of the
        # device, so it works on whatever path the user ended up with.
        self._zeros=0
        self._zrun_max=0
        self._zrun_cur=0

        def _incoming(indata,frames,time_info,status):
            # Runs on PortAudio's thread. Keep it short and never raise:
            # an exception here kills the stream mid-take.
            if self._t0 is None:
                import time as _t
                self._t0=_t.perf_counter()
            if status:
                # input_overflow means samples were DROPPED — the recording
                # has a hole in it. Counted, not just logged, so the summary
                # can say how bad it was.
                if getattr(status,'input_overflow',False):
                    self._overflows+=1
                else:
                    log.info("recording status: {}".format(status))
            try:
                self._sf.write(indata)
                self._frames.append(indata.copy())
                self._frames_in+=len(indata)
                if numpy is not None and len(indata):
                    # Peak as a fraction of full scale, so "did anything
                    # arrive?" is answerable without opening the file.
                    scale=float(numpy.iinfo(indata.dtype).max) \
                            if indata.dtype.kind=='i' else 1.0
                    p=float(numpy.abs(indata).max())/scale
                    if p>self._peak:
                        self._peak=p
                    # Zero runs, carried ACROSS blocks by zero_runs()'s
                    # carry/trailing pair — a gate's silence is far longer
                    # than one callback. The counting lives in
                    # backend.core.sound so it can be TESTED against known
                    # input instead of inferred from a log.
                    found,longest,self._zrun_cur=zero_runs(indata,
                                                           self._zrun_cur)
                    self._zeros+=found
                    if longest>self._zrun_max:
                        self._zrun_max=longest
            except Exception as e:
                log.error("couldn't write a recorded block ({})".format(e))

        try:
            self._stream=sounddevice.InputStream(samplerate=rate,
                                                 device=device,
                                                 channels=channels,
                                                 dtype=dtype,
                                                 callback=_incoming)
            self._stream.start()
            # What PortAudio ACTUALLY negotiated, which is authoritative where
            # the device's advertised default rate was only a hint.
            got=int(getattr(self._stream,'samplerate',rate) or rate)
            if got!=rate:
                log.warning("asked for %d Hz and the stream opened at %d Hz; "
                            "the file will be written as %d Hz and will be "
                            "WRONG unless something resampled",rate,got,rate)
        except Exception as e:
            log.error("Couldn't open the input stream ({}); no recording"
                      "".format(e))
            try:
                self._sf.close()
            except Exception:
                pass
            self._sf=None
            self._stream=None
    # `fileopen()` is gone: the file is opened in start(), by soundfile, which
    # needs no sample WIDTH — the old version got one from
    # `pa.get_sample_size(sample_format)`, and a subtype name says it better.
    def _report_take(self):
        """Say what was actually recorded, and complain when it isn't right.

        WHY THIS EXISTS. The recorder's worst failure is a file that exists
        and is wrong — silence, a hole, or the wrong rate — because a file
        that exists gets trusted, and a linguist discovers the problem weeks
        later with the speaker gone. Kent 2026-09-10, on sysdefault: "it just
        doesn't record well", with no error to go on.
          So five independent facts, none of them a guess: how many frames
        PortAudio actually handed us, how long the take really lasted, how
        loud the loudest sample was, how many times the input overflowed, and
        how much of it is exactly zero. Together they answer "did we record
        what we said we did".
        """
        if not getattr(self,'_asked_rate',None):
            return              # start() never ran; nothing to report on
        # PROBLEM + WHAT TO DO, for the user and not only the log.
        #
        # Everything below was measured before today and went to the log,
        # where no user will ever see it — so the app "detected" bad
        # recordings and the linguist still found out weeks later with the
        # speaker gone, which was the whole point of measuring. Each `bad()`
        # states the problem in the user's terms and what to do about it;
        # they are collected and sent as ONE message, because five separate
        # notices about one take is noise, and noise gets dismissed.
        problems=[]

        def bad(problem,fix):
            problems.append("{}\n    -> {}".format(problem,fix))

        import time as _t
        elapsed=(_t.perf_counter()-self._t0) if self._t0 else 0.0
        frames=self._frames_in
        implied=(frames/elapsed) if elapsed>0.05 else None
        log.info("take: %d frames in %.2fs at %d Hz asked (%s), peak %.1f%% "
                 "of full scale, %d overflow(s), %.1f%% exact zeros "
                 "(longest run %d samples)",
                 frames,elapsed,self._asked_rate,
                 "implies {:.0f} Hz".format(implied) if implied else "too "
                 "short to imply a rate",
                 100.0*self._peak,self._overflows,
                 100.0*self._zeros/float(frames) if frames else 0.0,
                 self._zrun_max)
        # NOTHING AUDIBLE. A file of digital silence is the purest form of
        # "claiming a recording we aren't doing": `file_ok` only checks SIZE,
        # so zeros pass it and the take is filed as good.
        # NO FRAMES AT ALL is its own case, and it had no notice: every test
        # below is guarded by `if frames`, so a take that delivered nothing
        # fell through all of them silently. That is precisely what a MUTED
        # microphone produces — Kent 2026-09-10: "mic muted doesn't register
        # a recording at all, as I think we asked it to" — and it is the
        # single most likely reason a user gets no recording, so it must be
        # the one case that always speaks.
        if not frames:
            log.error("that take received NO AUDIO AT ALL: the stream opened "
                      "and delivered zero frames. A muted input does this.")
            bad(_("No sound reached A-Z+T at all — not even silence."),
                _("The microphone is almost certainly muted. Check the mute "
                  "button on the microphone or headset itself, and the "
                  "microphone's level in your system's sound settings. This "
                  "is different from a quiet recording: nothing arrived."))
        if frames and self._peak < 0.0005:
            log.error("that take is SILENT (peak %.4f%% of full scale). A "
                      "file will be written and it contains nothing audible "
                      "— check the input device and its level before "
                      "collecting more.",100.0*self._peak)
            bad(_("This recording contains no sound at all."),
                _("The file will be saved but there is nothing in it. Check "
                  "that the right microphone is selected in Sound Settings, "
                  "that it is plugged in, and that it is not muted — then "
                  "record this word again."))
        elif frames and self._peak < 0.01:
            log.warning("that take peaked at only %.1f%% of full scale — very "
                        "quiet. Check the microphone and its level.",
                        100.0*self._peak)
            bad(_("This recording is very quiet (loudest point only "
                  "{peak:.1f}% of what the microphone can capture).").format(
                        peak=100.0*self._peak),
                _("It may be hard to hear and hard to analyse. Move the "
                  "microphone closer to the speaker, or raise the recording "
                  "level in your system's sound settings."))
        # THE RATE WE GOT vs THE RATE WE WROTE. frames/elapsed is crude (it
        # includes start-up latency), so this only fires on a gross mismatch —
        # the 4x kind that means a sound server resampled, or the stream ran
        # at a different rate than the header claims.
        if implied and (implied < self._asked_rate*0.6
                        or implied > self._asked_rate*1.6):
            log.warning("only %.0f frames/second arrived while the file is "
                        "being written as %d Hz — so its duration and pitch "
                        "will be wrong. Something between A-Z+T and the "
                        "hardware is not running at the rate we asked for.",
                        implied,self._asked_rate)
            bad(_("This recording will play back at the wrong speed and "
                  "pitch."),
                _("The microphone delivered about {got:.0f} samples a second "
                  "while the file says {asked}. Choose a different sample "
                  "rate in Sound Settings — {got_r} Hz is what this "
                  "microphone is really doing.").format(
                        got=implied,asked=self._asked_rate,
                        got_r=int(round(implied/1000.0)*1000)))
        if self._overflows:
            log.warning("the input overflowed %d time(s): samples were "
                        "DROPPED, so this recording has gaps. A slower rate "
                        "or a less busy machine will help.",self._overflows)
            bad(_("Parts of this recording are missing: the computer could "
                  "not keep up ({n} time(s)).").format(n=self._overflows),
                _("There are small gaps in the audio. Choose a lower sample "
                  "rate in Sound Settings, or close other programs, and "
                  "record this word again."))
        # GATED OR DROPPED AUDIO. Reported as milliseconds because that is
        # what decides whether it matters: a few samples is nothing, 50 ms
        # swallows a stop release, and half a second removes a whole syllable.
        if frames and self._zrun_max:
            rate=float(self._asked_rate) or 1.0
            run_ms=1000.0*self._zrun_max/rate
            share=100.0*self._zeros/float(frames)
            if run_ms>=20.0:
                # Which of the two causes it is matters for the fix, and the
                # overflow count separates them: dropouts are accompanied by
                # overflows, a gate is not.
                cause=("samples were dropped (the input also overflowed)"
                       if self._overflows else
                       "something is GATING the audio to digital silence — "
                       "noise suppression on this input, most likely")
                log.warning("this take contains %.0f ms of unbroken digital "
                            "silence (%.1f%% of all samples are exactly "
                            "zero): %s. Quiet speech is what goes first — "
                            "breathy release, final devoicing, weak "
                            "fricatives — and the file will still look and "
                            "play fine. Recording from the microphone's own "
                            "hardware device instead of the system default "
                            "usually avoids it.",run_ms,share,cause)
                if self._overflows:
                    bad(_("This recording has {ms:.0f} ms of complete "
                          "silence in it where sound is missing.").format(
                                ms=run_ms),
                        _("The computer could not keep up. Choose a lower "
                          "sample rate in Sound Settings, or close other "
                          "programs, and record this word again."))
                else:
                    bad(_("Something is removing the quiet parts of this "
                          "recording: {ms:.0f} ms of it is completely "
                          "silent.").format(ms=run_ms),
                        _("Your computer is applying noise removal to this "
                          "microphone. That deletes exactly what you need — "
                          "breathy releases, quiet consonants, the ends of "
                          "words — and the recording still sounds normal. In "
                          "Sound Settings, choose the microphone's own entry "
                          "rather than 'default', or turn off noise "
                          "suppression in your system's sound settings."))
            elif share>5.0:
                log.info("%.1f%% of this take's samples are exactly zero "
                         "(longest run %.0f ms) — worth watching if it "
                         "grows.",share,run_ms)
        # IS THE RATE REAL, OR DID SOMETHING RESAMPLE? Asked of the RECORDING,
        # because nothing available beforehand can answer it: the device
        # accepts any rate, its advertised default is not a maximum, and
        # frames-per-second come out right even when the content was
        # upsampled. Only the spectrum tells — see spectral_ceiling().
        try:
            if numpy is not None and self._frames:
                # Concatenated ONCE: a long take is a large array and both
                # checks want the same one.
                whole=numpy.concatenate(self._frames)
                # THE VERDICT comes from rate_is_fake, the CEILING only names
                # the frequency for the message. They were the other way
                # round, with `ceiling < asked*0.28` deciding — and that test
                # is the weaker one on general grounds, not just here:
                #   * it estimates its noise floor from the TOP 5% OF THE
                #     BAND, which in an upsampled capture is exactly where the
                #     resampler's residue lives, so the reference is
                #     contaminated by the thing being detected and the verdict
                #     swings on numerical noise;
                #   * it asserts "real" where rate_is_fake declines to;
                #   * rate_is_fake compares two FIXED bands against a
                #     threshold no acoustic signal can reach (a hole 100+ dB
                #     down is not an ADC's broadband noise), and it is the one
                #     with synthetic tests behind it.
                # Kent's call, 2026-09-10: "if you think rate_is_fake is a
                # better metric generally (not just on my machine), that's
                # fine."
                # Known limit kept in view: rate_is_fake cannot see a SMALL
                # ratio (44.1 kHz content in a 48 kHz file leaves a hole too
                # narrow to move the top-band median). That case is harmless.
                ceiling=spectral_ceiling(whole,self._asked_rate)
                if rate_is_fake(whole,self._asked_rate):
                    # NO ESTIMATED "real rate" HERE. It used `ceiling*2`, and
                    # that number is meaningless in exactly the case this
                    # branch handles: `spectral_ceiling` estimates its floor
                    # from the top of the band, which IS the hole, so
                    # numerical noise clears floor+12 dB and it reported
                    # "energy to 89851 Hz" for a band measured 136 dB empty —
                    # yielding the notice "192000 Hz really holds only 180000
                    # Hz of sound" (2026-09-10). Using the weaker test's
                    # number to describe the stronger test's verdict.
                    #   What IS known: the top of the band is empty, and which
                    # rate we switched to. Both are facts; the true source
                    # rate is not one we can measure, so it goes unstated.
                    log.warning("this take SAYS %d Hz and the top of its band "
                                "is EMPTY — something between A-Z+T and the "
                                "microphone upsampled it. The file is honest "
                                "about its rate and holds less detail than "
                                "that rate implies. On PipeWire, "
                                "clock.allowed-rates must include %d "
                                "(`pw-metadata -n settings | grep rate`).",
                                self._asked_rate,self._asked_rate)
                    # Tell the settings, so the rate just disproved stops
                    # being offered. The user's own test recording is the
                    # best evidence available and it arrives for free —
                    # better than the fraction-of-a-second probe the settings
                    # can afford on their own.
                    try:
                        self.settings.note_fake_rate(self._asked_rate)
                    except Exception as e:
                        log.info("couldn't record that %d Hz is upsampled "
                                 "(%s)",self._asked_rate,e)
                    # No "really holds only N Hz" and no "Nx larger": both
                    # came from the bogus ceiling estimate, and produced
                    # "This file says 96000 Hz but really holds only 96000 Hz
                    # of sound" — a sentence that contradicts itself, from
                    # arithmetic on a number that meant nothing (2026-09-10).
                    #   Say only what was measured: the upper part of the band
                    # is empty, so the rate buys nothing here. And warn that
                    # settling may take another take, because each take can
                    # only disprove the rate it was made at — the step down is
                    # one rate at a time by nature.
                    # A RECOMMENDATION, not a change. Nothing has been
                    # altered; the rate stays as chosen until the user says
                    # otherwise.
                    bad(_("This recording is stored as {asked} Hz, but the "
                          "top of its frequency range is empty.").format(
                                asked=self._asked_rate),
                        _("Something between A-Z+T and the microphone "
                          "stretched it to fit. Nothing is wrong with the "
                          "sound you hear and nothing has been changed — the "
                          "file is simply bigger than its content needs. If "
                          "that matters to you, choose a lower sample rate in "
                          "Sound Settings; the recording will sound the "
                          "same."))
                elif ceiling is None:
                    log.info("take: nothing suggests %d Hz is upsampled, but "
                             "it was too quiet to place the band edge either",
                             self._asked_rate)
                else:
                    # NOT "consistent with a real N Hz". Energy reaching
                    # Nyquist does not prove the rate is real: a cheap
                    # resampler's images land exactly where a converter's
                    # noise does. A shape-based test to separate them was
                    # attempted four ways and abandoned — see
                    # _mirror_test_abandoned_2026_09_10 in backend/core/sound.
                    # So report the measurement and claim nothing more.
                    log.info("take: energy up to %.0f Hz. That is consistent "
                             "with a real %d Hz, but does not prove it — a "
                             "resampler can put energy there too.",
                             ceiling,self._asked_rate)
                    # Report the GOOD outcome too, so an earlier "upsampled"
                    # mark can be withdrawn. The graph rate changes under us,
                    # so a mark made at one moment must not outlive evidence
                    # that it no longer holds.
                    try:
                        self.settings.note_real_rate(self._asked_rate)
                    except Exception as e:
                        log.info("couldn't clear the rate mark for %d Hz (%s)",
                                 self._asked_rate,e)
        except (NameError,AttributeError,TypeError) as e:
            # These mean the CHECK is broken, not the audio — and the check
            # silently not running is the same failure it exists to prevent.
            # It hid for a day as an `info` line reading like a normal
            # environmental hiccup: `spectral_ceiling` was never imported
            # here, so the upsampling test had never run once. Logged loudly
            # now, and still caught, because a broken diagnostic must not lose
            # the user's recording.
            log.error("the take's upsampling check is BROKEN and did not run "
                      "(%s: %s) — recordings are being saved without it",
                      type(e).__name__,e)
        except Exception as e:
            log.info("couldn't check the take's spectrum (%s)",e)
        # notify_user, not notify_error: the take is saved and the user is in
        # the middle of a word list. This appends to the one status window
        # instead of interrupting with a dialog per recording — and it is
        # wired to App.notify_user_threadsafe (main.py:818), so it is safe
        # from wherever fileclose() is called.
        if problems:
            try:
                notify_user("{}\n\n{}".format(
                        _("About the recording just made:"),
                        "\n\n".join("  * "+p for p in problems)))
            except Exception as e:
                log.error("couldn't show the take's problems to the user "
                          "(%s); they are in the log above",e)

    def fileclose(self):
        """Close the file and, only if it holds real audio, put it in place.

        The wait-for-the-stream loop is gone because stop() closes the stream
        before calling this, so there is nothing left in flight. The
        `.tmp`-then-replace dance stays exactly as it was: a take that fails
        `file_ok` must not overwrite a good recording.
        """
        sf=getattr(self,'_sf',None)
        if sf is not None:
            try:
                sf.close()
            except Exception as e:
                log.info("couldn't close the recording file ({})".format(e))
            self._sf=None
        # NOTHING TO FINALISE if start() never got a file open. Without this,
        # a failed start led to `file_ok()` → `getsize()` on a path that does
        # not exist, and the caller reported "Couldn't stop recorder; was it
        # on?" — which blamed the stop for the start's failure and buried the
        # real message (Kent 2026-09-10).
        if not file.exists(self.file_tmp):
            log.info("no recording to finalise (%s was never written)",
                     self.file_tmp)
            return
        self._report_take()
        if self.settings.file_ok(self.file_tmp):
            log.info(f"File recorded! ({file.getsize(self.file_tmp)})")
            self.file_write_OK=True
            file.replace(self.file_tmp,self.filenameURL)
        else:
            log.error("Nothing recorded! "
                        f"(file size: {file.getsize(self.file_tmp)})")
    def toaudiosample(self):
        """A 16 kHz mono WAV in memory, for ASR.

        NOT CALLED ANYWHERE (checked 2026-09-09) and it could not have worked
        if it were: `setsampwidth(self.settings.sample_format)` passed a
        PyAudio format CONSTANT where a byte width belongs — paInt32 is 2, so
        it declared 16-bit — and it neither resampled to the 16000 it claimed
        nor mixed down to the 1 channel it claimed.
          Rewritten rather than deleted because ASR does want exactly this and
        may reach for it: soundfile writes the real dtype, and the resampling
        is left to the ASR path (utilities/file_sound.py) which already does
        it properly. If this is ever wired up, resample there, not here.
        """
        import io
        if soundfile is None or not getattr(self,'_frames',None):
            log.info("nothing recorded to hand to ASR")
            return None
        buf=io.BytesIO()
        data=numpy.concatenate(self._frames)
        soundfile.write(buf,data,int(self.settings.fs),format='WAV')
        buf.seek(0)
        return buf
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
        """Stop recording, then close the file and put it in place.

        ORDER MATTERS, and it is the reverse of what it was: the stream is
        closed FIRST, so no callback can be writing while the file closes.
        The old version stopped the stream, then had `fileclose()` poll
        `stream.is_active()` in a sleep loop before writing everything it had
        buffered in memory. There is nothing to wait for now.
        """
        log.log(3,"I'm stopping recording now")
        self.streamclose()
        self.fileclose()
    def __init__(self,filenameURL,audio,settings):
        # Renamed from `pyaudio` 2026-09-09, same latent hazard the player's
        # had: a parameter of that name shadowed the imported MODULE for the
        # whole method, so any later edit reaching for a module attribute here
        # would have got an instance instead. (The player's was caught on
        # 2026-09-09; this one was missed in the same pass.)
        log.debug("Initializing Recording to {}".format(filenameURL))
        self.callbackrecording=True
        self.pa=audio
        self.settings=settings
        self.filenameURL=filenameURL

    @property
    def file_tmp(self):
        """Derived, not stored. `filenameURL` can be reassigned after
        construction — the mic-check screen does exactly that when the user
        changes rate or format (frontend/sound_ui.py) — and a `file_tmp`
        captured in __init__ would then point at the previous take, so the
        recording and the rename would disagree about which file they mean."""
        return str(self.filenameURL)+'.tmp'


class BeepGenerator(object):
    """Synthesised tone beeps for the Transcriber's tone letters.

    PORTED to sounddevice 2026-09-09. It kept no stream of its own: one was
    opened in __init__ and held for the object's life, which meant the
    Transcriber owned an output stream from the moment it was built, whether
    or not anyone ever pressed play. sounddevice opens and closes per play,
    so an idle Transcriber now holds no audio device at all.

    NOTHING SOUNDS DIFFERENT: the old playback's odd shape (a mono buffer fed
    to a 2-channel stream) is reproduced exactly, on purpose. See
    `_as_played()`.
    """
    def _as_played(self):
        """The compiled tone, ready for the device: plain mono.

        THE SOUND IS UNCHANGED FROM THE PyAudio ERA — the CONSTANTS changed
        instead, which is the difference between reproducing a quirk and
        reproducing a sound.

        What the old code did: opened the stream `channels = 2` and fed it a
        MONO buffer, so PortAudio consumed consecutive samples as left/right
        pairs. Each channel therefore got `sin(0.8π·(2n)·hz/bitrate)` — a
        CLEAN sine at double the frequency (700 Hz, far below Nyquist, so no
        aliasing) and half the length, the two channels a couple of degrees
        out of phase. Nothing was distorted; the numbers simply meant half
        what they said.
          So `hz=350` sounded 700, `secpersyl=.4` lasted 0.2s, and every
        `deltaHL` interval was doubled. Those are the values Kent tuned by
        ear, and they are the values the user's faster/slower/higher/lower
        controls multiply — so leaving them lying makes every adjustment lie
        too (Kent 2026-09-09: "I want tempo and pitch to have decent
        defaults, as they are user modifyable").
          The defaults below are now the doubled ones, played as mono. The
        arithmetic is exact, not approximate: mono `sin(0.8π·n·700/…)` is
        the same sequence as the old left channel's `sin(0.8π·(2n)·350/…)`,
        so the output is sample-for-sample what it always was.
        """
        return self.wavdata

    def play(self):
        """Play the compiled tone, at the pitch and length users know."""
        if not AUDIO_OK:
            log.info("no audio backend; no beeps")
            return
        try:
            sounddevice.play(self._as_played(), samplerate=self.bitrate)
        except Exception as e:
            log.info("couldn't play the tone beeps ({})".format(e))
    def pause(self):
        """A syllable's worth of silence. Was `stream.write(chr(0)*frames)` —
        a str of NULs into a float32 stream, which is not a valid frame buffer
        at all; whatever it produced was luck."""
        if not AUDIO_OK:
            return
        try:
            sounddevice.play(numpy.zeros(self.framespersyl,
                                         dtype=numpy.float32),
                             samplerate=self.bitrate)
        except Exception as e:
            log.info("couldn't pause ({})".format(e))
    def done(self):
        """Stop. There is no per-object stream to close any more."""
        try:
            sounddevice.stop()
        except Exception as e:
            log.info("nothing to stop ({})".format(e))
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
    # A few ms of ramp at each end of a segment. 4ms at 64000 = 256 samples,
    # far too short to alter the pitch and long enough to remove the step.
    declick_ms = 4

    def _declick(self, segment):
        """Fade a tone segment in and out, so joining it to silence does not
        click.

        YES, THE POPS WERE THE JOINS (Kent asked, 2026-09-09: "there's
        popping; is that from transitions to/fom zeros?"). Each segment is
        `sin(0.8π·n·hz/bitrate)`, which starts at zero but is CUT AFTER
        `nframes` SAMPLES wherever that lands in the cycle — typically at
        some non-zero amplitude. Appending silence after it is then a step
        from, say, 0.9 to 0.0 in one sample, and a step is a click. The same
        happens between two syllables at different pitches, and again at the
        word-break zeros.
          A raised-cosine ramp (not a straight line: linear ramps still leave
        a slope discontinuity, which is audible as a softer tick) takes each
        end to zero over a few milliseconds. Nothing else about the tone
        changes — which is the point, given the pitches and tempo are tuned
        by ear.
        """
        if numpy is None or segment is None or not len(segment):
            return segment
        n = min(int(self.bitrate * self.declick_ms / 1000.0), len(segment)//2)
        if n < 2:
            return segment
        ramp = (1.0 - numpy.cos(numpy.linspace(0.0, numpy.pi, n,
                                               dtype=numpy.float32))) / 2.0
        segment = segment.astype(numpy.float32).copy()
        segment[:n] *= ramp
        segment[-n:] *= ramp[::-1]
        return segment

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
                        # ── THE /2 IS LOAD-BEARING. DO NOT "SIMPLIFY" IT. ──
                        # This array spans only HALF the pitch difference
                        # (fromhz → fromhz+dhz/2), which looks like a glide
                        # that stops halfway. It isn't. The waveform below is
                        # sin(0.8π·n·f(n)/R), so the instantaneous frequency
                        # is (1/2π)·dφ/dn·R = 0.4·(f(n) + n·f′(n)) — the
                        # n·f′(n) term DOUBLES whatever slope this array has.
                        # With f(n) = fromhz + n·dhz/(2·nframes):
                        #   at n=0        → 0.4·fromhz
                        #   at n=nframes  → 0.4·(fromhz+dhz) = 0.4·tohz
                        # i.e. the audible glide starts on one pitch and ends
                        # on the other, linearly, exactly as intended. Widen
                        # this array to the full dhz and the glide overshoots
                        # to twice the interval.
                        #   (The same 0.4 applies to level tones: `hz` is not
                        # Hz. 0.8π rather than 2π means every pitch sounds at
                        # 0.4× its number, so hz=700 is 280 Hz and the five
                        # levels span 216–344 Hz.)
                        #
                        # linspace, NOT arange. `arange(fromhz, tohz-dhz/2,
                        # dhz/nframes/2)` is meant to produce exactly nframes
                        # values — the count is (dhz/2)÷(dhz/2/nframes) — but
                        # that quotient is computed in floating point, and
                        # when it lands a hair above nframes, arange emits one
                        # EXTRA value. It then multiplies against
                        # `arange(nframes)` and numpy refuses:
                        #   ValueError: operands could not be broadcast
                        #   together with shapes (5632,) (5633,)
                        # A latent fencepost that happened to be safe at the
                        # old syllable length and fired the moment the tempo
                        # default changed (2026-09-09). linspace takes the
                        # COUNT as an argument, so it cannot miscount.
                        #   Same values as before: endpoint=False reproduces
                        # arange's half-open interval, and tohz-dhz/2 is
                        # fromhz+dhz/2, so start, stop and spacing all match.
                        hz=numpy.linspace(fromhz,fromhz+dhz/2.0,nframes,
                                          endpoint=False,
                                          dtype=numpy.float32)
                    step=1
                    if not done:
                        self.wavdata=numpy.append(self.wavdata,
                                self._declick(numpy.sin(
                                0.8*numpy.pi*(numpy.arange(
                                                    nframes,dtype=numpy.float32
                                                        )*hz)/self.bitrate
                                            ))
                                    ).astype(numpy.float32)
            self.wavdata=numpy.append(self.wavdata,numpy.zeros(int(self.secperwordbreak*self.bitrate),dtype=numpy.float32))
        # KEEP THE NUMPY ARRAY. `.tobytes()` was for PyAudio's byte-oriented
        # stream.write(); sounddevice takes the array — and takes the channel
        # count and dtype FROM it, which is what makes the mono fix in play()
        # work.
        self.wavdata = self.wavdata.astype(numpy.float32)
        # The debug copy on disk, via soundfile rather than `wave`: `wave`
        # writes a header claiming N-byte PCM, so float32 samples through it
        # produced a file whose header contradicted its contents (and its
        # sample width came from PyAudio's get_sample_size, now gone).
        # soundfile knows what float32 is.
        #   Written in the SHAPE THAT PLAYS (_as_played), not the raw mono
        # buffer, so the file on disk sounds like what came out of the
        # speakers. That is the point of a debug copy.
        try:
            soundfile.write('test'+__name__+'.wav', self._as_played(),
                            int(self.bitrate))
        except Exception as e:
            log.info("couldn't write the beep debug wav ({})".format(e))
    def __init__(self,audio=None,settings=None):
        if not audio:
            self.p = AudioInterface()
        else:
            self.p = audio
        if not settings:
            # STILL WRONG, and left alone on purpose: this hands an AUDIO
            # HANDLE to a parameter named `program` (see
            # frontend/transcriber.py:87-99, which documents the trap and the
            # divergent second settings object it yields). It does not raise,
            # because `program` is only dereferenced later — so "fixing" it
            # here would change which object callers get. Every real caller
            # now passes settings; this branch is a trap for the next one.
            self.settings=SoundSettings(self.p)
        else:
            self.settings=settings
        # float32 IS right here, unlike on the file paths: this data is a
        # numpy sine wave, so float32 is its natural dtype and no conversion
        # happens. Kent's caution ("a bug somewhere that made 32float cause
        # problems") was about asking a CARD to accept float32 as its output
        # format for recorded audio; sounddevice converts for the device.
        self.format='float32'
        self.bitrate = 64000
        # DOUBLED / HALVED 2026-09-09, and the sound did NOT change: these
        # are the values the old stereo-fed-mono stream actually produced
        # (see _as_played). Every one of them is a user dial, so they now say
        # what they do — a "higher" click multiplies a real frequency, and a
        # stored setting will mean something.
        self.hz = 700           # was 350, and sounded 700
        self.deltaHL = 80       # was 40, and every interval was doubled
        # TEMPO IS A NEW DEFAULT, not a preserved one (Kent 2026-09-09: "this
        # is way too fast for a default"). The old numbers said .4/.05/.15 and
        # DELIVERED half of each — .2s syllables — because of the stereo
        # doubling; making the numbers honest exposed that the tempo everyone
        # had was the fast one. These are the values the code always claimed,
        # now actually produced: a syllable long enough to hear its contour,
        # and breaks in proportion to it.
        self.secpersyl = .4
        self.secpersylbreak = .05
        self.secperwordbreak = .15
        # NO STREAM HERE ANY MORE. This used to open one in the constructor
        # and hold it for the object's life, so every Transcriber owned an
        # output device from the moment it was built — pressed or not.
        # sounddevice opens per play() and closes when it finishes.
        self.setparameters()


if __name__ == "__main__":
    """Set volume, somehow!!"""
    analang='tbt'
    # Both of these need a program: Languages assigns `program.languages=self`
    # and SoundSettings reaches for `program.audio`. Neither was being given
    # one, so this block raised before it played anything (2026-09-09) — the
    # same two omissions as frontend/transcriber.py's standalone run.
    from dummy import App
    from backend import langtags
    program=App()
    languages=langtags.Languages(program)
    language=languages.get_obj(analang)
    soundsettings=SoundSettings(program,analang_obj=language)
    log.info(f"soundsettings.asr_kwargs: {soundsettings.asr_kwargs}")
    # Pass the settings we just built rather than letting BeepGenerator's
    # fallback construct its own — that fallback is `SoundSettings(self.p)`,
    # which hands an AUDIO HANDLE to the `program` parameter (documented at
    # frontend/transcriber.py:87-99) and quietly yields a second, divergent
    # settings object.
    b=BeepGenerator(audio=soundsettings.audio,settings=soundsettings)
    b.compile()
    b.play()
    log.info("Done!")
