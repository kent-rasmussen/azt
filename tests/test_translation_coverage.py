"""Translation coverage for French and Mandarin (Kent, 2026-10-19).

Two questions, each its own test, each listing what is missing:
1. Does `translations/azt.pot` hold every literal `_("…")` in the program?
2. Does each of fr_FR and zh_CN translate every msgid in azt.pot (an
   entry, a non-empty msgstr, not marked fuzzy)?

The .po reader here is deliberately small: it handles continuation lines,
flags, msgctxt and obsolete (#~) entries, which is all these files use.
"""
import ast
import pathlib

import pytest

AZT = pathlib.Path(__file__).resolve().parent.parent
TRANSLATIONS = AZT / 'translations'
LANGS = ['fr_FR', 'zh_CN']
SKIP_DIRS = {'tests', 'env', 'env3.14', 'translations', 'xlptransforms',
             '.buildozer', '__pycache__', 'userlogs', 'docs'}


def _unquote(s):
    return ast.literal_eval(s)


def read_po(path):
    """{msgid: (msgstr, fuzzy)} for the live entries of a .po/.pot."""
    entries = {}
    cur = None
    field = None
    fuzzy = False

    def flush():
        if cur and cur.get('msgid'):
            key = (cur.get('msgctxt'), cur['msgid'])
            entries[key] = (cur.get('msgstr', ''), cur['fuzzy'])

    for raw in path.read_text(encoding='utf-8').splitlines():
        line = raw.strip()
        # A comment or msgctxt/msgid after a msgstr also starts a new entry:
        # older catalogs omit the blank line, and splitting only on blank
        # lines read such a pair as one garbled entry (2026-10-19).
        starts_new = (cur is not None and field == 'msgstr'
                      and (line.startswith('#') or line.startswith('msgctxt ')
                           or line.startswith('msgid ')))
        if not line or starts_new:
            flush()
            cur, field, fuzzy = None, None, False
            if not line:
                continue
        if line.startswith('#~'):
            continue                    # obsolete
        if line.startswith('#,'):
            fuzzy = fuzzy or 'fuzzy' in line
            continue
        if line.startswith('#'):
            continue
        if cur is None:
            cur = {'fuzzy': fuzzy}
        for kw in ('msgctxt', 'msgid_plural', 'msgid', 'msgstr[0]',
                   'msgstr'):
            if line.startswith(kw + ' '):
                field = 'msgstr' if kw.startswith('msgstr') else kw
                cur[field] = cur.get(field, '') + _unquote(
                    line[len(kw) + 1:])
                break
        else:
            if line.startswith('"') and field:
                cur[field] = cur.get(field, '') + _unquote(line)
    flush()
    return entries


def code_msgids():
    """{msgid: 'file:line'} for every _("literal") and N_("literal")."""
    found = {}
    for p in sorted(AZT.rglob('*.py')):
        rel = p.relative_to(AZT)
        if SKIP_DIRS & set(rel.parts[:-1]) or rel.name == 'test.py':
            continue
        try:
            tree = ast.parse(p.read_text(encoding='utf-8'))
        except (SyntaxError, UnicodeDecodeError):
            continue
        for node in ast.walk(tree):
            if (isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name)
                    and node.func.id in ('_', 'N_') and node.args
                    and isinstance(node.args[0], ast.Constant)
                    and isinstance(node.args[0].value, str)
                    and node.args[0].value):
                found.setdefault(node.args[0].value,
                                 f'{rel}:{node.lineno}')
    return found


@pytest.fixture(scope='module')
def pot():
    path = TRANSLATIONS / 'azt.pot'
    if not path.exists():
        pytest.skip('no azt.pot')
    return read_po(path)


def _report(title, items, limit=400):
    items = sorted(items)
    shown = '\n'.join(items[:limit])
    more = f'\n… and {len(items) - limit} more' if len(items) > limit else ''
    return f'{title}: {len(items)}\n{shown}{more}'


