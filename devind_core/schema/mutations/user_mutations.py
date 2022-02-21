import json
import re
from datetime import datetime
from random import randrange
from typing import List, Optional, Type

import graphene
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import FieldDoesNotExist
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import models
from django.db import transaction
from django.template.loader import render_to_string
from django.utils.timezone import make_aware
from graphene_file_upload.scalars import Upload
from graphql import ResolveInfo
from graphql_relay import from_global_id
from oauth2_provider.models import AccessToken
from oauth2_provider.views.base import TokenView

from apps.core.schema import UserType
from devind_core.models import get_file_model, \
    get_profile_model, \
    get_profile_value_model, \
    get_reset_password_model, \
    get_session_model
from devind_core.permissions import AddUser, \
    ChangeUser, \
    DeleteUser, \
    ChangeGroup
from devind_core.schema.types import GroupType
from devind_helpers.schema.types import ErrorFieldType, RowFieldErrorType, TableType
from devind_core.validators import UserValidator
from devind_helpers.decorators import permission_classes
from devind_helpers.import_from_file import ImportFromFile
from devind_helpers.orm_utils import get_object_or_none, get_object_or_404
from devind_helpers.permissions import IsAuthenticated, IsGuest
from devind_helpers.redis_client import redis
from devind_helpers.request import Request
from devind_helpers.schema.mutations import BaseMutation
from devind_helpers.utils import convert_str_to_int
from devind_notifications.models import Mailing

File: Type[models.Model] = get_file_model()
Profile: Type[models.Model] = get_profile_model()
ProfileValue: Type[models.Model] = get_profile_value_model()
ResetPassword: Type[models.Model] = get_reset_password_model()
Session: Type[models.Model] = get_session_model()
User: Type[models.Model] = get_user_model()


class GetTokenMutation(BaseMutation):
    """Мутация для получения токена авторизации."""

    class Input:
        """Входные данные."""
        client_id = graphene.String(description='Открытый идентификатор приложения')
        client_secret = graphene.String(description='Секретный идентификатор приложения')
        grant_type = graphene.String(description='Тип авторизации')
        username = graphene.String(description='Имя пользователя')
        password = graphene.String(description='Пароль')

    access_token = graphene.String(description='Токен доступа')
    expires_in = graphene.Int(description='Время жизни токена')
    token_type = graphene.String(description='Тип токена')
    scope = graphene.String(description='Разрешения')
    refresh_token = graphene.String(description='Токен обновления')
    user = graphene.Field(UserType, description='Авторизованный пользователь')

    @staticmethod
    def mutate_and_get_payload(root, info: ResolveInfo, **kwargs):
        request = Request(
            '/graphql',
            body=json.dumps(kwargs).encode('utf-8'),
            headers=info.context.headers,
            meta=info.context.META
        )
        url, header, body, status = TokenView().create_token_response(request)
        if status != 200:
            return GetTokenMutation(success=False, errors=[ErrorFieldType('login', ['Неверный логин или пароль'])])
        body_dict = json.loads(body)
        ip: str = info.context.META['REMOTE_ADDR']
        user_agent: str = info.context.META['HTTP_USER_AGENT']
        access_token: AccessToken = AccessToken.objects.get(token=body_dict['access_token'])
        Session.objects.create(
            ip=ip,
            user_agent=user_agent,
            access_token=access_token,
            user=access_token.user
        )
        return GetTokenMutation(**{**body_dict, 'user': access_token.user})


class RegisterMutation(BaseMutation):
    """Мутация регистрации новых пользователей."""
    class Input:
        username = graphene.String(required=True, description='Логин')
        email = graphene.String(required=True, description='Email')
        last_name = graphene.String(required=True, description='Фамилия')
        first_name = graphene.String(required=True, description='Имя')
        sir_name = graphene.String(description='Отчество')
        birthday = graphene.Date(required=True, description='Дата рождения')
        password = graphene.String(required=True, description='Пароль')
        agreement = graphene.Boolean(required=True, description='Согласие на обработку персональных данных')

    @staticmethod
    @permission_classes([IsGuest])
    def mutate_and_get_payload(root, info: ResolveInfo, *args, **kwargs):
        validator = UserValidator(kwargs)
        if validator.validate():
            kwargs['agreement'] = make_aware(datetime.now()) if kwargs['agreement'] else None
            user = User.objects.create(**kwargs)
            user.set_password(kwargs['password'])
            user.save(update_fields=('password',))
        else:
            return RegisterMutation(success=False, errors=ErrorFieldType.from_validator(validator.get_message()))
        return RegisterMutation()


