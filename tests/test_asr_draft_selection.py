"""Selector-side tests for ASR draft display: the 'top models only' filter
must never collapse the selector to a single form when widening the top-N
window would surface a disagreement (2026-07-07 bulk-ASR UI follow-up).

`WordCollectionwRecordings._filter_top_asr` is a staticmethod and
`SoundSettings.top_asr_keys` only reads `asr_kwargs`/`asr_repos`, so both run
headless with a fake-`self` SoundSettings (no Tk, no models, no audio card).
"""
from types import SimpleNamespace

import pytest

try:
    from tasks.tasks import WordCollectionwRecordings
    from backend.core import sound
except ImportError as e:  # optional dep missing in this env
    pytest.skip(f"optional dependency not installed: {e.name}",
                allow_module_level=True)

_REPO_MAP = {
    'mms_all': 'facebook/mms-1b-all',
    'allosaurus': 'allosaurus',
    'whisper-large': 'whisper-large',
    'whisper-large-v3': 'whisper-large-v3',
    # output-lane flags alias model repos in the real map:
    'neurlang': 'neurlang/ipa-whisper-base',
    'return_ipa': 'neurlang/ipa-whisper-base',
    'katyayego': 'katyayego/Wav2Vec2Phoneme-CSfinetune',
    'show_tone': 'katyayego/Wav2Vec2Phoneme-CSfinetune',
}


def _ss(top_models_only=True, tally=None, models=None, sister=None):
    """Fake-self SoundSettings; `models` (kwarg->bool) also fakes the loaded
    ASR object whose repo_modelnames/_sister_members/_mms_lang the
    kwarg-selection display filter reads. Without `models` there is no .asr
    at all — the filter must fail open."""
    ss = object.__new__(sound.SoundSettings)
    ss.asr_kwargs = {'top_models_only': top_models_only, **(models or {})}
    if sister is not None:
        ss.asr_kwargs['sister_languages'] = tuple(sister)
    ss.asr_repos = dict(tally or {})
    if models is not None:
        ss.asr = SimpleNamespace(
            repo_modelnames=dict(_REPO_MAP),
            _sister_members=lambda code: {'swa': ['swh', 'swc']}.get(code, []),
            _mms_lang=lambda code: {'en': 'eng'}.get(code, code),
        )
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


def test_disabled_models_hidden_from_display():
    # 'just these models' governs display too: stored drafts from switched-off
    # models are hidden (language-decorated keys match by repo-name prefix).
    tx = {'facebook/mms-1b-all (swh!)': 'mbumi', 'allosaurus': 'bumi'}
    ss = _ss(top_models_only=False,
             models={'mms_all': True, 'allosaurus': False})
    assert _filter(tx, ss) == {'facebook/mms-1b-all (swh!)': 'mbumi'}


def test_enabled_prefix_never_matches_sibling_repo():
    # whisper-large enabled must not leak whisper-large-v3's drafts in.
    tx = {'whisper-large-v3 (eng!)': 'aaa', 'whisper-large': 'bbb'}
    ss = _ss(top_models_only=False,
             models={'whisper-large': True, 'whisper-large-v3': False})
    assert _filter(tx, ss) == {'whisper-large': 'bbb'}


def test_none_enabled_fails_open():
    # A kwarg set with no model enabled (pathological — nothing could have
    # produced drafts) must not blank the selector: show the stored drafts.
    tx = {'allosaurus': 'x', 'whisper-large': 'y'}
    assert _filter(tx, _ss(top_models_only=False)) == tx  # no model kwargs
    ss = _ss(top_models_only=False, models={'mms_all': False})
    assert _filter(tx, ss) == tx


def test_deselected_sister_language_hidden():
    # sister_languages down to ('bem',): the swh-directed draft hides, the
    # bem-directed one stays — top-five (or widening) must not reach past
    # the user's selection to bring swh back.
    tx = {'facebook/mms-1b-all (swh!)': 'mbumi',
          'facebook/mms-1b-all (bem!)': 'bumi'}
    ss = _ss(top_models_only=False, models={'mms_all': True}, sister=('bem',))
    assert _filter(tx, ss) == {'facebook/mms-1b-all (bem!)': 'bumi'}


def test_macrolanguage_selection_admits_member_drafts():
    # 'swa' selected: member-language runs (swh) are part of the selection.
    tx = {'facebook/mms-1b-all (swh!)': 'mbumi'}
    ss = _ss(top_models_only=False, models={'mms_all': True}, sister=('swa',))
    assert _filter(tx, ss) == tx


