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


class Waiting:
    """A stand-in for `task.waiting(...)`: callable, and a context manager."""

    def __init__(self, called, label='waiting'):
        self.called = called
        self.label = label

    def __call__(self, text=None, **kwargs):
        self.called.append(self.label)
        return self

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


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
    # THE REAL METHOD, not Recorder's catch-all no-op. `setsoundcardindex`
    # delegates the whole after-a-card-change sequence to `_new_input_card`,
    # so letting the stand-in absorb that call would make the filename and
    # measurement tests below pass while testing nothing.
    stand_in._new_input_card = types.MethodType(
        sound_ui.SoundSettingsWindow._new_input_card, stand_in)
    # `waiting` ON THE WINDOW, because that is where the handler takes it —
    # `wait()` withdraws and `waitdone()` reveals the window it was called
    # on, so taking it on the task returned the user to the task page.
    stand_in.waiting = Waiting(stand_in.called)
    # The task's is present too, recording under a DIFFERENT name, so a
    # regression to `self.task.waiting(...)` is visible rather than silent.
    stand_in.task = types.SimpleNamespace(
        waiting=Waiting(stand_in.called, label='task.waiting'))
    for k, v in attrs.items():
        setattr(stand_in, k, v)
    return stand_in


def measuring_stand_in(verdict=(48000, 'recording at 48000 Hz'), **attrs):
    """A stand-in whose SoundSettings can re-derive and measure."""
    stand_in = window_stand_in(**attrs)
    ss = stand_in.soundsettings
    ss.default_fs = lambda: stand_in.called.append('default_fs')
    ss.default_sf = lambda: stand_in.called.append('default_sf')
    ss.verify_fs = lambda: (stand_in.called.append('verify_fs') or verdict)
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


# ─── Switching the input card measures it (Kent's call, 2026-09-11) ─────────
# "any card switch legitimately implies other settings change; let's offer the
# best the newly selected card has" + "running that on switching input cards
# would be preferable to another button users have to hit".

def test_switching_the_input_card_re_derives_and_measures():
    """The sequence, in order: take the new card's best, then measure it.

    `choose_card` already forgets the old card's rate checks, so without a
    re-measure here a card switch could only LOSE information — the rate list
    went back to unannotated until the user happened to record something."""
    stand_in = measuring_stand_in()
    sound_ui.SoundSettingsWindow.setsoundcardindex(stand_in, 8, Recorder())
    assert 'default_fs' in stand_in.called, \
        "the new card's own best rate must be taken before measuring"
    assert 'verify_fs' in stand_in.called, \
        "switching the input card must measure what it really delivers"
    assert stand_in.called.index('default_fs') \
            < stand_in.called.index('verify_fs')


@pytest.mark.skip(reason="wait dialog commented out at Kent's request "
                         "2026-09-11 ('I want to see it without'); "
                         "un-skip with the `with self.waiting(...)` in "
                         "_new_input_card")
def test_switching_the_input_card_shows_the_wait_dialog():
    """It RECORDS, on this thread, inside the click handler. Without the
    dialog the settings window just freezes for the capture — now for ~2s,
    since the settle pause and confirm-on-repeat were added."""
    stand_in = measuring_stand_in()
    sound_ui.SoundSettingsWindow.setsoundcardindex(stand_in, 8, Recorder())
    assert 'waiting' in stand_in.called


def test_the_wait_is_NEVER_taken_on_the_task():
    """Stands whether or not the dialog is enabled. `wait()` withdraws the
    window it is called on and `waitdone()` reveals that same window, so
    waiting on the TASK left the user back at the task page with Sound
    Settings buried behind it (Kent, 2026-09-11). If the dialog is restored,
    it must be restored on the settings window."""
    stand_in = measuring_stand_in()
    sound_ui.SoundSettingsWindow.setsoundcardindex(stand_in, 8, Recorder())
    assert 'task.waiting' not in stand_in.called, \
        "the wait must be taken on the settings window, not on the task"


