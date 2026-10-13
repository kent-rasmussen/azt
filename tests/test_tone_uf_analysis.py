"""Tone underlying-form (UF) analysis — `backend.core.analysis.Analysis`.

The glossary (CONTEXT.md, "Tone terms"): a word's UF tone is "composed from
its surface groups across all frames (words with the same cross-frame
signature share a UF). One value per sense (`uftonevalue`). Drafts are named
like `Noun_CVC_1` until the user renames them."

These tests assert that INTENDED behaviour. A failing test here is a
finding, not a test to loosen. Where the intent had to be inferred rather
than read, the test's docstring says so.

Headless: real `io_put.lift` tone fields on in-memory nodes (see
`tests/ufkit.py`); no file is read or written — `db.write()` is a counter.
"""
import re
from types import SimpleNamespace
from xml.etree import ElementTree as ET

import pytest

analysis = pytest.importorskip('backend.core.analysis')
lift = pytest.importorskip('io_put.lift')

import ufkit  # noqa: E402  (tests/ is on sys.path via conftest)
from ufkit import build_senses, make_program, tone_forms  # noqa: E402

NOUN_FRAMES = ['Isolation', 'Possessive']


def analyse(specs, frames_by_ps=None, slice_=('Noun', 'CVC'), run=True,
            current=None, cvt='T'):
    """Build senses from specs (all in `slice_`), run Analysis.do()."""
    frames_by_ps = frames_by_ps or {'Noun': NOUN_FRAMES}
    db, senses = build_senses(specs)
    prog = make_program({slice_: senses}, frames_by_ps, db,
                        current=current or slice_, cvt=cvt)
    a = analysis.Analysis(prog, ps=slice_[0], profile=slice_[1])
    if run:
        a.do()
    return prog, a, {s.id: s for s in senses}


def uf(s):
    """The UF group a word is in: join/rename, else draft (D3)."""
    return s.ufgroup()


# ── 1. the cross-frame signature ───────────────────────────────────────────

def test_words_agreeing_in_every_frame_share_one_UF_group():
    _, a, s = analyse([
        dict(id='a', tones={'Isolation': '1', 'Possessive': '2'}),
        dict(id='b', tones={'Isolation': '1', 'Possessive': '2'}),
        dict(id='c', tones={'Isolation': '1', 'Possessive': '2'}),
    ])
    assert uf(s['a']) and uf(s['a']) == uf(s['b']) == uf(s['c'])
    assert len(a.sensesbygroup) == 1
    assert set(a.sensesbygroup[uf(s['a'])]) == {s['a'], s['b'], s['c']}


@pytest.mark.parametrize('frame', NOUN_FRAMES)
def test_a_word_differing_in_any_one_frame_gets_a_different_UF(frame):
    other = {'Isolation': '1', 'Possessive': '2'}
    other[frame] = '3'
    _, a, s = analyse([
        dict(id='a', tones={'Isolation': '1', 'Possessive': '2'}),
        dict(id='b', tones={'Isolation': '1', 'Possessive': '2'}),
        dict(id='odd', tones=other),
    ])
    assert uf(s['a']) == uf(s['b'])
    assert uf(s['odd']) and uf(s['odd']) != uf(s['a'])
    assert len(a.sensesbygroup) == 2


def test_the_UF_group_records_its_surface_value_in_each_frame():
    _, a, s = analyse([
        dict(id='a', tones={'Isolation': '1', 'Possessive': '2'}),
        dict(id='b', tones={'Isolation': '1', 'Possessive': '3'}),
    ])
    assert a.valuesbygroupcheck[uf(s['a'])] == {'Isolation': ['1'],
                                                'Possessive': ['2']}
    assert a.valuesbygroupcheck[uf(s['b'])] == {'Isolation': ['1'],
                                                'Possessive': ['3']}


def test_comparison_outputs_cover_every_group_and_frame():
    """doanyway's orderings are what the join page and the report iterate;
    a group or frame missing from them never shows."""
    _, a, s = analyse([
        dict(id='a', tones={'Isolation': '1', 'Possessive': '2'}),
        dict(id='b', tones={'Isolation': '1', 'Possessive': '3'}),
        dict(id='c', tones={'Isolation': '2', 'Possessive': '3'}),
    ])
    assert sorted(a.orderedUFs) == sorted(a.sensesbygroup)
    assert sorted(a.orderedchecks) == sorted(NOUN_FRAMES)


# ── 2. draft names ─────────────────────────────────────────────────────────

FOUR_WORDS = [
    dict(id='a', tones={'Isolation': '1', 'Possessive': '2'}),
    dict(id='b', tones={'Isolation': '1', 'Possessive': '2'}),
    dict(id='c', tones={'Isolation': '1', 'Possessive': '3'}),
    dict(id='d', tones={'Isolation': '2', 'Possessive': '2'}),
]


