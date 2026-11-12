"""Word breaks by vote (azt_asr/wordbreaks.py consensus). 2026-11-07: breaks came out a letter early
("you hav elentus cars", "lik eroyalty") where some voters lacked a word-final letter the reference had."""
import pytest

pytest.importorskip('numpy')


def _wb():
    try:
        from backend.core import texts
        return texts.wordbreaks()
    except Exception as e:  # torch etc.; skip if the env can't load them
        pytest.skip(f"wordbreaks import failed: {e}")


def test_a_voter_missing_a_final_letter_doesnt_pull_the_break_early():
    wb = _wb()
    words, _info = wb.consensus({'a': 'you have lent us cars',
                                 'b': 'you have lent us cars',
                                 'c': 'you hav lent us cars',
                                 'd': 'you hav lent us cars'})
    assert words == ['you', 'have', 'lent', 'us', 'cars']


def _old_words(*pairs):
    import xml.etree.ElementTree as ET
    out = []
    for guid, form in pairs:
        w = ET.Element('word', {'guid': guid})
        ET.SubElement(w, 'item', {'type': 'txt'}).text = form
        out.append(w)
    return out


def test_words_keep_their_guids_when_breaks_move():
    """Kent, 2026-11-11: the word lexicon follows a word by its guid, so a reparse must keep them."""
    wb = _wb()
    old = _old_words(('a', 'you'), ('b', 'hav'), ('c', 'elentus'), ('d', 'cars'))
    assert wb.kept_guids(old, ['you', 'have', 'lent', 'us', 'cars']) == ['a', 'b', 'c', None, 'd']
    assert wb.kept_guids(old, ['you', 'hav', 'elentus', 'cars']) == ['a', 'b', 'c', 'd']
    assert wb.kept_guids(old, ['you', 'cars']) == ['a', 'd']


def test_agreeing_voters_keep_their_breaks():
    wb = _wb()
    words, _info = wb.consensus({'a': 'treated our kids like royalty',
                                 'b': 'treated our kids like royalty',
                                 'c': 'treated our kids lik royalty'})
    assert words == ['treated', 'our', 'kids', 'like', 'royalty']
