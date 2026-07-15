
from .manager import ConfigManager

class ToneFramesConfig(ConfigManager):
    def __init__(self, base_path, hostname=None, user=None):
        super().__init__('tone_frames', base_path, hostname, user)
        self.load()
