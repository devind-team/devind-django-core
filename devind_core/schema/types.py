from datetime import datetime
from typing import Any, Union, Type

import graphene
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models import QuerySet, Count, Model
from graphene.relay import Node
from graphene_django.types import DjangoObjectType
from graphene_django_optimizer import resolver_hints
from graphql import ResolveInfo
from graphql_relay import from_global_id
from oauth2_provider.models import AccessToken, Application

from devind_core.models import get_file_model, \
    get_session_model, \
    get_profile_model, \
    get_profile_value_model, \
    get_setting_model, \
    get_setting_value_model, \
    get_log_entry_model, \
    get_log_request_model
from devind_core.models import AbstractFile, \
    AbstractSetting, \
    AbstractSettingValue, \
    AbstractProfile, \
    AbstractProfileValue, \
    AbstractSession, \
    AbstractLogRequest, \
    AbstractLogEntry
from devind_core.schema.connections.countable_connection import CountableConnection
from devind_core.settings import devind_settings
from devind_helpers.optimized import OptimizedDjangoObjectType
from devind_helpers.orm_utils import get_object_or_none

File: Type[AbstractFile] = get_file_model()
Setting: Type[AbstractSetting] = get_setting_model()
SettingValue: Type[AbstractSettingValue] = get_setting_value_model()
Profile: Type[AbstractProfile] = get_profile_model()
ProfileValue: Type[AbstractProfileValue] = get_profile_value_model()
Session: Type[AbstractSession] = get_session_model()
LogRequest: Type[AbstractLogRequest] = get_log_request_model()
LogEntry: Type[AbstractLogEntry] = get_log_entry_model()
User = get_user_model()


class ContentTypeType(OptimizedDjangoObjectType):
    """Тип модели Django."""

    class Meta:
        model = ContentType


class GroupType(OptimizedDjangoObjectType):
    """Группа пользователей."""

    class Meta:
        model = Group
        fields = '__all__'


class PermissionType(OptimizedDjangoObjectType):
    """Привилегия пользователя или группы пользователей."""

    groups = graphene.Field(GroupType, description='Группы')
    content_type = graphene.Field(ContentTypeType, required=True, description='Тип модели Django')

    class Meta:
        model = Permission
        fields = ('id', 'name', 'content_type', 'codename',)


class SessionType(OptimizedDjangoObjectType):
    """Сессия пользователя."""

    browser = graphene.String(required=True, description='Браузер пользователя')
    os = graphene.String(required=True, description='Операционная система пользователя')
    device = graphene.String(required=True, description='Устройство пользователя')
    date = graphene.DateTime(description='Дата сессии пользователя')
    activity = graphene.Int(required=True, description='Количество действий в сессии пользователя')
    history = graphene.Int(required=True, description='Количество запросов в сессии пользователя')
    user = graphene.Field(devind_settings.USER_TYPE, required=True, description='Пользователь')

    class Meta:
        model = Session
        interfaces = (Node,)
        fields = (
            'id',
            'ip',
            'browser',
            'os',
            'device',
            'activity',
            'history',
        )

    @classmethod
    def get_queryset(cls, queryset, info):
        queryset = queryset.annotate(Count('logentry'), Count('logrequest'))
        return super(OptimizedDjangoObjectType, cls).get_queryset(queryset, info)

    @staticmethod
    @resolver_hints(select_related=('access_token',), only=('access_token__updated',))
    def resolve_date(session: Session, info: ResolveInfo) -> datetime or None:
        return session.created_at

    @staticmethod
    @resolver_hints(model_field='logentry__count')
    def resolve_activity(session: Union[Session, Any], info: ResolveInfo) -> int:
        return session.logentry__count

    @staticmethod
    @resolver_hints(model_field='logrequest__count')
    def resolve_history(session: Union[Session, Any], info: ResolveInfo) -> int:
        return session.logrequest__count


class FileType(OptimizedDjangoObjectType):
    """Файл пользователя."""

    ext = graphene.String(description='Расширение файла')
    size = graphene.Int(description='Размер файла в байтах')
    user = graphene.Field(devind_settings.USER_TYPE, description='Пользователь, добавивший файл')

    class Meta:
        model = File
        interfaces = (Node,)
        fields = (
            'id',
            'name',
            'src',
            'size',
            'deleted',
            'created_at',
            'updated_at',
            'user',
            'ext',
            'size',
        )
        filter_fields = {'name': ['icontains']}
        connection_class = CountableConnection


