"""A column-count change must reach the page you are looking at.

`setbuttoncolumns` stored the value, relabelled its own line, and stopped —
no `attrschanged`, no `refreshattributechanges` — so unlike `ftype` or the
gloss languages there was no path from the setting to anything on screen.
`SortButtonFrame.__init__` takes a SNAPSHOT (`self.buttoncolumns =
self.task.buttoncolumns`), so a frame is correct for whatever the setting was
when it was built and can never change afterwards.

That is the whole of the two-month-old "the `buttoncolumns` setting doesn't
work" report. Kent, 2026-09-30, after testing it: *"3: no, as i described
earlier / 5: yes now"* — no change on the open page, correct after leaving
the task and returning. It worked, on the next open, which from the user's
chair is indistinguishable from not working.

Also his: *"both on Sort!, not before, since the settings is meaningless
before"* — the group buttons live in the run window, so zero frames re-laid
is a normal answer, not a failure.
"""
import inspect
from types import SimpleNamespace

import pytest

pytest.importorskip("lxml")
from frontend.sort_buttons import SortButtonFrame


class _Button:
    def __init__(self, group):
        self.group = group
        self.row = self.column = None
        self.grids = 0

    def grid(self, row=None, column=None, **kw):
        self.grids += 1


def _frame(columns, nbuttons=5, from_setting=True, alive=True):
    """A fake frame carrying the REAL methods — the suite's technique."""
    f = SimpleNamespace(buttoncolumns=columns,
                        _columns_from_setting=from_setting,
                        groupbuttonlist=[_Button(str(i))
                                         for i in range(nbuttons)],
                        winfo_exists=lambda: alive)
    f.regrid_group_buttons = SortButtonFrame.regrid_group_buttons.__get__(f)
    return f


@pytest.fixture(autouse=True)
def _clean_registry():
    """`_live` is class state; never leak a fake into another test."""
    saved = list(SortButtonFrame._live)
    SortButtonFrame._live.clear()
    yield
    SortButtonFrame._live[:] = saved


# ── the sweep itself ─────────────────────────────────────────────────────

def test_one_column_puts_each_button_on_its_own_row():
    f = _frame(1, nbuttons=3)
    f.regrid_group_buttons()
    assert [(b.row, b.column) for b in f.groupbuttonlist] == \
        [(0, 0), (1, 0), (2, 0)]


def test_two_columns_fill_across_then_down():
    f = _frame(2, nbuttons=5)
    f.regrid_group_buttons()
    assert [(b.row, b.column) for b in f.groupbuttonlist] == \
        [(0, 0), (0, 1), (1, 0), (1, 1), (2, 0)]


def test_a_button_already_in_place_is_not_regridded():
    """The skip that `removegroupbutton` relied on, kept: re-gridding every
    button on every sweep is a visible reflow for nothing."""
    f = _frame(1, nbuttons=3)
    f.regrid_group_buttons()
    assert all(b.grids == 1 for b in f.groupbuttonlist)
    f.regrid_group_buttons()
    assert all(b.grids == 1 for b in f.groupbuttonlist), \
        'a second sweep over unchanged positions must grid nothing'


def test_zero_columns_cannot_divide_by_zero():
    """The value arrives from a chooser, and a ZeroDivisionError inside a
    layout refresh would take the page with it."""
    f = _frame(0, nbuttons=2)
    f.regrid_group_buttons()
    assert [(b.row, b.column) for b in f.groupbuttonlist] == [(0, 0), (1, 0)]


# ── which frames get it ──────────────────────────────────────────────────

def test_a_live_setting_driven_frame_is_relaid():
    f = _frame(1, nbuttons=4)
    SortButtonFrame._live.append(f)
    assert SortButtonFrame.relayout_all(2) == 1
    assert f.buttoncolumns == 2
    assert [(b.row, b.column) for b in f.groupbuttonlist] == \
        [(0, 0), (0, 1), (1, 0), (1, 1)]


def test_macrosort_frames_stay_pinned_at_one():
    """Two of the three branches in `__init__` set `buttoncolumns=1`
    deliberately — the gather and verify pages — and only the ordinary sort
    branch reads the user's setting. A refresh must not push the setting
    onto the pinned ones."""
    pinned = _frame(1, from_setting=False)
    SortButtonFrame._live.append(pinned)
    assert SortButtonFrame.relayout_all(3) == 0
    assert pinned.buttoncolumns == 1


