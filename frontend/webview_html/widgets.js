/**
 * Widget management for the pywebview backend.
 *
 * Each Python widget has a unique integer _wid.
 * This module maps wid → HTMLElement, handles creation, property updates,
 * grid layout, event dispatch, and destruction.
 */
'use strict';

const _widgets = new Map();  // wid → HTMLElement
let _nextWid = 0;

// ── Helpers ────────────────────────────────────────────────────────────

function _stickyToStyle(sticky) {
    // Convert tkinter sticky string to CSS justify-self / align-self
    const s = (sticky || '').toLowerCase();
    const style = {};
    const hasN = s.includes('n');
    const hasS = s.includes('s');
    const hasE = s.includes('e');
    const hasW = s.includes('w');

    // NO STICKY MEANS CENTRE, NOT STRETCH. Saying nothing here left the grid
    // to its own default, which IS stretch — so `sticky=''` behaved exactly
    // like `sticky='nsew'`, the opposite of what tkinter means by it
    // ("do not stretch; centre in the cell"). Every axis is now stated
    // rather than defaulted (Kent, 2026-09-14: "nor sticky impact").
    if (hasN && hasS) style.alignSelf = 'stretch';
    else if (hasN)    style.alignSelf = 'start';
    else if (hasS)    style.alignSelf = 'end';
    else              style.alignSelf = 'center';

    if (hasE && hasW) style.justifySelf = 'stretch';
    else if (hasE)    style.justifySelf = 'end';
    else if (hasW)    style.justifySelf = 'start';
    else              style.justifySelf = 'center';

    return style;
}

function _applyGrid(el, opts) {
    // Apply CSS Grid placement from tkinter-style grid kwargs
    if (opts.row !== undefined)
        el.style.gridRow = (opts.row + 1) + (opts.rowspan > 1 ? ' / span ' + opts.rowspan : '');
    if (opts.column !== undefined)
        el.style.gridColumn = (opts.column + 1) + (opts.columnspan > 1 ? ' / span ' + opts.columnspan : '');

    const sty = _stickyToStyle(opts.sticky);
    if (sty.alignSelf)   el.style.alignSelf   = sty.alignSelf;
    if (sty.justifySelf) el.style.justifySelf = sty.justifySelf;

    if (opts.padx) el.style.margin = `0 ${opts.padx}px`;
    if (opts.pady) {
        el.style.marginTop    = `${opts.pady}px`;
        el.style.marginBottom = `${opts.pady}px`;
    }
    if (opts.ipadx) el.style.paddingLeft = el.style.paddingRight = `${opts.ipadx}px`;
    if (opts.ipady) el.style.paddingTop = el.style.paddingBottom = `${opts.ipady}px`;
}

// ── API exposed to Python via pywebview.api ───────────────────────────

