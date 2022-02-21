"""
Этот модуль представляет собой набор настроек для реализации ядра приложений.
Настройки devind_core находятся в простанстве имен DEVIND_CORE.
Для примера, Ваши настройки выглядят вот так:
DEVIND_CORE = {
    ...
}
"""

from typing import Optional, Dict

from django.conf import settings


USER_SETTINGS: Optional[Dict] = getattr(settings, 'DEVIND_CORE', None)

FILE_MODEL = getattr(settings, 'DEVIND_CORE_FILE_MODEL', 'devind_core.File')
LOG_ENTRY_MODEL = getattr(settings, 'DEVIND_CORE_LOG_ENTRY_MODEL', 'devind_core.LogEntry')
LOG_REQUEST_MODEL = getattr(settings, 'DEVIND_CORE_LOG_REQUEST_MODEL', 'devind_core.LogRequest')
RESET_PASSWORD_MODEL = getattr(settings, 'DEVIND_CORE_RESET_PASSWORD_MODEL', 'devind_core.ResetPassword')
SESSION_MODEL = getattr(settings, 'DEVIND_CORE_SESSION_MODEL', 'devind_core.Session')
SETTING_MODEL = getattr(settings, 'DEVIND_CORE_SETTING_MODEL', 'devind_core.Setting')
SETTING_VALUE_MODEL = getattr(settings, 'DEVIND_CORE_SETTING_VALUE_MODEL', 'devind_core.SettingValue')
PROFILE_MODEL = getattr(settings, 'DEVIND_CORE_PROFILE_MODEL', 'devind_core.Profile')
PROFILE_VALUE_MODEL = getattr(settings, 'DEVIND_CORE_PROFILE_VALUE_MODEL', 'devind_core.ProfileValue')

USER_TYPE = getattr(settings, 'DEVIND_CORE_USER_TYPE', 'devind_core.schema.UserType')


DEFAULTS = {
    'FILE_MODEL': FILE_MODEL,
    'LOG_ENTRY_MODEL': LOG_ENTRY_MODEL,
    'LOG_REQUEST_MODEL': LOG_REQUEST_MODEL,
    'RESET_PASSWORD_MODEL': RESET_PASSWORD_MODEL,
    'SESSION_MODEL': SESSION_MODEL,
    'SETTING_MODEL': SETTING_MODEL,
    'SETTING_VALUE_MODEL': SETTING_VALUE_MODEL,
    'PROFILE_MODEL': PROFILE_MODEL,
    'PROFILE_VALUE_MODEL': PROFILE_VALUE_MODEL,
    'USER_TYPE': USER_TYPE
}


class DevindCoreSettings:
    """Настройки приложения devind_core."""

    def __init__(self, user_settings: Optional[Dict] = None, defaults: Optional[Dict] = None):
        """Инициализация настроек."""
        self._user_settings: Dict[str, str] = user_settings or {}
        self.defaults: Dict[str, str] = defaults or DEFAULTS

    @property
    def user_settings(self) -> Dict[str, str]:
        """Пользовательские настройки."""
        if not hasattr(self, '_user_settings'):
            self._user_settings = getattr(settings, 'DEVIND_CORE', {})
        return self._user_settings

    def __getattr__(self, item: str) -> str:
        """Получение атрибута из настроек."""
        if item not in self.defaults:
            raise AttributeError(f'Invalid devind_core settings: {item}')
        value: str = self.user_settings[item] if item in self.user_settings else self.defaults[item]
        return value


devind_settings = DevindCoreSettings(USER_SETTINGS, DEFAULTS)
