# coding=UTF-8
"""Playing a SPAN of a longer recording, and play-all's chaining.

Text words have no cut files: each word's audio form is a W3C media
fragment into the story recording ('story.ogg#t=12.340,12.810'). These
guard the three pieces that make that playable (Kent 2026-11-05):

  * the fragment round trip (io_put/lift.py split_media_fragment /
    media_fragment) — the format the form stores;
  * SoundFilePlayer playing just the span, RETURNING ITS DURATION (play-all
    chains on it: sounddevice.play() returns at once, so it is the only
    clock), and keeping the decoded recording in memory so word after word
    of one story doesn't re-read the whole file;
  * PlayAll stepping row to row on those durations, and stopping when told,
    when the page goes, and when the row list changes.

Headless: fake soundfile/sounddevice/ffmpeg and fake widgets; no audio
device, no display.
"""
import types

import pytest

io_sound = pytest.importorskip('io_put.sound')
numpy = pytest.importorskip('numpy')


# ─── the stored format ─────────────────────────────────────────────────────

def test_media_fragment_round_trip():
    lift = pytest.importorskip('io_put.lift')
    value = lift.media_fragment('story.ogg', 12.34, 12.81)
    assert value == 'story.ogg#t=12.340,12.810'
    name, span = lift.split_media_fragment(value)
    assert name == 'story.ogg'
    assert span == pytest.approx((12.34, 12.81))


def test_plain_filename_has_no_span():
    lift = pytest.importorskip('io_put.lift')
    assert lift.split_media_fragment('word.wav') == ('word.wav', None)


def test_open_ended_fragment():
    lift = pytest.importorskip('io_put.lift')
    assert lift.split_media_fragment('s.ogg#t=,2.5') == ('s.ogg', (None, 2.5))
    assert lift.split_media_fragment('s.ogg#t=3,') == ('s.ogg', (3.0, None))


# ─── span arithmetic ───────────────────────────────────────────────────────

def test_span_frames_cuts_at_rounded_samples():
    assert io_sound.span_frames(3000, 1000, 1.0, 1.5) == (1000, 1500)
    assert io_sound.span_frames(3000, 1000, None, 0.25) == (0, 250)
    assert io_sound.span_frames(3000, 1000, 2.0, None) == (2000, 3000)


def test_span_frames_clamps_a_span_past_the_end():
    """A stale time (a shortened file) must give a short or empty slice,
    never an error or an inverted range."""
    assert io_sound.span_frames(3000, 1000, 2.5, 9.0) == (2500, 3000)
    a, b = io_sound.span_frames(3000, 1000, 5.0, 6.0)
    assert a == b == 3000
    a, b = io_sound.span_frames(3000, 1000, 1.5, 1.0)   # end before start
    assert b >= a


# ─── the player, with fakes ────────────────────────────────────────────────

class FakeSettings:
    audio_card_out = 3

    def __init__(self):
        self.defaulted = 0

    def default_out(self):
        self.defaulted += 1


@pytest.fixture
def fakes(monkeypatch, tmp_path):
    """Fake soundfile + sounddevice, fresh caches, and a 3 s 'recording' at
    1000 Hz whose samples are their own indexes (so a slice is checkable)."""
    reads, played = [], []
    rate = 1000
    data = numpy.arange(3 * rate, dtype='int16')

    fake_sf = types.SimpleNamespace(
        read=lambda path, dtype=None: (reads.append(path) or (data, rate)),
        info=lambda path: types.SimpleNamespace(subtype='PCM_16'))

    def play(d, samplerate=None, device=None):
        played.append((d, samplerate, device))

    fake_sd = types.SimpleNamespace(play=play, stop=lambda: None)
    monkeypatch.setattr(io_sound, 'soundfile', fake_sf)
    monkeypatch.setattr(io_sound, 'sounddevice', fake_sd)
    monkeypatch.setattr(io_sound, '_LOADED', {})
    monkeypatch.setattr(io_sound, '_DECODED', {})
    story = tmp_path / 'story.wav'
    story.write_bytes(b'RIFF')          # exists, so it has an mtime
    return types.SimpleNamespace(reads=reads, played=played, data=data,
                                 rate=rate, story=str(story),
                                 tmp=tmp_path, sd=fake_sd)


def test_play_span_slices_and_returns_duration(fakes):
    p = io_sound.SoundFilePlayer(fakes.story, None, FakeSettings())
    d = p.play(start=1.0, end=1.5)
    assert d == pytest.approx(0.5)
    sent, rate, device = fakes.played[-1]
    assert rate == fakes.rate and device == 3
    assert list(sent) == list(fakes.data[1000:1500])


def test_player_span_applies_when_no_times_given(fakes):
    """A button wired as cmd=player.play plays just its word."""
    p = io_sound.SoundFilePlayer(fakes.story, None, FakeSettings(),
                                 span=(2.0, 2.25))
    assert p.play() == pytest.approx(0.25)
    assert list(fakes.played[-1][0]) == list(fakes.data[2000:2250])


