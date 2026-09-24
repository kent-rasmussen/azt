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


def _git_noninteractive():
    """Environment for rollout git runs: no terminal is attached (and the
    caller may be on the UI thread), so any credential/passphrase prompt
    must fail immediately — surfacing as 'pull-failed' — rather than hang
    the subprocess until its timeout."""
    env = dict(os.environ)
    env['GIT_TERMINAL_PROMPT'] = '0'
    env.setdefault('GIT_SSH_COMMAND', 'ssh -oBatchMode=yes')
    return env


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


def _is_link(path):
    """Is `path` a link of any kind — including a Windows JUNCTION?

    WE MAKE JUNCTIONS AND THEN CANNOT SEE THEM. `_make_link` falls back to
    `mklink /J` on Windows, because a real symlink there needs Developer Mode
    or admin. But `os.path.islink()` is False for a junction: it is a reparse
    point, not a symlink. So every start found our own link, judged it "a real
    directory, not a link", and warned the user to move it aside — about
    something that was exactly what we had created (Kim, Windows,
    2026-09-24, with `ls -l` showing the link plainly).

    `os.path.isjunction` would answer this directly but arrived in 3.12, and
    ADR 0005 puts our floor at 3.10, so the reparse-point attribute is the
    fallback. It has been on `os.lstat` results since 3.8."""
    if os.path.islink(path):
        return True
    isjunction = getattr(os.path, 'isjunction', None)   # 3.12+
    if isjunction is not None:
        try:
            if isjunction(path):
                return True
        except OSError:
            pass
    try:
        return bool(getattr(os.lstat(path), 'st_reparse_tag', 0))
    except OSError:
        return False


def _link_target(path):
    """Where a link points, for a log line. `os.readlink` handles junctions
    on Windows too; anything it refuses is reported as unknown."""
    try:
        return os.readlink(path)
    except OSError:
        return '?'


def _remove_link(path):
    """Delete a link without following it. A junction is a DIRECTORY entry, so
    `os.remove` refuses it on Windows and `os.rmdir` is the one that works —
    and it removes only the link, never what it points at."""
    try:
        os.remove(path)
    except OSError:
        os.rmdir(path)


def _make_link(target, lp):
    """Point lp at target: relative symlink, or a directory junction on
    Windows (no privilege needed, unlike symlinks without Developer Mode)."""
    parent = os.path.dirname(lp)
    # A MISSING PARENT IS A BROKEN CHECKOUT, AND MUST NOT BE PAPERED OVER.
    # Every link we make lives INSIDE a tracked directory of this repo —
    # `lift_templates/SILCAWL` sits beside `lift_templates/__init__.py`, and
    # `images/toselect` beside the images. Only the link itself is
    # gitignored. So the parent is git's to deliver, and its absence means the
    # working copy is incomplete (Kent, 2026-09-24: "lift_templates isn't the
    # repo link, l_t/SILCAWL is").
    #   Creating it was my first fix and it was wrong: `mklink` would then
    # succeed while `import lift_templates` still failed, because the tracked
    # `__init__.py` is gone too — trading a clear error for a confusing one.
    # Say what is actually wrong instead.
    if parent and not os.path.isdir(parent):
        log.error(_("{dir} is missing. That directory is part of A-Z+T "
                    "itself, not something we fetch, so this working copy is "
                    "incomplete — check the branch and whether the files "
                    "arrived. Nothing can be linked into it until it is "
                    "back.").format(dir=parent))
        return False
    rel = os.path.relpath(target, parent)
    if _is_link(lp):
        # SAME PLACE? compare resolved paths, not the stored text. A junction
        # stores an ABSOLUTE target while a symlink here stores a RELATIVE
        # one, so `os.readlink(lp) == rel` is false for every junction we
        # made ourselves, and the link was replaced on every start.
        try:
            same = os.path.realpath(lp) == os.path.realpath(
                os.path.join(parent, rel))
        except OSError:
            same = False
        if same:
            return True
        log.info(_("Fixing link {link} (was {old}, now {new})").format(
                    link=lp, old=_link_target(lp), new=rel))
        _remove_link(lp)
    elif os.path.isdir(lp):
        # ASK WHETHER IT CAN BE UPDATED, NOT WHETHER IT IS A LINK. Kent,
        # 2026-09-24: *"Does it matter if windows treats it as a link? the
        # point was that this directory is a copy of a repo being maintained
        # outside this repo."* Quite so. A link is one mechanism for reaching
        # the managed clone; what the user loses by not having one is UPDATES.
        # So test for the thing we actually care about.
        #   This matters on Windows specifically, because Git Bash prints
        # `lrwxrwxrwx` for its own "symlinks" while MSYS may have made a copy
        # or a .lnk that Windows does not treat as a link at all. Judging by
        # linkness there produced a warning that contradicted what the user
        # could plainly see (Kim, same day), and judged the wrong property
        # besides.
        resolved = os.path.realpath(lp)
        if resolved == os.path.realpath(target):
            # It resolves to the managed clone by SOME mechanism — a native
            # symlink, a junction, an MSYS shortcut. Invisible to us, and
            # entirely fine: updates land here because this IS there.
            log.info(_("{link} already resolves to {target}; leaving it."
                       "").format(link=lp, target=target))
            return True
        if os.path.isdir(os.path.join(resolved, '.git')):
            log.info(_("{link} is its own clone rather than the managed one. "
                       "It can still be updated, just not by us; leaving it "
                       "alone.").format(link=lp))
            return True
        log.warning(_("{link} is a detached copy — not the managed clone and "
                    "not a repository, so NOTHING WILL EVER UPDATE IT. It "
                    "works today and will silently fall behind. Move it aside "
                    "and restart to have it managed.").format(link=lp))
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


