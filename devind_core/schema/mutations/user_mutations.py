import json
import re
import datetime
from random import randrange
from typing import List, Optional, Type, TypedDict

from django.core.exceptions import ValidationError
from strawberry.file_uploads import Upload
from strawberry_django_plus.permissions import IsAuthenticated, HasPerm
from strawberry_django_plus import gql
from strawberry.types import Info
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import FieldDoesNotExist

from django.db import models
from django.db import transaction
from django.template.loader import render_to_string
from django.utils.timezone import make_aware
from oauth2_provider.models import AccessToken
from oauth2_provider.views.base import TokenView

from devind_core.models import get_file_model, \
    get_profile_model, \
    get_profile_value_model, \
    get_reset_password_model, \
    get_session_model

from devind_core.schema.types import GroupType, UserType, SessionType
from devind_core.permissions.group_permission import ChangeGroup
from devind_helpers.schema.types import TableType
# from devind_helpers.decorators import permission_classes
from devind_helpers.import_from_file import ImportFromFile
from devind_helpers.orm_utils import get_object_or_none, get_object_or_404
# from devind_helpers.permissions import IsAuthenticated, IsGuest
# from devind_helpers.redis_client import redis
from devind_helpers.request import Request
from devind_helpers.utils import convert_str_to_int
from devind_core.permissions import self_or_can_change
from devind_core.legacy import legacy_mutation

try:
    from devind_notifications.models import Mailing
except ModuleNotFoundError:
    """Если модуль уведомлений не установлен"""
    Mailing = False

File: Type[models.Model] = get_file_model()
Profile: Type[models.Model] = get_profile_model()
ProfileValue: Type[models.Model] = get_profile_value_model()
ResetPassword: Type[models.Model] = get_reset_password_model()
Session: Type[models.Model] = get_session_model()
User: Type[models.Model] = get_user_model()


