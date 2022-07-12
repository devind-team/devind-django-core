import os
from typing import TypedDict
from mimetypes import guess_type
from strawberry.types import Info
from strawberry.file_uploads.scalars import Upload
from strawberry_django_plus import gql
from strawberry_django_plus.permissions import IsAuthenticated
from django.core.mail import EmailMultiAlternatives
from devind_core.legacy import legacy_mutation


@gql.type
class SupportMutations:
    @legacy_mutation(directives=[IsAuthenticated()])
    def support_submit(self, info: Info, topic: str, text: str, files: list[Upload]) -> TypedDict('', {}):
        """Отправка письма поддержки"""
        user = info.context.request.user
        from_email: str = os.getenv('EMAIL_HOST_USER')
        mail: EmailMultiAlternatives = EmailMultiAlternatives(
            f'{topic}: {user.email}', text, from_email, [os.getenv('EMAIL_HOST_SUPPORT')]
        )
        for file in files:
            mail.attach(file.name, file.file.read(), guess_type(file.name)[0])
        return {}
