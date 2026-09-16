# coding=UTF-8
"""One widget gallery, either backend, chosen the way the app chooses.

    python -m frontend.gallery              # tkinter (the default)
    python -m frontend.gallery --webview
    python -m frontend.gallery --webview --engine=qt

Kent, 2026-09-14: "ui_tkinter.py has a test suite that allows me to check
things more directly. can we do something similar for webviews? nice if it
were in ui, and sensitive to --webviews like the program generally." Then, on
scope: "go through the rest of the testapps (there are a few) and make sure
everything is present somewhere in this gallery. use tabs to get everything
on the page."

**ONE MODULE, NOT A WEBVIEW TWIN.** Everything goes through
`from frontend import ui`, so the same page is built by whichever backend the
switch selects. That makes it a PARITY HARNESS rather than a demo: run it
twice and any difference is a difference in the backends, not in the test.
Two separate galleries would drift, and the drift would be invisible.

It has already earned that twice, both times by the TKINTER run disagreeing
with what the page claimed: the anchor cells were not bigger than their text
(so no backend could have shown an anchor), and the entry-field row seeded
the variable with the same string the reader was told to type (so a broken
binding looked identical to a working one).

## WHAT IS COVERED, and where it came from

`ui_tkinter.testapp/2/3/4/Y` are five separate `__main__` pages, and they are
left exactly as they are (`python -m frontend.ui_tkinter` still runs
`testapp`); ADR 0004's amendment makes "tkinter must not regress" an
invariant, and that includes Kent's own tools. Their coverage is gathered
here, plus the options from
`agenda/webview_discards_widget_options.md`:

  * testapp2  — drag and drop on labels
  * testapp3  — a widget parented to each kind of container
  * testapp4  — ScrollingButtonFrame with image/compound/bsticky
  * testappY  — one variable shared by a label and an entry
  * testapp   — everything else: the button/radio/check/list/combo family,
                Message vs Label, wraplength, tooltips, progress bars in
                both orientations, key and mouse bindings, Variable types

## EVERY SPECIMEN SAYS WHAT IT SHOULD LOOK LIKE

In words, beside the widget — never by colour, and never "the third one"
(`~/.claude-sil/CLAUDE.md`: identify things by text, title, position or
shape). A row reading "raised should look to stand out" is checkable by eye,
and a fault is reportable without anyone having to describe a hue.
"""
import sys

from frontend import ui, backend, composites
from utilities import logsetup
log = logsetup.getlog(__name__)
logsetup.setlevel('INFO', log)

ANCHORS = ('nw', 'n', 'ne', 'w', 'c', 'e', 'sw', 's', 'se')
# A SPACER THAT SURVIVES HTML. `" " * 18` sizes a cell in tkinter and
# measures zero in a page — runs of whitespace collapse — so every cell
# whose width or height came from blank text was full-size under one backend
# and text-size under the other, and no alignment test inside it could show
# anything. Printable characters, so both backends measure the same string,
# and they read as the cell's ruler.
RULER = "|" + "-" * 20 + "|"
# The sticky cells need much more slack than the anchor cells: their labels
# say what they are ("sticky='ew'"), so the label is already wide, and a cell
# only as wide as its label shows nothing at all — 'w', 'e' and '' all land in
# the same place, which is exactly what the anchor row's first two versions
# did. This ruler is wider than the longest of those labels by a clear margin.
RULER_WIDE = "|" + "-" * 34 + "|"
RELIEFS = ('flat', 'solid', 'raised', 'sunken', 'groove', 'ridge')
CHOICES = ("choice 1", "choice 2", "choice 3", "choice 4")


def _note(parent, text, row, column=0, columnspan=1, font='small'):
    """A line of instructions. A plain Label with no anchor and no relief, so
    it cannot itself be a casualty of what it is describing."""
    return ui.Label(parent, text=text, font=font, row=row, column=column,
                    columnspan=columnspan, sticky='w')


def _fill(widget, rows=1, cols=1):
    """Let a frame's own cells take the whole size the frame was given.

    TKINTER HAS TO BE TOLD; A CSS GRID DOES NOT. `sticky='nsew'` stretches a
    widget into the space its ROW AND COLUMN have, and a tkinter row or
    column takes space beyond its content only if it has WEIGHT. So a cell
    frame stretched by its neighbours still laid its own single row and
    column out at text size, the label filled that, and `anchor` and
    `sticky` both had nothing to work in — every letter top-left, all four
    sticky boxes identical (Kent, tkinter, 2026-09-14: "neither anchors nor
    sticky working here?"). The same page was correct under webview, where a
    grid track fills its container by itself.

    Worth stating plainly, because it is a real rule for app code and not a
    harness quirk: a page written against webview alone can rely on
    stretching that tkinter will not do, and the fix is always the weight.
    """
    for i in range(rows):
        try:
            widget.grid_rowconfigure(i, weight=1)
        except Exception as e:
            log.info("gallery: no row weight available (%r)", e)
    for i in range(cols):
        try:
            widget.grid_columnconfigure(i, weight=1)
        except Exception as e:
            log.info("gallery: no column weight available (%r)", e)


def _try(what, fn, parent, row):
    """Build one specimen; if it raises, SAY SO ON THE PAGE.

    Per specimen rather than per tab: a gallery exists to show what works,
    and one missing widget must not cost the other twenty on its tab. The
    failure is written where it happened, not only logged, because the page
    is the thing being read.
    """
    try:
        return fn()
    except Exception as e:
        log.error("gallery %s failed: %r", what, e)
        _note(parent, "{} FAILED: {!r}".format(what, e), row=row,
              columnspan=3)
        return None


# ── tab: Alignment ───────────────────────────────────────────────────────

