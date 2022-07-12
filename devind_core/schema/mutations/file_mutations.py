import os
from typing import Type, TypedDict
from strawberry.types import Info
from strawberry_django_plus import gql
from django.contrib.auth import get_user_model
from django.db import models
from strawberry_django_plus.permissions import IsAuthenticated
from strawberry.file_uploads.scalars import Upload
from devind_core.permissions import self_or_has_perm
from devind_core.models import get_file_model

from devind_core.schema.types import FileType, UserType
from devind_core.legacy import legacy_mutation

User: Type[models.Model] = get_user_model()
File: Type[models.Model] = get_file_model()


@gql.type
class FileMutations:

    @legacy_mutation(directives=[IsAuthenticated()])
    def add_file(self, info: Info, user_id: gql.ID, files: list[Upload]) -> TypedDict('', {'files': list[FileType] | None}):
        """Мутация для загрузки файлов"""
        user = UserType.resolve_node(user_id, required=True)
        self_or_has_perm(info, user, 'devind_core.change_file')
        return {'files': list(reversed([File.objects.create(user=user, name=file.name, src=file) for file in files]))}

    @legacy_mutation(directives=[IsAuthenticated()])
    def change_file(self, info: Info, file_id: gql.ID, field: str, value: str) -> TypedDict('', {'file': FileType | None}):
        """Мутация для изменения файла"""
        file: File = FileType.resolve_node(file_id)
        self_or_has_perm(info, file.user, 'devind_core.change_file')
        if field == 'deleted':
            value: bool = value == 'true'
        setattr(file, field, value)
        file.save(update_fields=(field,))
        return {'file': file}

    @legacy_mutation(directives=[IsAuthenticated()])
    def delete_file(self, info: Info, file_id: gql.ID) -> TypedDict('', {'id': gql.ID | None}):
        """Мутация для полного удаления файла"""
        file: File = FileType.resolve_node(file_id)
        self_or_has_perm(info, file.user, 'devind_core.delete_file')
        if os.path.isfile(file.src.path):
            os.remove(file.src.path)
        file.delete()
        return {'id': file_id}
