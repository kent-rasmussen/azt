"""A tone location reads and writes its OWN form, never the global one.

Kent, 2026-10-12: "let's make everything write the location.ftype. Let's
offer all locations for a ps, then read and write correctly by
location.ftype." A frame is built on one form for good (its `field`). Before
this, rewriting an existing example used `params.ftype()`, so a plural frame
sorted while the global form was `lc` put citation forms into its examples;
and the sort page handed `sense.formatted` the global form with a plural
frame, which it refuses, so the word showed no text.
"""
from types import SimpleNamespace

import pytest

lexicon = pytest.importorskip('backend.core.lexicon')
sorting_engine = pytest.importorskip('backend.core.sorting_engine')

PL_FRAME = {'field': 'pl', 'xyz_pl': 'nde __ wa', 'en': 'these are my __'}


def program(global_ftype='lc'):
    from backend.core import analysis_inputs
    p = analysis_inputs.CheckParameters.__new__(analysis_inputs.CheckParameters)
    p.ftype = lambda: global_ftype
    prog = SimpleNamespace(
        params=p,
        settings=SimpleNamespace(secondformfield={'Noun': 'Plural'},
                                 nominalps='Noun', verbalps='Verb'),
        toneframes={'Noun': {'Possessive-pl': PL_FRAME}})
    p.program = prog
    return prog


def test_a_field_name_is_never_mapped_to_a_code():
    """A language can have two plural fields; a frame on one must not pick
    up the other because both are 'plural' (Kent, 2026-10-13)."""
    p = program().params
    assert p.form_code('Plural') == 'Plural'
    assert p.form_code('pl') == 'pl'
    assert p.form_code(None) == 'lc'


def test_a_frame_stored_by_field_name_uses_that_field():
    item = FakeSense()
    prog = program('lc')
    prog.toneframes = {'Noun': {'Possessive-pl': {'field': 'Plural',
                                                  'en': 'my __'}}}
    s = SimpleNamespace(program=prog, analang='xyz', glosslangs=['en'])
    lexicon.Tone.setitemgroup(s, item, 'Possessive-pl', '3')
    assert item.asked == ['Plural']
    assert item.examples['Possessive-pl'].tone == '3'


def test_a_sense_without_the_form_still_gets_its_group():
    """A KeyError there fell into the new-example branch, which refuses an
    existing example, so the group was never written."""
    item = FakeSense()
    del item.ftypes['pl']
    s = SimpleNamespace(program=program('lc'), analang='xyz', glosslangs=['en'])
    lexicon.Tone.setitemgroup(s, item, 'Possessive-pl', '4')
    assert item.examples['Possessive-pl'].tone == '4'


def test_location_ftype_is_the_frames_own_form():
    s = SimpleNamespace(program=program('lc'))
    assert sorting_engine.Sort.location_ftype(s, PL_FRAME) == 'pl'


def test_without_a_frame_it_is_the_form_being_worked_on():
    s = SimpleNamespace(program=program('lc'))
    assert sorting_engine.Sort.location_ftype(s, None) == 'lc'
    assert sorting_engine.Sort.location_ftype(s, {'en': '__'}) == 'lc'


class FakeExample:
    def __init__(self):
        self.text = self.tone = None

    def textvaluebylang(self, lang=None, value=None):
        self.text = value

    def tonevalue(self, value=None):
        self.tone = value

    def translationvalue(self, lang, value):
        pass

    def lastAZTsort(self):
        pass


class FakeSense:
    def __init__(self):
        self.examples = {'Possessive-pl': FakeExample()}
        self.ftypes = {'lc': [], 'pl': []}
        self.glosses = {}                 # no glosses: no translation rewrite
        self.asked = []

    def psvalue(self):
        return 'Noun'

    def nodebyftype(self, ftype):
        return self.ftypes.get(ftype)

    def formattedform(self, analang, ftype=None, frame=False):
        self.asked.append(ftype)
        return f'<{ftype} form in frame>'

    def formattedgloss(self, g, frame=None):
        return []


TONEFRAMES = {'Noun': {'Isolation': {'field': 'lc', 'en': '__'},
                       'Possessive-pl': PL_FRAME,
                       'Old': {'en': 'the __'}}}       # no field: a citation frame


def params_with_frames():
    from backend.core import analysis_inputs
    p = analysis_inputs.CheckParameters.__new__(analysis_inputs.CheckParameters)
    p.program = SimpleNamespace(toneframes=TONEFRAMES)
    return p


