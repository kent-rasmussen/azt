"""Text prep round trip (Kent, 2026-11-21/23):
  A. a clause with a careful take: its ASR and its words come only from the take, and the word lexicon plays
     them from it;
  B. sorting corrects the texts: what the word lexicon respelled goes back into the words and transcriptions
     (text_lexicon.texts_from_lexicon, run on "Back to the main lexicon" and before "Sort words from these
     texts").

A real texts file in tmp_path, words put in by hand as wordbreaks writes them: no audio, no models, no display.
"""
import xml.etree.ElementTree as ET

import numpy as np
import pytest

try:
    from backend.core import texts, text_lexicon
except ImportError as e:  # optional dep missing in this env
    pytest.skip(f"optional dependency not installed: {e.name}", allow_module_level=True)

ANALANG = 'xyy'
AUDIO = 'xyy-Zxxx-x-audio'


def _put_words(phrase, words):
    """[(guid, form, begin, end)] or [(guid, form, begin, end, {item type: value})]: the items are what
    Parse writes beside a bare form (punct-before, punct-after, case)."""
    holder = phrase.node.find('words')
    for w in list(holder):
        holder.remove(w)
    for guid, form, begin, end, *more in words:
        word = ET.SubElement(holder, 'word', {'guid': guid})
        ET.SubElement(word, 'item', {'type': 'txt', 'lang': ANALANG}).text = form
        if begin is not None:
            ET.SubElement(word, 'item', {'type': texts.WORD_BEGIN, 'lang': 'en'}).text = str(begin)
            ET.SubElement(word, 'item', {'type': texts.WORD_END, 'lang': 'en'}).text = str(end)
        for type_, value in (more[0] if more else {}).items():
            ET.SubElement(word, 'item', {'type': type_, 'lang': ANALANG}).text = value


@pytest.fixture
def project(tmp_path):
    """(project dir, db, text): clause 1 'kalo tama' (not transcribed); clause 2 transcribed 'Kalo sibe.'
    with its words as Parse writes them (bare forms; the capital and the period beside them); clause 3
    transcribed 'one two three' with two words found (edited since Parse)."""
    db = texts.TextsDB(tmp_path / 'proj.texts.flextext', tmp_path, ANALANG)
    text = db.add(str(tmp_path / 'texts' / 'story.ogg'), 'md5', [(0, 1000), (2000, 3000), (4000, 5000)],
                  'story')
    p1, p2, p3 = text.phrases()
    _put_words(p1, [('w1', 'kalo', 0, 400), ('w2', 'tama', 400, 1000)])
    p2.set_final('Kalo sibe.')
    _put_words(p2, [('w3', 'kalo', 2000, 2450, {texts.CASE: 'capital'}),
                    ('w4', 'sibe', 2450, 3000, {texts.PUNCT_AFTER: '.'})])
    p3.set_final('one two three')
    _put_words(p3, [('w5', 'one', 4000, 4500), ('w6', 'twothree', 4500, 5000)])
    return tmp_path, db, text


def _lexicon(prj, text):
    path = str(prj / 'texts' / 'proj_text_words.lift')
    text_lexicon.make_texts_lexicon(path, [text], prj / 'texts', ANALANG, AUDIO)
    return path


def _respell_in_lexicon(path, respellings):
    """Do what sorting does to a word's spelling: change its entry's citation form."""
    tree = ET.parse(path)
    for entry in tree.getroot().findall('entry'):
        if entry.get('guid') in respellings:
            entry.find(f"citation/form[@lang='{ANALANG}']/text").text = respellings[entry.get('guid')]
    tree.write(path, encoding='utf-8', xml_declaration=True)


def _words(phrase):
    return [form for _g, form, _b, _e in phrase.words()]


# ---- B: sorting corrects the texts ----------------------------------------------------------------------

def test_an_untranscribed_clause_gets_its_respelled_words_as_its_transcription(project):
    prj, db, text = project
    path = _lexicon(prj, text)
    _respell_in_lexicon(path, {'w2': 'tamá'})
    result = text_lexicon.texts_from_lexicon(path, db, ANALANG)
    p1 = text.phrases()[0]
    assert _words(p1) == ['kalo', 'tamá']
    assert p1.final() == 'kalo tamá'
    assert result['words'] == 1 and result['clauses'] == 1 and result['conflicts'] == []


