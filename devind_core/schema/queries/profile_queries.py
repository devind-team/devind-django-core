import graphene
from django.contrib.auth import get_user_model
from django.db import models
from graphene_django import DjangoListField
from graphql import ResolveInfo
from graphql_relay import from_global_id

from devind_core.models import get_profile_model, get_profile_value_model
from devind_core.schema.types import ProfileType, ProfileValueType
from devind_helpers.orm_utils import get_object_or_404

User: models.Model = get_user_model()
Profile: models.Model = get_profile_model()
ProfileValue: models.Model= get_profile_value_model()


class ProfileQueries(graphene.ObjectType):

    profiles = DjangoListField(graphene.NonNull(ProfileType), required=True, description='Список настроек профиля')
    profiles_value = graphene.List(
        graphene.NonNull(ProfileValueType),
        user_id=graphene.ID(required=True, description='Идентификатор пользователя'),
        required=True,
        description='Значение профиля пользователя'
    )
    profile_information = graphene.List(
        graphene.NonNull(ProfileType),
        user_id=graphene.ID(required=True, description='Идентификатор пользователя'),
        required=True,
        description='Доступные значения профиля пользователя'
    )

    @staticmethod
    def resolve_profiles(root, info: ResolveInfo, *args, **kwargs):
        return Profile.objects.filter(parent__isnull=True)

    @staticmethod
    def resolve_profiles_value(root, info: ResolveInfo, user_id: str, *args, **kwargs):
        user: User = get_object_or_404(User, pk=from_global_id(user_id)[1])
        return ProfileValue.objects.filter(user=user)

    @staticmethod
    def resolve_profile_information(root, info: ResolveInfo, *args, **kwargs):
        return Profile.objects.filter(parent__isnull=True)
