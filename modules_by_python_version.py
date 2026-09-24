#!/usr/bin/env python3
# coding=UTF-8
"""Can we move to a new python? Ask PyPI, per platform, before anyone moves.

═══ NORMAL USE IS TWO COMMANDS. Everything else is for a rare day. ═══

    python modules_by_python_version.py
        The answer: floor, ceiling, what blocks moving up, whether the
        winner really resolves, and which of our pins have gone stale.

    python modules_by_python_version.py --versions torch
        The candidates: which versions of one package publish a wheel, per
        python and platform. Use it to choose a new pin.

`--help` lists the rest, grouped, with the rarely-needed ones last. If you
are reading this because a switch was needed twice, that is a bug — say so
and it becomes a default, as --best, --via-pip, --audit-pins, the extra index
and the set-aside list all did.


WHAT THIS ANSWERS. "Everything installs on 3.12; does it all install on
3.13?" — for every requirement, on every platform we ship to, before a single
user is moved. Kent, 2026-09-23: *"before putting anyone on 3.13, we should
make sure that everything installs there fine all around. then move everyone
together. We should probably set up a process for doing this in an orderly
way, since this will come up again."*

  python modules_by_python_version.py

That is the whole process: run it and read the last two lines. Searching is
the DEFAULT, because asking about one candidate version answers "does 3.13
work" without ever saying what the alternative would have been — and the
alternative is the decision. `--python X.Y` still asks about one version, and
`--compare X.Y,X.Z` reports only what changes between two.
`--fail-on-missing` makes it exit non-zero, so it can gate a release rather
than merely inform one.

DELIBERATELY REPO-AGNOSTIC. Nothing here knows what A-Z+T is. It reads
whatever `requirements*.txt` it finds beside it (or `--requirements`), so it
can be copied into another repo and run unchanged. Only two imports beyond the
standard library, and one of them is optional.

WHAT IT IMPROVED ON, from the first draft — worth stating, because each was a
wrong answer rather than a missing feature:

 1. **It was Windows-only.** The file filter dropped every `macosx` and
    `linux` wheel and the result dict was called `winvers`, so the two
    platforms with the actual problems could not be seen. macOS is where the
    known failures are (torch on Intel, openai_whisper's numba).
 2. **The module list was hand-kept and had drifted** — it still asked about
    `pyaudio`, `librosa`, `whisper`, `torchaudio`, `mysql-connector-python`
    and `wave`, none of which are requirements any more, while missing most
    of the ones that are. Reading `requirements*.txt` cannot drift.
 3. **It ignored environment markers**, so `allosaurus; sys_platform ==
    "linux"` would read as "missing on Windows and macOS" — a false alarm on
    a line written precisely to prevent that failure. Markers are now
    evaluated per platform, and a requirement excluded by its own marker is
    reported as `n/a`, not as a problem.
 4. **It ignored `Requires-Python`.** A package can publish a `py3-none-any`
    wheel and still refuse to install, which is exactly the numpy incident
    recorded at the bottom of `requirements.txt` ("Requires-Python
    >=3.9,<3.13"). That is the single most likely shape of a 3.13 problem and
    the old script could not see it.
 5. **It ignored the pins.** `numpy>=2.1,<2.5` means the question is whether
    a wheel exists *within that range*, not whether the newest release has
    one.
 6. **It counted rather than judged.** A table of how many wheels each python
    tag had does not say whether the thing installs.

TWO LIMITS, STATED RATHER THAN HIDDEN.

**It reads the names you listed, and does not resolve what THEY require.**
The default scan asks PyPI about each line of `requirements*.txt` and nothing
further. That is not a corner case in this repo: every install disaster
`requirements.txt` records was caused by a dependency nobody listed — numba
(behind openai_whisper) for the python-3.13 Intel-macOS failure AND for the
`numpy<2.5` cap, and editdistance (behind allosaurus) for the Windows one. A
declared-requirements scan calls all three fine. So the scan is a fast first
pass that NAMES the requirement to look at, and `--via-pip X.Y` is the
authoritative answer: it hands the whole set to pip's own resolver, per
platform, refusing source builds. Run that before moving anyone.

**A pin carrying a local version** (`torch==2.7.1+cpu`) lives on a separate
index, so PyPI cannot answer for it and it is reported as `extra-index`
rather than guessed at. `--via-pip` with `--pip-extra-index-url` resolves it
properly.
"""
import argparse
import fnmatch
import glob
import json
import os
import sys
import textwrap
import urllib.error
import urllib.request

try:
    from packaging.markers import UndefinedEnvironmentName
    from packaging.requirements import InvalidRequirement, Requirement
    from packaging.specifiers import InvalidSpecifier, SpecifierSet
    from packaging.version import InvalidVersion, Version
except ImportError:
    sys.exit("This needs `packaging` (pip install packaging).")


# ── Platforms we ship to ────────────────────────────────────────────────────
# Each entry is what a wheel must match to count, plus the marker environment
# that decides whether a requirement applies here at all. Add a row to support
# another target; nothing else needs touching.
#
# `tags` are matched against the wheel's PLATFORM tag as prefixes, because the
# real tags carry version detail we do not want to enumerate
# (`manylinux_2_17_x86_64`, `macosx_11_0_arm64`, `macosx_10_9_universal2`...).
# ── Project knowledge: the few things the tool cannot work out ──────────────
# KEPT AT THE TOP SO THE NEXT ONE HAS AN OBVIOUS HOME (Kent, 2026-09-23:
# "maybe keep oai_whisper exception near the top, in case we need to add
# another later").
#
# Packages that publish NO WHEEL, by their own long-standing choice rather
# than by oversight. They matter because cross-platform resolution forces
# `--only-binary`, so one of these aborts the whole resolve and hides every
# co-requisite behind it.
#
# THIS LIST IS A CONVENIENCE, NOT A REQUIREMENT. The scan derives the same
# set from what it finds on the indexes, and the two are merged — so an empty
# list here still works, which is what keeps the tool portable to a repo with
# entirely different packages. Naming them here documents the ones we already
# know about, and makes adding the next one a one-line edit instead of a
# rediscovery.
#   openai_whisper: sdist-only for years; pure python, so it installs anyway.
KNOWN_SDIST_ONLY = ('openai_whisper',)

# Families released as a matched set live in ALIGNED_FAMILIES, further down
# beside the code that uses them.
#
# `pip_tags` are the concrete `--platform` values for the `--via-pip` pass,
# which is the only one that sees TRANSITIVE dependencies. See `via_pip`.
PLATFORMS = {
    'linux-x86_64': {
        # NEWER manylinux TAGS MATTER. PyTorch moved its Linux wheels to
        # manylinux_2_28 around 2.7, so a tag list stopping at 2_17 made
        # `torch==2.7.1+cpu` look absent while pip cheerfully listed 2.6.0+cpu
        # as available (Kent's run, 2026-09-23). A platform's tag list is a
        # claim about what the target can load; keep it ahead of the wheels.
        'pip_tags': ('manylinux_2_34_x86_64', 'manylinux_2_31_x86_64',
                     'manylinux_2_28_x86_64', 'manylinux2014_x86_64',
                     'manylinux_2_17_x86_64', 'linux_x86_64'),
        'tags': ('manylinux', 'linux_x86_64', 'musllinux'),
        'tag_must_end': ('x86_64',),
        'env': {'sys_platform': 'linux', 'platform_system': 'Linux',
                'platform_machine': 'x86_64', 'os_name': 'posix'},
    },
    'linux-aarch64': {
        'pip_tags': ('manylinux_2_34_aarch64', 'manylinux_2_31_aarch64',
                     'manylinux_2_28_aarch64', 'manylinux2014_aarch64',
                     'manylinux_2_17_aarch64'),
        'tags': ('manylinux', 'linux_aarch64', 'musllinux'),
        'tag_must_end': ('aarch64',),
        'env': {'sys_platform': 'linux', 'platform_system': 'Linux',
                'platform_machine': 'aarch64', 'os_name': 'posix'},
    },
    'macos-x86_64': {
        'pip_tags': ('macosx_10_9_x86_64', 'macosx_11_0_x86_64',
                     'macosx_10_9_universal2'),
        'tags': ('macosx',),
        'tag_must_end': ('x86_64', 'universal2', 'intel', 'fat64'),
        'env': {'sys_platform': 'darwin', 'platform_system': 'Darwin',
                'platform_machine': 'x86_64', 'os_name': 'posix'},
    },
    'macos-arm64': {
        'pip_tags': ('macosx_11_0_arm64', 'macosx_12_0_arm64',
                     'macosx_11_0_universal2'),
        'tags': ('macosx',),
        'tag_must_end': ('arm64', 'universal2'),
        'env': {'sys_platform': 'darwin', 'platform_system': 'Darwin',
                'platform_machine': 'arm64', 'os_name': 'posix'},
    },
    'windows-amd64': {
        'pip_tags': ('win_amd64',),
        'tags': ('win_amd64',),
        'tag_must_end': (),
        'env': {'sys_platform': 'win32', 'platform_system': 'Windows',
                'platform_machine': 'AMD64', 'os_name': 'nt'},
    },
    'windows-win32': {
        'pip_tags': ('win32',),
        'tags': ('win32',),
        'tag_must_end': (),
        'env': {'sys_platform': 'win32', 'platform_system': 'Windows',
                'platform_machine': 'x86', 'os_name': 'nt'},
    },
    'windows-arm64': {
        'pip_tags': ('win_arm64',),
        'tags': ('win_arm64',),
        'tag_must_end': (),
        'env': {'sys_platform': 'win32', 'platform_system': 'Windows',
                'platform_machine': 'ARM64', 'os_name': 'nt'},
    },
}
# WINDOWS FIRST, AND THE ORDER IS THE POINT. Kent, 2026-09-23: *"windows is my
# primary concern for 'what might bite me on others' computers?'"* — it is the
# platform with the most installs, the least room to experiment and the least
# ability to build anything locally, so it is the leftmost column, which is the
# one a reader checks first. 32-bit and arm64 Windows are supported but off by
# default: ask for them with --platform when a machine turns up needing them.
DEFAULT_PLATFORMS = ('windows-amd64', 'linux-x86_64', 'macos-arm64',
                     'macos-x86_64')

