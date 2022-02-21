"""Модуль описания пользовательской модели."""

from typing import Optional

from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from oauth2_provider.models import RefreshToken

from devind_helpers.orm_utils import get_object_or_none
from devind_helpers.utils import random_string
from ..managers import UserManager


class AbstractUser(AbstractBaseUser, PermissionsMixin):
    """Абстрактная модель хранения пользовательских данных."""

    username = models.CharField(max_length=30, unique=True, help_text='login')
    email = models.EmailField(null=False, unique=True, help_text='email')
    first_name = models.CharField(max_length=30, help_text='Имя')
    last_name = models.CharField(max_length=30, help_text='Фамилия')
    sir_name = models.CharField(max_length=30, null=True, help_text='Отчество')
    is_active = models.BooleanField(default=True, help_text='Является ли пользователь активным')
    avatar = models.FileField(upload_to='storage/avatars/', default=None, null=True, help_text='Аватар')
    birthday = models.DateField(null=True, help_text='День рождения')
    agreement = models.DateTimeField(null=True, help_text='Пользовательское соглашение')
    created_at = models.DateTimeField(auto_now_add=True, help_text='Дата добавления')

    class Meta:
        """Мета класс хранения пользовательских данных."""

        abstract = True
        ordering = ('-created_at',)
        db_table = 'users'
        permissions = [
            ('view_experimental', 'Can view experimental features')
        ]

    objects = UserManager()

    USERNAME_FIELD = 'username'  # Имя, которое используем в качестве идентификатора
    REQUIRED_FIELDS = []  # Список полей при создании createsuperuser

    @property
    def get_full_name(self):
        """Полное имя пользователя."""

        return "%s %s" % (self.last_name, self.first_name)

    def get_token(self) -> str:
        """Получение токена для восстановления пароля."""
        token = random_string(40)
        self.resetpassword_set.filter(password=None).delete()   # Удаляем активные сессии
        self.resetpassword_set.create(token=token)  # Создаем новый токен
        return token

    def logout(self, session: Optional = None):
        """Выход пользователя."""

        if session is None:
            for refresh_token in RefreshToken.objects.filter(user=self).all():
                refresh_token.revoke()
                refresh_token.delete()
        else:
            refresh_token = RefreshToken.objects.get(access_token__session=session)
            refresh_token.revoke()
            refresh_token.delete()

    def get_settings(self, key: str) -> Optional[str]:
        """Получение настроек пользователя."""
        from . import get_setting_model, get_setting_value_model
        Setting = get_setting_model()
        SettingValue = get_setting_value_model()
        setting: Setting = Setting.objects.get(key=key)
        user_value: Optional[SettingValue] = get_object_or_none(SettingValue, user=self, setting=setting)
        return user_value.value if user_value else setting.value    # noqa
