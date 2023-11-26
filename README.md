# Lock-based celery tasks using Redis

`rhubarb` provides a `LockableTask` which implements the [Redlock][1]
algorithm in order to guarantee that only one instance of a given task is
running at the same time, while preventing deadlocks from happening in case
of e.g. a worker getting killed, which is not uncommon in cloud environments.


## Why use rhubarb?

There are certainly other very similar libraries and tools that can help you
achieve the same results, but rhubarb aims to be a very opinionated approach
to the same problem these other libraries solve. You can use rhubarb without
changing any settings and be confident that the defaults will be enough to
not worry about it.

Rhubarb's long-term goal is to guarantee exclusive task execution with minimal,
almost inexistent downtime while taking resiliency towards unexpected worker
termination very seriously.


## Usage

```python
from rhubarb.tasks import LockableTask

@app.task(base=LockableTask)
def my_task():
    ...
```


## Settings

See the official celery [docs][2] on where/how to set the following settings:

* `rhubarb_backend_url`: URL to the Redis instance which will be used for
  creating the locks. If not present, will fallback to Celery's `broker_url`
  or `result_backend` settings, in that order of precedence.
* `rhubarb_backend_kwargs`: Dict of keyword arguments to pass to the Redis
  connection constructor, use for anything not present in the URL. Note that
  query parameters in the URL always take precedence over key-value pairs in
  this dict.
* `rhubarb_task_lock_ttl`: Global default expiry time for locks in seconds,
  if not present will default to 60 minutes.


## Testing

* Make sure you install both `requirements.txt` and `requirements-testing.txt`.
* Set up a local Redis instance, the `tests/` directory includes a `compose.yml`
  file which sets up a local Redis instance using `docker` and `docker-compose`.
* Run the `tox` command.


## Why is it called rhubarb?

It's a plugin for **celery** that implements the **Red**lock algorithm using
**Red**is... Have you ever seen a rhubarb? It's practically a red celery :-)


[1]: https://redis.io/docs/manual/patterns/distributed-locks/
[2]: https://docs.celeryq.dev/en/stable/userguide/configuration.html
