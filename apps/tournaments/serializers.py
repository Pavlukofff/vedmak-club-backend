from rest_framework import serializers

from apps.accounts.models import User
from apps.battles.models import Battle

from .models import Tournament, TournamentMatch, TournamentParticipant, TournamentPhoto


class TournamentParticipantSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(slug_field="username", read_only=True)

    class Meta:
        model = TournamentParticipant
        fields = ["id", "user", "seed"]


class ParticipantCreateSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(slug_field="username", queryset=User.objects.all())

    class Meta:
        model = TournamentParticipant
        fields = ["id", "user", "seed"]


class TournamentMatchSerializer(serializers.ModelSerializer):
    participant1 = TournamentParticipantSerializer(read_only=True)
    participant2 = TournamentParticipantSerializer(read_only=True)
    winner = TournamentParticipantSerializer(read_only=True)

    class Meta:
        model = TournamentMatch
        fields = [
            "id", "bracket", "round_number", "position",
            "participant1", "participant2", "battle", "winner",
        ]


class MatchLinkBattleSerializer(serializers.ModelSerializer):
    """Привязать зафиксированный судьёй бой к ячейке сетки."""

    battle = serializers.PrimaryKeyRelatedField(queryset=Battle.objects.all())

    class Meta:
        model = TournamentMatch
        fields = ["id", "battle"]

    def validate_battle(self, battle):
        match = self.instance
        fighters = set()
        if match.participant1_id:
            fighters.add(match.participant1.user_id)
        if match.participant2_id:
            fighters.add(match.participant2.user_id)
        if not fighters or {battle.fighter1_id, battle.fighter2_id} != fighters:
            raise serializers.ValidationError(
                "Участники боя не совпадают с участниками этой ячейки сетки.",
            )
        return battle


class TournamentPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TournamentPhoto
        fields = ["id", "image", "caption"]


class TournamentSerializer(serializers.ModelSerializer):
    """Раздел 1 плана: список турниров (в т.ч. архив прошедших с фото)."""

    winner = serializers.SlugRelatedField(slug_field="username", read_only=True)
    runner_up = serializers.SlugRelatedField(slug_field="username", read_only=True)
    photos = TournamentPhotoSerializer(many=True, read_only=True)

    class Meta:
        model = Tournament
        fields = [
            "id", "title", "description", "date_start", "date_end", "status",
            "bracket_type", "winner", "runner_up", "results_notes",
            "bracket_generated", "photos",
        ]


class TournamentCreateSerializer(serializers.ModelSerializer):
    """«Создать турнир» — доступно только can_manage_tournaments (см. view).

    status/bracket_type необязательны, берут значение по умолчанию модели
    (upcoming/single), если не переданы явно.
    """

    class Meta:
        model = Tournament
        fields = [
            "id", "title", "description", "date_start", "date_end",
            "status", "bracket_type",
        ]


class TournamentUpdateSerializer(serializers.ModelSerializer):
    """Редактирование турнира (в т.ч. смена статуса) — только can_manage_tournaments.

    bracket_type менять нельзя после того, как сетка уже сгенерирована —
    дальнейшая логика продвижения по сетке (single/double) завязана на нём.
    """

    class Meta:
        model = Tournament
        fields = [
            "id", "title", "description", "date_start", "date_end",
            "status", "bracket_type", "results_notes",
        ]

    def validate_bracket_type(self, value):
        if self.instance and self.instance.bracket_generated and value != self.instance.bracket_type:
            raise serializers.ValidationError(
                "Нельзя менять формат сетки после того, как она сгенерирована.",
            )
        return value


class TournamentDetailSerializer(TournamentSerializer):
    """Раздел «таблица посева»: полная сетка турнира, сгруппированная

    по веткам (upper/lower/final) и раундам внутри каждой ветки.
    """

    participants = TournamentParticipantSerializer(many=True, read_only=True)
    brackets = serializers.SerializerMethodField()

    class Meta(TournamentSerializer.Meta):
        fields = TournamentSerializer.Meta.fields + ["participants", "brackets"]

    def get_brackets(self, obj):
        matches = obj.matches.select_related(
            "participant1__user", "participant2__user", "winner__user", "battle",
        ).order_by("bracket", "round_number", "position")

        grouped = {}
        for match in matches:
            grouped.setdefault(match.bracket, {}).setdefault(match.round_number, []).append(
                TournamentMatchSerializer(match).data,
            )

        return {
            bracket_name: [
                {"round": round_number, "matches": ms}
                for round_number, ms in sorted(rounds.items())
            ]
            for bracket_name, rounds in grouped.items()
        }
