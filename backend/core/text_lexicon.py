# coding=UTF-8
"""The word lexicon of the project's texts: `<project>/texts/<liftbase>_text_words.lift`, for sorting the words
found in them. ONE lexicon for all the texts, not one per text (Kent, 2026-11-06): the words of several texts
are sorted together. (Until then each text had `<project>/texts/<recording stem>.lift`; the first build of the
shared one takes in their entries, sorting and all — absorb().)

Made by "Sort words from these texts" on the Transcribe Texts board, from the words "Find words" stored in the
texts file (backend/core/texts.py). Not a project of its own: it uses the main project's settings and audio
folder.

ONE ENTRY PER OCCURRENCE (Kent, 2026-11-05), never one per word form: merged entries would have to be split
later, each usage assigned to one side. "Same word" is a sameSort set instead, which the user can split and
join; sets are preloaded only for identical transcriptions.

    <entry guid=WORD-GUID id=WORD-GUID dateCreated=… dateModified=…>    the flextext word's guid: the link back
      <citation>                                                        no lexical-unit
        <form lang=analang><text>word</text></form>
        <form lang=analang-Zxxx-x-audio><text>story.ogg#t=12.340,12.810</text></form>
      </citation>
      <sense id=…>
        <grammatical-info value="Word"/>                                no gloss
        <example>                                                       the word's phrase; no location field,
          <form lang=analang><text>phrase text</text></form>            so it isn't a tone frame
          <form lang=analang-Zxxx-x-audio><text>story.ogg#t=12.000,14.500</text></form>
          <trait name="text-phrase" value=PHRASE-GUID/>
        </example>
        <trait name="sameSort" value=SET-ID/>                           only in a set of two or more
      </sense>
    </entry>

Audio is a span of the recording (W3C media fragment), relative to the project's audio folder; nothing is cut.

RERUN-SAFE: entries already in the file are never changed (they may carry sorting), except that a new
occurrence identical to an existing singleton puts both in a new set, which adds the trait to the old one, and
that a recording that moved has its new name put in the spans (_follow_moves).
The recording's name is relative to the lexicon's own folder, <project>/texts/, which is its audio folder when
it is open (backend/core/file_parser.py): 'story.ogg'. Takes recorded in it go in texts/audio/ ('audio/…').
Words no longer in the texts (another "Find words" changed their forms, so their guids) are counted, not deleted.
"""
import os
import unicodedata
import uuid
import xml.etree.ElementTree as ET

from backend import langtags
from backend.core import texts
from io_put import lift
from utilities import logsetup
log = logsetup.getlog(__name__)

PS = 'Word'                # only for transcription; real categories if words ever go into the main lexicon
PRODUCER = 'A-Z+T text word lexicon'
LIFT_VERSION = '0.13'


def _key(form):
    """What counts as an identical transcription: the same characters, once composed (NFC)."""
    return unicodedata.normalize('NFC', form or '')


def _form(parent, lang, value):
    form = ET.SubElement(parent, 'form', {'lang': lang})
    ET.SubElement(form, 'text').text = value
    return form


def _set_id(entry):
    trait = entry.find(f"sense/trait[@name='{lift.SAMESORT_TRAIT}']")
    return trait.get('value') if trait is not None else None


def recording_name(text, audiodir):
    """The text's recording relative to `audiodir` (the lexicon's folder), '/'-separated ('texts/story.ogg' in
    the texts file -> 'story.ogg')."""
    return os.path.relpath(os.path.abspath(text.path()), os.path.abspath(str(audiodir))).replace(os.sep, '/')


def text_phrases(text):
    """[{'guid', 'text', 'begin_ms', 'end_ms', 'words': [(guid, form, begin_ms, end_ms)]}] of a texts.Text.
    A phrase's text is its final transcription if it has one, else its words joined by spaces."""
    out = []
    for p in text.phrases():
        words = p.words()
        out.append({'guid': p.guid, 'text': p.final() or ' '.join(form for _g, form, _b, _e in words),
                    'begin_ms': p.begin_ms, 'end_ms': p.end_ms, 'words': words})
    return out


def word_count(phrases):
    return sum(len(p['words']) for p in phrases)


def _fragment(recording, begin_ms, end_ms):
    return lift.media_fragment(recording, begin_ms / 1000, end_ms / 1000)


def _follow_moves(entries, phrases, recording, audiolang):
    """Point existing entries' text spans at their recording's current name, when it has moved (texts' audio went
    from audio/ to texts/, and spans are named from texts/, 2026-11-06): only the file part of the citation's and the phrase example's audio form
    changes, never the times. Returns the number of entries changed."""
    where = {w[0]: p.get('recording', recording) for p in phrases for w in p['words']}
    n = 0
    for guid, entry in entries.items():
        now = where.get(guid)
        if not now:
            continue
        changed = False
        for form in (entry.findall(f"citation/form[@lang='{audiolang}']")
                     + [f for ex in entry.findall('sense/example')
                        if ex.find(f"trait[@name='{lift.PHRASE_TRAIT}']") is not None
                        for f in ex.findall(f"form[@lang='{audiolang}']")]):
            text = form.find('text')
            if text is None or not text.text:
                continue
            name, span = lift.split_media_fragment(text.text)
            if span is not None and name != now:
                text.text = now + text.text[len(name):]
                changed = True
        if changed:
            entry.set('dateModified', lift.getnow())
            n += 1
    return n


