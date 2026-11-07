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

Chunking is by pauses (an approximation of phonological clauses), the same algorithm as
azt_asr/transcribe.py: 10 ms RMS frames; silence is `silence_db` below the loud (95th-percentile) level;
a pause of `min_pause` s ends a chunk; chunks over `max_chunk` s split at their deepest pause; shorter than
`min_chunk` s are dropped; `pad` s kept at each edge.
"""
import copy
import hashlib
import os
import re
import subprocess
import sys
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
WORD_BEGIN, WORD_END = 'begin-time-offset', 'end-time-offset'   # items on a <word>, ms (wordbreaks.py)
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


def segment(audio, rate=SR, min_pause=0.25, silence_db=25.0, max_chunk=15.0, min_chunk=0.3, pad=0.1):
    """Pause-delimited chunks, as [(begin_ms, end_ms)]."""
    frame = rate // 100
    n = len(audio) // frame
    if n == 0:
        return []
    rms = np.sqrt((audio[:n * frame].reshape(n, frame) ** 2).mean(axis=1)) + 1e-10
    db = 20 * np.log10(rms)
    silent = db < np.percentile(db, 95) - silence_db
    fps = rate / frame

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

    def split_long(s):
        a, b = s
        if (b - a) / fps <= max_chunk:
            return [s]
        inner = silent_runs(silent[a:b], 2) or [((b - a) // 2, (b - a) // 2)]
        x, y = max(inner, key=lambda r: (r[1] - r[0], -abs((r[0] + r[1]) / 2 - (b - a) / 2)))
        return split_long((a, a + x)) + split_long((a + y, b))

    total_ms = round(len(audio) * 1000 / rate)
    chunks = [c for s in spans for c in split_long(s) if (c[1] - c[0]) / fps >= min_chunk]
    return [(max(0, round((a / fps - pad) * 1000)), min(total_ms, round((b / fps + pad) * 1000)))
            for a, b in chunks]


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
        its own thread) into the phrase with the same guid here. Returns the number of phrases changed."""
        found = {p.get('guid'): p.find('words') for p in other.iter('phrase')}
        n = 0
        for phrase in self.node.iter('phrase'):
            words = found.get(phrase.get('guid'))
            if words is None:
                continue
            old = phrase.find('words')
            index = list(phrase).index(old) if old is not None else len(phrase)
            if old is not None:
                phrase.remove(old)
            phrase.insert(index, copy.deepcopy(words))
            n += 1
        return n

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
            chunks = segment(audio)
            title = os.path.splitext(os.path.basename(audio_path))[0]
            text = self.add(audio_path, md5, chunks, title)
            log.info(f"new text '{title}': {len(chunks)} chunks from {audio_path}")
            self.save()
        return text, audio

    def save(self):
        ET.indent(self.root)
        tmp = self.path + '.tmp'
        ET.ElementTree(self.root).write(tmp, encoding='utf-8', xml_declaration=True)
        os.replace(tmp, self.path)


# ---- words (azt_asr/wordbreaks.py) -------------------------------------------------------------------------

MMS_CANDIDATE = re.compile(r'^facebook/mms-1b-all \((\w+)!\)$')   # bulk ASR's key for an MMS-1b-all adapter


def wordbreaks():
    """azt_asr's wordbreaks module ("Find words"). Found as a plain import (an installed azt_asr), else as the
    azt_asr folder beside the azt folder, as backend/core/collab.py finds azt-collab. It imports torch, so call
    this off the main thread. Raises ImportError (with the reason) if it can't be had."""
    try:
        from azt_asr import wordbreaks as module
        return module
    except ImportError as e:
        reason = e
    azt_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    suite_root = os.path.dirname(azt_root)
    if not os.path.isfile(os.path.join(suite_root, 'azt_asr', 'wordbreaks.py')):
        raise ImportError(f"no azt_asr folder beside {azt_root} ({reason})")
    if suite_root not in sys.path:
        sys.path.append(suite_root)   # last: nothing else in the suite folder may shadow azt's own modules
    from azt_asr import wordbreaks as module   # its ImportError, if any, says what is missing
    log.info(f"azt_asr located beside azt, at {suite_root}")
    return module


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
               should_cancel=None, mms=None):
    """wordbreaks over `snapshot` (a copy of a text's node, made on the main thread: this runs on a worker
    thread while the page goes on using the text); the words go into the copy, for Text.take_words on the main
    thread. `audio` is the recording at SR (wordbreaks' rate too). Writes the TextGrid and the per-clause report.
    mms: loaded_mms()'s (model, feat, lock), to borrow and give back; the lock is released here, however this
    ends. Returns wordbreaks' counts."""
    wb = wordbreaks()
    model, feat, lock = mms or (None, None, None)
    try:
        aligner = wb.Aligner(log.info, adapter=adapter, cache_dir=cache_dir, model=model, feat=feat)
        try:
            return wb.find_words(snapshot, textgrid=textgrid, tsv=tsv, log=log.info, root=project_dir,
                                 audio=audio, aligner=aligner, progress=progress, should_cancel=should_cancel)
        finally:
            aligner.release()
    finally:
        if lock is not None:
            lock.release()


def chunk_files(text, audio, phrases, folder):
    """Write each phrase's span of `audio` (at SR) as a wav in `folder`, for the ASR models, which take
    paths. Returns {path: phrase}. Named by md5 and times, so a file is the same chunk wherever it is."""
    os.makedirs(folder, exist_ok=True)
    out = {}
    for p in phrases:
        path = os.path.join(folder, f"{text.md5}_{p.begin_ms}_{p.end_ms}.wav")
        if not os.path.exists(path):
            write_wav(path, span(audio, p.begin_ms, p.end_ms))
        out[path] = p
    return out
