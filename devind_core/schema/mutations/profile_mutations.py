import graphene
from django.contrib.auth import get_user_model
from django.db.models import Max, Model
from graphql import ResolveInfo
from graphql_relay import from_global_id

from devind_core.models import get_profile_model, get_profile_value_model
from devind_core.permissions import AddProfile, DeleteProfile, ChangeProfileValue
from devind_core.schema.types import ProfileType, ProfileValueType
from devind_helpers.schema.types import ErrorFieldType
from devind_core.validators import ProfileValidator, ProfileValueValidator
from devind_helpers.decorators import permission_classes
from devind_helpers.orm_utils import get_object_or_none, get_object_or_404
from devind_helpers.permissions import IsAuthenticated
from devind_helpers.schema.mutations import BaseMutation

User: Model = get_user_model()
Profile: Model = get_profile_model()
ProfileValue: Model = get_profile_value_model()


class AddProfileMutation(BaseMutation):
    """Мутация для добавления записи профиля."""
    class Input:
        name = graphene.String(required=True, description='Название настройки')
        code = graphene.String(required=True, description='Уникальный код настройки')
        kind = graphene.Int(default=0, description='Тип настройки: [0-3]')
        parent_id = graphene.Int(description='Родительская настройка')

    profile = graphene.Field(ProfileType, description='Добавленный профайл')

    @staticmethod
    @permission_classes([IsAuthenticated, AddProfile])
    def mutate_and_get_payload(root, info: ResolveInfo, **kwargs):
        validator: ProfileValidator = ProfileValidator(kwargs)
        if validator.validate():
            return AddProfileMutation(profile=Profile.objects.create(position=Max('position') + 1, **kwargs))
        return AddProfileMutation(success=False, errors=ErrorFieldType.from_validator(validator.get_message()))


class DeleteProfileMutation(BaseMutation):
    """Мутация для удаления записи профиля."""

    class Input:
        profile_id = graphene.Int(required=True, description='Идентификатор записи')

    @staticmethod
    @permission_classes([IsAuthenticated, DeleteProfile])
    def mutate_and_get_payload(root, info: ResolveInfo, profile_id: int, **kwargs):
        return DeleteProfileMutation(success=Profile.objects.filter(pk=profile_id)[0] > 0)


class ChangeProfileValueMutation(BaseMutation):
    """Мутация на изменение значения профиля."""

    class Input:
        user_id = graphene.ID(required=True, description='Идентификатор пользователя')
        profile_id = graphene.ID(required=True, description='Идентификатор записи профиля')
        value = graphene.String(required=True, description='Значение записи')

    profile_value = graphene.Field(ProfileValueType, description='Добавленное значение профиля')

    @staticmethod
    @permission_classes([IsAuthenticated, ChangeProfileValue])
    def mutate_and_get_payload(root, info: ResolveInfo, user_id: str, profile_id: str, value: str, **kwargs):
        _, user_id = from_global_id(user_id)
        user: User = get_object_or_none(User, pk=user_id)
        info.context.check_object_permissions(info.context, user)
        validator: ProfileValueValidator = ProfileValueValidator({
            'user_id': user_id,
            'profile_id': profile_id,
            'value': value
        })
        if validator.validate():
            profile_value, _ = ProfileValue.objects.update_or_create(user_id=user_id, profile_id=profile_id, defaults={
                'value': value
            })
            return ChangeProfileValueMutation(profile_value=profile_value)
        return ChangeProfileValueMutation(success=False, errors=ErrorFieldType.from_validator(validator.get_message()))


class ChangeProfileVisibilityMutation(BaseMutation):
    """Матция для изменения видимости."""

    class Input:
        profile_value_id = graphene.ID(required=True, description='Идентификатор записи')
        visibility = graphene.Boolean(required=True, description='Значение доступности')

    profile_value = graphene.Field(ProfileValueType, description='Измененное значение поля')

    @staticmethod
    @permission_classes([IsAuthenticated, ChangeProfileValue])
    def mutate_and_get_payload(root, info: ResolveInfo, profile_value_id: str, visibility: bool, **kwargs):
        profile_value: ProfileValue = get_object_or_404(ProfileValue, pk=profile_value_id)
        info.context.check_object_permissions(info.context, profile_value.user)
        profile_value.visibility = visibility
        profile_value.save(update_fields=('visibility',))
        return ChangeProfileVisibilityMutation(profile_value=profile_value)


class ProfileMutations(graphene.ObjectType):
    add_profile = AddProfileMutation.Field(required=True)
    delete_profile = DeleteProfileMutation.Field(required=True)
    change_profile_value = ChangeProfileValueMutation.Field(required=True)
    change_profile_visibility = ChangeProfileVisibilityMutation.Field(required=True)
