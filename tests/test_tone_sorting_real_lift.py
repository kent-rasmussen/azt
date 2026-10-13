"""Tone sorting on a REAL lexicon, loaded through the real loader.

Uses the `tone_mini` fixture (see tests/tonefixture.py for what is in it).
Every test loads a fresh copy into tmp_path, works on real io_put.lift Sense
and Example objects, and calls the real backend methods: Tone.setitemgroup /
getitemgroup / getsensesingroup, Sort.updatestatus (what the verify page
calls for cvt 'T'), Categories.marksortgroup / rename_group,
LiftXML.tone_values_by_ps_profile, Settings.generate_status_by_tone_groups,
LiftXML.write, and Transcribe.submitform.

These assert what tone sorting is MEANT to do. A failure is a finding, not
a test to loosen. Where the intended behaviour is my reading of the code
and not something Kent has stated, the test's docstring says "INFERRED".

Headless: no display, no audio, no network. Nothing is written outside
tmp_path.
"""
from types import SimpleNamespace

import pytest

pytest.importorskip('io_put.lift')
pytest.importorskip('backend.core.lexicon')
pytest.importorskip('backend.core.sorting_engine')

import tonefixture as tf  # noqa: E402  (tests/ is on sys.path via conftest)
from tonefixture import ANALANG, GLOSSLANG, sense  # noqa: E402

pytestmark = pytest.mark.integration


@pytest.fixture
def db(tmp_path, monkeypatch):
    return tf.load_lift(tmp_path, monkeypatch)


@pytest.fixture
def program(db):
    return tf.make_program(db)      # Noun / CVCV / Isolation, form lc, cvt T


@pytest.fixture
def work(program):
    return tf.tone_worker(program)


def examples_at(s, loc):
    """The <example> nodes in the XML whose location is `loc`, counted from
    the tree itself rather than from the `examples` dict."""
    return [e for e in s.findall('example')
            if e.findtext('field[@type="location"]/form/text') == loc]


def text(ex):
    return ex.textvaluebylang(ANALANG)


def codes(s, profile):
    return s.verificationtextvalue(profile, 'lc')


# ── Part 0: the fixture itself ───────────────────────────────────────────

def test_fixture_loads_through_the_real_loader(db):
    assert db.analang == ANALANG
    assert ANALANG in db.analangs, "the analysis language must count as valid"
    assert db.glosslangs == [GLOSSLANG]
    assert len(db.entries) == len(tf.WORDS) == 8
    for gloss, (lc, ps, profile, plural) in tf.WORDS.items():
        s = sense(db, gloss)
        assert s.entry.lcvalue() == lc
        assert s.psvalue() == ps
        assert s.cvprofilevalue('lc') == profile, gloss
    assert db.ps_profiles == {'Noun': {'CVCV', 'CVC'},
                              'Verb': {'CVCV', 'CVC'}}


def test_fixture_second_forms_are_entry_fields_found_by_name(db):
    for gloss, (lc, ps, profile, plural) in tf.WORDS.items():
        node = sense(db, gloss).nodebyftype('Plural')
        if plural:
            assert node.textvaluebylang(ANALANG) == plural
        else:
            assert node is None, gloss
    assert sense(db, 'tree').nodebyftype('Pluriel').textvaluebylang(
                                                        ANALANG) == 'basibo'


def test_fixture_presorted_word_reads_back(db):
    house = sense(db, 'house')
    assert house.tonevaluebyframe('Isolation') == '1'
    assert text(house.examples['Isolation']) == 'tama ka'
    assert house.examples['Isolation'].translationvalue(GLOSSLANG) == \
        'the house'
    assert codes(house, 'CVCV') == ['Isolation=1']
    assert db.locations == ['Isolation']


def test_load_stays_in_the_sandbox(db, tmp_path):
    assert str(db.filename).startswith(str(tmp_path))
    assert str(db.audiodir).startswith(str(tmp_path))
    assert str(db.imgdir).startswith(str(tmp_path))
    assert str(db.reportdir).startswith(str(tmp_path))


# ── Part 2a/b: setitemgroup creates, then rewrites, one example ──────────

def test_sorting_a_word_with_no_example_creates_it(db, work):
    kalo = sense(db, 'dog')
    assert 'Isolation' not in kalo.examples
    work.setitemgroup(kalo, 'Isolation', '2')
    ex = kalo.examples['Isolation']
    assert ex.locationvalue() == 'Isolation'
    assert ex.tonevalue() == '2'
    assert list(ex.fields['tone'].forms) == [ANALANG + '-x-tone'], \
        "a sort group is the human tone form, not the _MT one"
    assert text(ex) == 'kalo ka', "the citation form inside the frame"
    assert ex.translationvalue(GLOSSLANG) == 'the dog'
    assert len(examples_at(kalo, 'Isolation')) == 1


