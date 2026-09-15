from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import Battle


@admin.register(Battle)
class BattleAdmin(ModelAdmin):
    list_display = (
        "fighter1", "fighter2", "winner", "type", "is_ranked", "tournament", "date", "recorded_by",
    )
    list_filter = ("type", "is_ranked", "tournament")
    date_hierarchy = "date"
    search_fields = (
        "fighter1__username", "fighter1__display_name",
        "fighter2__username", "fighter2__display_name",
    )
    autocomplete_fields = (
        "fighter1", "fighter2", "winner", "main_judge", "side_judge", "tournament", "recorded_by",
    )
    readonly_fields = ("recorded_by",)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.recorded_by = request.user
        super().save_model(request, obj, form, change)