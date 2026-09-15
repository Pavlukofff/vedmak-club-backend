from django.urls import path

from . import views

urlpatterns = [
    path("feed/", views.ActivityFeedView.as_view(), name="dashboard-feed"),
    path("birthdays/", views.BirthdaysView.as_view(), name="dashboard-birthdays"),
]
