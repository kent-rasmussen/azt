"""Unit tests for io_put/dekereke.py — Dekereke <-> LIFT conversion.

Fixtures are generated here rather than read from sample files, so the three
on-disk encodings Dekereke has used over the years (UTF-16LE with BOM from the
older releases, UTF-8 with BOM, and bare UTF-8 from the current one) are each
covered without committing a file whose encoding an editor could silently
"fix". Getting that wrong is the single most common way to break a Dekereke
reader, so it is pinned first.

The round-trip tests are the important ones: a Dekereke database holds columns
A-Z+T has no concept of — other speakers, dialect forms, acoustic measurements
— and an export that dropped them would destroy the user's data.
"""
import pathlib

import pytest

from io_put import dekereke

lxml = pytest.importorskip("lxml")  # the transforms need it; the reader doesn't


RECORDS = """\
  <data_form>
    <Reference>0015</Reference>
    <Category>Noun</Category>
    <SoundFile>0015_rawa.wav</SoundFile>
    <IndonesianGloss>rawa</IndonesianGloss>
    <Phonetic>tei</Phonetic>
    <Tulisan>tei</Tulisan>
    <Speaker2>tei</Speaker2>
    <kosong />
    <Xstraight>tei dobe</Xstraight>
    <Xstraight_Pitch>LH</Xstraight_Pitch>
    <Catatan>periksa dengan penutur lain</Catatan>
  </data_form>
  <data_form>
    <Reference>0012</Reference>
    <Category>Verb</Category>
    <SoundFile>0012_turun.wav</SoundFile>
    <IndonesianGloss>turun</IndonesianGloss>
    <Phonetic />
    <Tulisan>oudo</Tulisan>
    <Speaker2>oudo</Speaker2>
    <kosong />
    <Xstraight />
    <Xstraight_Pitch />
    <Catatan />
  </data_form>
"""
DATABASE = '<?xml version="1.0" encoding="{declared}"?>\n<phon_data>\n{records}</phon_data>\n'


def write(dirname, encoding="utf-8", bom=False, declared="utf-8"):
    """One Dekereke database on disk, in a given encoding."""
    path = pathlib.Path(dirname) / "SampleLang.xml"
    text = DATABASE.format(declared=declared, records=RECORDS).replace("\n", "\r\n")
    raw = text.encode(encoding)
    if bom and encoding == "utf-8":
        raw = b"\xef\xbb\xbf" + raw
    path.write_bytes(raw)
    return path


def settings(path, sound_file_path=r"C:\SampleLang\audio"):
    """The sibling per-user settings file, which is where Dekereke keeps the
    audio folder and the per-column recording suffixes."""
    sibling = path.with_name(path.stem + dekereke.SETTINGSSUFFIX)
    sibling.write_text(
        '<?xml version="1.0" encoding="utf-8"?>\n'
        "<settings>\n"
        f"  <sound_file_path>{sound_file_path}</sound_file_path>\n"
        "  <column_to_sound_file_suffix_mappings>\n"
        "    <column_to_sound_file_suffix_mapping>Speaker2\t-sp2"
        "</column_to_sound_file_suffix_mapping>\n"
        "  </column_to_sound_file_suffix_mappings>\n"
        "</settings>\n",
        encoding="utf-8",
    )
    return sibling


def mapped(path, analang="fau", glosslangs=("id",)):
    dk = dekereke.DekerekeXML(path)
    map = dekereke.ColumnMap(dk.columns, analang=analang, glosslangs=list(glosslangs))
    map.automap()
    return dk, map


# --- encodings: all three must read identically ------------------------------

@pytest.mark.parametrize(
    "encoding,bom,declared",
    [
        ("utf-8", False, "utf-8"),        # current Dekereke release
        ("utf-8", True, "utf-8"),         # intermediate
        ("utf-16", False, "utf-16"),      # older releases; codec writes the BOM
    ],
)
def test_reads_every_dekereke_encoding(tmp_path, encoding, bom, declared):
    path = write(tmp_path, encoding=encoding, bom=bom, declared=declared)
    dk = dekereke.DekerekeXML(path)
    assert len(dk.records()) == 2
    assert dk.columns[0] == "Reference"
    assert "Speaker2" in dk.columns


