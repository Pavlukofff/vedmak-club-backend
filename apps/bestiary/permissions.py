from rest_framework import permissions


class CanRecordKills(permissions.BasePermission):
    """Раздел 4.7 плана: запись об убийстве создаёт только админ/судья.

    Бестиарий и журнал убийств — публичны на чтение, запись/редактирование
    журнала убийств — только для роли с правом can_record_kills.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        user = request.user
        return bool(
            user and user.is_authenticated
            and (user.is_superuser or user.has_perm("bestiary.can_record_kills")),
        )