import pytest
from celery.exceptions import ImproperlyConfigured

from rhubarb.settings import Settings


# override conftest
@pytest.fixture
def celery_config():
    return {}


class TestBackendUrl:
    @pytest.mark.celery(broker_url="redis://")
    def test_default_backend(self, celery_app):
        """
        Copy celery's BROKER_URL setting by default.
        """
        settings = Settings(celery_app)
        assert settings.BACKEND_URL == celery_app.conf.broker_url

    @pytest.mark.celery(result_backend="redis://")
    def test_fallback_backend(self, celery_app):
        """
        Copy celery's RESULT_BACKEND as fallback.
        """
        settings = Settings(celery_app)
        assert settings.BACKEND_URL == celery_app.conf.result_backend

    @pytest.mark.celery(broker_url="amqp://", result_backend="redis://")
    def test_fallback_if_not_redis(self, celery_app):
        """
        Copy celery's RESULT_BACKEND if BROKER_URL is not redis.
        """
        settings = Settings(celery_app)
        assert settings.BACKEND_URL == celery_app.conf.result_backend

    @pytest.mark.celery(rhubarb_backend_url="redis://")
    def test_explicit_rhubarb_backend_url(self, celery_app):
        """
        Use rhubarb-specific backend url.
        """
        settings = Settings(celery_app)
        assert settings.BACKEND_URL == "redis://"

    @pytest.mark.celery(
        rhubarb_backend_url="redis://", broker_url="amqp://", result_backend="django-db"
    )
    def test_precedence_backend_url(self, celery_app):
        """
        Use rhubarb-specific backend url over other options when available.
        """
        settings = Settings(celery_app)
        assert settings.BACKEND_URL == "redis://"

    @pytest.mark.celery(broker_url="rediss://")
    def test_ssl_connection(self, celery_app):
        """
        Use SSL connection urls.
        """
        settings = Settings(celery_app)
        assert settings.BACKEND_URL == "rediss://"

    @pytest.mark.celery(broker_url="amqp://", result_backend="django-db")
    def test_no_redis_backend_available(self, celery_app):
        """
        Raise ImproperlyConfigured if no valid backend has been configured.
        """
        settings = Settings(celery_app)
        with pytest.raises(ImproperlyConfigured, match="No valid backend was found"):
            settings.BACKEND_URL

    @pytest.mark.celery
    def test_default_backend_kwargs(self, celery_app):
        """
        Use empty dict for Redis connection kwargs if not explicitly defined.
        """
        settings = Settings(celery_app)
        assert settings.BACKEND_KWARGS == {}

    @pytest.mark.celery(rhubarb_backend_kwargs={"foo": "bar"})
    def test_explicit_backend_kwargs(self, celery_app):
        """
        Use explicit dict for Redis connection kwargs.
        """
        settings = Settings(celery_app)
        assert settings.BACKEND_KWARGS == {"foo": "bar"}

    @pytest.mark.celery
    def test_default_task_lock_ttl(self, celery_app):
        """
        Use the default TASK_LOCK_TTL value if not explicitly defined.
        """
        settings = Settings(celery_app)
        assert settings.TASK_LOCK_TTL == 3600

    @pytest.mark.celery(rhubarb_task_lock_ttl=60)
    def test_explicit_task_lock_ttl(self, celery_app):
        """
        Use explicit value for TASK_LOCK_TTL.
        """
        settings = Settings(celery_app)
        assert settings.TASK_LOCK_TTL == 60
