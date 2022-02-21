"""Модуль настроек приложения DevindCore."""

from typing import Iterable

import django.contrib.auth.management as management
from django.apps import AppConfig
from django.contrib.auth import get_permission_codename
from django.db.models.options import Options
from django.db.models.signals import post_migrate


class DevindCoreConfig(AppConfig):
    """Конфигурация приложения."""

    name = 'devind_core'

    @staticmethod
    def add_default_permissions(permissions: Iterable[str]) -> None:
        """Добавление разрешений к каждой модели.

        Стандартные разрешения - ('add', 'change', 'delete', 'view') (См. django.db.models.options)
        Для добавления новых разрешений применяется подход из django.contrib.auth.apps с подменой
        функции _get_builtin_permissions модуля django.contrib.auth.management
        :param permissions: классы разрешений
        """

        def _get_builtin_permissions(opts: Options):
            """Переопределение метода модуля django.contrib.auth.management"""

            if opts.default_permissions == ('add', 'change', 'delete', 'view'):
                # Модель в классе Meta не переопределяет базовое значение default_permissions,
                # поэтому добавляем новые разрешения
                default_permissions = tuple(list(opts.default_permissions) + list(permissions))
            else:
                # Модель в классе Meta переопределяет базовое значение default_permissions,
                # поэтому оставляем разрешения, как есть
                default_permissions = opts.default_permissions
            perms = []
            for action in default_permissions:
                perms.append((
                    get_permission_codename(action, opts),
                    'Can %s %s' % (' '.join(action.split('_')), opts.verbose_name_raw)
                ))
            return perms
        management._get_builtin_permissions = _get_builtin_permissions
        post_migrate.connect(
            management.create_permissions,
            dispatch_uid='apps.core.create_permissions'
        )

    def ready(self):
        pass
