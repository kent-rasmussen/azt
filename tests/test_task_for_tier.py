"""One table from tier to task; no class name is built from a tier letter.

Until 2026-10-02 the tier switch made the new task's class name by string
arithmetic — `task_base + choice` in `SettingsUI.setcvt`, f"Sort{cvt}" in
`Sort.update_to_cvt` and in the two go-back paths of the segmental
transcribe task — and `program.task_base()` recovered the family by
stripping the cvt letters off the class name. The syllable sort broke both:
its class is `SortSyllables` and its cvt was `'S'`, which was also the last
letter of `SortS`, the segmental base. So choosing `S` on a vowel sort
resolved to the segmental base, and choosing `V` on the syllable sort asked
for `SortSyllableV`. Kent's decision (the S-codes decision, 2026-10-02):
"segmental --> 'CV' everywhere a code is used … a SortCV which is not
currently called, but is mixed into SortV and SortC."

The behaviour needs a window; what can be checked headless is the table, the
class tree, and that no switch site builds a name any more.
"""
import pytest

from sourcescan import code as _code

tasks = pytest.importorskip('tasks.tasks')
from backend.core import sorting_engine            # noqa: E402
from frontend.config import settings_ui            # noqa: E402


def test_the_table_maps_every_tier_to_its_task():
    t = tasks.task_for_tier
    assert t('Sort', 'V') is tasks.SortV
    assert t('Sort', 'C') is tasks.SortC
    assert t('Sort', 'T') is tasks.SortT
    assert t('Sort', 'σ') is tasks.SortSyllables, \
        "σ must reach the syllable sort, not the segmental base"
    assert t('Sort', 'S') is None, \
        "S alone is the sonorant class, not a tier (the S-codes decision)"
    assert t('Transcribe', 'V') is tasks.TranscribeV
    assert t('Transcribe', 'C') is tasks.TranscribeC
    assert t('Transcribe', 'T') is tasks.TranscribeT


def test_no_task_is_an_answer_not_an_error():
    """CV and VC are offered on a transcribe task's tier line and have no
    task; the concatenation raised AttributeError there."""
    assert tasks.task_for_tier('Transcribe', 'CV') is None
    assert tasks.task_for_tier('Transcribe', 'VC') is None
    assert tasks.task_for_tier('Transcribe', 'σ') is None
    assert tasks.task_for_tier('Report', 'V') is None


def test_the_segmental_base_is_SortCV_and_the_S_is_gone():
    assert not hasattr(tasks, 'SortS')
    assert not hasattr(tasks, 'TranscribeS')
    assert tasks.SortCV in tasks.SortV.__mro__
    assert tasks.SortCV in tasks.SortC.__mro__
    assert tasks.TranscribeCV in tasks.TranscribeV.__mro__
    assert tasks.TranscribeCV in tasks.TranscribeC.__mro__


def test_the_family_is_declared_not_derived():
    """`program.task_base()` reads this attribute instead of stripping
    letters off the class name."""
    assert tasks.Sort.task_family == 'Sort'
    assert tasks.Transcribe.task_family == 'Transcribe'
    assert tasks.SortSyllables.task_family == 'Sort'
    assert tasks.SortV.task_family == 'Sort'
    assert tasks.TranscribeV.task_family == 'Transcribe'


@pytest.mark.parametrize('fn', [
    settings_ui.SettingsUI.setcvt,
    sorting_engine.Sort.update_to_cvt,
    tasks.TranscribeCV.go_back,
    tasks.TranscribeCV._go_back_from_helper,
], ids=lambda f: f.__qualname__)
def test_no_switch_site_builds_a_class_name_from_the_tier(fn):
    src = _code(fn)                       # comments and docstring removed
    assert 'task_for_tier' in src
    assert 'task_base+' not in src.replace(' ', '')
    assert 'f"Sort{' not in src and "f'Sort{" not in src
