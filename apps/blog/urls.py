from django.urls import path

from . import views

urlpatterns = [
    path("posts/", views.BlogPostListCreateView.as_view(), name="blog-post-list-create"),
    path("posts/<slug:slug>/", views.BlogPostDetailView.as_view(), name="blog-post-detail"),
    path("festivals/", views.FestivalListCreateView.as_view(), name="festival-list-create"),
    path("festivals/<int:pk>/", views.FestivalDetailView.as_view(), name="festival-detail"),
    path(
        "festivals/<int:festival_id>/photos/",
        views.FestivalPhotoUploadView.as_view(),
        name="festival-photo-upload",
    ),
    path(
        "festivals/photos/<int:pk>/",
        views.FestivalPhotoDeleteView.as_view(),
        name="festival-photo-delete",
    ),
]