class LogoutMutation(BaseMutation):
    """Мутация выхода"""
    class Input:
        session_id = graphene.ID(required=True, description='Идентификатор сессии')

    @staticmethod
    @permission_classes([IsAuthenticated, ChangeUser, DeleteUser])
    def mutate_and_get_payload(root, info: ResolveInfo, session_id: str):
        _, pk = from_global_id(session_id)
        session: Optional[Session] = get_object_or_none(Session, pk=pk)
        info.context.check_object_permissions(info.context, session.access_token.user)
        session.user.logout(session)
        return LogoutMutation()


class UploadUsersMutation(graphene.relay.ClientIDMutation):
    """Мутация для загрузки пользователей из файла excel | csv."""

    class Input:
        groups_id = graphene.List(graphene.Int, description='Для загрузки пользователей')
        file = Upload(required=True, description='Источник данных, файл xlsx или csv')

    success = graphene.Boolean(required=True, description='Успех мутации')
    errors = graphene.List(RowFieldErrorType, required=True, description='Ошибки валидации')
    table = graphene.Field(TableType, description='Валидируемый документ')
    users = graphene.List(UserType, description='Загруженные пользователи')

    @staticmethod
    @permission_classes([IsAuthenticated, AddUser])
    def mutate_and_get_payload(root, info: ResolveInfo, groups_id: List[int], file: InMemoryUploadedFile):
        f: File = File.objects.create(name=file.name, src=file, user=info.context.user, deleted=True)
        iff: ImportFromFile = ImportFromFile(User, f.src.path, UserValidator)
        profiles = Profile.objects.filter(parent__isnull=False).values('id', 'code')
        profile_values = []

        for user in iff.items:
            pv = []
            for k, v in user['profile'].items() if 'profile' in user else ():
                profile_id = next((x['id'] for x in profiles if x['code'] == k), None)
                if v is None:
                    continue
                if profile_id is None:
                    raise FieldDoesNotExist(f'Неизвестный столбец {k}')
                pv.append({'value': v, 'profile_id': profile_id})
            profile_values.append(pv)
            user.pop('profile')
        success, errors = iff.validate()

        if success:
            users: List[User] = iff.run()
            groups: List[Group] = Group.objects.filter(pk__in=groups_id).all()

            for i, user in enumerate(users):
                ProfileValue.objects.bulk_create([ProfileValue(user_id=user.id, **value) for value in profile_values[i]])
                user.groups.add(*groups)
            return UploadUsersMutation(success=True, errors=[], users=users)
        else:
            return UploadUsersMutation(
                success=False,
                errors=[
                    RowFieldErrorType(row=row, errors=ErrorFieldType.from_validator(error)) for row, error in errors
                ],
                table=TableType.from_iff(iff)
            )


class ChangeUserGroupsMutation(BaseMutation):
    """Мутация для изменения групп конкретного пользователя."""
    class Input:
        user_id: graphene.ID = graphene.ID(required=True, description='Идентификатор пользователя')
        groups_id: graphene.List = graphene.List(graphene.Int, required=True, description='Идентификатор групп')

    groups = graphene.List(GroupType, description='Новые группы')

    @staticmethod
    @permission_classes([IsAuthenticated, ChangeUser, ChangeGroup])
    def mutate_and_get_payload(root, info: ResolveInfo, user_id: str, groups_id: List[int]):
        user_id = from_global_id(user_id)[1]
        user: Optional[User] = get_object_or_none(User, pk=user_id)
        if user is None:
            return ChangeUserGroupsMutation(success=False, errors=[ErrorFieldType('user', ['Пользователь не найден'])])
        groups: List[Group] = Group.objects.filter(pk__in=groups_id).all()
        user.groups.set(groups)
        return ChangeUserGroupsMutation(groups=groups)


class DeleteSessionsMutation(BaseMutation):
    """Мутация для удаления всех сессий кроме текущей."""
    class Input:
        pass

    @staticmethod
    @permission_classes([IsAuthenticated])
    def mutate_and_get_payload(root, info: ResolveInfo):
        me: User = info.context.user
        current_session: Session = info.context.session
        for session in Session.objects.filter(access_token__user=me).exclude(pk=current_session.pk).all():
            me.logout(session)
        return DeleteSessionsMutation()


