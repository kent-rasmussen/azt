# coding=UTF-8
"""Themes and images are the APP's, and there is exactly one copy of each.

WHY. Both were declared in `ui_tkinter.Theme` and hand-copied into
`ui_webview.Theme`, and both copies were short. That cost two user-visible
faults in one afternoon (2026-09-11):

  * 35 of 81 images missing from the webview copy — `record` (so the record
    button had no icon in the Sound Card Settings window, whose purpose is
    testing recording), every sort-board verb image, the numbered C/V images,
    and both alphabet-task icons. `theme.photo.get(name)` returns None for a
    name that was never there, and `image=None` draws nothing and logs
    nothing, so the whole class failed silently;
  * `Kim` — Kent's own theme — absent from the webview copy's four entries,
    with an unknown name falling back to greygreen without a word. The log
    said "Using theme Kim" and the screen was green.

These tests read source and data, not pixels, so they run headless on any
platform. The point is not that the values are right; it is that there is
only ONE set of them.
"""
import ast
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

theme_data = pytest.importorskip('frontend.theme_data')


def test_theme_data_imports_nothing():
    """The constraint that made copying look necessary: `ui_webview` must not
    pull in tkinter, so the shared module has to be importable on a machine
    with no Tk. If it ever grows an import, the sharing breaks and someone
    will copy the data again."""
    tree = ast.parse((ROOT / 'frontend' / 'theme_data.py').read_text())
    imports = [n for n in ast.walk(tree)
               if isinstance(n, (ast.Import, ast.ImportFrom))]
    assert not imports, \
        "theme_data must import nothing: {}".format(
            [ast.dump(n) for n in imports])


def test_both_backends_use_THE_SAME_image_list():
    tk = pytest.importorskip('frontend.ui_tkinter',
                             reason='needs tkinter importable')
    wv = pytest.importorskip('frontend.ui_webview',
                             reason='needs the webview backend importable')
    assert tk.Theme.imagelist is theme_data.IMAGELIST
    assert wv.Theme.imagelist is theme_data.IMAGELIST


def test_both_backends_use_THE_SAME_themes():
    tk = pytest.importorskip('frontend.ui_tkinter',
                             reason='needs tkinter importable')
    wv = pytest.importorskip('frontend.ui_webview',
                             reason='needs the webview backend importable')
    assert wv.Theme.themes is theme_data.THEMES
    # tkinter builds its copy in setthemes(); check the CONTENT matches,
    # since it legitimately holds an instance dict.
    theme = tk.Theme.__new__(tk.Theme)
    tk.Theme.setthemes(theme)
    assert theme.themes == theme_data.THEMES


def test_the_webview_backend_reads_the_theme_THE_APP_SET():
    """TWO faults in one line, and fixing the dictionary only removed one.

    `App.check_for_theme` (main.py:1528) puts the chosen theme's NAME on
    `program.theme` as a string. `ui_webview.Theme` read `program.theme_name`
    — an attribute NOTHING sets, appearing twice in the codebase, both in
    that file — so the webview backend never learned the user's theme and
    silently used the default. The fallback could not even warn, because the
    default is a valid theme name.

    Kent, after the missing-themes fix: "still says Kim on my machine without
    my Kim theme visible (qt and gtk)."
    """
    wv = pytest.importorskip('frontend.ui_webview',
                             reason='needs the webview backend importable')
    import types
    program = types.SimpleNamespace(theme='Kim', name='A-Z+T')
    theme = wv.Theme.__new__(wv.Theme)
    # Only the theme-choosing part; the rest builds fonts and loads images.
    chosen = getattr(program, 'theme', None)
    if not isinstance(chosen, str):
        chosen = getattr(program, 'theme_name', None)
    assert chosen == 'Kim', 'the name must be read BEFORE program.theme is ' \
                            'replaced by the Theme object'
    theme.themes = theme_data.THEMES
    theme.name = chosen if isinstance(chosen, str) else theme_data.DEFAULT_THEME
    assert theme.name in theme.themes
    assert theme.themes[theme.name] is theme_data.THEMES['Kim']