function createWidget(spec) {
    // spec: {wid, type, parent_wid, props, grid}
    //
    // A WINDOW IS NOT A DOM WIDGET. Toplevel/Root create a pywebview window,
    // never a DOM element, so they are absent from _widgets — and every
    // widget parented directly to a task window therefore resolved
    // parent_wid to `undefined`, hit `if (parentEl)` and was SILENTLY NEVER
    // APPENDED. Its children inherited the same fate, so an entire page
    // vanished with no error, an empty console and a blank window. (The
    // debug badge stayed visible because it appends to <body> itself, which
    // is what made the pages look like a visibility problem rather than a
    // parenting one.)
    //
    // In a window the window IS the page, so an unresolved parent means the
    // page root. Warn rather than fail quietly: a parent that is missing for
    // any OTHER reason is a real bug and must not look like this again.
    let el;
    let parentEl = spec.parent_wid != null
        ? _widgets.get(spec.parent_wid) : document.getElementById('root');
    if (!parentEl) {
        parentEl = document.getElementById('root');
        // Only a WIDGET parent that cannot be found is a fault. Parented to a
        // window is normal and must stay quiet, or the console fills with
        // warnings about the expected case and real ones get lost in them.
        if (!spec.parent_is_window) {
            console.warn('azt: widget', spec.wid, '(' + spec.type + ') has no'
                         + ' DOM parent for wid', spec.parent_wid,
                         '- attaching to #root');
        }
    }

    switch (spec.type) {
        case 'frame':
            el = document.createElement('div');
            el.className = 'wv-widget wv-frame';
            if (spec.props.borderwidth || spec.props.relief)
                _setBorder(el, spec.props.borderwidth, spec.props.relief);
            break;
        case 'label':
            el = document.createElement('div');
            el.className = 'wv-widget wv-label';
            if (spec.props.text) el.textContent = spec.props.text;
            if (spec.props.font) el.classList.add('font-' + spec.props.font);
            if (spec.props.image) _setImage(el, spec.props.image, spec.props.compound,
                                            spec.props.image_pixels,
                                            spec.props.image_scaleto);
            // AFTER the image: _setImage adds the .wv-compound classes that
            // decide flex-direction, and _setAnchor reads that direction.
            if (spec.props.anchor) _setAnchor(el, spec.props.anchor);
            if (spec.props.borderwidth || spec.props.relief)
                _setBorder(el, spec.props.borderwidth, spec.props.relief);
            break;
        case 'button':
            el = document.createElement('button');
            el.className = 'wv-widget wv-button';
            if (spec.props.text) el.textContent = spec.props.text;
            if (spec.props.font) el.classList.add('font-' + spec.props.font);
            if (spec.props.image) _setImage(el, spec.props.image, spec.props.compound,
                                            spec.props.image_pixels,
                                            spec.props.image_scaleto);
            if (spec.props.anchor) _setAnchor(el, spec.props.anchor);
            if (spec.props.disabled) el.disabled = true;
            if (spec.props.state) _setState(el, spec.props.state);
            el.addEventListener('click', () => {
                if (window.pywebview && window.pywebview.api) {
                    window.pywebview.api.on_event(spec.wid, 'command', {});
                }
            });
            break;
        case 'entry':
            el = document.createElement('input');
            el.className = 'wv-widget wv-entry';
            el.type = 'text';
            // An <input> does NOT inherit font from its ancestors — browsers
            // give form controls their own default — so a font class on a
            // parent never reached it, and `font='readbig'` was being dropped
            // in ui_webview besides. Both halves, or an entry field stays at
            // the browser default while every label around it is right.
            if (spec.props.font) el.classList.add('font-' + spec.props.font);
            if (spec.props.width) el.style.width = spec.props.width + 'ch';
            el.addEventListener('input', () => {
                if (window.pywebview && window.pywebview.api) {
                    window.pywebview.api.on_event(spec.wid, 'input', {value: el.value});
                }
            });
            break;
        case 'progressbar':
            el = document.createElement('div');
            el.className = 'wv-widget wv-progressbar';
            const fill = document.createElement('div');
            fill.className = 'wv-progressbar-fill';
            el.appendChild(fill);
            // A VERTICAL BAR IS A DIFFERENT SHAPE, not a rotated one: it is
            // tall and narrow and fills from the BOTTOM, which is what
            // tkinter draws and what a reader expects of a column.
            if (String(spec.props.orient || '') === 'vertical')
                el.classList.add('wv-progressbar-vertical');
            break;
        case 'checkbutton': {
            el = document.createElement('label');
            el.className = 'wv-widget wv-checkbutton';
            const cb = document.createElement('input');
            cb.type = 'checkbox';
            cb.checked = !!spec.props.checked;
            // SIZE. tkinter draws this control from a theme image pair, so a
            // page asking for a bigger or smaller checkbox says so with
            // `image_pixels`/`large_images` — see ui_webview.CheckButton.
            // The browser draws the box, but not at a size anyone chose, so
            // every webview checkbox came out at the engine default.
            _setBoxSize(cb, spec.props.box_pixels, spec.props.box_scaleto,
                        spec.props.box_large);
            el.appendChild(cb);
            const cblbl = document.createElement('span');
            cblbl.textContent = spec.props.text || '';
            el.appendChild(cblbl);
            if (spec.props.font) el.classList.add('font-' + spec.props.font);
            cb.addEventListener('change', () => {
                if (window.pywebview && window.pywebview.api) {
                    window.pywebview.api.on_event(spec.wid, 'toggle', {checked: cb.checked});
                }
            });
            break;
        }
        case 'radiobutton': {
            el = document.createElement('label');
            el.className = 'wv-widget wv-radiobutton';
            const rb = document.createElement('input');
            rb.type = 'radio';
            rb.name = spec.props.group || 'default';
            rb.value = spec.props.value || '';
            el.appendChild(rb);
            const rblbl = document.createElement('span');
            rblbl.textContent = spec.props.text || '';
            el.appendChild(rblbl);
            if (spec.props.font) el.classList.add('font-' + spec.props.font);
            rb.addEventListener('change', () => {
                if (window.pywebview && window.pywebview.api) {
                    window.pywebview.api.on_event(spec.wid, 'select', {value: rb.value});
                }
            });
            break;
        }
        case 'listbox': {
            el = document.createElement('div');
            el.className = 'wv-widget wv-listbox';
            el.tabIndex = 0;
            if (spec.props.height) el.style.maxHeight = (spec.props.height * 1.5) + 'em';
            if (spec.props.width) el.style.width = spec.props.width + 'ch';
            if (spec.props.font) el.classList.add('font-' + spec.props.font);
            // Read by the click handler in updateProp('items'), which is
            // where rows are built — so it has to be on the element rather
            // than in a closure over this spec. The MODE ITSELF, not just
            // the boolean: extended and multiple are both "more than one"
            // and behave differently under the pointer.
            if (spec.props.multiple) el.dataset.multiple = 'true';
            if (spec.props.selectmode)
                el.dataset.selectmode = String(spec.props.selectmode);
            // Items added via updateProp('items', [...])
            break;
        }
        case 'combobox': {
            // TYPEABLE ONLY IF ASKED. ttk.Combobox has a `state`: 'readonly'
            // restricts the user to the list, and 'normal' (ttk's default)
            // leaves the entry half EDITABLE, so a value that is not in the
            // list can be typed in (Kent, 2026-09-14: "I recall an option
            // that allows you to search/filter, and/or input something not
            // on the list?"). A <select> cannot do that at all.
            //   The <select> stays the default even though ttk's default is
            // 'normal', because it is the better control for the app's one
            // call site (the field-type picker, tasks.py:1119, where a typed
            // value has nothing to map to) and because <datalist> support in
            // WebKitGTK cannot be relied on for the dropdown half. Asking for
            // state='normal' explicitly gets the editable form; the
            // divergence from ttk's default is deliberate and recorded here.
            if (String(spec.props.state || '') === 'normal') {
                el = document.createElement('span');
                el.className = 'wv-widget wv-combobox-wrap';
                const inp = document.createElement('input');
                inp.type = 'text';
                inp.className = 'wv-combobox';
                inp.setAttribute('list', 'wv-dl-' + spec.wid);
                const dl = document.createElement('datalist');
                dl.id = 'wv-dl-' + spec.wid;
                if (spec.props.width) inp.style.width = spec.props.width + 'ch';
                if (spec.props.font) inp.classList.add('font-' + spec.props.font);
                el.appendChild(inp);
                el.appendChild(dl);
                // `change` (not `input`) so the report fires on a finished
                // entry rather than on every keystroke — ttk fires
                // <<ComboboxSelected>> on a pick, and a typed value lands
                // when the field is left or Enter is pressed.
                inp.addEventListener('change', () => {
                    if (window.pywebview && window.pywebview.api) {
                        window.pywebview.api.on_event(spec.wid, 'select',
                                                      {value: inp.value});
                    }
                });
                break;
            }
            el = document.createElement('select');
            el.className = 'wv-widget wv-combobox';
            if (spec.props.width) el.style.width = spec.props.width + 'ch';
            if (spec.props.font) el.classList.add('font-' + spec.props.font);
            el.addEventListener('change', () => {
                if (window.pywebview && window.pywebview.api) {
                    window.pywebview.api.on_event(spec.wid, 'select', {value: el.value});
                }
            });
            break;
        }
        case 'menu': {
            el = document.createElement('div');
            el.className = 'wv-widget wv-menu wv-hidden';
            break;
        }
        case 'notebook': {
            // Tab strip above, one panel showing at a time below. Explicit
            // display so the generic "make the parent a grid" below leaves it
            // alone - a notebook is not a grid container, its PANELS are.
            el = document.createElement('div');
            el.className = 'wv-widget wv-notebook';
            el.style.display = 'flex';
            el.style.flexDirection = 'column';
            const strip = document.createElement('div');
            strip.className = 'wv-tabstrip';
            const panels = document.createElement('div');
            panels.className = 'wv-tabpanels';
            el.appendChild(strip);
            el.appendChild(panels);
            break;
        }
        default:
            el = document.createElement('div');
            el.className = 'wv-widget';
    }

    // EXTRA CLASSES FROM PYTHON. A subclass that wants its own styling has
    // no way to say so otherwise: every Frame subclass is created with
    // widget_type='frame' and gets `wv-frame`, so `.wv-scrolling-frame` in
    // grid.css had never matched anything at all — ScrollingFrame was a
    // plain frame wearing no class of its own, which is why capping its
    // height in the stylesheet did nothing (Kent, 2026-09-14).
    if (spec.props && spec.props.cssclass) {
        String(spec.props.cssclass).split(/\s+/).forEach(c => {
            if (c) el.classList.add(c);
        });
    }

    el.dataset.wid = spec.wid;
    _widgets.set(spec.wid, el);

    // AFTER REGISTRATION, because these route through updateProp and it
    // looks the widget up in `_widgets`. A `wraplength` given at
    // construction was going nowhere: updateProp has handled the option for
    // a while, but only `wrap()` ever called it, so the constructor kwarg
    // was inert and a label asked to wrap at 200px ran to full width and
    // blew its grid column out (Kent's gallery, 2026-09-14).
    if (spec.props && spec.props.wraplength)
        updateProp(spec.wid, 'wraplength', spec.props.wraplength);

    if (spec.grid) {
        _applyGrid(el, spec.grid);
    }

    if (parentEl) {
        // Ensure parent is a grid container
        if (!parentEl.style.display || parentEl.style.display === '') {
            parentEl.style.display = 'grid';
        }
        parentEl.appendChild(el);
    }

    return spec.wid;
}

