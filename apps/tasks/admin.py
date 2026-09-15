from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import TaskAssignment, TaskTemplate


@admin.register(TaskTemplate)
class TaskTemplateAdmin(ModelAdmin):
    list_display = (
        "title", "reward_experience", "reward_currency", "max_slots",
        "is_repeatable", "is_active", "completions_count", "available_slots",
    )
    list_filter = ("is_active", "is_repeatable")
    search_fields = ("title",)


@admin.register(TaskAssignment)
class TaskAssignmentAdmin(ModelAdmin):
    list_display = ("user", "task_template", "status", "assigned_at", "completed_at")
    list_filter = ("status", "task_template")
    date_hierarchy = "assigned_at"
    search_fields = ("user__username", "user__display_name", "task_template__title")
    autocomplete_fields = ("user", "task_template")
    readonly_fields = ("completed_at",)