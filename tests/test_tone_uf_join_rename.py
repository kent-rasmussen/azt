"""Renaming and joining UF groups — `tasks.tasks.JoinUFgroups`.

`tonegroupsjoinrename` builds the join/rename page and keeps the logic in
its nested `submitform`, so the page is driven here with a recording stand-in
for the `ui` module: the test ticks group check-buttons, types a name, and
presses the OK button's own command. Everything below the page — the
Analysis, the sense tone fields — is real (see `tests/ufkit.py`).

What is asserted (intended behaviour, from the task's own text):
  * renaming rewrites every member's UF tone field;
  * joining puts every member of the selected groups under one name;
  * an empty name is refused, and so is a name already used by another
    group in the slice (unless that group is part of the selection);
  * a refused submit changes nothing and writes nothing.
"""
import contextlib
from types import SimpleNamespace

import pytest

tasks_mod = pytest.importorskip('tasks.tasks')
lexicon = pytest.importorskip('backend.core.lexicon')

from ufkit import build_senses, make_program  # noqa: E402


# ── a recording stand-in for `frontend.ui` ─────────────────────────────────

class Var:
    def __init__(self, value=''):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


class Widget:
    def __init__(self, page, *args, **kwargs):
        self.page = page
        self.kwargs = kwargs
        self.items = {'text': kwargs.get('text', '')}
        self.content = self            # ScrollingFrame.content

    def __setitem__(self, key, value):
        self.items[key] = value
        if key == 'text' and value:
            self.page.messages.append(value)

    def __getitem__(self, key):
        return self.items[key]

    def __getattr__(self, name):       # grid, wrap, bind, reflow, …
        return lambda *a, **k: None


class Page:
    def __init__(self):
        self.messages = []
        self.buttons = []
        self.checkbuttons = {}         # onvalue (group name) -> variable
        self.entry_var = None

    def press(self, fname):
        cmds = [b.kwargs.get('command') or b.kwargs.get('cmd')
                for b in self.buttons]
        hits = [c for c in cmds if getattr(c, '__name__', None) == fname]
        assert len(hits) == 1, f"one '{fname}' button expected: {cmds}"
        hits[0]()

    def tick(self, *groups):
        for g in groups:
            self.checkbuttons[g].set(g)    # Tk sets the var to its onvalue

    def type_name(self, text):
        self.entry_var.set(text)


class FakeUI:
    def __init__(self):
        self.pages = []

    def new_page(self):
        self.pages.append(Page())

    @property
    def page(self):
        return self.pages[-1]

    def StringVar(self, *a, **k):
        return Var()

    def Label(self, *a, **k):
        return Widget(self.page, *a, **k)

    Frame = ScrollingFrame = Label

    def Button(self, *a, **k):
        w = Widget(self.page, *a, **k)
        self.page.buttons.append(w)
        return w

    def EntryField(self, *a, **k):
        self.page.entry_var = k.get('text') or k.get('textvariable')
        return Widget(self.page, *a, **k)

    def CheckButton(self, *a, **k):
        self.page.checkbuttons[k['onvalue']] = k['variable']
        return Widget(self.page, *a, **k)


class RunWindow:
    def __init__(self):
        self.frame = object()
        self.quits = 0

    def on_quit(self, *a, **k):
        self.quits += 1

    def __getattr__(self, name):       # title, waitdone, deiconify, wait_window
        return lambda *a, **k: None


class TaskUI:
    def __init__(self, fake_ui):
        self.fake_ui = fake_ui
        self.runwindow = RunWindow()

    def getrunwindow(self, *a, **k):
        self.fake_ui.new_page()


class JoinTask:
    """Fake `self` for the real JoinUFgroups / Tone methods."""
    tonegroupsjoinrename = tasks_mod.JoinUFgroups.tonegroupsjoinrename
    makeanalysis = lexicon.Tone.makeanalysis

    def __init__(self, program, fake_ui):
        self.program = program
        self.ui = TaskUI(fake_ui)
        self.writes = 0

    def maybewrite(self):
        self.writes += 1

    def update(self):
        pass

    def waiting(self, *a, **k):
        return contextlib.nullcontext()


SPECS = [
    dict(id='a1', tones={'Isolation': '1', 'Possessive': '2'}),
    dict(id='a2', tones={'Isolation': '1', 'Possessive': '2'}),
    dict(id='b1', tones={'Isolation': '1', 'Possessive': '3'}),
    dict(id='c1', tones={'Isolation': '2', 'Possessive': '3'}),
    dict(id='c2', tones={'Isolation': '2', 'Possessive': '3'}),
]