def test_switching_the_OUTPUT_card_does_not_measure():
    """Nothing about the speakers affects what gets recorded, and a capture
    per output click would be a second of freeze for no information."""
    stand_in = measuring_stand_in()
    sound_ui.SoundSettingsWindow.setsoundcardoutindex(stand_in, 8, Recorder())
    assert 'verify_fs' not in stand_in.called


def test_a_quiet_room_is_logged_not_announced(monkeypatch):
    """QUIETER THAN A BUTTON. `verify_fs` returns (None, reason) when it could
    not judge; on a button that answers a question the user asked, but on every
    card switch it is a nag about something they did not ask and cannot act
    on."""
    said = []
    monkeypatch.setattr(sound_ui, 'notify_user',
                        lambda text, **k: said.append(text))
    stand_in = measuring_stand_in(verdict=(None, 'the room was too quiet'))
    sound_ui.SoundSettingsWindow.setsoundcardindex(stand_in, 8, Recorder())
    assert 'verify_fs' in stand_in.called, 'it should still have tried'
    assert not said, "a can't-tell result must not interrupt the user"


def test_a_real_result_IS_announced(monkeypatch):
    said = []
    monkeypatch.setattr(sound_ui, 'notify_user',
                        lambda text, **k: said.append(text))
    stand_in = measuring_stand_in(verdict=(48000, 'recording at 48000 Hz'))
    sound_ui.SoundSettingsWindow.setsoundcardindex(stand_in, 8, Recorder())
    assert said == ['recording at 48000 Hz']


def test_switching_the_input_card_relabels_everything():
    """fs and sample_format moved, not just the card, so the card label alone
    would leave two stale numbers on screen — the invisible-switch bug of
    2026-09-10 in a new place."""
    stand_in = measuring_stand_in()
    sound_ui.SoundSettingsWindow.setsoundcardindex(stand_in, 8, Recorder())
    assert 'relabel_settings' in stand_in.called


def test_card_switch_survives_a_settings_object_that_cannot_measure():
    """An older/partial SoundSettings must not turn a card click into a
    traceback: every measurement step is best-effort."""
    stand_in = window_stand_in()      # no default_fs/verify_fs at all
    chooser = Recorder()
    sound_ui.SoundSettingsWindow.setsoundcardindex(stand_in, 8, chooser)
    assert 'destroy' in chooser.called, \
        "the chooser must close even when nothing could be measured"
    assert '_refresh_test_filename' in stand_in.called


# ─── The rate list ANNOTATES, never withholds ───────────────────────────────
# Kent, 2026-09-11: "Can we show users what we believe is true without
# actually limiting options?" Every rate the card opens stays selectable; the
# notes say what was measured.

def rate_stand_in(disproved=(), verified=None, confirmed=None):
    stand_in = window_stand_in()
    # THE REAL `_describe`, not Recorder's catch-all. The label names the
    # original rate through it, and a no-op stand-in returns None — which is
    # what "192khz — upsampled from None" was.
    stand_in._describe = types.MethodType(
        sound_ui.SoundSettingsWindow._describe, stand_in)
    ss = stand_in.soundsettings
    ss.hypothetical = {'fss': {48000: '48khz', 96000: '96khz',
                               192000: '192khz'}}
    ss.fake_rates_here = lambda: set(disproved)
    # `confirmed` defaults to `verified` so the older cases below still read
    # naturally; the point of the split is that evidence is now PER RATE.
    ss.real_rates_here = lambda: set(confirmed if confirmed is not None
                                     else ([verified] if verified else []))
    ss.measured_fs = lambda: verified
    return stand_in


def test_evidence_about_one_rate_does_not_erase_evidence_about_another():
    """Kent, 2026-09-11: "I thought I recalled a comment on 44.1, which wasn't
    there after 192 got one."

    It had been there. `verify_fs` cached 44100 in `_verified_fs`, the label
    read that, then a 192000 take was marked fake — and `note_fake_rate` pops
    `_verified_fs`, because it holds ONE derived value per device ("the
    highest not provably fake"). So news about 192 kHz deleted the finding
    about 44.1 kHz, which is not news about 44.1 kHz at all. Evidence is now
    kept per rate."""
    stand_in = rate_stand_in(disproved=[192000], confirmed=[48000])
    assert 'not upsampled' in \
        sound_ui.SoundSettingsWindow._rate_option_label(stand_in, 48000)
    assert 'upsampled from' in \
        sound_ui.SoundSettingsWindow._rate_option_label(stand_in, 192000)


