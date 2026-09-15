from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import ClubCodex


@admin.register(ClubCodex)
class ClubCodexAdmin(ModelAdmin):
    list_display = ("updated_at", "updated_by")
    readonly_fields = ("updated_at", "updated_by")

    def has_add_permission(self, request):
        return not ClubCodex.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
