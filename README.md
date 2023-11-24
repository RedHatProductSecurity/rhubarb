# Lock-based celery tasks using Redis

`rhubarb` provides a `LockableTask` which implements the [Redlock][1]
algorithm in order to guarantee that only one instance of a given task is
running at the same time, while preventing deadlocks from happening in case
of e.g. a worker getting killed which is not uncommon in cloud environments.

# Why is it called rhubarb?

It's a plugin for **celery** that implements the **Red**lock algorithm using
**Red**is... Have you ever seen a rhubarb? It's practically a red celery :-)


[1]: https://redis.io/docs/manual/patterns/distributed-locks/
