from django.core.exceptions import ValidationError, ObjectDoesNotExist
from typing import TypedDict
from strawberry_django_plus import gql
from strawberry_django_plus.permissions import IsAuthenticated, HasPerm
from django.contrib.auth.models import Group, Permission

from devind_core.schema.types import GroupType
from devind_helpers.schema.types import ActionRelationShip
from devind_helpers.orm_utils import get_object_or_none, get_object_or_404

from devind_core.legacy import legacy_mutation


@gql.type
class GroupMutations:

    @legacy_mutation(directives=[IsAuthenticated(), HasPerm('auth.add_group')])
    def add_group(self, name: str, permission_from: gql.ID | None) -> TypedDict('', {'group': GroupType | None}):
        """Мутация для добавления группы."""
        if len(name) < 2:
            raise ValidationError({'name': 'Длина названия меньше 2 символов'})
        group: Group = Group.objects.create(name=name)
        if permission_from is not None:
            permissions: list[Permission] = Permission.objects.filter(group=permission_from).all()
            group.permissions.add(*permissions)
        return {'group': group}

    @legacy_mutation(directives=[IsAuthenticated(), HasPerm('auth.change_group')])
    def change_group_name(self, group_id: gql.ID, name: str) -> TypedDict('', {'group': GroupType | None}):
        group: Group = get_object_or_none(Group, pk=group_id)
        if group is None:
            raise ObjectDoesNotExist('Группа не найдена')
        group.name = name
        group.save(update_fields=('name',))
        return {'group': group}

    @legacy_mutation(directives=[IsAuthenticated(), HasPerm('auth.change_group')])
    def change_group_permissions(self, group_id: gql.ID, permissions_id: list[gql.ID], action: ActionRelationShip) -> TypedDict('', {'permissions_id': list[gql.ID] | None, 'action': ActionRelationShip | None}):
        group: Group = get_object_or_404(Group, pk=group_id)
        if action == ActionRelationShip.ADD:
            group.permissions.add(*Permission.objects.filter(pk__in=permissions_id))
        elif action == ActionRelationShip.DELETE:
            group.permissions.remove(*Permission.objects.filter(pk__in=permissions_id))
        else:
            raise ValidationError({'action': 'Действие не найдено'})
        return {'permissions_id': permissions_id, 'action': action}
