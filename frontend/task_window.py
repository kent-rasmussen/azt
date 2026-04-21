# coding=UTF-8
"""TaskWindow: tkinter window wrapper for task logic objects.

Separates the window (TaskDressing/Toplevel) from the task logic
(TaskBase). TaskWindow delegates unknown attribute reads to self.task
so that TaskDressing can transparently access task flags and methods.
"""
from frontend.ui_shell import TaskDressing


class TaskWindow(TaskDressing):
    """Tkinter window that wraps a TaskBase instance."""

    def __getattr__(self, name):
        """Delegate unknown attributes to the wrapped task object.

        Uses object.__getattribute__ to read from the task, which
        bypasses the task's own __getattr__ and prevents infinite
        recursion (task.__getattr__ delegates back to self.ui).
        """
        task = object.__getattribute__(self, 'task')
        return object.__getattribute__(task, name)

    def __init__(self, task, parent, **kwargs):
        self.task = task        # window → task (for flag reads)
        task.ui = self          # task → window (for UI delegation)
        self.program = task.program
        TaskDressing.__init__(self, parent, **kwargs)
