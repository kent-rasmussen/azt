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
