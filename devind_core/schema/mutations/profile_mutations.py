from typing import TypedDict
from django.contrib.auth import get_user_model
from django.db.models import Max, Model
from django.core.exceptions import ValidationError
from strawberry.types import Info
from strawberry_django_plus import gql
from strawberry_django_plus.permissions import IsAuthenticated, HasPerm
from devind_core.legacy import legacy_mutation
from devind_core.models import get_profile_model, get_profile_value_model
from devind_core.permissions import self_or_has_perm
from devind_core.schema.types import ProfileType, ProfileValueType, UserType
from devind_core.validators import ProfileValidator, ProfileValueValidator
from devind_helpers.orm_utils import get_object_or_none, get_object_or_404


User: Model = get_user_model()
Profile: Model = get_profile_model()
ProfileValue: Model = get_profile_value_model()


@gql.type
class ProfileMutations:

    @legacy_mutation(directives=[IsAuthenticated(), HasPerm('devind_core.add_profile')])
    def add_profile(self, name: str, code: str, kind: int, parent_id: int) -> TypedDict('', {
        'profile': ProfileType | None}):
        """Мутация для добавления записи профиля."""
        validator: ProfileValidator = ProfileValidator({'name': name, 'kind': kind, 'parent': parent_id, 'code': code})
        if validator.is_valid():
            return {'profile': Profile.objects.create(code=code, name=name, kind=kind, parent_id=parent_id)}
        raise ValidationError(validator.errors)

    @legacy_mutation(directives=[IsAuthenticated(), HasPerm('devind_core.delete_profile')])
    def delete_profile(self, profile_id: gql.ID) -> TypedDict('', {}):
        """Мутация для удаления записи профиля."""
        Profile.objects.get(id=profile_id).delete()
        return {}

    @legacy_mutation(directives=[IsAuthenticated()])
    def change_profile_value(self, user_id: gql.relay.GlobalID, profile_id: gql.ID, value: str, info: Info) -> TypedDict('', {
        'profile_value': ProfileValueType | None}):
        """Мутация на изменение значения профиля."""
        user: User = UserType.resolve_node(user_id)
        self_or_has_perm(info, user, 'devind_core.change_profilevalue')
        validator: ProfileValueValidator = ProfileValueValidator({
            'user': user_id,
            'profile': profile_id,
            'value': value
        })
        if validator.is_valid():
            profile_value, _ = ProfileValue.objects.update_or_create(user_id=user_id, profile_id=profile_id, defaults={
                'value': value
            })
            return {'profile_value': profile_value}
        raise ValidationError(validator.errors)

    @legacy_mutation(directives=[IsAuthenticated()])
    def change_profile_visibility(self, profile_value_id: gql.ID, visibility: bool, info: Info) -> TypedDict('', {
        'profile_value': ProfileValueType | None}):
        """Мутация для изменения видимости значения профиля."""
        profile_value: ProfileValue = get_object_or_404(ProfileValue, pk=profile_value_id)
        self_or_has_perm(info, profile_value.user, 'devind_core.change_profilevalue')
        profile_value.visibility = visibility
        profile_value.save(update_fields=('visibility',))
        return {'profile_value': profile_value}
