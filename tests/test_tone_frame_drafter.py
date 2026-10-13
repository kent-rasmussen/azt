# coding=UTF-8
"""Tone frame drafting (tasks/tasks.py ToneFrameDrafter) — intended behaviour.

A tone frame is a permanent definition: once submitted its NAME is its code
and its FIELD decides which form every sort on it reads. So what the drafter
writes is tested rather than trusted:

  * which fields are offered, and that the stored value is the field's CODE
    or FIELD NAME ('lc', 'Plural'), never the label a user picked;
  * that changing the field re-keys the analysis-language row
    ('<analang>_<field>');
  * the word-break box, through the real commit path;
  * the definition `exemplified` builds and hands to `submit`, and its
    empty-name gate;
  * the rendered example — through the same calls the drafter makes, on
    REAL `io_put.lift` nodes — for a citation frame and a plural-field frame
    (the plural one crashed with AttributeError before the 2026-10-13
    `nodebyftype` fix);
  * `ToneFrames.addframe` storage and its duplicate refusal, and
    `ToneFrames.source` defaulting a field-less frame to 'lc'.

HOW, HEADLESS. The drafter is a ui.Window. Its own methods (every name in
`ToneFrameDrafter.__dict__`) are copied onto a plain class, so they are the
real methods but no window machinery of either backend is involved; and the
module's `ui` is swapped for a recording fake, so the real `status()` /
`editable()` / `exemplified()` run and build "widgets" that are only records
of their keyword arguments. That lets the tests drive the page the way a user
does (the field-type dropdown's own `command`, the "Use … tone frame"
button's own `command`) without a display.

Not covered here (needs a display or a live app): geometry, reflow timing,
focus, rendering of the analysis font, and the real backends' widgets.
The `ui.StringVar(value=…)` keyword guard and the "{name}-{ps}" proposal
have their own files (test_ui_vars_take_value_by_keyword.py,
test_frame_name_suffix.py) and are not duplicated.
"""
import xml.etree.ElementTree as ET
from types import SimpleNamespace

import pytest

tasks = pytest.importorskip('tasks.tasks')
lift = pytest.importorskip('io_put.lift')
analysis_inputs = pytest.importorskip('backend.core.analysis_inputs')
TFD = tasks.ToneFrameDrafter
ToneFrames = analysis_inputs.ToneFrames

ANALANG = 'xyz'


# ── a recording stand-in for `frontend.ui` ────────────────────────────────

class _Var:
    """StringVar/BooleanVar stand-in. Accepts tkinter's (master, value) and
    the keyword form; the keyword guard lives in its own test file."""

    def __init__(self, master=None, value=None, name=None):
        self._v = value

    def get(self):
        return self._v

    def set(self, v):
        self._v = v


class _Root:
    def after_idle(self, *a, **k):
        pass

    def after(self, *a, **k):
        pass


@pytest.fixture
def ui(monkeypatch):
    created = []

    class Widget:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.opts = dict(kwargs)
            self.destroyed = False
            created.append(self)

        def __setitem__(self, k, v):
            self.opts[k] = v

        def __getitem__(self, k):
            return self.opts.get(k)

        def destroy(self):
            self.destroyed = True

        def __getattr__(self, name):  # grid, grid_remove, bind, wrap, …
            if name.startswith('__'):
                raise AttributeError(name)
            return lambda *a, **k: None

    fake = SimpleNamespace(
        created=created,
        Frame=Widget, Label=Widget, Button=Widget, ToolTip=Widget,
        Combobox=Widget, EntryField=Widget, CheckButton=Widget,
        ScrollingFrame=Widget,
        StringVar=_Var, BooleanVar=_Var,
        LEFT='left',
        default_root=lambda: _Root(),
    )
    monkeypatch.setattr(tasks, 'ui', fake)
    return fake


# ── the drafter, real methods, no window ──────────────────────────────────

Drafter = type('Drafter', (), {k: v for k, v in vars(TFD).items()
                               if not k.startswith('__')})


