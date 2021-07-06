# -*- coding: utf-8 -*-
from __future__ import absolute_import
from . import Listener
import pika  # noqa


class RabbitListener(Listener):
    kind = "rabbit"

    def __init__(self, event_name, url, queue_kwargs=None, filter=None):
        super(RabbitListener, self).__init__(event_name, filter)

    def _do_notify(self, event_name, event_data):
        pass
