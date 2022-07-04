#from devind_core.schema.converter import Schema
from strawberry_django_plus import gql
from strawberry_django_plus.directives import SchemaDirectiveExtension
from strawberry_django_plus.optimizer import DjangoOptimizerExtension
from devind_core.schema import Query
from devind_core.schema.queries.user_queries import UserMutations

schema = gql.Schema(query=Query, mutation=UserMutations, extensions=[SchemaDirectiveExtension, DjangoOptimizerExtension])