def test_resorting_rewrites_the_same_example(db, work):
    kalo = sense(db, 'dog')
    work.setitemgroup(kalo, 'Isolation', '2')
    work.setitemgroup(kalo, 'Isolation', '3')
    assert len(examples_at(kalo, 'Isolation')) == 1, "no second example"
    ex = kalo.examples['Isolation']
    assert ex.tonevalue() == '3'
    assert text(ex) == 'kalo ka'
    assert ex.translationvalue(GLOSSLANG) == 'the dog'


def test_resorting_a_presorted_word_rewrites_its_example(db, work):
    house = sense(db, 'house')
    work.setitemgroup(house, 'Isolation', '2')
    assert len(examples_at(house, 'Isolation')) == 1
    assert house.tonevaluebyframe('Isolation') == '2'
    assert text(house.examples['Isolation']) == 'tama ka'


def test_resorting_refreshes_the_translation_from_the_gloss(db, work):
    """INFERRED. The rewrite branch of Tone.setitemgroup has a loop whose job
    is to rewrite the frame translation (lexicon.py:2671-2677). Its third
    set is `set(item.nodebyftype(ftype) or [])`, the set of a form node's
    CHILD ELEMENTS, which never meets a set of language codes. So the loop
    never runs, and a gloss fixed after the first sort never reaches the
    example."""
    kalo = sense(db, 'dog')
    work.setitemgroup(kalo, 'Isolation', '2')
    kalo.glosses[GLOSSLANG][0].textvalue('hound')
    work.setitemgroup(kalo, 'Isolation', '3')
    assert kalo.examples['Isolation'].translationvalue(GLOSSLANG) == \
        'the hound'


# ── Part 2c: a frame on the Plural field ─────────────────────────────────

def test_possessive_example_uses_the_plural_form(db, work, program):
    assert program.params.ftype() == 'lc', "global form is citation"
    kalo = sense(db, 'dog')
    work.setitemgroup(kalo, 'Possessive', '1')
    ex = kalo.examples['Possessive']
    assert ex.locationvalue() == 'Possessive'
    assert ex.tonevalue() == '1'
    assert text(ex) == 'nde bakalo wa', "the PLURAL form, not 'nde kalo wa'"
    tr = ex.translationvalue(GLOSSLANG)
    assert tr.startswith('my ') and 'dog' in tr
    assert 'Isolation' not in kalo.examples


def test_resorting_possessive_keeps_the_plural_form(db, work):
    kalo = sense(db, 'dog')
    work.setitemgroup(kalo, 'Possessive', '1')
    work.setitemgroup(kalo, 'Possessive', '2')
    assert len(examples_at(kalo, 'Possessive')) == 1
    ex = kalo.examples['Possessive']
    assert ex.tonevalue() == '2'
    assert text(ex) == 'nde bakalo wa'


def test_possessive_reads_its_field_by_name_not_by_code(db, work):
    """'tree' has two plural-like fields. Pointing the app's 'pl' code at
    the other one must not move a frame built on 'Plural'."""
    sibo = sense(db, 'tree')
    assert sibo.set_ftype('pl', 'Pluriel')
    work.setitemgroup(sibo, 'Possessive', '1')
    assert text(sibo.examples['Possessive']) == 'nde misibo wa'
    work.setitemgroup(sibo, 'Possessive', '2')
    assert text(sibo.examples['Possessive']) == 'nde misibo wa'


def test_possessive_on_a_word_without_a_plural_never_uses_the_citation(db,
                                                                      work):
    tob = sense(db, 'stone')
    work.setitemgroup(tob, 'Possessive', '1')
    ex = tob.examples['Possessive']
    assert ex.tonevalue() == '1', "the group is still written"
    assert not text(ex), "no plural to frame, so no analysis text at all"


def test_sorting_one_frame_leaves_the_other_alone(db, work):
    house = sense(db, 'house')
    work.setitemgroup(house, 'Possessive', '2')
    assert house.tonevaluebyframe('Isolation') == '1'
    assert text(house.examples['Isolation']) == 'tama ka'
    assert text(house.examples['Possessive']) == 'nde matama wa'


# ── Part 2d: reading groups back ─────────────────────────────────────────

def ids(senses):
    return {s.id for s in senses}