// ── checkbox / radio size ────────────────────────────────────────────
// A native <input> ignores width/height in some engines unless the default
// appearance is turned off, so set both dimensions AND clear the appearance
// when a size is asked for. `accent-color` keeps it looking like a control
// rather than a bare square once appearance is gone.
//
// `large_images` is not a pixel figure in tkinter — it selects the full-size
// theme image over the `_sm` one — so it maps to a step up from the default
// rather than to a number.
const _BOX_LARGE_PX = 24;

function _setBoxSize(input, px, scaleto, large) {
    const n = px ? parseInt(px, 10) : (large ? _BOX_LARGE_PX : 0);
    if (!(n > 0)) return;
    // scaleto 'height' is what the app passes (tasks.py:1173) and a checkbox
    // is square, so one figure drives both unless a width is named.
    if (scaleto === 'width') {
        input.style.width = n + 'px';
    } else if (scaleto === 'height') {
        input.style.height = n + 'px';
        input.style.width = n + 'px';
    } else {
        input.style.width = n + 'px';
        input.style.height = n + 'px';
    }
    // THE CLASS CARRIES THE APPEARANCE, not inline styles. Sizing a native
    // checkbox needs `appearance:none` (WebKit ignores width/height
    // otherwise), and that removes the engine's check mark — so a checked
    // box would show NOTHING, which is worse than the wrong size. Drawing
    // the mark needs `:checked`, which cannot be written inline. See
    // `.wv-sized-box` in grid.css.
    input.classList.add('wv-sized-box');
}

// ── borderwidth / relief ─────────────────────────────────────────────
// tkinter's reliefs have EXACT CSS counterparts, which is rare among the
// options in this file: raised→outset, sunken→inset, and groove/ridge are
// CSS values by those very names. So this is a translation, not a
// lookalike. 'flat' means no border however wide it was asked to be, which
// is tkinter's behaviour too.
//
// Border COLOUR is `currentColor` — the text colour — deliberately: it
// follows the theme without a second variable to keep in step, and it
// cannot become a colour-only signal, since a border is a shape.
const _RELIEF = {
    flat: 'none', solid: 'solid', raised: 'outset', sunken: 'inset',
    groove: 'groove', ridge: 'ridge',
};

function _setBorder(el, width, relief) {
    const style = _RELIEF[String(relief || '').toLowerCase()]
                  || (width ? 'solid' : null);
    if (!style) return;
    const n = parseInt(width, 10);
    el.style.borderStyle = style;
    el.style.borderWidth = ((n > 0 ? n : 1)) + 'px';
    el.style.borderColor = 'currentColor';
    el.style.boxSizing = 'border-box';
}

