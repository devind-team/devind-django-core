from strawberry_django_plus import gql
from strawberry.types import Info
from strawberry_django_plus.permissions import IsAuthenticated
from typing import Iterable

from django.contrib.auth import get_user_model
from django.db import models
from devind_core.models import get_setting_model, get_setting_value_model, get_file_model
from devind_core.permissions import self_or_can_change
from devind_core.schema.types import SettingType, FileType, UserType, SettingValueType
from devind_helpers.utils import convert_str_to_bool

User: models.Model = get_user_model()
Setting: models.Model = get_setting_model()
SettingValue: models.Model = get_setting_value_model()
File: models.Model = get_file_model()


@gql.type
class TokenType:
    access_token: str
    expires_in: str
    token_type: str
    scope: str
    refresh_token: str
    user: UserType


@gql.type
class UserQueries:

    users: gql.relay.Connection[UserType] = gql.django.connection(directives=[IsAuthenticated()])
    settings: list[SettingType] = gql.django.field(description='Настройки приложения')

    @gql.django.field
    def me(self, info: Info) -> UserType | None:
        """Информация обо мне"""
        return hasattr(info.context.request, 'user') and info.context.request.user or None

    @gql.django.field(directives=[IsAuthenticated()])
    def user(self, user_id: gql.relay.GlobalID) -> UserType | None:
        return UserType.resolve_node(user_id)

    @gql.django.field
    def user_information(self, user_id: gql.relay.GlobalID) -> UserType | None:
        """Доступная информация о пользователе"""
        user: User = UserType.resolve_node(user_id, required=True)
        return user if convert_str_to_bool(user.get_settings('USER_PUBLIC')) else None

    @gql.django.field
    def has_settings(self) -> bool:
        """Установлены ли настройки приложения"""
        return Setting.objects.exists()

    @gql.django.field
    def settings_values(self, user_id: gql.relay.GlobalID) -> list[SettingValueType]:
        user: User = UserType.resolve_node(user_id, required=True)
        return SettingValue.objects.filter(user=user)

    @gql.django.connection(directives=[IsAuthenticated()])
    def files(self, info: Info, user_id: gql.relay.GlobalID | None = None) -> Iterable[FileType]:
        """Разрешение выгрузки файлов """

        if user_id is not None:
            user: User = UserType.resolve_node(user_id, required=True)
        else:
            user: User = info.context.request.user
        self_or_can_change(info, user)
        return File.objects.filter(user=user)
