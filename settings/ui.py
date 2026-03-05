
from .manager import ConfigManager

class UIConfig(ConfigManager):
    def __init__(self, base_path, hostname=None, user=None):
        super().__init__('ui', base_path, hostname, user)
        self.load()
