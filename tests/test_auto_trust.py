"""Words created since the last Trust are trusted without asking (backend/core/profiles.py auto_trust_new;
Kent 2026-11-11), all of them on a lexicon's first open. Fake program, real methods."""
import types

import pytest

try:
    from backend.core.profiles import ProfileAnalyzer
except ImportError as e:  # optional dep missing in this env
    pytest.skip(f"optional dependency not installed: {e.name}", allow_module_level=True)


class Entry(dict):
    pass


class Sense:
    def __init__(self, created, profile=None, machine='CVC'):
        self.entry = Entry(dateCreated=created)
        self.profile = profile
        self.machine = machine

    def cvprofilevalue(self, ftype, value=None):
        if value:
            self.profile = value
        return self.profile


class Settings:
    def __init__(self, dates=None):
        self.dates = dict(dates or {})
        self.stored = []

    def trust_dates(self, value=None):
        if isinstance(value, dict):
            self.dates = dict(value)
        return dict(self.dates)

    def storesettingsfile(self, setting='defaults'):
        self.stored.append(setting)


def _profiles(senses, dates=None):
    program = types.SimpleNamespace(db=types.SimpleNamespace(senses=senses),
                                    settings=Settings(dates), writes=[])
    program.maybewrite = lambda definitely=False: program.writes.append(definitely)
    p = types.SimpleNamespace(program=program, rebuilt=[])
    for name in ('note_trust', 'created_since_trust', 'auto_trust_new', 'affirm_machine_profiles'):
        setattr(p, name, types.MethodType(getattr(ProfileAnalyzer, name), p))
    p.trusted_profile_for = lambda s, ftype=None: None if s.profile else s.machine
    p._set_trusted_profile = lambda s, ftype, prof: s.cvprofilevalue(ftype, prof)
    p.rebuild_slices = lambda ftype=None: p.rebuilt.append(ftype)
    return p


def test_first_open_trusts_everything_and_records_it():
    senses = [Sense('2008-08-09T05:17:11Z'), Sense('2026-11-11T10:00:00Z')]
    p = _profiles(senses)
    assert p.auto_trust_new('lc') == 2
    assert [s.profile for s in senses] == ['CVC', 'CVC']
    assert 'lc' in p.program.settings.dates and p.program.settings.stored == ['profiledata']


def test_only_words_created_since_the_last_trust():
    old, new = Sense('2026-11-01T00:00:00Z'), Sense('2026-11-10T00:00:00Z')
    p = _profiles([old, new], {'lc': '2026-11-05T00:00:00Z'})
    assert p.auto_trust_new('lc') == 1
    assert old.profile is None and new.profile == 'CVC'      # old: sent back or newly profilable; asked


def test_no_record_but_profiles_exist_asks_as_before():
    """Lexicons trusted before the date was kept: a missing profile may be one the user sent back."""
    done, missing = Sense('2026-11-01T00:00:00Z', profile='CV'), Sense('2026-11-02T00:00:00Z')
    p = _profiles([done, missing])
    assert p.auto_trust_new('lc') == 0
    assert missing.profile is None
    assert p.program.settings.dates == {}


def test_trust_dates_are_per_form():
    p = _profiles([Sense('2026-11-10T00:00:00Z')], {'lc': '2026-11-05T00:00:00Z'})
    p.note_trust('pl')
    assert set(p.program.settings.dates) == {'lc', 'pl'}
