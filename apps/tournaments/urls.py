from django.urls import path

from . import views

urlpatterns = [
    path("", views.TournamentListView.as_view(), name="tournament-list"),
    path("<int:pk>/", views.TournamentDetailView.as_view(), name="tournament-detail"),
    path(
        "<int:tournament_id>/participants/",
        views.ParticipantCreateView.as_view(),
        name="tournament-participant-create",
    ),
    path(
        "<int:tournament_id>/generate-bracket/",
        views.GenerateBracketView.as_view(),
        name="tournament-generate-bracket",
    ),
    path(
        "matches/<int:pk>/battle/",
        views.MatchLinkBattleView.as_view(),
        name="tournament-match-link-battle",
    ),
    path(
        "<int:tournament_id>/photos/",
        views.TournamentPhotoUploadView.as_view(),
        name="tournament-photo-upload",
    ),
    path(
        "photos/<int:pk>/",
        views.TournamentPhotoDeleteView.as_view(),
        name="tournament-photo-delete",
    ),
]
