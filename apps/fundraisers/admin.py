from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from .models import Fundraiser, FundraiserContribution


class ContributionInline(TabularInline):
    model = FundraiserContribution
    extra = 0
    autocomplete_fields = ("contributor",)
    readonly_fields = ("recorded_by", "created_at")


@admin.register(Fundraiser)
class FundraiserAdmin(ModelAdmin):
    list_display = ("title", "status", "goal_amount", "raised_amount_display", "start_date", "end_date")
    list_filter = ("status",)
    date_hierarchy = "start_date"
    search_fields = ("title",)
    inlines = [ContributionInline]

    @admin.display(description="Собрано, BYN")
    def raised_amount_display(self, obj):
        return obj.raised_amount

    def save_formset(self, request, form, formset, change):
        if formset.model is not FundraiserContribution:
            return super().save_formset(request, form, formset, change)
        instances = formset.save(commit=False)
        for instance in instances:
            if not instance.pk:
                instance.recorded_by = request.user
            instance.save()
        formset.save_m2m()


@admin.register(FundraiserContribution)
class FundraiserContributionAdmin(ModelAdmin):
    list_display = ("fundraiser", "amount", "contributor", "contributor_name", "is_anonymous", "created_at")
    list_filter = ("is_anonymous", "fundraiser")
    date_hierarchy = "created_at"
    search_fields = ("contributor__username", "contributor__display_name", "contributor_name")
    autocomplete_fields = ("fundraiser", "contributor")
    readonly_fields = ("recorded_by",)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.recorded_by = request.user
        super().save_model(request, obj, form, change)
