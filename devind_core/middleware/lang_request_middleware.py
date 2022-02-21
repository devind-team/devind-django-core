from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.utils import translation


class LangRequestMiddleware:
    """Прослойка, добавляющая язык в запрос."""

    def __init__(self, get_response):
        """Инициализация прослойки определение языка запроса."""
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """Получение языка из заголовков."""
        locale = request.headers.get('Accept-Language', settings.LANGUAGE_CODE)
        translation.activate(locale)
        request.LANGUAGE_CODE = locale
        return self.get_response(request)
