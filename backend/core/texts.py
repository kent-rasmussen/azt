# coding=UTF-8
"""Texts: long recordings, cut into clause chunks, transcribed chunk by chunk.

The project keeps ONE FLExText file beside its LIFT file, `<liftbase>.texts.flextext`, holding one
`interlinear-text` per recording. It is schema-valid FLEx interlinear XML (FlexInterlinear.xsd lets an
item's `type` be any string), with our data in items of our own types:

    <interlinear-text guid=...>
      <item type="title" lang=analang>…</item>
      <item type="media-md5" lang=analang>md5 of the recording's bytes</item>   ← its identity
      <item type="speaker" lang=analang>…</item>
      <item type="other-voices" lang=analang>…</item>
      <paragraphs><paragraph guid=...><phrases>
        <phrase guid=... begin-time-offset="570" end-time-offset="2570" media-file=MEDIA-GUID>
          <item type="segnum" lang=analang>1</item>
          <item type="txt" lang=lang>final transcription</item>            once someone saved one
          <item type="candidate-<model key>" lang=lang>ASR output</item>   one per model
          <item type="chosen" lang=analang><model key></item>             button(s) the final started from
          <words>                                                          required by the schema; filled
            <word guid=...>                                                by "Find words" (wordbreaks.py)
              <item type="txt" lang=lang>form</item>
              <item type="begin-time-offset" lang=analang>ms</item>       in the recording, like the phrase's
              <item type="end-time-offset" lang=analang>ms</item>
              <item type="word-source" lang=analang>consensus</item>      final | consensus | single
            </word> …
          </words>
        </phrase> …
      </phrases></paragraph></paragraphs>
      <languages>…</languages>
      <media-files offset-type="milliseconds">
        <media guid=MEDIA-GUID location="audio/story.ogg"/>    relative to the project folder, '/'-separated
      </media-files>
    </interlinear-text>

THE CHUNK IS (md5, begin ms, end ms). Times are whole milliseconds from the start of the recording, so the
text can be rebuilt from its phrases, and a span is cut at samples round(ms * rate / 1000) everywhere
(transcribing, playing, exporting). Clauses play from the whole recording, not from chunk files (decided
2026-11-04: context before/after, original quality, and merging/splitting changes only two numbers).
A recording whose md5 is not in the file is a NEW text: a re-recorded file starts over, as word drafts do
(ADR 0002).

The recordings themselves are in `<project>/texts/` (texts_dir; before 2026-11-06 they were in the audio folder,
and a text whose recording moved is found by md5 and its location updated). Per-recording outputs go there too,
named by the recording's stem: `<stem>_words.TextGrid` and
`<stem>_words.tsv` from "Find words". The word lexicon of all the texts is there too
(backend/core/text_lexicon.py).

Chunking is by pauses (an approximation of phonological clauses); segment() has the details. It started as
azt_asr/transcribe.py's algorithm and has moved on from it (2026-11-19). What counts as a pause is decided by
a DETECTOR: 'energy' (10 ms RMS frames against a threshold from the recording's own levels), 'silero'
(Silero VAD, MIT licence, if the silero-vad package is installed) or 'prosody' (Silero's pauses plus cuts at
level dips with a pitch reset: azt_asr/boundaries.py); the rest is the same for all. Each new
recording is cut with --segmenter=NAME (default silero, plan A since 2026-11-20; energy where it can't run), and
also with every other detector that can run, into
`<stem>_segments.TextGrid` (a tier each), to compare them (Kent, 2026-11-19).
"""
import copy
import hashlib
import os
import re
import subprocess
import sys
import unicodedata
import uuid
import xml.etree.ElementTree as ET

import numpy as np

from utilities import logsetup
log = logsetup.getlog(__name__)

SR = 16000                 # ASR rate; chunks for the models are cut from this copy
AUDIO_EXTENSIONS = ('.wav', '.flac', '.ogg', '.opus', '.mp3', '.m4a', '.aac')
MIN_TEXT_SECONDS = 60      # shorter recordings are words/phrases, not texts
MIN_BYTES_PER_SECOND = 750 # 6 kbit/s, below any speech codec's usual rate: a file smaller than
                           # MIN_TEXT_SECONDS of this can't be a text, so it isn't probed at all

MD5 = 'media-md5'
SPEAKER = 'speaker'
VOICES = 'other-voices'
CANDIDATE = 'candidate-'   # + model key
CHOSEN = 'chosen'
CAREFUL = 'careful-audio'   # phrase item: the clause said again carefully, a file in texts/ ('audio/…')
# Once a clause has a careful take, its ASR and its word cuts come ONLY from the take (Kent, 2026-11-21). What
# audio they came from is kept beside them, so a take recorded later can't leave them pointing at the wrong one:
ASR_AUDIO = 'asr-audio'       # phrase item: the take its candidates came from ('' or absent: the recording)
WORDS_AUDIO = 'words-audio'   # phrase item: the take its words are timed in (absent: ms in the recording)
WORD_BEGIN, WORD_END = 'begin-time-offset', 'end-time-offset'   # items on a <word>, ms (wordbreaks.py)
# Also on a <word>: what its token in the transcription has around its bare form (`txt`, which the word lexicon
# sorts: no capitals, no punctuation; Kent 2026-11-23), to put the transcription back together (azt_asr/tokens.py)
PUNCT_BEFORE, PUNCT_AFTER, CASE = 'punct-before', 'punct-after', 'case'
TEXTS_FOLDER = 'texts'     # in the project folder: per-recording outputs (word TextGrid, word lexicon)


def _guid():
    return str(uuid.uuid4())


def md5_of(path):
    with open(path, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()


# ---- audio -----------------------------------------------------------------------------------------------

_durations = {}   # (path, mtime) -> seconds


MP4_EXTENSIONS = ('.m4a', '.mp4', '.m4v', '.3gp')


def _mp4_duration(path):
    """Seconds from an MP4/M4A file's `moov/mvhd` header, or None. A few seeks and reads, where
    ffprobe is a whole process per file — the difference between a second and half a minute over a
    folder of phone-recorded word clips. Atoms are walked by size, so a `moov` at the end is found."""
    import struct

    def atoms(f, start, end):
        pos = start
        while pos + 8 <= end:
            f.seek(pos)
            head = f.read(8)
            if len(head) < 8:
                return
            size, kind = struct.unpack('>I4s', head)
            body = pos + 8
            if size == 1:
                size = struct.unpack('>Q', f.read(8))[0]
                body = pos + 16
            elif size == 0:
                size = end - pos
            if size < 8:
                return
            yield kind, body, pos + size
            pos += size

    with open(path, 'rb') as f:
        end = os.fstat(f.fileno()).st_size
        for kind, body, stop in atoms(f, 0, end):
            if kind != b'moov':
                continue
            for kind2, body2, _stop2 in atoms(f, body, stop):
                if kind2 != b'mvhd':
                    continue
                f.seek(body2)
                version = f.read(4)[0]
                if version == 1:
                    f.seek(16, 1)
                    timescale, length = struct.unpack('>IQ', f.read(12))
                else:
                    f.seek(8, 1)
                    timescale, length = struct.unpack('>II', f.read(8))
                return length / timescale if timescale else None
    return None


def duration(path):
    """Seconds, or None if nothing can read it. Cached per file version.
    MP4 header first (m4a), then soundfile (wav, flac, ogg, mp3), then ffprobe for the rest."""
    try:
        key = (str(path), os.path.getmtime(path))
    except OSError:
        return None
    if key in _durations:
        return _durations[key]
    seconds = None
    if str(path).lower().endswith(MP4_EXTENSIONS):
        try:
            seconds = _mp4_duration(path)
        except Exception as e:
            log.info(f"couldn't read the MP4 header of {path} ({e}); trying the other readers")
        if seconds is not None:
            _durations[key] = seconds
            return seconds
    try:
        import soundfile
        seconds = soundfile.info(str(path)).duration
    except Exception:
        try:
            out = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                                  '-of', 'default=nw=1:nk=1', str(path)],
                                 capture_output=True, text=True, check=True).stdout
            seconds = float(out.strip())
        except Exception as e:
            log.info(f"couldn't read the length of {path}: {e}")
    _durations[key] = seconds
    return seconds