def make_program(frames=None, senses=None, ps='Noun', pluralname='Plural',
                 imperativename='Imperative'):
    settings = SimpleNamespace(
        nominalps='Noun', verbalps='Verb',
        pluralname=pluralname, imperativename=imperativename,
        glosslangs=['en'],
        languagenames={ANALANG: 'Xyzish', 'en': 'English', 'fr': 'French'},
        stored=[], checks=[])
    settings.storesettingsfile = (
        lambda setting=None: settings.stored.append(setting))
    settings.setcheck = lambda c: settings.checks.append(c)
    senses = senses or []
    prog = SimpleNamespace(
        settings=settings,
        params=SimpleNamespace(ftype=lambda: 'lc'),
        db=SimpleNamespace(glosslangs=['en', 'fr'],
                           sensesbyps={ps: senses}, nsenses=len(senses)),
        status=SimpleNamespace(renewchecks=lambda: None))
    ToneFrames(prog, frames)          # sets prog.toneframes
    return prog


def make_drafter(ps='Noun', field='lc', program=None, build=True):
    d = Drafter()
    d.program = program or make_program(ps=ps)
    d.task = SimpleNamespace(deiconify=lambda: None)
    d.analang = ANALANG
    d.ps = ps
    d.forms = {'field': field} if field is not None else {}
    d.glosslangs = []
    d.exitFlag = SimpleNamespace(istrue=lambda: False)
    d.content = object()
    d.scroll = SimpleNamespace(reflow=lambda: None, tobottom=lambda: None)
    d.active = None
    d.fields = {}
    d.destroyed = False
    d.destroy = lambda: setattr(d, 'destroyed', True)
    if build:
        d.status()
    return d


def label_for(d, code):
    return dict(d.fieldtypes())[code]


# ── real LIFT nodes ───────────────────────────────────────────────────────

class _Host(ET.Element):
    """An element parent carrying what lift's Node/FormParent read off it."""


def _host():
    h = _Host('sense')
    h.db = SimpleNamespace(analang=ANALANG)
    h.annotationlang = 'en'
    return h


def _wrap(cls, host, xml):
    raw = ET.fromstring(xml)
    host.append(raw)          # Node.__init__ swaps itself in for `raw`
    return cls(host, raw)


def _formxml(tag, text, type_=None):
    t = ' type="{}"'.format(type_) if type_ else ''
    return ('<{tag}{t}><form lang="{l}"><text>{x}</text></form></{tag}>'
            .format(tag=tag, t=t, l=ANALANG, x=text))


def make_sense(sid='s1', lc='bana', plural='babana', plural2='bibana',
               gloss_en='child', gloss_fr='enfant'):
    """A real lift.Sense (no __init__) over real Citation/Field/Gloss nodes.

    Two plural fields, 'Plural' and 'Plural2', with 'Plural' the one the
    app's `pl` code points at — the case Kent named: a frame on one plural
    must never pick up the other."""
    h = _host()
    lc_node = _wrap(lift.Citation, h, _formxml('citation', lc))
    fields = {}
    if plural:
        fields['Plural'] = _wrap(lift.Field, h,
                                 _formxml('field', plural, 'Plural'))
    if plural2:
        fields['Plural2'] = _wrap(lift.Field, h,
                                  _formxml('field', plural2, 'Plural2'))
    s = lift.Sense.__new__(lift.Sense)
    s.id = sid
    s.ftypes = {'lc': lc_node}
    if plural:
        s.ftypes['pl'] = fields['Plural']
    s.entry = SimpleNamespace(fields=fields)
    s.glosses = {
        'en': [_wrap(lift.Gloss, h,
                     '<gloss lang="en"><text>{}</text></gloss>'.format(gloss_en))],
        'fr': [_wrap(lift.Gloss, h,
                     '<gloss lang="fr"><text>{}</text></gloss>'.format(gloss_fr))],
    }
    return s