// ── anchor ───────────────────────────────────────────────────────────
// tkinter's `anchor` says where the CONTENT sits when the widget is bigger
// than it: n/ne/e/se/s/sw/w/nw, or c/center. 91 call sites pass it and
// ui_webview dropped every one, so nothing honoured it.
//
// THE AXIS SWAP IS THE WHOLE DIFFICULTY. `.wv-label` is already
// `display:flex`, so horizontal is `justify-content` and vertical is
// `align-items` — but `.wv-compound-top` / `-bottom` set
// `flex-direction: column` for an image above or below its text, and that
// EXCHANGES the two. Setting them by name without checking direction would
// rotate the anchor on exactly the widgets that carry pictures.
//
// A non-flex element (a plain `.wv-button`) has neither property, so it gets
// `text-align` for the horizontal part; there is nothing sensible to do
// about the vertical one and nothing that asked for it.
const _ANCHOR = {
    n:  ['center', 'start'],  ne: ['end',    'start'],  e: ['end',    'center'],
    se: ['end',    'end'],    s:  ['center', 'end'],    sw:['start',  'end'],
    w:  ['start',  'center'], nw: ['start',  'start'],
    c:  ['center', 'center'], center: ['center', 'center'],
};
const _FLEX = {start: 'flex-start', center: 'center', end: 'flex-end'};

function _setAnchor(el, anchor) {
    const key = String(anchor || '').toLowerCase();
    const pair = _ANCHOR[key];
    if (!pair) return;                  // unknown: leave the default alone
    const [h, v] = pair;
    // NOT getComputedStyle. The first version branched on the computed
    // `display`, and this runs from createWidget BEFORE the element is in
    // the document — so the computed value is the UA default (`block`),
    // never the stylesheet's `flex`, and every single anchor took the
    // text-align branch. All nine specimens in frontend/gallery.py came out
    // identical (2026-09-14).
    //
    // classList is knowable without the document, and BOTH mechanisms are
    // set unconditionally: flex properties are inert on a non-flex element
    // (a plain .wv-button) and text-align is inert on a flex container, so
    // whichever applies, applies.
    const column = el.classList.contains('wv-compound-top')
                || el.classList.contains('wv-compound-bottom');
    el.style.justifyContent = _FLEX[column ? v : h];
    el.style.alignItems     = _FLEX[column ? h : v];
    el.style.textAlign = h === 'start' ? 'left'
                       : h === 'end'   ? 'right' : 'center';
    el.dataset.anchor = key;    // so _reportAnchor can find one to measure
}

// ONE MEASUREMENT, ONCE, AFTER LAYOUT. Whether an anchored label can honour
// its anchor depends on whether `sticky` actually stretched it, and that
// cannot be read before the element is in the document — which is the same
// mistake as above, so it is not repeated by guessing. Called from a
// deferred hook; reports to the Python log through the console bridge.
function reportAnchor() {
    // ALL OF THEM, AND WHERE THE TEXT ACTUALLY SITS. Measuring one label's
    // box answered "was it stretched?" and nothing else, so it took a second
    // run to learn that the box had room and the letters still would not
    // move. What settles it is the TEXT's offset inside its own box: if
    // `at(dx,dy)` is the same in all nine, the anchor is not being applied;
    // if it varies with the anchor, it is, and the doubt was the eye's. The
    // `slack` pair says whether there was any room to move in — a slack of 0
    // makes every anchor look identical however correct the code is, which
    // is the trap the first two versions of this row fell into.
    const els = [...document.querySelectorAll('[data-anchor]')];
    if (!els.length) return 'no anchored widget on this page';
    return els.map(el => {
        const cs = getComputedStyle(el);
        const r = el.getBoundingClientRect();
        const range = document.createRange();
        range.selectNodeContents(el);
        const tr = range.getBoundingClientRect();
        return (el.dataset.anchor
                + ' box=' + Math.round(r.width) + 'x' + Math.round(r.height)
                + ' text=' + Math.round(tr.width) + 'x' + Math.round(tr.height)
                + ' at(' + Math.round(tr.left - r.left) + ','
                         + Math.round(tr.top - r.top) + ')'
                + ' slack(' + Math.round(r.width - tr.width) + ','
                            + Math.round(r.height - tr.height) + ')'
                + ' ' + cs.display + '/' + cs.justifyContent
                + '/' + cs.alignItems);
    }).join('\n    ');
}

// ── state: 'disabled' / 'normal' ─────────────────────────────────────
// tkinter's `state` reaches here three ways — a constructor kwarg, item
// assignment (`b['state']='disabled'`), and `.config(state=…)` — and the
// last two already worked, because `configure()` forwards any scalar as an
// updateProp. Two gaps remained (Kent, 2026-09-14):
//
//   * the CONSTRUCTOR path, which ui_webview popped and dropped, so a
//     button asked for disabled at creation started enabled
//     (`ui_shell.py:3227`);
//   * every widget that is not a <button>. `list_of_possibles.config(
//     state='disabled')` (ui_shell.py:3356) and `check_label['state']`
//     (sort_buttons.py:1154) did nothing at all.
//
// A native control gets `.disabled`, which stops events AND greys it. A div
// has neither, so it gets `pointer-events:none` (a Label's state is about
// look, but a clickable one must also stop responding) plus the class, so
// the stylesheet can say what disabled looks like.
function _setState(el, value) {
    const off = (value === 'disabled');
    if ('disabled' in el) {
        el.disabled = off;
    } else {
        el.style.pointerEvents = off ? 'none' : '';
    }
    el.classList.toggle('wv-disabled', off);
    // A fallback appearance, so a disabled control is visibly disabled even
    // with no stylesheet rule for the class. Cleared rather than set to a
    // value, so it does not fight a rule that does exist.
    el.style.opacity = off ? '0.5' : '';
}

