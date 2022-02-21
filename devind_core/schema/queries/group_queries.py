import graphene
from graphene_django import DjangoListField

from devind_core.schema.types import GroupType, PermissionType


class GroupQueries(graphene.ObjectType):

    groups = DjangoListField(GroupType, required=True)
    permissions = DjangoListField(PermissionType, required=True)

