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
