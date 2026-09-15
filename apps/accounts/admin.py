from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from unfold.admin import ModelAdmin
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm

from .models import AvatarPreset, CurrencyTransfer, DisplayNameChangeRequest, SiteSettings, User


@admin.register(User)
class UserAdmin(DjangoUserAdmin, ModelAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm

    list_display = (
        "username", "display_name", "email", "school", "rank",
        "level", "balance", "is_staff",
    )
    list_filter = DjangoUserAdmin.list_filter + ("school", "rank")
    search_fields = ("username", "display_name", "email")

    fieldsets = DjangoUserAdmin.fieldsets + (
        ("Персонаж", {
            "fields": (
                "display_name", "name_visibility", "avatar",
                "school", "rank", "level", "experience", "balance",
                "birth_date", "birth_date_visibility", "character_description",
            ),
        }),
        ("Верификация", {"fields": ("email_verified",)}),
    )

    def save_model(self, request, obj, form, change):
        # Проставляем безусловно — сигнал дашборда сам решит, было ли
        # реальное изменение ранга/баланса, и создаст запись в ленте
        # только тогда, а не при любом сохранении формы пользователя.
        obj._activity_actor = request.user
        super().save_model(request, obj, form, change)


@admin.register(DisplayNameChangeRequest)
class DisplayNameChangeRequestAdmin(ModelAdmin):
    list_display = ("user", "current_name", "requested_name", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("user__username", "user__display_name", "requested_name")
    autocomplete_fields = ("user", "reviewed_by")
    readonly_fields = ("reviewed_by", "reviewed_at")

    def save_model(self, request, obj, form, change):
        reviewing_now = change and "status" in form.changed_data and obj.status in (
            DisplayNameChangeRequest.Status.APPROVED, DisplayNameChangeRequest.Status.REJECTED,
        )
        if reviewing_now:
            if not (request.user.is_superuser or request.user.has_perm("accounts.can_review_displayname_requests")):
                raise PermissionDenied("Нет права рассматривать заявки на смену никнейма.")
            obj.reviewed_by = request.user
            obj.reviewed_at = timezone.now()
            if obj.status == DisplayNameChangeRequest.Status.APPROVED:
                obj.user.display_name = obj.requested_name
                obj.user.save(update_fields=["display_name"])

        super().save_model(request, obj, form, change)


@admin.register(AvatarPreset)
class AvatarPresetAdmin(ModelAdmin):
    list_display = ("title", "category", "is_active")
    list_filter = ("category", "is_active")
    search_fields = ("title",)


@admin.register(CurrencyTransfer)
class CurrencyTransferAdmin(ModelAdmin):
    list_display = ("sender", "recipient", "amount", "created_at")
    search_fields = ("sender__username", "recipient__username")
    autocomplete_fields = ("sender", "recipient")
    readonly_fields = ("created_at",)


@admin.register(SiteSettings)
class SiteSettingsAdmin(ModelAdmin):
    list_display = ("starting_balance",)

    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
