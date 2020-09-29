import logging
from . import Listener
from environs import Env
from celery import current_app

env = Env()
logger = logging.getLogger()


class CeleryListener(Listener):
    kind = "celery"

    def __init__(self, event_name, queue, task_name, task_args=None, task_kwargs=None,
                 send_task_kargs={}, filter=None):
        super().__init__(event_name, filter)
        self.queue = queue
        self.task_name = task_name
        if task_args is None and task_kwargs is None:
            self.task_args = []
            self.task_kwargs = {"event_name": "{event_name}", "event_data": "{event_data}"}
        elif task_args is None:
            self.task_args = []
            self.task_kwargs = task_kwargs
        elif task_kwargs is None:
            self.task_args = task_args
            self.task_kwargs = {}
        else:
            self.task_args = task_args
            self.task_kwargs = task_kwargs
        self.send_task_kargs = send_task_kargs

    def _do_notify(self, event_name, event_data):
        queue = self.format(self.queue, event_name, event_data)
        task_name = self.format(self.task_name, event_name, event_data)
        args = [self.format(arg, event_name, event_data) for arg in self.task_args]
        if self.task_kwargs == "**event_data":
            kwargs = event_data
        else:
            kwargs = dict((k, self.format(v, event_name, event_data))
                          for (k, v) in self.task_kwargs.items())
        self.send_task(
            task_name,
            args=args, kwargs=kwargs,
            queue=queue,
            **self.send_task_kargs
        )
        return True

    def _do_notify_dryrun(self, event_name, event_data):
        logger.info("EVENTISC_DRYRUN=Y _do_notify(%s, %s)", event_name, event_data)
        return self._do_notify(event_name, event_data)  # send_task supports EVENTISC_DRYRUN

    @classmethod
    def send_task(cls, *args, **kwargs):
        if env.bool("EVENTISC_DRYRUN", False):
            logger.info("send_task(args={}, kwargs={}".format(args, kwargs))
        else:
            return current_app.send_task(*args, **kwargs)
