# -*- coding: utf-8 -*-
from __future__ import absolute_import
from . import Listener
import pika
import json
import logging
import threading
from functools import wraps

logger = logging.getLogger(__name__)


def reconnection_handler(f):
    @wraps(f)
    def decorator(self, *args, **kwargs):
        try:
            ret = f(self, *args, **kwargs)
        except pika.exceptions.AMQPConnectionError:
            logger.info("Error connecting RabbitMQ, deleting channel...")
            del self.local.channel
            ret = f(self, *args, **kwargs)
        return ret
    return decorator


class RabbitListener(Listener):
    kind = "rabbit"

    def __init__(self, event_name, url, queue_kwargs=None, publish_kwargs=None, filter=None):
        super(RabbitListener, self).__init__(event_name, filter)
        self.url = url
        self.queue_kwargs = queue_kwargs
        self.publish_kwargs = publish_kwargs

        self.local = threading.local()
        self.lock = threading.Lock()
        self.connection = None

        self.declare_queue_and_exchange()

    @reconnection_handler
    def declare_queue_and_exchange(self):
        queue = self.queue_kwargs.get("queue", {})
        self.get_channel().queue_declare(**queue)
        exchange = self.queue_kwargs.get("exchange", {})
        if exchange:
            self.get_channel().exchange_declare(**exchange)
            self.get_channel().queue_bind(exchange=exchange.get("exchange"), queue=queue.get("queue"))

    def get_channel(self):
        self._connect()

        if hasattr(self.local, 'channel'):
            return self.local.channel

        try:
            self.local.channel = self.connection.channel()
        except pika.exceptions.AMQPConnectionError:
            logger.info("Error connecting RabbitMQ, getting new connection...")
            self._connect(force_reconnect=True)
            self.local.channel = self.connection.channel()

        return self.local.channel

    def _connect(self, force_reconnect=False):
        # thread safe connection aquire
        with self.lock:
            if force_reconnect:
                self.connection = None

            if self.connection is not None:
                return

            self.connection = pika.BlockingConnection(pika.URLParameters(self.url))

        if not hasattr(self.local, "channel"):
            self.local.channel = self.connection.channel()

    @reconnection_handler
    def _do_notify(self, event_name, event_data):
        if self.publish_kwargs:
            data = dict((k, self.format(v, event_name, event_data, queue_kwargs=self.queue_kwargs))
                        for (k, v) in self.publish_kwargs.items())
        else:
            data = None
        data["body"] = json.dumps(event_data)
        self.get_channel().basic_publish(**data)


RabbitListener.register()
