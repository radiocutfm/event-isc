# -*- coding: utf-8 -*-
from unittest import TestCase
import json
import responses
import eventisc


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

    @responses.activate
    def test_auth_param(self):
        app = eventisc.init_default_app(listeners=[
            {
                "event_name_regex": ".*",
                "kind": "http",
                "url": "http://example.com/notify/{event_name}/",
                "data": {"foo": "{event_data['foo']}"},
                "requests_kwargs": {"auth": ["myuser", "mypassword"]},
            }
        ])

        responses.add(
            responses.POST,
            "http://example.com/notify/something_else/",
        )

        app.trigger('something_else', {"foo": "bar"})

        request = responses.calls[0].request
        assert json.loads(request.body) == {
            "foo": "bar"
        }
        assert request.headers["Authorization"] == "Basic bXl1c2VyOm15cGFzc3dvcmQ="