def texts_dir(project_dir):
    """<project>/texts: the texts' recordings (Kent, 2026-11-06: not in audio/, with the word clips) and what is
    made from them."""
    return os.path.join(str(project_dir), TEXTS_FOLDER)


def recordings(audiodir, min_seconds=MIN_TEXT_SECONDS):
    """[(path, seconds)] of the recordings in `audiodir` long enough to be texts, by name.
    The audio folder holds thousands of word clips; a size check (one stat) rules them out before any
    probe, since an m4a probe is an ffprobe process each."""
    out = []
    try:
        names = sorted(os.listdir(audiodir))
    except OSError as e:
        log.info(f"can't list {audiodir}: {e}")
        return out
    import time
    started = time.perf_counter()
    min_bytes = min_seconds * MIN_BYTES_PER_SECOND
    measured = 0
    for name in names:
        path = os.path.join(audiodir, name)
        if not name.lower().endswith(AUDIO_EXTENSIONS):
            continue
        try:
            if not os.path.isfile(path) or os.path.getsize(path) < min_bytes:
                continue
        except OSError:
            continue
        measured += 1
        seconds = duration(path)
        if seconds and seconds > min_seconds:
            out.append((path, seconds))
    log.info(f"texts: {len(out)} recordings over {min_seconds} s in {audiodir}; {measured} of "
             f"{len(names)} files measured (the rest too small) in {time.perf_counter() - started:.2f}s")
    return out


def load_audio(path, rate=SR):
    """Mono float32 at `rate`. soundfile for what it reads; ffmpeg for the rest (m4a, aac)."""
    try:
        import soundfile
        data, sr = soundfile.read(str(path), dtype='float32', always_2d=True)
        data = data.mean(axis=1)
        if sr != rate:
            from math import gcd
            from scipy.signal import resample_poly
            g = gcd(sr, rate)
            data = resample_poly(data, rate // g, sr // g).astype('float32')
        return data
    except Exception as e:
        log.info(f"soundfile couldn't read {path} ({e}); decoding with ffmpeg")
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(path), '-ac', '1', '-ar', str(rate),
                          '-f', 'f32le', '-'], capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype='<f4').copy()


def span(audio, begin_ms, end_ms, rate=SR):
    return audio[round(begin_ms * rate / 1000):round(end_ms * rate / 1000)]


def energy_silence(audio, rate, db, silence_db=25.0, floor_db=6.0, min_drop=12.0, smooth=5):
    """Detector 'energy': which 10 ms frames (`db`, their levels) are silent, and a note for the log.
      - silent below a threshold set from the recording's own levels: the speech level (95th percentile) less
        `silence_db`, OR the noise floor (10th percentile) plus `floor_db` (but at least `min_drop` below the
        speech level), whichever is higher — so the background noise of a field recording counts as quiet;
      - smoothed by a majority over `smooth` frames, so a click or one loud frame doesn't break a pause in two."""
    speech, floor = np.percentile(db, 95), np.percentile(db, 10)
    # The old peak-relative rule, unless the noise floor is above it; the floor-based one never less than
    # `min_drop` below speech, so a recording with no pauses in it (its 10th percentile is speech) doesn't have
    # its quieter speech called silence. In a clean recording this is the old threshold exactly.
    threshold = max(speech - silence_db, min(floor + floor_db, speech - min_drop))
    silent = db < threshold
    if smooth > 1:
        before = smooth // 2   # ends padded with their own flags, not 'sounding'
        votes = np.convolve(np.pad(silent.astype(int), (before, smooth - 1 - before), mode='edge'),
                            np.ones(smooth, dtype=int), mode='valid')
        silent = votes > smooth // 2
    return silent, f"speech {speech:.1f} dB, floor {floor:.1f} dB, silent below {threshold:.1f} dB"


_silero_model = None


def silero_silence(audio, rate, db):
    """Detector 'silero': frames outside the speech Silero VAD finds (github.com/snakers4/silero-vad, MIT
    licence; the silero-vad package, which needs only torch). Its own merging is turned off (no minimum speech
    or silence, no padding), so segment() decides pauses for both detectors alike. Raises ImportError when the
    package isn't installed."""
    silent, note, _probs = _silero(audio, rate, len(db))
    return silent.copy(), note


SILERO_WINDOW = 512   # samples per Silero probability at 16 kHz (32 ms); its own get_speech_timestamps' size


