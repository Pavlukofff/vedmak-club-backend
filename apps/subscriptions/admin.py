from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import ActivityPrice, Subscription


@admin.register(ActivityPrice)
class ActivityPriceAdmin(ModelAdmin):
    list_display = ("name", "price_real", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)


@admin.register(Subscription)
class SubscriptionAdmin(ModelAdmin):
    list_display = ("name", "price_real", "price_currency", "duration_days", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)
    filter_horizontal = ("included_activities",)