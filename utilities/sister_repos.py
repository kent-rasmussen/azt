#!/usr/bin/env python3
# coding=UTF-8
"""Sister-repo management — THE one principled mechanism.

azt expects certain repos cloned BESIDE its own clone (same parent
directory), some of them reached in-app through an in-repo symlink (or,
on Windows, a directory junction). This module owns the table of those
repos and all the mechanics; everything else delegates here:

- ``utilities/py_modules.py`` runs ``ensure_all()`` at every start;
- ``images/to_select_update.py`` and ``lift_templates/SILCAWL_update.py``
  are thin CLI/back-compat wrappers over ``ensure()``/``update()``;
- ``backend/core/collab.py::_ensure_client_importable`` remains the
  RUNTIME import shim for the collab client (sys.path wiring) — this
  module only guarantees there is something for it to find.

Principles:
- never block or kill startup — every failure path logs and returns
  False (azt degrades gracefully without each of these repos);
- never delete or overwrite anything this run didn't just create;
- no network when the repo is already reachable locally (dev symlink,
  pip install, env var, existing clone);
- symlink where possible, Windows directory junction where symlinks
  need Developer Mode.
"""
import os
import shutil
import subprocess
import sys

from utilities import logsetup
log = logsetup.getlog(__name__)
from utilities.i18n import _


def azt_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def suite_root():
    return os.path.dirname(azt_root())


REPOS = {
    'azt-collab': dict(
        url='https://github.com/kent-rasmussen/azt-collab.git',
        # proves a directory is (enough of) this repo:
        marker=os.path.join('azt_collab_client', '__init__.py'),
        importable='azt_collab_client',  # dev symlink or pip install
        env='AZT_COLLAB_DIR',
        altdirs=['azt_collab'],
        link=None,  # runtime sys.path wiring is backend/core/collab.py's job
        timeout=600,
    ),
    'images_CAWL': dict(
        url='https://github.com/kent-rasmussen/images_CAWL.git',
        marker=None,  # any non-empty clone will do
        link=('images', 'toselect'),
        timeout=3600,
        size_note=_("(the CAWL image set is a few hundred MB; the first "
                    "clone can take a while)"),
    ),
    'lift_templates': dict(
        url='https://github.com/kent-rasmussen/lift_templates.git',
        marker='SILCAWL.lift',
        link=('lift_templates', 'SILCAWL'),
        timeout=600,
    ),
}


def _has_marker(directory, marker):
    if not os.path.isdir(directory):
        return False
    if marker:
        return os.path.exists(os.path.join(directory, marker))
    return bool(os.listdir(directory))


def _candidates(name, spec):
    """Where an existing clone may legitimately live, in lookup order."""
    dirs = []
    env = spec.get('env')
    if env and os.environ.get(env):
        dirs.append(os.environ[env])
    dirs.append(os.path.join(suite_root(), name))
    for alt in spec.get('altdirs', []):
        dirs.append(os.path.join(suite_root(), alt))
    return dirs


def linkpath(spec):
    link = spec.get('link')
    if not link:
        return None
    return os.path.join(azt_root(), *link)


def available(name, spec=None):
    """True when the repo is reachable the way the app reads it: through
    its in-repo link if it has one, else importable or found by marker."""
    spec = spec or REPOS[name]
    lp = linkpath(spec)
    if lp:
        return os.path.isdir(lp)  # follows symlinks/junctions
    imp = spec.get('importable')
    if imp:
        try:
            __import__(imp)
            return True
        except ImportError:
            pass
    return any(_has_marker(c, spec.get('marker'))
               for c in _candidates(name, spec))


def _make_link(target, lp):
    """Point lp at target: relative symlink, or a directory junction on
    Windows (no privilege needed, unlike symlinks without Developer Mode)."""
    parent = os.path.dirname(lp)
    rel = os.path.relpath(target, parent)
    if os.path.islink(lp):
        if os.readlink(lp) == rel:
            return True
        log.info(_("Fixing link {link} (was {old}, now {new})").format(
                    link=lp, old=os.readlink(lp), new=rel))
        os.remove(lp)
    elif os.path.isdir(lp):
        log.warning(_("{link} is a real directory, not a link; not touching "
                    "it. Move it aside (or fix it) and restart.").format(
                        link=lp))
        return False
    elif os.path.exists(lp):
        os.remove(lp)
    try:
        os.symlink(rel, lp)
        log.info(_("Linked {link} -> {target}").format(link=lp, target=rel))
    except OSError:
        if sys.platform != 'win32':
            raise
        subprocess.check_call(['cmd', '/c', 'mklink', '/J', lp,
                               os.path.abspath(target)])
        log.info(_("Junctioned {link} -> {target}").format(
                    link=lp, target=target))
    return True


def ensure(name):
    """Make REPOS[name] available (clone and/or link as needed). Every
    failure path logs and returns False; never raises."""
    spec = REPOS[name]
    try:
        if available(name, spec):
            return True
        target = None  # an existing clone, else make one
        for c in _candidates(name, spec):
            if _has_marker(c, spec.get('marker')):
                target = c
                break
        if target is None:
            dest = os.path.join(suite_root(), name)
            if os.path.exists(dest):
                log.warning(_("{dest} exists but doesn’t look like {name}; "
                            "not touching it. Move it aside (or fix it) and "
                            "restart.").format(dest=dest, name=name))
                return False
            git = shutil.which('git')
            if not git:
                log.info(_("No git executable found; can’t fetch {name}."
                            "").format(name=name))
                return False
            log.info(_("{name} not found; cloning {url} to {dest}...").format(
                        name=name, url=spec['url'], dest=dest))
            if spec.get('size_note'):
                log.info(spec['size_note'])
            subprocess.check_call([git, 'clone', spec['url'], dest],
                                  timeout=spec.get('timeout', 600))
            target = dest
        lp = linkpath(spec)
        if lp:
            return _make_link(target, lp)
        return True
    except subprocess.TimeoutExpired:
        log.info(_("Fetching {name} timed out; will try again next start."
                    "").format(name=name))
    except Exception as e:
        log.info(_("Couldn’t set up {name} ({error}); maybe no internet? "
                    "Will try again next start.").format(name=name, error=e))
    return False


def update(name):
    """git pull an existing sister clone (CLI/maintenance use — ensure()
    deliberately never pulls at boot), then ensure availability. A failed
    pull is logged and does NOT prevent linking the existing clone."""
    spec = REPOS[name]
    for c in _candidates(name, spec):
        if os.path.isdir(os.path.join(c, '.git')):
            log.info(_("Updating {dir}...").format(dir=c))
            try:
                subprocess.check_call([shutil.which('git') or 'git',
                                       '-C', c, 'pull'],
                                      timeout=spec.get('timeout', 600))
            except Exception as e:
                log.info(_("Pull failed ({error}); continuing with the "
                            "existing clone.").format(error=e))
            break
    return ensure(name)


def ensure_all():
    """Ensure every sister repo; returns {name: ok}."""
    return {name: ensure(name) for name in REPOS}
