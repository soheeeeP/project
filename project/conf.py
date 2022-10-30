import inspect
from typing import Any


class AppSettings:
    @property
    def OTP_TIME_INTERVAL(self) -> int:
        return self._settings("OTP_TIME_INTERVAL", 300)

    @property
    def AUTH_USER_MODEL(self) -> str:
        value = self._settings("AUTH_USER_MODEL", "users.User")
        return self._model(value)

    @property
    def SIMPLE_JWT_UPDATE_LOGIN_SETTING(self) -> bool:
        return self._settings("SIMPLE_JWT", {}).get("UPDATE_LAST_LOGIN", False)

    @property
    def REST_FRAMEWORK_AUTHENTICATION_CLASSES(self) -> Any:
        default = "rest_framework_simplejwt.authentication.JWTAuthentication"
        value = self._multiple_settings("REST_FRAMEWORK", "DEFAULT_AUTHENTICATION_CLASSES", {}, default)
        return value

    @property
    def REST_FRAMEWORK_JSON_RESPONSE_RENDERER(self) -> Any:
        default = "rest_framework.renderers.JSONRenderer"
        value = self._multiple_settings("REST_FRAMEWORK", "DEFAULT_RENDERER_CLASSES", {}, default)
        return value

    @property
    def REST_FRAMEWORK_THROTTLE_CLASSES(self) -> Any:
        default = (
            'rest_framework.throttling.AnonRateThrottle',
            'rest_framework.throttling.UserRateThrottle'
        )
        value = self._multiple_settings("REST_FRAMEWORK", "DEFAULT_THROTTLE_CLASSES", {}, default)
        return value

    @property
    def REST_FRAMEWORK_DEFAULT_THROTTLE_RATES(self) -> Any:
        default = (
            'rest_framework.throttling.AnonRateThrottle',
            'rest_framework.throttling.UserRateThrottle'
        )
        value = self._settings("REST_FRAMEWORK", {}).get("DEFAULT_THROTTLE_RATES", default)
        return value

    def _multiple_settings(self, name: str, detail: str, name_default: Any = None, detail_default: Any = None) -> Any:
        settings = self._settings(name, name_default)
        value = settings.get(detail, detail_default)
        print(value)
        if isinstance(value, str):
            return self._class(value)
        elif isinstance(value, list) or isinstance(value, tuple):
            return [self._class(v) for v in value]
        elif isinstance(value, dict):
            return {k: self._class(v) for k, v in value.items()}

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

    def _class(self, path: str) -> Any:
        value = self._import(path)
        if not inspect.isclass(value):
            self._config_error(f"{value}_is_not_a_class")
        return value

    def _import(self, path: str) -> Any:
        from django.utils.module_loading import import_string
        try:
            return import_string(path)
        except ImportError as e:
            self._config_error(f"import_error_{path}")


app_settings = AppSettings()
