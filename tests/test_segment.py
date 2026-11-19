"""texts.segment: a recording cut into clause chunks at pauses (2026-11-19).

A sounding stretch shorter than min_chunk joins its neighbour across the
shorter pause; it used to be dropped, leaving its audio in no phrase.
"""
import numpy as np
import pytest

texts = pytest.importorskip('backend.core.texts')
SR = texts.SR


def _audio(*parts):
    """('tone' | 'quiet', seconds) pieces, joined."""
    out = []
    for kind, s in parts:
        n = round(s * SR)
        if kind == 'tone':
            out.append(0.5 * np.sin(2 * np.pi * 220 * np.arange(n) / SR))
        else:
            out.append(np.zeros(n))
    return np.concatenate(out).astype('float32')


def _close(got, want, ms=20):
    assert len(got) == len(want), got
    for (a, b), (c, d) in zip(got, want):
        assert abs(a - c) <= ms and abs(b - d) <= ms, got


def test_a_short_stretch_joins_the_left_across_the_shorter_pause():
    audio = _audio(('tone', 1.0), ('quiet', 0.3), ('tone', 0.15), ('quiet', 0.5), ('tone', 1.0))
    # pad 0.1 s each side: (0 - 0.1 → 0, 1.45 + 0.1), (1.95 - 0.1, 2.95 → end)
    _close(texts.segment(audio), [(0, 1550), (1850, 2950)])


def test_a_short_stretch_joins_the_right_across_the_shorter_pause():
    audio = _audio(('tone', 1.0), ('quiet', 0.5), ('tone', 0.15), ('quiet', 0.3), ('tone', 1.0))
    _close(texts.segment(audio), [(0, 1100), (1400, 2950)])


def test_a_lone_short_stretch_is_kept():
    audio = _audio(('quiet', 0.5), ('tone', 0.15), ('quiet', 0.5))
    _close(texts.segment(audio), [(400, 750)])


def test_a_pause_of_a_fifth_of_a_second_splits():
    audio = _audio(('tone', 1.0), ('quiet', 0.2), ('tone', 1.0))
    _close(texts.segment(audio), [(0, 1100), (1100, 2200)])
