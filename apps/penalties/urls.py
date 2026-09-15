from django.urls import path

from . import views

urlpatterns = [
    path("", views.PenaltyListCreateView.as_view(), name="penalty-list-create"),
    path("<int:pk>/cancel/", views.PenaltyCancelView.as_view(), name="penalty-cancel"),
]
