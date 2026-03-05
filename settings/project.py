
from .manager import ConfigManager

class ProjectConfig(ConfigManager):
    def __init__(self, base_path, hostname=None, user=None):
        super().__init__('project', base_path, hostname, user)
        self.load()

    def get_analang(self):
        return self.get('analang')

    # Add more domain-specific helpers as needed
