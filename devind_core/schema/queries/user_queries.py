from typing import List

import graphene
from django.contrib.auth import get_user_model
from django.db import models
from graphene_django import DjangoListField
from graphene_django.filter import DjangoFilterConnectionField
from graphql import ResolveInfo
from graphql_relay import from_global_id

from devind_core.models import get_setting_model, get_setting_value_model, get_file_model
from devind_core.permissions import ChangeUser
from devind_core.schema.types import SettingType, FileType
from devind_core.settings import devind_settings
from devind_helpers.decorators import permission_classes
from devind_helpers.orm_utils import get_object_or_none, get_object_or_404
from devind_helpers.permissions import IsAuthenticated
from devind_helpers.utils import convert_str_to_bool

User: models.Model = get_user_model()
Setting: models.Model = get_setting_model()
SettingValue: models.Model = get_setting_value_model()
File: models.Model = get_file_model()


class UserQueries(graphene.ObjectType):
    me = graphene.Field(devind_settings.USER_TYPE, description='Информация обо мне')
    user = graphene.Field(devind_settings.USER_TYPE, user_id=graphene.ID(required=True), description='Информация о указанном пользователе')
    users = DjangoFilterConnectionField(devind_settings.USER_TYPE, required=True, description='Пользователи приложения')
    user_information = graphene.Field(
        devind_settings.USER_TYPE,
        user_id=graphene.ID(required=True, description='Идентификатор пользователя'),
        description='Доступная информация о пользователе'
    )
    has_settings = graphene.Boolean(required=True, description='Установлены ли настройки приложения')
    settings = DjangoListField(graphene.NonNull(SettingType), required=True, description='Настройки приложения')
    files = DjangoFilterConnectionField(FileType, user_id=graphene.ID(), required=True)

    @staticmethod
    def resolve_me(root, info: ResolveInfo) -> User or None:
        return hasattr(info.context, 'user') and info.context.user or None

    @staticmethod
    @permission_classes([IsAuthenticated])
    def resolve_user(root, info: ResolveInfo, user_id: str, *args, **kwargs):
        return get_object_or_none(User, pk=from_global_id(user_id)[1])

    @staticmethod
    def resolve_user_information(root, info: ResolveInfo, user_id: str, *args, **kwargs):
        user: User = get_object_or_404(User, pk=from_global_id(user_id)[1])
        return user if convert_str_to_bool(user.get_settings('USER_PUBLIC')) else None

    @staticmethod
    def resolve_has_settings(root, info: ResolveInfo) -> bool:
        return Setting.objects.exists()

    @staticmethod
    def resolve_settings_values(root, info: ResolveInfo, user_id: str, *args, **kwargs):
        user: User = get_object_or_404(User, pk=from_global_id(user_id)[1])
        return SettingValue.objects.filter(user=user)

    @staticmethod
    @permission_classes([IsAuthenticated, ChangeUser])
    def resolve_files(root, info: ResolveInfo, user_id=None, **kwargs) -> List[File]:
        """Разрешение выгрузки файлов"""

        if user_id is not None:
            user: User = get_object_or_404(User, pk=from_global_id(user_id)[1])
        else:
            user: User = info.context.user
        info.context.check_object_permissions(info.context, user)
        return File.objects.filter(user=user)
