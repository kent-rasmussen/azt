"""`<unset>` is a word the label may say and the editor may not.

Kent, 2026-09-17, on the second-form field line in a vowel sort: the combo
opened with `<unset>` in it, as if that were the current field name — "we
don't want that value to show in the editor at all". The same commit is how
the string reached `project.json`: `close_open_field` commits an open field
when the user clicks a different one, so clicking away from a field nobody
answered handed the display placeholder to the setter.

These exercise `ClickToEdit` with a stand-in `self` rather than a live Tk
root, which is the suite's idiom for the composites (see
`test_sound_ui_handlers.py`).
"""
import types

from frontend import composites
from frontend import ui_variables


PLACEHOLDER = '<unset>'


def _field(value, placeholder=PLACEHOLDER, on_commit=None):
    """A stand-in with the attributes `edit`/`commit` actually touch."""
    var = ui_variables.StringVar(value=value)
    grid = []
    ns = types.SimpleNamespace(
        var=var,
        grid=grid,
        _placeholder=placeholder,
        _clear_on_edit=False,
        _cleared=False,
        _was=None,
        _on_commit=on_commit,
        _rebuild=False,
        _editor=lambda box: None,
        widget=None,
        box=types.SimpleNamespace(grid=lambda: grid.append('box'),
                                  grid_remove=lambda: grid.append('-box'),
                                  bind=lambda *a: None,
                                  unbind=lambda *a: None),
        shown=types.SimpleNamespace(grid=lambda: grid.append('label'),
                                    grid_remove=lambda: grid.append('-label')),
        )
    # The real method, on the stand-in: `edit` and `commit` both ask it.
    ns.showing_placeholder = lambda: composites.ClickToEdit.showing_placeholder(
                                        ns)
    return ns


def _edit(field):
    # No field is open: `edit` closes whatever is (`close_open_field`), and a
    # stand-in left open by an earlier test is not this test's business.
    composites._editing = None
    composites.ClickToEdit.edit(field)


def _commit(field, **kwargs):
    composites.ClickToEdit.commit(field, **kwargs)


def test_the_editor_does_not_open_on_the_placeholder():
    field = _field(PLACEHOLDER)
    _edit(field)
    assert field.var.get() == '', \
        'the editor must start empty, not offering "<unset>" as the value'
    assert field._was == PLACEHOLDER, 'the label has to get its word back'


def test_a_real_value_stays_in_the_editor():
    """Only the placeholder is cleared. A defined field opens on what it is,
    so a small correction does not mean retyping the name."""
    field = _field('Plural')
    _edit(field)
    assert field.var.get() == 'Plural'


def test_closing_without_choosing_puts_the_placeholder_back_and_sets_nothing():
    """`close_open_field` commits this field when another is clicked, so a
    commit is not evidence that anything was chosen."""
    set_to = []
    field = _field(PLACEHOLDER, on_commit=set_to.append)
    _edit(field)
    _commit(field)
    assert field.var.get() == PLACEHOLDER, 'the line still reads "<unset>"'
    assert set_to == [], 'the placeholder must never reach the setter'


def test_choosing_a_field_name_reaches_the_setter():
    set_to = []
    field = _field(PLACEHOLDER, on_commit=set_to.append)
    _edit(field)
    field.var.set('Imperative')     # what picking or typing does
    _commit(field)
    assert set_to == ['Imperative']
    assert field.var.get() == 'Imperative'


def test_the_resume_hook_still_fires_on_an_abandoned_field():
    """`after_commit` belongs to whoever OPENED the field (`assure_second_forms`)
    and clears itself on the way through. Suppressing it along with the setter
    would leave the hook armed for a later, unrelated edit of the same field —
    Kent: "ONLY ONLY ONLY if it got there from runcheck. NEVER runcheck just
    because that was set."."""
    called = []
    field = _field(PLACEHOLDER)
    field.after_commit = lambda value: called.append(value)
    _edit(field)
    _commit(field)
    assert called == [PLACEHOLDER], 'the hook must run so it can clear itself'


def test_a_field_with_no_placeholder_is_unaffected():
    field = _field('Plural', placeholder=None)
    _edit(field)
    assert field.var.get() == 'Plural'
    _commit(field)
    assert field.var.get() == 'Plural'


def test_the_window_can_be_asked_to_assure_the_fields():
    """The method that opens the field lives on the StatusFrame, because that
    is what holds the widgets — but backend code can only reach the WINDOW
    (`task.ui`), which is why `runcheck` raised AttributeError on it
    (Kent, 2026-09-17). The forwarder is the fix; this guards the name."""
    from frontend import ui_shell
    assert hasattr(ui_shell.TaskDressing, 'assure_second_forms')

    stand_in = types.SimpleNamespace()       # a window with no settings pane
    assert ui_shell.TaskDressing.assure_second_forms(stand_in) is True, \
        'no pane means no field to open, and work must not block on it'


def test_the_sentinel_has_one_owner():
    """`fieldsvalue` shows it and the setters refuse it; both read it from
    here, so display and refusal cannot drift apart.

    `Settings`, not `SettingsManager`: `program.settings` IS a `Settings`
    (it assigns itself, settings/__init__.py:1271), and that is the object
    both `fieldsvalue` and `_refuse_unset_field` read the sentinel from.
    `SettingsManager` is the JSON-domain manager underneath it. The first
    version of this test named the wrong one (Kent's pytest run,
    2026-09-17)."""
    from settings import Settings
    assert Settings.UNSETFIELD == PLACEHOLDER
