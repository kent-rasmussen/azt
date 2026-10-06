# ADR 0005 — The supported python range: a declared floor and ceiling, with the floor defended

- Status: **accepted 2026-09-23.** Kent: *"I think we leave 3.10 as floor
  because everything works there, and we have no reason to force things up
  from there (except maybe torch)."* D9's syntax audit was added and the suite
  ran green the same day (754 passed, 9 skipped), so nothing in the source
  needs a python newer than the floor — see Measurements for the one caveat.
- Date: 2026-09-23
- Scope: `azt/` — `requirements.txt`, `requirements-webview.txt`,
  `utilities/py_modules.py` (`MIN_PYTHON`, `ensure_venv`,
  `sync_requirements`), `installfiles/` (all launchers), and
  `modules_by_python_version.py`, which is how the range is measured. Affects
  every install on every platform, and the Windows executable in
  `aztinstaller_windows_exe`, which runs this repo's `requirements.txt`.
- Author: drafted by Claude with Kent, from the 2026-09-23 session. Kent:
  *"we should start an ADR to track the floor and ceiling, with clear
  rationale for each. this will enable us to not start this conversation
  afresh the next time."*
- Related: the non-Windows install item (the install work this governs), the
  torch-for-Intel-Mac item, ADR 0004 D5, and **ADR 0006
  — installers resolve downloads and never pin a URL**, which generalises this
  ADR's install-target lesson to every program an installer fetches. The rule
  "pin the minor, resolve the patch" is stated in both; 0006 owns the URL half
  and carries the lookup endpoints.

## Context

**There is no declared supported python, and the installers disagree.**
Linux installs 3.12 from deadsnakes, macOS 3.13.15, and Windows **3.13** —
the exe decides its own patch and it moves, so this ADR names only the minor
(Kent, 2026-09-24: *"this will be updated again"*). `py_modules.MIN_PYTHON`
says 3.10 and the macOS script's own gate says 3.11. Development happens on
3.13.7.

**CORRECTION 2026-09-24.** This said Windows installs **3.12.4** until that
date, and that number was wrong in a way worth recording, because it came
from reading the wrong file: `installfiles/RunMeAsAdmin-RightClick-toInstall.bat`
hardcodes 3.12.4, and that batch file **is not used** — Windows installs come
from `aztinstaller_windows_exe`. Kent: *"That figure comes from the unused
.bat file; the exe actually uses 3.13.7."* Anything else read out of that
`.bat` is suspect for the same reason.

**It makes the alignment job much smaller than this ADR first described.**
Windows — the platform with the most installs — is already on the same minor
as macOS and as development. **Only Linux is off, by one minor, below the
others.** So "three installers disagree" was never the shape of it; one
installer is behind, and moving it is a single change to a single script.

The cost of that gap is unchanged and is the reason to close it: wheel
availability is per minor, so a 3.12-only fault cannot reproduce on the
developer's machine, and measurements taken on 3.13 do not describe what a
Linux user actually gets.

**`requirements.txt` is a rollout mechanism, which turns a python floor into a
live hazard.** `sync_requirements()` re-runs `pip install -r requirements.txt`
on every install whose venv stamp no longer matches the file's hash. So a
dependency that quietly raises its own python floor does not merely fail to
improve an old machine: it breaks that machine's **next routine update**. And
a failed `-r` withholds the stamp, so the failure repeats on **every boot**
thereafter. That is the shape of the `allosaurus` incident (2026-07-16) with a
different cause, and nothing currently checks for it.

**A python move is a migration, not a version bump.** Kent, 2026-09-23:
*"installing a newer python is not as easy as pulling from azt's git repo to
update azt. We probably should not assume anyone will ever update python
version without being required to, and probably helped."* An azt update is a
git pull. A python move is a new interpreter (administrator rights on
Windows), a new virtual environment, and a full re-download of the dependency
stack — mostly torch — over whatever connection the field has.

