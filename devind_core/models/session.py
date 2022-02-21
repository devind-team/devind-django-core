"""Модуль, содержащий информацию о сессиях пользователя."""

from typing import Optional

from django.conf import settings
from django.db import models
from oauth2_provider.models import AccessToken
from user_agents import parse
from user_agents.parsers import UserAgent


class AbstractSession(models.Model):
    """Абстрактная модель хранения информации о сессии пользователя."""

    ip = models.GenericIPAddressField(help_text='ip-адрес сессии')
    user_agent = models.TextField(help_text='HTTP_USER_AGENT сессии')

    access_token = models.OneToOneField(
        AccessToken,
        null=True,
        on_delete=models.SET_NULL,
        help_text='Токен сессии'
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=False,
        help_text='Пользователь'
    )

    created_at = models.DateTimeField(auto_now=True, help_text='Дата создания сессии')

    _parse_cache: Optional[UserAgent] = None

    class Meta:
        """Мета класс хранения сессии пользователя."""

        abstract = True
        ordering = ('-created_at',)

    @property
    def browser(self) -> str:
        """Определение браузера."""
        family, _, version_string = self._parse().browser
        return f'{family} {version_string}'

    @property
    def os(self) -> str:
        """Определение операционной системы."""
        return self._parse().os.family

    @property
    def device(self):
        """Определение используемого девайса."""
        family = self._parse().device.family
        if family == 'Other':
            return 'PC'
        return family

    def _parse(self) -> UserAgent:
        """Функция парсинга информации из запроса."""
        if self._parse_cache is None:
            self._parse_cache = parse(self.user_agent)
        return self._parse_cache
