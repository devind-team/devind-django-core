"""Прослойка определения пользовательской сессии."""

from typing import Type

from django.db import models
from django.http import HttpRequest, HttpResponse

from devind_helpers.orm_utils import get_object_or_none
from ..models import get_session_model


class SessionMiddleware:
    """Прослойка находит и добавляет к пользователю сессию."""

    def __init__(self, get_response):
        """Инициализация прослойки."""
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """Непосредственная обработка запроса."""
        Session: Type[models.Model] = get_session_model()   # noqa
        if request.META.get("HTTP_AUTHORIZATION", "").startswith("Bearer") \
                and hasattr(request, 'user') \
                and request.user.is_authenticated:
            _, token = request.META.get("HTTP_AUTHORIZATION", "").split(' ')
            request.session = get_object_or_none(Session, access_token__token=token, user=request.user)
        else:
            request.session = None
        return self.get_response(request)
