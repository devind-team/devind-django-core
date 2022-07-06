import os
from mimetypes import guess_type
from strawberry.types import Info
from strawberry.file_uploads.scalars import Upload
from strawberry_django_plus import gql
from strawberry_django_plus.permissions import IsAuthenticated
from django.core.mail import EmailMultiAlternatives


@gql.input
class SupportSubmitInput:
    topic: str
    text: str
    files: list[Upload]


@gql.type
class SupportMutations:
    @gql.mutation(directives=[IsAuthenticated()])
    def support_submit(self, info: Info, input: SupportSubmitInput) -> None:
        """Отправка письма поддержки"""
        user = info.context.request.user
        from_email: str = os.getenv('EMAIL_HOST_USER')
        mail: EmailMultiAlternatives = EmailMultiAlternatives(
            f'{input.topic}: {user.email}', input.text, from_email, [os.getenv('EMAIL_HOST_SUPPORT')]
        )
        for file in input.files:
            mail.attach(file.name, file.file.read(), guess_type(file.name)[0])