# Verdicts, worst first. NO COLOUR ANYWHERE — a cell says what it is in
# words, so the table reads the same to everyone and in a pipe.
WHEEL = 'wheel'          # a binary wheel exists: installs with no compiler
SDIST = 'sdist-only'     # source only: needs a compiler on the user's machine
NONE = 'NONE'            # nothing matches the pin and this python
EXTRA = 'extra-index'    # local-version pin; not answerable from PyPI
SKIP = 'n/a'             # its own marker excludes this platform
ERROR = 'error'          # could not ask
RANK = {NONE: 0, ERROR: 1, SDIST: 2, EXTRA: 3, WHEEL: 4, SKIP: 5}


def parse_wheel_tags(filename):
    """`(python tags, abi tags, platform tags)` from a wheel filename, or None.

    PEP 427 names are `dist-version(-build)?-python-abi-platform.whl`, and each
    of the last three may be a dot-separated SET (`cp39.cp310`,
    `macosx_10_9_x86_64.macosx_11_0_arm64`). Splitting from the RIGHT is what
    makes the optional build tag harmless."""
    if not filename.endswith('.whl'):
        return None
    parts = filename[:-4].split('-')
    if len(parts) < 5:
        return None
    pytags, abitags, plattags = parts[-3], parts[-2], parts[-1]
    return (pytags.split('.'), abitags.split('.'), plattags.split('.'))


def python_tag_matches(pytags, abitags, major, minor):
    """Does a wheel's python/abi tag pair run on `major.minor`?

    THE abi3 CASE IS NOT A DETAIL. A `cp39-abi3-win_amd64` wheel runs on 3.9
    and every later 3.x, and several requirements here ship exactly that
    (cryptography is the obvious one). Treating the python tag as an equality
    test would report those as missing on every newer python — the precise
    false alarm this tool exists to avoid."""
    want_cp = 'cp{}{}'.format(major, minor)
    stable_abi = any(t == 'abi3' for t in abitags)
    for tag in pytags:
        tag = tag.strip()
        # `py3` and `py2.py3` arrive here already split on the dot, so the
        # generic tags are just `py{major}` and `py{major}{minor}`.
        if tag in (want_cp, 'py{}'.format(major), 'py{}{}'.format(major, minor)):
            return True
        # abi3: any cp3X tag at or below the target python runs here.
        if stable_abi and tag.startswith('cp{}'.format(major)):
            rest = tag[len('cp{}'.format(major)):]
            if rest.isdigit() and int(rest) <= minor:
                return True
    return False


def platform_tag_matches(plattags, spec):
    """Does a wheel's platform tag belong to one of our targets?"""
    for tag in plattags:
        tag = tag.strip()
        if tag == 'any':
            return True
        if not tag.startswith(spec['tags']):
            continue
        if not spec['tag_must_end']:
            return True
        if tag.endswith(spec['tag_must_end']):
            return True
    return False


class Index(object):
    """PyPI, asked once per project and remembered.

    TWO ENDPOINTS, newest first. The JSON Simple API (PEP 691) is the one
    designed for "what files exist", and it carries `requires-python` per
    file, which is the question that matters most here. The legacy
    `/pypi/<name>/json` is the fallback, because its `releases` key has been
    on the way out for years and a tool that only knows it will eventually
    stop working without saying why."""

    SIMPLE_ACCEPT = ('application/vnd.pypi.simple.v1+json, '
                     'application/vnd.pypi.simple.v1+html;q=0.2')

    def __init__(self, base='https://pypi.org', timeout=30, cache_dir=None,
                 extra=()):
        self.base = base.rstrip('/')
        # EXTRA INDEXES COME FROM THE REQUIREMENTS FILES THEMSELVES. Without
        # them a `torch==2.7.1+cpu` pin can only be reported as unanswerable,
        # which is a gap in the answer rather than a fact about the package.
        self.extra = [u.rstrip('/') for u in extra]
        self.timeout = timeout
        self.cache_dir = cache_dir
        self._seen = {}
        if cache_dir:
            try:
                os.makedirs(cache_dir, exist_ok=True)
            except OSError as e:
                print('   (cache unusable: {})'.format(e), file=sys.stderr)
                self.cache_dir = None

    def _cache_path(self, name):
        safe = ''.join(c if c.isalnum() or c in '-_.' else '_' for c in name)
        return os.path.join(self.cache_dir, safe + '.json')

    def _fetch(self, url, accept=None):
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'modules_by_python_version/2')
        if accept:
            req.add_header('Accept', accept)
        with urllib.request.urlopen(req, timeout=self.timeout) as fh:
            return json.loads(fh.read().decode('utf-8'))

    def files(self, name):
        """`[(filename, requires_python, version), ...]`, or None on failure."""
        key = name.lower()
        if key in self._seen:
            return self._seen[key]
        cached = None
        if self.cache_dir:
            try:
                with open(self._cache_path(key)) as fh:
                    cached = json.load(fh)
            except (OSError, ValueError):
                cached = None
        if cached is not None:
            self._seen[key] = cached
            return cached
        out = self._from_simple(key)
        if out is None:
            out = self._from_legacy(key)
        # Anything the extra indexes hold is ADDED, not substituted: a
        # package can live on both, and the pin decides which file matches.
        for base in self.extra:
            more = self._from_html(base, key)
            if more:
                out = (out or []) + more
        self._seen[key] = out
        if out is not None and self.cache_dir:
            try:
                with open(self._cache_path(key), 'w') as fh:
                    json.dump(out, fh)
            except OSError:
                pass
        return out

    def _from_simple(self, name):
        url = '{}/simple/{}/'.format(self.base, name)
        try:
            data = self._fetch(url, accept=self.SIMPLE_ACCEPT)
        except (urllib.error.URLError, ValueError, OSError):
            return None
        files = data.get('files')
        if files is None:
            return None
        out = []
        for f in files:
            if f.get('yanked'):
                continue          # a yanked file is not installable
            out.append((f.get('filename') or '',
                        f.get('requires-python') or '',
                        ''))      # version is read from the filename below
        return out

    def _from_html(self, base, name):
        """A PEP 503 HTML index — which is what most non-PyPI indexes are.

        `download.pytorch.org/whl/cpu` serves HTML, not the JSON of PEP 691,
        so neither method below can read it. The format is a flat list of
        anchors whose TEXT is the filename; `data-requires-python` carries
        what the JSON API calls `requires-python`. The href is URL-encoded
        (`%2Bcpu`) and the text is not, which is why the text is what gets
        parsed."""
        import re
        url = '{}/{}/'.format(base, normalize(name))
        try:
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'modules_by_python_version/2')
            with urllib.request.urlopen(req, timeout=self.timeout) as fh:
                body = fh.read().decode('utf-8', 'replace')
        except (urllib.error.URLError, OSError, ValueError):
            return []
        out = []
        for tag, text in re.findall(r'(<a\b[^>]*>)([^<]+)</a>', body, re.I):
            fname = text.strip()
            if not fname:
                continue
            m = re.search(r'data-requires-python=["\']([^"\']*)["\']', tag,
                          re.I)
            requires = m.group(1).replace('&gt;', '>').replace('&lt;', '<') \
                if m else ''
            out.append((fname, requires, ''))
        return out

    def _from_legacy(self, name):
        url = '{}/pypi/{}/json'.format(self.base, name)
        try:
            data = self._fetch(url)
        except (urllib.error.URLError, ValueError, OSError):
            return None
        releases = data.get('releases')
        if releases is None:
            return None
        out = []
        for version, items in releases.items():
            for f in items or []:
                if f.get('yanked'):
                    continue
                out.append((f.get('filename') or '',
                            f.get('requires_python') or '',
                            version))
        return out


def version_of(filename, fallback=''):
    """The release version a distribution filename belongs to."""
    if fallback:
        return fallback
    name = filename
    for suffix in ('.whl', '.tar.gz', '.zip', '.tar.bz2'):
        if name.endswith(suffix):
            name = name[:-len(suffix)]
            break
    parts = name.split('-')
    return parts[1] if len(parts) > 1 else ''


def read_requirements(paths):
    """Every requirement in every file, as `(Requirement, source, raw)`.

    Requirements files are not PEP 508 files: they carry pip options, `-r`
    includes, and trailing `# comments` that `Requirement()` will not parse.
    Anything unrecognised is REPORTED rather than dropped silently, because a
    dependency this tool quietly skipped is one nobody checked."""
    found, problems, seen, indexes = [], [], set(), []
    queue = list(paths)
    while queue:
        path = queue.pop(0)
        if path in seen:
            continue
        seen.add(path)
        try:
            with open(path, encoding='utf-8') as fh:
                lines = fh.readlines()
        except OSError as e:
            problems.append((path, '', str(e)))
            continue
        for raw in lines:
            line = raw.strip()
            if not line or line.startswith('#'):
                continue
            if line.startswith(('-r ', '--requirement ')):
                inc = line.split(None, 1)[1].strip()
                queue.append(os.path.join(os.path.dirname(path) or '.', inc))
                continue
            if line.startswith('-'):
                # HARVEST THE INDEXES RATHER THAN DISCARDING THEM. A
                # requirements file that says where its packages live has
                # already answered the question; asking the user to repeat it
                # on the command line is asking for something we are holding
                # (Kent, 2026-09-23: "any advantage to making the user pass
                # --pip-extra-index-url ...?" — none). Harvesting it is also
                # what makes the `+cpu` torch pin answerable at all.
                bits = line.replace('=', ' ').split()
                if len(bits) > 1 and bits[0] in ('-i', '--index-url',
                                                 '--extra-index-url'):
                    indexes.append(bits[1].strip())
                continue
            if ' #' in line:
                line = line.split(' #', 1)[0].strip()
            if line.endswith('\\'):
                line = line[:-1].strip()
            if not line:
                continue
            try:
                found.append((Requirement(line), path, line))
            except InvalidRequirement as e:
                problems.append((path, line, str(e)))
    return found, problems, indexes


