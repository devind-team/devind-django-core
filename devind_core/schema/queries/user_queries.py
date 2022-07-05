# from typing import List
#
# import graphene
from strawberry_django_plus import gql
from strawberry.types import Info
from strawberry_django_plus.permissions import IsAuthenticated

from django.contrib.auth import get_user_model
from django.db import models
# from graphene_django import DjangoListField
# from graphene_django.filter import DjangoFilterConnectionField
# from graphql import ResolveInfo
from graphql_relay import from_global_id
#
from devind_core.models import get_setting_model, get_setting_value_model, get_file_model
from devind_core.permissions import self_or_can_change
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


@gql.type
class UserQueries:

    users: gql.relay.Connection[UserType] = gql.django.connection(directives=[IsAuthenticated()])
    user: UserType | None = gql.django.node(directives=[IsAuthenticated()]) # todo: ломать api еще больше ради простоты?
    settings: list[SettingType] = gql.django.field(description='Настройки приложения')

    @gql.django.field
    def me(self, info: Info) -> UserType | None:
        """Информация обо мне"""
        return hasattr(info.context.request, 'user') and info.context.request.user or None

    #@gql.django.field(directives=[IsAuthenticated()])
    #def user(self, user_id: gql.relay.GlobalID) -> UserType | None:
    #    return UserType.resolve_node(user_id)

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

    @gql.django.field(directives=[IsAuthenticated()])
    def files(self, info: Info, user_id: gql.relay.GlobalID | None = None) -> list[FileType]:
        """Разрешение выгрузки файлов """

        if user_id is not None:
            user: User = UserType.resolve_node(user_id, required=True)
        else:
            user: User = info.context.request.user
        self_or_can_change(info, user)
        return File.objects.filter(user=user)
