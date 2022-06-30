from strawberry_django_plus import gql

# from devind_core.schema.mutations import FileMutations, \
#     GroupMutations, \
#     ProfileMutations, \
#     SettingMutations, \
#     SupportMutations, \
#     UserMutations
# from devind_core.schema.types import SettingType, \
#     ProfileType, \
#     ProfileValueType, \
#     SessionType, \
#     ApplicationType, \
#     LogRequestType, \
#     FileType, \
#     LogEntryType, \
#     GroupType, \
#     PermissionType
#from .queries import UserQueries, ProfileQueries, GroupQueries, SessionQueries
from .queries import GroupQueries, ProfileQueries

@gql.type
class Query(
    #UserQueries,
    ProfileQueries,
    GroupQueries
    #SessionQueries,
):
    """Запросы для приложения core"""
    pass


# class Mutation(
#     FileMutations,
#     GroupMutations,
#     ProfileMutations,
#     SettingMutations,
#     SupportMutations,
#     UserMutations,
#     graphene.ObjectType
# ):
#     """Мутации для приложения core"""
#
#     pass