def silero_probabilities(audio, rate=SR):
    """Silero's speech probability per 10 ms frame (its 32 ms windows, each frame taking the window it falls
    in). The curve get_speech_timestamps thresholds and then throws away (Kent, 2026-11-20: secondary
    breakpoint candidates, and a curve to see in Praat). Raises ImportError without silero-vad."""
    frame = rate // 100
    _silent, _note, probs = _silero(audio, rate, len(audio) // frame)
    return probs


def _silero(audio, rate, n_frames):
    """(silent flags per 10 ms frame, note, speech probability per 10 ms frame), for `audio`, kept for the
    last recording: the detector, prosody's pauses and breakpoints all ask for it. The probabilities are
    computed here as get_speech_timestamps computes them (reset_states, then model(512 samples, rate) per
    window), so the stretches are the same as before, and the curve is kept."""
    global _silero_model, _silero_last
    import torch
    from silero_vad import load_silero_vad, get_speech_timestamps_from_probs
    key = (len(audio), rate, n_frames, hashlib.md5(np.ascontiguousarray(audio[::997]).tobytes()).hexdigest())
    if _silero_last and _silero_last[0] == key:
        return _silero_last[1]
    if _silero_model is None:
        _silero_model = load_silero_vad()
    samples = torch.from_numpy(np.ascontiguousarray(audio, dtype=np.float32))
    window = SILERO_WINDOW if rate == 16000 else SILERO_WINDOW // 2
    probs = []
    _silero_model.reset_states()
    with torch.no_grad():
        for start in range(0, len(samples), window):
            chunk = samples[start:start + window]
            if len(chunk) < window:
                chunk = torch.nn.functional.pad(chunk, (0, window - len(chunk)))
            probs.append(_silero_model(chunk, rate).item())
    stamps = get_speech_timestamps_from_probs(probs, sampling_rate=rate, min_speech_duration_ms=0,
                                              min_silence_duration_ms=0, speech_pad_ms=0,
                                              audio_length_samples=len(samples))
    fps = 100
    silent = np.ones(n_frames, dtype=bool)
    for s in stamps:
        silent[int(s['start'] / rate * fps):int(np.ceil(s['end'] / rate * fps))] = False
    frame = rate // fps
    per_frame = np.array(probs)[np.minimum((np.arange(n_frames) * frame + frame // 2) // window, len(probs) - 1)] \
        if probs else np.zeros(n_frames)
    result = (silent, f"{len(stamps)} stretches of speech", per_frame)
    _silero_last = (key, result)
    return result


def write_intensity_tier(path, values, xmax, step=0.01):
    """`values` (one per `step` s, from 0) as a Praat IntensityTier text file: open it in Praat with the
    recording to see the curve (e.g. Silero's speech probability × 100)."""
    lines = ['File type = "ooTextFile"', 'Object class = "IntensityTier"', '', 'xmin = 0', f'xmax = {xmax}',
             f'points: size = {len(values)}']
    for i, v in enumerate(values, 1):
        lines += [f'points [{i}]:', f'    number = {(i - 0.5) * step:.3f}', f'    value = {float(v):.2f}']
    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')


_silero_last = None


def prosody_silence(audio, rate, db):
    """Detector 'prosody' (agenda: prosodic boundaries; Kent, 2026-11-19, the third point to compare): the
    pauses of Silero (plan A; energy's where it can't run), less those the pitch carries on across (short
    hesitations inside a clause), plus cuts INSIDE sounding stretches where the level dips and the pitch resets
    (azt_asr/boundaries.py). So its tier differs from silero's by exactly what prosody changes. Raises
    ImportError without azt_asr's boundaries module or parselmouth."""
    boundaries = _azt_asr('boundaries')
    try:
        silent, _note = silero_silence(audio, rate, db)
        base = 'silero'
    except ImportError:
        silent, _note = energy_silence(audio, rate, db)
        base = 'energy'
    found = boundaries.prosodic_boundaries(audio, rate, silent, db)
    return found['silent'], f"pauses by {base}; {len(found['cuts'])} prosodic cuts; {found['note']}", \
        found['cuts']


BREAKPOINTS = 'breakpoints'   # phrase item: places it could be split, "ms:score:start:end:depth:p …", best first


def breakpoints_for(audio, chunks=None, rate=SR):
    """The places the recording could be split (azt_asr boundaries.breakpoints: silences, level dips, pitch
    resets), for "split this in 2/3/4" and for judging the clause boundaries themselves (Kent, 2026-11-20).
    Each is (ms, score, start ms, end ms, depth dB, p): the place, the quiet stretch it is in, how far under
    the speech level around it 0.2 s of quiet can be found, and Silero's lowest speech probability in the
    stretch (None without Silero).
    Found over the WHOLE recording, not clause by clause (Kent, 2026-11-20): a pause at a clause's edge is that
    boundary's evidence, and was missed when only a clause's inside was looked at. With `chunks` [(begin_ms,
    end_ms)], returns one list per chunk, of the places whose stretch overlaps it (so a place straddling a
    boundary is in both clauses), best first; without, one list of them all. Silences by energy's flags.
    Raises ImportError without azt_asr's boundaries module."""
    boundaries = _azt_asr('boundaries')
    frame = rate // 100
    n = len(audio) // frame
    rms = np.sqrt((audio[:n * frame].reshape(n, frame) ** 2).mean(axis=1)) + 1e-10
    db = 20 * np.log10(rms)
    silent, _note = energy_silence(audio, rate, db)
    try:   # Silero's speech probability: its sags are places too, and evidence at the others (2026-11-20)
        vad = silero_probabilities(audio, rate)
    except ImportError:
        vad = None
    except Exception as e:
        log.error(f"breakpoints: no Silero probabilities ({e})")
        vad = None
    found, note = boundaries.breakpoints(audio, rate, [(0, n)], silent, db, limit=None, vad=vad)
    places = [(c * 10, score, s * 10, e * 10, depth, p) for c, score, s, e, depth, p in found[0]]
    log.info(f"breakpoints: {len(places)} in the recording ({note})")
    if chunks is None:
        return [places]
    return [[p for p in places if p[2] < end and p[3] > begin] for begin, end in chunks]


# name -> f(audio, rate, db) -> (silent flags per 10 ms frame, note[, frames to cut at inside sounding
# stretches]). A detector that can't run raises ImportError (its package is missing).
DETECTORS = {'energy': energy_silence, 'silero': silero_silence, 'prosody': prosody_silence}


DEFAULT_SEGMENTER = 'silero'   # plan A (Kent, 2026-11-20: it beat energy 9 times in 10); energy where it can't run


def segmenter_switch(argv=None):
    """--segmenter=NAME: the detector that cuts new recordings (default DEFAULT_SEGMENTER; segment() falls back
    to energy, and logs it, where that can't run)."""
    for a in (sys.argv if argv is None else argv):
        if a.startswith('--segmenter='):
            name = a.split('=', 1)[1]
            if name in DETECTORS:
                return name
            log.error(f"--segmenter={name}: no such detector (there are {', '.join(DETECTORS)}); "
                      f"using {DEFAULT_SEGMENTER}")
    return DEFAULT_SEGMENTER


def segment(audio, rate=SR, detector='energy', min_pause=0.2, max_chunk=8.0, min_chunk=0.3, edge=1.0, pad=0.1,
            name='', fallback=True):
    """Pause-delimited chunks, as [(begin_ms, end_ms)], in 10 ms frames (Kent, 2026-11-19):
      - `detector` (DETECTORS) says which frames are silent; if it can't run, energy does, and the log says so
        (with fallback=False, its ImportError is raised instead);
      - a PAUSE is `min_pause` (0.2 s, "a more linguistically real value") or more of silence;
      - a chunk longer than `max_chunk` (8 s; was 15) is cut at its longest inner silence, or if it has none,
        at its quietest 100 ms at least `edge` s from either end;
      - a chunk shorter than `min_chunk` joins a neighbour (merge_short): nothing that sounds is dropped.
    `name` is for the log line only."""
    frame = rate // 100
    n = len(audio) // frame
    if n == 0:
        return []
    rms = np.sqrt((audio[:n * frame].reshape(n, frame) ** 2).mean(axis=1)) + 1e-10
    db = 20 * np.log10(rms)
    try:
        silent, note, *cuts = DETECTORS[detector](audio, rate, db)
    except ImportError as e:
        if not fallback:
            raise
        log.info(f"segment {name}: detector {detector} unavailable ({e}); using energy")
        detector = 'energy'
        silent, note = energy_silence(audio, rate, db)
        cuts = []
    cuts = sorted(cuts[0]) if cuts else []
    silent = silent[:n]
    fps = rate / frame
    # the level over 100 ms around each frame: where a chunk with no silence in it is quietest
    # (ends padded with their own values: zero-padding reads as 0 dB, the loudest there is)
    quiet = np.convolve(np.pad(db, (5, 4), mode='edge'), np.ones(10) / 10, mode='valid')
    stats = {'dips': 0, 'merged': 0}

    def silent_runs(flags, min_frames):
        runs, start = [], None
        for i, s in enumerate(list(flags) + [False]):
            if s and start is None:
                start = i
            elif not s and start is not None:
                if i - start >= min_frames:
                    runs.append((start, i))
                start = None
        return runs

    pauses = silent_runs(silent, int(min_pause * fps))
    edges = [0] + [x for p in pauses for x in p] + [len(silent)]
    spans = [(edges[i], edges[i + 1]) for i in range(0, len(edges), 2) if edges[i + 1] > edges[i]]
    if cuts:   # a detector's own boundaries inside sounding stretches (prosody), before any length rule
        cut_spans = []
        for a, b in spans:
            inner = [c for c in cuts if a < c < b]
            ends = [a] + inner + [b]
            cut_spans += list(zip(ends, ends[1:]))
        spans = cut_spans
    stats['cuts'] = len(cuts)

    def split_long(s):
        a, b = s
        if (b - a) / fps <= max_chunk:
            return [s]
        inner = silent_runs(silent[a:b], 2)
        if inner:
            x, y = max(inner, key=lambda r: (r[1] - r[0], -abs((r[0] + r[1]) / 2 - (b - a) / 2)))
        else:
            # no silence at all: the quietest 100 ms, not too near either end (the middle if it's too short)
            lo, hi = a + int(edge * fps), b - int(edge * fps)
            x = y = (int(np.argmin(quiet[lo:hi])) + lo - a) if hi > lo else (b - a) // 2
            stats['dips'] += 1
        return split_long((a, a + x)) + split_long((a + y, b))

    def merge_short(chunks):
        """A chunk shorter than min_chunk joins its neighbour across the SHORTER of its two pauses (the left one
        on a tie); alone, it stays. Short ones used to be dropped, so a short word between two pauses ('mm',
        'yes') was in no phrase at all (Kent, 2026-11-19: every sounding stretch belongs somewhere)."""
        chunks = list(chunks)
        while len(chunks) > 1:
            k = next((k for k, (a, b) in enumerate(chunks) if (b - a) / fps < min_chunk), None)
            if k is None:
                break
            left = chunks[k][0] - chunks[k - 1][1] if k > 0 else None
            right = chunks[k + 1][0] - chunks[k][1] if k < len(chunks) - 1 else None
            if right is None or (left is not None and left <= right):
                chunks[k - 1:k + 1] = [(chunks[k - 1][0], chunks[k][1])]
            else:
                chunks[k:k + 2] = [(chunks[k][0], chunks[k + 1][1])]
            stats['merged'] += 1
        return chunks

    total_ms = round(len(audio) * 1000 / rate)
    chunks = merge_short(c for s in spans for c in split_long(s))
    lengths = [(b - a) / fps for a, b in chunks]
    # What decided the cuts, so a chunk that looks wrong can be traced to its threshold (Kent, 2026-11-19).
    log.info(f"segment {name} by {detector}: {note}; "
             f"{len(pauses)} pauses of {min_pause} s+; {len(chunks)} chunks (longest "
             f"{max(lengths, default=0):.1f} s, median {float(np.median(lengths)) if lengths else 0:.1f} s); "
             f"{stats['dips']} cut at a quiet dip, not a silence; {stats['merged']} short ones merged")
    return [(max(0, round((a / fps - pad) * 1000)), min(total_ms, round((b / fps + pad) * 1000)))
            for a, b in chunks]


def compare_segments(audio, out_path, clauses=None, rate=SR, name='', breakpoints=None):
    """Cut `audio` with every detector that can run, and write a Praat TextGrid at `out_path` with a tier each
    (Kent, 2026-11-19: to see how each splits the clauses), after a 'clauses' tier of the text's own chunks
    [(begin_ms, end_ms)] when given, and a 'breakpoints' tier (each over its quiet stretch, labelled with its
    score and length) when `breakpoints` (breakpoints_for's, per clause) are. Detector tiers are UNPADDED (pad=0), so their gaps are
    the pauses each found; intervals are numbered. A detector that can't run gets no tier (logged). Returns
    {detector: chunks}."""
    textgrid = _azt_asr('textgrid')
    tiers, found = [], {}
    if clauses:
        tiers.append(('clauses', [(b / 1000, e / 1000, str(i)) for i, (b, e) in enumerate(clauses, 1)]))
    if breakpoints:
        # each over its quiet stretch, labelled "score / length ms / depth of 0.2 s of quiet" (Kent, 2026-11-20:
        # a 20 ms mark hid what happens across the break)
        # set: a place straddling a clause boundary is in both clauses' lists
        marks = sorted({(start, end, score, depth, p)
                        for places in breakpoints for _ms, score, start, end, depth, p in places})
        tiers.append(('breakpoints', [(s / 1000, max(e, s + 10) / 1000,
                                       f"{score:g} / {e - s} ms / 200 ms at "
                                       f"{'?' if depth is None else f'-{depth:g}'} dB"
                                       + ('' if p is None else f" / p {p:g}"))
                                      for s, e, score, depth, p in marks]))
    for detector in DETECTORS:
        try:
            found[detector] = segment(audio, rate, detector=detector, pad=0, name=name, fallback=False)
        except ImportError as e:
            log.info(f"compare_segments {name}: no {detector} tier ({e})")
            continue
        tiers.append((detector, [(b / 1000, e / 1000, str(i)) for i, (b, e) in enumerate(found[detector], 1)]))
    textgrid.write_textgrid(out_path, len(audio) / rate, tiers)
    log.info(f"compare_segments {name}: tiers {', '.join(t for t, _s in tiers)} -> {out_path}")
    # Silero's speech probability as a curve to see beside it (× 100, so 0–100): <stem>_silero.IntensityTier
    try:
        probs = silero_probabilities(audio, rate)
        stem = out_path[:-len('_segments.TextGrid')] if out_path.endswith('_segments.TextGrid') \
            else os.path.splitext(out_path)[0]
        write_intensity_tier(stem + '_silero.IntensityTier', np.asarray(probs) * 100, len(audio) / rate)
        log.info(f"compare_segments {name}: Silero's speech probability -> {stem}_silero.IntensityTier")
    except ImportError as e:
        log.info(f"compare_segments {name}: no Silero curve ({e})")
    return found


def write_wav(path, audio, rate=SR):
    import soundfile
    soundfile.write(str(path), audio, rate, subtype='PCM_16')


# ---- the FLExText ----------------------------------------------------------------------------------------

def _items(node):
    return node.findall('item')


def _get(node, type_):
    item = node.find(f"item[@type='{type_}']")
    return (item.text or '') if item is not None else ''


def _set(node, type_, lang, value, after=()):
    """Set (or, for '', remove) the item of this type; a new one goes after the last item of a type in
    `after`, else after the node's last item — schema order: items before child elements."""
    item = node.find(f"item[@type='{type_}']")
    if not value:
        if item is not None:
            node.remove(item)
        return
    if item is None:
        item = ET.Element('item', {'type': type_, 'lang': lang})
        children = list(node)
        index = 0
        for i, child in enumerate(children):
            if child.tag == 'item' and (not after or child.get('type') in after):
                index = i + 1
        node.insert(index, item)
    item.text = value


class Phrase:
    """One clause chunk of a text."""

    def __init__(self, node, text):
        self.node = node
        self.text = text

    @property
    def guid(self):
        return self.node.get('guid')

    @property
    def begin_ms(self):
        return int(self.node.get('begin-time-offset'))

    @property
    def end_ms(self):
        return int(self.node.get('end-time-offset'))

    @property
    def number(self):
        return _get(self.node, 'segnum')

    def candidates(self):
        """{model key: text}, in the order stored."""
        n = len(CANDIDATE)
        return {i.get('type')[n:]: i.text or '' for i in _items(self.node)
                if i.get('type', '').startswith(CANDIDATE)}

    def add_candidates(self, found):
        """Store new model outputs beside the old; a model run again replaces its own."""
        for model, value in found.items():
            if value:
                _set(self.node, CANDIDATE + model, self.text.lang, value, after=('segnum', 'txt')
                     + tuple(CANDIDATE + m for m in self.candidates()))

    def final(self):
        return _get(self.node, 'txt')

    def chosen(self):
        return [i.text for i in _items(self.node) if i.get('type') == CHOSEN and i.text]

    def breakpoints(self):
        """[(ms, score, start ms, end ms, depth dB, p)] where this clause could be split, best first: the
        place, the quiet stretch it is in (times in the recording), how far under the speech level 0.2 s of
        quiet is found around it, and Silero's lowest speech probability in the stretch (None: unknown); [] if
        none stored (texts cut before 2026-11-20 have none). Shorter older forms are still read ("ms:score",
        with start = end = ms; "ms:score:start:end"; "…:depth")."""
        out = []
        for place in (_get(self.node, BREAKPOINTS) or '').split():
            parts = place.split(':')
            try:
                ms, score = int(parts[0]), float(parts[1])
                start, end = (int(parts[2]), int(parts[3])) if len(parts) >= 4 else (ms, ms)
                depth = float(parts[4]) if len(parts) >= 5 and parts[4] else None
                p = float(parts[5]) if len(parts) >= 6 and parts[5] else None
                out.append((ms, score, start, end, depth, p))
            except (ValueError, IndexError):
                log.info(f"phrase {self.guid}: unreadable breakpoint {place!r}")
        return out

    def set_breakpoints(self, places):
        def num(x):
            return '' if x is None else f'{x:g}'
        if places:
            _set(self.node, BREAKPOINTS, self.text.analang,
                 ' '.join(f"{ms}:{score:g}:{start}:{end}:{num(depth)}:{num(p)}"
                          for ms, score, start, end, depth, p in places),
                 after=('segnum',))

    def words(self):
        """[(guid, form, begin_ms, end_ms)] of the words "Find words" stored (azt_asr/wordbreaks.py); the
        times are None for a word it couldn't align."""
        out = []
        for w in self.node.findall('words/word'):
            begin, end = _get(w, WORD_BEGIN), _get(w, WORD_END)
            out.append((w.get('guid'), _get(w, 'txt'),
                        int(begin) if begin else None, int(end) if end else None))
        return out

    def set_final(self, value, chosen=None):
        """The person's transcription; `chosen` lists the model keys whose candidate it started from
        (several when models agreed), or None to leave the record as it is (an edit of a value already
        saved), or [] for typed from scratch."""
        _set(self.node, 'txt', self.text.lang, value, after=('segnum',))
        if chosen is not None:
            for item in [i for i in _items(self.node) if i.get('type') == CHOSEN]:
                self.node.remove(item)
            for model in chosen:
                item = ET.Element('item', {'type': CHOSEN, 'lang': self.text.analang})
                item.text = model
                self.node.append(item)

    def careful(self):
        """The clause said again carefully: its file name relative to the texts folder ('audio/…'), or None."""
        return _get(self.node, CAREFUL) or None

    def set_careful(self, filename):
        _set(self.node, CAREFUL, self.text.analang, filename or '', after=('segnum',))

    def careful_path(self):
        """The careful take's full path, if the clause has one and the file is there; else None."""
        name = self.careful()
        if not name:
            return None
        path = os.path.join(self.text.db.project_dir, TEXTS_FOLDER, *name.split('/'))
        return path if os.path.exists(path) else None

    def take_recorded(self, filename):
        """A careful take was just saved for this clause: link it, and drop the ASR candidates, which heard other
        audio (the recording, or an earlier take under the same name). Its words stay until "Parse" makes them
        again from the take (keeping their guids where they continue: wordbreaks.kept_guids)."""
        self.set_careful(filename)
        self.clear_candidates()

    def asr_audio(self):
        """The take this clause's candidates came from, or '' (the recording)."""
        return _get(self.node, ASR_AUDIO)

    def set_asr_audio(self, filename):
        _set(self.node, ASR_AUDIO, self.text.analang, filename or '', after=('segnum',))

    def clear_candidates(self):
        """Drop the models' candidates (not `chosen`: that is the history of the person's transcription)."""
        for item in [i for i in _items(self.node)
                     if i.get('type', '').startswith(CANDIDATE) or i.get('type') == ASR_AUDIO]:
            self.node.remove(item)

    def stale_candidates(self):
        """True if the candidates heard other audio than the clause's ASR now uses (its take, else the
        recording): a take linked before candidates said where they came from, or the take was redone."""
        return bool(self.candidates()) and self.asr_audio() != self.audio_source()

    def audio_source(self):
        """What the clause's ASR and words are made from now: its take ('audio/…') if the file is there, else ''
        (its span of the recording)."""
        return self.careful() if self.careful_path() else ''

    def words_audio(self):
        """The take this clause's word times are in ('audio/…'), or None: ms in the recording."""
        return _get(self.node, WORDS_AUDIO) or None


class Text:
    """One recording's interlinear-text."""

    def __init__(self, node, db):
        self.node = node
        self.db = db
        self.lang = db.lang
        self.analang = db.analang

    @property
    def md5(self):
        return _get(self.node, MD5)

    @property
    def location(self):
        media = self.node.find('media-files/media')
        return media.get('location') if media is not None else ''

    def path(self):
        return os.path.join(self.db.project_dir, *self.location.split('/'))

    @property
    def guid(self):
        return self.node.get('guid')

    @property
    def stem(self):
        """The recording's file name without its extension: names this text's files in the texts folder."""
        return os.path.splitext(os.path.basename(self.location))[0]

    def output_path(self, suffix):
        """<project>/texts/<recording stem><suffix> (the folder made if need be)."""
        folder = os.path.join(self.db.project_dir, TEXTS_FOLDER)
        os.makedirs(folder, exist_ok=True)
        return os.path.join(folder, self.stem + suffix)

    def take_words(self, other):
        """Put the <words> of each phrase of `other` (a copy of this text's node, that "Find words" filled on
        its own thread) into the phrase with the same guid here, with the take they are timed in (WORDS_AUDIO).
        Returns the number of phrases changed."""
        found = {p.get('guid'): p for p in other.iter('phrase')}
        n = 0
        for phrase in self.node.iter('phrase'):
            source = found.get(phrase.get('guid'))
            words = source.find('words') if source is not None else None
            if words is None:
                continue
            old = phrase.find('words')
            index = list(phrase).index(old) if old is not None else len(phrase)
            if old is not None:
                phrase.remove(old)
            phrase.insert(index, copy.deepcopy(words))
            _set(phrase, WORDS_AUDIO, self.analang, _get(source, WORDS_AUDIO), after=('segnum',))
            n += 1
        return n

    def renumber(self):
        """Each phrase's segnum: its place in the text, from 1."""
        for n, phrase in enumerate(self.phrases(), 1):
            _set(phrase.node, 'segnum', self.analang, str(n))

    def split_phrase(self, phrase, cuts_ms):
        """Cut `phrase` at `cuts_ms` (inside it, ascending) into len(cuts_ms) + 1 phrases, the first keeping its
        node and guid, the rest new, next to it in order; then renumber. Returns the pieces (Phrases).
        What each piece keeps (Kent, 2026-11-20, the split screen):
          - WORDS go to the piece their middle falls in, guids kept (so their lexicon entries follow them);
            a word with no times stays in the first piece, and so do all the words of a clause whose words were
            timed in its careful take (their times aren't in the recording), with the take's name;
          - the person's TRANSCRIPTION is split with them when it has as many words as were found (they come
            from it); otherwise it stays on the first piece;
          - ASR candidates and the models they were chosen from are dropped: they were for the whole clause
            (run ASR again for the pieces);
          - BREAKPOINTS go to every piece their stretch overlaps;
          - a careful-speech take of the whole clause no longer matches any piece, so its link is dropped (the
            file stays)."""
        begin, end = phrase.begin_ms, phrase.end_ms
        cuts = [c for c in sorted(cuts_ms) if begin < c < end]
        if not cuts:
            return [phrase]
        spans = list(zip([begin] + cuts, cuts + [end]))
        words = phrase.words()
        final = phrase.final()
        pieces_of_final = transcription_tokens(final) if final else []   # one per word, as Parse found them
        split_final = bool(pieces_of_final) and len(pieces_of_final) == len(words)
        places = phrase.breakpoints()
        container = next(p for p in self.node.iter('phrases') if phrase.node in list(p))
        original = copy.deepcopy(phrase.node)

        timed_in_take = phrase.words_audio() is not None

        def piece_of(word):
            _g, _f, b, e = word
            if b is None or e is None or timed_in_take:
                return 0   # untimed, or timed in the take, not the recording: no place among the pieces
            middle = (b + e) / 2
            return next((i for i, (_s, e2) in enumerate(spans) if middle < e2), len(spans) - 1)

        assigned = [piece_of(w) for w in words]
        nodes = [phrase.node]
        at = list(container).index(phrase.node)
        for i in range(1, len(spans)):
            node = copy.deepcopy(original)
            node.set('guid', _guid())
            at += 1
            container.insert(at, node)
            nodes.append(node)
        pieces = []
        for i, (node, (b, e)) in enumerate(zip(nodes, spans)):
            node.set('begin-time-offset', str(b))
            node.set('end-time-offset', str(e))
            for item in [it for it in _items(node)
                         if it.get('type', '').startswith(CANDIDATE)
                         or it.get('type') in (CHOSEN, CAREFUL, ASR_AUDIO, BREAKPOINTS, 'txt')
                         or (i and it.get('type') == WORDS_AUDIO)]:
                node.remove(item)
            box = node.find('words')
            if box is None:
                box = ET.SubElement(node, 'words')
            for w in list(box):
                box.remove(w)
            for w, k in zip(original.findall('words/word'), assigned):
                if k == i:
                    box.append(copy.deepcopy(w))
            piece = Phrase(node, self)
            if split_final:
                piece.set_final(' '.join(t for t, k in zip(pieces_of_final, assigned) if k == i))
            elif final and i == 0:
                piece.set_final(final)
            piece.set_breakpoints([p for p in places if p[2] < e and p[3] > b])
            pieces.append(piece)
        self.renumber()
        log.info(f"text '{self.title}': phrase {phrase.guid} ({begin}–{end} ms) split at {cuts} into "
                 f"{len(pieces)}; transcription {'split by words' if split_final else 'kept on the first'}")
        return pieces

    def join_phrases(self, first, second):
        """Join `second` onto `first`, the clause right after it (Kent, 2026-11-23: badly split clauses), the
        reverse of split_phrase: `first` keeps its node and guid and runs to `second`'s end; then renumber.
        Returns `first`, or None if `second` doesn't come right after it. What the joined clause keeps:
          - WORDS: both clauses', in order, guids kept (so their lexicon entries follow them); words timed in a
            careful take lose their times (the take doesn't cover the joined clause): "Parse" times them again;
          - TRANSCRIPTION: both clauses' text joined with a space, when either was transcribed (a clause not
            transcribed contributes its words, as its text is shown everywhere else);
          - BREAKPOINTS: both clauses' (the same place once);
          - dropped, as on a split: ASR candidates, the models they were chosen from, careful-take links (the
            files stay)."""
        phrases = self.phrases()
        at = next((i for i, p in enumerate(phrases) if p.node is first.node), None)
        if at is None or at + 1 >= len(phrases) or phrases[at + 1].node is not second.node:
            return None
        container = next((c for c in self.node.iter('phrases') if second.node in list(c)), None)
        if container is None or first.node not in list(container):
            return None   # in another paragraph: not one clause's neighbour in the file

        def text_of(p):
            return p.final() or ' '.join(word_token(w) for w in p.node.findall('words/word'))
        either_final = bool(first.final() or second.final())
        joined = ' '.join(t for t in (text_of(first), text_of(second)) if t)
        places = {p[0]: p for p in first.breakpoints() + second.breakpoints()}
        timed_in_take = [p for p in (first, second) if p.words_audio()]
        box = first.node.find('words')
        if box is None:
            box = ET.SubElement(first.node, 'words')
        if timed_in_take:
            for p in timed_in_take:
                for w in p.node.findall('words/word'):
                    for item in [i for i in w.findall('item') if i.get('type') in (WORD_BEGIN, WORD_END)]:
                        w.remove(item)
        for w in second.node.findall('words/word'):
            box.append(copy.deepcopy(w))
        begin, end = first.end_ms, second.end_ms
        first.node.set('end-time-offset', str(end))
        for item in [it for it in _items(first.node)
                     if it.get('type', '').startswith(CANDIDATE)
                     or it.get('type') in (CHOSEN, CAREFUL, ASR_AUDIO, WORDS_AUDIO, BREAKPOINTS, 'txt')]:
            first.node.remove(item)
        if either_final and joined:
            first.set_final(joined)
        first.set_breakpoints(sorted(places.values(), key=lambda p: -p[1]))
        container.remove(second.node)
        self.renumber()
        log.info(f"text '{self.title}': phrase {second.guid} joined onto {first.guid} (was {first.begin_ms}–"
                 f"{begin} ms, now to {end} ms); transcription {'joined' if either_final else 'none'}"
                 + (f"; {len(timed_in_take)} take-timed clause(s) left untimed" if timed_in_take else ''))
        return first

    def sync_words(self):
        """Make each transcribed clause's words say what its transcription now does, before sorting (Kent,
        2026-11-23): the word lexicon is built from the words, and "Parse" made them from the transcription
        as it was then. Same number of tokens as words: each word takes its token's spelling, keeping its
        guid and times (no break moved). Otherwise the breaks changed, and the words must be found and timed
        again: those clauses are returned, as guids, for find_words(only=…). Returns (words respelled,
        {guids to find again})."""
        def nfc(s):
            return unicodedata.normalize('NFC', s or '')
        keys = (('txt', 'form'), (PUNCT_BEFORE, 'before'), (PUNCT_AFTER, 'after'), (CASE, 'case'))
        respelled, again = 0, set()
        for phrase in self.phrases():
            final = phrase.final()
            if not final:
                continue
            # bare forms + punctuation + case (tokens.words_of), as Parse writes them; words written before
            # 2026-11-23 kept the whole token as their form, and are brought to this here too
            parts = tokens().words_of(final)
            nodes = phrase.node.findall('words/word')
            stored = [tuple(nfc(_get(w, t)) for t, _k in keys) for w in nodes]
            wanted = [tuple(nfc(p[k]) for _t, k in keys) for p in parts]
            if stored == wanted:
                continue
            if len(parts) != len(nodes):
                again.add(phrase.guid)
                continue
            for w, have, want, part in zip(nodes, stored, wanted, parts):
                if have != want:
                    for type_, key in keys:
                        _set(w, type_, self.lang, part[key])
                    respelled += 1
        if respelled or again:
            log.info(f"text '{self.title}': {respelled} words respelled from their transcriptions; "
                     f"{len(again)} clauses' breaks changed, to find again")
        return respelled, again

    def get(self, type_):
        return _get(self.node, type_)

    def set(self, type_, value):
        _set(self.node, type_, self.analang, value.strip(), after=('title', MD5, SPEAKER, VOICES))

    title = property(lambda self: self.get('title'), lambda self, v: self.set('title', v))
    speaker = property(lambda self: self.get(SPEAKER), lambda self, v: self.set(SPEAKER, v))
    voices = property(lambda self: self.get(VOICES), lambda self, v: self.set(VOICES, v))

    def phrases(self):
        return [Phrase(p, self) for p in self.node.iter('phrase')]

    def progress(self):
        """(phrases with a final transcription, phrases)."""
        ps = self.phrases()
        return sum(1 for p in ps if p.final()), len(ps)

    def counts(self):
        """For the texts board: {'clauses', 'asr' (with a model's candidate), 'worded' (with words found),
        'words', 'final' (transcribed by the person)}."""
        ps = self.phrases()
        words = [len(p.node.findall('words/word')) for p in ps]
        return {'clauses': len(ps), 'asr': sum(1 for p in ps if p.candidates()),
                'worded': sum(1 for n in words if n), 'words': sum(words),
                'final': sum(1 for p in ps if p.final())}


class TextsDB:
    """The project's texts file. Read on open; written by save() (to a temporary file, then renamed)."""

    def __init__(self, path, project_dir, lang, analang='en'):
        self.path = str(path)
        self.project_dir = str(project_dir)
        self.lang = lang
        self.analang = analang
        if os.path.exists(self.path):
            self.root = ET.parse(self.path).getroot()
            # Files written before 2026-11-04 lack the `words` element FlexInterlinear.xsd requires.
            for phrase in self.root.iter('phrase'):
                if phrase.find('words') is None:
                    ET.SubElement(phrase, 'words')
        else:
            self.root = ET.Element('document', {'version': '2'})

    def texts(self):
        return [Text(t, self) for t in self.root.findall('interlinear-text')]

    def find(self, md5):
        for t in self.texts():
            if t.md5 == md5:
                return t
        return None

    def location_of(self, audio_path):
        return os.path.relpath(os.path.abspath(audio_path), os.path.abspath(self.project_dir)
                               ).replace(os.sep, '/')

    def at(self, audio_path):
        """The text last opened from this file, by location (no md5: the board reads this for every recording
        each time it's drawn); None if it hasn't been opened. Opening it (open_recording) still goes by md5."""
        location = self.location_of(audio_path)
        found = [t for t in self.texts() if t.location == location]
        if not found:   # moved here and not opened since (open_recording then puts in the new location)
            name = os.path.basename(audio_path)
            found = [t for t in self.texts() if t.location.split('/')[-1] == name
                     and not os.path.exists(t.path())]
        return found[-1] if found else None

    def add(self, audio_path, md5, chunks, title):
        """A new text for this recording, one phrase per (begin_ms, end_ms) chunk."""
        media_guid = _guid()
        text = ET.SubElement(self.root, 'interlinear-text', {'guid': _guid()})
        for type_, value in (('title', title), (MD5, md5)):
            ET.SubElement(text, 'item', {'type': type_, 'lang': self.analang}).text = value
        phrases = ET.SubElement(ET.SubElement(ET.SubElement(text, 'paragraphs'), 'paragraph',
                                              {'guid': _guid()}), 'phrases')
        for n, (begin_ms, end_ms) in enumerate(chunks, 1):
            phrase = ET.SubElement(phrases, 'phrase', {
                'guid': _guid(), 'begin-time-offset': str(begin_ms), 'end-time-offset': str(end_ms),
                'media-file': media_guid})
            ET.SubElement(phrase, 'item', {'type': 'segnum', 'lang': self.analang}).text = str(n)
            ET.SubElement(phrase, 'words')   # required by FlexInterlinear.xsd, even empty
        languages = ET.SubElement(text, 'languages')
        ET.SubElement(languages, 'language', {'lang': self.lang, 'vernacular': 'true'})
        ET.SubElement(languages, 'language', {'lang': self.analang})
        media_files = ET.SubElement(text, 'media-files', {'offset-type': 'milliseconds'})
        ET.SubElement(media_files, 'media', {'guid': media_guid, 'location': self.location_of(audio_path)})
        return Text(text, self)

    def open_recording(self, audio_path):
        """The text for this recording: found by md5, or cut into chunks and added (then saved).
        Returns (text, audio at SR) — the audio is needed to cut chunks for ASR anyway."""
        md5 = md5_of(audio_path)
        audio = load_audio(audio_path)
        text = self.find(md5)
        if text is not None and text.location != self.location_of(audio_path):
            # the same recording, moved (texts' audio went from audio/ to texts/, 2026-11-06)
            log.info(f"text '{text.title}' moved: {text.location} -> {self.location_of(audio_path)}")
            text.node.find('media-files/media').set('location', self.location_of(audio_path))
            self.save()
        if text is None:
            chunks = segment(audio, detector=segmenter_switch(), name=os.path.basename(audio_path))
            title = os.path.splitext(os.path.basename(audio_path))[0]
            text = self.add(audio_path, md5, chunks, title)
            log.info(f"new text '{title}': {len(chunks)} chunks from {audio_path}")
            places = None
            try:   # where each clause could be split, for "split this in 2/3/4" later (Kent, 2026-11-20)
                places = breakpoints_for(audio, chunks)
                by_begin = dict(zip((b for b, _e in chunks), places))
                for phrase in text.phrases():
                    phrase.set_breakpoints(by_begin.get(phrase.begin_ms))
            except Exception as e:
                log.error(f"couldn't find breakpoints for {audio_path}: {e}")
            try:   # every detector's cuts side by side, for comparing (Kent, 2026-11-19); never fatal
                compare_segments(audio, text.output_path('_segments.TextGrid'), chunks,
                                 name=os.path.basename(audio_path), breakpoints=places)
            except Exception as e:
                log.error(f"couldn't write the segment comparison for {audio_path}: {e}")
            self.save()
        return text, audio

    def save(self):
        ET.indent(self.root)
        tmp = self.path + '.tmp'
        ET.ElementTree(self.root).write(tmp, encoding='utf-8', xml_declaration=True)
        os.replace(tmp, self.path)


# ---- words (azt_asr/wordbreaks.py) -------------------------------------------------------------------------

MMS_CANDIDATE = re.compile(r'^facebook/mms-1b-all \((\w+)!\)$')   # bulk ASR's key for an MMS-1b-all adapter


def _azt_asr(module_name):
    """A module of azt_asr. Found as a plain import (an installed azt_asr), else as the azt_asr folder beside
    the azt folder, as backend/core/collab.py finds azt-collab. Raises ImportError (with the reason) if it can't
    be had."""
    import importlib
    try:
        return importlib.import_module(f'azt_asr.{module_name}')
    except ImportError as e:
        reason = e
    azt_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    suite_root = os.path.dirname(azt_root)
    if not os.path.isfile(os.path.join(suite_root, 'azt_asr', f'{module_name}.py')):
        raise ImportError(f"no azt_asr/{module_name}.py beside {azt_root} ({reason})")
    if suite_root not in sys.path:
        sys.path.append(suite_root)   # last: nothing else in the suite folder may shadow azt's own modules
        log.info(f"azt_asr located beside azt, at {suite_root}")
    return importlib.import_module(f'azt_asr.{module_name}')   # its ImportError, if any, says what is missing


def tokens():
    """azt_asr/tokens.py: a transcription's words as bare forms + their punctuation and case. Standard library
    only, so it is there whenever azt_asr is."""
    return _azt_asr('tokens')


def word_token(node, form=None):
    """A <word>'s token in the transcription: its form (or `form`, a respelling) with its punctuation and case
    put back. A word written before 2026-11-23 has none of those items: its txt is its token."""
    return tokens().surface(_get(node, 'txt') if form is None else form, _get(node, PUNCT_BEFORE),
                            _get(node, PUNCT_AFTER), _get(node, CASE))


def transcription_tokens(final):
    """The tokens of a transcription, one per word as words_of() finds them (a punctuation-only token goes
    with its neighbour), each as surface() puts it back."""
    t = tokens()
    return [t.surface(**w) for w in t.words_of(final)]


def wordbreaks():
    """azt_asr's wordbreaks module ("Find words"). It imports torch, so call this off the main thread."""
    return _azt_asr('wordbreaks')


def align_adapter(text, tally=None):
    """The released MMS-1b-all adapter (ISO 639-3 code) to align `text`'s words with: of the adapters that gave
    it candidates, the one picked most often (tally: {model key: picks}, as SoundSettings.asr_repos), then the
    one with the most candidates in the text. None if no MMS-1b-all adapter gave any."""
    found = {}   # code -> (key, candidates)
    for phrase in text.phrases():
        for key in phrase.candidates():
            m = MMS_CANDIDATE.match(key)
            if m:
                code = m.group(1)
                found[code] = (key, found.get(code, (key, 0))[1] + 1)
    if not found:
        return None
    tally = tally or {}
    return max(sorted(found), key=lambda c: (tally.get(found[c][0], 0), found[c][1]))


def loaded_mms(program):
    """(model, feature extractor) of the MMS-1b-all azt's ASR has loaded, or None. Transcribing the clauses and
    finding their words are adjacent steps, so the second borrows the first's model rather than load a second
    ~4 GB copy (Kent, 2026-11-06); when it isn't loaded, Find words loads its own and drops it at the end.
    Borrowing takes the ASR's mms_lock (ASR waits until find_words gives it back); if ASR holds it now, this
    doesn't wait: None, and Find words loads its own. Returns (model, feat, lock), the lock held."""
    asr = getattr(getattr(program, 'soundsettings', None), 'asr', None)
    pipe = (getattr(asr, 'models', None) or {}).get('facebook/mms-1b-all')
    model = getattr(pipe, 'model', None)
    feat = getattr(pipe, 'feature_extractor', None)
    lock = getattr(asr, 'mms_lock', None)
    if model is None or feat is None or lock is None:
        return None
    if not lock.acquire(blocking=False):
        log.info("ASR is using mms-1b-all; Find words loads its own copy")
        return None
    return model, feat, lock


def find_words(snapshot, audio, project_dir, textgrid, tsv, adapter, cache_dir=None, progress=None,
               should_cancel=None, mms=None, takes=None, only=None):
    """wordbreaks over `snapshot` (a copy of a text's node, made on the main thread: this runs on a worker
    thread while the page goes on using the text); the words go into the copy, for Text.take_words on the main
    thread. `audio` is the recording at SR (wordbreaks' rate too). Writes the TextGrid and the per-clause report.
    mms: loaded_mms()'s (model, feat, lock), to borrow and give back; the lock is released here, however this
    ends. takes: take_audio()'s {phrase guid: (take name, audio)}: those clauses' words are cut from their take,
    timed in it, and the take's name put on the clause (WORDS_AUDIO); every other clause's WORDS_AUDIO is
    cleared. only: guids of the clauses to do (Text.sync_words); then no TextGrid or report is written, as
    they would hold only those. Returns wordbreaks' counts."""
    if only is not None:
        textgrid = tsv = None
    wb = wordbreaks()
    takes = takes or {}
    analang = next((l.get('lang') for l in snapshot.iter('language') if l.get('vernacular') != 'true'), 'en')
    model, feat, lock = mms or (None, None, None)
    try:
        aligner = wb.Aligner(log.info, adapter=adapter, cache_dir=cache_dir, model=model, feat=feat)
        try:
            def timed_in_take(phrase):
                """wordbreaks asks this for each clause it times: the take's audio, or None (its span of the
                recording). Either way the clause says which (WORDS_AUDIO), as its new times will be."""
                take = takes.get(phrase.get('guid'))
                _set(phrase, WORDS_AUDIO, analang, take[0] if take else '', after=('segnum',))
                return take[1] if take else None
            return wb.find_words(snapshot, textgrid=textgrid, tsv=tsv, log=log.info, root=project_dir,
                                 audio=audio, aligner=aligner, progress=progress, should_cancel=should_cancel,
                                 phrase_audio=timed_in_take, only=only)
        finally:
            aligner.release()
    finally:
        if lock is not None:
            lock.release()


def chunk_files(text, audio, phrases, folder):
    """Write each phrase's span of `audio` (at SR) as a wav in `folder`, for the ASR models, which take
    paths. Returns {path: phrase}. Named by md5 and times, so a file is the same chunk wherever it is.
    A clause with a careful take is the take instead (Kent, 2026-11-21), at SR, named by the take and its time
    (a take recorded again is a new chunk)."""
    os.makedirs(folder, exist_ok=True)
    out = {}
    for p in phrases:
        take = p.careful_path()
        if take:
            stamp = int(os.path.getmtime(take))
            path = os.path.join(folder, f"{text.md5}_{os.path.splitext(os.path.basename(take))[0]}_{stamp}.wav")
            if not os.path.exists(path):
                write_wav(path, load_audio(take))
        else:
            path = os.path.join(folder, f"{text.md5}_{p.begin_ms}_{p.end_ms}.wav")
            if not os.path.exists(path):
                write_wav(path, span(audio, p.begin_ms, p.end_ms))
        out[path] = p
    return out


def take_audio(text):
    """{phrase guid: (take name, audio at SR)} for each clause of `text` with a careful take: what its words are
    cut from, instead of its span of the recording (find_words)."""
    out = {}
    for p in text.phrases():
        take = p.careful_path()
        if take:
            try:
                out[p.guid] = (p.careful(), load_audio(take))
            except Exception as e:
                log.error(f"couldn't read the careful take {take}: {e}; its clause's words come from the "
                          f"recording")
    return out
