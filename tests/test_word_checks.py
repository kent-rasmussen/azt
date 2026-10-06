"""Word checks: WHICH FORM of the word a whole-word task works on.

A WORD CHECK IS NOT A CVT CHECK. Kent, 2026-09-29: "these are **word**
checks, not cvt checks." A cvt check picks segments WITHIN a form (the first
vowel, the tone frame); a word check picks the form — `lc`, `lx`, and
`pl`/`imp` where their field is named. They are independent: you sort the
first vowel OF the citation form.

These replaced a CLASS PER FORM (`WordCollectionLexeme`,
`WordCollectionCitation`, `WordCollectionPlural`, `WordCollectionImperative`),
none of which the chooser offered. Plan 2 of the second-form flags audit.

Exercised with a stand-in `self` rather than a live app, which is the suite's
idiom for `backend/core` (see `test_second_form_field_placeholder.py`).
"""
import types

import pytest

from backend.core import analysis_inputs


UNSET = '<unset>'


def _params(fields=None, ftype='lc'):
    """A stand-in carrying only what the word-check methods touch."""
    fields = dict(fields or {})

    def secondformfieldset(ps):
        if not ps or ps not in fields:
            return False
        return str(fields[ps]).strip() not in ('', UNSET)

    settings = types.SimpleNamespace(nominalps='Noun', verbalps='Verb',
                                     secondformfield=fields,
                                     secondformfieldset=secondformfieldset)
    ns = types.SimpleNamespace(program=types.SimpleNamespace(settings=settings),
                               _ftype=ftype)
    for name in ('ftype', 'secondfield', 'second_forms_available',
                 'word_checks', 'resolve_word_check', 'word_check_name',
                 'second_form_checks'):
        setattr(ns, name,
                getattr(analysis_inputs.CheckParameters, name).__get__(ns))
    return ns


def _codes(params):
    return [code for code, name in params.word_checks()]


# ── which checks exist ───────────────────────────────────────────────────

def test_citation_and_root_are_always_offered():
    """Neither depends on a field the user has to name, so a project that
    has defined nothing still has two forms to choose between."""
    assert _codes(_params()) == ['lc', 'lx']


def test_a_second_form_appears_once_its_field_is_named():
    """Kent, 2026-09-29: a user should be able to "define a second form
    field, then immediately select the check for it".

    Withheld for part of that day, because naming the field was NOT
    sufficient: nothing ever pointed a sense's `pl` at it, so every
    ftype-keyed read returned None and a plural page showed every word as
    uncollected forever. `Sense.set_ftype` closed that; the field being
    named is the only condition again."""
    assert 'pl' not in _codes(_params())
    assert 'pl' in _codes(_params({'Noun': 'Plural'}))
    assert 'imp' in _codes(_params({'Verb': 'Imperative'}))


def test_the_placeholder_does_not_count_as_a_named_field():
    """`<unset>` reached `project.json` once and read as a defined value to
    every guard that tested presence — including, now, the one that decides
    whether to register an ftype against a LIFT field of that name."""
    assert 'pl' not in _codes(_params({'Noun': UNSET}))
    assert 'imp' not in _codes(_params({'Verb': ' '}))


def test_the_name_follows_the_field():
    names = dict(_params({'Noun': 'Pluriel'}).word_checks())
    assert 'Pluriel' in names['pl'], names['pl']


def test_the_code_does_not_follow_the_field():
    """Stored verification codes key on the CODE, so a rename must not touch
    it — that is what makes renaming safe."""
    assert 'pl' in _codes(_params({'Noun': 'Pluriel'}))


def test_word_checks_and_syllable_checks_agree_on_availability():
    """Two lines ask the same question — the syllable sort's check list and
    the word-check line — and one offering a form the other does not is a
    choice that does nothing. Both go through `second_forms_available`."""
    for fields in ({}, {'Noun': 'Plural'}, {'Noun': 'Plural', 'Verb': 'Imp'}):
        p = _params(fields)
        assert ([c for c, n in p.second_form_checks()]
                == [c for c in _codes(p) if c in ('pl', 'imp')]), fields


