"""The word lexicon of the texts (backend/core/text_lexicon.py): one LIFT entry per word occurrence found by
"Find words", all texts in one <project>/texts/<liftbase>_text_words.lift.

Built from a real texts file (backend/core/texts.TextsDB) in tmp_path, with the words "Find words" would
store put into its phrases by hand: no audio, no models, no display.
"""
import xml.etree.ElementTree as ET

import pytest

try:
    from backend.core import texts, text_lexicon
    from io_put import lift
except ImportError as e:  # optional dep missing in this env
    pytest.skip(f"optional dependency not installed: {e.name}", allow_module_level=True)

ANALANG = 'xyy'
AUDIO = 'xyy-Zxxx-x-audio'


def _put_words(phrase, words):
    """Give a texts.Phrase these words, as wordbreaks writes them: [(guid, form, begin_ms, end_ms)]."""
    holder = phrase.node.find('words')
    for w in list(holder):
        holder.remove(w)
    for guid, form, begin, end in words:
        word = ET.SubElement(holder, 'word', {'guid': guid})
        ET.SubElement(word, 'item', {'type': 'txt', 'lang': ANALANG}).text = form
        if begin is not None:
            ET.SubElement(word, 'item', {'type': texts.WORD_BEGIN, 'lang': 'en'}).text = str(begin)
            ET.SubElement(word, 'item', {'type': texts.WORD_END, 'lang': 'en'}).text = str(end)
        ET.SubElement(word, 'item', {'type': 'word-source', 'lang': 'en'}).text = 'consensus'


@pytest.fixture
def project(tmp_path):
    """(project dir, audio dir, text): a text of three clauses from audio/story.ogg (the file need not exist).
    Clause 1: kalo tama; clause 2 (final transcription 'Kalo sibe.'): kalo sibe; clause 3: no words yet."""
    audiodir = tmp_path / 'audio'
    db = texts.TextsDB(tmp_path / 'proj.texts.flextext', tmp_path, ANALANG)
    text = db.add(str(audiodir / 'story.ogg'), 'md5-of-story', [(0, 1000), (2000, 3000), (4000, 5000)], 'story')
    p1, p2, _p3 = text.phrases()
    _put_words(p1, [('w1', 'kalo', 0, 400), ('w2', 'tama', 400, 1000)])
    p2.set_final('Kalo sibe.')
    _put_words(p2, [('w3', 'kalo', 2000, 2450), ('w4', 'sibe', 2450, 3000)])
    return tmp_path, audiodir, text


def _path(prj):
    return str(prj / 'texts' / 'proj_text_words.lift')


def _make(project, more=()):
    prj, audiodir, text = project
    return text_lexicon.make_texts_lexicon(_path(prj), [text, *more], audiodir, ANALANG, AUDIO)


def _entries(result):
    root = ET.parse(result['path']).getroot()
    assert root.tag == 'lift' and root.get('version') == '0.13'
    return {e.get('guid'): e for e in root.findall('entry')}


def _set(entry):
    trait = entry.find(f"sense/trait[@name='{lift.SAMESORT_TRAIT}']")
    return trait.get('value') if trait is not None else None


def test_written_to_texts_folder(project):
    prj, _audiodir, text = project
    assert text_lexicon.lexicon_path(text.db, 'proj') == _path(prj)
    result = _make(project)
    assert result['path'] == _path(prj)
    assert (prj / 'texts' / 'proj_text_words.lift').exists()
    assert result['added'] == 4 and result['existing'] == 0 and result['missing'] == 0


def test_one_lexicon_for_several_texts(project):
    """Kent, 2026-11-06: the words of several texts are sorted together; each keeps its own recording."""
    prj, audiodir, text = project
    other = text.db.add(str(audiodir / 'song.ogg'), 'md5-of-song', [(0, 1000)], 'song')
    _put_words(other.phrases()[0], [('s1', 'kalo', 100, 500)])
    entries = _entries(_make(project, [other]))
    assert set(entries) == {'w1', 'w2', 'w3', 'w4', 's1'}
    assert entries['s1'].findtext(f"citation/form[@lang='{AUDIO}']/text") == 'song.ogg#t=0.100,0.500'
    assert entries['w2'].findtext(f"citation/form[@lang='{AUDIO}']/text") == 'story.ogg#t=0.400,1.000'
    assert _set(entries['s1']) and _set(entries['s1']) == _set(entries['w1'])   # kalo across texts


