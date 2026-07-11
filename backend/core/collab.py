"""Collab-daemon integration for desktop A-Z+T (strangler seam).

This module is the ONLY azt code that talks to ``azt_collab_client``.
Everything is gated on a per-project opt-in (``collab: true`` in the
project settings domain, set by ``connect_current_project``); when the
flag is off — or the client package / daemon is unavailable — every
entry point degrades to "legacy path, untouched" so a non-connected
project cannot be affected by any of this.

Contract: azt-collab/azt_collab_client/CLIENT_INTEGRATION.md § 8b
(whole-file editor). Plan: azt/agenda/azt_run_with_server.md.

Wiring (all in place as of Phase 2):
- ``attach(program)`` from ``main._run_setup`` right after FileParser —
  creates the session and hooks ``db.collab_submit`` when opted in.
- ``Lift.write()`` hands its ``.part`` file to ``session.submit`` in
  collab mode instead of doing its own ``os.replace`` + repo_commit.
- ``main.repocheck`` / ``repo_commit`` and the shutdown ``share()``
  loop branch on ``program.collab``.

How ``azt_collab_client`` is found (in order; see
``_ensure_client_importable``): a plain import (covers the dev
symlink at the repo root and any future pip install), the
``AZT_COLLAB_DIR`` env var, then an ``azt-collab``/``azt_collab``
clone beside the azt repo. The committed symlink is a developer
convenience only — Windows checkouts without Developer Mode turn git
symlinks into plain text files, so it must never be load-bearing.
azt itself must never import ``azt_collabd``; daemon *subprocesses*
(auto-spawn, picker, settings UI) find it via the client's
``_spawn.build_spawn_env``, which derives the path from wherever the
client package was imported from — so the sys.path insertion below
serves both processes at once.
"""

import os
import subprocess
import sys

from utilities import logsetup
log = logsetup.getlog(__name__)
from utilities.i18n import _

# Belt-and-braces: if anything in the client's dependency graph ever
# imports Kivy inside this (tkinter) process, keep Kivy's import-time
# argv parser from eating azt's own flags (e.g. --restart → "Core:
# option --restart not recognized" + hard exit, seen 2026-07-07) and
# keep its log handlers quiet. The real fix is that the client is
# Kivy-free on desktop paths since 0.53.1 (_platform.py); these
# defaults make any regression harmless instead of fatal.
os.environ.setdefault('KIVY_NO_ARGS', '1')
os.environ.setdefault('KIVY_NO_FILELOG', '1')
os.environ.setdefault('KIVY_NO_CONSOLELOG', '1')


def _ensure_client_importable():
    """Make ``azt_collab_client`` importable without relying on the
    dev symlink (per the module docstring). Returns True when the
    package can be imported. On fallback success the azt-collab
    ROOT goes onto sys.path, which also lets the client's
    ``build_spawn_env`` hand daemon subprocesses an importable
    ``azt_collabd``."""
    try:
        import azt_collab_client  # noqa: F401 — symlink or pip
        return True
    except ImportError:
        pass
    candidates = []
    env_dir = os.environ.get('AZT_COLLAB_DIR', '')
    if env_dir:
        candidates.append(env_dir)
    azt_root = os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))))
    suite_root = os.path.dirname(azt_root)
    candidates += [os.path.join(suite_root, 'azt-collab'),
                   os.path.join(suite_root, 'azt_collab')]
    for c in candidates:
        if not os.path.isfile(os.path.join(
                c, 'azt_collab_client', '__init__.py')):
            continue
        if c not in sys.path:
            sys.path.insert(0, c)
        try:
            import azt_collab_client  # noqa: F401
        except ImportError as e:
            log.warning(f"azt_collab_client found at {c} but failed "
                        f"to import: {e}")
            continue
        log.info(f"azt_collab_client located via fallback at {c}")
        return True
    log.info(_(
        "azt_collab_client not found (no symlink, no clone beside "
        "the azt folder, AZT_COLLAB_DIR unset) — collaboration "
        "features unavailable; clone azt-collab beside azt or set "
        "AZT_COLLAB_DIR."))
    return False


