# ADR 0006 — Installers RESOLVE their downloads at run time; no pinned version in any download URL

- Status: **accepted 2026-09-28.** Kent: *"We should be using pin free URLs for
  all our installs."* The endpoints below are his, checked by hand 2026-09-25
  to 2026-09-28.
- Date: 2026-09-28
- Scope: every installer in the suite, and this is deliberately wider than one
  repo — `azt/installfiles/` (`RunMetoInstall_Linux.sh`,
  `RunMetoInstall_Mac.command`), `aztinstaller_windows_exe`, and any future
  installer. It governs what a script DOWNLOADS. It does **not** govern
  `requirements.txt`, which stays pinned; see "What this does not change".
- Author: drafted by Claude with Kent, from the 2026-09-25/28 sessions.
- Related: ADR 0005 (the python range — this is the generalisation of its
  install-target lesson), `agenda/update_install_non-windows-specific.md`.

## Context

**The standing instruction.** Kent, 2026-09-28: *"We should be using pin free
URLs for all our installs."* That is the decision; the reasons below support
it, and the first of them is weaker than it first appeared.

**THE MOTIVATING CLAIM IS QUESTIONED — do not repeat it as fact.** This ADR
began from `aztinstaller_windows_exe` asking for python **3.13.7** and Kent
reporting, 2026-09-25, *"PYTHON doesn't have an installer less than 3.13.15,
so the exe, trying to download 3.13.7, would break."* On 2026-09-28, while
working the exe, he found `python-3.12.10-amd64.exe` **still on python.org's
FTP** although 3.12 has been security-only since 2025. So python.org does not
appear to withdraw old bugfix installers, and "a pinned URL rots because the
file is taken down" is **not established**. Whether 3.13.7's own installer
still downloads has not been checked by hand:

```
https://www.python.org/ftp/python/3.13.7/python-3.13.7-amd64.exe
```

A plausible reconciliation is that the per-minor "latest" page names only the
current patch while the FTP archive keeps every past one, so both statements
are about different places. **That has not been verified and is not relied on
anywhere in this ADR.** See `agenda/update_install_non-windows-specific.md`,
which carries the open question.

**The decision survives without it**, on reasons that are demonstrated rather
than inferred:

