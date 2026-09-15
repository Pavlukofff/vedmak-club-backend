from django.urls import path

from . import views

urlpatterns = [
    path("register/", views.RegisterView.as_view(), name="register"),
    path("verify-email/", views.EmailVerifyView.as_view(), name="verify-email"),
    path("me/", views.MeView.as_view(), name="me"),
    path("me/avatar/preset/", views.SetAvatarPresetView.as_view(), name="me-avatar-preset"),
    path("me/avatar/upload/", views.UploadAvatarView.as_view(), name="me-avatar-upload"),
    path("avatar-presets/", views.AvatarPresetListView.as_view(), name="avatar-presets"),
    path("users/", views.PublicProfileListView.as_view(), name="public-profile-list"),
    path("users/<str:username>/", views.PublicProfileDetailView.as_view(), name="public-profile-detail"),
    path(
        "displayname-requests/",
        views.DisplayNameChangeRequestListCreateView.as_view(),
        name="displayname-requests",
    ),
    path(
        "displayname-requests/<int:pk>/approve/",
        views.DisplayNameChangeRequestReviewView.as_view(),
        {"decision": "approve"},
        name="displayname-request-approve",
    ),
    path(
        "displayname-requests/<int:pk>/reject/",
        views.DisplayNameChangeRequestReviewView.as_view(),
        {"decision": "reject"},
        name="displayname-request-reject",
    ),
    path(
        "currency-transfers/",
        views.CurrencyTransferListCreateView.as_view(),
        name="currency-transfers",
    ),
]