// ── Images on labels and buttons ─────────────────────────────────────
// Both used to DISCARD `image` (ui_webview popped it and never sent it), so
// the chooser rendered as text-only buttons where the app shows icons.
// `compound` mirrors tkinter's: where the image sits relative to the text.
// `px`/`scaleto` are tkinter's image_pixels/image_scaleto. Without them the
// <img> had no size constraint at all, so an illustration rendered at its
// own resolution: the alphabet chart's cells burst the grid (Kent,
// 2026-09-14). Python was popping both kwargs and never sending them, so
// this is the other half of that fix.
//   'width'/'height' pin that dimension and let the other follow the aspect
// ratio, as scaling to one edge does in tkinter. With no scaleto, the image
// is FITTED INSIDE a px-by-px box (max-width and max-height), which
// preserves the aspect ratio and never enlarges a small picture — the
// behaviour a chart cell wants.
function _setImage(el, src, compound, px, scaleto) {
    const img = document.createElement('img');
    img.className = 'wv-img';
    img.src = src;
    img.alt = '';
    if (px) {
        const n = parseInt(px, 10);
        if (n > 0) {
            if (scaleto === 'width') {
                img.style.width = n + 'px';
                img.style.height = 'auto';
            } else if (scaleto === 'height') {
                img.style.height = n + 'px';
                img.style.width = 'auto';
            } else {
                img.style.maxWidth = n + 'px';
                img.style.maxHeight = n + 'px';
            }
        }
    }
    const text = el.textContent;
    el.textContent = '';
    el.classList.add('wv-compound', 'wv-compound-' + (compound || 'top'));
    if (text) {
        const span = document.createElement('span');
        span.className = 'wv-img-text';
        span.textContent = text;
        // 'left'/'top' describe where the IMAGE goes, as in tkinter.
        if (compound === 'right' || compound === 'bottom') {
            el.appendChild(span);
            el.appendChild(img);
        } else {
            el.appendChild(img);
            el.appendChild(span);
        }
    } else {
        el.appendChild(img);
    }
}

// ── Notebook ─────────────────────────────────────────────────────────
// add/select/bind were three bare `pass` stubs, which is what made the
// chooser unreachable: its three tab frames were created, never attached,
// and never shown.
function _notebookParts(wid) {
    const el = _widgets.get(wid);
    if (!el) return null;
    return {el: el,
            strip: el.querySelector(':scope > .wv-tabstrip'),
            panels: el.querySelector(':scope > .wv-tabpanels')};
}

function notebookAdd(wid, childWid, text) {
    const p = _notebookParts(wid);
    const child = _widgets.get(childWid);
    if (!p || !child) return;
    // createWidget already appended the child to the notebook itself; a tab
    // panel belongs in the panels box, so move it.
    p.panels.appendChild(child);
    child.classList.add('wv-tabpanel');

    const tab = document.createElement('div');
    tab.className = 'wv-tab';
    tab.textContent = text || '';
    tab.dataset.panelWid = childWid;
    tab.addEventListener('click', () => notebookSelect(wid, childWid, true));
    p.strip.appendChild(tab);

    // FIRST TAB SELECTED, EVERY LATER ONE HIDDEN. Only the first add used to
    // call notebookSelect, so panels 2..n were appended VISIBLE and nothing
    // ever hid them: a notebook's pages all stacked on top of each other
    // (Kent's gallery, 2026-09-14, seven tabs' content on one page).
    //
    // The chooser escaped it by accident — it adds its three tabs and then
    // calls `_select_chooser_tab(...)`, and that select hides the rest. So
    // the bug was invisible for as long as the only caller happened to
    // select afterwards, which is not something a Notebook may require.
    if (p.strip.children.length === 1) {
        notebookSelect(wid, childWid, false);
    } else {
        child.classList.add('wv-hidden');
    }
}

function notebookSelect(wid, childWid, notify) {
    const p = _notebookParts(wid);
    if (!p) return;
    let index = -1, i = 0;
    for (const tab of p.strip.children) {
        const on = String(tab.dataset.panelWid) === String(childWid);
        tab.classList.toggle('wv-tab-selected', on);
        const panel = _widgets.get(Number(tab.dataset.panelWid));
        if (panel) panel.classList.toggle('wv-hidden', !on);
        if (on) index = i;
        i += 1;
    }
    if (notify && window.pywebview && window.pywebview.api) {
        window.pywebview.api.on_event(wid, 'tabchanged',
                                      {index: index, panel_wid: childWid});
    }
}

// ── focus_set ────────────────────────────────────────────────────────
// Put the keyboard in a widget. tkinter's widgets all answer focus_set(),
// and EntryField.focus_set() calls this — Transcriber.addchar uses it after
// clearing the field so the user can carry on typing. Missing until
// 2026-09-09, when EntryField.delete/insert were added for the same caller.
// `select` as well as `focus`: an entry that has just been cleared and
// refilled reads better with its contents selected, which is what tkinter's
// focus into a re-set entry effectively gives you.
function focusWidget(wid) {
    const el = _widgets.get(wid);
    if (!el) return;
    try {
        el.focus();
        if (typeof el.select === 'function' && el.value) el.select();
    } catch (e) {
        console.warn('focusWidget failed for ' + wid, e);
    }
}

// ── ToolTip ──────────────────────────────────────────────────────────
// The CSS class existed and nothing ever created one. ~38 call sites.
function setTooltip(wid, text) {
    const el = _widgets.get(wid);
    if (!el) return;
    if (!text) { delete el.dataset.tooltip; return; }
    el.dataset.tooltip = text;
    if (el._wvTipBound) return;
    el._wvTipBound = true;
    let tip = null;
    const show = (ev) => {
        if (tip || !el.dataset.tooltip) return;
        tip = document.createElement('div');
        tip.className = 'wv-tooltip';
        tip.textContent = el.dataset.tooltip;
        document.body.appendChild(tip);
        const r = el.getBoundingClientRect();
        tip.style.left = Math.round(r.left) + 'px';
        tip.style.top = Math.round(r.bottom + 4) + 'px';
    };
    const hide = () => { if (tip) { tip.remove(); tip = null; } };
    el.addEventListener('mouseenter', show);
    el.addEventListener('mouseleave', hide);
    el.addEventListener('click', hide);
}

