"""Click-to-edit composites: a label that becomes an editor, and a label again.

THE APP'S OWN IDIOM, WRITTEN FIVE TIMES AND NEVER ONCE AS A CLASS. The
alphabet chart does it for its title and its copyright
(`alphabet_chart.py:548-580`), the comparison booklet for its title and
copyright (`alphabet_comparison.py:494-562`), each with its own pair of
`edit_x`/`save_x` methods and its own `grid_remove()`/`grid()` pair. Kent,
2026-09-14: "We need to add to gallery a class for entry/label, as we used in
Alphabet, and repeated later. And another that turns a label into a list box.
there might be another." It was then written a sixth time, as
`gallery._click_to_edit`, to have something to test — and that is the version
lifted here, because the gallery had already reduced the five copies to one
helper with three editors.

WHY THIS MODULE EXISTS RATHER THAN THE HELPER STAYING IN THE GALLERY: the
gallery is a test harness. `agenda/settings_prompts_one_window.md` (promoted
to the top of the agenda 2026-09-15) is about the app raising a whole WINDOW
per settings value — "Enter Analysis Language Name" containing one prompt and
one entry; "Select Input Sound Card" containing a list — when what it wants
is a label with its field beside it, in the window already open. The idiom
that replaces those windows cannot live in the harness that tests it.

`from frontend import ui`, so this works on whichever backend is active. It
is deliberately NOT in ui_tkinter/ui_webview: it is composed entirely of
widgets both backends already provide, so writing it once keeps the two from
drifting — and a composite in one backend and not the other is exactly the
fork this port is trying to avoid.

WHAT A BACKEND HAS TO GET RIGHT for this to work, all three of them real
contracts that the gallery's Composites tab exercises on the page:

  * `bind('<Button-1>')` ON A LABEL, not on a button;
  * `grid_remove()` then `grid()` — hide and RESTORE in place, which is
    different from destroying and rebuilding, and which keeps the layout
    from jumping;
  * one variable shared by the label and the editor, so the label shows what
    was typed or picked without anyone copying it across.

A backend that cannot do the second will show the label and the editor at
once, or lose the row entirely.

THE THREE KINDS OF FIELD, which are Kent's own division (2026-09-15) and the
vocabulary this module is built around, because getting the kind wrong is how
a settings prompt ends up unable to express the answer:

  1. **An ABSOLUTE LIST** — pick one of a fixed set, and nothing else is a
     valid answer. The sound card, the sample format, the rate. Readonly:
     typing would offer the user a value the device cannot do.
     → `choice_field(...)`, or `list_field(...)` when the set is long enough
     to want scrolling.

  2. **ENTRY WITH TYPING** — free text with no list at all, because there is
     no set to choose from. The analysis language name is the example Kent
     named ("maybe just language name").
     → `entry_field(...)`.

  3. **A LIST OF PREVIOUS VALUES THAT ALSO ALLOWS ENTRY** — the answer is
     usually one you have given before, but a new one must be possible.
     Kent: "lists with previous values, that allow entry (currently two
     dialogs)" — and that parenthesis is the point: today this costs the
     user TWO windows, one offering the old values and a second to type a
     new one, because a readonly list cannot express "something else". One
     editable field is both.
     → `history_field(...)`.

Kind 3 is the one that must not be quietly turned into kind 1. A readonly
combo box for it looks correct and silently removes the only way to give a
new answer — which is the same fault as the two-window flow, minus the
second window.
"""
import logging

from frontend import ui
from utilities.i18n import _

log = logging.getLogger(__name__)

# THE ONE FIELD CURRENTLY OPEN, anywhere. Opening a second closes the first.
#
# Without this every click opens another editor and none of them ever close,
# so a settings page ends up as a column of open combo boxes with no labels
# left to read — Kent, 2026-09-15, on the sound page with all four open at
# once: "this really isn't going to work for us … can we set each on a page
# to revert others to label, so we only edit one at a time?"
#
# ONE SLOT FOR THE WHOLE APP, not one per page: a user edits one value at a
# time, and a field left open on a page they have navigated away from is
# still a field left open. Closing is `commit`, so the value the user had
# chosen is kept; a field opened and abandoned without a choice restores what
# it had (see `clear_on_edit`), so nothing is lost either way.
_editing = None

# How much wider than its own `width` an editor renders, in characters: a
# combo box's border, padding and dropdown arrow, none of which the `width`
# number covers. The value label reserves `width + this` so that the LABEL,
# not the editor, is what sizes the column — see `choice_field`. Approximate
# on purpose: too large only costs trailing space after a short value, while
# too small lets the page jump when a field opens.
_EDITOR_CHROME = 5


