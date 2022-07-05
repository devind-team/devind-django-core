from strawberry_django_plus import gql
from strawberry.types import Info
from django.contrib.auth import get_user_model
from django.db import models

from devind_core.models import get_profile_model, get_profile_value_model
from devind_core.schema.types import ProfileType, ProfileValueType, UserType


User: models.Model = get_user_model()
Profile: models.Model = get_profile_model()
ProfileValue: models.Model = get_profile_value_model()


@gql.type
class ProfileQueries:

    @gql.django.field
    def profiles(self) -> list[ProfileType]:
        """Список настроек профиля"""
        return Profile.objects.filter(parent__isnull=True)

    @gql.django.field
    def profiles_value(self, user_id: gql.relay.GlobalID, info: Info) -> list[ProfileValueType]:
        """Значение профиля пользователя"""
        user: User = UserType.resolve_node(user_id, required=True)
        return ProfileValue.objects.filter(user=user)

    @gql.django.field
    def profile_information(self, user_id: gql.relay.GlobalID) -> list[ProfileType]:#todo убрать user_id и рефакторинг типа
        """Доступные значения профиля пользователя"""
        return Profile.objects.filter(parent__isnull=True)

