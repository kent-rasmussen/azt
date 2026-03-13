#!/usr/bin/env python3
# coding=UTF-8
"""Resolve CAWL numbers to illustration image URLs from GitHub.

Fetches the kent-rasmussen/images_CAWL repo tree once via the GitHub API,
caches the CAWL→URL mapping to a local JSON file so subsequent runs don't
need network access.
"""
from utilities import logsetup
log=logsetup.getlog(__name__)
logsetup.setlevel('DEBUG',log)
import json
import os
import threading
import urllib.parse
import urllib.request

_GITHUB_REPO = 'kent-rasmussen/images_CAWL'
_GITHUB_BRANCH = 'main'
_RAW_BASE = (f'https://raw.githubusercontent.com/'
             f'{_GITHUB_REPO}/{_GITHUB_BRANCH}')

class CAWLImageResolver:
    """Resolves CAWL numbers to image URLs from kent-rasmussen/images_CAWL.

    Fetches the repo tree once via the GitHub API, caches the CAWL→URL
    mapping to a local JSON file so subsequent runs don't need network.
    """

    def __init__(self, cache_dir):
        self._cache_dir = str(cache_dir)
        self._cache_file = os.path.join(self._cache_dir,
                                        '.cawl_image_urls.json')
        self._urls = None          # cawl str → raw URL
        self._lock = threading.Lock()

    def get_url(self, cawl):
        """Return a raw.githubusercontent.com URL for *cawl*, or ''."""
        if self._urls is None:
            self._load()
        return self._urls.get(str(cawl), '')

    # ── internals ────────────────────────────────────────────────────────

    def _load(self):
        with self._lock:
            if self._urls is not None:
                return

            # Try disk cache first
            if os.path.exists(self._cache_file):
                try:
                    with open(self._cache_file, 'r', encoding='utf-8') as f:
                        self._urls = json.load(f)
                    log.info("Loaded CAWL image cache from %s",
                             self._cache_file)
                    return
                except Exception:
                    pass

            # Fetch from GitHub
            self._urls = {}
            try:
                api_url = (
                    f'https://api.github.com/repos/{_GITHUB_REPO}'
                    f'/git/trees/{_GITHUB_BRANCH}?recursive=1'
                )
                req = urllib.request.Request(
                    api_url,
                    headers={'Accept': 'application/vnd.github.v3+json'},
                )
                with urllib.request.urlopen(req, timeout=30) as resp:
                    data = json.loads(resp.read())

                for item in data.get('tree', []):
                    if item['type'] != 'blob':
                        continue
                    path = item['path']
                    if not path.lower().endswith('.png'):
                        continue
                    parts = path.split('/')
                    if len(parts) != 2:
                        continue
                    cawl_num = parts[0].split('_')[0]
                    if cawl_num in self._urls:
                        continue  # keep first match per CAWL
                    encoded = '/'.join(
                        urllib.parse.quote(p, safe='') for p in parts
                    )
                    self._urls[cawl_num] = f'{_RAW_BASE}/{encoded}'

                log.info("Fetched %d CAWL image URLs from GitHub",
                         len(self._urls))

                # Persist to disk
                try:
                    os.makedirs(self._cache_dir, exist_ok=True)
                    with open(self._cache_file, 'w', encoding='utf-8') as f:
                        json.dump(self._urls, f)
                except OSError:
                    pass
            except Exception as e:
                log.info('Could not fetch CAWL image index: %s', e)