def test_draft_names_are_ps_profile_n_and_unique_within_the_slice():
    _, a, s = analyse(FOUR_WORDS)
    names = list(a.sensesbygroup)
    assert len(names) == len(set(names)) == 3
    for n in names:
        assert re.fullmatch(r'Noun_CVC_[1-9][0-9]*', n), n
    numbers = sorted(int(n.rsplit('_', 1)[1]) for n in names)
    assert numbers == [1, 2, 3], "drafts are numbered 1..n with no gaps"
    # each sense carries the name of the group it is listed under
    for name, members in a.sensesbygroup.items():
        assert {uf(m) for m in members} == {name}


def test_draft_names_carry_the_slice_they_were_made_in():
    _, a, s = analyse([dict(id='v', ps='Verb',
                            tones={'Isolation-Verb': '1'})],
                      frames_by_ps={'Verb': ['Isolation-Verb']},
                      slice_=('Verb', 'CVCV'))
    assert uf(s['v']) == 'Verb_CVCV_1'


def test_draft_numbering_is_stable_for_the_same_input():
    _, _, s1 = analyse(FOUR_WORDS)
    _, _, s2 = analyse(FOUR_WORDS)
    assert {k: uf(v) for k, v in s1.items()} == \
           {k: uf(v) for k, v in s2.items()}


# ── 3. a word missing a value in a frame ───────────────────────────────────

def test_a_word_missing_one_frame_does_not_crash_and_gets_a_UF():
    _, a, s = analyse([
        dict(id='full', tones={'Isolation': '1', 'Possessive': '2'}),
        dict(id='part', tones={'Isolation': '1'}),
    ])
    assert uf(s['part']), "a partly sorted word still gets a draft UF"
    assert a.valuesbygroupcheck[uf(s['part'])] == {'Isolation': ['1']}


def test_a_word_missing_one_frame_is_its_own_draft_group():
    """READ from sorttoUFs: the signature is the set of frame:group pairs
    the word HAS, so a missing frame is a different signature, never a
    wildcard. Drafts are expected to be hypersplit and joined by the user
    (JoinUFgroups' own text), so this is consistent with the design; see
    the report for the open question of whether a gap should be a
    wildcard."""
    _, a, s = analyse([
        dict(id='full', tones={'Isolation': '1', 'Possessive': '2'}),
        dict(id='part', tones={'Isolation': '1'}),
    ])
    assert uf(s['part']) != uf(s['full'])


def test_an_empty_tone_value_counts_as_missing_not_as_a_group():
    """`if group:` in checkgroupsbysense: an example whose tone text is
    empty is the same as no example."""
    _, a, s = analyse([
        dict(id='none', tones={'Isolation': '1'}),
        dict(id='empty', tones={'Isolation': '1', 'Possessive': ''}),
    ])
    assert uf(s['none']) == uf(s['empty'])


def test_a_word_with_no_surface_tone_at_all_gets_no_UF_group():
    """INFERRED intent. A UF is 'composed from its surface groups across all
    frames'; a word sorted in no frame has none to compose from. sorttoUFs
    gives every sense in the slice a signature, so all unsorted words share
    a draft whose signature is empty (`{}`) — a UF group with no surface
    values, which the report and the join page then list as a real group."""
    _, a, s = analyse([
        dict(id='sorted', tones={'Isolation': '1', 'Possessive': '2'}),
        dict(id='unsorted1', tones={}),
        dict(id='unsorted2', tones={}),
    ])
    assert not uf(s['unsorted1'])
    assert not uf(s['unsorted2'])
    assert all(a.valuesbygroupcheck[g] for g in a.valuesbygroupcheck), \
        "no UF group should have an empty cross-frame signature"


# ── 4. which frames are in the signature ───────────────────────────────────

def test_frames_on_different_fields_are_all_in_the_signature():
    """A frame on a second form ('Plural') is as much a location as one on
    the citation form; words alike on lc but not on Plural differ in UF."""
    frames = {'Noun': ['Isolation', 'Possessive-pl']}
    _, a, s = analyse([
        dict(id='a', tones={'Isolation': '1', 'Possessive-pl': '4'}),
        dict(id='b', tones={'Isolation': '1', 'Possessive-pl': '5'}),
    ], frames_by_ps=frames)
    assert uf(s['a']) != uf(s['b'])
    assert set(a.orderedchecks) == {'Isolation', 'Possessive-pl'}


def test_examples_at_frames_outside_the_ps_do_not_split_UF_groups():
    """Only the slice's frames (status.checks for the ps) count. A leftover
    example at a frame the ps no longer has must not make a difference."""
    _, a, s = analyse([
        dict(id='a', tones={'Isolation': '1', 'Possessive': '2'}),
        dict(id='b', tones={'Isolation': '1', 'Possessive': '2',
                            'OldFrame': '9'}),
    ])
    assert uf(s['a']) == uf(s['b'])
    assert 'OldFrame' not in a.valuesbygroupcheck[uf(s['a'])]


