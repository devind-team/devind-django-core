import datetime
from typing import Any, Type

from importlib import import_module
from strawberry_django_plus import gql
from strawberry.types.info import Info

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from auditlog.models import LogEntry
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


@gql.django.filter(ContentType, lookups=True)
class ContentTypeFilter:
    model: gql.auto


#todo документация
@gql.django.type(ContentType, filters=ContentTypeFilter)
class ContentTypeType:
    id: gql.auto
    app_label: gql.auto
    model: gql.auto


@gql.django.type(Group)
class GroupType:
    id: gql.auto
    name: gql.auto
    permissions: 'list[PermissionType]'


@gql.django.type(Permission)
class PermissionType:
    id: gql.auto
    name: gql.auto
    content_type: ContentTypeType
    codename: gql.auto

    @gql.django.field(prefetch_related=['group_set'])
    def groups(self, root: Permission) -> list[GroupType]:
        return root.group_set.all()


@gql.django.type(Session, pagination=True)
class SessionType(gql.relay.Node):
    id: gql.auto
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

    @gql.django.field
    def date(self, root: Session) -> datetime.datetime:
        return root.created_at

    @gql.django.field
    def resolve_activity(self, root: Session | Any) -> int:
        return root.logentrysession_set.count

    @gql.django.field
    def resolve_history(self, root: Session | Any) -> int:
        return root.logrequest_set.count


@gql.django.filter(File, lookups=True)
class FileFilter:
    name: gql.auto


@gql.django.type(File, filters=FileFilter, pagination=True)
class FileType(gql.relay.Node):
    id: gql.auto
    name: gql.auto
    src: str
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


@gql.django.type(Setting)
class SettingType:
    id: gql.auto
    key: gql.auto
    kind_value: gql.auto
    readonly: gql.auto

    @gql.django.field
    def value(self, root: Setting, info: Info) -> str:
        user_auth: bool = hasattr(info.context, 'user') and info.context.request.user.is_authenticated
        if root.readonly or not user_auth:
            return root.value
        user_setting = get_object_or_none(SettingValue, user=info.context.request.user, setting=root)
        return user_setting.value if user_setting is not None else root.value


@gql.django.type(SettingValue)
class SettingValueType:
    id: gql.auto
    value: gql.auto
    created_at: gql.auto
    updated_at: gql.auto
    setting: SettingType
    user: UserType


@gql.django.type(Profile)
class ProfileType:
    id: gql.auto
    name: gql.auto
    code: gql.auto
    kind: gql.auto
    position: gql.auto

    @gql.django.field(prefetch_related=['profile_set'])
    def children(self, root: Profile) -> 'list[ProfileType]':
        return root.profile_set.all()

    @gql.django.field(prefetch_related=['profile_set'])
    def available(self, root: Profile, info: Info) -> 'list[ProfileType]':
        user_id = info.variable_values.get('userId', None)
        if not user_id:
            return root.profilevalue_set.none()
        _, user_id = from_global_id(user_id)
        return root.profilevalue_set.get(user_id=user_id)

    @gql.django.field(prefetch_related=['profile_set'])
    def value(self, root: Profile, info: Info) -> 'list[ProfileValueType]':
        user_id = info.variable_values.get('userId', None)
        if not user_id:
            return root.profilevalue_set.none()
        _, user_id = from_global_id(user_id)
        return root.profilevalue_set.get(user_id=user_id)


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
        visibility = root.visibility or info.context.request.user == root.user or \
                     info.context.request.user.has_perm('devind_core.view_profilevalue')
        return root.value if visibility else None


@gql.django.type(AccessToken)
class AccessTokenType:
    id: gql.auto
    user: UserType
    source_refresh_token: gql.auto
    token: gql.auto
    id_token: gql.auto
    application: gql.auto
    expires: gql.auto
    scope: gql.auto
    created: gql.auto
    updated: gql.auto


@gql.django.type(Application)
class ApplicationType:
    id: gql.auto
    client_id: gql.auto
    user: UserType
    redirect_uris: gql.auto
    client_type: gql.auto
    authorization_grant_type: gql.auto
    client_secret: gql.auto
    name: gql.auto
    skip_authorization: gql.auto
    created: gql.auto
    updated: gql.auto
    algorithm: gql.auto


@gql.django.filter(LogRequest, lookups=True)
class LogRequestFilter:
    page: gql.auto
    created_at: gql.auto


@gql.django.type(LogRequest, filters=LogRequestFilter, pagination=True)
class LogRequestType(gql.relay.Node):
    id: gql.auto
    page: gql.auto
    time: gql.auto
    created_at: gql.auto
    session: 'SessionType'


@gql.django.filter(LogEntry, lookups=True)
class LogEntryFilter:
    action: gql.auto
    content_type: 'ContentTypeFilter'


@gql.django.type(LogEntry, filters=LogEntryFilter, pagination=True)
class LogEntryType(gql.relay.Node):
    id: gql.relay.GlobalID
    object_id: gql.auto
    action: gql.auto
    content_type: 'ContentTypeType' = gql.django.field(filters=ContentTypeFilter)

    @gql.django.field
    def session(self, root: LogEntry) -> SessionType | None:
        if hasattr(root, 'logentrysession'):
            return root.logentrysession.session

    @gql.django.field(only=['changes'])
    def payload(self, root: LogEntry) -> str:
        return root.changes

    @gql.django.field(only=['timestamp'])
    def created_at(self, root: LogEntry) -> datetime.time:
        return root.timestamp
