"""Логгирование действий пользователей."""

import inspect

from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.http import HttpRequest
from django.db.models import AutoField
from django.db.models.fields.related import ManyToManyField, ManyToManyRel, ManyToOneRel

from ..settings import devind_settings


class AbstractLogEntry(models.Model):
    """Логгирование действия пользователя."""

    # Тип действия пользователя
    ADDITION = 1
    CHANGE = 2
    DELETION = 3
    ACTIONS = (
        (ADDITION, 'addition'),
        (CHANGE, 'change'),
        (DELETION, 'deletion')
    )

    object_id = models.TextField(null=True, help_text='Идентификатор модели')
    content_type = models.ForeignKey(
        ContentType,
        null=True,
        on_delete=models.SET_NULL,
        help_text='Модель, связанная с действием'
    )

    action = models.PositiveSmallIntegerField(choices=ACTIONS, default=ADDITION, help_text='Действие пользователя')
    payload = models.JSONField(help_text='Измененные данные')

    created_at = models.DateTimeField(auto_now_add=True, help_text='Дата и время действия')

    session = models.ForeignKey(
        devind_settings.SESSION_MODEL,
        null=True,
        on_delete=models.SET_NULL,
        help_text='Сессия пользователя'
    )

    class Meta:
        """Мета класс хранения изменений данных."""

        abstract = True
        ordering = ('-created_at',)

    @classmethod
    def logging(cls, sender, instance: models.Model, **kwargs):
        """Логгируем изменение модели."""
        request: HttpRequest or None = None
        for entry in reversed(inspect.stack()):
            try:
                request = entry[0].f_locals['request']
                if isinstance(request, HttpRequest):
                    break
            except KeyError:
                pass
        if request is not None and hasattr(request, 'session'):
            created: bool or None = kwargs.get('created', None)
            if created is None:
                cls.delete_logging(request.session, sender, instance)
            else:
                del kwargs['created']
                cls.action_logging(request.session, sender, instance, created, **kwargs)

    @classmethod
    def action_logging(cls, session, sender, instance: models.Model, created: bool, **kwargs):
        """Логируем изменение добавления или удаления."""
        cls.objects.create(
            object_id=instance.pk,
            action=cls.ADDITION if created else cls.CHANGE,
            payload=cls.change_values(instance)
            if created else {field: str(getattr(instance, field)) for field in kwargs.get('update_fields', [])},
            content_type=ContentType.objects.get_for_model(sender),
            session=session
        )

    @classmethod
    def delete_logging(cls, session, sender, instance: models.Model):
        """Логгируем удаление модели."""
        cls.objects.create(
            object_id=instance.pk,
            action=cls.DELETION,
            payload=cls.change_values(instance),
            content_type=ContentType.objects.get_for_model(sender),
            session=session
        )

    @classmethod
    def change_values(cls, instance: models.Model) -> dict:
        """Вспомогательный метод по идентификаторам."""
        return {
            field.name: str(getattr(instance, field.name))
            for field in instance._meta.get_fields()
            if cls.is_valid(field)
        }

    @staticmethod
    def is_valid(field):
        """Проверяем, валидно ли сохранение изменения."""
        return not (
                isinstance(field, AutoField)
                or isinstance(field, ManyToManyField)
                or isinstance(field, ManyToManyRel)
                or isinstance(field, ManyToOneRel)
        )