def test_a_confirmed_rate_is_not_called_real():
    """`rate_is_fake` never returns False, so no take can certify a rate. The
    label must claim only what was established."""
    stand_in = rate_stand_in(confirmed=[48000])
    label = sound_ui.SoundSettingsWindow._rate_option_label(stand_in, 48000)
    assert 'not upsampled' in label
    for overclaim in ('real', 'genuine', 'cleanly', 'verified'):
        assert overclaim not in label.lower(), \
            "label overclaims with {!r}: {}".format(overclaim, label)


def test_no_note_says_checked():
    """"checked:" prefixed all three notes, so it distinguished none of them —
    the presence of any note already says the rate was checked (Kent,
    2026-09-11: "agreed on checked; that was my first thought")."""
    for kwargs in ({'confirmed': [48000]},
                   {'disproved': [48000]},
                   {'disproved': [192000], 'confirmed': [48000]}):
        stand_in = rate_stand_in(**kwargs)
        for fs in (48000, 192000):
            label = sound_ui.SoundSettingsWindow._rate_option_label(stand_in,
                                                                    fs)
            assert 'checked' not in label, label


def test_the_original_rate_is_named_in_THE_SAME_UNITS():
    """"192khz — upsampled from 44100 Hz" mixed two units in one line, because
    the measurement works in Hz and the name does not. The label the user
    already reads for that rate is the one to reuse."""
    stand_in = rate_stand_in(disproved=[192000], confirmed=[48000])
    label = sound_ui.SoundSettingsWindow._rate_option_label(stand_in, 192000)
    assert '48khz' in label, label
    assert 'Hz' not in label.replace('khz', ''), \
        "no raw-Hz figure beside a khz name: {}".format(label)


def test_an_unchecked_rate_gets_no_note():
    """The common case, and the reason there is no legend above the list
    (Kent: "leave this off"): nothing measured, nothing said."""
    stand_in = rate_stand_in()
    label = sound_ui.SoundSettingsWindow._rate_option_label(stand_in, 192000)
    assert label == '192khz'


def test_a_disproved_rate_says_what_was_measured():
    stand_in = rate_stand_in(disproved=[192000], verified=48000)
    label = sound_ui.SoundSettingsWindow._rate_option_label(stand_in, 192000)
    assert '192khz' in label
    assert 'upsampled from' in label and '48khz' in label


def test_a_disproved_rate_with_no_known_original_just_says_upsampled():
    """Honest about what is not known — the record says THAT a rate was
    band-limited, not what it was band-limited to — and no "from a lower rate"
    tail, which adds nothing the word does not carry (Kent, 2026-09-11)."""
    stand_in = rate_stand_in(disproved=[192000])
    label = sound_ui.SoundSettingsWindow._rate_option_label(stand_in, 192000)
    assert label.endswith('upsampled'), label


def test_a_checked_rate_says_so():
    stand_in = rate_stand_in(verified=48000)
    label = sound_ui.SoundSettingsWindow._rate_option_label(stand_in, 48000)
    assert 'not upsampled' in label


def test_a_rate_that_is_neither_is_left_alone():
    """Only the ONE rate that was measured clean is marked clean. The others
    are unknown, not endorsed."""
    stand_in = rate_stand_in(verified=48000)
    assert sound_ui.SoundSettingsWindow._rate_option_label(stand_in,
                                                           96000) == '96khz'


def test_the_label_survives_settings_without_the_check_accessors():
    stand_in = window_stand_in()
    stand_in.soundsettings.hypothetical = {'fss': {48000: '48khz'}}
    label = sound_ui.SoundSettingsWindow._rate_option_label(stand_in, 48000)
    assert label == '48khz'


