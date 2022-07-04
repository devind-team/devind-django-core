#from datetime import datetime
from typing import Any, Union, Type

from importlib import import_module
from strawberry_django_plus import gql
from strawberry.types.info import Info

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models import QuerySet, Count, Model
from auditlog.models import LogEntry
# from graphene.relay import Node
# from graphene_django.types import DjangoObjectType
# from graphene_django_optimizer import resolver_hints
# from graphql import ResolveInfo
from graphql_relay import from_global_id
from oauth2_provider.models import AccessToken, Application

from devind_core.models import get_file_model, \
    get_session_model, \
    get_profile_model, \
    get_profile_value_model, \
    get_setting_model, \
    get_setting_value_model, \
    get_log_request_model
from devind_core.models import AbstractFile, \
    AbstractSetting, \
    AbstractSettingValue, \
    AbstractProfile, \
    AbstractProfileValue, \
    AbstractSession, \
    AbstractLogRequest
from devind_core.settings import devind_settings
from devind_helpers.orm_utils import get_object_or_none

File: Type[AbstractFile] = get_file_model()
Setting: Type[AbstractSetting] = get_setting_model()
SettingValue: Type[AbstractSettingValue] = get_setting_value_model()
Profile: Type[AbstractProfile] = get_profile_model()
ProfileValue: Type[AbstractProfileValue] = get_profile_value_model()
Session: Type[AbstractSession] = get_session_model()
LogRequest: Type[AbstractLogRequest] = get_log_request_model()
User = get_user_model()


def get_user_type():
    path, cls = devind_settings.USER_TYPE.rsplit('.', 1)
    module = import_module(path)
    return getattr(module, cls)


UserType = get_user_type()


@gql.django.type(ContentType)
class ContentTypeType:
    id: gql.auto
    app_label: gql.auto
    model: gql.auto


# class ContentTypeType(OptimizedDjangoObjectType):
#     """Тип модели Django."""
#
#     class Meta:
#         model = ContentType

@gql.django.type(Group)
class GroupType(gql.relay.Node):
    id: gql.auto
    name: gql.auto
    permissions: 'list[PermissionType]'

# class GroupType(OptimizedDjangoObjectType):
#     """Группа пользователей."""
#
#     class Meta:
#         model = Group
#         fields = '__all__'


@gql.django.type(Permission)
class PermissionType:
    id: gql.auto
    name: gql.auto
    content_type: ContentTypeType
    codename: gql.auto

    @gql.django.field#(only=['group_set']) todo
    def groups(self, root: Permission) -> list[GroupType]:
        return root.group_set.all()


# class PermissionType(OptimizedDjangoObjectType):
#     """Привилегия пользователя или группы пользователей."""
#
#     groups = graphene.Field(GroupType, description='Группы')
#     content_type = graphene.Field(ContentTypeType, required=True, description='Тип модели Django')
#
#     class Meta:
#         model = Permission
#         fields = ('id', 'name', 'content_type', 'codename',)


@gql.django.type(Session)
class SessionType(gql.relay.Node):
    id: gql.auto
    #date: gql.auto todo??
    #activity: gql.auto
    #history: gql.auto
    user: UserType

    @gql.django.field
    def browser(self, root: Session) -> str:
        return root.browser

    @gql.django.field
    def device(self, root: Session) -> str:
        return root.device

    @gql.django.field
    def os(self, root: Session) -> str:
        return root.os

    # @gql.django.field todo
    # def date(self, root: Session):
    #     return root.created_at


# class SessionType(OptimizedDjangoObjectType):
#     """Сессия пользователя."""
#
#     browser = graphene.String(required=True, description='Браузер пользователя')
#     os = graphene.String(required=True, description='Операционная система пользователя')
#     device = graphene.String(required=True, description='Устройство пользователя')
#     date = graphene.DateTime(description='Дата сессии пользователя')
#     activity = graphene.Int(required=True, description='Количество действий в сессии пользователя')
#     history = graphene.Int(required=True, description='Количество запросов в сессии пользователя')
#     user = graphene.Field(devind_settings.USER_TYPE, required=True, description='Пользователь')
#
#     class Meta:
#         model = Session
#         interfaces = (Node,)
#         fields = (
#             'id',
#             'ip',
#             'browser',
#             'os',
#             'device',
#             'activity',
#             'history',
#         )
#
#     @classmethod
#     def get_queryset(cls, queryset, info):
#         queryset = queryset.annotate(Count('logentrysession'), Count('logrequest'))
#         return super(OptimizedDjangoObjectType, cls).get_queryset(queryset, info)
#
#     @staticmethod
#     @resolver_hints(select_related=('access_token',), only=('access_token__updated',))
#     def resolve_date(session: Session, info: ResolveInfo) -> datetime or None:
#         return session.created_at
#
#     @staticmethod
#     @resolver_hints(model_field='logentrysession__count')
#     def resolve_activity(session: Union[Session, Any], info: ResolveInfo) -> int:
#         return session.logentrysession__count
#
#     @staticmethod
#     @resolver_hints(model_field='logrequest__count')
#     def resolve_history(session: Union[Session, Any], info: ResolveInfo) -> int:
#         return session.logrequest__count