def close_open_field(exceptfor=None):
    """Commit whatever field is open, if it is not `exceptfor`."""
    global _editing
    open_one = _editing
    if open_one is None or open_one is exceptfor:
        return
    _editing = None
    try:
        open_one.commit()
    except Exception as e:
        log.info("click-to-edit: could not close the open field (%r)", e)


class ClickToEdit:
    """A label showing `var`, which swaps for an editor when clicked.

    One grid cell of `parent`: everything lives in a Frame placed at
    `row`/`column`, so a caller adds a field without knowing anything about
    the composite's internals.

    `editor` is a callable taking the container Frame and returning the
    widget to focus — the caller builds whatever control it wants, which is
    what keeps one class covering entry, list and combo rather than three.

    `on_commit` is called with the committed value after the label comes
    back. Settings callers need it: showing the new value is this class's
    job, PERSISTING it is theirs.

    `rebuild=True` builds the editor afresh on every open instead of once.
    Needed when the CHOICES change — the sound settings' rate list depends
    on which card is selected, so an editor built once would go on offering
    the first card's rates forever.
    """

    def __init__(self, parent, var, editor, row=0, column=0, label=None,
                 clear_on_edit=False, on_commit=None, rebuild=False,
                 font='default', ok=_("OK"), show_ok=True, width=None,
                 label_anchor='e', **gridkwargs):
        self.var = var
        self._editor = editor
        self._clear_on_edit = clear_on_edit
        self._on_commit = on_commit
        self._rebuild = rebuild
        self._was = None
        self.widget = None
        self.namelabel = None

        # TWO COLUMNS OF THE PARENT, not one cell holding both. Kent,
        # 2026-09-15: "let's try two columns: name (right aligned) and value
        # (left aligned)."
        #   This used to wrap the pair in a frame of its own, which is why
        # the names never lined up with each other: every row sized its own
        # frame, so each name sat wherever its own value put it. Gridded
        # straight into the parent they are siblings, the parent's column 0
        # is as wide as the widest name, and the values all start at the same
        # x. The alignment then comes from the grid rather than from
        # anchoring, which is what the three earlier attempts were trying to
        # do by hand.
        gridkwargs.pop('sticky', None)
        gridkwargs.pop('columnspan', None)   # meaningless across two cells
        self.frame = parent
        # BOTH COLUMNS RESERVE THE SAME WIDTH — the value so its editor fits
        # without resizing the column, the name so the colon between them
        # lands on the block's centre. Characters, as tkinter and
        # `updateProp('width')` both mean it.
        size = {} if width is None else {'width': width}
        col = column
        if label:
            # THE NAME STAYS PUT; ONLY THE VALUE IS SWAPPED. Kent,
            # 2026-09-15: "you have name:value replaced. Let's keep name
            # there, and just swap out the value label, here and elsewhere."
            # It is its own widget in its own column for exactly that reason
            # — a caller that folds the name into the variable ("Rate:
            # 48000") loses the name the moment the chooser opens, and the
            # user is then editing an unlabelled box.
            #   SAME SIZE, so there is nothing to align vertically either.
            # Three attempts went by hand first — a shared baseline via
            # `sticky='s'`, then `sticky='n'` with the smaller name raised,
            # then matching the sizes — and the sizes are what settled it:
            # two labels of one size share a baseline by construction, on
            # both backends. The value keeps its own `font` parameter, so a
            # caller that wants it emphasised can still ask; only the DEFAULT
            # is no longer larger than the name beside it.
            #   THE SAME RESERVED WIDTH AS THE VALUE, so the colon sits on
            # the block's centre line. The value column reserves room for its
            # editor (see below), which made it the wider of the two — and a
            # block centred on the page then puts its MIDDLE on the page's
            # centre, which is somewhere out in the value column. The colons
            # ended up left of the button beneath them (Kent, 2026-09-15:
            # "the colons are no longer centered over the button").
            #   Two columns of one width put the boundary between them at the
            # block's centre, and the names are right-aligned into it, so the
            # colons land exactly there. The leading space before a short
            # name is the mirror of the trailing space after a short value.
            #   `anchor`, NOT just `sticky`. Sticky says where the LABEL sits
            # in its cell, and once the label reserves the whole column there
            # is nothing left for it to move within — so the names stayed
            # flush left and only the cell was right-aligned, which is
            # invisible (Kent, 2026-09-15: "right justify name column").
            # `anchor='e'` is where the TEXT sits inside the label, which is
            # the half that was missing.
            #   `label_anchor` because not every caller wants a COLUMN. A
            # settings page wants names right-aligned against the colons; a
            # prose line ("Studying Kent's English") wants the words to run
            # on, so it passes 'w' and no `width`, and the pair reads as a
            # sentence with the last word clickable.
            #   The SAME `font` as the value, which is the whole of what made
            # the two sit on a line together (see above).
            self.namelabel = ui.Label(parent, text=label, font=font, row=row,
                                      column=col, sticky=label_anchor,
                                      anchor=label_anchor, **size)
            col += 1
        # THE VALUE LABEL AND THE EDITOR SHARE ONE CELL. That is what makes
        # the swap happen in place instead of the row growing: grid_remove()
        # remembers the placement, so grid() puts the widget back exactly
        # where it was. Destroying and rebuilding would not.
        # PLAIN TEXT: a row reads "Speakers: default" and nothing else. No
        # border, no relief, no padding box, no background of its own.
        # Kent, 2026-09-15: "I want no boxes or background, just
        # 'name: value'."
        #   It arrived here with `relief='sunken'` and a border, which made
        # the value look like a control — a sunken relief is a BEVEL
        # (widgets.js `_RELIEF`: inset), and a bevelled box reads as a
        # button. What says the value can be changed is the page's own
        # "(click any to change)", not decoration on every row.
        # THE VALUE CELL IS AS WIDE AS THE EDITOR, OPEN OR CLOSED. Without
        # this the label and the editor share a cell that is sized to
        # whichever is showing — so opening a field widened column 1, and a
        # centred block then re-centred: the whole page moved under the
        # user's cursor (Kent, 2026-09-15: "clicking moves everything. can we
        # anchor the editable layer to left align in the same place?").
        #   Reserving the width in the CLOSED state costs some trailing space
        # after a short value, and buys a page that does not jump. The value
        # is left-aligned in that space, so it stays exactly where the
        # editor's text will appear.
        #   Characters, not pixels: `width` means the same thing to a Tk
        # Label and to `updateProp('width')` (which sets `ch`), and it is the
        # unit the editors are already specified in.
        self.shown = ui.Label(parent, textvariable=var, font=font,
                              row=row, column=col, sticky='w',
                              **size, **gridkwargs)
        self.box = ui.Frame(parent, row=row, column=col, sticky='w',
                            **gridkwargs)
        if not rebuild:
            self.widget = self._build()
        # AN OK BUTTON ONLY WHERE THERE IS SOMETHING TO CONFIRM. A list has
        # nothing: picking an item IS the answer, and making the user then
        # press OK asks them to say it twice (Kent, 2026-09-15: "clicking on
        # a value requires a further OK, by mouse or keyboard. selecting on
        # the list should be enough"). So the pick-only fields commit on
        # selection and show no button; the fields that accept TYPING keep
        # one, because a half-typed value needs a moment that says "done".
        if show_ok:
            ui.Button(self.box, text=ok, command=self.commit, row=0, column=1)
        # THE WHOLE LINE OPENS IT, not just the value. "Rate: 192khz" reads
        # as one thing and is one thing; requiring the click to land on the
        # right half of it is a target the user has to aim at for no reason
        # they can see (Kent, 2026-09-15: "bind name label click to edit
        # value fields, so people click anywhere in a line to open editor").
        #   The name is not itself editable — it opens the VALUE's editor,
        # which is what the row is for.
        for clickable in (self.shown, self.namelabel):
            if clickable is None:
                continue
            try:
                clickable.bind('<Button-1>', self.edit)
            except Exception as e:
                log.info("click-to-edit: could not bind a label (%r); this "
                         "field may not open from there", e)
        self.commit(notify=False)   # start as a label, editor hidden

    def _build(self):
        try:
            return self._editor(self.box)
        except Exception as e:
            log.info("click-to-edit: could not build the editor (%r)", e)
            return None

    def edit(self, event=None):
        """Show the editor in the label's place."""
        global _editing
        # ONE AT A TIME. Opening this closes whatever else was open, so a
        # page never accumulates editors — see `close_open_field`.
        close_open_field(exceptfor=self)
        _editing = self
        # TWO KINDS OF OPEN, and only one of them clears (Kent, 2026-09-14):
        #   1. CONVERTING THE LABEL into the editor — the field must start
        #      EMPTY, because the user is choosing afresh and typing into
        #      "choice 1" would append to the value being replaced;
        #   2. typing and picking WITHIN that session, repeatedly, before
        #      OK — filtering is the point there and must stay.
        # So the clearing hangs off this, the conversion, and never off
        # focus, which happens again on every pick. Committing without
        # having chosen anything restores what was there, so opening an
        # editor is never destructive.
        if self._clear_on_edit:
            self._was = self.var.get()
            self.var.set('')
        self.shown.grid_remove()
        self.box.grid()
        if self._rebuild:
            # The OK button stays; only the editor is replaced, because only
            # the editor's CONTENTS can be out of date.
            if self.widget is not None:
                try:
                    self.widget.destroy()
                except Exception as e:
                    log.info("click-to-edit: could not clear the old editor "
                             "(%r)", e)
            self.widget = self._build()
        # RETURN COMMITS, and is bound only while editing — the app's own
        # copies unbind it on save (`alphabet_chart.py:536`), and a binding
        # left in place would fire at an editor nobody can see.
        for w in (self.widget, self.box):
            if w is None:
                continue
            try:
                w.bind('<Return>', self.commit)
            except Exception as e:
                log.info("click-to-edit: could not bind Return (%r)", e)
        if self.widget is not None:
            try:
                self.widget.focus_set()
            except Exception as e:
                log.info("click-to-edit: no focus_set on the editor (%r)", e)

    def commit(self, event=None, notify=True):
        """Put the label back, showing whatever was chosen."""
        global _editing
        if _editing is self:
            _editing = None
        if self._clear_on_edit and not str(self.var.get() or '').strip():
            self.var.set(self._was or '')
        for w in (self.widget, self.box):
            if w is None:
                continue
            try:
                w.unbind('<Return>')
            except Exception as e:
                log.info("click-to-edit: could not unbind Return (%r)", e)
        self.box.grid_remove()
        self.shown.grid()
        if notify and self._on_commit is not None:
            try:
                self._on_commit(self.var.get())
            except Exception as e:
                # A SETTING THAT WILL NOT SAVE MUST NOT TAKE THE PAGE WITH
                # IT. The label already shows the new value, so the user
                # sees their choice; the log says why it did not stick.
                log.error("click-to-edit: %r rejected the value %r (%r)",
                          self._on_commit, self.var.get(), e)


