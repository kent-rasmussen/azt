"""A frame name already used for another category is proposed as "{name}-{ps}".

Kent, 2026-10-12: "someone will eventually want to define a second
Isolation, so We'll want to treat it well. I imagine something like
appending "_{ps}" when a name already exists for another ps should be
sufficient. Probably do this upfront, so people can modify as needed."
A hyphen, not an underscore (2026-10-09).
"""
from types import SimpleNamespace

import pytest

tasks = pytest.importorskip('tasks.tasks')
propose = tasks.ToneFrameDrafter._name_for_this_ps

FRAMES = {'Noun': {'Isolation': {}, 'Possessive': {}},
          'Verb': {'Imperative': {}}}


def drafter(ps):
    return SimpleNamespace(ps=ps, program=SimpleNamespace(toneframes=FRAMES))


def test_a_name_from_another_category_gets_the_suffix():
    assert propose(drafter('Verb'), 'Isolation') == 'Isolation-Verb'
    assert propose(drafter('Noun'), 'Imperative') == 'Imperative-Noun'


def test_a_new_name_is_left_alone():
    assert propose(drafter('Verb'), 'Question') == 'Question'


def test_a_name_this_category_has_is_not_this_rules_case():
    assert propose(drafter('Noun'), 'Isolation') == 'Isolation'


def test_the_proposal_can_be_edited_and_is_then_kept():
    assert propose(drafter('Verb'), 'Isolation-Verb') == 'Isolation-Verb'
    assert propose(drafter('Verb'), 'Bare') == 'Bare'


def test_an_empty_name_passes_through_for_the_name_gate():
    assert propose(drafter('Verb'), '') == ''
    assert propose(drafter('Verb'), None) is None


def test_the_commit_applies_it_to_the_name():
    from sourcescan import code
    assert '_name_for_this_ps' in code(tasks.ToneFrameDrafter.commit)