if _ensure_client_importable():
    import azt_collab_client as _client
    from azt_collab_client import status as S
    AVAILABLE = True
else:
    _client = None
    S = None
    AVAILABLE = False


def _settings_mgr(lift_filename):
    import settings as _settings_pkg
    return _settings_pkg.SettingsManager(lift_filename)


def _git_config(working_dir, key):
    """Read a git config value the way legacy vcs.py sources the
    commit author. Empty string when git/absent/unset."""
    try:
        out = subprocess.check_output(
            ['git', '-C', working_dir, 'config', '--get', key],
            stderr=subprocess.DEVNULL)
        return out.decode('utf-8', 'replace').strip()
    except Exception:
        return ''


def _git_remote_urls(working_dir):
    try:
        out = subprocess.check_output(
            ['git', '-C', working_dir, 'config', '--get-regexp',
             r'remote\..*\.url'],
            stderr=subprocess.DEVNULL).decode('utf-8', 'replace')
    except Exception:
        return []
    urls = []
    for line in out.splitlines():
        parts = line.split(None, 1)
        if len(parts) == 2:
            urls.append(parts[1].strip())
    return urls


def _is_internet_url(url):
    return url.startswith(('http://', 'https://', 'git@', 'ssh://'))


class CollabSession:
    """One connected project's live state: the daemon langcode and the
    base ``head_sha`` every save is declared against. Created by
    ``attach``; owned as ``program.collab``."""

    def __init__(self, program, langcode, base_sha, lift_path=''):
        self.program = program
        self.langcode = langcode
        self.base_sha = base_sha or ''
        self.lift_path = lift_path or ''
        self.stale = False       # a MERGED_WITH_LOCAL arrived; in-memory
        #                          model is behind the on-disk merge.
        self.degraded = False    # daemon failed mid-session; direct
        #                          writes are landing (legacy-identical).
        self.lift_stat = None    # (mtime_ns, size) of the LIFT as last
        #                          written/loaded by US — the cheap "did
        #                          someone else change the file" probe.
        self.base_lift_blob = ''  # LIFT blob SHA (git) at our base_sha,
        #                          learned from project_status whenever
        #                          base==head — the content-identity
        #                          anchor that lets a stale latch heal
        #                          (F2): HEAD's LIFT blob == this ⇒ the
        #                          advance changed no LIFT we can't see.
        self._warned_uncommitted = False
        self._reload_offered_at = 0.0
        self._last_detected_head = ''  # newest peer head we've seen
        self._offered_head = ''        # head the last dialog was for
        self._sync_in_flight = False   # user-gesture sync guard (§17c)

    def record_lift_stat(self):
        """Remember the on-disk identity of the LIFT as of our last
        load/write, so the poll can tell a foreign content change from
        a HEAD advance that didn't touch the LIFT (artifact commits)."""
        try:
            st = os.stat(self.lift_path)
            self.lift_stat = (st.st_mtime_ns, st.st_size)
        except OSError:
            self.lift_stat = None

    def _lift_changed_on_disk(self):
        try:
            st = os.stat(self.lift_path)
        except OSError:
            return False
        return (st.st_mtime_ns, st.st_size) != self.lift_stat

    # ── the write seam ────────────────────────────────────────────────

    def submit(self, filename, staged):
        """Hand a fully-serialized staged sibling file to the daemon
        (base-aware). Returns ``'ok'`` (bytes landed; caller must NOT
        replace) or ``'fallback'`` (caller should do its legacy
        ``os.replace`` of *staged* itself)."""
        rel = os.path.basename(str(filename))
        result = _client.submit_file(
            self.langcode, rel, str(staged), self.base_sha)
        if result.has(S.MERGED_WITH_LOCAL):
            # Peer changes were merged with this save — nothing lost,
            # but our in-memory tree no longer matches disk. The base
            # deliberately does NOT advance to the merge commit: our
            # in-memory tree still derives from the OLD base, and
            # advancing would make the next save fast-path replace the
            # merged file, content-clobbering the peer changes. Keeping
            # the old base makes every subsequent save re-merge against
            # it — peer changes live in "ours" (HEAD) and survive each
            # round — until the reload resets the session.
            self.stale = True
            self._last_detected_head = result.head_sha or self.base_sha
            self.record_lift_stat()
            n = result.param(S.MERGED_WITH_LOCAL, 'n_conflicts', 0)
            log.warning(_(
                "Teammates’ changes were merged with your last save "
                "({n} conflict(s) annotated). Reload to see them; "
                "saving remains safe meanwhile.").format(n=n))
            return 'ok'
        if result.has(S.COMMITTED_LOCAL):
            self.base_sha = result.head_sha or self.base_sha
            self.degraded = False
            self.record_lift_stat()
            return 'ok'
        if result.has(S.CONTRIBUTOR_UNSET):
            self.record_lift_stat()
            # The daemon landed the bytes but refused the commit until
            # a contributor name is set. Durable, so the save is OK.
            if not self._warned_uncommitted:
                self._warned_uncommitted = True
                log.warning(_(
                    "Saves are not entering project history because "
                    "no contributor name is set for collaboration; "
                    "set one in the collaboration settings."))
            return 'ok'
        # SERVER_UNAVAILABLE / SERVER_ERROR / BUSY / COMMIT_FAILED /
        # 'not_found' (daemon predates submit_file). If the staged file
        # is GONE the daemon consumed it before failing (e.g. replace
        # succeeded, commit blew up) — the bytes are on disk, so the
        # save is OK; a legacy replace would find no source and report
        # a false write failure.
        if not os.path.exists(str(staged)):
            # The daemon consumed the staged file (os.replace succeeded)
            # then failed to commit: the DEST LIFT now holds OUR bytes.
            # Record its stat so the poll recognises the eventual HEAD
            # advance (when the commit catches up) as OUR content, not a
            # peer change — omitting this was the root of the spurious
            # "Team changes available" popup (F1).
            self.record_lift_stat()
            log.warning(_(
                "Collaboration server reported a problem after "
                "storing the file ({codes}); save is safe, history "
                "may catch up on the next save.").format(
                    codes=result.codes()))
            # F5: the client wrapper preserves the daemon's exception
            # text as Status('SERVER_ERROR', {'error': str(ex)}); log
            # it too — codes() alone discarded the root cause of the
            # persistent submit_file failure on both incidents.
            detail = result.param('SERVER_ERROR', 'error', '')
            if detail:
                log.warning(_(
                    "Collaboration server error detail: {detail}"
                    ).format(detail=detail))
            return 'ok'
        if not self.degraded:
            self.degraded = True
            log.warning(_(
                "Collaboration server unavailable ({codes}); saving "
                "directly to disk (legacy mode) until it returns."
                ).format(codes=result.codes()))
        return 'fallback'

    def adopt_reloaded_db(self):
        """After an IN-PLACE reload (A5) rebuilt ``program.db`` from the
        on-disk LIFT: re-hook the new db's write seam and adopt the
        daemon's current head as our base — the in-memory tree now
        derives from that content, so the stale latch clears and saves
        return to the fast path. Daemon unreachable → keep the old base
        (every save still re-merges against it; safe, just not fast).
        If a peer merge lands in the tiny window between the disk read
        and this rebase, the lift-stat probe flags it on the next poll."""
        try:
            self.program.db.collab_submit = self.submit
        except Exception as e:
            log.error(f"adopt_reloaded_db hook: {e}")
        try:
            st = _client.project_status(self.langcode)
            head = getattr(st, 'head_sha', '') if st else ''
            head_blob = getattr(st, 'lift_blob_sha', '') if st else ''
            if head:
                self.base_sha = head
            if head_blob:
                self.base_lift_blob = head_blob
        except Exception as e:
            log.info(f"adopt_reloaded_db status probe: {e}")
        self.record_lift_stat()
        self.stale = False
        self._last_detected_head = ''
        self._offered_head = ''
        log.info(_("Collaboration rebased after in-place reload "
                   "(base {base}).").format(
                       base=self.base_sha[:12] or '<none>'))

    # ── Phase 3: remote-change detection (§17b applied to desktop) ───

    def poll_remote_change(self):
        """Cheap periodic probe (caller schedules it ~every 10 s on the
        UI loop). Returns:

        - ``'none'``    — nothing new (or daemon unreachable; a probe
          failure is never an event).
        - ``'benign'``  — HEAD advanced but the LIFT on disk is still
          exactly what we last wrote (artifact-only commit, e.g. the
          settings JSONs). The base is advanced silently; a save after
          this stays on the fast path.
        - ``'changed'`` — the LIFT changed under us (peer merge landed
          via LAN/WAN, or an earlier save came back MERGED_WITH_LOCAL).
          The base is deliberately NOT advanced — saving stays safe
          (every save re-merges against our real base) — but the user
          should reload to SEE the team's changes.
        """
        if self.stale:
            # Already behind (a merged save, or a peer change detected
            # earlier) — LOCAL knowledge, so normally report 'changed'
            # even if the daemon is unreachable. NEVER advance base or
            # take the benign path on the strength of file stat alone —
            # our in-memory tree is stale regardless of what's on disk.
            #
            # BUT self-heal a FALSE latch (F2): if our on-disk LIFT is
            # still exactly what we last wrote AND the LIFT blob at HEAD
            # equals the blob at our base, then the advance changed no
            # LIFT content we can't already see — the latch was spurious
            # (a LAN hard-reset receive that rewrote identical bytes, or
            # a save the daemon stored but couldn't commit until now).
            # Un-latch by CONTENT identity instead of nagging to reload.
            try:
                st = _client.project_status(self.langcode)
                head = getattr(st, 'head_sha', '') if st else ''
                head_blob = getattr(st, 'lift_blob_sha', '') if st else ''
                if (head_blob and self.base_lift_blob
                        and head_blob == self.base_lift_blob
                        and not self._lift_changed_on_disk()):
                    self.stale = False
                    if head:
                        self.base_sha = head
                    self.base_lift_blob = head_blob
                    self._last_detected_head = ''
                    self._offered_head = ''
                    log.info(_("Team-changes latch cleared: HEAD advanced "
                               "but the lexicon content is unchanged."))
                    return 'benign'
                if head:
                    self._last_detected_head = head
            except Exception:
                pass
            return 'changed'
        try:
            st = _client.project_status(self.langcode)
        except Exception:
            return 'none'
        head = getattr(st, 'head_sha', '') if st else ''
        head_blob = getattr(st, 'lift_blob_sha', '') if st else ''
        if not head or head == self.base_sha:
            # At base: our in-memory tree derives from this LIFT, so
            # anchor its blob as our base blob (content-identity anchor
            # for the F2 self-heal above).
            if head_blob:
                self.base_lift_blob = head_blob
            return 'none'
        if not self._lift_changed_on_disk():
            # HEAD moved but not the LIFT: our own artifact commit (or
            # a peer change to non-LIFT files only). Safe to adopt as
            # the new base — the file our in-memory tree derives from
            # is byte-identical to disk.
            self.base_sha = head
            if head_blob:
                self.base_lift_blob = head_blob
            return 'benign'
        self.stale = True
        self._last_detected_head = head
        log.info(_(
            "Team changes detected (HEAD {head} != base {base}); "
            "reload needed to display them.").format(
                head=head[:12], base=self.base_sha[:12] or '<none>'))
        return 'changed'

    def reload_offer_due(self, snooze_s=300):
        """True when the user should be (re-)offered the reload.

        Rate-limited so declining doesn't nag every poll tick — BUT a
        genuinely new peer head (one we haven't offered for yet)
        bypasses the snooze. So "I said later" quiets THAT change for
        ``snooze_s``, while fresh team work always gets through
        promptly."""
        import time
        now = time.time()
        # A genuinely new peer head bypasses the snooze — but only once
        # we have ACTUALLY offered before (``_offered_head`` non-empty).
        # Without that guard the first offer (fired via the time check
        # below) could store an empty ``_offered_head`` while
        # ``_last_detected_head`` was still empty; the next poll fills
        # the real head, which then reads as "new" and bypasses the
        # snooze → two dialogs back-to-back (the observed quirk).
        new_change = bool(self._last_detected_head) and bool(
            self._offered_head) and (
            self._last_detected_head != self._offered_head)
        if not new_change and now - self._reload_offered_at < snooze_s:
            return False
        self._offered_head = self._last_detected_head
        self._reload_offered_at = now
        return True

    # ── commit/sync surfaces ─────────────────────────────────────────

    def commit_artifacts(self):
        """Debounced whole-tree commit for non-LIFT changes (settings
        JSONs, audio, chart adds). Cheap; call at task boundaries."""
        try:
            _client.commit_project(self.langcode)
        except Exception as e:
            log.info(f"commit_artifacts: {e}")

    def shutdown_sync(self):
        """Replaces the legacy shutdown ``share()``: one commit of any
        remaining artifacts, then the user-gesture-class sync (commit +
        push + pull under one daemon lock). Returns the Result (or
        None); severe codes are surfaced, the rest logged."""
        try:
            result = _client.sync_project(self.langcode)
        except Exception as e:
            log.error(_("Collaboration sync at shutdown failed: "
                        "{error}").format(error=e))
            return None
        log.info("shutdown sync codes: {}".format(result.codes()))
        try:
            from utilities.error_handler import notify_error
            if result.has_any(S.DATA_LOSS_RISK,
                              S.COMMIT_REPEATEDLY_FAILED):
                from azt_collab_client import translate_result
                notify_error(translate_result(result))
        except Exception:
            pass
        if result.has(S.PULLED):
            log.info(_("Teammates’ changes were pulled; they will "
                       "appear the next time this database is opened."))
        return result

    def status(self):
        """ProjectStatus or None (never raises)."""
        try:
            return _client.project_status(self.langcode)
        except Exception:
            return None

    # ── Phase 4: user-gestured sync + routing (recorder §17 table) ───

    def sync(self):
        """User-gestured commit+push+pull, with the canonical result
        routing. Blocks on the network — call under a waiting()
        context. Returns the final Result (or None when a sync was
        already in flight)."""
        if self._sync_in_flight:
            log.info("sync already in flight; ignoring gesture")
            return None
        self._sync_in_flight = True
        try:
            result = _client.sync_project(self.langcode)
            if result.has(S.JOB_INTERRUPTED):
                # Daemon restarted mid-job — typed-retryable, one
                # silent retry (recorder discipline).
                log.info("sync JOB_INTERRUPTED; retrying once")
                result = _client.sync_project(self.langcode)
        finally:
            self._sync_in_flight = False
        self.route_sync_result(result)
        return result

    def route_sync_result(self, result):
        """The user-gesture routing table (adapted from the recorder's
        ``do_sync``, azt_recorder/main.py §17): never-silenced codes
        first, then route-to-what-fixes-it, then transient, then the
        success line. All display goes through ``notify_error`` (the
        ErrorNotice channel); config-class problems also open the
        daemon settings UI (a separate process — non-blocking)."""
        from utilities.error_handler import notify_error
        from azt_collab_client import translate_result, open_server_ui
        title = _("Collaboration")
        # 1. Never-silenced, before any routing.
        if result.has_any(S.DATA_LOSS_RISK, S.COMMIT_REPEATEDLY_FAILED):
            notify_error(translate_result(result), title=title)
        # 2. Piggybacked advisory.
        if result.has(S.AUTH_REFRESH_STALE):
            log.warning("AUTH_REFRESH_STALE: GitHub session needs "
                        "re-authentication soon")
        # 3. Configuration-class → open the screen that fixes it.
        if result.has_any(S.NOT_A_REPO, S.NO_REMOTE, S.AUTH_REQUIRED,
                          S.CONTRIBUTOR_UNSET, S.WORK_OFFLINE_ENABLED):
            notify_error(translate_result(result), title=title)
            try:
                open_server_ui()
            except Exception as e:
                log.error(f"open_server_ui: {e}")
        elif result.has_any(S.APP_NOT_INSTALLED, S.APP_SUSPENDED,
                            S.REPO_NOT_AUTHORIZED, S.REPO_NO_ACCESS):
            # GitHub-side problem; the Result carries the URL that
            # fixes it when known.
            url = ''
            for code in (S.APP_NOT_INSTALLED, S.APP_SUSPENDED,
                         S.REPO_NOT_AUTHORIZED, S.REPO_NO_ACCESS):
                url = result.param(code, 'url', '') or url
            notify_error(translate_result(result), title=title)
            if url:
                try:
                    import webbrowser
                    webbrowser.open(url)
                except Exception as e:
                    log.error(f"webbrowser.open({url!r}): {e}")
        elif result.has_any(S.SERVER_UNAVAILABLE, S.SERVER_ERROR,
                            S.BUSY, S.JOB_INTERRUPTED):
            # Transient — say so, nothing else to route.
            notify_error(translate_result(result), title=title)
        else:
            # Success-shaped (PUSHED / PULLED / NOTHING_TO_COMMIT /
            # COMMITTED_*): show the one-line outcome.
            notify_error(translate_result(result), title=title)
        # 4. Content dimension, independent of the above: a pull that
        # changed local bytes means our in-memory tree is behind.
        # Flag stale; the 10 s poll raises the reload offer (avoids
        # stacking a second dialog right on top of this one).
        if result.has(S.PULLED):
            self.stale = True
            head = getattr(result, 'head_sha', '')
            if head:
                self._last_detected_head = head
            log.info(_("Sync pulled team changes; reload offer will "
                       "follow."))

    def status_summary(self):
        """One human-readable block for the 'Collaboration status'
        popup. Backup truth per §17b (0.53.3): backed-up requires
        wan_unshared == 0 AND main_merged — the count can reach 0
        while bytes await their merge on a topic ref."""
        st = self.status()
        if st is None:
            return _("The collaboration server is not responding.")
        lines = [_("Project: {langcode}").format(langcode=self.langcode)]
        remote = getattr(st, 'remote_url', '')
        wan = getattr(st, 'wan_unshared', 0)
        merged = getattr(st, 'main_merged', True)
        if not remote:
            lines.append(_("Backup: local only (not yet published "
                           "to GitHub)"))
        elif wan == 0 and merged:
            lines.append(_("Backup: up to date on GitHub"))
        elif wan == 0:
            lines.append(_("Backup: finishing (merging on GitHub)…"))
        else:
            lines.append(_("Backup: {n} commit(s) not yet on GitHub"
                           ).format(n=wan))
        n_changes = getattr(st, 'n_changes', 0)
        if n_changes:
            lines.append(_("{n} change(s) not yet committed"
                           ).format(n=n_changes))
        if getattr(st, 'work_offline', False):
            lines.append(_("Work-offline is ON (nothing will be "
                           "sent until it is turned off)"))
        if self.stale:
            lines.append(_("Team changes are waiting — reload to "
                           "see them"))
        if self.degraded:
            lines.append(_("Server was unreachable earlier; saves "
                           "are going directly to disk"))
        try:
            contributor = _client.get_contributor()
            if contributor:
                lines.append(_("Contributor: {name}"
                               ).format(name=contributor))
        except Exception:
            pass
        return '\n'.join(lines)