def make_lexicon(path, phrases, recording, analang, audiolang=None):
    """Write (or add to) the word lexicon at `path` from `phrases` (as text_phrases gives them); `recording` is
    the media name the audio forms use (recording_name), unless a phrase has its own 'recording' (phrases from
    several texts). Returns {'path', 'added', 'existing' (entries already there), 'missing' (of those, guids no
    longer among the phrases' words), 'sets' (sets the new entries are in), 'untimed' (new entries with no
    times, so no audio)}."""
    audiolang = audiolang or analang + langtags.audio_code
    if os.path.exists(path):
        tree = ET.parse(path)
        root = tree.getroot()
    else:
        root = ET.Element('lift', {'version': LIFT_VERSION, 'producer': PRODUCER})
        tree = ET.ElementTree(root)
    entries = {e.get('guid'): e for e in root.findall('entry')}
    by_form = {}   # existing entries, by transcription
    for e in entries.values():
        by_form.setdefault(_key(e.findtext(f"citation/form[@lang='{analang}']/text")), []).append(e)
    text_guids = {w[0] for p in phrases for w in p['words']}
    new = [(p, w) for p in phrases for w in p['words'] if w[0] not in entries and w[1] and w[1].strip()]
    now = lift.getnow()

    # One set id per transcription with two or more occurrences, old and new together. An existing set is
    # joined (the biggest, if the user split identical forms into several); else an existing singleton gets
    # the new set's trait (the one change made to an existing entry).
    counts = {}
    for _p, w in new:
        counts[_key(w[1])] = counts.get(_key(w[1]), 0) + 1
    set_ids = {}
    for key, n in counts.items():
        old = by_form.get(key, [])
        if n + len(old) < 2:
            continue
        sets = [s for s in (_set_id(e) for e in old) if s]
        if sets:
            set_ids[key] = max(sorted(set(sets)), key=sets.count)
            continue
        set_ids[key] = str(uuid.uuid4())
        if old:
            single = old[0]
            sense = single.find('sense')
            if sense is None:
                sense = ET.SubElement(single, 'sense', {'id': str(uuid.uuid4())})
            ET.SubElement(sense, 'trait', {'name': lift.SAMESORT_TRAIT, 'value': set_ids[key]})
            single.set('dateModified', now)

    untimed = 0
    for phrase, (guid, form, begin_ms, end_ms) in new:
        recording = phrase.get('recording', recording)
        entry = ET.SubElement(root, 'entry', {'dateCreated': now, 'dateModified': now, 'guid': guid, 'id': guid})
        citation = ET.SubElement(entry, 'citation')
        _form(citation, analang, form)
        if begin_ms is not None and end_ms is not None:
            _form(citation, audiolang, _fragment(recording, begin_ms, end_ms))
        else:
            untimed += 1
        sense = ET.SubElement(entry, 'sense', {'id': str(uuid.uuid4())})
        ET.SubElement(sense, 'grammatical-info', {'value': PS})
        example = ET.SubElement(sense, 'example')
        _form(example, analang, phrase['text'])
        _form(example, audiolang, _fragment(recording, phrase['begin_ms'], phrase['end_ms']))
        ET.SubElement(example, 'trait', {'name': lift.PHRASE_TRAIT, 'value': phrase['guid']})
        set_id = set_ids.get(_key(form))
        if set_id:
            ET.SubElement(sense, 'trait', {'name': lift.SAMESORT_TRAIT, 'value': set_id})

    moved = _follow_moves(entries, phrases, recording, audiolang)
    missing = len(set(entries) - text_guids)
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    ET.indent(tree)
    tmp = path + '.tmp'
    tree.write(tmp, encoding='utf-8', xml_declaration=True)
    os.replace(tmp, path)
    result = {'path': path, 'added': len(new), 'existing': len(entries), 'missing': missing, 'moved': moved,
              'sets': len({set_ids[_key(w[1])] for _p, w in new if _key(w[1]) in set_ids}), 'untimed': untimed}
    log.info(f"word lexicon {path}: {result['added']} entries added ({untimed} without times), "
             f"{result['existing']} already there, {missing} of those no longer in the text (kept)")
    return result


def lexicon_path(db, liftbase):
    """<project>/texts/<liftbase>_text_words.lift: the one word lexicon of the project's texts."""
    return os.path.join(db.project_dir, texts.TEXTS_FOLDER, f"{liftbase}_text_words.lift")


def absorb(path, old_paths):
    """Start the shared lexicon at `path` (which doesn't exist yet) from the per-text ones written before
    2026-11-06: their entries, as they are (sorting included). Returns the number of entries taken in."""
    root = ET.Element('lift', {'version': LIFT_VERSION, 'producer': PRODUCER})
    seen = set()
    for old in old_paths:
        try:
            entries = ET.parse(old).getroot().findall('entry')
        except (OSError, ET.ParseError) as e:
            log.error(f"couldn't read the old word lexicon {old}: {e}")
            continue
        for entry in entries:
            if entry.get('guid') not in seen:
                seen.add(entry.get('guid'))
                root.append(entry)
    if seen:
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        tree = ET.ElementTree(root)
        ET.indent(tree)
        tmp = path + '.tmp'
        tree.write(tmp, encoding='utf-8', xml_declaration=True)
        os.replace(tmp, path)
        log.info(f"word lexicon {path}: started from {len(seen)} entries of {len(old_paths)} per-text lexicons")
    return len(seen)


def make_texts_lexicon(path, text_list, audiodir, analang, audiolang=None):
    """The word lexicon of these texts.Texts, at `path` (lexicon_path). Returns make_lexicon's result, or None
    if no text has words yet ("Find words" first)."""
    if not os.path.exists(path):
        old = [t.output_path('.lift') for t in text_list]
        absorb(path, [p for p in old if os.path.exists(p)])
    phrases = []
    for text in text_list:
        recording = recording_name(text, audiodir)
        phrases += [dict(p, recording=recording) for p in text_phrases(text)]
    if not word_count(phrases):
        return None
    return make_lexicon(path, phrases, None, analang, audiolang)
