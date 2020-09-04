# -*- coding: utf-8 -*-
__version__ = "0.0.1"

import logging
import re
import json
from abc import ABC, abstractmethod
from environs import Env

try:
    import yaml
except ImportError:
    pass  # will fail if using yaml config_file


logger = logging.getLogger()

env = Env()

default_app = None


def get_current_app():
    global default_app

    if default_app is None:
        init_default_app()
    return default_app


class EventApp:

    def __init__(self, name_prefix="", listeners=None):
        self.name_prefix = name_prefix or ""
        listeners = listeners or []
        self.listeners = []
        [self.add_listener(lis) for lis in listeners]

    def add_listener(self, listener):
        if not isinstance(listener, Listener):
            listener = Listener.from_dict(listener)
        self.listeners.append(listener)

    def trigger(self, event_name, event_data):
        event_name = self.name_prefix + event_name
        count = 0
        for lis in self.listeners:
            sent = lis.notify(event_name, event_data)
            if sent:
                count += 1
        return count


class Listener(ABC):
    _registry = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if hasattr(cls, "kind"):
            Listener._registry[cls.kind] = cls

    @classmethod
    def get(cls, kind):
        return cls._registry[kind]

    @classmethod
    def from_dict(cls, listener_def):
        listener_def = dict(listener_def)
        kind = listener_def.pop("kind")
        listener_cls = cls.get(kind)
        if "event_name_regex" in listener_def:
            listener_def["event_name"] = re.compile(listener_def.pop("event_name_regex"))
        # TODO: filter
        return listener_cls(**listener_def)

    def __init__(self, event_name, filter=None):
        self.event_name = event_name
        self.filter = filter

    def notify(self, event_name, event_data):
        if hasattr(self.event_name, "match"):  # is REGEX
            m = self.event_name.match(event_name)
            if not m:
                return False
        elif self.event_name != event_name:
            return False

        if self.filter and not self.filter(event_name, event_data):
            return False

        return self._do_notify(event_name, event_data)

    @abstractmethod
    def _do_notify(self, event_name, event_data):
        raise NotImplementedError


def read_config_file(config_file):
    if hasattr(config_file, "read"):
        # Assume json format
        format = "json"
    elif config_file.endswith(".yaml") or config_file.endswith(".yml"):
        format = "yaml"
        config_file = open(config_file, "rt")
    else:
        format = "json"
        config_file = open(config_file, "rt")

    if format == "json":
        config = json.load(config_file)
    elif format == "yaml":
        config = yaml.safe_load(config_file)

    return config.get("name_prefix", None), config.get("listeners", [])


def init_default_app(name_prefix=None, listeners=None, config_file=None):
    global default_app
    if name_prefix is None and listeners is None and config_file is None:
        # Try reading from env
        config_file = env.str("EVENTISC_CONFIG", None)
        if config_file is None:
            name_prefix = env.str("EVENTISC_NAME_PREFIX", "")
            listeners = []
        else:
            name_prefix, listeners = read_config_file(config_file)
    elif name_prefix is None and config_file is None:
        name_prefix = env.str("EVENTISC_NAME_PREFIX", "")

    default_app = create_app(name_prefix, listeners)
    return default_app


def create_app(name_prefix=None, listeners=None, config_file=None):
    if config_file is not None:
        name_prefix, listeners = read_config_file(config_file)

    return EventApp(name_prefix, listeners)


def trigger(event_name, event_data):
    return get_current_app().trigger(event_name, event_data)
