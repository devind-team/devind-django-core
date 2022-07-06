"""Проверка пользовательских разрешений профиля пользователя."""

from strawberry_django_plus.permissions import HasPerm


AddProfile = HasPerm('devind_core.add_profile')
ChangeProfile = HasPerm('devind_core.change_profile')
DeleteProfile = HasPerm('devind_core.delete_profile')


# class ChangeProfileValue(BasePermission):
#     """Пропускает пользователей, которые могут изменять значение настроек профиля пользователя."""
#
#     @staticmethod
#     def has_object_permission(context, user):
#         """Непосредственная проверка пользовательского разрешения."""
#         return context.user.has_perm('devind_core.change_profilevalue') or context.user == user