def test_the_old_per_text_lexicon_is_taken_in(project):
    """Before 2026-11-06 each text had <stem>.lift; its entries (sorting and all) start the shared one."""
    prj, _audiodir, text = project
    old = text_lexicon.make_lexicon(text.output_path('.lift'), text_lexicon.text_phrases(text), 'story.ogg',
                                    ANALANG, AUDIO)
    tree = ET.parse(old['path'])
    ET.SubElement(tree.getroot().find("entry[@guid='w2']").find('sense'), 'field', {'type': 'sorted-here'})
    tree.write(old['path'], encoding='utf-8', xml_declaration=True)
    result = _make(project)
    assert result['existing'] == 4 and result['added'] == 0
    assert _entries(result)['w2'].find("sense/field[@type='sorted-here']") is not None


def test_a_moved_recording_moves_the_spans_not_the_times(project):
    """Texts' audio went from audio/ to <project>/texts/, and the lexicon there names spans from its own folder
    (Kent, 2026-11-06): spans written relative to audio/ become plain names, times kept."""
    prj, audiodir, text = project
    text.node.find('media-files/media').set('location', 'texts/story.ogg')
    first = _make(project)                                     # relative to audio/: '../texts/story.ogg'
    assert _entries(first)['w2'].findtext(f"citation/form[@lang='{AUDIO}']/text").startswith('../texts/')
    second = text_lexicon.make_texts_lexicon(_path(prj), [text], prj / 'texts', ANALANG, AUDIO)
    assert second['moved'] == 4 and second['added'] == 0
    e = _entries(second)['w2']
    assert e.findtext(f"citation/form[@lang='{AUDIO}']/text") == 'story.ogg#t=0.400,1.000'
    assert e.findtext(f"sense/example/form[@lang='{AUDIO}']/text") == 'story.ogg#t=0.000,1.000'


def test_a_moved_recording_is_still_on_its_row(project):
    prj, audiodir, text = project
    assert text.db.at(str(prj / 'texts' / 'story.ogg')).node is text.node   # audio/story.ogg is gone


def test_board_counts_and_lookup_by_file(project):
    prj, audiodir, text = project
    text.phrases()[0].add_candidates({'m': 'kalo tama'})
    assert text.counts() == {'clauses': 3, 'asr': 1, 'worded': 2, 'words': 4, 'final': 1}
    assert text.db.at(str(audiodir / 'story.ogg')).node is text.node
    assert text.db.at(str(audiodir / 'other.ogg')) is None


def test_entry_per_occurrence(project):
    entries = _entries(_make(project))
    assert set(entries) == {'w1', 'w2', 'w3', 'w4'}
    for guid, e in entries.items():
        assert e.get('id') == guid
        assert e.get('dateCreated') and e.get('dateModified')
        assert e.find('lexical-unit') is None
        sense = e.find('sense')
        assert sense.get('id')
        assert sense.find('grammatical-info').get('value') == 'Word'
        assert sense.find('gloss') is None and sense.find('definition') is None


def test_citation_word_and_audio_span(project):
    e = _entries(_make(project))['w2']
    assert e.findtext(f"citation/form[@lang='{ANALANG}']/text") == 'tama'
    assert e.findtext(f"citation/form[@lang='{AUDIO}']/text") == 'story.ogg#t=0.400,1.000'
    assert lift.split_media_fragment('story.ogg#t=0.400,1.000') == ('story.ogg', (0.4, 1.0))


def test_same_sort_only_for_identical_words(project):
    entries = _entries(_make(project))
    assert _set(entries['w1']) and _set(entries['w1']) == _set(entries['w3'])   # kalo, kalo
    assert _set(entries['w2']) is None   # tama: once
    assert _set(entries['w4']) is None   # sibe: once


