from channels.auth import AuthMiddlewareStack
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from oauth2_provider.models import AccessToken


class TokenAuthMiddleware:
    """Токен авторизация дл Django Channels 2."""

    token_name: str = 'apollo-token'

    def __init__(self, app):
        self.app = app

    @database_sync_to_async
    def get_user_by_token(self, token):
        """Получение пользователя с помощью токена."""
        return AccessToken.objects.get(token=token).user

    async def get_user(self, token):
        """Попытка выгрузки пользователя."""
        try:
            return await self.get_user_by_token(token)
        except AccessToken.DoesNotExist:
            return AnonymousUser()

    async def __call__(self, scope, receive, send):
        """Непосредственная обработка запроса."""
        headers = dict(scope['headers'])
        if b'cookie' in headers:
            token_str = ''
            for cookie in headers[b'cookie'].decode().split():
                if cookie.startswith(f'{self.token_name}='):
                    token_str = cookie
            token = token_str.split('=')[-1].replace(';', '')
            scope['user'] = await self.get_user(token)
        return await self.app(scope, receive, send)


def TokenAuthMiddlewareStack(inner):
    """Функция вызова прослойки для Django Channels 2."""
    return TokenAuthMiddleware(AuthMiddlewareStack(inner))
