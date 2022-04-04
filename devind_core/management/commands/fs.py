"""Модуль с командой первоначального развертывания проекта."""

import json
import time
from os import listdir
from os.path import join, isdir, isfile, splitext
from typing import Optional, Protocol, Any, Type

from django.apps import apps
from django.conf import settings
from django.contrib.contenttypes.fields import ReverseGenericManyToOneDescriptor
from django.core.management.base import BaseCommand
from django.db import connection
from django.db.models import Model, Field, ForeignKey, ManyToManyField


class _WithTranslations(Protocol):
    """Модель с полем translations."""

    translations: ReverseGenericManyToOneDescriptor


class Command(BaseCommand):
    """Команда первоначального развертывания проекта."""

    help = 'Первоначальное развертывание проекта'

    seed_path = join(settings.BASE_DIR, 'apps/%s/management/seed')

    @staticmethod
    def separate_and_resolve(
            mdl: Type[Model],
            data: dict[str, Any]
    ) -> tuple[dict[str, Any], dict[str, list[Model]]]:
        """Отделение и разрешение полей типа ForeignKey и ManyToMany.

        :param mdl: модель
        :param data: данные для создания объекта модели
        :return (данные для создания объекта модели с разрешенными полями ForeignKey и без полей ManyToMany,
        разрешенные поля ManyToMany)
        """

        result_data: dict[str, Any] = {}
        many_to_many: dict[str, list[Model]] = {}
        for k, v in data.items():
            field: Field = mdl._meta.get_field(k)
            if type(field) is ManyToManyField:
                many_to_many[k] = [field.related_model.objects.get(pk=pk) for pk in v]
            elif type(field) is ForeignKey:
                result_data[k] = field.related_model.objects.get(pk=v)
            else:
                result_data[k] = v
        return result_data, many_to_many

    @staticmethod
    def apply_modifiers(data: dict[str, Any]) -> dict[str, Any]:
        """Применение модификаторов.

        :param data: данные для создания объекта модели
        :return: данные для создания объекта модели с примененными модификаторами
        """

        result_data: dict[str, Any] = {}
        for k, v in data.items():
            k, *modifiers = k.split('|')
            for modifier in modifiers:
                if modifier == 'json':
                    v = json.dumps(v)
            result_data[k] = v
        return result_data

    @staticmethod
    def apply_methods(obj: Model, methods: list[dict]) -> None:
        """Применение методов к объекту модели.

        :param obj: объект модели
        :param methods: описание методов
        """

        for method in methods:
            method_name = method.pop('name')
            args = method.pop('args', [])
            kwargs = method.pop('kwargs', {})
            getattr(obj, method_name)(*args, **kwargs)
            obj.save()

    def seeder_factory(
            self,
            mdl: Type[Model],
            data: list[dict[str, Any]],
            parent: Optional[Model] = None) -> Optional[int]:
        """Фабрика объектов модели.

        :param mdl: модель
        :param data: данные для создание объектов модели
        :param parent: родительский объект модели
        :return: максимальный идентификатор созданных объектов модели
        """

        ids = []
        for d in data:
            methods: Optional[list[dict]] = d.pop('methods', None)
            translations: Optional[dict[str, list]] = d.pop('translations', None)
            children: Optional[list[dict]] = d.pop('children', None)
            try:
                data_for_creating = self.apply_modifiers(d)
                data_for_creating, many_to_many = self.separate_and_resolve(mdl, data_for_creating)
                data_for_creating = data_for_creating if parent is None else {**data_for_creating, 'parent': parent}
                obj, _ = mdl.objects.get_or_create(**data_for_creating)
                for field_name in many_to_many:
                    for item in many_to_many[field_name]:
                        getattr(obj, field_name).add(item)
                if 'id' in d:
                    ids.append(d['id'])
                if methods is not None:
                    self.apply_methods(obj, methods)
                if children is not None:
                    ids.append(self.seeder_factory(mdl, children, obj))
            except Exception as ex:
                self.stdout.write(str(ex))
                continue
        return max((e for e in ids if e is not None), default=None)

    def add_arguments(self, parser):
        parser.add_argument(
            '--app',
            default='core',
            help='Указываем приложение для парсинга'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            default=False,
            help='Очищать модели или нет'
        )
        parser.add_argument(
            '--no-sequencer',
            '-ns',
            action='store_true',
            default=False,
            help='Отключение изменения SEQUENCE'
        )

    def handle(self, *args, **options):
        start_time = time.time()
        self.stdout.write('Инициализация проекта')
        seed_path = self.seed_path % options['app']
        app_dirs = sorted(name for name in listdir(join(seed_path)) if isdir(join(seed_path, name)))
        for app_name in app_dirs:
            self.stdout.write(f'  Приложение {app_name[4:]}')
            app_path = join(seed_path, app_name)
            mdls_name = sorted(name for name in listdir(app_path) if isfile(join(app_path, name)))
            for mdl_name in mdls_name:
                mdl_path = join(app_path, mdl_name)
                mdl, _ = splitext(mdl_name)
                self.stdout.write(f'    Модель {mdl}')
                model = apps.get_model(app_name[4:], mdl[4:])
                if options['clear']:
                    model.objects.all().delete()
                with open(mdl_path, encoding='utf-8') as file:
                    max_id = self.seeder_factory(model, json.load(file))
                if not options['no-sequencer'] and max_id is not None:
                    with connection.cursor() as cursor:
                        cursor.execute(
                            f'ALTER SEQUENCE {model._meta.db_table}_id_seq RESTART WITH {max_id + 1};'
                        )
        self.stdout.write(f'Развертывание проекта завершено за время: {str((time.time() - start_time) / 60)} минут')
