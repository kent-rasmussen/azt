
class Converter:
    """Single source of truth for settings attribute schema.
    
    DOMAIN_MAPPING: which attributes belong to which domain.
    LEGACY_FILE_MAPPING: maps old settingsbyfile group names to domain names.
    LEGACY_FILE_ATTRS: maps old settingsbyfile group names to legacy file attrs.
    """
    DOMAIN_MAPPING = {
        'project': [
            'analang', 'glosslangs', 'audiolang', 'additionalps', 'entriestoshow', 
            'additionalprofiles', 'adnlangnames', 'maxpss', 'maxprofiles', 
            'menu', 'secondformfield', 'giturls', 'hgurls', 'aztrepourls', 
            'minimumwordstoreportUFgroup', 'askedlxtolc', 'start_at_entry', 
            'end_at_entry', 'writeeverynwrites', 'ps', 'profile', 'cvt', 
            'check', 'regexCV'
        ],
        'ui': [
            'interfacelang', 'mainrelief', 'fontthemesmall', 'buttoncolumns',
            'showoriginalorthographyinreports', 'lowverticalspace', 'showdetails',
            'examplespergrouptorecord', 'syllable_max_slice'
        ],
        'audio': [
            'sample_format', 'fs', 'audio_card_in', 'audio_card_out',
            'asr_kwargs', 'asr_repos', 'soundsettingsok', 'asr_in_process'
        ],
        'alphabet': [
            'glyphdict', 'alphabet_order', 'alphabet_ncolumns', 
            'alphabet_chart_title', 'alphabet_exids', 'alphabet_pagesize', 
            'glyph_members', 'glyphs_distinguished', 'alphabet_copyright'
        ],
        'contributors': [
            'contributors'
        ],
        'data': [
            'status', 'adhocgroups', 'scount', 'sextracted',
            'distinguish', 'interpret', 'polygraphs'
        ],
        'tone_frames': [
            'toneframes'
        ],
        'reports': [
            # alphabet_comparison_settings.json will be handled separately
        ]
    }

    # Maps old settingsbyfile group names to lists of new domain names
    LEGACY_FILE_MAPPING = {
        'defaults': ['project', 'ui'],
        'soundsettings': ['audio'],
        'alphabet': ['alphabet'],
        'contributors': ['contributors'],
        'status': ['data'],
        'toneframes': ['tone_frames'],
        'adhocgroups': ['data'],
        'profiledata': ['data'],
    }

    # Maps old settingsbyfile group names to the legacy file attribute on Settings
    LEGACY_FILE_ATTRS = {
        'defaults': 'defaultfile',
        'soundsettings': 'soundsettingsfile',
        'alphabet': 'alphabetsettingsfile',
        'contributors': 'contributorsfile',
        'status': 'statusfile',
        'toneframes': 'toneframesfile',
        'adhocgroups': 'adhocgroupsfile',
        'profiledata': 'profiledatafile',
    }

    # Declarative mapping for settingsobjects bridge.
    # Maps attr -> (target_object_string, method_name)
    OBJECT_MAPPING = {
        'cvt': ('program.params', 'cvt'),
        'check': ('program.params', 'check'),
        'ftype': ('program.params', 'ftype'),
        'analang': ('program.params', 'analang'),
        'glosslang': ('self.glosslangs', 'lang1'),
        'glosslang2': ('self.glosslangs', 'lang2'),
        'glosslangs': ('self.glosslangs', 'langs'),
        'aztrepourls': ('program.repo', 'remoteurls'),
        'status': ('program.alphabet', 'status'),
        'glyphdict': ('program.alphabet', 'glyphdict'),
        'glyph_members': ('program.alphabet', 'glyph_members'),
        'glyphs_distinguished': ('program.alphabet', 'distinguished'),
        'alphabet_order': ('program.alphabet', 'order'),
        'alphabet_ncolumns': ('self', 'alpha_ncolumns'),
        'alphabet_exids': ('self', 'alpha_exids'),
        'alphabet_chart_title': ('self', 'alpha_chart_title'),
        'alphabet_copyright': ('self', 'alpha_copyright'),
        'alphabet_pagesize': ('self', 'alpha_pagesize'),
        'contributors': ('self', 'alphabet_contributors'),
        'ps': ('program.slices', 'ps'),
        'profile': ('program.slices', 'profile'),
        'profilecounts': ('program.slices', 'slicepriority'),
        'giturls': ('self.repo["git"]', 'remoteurls'),
        'asr_repos': ('program.soundsettings', 'asr_repo_tally'),
        'asr_kwargs': ('program.soundsettings', 'asr_kwarg_dict'),
        'hgurls': ('self.repo["hg"]', 'remoteurls'),
    }

    # Maps old settingsbyfile group names to their attribute lists.
    # This replaces Settings.settingsbyfile() entirely.
    LEGACY_SETTINGS = {
        'defaults': {
            'file': 'defaultfile',
            'attributes': (
                DOMAIN_MAPPING['project'] + DOMAIN_MAPPING['ui']
                # soundsettingsok was listed in defaults but belongs to audio
                + ['soundsettingsok']
            )
        },
        'profiledata': {
            'file': 'profiledatafile',
            'attributes': [
                'analang', 'ftype', 'distinguish', 'interpret', 
                'polygraphs', 'scount', 'sextracted'
            ]
        },
        'status': {
            'file': 'statusfile',
            'attributes': ['status']
        },
        'adhocgroups': {
            'file': 'adhocgroupsfile',
            'attributes': ['adhocgroups']
        },
        'soundsettings': {
            'file': 'soundsettingsfile',
            'attributes': [
                'sample_format', 'fs', 'audio_card_in', 
                'audio_card_out', 'asr_kwargs', 'asr_repos'
            ]
        },
        'alphabet': {
            'file': 'alphabetsettingsfile',
            'attributes': [
                'status', 'glyphdict', 'alphabet_order', 
                'alphabet_ncolumns', 'alphabet_chart_title', 
                'alphabet_exids', 'alphabet_pagesize', 
                'glyph_members', 'glyphs_distinguished', 
                'alphabet_copyright'
            ]
        },
        'contributors': {
            'file': 'contributorsfile',
            'attributes': ['contributors']
        },
        'toneframes': {
            'file': 'toneframesfile',
            'attributes': ['toneframes']
        },
    }

    @classmethod
    def attrs_for_domain(cls, domain):
        """Return the list of attributes for a given domain."""
        return cls.DOMAIN_MAPPING.get(domain, [])

    @classmethod
    def attrs_for_legacy_setting(cls, setting):
        """Return the attribute list for a legacy settingsbyfile group name."""
        return cls.LEGACY_SETTINGS.get(setting, {}).get('attributes', [])

    @classmethod
    def file_for_legacy_setting(cls, setting):
        """Return the file attribute name for a legacy settingsbyfile group."""
        return cls.LEGACY_SETTINGS.get(setting, {}).get('file')

    @classmethod
    def domains_for_legacy_setting(cls, setting):
        """Return the list of new domain names for a legacy setting group."""
        return cls.LEGACY_FILE_MAPPING.get(setting, [])

    @classmethod
    def domain_for_attr(cls, attr):
        """Return the domain name that owns a given attribute, or None."""
        for domain, attrs in cls.DOMAIN_MAPPING.items():
            if attr in attrs:
                return domain
        return None

    @classmethod
    def convert(cls, legacy_data):
        """
        Takes a dict of all legacy data and splits it into domains.
        legacy_data should be a flat dict of key-value pairs.
        """
        new_data = {domain: {} for domain in cls.DOMAIN_MAPPING}
        
        for domain, attributes in cls.DOMAIN_MAPPING.items():
            for attr in attributes:
                if attr in legacy_data:
                    new_data[domain][attr] = legacy_data[attr]
        
        return new_data