def test_the_real_nodes_are_what_they_claim():
    """Sanity check of the fixture itself, so a failure below is about the
    drafter and not about how these nodes were built."""
    s = make_sense()
    assert s.ftypes['lc'].ftype == 'lc'
    assert s.ftypes['lc'].textvaluebylang(ANALANG) == 'bana'
    assert s.entry.fields['Plural'].ftype == 'Plural'
    assert s.entry.fields['Plural'].textvaluebylang(ANALANG) == 'babana'
    assert s.glosses['en'][0].textvalue() == 'child'


# ── 1. which fields are offered ───────────────────────────────────────────

def test_citation_and_lexeme_are_always_offered():
    for ps in ('Noun', 'Verb', 'Adjective'):
        d = make_drafter(ps=ps, build=False)
        codes = [c for c, _l in d.fieldtypes()]
        assert codes[:2] == ['lc', 'lx'], ps


def test_the_plural_field_is_offered_by_its_field_name_for_the_nominal_ps():
    d = make_drafter(ps='Noun', build=False)
    codes = [c for c, _l in d.fieldtypes()]
    assert 'Plural' in codes, "the plural field, by its FIELD NAME"
    assert 'pl' not in codes, "never the 'pl' code"
    assert 'Imperative' not in codes, "no imperative on the nominal ps"


def test_the_imperative_field_is_offered_only_for_the_verbal_ps():
    d = make_drafter(ps='Verb', build=False)
    codes = [c for c, _l in d.fieldtypes()]
    assert 'Imperative' in codes
    assert 'imp' not in codes
    assert 'Plural' not in codes, "no plural on the verbal ps"


def test_no_second_form_on_any_other_ps():
    d = make_drafter(ps='Adjective', build=False)
    assert [c for c, _l in d.fieldtypes()] == ['lc', 'lx']


@pytest.mark.parametrize('ps', ['Noun', 'Verb'])
def test_nothing_is_offered_for_an_unset_second_form_field(ps):
    prog = make_program(ps=ps, pluralname=None, imperativename=None)
    d = make_drafter(ps=ps, program=prog, build=False)
    codes = [c for c, _l in d.fieldtypes()]
    assert codes == ['lc', 'lx']
    assert None not in codes


def test_the_dropdown_offers_exactly_the_labels_of_those_fields(ui):
    d = make_drafter(ps='Noun')
    combos = [w for w in ui.created if 'optionlist' in w.opts]
    assert combos, "the field-type control was not built"
    assert combos[-1].opts['optionlist'] == [l for _c, l in d.fieldtypes()]


# ── 2. a picked LABEL is stored as its CODE / field name ──────────────────

def test_picking_a_label_stores_the_code_never_the_label(ui):
    d = make_drafter(ps='Noun')
    label = label_for(d, 'Plural')
    d._pick_fieldtype(('field', None), label)
    assert d.forms['field'] == 'Plural'
    assert d.forms['field'] != label
    assert d.analangftypecode() == 'xyz_Plural'


def test_picking_through_the_dropdowns_own_command(ui):
    """Drive the control the way a user does: set its variable, fire its
    command."""
    d = make_drafter(ps='Noun')
    combo = [w for w in ui.created if 'optionlist' in w.opts][-1]
    combo.opts['textvariable'].set(label_for(d, 'lx'))
    combo.opts['command']()
    assert d.forms['field'] == 'lx'


def test_an_unknown_label_stores_nothing(ui):
    d = make_drafter(ps='Noun')
    d._pick_fieldtype(('field', None), 'No such form')
    assert d.forms['field'] == 'lc'


def test_a_code_is_not_a_label(ui):
    """The dropdown deals in labels; a raw code arriving as the pick ('lx')
    matches no label and must store nothing."""
    d = make_drafter(ps='Noun')
    d._pick_fieldtype(('field', None), 'lx')
    assert d.forms['field'] == 'lc'


