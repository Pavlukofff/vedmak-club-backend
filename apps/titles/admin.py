from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import Title, TitleAward


@admin.register(Title)
class TitleAdmin(ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(TitleAward)
class TitleAwardAdmin(ModelAdmin):
    list_display = ("user", "title", "granted_by", "granted_at")
    list_filter = ("title",)
    date_hierarchy = "granted_at"
    search_fields = ("user__username", "user__display_name", "title__name")
    autocomplete_fields = ("user", "title", "granted_by")
    readonly_fields = ("granted_by", "granted_at")

    def save_model(self, request, obj, form, change):
        if not change:
            obj.granted_by = request.user
        super().save_model(request, obj, form, change)

    def delete_model(self, request, obj):
        obj._deleted_by = request.user
        super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        for obj in queryset:
            obj._deleted_by = request.user
            obj.delete()
