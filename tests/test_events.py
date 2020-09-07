# -*- coding: utf-8 -*-
import os
import tempfile
from unittest import TestCase
import eventisc

import mock


class MyTestListener(eventisc.Listener):
    kind = "test"

    def __init__(self, event_name, filter=None, foo=None):
        super(MyTestListener, self).__init__(event_name, filter)
        self.foo = foo
        self.mock = mock.MagicMock()

    def _do_notify(self, event_name, event_data):
        return self.mock(event_name, event_data)


MyTestListener.register()


class TestEventApp(TestCase):
    def tearDown(self):
        eventisc.default_app = None

    def test_default_app(self):
        app = eventisc.get_current_app()
        assert app is not None

        with mock.patch.object(app, "trigger", wraps=app.trigger) as trigger_mock:
            app.trigger("myevent", {"foo": "bar"})
            trigger_mock.assert_called_once_with("myevent", {"foo": "bar"})
            trigger_mock.reset_mock()

            eventisc.trigger("myevent", {"foo": "bar"})
            trigger_mock.assert_called_once_with("myevent", {"foo": "bar"})

    def test_init_manual(self):
        my_listener = MyTestListener("testapp.myevent")
        app = eventisc.init_default_app("testapp.", [my_listener])
        assert app is not None
        assert len(app.listeners) == 1

        eventisc.trigger("fooevent", {"fii": "bar"})
        my_listener.mock.assert_not_called()

        eventisc.trigger("myevent", {"fii": "bar"})
        my_listener.mock.assert_called_once_with("testapp.myevent", {"fii": "bar"})

    @mock.patch.dict(os.environ, {"EVENTISC_NAME_PREFIX": "envname."})
    def test_init_from_dict(self):
        eventisc.init_default_app(listeners=[
            {"kind": "test", "event_name": "envname.myevent", "foo": 23},
            {"kind": "test", "event_name_regex": ".*_created", "foo": 45},
        ])

        app = eventisc.get_current_app()
        assert app.name_prefix == "envname."
        assert len(app.listeners) == 2

        assert isinstance(app.listeners[0], MyTestListener)
        assert app.listeners[0].foo == 23
        assert app.listeners[1].foo == 45

        count = eventisc.trigger("fooevent", {"fii": "bar"})
        assert count == 0

        count = eventisc.trigger("myevent", {"fii": "bar"})
        assert count == 1
        app.listeners[0].mock.assert_called_once_with("envname.myevent", {"fii": "bar"})
        app.listeners[1].mock.assert_not_called()
        app.listeners[0].mock.reset_mock()

        count = eventisc.trigger("bar_created", {"bar_name": "Moe's"})
        assert count == 1
        app.listeners[0].mock.assert_not_called()
        app.listeners[1].mock.assert_called_once_with("envname.bar_created", {"bar_name": "Moe's"})

    def test_init_from_json(self):
        config = """{"name_prefix": "jsonapp.",
            "listeners": [{"kind": "test", "event_name": "jsonapp.myevent", "foo": 33}]
        }"""

        config_file = tempfile.NamedTemporaryFile(suffix=".json", mode="wt")
        config_file.write(config)
        config_file.flush()

        with mock.patch.dict(os.environ, {"EVENTISC_CONFIG": config_file.name}):
            app = eventisc.get_current_app()
            assert app.name_prefix == "jsonapp."
            assert len(app.listeners) == 1
            assert app.listeners[0].foo == 33

    def test_init_from_yaml(self):
        config = """name_prefix: yamlapp.
listeners:
 - kind: test
   event_name: jsonapp.myevent
   foo: 666
"""

        config_file = tempfile.NamedTemporaryFile(suffix=".yaml", mode="wt")
        config_file.write(config)
        config_file.flush()

        with mock.patch.dict(os.environ, {"EVENTISC_CONFIG": config_file.name}):
            app = eventisc.get_current_app()
            assert app.name_prefix == "yamlapp."
            assert len(app.listeners) == 1
            assert app.listeners[0].foo == 666

    def test_filter_expression(self):
        eventisc.init_default_app(listeners=[
            {"kind": "test", "event_name": "myevent", "foo": 23,
             "filter": {"kind": "expr", "expr": "event_data['fii'] > 10"}},
        ])

        app = eventisc.get_current_app()
        assert len(app.listeners) == 1

        assert isinstance(app.listeners[0], MyTestListener)
        assert app.listeners[0].foo == 23

        count = eventisc.trigger("myevent", {"fii": 34})
        assert count == 1
        app.listeners[0].mock.assert_called_once_with("myevent", {"fii": 34})
        app.listeners[0].mock.reset_mock()

        count = eventisc.trigger("myevent", {"fii": 9})
        assert count == 0
        app.listeners[0].mock.assert_not_called()

    @mock.patch.dict(os.environ, {"EVENTISC_DRYRUN": "1"})
    def test_dry_run(self):
        eventisc.init_default_app(listeners=[
            {"kind": "test", "event_name": "myevent", "foo": 23},
        ])

        app = eventisc.get_current_app()
        assert len(app.listeners) == 1

        assert isinstance(app.listeners[0], MyTestListener)
        assert app.listeners[0].foo == 23

        with mock.patch.object(eventisc.logger, "info", wraps=eventisc.logger.info) as info_log:
            count = eventisc.trigger("myevent", {"fii": 34})
            assert count == 1
            app.listeners[0].mock.assert_not_called()
            info_log.assert_called_once_with('EVENTISC_DRYRUN=Y _do_notify(%s, %s)',
                                             'myevent', {'fii': 34})