def test_getitemgroup_and_getsensesingroup_read_back(db, work):
    kalo, sibo, kan = sense(db, 'dog'), sense(db, 'tree'), sense(db, 'eye')
    work.setitemgroup(kalo, 'Isolation', '2')
    work.setitemgroup(sibo, 'Isolation', '2')
    work.setitemgroup(kan, 'Isolation', '2')
    work.setitemgroup(kalo, 'Possessive', '1')
    assert work.getitemgroup(kalo, 'Isolation') == '2'
    assert work.getitemgroup(kalo, 'Possessive') == '1'
    assert work.getitemgroup(sense(db, 'stone'), 'Isolation') is None
    assert ids(work.getsensesingroup('Isolation', '2')) == ids([kalo, sibo,
                                                                kan])
    assert ids(work.getsensesingroup('Isolation', 2)) == ids([kalo, sibo,
                                                              kan])
    assert ids(work.getsensesingroup('Isolation', '1')) == ids(
                                                    [sense(db, 'house')])
    assert ids(work.getsensesingroup('Possessive', '1')) == ids([kalo])


# ── Part 2e: verification, by the path verify uses for cvt 'T' ──────────
# Sort.verify's inner updatestatus() calls status.last('verify') and then
# self.updatestatus(verified=…, writestatus=True); the second is the one that
# writes LIFT, and is what these call. status.last is left out: with no check
# given it walks every check, which needs the full app.

def verify_group(program, work, group, verified=True):
    program.status.group(group)
    return work.updatestatus(verified=verified, writestatus=True)


def sort_isolation_2(db, work, program):
    kalo, sibo, kan = sense(db, 'dog'), sense(db, 'tree'), sense(db, 'eye')
    for s in (kalo, sibo, kan):
        work.setitemgroup(s, 'Isolation', '2')
    program.status.groups(['1', '2'], wsorted=True)
    return kalo, sibo, kan


def test_verifying_a_group_writes_its_code(db, work, program):
    kalo, sibo, kan = sort_isolation_2(db, work, program)
    assert verify_group(program, work, '2')
    assert 'Isolation=2' in codes(kalo, 'CVCV')
    assert 'Isolation=2' in codes(sibo, 'CVCV')
    assert 'CVCV lc verification' in kalo.fields
    assert program.status.verified() == ['2']
    assert 'status' in program.settings.stored
    # out of the slice: kan is CVC
    assert 'Isolation=2' not in codes(kan, 'CVC')
    assert 'Isolation=2' not in codes(kan, 'CVCV')
    # another group's code is left alone
    assert codes(sense(db, 'house'), 'CVCV') == ['Isolation=1']


def test_unverifying_a_group_removes_its_code(db, work, program):
    kalo, sibo, kan = sort_isolation_2(db, work, program)
    verify_group(program, work, '2')
    assert verify_group(program, work, '2', verified=False)
    assert 'Isolation=2' not in codes(kalo, 'CVCV')
    assert 'Isolation=2' not in codes(sibo, 'CVCV')
    assert 'CVCV lc verification' not in kalo.fields, \
        "an emptied verification field is removed"
    assert program.status.verified() == []
    assert codes(sense(db, 'house'), 'CVCV') == ['Isolation=1']


def test_sorting_a_word_into_another_group_unverifies_it(db, work, program):
    """Categories.marksortgroup without updateverification: "unless
    specifically doing otherwise, marking should unverify"."""
    house = sense(db, 'house')
    work.marksortgroup(house, '2', not_sorting=True)
    assert house.tonevaluebyframe('Isolation') == '2'
    assert 'Isolation=1' not in codes(house, 'CVCV')
    assert 'Isolation=2' not in codes(house, 'CVCV')


def test_verifying_a_group_with_no_members_touches_no_word(db, work, program):
    """INFERRED. updatestatuslift (sorting_engine.py:380-403) asks
    slices.inslice(senses) for the group's members in the slice, and
    SliceDict.inslice (analysis.py:609) answers an EMPTY list with the WHOLE
    slice. So verifying a group nobody is in writes '<check>=<group>' on
    every word of the slice (and unverifying one strips every word's code
    for the check)."""
    program.status.groups(['1', '2', '3'], wsorted=True)
    verify_group(program, work, '3')
    for gloss in ('dog', 'house', 'tree'):
        assert 'Isolation=3' not in codes(sense(db, gloss), 'CVCV'), gloss


# ── Part 2f: rebuilding status from LIFT ─────────────────────────────────

def sort_a_few(db, work):
    work.setitemgroup(sense(db, 'dog'), 'Isolation', '2')
    work.setitemgroup(sense(db, 'tree'), 'Isolation', '2')
    work.setitemgroup(sense(db, 'eye'), 'Isolation', '2')
    work.setitemgroup(sense(db, 'dog'), 'Possessive', '1')
    work.setitemgroup(sense(db, 'see'), 'Infinitive', '1')


