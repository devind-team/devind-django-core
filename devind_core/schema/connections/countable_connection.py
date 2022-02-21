"""Модуль"""
import graphene


class CountableConnection(graphene.relay.Connection):
    class Meta:
        abstract = True

    @classmethod
    def __init_subclass_with_meta__(cls, node=None, name=None, **options):
        result = super().__init_subclass_with_meta__(node=node, name=name, **options)
        cls._meta.fields["total_count"] = graphene.Field(
            type=graphene.Int,
            name="totalCount",
            description="Number of items in the queryset.",
            required=True,
            resolver=cls.resolve_total_count,
        )
        cls._meta.fields["node_count"] = graphene.Field(
            type=graphene.Int,
            name="nodeCount",
            description="Number of nodes.",
            required=True,
            resolver=cls.resolve_node_count,
        )
        return result

    def resolve_total_count(self, *_) -> int:
        return self.iterable.count()

    def resolve_node_count(self, *_) -> int:
        return len(self.edges)
