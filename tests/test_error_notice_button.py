"""An ErrorNotice's action button is a command, so it works under webview.

It used to be three '<ButtonRelease>' bindings; under webview that event
never fired, so "Use this folder for collaboration" was drawn and did
nothing (Kent, 2026-10-13: "there, but nonfunctional").
"""
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]


def test_no_bare_buttonrelease_binding_on_the_action_button():
    code = [l.split('#', 1)[0] for l in
            (ROOT / 'frontend/error_notice.py').read_text(
                encoding='utf-8').splitlines()]
    text = '\n'.join(code)
    assert "bind('<ButtonRelease>'" not in text
    assert 'cmd=_act' in text
