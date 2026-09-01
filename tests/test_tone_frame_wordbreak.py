"""The tone-frame word-break rule (added in v1.14.x).

Kent's rule, 2026-08-31: a frame form is separated from the neighbouring word
by a space IF AND ONLY IF the word-break box is checked, WHATEVER the user
typed. The box is the authority — which is the point of the feature, since a
leading, trailing or absent space are indistinguishable on screen, so the space
is otherwise something you acquire by accident and cannot audit afterwards.

This writes to the frame definition, so the rule is tested rather than trusted.
The real methods are invoked with a fake `self` (the `waiting()` contract tests
use the same trick): they touch only `forms` and `fields`, so this exercises the
actual code path with no Tk.
"""
import pytest

tasks = pytest.importorskip("tasks.tasks")
TFD = tasks.ToneFrameDrafter


class _Box:
    """Stand-in for the checkbox's BooleanVar."""
    def __init__(self, checked):
        self.checked = checked

    def get(self):
        return self.checked


class _Fake:
    """Only what the composition methods actually read."""
    WORDBREAK_MARK = TFD.WORDBREAK_MARK
    STRUCTURAL = TFD.STRUCTURAL
    _value = TFD._value
    _wordbreak = TFD._wordbreak
    _compose = TFD._compose
    _display = TFD._display

    def __init__(self, stored='', checked=False, placeholder='______'):
        self.forms = {'lg': {'before': stored, 'after': stored}}
        self.fields = {
            ('lg', 'before'): {'wordbreak': _Box(checked),
                               'placeholder': placeholder},
            ('lg', 'after'): {'wordbreak': _Box(checked),
                              'placeholder': placeholder},
        }


@pytest.mark.parametrize("typed", ["la", "la ", "la   ", "la\t"])
def test_checked_gives_exactly_one_trailing_space(typed):
    """'before' abuts the word on its right. Checked means one space there —
    from any of: none typed, one typed, several typed."""
    assert _Fake(checked=True)._compose(('lg', 'before'), typed) == "la "


@pytest.mark.parametrize("typed", ["la", "la ", "la   "])
def test_unchecked_removes_the_boundary_space(typed):
    """Unchecked is an assertion, not a default: a space the user typed does
    not survive it. That is what stops an invisible character being smuggled
    past the box."""
    assert _Fake(checked=False)._compose(('lg', 'before'), typed) == "la"


@pytest.mark.parametrize("typed,expected", [("la", " la"), ("  la", " la")])
def test_after_is_mirrored_onto_the_leading_edge(typed, expected):
    """'after' abuts the word on its LEFT, so its boundary is the other end."""
    assert _Fake(checked=True)._compose(('lg', 'after'), typed) == expected


def test_far_edge_is_left_alone():
    """Only the word boundary is the box's business. Trimming the far edge too
    would be an edit nobody asked for."""
    assert _Fake(checked=False)._compose(('lg', 'before'), "  la") == "  la"
    assert _Fake(checked=False)._compose(('lg', 'after'), "la  ") == "la  "


def test_box_state_is_derived_from_the_stored_form():
    """On open the box must describe the definition so far (Kent), so the page
    can never claim something the stored form does not say."""
    assert _Fake(stored="la ")._wordbreak(('lg', 'before')) is True
    assert _Fake(stored="la")._wordbreak(('lg', 'before')) is False
    assert _Fake(stored=" la")._wordbreak(('lg', 'after')) is True
    assert _Fake(stored="la")._wordbreak(('lg', 'after')) is False


def test_display_marks_the_break_and_never_stores_the_mark():
    """The mark exists so a break is visible on the button; it is presentation
    only, and must never reach the value."""
    f = _Fake(stored="la ")
    shown = f._display(('lg', 'before'))
    assert shown == "la" + TFD.WORDBREAK_MARK
    assert TFD.WORDBREAK_MARK not in f.forms['lg']['before']
    assert _Fake(stored="la")._display(('lg', 'before')) == "la"


def test_empty_value_shows_its_placeholder():
    assert _Fake(stored="")._display(('lg', 'before')) == "______"
