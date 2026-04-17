# coding=UTF-8
"""Protocol that backend mixins use for UI operations.

Backend code should interact with the UI only through methods on self.ui
(an instance of this protocol). The tkinter implementation is in
frontend/ui_shell.py (TaskDressing). A test stub could provide a headless
implementation.
"""

class TaskUI:
    """Abstract interface for task UI operations."""

    def show_run_window(self, msg=None, title=None):
        """Create and show a secondary work window. Returns a window handle."""
        raise NotImplementedError

    def clear_run_window(self):
        """Destroy the current run window if it exists."""
        raise NotImplementedError

    def hide(self):
        """Hide the task window."""
        raise NotImplementedError

    def show(self):
        """Show the task window."""
        raise NotImplementedError

    def wait_for_window(self, window):
        """Block until window is destroyed."""
        raise NotImplementedError

    def show_progress(self, value):
        """Update progress indicator."""
        raise NotImplementedError

    def drive_work(self, generator, on_done=None):
        """Consume a work generator one yield at a time, letting the
        event loop paint between chunks. Calls waitdone() on completion,
        then on_done() if provided."""
        raise NotImplementedError

    @property
    def run_window(self):
        """The current secondary work window, or None."""
        raise NotImplementedError

    @property
    def exit_requested(self):
        """Whether the user has requested exit."""
        raise NotImplementedError
