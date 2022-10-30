from typing import Any


class AppSettings:
    @property
    def OTP_TIME_INTERVAL(self) -> int:
        return self._settings("OTP_TIME_INTERVAL", 300)

    @property
    def AUTH_USER_MODEL(self) -> str:
        value = self._settings("AUTH_USER_MODEL", "users.User")
        return self._model(value)

    def SIMPLE_JWT_UPDATE_LOGIN_SETTING(self) -> bool:
        return self._settings("SIMPLE_JWT", {}).get("UPDATE_LAST_LOGIN", False)

    def _settings(self, name: str, default: Any = None) -> Any:
        from django.conf import settings
        return getattr(settings, name, default)

    def _config_error(self, message: str or Exception) -> None:
        from django.core.exceptions import ImproperlyConfigured
        raise ImproperlyConfigured(message)

    def _model_label(self, value: str) -> tuple[str, str]:
        try:
            app_label, model_name = value.split(".")
            return app_label, model_name
        except ValueError:
            self._config_error(f"invalid_model_format_{value}")

    def _model(self, value: str):
        from django.apps import apps

        app_label, model_name = self._model_label(value)
        try:
            return apps.get_model(app_label, model_name)
        except ValueError:
            self._config_error(f"invalid_model_class_{model_name}")


app_settings = AppSettings()