@gql.django.filter(File)
class FileFilter:
    name: gql.auto


@gql.django.type(File, filters=FileFilter)
class FileType(gql.relay.Node):
    id: gql.auto
    name: gql.auto
    src: gql.auto
    deleted: gql.auto
    created_at: gql.auto
    updated_at: gql.auto
    user: UserType


    @gql.django.field
    def ext(self, root: File) -> str:
        return root.ext

    @gql.django.field
    def size(self, root: File) -> float:
        return root.size


# class FileType(OptimizedDjangoObjectType):
#     """Файл пользователя."""
#
#     ext = graphene.String(description='Расширение файла')
#     size = graphene.Int(description='Размер файла в байтах')
#     user = graphene.Field(devind_settings.USER_TYPE, description='Пользователь, добавивший файл')
#
#     class Meta:
#         model = File
#         interfaces = (Node,)
#         fields = (
#             'id',
#             'name',
#             'src',
#             'size',
#             'deleted',
#             'created_at',
#             'updated_at',
#             'user',
#             'ext',
#             'size',
#         )
#         filter_fields = {'name': ['icontains']}
#         connection_class = CountableConnection


@gql.django.type(Setting)
class SettingType:#todo ds
    id: gql.auto
    key: gql.auto
    kind_value: gql.auto
    readonly: gql.auto

    @gql.django.field
    def value(self, root: Setting, info: Info) -> str:
        user_auth: bool = hasattr(info.context, 'user') and info.context.user.is_authenticated
        if root.readonly or not user_auth:
            return root.value
        user_setting = get_object_or_none(SettingValue, user=info.context.user, setting=root)
        return user_setting.value if user_setting is not None else root.value


@gql.django.type(SettingValue)
class SettingValueType:#todo ds
    id: gql.auto
    value: gql.auto
    created_at: gql.auto
    updated_at: gql.auto
    setting: SettingType
    user: UserType



# class SettingType(OptimizedDjangoObjectType):
#     """Настройка приложения."""
#
#     value = graphene.String(required=True, description='Значение')
#
#     class Meta:
#         model = Setting
#         fields = (
#             'id',
#             'key',
#             'kind_value',
#             'value',
#             'readonly',
#         )
#
#     @staticmethod
#     def resolve_value(setting: Setting, info: ResolveInfo) -> str:
#         """Возвращаем настройку по умолчанию или настройку, установленную пользователем
#
#         :param setting:
#         :param info:
#         :return:
#         """
#         user_auth: bool = hasattr(info.context, 'user') and info.context.user.is_authenticated
#         if setting.readonly or not user_auth:
#             return setting.value
#         user_setting = get_object_or_none(SettingValue, user=info.context.user, setting=setting)
#         return user_setting.value if user_setting is not None else setting.value


@gql.django.type(Profile)
class ProfileType:#todo ds
    id: gql.auto
    name: gql.auto
    code: gql.auto
    kind: gql.auto
    position: gql.auto

    @gql.django.field#(only=['profile_set'])
    def children(self, root: Profile) -> 'list[ProfileType]':
        return root.profile_set.all()

    @gql.django.field#(only=['profile_set'])
    def available(self, root: Profile, info: Info) -> 'list[ProfileType]':
        user_id = info.variable_values.get('userId', None)
        if not user_id:
            return root.profilevalue_set.none()
        _, user_id = from_global_id(user_id)
        return root.profilevalue_set.get(user_id=user_id)

    @gql.django.field#(only=['profile_set'])
    def value(self, root: Profile, info: Info) -> 'list[ProfileValueType]':
        user_id = info.variable_values.get('userId', None)
        if not user_id:
            return root.profilevalue_set.none()
        _, user_id = from_global_id(user_id)
        return root.profilevalue_set.get(user_id=user_id)


# class ProfileType(DjangoObjectType):
#     """Тип параметров пользователей."""
#
#     children = graphene.List(graphene.NonNull(lambda: ProfileType), required=True, description='Дочерние')
#     available = graphene.List(graphene.NonNull(lambda: ProfileType), required=True,
#                               description='Доступные дочерние поля')
#     value = graphene.Field(lambda: ProfileValueType, description='Значение пользователя')
#
#     class Meta:
#         model = Profile
#         fields = ('id', 'name', 'code', 'kind', 'position', 'children', 'available', 'value',)
#
#     @staticmethod
#     @resolver_hints(model_field='profile_set')
#     def resolve_children(profile: Profile, info: ResolveInfo) -> QuerySet[Profile]:
#         return profile.profile_set.all()
#
#     @staticmethod
#     @resolver_hints(model_field='profile_set')
#     def resolve_available(profile: Profile, info: ResolveInfo, *args, **kwargs) -> QuerySet[Profile]:
#         user_id = info.variable_values.get('userId', None)
#         if not user_id:
#             return profile.profile_set.none()
#         _, user_id = from_global_id(user_id)
#         return profile.profile_set.filter(profilevalue__user_id=user_id, profilevalue__visibility=True).all()
#
#     @staticmethod
#     def resolve_value(profile: Profile, info: ResolveInfo) -> QuerySet[ProfileValue]:
#         user_id = info.variable_values.get('userId', None)
#         if not user_id:
#             return profile.profilevalue_set.none()
#         _, user_id = from_global_id(user_id)
#         return profile.profilevalue_set.get(user_id=user_id)

