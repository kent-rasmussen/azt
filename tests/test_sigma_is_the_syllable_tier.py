"""σ is the syllable tier's code; S alone is the sonorant class.

The S-codes decision (Kent, 2026-10-02): "syllable --> :sigma: everywhere a
code is used. S alone is **always** sonorant. segmental --> 'CV' everywhere a
code is used." Until then the syllable sort's cvt was `'S'`, which collided
with the sonorant class `S` in the profile machinery and with `SortS`, the
segmental base class (see test_task_for_tier).

Two stored places carried the old code and must keep working: the status key
in the project's data.json, and a saved cvt setting. The LIFT file never
carried a tier code, so nothing there moves.
"""
import pytest

from sourcescan import code as _code

from backend.core import analysis_inputs


def test_sigma_is_a_tier_and_S_is_not():
    """The `_cvts` table is built in __init__, which needs a live program;
    read the literal instead, comments stripped."""
    src = _code(analysis_inputs.CheckParameters.__init__)
    assert "'σ':{'sg':'Syllable Profile'" in src
    assert "'S':{'sg'" not in src
    assert analysis_inputs.CheckParameters.SYLLABLE_CVT == 'σ'
    assert analysis_inputs.CheckParameters.LEGACY_SYLLABLE_CVT == 'S'


def test_a_saved_S_is_read_as_sigma():
    """A settings file written before the change says cvt 'S'; the setter
    is the one door it comes through."""
    # An instance without __init__ (which needs a live program): the class
    # attributes the setter reads are still there.
    p = analysis_inputs.CheckParameters.__new__(analysis_inputs.CheckParameters)
    assert p.cvt('S') == 'σ'
    assert p._cvt == 'σ'
    assert p.cvt('V') == 'V'
    assert p.cvt() == 'V'


def test_the_status_key_migrates_once():
    settings = pytest.importorskip('settings')
    st = {'S': {'*': {'whole-word': {'#C': {'done': ['C']}}}}, 'V': {}}
    assert settings.migrate_syllable_tier_code(st) is True
    assert 'S' not in st
    assert st['σ']['*']['whole-word']['#C']['done'] == ['C']
    assert st['V'] == {}
    assert settings.migrate_syllable_tier_code(st) is False, "idempotent"


def test_when_both_keys_exist_sigma_wins():
    """A file touched by both old and new code: the σ branch was written by
    code that knew, so it is kept and S fills only what σ lacks."""
    settings = pytest.importorskip('settings')
    both = {'S': {'*': {'a': 1}, 'Noun': {'b': 2}}, 'σ': {'*': {'a': 9}}}
    assert settings.migrate_syllable_tier_code(both) is True
    assert both['σ']['*'] == {'a': 9}
    assert both['σ']['Noun'] == {'b': 2}
    assert 'S' not in both


def test_nothing_to_migrate_is_not_a_change():
    settings = pytest.importorskip('settings')
    assert settings.migrate_syllable_tier_code(None) is False
    assert settings.migrate_syllable_tier_code({}) is False
    assert settings.migrate_syllable_tier_code({'V': {}}) is False


def test_the_syllable_task_and_its_photo_say_sigma():
    tasks = pytest.importorskip('tasks.tasks')
    assert tasks.SortSyllables.cvt == 'σ'
    from frontend import theme_data
    pairs = [t for v in vars(theme_data).values() if isinstance(v, (list, tuple))
             for t in v if isinstance(t, tuple) and len(t) == 2]
    assert ('σ', 'ZA alone clear6.png') in pairs
    assert not [t for t in pairs if t[0] == 'S'], "no theme photo keyed by S"