def applies_here(req, platform_name, major, minor, patch=0):
    """Does this requirement's own marker include this platform and python?"""
    if req.marker is None:
        return True
    env = dict(PLATFORMS[platform_name]['env'])
    env['python_version'] = '{}.{}'.format(major, minor)
    env['python_full_version'] = '{}.{}.{}'.format(major, minor, patch)
    env['implementation_name'] = 'cpython'
    env['platform_python_implementation'] = 'CPython'
    env['extra'] = ''
    try:
        return bool(req.marker.evaluate(env))
    except UndefinedEnvironmentName:
        return True         # an unknown key is not a reason to skip a check


def judge(req, files, platform_name, major, minor, patch=0):
    """`(verdict, detail)` for one requirement on one platform and python.

    PATCH LEVEL IS ALMOST NEVER RELEVANT, AND THE EXCEPTION IS HERE. Wheel
    tags carry only major and minor (`cp313-cp313-win_amd64`), because
    CPython's ABI is stable across a minor series — so a wheel built against
    3.13.0 loads on 3.13.15 and the patch number cannot change whether a
    wheel exists. `Requires-Python` is the one place it can matter: a project
    may declare `>=3.9.2`, or exclude a single broken patch release. The
    sweep assumes `.0`, which is the CONSERVATIVE end — it can report a
    blocker that a later patch would not have — and `--python X.Y.Z` asks
    about an exact release when that matters."""
    if not applies_here(req, platform_name, major, minor, patch):
        return SKIP, 'excluded by its own marker'
    if files is None:
        return ERROR, 'could not reach the index'
    spec = PLATFORMS[platform_name]
    target = Version('{}.{}.{}'.format(major, minor, patch))
    best, detail = NONE, 'no release matching the pin'
    saw_any_version = False
    for filename, requires_python, version in files:
        ver = version_of(filename, version)
        if ver:
            try:
                if not req.specifier.contains(Version(ver), prereleases=True):
                    continue
            except InvalidVersion:
                continue
        saw_any_version = True
        if requires_python:
            try:
                if not SpecifierSet(requires_python).contains(target,
                                                              prereleases=True):
                    continue
            except (InvalidSpecifier, InvalidVersion):
                pass        # an unparseable Requires-Python does not exclude
        tags = parse_wheel_tags(filename)
        if tags is None:
            if RANK[SDIST] > RANK[best]:
                best, detail = SDIST, 'source distribution only'
            continue
        pytags, abitags, plattags = tags
        if not python_tag_matches(pytags, abitags, major, minor):
            continue
        if not platform_tag_matches(plattags, spec):
            continue
        return WHEEL, filename
    if best is NONE and any('+' in str(s.version) for s in req.specifier):
        # A LOCAL-VERSION PIN LIVES ON ANOTHER INDEX. Reported as its own
        # verdict rather than as "missing", which would be a gap in the
        # answer dressed up as a fact about the package. If the requirements
        # files name that index, it has already been searched and this does
        # not fire.
        return EXTRA, 'local-version pin; not found on the indexes searched'
    if best is NONE and saw_any_version:
        detail = 'releases exist, but none for this python and platform'
    return best, detail


def collect(requirements, index, platforms, major, minor, quiet=False,
            patch=0):
    """`{requirement name: {platform: (verdict, detail)}}`."""
    table = {}
    for req, source, raw in requirements:
        if not quiet:
            print('   asking about {}'.format(req.name), file=sys.stderr)
        files = index.files(req.name)
        row = {}
        for platform_name in platforms:
            row[platform_name] = judge(req, files, platform_name, major, minor,
                                       patch)
        table[str(req)] = {'req': req, 'source': source, 'row': row}
    return table


def worst(row):
    return min((RANK[v] for v, _ in row.values()), default=RANK[SKIP])


def row_label(entry):
    """`name` plus its pin — NOT the bare name.

    THE BARE NAME LIES WHEN TWO FILES DISAGREE. Reading `requirements.txt` and
    an archived `requirements_preAug2025.txt` together gives two rows both
    printed as `lxml`, one of them pinned to a 2022 release with no wheel for
    a current python — so the table showed `lxml  sdist-only` and looked like
    a finding about the dependency rather than about the file it came from
    (Kent's first run, 2026-09-23). The pin is what tells them apart, and the
    source column beside it says which file to go and fix.

    EXTRAS BELONG IN THE LABEL TOO. `requirements-webview.txt` asks for
    `pywebview`, `pywebview[gtk]` and `pywebview[qt]`; `Requirement.name`
    drops the extras, so all three printed as a bare `pywebview` and the OK
    list showed the same word three times with no way to tell which was
    which (Kent's run, 2026-09-23).

    THE MARKER IS NOT IN HERE, and putting it in was a mistake worth
    recording. `requirements.txt` carries two torch lines differing only by
    marker, and overridden to the same version they printed as identical
    text. The fix applied first was to append the marker to EVERY label —
    which turned the OK list into a wall and pushed the table past 100
    columns, to disambiguate two rows out of thirty-seven (Kent, 2026-09-23:
    "I don't get what you have done here, if anything, and I feel like we're
    wasting time"). Disambiguation belongs where the collision is, so
    `print_table` appends `marker_hint` ONLY to labels that would otherwise
    be identical."""
    req = entry['req']
    return plain_name(req) + str(req.specifier)


def plain_name(req):
    """Just the name, with extras. What a reader scans a list for."""
    extras = '[{}]'.format(','.join(sorted(req.extras))) if req.extras else ''
    return req.name + extras


def marker_hint(req, width=24):
    """A short tail that tells two otherwise-identical labels apart."""
    if req.marker is None:
        return ''
    hint = ' '.join(str(req.marker).replace('"', '').replace("'", '').split())
    for noise in ('sys_platform ', 'platform_machine ', 'python_version '):
        hint = hint.replace(noise, '')
    return ' ;' + (hint[:width - 1] + '…' if len(hint) > width else hint)


def print_table(table, platforms, label, show_all, show_source=True):
    # COLLISION-ONLY DISAMBIGUATION. Two requirements can share a name, a pin
    # and their extras, differing only by marker — the two torch lines do. The
    # marker goes on those rows and nowhere else, so one ambiguity does not
    # cost every other row its readability. See `row_label`.
    labels = {k: row_label(e) for k, e in table.items()}
    seen = {}
    for value in labels.values():
        seen[value] = seen.get(value, 0) + 1
    for key, entry in table.items():
        if seen[labels[key]] > 1:
            labels[key] += marker_hint(entry['req'])
    name_width = max([len('requirement')]
                     + [len(v) for v in labels.values()]) + 2
    widths = [max(len(p), 11) + 2 for p in platforms]
    header = 'requirement'.ljust(name_width)
    header += ''.join(p.ljust(w) for p, w in zip(platforms, widths))
    if show_source:
        header += 'from'
    print('\n' + label)
    print(header)
    print('-' * len(header))
    rows = sorted(table.items(), key=lambda kv: (worst(kv[1]['row']),
                                                 kv[1]['req'].name.lower()))
    shown, ok, na = 0, [], []
    for key, entry in rows:
        verdicts = {v for v, _d in entry['row'].values()}
        if verdicts == {SKIP}:
            # Excluded by its own marker on EVERY platform asked about, so it
            # was not really checked here. Saying "OK" would overclaim.
            # NAMES ONLY in these two lists: they are read to confirm that
            # something WAS checked, not to identify a row, so pins and
            # markers are noise there.
            na.append(plain_name(entry['req']))
            continue
        if not show_all and worst(entry['row']) >= RANK[WHEEL]:
            ok.append(plain_name(entry['req']))
            continue
        line = labels[key].ljust(name_width)
        line += ''.join(v.ljust(w) for (v, _d), w
                        in zip((entry['row'][p] for p in platforms), widths))
        if show_source:
            line += os.path.basename(entry['source'])
        print(line)
        shown += 1
        ok.append(None)          # placeholder; it is in the table above
    if not shown:
        print('   (nothing above — see OK below)')
    # EVERYTHING ELSE, BY NAME. A table that lists only problems cannot be
    # told apart from one that quietly failed to check things (Kent,
    # 2026-09-23: "are those eight rows the only ones with problems? If so, it
    # would be good to list everything else checked under ---OK----"). So the
    # rest are named, not merely counted.
    ok = sorted({x for x in ok if x}, key=str.lower)
    if ok:
        print('\n--- OK: a wheel everywhere it applies ({}) ---'
              .format(len(ok)))
        for line in textwrap.wrap(', '.join(ok), width=76):
            print('   ' + line)
    if na:
        na = sorted(set(na), key=str.lower)
        print('\n--- NOT CHECKED HERE: excluded by their own markers on every '
              'platform asked about ({}) ---'.format(len(na)))
        for line in textwrap.wrap(', '.join(na), width=76):
            print('   ' + line)


def print_details(table, platforms):
    print('\nWhy, for anything that is not a plain wheel:')
    for _key, entry in sorted(table.items(),
                              key=lambda kv: kv[1]['req'].name.lower()):
        lines = []
        for p in platforms:
            verdict, detail = entry['row'][p]
            if verdict is WHEEL:
                continue
            lines.append('      {}: {} — {}'.format(p, verdict, detail))
        if lines:
            print('   {}  (from {})'.format(entry['req'], entry['source']))
            print('\n'.join(lines))


def blockers(table, platforms, count_sdist=False):
    """`[(name, platform, verdict), ...]` for anything that will not install.

    `n/a` and `extra-index` are never blockers: the first is a requirement
    excluded by its own marker, the second is a pin this index cannot answer
    for. Counting either would make a clean python look broken."""
    out = []
    for _key, entry in table.items():
        for p in platforms:
            verdict, _detail = entry['row'][p]
            if verdict in (NONE, ERROR) or (count_sdist and verdict is SDIST):
                out.append((row_label(entry), p, verdict))
                break
    return out


