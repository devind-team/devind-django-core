"""Файл содержащий валидацию пользователей."""
from django.contrib.auth import get_user_model
from django.forms import ModelForm, CharField, EmailField
from devind_core.models import ProfileValue, Profile


class UserValidator(ModelForm):
    """Класс валидации пользователей."""
    username = CharField(min_length=2, max_length=30)
    email = EmailField(required=True)
    last_name = CharField(required=True, min_length=2, max_length=30)
    first_name = CharField(required=True, min_length=2, max_length=30)
    sir_name = CharField(min_length=2, max_length=30)
    password = CharField(min_length=8)

    class Meta:
        model = get_user_model()
        fields = ['username', 'email', 'last_name', 'first_name', 'sir_name', 'birthday']
    # todo локализация
    # message = {
    #     'username': {
    #         'required': 'Поле "Имя пользователя" обязательное для заполнения',
    #         'min_length': 'Минимальная длина не менее 2 символа',
    #         'max_length': 'Максимальная длина не более 30 символа',
    #         'unique': 'Пользователь с таким логином существует'
    #     },
    #     'email': {
    #         'email': 'Поле должно быть действительным адресом для Email',
    #         'unique': 'Пользователь с таким email существует'
    #     },
    #     'last_name': {
    #         'required': 'Поле "Имя пользователя" обязательное для заполнения',
    #         'min_length': 'Минимальная длина не менее 2 символа',
    #         'max_length': 'Максимальная длина не более 30 символа'
    #     },
    #     'first_name': {
    #         'required': 'Поле "Имя пользователя" обязательное для заполнения',
    #         'min_length': 'Минимальная длина не менее 2 символа',
    #         'max_length': 'Максимальная длина не более 30 символа'
    #     },
    #     'sir_name': {
    #         'min_length': 'Минимальная длина не менее 2 символа',
    #         'max_length': 'Максимальная длина не более 30 символа'
    #     }
    # }


class ProfileValidator(ModelForm):
    """Класс валидации пользователя."""
    name = CharField(min_length=2, max_length=512)
    code = CharField(min_length=2, max_length=30)

    class Meta:
        model = Profile
        fields = ['name', 'code', 'parent']
    # todo локализация
    #
    # message = {
    #     'name': {
    #         'required': 'Поле "Название показателя" обязательное для заполнения',
    #         'min_length': 'Минимальная длина не менее 2 символа',
    #         'max_length': 'Максимальная длина не более 512 символа'
    #     },
    #     'code': {
    #         'required': 'Поле "Уникальный код" обязательное для заполнения',
    #         'min_length': 'Минимальная длина не менее 2 символа',
    #         'max_length': 'Максимальная длина не более 30 символа',
    #         'unique': 'Запись с таким кодом уже существует'
    #     },
    #     'parent_id': {
    #         'exist': 'Записи с таким идентификатором не существует'
    #     }
    # }


class ProfileValueValidator(ModelForm):
    """Класс изменения значения профиля."""

    class Meta:
        model = ProfileValue
        fields = ['value', 'user', 'profile']
    # value = 'required'
    # user_id = 'exist:AUTH_USER_MODEL,id'
    # profile_id = 'exist:devind_core.Profile,id'
    #
    # message = {
    #     'value': {
    #         'required': 'Поле "Значение" обязательное для заполнения'
    #     },
    #     'user_id': {
    #         'exist': 'Пользователя не существует'
    #     },
    #     'profile_id': {
    #         'exist': 'Записи с таким идентификатором не существует'
    #     }
    # }
