"""Проверка пользовательских разрешений файлов."""

from devind_helpers.permissions import ModelPermission, BasePermission


class ChangeFile(BasePermission):
    """Пропускает пользователей, которые могут изменять файл."""

    @staticmethod
    def has_object_permission(context, obj):
        """Проверка прав."""
        return context.user.has_perm('devind_core.change_file') or context.user == obj


DeleteFile = ModelPermission('devind_core.delete_file')
