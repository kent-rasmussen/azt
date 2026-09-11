#!/usr/bin/env python3
# coding=UTF-8
"""Themes and the image list — the app's, not a backend's.

WHY THIS MODULE EXISTS. Both were declared inside `ui_tkinter.Theme` and then
HAND-COPIED into `ui_webview.Theme`, and both copies were short. That produced
two user-visible faults on one afternoon (2026-09-11), plus the suspicion that
there are more:

  * **35 of 81 images missing** from the webview copy — including `record`
    (so the record button had no icon), every sort-board verb image (`sort`,
    `join`, `join_same`, `verify`, `joinglyphs`…), the numbered C/V images,
    and `alpha_chart_icon`/`alpha_page_icon` (so two Reports-tab entries had
    no icon while the other seven did). `theme.photo.get(name)` returns None
    for a name that was never in the list, and a Button given `image=None`
    draws no image and logs nothing, so all of it failed silently.
    See agenda/webview_imagelist_stale_copy.md.
  * **Kent's own theme missing** — `Kim` is defined under tkinter and absent
    from the webview copy's four entries, and `ui_webview.Theme.__init__`
    answered an unknown name by falling back to `greygreen` WITHOUT SAYING
    SO. So the log said "Using theme Kim" and the screen was green.

Neither is a backend question. A theme is a choice the user made and an image
is a file in `images/`; which widget toolkit paints them is irrelevant. So
they live here, the backends import them, and there is nothing left to drift.

This module imports NOTHING — which is the point. `ui_webview` deliberately
avoids importing `ui_tkinter` (that would pull in tkinter, which may be absent
on a webview-only machine), and that constraint is what made copying look like
the only option. A data module with no imports satisfies it.

**Adding a theme or an image: do it HERE, once.**
"""

# ── Images ───────────────────────────────────────────────────────────────
# (name, filename) relative to `<aztdir>/images/`. Order is preserved because
# the tkinter loader reports progress against it.
IMAGELIST = [
    ('transparent', 'AZT stacks6.png'),
    ('tall', 'AZT clear stacks tall.png'),
    ('small', 'AZT stacks6_sm.png'),
    ('icon', 'AZT stacks6_icon.png'),
    ('icontall', 'AZT clear stacks tall_icon.png'),
    ('iconT', 'T alone clear6_icon.png'),
    ('iconC', 'Z alone clear6_icon.png'),
    ('iconV', 'A alone clear6_icon.png'),
    ('iconCV', 'ZA alone clear6_icon.png'),
    ('iconWord', 'ZAZA clear stacks6_icon.png'),
    ('iconWordRec', 'ZAZA Rclear stacks6_icon.png'),
    ('iconTRec', 'T Rclear stacks6_icon.png'),
    ('iconReport', 'Report_icon.png'),
    ('iconReportLogo', 'Generic AZT Reports_icon.png'),
    ('iconTRep', 'T Report_icon.png'),
    ('iconCVRep', 'ZA Report_icon.png'),
    ('iconTranscribe', 'Transcribe Tone_icon.png'),
    ('iconTranscribeC', 'Consonant Choice_icon.png'),
    ('iconTranscribeV', 'Vowel Choice_icon.png'),
    ('iconJoinUF', 'Join Tone_icon.png'),
    ('iconTRepcomp', 'T Report Comprehensive_icon.png'),
    ('iconVRepcomp', 'A Report Comprehensive_icon.png'),
    ('iconCRepcomp', 'Z Report Comprehensive_icon.png'),
    ('iconCVRepcomp', 'ZA Report Comprehensive_icon.png'),
    ('iconVCCVRepcomp', 'AZZA Report Comprehensive_icon.png'),
    ('USBdrive', 'USB drive.png'),
    ('T', 'T alone clear6.png'),
    ('C', 'Z alone clear6.png'),
    ('C1', 'Z alone 1.png'),
    ('C2', 'Z alone 2.png'),
    ('C3', 'Z alone 3.png'),
    ('C4', 'Z alone 4.png'),
    ('C5', 'Z alone 5.png'),
    ('C6', 'Z alone 6.png'),
    ('V', 'A alone clear6.png'),
    ('V1', 'A alone 1.png'),
    ('V2', 'A alone 2.png'),
    ('V=', 'A alone equals.png'),
    ('V1=V2', 'A alone 1=2.png'),
    ('V2=V3', 'A alone 2=3.png'),
    ('V3=V4', 'A alone 3=4.png'),
    ('V3', 'A alone 3.png'),
    ('V4', 'A alone 4.png'),
    ('V5', 'A alone 5.png'),
    ('V6', 'A alone 6.png'),
    # syllable-profile (cvt 'S'); was 'CV' (dormant SortCV)
    ('S', 'ZA alone clear6.png'),
    ('Word', 'ZAZA clear stacks6.png'),
    ('WordRec', 'ZAZA Rclear stacks6.png'),
    ('TRec', 'T Rclear stacks6.png'),
    ('Report', 'Report.png'),
    ('ReportLogo', 'Generic AZT Reports.png'),
    ('TRep', 'T Report.png'),
    ('CVRep', 'ZA Report.png'),
    ('Transcribe', 'Transcribe Tone.png'),
    ('TranscribeC', 'Consonant Choice.png'),
    ('TranscribeV', 'Vowel Choice.png'),
    ('JoinUF', 'Join Tone.png'),
    ('TRepcomp', 'T Report Comprehensive.png'),
    ('VRepcomp', 'A Report Comprehensive.png'),
    ('CRepcomp', 'Z Report Comprehensive.png'),
    ('CVRepcomp', 'ZA Report Comprehensive.png'),
    ('VCCVRepcomp', 'AZZA Report Comprehensive.png'),
    ('backgrounded', 'AZT stacks6.png'),
    # Images for tasks
    ('verify', 'Verify List.png'),
    ('verifyglyphs', 'Verify Group List.png'),
    ('sort', 'Sort List.png'),
    ('sortglyphs', 'Sort List Stack Groups.png'),
    ('join', 'Join List.png'),
    ('join_same', 'Join List same.png'),
    ('join_different', 'Join List different.png'),
    ('joinglyphs', 'Join Stack Groups.png'),
    ('joinglyphs_same', 'Join Stack Groups same.png'),
    ('joinglyphs_different', 'Join Stack Groups different.png'),
    ('record', 'Microphone alone_sm.png'),
    ('change', 'Change Circle_sm.png'),
    ('checkedbox', 'checked.png'),
    ('uncheckedbox', 'unchecked.png'),
    ('checkedbox_sm', 'checked_sm.png'),
    ('uncheckedbox_sm', 'unchecked_sm.png'),
    ('alpha_chart', 'Alphabet_ChartZ.png'),
    ('alpha_chart_icon', 'Alphabet_ChartZ_icon.png'),
    ('alpha_page', 'Alphabet_PageZ.png'),
    ('alpha_page_icon', 'Alphabet_PageZ_icon.png'),
    ('NoImage', 'toselect/Image-Not-Found.png'),
    ('Order!', 'toselect/order!.png'),
]

