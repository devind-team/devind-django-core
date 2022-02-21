"""Проверка пользовательских разрешений групп пользователей."""

from devind_helpers.permissions import ModelPermission


AddGroup = ModelPermission('auth.add_group')
ChangeGroup = ModelPermission('auth.change_group')
DeleteGroup = ModelPermission('auth.delete_group')
