# coding=UTF-8
"""UI presenter for lexicon operations (WordCollection, Parse).

Backend lexicon.py delegates all UI widget creation here, so it has
zero frontend imports.
"""
from frontend import ui
from frontend.ui_shell import ImageFrame


class LexiconPresenter:
    """Handles UI widget creation for WordCollection and Parse workflows."""

    # -- Widget factories --

    def frame(self, parent, **kwargs):
        return ui.Frame(parent, **kwargs)

    def label(self, parent, **kwargs):
        return ui.Label(parent, **kwargs)

    def button(self, parent, **kwargs):
        return ui.Button(parent, **kwargs)

    def string_var(self, *args, **kwargs):
        return ui.StringVar(*args, **kwargs)

    def entry_field(self, parent, **kwargs):
        return ui.EntryField(parent, **kwargs)

    def scrolling_frame(self, parent, **kwargs):
        return ui.ScrollingFrame(parent, **kwargs)

    def scrolling_button_frame(self, parent, **kwargs):
        return ui.ScrollingButtonFrame(parent, **kwargs)

    def window(self, parent, **kwargs):
        return ui.Window(parent, **kwargs)

    def image(self, path):
        return ui.Image(path)

    def image_frame(self, parent, sense, **kwargs):
        return ImageFrame(parent, sense, **kwargs)

    @property
    def LEFT(self):
        return ui.LEFT
