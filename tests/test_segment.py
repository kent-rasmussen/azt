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


@pytest.fixture
def no_silero(monkeypatch):
    """Breakpoints without Silero's probabilities: what a VAD makes of a pure tone is no test of ours."""
    def missing(audio, rate=SR):
        raise ImportError('not for this test')
    monkeypatch.setattr(texts, 'silero_probabilities', missing)


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


def test_background_noise_counts_as_a_pause():
    """Noise ~21 dB under the speech: above the old peak-25 dB threshold, so
    the pause wasn't one. The noise floor now sets the threshold."""
    audio = _audio(('tone', 1.0), ('quiet', 0.4), ('tone', 1.0))
    audio = audio + np.random.default_rng(0).normal(0, 0.03, len(audio)).astype('float32')
    _close(texts.segment(audio), [(0, 1100), (1300, 2400)])


def test_a_click_in_a_pause_doesnt_break_it():
    """15 + 15 frames of silence around one loud frame: two runs too short
    to be pauses, until the flags are smoothed."""
    audio = _audio(('tone', 1.0), ('quiet', 0.15), ('tone', 0.01), ('quiet', 0.15), ('tone', 1.0))
    _close(texts.segment(audio), [(0, 1100), (1210, 2310)])


def test_a_long_chunk_with_no_silence_is_cut_at_its_quietest():
    """10 s, no pause: cut in the dip (4.0–4.2 s, 8 dB down: not silent,
    which needs 12 dB here)."""
    t = np.arange(10 * SR) / SR
    level = np.where((t >= 4.0) & (t < 4.2), 0.2, 0.5)
    audio = (level * np.sin(2 * np.pi * 220 * t)).astype('float32')
    _close(texts.segment(audio), [(0, 4200), (4000, 10000)], ms=100)


def test_the_segmenter_switch():
    assert texts.segmenter_switch(['main.py']) == 'silero'                 # plan A, 2026-11-20
    assert texts.segmenter_switch(['main.py', '--segmenter=energy']) == 'energy'
    assert texts.segmenter_switch(['main.py', '--segmenter=nonsense']) == 'silero'


def test_a_missing_detector_falls_back_to_energy_or_raises(monkeypatch):
    def missing(audio, rate, db):
        raise ImportError('no such package')
    monkeypatch.setitem(texts.DETECTORS, 'missing', missing)
    audio = _audio(('tone', 1.0), ('quiet', 0.4), ('tone', 1.0))
    assert texts.segment(audio, detector='missing') == texts.segment(audio)
    with pytest.raises(ImportError):
        texts.segment(audio, detector='missing', fallback=False)


def test_the_comparison_has_a_tier_per_detector_that_runs(tmp_path, monkeypatch, no_silero):
    try:
        texts._azt_asr('textgrid')
    except ImportError as e:
        pytest.skip(f'azt_asr textgrid unavailable: {e}')

    def missing(audio, rate, db):
        raise ImportError('no such package')
    monkeypatch.setattr(texts, 'DETECTORS', {'energy': texts.energy_silence, 'missing': missing})
    audio = _audio(('tone', 1.0), ('quiet', 0.4), ('tone', 1.0))
    out = tmp_path / 'story_segments.TextGrid'
    found = texts.compare_segments(audio, str(out), clauses=[(0, 1100), (1300, 2400)])
    assert list(found) == ['energy']
    _close(found['energy'], [(0, 1000), (1400, 2400)])          # unpadded
    grid = out.read_text()
    assert 'name = "clauses"' in grid and 'name = "energy"' in grid and 'missing' not in grid


def test_a_detectors_own_cuts_split_a_sounding_stretch(monkeypatch):
    def with_a_cut(audio, rate, db):
        silent, note = texts.energy_silence(audio, rate, db)
        return silent, note, [150]                               # frame 150: 1.5 s
    monkeypatch.setitem(texts.DETECTORS, 'cutting', with_a_cut)
    t = np.arange(3 * SR) / SR
    audio = (0.5 * np.sin(2 * np.pi * 220 * t)).astype('float32')
    _close(texts.segment(audio, detector='cutting', pad=0), [(0, 1500), (1500, 3000)])


