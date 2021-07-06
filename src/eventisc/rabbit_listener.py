# -*- coding: utf-8 -*-
from __future__ import absolute_import
from . import Listener
import pika
import json


class RabbitListener(Listener):
    kind = "rabbit"

    def __init__(self, event_name, url, queue_kwargs=None, data=None, filter=None):
        super(RabbitListener, self).__init__(event_name, filter)
        self.url = url
        self.queue_kwargs = queue_kwargs
        self.data = data
        queue = self.queue_kwargs.get("routing_key")
        connection = pika.BlockingConnection(pika.URLParameters(self.url))
        self.channel = connection.channel()
        self.channel.queue_declare(queue)
        exchange = self.queue_kwargs.get("exchange")
        if exchange:
            self.channel.exchange_declare(exchange=exchange, exchange_type='direct')
            self.channel.queue_bind(exchange=exchange, queue=queue)

    def _do_notify(self, event_name, event_data):
        if self.data:
            data = dict((k, self.format(v, event_name, event_data))
                        for (k, v) in self.data.items())
        else:
            data = None
        publish_kwargs = dict(self.queue_kwargs)
        publish_kwargs["body"] = json.dumps(data)
        self.channel.basic_publish(**publish_kwargs)
