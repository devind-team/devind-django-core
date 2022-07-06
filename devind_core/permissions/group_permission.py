"""Проверка пользовательских разрешений групп пользователей."""

from strawberry_django_plus.permissions import HasPerm


AddGroup = HasPerm('auth.add_group')
ChangeGroup = HasPerm('auth.change_group')
DeleteGroup = HasPerm('auth.delete_group')
