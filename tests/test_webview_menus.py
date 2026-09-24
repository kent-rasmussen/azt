# coding=UTF-8
"""Menus under the webview backend: cascades must survive to the renderer.

WHY THIS EXISTS. `Menu.add_cascade` stored submenus happily while
`Menu.tk_popup` rendered only `kind == 'command'` — so every submenu in the
app was accepted and silently not drawn, and the menu bar did not exist at all
because `config(menu=…)` fell through `configure`'s scalar filter into a dict
nobody read (Kent, 2026-09-24: "Is 'show menus' not working?").

Neither fault could fail a test that only checked commands, which is why there
was not one. These assert the SHAPE that reaches the page: the serialisation
both renderers now share, and the path that carries a click back.

See `agenda/webview_menubar_and_cascades.md`.
"""
import types

import pytest

wv = pytest.importorskip('frontend.ui_webview',
                         reason='needs the webview backend importable')


def _menu():
    """A Menu with no live window behind it — spec() touches no page."""
    return wv.Menu(types.SimpleNamespace(_wv_window=None))


def test_a_cascade_reaches_the_spec():
    """THE REGRESSION. A submenu must appear, with its children."""
    inner = _menu()
    inner.add_command(label='Deeper', command=lambda: None)
    outer = _menu()
    outer.add_command(label='Plain', command=lambda: None)
    outer.add_cascade(label='More', menu=inner)

    spec = outer.spec()
    kinds = [item['kind'] for item in spec]
    assert 'cascade' in kinds, "the cascade was dropped — the 2026-09-24 bug"
    cascade = [i for i in spec if i['kind'] == 'cascade'][0]
    assert [c['kind'] for c in cascade['items']] == ['command']
    assert cascade['items'][0]['label'].strip() == 'Deeper'


def test_a_command_is_addressed_by_path_not_index():
    """An index cannot name anything below the top level."""
    inner = _menu()
    inner.add_command(label='Deeper', command=lambda: None)
    outer = _menu()
    outer.add_command(label='Plain', command=lambda: None)
    outer.add_cascade(label='More', menu=inner)

    deep = outer.spec()[1]['items'][0]
    assert deep['path'] == [1, 0]


def test_command_at_walks_the_path_back():
    fired = []
    inner = _menu()
    inner.add_command(label='Deeper', command=lambda: fired.append('deep'))
    outer = _menu()
    outer.add_command(label='Plain', command=lambda: fired.append('top'))
    outer.add_cascade(label='More', menu=inner)

    outer.command_at([0])()
    outer.command_at([1, 0])()
    assert fired == ['top', 'deep']


def test_command_at_is_safe_on_a_path_that_does_not_exist():
    """The page sends these, so a stale path must not raise."""
    m = _menu()
    m.add_command(label='Only', command=lambda: None)
    assert m.command_at([7]) is None
    assert m.command_at([0, 3]) is None
    assert m.command_at([]) is None


def test_a_cascade_with_a_foreign_menu_is_shown_disabled_not_dropped():
    """An absent entry is indistinguishable from a bug; a greyed one is not."""
    outer = _menu()
    outer.add_cascade(label='Odd', menu=object())
    assert [i['kind'] for i in outer.spec()] == ['disabled']


def test_the_methods_the_app_actually_calls_all_exist():
    """WHAT THE FIRST RUN FOUND. `Menus(self)` raised AttributeError on
    `add_separator` before a single item could be drawn — Tk's Menu has it,
    `ui_shell` calls it seven times, and this one never had it. `index` and
    `delete` go with it: `redoadvanced` deletes the Advanced cascade by label
    and reinserts it at the index it had."""
    m = _menu()
    for name in ('add_command', 'add_cascade', 'insert_cascade',
                 'add_separator', 'index', 'delete', 'spec', 'command_at'):
        assert callable(getattr(m, name, None)), name


def test_a_separator_survives_to_the_spec():
    m = _menu()
    m.add_command(label='One', command=lambda: None)
    m.add_separator()
    m.add_command(label='Two', command=lambda: None)
    assert [i['kind'] for i in m.spec()] == ['command', 'separator', 'command']


def test_index_and_delete_address_entries_by_label():
    inner = _menu()
    m = _menu()
    m.add_command(label='Keep', command=lambda: None)
    m.add_cascade(label='Advanced', menu=inner)
    assert m.index('Advanced') == 1        # padding must not defeat the match
    assert m.index('Nope') is None
    m.delete('Advanced')
    assert [i['label'].strip() for i in m.spec()] == ['Keep']
    m.delete('Nope')                       # must not raise or remove anything
    assert len(m.spec()) == 1


def test_insert_cascade_appends_rather_than_raising_on_a_missing_index():
    """`redoadvanced` feeds `index()`'s answer straight back in, so a label
    that was not there would otherwise reach `list.insert(None, …)`."""
    m = _menu()
    m.insert_cascade(label='Advanced', menu=_menu(), index=None)
    assert [i['kind'] for i in m.spec()] == ['cascade']


def test_both_renderers_are_fed_from_spec():
    """Source-level: the popup must not build its own rows again.

    The bug was two renderers disagreeing about which item kinds exist, so
    the guard is that there is one serialisation and both call it."""
    from pathlib import Path
    src = (Path(__file__).resolve().parents[1]
           / 'frontend' / 'ui_webview.py').read_text()
    popup = src[src.index('    def tk_popup(self, x, y):'):]
    popup = popup[:popup.index('\n    def ', 1)]
    # CODE ONLY. The docstring explains the bug and therefore CONTAINS the
    # phrase this asserts against, so a naive search matches the explanation
    # and fails a correct implementation — which it duly did on the first run.
    code = popup.split('"""', 2)[-1]
    code = '\n'.join(line for line in code.splitlines()
                     if not line.strip().startswith('#'))
    assert 'self.spec()' in code, "tk_popup must render from spec()"
    assert "kind == 'command'" not in code, \
        "tk_popup is filtering item kinds again — that is the cascade bug"

    js = (Path(__file__).resolve().parents[1]
          / 'frontend' / 'webview_html' / 'widgets.js').read_text()
    assert '_buildMenuRows' in js
    for fn in ('function setMenubar(', 'function postMenu('):
        assert fn in js, fn
