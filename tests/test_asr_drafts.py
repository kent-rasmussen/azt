"""Phase-1 storage-helper tests for ASR draft persistence (ADR 0002).

`lift.Form.persist_drafts` / `load_drafts` / `wipe_drafts` store ASR
transcription drafts as annotations on the `<analang>-x-audio` form:

    {repo}      -> transcription     ipa-{repo}  -> IPA
    tone-{repo} -> tone melody       md5         -> audio fingerprint

These helpers are pure and headless (no filesystem, no Tk, no models) — exactly
the backend guidance in tests/README.md — so they round-trip in memory.
"""
import xml.etree.ElementTree as ET

import pytest

try:
    from io_put import lift
except ImportError as e:  # optional dep missing in this env
    pytest.skip(f"optional dependency not installed: {e.name}",
                allow_module_level=True)


class _Root(ET.Element):
    """Minimal parent: a real Element (so lift's isinstance checks pass) that
    also carries the `.db` attribute lift.Node.__init__ copies onto children.
    A pure-Python subclass gets a __dict__, so `.db` assignment works where the
    C Element would reject it."""


def _audio_form(filename='dive.wav'):
    """A lift.Form wrapping an <analang>-x-audio form, initialised the way the
    LIFT parser leaves it (annotations dict populated)."""
    parent = _Root('field')
    parent.db = None
    el = ET.SubElement(parent, 'form', {'lang': 'nml-x-audio'})
    ET.SubElement(el, 'text').text = filename
    form = lift.Form(parent, el)
    form.getannotations()
    return form


def test_persist_then_load_roundtrips():
    form = _audio_form()
    form.persist_drafts(
        transcriptions={'facebook/mms-1b-all (swh!)': 'dìve', 'allosaurus': 'dive'},
        ipa={'neurlang/ipa-whisper-base': 'diːve'},
        tone={'katyayego': 'HL'},
        md5='abc123',
    )
    tx, ipa, tone, md5 = form.load_drafts()
    assert tx == {'facebook/mms-1b-all (swh!)': 'dìve', 'allosaurus': 'dive'}
    assert ipa == {'neurlang/ipa-whisper-base': 'diːve'}
    assert tone == {'katyayego': 'HL'}
    assert md5 == 'abc123'


def test_empty_candidates_skipped():
    form = _audio_form()
    form.persist_drafts(transcriptions={'mms': '', 'allosaurus': 'dive'}, md5='m')
    tx, _ipa, _tone, _md5 = form.load_drafts()
    assert tx == {'allosaurus': 'dive'}  # empty string never stored


def test_md5_mismatch_wipes_and_redrafts():
    form = _audio_form()
    form.persist_drafts(transcriptions={'mms': 'old'}, ipa={'neur': 'oʊld'}, md5='v1')
    # re-record: same filename, new audio -> new md5 -> stale drafts wiped
    form.persist_drafts(transcriptions={'mms': 'new'}, md5='v2')
    tx, ipa, _tone, md5 = form.load_drafts()
    assert tx == {'mms': 'new'}
    assert ipa == {}          # old IPA lane wiped, not carried over
    assert md5 == 'v2'


def test_md5_match_fills_gaps_idempotent():
    form = _audio_form()
    form.persist_drafts(transcriptions={'mms': 'dive'}, md5='same')
    # same md5 -> no wipe; a second model's draft just fills the gap
    form.persist_drafts(transcriptions={'allosaurus': 'dive'}, md5='same')
    tx, _i, _t, md5 = form.load_drafts()
    assert tx == {'mms': 'dive', 'allosaurus': 'dive'}
    assert md5 == 'same'


def test_legacy_form_no_annotations():
    form = _audio_form()
    assert form.load_drafts() == ({}, {}, {}, None)


def test_wipe_preserves_digit_named_annotations():
    form = _audio_form()
    form.annotationvalue('0', 'original')          # revert-history style
    form.persist_drafts(transcriptions={'mms': 'x'}, md5='a')
    form.persist_drafts(transcriptions={'mms': 'y'}, md5='b')  # triggers wipe
    assert form.annotationvalue('0') == 'original'  # survived the ASR wipe
    tx, *_ = form.load_drafts()
    assert tx == {'mms': 'y'}