# ── Themes ───────────────────────────────────────────────────────────────
# Every theme supplies the same six keys. `None` means "leave it to the
# toolkit's own default", which is why `tkinterdefault` is mostly None and
# why `offwhite` is None in the older themes.
#
# `highlight` is 'red' in EVERY theme and is read by nothing but a comment
# warning against using it (see .wv-progressbar in grid.css, where using it
# painted the bar red). Left as-is: changing it is a separate decision from
# sharing the data.
DEFAULT_THEME = 'greygreen'

THEMES = {
    'lightgreen': {            # lighter green
        'background': '#c6ffb3', 'activebackground': '#c6ffb3',
        'offwhite': None, 'highlight': 'red',
        'menubackground': 'white', 'white': 'white'},
    'green': {
        'background': '#b3ff99', 'activebackground': '#c6ffb3',
        'offwhite': None, 'highlight': 'red',
        'menubackground': 'white', 'white': 'white'},
    'pink': {
        'background': '#ff99cc', 'activebackground': '#ff66b3',
        'offwhite': None, 'highlight': 'red',
        'menubackground': 'white', 'white': 'white'},
    'lighterpink': {
        'background': '#ffb3d9', 'activebackground': '#ff99cc',
        'offwhite': None, 'highlight': 'red',
        'menubackground': 'white', 'white': 'white'},
    'evenlighterpink': {
        'background': '#ffcce6', 'activebackground': '#ffb3d9',
        'offwhite': '#ffe6f3', 'highlight': 'red',
        'menubackground': 'white', 'white': 'white'},
    'purple': {
        'background': '#ffb3ec', 'activebackground': '#ff99e6',
        'offwhite': '#ffe6f9', 'highlight': 'red',
        'menubackground': 'white', 'white': 'white'},
    'Howard': {
        'background': 'green', 'activebackground': 'red',
        'offwhite': 'grey', 'highlight': 'red',
        'menubackground': 'white', 'white': 'white'},
    'Kent': {
        'background': 'red', 'activebackground': 'green',
        'offwhite': 'grey', 'highlight': 'red',
        'menubackground': 'white', 'white': 'white'},
    'Kim': {
        'background': '#ffbb99', 'activebackground': '#ffaa80',
        'offwhite': '#ffeee6', 'highlight': 'red',
        'menubackground': 'white', 'white': 'white'},
    'yellow': {
        'background': '#ffff99', 'activebackground': '#ffff80',
        'offwhite': '#ffffe6', 'highlight': 'red',
        'menubackground': 'white', 'white': 'white'},
    'greygreen1': {
        'background': '#62d16f', 'activebackground': '#4dcb5c',
        'offwhite': '#ebf9ed', 'highlight': 'red',
        'menubackground': 'white', 'white': 'white'},
    'lightgreygreen': {
        'background': '#9fdfca', 'activebackground': '#8cd9bf',
        'offwhite': '#ecf9f4', 'highlight': 'red',
        'menubackground': 'white', 'white': 'white'},
    'greygreen': {             # default; activebackground 10% darker
        'background': '#8cd9bf', 'activebackground': '#66ccaa',
        'offwhite': '#ecf9f4', 'highlight': 'red',
        'menubackground': 'white', 'white': 'white'},
    'highcontrast': {          # for low light environments
        'background': 'white', 'activebackground': '#e6fff9',
        'offwhite': '#ecf9f4', 'highlight': 'red',
        'menubackground': 'white', 'white': 'white'},
    'tkinterdefault': {
        'background': None, 'activebackground': None,
        'offwhite': None, 'highlight': 'red',
        'menubackground': 'white', 'white': 'white'},
}
