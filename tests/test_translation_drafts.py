"""Drafted translations waiting for a speaker's check (2026-10-19).

translations/drafts/<lang>_*.po are merged into the catalogs by
translations/merge_drafts.py, marked fuzzy. Before that, each draft must
parse, have a translation, and keep the source's
{placeholders} exactly: a missing or renamed one makes .format() raise
in the running program.
"""
import importlib.util
import pathlib

import pytest

AZT = pathlib.Path(__file__).resolve().parent.parent
TR = AZT / 'translations'
DRAFTS = sorted((TR / 'drafts').glob('*.po')) if (TR / 'drafts').exists() \
    else []


def _merge_module():
    spec = importlib.util.spec_from_file_location(
        'merge_drafts', TR / 'merge_drafts.py')
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


@pytest.fixture(scope='module')
def md():
    return _merge_module()


@pytest.mark.skipif(not DRAFTS, reason='no drafts waiting')
@pytest.mark.parametrize('path', DRAFTS, ids=lambda p: p.name)
def test_a_draft_file_is_usable(path, md):
    # A string missing from azt.pot is NOT a problem: the merge keeps its
    # translation in case the string is used again (Kent 2026-11-12).
    entries = md.parse(path.read_text('utf-8'))[0]
    assert entries, f'{path.name}: no entries parsed'
    bad = []
    for e in entries:
        why = md.problems(e)
        if why:
            bad.append(f'{why}: {e["msgid"][:80]!r}')
    assert not bad, f'{path.name}: {len(bad)} unusable\n' + '\n'.join(bad)


def test_an_entry_with_no_blank_line_before_the_next_is_still_two(md):
    """Older catalogs run entries together; that read as one garbled entry,
    both looked missing, and the merge appended duplicates (2026-10-19)."""
    entries = md.parse('msgid "a"\nmsgstr "A"\n#: x.py:1\nmsgid "b"\n'
                       'msgstr "B"\nmsgid "c"\nmsgstr "C"\n')[0]
    assert [(e['msgid'], e['msgstr']) for e in entries] == \
        [('a', 'A'), ('b', 'B'), ('c', 'C')]


def test_merging_fills_gaps_and_never_overwrites(md, tmp_path, monkeypatch):
    lang = tmp_path / 'xx_XX' / 'LC_MESSAGES'
    lang.mkdir(parents=True)
    (tmp_path / 'azt.pot').write_text(
        'msgid "a {n}"\nmsgstr ""\n\nmsgid "b"\nmsgstr ""\n\n'
        'msgid "c"\nmsgstr ""\n', encoding='utf-8')
    (lang / 'azt.po').write_text(
        'msgid "b"\nmsgstr "kept"\n\nmsgid "c"\nmsgstr ""\n',
        encoding='utf-8')
    monkeypatch.setattr(md, 'HERE', tmp_path)
    drafts = md.parse('msgid "a {n}"\nmsgstr "A {n}"\n\n'
                      'msgid "b"\nmsgstr "NOT THIS"\n\n'
                      'msgid "c"\nmsgstr "C"\n\n'
                      'msgid "gone"\nmsgstr "G"\n')[0]
    appended, filled, skipped = md.merge('xx_XX', drafts)
    po = md.parse((lang / 'azt.po').read_text('utf-8'))[0]
    got = {e['msgid']: (e['msgstr'], 'fuzzy' in e['flags']) for e in po}
    assert got['b'] == ('kept', False), "a translation is never touched"
    assert got['c'] == ('C', True)
    assert got['a {n}'] == ('A {n}', True)
    # A string no longer in azt.pot is still kept: it may be used again
    # (Kent 2026-11-12).
    assert got['gone'] == ('G', True) and appended == 2 and filled == 1
    gone = next(e for e in po if e['msgid'] == 'gone')
    assert any('Not in azt.pot' in c for c in gone['comments'])


def test_a_merged_draft_is_deleted(md, tmp_path):
    """Drafts used to stay for good, and a string later removed from the
    code failed a draft merged weeks before (Kent 2026-11-12). "gone"
    (not in azt.pot) is in the catalog now too, so the draft holds
    nothing the catalog lacks."""
    f = tmp_path / 'xx_XX_done.po'
    f.write_text('#, fuzzy\nmsgid "a"\nmsgstr "A"\n\n'
                 'msgid "gone"\nmsgstr "G"\n', encoding='utf-8')
    assert md.retire(f) == []
    assert not f.exists()


def test_a_draft_keeps_only_what_still_needs_a_person(md, tmp_path):
    f = tmp_path / 'xx_XX_part.po'
    f.write_text('msgid "a"\nmsgstr "A"\n\n'
                 '# CHECK: n is a count\n'
                 'msgid "b {n}"\nmsgstr "B {m}"\n\n'
                 'msgid "c"\nmsgstr ""\n', encoding='utf-8')
    kept = md.retire(f)
    assert [e['msgid'] for e in kept] == ['b {n}', 'c']
    left = md.parse(f.read_text('utf-8'))[0]
    assert [(e['msgid'], e['msgstr']) for e in left] == \
        [('b {n}', 'B {m}'), ('c', '')]
    assert '# CHECK: n is a count' in f.read_text('utf-8')


def test_a_dry_run_changes_no_draft(md, tmp_path):
    f = tmp_path / 'xx_XX_done.po'
    text = 'msgid "a"\nmsgstr "A"\n'
    f.write_text(text, encoding='utf-8')
    md.retire(f, dry_run=True)
    assert f.read_text('utf-8') == text
