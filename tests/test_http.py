# -*- coding: utf-8 -*-
from unittest import TestCase
import json
import responses
import eventisc
import eventisc.http_listener  # noqa


class TestHTTPListenerApp(TestCase):
    def tearDown(self):
        eventisc.default_app = None

    @responses.activate
    def test_http_listener(self):
        app = eventisc.init_default_app(listeners=[
            {
                "event_name_regex": ".*",
                "kind": "http",
                "url": "http://example.com/notify/{event_name}/?{query_string}",
                "query_kwargs": {"fifi": "{event_data['foo']}"},
                "data": {"foo": "{event_data['foo']}", "fofofo": "Esto esta {event_data[foo]}",
                         "bar": 3, "barcito": "{event_data['bar']}"},
                "requests_kwargs": {"headers": {"X-Foo": "sss"}},
            }
        ])

        responses.add(
            responses.POST,
            "http://example.com/notify/something/?fifi=FFOO",
        )

        app.trigger('something', {"foo": "FFOO", "bar": 43})

        request = responses.calls[0].request
        assert json.loads(request.body) == {
            "foo": "FFOO", "fofofo": "Esto esta FFOO",
            "bar": 3, "barcito": 43
        }
        assert request.headers["X-Foo"] == "sss"