def test_a_transcription_is_made_again_from_its_words_as_sorted(project):
    prj, db, text = project
    path = _lexicon(prj, text)
    _respell_in_lexicon(path, {'w3': 'kàlo', 'w4': 'sibé'})   # the lexicon: no capitals, no punctuation
    text_lexicon.texts_from_lexicon(path, db, ANALANG)
    p2 = text.phrases()[1]
    assert p2.final() == 'Kàlo sibé.'                         # put back with them
    assert _words(p2) == ['kàlo', 'sibé']


def test_a_transcription_that_doesnt_match_its_words_is_left_and_reported(project):
    prj, db, text = project
    path = _lexicon(prj, text)
    _respell_in_lexicon(path, {'w5': 'òne'})
    result = text_lexicon.texts_from_lexicon(path, db, ANALANG)
    p3 = text.phrases()[2]
    assert p3.final() == 'one two three' and _words(p3) == ['one', 'twothree']   # nothing changed there
    assert result['conflicts'] == [('story', '3')] and result['clauses'] == 0


def test_after_the_round_trip_the_lexicon_rebuild_keeps_the_sorting(project):
    """The entries already say what their words do: nothing respelled back, nothing to verify again."""
    prj, db, text = project
    path = _lexicon(prj, text)
    _respell_in_lexicon(path, {'w2': 'tamá', 'w4': 'sibé'})
    text_lexicon.texts_from_lexicon(path, db, ANALANG)
    again = text_lexicon.make_texts_lexicon(path, [text], prj / 'texts', ANALANG, AUDIO)
    assert again['unverified'] == 0 and again['removed'] == 0 and again['added'] == 0
    forms = {e.get('guid'): e.findtext(f"citation/form[@lang='{ANALANG}']/text")
             for e in ET.parse(path).getroot().findall('entry')}
    assert forms['w2'] == 'tamá' and forms['w4'] == 'sibé' and forms['w3'] == 'kalo'


def test_nothing_respelled_changes_nothing(project):
    prj, db, text = project
    path = _lexicon(prj, text)
    result = text_lexicon.texts_from_lexicon(path, db, ANALANG)
    assert result == {'words': 0, 'clauses': 0, 'conflicts': []}
    assert text.phrases()[0].final() == ''


# ---- before sorting: the words say what the transcriptions now do (Text.sync_words) -------------------

def test_a_spelling_edit_since_parse_respells_the_word_in_place(project):
    prj, db, text = project
    p2 = text.phrases()[1]
    p2.set_final('Kalo sibé!')                         # edited on the clause page after Parse
    respelled, again = text.sync_words()
    assert respelled == 1 and again == {text.phrases()[2].guid}   # clause 3's breaks changed
    assert p2.words() == [('w3', 'kalo', 2000, 2450), ('w4', 'sibé', 2450, 3000)]   # guid and times kept
    assert texts.word_token(p2.node.findall('words/word')[1]) == 'sibé!'


def test_words_from_before_bare_forms_are_brought_to_them(project):
    """Words Parse wrote before 2026-11-23 kept the whole token ('Kalo', 'sibe.') as their form."""
    prj, db, text = project
    p2 = text.phrases()[1]
    _put_words(p2, [('w3', 'Kalo', 2000, 2450), ('w4', 'sibe.', 2450, 3000)])
    path = _lexicon(prj, text)
    _respell_in_lexicon(path, {'w4': 'sibé.'})          # its old lexicon form had the period
    result = text_lexicon.texts_from_lexicon(path, db, ANALANG)
    assert result['conflicts'] == []                    # their tokens are still the transcription's
    assert p2.final() == 'Kalo sibé.'
    respelled, _again = text.sync_words()
    assert respelled == 2 and _words(p2) == ['kalo', 'sibé']
    assert [texts.word_token(w) for w in p2.node.findall('words/word')] == ['Kalo', 'sibé.']


