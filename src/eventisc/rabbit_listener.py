# -*- coding: utf-8 -*-
from __future__ import absolute_import
from . import Listener
import json
import logging
from functools import wraps

import pika
import pika_pool

logger = logging.getLogger(__name__)

# Reduce pika's verbosity
logging.getLogger("pika").setLevel(logging.WARNING)


def retry_on_connection_error(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            ret = f(*args, **kwargs)
        except pika.exceptions.AMQPConnectionError:
            logger.warning("AMQPConnection error executing %s. Retrying...", f.__name__)
            ret = f(*args, **kwargs)
        except Exception as e:
            logger.warning("Ignoring exception %s from decorated function %s: %s", type(e), f.__name__, e)
            raise
        return ret
    return decorated


class RabbitListener(Listener):
    kind = "rabbit"

    def __init__(self, event_name, url, queue_kwargs=None, publish_kwargs=None, filter=None, stale=None, declare=True):
        super(RabbitListener, self).__init__(event_name, filter)
        self.url = url
        self.queue_kwargs = queue_kwargs
        self.publish_kwargs = publish_kwargs

        self.pool = pika_pool.QueuedPool(
            create=lambda: pika.BlockingConnection(pika.URLParameters(self.url)),
            stale=stale
        )

        if declare:
            self.declare_queue_and_exchange()

    def heartbeat(self):
        self.pool.process_data_events()

    @retry_on_connection_error
    def declare_queue_and_exchange(self):
        queue = self.queue_kwargs.get("queue", {})
        exchange = self.queue_kwargs.get("exchange", {})
        with self.pool.acquire() as conn:
            conn.channel.queue_declare(**queue)
            if exchange:
                conn.channel.exchange_declare(**exchange)
                conn.channel.queue_bind(exchange=exchange.get("exchange"), queue=queue.get("queue"))

    @retry_on_connection_error
    def _do_notify(self, event_name, event_data):
        if self.publish_kwargs:
            data = dict((k, self.format(v, event_name, event_data, queue_kwargs=self.queue_kwargs))
                        for (k, v) in self.publish_kwargs.items())
        else:
            data = None
        data["body"] = json.dumps(event_data)
        with self.pool.acquire() as conn:
            conn.channel.basic_publish(**data)
        return True