def test_tone_values_by_ps_profile_returns_written_groups(db, work):
    sort_a_few(db, work)
    t = db.tone_values_by_ps_profile()
    assert t['Noun']['CVCV'] == {'Isolation': {'1', '2'},
                                 'Possessive': {'1'}}
    assert t['Noun']['CVC'] == {'Isolation': {'2'}}
    assert t['Verb']['CVCV'] == {'Infinitive': {'1'}}
    assert t['Verb']['CVC'] == {}


def test_tone_values_can_be_limited_to_one_forms_frames(db, work):
    sort_a_few(db, work)
    t = db.tone_values_by_ps_profile(frames={'Noun': {'Isolation'},
                                             'Verb': {'Infinitive'}})
    assert t['Noun']['CVCV'] == {'Isolation': {'1', '2'}}
    assert t['Verb']['CVCV'] == {'Infinitive': {'1'}}


def status_groups(program, ps, profile, check):
    return program.status.groups(wsorted=True, cvt='T', ps=ps,
                                 profile=profile, check=check)


def test_status_rebuild_files_tone_groups_by_ps_profile_frame(db, work,
                                                              program):
    sort_a_few(db, work)
    list(program.settings.generate_status_by_tone_groups())
    assert status_groups(program, 'Noun', 'CVCV', 'Isolation') == ['1', '2']
    assert status_groups(program, 'Noun', 'CVCV', 'Possessive') == ['1']
    assert status_groups(program, 'Noun', 'CVC', 'Isolation') == ['2']
    assert status_groups(program, 'Verb', 'CVCV', 'Infinitive') == ['1']


def test_tone_status_groups_can_be_renamed_after_a_rebuild(db, work,
                                                           program):
    """generate_status_by_tone_groups (settings/__init__.py:1214) stores the
    SET that tone_values_by_ps_profile builds as the node's 'groups'; the
    annotation rebuild beside it stores a list. StatusDict.renamegroup
    (analysis.py:2109-2110) then calls .append on it, so TranscribeT's
    rename after a status rebuild raises AttributeError."""
    sort_a_few(db, work)
    list(program.settings.generate_status_by_tone_groups())
    k = dict(cvt='T', ps='Noun', profile='CVCV', check='Isolation')
    program.status.renamegroup('2', 'HH', **k)
    assert status_groups(program, 'Noun', 'CVCV', 'Isolation') == ['1', 'HH']


# ── Part 2g: write, reload, same tone data ───────────────────────────────

def test_tone_values_survive_a_write_and_reload(db, work, program):
    kalo, sibo, kan = sort_isolation_2(db, work, program)
    work.setitemgroup(kalo, 'Possessive', '1')
    work.setitemgroup(sense(db, 'see'), 'Infinitive', '1')
    verify_group(program, work, '2')
    db.write()
    assert db.write_OK, getattr(db, 'write_error', None)
    db2 = tf.reload_lift(db)
    for gloss in tf.WORDS:
        s1, s2 = sense(db, gloss), sense(db2, gloss)
        assert s2.tonevaluedict() == s1.tonevaluedict(), gloss
        for loc, ex1 in s1.examples.items():
            ex2 = s2.examples[loc]
            assert text(ex2) == text(ex1), (gloss, loc)
            assert ex2.translationvalue(GLOSSLANG) == \
                ex1.translationvalue(GLOSSLANG), (gloss, loc)
            assert ex2.locationvalue() == loc
        for profile in ('CVCV', 'CVC'):
            assert codes(s2, profile) == codes(s1, profile), (gloss, profile)
    k2 = sense(db2, 'dog')
    assert k2.tonevaluedict() == {'Isolation': '2', 'Possessive': '1'}
    assert text(k2.examples['Possessive']) == 'nde bakalo wa'
    assert 'Isolation=2' in codes(k2, 'CVCV')
    assert set(db2.locations) == {'Isolation', 'Possessive', 'Infinitive'}


# ── Part 3: transcription renames a surface group ────────────────────────

def sorted_and_verified(db, work, program):
    """Noun CVCV Isolation: '1' = dog + house (verified), '2' = tree (not
    verified). Outside that: eye (CVC) is Isolation '1', and dog is also
    Possessive '1'."""
    kalo, tama = sense(db, 'dog'), sense(db, 'house')
    sibo, kan = sense(db, 'tree'), sense(db, 'eye')
    work.setitemgroup(kalo, 'Isolation', '1')
    work.setitemgroup(sibo, 'Isolation', '2')
    work.setitemgroup(kan, 'Isolation', '1')
    work.setitemgroup(kalo, 'Possessive', '1')
    program.status.groups(['1', '2'], wsorted=True)
    verify_group(program, work, '1')
    assert 'Isolation=1' in codes(kalo, 'CVCV')      # preconditions
    assert program.status.verified() == ['1']
    return kalo, tama, sibo, kan


