"""Forced alignment's backtrack survives more than 127 CTC states (azt_asr/wordbreaks.py ctc_viterbi).
Find words died on a long clause, 2026-11-06: 'Python integer 202 out of bounds for int8'."""
import pytest

np = pytest.importorskip('numpy')


def _wb():
    try:
        from backend.core import texts
        return texts.wordbreaks()
    except Exception as e:  # torch etc.; skip if the env can't load them
        pytest.skip(f"wordbreaks import failed: {e}")


def test_a_clause_of_more_than_127_states_aligns():
    wb = _wb()
    L, V, blank = 120, 5, 0                       # 241 states
    tokens = [1 + k % (V - 1) for k in range(L)]
    T = 2 * L + 10
    logp = np.full((T, V), -10.0)
    for t in range(T):                            # token k strongest at frames 2k, 2k+1
        k = min(t // 2, L - 1)
        logp[t, tokens[k]] = 0.0
    spans = wb.ctc_viterbi(logp, tokens, blank)
    assert spans is not None and len(spans) == L
    assert all(a <= b for a, b in spans)
    assert all(spans[k][1] < spans[k + 1][0] for k in range(L - 1))
