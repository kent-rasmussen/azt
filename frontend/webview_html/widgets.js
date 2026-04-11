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
    let el;
    const parentEl = spec.parent_wid != null ? _widgets.get(spec.parent_wid) : document.getElementById('root');

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
            break;
        case 'button':
            el = document.createElement('button');
            el.className = 'wv-widget wv-button';
            if (spec.props.text) el.textContent = spec.props.text;
            if (spec.props.font) el.classList.add('font-' + spec.props.font);
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
        case 'font':
            // Remove old font class, add new
            el.className = el.className.replace(/font-\S+/g, '');
            el.classList.add('font-' + value);
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

function bindEvent(wid, eventName) {
    const el = _widgets.get(wid);
    if (!el) return;

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
    };

    const domEvent = eventMap[eventName] || eventName;
    el.addEventListener(domEvent, (e) => {
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
