"""Файл содержащий валидацию пользователей."""
from devind_helpers.validator import Validator


class UserValidator(Validator):
    """Класс валидации пользователей."""

    username = 'required|min_length:2|max_length:30|unique:AUTH_USER_MODEL,username'
    email = 'required|email|unique:AUTH_USER_MODEL,email'
    last_name = 'required|min_length:2|max_length:30'
    first_name = 'required|min_length:2|max_length:30'
    sir_name = 'min_length:2|max_length:30'
    birthday = 'required|min_length:10|max_length:19'
    password = 'min_length:8'

    message = {
        'username': {
            'required': 'Поле "Имя пользователя" обязательное для заполнения',
            'min_length': 'Минимальная длина не менее 2 символа',
            'max_length': 'Максимальная длина не более 30 символа',
            'unique': 'Пользователь с таким логином существует'
        },
        'email': {
            'email': 'Поле должно быть действительным адресом для Email',
            'unique': 'Пользователь с таким email существует'
        },
        'last_name': {
            'required': 'Поле "Имя пользователя" обязательное для заполнения',
            'min_length': 'Минимальная длина не менее 2 символа',
            'max_length': 'Максимальная длина не более 30 символа'
        },
        'first_name': {
            'required': 'Поле "Имя пользователя" обязательное для заполнения',
            'min_length': 'Минимальная длина не менее 2 символа',
            'max_length': 'Максимальная длина не более 30 символа'
        },
        'sir_name': {
            'min_length': 'Минимальная длина не менее 2 символа',
            'max_length': 'Максимальная длина не более 30 символа'
        }
    }


class ProfileValidator(Validator):
    """Класс валидации пользователя."""

    name = 'required|min_length:2|max_length:512'
    code = 'required|min_length:2|max_length:30|unique:devind_core.Profile,core'
    parent_id = 'exist:devind_core.Profile,id'

    message = {
        'name': {
            'required': 'Поле "Название показателя" обязательное для заполнения',
            'min_length': 'Минимальная длина не менее 2 символа',
            'max_length': 'Максимальная длина не более 512 символа'
        },
        'code': {
            'required': 'Поле "Уникальный код" обязательное для заполнения',
            'min_length': 'Минимальная длина не менее 2 символа',
            'max_length': 'Максимальная длина не более 30 символа',
            'unique': 'Запись с таким кодом уже существует'
        },
        'parent_id': {
            'exist': 'Записи с таким идентификатором не существует'
        }
    }


class ProfileValueValidator(Validator):
    """Класс изменения значения профиля."""

    value = 'required'
    user_id = 'exist:AUTH_USER_MODEL,id'
    profile_id = 'exist:devind_core.Profile,id'

    message = {
        'value': {
            'required': 'Поле "Значение" обязательное для заполнения'
        },
        'user_id': {
            'exist': 'Пользователя не существует'
        },
        'profile_id': {
            'exist': 'Записи с таким идентификатором не существует'
        }
    }
