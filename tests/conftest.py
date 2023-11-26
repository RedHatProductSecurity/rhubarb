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
