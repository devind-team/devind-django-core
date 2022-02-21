from devind_helpers.permissions import BasePermission, ModelPermission


AddUser = ModelPermission('devind_core.add_user')


class ChangeUser(BasePermission):
    """Пропускает пользователей, которые могут изменять пользователя."""

    @staticmethod
    def has_object_permission(context, obj):
        """Непосредственная проверка разрешений."""
        return ChangeUser.has_permission(context) or obj.change(context.user) or context.user == obj


class DeleteUser(BasePermission):
    """Пропускает пользователей, которые могут удалять пользователя."""

    @staticmethod
    def has_object_permission(context, obj):
        """Непосредственная проверка разрешений."""
        return DeleteUser.has_permission(context) or obj.change(context.user) or context.user == obj


class ViewUser(BasePermission):
    """Пропускает пользователя, который может просматривать другого пользователя."""

    @staticmethod
    def has_object_permission(context, obj):
        """Непосредственная проверка разрешений."""
        return ViewUser.has_permission(context) or obj.change(context.user) or context.user == obj
