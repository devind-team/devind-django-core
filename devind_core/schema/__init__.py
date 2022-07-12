from strawberry_django_plus import gql

from devind_core.schema.mutations import (
    UserMutations,
    FileMutations,
    SettingMutations,
    SupportMutations,
    GroupMutations
)

from devind_core.schema.types import SettingType, \
    ProfileType, \
    ProfileValueType, \
    SessionType, \
    ApplicationType, \
    LogRequestType, \
    FileType, \
    LogEntryType, \
    GroupType, \
    PermissionType
from .queries import GroupQueries, ProfileQueries, UserQueries, SessionQueries


@gql.type
class Query(
    UserQueries,
    ProfileQueries,
    GroupQueries,
    SessionQueries
):
    """Запросы для приложения core"""
    pass


@gql.type
class Mutation(
    FileMutations,
    GroupMutations,
    #     ProfileMutations,
    SettingMutations,
    SupportMutations,
    UserMutations
):
    """Мутации для приложения core"""

    pass
