"""Модуль, описывающий схему хранения настроек"""

from django.conf import settings
from django.db import models

from ..settings import devind_settings


class AbstractSetting(models.Model):
    """Абстрактный класс хранения доступных пользовательских настроек."""

    TEXT = 0
    FILE = 1
    JSON = 2
    BOOL = 4

    KIND_VALUE = (
        (TEXT, 'text'),
        (FILE, 'file'),
        (JSON, 'json'),
        (BOOL, 'bool')
    )

    kind_value = models.PositiveIntegerField(choices=KIND_VALUE, default=TEXT, help_text='Тип значения настройки')
    readonly = models.BooleanField(default=True, help_text='Может ли поле быть изменено')
    key = models.CharField(max_length=255, help_text='Ключ настройки')
    value = models.TextField(blank=True, help_text='Значение настройки по умолчанию')

    users = models.ManyToManyField(settings.AUTH_USER_MODEL, through='SettingValue', help_text='Пользователи')

    class Meta:
        """Мета класс хранения доступных пользовательских настроек."""

        abstract = True


class AbstractSettingValue(models.Model):
    """Абстрактный класс хранения настроек пользователей."""

    value = models.TextField(blank=True, help_text='Значение настройки')

    created_at = models.DateTimeField(auto_now_add=True, help_text='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, help_text='Дата обновления')

    setting = models.ForeignKey(
        devind_settings.SETTING_MODEL,
        on_delete=models.CASCADE,
        null=False,
        help_text='Настройка'
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=False, on_delete=models.CASCADE, help_text='Пользователь')

    class Meta:
        """Мета класс хранения пользовательских настроек."""

        abstract = True
        unique_together = (('setting', 'user'),)
