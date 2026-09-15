from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from .models import BlogPost, Festival, FestivalPhoto


class FestivalPhotoInline(TabularInline):
    model = FestivalPhoto
    extra = 1


@admin.register(Festival)
class FestivalAdmin(ModelAdmin):
    list_display = ("title", "date_start", "date_end")
    search_fields = ("title",)
    inlines = [FestivalPhotoInline]


@admin.register(BlogPost)
class BlogPostAdmin(ModelAdmin):
    list_display = ("title", "author", "festival", "is_published", "published_at")
    list_filter = ("is_published", "festival")
    date_hierarchy = "published_at"
    search_fields = ("title", "content")
    autocomplete_fields = ("author", "festival")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("author",)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.author = request.user
        super().save_model(request, obj, form, change)
