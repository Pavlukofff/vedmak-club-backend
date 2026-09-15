from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import SocialLink


@admin.register(SocialLink)
class SocialLinkAdmin(ModelAdmin):
    list_display = ("owner_type", "owner", "platform", "url", "label")
    list_filter = ("owner_type", "platform")
    search_fields = ("platform", "label", "owner__username", "owner__display_name")
    autocomplete_fields = ("owner",)
