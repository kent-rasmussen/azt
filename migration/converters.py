
class Converter:
    DOMAIN_MAPPING = {
        'project': [
            'analang', 'glosslangs', 'audiolang', 'additionalps', 'entriestoshow', 
            'additionalprofiles', 'adnlangnames', 'maxpss', 'maxprofiles', 
            'menu', 'secondformfield', 'giturls', 'hgurls', 'aztrepourls', 
            'minimumwordstoreportUFgroup', 'askedlxtolc', 'start_at_entry', 
            'end_at_entry', 'writeeverynwrites', 'ps', 'profile', 'cvt', 'check', 'regexCV'
        ],
        'ui': [
            'interfacelang', 'mainrelief', 'fontthemesmall', 'buttoncolumns', 
            'showoriginalorthographyinreports', 'lowverticalspace', 'showdetails',
            'examplespergrouptorecord'
        ],
        'audio': [
            'sample_format', 'fs', 'audio_card_in', 'audio_card_out', 'asr_kwargs', 'asr_repos', 'soundsettingsok'
        ],
        'alphabet': [
            'glyphdict', 'alphabet_order', 'alphabet_ncolumns', 'alphabet_chart_title', 
            'alphabet_exids', 'alphabet_pagesize', 'glyph_members', 
            'glyphs_distinguished', 'alphabet_copyright'
        ],
        'contributors': [
            'contributors'
        ],
        'data': [
            'status', 'toneframes', 'adhocgroups', 'scount', 'sextracted', 'distinguish', 'interpret', 'polygraphs'
        ],
        'reports': [
            # alphabet_comparison_settings.json will be handled separately or added here
        ]
    }

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
