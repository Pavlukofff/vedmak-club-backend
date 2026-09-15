from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import School


@admin.register(School)
class SchoolAdmin(ModelAdmin):
    list_display = ("name", "weapon_type", "base_hp", "status")
    list_filter = ("status",)
    search_fields = ("name",)