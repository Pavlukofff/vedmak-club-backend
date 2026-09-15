from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import ActivityLogEntry


@admin.register(ActivityLogEntry)
class ActivityLogEntryAdmin(ModelAdmin):
    list_display = ("created_at", "type", "actor", "target", "message")
    list_filter = ("type",)
    date_hierarchy = "created_at"
    search_fields = ("message", "actor__username", "target__username")
    readonly_fields = ("type", "actor", "target", "related_object_id", "message", "created_at")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
