from django.utils import timezone
from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Rank, RankUpRequest
from .serializers import (
    RankSerializer,
    RankUpRequestCreateSerializer,
    RankUpRequestSerializer,
)


def can_approve_ranks(user):
    return user.is_superuser or user.has_perm("ranks.can_approve_ranks")


class RankListView(generics.ListAPIView):
    """Публичный справочник рангов цеха с требованиями/наградами (раздел 4.11)."""

    queryset = Rank.objects.prefetch_related("requirements", "rewards")
    serializer_class = RankSerializer
    permission_classes = [permissions.AllowAny]


class RankDetailView(generics.RetrieveAPIView):
    queryset = Rank.objects.prefetch_related("requirements", "rewards")
    serializer_class = RankSerializer
    permission_classes = [permissions.AllowAny]


class RankUpRequestListCreateView(generics.ListCreateAPIView):
    """Раздел 4.11 плана.

    GET: участник видит только свои заявки; роль с can_approve_ranks — все,
    с фильтром ?user=<username> (очередь на рассмотрение).
    POST: «подать заявку на ранг X» — только на следующий по порядку ранг,
    не более одной заявки в очереди одновременно.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        return RankUpRequestCreateSerializer if self.request.method == "POST" else RankUpRequestSerializer

    def get_queryset(self):
        qs = RankUpRequest.objects.select_related("user", "from_rank", "to_rank", "reviewed_by")
        requester = self.request.user
        if can_approve_ranks(requester):
            username = self.request.query_params.get("user")
            return qs.filter(user__username=username) if username else qs
        return qs.filter(user=requester)

    def perform_create(self, serializer):
        user = self.request.user
        serializer.save(user=user, from_rank=user.rank)


class RankUpRequestDetailView(generics.RetrieveAPIView):
    """GET — владелец или can_approve_ranks."""

    queryset = RankUpRequest.objects.select_related("user", "from_rank", "to_rank", "reviewed_by")
    serializer_class = RankUpRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        obj = super().get_object()
        requester = self.request.user
        if obj.user_id != requester.id and not can_approve_ranks(requester):
            raise PermissionDenied("Это не ваша заявка.")
        return obj


class RankUpRequestReviewView(APIView):
    """POST /api/ranks/rank-up-requests/<id>/approve/ | /reject/.

    Раздел 4.11: одобряет/отклоняет мастер/админ вручную. При одобрении
    пользователю реально присваивается новый ранг.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk, decision):
        if not can_approve_ranks(request.user):
            raise PermissionDenied("Нет права подтверждать заявки на повышение ранга.")

        req = generics.get_object_or_404(RankUpRequest, pk=pk)
        if req.status != RankUpRequest.Status.PENDING:
            raise ValidationError("Заявка уже рассмотрена.")

        req.status = RankUpRequest.Status.APPROVED if decision == "approve" else RankUpRequest.Status.REJECTED
        req.reviewed_by = request.user
        req.reviewed_at = timezone.now()
        req.save(update_fields=["status", "reviewed_by", "reviewed_at"])

        if decision == "approve":
            req.user.rank = req.to_rank
            req.user._activity_actor = request.user
            req.user.save(update_fields=["rank"])

        return Response(RankUpRequestSerializer(req).data)