class ChangeAvatarMutation(BaseMutation):
    """Мутация для изменения аватара пользователя."""
    class Input:
        user_id = graphene.ID(required=True, description='Идентификатор пользователя')
        file = Upload(required=True, description='Загружаемый файл аватара')

    avatar = graphene.String(required=True, description='Загруженный аватар')

    @staticmethod
    @permission_classes([IsAuthenticated, ChangeUser])
    def mutate_and_get_payload(root, info: ResolveInfo, user_id: str, file: InMemoryUploadedFile):
        user: Optional[User] = get_object_or_none(User, pk=from_global_id(user_id)[1])
        info.context.check_object_permissions(info.context, user)
        user.avatar.delete(save=False)
        user.avatar = file
        user.save(update_fields=('avatar',))
        return ChangeAvatarMutation(avatar=user.avatar)


class ChangePasswordMutation(BaseMutation):
    """Мутация для изменения пароля пользователя."""

    class Input:
        password: graphene.String = graphene.String(required=True, description='Старый пароль')
        password_new: graphene.String = graphene.String(required=True, description='Новый пароль')

    @staticmethod
    @permission_classes([IsAuthenticated, ChangeUser, DeleteUser])
    def mutate_and_get_payload(root, info: ResolveInfo, password: str, password_new: str):
        user: User = info.context.user
        info.context.check_object_permissions(info.context, user)
        if not user.check_password(password):
            return ChangePasswordMutation(success=False, errors=[ErrorFieldType('password', ['Введенный пароль неверный'])])
        else:
            user.set_password(password_new)
            user.save(update_fields=('password',))
            Mailing.objects.create(
                address=user.email,
                header='Изменение пароля',
                text=render_to_string('mail/auth/changed_password.html', {'user': user}, request=info.context),
                user=user,
            ).dispatch(True)
        return ChangePasswordMutation()


class ChangeUserPropsMutation(BaseMutation):
    """Мутация для изменения полей пользователя."""
    class Input:
        user_id = graphene.ID(required=True, description='Идентификатор пользователя')
        email = graphene.String(required=True, description='Email')
        first_name = graphene.String(required=True, description='Имя')
        last_name = graphene.String(required=True, description='Фамилия')
        sir_name = graphene.String(required=True, description='Отчество')
        birthday = graphene.Date(required=True, description='Дата рождения')

    user = graphene.Field(UserType, required=True, description='Измененный пользователь')

    @staticmethod
    @permission_classes([IsAuthenticated, ChangeUser])
    def mutate_and_get_payload(root, info: ResolveInfo, **kwargs):
        _, pk = from_global_id(kwargs['user_id'])
        user: User = get_object_or_404(User, pk=pk)
        info.context.check_object_permissions(info.context, user)
        user.email = kwargs['email']
        user.first_name = kwargs['first_name']
        user.last_name = kwargs['last_name']
        user.sir_name = kwargs['sir_name']
        user.birthday = kwargs['birthday']
        user.save(update_fields=('email', 'first_name', 'last_name', 'sir_name', 'birthday',))
        return ChangeUserPropsMutation(user=user)


class RestorePasswordMutation(BaseMutation):
    """Мутация для сброса пароля пользователя."""

    class Input:
        token = graphene.String(required=True, description='Токен')
        password = graphene.String(required=True, description='Пароль')

    @staticmethod
    def mutate_and_get_payload(root, info: ResolveInfo, token: str, password: str):
        reset_password: ResetPassword = get_object_or_none(ResetPassword, token=token, password__isnull=True)
        if reset_password is None:
            return RestorePasswordMutation(success=False, errors=[ErrorFieldType('token', ['Токен не найден'])])
        if len(password) < 8:
            return RestorePasswordMutation(success=False, errors=[ErrorFieldType('password', ['Длина пароля меньше 4 символов'])])
        reset_password.password = password
        reset_password.user.set_password(password)
        with transaction.atomic():
            reset_password.user.save(update_fields=('password',))
            reset_password.save(update_fields=('password',))
        Mailing.objects.create(
            address=reset_password.user.email,
            header='Изменение пароля',
            text=render_to_string(
                'mail/auth/changed_password.html',
                {'user': reset_password.user},
                request=info.context
            ),
            user=reset_password.user,
        ).dispatch(True)
        return RestorePasswordMutation()


