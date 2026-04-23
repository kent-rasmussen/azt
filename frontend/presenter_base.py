# coding=UTF-8
"""Shared widget factory methods for presenter classes.

Backend modules delegate UI widget creation to presenters so they have
zero frontend imports.  This base class provides the common factories
used by SortPresenter, LexiconPresenter, and others.
"""
from frontend import ui


class PresenterBase:
    """Common widget factories shared across all presenters."""

    def label(self, parent, **kwargs):
        return ui.Label(parent, **kwargs)

    def frame(self, parent, **kwargs):
        return ui.Frame(parent, **kwargs)

    def button(self, parent, **kwargs):
        return ui.Button(parent, **kwargs)

    def string_var(self, *args, **kwargs):
        return ui.StringVar(*args, **kwargs)

    def entry_field(self, parent, **kwargs):
        return ui.EntryField(parent, **kwargs)

    def scrolling_frame(self, parent, **kwargs):
        return ui.ScrollingFrame(parent, **kwargs)
