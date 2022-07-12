from strawberry.utils.await_maybe import AwaitableOrValue
from strawberry.utils.str_converters import to_camel_case
from typing import (
    Any,
    Callable,
    Iterable,
    Type,
    Union,
    Sequence,
    get_origin,
    get_args
)
from strawberry_django_plus.utils import aio
from collections import namedtuple
from strawberry_django_plus.mutations.fields import DjangoInputMutationField, DjangoMutationField
from strawberry_django_plus import relay
import strawberry
from strawberry import UNSET
from strawberry.permission import BasePermission
from strawberry.types import Info
from django.core.exceptions import (
    NON_FIELD_ERRORS,
    ObjectDoesNotExist,
    PermissionDenied,
    ValidationError,
)


@strawberry.type
class ErrorType:
    messages: list[str]
    field: str = strawberry.field(default='')


def _get_validation_errors(error: Exception):
    if isinstance(error, ValidationError) and hasattr(error, "error_dict"):
        # convert field errors
        for field, field_errors in error.message_dict.items():
            yield ErrorType(
                field=to_camel_case(field) if field != NON_FIELD_ERRORS else None,
                messages=field_errors,
            )
    elif isinstance(error, ValidationError) and hasattr(error, "error_list"):
        # convert non-field errors
        for e in error.error_list:
            yield ErrorType(
                messages=[e.message],
            )
    else:
        msg = getattr(error, "msg", None)
        if msg is None:
            msg = str(error)

        yield ErrorType(
            messages=[msg],
        )


def _map_exception(error: Exception):
    if isinstance(error, (ValidationError, PermissionDenied, ObjectDoesNotExist)):
        return {'success': False, 'errors': _get_validation_errors(error)}

    return error


def is_optional(field):
    # org = field is None
    t = type(None) in get_args(field)
    a = 10
    return t
    # return get_origin(field) is Union and \
    #        type(None) in get_args(field)


class DjMutationField(DjangoInputMutationField):
    ret_fields: list[str]

    def __int__(self, args, kwargs):
        super.__init__(*args, **kwargs)

    def __call__(self, resolver: Callable[..., Iterable[relay.Node]]):
        if self._handle_errors:
            name = to_camel_case(resolver.__name__)
            cap_name = name[0].upper() + name[1:]
            anns = resolver.__annotations__["return"].__annotations__
            for val in anns.values():
                a = is_optional(val)
                if not is_optional(val):
                    raise TypeError("Возвращаемый Тип должен быть Optional")
            self.ret_fields = anns.keys()
            klass = type('TPayload', (), {})
            klass.__annotations__ = {**anns, 'success': bool, 'errors': list[ErrorType]}
            name = resolver.__annotations__["return"].__name__
            ret_type = strawberry.type(klass, name=f"{cap_name}Payload" if not name else name)
            resolver.__annotations__["return"] = ret_type
        return super(DjangoMutationField, self).__call__(resolver)

    def get_result(
        self,
        source: Any,
        info: Info,
        args: list[Any],
        kwargs: dict[str, Any],
    ) -> AwaitableOrValue[Any]:
        input_obj = kwargs.pop("input", None)

        # FIXME: Any other exception types that we should capture here?
        resolver = aio.resolver(self.resolver, on_error=_map_exception, info=info)
        resolved = resolver(source, info, input_obj, args, kwargs)
        if not resolved.get('success', True):
            return namedtuple("ObjectName", ['success', 'errors', *self.ret_fields])(*resolved.values(), *[None for _ in self.ret_fields])
        return namedtuple("ObjectName", ['success', 'errors', *self.ret_fields])(True, [], *resolved.values())


def legacy_mutation(
    resolver=None,
    *,
    input_type: type | None = None,
    name: str | None = None,
    field_name: str | None = None,
    filters: Any = UNSET,
    is_subscription: bool = False,
    description: str | None = None,
    permission_classes: list[Type[BasePermission]] | None = None,
    deprecation_reason: str | None = None,
    default: Any = UNSET,
    default_factory: Union[Callable, object] = UNSET,
    directives: Sequence[object] | None = (),
    handle_django_errors: bool = True,
    # This init parameter is used by pyright to determine whether this field
    # is added in the constructor or not. It is not used to change
    # any behavior at the moment.
    init=None,
) -> Any:
    """Annotate a property or a method to create an input mutation field.

    This fields does 3 things:

        - It ensures that the mutation resolver gets called in an async safe environment.
        - If `handle_django_errors` is True (the default), the return values gets
          changed to a union with `OperationMessage`, which will be returned instead
          if the mutation raises any `PermissionDenied`, `ValidationError` or
          `ObjectDoesNotExist`.
        - It transforms the resolver arguments to a new type and receives it in
          a `input` argument at the graphql side.

    """
    f = DjMutationField(
        input_type=input_type,
        python_name=None,
        django_name=field_name,
        graphql_name=name,
        type_annotation=None,
        description=description,
        is_subscription=is_subscription,
        permission_classes=permission_classes or [],
        deprecation_reason=deprecation_reason,
        default=default,
        default_factory=default_factory,
        directives=directives,
        filters=filters,
        handle_django_errors=handle_django_errors,
    )
    if resolver is not None:
        f = f(resolver)
    return f
