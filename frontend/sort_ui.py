# coding=UTF-8
"""UI presenter for Sort workflow operations.

Backend sorting_engine.py delegates all UI widget creation here, so it
has zero frontend imports.
"""
from frontend import ui
from frontend.presenter_base import PresenterBase
from frontend.sort_buttons import (SortButtonFrame, SortGroupButtonFrame,
                                   SortGlyphGroupButtonFrame)
from utilities.i18n import _


class SortPresenter(PresenterBase):
    """Handles all UI rendering for Sort, Verify, and Join workflows."""
    def __init__(self, theme):
        self.theme=theme

    def check_button(self, parent, **kwargs):
        return ui.CheckButton(parent, **kwargs)

    def progressbar(self, parent, **kwargs):
        return ui.Progressbar(parent, **kwargs)

    def set_sense_illustration(self, sense):
        if not sense.image or not sense.image.base_img:
            # don't reload images unnecessarily; 
            # base_img is None if image failed to load
            iuri=sense.illustrationURI()
            if iuri in self.theme.image_cache:
                sense.image=self.theme.image_cache[iuri]
            elif iuri:
                sense.image=ui.Image(iuri)
        if sense.image and sense.image.base_img:
            sense.image.scale(self.theme.scale, pixels=65, scaleto='height')
            return sense.image.scaled
    # -- Sort button frame factories --

    def sort_button_frame(self, parent, sort_obj, groups, **kwargs):
        return SortButtonFrame(parent, sort_obj, groups, **kwargs)

    def sort_group_button_frame(self, parent, sort_obj, **kwargs):
        return SortGroupButtonFrame(parent, sort_obj, **kwargs)

    def sort_glyph_group_button_frame(self, parent, sort_obj, **kwargs):
        return SortGlyphGroupButtonFrame(parent, sort_obj, **kwargs)

    def group_button_class(self, macrosort):
        """Return the appropriate button frame class for sort/macrosort."""
        if macrosort:
            return SortGlyphGroupButtonFrame
        return SortGroupButtonFrame

    # -- Composite UI builders --

    def build_present_sense(self, runwindow_frame, buttonframe, text, sense):
        """Build the sort item display for a single sense. Returns the frame."""
        sortitem = ui.Frame(runwindow_frame, column=1, row=1,
                           sticky='nw', border=True)
        l = ui.Label(sortitem, text=text, font='readbig', sticky='w')
        if sense.image:
            sense.image.scale(l.theme.scale, pixels=65, scaleto='height')
            l['image'] = sense.image.scaled
            l['compound'] = 'left'
        l.wrap()
        buttonframe.sortitem = sortitem
        return sortitem

    def build_present_group(self, runwindow_frame, buttonframe, sort_obj,
                           item, kwargs):
        """Build the sort item display for a group. Returns frame or None."""
        sortitem = ui.Frame(runwindow_frame, border=True,
                           column=1, row=1, sticky='nw')
        ui.Label(sortitem, text='', width=5, sticky='')
        tosort_frame = SortGroupButtonFrame(sortitem, sort_obj,
                                           show_check=True, label=True,
                                           sticky='', **kwargs)
        if tosort_frame.hasexample:
            buttonframe.sortitem = sortitem
            return sortitem
        else:
            tosort_frame.destroy()
            return None

    def build_sort_layout(self, runwindow, img_mod, page_icon,
                         instructions, sort_obj, groups, macrosort):
        """Build the main sort window layout. Returns (groupsFrame, buttonframe)."""
        f = runwindow.frame
        ui.Label(f, image=f'sort{img_mod}',
                row=0, column=0, rowspan=3, sticky='new', anchor='center')
        ui.Label(f, image=page_icon, image_pixels=270,
                row=3, column=0, #rowspan=3, 
                sticky='nw')
        groupsFrame = ui.Frame(f, column=1, row=2,
                              rowspan=2, pady=0, sticky='nsew')
        f.rowconfigure(1, weight=0)
        f.rowconfigure(2, weight=1)
        f.columnconfigure(0, weight=0)
        f.columnconfigure(1, weight=1)
        ui.Label(groupsFrame, text=instructions, font='instructions',
                anchor='c', sticky='sew')
        buttonframe = SortButtonFrame(groupsFrame, sort_obj, groups,
                                     macrosort=macrosort,
                                     row=1, sticky='nsew', columnspan=2)
        return groupsFrame, buttonframe

    def build_verify_layout(self, runwindow, title, page_icon, instructions,
                           prog_text, img_mod, group,
                           items, sort_obj, macrosort, oktext,
                           min_to_multicolumn, buttoncolumns,
                           verifybutton_fn):
        """Build the verify window layout.
        Returns (buttonframe, verifycanary)."""
        f = runwindow.frame
        # Let the content area expand to fill the kiosk screen
        # Override the centering spacers (rows 0,2 weight=3 from Window.post_tk_init)
        f.grid_rowconfigure(1, weight=1)
        f.grid_columnconfigure(1, weight=1)
        titles = ui.Frame(f, column=1, row=0, columnspan=1, sticky='w')
        ui.Label(titles, text=' '.join(title), font='title',
                column=0, row=0, sticky='w')
        if prog_text:
            ui.Label(titles, text=prog_text, anchor='w', padx=10,
                    column=1, sticky='ew')
        ui.Label(f, image=page_icon, text='', row=0, column=0, sticky='nw')
        i = ui.Label(titles, text=instructions,
                    row=1, column=0, columnspan=2, sticky='wns')
        i.wrap()
        if group != 'NA':
            ui.Label(f, image=f'verify{img_mod}', text='',
                    row=1, column=0, sticky='nws')
        if macrosort:
            buttonframe = SortButtonFrame(f, sort_obj,
                                         list(items), macrosort=True,
                                         show_check=True,
                                         remove_on_click=True, column=1,
                                         row=1, sticky='nsew', columnspan=2)
        else:
            buttonframe = ui.ScrollingFrame(f, row=1, column=1, sticky='wsn')
            bc = buttoncolumns if len(items) >= min_to_multicolumn else 1
            for item in items:
                if runwindow.exitFlag.istrue():
                    return buttonframe, None
                if item is None:
                    continue
                n = len(buttonframe.content.winfo_children())
                verifybutton_fn(buttonframe.content, item,
                               row=n // bc, column=n % bc, label=False)
        verifycanary = ui.Frame(buttonframe.content,
                               row=buttonframe.content.nrows(), sticky='ew')
        ui.Button(verifycanary, text=oktext,
                 cmd=verifycanary.destroy, anchor='w',
                 font='instructions', column=0, row=0, sticky='ew')
        return buttonframe, verifycanary

    def build_verify_button(self, parent, text, sense, is_label,
                           notok_fn, row, column, ipady, **kwargs):
        """Build a single verify button or label. Returns (widget, frame_or_None)."""
        if is_label:
            b = ui.Label(parent, text=text, column=column, row=row,
                        sticky='ew', ipady=ipady, **kwargs)
            bf = None
        else:
            bf = ui.Frame(parent, pady=1, padx=1, column=column, row=row,
                         sticky='w', border=True)
            b = ui.Button(bf, text=text, pady='0', cmd=notok_fn,
                         column=column, row=0, sticky='ew',
                         ipady=ipady, **kwargs)
        b['image'] = self.set_sense_illustration(sense)
        b['compound'] = 'left'
        return b, bf

    def build_join_layout(self, runwindow, title, page_icon, img_mod):
        """Build the join window layout.
        Returns (titles_frame, progress, response_button_frame, pair_frame)."""
        f = runwindow.frame
        f.titles = ui.Frame(f, column=1, row=0, columnspan=1, sticky='ew')
        ui.Label(f.titles, text=title, font='title', anchor='w',
                column=0, row=0, sticky='ew')
        progress = ui.Progressbar(f.titles, row=1, sticky='ew')
        ui.Label(f, image=page_icon, text='', row=0, column=0, sticky='nw')
        ui.Label(f, image=f'join{img_mod}', image_pixels=300,
                image_scaleto='width', text='',
                row=1, column=0, rowspan=2, sticky='nw')
        response_button_frame = ui.Frame(f, column=1, row=2,
                                        pady=10, sticky='news')
        pair_frame = ui.Frame(f, column=1, row=1)
        return progress, response_button_frame, pair_frame

    def build_join_buttons(self, response_frame, img_mod,
                          join_fn, distinguish_fn):
        """Add Same/Different buttons to the join response frame."""
        ui.Button(response_frame, text=_("Same"), font='read',
                 image=f'join{img_mod}_same', compound="bottom",
                 image_pixels=200, image_scaleto='width',
                 cmd=join_fn, column=0, padx=10, ipadx=10, sticky='nsw')
        ui.Button(response_frame, text=_("Different"), font='read',
                 image=f'join{img_mod}_different', compound="bottom",
                 image_pixels=200, image_scaleto='width',
                 cmd=distinguish_fn, column=1, padx=10, ipadx=10, sticky='nes')

    def build_join_pair(self, pair_frame, buttonclass, sort_obj,
                       current_pair, buttons):
        """Build or show button frames for a pair of groups.
        Returns canary label."""
        r = 0
        for group in current_pair:
            if group in buttons:
                buttons[group].grid(row=r)
            else:
                buttons[group] = buttonclass(pair_frame, sort_obj,
                                            group=group, showtonegroup=True,
                                            label=True, row=r, sticky='w')
            r = 1
        canary = ui.Label(pair_frame, text='', col=1)
        return canary