# Packages RELEASED AS A MATCHED SET, which therefore have to move together.
# The versions are not equal across a family and cannot be checked by
# arithmetic — torch 2.7.1 goes with torchvision 0.22.1 and torchaudio 2.7.1,
# a mapping only PyTorch publishes. What CAN be checked is that they move
# together, because each sibling pins an exact torch, so pip's own resolve
# rejects a mismatched set. Hence: no matrix here, just a warning when a
# what-if moves one member and leaves the others behind (Kent, 2026-09-23:
# "torch, torchvision and touchaudio need to be aligned"). Add more with
# --align.
ALIGNED_FAMILIES = [('torch', 'torchvision', 'torchaudio')]


def family_of(name, families):
    key = normalize(name)
    for fam in families:
        if key in {normalize(n) for n in fam}:
            return fam
    return None


def normalize(name):
    """PEP 503 name normalization, for comparing package names safely."""
    import re
    return re.sub(r'[-_.]+', '-', name).lower()


def via_pip(paths, platforms, version, index_url=None, extra_index=None,
            verbose=False, allow_sdist=(), requirements=None, indexes=()):
    """THE AUTHORITATIVE PASS — and the only one that sees CO-REQUISITES.

    WHY IT HAD TO EXIST (Kent, 2026-09-23: *"are you considering corequisites
    of torch, python, and related modules?"* — the answer was no, and that
    made every other number in this tool optimistic). Everything above reads
    the requirements files and asks PyPI about THOSE names. It never resolves
    what they in turn require. That is not a corner case here: every install
    disaster `requirements.txt` records was caused by a dependency nobody
    listed.

      * `openai_whisper` was excluded on Intel macOS because **numba**, its
        dependency, had no python-3.13 wheel there.
      * `numpy<2.5` is pinned because **numba** requires numpy<2.5 — a
        transitive constraint that forced a direct pin to stop pip going
        ResolutionImpossible.
      * `allosaurus` is Linux-only because **editdistance**, its C-extension
        dependency, had no Windows py3.13 wheel and "killed the whole -r".

    A declared-requirements scan would have called all three fine. So this
    hands the job to the one thing that does it properly: pip's own resolver,
    cross-targeted with `--python-version` and `--platform`, refusing source
    builds so anything without a wheel FAILS rather than silently compiling.
    `--dry-run` means nothing is installed. The same idea as the macOS
    installer's `--check-wheels`, widened to every platform and any python.

    It is not the default because it is slow (a full resolve per platform)
    and needs a network and a pip new enough for `--dry-run`. The fast scan
    stays useful as a first pass: it names the direct requirement to look at,
    which pip's error output often does not."""
    import re
    import subprocess
    import tempfile
    print('\n' + '=' * 72)
    print('PIP RESOLVE (includes co-requisites) — python {}'.format(version))
    print('=' * 72)
    skip = {normalize(n) for n in (allow_sdist or ())}
    if skip:
        print('\nSet aside (no wheel by their own choice, checked '
              'separately): {}'.format(', '.join(sorted(skip))))
    try:
        major, minor = int(version.split('.')[0]), int(version.split('.')[1])
        patch = int(version.split('.')[2]) if version.count('.') > 1 else 0
    except (IndexError, ValueError):
        sys.exit('--via-pip wants X.Y or X.Y.Z, not {!r}'.format(version))

    def req_text(req):
        extras = ('[{}]'.format(','.join(sorted(req.extras)))
                  if req.extras else '')
        return req.name + extras + str(req.specifier)

    def requirements_for(platform_name):
        """A requirements file holding only what applies to THIS target.

        PIP EVALUATES MARKERS AGAINST THE MACHINE IT RUNS ON, not against
        `--platform`. `--platform` selects which wheel TAGS are acceptable
        and nothing more, so on a Linux box a
        `torch==2.7.1+cpu; sys_platform != "darwin"` line is still required
        during a `--platform macosx_11_0_arm64` run — and duly fails, because
        macOS has no +cpu build. That is what produced both macOS failures
        (Kent's run, 2026-09-23), and it cuts the other way too: the Windows
        run was carrying `allosaurus; sys_platform == "linux"`, so it was
        answering a harder question than reality asks.

        So the markers are evaluated HERE, against the real target, and the
        file handed to pip carries only the applicable lines with their
        markers already resolved away. pip is then asked exactly the question
        we mean."""
        out = []
        for url in (indexes or []):
            out.append('--extra-index-url {}'.format(url))
        for req, _source, _raw in (requirements or []):
            if normalize(req.name) in skip:
                continue
            if not applies_here(req, platform_name, major, minor, patch):
                continue
            out.append(req_text(req))
        handle = tempfile.NamedTemporaryFile('w', suffix='.txt', delete=False,
                                             encoding='utf-8')
        handle.write('\n'.join(out) + '\n')
        handle.close()
        return handle.name

    failures, sdists, temps, declared = [], {}, [], set()
    for name in platforms:
        tags = PLATFORMS[name].get('pip_tags') or ()
        if not tags:
            print('\n{}: no pip platform tags defined; skipped'.format(name))
            continue
        with tempfile.TemporaryDirectory() as target:
            report = os.path.join(target, 'report.json')
            cmd = [sys.executable, '-m', 'pip', 'install', '--dry-run',
                   '--report', report,
                   '--only-binary=:all:', '--python-version', version,
                   '--implementation', 'cp', '--target',
                   os.path.join(target, 'x')]
            for tag in tags:
                cmd += ['--platform', tag]
            if index_url:
                cmd += ['--index-url', index_url]
            if extra_index:
                cmd += ['--extra-index-url', extra_index]
            reqfile = requirements_for(name)
            temps.append(reqfile)
            cmd += ['-r', reqfile]
            print('\n{}:'.format(name))
            if verbose:
                print('   ' + ' '.join(cmd))
            try:
                done = subprocess.run(cmd, capture_output=True, text=True)
            except OSError as e:
                print('   could not run pip: {}'.format(e))
                failures.append((name, str(e)))
                continue
            if done.returncode != 0:
                failures.append((name, (done.stderr or '').strip()))
                print('   FAILED. pip says:')
                for line in [l for l in (done.stderr or '').splitlines()
                             if l.strip()][-8:]:
                    print('      ' + line)
                for missing in re.findall(
                        r'satisfies the requirement ([A-Za-z0-9._-]+)',
                        done.stderr or ''):
                    if normalize(missing) not in skip:
                        print('   → {} has no wheel here. If that is known '
                              'and it is pure python, re-run with '
                              '--allow-sdist {} so pip can get past it and '
                              'check everything behind it.'.format(missing,
                                                                   missing))
                continue
            # THE PAYOFF: the report names every distribution pip resolved,
            # co-requisites included, so the check can be SHOWN rather than
            # asserted.
            try:
                with open(report) as fh:
                    data = json.load(fh)
                installs = data.get('install') or []
            except (OSError, ValueError):
                installs = []
            names = []
            for item in installs:
                meta = item.get('metadata') or {}
                url = ((item.get('download_info') or {}).get('url') or '')
                pkg = meta.get('name') or '?'
                names.append(pkg)
                if not url.endswith('.whl'):
                    sdists.setdefault(pkg, []).append(name)
            declared.update(names)
            print('   OK — {} distributions resolved, wheels throughout'
                  .format(len(names)))
    for path in temps:
        try:
            os.unlink(path)
        except OSError:
            pass
    print('')
    if declared:
        print('Co-requisites were included: {} distinct distributions were '
              'resolved, not just the {} lines you listed.'.format(
                  len(declared), 'requirement'))
    if sdists:
        print('Resolved as source rather than a wheel:')
        for pkg, where in sorted(sdists.items()):
            print('   {} ({})'.format(pkg, ', '.join(where)))
    if failures:
        print('{} of {} platform(s) did not resolve on python {}.'.format(
            len(failures), len(platforms), version))
    else:
        print('Every platform resolves on python {}, co-requisites included.'
              .format(version))
    return len(failures)


def pip_resolve(lines, platform_name, version, extra_index=None):
    """One cross-targeted pip resolve. `(ok, {name: version}, stderr)`.

    Shares its shape with `via_pip`'s inner loop deliberately rather than
    being called from it: that one reports per platform as it goes, this one
    is called dozens of times by `audit_pins` and must stay silent."""
    import subprocess
    import tempfile
    tags = PLATFORMS[platform_name].get('pip_tags') or ()
    if not tags:
        return False, {}, 'no pip platform tags for {}'.format(platform_name)
    with tempfile.TemporaryDirectory() as work:
        reqfile = os.path.join(work, 'r.txt')
        with open(reqfile, 'w', encoding='utf-8') as fh:
            fh.write('\n'.join(lines) + '\n')
        report = os.path.join(work, 'report.json')
        cmd = [sys.executable, '-m', 'pip', 'install', '--dry-run',
               '--report', report, '--only-binary=:all:',
               '--python-version', version, '--implementation', 'cp',
               '--target', os.path.join(work, 'x')]
        for tag in tags:
            cmd += ['--platform', tag]
        if extra_index:
            cmd += ['--extra-index-url', extra_index]
        cmd += ['-r', reqfile]
        try:
            done = subprocess.run(cmd, capture_output=True, text=True)
        except OSError as e:
            return False, {}, str(e)
        if done.returncode != 0:
            return False, {}, (done.stderr or '').strip()
        chosen = {}
        try:
            with open(report) as fh:
                for item in (json.load(fh).get('install') or []):
                    meta = item.get('metadata') or {}
                    if meta.get('name'):
                        chosen[normalize(meta['name'])] = meta.get('version',
                                                                   '?')
        except (OSError, ValueError) as e:
            return True, {}, 'resolved, but the report was unreadable: '\
                             '{}'.format(e)
        return True, chosen, ''


