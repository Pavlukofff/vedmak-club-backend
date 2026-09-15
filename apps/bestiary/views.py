from rest_framework import generics, permissions

from .models import Bestiary, MonsterKill
from .permissions import CanRecordKills
from .serializers import (
    BestiaryDetailSerializer,
    BestiarySerializer,
    MonsterKillSerializer,
    MonsterKillWriteSerializer,
)


class BestiaryListView(generics.ListAPIView):
    """Раздел 1 плана: справочник видов монстров, публичный."""

    queryset = Bestiary.objects.all()
    serializer_class = BestiarySerializer
    permission_classes = [permissions.AllowAny]


class BestiaryDetailView(generics.RetrieveAPIView):
    """Карточка вида — с полным списком пользователей, убивавших это существо."""

    queryset = Bestiary.objects.prefetch_related("kills__user")
    serializer_class = BestiaryDetailSerializer
    permission_classes = [permissions.AllowAny]


class MonsterKillListCreateView(generics.ListCreateAPIView):
    """Раздел 1 плана: журнал охот, публичный на чтение.

    Запись создаёт только судья/админ (can_record_kills) — раздел 4.7.
    ?user=<username> — убийства конкретного участника (профиль/кабинет).
    ?bestiary=<id> — кто убивал конкретный вид.
    """

    permission_classes = [CanRecordKills]

    def get_serializer_class(self):
        return MonsterKillWriteSerializer if self.request.method == "POST" else MonsterKillSerializer

    def get_queryset(self):
        qs = MonsterKill.objects.select_related(
            "user", "bestiary", "battle", "recorded_by", "reward_granted_by",
        )
        username = self.request.query_params.get("user")
        if username:
            qs = qs.filter(user__username=username)
        bestiary_id = self.request.query_params.get("bestiary")
        if bestiary_id:
            qs = qs.filter(bestiary_id=bestiary_id)
        return qs

    def perform_create(self, serializer):
        extra = {"recorded_by": self.request.user}
        if serializer.validated_data.get("reward_granted"):
            extra["reward_granted_by"] = self.request.user
        serializer.save(**extra)


class MonsterKillDetailView(generics.RetrieveUpdateAPIView):
    """Редактирование записи / дозапись награды — раздел 4.7 плана."""

    queryset = MonsterKill.objects.select_related(
        "user", "bestiary", "battle", "recorded_by", "reward_granted_by",
    )
    permission_classes = [CanRecordKills]

    def get_serializer_class(self):
        return MonsterKillWriteSerializer if self.request.method in ("PUT", "PATCH") else MonsterKillSerializer

    def perform_update(self, serializer):
        was_granted = serializer.instance.reward_granted
        extra = {}
        if serializer.validated_data.get("reward_granted") and not was_granted:
            extra["reward_granted_by"] = self.request.user
        serializer.save(**extra)
