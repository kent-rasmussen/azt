
from .manager import ConfigManager

class AudioConfig(ConfigManager):
    def __init__(self, base_path, hostname=None):
        super().__init__('audio', base_path, hostname)
        self.load()
