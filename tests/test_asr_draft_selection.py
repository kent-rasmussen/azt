"""Selector-side tests for ASR draft display: the 'top models only' filter
must never collapse the selector to a single form when widening the top-N
window would surface a disagreement (2026-07-07 bulk-ASR UI follow-up).

`WordCollectionwRecordings._filter_top_asr` is a staticmethod and
`SoundSettings.top_asr_keys` only reads `asr_kwargs`/`asr_repos`, so both run
headless with a fake-`self` SoundSettings (no Tk, no models, no audio card).
"""
import pytest

try:
    from tasks.tasks import WordCollectionwRecordings
    from backend.core import sound
except ImportError as e:  # optional dep missing in this env
    pytest.skip(f"optional dependency not installed: {e.name}",
                allow_module_level=True)


def _ss(top_models_only=True, tally=None):
    ss = object.__new__(sound.SoundSettings)
    ss.asr_kwargs = {'top_models_only': top_models_only}
    ss.asr_repos = dict(tally or {})
    return ss


def _filter(tx, ss):
    return WordCollectionwRecordings._filter_top_asr(tx, ss)


def test_no_settings_or_toggle_off_passes_through():
    tx = {'a': 'x', 'b': 'y'}
    assert _filter(tx, None) == tx
    assert _filter(tx, _ss(top_models_only=False, tally={'a': 9})) == tx


def test_top5_agreement_kept_when_second_form_exists_in_window():
    # Two distinct forms already inside the top-5 window: plain filter applies.
    tally = {'a': 9, 'b': 8, 'c': 7, 'd': 6, 'e': 5, 'f': 1}
    tx = {'a': 'mbumi', 'b': 'mbumi', 'c': 'bumi', 'f': 'other'}
    kept = _filter(tx, _ss(tally=tally))
    assert kept == {'a': 'mbumi', 'b': 'mbumi', 'c': 'bumi'}  # 'f' outside top-5


def test_unanimous_top5_widens_until_two_forms():
    # Top-5 all say 'mbumi'; the dissent is ranked 6th. Widening to top-10
    # must surface it instead of collapsing the selector to one form.
    tally = {'a': 10, 'b': 9, 'c': 8, 'd': 7, 'e': 6, 'f': 5, 'g': 1}
    tx = {'a': 'mbumi', 'b': 'mbumi', 'c': 'mbumi', 'd': 'mbumi', 'e': 'mbumi',
          'f': 'bumi'}
    kept = _filter(tx, _ss(tally=tally))
    assert set(kept.values()) == {'mbumi', 'bumi'}
    assert 'f' in kept


def test_unanimous_everywhere_returns_all_drafts():
    # Every draft is the same form: widening can't help; show what we have
    # (the one-button case) rather than an empty selector.
    tally = {'a': 9, 'b': 8, 'c': 7, 'd': 6, 'e': 5, 'f': 4}
    tx = {r: 'mbumi' for r in tally}
    assert _filter(tx, _ss(tally=tally)) == tx


def test_tally_exhausted_falls_back_to_all_drafts():
    # The only disagreeing repo was never tallied, so no amount of widening
    # ranks it; once widening stops adding repos, return everything.
    tally = {'a': 9, 'b': 8, 'c': 7}
    tx = {'a': 'mbumi', 'b': 'mbumi', 'c': 'mbumi', 'untallied': 'bumi'}
    kept = _filter(tx, _ss(tally=tally))
    assert kept == tx
