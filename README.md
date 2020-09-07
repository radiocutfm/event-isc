# Inter-service event communication

This library handles inter (micro)services communication in a decoupled way using the event/observer pattern.

The code raises an event when something happens and that event fires notifications to the registered listeners.

**THIS IS A PYTHON 2.7 COMPATIBLE PACKAGE, FOR PYTHON 3 USE https://pypi.org/project/event-isc/**

Implemented notifications are:

1. Celery task
2. HTTP request


## YAML file configuration

Can be configured with a yaml file like this, passed as initialization argument or in environment variable EVENTISC_CONFIG

```yaml
name_prefix: myapp.
listeners:
- kind: http
  event_name: myapp.user_created
  url: http://notification-service.mycompany.com/send-welcome/
  requests_kwargs:
    auth: ["myuser", "password"]
  request_format: json
  data:
    user_id: "{event_data['user'].id}"
    email: "{event_data['user'].email}"
- kind: celery
  event_name_regex: myapp[.].*_created
  queue: foo_service
  task_name: foo_handle_created
  task_kwargs:
    event_name: {event_name}
    event_data: {event_data}
```


## Usage

```python

import eventisc

...
eventisc.trigger("user_created", {"user": user})  # Should fire both listeners

eventisc.trigger("foo_created", {"foo": "bar"})  # Should fire only celery

```
