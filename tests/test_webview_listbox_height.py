# coding=UTF-8
"""A listbox's `height` is a row count, honoured on configure as at creation.

Kent, 2026-09-22: "the page to start work on a new language has two scrolling
lists that are very difficult to use because they are only one line tall,
including scrollbars." The page builds both lists at `height=1` and
reconfigures them to `min(4, n)` once it knows `n` (ui_shell.py:4019, :4147,
:4219). Under tkinter that reconfigure is native. Under webview it arrived as
`updateProp(wid, "height", 4)`, and the switch had a `width` case and a
`max_height_em` case but no `height` case — so the value went to the
console-only "no handler for option" warning and the lists kept the one-row
`maxHeight` they were created with.

String assertions on the page script, the suite's idiom for widgets.js (see
`test_webview_context_menu.py`).
"""
from pathlib import Path

JS = (Path(__file__).resolve().parents[1]
      / 'frontend' / 'webview_html' / 'widgets.js').read_text()


def test_update_prop_has_a_height_case():
    assert "case 'height':" in JS, \
        "configure(height=n) on a listbox must reach the page"


def test_creation_and_configure_share_one_rule():
    """Two formulas drift; one helper cannot."""
    assert 'function _listboxRows(' in JS
    # the definition, the creation-time call, and the configure-time call
    assert JS.count('_listboxRows(') >= 3, \
        "creation and updateProp must both apply the row count through " \
        "_listboxRows"
    assert "el.style.maxHeight = (spec.props.height * 1.5)" not in JS, \
        "the creation path still carries its own inline formula"


def test_height_on_a_non_list_is_still_reported_not_guessed():
    """Only a list has a rule; anything else must fall through to the
    'no handler for option' report, not silently take the list's."""
    case = JS.index("case 'height':")
    default = JS.index("default:", case)
    body = JS[case:default]
    assert "wv-listbox" in body
    assert "// falls through" in body