def test_frame_form_reads_the_definition():
    p = params_with_frames()
    assert p.frame_form('Noun', 'Possessive-pl') == 'pl'
    assert p.frame_form('Noun', 'Isolation') == 'lc'
    assert p.frame_form('Noun', 'Old') == 'lc'
    assert p.frame_form('Noun', 'Missing') is None
    assert p.frame_form('Verb', 'Isolation') is None


class ToneSense:
    def __init__(self, values):
        self.values = values

    def tonevaluedict(self):
        return self.values


def test_tone_status_keeps_only_the_loaded_forms_frames():
    lift = pytest.importorskip('io_put.lift')
    db = SimpleNamespace(
        ps_profiles={'Noun': ['CVC']},
        sensesbyps_profile={'Noun': {'CVC': [
            ToneSense({'Isolation': '1', 'Possessive-pl': '2'})]}})
    every = lift.LiftXML.tone_values_by_ps_profile(db)
    assert set(every['Noun']['CVC']) == {'Isolation', 'Possessive-pl'}
    lc_only = lift.LiftXML.tone_values_by_ps_profile(
                                    db, frames={'Noun': {'Isolation'}})
    assert set(lc_only['Noun']['CVC']) == {'Isolation'}, \
        "a plural frame must not be filed under citation-form profiles"


def fake_settings(form='lc'):
    state = {'ftype': form, 'ps': 'Noun', 'rebuilt': None, 'ps_set': None}
    params = params_with_frames()
    params.ftype = lambda v=None: state.update(ftype=v) if v else state['ftype']
    def ps(v=None):
        if v:
            state['ps_set'] = v
        return state['ps']
    s = SimpleNamespace(
        program=SimpleNamespace(
            params=params, toneframes=TONEFRAMES,
            slices=SimpleNamespace(ps=ps),
            profiles=SimpleNamespace(
                rebuild_slices=lambda f: state.update(rebuilt=f))),
        statusisup=lambda: False,
        attrschanged=[])
    return s, state


def test_choosing_a_frame_on_another_form_switches_to_it():
    settings_ui = pytest.importorskip('settings') and \
        __import__('frontend.config.settings_ui', fromlist=['SettingsUI'])
    s, state = fake_settings('lc')
    assert settings_ui.SettingsUI._tone_frame_sets_the_form(s, 'Possessive-pl')
    assert state['ftype'] == 'pl'
    assert state['rebuilt'] == 'pl', "slices are rebuilt from plural profiles"
    assert state['ps_set'] == 'Noun', "the ps is kept"
    assert 'ftype' in s.attrschanged


def test_choosing_a_frame_on_the_same_form_changes_nothing():
    settings_ui = pytest.importorskip('settings') and \
        __import__('frontend.config.settings_ui', fromlist=['SettingsUI'])
    s, state = fake_settings('lc')
    assert not settings_ui.SettingsUI._tone_frame_sets_the_form(s, 'Isolation')
    assert state['ftype'] == 'lc' and state['rebuilt'] is None
    assert s.attrschanged == []


def test_no_check_means_no_groups_not_a_crash():
    """Opening the tone sort on a ps with no frames on the current form
    unset the check, then asked for its groups: KeyError: None (log,
    2026-10-12)."""
    analysis = pytest.importorskip('backend.core.analysis')
    def boom(**kw):
        raise KeyError(None)
    set_to = []
    s = SimpleNamespace(
        program=SimpleNamespace(params=SimpleNamespace(check=lambda: None)),
        groups=boom, group=lambda g: set_to.append(g), _group='1')
    analysis.StatusDict.makegroupok(s)
    assert set_to == [None]


def test_a_ps_with_frames_only_on_another_form_moves_to_that_form():
    analysis = pytest.importorskip('backend.core.analysis')
    asked = []
    s = SimpleNamespace(program=SimpleNamespace(
        slices=SimpleNamespace(ps=lambda: 'Verb'),
        toneframes={'Verb': {'Command': {'field': 'imp'}}},
        settings=SimpleNamespace(
            _tone_frame_sets_the_form=lambda f: asked.append(f) or True)))
    assert analysis.StatusDict._tone_form_with_frames(s, None)
    assert asked == ['Command']
    s.program.toneframes = {'Noun': {}}
    asked.clear()
    assert not analysis.StatusDict._tone_form_with_frames(s, None)
    assert asked == []


def test_rewriting_an_existing_example_uses_the_frames_form():
    item = FakeSense()
    s = SimpleNamespace(program=program('lc'), analang='xyz', glosslangs=['en'])
    lexicon.Tone.setitemgroup(s, item, 'Possessive-pl', '2')
    assert item.asked == ['pl'], "the global form (lc) must not be used"
    ex = item.examples['Possessive-pl']
    assert ex.text == '<pl form in frame>' and ex.tone == '2'