// ── Style ────────────────────────────────────────────────────────────
// ttk's Style is a name->options table consulted by widgets; CSS is a
// name->options table consulted by elements. So a ttk style name maps to a
// selector and the options to declarations, written into one stylesheet
// that later calls can overwrite by rule name.
const _styleSheet = (() => {
    const s = document.createElement('style');
    s.id = 'wv-ttk-styles';
    document.head.appendChild(s);
    return s;
})();
const _styleRules = new Map();   // selector -> {prop: value}

function setStyleRule(selector, decls) {
    const cur = _styleRules.get(selector) || {};
    Object.assign(cur, decls);
    _styleRules.set(selector, cur);
    let css = '';
    for (const [sel, d] of _styleRules) {
        const body = Object.entries(d)
            .map(([k, v]) => `${k}: ${v};`).join(' ');
        if (body) css += `${sel} { ${body} }\n`;
    }
    _styleSheet.textContent = css;
}

function updateProp(wid, prop, value) {
    const el = _widgets.get(wid);
    if (!el) return;

    switch (prop) {
        case 'text':
            el.textContent = value;
            break;
        case 'background':
            el.style.background = value;
            break;
        case 'state':
            _setState(el, value);
            break;
        case 'anchor':
            _setAnchor(el, value);
            break;
        case 'image':
            // value is a base64 data URI
            if (el.tagName === 'IMG') {
                el.src = value;
            } else {
                let img = el.querySelector('img');
                if (!img) {
                    img = document.createElement('img');
                    el.prepend(img);
                }
                img.src = value;
            }
            break;
        case 'progress':
            const fill = el.querySelector('.wv-progressbar-fill');
            if (fill) {
                // The percentage drives the dimension the bar GROWS in, so
                // a vertical bar sets height and stays full width. Setting
                // width on a vertical bar is what drew it horizontally.
                if (el.classList.contains('wv-progressbar-vertical')) {
                    fill.style.height = value + '%';
                    fill.style.width = '100%';
                } else {
                    fill.style.width = value + '%';
                }
            }
            break;
        case 'width':
            el.style.width = value + 'ch';
            break;
        case 'max_height_em':
            // A scroller's own height, in text rows, beating the stylesheet's
            // generic cap. Inline so it wins; `em` so it tracks the font the
            // way tkinter's row count does.
            el.style.maxHeight = value + 'em';
            break;
        case 'wraplength':
            // TEXT THAT MUST WRAP. Named after tkinter's own option, which
            // is what the app calls `Label.wrap()` to get — and which the
            // webview backend answered with `pass` ("handled by CSS"). The
            // CSS rule is scoped to labels one or two levels under #root, on
            // purpose, so anything deeper got no constraint: ErrorNotice's
            // text rendered as one unbroken line and the window fitted
            // itself to it, 1680px wide with a single line across the top
            // (macOS, 2026-09-11).
            //   PIXELS for a number, because every layout figure in this app
            //   is raw pixels (see the PT_TO_PX note in ui_tkinter) and the
            //   value arriving here is the caller's own measurement of the
            //   box this label sits in — or `availablexy`'s. A string is
            //   passed through so a caller can still say '40em' deliberately.
            // CLAMPED TO THE VIEWPORT, because an inline style BEATS the
            // stylesheet. grid.css caps .wv-label at 92vw so nothing can
            // demand more width than the window has — and setting maxWidth
            // inline here silently defeated that cap for every caller of
            // wrap(). The Sound Card Settings caveat ran off the right edge
            // of its window under GTK on exactly this path (2026-09-11):
            // wrap() measured a box wider than the window, and the 92vw
            // safety valve was overridden by the number it measured.
            //   CSS min() keeps BOTH constraints in one value: the caller's
            // measurement of its own box, and the invariant that nothing
            // exceeds the display.
            el.style.maxWidth = (typeof value === 'number')
                                    ? 'min(' + value + 'px, 92vw)' : value;
            // `pre-wrap`, NOT `normal`: the app's messages carry real newlines
            // and HTML collapses them. The transcription notice is written as
            // a lead line, a bulleted problem list and a closing paragraph,
            // and it arrived as one run of prose (macOS, 2026-09-11, Kent:
            // "the newlines (at least) that are present elsewhere are not
            // there"). `pre-wrap` keeps the author's line breaks AND still
            // wraps long lines, which is exactly tkinter's Label contract —
            // `normal` only did the second half.
            el.style.whiteSpace = 'pre-wrap';
            el.style.overflowWrap = 'break-word';
            break;
        case 'font':
            // Remove old font class, add new
            el.className = el.className.replace(/font-\S+/g, '');
            el.classList.add('font-' + value);
            break;
        case 'checked':
            { const cb = el.querySelector('input[type="checkbox"]');
              if (cb) cb.checked = !!value; }
            break;
        case 'items':
            // For listbox: value is an array of strings
            if (el.classList.contains('wv-listbox')) {
                el.innerHTML = '';
                (value || []).forEach((item, i) => {
                    const div = document.createElement('div');
                    div.className = 'wv-listbox-item';
                    div.textContent = item;
                    div.dataset.index = i;
                    div.addEventListener('click', (ev) => {
                        // FOUR MODES, NOT TWO. The first version asked only
                        // "is this multiple?", which is right for tkinter's
                        // MULTIPLE and wrong for EXTENDED: extended is the
                        // file-manager gesture — a plain click REPLACES the
                        // selection, shift-click extends a run from the
                        // anchor, ctrl/cmd-click toggles one row. Treating
                        // it as multiple made every click toggle, so a user
                        // could never narrow a selection back down without
                        // clicking each row off again (Kent, 2026-09-14:
                        // "is this correct for extended?" — it was not).
                        //   single/browse differ only in drag behaviour,
                        // which a click handler cannot express; both replace.
                        const mode = el.dataset.selectmode
                                  || (el.dataset.multiple === 'true'
                                      ? 'multiple' : 'browse');
                        const rows = [...el.querySelectorAll(
                                            '.wv-listbox-item')];
                        const clear = () => rows.forEach(
                                d => d.classList.remove('selected'));
                        if (mode === 'multiple') {
                            div.classList.toggle('selected');
                            el.dataset.anchor = i;
                        } else if (mode === 'extended' && ev.shiftKey) {
                            const a = parseInt(el.dataset.anchor);
                            const from = isNaN(a) ? i : a;
                            clear();
                            rows.slice(Math.min(from, i), Math.max(from, i) + 1)
                                .forEach(d => d.classList.add('selected'));
                        } else if (mode === 'extended'
                                   && (ev.ctrlKey || ev.metaKey)) {
                            div.classList.toggle('selected');
                            el.dataset.anchor = i;
                        } else {
                            clear();
                            div.classList.add('selected');
                            el.dataset.anchor = i;
                        }
                        const chosen = [...el.querySelectorAll(
                                            '.wv-listbox-item.selected')]
                                       .map(d => parseInt(d.dataset.index));
                        if (window.pywebview && window.pywebview.api) {
                            window.pywebview.api.on_event(
                                parseInt(el.dataset.wid), 'select',
                                {index: i, value: item, indices: chosen});
                        }
                    });
                    el.appendChild(div);
                });
            }
            // For combobox: value is an array of strings. Two shapes — the
            // <select>, and the editable state='normal' form, whose options
            // live in a <datalist> beside its <input>.
            { const dl = el.classList.contains('wv-combobox-wrap')
                       ? el.querySelector('datalist') : null;
              const holder = dl || (el.tagName === 'SELECT' ? el : null);
              if (holder) {
                  holder.innerHTML = '';
                  (value || []).forEach(item => {
                      const opt = document.createElement('option');
                      opt.value = item;
                      opt.textContent = item;
                      holder.appendChild(opt);
                  });
              } }
            break;
        case 'value':
            if (el.tagName === 'SELECT') el.value = value;
            if (el.tagName === 'INPUT') el.value = value;
            if (el.classList.contains('wv-combobox-wrap')) {
                const inp = el.querySelector('input');
                if (inp) inp.value = value;
            }
            break;
    }
}

