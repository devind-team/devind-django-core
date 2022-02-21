"""Модуль получения моделей, содержащихся в ядре приложения."""

from typing import Type

from django.apps import apps

from .file import AbstractFile
from .log_entry import AbstractLogEntry
from .log_request import AbstractLogRequest
from .profile import AbstractProfile, AbstractProfileValue
from .reset_password import AbstractResetPassword
from .session import AbstractSession
from .settings import AbstractSetting, AbstractSettingValue
from .user import AbstractUser
from ..settings import devind_settings


class File(AbstractFile):
    """Модель хранения файлов."""

    class Meta(AbstractFile.Meta):
        """Мета класс хранения файлов."""

        pass


def get_file_model() -> Type[AbstractFile]:
    """Модель хранения файлов."""
    return apps.get_model(devind_settings.FILE_MODEL)


class LogEntry(AbstractLogEntry):
    """Модель хранения изменений моделей."""
    class Meta(AbstractLogEntry.Meta):
        """Мета класс хранения изменений моделей."""

        pass


def get_log_entry_model() -> Type[AbstractLogEntry]:
    """Модель изменений данных."""
    return apps.get_model(devind_settings.LOG_ENTRY_MODEL)


class LogRequest(AbstractLogRequest):
    """Модель хранения пользовательских запросов."""

    class Meta(AbstractLogRequest.Meta):
        """Мета класс хранения пользовательских запросов."""

        pass


def get_log_request_model() -> Type[AbstractLogRequest]:
    """Модель хранения пользовательских запросов."""
    return apps.get_model(devind_settings.LOG_REQUEST_MODEL)


class ResetPassword(AbstractResetPassword):
    """Модель для восстановления пароля."""

    class Meta(AbstractResetPassword.Meta):
        """Мета класс хранения данных восстановления пароля."""

        pass


def get_reset_password_model() -> Type[AbstractResetPassword]:
    """Модель восстановления паролей."""
    return apps.get_model(devind_settings.RESET_PASSWORD_MODEL)


class Session(AbstractSession):
    """Модель хранения сессий пользователей."""

    class Meta(AbstractSession.Meta):
        """Мета класс хранения пользовательских сессий."""

        pass


def get_session_model() -> Type[AbstractSession]:
    """Модель хранения сессий пользователя."""
    return apps.get_model(devind_settings.SESSION_MODEL)


class Setting(AbstractSetting):
    """Модель хранений списка настроек."""

    class Meta(AbstractSetting.Meta):
        """Мета класс хранения списка пользовательских настроек."""

        pass


def get_setting_model() -> Type[AbstractSetting]:
    """Модель хранения доступных настроек пользователей."""
    return apps.get_model(devind_settings.SETTING_MODEL)


class SettingValue(AbstractSettingValue):
    """Модель хранения пользовательских настроек."""

    class Meta(AbstractSettingValue.Meta):
        """Мета класс хранения пользовательских настроек"""

        pass


def get_setting_value_model() -> Type[AbstractSettingValue]:
    """Модель получения значений настроек пользователей."""
    return apps.get_model(devind_settings.SETTING_VALUE_MODEL)


class Profile(AbstractProfile):
    """Модель хранения пользовательских данных."""

    class Meta(AbstractProfile.Meta):
        """Мета класс хранения пользовательских данных."""

        pass


def get_profile_model() -> Type[AbstractProfile]:
    """Модель хранения списка пользовательских данных."""
    return apps.get_model(devind_settings.PROFILE_MODEL)


class ProfileValue(AbstractProfileValue):
    """Модель хранения списка пользовательских настроек."""

    class Meta(AbstractProfileValue.Meta):
        """Мета класс хранения пользовательских настроек."""

        pass


def get_profile_value_model() -> Type[AbstractSettingValue]:
    """Модель получения пользовательских"""
    return apps.get_model(devind_settings.PROFILE_VALUE_MODEL)
