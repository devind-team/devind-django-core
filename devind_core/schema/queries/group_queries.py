from strawberry_django_plus import gql


from devind_core.schema.types import GroupType, PermissionType


@gql.type
class GroupQueries:

    groups: list[GroupType] = gql.django.field()
    permissions: list[PermissionType] = gql.django.field()

