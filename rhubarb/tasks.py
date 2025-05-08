import functools
import hashlib
import uuid
from dataclasses import dataclass

import redis
from celery import Task

from rhubarb.constants import REDIS_LOCK_RELEASE_SCRIPT
from rhubarb.exceptions import ConcurrentExecutionException
from rhubarb.settings import Settings


@dataclass
class Lock:
    key: str
    val: str
    ttl: int


class LockableTask(Task):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lock_key = f"{self.name}_lock"
        self.__lock = None
        self.__lock_ttl = getattr(
            self, "lock_ttl", self._rhubarb_settings.TASK_LOCK_TTL
        )

    @functools.cached_property
    def _rhubarb_settings(self) -> Settings:
        return Settings(self.app)

    @functools.cached_property
    def __redis_client(self) -> redis.Redis:
        return redis.from_url(
            self._rhubarb_settings.BACKEND_URL,
            **self._rhubarb_settings.BACKEND_KWARGS,
        )

    def _gen_unique_value(self) -> str:
        return str(uuid.uuid4())

    def acquire_lock(self, ttl=None) -> bool:
        """
        Create a lock in Redis for the current task being executed.

        This method will create a KEY in the Redis instance, the name of said
        KEY is the task's name + the "_lock" suffix, the value is the string
        representation of an UUIDv4 and by default the KEY expires in
        TASK_LOCK_TTL seconds.

        The KEY is only created if it does not already exist.

        This method returns True if the KEY was successfully created, signaling
        that the lock was acquired, and False if the lock is already in use.
        """

        if ttl is None:
            ttl = self.__lock_ttl
        lock = Lock(self.lock_key, self._gen_unique_value(), ttl)
        if locked := self.__redis_client.set(lock.key, lock.val, nx=True, ex=lock.ttl):
            # lock has been successfully acquired
            self.__lock = lock
        return bool(locked)

    def release_lock(self) -> bool:
        """
        Release an existing lock in Redis for the current task being executed.

        This method will attempt to release the lock for the current task iff
        the caller is the owner of the Redis lock.

        If there is no lock or the caller does not match the owner (the UUIDv4)
        then the method returns False and is essentially a no-op.

        If there is a lock and the caller matches the owner of the lock, the
        KEY is deleted from Redis, signaling a release of the lock.
        """
        if lock := self.__lock:
            return bool(
                self.__redis_client.eval(
                    REDIS_LOCK_RELEASE_SCRIPT,
                    1,
                    lock.key,
                    lock.val,
                )
            )
        return False

    def extend_lock(self, ttl=None):
        """
        Extend the TTL of the KEY that serves as a lock.

        Currently unused.
        """
        if ttl is None:
            ttl = self.__lock_ttl
        self.__redis_client.expire(self.lock_key, ttl)

    def before_start(self, task_id, args, kwargs):
        if not self.acquire_lock():
            # We need both of these so that Flower doesn't treat them as active
            self.update_state(task_id, state="DUPLICATE")
            self.send_event("task-revoked")
            raise ConcurrentExecutionException(
                f"Failed to acquire lock for task {self.name} with ID {task_id}, skipping."
            )

    def on_success(self, retval, task_id, args, kwargs):
        self.release_lock()

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        self.release_lock()

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        self.release_lock()


class LockableTaskWithArgs(LockableTask):
    """
    A subclass of LockableTask that generates a unique lock key based on the
    task's arguments.
    """

    def before_start(self, task_id, args, kwargs):
        self.lock_key = (
            f"{self.name}_{hashlib.sha256(str(args).encode()).hexdigest()}_lock"
        )
        super().before_start(task_id, args, kwargs)