# ── session construction ─────────────────────────────────────────────


def attach(program):
    """Create ``program.collab`` for an opted-in project (else None).
    Call once at startup, after FileParser (needs ``program.db`` +
    ``program.filename``) and BEFORE ``repocheck`` (which skips legacy
    VCS construction when a session exists). Daemon-unavailable at
    open degrades to the legacy path with a logged warning — a field
    tool must never lose the ability to save (contract D9)."""
    program.collab = None
    try:
        mgr = _settings_mgr(program.filename)
        if not mgr.project.get('collab', False):
            return None
        langcode = (mgr.project.get('collab_langcode', '')
                    or mgr.project.get('analang', ''))
    except Exception as e:
        log.info(f"collab.attach settings read: {e}")
        return None
    if not AVAILABLE:
        log.warning(_(
            "This project is set to use collaboration, but the "
            "azt_collab_client package could not be found (clone "
            "azt-collab beside the azt folder, or set "
            "AZT_COLLAB_DIR); running in legacy mode."))
        return None
    if not langcode:
        log.warning(_("Collaboration is on but no language code is "
                      "stored; running in legacy mode."))
        return None
    try:
        _client.configure(app_id='azt')
        proj = _client.open_project(langcode)
    except Exception as e:
        proj = None
        log.warning(f"collab.attach open_project: {e}")
    if proj is None:
        log.warning(_(
            "Collaboration server unavailable or project {langcode} "
            "not registered; running in legacy mode this session."
            ).format(langcode=langcode))
        return None
    st = None
    try:
        st = _client.project_status(langcode)
    except Exception:
        pass
    base = getattr(st, 'head_sha', '') if st else ''
    session = CollabSession(
        program, langcode, base,
        lift_path=os.path.abspath(str(program.filename)))
    session.record_lift_stat()
    program.collab = session
    # The write seam: Lift.write() hands its .part to the session.
    try:
        program.db.collab_submit = session.submit
    except Exception as e:
        log.error(f"collab.attach db hook: {e}")
        program.collab = None
        return None
    log.info(_("Collaboration active for {langcode} "
               "(base {base}).").format(langcode=langcode,
                                        base=base[:12] or '<none>'))
    return session


