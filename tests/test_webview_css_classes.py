# coding=UTF-8
"""Every class the JS toggles must be a class the stylesheet styles.

THE BUG THIS EXISTS FOR (2026-09-24). `_buildMenuRows` set `wv-menu-open` to
open a menu; `grid.css` matched `wv-menubar-open`. A class that matches no
rule is legal CSS and raises nothing, so the menu opened in the DOM and stayed
invisible: the bar drew and nothing on it worked (Kent: "menus showed, but
nothing was clickable"). The rename happened in one file and not the other.

That is the second fault of the same shape in one session — two places that
agree only by convention, with nothing able to check the pair. Neither file
can validate the other, so the check has to live here.

DIRECTION: JS → CSS. A class the JS sets and the stylesheet ignores is either
a bug like the one above or a deliberate marker with no appearance. The
second kind goes in `JS_ONLY` below, WITH ITS REASON — which is the point:
the exemption is cheap, and writing down why makes the next reader able to
tell the two apart. The reverse direction (CSS rules for classes nothing
sets) is dead styling rather than broken behaviour, and is not checked here.
"""
import re
from pathlib import Path

import pytest

HTML = Path(__file__).resolve().parents[1] / 'frontend' / 'webview_html'
JS = HTML / 'widgets.js'
CSS = HTML / 'grid.css'

# Classes the JS sets that the stylesheet deliberately does not style —
# markers read back by other JS, or hooks for nothing visual. ADD A REASON.
JS_ONLY = {
    'wv-disabled':
        "deliberate hook, not an oversight. `_setState` greys a disabled "
        "control with an INLINE opacity so it looks disabled with no rule at "
        "all, and adds this class so the stylesheet CAN say what disabled "
        "looks like if it wants to. Native controls are handled separately by "
        "`.wv-button[disabled]`, which grid.css does style.",
}


def _js_classes(text):
    """Class names the JS adds, removes or toggles, or assigns to className."""
    names = set()
    for m in re.finditer(r"""classList\.(?:add|remove|toggle)\(\s*['"]([^'"]+)['"]""",
                         text):
        names.add(m.group(1))
    # `className = 'a b'` and `className += ' a b'` — several at once.
    for m in re.finditer(r"""className\s*\+?=\s*['"]([^'"]+)['"]""", text):
        names.update(m.group(1).split())
    return {n for n in names if n and not n.startswith('${')}


def _css_classes(text):
    """Every class named anywhere in a selector."""
    # Strip comments so a class mentioned only in prose does not count as
    # styled — the mistake that let the menu bug through would otherwise be
    # masked by the comment explaining it.
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.S)
    return set(re.findall(r'\.([A-Za-z_][\w-]*)', text))


@pytest.mark.skipif(not JS.exists() or not CSS.exists(),
                    reason='webview HTML assets not present')
def test_every_class_the_js_toggles_is_styled():
    used = _js_classes(JS.read_text())
    styled = _css_classes(CSS.read_text())
    missing = sorted(used - styled - set(JS_ONLY))
    if missing:
        pytest.fail(
            '{} class(es) are set by widgets.js and styled nowhere in '
            'grid.css:\n\n  {}\n\n'
            'Each is either the menu bug again — a rename in one file and not '
            'the other,\nwhich fails silently because unmatched CSS classes '
            'are legal — or a JS-only\nmarker with no appearance. Fix the '
            'first kind; add the second to JS_ONLY in\nthis file WITH ITS '
            'REASON, so the next reader can tell them apart.'
            ''.format(len(missing), '\n  '.join(missing)))


def test_the_menu_open_class_is_the_one_the_stylesheet_uses():
    """The exact pair that broke, asserted by name.

    Kept separate from the sweep above so it survives someone widening
    JS_ONLY: these two must agree, whatever else is exempted."""
    js = JS.read_text()
    css = _css_classes(CSS.read_text())
    assert 'wv-menu-open' in js, 'the JS no longer sets wv-menu-open'
    assert 'wv-menu-open' in css, \
        'grid.css does not style wv-menu-open — menus will open invisibly'
    assert 'wv-menubar-open' not in css, \
        'grid.css still matches the OLD open-state class; menus will not open'
