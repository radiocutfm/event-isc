# Inter-service event communication

This library handles inter (micro)services communication in a decoupled way using the event/observer pattern.

The code raises an event when something happens and that event fires notifications to the registered listeners.

**THIS IS A PYTHON 2.7 COMPATIBLE PACKAGE, FOR PYTHON 3 USE https://pypi.org/project/event-isc/**

Implemented notifications are:

1. Celery task
2. HTTP request
3. RabbitMQ Message


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


## RabbitMQ / Pika special behaviour

Pika does not support multithreading, pika-pool is used to have thread-safety but still have long-lived persistent
connections.

You should periodically call `eventisc.heartbeat` if you're planning on supporting rabbit listeners. This ensures
server heartbeats are handled and reduces connection churn:

```python
import threading

def heartbeat_thread():
    while True:
        time.sleep(60)  # 60 is pika's default as of 1.2.0
        app.heartbeat()


t = threading.Thread(target=heartbeat_thread, daemon=True)
t.start()
```

Alternatively, users can avoid connection lost errors by setting the `stale` parameter lower than the heartbeat
timeout:

```yaml
listeners:
  - kind: rabbit
    event_name_regex: .*
    url: "amqp://localhost:5672/?heartbeat=90"  # heartbeat timeout set to 90 secs
    queue_kwargs:
      queue:
        queue: myqueue
    publish_kwargs:
      exchange: ""
      routing_key: "{queue_kwargs['queue']['queue']}"
    stale: 60
```

This will *not* avoid connection churn, but it should reduce the chances of getting a connection error when sending a
message.
