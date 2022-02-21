"""Модуль с командой обновления настроек приложения."""

import json
from os.path import join

from django.apps import apps
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand
from django.db.models import Model


class Command(BaseCommand):
    """Команда обновления настроек приложения."""

    help = 'Обновление настроек приложения'

    def add_arguments(self, parser):
        parser.add_argument(
            '-m',
            '--model',
            help='Имя модели',
            default='core.Setting'
        )
        parser.add_argument(
            '-f',
            '--file',
            help='Имя модели',
            default='001.core/003.Setting.json'
        )

    def handle(self, *args, **options):
        app, model = options['model'].split('.')
        path = join(settings.BASE_DIR, 'apps', app, 'management', 'seed')
        model: Model = apps.get_model(app, model)
        model_data: str = join(path, *options['file'].split('/'))
        with open(model_data) as f:
            settings_data = json.load(f)
        for sd in settings_data:
            try:
                model.objects.get(**sd)
            except ObjectDoesNotExist:
                model.objects.create(**sd)
        self.stdout.write(f'Настройки успешно обновлены')