@gql.type
class UserMutations:
    @legacy_mutation
    def get_token(self, info: Info, client_id: str, client_secret: str, grant_type: str, username: str,
                  password: str) -> TypedDict('', {'access_token': str | None, 'expires_in': int | None,
                                                   'token_type': str | None, 'scope': str | None,
                                                   'refresh_token': str | None, 'user': UserType | None}):
        request = Request(
            '/graphql',
            body=json.dumps({
                'client_id': client_id,
                'client_secret': client_secret,
                'grant_type': grant_type,
                'username': username,
                'password': password}).encode('utf-8'),
            headers=info.context.request.headers,
            meta=info.context.request.META
        )
        url, header, body, status = TokenView().create_token_response(request)
        if status != 200:
            raise ValidationError({'username': 'Неверный логин или пароль'})
        body_dict = json.loads(body)
        ip: str = info.context.request.META['REMOTE_ADDR']
        user_agent: str = info.context.request.META['HTTP_USER_AGENT']
        access_token: AccessToken = AccessToken.objects.get(token=body_dict['access_token'])
        Session.objects.create(
            ip=ip,
            user_agent=user_agent,
            access_token=access_token,
            user=access_token.user
        )

        return {**body_dict, 'user': access_token.user}

    @legacy_mutation
    def register(self, username: str, email: str, last_name: str, first_name: str, sir_name: str,
                 birthday: datetime.date, password: str, agreement: bool) -> TypedDict('', {}):  # todo: isGuest
        agreement = make_aware(datetime.datetime.now()) if agreement else None
        user = User.objects.create(username=username, email=email, last_name=last_name, first_name=first_name,
                                   sir_name=sir_name, birthday=birthday, agreement=agreement)
        user.set_password(password)
        user.save(update_fields=('password',))
        return {}

    @legacy_mutation(directives=[IsAuthenticated()])
    def logout(self, session_id: gql.ID, info: Info) -> TypedDict('', {}):
        session: Session | None = SessionType.resolve_node(session_id)
        self_or_can_change(info, session.access_token.user)
        session.user.logout(session)
        return {}

    @legacy_mutation(directives=[IsAuthenticated(), HasPerm('.add_user')])
    def upload_users(self, info: Info, groups_id: List[int], file: Upload) -> TypedDict('', {
        'users': list[UserType] | None}):  # todo union tabletype
        f: File = File.objects.create(name=file.name, src=file, user=info.context.user, deleted=True)
        iff: ImportFromFile = ImportFromFile(User, f.src.path)  # todo validator
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
        success, errors = (True, [])  # todo iff.validate()

        if success:
            users: List[User] = iff.run()
            groups: List[Group] = Group.objects.filter(pk__in=groups_id).all()

            for i, user in enumerate(users):
                ProfileValue.objects.bulk_create(
                    [ProfileValue(user_id=user.id, **value) for value in profile_values[i]])
                user.groups.add(*groups)
            return {'users': users}  # todo
        else:
            pass  # todo
        # return UploadUsersMutation(
        #    success=False,
        #    errors=[
        #        RowFieldErrorType(row=row, errors=ErrorFieldType.from_validator(error)) for row, error in errors
        #    ],
        #    table=TableType.from_iff(iff)
        # )

    @legacy_mutation(directives=[IsAuthenticated(), HasPerm('auth.change_group')])
    def change_user_groups(self, user_id: gql.ID, groups_id: List[int]) -> TypedDict('', {
        'groups': list[GroupType] | None}):
        user: User | None = UserType.resolve_node(user_id)
        if user is None:
            raise ValidationError({'user': 'Пользователь не найден'})
        groups = Group.objects.filter(pk__in=groups_id).all()
        user.groups.set(groups)
        return {'groups': groups}

    @legacy_mutation(directives=[IsAuthenticated()])
    def delete_sessions(self, dummy: int | None, info: Info) -> TypedDict('', {}):
        me: User = info.context.request.user
        current_session: Session = info.context.request.session
        for session in Session.objects.filter(access_token__user=me).exclude(pk=current_session.pk).all():
            me.logout(session)
        return {}

    @legacy_mutation(directives=[IsAuthenticated()])
    def change_avatar(self, info: Info, user_id: gql.ID, file: Upload) -> TypedDict('', {'avatar': str | None}):
        user: User | None = UserType.resolve_node(user_id)
        self_or_can_change(info, user)
        user.avatar.delete(save=False)
        user.avatar = file
        user.save(update_fields=('avatar',))
        return {'avatar': user.avatar}

    @legacy_mutation(directives=[IsAuthenticated()])
    def change_password(self, info: Info, password: str, password_new: str) -> TypedDict('', {}):
        user: User = info.context.request.user
        self_or_can_change(info, user)
        if not user.check_password(password):
            raise ValidationError({'password': 'Введенный пароль неверный'})
        else:
            user.set_password(password_new)
            user.save(update_fields=('password',))
            Mailing and Mailing.objects.create(
                address=user.email,
                header='Изменение пароля',
                text=render_to_string('mail/auth/changed_password.html', {'user': user}, request=info.context),
                user=user,
            ).dispatch(True)
        return {}

    @legacy_mutation(directives=[IsAuthenticated()])
    def change_user_props(self, info: Info, user_id: gql.ID, email: str, first_name: str, last_name: str,
                          sir_name: str, birthday: datetime.date) -> TypedDict('', {'user': UserType | None}):
        user: User = UserType.resolve_node(user_id, required=True)
        self_or_can_change(info, user)
        user.email = email
        user.first_name = first_name
        user.last_name = last_name
        user.sir_name = sir_name
        user.birthday = birthday
        user.save(update_fields=('email', 'first_name', 'last_name', 'sir_name', 'birthday',))
        return {'user': user}

    @legacy_mutation
    def restore_password(self, info: Info, token: str, password: str) -> TypedDict('', {}):
        reset_password: ResetPassword = get_object_or_none(ResetPassword, token=token, password__isnull=True)
        if reset_password is None:
            raise ValidationError({'token': 'Токен не найден'})
        if len(password) < 8:
            raise ValidationError({'password': 'Длина пароля меньше 4 символов'})
        reset_password.password = password
        reset_password.user.set_password(password)
        with transaction.atomic():
            reset_password.user.save(update_fields=('password',))
            reset_password.save(update_fields=('password',))
        Mailing and Mailing.objects.create(
            address=reset_password.user.email,
            header='Изменение пароля',
            text=render_to_string(
                'mail/auth/changed_password.html',
                {'user': reset_password.user},
                request=info.context
            ),
            user=reset_password.user,
        ).dispatch(True)
        return {}

    @legacy_mutation
    def recovery_password(self, info: Info, email: str) -> TypedDict('', {}):
        error_email = ValidationError({'email': 'Указанный email не является действительным'})

        if not re.findall(r'^[\w\.-]+@[\w\.-]+(\.[\w]+)+$', email):
            raise error_email
        user: User = get_object_or_none(User, email=email)
        if user is None:
            raise error_email
        token: str = user.get_token()
        Mailing and Mailing.objects.create(
            address=email,
            header='Восстановление пароля',
            text=render_to_string(
                'mail/auth/recovery_password.html',
                {'user': user, 'token': token},
                request=info.context
            ),
            user=user,
        ).dispatch()
        return {}

    @legacy_mutation(directives=[IsAuthenticated()])
    def request_code(self, info: Info, email: str) -> TypedDict('', {}):
        if not re.findall(r'^[\w\.-]+@[\w\.-]+(\.[\w]+)+$', email):
            raise ValidationError({'email': 'Указанный email не является действительным'})

        user: User = info.context.request.user

        code: int = randrange(10 ** 5, 10 ** 6)
        # redis.set(f'user.{user.pk}.request_code', code, ex=60)  # Время жизни 60 секунд todo
        Mailing and Mailing.objects.create(
            address=email,
            header='Верификация аккаунта',
            text=render_to_string('mail/auth/request_code.html', {'user': user, 'code': code}, request=info.context),
            user=user,
        ).dispatch()
        return {}

    @legacy_mutation(directives=[IsAuthenticated()])
    def confirm_email(self, info: Info, email: str, code: str) -> TypedDict('', {'user': UserType | None}):
        user: User = info.context.request.user
        code: Optional[int] = convert_str_to_int(code)
        if not code:
            raise ValidationError({'code': 'Код состоит из цифр'})
        # saved_code = redis.get(f'user.{user.pk}.request_code') todo
        # if saved_code is None or code != int(saved_code):
        #     return ConfirmEmailMutation(
        #         success=False,
        #         errors=[ErrorFieldType('code', [f'Указанный код не является действительным'])]
        #     )
        if not re.findall(r'^[\w\.-]+@[\w\.-]+(\.[\w]+)+$', email):
            raise ValidationError({'code': f'Указанный email не является действительным: {email}'})
        user.email, user.agreement = email, make_aware(datetime.now())
        user.save(update_fields=('email', 'agreement',))
        Mailing and Mailing.objects.create(
            address=email,
            header='Верификация аккаунта',
            text=render_to_string('mail/auth/confirm_email.html', {'user': user}, request=info.context),
            user=user,
        ).dispatch(True)
        return {'user': user}

