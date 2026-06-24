
import os
import getpass
import platform
from pathlib import Path
from migration.readers import LegacyReader
from migration.converters import Converter
from settings.manager import ConfigManager

class MigrationManager:
    def __init__(self, lift_base_path, username=None, hostname=None):
        self.base_path = Path(lift_base_path)
        self.username = username or getpass.getuser()
        self.hostname = hostname or platform.uname().node

    def get_legacy_filenames(self):
        basename = self.base_path
        return {
            'defaults': basename.with_suffix(f'.{self.username}.{self.hostname}.CheckDefaults.ini'),
            'defaults_legacy': basename.with_suffix('.CheckDefaults.ini'),
            'toneframes': basename.with_suffix(".ToneFrames.dat"),
            'status': basename.with_suffix(".VerificationStatus.dat"),
            'profiledata': basename.with_suffix(".ProfileData.dat"),
            'adhocgroups': basename.with_suffix(".AdHocGroups.dat"),
            'contributors': basename.with_suffix(".Contributors.ini"),
            'soundsettings': basename.with_suffix(f'.{self.username}.{self.hostname}.SoundSettings.ini'),
            'soundsettings_legacy': basename.with_suffix(".SoundSettings.ini"),
            'alphabet': basename.with_suffix(".Alphabet.ini"),
            'reports': Path("alphabet_comparison_settings.json") # Often in local dir
        }

    def migrate(self):
        legacy_files = self.get_legacy_filenames()
        # Read all legacy files and collect data
        special_data = {}
        generic_data = {}
        
        for key, path in legacy_files.items():
            if not path.exists():
                continue
            
            if path.suffix == '.ini':
                data = LegacyReader.read_ini(path)
            elif path.suffix == '.dat':
                data = LegacyReader.read_dat(path)
            elif path.suffix == '.json':
                import json
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                continue
            
            if key in ['toneframes', 'status', 'adhocgroups', 'profiledata']:
                special_data[key] = data
            else:
                generic_data.update(data)

        # Combine data, giving priority to special data to avoid collisions 
        # (e.g. from generic sections in Alphabet.ini)
        all_legacy_data = generic_data
        all_legacy_data.update(special_data)

        if not all_legacy_data:
            return False

        # Convert to domains
        domain_data = Converter.convert(all_legacy_data)

        # Save to new format — but NEVER overwrite a domain JSON that already
        # exists. Migration is strictly one-time: the legacy .dat/.ini files are
        # frozen (no longer written) and never removed, so once the app owns a
        # domain's JSON, re-running this conversion every boot would clobber it
        # with the stale legacy snapshot — e.g. wiping CVC sort status saved
        # since the first migration. Only fill in domains not yet migrated.
        migrated_any = False
        for domain, data in domain_data.items():
            if not data:
                continue
            mgr = ConfigManager(domain, self.base_path, self.hostname, self.username)
            if mgr.filename.exists():
                continue  # already migrated; app's JSON is authoritative
            mgr.save(data)
            migrated_any = True

        return migrated_any
