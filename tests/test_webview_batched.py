"""ui.batched(): layout calls (grid / grid_remove) made inside it reach the
page in one evaluate_js per window, and any other call sends what is held
first, so order never changes. Added 2026-11-12: a sameSort split on a
346-row verify page moved every later row one round trip at a time (9-12s)."""
import pytest


class FakeWindow:
    def __init__(self):
        self.calls = []

    def evaluate_js(self, code):
        self.calls.append(code)
        return 'result'


@pytest.fixture
def wv(monkeypatch):
    wv = pytest.importorskip('frontend.ui_webview')
    monkeypatch.setattr(wv._started, 'is_set', lambda: True)
    return wv


def test_layout_calls_go_in_one_round_trip(wv):
    w = FakeWindow()
    with wv.batched():
        for i in range(250):
            wv._js(w, f'gridWidget({i}, {{}})', fire=True)
        assert w.calls == []  # nothing sent yet
    assert len(w.calls) == 3  # _JS_BATCH=100 per evaluate_js
    sent = ''.join(w.calls)
    assert sent.index('gridWidget(0,') < sent.index('gridWidget(249,')


def test_a_call_that_may_be_read_sends_the_held_ones_first(wv):
    w = FakeWindow()
    with wv.batched():
        wv._js(w, 'gridWidget(1, {})', fire=True)
        assert wv._js(w, 'measure()') == 'result'
        assert len(w.calls) == 2
        assert 'gridWidget(1,' in w.calls[0] and w.calls[1] == 'measure()'
    assert len(w.calls) == 2  # nothing left to send on exit


def test_outside_a_batch_each_call_goes_at_once(wv):
    w = FakeWindow()
    wv._js(w, 'gridWidget(1, {})', fire=True)
    assert w.calls == ['gridWidget(1, {})']


def test_nested_batches_send_only_at_the_outermost_exit(wv):
    w = FakeWindow()
    with wv.batched():
        with wv.batched():
            wv._js(w, 'gridWidget(1, {})', fire=True)
        assert w.calls == []
    assert len(w.calls) == 1


def test_tkinter_has_it_too():
    tk = pytest.importorskip('frontend.ui_tkinter')
    with tk.batched():
        pass