def audit_pins(requirements, platform_name, version, indexes=(),
               extra_index=None, quiet=False, allow_sdist=()):
    """WHICH OF OUR OWN PINS ARE STILL EARNING THEIR PLACE?

    Kent, 2026-09-23, on `numpy>=2.1,<2.5`: *"We want to be able to
    re-evaluate lines like this ... otherwise, we will just be kept in place
    by our own req.txt."* Exactly so. That cap was written because numba
    required numpy<2.5 at a moment in time, and its own comment says "Recheck
    when numba's cap moves" — but nothing rechecks, so the workaround
    outlives the problem and quietly becomes the problem.

    The method is to remove ONE pin at a time and re-resolve:

      * resolve fails without it        → LOAD-BEARING. Keep it.
      * same version chosen without it  → REDUNDANT. Something else in the
                                          tree already enforces this, so the
                                          line is documentation, not a
                                          constraint. Safe to relax.
      * a HIGHER version chosen         → HOLDING US BACK. The constraint it
                                          recorded has lifted.

    The third case is the one worth having. The second is worth knowing too:
    a redundant pin is harmless until the day it disagrees with the thing
    actually enforcing the rule.
    """
    head = ['--extra-index-url {}'.format(u) for u in (indexes or [])]
    # THE SAME SET-ASIDE THE PIP PASS USES. Without it the baseline resolve
    # fails on a package we already know publishes no wheel, and the audit
    # reports "nothing to audit against" — which is what happened on the
    # first run (Kent, 2026-09-23): the pip pass had set openai_whisper aside
    # and this had not, so the two disagreed about the same requirements.
    skip = {normalize(n) for n in (allow_sdist or ())}
    applicable = [(req, s, r) for (req, s, r) in requirements
                  if normalize(req.name) not in skip
                  and applies_here(req, platform_name,
                                   int(version.split('.')[0]),
                                   int(version.split('.')[1]))]
    if skip:
        print('\nNot audited (set aside, no wheel published): {}'.format(
            ', '.join(sorted(skip))))

    def text(req, drop=False):
        extras = ('[{}]'.format(','.join(sorted(req.extras)))
                  if req.extras else '')
        return req.name + extras + ('' if drop else str(req.specifier))

    print('\n' + '=' * 72)
    print('PIN AUDIT — python {} on {}'.format(version, platform_name))
    print('=' * 72)
    base_lines = head + [text(r) for r, _s, _raw in applicable]
    ok, baseline, err = pip_resolve(base_lines, platform_name, version,
                                    extra_index)
    if not ok:
        print('\nThe requirements as written do not resolve here, so there '
              'is nothing to audit against:')
        for line in (err or '').splitlines()[-6:]:
            print('   ' + line)
        return 1
    print('\nBaseline resolves: {} distributions.'.format(len(baseline)))
    pinned = [(r, s, raw) for (r, s, raw) in applicable if str(r.specifier)]
    if not pinned:
        print('No pinned requirements to audit.')
        return 0
    verdicts = []
    for req, _source, _raw in pinned:
        if not quiet:
            print('   trying without {}{}'.format(req.name, req.specifier),
                  file=sys.stderr)
        lines = head + [text(r, drop=(r is req)) for r, _s, _raw in applicable]
        ok2, chosen, err2 = pip_resolve(lines, platform_name, version,
                                        extra_index)
        key = normalize(req.name)
        was = baseline.get(key, '?')
        if not ok2:
            verdicts.append((req, 'LOAD-BEARING', was, '',
                             'without it nothing resolves'))
            continue
        now = chosen.get(key, '?')
        if now == was:
            verdicts.append((req, 'redundant', was, now,
                             'the tree already enforces this'))
        else:
            try:
                higher = Version(now) > Version(was)
            except InvalidVersion:
                higher = False
            verdicts.append((
                req, 'HOLDING US BACK' if higher else 'changes the answer',
                was, now,
                'unpinned this resolves to {}'.format(now)))
    order = {'HOLDING US BACK': 0, 'changes the answer': 1, 'redundant': 2,
             'LOAD-BEARING': 3}
    print('')
    fmt = '{:<28}{:<18}{:<12}{}'
    print(fmt.format('pin', 'verdict', 'now', 'without it'))
    print('-' * 76)
    for req, verdict, was, now, why in sorted(verdicts,
                                              key=lambda v: order[v[1]]):
        print(fmt.format((req.name + str(req.specifier))[:27], verdict,
                         was, why))
    loose = [v for v in verdicts if v[1] == 'HOLDING US BACK']
    if loose:
        print('\n{} pin(s) are holding this project below what the ecosystem '
              'now allows. Each one was written for a reason; check whether '
              'that reason still holds before relaxing it — the comment '
              'beside it in the requirements file usually says.'
              ''.format(len(loose)))
    else:
        print('\nNo pin is holding you back on this platform and python.')
    return 0


def blocking_packages(table, platforms, count_sdist=False):
    """`{requirement label: [platforms it fails on]}` — ALL of them.

    Unlike `blockers()`, which stops at the first bad platform because it is
    counting affected REQUIREMENTS, this keeps every platform, because "what
    are we waiting on" is answered by naming the package and saying where it
    is missing."""
    out = {}
    for _key, entry in table.items():
        for p in platforms:
            verdict, _detail = entry['row'][p]
            if verdict in (NONE, ERROR) or (count_sdist and verdict is SDIST):
                out.setdefault(row_label(entry), []).append(p)
    return out


def entry_for_label(table, label):
    for _key, entry in table.items():
        if row_label(entry) == label:
            return entry
    return None


def versions_supporting(index, req, platform_name, major, minor, patch=0):
    """Versions of this package that DO have a matching wheel — IGNORING our
    pin. Sorted, newest last.

    THIS IS THE DIFFERENCE BETWEEN A BLOCKER AND A CO-MOVE, and the tool could
    not tell them apart until now (Kent, 2026-09-23): *"if there's a more
    recent version of torch, but we need to have a higher python version to
    use it, then torch isn't blocking us from moving up python; we just need
    to do them in synch."* Precisely. A pinned release can never gain wheels
    for a python published after it, so an exact old pin ALWAYS looks like a
    blocker at some future python — when what it really means is that the two
    move together. Only when NO version of the package has a wheel for that
    python is upstream actually the thing being waited on."""
    files = index.files(req.name) if index else None
    if not files:
        return []
    spec = PLATFORMS[platform_name]
    target = Version('{}.{}.{}'.format(major, minor, patch))
    good = set()
    for filename, requires_python, version in files:
        ver = version_of(filename, version)
        if not ver:
            continue
        if requires_python:
            try:
                if not SpecifierSet(requires_python).contains(
                        target, prereleases=True):
                    continue
            except (InvalidSpecifier, InvalidVersion):
                pass
        tags = parse_wheel_tags(filename)
        if tags is None:
            continue
        pytags, abitags, plattags = tags
        if not python_tag_matches(pytags, abitags, major, minor):
            continue
        if not platform_tag_matches(plattags, spec):
            continue
        good.add(ver)

    def key(v):
        try:
            return (0, Version(v))
        except InvalidVersion:
            return (1, v)
    return sorted(good, key=key)


def report_versions(index, requirements, names, platforms, versions):
    """WHICH VERSIONS OF THIS PACKAGE WORK ON WHICH PYTHON — asked directly.

    Kent, 2026-09-23: *"Does this show which torch versions are consistent
    with python3.13? what do you think we're trying for right now?"* It did
    not, and that is the question the whole session is actually for: torch is
    the only thing gating the ceiling, so choosing a python and choosing a
    torch are one decision, and nothing was listing the candidates.

    Everything else here asks "does the PINNED version work". This ignores
    the pin and asks what is on offer, which is what you need in order to
    change the pin."""
    by_name = {}
    for req, _source, _raw in requirements:
        by_name.setdefault(normalize(req.name), req)
    for raw in names:
        req = by_name.get(normalize(raw))
        if req is None:
            req = Requirement(raw)
        print('\n' + '=' * 72)
        print('{} — versions publishing a wheel (the pin is IGNORED here)'
              ''.format(req.name))
        print('=' * 72)
        head = '{:<9}{:<17}{:<7}{:<12}{}'.format('python', 'platform',
                                                 'count', 'oldest', 'newest')
        print('\n' + head)
        print('-' * len(head))
        for major, minor in versions:
            per = {}
            for platform_name in platforms:
                per[platform_name] = versions_supporting(index, req,
                                                         platform_name,
                                                         major, minor)
            first = True
            for platform_name in platforms:
                got = per[platform_name]
                print('{:<9}{:<17}{:<7}{:<12}{}'.format(
                    '{}.{}'.format(major, minor) if first else '',
                    platform_name, len(got),
                    got[0] if got else '—', got[-1] if got else '—'))
                first = False
            # COMPARE PUBLIC VERSIONS, AND SKIP PLATFORMS THAT HAVE NONE.
            # Both matter, and without them this line is useless. The CPU
            # index labels its builds `2.14.0+cpu` while macOS publishes a
            # plain `2.14.0`, so a set intersection over the raw strings is
            # empty even when every platform has the same release. And a
            # platform with NO versions at all (Intel macOS has no torch
            # since 2.2.x) would zero the intersection for everyone,
            # reporting "none" when the requirements file already excludes
            # that platform by marker. So: strip the local label, intersect
            # only over platforms that have something, and name the ones left
            # out (Kent, 2026-09-23, reading "on EVERY platform: none" for
            # both 3.13 and 3.14).
            have = {p: {public(v) for v in got} for p, got in per.items()
                    if got}
            empty = [p for p, got in per.items() if not got]
            common = None
            for got in have.values():
                common = set(got) if common is None else common & got
            common = sorted(common or [], key=lambda v: (0, Version(v))
                            if _isver(v) else (1, v))
            where = 'on {}'.format(', '.join(have)) if empty else \
                    'on EVERY platform listed'
            note = ' (none at all on {})'.format(', '.join(empty)) if empty \
                else ''
            print('{:<9}{}'.format('', '→ {}: {}{}'.format(
                where,
                '{} … {} ({})'.format(common[0], common[-1], len(common))
                if common else 'none', note)))
        # ACROSS EVERY PYTHON, NOT JUST ONE. A single pin has to serve the
        # whole supported range at once: the RUNTIME FLOOR, because existing
        # installs re-resolve requirements.txt on every update, and the
        # INSTALL TARGET, because that is what new machines get. Those are
        # different numbers (ADR 0005 D10), so the usable pins are the
        # intersection down the whole table, not the best row in it.
        spans = []
        for major, minor in versions:
            got = set()
            for platform_name in platforms:
                got |= {public(v) for v in
                        versions_supporting(index, req, platform_name,
                                            major, minor)}
            if got:
                spans.append(got)
        across = set.intersection(*spans) if spans else set()
        across = sorted(across, key=lambda v: (0, Version(v))
                        if _isver(v) else (1, v))
        print('\n   ACROSS EVERY PYTHON IN THE RANGE: {}'.format(
            '{} … {} ({} version(s))'.format(across[0], across[-1],
                                             len(across))
            if across else
            'NONE — no single pin covers the whole range, so the range '
            'itself has to narrow, or the pin needs a python marker'))
    print('\nVersions are shown as published; the arrow lines compare PUBLIC '
          'versions, so a\n`+cpu` build from the extra index and a plain macOS '
          'build of the same release\ncount as the same version. A platform '
          'with none at all needs a marker, which\nis why requirements.txt '
          'already splits torch across two lines.')