class SettingType(OptimizedDjangoObjectType):
    """Настройка приложения."""

    value = graphene.String(required=True, description='Значение')

    class Meta:
        model = Setting
        fields = (
            'id',
            'key',
            'kind_value',
            'value',
            'readonly',
        )

    @staticmethod
    def resolve_value(setting: Setting, info: ResolveInfo) -> str:
        """Возвращаем настройку по умолчанию или настройку, установленную пользователем

        :param setting:
        :param info:
        :return:
        """
        user_auth: bool = hasattr(info.context, 'user') and info.context.user.is_authenticated
        if setting.readonly or not user_auth:
            return setting.value
        user_setting = get_object_or_none(SettingValue, user=info.context.user, setting=setting)
        return user_setting.value if user_setting is not None else setting.value


class ProfileType(DjangoObjectType):
    """Тип параметров пользователей."""

    children = graphene.List(graphene.NonNull(lambda: ProfileType), required=True, description='Дочерние')
    available = graphene.List(graphene.NonNull(lambda: ProfileType), required=True,
                              description='Доступные дочерние поля')
    value = graphene.Field(lambda: ProfileValueType, description='Значение пользователя')

    class Meta:
        model = Profile
        fields = ('id', 'name', 'code', 'kind', 'position', 'children', 'available', 'value',)

    @staticmethod
    @resolver_hints(model_field='profile_set')
    def resolve_children(profile: Profile, info: ResolveInfo) -> QuerySet[Profile]:
        return profile.profile_set.all()

    @staticmethod
    @resolver_hints(model_field='profile_set')
    def resolve_available(profile: Profile, info: ResolveInfo, *args, **kwargs) -> QuerySet[Profile]:
        user_id = info.variable_values.get('userId', None)
        if not user_id:
            return profile.profile_set.none()
        _, user_id = from_global_id(user_id)
        return profile.profile_set.filter(profilevalue__user_id=user_id, profilevalue__visibility=True).all()

    @staticmethod
    def resolve_value(profile: Profile, info: ResolveInfo) -> QuerySet[ProfileValue]:
        user_id = info.variable_values.get('userId', None)
        if not user_id:
            return profile.profilevalue_set.none()
        _, user_id = from_global_id(user_id)
        return profile.profilevalue_set.get(user_id=user_id)


class ProfileValueType(OptimizedDjangoObjectType):
    """Значение параметров пользователей."""

    profile = graphene.Field(ProfileType, required=True, description='Профиль')
    user = graphene.Field(devind_settings.USER_TYPE, required=True, description='Пользователь')

    class Meta:
        model = ProfileValue
        fields = ('id', 'value', 'visibility', 'created_at', 'updated_at', 'profile', 'user',)

    @staticmethod
    def resolve_value(pv: ProfileValue, info: ResolveInfo):
        visibility = pv.visibility or info.context.user == pv.user or \
                     info.context.user.has_perm('devind_core.view_profilevalue')
        return pv.value if visibility else None


class AccessTokenType(OptimizedDjangoObjectType):
    """Токен."""

    class Meta:
        model = AccessToken
        fields = '__all__'


class ApplicationType(OptimizedDjangoObjectType):
    """Приложение."""

    class Meta:
        model = Application
        interfaces = (Node,)
        fields = '__all__'


class LogRequestType(OptimizedDjangoObjectType):
    """Лог запроса."""

    session = graphene.Field(SessionType, description='Сессия пользователя')

    class Meta:
        model = LogRequest
        interfaces = (Node,)
        fields = ('page', 'time', 'created_at', 'session',)
        filter_fields = {
            'page': ['icontains'],
            'created_at': ['gt', 'lt', 'gte', 'lte']
        }
        connection_class = CountableConnection


class LogEntryType(OptimizedDjangoObjectType):
    """Логирование действия пользователя."""

    session = graphene.Field(SessionType, description='Сессия пользователя')
    content_type = graphene.Field(ContentTypeType, description='Модель, связанная с действием')

    class Meta:
        model = LogEntry
        interfaces = (Node,)
        fields = ('object_id', 'action', 'payload', 'created_at', 'content_type', 'session',)
        filter_fields = {
            'object_id': ['icontains'],
            'action': ['contains'],
            'created_at': ['gt', 'lt', 'gte', 'lte'],
            'content_type__model': ['icontains']
        }
        connection_class = CountableConnection