def test_nothing_reads_the_attribute_nobody_sets():
    """`theme_name` was read and never written. Assert the read is gone, so
    the next person does not reintroduce a lookup with no source."""
    src = (ROOT / 'frontend' / 'ui_webview.py').read_text()
    live = [ln for ln in src.splitlines()
            if 'theme_name' in ln and not ln.strip().startswith('#')]
    assert len(live) <= 1, \
        "theme_name should survive only as a fallback: {}".format(live)


def test_the_themes_that_were_missing_are_present():
    """Named rather than counted: `Kim` is the one that was actually being
    used when this was found."""
    for name in ('Kim', 'Kent', 'Howard', 'yellow', 'purple', 'green',
                 'lightgreen', 'lighterpink', 'evenlighterpink',
                 'greygreen1', 'tkinterdefault'):
        assert name in theme_data.THEMES, "theme {!r} lost".format(name)


def test_every_theme_supplies_every_key():
    """A theme missing a key is an AttributeError later, on whichever screen
    happens to read it first."""
    keys = set(theme_data.THEMES[theme_data.DEFAULT_THEME])
    for name, theme in theme_data.THEMES.items():
        assert set(theme) == keys, \
            "theme {!r} has {} not {}".format(name, sorted(theme),
                                              sorted(keys))


def test_the_default_theme_exists():
    assert theme_data.DEFAULT_THEME in theme_data.THEMES


def test_image_names_are_unique():
    names = [n for n, _f in theme_data.IMAGELIST]
    dupes = {n for n in names if names.count(n) > 1}
    assert not dupes, "duplicate image names: {}".format(sorted(dupes))


def test_the_images_that_were_missing_are_present():
    """The 35, by the groups they fall into. `record` first: it is the one
    Kent hit, on the button the window exists for."""
    for name in ('record', 'change', 'backgrounded', 'Order!',
                 'alpha_chart', 'alpha_chart_icon',
                 'alpha_page', 'alpha_page_icon',
                 'sort', 'sortglyphs', 'verify', 'verifyglyphs',
                 'join', 'join_same', 'join_different',
                 'joinglyphs', 'joinglyphs_same', 'joinglyphs_different',
                 'C1', 'C6', 'V1', 'V6', 'V=', 'V1=V2', 'V2=V3', 'V3=V4',
                 'TRepcomp', 'VRepcomp', 'CRepcomp', 'CVRepcomp',
                 'VCCVRepcomp'):
        assert name in dict(theme_data.IMAGELIST), \
            "image {!r} lost".format(name)


def test_every_taskicon_the_app_asks_for_exists():
    """THE CHECK THAT WOULD HAVE CAUGHT IT. `chooser.py` does
    `photos.get(task.taskicon)`, so a task naming an icon nobody supplied
    gets None and renders blank with nothing in the log. Read from source, so
    this needs neither a display nor the tasks importable."""
    have = dict(theme_data.IMAGELIST)
    asked = {}
    for path in (ROOT / 'tasks').rglob('*.py'):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if not isinstance(node, ast.Assign):
                continue
            for target in node.targets:
                if (isinstance(target, ast.Name)
                        and target.id == 'taskicon'
                        and isinstance(node.value, ast.Constant)
                        and isinstance(node.value.value, str)):
                    asked[node.value.value] = path.name
    assert asked, "found no taskicon assignments — has the attribute moved?"
    missing = {k: v for k, v in asked.items() if k not in have}
    assert not missing, \
        "tasks ask for icons that no backend can supply: {}".format(missing)


def test_the_image_files_exist():
    """A name in the list whose file is absent fails at load time with one
    WARNING for the batch, which is easy to miss. Cheap to check here."""
    images = ROOT / 'images'
    if not images.is_dir():
        pytest.skip('no images/ directory in this checkout')
    missing = [f for _n, f in theme_data.IMAGELIST
               if not (images / f).is_file()]
    assert not missing, "image files named but absent: {}".format(missing)