def public(text):
    """A version without its local build label: `2.14.0+cpu` → `2.14.0`."""
    try:
        return Version(text).public
    except InvalidVersion:
        return text.split('+', 1)[0]


def _isver(text):
    try:
        Version(text)
        return True
    except InvalidVersion:
        return False


def report_waiting(rows, platforms, index=None):
    """WHAT ARE WE WAITING ON TO MIGRATE UP?

    Kent, 2026-09-23. The two bests say where we can be today; this says what
    would have to happen to go further, and names it.

    TWO CANDIDATES, because "next" has two meanings and he named both:

      * the next NUMBERED version, however many holes it has;
      * the higher version with the FEWEST holes, which need not be the next
        number — *"not everything is compiled for every version, and the next
        to become available might not be v+1"*. That is right, and it is why
        this reports the whole range rather than only v+1: a package can skip
        a python entirely and publish for the one after, so the cheapest move
        up is sometimes two steps, not one.
    """
    clear = None
    for i, r in enumerate(rows):
        if not r['missing']:
            clear = i
    higher = rows[clear + 1:] if clear is not None else rows
    print('\n' + '=' * 72)
    print('WHAT WE ARE WAITING ON TO MIGRATE UP')
    print('=' * 72)
    if clear is None:
        print('\nNothing in the range installs cleanly, so there is no '
              'baseline to move up FROM. Fix the lowest version first.')
    elif not higher:
        print('\n{} is the top of --range and it is already clear. Widen '
              '--range to look further up.'.format(rows[clear]['version']))
        return
    else:
        print('\nClear today: python {}'.format(rows[clear]['version']))
    head = '{:<9}{:<12}{}'.format('python', 'blocked-by', 'what, and where')
    print('\n' + head)
    print('-' * max(len(head), 60))
    for r in higher:
        names = sorted(r['blocking'], key=str.lower)
        if not names:
            print('{:<9}{:<12}{}'.format(r['version'], 0,
                                         'nothing — this one is clear too'))
            continue
        first = True
        major, minor = (int(x) for x in r['version'].split('.')[:2])
        for name in names:
            where = r['blocking'][name]
            label = '{:<9}{:<12}'.format(r['version'] if first else '',
                                         len(names) if first else '')
            print('{}{} ({})'.format(label, name, ', '.join(where)))
            first = False
            # IS IT THE PACKAGE, OR IS IT OUR PIN? Ask what versions DO have a
            # wheel here, ignoring what we pinned.
            entry = entry_for_label(r['table'], name)
            if entry is None or index is None:
                continue
            usable = versions_supporting(index, entry['req'], where[0],
                                         major, minor)
            if usable:
                r.setdefault('comove', []).append((name, usable[-1]))
                print('{:<21}→ NOT upstream: {} {} has a wheel here. This is '
                      'a CO-MOVE, not a wait — python and this package go up '
                      'together.'.format('', entry['req'].name, usable[-1]))
            else:
                r.setdefault('upstream', []).append(name)
                print('{:<21}→ a real wait: NO version of {} has a wheel for '
                      'python {} on {}.'.format('', entry['req'].name,
                                                r['version'], where[0]))
    nxt = higher[0]
    fewest = min(higher, key=lambda r: len(r['blocking']))
    print('')
    comove = nxt.get('comove') or []
    upstream = nxt.get('upstream') or []
    print('Next numbered version is {}:'.format(nxt['version']))
    if comove:
        print('   CO-MOVE (ours to schedule, not to wait for): {}'.format(
            ', '.join('{} → {}'.format(n.split('=')[0].split('<')[0]
                                       .split('>')[0], v)
                      for n, v in comove)))
        print('   Try it with: --override {}'.format(' --override '.join(
            '{}=={}'.format(n.split('=')[0].split('<')[0].split('>')[0], v)
            for n, v in comove)))
    if upstream:
        print('   WAITING ON UPSTREAM: {}'.format(', '.join(upstream)))
    if not comove and not upstream:
        print('   nothing blocks it')
    if fewest is not nxt and len(fewest['blocking']) < len(nxt['blocking']):
        print('FEWEST holes above the baseline is {}, needing: {}'.format(
            fewest['version'],
            ', '.join(sorted(fewest['blocking'], key=str.lower)) or 'nothing'))
        print('   — so the cheapest move up is not the next number. That '
              'happens when a package skips a python and publishes for the '
              'one after.')
    else:
        print('No higher version has fewer holes than the next number, so '
              'there is no cheaper jump to make.')


def parse_range(spec):
    """`3.9-3.14` → `[(3,9), ... (3,14)]`. One major version at a time."""
    try:
        lo, hi = spec.split('-')
        lomaj, lomin = (int(x) for x in lo.split('.')[:2])
        himaj, himin = (int(x) for x in hi.split('.')[:2])
    except ValueError:
        sys.exit('--range wants X.Y-X.Z, e.g. 3.9-3.14')
    if lomaj != himaj:
        sys.exit('--range cannot cross major versions')
    if himin < lomin:
        sys.exit('--range is backwards')
    return [(lomaj, m) for m in range(lomin, himin + 1)]


def find_highest(requirements, index, platforms, versions, quiet):
    """THE QUESTION THIS TOOL IS REALLY FOR.

    Kent, 2026-09-23: *"the fundamental question is 'What is the highest
    version that will install everywhere?'"* — not "does 3.13 work", which is
    that question asked one candidate at a time and answered without saying
    what the alternative would have been.

    Answered at TWO strictnesses, because they can differ and the difference
    matters: the highest python where everything has some installable file,
    and the highest where everything has a WHEEL.

    WHAT "no wheel" DOES AND DOES NOT MEAN — read this before treating the
    second number as a verdict. It is a fact about PyPI: no binary was
    published for that python and platform. It is NOT the same as "needs a
    compiler". A source distribution with no C extension is pure python and
    installs anywhere with no build tools at all; `openai_whisper` is exactly
    that case here, and it is why `requirements.txt` can carry it for Windows
    while calling it sdist-only. A source distribution that DOES carry an
    extension needs a toolchain the user may not have, which is the real
    hazard on Windows and on a Mac without the Xcode tools. Nothing in a
    filename distinguishes the two, so this tool does not guess: it reports
    "no wheel" and leaves that judgement to a reader who can check the
    project. Treat the second number as an upper bound on trouble, not as a
    count of failures.

    One network fetch per package for the whole sweep: the index remembers
    what it was told, and only the judging is redone per version."""
    rows = []
    for major, minor in versions:
        if not quiet:
            print('\n== python {}.{}'.format(major, minor), file=sys.stderr)
        table = collect(requirements, index, platforms, major, minor,
                        quiet=quiet)
        rows.append({
            'version': '{}.{}'.format(major, minor),
            'table': table,
            'missing': blockers(table, platforms, count_sdist=False),
            'nowheel': blockers(table, platforms, count_sdist=True),
            'blocking': blocking_packages(table, platforms),
            'nowheel_pkgs': blocking_packages(table, platforms,
                                              count_sdist=True),
        })
    return rows


def standing(rows, key='nowheel_pkgs'):
    """Packages that fail at EVERY version in the range.

    A DEPENDENCY THAT HAS NEVER PUBLISHED A WHEEL IS NOT A VERSION PROBLEM,
    and reporting it as one makes the headline permanently false. Here
    `openai_whisper` has been sdist-only for years by its own choice, so
    "no python has a wheel for everything" was true, useless, and alarming —
    it would stay true whatever python anyone picked (Kent's sweep,
    2026-09-23). Split these out, say so once, and give the number that
    actually varies."""
    if not rows:
        return {}
    common = set(rows[0][key])
    for r in rows[1:]:
        common &= set(r[key])
    return {name: rows[-1][key][name] for name in sorted(common, key=str.lower)}