# ── resolving one ────────────────────────────────────────────────────────

def test_an_unavailable_form_falls_back_to_citation():
    """Kent, 2026-09-29: "we cannot collect without a field name." The ftype
    is written by callers that never consult the check list — a stored
    verification code, another task — so it can name a form no page can
    work on."""
    assert _params(ftype='pl').resolve_word_check() == 'lc'


def test_an_available_form_is_left_alone():
    assert _params(ftype='lx').resolve_word_check() == 'lx'
    assert _params({'Noun': 'Plural'}, ftype='pl').resolve_word_check() == 'pl'


def test_the_label_never_shows_a_bare_code():
    """A page reading "collecting pl" is useless (Kent). It must name the
    form the page will ACTUALLY work on."""
    name = _params(ftype='pl').word_check_name()
    assert name != 'pl'
    assert name == dict(_params().word_checks())['lc']


# ── the classes this replaced ────────────────────────────────────────────

@pytest.mark.parametrize('name', ['WordCollectionLexeme',
                                  'WordCollectionCitation',
                                  'WordCollectionPlural',
                                  'WordCollectionImperative',
                                  '_WordCollectionSecondForm'])
def test_the_class_per_form_is_gone(name):
    """Each hard-coded one ftype before `super().__init__`, and the chooser
    offered none of them. The form is a choice on the page now."""
    tasks = pytest.importorskip('tasks.tasks')
    assert not hasattr(tasks, name), \
        '{} came back; the form is a word check, not a class'.format(name)


# ── the ftype table that makes pl/imp readable ───────────────────────────

class _FakeEntry:
    def __init__(self, fields):
        self.fields = dict(fields)
        self.lx, self.lc = object(), object()


def _sense(fields):
    """A stand-in carrying only what `set_ftype` touches."""
    from io_put import lift
    ns = types.SimpleNamespace(entry=_FakeEntry(fields),
                               ftypes={'lx': 1, 'lc': 2})
    ns.set_ftype = lift.Sense.set_ftype.__get__(ns)
    return ns


def test_set_ftype_points_a_code_at_a_named_field():
    s = _sense({'Plural': 'the-plural-field'})
    assert s.set_ftype('pl', 'Plural') is True
    assert s.ftypes['pl'] == 'the-plural-field'


def test_set_ftype_leaves_the_code_unset_when_the_entry_has_no_such_field():
    """The honest answer for an entry nobody has given a plural: absent, so
    `textvaluebyftypelang` returns None and the word reads as uncollected —
    which it is."""
    s = _sense({})
    assert s.set_ftype('pl', 'Plural') is False
    assert 'pl' not in s.ftypes


def test_set_ftype_repoints_on_rename_rather_than_accumulating():
    """A renamed field must not leave `pl` resolving to the one the user
    abandoned."""
    s = _sense({'Plural': 'old', 'Pluriel': 'new'})
    s.set_ftype('pl', 'Plural')
    s.set_ftype('pl', 'Pluriel')
    assert s.ftypes['pl'] == 'new'


def test_set_ftype_clears_the_code_when_the_name_goes_away():
    s = _sense({'Plural': 'old'})
    s.set_ftype('pl', 'Plural')
    assert s.set_ftype('pl', None) is False
    assert 'pl' not in s.ftypes


def test_lx_and_lc_are_lifts_own_and_are_not_disturbed():
    s = _sense({'Plural': 'x'})
    s.set_ftype('pl', 'Plural')
    assert s.ftypes['lx'] == 1 and s.ftypes['lc'] == 2


def test_the_registration_pass_exists_and_is_settings_side():
    """lift.py is TOLD the mapping, never derives it — so the pass belongs
    to the layer that knows what the setting means."""
    from settings import Settings
    assert hasattr(Settings, 'register_second_forms')


def test_the_collection_page_can_reload_without_rebuilding_its_frames():
    """Changing the word check shows a different set of words in the SAME
    widgets. `getwords` grids a new `wordsframe` on every call, so the
    reloadable half had to be split out."""
    from backend.core import lexicon
    assert hasattr(lexicon.WordCollection, 'loadwords')


