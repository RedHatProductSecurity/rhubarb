import pytest


@pytest.fixture(scope="session")
def local_redis_instance_url():
    return "redis://localhost:6399/"


@pytest.fixture(scope="session")
def celery_config(local_redis_instance_url):
    return {
        "broker_url": local_redis_instance_url,
        "result_backend": local_redis_instance_url,
    }


@pytest.fixture(scope="session", autouse=True)
def clean_redis_instance(local_redis_instance_url):
    """
    Failed tests can leave a lock between runs.
    This fixture will remove the lock from
    the redis server before running the tests.
    """
    import redis

    client = redis.from_url(local_redis_instance_url)
    client.flushdb()
    client.close()
