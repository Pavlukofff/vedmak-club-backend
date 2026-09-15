from django.urls import path

from . import views

urlpatterns = [
    path("templates/", views.TaskTemplateListView.as_view(), name="task-template-list"),
    path("templates/<int:pk>/", views.TaskTemplateDetailView.as_view(), name="task-template-detail"),
    path("assignments/", views.TaskAssignmentListCreateView.as_view(), name="task-assignment-list-create"),
    path("assignments/<int:pk>/", views.TaskAssignmentDetailView.as_view(), name="task-assignment-detail"),
]