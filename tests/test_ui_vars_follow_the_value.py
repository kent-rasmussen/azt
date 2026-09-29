"""A status label must show THIS task's value, not the last one's.

Kent, 2026-09-29, after opening Sort Consonants and coming back: *"just
went to SortC and back, and it still said vowels."* On a page whose cvt is
unambiguously `'C'` — `Consonants.cvt='C'`, applied by `Task.__init__`
before the window exists — so the VALUE was never wrong. The label was.

`get_ui_var` caches one StringVar per attribute for the SESSION, and every
status label asks for one with the text it has just computed:

    get_ui_var('cvt_label', self.cvtlabel())

The cached branch returned the existing var and dropped that text on the
floor, so the settings line froze at whatever wrote it first. Nothing
repainted it on a plain task open either: `update_all_labels` runs on
settings CHANGES. The family affected is every prose label —
`cvt_label`, `cvcheck_label`, `ps_label`, `profile_label`,
`fields<ps>_label`, `wordcheck_label` and the rest.

HEADLESS: `get_ui_var` does `from frontend import ui` and builds a
`ui.StringVar`, which under the tkinter backend wants a root. The
standalone `ui_variables.StringVar` is the same contract without one (it
exists for the webview backend), so it stands in here — what is under test
is `get_ui_var`'s branching, not a toolkit.
"""
import types

import pytest

from frontend import ui_variables
from settings import Settings


@pytest.fixture(autouse=True)
def _ns(monkeypatch):
    """A fresh cache per test, and a Variable that needs no display."""
    from frontend import ui
    monkeypatch.setattr(ui, 'StringVar', ui_variables.StringVar,
                        raising=False)
    return types.SimpleNamespace(ui_vars={})


def _get(ns, attr, value=None):
    return Settings.get_ui_var(ns, attr, value)


def test_the_first_call_creates_the_var_with_the_value(_ns):
    assert _get(_ns, 'cvt_label', 'Checking Vowels,').get() \
        == 'Checking Vowels,'


def test_a_later_call_applies_the_new_value(_ns):
    """THE REGRESSION. The second task of a session computes its own label
    and must not be handed the first task's."""
    _get(_ns, 'cvt_label', 'Checking Vowels,')
    var = _get(_ns, 'cvt_label', 'Checking Consonants,')
    assert var.get() == 'Checking Consonants,', \
        'the freshly computed label was discarded for the cached one'


def test_the_same_var_object_is_reused(_ns):
    """Reuse is the point of the cache — widgets and `trace_add` callbacks
    bind to the object, so replacing it would orphan them."""
    first = _get(_ns, 'cvt_label', 'a')
    assert _get(_ns, 'cvt_label', 'b') is first


def test_passing_no_value_leaves_the_var_alone(_ns):
    """The `trace_add` registrations (`ui_shell.py:1409`, `:1459`) ask for
    the var, not for a value, and must not blank it."""
    _get(_ns, 'toneframe_label', 'working on ‘H’ tone frame')
    assert _get(_ns, 'toneframe_label').get() == 'working on ‘H’ tone frame'


def test_the_value_is_stringified(_ns):
    """`maxslice_label` and friends hand in numbers."""
    assert _get(_ns, 'maxslice_label', 50).get() == '50'
    assert _get(_ns, 'maxslice_label', 25).get() == '25'


def test_updatecvt_refreshes_before_it_renders():
    """The second half of the same bug: `cvtlabel()` reads `self.cvt`, and
    `makesliceattrs` is what re-reads that from `params` — so painting
    first rendered the PREVIOUS cvt on every explicit update."""
    import inspect
    from frontend import ui_shell
    src = inspect.getsource(ui_shell.StatusFrame.updatecvt)
    assert src.index('makesliceattrs') < src.index("labels['cvt']"), \
        'updatecvt must refresh self.cvt before rendering a label from it'