# ── one owner for ftype ──────────────────────────────────────────────────

def test_nothing_in_the_task_layer_has_an_ftype_attribute():
    """Kent, 2026-09-29: "drop self.ftype and read params.ftype()
    everywhere." Not a property standing in for it either — a task-side
    `self.ftype` keeps the app's setting looking like the value you hand to
    `lift.py`, whose `ftype` is a different thing sharing the name, and that
    resemblance is what hid the `sense.ftypes` gap."""
    from tasks import base
    from backend.core import alphabet
    assert 'ftype' not in base.TaskBase.__dict__
    assert 'ftype' not in base.Task.__dict__
    # Not a task — a service object on `program.alphabet`, built once per
    # project, so its copy was the longest-lived of them all.
    assert 'ftype' not in alphabet.Alphabet.__dict__


def test_the_declared_form_defaults_to_citation():
    """`works_on_ftype` on TaskBase, overridden where necessary — Kent's
    call, and nothing overrides it today."""
    from tasks import base
    assert base.TaskBase.works_on_ftype == 'lc'


TASK_LAYER = ('tasks/base.py', 'tasks/tasks.py', 'tasks/chooser.py',
              'tasks/sound.py', 'tasks/alphabet_chart.py',
              'backend/core/lexicon.py', 'backend/core/categories.py',
              'backend/core/sorting_engine.py', 'backend/core/alphabet.py')


def test_no_task_layer_code_says_self_ftype():
    """THE SECOND COPY MUST NOT COME BACK — neither written nor read.

    It was set in six constructors and re-copied in four more, and
    `categories.py` carried an ErrorNotice for when the two disagreed. Reads
    are scanned as well as writes, because a read is how a copy gets
    reintroduced: `self.ftype` only means anything if something assigned it.

    `io_put/lift.py` and `backend/core/analysis.py` are NOT scanned: their
    `self.ftype` is a different thing sharing the name — a LIFT node's
    `type` string, and `SyllableSliceDict`'s key, set from its own
    constructor argument — and both are legitimately their own."""
    import pathlib
    import re
    root = pathlib.Path(__file__).resolve().parent.parent
    pattern = re.compile(r'\bself\.ftype\b')
    offenders = []
    for rel in TASK_LAYER:
        path = root / rel
        if not path.exists():
            continue
        for n, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
            code = line.split('#', 1)[0]
            if pattern.search(code):
                offenders.append('{}:{}: {}'.format(rel, n, line.strip()))
    assert not offenders, (
        'the word form has one owner, params.ftype(); these keep a copy:\n  '
        + '\n  '.join(offenders))


def test_the_collection_page_declares_the_flag_and_a_verb():
    from backend.core import lexicon
    assert lexicon.WordCollection.whole_word_checks is True
    assert lexicon.WordCollection.word_check_prefix


def test_parse_does_not_offer_a_word_check():
    """PARSE PINS `lc`, so a chooser there offers what it will ignore.

    The combos take `WordCollection` too — which sets the flag True — and
    `Parse` precedes it in every MRO, so this has to be declared rather
    than merely absent. Kent, 2026-09-29, seeing the miss: "collecting
    citation forms" appeared on **Parse Already Collected Words**.

    The FIELD line is a different question and Parse keeps it, through
    `uses_second_forms`."""
    from backend.core import lexicon
    from tasks import tasks
    assert lexicon.Parse.whole_word_checks is False
    assert lexicon.Parse.uses_second_forms is True
    for name in ('WordsParse', 'WordCollectnParse',
                 'WordCollectnParsewRecordings'):
        cls = getattr(tasks, name)
        assert cls.whole_word_checks is False, name
        assert cls.uses_second_forms is True, name
    # The plain collection task is the one that DOES offer it.
    assert tasks.WordCollectionCitationwRecordings.whole_word_checks is True


