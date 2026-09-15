from django.db.models import Q
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Battle
from .permissions import CanRecordBattles
from .serializers import BattleSerializer
from .stats import battle_ratings


class BattleListCreateView(generics.ListCreateAPIView):
    """Раздел 1 плана: публичная таблица боёв. Запись — только судья/админ.

    ?user=<username> — бои конкретного участника (страница профиля,
    «Мои бои» в личном кабинете). ?tournament=<id> — бои турнира.
    """

    serializer_class = BattleSerializer
    permission_classes = [CanRecordBattles]

    def get_queryset(self):
        qs = Battle.objects.select_related(
            "fighter1", "fighter2", "winner", "main_judge", "side_judge", "recorded_by", "tournament",
        )
        username = self.request.query_params.get("user")
        if username:
            qs = qs.filter(Q(fighter1__username=username) | Q(fighter2__username=username))
        tournament_id = self.request.query_params.get("tournament")
        if tournament_id:
            qs = qs.filter(tournament_id=tournament_id)
        return qs

    def perform_create(self, serializer):
        serializer.save(recorded_by=self.request.user)


class BattleDetailView(generics.RetrieveUpdateAPIView):
    """Редактирование результата — раздел 1 плана («Управление боями»)."""

    queryset = Battle.objects.select_related(
        "fighter1", "fighter2", "winner", "main_judge", "side_judge", "recorded_by",
    )
    serializer_class = BattleSerializer
    permission_classes = [CanRecordBattles]


class BattleRatingsView(APIView):
    """Раздел 1 плана: рейтинг побед/поражений, отсортированный по победам."""

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response(battle_ratings())