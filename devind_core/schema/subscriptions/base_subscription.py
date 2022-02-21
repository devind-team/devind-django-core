from typing import Dict

import graphene
from channels_graphql_ws import Subscription

from devind_helpers.schema.types import ConsumerActionType


class BaseSubscription(Subscription):
    """Базовый протокол общения с подписками."""

    class Meta:
        abstract = True

    id = graphene.ID(required=True, description='Идентификатор объекта')
    action = graphene.Field(ConsumerActionType, required=True, description='Действие пользователя')

    def __init__(self, *args, **kwargs):
        super(BaseSubscription, self).__init__(*args, **kwargs)
        if self.action is None:
            self.action = ConsumerActionType.ADD

    @staticmethod
    async def subscribe(root, info, *args, **kwargs):
        ...

    @staticmethod
    async def publish(payload: Dict, info, *args, **kwargs):
        ...

    @classmethod
    def notify(cls, group_name, action: ConsumerActionType, object_id: int):
        cls.broadcast(group=group_name, payload={
            'action_value': action.value,
            'object_id': object_id
        })