**The question was being asked the wrong way round.** The session began with
"does 3.13 work?", which answers one candidate without saying what the
alternative would have been, and ended at "what is the highest version that
will install everywhere?" — and then at the realisation that the *lowest* is
the number with teeth.

## The principle underneath all of this

**A user will not opt in. Anything we want them to have must arrive by
default, and the software has to do the work.** Kent, 2026-09-23, on whether
a change should wait for people to ask for it one machine at a time: *"which
they WON'T, is the point."*

It is stated here because it is what makes the rest of this file follow, and
because it is not specific to python versions:

- Nobody installs a new interpreter voluntarily, so a forced move has to be
  carried by the installers (D4).
- Nobody runs `pip install pywebview`, so when the webview becomes the
  default backend the app installs it itself, gated on the backend actually
  in use rather than on someone naming it
  (`utilities/ui_backend.py::chosen`, and ADR 0004 A4).
- `requirements.txt` is a rollout mechanism rather than a manifest for the
  same reason — which is exactly why raising its python floor is dangerous.

The corollary worth saying out loud: **an opt-in is a decision not to ship the
thing.** Where that is the intent, fine; where it is not, the default has to
move. The one standing constraint is that doing the work must never make
things worse than not doing it, which is why the automatic install fails fast
without a network and never raises.

## Decision

**D1. The supported python range is DECLARED, and lives here.** A floor and a
ceiling, each with its reason and the date it was measured. Anything that
would change either is a decision recorded in this file, not a side effect of
a requirements edit.

**D2. FLOOR: python 3.10.** Rationale, in order of weight:

- It is free today. Measured 2026-09-23, every requirement installs on 3.10,
  3.11, 3.12 and 3.13 across Windows, Linux and both macOS architectures. A
  floor that costs nothing is one to take while it is available, because it
  will not stay available.
- 3.9 is already impossible: `numpy>=2.1` requires 3.10 or later. So 3.10 is
  not a choice so much as the current bottom of the range.
- It is what `py_modules.MIN_PYTHON` already claims, so declaring it
  regularises the code rather than changing it.

**This number should be replaced by evidence of what is actually installed in
the field, when that exists.** A floor set by what still resolves is a
convenience; a floor set by what people are running is the real thing. See
the cross-platform-checks item.

