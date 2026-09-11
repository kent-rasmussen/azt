# coding=UTF-8
"""One source of truth for dependencies: requirements.txt.

WHY. `utilities/py_modules.py` carried a hand-written list of packages beside
`requirements.txt`, so the two drifted — and a python list cannot hold a PEP
508 marker, which is how a Mac came to be asked for `torch==2.7.1+cpu`:

    ERROR: No matching distribution found for torch==2.7.1+cpu
                                             (from versions: none)

twice per pass, offline then online, while requirements.txt held the correct
`torch==2.7.1; sys_platform == "darwin"` all along (measured 2026-09-10). The
list's own comments said "keep in step with requirements.txt" in two places;
it could not.

The list is gone. The per-package fallback — which exists because
`pip install -r` is all-or-nothing, so one unavailable package otherwise
costs the user numpy and sound as well — now derives its work from the file,
one requirement per invocation, markers and options passed through verbatim.

These tests pin that derivation, and the one platform decision a marker
cannot express.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from utilities import py_modules

APP = Path(__file__).resolve().parents[1]


def flat(entries):
    return [item for entry in entries for item in entry]


# ─── The derivation ─────────────────────────────────────────────────────────

def test_every_requirement_becomes_its_own_pip_invocation():
    """One package per call is the whole point: a failure is then contained
    to the package that failed, instead of costing the user every other
    package in the file."""
    entries = py_modules.requirements_one_at_a_time(str(APP))
    assert len(entries) > 20, 'requirements.txt should yield many entries'
    names = [e[0] for e in entries]
    assert any(n.startswith('numpy') for n in names)
    assert any(n.startswith('sounddevice') for n in names)
    assert any(n.startswith('soundfile') for n in names)


def test_markers_are_passed_through_verbatim():
    """THE REGRESSION. The marker is what makes one line right on Linux and
    another right on macOS; pip evaluates it when given on the command line,
    so it must arrive intact rather than being re-expressed in python."""
    names = [e[0] for e in py_modules.requirements_one_at_a_time(str(APP))]
    torch_lines = [n for n in names if n.startswith('torch')]
    assert len(torch_lines) == 2, 'both platform torch lines must survive'
    assert any('sys_platform != "darwin"' in n and '+cpu' in n
               for n in torch_lines), 'the Linux/Windows CPU pin'
    assert any('sys_platform == "darwin"' in n and '+cpu' not in n
               for n in torch_lines), \
        'the macOS line must NOT ask for +cpu — no such build exists'


def test_pip_option_lines_apply_to_every_requirement():
    """`--extra-index-url` is a global option in requirements.txt, and an
    EXTRA index is additive — pip searches PyPI as well, so it is harmless on
    platforms that want the plain wheel and finds nothing there. It has to
    ride along with each invocation or the pytorch pin cannot resolve."""
    entries = py_modules.requirements_one_at_a_time(str(APP))
    for entry in entries:
        assert '--extra-index-url' in entry, \
            'every invocation needs the option lines from the file'
        assert 'https://download.pytorch.org/whl/cpu' in entry


def test_comments_do_not_leak_into_requirements():
    """Half the file is commentary, including trailing comments on lines that
    also carry a marker containing punctuation."""
    for entry in py_modules.requirements_one_at_a_time(str(APP)):
        assert '#' not in entry[0]
        assert entry[0].strip() == entry[0]


def test_a_missing_requirements_file_is_survivable(tmp_path):
    """The fallback runs when things are already broken; it must not add a
    traceback to that."""
    assert py_modules.requirements_one_at_a_time(str(tmp_path)) == []


# ─── The one thing a marker cannot say ──────────────────────────────────────

def test_source_only_packages_are_dropped_on_a_mac_without_tools(monkeypatch):
    """A marker can test the platform; it cannot test whether developer tools
    are installed. On such a Mac the install runs `--only-binary :all:` by
    design, so a package with no wheel can never arrive — and saying so beats
    a failure nobody can act on."""
    monkeypatch.setattr(py_modules, '_mac_without_compiler', lambda: True)
    entries = [['numpy'], ['openai_whisper; sys_platform != "darwin"'],
               ['soundfile']]
    kept = flat(py_modules.drop_what_cannot_build(entries))
    assert not any(k.startswith('openai_whisper') for k in kept)
    assert 'numpy' in kept and 'soundfile' in kept


def test_nothing_is_dropped_where_it_could_be_built(monkeypatch):
    monkeypatch.setattr(py_modules, '_mac_without_compiler', lambda: False)
    entries = [['numpy'], ['openai_whisper'], ['soundfile']]
    assert py_modules.drop_what_cannot_build(entries) == entries


def test_dropping_survives_marker_and_extra_syntax(monkeypatch):
    """Requirement lines carry markers, extras and pins; the name has to be
    recovered from all three shapes or the wrong thing gets dropped."""
    monkeypatch.setattr(py_modules, '_mac_without_compiler', lambda: True)
    kept = flat(py_modules.drop_what_cannot_build(
                    [['huggingface_hub[hf_xet]'], ['numpy>=2.1,<2.5'],
                     ['openai_whisper; sys_platform != "darwin"']]))
    assert 'huggingface_hub[hf_xet]' in kept
    assert 'numpy>=2.1,<2.5' in kept
    assert not any(k.startswith('openai_whisper') for k in kept)


# ─── The file itself still says what the code assumes ───────────────────────

def test_requirements_txt_still_carries_both_torch_lines():
    """If the markers are ever simplified back to one torch line, the macOS
    install breaks again and nothing else here would notice."""
    req = (APP / 'requirements.txt').read_text()
    assert 'sys_platform == "darwin"' in req
    assert 'torch==2.7.1;' in req


def test_the_macos_torch_line_is_restricted_to_apple_silicon():
    """PyTorch ABANDONED macOS x86_64 after the 2.2.x series, so 2.7.1 does
    not exist for an Intel Mac — measured 2026-09-11, "No matching
    distribution found for torch==2.7.1 (from versions: none)" on
    Darwin_i386. Without the chip in the marker, every Intel Mac fails that
    requirement on every install."""
    req = (APP / 'requirements.txt').read_text()
    darwin_torch = [l for l in req.splitlines()
                    if l.startswith('torch') and 'darwin"' in l
                    and '+cpu' not in l]
    assert darwin_torch, 'the macOS torch line went missing'
    assert all('arm64' in l for l in darwin_torch), \
        'the macOS torch pin must require arm64; Intel Macs have no such wheel'


def test_transcription_engines_are_not_treated_as_mandatory():
    """The bug that made a COMPLETE install reinstall on every open.

    `py_modules` decides whether to run the installer from a block of
    imports, and `torch`/`whisper` sat in it. Those are absent by design on
    platforms where no wheel exists (Intel macOS since torch 2.2.x), so the
    block raised on every boot however complete the install was, and the
    per-package backstop ran every time — trying to install packages that
    cannot exist there.

    Checked with `ast`, not by slicing the text: the first attempt split on
    "except Exception as e:" and cut the file at an EARLIER handler, so the
    test failed on its own string surgery rather than on the code. The
    property is structural, so ask the structure.
    """
    import ast
    tree = ast.parse((APP / 'utilities' / 'py_modules.py').read_text())

    def imported(node):
        names = set()
        for child in ast.walk(node):
            if isinstance(child, ast.Import):
                names.update(a.name.split('.')[0] for a in child.names)
        return names

    def calls_the_installer(handlers):
        for handler in handlers:
            for child in ast.walk(handler):
                if (isinstance(child, ast.Call)
                        and getattr(child.func, 'id', '') == 'pip_install'):
                    return True
        return False

    for node in ast.walk(tree):
        if not isinstance(node, ast.Try):
            continue
        if not calls_the_installer(node.handlers):
            continue
        got = imported(node) & {'torch', 'whisper'}
        assert not got, (
            'the block that decides to run the installer imports {} — absent '
            'by design on some platforms, so it would reinstall on every '
            'open there'.format(', '.join(sorted(got))))


def test_NOTHING_that_mutates_the_machine_runs_on_import():
    """EVERY import-time call must be behind the test guard, not the two I
    happened to think of.

    A first pass gated `ensure_sister_repos()` and `pip_install()` and missed
    `sync_requirements()` — which is the bulk `pip install -r` — so a test run
    still ran pip wherever the requirements stamp did not match. That read as
    a Windows-versus-macOS difference (the Mac's stamp matched, so its call
    returned early) and was nothing of the kind. Enumerating the calls
    instead of naming them is what makes this test worth having; `ensure_venv`
    was the third, and it can relaunch the process with the current argv.
    """
    import ast
    tree = ast.parse((APP / 'utilities' / 'py_modules.py').read_text())
    dangerous = {'ensure_venv', 'sync_requirements', 'pip_install',
                 'ensure_sister_repos'}
    unguarded = []
    for node in tree.body:      # MODULE LEVEL only
        if (isinstance(node, ast.Expr) and isinstance(node.value, ast.Call)
                and getattr(node.value.func, 'id', '') in dangerous):
            unguarded.append(node.value.func.id)
    assert not unguarded, (
        '{} run(s) at import time with no test guard — importing this module '
        'would change the machine'.format(', '.join(unguarded)))
    # And the guard has to be the thing wrapping them.
    guarded = set()
    for node in tree.body:
        if not isinstance(node, ast.If):
            continue
        for child in ast.walk(node):
            if (isinstance(child, ast.Call)
                    and getattr(child.func, 'id', '') in dangerous):
                guarded.add(child.func.id)
    assert {'ensure_venv', 'sync_requirements'} <= guarded, \
        'ensure_venv and sync_requirements must both be behind the guard'


def test_requirements_txt_declares_everything_the_app_must_import():
    """The fallback can only repair what the file names, so an unconditional
    import that is not declared is unrepairable. `soundfile` and
    `sounddevice` are both here because the sounddevice port added the first
    and replaced pyaudio with the second."""
    req = (APP / 'requirements.txt').read_text()
    for package in ('numpy', 'sounddevice', 'soundfile', 'scipy', 'Pillow',
                    'lxml', 'psutil'):
        assert package in req, \
            '{} is imported unconditionally but not in requirements.txt' \
            .format(package)