# ---- tokens: bare forms, and what the transcription has around them -------------------------------------

def test_tokens_split_and_put_back():
    t = texts.tokens()
    words = t.words_of('«Kalo, — sibe» ABC dʼa.')
    assert [w['form'] for w in words] == ['kalo', 'sibe', 'abc', 'dʼa']   # ʼ is a letter, not punctuation
    assert words[0] == {'form': 'kalo', 'before': '«', 'after': ', —', 'case': 'capital'}
    assert words[2]['case'] == 'upper'
    assert t.text_of(words) == '«Kalo, — sibe» ABC dʼa.'
    respelled = dict(words[0], form='kàlo')
    assert t.surface(**respelled) == '«Kàlo, —'


def test_words_already_matching_are_left(project):
    prj, db, text = project
    text.phrases()[2].set_final('one twothree')
    assert text.sync_words() == (0, set())


# ---- join: the reverse of a split -----------------------------------------------------------------------

def test_join_makes_two_clauses_one(project):
    prj, db, text = project
    p1, p2, p3 = text.phrases()
    p1.add_candidates({'mms': 'kalo tama'})
    p2.set_breakpoints([(2600, 1.0, 2550, 2650, 12.0, 0.1)])
    guid = p1.guid
    joined = text.join_phrases(p1, p2)
    assert joined.guid == guid and (joined.begin_ms, joined.end_ms) == (0, 3000)
    assert [w[0] for w in joined.words()] == ['w1', 'w2', 'w3', 'w4']
    assert joined.final() == 'kalo tama Kalo sibe.'   # clause 1 untranscribed: its words stand for it
    assert joined.candidates() == {}
    assert [b[0] for b in joined.breakpoints()] == [2600]
    phrases = text.phrases()
    assert len(phrases) == 2 and [p.number for p in phrases] == ['1', '2'] and phrases[1].guid == p3.guid


def test_join_needs_the_clause_right_after(project):
    prj, db, text = project
    p1, _p2, p3 = text.phrases()
    assert text.join_phrases(p1, p3) is None and len(text.phrases()) == 3


def test_join_leaves_words_timed_in_a_take_untimed(project):
    prj, db, text = project
    p1, p2, _p3 = text.phrases()
    texts._set(p2.node, texts.WORDS_AUDIO, 'en', 'audio/story_x_careful.wav')
    joined = text.join_phrases(p1, p2)
    assert joined.words()[2:] == [('w3', 'kalo', None, None), ('w4', 'sibe', None, None)]
    assert joined.words_audio() is None


def test_join_then_split_gives_back_the_clauses(project):
    prj, db, text = project
    p1, p2, _p3 = text.phrases()
    joined = text.join_phrases(p1, p2)
    pieces = text.split_phrase(joined, [1500])
    assert [[w[0] for w in p.words()] for p in pieces] == [['w1', 'w2'], ['w3', 'w4']]


# ---- A: a careful take is what ASR and the words come from --------------------------------------------

def _take(prj, phrase, name='audio/story_ab_careful.wav'):
    path = prj / 'texts' / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b'RIFF')   # only its being there matters here
    phrase.take_recorded(name)
    return name


def test_recording_a_take_drops_the_candidates_that_heard_the_recording(project):
    prj, db, text = project
    p1 = text.phrases()[0]
    p1.add_candidates({'mms': 'kalo tama'})
    p1.set_asr_audio(p1.audio_source())
    assert not p1.stale_candidates()
    name = _take(prj, p1)
    assert p1.careful() == name and p1.candidates() == {} and p1.audio_source() == name
    assert _words(p1) == ['kalo', 'tama']   # the words stay until Parse makes them again


def test_candidates_from_before_a_take_was_linked_are_stale(project):
    prj, db, text = project
    p1 = text.phrases()[0]
    p1.add_candidates({'mms': 'kalo tama'})   # no asr-audio: they heard the recording
    name = 'audio/story_ab_careful.wav'
    (prj / 'texts' / 'audio').mkdir(parents=True)
    (prj / 'texts' / name).write_bytes(b'RIFF')
    p1.set_careful(name)                         # linked by code older than take_recorded
    assert p1.stale_candidates()


