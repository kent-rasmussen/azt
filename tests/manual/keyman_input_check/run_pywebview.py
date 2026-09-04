# coding=UTF-8
"""A-Z+T manual test: Keyman input check, tier 2 - the REAL host.

Tier 1 (run_edge.cmd) tests Chromium's input path. This tests WebView2 hosted
inside a *Python* process, which is the configuration a ported A-Z+T page would
actually run in - host-window message-loop handling is a known WebView2 input
variable, so tier 1 passing does not guarantee this passes.

    pip install pywebview            # Windows: also pulls pythonnet
    python run_pywebview.py

On Linux, pick the engine with the same env var pywebview uses:

    PYWEBVIEW_GUI=gtk python run_pywebview.py     # WebKitGTK
    PYWEBVIEW_GUI=qt  python run_pywebview.py     # QtWebEngine (= Chromium)

Deliberately dependency-free apart from pywebview itself: this file must run on
a field machine that has only done `git pull`, without importing any of azt.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PAGE = os.path.join(HERE, 'index.html')


def main():
    try:
        import webview
    except ImportError:
        sys.stderr.write(
            "pywebview is not installed in this interpreter.\n"
            "  pip install pywebview\n"
            "Or just use run_edge.cmd, which needs nothing installed.\n")
        return 2
    if not os.path.exists(PAGE):
        sys.stderr.write("Cannot find {}\n".format(PAGE))
        return 1
    # Served over pywebview's bundled server rather than file://, which its own
    # docs recommend against.
    webview.create_window('Keyman input check - A-Z+T', PAGE,
                          width=1100, height=900)
    webview.start(http_server=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
