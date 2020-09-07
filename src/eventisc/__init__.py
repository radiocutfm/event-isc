# -*- coding: utf-8 -*-
__version__ = "0.0.1"

import logging
import importlib
import re
import json
from abc import ABCMeta, abstractmethod
from environs import Env

try:
    import yaml
except ImportError:
    pass  # will fail if using yaml config_file


logger = logging.getLogger()

env = Env()

default_app = None


def eval_globals():
    """Global modules that might be used in expressions"""
    import math
    import datetime
    return {"datetime": datetime, "math": math, "json": json}


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


class Listener(object):
    __metaclass__ = ABCMeta

    _registry = {}

    @classmethod
    def register(cls):
        if hasattr(cls, "kind"):
            Listener._registry[cls.kind] = cls

    @classmethod
    def get(cls, kind):
        if kind not in cls._registry:
            # Try import listener module
            try:
                importlib.import_module("eventisc.{}_listener".format(kind))
            except ImportError:
                pass
        return cls._registry[kind]

    @classmethod
    def from_dict(cls, listener_def):
        listener_def = dict(listener_def)
        kind = listener_def.pop("kind")
        listener_cls = cls.get(kind)
        if "event_name_regex" in listener_def:
            listener_def["event_name"] = re.compile(listener_def.pop("event_name_regex"))
        if "filter" in listener_def:
            listener_def["filter"] = Filter.from_dict(listener_def["filter"])
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

        if env.bool("EVENTISC_DRYRUN", False):
            return self._do_notify_dryrun(event_name, event_data)
        else:
            return self._do_notify(event_name, event_data)

    @abstractmethod
    def _do_notify(self, event_name, event_data):
        raise NotImplementedError

    def _do_notify_dryrun(self, event_name, event_data):
        logger.info("EVENTISC_DRYRUN=Y _do_notify(%s, %s)", event_name, event_data)
        return True

    @classmethod
    def format(self, value, event_name, event_data, **kwargs):
        """Formats a field that can be constant, proxy or format string of the event values"""
        if not isinstance(value, str) or '{' not in value:
            return value
        context_dict = dict(event_name=event_name, event_data=event_data, **kwargs)
        if value.startswith("{") and value.endswith("}") and '{' not in value[1:-1]:
            # It's a simple value, {variable}, use eval to keep type
            try:
                expr = compile(value[1:-1], __file__, "eval")
            except SyntaxError:
                return value.format(**context_dict)
            return eval(expr, eval_globals(), context_dict)
        return value.format(**context_dict)


class Filter(object):
    __metaclass__ = ABCMeta

    _registry = {}

    @classmethod
    def register(cls):
        if hasattr(cls, "kind"):
            Filter._registry[cls.kind] = cls

    @classmethod
    def get(cls, kind):
        return cls._registry[kind]

    @classmethod
    def from_dict(cls, filter_def):
        filter_def = dict(filter_def)
        kind = filter_def.pop("kind")
        filter_cls = cls.get(kind)
        return filter_cls(**filter_def)

    @abstractmethod
    def __call__(self, event_name, event_data):
        raise NotImplementedError


class ExprFilter(Filter):
    kind = "expr"

    def __init__(self, expr):
        self.expr = compile(expr, __file__, "eval")

    def __call__(self, event_name, event_data):
        return bool(eval(self.expr, eval_globals(), {"event_name": event_name, "event_data": event_data}))


ExprFilter.register()


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


def get_current_app():
    global default_app

    if default_app is None:
        init_default_app()
    return default_app


def trigger(event_name, event_data):
    return get_current_app().trigger(event_name, event_data)