function gridWidget(wid, opts) {
    const el = _widgets.get(wid);
    if (!el) return;
    _applyGrid(el, opts);
    el.classList.remove('wv-hidden');
}

function gridRemove(wid) {
    const el = _widgets.get(wid);
    if (el) el.classList.add('wv-hidden');
}

function destroyWidget(wid) {
    const el = _widgets.get(wid);
    if (el) {
        el.remove();
        _widgets.delete(wid);
    }
}

// tkinter names a specific key; the DOM gives you keydown plus a `key` value.
// Without this, `<Escape>` fell through as a literal event name that can never
// fire — which is why nothing released kiosk mode.
const _keyNames = {
    '<Escape>': 'Escape', '<Return>': 'Enter', '<KP_Enter>': 'Enter',
    '<Tab>': 'Tab', '<space>': ' ', '<BackSpace>': 'Backspace',
    '<Delete>': 'Delete', '<Home>': 'Home', '<End>': 'End',
    '<Prior>': 'PageUp', '<Next>': 'PageDown',
    '<Up>': 'ArrowUp', '<Down>': 'ArrowDown',
    '<Left>': 'ArrowLeft', '<Right>': 'ArrowRight',
    '<F11>': 'F11',
};

function bindEvent(wid, eventName) {
    // A WINDOW IS NOT A DOM WIDGET, so a binding made on a window found no
    // element and was silently dropped — `takekioskscreen()` binds Escape and
    // double-click on the WINDOW to leave fullscreen, so kiosk mode had no
    // exit at all. Window-level bindings belong on the document: in a window,
    // the window is the page, and events from any widget bubble up to it,
    // which is also how tkinter's window-level binds behave.
    const el = _widgets.get(wid) || document;

    // Map tkinter event names to DOM events
    const eventMap = {
        // PRESS IS PRESS. `<ButtonPress-1>` was absent from this map, so it
        // fell through to addEventListener('<ButtonPress-1>') — a listener
        // for an event nothing fires, the same dead end <Button-3> had. The
        // RECORD BUTTON binds press to _start and release to _stop
        // (sound_ui.py:70-71), so under webview recording never STARTED and
        // the release handler then raised on state that start() creates:
        //     no recording to finalise (…wav.tmp was never written)
        //     AttributeError: 'SoundFileRecorder' object has no attribute
        //                     'file_write_OK'
        // (Kent, 2026-09-11.) A press-and-hold control cannot work without
        // this, and recording is the one thing the sound settings window is
        // for.
        //   `<Button-1>` and `<ButtonPress-1>` are SYNONYMS in tkinter, both
        // meaning press, so both map to mousedown. `<Button-1>` was 'click',
        // which fires AFTER mouseup — i.e. after `<ButtonRelease-1>` — so the
        // two ran in the wrong order relative to each other. Anything that
        // wants "activated" uses `command=`, not a press binding.
        '<Button-1>': 'mousedown',
        '<ButtonPress-1>': 'mousedown',
        '<ButtonRelease-1>': 'mouseup',
        '<Double-Button-1>': 'dblclick',
        '<Enter>': 'mouseenter',
        '<Leave>': 'mouseleave',
        '<KeyPress>': 'keydown',
        '<KeyRelease>': 'keyup',
        '<FocusIn>': 'focusin',
        '<FocusOut>': 'focusout',
        '<Configure>': 'resize',
        '<Motion>': 'mousemove',
        // RIGHT AND MIDDLE CLICK, missing until 2026-09-09. Unmapped names
        // fell through to `addEventListener(eventName)` — i.e. a listener for
        // an event literally called "<Button-3>", which nothing ever fires.
        // So every right-click binding was silently dead, including the
        // Transcriber's "Right click to configure" tone-beep window, whose
        // own tooltip advertises it (transcriber.py:188-190).
        '<Button-3>': 'contextmenu',
        '<ButtonRelease-3>': 'contextmenu',
        // tkinter's VIRTUAL context-menu event, which ui_tkinter's
        // ContextMenu binds on the window (and re-points at
        // <Control-Button-1> on Aqua, where there is no Button-3). Unmapped,
        // it registered a listener for an event named "<<ContextMenu>>" —
        // dead the same way Button-3 was before 2026-09-09, which is why the
        // right-click route to Sound Settings did nothing under webview.
        '<<ContextMenu>>': 'contextmenu',
        '<Button-2>': 'auxclick',
        '<ButtonRelease-2>': 'auxclick',
        '<ButtonPress-2>': 'auxclick',
        '<ButtonPress-3>': 'contextmenu',
    };

    const wantedKey = _keyNames[eventName];
    const domEvent = wantedKey ? 'keydown' : (eventMap[eventName] || eventName);
    el.addEventListener(domEvent, (e) => {
        if (wantedKey && e.key !== wantedKey) return;
        // A right-click that opens OUR menu must not also open the engine's.
        if (domEvent === 'contextmenu') e.preventDefault();
        // auxclick covers every non-primary button; only the middle one is
        // tkinter's Button-2.
        if (domEvent === 'auxclick' && e.button !== 1) return;
        if (window.pywebview && window.pywebview.api) {
            window.pywebview.api.on_event(wid, eventName, {
                x: e.clientX, y: e.clientY,
                key: e.key, keyCode: e.keyCode
            });
        }
    });
}