def test_alpha2_selection_matches_alpha3_decoration():
    tx = {'facebook/mms-1b-all (eng!)': 'mbumi'}
    ss = _ss(top_models_only=False, models={'mms_all': True}, sister=('en',))
    assert _filter(tx, ss) == tx


def test_detected_language_and_mismatch_decorations():
    # '(en?)' is a detection, not a user direction: passes on the model.
    # '(bem!=swh!)' names the requested/actual pair: selected on either side.
    tx = {'whisper-large (en?)': 'aaa',
          'facebook/mms-1b-all (bem!=swh!)': 'bbb'}
    ss = _ss(top_models_only=False,
             models={'mms_all': True, 'whisper-large': True}, sister=('bem',))
    assert _filter(tx, ss) == tx


def test_sister_filter_works_before_asr_loads():
    # Stored drafts display without ASR ever running (stage-3 contract), so
    # the selection filter must too: no .asr object here — the module-level
    # REPO_MODELNAMES/sister_members/mms_lang carry it (live 2026-07-07:
    # flr/kam/lam/myx drafts showed with only bem selected, because the
    # filter failed open before the first load_ASR).
    tx = {'facebook/mms-1b-all (bem!)': 'bumi',
          'facebook/mms-1b-all (flr!)': 'mbumi'}
    ss = _ss(top_models_only=False, sister=('bem',))
    assert _filter(tx, ss) == {'facebook/mms-1b-all (bem!)': 'bumi'}


def test_output_lane_flags_do_not_enable_their_model():
    # return_ipa is forced True (no checkbox) and aliases the neurlang repo;
    # show_tone likewise aliases katyayego. Neither may resurrect a
    # deselected model's transcription drafts (seen live 2026-07-07: a
    # neurlang button with only mms/bem selected).
    tx = {'neurlang/ipa-whisper-base': 'ipaish',
          'katyayego/Wav2Vec2Phoneme-CSfinetune': 'toneish',
          'facebook/mms-1b-all (bem!)': 'bumi'}
    ss = _ss(top_models_only=False,
             models={'mms_all': True, 'neurlang': False, 'return_ipa': True,
                     'katyayego': False, 'show_tone': True},
             sister=('bem',))
    assert _filter(tx, ss) == {'facebook/mms-1b-all (bem!)': 'bumi'}


def test_enabled_unanimous_gives_single_form_despite_disabled_dissent():
    # The single-button test case Kent needs: one model enabled, its drafts
    # unanimous — a disabled model's dissent must not widen back in.
    tx = {'facebook/mms-1b-all (swh!)': 'mbumi',
          'facebook/mms-1b-all (bem!)': 'mbumi',
          'allosaurus': 'bumi'}
    ss = _ss(tally={'allosaurus': 9, 'facebook/mms-1b-all (swh!)': 5},
             models={'mms_all': True, 'allosaurus': False})
    kept = _filter(tx, ss)
    assert set(kept.values()) == {'mbumi'}
    assert 'allosaurus' not in kept


def test_top_only_caps_buttons_at_twenty():
    # 2026-07-23: 'top only' also promises a page that fits. Top-5
    # unanimous + 30 untallied dissenting repos exhausts widening and
    # returns the full selection — which must arrive capped at 20
    # distinct forms, with the top-tallied form guaranteed a slot.
    tx = {f'top{i}': 'agreed' for i in range(5)}
    tx.update({f'r{i}': f'form{i}' for i in range(30)})
    ss = _ss(top_models_only=True, tally={f'top{i}': 9 for i in range(5)})
    forms = {v for v in _filter(tx, ss).values() if v}
    assert len(forms) == 20
    assert 'agreed' in forms  # top-tallied forms are kept first


def test_top_only_caps_even_before_any_tally():
    # Toggle on, nothing tallied yet: the model window is unlimited
    # (run everything), but the page cap still applies.
    tx = {f'r{i}': f'form{i}' for i in range(25)}
    forms = {v for v in _filter(tx, _ss(top_models_only=True)).values() if v}
    assert len(forms) == 20


def test_all_models_shows_everything_uncapped():
    # Explicitly selecting all models means all buttons, page be damned.
    tx = {f'r{i}': f'form{i}' for i in range(30)}
    assert _filter(tx, _ss(top_models_only=False, tally={'r0': 9})) == tx
