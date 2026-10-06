"""Every switch the code tests for is in `--help`, and vice versa.

A-Z+T has no argument parser: each switch is an independent membership test
against `sys.argv`, made wherever it matters. That is a deliberate choice —
several switches are passed THROUGH rather than consumed, so a parser that
refused unknown arguments would break callers that work today — but it means
nothing forces the documentation to keep up.

`utilities/switches.py` is therefore a hand-written list, and this is what
stops it drifting. The list it replaced (a block in `azt/CLAUDE.md`) had
already drifted: it was missing `--no-window-focus`, `--gtk-theme=`,
`--no-install` and `--restart`, and it was not visible to users at all.

Source-scanning, so it stays true without a display or a project.
"""
import pathlib
import re

import pytest

from utilities import switches

ROOT = pathlib.Path(__file__).resolve().parent.parent

# Where switches are read. `frontend/ui_webview.py` goes through `_switch` /
# `_switch_value`; the rest test `sys.argv` directly.
SOURCES = ('main.py', 'utilities/ui_backend.py', 'utilities/duplicates.py',
           'utilities/utilities.py', 'utilities/restartmark.py',
           'frontend/ui_webview.py', 'frontend/ui_shell.py')

# Switches that exist but are NOT the user's to type, so they stay out of the
# list on purpose. Keep this short and say why for each.
UNDOCUMENTED_ON_PURPOSE = {
    # A pip argument that happens to appear in the same files.
    '--system-site-packages', '--extra-index-url', '--index-url',
    '--retries', '--timeout',
    # Dead: the mixed-mode subprocess architecture (ADR 0004 dropped D7).
    '--serve',
    # Renamed to `--console`; a test asserts these stay gone.
    '--webview-devtools', '--no-webview-devtools',
}

SWITCH_RE = re.compile(r"""['"](--[a-z][a-z0-9-]*)['"]|(--[a-z][a-z0-9-]*)=""")


def _switches_in_source(strict):
    """Switch names found in the files that read switches.

    TWO SCANS, BECAUSE THE TWO DIRECTIONS FAIL DIFFERENTLY, and the first
    run got this wrong by using one for both.

    `strict=True` counts only lines that visibly TEST for a switch
    (`sys.argv` or `_switch` on the line). Used by "is everything
    documented?", where counting a switch merely NAMED in prose would demand
    documentation for something that does not exist.

    `strict=False` counts any switch-shaped literal in those files. Used by
    "does the help invent switches?", where over-counting only makes the
    test more permissive — and under-counting is what failed: the names are
    often not on the line that reads them. `ui_backend.py` lists
    `'--webview'`/`'--tkinter'` on one line and tests `sys.argv` on another;
    `ui_webview.py` holds `--gdk-backend`/`--qt-platform` in a dict."""
    found = {}
    for rel in SOURCES:
        path = ROOT / rel
        if not path.exists():
            continue
        for n, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
            code = line.split('#', 1)[0]
            if strict and not ('sys.argv' in code or '_switch' in code):
                continue
            for quoted, prefixed in SWITCH_RE.findall(code):
                name = (quoted or prefixed)
                if name in UNDOCUMENTED_ON_PURPOSE:
                    continue
                found.setdefault(name, '{}:{}'.format(rel, n))
    return found


def test_the_help_lists_every_switch_the_code_reads():
    """The direction that matters: a switch nobody can discover."""
    documented = switches.names()
    missing = {s: where for s, where in _switches_in_source(strict=True).items()
               if s not in documented}
    assert not missing, (
        'these switches are read but not in `--help`:\n  '
        + '\n  '.join('{}  ({})'.format(s, w) for s, w in sorted(missing.items())))


def test_the_help_does_not_invent_switches():
    """The other direction: documentation for something that does nothing."""
    in_source = set(_switches_in_source(strict=False))
    # `--help` itself is handled in `utilities.switches`, which is not one of
    # the scanned files, so the scan never finds it.
    extra = switches.names() - in_source - {'--help'}
    assert not extra, (
        '`--help` lists switches nothing reads: ' + ', '.join(sorted(extra)))


def test_the_help_says_it_is_not_a_parser():
    """Kent, 2026-09-30: "be clear in the --help what you're doing, so users
    don't think we're using argparse." A user who assumes argparse will
    expect a typo to be refused; it is silently ignored."""
    text = switches.help_text()
    assert 'NOT A PARSER' in text
    assert 'IGNORED' in text or 'ignored' in text


def test_help_costs_nothing_heavy():
    """It runs before the duplicate gate and before `py_modules`, so it must
    not need anything that is not in the standard library."""
    import ast
    src = (ROOT / 'utilities' / 'switches.py').read_text(encoding='utf-8')
    imported = set()
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.Import):
            imported |= {a.name.split('.')[0] for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split('.')[0])
    assert imported <= {'sys'}, \
        'switches.py must stay stdlib-only and tiny; found {}'.format(imported)


def test_main_asks_before_it_builds_anything():
    """Position is the feature: `--help` on a machine with no venv must
    answer, not install."""
    src = (ROOT / 'main.py').read_text(encoding='utf-8')
    assert 'switches.maybe_help()' in src
    assert src.index('switches.maybe_help()') < src.index('import utilities.py_modules'), \
        '--help must be answered before py_modules builds the venv'


@pytest.mark.parametrize('name', ['--webview', '--tkinter', '--console',
                                  '--no-kiosk', '--dmabuf', '--log-resizes',
                                  '--no-window-focus', '--gtk-theme',
                                  '--no-install', '--restart'])
def test_the_known_switches_survive(name):
    """Including the four the CLAUDE.md list had lost."""
    assert name in switches.names()
