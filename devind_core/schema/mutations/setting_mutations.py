from typing import TypedDict
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.db import models
from strawberry.types import Info
from strawberry_django_plus import gql
from strawberry_django_plus.permissions import IsAuthenticated

from devind_core.models import get_setting_model, get_setting_value_model
from devind_core.schema.types import SettingType, UserType, SettingValueType
from devind_core.permissions import self_or_has_perm
from devind_core.legacy import legacy_mutation

Setting: models.Model = get_setting_model()
SettingValue: models.Model = get_setting_value_model()
User: models.Model = get_user_model()


@gql.type
class SettingMutations:

    @legacy_mutation(directives=[IsAuthenticated()])
    def change_settings(self, info: Info, user_id: str, key: str, value: str) -> TypedDict('', {'setting': SettingType | SettingValueType | None}):
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
        return {'setting': res}

    @legacy_mutation(directives=[IsAuthenticated()])
    def reset_settings(self, info: Info, user_id: gql.relay.GlobalID) -> TypedDict('', {'settings': list[SettingType] | None}):
        """Мутация для сброса настроек по умолчанию"""
        user: User = UserType.resolve_node(user_id)
        self_or_has_perm(info, user, 'devind_core.delete_setting')
        SettingValue.objects.filter(user=user).delete()
        settings = Setting.objects.all()
        return {'settings': settings}
