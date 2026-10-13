"""The `tone_mini` LIFT fixture, and a way to load it through the real loader.

WHAT THE FIXTURE IS (tests/fixtures/tone_mini/tone_mini.lift)
--------------------------------------------------------------
Eight entries in the analysis language 'xyy', glossed in English. The words
are invented. 'xyz' is the suite's usual stand-in, but langcodes does not
register it, so `LiftXML.get_langs` would drop it from `analangs`. 'xyy' is
registered.

    gloss  citation  ps    cvprofile_lc  entry fields
    dog    kalo      Noun  CVCV          Plural=bakalo
    house  tama      Noun  CVCV          Plural=matama   (already sorted, see below)
    tree   sibo      Noun  CVCV          Plural=misibo, Pluriel=basibo
    eye    kan       Noun  CVC           Plural=makan
    stone  tob       Noun  CVC           (no Plural)
    see    pema      Verb  CVCV
    eat    lisa      Verb  CVCV
    go     dop       Verb  CVC

Each sense has a confirmed profile: the plain `xyy-x-cvprofile` form of the
`cvprofile_lc` field. dog and house also carry the machine `_MT` form, the
way a profiled project does. 'Pluriel' on tree is a SECOND plural-like
field. It is there so a test can show that a frame built on 'Plural' reads
that field by name, and never "whichever field is the plural now".

house ('tama') is already sorted the way azt writes it: an Isolation example
with tone group '1', text 'tama ka' and translation 'the house', plus the
code 'Isolation=1' in its 'CVCV lc verification' field.

The tone frames (TONEFRAMES) are not in the LIFT, since azt keeps them in
settings:
    Noun/Isolation   on 'lc'      xyy '__ ka'     en 'the __'
    Noun/Possessive  on 'Plural'  xyy 'nde __ wa' en 'my __'
    Verb/Infinitive  on 'lc'      xyy 'ku __'     en 'to __'
The analysis-language key is '<analang>_<field>', as ToneFrameDrafter writes
it (`analangftypecode`) and FormParent.formattedbylang reads it
(`langftypecode`).

HOW TO USE IT
-------------
    db = load_lift(tmp_path, monkeypatch)     # a real io_put.lift.LiftXML
    kalo = sense(db, 'dog')
    program = make_program(db)                # Noun / CVCV / Isolation, cvt T
    work = tone_worker(program)               # real Sort + Tone methods
    work.setitemgroup(kalo, 'Isolation', '2')
    db.write(); db2 = reload_lift(db)         # round trip

Loading is sandboxed. The LIFT is copied into tmp_path. The cwd moves to
tmp_path for the test, because `Sense.getglosses` looks for 'images/toselect/'
relative to the cwd and runs `images.to_select_update.ensure_available()` (a
git clone) when the folder is missing. An empty one is created there, and
that function is replaced by one that fails the test if anything calls it.
The audio/, images/ and reports/ folders that the loader makes go next to
the copied LIFT. Nothing touches the network, the user's projects or the
real image folders.

`make_program` uses the real CheckParameters, ToneFrames and StatusDict.
Only the edges are fakes: slices (whose `inslice` is the real
SliceDict.inslice), settings (it records stores, and borrows the real status
rebuild methods from settings.Settings), and the example cache.
"""
import copy
import pathlib
import shutil
import sys
import threading
from types import SimpleNamespace

ANALANG = 'xyy'
GLOSSLANG = 'en'
HERE = pathlib.Path(__file__).resolve().parent
FIXTURE = HERE / 'fixtures' / 'tone_mini' / 'tone_mini.lift'

ISOLATION = {'field': 'lc', 'xyy_lc': '__ ka', 'en': 'the __'}
POSSESSIVE = {'field': 'Plural', 'xyy_Plural': 'nde __ wa', 'en': 'my __'}
INFINITIVE = {'field': 'lc', 'xyy_lc': 'ku __', 'en': 'to __'}
TONEFRAMES = {'Noun': {'Isolation': ISOLATION, 'Possessive': POSSESSIVE},
              'Verb': {'Infinitive': INFINITIVE}}

# gloss: (citation, ps, profile, Plural or None)
WORDS = {
    'dog':   ('kalo', 'Noun', 'CVCV', 'bakalo'),
    'house': ('tama', 'Noun', 'CVCV', 'matama'),
    'tree':  ('sibo', 'Noun', 'CVCV', 'misibo'),
    'eye':   ('kan',  'Noun', 'CVC',  'makan'),
    'stone': ('tob',  'Noun', 'CVC',  None),
    'see':   ('pema', 'Verb', 'CVCV', None),
    'eat':   ('lisa', 'Verb', 'CVCV', None),
    'go':    ('dop',  'Verb', 'CVC',  None),
}
TOSELECT = 'images/toselect/'


def toneframes_dict():
    """A fresh copy of TONEFRAMES, so no test can change another's frames."""
    return copy.deepcopy(TONEFRAMES)


def _no_download():
    raise AssertionError("the LIFT load tried to download the image set "
                         "(images.to_select_update.ensure_available)")