class RecoveryPasswordMutation(BaseMutation):
    """Мутация для сброса пароля пользователя."""

    class Input:
        email = graphene.String(required=True, description='Email адрес')

    @staticmethod
    def mutate_and_get_payload(root, info: ResolveInfo, email: str):
        error_email = RecoveryPasswordMutation(
            success=False,
            errors=[ErrorFieldType('email', [f'Указанный email не является действительным'])]
        )

        if not re.findall(r'^[\w\.-]+@[\w\.-]+(\.[\w]+)+$', email):
            return error_email
        user: User = get_object_or_none(User, email=email)
        if user is None:
            return error_email
        token: str = user.get_token()
        Mailing.objects.create(
            address=email,
            header='Восстановление пароля',
            text=render_to_string(
                'mail/auth/recovery_password.html',
                {'user': user, 'token': token},
                request=info.context
            ),
            user=user,
        ).dispatch()
        return RecoveryPasswordMutation()


class RequestCodeMutation(BaseMutation):
    """Отправка email с кодом на электронную почту."""
    class Input:
        email = graphene.String(required=True, description='Email адрес')

    @staticmethod
    @permission_classes([IsAuthenticated])
    def mutate_and_get_payload(root, info: ResolveInfo, email: str, *args, **kwargs):

        if not re.findall(r'^[\w\.-]+@[\w\.-]+(\.[\w]+)+$', email):
            return RequestCodeMutation(
                success=False,
                errors=[ErrorFieldType('email', [f'Указанный email не является действительным'])]
            )

        user: User = info.context.user

        code: int = randrange(10 ** 5, 10 ** 6)
        redis.set(f'user.{user.pk}.request_code', code, ex=60)   # Время жизни 60 секунд
        Mailing.objects.create(
            address=email,
            header='Верификация аккаунта',
            text=render_to_string('mail/auth/request_code.html', {'user': user, 'code': code}, request=info.context),
            user=user,
        ).dispatch()
        return RequestCodeMutation()


class ConfirmEmailMutation(BaseMutation):
    """Подтверждение кода."""
    class Input:
        email = graphene.String(required=True, description='Email адрес')
        code = graphene.String(required=True, description='Код, полученный по Email')

    user = graphene.Field(UserType, description='Пользователь')

    @staticmethod
    @permission_classes([IsAuthenticated])
    def mutate_and_get_payload(root, info: ResolveInfo, email: str, code: str):
        user: User = info.context.user
        code: Optional[int] = convert_str_to_int(code)
        if not code:
            return ConfirmEmailMutation(
                success=False,
                errors=[ErrorFieldType('code', [f'Код состоит из цифр'])]
            )
        saved_code = redis.get(f'user.{user.pk}.request_code')
        if saved_code is None or code != int(saved_code):
            return ConfirmEmailMutation(
                success=False,
                errors=[ErrorFieldType('code', [f'Указанный код не является действительным'])]
            )
        if not re.findall(r'^[\w\.-]+@[\w\.-]+(\.[\w]+)+$', email):
            return ConfirmEmailMutation(
                success=False,
                errors=[ErrorFieldType('code', [f'Указанный email не является действительным: {email}'])]
            )
        user.email, user.agreement = email, make_aware(datetime.now())
        user.save(update_fields=('email', 'agreement',))
        Mailing.objects.create(
            address=email,
            header='Верификация аккаунта',
            text=render_to_string('mail/auth/confirm_email.html', {'user': user}, request=info.context),
            user=user,
        ).dispatch(True)
        return ConfirmEmailMutation(user=user)


class UserMutations(graphene.ObjectType):
    upload_users = UploadUsersMutation.Field(required=True)
    change_avatar = ChangeAvatarMutation.Field(required=True)
    change_password = ChangePasswordMutation.Field(required=True)
    change_user_props = ChangeUserPropsMutation.Field(required=True)
    delete_sessions = DeleteSessionsMutation.Field(required=True)
    register = RegisterMutation.Field(required=True)
    get_token = GetTokenMutation.Field(required=True)
    logout = LogoutMutation.Field(required=True)
    recovery_password = RecoveryPasswordMutation.Field(required=True)
    restore_password = RestorePasswordMutation.Field(required=True)
    change_user_groups = ChangeUserGroupsMutation.Field(required=True)
    request_code = RequestCodeMutation.Field(required=True)
    confirm_email = ConfirmEmailMutation.Field(required=True)