# ── opt-in (the per-project cutover switch, decision D3) ─────────────


def connect_current_project(program):
    """Connect the currently-open project to the collaboration daemon
    (adopt-in-place). Returns ``(ok, message)`` for the caller to
    display. Idempotent: reconnecting an already-connected project
    refreshes the registration.

    Eligibility (decision D2): projects with a non-GitHub *internet*
    remote, or Mercurial-only history, stay on the legacy path."""
    if not AVAILABLE:
        return False, _("The collaboration client could not be found; "
                        "clone azt-collab beside the azt folder, or "
                        "set AZT_COLLAB_DIR.")
    working_dir = os.path.dirname(os.path.abspath(str(program.filename)))
    lift_path = os.path.abspath(str(program.filename))
    # Eligibility: Mercurial-only → refuse (hg is retired).
    if (os.path.isdir(os.path.join(working_dir, '.hg'))
            and not os.path.isdir(os.path.join(working_dir, '.git'))):
        return False, _(
            "This project’s history is in Mercurial, which "
            "collaboration does not support; it stays on the legacy "
            "path.")
    # Eligibility: non-GitHub internet remotes → refuse for now.
    for url in _git_remote_urls(working_dir):
        if _is_internet_url(url) and 'github.com' not in url:
            return False, _(
                "This project pushes to a non-GitHub server ({url}); "
                "collaboration currently supports GitHub only, so it "
                "stays on the legacy path.").format(url=url)
    # langcode: settings-authoritative (decision D7).
    try:
        mgr = _settings_mgr(program.filename)
        langcode = mgr.project.get('analang', '') or ''
    except Exception as e:
        return False, _("Could not read project settings: "
                        "{error}").format(error=e)
    if not langcode:
        return False, _("No vernacular language code is set for this "
                        "project yet; open it once and set the "
                        "language first.")
    try:
        _client.configure(app_id='azt')
        # A different project already claiming this directory is the
        # daemon-side 409; surface it usefully rather than as None.
        for p in _client.list_projects():
            if (os.path.abspath(p.working_dir) == working_dir
                    and p.langcode != langcode):
                return False, _(
                    "This folder is already registered to project "
                    "{langcode}; un-register it first or reuse that "
                    "code.").format(langcode=p.langcode)
        proj = _client.register_project(langcode, working_dir, lift_path)
    except Exception as e:
        return False, _("Could not reach the collaboration server: "
                        "{error}").format(error=e)
    if proj is None:
        return False, _("The collaboration server refused the "
                        "registration; see the daemon log.")
    # Contributor seeding (decision D8): mirror the git author once.
    try:
        if not _client.get_contributor():
            name = (_git_config(working_dir, 'user.name')
                    or _git_config(os.path.expanduser('~'), 'user.name'))
            if name:
                _client.set_contributor(name)
                log.info(f"collab contributor seeded from git: {name!r}")
    except Exception as e:
        log.info(f"contributor seeding: {e}")
    # Flip the per-project switch + remember the daemon key.
    try:
        mgr.project.set('collab', True)
        mgr.project.set('collab_langcode', langcode)
        mgr.project.save()
    except Exception as e:
        return False, _("Registered, but could not store the project "
                        "setting: {error}").format(error=e)
    return True, _(
        "Connected! Saves will now go through the collaboration "
        "server.")


