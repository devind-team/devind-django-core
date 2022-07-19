from typing import Iterable
from strawberry_django_plus import gql
from strawberry.types import Info
from strawberry_django_plus.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from django.db import models
from auditlog.models import LogEntry

from devind_core.models import get_session_model, get_log_request_model
from devind_core.schema.types import SessionType, \
    ApplicationType, \
    LogRequestType, \
    LogEntryType, \
    UserType
from devind_core.permissions import self_or_can_change

User: models.Model = get_user_model()
Session: models.Model = get_session_model()
LogRequest: models.Model = get_log_request_model()


@gql.type
class SessionQueries:
    applications: list[ApplicationType] = gql.django.field(directives=[IsAuthenticated()], description='Приложения')

    @gql.field(directives=[IsAuthenticated()])
    def sessions(self, info: Info, user_id: gql.relay.GlobalID | None = None) -> list[SessionType]:
        """Доступные сессии"""
        if user_id is not None:
            user: User = UserType.resolve_node(user_id)
        else:
            user: User = info.context.request.user
        self_or_can_change(info, user)
        return Session.objects.filter(access_token__user=user).order_by('-access_token')

    @gql.django.connection(directives=[IsAuthenticated()])
    def log_requests(self, info: Info, user_id: gql.relay.GlobalID | None = None) -> Iterable[LogRequestType]:
        if user_id is not None:
            user: User = UserType.resolve_node(user_id)
        else:
            user: User = info.context.request.user
        self_or_can_change(info, user)
        return LogRequest.objects.filter(session__user=user)

    @gql.django.connection(directives=[IsAuthenticated()])
    def log_entry(self, info: Info, user_id: gql.relay.GlobalID | None = None) -> Iterable[LogEntryType]:
        """Возвращаем логгированные Entry. Либо это я, либо имею право."""
        user: User = UserType.resolve_node(user_id) \
            if user_id is not None \
            else info.context.request.user
        self_or_can_change(info, user)
        return LogEntry.objects.filter(actor=user)
