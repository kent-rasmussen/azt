"""Guards from the pre-workshop audit (2026-10-12).

A user reported difficulty updating. The audit found, among others:
- every Windows install ran with DEVELOPER settings, because dev mode was
  chosen by the parent folder being called 'AZT' and the installer puts
  azt at %LOCALAPPDATA%\\Programs\\AZT\\azt — and in dev mode Update PUSHES
  to local remotes instead of pulling;
- a refused pull ("error: … Aborting") was reported as an update;
- the σ status migration was undone by load order.

main.py is read as TEXT, not imported: importing it starts the app.
"""
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _code_lines(path):
    """Source lines with comments stripped, so prose can't satisfy a test."""
    return [l.split('#', 1)[0] for l in
            (ROOT / path).read_text(encoding='utf-8').splitlines()]


def test_dev_settings_need_the_switch_or_the_dev_machine():
    lines = _code_lines('main.py')
    gate = [l for l in lines if "'--user' not in sys.argv" in l]
    assert gate, 'the dev-settings gate moved; update this test'
    assert all("'--dev'" in l for l in gate), \
        "dev settings must need --dev (or the dev machine), not a folder name"
    assert any("'karlap'" in l for l in lines)
    assert not any(re.search(r"parent\.stem\s*==\s*'AZT'\s+and\s+'--user'", l)
                   for l in lines), "the folder name alone must not decide"


def test_dev_switch_is_documented():
    from utilities import switches
    assert '--dev' in switches.names()


def test_no_code_reads_the_old_cawln_attribute():
    """`Sense.cawln` was renamed `word_list_n`; `slicebyerror` still read the
    old name, so any word without an image folder (e.g. after the image set
    failed to download) stopped the project loading (2026-10-14)."""
    for path in ROOT.rglob('*.py'):
        if 'tests' in path.parts:
            continue
        for n, line in enumerate(_code_lines(path.relative_to(ROOT)), 1):
            assert '.cawln' not in line, f'{path.name}:{n}: {line.strip()}'


def test_the_digraph_ok_is_decided_before_the_window_closes():
    """Under webview, destroying the digraph window released the waiting
    code at once; it ran the default "no changes" exit, reported that the
    user had exited, and the program quit while OK's handler restarted it —
    two copies running (2026-10-13)."""
    lines = _code_lines('frontend/config/settings_ui.py')
    text = '\n'.join(lines)
    start = text.index('def askaboutpolygraphs')
    body = text[start:text.index('def notifyuserofextrasegments')]
    mc = body[body.index('def makechanges'):body.index('def foundchanges')]
    assert mc.index("decided['changes']=True") < mc.index('pgw.destroy()')
    after = body[body.index('pgw.wait_window(pgw)'):]
    assert after.index("decided.get('changes')") < after.index('nochanges()')


def test_the_predecessor_has_an_exit_deadline():
    """Under webview the predecessor's main loop never returned after a
    confirmed restart; it lingered with "Restarting…" on screen."""
    text = '\n'.join(_code_lines('main.py'))
    i = text.index('predecessor leaving')
    block = text[i:i + 1500]
    assert 'threading.Timer(' in block and 'os._exit(0)' in block
    assert block.index('threading.Timer(') < block.index('self.tk_root.quit()')


def test_a_users_program_update_never_merges():
    """Update for a user resets to the published branch; the merge-and-
    preserve machinery (try_pull_main, work_from_x) is for user DATA and
    stays on the base class (Kent, 2026-10-13)."""
    text = '\n'.join(_code_lines('backend/core/vcs.py'))
    cls = text[text.index('class GitReadOnly'):]
    share = cls[cls.index('def share'):cls.index('def update_by_reset')]
    user_branch = share[share.index('else:'):]
    assert 'update_by_reset()' in user_branch
    assert 'Repository.pull' not in user_branch
    upd = cls[cls.index('def update_by_reset'):cls.index('def switchbranches')]
    assert "'checkout','-f','-B'" in upd.replace(' ', '')
    assert "'pull'" not in upd, 'no git pull (a merge) in the user update'
    assert 'def try_pull_main' in text, 'the data repo still needs it'


def test_try_and_revert_do_not_also_update():
    text = '\n'.join(_code_lines('frontend/ui_shell.py'))
    for fn in ('def reverttomainazt', 'def trytestazt'):
        body = text[text.index(fn):]
        body = body[:body.index('\n    def ', 10)]
        assert 'updateazt()' not in body


def test_a_refusal_is_not_an_update():
    from utilities.utilities import updated
    assert not updated('error: Your local changes to the following files '
                       'would be overwritten by merge:\n\tmain.py\nAborting')
    assert not updated('fatal: unable to access …')
    assert not updated('Already up to date.')
    assert not updated('')
    assert updated('Updating 1a2b..3c4d\nFast-forward\n main.py | 2 +-')


def test_the_live_status_is_built_from_the_migrated_dict():
    text = '\n'.join(_code_lines('settings/__init__.py'))
    i = text.index("elif s == 'status' and not hasattr(self.program,'status')")
    branch = text[i:i + 600]
    assert 'migrate_syllable_tier_code(d)' in branch
    assert branch.index('migrate_syllable_tier_code(d)') < \
        branch.index('self.makestatus(d)')
