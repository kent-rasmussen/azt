"""A stored `<unset>` must not survive the read.

`<unset>` is what the status line SHOWS when a second-form field has no
value. It reached `project.json` as a real setting — Kent, 2026-09-17:
`"Verb": "<unset>"`, "is that going to get us into trouble?" — because the
second-form line is free-text and clicking away commits whatever it was
displaying.

`_refuse_unset_field` stopped that being stored from then on, but a refusal
at the setter cannot reach a file already written. Parse indexes
`secondformfield[ps]` directly, so a project carrying the placeholder asks
"what is the `<unset>` of x?" and writes the answer into a LIFT field
literally named `<unset>`.

Plan 8 of the second-form flags audit: apply the setter's predicate on load.
"""
from settings import Settings


def _settings(**attrs):
    """A `Settings` with no `__init__` — the suite's fake-self technique."""
    s = Settings.__new__(Settings)
    for k, v in attrs.items():
        setattr(s, k, v)
    return s


def test_the_placeholder_is_dropped_on_load():
    s = _settings()
    s.load_second_form_fields({'Noun': 'Plural', 'Verb': Settings.UNSETFIELD})
    assert s.secondformfield == {'Noun': 'Plural'}


def test_the_key_goes_too_not_just_the_value():
    """DROPPED, NOT BLANKED. `parser.pscheck` treats the dict's KEYS as the
    set of legal parts of speech, so a key left behind with a blank value
    still says "this ps is configured" to it while saying "unset" to
    `secondformfieldset` — the split that fooled three consumers at once."""
    s = _settings()
    s.load_second_form_fields({'Verb': Settings.UNSETFIELD})
    assert 'Verb' not in s.secondformfield


def test_a_blank_is_refused_the_same_way():
    """The setter refuses `''` and the placeholder together; so does this."""
    s = _settings()
    s.load_second_form_fields({'Noun': '', 'Verb': '   '})
    assert s.secondformfield == {}


def test_real_names_are_kept_and_merged():
    """Everything else loads as before, onto whatever is already there."""
    s = _settings(secondformfield={'Noun': 'Plural'})
    s.load_second_form_fields({'Verb': 'Imperative'})
    assert s.secondformfield == {'Noun': 'Plural', 'Verb': 'Imperative'}


def test_the_reader_routes_second_forms_through_the_scrub():
    """The guard that matters: `readsettingsdict`'s generic dict branch
    would `update()` the placeholder straight in, so second forms need
    their own case ahead of it."""
    from sourcescan import code
    src = code(Settings.readsettingsdict)
    assert 'load_second_form_fields' in src
    assert src.index("'secondformfield'") < src.index('isinstance(v,dict)'), \
        'the second-form case must come BEFORE the generic dict update'


def test_a_scrubbed_setting_reads_as_unset():
    """End to end with the predicate every consumer asks: having dropped
    it, the ps is unset, and the page will ask for it."""
    s = _settings(nominalps='Noun', verbalps='Verb')
    s.load_second_form_fields({'Noun': 'Plural', 'Verb': Settings.UNSETFIELD})
    assert s.secondformfieldset('Noun')
    assert not s.secondformfieldset('Verb')
    assert s.missing_second_form_pss() == ['Verb']