def test_whole_file_duration(fakes):
    p = io_sound.SoundFilePlayer(fakes.story, None, FakeSettings())
    assert p.play() == pytest.approx(3.0)


def test_recording_is_read_once_for_many_spans(fakes):
    """Each word has its own player; all point into one recording. It is
    read once, not once per word."""
    for i in range(5):
        io_sound.SoundFilePlayer(fakes.story, None, FakeSettings(),
                                 span=(i * 0.5, i * 0.5 + 0.4)).play()
    assert len(fakes.reads) == 1
    assert len(fakes.played) == 5


def test_only_one_file_is_kept(fakes):
    other = fakes.tmp / 'other.wav'
    other.write_bytes(b'RIFF')
    io_sound.SoundFilePlayer(fakes.story, None, FakeSettings()).play()
    io_sound.SoundFilePlayer(str(other), None, FakeSettings()).play()
    io_sound.SoundFilePlayer(fakes.story, None, FakeSettings()).play()
    assert len(fakes.reads) == 3            # story evicted by other
    assert io_sound._LOADED['key'][0] == fakes.story


def test_failed_play_returns_none_after_one_retry(fakes, monkeypatch):
    calls = []

    def broken(*a, **k):
        calls.append(k)
        raise RuntimeError('no such device')

    monkeypatch.setattr(fakes.sd, 'play', broken)
    s = FakeSettings()
    p = io_sound.SoundFilePlayer(fakes.story, None, s)
    assert p.play() is None
    assert len(calls) == 2 and s.defaulted == 1   # the retry is kept


def test_retry_on_default_device_still_returns_duration(fakes, monkeypatch):
    calls = []

    def first_fails(d, samplerate=None, device=None):
        calls.append(device)
        if len(calls) == 1:
            raise RuntimeError('stale card index')

    monkeypatch.setattr(fakes.sd, 'play', first_fails)
    p = io_sound.SoundFilePlayer(fakes.story, None, FakeSettings())
    assert p.play(start=0, end=1) == pytest.approx(1.0)


def test_no_backend_returns_none(fakes, monkeypatch):
    monkeypatch.setattr(io_sound, 'sounddevice', None)
    p = io_sound.SoundFilePlayer(fakes.story, None, FakeSettings())
    assert p.play() is None


def test_compressed_recording_is_decoded_once(fakes, monkeypatch):
    """A story.ogg goes through ffmpeg; every word's player shares the one
    decode instead of each re-decoding the whole story."""
    import subprocess
    import tempfile
    src = fakes.tmp / 'story.ogg'
    src.write_bytes(b'OggS')
    outdir = fakes.tmp / 'decoded'
    outdir.mkdir()
    runs = []

    def fake_run(args, **kw):
        runs.append(args)
        with open(args[-1], 'wb') as f:
            f.write(b'RIFF')

    monkeypatch.setattr(subprocess, 'run', fake_run)
    monkeypatch.setattr(tempfile, 'gettempdir', lambda: str(outdir))
    for i in range(3):
        io_sound.SoundFilePlayer(str(src), None, FakeSettings(),
                                 span=(i, i + 0.5)).play()
    assert len(runs) == 1
    assert len(fakes.reads) == 1


# ─── PlayAll, with fake widgets ────────────────────────────────────────────

class FakeWidget:
    def __init__(self):
        self.alive = True
        self.opts = {'highlightthickness': 1, 'text': ''}
        self.scheduled = []

    def winfo_exists(self):
        return self.alive

    def __getitem__(self, k):
        return self.opts.get(k)

    def __setitem__(self, k, v):
        self.opts[k] = v

    def configure(self, **kw):
        self.opts.update(kw)

    def after(self, ms, fn):
        self.scheduled.append((ms, fn))
        return len(self.scheduled)

    def after_cancel(self, t):
        pass


class FakeScroller:
    def __init__(self):
        self.seen = []

    def see(self, w):
        self.seen.append(w)


@pytest.fixture
def playall(monkeypatch):
    pb = pytest.importorskip('frontend.play_buttons')
    monkeypatch.setattr(pb, 'sound',
                        types.SimpleNamespace(stop_playback=lambda: None))
    state = {'alive': True}
    scroller = FakeScroller()
    pa = pb.PlayAll(FakeWidget(), scroller=scroller,
                    alive=lambda: state['alive'])
    pa.button = FakeWidget()        # skip building a real ui.Button
    played = []
    frames, markers = [], []
    # Added OUT of reading order: play must follow the keys.
    for key, dur in (((1, 0), 0.5), ((0, 0), 1.0), ((2, 0), None)):
        f, m = FakeWidget(), FakeWidget()
        frames.append(f)
        markers.append(m)
        pa.add(key, f, (lambda k=key, d=dur: played.append(k) or d),
               marker=m)
    return types.SimpleNamespace(pa=pa, pb=pb, played=played, frames=frames,
                                 markers=markers, state=state,
                                 scroller=scroller)