def test_the_button_shows_the_label_for_the_stored_code(ui):
    d = make_drafter(ps='Noun', field='Plural')
    assert d.fieldtypename() == label_for(d, 'Plural')
    assert d._display(('field', None)) == label_for(d, 'Plural')


def test_a_stored_field_not_offered_here_still_renders(ui):
    """The page builds before anything is settled: a stored field this ps
    does not offer shows as its raw value, not an IndexError."""
    d = make_drafter(ps='Noun', field='Imperative')
    assert d.fieldtypename() == 'Imperative'


# ── 3. committing the field is structural ─────────────────────────────────

def test_committing_the_field_rekeys_the_analysis_language_row(ui):
    d = make_drafter(ps='Noun', field='lc')
    assert d.analangftypecode() == 'xyz_lc'
    calls = []
    real_status = d.status
    d.status = lambda: (calls.append(1), real_status())
    d.commit(('field', None), 'Plural')
    assert calls, "a field commit must rebuild the page (STRUCTURAL)"
    assert d.analangftypecode() == 'xyz_Plural'
    assert d.langs[0] == 'xyz_Plural'
    assert 'xyz_Plural' in d.forms
    assert ('xyz_Plural', 'before') in d.fields
    assert ('xyz_lc', 'before') not in d.fields


def test_the_old_fields_row_does_not_survive_into_the_definition(ui):
    """After switching lc → Plural, the definition is a PLURAL frame; a
    leftover 'xyz_lc' entry in it is stale data written to disk for good
    (and resurrects on switching back). STRUCTURAL's docstring says the
    commit 're-keys every analysis-language row in self.forms'."""
    d = make_drafter(ps='Noun', field='lc')
    d.commit(('xyz_lc', 'before'), 'nde')
    d.commit(('field', None), 'Plural')
    d.commit(('name', None), 'Possessive')
    seen = []
    d.gimmesenseformdictwftypengloss = (
        lambda framedef, **k: seen.append(dict(framedef)) or {'en': 'x'})
    d.exemplified()
    assert seen, "exemplified did not build a definition"
    assert 'xyz_lc' not in seen[0], (
        "the citation row outlived the switch to the plural field: {}"
        .format(seen[0]))


def test_a_name_commit_is_not_structural(ui):
    d = make_drafter(ps='Noun')
    calls = []
    d.status = lambda: calls.append(1)
    d.commit(('name', None), 'Isolation')
    assert d.forms['name'] == 'Isolation'
    assert not calls
    assert d.fields[('name', None)]['button']['text'] == 'Isolation'


def test_escape_writes_nothing(ui):
    d = make_drafter(ps='Noun')
    d.edit(('name', None))
    d.fields[('name', None)]['var'].set('Typed but abandoned')
    d.commit()
    assert d.forms['name'] == ''


# ── 4. the word-break box, through commit ─────────────────────────────────

@pytest.mark.parametrize('typed', ['nde', 'nde ', 'nde   '])
def test_before_gets_exactly_one_space_when_the_box_is_set(ui, typed):
    d = make_drafter(ps='Noun')
    key = ('xyz_lc', 'before')
    d.edit(key)
    d.fields[key]['wordbreak'].set(True)
    d.commit(key, typed)
    assert d.forms['xyz_lc']['before'] == 'nde '


@pytest.mark.parametrize('typed', ['nde', 'nde ', 'nde   '])
def test_before_gets_no_space_when_the_box_is_clear(ui, typed):
    d = make_drafter(ps='Noun')
    key = ('xyz_lc', 'before')
    d.edit(key)
    d.fields[key]['wordbreak'].set(False)
    d.commit(key, typed)
    assert d.forms['xyz_lc']['before'] == 'nde'


@pytest.mark.parametrize('typed,checked,expected', [
    ('wa', True, ' wa'), ('  wa', True, ' wa'),
    ('wa', False, 'wa'), (' wa', False, 'wa')])
