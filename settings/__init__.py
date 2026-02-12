
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
    """
    def __init__(self, base_path, hostname=None):
        self.project = ProjectConfig(base_path, hostname)
        self.ui = UIConfig(base_path, hostname)
        self.audio = AudioConfig(base_path, hostname)
        self.alphabet = AlphabetConfig(base_path, hostname)
        self.contributors = ContributorsConfig(base_path, hostname)
        self.data = DataConfig(base_path, hostname)
        self.reports = ReportsConfig(base_path, hostname)

    def save_all(self):
        self.project.save()
        self.ui.save()
        self.audio.save()
        self.alphabet.save()
        self.contributors.save()
        self.data.save()
        self.reports.save()
