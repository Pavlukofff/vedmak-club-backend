from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .birthdays import upcoming_birthdays
from .models import ActivityLogEntry
from .serializers import ActivityLogEntrySerializer, BirthdaySerializer


class IsStaff(permissions.BasePermission):
    """Dashboard — раздел 4.13 плана: «открывается первой при входе в админку»."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)


class ActivityFeedView(generics.ListAPIView):
    """GET /api/dashboard/feed/?type=... — последние события, раздел 4.13 плана."""

    serializer_class = ActivityLogEntrySerializer
    permission_classes = [IsStaff]

    def get_queryset(self):
        qs = ActivityLogEntry.objects.select_related("actor", "target")
        entry_type = self.request.query_params.get("type")
        if entry_type:
            qs = qs.filter(type=entry_type)
        return qs[:200]


class BirthdaysView(APIView):
    """GET /api/dashboard/birthdays/?days=7 — раздел 4.13 плана: ближайшие ДР."""

    permission_classes = [IsStaff]

    def get(self, request):
        days = int(request.query_params.get("days", 7))
        rows = upcoming_birthdays(days=days)
        return Response(BirthdaySerializer(rows, many=True).data)
