
from .manager import ConfigParser, write_ini, read_ini
from .project import ProjectConfig
from .ui import UIConfig
from .audio import AudioConfig
from .alphabet import AlphabetConfig
from .contributors import ContributorsConfig
from .data import DataConfig
from .reports import ReportsConfig

class SettingsManager:
    """
    Centralized settings manager that provides access to all domains.
    Use get(attr)/set(attr, value) for routing to the correct domain.
    """
    def __init__(self, base_path, hostname=None, user=None):
        self.project = ProjectConfig(base_path, hostname, user)
        self.ui = UIConfig(base_path, hostname, user)
        self.audio = AudioConfig(base_path, hostname, user)
        self.alphabet = AlphabetConfig(base_path, hostname, user)
        self.contributors = ContributorsConfig(base_path, hostname, user)
        self.data = DataConfig(base_path, hostname, user)
        self.reports = ReportsConfig(base_path, hostname, user)
        self._domains = {
            'project': self.project,
            'ui': self.ui,
            'audio': self.audio,
            'alphabet': self.alphabet,
            'contributors': self.contributors,
            'data': self.data,
            'reports': self.reports,
        }

    def domain_for(self, attr):
        """Return the ConfigManager instance that owns the given attribute."""
        from migration.converters import Converter
        domain_name = Converter.domain_for_attr(attr)
        if domain_name and domain_name in self._domains:
            return self._domains[domain_name]
        return None

    def get(self, attr, default=None):
        """Get a setting value by attribute name, routing to the correct domain."""
        domain = self.domain_for(attr)
        if domain is not None:
            return domain.get(attr, default)
        return default

    def set(self, attr, value):
        """Set a setting value by attribute name, routing to the correct domain."""
        domain = self.domain_for(attr)
        if domain is not None:
            domain.set(attr, value)

    def save_all(self):
        for domain in self._domains.values():
            domain.save()
