#from graphene_django.types import DjangoObjectType
from apps.core.models import User
import strawberry
from strawberry import auto


@strawberry.django.type(User)
class UserType:
    id: auto
    username: auto
    email: auto
    first_name: auto

# class UserType(DjangoObjectType):
#     """Описание пользовательского типа."""
#
#     class Meta:
#         model = User
#         fields = (
#             'id',
#             'username',
#             'email',
#             'first_name',
#         )