def test_utf16_is_detected_so_an_export_can_match_it(tmp_path):
    dk = dekereke.DekerekeXML(write(tmp_path, encoding="utf-16", declared="utf-16"))
    assert dk.utf16 is True
    assert dekereke.DekerekeXML(write(tmp_path)).utf16 is False


def test_a_file_that_is_not_dekereke_is_refused(tmp_path):
    path = tmp_path / "notdekereke.xml"
    path.write_text('<?xml version="1.0"?><lift><entry/></lift>')
    with pytest.raises(dekereke.BadParseError):
        dekereke.DekerekeXML(path)


# --- the column inventory ----------------------------------------------------

def test_columns_are_in_the_databases_own_order(tmp_path):
    dk = dekereke.DekerekeXML(write(tmp_path))
    assert dk.columns[:4] == ["Reference", "Category", "SoundFile", "IndonesianGloss"]


def test_nested_blocks_are_not_columns(tmp_path):
    """<qvp_acoustic_data_> holds Praat measurements, not a column value."""
    path = write(tmp_path)
    path.write_bytes(
        path.read_bytes().replace(
            b"<Catatan>periksa dengan penutur lain</Catatan>",
            b"<qvp_acoustic_data_><V1T>0.212</V1T></qvp_acoustic_data_>",
        )
    )
    assert "qvp_acoustic_data_" not in dekereke.DekerekeXML(path).columns


def test_settings_file_gives_the_audio_folder_and_per_column_takes(tmp_path):
    path = write(tmp_path)
    settings(path)
    dk = dekereke.DekerekeXML(path)
    assert dk.audiodir == r"C:\SampleLang\audio"
    assert dk.audiosuffixes == {"Speaker2": "-sp2"}


def test_a_missing_settings_file_is_not_an_error(tmp_path):
    dk = dekereke.DekerekeXML(write(tmp_path))
    assert dk.audiodir is None and dk.audiosuffixes == {}


# --- guessing what the columns are for ---------------------------------------

def test_automap_recognizes_the_usual_columns(tmp_path):
    _, map = mapped(write(tmp_path))
    assert map.role("Phonetic") == "phonetic"
    assert map.role("Reference") == "reference"
    assert map.role("Category") == "pos"
    assert map.role("SoundFile") == "audio"
    assert map.role("Catatan") == "note"
    assert map.role("IndonesianGloss") == "gloss"
    assert map.langs["IndonesianGloss"] == "id"


def test_automap_recognizes_indonesian_column_names(tmp_path):
    """National-language column names are as common in the field as English
    ones, and a database uses one or the other, not both."""
    path = write(tmp_path)
    path.write_bytes(path.read_bytes().replace(b"Catatan", b"Notes"))
    _, map = mapped(path)
    assert map.role("Notes") == "note"


def test_an_elicitation_frame_becomes_a_frame(tmp_path):
    _, map = mapped(write(tmp_path))
    assert map.role("Xstraight") == "frame"


def test_a_pitch_column_is_tied_to_the_frame_it_belongs_to(tmp_path):
    _, map = mapped(write(tmp_path))
    assert map.twins["Xstraight"] == "Xstraight_Pitch"
    assert map.role("Xstraight_Pitch") == "pitchtwin"


def test_a_pitch_column_with_no_frame_stands_alone(tmp_path):
    """Not every frame has a twin, so pairing must never be required."""
    map = dekereke.ColumnMap(["Phonetic", "Orphan_Pitch"], analang="fau")
    map.automap()
    assert map.role("Orphan_Pitch") == "tone"
    assert map.twins == {}


def test_every_column_gets_a_role_so_nothing_is_dropped_unseen(tmp_path):
    dk, map = mapped(write(tmp_path))
    assert set(map.roles) == set(dk.columns)


def test_an_unrecognized_column_is_preserved_as_a_field(tmp_path):
    _, map = mapped(write(tmp_path))
    assert map.role("Speaker2") == "field"
    assert map.fieldname("Speaker2") == "Dk_Speaker2"


