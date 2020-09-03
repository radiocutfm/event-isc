# Inter-service event communication

This library handles inter (micro)services communication in a decoupled way using the event/observer pattern.

The code raises an event when something happens and that event fires notifications to the registered listeners.

Implemented notifications are:

1. Celery task 
2. HTTP request 