def test_a_take_whose_file_is_gone_leaves_the_clause_on_the_recording(project):
    prj, db, text = project
    p1 = text.phrases()[0]
    p1.set_careful('audio/missing_careful.wav')
    assert p1.careful_path() is None and p1.audio_source() == ''


def test_take_words_brings_the_take_the_words_are_timed_in(project):
    prj, db, text = project
    import copy
    snapshot = copy.deepcopy(text.node)
    first = next(snapshot.iter('phrase'))
    texts._set(first, texts.WORDS_AUDIO, 'en', 'audio/story_ab_careful.wav')
    text.take_words(snapshot)
    assert text.phrases()[0].words_audio() == 'audio/story_ab_careful.wav'
    assert text.phrases()[1].words_audio() is None


def test_words_timed_in_a_take_play_from_it_in_the_word_lexicon(project):
    prj, db, text = project
    p1 = text.phrases()[0]
    texts._set(p1.node, texts.WORDS_AUDIO, 'en', 'audio/story_ab_careful.wav')
    _put_words(p1, [('w1', 'kalo', 0, 300), ('w2', 'tama', 300, 800)])   # ms in the take
    path = _lexicon(prj, text)
    entries = {e.get('guid'): e for e in ET.parse(path).getroot().findall('entry')}
    assert entries['w1'].findtext(f"citation/form[@lang='{AUDIO}']/text").startswith('audio/story_ab_careful.wav#')
    assert entries['w1'].findtext(f"sense/example/form[@lang='{AUDIO}']/text") == 'audio/story_ab_careful.wav'
    assert entries['w3'].findtext(f"citation/form[@lang='{AUDIO}']/text").startswith('story.ogg#')


def test_a_split_keeps_words_timed_in_a_take_on_the_first_piece(project):
    prj, db, text = project
    p1 = text.phrases()[0]
    texts._set(p1.node, texts.WORDS_AUDIO, 'en', 'audio/story_ab_careful.wav')
    pieces = text.split_phrase(p1, [500])
    assert _words(pieces[0]) == ['kalo', 'tama'] and _words(pieces[1]) == []
    assert pieces[0].words_audio() == 'audio/story_ab_careful.wav' and pieces[1].words_audio() is None


def test_wordbreaks_cuts_a_clause_from_its_own_audio_timed_from_zero(project):
    try:
        wb = texts.wordbreaks()
    except ImportError as e:
        pytest.skip(f"azt_asr not importable: {e}")
    prj, db, text = project

    class Aligner:   # the forced aligner, faked: equal shares of whatever audio it is given
        letters = []

        def covers(self, _text):
            return True

        def word_spans(self, piece, words):
            share = len(piece) / 16000 / len(words)
            return [(k * share, (k + 1) * share) for k in range(len(words))], 0

    takes = {text.phrases()[1].guid: ('audio/story_ab_careful.wav', np.zeros(16000, dtype='float32'))}
    import copy
    snapshot = copy.deepcopy(text.node)
    wb.find_words(snapshot, audio=np.zeros(16000 * 6, dtype='float32'), aligner=Aligner(),
                  phrase_audio=lambda ph: takes.get(ph.get('guid'), (None, None))[1], log=lambda *_a: None)
    phrases = list(snapshot.iter('phrase'))
    times = [(int(w.findtext(f"item[@type='{texts.WORD_BEGIN}']")), int(w.findtext(f"item[@type='{texts.WORD_END}']")))
             for w in phrases[1].findall('words/word')]
    assert times == [(0, 500), (500, 1000)]                     # in the 1 s take, from 0
    found = phrases[1].findall('words/word')
    assert [w.findtext("item[@type='txt']") for w in found] == ['kalo', 'sibe']   # bare forms
    assert texts.word_token(found[0]) == 'Kalo' and texts.word_token(found[1]) == 'sibe.'
    first = [int(w.findtext(f"item[@type='{texts.WORD_BEGIN}']")) for w in phrases[2].findall('words/word')]
    assert first[0] == 4000                                     # the recording's clause: ms in the recording
