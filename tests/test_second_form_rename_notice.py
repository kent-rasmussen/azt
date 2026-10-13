"""Renaming a second-form field tells the user about the data it leaves behind.

Kent, 2026-10-12: renaming orphans the old field's data, "a consequence of
changing data forms. If someone changes from a field name with lots of data
in it, we should probably post a note that they should convert that data
manually, if they want to use it under the new field name." Nothing is moved;
the user is told, through the Messages window (notify_user).
"""
from types import SimpleNamespace

import pytest

# The `settings` package FIRST: it imports settings_ui itself (settings/__init__),
# and settings_ui → migration → settings is a cycle when settings_ui is
# imported on its own. Entered through `settings`, settings_ui is complete.
pytest.importorskip('settings')
from frontend.config import settings_ui            # noqa: E402
SettingsUI = settings_ui.SettingsUI


class FakeField:
    def __init__(self, text):
        self.text = text

    def textvaluebylang(self, lang=None, value=None, machine=False):
        return self.text


def fake_self(entries, stored=None, is_set=True):
    return SimpleNamespace(
        program=SimpleNamespace(
            params=SimpleNamespace(analang=lambda: 'xyz'),
            db=SimpleNamespace(entries=entries)),
        secondformfield=dict(stored or {}),
        secondformfieldset=lambda ps: is_set,
        _frames_on_field=lambda ps, field: [],
    )


def entry(**fields):
    return SimpleNamespace(fields={k: FakeField(v) for k, v in fields.items()})


@pytest.fixture
def notices(monkeypatch):
    said = []
    monkeypatch.setattr(settings_ui, 'notify_user',
                        lambda text, **kw: said.append((text, kw)))
    return said


def note(self, old, new):
    return SettingsUI._note_data_left_in_old_field(self, 'Noun', old, new)


def test_old_field_with_data_is_announced_with_its_count(notices):
    s = fake_self([entry(Plural='babibi'), entry(Plural='pibabi'),
                   entry(Plural=''), entry(Other='x')])
    assert note(s, 'Plural', 'Plurals') == 2
    (text, kw), = notices
    assert '‘Plural’' in text and '‘Plurals’' in text and ': 2.' in text
    assert 'Plural' in kw.get('title', '')


def test_no_data_in_the_old_field_says_nothing(notices):
    s = fake_self([entry(Plural=''), entry(Other='x')])
    assert note(s, 'Plural', 'Plurals') == 0
    assert notices == []


def test_same_name_or_no_old_field_says_nothing(notices):
    s = fake_self([entry(Plural='babibi')])
    assert note(s, 'Plural', 'Plural') == 0
    assert note(s, None, 'Plural') == 0
    assert notices == []


def test_the_old_field_is_read_only_when_it_was_really_set():
    s = fake_self([], stored={'Noun': '<unset>'}, is_set=False)
    assert SettingsUI._old_second_form_field(s, 'Noun') is None
    s = fake_self([], stored={'Noun': 'Plural'})
    assert SettingsUI._old_second_form_field(s, 'Noun') == 'Plural'


def test_a_failed_count_never_breaks_the_setting(notices):
    s = fake_self(None)                 # iterating None raises inside
    assert note(s, 'Plural', 'Plurals') is None   # unknown, not "no data"
    assert notices == []


class FakeFrames(dict):
    stored = 0

    def store(self):
        FakeFrames.stored += 1


def frames():
    FakeFrames.stored = 0
    return FakeFrames({'Noun': {
        'Possessive-pl': {'field': 'Plural', 'xyz_Plural': 'nde __ wa',
                          'en': 'my __'},
        'Isolation': {'field': 'lc', 'xyz_lc': '__', 'en': '__'}}})


@pytest.fixture
def offers(monkeypatch):
    shown = []
    monkeypatch.setattr(settings_ui, 'ErrorNotice',
                        lambda text, **kw: shown.append((text, kw)))
    return shown


def offer(s, old, new, left):
    s._frames_on_field = lambda ps, f: SettingsUI._frames_on_field(s, ps, f)
    s._move_frames_to_field = lambda ps, o, n: \
        SettingsUI._move_frames_to_field(s, ps, o, n)
    return SettingsUI._offer_to_move_frames(s, 'Noun', old, new, left)


def test_an_apparent_rename_only_OFFERS_to_move_the_frames(offers):
    """Kent, 2026-10-13: "we can't just rename here. we can offer the user
    to ask for that, but don't just do it without the user's request"."""
    s = fake_self([])
    s.program.toneframes = frames()
    assert offer(s, 'Plural', 'Pluriel', 0) == ['Possessive-pl']
    assert s.program.toneframes['Noun']['Possessive-pl']['field'] == 'Plural'
    assert FakeFrames.stored == 0, 'nothing moves until the user asks'
    (text, kw), = offers
    assert 'Possessive-pl' in text
    label, act = kw['button']
    act()                                   # the user asks
    d = s.program.toneframes['Noun']['Possessive-pl']
    assert d['field'] == 'Pluriel'
    assert d['xyz_Pluriel'] == 'nde __ wa' and 'xyz_Plural' not in d
    assert s.program.toneframes['Noun']['Isolation']['field'] == 'lc'
    assert FakeFrames.stored == 1


def test_two_fields_offer_nothing_and_move_nothing(offers):
    """Data still in the old field: two different fields, and a frame good
    for one may not suit the other."""
    s = fake_self([])
    s.program.toneframes = frames()
    assert offer(s, 'Plural', 'Plural2', 5) == []
    assert offers == []
    assert s.program.toneframes['Noun']['Possessive-pl']['field'] == 'Plural'


def test_an_unknown_count_offers_nothing(offers):
    s = fake_self([])
    s.program.toneframes = frames()
    assert offer(s, 'Plural', 'Pluriel', None) == []
    assert offers == []


def test_the_note_names_the_frames_that_stay(notices):
    s = fake_self([entry(Plural='babibi')])
    s.program.toneframes = frames()
    s._frames_on_field = lambda ps, f: SettingsUI._frames_on_field(s, ps, f)
    note(s, 'Plural', 'Plural2')
    (text, _kw), = notices
    assert 'Possessive-pl' in text