def _run_next(t):
    ms, fn = t.pa.button.scheduled[-1]
    fn()
    return ms


def test_playall_plays_in_reading_order_on_durations(playall):
    t = playall
    t.pa.start()
    assert t.played == [(0, 0)]
    assert t.pa.button['text'] == t.pb._("Stop")
    assert t.markers[1]['text'] == t.pb.PLAYING_MARK      # row (0,0)
    assert t.frames[1]['highlightthickness'] == 3
    assert t.scroller.seen == [t.frames[1]]
    ms = _run_next(t)
    assert ms == 1000 + t.pa.GAP_MS
    assert t.played == [(0, 0), (1, 0)]
    assert t.markers[1]['text'] == ' '                    # moved on
    assert t.frames[1]['highlightthickness'] == 1         # restored
    ms = _run_next(t)
    assert ms == 500 + t.pa.GAP_MS
    ms = _run_next(t)                                      # row with no sound
    assert ms == t.pa.GAP_MS
    _run_next(t)                                           # past the end
    assert not t.pa._playing
    assert t.pa.button['text'] == t.pb._("Play all")


def test_stop_retires_the_pending_step(playall):
    t = playall
    t.pa.start()
    t.pa.toggle()                       # the button, now reading "Stop"
    assert t.pa.button['text'] == t.pb._("Play all")
    assert t.markers[1]['text'] == ' '
    _run_next(t)                        # the step scheduled before Stop
    assert t.played == [(0, 0)]


def test_removed_row_stops_playall(playall):
    t = playall
    t.pa.start()
    t.frames[0].alive = False           # user clicked a row away
    _run_next(t)
    assert t.played == [(0, 0)]
    assert not t.pa._playing


def test_page_gone_stops_playall(playall):
    t = playall
    t.pa.start()
    t.state['alive'] = False
    _run_next(t)
    assert t.played == [(0, 0)]
    assert not t.pa._playing


def test_row_without_word_is_not_registered(playall):
    t = playall
    n = len(t.pa.rows)
    t.pa.add((9, 0), FakeWidget(), None)
    assert len(t.pa.rows) == n


def test_a_frame_added_again_replaces_its_row(playall):
    """A sort-page group button rebuilds its insides when its example changes,
    and registers again: one row, the new player."""
    t = playall
    t.pa.add((5, 0), t.frames[2], lambda: t.played.append('new') or 0.1)
    assert len(t.pa.rows) == 3
    assert [r for r in t.pa.rows if r['frame'] is t.frames[2]][0]['key'] == (5, 0)


def test_keys_may_be_read_at_start(playall):
    """Group buttons re-grid as groups come and go: a function key is read at
    start, not at add."""
    t = playall
    order = {'a': 1}
    f = FakeWidget()
    t.pa.add(lambda: (order['a'], -1), f, lambda: t.played.append('moved') or 0.1)
    order['a'] = -1                      # moved to the top since it was added
    t.pa.start()
    assert t.played == ['moved']


def test_phrase_is_the_word_with_a_second_each_side():
    pb = pytest.importorskip('frontend.play_buttons')
    word = ('/p/texts/story.ogg', (12.3, 12.8))
    phrase = ('/p/texts/story.ogg', (2.0, 20.0))
    assert pb.in_context(word, phrase)[0] == '/p/texts/story.ogg'
    assert pb.in_context(word, phrase)[1] == pytest.approx((11.3, 13.8))
    near_start = ('/p/texts/story.ogg', (2.4, 2.9))
    assert pb.in_context(near_start, phrase)[1] == pytest.approx((2.0, 3.9))   # not before the phrase
    near_end = ('/p/texts/story.ogg', (19.5, 19.9))
    assert pb.in_context(near_end, phrase)[1] == pytest.approx((18.5, 20.0))
    other = ('/p/audio/take.wav', None)                          # careful take: no span
    assert pb.in_context(other, phrase) == phrase
    assert pb.in_context(('/p/texts/song.ogg', (1.0, 2.0)), phrase) == phrase


def test_word_plays_a_tenth_of_a_second_past_each_boundary():
    pb = pytest.importorskip('frontend.play_buttons')
    word = ('/p/texts/story.ogg', (12.3, 12.8))
    phrase = ('/p/texts/story.ogg', (12.25, 20.0))
    assert pb.padded(word)[1] == pytest.approx((12.2, 12.9))
    assert pb.padded(word, phrase)[1] == pytest.approx((12.25, 12.9))   # not before the phrase
    assert pb.padded(('/p/t.ogg', (0.05, 0.5)))[1] == pytest.approx((0.0, 0.6))
    whole = ('/p/audio/take.wav', None)                          # careful take: no span
    assert pb.padded(whole, phrase) == whole
