from django.urls import path

from . import views

urlpatterns = [
    path("species/", views.BestiaryListView.as_view(), name="bestiary-species-list"),
    path("species/<int:pk>/", views.BestiaryDetailView.as_view(), name="bestiary-species-detail"),
    path("kills/", views.MonsterKillListCreateView.as_view(), name="monster-kill-list-create"),
    path("kills/<int:pk>/", views.MonsterKillDetailView.as_view(), name="monster-kill-detail"),
]