**D3. CEILING: python 3.13, and it is REAL: python 3.14 breaks kivy.**
(Restated 2026-09-28. Kent: *"adr5 needs to acknowledge the ceiling, as
python3.14 would break kivy."*) 3.13 is the highest minor on which everything
installs, and what development runs. The binding reason is **kivy**: it has no
cp314 wheels on any platform, so on 3.14 pip tries to compile it. That fails on
field machines and repeats on every boot (details in the amendment below). That
is a **wait on upstream**. Nothing in this repo can lift it.

**What this means for every installer, the Windows exe included:** the minor it
installs comes from HERE and never goes above this ceiling. An installer must
not choose "the newest python" or step up to the next minor on its own. When its
named minor has no newer installer, it takes the newest patch of THAT minor
that still has one. A statement elsewhere, made on 2026-09-25, that azt has "no
python version ceiling" is superseded by this paragraph. It is true of *policy*
(nobody chose 3.13 as a limit), not of *fact*, and the installers must follow
the fact.

*Original text, kept for the record (it named torch as the blocker; the torch pin
has since been split with a `python_version` marker, so torch no longer blocks
3.14 at all):* 3.14 is NOT the ceiling, and the reason
is instructive rather than incidental: the pinned `torch==2.7.1` predates 3.14
and therefore has no cp314 wheel and never will. That is a **co-move**, not a
wait on upstream — python and torch would go up together. See D6.

**AMENDED 2026-09-25 — "blocked ONLY by torch" is no longer true, and the
second blocker is a worse shape.** This paragraph said torch was the only
thing in the way, measured 2026-09-23. Kent, running `--compare 3.13,3.14` on
2026-09-25: *"I'm seeing kivy show up as a problem now. That could be a real
reason for not upgrading to python 3.14."*

The two are not the same kind of obstacle, and the difference decides whether
3.14 is reachable at all:

- **torch is OURS to move.** The blocking pin is one we wrote, and the
  Measurements below already show 2.9.0 and later resolving on 3.14. Bumping
  it is work, and it waits on nobody.
- **kivy may be a WAIT ON UPSTREAM.** If Kivy has published no cp314 wheel,
  nothing in this repo can produce one. A co-move is a decision; a wait is
  not.

**AND THE CONSEQUENCE HERE IS WORSE THAN A DEGRADED FEATURE, because of how
kivy is checked at boot.** `py_modules.py` tests it with `find_spec('kivy')`
and raises ImportError when it is absent — inside the MANDATORY backstop, not
the `OPTIONAL_ENGINES` list. A missing kivy therefore calls `pip_install()` on
**every boot**. That is precisely the failure the OPTIONAL_ENGINES block was
created to stop: torch and whisper were once mandatory the same way, and a
correctly-installed Intel Mac ran the installer on every open for months.
Moving to 3.14 without a kivy wheel would reproduce it exactly.

**The escape hatch exists and is already this file's established pattern**, but
it is not free. `allosaurus` and `openai_whisper` are excluded by PEP 508
markers where they cannot install, and `python_version` is a legal marker, so
`kivy; python_version < "3.14"` would work. Two costs come with it: kivy must
ALSO move out of the mandatory backstop into the optional list, or the
every-boot pip loop happens regardless of the marker; and kivy's absence is a
real feature loss, not a cosmetic one — the collab project picker and settings
UI are Kivy subprocesses, and on a standalone install azt's venv is the only
python available to run them.

**CHARACTERISED 2026-09-25 — `--compare 3.13,3.14` says `wheel → sdist-only`
on ALL FOUR platforms** (windows-amd64, linux-x86_64, macos-arm64,
macos-x86_64). So kivy is not excluded by a `Requires-Python` bound and no
dependency of its own is at fault: upstream simply has not built cp314 wheels
yet. It is a **wait on Kivy**, and it is the same wait everywhere — there is
no platform that could move first.

**"sdist-only" means pip would TRY TO BUILD, and that is worse than
unavailable here.** The tool measures availability; what matters is whether a
field machine can install it, and kivy is a C/Cython extension:

- **Windows** — needs MSVC build tools. Field users do not have them.
- **macOS without the Xcode tools** — the install deliberately runs
  `--only-binary :all:` there, so the sdist is refused outright by design.
- **Linux** — needs a compiler plus SDL2 development headers. The installer
  apt-installs `python*-dev` and **not** SDL2, so the build would fail; and
  even where it succeeded it would be a long compile in front of a user who
  is installing a dictionary tool.

**AND THE FAILURE COMPOUNDS TWICE ON EVERY BOOT.** A kivy that will not
install fails the whole `-r`, which withholds the requirements stamp, so
`sync_requirements()` re-resolves the entire file on every start — and the
mandatory backstop's `find_spec('kivy')` then raises as well, calling
`pip_install()` a second time. On 3.14 the app would attempt to COMPILE kivy
twice per startup, forever. That is not a degraded install; it is an app that
never finishes starting.

**Why 2.7.1, since it is now the deciding pin — searched 2026-09-23, and NO
REASON IS RECORDED.** The changelog mentions the version only when explaining
the macOS marker split; the requirements comments explain the split and the
`+cpu` build but never the number; and the code uses only `import torch` and
`torch.cuda.is_available()` (grep recorded in the torch-for-Intel-Mac item).
What IS visible: the error note at the foot of `requirements.txt` shows
`torch==2.6.0+cpu` failing against a list ending at 2.8.0, so 2.7.1 was picked
when 2.8.0 was newest. **Inference, not record**: it most likely came from a
`pip freeze` of a working environment, which is exactly what that file's pin
discipline prescribes, one release back from the newest.

One constraint points the other way and must not be lost:
The ASR model-expansion design item notes fairseq2 publishes against
`pt2.7.0/cpu` and says to verify the pin before building that engine. That is
a planned engine, not a shipped one, and it names 2.7.0 rather than 2.7.1.

So nothing currently shipped requires this version. Moving it is a decision
about the ASR roadmap, not about anything running today.

**D4. RAISING THE FLOOR IS A MIGRATION, AND MUST BE HELPED.** It may never
happen as a side effect of a dependency change, and never as a release note
saying "install python 3.13". Given the upfront-install decision in
the non-Windows install item, the installers are the
natural place to carry it: they already locate or install a python, and they
run at the one moment a user is present and watching. What that help looks
like — detect-and-offer, or a separate migration path — is open. The
requirement is that nobody is left to do it alone.

**D5. The floor is checked BEFORE any requirements change, by command.**

```bash
python modules_by_python_version.py --python 3.10 --fail-on-missing --no-pip
```

Non-zero means the edit has raised the floor and would strand every machine
below it. The authoritative form, which also resolves co-requisites — where
every failure this project has actually suffered came from — is:

```bash
python modules_by_python_version.py --via-pip 3.10
```

**D6. The range is RE-MEASURED, not remembered.** A bare run of
`modules_by_python_version.py` sweeps the range, reports the highest and
lowest workable versions, and splits what stands in the way of moving up into
things we schedule (a co-move: a newer release of our own pinned package has
wheels) and things we wait on (nobody publishes one). Record each measurement
below with its date, so the next reading is a comparison rather than a fresh
start.

**D7. A BUMP MOVES EVERY INSTALLER AT ONCE, to the highest workable version,
and is recorded.** Kent, 2026-09-23: *"Each time we bump the install version,
all installers should get the same version (the highest workable at that
point), and that version and the transition date should be noted somewhere."*
That somewhere is the Transitions table below. One version across Linux, macOS
and the Windows executable — the present state, where three installers target
three pythons and development runs a fourth, is what makes a fault
irreproducible on the developer's machine.

**D8. EVERY INSTALLER IS IDEMPOTENT.** Re-running it is how a user gets the
new install: it must find what is already there, bring it up to the declared
version, and never duplicate or half-replace anything. Re-running must be the
answer to "how do I get the update", because it is the only instruction that
survives being given once, in the field, to someone without a terminal.

The venv half of this is ALREADY BUILT and keyed correctly.
`py_modules.ensure_venv()` probes the environment's python, and rebuilds it
when the interpreter will not run, when it is not really a venv (a
half-created one, seen on Windows 2026-07-16), or when its version is below
`MIN_PYTHON`. **It keys on the FLOOR, not on the target, and that is
deliberate**: a wipe means re-downloading the whole dependency stack, most of
it torch, over a field connection. Rebuilding because someone is below the
floor is a correctness requirement; rebuilding because they are below the
current target would spend that cost on a preference. Do not "improve" it by
keying it on the target.

**D9. THE FLOOR IS AUDITED AGAINST OUR OWN SOURCE, not only against wheels.**
Kent, 2026-09-23: *"I think fstrings changed since then... So we might want to
audit that against current code."* Correct, and it is the failure mode most
likely to go unnoticed: PEP 701 (python 3.12) relaxed f-string grammar, so
reusing a quote inside the braces or putting a backslash in the expression
compiles happily on a 3.13 development machine and is a SyntaxError on the
floor. `match` (3.10) and `except*` (3.11) are the same shape.

`tests/test_python_floor_syntax.py` parses every module in the repo with
`ast.parse(..., feature_version=MIN_PYTHON)` and fails naming the file and
line. It reads the floor from `MIN_PYTHON`, which is the single source — this
ADR quotes that constant rather than the other way round. The check is best
effort by CPython's own admission, so when the floor MOVES, compile once with
a real interpreter of that version as well.

**D10. AMENDMENT 2026-09-23 — the floor is TWO numbers, not one.** Kent, the
same day: *"3.13.15 is the lowest version with a windows installer, as of
today. So we need to update all of those before anyone installs again,
probably to 3.14 and all its requirements."*

That fact breaks D2 in half, because a floor chosen from "what still
resolves" quietly assumed anyone could still obtain that python. On Windows
they cannot: CPython publishes binary installers only during a release's
bugfix phase, and a version in security-only maintenance is source-only. So
3.10, 3.11 and 3.12 can still RUN the app while being uninstallable on a new
machine. Two distinct numbers follow:

- **RUNTIME FLOOR — 3.10, unchanged.** The oldest python the app still works
  on. It governs machines that ALREADY have one, and it is the number
  `requirements.txt` must keep resolving against, because every existing
  install re-resolves on its next update. Lowering the ceiling of a
  dependency below this strands them. D5's gate defends exactly this.
- **INSTALL TARGET — what a NEW install gets, and it must be a version whose
  installer still exists.** Today that is 3.13.15 at the lowest, and the
  proposal is 3.14.

> **QUESTIONED 2026-09-28.** Kent has since confirmed that 3.12.10's Windows
> installer is still on python.org's FTP, although 3.12 is security-only. So old
> bugfix-release installers are NOT withdrawn. Security-only releases simply never
> ship one. The "outage" below, and "installers disappear", are unverified as
> stated. A hand check settles it:
> `https://www.python.org/ftp/python/3.13.7/python-3.13.7-amd64.exe`. The
> minor-not-patch fix stands either way.

**THIS IS ALREADY BROKEN ON WINDOWS, found 2026-09-24.** Kent: *"PYTHON
doesn't have an installer less than 3.13.15, so the exe, trying to download
3.13.7, would break."* `aztinstaller_windows_exe` asks for **3.13.7**, and no
installer for it is available, so a fresh Windows install fails at the first
step — on the platform with the most installs and the least room to
experiment. It is not a future migration risk; it is a current outage for
anyone installing today.

The fix belongs in `aztinstaller_windows_exe`, not here, but the shape of it
is this ADR's business and it is the same lesson as the rest of the alignment
work: **a hardcoded patch version is a time bomb precisely because installers
disappear.** The exe should ask for a MINOR and resolve the newest patch that
still has an installer, the way the macOS script already asks GitHub which
Charis release is current. A pinned URL is a fallback, never the mechanism.

**These move independently, and that is what makes the change safe.** Raising
the install target strands nobody: existing machines keep their python and
keep updating, while new machines get a current one. Only raising the RUNTIME
FLOOR breaks anyone.

**The constraint this creates: one pin must serve both ends at once.**
`requirements.txt` is a single file shared by a 3.10 machine in the field and
a 3.14 machine installed tomorrow, so every pin has to satisfy the whole
range. For torch that is a real question — 3.14 needs 2.9.0 or later, and
whether 2.9.0 still has 3.10 wheels decides whether the range can be spanned
at all. `--versions torch` now prints an "ACROSS EVERY PYTHON IN THE RANGE"
line for exactly this. If it comes back empty, the choice is to narrow the
supported range (raise the runtime floor, a migration) or to split the pin
with a `python_version` marker.

~~**Open, and the next thing to settle:**~~ **BOTH SETTLED 2026-09-25**, and
the split is why the second stopped being a question. The install target is
3.13.15 (kivy blocks 3.14); the torch pin no longer has to span the range at
all, because a `python_version` marker now carries one pin on each side of
3.14. Both installers plus the Windows executable still move together per D7.

**DECIDED BY MEASUREMENT 2026-09-25 — THE INSTALL TARGET IS 3.13.15, AND 3.14
IS NOT AVAILABLE TO CHOOSE.** Kivy is sdist-only on 3.14 across all four
platforms (D3 amendment), so the move waits on Kivy publishing wheels, at a
date nobody here controls.

**This removes the deadline that made 3.14 look urgent.** D10's argument was
that 3.13's installers would vanish anyway, so moving was forced rather than
chosen. But **3.13.15 is precisely the version whose installer still exists** —
it is the one D10 names. So the urgent problem is not "get to 3.14 before the
door shuts"; it is "stop asking for 3.13.7, which is already gone". Those have
completely different sizes, and only the second is on fire.

So the settled position:

- **Install target: 3.13.15.** Available on every platform, carries every
  requirement, and is the minor development already runs.
- **Windows exe: change 3.13.7 → 3.13.15.** That alone ends the current
  outage. No 3.14 migration is needed or possible.
- **Linux: 3.12 → 3.13**, which is now an alignment onto a settled target
  rather than a step toward a moving one.
- **3.14: PINNED OUT, and the pin is managed by hand.** Kent, 2026-09-25: *"I
  think we need to just pin on 3.13.15 for now (at least the next 6 weeks?).
  Annoying to have to manage that manually, but good to know."* There is no
  automation that will notice Kivy publishing cp314 wheels, so somebody has to
  ask. The asking is one command:

  ```
  python modules_by_python_version.py --compare 3.13,3.14
  ```

  Clear on kivy means the 3.14 question reopens. Still sdist-only means do
  nothing and ask again later. **First review: around 2026-11-06** — Kent's
  estimate, not a measured release date, so treat it as a reminder rather than
  a deadline.

  **How the all-clear will LOOK, and it is not a kivy line.** `compare()`
  reports only rows that CHANGE between the two pythons. Once kivy has a cp314
  wheel it is `wheel` on both, so it stops differing and **drops out
  entirely**. The signal is the absence of the kivy block, and the headline
  `Nothing gets worse on 3.14.` Do not wait for kivy to appear under "Better
  on 3.14" — that section fires only when a package is worse on the OLD
  python, which is not what happens here.
- **The torch pin is SPLIT, 2026-09-25, so it cannot break on 3.14 whenever
  3.14 arrives.** Kent: *"in order to keep torch from breaking, in any case,
  let's pin current to py <3.14, and then 2.14.0 to py >=3.14."* This takes
  the escape named above under "one pin must serve both ends" — a
  `python_version` marker rather than narrowing the supported range. Four
  lines now, since each of the two platform cases splits in two. The new lines
  are **inert**: their marker excludes every python in use, so they change no
  existing install and are a guard rather than a rollout. The 2.14.0 figure is
  the top of the 2026-09-23 sweep and NOT a `pip freeze` of a working 3.14
  environment, because none exists — re-check with `--via-pip 3.14` before
  anyone moves.
- **The comparison tool needed a fix to survive that split**, made the same
  day. `n/a` outranks every real verdict, so a line switched ON by a
  `python_version` marker scored as a rank DROP and printed under "these block
  the move" — torch would have been reported as blocking 3.14 on every
  compare, with its other half listed as an improvement, burying the kivy
  answer the command exists to give. `compare()` now skips any transition
  where either side is `n/a`.

**THE FALLBACK IS BETTER THAN "GIVE UP THE COLLAB UI" (checked 2026-09-25).**
An earlier draft of this section said excluding kivy meant losing the picker
and settings window. Reading `backend/core/collab.py` says otherwise, and the
distinction matters if 3.14 ever becomes compulsory:

- **The daemon is Kivy-free and always has been** — `collab.py:49` records it
  as such on desktop paths since client 0.53.1. Sync, git, credentials
  storage, locking and merging do not touch Kivy.
- **Both Kivy call sites degrade, they do not crash.** `open_settings()`
  shows a notice and returns; `pick_team_project()` returns an error string
  its caller already handles.
- **The interpreter running those two windows is ALREADY pluggable.**
  `_settings_ui_pythons()` tries `AZT_COLLAB_UI_PYTHON`, then azt's own
  python, then the `azt_recorder` and `azt-viewer` venvs beside the
  azt-collab clone. Kivy never had to be in azt's venv — its own docstring
  says azt's venv "typically doesn't have Kivy".

**BUT THE THIRD POINT OVERSTATED IT, and Kent caught it the same day:** *"I
don't think there are actually those venvs today. If we want a kivy venv, we
should set that up distinctly, and know where to find it."*

Right. `_settings_ui_pythons()` PROBES for `azt_recorder/env` and
`azt-viewer/env`; it does not create them, and on a standalone azt install
neither exists. So of its three candidates:

| Candidate | Status today |
|---|---|
| `AZT_COLLAB_UI_PYTHON` | nothing sets it |
| azt's own `sys.executable` | **the one that works** — kivy is in `requirements.txt`, so azt's venv has it |
| sibling `azt_recorder` / `azt-viewer` venvs | speculative; not present on a standalone install, and per Kent not present today at all |

**So there is no fallback today — there is one working path, and 3.14 is
exactly what breaks it.** Kivy works now only because it rides in azt's own
venv, which is precisely the venv that could not have it on 3.14. The sibling
probe is a convenience for a suite development machine, not a design.

**DECISION: if the Kivy UIs are to survive a python azt cannot share, they get
their own venv, created deliberately, at a known location.** Not discovered by
probing whatever happens to be lying beside the clone. Properties it needs:

- **A fixed, documented path**, so both the daemon and azt look in one place
  and an installer has something definite to build. The suite already puts its
  shared venv at `AZT/env`, so a sibling under that root is the consistent
  shape.
- **Its own python, pinned to whatever has kivy wheels** — 3.13 today. That is
  the entire point: it is deliberately NOT azt's interpreter.
- **Built by the installers**, like the main venv, and skippable, since it is
  only needed by collaboration.
- **Selected by a switch, not `AZT_COLLAB_UI_PYTHON`**, per the
  switches-not-env-vars rule of 2026-09-08. The env var can stay as the
  override of last resort.

**AND IT STILL DOES NOT RESCUE 3.14.** Kent, 2026-09-25: *"This new design
would require users to have both pythons installed, to have any value."* That
is the end of it. A separate venv needs a separate INTERPRETER — that is the
whole reason for wanting one — so a field user would have to obtain and keep
both 3.14 and 3.13. The installers install one python, on a connection that
makes installing one slow; two is not a refinement of that, it is a different
proposition. So `env-kivy` is a **tidiness improvement, not an escape hatch**,
and the 3.14 question does not have a price after all. It has a blocker.

**`env-kivy` is still worth building, on its own merits and not for 3.14.**
Kent, same message: *"we should consider making env-kivy, corresponding to
env, with the same mechanics of location and creation, but with a distinct
requirements-kivy.txt."* That shape is right: mirror `env` exactly — same
place, same creation path, same stamp discipline — and give it its own
requirements file. What it buys is that a heavy GUI dependency stops riding in
the venv of a tkinter application that never imports it. What it does NOT buy
is a python azt cannot share. Those are separate claims and only the first
survives.

One thing still unchecked: whether GitHub credentials can be entered without
the settings window. Contributor is fine — `connect_current_project` seeds it
from git config automatically — but if credentials have no other route, then
losing the Kivy UI means a new user cannot authenticate, which would make the
"degrades gracefully" claim above true in code and false in practice.

## Transitions

One row per bump, per D7. All installers move together on the same date.

| Date | Floor | Target installed | Why |
|---|---|---|---|
| (before 2026-09-23) | undeclared | Linux 3.12, Windows 3.13, macOS 3.13.15 | no policy; each installer chose its own |
| 2026-09-23 | **3.10** | *unchanged, pending alignment* | floor declared by this ADR; aligning the installers belongs to the non-Windows install item |
| 2026-09-25 | 3.10 | **3.13.15** *(decided; not yet applied anywhere)* | kivy is sdist-only on 3.14, so 3.14 is a wait on upstream and 3.13.15 is the highest target that exists. Linux moves 3.12 → 3.13. **Held here until kivy ships cp314 wheels; review ~2026-11-06 with the `--compare` command in D10.** |

The Windows cell read **3.12.4** until 2026-09-24. It was taken from the dead
`.bat`; the exe is on 3.13. See the correction in Context. **Do not restate
the exe's PATCH version anywhere in this repo** — it moves on its own
schedule, and `aztinstaller_windows_exe` is its only source of truth. The
minor is what this ADR governs, and it is the only part that decides whether
anything installs.

## Measurements

**2026-09-23** — `modules_by_python_version.py`, four platforms
(windows-amd64, linux-x86_64, macos-arm64, macos-x86_64), range 3.9–3.14.

| python | verdict |
|---|---|
| 3.9 | fails: `numpy>=2.1` needs 3.10+ |
| 3.10–3.13 | everything installs |
| 3.14 | **kivy is sdist-only on all four platforms** (measured 2026-09-25) — a wait on upstream, and the binding constraint. Also `torch==2.7.1` has no cp314 wheel, but that is a co-move we control and moot while kivy blocks. |

Standing cases, unchanged by python version and therefore not version
problems: `openai_whisper` publishes no wheel at all (pure python, so it
installs anyway) and `torch==…+cpu` resolves from the PyTorch index rather
than PyPI. Windows resolved 85 distributions cleanly on 3.13 with
co-requisites included.

**Torch candidates, 2026-09-23** (`--versions torch`), which settle what the
pin costs at each python:

| python | windows-amd64 | linux-x86_64 | macos-arm64 | macos-x86_64 |
|---|---|---|---|---|
| 3.13 | 2.6.0 – 2.14.0 | 2.5.0 – 2.14.0 | 2.6.0 – 2.14.0 | none |
| 3.14 | 2.9.0 – 2.14.0 | 2.9.0 – 2.14.0 | 2.9.0 – 2.14.0 | none |

Read: **the newest torch works on both**, so torch does not force a choice
between 3.13 and 3.14. What 3.14 forces is a FLOOR on torch of 2.9.0, where
3.13 allows 2.6.0. Intel macOS has no torch at either python — long known,
already handled by the `platform_machine == "arm64"` marker, and not a new
finding.

So the standing pin of 2.7.1 is compatible with 3.13 and NOT with 3.14. Moving
it to 2.9.0 or later would make both pythons available. Nothing forces that
move and nothing blocks it; it is a scheduling decision, which is what D3
means by calling 3.14 a co-move.

**Syntax audit, 2026-09-23**: `tests/test_python_floor_syntax.py` added and
the full suite ran green — 754 passed, 9 skipped. So no module in the repo
uses syntax newer than 3.10, and the f-string worry that prompted D9 is
answered for now.

**Confirmed the same day**: the nine skips were all accounted for elsewhere —
three backend-logic stubs, four orphan/standalone modules in the import smoke
test, one commented-out wait dialog and one unused sound path. None was the
floor test, so it ran and passed. The floor is verified against the source,
not merely assumed.

## Consequences

- **The develop/ship gap becomes visible and must be closed or accepted
  knowingly.** Development on 3.13 while Linux and Windows deploy 3.12 means
  a 3.12 fault cannot reproduce locally. D5's gate is the mitigation; aligning
  the installers is the fix, and belongs to the install item.
- **Pins acquire an expiry.** An exact pin can never gain wheels for a python
  released after it, so every such pin eventually reads as a blocker when it
  is really a scheduling item. `--audit-pins` exists to find pins that have
  stopped earning their place, including `numpy<2.5`, whose own comment says
  "recheck when numba's cap moves" and which nothing has ever rechecked.
- **The floor is expensive to move; the ceiling is cheap only when WE are what
  holds it.** A pin of ours (torch) is ours to schedule. A missing upstream
  wheel (kivy, 2026-09-25) is not: the ceiling then waits on someone else, and
  the only lever is the `--compare` check in D10. Moving the floor spends other people's bandwidth and
  goodwill, in the field, without us there.
- **This ADR is the thing that stops the conversation restarting.** The
  2026-09-23 session rediscovered, from scratch, that requirements files are a
  rollout mechanism, that transitive dependencies caused every past failure,
  and that macOS and Windows fail for unrelated reasons. All of that is
  written down now — here, in `requirements-webview.txt`, and in the install
  item.
