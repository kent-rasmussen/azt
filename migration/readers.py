
import configparser
import ast
from pathlib import Path

class LegacyReader:
    @staticmethod
    def read_ini(filename):
        from utilities import ofromstr
        config = configparser.ConfigParser(interpolation=None)
        config.optionxform = str # Preserve case
        if Path(filename).exists():
            config.read(filename, encoding='utf-8')
            res = {}
            for section in config.sections():
                section_data = {}
                for key, val in config.items(section):
                    section_data[key] = ofromstr(val)
                res[section] = section_data
            if 'default' in config:
                for key, val in config.items('default'):
                    res[key] = ofromstr(val)
            if 'DEFAULT' in config:
                for key, val in config.items('DEFAULT'):
                    res[key] = ofromstr(val)
            return res
        return {}

    @staticmethod
    def read_dat(filename):
        # Manual parsing for .dat files to handle keys like '=' which break ConfigParser
        res = {}
        current_section = 'default'
        res[current_section] = {}
        
        if not Path(filename).exists():
            return {}
            
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith(('#', ';')):
                        continue
                    if line.startswith('[') and line.endswith(']'):
                        current_section = line[1:-1]
                        if current_section not in res:
                            res[current_section] = {}
                        continue
                    
                    if '=' in line:
                        if ' = ' in line:
                            parts = line.split(' = ', 1)
                        else:
                            # Fallback if no spaces, split on first '=' but handle leading case
                            if line.startswith('='):
                                # If it starts with =, then the next part after another = is the value
                                # e.g. "= = True" -> key is "=", val is "= True" ? 
                                # Actually, looking at the file it was "= = True"
                                parts = line.split('=', 1)
                                if not parts[0] and '=' in parts[1]:
                                    # Try to split again
                                    p2 = parts[1].strip().split('=', 1)
                                    parts = ['=', p2[1].strip()]
                            else:
                                parts = line.split('=', 1)
                                
                        key, val = [i.strip() for i in parts]
                        try:
                            # Use ast.literal_eval for fidelity, fallback to string
                            res[current_section][key] = ast.literal_eval(val)
                        except (SyntaxError, ValueError):
                            res[current_section][key] = val
            
            # Lift 'default' or 'DEFAULT' values to top level
            for def_sec in ['default', 'DEFAULT']:
                if def_sec in res:
                    data = res.pop(def_sec)
                    for k, v in data.items():
                        if k not in res:
                            res[k] = v
            return res
        except Exception as e:
            from logsetup import getlog
            log = getlog(__name__)
            log.error(f"Error manually parsing .dat file {filename}: {e}")
            return {}
