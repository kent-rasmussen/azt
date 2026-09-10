# coding=UTF-8
"""The sound-settings window's handlers, called without a display.

WHY. Two bugs on 2026-09-10 were the SAME SHAPE: a derived value updated in
one place while several handlers change its inputs.

  * the test filename encodes fs, sample_format and the input card, and
    `_refresh_test_filename()` was called only from the full
    `soundcheckrefresh()`. The per-setting choosers do not run that, so a
    192000 Hz take was written to `test_44100_int32_6.wav` — the name lied,
    and every combination overwrote the last;
  * then my fix put the refresh in `relabel_settings()`, which runs AFTER a
    take — renaming the file that had just been recorded.

So the contract worth pinning is not "the label says the right thing" (that
needs Tk and a human) but "every handler that changes an input to the
filename re-derives it, and nothing re-derives it after the fact".

HOW, WITHOUT TK. These are plain methods; calling them unbound on a stand-in
`self` exercises the real code with no widgets. What the stand-in must offer
is exactly what the handler touches, which is itself the useful discipline:
if a handler starts reaching for something new, these fail loudly rather than
silently drifting.
"""
import sys
import types
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

sound_ui = pytest.importorskip('frontend.sound_ui',
                               reason='needs the frontend importable')


class Recorder:
    """Records which no-argument methods a handler called."""

    def __init__(self):
        self.called = []

    def __getattr__(self, name):
        def note(*a, **k):
            self.called.append(name)
        return note


def window_stand_in(**attrs):
    """Enough of a SoundSettingsWindow for one handler call."""
    stand_in = Recorder()
    stand_in.soundsettings = types.SimpleNamespace(
        fs=48000, sample_format='int32', audio_card_in=5,
        cards={'dict': {5: 'pipewire', 8: 'default'}},
        choose_card=lambda direction, index: stand_in.called.append(
                                    'choose_card:{}:{}'.format(direction,
                                                               index)),
    )
    for k, v in attrs.items():
        setattr(stand_in, k, v)
    return stand_in


HANDLERS = [
    ('setsoundhz', (44100,)),
    ('setsoundformat', ('int16',)),
    ('setsoundcardindex', (8,)),
]


@pytest.mark.parametrize('name,args', HANDLERS)
def test_every_setter_re_derives_the_test_filename(name, args):
    """The filename carries fs, sample_format AND the input card, so all
    three setters must re-derive it. Missing one is how a take ends up in a
    file named for different settings."""
    stand_in = window_stand_in()
    getattr(sound_ui.SoundSettingsWindow, name)(stand_in, *args,
                                                Recorder())
    assert '_refresh_test_filename' in stand_in.called, (
        "{} changed a setting the test filename is built from and did not "
        "re-derive it".format(name))


@pytest.mark.parametrize('name,args', HANDLERS)
def test_every_setter_closes_its_chooser_window(name, args):
    """Each of these opens a window to pick a value; leaving it up would
    strand the user behind a dialog that has already done its job."""
    stand_in = window_stand_in()
    chooser = Recorder()
    getattr(sound_ui.SoundSettingsWindow, name)(stand_in, *args, chooser)
    assert 'destroy' in chooser.called


def test_choosing_a_card_goes_through_choose_card():
    """NOT a direct assignment to `audio_card_in`. That is what let the
    stored device NAME go stale, so `resolve_cards()` followed the old name
    and the user's pick did not stick."""
    stand_in = window_stand_in()
    sound_ui.SoundSettingsWindow.setsoundcardindex(stand_in, 8, Recorder())
    assert any(c.startswith('choose_card:in:8') for c in stand_in.called), \
        "the card must be set through choose_card, which also records the name"


def test_choosing_an_output_card_goes_through_choose_card():
    stand_in = window_stand_in()
    sound_ui.SoundSettingsWindow.setsoundcardoutindex(stand_in, 8, Recorder())
    assert any(c.startswith('choose_card:out:8') for c in stand_in.called)


def test_relabel_settings_does_NOT_touch_the_filename():
    """The opposite direction, and the bug my own fix introduced: this runs
    after a take, so re-deriving the name here renames the file that was just
    recorded. Labels only."""
    stand_in = window_stand_in()
    sound_ui.SoundSettingsWindow.relabel_settings(stand_in)
    assert '_refresh_test_filename' not in stand_in.called, (
        "relabel_settings runs after a recording; re-deriving the filename "
        "there mislabels the take that just happened")


def test_relabel_settings_refreshes_all_four_labels():
    """It exists because a take can change the settings behind the window —
    `note_fake_rate` records a finding — and the window went on showing the
    old values, so the only evidence was the log."""
    stand_in = window_stand_in()
    sound_ui.SoundSettingsWindow.relabel_settings(stand_in)
    for label in ('updatesoundcard', 'updatesoundhz', 'updatesoundformat',
                  'updatesoundcardoutindex'):
        assert label in stand_in.called, '{} was not refreshed'.format(label)
