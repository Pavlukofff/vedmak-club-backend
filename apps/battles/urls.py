from django.urls import path

from . import views

urlpatterns = [
    path("", views.BattleListCreateView.as_view(), name="battle-list-create"),
    path("ratings/", views.BattleRatingsView.as_view(), name="battle-ratings"),
    path("<int:pk>/", views.BattleDetailView.as_view(), name="battle-detail"),
]