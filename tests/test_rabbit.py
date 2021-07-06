# -*- coding: utf-8 -*-
from unittest import TestCase
from unittest import mock

import eventisc
import eventisc.rabbit_listener


class TestRabbitListenerApp(TestCase):
    def tearDown(self):
        eventisc.default_app = None

    def _default_rabbit_config(self):
        return {
            "event_name_regex": ".*",
            "kind": "rabbit",
            "url": "http://rabbit:5672/end",
            "queue_kwargs": {
                "exchange": {
                    "exchange": "some-exchange",
                    "exchange_type": "direct"
                },
                "queue": {
                    "queue": "some-queue"
                }
            },
            "publish_kwargs": {
                "exchange": "{queue_kwargs['exchange']['exchange']}",
                "routing_key": "{queue_kwargs['queue']['queue']}"
            }
        }

    @mock.patch.object(eventisc.rabbit_listener, "pika")
    def test_rabbit_listener(self, pika_mock):
        app = eventisc.init_default_app(listeners=[self._default_rabbit_config()])

        channel_mock = app.listeners[0].local.channel

        app.trigger('client_created', {"id": 14, "topic": "client", "action": "created"})

        channel_mock.basic_publish.assert_called_once_with(
            exchange='some-exchange',
            routing_key='some-queue',
            body='{"id": 14, "topic": "client", "action": "created"}'
        )

    @mock.patch.object(eventisc.rabbit_listener, "pika")
    def test_pika_connection(self, pika_mock):
        app = eventisc.init_default_app(listeners=[self._default_rabbit_config()])

        channel_mock = app.listeners[0].local.channel

        channel_mock.queue_declare.assert_called_once_with(queue="some-queue")

        channel_mock.exchange_declare.assert_called_once_with(
            exchange="some-exchange",
            exchange_type="direct"
        )

        channel_mock.queue_bind.assert_called_once_with(
            exchange="some-exchange",
            queue="some-queue"
        )