@gql.django.type(ProfileValue)
class ProfileValueType:
    id: gql.auto
    visibility: gql.auto
    created_at: gql.auto
    updated_at: gql.auto
    user: 'UserType'
    profile: 'ProfileType'

    @gql.django.field
    def value(self, root: Profile, info: Info) -> str | None:
        visibility = root.visibility or info.context.user == root.user or \
                     info.context.user.has_perm('devind_core.view_profilevalue')
        return root.value if visibility else None



# class ProfileValueType(OptimizedDjangoObjectType):
#     """Значение параметров пользователей."""
#
#     profile = graphene.Field(ProfileType, required=True, description='Профиль')
#     user = graphene.Field(devind_settings.USER_TYPE, required=True, description='Пользователь')
#
#     class Meta:
#         model = ProfileValue
#         fields = ('id', 'value', 'visibility', 'created_at', 'updated_at', 'profile', 'user',)
#
#     @staticmethod
#     def resolve_value(pv: ProfileValue, info: ResolveInfo):
#         visibility = pv.visibility or info.context.user == pv.user or \
#                      info.context.user.has_perm('devind_core.view_profilevalue')
#         return pv.value if visibility else None


@gql.django.type(AccessToken)
class AccessTokenType:
    id: gql.auto
    user: UserType
    source_refresh_token: gql.auto # todo a
    token: gql.auto
    id_token: gql.auto #todo a
    application: gql.auto #todo a
    expires: gql.auto
    scope: gql.auto
    created: gql.auto
    updated: gql.auto

#class AccessTokenType(OptimizedDjangoObjectType):
#    """Токен."""
#
#    class Meta:
#        model = AccessToken
#        fields = '__all__'


@gql.django.type(Application)
class ApplicationType: #todo a
    id: gql.auto

# class ApplicationType(OptimizedDjangoObjectType):
#     """Приложение."""
#
#     class Meta:
#         model = Application
#         interfaces = (Node,)
#         fields = '__all__'

@gql.django.filter
class LogRequestFilter:
    page: gql.auto
    created_at: gql.auto


@gql.django.type(LogRequest, filters=LogRequestFilter)
class LogRequestType(gql.relay.Node):
    id: gql.auto
    page: gql.auto
    time: gql.auto
    created_at: gql.auto
    session: 'SessionType'




# class LogRequestType(OptimizedDjangoObjectType):
#     """Лог запроса."""
#
#     session = graphene.Field(SessionType, description='Сессия пользователя')
#
#     class Meta:
#         model = LogRequest
#         interfaces = (Node,)
#         fields = ('page', 'time', 'created_at', 'session',)
#         filter_fields = {
#             'page': ['icontains'],
#             'created_at': ['gt', 'lt', 'gte', 'lte']
#         }
#         connection_class = CountableConnection


@gql.django.type(LogEntry, filters=LogRequestFilter)
class LogEntryType(gql.relay.Node):
    id: gql.auto
    object_id: gql.auto
    action: gql.auto
    content_type: 'ContentTypeType'

    @gql.django.field
    def session(self, root: LogEntry) -> Session | None: #todo a
        if hasattr(root, 'logentrysession'):
            return root.logentrysession.session

    @gql.django.field(only=['changes'])
    def payload(self, root: LogEntry) -> str:
        return root.changes

    @gql.django.field(only=['timestamp'])
    def created_at(self, root: LogEntry) -> gql.auto:
        return root.timestamp


# class LogEntryType(OptimizedDjangoObjectType):
#     """Логирование действия пользователя."""
#
#     session = graphene.Field(SessionType, description='Сессия пользователя')
#     content_type = graphene.Field(ContentTypeType, description='Модель, связанная с действием')
#     payload = graphene.Field(graphene.String, description='Измененные данные')
#     created_at = graphene.Field(graphene.DateTime, description='Дата и время действия')
#
#     class Meta:
#         model = LogEntry
#         interfaces = (Node,)
#         fields = ('object_id', 'action', 'payload', 'created_at', 'content_type',)
#         filter_fields = {
#             'object_id': ['icontains'],
#             'action': ['contains'],
#             'content_type__model': ['icontains']
#         }
#         connection_class = CountableConnection
#
#     @staticmethod
#     def resolve_payload(le: LogEntry, info: ResolveInfo):
#         return le.changes
#
#     @staticmethod
#     def resolve_session(le: LogEntry, info: ResolveInfo) -> Session | None:
#         if hasattr(le, 'logentrysession'):
#             return le.logentrysession.session
#
#     @staticmethod
#     def resolve_created_at(le: LogEntry, info: ResolveInfo):
#         return le.timestamp