def ensure_detail(name):
    """Make REPOS[name] available (clone and/or link as needed), and say HOW.

    Returns ``(ok, how)`` where how is one of:
      ``'present'``  already available; nothing was found to manage and nothing
                     was done — see the warning below, this is the state that
                     looks fine and can never be updated;
      ``'linked'``   an existing clone was found and linked; nothing fetched;
      ``'cloned'``   no clone existed, so one was fetched;
      ``''``         failed (every failure path logs and returns False).

    The distinction exists because `update()` collapsed all three into the code
    `installed`, whose docstring claimed "no clone existed; ensure() fetched
    one" — which was FALSE, and misleadingly so: a fresh copy reported
    `images_CAWL: newly installed` having cloned nothing at all (Kent,
    2026-09-01). Callers drive display and logic off that code, so it has to
    mean what it says.

    Never raises."""
    spec = REPOS[name]
    try:
        if available(name, spec):
            lp = linkpath(spec)
            if lp and os.path.isdir(lp) and not os.path.islink(lp):
                # THE SILENT STATE. `available()` is satisfied by a populated
                # real directory at the link path, so we return here — before
                # _make_link, whose warning for exactly this case is therefore
                # unreachable. The pictures work, so nothing looks wrong; but
                # there is no clone to pull, so this repo can never be updated
                # and `update()` will keep reporting success. Seen on a copy
                # made with cp -r, which dereferenced the symlink into ~1700
                # real files (Kent, 2026-09-01).
                log.warning(_("{link} is a real directory, not a link to a "
                            "managed clone of {name}. It works, but {name} can "
                            "never be updated this way. Move it aside and "
                            "restart to have {name} managed properly."
                            ).format(link=lp, name=name))
            return True, 'present'
        target = None  # an existing clone, else make one
        for c in _candidates(name, spec):
            if _has_marker(c, spec.get('marker')):
                target = c
                break
        how = 'linked'
        if target is None:
            dest = os.path.join(suite_root(), name)
            if os.path.exists(dest):
                log.warning(_("{dest} exists but doesn’t look like {name}; "
                            "not touching it. Move it aside (or fix it) and "
                            "restart.").format(dest=dest, name=name))
                return False, ''
            git = shutil.which('git')
            if not git:
                log.info(_("No git executable found; can’t fetch {name}."
                            "").format(name=name))
                return False
            log.info(_("{name} not found; cloning {url} to {dest}...").format(
                        name=name, url=spec['url'], dest=dest))
            if spec.get('size_note'):
                log.info(spec['size_note'])
            # SHALLOW BY DEFAULT (Kent 2026-09-01: "all our cloning should be
            # shallow clones. we don't need history for any users"). These are
            # rollout assets, not anybody's work: nothing here reads history,
            # `update()` only ever `pull --ff-only`s the tip, and images_CAWL is
            # a few hundred MB, so depth 1 is the difference between a usable
            # first run and a long one on a field connection.
            #
            # NB --depth implies --single-branch, so a shallow clone has ONE
            # remote-tracking branch. That is fine for these three (no caller
            # switches their branches) but would NOT be for the azt source
            # clone, where `hard_checkout` names origin/<branch> explicitly and
            # "try the testing version" would break. Per-repo `depth` override
            # (set it to 0 or None for a full clone) so that distinction stays
            # visible in the table rather than being rediscovered later.
            args = [git, 'clone']
            depth = spec.get('depth', 1)
            if depth:
                args += ['--depth', str(depth)]
            args += [spec['url'], dest]
            subprocess.check_call(args,
                                  stdin=subprocess.DEVNULL,
                                  env=_git_noninteractive(),
                                  timeout=spec.get('timeout', 600))
            target = dest
        lp = linkpath(spec)
        if lp:
            return _make_link(target, lp), how
        return True, how
    except subprocess.TimeoutExpired:
        log.info(_("Fetching {name} timed out; will try again next start."
                    "").format(name=name))
    except Exception as e:
        # DON'T BLAME THE NETWORK FOR EVERYTHING. This said "maybe no
        # internet?" for any failure at all, and on Kim's Windows machine the
        # actual fault was a MISSING LOCAL DIRECTORY — `mklink` reporting "The
        # system cannot find the path specified" because `lift_templates\` was
        # not in her checkout. Nothing had touched the network. The guess sent
        # two people looking at cloning and connectivity for a folder that was
        # simply absent (2026-09-24).
        #   Only the steps that actually reach out get the network guess; a
        # link failure is local by definition.
        network = not isinstance(e, (OSError, subprocess.CalledProcessError)) \
            or 'clone' in str(e) or 'fetch' in str(e)
        log.info(_("Couldn’t set up {name}: {error}.{guess} Will try again "
                    "next start.").format(
                        name=name, error=e,
                        guess=_(" Maybe no internet?") if network else ''))
    return False, ''


