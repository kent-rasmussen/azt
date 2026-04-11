# coding=UTF-8
"""Standalone Variable classes for non-tkinter backends.

These replicate the tkinter Variable API (get, set, trace_add, trace_remove)
without any tkinter dependency. Used by ui_webview; the tkinter backend
continues using tkinter's own Variable classes.
"""
import threading


class Variable:
    """General-purpose observable variable, analogous to tkinter.Variable."""
    _id_counter = 0
    _id_lock = threading.Lock()

    def __init__(self, value=None, name=None):
        self._value = value if value is not None else ''
        self._name = name or self._generate_name()
        self._traces = {}  # {trace_id: (mode, callback)}

    @classmethod
    def _generate_name(cls):
        with cls._id_lock:
            cls._id_counter += 1
            return f'PY_VAR{cls._id_counter}'

    def get(self):
        return self._value

    def set(self, value):
        old = self._value
        self._value = value
        if old != value:
            self._fire_traces('write')

    def trace_add(self, mode, callback):
        """Register a callback for variable changes.

        mode: 'write', 'read', or 'unset' (matching tkinter API).
        callback: called as callback(var_name, index, mode) — same signature
                  as tkinter trace callbacks. The arguments are kept for
                  compatibility but most callers use *args and ignore them.
        Returns a trace id string for use with trace_remove.
        """
        trace_id = f'trace_{id(callback)}_{len(self._traces)}'
        self._traces[trace_id] = (mode, callback)
        return trace_id

    def trace_remove(self, mode, trace_id):
        """Remove a previously registered trace."""
        self._traces.pop(trace_id, None)

    def _fire_traces(self, mode):
        for tid, (tmode, cb) in list(self._traces.items()):
            if tmode == mode:
                try:
                    cb(self._name, '', mode)
                except Exception:
                    import traceback
                    traceback.print_exc()


class StringVar(Variable):
    """String-valued observable variable."""
    def __init__(self, value=None, name=None):
        super().__init__(value=value if value is not None else '', name=name)

    def set(self, value):
        super().set(str(value))


class IntVar(Variable):
    """Integer-valued observable variable."""
    def __init__(self, value=None, name=None):
        super().__init__(value=value if value is not None else 0, name=name)

    def get(self):
        return int(self._value)

    def set(self, value):
        super().set(int(value))


class BooleanVar(Variable):
    """Boolean-valued observable variable."""
    def __init__(self, value=None, name=None):
        super().__init__(
            value=value if value is not None else False, name=name
        )

    def get(self):
        return bool(self._value)

    def set(self, value):
        super().set(bool(value))
