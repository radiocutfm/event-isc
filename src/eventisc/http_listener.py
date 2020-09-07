from __future__ import absolute_import
from urllib import urlencode
import requests
from . import Listener


class HttpListener(Listener):
    kind = "http"

    def __init__(self, event_name, url, method="post", query_kwargs=None, data=None,
                 requests_kwargs=None, request_format="json", filter=None):
        super(HttpListener, self).__init__(event_name, filter)
        self.url = url
        self.method = method
        self.requests_kwargs = requests_kwargs or {}
        if "auth" in self.requests_kwargs:
            # Fix: auth parameter must be tuple and if read from yaml is list
            self.requests_kwargs["auth"] = tuple(self.requests_kwargs["auth"])
        self.query_kwargs = query_kwargs
        self.data = data
        self.request_format = request_format

    def _do_notify(self, event_name, event_data):
        if self.query_kwargs:
            query_kwargs = dict((k, self.format(v, event_name, event_data))
                                for (k, v) in self.query_kwargs.items())
            query_string = urlencode(query_kwargs)
        else:
            query_string = ""

        url = self.format(self.url, event_name, event_data, query_string=query_string)

        if self.data:
            data = dict((k, self.format(v, event_name, event_data))
                        for (k, v) in self.data.items())
        else:
            data = None

        request_method = getattr(requests, self.method)

        if self.request_format == "json":
            resp = request_method(url, json=data, **self.requests_kwargs)
        else:
            resp = request_method(url, data=data, **self.requests_kwargs)

        resp.raise_for_status()

        return True


HttpListener.register()
