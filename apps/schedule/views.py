from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied

from .models import ScheduleEntry
from .serializers import ScheduleEntrySerializer, ScheduleEntryWriteSerializer


def can_manage_schedule(user):
    return user.is_authenticated and (user.is_superuser or user.has_perm("schedule.can_manage_schedule"))


class ScheduleEntryListCreateView(generics.ListCreateAPIView):
    """Раздел 1 плана: расписание тренировок/занятий клуба, публичное на чтение."""

    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_serializer_class(self):
        return ScheduleEntryWriteSerializer if self.request.method == "POST" else ScheduleEntrySerializer

    def get_queryset(self):
        qs = ScheduleEntry.objects.select_related("activity")
        if not can_manage_schedule(self.request.user):
            qs = qs.filter(is_active=True)
        return qs

    def perform_create(self, serializer):
        if not can_manage_schedule(self.request.user):
            raise PermissionDenied("Нет права редактировать расписание.")
        serializer.save()


class ScheduleEntryDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = ScheduleEntry.objects.select_related("activity")
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_serializer_class(self):
        return ScheduleEntryWriteSerializer if self.request.method in ("PUT", "PATCH") else ScheduleEntrySerializer

    def perform_update(self, serializer):
        if not can_manage_schedule(self.request.user):
            raise PermissionDenied("Нет права редактировать расписание.")
        serializer.save()

    def perform_destroy(self, instance):
        if not can_manage_schedule(self.request.user):
            raise PermissionDenied("Нет права редактировать расписание.")
        instance.delete()
