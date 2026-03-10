# coding=UTF-8
from frontend.ui_shell import TaskDressing

class Task(TaskDressing):
    def __init__(self, program, _parent=None):
        self.program = program
        parent = _parent if _parent is not None else self.program.taskchooser
        TaskDressing.__init__(self, parent)
