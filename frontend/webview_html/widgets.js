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

    if (hasN && hasS) style.alignSelf = 'stretch';
    else if (hasN)    style.alignSelf = 'start';
    else if (hasS)    style.alignSelf = 'end';

    if (hasE && hasW) style.justifySelf = 'stretch';
    else if (hasE)    style.justifySelf = 'end';
    else if (hasW)    style.justifySelf = 'start';

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
            break;
        case 'label':
            el = document.createElement('div');
            el.className = 'wv-widget wv-label';
            if (spec.props.text) el.textContent = spec.props.text;
            if (spec.props.font) el.classList.add('font-' + spec.props.font);
            if (spec.props.image) _setImage(el, spec.props.image, spec.props.compound);
            break;
        case 'button':
            el = document.createElement('button');
            el.className = 'wv-widget wv-button';
            if (spec.props.text) el.textContent = spec.props.text;
            if (spec.props.font) el.classList.add('font-' + spec.props.font);
            if (spec.props.image) _setImage(el, spec.props.image, spec.props.compound);
            if (spec.props.disabled) el.disabled = true;
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
            break;
        case 'checkbutton': {
            el = document.createElement('label');
            el.className = 'wv-widget wv-checkbutton';
            const cb = document.createElement('input');
            cb.type = 'checkbox';
            cb.checked = !!spec.props.checked;
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
            // Items added via updateProp('items', [...])
            break;
        }
        case 'combobox': {
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

    el.dataset.wid = spec.wid;
    _widgets.set(spec.wid, el);

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

// ── Images on labels and buttons ─────────────────────────────────────
// Both used to DISCARD `image` (ui_webview popped it and never sent it), so
// the chooser rendered as text-only buttons where the app shows icons.
// `compound` mirrors tkinter's: where the image sits relative to the text.
function _setImage(el, src, compound) {
    const img = document.createElement('img');
    img.className = 'wv-img';
    img.src = src;
    img.alt = '';
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

    // First tab added is the selected one, as ttk does.
    if (p.strip.children.length === 1) notebookSelect(wid, childWid, false);
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
            if (el.tagName === 'BUTTON') el.disabled = (value === 'disabled');
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
            if (fill) fill.style.width = value + '%';
            break;
        case 'width':
            el.style.width = value + 'ch';
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
            el.style.maxWidth = (typeof value === 'number')
                                    ? value + 'px' : value;
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
                    div.addEventListener('click', () => {
                        el.querySelectorAll('.wv-listbox-item').forEach(d => d.classList.remove('selected'));
                        div.classList.add('selected');
                        if (window.pywebview && window.pywebview.api) {
                            window.pywebview.api.on_event(parseInt(el.dataset.wid), 'select', {index: i, value: item});
                        }
                    });
                    el.appendChild(div);
                });
            }
            // For combobox: value is an array of strings
            if (el.tagName === 'SELECT') {
                el.innerHTML = '';
                (value || []).forEach(item => {
                    const opt = document.createElement('option');
                    opt.value = item;
                    opt.textContent = item;
                    el.appendChild(opt);
                });
            }
            break;
        case 'value':
            if (el.tagName === 'SELECT') el.value = value;
            if (el.tagName === 'INPUT') el.value = value;
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
        '<Button-1>': 'click',
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
        '<Button-2>': 'auxclick',
        '<ButtonRelease-2>': 'auxclick',
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

    el.addEventListener('dragstart', (e) => {
        _dragSourceWid = wid;
        e.dataTransfer.effectAllowed = 'move';
        e.dataTransfer.setData('text/plain', String(wid));
        el.style.opacity = '0.5';
        // Notify Python of drag start
        if (window.pywebview && window.pywebview.api) {
            window.pywebview.api.on_event(wid, 'dnd_start', {x: e.clientX, y: e.clientY});
        }
    });

    el.addEventListener('dragend', (e) => {
        el.style.opacity = '1';
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
        el.style.background = 'var(--activebackground)';
        if (window.pywebview && window.pywebview.api) {
            window.pywebview.api.on_event(wid, 'dnd_enter', {source_wid: _dragSourceWid});
        }
    });

    el.addEventListener('dragleave', (e) => {
        el.style.background = '';
        if (window.pywebview && window.pywebview.api) {
            window.pywebview.api.on_event(wid, 'dnd_leave', {source_wid: _dragSourceWid});
        }
    });

    el.addEventListener('drop', (e) => {
        e.preventDefault();
        el.style.background = '';
        const sourceWid = parseInt(e.dataTransfer.getData('text/plain'));
        if (window.pywebview && window.pywebview.api) {
            window.pywebview.api.on_event(wid, 'dnd_commit', {
                source_wid: sourceWid,
                x: e.clientX, y: e.clientY
            });
        }
    });
}
