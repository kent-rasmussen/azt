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
- Related: `agenda/update_install_non-windows-specific.md` (the install work
  this governs), `agenda/torch_for_intel_mac.md`, ADR 0004 D5.

## Context

**There is no declared supported python, and three installers disagree.**
Linux installs 3.12 from deadsnakes, Windows 3.12.4, macOS 3.13.15, while
`py_modules.MIN_PYTHON` says 3.10 and the macOS script's own gate says 3.11.
Development happens on 3.13.7. So the project ships one python, develops on
another, and enforces a third — and a 3.12-only fault cannot reproduce on the
developer's machine.

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
`agenda/cross_platform_checks.md`.

**D3. CEILING: python 3.13** — the highest on which everything
installs, and what development runs. 3.14 is NOT the ceiling, and the reason
is instructive rather than incidental: it is blocked only by the pinned
`torch==2.7.1`, which predates 3.14 and therefore has no cp314 wheel and never
will. That is a **co-move**, not a wait on upstream — python and torch would
go up together. See D6.

**Why 2.7.1, since it is now the deciding pin — searched 2026-09-23, and NO
REASON IS RECORDED.** The changelog mentions the version only when explaining
the macOS marker split; the requirements comments explain the split and the
`+cpu` build but never the number; and the code uses only `import torch` and
`torch.cuda.is_available()` (grep recorded in `agenda/torch_for_intel_mac.md`).
What IS visible: the error note at the foot of `requirements.txt` shows
`torch==2.6.0+cpu` failing against a list ending at 2.8.0, so 2.7.1 was picked
when 2.8.0 was newest. **Inference, not record**: it most likely came from a
`pip freeze` of a working environment, which is exactly what that file's pin
discipline prescribes, one release back from the newest.

One constraint points the other way and must not be lost:
`agenda/asr_model_expansion_design.md` notes fairseq2 publishes against
`pt2.7.0/cpu` and says to verify the pin before building that engine. That is
a planned engine, not a shipped one, and it names 2.7.0 rather than 2.7.1.

So nothing currently shipped requires this version. Moving it is a decision
about the ASR roadmap, not about anything running today.

**D4. RAISING THE FLOOR IS A MIGRATION, AND MUST BE HELPED.** It may never
happen as a side effect of a dependency change, and never as a release note
saying "install python 3.13". Given the upfront-install decision in
`agenda/update_install_non-windows-specific.md`, the installers are the
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

**Open, and the next thing to settle:** the install target itself (3.13.15 or
3.14), and the torch pin that spans the resulting range. Both belong in the
Transitions table below once decided, and both installers plus the Windows
executable move together per D7.

## Transitions

One row per bump, per D7. All installers move together on the same date.

| Date | Floor | Target installed | Why |
|---|---|---|---|
| (before 2026-09-23) | undeclared | Linux 3.12, Windows 3.12.4, macOS 3.13.15 | no policy; each installer chose its own |
| 2026-09-23 | **3.10** | *unchanged, pending alignment* | floor declared by this ADR; aligning the installers belongs to `agenda/update_install_non-windows-specific.md` |

## Measurements

**2026-09-23** — `modules_by_python_version.py`, four platforms
(windows-amd64, linux-x86_64, macos-arm64, macos-x86_64), range 3.9–3.14.

| python | verdict |
|---|---|
| 3.9 | fails: `numpy>=2.1` needs 3.10+ |
| 3.10–3.13 | everything installs |
| 3.14 | `torch==2.7.1` has no cp314 wheel (co-move, not a wait) |

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
- **The ceiling is cheap to move and the floor is expensive.** Moving up is
  ours to schedule. Moving the floor spends other people's bandwidth and
  goodwill, in the field, without us there.
- **This ADR is the thing that stops the conversation restarting.** The
  2026-09-23 session rediscovered, from scratch, that requirements files are a
  rollout mechanism, that transitive dependencies caused every past failure,
  and that macOS and Windows fail for unrelated reasons. All of that is
  written down now — here, in `requirements-webview.txt`, and in the install
  item.
