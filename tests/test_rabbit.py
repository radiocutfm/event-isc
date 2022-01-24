# -*- coding: utf-8 -*-
import re
from unittest import TestCase
import mock
import json

import eventisc
import eventisc.rabbit_listener


class TestRabbitListenerApp(TestCase):
    @mock.patch("eventisc.rabbit_listener.pika.BlockingConnection", autospec=True)
    def test_message_publish(self, pika_mock):
        listener = eventisc.rabbit_listener.RabbitListener(
            event_name=re.compile(".*"),
            url="amqp://rabbit:5672",
            publish_kwargs={"exchange": "", "routing_key": "testrun"},
            queue_kwargs={"queue": "testrun"},
            declare=False,
        )

        with listener.pool.acquire() as conn:
            channel = conn.channel

        listener.notify("test_event", {"some": "data"})

        channel.basic_publish.assert_called_once_with(
            body='{"some": "data"}',
            exchange="",
            routing_key="testrun",
        )

    @mock.patch("eventisc.rabbit_listener.pika.BlockingConnection", autospec=True)
    def test_declare_queue_and_exchange(self, pika_mock):
        listener = eventisc.rabbit_listener.RabbitListener(
            event_name=re.compile(".*"),
            url="amqp://rabbit:5672",
            publish_kwargs={"exchange": "", "routing_key": "testrun"},
            queue_kwargs={
                "exchange": {"exchange": "some-exchange", "exchange_type": "direct"},
                "queue": {"queue": "some-queue"},
            },
            declare=False,
        )

        with listener.pool.acquire() as conn:
            channel = conn.channel

        listener.declare_queue_and_exchange()

        channel.queue_declare.assert_called_once_with(queue="some-queue")

        channel.exchange_declare.assert_called_once_with(
            exchange="some-exchange", exchange_type="direct"
        )

        channel.queue_bind.assert_called_once_with(
            exchange="some-exchange", queue="some-queue"
        )
