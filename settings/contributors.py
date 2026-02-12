
from .manager import ConfigManager

class ContributorsConfig(ConfigManager):
    def __init__(self, base_path, hostname=None):
        super().__init__('contributors', base_path, hostname)
        self.load()
