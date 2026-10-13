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
    assert note(s, 'Plural', 'Plurals') == 0
    assert notices == []
