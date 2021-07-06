# -*- coding: utf-8 -*-
from unittest import TestCase
from unittest import mock

import eventisc
import eventisc.rabbit_listener


class TestRabbitListenerApp(TestCase):
    def tearDown(self):
        eventisc.default_app = None

    @mock.patch.object(eventisc.rabbit_listener, "pika")
    def test_http_listener(self, pika_mock):
        app = eventisc.init_default_app(listeners=[
            {
                "event_name_regex": ".*",
                "kind": "rabbit",
                "url": "http://rabbit:5672/end",
                "queue_kwargs": {"exchange": "some-exchange", "routing_key": "some-queue"}
            }
        ])

        channel_mock = pika_mock.channel

        app.trigger('client_created', {"id": 14})

        channel_mock.basic_publish.assert_called_once_with(
            exchange='some-exchange',
            routing_key='some-queue',
            body="{'topic': 'client', 'action': 'created', id: 14}"
        )