def _sandbox(tmp_path, monkeypatch):
    from utilities import file
    monkeypatch.chdir(tmp_path)
    (tmp_path / TOSELECT).mkdir(parents=True, exist_ok=True)
    monkeypatch.setitem(sys.modules, 'images.to_select_update',
                        SimpleNamespace(ensure_available=_no_download))
    # The listing cache is keyed by the RELATIVE path, so a listing cached
    # under another cwd (the real image folder) would be served here. A
    # private cache for the test, restored afterwards.
    monkeypatch.setattr(file, '_dircache', {})


def _load(path):
    """LiftXML(path, ANALANG), then wait for the duplicate-example threads
    the loader starts, so they never run alongside a test's writes."""
    from io_put import lift
    before = set(threading.enumerate())
    db = lift.LiftXML(str(path), ANALANG)
    for t in set(threading.enumerate()) - before:
        t.join(timeout=10)
    return db


def load_lift(tmp_path, monkeypatch):
    """Copy the fixture into tmp_path and load it with the real loader."""
    _sandbox(tmp_path, monkeypatch)
    proj = tmp_path / 'project'
    proj.mkdir(exist_ok=True)
    dest = proj / FIXTURE.name
    shutil.copyfile(FIXTURE, dest)
    return _load(dest)


def reload_lift(db):
    """Load db's file again. Call it in the same test as load_lift, which
    is what keeps the cwd in the sandbox."""
    return _load(db.filename)


def sense(db, gloss):
    """The sense whose English gloss is `gloss`."""
    found = [s for s in db.senses
             if [g.textvalue() for g in s.glosses.get(GLOSSLANG, [])] == [gloss]]
    assert len(found) == 1, f"{len(found)} senses glossed {gloss!r}"
    return found[0]


def sense_by_id(db, senseid):
    return db.sensedict[senseid]


class Slices:
    """The current ps/profile slice, read from the loaded LIFT's own
    ps/profile index (`db.sensesbyps_profile`). `inslice` is the real
    SliceDict.inslice."""
    def __init__(self, program, ps, profile):
        self.program = program
        self._ps = ps
        self._profile = profile

    def ps(self, ps=None):
        if ps:
            self._ps = ps
        return self._ps

    def profile(self, profile=None):
        if profile:
            self._profile = profile
        return self._profile

    def senses(self, ps=None, profile=None, **kwargs):
        byps = self.program.db.sensesbyps_profile.get(ps or self._ps, {})
        return list(byps.get(profile or self._profile, []))

    def inslice(self, s=None, **kwargs):
        from backend.core.analysis import SliceDict
        return SliceDict.inslice(self, s, **kwargs)


class SettingsStub:
    """What the tone paths ask of program.settings. Stores are recorded, not
    written. The status rebuild methods are the real ones from
    settings.Settings, run with this object as `self`."""
    def __init__(self, program):
        self.program = program
        self.glosslangs = [GLOSSLANG]
        self.secondformfield = {'Noun': 'Plural'}
        self.nominalps = 'Noun'
        self.verbalps = 'Verb'
        self.stored = []

    def secondformfieldset(self, ps):
        return bool(self.secondformfield.get(ps))

    def storesettingsfile(self, setting='defaults'):
        self.stored.append(setting)

    @staticmethod
    def _real(name):
        import settings
        return getattr(settings.Settings, name)

    def reloadstatusdata(self):
        return self._real('reloadstatusdata')(self)

    def reloadstatusdata_cleanup(self):
        return self._real('reloadstatusdata_cleanup')(self)

    def generate_status_by_annotations(self, **kwargs):
        return self._real('generate_status_by_annotations')(self, **kwargs)

    def generate_status_by_tone_groups(self, **kwargs):
        return self._real('generate_status_by_tone_groups')(self, **kwargs)

    def scrub_foreign_status(self):
        return self._real('scrub_foreign_status')(self)


class ExampleCacheStub:
    """program.examples: only the cache is dropped on these paths."""
    def __init__(self):
        self.cleared = []

    def clear_cache(self, **kwargs):
        self.cleared.append(kwargs)


def make_program(db, ps='Noun', profile='CVCV', check='Isolation',
                 ftype='lc'):
    """A `program` for tone work on `db`: real CheckParameters (cvt 'T'),
    ToneFrames (TONEFRAMES) and an empty StatusDict, sitting on the
    ps/profile slice given."""
    from backend.core.analysis import StatusDict
    from backend.core.analysis_inputs import CheckParameters, ToneFrames
    program = SimpleNamespace(db=db, Demo=True)
    program.settings = SettingsStub(program)
    program.slices = Slices(program, ps, profile)
    program.examples = ExampleCacheStub()
    ToneFrames(program, toneframes_dict())      # sets program.toneframes
    CheckParameters(program)                     # sets program.params
    program.params.cvt('T')
    program.params.check(check)
    program.params.ftype(ftype)
    StatusDict('status', {}, program)            # sets program.status
    return program


def tone_worker(program):
    """An object with the real Sort (and so Categories) and Tone methods,
    as SortT has them, minus the window. `maybewrite` is counted."""
    from backend.core.lexicon import Tone
    from backend.core.sorting_engine import Sort

    class ToneWork(Sort, Tone):
        def maybewrite(self, definitely=False):
            self.writes += 1

    w = ToneWork()
    w.program = program
    w.cvt = 'T'
    w.analang = program.params.analang()
    w.glosslangs = list(program.settings.glosslangs)
    w.writes = 0
    return w
