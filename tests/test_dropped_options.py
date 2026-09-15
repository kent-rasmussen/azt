# coding=UTF-8
"""A widget option may be dropped — but not SILENTLY.

This is the gate `agenda/webview_discards_widget_options.md` plan step 5
asks for: "every deliberate drop gets a comment… A drop with no comment then
reads as a bug, which is the only way this stops recurring."

Eleven dropped options were found in one week, every one of them because a
person noticed a PAGE looked wrong. The shape raises nothing, logs nothing
and passes every test:

    kwargs.pop('anchor', None)          # the caller asked; nothing happens

So there is no way to catch it except to look for it, and no reason to look
for it unless something looks. That is this test.

**It does not forbid dropping an option.** Plenty should be dropped — a
browser has no bitmap-text path, no tearoff menus, no focus ring to theme.
It requires only that the code SAY SO, in a comment within six lines. That
is the difference between a decision and an oversight, and it is the only
part a reader can check.

The sweep itself lives in `tests/manual/dropped_options_sweep.py`; run it by
hand to see the full report.
"""
import importlib.util
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent.parent

# KNOWN AND ACCEPTED, keyed on (file, rule, name) so the baseline survives
# edits above them. Line numbers would go stale on the next change and a
# guard that cries wolf gets switched off — which is how the class comes
# back.
ACCEPTED = {
    # FIXED 2026-09-14: `anchor` now reaches Tk from `TextBase.post_tk_init`.
    # The attribute is still stored and still read by nothing, which is what
    # the sweep sees — it is the historical artefact, not the bug. Remove
    # this line if `self.anchor` is ever deleted.
    ('frontend/ui_tkinter.py', 'D2', 'anchor'),
    # NOT A FAULT: `self.compound` is read by `getattr(self, k)` in
    # `restore_kwargs`, iterating `Text.tk_textkwargs`, which contains
    # 'compound'. The sweep says as much in its message. This is exactly the
    # pair that makes the rule worth having: 'anchor' is in no such set and
    # was never restored; 'compound' is, and always was.
    ('frontend/ui_tkinter.py', 'D2', 'compound'),
}


def _load_sweep():
    path = HERE / 'tests' / 'manual' / 'dropped_options_sweep.py'
    if not path.exists():
        pytest.skip("dropped_options_sweep.py is not in this checkout")
    spec = importlib.util.spec_from_file_location('dropped_options_sweep',
                                                  path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules['dropped_options_sweep'] = mod
    spec.loader.exec_module(mod)
    return mod


def test_no_unexplained_dropped_options():
    """Every `kwargs.pop` that discards an option must say why."""
    sweep = _load_sweep()
    unexpected = []
    for rel, rule, name, lineno, why, text in sweep.findings():
        if (rel, rule, name) in ACCEPTED:
            continue
        unexpected.append("{}:{}: [{}] {}\n        {}".format(
                            rel, lineno, rule, why, text))
    assert not unexpected, (
        "A widget option is being accepted and thrown away with nothing "
        "saying why. Either honour it, or drop it with a comment giving the "
        "reason (a browser has no bitmap-text path, no tearoff menus, and so "
        "on) — a drop with no comment is indistinguishable from an "
        "oversight, and eleven of those were found in one week. If this one "
        "is genuinely known and accepted, add it to ACCEPTED in this file "
        "with the reason.\n\n" + "\n".join(unexpected))
