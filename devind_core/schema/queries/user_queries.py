# from typing import List
#
# import graphene
from strawberry_django_plus import gql
from strawberry.types import Info
from strawberry_django_plus.permissions import (
    HasObjPerm,
    HasPerm,
    IsAuthenticated,
    IsStaff,
    IsSuperuser,
)

from django.contrib.auth import get_user_model
from django.db import models
# from graphene_django import DjangoListField
# from graphene_django.filter import DjangoFilterConnectionField
# from graphql import ResolveInfo
from graphql_relay import from_global_id
#
from devind_core.models import get_setting_model, get_setting_value_model, get_file_model
from devind_core.permissions import can_change_user
from devind_core.schema.types import SettingType, FileType, UserType, SettingValueType
# from devind_core.settings import devind_settings
# from devind_helpers.decorators import permission_classes
from devind_helpers.orm_utils import get_object_or_none, get_object_or_404
# from devind_helpers.permissions import IsAuthenticated
from devind_helpers.utils import convert_str_to_bool
#
User: models.Model = get_user_model()
Setting: models.Model = get_setting_model()
SettingValue: models.Model = get_setting_value_model()
File: models.Model = get_file_model()

from devind_helpers.request import Request
from oauth2_provider.views.base import TokenView
from django.core.exceptions import ValidationError
import json
from oauth2_provider.models import AccessToken
from devind_core.models import Session


@gql.type
class TokenType:
    access_token: str
    expires_in: str
    token_type: str
    scope: str
    refresh_token: str
    user: UserType

@gql.type
class UserMutations:
    @gql.django.input_mutation
    def get_token(self, info: Info, client_id: str, client_secret: str, grant_type: str, username: str, password: str) -> TokenType:
        request = Request(
            '/graphql',
            body=json.dumps({
                'client_id': client_id,
                'client_secret': client_secret,
                'grant_type': grant_type,
                'username': username,
                'password': password}).encode('utf-8'),
            headers=info.context.request.headers,
            meta=info.context.request.META
        )
        url, header, body, status = TokenView().create_token_response(request)
        if status != 200:
            raise ValidationError({'username': 'Неверный логин или пароль'})
        body_dict = json.loads(body)
        ip: str = info.context.request.META['REMOTE_ADDR']
        user_agent: str = info.context.request.META['HTTP_USER_AGENT']
        access_token: AccessToken = AccessToken.objects.get(token=body_dict['access_token'])
        Session.objects.create(
            ip=ip,
            user_agent=user_agent,
            access_token=access_token,
            user=access_token.user
        )

        tt = TokenType(**body_dict, user=access_token.user)
        return tt


#todo isAuth
@gql.type
class UserQueries:

    users: gql.relay.Connection[UserType] = gql.django.connection(directives=[IsAuthenticated()])
    user: UserType | None = gql.django.node(directives=[IsAuthenticated()]) # todo: ломать api еще больше ради простоты?

    @gql.django.field
    def me(self, info: Info) -> UserType | None:
        return hasattr(info.context.request, 'user') and info.context.request.user or None

    #@gql.django.field(directives=[IsAuthenticated()])
    #def user(self, user_id: gql.relay.GlobalID) -> UserType | None:
    #    return UserType.resolve_node(user_id)

    @gql.django.field
    def user_information(self, user_id: gql.relay.GlobalID) -> UserType | None:
        user: User = UserType.resolve_node(user_id, required=True)
        return user if convert_str_to_bool(user.get_settings('USER_PUBLIC')) else None

    @gql.django.field
    def has_settings(self) -> bool:
        return Setting.objects.exists()

    @gql.django.field
    def settings_values(self, user_id: gql.relay.GlobalID) -> list[SettingValueType]:
        user: User = UserType.resolve_node(user_id, required=True)
        return SettingValue.objects.filter(user=user)

    @gql.django.field(directives=[HasPerm(perms=['.add_user'], obj_perm_checker=can_change_user, any=False)])
    def files(self, info: Info, user_id: gql.relay.GlobalID | None = None) -> list[FileType]:
        """Разрешение выгрузки файлов """

        if user_id is not None:
            user: User = UserType.resolve_node(user_id, required=True)
        else:
            user: User = info.context.request.user
        #info.context.request.check_object_permissions(info.context.request, user)
        return File.objects.filter(user=user)


# class UserQueries(graphene.ObjectType):
#     me = graphene.Field(devind_settings.USER_TYPE, description='Информация обо мне')
#     user = graphene.Field(devind_settings.USER_TYPE, user_id=graphene.ID(required=True), description='Информация о указанном пользователе')
#     users = DjangoFilterConnectionField(devind_settings.USER_TYPE, required=True, description='Пользователи приложения')
#     user_information = graphene.Field(
#         devind_settings.USER_TYPE,
#         user_id=graphene.ID(required=True, description='Идентификатор пользователя'),
#         description='Доступная информация о пользователе'
#     )
#     has_settings = graphene.Boolean(required=True, description='Установлены ли настройки приложения')
#     settings = DjangoListField(graphene.NonNull(SettingType), required=True, description='Настройки приложения')
#     files = DjangoFilterConnectionField(FileType, user_id=graphene.ID(), required=True)
#
#     @staticmethod
#     def resolve_me(root, info: ResolveInfo) -> User or None:
#         return hasattr(info.context, 'user') and info.context.user or None
#
#     @staticmethod
#     @permission_classes([IsAuthenticated])
#     def resolve_user(root, info: ResolveInfo, user_id: str, *args, **kwargs):
#         return get_object_or_none(User, pk=from_global_id(user_id)[1])
#
#     @staticmethod
#     def resolve_user_information(root, info: ResolveInfo, user_id: str, *args, **kwargs):
#         user: User = get_object_or_404(User, pk=from_global_id(user_id)[1])
#         return user if convert_str_to_bool(user.get_settings('USER_PUBLIC')) else None
#
#     @staticmethod
#     def resolve_has_settings(root, info: ResolveInfo) -> bool:
#         return Setting.objects.exists()
#
#     @staticmethod
#     def resolve_settings_values(root, info: ResolveInfo, user_id: str, *args, **kwargs):
#         user: User = get_object_or_404(User, pk=from_global_id(user_id)[1])
#         return SettingValue.objects.filter(user=user)
#
#     @staticmethod
#     @permission_classes([IsAuthenticated, ChangeUser])
#     def resolve_files(root, info: ResolveInfo, user_id=None, **kwargs) -> List[File]:
#         """Разрешение выгрузки файлов"""
#
#         if user_id is not None:
#             user: User = get_object_or_404(User, pk=from_global_id(user_id)[1])
#         else:
#             user: User = info.context.user
#         info.context.check_object_permissions(info.context, user)
#         return File.objects.filter(user=user)