def ensure(name):
    """Availability as a plain bool — what almost every caller wants
    (``py_modules.ensure_sister_repos``, and the ``ensure_available()``
    wrappers in ``images/to_select_update.py`` and
    ``lift_templates/SILCAWL_update.py``). Use ``ensure_detail`` when you need
    to know HOW it became available."""
    return ensure_detail(name)[0]


def update(name):
    """git pull an existing sister clone (ensure() deliberately never
    pulls at boot), then ensure availability. A failed pull is logged
    and does NOT prevent linking the existing clone.

    Returns ``(ok, code, output)``: ``ok`` is availability after the
    attempt; ``code`` is one of ``'updated'`` / ``'current'`` /
    ``'pull-failed'`` / ``'installed'`` (no clone existed; ensure()
    fetched one) / ``'missing'`` — drive logic off the code, never off
    ``output`` (raw git text / error, display only). ``--ff-only``
    because rollout clones must never grow local merge state; a
    diverged clone surfaces as ``pull-failed`` for a human to look at."""
    spec = REPOS[name]
    code, output = '', ''
    for c in _candidates(name, spec):
        if os.path.isdir(os.path.join(c, '.git')):
            log.info(_("Updating {dir}...").format(dir=c))
            try:
                r = subprocess.run([shutil.which('git') or 'git',
                                    '-C', c, 'pull', '--ff-only'],
                                   capture_output=True, text=True,
                                   stdin=subprocess.DEVNULL,
                                   env=_git_noninteractive(),
                                   timeout=spec.get('timeout', 600))
                output = ((r.stdout or '') + (r.stderr or '')).strip()
                if r.returncode != 0:
                    code = 'pull-failed'
                    log.info(_("Pull failed ({error}); continuing with "
                                "the existing clone.").format(error=output))
                elif 'Already up to date' in output \
                        or 'Already up-to-date' in output:
                    code = 'current'
                else:
                    code = 'updated'
            except Exception as e:
                code, output = 'pull-failed', str(e)
                log.info(_("Pull failed ({error}); continuing with the "
                            "existing clone.").format(error=e))
            break
    ok, how = ensure_detail(name)
    if not code:
        # `installed` now means CLONED, which is what its docstring always
        # claimed. It used to be returned for anything that ended up available
        # without a pull, so a copy whose images sat in a plain directory
        # reported "newly installed" having fetched nothing (Kent, 2026-09-01).
        code = {'cloned': 'installed',
                'linked': 'linked',
                'present': 'present'}.get(how, 'missing' if not ok else 'present')
    return ok, code, output


def describe(code):
    """Translated one-phrase summary of an update() code, for display."""
    return {
        'linked': _("found on this computer and linked (not downloaded)"),
        'present': _("already in place (not a managed copy, so it can’t be "
                    "updated)"),
        'updated': _("updated (restart to use)"),
        'current': _("already up to date"),
        'pull-failed': _("could not update; keeping the current copy"),
        'installed': _("newly installed"),
        'missing': _("not available (no internet?)"),
    }.get(code, code)


def update_all():
    """Update every sister repo (git pull + ensure); the in-app update
    flow (``main.App.updateazt``) runs this so machines that never touch a
    shell — Windows field laptops — still get server/client updates.
    Returns ``{name: (ok, code, output)}``."""
    return {name: update(name) for name in REPOS}


def ensure_all():
    """Ensure every sister repo; returns {name: ok}."""
    return {name: ensure(name) for name in REPOS}
