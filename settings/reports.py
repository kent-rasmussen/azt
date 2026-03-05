
from .manager import ConfigManager

class ReportsConfig(ConfigManager):
    def __init__(self, base_path, hostname=None, user=None):
        super().__init__('reports', base_path, hostname, user)
        self.load()
