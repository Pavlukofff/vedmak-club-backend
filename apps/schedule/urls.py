from django.urls import path

from . import views

urlpatterns = [
    path("", views.ScheduleEntryListCreateView.as_view(), name="schedule-entry-list-create"),
    path("<int:pk>/", views.ScheduleEntryDetailView.as_view(), name="schedule-entry-detail"),
]
