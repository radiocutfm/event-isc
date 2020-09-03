# -*- coding: utf-8 -*-
__version__ = "0.0.1"

import logging

logger = logging.getLogger()

default_app = None


def get_current_app():
    global default_app

    if default_app is None:
        init_default_app()
    return default_app


class EventApp:
    def trigger(self, event_name, event_data):
        pass


def init_default_app(*args, **kargs):
    global default_app
    default_app = create_app(*args, **kargs)


def create_app(*args, **kargs):
    # TODO: defaults from environment
    return EventApp()


def trigger(event_name, event_data):
    return get_current_app().trigger(event_name, event_data)
