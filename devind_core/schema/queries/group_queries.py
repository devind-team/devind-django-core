from strawberry_django_plus import gql


from devind_core.schema.types import GroupType, PermissionType


@gql.type
class GroupQueries:

    groups: gql.relay.Connection[GroupType] = gql.django.connection()
    permissions: list[PermissionType] = gql.django.field()

