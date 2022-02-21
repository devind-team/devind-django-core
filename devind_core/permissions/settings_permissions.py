"""Проверка пользовательских разрешений настроек пользователей."""

from devind_helpers.permissions import BasePermission


class ChangeSetting(BasePermission):
    """Пропускает пользователей, которые могут изменять настройки приложения."""

    @staticmethod
    def has_object_permission(context, setting):
        """Непосредственная проверка."""
        return context.user.has_perm('devind_core.change_setting') or not setting.readonly


class DeleteSettings(BasePermission):
    """Пропускает пользователей, которые могут удалять настройки приложения."""

    @staticmethod
    def has_object_permission(context, user):
        """Непосредственная проверка."""
        return context.user.has_perm('devind_core.delete_setting') or context.user == user
