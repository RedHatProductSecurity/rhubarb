import ssl

import pytest

from rhubarb.tasks import Lock, LockableTask, LockableTaskWithArgs


class TestLockableTask:
    def _get_task_instance(self, celery_app):
        @celery_app.task(base=LockableTask)
        def my_task():
            return

        return celery_app.tasks["tests.test_tasks.my_task"]

    def test_init(self, celery_app):
        """
        Test that task initialization sets up the necessary attributes.
        """
        task_instance = self._get_task_instance(celery_app)
        assert task_instance.lock_key == "tests.test_tasks.my_task_lock"
        assert task_instance._LockableTask__lock is None

    def test_standard_connection(self, celery_app):
        """
        Test that the connection to the Redis server works.
        """
        task_instance = self._get_task_instance(celery_app)
        assert task_instance._LockableTask__redis_client.ping() is True

    @pytest.mark.celery(
        rhubarb_backend_url="rediss://localhost:7000/",
        rhubarb_backend_kwargs={
            "ssl_keyfile": "./tests/etc/redis/redis.key",
            "ssl_certfile": "./tests/etc/redis/redis.crt",
            "ssl_ca_certs": "./tests/etc/redis/ca.crt",
            "ssl_cert_reqs": ssl.CERT_REQUIRED,
        },
    )
    def test_tls_connection(self, celery_app):
        task_instance = self._get_task_instance(celery_app)
        assert task_instance._LockableTask__redis_client.ping() is True

    def test_acquire_lock(self, celery_app):
        """
        Test that acquiring a lock actually acquires said lock.
        """
        task_instance = self._get_task_instance(celery_app)
        assert task_instance.acquire_lock() is True

        lock = task_instance._LockableTask__lock
        assert lock is not None

        assert task_instance.lock_key == lock.key
        # use getdel to cleanup test redis instance
        assert (
            task_instance._LockableTask__redis_client.getdel(lock.key)
            == lock.val.encode()
        )

    def test_reacquire_lock(self, celery_app):
        """
        Test that reacquiring the same lock fails.
        """
        task_instance = self._get_task_instance(celery_app)
        assert task_instance.acquire_lock() is True
        assert task_instance.acquire_lock() is False
        # cleanup test redis instance
        task_instance._LockableTask__redis_client.getdel(
            task_instance._LockableTask__lock.key
        )

    def test_release_lock(self, celery_app):
        """
        Test that releasing a lock actually releases it.
        """
        task_instance = self._get_task_instance(celery_app)
        task_instance.acquire_lock()
        lock = task_instance._LockableTask__lock
        assert task_instance.release_lock()
        assert not task_instance._LockableTask__redis_client.get(lock.key)

    def test_release_unacquired_lock(self, celery_app):
        """
        Test that releasing an unacquired locked is a no-op.
        """
        task_instance = self._get_task_instance(celery_app)
        assert task_instance.release_lock() is False

    def test_release_lock_different_owner(self, celery_app):
        """
        Test that attempting to release a lock not owned by the current process fails.
        """
        task_instance = self._get_task_instance(celery_app)
        assert task_instance.acquire_lock()
        # simulate different owner by creating a new lock
        old_lock = task_instance._LockableTask__lock
        new_lock = Lock(old_lock.key, "foo", old_lock.ttl)
        task_instance._LockableTask__lock = new_lock
        assert task_instance.release_lock() is False
        # test that releasing old lock works (and cleanup)
        task_instance._LockableTask__lock = old_lock
        assert task_instance.release_lock() is True

    def test_ttl_per_task(self, celery_app):
        @celery_app.task(base=LockableTask, lock_ttl=1337)
        def my_task():
            return

        task_instance = celery_app.tasks["tests.test_tasks.my_task"]
        task_instance.acquire_lock()

        lock = task_instance._LockableTask__lock

        assert lock is not None
        assert lock.ttl == 1337

        # use getdel to cleanup test redis instance
        assert (
            task_instance._LockableTask__redis_client.getdel(lock.key)
            == lock.val.encode()
        )


class TestIntegration:
    def test_single_run(self, celery_app, celery_worker):
        """
        Test that running a task works as expected.
        """

        @celery_app.task(
            base=LockableTask, name="tests.test_tasks.test_single_run.my_task"
        )
        def my_task():
            return "foo"

        task_exec = my_task.apply()
        result, output = next(task_exec.collect(timeout=10))

        assert output == "foo"
        assert result.state == "SUCCESS"

    def test_duplicate_run(self, celery_app, celery_worker):
        """
        Test that running the same task in parallel fails.
        """

        @celery_app.task(base=LockableTask)
        def my_task():
            return "foo"

        # simulate the task already running (i.e. acquired lock) as there is no
        # easy way to test concurrent task execution with pytest
        task_instance = celery_app.tasks["tests.test_tasks.my_task"]
        task_instance.acquire_lock()

        # actually execute the task
        task_exec = my_task.apply()
        result, output = next(task_exec.collect(timeout=10))

        assert output is None
        # Celery overrides the task's state based on the raised exception
        assert result.state == "REJECTED"
        # cleanup
        task_instance.release_lock()

    def test_with_params(self, celery_app, celery_worker):
        """
        Test that running multiple tasks with different parameters works as expected.
        """

        @celery_app.task(base=LockableTaskWithArgs)
        def my_task(param):
            return param

        # simulate the task already running (i.e. acquired lock) as there is no
        # easy way to test concurrent task execution with pytest
        task_instance = celery_app.tasks["tests.test_tasks.my_task"]
        task_instance.before_start("mock_task_id", args=["bar"], kwargs={})

        task_exec = my_task.apply(args=["foo"])
        result, output = next(task_exec.collect(timeout=10))

        assert output == "foo"
        assert result.state == "SUCCESS"
        # cleanup
        task_instance.release_lock()

    def test_with_params_duplicate(self, celery_app, celery_worker):
        """
        Test that running the same task with the same parameters in parallel fails.
        """

        @celery_app.task(base=LockableTaskWithArgs)
        def my_task(param):
            return param

        # simulate the task already running (i.e. acquired lock) as there is no
        # easy way to test concurrent task execution with pytest
        task_instance = celery_app.tasks["tests.test_tasks.my_task"]
        task_instance.before_start("mock_task_id", args=["foo"], kwargs={})

        # actually execute the task
        task_exec = my_task.apply(args=["foo"])
        result, output = next(task_exec.collect(timeout=10))

        assert output is None
        assert result.state == "REJECTED"
        # cleanup
        task_instance.release_lock()
