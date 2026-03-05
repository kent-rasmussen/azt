import configparser
import ast
from pathlib import Path

class LegacyReader:
    @staticmethod
    def read_ini(filename):
        from utilities.utilities import ofromstr
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
        # Manual parsing for .dat files to handle:
        # 1. Keys like '=' which break ConfigParser
        # 2. Multi-line values (indented lines)
        res = {}
        current_section = 'default'
        res[current_section] = {}
        
        if not Path(filename).exists():
            return {}
            
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                last_key = None
                for line in f:
                    if not line.strip():
                        continue
                    
                    # Continuation of a value?
                    if line.startswith(('\t', ' ')) and last_key is not None:
                        res[current_section][last_key] += " " + line.strip()
                        continue

                    stripped = line.strip()
                    if stripped.startswith(('#', ';')):
                        continue
                        
                    if stripped.startswith('[') and stripped.endswith(']'):
                        current_section = stripped[1:-1]
                        if current_section not in res:
                            res[current_section] = {}
                        last_key = None
                        continue
                    
                    if '=' in line:
                        # Target established patterns like 'key = value'
                        if ' = ' in line:
                            parts = line.split(' = ', 1)
                        else:
                            # Fallback if no spaces, handle leading '=' case (e.g. "= = True")
                            if line.startswith('='):
                                parts = line.split('=', 1)
                                if not parts[0] and '=' in parts[1]:
                                    p2 = parts[1].strip().split('=', 1)
                                    parts = ['=', p2[1].strip()]
                            else:
                                parts = line.split('=', 1)
                        
                        if len(parts) == 2:
                            key, val = [i.strip() for i in parts]
                            res[current_section][key] = val
                            last_key = key
            
            # Process all values with ast.literal_eval for fidelity
            for section in res:
                for key in list(res[section].keys()):
                    val = res[section][key]
                    try:
                        res[section][key] = ast.literal_eval(val)
                    except (SyntaxError, ValueError):
                        # Keep as string if literal_eval fails
                        pass
            
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
