from django.core.exceptions import PermissionDenied
from strawberry.types import Info
from devind_core.models import AbstractUser


def self_or_can_change(info: Info, user: AbstractUser):
    """Пропускает пользователей, которые могут изменять пользователя."""
    if user.can_change(info.context.request.user):
        return
    raise PermissionDenied('Ошибка доступа')


def self_or_has_perm(info: Info, user: AbstractUser, perm: str):
    """"""
    if user == info.context.request.user or info.context.request.user.has_perm(perm):
        return
    raise PermissionDenied('Ошибка доступа')
