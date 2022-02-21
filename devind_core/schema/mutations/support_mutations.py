import os
from mimetypes import guess_type

import graphene
from django.core.mail import EmailMultiAlternatives
from graphene_file_upload.scalars import Upload
from graphql import ResolveInfo

from devind_helpers.schema.mutations import BaseMutation


class SupportSubmitMutation(BaseMutation):
    """Отправка письма поддержки"""

    class Input:
        topic = graphene.String(required=True, description='Тема')
        text = graphene.String(required=True, description='Текст')
        files = graphene.List(graphene.NonNull(Upload), description='Загружаемые файлы')

    @staticmethod
    def mutate_and_get_payload(root, info: ResolveInfo, topic: str, text: str, **kwargs):
        user = info.context.user
        from_email: str = os.getenv('EMAIL_HOST_USER')
        mail: EmailMultiAlternatives = EmailMultiAlternatives(
            f'{topic}: { user.email }', text, from_email, [os.getenv('EMAIL_HOST_SUPPORT')]
        )
        if 'files' in kwargs and kwargs['files'] is not None:
            for file in kwargs['files']:
                mail.attach(file.name, file.file.read(), guess_type(file.name)[0])
        return SupportSubmitMutation(success=mail.send() > 0)


class SupportMutations(graphene.ObjectType):
    support_submit = SupportSubmitMutation.Field(required=True)