def test_after_takes_the_space_on_its_leading_edge(ui, typed, checked,
                                                   expected):
    d = make_drafter(ps='Noun')
    key = ('en', 'after')
    d.edit(key)
    d.fields[key]['wordbreak'].set(checked)
    d.commit(key, typed)
    assert d.forms['en']['after'] == expected


def test_reopening_derives_the_box_from_the_stored_form(ui):
    d = make_drafter(ps='Noun')
    key = ('xyz_lc', 'before')
    d.edit(key)
    d.fields[key]['wordbreak'].set(True)
    d.commit(key, 'nde')
    d.fields[key]['wordbreak'].set(False)     # leftover from somewhere else
    d.edit(key)
    assert d.fields[key]['wordbreak'].get() is True
    assert d.fields[key]['var'].get() == 'nde '


def test_the_button_marks_the_break_and_the_mark_is_never_stored(ui):
    d = make_drafter(ps='Noun')
    key = ('xyz_lc', 'before')
    d.edit(key)
    d.fields[key]['wordbreak'].set(True)
    d.commit(key, 'nde')
    assert d.fields[key]['button']['text'] == 'nde' + TFD.WORDBREAK_MARK
    assert TFD.WORDBREAK_MARK not in d.forms['xyz_lc']['before']


# ── 5. the definition exemplified builds, and the name gate ───────────────

def _use_button(ui):
    return [w for w in ui.created
            if 'command' in w.opts
            and str(w.opts.get('text', '')).startswith('Use ')]


def _define(d, name='Isolation'):
    d.commit(('name', None), name)
    for key, checked, typed in [((d.analangftypecode(), 'before'), True, 'nde'),
                                ((d.analangftypecode(), 'after'), True, 'wa'),
                                (('en', 'before'), True, 'my'),
                                (('en', 'after'), False, '')]:
        d.edit(key)
        d.fields[key]['wordbreak'].set(checked)
        d.commit(key, typed)


def test_the_definition_handed_to_submit(ui):
    d = make_drafter(ps='Noun', field='lc')
    _define(d)
    d.gimmesenseformdictwftypengloss = lambda framedef, **k: {'en': 'x'}
    got = []
    d.submit = lambda defn, name, event=None: got.append((defn, name))
    d.exemplified()
    buttons = _use_button(ui)
    assert len(buttons) == 1, "one 'Use … tone frame' button"
    buttons[0].opts['command']()
    assert got == [({'field': 'lc',
                     'xyz_lc': 'nde __ wa',
                     'en': 'my __'}, 'Isolation')]


def test_a_plural_frame_keys_its_text_by_the_field_name(ui):
    d = make_drafter(ps='Noun', field='Plural')
    _define(d, 'Possessive')
    seen = []
    d.gimmesenseformdictwftypengloss = (
        lambda framedef, **k: seen.append(dict(framedef)) or {'en': 'x'})
    d.exemplified()
    assert seen == [{'field': 'Plural',
                     'xyz_Plural': 'nde __ wa',
                     'en': 'my __'}]


def test_an_added_language_is_included_and_a_skipped_one_is_not(ui):
    d = make_drafter(ps='Noun', field='lc')
    _define(d)
    d.addback('fr')
    d.commit(('fr', 'before'), 'mon')
    seen = []
    d.gimmesenseformdictwftypengloss = (
        lambda framedef, **k: seen.append(dict(framedef)) or {'en': 'x'})
    d.exemplified()
    assert seen[-1].get('fr') == 'mon__'
    d.skiplang('fr')
    d.exemplified()
    assert 'fr' not in seen[-1]


@pytest.mark.parametrize('name', ['', '   '])
def test_the_empty_name_gate_refuses(ui, name):
    d = make_drafter(ps='Noun', field='lc')
    _define(d, name)
    asked = []
    d.gimmesenseformdictwftypengloss = (
        lambda framedef, **k: asked.append(framedef) or {'en': 'x'})
    d.exemplified()
    assert not asked, "no example lookup without a name"
    assert not _use_button(ui), "no way to submit an unnamed frame"


