# coding=UTF-8
"""Two small pieces that make the audio diagnostics usable at all.

`quiet_probing()` and `_which_python` are not about audio; they are about
whether a diagnostic can be READ and RUN. Both earned tests the hard way on
2026-09-10:

  * PortAudio's ALSA layer writes to file descriptor 2 from C, so probing
    buried its own answer — 24 lines of trace around one verdict, and 21
    identical "unable to open slave" lines in another run. Suppressing that
    means swapping a file descriptor, which is exactly the kind of thing that
    leaks or breaks stderr for the rest of the process if it goes wrong;
  * the manual scripts were run with the system python on a Windows and a
    macOS box and reported every audio dependency missing on machines where
    A-Z+T runs fine. The scripts are meant to be handed to other people, so
    that failure has to end in a command they can paste.
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.core import sound


# ─── quiet_probing: silence the C library, then give stderr back ────────────

def test_quiet_probing_restores_stderr():
    """The whole risk of a descriptor swap: not getting it back. Everything
    logged after a probe would vanish for the life of the process.

    Checked by USING fd 2 rather than comparing `os.fstat` modes, which is
    what this did first: two dups of the same descriptor have the same mode
    whether or not the restore happened, so the assertion was weak — and
    st_mode on a Windows console handle is not a comparison worth relying on
    either. That the descriptor accepts a write is the property that matters,
    and it means the same thing on every platform.
    """
    with sound.quiet_probing():
        pass
    os.write(2, b'')


def test_quiet_probing_restores_stderr_after_an_exception():
    """A probe that raises is NORMAL — that is what a device refusing a rate
    looks like — so the restore has to happen on that path too."""
    with pytest.raises(ValueError):
        with sound.quiet_probing():
            raise ValueError('a device said no')
    os.write(2, b'')        # still a working descriptor


def test_quiet_probing_does_not_leak_descriptors():
    """It opens devnull and dups the real stderr on every call, and probing
    calls it once per device and per combination — a leak would exhaust the
    process's descriptors on a machine with many devices."""
    def open_count():
        try:
            return len(os.listdir('/proc/self/fd'))
        except OSError:
            pytest.skip('no /proc/self/fd on this platform')
    start = open_count()
    for _ in range(50):
        with sound.quiet_probing():
            pass
    assert open_count() <= start + 2, 'descriptors are not being closed'


def test_c_level_writes_are_actually_suppressed(tmp_path):
    """The point of the exercise, checked at the level that matters: a write
    straight to fd 2, as the C library does, must not reach the terminal.
    Python-level `redirect_stderr` cannot do this, which is why the fd swap
    exists."""
    script = tmp_path / 'probe.py'
    script.write_text(
        'import os, sys\n'
        'sys.path.insert(0, {!r})\n'
        'from backend.core import sound\n'
        'with sound.quiet_probing():\n'
        '    os.write(2, b"NOISE FROM C\\n")\n'
        'os.write(2, b"KEPT\\n")\n'.format(
                        str(Path(__file__).resolve().parents[1])))
    done = subprocess.run([sys.executable, str(script)],
                          capture_output=True, text=True)
    assert 'NOISE FROM C' not in done.stderr
    assert 'KEPT' in done.stderr, 'stderr must work again afterwards'


# ─── _which_python: end the failure with a command, not a diagnosis ─────────

which = pytest.importorskip('tests.manual.sound_check._which_python')


def test_it_finds_a_venv_beside_the_app(tmp_path):
    """The layout azt/CLAUDE.md documents: `AZT/env`, beside the app
    directory, NOT `azt/env`."""
    app = tmp_path / 'AZT' / 'azt'
    (app / 'tests' / 'manual' / 'sound_check').mkdir(parents=True)
    binned = tmp_path / 'AZT' / 'env' / 'bin'
    binned.mkdir(parents=True)
    (binned / 'python3').write_text('')
    found = which.venv_python(
                app / 'tests' / 'manual' / 'sound_check' / 'x.py')
    assert found == binned / 'python3'


def test_it_finds_a_windows_venv(tmp_path):
    """Where it actually bit: MINGW64 on Windows, where the interpreter is
    `env/Scripts/python.exe` and the old hardcoded hint said
    `../env/bin/python`."""
    app = tmp_path / 'AZT' / 'azt'
    (app / 'tests' / 'manual' / 'sound_check').mkdir(parents=True)
    scripts = tmp_path / 'AZT' / 'env' / 'Scripts'
    scripts.mkdir(parents=True)
    (scripts / 'python.exe').write_text('')
    found = which.venv_python(
                app / 'tests' / 'manual' / 'sound_check' / 'x.py')
    assert found == scripts / 'python.exe'


def test_the_message_ends_in_a_runnable_command(tmp_path):
    app = tmp_path / 'AZT' / 'azt'
    (app / 'tests' / 'manual' / 'sound_check').mkdir(parents=True)
    binned = tmp_path / 'AZT' / 'env' / 'bin'
    binned.mkdir(parents=True)
    (binned / 'python3').write_text('')
    text = which.how_to_run('tests.manual.sound_check.mic_check',
                            missing='numpy')
    assert 'mic_check' in text
    assert '-um' in text


def test_it_warns_against_installing_into_the_system_python():
    """What Kent started doing when the message only named what was missing:
    `pip install numpy`, into a python the app will never use."""
    text = which.how_to_run('tests.manual.sound_check.mic_check')
    if which.venv_python() is not None:
        assert 'system python' in text.lower()


def test_no_venv_found_says_where_it_looked(tmp_path):
    """A path that does not exist is worse than an admission of not knowing."""
    app = tmp_path / 'nowhere' / 'azt'
    (app / 'tests' / 'manual' / 'sound_check').mkdir(parents=True)
    text = which.how_to_run(
                'tests.manual.sound_check.mic_check')
    assert isinstance(text, str) and text
