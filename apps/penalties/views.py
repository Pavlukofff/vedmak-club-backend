from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Penalty
from .serializers import PenaltyCancelSerializer, PenaltyIssueSerializer, PenaltySerializer


def can_view_all_penalties(user):
    return user.is_superuser or user.has_perm("penalties.can_view_penalties") \
        or user.has_perm("penalties.can_issue_penalties")


class PenaltyListCreateView(generics.ListCreateAPIView):
    """Раздел 4.17 плана.

    GET: у обычного участника — только своя история взысканий (личный
    кабинет); у ролей с canViewPenalties/canIssuePenalties — вся история,
    с необязательным фильтром ?user=<username> (страница пользователя в
    админке).
    POST: «вынести взыскание» — доступно только ролям с canIssuePenalties.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        return PenaltyIssueSerializer if self.request.method == "POST" else PenaltySerializer

    def get_queryset(self):
        qs = Penalty.objects.select_related("user", "issued_by", "cancelled_by")
        user = self.request.user
        if can_view_all_penalties(user):
            username = self.request.query_params.get("user")
            return qs.filter(user__username=username) if username else qs
        return qs.filter(user=user)

    def perform_create(self, serializer):
        user = self.request.user
        if not (user.is_superuser or user.has_perm("penalties.can_issue_penalties")):
            raise PermissionDenied("Нет права выносить взыскания.")
        serializer.save(issued_by=user)


class PenaltyCancelView(APIView):
    """POST /api/penalties/<id>/cancel/ — раздел 4.17: отдельное действие с причиной.

    По регламенту клуба — право Главы Клуба; на сайте Админ имеет это право
    по умолчанию, независимо от офлайн-иерархии.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        user = request.user
        if not (user.is_superuser or user.has_perm("penalties.can_cancel_penalties")):
            raise PermissionDenied("Нет права отменять взыскания.")

        penalty = generics.get_object_or_404(Penalty, pk=pk)
        serializer = PenaltyCancelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        penalty.status = Penalty.Status.CANCELLED
        penalty.cancelled_by = user
        penalty.cancel_reason = serializer.validated_data["cancel_reason"]
        penalty.cancelled_at = timezone.now()
        penalty.save(update_fields=["status", "cancelled_by", "cancel_reason", "cancelled_at"])

        return Response(PenaltySerializer(penalty).data, status=status.HTTP_200_OK)
