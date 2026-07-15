# coding=UTF-8
"""UI presenter for lexicon operations (WordCollection, Parse).

Backend lexicon.py delegates all UI widget creation here, so it has
zero frontend imports.
"""
from frontend import ui
from frontend.presenter_base import PresenterBase
from frontend.ui_shell import ImageFrame


class LexiconPresenter(PresenterBase):
    """Handles UI widget creation for WordCollection and Parse workflows."""

    def scrolling_button_frame(self, parent, **kwargs):
        return ui.ScrollingButtonFrame(parent, **kwargs)

    def window(self, parent, **kwargs):
        return ui.Window(parent, **kwargs)

    def image(self, path):
        return ui.Image(path)

    def image_frame(self, parent, url=None, **kwargs):
        # ImageFrame takes (parent, url) — callers pass url positionally or
        # as a keyword (the image-selection grid); 'sense' here was stale.
        return ImageFrame(parent, url, **kwargs)

    @property
    def LEFT(self):
        return ui.LEFT
