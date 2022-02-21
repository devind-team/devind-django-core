"""Прослойка логгирования и вычисления скорости работы запросов."""

import time

from django.http import HttpRequest, HttpResponse

from ..models import get_log_request_model


class TimeRequestMiddleware:
    """Прослойка, которая высчитывает время исполнения скрипта."""

    def __init__(self, get_response):
        """Инициализация прослойки."""
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """Непосредственная обработка запроса."""
        time_start: float = time.time()
        response: HttpResponse = self.get_response(request)
        time_request = time.time() - time_start
        response['Time-Request'] = time_request
        # Не логгируем некоторые записи принудительно
        if request.body.find(b'"query":"mutation') == -1 and \
                request.body.find(b'"query":"query LogRequests') == -1 and \
                request.body.find(b'"query":"query LogGeneralRequests') == -1:
            get_log_request_model().logging(request, response, time_request)
        return response
