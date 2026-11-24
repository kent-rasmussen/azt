"""Splitting a clause into several (the split screen; Kent, 2026-11-20):
what each piece keeps of the clause it came from."""
import xml.etree.ElementTree as ET

import pytest

texts = pytest.importorskip('backend.core.texts')


def _text(tmp_path, chunks=((0, 10000), (10000, 12000))):
    db = texts.TextsDB(tmp_path / 'p.texts.flextext', tmp_path, 'xx')
    return db, db.add(str(tmp_path / 'texts' / 'story.ogg'), 'md5', list(chunks), 'story')


def _word(phrase, guid, form, begin, end):
    w = ET.SubElement(phrase.node.find('words'), 'word', {'guid': guid})
    for type_, value in (('txt', form), (texts.WORD_BEGIN, begin), (texts.WORD_END, end)):
        if value is not None:
            ET.SubElement(w, 'item', {'type': type_, 'lang': 'xx'}).text = str(value)


def test_a_clause_split_in_three_shares_out_its_words_and_transcription(tmp_path):
    db, text = _text(tmp_path)
    first = text.phrases()[0]
    for guid, form, b, e in (('w1', 'one', 500, 1500), ('w2', 'two', 4000, 5000), ('w3', 'three', 7000, 8000)):
        _word(first, guid, form, b, e)
    first.set_final('one two three')
    first.add_candidates({'mms': 'won too tree'})
    first.set_careful('audio/story_x_careful.wav')
    first.set_breakpoints([(3000, 2.0, 2900, 3100, 15.0, 0.1), (6000, 1.5, 5900, 6100, 12.0, 0.2)])
    guid = first.guid
    pieces = text.split_phrase(first, [3000, 6000])
    assert [(p.begin_ms, p.end_ms) for p in pieces] == [(0, 3000), (3000, 6000), (6000, 10000)]
    assert pieces[0].guid == guid and len({p.guid for p in pieces}) == 3
    assert [[w[0] for w in p.words()] for p in pieces] == [['w1'], ['w2'], ['w3']]
    assert [p.final() for p in pieces] == ['one', 'two', 'three']
    assert all(not p.candidates() and p.careful() is None for p in pieces)
    assert [len(p.breakpoints()) for p in pieces] == [1, 2, 1]        # the cut places are at the edges
    phrases = text.phrases()
    assert len(phrases) == 4 and [p.number for p in phrases] == ['1', '2', '3', '4']
    assert phrases[3].begin_ms == 10000                              # the next clause, after the pieces


def test_a_transcription_that_doesnt_match_the_words_stays_on_the_first_piece(tmp_path):
    db, text = _text(tmp_path)
    first = text.phrases()[0]
    _word(first, 'w1', 'one', 500, 1500)
    first.set_final('one two')                                       # two tokens, one word found
    pieces = text.split_phrase(first, [5000])
    assert [p.final() for p in pieces] == ['one two', '']


def test_a_cut_outside_the_clause_changes_nothing(tmp_path):
    db, text = _text(tmp_path)
    first = text.phrases()[0]
    assert text.split_phrase(first, [0, 10000, 15000]) == [first]
    assert len(text.phrases()) == 2


def test_a_careful_take_is_linked_on_a_clause(tmp_path):
    db, text = _text(tmp_path)
    first = text.phrases()[0]
    assert first.careful() is None
    first.set_careful('audio/story_ab12_careful.wav')
    assert first.careful() == 'audio/story_ab12_careful.wav'
