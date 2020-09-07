# -*- coding: utf-8 -*-
from unittest import TestCase
import eventisc
import eventisc.celery_listener

from unittest import mock


class TestCeleryListener(TestCase):
    def tearDown(self):
        eventisc.default_app = None

    @mock.patch.object(eventisc.celery_listener, "current_app")
    def test_celery_listener(self, celery_mock):
        app = eventisc.init_default_app(listeners=[
            {
                "event_name_regex": ".*",
                "kind": "celery", "queue": "cola", "task_name": "{event_name}",
                "task_kwargs": {"foo": "{event_data['foo']}", "fofofo": "Esto esta {event_data[foo]}",
                                "bar": 3, "barcito": "{event_data['bar']}"},
                "send_task_kargs": {"priority": 3, "serializer": "json"},
            }
        ])

        app.trigger('something', {"foo": "FFOO", "bar": 43})
        celery_mock.send_task.assert_called_once_with(
            'something', args=[],
            kwargs={'foo': 'FFOO', 'fofofo': 'Esto esta FFOO', 'bar': 3, 'barcito': 43},
            priority=3, queue='cola', serializer='json'
        )

    @mock.patch.object(eventisc.celery_listener, "current_app")
    def test_celery_default_kwargs(self, celery_mock):
        app = eventisc.init_default_app(listeners=[
            {
                "event_name_regex": ".*",
                "kind": "celery", "queue": "cola", "task_name": "event_receiver",
            }
        ])

        app.trigger('something', {"foo": "FFOO", "bar": 43})
        celery_mock.send_task.assert_called_once_with(
            'event_receiver', args=[],
            kwargs={'event_name': 'something', "event_data": {"foo": "FFOO", "bar": 43}},
            queue="cola",
        )

    @mock.patch.object(eventisc.celery_listener, "current_app")
    def test_celery_both(self, celery_mock):
        app = eventisc.init_default_app(listeners=[
            {
                "event_name_regex": ".*",
                "task_args": ["{event_name}"], "task_kwargs": "**event_data",
                "kind": "celery", "queue": "cola", "task_name": "event_receiver",
            }
        ])

        app.trigger('something', {"foo": "FFOO", "bar": 43})
        celery_mock.send_task.assert_called_once_with(
            'event_receiver', args=["something"],
            kwargs={"foo": "FFOO", "bar": 43},
            queue="cola",
        )