@pytest.fixture
def join(monkeypatch):
    fake_ui = FakeUI()
    monkeypatch.setattr(tasks_mod, 'ui', fake_ui)
    db, senses = build_senses(SPECS)
    prog = make_program({('Noun', 'CVC'): senses},
                        {'Noun': ['Isolation', 'Possessive']}, db)
    task = JoinTask(prog, fake_ui)
    task.makeanalysis()
    task.analysis.do()                 # draft UFs onto the senses
    by_id = {s.id: s for s in senses}
    groups = {sid: by_id[sid].ufgroup() for sid in by_id}
    assert groups['a1'] == groups['a2'] != groups['b1'] != groups['c1']
    task.tonegroupsjoinrename()
    assert fake_ui.pages, "the join page was built"
    return SimpleNamespace(task=task, ui=fake_ui, s=by_id, drafts=groups,
                           db=db)


def ufs(j):
    """The group each word is in: its join/rename, else its draft (D3)."""
    return {sid: s.ufgroup() for sid, s in j.s.items()}


def test_the_page_offers_every_draft_group_of_the_slice(join):
    assert set(join.ui.page.checkbuttons) == set(join.drafts.values())


def test_renaming_rewrites_every_member(join):
    old = join.drafts['a1']
    page = join.ui.page
    page.tick(old)
    page.type_name('High')
    page.press('submitform')
    now = ufs(join)
    assert now['a1'] == now['a2'] == 'High'
    for sid in ('b1', 'c1', 'c2'):
        assert now[sid] == join.drafts[sid], "unselected groups unchanged"
    assert join.task.writes == 1
    # the page is rebuilt from the LIFT values: the new name, not the old
    assert len(join.ui.pages) == 2
    offered = set(join.ui.page.checkbuttons)
    assert 'High' in offered and old not in offered


def test_joining_puts_all_members_under_one_name(join):
    g_a, g_b = join.drafts['a1'], join.drafts['b1']
    page = join.ui.page
    page.tick(g_a, g_b)
    page.type_name('Low')
    page.press('submitform')
    now = ufs(join)
    assert now['a1'] == now['a2'] == now['b1'] == 'Low'
    assert now['c1'] == now['c2'] == join.drafts['c1']
    assert set(join.task.analysis.sensesbygroup['Low']) == \
        {join.s['a1'], join.s['a2'], join.s['b1']}


def test_joining_into_one_of_the_selected_names_is_allowed(join):
    g_a, g_b = join.drafts['a1'], join.drafts['b1']
    page = join.ui.page
    page.tick(g_a, g_b)
    page.type_name(g_b)
    page.press('submitform')
    now = ufs(join)
    assert now['a1'] == now['a2'] == now['b1'] == g_b
    assert not page.messages


def test_an_empty_name_is_refused_and_nothing_changes(join):
    page = join.ui.page
    page.tick(join.drafts['a1'])
    page.type_name('')
    page.press('submitform')
    assert page.messages, "the user is told why"
    assert ufs(join) == join.drafts
    assert join.task.writes == 0
    assert len(join.ui.pages) == 1, "the page stays up for another try"


def test_a_blank_name_is_refused_like_an_empty_one(join):
    """INFERRED intent: the check is `uf == ''`, so '   ' passes and
    becomes a UF value that reads as blank everywhere it is shown."""
    page = join.ui.page
    page.tick(join.drafts['a1'])
    page.type_name('   ')
    page.press('submitform')
    assert page.messages
    assert ufs(join) == join.drafts
    assert join.task.writes == 0


def test_a_name_used_by_another_group_in_the_slice_is_refused(join):
    taken = join.drafts['c1']
    page = join.ui.page
    page.tick(join.drafts['a1'])
    page.type_name(taken)
    page.press('submitform')
    assert page.messages, "the user is told the name is taken"
    assert ufs(join) == join.drafts, "nothing was merged into the other group"
    assert join.task.writes == 0


def test_a_rename_goes_to_the_human_form_over_the_machine_draft(join):
    """D3 (Kent, 2026-10-13): "put our analysis into machine codes, then the
    joined and renamed forms into data fields"."""
    draft = join.drafts['a1']
    page = join.ui.page
    page.tick(draft)
    page.type_name('High')
    page.press('submitform')
    for sid in ('a1', 'a2'):
        assert join.s[sid].uftonevalue() == 'High'
        assert join.s[sid].uftonevalue(machine=True) == draft
    assert join.s['b1'].uftonevalue() is None, "untouched: draft only"


def test_rename_stamps_the_join_on_the_slice_shown(join):
    page = join.ui.page
    page.tick(join.drafts['a1'])
    page.type_name('High')
    page.press('submitform')
    stamps = [kw for t, u, kw in join.task.program.status.last_calls
              if (t, u) == ('joinUF', True)]
    assert stamps and stamps[0].get('ps') == 'Noun' \
        and stamps[0].get('profile') == 'CVC', stamps


def test_rename_stamps_the_join(join):
    page = join.ui.page
    page.tick(join.drafts['a1'])
    page.type_name('High')
    page.press('submitform')
    assert ('joinUF', True) in [(t, u) for t, u, _ in
                                join.task.program.status.last_calls]
