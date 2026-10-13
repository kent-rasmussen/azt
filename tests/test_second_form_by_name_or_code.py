"""A frame's field is found EXACTLY: by code through `ftypes`, or by the
exact field name on the entry — never "whatever is the plural now".

A tone frame stores the field NAME; looking it up as a code found nothing,
so defining or using a plural/imperative frame crashed (pre-workshop audit,
2026-10-13). Kent, the same day: "If there are two plurals in a language,
we don't want the wrong one picked up for a frame, just because it's
plural."
"""
from types import SimpleNamespace

import pytest

lift = pytest.importorskip('io_put.lift')
Sense = lift.Sense


def fake_sense():
    lc = SimpleNamespace(ftype='lc')
    plural = SimpleNamespace(ftype='Plural')
    plural2 = SimpleNamespace(ftype='Plural2')
    s = Sense.__new__(Sense)
    s.ftypes = {'lc': lc, 'pl': plural}            # 'Plural' is THE plural now
    s.entry = SimpleNamespace(fields={'Plural': plural, 'Plural2': plural2})
    return s, lc, plural, plural2


def test_found_by_code_or_by_exact_field_name():
    s, lc, plural, plural2 = fake_sense()
    assert Sense.nodebyftype(s, 'pl') is plural
    assert Sense.nodebyftype(s, 'lc') is lc
    assert Sense.nodebyftype(s, 'Plural') is plural
    assert Sense.nodebyftype(s, 'imp') is None


def test_a_frame_on_the_other_plural_gets_that_field_not_the_current_one():
    s, _lc, plural, plural2 = fake_sense()
    assert Sense.nodebyftype(s, 'Plural2') is plural2
    assert Sense.nodebyftype(s, 'Plural2') is not plural


def test_same_form_is_identity_of_the_field():
    s, *_ = fake_sense()
    assert Sense.same_form(s, 'pl', 'Plural')
    assert not Sense.same_form(s, 'pl', 'Plural2')
    assert not Sense.same_form(s, 'lc', 'Plural')