def test_reading_UFs_back_from_LIFT_reports_only_the_ps_frames():
    """donoUFanalysis (the path reports and the join page normally take)
    must describe the same frames as do(). tonegroupsbyUFcheckfromLIFT
    iterates `sense.examples` — every example the sense has — instead of
    self.checks, so a frame outside the ps reaches the report."""
    prog, a, s = analyse([
        dict(id='a', tones={'Isolation': '1', 'Possessive': '2'}),
        dict(id='b', tones={'Isolation': '1', 'Possessive': '2',
                            'OldFrame': '9'}),
    ])
    a.donoUFanalysis()
    for group, byframe in a.valuesbygroupcheck.items():
        assert set(byframe) <= set(NOUN_FRAMES), (group, byframe)
    assert set(a.orderedchecks) <= set(NOUN_FRAMES)


def test_the_analysis_asks_for_TONE_frames_whatever_tier_is_current():
    """INFERRED intent: Analysis is tone-only (CONTEXT.md, 'Analysis …
    overloaded'), but setslice calls status.checks(ps=, profile=) without
    cvt='T', so it gets whatever tier params.cvt() names. The tone tasks
    set cvt 'T' first, so today this needs a caller that has not; it is a
    latent trap for a report or background caller."""
    prog, a, s = analyse([
        dict(id='a', tones={'Isolation': '1', 'Possessive': '2'}),
        dict(id='b', tones={'Isolation': '1', 'Possessive': '3'}),
    ], cvt='V')
    assert a.checks == NOUN_FRAMES
    assert uf(s['a']) != uf(s['b'])


# ── 5. write-back ──────────────────────────────────────────────────────────

def test_do_writes_the_draft_to_the_machine_tone_form():
    """D3 (Kent, 2026-10-13): "put our analysis into machine codes, then the
    joined and renamed forms into data fields". The draft replaces an old
    machine value; the human form is the user's, and holds nothing until
    they join or rename."""
    prog, a, s = analyse([
        dict(id='a', tones={'Isolation': '1'}, uf_mt='machine-guess'),
    ], frames_by_ps={'Noun': ['Isolation']})
    db = prog.db
    human = db.tonelangname(db.analang)
    machine = db.tonelangname(db.analang, machine=True)
    assert human != machine
    forms = tone_forms(s['a'])
    assert forms[machine] == 'Noun_CVC_1'
    assert human not in forms
    assert len(s['a'].findall('field[@type="tone"]')) == 1, \
        "one sense-level tone field, not a second one"


def test_reanalysis_drops_an_old_join():
    """D5 (Kent, 2026-10-13): "joining is supposed to be ephemeral, and
    analysis changes with new data"."""
    prog, a, s = analyse([
        dict(id='a', tones={'Isolation': '1'}, uf='High'),
    ], frames_by_ps={'Noun': ['Isolation']})
    db = prog.db
    assert uf(s['a']) == 'Noun_CVC_1'
    human = db.tonelangname(db.analang)
    assert not s['a'].findall(f'field[@type="tone"]/form[@lang="{human}"]')


def test_do_writes_LIFT_once_and_stamps_the_analysis():
    prog, a, s = analyse(FOUR_WORDS)
    assert prog.db.writes == 1
    assert [c[0] for c in prog.status.last_calls] == ['analysis']
    assert prog.status.last_calls[0][1] is True
    assert prog.status.stores == 1


def test_the_analysis_stamp_goes_to_the_slice_that_was_analysed():
    """INFERRED intent (JoinUFgroups: '#Should specify which lasts...').
    makeanalysis(**kwargs) analyses ANY slice (reports iterate slices), but
    do() calls status.last('analysis', update=True) with no ps/profile, so
    StatusDict.last stamps the CURRENT slice: the analysed one keeps looking
    stale (isanalysisOK False → re-analysis, overwriting joins) and the
    current one looks freshly analysed when it was not."""
    prog, a, s = analyse(FOUR_WORDS, slice_=('Verb', 'CVCV'),
                         frames_by_ps={'Verb': NOUN_FRAMES},
                         current=('Noun', 'CVC'))
    assert prog.status.last_calls, "do() records the analysis time"
    _, _, kw = prog.status.last_calls[0]
    assert kw.get('ps') == 'Verb' and kw.get('profile') == 'CVCV', kw


