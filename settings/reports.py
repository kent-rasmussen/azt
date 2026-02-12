
from .manager import ConfigManager

class ReportsConfig(ConfigManager):
    def __init__(self, base_path, hostname=None):
        super().__init__('reports', base_path, hostname)
        self.load()