def tab_align(nb):
    t = ui.Frame(nb)
    _note(t, "ANCHOR: nine bordered cells holding nothing but their letters. "
             "The '|' stacks at the right of each band set the row height and "
             "the '|---|' rulers along the bottom set the column width, from "
             "OUTSIDE the cells, so every cell is bigger than its text. The "
             "two letters in each should sit at the corner or edge the "
             "caption names, with plenty of room around them. "
             "tkinter places the whole text BLOCK, so N's pair straddles the "
             "centre line rather than starting at it. A rotated set (e.g. N "
             "at the left) means the flex axis was read wrong; all nine "
             "sitting in the same place means the anchor is not reaching the "
             "label.", row=0, columnspan=3)
    grid = ui.Frame(t, row=1, column=0, columnspan=3, sticky='w')
    # THE RULERS ARE IN CELLS OF THEIR OWN (Kent, 2026-09-14: "maybe we put
    # your misguided rulers into their own cells, so they expand these cells
    # without otherwise messing with them? then we could keep appropriate
    # cell boundaries"). Exactly right, and the previous version had the flaw
    # he is naming: the ruler and the '|' spacers were INSIDE each bordered
    # cell, so the cell's grid had to hold three things and the label's own
    # box was only one column of it — the letters could not use the width the
    # border was drawing, and the specimen was no longer a specimen.
    #   Now each bordered cell contains exactly ONE label, stretched into it
    # with sticky='nsew'. The size comes from neighbours in the same row and
    # column of the OUTER grid: a stack of three '|' at the right of each
    # band gives the rows their height, and a ruler under each column gives
    # the columns their width. Nothing the anchor is being tested on has
    # anything else in it.
    for band in range(3):
        spacer = ui.Frame(grid, row=band * 2, column=3, sticky='ns')
        for k in range(4):      # four rows tall, a quarter more than three
            ui.Label(spacer, text="|", font='small', row=k, column=0)
    for c in range(3):
        _note(grid, RULER, row=6, column=c)
    for n, a in enumerate(ANCHORS):
        # REAL BORDERED CELLS. Two earlier versions could not show the anchor
        # at all, and I explained why wrongly both times — the cause was
        # never established by reading, which is why `_measure_anchor`
        # reports computed values instead. What IS established: the cell has
        # a border, so a label failing to fill it is visible rather than
        # inferred. Kent: "can we not make actual cells with borders, so the
        # 'ruler's have real values and effects?"
        cell = ui.Frame(grid, row=(n // 3) * 2, column=n % 3, sticky='nsew',
                        padx=6, pady=6, borderwidth=1, relief='solid')
        _fill(cell)     # or the label fills text-size and never moves
        # ONE LABEL, NOTHING ELSE, and its SIZE FROM OUTSIDE. Two earlier
        # versions gave the cell its height from inside — first `ipady`,
        # which becomes padding and so leaves the content box exactly
        # text-height, then a sibling holding "\n\n\n", which is four lines
        # in tkinter and nothing at all in a page. Both left the label with
        # no spare space, and `align-items: flex-start` and `center` land in
        # the same pixel when there is none to distribute. The measurement
        # said so in one line: label 170x53 inside a 176x55 parent,
        # alignSelf=stretch, alignItems=flex-start — the stretch was working
        # and there was nothing to stretch into.
        ui.Label(cell, text=a.upper(), anchor=a, font='read',
                 row=0, column=0, sticky='nsew')
        _note(grid, "anchor={}".format(a),
              row=(n // 3) * 2 + 1, column=n % 3)

    _note(t, "RELIEF: six treatments, and 'flat' with no border at all. "
             "raised should look to stand out, sunken to be pressed in. These "
             "map 1:1 onto CSS border styles.", row=8, columnspan=3)
    bar = ui.Frame(t, row=9, column=0, columnspan=3, sticky='w')
    for n, r in enumerate(RELIEFS):
        cell = ui.Frame(bar, row=0, column=n, padx=4, pady=4,
                        borderwidth=3, relief=r)
        ui.Label(cell, text=r, row=0, column=0, ipadx=10, ipady=10)

    _note(t, "STICKY: the RAISED box in each cell is the label; the thin "
             "outline around it is the cell, made a good deal wider than the "
             "label by the ruler beneath it. Watch the raised box: 'ew' fills "
             "the cell edge to edge, 'w' is narrow at the left, 'e' narrow at "
             "the right, '' narrow and centred. If all four boxes look the "
             "same, sticky is not reaching the label.",
          row=10, columnspan=3)
    sbar = ui.Frame(t, row=11, column=0, columnspan=3, sticky='w')
    for n, s in enumerate(('ew', 'w', 'e', '')):
        # sticky='ew' ON THE CELL, or the ruler widens the COLUMN and the
        # cell sits narrow and centred inside it — the border would then
        # still be drawn tight around the label and nothing would have
        # changed. The cell must take the width before it can give the label
        # any room.
        cell = ui.Frame(sbar, row=0, column=n, padx=4, pady=4, sticky='ew',
                        borderwidth=1, relief='solid')
        _fill(cell)     # the cell's own column must take the width too
        # THE LABEL WEARS THE BORDER TOO (Kent: "sticky would probably be
        # more visually obvious if the cell that is sticky had a border?").
        # Right, and without it the row could barely be read: a stretched
        # label and an unstretched one are both invisible boxes, so only the
        # TEXT moved and 'ew' looked like a wider version of nothing. The
        # raised box makes the label's own extent the thing you watch.
        #   And NO ipadx: padding makes the LABEL wide, which is the opposite
        # of what this row needs — the cell has to be wider than the label or
        # there is nowhere for 'w' and 'e' to differ, the same mistake the
        # anchor cells made twice. The width comes from the ruler below.
        ui.Label(cell, text="sticky={!r}".format(s), sticky=s,
                 row=0, column=0, borderwidth=2, relief='raised')
        _note(sbar, RULER_WIDE, row=1, column=n)

    # THE HIGHLIGHT RING, which the app uses as a separator and not as a
    # focus ring (Kent, 2026-09-14: "let's add highlight options to the
    # gallery. we do actually use those"). `tasks.py:2064` and
    # `transcribe_glyph.py:422` both put a 10px one in the theme's white
    # around the comparison frame; `sort_ui.py:1193` turns one off.
    _note(t, "HIGHLIGHT RING: four labels, each captioned with the ring it "
             "was given — none, 1, 4 and 10 pixels. They must be visibly "
             "different thicknesses, and the ring sits OUTSIDE the black "
             "border each one also carries, so you should see two edges on "
             "the last three. Under tkinter the ring takes up space (the "
             "labels sit further apart); under webview it is an outline and "
             "overlaps instead, which is the one known difference.",
          row=12, columnspan=3)
    hbar = ui.Frame(t, row=13, column=0, columnspan=3, sticky='w')
    ring = getattr(getattr(t, 'theme', None), 'white', None) or 'black'
    for n, thick in enumerate((0, 1, 4, 10)):
        cell = ui.Frame(hbar, row=0, column=n, padx=10, pady=10)
        _try("highlightthickness={}".format(thick),
             lambda cell=cell, thick=thick: ui.Label(
                 cell, text="ring {}".format(thick or 'none'),
                 row=0, column=0, borderwidth=1, relief='solid',
                 highlightthickness=thick, highlightbackground=ring),
             cell, 0)
    return t


# ── tab: Controls ────────────────────────────────────────────────────────

def tab_controls(nb):
    t = ui.Frame(nb)
    row = 0
    _note(t, "STATE: 'live' and 'enabled later' must respond to a click; "
             "'born disabled' and 'disabled later' must NOT, and must look "
             "inert.", row=row, columnspan=3)
    bar = ui.Frame(t, row=row + 1, column=0, columnspan=3, sticky='w')
    said = ui.Label(bar, text="(nothing clicked yet)",
                    row=1, column=0, columnspan=4, sticky='w')

    def click(which):
        def go():
            said['text'] = "clicked: {}".format(which)
            log.info("gallery: clicked %s", which)
        return go

    ui.Button(bar, text="live", command=click('live'), row=0, column=0)
    ui.Button(bar, text="born disabled", command=click('born disabled'),
              state='disabled', row=0, column=1)
    b = ui.Button(bar, text="disabled later", command=click('disabled later'),
                  row=0, column=2)
    b['state'] = 'disabled'
    b2 = ui.Button(bar, text="enabled later", command=click('enabled later'),
                   state='disabled', row=0, column=3)
    b2['state'] = 'normal'
    row += 2

    _note(t, "BUTTONFRAME: five buttons from an optionlist, built by the "
             "frame rather than one at a time. The frame beside it is built "
             "from options that carry their own picture and description — "
             "each of its three must show the icon at its LEFT and read "
             "'opt 1 (1 of 3)'. RADIOBUTTONS below share one "
             "variable — picking one must clear the others, and the echo "
             "must follow. Then a RADIOBUTTONFRAME of four, '+0' to '+3', "
             "which must also share it. The pair labelled 'indicator' and 'no "
             "indicator' look DIFFERENT under tkinter (indicatoron=0 draws a "
             "button that stays pressed in) and the SAME under webview, which "
             "is deliberate — nothing in the app asks for it.",
          row=row, columnspan=3)
    fr = ui.Frame(t, row=row + 1, column=0, columnspan=3, sticky='w')
    _try("ButtonFrame", lambda: ui.ButtonFrame(
            fr, optionlist=range(5, 10), command=click('ButtonFrame'),
            row=0, column=0), fr, 0)
    # OPTIONS THAT CARRY THEIR OWN PICTURE AND DESCRIPTION — the 4-tuple
    # form, which `alphabet_chart.py:703` builds and nothing tested. Under
    # webview the frame threw away every button kwarg it was given and never
    # looked at the option's image, so both halves of this row were missing.
    _try("ButtonFrame with pictures", lambda: ui.ButtonFrame(
            fr, optionlist=[(i, "opt {}".format(i), "{} of 3".format(i),
                             'icon') for i in (1, 2, 3)],
            command=click('picture ButtonFrame'), compound='left',
            image_pixels=20, row=0, column=1), fr, 0)

    rb_var = ui.StringVar(value='')
    rb_echo = ui.Label(fr, text="radio: (none)", row=1, column=1, sticky='w')
    rb_var.trace_add('write',
                     lambda *a: rb_echo.configure(
                         text="radio: {!r}".format(rb_var.get())))
    rbox = ui.Frame(fr, row=1, column=0, sticky='w')
    _try("RadioButton", lambda: (
            ui.RadioButton(rbox, text="indicator", variable=rb_var, value='1',
                           row=0, column=0),
            ui.RadioButton(rbox, text="no indicator", variable=rb_var,
                           value='2', indicatoron=0, row=0, column=1)),
         rbox, 1)
    _try("RadioButtonFrame", lambda: ui.RadioButtonFrame(
            fr, variable=rb_var,
            optionlist=[(str(i), '+' + str(i)) for i in range(4)],
            indicatoron=1, row=2, column=0), fr, 2)
    row += 2

    _note(t, "CHECKBOXES: the first three must be three visibly DIFFERENT "
             "sizes, smallest in the middle, and each must show a mark when "
             "ticked. The last two are tkinter's indicator variants — under "
             "webview all of these are a native checkbox, which is correct: "
             "tkinter draws its own from theme images because it has none.",
          row=row, columnspan=3)
    cbar = ui.Frame(t, row=row + 1, column=0, columnspan=3, sticky='w')
    for n, (label, kw) in enumerate((
            ("default", {}),
            ("image_pixels=12", {'image_pixels': 12,
                                 'image_scaleto': 'height'}),
            ("large_images", {'large_images': True}),
            ("indicatoron", {'indicatoron': True}),
            ("selectimage=None", {'selectimage': None}))):
        _try("CheckButton {}".format(label),
             lambda label=label, kw=kw, n=n: ui.CheckButton(
                 cbar, text=label, variable=ui.BooleanVar(value=(n == 1)),
                 anchor='c', row=n // 3, column=n % 3, sticky='w', **kw),
             cbar, 2)
    _note(cbar, "(the second starts ticked, so a missing mark shows at once)",
          row=2, columnspan=3)
    return t


# ── tab: Text ────────────────────────────────────────────────────────────

def tab_text(nb):
    t = ui.Frame(nb)
    _note(t, "ENTRY FIELD, three things at once: the box should ALREADY read "
             "'SEEDED' before you touch it (initial value), in the large "
             "reading font (not the default size), and typing should change "
             "the label beside it (two-way binding).", row=0, columnspan=3)
    bar = ui.Frame(t, row=1, column=0, columnspan=3, sticky='w')
    # DISTINCT STRINGS. An earlier version seeded the variable with the same
    # text it told the reader to type, so the echo read the same whether the
    # binding worked or not, and Kent reasonably asked whether the value was
    # meant to be a default. It was meant to be there at startup; it was not.
    var = ui.StringVar(value="SEEDED")
    ui.EntryField(bar, text=var, font='readbig', row=0, column=0,
                  render=False)
    echo = ui.Label(bar, text="(echo)", row=0, column=1, sticky='w')
    var.trace_add('write',
                  lambda *a: echo.configure(text="echo: " + (var.get() or '')))
    echo['text'] = "echo: " + var.get()

    _note(t, "ONE VARIABLE, TWO WIDGETS (testappY): the label below shows the "
             "same variable as the field above. Typing must change both.",
          row=2, columnspan=3)
    ui.Label(t, textvariable=var, font='read', row=3, column=0, sticky='w')

    _note(t, "COMBOBOX and LISTBOX: the combo must offer four choices and "
             "report the pick. The list is rebuilt in whichever SELECTMODE "
             "the radio row names: 'multiple' and 'extended' must report more "
             "than one row at a time, 'single' and 'browse' exactly one. The "
             "call count in the report is what tells a list that reports an "
             "empty selection apart from one that never calls back at all — "
             "the distinction the first version could not make (two rows "
             "ticked on the page, 'list selection: (none)' beside them).",
          row=4, columnspan=3)
    lbar = ui.Frame(t, row=5, column=0, columnspan=3, sticky='w')
    # ONE REPORT LINE EACH. They shared a single label, so whichever fired
    # last overwrote the other — the combo's report hid the list's entirely,
    # and a working list looked like a dead one. The same mistake as seeding
    # the entry with the text the reader was told to type: two things, one
    # output.
    combo_says = ui.Label(lbar, text="combo variable: (unset)", row=1,
                          column=0, sticky='w')
    list_says = ui.Label(lbar, text="list selection: (none)", row=1,
                         column=1, sticky='w')
    cb_var = ui.StringVar()
    # READ THE VARIABLE, not the widget: a combobox that displays the pick
    # while leaving its variable empty is the fault this row is for.
    cb_var.trace_add('write',
                     lambda *a: combo_says.configure(
                         text="combo variable: {!r}".format(cb_var.get())))
    # STATE IS THE COMBOBOX'S EQUIVALENT AXIS (Kent, 2026-09-14: "there are
    # options for combobox, too, right?" and "I recall an option that allows
    # you to search/filter, and/or input something not on the list?").
    # ttk's three: 'normal' (its default) leaves the entry EDITABLE, so a
    # value that is not among the four can be typed and must still reach the
    # variable; 'readonly' allows only the four; 'disabled' allows none and
    # must look inert. Under webview, 'normal' builds an <input> with a
    # <datalist> — which also filters as you type — and the other two build
    # a <select>, so this row is where that divergence shows itself.
    STATES = ('normal', 'readonly', 'disabled')
    state_var = ui.StringVar(value='readonly')
    combo_held = {'cb': None}

    def build_combo(*args):
        old = combo_held.get('cb')
        if old is not None:
            try:
                old.destroy()
            except Exception as e:
                log.info("gallery: could not destroy the old combo (%r)", e)
        combo_held['cb'] = _try("Combobox", lambda: ui.Combobox(
                lbar, textvariable=cb_var, optionlist=CHOICES,
                state=state_var.get(), command=lambda *a: None,
                row=0, column=0), lbar, 1)

    statebar = ui.Frame(lbar, row=3, column=0, columnspan=2, sticky='w')
    _note(statebar, "combobox state:", row=0, column=0)
    for n, s in enumerate(STATES):
        _try("combobox state radio {!r}".format(s),
             lambda s=s, n=n: ui.RadioButton(
                 statebar, text=s, variable=state_var, value=s,
                 command=build_combo, row=0, column=n + 1), statebar, 1)
    build_combo()

    # SELECTMODE ON A RADIO ROW, and the list REBUILT on each change (Kent,
    # 2026-09-14: "There are a number of selection options for combo/list
    # box: can we set a radio selection to switch between them, and refresh
    # the widget on change?"). Rebuilt rather than reconfigured because
    # selectmode is read at construction on both backends — tkinter passes it
    # to the Tk widget, and ui_webview turns it into `multiple` on the
    # element — so a live `config(selectmode=…)` would be a third path
    # neither backend has, and testing one the app never uses proves nothing.
    MODES = ('browse', 'single', 'multiple', 'extended')
    mode_var = ui.StringVar(value='multiple')
    held = {'lb': None, 'calls': 0}

    def selected(*args):
        held['calls'] += 1
        lb = held['lb']
        try:
            got = [lb.get(i) for i in lb.curselection()]
        except Exception as e:
            got = ['(could not read the selection: {!r})'.format(e)]
        list_says['text'] = "list selection ({}, {} call{}): {}".format(
            mode_var.get(), held['calls'],
            '' if held['calls'] == 1 else 's',
            ', '.join(str(g) for g in got) or '(none)')

    def build_list(*args):
        old = held.get('lb')
        if old is not None:
            try:
                old.destroy()
            except Exception as e:
                log.info("gallery: could not destroy the old list (%r)", e)
        held['calls'] = 0
        held['lb'] = _try("ListBox", lambda: ui.ListBox(
                lbar, listvariable=ui.StringVar(),
                selectmode=mode_var.get(), optionlist=CHOICES,
                command=selected, height=5, row=0, column=1), lbar, 1)
        list_says['text'] = "list selection ({}, 0 calls): (none yet)".format(
                                mode_var.get())

    modebar = ui.Frame(lbar, row=2, column=0, columnspan=2, sticky='w')
    _note(modebar, "selectmode:", row=0, column=0)
    for n, m in enumerate(MODES):
        _try("selectmode radio {!r}".format(m),
             lambda m=m, n=n: ui.RadioButton(
                 modebar, text=m, variable=mode_var, value=m,
                 command=build_list, row=0, column=n + 1), modebar, 1)
    build_list()

    _note(t, "LABEL vs MESSAGE at four lengths, all bordered. The longest is "
             "given wraplength=200 — it must wrap inside its border, not run "
             "past it. This is the row that used to clip mid-word.",
          row=6, columnspan=3)
    wbar = ui.Frame(t, row=7, column=0, columnspan=3, sticky='w')
    for col, cls_name in enumerate(('Label', 'Message')):
        cls = getattr(ui, cls_name, None)
        if cls is None:
            _note(wbar, "{} is missing from this backend".format(cls_name),
                  row=0, column=col)
            continue
        _note(wbar, cls_name, row=0, column=col)
        for n, text in enumerate((
                "short ˥˥˦˦˨",
                "a somewhat longer one",
                "longer still, with more words in it than that",
                "the very long one, with a great many words in it indeed, "
                "which must wrap inside its own border rather than running "
                "out past the edge of it")):
            # `wraplength` IS A LABEL OPTION, and Tk's Message has no such
            # thing — it measures its line length with `width`, in PIXELS
            # (unlike Entry and Label, where width counts characters). The
            # first version passed wraplength to both and the Message column
            # died on the spot: "gallery Message #3 failed: TclError('unknown
            # option -wraplength')" (Kent, tkinter, 2026-09-14). Same 200px
            # either way, spelled the way each widget spells it.
            kw = {}
            if n == 3:
                kw = {'width': 200} if cls_name == 'Message' \
                     else {'wraplength': 200}
            _try("{} #{}".format(cls_name, n),
                 lambda cls=cls, text=text, n=n, col=col, kw=kw: cls(
                     wbar, text=text, row=n + 1, column=col,
                     borderwidth=1, relief='solid', **kw),
                 wbar, n + 1)
    return t


# ── tab: Images ──────────────────────────────────────────────────────────

def tab_images(nb):
    t = ui.Frame(nb)
    # A TALL IMAGE AND A SMALL CAP. Kent, 2026-09-14: "I think these images
    # are correct; a smaller number (or a less square image) might make it
    # more obvious", then "use images/Verify Group List.png". Exactly right,
    # and the first version could not have shown the difference: 'icon' is
    # roughly square, so capping its WIDTH at 80 and its HEIGHT at 80 give
    # the same picture.
    #   'verifyglyphs' is that file (theme_data.py:105), about 1:2 — so
    # width-capped stays tall and narrows, height-capped becomes short and
    # wide, and 'by both' follows the taller side. Four visibly different
    # shapes rather than four similar squares.
    _note(t, "IMAGE SIZE: a TALL image (about 1:2), so the caps differ "
             "visibly. The first is unconstrained; then capped at 40px by "
             "width (stays tall, narrows), by height (becomes short), and by "
             "both (fits a 40 square, so the tall side wins). If all four "
             "look alike, image_pixels is being dropped.",
          row=0, columnspan=3)
    bar = ui.Frame(t, row=1, column=0, columnspan=3, sticky='w')
    for n, (label, kw) in enumerate((
            ("as-is", {}),
            ("40 wide", {'image_pixels': 40, 'image_scaleto': 'width'}),
            ("40 high", {'image_pixels': 40, 'image_scaleto': 'height'}),
            ("40 box", {'image_pixels': 40}))):
        cell = ui.Frame(bar, row=0, column=n, padx=6)
        _try("image {}".format(label),
             lambda cell=cell, kw=kw: ui.Label(cell, image='verifyglyphs',
                                               text='', row=0, column=0,
                                               **kw),
             cell, 0)
        _note(cell, label, row=1)

    _note(t, "COMPOUND: where the picture sits relative to the words. Four "
             "buttons, each naming its own setting — the picture should be in "
             "that position.", row=2, columnspan=3)
    cbar = ui.Frame(t, row=3, column=0, columnspan=3, sticky='w')
    for n, where in enumerate(('top', 'bottom', 'left', 'right')):
        _try("compound {}".format(where),
             lambda where=where, n=n: ui.Button(
                 cbar, text=where, image='icon', compound=where,
                 image_pixels=48, command=lambda: None, row=0, column=n),
             cbar, 1)

    _note(t, "A THEME IMAGE BY NAME: 'transparent' is the A-Z+T stack logo. A "
             "name absent from the theme's imagelist draws nothing and used "
             "to say nothing either (35 of 81 were missing from webview's "
             "copy).", row=4, columnspan=3)
    _try("theme image", lambda: ui.Label(t, image='transparent', text='',
                                         image_pixels=120, row=5, column=0),
         t, 5)
    return t


# ── tab: Scrolling ───────────────────────────────────────────────────────

def tab_scrolling(nb):
    t = ui.Frame(nb)
    # EVERY SPECIMEN MUST OVERFLOW ITS BOX, or it proves nothing. The first
    # version gave the button frame ten buttons and no height: ten fitted
    # inside the default cap, so it did not scroll and looked broken beside a
    # neighbour that did — Kent saw the same under tkinter ("the middle one
    # is too tall to scroll"). An explicit `height` and enough items make the
    # question "does it scroll" answerable, and exercise the height path as
    # well as the default cap.
    _note(t, "SCROLLING FRAME: thirty rows in a box six rows tall. It must "
             "scroll rather than grow — if you can see all thirty, the "
             "viewport is not being capped.", row=0, columnspan=3)
    sf = _try("ScrollingFrame",
              lambda: ui.ScrollingFrame(t, height=6, row=1, column=0), t, 1)
    if sf is not None:
        for i in range(30):
            _try("scroller row {}".format(i),
                 lambda i=i: ui.Label(sf.content, text="row {}".format(i),
                                      row=i, column=0, sticky='w'),
                 t, 1)

    # THESE CONTROLS MUST REPORT, or scrolling is all they test (Kent,
    # 2026-09-14: "scrolling button frame buttons should do something (show
    # button number?)"). `command=lambda *a: None` made them handsome and
    # inert: a button frame that scrolls perfectly and calls nothing back
    # looks exactly like one that works. The same flaw as the drag tab's
    # "(no drop yet)", and it hid a live one — the list box below reached
    # this page with a callback that could never fire.
    #   Both report into one line, since only one of them can be clicked at
    # a time, and the line names WHICH control spoke.
    said = ui.Label(t, text="scrolling controls: (nothing clicked yet)",
                    row=6, column=0, columnspan=3, sticky='w')

    def report(what):
        def go(choice=None, **kw):
            said['text'] = "scrolling controls: {} → {!r}".format(what, choice)
            log.info("gallery: %s reported %r", what, choice)
        return go

    _note(t, "SCROLLING BUTTON FRAME (testapp4): twenty buttons in a box five "
             "rows tall, each with the icon to the RIGHT of its number. Same "
             "test as above, built by a frame from an optionlist. Clicking one "
             "must name its number in the line below the boxes.",
          row=2, columnspan=3)
    _try("ScrollingButtonFrame", lambda: ui.ScrollingButtonFrame(
            t, optionlist=range(6, 26), command=report("button frame"),
            image='icon', compound='right', image_pixels=24,
            bsticky='ew', height=5, row=3, column=0), t, 3)

    _note(t, "SCROLLING LIST BOX: twenty items in a box four rows tall. "
             "Picking a row must name it in the line below.",
          row=4, columnspan=3)
    _try("ScrollingListBox", lambda: ui.ScrollingListBox(
            t, optionlist=["item {}".format(i) for i in range(20)],
            command=report("list box"), height=4, row=5, column=0), t, 5)
    return t


# ── tab: Drag ────────────────────────────────────────────────────────────

class _DropCell(ui.Label):
    """A droppable that SAYS a drop reached it.

    The first version of this tab wired no handler at all: six cells were
    given `draggable`/`droppable` and a label beside them read "(no drop
    yet)" that nothing could ever change. Kent, 2026-09-14: "what does '(no
    drop yet)' mean? there was no drop registered by the program? I see
    animation, but no other effect." Nothing was registered because nothing
    was listening — the harness could not have shown a working drop.

    `dnd_commit(source, event)` is the target-side call, and BOTH backends
    make it (`ui_tkinter.Gridded.dnd_commit`, `ui_webview` via the page's
    `dnd_commit` event), so overriding it here tests the real contract
    rather than a page-local listener. The base call is still made after
    reporting, because it is what puts an un-accepted source back.
    """

    def dnd_commit(self, source, event):
        _drag_report(self, "DROP on {}".format(
            getattr(self, 'cellname', '?')), source)
        try:
            super().dnd_commit(source, event)
        except Exception as e:
            log.info("gallery: dnd_commit chain said %r", e)


class _DragCell(ui.Label):
    """The draggable, reporting where its own drag ENDED.

    Two reports rather than one, because they fail separately: a drop can
    reach the target and the source never hear (tkinter calls
    `dnd_commit` then `dnd_end`), or the drag can end over nothing at all —
    which is a legitimate outcome and must be distinguishable from a dead
    drag layer.
    """

    def dnd_end(self, target, event):
        _drag_report(self, "drag ended {}".format(
            "on " + getattr(target, 'cellname', '?') if target
            else "off any target"), self)
        try:
            super().dnd_end(target, event)
        except Exception as e:
            log.info("gallery: dnd_end chain said %r", e)


def _drag_report(widget, what, source=None):
    """Append one line to the drag tab's running report."""
    held = getattr(_DropCell, 'held', None)
    if held is None:
        log.info("gallery drag: %s (no report label)", what)
        return
    held['seen'].append(what)
    try:
        held['label']['text'] = "drops seen ({}): {}".format(
            len(held['seen']), ' | '.join(held['seen'][-3:]))
    except Exception as e:
        log.info("gallery: could not write the drag report (%r)", e)


def tab_drag(nb):
    t = ui.Frame(nb)
    _note(t, "DRAG AND DROP (testapp2): the cell reading 'DRAG ME' is the "
             "DRAGGABLE one, the five reading 'drop here' are DROPPABLE. Drag "
             "the first onto any other — the report below counts the drops it "
             "was told about and names the last three targets. Nothing "
             "visibly moving during the drag is a known gap "
             "(agenda/drag_and_drop_animation.md), not a failure of this row.",
          row=0, columnspan=3)
    bar = ui.Frame(t, row=1, column=0, columnspan=3, sticky='w')
    report = ui.Label(t, text="drops seen (0): (none yet)", row=2, column=0,
                      columnspan=3, sticky='w')
    # ON THE CLASS, not in a closure: the two handlers are methods, reached
    # by the backend rather than by anything this function calls, so they
    # have no other route to the label. One drag tab per run, so one holder.
    _DropCell.held = {'label': report, 'seen': []}
    for i in range(6):
        first = (i == 0)
        cls = _DragCell if first else _DropCell

        def make(i=i, first=first, cls=cls):
            cell = cls(bar, text="{}\n{}".format(
                           i, "DRAG ME" if first else "drop here"),
                       font='read', row=i // 3, column=i % 3,
                       draggable=first, droppable=not first,
                       borderwidth=2, relief='raised', ipadx=16, ipady=16)
            cell.cellname = "cell {}".format(i)
            return cell

        _try("drag cell {}".format(i), make, bar, 1)
    _note(t, "(a backend with no drag layer should say so above rather than "
             "silently doing nothing — if the cells build and the count stays "
             "at 0 however you drag, that is the gap to report)", row=3,
          columnspan=3)
    return t


# ── tab: Events ──────────────────────────────────────────────────────────

def tab_events(nb):
    t = ui.Frame(nb)
    _note(t, "PROGRESS: horizontal at one third, vertical at two thirds — and "
             "press 'run the bars'. It EMPTIES both bars first (so they fall "
             "before they climb; that is the reset, not a fault), pauses, then "
             "steps 0→100 in fives. The commanded value is printed beside the "
             "button: a bar that lags its number is a drawing problem, a "
             "number that stops climbing is a scheduling one. A vertical bar "
             "drawn horizontally means 'orient' is being dropped.",
          row=0, columnspan=3)
    bar = ui.Frame(t, row=1, column=0, columnspan=3, sticky='w')
    bars = []
    for n, (orient, value, sticky) in enumerate((('horizontal', 33, 'ew'),
                                                 ('vertical', 66, 'ns'))):
        p = _try("Progressbar {}".format(orient),
                 lambda orient=orient, n=n, sticky=sticky: ui.Progressbar(
                     bar, orient=orient, mode='determinate',
                     row=0, column=n, sticky=sticky), bar, 0)
        if p is not None:
            bars.append(p)
            _try("Progressbar {} value".format(orient),
                 lambda p=p, value=value: p.current(value), bar, 0)

    # MOVING, because a static bar cannot show whether it moves. Kent,
    # 2026-09-14: "it would be nice to see those progress bars move, maybe on
    # click or something."
    #   Driven by `after`, NOT a sleep loop: a loop would hold the main
    # thread and neither backend would repaint until it finished, so the bars
    # would sit still and then jump to 100 — which is `ui_tkinter.testapp`'s
    # own `progress()` (it sleeps 2ms per step) and the same trap as the
    # wait-dialog delay. Each step schedules the next.
    #
    # WHAT THE FIRST VERSION ACTUALLY DREW (Kent: "'run the bars' does
    # something, but not move bars 0-100... right/top --> left/bottom
    # 60%-ish, slows, turns around and returns", and "H&V are synchronized,
    # with same behavior over time"). Two faults, both in this harness:
    #
    #   1. It began by commanding 0 while the bars rested at 33 and 66, so
    #      the first thing on screen was both bars EMPTYING — right-to-left
    #      and top-to-bottom, exactly as described — before anything climbed.
    #   2. It stepped every 30ms under a 0.2s CSS transition, so the drawn
    #      fill was always chasing a value six steps old and never arrived
    #      anywhere it was told; the fall decelerated ("slows") and was
    #      overtaken by the climb ("turns around and returns").
    #
    # So: the reset to 0 is now a separate, announced step with a pause
    # after it, the step interval is longer than the transition, and the
    # COMMANDED value is printed beside the bars. That last is the point —
    # a bar that lags its number is a rendering question, a number that
    # stops climbing is a scheduling one, and the two looked identical.
    step_says = ui.Label(t, text="commanded: (idle)", row=2, column=1,
                         sticky='w')

    def sweep(value=0):
        for p in bars:
            try:
                p.current(value)
            except Exception as e:
                log.info("gallery: could not set the bar (%r)", e)
        step_says['text'] = "commanded: {}%".format(value)
        if value < 100:
            try:
                t.after(150, lambda: sweep(value + 5))
            except Exception as e:
                log.info("gallery: no after() to drive the sweep (%r)", e)

    def run_bars():
        sweep(0)                       # empty first, and SAY it is a reset
        step_says['text'] = "commanded: 0% (reset — climbing from here)"
        try:
            t.after(600, lambda: sweep(5))
        except Exception as e:
            log.info("gallery: no after() to start the sweep (%r)", e)
            sweep(5)

    ui.Button(t, text="run the bars", command=run_bars, row=2, column=0)

    _note(t, "TOOLTIP: hover the bordered label below — a tip should appear "
             "and then go away.", row=3, columnspan=3)
    tip_target = ui.Label(t, text="hover me", row=4, column=0,
                          borderwidth=1, relief='solid', ipadx=12, ipady=8)
    _try("ToolTip", lambda: ui.ToolTip(tip_target,
                                       "this label has a tooltip"), t, 4)

    _note(t, "BINDINGS: click anywhere on this tab, or press an arrow key, "
             "and the line below should record it. A backend with no bind() "
             "records nothing.", row=5, columnspan=3)
    seen = ui.Label(t, text="events: (none)", row=6, column=0, columnspan=3,
                    sticky='w')
    log_of = []

    def note_event(name):
        def go(event=None):
            log_of.append(name)
            seen['text'] = "events: " + ' '.join(log_of[-12:])
        return go

    for seq, name in (('<ButtonRelease-1>', 'click'), ('<Up>', '^'),
                      ('<Down>', 'v'), ('<Left>', '<'), ('<Right>', '>')):
        _try("bind {}".format(seq),
             lambda seq=seq, name=name: t.bind(seq, note_event(name),
                                               add=True), t, 6)

    _note(t, "VARIABLE TYPES: each should report its own class and value. A "
             "Variable holding a list must come back as a sequence, not as a "
             "string of one.", row=7, columnspan=3)
    vbar = ui.Frame(t, row=8, column=0, columnspan=3, sticky='w')
    for n, (name, make) in enumerate((
            ('StringVar', lambda: ui.StringVar(value='text')),
            ('IntVar', lambda: ui.IntVar(value=7)),
            ('BooleanVar', lambda: ui.BooleanVar(value=True)),
            ('Variable(list)', lambda: ui.Variable(value=[1, 2, 3])))):
        def show(name=name, make=make, n=n):
            v = make()
            got = v.get()
            return _note(vbar, "{}: {!r} ({})".format(name, got,
                                                      type(got).__name__),
                         row=n)
        _try(name, show, vbar, n)
    return t


# ── tab: Composites ──────────────────────────────────────────────────────

def _click_to_edit(parent, row, what, var, editor, note, clear_on_edit=False):
    """The gallery's wrapper around `composites.ClickToEdit`.

    THE HELPER MOVED OUT, 2026-09-15. It was written here first — as the
    sixth copy of an idiom the alphabet pages already carried five times —
    because the gallery needed something to test. It is now
    `frontend/composites.py`, because the app needs it: settings raise a
    whole WINDOW per value, and this is what replaces them
    (`agenda/settings_prompts_one_window.md`, top of the agenda).

    What is left here is the HARNESS part — the note above each row, and the
    row's placement in the tab's grid — so the gallery goes on exercising
    the same code the app now runs, rather than a copy of it that can
    drift."""
    _note(parent, note, row=row, columnspan=3)
    c = composites.ClickToEdit(parent, var, editor, row=row + 1, column=0,
                               columnspan=3, label=what + ":",
                               clear_on_edit=clear_on_edit)
    return c.shown, c.widget


def tab_composites(nb):
    t = ui.Frame(nb)
    _note(t, "COMPOSITES: the app's own click-to-edit idiom, which is "
             "written out five times in the alphabet pages and is not a "
             "class anywhere. Each row shows a bordered label; CLICK IT and "
             "the label should be replaced IN PLACE by an editor and an OK "
             "button, and OK should put the label back showing the new "
             "value. Two failures to watch for: the label and the editor "
             "visible at once (grid_remove did nothing), and the row "
             "collapsing or jumping when it swaps (the restored widget lost "
             "its cell). RETURN commits too, exactly as OK does — it is "
             "bound when the editor appears and unbound when it goes, so a "
             "backend that binds and cannot unbind will leave Return firing "
             "at an editor nobody can see.", row=0, columnspan=3)

    entry_var = ui.StringVar(value="click me to edit")
    _click_to_edit(t, 1, "entry", entry_var,
                   lambda box: ui.EntryField(box, textvariable=entry_var,
                                             row=0, column=0),
                   "1. LABEL ↔ ENTRY — the alphabet chart's title and "
                   "copyright. Type something and press OK; the label must "
                   "show what you typed.")

    list_var = ui.StringVar(value=CHOICES[0])

    def _list(box):
        def picked(choice=None, **kw):
            list_var.set(str(choice))
        return _try("click-to-edit list", lambda: ui.ListBox(
                        box, optionlist=CHOICES, command=picked,
                        height=4, row=0, column=0), box, 1)

    _click_to_edit(t, 3, "list", list_var, _list,
                   "2. LABEL ↔ LIST BOX — same idiom, a list instead of a "
                   "field. Pick a row and the label must show that choice "
                   "before you press OK.")

    # state='normal', NOT 'readonly'. Kent, 2026-09-14: "which of those
    # (currently none) allows a user to type in something not currently on
    # the list?" — none of them did, because this row was built readonly,
    # which is the one setting that forbids exactly that. 'normal' is the
    # combination the question is about: pick from the list OR type
    # something that is not on it. Under webview it is the <input> with a
    # <datalist>, which also narrows the list as you type; under tkinter it
    # is ttk's default editable combobox.
    combo_var = ui.StringVar(value=CHOICES[0])
    _click_to_edit(t, 5, "combo", combo_var,
                   lambda box: _try("click-to-edit combo",
                                    lambda: ui.Combobox(
                                        box, textvariable=combo_var,
                                        optionlist=CHOICES,
                                        state='normal',
                                        command=lambda *a: None,
                                        row=0, column=0), box, 1),
                   "3. LABEL ↔ COMBOBOX, editable — the only row of the "
                   "three where you can both PICK from the four choices and "
                   "TYPE something that is not among them. Clicking the "
                   "label must open an EMPTY field showing all four; typing "
                   "narrows them; picking one, then typing again, narrows "
                   "again. Type 'choice 9' and press Return: the label must "
                   "come back reading 'choice 9'. Press OK having typed "
                   "nothing and the old value must return.",
                   clear_on_edit=True)
    return t


TABS = (("Alignment", tab_align), ("Controls", tab_controls),
        ("Text", tab_text), ("Images", tab_images),
        ("Scrolling", tab_scrolling), ("Composites", tab_composites),
        ("Drag", tab_drag), ("Events", tab_events))


def build(window):
    f = window.frame
    ui.Label(f, text="A-Z+T widget gallery — backend: {}".format(backend),
             font='title', row=0, column=0, sticky='ew')
    nb = ui.Notebook(f, row=1, column=0)
    for name, maker in TABS:
        try:
            nb.add(maker(nb), text=name)
        except Exception as e:
            # A TAB THAT CANNOT BE BUILT MUST NOT COST THE OTHERS. Per-tab as
            # well as per-specimen (`_try`), because a Notebook.add that
            # fails takes its whole page with it.
            log.error("gallery tab %r failed: %r", name, e)
            try:
                nb.add(ui.Frame(nb), text="{} (FAILED)".format(name))
            except Exception:
                pass
    return nb


def _measure_anchor(window):
    """Ask the page what an anchored label actually computed to.

    Three readings of the anchor row disagreed with three different
    explanations, and none could be settled from the source: whether the
    label was stretched by `sticky`, whether it was a flex container when the
    anchor was applied, and whether the anchor reached it at all look
    identical on screen. One line of measurement ends that, the way timing
    `load_by_iso` did after two wrong guesses from reading (2026-09-14).

    Webview only, and never fatal: under tkinter there is no page to ask.
    """
    if backend != 'webview':
        return
    wv = getattr(window, '_wv_window', None)
    if wv is None:
        log.info("gallery: no pywebview window to measure")
        return
    try:
        log.info("gallery anchor measurement: %s",
                 wv.evaluate_js('reportAnchor()'))
    except Exception as e:
        log.info("gallery: could not measure the anchor (%r)", e)


def _program():
    """A program object the backends treat as the REAL app, not a dummy.

    `ui.Root()` with no program falls back to `dummy.App`, which sets
    `dummy=True` — and `ui_tkinter.Root.__init__` gates real-app setup on
    that flag, including the app-wide mouse-wheel dispatcher:

        if not getattr(self.program,'dummy',False) and not noimagescaling:
            _app_root=self
            self.bind_all("<MouseWheel>", self._on_global_mousewheel)

    So the gallery had NO wheel binding at all, and the three scrollers
    behaved differently for a reason that was nothing to do with them: the
    list box scrolled because a Tk Listbox handles the wheel natively, and
    the other two could only be dragged by their bars (Kent, 2026-09-14:
    "only the last one is bound to the wheel"). A harness that silently
    under-tests is worse than no harness, and this one was reporting a gap
    the app does not have.

    `dummy.App` with the flag cleared, rather than a bespoke object: it
    already carries the name/theme/url the backends read, so clearing one
    attribute is the whole difference between "a scratch root" and "the
    app's root".
    """
    from dummy import App
    program = App()
    program.dummy = False
    return program


def main():
    log.info("gallery: building with the %r backend", backend)
    root = ui.Root(program=_program())
    window = ui.Window(root, title="A-Z+T widget gallery ({})".format(backend))
    window.mainwindow = True    # so closing it ends the run, under either
    build(window)
    try:
        window.deiconify()
    except Exception as e:
        log.info("gallery: deiconify not needed or not available (%s)", e)
    # The measurement needs the page LOADED, so it goes in the callback
    # webview runs after load. tkinter's mainloop takes no callback and needs
    # none, so it is called the plain way there.
    if backend == 'webview':
        root.mainloop(setup_callback=lambda: _measure_anchor(window))
    else:
        root.mainloop()
    return 0


if __name__ == '__main__':
    sys.exit(main())