def _options_of(options):
    """`options` may be a list or a callable returning one.

    A callable is how a field whose choices depend on other settings stays
    honest: the sound settings' sample rates come from whichever card is
    selected NOW, so a list captured at build time is the previous card's."""
    if callable(options):
        try:
            return list(options())
        except Exception as e:
            log.info("click-to-edit: could not get the current options "
                     "(%r); offering none", e)
            return []
    return list(options or [])


def entry_field(parent, var, **kwargs):
    """Label ↔ text entry. The alphabet chart's title and copyright."""
    return ClickToEdit(parent, var,
                       lambda box: ui.EntryField(box, textvariable=var,
                                                 row=0, column=0),
                       **kwargs)


def _committing(command, holder, var):
    """A `command` for a picker that also CLOSES the field.

    PICKING IS ANSWERING. A list has nothing to confirm — the item you
    clicked is the value — so requiring OK afterwards asks the user to say
    the same thing twice (Kent, 2026-09-15: "clicking on a value requires a
    further OK, by mouse or keyboard. selecting on the list should be
    enough").

    `holder` is a one-key dict rather than the composite itself because the
    editor is built BY the composite, during its own construction: there is
    no finished object to close over yet. By the time a user can click an
    option there certainly is."""
    def picked(choice=None, **kw):
        # THE TWO BACKENDS HAND THIS CALLBACK DIFFERENT THINGS, and only one
        # of them is a value. `ui_tkinter.Combobox` binds the command
        # straight to `<<ComboboxSelected>>` (:3625), so it arrives as a
        # tkinter Event; `ui_webview` calls it with the picked string. Taking
        # the argument on trust put "<Event ...>" in the field where the
        # sample rate belongs (Kent, 2026-09-15: "sound settings broke in
        # tkinter (event shown, rather than value, after selection)").
        #   So: use the argument only if it IS a value. When it is not, the
        # control's own `textvariable` already holds the pick — ttk writes it
        # before generating the event — and that variable is `var`, which is
        # why this can recover rather than guess.
        #   (The wider disagreement is its own agenda item: "Button command
        # arity: tkinter and webview disagree, one is wrong".)
        if isinstance(choice, (str, int, float)) and str(choice) != '':
            var.set(str(choice))
        else:
            # ASK THE WIDGET, NOT THE VARIABLE. Reading `var` here was one
            # selection behind: ttk generates `<<ComboboxSelected>>` before
            # the textvariable write has landed, so the variable still held
            # the PREVIOUS pick — "showing real values now, but not the ones
            # selected" (Kent, 2026-09-15). The event carries the widget, and
            # the widget's own `get()` is current at event time, which is the
            # only thing here that is.
            widget = getattr(choice, 'widget', None)
            getter = getattr(widget, 'get', None)
            if callable(getter):
                try:
                    picked_value = getter()
                except Exception as e:
                    log.info("click-to-edit: could not read the picker (%r)",
                             e)
                else:
                    if str(picked_value) != '':
                        var.set(str(picked_value))
        if command is not None:
            command(choice)
        c = holder.get('c')
        if c is not None:
            c.commit()
    return picked