# class UploadUsersMutation(graphene.relay.ClientIDMutation):
#     """Мутация для загрузки пользователей из файла excel | csv."""
#
#     class Input:
#         groups_id = graphene.List(graphene.Int, description='Для загрузки пользователей')
#         file = Upload(required=True, description='Источник данных, файл xlsx или csv')
#
# success = graphene.Boolean(required=True, description='Успех мутации')
# errors = graphene.List(RowFieldErrorType, required=True, description='Ошибки валидации')
# table = graphene.Field(TableType, description='Валидируемый документ')
# users = graphene.List(UserType, description='Загруженные пользователи')
#
# @staticmethod
# @permission_classes([IsAuthenticated, AddUser])
# def mutate_and_get_payload(root, info: ResolveInfo, groups_id: List[int], file: InMemoryUploadedFile):
#     f: File = File.objects.create(name=file.name, src=file, user=info.context.user, deleted=True)
#     iff: ImportFromFile = ImportFromFile(User, f.src.path, UserValidator)
#     profiles = Profile.objects.filter(parent__isnull=False).values('id', 'code')
#     profile_values = []
#
#     for user in iff.items:
#         pv = []
#         for k, v in user['profile'].items() if 'profile' in user else ():
#             profile_id = next((x['id'] for x in profiles if x['code'] == k), None)
#             if v is None:
#                 continue
#             if profile_id is None:
#                 raise FieldDoesNotExist(f'Неизвестный столбец {k}')
#             pv.append({'value': v, 'profile_id': profile_id})
#         profile_values.append(pv)
#         user.pop('profile')
#     success, errors = iff.validate()
#
#     if success:
#         users: List[User] = iff.run()
#         groups: List[Group] = Group.objects.filter(pk__in=groups_id).all()
#
#         for i, user in enumerate(users):
#             ProfileValue.objects.bulk_create([ProfileValue(user_id=user.id, **value) for value in profile_values[i]])
#             user.groups.add(*groups)
#         return UploadUsersMutation(success=True, errors=[], users=users)
#     else:
#         return UploadUsersMutation(
#             success=False,
#             errors=[
#                 RowFieldErrorType(row=row, errors=ErrorFieldType.from_validator(error)) for row, error in errors
#             ],
#             table=TableType.from_iff(iff)
#         )
