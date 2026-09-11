"""Backend/core logic tests.

Two layers:

1. **API-surface guards** (active): the documented public classes exist and are
   classes. Cheap regression guard against accidental rename/removal; class
   names verified against source on 2026-06-06.

2. **Behavioral tests** (skipped stubs): real assertions about sorting,
   parsing, and analysis need either a small LIFT fixture or a constructed
   ``program`` object. They're stubbed here as a TODO map so the next person
   (or session) has an obvious place to add them — rather than fabricating
   assertions against an unverified API. See tests/README.md.
"""
import importlib

import pytest


def _import_or_skip(mod):
    try:
        return importlib.import_module(mod)
    except ImportError as e:
        pytest.skip(f"optional dependency not installed: {e.name}")


# ── 1. API-surface guards ────────────────────────────────────────────────

def test_lexicon_public_classes_present():
    lex = _import_or_skip("backend.core.lexicon")
    for name in ["Senses", "Segments", "WordCollection", "Parse", "Tone"]:
        assert isinstance(getattr(lex, name, None), type), f"lexicon.{name} missing"


def test_sorting_engine_sort_present_and_subclasses_categories():
    se = _import_or_skip("backend.core.sorting_engine")
    cats = _import_or_skip("backend.core.categories")
    assert isinstance(getattr(se, "Sort", None), type)
    assert issubclass(se.Sort, cats.Categories)


def test_lexicon_inheritance_chain():
    lex = _import_or_skip("backend.core.lexicon")
    # documented hierarchy: Segments(Senses); WordCollection(Segments); Parse(Segments); Tone(Senses)
    assert issubclass(lex.Segments, lex.Senses)
    assert issubclass(lex.WordCollection, lex.Segments)
    assert issubclass(lex.Parse, lex.Segments)
    assert issubclass(lex.Tone, lex.Senses)


# ── 2. Behavioral tests — TODO (skipped stubs) ───────────────────────────

@pytest.mark.integration
def test_lift_parse_roundtrip():
    pytest.skip(
        "TODO: add a minimal LIFT XML fixture under tests/fixtures/ and assert "
        "io_put.lift parses entries/senses/glosses from it. Needs the lift loader "
        "API confirmed first."
    )


@pytest.mark.integration
def test_sort_groups_words_by_profile():
    pytest.skip(
        "TODO: assert grouping/verification logic on known input. NOT by "
        "building a whole `program`: dummy.App is only a container (it sets a "
        "few identity fields and setattrs a dict), while sorting_engine.py "
        "reads SIXTEEN collaborators off program — slices, params, settings, "
        "status, status_dirty, db, profiles, alphabet, examples, toneframes, "
        "taskchooser, sort_ui, data_repo, maybewrite, ui_settings, "
        "syllable_preferred_slice — most of them rich objects. That is why "
        "this stub has not moved. Instead pick ONE method and fake only what "
        "IT touches, on an instance built with __new__ (no __init__): the "
        "technique that worked for SoundSettings and the sound_ui handlers "
        "(see test_sound_settings_contracts.py, test_sound_ui_handlers.py). "
        "Kent asked 2026-09-11 whether dummy.App was enough; it is the right "
        "shell and none of the contents."
    )


@pytest.mark.integration
def test_profile_analyzer_cv_profiles():
    pytest.skip(
        "TODO: feed ProfileAnalyzer known syllable data and assert the CV "
        "profiles it produces."
    )
