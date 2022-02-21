import graphene

from devind_core.schema.mutations import FileMutations, \
    GroupMutations, \
    ProfileMutations, \
    SettingMutations, \
    SupportMutations, \
    UserMutations
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
from .queries import UserQueries, ProfileQueries, GroupQueries, SessionQueries


class Query(
    UserQueries,
    ProfileQueries,
    GroupQueries,
    SessionQueries,
    graphene.ObjectType
):
    """Запросы для приложения core"""
    pass


class Mutation(
    FileMutations,
    GroupMutations,
    ProfileMutations,
    SettingMutations,
    SupportMutations,
    UserMutations,
    graphene.ObjectType
):
    """Мутации для приложения core"""

    pass