def test_the_first_of_two_candidates_wins(tmp_path):
    """'Orthography' beats 'Tulisan'; the loser is preserved, not dropped."""
    map = dekereke.ColumnMap(
        ["Phonetic", "Orthography", "Tulisan"], analang="fau")
    map.automap()
    assert map.role("Orthography") == "orthographic"
    assert map.role("Tulisan") == "field"


def test_a_map_without_a_form_to_analyze_is_refused(tmp_path):
    map = dekereke.ColumnMap(["Reference", "Gloss"], analang="fau")
    map.automap()
    assert map.check()  # user-facing text, not an exception


def test_bookkeeping_uses_a_language_the_database_actually_glosses_in(tmp_path):
    """A database glossed only in Indonesian must not be labelled 'en'."""
    _, map = mapped(write(tmp_path), glosslangs=("id",))
    assert map.bookkeepinglang() == "id"


# --- import ------------------------------------------------------------------

def imported(tmp_path):
    path = write(tmp_path)
    settings(path)
    dk, map = mapped(path)
    lift = tmp_path / "SampleLang.lift"
    count = dekereke.tolift(dk, map, lift)
    return path, lift, count, map


def test_import_writes_one_entry_per_usable_record(tmp_path):
    """The record with no phonetic form cannot become an entry: A-Z+T would
    show it as an empty button in every sort."""
    _, _, count, _ = imported(tmp_path)
    assert count == 1


def test_import_puts_the_form_to_analyze_where_azt_looks_for_it(tmp_path):
    _, lift, _, _ = imported(tmp_path)
    tree = lxml.etree.parse(str(lift))
    assert tree.xpath("//entry/citation/form[@lang='fau']/text/text()") == ["tei"]


def test_import_writes_a_gloss_and_a_definition(tmp_path):
    """A-Z+T cannot open a file with no gloss anywhere in it, and its own
    addentry writes the same text to both."""
    _, lift, _, _ = imported(tmp_path)
    tree = lxml.etree.parse(str(lift))
    assert tree.xpath("//sense/gloss[@lang='id']/text/text()") == ["rawa"]
    assert tree.xpath("//sense/definition/form[@lang='id']/text/text()") == ["rawa"]


def test_import_uses_the_audio_tag_azt_actually_recognizes(tmp_path):
    """backend/langtags.py builds '-Zxxx-x-audio'; a bare '-x-audio' form is
    not detected as audio at all."""
    _, lift, _, _ = imported(tmp_path)
    tree = lxml.etree.parse(str(lift))
    assert tree.xpath("//citation/form[@lang='fau-Zxxx-x-audio']/text/text()")


def test_import_keeps_the_row_key_so_a_re_import_can_update(tmp_path):
    _, lift, _, _ = imported(tmp_path)
    tree = lxml.etree.parse(str(lift))
    assert tree.xpath("//entry/field[@type='Dekereke-Reference']/form/text/text()") == ["0015"]
    assert tree.xpath("//header/fields/field[@tag='Dekereke-Reference']")


def test_import_turns_a_frame_column_into_an_example_azt_can_sort(tmp_path):
    _, lift, _, _ = imported(tmp_path)
    tree = lxml.etree.parse(str(lift))
    assert tree.xpath("//sense/example/form[@lang='fau']/text/text()") == ["tei dobe"]
    assert tree.xpath(
        "//sense/example/field[@type='location']/form/text/text()") == ["Xstraight"]


def test_import_puts_frame_tone_on_the_machine_form(tmp_path):
    """The plain form means a speaker confirmed it by ear; nobody has yet."""
    _, lift, _, _ = imported(tmp_path)
    tree = lxml.etree.parse(str(lift))
    assert tree.xpath(
        "//example/field[@type='tone']/form[@lang='fau-x-tone_MT']/text/text()") == ["LH"]


def test_import_preserves_a_column_azt_has_no_concept_of(tmp_path):
    """A second speaker's forms must survive the trip even though A-Z+T can
    only analyze one form per entry."""
    _, lift, _, _ = imported(tmp_path)
    tree = lxml.etree.parse(str(lift))
    assert tree.xpath(
        "//entry/field[@type='Dk_Speaker2']/form[@lang='fau']/text/text()") == ["tei"]


