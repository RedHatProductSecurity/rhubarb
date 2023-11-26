from celery import exceptions


class ConcurrentExecutionException(exceptions.Reject):
    """
    Raised when trying to execute a task that is already running.

    Since a LockableTask acquires a mutex lock when it's executed, another
    execution of the same task is impossible until the lock is released by
    the first execution of the task coming to an end or by lock expiration.

    The choice of inheriting from exceptions.Reject is an explicit one, as it
    is not processed by the `on_failure`, `on_success` or `on_retry` hooks, we
    do not want a ConcurrentExecutionException to release the lock of a
    currently running task, we simply want it to prevent execution of the task.
    """

    pass