def choice_field(parent, var, options, editable=False, command=None,
                 **kwargs):
    """Label ↔ combo box — the replacement for a window full of buttons.

    `editable=True` (state='normal') lets the user type something that is
    not on the list as well as pick from it; `False` is readonly, pick-only.
    Kent, 2026-09-14, on the gallery's readonly row: "which of those
    (currently none) allows a user to type in something not currently on the
    list?" — so the choice is explicit here rather than defaulted.

    A callable `options` is re-read on every open (see `_options_of`), which
    is why this passes `rebuild=True`."""
    holder = {}
    # THE LABEL IS WIDER THAN THE EDITOR, so the LABEL is what sizes the
    # column and the editor never changes it.
    #
    # Giving both the same `width` was the obvious thing and does not work:
    # the number is in CHARACTERS, and a label of 20 characters and an input
    # of 20 characters are not the same rendered width — the input adds its
    # own border and padding on top. So the cell still grew when the editor
    # appeared, the centred block re-centred, and the page moved under the
    # cursor exactly as before (Kent, 2026-09-15: "clicking still moves
    # stuff; try again").
    #   `_EDITOR_CHROME` is that difference, in characters, rounded up. It
    # does not have to be exact — only big enough that the editor stays
    # inside the space the label has already claimed.
    #   `width=None` MEANS "DO NOT RESERVE" — prose needs that. A settings
    # page is a column and wants every row the same width; a sentence
    # ("Studying Kent's English") wants the words against each other, and
    # reserving 25 characters for each half put an inch of nothing between
    # them and wrapped the longer values (Kent, 2026-09-15: "excess spacing",
    # twice — the per-pair frame was not the whole of it).
    width = kwargs.pop('width', 20)
    if width is not None:
        kwargs['width'] = width + _EDITOR_CHROME

    def _editor(box):
        size = {} if width is None else {'width': width}
        return ui.Combobox(box, textvariable=var,
                           optionlist=_options_of(options),
                           state='normal' if editable else 'readonly',
                           command=_committing(command, holder, var),
                           row=0, column=0, **size)
    kwargs.setdefault('rebuild', True)
    # An OK button only where typing is possible — a readonly list is
    # answered by the pick itself. See `_committing` and `ClickToEdit`.
    kwargs.setdefault('show_ok', bool(editable))
    c = ClickToEdit(parent, var, _editor, **kwargs)
    holder['c'] = c
    return c