def test_a_name_containing_before_and_after_is_not_a_language(ui):
    """exemplified picks the languages as `self.forms` keys whose value
    contains 'before' and 'after' — a SUBSTRING test on the name string, so
    a frame named e.g. 'before and after' is taken for a language and
    indexed as a dict."""
    d = make_drafter(ps='Noun', field='lc')
    _define(d, 'before and after')
    seen = []
    d.gimmesenseformdictwftypengloss = (
        lambda framedef, **k: seen.append(dict(framedef)) or {'en': 'x'})
    d.exemplified()
    assert seen and 'name' not in seen[0]


# ── 6. a rendered example, through the drafter's own calls ────────────────

CITATION_FRAME = {'field': 'lc', 'xyz_lc': 'nde __ wa', 'en': 'my __'}
PLURAL_FRAME = {'field': 'Plural', 'xyz_Plural': 'nde __ wa', 'en': 'my __'}
PLURAL2_FRAME = {'field': 'Plural2', 'xyz_Plural2': 'nde __ wa',
                 'en': 'my __'}


def drafter_on(senses, field):
    prog = make_program(senses=senses)
    return make_drafter(ps='Noun', field=field, program=prog, build=False)


def test_a_citation_frame_renders_the_citation_form():
    d = drafter_on([make_sense()], 'lc')
    got = d.gimmesenseformdictwftypengloss(CITATION_FRAME)
    assert got is not None
    assert got['xyz_lc'] == 'nde bana wa'
    assert 'my child' in got['en']


def test_a_plural_frame_renders_the_plural_form():
    """Crashed with AttributeError before the 2026-10-13 nodebyftype fix:
    the frame stores the field NAME and `ftypes` is keyed by code."""
    d = drafter_on([make_sense()], 'Plural')
    got = d.gimmesenseformdictwftypengloss(PLURAL_FRAME)
    assert got is not None
    assert got['xyz_Plural'] == 'nde babana wa', (
        "not the plural form (citation is 'bana', the other plural 'bibana')")
    assert 'child' in got['en']


def test_a_frame_on_the_other_plural_field_renders_that_field():
    """Kent, 2026-10-13: 'If there are two plurals in a language, we don't
    want the wrong one picked up for a frame, just because it's plural.'"""
    d = drafter_on([make_sense()], 'Plural2')
    got = d.gimmesenseformdictwftypengloss(PLURAL2_FRAME)
    assert got['xyz_Plural2'] == 'nde bibana wa'


def test_senses_without_the_field_are_passed_over():
    without = make_sense('s0', plural=None, plural2=None)
    d = drafter_on([without, make_sense('s1')], 'Plural')
    got = d.gimmesenseformdictwftypengloss(PLURAL_FRAME)
    assert got is not None and got['xyz_Plural'] == 'nde babana wa'


def test_no_sense_with_the_field_gives_up_rather_than_spinning():
    without = make_sense('s0', plural=None, plural2=None)
    d = drafter_on([without], 'Plural')
    assert d.gimmesenseformdictwftypengloss(PLURAL_FRAME) is None


@pytest.mark.parametrize('field,expected', [('lc', 'nde bana wa'),
                                            ('Plural', 'nde babana wa')])
def test_the_example_reaches_the_page(ui, field, expected):
    """End to end: define on the page, Get Example, read the labels."""
    prog = make_program(senses=[make_sense()])
    d = make_drafter(ps='Noun', field=field, program=prog)
    _define(d)
    d.exemplified()
    texts = [str(w.opts.get('text', '')) for w in ui.created]
    want = '[xyz_{}]: {}'.format(field, expected)
    assert want in texts, "example label missing; page shows {}".format(
        [t for t in texts if t.startswith('[')])
    assert _use_button(ui)


# ── 7. submit → ToneFrames.addframe ───────────────────────────────────────

