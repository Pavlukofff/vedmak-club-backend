from django.urls import path

from . import views

urlpatterns = [
    path("posts/", views.BlogPostListCreateView.as_view(), name="blog-post-list-create"),
    # Не <slug:slug> — встроенный SlugConverter матчит только ASCII
    # ([-a-zA-Z0-9_]+), а BlogPost.slug генерируется с allow_unicode=True
    # (заголовки клуба обычно на кириллице) — с slug: почти любой реальный
    # пост давал бы 404 ещё на уровне роутинга, до вьюхи.
    path("posts/<str:slug>/", views.BlogPostDetailView.as_view(), name="blog-post-detail"),
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
