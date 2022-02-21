from typing import List

import graphene
from django.contrib.auth import get_user_model
from django.db import models
from graphene_django import DjangoListField
from graphene_django.filter import DjangoFilterConnectionField
from graphql import ResolveInfo
from oauth2_provider.models import Application

from devind_core.models import get_session_model, get_log_entry_model, get_log_request_model
from devind_core.permissions import ChangeUser
from devind_core.schema.types import SessionType, \
    ApplicationType, \
    LogRequestType, \
    LogEntryType
from devind_helpers.decorators import permission_classes
from devind_helpers.orm_utils import get_object_or_404
from devind_helpers.permissions import IsAuthenticated
from devind_helpers.utils import from_gid_or_none

User: models.Model = get_user_model()
Session: models.Model = get_session_model()
LogEntry: models.Model = get_log_entry_model()
LogRequest: models.Model = get_log_request_model()


class SessionQueries(graphene.ObjectType):

    applications = DjangoListField(ApplicationType, required=True, description='Приложения')
    sessions = DjangoListField(SessionType, user_id=graphene.ID(), required=True, description='Доступные сессии')
    log_requests = DjangoFilterConnectionField(LogRequestType, user_id=graphene.ID(), required=True)
    log_entry = DjangoFilterConnectionField(LogEntryType, user_id=graphene.ID(), required=True)

    @staticmethod
    @permission_classes([IsAuthenticated])
    def resolve_applications(root, info: ResolveInfo, *args, **kwargs):
        return Application.objects.all()

    @staticmethod
    @permission_classes([IsAuthenticated, ChangeUser])
    def resolve_sessions(root, info: ResolveInfo, user_id=None) -> List[Session]:
        if user_id is not None:
            user: User = get_object_or_404(User, pk=from_gid_or_none(user_id)[1])
        else:
            user: User = info.context.user
        info.context.check_object_permissions(info.context, user)
        return Session.objects.filter(access_token__user=user).order_by('-access_token')

    @staticmethod
    @permission_classes([IsAuthenticated, ChangeUser])
    def resolve_log_requests(root, info: ResolveInfo, user_id=None, **kwargs) -> List[LogRequest]:
        if user_id is not None:
            user: User = get_object_or_404(User, pk=from_gid_or_none(user_id)[1])
        else:
            user: User = info.context.user
        info.context.check_object_permissions(info.context, user)
        return LogRequest.objects.filter(session__user=user)

    @staticmethod
    @permission_classes([IsAuthenticated, ChangeUser])
    def resolve_log_entry(root, info: ResolveInfo, user_id=None, **kwargs) -> List[LogEntry]:
        """Возвращаем логгированные Entry. Либо это я, либо имею право."""
        user: User = get_object_or_404(User, pk=from_gid_or_none(user_id)[1]) \
            if user_id is not None \
            else info.context.user
        info.context.check_object_permissions(info.context, user)
        return LogEntry.objects.filter(session__user=user)
