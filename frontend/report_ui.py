# coding=UTF-8
"""UI presenter for report result rendering.

Backend generator.py delegates all UI widget creation here, so it has
zero frontend imports.
"""
from frontend import ui_tkinter as ui
from frontend.ui_shell import ResultWindow


class ReportPresenter:
    """Handles UI widget creation for report results display."""

    def create_results_frame(self, parent_frame):
        """Create the results container with scrolling. Returns a results frame
        with .scroll and .row attributes."""
        results = ui.Frame(parent_frame, width=800)
        results.grid(column=0,
                     row=parent_frame.grid_info()['row'] + 1,
                     columnspan=5,
                     sticky=(ui.N, ui.S, ui.E, ui.W))
        results.scroll = ui.ScrollingFrame(results)
        results.scroll.grid(column=0, row=1)
        results.row = 0
        return results

    def create_scrolling_frame(self, parent):
        """Create a scrolling frame. Returns frame with .content attribute."""
        sf = ui.ScrollingFrame(parent)
        sf.grid(row=0, column=0)
        return sf

    def add_label(self, parent, text, **kwargs):
        """Create a label widget in the given parent."""
        return ui.Label(parent, text=text, **kwargs)

    def create_result_window(self, parent, msg=None):
        """Create a ResultWindow for displaying report output."""
        return ResultWindow(parent, msg=msg)
