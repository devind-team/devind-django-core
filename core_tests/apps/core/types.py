#from graphene_django.types import DjangoObjectType
from apps.core.models import User
from strawberry_django_plus import gql


@gql.django.type(User)
class UserType(gql.relay.Node):
    id: gql.relay.GlobalID
    username: gql.auto
    email: gql.auto
    first_name: gql.auto

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