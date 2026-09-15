from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.dashboard.models import ActivityLogEntry

from .bracket import generate_bracket
from .models import Tournament, TournamentMatch, TournamentPhoto
from .serializers import (
    MatchLinkBattleSerializer,
    ParticipantCreateSerializer,
    TournamentDetailSerializer,
    TournamentPhotoSerializer,
    TournamentSerializer,
)


def can_manage_tournaments(user):
    return user.is_superuser or user.has_perm("tournaments.can_manage_tournaments")


class TournamentListView(generics.ListAPIView):
    """Раздел 1 плана: турниры (список, расписание) — публично.

    ?status=finished — архив прошедших турниров (с сохранённой сеткой и фото).
    """

    serializer_class = TournamentSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = Tournament.objects.prefetch_related("photos")
        status_param = self.request.query_params.get("status")
        if status_param:
            qs = qs.filter(status=status_param)
        return qs


class TournamentDetailView(generics.RetrieveAPIView):
    """Турнир с полной сеткой (посев, раунды, результаты) — публично."""

    queryset = Tournament.objects.prefetch_related("participants__user", "matches")
    serializer_class = TournamentDetailSerializer
    permission_classes = [permissions.AllowAny]


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
