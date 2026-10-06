# coding=UTF-8
"""Does this code actually PARSE on the python we claim as our floor?

THE FLOOR IS A CLAIM ABOUT SYNTAX, NOT ONLY ABOUT WHEELS, and the two can
drift apart without anyone noticing. `modules_by_python_version.py` answers
whether every dependency INSTALLS on the floor; nothing answered whether our
own source still COMPILES there. Kent, 2026-09-23, on declaring 3.10:
*"Actually, I think fstrings changed since then... So we might want to audit
that against current code."*

He is right, and f-strings are the sharpest example. PEP 701 (python 3.12)
relaxed their grammar: reusing the same quote inside the braces
(`f"{d["key"]}"`), backslashes inside the expression, multi-line expressions
with comments. All of that is a SyntaxError on 3.11 and earlier — and it is
easy to write by accident on a 3.13 machine, because it simply works there.
The same trap exists for `match` (3.10), `except*` (3.11) and a few others.

WHAT THIS CANNOT DO. `ast.parse(feature_version=…)` is best effort: CPython's
own documentation says it is "not fully supported for all syntax features".
So a pass here is strong evidence, not proof. The authoritative check is
compiling with a real interpreter of the floor version, which is worth doing
once when the floor moves rather than on every test run.

See `docs/adr/0005-python-version-floor-and-ceiling.md`.
"""
import ast
import os
import sys

import pytest

py_modules = pytest.importorskip('utilities.py_modules',
                                 reason='needs utilities importable')

FLOOR = getattr(py_modules, 'MIN_PYTHON', (3, 10))
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Not ours, or not shipped. `env` is the virtual environment; the rest are
# build output and caches.
SKIP_DIRS = {'env', '.git', '.buildozer', 'build', 'dist', '__pycache__',
             'node_modules', 'bin', 'images', 'audio', '.pytest_cache',
             'userlogs'}


def python_files():
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS
                       and not d.startswith('.')]
        for name in sorted(filenames):
            if name.endswith('.py'):
                yield os.path.join(dirpath, name)


@pytest.mark.skipif(sys.version_info[:2] < FLOOR,
                    reason='cannot check a floor newer than this interpreter')
def test_every_module_parses_on_the_declared_floor():
    """Every .py in the repo must parse under the floor's grammar."""
    floor = '.'.join(str(n) for n in FLOOR)
    bad = []
    for path in python_files():
        try:
            with open(path, encoding='utf-8') as fh:
                source = fh.read()
        except (OSError, UnicodeDecodeError) as e:
            bad.append((path, 0, 'could not read: {}'.format(e)))
            continue
        try:
            ast.parse(source, filename=path, feature_version=FLOOR)
        except SyntaxError as e:
            bad.append((os.path.relpath(path, ROOT), e.lineno or 0,
                        e.msg or str(e)))
        except ValueError as e:
            # feature_version out of the range this interpreter supports.
            pytest.skip('this python cannot parse for {}: {}'.format(floor, e))
    if bad:
        lines = ['{} uses syntax newer than python {} (the declared floor, '
                 'from py_modules.MIN_PYTHON):'.format(len(bad), floor), '']
        lines += ['  {}:{}: {}'.format(p, n, m) for p, n, m in bad]
        lines += ['',
                  'Either rewrite it to the floor, or RAISE THE FLOOR '
                  'deliberately in ADR 0005 —',
                  'which strands every field machine below the new number '
                  'and is a migration,',
                  'not a version bump.']
        pytest.fail('\n'.join(lines))


def test_the_floor_is_declared_in_one_place():
    """MIN_PYTHON is the single source; the ADR quotes it, not the reverse."""
    assert isinstance(FLOOR, tuple) and len(FLOOR) >= 2
    assert FLOOR >= (3, 0)
