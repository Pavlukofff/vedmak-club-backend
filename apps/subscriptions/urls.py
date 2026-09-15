from django.urls import path

from . import views

urlpatterns = [
    path("activities/", views.ActivityPriceListView.as_view(), name="activity-price-list"),
    path("tickets/", views.SubscriptionListView.as_view(), name="subscription-list"),
    path("tickets/<int:pk>/", views.SubscriptionDetailView.as_view(), name="subscription-detail"),
]