function setThemeVars(vars) {
    // vars: {background, activebackground, ...}
    const root = document.documentElement;
    for (const [key, value] of Object.entries(vars)) {
        root.style.setProperty('--' + key, value);
    }
}

function getWidgetRect(wid) {
    const el = _widgets.get(wid);
    if (!el) return null;
    const r = el.getBoundingClientRect();
    return {x: r.x, y: r.y, width: r.width, height: r.height};
}

function batchCreate(specs) {
    // Create multiple widgets at once for performance
    for (const spec of specs) {
        createWidget(spec);
    }
}

// ── Drag and Drop (HTML5 DnD API) ────────────────────────────────────

let _dragSourceWid = null;

function makeDraggable(wid) {
    const el = _widgets.get(wid);
    if (!el) return;
    el.draggable = true;
    el.style.cursor = 'grab';

    // THE FEEDBACK IS OURS, NOT THE ENGINE'S. WebKitGTK draws a translucent
    // snapshot of the dragged element under the cursor; QtWebEngine draws
    // nothing, so the same page and the same JS looked alive on one engine
    // and dead on the other (Kent, 2026-09-14: "drag drop registers now, but
    // animation is gone from qt (there is gtk)"). A class we set ourselves
    // is drawn by the stylesheet, which both engines do the same way.
    //   Marked by OUTLINE STYLE, not colour — dashed on the thing being
    // dragged, solid on the target it is over (~/.claude-sil/CLAUDE.md:
    // colour may accompany meaning, never carry it). `outline` rather than
    // `border` so nothing reflows when it appears.
    el.addEventListener('dragstart', (e) => {
        _dragSourceWid = wid;
        e.dataTransfer.effectAllowed = 'move';
        e.dataTransfer.setData('text/plain', String(wid));
        el.classList.add('wv-dragging');
        // Notify Python of drag start
        if (window.pywebview && window.pywebview.api) {
            window.pywebview.api.on_event(wid, 'dnd_start', {x: e.clientX, y: e.clientY});
        }
    });

    el.addEventListener('dragend', (e) => {
        el.classList.remove('wv-dragging');
        document.querySelectorAll('.wv-drop-target').forEach(
            d => d.classList.remove('wv-drop-target'));
        _dragSourceWid = null;
        if (window.pywebview && window.pywebview.api) {
            window.pywebview.api.on_event(wid, 'dnd_end', {});
        }
    });
}

function makeDroppable(wid) {
    const el = _widgets.get(wid);
    if (!el) return;

    el.addEventListener('dragover', (e) => {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
    });

    el.addEventListener('dragenter', (e) => {
        e.preventDefault();
        el.classList.add('wv-drop-target');
        if (window.pywebview && window.pywebview.api) {
            window.pywebview.api.on_event(wid, 'dnd_enter', {source_wid: _dragSourceWid});
        }
    });

    el.addEventListener('dragleave', (e) => {
        el.classList.remove('wv-drop-target');
        if (window.pywebview && window.pywebview.api) {
            window.pywebview.api.on_event(wid, 'dnd_leave', {source_wid: _dragSourceWid});
        }
    });

    el.addEventListener('drop', (e) => {
        e.preventDefault();
        el.classList.remove('wv-drop-target');
        const sourceWid = parseInt(e.dataTransfer.getData('text/plain'));
        if (window.pywebview && window.pywebview.api) {
            window.pywebview.api.on_event(wid, 'dnd_commit', {
                source_wid: sourceWid,
                x: e.clientX, y: e.clientY
            });
        }
    });
}
