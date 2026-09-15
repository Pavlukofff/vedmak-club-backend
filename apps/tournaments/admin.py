from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from .models import Tournament, TournamentMatch, TournamentParticipant, TournamentPhoto


class TournamentPhotoInline(TabularInline):
    model = TournamentPhoto
    extra = 1


@admin.register(Tournament)
class TournamentAdmin(ModelAdmin):
    list_display = (
        "title", "status", "bracket_type", "date_start", "date_end",
        "winner", "runner_up", "bracket_generated",
    )
    list_filter = ("status", "bracket_type", "bracket_generated")
    date_hierarchy = "date_start"
    search_fields = ("title",)
    autocomplete_fields = ("winner", "runner_up")
    readonly_fields = ("bracket_generated",)
    inlines = [TournamentPhotoInline]


@admin.register(TournamentParticipant)
class TournamentParticipantAdmin(ModelAdmin):
    list_display = ("tournament", "seed", "user")
    list_filter = ("tournament",)
    search_fields = ("user__username", "user__display_name", "tournament__title")
    autocomplete_fields = ("tournament", "user")


@admin.register(TournamentMatch)
class TournamentMatchAdmin(ModelAdmin):
    list_display = (
        "tournament", "bracket", "round_number", "position",
        "participant1", "participant2", "winner", "battle",
    )
    list_filter = ("tournament", "bracket", "round_number")
    autocomplete_fields = ("tournament", "participant1", "participant2", "winner", "battle")
