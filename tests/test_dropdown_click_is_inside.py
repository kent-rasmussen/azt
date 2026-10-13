"""A click on an open dropdown's option is a click INSIDE the field.

Under tkinter a ttk Combobox's list is Tk's own `<combobox>.popdown.f.l`,
which Python never created, so the click reaches the click-away watch with
`event.widget` as a path STRING. The watch walked `master` on it, found
nothing, called the click "away", and cancelled the field before the pick
landed (Kent, 2026-10-12: choosing a second form field from the list did
nothing).
"""
from types import SimpleNamespace

import pytest

composites = pytest.importorskip('frontend.composites')
inside = composites._click_landed_inside


class Box:
    def __init__(self, path):
        self.path = path

    def __str__(self):
        return self.path


def field(path='.!frame.!clicktoedit'):
    return SimpleNamespace(box=Box(path), _click_was_inside=False)


def test_the_dropdown_list_is_inside_its_field():
    f = field()
    click = SimpleNamespace(widget='.!frame.!clicktoedit.!combobox.popdown.f.l')
    assert inside(click, f)


def test_another_widgets_path_is_outside():
    f = field()
    assert not inside(SimpleNamespace(widget='.!frame.!clicktoedit2.!entry'), f)
    assert not inside(SimpleNamespace(widget='.!other.popdown.f.l'), f)


def test_the_box_itself_is_inside():
    f = field()
    assert inside(SimpleNamespace(widget='.!frame.!clicktoedit'), f)
