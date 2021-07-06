# -*- coding: utf-8 -*-
from __future__ import absolute_import
from . import Listener
import pika
import json
import threading

local = threading.local()


class RabbitListener(Listener):
    kind = "rabbit"

    def _connect(self):
        if not hasattr(local, "channel"):
            connection = pika.BlockingConnection(pika.URLParameters(self.url))
            local.channel = connection.channel()
            queue = self.queue_kwargs.get("queue", {})
            local.channel.queue_declare(**queue)
            exchange = self.queue_kwargs.get("exchange", {})
            if exchange:
                local.channel.exchange_declare(**exchange)
                local.channel.queue_bind(exchange=exchange.get("exchange"), queue=queue.get("queue"))

    def __init__(self, event_name, url, queue_kwargs=None, publish_kwargs=None, filter=None):
        super(RabbitListener, self).__init__(event_name, filter)
        self.url = url
        self.queue_kwargs = queue_kwargs
        self.publish_kwargs = publish_kwargs
        self._connect()

    def _do_notify(self, event_name, event_data):
        if self.publish_kwargs:
            data = dict((k, self.format(v, event_name, event_data, queue_kwargs=self.queue_kwargs))
                        for (k, v) in self.publish_kwargs.items())
        else:
            data = None
        data["body"] = json.dumps(event_data)
        local.channel.basic_publish(**data)
