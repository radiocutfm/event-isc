# -*- coding: utf-8 -*-
from unittest import TestCase

try:
    from unittest import mock
except ImportError:
    import mock

import eventisc


class TestEventApp(TestCase):
    def test_default_app(self):
        app = eventisc.get_current_app()
        assert app is not None

        with mock.patch.object(app, "trigger", wraps=app.trigger) as trigger_mock:
            app.trigger("myevent", {"foo": "bar"})
            trigger_mock.assert_called_once_with("myevent", {"foo": "bar"})
            trigger_mock.reset_mock()

            eventisc.trigger("myevent", {"foo": "bar"})
            trigger_mock.assert_called_once_with("myevent", {"foo": "bar"})
