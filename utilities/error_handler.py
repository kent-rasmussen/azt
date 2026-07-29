# coding=UTF-8
"""Backend-safe error notification.

Backend modules call `notify_error(text, **kwargs)` instead of importing
ErrorNotice from the frontend. At startup, `set_error_handler()` is called
to wire this to the real UI ErrorNotice dialog.

Before the UI is initialized, errors are logged to stderr.
"""
import logging
log = logging.getLogger(__name__)

def _default_handler(text, **kwargs):
    """Fallback before UI is initialized."""
    log.error(f"ErrorNotice (no UI): {text}")

_handler = _default_handler

def notify_error(text, **kwargs):
    """Show an error to the user. Backend-safe — no tkinter dependency.
    Returns whatever the handler returns (the notice window instance for
    the ErrorNotice handler), so callers that need to track a single
    open dialog can — see App.collab_offer_reload (F6)."""
    return _handler(text, **kwargs)

def set_error_handler(handler):
    """Set the error display function. Called once at startup with ErrorNotice."""
    global _handler
    _handler = handler


def _default_notifier(text, **kwargs):
    """Fallback before UI is initialized."""
    log.info(f"NotifyUser (no UI): {text}")

_notifier = _default_notifier

def notify_user(text, **kwargs):
    """Tell the user something WITHOUT interrupting the work in front of them.

    The counterpart of notify_error: use notify_error when the user MUST deal
    with it now, and notify_user for everything that is merely worth saying —
    "that group is done", "you're not finished here", "we'll retry the rest
    later". Appends to ONE status window for the whole session instead of
    building a Toplevel per message (frontend.status_window); accepts and
    ignores ErrorNotice's `wait`/`parent` kwargs so a call site converts by
    changing only the function name.

    Backend-safe — no tkinter dependency, wired at startup by
    set_user_notifier()."""
    return _notifier(text, **kwargs)

def set_user_notifier(notifier):
    """Set the status-message function. Called at startup with
    frontend.status_window.notify_user."""
    global _notifier
    _notifier = notifier
