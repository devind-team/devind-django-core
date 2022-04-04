from typing import List

import graphene
from django.contrib.auth.models import Group, Permission
from graphql import ResolveInfo

from devind_core.permissions import AddGroup, ChangeGroup, DeleteGroup
from devind_core.schema.types import GroupType
from devind_helpers.schema.types import ErrorFieldType, ActionRelationShip
from devind_helpers.decorators import permission_classes
from devind_helpers.orm_utils import get_object_or_404
from devind_helpers.permissions import IsAuthenticated
from devind_helpers.schema.mutations import BaseMutation


class AddGroupMutation(BaseMutation):
    """Мутация для добавления группы."""

    class Input:
        name = graphene.String(required=True, description='Название группы')
        permission_from = graphene.Int(desctiption='Скопировать привилегии из указанной группы')

    group = graphene.Field(GroupType, description='Добавленная группа')

    @staticmethod
    @permission_classes([IsAuthenticated, AddGroup])
    def mutate_and_get_payload(root, info: ResolveInfo, name: str, permission_from: int or None = None):
        if len(name) < 2:
            return AddGroupMutation(
                success=False,
                errors=[ErrorFieldType('name', ['Длина названия меньше 2 символов'])]
            )
        group: Group = Group.objects.create(name=name)
        if permission_from is not None:
            permissions: List[Permission] = Permission.objects.filter(group=permission_from).all()
            group.permissions.add(*permissions)
        return AddGroupMutation(group=group)


class ChangeGroupNameMutation(BaseMutation):
    """Мутация для изменения имени группы."""

    class Input:
        group_id = graphene.Int(required=True, description='Идентификатор группы')
        name = graphene.String(required=True, description='Название группы')

    group = graphene.Field(GroupType, description='Измененная группа')

    @staticmethod
    @permission_classes([IsAuthenticated, ChangeGroup])
    def mutate_and_get_payload(root, info: ResolveInfo, group_id: int, name: str):
        group: Group = get_object_or_404(Group, pk=group_id)
        group.name = name
        group.save(update_fields=('name',))
        return ChangeGroupNameMutation(group=group)


class ChangeGroupPermissionsMutation(BaseMutation):
    """Мутация для изменения привилегий группы."""

    class Input:
        group_id = graphene.Int(required=True, description='Идентификатор группы')
        permissions_id = graphene.List(graphene.Int, required=True, description='Идентификаторы привилегий')
        action = graphene.Field(ActionRelationShip, required=True, description='Действие')

    permissions_id = graphene.List(graphene.Int, required=True, description='Идентификаторы привилегий')
    action = graphene.Field(ActionRelationShip, required=True, description='Действие')

    @staticmethod
    @permission_classes([IsAuthenticated, ChangeGroup])
    def mutate_and_get_payload(
            root,
            info: ResolveInfo,
            group_id: int,
            permissions_id,
            action: ActionRelationShip):
        group: Group = get_object_or_404(Group, pk=group_id)
        if action == ActionRelationShip.ADD:
            group.permissions.add(*Permission.objects.filter(pk__in=permissions_id))
        elif action == ActionRelationShip.DELETE:
            group.permissions.remove(*Permission.objects.filter(pk__in=permissions_id))
        else:
            return ChangeGroupPermissionsMutation(
                status=False,
                errors=[ErrorFieldType('action', ['Действие не найдено'])]
            )
        return ChangeGroupPermissionsMutation(permissions_id=permissions_id, action=action)


class DeleteGroupMutation(BaseMutation):
    """Мутация для удаления группы."""

    class Input:
        group_id = graphene.Int(required=True, description='Идентификатор группы')

    id = graphene.ID(required=True, description='Идентификатор группы')

    @staticmethod
    @permission_classes([IsAuthenticated, DeleteGroup])
    def mutate_and_get_payload(root, info: ResolveInfo, group_id: int):
        Group.objects.filter(pk=group_id).delete()
        return DeleteGroupMutation(id=group_id)


class GroupMutations(graphene.ObjectType):
    add_group = AddGroupMutation.Field(required=True)
    change_group_name = ChangeGroupNameMutation.Field(required=True)
    change_group_permissions = ChangeGroupPermissionsMutation.Field(required=True)
    delete_group = DeleteGroupMutation.Field(required=True)