# coding=UTF-8
"""Contracts between the sound settings UI and the settings object.

WHY THESE EXIST. Every bug on 2026-09-10 that reached Kent was in this seam,
not in the measuring code — and each one was invisible to the existing tests
because it lived in the gap between a UI handler and the state it changes:

  * the settings window assigned `audio_card_in` directly, so the stored NAME
    still held the old device and `resolve_cards()` followed it back. Picking
    a microphone did not stick, and REDRAWING THE LABEL was what reverted it;
  * `_refresh_test_filename()` was called only from the full
    `soundcheckrefresh()`, so changing the rate left the previous rate's name:
    a 192000 Hz take written to `test_44100_int32_6.wav`;
  * then the opposite, from my fix: refreshing the filename AFTER a take
    renamed the file that had just been recorded;
  * `note_fake_rate` switched the rate on its own, which was never agreed.

None of that needs a display to test. The methods are real methods; they are
called here on an instance built with `__new__` so no `__init__` and no audio
device is involved. That is the project's stated preference (azt/CLAUDE.md:
"prefer testing real methods with a fake `self` over a live Tk root") and it
is what makes these runnable on a machine with no sound at all.

WHAT THEY DELIBERATELY DO NOT TEST: rendering, geometry, or anything needing
Tk. The question here is "does changing a setting leave the object
consistent", which is where the damage was.
"""
import sys
import types
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.core import sound


CARDS = {
    'in': {5: {192000: ['int32'], 48000: ['int32', 'int16'],
               44100: ['int32']},
           8: {48000: ['int32']}},
    'out': {6: {48000: ['int32']}, 8: {48000: ['int32']}},
    'dict': {5: 'pipewire', 6: 'hdmi', 8: 'default'},
}


def settings(**attrs):
    """A SoundSettings with real methods and no __init__, audio or files.

    `_verified_fs` and `_fake_rates` are CLASS attributes, so they are shared
    by every instance and would leak between tests — cleared here. (Worth
    noting as a latent fragility in its own right: with one settings object
    per app it is harmless, but nothing enforces that.)
    """
    ss = sound.SoundSettings.__new__(sound.SoundSettings)
    ss._verified_fs.clear()
    ss._fake_rates.clear()
    ss.cards = {k: (v.copy() if hasattr(v, 'copy') else v)
                for k, v in CARDS.items()}
    ss.audio_card_in = 5
    ss.audio_card_out = 6
    ss.fs = 48000
    ss.sample_format = 'int32'
    # Device names come from the probed table in these tests, never from
    # PortAudio: the point is the bookkeeping, not the hardware.
    ss._device_name = lambda index: ss.cards['dict'].get(index)
    for k, v in attrs.items():
        setattr(ss, k, v)
    return ss


# ─── Choosing a card must move the INDEX and the NAME together ──────────────

def test_choose_card_records_which_device_it_is():
    """The regression that stopped a chosen microphone from sticking.

    An index alone is not identity, so `resolve_cards()` follows the stored
    name — and if a setter changes only the index, the name it left behind
    wins. Kent: "Couldn't get it to stick at pipewire mic."
    """
    ss = settings()
    ss.choose_card('in', 8)
    assert ss.audio_card_in == 8
    assert ss.audio_card_in_name == 'default', "the name must move too"


def test_choosing_a_card_survives_resolve_cards():
    """The full round trip, because the revert happened via `resolve_cards`
    being called from `check()` from `soundcardlabel()` — that is, by drawing
    the label that was supposed to show the new value."""
    ss = settings()
    ss.choose_card('in', 8)
    ss.resolve_cards()
    assert ss.audio_card_in == 8, "resolve_cards must not undo a fresh choice"
    assert ss.audio_card_in_name == 'default'