def test_the_template_holds_every_string_in_the_code(pot):
    in_pot = {msgid for _ctx, msgid in pot}
    missing = {f'{where}  {msgid!r}' for msgid, where in code_msgids().items()
               if msgid not in in_pot}
    # translations/extract.py (xgettext --keyword=_ over every .py) makes
    # azt.pot; a failure here only means it hasn't been run since these
    # strings were added — run it, don't edit azt.pot by hand.
    assert not missing, _report('Strings in the code but not in azt.pot '
                                '(run translations/extract.py)', missing)


@pytest.mark.parametrize('lang', LANGS)
def test_a_catalog_defines_each_message_once(lang):
    """msgfmt refuses a catalog with a duplicate msgid ("duplicate message
    definition"), so nothing compiles for that language."""
    path = TRANSLATIONS / lang / 'LC_MESSAGES' / 'azt.po'
    if not path.exists():
        pytest.skip(f'no {lang} catalog')
    seen, dupes = set(), []
    text = path.read_text(encoding='utf-8')
    for e in _all_entries(text):
        if e in seen:
            dupes.append(repr(e[1][:80]))
        seen.add(e)
    assert not dupes, f'{lang}: duplicate entries:\n' + '\n'.join(dupes)


def _all_entries(text):
    """Every live (ctx, msgid) in order, duplicates included (read_po keeps
    only the last of a duplicate, so it can't count them)."""
    keys = []
    cur_id, cur_ctx, field = None, None, None
    for raw in text.splitlines() + ['']:
        line = raw.strip()
        if line.startswith('#~'):
            continue
        if (not line or line.startswith('#') or line.startswith('msgctxt ')
                or line.startswith('msgid ')) and field == 'msgstr':
            if cur_id:
                keys.append((cur_ctx, cur_id))
            cur_id, cur_ctx, field = None, None, None
        if line.startswith('msgctxt '):
            cur_ctx, field = _unquote(line[8:]), 'msgctxt'
        elif line.startswith('msgid '):
            cur_id, field = _unquote(line[6:]), 'msgid'
        elif line.startswith('msgstr'):
            field = 'msgstr'
        elif line.startswith('"') and field == 'msgid':
            cur_id += _unquote(line)
        elif line.startswith('"') and field == 'msgctxt':
            cur_ctx += _unquote(line)
    return keys


def use_fuzzy():
    """translations/compile.py's USE_FUZZY: whether fuzzy (drafted, not yet
    checked) entries are compiled in. When they are, they are what users
    see, so they count as translated here; when not, they are reported only
    as a count, not listed one by one."""
    import importlib.util
    import contextlib
    import io
    spec = importlib.util.spec_from_file_location(
        'azt_translations_compile', TRANSLATIONS / 'compile.py')
    mod = importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(io.StringIO()):  # it prints on import
        spec.loader.exec_module(mod)
    return bool(getattr(mod, 'USE_FUZZY', False))


@pytest.mark.parametrize('lang', LANGS)
def test_every_template_string_is_translated(pot, lang):
    path = TRANSLATIONS / lang / 'LC_MESSAGES' / 'azt.po'
    if not path.exists():
        pytest.skip(f'no {lang} catalog')
    po = read_po(path)
    fuzzy_ok = use_fuzzy()
    absent, empty, fuzzy = set(), set(), set()
    for key in pot:
        msgid = key[1]
        if key not in po:
            absent.add(repr(msgid))
        elif not po[key][0]:
            empty.add(repr(msgid))
        elif po[key][1]:
            fuzzy.add(repr(msgid))
    problems = len(absent) + len(empty) + (0 if fuzzy_ok else len(fuzzy))
    report = [f'{lang}: {problems} of {len(pot)} template strings not usable'
              f' (USE_FUZZY={fuzzy_ok})',
              _report('No entry', absent),
              _report('Empty translation', empty)]
    if not fuzzy_ok and fuzzy:
        report.append(f'Marked fuzzy (awaiting a speaker; set USE_FUZZY in '
                      f'translations/compile.py to use them): {len(fuzzy)}')
    assert not problems, '\n\n'.join(report)