def test_rename_group_rewrites_that_frames_tone_values(db, work, program):
    kalo, tama, sibo, kan = sorted_and_verified(db, work, program)
    work.rename_group('1', 'HH')
    assert kalo.tonevaluebyframe('Isolation') == 'HH'
    assert tama.tonevaluebyframe('Isolation') == 'HH'
    assert text(kalo.examples['Isolation']) == 'kalo ka'
    assert len(examples_at(kalo, 'Isolation')) == 1


def test_rename_group_leaves_other_frames_groups_and_slices(db, work,
                                                            program):
    kalo, tama, sibo, kan = sorted_and_verified(db, work, program)
    work.rename_group('1', 'HH')
    assert kalo.tonevaluebyframe('Possessive') == '1', "another frame"
    assert sibo.tonevaluebyframe('Isolation') == '2', "another group"
    assert kan.tonevaluebyframe('Isolation') == '1', "another profile"


def test_rename_group_rewrites_verification_codes(db, work, program):
    kalo, tama, sibo, kan = sorted_and_verified(db, work, program)
    work.rename_group('1', 'HH')
    for s in (kalo, tama):
        assert 'Isolation=HH' in codes(s, 'CVCV'), s.id
        assert 'Isolation=1' not in codes(s, 'CVCV'), s.id


def test_rename_group_updates_status(db, work, program):
    kalo, tama, sibo, kan = sorted_and_verified(db, work, program)
    work.rename_group('1', 'HH')
    groups = status_groups(program, 'Noun', 'CVCV', 'Isolation')
    assert 'HH' in groups and '1' not in groups


def test_rename_group_keeps_the_group_verified_in_status(db, work, program):
    """categories.py:236-243: rename_group runs reloadstatusdata_cleanup
    (cull: done = done & groups, analysis.py:1861-1863) BEFORE
    rename_group_verification. After the reload the groups hold 'HH', so
    cull drops '1' from done, and the rename then finds no '1' to rename.
    The renamed group comes out unverified in status, though its words
    carry 'Isolation=HH' in LIFT."""
    sorted_and_verified(db, work, program)
    work.rename_group('1', 'HH')
    assert program.status.verified() == ['HH']


def test_renaming_an_unverified_group_does_not_verify_it(db, work, program):
    """INFERRED. updatebygroupsense marks every member with
    updateverification=True (categories.py:264-270), and marksortgroup sets
    noconfirmation=True (:119), so renaming a group that was never verified
    writes '<check>=<new>' codes on all its words."""
    kalo, tama, sibo, kan = sorted_and_verified(db, work, program)
    assert 'Isolation=2' not in codes(sibo, 'CVCV')      # precondition
    work.rename_group('2', 'LL')
    assert sibo.tonevaluebyframe('Isolation') == 'LL'
    assert 'Isolation=LL' not in codes(sibo, 'CVCV')


def test_transcribe_tone_submit_renames_the_group_in_lift(db, work, program):
    """The TranscribeT OK button: Transcribe.submitform (tasks.py:1791).
    It calls self.updatebygroupsense(...) at tasks.py:1800 and drops the
    result. updatebygroupsense is a GENERATOR (categories.py:251, it
    yields), so dropping it runs none of it: no example changes, and only
    the status file is renamed."""
    tasks = pytest.importorskip('tasks.tasks')
    kalo, tama, sibo, kan = sorted_and_verified(db, work, program)
    quit_calls = []
    work.group = '1'
    work.transcriber = SimpleNamespace(
                        formfield=SimpleNamespace(get=lambda: 'HH'))
    work.updategroups = lambda: 1
    work.ui = SimpleNamespace(runwindow=SimpleNamespace(
                                    on_quit=lambda: quit_calls.append(1)))
    tasks.Transcribe.submitform(work)
    assert quit_calls, "submitform ran to the end"
    assert 'HH' in status_groups(program, 'Noun', 'CVCV', 'Isolation')
    assert kalo.tonevaluebyframe('Isolation') == 'HH'
    assert tama.tonevaluebyframe('Isolation') == 'HH'
    assert 'Isolation=HH' in codes(kalo, 'CVCV')
    assert kalo.tonevaluebyframe('Possessive') == '1'
    assert kan.tonevaluebyframe('Isolation') == '1'
