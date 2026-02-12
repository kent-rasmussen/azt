
from .manager import ConfigManager

class AlphabetConfig(ConfigManager):
    def __init__(self, base_path, hostname=None):
        super().__init__('alphabet', base_path, hostname)
        self.load()
