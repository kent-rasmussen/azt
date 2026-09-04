# coding=UTF-8
"""A-Z+T manual test: tone feature check, tier 2 - the REAL host.

Tier 1 (run_edge.cmd) shows the page in the Edge browser. This shows it in
pywebview, which is the configuration a ported A-Z+T page would actually run
in: WebView2 on Windows, WebKitGTK or QtWebEngine on Linux. Font resolution and
OpenType feature support can differ between a browser and an embedded webview,
so tier 1 passing does not guarantee this passes.

    pip install pywebview            # Windows: also pulls pythonnet
    python run_pywebview.py

    python run_pywebview.py /path/to/CharisSIL-tstv-Regular.ttf   # explicit

On Linux pywebview also needs a host toolkit, and neither comes with pip alone:

    PYWEBVIEW_GUI=gtk python run_pywebview.py     # WebKitGTK
    PYWEBVIEW_GUI=qt  python run_pywebview.py     # QtWebEngine (= Chromium)

WHY THIS SCRIPT HUNTS FOR A FONT: dragging a file onto the page works in a
browser but not reliably in an embedded webview - observed 2026-09-04, drop
worked in the browser and did nothing under pywebview. Rather than depend on
it, this finds a `-tstv` build itself and injects the bytes through
`evaluate_js`, which needs no drop, no file dialog and no reachable URL. The
page's drop zone and file picker still work where they work.

Deliberately dependency-free apart from pywebview: it must run on a field
machine that has only done `git pull`, without importing any of azt. The font
search therefore duplicates a little of `utilities/fonts.py` on purpose -
`render_pil_baseline.py` is the one that uses the real table.
"""
import base64
import glob
import json
import os
import platform
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
PAGE = os.path.join(HERE, 'index.html')

# evaluate_js takes a string; a megabyte in one call is asking for trouble in
# some backends, so the base64 goes over in pieces and is joined in the page.
CHUNK = 64 * 1024

# Printed when pywebview is installed but has no GUI toolkit to host it - the
# failure a fresh Linux checkout actually hits. pywebview's own exception says
# only "install QT or GTK", which is true but not actionable.
NO_TOOLKIT = """
pywebview is installed, but neither of its Linux hosts is:
  - GTK needs the SYSTEM package (pip install PyGObject wants dev headers), and
    a venv that can see it:
        sudo apt install -y python3-gi gir1.2-webkit2-4.1
        python3 -m venv --system-site-packages /tmp/wv_gtk
        /tmp/wv_gtk/bin/pip install pywebview
        PYWEBVIEW_GUI=gtk /tmp/wv_gtk/bin/python {script}
  - Qt is pure pip, no sudo, and QtWebEngine IS Chromium, so it matches what
    the Windows field machines run:
        python3 -m venv /tmp/wv_qt
        /tmp/wv_qt/bin/pip install "pywebview[qt]"
        /tmp/wv_qt/bin/python {script}
If a GTK window opens but stays blank, retry with
WEBKIT_DISABLE_DMABUF_RENDERER=1 - that is the NVIDIA/Wayland DMABUF bug.
"""


def font_dirs():
    """Where fonts actually land. Mirrors utilities.fonts.font_dirs, including
    the per-user Windows directory a font-dialog 'Install' writes to."""
    if platform.system() == 'Windows':
        local = (os.environ.get('LOCALAPPDATA')
                 or os.path.join(os.path.expanduser('~'), 'AppData', 'Local'))
        dirs = [os.path.join(os.environ.get('WINDIR', r'C:\Windows'), 'Fonts'),
                os.path.join(local, 'Microsoft', 'Windows', 'Fonts')]
    else:
        dirs = ['/usr/share/fonts', '/usr/local/share/fonts',
                os.path.expanduser('~/.fonts'),
                os.path.expanduser('~/.local/share/fonts'),
                '/System/Library/Fonts', '/Library/Fonts',
                os.path.expanduser('~/Library/Fonts')]
    return [d for d in dirs if os.path.isdir(d)]


def find_tstv():
    """First '*tstv*' font file on this machine, or None. The tstv builds are
    what utilities/fonts.py puts FIRST for every family, so this is the file
    the app itself would draw with."""
    for d in font_dirs():
        hits = sorted(glob.glob(os.path.join(glob.escape(d), '**', '*tstv*.tt*'),
                                recursive=True))
        if hits:
            return hits[0]
    return None


def inject_font(window, path):
    """Hand the page a font file's bytes. Returns True if the page took it."""
    try:
        with open(path, 'rb') as fh:
            b64 = base64.b64encode(fh.read()).decode('ascii')
    except (IOError, OSError) as e:
        print("Could not read {}: {}".format(path, e))
        return False

    # The page may not have parsed its script yet; wait for the hook rather
    # than guessing at a load event, whose name has moved across pywebview
    # versions.
    for _ in range(100):
        try:
            if window.evaluate_js('typeof window.aztInstallFontB64') == 'function':
                break
        except Exception:
            pass
        time.sleep(0.1)
    else:
        print("The page never exposed aztInstallFontB64; not injecting.")
        return False

    try:
        window.evaluate_js('window.__aztFontParts = [];')
        for i in range(0, len(b64), CHUNK):
            window.evaluate_js('window.__aztFontParts.push("{}");'
                               ''.format(b64[i:i + CHUNK]))
        result = window.evaluate_js(
            'window.aztInstallFontB64({}, window.__aztFontParts.join(""))'
            ''.format(json.dumps(os.path.basename(path))))
    except Exception as e:
        print("Injection failed: {}".format(e))
        return False
    if result != 'ok':
        print("The page rejected the font: {}".format(result))
        return False
    print("Injected {} ({:.0f} KB) - selectable in the page as the dropped "
          "font.".format(path, len(b64) * 3 / 4 / 1024))
    return True


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

    fontpath = sys.argv[1] if len(sys.argv) > 1 else find_tstv()
    if fontpath and not os.path.exists(fontpath):
        sys.stderr.write("No such font file: {}\n".format(fontpath))
        return 1
    if fontpath:
        print("Found a staveless build: {}".format(fontpath))
    else:
        print("No '*tstv*' font file on this machine - so the page's dropped-font\n"
              "column will stay empty unless you pick a file by hand. That is\n"
              "itself the answer to agenda/tstv_font_availability.md for this box.")

    # Served over pywebview's bundled server rather than file://, which its own
    # docs recommend against.
    window = webview.create_window('Tone feature check - A-Z+T', PAGE,
                                   width=1300, height=950)

    def after_start(win):
        if fontpath:
            inject_font(win, fontpath)

    try:
        webview.start(after_start, window, http_server=True)
    except Exception as e:
        # WebViewException is what "no GTK, no QT" raises; catching it by name
        # would mean importing webview.errors, and any startup failure wants
        # this hint anyway.
        if 'QT' in str(e) or 'GTK' in str(e):
            sys.stderr.write(NO_TOOLKIT.format(script=os.path.abspath(__file__)))
            return 3
        raise
    return 0


if __name__ == '__main__':
    sys.exit(main())