def test_recording_is_a_word_check_page_and_not_a_cvt_one():
    """Kent, 2026-09-29: the record page "is, by definition, a word check
    page". You record a whole word FORM, never a segment within one.

    And the cvt line it used to draw did no work:
    `showentryformstorecordpage` reads ps, profile, count and
    `slices.senses(ps=,profile=)`, and never `params.check()`. The slice
    line stays, since ps and profile are what it does read."""
    from tasks import tasks
    assert tasks.RecordCitation.whole_word_checks is True
    assert tasks.RecordCitation.do_not_show_cvt is True
    assert tasks.RecordCitation.do_not_show_slices is False
    # Tone recording is NOT the same case: it records into tone frames, and
    # a tone frame IS the check.
    assert tasks.RecordCitationT.do_not_show_cvt is False


def test_only_word_collection_draws_its_own_chooser():
    """THREE WORD-CHECK PAGES, ONE CHOOSER — the flag says which.

    Word collection has no slice line and no check line
    (`do_not_show_slices`), so the word-check line is its only way to pick
    a form. The syllable sort picks it on the SLICE line, beside the
    profile class — its check line states the check and does not offer one
    (the check IS the form). The record page shows a button per form and
    needs no mode (Kent, 2026-09-29)."""
    from backend.core import lexicon
    from tasks import tasks
    assert lexicon.WordCollection.offers_word_check_line is True
    # Through the concrete tasks for these two: `Syllables` is a backend
    # mixin and never sees TaskBase's defaults on its own.
    assert tasks.SortSyllables.offers_word_check_line is False
    assert tasks.RecordCitation.offers_word_check_line is False
    # All three are still word-check pages.
    for cls in (lexicon.WordCollection, tasks.SortSyllables,
                tasks.RecordCitation):
        assert cls.whole_word_checks is True, cls


def test_the_reloading_pages_answer_to_one_name():
    """A form change reaches the page through `reload_for_word_check`, and
    the implementations differ — a word list; profile slices and a board;
    `(ps, ftype)` slices, prep state and a board.

    EVERY SORT HAS ONE, not just the syllable sort: the vowels of a
    citation form are not the vowels of a plural, and the profile slices
    are ftype-derived. Kent, 2026-09-30, when I offered a choice between
    giving segmental sorts a reload and showing them no form: "that's a
    false choice, but let's give SortV a reload"."""
    from backend.core import lexicon, sorting_engine
    from tasks import tasks
    assert hasattr(lexicon.WordCollection, 'reload_for_word_check')
    assert hasattr(sorting_engine.Sort, 'reload_for_word_check')
    for name in ('SortV', 'SortC', 'SortSyllables'):
        assert hasattr(getattr(tasks, name), 'reload_for_word_check'), name
    # The syllable sort keeps its own, larger version.
    assert (tasks.SortSyllables.reload_for_word_check
            is not sorting_engine.Sort.reload_for_word_check)
    # The record page has no reload, which is consistent with offering no
    # choice to act on.
    assert not hasattr(tasks.RecordCitation, 'reload_for_word_check')


def test_an_empty_delimiter_builds_no_widget():
    """`delimit=('', ',')` — a comma tight after the value and nothing
    before it — used to build an EMPTY label and give it a grid column,
    and an empty cell is not a zero-width one (Kent, 2026-09-30: "I'm
    still seeing extra space around the cvt label")."""
    import inspect
    from frontend import composites
    src = inspect.getsource(composites.ClickToEdit.__init__)
    assert 'if delimit and delimit[0]:' in src
    assert 'if delimit and delimit[1]:' in src


def test_the_syllable_check_is_the_current_form():
    """DIRECTION IS ftype → check, and the check CODE is the ftype.

    Plan 6 briefly inverted this so the check line could choose the form.
    Reverted 2026-09-30, once the scope came out right: the form is
    slice-scope and is chosen beside the profile class, and the check
    follows it.

    The code must STAY the ftype. LIFT stores the verification as
    `<check>=<group>` with the ftype as the check —
    `<field type="C_1_V lc verification">` holding `['lc=CV']`, from Kent's
    own file — so a separate stage-2 code would orphan every existing
    one."""
    import inspect
    from backend.core import analysis
    src = inspect.getsource(analysis.StatusDict.updatechecksbycvt)
    assert '[self.program.params.ftype()]' in src
    assert 'word_checks()' not in src


