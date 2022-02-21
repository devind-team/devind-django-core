"""Модель, описывающий таблицу хранения пользовательских запросов."""

from django.db import models

from ..settings import devind_settings


class AbstractLogRequest(models.Model):
    """Модель для хранения логов пользовательских запросов."""

    page = models.CharField(max_length=255, null=True, help_text='Страница, с которой отправлен запрос')
    body = models.BinaryField(help_text='Запрос или мутация')
    time = models.FloatField(default=0, help_text='Время работы страницы')

    created_at = models.DateTimeField(auto_now=True, help_text='Дата и время запроса')

    session = models.ForeignKey(
        devind_settings.SESSION_MODEL,
        null=True,
        on_delete=models.CASCADE,
        help_text='Сессия пользователя (null, если пользователя нет)'
    )

    class Meta:
        """Мета класс модель для хранения пользовательских запросов."""

        abstract = True
        ordering = ('-created_at',)

    @classmethod
    def logging(cls, request, response, time_request: float) -> None:   # noqa
        """Функция записи логов."""
        cls.objects.create(
            page=request.headers.get('Referer', request.path_info),
            body=request.body,
            time=time_request,
            session=request.session
        )
