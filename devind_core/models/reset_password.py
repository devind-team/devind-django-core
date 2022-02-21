"""Модуль, содержащий таблицу для восстановления пароля."""

from django.conf import settings
from django.db import models


class AbstractResetPassword(models.Model):
    """Абстрактный класс восстановления пароля пользователя."""

    token = models.CharField(max_length=255, unique=True, null=False, help_text='Токен восстановления пароля')
    password = models.CharField(max_length=255, null=True, help_text='Новый пароль пользователя')

    created_at = models.DateTimeField(auto_now_add=True, help_text='Время запроса восстановления пароля')
    updated_at = models.DateTimeField(auto_now=True, help_text='Время изменения пароля')

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=False,
        help_text='Пользователь, который запросил восстановление пароля'
    )

    class Meta:
        """Мета класс модели восстановления пароля."""

        abstract = True