def test_changing_the_form_realigns_the_check():
    """Kent, 2026-09-30: "this means we'll need a makecheckOK, since the
    check will need to align with the ftype, should it ever change."

    `makecheckok` already is that — `checks()` for 'S' is `[ftype()]`, so a
    changed form invalidates the standing check and it picks the only valid
    one. It must run BEFORE the reload, or the page rebuilds against the
    old check; and it chains into `makegroupok`, so one call settles
    ftype → check → group.

    ON THE COMMENT STRIPPING: the branch opens with a fifteen-line comment
    that NAMES `reload_for_word_check` while explaining why the check has to
    be settled first. Reading the raw source, this test found that mention
    at offset 497 and the real `makecheckok()` call at 1702, and failed a
    correctly-ordered branch."""
    from sourcescan import code
    from settings import Settings
    branch = code(Settings.refreshattributechanges).split(
                        "'ftype' in self.attrschanged")[1]
    branch = branch.split("attrschanged.remove('ftype')")[0]
    assert 'makecheckok()' in branch
    assert branch.index('makecheckok()') < branch.index('reload_for_word_check')


def test_the_form_names_are_adjectival():
    """Two lines show them and each supplies its own noun: "Collecting
    Citation forms", "Looking at Citation C1C words"."""
    names = dict(_params().word_checks())
    assert names['lc'] == 'Citation'
    assert names['lx'] == 'Root'


def test_each_syllable_check_is_named_for_itself():
    """Kent, 2026-09-29, on the new chooser: "I see whole citation twice?"

    `cvcheckname` overwrote its `code` argument with `ftype()` for cvt 'S',
    so the option list — built as `[(c, cvcheckname(c)) for c in checks]`
    (`ui_shell.py:3222`) — named every option after the CURRENT form. One
    entry in the list hid it; a chooser does not."""
    names = {}
    p = _params({'Noun': 'Plural'}, ftype='lc')
    p.cvt = lambda: 'σ'
    for attr in ('cvcheckname', 'is_syllable_primitive_check',
                 'syllable_check_name', 'check'):
        setattr(p, attr,
                getattr(analysis_inputs.CheckParameters, attr).__get__(p))
    p._check = 'lc'
    p._cvchecknames = {'lc': 'Whole Citation Word Syllable Profile',
                       'lx': 'Whole Root Syllable Profile',
                       'pl': 'Whole Plural Word Syllable Profile'}
    for code in ('lc', 'lx', 'pl'):
        names[code] = p.cvcheckname(code)
    assert len(set(names.values())) == 3, names
    assert names['lx'] == 'Whole Root Syllable Profile'
    # No code given still means "the current form", which is what the
    # status line asks for.
    assert p.cvcheckname() == 'Whole Citation Word Syllable Profile'


def test_a_prep_primitive_is_still_named_for_itself():
    """The other half of the same method: #C/C#/syls share one ftype, so
    they are named by the primitive rather than the form."""
    p = _params(ftype='lc')
    p.cvt = lambda: 'σ'
    for attr in ('cvcheckname', 'is_syllable_primitive_check',
                 'syllable_check_name', 'check'):
        setattr(p, attr,
                getattr(analysis_inputs.CheckParameters, attr).__get__(p))
    p._check = '#C'
    p._cvchecknames = {}
    assert p.cvcheckname('#C') == 'word-initial sounds'
    assert p.cvcheckname('syls') == 'syllable counts'


def test_the_prep_handoff_aligns_the_check_with_the_form():
    """Unconditional, and that IS the direction: for cvt 'S' the check is
    the current form, so aligning them on the way out of prep honours the
    choice made on the slice line rather than overwriting one."""
    import inspect
    from backend.core import sorting_engine
    src = inspect.getsource(sorting_engine.SyllablePrep.runcheck)
    assert 'params.check(self.program.params.ftype())' in src
    assert 'is_word_check()' not in src