def report_highest(rows, platforms, index=None):
    print('\n' + '=' * 72)
    print('HIGHEST PYTHON EVERYTHING INSTALLS ON')
    print('=' * 72)
    fixed = standing(rows)
    row_fmt = '{:<9}{:<16}{:<16}{}'
    head = row_fmt.format('python', 'wont-install', 'no-wheel', 'first blocker')
    print('\n' + head)
    print('-' * max(len(head), 62))
    for r in rows:
        first = r['missing'][0] if r['missing'] else (
            r['nowheel'][0] if r['nowheel'] else None)
        detail = '' if first is None else '{} ({})'.format(first[0], first[1])
        print(row_fmt.format(r['version'], len(r['missing']),
                             len(r['nowheel']), detail))
    installable = [r for r in rows if not r['missing']]
    wheels = [r for r in rows if not r['nowheel']]
    # The same comparison again, ignoring packages that have no wheel at ANY
    # version — see `standing()`.
    varying = [r for r in rows
               if not [n for n in r['nowheel_pkgs'] if n not in fixed]]
    print('')
    if fixed:
        print('NO WHEEL AT ANY VERSION IN THE RANGE — a standing fact about '
              'these\ndependencies, not a reason to prefer one python:')
        for name, where in fixed.items():
            print('   {} (no wheel on {})'.format(name, ', '.join(where)))
        print('   A source distribution with no C extension still installs '
              'anywhere;\n   these are worth checking once, not once per '
              'python.')
        print('')
    if installable:
        print('Highest python where every requirement has an installable '
              'file: {}'.format(installable[-1]['version']))
        # THE FLOOR IS THE NUMBER WITH TEETH, and it is easy to miss while
        # looking at the ceiling. Kent, 2026-09-23: *"installing a newer
        # python is not as easy as pulling from azt's git repo ... We
        # probably should not assume anyone will ever update python version
        # without being required to, and probably helped."* Quite so — and
        # this project's requirements file is a ROLLOUT mechanism, re-run on
        # every install whose stamp changes. So a dependency that quietly
        # raises its own python floor does not merely fail to improve an old
        # machine; it breaks the next routine update on it, and a failed
        # resolve withholds the stamp, so it retries on every boot.
        print('LOWEST python in the range that still installs everything: {}'
              ''.format(installable[0]['version']))
        print('   That is the floor, and it is the number to defend: every '
              'field machine below it\n   breaks on its next update, with no '
              'one there to help. Raising it is a MIGRATION,\n   not a '
              'version bump.')
    else:
        print('NO python in the range installs everything. The table above '
              'says what blocks each one.')
    if wheels:
        print('Highest python where every requirement has a WHEEL: {}'
              .format(wheels[-1]['version']))
    elif varying:
        print('Highest python where everything EXCEPT the standing cases '
              'above has a wheel: {}'.format(varying[-1]['version']))
    else:
        print('At every version tried, something has no wheel beyond the '
              'standing cases above. Run one version with --details to see '
              'which.')
    if installable and wheels and installable[-1]['version'] != wheels[-1]['version']:
        print('\nThose differ, which is the useful part: between {} and {} '
              'something has no wheel — which costs a compiler only if that '
              'sdist carries a C extension. See the note in find_highest.'
              ''.format(wheels[-1]['version'], installable[-1]['version']))
    report_waiting(rows, platforms, index)
    return 0 if installable else 1


def compare(before, after, platforms, old, new):
    """What CHANGES between two pythons. This is the move/don't-move answer."""
    print('\n' + '=' * 70)
    print('DIFFERENCES: python {} → {}'.format(old, new))
    print('=' * 70)
    regressions, improvements = [], []
    for key, entry in sorted(after.items(),
                             key=lambda kv: kv[1]['req'].name.lower()):
        if key not in before:
            continue
        for p in platforms:
            was = before[key]['row'][p][0]
            now = entry['row'][p][0]
            if was == now:
                continue
            line = '   {:<24} {:<16} {} → {}'.format(entry['req'].name, p,
                                                     was, now)
            if RANK[now] < RANK[was]:
                regressions.append((line, entry['row'][p][1]))
            else:
                improvements.append(line)
    if regressions:
        print('\nWORSE on {} — these block the move:'.format(new))
        for line, detail in regressions:
            print(line)
            print('   {:<24} {}'.format('', detail))
    else:
        print('\nNothing gets worse on {}.'.format(new))
    if improvements:
        print('\nBetter on {}:'.format(new))
        for line in improvements:
            print(line)
    return len(regressions)


