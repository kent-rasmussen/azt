
import json
import os
import platform
from pathlib import Path

class CustomEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, set):
            return list(o)
        if isinstance(o, Path):
            return str(o)
        return str(o) # Fallback for other non-serializable types

class ConfigManager:
    def __init__(self, domain, base_path, hostname=None):
        self.domain = domain
        self.base_path = Path(base_path)
        self.hostname = hostname or platform.uname().node
        self.data = {}
        self.filename = self._get_filename()

    def _get_filename(self):
        # We'll use the domain name and hostname to uniquely identify settings files
        # following the pattern seen in the legacy code but standardized to JSON.
        return self.base_path.with_suffix(f'.{self.domain}.json')

    def load(self):
        if self.filename.exists():
            with open(self.filename, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
        return self.data

    def save(self, data=None):
        if data is not None:
            self.data = data
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=4, ensure_ascii=False, cls=CustomEncoder)

    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value):
        self.data[key] = value
        self.save()