def test_choose_card_forgets_cached_rate_checks():
    """A rate verdict describes the path it was measured on. Changing the
    card is exactly when it stops applying (Kent: an 'on boot' test is not an
    'on run' test)."""
    ss = settings()
    ss._verified_fs['pipewire'] = 192000
    ss._fake_rates['pipewire'] = {192000}
    ss.choose_card('in', 8)
    assert not ss._verified_fs
    assert not ss._fake_rates


def test_choose_card_handles_the_output_side_too():
    ss = settings()
    ss.choose_card('out', 8)
    assert ss.audio_card_out == 8
    assert ss.audio_card_out_name == 'default'


# ─── resolve_cards: three outcomes, all normal ──────────────────────────────

def test_resolve_cards_follows_a_renumbered_device():
    """PortAudio renumbers devices between runs; the name is what persists."""
    ss = settings(audio_card_in=99, audio_card_in_name='pipewire')
    ss.resolve_cards()
    assert ss.audio_card_in == 5, "should follow 'pipewire' to its index now"


def test_resolve_cards_drops_a_device_that_is_gone():
    """A stored name that no longer resolves must DROP the setting, so the
    defaults are re-derived — not fall back to the stale index, which today
    may mean a different microphone entirely."""
    ss = settings(audio_card_in=5, audio_card_in_name='a mic long unplugged')
    ss.resolve_cards()
    assert not hasattr(ss, 'audio_card_in')
    assert not hasattr(ss, 'audio_card_in_name')


def test_resolve_cards_does_not_adopt_an_index_it_cannot_vouch_for():
    """MIGRATION. Settings written before names were stored have an index and
    no name. Adopting whatever that index means today canonicalises a
    possibly-stale value into a name that is then followed faithfully — which
    is how Kent's output ended up pinned to 'hdmi', a device he never chose.
    An index we cannot vouch for is not evidence of a choice."""
    ss = settings(audio_card_out=6)
    assert not hasattr(ss, 'audio_card_out_name')
    ss.resolve_cards()
    assert not hasattr(ss, 'audio_card_out'), \
        "an unvouched index must be dropped, not turned into a name"


# ─── Rate findings: recorded, never acted on ────────────────────────────────

def test_note_fake_rate_does_not_change_the_rate():
    """DECIDED 2026-09-10, Kent: "I thought we weren't dropping the rate for
    upsampling, just notifying the user?" Detection may inform; it must not
    reach in and change a setting in use."""
    ss = settings(fs=192000)
    result = ss.note_fake_rate(192000)
    assert result is None, "no switch, so nothing to announce"
    assert ss.fs == 192000, "the rate in use must be left alone"


def test_note_fake_rate_records_the_finding():
    ss = settings(fs=192000)
    ss.note_fake_rate(192000)
    assert 192000 in ss.fake_rates_here()


def test_note_real_rate_withdraws_an_earlier_mark():
    """Latest evidence wins, because the graph rate changes underneath: a
    rate that was upsampled at one moment can be genuine at the next, and a
    permanent mark would lock the user out of it."""
    ss = settings(fs=192000)
    ss.note_fake_rate(192000)
    assert 192000 in ss.fake_rates_here()
    ss.note_real_rate(192000)
    assert 192000 not in ss.fake_rates_here()


def test_a_disproved_rate_is_not_chosen_as_a_default():
    """The record still shapes what gets OFFERED when a default is
    re-derived — the line between informing a choice and overriding one."""
    ss = settings()
    ss.note_fake_rate(192000)
    ss.default_fs()
    assert ss.fs != 192000
    assert ss.fs == 48000, "the highest offered that was not disproved"


def test_default_fs_takes_the_highest_offered_when_nothing_is_disproved():
    """No guessed fallback. Kent rejected one: "'I'm not sure, so we're using
    48khz' is bad, lazy policy." """
    ss = settings()
    ss.default_fs()
    assert ss.fs == 192000


def test_forget_rate_checks_is_safe_when_there_is_nothing_to_forget():
    settings().forget_rate_checks(' for no reason')