def test_import_gives_a_column_with_its_own_take_that_recording(tmp_path):
    _, lift, _, _ = imported(tmp_path)
    tree = lxml.etree.parse(str(lift))
    assert tree.xpath(
        "//field[@type='Dk_Speaker2']/form[@lang='fau-Zxxx-x-audio']/text/text()"
    ) == ["0015_rawa-sp2.wav"]


def test_import_writes_a_sidecar_remembering_the_source(tmp_path):
    path, lift, _, _ = imported(tmp_path)
    sidecar = dekereke.sidecarname(lift)
    assert sidecar.exists()
    reread = dekereke.ColumnMap.read(sidecar)
    assert reread.columns == dekereke.DekerekeXML(path).columns
    assert reread.audiodir == r"C:\SampleLang\audio"
    assert reread.suffixes == {"Speaker2": "-sp2"}


def test_guids_look_like_the_ones_azt_makes_itself(tmp_path):
    _, lift, _, _ = imported(tmp_path)
    guid = lxml.etree.parse(str(lift)).xpath("//entry/@guid")[0]
    assert [len(p) for p in guid.split("-")] == [8, 4, 4, 4, 12]
    assert guid == guid.lower()


# --- export ------------------------------------------------------------------

def test_export_returns_every_record_unchanged_when_nothing_was_edited(tmp_path):
    """The strongest guarantee this module offers: a user can import into
    A-Z+T and export back without losing a single cell."""
    path, lift, _, _ = imported(tmp_path)
    out = tmp_path / "roundtrip.xml"
    dekereke.todekereke(lift, out, dekerekefilename=path)
    before = lxml.etree.fromstring(path.read_bytes())
    after = lxml.etree.fromstring(out.read_bytes())
    assert len(before) == len(after)
    for old, new in zip(before, after):
        assert [(c.tag, c.text) for c in old] == [(c.tag, c.text) for c in new]


def test_export_keeps_a_record_azt_never_imported(tmp_path):
    """The skipped record has no LIFT entry to merge from, so it must come
    through the identity transform untouched rather than being emptied."""
    path, lift, _, _ = imported(tmp_path)
    out = tmp_path / "roundtrip.xml"
    dekereke.todekereke(lift, out, dekerekefilename=path)
    after = lxml.etree.fromstring(out.read_bytes())
    skipped = [r for r in after if r.findtext("Reference") == "0012"]
    assert skipped and skipped[0].findtext("Tulisan") == "oudo"


def test_export_writes_an_edit_back_into_the_right_column(tmp_path):
    path, lift, _, _ = imported(tmp_path)
    tree = lxml.etree.parse(str(lift))
    tree.xpath("//citation/form[@lang='fau']/text")[0].text = "teii"
    tree.write(str(lift), encoding="UTF-8")
    out = tmp_path / "edited.xml"
    dekereke.todekereke(lift, out, dekerekefilename=path)
    after = lxml.etree.fromstring(out.read_bytes())
    assert after[0].findtext("Phonetic") == "teii"
    assert after[0].findtext("Speaker2") == "tei"  # untouched


def test_export_does_not_blank_a_cell_azt_has_no_opinion_about(tmp_path):
    """An entry deleted in A-Z+T must not empty the user's Dekereke row."""
    path, lift, _, _ = imported(tmp_path)
    tree = lxml.etree.parse(str(lift))
    entry = tree.xpath("//entry")[0]
    entry.getparent().remove(entry)
    tree.write(str(lift), encoding="UTF-8")
    out = tmp_path / "deleted.xml"
    dekereke.todekereke(lift, out, dekerekefilename=path)
    after = lxml.etree.fromstring(out.read_bytes())
    assert after[0].findtext("Phonetic") == "tei"


def test_export_matches_the_encoding_of_the_source_database(tmp_path):
    path = write(tmp_path, encoding="utf-16", declared="utf-16")
    dk, map = mapped(path)
    lift = tmp_path / "SampleLang.lift"
    dekereke.tolift(dk, map, lift)
    out = tmp_path / "roundtrip.xml"
    dekereke.todekereke(lift, out, dekerekefilename=path)
    raw = out.read_bytes()
    assert raw[:2] == b"\xff\xfe"  # UTF-16LE, with the BOM Dekereke writes


