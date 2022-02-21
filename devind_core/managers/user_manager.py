"""Модуль переопределения стандарного пользовательского менеджера."""

from django.contrib.auth.base_user import BaseUserManager


class UserManager(BaseUserManager):
    """Класс переопределения стандартного пользовательского менеджера."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """Создание и сохранение пользователя с email и password

        :param email: Email
        :param password: Пароль
        :param extra_fields: Дополнительные поля
        :return: Возвращает или сохраняет нового пользователя
        """
        if not email:
            raise ValueError('Значение Email должно быть заполнено')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        """Функция создания пользователей."""
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        """Функция создания суперюзеров."""
        extra_fields.setdefault('is_superuser', True)
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self._create_user(email, password, **extra_fields)
