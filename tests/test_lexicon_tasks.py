"""Which tasks the chooser offers for the main lexicon and for the texts' word
lexicon, and the title marker for the latter (Kent, 2026-11-20)."""
import types

import pytest

base = pytest.importorskip('tasks.base')


def test_the_open_lexicon_is_told_by_lexicon_filename():
    assert base.lexicon_kind(types.SimpleNamespace()) == 'main'
    assert base.lexicon_kind(types.SimpleNamespace(lexicon_filename=None)) == 'main'
    assert base.lexicon_kind(types.SimpleNamespace(lexicon_filename='/p/texts/p_text_words.lift')) == 'texts'


def test_a_title_is_marked_only_on_the_text_lexicon():
    main = types.SimpleNamespace(lexicon_filename=None)
    texts = types.SimpleNamespace(lexicon_filename='/p/texts/p_text_words.lift')
    assert base.title_for_lexicon('Sort Vowels', main) == 'Sort Vowels'
    marked = base.title_for_lexicon('Sort Vowels', texts)
    assert marked != 'Sort Vowels' and 'Sort Vowels' in marked


def test_adding_words_and_transcribing_texts_are_main_lexicon_only():
    tasks = pytest.importorskip('tasks.tasks')
    texts = pytest.importorskip('tasks.texts')
    for cls in (tasks.WordCollectionCitationwRecordings, tasks.WordCollectnParse,
                tasks.WordCollectnParsewRecordings, texts.TranscribeTexts):
        assert cls.lexicons == ('main',), cls.__name__
    for cls in (tasks.SortV, tasks.SortC, tasks.SortT, tasks.WordsParse):
        assert 'texts' in cls.lexicons and 'main' in cls.lexicons, cls.__name__


def test_back_to_the_main_lexicon_is_a_text_lexicon_button():
    texts = pytest.importorskip('tasks.texts')
    assert texts.BackToMainLexicon.lexicons == ('texts',)
    assert texts.BackToMainLexicon.mark_texts is False
    asked = []
    program = types.SimpleNamespace(use_lexicon=asked.append)
    texts.BackToMainLexicon(program=program)
    assert asked == [None]
