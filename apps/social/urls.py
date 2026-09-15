from django.urls import path

from . import views

urlpatterns = [
    path("", views.SocialLinkListCreateView.as_view(), name="social-link-list-create"),
    path("<int:pk>/", views.SocialLinkDetailView.as_view(), name="social-link-detail"),
]
