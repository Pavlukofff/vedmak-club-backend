from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import FAQItem


@admin.register(FAQItem)
class FAQItemAdmin(ModelAdmin):
    list_display = ("question", "category", "order", "is_active")
    list_filter = ("category", "is_active")
    search_fields = ("question", "answer")
    list_editable = ("order", "is_active")
