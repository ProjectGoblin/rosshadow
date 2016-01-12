"""
ROS Shadow Configuration Parser, supporting JSON & YAML.

Example:

default_configuration: &default
    priority: local # local or remote
    fallback: No    # Yes/No for (en/dis)able, or a list of alternative services.
    config-dependency: Yes # chose Yes if you want to rule any dependency as while.

services:
  - ros*: # Yes, with full-regex supporting. :P
      <<: *default

  - AddInts:
      <<: *default
      fallback: 
        - sum
  - sum:
      priority: remote
      fallback: true

  - GetMap3D:
      priority: remote
      fallback: false
"""
import rospkg
import json
import yaml
import threading
import re
import os
from os import environ
import sys

rp = rospkg.RosPack
rp_lock = threading.Lock()

"""
Reserved keywords for Shadow Configuration
"""
SERVICES = "services"
PRIORITY = "priority"
FALLBACK = "fallback"
RECURSIVE = "recursive"
REMOTE   = "remote"
LOCAL    = "local"
LOCALTYPE = "localtype"


class ServiceConfiguration:
    DEFALUT = {
            FALLBACK: True,
            PRIORITY: REMOTE,
            RECURSIVE: True
            }

    def __init__(self, regex=None, obj=None):
        _regex = regex if regex is not None else '.*'
        self._regex = re.compile(_regex, re.UNICODE)
        if obj is None:
            obj = ServiceConfiguration.DEFALUT
        self.fallback = obj.get(FALLBACK,   ServiceConfiguration.DEFALUT[FALLBACK])
        self.priority = obj.get(PRIORITY,   ServiceConfiguration.DEFALUT[PRIORITY])
        self.recursive = obj.get(RECURSIVE, ServiceConfiguration.DEFALUT[RECURSIVE])

    def is_match(self, name):
        """
        Detect if a name matches this rule.
        """
        if self._regex is None:
            return True
        else:
            return self._regex.match(name)

    def __repr__(self):
        return '<ServiceConfiguration {}>'.format(self._regex.pattern)

    @staticmethod
    def default():
        return ServiceConfiguration()

class ServiceConfigurations:
    def __init__(self, objs=None):
        if objs is None:
            objs = []
        self.routines = []
        for regex, obj in objs.items():
            self.routines.append(ServiceConfiguration(regex, obj))

    def get_config(self, name):
        for cfg in self.routines:
            if cfg.is_match(name):
                return cfg
        else:
            # Use defaule configuration as a backup
            return ServiceConfiguration.default()

    @staticmethod
    def default():
        return ServiceConfigurations()

class Configuration:
    def __init__(self, obj):
        self.services = ServiceConfigurations(obj.get(SERVICES, None))
        self.localtype = obj.get(LOCALTYPE, LOCAL)

    @staticmethod
    def default():
        return Configuration({})


def load_shadow_config():
    """
    Load shadow.(yaml|json). Use default configuration if file not exist.
    """
    root = environ.get('SHADOW_CONFIG_PATH',
                       environ.get('SHADOW_ROOT',
                                   environ.get('PWD', os.curdir)))
    for suffix, loader in [('yaml', yaml.load), ('json', json.load)]:
        fullpath = os.path.join(root, 'shadow.' + suffix)
        if os.path.exists(fullpath):
            with open(fullpath, 'r') as stream:
                obj = loader(stream)
                return Configuration(obj)
    return Configuration.default()

