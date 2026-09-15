from django.contrib import admin
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from unfold.admin import ModelAdmin

from .models import Penalty


@admin.register(Penalty)
class PenaltyAdmin(ModelAdmin):
    list_display = (
        "user", "type", "status", "issued_by", "issued_at", "expires_at", "cancelled_at",
    )
    list_filter = ("type", "status")
    date_hierarchy = "issued_at"
    search_fields = ("user__username", "user__display_name", "reason")
    autocomplete_fields = ("user", "issued_by", "cancelled_by", "related_battle")
    readonly_fields = ("issued_by", "issued_at", "cancelled_by", "cancelled_at")

    def save_model(self, request, obj, form, change):
        cancelling_now = change and "status" in form.changed_data and obj.status == Penalty.Status.CANCELLED
        if cancelling_now:
            if not (request.user.is_superuser or request.user.has_perm("penalties.can_cancel_penalties")):
                raise PermissionDenied("Отменять взыскания может только Глава Клуба или Админ сайта.")
            obj.cancelled_by = request.user
            obj.cancelled_at = timezone.now()

        if not change:
            obj.issued_by = request.user

        super().save_model(request, obj, form, change)
