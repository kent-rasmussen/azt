
from .manager import ConfigManager

class DataConfig(ConfigManager):
    def __init__(self, base_path, hostname=None, user=None):
        super().__init__('data', base_path, hostname, user)
        self.load()
