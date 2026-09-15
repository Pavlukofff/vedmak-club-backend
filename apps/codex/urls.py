from django.urls import path

from . import views

urlpatterns = [
    path("", views.ClubCodexView.as_view(), name="club-codex"),
]
