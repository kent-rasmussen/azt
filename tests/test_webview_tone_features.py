# coding=UTF-8
"""Tone letters are asked to drop their staves on every webview page.

Kent, 2026-09-22: "I see ligatures working correctly, but staves are there;
not sure if that's a bug or not asking." Not asking: theme.css defined four
`.tone-*` classes and nothing in the app ever applied one. Under tkinter the
same machine renders staveless wherever a -tstv font file exists, and ADR
0004 D4 says the browser is to get that from the OpenType feature — so the
feature is now on at the root. The two classes that ask for a DIFFERENT
variant (numbers, Chinantec) ask for that alone: there are no staves on a
number, so cv92 beside cv91 would be noise (Kent: "numbers without staves?").

Also here, for the same reason (a tkinter shape the app grids itself): a
`render=True` entry field must carry a `rendered` label.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSS = (ROOT / 'frontend' / 'webview_html' / 'theme.css').read_text()
PY = (ROOT / 'frontend' / 'ui_webview.py').read_text()


def _rules(selector):
    """Every rule body for `selector`, joined. A stylesheet may declare the
    same selector more than once — theme.css has a `:root` block for its
    variables AND one for the tone feature — and the first version of this
    helper stopped at the first match and missed the second."""
    bodies = re.findall(r'(?m)^' + re.escape(selector) + r'\s*\{([^}]*)\}', CSS)
    assert bodies, "no rule for {}".format(selector)
    return '\n'.join(bodies)


def test_staveless_is_asked_for_on_every_element():
    """`*`, not `:root`: form controls get a user-agent `font` shorthand that
    resets font-feature-settings, and a declared value beats inheritance, so
    a :root rule missed the transcriber's entry and the sort buttons."""
    assert '"cv92" 1' in _rules('*')


def test_number_and_chinantec_variants_ask_for_their_own_feature_only():
    assert '"cv91" 1' in _rules('.tone-numbers')
    assert 'cv92' not in _rules('.tone-numbers')
    assert '"cv90" 1' in _rules('.tone-chinantec')
    assert 'cv92' not in _rules('.tone-chinantec')


def test_staves_remain_an_explicit_opt_out():
    assert '"cv92" 0' in _rules('.tone-staves')


def test_a_rendered_entry_field_has_its_rendered_label():
    """`lexicon.py:970` grids `formfield.rendered` itself; the attribute has
    to exist on this backend even though the bitmap mechanism does not."""
    cls = PY[PY.index('class EntryField('):]
    cls = cls[:cls.index('\nclass ', 1)]
    assert 'self.rendered = Label(' in cls
