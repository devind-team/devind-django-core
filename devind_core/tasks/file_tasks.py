"""Модуль с задачами по обработке файлов."""

from celery import shared_task
from django.apps import apps

from devind_helpers.files import SynchronizeModelFilesInfo, SynchronizedFilesInfo, synchronize_sign as synchronize
from devind_helpers.files import clear_apps_files, DeletedFileInfo


@shared_task
def synchronize_sign(data: list[dict]) -> list[dict[str, str]]:
    """Синхронизация между файлами и их электронными подписями.

    :param data: данные для формирования информации о файлах моделей для синхронизации
    :return: информация о синхронизированных файлах
    """
    result: list[dict[str, str]] = []
    synchronize(
        map(
            lambda info_data: SynchronizeModelFilesInfo(
                model=apps.get_model(info_data['model']),
                file_field_name=info_data['file_field_name'],
                sign_field_name=info_data['sign_field_name']
            ), data
        ),
        lambda files_info: result.append(_synchronize_result_to_dict(files_info))
    )
    return result


@shared_task
def clear_files(app_labels: list[str]) -> list[dict[str, str]]:
    """Удаление лишних файлов.

    :param app_labels: названия приложений, в которых необходимо удалить файлы
    :return: информация об удаленных файлах
    """
    result: list[dict[str, str]] = []
    clear_apps_files(app_labels, lambda files_info: result.append(_clear_result_to_dict(files_info)))
    return result


@shared_task
def process_files(synchronize_sign_data: list[dict], clear_files_data: list[str]) -> None:
    """Обработка файлов.

    :param synchronize_sign_data: данные для задачи synchronize_sign
    :param clear_files_data: данные для задачи clear_files
    """
    (synchronize_sign.si(synchronize_sign_data) | clear_files.si(clear_files_data)).delay()


def _synchronize_result_to_dict(synchronized_files_info: SynchronizedFilesInfo) -> dict[str, str]:
    """Преобразование информации о синхронизированных файлах в словарь.

    :param synchronized_files_info: информация о синхронизированных файлах
    :return: информация о синхронизированных файлах в виде словаря
    """
    return {
        'model': synchronized_files_info.files_info.model.__name__,
        'file_field_name': synchronized_files_info.files_info.file_field_name,
        'sign_field_name': synchronized_files_info.files_info.sign_field_name,
        'file_path': {
            'path': synchronized_files_info.file_path[0],
            'added': synchronized_files_info.file_path[1]
        },
        'sign_path': {
            'path': synchronized_files_info.sign_path[0],
            'added': synchronized_files_info.sign_path[1]
        }
    }


def _clear_result_to_dict(deleted_files_info: DeletedFileInfo) -> dict[str, str]:
    """Преобразование информации об удаленном файле в словарь.

    :param deleted_files_info: информация об удаленном файле
    :return: информация об удаленном файле в виде словаря
    """
    return {
        'model': deleted_files_info.files_info.model.__name__,
        'field': deleted_files_info.files_info.field.name,
        'path': deleted_files_info.path
    }
