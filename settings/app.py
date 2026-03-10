
from .manager import ConfigManager

class AppConfig(ConfigManager):
    """Pre-project app-level settings: last opened file, known files, UI language."""
    def __init__(self, base_path, hostname=None, user=None):
        super().__init__('preproject', base_path, hostname, user)
        self.load()

    def get_filename(self):
        return self.get('filename', '')

    def get_filenames(self):
        return self.get('filenames', [])

    def set_filename(self, filename):
        filenames = self.get_filenames()
        s = str(filename) if filename else ''
        if s and s not in filenames:
            filenames.append(s)
        self.set('filenames', filenames)
        self.set('filename', s)

    def get_ui_lang(self):
        return self.get('ui_lang', '')

    def set_ui_lang(self, lang):
        self.set('ui_lang', lang)
