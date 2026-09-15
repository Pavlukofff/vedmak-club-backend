from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import ScheduleEntry


@admin.register(ScheduleEntry)
class ScheduleEntryAdmin(ModelAdmin):
    list_display = ("weekday", "start_time", "end_time", "title", "activity", "location", "is_active")
    list_filter = ("weekday", "is_active")
    search_fields = ("title", "location")
    autocomplete_fields = ("activity",)