def test_prosody_cuts_at_a_dip_with_a_pitch_reset(monkeypatch):
    """3 s with no pause: pitch falls 240 → 180 Hz, then starts again at 260;
    the level dips 10 dB at the join. Energy keeps it whole; prosody cuts."""
    pytest.importorskip('parselmouth')
    try:
        texts._azt_asr('boundaries')
    except ImportError as e:
        pytest.skip(f'azt_asr boundaries unavailable: {e}')

    def no_silero(audio, rate, db):
        raise ImportError('not for this test')
    monkeypatch.setattr(texts, 'silero_silence', no_silero)     # pauses by energy: no VAD on a tone
    t = np.arange(3 * SR) / SR
    freq = np.where(t < 1.5, 240 - 40 * t, 260 - 40 * (t - 1.5) / 1.5)
    level = np.where((t >= 1.42) & (t < 1.58), 0.15, 0.5)
    audio = (level * np.sin(2 * np.pi * np.cumsum(freq) / SR)).astype('float32')
    _close(texts.segment(audio, pad=0), [(0, 3000)])
    _close(texts.segment(audio, detector='prosody', pad=0, fallback=False), [(0, 1500), (1500, 3000)], ms=100)


def _boundaries_or_skip():
    pytest.importorskip('parselmouth')
    try:
        texts._azt_asr('boundaries')
    except ImportError as e:
        pytest.skip(f'azt_asr boundaries unavailable: {e}')


def _two_tones(start2, gap=0.3):
    """1.5 s falling 200 → 190 Hz, `gap` s of silence, 1.5 s from `start2` Hz falling 10 Hz."""
    t = np.arange(round(1.5 * SR)) / SR
    first = 0.5 * np.sin(2 * np.pi * np.cumsum(200 - 10 * t / 1.5) / SR)
    second = 0.5 * np.sin(2 * np.pi * np.cumsum(start2 - 10 * t / 1.5) / SR)
    return np.concatenate([first, np.zeros(round(gap * SR)), second]).astype('float32')


def test_the_pause_test_joins_a_hesitation_and_keeps_a_reset(monkeypatch):
    """A 0.3 s pause: the pitch carrying on across it (190 → 189 Hz) is a
    hesitation, joined; jumping to 250 Hz is a new clause, kept."""
    _boundaries_or_skip()

    def no_silero(audio, rate, db):
        raise ImportError('not for this test')
    monkeypatch.setattr(texts, 'silero_silence', no_silero)
    carrying, resetting = _two_tones(189), _two_tones(250)
    assert len(texts.segment(carrying, pad=0)) == 2                     # energy cuts both
    _close(texts.segment(carrying, detector='prosody', pad=0, fallback=False), [(0, 3300)])
    _close(texts.segment(resetting, detector='prosody', pad=0, fallback=False), [(0, 1500), (1800, 3300)])


def test_breakpoints_are_stored_on_a_phrase_and_read_back():
    import types
    import xml.etree.ElementTree as ET
    phrase = texts.Phrase(ET.Element('phrase', {'guid': 'g'}), types.SimpleNamespace(analang='en'))
    assert phrase.breakpoints() == []
    phrase.set_breakpoints([(1200, 2.5, 1150, 1260, 18.5, 0.12), (3400, 1.0, 3380, 3420, None, None)])
    assert phrase.breakpoints() == [(1200, 2.5, 1150, 1260, 18.5, 0.12), (3400, 1.0, 3380, 3420, None, None)]
    phrase.node.find('item').text = '1200:2.5'                  # the first form: a point
    assert phrase.breakpoints() == [(1200, 2.5, 1200, 1200, None, None)]
    phrase.node.find('item').text = '1200:2.5:1150:1260'        # the second: no depth
    assert phrase.breakpoints() == [(1200, 2.5, 1150, 1260, None, None)]
    phrase.node.find('item').text = '1200:2.5:1150:1260:18.5'   # the third: no probability
    assert phrase.breakpoints() == [(1200, 2.5, 1150, 1260, 18.5, None)]


