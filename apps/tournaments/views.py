from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.dashboard.models import ActivityLogEntry

from .bracket import generate_bracket
from .models import Tournament, TournamentMatch, TournamentParticipant, TournamentPhoto
from .serializers import (
    MatchLinkBattleSerializer,
    ParticipantCreateSerializer,
    TournamentCreateSerializer,
    TournamentDetailSerializer,
    TournamentPhotoSerializer,
    TournamentSerializer,
    TournamentUpdateSerializer,
)


def can_manage_tournaments(user):
    return user.is_superuser or user.has_perm("tournaments.can_manage_tournaments")


class TournamentListView(generics.ListCreateAPIView):
    """Раздел 1 плана: турниры (список, расписание) — чтение публично.

    ?status=finished — архив прошедших турниров (с сохранённой сеткой и фото).
    Создание турнира — только can_manage_tournaments; сам турнир создаётся
    без участников и сетки, дальше они добавляются отдельными эндпоинтами.
    """

    permission_classes = [permissions.AllowAny]

    def get_permissions(self):
        if self.request.method == "POST":
            return [permissions.IsAuthenticated()]
        return super().get_permissions()

    def get_serializer_class(self):
        return TournamentCreateSerializer if self.request.method == "POST" else TournamentSerializer

    def get_queryset(self):
        qs = Tournament.objects.prefetch_related("photos")
        status_param = self.request.query_params.get("status")
        if status_param:
            qs = qs.filter(status=status_param)
        participant = self.request.query_params.get("participant")
        if participant:
            qs = qs.filter(participants__user__username=participant).distinct()
        return qs

    def perform_create(self, serializer):
        if not can_manage_tournaments(self.request.user):
            raise PermissionDenied("Нет права управлять турнирами.")
        serializer.save()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(TournamentSerializer(serializer.instance).data, status=201)


class TournamentDetailView(generics.RetrieveUpdateAPIView):
    """Турнир с полной сеткой (посев, раунды, результаты) — чтение публично.

    PATCH/PUT — редактирование (в т.ч. статуса) — только can_manage_tournaments.
    """

    queryset = Tournament.objects.prefetch_related("participants__user", "matches")
    permission_classes = [permissions.AllowAny]

    def get_permissions(self):
        if self.request.method in ("PUT", "PATCH"):
            return [permissions.IsAuthenticated()]
        return super().get_permissions()

    def get_serializer_class(self):
        return TournamentUpdateSerializer if self.request.method in ("PUT", "PATCH") else TournamentDetailSerializer

    def perform_update(self, serializer):
        if not can_manage_tournaments(self.request.user):
            raise PermissionDenied("Нет права управлять турнирами.")
        serializer.save()

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(TournamentDetailSerializer(serializer.instance).data)


class ParticipantCreateView(generics.CreateAPIView):
    """Добавить участника с номером посева — только can_manage_tournaments,

    пока сетка ещё не сгенерирована.
    """

    serializer_class = ParticipantCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        if not can_manage_tournaments(self.request.user):
            raise PermissionDenied("Нет права управлять турнирами.")
        tournament = generics.get_object_or_404(Tournament, pk=self.kwargs["tournament_id"])
        if tournament.bracket_generated:
            raise ValidationError("Сетка уже сгенерирована — участников больше нельзя добавлять.")

        # unique_together (tournament, user)/(tournament, seed) не проверяется
        # автоматически DRF-валидатором — поле tournament не входит в
        # сериализатор (проставляется здесь), поэтому проверяем вручную,
        # иначе дублирование падает в необработанный IntegrityError (500).
        user = serializer.validated_data["user"]
        seed = serializer.validated_data["seed"]
        if TournamentParticipant.objects.filter(tournament=tournament, user=user).exists():
            raise ValidationError({"user": "Этот участник уже добавлен в турнир."})
        if TournamentParticipant.objects.filter(tournament=tournament, seed=seed).exists():
            raise ValidationError({"seed": "Этот номер посева уже занят."})

        serializer.save(tournament=tournament)


class GenerateBracketView(APIView):
    """POST /api/tournaments/<id>/generate-bracket/ — построить сетку по посеву."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, tournament_id):
        if not can_manage_tournaments(request.user):
            raise PermissionDenied("Нет права управлять турнирами.")

        tournament = generics.get_object_or_404(Tournament, pk=tournament_id)
        if tournament.bracket_generated:
            raise ValidationError("Сетка уже сгенерирована.")

        generate_bracket(tournament)

        ActivityLogEntry.objects.create(
            type=ActivityLogEntry.Type.BRACKET_GENERATED,
            actor=request.user,
            related_object_id=str(tournament.pk),
            message=f"{request.user.display_name}: сгенерировал(а) сетку турнира «{tournament.title}»",
        )

        return Response(TournamentDetailSerializer(tournament).data)


class MatchLinkBattleView(generics.UpdateAPIView):
    """Привязать зафиксированный судьёй Battle к ячейке сетки —

    дальше TournamentMatch.save() сам разберёт победителя и продвинет по сетке.
    """

    queryset = TournamentMatch.objects.select_related("participant1", "participant2")
    serializer_class = MatchLinkBattleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_update(self, serializer):
        if not can_manage_tournaments(self.request.user):
            raise PermissionDenied("Нет права управлять турнирами.")
        serializer.save()


class TournamentPhotoUploadView(APIView):
    """POST multipart {"image": file, "caption": str} — фото прошедшего турнира."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, tournament_id):
        if not can_manage_tournaments(request.user):
            raise PermissionDenied("Нет права управлять турнирами.")
        tournament = generics.get_object_or_404(Tournament, pk=tournament_id)
        image = request.FILES.get("image")
        if not image:
            return Response({"detail": "Файл не передан."}, status=400)
        photo = TournamentPhoto.objects.create(
            tournament=tournament, image=image, caption=request.data.get("caption", ""),
        )
        return Response(TournamentPhotoSerializer(photo).data, status=201)


class TournamentPhotoDeleteView(generics.DestroyAPIView):
    queryset = TournamentPhoto.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def perform_destroy(self, instance):
        if not can_manage_tournaments(self.request.user):
            raise PermissionDenied("Нет права управлять турнирами.")
        instance.delete()
