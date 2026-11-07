"""Find words borrows the ASR's loaded mms-1b-all only when no ASR holds it (backend/core/texts.py loaded_mms)."""
import threading
from types import SimpleNamespace

import pytest


def _texts():
    try:
        from backend.core import texts
    except Exception as e:  # heavy imports; skip if the env can't load them
        pytest.skip(f"backend.core.texts import failed: {e}")
    return texts


def _program(lock):
    pipe = SimpleNamespace(model=object(), feature_extractor=object())
    asr = SimpleNamespace(models={'facebook/mms-1b-all': pipe}, mms_lock=lock)
    return SimpleNamespace(soundsettings=SimpleNamespace(asr=asr)), pipe


def test_borrowing_takes_the_lock():
    texts = _texts()
    lock = threading.Lock()
    program, pipe = _program(lock)
    got = texts.loaded_mms(program)
    assert got == (pipe.model, pipe.feature_extractor, lock)
    assert lock.locked()


def test_a_busy_asr_means_no_borrowing_and_no_wait():
    texts = _texts()
    lock = threading.Lock()
    lock.acquire()
    program, _pipe = _program(lock)
    assert texts.loaded_mms(program) is None


def test_nothing_loaded_means_nothing_borrowed():
    texts = _texts()
    program = SimpleNamespace(soundsettings=SimpleNamespace(asr=SimpleNamespace(models={},
                                                                                mms_lock=threading.Lock())))
    assert texts.loaded_mms(program) is None
    assert texts.loaded_mms(SimpleNamespace()) is None
