from django.urls import path

from . import views

urlpatterns = [
    path("", views.RankListView.as_view(), name="rank-list"),
    path("<int:pk>/", views.RankDetailView.as_view(), name="rank-detail"),
    path(
        "rank-up-requests/",
        views.RankUpRequestListCreateView.as_view(),
        name="rank-up-request-list-create",
    ),
    path(
        "rank-up-requests/<int:pk>/",
        views.RankUpRequestDetailView.as_view(),
        name="rank-up-request-detail",
    ),
    path(
        "rank-up-requests/<int:pk>/approve/",
        views.RankUpRequestReviewView.as_view(),
        {"decision": "approve"},
        name="rank-up-request-approve",
    ),
    path(
        "rank-up-requests/<int:pk>/reject/",
        views.RankUpRequestReviewView.as_view(),
        {"decision": "reject"},
        name="rank-up-request-reject",
    ),
]
