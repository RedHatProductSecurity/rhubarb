from celery.exceptions import ImproperlyConfigured


class Settings:
    def __init__(self, app):
        self.app = app

    def _get(self, key: str, default=None):
        return self.app.conf.get(key, default)

    @property
    def BACKEND_URL(self) -> str:
        # fallback to celery's broker url
        url = self._get("rhubarb_backend_url", self._get("broker_url"))
        if url is None or not url.startswith("redis"):
            # fallback to celery's results backend
            url = self._get("result_backend")
        if url is None or not url.startswith("redis"):
            raise ImproperlyConfigured("No valid backend was found")
        return url

    @property
    def BACKEND_KWARGS(self) -> dict:
        return self._get("rhubarb_backend_kwargs", {})

    @property
    def TASK_LOCK_TTL(self) -> int:
        return self._get("rhubarb_task_lock_ttl", 3600)