def test_rerunning_on_unchanged_data_changes_nothing():
    prog, a, s = analyse(FOUR_WORDS)
    before_xml = {k: ET.tostring(v) for k, v in s.items()}
    before = ({k: uf(v) for k, v in s.items()},
              {g: sorted(m.id for m in ms)
               for g, ms in a.sensesbygroup.items()},
              dict(a.valuesbygroupcheck))
    a.do()
    after = ({k: uf(v) for k, v in s.items()},
             {g: sorted(m.id for m in ms)
              for g, ms in a.sensesbygroup.items()},
             dict(a.valuesbygroupcheck))
    assert after == before
    assert {k: ET.tostring(v) for k, v in s.items()} == before_xml


def test_reading_back_from_LIFT_gives_the_groups_do_wrote():
    """donoUFanalysis (reports, join page) must see what do() wrote."""
    prog, a, s = analyse(FOUR_WORDS)
    wrote_members = {g: set(ms) for g, ms in a.sensesbygroup.items()}
    wrote_values = {g: {f: set(v) for f, v in byf.items()}
                    for g, byf in a.valuesbygroupcheck.items()}
    a.donoUFanalysis()
    assert {g: set(ms) for g, ms in a.sensesbygroup.items()} == wrote_members
    assert {g: {f: set(v) for f, v in byf.items()}
            for g, byf in a.valuesbygroupcheck.items()} == wrote_values


# ── Tone.getsensesinUFgroup / getUFgroupofsense ────────────────────────────

def test_UF_lookups_prefer_the_human_form_then_the_machine_draft():
    """D3: a join/rename (human form) wins; a word with only a draft
    (machine form) is in its draft group."""
    lexicon = pytest.importorskip('backend.core.lexicon')
    db, senses = build_senses([
        dict(id='h1', uf='High'),
        dict(id='h2', uf='High', uf_mt='Noun_CVC_2'),   # joined: human wins
        dict(id='lo', uf='Low'),
        dict(id='mt', uf_mt='High'),            # draft only
        dict(id='d', uf_mt='Noun_CVC_3'),
    ])
    s = {x.id: x for x in senses}
    task = SimpleNamespace(program=SimpleNamespace(db=db))
    got = lexicon.Tone.getsensesinUFgroup(task, 'High')
    assert {x.id for x in got} == {'h1', 'h2', 'mt'}
    assert lexicon.Tone.getUFgroupofsense(task, s['lo']) == 'Low'
    assert lexicon.Tone.getUFgroupofsense(task, s['h2']) == 'High'
    assert lexicon.Tone.getUFgroupofsense(task, s['d']) == 'Noun_CVC_3'


# ── status.checks(): every frame of the ps (the 2026-10-12 withdrawal) ─────

def real_status(toneframes, ftype='lc', pss=('Noun', 'Verb'), ps='Noun'):
    prog = SimpleNamespace(
        params=SimpleNamespace(cvt=lambda *a: 'T', ftype=lambda *a: ftype,
                               check=lambda *a: None),
        slices=SimpleNamespace(pss=lambda: list(pss), ps=lambda: ps,
                               profile=lambda: 'CVC'),
        toneframes=toneframes)
    st = analysis.StatusDict('status.json', {}, prog)
    st.task(SimpleNamespace(is_sort_task=False))
    return prog, st


TONEFRAMES = {
    'Noun': {'Isolation': {'field': 'lc', 'en': '__'},
             'Possessive-pl': {'field': 'Plural', 'en': 'my __'}},
    'Verb': {'Isolation-Verb': {'field': 'lc', 'en': 'to __'}},
}


@pytest.mark.parametrize('ftype', ['lc', 'pl', 'Plural'])
def test_status_checks_gives_every_frame_of_the_ps_whatever_the_form(ftype):
    """The form filter added to updatechecksbycvt on 2026-10-12 was
    withdrawn the same day; the UF analysis and reports must see every frame
    of the ps, on every field, whichever form is current — and no frame of
    another ps."""
    _, st = real_status(TONEFRAMES, ftype=ftype)
    assert sorted(st.checks(ps='Noun', profile='CVC')) == \
        ['Isolation', 'Possessive-pl']
    assert st.checks(ps='Verb', profile='CVCV') == ['Isolation-Verb']


def test_UF_analysis_on_the_real_status_includes_the_plural_frame():
    prog, st = real_status(TONEFRAMES, ftype='lc')
    db, senses = build_senses([
        dict(id='a', tones={'Isolation': '1', 'Possessive-pl': '4'}),
        dict(id='b', tones={'Isolation': '1', 'Possessive-pl': '5'}),
        dict(id='c', tones={'Isolation': '1', 'Possessive-pl': '4'}),
    ])
    prog.db = db
    prog.slices.senses = lambda ps=None, profile=None, **k: list(senses)
    a = analysis.Analysis(prog, ps='Noun', profile='CVC')
    assert sorted(a.checks) == ['Isolation', 'Possessive-pl']
    a.checkgroupsbysense()
    a.sorttoUFs()
    s = {x.id: x for x in senses}
    assert uf(s['a']) == uf(s['c']) != uf(s['b'])
