"""The XLingPaper → TeX → PDF path in `io_put/xlp.py` (2026-10-15).

What stopped it, each tested here:
* `file.getstylesheetdir`/`gettransformsdir` looked in utilities/, not at
  the top of the program, so neither folder was ever found.
* The character conversion ran over the whole serialized document and could
  not put the tags back; it now converts text only, in one pass.
* Non-ASCII ids (ŋ, ɛ, tone letters…) reach TeX labels unconverted.
* The transforms still called Saxon-only functions lxml doesn't have.

xelatex itself is not run here: the pipeline test stops at the .tex file.
"""
from types import SimpleNamespace

import pytest

xlp = pytest.importorskip('io_put.xlp')
rx = pytest.importorskip('utilities.rx')
file = pytest.importorskip('utilities.file')


def test_the_xlingpaper_folders_are_found():
    assert file.exists(file.gettransformsdir()), file.gettransformsdir()
    assert file.exists(file.getstylesheetdir('/nowhere/report.xml'))


def test_text_conversion_is_one_pass():
    assert rx.texmllike_text('\\') == '\\textbackslash{}', \
        "the braces it writes must not be escaped again"
    assert rx.texmllike_text('a_b & c%') == 'a\\_b \\& c\\%'
    assert rx.texmllike_text('{x}') == '\\{x\\}'
    assert rx.texmllike_text('<') == '\\textless{}'
    assert rx.texmllike_text('ŋɔ́ ˥˩') == 'ŋɔ́ ˥˩', "letters pass through"
    assert rx.texmllike_text(None) is None


def test_tree_conversion_leaves_markup_alone():
    lxml = pytest.importorskip('lxml.etree')
    root = lxml.fromstring('<a x="_">1_2<b>$</b>tail#</a>')
    rx.texmllike_tree(root)
    assert root.get('x') == '_', "attributes untouched"
    assert root.text == '1\\_2'
    assert root[0].text == '\\textdollar{}'
    assert root[0].tail == 'tail\\#'


def test_non_ascii_ids_and_their_references_convert_together():
    lxml = pytest.importorskip('lxml.etree')
    root = lxml.fromstring(
        '<p><example num="ŋa"/><exampleRef num="ŋa"/>'
        '<section1 id="ŋa"/><x lang="en" name="ŋb"/></p>')
    xlp.ascii_ids(root)
    assert root.find('section1').get('id') == '14Ba'
    assert root.find('exampleRef').get('num') == '14Ba'
    assert root.find('x').get('lang') == 'en'
    assert root.find('x').get('name') == 'ŋb', "not an id: left alone"


def test_no_saxon_only_functions_left_in_the_transforms():
    import pathlib
    import re
    d = pathlib.Path(file.gettransformsdir())
    calls = {p.name: len(re.findall(r'saxon:[a-z-]+\(', p.read_text(
                                                encoding='utf-8')))
             for p in d.glob('*.xsl')}
    assert not {k: v for k, v in calls.items() if v}


def test_a_finished_pdf_is_shown_and_a_missing_one_is_not(tmp_path,
                                                          monkeypatch):
    utilities = pytest.importorskip('utilities.utilities')
    opened = []
    monkeypatch.setattr(utilities, 'open_file', opened.append)
    pdf = tmp_path / 'r.pdf'
    assert utilities.show_finished_pdf(pdf) is False and not opened
    pdf.write_bytes(b'%PDF-1.4')
    assert utilities.show_finished_pdf(pdf) is True
    assert opened == [str(pdf)]


def test_every_pdf_maker_shows_its_pdf_through_one_helper():
    """Kent, 2026-10-19: "make this general". The three PDF makers (report,
    alphabet chart, booklet) call show_finished_pdf, not open_file."""
    import pathlib
    root = pathlib.Path(file.__file__).resolve().parent.parent
    for rel in ('io_put/xlp.py', 'frontend/alphabet_chart.py',
                'backend/core/alphabet.py'):
        src = (root / rel).read_text(encoding='utf-8')
        assert 'show_finished_pdf(' in src, rel
        assert 'import open_file' not in src, rel


def test_a_small_report_transforms_all_the_way_to_tex(tmp_path, monkeypatch):
    """The whole XSLT chain on a real (small) report. Stops before xelatex,
    which isn't assumed to be installed."""
    pytest.importorskip('lxml.etree')
    import shutil
    monkeypatch.setattr(shutil, 'which', lambda name: None)
    fn = str(tmp_path / 'r_ReportXLP.xml')
    r = xlp.Report(fn, 'Test', 'English', SimpleNamespace(name='A-Z+T'))
    assert hasattr(r, 'node')
    r.addlang({'id': 'xyz', 'name': 'Xyz'})
    s = xlp.Section(r, 'Noun CVC ŋa_1 & more')
    xlp.Paragraph(s, 'Words with {braces}, 50% and a_b.')
    r.close(me=False)
    assert (tmp_path / 'r_ReportXLP.xml').exists()
    r.compile()
    tex = tmp_path / 'r_ReportXLP.tex'
    assert tex.exists(), "the XSLT chain stopped; see the log"
    text = tex.read_text(encoding='utf-8')
    assert '\\documentclass' in text
    assert '50\\%' in text and 'a\\_b' in text
