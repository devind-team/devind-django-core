from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.db import models
from strawberry.types import Info
from strawberry_django_plus import gql
from strawberry_django_plus.permissions import IsAuthenticated

from devind_core.models import get_setting_model, get_setting_value_model
from devind_core.schema.types import SettingType, UserType, SettingValueType
from devind_core.permissions import self_or_has_perm

Setting: models.Model = get_setting_model()
SettingValue: models.Model = get_setting_value_model()
User: models.Model = get_user_model()


@gql.type
class SettingMutations:

    @gql.input_mutation(directives=[IsAuthenticated()])
    def change_settings(self, info: Info, user_id: str, key: str, value: str) -> SettingType | SettingValueType:
        """Мутация для изменения настроек"""
        user: User = UserType.resolve_node(user_id)
        setting = Setting.objects.get(key=key)
        if setting.readonly:
            if not info.context.request.user.has_perm('devind_core.change_setting'):
                raise PermissionDenied('Ошибка доступа')
            setting.value = value
            setting.save(update_fields=('value',))
            res = setting
        else:
            res = SettingValue.objects.update_or_create(user=user, setting=setting, defaults={'value': value})[0]
        return res

    @gql.django.input_mutation(directives=[IsAuthenticated()])
    def reset_settings(self, info: Info, user_id: gql.relay.GlobalID) -> list[SettingType]:
        """Мутация для сброса настроек по умолчанию"""
        user: User = UserType.resolve_node(user_id)
        self_or_has_perm(info, user, 'devind_core.delete_setting')
        SettingValue.objects.filter(user=user).delete()
        settings = Setting.objects.all()
        return settings



# class ChangeSettingsMutation(BaseMutation):
#     """Мутация для изменения настроек"""
#
#     class Input:
#         key = graphene.String(required=True, description='Идентификатор настройки')
#         user_id = graphene.ID(required=True, description='Идентификатор пользователя')
#         value = graphene.String(required=True, description='Значение настройки')
#
#     setting = graphene.Field(SettingType, description='Измененная настройка')
#
#     @staticmethod
#     @permission_classes([IsAuthenticated, ChangeSetting])
#     def mutate_and_get_payload(root, info: ResolveInfo, user_id: str, key: str, value: str, **kwargs):
#         _, user_id = from_global_id(user_id)
#         user: User = get_object_or_404(User, pk=user_id)
#         setting = Setting.objects.get(key=key)
#         if setting.readonly:
#             info.context.check_object_permissions(info.context, setting)
#             setting.value = value
#             setting.save(update_fields=('value',))
#         else:
#             SettingValue.objects.update_or_create(user=user, setting=setting, defaults={'value': value})
#         return ChangeSettingsMutation(setting=setting)


# class ResetSettingsMutation(BaseMutation):
#     """Мутация для сброса настроек по умолчанию"""
#
#     class Input:
#         user_id = graphene.ID(required=True, description='Идентификатор пользователя')
#
#     settings = graphene.List(graphene.NonNull(SettingType), description='Лист настроек')
#
#     @staticmethod
#     @permission_classes([IsAuthenticated, DeleteSettings])
#     def mutate_and_get_payload(root, info: ResolveInfo, user_id: str, **kwargs):
#         _, user_id = from_global_id(user_id)
#         user: User = get_object_or_404(User, pk=user_id)
#         info.context.check_object_permissions(info.context, user)
#         SettingValue.objects.filter(user=user).delete()
#         settings = Setting.objects.all()
#         return ResetSettingsMutation(settings=settings)


# class SettingMutations(graphene.ObjectType):
#     change_settings = ChangeSettingsMutation.Field(required=True)
#     reset_settings = ResetSettingsMutation.Field(required=True)
