from rest_framework import permissions


class CanRecordBattles(permissions.BasePermission):
    """Раздел 4.14 плана: результаты боёв фиксирует только судья/админ.

    Список и карточка боя — публичны (раздел 1: «Таблица боёв»), запись и
    редактирование — только для роли с правом can_record_battles.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        user = request.user
        return bool(
            user and user.is_authenticated
            and (user.is_superuser or user.has_perm("battles.can_record_battles")),
        )
