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

RERUN: an entry follows its word (by guid; wordbreaks keeps a word's guid when its breaks move, write_words).
Kent, 2026-11-11:
  - a word whose spelling or times changed has its entry UPDATED, and its verification removed: the sorting
    stays, to be verified again (_update). Its 'Same word' set goes too, if its spelling changed: it is put in a
    set with its new spelling's occurrences, as a new word would be;
  - a word no longer in the texts is REMOVED: not in the text, not in the lexicon of text words.
Otherwise an entry isn't changed (it may carry sorting), except that a new occurrence identical to an existing
singleton puts both in a new set, which adds the trait to the old one, and that a recording that moved has its
new name put in the spans (times kept).
The recording's name is relative to the lexicon's own folder, <project>/texts/, which is its audio folder when
it is open (backend/core/file_parser.py): 'story.ogg'. Takes recorded in it go in texts/audio/ ('audio/…').
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


def _put(parent, lang, value):
    """Make parent's form in `lang` say `value` (None: no such form). Returns the old value."""
    form = parent.find(f"form[@lang='{lang}']")
    old = form.findtext('text') if form is not None else None
    if old == value:
        return old
    if value is None:
        parent.remove(form)
    elif form is None:
        _form(parent, lang, value)
    else:
        text = form.find('text')
        if text is None:
            text = ET.SubElement(form, 'text')
        text.text = value
    return old


def _times(fragment):
    """A media fragment without its file name: what says when, wherever the recording now is."""
    if not fragment:
        return None
    name, _span = lift.split_media_fragment(fragment)
    return fragment[len(name):]


def _unverify(entry):
    """Remove the entry's verification (sense fields '<profile> <ftype> verification', lift.addverificationnode);
    its sorting stays."""
    for sense in entry.findall('sense'):
        for field in sense.findall('field'):
            if (field.get('type') or '').endswith(' verification'):
                sense.remove(field)


def _drop_set(entry):
    for sense in entry.findall('sense'):
        for trait in sense.findall(f"trait[@name='{lift.SAMESORT_TRAIT}']"):
            sense.remove(trait)


def _update(entry, phrase, word, recording, analang, audiolang, now):
    """Make an existing entry say what its word now does. Returns the set of what changed, of 'spelling',
    'times' (both remove the verification), 'recording' (it moved: new name, same times) and 'phrase'."""
    _guid, form, begin_ms, end_ms = word
    changed = set()
    citation = entry.find('citation')
    if citation is None:
        citation = ET.Element('citation')
        entry.insert(0, citation)
    if _key(_put(citation, analang, form)) != _key(form):
        changed.add('spelling')
    audio = _fragment(recording, begin_ms, end_ms) if begin_ms is not None and end_ms is not None else None
    old = _put(citation, audiolang, audio)
    if _times(old) != _times(audio):
        changed.add('times')
    elif old != audio:
        changed.add('recording')
    for ex in entry.findall('sense/example'):
        trait = ex.find(f"trait[@name='{lift.PHRASE_TRAIT}']")
        if trait is None:
            continue
        if _put(ex, analang, phrase['text']) != phrase['text'] or trait.get('value') != phrase['guid']:
            changed.add('phrase')
        trait.set('value', phrase['guid'])
        span = _fragment(recording, phrase['begin_ms'], phrase['end_ms'])
        old = _put(ex, audiolang, span)
        if _times(old) != _times(span):
            changed.add('phrase')
        elif old != span:
            changed.add('recording')
    if changed & {'spelling', 'times'}:
        _unverify(entry)
    if 'spelling' in changed:
        _drop_set(entry)
    if changed:
        entry.set('dateModified', now)
    return changed


def make_lexicon(path, phrases, recording, analang, audiolang=None, known=None):
    """Write (or update) the word lexicon at `path` from `phrases` (as text_phrases gives them); `recording` is
    the media name the audio forms use (recording_name), unless a phrase has its own 'recording' (phrases from
    several texts). known: the guids of every word in the texts, when `phrases` aren't all of them (a text whose
    recording is missing); an entry whose word is neither there nor in `phrases` is removed.
    Returns {'path', 'added', 'existing' (entries already there, removed ones included), 'updated' (of those,
    changed), 'unverified' (of those, their spelling or times changed), 'removed', 'moved' (entries whose
    recording's name changed), 'sets' (sets the new and respelled entries are in), 'untimed' (new entries with
    no times, so no audio)}."""
    audiolang = audiolang or analang + langtags.audio_code
    if os.path.exists(path):
        tree = ET.parse(path)
        root = tree.getroot()
    else:
        root = ET.Element('lift', {'version': LIFT_VERSION, 'producer': PRODUCER})
        tree = ET.ElementTree(root)
    entries = {e.get('guid'): e for e in root.findall('entry')}
    existing = len(entries)
    current = {w[0]: (p, w) for p in phrases for w in p['words'] if w[1] and w[1].strip()}
    keep = set(current) | set(known or ())
    removed = [g for g in entries if g not in keep]
    for guid in removed:
        root.remove(entries.pop(guid))
    now = lift.getnow()
    updated = unverified = moved = 0
    respelled = []   # entries to set again, as new ones are
    for guid, entry in entries.items():
        if guid not in current:
            continue
        phrase, word = current[guid]
        changed = _update(entry, phrase, word, phrase.get('recording', recording), analang, audiolang, now)
        updated += bool(changed)
        unverified += bool(changed & {'spelling', 'times'})
        moved += 'recording' in changed
        if 'spelling' in changed:
            respelled.append(entry)
    by_form = {}   # existing entries, by transcription (respelled ones are set below, as new)
    for e in entries.values():
        if e not in respelled:
            by_form.setdefault(_key(e.findtext(f"citation/form[@lang='{analang}']/text")), []).append(e)
    new = [(p, w) for guid, (p, w) in current.items() if guid not in entries]
    joining = [w[1] for _p, w in new] + [e.findtext(f"citation/form[@lang='{analang}']/text") for e in respelled]

    # One set id per transcription with two or more occurrences, old and new together. An existing set is
    # joined (the biggest, if the user split identical forms into several); else an existing singleton gets
    # the new set's trait (the one change made to an existing entry).
    counts = {}
    for form in joining:
        counts[_key(form)] = counts.get(_key(form), 0) + 1
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
    for entry in respelled:
        set_id = set_ids.get(_key(entry.findtext(f"citation/form[@lang='{analang}']/text")))
        sense = entry.find('sense')
        if set_id and sense is not None:
            ET.SubElement(sense, 'trait', {'name': lift.SAMESORT_TRAIT, 'value': set_id})

    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    ET.indent(tree)
    tmp = path + '.tmp'
    tree.write(tmp, encoding='utf-8', xml_declaration=True)
    os.replace(tmp, path)
    result = {'path': path, 'added': len(new), 'existing': existing, 'updated': updated,
              'unverified': unverified, 'removed': len(removed), 'moved': moved,
              'sets': len({set_ids[_key(f)] for f in joining if _key(f) in set_ids}), 'untimed': untimed}
    log.info(f"word lexicon {path}: {result['added']} entries added ({untimed} without times); of {existing} "
             f"already there, {updated} updated ({unverified} to verify again), {len(removed)} removed "
             f"(no longer in the texts)")
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


def make_texts_lexicon(path, text_list, audiodir, analang, audiolang=None, all_texts=None):
    """The word lexicon of these texts.Texts, at `path` (lexicon_path). all_texts: every text, when text_list
    leaves some out (no recording): their words' entries are kept, not removed. Returns make_lexicon's result,
    or None if no text has words yet ("Find words" first)."""
    if not os.path.exists(path):
        old = [t.output_path('.lift') for t in text_list]
        absorb(path, [p for p in old if os.path.exists(p)])
    phrases = []
    for text in text_list:
        recording = recording_name(text, audiodir)
        phrases += [dict(p, recording=recording) for p in text_phrases(text)]
    if not word_count(phrases):
        return None
    known = {w[0] for text in (all_texts or ()) for p in text.phrases() for w in p.words()}
    return make_lexicon(path, phrases, None, analang, audiolang, known)
