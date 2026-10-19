#!/usr/bin/env python3
"""Merge drafted translations into the catalogs, for a speaker to check.

    python translations/merge_drafts.py            # every translations/drafts/<lang>_*.po
    python translations/merge_drafts.py --dry-run  # say what would change

Each draft file holds .po entries for ONE language (the file name starts
with the language folder's name, e.g. fr_FR_part1.po). For each entry:

  * the msgid must be in azt.pot (else it is skipped: the string is gone);
  * if the catalog has no entry for it, the entry is APPENDED;
  * if the catalog's entry has an EMPTY msgstr, the draft fills it;
  * a catalog entry that already has a translation is NEVER touched.

Every merged entry is marked `fuzzy`. msgfmt (translations/compile.py)
leaves fuzzy entries out of the .mo, so nothing unchecked reaches users;
a checker accepts an entry by removing "fuzzy" from its "#," line.
"""
import argparse
import ast
import pathlib
import re

HERE = pathlib.Path(__file__).resolve().parent
DRAFTS = HERE / 'drafts'
BRACES = re.compile(r'\{[^{}]*\}')


def _unquote(s):
    return ast.literal_eval(s)


def _quote(s):
    return '"' + (s.replace('\\', '\\\\').replace('"', '\\"')
                   .replace('\n', '\\n').replace('\t', '\\t')) + '"'


def parse(text):
    """[entry] where entry = {'flags': set, 'comments': [str],
    'msgctxt', 'msgid', 'msgstr', 'start', 'end'} (line indexes)."""
    lines = text.splitlines()
    entries, cur, field = [], None, None
    for i, raw in enumerate(lines + ['']):
        line = raw.strip()
        # A NEW ENTRY ALSO STARTS where a comment or msgctxt/msgid follows a
        # msgstr with no blank line between — valid PO, and present in the
        # older catalogs. Splitting only on blank lines merged such pairs
        # into one garbled entry, so both read as missing and a merge
        # appended duplicates msgfmt then refused (2026-10-19).
        starts_new = (cur is not None and (field or '').startswith('msgstr')
                      and (line.startswith('#') or line.startswith('msgctxt ')
                           or line.startswith('msgid ')))
        if not line or starts_new:
            if cur is not None and 'msgid' in cur:
                cur['end'] = i
                entries.append(cur)
            cur, field = None, None
            if not line:
                continue
        if cur is None:
            cur = {'flags': set(), 'comments': [], 'start': i}
        if line.startswith('#~'):
            cur['obsolete'] = True
            continue
        if line.startswith('#,'):
            cur['flags'] |= {f.strip() for f in line[2:].split(',')
                             if f.strip()}
            continue
        if line.startswith('#'):
            cur['comments'].append(raw)
            continue
        m = re.match(r'(msgctxt|msgid_plural|msgid|msgstr(\[\d+\])?) (".*")$',
                     line)
        if m:
            field = m.group(1)
            cur[field] = cur.get(field, '') + _unquote(m.group(3))
        elif line.startswith('"') and field:
            cur[field] = cur.get(field, '') + _unquote(line)
    return [e for e in entries if not e.get('obsolete')], lines


def render(e):
    out = [c for c in e['comments']]
    if e['flags']:
        out.append('#, ' + ', '.join(sorted(e['flags'])))
    if e.get('msgctxt') is not None:
        out.append('msgctxt ' + _quote(e['msgctxt']))
    out.append('msgid ' + _quote(e['msgid']))
    out.append('msgstr ' + _quote(e['msgstr']))
    return out


def problems(e):
    """Why a draft can't be used as it stands, or ''."""
    if not e.get('msgstr'):
        return 'empty translation'
    if sorted(BRACES.findall(e['msgid'])) != sorted(BRACES.findall(
                                                        e['msgstr'])):
        return 'placeholders differ: {} vs {}'.format(
            BRACES.findall(e['msgid']), BRACES.findall(e['msgstr']))
    return ''


def merge(lang, drafts, dry_run=False):
    po_path = HERE / lang / 'LC_MESSAGES' / 'azt.po'
    pot_ids = {(e.get('msgctxt'), e['msgid'])
               for e in parse((HERE / 'azt.pot').read_text('utf-8'))[0]}
    entries, lines = parse(po_path.read_text('utf-8'))
    by_key = {(e.get('msgctxt'), e['msgid']): e for e in entries}
    appended, filled, skipped = [], 0, []
    replace = {}  # start line -> (end line, new lines)
    for d in drafts:
        key = (d.get('msgctxt'), d['msgid'])
        why = problems(d)
        if key not in pot_ids:
            why = why or 'not in azt.pot'
        if why:
            skipped.append((d['msgid'], why))
            continue
        d['flags'] = set(d['flags']) | {'fuzzy'}
        have = by_key.get(key)
        if have is None:
            appended.append(d)
            by_key[key] = d
        elif not have.get('msgstr'):
            new = dict(have, msgstr=d['msgstr'],
                       flags=have['flags'] | {'fuzzy'},
                       comments=have['comments'] + [
                           c for c in d['comments'] if c.startswith('# ')])
            replace[have['start']] = (have['end'], render(new))
            filled += 1
        # else: already translated; never touched
    out, i = [], 0
    while i < len(lines):
        if i in replace:
            end, new = replace[i]
            out.extend(new)
            i = end
        else:
            out.append(lines[i])
            i += 1
    for d in appended:
        out.append('')
        out.extend(render(d))
    print(f'{lang}: {len(appended)} appended, {filled} filled, '
          f'{len(skipped)} skipped')
    for msgid, why in skipped:
        print(f'  skipped ({why}): {msgid[:70]!r}')
    if not dry_run and (appended or filled):
        po_path.write_text('\n'.join(out) + '\n', encoding='utf-8')
    return len(appended), filled, skipped


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--dry-run', action='store_true',
                    help='report what would change; write nothing')
    args = ap.parse_args()
    by_lang = {}
    for f in sorted(DRAFTS.glob('*.po')):
        lang = next((d.name for d in HERE.iterdir()
                     if d.is_dir() and f.name.startswith(d.name + '_')), None)
        if lang is None:
            print(f'{f.name}: no language folder matches its name; skipped')
            continue
        by_lang.setdefault(lang, []).extend(parse(f.read_text('utf-8'))[0])
    for lang, drafts in sorted(by_lang.items()):
        merge(lang, drafts, dry_run=args.dry_run)


if __name__ == '__main__':
    main()