def test_phrase_example(project):
    _prj, _audiodir, text = project
    p1, p2, _p3 = text.phrases()
    entries = _entries(_make(project))
    ex = entries['w1'].find('sense/example')
    assert ex.findtext(f"form[@lang='{ANALANG}']/text") == 'kalo tama'   # no final: the words
    assert ex.findtext(f"form[@lang='{AUDIO}']/text") == 'story.ogg#t=0.000,1.000'
    assert ex.find(f"trait[@name='{lift.PHRASE_TRAIT}']").get('value') == p1.guid
    assert ex.find("trait[@name='location']") is None   # not a tone frame
    assert ex.find("field[@type='location']") is None
    ex2 = entries['w4'].find('sense/example')
    assert ex2.findtext(f"form[@lang='{ANALANG}']/text") == 'Kalo sibe.'   # the final transcription
    assert ex2.find(f"trait[@name='{lift.PHRASE_TRAIT}']").get('value') == p2.guid


def test_rerun_adds_only_new_and_joins_sets(project):
    _prj, _audiodir, text = project
    first = _make(project)
    before = _entries(first)
    kalo_set = _set(before['w1'])
    # Sorting data on an existing entry, which a rerun must leave alone.
    tree = ET.parse(first['path'])
    tama = tree.getroot().find("entry[@guid='w2']")
    ET.SubElement(tama.find('sense'), 'field', {'type': 'sorted-here'})
    tree.write(first['path'], encoding='utf-8', xml_declaration=True)
    w1_before = ET.tostring(tree.getroot().find("entry[@guid='w1']"))

    p1, p2, p3 = text.phrases()
    _put_words(p2, [('w3', 'kalo', 2000, 2450)])                       # sibe (w4) gone from the text
    _put_words(p3, [('w5', 'tama', 4000, 4500), ('w6', 'kalo', 4500, 4800), ('w7', 'nu', 4800, 5000)])
    second = _make(project)
    assert second['added'] == 3
    assert second['existing'] == 4
    assert second['missing'] == 1                                      # w4: counted, not deleted
    after = _entries(second)
    assert set(after) == {'w1', 'w2', 'w3', 'w4', 'w5', 'w6', 'w7'}
    assert _set(after['w6']) == kalo_set                               # joins the existing set
    assert _set(after['w5']) and _set(after['w5']) == _set(after['w2'])   # joins the singleton: a new set
    assert after['w2'].find("sense/field[@type='sorted-here']") is not None
    assert _set(after['w7']) is None
    root = ET.parse(second['path']).getroot()
    assert ET.tostring(root.find("entry[@guid='w1']")).split() == w1_before.split()


def test_identical_means_nfc_equal(tmp_path):
    phrases = [{'guid': 'p1', 'text': 'x', 'begin_ms': 0, 'end_ms': 1000,
                'words': [('a', 'kàlo', 0, 500), ('b', 'kàlo', 500, 1000), ('c', 'kalo', 500, 1000)]}]
    path = str(tmp_path / 'texts' / 'x.lift')
    entries = _entries(text_lexicon.make_lexicon(path, phrases, 'x.wav', ANALANG))
    assert _set(entries['a']) and _set(entries['a']) == _set(entries['b'])
    assert _set(entries['c']) is None   # no tone mark: a different transcription


def test_untimed_word_has_no_audio(tmp_path):
    phrases = [{'guid': 'p1', 'text': 'x', 'begin_ms': 0, 'end_ms': 1000, 'words': [('a', 'kalo', None, None)]}]
    path = str(tmp_path / 'x.lift')
    result = text_lexicon.make_lexicon(path, phrases, 'x.wav', ANALANG)
    e = _entries(result)['a']
    assert result['untimed'] == 1
    assert e.find(f"citation/form[@lang='{AUDIO}']") is None
    assert e.findtext(f"sense/example/form[@lang='{AUDIO}']/text") == 'x.wav#t=0.000,1.000'


def test_no_words_means_find_words_first(tmp_path):
    db = texts.TextsDB(tmp_path / 'p.texts.flextext', tmp_path, ANALANG)
    text = db.add(str(tmp_path / 'audio' / 's.ogg'), 'md5', [(0, 1000)], 's')
    path = str(tmp_path / 'texts' / 'p_text_words.lift')
    assert text_lexicon.make_texts_lexicon(path, [text], tmp_path / 'audio', ANALANG) is None
    assert not (tmp_path / 'texts' / 'p_text_words.lift').exists()
