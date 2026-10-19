"""Prose lines are ONE translated sentence each (Kent, 2026-10-19).

Converting the status lines to click-to-edit values had split each sentence
into fragments ("Using", "Meanings in", "and", "words ({count})") that a
translator saw with no idea what followed and no way to move the value.
`StatusFrame.prose_sentence` now takes one template with a {slot} per value
and cuts it in the TRANSLATION's order. And text defined where `_()` can't
run (task titles, menu lists, the task's word-check sentence) is marked
`N_()` so xgettext collects it.
"""
import ast
import pathlib

import pytest

ui_shell = pytest.importorskip('frontend.ui_shell')
SF = ui_shell.StatusFrame
AZT = pathlib.Path(__file__).resolve().parent.parent


def parts(template, slots, fmt=None):
    # No instance state is used: the class carries the patterns.
    return SF._sentence_parts(SF, template, set(slots), fmt)


def test_a_one_value_sentence_is_cut_at_its_slot():
    order, texts, delims = parts('Using {lang}', ['lang'])
    assert order == ['lang'] and texts == ['Using', '']
    assert delims == {'lang': ('', '')}


def test_the_translation_decides_the_order_of_the_values():
    order, texts, _d = parts('{ps} : {profile} を見る', ['profile', 'ps'])
    assert order == ['ps', 'profile']
    assert texts == ['', ':', 'を見る']


def test_other_placeholders_are_filled_and_slots_are_not():
    order, texts, _d = parts('Looking at {profile} {ps} words ({count})',
                             ['profile', 'ps'], {'count': 51})
    assert order == ['profile', 'ps']
    assert texts == ['Looking at', '', 'words (51)']


def test_punctuation_touching_a_slot_becomes_its_delimiter():
    order, texts, delims = parts(
        'Using second form field ‘{field}’ ({ps})', ['field'], {'ps': 'Noun'})
    assert delims['field'] == ('‘', '’'), "quotes stay tight to the value"
    assert texts == ['Using second form field', '(Noun)']


def test_a_comma_after_a_value_is_its_closing_delimiter():
    order, texts, delims = parts('Checking {cvt}, working on {check}',
                                 ['cvt', 'check'])
    assert delims['cvt'] == ('', ',')
    assert texts == ['Checking', 'working on', '']


def test_a_slot_the_template_lacks_is_simply_not_drawn():
    order, _t, _d = parts('Looking at {profile} words', ['form', 'profile'])
    assert order == ['profile']


def test_the_fragment_prefixes_are_gone_from_the_status_lines():
    """No prose line may hand prosefield a bare translated fragment again."""
    src = (AZT / 'frontend' / 'ui_shell.py').read_text(encoding='utf-8')
    tree = ast.parse(src)
    bad = []
    for node in ast.walk(tree):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and node.func.attr == 'prosefield'
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == 'self' and len(node.args) > 1):
            a = node.args[1]
            if (isinstance(a, ast.Call) and getattr(a.func, 'id', '') == '_'):
                bad.append(node.lineno)
    assert not bad, f'prosefield called with a translated fragment at {bad}'


def _class_attr_literals(names):
    """(file, line, attr) for each `attr = "literal"` in a class body."""
    found = []
    for p in sorted(AZT.rglob('*.py')):
        rel = p.relative_to(AZT)
        if rel.parts[0] in ('tests', 'env', 'translations', 'docs'):
            continue
        try:
            tree = ast.parse(p.read_text(encoding='utf-8'))
        except (SyntaxError, UnicodeDecodeError):
            continue
        for cls in [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]:
            for st in cls.body:
                if (isinstance(st, ast.Assign) and len(st.targets) == 1
                        and isinstance(st.targets[0], ast.Name)
                        and st.targets[0].id in names
                        and isinstance(st.value, ast.Constant)
                        and isinstance(st.value.value, str)):
                    found.append(f'{rel}:{st.lineno} {st.targets[0].id}')
    return found


def test_task_titles_and_word_check_sentences_are_marked_for_extraction():
    bare = _class_attr_literals({'tasktitle', 'word_check_sentence',
                                 'word_check_prefix'})
    assert not bare, ('wrap these in N_() so xgettext sees them:\n'
                      + '\n'.join(bare))


def test_no_f_string_is_handed_to_the_translator():
    """_(f"…") is filled in before the lookup, so it never matches."""
    bad = []
    for p in sorted(AZT.rglob('*.py')):
        rel = p.relative_to(AZT)
        if rel.parts[0] in ('tests', 'env', 'translations', 'docs'):
            continue
        try:
            tree = ast.parse(p.read_text(encoding='utf-8'))
        except (SyntaxError, UnicodeDecodeError):
            continue
        for node in ast.walk(tree):
            if (isinstance(node, ast.Call)
                    and getattr(node.func, 'id', '') in ('_', 'N_')
                    and node.args and isinstance(node.args[0], ast.JoinedStr)):
                bad.append(f'{rel}:{node.lineno}')
    assert not bad, 'f-string inside _(): ' + ', '.join(bad)