def history_field(parent, var, previous, command=None, **kwargs):
    """Label ↔ editable combo of PREVIOUS VALUES — kind 3 of three.

    THIS ONE REPLACES TWO WINDOWS, not one. The answer is usually a value
    already given, so the previous ones are offered; but a new answer must
    be possible, and a readonly list cannot say "something else" — so the
    app asks twice, once with a list and again with an entry. Kent,
    2026-09-15: "lists with previous values, that allow entry (currently two
    dialogs)". One editable field is both questions, and the user can see
    the old answers while typing a new one.

    `clear_on_edit` is ON by default here and nowhere else: opening this
    field means choosing afresh, so typing must not append to the value
    being replaced — and committing without typing anything restores what
    was there, so opening it is never destructive. (The absolute-list kinds
    do not need it: there is nothing to type into.)

    Do NOT "tidy" this into `choice_field` with a readonly list. That looks
    right and removes the only way to give a new answer."""
    kwargs.setdefault('clear_on_edit', True)
    return choice_field(parent, var, previous, editable=True,
                        command=command, **kwargs)


def list_field(parent, var, options, height=6, command=None, **kwargs):
    """Label ↔ list box, for a choice long enough to want scrolling."""
    holder = {}

    def _editor(box):
        return ui.ListBox(box, optionlist=_options_of(options),
                          command=_committing(command, holder, var),
                          height=height, row=0, column=0)
    kwargs.setdefault('rebuild', True)
    kwargs.setdefault('show_ok', False)   # picking a row is the answer
    c = ClickToEdit(parent, var, _editor, **kwargs)
    holder['c'] = c
    return c
