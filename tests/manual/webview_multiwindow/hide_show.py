# coding=UTF-8
"""A-Z+T manual test: does hide() then show() bring a pywebview window back?

THE LAST UNTESTED ASSUMPTION. A-Z+T's whole window model rests on it: task
windows are created withdrawn and revealed later, and the Wait window is
explicitly "built ONCE on the root and then withdrawn/deiconified rather than
destroyed/rebuilt per wait". Under the webview backend no task window has ever
been seen on screen, and the log now shows the reveal arriving correctly and
being accepted:

    window 10: replaying deferred ['set_title','set_title','hide','show','show']

...with no window appearing. Everything upstream of pywebview is proven; what
was never checked is whether hide()/show() round-trips at all. The earlier
multi-window probe only ever created and DESTROYED windows.

    python hide_show.py                  # create visible, then hide/show
    python hide_show.py --start-hidden   # create hidden, then show
    PYWEBVIEW_GUI=gtk python hide_show.py
    PYWEBVIEW_GUI=qt  python hide_show.py

WATCH THE SCREEN and compare with the console, which announces each step
before it takes it. The window is titled so it is findable in a window list.
Deliberately imports nothing from azt.
"""
import os
import sys
import time

PAGE = ('<html><body style="font:20px system-ui;padding:30px;'
        'background:#8cd9bf">'
        '<h2 id="h">extra window</h2>'
        '<p>If you can read this, the window is mapped.</p></body></html>')

PAUSE = 2.5
ROUNDS = 3


def main():
    try:
        import webview
    except ImportError:
        sys.stderr.write("pywebview is not installed in this interpreter.\n")
        return 2

    start_hidden = '--start-hidden' in sys.argv
    main_window = webview.create_window(
        'hide/show probe — MAIN', html=PAGE.replace('extra window', 'main window'),
        width=600, height=300)

    def work(window):
        print("")
        print("=== creating the extra window {} ===".format(
            'HIDDEN' if start_hidden else 'VISIBLE'))
        extra = webview.create_window(
            'hide/show probe — EXTRA', html=PAGE,
            width=600, height=300, hidden=start_hidden)
        time.sleep(PAUSE)
        print("    -> is 'EXTRA' on screen now? (expected: {})".format(
            'NO' if start_hidden else 'yes'))

        if start_hidden:
            print("--- show() on a window created hidden")
            extra.show()
            time.sleep(PAUSE)
            print("    -> did 'EXTRA' APPEAR? (this is the case A-Z+T uses)")

        for n in range(1, ROUNDS + 1):
            print("--- round {}: hide()".format(n))
            extra.hide()
            time.sleep(PAUSE)
            print("    -> did 'EXTRA' DISAPPEAR?")
            print("--- round {}: show()".format(n))
            extra.show()
            time.sleep(PAUSE)
            print("    -> did 'EXTRA' COME BACK?")

        print("")
        print("Done. If show() never brought it back, that is the fault:")
        print("pywebview's {} backend does not re-map a hidden window, and"
              "".format(os.environ.get('PYWEBVIEW_GUI') or 'default'))
        print("A-Z+T's withdraw/deiconify model cannot work on it as written.")
        print("Close the MAIN window to finish.")

    webview.start(work, main_window)
    return 0


if __name__ == '__main__':
    sys.exit(main())