def test_a_dead_frame_is_dropped_rather_than_touched():
    """A frame dies with its window and gets no say in it, so the registry
    is pruned when it is walked."""
    dead = _frame(1, alive=False)
    SortButtonFrame._live.append(dead)
    assert SortButtonFrame.relayout_all(2) == 0
    assert dead not in SortButtonFrame._live


def test_no_frames_at_all_is_a_normal_answer():
    """Before `Sort!` there is no frame. Kent: "both on Sort!, not before,
    since the settings is meaningless before." The next frame built reads
    the setting itself."""
    assert SortButtonFrame.relayout_all(2) == 0


def test_setting_the_same_count_changes_nothing():
    f = _frame(2, nbuttons=3)
    SortButtonFrame._live.append(f)
    assert SortButtonFrame.relayout_all(2) == 0


def test_a_junk_column_count_is_refused_not_raised():
    f = _frame(1)
    SortButtonFrame._live.append(f)
    assert SortButtonFrame.relayout_all('two columns') == 0
    assert f.buttoncolumns == 1


# ── the wiring ───────────────────────────────────────────────────────────

def test_the_setter_refreshes_the_windows_copy():
    """THE ACTUAL CAUSE, and the reason the first fix changed nothing.

    `TaskDressing.inherittaskattrs` copies `buttoncolumns` off
    `program.settings` onto the task window when the WINDOW is built, and
    `SortButtonFrame` reads `self.task.buttoncolumns` — which resolves
    through the task→window bridge to that copy, not to the setting. The run
    window and its frame are rebuilt on every sort cycle, so every rebuild
    re-read the stale copy; only a new task window refreshed it. Kent:
    *"buttoncolumns only applies after a task restart."*

    So re-laying live frames is not enough on its own: the copy has to move
    too, or the next rebuild undoes it."""
    from sourcescan import code
    from frontend.config.settings_ui import SettingsUI
    src = code(SettingsUI.setbuttoncolumns)
    assert 'buttoncolumns=choice' in src.replace(' ', ''), \
        'the setter must write the window copy, not only program.settings'
    assert 'mainwindow' in src and 'task' in src, \
        'both holders of a copy have to be updated'


def test_the_copy_is_still_taken_at_build_time():
    """The guard on the thing being worked around: if `inherittaskattrs`
    ever stops copying `buttoncolumns`, the setter's refresh is dead code
    and should go with it. See the duplicated-settings item."""
    from sourcescan import code
    from frontend.ui_shell import TaskDressing
    assert 'buttoncolumns' in code(TaskDressing.inherittaskattrs)


def test_the_setter_asks_the_presenter():
    """The seam: the settings layer goes through `sort_ui` rather than
    importing a widget class, like every other backend→frontend call here.
    And it must actually call something — storing the value and relabelling
    the line is what it did for two months."""
    from sourcescan import code
    from frontend.config.settings_ui import SettingsUI
    src = code(SettingsUI.setbuttoncolumns)
    assert 'relayout_group_buttons' in src, \
        'setbuttoncolumns must tell the page, not just store the value'
    assert 'sort_ui' in src


def test_the_presenter_exposes_the_seam():
    from frontend.sort_ui import SortPresenter
    assert hasattr(SortPresenter, 'relayout_group_buttons')


def test_remove_group_button_uses_the_same_sweep():
    """One implementation, two callers — `removegroupbutton`'s own re-grid
    and a column change are the same operation, and were the same code
    duplicated before 2026-09-30."""
    from sourcescan import code
    src = code(SortButtonFrame.removegroupbutton)
    assert 'regrid_group_buttons' in src
    assert 'i%' not in src, 'the column formula should live in one place'


def test_the_build_records_which_branch_set_the_count():
    """`_columns_from_setting` is what lets a refresh tell a pinned frame
    from a settings-driven one without re-deriving the branch."""
    src = inspect.getsource(SortButtonFrame.__init__)
    assert src.count('_columns_from_setting') == 3, \
        'all three branches must say where the column count came from'