def test_the_best_breakpoint_of_a_clause_is_its_long_dip_and_a_short_one_isnt_offered(no_silero):
    """Ranked mainly by the depth over 0.2 s (and Silero's sag, left out
    here; Kent, 2026-11-20): a 0.3 s dip 10 dB down is a place; a 0.1 s one,
    which has no 0.2 s of quiet in it, is too weak to offer."""
    try:
        texts._azt_asr('boundaries')
    except ImportError as e:
        pytest.skip(f'azt_asr boundaries unavailable: {e}')
    t = np.arange(3 * SR) / SR
    long_dip = np.where((t >= 1.35) & (t < 1.65), 0.15, 0.5)
    places = texts.breakpoints_for((long_dip * np.sin(2 * np.pi * 220 * t)).astype('float32'), [(0, 3000)])[0]
    assert places and abs(places[0][0] - 1500) <= 150, places
    _ms, _score, start, end, depth, _p = places[0]
    assert 1300 <= start < end <= 1700 and end - start >= 200, places[0]   # the dip's stretch, ~300 ms
    assert depth is not None and depth >= 6, places[0]
    short_dip = np.where((t >= 1.45) & (t < 1.55), 0.15, 0.5)
    assert not texts.breakpoints_for((short_dip * np.sin(2 * np.pi * 220 * t)).astype('float32'))[0]


def test_a_pause_at_a_clause_edge_is_a_breakpoint_of_both_clauses(no_silero):
    """Breakpoints are found over the whole recording (Kent, 2026-11-20): the
    pause between two clauses is evidence for that boundary, in both."""
    try:
        texts._azt_asr('boundaries')
    except ImportError as e:
        pytest.skip(f'azt_asr boundaries unavailable: {e}')
    audio = _audio(('tone', 1.0), ('quiet', 0.4), ('tone', 1.0))
    first, second = texts.breakpoints_for(audio, [(0, 1100), (1300, 2400)])
    assert first and second
    assert first[0][2:4] == second[0][2:4]                       # the same stretch
    assert 950 <= first[0][2] and first[0][3] <= 1450, first[0]  # the pause, 1.0–1.4 s
    whole, = texts.breakpoints_for(audio)
    assert whole[0][2:4] == first[0][2:4]


def test_a_sag_in_the_vads_probability_is_a_breakpoint():
    """No silence and no dip in the level, but the VAD's speech probability
    sags 0.95 → 0.4 for 150 ms: that is a place, with its stretch and p."""
    try:
        boundaries = texts._azt_asr('boundaries')
    except ImportError as e:
        pytest.skip(f'azt_asr boundaries unavailable: {e}')
    n = 300
    db = np.full(n, -10.0)
    vad = np.full(n, 0.95)
    vad[140:155] = 0.4
    found, note = boundaries.breakpoints(np.zeros(n * 160, dtype='float32'), SR, [(0, n)],
                                         np.zeros(n, dtype=bool), db, limit=None, vad=vad)
    assert found[0], note
    c, score, s, e, _depth, p = found[0][0]
    assert 135 <= c <= 160 and s < 147 < e, found[0][0]
    assert p is not None and p < 0.7 and score > 0.4, found[0][0]


def test_a_200ms_pause_is_deep_and_a_short_dip_is_not():
    try:
        boundaries = texts._azt_asr('boundaries')
    except ImportError as e:
        pytest.skip(f'azt_asr boundaries unavailable: {e}')
    level = np.full(300, -10.0)
    level[100:125] = -40.0                    # 250 ms quiet: 200 ms of it at -40
    level[200:205] = -40.0                    # 50 ms quiet
    assert boundaries._quiet_for(level, 110, 0, 300, 20) == -40.0
    assert boundaries._quiet_for(level, 202, 0, 300, 20) == -10.0
    assert boundaries._quiet_for(level, 10, 0, 15, 20) is None


def test_continuous_sound_has_no_silence():
    """No pause anywhere: the 10th percentile is the speech itself, and must
    not make its quieter frames 'silent'."""
    t = np.arange(5 * SR) / SR
    audio = (0.5 * np.sin(2 * np.pi * 220 * t)).astype('float32')
    _close(texts.segment(audio), [(0, 5000)])
