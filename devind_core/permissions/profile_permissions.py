"""Проверка пользовательских разрешений профиля пользователя."""

from devind_helpers.permissions import BasePermission, ModelPermission


AddProfile = ModelPermission('devind_core.add_profile')
ChangeProfile = ModelPermission('devind_core.change_profile')
DeleteProfile = ModelPermission('devind_core.delete_profile')


class ChangeProfileValue(BasePermission):
    """Пропускает пользователей, которые могут изменять значение настроек профиля пользователя."""

    @staticmethod
    def has_object_permission(context, user):
        """Непосредственная проверка пользовательского разрешения."""
        return context.user.has_perm('devind_core.change_profilevalue') or context.user == user
