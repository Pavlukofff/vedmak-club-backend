from django.urls import path

from . import views

urlpatterns = [
    path("", views.TitleListView.as_view(), name="title-list"),
    path("awards/", views.TitleAwardListCreateView.as_view(), name="title-award-list-create"),
    path("awards/<int:pk>/", views.TitleAwardDetailView.as_view(), name="title-award-detail"),
]
