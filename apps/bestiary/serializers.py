from rest_framework import serializers

from apps.accounts.models import User
from apps.battles.models import Battle

from .models import Bestiary, MonsterKill


class BestiarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Bestiary
        fields = ["id", "name", "category", "danger_level", "description", "image"]


class KillerBriefSerializer(serializers.Serializer):
    """Один из убийц вида — для списка «кто убивал» на карточке существа."""

    username = serializers.CharField(source="user.username")
    display_name = serializers.CharField(source="user.display_name")
    date = serializers.DateTimeField()


class BestiaryDetailSerializer(BestiarySerializer):
    """Карточка вида — плюс список пользователей, убивавших это существо."""

    killers = serializers.SerializerMethodField()

    class Meta(BestiarySerializer.Meta):
        fields = BestiarySerializer.Meta.fields + ["killers"]

    def get_killers(self, obj):
        kills = obj.kills.select_related("user").order_by("-date")
        return KillerBriefSerializer(kills, many=True).data


class MonsterKillSerializer(serializers.ModelSerializer):
    """Чтение журнала охот — публично (раздел 1 плана)."""

    user = serializers.SlugRelatedField(slug_field="username", read_only=True)
    bestiary = BestiarySerializer(read_only=True)
    recorded_by = serializers.SlugRelatedField(slug_field="username", read_only=True)
    reward_granted_by = serializers.SlugRelatedField(slug_field="username", read_only=True)

    class Meta:
        model = MonsterKill
        fields = [
            "id", "user", "bestiary", "battle", "date", "notes", "recorded_by",
            "reward_granted", "reward_granted_by", "reward_experience", "reward_currency",
        ]
        read_only_fields = fields


class MonsterKillWriteSerializer(serializers.ModelSerializer):
    """Форма записи убийства — раздел 4.7 плана.

    recorded_by и (при выставлении reward_granted) reward_granted_by
    проставляются во view. Фактическое начисление опыта/кронов при переходе
    reward_granted False -> True обрабатывает MonsterKill.save().
    """

    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    bestiary = serializers.PrimaryKeyRelatedField(queryset=Bestiary.objects.all())
    battle = serializers.PrimaryKeyRelatedField(
        queryset=Battle.objects.all(), required=False, allow_null=True,
    )

    class Meta:
        model = MonsterKill
        fields = [
            "id", "user", "bestiary", "battle", "date", "notes",
            "reward_granted", "reward_experience", "reward_currency",
        ]
