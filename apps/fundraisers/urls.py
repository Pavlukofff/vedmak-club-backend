from django.urls import path

from . import views

urlpatterns = [
    path("", views.FundraiserListCreateView.as_view(), name="fundraiser-list-create"),
    path("<int:pk>/", views.FundraiserDetailView.as_view(), name="fundraiser-detail"),
    path(
        "<int:fundraiser_id>/contributions/",
        views.ContributionCreateView.as_view(),
        name="fundraiser-contribution-create",
    ),
]