def test_export_restores_the_line_endings_dekereke_uses(tmp_path):
    """XML parsers normalize CRLF away and xsl:output has no lever for it."""
    path, lift, _, _ = imported(tmp_path)
    out = tmp_path / "roundtrip.xml"
    dekereke.todekereke(lift, out, dekerekefilename=path)
    assert b"\r\n" in out.read_bytes()


def test_export_refuses_a_column_name_xml_cannot_write(tmp_path):
    """xsl:element aborts the run part-written on a bad name, so we check
    before starting rather than leaving a half-written database."""
    path, lift, _, map = imported(tmp_path)
    map.columns.append("2ndSpeaker")
    map.roles["2ndSpeaker"] = "field"
    map.write(dekereke.sidecarname(lift))
    with pytest.raises(dekereke.Error) as caught:
        dekereke.todekereke(lift, tmp_path / "out.xml", dekerekefilename=path)
    assert "2ndSpeaker" in str(caught.value)


# --- the whole path a user actually takes ------------------------------------

@pytest.mark.integration
def test_a_dekereke_database_becomes_a_project_azt_can_open(tmp_path, monkeypatch):
    """End to end: pick a Dekereke file, confirm the columns, and A-Z+T opens
    the result as a project — the path the Import option in the database
    chooser runs."""
    import types

    from backend.core import templates
    from utilities import file as fileutil

    monkeypatch.setattr(fileutil, "gethome", lambda: tmp_path)

    class Languages:
        def get_obj(self, code):
            from backend import langtags

            return langtags.langcodes.Language.get(code)

    program = types.SimpleNamespace(languages=Languages(), name="A-Z+T")
    dk, map = mapped(write(tmp_path))
    template = templates.Dekereke(
        program, source=dk, columnmap=map, analang="fau")

    assert template.error_text is None
    assert template.entries == 1
    assert len(template.db.senses) == 1
    assert template.db.analangs == ["fau"]
    assert template.db.glosslangs == ["id"]
    assert dekereke.sidecarname(template.filename).exists()


@pytest.mark.integration
def test_cancelling_the_column_dialog_leaves_no_project(tmp_path):
    """A template built without a language code must do nothing at all, since
    that is what the chooser constructs when the user cancels."""
    import types

    from backend.core import templates

    template = templates.Dekereke(types.SimpleNamespace(name="A-Z+T"))
    assert template.db is None
    assert template.entries == 0


# --- a researcher's curated syllable profiles --------------------------------

def profiled(tmp_path, role):
    """A database whose SyllableProfile column the researcher filled in."""
    path = write(tmp_path)
    path.write_bytes(path.read_bytes().replace(
        b"<Tulisan>tei</Tulisan>",
        b"<Tulisan>tei</Tulisan><SyllableProfile>CVV</SyllableProfile>"))
    dk, map = mapped(path)
    map.roles["SyllableProfile"] = role
    lift = tmp_path / "SampleLang.lift"
    dekereke.tolift(dk, map, lift)
    return lxml.etree.parse(str(lift))


def test_a_checked_profile_column_is_imported_as_confirmed(tmp_path):
    """A-Z+T slices by the confirmed profile and never overwrites it, so a
    column the researcher curated by hand must land in the plain form — that
    is what makes A-Z+T defer to their analysis instead of its own guess."""
    tree = profiled(tmp_path, "cvprofileok")
    assert tree.xpath("//field[@type='cvprofile_lc']"
                      "/form[@lang='fau-x-cvprofile']/text/text()") == ["CVV"]


def test_an_unchecked_profile_column_is_imported_as_a_guess(tmp_path):
    """Auto-generated profiles go in the machine form, where A-Z+T treats them
    as something still to be checked."""
    tree = profiled(tmp_path, "cvprofile")
    assert tree.xpath("//field[@type='cvprofile_lc']"
                      "/form[@lang='fau-x-cvprofile_MT']/text/text()") == ["CVV"]
    assert not tree.xpath("//form[@lang='fau-x-cvprofile']")
