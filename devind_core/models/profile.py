"""Модуль, содержащий варьируемые расширяемые данные о пользователе."""

from django.conf import settings
from django.db import models

from ..settings import devind_settings


class AbstractProfile(models.Model):
    """Модель доступных настроек пользователей."""

    TEXT = 0
    DATE = 1
    BOOL = 2
    FILE = 3
    CHOICE = 4

    KIND = (
        (TEXT, 'text'),
        (DATE, 'date'),
        (BOOL, 'bool'),
        (FILE, 'file'),
        (CHOICE, 'choice')
    )

    name = models.CharField(max_length=512, help_text='Название настройки')
    code = models.CharField(max_length=30, help_text='Уникальный код настройки', unique=True)
    kind = models.PositiveIntegerField(choices=KIND, default=TEXT, help_text='Тип настройки')
    position = models.PositiveIntegerField(default=0, help_text='Позиция')

    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, help_text='Родительское правило')
    users = models.ManyToManyField(settings.AUTH_USER_MODEL, through='ProfileValue', help_text='Пользователи')

    class Meta:
        """Мета класс доступных настроек пользователей."""

        abstract = True
        ordering = ('position',)


class AbstractProfileValue(models.Model):
    """Значение настройки профиля пользователя."""

    value = models.TextField(help_text='Значение хранимой информации')
    visibility = models.BooleanField(default=True, help_text='Доступность настройки')

    created_at = models.DateTimeField(auto_now_add=True, help_text='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, help_text='Дата обновления')

    profile = models.ForeignKey(
        devind_settings.PROFILE_MODEL,
        on_delete=models.CASCADE,
        null=False,
        help_text='Профиль'
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=False, help_text='Пользователь')

    class Meta:
        """Мета класс хранения значений параметров пользователя."""

        abstract = True
        unique_together = (('profile', 'user'),)
