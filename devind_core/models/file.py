"""Модуль, описывающие модель файла."""

import os

from django.conf import settings
from django.db import models


def user_directory_path(instance, filename: str):
    """Формируем автоматический путь директории пользователя."""
    return f'storage/user_files/{instance.user.id}/{filename}'


class AbstractFile(models.Model):
    """Абстрактный класс для описания моделей пользователя."""

    name = models.CharField(max_length=255, help_text='Название файла')
    src = models.FileField(upload_to=user_directory_path, help_text='Путь к файлу')
    deleted = models.BooleanField(default=False, help_text='Помечаем удаленный файл')

    created_at = models.DateTimeField(auto_now_add=True, help_text='Дата добавления файла')
    updated_at = models.DateTimeField(auto_now=True, help_text='Дата обновления файла')

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.SET_NULL,
        help_text='Пользователь, добавивший файл'
    )

    class Meta:
        """Мета класс модели для файлов."""

        abstract = True
        ordering = ('-created_at',)

    @property
    def ext(self) -> str:
        """Расширение файла."""
        return os.path.splitext(self.src.path)[1]

    @property
    def size(self) -> float:
        """Размер файла в байтах, кБайт = 1 байт * 1024."""
        return os.path.getsize(self.src.path) if os.path.isfile(self.src.path) else -1.
