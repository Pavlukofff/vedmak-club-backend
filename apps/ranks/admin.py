from django.contrib import admin
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from unfold.admin import ModelAdmin, TabularInline

from .models import Rank, RankRequirement, RankReward, RankUpRequest


class RankRequirementInline(TabularInline):
    model = RankRequirement
    fk_name = "rank"
    extra = 0


class RankRewardInline(TabularInline):
    model = RankReward
    extra = 0


@admin.register(Rank)
class RankAdmin(ModelAdmin):
    list_display = ("order", "icon", "name")
    ordering = ("order",)
    search_fields = ("name",)
    inlines = [RankRequirementInline, RankRewardInline]


@admin.register(RankUpRequest)
class RankUpRequestAdmin(ModelAdmin):
    list_display = ("user", "from_rank", "to_rank", "status", "created_at", "reviewed_by")
    list_filter = ("status",)
    date_hierarchy = "created_at"
    search_fields = ("user__username", "user__display_name")
    autocomplete_fields = ("user", "from_rank", "to_rank", "reviewed_by")
    readonly_fields = ("reviewed_by", "reviewed_at")

    def save_model(self, request, obj, form, change):
        reviewing_now = change and "status" in form.changed_data and obj.status in (
            RankUpRequest.Status.APPROVED, RankUpRequest.Status.REJECTED,
        )
        if reviewing_now:
            if not (request.user.is_superuser or request.user.has_perm("ranks.can_approve_ranks")):
                raise PermissionDenied("Нет права подтверждать заявки на повышение ранга.")
            obj.reviewed_by = request.user
            obj.reviewed_at = timezone.now()
            if obj.status == RankUpRequest.Status.APPROVED:
                obj.user.rank = obj.to_rank
                obj.user._activity_actor = request.user
                obj.user.save(update_fields=["rank"])

        super().save_model(request, obj, form, change)