def _settings_ui_pythons():
    """Candidate interpreters for the daemon settings UI, which needs
    Kivy — azt's own venv typically doesn't have it (tkinter app; the
    Kivy-free daemon spawn is unaffected). Order: explicit override,
    our own interpreter (covers a Kivy-equipped azt env), then the
    suite's Kivy venvs beside the azt-collab clone."""
    import sys
    cands = []
    env_py = os.environ.get('AZT_COLLAB_UI_PYTHON', '')
    if env_py:
        cands.append(env_py)
    cands.append(sys.executable)
    try:
        collab_root = os.path.dirname(os.path.dirname(
            os.path.abspath(_client.__file__)))
        suite_root = os.path.dirname(collab_root)
        for app in ('azt_recorder', 'azt-viewer'):
            py = os.path.join(suite_root, app, 'env', 'bin', 'python')
            if os.path.isfile(py):
                cands.append(py)
    except Exception:
        pass
    seen = set()
    return [c for c in cands if not (c in seen or seen.add(c))]


def open_settings(program):
    """Open the daemon settings UI (contributor, credentials,
    work-offline, LAN) — a separate process; returns immediately.
    Useful before AND after connecting, so it isn't gated on a
    session. Tries each candidate interpreter until one survives the
    spawn (the UI needs Kivy; see ``_settings_ui_pythons``)."""
    from utilities.error_handler import notify_error
    if not AVAILABLE:
        notify_error(_("The collaboration client could not be found; "
                       "clone azt-collab beside the azt folder, or "
                       "set AZT_COLLAB_DIR."),
                     title=_("Collaboration"))
        return
    last = {}
    for py in _settings_ui_pythons():
        try:
            result = _client.open_server_ui(python_exe=py)
        except TypeError:
            # Client predates the python_exe param (0.53.4).
            result = _client.open_server_ui()
        except Exception as e:
            result = {'ok': False, 'error': str(e)}
        if result.get('ok'):
            log.info(f"settings UI spawned with {py}")
            return
        last = result
        log.warning(
            f"settings UI spawn with {py} failed: "
            f"{result.get('error')} rc={result.get('returncode')} "
            f"detail={result.get('detail', '')!r}")
    detail = last.get('detail', '') or last.get('error', 'unknown')
    notify_error(_(
        "Could not open the collaboration settings: {detail}\n"
        "The settings window needs the Kivy package; install it in "
        "one of the A-Z+T suite’s Python environments, or set "
        "AZT_COLLAB_UI_PYTHON to a python that has it."
        ).format(detail=detail),
        title=_("Collaboration"))


def disconnect_current_project(program):
    """Flip the per-project switch off (rollback path). The daemon
    registration and git history stay — reconnecting is one call."""
    try:
        mgr = _settings_mgr(program.filename)
        mgr.project.set('collab', False)
        mgr.project.save()
    except Exception as e:
        return False, _("Could not store the project setting: "
                        "{error}").format(error=e)
    return True, _("Disconnected; this project will save directly "
                   "to disk again.")