# ─── A BAD SETTING MUST NOT STOP THE SETTINGS WINDOW OPENING ────────────────
# Kent, 2026-09-11: "sound settings window didn't show." The log stopped
# between "Done setting up labels" and the labels being filled, i.e. inside
# `soundcheckrefresh`'s four `update*` calls — three of which indexed their
# lookup tables directly, so one unrecognised value raised and the window was
# built, left withdrawn and never shown. This is the screen you open IN ORDER
# TO fix a bad sound setting, so a bad setting is the one thing that must not
# keep it shut.

def label_stand_in(fs=48000, sample_format='int32', card_in=5, card_out=7,
                   fss=None, formats=None, cards=None):
    stand_in = window_stand_in()
    stand_in._describe = types.MethodType(
        sound_ui.SoundSettingsWindow._describe, stand_in)
    stand_in.soundsettings = types.SimpleNamespace(
        fs=fs, sample_format=sample_format,
        audio_card_in=card_in, audio_card_out=card_out,
        check=lambda: None,
        hypothetical={'fss': fss if fss is not None else {48000: '48khz'},
                      'sample_formats': (formats if formats is not None
                                         else {'int32': '32 bit integer'})},
        cards={'dict': cards if cards is not None else {5: 'pipewire',
                                                        7: 'hdmi'}},
    )
    return stand_in


LABELS = ['soundhzlabel', 'soundformatlabel', 'soundcardlabel',
          'soundcardoutindexlabel']


@pytest.mark.parametrize('name', LABELS)
def test_every_label_survives_an_unknown_value(name):
    """All four, not just the three that were unguarded — the contract is the
    method never raises, whatever is stored."""
    stand_in = label_stand_in(fs=192000, sample_format='paInt24',
                              card_in=99, card_out=99)
    getattr(sound_ui.SoundSettingsWindow, name)(stand_in)   # must not raise


def test_an_unknown_rate_is_shown_as_itself():
    """Not `None`, and not a blank: the odd value is the thing the user needs
    to see, and it names what to fix."""
    stand_in = label_stand_in(fs=192000)          # not in fss
    assert '192000' in sound_ui.SoundSettingsWindow.soundhzlabel(stand_in)


def test_an_unknown_output_card_is_shown_as_itself():
    stand_in = label_stand_in(card_out=99)
    assert '99' in \
        sound_ui.SoundSettingsWindow.soundcardoutindexlabel(stand_in)


def test_a_known_value_still_gets_its_friendly_name():
    """The guard must not cost the normal case."""
    stand_in = label_stand_in()
    assert '48khz' in sound_ui.SoundSettingsWindow.soundhzlabel(stand_in)
    assert '32 bit integer' in \
        sound_ui.SoundSettingsWindow.soundformatlabel(stand_in)
    assert 'pipewire' in sound_ui.SoundSettingsWindow.soundcardlabel(stand_in)
    assert 'hdmi' in \
        sound_ui.SoundSettingsWindow.soundcardoutindexlabel(stand_in)


@pytest.mark.parametrize('name', LABELS)
def test_every_row_says_what_it_is(name):
    """Two rows named themselves and two showed a bare value — "44.1khz" and
    "32 bit integer", with nothing saying what they were, on exactly the two
    settings this item exists to make honest. Step 6 of
    agenda/honest_sound_settings.md."""
    stand_in = label_stand_in()
    label = getattr(sound_ui.SoundSettingsWindow, name)(stand_in)
    assert ':' in label, \
        "{} shows a value with no name: {!r}".format(name, label)
    assert label.split(':')[0].strip(), 'the name must not be empty'


@pytest.mark.parametrize('name', LABELS)
def test_every_label_survives_a_MISSING_setting(name):
    """`makedefaultifnot` should have filled these in, but the window must not
    depend on that having worked."""
    stand_in = label_stand_in()
    for attr in ('fs', 'sample_format', 'audio_card_in', 'audio_card_out'):
        if hasattr(stand_in.soundsettings, attr):
            delattr(stand_in.soundsettings, attr)
    getattr(sound_ui.SoundSettingsWindow, name)(stand_in)   # must not raise


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
