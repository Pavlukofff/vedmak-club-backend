from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import Bestiary, MonsterKill


@admin.register(Bestiary)
class BestiaryAdmin(ModelAdmin):
    list_display = ("name", "category", "danger_level")
    list_filter = ("category", "danger_level")
    search_fields = ("name",)


@admin.register(MonsterKill)
class MonsterKillAdmin(ModelAdmin):
    list_display = ("user", "bestiary", "date", "reward_granted", "recorded_by")
    list_filter = ("reward_granted", "bestiary")
    date_hierarchy = "date"
    search_fields = ("user__username", "user__display_name", "bestiary__name")
    autocomplete_fields = ("user", "bestiary", "battle", "recorded_by", "reward_granted_by")
    readonly_fields = ("recorded_by", "reward_granted_by")

    def save_model(self, request, obj, form, change):
        if not change:
            obj.recorded_by = request.user
        if "reward_granted" in form.changed_data and obj.reward_granted:
            obj.reward_granted_by = request.user
        super().save_model(request, obj, form, change)