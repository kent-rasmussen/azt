# coding=UTF-8
"""The two backend-parity checks that actually ASSERT something.

The inventories live in `tests/manual/backend_surface_parity.py`, which is
also where the machinery is — this module imports it. Kent, 2026-09-11: "more
of a manual test than a regression protection, right? any reason to not put it
in manual?" None, and the split is sharper than manual-vs-suite: the two
inventories were `xfail`, so they could never fail the suite and protected
nothing. They are lists for a person to triage.

What belongs here is what breaks a build:

  * the widget classes both backends need must exist in both;
  * the three classes that bit us on 2026-09-11 must stay complete.

`ContextMenu` is why any of this exists: a stub that satisfied its ABC
completely while implementing none of the members the app calls, so the app
ran to completion against a menu that was not there — and Sound Settings, its
only route from a task window, was unreachable under webview.
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

parity = pytest.importorskip('tests.manual.backend_surface_parity',
                             reason='needs the parity report importable')


def test_both_backends_define_the_same_widget_classes():
    """A class missing outright is the bluntest gap: every call site for it
    fails, and usually at import or construction rather than in a callback
    where it would be swallowed."""
    shared_worth_having = {
        'Window', 'Toplevel', 'Frame', 'Label', 'Button', 'Entry',
        'EntryField', 'CheckButton', 'RadioButton', 'ListBox', 'Combobox',
        'Progressbar', 'ScrollingFrame', 'Menu', 'ContextMenu', 'ToolTip',
        'Theme', 'Style', 'Image', 'Notebook', 'ButtonFrame',
    }
    missing = sorted(c for c in shared_worth_having
                     if c in parity.TK and c not in parity.WV)
    assert not missing, "webview has no class for: {}".format(missing)


@pytest.mark.parametrize('cls', ['ContextMenu', 'Menu', 'ToolTip'])
def test_the_classes_that_bit_us_are_complete(cls):
    """Pinned so they cannot regress. Declared members only — resolving
    inheritance here reports the shared tkinter mixins (`inherit`,
    `is_descendant_of`) as gaps in every class, which they are not."""
    found = parity.gaps(cls)
    assert not found, \
        "webview {} is missing: {}".format(cls, sorted(found))