def main(argv=None):
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser(
        description='Which requirements install, on which python, on which '
                    'platform. Switches only; no environment variables.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='NORMAL USE IS TWO COMMANDS:\n\n'
               '  %(prog)s\n'
               '      floor, ceiling, what blocks moving up, a real pip\n'
               '      resolve of the winner, and a stale-pin audit.\n\n'
               '  %(prog)s --versions torch\n'
               '      which versions of one package have wheels, per python\n'
               '      and platform. For choosing a new pin.\n\n'
               'Everything below is for a rare day. If you find yourself\n'
               'needing one of them twice, say so and it should become a\n'
               'default instead.\n')
    # GROUPED, because the list had grown past what anyone can hold (Kent,
    # 2026-09-23: "my head is spinning with them, and there's no chance I'll
    # remember it next time"). The two that matter are in the epilog above;
    # these headings are so the rest can be skimmed and forgotten again.
    rare = ap.add_argument_group(
        'rarely needed — indexes, caching, exit codes, and naming a version '
        'by hand')
    ap.add_argument('--python', metavar='X.Y',
                    help='ask about ONE python version instead of searching')
    rare.add_argument('--best', action='store_true',
                    help='the default; accepted so the switch still works')
    ap.add_argument('--range', default='3.9-3.14', metavar='X.Y-X.Z',
                    help='versions --best searches (default: %(default)s)')
    ap.add_argument('--compare', metavar='X.Y,X.Z',
                    help='two versions: report only what CHANGES between them')
    ap.add_argument('--requirements', action='append', metavar='GLOB',
                    help='requirements file or glob; repeatable. Default: '
                         'requirements*.txt beside this script')
    ap.add_argument('--exclude', action='append', metavar='GLOB',
                    help='requirements file to skip; repeatable, matched '
                         'against the name or the path. NEEDED WHENEVER A '
                         'REPO KEEPS ARCHIVED REQUIREMENTS: a bare '
                         'requirements*.txt glob will happily read a 2025 '
                         'snapshot and report its long-removed pins as '
                         'blockers')
    ap.add_argument('--platform', action='append', metavar='NAME',
                    choices=sorted(PLATFORMS),
                    help='platform to check; repeatable. Default: {}'.format(
                        ', '.join(DEFAULT_PLATFORMS)))
    ap.add_argument('--all-platforms', action='store_true',
                    help='every platform this tool knows about')
    ap.add_argument('--all', action='store_true',
                    help='show every requirement, not just the problems')
    ap.add_argument('--details', action='store_true',
                    help='say why, for anything that is not a plain wheel')
    rare.add_argument('--via-pip', nargs='?', const='auto', metavar='X.Y',
                    help='ON BY DEFAULT; this only names a version to check '
                         'instead of searching. The pip resolve is the '
                         'authoritative pass and the only one that sees '
                         'CO-REQUISITES. Turn it off with --no-pip')
    ap.add_argument('--audit-pins', nargs='?', const='auto', metavar='X.Y',
                    help='ON BY DEFAULT; this only names a version. Asks '
                         'which of YOUR OWN pins still earn their place by '
                         'dropping each in turn and re-resolving: '
                         'load-bearing, redundant, or HOLDING YOU BACK '
                         'because the constraint it was written for has '
                         'lifted. Turn it off with --no-audit')
    ap.add_argument('--no-audit', action='store_true',
                    help='skip the pin audit. It is the slowest pass, one '
                         'resolve per pinned requirement, so this is the one '
                         'to drop when you just want the version answer')
    ap.add_argument('--versions', action='append', default=[], metavar='NAME',
                    help='list which VERSIONS of a package publish a wheel, '
                         'per python and platform, ignoring the pin. Use it '
                         'to choose a new pin: "which torch works on 3.13?". '
                         'Repeatable')
    ap.add_argument('--override', action='append', default=[],
                    metavar='NAME==VERSION',
                    help='WHAT-IF: replace the pin for NAME everywhere it '
                         'appears, then answer as usual. "How would moving '
                         'torch up change things?" is this switch. A local '
                         'version already on the pin (+cpu) is kept unless '
                         'you give one; markers are kept as written')
    ap.add_argument('--align', action='append', default=[], metavar='A,B,C',
                    help='declare another family of packages released as a '
                         'matched set, so --override warns when you move one '
                         'and not the rest. torch/torchvision/torchaudio are '
                         'known already')
    ap.add_argument('--no-pip', action='store_true',
                    help='skip the pip resolve and report only the fast scan '
                         'of the names you listed. Faster, and needs no pip, '
                         'but it cannot see co-requisites')
    ap.add_argument('--allow-sdist', action='append', metavar='NAME',
                    default=[],
                    help='ANOTHER requirement to take out of the pip resolve. '
                         'Rarely needed: the scan works out which packages '
                         'have no wheel and sets those aside itself, and '
                         'KNOWN_SDIST_ONLY at the top of this file names the '
                         'ones already known. Repeatable')
    ap.add_argument('--pip-extra-index-url', metavar='URL',
                    help='an index NOT already named in the requirements '
                         'files. Usually unnecessary: pip reads their own '
                         '--extra-index-url lines, and so does this tool')
    ap.add_argument('--index-url', default='https://pypi.org',
                    help='index to ask (default: %(default)s)')
    ap.add_argument('--cache', metavar='DIR',
                    help='remember answers here, so repeat runs need no '
                         'network')
    ap.add_argument('--timeout', type=int, default=30, metavar='SECONDS')
    ap.add_argument('--quiet', action='store_true',
                    help='no per-package progress on stderr')
    ap.add_argument('--fail-on-missing', action='store_true',
                    help='exit non-zero if anything lacks a wheel, so this '
                         'can gate a release')
    args = ap.parse_args(argv)

    if args.all_platforms:
        platforms = sorted(PLATFORMS)
    elif args.platform:
        platforms = args.platform
    else:
        platforms = list(DEFAULT_PLATFORMS)

    patterns = args.requirements or [os.path.join(here, 'requirements*.txt')]
    paths = []
    for pattern in patterns:
        hits = sorted(glob.glob(pattern))
        if not hits and os.path.exists(pattern):
            hits = [pattern]
        paths.extend(hits)
    skipped = []
    for pattern in args.exclude or []:
        for path in list(paths):
            if (fnmatch.fnmatch(os.path.basename(path), pattern)
                    or fnmatch.fnmatch(path, pattern)):
                paths.remove(path)
                skipped.append(path)
    if not paths:
        sys.exit('No requirements files matched: {}'.format(
            ', '.join(patterns)))

    requirements, problems, harvested = read_requirements(paths)
    print('Requirements files read:')
    for p in paths:
        print('   {}'.format(p))
    print('   {} requirements, {} platforms'.format(len(requirements),
                                                    len(platforms)))
    if problems:
        print('\nLINES THAT COULD NOT BE PARSED — check these by hand:')
        for path, line, why in problems:
            print('   {}: {!r} ({})'.format(path, line, why))
    if not requirements:
        sys.exit('Nothing to check.')

    if args.override:
        # KEEP THE LOCAL VERSION UNLESS TOLD OTHERWISE. `torch==2.7.1+cpu`
        # answered with `--override torch==2.10.0` means "the same build, two
        # releases on", not "drop the CPU wheel and take the CUDA one" — the
        # `+cpu` is which BUILD, not which version, and losing it silently
        # would change the question being asked.
        def keep_local(new_spec, old_spec):
            tags = {str(s.version).split('+', 1)[1] for s in old_spec
                    if '+' in str(s.version)}
            if not tags:
                return new_spec
            tag = sorted(tags)[0]
            parts = []
            for s in new_spec:
                ver = str(s.version)
                # PEP 440: A LOCAL LABEL IS LEGAL ONLY WITH == OR !=. Adding
                # `+cpu` to a `>=` produces `torch>=2.7.1+cpu`, which pip
                # rejects outright — "Local version label can only be used
                # with `==` or `!=` operators" (Kent hit exactly this writing
                # it by hand, 2026-09-23). So a range override drops the
                # build label rather than carrying it into an invalid
                # specifier, and says so.
                if s.operator in ('==', '!=') and '+' not in ver:
                    ver = ver + '+' + tag
                parts.append('{}{}'.format(s.operator, ver))
            if any(s.operator not in ('==', '!=') for s in new_spec):
                print('   NOTE: dropped the +{} build label — PEP 440 allows '
                      'one only with == or !=. Which build you get is then '
                      'decided by which index answers first.'.format(tag))
            return SpecifierSet(','.join(parts))

        subs = {}
        for text in args.override:
            try:
                over = Requirement(text)
            except InvalidRequirement as e:
                sys.exit('--override wants NAME==VERSION ({})'.format(e))
            subs[normalize(over.name)] = over.specifier
        changed = []
        for i, (req, source, raw) in enumerate(requirements):
            key = normalize(req.name)
            if key not in subs:
                continue
            was = str(req.specifier)
            req.specifier = keep_local(subs[key], req.specifier)
            requirements[i] = (req, source, raw)
            changed.append('{}{} → {}{}'.format(req.name, was, req.name,
                                                req.specifier))
        if changed:
            print('\nWHAT-IF, pins replaced for this run only:')
            for line in changed:
                print('   {}'.format(line))
        else:
            print('\n--override matched nothing: {}'.format(
                ', '.join(sorted(subs))))
        # MOVING ONE MEMBER OF A MATCHED SET ASKS A FALSE QUESTION.
        families = list(ALIGNED_FAMILIES)
        for spec in args.align or []:
            families.append(tuple(n.strip() for n in spec.split(',')
                                  if n.strip()))
        present = {normalize(r.name) for r, _s, _raw in requirements}
        for key in subs:
            fam = family_of(key, families)
            if not fam:
                continue
            siblings = [n for n in fam if normalize(n) != key]
            left = [n for n in siblings
                    if normalize(n) in present and normalize(n) not in subs]
            absent = [n for n in siblings if normalize(n) not in present]
            if left:
                print('   WARNING: {} is released as a matched set with {}. '
                      'You moved {} and left {} where they were, so this run '
                      'asks a question no real install can answer — each '
                      'sibling pins an exact {}, and pip will reject the '
                      'mismatch. Override them together.'.format(
                          key, ', '.join(siblings), key, ', '.join(left), key))
            elif absent and len(absent) == len(siblings):
                print('   NOTE: {} is released as a matched set with {}, but '
                      'neither is a requirement here, so nothing pins them '
                      'against this version. If they are ever added, they '
                      'move together.'.format(key, ', '.join(siblings)))

    if harvested:
        print('   extra indexes named by those files (used automatically): '
              '{}'.format(', '.join(harvested)))
    index = Index(args.index_url, timeout=args.timeout, cache_dir=args.cache,
                  extra=harvested)

    def ask(version):
        bits = version.split('.')
        try:
            major, minor = int(bits[0]), int(bits[1])
            patch = int(bits[2]) if len(bits) > 2 else 0
        except (IndexError, ValueError):
            sys.exit('--python/--compare want X.Y or X.Y.Z, not {!r}'
                     .format(version))
        return collect(requirements, index, platforms, major, minor,
                       quiet=args.quiet, patch=patch)

    def sdist_names(table):
        """Requirements with NO WHEEL anywhere they apply, by name.

        THE PIP PASS NEEDS THIS AND SHOULD NOT BE TOLD IT. Cross-platform
        resolution forces `--only-binary`, so any such package aborts the
        resolve and hides everything behind it — which is why the first run
        had to be given `--allow-sdist openai_whisper` by hand. The scan has
        just worked out which packages those are, so it hands them over
        (Kent, 2026-09-23: "the second is a known exception"). Derived, not
        hardcoded, so this keeps working in another repo with other
        packages."""
        out = set()
        for _key, entry in table.items():
            verdicts = {v for v, _d in entry['row'].values()}
            if SDIST in verdicts and WHEEL not in verdicts:
                out.add(entry['req'].name)
        return out

    def set_aside_for(table):
        """One list, used by BOTH the pip resolve and the pin audit."""
        auto = sdist_names(table)
        known = {n for n in KNOWN_SDIST_ONLY
                 if normalize(n) in {normalize(r.name)
                                     for r, _s, _raw in requirements}}
        return sorted(set(args.allow_sdist) | auto | known), auto, known

    def run_pip_for(version, table):
        names, auto, known = set_aside_for(table)
        if auto or known:
            print('\nSet aside so pip can reach what is behind them:')
            for n in sorted(auto):
                print('   {} — the scan found no wheel for it anywhere'
                      .format(n))
            for n in sorted(known - auto):
                print('   {} — listed in KNOWN_SDIST_ONLY'.format(n))
        return via_pip(paths, platforms, version,
                       extra_index=args.pip_extra_index_url,
                       verbose=not args.quiet, allow_sdist=names,
                       requirements=requirements, indexes=harvested)

    def run_all_for(version, table):
        """THE THREE PASSES, IN ORDER, FOR ONE VERSION — and all three are on
        by default.

        They answer different questions and each is useless without the
        others: the scan says whether the names we listed have wheels, pip
        says whether the whole tree does, and the audit says whether our own
        pins are still earning their place. The switches turn passes OFF
        (`--no-pip`, `--no-audit`); nothing has to be turned on. Kent asked
        the same question about each of them in turn — the index URL, the
        set-aside package, --best, --via-pip, --audit-pins — and the answer
        was the same every time: don't make someone ask for the tool's actual
        job."""
        failed = 0
        if not args.no_pip:
            failed = run_pip_for(version, table)
            if failed:
                print('\nSo {} does NOT survive a real resolve. Something a '
                      'requirement depends on has no wheel; pip named it '
                      'above.'.format(version))
            else:
                print('\nConfirmed: {} resolves cleanly with co-requisites '
                      'included.'.format(version))
        if not args.no_audit:
            audit_pins(requirements, platforms[0], version, indexes=harvested,
                       extra_index=args.pip_extra_index_url, quiet=args.quiet,
                       allow_sdist=set_aside_for(table)[0])
        return failed

    # A NAMED version skips the search. --via-pip and --audit-pins may each
    # carry one; so may --python. They all mean the same thing here.
    named = None
    for value in (args.via_pip, args.audit_pins, args.python):
        if value and value != 'auto':
            named = value
            break

    # A DIRECT QUESTION, ANSWERED AND NOTHING ELSE. No sweep, no pip, no
    # audit — those answer "does the pin work", and this is for choosing one.
    if args.versions:
        report_versions(index, requirements, args.versions, platforms,
                        parse_range(args.range) if not named
                        else [tuple(int(x) for x in named.split('.')[:2])])
        return 0

    if args.compare:
        parts = [v.strip() for v in args.compare.split(',') if v.strip()]
        if len(parts) != 2:
            sys.exit('--compare wants exactly two versions, e.g. 3.12,3.13')
        old, new = parts
        before, after = ask(old), ask(new)
        print_table(before, platforms, 'PYTHON {}'.format(old), args.all)
        print_table(after, platforms, 'PYTHON {}'.format(new), args.all)
        if args.details:
            print_details(after, platforms)
        regressions = compare(before, after, platforms, old, new)
        print('\nVerdict: {}'.format(
            'do NOT move yet — {} regression(s) above'.format(regressions)
            if regressions else
            'nothing regresses; the move is safe as far as PyPI can say'))
        return 1 if (regressions and args.fail_on_missing) else 0

    if named:
        table = ask(named)
        print_table(table, platforms, 'PYTHON {}'.format(named), args.all)
        if args.details:
            print_details(table, platforms)
        missing = sum(1 for e in table.values()
                      if worst(e['row']) < RANK[SDIST])
        if missing:
            print('\n{} requirement(s) have NO installable file on at least '
                  'one platform.'.format(missing))
        failed = run_all_for(named, table)
        return 1 if ((missing or failed) and args.fail_on_missing) else 0

    # SEARCHING IS THE DEFAULT (Kent, 2026-09-23: "so let's just do --best by
    # default, then"). Asking about one version is the special case, because
    # it answers "does 3.13 work" without ever saying what the alternative
    # would have been — and the alternative is the decision.
    rows = find_highest(requirements, index, platforms,
                        parse_range(args.range), args.quiet)
    # Only versions with a HARD block get a table. Printing one wherever
    # anything lacked a wheel meant six near-identical tables whose only rows
    # were the standing cases (Kent's sweep, 2026-09-23); the summary and the
    # waiting block carry those. --all still shows every version in full.
    for r in rows:
        if args.all or r['missing']:
            print_table(r['table'], platforms,
                        'PYTHON {}'.format(r['version']), args.all)
    status = report_highest(rows, platforms, index)
    clear = [r for r in rows if not r['missing']]
    if not clear:
        print('\nNothing further to check: no version in the range is clear '
              'even on the declared requirements.')
        return 1 if args.fail_on_missing else 0
    failed = run_all_for(clear[-1]['version'], clear[-1]['table'])
    return 1 if ((failed or status) and args.fail_on_missing) else 0


if __name__ == '__main__':
    sys.exit(main())
