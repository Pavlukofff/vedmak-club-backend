from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from .models import EffectType, ItemEffect, Purchase, ShopItem


@admin.register(EffectType)
class EffectTypeAdmin(ModelAdmin):
    list_display = ("name", "code")
    search_fields = ("name", "code")


class ItemEffectInline(TabularInline):
    model = ItemEffect
    extra = 0
    autocomplete_fields = ("type",)


@admin.register(ShopItem)
class ShopItemAdmin(ModelAdmin):
    list_display = ("name", "category", "price", "min_rank", "toxicity", "is_active")
    list_filter = ("category", "is_active")
    search_fields = ("name",)
    autocomplete_fields = ("min_rank",)
    inlines = [ItemEffectInline]


@admin.register(Purchase)
class PurchaseAdmin(ModelAdmin):
    list_display = ("user", "item", "price_paid", "granted_by", "purchased_at", "is_used")
    list_filter = ("is_used", "item__category")
    date_hierarchy = "purchased_at"
    search_fields = ("user__username", "user__display_name", "item__name")
    autocomplete_fields = ("user", "item", "granted_by")
    readonly_fields = ("purchased_at",)