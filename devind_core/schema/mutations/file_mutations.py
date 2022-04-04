import os
from typing import List, Optional, Type

import graphene
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import models
from graphene_file_upload.scalars import Upload
from graphql import ResolveInfo

from devind_core.models import get_file_model
from devind_core.permissions import ChangeFile, DeleteFile
from devind_core.schema.types import FileType
from devind_helpers.decorators import permission_classes
from devind_helpers.orm_utils import get_object_or_404, get_object_or_none
from devind_helpers.permissions import IsAuthenticated
from devind_helpers.schema.mutations import BaseMutation
from devind_helpers.utils import from_gid_or_none

User: Type[models.Model] = get_user_model()
File: Type[models.Model] = get_file_model()


class AddFileMutation(BaseMutation):
    """Мутация для загрузки файлов"""
    class Input:
        user_id = graphene.ID(description='Идентификатор пользователя')
        files = graphene.List(graphene.NonNull(Upload), required=True, description='Загружаемые файлы')

    files = graphene.List(FileType, required=True, description='Загруженные файлы')

    @staticmethod
    @permission_classes((IsAuthenticated,))
    def mutate_and_get_payload(root, info: ResolveInfo, user_id: Optional[str], files: List[InMemoryUploadedFile]):
        user: Optional[User] = get_object_or_none(User, pk=from_gid_or_none(user_id)[1]) \
            if user_id \
            else info.context.user
        return AddFileMutation(
            files=reversed([File.objects.create(user=user, name=file.name, src=file) for file in files])
        )


class ChangeFileMutation(BaseMutation):
    """Мутация для изменения файла"""
    class Input:
        file_id = graphene.ID(required=True, description='Идентификатор файла')
        field = graphene.String(required=True, description='Поле файла')
        value = graphene.String(required=True, description='Значение поля файла')

    file = graphene.Field(FileType, description='Измененный файл')

    @staticmethod
    @permission_classes([IsAuthenticated, ChangeFile])
    def mutate_and_get_payload(root, info: ResolveInfo, file_id, field: str, value: str, *args, **kwargs):
        file: File = get_object_or_404(File, pk=from_gid_or_none(file_id)[1])
        info.context.check_object_permissions(info.context, file.user)
        if field == 'deleted':
            value: bool = value == 'true'
        setattr(file, field, value)
        file.save(update_fields=(field,))
        return ChangeFileMutation(file=file)


class DeleteFileMutation(BaseMutation):
    """Мутация для полного удаления файла"""
    class Input:
        file_id = graphene.ID(required=True, description='Идентификатор файла')

    id = graphene.ID(required=True, description='Идентификатор удаляемого файла')

    @staticmethod
    @permission_classes([IsAuthenticated, DeleteFile])
    def mutate_and_get_payload(root, info: ResolveInfo, file_id: str, *args, **kwargs):
        file: File = get_object_or_404(File, pk=from_gid_or_none(file_id)[1])
        if os.path.isfile(file.src.path):
            os.remove(file.src.path)
        file.delete()
        return DeleteFileMutation(id=file_id)


class FileMutations(graphene.ObjectType):
    add_file = AddFileMutation.Field(required=True)
    change_file = ChangeFileMutation.Field(required=True)
    delete_file = DeleteFileMutation.Field(required=True)
