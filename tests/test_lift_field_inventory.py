# coding=UTF-8
"""`getsensefieldnames`: which field names carry data in which language.

**32.6 seconds of a 53-second boot** (Kent's log, 2026-09-14), for 1700
senses — ~19 ms each, against 0.1 s for the LIFT XML parse that precedes it.
The cause was the shape of a dict comprehension: its OUTER loops ran over
every (sense, field, language) triple and the inner set rescanned every
sense for each one, so thousands of triples each did a full pass and then
collapsed onto five keys.

These tests pin the OUTPUT, not the speed — the rewrite is only worth
anything if it computes the same thing. A fake `self` with a `senses` list,
per tests/README.md: no LIFT file, no display.
"""
import pytest

lift = pytest.importorskip('io_put.lift', reason='needs io_put importable')


class Field:
    """A LIFT field: a name, and forms keyed by language."""

    def __init__(self, *langs):
        self.forms = {l: 'some text' for l in langs}


class Sense:
    def __init__(self, fields):
        self.fields = fields


class Db:
    """Only what the method reads."""

    def __init__(self, senses):
        self.senses = senses


def names(senses):
    db = Db(senses)
    lift.LiftXML.getsensefieldnames(db)
    return db.sensefieldnames


def test_a_field_is_listed_under_every_language_it_carries():
    result = names([Sense({'SILCAWL': Field('en', 'fr')})])
    assert result == {'en': {'SILCAWL'}, 'fr': {'SILCAWL'}}


def test_fields_accumulate_across_senses():
    """The whole point: the inventory is the union over all senses, which is
    what the old version recomputed thousands of times."""
    result = names([
        Sense({'SILCAWL': Field('en')}),
        Sense({'tone': Field('en-x-tone')}),
        Sense({'cvprofile_lc': Field('en-x-cvprofile'), 'SILCAWL': Field('en')}),
    ])
    assert result == {'en': {'SILCAWL'},
                      'en-x-tone': {'tone'},
                      'en-x-cvprofile': {'cvprofile_lc'}}


def test_a_language_appearing_only_under_an_unnamed_field_keeps_its_key():
    """FAITHFUL TO THE ODDITY. The old outer loop did not test `if k`, so a
    language reached only through a field with a falsy name still produced a
    key — with an empty set, because the inner loop DID test it. Preserved
    deliberately rather than quietly changed."""
    result = names([Sense({'': Field('en-x-py')})])
    assert result == {'en-x-py': set()}


def test_an_unnamed_field_does_not_pollute_a_real_language():
    result = names([Sense({'': Field('en'), 'SILCAWL': Field('en')})])
    assert result == {'en': {'SILCAWL'}}


def test_no_senses_gives_no_inventory():
    assert names([]) == {}


def test_a_field_with_no_forms_contributes_nothing():
    assert names([Sense({'SILCAWL': Field()})]) == {}


def test_the_result_is_sets_not_lists():
    """Callers index it by language and test membership; the old version
    built `set(...)` and the shape must not change."""
    result = names([Sense({'SILCAWL': Field('en')})])
    assert isinstance(result['en'], set)


def _reads_for(n):
    """How many times `sense.fields` is read while inventorying n senses."""
    reads = []

    class Counted:
        def __init__(self):
            self._fields = {'SILCAWL': Field('en', 'fr'),
                            'tone': Field('en-x-tone')}

        @property
        def fields(self):
            reads.append(1)
            return self._fields

    names([Counted() for _ in range(n)])
    return len(reads)


def test_the_inventory_scales_LINEARLY_with_the_senses():
    """THE REGRESSION GUARD, and the only test here that would have caught
    the original — every output test passes against it, because it was
    correct, merely quadratic.

    SCALING, not an exact count: a first version asserted exactly one read
    per sense and failed at three, because `sense.fields` is a property and
    the code read it again per field. That is a fair implementation detail to
    change; going quadratic is not. So double the input and require the work
    to roughly double.

    The old shape would give ~n² here: every (sense, field, language) triple
    — 3n of them — rescanned all n senses.
    """
    small, large = _reads_for(20), _reads_for(40)
    assert large < small * 3, (
        "reads went {} → {} when the senses doubled; that is superlinear "
        "and the quadratic shape is back".format(small, large))
    assert large >= small, "fewer reads for more senses is not credible"