1. **Asset filenames are not derivable, and they change.** Three of the four
   GitHub projects we fetch mangle the version in the asset name (D2's table).
   A URL typed from one release is not a pattern that holds for the next.
2. **A resolved URL gets the current release; a pinned one silently gets an
   old one.** Even where the old file still serves, the user installs
   something stale that nobody chose. That is the Windows `.bat`'s Charis
   6.200 against the Mac script's 7.000: not a breakage, just two platforms
   quietly diverging.
3. **Hosting moves even when files do not.** GitHub asset URLs, SourceForge
   redirects and vendor download paths are outside our control and have no
   deprecation notice that reaches us.
4. **A pinned URL is never re-checked.** It records what was true when it was
   typed, in a file nobody revisits until a user reports that installation is
   broken.

**The precedent was already in the repo, and it worked.** The macOS installer
asks GitHub which Charis release is current rather than naming one, precisely
so it needs no editing when SIL publishes. Its own comment says as much. The
Linux installer gets the same property free from apt, which takes a package
name and supplies whatever version it has. What was missing was the rule.

**The precedent was already in the repo, and it worked.** The macOS installer
asks GitHub which Charis release is current rather than naming one, precisely
so it needs no editing when SIL publishes. Its own comment says as much. The
Linux installer gets the same property free from apt, which takes a package
name and supplies whatever version it has. What was missing was the rule.

## Decision

**D1. Every download URL is RESOLVED from a publisher endpoint at install
time.** The installer asks what the current release is, then downloads what
the answer names. No installer contains a version number in a URL it intends
to use.

**D2. READ THE ASSET NAME FROM THE ANSWER; never construct it from the tag.**
This is the operational half, and three of the four GitHub projects below
break the obvious guess:

| Project | Tag | Asset filename |
|---|---|---|
| Git for Windows | `v2.55.0.windows.5` | `Git-2.55.0.5-64-bit.exe` |
| Praat | `v7.0.02` | `praat7002_win-x64v1.zip` |
| XLingPaper | `v3.19.3` | `XLingPaper3.19.3.0XXEPersonalEditionFullSetup.exe` |
| Charis | `v7.000` | `Charis-7.000.zip` |

Only Charis is derivable, and even there the filename is **case-sensitive** on
software.sil.org (`Charis-7.000.zip` serves, `charis-7.000.zip` does not). So
GitHub's `releases/latest/download/<asset>` form — which redirects to a FIXED
asset name inside whatever release is latest — is unusable here: it works only
for projects whose asset names stay constant across releases, and none of ours
do. Ask the API for the asset list and pick from it.

**D3. A pinned URL is allowed ONLY as a named fallback, never as the
mechanism.** The lookup can fail for reasons that have nothing to do with the
release: `api.github.com` rate-limited behind a shared NAT, or a proxy that
permits `software.sil.org` and not GitHub. One known-good URL behind the
lookup means a user gets a release one behind instead of nothing. It does not
need urgent updating, because it is only ever reached in that situation.

**D4. Verify what arrived before installing it.** A 404 page saved under the
expected filename must not count as success. The macOS script's rule is the
one to copy: list the archive and check it contains the file type expected
before touching the system. It found several bad downloads that way.

**D5. Where no "latest" endpoint exists, WALK BACKWARDS.** python.org's
per-minor latest page can name a version with no Windows installer. The
installer then probes each earlier patch at the ftp pattern until one exists,
rather than giving up or guessing:

```
https://www.python.org/ftp/python/<version>/python-<version>-amd64.exe
```

**D6. Pin the MINOR, resolve the PATCH.** From ADR 0005, restated here because
it is the same rule seen from the other side. Wheel availability is per python
minor, so the minor is a compatibility decision that must be deliberate. The
patch affects nothing about what installs and must never be written down.

**D7. THE MINOR IS NAMED BY `azt`, AND AN INSTALLER NEVER BUMPS IT ITSELF.**
This is the contract that keeps D1 from quietly becoming "always install the
newest python", which would walk straight into the kivy wall of ADR 0005 —
kivy is sdist-only on 3.14, so an installer that took "latest" would break
every new install the day 3.14 became latest. So the split of authority is:

- **`azt` names the MINOR.** It is a compatibility decision, measured with
  `modules_by_python_version.py` and recorded in ADR 0005's Transitions table.
- **The installer resolves the PATCH** of that minor, walking back per D5 when
  the newest is source-only.

Agreed with Kent 2026-09-28 while building the exe's PR2, in exactly those
terms: it *"takes the minor THIS repo names, and the newest patch of that minor
with a Windows installer... It never bumps to the next minor on its own."* So
when 3.13 eventually goes security-only, nothing moves on its own — ADR 0005
gets edited, deliberately, and every installer follows.

## What this does NOT change

**`requirements.txt` stays pinned, and nothing here argues otherwise.** The two
look similar and are opposites:

- A **requirement pin** is a compatibility statement: this version is known to
  work with the others. Its file has explicit pin discipline — pin from a
  known-good environment, never below what deployed environments run — and
  unpinning would hand every install a resolver's opinion on every update.
- A **URL pin** is a bet that a file stays hosted, which nobody made
  deliberately and which decays with no signal.

So: resolve what you fetch from a publisher; pin what your code depends on.

## The endpoints, checked 2026-09-25 to 2026-09-28

Kent's measurements. Each shows what the lookup returned on the day, as
evidence the endpoint works — **not** as a version to write into anything.

**Python 3.13** — `https://www.python.org/downloads/latest/python3.13/`
→ 3.13.15 → `https://www.python.org/ftp/python/3.13.15/python-3.13.15-amd64.exe`

**Git for Windows** — `https://api.github.com/repos/git-for-windows/git/releases/latest`
→ v2.55.0.windows.5 → `https://github.com/git-for-windows/git/releases/download/v2.55.0.windows.5/Git-2.55.0.5-64-bit.exe`

**Charis** — `https://api.github.com/repos/silnrsi/font-charis/releases/latest`
→ v7.000 → `https://github.com/silnrsi/font-charis/releases/download/v7.000/Charis-7.000.zip`

**Praat** — `https://api.github.com/repos/praat/praat.github.io/releases/latest`
→ v7.0.02 → `https://github.com/praat/praat.github.io/releases/download/v7.0.02/praat7002_win-x64v1.zip`

**XLingPaper** — `https://api.github.com/repos/sillsdev/XLingPap/releases/latest`
→ v3.19.3 → `https://github.com/sillsdev/XLingPap/releases/download/v3.19.3/XLingPaper3.19.3.0XXEPersonalEditionFullSetup.exe`

**Mercurial** — `https://www.mercurial-scm.org/release/windows/latest.dat`
→ 7.1.2 → `https://mercurial-scm.org/release/windows/Mercurial-7.1.2-x64.exe`

### The same four, for a human with a browser

- `https://github.com/git-for-windows/git/releases/latest`
- `https://github.com/silnrsi/font-charis/releases/latest`
- `https://github.com/praat/praat.github.io/releases/latest`
- `https://github.com/sillsdev/XLingPap/releases/latest`

## Compliance today

| Installer | Status |
|---|---|
| `aztinstaller_windows_exe` | the reason this ADR exists. **STATE UNVERIFIED FROM HERE** — see note below |
| `RunMetoInstall_Mac.command` | **compliant 2026-09-28, UNTESTED.** Charis resolves via the GitHub API with a pinned fallback; the git URL is SourceForge's "latest" redirect; python is now `PY_MINOR="3.13"` plus `resolve_python_url()`, which asks the per-minor latest page and walks back to a patch that has a macOS installer (D5/D6), with 3.13.15 demoted to the D3 fallback. Nobody has run it |
| `RunMetoInstall_Linux.sh` | **compliant by construction** — apt takes a package name and supplies its own newest patch; `PYMINOR` names only the minor, per D6 |
| `RunMeAsAdmin-RightClick-toInstall.bat` | dead file, not in use; its hardcoded 3.12.4 and Charis 6.200 are exactly what this ADR forbids |

**Known gaps:** none left in `azt/` as of 2026-09-28. The macOS script's
pinned patch was the last one, and the three user-facing docs that handed out
a dead `python-3.12.4-amd64.exe` link (`SIMPLEINSTALL.md`, `INSTALL.md`,
`INSTALL_BOUNTY.md`) now point at the per-minor latest page. **None of it is
tested** — the macOS resolution in particular has never run.

**DO NOT DESCRIBE THE EXE'S STATE FROM THIS REPO (2026-09-28).** An earlier
version of the row above said what the exe's PR1 and PR2 did, taken from notes
in `azt/agenda/`. Kent, marking that work done: *"it's notes aren't current,
apparently, if they say what you think."* They were not. The exe repo is the
only authority on what the exe does, and the boundary this whole item exists
to protect is the same one that makes second-hand notes go stale here without
anyone noticing. Record what `azt/` decides; ask the exe repo what it does.
