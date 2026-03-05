
from utilities import logsetup
log = logsetup.getlog(__name__)
import gettext
_ = gettext.gettext

import configparser
import json
import os
import platform
import getpass
from pathlib import Path

class CustomEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, set):
            return {"__type__": "set", "data": list(o)}
        if isinstance(o, Path):
            return str(o)
        try:
            return super().default(o)
        except TypeError:
            return str(o)

def make_hashable(it):
    """Recursively convert lists to tuples to make them hashable for sets."""
    if isinstance(it, list):
        return tuple(make_hashable(i) for i in it)
    return it

def custom_object_hook(obj):
    if "__type__" in obj:
        if obj["__type__"] == "set":
            return set(make_hashable(i) for i in obj["data"])
    return obj

class ConfigManager:
    def __init__(self, domain, base_path, hostname=None, user=None):
        self.domain = domain
        self.base_path = Path(base_path)
        self.hostname = hostname or platform.uname().node
        self.user = user or getpass.getuser()
        self.data = {}
        self.filename = self._get_filename()

    def _get_filename(self):
        if self.domain in ['audio', 'project', 'ui']:
            return self.base_path.with_suffix(f'.{self.user}.{self.hostname}.{self.domain}.json')
        return self.base_path.with_suffix(f'.{self.domain}.json')

    def load(self):
        if self.filename.exists():
            with open(self.filename, 'r', encoding='utf-8') as f:
                self.data = json.load(f, object_hook=custom_object_hook)
        return self.data

    def save(self, data=None):
        if data is not None:
            self.data = data
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=4, ensure_ascii=False, cls=CustomEncoder)

    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value):
        self.data[key] = value
        self.save()

    def __getattr__(self, name):
        if 'data' in self.__dict__ and name in self.data:
            return self.data[name]
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    def __setattr__(self, name, value):
        # Allow normal attribute assignment for initialization
        if name in ['domain', 'base_path', 'hostname', 'user', 'data', 'filename']:
            super().__setattr__(name, value)
            return
        
        # Route unknown attributes to self.data
        if hasattr(self, 'data'):
            self.data[name] = value
            self.save()
        else:
            super().__setattr__(name, value)

class ConfigParser(configparser.ConfigParser):
    def output(self):
        for k in self:
            if isinstance(self[k],str):
                log.info(_("Config {k}: {v}").format(k=k,v=self[k]))
            else:
                for j in self[k]:
                    log.info(_("Config {k}/{j}: {v}").format(k=k,j=j,v=self[k][j]))
    def write(self,*args,**kwargs):
        configparser.ConfigParser.write(self,*args,**kwargs,
                                            space_around_delimiters=False)
    def __init__(self):
        super(ConfigParser, self).__init__(
        converters={'list':list},
        delimiters=(' = ', ' : '),
        allow_no_value=True
        )
        self.optionxform=str
        # self.converters={'list':list} #lambda x: [i.strip() for i in x.split(',')]
