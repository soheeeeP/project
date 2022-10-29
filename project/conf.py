from typing import Any


class AppSettings:
    @property
    def OTP_TIME_INTERVAL(self) -> int:
        return self._settings("OTP_TIME_INTERVAL", 300)

    def _settings(self, name: str, default: Any = None) -> Any:
        from django.conf import settings
        return getattr(settings, name, default)


app_settings = AppSettings()