def test_submit_stores_the_definition_under_ps_and_name(ui):
    d = make_drafter(ps='Noun', field='lc')
    _define(d)
    d.gimmesenseformdictwftypengloss = lambda framedef, **k: {'en': 'x'}
    d.exemplified()
    _use_button(ui)[0].opts['command']()
    frames = d.program.toneframes
    assert frames['Noun']['Isolation'] == {'field': 'lc',
                                           'xyz_lc': 'nde __ wa',
                                           'en': 'my __'}
    assert 'toneframes' in d.program.settings.stored
    assert d.program.settings.checks == ['Isolation']
    assert d.destroyed


def test_addframe_stores_under_ps_then_name():
    tf = ToneFrames(SimpleNamespace(), None)
    defn = {'field': 'lc', 'en': '__'}
    tf.addframe('Noun', 'Isolation', defn)
    assert tf == {'Noun': {'Isolation': defn}}


def test_addframe_refuses_a_duplicate_name_in_the_same_ps():
    tf = ToneFrames(SimpleNamespace(), None)
    first = {'field': 'lc', 'en': '__'}
    tf.addframe('Noun', 'Isolation', first)
    tf.addframe('Noun', 'Isolation', {'field': 'lc', 'en': 'the __'})
    assert tf['Noun']['Isolation'] is first, (
        "a second 'Isolation' for Noun replaced the first")


def test_submitting_a_duplicate_name_does_not_replace_the_frame(ui):
    first = {'field': 'lc', 'xyz_lc': '__', 'en': '__'}
    prog = make_program(frames={'Noun': {'Isolation': first}})
    d = make_drafter(ps='Noun', field='lc', program=prog)
    d.submit({'field': 'lc', 'xyz_lc': 'nde __', 'en': 'the __'}, 'Isolation')
    assert prog.toneframes['Noun']['Isolation'] == first


def test_a_name_that_equals_some_ps_is_not_a_duplicate():
    """Duplicates are names within a ps; a ps key is not a frame name."""
    tf = ToneFrames(SimpleNamespace(), None)
    tf.addframe('Verb', 'Command', {'field': 'lc', 'en': '__!'})
    defn = {'field': 'lc', 'en': 'a __'}
    tf.addframe('Noun', 'Verb', defn)
    assert tf.get('Noun', {}).get('Verb') == defn


def test_the_same_name_in_another_ps_is_its_own_frame():
    tf = ToneFrames(SimpleNamespace(), None)
    noun = {'field': 'lc', 'en': '__'}
    verb = {'field': 'lc', 'en': 'to __'}
    tf.addframe('Noun', 'Isolation', noun)
    tf.addframe('Verb', 'Isolation', verb)
    assert tf['Noun']['Isolation'] is noun
    assert tf['Verb']['Isolation'] is verb


def test_addframe_refuses_a_definition_that_is_not_a_dict():
    tf = ToneFrames(SimpleNamespace(), None)
    tf.addframe('Noun', 'Isolation', 'nde __')
    assert 'Isolation' not in tf.get('Noun', {})


# ── 8. ToneFrames.source ──────────────────────────────────────────────────

def test_source_gives_a_fieldless_frame_the_citation_field():
    tf = ToneFrames(SimpleNamespace(),
                    {'Noun': {'Old': {'xyz': '__', 'en': 'the __'}}})
    assert tf['Noun']['Old']['field'] == 'lc'


def test_source_keeps_a_field_name_as_it_is():
    """A frame stores its FIELD NAME; loading must never turn it into a
    code ('pl') or anything else."""
    tf = ToneFrames(SimpleNamespace(),
                    {'Noun': {'Possessive': {'field': 'Plural',
                                             'xyz_Plural': '__'}},
                     'Verb': {'Command': {'field': 'Imperative'}}})
    assert tf['Noun']['Possessive']['field'] == 'Plural'
    assert tf['Verb']['Command']['field'] == 'Imperative'


def test_source_registers_itself_on_the_program():
    prog = SimpleNamespace()
    tf = ToneFrames(prog, None)
    assert prog.toneframes is tf
